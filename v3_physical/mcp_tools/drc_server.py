"""
drc_server.py
MCP Tool — runs KLayout DRC on the generated GDSII.
Returns violation count and violation details.
"""
import subprocess
import shutil
from pathlib import Path
from v1_core.utils import logger


def _find_klayout() -> str | None:
    """Locate a runnable KLayout binary (CLI or pip-based)."""
    # Prefer system klayout binary
    klayout_bin = shutil.which("klayout")
    if klayout_bin:
        return klayout_bin
    # Try python -m klayout (pip package provides Python bindings only — no CLI)
    # The pip package klayout 0.29.x has no __main__, so this won't work.
    return None


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

    klayout_bin = _find_klayout()
    if not klayout_bin:
        logger.warning(
            "KLayout CLI not found — install 'klayout' system package for DRC. "
            "The pip package 'klayout' only provides Python bindings."
        )
        return {
            "violations": -1,
            "passed": False,
            "log": "KLayout CLI not available — install system klayout package",
        }

    drc_script = Path("pdk/sky130/sky130A.drc")
    if not drc_script.exists():
        logger.warning(f"DRC script not found: {drc_script}")
        return {"violations": -1, "passed": False, "log": "DRC script not found"}

    logger.info(f"Running KLayout DRC on: {gds_file}")

    result = subprocess.run(
        [klayout_bin, "-b", "-r", str(drc_script), "-rd", f"input={gds_file}"],
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
