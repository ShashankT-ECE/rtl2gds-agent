"""
rtl_gen_agent.py
RTL Generation Agent — LangGraph node.
Takes natural language spec from state and generates synthesizable Verilog.
Uses model_router for all LLM calls — never calls DeepSeek directly.
"""

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils.model_router import call_llm
from v1_core.utils import logger
from v1_core.utils import strip_code_fences


RTL_PROMPT = """You are an expert RTL design engineer.
Generate synthesizable Verilog HDL code for the following specification.

Rules:
- Output ONLY the Verilog code, nothing else
- No explanation, no markdown, no code fences
- Use only synthesizable constructs
- Follow clean coding style with comments
- All ports must be explicitly declared

Specification:
{spec}

Generate the complete Verilog module now:"""


def rtl_gen_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — generates Verilog RTL from natural language spec.

    Input state fields used: spec, design_name
    Output state fields updated: rtl_code, stage
    Model used: deepseek-v4-flash
    """
    logger.agent("RTLGenAgent", f"Generating RTL for: {state['design_name']}")

    prompt = RTL_PROMPT.format(spec=state["spec"])

    rtl_code = call_llm(prompt=prompt, task="rtl_generation", thinking=False)
    rtl_code = strip_code_fences(rtl_code)

    logger.success(f"RTL generated — {len(rtl_code)} characters")

    return {
        **state,
        "rtl_code": rtl_code,
        "stage": "rtl_generated"
    }
