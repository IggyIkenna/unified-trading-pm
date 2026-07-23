---
doc_type: codex-ssot
title: "Archetype: `PORTFOLIO_MULTI_STRATEGY`"
summary: >-
  `PORTFOLIO_MULTI_STRATEGY` archetype — the simplest Portfolio sleeve: fixed operator-set `child_weights` across child
  strategy instances, emits `AllocationDirective` only (never TRADE), redistributes across active children, rebalances
  on DAILY/WEEKLY/MONTHLY cadence + `rebalance_threshold`; enables nested (composable) portfolio construction.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [portfolio, allocation, strategy, orchestrator]
related:
  [
    ../families/portfolio.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-risk-parity.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-factor-allocation.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-tactical-overlay.md,
    ../cross-cutting/portfolio-allocator.md,
  ]
created: 2026-05-18
authoritative_for: [PORTFOLIO_MULTI_STRATEGY archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/portfolio-factor-allocation.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-risk-parity.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-tactical-overlay.md,
    /codex/09-strategy/architecture-v2/families/portfolio.md,
    /codex/09-strategy/strategy-summary.md,
  ]
owner:
last_reviewed: 2026-05-18
code_refs:
archetype: PORTFOLIO_MULTI_STRATEGY
family: PORTFOLIO
venue_universe: []
topology_requirements:
  isolation: {}
  co_location: []
  latency_budget_ms: 60000
  min_sla_tier: basic
---

# Archetype: `PORTFOLIO_MULTI_STRATEGY`

> **Family:** [Portfolio](../families/portfolio.md) **Settlement model:** Cadence-driven — rebalances on a fixed
> schedule (daily / weekly / monthly). **Code module (target):**
> `strategy-service/engine/strategies/portfolio/multi_strategy_engine.py`

## What it does

Equal-weighted (or operator-fixed-weight) multi-strategy sleeve. Allocates equity across N child strategy instances
spanning multiple families (e.g. ML Directional + Carry + Vol Trading) with operator-mandated weights. Rebalances on a
fixed cadence; within a rebalance window the weights are held constant.

This is the simplest Portfolio archetype — the allocation rule is static: weights are set in config and only change when
the operator updates the config. The value-add versus the Portfolio Allocator service's FIXED allocator is that this
archetype is itself a strategy instance (receives equity, is risk-gated, can be itself allocated-to by a higher
allocator) enabling **nested portfolio construction**.

## Position / flow

```
1. RECEIVE: AllocationDirective from Portfolio Allocator service OR operator equity injection.
   Total equity E is the sleeve's working capital.

2. COMPUTE weights: fixed config array (weight_i for each child i; sum = 1.0).
   If any child is inactive (kill-switched, paused), redistribute proportionally
   across remaining active children (or hold as cash if min_active_fraction not met).

3. EMIT: AllocationDirective per child:
   target_equity_i = E × weight_i

4. MONITOR: on each cadence tick, re-read child realized equity.
   If |realized_i / E - weight_i| > rebalance_threshold, re-emit directive.

5. REBALANCE: cadence-triggered re-emission of directives at rebalance_cadence.
```

## Supported venues / instruments

No direct instrument positions. Child strategies hold the actual positions; the sleeve manages only capital allocation.
The `child_strategy_ids` config must reference valid registered strategy instances.

## Config schema

```yaml
archetype: PORTFOLIO_MULTI_STRATEGY
child_strategy_ids:
  - "ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod"
  - "CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod"
  - "STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod"

child_weights: # must sum to 1.0; indexed same order as child_strategy_ids
  - 0.40
  - 0.35
  - 0.25

rebalance_cadence: DAILY # or WEEKLY | MONTHLY | MANUAL
rebalance_threshold: 0.05 # drift fraction before intra-cadence rebalance fires (0.05 = 5%)
min_active_fraction: 0.5 # if fewer than 50% of children active, suspend allocation + alert
cash_buffer_pct: 0.0 # fraction of equity held as unallocated cash (0 = fully deployed)
share_class: USD # always USD* for portfolio archetypes

# Leverage + net-delta controls (universal per StrategyInstanceDefinition):
target_leverage: 1.0 # portfolio sleeve operates at 1× by definition
target_net_delta: 0.0 # sleeve itself is delta-neutral; children manage their own delta
```

## Execution semantics

- Emits `AllocationDirective` events only (no `TRADE` instructions).
- No kill-switch at the sleeve level triggers child CLOSE_ALL — each child has its own kill-switch.
- Sleeve-level kill-switch suspends re-emission of new directives; existing child allocations wind down naturally.
- `MANUAL` cadence requires an explicit operator `RebalanceTrigger` event.

## Risk / P&L attribution

- **P&L** = weighted sum of child realized P&Ls. Attribution factor: `CARRY_SLEEVE` / `ML_SLEEVE` per child family.
- **Risk gate** fires at sleeve level on total equity drawdown (sleeve-level `max_drawdown_pct` in config).
- **Concentration risk**: `child_weights[i] ≤ max_single_strategy_weight` enforced at config load time.

## Relationship to Portfolio Allocator service

`PORTFOLIO_MULTI_STRATEGY` is itself allocated equity by the Portfolio Allocator service (or operator injection). It
then acts as a mini-allocator for its child strategies. The Portfolio Allocator's `FIXED` archetype does the same thing
one level up — but it is not a strategy instance and cannot itself be nested. This archetype enables **composable
nesting**:

```
Portfolio Allocator (service)
  → AllocationDirective → PORTFOLIO_MULTI_STRATEGY (strategy instance)
      → AllocationDirective → ML_DIRECTIONAL_CONTINUOUS (child strategy)
      → AllocationDirective → CARRY_BASIS_PERP (child strategy)
```

See [`../cross-cutting/portfolio-allocator.md`](../cross-cutting/portfolio-allocator.md) for the service-level
architecture.

## Example instances

```
PORTFOLIO_MULTI_STRATEGY@multi-strategy-crypto-daily-usd-prod
PORTFOLIO_MULTI_STRATEGY@multi-strategy-tradfi-weekly-usd-prod
PORTFOLIO_MULTI_STRATEGY@multi-strategy-mixed-daily-usd-prod
```

## Not in this archetype

- Dynamic weight optimisation (that's `PORTFOLIO_RISK_PARITY` or `PORTFOLIO_FACTOR_ALLOCATION`).
- Regime-aware weight switching (that's `PORTFOLIO_TACTICAL_OVERLAY`).
- Direct instrument positions (no `TRADE` instructions ever).
