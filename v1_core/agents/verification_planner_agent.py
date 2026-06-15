"""
verification_planner_agent.py
Second agent in the pipeline. Takes spec_analysis and generates a structured
verification plan with tiers, reference model, and timing requirements.
Runs AFTER spec_parser_agent and BEFORE rtl_gen_agent.
"""

from v1_core.agents.orchestrator import PipelineState
from v1_core.utils.model_router import call_llm
from v1_core.utils import logger
import json

VERIFICATION_PLANNER_PROMPT = """You are a hardware verification planning expert.
Generate a structured verification plan from the following specification analysis.

Output ONLY valid JSON, no markdown. No explanation, no code fences.

Required JSON structure:
{{
  "design_name": "module name",
  "design_type": "combinational|sequential|fsm|protocol",
  "verification_tiers": [
    {{
      "tier": 1,
      "name": "Reset and Initialization",
      "tests": [
        {{
          "test_id": "T1_RESET",
          "description": "What the test does",
          "stimulus": {{"input_conditions": "values"}},
          "expected": {{"output_conditions": "values"}},
          "pass_criteria": "How to determine pass"
        }}
      ]
    }},
    {{
      "tier": 2,
      "name": "Functional Verification",
      "tests": [
        {{
          "test_id": "T2_FUNC_001",
          "description": "What the test does",
          "stimulus": {{"input_conditions": "values"}},
          "expected": {{"output_conditions": "values"}},
          "pass_criteria": "How to determine pass"
        }}
      ]
    }},
    {{
      "tier": 3,
      "name": "Boundary and Corner Cases",
      "tests": [
        {{
          "test_id": "T3_BOUNDARY_001",
          "description": "What the test does",
          "stimulus": {{"input_conditions": "values"}},
          "expected": {{"output_conditions": "values"}},
          "pass_criteria": "How to determine pass"
        }}
      ]
    }}
  ],
  "reference_model_code": "Python function string — def reference_model(inputs: dict) -> dict: ...",
  "forbidden_behaviors": ["list of things that must never happen"],
  "timing_requirements": {{
    "clock_signal": "clk signal name or null if combinational",
    "clock_period_ns": 10.0 or null if combinational,
    "skip_sta": true if design_type is combinational else false
  }}
}}

Instructions:
- Generate exactly 3 tiers: Tier 1 (Reset and Initialization), Tier 2 (Functional Verification), Tier 3 (Boundary and Corner Cases).
- Each tier must have at least 2 tests with meaningful stimulus/expected/pass_criteria.
- Generate a reference_model as a Python function string. The function must be named reference_model and take a single dict parameter called inputs and return a dict.
- The reference_model function should implement the expected behavior of the design based on the spec.
- Extract clock signal and clock period from the specification analysis. Set to null if combinational.
- Set skip_sta=true if design_type is combinational, otherwise false.
- List at least 3 forbidden behaviors that must never occur in the design.

Specification Analysis:
{spec_analysis}"""


def verification_planner_agent(state: PipelineState) -> PipelineState:
    """
    LangGraph node — generates a structured verification plan from spec_analysis.
    Must run AFTER spec_parser_agent and BEFORE rtl_gen_agent.
    Input: state.spec_analysis
    Output: state.verification_plan
    """
    logger.agent("VerificationPlannerAgent", f"Generating plan for: {state['design_name']}")

    spec_analysis_json = json.dumps(state["spec_analysis"], indent=2)
    prompt = VERIFICATION_PLANNER_PROMPT.format(spec_analysis=spec_analysis_json)
    response = call_llm(prompt=prompt, task="general", thinking=False)

    # Strip any accidental markdown
    clean = response.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1])

    try:
        verification_plan = json.loads(clean)
        tiers = verification_plan.get("verification_tiers", [])
        total_tests = sum(len(t.get("tests", [])) for t in tiers)
        logger.success(f"Plan generated: {len(tiers)} tiers, {total_tests} tests")
    except json.JSONDecodeError:
        logger.warning("Verification plan parsing failed — using empty plan")
        verification_plan = {
            "design_name": state["design_name"],
            "design_type": state["spec_analysis"].get("design_type", "unknown"),
            "verification_tiers": [],
            "reference_model_code": "",
            "forbidden_behaviors": [],
            "timing_requirements": {
                "clock_signal": None,
                "clock_period_ns": None,
                "skip_sta": True
            }
        }

    return {**state, "verification_plan": verification_plan, "stage": "plan_generated"}
