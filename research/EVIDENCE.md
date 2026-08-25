# Evidence review and design decisions

## What “100 proven techniques” can honestly mean

There is no authoritative ranking of the “100 most proven” trading techniques. Finance research instead contains a smaller number of recurring effects with many parameterizations, mixed replication quality, and substantial data-snooping risk. Treating 100 moving-average settings as 100 independent confirmations would be statistically misleading.

This project therefore implements **100 fully specified candidate techniques in 10 equal-weight families**. Every family gets one vote regardless of how many of its ten variants are bullish. The live paper rules do not optimize parameters or select the best-looking historical rule.

## Primary evidence used

1. **Time-series momentum and trend persistence.** Moskowitz, Ooi, and Pedersen document time-series momentum across 58 liquid equity-index, currency, commodity, and bond futures. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2089463
2. **Long-run trend evidence.** Hurst, Ooi, and Pedersen extend a time-series trend strategy back to 1880 and report persistence across long samples and asset classes. https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing
3. **Moving averages and trading-range breakouts.** Brock, Lakonishok, and LeBaron test moving-average and breakout rules on the Dow from 1897–1986 using bootstrap null models. https://doi.org/10.1111/j.1540-6261.1992.tb04681.x
4. **Cross-sectional momentum.** Jegadeesh and Titman’s momentum evidence and later evaluation establish intermediate-horizon continuation, while also showing that the effect is not a riskless law. https://www.nber.org/papers/w7159
5. **Short-horizon reversal.** The literature beginning with Lehmann and Lo–MacKinlay connects short-run reversals to liquidity provision and microstructure. A modern review is https://www.nber.org/papers/w30917
6. **Volatility-managed exposure.** Moreira and Muir report improved risk-adjusted results when exposure is reduced during high-volatility periods. https://www.nber.org/papers/w22208
7. **Volatility and expected returns.** Ang, Hodrick, Xing, and Zhang document the low-volatility/expected-return puzzle in the cross-section. https://www.nber.org/papers/w10852
8. **Momentum crash risk.** Daniel and Moskowitz document rare, severe momentum losses, especially around sharp rebounds after bear markets. https://www.nber.org/papers/w20439
9. **Multiple-testing danger.** Harvey, Liu, and Zhu show why hundreds of tested factors require much higher statistical hurdles and argue that many reported discoveries are false. https://doi.org/10.1093/rfs/hhv059
10. **Backtest-overfitting danger.** Bailey, Borwein, López de Prado, and Zhu formalize the probability of selecting an overfit backtest when many configurations are tried. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253

## The 100 techniques

Each row below represents ten fixed variants. The exact parameters are defined in `src/techniques.py` and tested for count, uniqueness, and family balance.

| Family | Techniques | Variants | Role |
|---|---:|---|---|
| Absolute momentum | 10 | Return lookbacks from 20 to 252 trading days | Continuation |
| Price vs. SMA | 10 | SMA lengths from 20 to 200 days | Trend regime |
| Dual SMA | 10 | Short/long moving-average pairs | Trend confirmation |
| Dual EMA | 10 | Faster exponential-average pairs | Faster trend confirmation |
| Range breakout | 10 | Prior-high lookbacks from 20 to 252 days | Resistance breakout |
| High proximity | 10 | Distance thresholds from 80% to 98% of 252-day high | Persistent strength |
| Risk-adjusted momentum | 10 | Momentum divided by realized volatility | Trend quality |
| Drawdown control | 10 | Peak-distance limits from 5% to 25% | Avoid damaged trends |
| Volatility regime | 10 | Short/long volatility ratios | Exposure restraint |
| Trend-conditioned reversal | 10 | Short dips of varying horizon/depth inside a 200-day uptrend | Controlled mean reversion |

## Ruleset

- A technique is bullish or not bullish from data available at the close.
- A family score is the bullish percentage of its ten variants.
- A family is bullish at a score of 60% or higher.
- Entry requires at least 6 of 10 bullish families **and** price above the 200-day SMA.
- Exit occurs at 3 or fewer bullish families, price below the 200-day SMA, or 20-day momentum at -5% or worse.
- Candidates rank first by independent family agreement, then by 20-day momentum.
- The portfolio remains long-only, unlevered, holds at most three ETFs, keeps at least 10% cash, and uses hypothetical slippage.

This is research design, not proof of future profit. The 30-day forward paper run is intentionally locked before results are known.
