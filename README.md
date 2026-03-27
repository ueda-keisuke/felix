# Felix

A CLI-based financial research agent that thinks before it answers. Powered by a ReAct loop with Yahoo Finance tools — no paid API keys required.

Inspired by [virattt/dexter](https://github.com/virattt/dexter). Felix replaces the paid Financial Datasets API ($200+/mo) with Yahoo Finance via `yfinance`, and supports any LLM provider through `litellm`.

## Quick Start

```bash
# Install
git clone https://github.com/ueda-keisuke/felix.git
cd felix
uv sync  # or: pip install -e .

# Set your LLM API key
cp .env.example .env
# Edit .env with your API key

# Run
uv run felix
```

## Features

- **ReAct agent loop** — iterative reasoning with tool calls (up to 10 iterations)
- **10 financial tools** via Yahoo Finance (free): prices, financials, metrics, earnings, news, etc.
- **Web search** via DuckDuckGo (free, no API key)
- **Multi-provider LLM** — any model litellm supports (OpenAI, Anthropic, Google, Ollama, ...)
- **Smart context management** — auto-trims old tool results when approaching token limits
- **Scratchpad** — JSONL debug log with duplicate-call detection
- **Investment philosophy** — Buffett/Munger-inspired analysis persona (customizable via `~/.felix/SOUL.md`)

## Usage

```
$ felix

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Felix — Financial Research Agent       ┃
┃ Model: gpt-4o                          ┃
┃ Type /quit to exit, /model to switch   ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

> Compare AAPL and MSFT valuation
```

**Commands:**
- `/quit` — exit
- `/model <name>` — switch model (e.g., `/model anthropic/claude-sonnet-4-20250514`)

## Configuration

| Env Variable | Default | Description |
|---|---|---|
| `FELIX_MODEL` | `gpt-4o` | LLM model (any litellm-supported string) |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `GEMINI_API_KEY` | — | Google Gemini API key |

See `.env.example` for all options.

## Available Tools

| Tool | Description |
|---|---|
| `get_stock_price` | Current price, change, volume |
| `get_price_history` | Historical OHLCV data (1d–5y) |
| `get_income_statement` | Revenue, net income, operating income |
| `get_balance_sheet` | Assets, liabilities, equity |
| `get_cash_flow` | Operating, investing, financing flows |
| `get_key_metrics` | P/E, P/B, ROE, margins, debt ratios |
| `get_analyst_recommendations` | Price targets and consensus |
| `get_earnings` | EPS actual vs. estimate, surprise % |
| `get_company_info` | Sector, industry, description |
| `get_news` | Recent headlines for a ticker |
| `web_search` | DuckDuckGo web search |

## Architecture

```
User query
  → ReAct loop (agent.py)
    → LLM call (llm.py, via litellm)
    → Tool execution (tools/)
    → Context trimming if needed
    → Repeat until final answer
  → Rich terminal output (main.py)
```

- **`agent.py`** — ReAct loop with context management
- **`llm.py`** — thin litellm wrapper, multi-provider support
- **`tools/`** — `@tool` decorator auto-registers functions
- **`scratchpad.py`** — JSONL logging with soft call-limit warnings
- **`prompts.py`** — system prompt builder with SOUL.md injection

## Acknowledgements

This project is heavily inspired by [virattt/dexter](https://github.com/virattt/dexter), a financial research agent by Virat Singh. Felix adapts Dexter's core design patterns (ReAct loop, scratchpad, context management, SOUL persona) while replacing the paid data source with free alternatives.

## License

[MIT](LICENSE)
