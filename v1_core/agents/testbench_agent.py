"""
testbench_agent.py
Testbench Agent — LangGraph node.
Takes RTL code from state and generates a basic cocotb testbench.
"""

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils.model_router import call_llm
from v1_core.utils import logger

TB_PROMPT = """You are an expert verification engineer.
Generate a basic cocotb testbench for the following Verilog RTL.

IMPORTANT — cocotb 2.x API rules:
- Use `unit='ns'` (not `units='ns'`) in Timer()
- Use `int(dut.signal.value)` to read signal values (not `.value.integer`)
- Use `dut.signal.value = val` to drive signals
- `for` loop over `cocotb.types.LogicArray` is deprecated; use `int()` to compare
- Do NOT import from `cocotb.binary` — that module was removed in cocotb 2.x
- Do NOT import `BinaryValue` at all unless actually needed; compare with `int()`
- End simulation cleanly with a log message

Rules:
- Output ONLY the Python cocotb testbench code, nothing else
- No explanation, no markdown, no code fences
- Use cocotb decorators correctly
- Test basic functionality and edge cases

RTL Code:
{rtl_code}

Generate the cocotb testbench now:"""

def testbench_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — generates cocotb testbench from RTL code.
    Input state fields used: rtl_code, design_name
    Output state fields updated: testbench_code, stage
    Model used: deepseek-v4-flash
    """
    logger.agent("TestbenchAgent", f"Generating testbench for: {state['design_name']}")

    prompt = TB_PROMPT.format(rtl_code=state["rtl_code"])
    testbench_code = call_llm(prompt=prompt, task="testbench_generation")

    logger.success(f"Testbench generated — {len(testbench_code)} characters")

    return {
        **state,
        "testbench_code": testbench_code,
        "stage": "testbench_generated"
    }
