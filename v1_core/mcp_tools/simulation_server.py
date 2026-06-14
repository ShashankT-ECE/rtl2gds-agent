"""
simulation_server.py
MCP Tool — wraps Icarus Verilog simulation.
Called by simulation_agent — never called directly by other agents.
"""

import subprocess
from pathlib import Path
from v1_core.utils import logger

WORKSPACE = Path("workspace")


def run_simulation(rtl_file: str, tb_file: str) -> dict:
    """
    Compile and run RTL + testbench using Icarus Verilog.

    Args:
        rtl_file: path to Verilog RTL file
        tb_file: path to cocotb testbench file

    Returns:
        {passed: bool, log: str}
    """
    WORKSPACE.mkdir(exist_ok=True)
    output_bin = WORKSPACE / "sim_out"

    compile_cmd = [
        "iverilog",
        "-o", str(output_bin),
        rtl_file,
        tb_file
    ]

    logger.info(f"Compiling: {' '.join(compile_cmd)}")

    compile_result = subprocess.run(
        compile_cmd,
        capture_output=True,
        text=True
    )

    if compile_result.returncode != 0:
        log = compile_result.stderr
        logger.error(f"Compilation failed")
        return {"passed": False, "log": log}

    run_result = subprocess.run(
        ["vvp", str(output_bin)],
        capture_output=True,
        text=True
    )

    log = run_result.stdout + run_result.stderr
    passed = run_result.returncode == 0

    if passed:
        logger.success("Simulation passed")
    else:
        logger.error("Simulation failed")

    return {"passed": passed, "log": log}
