---
doc_type: codex-ssot
title: Slow-Fast Routing Split (Architecture View)
summary:
  Architectural justification for splitting venue routing — slow-path eligibility (strategy-service config,
  human-approved) vs fast-path per-order SOR (execution-service, ms); the StrategyInstruction contract, meta-broker
  case, forbidden bypasses.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: [execution, strategy, mtds, ssot]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md,
    /codex/04-architecture/execution-policy.md,
    /codex/02-venues/venue-registry-reference.md,
  ]
created: 2026-04-17
authoritative_for: [slow-fast venue-routing split architecture (strategy eligibility vs execution SOR)]
referenced_by:
  [
    /codex/02-venues/prime-brokers.md,
    /codex/03-services/venue-capability-registry.md,
    /codex/04-architecture/strategy-execution-protocol.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Slow-Fast Routing Split (Architecture View)

> **What it is:** The architectural justification and contract for splitting venue routing into two services —
> slow-moving eligibility (strategy-service) + fast-moving SOR (execution-service). Companion to
> [/codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md)
> which covers the strategy-facing perspective.

## The core split

```
┌────────────────────────────────────────────────────────────────┐
│  SLOW PATH — STRATEGY CONFIG (change = new config version)     │
│  ───────────────────────────────────────────────────────────── │
│  • Eligible venue set                                          │
│  • Venue constraints (max_notional, min_liquidity, fee tier)   │
│  • Child-book preferences (META_BROKER)                        │
│  • Chain eligibility (DeFi)                                    │
│  • Share-class compatibility                                   │
│  • Pre-funding policy                                          │
│  • Credential availability (derived, gating)                   │
│  Cadence: monthly/quarterly; review + approve per change       │
│  Service: strategy-service (config registry)                   │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼  StrategyInstruction emitted
┌────────────────────────────────────────────────────────────────┐
│  FAST PATH — EXECUTION-SERVICE PER-ORDER (milliseconds)        │
│  ───────────────────────────────────────────────────────────── │
│  • Best quote (price + depth) across eligible venues           │
│  • Net cost (fees + slippage + gas)                            │
│  • Real-time liquidity                                         │
│  • Venue health + latency                                      │
│  • Rate-limit headroom                                         │
│  • MEV mode (DeFi)                                             │
│  • Venue-account margin + balance (PBMS)                       │
│  Cadence: per instruction (ms); not audit-reviewed             │
│  Service: execution-service (SOR + pre-flight)                 │
└────────────────────────────────────────────────────────────────┘
```

## Why split architecturally

### Different change velocity

- **Eligibility** changes monthly: new venue onboarding, compliance approval, credential provisioning
- **SOR picks** change per-millisecond: each quote update, each latency blip, each margin change

Collapsing into one service conflates two rates of change. Splitting lets each evolve on its own cadence.

### Different authorities

- **Eligibility** requires human approval, legal sign-off, compliance checks (onboarding a new venue affects client
  obligations)
- **SOR** requires only real-time data (picking OKX vs Binance for one order doesn't require legal approval)

Splitting isolates human-review-required changes from automated routing.

### Different blast radius

- **Bad eligibility** = fund flows somewhere unauthorized (catastrophic)
- **Bad SOR pick** = loses a few bps on one order (minor)

Splitting lets different fail-safes apply:

- Eligibility has PR review, change approval, dry-run validation
- SOR has runtime circuit breakers, fallback cascades, quote-freshness checks

### Different data sources

- **Eligibility** uses slow-moving artifacts: config registry, credential store, venue capability registry, compliance
  matrix
- **SOR** uses fast-moving data: MTDS live feed, PBMS real-time balance, execution-service health tables

Shared service would couple these unnecessarily.

### Different ownership

- **Eligibility** owned by strategy-service + platform onboarding
- **SOR** owned by execution-service + venue adapters

Clean service boundaries match team boundaries.

## Contract between slow and fast paths

Strategy-service emits `StrategyInstruction` with:

```
eligible_venues: [BINANCE, OKX, BYBIT]
venue_constraints: {
  BINANCE: {max_notional_usd: 500_000, min_liquidity: 100_000, fee_tier: VIP_3},
  OKX: {max_notional_usd: 300_000, min_liquidity: 50_000, fee_tier: VIP_1},
  BYBIT: {max_notional_usd: 200_000, min_liquidity: 30_000, fee_tier: VIP_0},
}
venue_routing_mode: SOR_AT_EXECUTION
```

Execution-service honors:

- Only picks from `eligible_venues`
- Respects `venue_constraints` (skip if violation)
- Runs SOR among remaining candidates
- Applies pre-flight (balance, margin, credential, health)
- Picks best

## When the strategy names a specific venue

For `STRATEGY_PICKED` mode, strategy emits `target_venue` directly:

```
action: TRADE
target_instrument: "BINANCE:SPOT:BTC/USDT"
target_venue: BINANCE
```

Execution doesn't SOR; it tries the named venue. Falls back ONLY if explicit `fallback_venues` declared.

Used when venues are non-fungible (perps with different funding, sports lines on specific books, options with different
strikes).

## Meta-broker special case

When venue is a `META_BROKER` (Unity), strategy emits one instruction; Unity's internal SOR picks the child book.
Execution-service:

- Submits to Unity master endpoint
- Unity's own routing engine picks PINNACLE_VIA_UNITY / VX / SHARPBET / etc. per its rules
- Fill report may include child-book attribution (for PBMS)

Strategy declares `unity_child_books_eligible` + `unity_child_book_preferences` at slow path; Unity's fast path uses
these as hints.

## Slow-fast interaction failures

| Failure                                         | Type                            | Handling                                                  |
| ----------------------------------------------- | ------------------------------- | --------------------------------------------------------- |
| Config lists BINANCE but credential revoked     | Eligibility vs runtime mismatch | Execution skips BINANCE; emits alert                      |
| Config lists venue that adapter doesn't support | Eligibility vs code mismatch    | Startup validator rejects config                          |
| SOR picks venue but margin simulation rejects   | Fast-path reject                | Execution falls through to next eligible                  |
| All eligible venues fail pre-flight             | Hard reject                     | INSTRUCTION_REJECTED_EXECUTION; strategy sees and decides |
| Stale quote (> threshold) on every venue        | Fast-path reject                | Wait N ms and retry; else timeout                         |

## Decision record table

At each decision point, execution-service emits an audit record:

```
instruction_id: abc123
sor_decision_record:
  candidate_venues:
    - venue: BINANCE
      picked: false
      reason_skipped: "insufficient margin in cross-margin simulation"
    - venue: OKX
      picked: true
      quote: {bid: 67850, ask: 67855, depth_usd: 500_000}
      net_cost_bps: 2.1
    - venue: BYBIT
      picked: false
      reason_skipped: "BYBIT venue health DEGRADED (>500ms avg latency last 60s)"
  picked_venue: OKX
  tie_breaker: N/A
```

Queryable for audit + post-mortem.

## Bypassing the split (forbidden)

Anti-patterns:

- **Strategy hardcodes venue per instruction when config says SOR_AT_EXECUTION** — violates the axis contract
- **Execution picks a non-eligible venue** — violates the eligibility contract
- **SOR mutates its ranking by consulting strategy internals** — violates separation (SOR is stateless by-instruction)
- **Strategy emits per-millisecond venue changes** — that's SOR work; do it there

## Registry lookups

Eligibility resolution:

```
strategy config → eligible_venues (literal list)
               → venue_registry.get(each) for capability check
               → credential_manager.has(client, venue) for gating
               → filtered final list
```

SOR resolution:

```
for each eligible venue:
  quote = mtds.live_quote(venue, instrument, ttl_ms=100)
  health = venue_health.get(venue)
  balance = pbms.venue_account_balance(client, venue)
  net_cost = cost_model.eval(venue, size, fee_tier)
  score = (quote.price, quote.depth, net_cost, health, balance)
pick max
```

## Cross-references

- Strategy-facing perspective:
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md)
- Venue eligibility axis:
  [/codex/09-strategy/architecture-v2/axes/venue-eligibility.md](/codex/09-strategy/architecture-v2/axes/venue-eligibility.md)
- Execution policies: [execution-policy.md](execution-policy.md)
- Venue-account coordination:
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
- Venue registry: [/codex/02-venues/venue-registry-reference.md](/codex/02-venues/venue-registry-reference.md)

## Not in this doc

- **Per-venue adapter mechanics** — execution-service/adapters/
- **Quote normalization** — market-tick-data-service
- **Venue health checks** — execution-service internal
- **Credential rotation** — ops
- **Cost-model internals** — cost_model artifact + execution-service
