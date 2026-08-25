# Robinhood ETF Research Agent

Read-only, paper-only research system for a 30-day evaluation of five liquid ETFs:

| Symbol | Exposure |
|---|---|
| SPY | U.S. large-cap stocks |
| QQQ | Nasdaq-100 growth stocks |
| IWM | U.S. small-cap stocks |
| TLT | Long-term U.S. Treasuries |
| GLD | Gold |

The project does **not** connect to Robinhood, contain Robinhood credentials, or include order-entry code. It uses public end-of-day prices, maintains a fictional $10,000 portfolio, explains every hypothetical action, and publishes a static dashboard with GitHub Pages.

## Research rules: 100 techniques without fake confirmation

The agent evaluates exactly **100 fully specified price techniques** across ten research-backed families: absolute momentum, price/SMA trend, dual SMA, dual EMA, breakouts, 52-week-high proximity, risk-adjusted momentum, drawdown control, volatility regimes, and trend-conditioned short-term reversal.

Each family contains ten parameter variants but gets only one vote. A family passes when at least 60% of its techniques are bullish. Entry requires at least six of ten independent families plus a close above the 200-day SMA. Exit occurs at three or fewer bullish families, below the 200-day SMA, or at 20-day momentum of -5% or worse.

Candidates are ranked first by family agreement and then by momentum. The paper portfolio holds at most three ETFs, targets 25% of equity per position, keeps at least 10% in cash, and applies 0.05% hypothetical slippage.

These rules are intentionally deterministic. The explanations describe all family votes; an LLM never decides whether a trade occurs. See [research/EVIDENCE.md](research/EVIDENCE.md) for the primary-source review, exact family design, and explicit limitations.

## Quick start

1. Create a new empty GitHub repository.
2. Copy this project's contents into it and push to `main`.
3. In **Settings → Pages**, choose **GitHub Actions** as the source.
4. Open **Actions → ETF paper research → Run workflow** for the first run.
5. The weekday schedule runs once after the U.S. market close.

See [SETUP.md](SETUP.md) for click-by-click instructions.

## Local commands

```bash
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.run_scan
```

Generated evaluation records live in `state/`. The dashboard is `docs/index.html`. All state-changing events are appended to a hash-chained `state/audit.jsonl` log.

## Safety boundary

- `paper_only` must remain `true`.
- `live_trading_enabled` must remain `false`.
- Startup and tests fail closed if either condition changes.
- There is no MCP client, brokerage authentication, account reader, or order function.
- Do not interpret a positive paper result as proof that the strategy will work with real money. Taxes, spreads, market impact, outages, and regime changes can materially alter results.

Robinhood's Agentic account is a separate live-trading product. This project deliberately does not connect to it. Review Robinhood's current disclosures before considering any future connection: https://robinhood.com/us/en/support/articles/agentic-trading-overview/
