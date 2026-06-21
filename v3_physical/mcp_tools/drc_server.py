"""
drc_server.py
MCP Tool — runs KLayout DRC on the generated GDSII.
Returns violation count and violation details.
"""
import subprocess
from pathlib import Path
from v1_core.utils import logger


def _run_drc(gds_file: str, top_module: str) -> dict:
    """
    Run KLayout DRC on GDSII file using Sky130 rules.
    Args:
        gds_file: path to GDSII file
        top_module: top module name for reporting
    Returns:
        {violations, violation_list, passed, log}
    """
    gds_path = Path(gds_file).resolve()
    if not gds_path.exists():
        logger.error(f"GDS file not found: {gds_file}")
        return {"violations": -1, "passed": False, "log": "GDS file not found"}

    logger.info(f"Running KLayout DRC on: {gds_file}")

    result = subprocess.run(
        ["klayout", "-b", "-r", "pdk/sky130/sky130A.drc", "-rd", f"input={gds_file}"],
        capture_output=True,
        text=True,
        timeout=300
    )

    log = result.stdout + result.stderr
    violations = log.count("DRC violation") if "DRC violation" in log else 0
    passed = violations == 0 and result.returncode == 0

    if passed:
        logger.success("DRC: CLEAN — zero violations")
    else:
        logger.error(f"DRC: {violations} violations found")

    return {
        "violations": violations,
        "passed": passed,
        "log": log
    }
