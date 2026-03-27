"""Yahoo Finance tools via yfinance.

All financial data comes from Yahoo Finance (free, no API key required).
"""

from __future__ import annotations

import json

import yfinance as yf

from felix.tools.registry import tool


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _compact_number(n: float | int | None) -> str | None:
    """1_234_567_890 -> '1.23B'"""
    if n is None or (isinstance(n, float) and n != n):  # NaN
        return None
    abs_n = abs(n)
    if abs_n >= 1e12:
        return f"{n / 1e12:.2f}T"
    if abs_n >= 1e9:
        return f"{n / 1e9:.2f}B"
    if abs_n >= 1e6:
        return f"{n / 1e6:.2f}M"
    if abs_n >= 1e3:
        return f"{n / 1e3:.1f}K"
    return f"{n:.2f}"


def _df_to_json(df, max_rows: int = 8) -> str:
    """Convert a yfinance DataFrame to compact JSON."""
    if df is None or df.empty:
        return json.dumps({"error": "No data available"})
    df = df.head(max_rows)
    records: dict = {}
    for col in df.columns:
        records[str(col)] = {
            str(k): v.item() if hasattr(v, "item") else v
            for k, v in df[col].items()
        }
    return json.dumps(records, ensure_ascii=False, default=str)


def _strip_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


# ------------------------------------------------------------------
# Tools
# ------------------------------------------------------------------

@tool(
    name="get_stock_price",
    description="Get current stock price, change, volume, and key stats",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol (e.g. AAPL, MSFT)"},
    },
)
def get_stock_price(ticker: str) -> str:
    info = yf.Ticker(ticker.upper()).info
    if not info or not info.get("regularMarketPrice"):
        return json.dumps({"error": f"No data found for {ticker}"})
    return json.dumps(
        _strip_none(
            {
                "ticker": ticker.upper(),
                "price": info.get("regularMarketPrice") or info.get("currentPrice"),
                "change": info.get("regularMarketChange"),
                "change_pct": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "market_cap": _compact_number(info.get("marketCap")),
                "52w_high": info.get("fiftyTwoWeekHigh"),
                "52w_low": info.get("fiftyTwoWeekLow"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
            }
        ),
        default=str,
    )


@tool(
    name="get_price_history",
    description="Get historical OHLCV price data",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
        "period": {
            "type": "string",
            "description": "Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max (default: 1mo)",
        },
    },
    required=["ticker"],
)
def get_price_history(ticker: str, period: str = "1mo") -> str:
    df = yf.Ticker(ticker.upper()).history(period=period)
    if df.empty:
        return json.dumps({"error": f"No price history for {ticker}"})

    records = [
        {
            "date": str(idx.date()),
            "close": round(row["Close"], 2),
            "volume": int(row["Volume"]),
        }
        for idx, row in df.iterrows()
    ]
    # Downsample if too many points
    if len(records) > 20:
        step = len(records) // 20
        records = records[::step]

    return json.dumps({"ticker": ticker.upper(), "period": period, "prices": records})


@tool(
    name="get_income_statement",
    description="Get income statement (revenue, net income, operating income, etc.)",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
        "quarterly": {"type": "boolean", "description": "Quarterly instead of annual (default: false)"},
    },
    required=["ticker"],
)
def get_income_statement(ticker: str, quarterly: bool = False) -> str:
    t = yf.Ticker(ticker.upper())
    df = t.quarterly_income_stmt if quarterly else t.income_stmt
    return _df_to_json(df)


@tool(
    name="get_balance_sheet",
    description="Get balance sheet (assets, liabilities, equity)",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
        "quarterly": {"type": "boolean", "description": "Quarterly instead of annual (default: false)"},
    },
    required=["ticker"],
)
def get_balance_sheet(ticker: str, quarterly: bool = False) -> str:
    t = yf.Ticker(ticker.upper())
    df = t.quarterly_balance_sheet if quarterly else t.balance_sheet
    return _df_to_json(df)


@tool(
    name="get_cash_flow",
    description="Get cash flow statement (operating, investing, financing)",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
        "quarterly": {"type": "boolean", "description": "Quarterly instead of annual (default: false)"},
    },
    required=["ticker"],
)
def get_cash_flow(ticker: str, quarterly: bool = False) -> str:
    t = yf.Ticker(ticker.upper())
    df = t.quarterly_cashflow if quarterly else t.cashflow
    return _df_to_json(df)


@tool(
    name="get_key_metrics",
    description="Get key financial ratios and valuation metrics (P/E, P/B, ROE, margins, growth, etc.)",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
    },
)
def get_key_metrics(ticker: str) -> str:
    info = yf.Ticker(ticker.upper()).info
    if not info:
        return json.dumps({"error": f"No data for {ticker}"})

    return json.dumps(
        _strip_none(
            {
                "ticker": ticker.upper(),
                "market_cap": _compact_number(info.get("marketCap")),
                "enterprise_value": _compact_number(info.get("enterpriseValue")),
                "trailing_pe": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "price_to_sales": info.get("priceToSalesTrailing12Months"),
                "ev_to_ebitda": info.get("enterpriseToEbitda"),
                "ev_to_revenue": info.get("enterpriseToRevenue"),
                "profit_margin": info.get("profitMargins"),
                "operating_margin": info.get("operatingMargins"),
                "gross_margin": info.get("grossMargins"),
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
                "free_cash_flow": _compact_number(info.get("freeCashflow")),
                "dividend_yield": info.get("dividendYield"),
                "payout_ratio": info.get("payoutRatio"),
                "beta": info.get("beta"),
            }
        ),
        default=str,
    )


@tool(
    name="get_analyst_recommendations",
    description="Get analyst recommendations and price targets",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
    },
)
def get_analyst_recommendations(ticker: str) -> str:
    t = yf.Ticker(ticker.upper())
    info = t.info

    result: dict = {"ticker": ticker.upper()}

    for key in ("targetHighPrice", "targetLowPrice", "targetMeanPrice", "targetMedianPrice"):
        if info.get(key):
            result[key] = info[key]
    if info.get("recommendationKey"):
        result["recommendation"] = info["recommendationKey"]
    if info.get("numberOfAnalystOpinions"):
        result["num_analysts"] = info["numberOfAnalystOpinions"]

    recs = t.recommendations
    if recs is not None and not recs.empty:
        result["recent"] = recs.tail(5).to_dict(orient="records")

    return json.dumps(result, default=str)


@tool(
    name="get_earnings",
    description="Get earnings history with EPS actual vs. estimate and surprise %",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
    },
)
def get_earnings(ticker: str) -> str:
    t = yf.Ticker(ticker.upper())
    ed = t.earnings_dates
    if ed is None or ed.empty:
        return json.dumps({"error": f"No earnings data for {ticker}"})

    records = []
    for idx, row in ed.head(8).iterrows():
        records.append(
            {
                "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                "eps_estimate": row.get("EPS Estimate"),
                "eps_actual": row.get("Reported EPS"),
                "surprise_pct": row.get("Surprise(%)"),
            }
        )
    return json.dumps({"ticker": ticker.upper(), "earnings": records}, default=str)


@tool(
    name="get_company_info",
    description="Get company profile: sector, industry, description, employees, website",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
    },
)
def get_company_info(ticker: str) -> str:
    info = yf.Ticker(ticker.upper()).info
    if not info:
        return json.dumps({"error": f"No data for {ticker}"})

    return json.dumps(
        _strip_none(
            {
                "ticker": ticker.upper(),
                "name": info.get("longName") or info.get("shortName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "country": info.get("country"),
                "website": info.get("website"),
                "employees": info.get("fullTimeEmployees"),
                "description": info.get("longBusinessSummary"),
            }
        ),
        default=str,
    )


@tool(
    name="get_news",
    description="Get recent news headlines for a ticker",
    parameters={
        "ticker": {"type": "string", "description": "Stock ticker symbol"},
    },
)
def get_news(ticker: str) -> str:
    news = yf.Ticker(ticker.upper()).news
    if not news:
        return json.dumps({"error": f"No news for {ticker}"})

    articles = [
        _strip_none(
            {
                "title": item.get("title"),
                "publisher": item.get("publisher"),
                "link": item.get("link"),
                "published": item.get("providerPublishTime"),
            }
        )
        for item in news[:10]
    ]
    return json.dumps({"ticker": ticker.upper(), "news": articles}, default=str)
