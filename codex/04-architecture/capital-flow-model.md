---
doc_type: codex-ssot
title: Capital Flow Model
summary:
  Capital flow at 3 scopes (client / strategy / venue) via one idempotent "target X at Y = Z" event-driven
  reconciliation primitive; one service owns each scope (platform-allocator / portfolio-allocator / transfer-rebalance)
  with no scope leakage; 7 transfer types.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [capital, execution, strategy, reconciliation, defi, cefi]
related:
  [
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
  ]
created: 2026-04-17
authoritative_for: [three-scope capital-flow reconciliation model]
referenced_by:
  [
    /codex/03-services/portfolio-allocator.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/04-architecture/share-class-architecture.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md,
    /codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md,
  ]
owner:
last_reviewed: 2026-05-13
code_refs:
---

# Capital Flow Model

> **What it is:** Capital moves at three scopes — venue, strategy, client — and all three use the SAME event-driven
> "target X at Y = Z" reconciliation primitive. One mental model; one code pattern; three services own the three scopes.

## Three scopes

```
┌─────────────────────────────────────────────────────────────────┐
│  CLIENT SCOPE  (platform-level allocator — future, out of v1)   │
│  ─────────────────────────────────────────────────────────────  │
│  Moves capital between clients / legal entities                 │
│  Trigger: sales, compliance, onboarding, offboarding            │
│  Mechanism: platform allocator emits client-level directives    │
│  Invariant: cross-client operations require human + compliance  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (client equity budget)
┌─────────────────────────────────────────────────────────────────┐
│  STRATEGY SCOPE  (portfolio-allocator-service)                  │
│  ─────────────────────────────────────────────────────────────  │
│  Moves capital between strategies within one client             │
│  Trigger: allocator cadence, PnL changes, kill switches         │
│  Mechanism: AllocationDirective events → strategies adapt       │
│  Per-client allocator instance with one archetype               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (strategy equity budget)
┌─────────────────────────────────────────────────────────────────┐
│  VENUE SCOPE  (transfer-rebalance-service)                      │
│  ─────────────────────────────────────────────────────────────  │
│  Moves capital between venues within one strategy's eligible    │
│  venue set                                                       │
│  Trigger: drift from allocation policy, scheduled cadence       │
│  Mechanism: TRANSFER / BRIDGE StrategyInstructions              │
│  7 transfer types (INTERNAL_SUBACCOUNT, CEX_WITHDRAWAL_DEPOSIT, │
│  ON_CHAIN_TRANSFER, BRIDGE, WRAP_UNWRAP, UNITY_WALLET_OP,       │
│  IBKR_FUND_MOVE)                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## The unified primitive: "target X at Y = Z"

At every scope, the actor emits a **target** at a **destination** with a **quantity**. Receiving actor reconciles.

### Venue-scope example

```yaml
# Transfer/rebalance emits:
action: TRANSFER
asset: USDT
venue_from: BINANCE
venue_to: OKX
target_balance_at_destination: 500_000
```

Destination state eventually matches target.

### Strategy-scope example

```yaml
# Portfolio Allocator emits:
AllocationDirective:
  client_id: client_A_fund
  directives:
    - strategy_instance_id: ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-5m-usdt-prod
      target_equity: 2_500_000
    - strategy_instance_id: CARRY_BASIS_PERP@uniswap-hyperliquid-eth-usdt-prod
      target_equity: 1_500_000
```

Strategy reconciles by rescaling internal positions proportionally.

### Client-scope example (conceptual, not v1)

```yaml
# Platform allocator emits (future):
ClientDirective:
  client_id: client_A_fund
  target_platform_equity: 10_000_000
  subject_to: compliance_ok
```

Client moves capital in/out via custody-model mechanics.

## Idempotency at every scope

All three scopes share idempotent semantics:

- Instructions are content-hashed (`instruction_id`)
- Re-emitting same id is a no-op
- Re-emitting new id with same target = no-op if reconciled
- Target state doesn't accumulate; it replaces

## Event-driven reconciliation

Each scope has:

- **Emitter**: allocator, strategy, transfer-service (depending on scope)
- **Reconciler**: strategy, transfer-service, venue adapter
- **Observer**: PBMS (tracks actual state)

Flow:

```
Emitter → [instruction event] → Reconciler
Reconciler → venue operation → Venue
Venue → [fill / ack] → PBMS
PBMS → [state update] → Reconciler (loop closed)
```

## Per-scope services

| Scope    | Service                     | Emits                               | Reconciles                               |
| -------- | --------------------------- | ----------------------------------- | ---------------------------------------- |
| Client   | platform-allocator (future) | ClientDirective                     | client-onboarding / client-account       |
| Strategy | portfolio-allocator         | AllocationDirective                 | strategy-service (reshapes per strategy) |
| Venue    | transfer-rebalance          | TRANSFER/BRIDGE StrategyInstruction | execution-service venue adapters         |

Each service owns ONE scope. No scope leakage. A strategy never moves capital between strategies (would require
allocator role); an allocator never moves capital between venues (would require transfer-rebalance role).

## Cross-scope interactions

Allocator emits strategy-scope directive:

```
AllocationDirective: raise strategy A from $1M to $1.5M
```

Strategy A:

- Updates internal equity
- Computes new target positions (scale 1.5×)
- Needs capital at eligible venues

If needed, strategy emits venue-scope rebalance:

```
TRANSFER: move $500k USDT from ops-reserve-venue to Binance
```

Transfer-rebalance executes, confirms. Strategy proceeds with new positions.

## Capital efficiency patterns

Running multiple strategies on the same venue account enables:

| Pattern                            | Scope interaction                                                     |
| ---------------------------------- | --------------------------------------------------------------------- |
| Cross-margin basis + directional   | Venue scope: one venue account; venue-account coordination primitives |
| Portfolio margin vol + directional | Venue scope: Deribit portfolio margin; shared account                 |
| DeFi LP + borrow                   | Same-chain multiple protocols; on-chain atomic composites             |
| Unity across books                 | Meta-broker single wallet; child books internal to Unity              |

See [capital-efficiency-patterns.md](capital-efficiency-patterns.md).

## Per-category custody × capital flow

Capital flow mechanics differ by custody model:

| Custody            | Client-scope                      | Strategy-scope                 | Venue-scope                                   |
| ------------------ | --------------------------------- | ------------------------------ | --------------------------------------------- |
| CeFi SMA           | Client deposits/withdraws via CEX | Allocator within client        | INTERNAL_SUBACCOUNT + CEX_WITHDRAWAL_DEPOSIT  |
| CeFi fund (future) | Fund-level deposits               | Allocator within fund          | Any CEX mechanism                             |
| DeFi client wallet | Copper/Fireblocks flows           | Allocator within client wallet | ON_CHAIN_TRANSFER + BRIDGE (client-co-signed) |
| DeFi firm          | Firm treasury ops                 | Allocator within firm capital  | ON_CHAIN_TRANSFER + BRIDGE                    |
| Sports Unity pool  | Firm Unity deposit/withdraw       | Allocator                      | UNITY_WALLET_OP                               |
| Sports direct      | Per-book deposit/withdraw         | Allocator                      | Per-book APIs                                 |
| TradFi IBKR        | Client funds IBKR                 | Allocator                      | IBKR_FUND_MOVE                                |

See [capital-structure-and-regulatory.md](capital-structure-and-regulatory.md).

## Reporting rollup

Capital flow data rolls up:

```
Fill (per strategy instance, per venue)
  → Strategy instance P&L (per share class)
    → Strategy instance NAV
      → Client NAV (allocator-aware, cross-share-class to reporting currency)
        → Firm NAV (platform-level)
```

## Audit

Every capital movement logged with:

- Scope
- Initiating service
- Emitting user / system / schedule
- Source + destination
- Asset + amount
- Cost (gas, fees, bridge)
- Target ack / reconciliation timestamp

Queryable per client, per strategy, per venue for compliance.

## Failure modes

| Scope    | Failure mode                           | Recovery                                             |
| -------- | -------------------------------------- | ---------------------------------------------------- |
| Venue    | Bridge hang                            | Monitor + manual; transfer-type-router handles retry |
| Venue    | Gas insufficient                       | Pre-flight gas top-up                                |
| Strategy | Directive violates strategy self-limit | Reject; allocator re-plans                           |
| Strategy | Directive moves to zero (retiring)     | Strategy unwinds; releases venue capital             |
| Client   | Client not onboarded                   | Rejected at platform boundary                        |

Full recovery matrix: [autonomous-recovery-matrix.md](autonomous-recovery-matrix.md).

## Cross-references

- Transfer/rebalance:
  [/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md](/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md)
- Portfolio allocator:
  [/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md](/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md)
- Capital efficiency: [capital-efficiency-patterns.md](capital-efficiency-patterns.md)
- Capital structure + regulatory: [capital-structure-and-regulatory.md](capital-structure-and-regulatory.md)
- Autonomous recovery: [autonomous-recovery-matrix.md](autonomous-recovery-matrix.md)
- Strategy-execution protocol: [strategy-execution-protocol.md](strategy-execution-protocol.md)

## Not in this doc

- **Client onboarding flow** — [capital-structure-and-regulatory.md](capital-structure-and-regulatory.md)
- **Platform-allocator design** — future (v2 of platform)
- **Per-bridge selection details** —
  [/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md](/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md)
- **Per-allocator archetype internals** —
  [/codex/03-services/portfolio-allocator.md](/codex/03-services/portfolio-allocator.md)
- **Accounting / NAV calc** — PBMS + finance-reporting
