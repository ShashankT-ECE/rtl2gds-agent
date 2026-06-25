"""
model_router.py
Single point of contact for all LLM API calls.
No agent should call an LLM directly — always use this file.

Provider-agnostic: supports deepseek, fireworks, anthropic, and ollama.
Select provider via the LLM_PROVIDER environment variable.
"""

import os
import re

# Conditional SDK imports — missing packages do not crash on import.
_openai_available = False
_anthropic_available = False

try:
    from openai import OpenAI as _OpenAI
    _openai_available = True
except ImportError:
    _OpenAI = None  # type: ignore

try:
    import anthropic as _anthropic_sdk
    _anthropic_available = True
except ImportError:
    _anthropic_sdk = None  # type: ignore

from v1_core.utils import logger
from v1_core.utils import strip_code_fences


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDERS = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "env_key": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-v4-flash",
        "thinking_model": "deepseek-v4-flash",  # thinking via API param, not model switch
        "sdk": "openai",
    },
    "fireworks": {
        "base_url": "https://api.fireworks.ai/inference/v1",
        "env_key": "FIREWORKS_API_KEY",
        "default_model": None,  # resolved at runtime via env / fallback
        "thinking_model": "accounts/fireworks/models/deepseek-r1",
        "sdk": "openai",
    },
    "anthropic": {
        "base_url": None,
        "env_key": "ANTHROPIC_API_KEY",
        "default_model": "claude-sonnet-4-6",
        "thinking_model": "claude-sonnet-4-6",
        "sdk": "anthropic",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "env_key": None,  # no API key required
        "default_model": None,  # resolved at runtime via env / fallback
        "thinking_model": None,  # same as default model
        "sdk": "openai",
    },
}

# ---------------------------------------------------------------------------
# Resolve provider & models at module load time
# ---------------------------------------------------------------------------

PROVIDER = os.environ.get("LLM_PROVIDER", "deepseek").lower().strip()

if PROVIDER not in PROVIDERS:
    logger.warning(
        "[ModelRouter] Unknown LLM_PROVIDER '%s', falling back to 'deepseek'",
        PROVIDER,
    )
    PROVIDER = "deepseek"

_cfg = PROVIDERS[PROVIDER]


def _resolve_default_model() -> str:
    """Return the default model for the current provider."""
    if PROVIDER == "fireworks":
        return os.environ.get("FIREWORKS_MODEL", "accounts/fireworks/models/deepseek-v3")
    if PROVIDER == "ollama":
        return os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
    # deepseek / anthropic
    return _cfg["default_model"] or "deepseek-v4-flash"


def _resolve_thinking_model() -> str:
    """Return the thinking model for the current provider."""
    val = _cfg["thinking_model"]
    if val is not None:
        return val
    return _resolve_default_model()


_DEFAULT_MODEL = _resolve_default_model()
_THINKING_MODEL = _resolve_thinking_model()

print(f"[ModelRouter] Provider: {PROVIDER} | Model: {_DEFAULT_MODEL}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    """Return the API key for the current provider, or '' if none required."""
    env_key = _cfg.get("env_key")
    if env_key is None:
        return ""  # ollama — no API key
    key = os.environ.get(env_key, "").strip()
    if not key:
        raise RuntimeError(
            f"call_llm: {env_key} environment variable is not set. "
            f"Provider '{PROVIDER}' requires this key. "
            f"Set it in your environment or .env file."
        )
    return key


# ---------------------------------------------------------------------------
# Provider-specific call implementations
# ---------------------------------------------------------------------------

def _call_openai(prompt: str, model: str, thinking: bool) -> str:
    """Call an OpenAI-compatible provider (deepseek, fireworks, ollama)."""
    if not _openai_available:
        raise RuntimeError(
            f"call_llm: OpenAI SDK is required for provider '{PROVIDER}'. "
            "Install with: pip install openai"
        )

    api_key = _get_api_key()
    base_url = _cfg["base_url"]

    # ollama does not require a real API key but the SDK needs a non-None value
    if PROVIDER == "ollama":
        api_key = api_key or "ollama"

    client = _OpenAI(api_key=api_key, base_url=base_url)

    messages: list[dict] = [{"role": "user", "content": prompt}]

    # For ollama thinking mode, prepend a system message to encourage reasoning
    if PROVIDER == "ollama" and thinking:
        messages.insert(0, {
            "role": "system",
            "content": "Think step by step and show your reasoning.",
        })

    kwargs: dict = {
        "model": model,
        "messages": messages,
        "max_tokens": 16000,
    }

    # DeepSeek supports a native thinking parameter.
    # Enable/disable explicitly — matches the old httpx logic where thinking
    # was controlled via the request body, not a separate model name.
    if PROVIDER == "deepseek":
        if thinking:
            kwargs["extra_body"] = {"thinking": {"type": "enabled", "budget_tokens": 16000}}
        else:
            kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        raise RuntimeError(
            f"call_llm: {PROVIDER} API call failed. Model={model}. Error: {exc}"
        ) from exc

    choice = response.choices[0]
    content = choice.message.content

    if not content or not content.strip():
        raise RuntimeError(
            f"call_llm: {PROVIDER} returned empty response. "
            f"Model={model}, provider={PROVIDER}"
        )

    return content


def _call_anthropic_direct(prompt: str, model: str, thinking: bool) -> str:
    """Call the Anthropic API via the anthropic Python SDK."""
    if not _anthropic_available:
        raise RuntimeError(
            f"call_llm: anthropic SDK is required for provider '{PROVIDER}'. "
            "Install with: pip install anthropic"
        )

    api_key = _get_api_key()
    client = _anthropic_sdk.Anthropic(api_key=api_key)

    kwargs: dict = {
        "model": model,
        "max_tokens": 16000,
        "messages": [{"role": "user", "content": prompt}],
    }

    if thinking:
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": 16000}

    try:
        response = client.messages.create(**kwargs)
    except Exception as exc:
        raise RuntimeError(
            f"call_llm: anthropic API call failed. Model={model}. Error: {exc}"
        ) from exc

    if thinking:
        # Extended thinking responses contain multiple content blocks:
        # one of type "thinking" followed by one of type "text".
        content = ""
        for block in response.content:
            if getattr(block, "type", "") == "text":
                content = block.text
                break
    else:
        content = response.content[0].text if response.content else ""

    if not content or not content.strip():
        raise RuntimeError(
            f"call_llm: anthropic returned empty response. Model={model}"
        )

    return content


# ---------------------------------------------------------------------------
# Public API  (preserved signature — all agents import this)
# ---------------------------------------------------------------------------

def call_llm(
    prompt: str,
    task: str = "general",
    thinking: bool = False,
    model: str = "",
) -> str:
    """
    Call the configured LLM provider and return the response text.

    Args:
        prompt: the full prompt to send
        task:   informational label describing the task (preserved for
                backward compatibility with existing agent code)
        thinking: if True, use the provider's reasoning model or
                  extended thinking mode
        model:  explicit model name override — takes priority over
                provider defaults and the *thinking* flag

    Returns:
        response text as a plain string (code fences stripped)
    """
    # Model selection: explicit override > thinking model > default model
    if not model:
        model = _THINKING_MODEL if thinking else _DEFAULT_MODEL

    # Route to the appropriate provider backend
    if PROVIDER == "anthropic":
        content = _call_anthropic_direct(prompt, model, thinking)
    else:
        content = _call_openai(prompt, model, thinking)

    # Strip markdown code fences from the response.
    # Callers that also call strip_code_fences() on the result are safe
    # because strip_code_fences is idempotent for already-clean text.
    content = strip_code_fences(content)

    if not content or not content.strip():
        raise RuntimeError(
            f"call_llm: LLM returned empty response after stripping. "
            f"Provider={PROVIDER}, Model={model}, task={task}"
        )

    return content
