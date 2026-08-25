from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .audit import AuditLog
from .dashboard import render
from .data import get_history
from .engine import evaluate, save_json
from .indicators import calculate


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = json.loads((ROOT / "config" / "settings.json").read_text())
    if settings.get("mode") != "PAPER_RESEARCH_ONLY" or not settings.get("paper_only") or settings.get("live_trading_enabled"):
        raise SystemExit("REFUSING TO RUN: paper-only configuration is not intact")
    snapshots, providers = {}, {}
    for symbol in settings["universe"]:
        bars, provider = get_history(symbol)
        snapshots[symbol] = calculate(symbol, bars)
        providers[symbol] = provider
    now = datetime.now(timezone.utc)
    result = evaluate(settings, snapshots, ROOT / "state", now)
    audit = AuditLog(ROOT / "state" / "audit.jsonl")
    verification = audit.verify()
    if not verification["ok"]:
        raise SystemExit("AUDIT CHAIN BROKEN")
    save_json(ROOT / "state" / "status.json", {
        "run_at": now.isoformat(), "paper_only": True, "live_trading_enabled": False,
        "providers": providers, "market_date": result["market_date"],
        "duplicate_market_day": result["duplicate_market_day"], "audit": verification,
    })
    render()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
