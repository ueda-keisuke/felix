"""Tool registry with decorator-based registration.

Tools register themselves at import time via the ``@tool`` decorator.
The agent imports the tool modules to trigger registration, then queries
the registry for OpenAI-format tool definitions and dispatch functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

_registry: list[Tool] = []


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    required: list[str] = field(default_factory=list)
    fn: Callable[..., str] = field(default=lambda **_kw: "", repr=False)


def tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    required: list[str] | None = None,
):
    """Decorator that registers a function as an agent tool."""

    def decorator(fn: Callable[..., str]) -> Callable[..., str]:
        _registry.append(
            Tool(
                name=name,
                description=description,
                parameters=parameters,
                required=required if required is not None else list(parameters.keys()),
                fn=fn,
            )
        )
        return fn

    return decorator


def get_tools() -> list[Tool]:
    return list(_registry)


def get_tool_map() -> dict[str, Tool]:
    return {t.name: t for t in _registry}


def get_openai_tools() -> list[dict]:
    """Convert registry to OpenAI function-calling format."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": {
                    "type": "object",
                    "properties": t.parameters,
                    "required": t.required,
                },
            },
        }
        for t in _registry
    ]


def get_tool_descriptions() -> str:
    """Human-readable tool list for the system prompt."""
    lines: list[str] = []
    for t in _registry:
        params = ", ".join(
            f"{k}: {v.get('description', '')}" for k, v in t.parameters.items()
        )
        lines.append(f"- **{t.name}**({params}): {t.description}")
    return "\n".join(lines)
