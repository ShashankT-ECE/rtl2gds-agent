"""
log_analysis_agent.py
Log Analysis Agent — LangGraph node.
Parses simulation log and classifies the error using 6-category taxonomy.
Checks Trace2Skill memory for known solutions before calling LLM.
"""

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils.model_router import call_llm
from v1_core.utils.trace2skill import retrieve_skills
from v1_core.utils import logger


ERROR_TYPES = {
    "SYNTAX":   "Verilog parse or compile error",
    "WIDTH":    "Signal width mismatch",
    "LOGIC":    "Functional failure — wrong output value",
    "TIMING":   "Simulation timeout or infinite loop",
    "COVERAGE": "Simulation passed but coverage too low",
    "UNKNOWN":  "Unclassified — needs human review"
}


LOG_ANALYSIS_PROMPT = """You are an expert RTL verification engineer.
Analyze the following simulation log and classify the error.

Respond in this exact format, nothing else:
ERROR_TYPE: <one of SYNTAX, WIDTH, LOGIC, TIMING, COVERAGE, UNKNOWN>
LOCATION: <file and line number if visible, else UNKNOWN>
CAUSE: <one sentence explaining the root cause>
FIX_SUGGESTION: <one sentence describing how to fix it>
KEYWORDS: <3 to 5 comma separated keywords from the error>

Simulation Log:
{sim_log}"""


def log_analysis_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — classifies simulation errors.
    Input state fields used: sim_log, design_name
    Output state fields updated: error_analysis, trace2skill_hits, stage
    Model used: deepseek-v4-flash
    """
    logger.agent("LogAnalysisAgent", "Analyzing simulation log")

    prompt = LOG_ANALYSIS_PROMPT.format(sim_log=state["sim_log"])
    response = call_llm(prompt=prompt, task="log_analysis")

    # Parse the structured response
    error_analysis = {}
    for line in response.strip().splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            error_analysis[key.strip()] = value.strip()

    error_type = error_analysis.get("ERROR_TYPE", "UNKNOWN")
    keywords = [k.strip() for k in error_analysis.get("KEYWORDS", "").split(",")]

    logger.info(f"Error classified as: {error_type}")

    # Check Trace2Skill memory for known fixes
    category = _guess_category(state["design_name"])
    hits = retrieve_skills(
        category=category,
        error_type=error_type,
        keywords=keywords
    )

    if hits:
        logger.success(f"Trace2Skill: {len(hits)} known fix(es) found")
    else:
        logger.info("Trace2Skill: no known fixes — LLM will generate fix")

    return {
        **state,
        "error_analysis": error_analysis,
        "trace2skill_hits": hits,
        "stage": "log_analysis_done"
    }


def _guess_category(design_name: str) -> str:
    """Guess skill category from design name."""
    name = design_name.lower()
    if "fifo" in name:
        return "fifo"
    if "fsm" in name or "uart" in name or "spi" in name:
        return "fsm"
    if "axi" in name or "apb" in name:
        return "axi"
    if "timing" in name:
        return "timing"
    return "combinational"
