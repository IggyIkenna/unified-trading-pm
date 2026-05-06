---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Lending/Borrowing Rate Impact Model

## Overview

When we lend or borrow from Aave V3 pools, our trade changes the pool's utilization ratio, which changes the interest
rates for ALL participants. This model simulates that impact BEFORE execution, allowing strategies to size positions
optimally.

## Aave V3 Interest Rate Model

The Aave V3 variable interest rate follows a two-slope kinked model:

```
U = total_borrows / total_supply   (utilization ratio)

if U <= U_optimal:
    borrow_rate = base_rate + (U / U_optimal) * slope1
else:
    borrow_rate = base_rate + slope1 + ((U - U_optimal) / (1 - U_optimal)) * slope2

supply_rate = borrow_rate * U * (1 - reserve_factor)
```

### Typical Parameters (Aave V3 Ethereum)

| Asset | U_optimal | Slope1 | Slope2 | Base Rate | Reserve Factor |
| ----- | --------- | ------ | ------ | --------- | -------------- |
| USDC  | 90%       | 4%     | 60%    | 0%        | 10%            |
| USDT  | 90%       | 4%     | 60%    | 0%        | 10%            |
| ETH   | 80%       | 3.8%   | 80%    | 0%        | 15%            |
| DAI   | 90%       | 4%     | 75%    | 0%        | 10%            |

### Rate Impact by Position Size

| Our Position | Pool Size | Utilization Change | Supply APY Change |
| ------------ | --------- | ------------------ | ----------------- |
| $500K        | $2B       | -0.025%            | < 1 bps           |
| $5M          | $2B       | -0.25%             | ~1-2 bps          |
| $50M         | $2B       | -2.5%              | ~10-20 bps        |
| $500M        | $2B       | -25%               | ~100+ bps         |

## Implementation

### Schema (UAC)

- `AavePoolParams` -- rate model parameters + pool liquidity
- `RateImpactResult` -- pre/post rates, utilization change, bps delta
- Functions: `compute_borrow_rate()`, `compute_supply_rate()`, `simulate_rate_impact()`
- Location: `unified_api_contracts/internal/domain/defi/rate_model.py`

### Feature Calculator (features-onchain-service)

- `AaveRateImpactCalculator` -- computes projected rates per pool
- Features: `projected_supply_apy`, `projected_borrow_apy`, `rate_impact_supply_bps`, `rate_impact_borrow_bps`
- Data source: DefiLlama Yields API (same as existing calculators)
- Location: `features_onchain_service/app/calculators/aave_rate_impact_calculator.py`

### Strategy Usage (strategy-service)

- Lending strategy reads `projected_supply_apy` from features
- If projected APY < min_threshold: strategy skips deployment
- Rate impact logged in signal metadata for audit trail

### P&L Attribution (pnl-attribution-service)

- Daily P&L adjusted by ratio `projected_apy / raw_apy`
- `rate_impact_adjustment_bps` logged per day per instrument
- Gives realistic P&L that accounts for our market impact

### Alerting (alerting-service)

- `check_rate_deviation()` -- fires when actual rate differs from projected
- Warning (P1) at >50 bps deviation -> Telegram
- Critical (P0) at >200 bps deviation -> PagerDuty + Telegram
- Causes: other large trades, governance parameter changes

## Pipeline Flow

```
features-onchain -> (aave_rate_impact calculator)
                 -> GCS: projected_supply_apy, projected_borrow_apy
                 -> strategy reads projected rates -> sizes position
                 -> execution fills -> pnl-attribution adjusts daily P&L
                 -> alerting monitors actual vs projected -> Telegram
```
