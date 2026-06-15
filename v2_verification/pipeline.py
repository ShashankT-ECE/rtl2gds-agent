"""
pipeline.py
V2 LangGraph pipeline extending V1 with synthesis and static timing analysis (STA).
Wires all V1 and V2 agents into a complete RTL-to-GDS state machine.

Flow:
  rtl_gen -> testbench -> simulation
     |                        |
     | (pass)     (fail) -----+---> log_analysis -> fix ->|
     v                        |                           |
  synthesis <-----------------+  (back to testbench)  <---+
     |
     v
   sta
     |\
     | (timing_met)  ---> END
     |
     | (timing fail, iter < MAX)
     v
  timing_opt -> synthesis -> sta (loop, max 3 timing iterations)
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


def _safe_agent_call(state: PipelineState, agent_fn, agent_name: str) -> PipelineState:
    """Wrap an agent call in try/except so a crash doesn't kill the pipeline."""
    try:
        return agent_fn(state)
    except Exception as e:
        logger.error(f"{agent_name} crashed: {e}")
        new_state = {**state, "stage": f"{agent_name.lower()}_failed"}
        if agent_name == "Simulation":
            new_state["sim_passed"] = False
        return new_state


# ---------------------------------------------------------------------------
# V2 agent imports — each wraps an MCP tool and returns updated PipelineState.
# These are created in parallel with this file; try/except guards ensure the
# pipeline loads cleanly even if a given agent module is not yet present.
# ---------------------------------------------------------------------------
try:
    from v2_verification.agents.synthesis_agent import synthesis_agent
    _V2_SYNTHESIS_AVAILABLE = True
except ImportError:
    synthesis_agent = None
    _V2_SYNTHESIS_AVAILABLE = False

try:
    from v2_verification.agents.sta_agent import sta_agent
    _V2_STA_AVAILABLE = True
except ImportError:
    sta_agent = None
    _V2_STA_AVAILABLE = False

try:
    from v2_verification.agents.timing_opt_agent import timing_opt_agent
    _V2_TIMING_OPT_AVAILABLE = True
except ImportError:
    timing_opt_agent = None
    _V2_TIMING_OPT_AVAILABLE = False

# Maximum number of timing-optimisation iterations before giving up.
MAX_TIMING_ITERATIONS = 3


# ---------------------------------------------------------------------------
# Router functions (conditional edge logic)
# ---------------------------------------------------------------------------


def should_fix_or_synthesize(state: PipelineState) -> str:
    """Router after the simulation node.

    Returns the destination label:
      "synthesis" -- simulation passed, proceed to synthesis flow.
      "fix"       -- simulation failed, enter the fix loop.
      "end"       -- max fix iterations exhausted, give up.
    """
    if state["sim_passed"]:
        logger.success("Simulation passed -- proceeding to synthesis")
        return "synthesis"

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
                f"Convergence detector: identical error repeated ({stuck_count}x) -- "
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
            f"attempts -- routing to END"
        )
        return "end"

    if state["iteration"] >= state["max_iterations"]:
        logger.error(
            f"Max fix iterations ({state['max_iterations']}) reached -- halting"
        )
        return "end"

    logger.info(
        f"Simulation failed -- routing to fix loop "
        f"(iteration {state['iteration']})"
    )
    return "fix"


def should_end_or_optimize(state: PipelineState) -> str:
    """Router after the STA node.

    Returns the destination label:
      "end"      -- timing is met, pipeline complete.
      "optimize" -- timing not met but iterations remain, enter opt loop.
      "end"      -- WNS is None (STA couldn't analyze), end pipeline.
      "end"      -- timing not met AND max timing iterations exhausted.
    """
    wns = state.get("wns")
    if wns is None:
        logger.warning(
            "STA produced no timing data (design may be combinational "
            "or missing a clock) -- ending pipeline"
        )
        return "end"

    if state.get("timing_met", False):
        logger.success(
            f"Timing met (WNS={wns}) -- pipeline complete"
        )
        return "end"

    timing_iters = state.get("timing_iterations", 0)
    if timing_iters >= MAX_TIMING_ITERATIONS:
        logger.error(
            f"Max timing iterations ({MAX_TIMING_ITERATIONS}) reached -- "
            f"pipeline halted"
        )
        return "end"

    logger.info(
        f"Timing not met (WNS={state.get('wns', 'N/A')}) -- "
        f"routing to timing optimisation "
        f"(iteration {timing_iters + 1}/{MAX_TIMING_ITERATIONS})"
    )
    return "optimize"


def should_run_sta_or_end(state: PipelineState) -> str:
    """Router after the synthesis node.

    If synthesis failed (no netlist, zero cells) we skip STA and end the
    pipeline with a clear error message rather than crashing into OpenSTA
    with a missing netlist file.

    Returns:
      "sta" -- synthesis succeeded, proceed to STA.
      "end" -- synthesis failed, stop the pipeline.
    """
    netlist = state.get("netlist_path", "")
    cell_count = state.get("cell_count", 0)
    if not netlist:
        logger.error(
            f"Synthesis produced no valid netlist "
            f"(netlist='{netlist}') -- "
            f"skipping STA and halting pipeline"
        )
        return "end"
    logger.success(f"Synthesis produced netlist -- proceeding to STA")
    return "sta"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_v2_pipeline(
    skip_rtl_gen: bool = False,
    skip_synthesis_sta: bool = False,
    skip_testbench: bool = False,
) -> StateGraph:
    """Build and compile the V2 LangGraph pipeline.

    Args:
        skip_rtl_gen: If True the entry point is ``testbench`` instead of
            ``rtl_gen`` (used when ``rtl_code`` is supplied directly).
        skip_synthesis_sta: If True, synthesis and STA nodes are omitted,
            effectively running in V1-only mode.

    Returns:
        A compiled ``StateGraph`` ready for ``.invoke()``.
    """
    graph = StateGraph(PipelineState)

    # ---- V1 nodes (wrapped for crash safety) ------------------------------
    graph.add_node("spec_parser", lambda s: _safe_agent_call(s, spec_parser_agent, "spec_parser"))
    graph.add_node("verification_planner", lambda s: _safe_agent_call(s, verification_planner_agent, "verification_planner"))
    graph.add_node("rtl_gen", lambda s: _safe_agent_call(s, rtl_gen_agent, "rtl_gen"))
    graph.add_node("testbench", lambda s: _safe_agent_call(s, testbench_agent, "testbench"))
    graph.add_node("simulation", lambda s: _safe_agent_call(s, simulation_agent, "Simulation"))
    graph.add_node("log_analysis", lambda s: _safe_agent_call(s, log_analysis_agent, "log_analysis"))
    graph.add_node("fix", lambda s: _safe_agent_call(s, fix_agent, "fix"))

    # ---- V2 nodes ---------------------------------------------------------
    v2_available = False
    if not skip_synthesis_sta:
        if _V2_SYNTHESIS_AVAILABLE:
            graph.add_node("synthesis", lambda s: _safe_agent_call(s, synthesis_agent, "Synthesis"))
            v2_available = True
        if _V2_STA_AVAILABLE:
            graph.add_node("sta", lambda s: _safe_agent_call(s, sta_agent, "STA"))
            v2_available = True
        if _V2_TIMING_OPT_AVAILABLE:
            graph.add_node("timing_opt", lambda s: _safe_agent_call(s, timing_opt_agent, "timing_opt"))

    # ---- Entry point ------------------------------------------------------
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

    # ---- Simulation pipeline (V1 flow) ------------------------------------
    if not skip_testbench:
        graph.add_edge("testbench", "simulation")

    # Simulation -> {synthesis | log_analysis | END}
    simulation_route_map = {
        "fix": "log_analysis",
        "end": END,
    }
    if v2_available:
        simulation_route_map["synthesis"] = "synthesis"
    else:
        # V2 unavailable -- treat "passed simulation" as pipeline end
        simulation_route_map["synthesis"] = END

    graph.add_conditional_edges(
        "simulation",
        should_fix_or_synthesize,
        simulation_route_map,
    )

    # Fix loop: log_analysis -> fix -> {testbench | simulation}
    graph.add_edge("log_analysis", "fix")
    if skip_testbench:
        graph.add_edge("fix", "simulation")
    else:
        graph.add_edge("fix", "testbench")

    # ---- Synthesis / STA flow (V2) ----------------------------------------
    if v2_available:
        # Synthesis -> {sta | END} (guards against failed synthesis)
        graph.add_conditional_edges(
            "synthesis",
            should_run_sta_or_end,
            {
                "sta": "sta",
                "end": END,
            },
        )

        # STA -> {END | timing_opt}
        sta_route_map = {
            "end": END,
        }
        if _V2_TIMING_OPT_AVAILABLE:
            sta_route_map["optimize"] = "timing_opt"
        else:
            # No timing-opt agent -- treat timing failure as end
            sta_route_map["optimize"] = END

        graph.add_conditional_edges(
            "sta",
            should_end_or_optimize,
            sta_route_map,
        )

        # Timing optimisation loop
        if _V2_TIMING_OPT_AVAILABLE:
            graph.add_edge("timing_opt", "synthesis")

    return graph.compile()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def run_v2_pipeline(spec: str, design_name: str, rtl_code: str = "",
                    reference_tb_path: str = "") -> dict:
    """Run the full V2 pipeline (V1 + synthesis + STA) for a given spec.

    Args:
        spec: Natural-language hardware specification.
        design_name: Short identifier such as ``alu_8bit`` or ``sync_fifo``.
        rtl_code: Optional pre-existing RTL code to use (skips RTL generation).

    Returns:
        Final ``PipelineState`` as a plain dictionary after the pipeline
        completes or is halted.
    """
    logger.divider()
    logger.info(f"Starting V2 pipeline for: {design_name}")

    if rtl_code:
        logger.info("RTL code provided -- skipping RTL generation")
    if reference_tb_path:
        logger.info("Reference testbench provided -- skipping LLM generation")

    # Warn if V2 agents are missing so the user knows what is unavailable.
    if not _V2_SYNTHESIS_AVAILABLE:
        logger.warning("synthesis_agent not found -- pipeline will run in V1 mode")
    if not _V2_STA_AVAILABLE:
        logger.warning("sta_agent not found -- skipping static timing analysis")
    if not _V2_TIMING_OPT_AVAILABLE:
        logger.warning(
            "timing_opt_agent not found -- timing optimisation loop disabled"
        )
    logger.divider()

    # Build the graph (auto-detects which agents exist).
    pipeline = build_v2_pipeline(
        skip_rtl_gen=bool(rtl_code),
        skip_testbench=bool(reference_tb_path),
    )

    # Create initial state and extend with V2 fields.
    initial_state = get_initial_state(spec=spec, design_name=design_name)
    if rtl_code:
        initial_state["rtl_code"] = rtl_code
    if reference_tb_path:
        initial_state["reference_tb_path"] = reference_tb_path
    initial_state.update({
        "netlist_path": "",
        "synthesis_report": "",
        "timing_met": False,
        "wns": 0.0,
        "tns": 0.0,
        "critical_path": "",
        "timing_iterations": 0,
    })

    # Run the graph.
    try:
        final_state = pipeline.invoke(
            initial_state,
            {"recursion_limit": 50},
        )
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user -- exiting")
        raise

    # ---- Summary ----------------------------------------------------------
    logger.divider()
    if final_state["sim_passed"]:
        logger.success(
            f"Pipeline COMPLETE -- {design_name} passed simulation"
        )
    else:
        logger.error(
            f"Pipeline HALTED -- {design_name} did not pass simulation "
            f"after {final_state['iteration']} iteration(s)"
        )

    if final_state.get("synthesis_report"):
        if final_state.get("timing_met", False):
            logger.success(
                f"Timing CLOSED -- {design_name}: "
                f"WNS={final_state.get('wns', 'N/A')}"
            )
        else:
            logger.warning(
                f"Timing NOT closed -- {design_name}: "
                f"WNS={final_state.get('wns', 'N/A')}"
            )
    logger.divider()

    return dict(final_state)
