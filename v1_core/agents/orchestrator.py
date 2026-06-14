"""
orchestrator.py
LangGraph state definition and pipeline orchestration for V1.
This is the brain of the system — defines shared state all agents read and write.
"""

from typing import TypedDict, Optional


class PipelineState(TypedDict):
    """
    Shared state passed between all agents in the LangGraph pipeline.
    Every agent reads from this and returns an updated copy.
    """
    spec: str                    # natural language hardware specification
    design_name: str             # short name like alu_8bit or sync_fifo
    rtl_code: str                # generated Verilog code
    testbench_code: str          # generated cocotb testbench
    sim_log: str                 # raw simulation output log
    sim_passed: bool             # True if simulation passed
    coverage_pct: float          # simulation coverage percentage
    error_analysis: dict         # {error_type, location, cause, fix_suggestion}
    iteration: int               # current fix loop iteration count
    max_iterations: int          # maximum allowed iterations before halting
    stage: str                   # current pipeline stage name
    trace2skill_hits: list       # skills retrieved from memory for this error


def get_initial_state(spec: str, design_name: str) -> PipelineState:
    """
    Returns a fresh PipelineState for a new design run.

    Args:
        spec: natural language specification
        design_name: short identifier for the design

    Returns:
        PipelineState with all fields initialized
    """
    return PipelineState(
        spec=spec,
        design_name=design_name,
        rtl_code="",
        testbench_code="",
        sim_log="",
        sim_passed=False,
        coverage_pct=0.0,
        error_analysis={},
        iteration=0,
        max_iterations=5,
        stage="start",
        trace2skill_hits=[]
    )
