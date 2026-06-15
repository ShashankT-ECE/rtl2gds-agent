"""
sta_agent.py
STA (Static Timing Analysis) Agent — LangGraph node.
Runs OpenSTA timing analysis on synthesized netlists for the V2 RTL-to-GDS pipeline.
Clock period is auto-detected from the verification_plan in pipeline state.
"""

from v1_core.agents.orchestrator import PipelineState
from v2_verification.mcp_tools.sta_server import _run_sta
from v1_core.utils import logger


def sta_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — runs OpenSTA static timing analysis on the synthesized netlist.

    Reads timing requirements from verification_plan in pipeline state:
      - clock_signal: if None, design is combinational — skip STA.
      - clock_period_ns: target period (default 20.0 ns if not specified).
      - skip_sta: explicit flag to bypass STA.

    Input state fields used: netlist_path, design_name, verification_plan
    Output state fields updated: wns, tns, timing_met, critical_path, stage
    """
    # --- Clock auto-detection from verification_plan ---
    verification_plan = state.get("verification_plan", {})
    timing_reqs = verification_plan.get("timing_requirements", {})

    if timing_reqs.get("skip_sta", False) or timing_reqs.get("clock_signal") is None:
        logger.info(
            "Verification plan indicates combinational design or no clock — "
            "skipping STA"
        )
        return {
            **state,
            "wns": 0.0,
            "tns": 0.0,
            "timing_met": True,
            "critical_path": (
                "STA skipped per verification_plan "
                "(combinational or no clock)"
            ),
            "stage": "sta_skipped",
        }

    clock_period_ns = timing_reqs.get("clock_period_ns", 20.0)

    logger.agent("STAAgent", f"Running STA for: {state['design_name']}")

    logger.info(
        f"Netlist: {state['netlist_path']} | "
        f"Target: {round(1e3 / clock_period_ns)} MHz ({clock_period_ns} ns)"
    )

    result = _run_sta(
        netlist_file=state["netlist_path"],
        liberty_file="pdk/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib",
        top_module=state["design_name"],
        clock_period_ns=clock_period_ns,
    )

    if not result["timing_met"]:
        logger.warning(
            f"Timing not met — WNS={result['wns']}, TNS={result['tns']}"
        )
        logger.warning(f"Critical path: {result['critical_path']}")
    else:
        logger.success(
            f"Timing met — WNS={result['wns']}, TNS={result['tns']}"
        )

    return {
        **state,
        "wns": result["wns"],
        "tns": result["tns"],
        "timing_met": result["timing_met"],
        "critical_path": result["critical_path"],
        "stage": "sta_done",
    }
