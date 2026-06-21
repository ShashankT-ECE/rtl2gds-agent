"""
pipeline.py
Wires all V1 agents into a LangGraph state machine.
This is the complete V1 pipeline graph.
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
from v1_core.utils import logger
from v1_core.utils.trace2skill import confirm_skill, reject_skill
from v1_core.agents.log_analysis_agent import _guess_category


def _confirm_or_reject_pending(state: PipelineState) -> PipelineState:
    """After simulation, confirm or reject any pending skill from the last fix."""
    pending_id = state.get("pending_skill_id", "")
    if not pending_id:
        return state

    category = _guess_category(state["design_name"])

    if state["sim_passed"]:
        confirm_skill(pending_id, category)
        logger.success(f"Confirmed skill {pending_id} in {category} — fix verified by simulation")
    else:
        reject_skill(pending_id, category)
        logger.info(f"Rejected skill {pending_id} in {category} — fix did not pass simulation")

    return {**state, "pending_skill_id": ""}


def should_fix_or_end(state: PipelineState) -> str:
    """
    Router function — decides next step after simulation.
    Returns: "fix" if simulation failed, "end" if passed or max iterations reached.
    """
    # Confirm or reject any pending skill from the last fix
    _confirm_or_reject_pending(state)

    if state["sim_passed"]:
        logger.success("Simulation passed — pipeline complete")
        return "end"

    # Convergence detection: if error_analysis repeats, increment stuck_count
    current_error = state.get("error_analysis", {})
    previous_error = state.get("previous_error_analysis", {})
    stuck_count = state.get("stuck_count", 0)

    if current_error and previous_error:
        same_type = current_error.get("ERROR_TYPE") == previous_error.get("ERROR_TYPE")
        same_cause = current_error.get("CAUSE") == previous_error.get("CAUSE")
        if same_type and same_cause:
            stuck_count += 1
            logger.warning(
                f"Convergence detector: identical error repeated ({stuck_count}x) — "
                f"ERROR_TYPE={current_error.get('ERROR_TYPE')}, "
                f"CAUSE={current_error.get('CAUSE')}"
            )
        else:
            stuck_count = 0  # different error, reset counter
    else:
        stuck_count = 0

    # Persist convergence state
    state["stuck_count"] = stuck_count
    state["previous_error_analysis"] = current_error

    if stuck_count >= 2:
        logger.error(
            f"Convergence detector: stuck at same error after {stuck_count} "
            f"attempts — routing to END"
        )
        return "end"

    if state["iteration"] >= state["max_iterations"]:
        logger.error(f"Max iterations ({state['max_iterations']}) reached — halting")
        return "end"

    logger.info(f"Simulation failed — routing to fix loop (iteration {state['iteration']})")
    return "fix"


def build_pipeline(skip_rtl_gen: bool = False, skip_testbench: bool = False) -> StateGraph:
    """
    Builds and compiles the V1 LangGraph pipeline.

    Args:
        skip_rtl_gen: if True, entry point is testbench instead of rtl_gen
                      (used when rtl_code is provided directly)
    Returns compiled graph ready to run.
    """
    graph = StateGraph(PipelineState)

    # Add all agent nodes
    graph.add_node("spec_parser", spec_parser_agent)
    graph.add_node("verification_planner", verification_planner_agent)
    graph.add_node("rtl_gen", rtl_gen_agent)
    graph.add_node("testbench", testbench_agent)
    graph.add_node("simulation", simulation_agent)
    graph.add_node("log_analysis", log_analysis_agent)
    graph.add_node("fix", fix_agent)

    # Define edges — linear flow
    graph.set_entry_point("spec_parser")
    graph.add_edge("spec_parser", "verification_planner")
    if skip_rtl_gen:
        if skip_testbench:
            graph.add_edge("verification_planner", "simulation")
        else:
            graph.add_edge("verification_planner", "testbench")
    else:
        graph.add_edge("verification_planner", "rtl_gen")
        if skip_testbench:
            graph.add_edge("rtl_gen", "simulation")
        else:
            graph.add_edge("rtl_gen", "testbench")

    if not skip_testbench:
        graph.add_edge("testbench", "simulation")

    # Conditional routing after simulation
    graph.add_conditional_edges(
        "simulation",
        should_fix_or_end,
        {
            "fix": "log_analysis",
            "end": END
        }
    )

    # Fix loop — after fix, regenerate testbench from corrected RTL, then re-simulate
    graph.add_edge("log_analysis", "fix")
    if skip_testbench:
        graph.add_edge("fix", "simulation")
    else:
        graph.add_edge("fix", "testbench")
        graph.add_edge("testbench", "simulation")

    return graph.compile()


def run_pipeline(spec: str, design_name: str, rtl_code: str = "",
                 reference_tb_path: str = "") -> PipelineState:
    """
    Run the full V1 pipeline for a given spec.

    Args:
        spec: natural language hardware specification
        design_name: short name like alu_8bit
        rtl_code: optional pre-existing RTL code to skip RTL generation
        reference_tb_path: optional path to reference testbench (skips LLM testbench gen)

    Returns:
        final PipelineState after pipeline completes
    """
    logger.divider()
    logger.info(f"Starting V1 pipeline for: {design_name}")
    if rtl_code:
        logger.info("RTL code provided — skipping RTL generation step")
    if reference_tb_path:
        logger.info(f"Reference testbench provided — skipping LLM testbench generation")
    logger.divider()

    skip_rtl_gen = bool(rtl_code)
    skip_testbench = bool(reference_tb_path)
    pipeline = build_pipeline(skip_rtl_gen=skip_rtl_gen, skip_testbench=skip_testbench)
    initial_state = get_initial_state(spec=spec, design_name=design_name)
    if rtl_code:
        initial_state["rtl_code"] = rtl_code
    if reference_tb_path:
        initial_state["reference_tb_path"] = reference_tb_path
    final_state = pipeline.invoke(initial_state)

    logger.divider()
    if final_state["sim_passed"]:
        logger.success(f"Pipeline COMPLETE — {design_name} passed simulation")
    else:
        logger.error(f"Pipeline HALTED — {design_name} did not pass after {final_state['iteration']} iterations")
    logger.divider()

    return final_state
