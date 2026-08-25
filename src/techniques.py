from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Technique:
    id: str
    family: str
    description: str
    kind: str
    parameters: tuple[float, ...]


def registry() -> list[Technique]:
    items: list[Technique] = []

    def add(family: str, kind: str, description: str, variants):
        for index, params in enumerate(variants, 1):
            params = params if isinstance(params, tuple) else (params,)
            items.append(Technique(f"{family}-{index:02}", family, description.format(*params), kind, tuple(params)))

    add("absolute_momentum", "momentum", "{}-day total return is positive",
        [20, 40, 60, 80, 100, 120, 160, 200, 240, 252])
    add("price_sma", "price_sma", "Close is above its {}-day SMA",
        [20, 30, 40, 50, 75, 100, 125, 150, 175, 200])
    add("dual_sma", "dual_sma", "{}-day SMA is above {}-day SMA",
        [(5, 50), (10, 50), (20, 50), (10, 100), (20, 100), (50, 100), (20, 150), (50, 150), (50, 200), (100, 200)])
    add("dual_ema", "dual_ema", "{}-day EMA is above {}-day EMA",
        [(5, 30), (10, 30), (10, 50), (20, 50), (20, 75), (30, 100), (50, 100), (50, 150), (50, 200), (100, 200)])
    add("range_breakout", "breakout", "Close is at or above the prior {}-day high",
        [20, 30, 40, 50, 60, 90, 120, 150, 200, 252])
    add("high_proximity", "high_proximity", "Close is at least {:.0%} of the 252-day high",
        [.80, .82, .84, .86, .88, .90, .92, .94, .96, .98])
    add("risk_adjusted_momentum", "risk_adjusted", "{}-day momentum / {}-day annualized volatility exceeds {:.1f}",
        [(60, 20, .5), (60, 40, .5), (90, 20, .5), (90, 60, .5), (120, 20, .5),
         (120, 60, .5), (180, 40, .5), (180, 90, .5), (252, 60, .5), (252, 120, .5)])
    add("drawdown_control", "drawdown", "Close is no more than {:.0%} below its {}-day high",
        [(.05, 60), (.075, 60), (.10, 90), (.10, 120), (.125, 120),
         (.15, 150), (.15, 200), (.175, 200), (.20, 252), (.25, 252)])
    add("volatility_regime", "vol_regime", "{}-day volatility is below {:.2f}× {}-day volatility",
        [(10, .80, 60), (10, 1.00, 60), (20, .80, 60), (20, 1.00, 60), (20, 1.20, 60),
         (20, .80, 120), (20, 1.00, 120), (40, .80, 120), (40, 1.00, 120), (60, 1.00, 252)])
    add("conditioned_reversal", "conditioned_reversal", "In a 200-day uptrend, {}-day return is between {:.1%} and 0%",
        [(2, -.02), (3, -.025), (4, -.03), (5, -.03), (5, -.05),
         (7, -.05), (10, -.05), (10, -.075), (15, -.075), (20, -.10)])
    assert len(items) == 100
    assert len({item.id for item in items}) == 100
    return items


REGISTRY = registry()


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _ema(values: list[float], period: int) -> float:
    alpha = 2.0 / (period + 1)
    value = values[-period]
    for observation in values[-period + 1 :]:
        value = alpha * observation + (1 - alpha) * value
    return value


def _volatility(values: list[float], period: int) -> float:
    returns = [b / a - 1 for a, b in zip(values[-period - 1 : -1], values[-period:])]
    mean = _mean(returns)
    variance = sum((value - mean) ** 2 for value in returns) / max(1, len(returns) - 1)
    return math.sqrt(variance) * math.sqrt(252)


def signal(technique: Technique, closes: list[float]) -> bool:
    kind, p = technique.kind, technique.parameters
    if kind == "momentum":
        lookback = int(p[0]); return closes[-1] / closes[-lookback - 1] - 1 > 0
    if kind == "price_sma":
        lookback = int(p[0]); return closes[-1] > _mean(closes[-lookback:])
    if kind == "dual_sma":
        short, long = map(int, p); return _mean(closes[-short:]) > _mean(closes[-long:])
    if kind == "dual_ema":
        short, long = map(int, p); return _ema(closes, short) > _ema(closes, long)
    if kind == "breakout":
        lookback = int(p[0]); return closes[-1] >= max(closes[-lookback - 1 : -1])
    if kind == "high_proximity":
        return closes[-1] >= p[0] * max(closes[-252:])
    if kind == "risk_adjusted":
        lookback, vol_period, threshold = int(p[0]), int(p[1]), p[2]
        momentum = closes[-1] / closes[-lookback - 1] - 1
        vol = _volatility(closes, vol_period)
        return vol > 0 and momentum / vol > threshold
    if kind == "drawdown":
        limit, lookback = p[0], int(p[1]); return closes[-1] / max(closes[-lookback:]) - 1 >= -limit
    if kind == "vol_regime":
        short, ratio, long = int(p[0]), p[1], int(p[2])
        return _volatility(closes, short) < ratio * _volatility(closes, long)
    if kind == "conditioned_reversal":
        lookback, floor = int(p[0]), p[1]
        recent = closes[-1] / closes[-lookback - 1] - 1
        return closes[-1] > _mean(closes[-200:]) and floor <= recent < 0
    raise ValueError(f"unknown technique kind: {kind}")


def consensus(closes: list[float], family_threshold: float = .60) -> dict:
    if len(closes) < 253:
        raise ValueError("at least 253 closes are required for the 100-technique registry")
    results = {item.id: signal(item, closes) for item in REGISTRY}
    families = sorted({item.family for item in REGISTRY})
    family_scores = {
        family: sum(results[item.id] for item in REGISTRY if item.family == family) / 10
        for family in families
    }
    return {
        "techniques_total": 100,
        "techniques_bullish": sum(results.values()),
        "family_scores": family_scores,
        "bullish_families": sum(score >= family_threshold for score in family_scores.values()),
        "results": results,
    }
