from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, default):
    path = ROOT / "state" / name
    return json.loads(path.read_text()) if path.exists() else default


def money(value) -> str:
    return f"${float(value):,.2f}"


def render() -> None:
    portfolio = _load("portfolio.json", {"cash": 10000, "positions": {}, "trades": [], "equity_history": []})
    evaluation = _load("evaluation.json", {"elapsed_days": 0, "duration_days": 30, "runs_observed": 0, "complete": False})
    decisions = _load("decisions.json", [])
    status = _load("status.json", {})
    latest = decisions[-1]["items"] if decisions else []
    equity = portfolio["equity_history"][-1]["equity"] if portfolio["equity_history"] else portfolio["cash"]
    start = 10000.0
    ret = equity / start - 1
    positions = "".join(
        f"<tr><td>{html.escape(symbol)}</td><td>{pos['shares']}</td><td>{money(pos['paper_entry_price'])}</td><td>{html.escape(pos['opened'])}</td></tr>"
        for symbol, pos in portfolio["positions"].items()
    ) or '<tr><td colspan="4">No open paper positions</td></tr>'
    explanations = "".join(
        f"<article><span class='pill'>{html.escape(item['action'])}</span><h3>{html.escape(item['symbol'])}</h3><p>{html.escape(item['explanation'])}</p></article>"
        for item in latest
    ) or "<p>No completed market-day evaluation yet.</p>"
    progress = min(100, 100 * float(evaluation.get("elapsed_days", 0)) / evaluation.get("duration_days", 30))
    output = f"""<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>
<title>ETF Paper Research</title><style>
:root{{--bg:#07111f;--card:#101e31;--ink:#edf4ff;--muted:#99abc3;--green:#42d392;--line:#263a54}}*{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#07111f,#0b1728);color:var(--ink);font:15px system-ui,-apple-system,sans-serif}}main{{max-width:1100px;margin:auto;padding:32px 20px}}h1{{font-size:clamp(28px,5vw,48px);margin:8px 0}}h2{{margin-top:34px}}.eyebrow,.muted{{color:var(--muted)}}.safety{{border:1px solid #2a8d69;background:#0d2b26;padding:12px 16px;border-radius:12px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:22px 0}}.card,article{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px}}.metric{{font-size:28px;font-weight:750;margin-top:5px}}.bar{{height:10px;background:#203047;border-radius:8px;overflow:hidden}}.bar i{{display:block;height:100%;width:{progress:.1f}%;background:var(--green)}}table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:14px;overflow:hidden}}th,td{{padding:12px;text-align:left;border-bottom:1px solid var(--line)}}.pill{{font-size:11px;font-weight:800;color:var(--green);letter-spacing:.05em}}article h3{{margin:8px 0}}article p{{color:#c2cee0;line-height:1.5}}footer{{color:var(--muted);margin-top:35px;font-size:13px}}
</style></head><body><main><div class='eyebrow'>READ-ONLY • PAPER-ONLY • END-OF-DAY</div><h1>ETF Research Agent</h1><p class='safety'>No Robinhood connection. No credentials. No live orders. Every transaction shown is hypothetical.</p>
<section class='grid'><div class='card'><div class='muted'>Paper equity</div><div class='metric'>{money(equity)}</div></div><div class='card'><div class='muted'>Paper return</div><div class='metric'>{ret:+.2%}</div></div><div class='card'><div class='muted'>Cash</div><div class='metric'>{money(portfolio['cash'])}</div></div><div class='card'><div class='muted'>Runs observed</div><div class='metric'>{evaluation.get('runs_observed',0)}</div></div><div class='card'><div class='muted'>Techniques evaluated</div><div class='metric'>100</div></div><div class='card'><div class='muted'>Independent families</div><div class='metric'>10</div></div></section>
<h2>30-day evaluation</h2><p>{evaluation.get('elapsed_days',0):.1f} of {evaluation.get('duration_days',30)} calendar days • {'COMPLETE' if evaluation.get('complete') else 'RUNNING'}</p><div class='bar'><i></i></div>
<h2>Open paper positions</h2><table><thead><tr><th>ETF</th><th>Shares</th><th>Paper entry</th><th>Opened</th></tr></thead><tbody>{positions}</tbody></table>
<h2>Latest explanations</h2>{explanations}
<footer>Last workflow heartbeat: {html.escape(str(status.get('run_at','not run')))} • Last market date: {html.escape(str(portfolio.get('last_market_date','none')))} • Generated {datetime.now(timezone.utc).isoformat()}</footer></main></body></html>"""
    path = ROOT / "docs" / "index.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(output)


if __name__ == "__main__":
    render()
