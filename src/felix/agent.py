"""Core ReAct agent loop with scratchpad and context management.

Ported from Dexter's architecture:
- Iterative tool-calling loop with configurable max iterations
- Scratchpad as single source of truth (JSONL debug log)
- Soft tool-call limits injected as warnings (never blocks)
- Anthropic-style context management: keep full tool results,
  trim oldest tool-call groups when token threshold exceeded
"""

from __future__ import annotations

import json
from typing import Generator

from felix.llm import call_llm
from felix.prompts import build_system_prompt
from felix.scratchpad import Scratchpad
from felix.tools.registry import get_openai_tools, get_tool_descriptions, get_tool_map
from felix.utils.tokens import CONTEXT_THRESHOLD, KEEP_RECENT_TOOLS, estimate_tokens

DEFAULT_MAX_ITERATIONS = 10


class Agent:
    def __init__(self, model: str, max_iterations: int = DEFAULT_MAX_ITERATIONS) -> None:
        self.model = model
        self.max_iterations = max_iterations
        self.tool_map = get_tool_map()
        self.openai_tools = get_openai_tools()
        self.system_prompt = build_system_prompt(get_tool_descriptions())

    def run(self, query: str) -> Generator[dict, None, None]:
        """Run the agent loop, yielding events for real-time UI updates."""
        scratchpad = Scratchpad(query)

        messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": query},
        ]

        for iteration in range(1, self.max_iterations + 1):
            # ---- LLM call ------------------------------------------------
            try:
                response = call_llm(messages, model=self.model, tools=self.openai_tools)
            except Exception as e:
                yield {"type": "error", "message": str(e)}
                return

            msg = response.choices[0].message

            # ---- Thinking (text alongside tool calls) --------------------
            if msg.content and msg.tool_calls:
                scratchpad.add_thinking(msg.content)
                yield {"type": "thinking", "message": msg.content}

            # ---- No tool calls → final answer ----------------------------
            if not msg.tool_calls:
                yield {"type": "done", "answer": msg.content or "", "iterations": iteration}
                return

            # ---- Execute tool calls --------------------------------------
            messages.append(_dump_message(msg))

            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                limit_check = scratchpad.check_tool_limit(tool_name, json.dumps(args))
                warning = limit_check.get("warning")

                yield {"type": "tool_start", "tool": tool_name, "args": args}

                tool_obj = self.tool_map.get(tool_name)
                if tool_obj:
                    try:
                        result = tool_obj.fn(**args)
                    except Exception as e:
                        result = json.dumps({"error": str(e)})
                else:
                    result = json.dumps({"error": f"Unknown tool: {tool_name}"})

                scratchpad.add_tool_result(tool_name, args, result, warning)

                content = f"[WARNING: {warning}]\n\n{result}" if warning else result
                messages.append(
                    {"role": "tool", "tool_call_id": tc.id, "content": content}
                )

                yield {"type": "tool_end", "tool": tool_name, "result": result}

            # ---- Context management --------------------------------------
            messages = _trim_context(messages)

            # ---- Inject tool usage status after first iteration -----------
            usage = scratchpad.format_tool_usage()
            if usage and iteration > 1:
                messages.append({"role": "user", "content": usage})

        yield {
            "type": "done",
            "answer": f"Reached maximum iterations ({self.max_iterations}).",
            "iterations": self.max_iterations,
        }


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _dump_message(msg) -> dict:
    """Convert an LLM response message to a plain dict for the messages list."""
    d: dict = {"role": "assistant"}
    if msg.content:
        d["content"] = msg.content
    if msg.tool_calls:
        d["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in msg.tool_calls
        ]
    return d


def _trim_context(messages: list[dict]) -> list[dict]:
    """Remove oldest tool-call groups when estimated tokens exceed threshold.

    A "group" is an assistant message with tool_calls plus its subsequent
    tool-result messages. We remove complete groups to keep the message
    list valid for the API.
    """
    total_chars = sum(len(str(m.get("content", ""))) for m in messages)
    if total_chars // 4 <= CONTEXT_THRESHOLD:
        return messages

    # Identify groups: (start_index, end_index_exclusive)
    groups: list[tuple[int, int]] = []
    i = 0
    while i < len(messages):
        m = messages[i]
        if m.get("role") == "assistant" and m.get("tool_calls"):
            start = i
            j = i + 1
            while j < len(messages) and messages[j].get("role") == "tool":
                j += 1
            groups.append((start, j))
            i = j
        else:
            i += 1

    if len(groups) <= KEEP_RECENT_TOOLS:
        return messages

    # Remove oldest groups, keep the most recent
    to_remove: set[int] = set()
    for start, end in groups[: -KEEP_RECENT_TOOLS]:
        to_remove.update(range(start, end))

    return [m for i, m in enumerate(messages) if i not in to_remove]
