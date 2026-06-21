"""
drc_agent.py
DRC Agent — LangGraph node for design rule checking.
Runs KLayout DRC on the GDSII output from OpenLane.
"""
from v1_core.agents.orchestrator import PipelineState
from v3_physical.mcp_tools.drc_server import _run_drc
from v1_core.utils import logger


def drc_agent(state: PipelineState) -> PipelineState:
    logger.agent("DRCAgent", f"Running DRC for: {state['design_name']}")

    if not state.get("gds_path"):
        logger.error("No GDS path — skipping DRC")
        return {**state, "stage": "drc_skipped"}

    result = _run_drc(
        gds_file=state["gds_path"],
        top_module=state["design_name"]
    )

    if result["passed"]:
        logger.success("DRC CLEAN — ready for tapeout")
    else:
        logger.error(f"DRC FAILED — {result['violations']} violations")

    return {
        **state,
        "drc_violations": result["violations"],
        "drc_passed": result["passed"],
        "stage": "drc_done"
    }
