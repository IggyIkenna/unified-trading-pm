---
doc_type: codex-ssot
title: Prime Brokers (Meta-Broker Venue Model)
summary:
  "The META_BROKER venue pattern (one endpoint + one wallet, internal SOR routes to child books): two live meta-brokers
  — Unity (sports, 10 child books) and IBKR (TradFi smart router); covers the required adapter shape, fill attribution
  to child books for PBMS, credential model, and meta-level kill switches."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [meta-broker, execution, venue, strategy, tradfi, unity]
related:
  [
    /codex/02-venues/unity-integration.md,
    /codex/02-venues/venue-registry-reference.md,
    /codex/03-services/venue-capability-registry.md,
    /codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md,
  ]
created: 2026-04-17
authoritative_for: [meta-broker venue pattern, prime-broker adapter shape]
referenced_by:
  [
    /codex/02-venues/unity-integration.md,
    /codex/02-venues/venue-registry-reference.md,
    /codex/09-strategy/architecture-v2/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Prime Brokers (Meta-Broker Venue Model)

> **What it is:** The meta-broker (prime-broker) pattern: one endpoint + one wallet that internally routes to multiple
> child books or downstream exchanges. The Unified Trading System has two live meta-brokers — **Unity** for sports (10
> child books) and **IBKR** for TradFi (internal smart router). This doc covers the pattern; Unity specifics are in
> [unity-integration.md](unity-integration.md).

## Why the meta-broker distinction

Without a distinct `venue_type = META_BROKER`, we'd have to:

- Treat each child book as a separate venue in config (10 entries per Unity strategy)
- Model credentials + capital per child book
- Attribute fills assuming per-book accounts when they don't exist

With `META_BROKER`:

- One venue entry in config
- One wallet / one account
- Strategy declares which child books are eligible; meta's internal SOR picks
- Fill reports parsed to attribute per-book for PBMS (but capital is aggregate)

## Required adapter shape

A meta-broker adapter must:

1. **Expose a single venue handle** (e.g., `UNITY`, `IBKR`)
2. **Maintain single wallet/account state** (one margin pool, one cash position)
3. **Accept standard StrategyInstructions** — the meta routes internally
4. **Declare child-book eligibility + preferences** via `unity_child_books_eligible` or `ibkr_routing_preferences` in
   config
5. **Parse fill reports** to extract child-book tag for PBMS attribution
6. **Report venue health** at meta level (underlying child-book health is meta's concern)

## The two live meta-brokers

### Unity

- **Scope:** Sports (Soccer + Tennis + Basketball)
- **Child books:** 10 (8 confirmed + 2 pending)
- **Wallet:** Single Unity wallet, USD share class
- **Connection:** Single TCP connection; Java Feed Connector as sidecar (protocol constraint)
- **SOR:** Unity's internal router picks best child book per bet
- **Commission range:** 0.2% (VX, SharpBet) → 3.0% (BROKER5)
- **Commercial:** $10.8k deposit refundable at $5.3M volume; $2.6k/mo subscription waived at $260k turnover; 1x rollover
- **Status:** Prime venue for sports routing

Full details: [unity-integration.md](unity-integration.md).

### IBKR

- **Scope:** TradFi (equities, options, futures, FX)
- **Child venues:** NYSE, NASDAQ, BATS, ARCA, CME, ICE, LSE (bridged), TSX (bridged), OTC dark pools
- **Wallet:** Single IBKR SMA per client
- **Connection:** TWS API or Client Portal API
- **SOR:** IBKR Smart Router — NBBO across all accessible exchanges
- **Commission:** Tiered; per asset class
- **Status:** Primary TradFi venue

For our stack, IBKR's internal routing decisions are **opaque** — we don't control venue pick within IBKR. We treat IBKR
as `venue = IBKR` always.

## Meta-broker in strategy config

```yaml
venue: UNITY
venue_routing_mode: META_BROKER
unity_child_books_eligible:
  - PINNACLE_VIA_UNITY
  - VX
  - SHARPBET
  - BETFAIR_VIA_UNITY
  - BROKER3
  - BROKER4
  - IBCBET
unity_child_book_preferences:
  preferred_first: [VX, SHARPBET] # lowest commission first
  avoid: [BROKER5] # 3% commission
  deny_on_commission_above_pct: 2.0
```

```yaml
venue: IBKR
venue_routing_mode: META_BROKER
ibkr_routing_preferences:
  primary_route: SMART # IBKR Smart Router
  exchange_priority: [NYSE, NASDAQ, ARCA, BATS]
  dark_pool_allowed: true
  max_route_latency_ms: 50
```

## Attribution of fills

For PBMS:

- Each fill from meta-broker includes a `child_venue_tag` (parsed from meta's fill report)
- PBMS records: `(strategy_instance_id, parent_venue=UNITY, child_venue=VX, price, size)`
- Position state aggregated at parent venue (capital level)
- Child-venue tag used for commission attribution + edge analysis per book

## Credential model

One credential per meta-broker:

- Unity: API key + auth token + TCP certificate
- IBKR: gateway session + client certificate

Internal children don't need separate credentials; meta's SOR handles downstream authentication.

> **Verified NON-finding (UTL/UAC reuse audit, 2026-07-13)**:
> `ibkr-gateway-infra/ibkr_gateway_client/health.py: check_tunnel_health()` is a plain `socket.create_connection`
> TCP-reachability probe on the SSH-tunnelled TWS API port — it verifies the tunnel + IB Gateway are up BEFORE a full
> TWS-protocol connect is attempted, one level below the "meta-level connection health" this doc's Monitoring section
> describes. It is not a retry/backoff call (no `@with_retry` target — a plain connect either succeeds or raises
> `OSError`) and there is no UTL/UAC health-probe primitive it should consolidate onto. Do not re-flag it in a future
> reuse audit. SSOT: `plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md` line 176-179 (verified
> NON-findings list).

## Risk + kill switches

Kill switches operate at meta level:

- `UNITY_PAUSED` kills all Unity strategies regardless of child book
- `IBKR_PAUSED` kills all TradFi strategies

Per-child-book kills (disable VX, enable SharpBet) done via config update — eligibility filter change, not kill switch.

## Venue-account coordination for meta-brokers

- Position aggregation happens at meta level
- Multiple strategies sharing a Unity wallet: coordination layer ensures non-conflicting bet placements
- Reservation mechanism for Unity deposit: strategies don't over-reserve deposit beyond available

## Child-book eligibility vs selection

- **Eligibility** (slow path): which child books are allowed (config)
- **Selection** (fast path): meta's internal SOR picks per bet

Our strategy-service controls the eligibility set; Unity/IBKR's internal engine does the pick. We influence the pick via
preference hints but don't override.

## Future meta-brokers

Potential additions:

- Coinbase Prime (CeFi prime broker; currently not integrated)
- Other prime brokers for FX / fixed income — deferred

If integrated, follow the same `venue_type = META_BROKER` pattern + adapter shape.

## Monitoring

Per meta-broker:

- Per-child-book commission aggregation
- Per-child-book edge capture (P&L attributable to pick)
- Per-child-book rejection rate
- Meta-level connection health
- Subscription/turnover tracking (Unity specific)

UI dashboards tailored per meta-broker.

## Cross-references

- Venue registry: [venue-registry-reference.md](venue-registry-reference.md)
- Unity specifics: [unity-integration.md](unity-integration.md)
- Slow-fast routing split:
  [/codex/04-architecture/slow-fast-routing-split.md](/codex/04-architecture/slow-fast-routing-split.md)
- Venue selection (strategy-facing):
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-selection-split.md)
- Venue-account coordination:
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)

## Not in this doc

- **Unity TCP sidecar + Java Feed Connector implementation** — [unity-integration.md](unity-integration.md) +
  execution-service code
- **IBKR TWS/Client Portal integration** — execution-service/adapters/ibkr/
- **Per-child-book commercial details** — commercial agreements + Unity portal
- **Future prime brokers** — deferred
