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

- [x] 1. ✅ [BACKEND] P0. Per-venue websocket-protocol spec type on the UAC venue-capability registry —
      unified-api-contracts@2bebacf085 + full `quality-gates.sh --no-fix` green pre-commit. Shipped as
      `WsProtocolSpec` (`registry/ws_protocol.py` — venue-scoping is the registry key, so the `Venue` prefix was
      dropped) + `ws_protocol` field on `SourceCapability` + `resolve_ws_protocol()` facade + lazy-registry exports
      + binance reference venue (facts seeded with an explicit `doc_retrieved=None` honest-provenance note — Phase-B
      re-verification owed) + `tests/unit/test_ws_protocol_registry.py`. All the planned fields present incl.
      `duplicate_subscription_allowed`, forced-disconnect window, auth cadence, gap detection, REST gap-backfill.
- [x] 2. ✅ [BACKEND] P0. Per-venue error-code registry schema — unified-api-contracts@2bebacf085 + same green gate.
      Extended `VenueErrorClassification` (never duplicated) with `surface` (rest/ws/fix) + `doc_url` provenance;
      `ve()` helper passthrough; `classify_venue_error(venue, code)` verified resolving newly-registered codes with
      doc_url at import (odds_api INVALID_STATUS check) + `tests/unit/test_venue_error_surface_fields.py`.

## Phase B — per-venue research from public API docs (bounded, promotable)

> Bar for every todo in this phase (decision 3): FULL published error-code table transcribed code-by-code + full
> `VenueWsProtocolSpec` facts; cite the exact public doc URL + retrieval date in the declaration file; record the
> doc version in UAC `provider_api_versions.yaml`. The venue universe enumerator is `VENUE_TO_ADAPTER_KEY`
> (`registry/venue_adapter_keys.py`, ~165 entries at authoring — pin the registry, not the count).

- [ ] [BACKEND] P0. CeFi execution venues (every venue declared in `capability_declarations/_cefi.py` with an
      execution adapter key) — populate `WsProtocolSpec` + full error-code table per venue, sub-checkbox per
      venue as each lands. Done-when — every CeFi execution venue populated + cited, QG green.
      Progress 2026-08-21 — binance shipped @2bebacf085; bybit/okx/coinbase/deribit/hyperliquid ws facts
      doc-fetched into the session scratchpad (`cefi_ws_research_notes.md`), file application + error tables next
      batch.
- [ ] [BACKEND] P1. CeFi pricing-only venues — same treatment. Done-when — same bar.
- [ ] [BACKEND] P1. TradFi venues (IBKR, CME, ICE) + Databento as the data vendor
      (`/codex/02-data/tradfi-databento-sourcing-ssot.md`) — same treatment; note TradFi surfaces include FIX/native
      protocols where websocket does not apply — record `no_websocket_surface` explicitly rather than omitting.
      Done-when — same bar. (2026-08-21 — research agent died on the session-limit with ZERO file output; tranche
      fully open, resume after the 16:40 Europe/London quota reset.)
- [ ] [BACKEND] P1. DeFi — per-chain WSS-RPC / subgraph subscription semantics into `WsProtocolSpec`
      equivalents, and extend the 35-code `DefiErrorCode` (`/codex/04-architecture/defi-execution-overview.md`) with
      per-protocol error surfaces from public docs. Done-when — every chain + DEX/lending/perp protocol in
      `capability_declarations/_defi.py` covered or explicitly marked absent.
      Partial @2bebacf085 — all 6 `DEFI_CAPABILITIES` sources done (uniswap/curve/instadapp/mev honest-absence with
      citations; aave 84-code `Errors.sol` table in `_defi_aave_codes.py`; versifi explicit-unverified);
      `PROTOCOL_CAPABILITIES` NOT covered — see the dedicated todo below.
- [ ] [BACKEND] P1. Sports + prediction venues and aggregators — same treatment over their declared venues.
      Done-when — same bar.
      Partial @2bebacf085 — 14/14 `_sports.py` venues carry `ws_protocol`; exhaustive odds_api (33 named codes) +
      polymarket CLOB (59 entries) tables shipped + wired into sports.py/prediction.py; error-table completeness for
      the other 12 venues is UNVERIFIED (agent died on quota pre-report) — verify before flipping.
- [ ] [BACKEND] P2. Data-only vendors (Tardis and peers) — ws protocol facts for capture feeds + vendor error codes.
      Done-when — same bar.
      Partial @2bebacf085 — 12/12 `_altdata.py` vendors carry `ws_protocol` + the `_altdata_infra_codes.py` table is
      wired; completeness UNVERIFIED (agent died pre-report); tardis/ccxt (declared in `_cefi.py`) still open.
- [ ] [BACKEND] P1. DeFi `PROTOCOL_CAPABILITIES` streaming-facts coverage — the ~60-protocol dict in
      `capability_declarations/_defi.py` is a distinct construct with NO `ws_protocol` field (found 2026-08-21);
      extend it (or record per-protocol streaming facts at the `SourceCapability` layer) and populate per the
      Phase-B bar. Done-when — every `PROTOCOL_CAPABILITIES` key covered or explicitly marked absent; QG green.
- [ ] [BACKEND] P2. Curve REST error-code table — `api.curve.finance/v1/documentation` returns HTTP 403 to
      automated fetch (2026-08-21); retrieve via a browser session or a mirror and transcribe. Done-when — curve
      rows carry doc_url citations.
- [ ] [OPERATOR] P2. Versifi public API docs — none discoverable (checked 2026-08-21; versifi.io has no developer
      section) despite its declared `ws_trades` operation; supply a doc link or credentialed access. Its declaration
      carries an explicit all-None unverified `WsProtocolSpec` until then.
- [ ] [BACKEND] P1. Census closure — extend the `registry_census.py` drift checks so every venue in
      `VENUE_TO_ADAPTER_KEY` either carries a populated ws-protocol + error-code declaration OR an explicit honest
      absence marker (`no_websocket_surface` / `no_published_error_codes`) — silent gaps impossible. Also dedupe the
      pre-existing duplicate `(venue, code)` keys found 2026-08-21 in the kalshi/hyperliquid/polymarket maps
      (duplicates are dead code under the linear-scan classify). Done-when — census check green over the full
      registry and wired into UAC quality gates.

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
- **2026-08-21 (batch 1 shipped)** — unified-api-contracts@2bebacf085 (full QG green pre-commit, quickmerge, LDR
  ancestry verified). Phase A complete (todos 1-2 flipped above) PLUS the DeFi/sports/altdata research tranche
  outputs (aave 84-code table; odds_api 42 / polymarket 68 merged codes; `classify_venue_error()` resolution
  verified at import). Sub-agent fleet hit the account session limit (resets 16:40 Europe/London): the tradfi agent
  died with ZERO file output (tranche fully open); sports + altdata agents died pre-report — their on-disk work was
  inherited under the dead-claim rule, lint-fixed (15 E501 + 1 I001), and the two orphan sibling tables wired into
  sports.py/prediction.py by this session. Phase C1 (UTL `WsSessionManager` + 5 unit tests + streaming exports) is
  AUTHORED but not yet gated — UTL QG is the next gate. CeFi ws facts for bybit/okx/coinbase/deribit/hyperliquid
  were doc-fetched into the session scratchpad (`cefi_ws_research_notes.md`) for the next UAC batch.
  `provider_api_versions.yaml` decision — most venue doc sites are living pages publishing NO version identifier;
  doc URLs + retrieval dates are recorded in the declaration files themselves, the yaml gets entries only where a
  real version exists (none surfaced so far).
