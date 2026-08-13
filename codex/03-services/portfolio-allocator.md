---
doc_type: codex-ssot
title: portfolio-allocator-service
summary:
  "The portfolio allocator: one instance per client owning strategy-scope capital allocation, runs ONE allocator
  archetype drawn from two groups — generic weighting engines (FIXED/PNL_WEIGHTED/SHARPE_WEIGHTED/RISK_PARITY/KELLY/
  MIN_CVAR/REGIME_AWARE/MANUAL) and per-archetype RANK allocators that select and weight along an axis (coin/venue/
  protocol/expiry/LST), including the two dispersion allocators — and emits versioned AllocationDirective events per
  cadence; reads PBMS NAVs + risk kill-switches; guard rails, shadow mode, cross-share-class NAV conversion; does NOT
  move venue capital or rebalance positions. Currently HOSTED INSIDE strategy-service, not yet a separate repo."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer]
tags: [portfolio-allocator, strategy, execution, reconciliation]
related:
  [
    /codex/03-services/venue-capability-registry.md,
    /codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md,
    /codex/04-architecture/capital-flow-model.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
  ]
created: 2026-04-17
authoritative_for: [portfolio-allocator-service, allocator archetypes]
referenced_by:
  [
    /codex/03-services/venue-capability-registry.md,
    /codex/04-architecture/capital-flow-model.md,
    /codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md,
  ]
owner:
last_reviewed:
code_refs:
---

# portfolio-allocator-service

> **What it is:** The component that owns the **strategy scope** of capital allocation. One instance per client, runs
> one allocator archetype, emits `AllocationDirective` events per cadence.
>
> **⚠️ WHERE IT ACTUALLY LIVES (corrected 2026-08-12).** This doc previously said "Not inside strategy-service —
> separate service with its own lifecycle, versioning, replay, and UI." **That describes the target, not the present.**
> The code is at `strategy_service/portfolio_allocator/` and its own `__init__.py` states the placement is pragmatic for
> the v2 migration, with a dedicated `portfolio-allocator-service` repo as the target — and **no such repo exists**
> (verified 2026-08-12 against the 26-repo estate). The import surface is deliberately stable so the sub-package can
> move in-tree with zero call-site changes when the split happens. Read "separate service" below as the destination;
> anyone looking for the repo today will not find one.

## Responsibilities

1. Per-client allocator configuration + state
2. Scheduled + event-driven allocation computation
3. Emit `AllocationDirective` events (versioned + auditable)
4. Shadow mode for allocator upgrades
5. Integration with PBMS (read NAVs + returns per strategy)
6. Integration with risk-service (killed strategies → 0 weight)
7. Cross-share-class NAV conversion for allocation
8. Validation (guard rails, limits)

## Service boundaries

- **Reads from:** PBMS (strategy NAVs, returns), risk-service (kill switches), config store (allocator configs)
- **Writes to:** event stream (AllocationDirective), audit log
- **Not responsible for:** moving venue capital (transfer-rebalance), rebalancing positions (strategies do this
  themselves)

## Allocator archetypes — two groups

> **No total is given here on purpose.** This doc claimed "8 allocator archetypes" in its title, summary,
> `authoritative_for` facet and this heading while `ALLOCATOR_ARCHETYPE_REGISTRY` had **more than twice that** — and the
> code's own `portfolio_allocator/__init__.py` docstring agreed with the wrong number, so doc and code corroborated each
> other into a false consensus. **That is how the entire rank-allocator layer, including both dispersion allocators,
> stayed invisible to a reader working from this SSOT** (measured 2026-08-12). The registry is the oracle:
> `grep 'AllocatorArchetype\.' strategy_service/portfolio_allocator/archetypes.py`.

### Group 1 — generic weighting engines

Weight a set of strategy instances by a portfolio statistic. Axis-agnostic.

| Archetype         | Allocation rule                    |
| ----------------- | ---------------------------------- |
| `FIXED`           | Constant weights                   |
| `PNL_WEIGHTED`    | Weight ∝ trailing P&L              |
| `SHARPE_WEIGHTED` | Weight ∝ trailing Sharpe           |
| `RISK_PARITY`     | Weight ∝ 1/vol                     |
| `KELLY`           | Fractional Kelly across strategies |
| `MIN_CVAR`        | Minimize tail risk                 |
| `REGIME_AWARE`    | Swap weights per detected regime   |
| `MANUAL`          | Human-in-loop                      |

### Group 2 — per-archetype RANK allocators (Phase 8)

**This is the layer that makes "weights on coins / venues / protocols" work.** Each ranks a candidate universe along an
axis, filters by a metric threshold, truncates to top-N and weights by the metric — so axis selection and axis weighting
are one operation. Implemented in `portfolio_allocator/archetypes_rank.py` over a shared `BaseRankAllocator`.

| Archetype                         | Axis (group → member)  | Ranking metric        |
| --------------------------------- | ---------------------- | --------------------- |
| `CARRY_FUNDING_RANK`              | coin                   | funding APY           |
| `CARRY_BASIS_PERP_RANK`           | coin → venue           | basis APY             |
| `CARRY_BASIS_DATED_RANK`          | coin → venue (+expiry) | dated basis APY       |
| `CARRY_STAKED_BASIS_RANK`         | LST → venue            | staked basis APY      |
| `CARRY_RECURSIVE_STAKED_RANK`     | LST → venue            | recursive staked APY  |
| `YIELD_STAKING_SIMPLE_RANK`       | protocol               | staking APY           |
| `YIELD_ROTATION_LENDING_RANK`     | protocol               | lending supply APY    |
| `CARRY_FUNDING_DISPERSION_RANK`   | coin (single-stage)    | raw perp funding bps  |
| `ARBITRAGE_PRICE_DISPERSION_RANK` | venue                  | cross-venue price gap |

Two shapes: **single-stage** (rank across the whole cohort, no grouping — the dispersion allocators) and **hierarchical
2-stage** (`_hierarchical_rank_weight`: group by axis token, score group by `avg(metric)`, filter, truncate to
`top_n_groups`, then within each surviving group filter and truncate to `top_n_per_group`).

Each archetype is a separate engine class. One engine per archetype. **One allocator instance picks one archetype.**

## How composition actually works — two levels, no composite archetype

A "composite strategy" is **not** a single archetype holding a basket, and there is no composition concept above the
instance. `StrategyInstanceDefinition` carries ONE `archetype_id` and ONE `capital_budget_amount` **by design**:

1. **Across instances** — the allocator weights many single-archetype instances via `target_weights` in one
   `AllocationDirective` per client per tick, then `apply_guard_rails` constrains those weights by per-weight cap,
   turnover, correlation and **family + category diversification**. "Weights on archetypes" is expressed as weights on
   instances plus family-level guard rails.
2. **Within an axis** — a Group-2 rank allocator selects and weights across coins/venues/protocols.

A long/short basket is therefore N instances of one archetype, each emitting its own leg, coordinated by a shared
cross-sectional signal — see
[`carry-funding-dispersion`](/codex/09-strategy/architecture-v2/archetypes/carry-funding-dispersion.md), which is
exactly this shape.

### `FIXED`

```yaml
archetype: FIXED
weights:
  ML_DIRECTIONAL_CONTINUOUS@...: 0.40
  CARRY_BASIS_PERP@...: 0.30
  STAT_ARB_PAIRS_FIXED@...: 0.20
  ARBITRAGE_PRICE_DISPERSION@...: 0.10
```

### `PNL_WEIGHTED`

```yaml
archetype: PNL_WEIGHTED
lookback_days: 30
weight_formula: TRAILING_RETURN
bottom_floor: 0.05 # no strategy goes below 5%
top_cap: 0.40 # no strategy goes above 40%
```

### `SHARPE_WEIGHTED`

```yaml
archetype: SHARPE_WEIGHTED
lookback_days: 30
weight_formula: TRAILING_SHARPE
negative_sharpe_floor: 0 # kill weight when Sharpe < 0
max_weight: 0.40
```

### `RISK_PARITY`

```yaml
archetype: RISK_PARITY
vol_window_days: 30
use_rolling_covariance: true
rebalance_threshold: 0.10
```

### `KELLY`

```yaml
archetype: KELLY
kelly_fraction: 0.25 # fractional Kelly to avoid over-leverage
edge_lookback_days: 90
covariance_window_days: 60
```

### `MIN_CVAR`

```yaml
archetype: MIN_CVAR
confidence_level: 0.95
lookback_days: 90
optimizer: SLSQP # or PY_CVXPY
constraints:
  min_weight: 0.02
  max_weight: 0.40
```

### `REGIME_AWARE`

```yaml
archetype: REGIME_AWARE
regime_feature_ref: macro-regime-feature@v4
regime_weights:
  VOL_HIGH: { ..., CARRY_BASIS_PERP: 0.05, VOL_TRADING_OPTIONS: 0.40, ... }
  VOL_LOW: { ..., CARRY_BASIS_PERP: 0.30, VOL_TRADING_OPTIONS: 0.10, ... }
  RISK_ON: { ... }
  RISK_OFF: { ... }
```

### `MANUAL`

```yaml
archetype: MANUAL
approval_queue: client-A-allocator-queue
auto_propose_formula: SHARPE_WEIGHTED # suggests; operator approves
```

## Cadence

```yaml
allocator_cadence: DAILY
cadence_time_utc: "16:00"
min_directive_change_pct: 0.05
cool_down_seconds: 3600
event_triggered:
  on_kill_switch: true
  on_strategy_retire: true
  on_deposit_ack: true
```

## AllocationDirective event

Output of each cycle:

```yaml
allocation_directive_id: "ad_2026-04-17T16:00:00Z_clientA"
allocator_id: "SHARPE_WEIGHTED@client-A-v3"
allocator_version: 3
client_id: "client_A_fund"
cadence_tick: "2026-04-17T16:00:00Z"
total_client_equity_reporting_currency: 10_000_000 # USD
directives:
  - strategy_instance_id: "ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod"
    target_equity: 2_500_000
    target_equity_share_class: 2_500_000 # USDT
    share_class: USDT
    weight_pct: 0.25
  - strategy_instance_id: "CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod"
    target_equity: 1_500_000
    target_equity_share_class: 1_500_000
    share_class: USDT
    weight_pct: 0.15
  - strategy_instance_id: "STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod"
    target_equity: 1_000_000
    target_equity_share_class: 1_000_000
    share_class: USD
    weight_pct: 0.10
rationale:
  - "Sharpe weighting 30-day window"
  - "ML strategy 30d Sharpe 1.8 → weight +5%"
  - "Basis strategy 30d Sharpe 1.2 → weight unchanged"
guard_rails_triggered: []
```

## Guard rails

Before emitting, the allocator validates:

- Max weight per strategy ≤ 40%
- Min weight per strategy ≥ 2% (else retire)
- Max turnover per cycle ≤ 30%
- Correlation cap: max combined weight across correlated pair ≤ 50%
- Family diversification: any family ≤ X%
- Category diversification: any category ≤ X%

If a rule fires, the directive is modified (clipped) and `guard_rails_triggered` records which.

## Shadow mode

Two allocator instances per client:

```yaml
primary: SHARPE_WEIGHTED@client-A-v3
shadow: KELLY@client-A-v1 # paper; directives logged not emitted
```

Shadow runs full logic; directives saved to audit but not published. After N cycles of satisfactory behavior → promote.
Shadow can span weeks.

## Cross-share-class handling

Client reports in one currency (e.g., USD). Strategies may be in different share classes. Allocator:

1. Pulls each strategy's NAV in its share class
2. Converts to client reporting currency using FX snapshot
3. Runs allocation in reporting currency
4. Converts back to each strategy's share class
5. Directive carries both `target_equity` (reporting currency) and `target_equity_share_class`

If cross-currency transfer required, allocator flags it for transfer-rebalance-service; actual move happens via
TRANSFER/BRIDGE instructions.

## API

```
GET  /allocators                                    → list per client
GET  /allocators/{client_id}                        → config + current state
GET  /allocators/{client_id}/history                → historical directives
POST /allocators/{client_id}/trigger                → force cycle
PUT  /allocators/{client_id}/config                 → update (new version)
GET  /allocators/{client_id}/shadow-compare         → shadow vs primary outputs
POST /allocators/{client_id}/approve-manual/{id}    → MANUAL archetype approval
```

## Storage

- Allocator configs: config registry (versioned, content-hashed)
- Directives: event stream + audit log
- NAVs + returns read from PBMS real-time
- No local strategy P&L computation — uses PBMS as SSOT

## Deployment

- Stateless service; one instance with horizontal scaling ok
- Scheduled jobs (cron or event-driven)
- Leader-election for single-emitter guarantee per (client_id, cadence_tick)

## Tests

- Unit: each archetype math correctness
- Integration: end-to-end with fake PBMS + event stream
- Property-based: guard rails never violated
- Shadow diff: shadow vs primary deterministic given same inputs
- Replay: given historical data, replay produces identical directives

## UI

- Dashboard per client showing current weights + rationale
- Historical directive timeline
- Shadow comparison
- Manual approval queue (for MANUAL archetype)
- Allocator config diff (v3 → v4)

## Cross-references

- Cross-cutting concern:
  [/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md](/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md)
- Capital flow model: [/codex/04-architecture/capital-flow-model.md](/codex/04-architecture/capital-flow-model.md)
- Venue capability registry: [venue-capability-registry.md](venue-capability-registry.md)
- Capital structure:
  [/codex/04-architecture/capital-structure-and-regulatory.md](/codex/04-architecture/capital-structure-and-regulatory.md)

## Not in this doc

- **Per-archetype math implementation** — service code
- **Regime detection feature** — features-onchain / features-macro
- **PBMS API details** — PBMS docs
- **Transfer execution** — transfer-rebalance service
- **UI-specific code** — UI repos
