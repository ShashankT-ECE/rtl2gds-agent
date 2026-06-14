"""
model_router.py
Single point of contact for all DeepSeek API calls.
No agent should call DeepSeek directly — always use this file.
"""

import os
import httpx

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

# Model names
FLASH = "deepseek-v4-flash"
FLASH_THINKING = "deepseek-v4-flash"  # use thinking=True for reasoning
PRO = "deepseek-v4-pro"


def call_llm(prompt: str, task: str = "general", thinking: bool = False) -> str:
    """
    Call DeepSeek API and return the response text.

    Args:
        prompt: the full prompt to send
        task: what kind of task this is (for model selection)
        thinking: set True for root cause reasoning tasks

    Returns:
        response text as string
    """

    # Model selection based on task
    if task == "architecture" or task == "hardest":
        model = PRO
    else:
        model = FLASH

    messages = [{"role": "user", "content": prompt}]

    response = httpx.post(
        f"{DEEPSEEK_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": messages,
            "max_tokens": 2048
        },
        timeout=60.0
    )

    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
