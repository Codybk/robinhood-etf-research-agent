from __future__ import annotations

import csv
import io
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

import requests


@dataclass(frozen=True)
class Bar:
    date: str
    close: float


class MarketDataError(RuntimeError):
    pass


def _request_json(url: str, attempts: int = 3) -> dict:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": "etf-paper-research/1.0"})
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # network boundary
            last_error = exc
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise MarketDataError(f"market-data request failed after {attempts} attempts: {last_error}")


def yahoo_daily(symbol: str) -> list[Bar]:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=10y&interval=1d&events=history"
    payload = _request_json(url)
    try:
        result = payload["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["adjclose"][0]["adjclose"]
    except (KeyError, IndexError, TypeError) as exc:
        raise MarketDataError(f"unexpected Yahoo response for {symbol}") from exc
    bars = []
    for timestamp, close in zip(timestamps, closes):
        if close is None:
            continue
        day = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
        bars.append(Bar(day, float(close)))
    return _validate(symbol, bars)


def stooq_daily(symbol: str) -> list[Bar]:
    url = f"https://stooq.com/q/d/l/?s={symbol.lower()}.us&i=d"
    response = requests.get(url, timeout=20, headers={"User-Agent": "etf-paper-research/1.0"})
    response.raise_for_status()
    rows = csv.DictReader(io.StringIO(response.text))
    bars = [Bar(row["Date"], float(row["Close"])) for row in rows if row.get("Close")]
    return _validate(symbol, bars[-2600:])


def _validate(symbol: str, bars: Iterable[Bar]) -> list[Bar]:
    clean = sorted({bar.date: bar for bar in bars}.values(), key=lambda bar: bar.date)
    if len(clean) < 253:
        raise MarketDataError(f"{symbol} returned only {len(clean)} daily bars; at least 253 required")
    if any(bar.close <= 0 for bar in clean):
        raise MarketDataError(f"{symbol} returned a non-positive close")
    return clean


def get_history(symbol: str) -> tuple[list[Bar], str]:
    errors = []
    for name, provider in (("Yahoo Finance chart", yahoo_daily), ("Stooq", stooq_daily)):
        try:
            return provider(symbol), name
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    raise MarketDataError(f"all providers failed for {symbol}: {'; '.join(errors)}")
