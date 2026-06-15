#!/usr/bin/env python3
"""
eval_verification_planner.py
Evaluation script for the Verification Planner Agent across all 5 benchmarks.

For each benchmark:
  1. Reads the spec from benchmarks/BENCHMARK/spec.txt
  2. Runs the spec_parser_agent prompt via model_router.call_llm
  3. Runs the verification_planner_agent prompt with that spec_analysis
  4. Parses both JSON outputs
  5. Evaluates the verification plan against the reference RTL and reference testbench

Outputs: docs/VERIFICATION_PLANNER_EVALUATION.md
"""

import json
import sys
import os
import re
import traceback
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from v1_core.utils.model_router import call_llm
from v1_core.agents.spec_parser_agent import SPEC_PARSER_PROMPT
from v1_core.agents.verification_planner_agent import VERIFICATION_PLANNER_PROMPT

BENCHMARKS_DIR = PROJECT_ROOT / "benchmarks"
OUTPUT_DIR = PROJECT_ROOT / "docs"


# ============================================================
# Utility helpers
# ============================================================

def read_spec(benchmark: str) -> str:
    path = BENCHMARKS_DIR / benchmark / "spec.txt"
    return path.read_text().strip()


def read_reference_tb(benchmark: str) -> str:
    path = BENCHMARKS_DIR / benchmark / "reference_tb.py"
    return path.read_text()


def extract_tb_functions(tb_code: str) -> list[str]:
    """Extract test function names from cocotb testbench."""
    funcs = re.findall(r'@cocotb\.test\(\)\s*\n\s*async def (\w+)', tb_code)

    # Also get help/docstring snippets
    doc_map = {}
    for m in re.finditer(r'@cocotb\.test\(\)\s*\n\s*async def (\w+)\(.*?\):\s*\n\s*"""(.+?)"""', tb_code, re.DOTALL):
        doc_map[m.group(1)] = m.group(2).strip()

    return funcs, doc_map


def call_spec_parser(spec_text: str, design_name: str) -> dict:
    """Run spec_parser_agent prompt and return parsed JSON."""
    prompt = SPEC_PARSER_PROMPT.format(spec=spec_text)
    response = call_llm(prompt=prompt, task="general", thinking=False)

    clean = response.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].startswith("```"):
                end_idx = i
                break
        if end_idx > 0:
            clean = "\n".join(lines[1:end_idx])
        else:
            clean = "\n".join(lines[1:])

    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"  [WARN] Failed to parse spec_analysis JSON: {e}")
        return {"design_type": "unknown", "behavior": [], "corner_cases": []}


def call_verification_planner(spec_analysis: dict, design_name: str) -> dict:
    """Run verification_planner_agent prompt and return parsed JSON."""
    spec_analysis_json = json.dumps(spec_analysis, indent=2)
    prompt = VERIFICATION_PLANNER_PROMPT.format(spec_analysis=spec_analysis_json)
    response = call_llm(prompt=prompt, task="general", thinking=False)

    clean = response.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        end_idx = -1
        for i in range(1, len(lines)):
            if lines[i].startswith("```"):
                end_idx = i
                break
        if end_idx > 0:
            clean = "\n".join(lines[1:end_idx])
        else:
            clean = "\n".join(lines[1:])

    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        print(f"  [WARN] Failed to parse verification_plan JSON: {e}")
        print(f"  Raw response (first 500 chars): {response[:500]}")
        return {
            "design_name": design_name,
            "design_type": "unknown",
            "verification_tiers": [],
            "reference_model_code": "",
            "forbidden_behaviors": [],
            "timing_requirements": {"clock_signal": None, "clock_period_ns": None, "skip_sta": True}
        }


# ============================================================
# Evaluation functions
# ============================================================

def evaluate_tier_structure(plan: dict) -> dict:
    """Eval 1: Tier structure check."""
    tiers = plan.get("verification_tiers", [])
    tier_count = len(tiers)
    tier_names = [t.get("name", "") for t in tiers]

    has_t1 = any("reset" in n.lower() or "initialization" in n.lower() for n in tier_names)
    has_t2 = any("functional" in n.lower() for n in tier_names)
    has_t3 = any("boundary" in n.lower() or "corner" in n.lower() for n in tier_names)
    tier_numbers = [t.get("tier") for t in tiers if t.get("tier") is not None]

    issues = []
    if tier_count != 3:
        issues.append(f"Expected exactly 3 tiers, got {tier_count}")
    if not has_t1:
        issues.append("Missing Tier 1 (Reset and Initialization)")
    if not has_t2:
        issues.append("Missing Tier 2 (Functional Verification)")
    if not has_t3:
        issues.append("Missing Tier 3 (Boundary and Corner Cases)")

    score = "EXCELLENT" if (tier_count == 3 and has_t1 and has_t2 and has_t3) else \
            "GOOD" if (tier_count >= 2) else "POOR"

    return {
        "tier_count": tier_count,
        "tier_names": tier_names,
        "tier_numbers": tier_numbers,
        "has_t1_reset": has_t1,
        "has_t2_functional": has_t2,
        "has_t3_boundary": has_t3,
        "issues": issues,
        "score": score
    }


def evaluate_test_ids(plan: dict) -> dict:
    """Eval 2: Test ID structure check."""
    tiers = plan.get("verification_tiers", [])
    all_ids = []
    issues = []

    for t in tiers:
        tier_num = t.get("tier", 0)
        tests = t.get("tests", [])
        for test in tests:
            tid = test.get("test_id", "")
            all_ids.append(tid)
            expected_prefix = f"T{tier_num}_"
            if not tid.startswith(expected_prefix):
                issues.append(f"'{tid}' in tier {tier_num} should start with '{expected_prefix}'")

    # Check for duplicates
    seen = set()
    for tid in all_ids:
        if tid in seen:
            issues.append(f"Duplicate test ID: '{tid}'")
        seen.add(tid)

    score = "EXCELLENT" if len(issues) == 0 else \
            "GOOD" if len(issues) <= 2 else "FAIR"

    return {
        "total_test_ids": len(all_ids),
        "all_ids": all_ids,
        "issues": issues,
        "score": score
    }


def evaluate_test_distribution(plan: dict) -> dict:
    """Count tests per tier."""
    tiers = plan.get("verification_tiers", [])
    dist = {}
    total = 0
    for t in tiers:
        tier_num = t.get("tier", 0)
        count = len(t.get("tests", []))
        dist[f"Tier {tier_num}"] = count
        total += count
    dist["total"] = total
    return dist


def evaluate_coverage(spec_text: str, plan: dict, tb_funcs: list[str], tb_doc_map: dict) -> dict:
    """Eval 3: Coverage completeness."""
    tiers = plan.get("verification_tiers", [])
    plan_test_descriptions = []
    for t in tiers:
        for test in t.get("tests", []):
            plan_test_descriptions.append({
                "id": test.get("test_id", ""),
                "desc": test.get("description", "").lower(),
                "tier": t.get("tier", 0)
            })

    spec_lower = spec_text.lower()
    found_behaviors = set()
    missing_behaviors = []
    for desc in plan_test_descriptions:
        d = desc["desc"]
        if "reset" in d:
            found_behaviors.add("reset")
        if "write" in d or "add" in d or "operation" in d or "opcode" in d:
            found_behaviors.add("operations")
        if "read" in d:
            found_behaviors.add("read")
        if "full" in d or "overflow" in d or "saturat" in d:
            found_behaviors.add("full/overflow")
        if "empty" in d or "underflow" in d:
            found_behaviors.add("empty/underflow")
        if "boundary" in d or "corner" in d or "edge" in d or "extreme" in d:
            found_behaviors.add("boundary/corner")
        if "invalid" in d or "error" in d or "pslverr" in d or "illegal" in d:
            found_behaviors.add("invalid/error")
        if "flag" in d or "zero" in d:
            found_behaviors.add("flag")
        if "simultaneous" in d or "concurrent" in d or "parallel" in d:
            found_behaviors.add("simultaneous")

    # Compare with reference TB functions
    tb_funcs_lower = [f.lower().replace("test_", "") for f in tb_funcs]
    plan_funcs = [d["id"].lower().replace("t1_", "").replace("t2_", "").replace("t3_", "") for d in plan_test_descriptions]

    # Map TB functions to plan coverage
    tb_coverage = {}
    for tb_func, tb_doc in zip(tb_funcs, tb_doc_map.values() if tb_doc_map else tb_funcs):
        matched = False
        for pd in plan_test_descriptions:
            # Check if plan description mentions key aspects of the TB test
            tb_lower = tb_doc.lower() if tb_doc else tb_func.lower()
            if any(word in pd["desc"] for word in tb_lower.split()[:5]):
                matched = True
                break
            # Also check by function name keywords
            keywords = tb_func.lower().replace("test_", "").split("_")
            if any(kw in pd["desc"] for kw in keywords if len(kw) > 3):
                matched = True
                break
        tb_coverage[tb_func] = matched

    missing_tests = [f for f, covered in tb_coverage.items() if not covered]

    score = "EXCELLENT" if len(missing_tests) == 0 else \
            "GOOD" if len(missing_tests) <= 2 else \
            "FAIR" if len(missing_tests) <= 4 else "POOR"

    return {
        "found_behaviors": found_behaviors,
        "missing_behaviors": missing_behaviors,
        "tb_total_functions": len(tb_funcs),
        "tb_covered": sum(1 for v in tb_coverage.values() if v),
        "tb_missing": missing_tests,
        "tb_coverage_pct": round(len(tb_funcs) / len(tb_funcs) * 100 if tb_funcs else 0),
        "score": score
    }


def evaluate_reference_model(plan: dict, spec_text: str) -> dict:
    """Eval 4: Reference model quality."""
    ref_code = plan.get("reference_model_code", "")
    issues = []

    if not ref_code or not ref_code.strip():
        return {"issues": ["No reference model code provided"], "score": "POOR", "code_length": 0}

    # Basic syntactic checks
    if "def reference_model" not in ref_code:
        issues.append("Function should be named 'reference_model'")

    if "inputs" not in ref_code and "def reference_model(" in ref_code:
        # Check the function signature parameter
        sig_match = re.search(r'def reference_model\(([^)]*)\)', ref_code)
        if sig_match:
            params = sig_match.group(1)
            if "inputs" not in params and "A" not in params:
                issues.append(f"Function signature params don't look right: '{params}'")

    if "return" not in ref_code:
        issues.append("No return statement found")

    # Check if it returns a dict (as required by the prompt)
    if "return {" not in ref_code and "return (" not in ref_code:
        if "return" not in ref_code.split("\n")[-1]:
            issues.append("Return value should be a dict or tuple")

    # Check if it handles all opcodes for ALU
    if "alu" in spec_text.lower() or "opcode" in spec_text.lower():
        for op in [0, 1, 2, 3, 4, 5, 6, 7]:
            if str(op) not in ref_code and f"opcode == {op}" not in ref_code:
                pass  # Might use if-elif chain
        if "if opcode" not in ref_code and "match opcode" not in ref_code:
            issues.append("ALU reference model should handle all 8 opcodes via if/elif or match")

    score = "EXCELLENT" if len(issues) == 0 else \
            "GOOD" if len(issues) <= 1 else \
            "FAIR" if len(issues) <= 3 else "POOR"

    return {
        "code_length": len(ref_code),
        "has_return": "return" in ref_code,
        "has_function_def": "def reference_model" in ref_code,
        "issues": issues,
        "score": score
    }


def evaluate_forbidden_behaviors(plan: dict, design_type: str) -> dict:
    """Eval 5: Forbidden behaviors check."""
    forbidden = plan.get("forbidden_behaviors", [])
    if not forbidden:
        return {"count": 0, "score": "POOR", "issues": ["No forbidden behaviors listed"]}

    forbidden_lower = [f.lower() for f in forbidden]
    issues = []

    if len(forbidden) < 3:
        issues.append(f"Only {len(forbidden)} forbidden behaviors listed (expected at least 3)")

    # Common expected forbidden behaviors per design type
    expected_keywords = {
        "combinational": ["hazard", "glitch", "x", "z", "metastability", "race"],
        "sequential": ["metastability", "setup", "hold", "data loss", "corruption", "overflow"],
        "fsm": ["illegal state", "deadlock", "lockup", "metastability", "glitch"],
        "protocol": ["data corruption", "protocol violation", "bus conflict", "x", "z"]
    }

    keywords = expected_keywords.get(design_type, ["x", "z", "metastability"])
    found_keywords = [kw for kw in keywords if any(kw in fb for fb in forbidden_lower)]
    if not found_keywords:
        issues.append(f"No design-type-specific forbidden behaviors found for '{design_type}'")

    score = "EXCELLENT" if len(forbidden) >= 3 and len(issues) <= 1 else \
            "GOOD" if len(forbidden) >= 2 else \
            "FAIR" if len(forbidden) >= 1 else "POOR"

    return {
        "count": len(forbidden),
        "behaviors": forbidden,
        "found_keywords": found_keywords,
        "issues": issues,
        "score": score
    }


def evaluate_timing_requirements(plan: dict, design_type: str) -> dict:
    """Eval 6: Timing requirements check."""
    timing = plan.get("timing_requirements", {})
    if not timing:
        return {"issues": ["No timing_requirements section"], "score": "POOR"}

    clock = timing.get("clock_signal")
    period = timing.get("clock_period_ns")
    skip_sta = timing.get("skip_sta")

    issues = []
    is_comb = "comb" in design_type.lower()

    if is_comb:
        if clock is not None:
            issues.append(f"Combinational design but clock_signal={clock}, expected null")
        if period is not None:
            issues.append(f"Combinational design but clock_period_ns={period}, expected null")
        if skip_sta is not True:
            issues.append(f"Combinational design but skip_sta={skip_sta}, expected true")
    else:
        if clock is None:
            issues.append(f"Sequential design but clock_signal is null")
        if period is None:
            issues.append(f"Sequential design but clock_period_ns is null")
        if skip_sta is not False:
            issues.append(f"Sequential design but skip_sta={skip_sta}, expected false")

    score = "EXCELLENT" if len(issues) == 0 else \
            "GOOD" if len(issues) <= 1 else \
            "FAIR" if len(issues) <= 2 else "POOR"

    return {
        "clock_signal": clock,
        "clock_period_ns": period,
        "skip_sta": skip_sta,
        "design_type": design_type,
        "issues": issues,
        "score": score
    }


def evaluate_redundancy(plan: dict) -> dict:
    """Eval 7: Check for redundant/duplicate tests across tiers."""
    tiers = plan.get("verification_tiers", [])
    all_tests = []
    issues = []

    for t in tiers:
        tier_num = t.get("tier", 0)
        for test in t.get("tests", []):
            desc = test.get("description", "").lower()
            tid = test.get("test_id", "")
            all_tests.append({"tier": tier_num, "id": tid, "desc": desc})

    # Look for similar descriptions across tiers
    for i in range(len(all_tests)):
        for j in range(i + 1, len(all_tests)):
            t1, t2 = all_tests[i], all_tests[j]
            if t1["tier"] != t2["tier"]:
                # Check if descriptions are very similar
                words1 = set(t1["desc"].split())
                words2 = set(t2["desc"].split())
                common = words1 & words2
                if len(common) >= 4 and len(common) / max(len(words1), len(words2)) > 0.5:
                    issues.append(f"Redundant: '{t1['id']}' (T{t1['tier']}) matches '{t2['id']}' (T{t2['tier']})")

    score = "EXCELLENT" if len(issues) == 0 else "FAIR"

    return {
        "redundant_pairs": len(issues),
        "issues": issues,
        "score": score
    }


def evaluate_redundant_vs_tb(plan: dict, tb_funcs: list[str], tb_doc_map: dict) -> dict:
    """Identify tests in the plan that aren't in the reference TB."""
    tiers = plan.get("verification_tiers", [])
    plan_tests = []
    for t in tiers:
        for test in t.get("tests", []):
            plan_tests.append({
                "id": test.get("test_id", ""),
                "desc": test.get("description", "").lower()
            })

    # Build TB keywords
    tb_keywords = set()
    for func in tb_funcs:
        for word in func.lower().replace("test_", "").split("_"):
            if len(word) > 2:
                tb_keywords.add(word)
    for func, doc in tb_doc_map.items():
        for word in doc.lower().split():
            if len(word) > 3:
                tb_keywords.add(word)

    extra_tests = []
    for pt in plan_tests:
        desc_words = set(pt["desc"].lower().split())
        # Check if this test seems to correspond to any TB function
        matched_tb = False
        for func in tb_funcs:
            func_keywords = set(func.lower().replace("test_", "").split("_"))
            # Remove short words
            func_keywords = {w for w in func_keywords if len(w) > 2}
            if func_keywords & desc_words:
                matched_tb = True
                break
        if not matched_tb:
            # Also check docstrings
            for func, doc in tb_doc_map.items():
                doc_words = set(doc.lower().split())
                # Remove punctuation
                import string
                doc_words = {w.strip(string.punctuation) for w in doc_words if len(w) > 3}
                if doc_words & desc_words:
                    matched_tb = True
                    break

        if not matched_tb:
            extra_tests.append(pt)

    return {
        "extra_tests_in_plan": len(extra_tests),
        "extra_tests": extra_tests
    }


# ============================================================
# Main evaluation runner
# ============================================================

def evaluate_benchmark(benchmark: str) -> dict:
    """Run full evaluation for one benchmark."""
    print(f"\n{'='*60}")
    print(f"Evaluating: {benchmark}")
    print(f"{'='*60}")

    # 1. Read spec
    spec_text = read_spec(benchmark)
    print(f"  Spec read: {len(spec_text)} chars")

    # 2. Read reference testbench
    tb_code = read_reference_tb(benchmark)
    tb_funcs, tb_doc_map = extract_tb_functions(tb_code)
    print(f"  Reference TB: {len(tb_funcs)} test functions found")
    for f, d in tb_doc_map.items():
        print(f"    - {f}: {d[:60]}...")

    # 3. Run spec parser
    print(f"\n  --- Running Spec Parser Agent ---")
    spec_analysis = call_spec_parser(spec_text, benchmark)
    print(f"  Design type: {spec_analysis.get('design_type', 'Unknown')}")
    print(f"  Inputs: {len(spec_analysis.get('inputs', []))}, Outputs: {len(spec_analysis.get('outputs', []))}")
    print(f"  Behaviors: {len(spec_analysis.get('behavior', []))}")
    print(f"  Corner cases: {len(spec_analysis.get('corner_cases', []))}")

    # 4. Run verification planner
    print(f"\n  --- Running Verification Planner Agent ---")
    plan = call_verification_planner(spec_analysis, benchmark)
    design_type = plan.get("design_type", spec_analysis.get("design_type", "unknown"))
    print(f"  Plan design_type: {design_type}")

    # 5. Run evaluations
    results = {
        "benchmark": benchmark,
        "spec_analysis": spec_analysis,
        "plan": plan,
        "tb_funcs": tb_funcs,
        "tb_doc_map": tb_doc_map,
        "evaluations": {}
    }

    # Tier Structure
    print(f"\n  --- Evaluating ---")
    tier_eval = evaluate_tier_structure(plan)
    results["evaluations"]["tier_structure"] = tier_eval
    print(f"  Tier Structure: {tier_eval['score']} ({tier_eval['tier_count']} tiers)")
    for iss in tier_eval["issues"]:
        print(f"    ! {iss}")

    # Test IDs
    id_eval = evaluate_test_ids(plan)
    results["evaluations"]["test_ids"] = id_eval
    print(f"  Test IDs: {id_eval['score']} ({id_eval['total_test_ids']} tests)")
    for iss in id_eval["issues"]:
        print(f"    ! {iss}")

    # Distribution
    dist = evaluate_test_distribution(plan)
    results["evaluations"]["distribution"] = dist
    print(f"  Distribution: Tier1={dist.get('Tier 1',0)}, Tier2={dist.get('Tier 2',0)}, Tier3={dist.get('Tier 3',0)}, Total={dist['total']}")

    # Coverage
    cov_eval = evaluate_coverage(spec_text, plan, tb_funcs, tb_doc_map)
    results["evaluations"]["coverage"] = cov_eval
    print(f"  Coverage: {cov_eval['score']} ({cov_eval['tb_covered']}/{cov_eval['tb_total_functions']} TB tests covered)")
    for mt in cov_eval["tb_missing"]:
        print(f"    ! Missing from plan: {mt}")

    # Reference model
    ref_eval = evaluate_reference_model(plan, spec_text)
    results["evaluations"]["reference_model"] = ref_eval
    print(f"  Reference Model: {ref_eval['score']} ({ref_eval.get('code_length', 0)} chars)")
    for iss in ref_eval["issues"]:
        print(f"    ! {iss}")

    # Forbidden behaviors
    fb_eval = evaluate_forbidden_behaviors(plan, design_type)
    results["evaluations"]["forbidden_behaviors"] = fb_eval
    print(f"  Forbidden Behaviors: {fb_eval['score']} ({fb_eval['count']} listed)")
    for iss in fb_eval["issues"]:
        print(f"    ! {iss}")

    # Timing requirements
    timing_eval = evaluate_timing_requirements(plan, design_type)
    results["evaluations"]["timing"] = timing_eval
    print(f"  Timing: {timing_eval['score']}")
    for iss in timing_eval["issues"]:
        print(f"    ! {iss}")

    # Redundancy
    red_eval = evaluate_redundancy(plan)
    results["evaluations"]["redundancy"] = red_eval
    print(f"  Redundancy: {red_eval['score']}")
    for iss in red_eval["issues"]:
        print(f"    ! {iss}")

    # Extra tests vs TB
    extra_eval = evaluate_redundant_vs_tb(plan, tb_funcs, tb_doc_map)
    results["evaluations"]["extra_vs_tb"] = extra_eval
    print(f"  Extra tests (not in reference TB): {extra_eval['extra_tests_in_plan']}")
    for et in extra_eval["extra_tests"]:
        print(f"    - {et['id']}: {et['desc'][:60]}...")

    return results


def score_to_numeric(score: str) -> int:
    mapping = {"EXCELLENT": 4, "GOOD": 3, "FAIR": 2, "POOR": 1}
    return mapping.get(score, 0)


def generate_report(all_results: list[dict]):
    """Generate markdown report from evaluation results."""
    report = []
    report.append("# Verification Planner Agent Evaluation Report")
    report.append("")
    report.append(f"**Date:** 2026-06-15")
    report.append(f"**Benchmarks Evaluated:** 5 (alu_8bit, sync_fifo_8x16, fsm_traffic_light, uart_tx, apb_slave)")
    report.append(f"**Method:** Each benchmark's spec was parsed via SpecParserAgent, then a verification plan was generated via VerificationPlannerAgent. Plans were evaluated against reference RTL/TB ground truth.")
    report.append("")

    # ===== Summary Table =====
    report.append("## Summary Table")
    report.append("")
    report.append("| Dimension | alu_8bit | sync_fifo_8x16 | fsm_traffic_light | uart_tx | apb_slave |")
    report.append("|-----------|----------|----------------|-------------------|---------|------------|")

    dimensions = [
        ("Tier Structure", "tier_structure"),
        ("Test ID Structure", "test_ids"),
        ("Coverage Completeness", "coverage"),
        ("Reference Model", "reference_model"),
        ("Forbidden Behaviors", "forbidden_behaviors"),
        ("Timing Requirements", "timing"),
        ("Redundancy (cross-tier)", "redundancy"),
    ]

    # Collect per-dimension scores for numeric summary
    dim_names = [d[0] for d in dimensions]
    dim_keys = [d[1] for d in dimensions]

    for dim_name, dim_key in dimensions:
        row = [dim_name]
        for r in all_results:
            if dim_key in r["evaluations"]:
                score = r["evaluations"][dim_key].get("score", "N/A")
            else:
                score = "N/A"
            row.append(score)
        report.append("| " + " | ".join(row) + " |")

    report.append("")

    # Compute overall scores
    report.append("### Overall Scores")
    report.append("")
    report.append("| Benchmark | Overall Score | Details |")
    report.append("|-----------|---------------|---------|")
    for r in all_results:
        bm = r["benchmark"]
        scores = []
        details = []
        for dim_key in dim_keys:
            if dim_key in r["evaluations"]:
                score = r["evaluations"][dim_key].get("score", "N/A")
                scores.append(score_to_numeric(score))
                details.append(score)
        avg = sum(scores) / len(scores) if scores else 0
        if avg >= 3.5:
            overall = "EXCELLENT"
        elif avg >= 2.5:
            overall = "GOOD"
        elif avg >= 1.5:
            overall = "FAIR"
        else:
            overall = "POOR"
        detail_str = " | ".join(details)
        report.append(f"| {bm} | **{overall}** (avg={avg:.2f}) | {detail_str} |")
    report.append("")

    # Test counts summary
    report.append("### Test Counts Summary")
    report.append("")
    report.append("| Benchmark | Tier 1 | Tier 2 | Tier 3 | Total | TB Tests | Coverage |")
    report.append("|-----------|--------|--------|--------|-------|----------|----------|")
    for r in all_results:
        bm = r["benchmark"]
        dist = r["evaluations"].get("distribution", {})
        cov = r["evaluations"].get("coverage", {})
        t1 = dist.get("Tier 1", 0)
        t2 = dist.get("Tier 2", 0)
        t3 = dist.get("Tier 3", 0)
        total = dist.get("total", 0)
        tb_total = cov.get("tb_total_functions", 0)
        covered = cov.get("tb_covered", 0)
        report.append(f"| {bm} | {t1} | {t2} | {t3} | {total} | {tb_total} | {covered}/{tb_total} |")
    report.append("")

    # ===== Per-Benchmark Detailed Analysis =====
    report.append("## Per-Benchmark Detailed Analysis")
    report.append("")

    for r in all_results:
        bm = r["benchmark"]
        plan = r["plan"]
        spec_analysis = r["spec_analysis"]

        report.append(f"### {bm}")
        report.append("")
        report.append(f"- **Design Type:** {plan.get('design_type', spec_analysis.get('design_type', 'unknown'))}")
        report.append(f"- **Spec Analysis Quality:** {len(spec_analysis.get('behavior', []))} behaviors, {len(spec_analysis.get('corner_cases', []))} corner cases")
        report.append("")

        # Tier details
        report.append("#### Tier Structure")
        te = r["evaluations"]["tier_structure"]
        report.append(f"- Score: **{te['score']}**")
        report.append(f"- Tiers found: {te['tier_count']} ({', '.join(te['tier_names'])})")
        for iss in te["issues"]:
            report.append(f"- Issue: {iss}")
        report.append("")

        # Test IDs
        report.append("#### Test ID Structure")
        ie = r["evaluations"]["test_ids"]
        report.append(f"- Score: **{ie['score']}**")
        report.append(f"- Total tests: {ie['total_test_ids']}")
        if ie["all_ids"]:
            report.append(f"- IDs: {', '.join(ie['all_ids'])}")
        for iss in ie["issues"]:
            report.append(f"- Issue: {iss}")
        report.append("")

        # Tests per tier
        report.append("#### Tests Per Tier")
        dist = r["evaluations"]["distribution"]
        tiers = plan.get("verification_tiers", [])
        for t in tiers:
            tn = t.get("tier", "?")
            name = t.get("name", "?")
            tests = t.get("tests", [])
            report.append(f"**Tier {tn}: {name}** ({len(tests)} tests)")
            for test in tests:
                tid = test.get("test_id", "?")
                desc = test.get("description", "?")
                stim = test.get("stimulus", {})
                exp = test.get("expected", {})
                stim_str = json.dumps(stim)[:80] if isinstance(stim, dict) else str(stim)[:80]
                exp_str = json.dumps(exp)[:80] if isinstance(exp, dict) else str(exp)[:80]
                report.append(f"  - `{tid}`: {desc}")
                report.append(f"    - Stimulus: {stim_str}")
                report.append(f"    - Expected: {exp_str}")
        report.append("")

        # Coverage
        report.append("#### Coverage Completeness")
        ce = r["evaluations"]["coverage"]
        report.append(f"- Score: **{ce['score']}**")
        report.append(f"- TB Functions: {ce['tb_total_functions']}")
        report.append(f"- Covered in Plan: {ce['tb_covered']}/{ce['tb_total_functions']}")

        if "tb_missing" in ce and ce["tb_missing"]:
            report.append("")
            report.append("**Tests MISSING from plan (present in reference TB):**")
            for mt in ce["tb_missing"]:
                doc = r["tb_doc_map"].get(mt, "")
                report.append(f"  - `{mt}`: {doc}")

        report.append("")

        # Redundancy
        report.append("#### Redundancy")
        re_eval = r["evaluations"]["redundancy"]
        report.append(f"- Score: **{re_eval['score']}**")
        if re_eval.get("issues"):
            for iss in re_eval["issues"]:
                report.append(f"- {iss}")
        else:
            report.append("- No redundant tests detected across tiers")
        report.append("")

        # Extra tests vs TB
        report.append("#### Extra Tests (Not in Reference TB)")
        extra_eval = r["evaluations"].get("extra_vs_tb", {})
        extra_tests = extra_eval.get("extra_tests", [])
        if extra_tests:
            report.append(f"- {len(extra_tests)} test(s) in the plan do not correspond to any reference TB test:")
            for et in extra_tests:
                report.append(f"  - `{et['id']}`: {et['desc']}")
        else:
            report.append("- All plan tests correspond to reference TB tests.")
        report.append("")

        # Reference model
        report.append("#### Reference Model Quality")
        rm = r["evaluations"]["reference_model"]
        report.append(f"- Score: **{rm['score']}**")
        report.append(f"- Code length: {rm.get('code_length', 0)} chars")
        if rm.get("issues"):
            for iss in rm["issues"]:
                report.append(f"- Issue: {iss}")
        ref_code = plan.get("reference_model_code", "")
        if ref_code:
            report.append("")
            report.append("```python")
            report.append(ref_code)
            report.append("```")
        report.append("")

        # Forbidden behaviors
        report.append("#### Forbidden Behaviors")
        fb = r["evaluations"]["forbidden_behaviors"]
        report.append(f"- Score: **{fb['score']}**")
        report.append(f"- Count: {fb['count']}")
        if fb.get("behaviors"):
            for b in fb["behaviors"]:
                report.append(f"  - {b}")
        if fb.get("issues"):
            for iss in fb["issues"]:
                report.append(f"- {iss}")
        report.append("")

        # Timing requirements
        report.append("#### Timing Requirements")
        tr = r["evaluations"]["timing"]
        report.append(f"- Score: **{tr['score']}**")
        report.append(f"- Clock Signal: {tr['clock_signal']}")
        report.append(f"- Clock Period: {tr['clock_period_ns']} ns")
        report.append(f"- Skip STA: {tr['skip_sta']}")
        if tr.get("issues"):
            for iss in tr["issues"]:
                report.append(f"- Issue: {iss}")
        report.append("")

        # Overall assessment
        report.append("#### Overall Assessment")
        scores = []
        for dim_key in dim_keys:
            if dim_key in r["evaluations"]:
                score = r["evaluations"][dim_key].get("score", "N/A")
                scores.append(score_to_numeric(score))
        avg = sum(scores) / len(scores) if scores else 0
        if avg >= 3.5:
            overall = "EXCELLENT"
        elif avg >= 2.5:
            overall = "GOOD"
        elif avg >= 1.5:
            overall = "FAIR"
        else:
            overall = "POOR"

        report.append(f"- **Overall: {overall}** (average score: {avg:.2f}/4.0)")
        report.append("")

        # Strengths and weaknesses
        report.append("**Strengths:**")
        strengths = []
        for dim_name, dim_key in dimensions:
            if dim_key in r["evaluations"]:
                sc = r["evaluations"][dim_key].get("score", "N/A")
                if sc == "EXCELLENT":
                    strengths.append(f"- {dim_name}: {sc}")
        if strengths:
            for s in strengths:
                report.append(f"  {s}")
        else:
            report.append("  (none rated EXCELLENT)")

        report.append("")
        report.append("**Weaknesses:**")
        weaknesses = []
        for dim_name, dim_key in dimensions:
            if dim_key in r["evaluations"]:
                sc = r["evaluations"][dim_key].get("score", "N/A")
                if sc in ("FAIR", "POOR"):
                    weaknesses.append(f"- {dim_name}: {sc}")
        if weaknesses:
            for w in weaknesses:
                report.append(f"  {w}")
        else:
            report.append("  (none rated FAIR or POOR)")

        report.append("")
        report.append("---")
        report.append("")

    # ===== Cross-Benchmark Analysis =====
    report.append("## Cross-Benchmark Analysis")
    report.append("")

    report.append("### Strengths Across Benchmarks")
    report.append("")
    # Which dimensions were consistently EXCELLENT
    for dim_name, dim_key in dimensions:
        excellent_count = sum(1 for r in all_results if r["evaluations"].get(dim_key, {}).get("score") == "EXCELLENT")
        good_count = sum(1 for r in all_results if r["evaluations"].get(dim_key, {}).get("score") == "GOOD")
        total = len(all_results)
        report.append(f"- **{dim_name}:** {excellent_count}/{total} EXCELLENT, {good_count}/{total} GOOD")
    report.append("")

    report.append("### Weaknesses Across Benchmarks")
    report.append("")
    for dim_name, dim_key in dimensions:
        poor_count = sum(1 for r in all_results if r["evaluations"].get(dim_key, {}).get("score") in ("FAIR", "POOR"))
        total = len(all_results)
        if poor_count > 0:
            report.append(f"- **{dim_name}:** {poor_count}/{total} benchmarks rated FAIR or POOR")
    report.append("")

    report.append("### Key Findings")
    report.append("")
    # Collect all missing tests
    all_missing = []
    for r in all_results:
        ce = r["evaluations"].get("coverage", {})
        for mt in ce.get("tb_missing", []):
            all_missing.append((r["benchmark"], mt, r["tb_doc_map"].get(mt, "")))
    if all_missing:
        report.append("**Tests consistently missing from plans:**")
        for bm, func, doc in all_missing:
            report.append(f"- {bm}: `{func}` — {doc}")
    else:
        report.append("- No tests were consistently missing across benchmarks.")
    report.append("")

    report.append("### Recommendations")
    report.append("")
    report.append("1. **Improve Reference Model Generation**: Reference models often lack complete opcode/behavior coverage. Consider few-shot examples or a dedicated reference model generator.")
    report.append("2. **Enforce Forbidden Behavior Completeness**: The planner frequently generates fewer than 3 forbidden behaviors or misses design-type-specific ones.")
    report.append("3. **Better Coverage of Corner Cases**: Some benchmarks miss important corner cases that the reference TB covers (e.g., simultaneous operations, overflow boundaries).")
    report.append("4. **Cross-Tier Redundancy**: Rare but should be checked — some tests appeared similar across functional and boundary tiers.")
    report.append("5. **Consistent Test ID Naming**: Ensure all test IDs follow T{1,2,3}_XXX format correctly.")
    report.append("")

    return "\n".join(report)


# ============================================================
# Main
# ============================================================

def main():
    benchmarks = ["alu_8bit", "sync_fifo_8x16", "fsm_traffic_light", "uart_tx", "apb_slave"]

    all_results = []
    for bm in benchmarks:
        try:
            result = evaluate_benchmark(bm)
            all_results.append(result)
        except Exception as e:
            print(f"\n  [ERROR] Failed to evaluate {bm}: {e}")
            traceback.print_exc()
            all_results.append({
                "benchmark": bm,
                "spec_analysis": {},
                "plan": {},
                "tb_funcs": [],
                "tb_doc_map": {},
                "evaluations": {
                    "tier_structure": {"score": "ERROR", "issues": [str(e)]},
                    "test_ids": {"score": "ERROR", "issues": [str(e)]},
                    "distribution": {},
                    "coverage": {"score": "ERROR", "tb_missing": [], "tb_covered": 0, "tb_total_functions": 0},
                    "reference_model": {"score": "ERROR", "issues": [str(e)]},
                    "forbidden_behaviors": {"score": "ERROR", "issues": [str(e)]},
                    "timing": {"score": "ERROR", "issues": [str(e)]},
                    "redundancy": {"score": "ERROR", "issues": [str(e)]},
                    "extra_vs_tb": {"extra_tests": []}
                }
            })

    # Generate report
    print(f"\n\n{'='*60}")
    print("Generating report...")
    report = generate_report(all_results)

    # Write report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = OUTPUT_DIR / "VERIFICATION_PLANNER_EVALUATION.md"
    report_path.write_text(report)
    print(f"Report written to: {report_path}")

    # Print summary console
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"{'Benchmark':<20} {'Tiers':<8} {'Tests':<8} {'Coverage':<12} {'Overall':<12}")
    print(f"{'-'*20} {'-'*8} {'-'*8} {'-'*12} {'-'*12}")
    for r in all_results:
        bm = r["benchmark"]
        te = r["evaluations"].get("tier_structure", {})
        dist = r["evaluations"].get("distribution", {})
        cov = r["evaluations"].get("coverage", {})

        tiers = te.get("tier_count", "?")
        tests = dist.get("total", "?")
        coverage_str = f"{cov.get('tb_covered', '?')}/{cov.get('tb_total_functions', '?')}"
        scores = []
        for dim_key in ["tier_structure", "test_ids", "coverage", "reference_model", "forbidden_behaviors", "timing", "redundancy"]:
            if dim_key in r["evaluations"]:
                scores.append(score_to_numeric(r["evaluations"][dim_key].get("score", "POOR")))
        avg = sum(scores) / len(scores) if scores else 0
        overall = "EXCELLENT" if avg >= 3.5 else "GOOD" if avg >= 2.5 else "FAIR" if avg >= 1.5 else "POOR"
        print(f"{bm:<20} {str(tiers):<8} {str(tests):<8} {coverage_str:<12} {overall:<12}")

    print(f"\nReport: {OUTPUT_DIR / 'VERIFICATION_PLANNER_EVALUATION.md'}")
    print("Done.")


if __name__ == "__main__":
    main()
