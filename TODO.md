# TODO

## Deferred from Dexter

- [ ] SEC EDGAR integration (10-K, 10-Q, 8-K filing text retrieval)
- [ ] Insider trading data (SEC Form 4 via EDGAR)
- [ ] Stock screener (filter by financial criteria)
- [ ] Segmented revenue breakdown
- [ ] Skills system (SKILL.md-based extensible workflows, e.g. DCF valuation)
- [ ] Memory system (SQLite + embeddings for persistent context)
- [ ] Heartbeat / cron system (periodic checks)
- [ ] Multi-channel gateway (WhatsApp, Telegram, etc.)
- [ ] Evaluation framework (LangSmith-based)
- [ ] Tool approval flow (user confirmation for dangerous operations)
- [ ] Interactive model switching via `/model` command with API key prompting
- [ ] Conversation history persistence across sessions

## Enhancements

- [ ] Streaming response output (token-by-token)
- [ ] Meta-tool: single `get_financials(query)` that routes to sub-tools via LLM
- [ ] Cryptocurrency support (yfinance supports some crypto tickers)
- [ ] Chart rendering in terminal (sparklines or ASCII plots)
- [ ] Export research to markdown file
