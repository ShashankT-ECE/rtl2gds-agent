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
from v1_core.utils.trace2skill import store_skill, get_curated_skills, retrieve_skills
from v1_core.utils import logger
from v1_core.utils import strip_code_fences
import json


FIX_PROMPT = """EXACT FIX REQUIRED: {exact_fix}

You must make ONLY this change and nothing else. Do not touch any other line. Do not improve anything else. Do not change comparison logic, thresholds, or structure unless the EXACT FIX explicitly says to.

You are an expert RTL design engineer fixing a Verilog bug.

CRITICAL RULES FOR FIXING:
- Change ONLY the single line or value identified in the error analysis
- Do NOT change anything else in the RTL
- Do NOT refactor, rename, or restructure
- Do NOT change multiple parameters when only one is wrong
- If the error says a parameter like GREEN_COUNT is wrong, fix ONLY that parameter value
- Make the minimal possible change that fixes the error — ideally one character

Error Analysis:
Type: {error_type}
Location: {location}
Cause: {cause}
Suggested Fix: {fix_suggestion}

The following are HINTS from memory — use them only if they directly match this exact error. Do NOT apply them blindly:
{known_fixes}

Verification Plan:
{verification_plan_json}
Failed test ID: {failed_test_id}
Expected behavior: {expected_behavior}
Actual behavior: {actual_behavior}
Change ONLY what is needed to make the actual behavior match the expected behavior per the plan.

Original RTL Code:
{rtl_code}

CRITICAL RULES — read carefully:
- Change ONLY the minimum lines needed to fix the bug. Ideally one value on one line.
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

    # Determine category
    from v1_core.agents.log_analysis_agent import _guess_category
    category = _guess_category(state["design_name"])

    # Extract precise fix instruction from error analysis
    exact_fix = error_analysis.get("EXACT_FIX", "See FIX_SUGGESTION below")

    # Format known fixes for the prompt — curated entries first, then Trace2Skill hits
    curated_hits = get_curated_skills(category, error_type)

    # Build curated hints block
    curated_text = ""
    if curated_hits:
        curated_text = "\n".join([
            f"[CURATED] Pattern: {h['pattern']} | Fix: {h['fix']}"
            for h in curated_hits
        ])
        logger.info(f"Found {len(curated_hits)} curated skill(s) for {category}/{error_type}")

    # Build Trace2Skill hits block
    if hits:
        if category == "fsm":
            hits = hits[:1]
        hits_text = "\n".join([
            f"- Pattern: {h['pattern']} | Fix: {h['fix']}"
            for h in hits
        ])
        logger.info(f"Using {len(hits)} Trace2Skill hint(s) in prompt")
    else:
        hits_text = ""

    # Combine curated + hits
    known_fixes_parts = []
    if curated_text:
        known_fixes_parts.append("=== CURATED FIXES (highest confidence) ===\n" + curated_text)
    if hits_text:
        known_fixes_parts.append("=== PREVIOUS FIXES ===\n" + hits_text)
    known_fixes_text = "\n\n".join(known_fixes_parts) if known_fixes_parts else "None available"

    # Use thinking mode for complex errors only — UNKNOWN should be simple
    use_thinking = error_type in ["LOGIC", "TIMING"]

    # Extract verification plan from state to guide fix
    verification_plan = state.get("verification_plan", {})
    verification_plan_json = json.dumps(verification_plan, indent=2)
    failed_test_id = error_analysis.get("LOCATION", "UNKNOWN")
    expected_behavior = "See verification_plan tiers"
    actual_behavior = error_analysis.get("CAUSE", "Unknown")

    prompt = FIX_PROMPT.format(
        exact_fix=exact_fix,
        error_type=error_type,
        location=error_analysis.get("LOCATION", "UNKNOWN"),
        cause=error_analysis.get("CAUSE", ""),
        fix_suggestion=error_analysis.get("FIX_SUGGESTION", ""),
        known_fixes=known_fixes_text,
        verification_plan_json=verification_plan_json,
        failed_test_id=failed_test_id,
        expected_behavior=expected_behavior,
        actual_behavior=actual_behavior,
        rtl_code=state["rtl_code"]
    )

    fixed_rtl = call_llm(
        prompt=prompt,
        task="rtl_fix",
        thinking=use_thinking
    )
    fixed_rtl = strip_code_fences(fixed_rtl)

    logger.success("Fix generated — storing tentatively in Trace2Skill")

    # Store this fix tentatively — confirmed only if next simulation passes
    skill_id = store_skill(
        category=category,
        error_type=error_type,
        pattern=error_analysis.get("CAUSE", "unknown pattern"),
        fix=error_analysis.get("FIX_SUGGESTION", ""),
        design_name=state["design_name"]
    )

    return {
        **state,
        "rtl_code": fixed_rtl,
        "testbench_code": "",  # Force testbench regeneration from fixed RTL
        "iteration": state["iteration"] + 1,
        "stage": "fix_applied",
        "pending_skill_id": skill_id
    }
