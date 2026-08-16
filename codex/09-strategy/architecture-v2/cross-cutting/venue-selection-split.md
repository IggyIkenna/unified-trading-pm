---
doc_type: codex-ssot
title: "Cross-Cutting: Venue Selection (Slow-Path Eligibility + Fast-Path SOR)"
summary:
  "Venue routing split: slow-moving eligibility (strategy config `eligible_venues` + constraints) vs fast-moving
  per-order SOR in execution-service; three routing modes SOR_AT_EXECUTION / STRATEGY_PICKED / META_BROKER; SOR algos
  (BEST_QUOTE_NET, BEST_FUNDING_NET, MEV_PROTECTED_ROUTE, …) are artifact-versioned."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [execution, strategy, venue-selection, cefi, defi, mev]
related:
  [
    ../axes/venue-eligibility.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
    ../../../04-architecture/slow-fast-routing-split.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md,
    /codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md,
  ]
created: 2026-04-17
authoritative_for:
  [venue-selection routing-mode catalog (SOR_AT_EXECUTION / STRATEGY_PICKED / META_BROKER + per-order SOR algo table)]
referenced_by:
  [
    /codex/02-venues/prime-brokers.md,
    /codex/04-architecture/slow-fast-routing-split.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
    /codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cross-Cutting: Venue Selection (Slow-Path Eligibility + Fast-Path SOR)

> **What it is:** Venue routing is split in two. _Eligibility_ is a slow-moving strategy-config concern. _Selection_ at
> order-submission time is a fast-moving execution-service concern. Never collapsed into one.

## The split

```
┌────────────────────────────────────────────────────────────────┐
│  STRATEGY CONFIG (slow-moving, change = new config version)    │
│  ───────────────────────────────────────────────────────────── │
│  eligible_venues: [...]                                        │
│  venue_constraints:                                            │
│    BINANCE: {max_notional_usd, min_liquidity, fee_tier}        │
│    ...                                                         │
│  venue_routing_mode: SOR_AT_EXECUTION | STRATEGY_PICKED |      │
│                      META_BROKER                               │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼  StrategyInstruction emitted
┌────────────────────────────────────────────────────────────────┐
│  EXECUTION-SERVICE PER-ORDER (fast-moving, milliseconds)       │
│  ───────────────────────────────────────────────────────────── │
│  • SOR among eligible_venues picks best venue NOW              │
│    - best quote (price + size)                                 │
│    - net cost (fees + taker/maker + gas + slippage)            │
│    - venue health (latency, rate-limit headroom)               │
│    - MEV protection mode for DeFi                              │
│    - real-time liquidity depth                                 │
│  • For ATOMIC multi-leg, check leg-venue coordination          │
│  • For META_BROKER, Unity's internal SOR picks child book      │
└────────────────────────────────────────────────────────────────┘
```

## Three routing modes

### `SOR_AT_EXECUTION`

Strategy lists all eligible venues; execution SOR picks per order.

- **Applies to**: fungible assets with SOR (crypto spot across CEXes, DEX swaps)
- **Pre-funding**: strategy (or ops) pre-funds each eligible venue with some allocation
- **Rebalance**: on schedule, transfer/rebalance service equalizes pre-funding
- **Example**: Binance + OKX + Bybit BTC/USDT spot — SOR picks best price per order

```yaml
venue_routing_mode: SOR_AT_EXECUTION
eligible_venues: [BINANCE, OKX, BYBIT]
prefund_policy:
  mode: EQUAL_WEIGHT # or PRO_RATA_VOLUME, MANUAL
  rebalance_cadence: DAILY
  rebalance_threshold_pct: 0.15
```

### `STRATEGY_PICKED`

Strategy names the specific venue per instruction at emission time; execution does NOT SOR.

- **Applies to**: non-fungible opportunities (perps with different funding rates, options with different strikes, sports
  lines on specific books)
- **Venue swap**: explicit close-on-A + open-on-B instructions
- **Example**: basis perp arb where funding on Binance is +0.03% and on OKX is -0.01% — strategy picks the venue per
  opportunity

```yaml
venue_routing_mode: STRATEGY_PICKED
eligible_venues: [BINANCE, OKX, HYPERLIQUID, DERIBIT]
# strategy emits: instruction.target_venue = "OKX"  per StrategyInstruction
```

### `META_BROKER`

Venue is a meta-broker (Unity) which itself routes among its children.

- **Applies to**: Unity (10 child books), future IBKR aggregator if treated as meta
- **Strategy declares eligible child books** — but child-venue selection happens inside the meta-broker per venue's own
  SOR
- **Example**: Unity sports routing where Unity picks PINNACLE_VIA_UNITY vs VX vs SHARPBET per bet

```yaml
venue_routing_mode: META_BROKER
venue: UNITY
unity_child_books_eligible: [PINNACLE_VIA_UNITY, VX, SHARPBET, BETFAIR_VIA_UNITY]
unity_child_book_preferences:
  preferred_first: [VX, SHARPBET] # lowest commission first
  avoid: [BROKER5] # 3% commission
```

## Why the split matters

1. **Different cadence** — eligibility changes monthly (new venue approved); SOR changes per-millisecond (quote update).
   A single routing system would conflate two rates of change.
2. **Different scope of truth** — eligibility requires human approval, credential setup, compliance checks. SOR requires
   only real-time quotes and venue health. Don't need compliance review to react to a quote change.
3. **Different blast radius** — bad SOR pick loses bps on one order; bad eligibility lets funds flow somewhere
   unauthorized. Fail-safes differ.
4. **Different ownership** — strategy-service owns eligibility; execution-service owns SOR. Clean service boundary.

## Interaction with venue-account balances

At execution time, SOR filters on:

- Eligible venue set (from config)
- Current quote (from real-time feed)
- **Current venue-account balance + margin available** (from PBMS)
- Credential validity (from Secret Manager)
- Venue health (from MTDS adapter state)
- Rate-limit headroom (from local execution-service counters)

A venue can be eligible but unselectable right now (no balance, stale credential, venue down). Execution skips and tries
next.

If no eligible venue can fulfill, execution emits `ORDER_REJECTED_EXECUTION`. Strategy sees rejection; optional fallback
behavior per config.

## SOR algorithms in execution-service

Registered execution algos that do SOR:

| Algo                  | Applies when           | Picks venue by                                          |
| --------------------- | ---------------------- | ------------------------------------------------------- |
| `BEST_QUOTE_NET`      | Spot TRADE on fungible | net_price = quote ± fees ± est_slippage                 |
| `BEST_DEPTH_NET`      | Large-size TRADE       | depth-adjusted net price                                |
| `BEST_FUNDING_NET`    | Perp carry TRADE       | funding rate ± fees, persistence-weighted               |
| `MEV_PROTECTED_ROUTE` | DeFi SWAP              | route via private RPC + expected execution price        |
| `LEAST_GAS_FIRST`     | DeFi SWAP (small)      | chain + DEX with lowest gas for size                    |
| `ATOMIC_MULTI_LEG`    | ATOMIC across legs     | venue supporting native atomic                          |
| `LEADER_HEDGE`        | Cross-venue legged     | one leg leads on preferred venue; hedge on counterparty |

All algos are artifact-versioned (see [execution-policies.md](execution-policies.md)).

## Configuration of venue order preferences

Strategies can express ordinal preference via config:

```yaml
venue_preferences:
  order: [BINANCE, OKX, BYBIT] # try in order; fallback cascades
  tie_breaker: LOWEST_NET_COST
  sticky_window_ms: 500 # don't re-SOR for 500ms after pick (reduce noise)
```

## Not in this doc

- **Venue set itself** — [../axes/venue-eligibility.md](../axes/venue-eligibility.md)
- **Unity child book details** — [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- **Venue onboarding / approval** — ops/compliance
- **Credential rotation** — ops +
  [../../../04-architecture/capital-structure-and-regulatory.md](../../../04-architecture/capital-structure-and-regulatory.md)
- **MEV protection specifics** — [mev-protection.md](mev-protection.md)
- **Rate limit management internals** — execution-service implementation

## Cross-references

- Venue eligibility axis: [../axes/venue-eligibility.md](../axes/venue-eligibility.md)
- Execution policies: [execution-policies.md](execution-policies.md)
- Slow-fast routing split architecture:
  [../../../04-architecture/slow-fast-routing-split.md](../../../04-architecture/slow-fast-routing-split.md)
- Venue-account coordination: [venue-account-coordination.md](venue-account-coordination.md)
