"""
spec_parser_agent.py
First agent in the pipeline. Parses natural language spec into structured format.
Gives all subsequent agents clear design intent — prevents fix agent from guessing.
"""

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils.model_router import call_llm
from v1_core.utils import logger
import json

SPEC_PARSER_PROMPT = """You are a hardware design specification analyst.
Parse the following natural language hardware specification into a structured JSON object.

Output ONLY valid JSON, nothing else. No markdown, no explanation.

Required JSON structure:
{{
  "module_name": "exact verilog module name",
  "design_type": "combinational|sequential|fsm|protocol",
  "inputs": [{{"name": "signal", "width": 1, "description": "what it does"}}],
  "outputs": [{{"name": "signal", "width": 1, "description": "what it does"}}],
  "behavior": ["rule 1", "rule 2"],
  "corner_cases": ["edge case 1", "edge case 2"],
  "clock": "clk signal name or null if combinational",
  "reset": "reset signal name or null"
}}

Specification:
{spec}"""

def spec_parser_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — parses spec into structured format.
    Must be the FIRST node in every pipeline.
    Input: state.spec
    Output: state.spec_analysis
    """
    logger.agent("SpecParserAgent", f"Parsing spec for: {state['design_name']}")

    prompt = SPEC_PARSER_PROMPT.format(spec=state["spec"])
    response = call_llm(prompt=prompt, task="general", thinking=False)

    # Strip any accidental markdown
    clean = response.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1])

    try:
        spec_analysis = json.loads(clean)
        logger.success(f"Spec parsed: {spec_analysis['design_type']} design, {len(spec_analysis['inputs'])} inputs, {len(spec_analysis['outputs'])} outputs")
    except json.JSONDecodeError:
        logger.warning("Spec parsing failed — using empty analysis")
        spec_analysis = {"design_type": "unknown", "behavior": [], "corner_cases": []}

    return {**state, "spec_analysis": spec_analysis, "stage": "spec_parsed"}
