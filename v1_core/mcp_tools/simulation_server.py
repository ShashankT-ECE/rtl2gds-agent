"""
simulation_server.py
MCP Tool — runs cocotb 2.x simulation using Makefile approach.
cocotb 2.x removed cocotb.runner — correct method is via Makefile.
"""

import subprocess
import os
from pathlib import Path
from v1_core.utils import logger

WORKSPACE = Path("workspace").resolve()


def run_simulation(rtl_file: str, tb_file: str) -> dict:
    """
    Run cocotb simulation using cocotb 2.x Makefile approach.

    Args:
        rtl_file: path to Verilog RTL file
        tb_file: path to cocotb testbench Python file

    Returns:
        {passed: bool, log: str}
    """
    WORKSPACE.mkdir(exist_ok=True)

    tb_path = Path(tb_file)
    rtl_path = Path(rtl_file)

    tb_module = tb_path.stem        # e.g. alu_8bit_tb

    # Auto-detect the toplevel module name from the RTL source
    # (the filename may not match the module name)
    rtl_source = rtl_path.read_text()
    import re
    m = re.search(r'^\s*module\s+(\w+)', rtl_source, re.MULTILINE)
    toplevel = m.group(1) if m else rtl_path.stem
    logger.info(f"Detected Verilog module name: {toplevel}")

    build_dir = WORKSPACE / "cocotb_build"
    build_dir.mkdir(exist_ok=True)

    # Clean old results before each run to avoid stale pass/fail detection
    old_results = build_dir / "results.xml"
    if old_results.exists():
        old_results.unlink()

    # Get cocotb makefiles path
    makefiles_dir = subprocess.check_output(
        ["cocotb-config", "--makefiles"]
    ).decode().strip()

    # Write Makefile
    makefile = build_dir / "Makefile"
    makefile.write_text(f"""
SIM = icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = {rtl_path.resolve()}
TOPLEVEL = {toplevel}
COCOTB_TEST_MODULES = {tb_module}
COCOTB_RESULTS_FILE = results.xml
include {makefiles_dir}/Makefile.sim
""")

    logger.info(f"Running cocotb simulation for: {toplevel}")

    # Append workspace dir to PYTHONPATH so cocotb can find the testbench module
    workspace_dir = str(tb_path.parent.resolve())
    existing_pp = os.environ.get("PYTHONPATH", "")
    pythonpath = f"{workspace_dir}:{existing_pp}" if existing_pp else workspace_dir

    env = {
        **os.environ,
        "PYTHONPATH": pythonpath,
        "COCOTB_REDUCED_LOG_FMT": "1",
    }

    result = subprocess.run(
        ["make", "-f", str(makefile.resolve())],
        capture_output=True,
        text=True,
        cwd=str(build_dir),
        env=env
    )

    raw_log = result.stdout + result.stderr

    # Extract cocotb-relevant portion — skip make/iverilog build noise
    # Cocotb output starts with timestamp like "0.00ns" or "     0.00ns"
    import re as _re
    cocotb_match = _re.search(r'^\s*\d+\.\d+ns', raw_log, _re.MULTILINE)
    if cocotb_match:
        log = raw_log[cocotb_match.start():]
    else:
        log = raw_log  # fall back to full log if no cocotb output found

    # Append results.xml content if it exists (structured failure data)
    results_file = build_dir / "results.xml"
    if results_file.exists():
        xml_content = results_file.read_text()
        log += "\n--- results.xml ---\n" + xml_content

    if log:
        logger.info(f"Simulation log (last 500 chars): {log[-500:]}")
    else:
        logger.warning("Simulation log is empty!")

    # cocotb writes results.xml — check it for pass/fail
    passed = False
    if results_file.exists():
        content = results_file.read_text()
        passed = 'failure' not in content.lower() and 'error' not in content.lower()

    if passed:
        logger.success("Simulation passed")
    else:
        logger.error("Simulation failed")

    return {"passed": passed, "log": log}
