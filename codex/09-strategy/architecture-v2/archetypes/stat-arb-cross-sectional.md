---
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

# Archetype: `STAT_ARB_CROSS_SECTIONAL`

> **Family:** [Stat Arb / Pairs](../families/stat-arb-pairs.md) **Settlement model:** Periodic rebalance — basket
> members rotate as rankings shift. **Code module (target):**
> `strategy-service/engine/strategies/stat_arb_cross_sectional_engine.py`

## What it does

Cross-sectional ranking across a universe of underlyings: score all N members on a signal (ML prediction, factor
exposure, or composite), long top-M / short bottom-M. Members rotate each rebalance period as rankings change. Joint
reasoning over the whole universe (this is what distinguishes it from running N independent ML directional strategies).

## Token / position flow

```
1. UNIVERSE READ: fetch current prices + features for all N members
   (e.g., Russell 1000, S&P 500, crypto top-50)

2. RANKING: cross-sectional ML model (or factor model) scores each member
   Returns score_i for all i in universe

3. BASKET SELECTION:
   - Long basket: top-M by score
   - Short basket: bottom-M by score
   - Equal-weight (default) OR rank-weighted OR confidence-weighted

4. REBALANCE (per cadence — e.g., daily):
   - Compute current_basket vs target_basket
   - Exits: close positions in members leaving both baskets
   - Entries: open positions in new basket members
   - Weight changes: resize existing positions to new weights

5. EMIT: ATOMIC multi-leg ideally; otherwise sequential TRADE instructions
   with pre-flight check for venue-account health across the whole trade set

6. HOLD: monitor gross exposure, factor exposures, single-name concentration
```

## Supported universes

| Universe                                 | Venues                       | Rebalance cadence |
| ---------------------------------------- | ---------------------------- | ----------------- |
| Russell 1000                             | IBKR                         | Daily             |
| S&P 500                                  | IBKR                         | Daily             |
| Nasdaq 100                               | IBKR                         | Daily             |
| Crypto top-50 by market cap              | Binance, OKX, Bybit          | Hourly or daily   |
| Crypto top-20 perps                      | Hyperliquid, Binance Futures | Hourly            |
| Sector constituents (XLE, XLF, XLK etc.) | IBKR                         | Daily             |

## Config schema

```yaml
universe_ref: RUSSELL_1000 # versioned universe artifact
ranking_model_ref: EQUITY_CS_CATBOOST_V3 # cross-sectional ML model
feature_group_refs:
  - equity-fundamentals@v4
  - equity-momentum@v3
  - equity-vol-adjusted@v2
basket_size_long_pct: 0.10 # long top 10% (100 names on R1000)
basket_size_short_pct: 0.10 # short bottom 10%
weighting_scheme: RANK_WEIGHTED # or EQUAL_WEIGHT or CONFIDENCE_WEIGHTED
rebalance_cadence: DAILY
rebalance_threshold_pct: 0.20 # only rebalance if ≥20% of basket changed
notional_per_side_pct_equity: 0.50 # 50% gross long + 50% gross short = 100% gross; net ~0
max_single_name_pct: 0.02 # no more than 2% equity in one name
share_class: USD
venues: [IBKR]
execution_policy_ref: tradfi-basket-execution-v2
```

## Execution semantics

- Rebalance emits **multi-instrument TRADE set** — potentially dozens or hundreds of target-state changes per rebalance
- Execution-service sequences per its policy (e.g., TWAP over N minutes, balanced entry/exit pacing)
- Pre-flight check against venue-account health for the combined trade set
- ATOMIC not feasible for hundreds of names; sequential execution with pacing

## P&L attribution

- **Cross-sectional spread P&L**: (top-basket return) - (bottom-basket return) net of commission
- **Factor attribution**: decompose returns into factor exposures (value, momentum, size, quality, vol)
- **Turnover cost**: rebalance-driven commission and slippage
- **Execution alpha**: vs benchmark fills

## Risk profile

- Drawdowns: factor reversals (value/momentum regime change) cause sharp reversals
- Typical Sharpe: 0.8-2.0 for well-run cross-sectional
- Kill switches: factor-exposure limit breach, single-name concentration breach, model calibration failure

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.notional_per_side = new_equity * self.config.notional_per_side_pct_equity
    # Scale all basket members proportionally
    return self._rescale_basket_proportionally()
```

## Example instances

```
STAT_ARB_CROSS_SECTIONAL@ibkr-russell1000-daily-usd-prod
STAT_ARB_CROSS_SECTIONAL@ibkr-sp500-daily-usd-prod
STAT_ARB_CROSS_SECTIONAL@multi-cex-top50-crypto-1h-usdt-prod
STAT_ARB_CROSS_SECTIONAL@multi-cex-top50-crypto-daily-usdt-prod
STAT_ARB_CROSS_SECTIONAL@ibkr-xle-constituents-daily-usd-prod   (sector internal)
```

## Not in this archetype

- **Fixed pair or small fixed basket** (GOOG-META, ES-NQ) — goes to `STAT_ARB_PAIRS_FIXED`
- **Portfolio of N independent ML strategies weighted by allocator** — that's not one strategy; it's N
  `ML_DIRECTIONAL_CONTINUOUS` instances + a Portfolio Allocator with SHARPE_WEIGHTED or CONFIDENCE_WEIGHTED archetype
- **Single-name directional bets** — goes to `ML_DIRECTIONAL_CONTINUOUS`
- **Sector rotation as a directional view** (long XLE, short SPY for a single-pair view) — fixed pair, goes to
  `STAT_ARB_PAIRS_FIXED`
- **Factor investing without cross-sectional spread** (just long value tilt) — goes to `RULES_DIRECTIONAL_CONTINUOUS`
  with factor rules

## Migration from legacy

No legacy doc. v2 introduces this archetype formally.

## See also

- Family: [stat-arb-pairs.md](../families/stat-arb-pairs.md)
- Fixed-pair variant: [stat-arb-pairs-fixed.md](stat-arb-pairs-fixed.md)
- Portfolio Allocator comparison (N independent ML strategies):
  [../cross-cutting/portfolio-allocator.md](../cross-cutting/portfolio-allocator.md)
