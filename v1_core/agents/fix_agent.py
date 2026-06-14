"""
fix_agent.py
Fix Agent — LangGraph node.
1. Checks Trace2Skill hits from Log Analysis Agent first
2. If known fix exists, applies it directly
3. If no known fix, calls LLM to generate fix
4. Stores every successful fix back into Trace2Skill
"""

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils.model_router import call_llm
from v1_core.utils.trace2skill import store_skill
from v1_core.utils import logger
from v1_core.utils import strip_code_fences


FIX_PROMPT = """You are an expert RTL design engineer fixing a Verilog bug.

Error Analysis:
Type: {error_type}
Location: {location}
Cause: {cause}
Suggested Fix: {fix_suggestion}

Known fixes from memory:
{known_fixes}

Original RTL Code:
{rtl_code}

CRITICAL RULES — read carefully:
- Change ONLY the minimum lines needed to fix the bug. Ideally one line.
- NEVER change the sensitivity list of always blocks.
- NEVER change blocking ( = ) to non-blocking ( <= ) or vice versa.
- NEVER change registered logic (always @(posedge clk)) to combinational (always @(*)) or vice versa.
- NEVER add, remove, or restructure modules or always blocks.
- Output the COMPLETE module, but with surgical changes only.
- Keep all original comments, structure, and coding style exactly as-is.

Generate the corrected Verilog now:"""


def fix_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — fixes RTL based on error analysis.
    Input state fields used: rtl_code, error_analysis, trace2skill_hits, iteration
    Output state fields updated: rtl_code, iteration, stage
    Model used: deepseek-v4-flash (simple fix) / deepseek-v4-flash thinking (complex)
    """
    logger.agent("FixAgent", f"Attempting fix — iteration {state['iteration'] + 1}")

    error_analysis = state["error_analysis"]
    error_type = error_analysis.get("ERROR_TYPE", "UNKNOWN")
    hits = state["trace2skill_hits"]

    # Format known fixes for the prompt
    if hits:
        known_fixes_text = "\n".join([
            f"- Pattern: {h['pattern']} | Fix: {h['fix']}"
            for h in hits
        ])
        logger.info(f"Using {len(hits)} Trace2Skill hint(s) in prompt")
    else:
        known_fixes_text = "None available"

    # Use thinking mode for complex errors only — UNKNOWN should be simple
    use_thinking = error_type in ["LOGIC", "TIMING"]

    prompt = FIX_PROMPT.format(
        error_type=error_type,
        location=error_analysis.get("LOCATION", "UNKNOWN"),
        cause=error_analysis.get("CAUSE", ""),
        fix_suggestion=error_analysis.get("FIX_SUGGESTION", ""),
        known_fixes=known_fixes_text,
        rtl_code=state["rtl_code"]
    )

    fixed_rtl = call_llm(
        prompt=prompt,
        task="rtl_fix",
        thinking=use_thinking
    )
    fixed_rtl = strip_code_fences(fixed_rtl)

    logger.success("Fix generated — storing in Trace2Skill")

    # Store this fix in Trace2Skill memory
    from v1_core.agents.log_analysis_agent import _guess_category
    category = _guess_category(state["design_name"])

    store_skill(
        category=category,
        error_type=error_type,
        pattern=error_analysis.get("CAUSE", "unknown pattern"),
        fix=error_analysis.get("FIX_SUGGESTION", ""),
        design_name=state["design_name"]
    )

    return {
        **state,
        "rtl_code": fixed_rtl,
        "iteration": state["iteration"] + 1,
        "stage": "fix_applied"
    }
