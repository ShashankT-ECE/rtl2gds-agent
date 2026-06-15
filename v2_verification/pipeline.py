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
from v1_core.agents.rtl_gen_agent import rtl_gen_agent
from v1_core.agents.testbench_agent import testbench_agent
from v1_core.agents.simulation_agent import simulation_agent
from v1_core.agents.log_analysis_agent import log_analysis_agent
from v1_core.agents.fix_agent import fix_agent
from v1_core.utils import logger

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
      "end"      -- timing not met AND max timing iterations exhausted.
    """
    if state.get("timing_met", False):
        logger.success(
            f"Timing met (WNS={state.get('wns', 'N/A')}) -- pipeline complete"
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


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_v2_pipeline(
    skip_rtl_gen: bool = False,
    skip_synthesis_sta: bool = False,
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

    # ---- V1 nodes ---------------------------------------------------------
    graph.add_node("rtl_gen", rtl_gen_agent)
    graph.add_node("testbench", testbench_agent)
    graph.add_node("simulation", simulation_agent)
    graph.add_node("log_analysis", log_analysis_agent)
    graph.add_node("fix", fix_agent)

    # ---- V2 nodes ---------------------------------------------------------
    v2_available = False
    if not skip_synthesis_sta:
        if _V2_SYNTHESIS_AVAILABLE:
            graph.add_node("synthesis", synthesis_agent)
            v2_available = True
        if _V2_STA_AVAILABLE:
            graph.add_node("sta", sta_agent)
            v2_available = True
        if _V2_TIMING_OPT_AVAILABLE:
            graph.add_node("timing_opt", timing_opt_agent)

    # ---- Entry point ------------------------------------------------------
    if skip_rtl_gen:
        graph.set_entry_point("testbench")
    else:
        graph.set_entry_point("rtl_gen")
        graph.add_edge("rtl_gen", "testbench")

    # ---- Simulation pipeline (V1 flow) ------------------------------------
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

    # Fix loop: log_analysis -> fix -> testbench
    graph.add_edge("log_analysis", "fix")
    graph.add_edge("fix", "testbench")

    # ---- Synthesis / STA flow (V2) ----------------------------------------
    if v2_available:
        graph.add_edge("synthesis", "sta")

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


def run_v2_pipeline(spec: str, design_name: str) -> dict:
    """Run the full V2 pipeline (V1 + synthesis + STA) for a given spec.

    Args:
        spec: Natural-language hardware specification.
        design_name: Short identifier such as ``alu_8bit`` or ``sync_fifo``.

    Returns:
        Final ``PipelineState`` as a plain dictionary after the pipeline
        completes or is halted.
    """
    logger.divider()
    logger.info(f"Starting V2 pipeline for: {design_name}")

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
    pipeline = build_v2_pipeline()

    # Create initial state and extend with V2 fields.
    # The V2 fields (netlist_path, timing_met, etc.) are being added to
    # PipelineState / get_initial_state in orchestrator.py in parallel, but
    # we set them here explicitly so the pipeline is self-contained.
    initial_state = get_initial_state(spec=spec, design_name=design_name)
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
