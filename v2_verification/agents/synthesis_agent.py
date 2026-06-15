"""
synthesis_agent.py
Synthesis Agent — LangGraph node for V2 RTL-to-GDS pipeline.
Takes RTL code from PipelineState, writes it to disk, runs Yosys synthesis,
and updates state with netlist path and synthesis results.
"""

from pathlib import Path

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils import logger
from v2_verification.mcp_tools.synthesis_server import _run_synthesis


SYNTHESIS_DIR = Path("workspace") / "synthesis"
LIBERTY_FILE = "pdk/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib"


def synthesis_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — runs Yosys synthesis on the generated RTL code.

    Input state fields used: rtl_code, design_name
    Output state fields updated: netlist_path, synthesis_report,
                                 timing_met, wns, tns, critical_path, stage
    """
    logger.agent("SynthesisAgent", f"Running synthesis for: {state['design_name']}")

    # ---- Write RTL to disk --------------------------------------------------
    SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)
    rtl_file = SYNTHESIS_DIR / f"{state['design_name']}.v"
    rtl_file.write_text(state["rtl_code"])
    logger.info(f"Written RTL to: {rtl_file}")

    # ---- Run Yosys synthesis ------------------------------------------------
    result = _run_synthesis(
        rtl_file=str(rtl_file),
        top_module=state["design_name"],
        liberty_file=LIBERTY_FILE,
    )

    netlist_path = result["netlist_path"]
    area = result["area"]
    cell_count = result["cell_count"]
    warnings = result.get("warnings", [])
    latches_inferred = result.get("latches_inferred", 0)

    # ---- Log synthesis summary ----------------------------------------------
    logger.success(
        f"Synthesis complete — cells: {cell_count}, "
        f"area: {area:.2f}, latches: {latches_inferred}"
    )

    if warnings:
        logger.warning(f"Synthesis produced {len(warnings)} warning(s):")
        for w in warnings[:5]:
            logger.warning(f"  {w}")
        if len(warnings) > 5:
            logger.warning(f"  ... and {len(warnings) - 5} more")

    if latches_inferred:
        logger.warning(
            f"Design infers {latches_inferred} latch(es) — "
            "check for incomplete case/if statements or missing default assignments"
        )

    # ---- Build synthesis report text ----------------------------------------
    report_parts = [
        f"Synthesis Results for {state['design_name']}",
        f"{'=' * 40}",
        f"Cell count:     {cell_count}",
        f"Area:           {area:.2f}",
        f"Latches:        {latches_inferred}",
        f"Warnings:       {len(warnings)}",
        f"Netlist:        {netlist_path}",
    ]
    if warnings:
        report_parts.append("")
        report_parts.append("Warnings:")
        for w in warnings:
            report_parts.append(f"  - {w}")
    synthesis_report = "\n".join(report_parts)

    logger.info(f"Synthesis report:\n{synthesis_report}")

    return {
        **state,
        "netlist_path": netlist_path,
        "synthesis_report": synthesis_report,
        "timing_met": False,
        "wns": 0.0,
        "tns": 0.0,
        "critical_path": "",
        "stage": "synthesis_done",
    }
