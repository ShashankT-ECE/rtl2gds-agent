"""
v3_physical/pipeline.py
V3 Pipeline — extends V2 with physical design (OpenLane 2 + DRC).
Full flow: NL spec → RTL → verification → synthesis → STA → OpenLane → DRC → GDSII
"""
from langgraph.graph import StateGraph, END
from v1_core.agents.orchestrator import PipelineState, get_initial_state
from v1_core.agents.spec_parser_agent import spec_parser_agent
from v1_core.agents.verification_planner_agent import verification_planner_agent
from v1_core.agents.rtl_gen_agent import rtl_gen_agent
from v1_core.agents.testbench_agent import testbench_agent
from v1_core.agents.simulation_agent import simulation_agent
from v1_core.agents.log_analysis_agent import log_analysis_agent
from v1_core.agents.fix_agent import fix_agent
from v2_verification.agents.synthesis_agent import synthesis_agent
from v2_verification.agents.sta_agent import sta_agent
from v3_physical.agents.openlane_agent import openlane_agent
from v3_physical.agents.drc_agent import drc_agent
from v1_core.utils import logger


def should_fix_or_proceed(state: PipelineState) -> str:
    """Router after simulation: proceed to synthesis, enter fix loop, or halt."""
    if state["sim_passed"]:
        return "proceed_to_synthesis"
    if state["iteration"] >= state["max_iterations"]:
        return "end"
    if state.get("stuck_count", 0) >= 2:
        logger.error("Fix loop stuck — halting")
        return "end"
    return "fix"


def should_run_openlane(state: PipelineState) -> str:
    """Router after STA: proceed to OpenLane if timing met or no timing data."""
    if state.get("timing_met") or state.get("wns") is None:
        return "proceed_to_openlane"
    return "end"


def should_run_drc(state: PipelineState) -> str:
    """Router after OpenLane: run DRC if GDS was produced."""
    if state.get("gds_path"):
        return "run_drc"
    return "end"


def build_v3_pipeline():
    """Build and compile the V3 LangGraph pipeline."""
    graph = StateGraph(PipelineState)

    graph.add_node("spec_parser", spec_parser_agent)
    graph.add_node("verification_planner", verification_planner_agent)
    graph.add_node("rtl_gen", rtl_gen_agent)
    graph.add_node("testbench", testbench_agent)
    graph.add_node("simulation", simulation_agent)
    graph.add_node("log_analysis", log_analysis_agent)
    graph.add_node("fix", fix_agent)
    graph.add_node("synthesis", synthesis_agent)
    graph.add_node("sta", sta_agent)
    graph.add_node("openlane", openlane_agent)
    graph.add_node("drc", drc_agent)

    graph.set_entry_point("spec_parser")
    graph.add_edge("spec_parser", "verification_planner")
    graph.add_edge("verification_planner", "rtl_gen")
    graph.add_edge("rtl_gen", "testbench")
    graph.add_edge("testbench", "simulation")

    graph.add_conditional_edges("simulation", should_fix_or_proceed, {
        "proceed_to_synthesis": "synthesis",
        "fix": "log_analysis",
        "end": END
    })

    graph.add_edge("log_analysis", "fix")
    graph.add_edge("fix", "testbench")

    # Synthesis → STA (no conditional — always attempt STA)
    graph.add_edge("synthesis", "sta")

    # STA → OpenLane if timing met or no timing data; END otherwise
    graph.add_conditional_edges("sta", should_run_openlane, {
        "proceed_to_openlane": "openlane",
        "end": END
    })

    # OpenLane → DRC if GDS produced; END otherwise
    graph.add_conditional_edges("openlane", should_run_drc, {
        "run_drc": "drc",
        "end": END
    })

    graph.add_edge("drc", END)
    return graph.compile()


def run_v3_pipeline(spec: str, design_name: str, rtl_code: str = "") -> PipelineState:
    """Run the full V3 pipeline (V1 + V2 + OpenLane 2 + DRC) for a given spec.

    Args:
        spec: Natural-language hardware specification.
        design_name: Short identifier such as ``alu_8bit`` or ``sync_fifo``.
        rtl_code: Optional pre-existing RTL code (skips LLM generation).

    Returns:
        Final ``PipelineState`` as a plain dictionary.
    """
    logger.divider()
    logger.info(f"Starting V3 pipeline for: {design_name}")
    logger.divider()

    pipeline = build_v3_pipeline()
    initial_state = get_initial_state(spec=spec, design_name=design_name)
    if rtl_code:
        initial_state["rtl_code"] = rtl_code

    return pipeline.invoke(initial_state)
