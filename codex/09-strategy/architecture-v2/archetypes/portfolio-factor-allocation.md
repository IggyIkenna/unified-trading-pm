---
doc_type: codex-ssot
title: "Archetype: `PORTFOLIO_FACTOR_ALLOCATION`"
summary: >-
  `PORTFOLIO_FACTOR_ALLOCATION` archetype — factor-exposure sleeve: estimates child factor loadings (carry / momentum /
  vol_premium / size / quality) via OLS over `factor_lookback_days`, solves min‖Σ wᵢβᵢ − target_β‖² under child-weight
  bounds, and emits `AllocationDirective` per child; weekly rebalance with a drift-threshold guard.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, strategy-service]
scope: [engineer, admin]
tags: [portfolio, factor, strategy, features, allocation]
related:
  [
    ../families/portfolio.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-multi-strategy.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-risk-parity.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-tactical-overlay.md,
    ../cross-cutting/portfolio-allocator.md,
  ]
created: 2026-05-18
authoritative_for: [PORTFOLIO_FACTOR_ALLOCATION archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/portfolio-multi-strategy.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-risk-parity.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-tactical-overlay.md,
    /codex/09-strategy/architecture-v2/families/portfolio.md,
    /codex/09-strategy/strategy-summary.md,
  ]
owner:
last_reviewed: 2026-05-18
code_refs:
archetype: PORTFOLIO_FACTOR_ALLOCATION
family: PORTFOLIO
venue_universe: []
topology_requirements:
  isolation: {}
  co_location: []
  latency_budget_ms: 60000
  min_sla_tier: basic
---

# Archetype: `PORTFOLIO_FACTOR_ALLOCATION`

> **Family:** [Portfolio](../families/portfolio.md) **Settlement model:** Cadence-driven — weekly factor-exposure
> re-estimation and weight update. **Code module (target):**
> `strategy-service/engine/strategies/portfolio/factor_allocation_engine.py`

## What it does

Factor-exposure allocation: declares target loadings on systemic factors (carry / momentum / vol / size / quality),
allocates equity to child strategies whose realised factor exposures best match the target. Used for mandate-driven
sleeves where the operator must maintain specific factor tilts (e.g. "40% carry exposure, 30% momentum, 30% vol
premium").

Unlike risk parity (minimise risk concentration) or multi-strategy (fixed weights), factor allocation optimises for a
specific **factor profile** — it allocates more equity to children that efficiently load on the target factors, and less
to children with redundant or off-mandate exposures.

## Position / flow

```
1. RECEIVE: AllocationDirective from Portfolio Allocator service OR operator equity injection.

2. ESTIMATE factor loadings per child i:
   β_i = [β_carry_i, β_momentum_i, β_vol_i, ...]
   Estimated via OLS regression of child daily P&L on factor returns over factor_lookback_days.
   Factor returns come from features-service cross-instrument family (cross-sectional factor realizations).

3. DEFINE target factor exposures (from config):
   target_β = [0.4, 0.3, 0.3, ...]  # operator-set factor targets

4. SOLVE allocation:
   Minimize ||Σ_i weight_i × β_i - target_β||²
   subject to: Σ weight_i = 1, min_child_weight ≤ weight_i ≤ max_child_weight

5. EMIT: AllocationDirective per child:
   target_equity_i = E × weight_i

6. REBALANCE: weekly (or on cadence) with drift-threshold guard.
```

## Canonical factors

| Factor        | Definition                                                            | Data source                               |
| ------------- | --------------------------------------------------------------------- | ----------------------------------------- |
| `carry`       | Funding rate + staking yield premium over risk-free                   | MTDS lending_indices + MTDS funding_rates |
| `momentum`    | 20-day risk-adjusted return per strategy                              | Strategy P&L events                       |
| `vol_premium` | Realized vol vs implied vol spread                                    | features-service volatility family        |
| `size`        | AUM-normalized return (smaller strategies score higher per $ managed) | strategy-service equity state             |
| `quality`     | Sharpe ratio over factor_lookback_days                                | strategy-service P&L attribution          |

The factor set is declared in UAC `unified_api_contracts.canonical.crosscutting.factors.StrategyFactor` (enum).
Non-registered factors → config-load-time error.

## Config schema

```yaml
archetype: PORTFOLIO_FACTOR_ALLOCATION
child_strategy_ids:
  - "ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod"
  - "CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod"
  - "STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod"
  - "YIELD_STAKING_SIMPLE@lido-eth-usdt-prod"

target_factor_exposures: # must reference canonical StrategyFactor enum keys
  carry: 0.40
  momentum: 0.20
  vol_premium: 0.30
  quality: 0.10

factor_lookback_days: 60 # OLS regression window for factor loading estimation
rebalance_cadence: WEEKLY # factor re-estimation + directive re-emission
rebalance_threshold: 0.08 # intra-cadence rebalance if factor exposure drifts > 8pp
min_child_weight: 0.05
max_child_weight: 0.50
min_active_fraction: 0.5
share_class: USD

# Leverage + net-delta (universal):
target_leverage: 1.0
target_net_delta: 0.0
```

## Execution semantics

Identical to `PORTFOLIO_MULTI_STRATEGY` — emits `AllocationDirective` only, no direct `TRADE` instructions.

## Risk / P&L attribution

- **P&L** = weighted sum of child realized P&Ls.
- **Factor attribution**: sleeve-level P&L decomposed into factor contributions via the same regression used for weight
  computation. Attribution events emitted per factor per cadence tick.
- **Risk gate**: fires at sleeve level on total equity drawdown.
- **Model risk**: OLS loadings are estimates with noise; factor exposures can drift between rebalance windows.
  `rebalance_threshold` provides intra-window correction.
- **Insufficient history guard**: children with < `factor_lookback_days` history receive `min_child_weight` until their
  loading estimate is reliable.

## Relationship to Portfolio Allocator service

The Portfolio Allocator's `REGIME_AWARE` allocator switches allocations by regime. `PORTFOLIO_FACTOR_ALLOCATION`
optimises for factor mandate rather than regime regime-switching — they compose for different objectives. See
[`../cross-cutting/portfolio-allocator.md`](../cross-cutting/portfolio-allocator.md).

## Example instances

```
PORTFOLIO_FACTOR_ALLOCATION@multi-strategy-carry-momentum-weekly-usd-prod
PORTFOLIO_FACTOR_ALLOCATION@multi-strategy-crypto-factor-weekly-usdt-prod
PORTFOLIO_FACTOR_ALLOCATION@multi-strategy-tradfi-factor-weekly-usd-prod
```

## Not in this archetype

- Fixed weights (that's `PORTFOLIO_MULTI_STRATEGY`).
- Inverse-vol risk parity (that's `PORTFOLIO_RISK_PARITY`).
- Regime multiplier overlay (that's `PORTFOLIO_TACTICAL_OVERLAY`).
- Full covariance + risk-model optimisation (future extension using `MIN_CVAR` from the Portfolio Allocator service
  archetype set).
