"""
Batch bug injection campaign runner.
Runs all 10 bug files through the V2 pipeline and collects structured results.
"""

import subprocess
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_FILE = PROJECT_ROOT / "docs" / "bug_injection_raw_data.json"

BUGS = [
    # (benchmark_name, bug_file_path)
    ("alu_8bit", "benchmarks/alu_8bit/bugs/bug_001_wrong_opcode.v"),
    ("alu_8bit", "benchmarks/alu_8bit/bugs/bug_002_missing_zero_flag.v"),
    ("sync_fifo_8x16", "benchmarks/sync_fifo_8x16/bugs/bug_001_wrong_full_flag.v"),
    ("sync_fifo_8x16", "benchmarks/sync_fifo_8x16/bugs/bug_002_no_reset.v"),
    ("fsm_traffic_light", "benchmarks/fsm_traffic_light/bugs/bug_001_wrong_count.v"),
    ("fsm_traffic_light", "benchmarks/fsm_traffic_light/bugs/bug_002_wrong_transition.v"),
    ("uart_tx", "benchmarks/uart_tx/bugs/bug_001_wrong_bit_order.v"),
    ("uart_tx", "benchmarks/uart_tx/bugs/bug_002_missing_stop_bit.v"),
    ("apb_slave", "benchmarks/apb_slave/bugs/bug_001_wrong_address.v"),
    ("apb_slave", "benchmarks/apb_slave/bugs/bug_002_pslverr_inverted.v"),
]

# Bug type descriptions from file headers
BUG_DESCRIPTIONS = {
    "alu_8bit/bug_001_wrong_opcode.v": "XOR operation changed to XNOR",
    "alu_8bit/bug_002_missing_zero_flag.v": "zero_flag output never assigned",
    "sync_fifo_8x16/bug_001_wrong_full_flag.v": "full threshold at 15 instead of 16",
    "sync_fifo_8x16/bug_002_no_reset.v": "rst_n removed from all sequential blocks",
    "fsm_traffic_light/bug_001_wrong_count.v": "RED_COUNT changed from 15 to 10",
    "fsm_traffic_light/bug_002_wrong_transition.v": "GREEN→RED and YELLOW→GREEN swapped",
    "uart_tx/bug_001_wrong_bit_order.v": "MSB-first instead of LSB-first",
    "uart_tx/bug_002_missing_stop_bit.v": "DATA→IDLE skip, no stop bit",
    "apb_slave/bug_001_wrong_address.v": "PADDR[4:3] instead of [3:2] for decode",
    "apb_slave/bug_002_pslverr_inverted.v": "PSLVERR asserts on valid addresses",
}

# Bug category classifications
BUG_CLASSIFICATION = {
    "alu_8bit/bug_001_wrong_opcode.v": "Logic Bug",
    "alu_8bit/bug_002_missing_zero_flag.v": "Interface Bug",
    "sync_fifo_8x16/bug_001_wrong_full_flag.v": "Boundary Condition Bug",
    "sync_fifo_8x16/bug_002_no_reset.v": "RTL Coding Bug (no reset)",
    "fsm_traffic_light/bug_001_wrong_count.v": "Logic Bug",
    "fsm_traffic_light/bug_002_wrong_transition.v": "Logic Bug",
    "uart_tx/bug_001_wrong_bit_order.v": "Interface Bug",
    "uart_tx/bug_002_missing_stop_bit.v": "Logic Bug",
    "apb_slave/bug_001_wrong_address.v": "Interface Bug",
    "apb_slave/bug_002_pslverr_inverted.v": "Logic Bug",
}


def parse_output(output: str) -> dict:
    """Parse pipeline output for key metrics."""
    result = {}

    # Pipeline completion
    result["pipeline_complete"] = "Pipeline COMPLETE" in output
    result["pipeline_halted"] = "Pipeline HALTED" in output

    # Simulation pass — look for explicit completion marker
    result["sim_passed"] = "Pipeline COMPLETE" in output and "passed simulation" in output

    # Timing
    result["timing_met"] = None
    if "Timing CLOSED" in output:
        result["timing_met"] = True
    elif "Timing NOT closed" in output:
        result["timing_met"] = False

    # WNS
    wns_match = re.search(r"WNS=([\d.-]+)", output)
    if wns_match:
        try:
            result["wns"] = float(wns_match.group(1))
        except ValueError:
            result["wns"] = wns_match.group(1)
    else:
        result["wns"] = None

    # Iterations
    iter_match = re.search(r"iteration['\"]?:\s*(\d+)", output)
    if iter_match:
        result["iterations"] = int(iter_match.group(1))
    elif "0 iteration" in output:
        result["iterations"] = 0
    else:
        # Count fix loop mentions
        fix_mentions = len(re.findall(r"Attempting fix", output))
        result["iterations"] = fix_mentions

    # Stuck count
    stuck_match = re.search(r"stuck_count['\"]?:\s*(\d+)", output)
    result["stuck_count"] = int(stuck_match.group(1)) if stuck_match else 0

    # Error type
    error_type_match = re.search(r"Error classified as:\s*(\w+)", output)
    if error_type_match:
        result["error_type"] = error_type_match.group(1)
    elif re.search(r"ERROR_TYPE\s*[=:]\s*(\w+)", output):
        error_type_match2 = re.search(r"ERROR_TYPE\s*[=:]\s*(\w+)", output)
        result["error_type"] = error_type_match2.group(1)
    else:
        result["error_type"] = "NONE"

    # Synthesis
    result["synthesis_success"] = "Synthesis produced netlist" in output or "netlist_path" in output
    result["synthesis_failed"] = "Synthesis produced no valid netlist" in output

    # Cells and area
    cells_match = re.search(r"cell_count['\"]?:\s*(\d+)", output)
    result["cells"] = int(cells_match.group(1)) if cells_match else None

    area_match = re.search(r"area['\"]?:\s*([\d.]+)", output)
    result["area"] = float(area_match.group(1)) if area_match else None

    # Convergence
    result["convergence_triggered"] = "stuck at same error" in output or "convergence" in output.lower()

    # Fix attempted
    result["fix_attempted"] = "Attempting fix" in output or "fix_applied" in output or "FixAgent" in output

    # Determine if fixed
    result["fixed"] = result.get("sim_passed", False)

    # Errors in output
    result["has_errors"] = "Error" in output or "CRASHED" in output or "Traceback" in output

    # Log analysis performed
    result["log_analysis_done"] = "Analyzing simulation log" in output or "Error classified" in output

    return result


def run_bug_test(benchmark: str, bug_file: str) -> dict:
    """Run a single bug test through the V2 pipeline."""
    bug_key = bug_file.replace("benchmarks/", "")

    cmd = [
        sys.executable, "main.py",
        "--benchmark", benchmark,
        "--rtl", bug_file,
        "--v2"
    ]

    print(f"\n{'='*80}")
    print(f"Testing: {benchmark} - {bug_key}")
    print(f"Bug: {BUG_DESCRIPTIONS.get(bug_key, 'Unknown')}")
    print(f"{'='*80}")

    start_time = time.time()

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
            env=None  # inherit env
        )
        elapsed = time.time() - start_time
        output = proc.stdout + "\n" + proc.stderr
        exit_code = proc.returncode

        print(f"Exit code: {exit_code}")
        print(f"Elapsed: {elapsed:.1f}s")

        parsed = parse_output(output)
        parsed["exit_code"] = exit_code
        parsed["elapsed_seconds"] = round(elapsed, 1)
        parsed["sim_passed"] = parsed.get("sim_passed", False) or ("sim_passed" in output and "sim_passed', True" in output)

        # If no explicit sim_passed marker, check full output
        if not parsed.get("sim_passed"):
            # Check for actual test pass indicators
            if "PASS" in output and "SIMULATION" in output:
                parsed["sim_passed"] = True

        print(f"  sim_passed={parsed.get('sim_passed')}, "
              f"error_type={parsed.get('error_type', 'N/A')}, "
              f"iterations={parsed.get('iterations', 0)}, "
              f"timing_met={parsed.get('timing_met', 'N/A')}")

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"TIMEOUT after {elapsed:.1f}s")
        output = f"TIMEOUT after {elapsed:.1f}s"
        parsed = {
            "exit_code": -1,
            "elapsed_seconds": round(elapsed, 1),
            "pipeline_complete": False,
            "sim_passed": False,
            "timing_met": None,
            "wns": None,
            "iterations": 0,
            "stuck_count": 0,
            "error_type": "TIMEOUT",
            "synthesis_success": False,
            "cells": None,
            "area": None,
            "convergence_triggered": False,
            "fix_attempted": False,
            "fixed": False,
            "has_errors": True,
            "log_analysis_done": False,
        }

    result = {
        "benchmark": benchmark,
        "bug_file": bug_key,
        "bug_description": BUG_DESCRIPTIONS.get(bug_key, "Unknown"),
        "bug_classification": BUG_CLASSIFICATION.get(bug_key, "Unknown"),
        "timestamp": datetime.now().isoformat(),
        **parsed,
        "full_output": output[-3000:]  # Last 3000 chars for analysis
    }

    return result


def main():
    results = []
    start_time = datetime.now()

    print(f"Bug Injection Campaign — {len(BUGS)} tests")
    print(f"Start time: {start_time.isoformat()}")
    print(f"Project root: {PROJECT_ROOT}")

    for benchmark, bug_file in BUGS:
        result = run_bug_test(benchmark, bug_file)
        results.append(result)

        # Save incrementally
        campaign_data = {
            "campaign_start": start_time.isoformat(),
            "campaign_end": None,
            "total_tests": len(BUGS),
            "results": results
        }

        RESULTS_FILE.parent.mkdir(exist_ok=True)
        with open(RESULTS_FILE, "w") as f:
            json.dump(campaign_data, f, indent=2)

        print(f"  → Saved to {RESULTS_FILE}")

    # Final save
    end_time = datetime.now()
    campaign_data = {
        "campaign_start": start_time.isoformat(),
        "campaign_end": end_time.isoformat(),
        "total_tests": len(BUGS),
        "total_duration_seconds": (end_time - start_time).total_seconds(),
        "summary": {
            "total_pass": sum(1 for r in results if r.get("sim_passed")),
            "total_fail": sum(1 for r in results if not r.get("sim_passed")),
            "timing_met": sum(1 for r in results if r.get("timing_met")),
            "fix_attempted": sum(1 for r in results if r.get("fix_attempted")),
            "fix_succeeded": sum(1 for r in results if r.get("fixed")),
        },
        "results": results
    }

    with open(RESULTS_FILE, "w") as f:
        json.dump(campaign_data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"CAMPAIGN COMPLETE")
    print(f"Passed: {campaign_data['summary']['total_pass']}/{len(BUGS)}")
    print(f"Failed: {campaign_data['summary']['total_fail']}/{len(BUGS)}")
    print(f"Timing met: {campaign_data['summary']['timing_met']}")
    print(f"Fix attempted: {campaign_data['summary']['fix_attempted']}")
    print(f"Fix succeeded: {campaign_data['summary']['fix_succeeded']}")
    print(f"Duration: {campaign_data['total_duration_seconds']:.1f}s")
    print(f"Results: {RESULTS_FILE}")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
