"""
Spec → RTL Generation Campaign (v2).
Runs the full V2 pipeline WITHOUT any reference files, forcing pure AI generation.
Uses --spec directly to bypass auto-detection of reference RTL/TB.
"""

import subprocess
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
RESULTS_FILE = PROJECT_ROOT / "docs" / "spec_to_rtl_raw_data.json"

BENCHMARK_SPECS = {
    "alu_8bit": ("8-bit ALU with 8-bit inputs A and B, 3-bit opcode, 8-bit output Y and 1-bit zero_flag. "
                 "Operations: 000=ADD, 001=SUB, 010=AND, 011=OR, 100=XOR, 101=NOT A, 110=SHL A by 1, 111=SHR A by 1. "
                 "zero_flag asserts when Y==0. Combinational, no clock."),
    "sync_fifo_8x16": ("Synchronous FIFO module sync_fifo_8x16. Depth=16, Width=8 bits. "
                       "Inputs: clk, rst_n, wr_en, rd_en, din[7:0]. Outputs: dout[7:0], full, empty. "
                       "Write on rising edge when wr_en=1 and full=0. Read on rising edge when rd_en=1 and empty=0. "
                       "full asserts at 16 entries, empty at 0. Active-low synchronous reset. Sequential design."),
    "fsm_traffic_light": ("3-state Traffic Light FSM module fsm_traffic_light. "
                          "Inputs: clk, rst_n. Outputs: red_light, green_light, yellow_light (all 1-bit), state_out (2-bit). "
                          "States: RED(00), GREEN(01), YELLOW(10). "
                          "RED duration=15 cycles, GREEN=20, YELLOW=5. "
                          "Asynchronous active-low reset. FSM loops RED→GREEN→YELLOW→RED."),
    "uart_tx": ("UART Transmitter module uart_tx. "
                "Inputs: clk, rst_n, tx_start, tx_data[7:0], baud_div[15:0]. Outputs: tx, tx_busy. "
                "Frame: 1 start bit (low), 8 data bits LSB first, 1 stop bit (high). "
                "tx_busy=1 during transmission. baud_div sets cycles per bit. "
                "Synchronous active-low reset. FSM: IDLE→START→DATA→STOP→IDLE."),
    "apb_slave": ("APB Slave module apb_slave with 4 32-bit registers. "
                  "Inputs: PCLK, PRESETn, PSEL, PENABLE, PWRITE, PADDR[7:0], PWDATA[31:0]. "
                  "Outputs: PRDATA[31:0], PREADY, PSLVERR. "
                  "Registers at 0x00, 0x04, 0x08, 0x0C (word-aligned). "
                  "Write when PSEL=1 & PENABLE=1 & PWRITE=1. Read when PSEL=1 & PENABLE=1 & PWRITE=0. "
                  "PREADY always 1. PSLVERR=1 on invalid address. Synchronous active-low reset. Sequential/protocol design."),
}


def parse_output(output: str) -> dict:
    result = {}
    result["pipeline_complete"] = "Pipeline COMPLETE" in output
    result["sim_passed"] = "Pipeline COMPLETE" in output and "passed simulation" in output
    result["timing_met"] = True if "Timing CLOSED" in output else (False if "Timing NOT closed" in output else None)

    wns_match = re.search(r"WNS=([-\d.]+)", output)
    result["wns"] = float(wns_match.group(1)) if wns_match else None

    fix_matches = re.findall(r"Attempting fix", output)
    result["iterations"] = len(fix_matches)

    error_types = re.findall(r"Error classified as:\s*(\w+)", output)
    result["error_type"] = error_types[-1] if error_types else "NONE"

    result["synthesis_success"] = "Synthesis produced netlist" in output
    cells_match = re.search(r"cell_count['\"]?:\s*(\d+)", output)
    result["cells"] = int(cells_match.group(1)) if cells_match else None

    area_match = re.search(r"area['\"]?:\s*([\d.]+)", output)
    result["area"] = float(area_match.group(1)) if area_match else None

    result["spec_parsed"] = "Spec parsed" in output
    result["plan_generated"] = "Plan generated" in output
    result["rtl_generated"] = "RTL generated" in output
    result["tb_generated"] = "Testbench generated" in output
    result["fix_attempted"] = "Attempting fix" in output
    result["convergence_triggered"] = "stuck at same error" in output
    result["agent_crashed"] = "crashed" in output.lower()

    return result


def run_benchmark(benchmark: str, spec: str) -> dict:
    """Run pipeline with --spec (forces AI generation, no reference auto-detect)."""
    cmd = [sys.executable, "main.py", "--spec", spec, "--name", benchmark, "--v2"]

    print(f"\n{'='*80}")
    print(f"Spec → RTL: {benchmark}")
    print(f"  Mode: Pure AI (no reference RTL/TB)")
    print(f"{'='*80}")

    start_time = time.time()

    try:
        proc = subprocess.run(
            cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True,
            timeout=300, env=None
        )
        elapsed = time.time() - start_time
        output = proc.stdout + "\n" + proc.stderr
        exit_code = proc.returncode

        print(f"Exit: {exit_code} | Elapsed: {elapsed:.1f}s")

        parsed = parse_output(output)
        parsed["exit_code"] = exit_code
        parsed["elapsed_seconds"] = round(elapsed, 1)

        for key in ["sim_passed", "iterations", "error_type", "spec_parsed",
                     "plan_generated", "rtl_generated", "tb_generated",
                     "synthesis_success", "cells", "area", "timing_met"]:
            val = parsed.get(key)
            if val is not None:
                print(f"  {key}: {val}")

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        print(f"TIMEOUT after {elapsed:.1f}s")
        output = f"TIMEOUT after {elapsed:.1f}s"
        parsed = {
            "exit_code": -1, "elapsed_seconds": round(elapsed, 1),
            "pipeline_complete": False, "sim_passed": False,
            "timing_met": None, "wns": None, "iterations": 0,
            "error_type": "TIMEOUT",
            "synthesis_success": False, "cells": None, "area": None,
            "spec_parsed": False, "plan_generated": False,
            "rtl_generated": False, "tb_generated": False,
            "fix_attempted": False, "convergence_triggered": False,
            "agent_crashed": False,
        }

    result = {
        "benchmark": benchmark,
        "timestamp": datetime.now().isoformat(),
        "mode": "spec_to_rtl_pure_ai",
        "rtl_source": "ai_generated",
        "tb_source": "ai_generated",
        **parsed,
        "full_output": output[-3000:],
    }
    return result


def main():
    results = []
    start_time = datetime.now()

    print(f"=== Spec → RTL Generation Campaign (Pure AI) ===")
    print(f"Start: {start_time.isoformat()}")
    print(f"Benchmarks: {', '.join(BENCHMARK_SPECS.keys())}")
    print(f"Mode: --spec only, no reference files")
    print()

    for benchmark, spec_text in BENCHMARK_SPECS.items():
        result = run_benchmark(benchmark, spec_text)
        results.append(result)

        data = {
            "campaign_start": start_time.isoformat(),
            "campaign_end": None,
            "total_benchmarks": len(BENCHMARK_SPECS),
            "mode": "spec_to_rtl_pure_ai",
            "results": results,
        }
        RESULTS_FILE.parent.mkdir(exist_ok=True)
        with open(RESULTS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    end_time = datetime.now()
    passed = sum(1 for r in results if r.get("sim_passed"))
    rtl_gen_count = sum(1 for r in results if r.get("rtl_generated"))
    tb_gen_count = sum(1 for r in results if r.get("tb_generated"))

    data = {
        "campaign_start": start_time.isoformat(),
        "campaign_end": end_time.isoformat(),
        "total_duration_seconds": (end_time - start_time).total_seconds(),
        "total_benchmarks": len(BENCHMARK_SPECS),
        "mode": "spec_to_rtl_pure_ai",
        "summary": {
            "passed": passed,
            "failed": len(BENCHMARK_SPECS) - passed,
            "pass_rate": f"{passed}/{len(BENCHMARK_SPECS)} ({passed/len(BENCHMARK_SPECS)*100:.0f}%)",
            "synthesis_success": sum(1 for r in results if r.get("synthesis_success")),
            "timing_met": sum(1 for r in results if r.get("timing_met")),
            "fix_attempted": sum(1 for r in results if r.get("fix_attempted")),
            "convergence_events": sum(1 for r in results if r.get("convergence_triggered")),
            "first_pass_success": sum(1 for r in results if r.get("sim_passed") and r.get("iterations", 99) == 0),
            "avg_iterations": round(sum(r.get("iterations", 0) for r in results) / len(results), 1) if results else 0,
            "rtl_generated": rtl_gen_count,
            "tb_generated": tb_gen_count,
        },
        "results": results,
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\n{'='*80}")
    print(f"CAMPAIGN COMPLETE")
    print(f"Passed: {data['summary']['passed']}/{len(BENCHMARK_SPECS)}")
    print(f"First-pass success: {data['summary']['first_pass_success']}")
    print(f"Avg iterations: {data['summary']['avg_iterations']}")
    print(f"RTL generated (AI): {rtl_gen_count}")
    print(f"TB generated (AI): {tb_gen_count}")
    print(f"Duration: {data['total_duration_seconds']:.1f}s")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
