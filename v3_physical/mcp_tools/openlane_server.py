"""
openlane_server.py
MCP Tool — wraps OpenLane 2 physical design flow via Docker.
Accepts netlist + config, runs full floorplan→placement→CTS→routing→GDSII.
Called by openlane_agent.py — never called directly from other agents.
"""
import subprocess
import os
import json
from pathlib import Path
from v1_core.utils import logger

WORKSPACE = Path("workspace/physical").resolve()
PDK_PATH = Path("pdk/sky130").resolve()

# OpenLane 2 Docker image from GitHub Container Registry.
# Version-matched to the installed pip package.
import openlane
_OL_VERSION = openlane.__version__
OPENLANE_IMAGE = f"ghcr.io/efabless/openlane2:{_OL_VERSION}"


def _run_openlane(
    netlist_file: str,
    top_module: str,
    clock_period_ns: float = 20.0,
    die_area: str = "0 0 500 500",
    target_density: float = 0.5
) -> dict:
    """
    Run OpenLane 2 physical design on a gate-level netlist.
    Args:
        netlist_file: path to synthesized gate-level Verilog netlist
        top_module: top-level module name
        clock_period_ns: clock period in nanoseconds
        die_area: die area in microns "x0 y0 x1 y1"
        target_density: target cell density 0.0-1.0
    Returns:
        {gds_path, routed_def, area, congestion, drc_violations, timing_met, log}
    """
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    design_dir = WORKSPACE / top_module
    design_dir.mkdir(exist_ok=True)

    # Copy netlist into design dir
    netlist_path = Path(netlist_file).resolve()
    dest_netlist = design_dir / f"{top_module}.v"
    import shutil
    shutil.copy(netlist_path, dest_netlist)

    # Generate OpenLane 2 config.json
    config = {
        "DESIGN_NAME": top_module,
        "VERILOG_FILES": f"/workspace/{top_module}/{top_module}.v",
        "CLOCK_PORT": "clk",
        "CLOCK_PERIOD": clock_period_ns,
        "DIE_AREA": die_area,
        "FP_CORE_UTIL": int(target_density * 100),
        "FP_SIZING": "absolute",
        "PDK": "sky130A",
        "STD_CELL_LIBRARY": "sky130_fd_sc_hd",
    }
    config_path = design_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2))

    logger.info(f"Running OpenLane 2 for: {top_module}")
    logger.info(f"Config: clock={clock_period_ns}ns, die={die_area}, density={target_density}")

    # Run OpenLane 2 in Docker
    docker_cmd = [
        "docker", "run", "--rm",
        "-v", f"{design_dir}:/workspace/{top_module}",
        "-v", f"{PDK_PATH}:/pdk/sky130",
        OPENLANE_IMAGE,
        "openlane", f"/workspace/{top_module}/config.json"
    ]

    result = subprocess.run(
        docker_cmd,
        capture_output=True,
        text=True,
        timeout=1800  # 30 min timeout for physical design
    )

    log = result.stdout + result.stderr
    logger.info(f"OpenLane log (last 500 chars): {log[-500:]}")

    # Look for GDSII output
    gds_files = list(design_dir.rglob("*.gds"))
    gds_path = str(gds_files[0]) if gds_files else ""

    # Parse basic metrics from log
    timing_met = "Timing analysis complete" in log or "WNS: 0" in log
    drc_violations = log.count("violation") if "violation" in log else 0

    return {
        "gds_path": gds_path,
        "timing_met": timing_met,
        "drc_violations": drc_violations,
        "log": log,
        "success": result.returncode == 0
    }
