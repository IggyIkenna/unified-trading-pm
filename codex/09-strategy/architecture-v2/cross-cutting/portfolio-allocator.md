---
doc_type: codex-ssot
title: "Cross-Cutting: Portfolio Allocator"
summary:
  "Strategy-scope capital allocator (dedicated service): 8 archetypes (FIXED / PNL_WEIGHTED / SHARPE_WEIGHTED /
  RISK_PARITY / KELLY / MIN_CVAR / REGIME_AWARE / MANUAL) emit `AllocationDirective` per cadence; strategies rescale via
  `react_to_equity_change`. Owns strategies-within-one-client scope only — not venue or client scope."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [portfolio-allocator, strategy, allocation, reconciliation, risk, kelly]
related:
  [
    ../../../03-services/portfolio-allocator.md,
    /codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md,
    /codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md,
    ../../../04-architecture/capital-flow-model.md,
  ]
created: 2026-04-17
authoritative_for:
  [strategy-scope capital-allocation primitive (AllocationDirective reconciliation across strategies-within-one-client)]
referenced_by:
  [
    /codex/03-services/portfolio-allocator.md,
    /codex/04-architecture/capital-flow-model.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/04-architecture/shadow-deployment-pattern.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-factor-allocation.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-multi-strategy.md,
    /codex/09-strategy/architecture-v2/archetypes/portfolio-risk-parity.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cross-Cutting: Portfolio Allocator

> **What it is:** The strategy-level capital allocation primitive. Portfolio Allocator decides how much equity each
> strategy instance has, per client, per cadence. Emits `AllocationDirective` events; strategies reconcile their new
> equity and adapt positions. Separate, dedicated service; not inside strategy-service.

## Scope

Portfolio Allocator owns the **strategy scope** of capital movement (strategies-within-one-client). It does NOT move
capital between venues (that's [transfer-rebalance.md](transfer-rebalance.md)) or between clients (platform allocator).

All three scopes share the "target X at Y = Z" event-driven reconciliation primitive.

## Why a dedicated service

- **Allocators are algorithms**, not strategy code — they need their own compute, own versioning, own replay
- **Per-client allocator instances** — each client can have a different allocator archetype + config
- **Separation of concerns** — strategy focuses on alpha; allocator focuses on capital efficiency
- **Versioned artifacts** — allocator algorithm changes are consumer-opt-in, not auto-upgrade
- **Auditable** — every AllocationDirective is logged with the allocator algorithm version + inputs

## 8 Allocator Archetypes

| #   | Archetype         | Allocation rule                                                            |
| --- | ----------------- | -------------------------------------------------------------------------- |
| 1   | `FIXED`           | Constant weights set by operator                                           |
| 2   | `PNL_WEIGHTED`    | Weight ∝ trailing P&L contribution                                         |
| 3   | `SHARPE_WEIGHTED` | Weight ∝ trailing Sharpe ratio                                             |
| 4   | `RISK_PARITY`     | Weight ∝ 1/vol; equal risk contribution                                    |
| 5   | `KELLY`           | Full/fractional Kelly across strategies using historical edge + covariance |
| 6   | `MIN_CVAR`        | Minimize tail risk (5% CVaR); constrained optimizer                        |
| 7   | `REGIME_AWARE`    | Weights swap by detected regime (vol-high/vol-low, risk-on/risk-off)       |
| 8   | `MANUAL`          | Human-in-loop approval on every directive                                  |

Every per-client allocator instance picks ONE archetype (no composite archetypes — if genuinely hybrid, build a new
archetype).

## AllocationDirective event

```yaml
allocation_directive_id: "ad_2026-04-17T12:00:00Z_clientA"
client_id: "client_A_fund"
allocator_id: "SHARPE_WEIGHTED@client-A-v3"
allocator_version: 3
cadence_tick: "2026-04-17T12:00:00Z"
directives:
  - strategy_instance_id: "ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod"
    target_equity: 2_500_000
  - strategy_instance_id: "CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod"
    target_equity: 1_500_000
  - strategy_instance_id: "STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod"
    target_equity: 1_000_000
  ...
rationale:
  - "Sharpe weighting over 30-day window"
  - "ML strategy delivered +1.8 Sharpe; equity raised 10%"
  - "Basis strategy Sharpe stable at 1.2; equity unchanged"
```

## Reconciliation flow

```
Allocator fires per cadence
    │
    ▼
Computes target equity per strategy instance
    │
    ▼
Emits AllocationDirective event
    │
    ▼
Each strategy subscribes to directives for its instance_id
    │
    ▼
Strategy:
  1. Self-check (new equity sane? within limits?)
  2. Update internal equity
  3. Rescale positions proportionally (via react_to_equity_change)
  4. Emit StrategyInstructions to realize new target
    │
    ▼
Transfer/rebalance pulls capital between venues if needed
    │
    ▼
PBMS confirms new strategy-level capital footprint
```

## Allocator inputs

Each archetype consumes a specific set of inputs:

| Archetype       | Inputs                                                                                        |
| --------------- | --------------------------------------------------------------------------------------------- |
| FIXED           | Operator config (weights)                                                                     |
| PNL_WEIGHTED    | Per-strategy P&L series from PBMS                                                             |
| SHARPE_WEIGHTED | P&L series + daily/hourly returns                                                             |
| RISK_PARITY     | Realized vol per strategy + correlation matrix                                                |
| KELLY           | Historical edge + covariance matrix per strategy                                              |
| MIN_CVAR        | Return distribution per strategy (bootstrapped)                                               |
| REGIME_AWARE    | Regime detection feature (from features-onchain or macro features) + per-regime weights table |
| MANUAL          | Operator approval queue                                                                       |

## Cadence

Allocators run on a schedule:

```yaml
allocator_cadence: DAILY # or HOURLY, WEEKLY, MONTHLY, ON_EVENT
cadence_time_utc: "16:00" # NYSE close
min_directive_change_pct: 0.05 # only emit directive if any weight moves >5%
cool_down_seconds: 3600 # don't re-fire within 1h of last directive
```

## Guard rails

- **Max weight per strategy** — e.g., no single strategy > 40% of client equity
- **Min weight per strategy** (when active) — e.g., no active strategy < 2% (else retire it)
- **Max turnover per cycle** — e.g., no directive that moves > 30% of total equity
- **Correlation cap** — if two strategies' correlation > 0.8, cap combined weight
- **Family diversification** — max X% in any one family
- **Venue-category diversification** — max X% in any one category (CEFI/DEFI/SPORTS/TRADFI/PREDICTION)

## Fund-client framing

When the client is itself a fund, the allocator runs at the **fund level** — treating the fund as a single client,
allocating across strategies that serve that fund. Investor-level accounting (who in the fund owns what % of the fund's
P&L) is handled at the fund layer, not by our allocator.

See
[../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md).

## Versioning

Allocator algorithm versions are **artifact versions** (consumer-opt-in). An algorithm upgrade is a new allocator
version; the per-client allocator instance pins a specific version.

Upgrading an allocator archetype (SHARPE → KELLY) is a new allocator instance, not a version bump.

## Interaction with strategy kill-switches

When a strategy is killed:

- Allocator receives kill-switch event
- Allocator re-runs with killed strategy at weight 0
- Redistributes freed capital across live strategies per its rule
- Emits new AllocationDirective

## Cross-share-class allocation

If strategies in the allocator's universe are in different share classes (USDT, USDC, USD, ETH), the allocator:

- Converts each strategy's NAV to the **client reporting currency**
- Allocates in the reporting currency
- Instructs each strategy with its share-class-native equity
- Transfer/rebalance handles cross-currency moves if needed

## Shadow allocator mode

Before promoting a new allocator version, run it in **shadow mode**:

- Shadow allocator computes directives but does NOT emit
- Directives are logged + compared vs live allocator
- After N cycles of satisfactory behavior → promote to live

## Not in this doc

- **Allocator algorithm internals** —
  [../../../03-services/portfolio-allocator.md](../../../03-services/portfolio-allocator.md)
- **Transfer between venues** — [transfer-rebalance.md](transfer-rebalance.md)
- **Per-strategy sizing within allocated equity** — [../axes/staking-methods.md](../axes/staking-methods.md)
- **Kill switch mechanics** — [risk-gates.md](risk-gates.md) +
  [../../../04-architecture/kill-switch-circuit-breaker.md](../../../04-architecture/kill-switch-circuit-breaker.md)
- **Platform-level allocation** (client-to-client) — out of scope here

## Cross-references

- Service: [../../../03-services/portfolio-allocator.md](../../../03-services/portfolio-allocator.md)
- Capital flow model: [../../../04-architecture/capital-flow-model.md](../../../04-architecture/capital-flow-model.md)
- Capital structure:
  [../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md)
- Stat arb cross-sectional (compares with portfolio allocator):
  [../archetypes/stat-arb-cross-sectional.md](../archetypes/stat-arb-cross-sectional.md)
