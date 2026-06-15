"""
timing_opt_agent.py
Timing Optimization Agent — LangGraph node for V2 pipeline.
Analyzes STA timing reports and suggests RTL-level timing fixes when WNS < 0.
"""

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils.model_router import call_llm
from v1_core.utils import logger
from v1_core.utils import strip_code_fences


TIMING_OPT_PROMPT = """You are an expert RTL design engineer fixing a timing violation.

Below is a static timing analysis (STA) report and the current RTL code. Your job is to analyze the timing report and suggest ONE specific RTL change to fix it. Replace the original RTL code with the improved version.

TIMING REPORT:
Worst Negative Slack (WNS): {wns} ns
Total Negative Slack (TNS): {tns} ns
Critical Path: {critical_path}

CURRENT RTL CODE:
{rtl_code}

INSTRUCTIONS:
- Analyze the critical path and identify the combinational logic depth causing the timing violation.
- Suggest ONE specific RTL change to reduce the critical path delay (e.g., pipelining, reducing fan-out, simplifying combinational logic, moving logic across clock domains, etc.).
- Output the COMPLETE improved RTL code — not just a diff or snippet.
- Keep the same module interface and functionality. Do NOT change the module name or port list.
- Add comments at the changed lines explaining why the timing fix was applied.
- If the timing report shows no issue or the WNS is already positive, output the original RTL code unchanged.

Generate the complete improved Verilog RTL code now:"""


def timing_opt_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — suggests RTL timing fixes when WNS < 0.

    Reads STA results from state (wns, tns, critical_path) and the current RTL code.
    Calls the LLM with thinking enabled to root-cause the timing violation and suggest
    a targeted RTL fix. Replaces the full RTL code with the improved version.

    Input state fields used:
        rtl_code, wns, tns, critical_path
    Output state fields updated:
        rtl_code, stage
    Model used:
        deepseek-v4-flash with thinking=True
    """
    logger.agent("TimingOptAgent", "Checking timing constraints")

    wns = state.get("wns", 0.0)
    tns = state.get("tns", 0.0)
    critical_path = state.get("critical_path", "Not available")

    # Skip if timing is already met
    if wns >= 0:
        logger.info(f"Timing met (WNS={wns:.3f} ns) — no optimization needed")
        return {
            **state,
            "stage": "timing_opt_done"
        }

    logger.info(f"Timing violation detected: WNS={wns:.3f} ns, TNS={tns:.3f} ns")
    logger.info(f"Critical path: {critical_path[:200] if len(str(critical_path)) > 200 else critical_path}...")  # truncate for readability

    prompt = TIMING_OPT_PROMPT.format(
        wns=wns,
        tns=tns,
        critical_path=critical_path,
        rtl_code=state["rtl_code"]
    )

    fixed_rtl = call_llm(
        prompt=prompt,
        task="root_cause",
        thinking=True
    )
    fixed_rtl = strip_code_fences(fixed_rtl)

    logger.success(f"Timing fix generated — WNS={wns:.3f} ns, TNS={tns:.3f} ns")

    return {
        **state,
        "rtl_code": fixed_rtl,
        "stage": "timing_opt_done"
    }
