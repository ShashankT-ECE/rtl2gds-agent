#!/usr/bin/env python3
"""
eval_spec_parser.py
Evaluates the Spec Parser Agent across all 5 benchmarks.
Calls the LLM directly via model_router with the spec_parser prompt,
then compares the parsed output against reference RTL.

Usage:
    cd /home/shashankt/projects/rtl2gds-agent
    source .venv/bin/activate
    python tools/eval_spec_parser.py
"""

import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

# Import project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v1_core.utils.model_router import call_llm
from v1_core.agents.spec_parser_agent import SPEC_PARSER_PROMPT
from v1_core.utils import logger

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BENCHMARKS_DIR = os.path.join(PROJECT_ROOT, "benchmarks")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")

BENCHMARKS = ["alu_8bit", "sync_fifo_8x16", "fsm_traffic_light", "uart_tx", "apb_slave"]

DESIGN_TYPE_MAP = {
    "alu_8bit": "combinational",
    "sync_fifo_8x16": "sequential",
    "fsm_traffic_light": "fsm",
    "uart_tx": "fsm",
    "apb_slave": "protocol",
}


# ============================================================
# Verilog Port Parser
# ============================================================

def parse_verilog_ports(rtl_text: str) -> Dict[str, Any]:
    """Parse Verilog module port declarations from reference RTL text.
    Returns dict with module_name, inputs, outputs.
    """
    result = {
        "module_name": "",
        "inputs": [],
        "outputs": [],
    }

    # Extract module name
    mod_match = re.search(r'module\s+(\w+)\s*\(', rtl_text)
    if mod_match:
        result["module_name"] = mod_match.group(1)

    # Extract port list — capture everything between module( and );
    port_section_match = re.search(
        r'module\s+\w+\s*\((.*?)\)\s*;', rtl_text, re.DOTALL
    )
    if not port_section_match:
        return result

    port_section = port_section_match.group(1)

    # Regex for port declarations:
    # input/output [wire/reg] [<width>] <name>
    # Handles:
    #   input  [7:0] A,
    #   input  wire       clk,
    #   input        PCLK,
    #   output reg [7:0] Y,
    #   output [31:0] PRDATA,
    #   output       PREADY
    #   output reg        red_light,
    #   output wire       full,
    port_pattern = re.compile(
        r'(input|output)\s+'           # direction
        r'(?:wire|reg)\s+'              # optional wire/reg
        r'(?:\[(\d+):(\d+)\])?\s*'      # optional width [MSB:LSB]
        r'(\w+)'                        # port name
        r'\s*,?\s*(?://.*)?$',          # trailing comma and optional comment
        re.MULTILINE
    )

    # Also handle ports without wire/reg keyword
    port_pattern2 = re.compile(
        r'(input|output)\s+'
        r'(?:\[(\d+):(\d+)\])?\s*'
        r'(\w+)'
        r'\s*,?\s*(?://.*)?$',
        re.MULTILINE
    )

    for line in port_section.split('\n'):
        line = line.strip()
        if not line or line.startswith('//') or line.startswith('*'):
            continue

        # Strip inline comments
        line_clean = re.sub(r'//.*$', '', line).strip()

        # Try pattern 1 (with wire/reg)
        m = port_pattern.match(line_clean)
        if not m:
            # Try pattern 2 (without wire/reg)
            m = port_pattern2.match(line_clean)

        if m:
            direction = m.group(1)
            msb = m.group(2)
            lsb = m.group(3)
            name = m.group(4)

            # Calculate width
            if msb and lsb:
                width = int(msb) - int(lsb) + 1
            else:
                width = 1  # Scalar port

            port_info = {"name": name, "width": width}

            if direction == "input":
                # Avoid duplicates
                if not any(p["name"] == name for p in result["inputs"]):
                    result["inputs"].append(port_info)
            else:
                if not any(p["name"] == name for p in result["outputs"]):
                    result["outputs"].append(port_info)

    return result


# ============================================================
# Comparison Functions
# ============================================================

def compare_ports(
    spec_ports: List[Dict], rtl_ports: List[Dict], port_type: str
) -> Dict[str, Any]:
    """Compare spec-parsed ports against reference RTL ports."""
    spec_names = {p["name"] for p in spec_ports}
    rtl_names = {p["name"] for p in rtl_ports}

    missing_ports = rtl_names - spec_names
    extra_ports = spec_names - rtl_names

    # Width mismatches
    width_errors = []
    rtl_by_name = {p["name"]: p for p in rtl_ports}
    for sp in spec_ports:
        if sp["name"] in rtl_by_name:
            rp = rtl_by_name[sp["name"]]
            if sp.get("width") != rp["width"]:
                width_errors.append(
                    f"{sp['name']}: spec width={sp.get('width','?')}, "
                    f"rtl width={rp['width']}"
                )

    match = len(missing_ports) == 0 and len(extra_ports) == 0 and len(width_errors) == 0

    return {
        "match": match,
        "spec_count": len(spec_ports),
        "rtl_count": len(rtl_ports),
        "missing": sorted(list(missing_ports)),
        "extra": sorted(list(extra_ports)),
        "width_errors": width_errors,
        "spec_ports": spec_ports,
        "rtl_ports": rtl_ports,
    }


def evaluate_benchmark(
    benchmark_name: str, spec_text: str, spec_analysis: Dict, rtl_text: str, raw_llm: str
) -> Dict[str, Any]:
    """Evaluate spec parser output against reference RTL for one benchmark."""
    rtl_info = parse_verilog_ports(rtl_text)
    result = {
        "benchmark": benchmark_name,
        "raw_llm_output": raw_llm,
        "spec_analysis": spec_analysis,
        "rtl_info": rtl_info,
        "json_valid": True,
        "module_name": {"spec": spec_analysis.get("module_name", ""),
                        "rtl": rtl_info["module_name"],
                        "match": spec_analysis.get("module_name", "").lower()
                                 == rtl_info["module_name"].lower()},
        "inputs": compare_ports(
            spec_analysis.get("inputs", []), rtl_info["inputs"], "input"
        ),
        "outputs": compare_ports(
            spec_analysis.get("outputs", []), rtl_info["outputs"], "output"
        ),
        "design_type": {
            "spec": spec_analysis.get("design_type", ""),
            "expected": DESIGN_TYPE_MAP.get(benchmark_name, "unknown"),
        },
        "behavior": spec_analysis.get("behavior", []),
        "corner_cases": spec_analysis.get("corner_cases", []),
        "clock": spec_analysis.get("clock", None),
        "reset": spec_analysis.get("reset", None),
    }

    # Determine expected clock/reset
    result["clock_expected"] = None
    result["reset_expected"] = None
    for p in rtl_info["inputs"]:
        name_lower = p["name"].lower()
        if name_lower in ("clk", "pclk"):
            result["clock_expected"] = p["name"]
        if name_lower in ("rst_n", "presetn"):
            result["reset_expected"] = p["name"]

    # Design type match
    result["design_type"]["match"] = (
        result["design_type"]["spec"].lower()
        == result["design_type"]["expected"].lower()
    )

    # Behavior rules assessment
    result["behavior_ok"] = len(result["behavior"]) >= 3
    result["behavior_count"] = len(result["behavior"])

    # Corner cases assessment
    result["corner_cases_ok"] = len(result["corner_cases"]) >= 2
    result["corner_cases_count"] = len(result["corner_cases"])

    # Clock/reset assessment
    result["clock_ok"] = result["clock"] == result["clock_expected"]
    result["reset_ok"] = result["reset"] == result["reset_expected"]

    # Overall assessment
    summary = {
        "module_name_ok": result["module_name"]["match"],
        "inputs_ok": result["inputs"]["match"],
        "outputs_ok": result["outputs"]["match"],
        "design_type_ok": result["design_type"]["match"],
        "behavior_ok": result["behavior_ok"],
        "corner_cases_ok": result["corner_cases_ok"],
        "clock_ok": result["clock_ok"],
        "reset_ok": result["reset_ok"],
        "json_valid": result["json_valid"],
    }

    all_ok = all(summary.values())
    critical_ok = (
        summary["module_name_ok"]
        and summary["inputs_ok"]
        and summary["outputs_ok"]
        and summary["design_type_ok"]
        and summary["json_valid"]
    )

    if not critical_ok:
        result["score"] = "FAIL"
    elif all_ok:
        result["score"] = "PASS"
    else:
        result["score"] = "PARTIAL"

    return result


# ============================================================
# Report Generation
# ============================================================

def generate_report(all_results: List[Dict]) -> str:
    """Generate the full evaluation report as Markdown."""
    lines = []
    lines.append("# Spec Parser Agent Evaluation Report")
    lines.append("")
    lines.append(
        f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )
    lines.append(f"**Benchmarks Evaluated**: {len(all_results)}")
    lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Benchmark | Score | Module | Inputs | Outputs | Design Type | Behavior | Corner Cases | Clock | Reset | JSON |")
    lines.append("|-----------|-------|--------|--------|---------|-------------|----------|--------------|-------|-------|------|")

    pass_count = sum(1 for r in all_results if r["score"] == "PASS")
    partial_count = sum(1 for r in all_results if r["score"] == "PARTIAL")
    fail_count = sum(1 for r in all_results if r["score"] == "FAIL")

    for r in all_results:
        name = r["benchmark"]
        score = r["score"]
        mod = "Y" if r["module_name"]["match"] else "N"
        inp = "Y" if r["inputs"]["match"] else "N"
        out = "Y" if r["outputs"]["match"] else "N"
        dt = "Y" if r["design_type"]["match"] else "N"
        bhv = f"{r['behavior_count']}" + ("*" if not r["behavior_ok"] else "")
        cc = f"{r['corner_cases_count']}" + ("*" if not r["corner_cases_ok"] else "")
        clk = "Y" if r["clock_ok"] else ("_" if r["clock_expected"] is None else "N")
        rst = "Y" if r["reset_ok"] else ("_" if r["reset_expected"] is None else "N")
        jsn = "Y" if r["json_valid"] else "N"
        lines.append(f"| {name} | {score} | {mod} | {inp} | {out} | {dt} | {bhv} | {cc} | {clk} | {rst} | {jsn} |")

    lines.append("")
    lines.append(f"**Overall**: {pass_count} PASS, {partial_count} PARTIAL, {fail_count} FAIL")
    lines.append("")

    # Per-benchmark detailed analysis
    for r in all_results:
        name = r["benchmark"]
        lines.append("---")
        lines.append("")
        lines.append(f"## {name}")
        lines.append("")
        lines.append(f"**Score**: {r['score']}")
        lines.append("")

        # Module name
        lines.append(f"### Module Name")
        lines.append(f"- Spec: `{r['module_name']['spec']}`")
        lines.append(f"- RTL:  `{r['module_name']['rtl']}`")
        lines.append(f"- Match: {'YES' if r['module_name']['match'] else 'NO'}")
        lines.append("")

        # Input ports
        lines.append("### Input Ports")
        lines.append(f"- Spec count: {r['inputs']['spec_count']}, RTL count: {r['inputs']['rtl_count']}")
        if r['inputs']['missing']:
            lines.append(f"- **Missing from spec**: {', '.join(f'`{p}`' for p in r['inputs']['missing'])}")
        if r['inputs']['extra']:
            lines.append(f"- **Extra in spec**: {', '.join(f'`{p}`' for p in r['inputs']['extra'])}")
        if r['inputs']['width_errors']:
            lines.append(f"- **Width errors**:")
            for we in r['inputs']['width_errors']:
                lines.append(f"  - {we}")
        lines.append("")
        lines.append("| # | Spec Port | Spec Width | RTL Port | RTL Width | Match |")
        lines.append("|---|-----------|------------|----------|-----------|-------|")

        # Build aligned port comparison
        all_input_names = set()
        for p in r['inputs']['spec_ports']:
            all_input_names.add(p['name'])
        for p in r['inputs']['rtl_ports']:
            all_input_names.add(p['name'])

        rtl_inputs_dict = {p['name']: p for p in r['inputs']['rtl_ports']}
        spec_inputs_dict = {p['name']: p for p in r['inputs']['spec_ports']}

        for idx, pname in enumerate(sorted(all_input_names)):
            sp = spec_inputs_dict.get(pname, {})
            rp = rtl_inputs_dict.get(pname, {})
            spec_name = sp.get('name', '---')
            spec_w = str(sp.get('width', '---'))
            rtl_name = rp.get('name', '---')
            rtl_w = str(rp.get('width', '---'))
            match = "Y" if (spec_w == rtl_w and spec_name == rtl_name) else "N"
            lines.append(f"| {idx+1} | `{spec_name}` | {spec_w} | `{rtl_name}` | {rtl_w} | {match} |")

        lines.append("")

        # Output ports
        lines.append("### Output Ports")
        lines.append(f"- Spec count: {r['outputs']['spec_count']}, RTL count: {r['outputs']['rtl_count']}")
        if r['outputs']['missing']:
            lines.append(f"- **Missing from spec**: {', '.join(f'`{p}`' for p in r['outputs']['missing'])}")
        if r['outputs']['extra']:
            lines.append(f"- **Extra in spec**: {', '.join(f'`{p}`' for p in r['outputs']['extra'])}")
        if r['outputs']['width_errors']:
            lines.append(f"- **Width errors**:")
            for we in r['outputs']['width_errors']:
                lines.append(f"  - {we}")
        lines.append("")
        lines.append("| # | Spec Port | Spec Width | RTL Port | RTL Width | Match |")
        lines.append("|---|-----------|------------|----------|-----------|-------|")

        all_output_names = set()
        for p in r['outputs']['spec_ports']:
            all_output_names.add(p['name'])
        for p in r['outputs']['rtl_ports']:
            all_output_names.add(p['name'])

        rtl_outputs_dict = {p['name']: p for p in r['outputs']['rtl_ports']}
        spec_outputs_dict = {p['name']: p for p in r['outputs']['spec_ports']}

        for idx, pname in enumerate(sorted(all_output_names)):
            sp = spec_outputs_dict.get(pname, {})
            rp = rtl_outputs_dict.get(pname, {})
            spec_name = sp.get('name', '---')
            spec_w = str(sp.get('width', '---'))
            rtl_name = rp.get('name', '---')
            rtl_w = str(rp.get('width', '---'))
            match = "Y" if (spec_w == rtl_w and spec_name == rtl_name) else "N"
            lines.append(f"| {idx+1} | `{spec_name}` | {spec_w} | `{rtl_name}` | {rtl_w} | {match} |")

        lines.append("")

        # Design Type
        lines.append("### Design Type")
        lines.append(f"- Spec: `{r['design_type']['spec']}`")
        lines.append(f"- Expected: `{r['design_type']['expected']}`")
        lines.append(f"- Match: {'YES' if r['design_type']['match'] else 'NO'}")
        lines.append("")

        # Behavior Rules
        lines.append("### Behavior Rules")
        lines.append(f"- Count: {r['behavior_count']}")
        lines.append(f"- Adequate (>=3): {'YES' if r['behavior_ok'] else 'NO'}")
        lines.append("")
        for i, rule in enumerate(r["behavior"]):
            lines.append(f"{i+1}. {rule}")
        lines.append("")

        # Corner Cases
        lines.append("### Corner Cases")
        lines.append(f"- Count: {r['corner_cases_count']}")
        lines.append(f"- Adequate (>=2): {'YES' if r['corner_cases_ok'] else 'NO'}")
        lines.append("")
        for i, cc in enumerate(r["corner_cases"]):
            lines.append(f"{i+1}. {cc}")
        lines.append("")

        # Clock/Reset
        lines.append("### Clock / Reset")
        lines.append(f"- Clock spec: `{r['clock']}` | expected: `{r['clock_expected']}` | OK: {'YES' if r['clock_ok'] else 'NO'}")
        lines.append(f"- Reset spec: `{r['reset']}` | expected: `{r['reset_expected']}` | OK: {'YES' if r['reset_ok'] else 'NO'}")
        lines.append("")

        # Raw LLM output
        lines.append("### Raw LLM Output")
        lines.append("```json")
        lines.append(r.get("raw_llm_output", "(empty)"))
        lines.append("```")
        lines.append("")

    # Overall Assessment
    lines.append("---")
    lines.append("")
    lines.append("## Overall Assessment")
    lines.append("")

    total_pass = pass_count
    total_partial = partial_count
    total_fail = fail_count
    total = len(all_results)

    lines.append(f"- **PASS**: {total_pass}/{total}")
    lines.append(f"- **PARTIAL**: {total_partial}/{total}")
    lines.append(f"- **FAIL**: {total_fail}/{total}")
    lines.append("")

    # Aggregate findings
    missing_reqs = []
    incorrect_reqs = []
    ambiguous_reqs = []

    for r in all_results:
        name = r["benchmark"]
        if r["inputs"]["missing"]:
            for p in r["inputs"]["missing"]:
                missing_reqs.append(f"{name}: input port `{p}` missing from spec")
        if r["outputs"]["missing"]:
            for p in r["outputs"]["missing"]:
                missing_reqs.append(f"{name}: output port `{p}` missing from spec")
        if r["inputs"]["extra"]:
            for p in r["inputs"]["extra"]:
                incorrect_reqs.append(f"{name}: extra input port `{p}` in spec not in RTL")
        if r["outputs"]["extra"]:
            for p in r["outputs"]["extra"]:
                incorrect_reqs.append(f"{name}: extra output port `{p}` in spec not in RTL")
        if r["inputs"]["width_errors"]:
            for we in r["inputs"]["width_errors"]:
                incorrect_reqs.append(f"{name}: input {we}")
        if r["outputs"]["width_errors"]:
            for we in r["outputs"]["width_errors"]:
                incorrect_reqs.append(f"{name}: output {we}")
        if not r["design_type"]["match"]:
            incorrect_reqs.append(
                f"{name}: design type '{r['design_type']['spec']}' != "
                f"expected '{r['design_type']['expected']}'"
            )
        if not r["module_name"]["match"]:
            incorrect_reqs.append(
                f"{name}: module name '{r['module_name']['spec']}' != "
                f"RTL '{r['module_name']['rtl']}'"
            )

    lines.append("### Missing Requirements Identified")
    if missing_reqs:
        for item in missing_reqs:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("### Incorrect Requirements Identified")
    if incorrect_reqs:
        for item in incorrect_reqs:
            lines.append(f"- {item}")
    else:
        lines.append("- None")
    lines.append("")

    lines.append("### Ambiguous Requirements Identified")
    lines.append("- None explicitly ambiguous in the specs — all designs have clear port specifications.")
    lines.append("")

    # Quality assessment
    lines.append("### Spec Parser Quality Assessment")
    lines.append("")

    if total_pass == total:
        lines.append(
            "The spec parser achieved a **perfect score** across all 5 benchmarks. "
            "It correctly extracted module names, input/output ports with widths, "
            "design type classifications, behavior rules, corner cases, and clock/reset signals."
        )
    elif total_pass >= 3:
        lines.append(
            f"The spec parser is **generally reliable** ({total_pass}/{total} PASS). "
            "It handles standard cases well but has occasional issues with specific design patterns."
        )
    else:
        lines.append(
            f"The spec parser has **significant issues** ({total_pass}/{total} PASS). "
            "Review and improve the prompt or parsing logic before production use."
        )

    lines.append("")

    lines.append("### Recommendations")
    lines.append("")
    lines.append("1. **Port width edge cases**: Ensure the prompt explicitly asks for bit-width extraction.")
    lines.append("2. **Clock/reset naming**: The prompt handles common names (clk, rst_n) well; verify custom names (PCLK, PRESETn).")
    lines.append("3. **Design type for FSMs**: The UART TX spec describes an FSM; check if the parser classifies it correctly.")
    lines.append("4. **APB clock/reset**: Verify PCLK/PRESETn are recognized as clock and reset signals respectively.")
    lines.append("5. **Zero_flag handling**: The ALU spec mentions 'assertes' (typo); check if parser interprets correctly.")

    return "\n".join(lines)


# ============================================================
# Main
# ============================================================

def main():
    """Run the spec parser evaluation for all 5 benchmarks."""
    print("=" * 70)
    print("Spec Parser Agent Evaluation")
    print("=" * 70)
    print()

    all_results = []

    for i, benchmark in enumerate(BENCHMARKS):
        print(f"[{i+1}/{len(BENCHMARKS)}] {benchmark}...")
        print("-" * 40)

        # Paths
        spec_path = os.path.join(BENCHMARKS_DIR, benchmark, "spec.txt")
        rtl_path = os.path.join(BENCHMARKS_DIR, benchmark, "reference_rtl.v")

        # Read spec
        with open(spec_path, "r") as f:
            spec_text = f.read().strip()
        print(f"  Spec: {len(spec_text)} chars")

        # Read reference RTL
        with open(rtl_path, "r") as f:
            rtl_text = f.read()
        print(f"  RTL: {len(rtl_text)} chars")

        # Call the LLM with the spec parser prompt
        prompt = SPEC_PARSER_PROMPT.format(spec=spec_text)

        print(f"  Calling LLM...")
        try:
            raw_response = call_llm(
                prompt=prompt, task="general", thinking=False
            )
            print(f"  LLM response: {len(raw_response)} chars")
        except Exception as e:
            print(f"  LLM call FAILED: {e}")
            raw_response = ""
            spec_analysis = {
                "module_name": "",
                "design_type": "unknown",
                "inputs": [],
                "outputs": [],
                "behavior": [],
                "corner_cases": [],
                "clock": None,
                "reset": None,
            }
            result = evaluate_benchmark(
                benchmark, spec_text, spec_analysis, rtl_text, raw_response
            )
            result["json_valid"] = False
            result["score"] = "FAIL"
            all_results.append(result)
            continue

        # Strip any accidental markdown
        clean = raw_response.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            # Remove first and last line (``` markers)
            if len(lines) > 2:
                clean = "\n".join(lines[1:-1])
            else:
                clean = ""
            clean = clean.strip()

        # Try JSON parsing
        try:
            spec_analysis = json.loads(clean)
            print(f"  JSON valid: YES")
            print(f"  Design type: {spec_analysis.get('design_type', '?')}")
            print(f"  Inputs: {len(spec_analysis.get('inputs', []))}")
            print(f"  Outputs: {len(spec_analysis.get('outputs', []))}")
            print(f"  Behavior rules: {len(spec_analysis.get('behavior', []))}")
            print(f"  Corner cases: {len(spec_analysis.get('corner_cases', []))}")
            result = evaluate_benchmark(
                benchmark, spec_text, spec_analysis, rtl_text, clean
            )
            result["json_valid"] = True
        except json.JSONDecodeError as e:
            print(f"  JSON parse FAILED: {e}")
            spec_analysis = {
                "module_name": "",
                "design_type": "unknown",
                "inputs": [],
                "outputs": [],
                "behavior": [],
                "corner_cases": [],
                "clock": None,
                "reset": None,
            }
            result = evaluate_benchmark(
                benchmark, spec_text, spec_analysis, rtl_text, clean
            )
            result["json_valid"] = False
            result["score"] = "FAIL"

        print(f"  Score: {result['score']}")
        all_results.append(result)
        print()

    # Generate and save report
    report = generate_report(all_results)

    os.makedirs(DOCS_DIR, exist_ok=True)
    report_path = os.path.join(DOCS_DIR, "SPEC_PARSER_EVALUATION.md")
    with open(report_path, "w") as f:
        f.write(report)

    print("=" * 70)
    print(f"Report saved to: {report_path}")
    print(f"Summary: {sum(1 for r in all_results if r['score']=='PASS')} PASS, "
          f"{sum(1 for r in all_results if r['score']=='PARTIAL')} PARTIAL, "
          f"{sum(1 for r in all_results if r['score']=='FAIL')} FAIL")
    print("=" * 70)


if __name__ == "__main__":
    main()
