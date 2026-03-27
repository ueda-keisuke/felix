"""JSONL-based scratchpad for tracking agent work.

Source of truth for all tool results within a query. Persisted to
~/.felix/scratchpad/ for debugging/history.

Includes soft tool-call limits with warnings (never blocks) and
query similarity detection to prevent retry loops — ported from Dexter.
"""

from __future__ import annotations

import json
import hashlib
import re
from datetime import datetime
from pathlib import Path

SCRATCHPAD_DIR = Path.home() / ".felix" / "scratchpad"
MAX_CALLS_PER_TOOL = 3
SIMILARITY_THRESHOLD = 0.7


class Scratchpad:
    def __init__(self, query: str) -> None:
        SCRATCHPAD_DIR.mkdir(parents=True, exist_ok=True)

        h = hashlib.md5(query.encode()).hexdigest()[:12]
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.filepath = SCRATCHPAD_DIR / f"{ts}_{h}.jsonl"

        self._tool_call_counts: dict[str, int] = {}
        self._tool_queries: dict[str, list[str]] = {}

        self._append({"type": "init", "content": query, "timestamp": _now()})

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def add_tool_result(
        self,
        tool_name: str,
        args: dict,
        result: str,
        warning: str | None = None,
    ) -> None:
        entry: dict = {
            "type": "tool_result",
            "timestamp": _now(),
            "tool_name": tool_name,
            "args": args,
            "result": _parse_json_safe(result),
        }
        if warning:
            entry["warning"] = warning
        self._append(entry)

        self._tool_call_counts[tool_name] = (
            self._tool_call_counts.get(tool_name, 0) + 1
        )
        self._tool_queries.setdefault(tool_name, []).append(json.dumps(args))

    def add_thinking(self, thought: str) -> None:
        self._append({"type": "thinking", "content": thought, "timestamp": _now()})

    # ------------------------------------------------------------------
    # Soft limits  (warn, never block)
    # ------------------------------------------------------------------

    def check_tool_limit(
        self, tool_name: str, query: str | None = None
    ) -> dict:
        """Return ``{"warning": "..."}`` if over or near the soft limit."""
        count = self._tool_call_counts.get(tool_name, 0)

        if count >= MAX_CALLS_PER_TOOL:
            return {
                "warning": (
                    f"Tool '{tool_name}' called {count} times "
                    f"(limit: {MAX_CALLS_PER_TOOL}). "
                    "Consider: (1) a different tool, (2) different parameters, "
                    "or (3) answer with what you have."
                )
            }

        if query and self._has_similar_query(tool_name, query):
            remaining = MAX_CALLS_PER_TOOL - count
            return {
                "warning": (
                    f"Similar query already sent to '{tool_name}'. "
                    f"{remaining} attempt(s) remaining. Try different parameters."
                )
            }

        if count == MAX_CALLS_PER_TOOL - 1:
            return {
                "warning": (
                    f"Approaching limit for '{tool_name}' "
                    f"({count + 1}/{MAX_CALLS_PER_TOOL})."
                )
            }

        return {}

    def format_tool_usage(self) -> str | None:
        """Format tool usage status for injection into the next prompt."""
        if not self._tool_call_counts:
            return None

        lines: list[str] = []
        for name, count in self._tool_call_counts.items():
            if count >= MAX_CALLS_PER_TOOL:
                status = f"{count} calls (over limit of {MAX_CALLS_PER_TOOL})"
            else:
                status = f"{count}/{MAX_CALLS_PER_TOOL} calls"
            lines.append(f"- {name}: {status}")

        return (
            "## Tool Usage This Query\n\n"
            + "\n".join(lines)
            + "\n\nIf a tool isn't returning useful results, try a different approach."
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _has_similar_query(self, tool_name: str, query: str) -> bool:
        new_words = _tokenize(query)
        for prev in self._tool_queries.get(tool_name, []):
            if _jaccard(new_words, _tokenize(prev)) >= SIMILARITY_THRESHOLD:
                return True
        return False

    def _append(self, entry: dict) -> None:
        with open(self.filepath, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")


# ------------------------------------------------------------------
# Pure helpers (module-level for testability)
# ------------------------------------------------------------------

def _now() -> str:
    return datetime.now().isoformat()


def _parse_json_safe(text: str) -> object:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _tokenize(text: str) -> set[str]:
    return {w for w in re.sub(r"[^\w\s]", " ", text.lower()).split() if len(w) > 2}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
