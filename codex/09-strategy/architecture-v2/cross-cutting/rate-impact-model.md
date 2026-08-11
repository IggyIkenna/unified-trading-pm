---
doc_type: codex-ssot
title: Lending/Borrowing Rate Impact Model
summary:
  "Lending/borrowing rate-impact model: simulates how our position shifts the Aave V3 two-slope kinked utilization curve
  before execution (`compute_borrow_rate` / `simulate_rate_impact`); features-onchain writes `projected_supply_apy` /
  `rate_impact_*_bps`; alerting fires >50 bps (P1) / >200 bps (P0) actual-vs-projected deviation."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, features-service, strategy-service]
scope: [engineer, admin]
tags: [defi, features, strategy, execution, risk, monitoring]
[/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md, /codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md]
created: 2026-03-30
authoritative_for: [lending/borrowing rate-impact model (Aave V3 kinked-curve pre-trade rate-impact simulation)]
referenced_by: [/codex/09-strategy/README.md, /codex/09-strategy/architecture-v2/families/carry-and-yield.md]
owner:
last_reviewed:
code_refs:
---

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

### Feature Calculator (features-service (onchain family))

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

## Dual-Mode Design

The rate impact model is designed for two operational modes:

### Mode 1: Batch (Current -- Implemented)

Batch mode defines actual execution prices for backtesting and T+1 reconciliation. The `AaveRateImpactCalculator` in
features-onchain-service computes projected rates from pool state at each candle close. Strategy-service reads these
projections from GCS and uses them for position sizing decisions.

```
features-onchain-service computes projected rates from DefiLlama pool state
  -> writes to GCS: projected_supply_apy, projected_borrow_apy per instrument per date
  -> strategy-service reads projected rates
    -> if projected_supply_apy < min_threshold: skip deployment
  -> execution fills at projected rates (batch/backtest mode)
  -> pnl-attribution adjusts daily P&L by projected_apy / raw_apy ratio
```

### Mode 2: Live Simulation (Planned)

Live mode provides a rate impact preview using actual protocol math per chain/protocol -- analogous to slippage preview
for swaps, but for lending/borrowing. The system simulates how our position size would shift the utilization curve and
change rates for all participants.

**Per-protocol math:**

| Protocol        | Rate Model                                                                                     |
| --------------- | ---------------------------------------------------------------------------------------------- |
| Aave V3         | Two-slope kinked model (see parameters below). Well-defined `U_optimal`, `slope1`, `slope2`.   |
| Compound        | Utilization-based: `borrow_rate = multiplier * utilization + base_rate`. Jump rate above kink. |
| Morpho          | P2P matching layer on top of Aave/Compound. Rate = blend of p2p_rate and pool_rate.            |
| Kamino (Solana) | Leverage vault model. Rate depends on vault utilization and underlying Solana lending rates.   |

**Live preview flow (planned):**

```
1. User requests: "What happens if I lend $5M USDC to Aave V3 on Arbitrum?"
2. Fetch current pool state: total_supply, total_borrows, reserve_factor
3. Simulate: new_utilization = total_borrows / (total_supply + $5M)
4. Compute: new_supply_apy = f(new_utilization, slope1, slope2)
5. Return: {current_apy: 4.2%, projected_apy: 4.05%, impact: -15bps}
```

This is the lending equivalent of DEX slippage preview: "this trade will move the rate by X bps."

## Pipeline Flow

```
features-onchain -> (aave_rate_impact calculator)
                 -> GCS: projected_supply_apy, projected_borrow_apy
                 -> strategy reads projected rates -> sizes position
                 -> execution fills -> pnl-attribution adjusts daily P&L
                 -> alerting monitors actual vs projected -> Telegram
```
