"""
sta_agent.py
STA (Static Timing Analysis) Agent — LangGraph node.
Runs OpenSTA timing analysis on synthesized netlists for the V2 RTL-to-GDS pipeline.
"""

from v1_core.agents.orchestrator import PipelineState
from v2_verification.mcp_tools.sta_server import _run_sta
from v1_core.utils import logger


def sta_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — runs OpenSTA static timing analysis on the synthesized netlist.

    Generates a TCL script targeting 50 MHz (20.0 ns period), executes OpenSTA
    via subprocess, and parses the output for WNS, TNS, and critical path.

    Input state fields used: netlist_path, design_name
    Output state fields updated: wns, tns, timing_met, critical_path, stage
    """
    logger.agent("STAAgent", f"Running STA for: {state['design_name']}")

    logger.info(
        f"Netlist: {state['netlist_path']} | "
        f"Target: 50 MHz (20.0 ns)"
    )

    result = _run_sta(
        netlist_file=state["netlist_path"],
        liberty_file="pdk/sky130/sky130_fd_sc_hd__tt_025C_1v80.lib",
        top_module=state["design_name"],
        clock_period_ns=20.0,
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
