"""
model_router.py
Single point of contact for all DeepSeek API calls.
No agent should call DeepSeek directly — always use this file.
"""

import os
import httpx
from v1_core.utils import logger

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# Model names
FLASH = "deepseek-v4-flash"
FLASH_THINKING = "deepseek-v4-flash"  # use thinking=True for reasoning
PRO = "deepseek-v4-pro"


def call_llm(prompt: str, task: str = "general", thinking: bool = False, model: str = "") -> str:
    """
    Call DeepSeek API and return the response text.

    Args:
        prompt: the full prompt to send
        task: what kind of task this is (for model selection when model is not overridden)
        thinking: set True for root cause reasoning tasks
        model: explicit model override (e.g. "deepseek-v4-pro") — takes priority over task-based selection

    Returns:
        response text as string
    """

    # Model selection — explicit override takes priority, else use task-based routing
    if not model:
        if task == "architecture" or task == "hardest":
            model = PRO
        else:
            model = FLASH

    messages = [{"role": "user", "content": prompt}]

    request_body = {
        "model": model,
        "messages": messages,
        "max_tokens": 16000,
        # Thinking disabled by default for ALL tasks — prevents the model
        # from burning all tokens on internal reasoning and returning
        # empty content. Only enabled for root_cause/architecture tasks.
        "thinking": {"type": "disabled"},
    }

    # Only enable thinking for tasks that genuinely need internal reasoning
    if task in ("root_cause", "architecture"):
        del request_body["thinking"]

    response = httpx.post(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        },
        json=request_body,
        timeout=120.0
    )

    response.raise_for_status()
    data = response.json()

    content = data["choices"][0]["message"]["content"]
    if not content or not content.strip():
        logger.info(f"Full API response: {data}")
        raise RuntimeError(
            f"call_llm: DeepSeek returned empty response. "
            f"Model={model}, task={task}, status={response.status_code}"
        )

    return content
