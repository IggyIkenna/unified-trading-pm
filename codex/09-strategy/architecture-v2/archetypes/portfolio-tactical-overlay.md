---
doc_type: codex-ssot
title: "Archetype: `PORTFOLIO_TACTICAL_OVERLAY`"
summary: >-
  `PORTFOLIO_TACTICAL_OVERLAY` archetype — regime/operator-driven re-weighting over a base allocation: a regime
  classifier (features-service `regime_classifier_signal`) or operator tactical-override maps per-family multipliers
  onto `base_weights` (clamped by `max_single_multiplier` 2.0), firing intraday on regime change (10s budget).
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, strategy-service]
scope: [engineer, admin]
tags: [portfolio, regime, allocation, features, tactical]
related:
  [
    ../families/portfolio.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-multi-strategy.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-risk-parity.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-factor-allocation.md,
    ../cross-cutting/portfolio-allocator.md,
  ]
created: 2026-05-18
authoritative_for: [PORTFOLIO_TACTICAL_OVERLAY archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/portfolio-factor-allocation.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-multi-strategy.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-risk-parity.md,
    /codex/09-strategy/architecture-v2/families/portfolio.md,
    /codex/09-strategy/strategy-summary.md,
  ]
owner:
last_reviewed: 2026-05-18
code_refs:
archetype: PORTFOLIO_TACTICAL_OVERLAY
family: PORTFOLIO
venue_universe: []
topology_requirements:
  isolation: {}
  co_location: []
  latency_budget_ms: 10000
  min_sla_tier: basic
---

# Archetype: `PORTFOLIO_TACTICAL_OVERLAY`

> **Family:** [Portfolio](../families/portfolio.md) **Settlement model:** Regime/operator-driven — fires on regime
> change or operator command; not purely cadence-driven. **Code module (target):**
> `strategy-service/engine/strategies/portfolio/tactical_overlay_engine.py`

## What it does

Operator/regime-driven tactical re-weighting on top of a base allocation. A regime classifier or explicit operator
command produces per-strategy multipliers that adjust the base weight vector. Higher-frequency rebalancing than the
other 3 portfolio archetypes — intraday firing is supported when regime transitions are detected.

The key distinction from the other Portfolio archetypes:

| Archetype                        | Weight driver                                      |
| -------------------------------- | -------------------------------------------------- |
| `PORTFOLIO_MULTI_STRATEGY`       | Static config — no change until operator edits     |
| `PORTFOLIO_RISK_PARITY`          | Realised volatility per child                      |
| `PORTFOLIO_FACTOR_ALLOCATION`    | Factor exposure vs mandate                         |
| **`PORTFOLIO_TACTICAL_OVERLAY`** | **Regime classifier OR explicit operator command** |

Tactical overlay is used for mandates that require **situational response**: reduce risk-on strategies during vol-spike
regimes; increase carry exposure in low-vol/high-rate environments; rotate toward defensive strategies on operator
risk-off command.

## Position / flow

```
1. RECEIVE: AllocationDirective (equity E) + base_weights config
   (same format as PORTFOLIO_MULTI_STRATEGY child_weights).

2. MONITOR regime signals (continuous):
   - Regime classifier: features-service cross-instrument regime_signal data_type
     (e.g. VIX level, vol-regime, carry-regime, risk-on/off composite)
   - Operator command: RebalanceTrigger event with multiplier_override payload

3. COMPUTE multiplier per child (on regime change or operator command):
   multiplier_i = regime_multiplier_table[detected_regime][child_archetype_family]
   e.g. HIGH_VOL regime → ML Directional ×1.2, Carry ×0.6, Vol Trading ×1.5

4. COMPUTE effective weights:
   raw_i = base_weight_i × multiplier_i
   weight_i = raw_i / sum(raw_j)   # renormalize
   Clip to [min_child_weight, max_child_weight]; renormalize again.

5. EMIT: AllocationDirective per child:
   target_equity_i = E × weight_i

6. REBALANCE cadence (background): fallback to base_weights on cadence if no regime event.
```

## Regime classifier integration

The regime signal comes from features-service `cross_instrument` family (`regime_classifier_signal` data_type). The
overlay maps each regime label to a multiplier table defined in config:

```yaml
regime_multiplier_tables:
  LOW_VOL_HIGH_CARRY: # calm, carry-rich environment
    CARRY: 1.4
    ML_DIRECTIONAL: 0.9
    VOL_TRADING: 0.7
    STAT_ARB: 1.0
  HIGH_VOL_RISK_OFF: # stress, vol-spike regime
    CARRY: 0.5
    ML_DIRECTIONAL: 1.1
    VOL_TRADING: 1.6
    STAT_ARB: 1.2
  NEUTRAL: # base weights — 1.0 multiplier for all families
    CARRY: 1.0
    ML_DIRECTIONAL: 1.0
    VOL_TRADING: 1.0
    STAT_ARB: 1.0
```

Multiplier table keys are child archetype FAMILY names (not individual archetype IDs), allowing bulk treatment of all
children in the same family.

## Config schema

```yaml
archetype: PORTFOLIO_TACTICAL_OVERLAY
child_strategy_ids:
  - "ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod"
  - "CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod"
  - "VOL_TRADING_OPTIONS@deribit-eth-usdt-prod"

base_weights: # base allocation; regime multipliers scale from here
  - 0.40 # ML_DIRECTIONAL_CONTINUOUS
  - 0.35 # CARRY_BASIS_PERP
  - 0.25 # VOL_TRADING_OPTIONS

regime_source: cross_instrument/regime_classifier_signal # features-service data_type
regime_lookback_bars: 12 # regime averaging window (12 × 4h bars = 2-day average)

regime_multiplier_tables: # see inline YAML example above
  LOW_VOL_HIGH_CARRY:
    CARRY: 1.4
    ML_DIRECTIONAL: 0.9
    VOL_TRADING: 0.7
  HIGH_VOL_RISK_OFF:
    CARRY: 0.5
    ML_DIRECTIONAL: 1.1
    VOL_TRADING: 1.6
  NEUTRAL:
    CARRY: 1.0
    ML_DIRECTIONAL: 1.0
    VOL_TRADING: 1.0

min_regime_confidence: 0.70 # classifier confidence threshold; below → NEUTRAL regime
rebalance_cadence: DAILY # fallback cadence when no regime event fires
rebalance_threshold: 0.08 # intra-cadence drift guard
min_child_weight: 0.05
max_child_weight: 0.70
min_active_fraction: 0.5
share_class: USD

# Leverage + net-delta (universal):
target_leverage: 1.0
target_net_delta: 0.0
```

## Execution semantics

Identical to `PORTFOLIO_MULTI_STRATEGY` — emits `AllocationDirective` only. On regime change:

1. Recompute effective weights using new regime label.
2. Emit revised directives to children immediately (within `latency_budget_ms` = 10 000 ms for intraday response).
3. Emit `REGIME_TRANSITION` event to audit log with old/new regime + old/new weights.

Operator command path:

- `POST /api/strategies/{id}/tactical-override` in strategy-service API.
- Body: `{ "regime_label": "HIGH_VOL_RISK_OFF", "duration_minutes": 240, "operator_id": "..." }`.
- Overlay reverts to classifier-driven regime after `duration_minutes` expires.

## Risk / P&L attribution

- **P&L** = weighted sum of child realized P&Ls.
- **Regime attribution**: sleeve P&L decomposed into base-weight component and overlay-multiplier component.
- **Risk gate**: fires at sleeve level on total equity drawdown.
- **Multiplier clamp**: `max_single_multiplier: 2.0` — no regime multiplier may exceed 2× regardless of table config.
  Guards against extreme regime mis-classification causing gross over-concentration.

## Relationship to Portfolio Allocator service

The Portfolio Allocator's `REGIME_AWARE` allocator also switches allocations by regime — but at the client→strategy
equity level. `PORTFOLIO_TACTICAL_OVERLAY` applies regime logic WITHIN a strategy sleeve (across child strategies), one
level deeper. They can be stacked without conflict. See
[`../cross-cutting/portfolio-allocator.md`](../cross-cutting/portfolio-allocator.md).

## Example instances

```
PORTFOLIO_TACTICAL_OVERLAY@multi-strategy-crypto-regime-daily-usdt-prod
PORTFOLIO_TACTICAL_OVERLAY@multi-strategy-tradfi-regime-daily-usd-prod
PORTFOLIO_TACTICAL_OVERLAY@multi-strategy-mixed-regime-daily-usd-prod
```

## Not in this archetype

- Static allocation (that's `PORTFOLIO_MULTI_STRATEGY`).
- Inverse-vol risk parity (that's `PORTFOLIO_RISK_PARITY`).
- Factor-mandate allocation (that's `PORTFOLIO_FACTOR_ALLOCATION`).
- Direct instrument trades (no `TRADE` instructions ever).
