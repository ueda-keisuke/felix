# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Felix is a CLI-based financial research agent built in Python, inspired by [virattt/dexter](https://github.com/virattt/dexter). Uses Yahoo Finance (free) instead of Financial Datasets API ($200+/mo). Multi-provider LLM support via litellm.

## Commands

- **Install:** `uv sync` (or `pip install -e .`)
- **Run:** `uv run felix` (or `python -m felix`)
- **Run directly:** `uv run python src/felix/main.py`

## Architecture

**ReAct agent loop** (`agent.py`): Iterative tool-calling loop (max 10 iterations). Calls LLM with tool definitions, executes tool calls, appends results to message history, repeats until the LLM responds without tool calls.

Key design patterns ported from Dexter:
- **Scratchpad** (`scratchpad.py`): JSONL append-only log in `~/.felix/scratchpad/`. Source of truth for debugging. Includes soft tool-call limits with Jaccard similarity detection to prevent retry loops.
- **Context management**: Full tool results kept in message history. When token estimate exceeds threshold, oldest tool-call groups (assistant + tool messages) are trimmed.
- **SOUL.md persona injection**: Investment philosophy (Buffett/Munger) injected into system prompt. User can override at `~/.felix/SOUL.md`.

**Tools** (`tools/`): Registered via `@tool` decorator at import time.
- `tools/finance.py` — Yahoo Finance via `yfinance` (10 tools: prices, financials, metrics, earnings, news, etc.)
- `tools/search.py` — DuckDuckGo web search (free, no API key)

**LLM** (`llm.py`): Thin wrapper around `litellm.completion()`. Set `FELIX_MODEL` env var to change model (default: `gpt-4o`). Any litellm-supported model string works.

## Coding Conventions

- Python 3.11+, type hints throughout
- `from __future__ import annotations` in all modules
- Tools are plain functions returning JSON strings, registered via decorator
- No classes where functions suffice
