"""Multi-provider LLM abstraction via litellm."""

from __future__ import annotations

import litellm

# Suppress litellm's verbose startup logging
litellm.suppress_debug_info = True

DEFAULT_MODEL = "gpt-4o"


def call_llm(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    tools: list[dict] | None = None,
) -> litellm.ModelResponse:
    """Call the LLM with optional tool definitions.

    Works with any provider litellm supports — just set the right env var
    and use the litellm model string (e.g. "anthropic/claude-sonnet-4-20250514").
    """
    kwargs: dict = {"model": model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return litellm.completion(**kwargs)
