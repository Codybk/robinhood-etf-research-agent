from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from src.audit import AuditLog
from src.data import Bar
from src.engine import evaluate
from src.indicators import Snapshot, calculate


def settings():
    return {
        "paper_only": True, "live_trading_enabled": False, "starting_cash": 10000,
        "evaluation_days": 30, "max_positions": 3, "target_position_pct": .25,
        "minimum_cash_pct": .10, "hypothetical_slippage_pct": .0005,
        "entry_bullish_families": 6, "exit_bullish_families": 3,
        "exit_momentum_threshold": -.05,
    }


def snap(symbol, score=7, momentum=.05, close=100, sma50=95, sma200=90, rsi=55):
    families = {f"family_{index}": (1.0 if index < score else 0.0) for index in range(10)}
    return Snapshot(symbol, "2026-08-24", close, sma50, sma200, momentum, rsi, score,
                    score * 10, 100, score, families)


def test_indicator_calculation_has_expected_shape():
    bars = [Bar(f"d{i:03}", 100 + i * .2) for i in range(260)]
    result = calculate("SPY", bars)
    assert result.close == pytest.approx(151.8)
    assert result.sma50 > result.sma200
    assert result.momentum20 > 0


def test_entries_are_paper_only_ranked_and_capped(tmp_path):
    snapshots = {symbol: snap(symbol, momentum=momentum) for symbol, momentum in
                 {"SPY": .03, "QQQ": .08, "IWM": .02, "TLT": .05, "GLD": .01}.items()}
    result = evaluate(settings(), snapshots, tmp_path, datetime(2026, 8, 25, tzinfo=timezone.utc))
    portfolio = json.loads((tmp_path / "portfolio.json").read_text())
    assert set(portfolio["positions"]) == {"QQQ", "TLT", "SPY"}
    assert all(trade["side"] == "PAPER_BUY" for trade in portfolio["trades"])
    assert portfolio["cash"] >= 1000
    assert len(result["decisions"]) == 5


def test_exit_explanation_and_pnl(tmp_path):
    first = {"SPY": snap("SPY"), "QQQ": snap("QQQ", score=0), "IWM": snap("IWM", score=0),
             "TLT": snap("TLT", score=0), "GLD": snap("GLD", score=0)}
    evaluate(settings(), first, tmp_path, datetime(2026, 8, 25, tzinfo=timezone.utc))
    second = {key: snap(key, score=0) for key in first}
    second["SPY"] = snap("SPY", score=0, momentum=-.03, close=90, sma50=95)
    for key, value in list(second.items()):
        second[key] = Snapshot(value.symbol, "2026-08-25", value.close, value.sma50, value.sma200,
                               value.momentum20, value.rsi14, value.entry_score, value.techniques_bullish,
                               value.techniques_total, value.bullish_families, value.family_scores)
    result = evaluate(settings(), second, tmp_path, datetime(2026, 8, 26, tzinfo=timezone.utc))
    assert result["decisions"][0]["action"] == "PAPER_EXIT"
    assert "momentum" in result["decisions"][0]["explanation"]


def test_duplicate_market_day_never_duplicates_trades(tmp_path):
    snapshots = {"SPY": snap("SPY")}
    now = datetime(2026, 8, 25, tzinfo=timezone.utc)
    evaluate(settings(), snapshots, tmp_path, now)
    result = evaluate(settings(), snapshots, tmp_path, now + timedelta(hours=1))
    portfolio = json.loads((tmp_path / "portfolio.json").read_text())
    assert result["duplicate_market_day"] is True
    assert len(portfolio["trades"]) == 1


def test_evaluation_start_is_stable_and_completes_after_30_days(tmp_path):
    snapshots = {"SPY": snap("SPY", score=0)}
    start = datetime(2026, 8, 1, tzinfo=timezone.utc)
    evaluate(settings(), snapshots, tmp_path, start)
    later_base = snap("SPY", score=0)
    later = {"SPY": Snapshot("SPY", "2026-09-03", 100, 95, 90, 0, 55, 0,
                             later_base.techniques_bullish, later_base.techniques_total,
                             later_base.bullish_families, later_base.family_scores)}
    evaluate(settings(), later, tmp_path, start + timedelta(days=33))
    record = json.loads((tmp_path / "evaluation.json").read_text())
    assert record["started_at"] == start.isoformat()
    assert record["complete"] is True
    assert record["runs_observed"] == 2


def test_safety_fails_closed(tmp_path):
    unsafe = settings() | {"live_trading_enabled": True}
    with pytest.raises(RuntimeError, match="REFUSING"):
        evaluate(unsafe, {"SPY": snap("SPY")}, tmp_path)


def test_audit_chain_detects_tampering(tmp_path):
    log = AuditLog(tmp_path / "audit.jsonl")
    log.append("ONE", {"value": 1})
    log.append("TWO", {"value": 2})
    assert log.verify()["ok"] is True
    text = (tmp_path / "audit.jsonl").read_text().replace('"value": 1', '"value": 9')
    (tmp_path / "audit.jsonl").write_text(text)
    assert log.verify()["ok"] is False
