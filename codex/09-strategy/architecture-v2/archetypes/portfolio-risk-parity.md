---
scope: [engineer, admin]
topology_requirements:
  isolation: {}
  co_location: []
  latency_budget_ms: 60000
  min_sla_tier: basic
last_reviewed: 2026-05-18
---

# Archetype: `PORTFOLIO_RISK_PARITY`

> **Family:** [Portfolio](../families/portfolio.md) **Settlement model:** Cadence-driven — rebalances daily using
> trailing realized-volatility estimates. **Code module (target):**
> `strategy-service/engine/strategies/portfolio/risk_parity_engine.py`

## What it does

Risk-parity allocation across child strategy instances. Per-strategy realized-volatility estimate → inverse-vol
weighting → child equity targets. Each child contributes equally to total portfolio risk (measured as P&L volatility
over the estimation window).

Unlike `PORTFOLIO_MULTI_STRATEGY` (static weights), risk parity adapts weights dynamically: a child strategy that
becomes more volatile automatically receives less equity; a child whose P&L stabilizes receives more. The
rebalance fires on cadence and also when drift exceeds `rebalance_threshold`.

## Position / flow

```
1. RECEIVE: AllocationDirective from Portfolio Allocator service OR operator equity injection.
   Total equity E is the sleeve's working capital.

2. ESTIMATE volatility per child i:
   σ_i = rolling realized P&L std dev over vol_lookback_days
   (Source: P&L attribution events per child, pulled from strategy-service state.)

3. COMPUTE weights (inverse-vol, normalized):
   raw_i = 1 / σ_i    (or min_weight_floor if σ_i < epsilon — guards zero-vol child)
   weight_i = raw_i / sum(raw_j)

4. APPLY constraints:
   weight_i = max(min_child_weight, min(max_child_weight, weight_i))
   Renormalize to sum = 1.0 after clipping.

5. EMIT: AllocationDirective per child:
   target_equity_i = E × weight_i

6. MONITOR + REBALANCE: cadence-triggered and drift-triggered (same as PORTFOLIO_MULTI_STRATEGY).
```

## Supported venues / instruments

No direct instrument positions. See `PORTFOLIO_MULTI_STRATEGY` — same structure; only the weight computation differs.

## Config schema

```yaml
archetype: PORTFOLIO_RISK_PARITY
child_strategy_ids:
  - "ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod"
  - "CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod"
  - "STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod"

vol_lookback_days: 20              # trailing window for per-child P&L volatility estimate
vol_estimation_frequency: DAILY    # how often to re-estimate σ_i (DAILY | INTRADAY_4H)
rebalance_cadence: DAILY           # weight recomputation + directive re-emission cadence
rebalance_threshold: 0.10          # intra-cadence rebalance if any weight drifts > 10%
min_child_weight: 0.05             # floor: no child gets less than 5% equity
max_child_weight: 0.60             # ceiling: no child gets more than 60% equity
min_active_fraction: 0.5           # suspend if < 50% of children active
share_class: USD

# Leverage + net-delta (universal):
target_leverage: 1.0
target_net_delta: 0.0
```

## Execution semantics

Identical to `PORTFOLIO_MULTI_STRATEGY` — emits `AllocationDirective` only, no direct `TRADE` instructions.

## Risk / P&L attribution

- **P&L** = weighted sum of child realized P&Ls.
- **Risk gate** fires at sleeve level on total equity drawdown.
- **Estimation risk**: if a child has < `vol_lookback_days` of history, use `max_child_weight` as a conservative
  fallback (new strategies should not dominate allocation before their vol is estimated).
- **Zero-vol guard**: a child with exactly zero P&L volatility (e.g. newly launched, no fills yet) receives the
  `min_child_weight` floor, not infinite weight.

## Relationship to Portfolio Allocator service

Risk-parity at the strategy level is distinct from the Portfolio Allocator's `RISK_PARITY` allocator archetype
(which operates at the client-level equity → strategy allocation layer). This archetype is a strategy-level
risk-parity computation running INSIDE the portfolio sleeve. They can be stacked:

```
Portfolio Allocator (RISK_PARITY archetype, client level)
  → AllocationDirective → PORTFOLIO_RISK_PARITY (strategy level)
      → AllocationDirective → child strategies (instrument level)
```

See [`../cross-cutting/portfolio-allocator.md`](../cross-cutting/portfolio-allocator.md).

## Not in this archetype

- Fixed weights (that's `PORTFOLIO_MULTI_STRATEGY`).
- Factor-exposure targeting (that's `PORTFOLIO_FACTOR_ALLOCATION`).
- Regime-aware switching (that's `PORTFOLIO_TACTICAL_OVERLAY`).
- Full-covariance optimisation (future extension; current implementation is diagonal — per-child vol only, no
  cross-strategy correlation term).
