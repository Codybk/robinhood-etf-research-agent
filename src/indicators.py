from __future__ import annotations

from dataclasses import dataclass

from .data import Bar
from .techniques import consensus


@dataclass(frozen=True)
class Snapshot:
    symbol: str
    date: str
    close: float
    sma50: float
    sma200: float
    momentum20: float
    rsi14: float
    entry_score: int
    techniques_bullish: int
    techniques_total: int
    bullish_families: int
    family_scores: dict[str, float]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _rsi(closes: list[float], periods: int = 14) -> float:
    changes = [b - a for a, b in zip(closes[-periods - 1 : -1], closes[-periods:])]
    gains = _mean([max(change, 0.0) for change in changes])
    losses = _mean([max(-change, 0.0) for change in changes])
    if losses == 0:
        return 100.0 if gains else 50.0
    rs = gains / losses
    return 100.0 - (100.0 / (1.0 + rs))


def calculate(symbol: str, bars: list[Bar]) -> Snapshot:
    if len(bars) < 253:
        raise ValueError("at least 253 bars are required")
    closes = [bar.close for bar in bars]
    close = closes[-1]
    sma50 = _mean(closes[-50:])
    sma200 = _mean(closes[-200:])
    momentum20 = close / closes[-21] - 1.0
    rsi14 = _rsi(closes)
    vote = consensus(closes)
    return Snapshot(symbol, bars[-1].date, close, sma50, sma200, momentum20, rsi14,
                    vote["bullish_families"], vote["techniques_bullish"], vote["techniques_total"],
                    vote["bullish_families"], vote["family_scores"])
