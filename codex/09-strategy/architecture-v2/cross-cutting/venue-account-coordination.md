---
doc_type: codex-ssot
title: "Cross-Cutting: Venue-Account Coordination"
summary:
  "Primitives for multiple strategies sharing one (client, venue, account): PBMS venue-account aggregation
  (sum-of-strategy-views invariant), aggregated venue-account pre-flight (L3 margin sim), atomic cross-strategy
  rebalance, and account locking — unlocks cross-margin / portfolio-margin capital efficiency without
  one-strategy-per-account."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [execution, strategy, risk, cefi, defi]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md,
    ../../../04-architecture/capital-efficiency-patterns.md,
    /codex/09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md,
    ../../../02-venues/unity-integration.md,
  ]
created: 2026-04-17
authoritative_for:
  [
    shared-venue-account coordination primitives (aggregation / venue-account preflight / atomic cross-strategy
    rebalance),
  ]
referenced_by:
  [
    /codex/02-venues/prime-brokers.md,
    /codex/02-venues/unity-integration.md,
    /codex/04-architecture/account-instructions.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/04-architecture/shadow-deployment-pattern.md,
    /codex/04-architecture/slow-fast-routing-split.md,
    /codex/04-architecture/strategy-execution-protocol.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cross-Cutting: Venue-Account Coordination

> **What it is:** The primitives for multiple strategies sharing a single venue account. When two or more strategies
> operate on the same (client, venue, account_id), they can conflict on margin, position, collateral, and pending
> orders. Venue-account coordination adds three primitives — **aggregation**, **pre-flight**, **atomic rebalance** —
> that keep shared-account behavior safe and efficient without forcing one-strategy-per-account.
>
> **Why this matters:** One-strategy-per-account is a common guard rail but it wastes capital. With coordination
> primitives, we can run directional + basis + MM + carry on the SAME venue account with netted margin and
> cross-strategy pre-flight, unlocking venue-level capital efficiency (Binance cross-margin, Deribit portfolio margin,
> IBKR reg-T netting).

## The shared-account scenario

Without coordination, two strategies on the same account:

```
Strategy A (ML directional BTC) → emits BUY 5 BTC
Strategy B (basis BTC-perp)     → emits BUY 5 BTC spot + SELL 5 BTC perp
    → combined: BUY 10 BTC spot + SELL 5 BTC perp
    → account has margin for 3 BTC cross-margin → 7 BTC over limit
    → one strategy or both get rejected at venue
    → P&L attribution tangled
```

With coordination:

```
Strategy A + B instructions flow through coordination layer
    ↓
Aggregate target state: +10 BTC spot + -5 BTC perp (net delta +5 BTC)
    ↓
Margin simulation: 5 BTC cross-margin fits within limit
    ↓
Pre-flight passes; both instructions proceed
    ↓
Post-fill: attribution reconciles per-strategy positions
```

## Primitive 1: Venue-account aggregation (PBMS)

PBMS maintains two orthogonal projections:

- **Strategy-instance view**: positions per strategy_instance_id, conceptual positions
- **Venue-account view**: actual positions at the venue, summed across strategies sharing the account

```
Venue-account view (PBMS):
(client_A, BINANCE, "account_1")
  BTC/USDT spot:   actual_balance = 12 BTC
  BTC-PERP:        actual_position = -5 BTC
  margin_used:     $60_000
  margin_available:$40_000

Strategy-instance views (PBMS):
ML_DIRECTIONAL_CONTINUOUS@binance-btc-5m-usdt-prod:
  BTC/USDT spot:   logical_position = 5 BTC    (strategy A's share)
CARRY_BASIS_PERP@binance-binance-btc-usdt-prod:
  BTC/USDT spot:   logical_position = 7 BTC    (strategy B's share)
  BTC-PERP:        logical_position = -5 BTC

Sum of strategy views === venue-account view  (invariant)
```

PBMS reconciles any drift; emits `VENUE_ACCOUNT_STRATEGY_SUM_DRIFT` if sum ≠ account.

## Primitive 2: Venue-account pre-flight

When an instruction arrives at execution-service Layer 3, pre-flight simulates the instruction against the current
venue-account state (not just the emitting strategy's view):

```python
def venue_account_preflight(instruction):
    va = pbms.venue_account_state(instruction.client_id, instruction.target_venue)
    simulated = va.apply(instruction)   # margin sim with haircuts, LTV, portfolio margin
    if simulated.margin_used > va.margin_limit:
        return Reject("insufficient cross-margin given other strategies' positions")
    if simulated.position_concentration > LIMITS.venue:
        return Reject("venue concentration")
    return Approve()
```

This is Layer 3 of the 4-layer risk model ([risk-gates.md](risk-gates.md)), but specifically using **aggregated**
venue-account state rather than single-strategy state.

Margin simulation accounts for:

- Cross-margin netting (Binance)
- Portfolio margin rules (Deribit)
- Reg-T netting (IBKR)
- DeFi LTV with haircuts (Aave stETH 75% LTV, etc.)
- Option greeks netting (Deribit portfolio margin greeks)

## Primitive 3: Atomic cross-strategy rebalance

When two strategies simultaneously want to adjust positions that share an account, coordination batches them into a
single atomic rebalance to minimize round-trip margin peaks:

```
Strategy A wants:
  BTC spot: 5 → 8   (+3)
Strategy B wants:
  BTC spot: 7 → 4   (-3)
  BTC-PERP: -5 → -2 (+3)

Without coordination:
  A fires first: spot goes 12 → 15, margin peak
  B fires second: spot goes 15 → 12, perp goes -5 → -2

With coordination:
  Batched instruction:
    net spot: 12 → 12 (no change)
    net perp: -5 → -2 (+3)
  One tx fires: perp BUY 3
  Attribution post-fill: allocated +3 spot to A, -3 spot to B, +3 perp to B
```

**Invariant:** atomic rebalance must preserve per-strategy target state AND minimize venue-level churn.

## Position attribution post-fill

When a fill arrives for a shared account, the coordination layer attributes to specific strategies per the instruction
that triggered it:

- Each StrategyInstruction carries `strategy_instance_id`
- Venue fills are tagged with the originating instruction's `instruction_id`
- PBMS matches fill → instruction → strategy_instance
- Strategy-instance-view positions update accordingly
- Venue-account-view updates mechanically from fills

## Capital efficiency patterns unlocked

| Pattern                          | Benefit                                                                  | Requirement                      |
| -------------------------------- | ------------------------------------------------------------------------ | -------------------------------- |
| Basis + directional same account | Margin netting; basis short-leg contributes margin relief to directional | Cross-margin or portfolio margin |
| Vol + delta-hedge same account   | Greek netting; hedge reduces portfolio margin requirement                | Deribit-style portfolio margin   |
| Multi-strategy market-making     | Shared inventory; one strategy's long hedges another's short             | Careful attribution              |
| Option spread + outright         | Box/butterfly structures consume less margin than legs separately        | Portfolio margin                 |
| DeFi LP + LST borrow             | LP earns fees while collateral borrowed for leverage loop                | LTV management                   |

Full patterns:
[../../../04-architecture/capital-efficiency-patterns.md](../../../04-architecture/capital-efficiency-patterns.md).

## Account locking for critical sections

For certain operations (emergency close, margin top-up), coordination acquires an **account lock** blocking all strategy
instructions on that account:

```
acquire_lock(client_A, BINANCE, "account_1")
try:
  emergency_close_all_positions()
  withdraw_surplus()
finally:
  release_lock(...)
```

Strategies emitting during lock see `VENUE_ACCOUNT_LOCKED` and queue instructions. Lock lifetime bounded (e.g., 60s max)
with auto-release on timeout.

## Multi-account per client-venue

A client can have multiple accounts on the same venue (subaccounts, master account):

- `(client_A, BINANCE, "binance-main")`
- `(client_A, BINANCE, "binance-sub-hft")`
- `(client_A, BINANCE, "binance-sub-options")`

Each account is an independent coordination scope. Strategies are assigned to specific accounts via config.
Cross-account moves via `TRANSFER` (internal subaccount).

## Meta-broker coordination

For Unity (META_BROKER) the account is Unity-master; child books are internal. Coordination happens at:

- Unity-master level (PBMS venue-account = Unity wallet)
- Unity's internal SOR handles child-book routing
- Child-book-level attribution in PBMS requires parsing Unity's fill reports

## Kill-switch interaction

When one strategy on a shared account is killed:

- Kill affects that strategy's ability to add new positions
- Does NOT force close the other strategies' positions
- Does NOT release margin held by the killed strategy's positions until explicit close
- Operator may issue `AccountInstruction.CLOSE_ALL_FOR_STRATEGY` or `CLOSE_ALL_FOR_ACCOUNT` per scope

See [risk-gates.md](risk-gates.md) +
[../../../04-architecture/kill-switch-circuit-breaker.md](../../../04-architecture/kill-switch-circuit-breaker.md).

## Not in this doc

- **Single-strategy-per-account scenarios** — trivially handled by strategy-instance view; no coordination needed
- **Cross-client coordination** — doesn't exist; client isolation forbids it
  ([capital-client-isolation.md](capital-client-isolation.md))
- **Specific margin formulas per venue** — venue registry +
  [../../../04-architecture/capital-efficiency-patterns.md](../../../04-architecture/capital-efficiency-patterns.md)
- **Unity child-book internals** — [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- **PBMS schema internals** — PBMS service docs

## Cross-references

- Capital efficiency patterns:
  [../../../04-architecture/capital-efficiency-patterns.md](../../../04-architecture/capital-efficiency-patterns.md)
- Risk gates (Layer 3 pre-flight): [risk-gates.md](risk-gates.md)
- Capital client isolation: [capital-client-isolation.md](capital-client-isolation.md)
- Venue registry: [../../../02-venues/venue-registry-reference.md](../../../02-venues/venue-registry-reference.md)
- Unity: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
