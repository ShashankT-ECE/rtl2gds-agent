"""
testbench_agent.py
Testbench Agent — LangGraph node.
Takes RTL code from state and generates a basic cocotb testbench.
"""

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils.model_router import call_llm
from v1_core.utils import logger
from v1_core.utils import strip_code_fences

TB_PROMPT = """CRITICAL: You must generate a COMPLETE, FULLY FUNCTIONAL cocotb testbench. Do not truncate. Do not summarize. Write every single test in full. Minimum 50 lines of actual test code.

You are an expert verification engineer.
Generate a cocotb testbench for the following Verilog RTL.

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

{fifo_requirements}
RTL Code:
{rtl_code}

Generate the COMPLETE cocotb testbench now — every test fully coded, no placeholders, no ellipsis, no "write similar tests":"""

FIFO_TB_REQUIREMENTS = """CRITICAL — YOU MUST INCLUDE ALL OF THE FOLLOWING TESTS IN YOUR TESTBENCH. DO NOT SKIP ANY. DO NOT SUBSTITUTE. WRITE EACH ONE AS A SEPARATE @cocotb.test() FUNCTION.

TIMING NOTE: full and empty are COMBINATIONAL (they reflect count instantly, no clock edge delay). After a write RisingEdge completes, you can check full immediately on the next RisingEdge.

YOU ARE REQUIRED TO IMPLEMENT THESE TESTS EXACTLY AS DESCRIBED:

TEST — write_15_not_full: Write 15 entries. After each write, assert full==0. This proves full does NOT assert early.

TEST — write_16th_full: Write the 16th entry. Then assert full==1. This proves full asserts at the correct threshold.

TEST — write_overflow_blocked: After full==1, try writing another entry. Assert full==1 still.

TEST — read_all_16_empty: Read all 16 entries. After the last read, assert empty==1.

TEST — simultaneous_write_read: Write and read simultaneously. Verify data integrity.

TEST — reset_check: After reset, assert empty==1 and full==0.

FAILURE TO INCLUDE ALL THESE TESTS WILL CAUSE THE ENTIRE SIMULATION TO FAIL.
"""

def testbench_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — generates cocotb testbench from RTL code.
    Input state fields used: rtl_code, design_name
    Output state fields updated: testbench_code, stage
    Model used: deepseek-v4-flash
    """
    logger.agent("TestbenchAgent", f"Generating testbench for: {state['design_name']}")

    # Detect if design is a FIFO and append FIFO-specific requirements
    rtl_code = state["rtl_code"]
    if "FIFO" in rtl_code or "fifo" in rtl_code:
        logger.info("FIFO design detected — appending FIFO-specific test requirements")
        fifo_requirements = FIFO_TB_REQUIREMENTS
    else:
        fifo_requirements = ""

    prompt = TB_PROMPT.format(rtl_code=rtl_code, fifo_requirements=fifo_requirements)
    if fifo_requirements:
        logger.info("Using deepseek-v4-flash for FIFO test generation")
    testbench_code = call_llm(prompt=prompt, task="testbench_generation", thinking=False)
    logger.info(f"Raw LLM response (first 200 chars): {testbench_code[:200]!r}")
    testbench_code = strip_code_fences(testbench_code)

    logger.success(f"Testbench generated — {len(testbench_code)} characters")

    return {
        **state,
        "testbench_code": testbench_code,
        "stage": "testbench_generated"
    }
