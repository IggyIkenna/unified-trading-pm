---
doc_type: plan
title: Venue websocket resilience — per-venue ws-protocol registry, stale-feed rotation, exhaustive error-code mapping
summary: >-
  Per-venue websocket resilience end to end — (1) a new ws-protocol axis on the UAC venue-capability registry
  (ping/pong, forced-disconnect windows, listen-key refresh, duplicate-subscription feasibility, REST gap-backfill
  endpoints), researched from every venue's public API docs; (2) an exhaustive per-venue error-code registry (every
  published code individually) wired into classify_venue_error() and every consumer — executes
  system_readiness_master W14's "every venue error code understood" P0; (3) a generic staleness-detect → retry →
  rotate runtime (make-before-break where the venue permits, REST gap-backfill elsewhere) bound into the existing
  feed-SLA registry, with execution private-stream position resync; (4) alerting + kill-switch escalation via the
  EXISTING frameworks (AlertRule routing, autonomous-recovery matrix) — no new alerting/DR framework is built here.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, live, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    market-tick-data-service,
    execution-service,
    instruments-service,
    strategy-service,
    alerting-service,
  ]
scope: [engineer]
tags: [websocket, staleness, rotation, error-codes, venue-capability, feed-sla, alerting, kill-switch, live-trading]
related:
  [
    /plans/active/w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 12
locked_by:
locked_since:
context_scope:
  [
    /codex/03-services/venue-capability-registry.md,
    /codex/03-observability/data-feed-sla-registry.md,
    /codex/03-observability/alerting.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
    /codex/02-venues/venue-registry-reference.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /plans/active/w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20.md,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/errors/,
    unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py,
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/,
    market-tick-data-service/market_tick_data_service/live/,
    execution-service/execution_service/trade_execution/ws_feeds.py,
    execution-service/execution_service/engine/modes/live/data_source.py,
  ]
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
effort: xhigh
drift_direction: advance-code
source:
  "operator ask 2026-08-21, interactive session slot 4 — stale-websocket rotation + per-venue feed timeouts +
  exhaustive per-venue error-code mapping (every published code individually, from public API docs, all venues);
  ruled part of system_readiness_master; ruled ALL-LOCAL for now (assigned_vm NA — research todos are authored
  promotable but nothing dispatches until the operator explicitly promotes them); gap policy ruled
  make-before-break where the venue permits duplicate subscriptions, rotate-then-REST-backfill elsewhere"
---

# Venue websocket resilience — ws-protocol registry, stale-feed rotation, exhaustive error-code mapping

## Why this doc exists

On crypto venues especially, a websocket connection goes silently stale — no error, no close frame, just no
messages — and execution's position view stops updating without anyone being told. Recovery today is ad-hoc
reconnects; rotation drops data; and no registry anywhere records what each venue's websocket contract actually is
(ping/pong cadence, forced-disconnect windows like Binance's 24h, listen-key refresh, whether a second overlapping
subscription is allowed). Verified at authoring (2026-08-21): UAC's `connectivity.py`, `rate_limits.py`, and
`registry/capability_declarations/` carry ZERO websocket-protocol facts; UTL has no reconnect/resubscribe primitive;
no per-venue error-code enumeration exists beyond DeFi's 35-code `DefiErrorCode`.

This plan closes that as FOUR pieces, in dependency order — schema, research, runtime, wiring — and deliberately
REUSES the frameworks that already exist rather than building new ones:

- **Feed timeouts with a configurable per-venue action already exist** — `DataFreshnessContract` +
  `ALL_FRESHNESS_CONTRACTS` (`data_freshness.py`; SSOT `/codex/03-observability/data-feed-sla-registry.md`) carry
  per-feed `max_age`/`warn_age`/criticality + a `refetch_action` Layer-0 self-heal binding. Rotation becomes a NEW
  ACTION in that registry, not a new mechanism.
- **The generic alerting framework already exists** — alerting-service + Incident Gateway with UAC-driven
  `AlertRule` routing (`/codex/03-observability/alerting.md`). New detections are new rules, not a new framework.
- **The kill-switch / DR framework already exists** and is direction+scope-aware
  (`/codex/04-architecture/autonomous-recovery-matrix.md`); this plan only adds which staleness conditions escalate
  into it.
- **The error-code target surface already exists** — `classify_venue_error(venue, error_code)` in UAC
  `canonical/crosscutting/errors/`. This plan makes it exhaustive per venue and executes
  `system_readiness_master` W14's open P0 — "Every venue error code understood across every consumer — MTDS,
  instruments-service, execution adaptors, and strategy-service balance queries" (no other active plan owns it;
  the sibling W14 plan covers only version-pinning/cassette drift).

## Decisions recorded (operator, 2026-08-21)

1. **All-local for now** — every todo stays `assigned_vm: NA`. Phase-B research todos are written bounded +
   promotable (each is a determinable outcome per the dispatch-eligibility bar) so a later `/na-eligibility-audit`
   or explicit operator promotion can flip them to an AO dispatch batch without rewriting; nothing dispatches until
   the operator says so.
2. **Gap policy — make-before-break + REST backfill**: open the replacement connection before closing the stale one
   wherever the venue permits duplicate subscriptions (a per-venue fact Phase B captures); where it doesn't,
   rotate then REST-backfill the blind window. Zero-drop where possible, bounded-drop-with-recovery elsewhere.
   Private (order/position) streams additionally ALWAYS resync via REST snapshot after rotation.
3. **Error-code completeness bar**: transcribe each venue's PUBLISHED error-code table in FULL — every single code
   individually, from the public API docs — never just the codes we have already observed in the wild.
4. **Part of `system_readiness_master`** (shared mechanism → the owning cross-cutting epic).

## Phase A — UAC schema (the axes everything else reads)

- [ ] [BACKEND] P0. Add a per-venue websocket-protocol spec type (`VenueWsProtocolSpec`) to the UAC venue-capability
      registry (sibling of `registry/capability_declarations/_{category}.py`, queried via the same typed facade —
      `/codex/03-services/venue-capability-registry.md`, static-at-deploy). Fields — ping/pong interval + which side
      initiates; application-level heartbeat channel if any; max connection lifetime before venue-forced disconnect;
      auth/listen-key refresh cadence + mechanism; max subscriptions per connection; max connections per IP/key;
      `duplicate_subscription_allowed` (make-before-break feasibility); resubscribe-after-reconnect semantics;
      sequence/update-id gap-detection support; REST gap-backfill endpoint per feed type; connect-attempt rate
      limit. Done-when — type + facade query + one fully-populated reference venue ship QG-green in
      unified-api-contracts.
- [ ] [BACKEND] P0. Add a per-venue error-code registry schema to UAC `canonical/crosscutting/errors/` — one row per
      published code (venue, code, surface REST/ws/FIX, published meaning, classification into the existing
      `classify_venue_error()` taxonomy, retryability, prescribed action), extending — never duplicating —
      `VenueErrorClassification`. Done-when — `classify_venue_error(venue, code)` resolves any registered code from
      the new tables; QG green.

## Phase B — per-venue research from public API docs (bounded, promotable)

> Bar for every todo in this phase (decision 3): FULL published error-code table transcribed code-by-code + full
> `VenueWsProtocolSpec` facts; cite the exact public doc URL + retrieval date in the declaration file; record the
> doc version in UAC `provider_api_versions.yaml`. The venue universe enumerator is `VENUE_TO_ADAPTER_KEY`
> (`registry/venue_adapter_keys.py`, ~165 entries at authoring — pin the registry, not the count).

- [ ] [BACKEND] P0. CeFi execution venues (every venue declared in `capability_declarations/_cefi.py` with an
      execution adapter key) — populate `VenueWsProtocolSpec` + full error-code table per venue, sub-checkbox per
      venue as each lands. Done-when — every CeFi execution venue populated + cited, QG green.
- [ ] [BACKEND] P1. CeFi pricing-only venues — same treatment. Done-when — same bar.
- [ ] [BACKEND] P1. TradFi venues (IBKR, CME, ICE) + Databento as the data vendor
      (`/codex/02-data/tradfi-databento-sourcing-ssot.md`) — same treatment; note TradFi surfaces include FIX/native
      protocols where websocket does not apply — record `no_websocket_surface` explicitly rather than omitting.
      Done-when — same bar.
- [ ] [BACKEND] P1. DeFi — per-chain WSS-RPC / subgraph subscription semantics into `VenueWsProtocolSpec`
      equivalents, and extend the 35-code `DefiErrorCode` (`/codex/04-architecture/defi-execution-overview.md`) with
      per-protocol error surfaces from public docs. Done-when — every chain + DEX/lending/perp protocol in
      `capability_declarations/_defi.py` covered or explicitly marked absent.
- [ ] [BACKEND] P1. Sports + prediction venues and aggregators — same treatment over their declared venues.
      Done-when — same bar.
- [ ] [BACKEND] P2. Data-only vendors (Tardis and peers) — ws protocol facts for capture feeds + vendor error codes.
      Done-when — same bar.
- [ ] [BACKEND] P1. Census closure — extend the `registry_census.py` drift checks so every venue in
      `VENUE_TO_ADAPTER_KEY` either carries a populated ws-protocol + error-code declaration OR an explicit honest
      absence marker (`no_websocket_surface` / `no_published_error_codes`) — silent gaps impossible. Done-when —
      census check green over the full registry and wired into UAC quality gates.

## Phase C — runtime rotation framework

- [ ] [BACKEND] P0. UTL websocket-session-manager primitive (new module under `unified_trading_library.streaming`) —
      staleness detection (no-message + missed-heartbeat timers driven by the feed's `DataFreshnessContract.max_age`
      and the venue's `VenueWsProtocolSpec`), a per-venue-configurable retry ladder, then ROTATE per decision 2
      (make-before-break when `duplicate_subscription_allowed`, else teardown-reconnect + REST gap-backfill via the
      spec's endpoint). Done-when — unit tests simulate silent-stall, venue-forced disconnect, and rotation with gap
      replay; all green.
- [ ] [BACKEND] P0. Bind rotation into the feed-SLA registry as a first-class action — extend the `refetch_action`
      vocabulary in `data_freshness.py` (`ALL_FRESHNESS_CONTRACTS`) so a stale live feed's Layer-0 self-heal can be
      `rotate_websocket`; keep the registry's CI no-orphan + warn<max invariants green
      (`/codex/03-observability/data-feed-sla-registry.md`). Done-when — action lands + invariant checks green.
- [ ] [BACKEND] P0. Adopt the session manager in MTDS live capture (`market_tick_data_service/live/`) for every
      ws-sourced live feed; gap accounting stays within the existing 4-category stale-not-missing semantics
      (`/codex/05-infrastructure/live-pipeline-architecture.md`) — a rotation gap is recorded honestly, never
      silently spanned. Done-when — rotation exercised against at least one real venue in paper mode with the
      backfilled gap rows manifest-verified (zero silent loss).
- [ ] [BACKEND] P0. Execution private-stream staleness + position resync — apply the same manager to
      `execution_service/trade_execution/ws_feeds.py` and `engine/modes/live/data_source.py`; EVERY rotation of a
      user-data/order/position stream is followed by a mandatory REST snapshot resync (positions + open orders)
      before the stream is trusted again, so execution's position state can never silently stay stale across a
      rotation. Done-when — tests prove a dropped private stream terminates in a resynced state, not a stale one.
- [ ] [BACKEND] P0. Wire the Phase-B error-code registry into every consumer — MTDS shard loops
      (`classify_venue_error()` per `/codex/04-architecture/shard-level-failure-isolation.md`), instruments-service,
      execution adaptors, strategy-service balance queries. This EXECUTES `system_readiness_master` W14's "Every
      venue error code understood across every consumer" P0 — flip that epic checkbox with evidence when this lands.
      Done-when — a census test asserts zero unmapped codes for registered venues; epic checkbox flipped.

## Phase D — alerting + kill-switch wiring (existing frameworks only)

- [ ] [BACKEND] P1. `AlertRule` entries in the UAC-driven routing table (`/codex/03-observability/alerting.md`) for —
      feed-stale-detected (warn tier), rotation-performed (log/digest tier, state-transition dedup — never
      every-tick), rotation-failed-after-retries (paging tier), private-stream-resync-failed (critical). Done-when —
      rules land with tiers per the alerting SSOT + a delivery test per rule.
- [ ] [BACKEND] P1. Kill-switch escalation — extend `/codex/04-architecture/autonomous-recovery-matrix.md` —
      rotation itself is a protective autonomous action (always allowed); repeated rotation failure or
      position-staleness beyond a configured bound on a live-trading venue escalates to the per-venue-scoped
      protective kill (arming autonomous, resume per the matrix's auto-recovery rules). Done-when — matrix doc
      updated in the same shipping window + the escalation path implemented and covered by a test.

## Phase E — post-phase codex audit

- [ ] [DOC] P1. Update every codex contract this plan changes — `/codex/03-services/venue-capability-registry.md`
      (new ws-protocol axis), `/codex/03-observability/data-feed-sla-registry.md` (rotate action),
      `/codex/04-architecture/autonomous-recovery-matrix.md` (escalation rows),
      `/codex/04-architecture/defi-execution-overview.md` (DefiErrorCode growth) — and author the framework's own
      codex SSOT under `codex/04-architecture/` (venue-websocket-resilience). Done-when — every doc named here
      updated or created in the same shipping window as the code it describes.

## Success criteria

- Code gates — `bash scripts/quality-gates.sh` green in every touched repo (UAC, UTL, MTDS, execution-service) at
  each phase boundary; ship via quickmerge per repo.
- The W14 epic checkbox flip (Phase C consumer wiring) carries a census-test citation as evidence.
- Runtime verification — the MTDS and execution rotation todos are not done on unit tests alone; each cites a real
  paper-mode rotation with manifest-verified gap rows (Phase C done-whens).

## Progress Log

- **2026-08-21** — Plan authored (interactive session, slot 4) from operator ask + `/plan-brainstorm` gate.
  Corpus check confirmed — no active plan owns W14's error-code todo; no ws-protocol facts anywhere in UAC; no UTL
  reconnect primitive. Operator rulings captured under "Decisions recorded".
