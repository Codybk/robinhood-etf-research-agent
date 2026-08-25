from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

from .audit import AuditLog
from .indicators import Snapshot


def load_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def explain(snapshot: Snapshot, action: str, reason: str) -> str:
    trend = "above" if snapshot.close > snapshot.sma200 else "below"
    cross = "above" if snapshot.sma50 > snapshot.sma200 else "below"
    return (
        f"{action}: {reason} Close ${snapshot.close:.2f} is {trend} the 200-day average "
        f"(${snapshot.sma200:.2f}); the 50-day average (${snapshot.sma50:.2f}) is {cross} it; "
        f"20-day momentum is {snapshot.momentum20:+.1%}; RSI(14) is {snapshot.rsi14:.1f}. "
        f"Across 100 techniques, {snapshot.techniques_bullish} are bullish and "
        f"{snapshot.bullish_families}/10 independent families pass. Family scores: "
        + ", ".join(f"{name} {score:.0%}" for name, score in sorted(snapshot.family_scores.items())) + "."
    )


def evaluate(settings: dict, snapshots: dict[str, Snapshot], state_dir: Path, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    if not settings.get("paper_only") or settings.get("live_trading_enabled"):
        raise RuntimeError("REFUSING TO RUN: paper-only safety settings are not intact")
    dates = {snapshot.date for snapshot in snapshots.values()}
    if len(dates) != 1:
        raise RuntimeError(f"market data is not aligned to one date: {sorted(dates)}")
    market_date = dates.pop()
    portfolio_path = state_dir / "portfolio.json"
    decisions_path = state_dir / "decisions.json"
    evaluation_path = state_dir / "evaluation.json"
    portfolio = load_json(portfolio_path, {
        "cash": float(settings["starting_cash"]), "positions": {}, "trades": [],
        "equity_history": [], "last_market_date": None,
    })
    evaluation = load_json(evaluation_path, {
        "started_at": now.isoformat(), "duration_days": settings["evaluation_days"],
        "runs_observed": 0, "market_days_observed": 0, "complete": False,
    })
    evaluation["runs_observed"] += 1
    elapsed = (now - datetime.fromisoformat(evaluation["started_at"])).total_seconds() / 86400
    evaluation["elapsed_days"] = round(elapsed, 3)
    evaluation["complete"] = elapsed >= evaluation["duration_days"]
    if portfolio.get("last_market_date") == market_date:
        save_json(evaluation_path, evaluation)
        return {"market_date": market_date, "duplicate_market_day": True, "decisions": []}

    audit = AuditLog(state_dir / "audit.jsonl")
    decisions = []
    slippage = settings["hypothetical_slippage_pct"]

    # Exits are processed before new entries.
    for symbol in list(portfolio["positions"]):
        snapshot = snapshots[symbol]
        position = portfolio["positions"][symbol]
        exit_reasons = []
        if snapshot.close < snapshot.sma200:
            exit_reasons.append("close fell below the 200-day trend regime")
        if snapshot.bullish_families <= settings["exit_bullish_families"]:
            exit_reasons.append(f"independent confirmation fell to {snapshot.bullish_families}/10 families")
        if snapshot.momentum20 <= settings["exit_momentum_threshold"]:
            exit_reasons.append(f"20-day momentum reached {snapshot.momentum20:+.1%}")
        if exit_reasons:
            execution = snapshot.close * (1 - slippage)
            proceeds = position["shares"] * execution
            pnl = proceeds - position["cost"]
            portfolio["cash"] += proceeds
            trade = {"date": market_date, "symbol": symbol, "side": "PAPER_SELL", "shares": position["shares"],
                     "market_price": snapshot.close, "paper_price": execution, "paper_pnl": pnl,
                     "reason": "; ".join(exit_reasons)}
            portfolio["trades"].append(trade)
            del portfolio["positions"][symbol]
            decisions.append({"symbol": symbol, "action": "PAPER_EXIT", "explanation": explain(snapshot, "PAPER EXIT", trade["reason"])})
            audit.append("PAPER_EXIT", trade)

    equity_before_entries = portfolio["cash"] + sum(
        position["shares"] * snapshots[symbol].close for symbol, position in portfolio["positions"].items()
    )
    slots = settings["max_positions"] - len(portfolio["positions"])
    candidates = sorted(
        (snapshot for symbol, snapshot in snapshots.items()
         if symbol not in portfolio["positions"]
         and snapshot.bullish_families >= settings["entry_bullish_families"]
         and snapshot.close > snapshot.sma200),
        key=lambda item: (item.bullish_families, item.momentum20),
        reverse=True,
    )
    for snapshot in candidates[:slots]:
        reserve = equity_before_entries * settings["minimum_cash_pct"]
        budget = min(equity_before_entries * settings["target_position_pct"], max(0.0, portfolio["cash"] - reserve))
        execution = snapshot.close * (1 + slippage)
        shares = math.floor(budget / execution)
        if shares < 1:
            continue
        cost = shares * execution
        portfolio["cash"] -= cost
        portfolio["positions"][snapshot.symbol] = {
            "shares": shares, "paper_entry_price": execution, "cost": cost, "opened": market_date
        }
        trade = {"date": market_date, "symbol": snapshot.symbol, "side": "PAPER_BUY", "shares": shares,
                 "market_price": snapshot.close, "paper_price": execution,
                 "reason": f"{snapshot.bullish_families}/10 independent technique families passed; ranked by family agreement then momentum"}
        portfolio["trades"].append(trade)
        decisions.append({"symbol": snapshot.symbol, "action": "PAPER_ENTRY", "explanation": explain(snapshot, "PAPER ENTRY", trade["reason"])})
        audit.append("PAPER_ENTRY", trade)

    acted = {item["symbol"] for item in decisions}
    for symbol, snapshot in snapshots.items():
        if symbol in acted:
            continue
        if symbol in portfolio["positions"]:
            reason = "position remains open because neither exit rule fired"
        else:
            reason = (f"no entry because {snapshot.bullish_families}/10 bullish families did not satisfy the "
                      f"{settings['entry_bullish_families']}/10 requirement or the 200-day trend filter")
        decisions.append({"symbol": symbol, "action": "HOLD_OR_WATCH", "explanation": explain(snapshot, "HOLD/WATCH", reason)})

    equity = portfolio["cash"] + sum(
        position["shares"] * snapshots[symbol].close for symbol, position in portfolio["positions"].items()
    )
    portfolio["last_market_date"] = market_date
    portfolio["equity_history"].append({"date": market_date, "equity": equity, "cash": portfolio["cash"]})
    evaluation["market_days_observed"] += 1
    all_decisions = load_json(decisions_path, [])
    all_decisions.append({"run_at": now.isoformat(), "market_date": market_date, "items": decisions})
    save_json(portfolio_path, portfolio)
    save_json(decisions_path, all_decisions[-100:])
    save_json(evaluation_path, evaluation)
    audit.append("SCAN_COMPLETE", {"market_date": market_date, "equity": equity, "decisions": len(decisions)})
    return {"market_date": market_date, "duplicate_market_day": False, "decisions": decisions, "equity": equity}
