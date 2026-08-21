---
doc_type: issue
title:
  "Centralize position reads between strategy-service and execution-service via one DB-backed reader —
  operator architecture direction, 2026-08-21"
summary: >-
  Surfaced answering a question about why execution-venue and position-read-venue are separate, unvalidated
  fields in strategy config (found during a venue-capability-registry audit). Operator's direction: don't
  reconcile the two venue axes — instead centralize position READS through one DB-backed reader in
  strategy-service that both services are forced to use, eliminating the need for strategy<->execution
  position reconciliation entirely. The only remaining reconciliation is (a) venue-subscription lists, and
  (b) each service independently reconciling ITS OWN positions from its own trades against the position
  monitor. Not built — this is architecture direction to scope into buildable todos, not a shipped design.
status: open
nature: design
asset_group: [cefi, defi, tradfi]
stage: [strategy, execution]
repos: [strategy-service, execution-service]
scope: [engineer, admin]
tags: [position, architecture, centralization, operator-direction, db]
related:
  [
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
  ]
created: "2026-08-21"
author: unknown
last_updated: "2026-08-21"
source: operator-request-2026-08-21
parent_epic: security_and_cross_cutting_master
resolved_by:
locked_by:
context_scope:
  [
    strategy-service/strategy_service/position/storage/database.py,
    strategy-service/strategy_service/position/storage/position_store.py,
    strategy-service/strategy_service/position/api/main.py,
  ]
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: strategy_engineering
drift_direction: advance-code
---

# Centralize position reads between strategy-service and execution-service

## Context — how this surfaced

A venue-capability-registry audit (2026-08-21) found strategy-service's execution-venue field
(`VolSurfaceConfig.venue`, `CrossExchangeConfig.venue_a`/`venue_b`, etc.) and its position-read venue
subscriptions (`RiskInstrumentSubscriptions`, `PositionMonitorConfig.position_subscriptions`, etc.) are two
structurally separate, unvalidated axes with real, intentional divergence in places (e.g. `staked_basis.py`'s
LST_AS_MARGIN reads DeFi collateral via subscriptions while executing perp hedges on a different venue). Asked
the operator whether this needs validation or documentation.

## OPERATOR DIRECTION 2026-08-21 (verbatim)

> "why not just centralise position between strategy and execution services via the DB position is kept. a
> central reader in strategy service ensures a strategy is reading its position across all its accounts which
> is safest way to guarantee. execution services is forced to read the same way. so no actual need for
> reconciliation between them just reconciliation of venue subscriptions and they each reconcile their
> positions from trades vs the position monitor."

Translation / what this means architecturally:

1. **One DB-backed position reader, owned by strategy-service** — strategy-service reads a strategy's positions
   across ALL its accounts through ONE central reader, not scattered per-purpose subscription mechanisms.
2. **execution-service is FORCED to read positions the same way** — through the same central reader/DB, not
   its own independent position view. This is the key move that eliminates cross-service position
   reconciliation: if both services read the identical source, there's nothing to reconcile between them.
3. **What reconciliation remains, narrowed to two kinds**:
   - Venue-SUBSCRIPTION reconciliation (are the two services subscribed to consistent venue lists — NOT
     position values).
   - Each service independently reconciles ITS OWN positions-from-trades against the position monitor (a
     trades-vs-holdings self-check per service, not a cross-service position diff).

## What already exists (verify before building — not independently confirmed this session)

`strategy_service/position/storage/{database.py,position_store.py}` — a real DB-backed position store already
exists in strategy-service (confirmed present via grep, contents NOT read this session). `position/api/main.py`
+ `position/api/routes/` expose an API surface. This may already BE (or be close to) the "central reader" the
operator describes — or it may be one of several scattered mechanisms this direction wants collapsed into.
**First real task is to read this existing code and determine how far it already is from the target
architecture**, not assume either "already done" or "must build from scratch."

## Todos

- [ ] [BACKEND] P1. **Audit the current state of `strategy_service/position/storage/{database.py,
      position_store.py}` + `position/api/`** against the operator's target: is this already a real
      cross-account-aggregating central reader? Does execution-service read positions from it today (grep
      execution-service for any call into strategy-service's position API/DB), or does execution-service
      maintain its own independent position view (if so, where, and is IT the thing that should be deleted in
      favor of reading strategy-service's central store)?
- [ ] [BACKEND] P1. **Scope the "forced to read the same way" mechanism** — is this an execution-service code
      change (call strategy-service's position API instead of its own view), a shared library
      (`unified-trading-library`) read path both services import, or something else? Note this workspace's
      hard "NO service<->service dependency" rule (T4/execution-service depends only on UTL/UAC, integrates by
      API contract — `/codex/04-architecture/tier-and-import-architecture.md`) — a direct execution-service ->
      strategy-service API call may conflict with that rule; if so, the shared-library-reading-one-DB shape is
      likely the right one, confirm before building either way.
- [ ] [BACKEND] P2. **Design the venue-subscription reconciliation check** — what does "reconcile venue
      subscriptions" mean concretely: a periodic diff of each service's subscribed-venue list against a
      shared registry, alerting on drift? Scope once todo 1's audit is done.
- [ ] [BACKEND] P2. **Design each service's independent trades-vs-position-monitor reconciliation** — likely
      already partially exists (position monitors + trade ledgers exist in both services); confirm what's real
      today vs. what needs building once todo 1 lands.
- [ ] [REVIEW] P3. Once centralized, revisit the venue-eligibility resolver work
      (`venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md`) — a central position reader may
      change how venue capability should be declared/checked (one source of truth for "what venues does this
      strategy actually hold positions on" becomes available).

## Progress Log

- **2026-08-21** — Filed from an interactive session after the operator gave this architecture direction in
  response to a venue-capability audit question. Not investigated further this session (session/time
  constrained) — todo 1 is the real next step, not yet started.
---
doc_type: issue
title:
  "Centralize position reads between strategy-service and execution-service via one DB-backed reader —
  operator architecture direction, 2026-08-21"
summary: >-
  Surfaced answering a question about why execution-venue and position-read-venue are separate, unvalidated
  fields in strategy config (found during a venue-capability-registry audit). Operator's direction: don't
  reconcile the two venue axes — instead centralize position READS through one DB-backed reader in
  strategy-service that both services are forced to use, eliminating the need for strategy<->execution
  position reconciliation entirely. The only remaining reconciliation is (a) venue-subscription lists, and
  (b) each service independently reconciling ITS OWN positions from its own trades against the position
  monitor. Todo 1 audit complete 2026-08-21: no working central reader exists today — the DB store is
  per-account/per-venue row-level only (no aggregation), the one aggregation mechanism (CrossVenueAggregator)
  is in-memory, unwired to any router, and never fed; execution-service has zero coupling to strategy-service's
  position store and maintains several independent position-tracking modules of its own.
status: open
nature: design
asset_group: [cefi, defi, tradfi]
stage: [strategy, execution]
repos: [strategy-service, execution-service]
scope: [engineer, admin]
tags: [position, architecture, centralization, operator-direction, db]
related:
  [
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
  ]
created: "2026-08-21"
author: unknown
last_updated: "2026-08-21"
source: operator-request-2026-08-21
parent_epic: security_and_cross_cutting_master
resolved_by:
locked_by:
context_scope:
  [
    strategy-service/strategy_service/position/storage/database.py,
    strategy-service/strategy_service/position/storage/position_store.py,
    strategy-service/strategy_service/position/api/main.py,
    strategy-service/strategy_service/position/api/routes/aggregated.py,
    strategy-service/strategy_service/position/core/cross_venue_aggregator.py,
    strategy-service/strategy_service/engine/position_client.py,
  ]
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: strategy_engineering
drift_direction: advance-code
---

# Centralize position reads between strategy-service and execution-service

## Context — how this surfaced

A venue-capability-registry audit (2026-08-21) found strategy-service's execution-venue field
(`VolSurfaceConfig.venue`, `CrossExchangeConfig.venue_a`/`venue_b`, etc.) and its position-read venue
subscriptions (`RiskInstrumentSubscriptions`, `PositionMonitorConfig.position_subscriptions`, etc.) are two
structurally separate, unvalidated axes with real, intentional divergence in places (e.g. `staked_basis.py`'s
LST_AS_MARGIN reads DeFi collateral via subscriptions while executing perp hedges on a different venue). Asked
the operator whether this needs validation or documentation.

## OPERATOR DIRECTION 2026-08-21 (verbatim)

> "why not just centralise position between strategy and execution services via the DB position is kept. a
> central reader in strategy service ensures a strategy is reading its position across all its accounts which
> is safest way to guarantee. execution services is forced to read the same way. so no actual need for
> reconciliation between them just reconciliation of venue subscriptions and they each reconcile their
> positions from trades vs the position monitor."

Translation / what this means architecturally:

1. **One DB-backed position reader, owned by strategy-service** — strategy-service reads a strategy's positions
   across ALL its accounts through ONE central reader, not scattered per-purpose subscription mechanisms.
2. **execution-service is FORCED to read positions the same way** — through the same central reader/DB, not
   its own independent position view. This is the key move that eliminates cross-service position
   reconciliation: if both services read the identical source, there's nothing to reconcile between them.
3. **What reconciliation remains, narrowed to two kinds**:
   - Venue-SUBSCRIPTION reconciliation (are the two services subscribed to consistent venue lists — NOT
     position values).
   - Each service independently reconciles ITS OWN positions-from-trades against the position monitor (a
     trades-vs-holdings self-check per service, not a cross-service position diff).

## Todo 1 audit findings (2026-08-21)

**No working central reader exists today.** Three separate, disconnected mechanisms, none of which does what
the operator described:

1. **`strategy_service/position/storage/{database.py,position_store.py}`** — a real SQLAlchemy DB store
   (`PositionDB`, SQLite dev / Postgres-migratable). `PositionDB.__table_args__` unique key is
   `(client_id, strategy_id, venue, account_id, instrument)` — i.e. rows are **per-account, per-venue, not
   aggregated** (`database.py:84-93`). `PositionStore.get_all_positions()` (`position_store.py:159-186`) can
   filter down to just `strategy_id` (account_id has no filter param) and so CAN return every row across all of
   a strategy's accounts — but it returns the raw un-aggregated `list[PositionRecord]`, never summed. **No
   method in `PositionStore` aggregates/sums across accounts.** This is a real, working row-level store; it is
   not the cross-account-aggregating reader the operator described.

2. **`strategy_service/position/core/cross_venue_aggregator.py`** (`CrossVenueAggregator`, `get_all_aggregated`
   at line 183) — the one component that DOES produce an `AggregatedPosition` shape, but it is **entirely
   in-memory**, updated only via `update_venue_position()` events (line 132) — it does **not read from
   `PositionStore`/the DB at all**. It is a third, disconnected mechanism from the DB store.

3. **`strategy_service/position/api/routes/aggregated.py`** exposes `/aggregated-positions`,
   `/portfolio-view/{client_id}`, `/risk-groups/{client_id}` etc. against that in-memory `CrossVenueAggregator`
   — **but this router is never mounted.** `position/api/main.py::create_app()` (the real app, run via
   `strategy_service.position.api.main:app` per `position/cli/handlers/monitor_handler.py:309`) only includes
   `recon_router`, `nav_snapshot_router`, `risk_router`, `trades_router`, `drift_router`, `treasury_router`,
   `pnl_series_router`, `positions_health_router` — `aggregated.py`'s router is imported nowhere. Additionally,
   `set_aggregator()` (the injection point that would wire a live `CrossVenueAggregator` instance into the
   router module) has **zero call sites in the whole repo** outside its own definition — the aggregator is
   never constructed/wired at startup either. Net effect: `strategy_service/engine/position_client.py`
   (`StrategyPositionClient.get_positions_for_strategy`, used by DeFi strategies to recover `is_deployed` state
   on restart) calls `GET /aggregated-positions` against `http://localhost:8013` — a route that does not exist
   in the running app, so this call always fails and is silently swallowed (`httpx.HTTPError` caught, logs a
   warning, returns `[]`). **Not fixed this session** — wiring `CrossVenueAggregator` to real data requires
   deciding what feeds it (currently nothing does), which is design work beyond this audit's "trivial fix"
   scope, not a one-line wiring gap.

4. **execution-service reads NONE of this.** Grepped execution-service exhaustively for
   `position-balance-monitor`, `strategy_service.position`, `StrategyPositionClient`, port `8013`, and
   `strategy-service` — **zero hits** outside its own unrelated files. execution-service maintains **several
   independent position-tracking modules of its own**: `execution_service/results/position_manager.py` (backtest
   only), `execution_service/services/position_tracker.py`, `execution_service/defi_execution/position_tracker.py`,
   `execution_service/defi_execution/position.py`, `execution_service/engine/live/positions.py`,
   `execution_service/models/position.py`, `execution_service/defi_execution/monitors/family2_position_registry.py`.
   None of these read from or write to strategy-service's `PositionStore`/DB.

**Cross-service integration pattern already established in this codebase** (answers todo 2's "how would
execution-service be forced to read the same way without violating T4's no-service↔service-call rule"):
strategy instructions reach execution-service via the **UTL `EventTransport` facade / event-log spine**
(`unified_trading_library.streaming.event_facade`), not a direct HTTP call — confirmed at
`execution-service/execution_service/engine/strategy_instruction_subscriber.py:13-14`
(`from unified_trading_library.streaming.event_facade import EventTransport` / `read as facade_read`),
consuming `atomic_instruction` envelopes published by strategy-service. `InMemoryTransport` is used for
paper/colocated, Pub/Sub for live — same code path both directions. This is the precedent the "central position
reader" build should follow: **not** a direct execution-service → strategy-service position-API HTTP call
(would violate `/codex/04-architecture/tier-and-import-architecture.md`'s T4 no-service-dependency rule the same
way a reverse call would), but either (a) execution-service reading the **same Postgres DB** strategy-service's
`PositionStore` writes to, via a shared UTL-owned read path/library both services import (not a service call —
a shared-infra dependency, same shape as both services reading GCS/UAC), or (b) strategy-service publishing
position snapshots onto the event-log spine the same way it publishes instructions, with execution-service
subscribing. Not decided here — that's todo 2, unchanged from the original filing.

## Todos

- [x] [BACKEND] P1. **Audit the current state of `strategy_service/position/storage/{database.py,
      position_store.py}` + `position/api/`** against the operator's target — **DONE 2026-08-21, findings
      above.** Answer: not a working cross-account-aggregating central reader (row-level DB store, no
      aggregation method; the one aggregator is in-memory/unwired/unfed). execution-service does not read from
      it — zero coupling, execution-service maintains its own independent position-tracking modules.
- [ ] [BACKEND] P1. **Fix `strategy_service/position/api/main.py::create_app()` to mount `aggregated.py`'s
      router** — code change WRITTEN 2026-08-21 (`app.include_router(aggregated_router)`, imported from
      `strategy_service.position.api.routes.aggregated`) but **NOT SHIPPED**: `quickmerge.sh` in this slot
      (.tabs/4) failed Stage 2 pre-flight — `unified-trading-library` and `unified-api-contracts` (path deps)
      have substantial uncommitted changes that are not this session's work (another concurrent session's WIP
      in the shared slot checkout — streaming/ws + error-code registry files). Per the multi-agent safety rule,
      foreign uncommitted WIP in a shared slot is not touched/committed without confirming it's dead. The edit
      itself is unchanged and still sitting uncommitted in `.tabs/4/strategy-service`; next session picking
      this up should re-run `bash scripts/quickmerge.sh "fix(position-api): mount unmounted aggregated-positions
      router" --agent --files 'strategy_service/position/api/main.py'` once the dep repos are clean (or from a
      clean slot). Before this, `StrategyPositionClient.get_positions_for_strategy`
      (`strategy_service/engine/position_client.py`) calls a route that 404's in production; mounting the
      router alone does NOT make it functional (`CrossVenueAggregator` is still unwired/unfed — callers would
      get a 503 "Cross-venue aggregation not initialized" instead of a silent 404), but it surfaces the real gap
      honestly instead of masking it. Wiring `CrossVenueAggregator`'s data feed was NOT attempted — that's a
      real design call (what feeds it — the DB store? a subscription?) folded into the next todo.
- [ ] [BACKEND] P1. **Design + build the actual DB-backed central reader** (the operator's real ask — neither
      existing mechanism qualifies): add an aggregation method to `PositionStore`
      (`strategy_service/position/storage/position_store.py`) that sums a strategy's positions across ALL its
      `account_id` rows per (client_id, strategy_id, venue, instrument) or per instrument across venues too,
      expose it via a route in `position/api/` that's actually mounted, and decide whether `CrossVenueAggregator`
      (in-memory) is replaced by this DB-backed path or kept as a distinct live cache in front of it. This
      supersedes/absorbs the previous todo 2 ("scope the forced-to-read-the-same-way mechanism") — the
      cross-service pattern to follow is now confirmed (UTL `EventTransport` facade precedent, or a
      shared-DB-read library import — see findings above), not the open question it was before.
- [ ] [BACKEND] P2. **Design the venue-subscription reconciliation check** — what does "reconcile venue
      subscriptions" mean concretely: a periodic diff of each service's subscribed-venue list against a
      shared registry, alerting on drift? Scope once the central reader (previous todo) lands.
- [ ] [BACKEND] P2. **Design each service's independent trades-vs-position-monitor reconciliation** — likely
      already partially exists (position monitors + trade ledgers exist in both services); confirm what's real
      today vs. what needs building once the central reader lands.
- [ ] [REVIEW] P3. Once centralized, revisit the venue-eligibility resolver work
      (`venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md`) — a central position reader may
      change how venue capability should be declared/checked (one source of truth for "what venues does this
      strategy actually hold positions on" becomes available).

## Progress Log

- **2026-08-21** — Filed from an interactive session after the operator gave this architecture direction in
  response to a venue-capability audit question. Not investigated further this session (session/time
  constrained) — todo 1 is the real next step, not yet started.
- **2026-08-21** — Todo 1 audit completed (interactive session, .tabs/4). Read
  `position/storage/{database.py,position_store.py}` in full, `position/api/main.py` + all of
  `position/api/routes/`, `position/core/cross_venue_aggregator.py`, `engine/position_client.py`; grepped
  execution-service exhaustively for any coupling to strategy-service's position store. Findings folded into
  the doc body above; flipped todo 1, added a concrete next-build-step todo and superseded the vague
  "scope the mechanism" todo with a concrete central-reader-build todo now that the cross-service pattern
  (UTL EventTransport facade / shared-DB-read precedent) is confirmed rather than open. Attempted to ship the
  small `aggregated.py` router-mounting fix via quickmerge — blocked by pre-existing dirty `unified-trading-library`
  / `unified-api-contracts` path deps in this shared slot (another session's WIP, not touched); code change left
  uncommitted in `.tabs/4/strategy-service` for a future session to ship once the slot is clean.
