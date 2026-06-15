"""
simulation_agent.py
Simulation Agent — LangGraph node.
Writes RTL and testbench to workspace, calls simulation_server, updates state.
"""

from pathlib import Path
from v1_core.agents.orchestrator import PipelineState
from v1_core.mcp_tools.simulation_server import run_simulation
from v1_core.utils import logger

WORKSPACE = Path("workspace")


def simulation_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — runs Icarus Verilog simulation.
    Input state fields used: rtl_code, testbench_code, design_name
    Output state fields updated: sim_log, sim_passed, stage
    """
    logger.agent("SimulationAgent", f"Running simulation for: {state['design_name']}")

    WORKSPACE.mkdir(exist_ok=True)

    rtl_path = WORKSPACE / f"{state['design_name']}.v"
    rtl_path.write_text(state["rtl_code"])

    # If a reference testbench path is provided, use it directly
    reference_tb_path = state.get("reference_tb_path", "")
    if reference_tb_path:
        tb_path = Path(reference_tb_path)
        logger.info(f"Using reference testbench file: {tb_path}")
    else:
        tb_path = WORKSPACE / f"{state['design_name']}_tb.py"
        tb_path.write_text(state["testbench_code"])

    result = run_simulation(rtl_file=str(rtl_path), tb_file=str(tb_path))

    if result["passed"]:
        logger.success("Simulation passed")
    else:
        logger.error("Simulation failed — passing to Log Analysis Agent")

    return {
        **state,
        "sim_log": result["log"],
        "sim_passed": result["passed"],
        "stage": "simulation_done"
    }
