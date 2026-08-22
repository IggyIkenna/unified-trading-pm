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

- [x] [BACKEND] P0. CeFi execution venues — ✅ unified-api-contracts@3b13629f9f (+ binance @2bebacf085,
      bybit/okx/coinbase/deribit/hyperliquid ws specs @54009a4fdd), full QG green (348s) pre-commit. ALL 22
      `_cefi.py` sources now carry `ws_protocol` (16 added @3b13629f9f; ccxt/nautilus/fix honest-absence as
      library/protocol abstractions; tardis architecture-level — remote surface is HTTP, ws is the local
      tardis-machine). Exhaustive error tables landed: ~1,600 doc-cited codes across 24 `_cefi_*_codes*.py`
      files (binance spot 78 — Binance states codes are universal across products; bybit 378; okx 381;
      deribit 136; kraken 34; kucoin 271; bitget 151; mexc 122; coinbase 26; upbit 16; hyperliquid 17 via
      onchain_perps.py). Honest-provenance residuals in the module docstrings: okx/coinbase/mexc transcribed
      from ccxt's maintained exact-code maps (official docs SPA-blocked); kraken_futures publishes no table
      (honest-absent); binance futures-only extension codes → P2 todo below.
- [ ] [BACKEND] P2. Binance futures-only extension error codes — developers.binance.com USDS-M/COIN-M pages
      render as SPA shells to automated fetch (confirmed twice 2026-08-21) and the docsify mirror is empty;
      retrieve via a browser session and append any codes beyond the universal spot table. Done-when — the
      futures pages checked + any futures-only codes appended with doc_url.
- [x] [BACKEND] P1. CeFi pricing-only venues — ✅ vacuously complete @3b13629f9f: the capability registry
      declares no CeFi source beyond the 22 in `_cefi.py`, all covered by the execution-venues todo above
      (verified 2026-08-21 via the `CEFI_CAPABILITIES` enumeration — zero entries without `ws_protocol`).
- [x] [BACKEND] P1. TradFi venues + Databento — ✅ unified-api-contracts@3b13629f9f. All 12 `_tradfi.py`
      sources carry `ws_protocol`: databento real gateway-session facts sourced from the vendor's own client
      code (docs.databento.com is a client-rendered SPA — confirmed, not assumed); ibkr `no_websocket_surface`
      (proprietary TWS socket, not ws); cme/cboe/nasdaq/nyse/ice/fx recorded per-source as routing exclusively
      via the IBKR gateway; fred/ecb/ofr/yahoo REST-only honest absence. Error tables: IBKR's full published
      TWS table (302 new codes in `_tradfi_ibkr_codes.py`; 6 collisions skipped; semantic-mismatch notes for
      pre-existing generic 400/401/429 entries feed the census todo), FRED completed to its full documented
      set (+423), databento's pre-existing 14-entry table verified comprehensive. Runtime-verified:
      `classify_venue_error("ibkr","10230")` and `("fred","423")` resolve.
- [ ] [BACKEND] P1. DeFi — per-chain WSS-RPC / subgraph subscription semantics into `WsProtocolSpec`
      equivalents, and extend the 35-code `DefiErrorCode` (`/codex/04-architecture/defi-execution-overview.md`) with
      per-protocol error surfaces from public docs. Done-when — every chain + DEX/lending/perp protocol in
      `capability_declarations/_defi.py` covered or explicitly marked absent.
      Partial @2bebacf085 — all 6 `DEFI_CAPABILITIES` sources done (uniswap/curve/instadapp/mev honest-absence with
      citations; aave 84-code `Errors.sol` table in `_defi_aave_codes.py`; versifi explicit-unverified);
      `PROTOCOL_CAPABILITIES` NOT covered — see the dedicated todo below.
- [x] [BACKEND] P1. Sports + prediction venues and aggregators — ✅ @2bebacf085 (tables) +
      unified-api-contracts@3b13629f9f (doc-verified completeness + gap-fill). odds_api VERIFIED-COMPLETE
      34/34 against the live doc; betfair +6 APINGException codes (`_sports_betfair_aping_codes.py`;
      official Confluence doc is an SPA — corroborated via the betfairlightweight enums mirror, the same
      secondary source the pre-existing entries cite); kalshi — the `_sports.py` note claiming a 22-code ws
      table was already transcribed was FALSE (nothing was wired): the real 28-code table from the
      authoritative asyncapi.yaml landed as `_prediction_kalshi_ws_codes.py` + the stale note corrected;
      polymarket CLOB +1 missing code (503 cancel-only) → 60, internal count mismatches fixed;
      pinnacle/opticodds honest-absent beyond 429 (pinnacle API access restricted since 2025-07-23).
- [x] [BACKEND] P2. Data-only vendors — ✅ @2bebacf085 + unified-api-contracts@3b13629f9f. 12/12 `_altdata.py`
      vendors verified against their docs (aws 15/15, github 5/5, gcp 16/16 canonical codes; alchemy +2
      gap-filled; glassnode confirmed complete); tardis ws-protocol spec + error addendum
      (`_tradfi_tardis_codes.py`, new code "30" only — RELOCATED from a new cefi key that was shadowing
      tradfi's existing tardis key in the merged `VENUE_ERROR_MAP` and silently reverting the 300/140
      structural-absence SKIP ruling); ccxt honest-absent (client-library abstraction).
- [ ] [BACKEND] P1. DeFi `PROTOCOL_CAPABILITIES` streaming-facts coverage — the ~60-protocol dict in
      `capability_declarations/_defi.py` is a distinct construct with NO `ws_protocol` field (found 2026-08-21);
      extend it (or record per-protocol streaming facts at the `SourceCapability` layer) and populate per the
      Phase-B bar. Done-when — every `PROTOCOL_CAPABILITIES` key covered or explicitly marked absent; QG green.
- [ ] [BACKEND] P2. Curve REST error-code table — `api.curve.finance/v1/documentation` returns HTTP 403 to
      automated fetch (2026-08-21); retrieve via a browser session or a mirror and transcribe. Done-when — curve
      rows carry doc_url citations.
- [ ] [BACKEND] P2. Polymarket perps outage-flag re-verification — `_cefi.py`'s polymarket_perp declaration still
      carries `BLOCKED-UPSTREAM-OUTAGE` (DNS NXDOMAIN on perps-api.polymarket.com, 2026-06-21), but
      docs.polymarket.com/api-reference/perps/\* now documents a live `wss://ws.perpetuals.polymarket.com/v1/ws`
      endpoint (found 2026-08-21 during the ws-spec research). Probe the documented hosts and flip
      `supports_live`/`supports_batch`/`base_urls` if the outage is over. Done-when — probe result recorded +
      declaration matches reality.
- [ ] [OPERATOR] P2. Versifi public API docs — none discoverable (checked 2026-08-21; versifi.io has no developer
      section) despite its declared `ws_trades` operation; supply a doc link or credentialed access. Its declaration
      carries an explicit all-None unverified `WsProtocolSpec` until then.
- [x] [BACKEND] P1. Census closure — ✅ unified-api-contracts@235acfea88. `registry_census.py` checks 7-10 +
      `errors/_census_registry.py` (5 `ERROR_KEY_ALIASES`: deribit_options/kalshi_perp/polymarket_perp/fx/
      aave_oracle; 41 `ERROR_CODES_HONEST_ABSENCE` adapter keys — on-chain protocols, oracles, wrapped-staking
      tokens, jupiter — each with a citation-grade reason; phantom/stale/dangling entries are error-level);
      66/66 capabilities declare `ws_protocol`. Dedupe: 14 dead-duplicate `(venue, code)` keys purged across
      kalshi/hyperliquid/polymarket/alchemy/kucoin — every copy carried identical action/retry flags (measured),
      so classification outcomes are unchanged; kalshi moved from the altdata family into its prediction home
      (one venue key, one family). Wired as UAC STEP 5.110 (fails the repo on any error-level finding; baseline 0).
- [ ] [BACKEND] P2. Consolidate the six venue-error keys still declared in two family maps (alchemy altdata+infra,
      defillama, hyperliquid defi+onchain_perps, kalshi prediction+sports, polymarket prediction+sports, thegraph)
      into one family each — the census `error_key_multi_family` WARNING names them; first-match order across
      families is a merge-order accident (the 2026-08-21 tardis shadowing). Done-when — that warning count is 0.

## Phase C — runtime rotation framework

- [x] 3. ✅ [BACKEND] P0. UTL websocket-session-manager primitive — unified-trading-library@fcfcbf3893 + full
      `quality-gates.sh --no-fix` green pre-commit (6907 passed). `streaming/ws_session_manager.py` — staleness
      watchdog driven by `DataFreshnessContract.max_age` + the venue `WsProtocolSpec`, per-venue retry ladder with
      exponential backoff, rotation per decision 2 (make-before-break when `duplicate_subscription_allowed`, else
      teardown-reconnect + REST gap-backfill callback), proactive rotation ahead of venue-forced disconnects,
      listen-key-style auth refresh; exported via `streaming/__init__`; 5 unit tests cover silent-stall,
      forced-disconnect make-before-break ordering, ladder-exhaustion rotation with gap replay, staleness deferral,
      and auth cadence. Broad-except registered in `QUALITY_GATE_BYPASS_AUDIT.md` §2.1a + the gate's excludes list.
- [ ] [BACKEND] P0. Bind rotation into the feed-SLA registry as a first-class action — extend the `refetch_action`
      vocabulary in `data_freshness.py` (`ALL_FRESHNESS_CONTRACTS`) so a stale live feed's Layer-0 self-heal can be
      `rotate_websocket`; keep the registry's CI no-orphan + warn<max invariants green
      (`/codex/03-observability/data-feed-sla-registry.md`). Done-when — action lands + invariant checks green.
      Progress 2026-08-21 — UAC half LANDED @3b13629f9f: two-verb vocabulary documented on the field, the 6
      ws-sourced CeFi venues bound to `rotate-websocket:<source>`, `ActionType.ROTATE_WEBSOCKET`, the verb-aware
      invariant test + dependency-revocation policies. UTL LANDED unified-trading-library@4fb84f00fe
      (`ws_rotation_request` sentinel + watchdog consumption + `RecoveryScriptRegistry` entry + the freezegun
      conftest fix); alerting-service LANDED alerting-service@adef9eb372 (`feed_refetch_rules` resolves the bound
      action from the contract; `ROTATE_WS_{feed_id}` confirm-string). deployment-service
      (`scripts/recovery/rotate_websocket.py` + 8 tests, gate-green on its own files) is BLOCKED on a peer's live
      untracked `terraform/gcp/pnl_attribution_scheduler.tf` failing the Cloud-Run-job registry guard in the shared
      checkout — flip once it ships.
- [ ] [BACKEND] P0. Adopt the session manager in MTDS live capture (`market_tick_data_service/live/`) for every
      ws-sourced live feed; gap accounting stays within the existing 4-category stale-not-missing semantics
      (`/codex/05-infrastructure/live-pipeline-architecture.md`) — a rotation gap is recorded honestly, never
      silently spanned. Done-when — rotation exercised against at least one real venue in paper mode with the
      backfilled gap rows manifest-verified (zero silent loss).
      Code LANDED market-tick-data-service@a06c346ee0 (bridge + runner wiring) + @2bdad93bd5 (the
      fresh-connector-per-generation fix below). ROTATION PROVEN by a real paper-mode drill against BINANCE-SPOT
      (public trade feed; direct-GCS sink on the `-test-` bucket, local Redis, 300s, rotation requested at t+140s
      via the real `rotate-websocket` Layer-0 sentinel): make-before-break run → 1 rotation, `gap_windows=[]`, all
      4 boundary windows FRESH with ticks continuing (1730/9489/1430/1519; reconnects=0), tick parquet
      `BINANCE-SPOT:SPOT_PAIR:BTC-USDT.parquet` written to
      `market-data-tick-cefi-test-central-element-323112` (18,586 B). **The drill CAUGHT A REAL DEFECT unit tests
      could not** (see the batch-6 Progress Log + the fix todo below). **NOT flipped**: the done-when requires
      manifest-verified gap rows and the drill's `MTDSShardManifestRecorder` captured 14,168 rows in-memory but
      persisted ZERO to the `-test-` catalogue (no `_index/per_vm/*` shard, `availability_index.parquet` 404) — the
      writes were silently swallowed by the per-instrument shard-isolation try/except. Tracked as the issue +
      todo below; the ws-resilience rotation logic itself is proven, this is a `-test-`-bucket manifest-write gap.
- [ ] [BACKEND] P1. MTDS live manifest-write to the `-test-` catalogue produces zero rows — the paper-mode drill
      (2026-08-22) captured 14,168 rows via `record_captured`/`record_flush_captured` and called
      `MTDSShardManifestRecorder.close()` → `ManifestWriter.close()`, but no `_catalogue/_index/*` object landed in
      `market-data-tick-cefi-test-central-element-323112`; the failure is swallowed by
      `flush_window`'s per-instrument isolation. Diagnose (SA write grant on the `-test-` bucket? `per_vm_shards`
      resolution off-VM? a `ManifestWriter.close()` early-return) and make a `-test-`-mode live run write
      manifest-verified rows — THEN the MTDS C3 done-when flips. Issue:
      `/plans/active/issues/mtds_live_manifest_write_to_test_bucket_silent_2026_08_22.md`. Done-when — a paper/test
      live run leaves manifest rows readable from the `-test-` catalogue with honest capture_status.
- [ ] [BACKEND] P1. Reset the `_closed` latch in `connect()` across the ~37 MTDS ws connectors that set
      `_closed = True` in `close()` and loop `while not self._closed` in `stream()` — a close()+connect() on the
      SAME instance (a bare reconnect/rotation without the bridge factory) leaves the replacement socket subscribed
      but never read (the shard goes dark; found by the 2026-08-22 paper drill, binance_futures_ws.py fixed as the
      exemplar). The C3 factory path is ALREADY immune (each generation is a fresh instance), so this is defensive
      hardening for any non-bridge reconnect caller. Done-when — every latching connector resets `_closed` on a
      successful reopen + a regression test.
- [x] 4. ✅ [BACKEND] P0. Execution private-stream staleness + position resync — execution-service@42e54a11f8 +
      full `quality-gates.sh --no-fix` green pre-commit. `trade_execution/private_stream_guard.py`
      (`PrivateStreamGuard`) wraps any `BaseOrderFeedHandler` with the UTL `WsSessionManager` and enforces the
      resync invariant — after EVERY new connection generation (initial/reconnect/rotation) the REST snapshot
      resync is awaited BEFORE any update from that generation is yielded; a venue-closed stream rotates
      immediately. `ws_feeds.py` gains a uniform base `close()`; `engine/modes/live/data_source.py` feeds ticks to
      an optional session manager. 3 tests prove a dropped private stream terminates resynced, never stale
      (initial-resync-before-first-update, close→rotate→resync-before-next-update ordering, stop semantics).
- [x] [BACKEND] P0. Error-code registry wired into every consumer — ✅ unified-api-contracts@235acfea88. Every
      consumer family already classifies through the UAC registry (`classify_venue_error` call sites measured
      2026-08-22: MTDS 117, instruments-service 60, execution-service 85, strategy-service 5 — no per-service
      tables), so the corpus landed @3b13629f9f reaches them by construction; the done-when artifact is
      `tests/unit/test_registry_census_ws_resilience.py` — census checks 7-10 assert every adaptered venue
      resolves a venue-error table (by name, adapter key, or explicit alias) or an explicit honest-absence marker,
      every capability declares its ws protocol, no dead-duplicate `(venue, code)` keys, and the registries cannot
      rot (phantom/stale/dangling are errors) — 0 error-level findings over all 187 venues; gated as UAC
      STEP 5.110. `system_readiness_master` W14 checkbox flipped with this evidence.
- [ ] [BACKEND] P2. Hoist the ws-resilience symbols onto the sanctioned import facades — export `WsProtocolSpec`
      from UAC's root `unified_api_contracts` facade and the `WsSession*` family from UTL's root facade, then drop
      the three `# noqa: qg-deep-import` markers this phase added (`streaming/ws_session_manager.py`,
      `execution_service/trade_execution/private_stream_guard.py`, `engine/modes/live/data_source.py`). Done-when —
      top-level imports in all three consumers; deep-import checks green with zero noqas from this plan.
- [ ] [BACKEND] P2. Harden UAC against the freezegun × lazy-registry import trap — `coverage_exclusions.py`
      validates `verified_at` against `datetime.now()` at IMPORT time, and `registry.__getattr__`'s lazy exports
      get force-imported by freezegun's module-attribute walk under a frozen clock (found 2026-08-21: it aborted
      `freeze_time` half-applied and froze every later test in a UTL xdist worker). UTL's `tests/conftest.py` now
      excludes `unified_api_contracts` from freezegun's walk; the UAC-side fix is to make that validation lazy or
      injectable (off import time) so no repo's `freeze_time` can trip it. Done-when — a UAC test freezes time at
      2026-01-01, imports `coverage_exclusions`, and nothing raises.

## Phase D — alerting + kill-switch wiring (existing frameworks only)

- [x] [BACKEND] P1. `AlertRule` entries — ✅ unified-api-contracts@3b13629f9f (codes + rules + delivery tests) +
      execution-service@c23b10c01b + market-tick-data-service@a06c346ee0 (emission wiring). `WS_ROTATION_COMPLETED`
      (INFO, log-only — one event per rotation EPISODE, never per-tick), `WS_ROTATION_FAILED` (HIGH, pages),
      `PRIVATE_STREAM_RESYNC_FAILED` (CRITICAL, pages), each with a first-match delivery test
      (`tests/internal/unit/test_ws_resilience_alert_rules.py`) and a dependency-revocation policy; the
      feed-stale-detected tier was verified to ride the EXISTING criticality-tiered DATA_STALE / FEED_UNHEALTHY
      rules (no new code needed, test asserts they resolve specifically). Emitted by the MTDS ws-session bridge
      and the execution `PrivateStreamGuard` via `log_event`.
- [x] [BACKEND] P1. Kill-switch escalation — ✅ execution-service@c23b10c01b + unified-trading-pm@8d35ca1cae (same
      shipping window). `PrivateStreamGuard`: ≥3 consecutive rotation failures OR ≥3 consecutive REST-resync
      failures on a venue emit `KILL_SWITCH_VENUE_DISCONNECT` (the existing VENUE-scope `triggers_kill_switch`
      rule publishes the KillSwitchEvent — arming autonomous; resume per the matrix, never the guard); a failed
      resync also withholds every update from that connection generation. 3 new tests prove paging-then-recovery,
      sustained-failure escalation with zero yields, and rotation-failure escalation. Rotation itself stays a
      protective autonomous action. Matrix: G8 row + three "Alerting Channels by Severity" rows.

## Phase E — post-phase codex audit

- [x] [DOC] P1. Codex audit — ✅ unified-trading-pm@8d35ca1cae, same shipping window as the code.
      `venue-capability-registry.md` (§ Websocket-protocol axis), `data-feed-sla-registry.md` (two-verb
      vocabulary, rotate Layer-0 script, consumers row), `autonomous-recovery-matrix.md` (G8 + channel rows),
      `defi-execution-overview.md` (published-table registry vs the 35-code runtime enum), NEW SSOT
      `/codex/04-architecture/venue-websocket-resilience.md` (authoritative for the ws-protocol axis, the rotation
      policy and the rotate-websocket Layer-0 action), two alerting playbooks (`ws_rotation_failed.md`,
      `private_stream_resync_failed.md`) and the RB-CONN-001 rotate step.

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
- **2026-08-21 (batch 2 shipped + pre-compact checkpoint)** — unified-api-contracts@54009a4fdd (cefi ws specs ×5) +
  unified-trading-library@fcfcbf3893 (C1 session manager) landed, LDR ancestry verified. Execution-service C4
  LANDED as execution-service@42e54a11f8 (the push-reject rebase renamed the local 6cef44435 — cite 42e54a11f8;
  content verified at origin tip; checkbox flipped above); nothing is uncommitted in any repo. **Lessons**: (1) quickmerge quarantines the dirty tree
  into a named `quickmerge-NNNNN` stash BEFORE its remote fetch — a DNS flap (`ssh.github.com` unresolvable, hit
  twice) then leaves a CLEAN tree + "Nothing to commit" on re-run; recovery is `git restore --source='stash@{N}'`
  for tracked files AND `--source='stash@{N}^3'` for untracked ones (the stash's untracked third parent —
  `git stash show` does NOT list untracked files); both the UAC and UTL batches were recovered exactly this way —
  ALWAYS check `git stash list` before re-authoring "lost" work. (2) UAC is EDITABLE-installed in UTL's venv
  (direct_url.json editable=true) — never edit UAC while a UTL/execution gate is mid-run. (3) UTL gate conventions:
  `unified_api_contracts.registry.*` counts as a deep import (only one-level domains like `.internal` or the root
  facade pass; `# noqa: qg-deep-import` is the sanctioned interim marker); a broad `except Exception:` needs BOTH a
  `QUALITY_GATE_BYPASS_AUDIT.md` §2.1a row AND a `BROAD_EXCEPT_EXTRA_EXCLUDES` glob in the repo's
  `scripts/quality-gates.sh` — the audit row alone does not clear the gate, and the violation prints as a ⚠️ line,
  not a ❌. (4) pytest-xdist `KeyError: <WorkerController gwN>` INTERNALERROR with "N passed, 0 failed" is a
  teardown flake under host contention — one re-run, not a test hunt. Stashes `quickmerge-47010` (UAC) and
  `quickmerge-66065` (UTL) are now-redundant copies of landed content — parked, droppable once shas confirmed on
  origin.
- **2026-08-21 (batch 3 — UAC mega-batch landed)** — unified-api-contracts@3b13629f9f (47 files, full QG green
  348s pre-commit). Phase B research integrated (4-agent wave: ~2,000 new doc-cited error codes + 28 ws specs);
  C2's UAC half; Phase D codes/rules/policies. **The first gate run FAILED 8 tests while the pipe reported
  exit 0** (`| tail` fabricates success — READ the gate's own banner): a rotted hardcoded count
  (ActionType 11 → made count-free), 3 new AlertCodes missing dependency-revocation policies (the closed-set
  guard working as designed), and agent E's new cefi `tardis` key SHADOWING tradfi's existing key in the merged
  `VENUE_ERROR_MAP` — silently reverting the tardis 300/140 structural-absence SKIP ruling; fixed by relocating
  the one genuinely-new code ("30") into the existing tradfi key. **Lesson**: a venue key may live in ONE
  family error map only — a second key in another family replaces the first wholesale at merge, with zero
  conflict signal. **Concurrent QGs flake**: UAC + UTL gates run simultaneously produced 2 UTL failures + 3
  errors in files the batch never touched (write_gate polars fixtures, utc_aligned_scheduler timing) — rerun
  standalone before diagnosing. Agent W found the shipped OKX spec passing `max_connection_attempts_per_window`
  (not a schema field — pydantic's default silently dropped it): fixed to `max_connections_per_ip` and
  `WsProtocolSpec` hardened with `extra="forbid"` so the whole class fails at import. Also authored + gated
  this wave (shipping as their gates clear): UTL C2 sentinel, execution guard Phase-D escalation, MTDS C3
  bridge, alerting resolver, deployment-service Layer-0 script, the Phase E codex set.
- **2026-08-21 (batch 4 — service repos landed)** — unified-trading-library@4fb84f00fe (C2 sentinel + watchdog
  consumption + registry entry + freezegun fix), execution-service@c23b10c01b (Phase D guard escalation),
  alerting-service@adef9eb372 (bound-action resolver + rotate confirm-string), unified-trading-pm@8d35ca1cae
  (Phase E codex set). **Every downstream gate hit a closed-set guard my new members violated — all working as
  designed**: the ActionType count test (UAC), one dependency-revocation policy per AlertCode (UAC), one
  confirm-string template per ActionType (alerting `gateway/manual_action_endpoint.py`), imports-inside-functions
  plus the 900-line file / 50-line method caps (MTDS — the legacy tick sink + blob-path builder were extracted to
  `live/_tick_sink.py`, runner 929 → 829 lines). **The UTL failure was NOT a flake**: freezegun's
  `freeze_time().start()` walks every loaded module's attributes; UAC `registry.__getattr__` lazy exports made
  that walk force-import `coverage_exclusions` under the frozen 2026-05-08 clock → its import-time `verified_at`
  validation raised → the freeze aborted half-applied → FakeDatetime leaked into the whole xdist worker (polars
  "expected datetime, got object" in write_gate). Fix: `freezegun.configure(extend_ignore_list=
  ["unified_api_contracts"])` in UTL `tests/conftest.py`; UAC-side hardening is a P2 todo above. **Two identical
  standalone reruns = a stable condition, not contention** — that rule is what made me read the traceback instead
  of retrying a third time. deployment-service is gate-green on its own files but tree-blocked by a peer's live
  untracked terraform WIP in the shared slot checkout (protected, not inherited — see Deferred).
- **2026-08-22 (batch 5 — census closure landed)** — unified-api-contracts@235acfea88 (full QG green 399s incl.
  the new STEP 5.110). C5 + census-closure flipped; `system_readiness_master` W14 "every venue error code
  understood" flipped with the census-test evidence. Measured before writing a line of census code: 66/66
  capabilities carried `ws_protocol` (the ws half was already closed by Phase B); 98/187 venues had no error key
  by venue or adapter name — 52 of them `NO_ADAPTER_YET` (no producer → no surface yet, already a check-1
  warning) and 46 adapter keys needing an explicit decision, split 5 aliases / 41 honest absences. **Duplicate
  keys were cross-FAMILY, not in-file**: kalshi was declared in three family maps (altdata's generic
  `_rest_macro_errors` expansion, prediction, sports), hyperliquid in defi + onchain_perps, polymarket in
  prediction + sports, alchemy in altdata + infra — `_merge_venue_error_maps` concatenates, so merge order
  decided the winner (same class as the tardis shadowing). Removed with a guarded line-based script (exact-one
  match asserted per spec) rather than 18 hand edits; the remaining non-duplicate cross-family splits now
  surface as a census WARNING with a P2 consolidation todo.

- **2026-08-22 (batch 6 — MTDS C3 rotation drill + fresh-connector fix)** — the paper-mode rotation drill was the
  first time the ws-resilience runtime met a REAL venue, and it earned its keep: the first drill (break-then-make,
  report `paper_rotation_report_20260821T233835Z.json`) rotated honestly (1 rotation, 5s gap recorded, the 23:42
  window correctly STALE) but **the shard went DARK after rotation** — 23:43 captured zero ticks. Root cause is
  FLEET-WIDE: all 52 MTDS ws connectors set `_closed = True` in `close()` and loop `while not self._closed` in
  `stream()`; a rotation is close()+connect() on the SAME instance, so the replacement socket was subscribed but
  the stream loop had already exited on the latch and never read it (37 connectors never reset the latch). **No
  unit test caught this** — the fakes don't model the real close/stream latch — which is exactly why the C3
  done-when demanded a real paper-mode run, not unit-test green. Fix (market-tick-data-service@2bdad93bd5): the
  bridge takes a `connector_factory` and builds a FRESH connector per generation (real make-before-break for
  duplicate-subscription venues; immune to the latch since each generation is a new instance), the runner reads
  the live connector through a property over `bridge.connector`, and the STALE flag is now raised by the manager's
  gap callback (so a zero-gap make-before-break rotation stays FRESH, a break-then-make gap goes STALE). The
  second drill (`paper_rotation_report_20260821T234848Z.json`) proved it: 1 rotation, `gap_windows=[]`, all 4
  windows FRESH, ticks continuous (1730/9489/1430/1519), reconnects=0. **Honest gap**: the same drill's manifest
  recorder captured 14,168 rows but persisted ZERO to the `-test-` catalogue (silently, via shard isolation) — so
  C3 stays OPEN (its done-when requires manifest-verified rows) with a P1 issue + todo; the rotation LOGIC is
  proven, the `-test-`-bucket manifest-write path is the remaining gap. The isolated-worktree quickmerge
  (`--isolated`) was the ship path — a peer's live untracked `lending_indices_radiant.py` (lint-dirty) was
  failing the shared-tree gate, and isolated mode gates the named files against a clean origin checkout, immune to
  peer working-tree dirt (verified the landed SHA's content by grep, not by trusting ahead=0).

## Rule-9 final report — 2026-08-22

**Umbrella goal**: per-venue websocket resilience end to end (ws-protocol registry axis, exhaustive per-venue
error-code mapping, staleness→retry→rotate runtime with make-before-break + honest gap accounting, alerting +
kill-switch escalation via existing frameworks) — executing `system_readiness_master` W14. **Shipped this
initiative (all on `origin/live-defi-rollout`)**:

- **Phase A** (UAC schema) — `WsProtocolSpec` axis + error-schema `surface`/`doc_url` — unified-api-contracts@2bebacf085.
- **Phase B** (per-venue research, ~2,000 doc-cited codes + 28 ws specs across CeFi/DeFi/TradFi/sports/prediction/
  altdata) — unified-api-contracts@3b13629f9f (+ @54009a4fdd, @2bebacf085). Every entry doc-cited or explicit
  honest absence.
- **Phase C1** (UTL `WsSessionManager`) — unified-trading-library@fcfcbf3893; **C2** (rotate-websocket Layer-0
  vocabulary + sentinel + registry entry + bound-action resolver) — UAC@3b13629f9f + UTL@4fb84f00fe +
  alerting-service@adef9eb372 (+ deployment-service Layer-0 script authored, ship pending — below); **C3** (MTDS
  bridge) — market-tick-data-service@a06c346ee0 + @2bdad93bd5, rotation drill-proven, manifest-verification owed;
  **C4** (execution `PrivateStreamGuard` resync-before-trust) — execution-service@42e54a11f8 + Phase-D escalation
  @c23b10c01b; **C5/census** (every adaptered venue resolves an error table or explicit absence; dead-dupe purge;
  UAC STEP 5.110) — unified-api-contracts@235acfea88.
- **Phase D** (alert rules + kill-switch escalation) — UAC@3b13629f9f (codes/rules/policies/delivery tests) +
  execution-service@c23b10c01b + market-tick-data-service@a06c346ee0 (emission). **Phase E** (codex audit: new
  `venue-websocket-resilience.md` SSOT, registry/SLA/matrix/DeFi doc updates, 2 alerting playbooks, RB-CONN-001)
  — unified-trading-pm@8d35ca1cae.
- **`system_readiness_master` W14** "every venue error code understood across every consumer" — **flipped** with
  census-test evidence (unified-trading-pm@e7d99c9275).

**Runtime verification**: the C3 rotation ran against a real BINANCE-SPOT feed and is make-before-break with
honest gap accounting; the drill also surfaced + fixed a fleet-wide connector-latch defect (batch-6). The C4
execution guard has unit proof (resync-before-trust, venue-kill escalation) but a real private-stream paper run
needs venue credentials (`[OPERATOR]`).

**Open (plan stays active — do NOT archive)**: deployment-service `rotate_websocket` ship + C2 flip (blocked on a
peer's live untracked terraform in the shared checkout); MTDS C3 manifest-write gap (P1 issue above); connector
`_closed`-latch defensive hardening (P1); C4 real paper run (`[OPERATOR]` credentials); Phase-B P2 residuals
(binance-futures codes, curve 403, `PROTOCOL_CAPABILITIES`, polymarket-perps probe, versifi `[OPERATOR]`); facade
hoist (P2); multi-family error-key consolidation (P2); UAC freezegun-hardening (P2).

## Deferred work after 2026-08-21

| Item                                                        | State / why deferred                                                                                                                                                                           | Blocked on                                                   |
| ----------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| deployment-service `rotate_websocket` ship                  | gate-green on its own files; the TREE gate fails on a PEER's live untracked `terraform/gcp/pnl_attribution_scheduler.tf` (mtime 22:44Z, the code_readiness_t3 session) — protected, not inherited | the peer committing + registering their tf (not mine to do) |
| C2 flip                                                     | UAC/UTL/alerting halves landed; flips on the deployment SHA                                                                                                                                    | the deployment ship above                                    |
| C3 paper-mode rotation verification                         | code landed (bridge + runner); done-when needs a real paper-mode run with manifest-verified gap rows                                                                                           | MTDS ship, then a runtime run                                |
| C5 consumer wiring + W14 epic flip + census closure         | error corpus landed; census test + dedupe (kucoin 109000/163000, kalshi/hyperliquid/polymarket)                                                                                                 | next UAC batch                                               |
| Phase B residuals: binance-futures codes, curve 403,        | P2 todos above; browser-session retrievals                                                                                                                                                     | nothing (versifi: operator)                                  |
| PROTOCOL_CAPABILITIES (P1), polymarket-perps probe, versifi |                                                                                                                                                                                                |                                                              |
| Facade hoist (P2); UAC freezegun hardening (P2)             | tracked todos above                                                                                                                                                                            | nothing                                                      |

Recommended next — land MTDS, then the C5/census UAC batch (the remaining P0); the C3 paper-mode run is the
remaining runtime-verification gate before the rule-9 report; deployment-service ships whenever the peer clears
their tf.
