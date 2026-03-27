"""Web search tool using DuckDuckGo (free, no API key)."""

from __future__ import annotations

import json

from felix.tools.registry import tool


@tool(
    name="web_search",
    description="Search the web for general information, news, or non-financial topics",
    parameters={
        "query": {"type": "string", "description": "Search query"},
        "max_results": {
            "type": "integer",
            "description": "Max results to return (default: 5)",
        },
    },
    required=["query"],
)
def web_search(query: str, max_results: int = 5) -> str:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        return json.dumps({"error": "duckduckgo-search not installed"})

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=max_results))

    items = [
        {"title": r.get("title"), "url": r.get("href"), "snippet": r.get("body")}
        for r in results
    ]
    return json.dumps({"query": query, "results": items}, ensure_ascii=False)
