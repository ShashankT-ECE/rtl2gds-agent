"""
openlane_agent.py
OpenLane Agent — LangGraph node for physical design.
Takes synthesized netlist from state, runs OpenLane 2 via Docker,
outputs GDSII path and physical design metrics.
"""
from v1_core.agents.orchestrator import PipelineState
from v3_physical.mcp_tools.openlane_server import _run_openlane
from v1_core.utils import logger


def openlane_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — runs OpenLane 2 physical design.
    Input state: netlist_path, design_name, wns (for clock period guidance)
    Output state: gds_path, drc_violations, stage
    """
    logger.agent("OpenLaneAgent", f"Starting physical design for: {state['design_name']}")

    if not state.get("netlist_path"):
        logger.error("No netlist path in state — cannot run physical design")
        return {**state, "stage": "openlane_failed"}

    # Use clock period from verification plan if available
    clock_period = 20.0
    if state.get("verification_plan"):
        timing = state["verification_plan"].get("timing_requirements", {})
        if timing.get("clock_period_ns"):
            clock_period = float(timing["clock_period_ns"])

    result = _run_openlane(
        netlist_file=state["netlist_path"],
        top_module=state["design_name"],
        clock_period_ns=clock_period
    )

    if result["success"]:
        logger.success(f"Physical design complete: {result['gds_path']}")
    else:
        logger.error("OpenLane 2 failed — check log")

    return {
        **state,
        "gds_path": result.get("gds_path", ""),
        "drc_violations": result.get("drc_violations", -1),
        "openlane_log": result.get("log", ""),
        "stage": "openlane_done" if result["success"] else "openlane_failed"
    }
