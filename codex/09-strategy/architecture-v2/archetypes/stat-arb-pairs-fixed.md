---
scope: [engineer, admin]
topology_requirements:
  isolation:
    execution-service: isolated
  co_location: []
  latency_budget_ms: 150
  min_sla_tier: standard
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Archetype: `STAT_ARB_PAIRS_FIXED`

> **Family:** [Stat Arb / Pairs](../families/stat-arb-pairs.md) **Settlement model:** Hold-until-flip — paired position
> held until spread reverts. **Code module (target):**
> `strategy-service/engine/strategies/stat_arb_pairs_fixed_engine.py`

## What it does

Trades a pre-determined, cointegration-tested (or historical-beta-stable) pair of underlyings. When the spread deviates
from its historical mean by a z-score threshold, enter long underperformer + short outperformer. Close when spread
reverts.

## Token / position flow

```
1. SPREAD COMPUTE: spread = price_A - hedge_ratio × price_B
   (hedge_ratio from rolling OLS or Kalman filter)

2. Z-SCORE: (spread - rolling_mean) / rolling_std

3. ENTRY: |z_score| > entry_threshold AND cointegration_pvalue < 0.05
   - Long leg: buy underperforming instrument (dollar-neutral sized)
   - Short leg: sell outperforming instrument
   - ATOMIC if both on same venue (CEX), LEADER_HEDGE if cross-venue

4. HOLD: monitor z-score + cointegration pvalue

5. EXIT:
   - |z_score| < exit_threshold → close both legs (convergence)
   - cointegration pvalue > 0.15 → forced exit (relationship degrading)
   - stop_loss (z-score > max_z) → forced exit
   - max_hold_bars → force close
```

**Venue × instrument coverage:** See
[`../category-instrument-coverage.md § 17. STAT_ARB_PAIRS_FIXED`](../category-instrument-coverage.md#17-stat_arb_pairs_fixed).
The pair-type table below is orthogonal to venue coverage.

## Supported pair types

| Type               | Examples                                              |
| ------------------ | ----------------------------------------------------- |
| Single-stock pairs | GOOG-META, AAPL-MSFT, KO-PEP                          |
| Sector-vs-index    | XLE-SPY, XLF-SPY                                      |
| Index-vs-index     | ES-NQ, ES-RTY, Nasdaq-S&P                             |
| Cross-asset        | CL-ES (crude vs S&P), GC-ES (gold vs S&P)             |
| Crypto majors      | BTC-ETH, BTC-SOL, ETH-SOL                             |
| Crypto-macro       | BTC-QQQ (crypto vs tech), ETH-SPY                     |
| Vol pairs          | BTC_realized_vol vs ETH_realized_vol (as instruments) |

## Config schema

```yaml
pair_instruments:
  long_candidate: "IBKR:EQUITY:GOOG"
  short_candidate: "IBKR:EQUITY:META"
hedge_ratio_model: KALMAN # or OLS_ROLLING, COINTEGRATION_VECTOR
hedge_ratio_window_days: 90
z_score_window_days: 60
entry_z_score: 2.0
exit_z_score: 0.3
stop_loss_z_score: 3.5
cointegration_pvalue_max: 0.10
max_hold_days: 30
half_life_max_days: 15 # skip if OU half-life too slow
notional_allocation_usd: 500_000 # per pair
share_class: USD
venues: [IBKR]
execution_policy_ref: tradfi-paired-execution-v2 # leader-hedge or atomic
```

## Execution semantics

- Both legs entered/exited as ATOMIC (same venue) or LEADER_HEDGE (different venues)
- Hedge ratio updates periodically; re-emit reconciliation if ratio drift > threshold

## P&L attribution

- **Spread P&L**: (entry_z × σ_spread) × notional captured on reversion
- **Leg-by-leg P&L**: attribution to long leg and short leg separately for interpretation
- **Hedge ratio drift cost**: when Kalman updates, small rebalance trades incur cost
- **Execution alpha**: per fill

## Risk profile

- Drawdowns: spread-risk (relationship breaks) — can be severe if cointegration breaks (M&A, index rebalance, regime
  shift)
- Typical Sharpe: 1.0-2.5 for well-run stat arb
- Kill switches: cointegration pvalue breach, one-leg liquidity collapse, extreme z-score without reversion

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.notional_per_pair = new_equity * self.config.allocation_pct_per_pair
    return self._rescale_paired_positions()
```

## Example instances

```
STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod
STAT_ARB_PAIRS_FIXED@ibkr-aapl-msft-daily-usd-prod
STAT_ARB_PAIRS_FIXED@ibkr-xle-spy-daily-usd-prod
STAT_ARB_PAIRS_FIXED@cme-es-nq-daily-usd-prod
STAT_ARB_PAIRS_FIXED@cme-es-rty-daily-usd-prod
STAT_ARB_PAIRS_FIXED@cme-cl-es-daily-usd-prod
STAT_ARB_PAIRS_FIXED@binance-btc-eth-1h-usdt-prod
STAT_ARB_PAIRS_FIXED@binance-btc-sol-1h-usdt-prod
STAT_ARB_PAIRS_FIXED@deribit-btc-eth-vol-1h-usdt-prod      (vol-pair instance)
```

## Not in this archetype

- **Dynamic basket (members rotate daily based on ranking)** — goes to `STAT_ARB_CROSS_SECTIONAL`
- **Same-underlying basis** (spot vs future/perp of same asset) — goes to `CARRY_BASIS_*`
- **Price-dispersion arb** (risk-free mechanical spread) — goes to `ARBITRAGE_PRICE_DISPERSION`
- **Single-asset directional ML without paired hedge** — goes to `ML_DIRECTIONAL_CONTINUOUS`
- **Cross-asset vol view** where the alpha is on vol metrics themselves (not the ratio mean-reverting) — goes to
  `VOL_TRADING_OPTIONS`
- **Multi-leg synthetic** (e.g., straddle + calendar) that's really a combined vol structure — goes to
  `VOL_TRADING_OPTIONS`

## Migration from legacy

| Legacy                      | Notes                                          |
| --------------------------- | ---------------------------------------------- |
| Code: `stat_arb_btc_eth.py` | → `StatArbPairsFixedEngine`                    |
| Code: `rel_vol_btc_eth.py`  | → `StatArbPairsFixedEngine` (vol-pair variant) |

## See also

- Family: [stat-arb-pairs.md](../families/stat-arb-pairs.md)
- Cross-sectional variant: [stat-arb-cross-sectional.md](stat-arb-cross-sectional.md)
- Leader-hedge execution: [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
