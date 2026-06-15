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

CRITICAL: The DUT toplevel module name is {design_name}. All references to dut must match this exact module name.

IMPORTANT — cocotb 2.x API rules:
- Use `unit='ns'` (not `units='ns'`) in Timer()
- Use `int(dut.signal.value)` to read signal values (not `.value.integer`)
- Use `dut.signal.value = val` to drive signals
- `for` loop over `cocotb.types.LogicArray` is deprecated; use `int()` to compare
- Do NOT import from `cocotb.binary` — that module was removed in cocotb 2.x
- Do NOT import `BinaryValue` at all unless actually needed; compare with `int()`
- Do NOT import anything from `cocotb.handle` — ModifiableObject and NonImplObject do not exist in cocotb 2.x
- Do NOT import numpy — it is not needed for cocotb testbenches
- End simulation cleanly with a log message

Rules:
- Output ONLY the Python cocotb testbench code, nothing else
- No explanation, no markdown, no code fences
- Use cocotb decorators correctly
- Test basic functionality and edge cases

MANDATORY REFERENCE MODEL:
Before writing any @cocotb.test() functions, implement this function:

def reference_model(inputs):
    # Pure Python implementation of the design spec
    # inputs: dict of signal names to values
    # returns: dict of expected output signal names to values
    # This function must NOT interact with the DUT

All test assertions MUST use this pattern:
    _expected = reference_model(dict(signal_name=int(dut.signal_name.value)))
    assert int(dut.output.value) == _expected['output'], f'Expected ' + str(_expected['output']) + ', got ' + str(int(dut.output.value))

Never hardcode expected values directly in assertions.

{fifo_requirements}
{timing_requirements}
{regeneration_note}
Structured specification analysis: {spec_analysis}
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

TIMING_TB_REQUIREMENTS = """MANDATORY TIMING TESTS — The RTL uses timing parameters (COUNT) with counter comparison at X_COUNT-1.

CRITICAL TIMING RULE — Copy this exact pattern for each state:
For a state with X_COUNT that transitions to NEXT_STATE, use this assertion pattern:

    // State should stay for X_COUNT-1 edges
    for i in range(X_COUNT - 1):
        await RisingEdge(dut.clk)
        assert int(dut.state_out) == THIS_STATE_ENCODING
        assert int(dut.THIS_LIGHT) == 1

    // After X_COUNT-1 edges, still current state (one RisingEdge before transition)
    await RisingEdge(dut.clk)
    assert int(dut.state_out) == THIS_STATE_ENCODING
    assert int(dut.THIS_LIGHT) == 1

    // After X_COUNT edges, HAS transitioned (the transition happened ON this edge)
    await RisingEdge(dut.clk)
    assert int(dut.state_out) == NEXT_STATE_ENCODING
    assert int(dut.NEXT_LIGHT) == 1

EXAMPLE for RED (encoding=0, RED_COUNT=15, transitions to GREEN encoding=1):
    for i in range(14):
        await RisingEdge(dut.clk)
        assert int(dut.state_out) == 0
        assert int(dut.red_light) == 1
    await RisingEdge(dut.clk)
    assert int(dut.state_out) == 0  # still RED
    assert int(dut.red_light) == 1
    await RisingEdge(dut.clk)
    assert int(dut.state_out) == 1  # now GREEN
    assert int(dut.green_light) == 1

Apply this exact pattern for ALL three states using their actual parameter values.
"""

def testbench_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — generates cocotb testbench from RTL code.
    Input state fields used: rtl_code, design_name
    Output state fields updated: testbench_code, stage
    Model used: deepseek-v4-flash
    """
    logger.agent("TestbenchAgent", f"Generating testbench for: {state['design_name']}")

    # If this is a regeneration after an RTL fix, add a regeneration note
    regeneration_note = ""
    if state.get("iteration", 0) > 0:
        logger.info("Regenerating testbench after RTL fix — cleared stale testbench")
        regeneration_note = (
            "NOTE: This testbench is being regenerated after an RTL fix. "
            "Generate tests based purely on the specification and RTL logic shown — "
            "do NOT assume any specific parameter values. "
            "Read parameter values from the RTL module directly and use them in your test calculations."
        )

    # Detect if design is a FIFO and append FIFO-specific requirements
    rtl_code = state["rtl_code"]
    if "FIFO" in rtl_code or "fifo" in rtl_code:
        logger.info("FIFO design detected — appending FIFO-specific test requirements")
        fifo_requirements = FIFO_TB_REQUIREMENTS
    else:
        fifo_requirements = ""

    # Detect timing parameters (COUNT, CYCLES) in the RTL and add timing boundary tests
    if "COUNT" in rtl_code or "_COUNT" in rtl_code or "CYCLES" in rtl_code or "count" in rtl_code:
        logger.info("Timing parameters detected — appending boundary timing test requirements")
        timing_requirements = TIMING_TB_REQUIREMENTS
    else:
        timing_requirements = ""

    import json

    prompt = TB_PROMPT.format(rtl_code=rtl_code, fifo_requirements=fifo_requirements, timing_requirements=timing_requirements, regeneration_note=regeneration_note, design_name=state["design_name"], spec_analysis=json.dumps(state.get("spec_analysis", {}), indent=2))
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
