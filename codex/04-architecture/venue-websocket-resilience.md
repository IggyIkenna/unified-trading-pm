---
doc_type: codex-ssot
title: Venue websocket resilience
summary: "Ws-resilience SSOT: per-venue WsProtocolSpec axis on the capability registry (ping/pong, forced-disconnect,
  auth cadence, duplicate-subscription feasibility, REST gap backfill), the UTL WsSessionManager runtime (staleness
  detect -> retry ladder -> rotate; make-before-break where the venue permits, else break-then-make + gap backfill;
  proactive lifetime rotation; external rotation-request sentinel), the rotate-websocket:<source> Layer-0 binding in
  the freshness registry, and the alert/kill-switch escalation (WS_ROTATION_* / PRIVATE_STREAM_RESYNC_FAILED ->
  KILL_SWITCH_VENUE_DISCONNECT)."
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [data, live, execution]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    market-tick-data-service,
    execution-service,
    deployment-service,
    alerting-service,
  ]
scope: [engineer]
tags: [websocket, staleness, rotation, venue-capability, feed-sla, alerting, kill-switch, live-trading]
related:
  [
    /codex/03-services/venue-capability-registry.md,
    /codex/03-observability/data-feed-sla-registry.md,
    /codex/03-observability/alerting.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
  ]
created: 2026-08-21
authoritative_for: [ws-protocol registry axis, ws session rotation policy, rotate-websocket Layer-0 action]
referenced_by: []
owner:
last_reviewed: 2026-08-22
code_refs:
  [
    unified-api-contracts/unified_api_contracts/registry/ws_protocol.py,
    unified-trading-library/unified_trading_library/streaming/ws_session_manager.py,
    unified-trading-library/unified_trading_library/streaming/ws_rotation_request.py,
    market-tick-data-service/market_tick_data_service/live/_ws_session_bridge.py,
    execution-service/execution_service/trade_execution/private_stream_guard.py,
    deployment-service/scripts/recovery/rotate_websocket.py,
  ]
---

# Venue websocket resilience

> Plan of record: `/plans/active/venue_websocket_resilience_and_error_code_mapping_2026_08_21.md` (archives when done —
> THIS doc is the durable SSOT).

## The problem

A venue websocket goes silently stale — no close frame, no error, just no messages. Execution's position view stops
updating; live capture windows silently thin out. Recovery must be venue-aware: each venue publishes a different ws
contract (ping/pong cadence, forced-disconnect window, listen-key auth refresh, whether a duplicate overlapping
subscription is allowed) and a different REST surface to close the gap a rotation leaves.

## The four pieces

### 1. Registry axis — `WsProtocolSpec` (UAC)

`unified_api_contracts/registry/ws_protocol.py`, attached per venue as `SourceCapability.ws_protocol` in
`registry/capability_declarations/`; resolve via `resolve_ws_protocol(source)` after
`capability_data.bootstrap_capabilities()` (raises for an UNKNOWN source; returns `None` for
registered-but-undeclared). Honest provenance: every field defaults `None` = NOT researched / not published — never a
guess; `doc_url` + `doc_retrieved` carry the citation. `model_config extra="forbid"` makes a declaration typo an
import-time error, never silent data loss (a mis-named okx field was silently dropped by pydantic's default before
2026-08-21). A venue with NO websocket surface records that explicitly in `notes` (`no_websocket_surface — ...`), it
does not omit the spec.

### 2. Error-code registry (UAC)

`canonical/crosscutting/errors/` — `VenueErrorClassification` rows with `surface` (rest/ws/fix) + `doc_url`
provenance; `classify_venue_error(venue, code)` resolves them. The completeness bar is the venue's PUBLISHED table
transcribed code-by-code (operator ruling 2026-08-21), landed as per-venue `_<family>_<venue>_codes*.py` sibling files
merged additively at each family module's EOF. Consumers classify per
`/codex/04-architecture/shard-level-failure-isolation.md`.

### 3. Runtime — `WsSessionManager` (UTL) + adapters

`unified_trading_library/streaming/ws_session_manager.py` owns policy for ONE venue session; the owning service keeps
its own transport and feeds `record_message()` from its read loop:

- staleness watchdog (explicit override, else freshness `max_age`, else 60s) → reconnect ladder (exponential backoff)
  → rotation;
- rotation is make-before-break when the venue's `duplicate_subscription_allowed` (zero drop), else break-then-make
  plus a `gap_backfill(gap_start, gap_end)` callback (operator gap-policy ruling 2026-08-21);
- proactive rotation at `lifetime_rotation_fraction` (0.9) of the venue's forced-disconnect window — a planned
  rotation replaces an unplanned drop;
- auth refresh on the spec cadence (listen-key keepalive family);
- external rotation requests consumed each watchdog tick from the `ws_rotation_request` file sentinel
  (`streaming/ws_rotation_request.py`; same-host, broker-free — the recovery path must not depend on the systems it
  heals).

Adapters:

- **MTDS live** — `market_tick_data_service/live/_ws_session_bridge.py`, wired by default in the websocket-streaming
  handler. Honest gap accounting by construction: every bridge-driven re-open raises a rotation flag the runner ORs
  into `pop_reconnect_flag()`'s STALE-window marking. Single-connector adapter → the venue's duplicate-subscription
  fact is downgraded to break-then-make at the session layer (a dual-connector overlap needs a connector-factory
  refactor — tracked in the plan). The rotation threshold is deliberately conservative (`max(60s, 4 x max_age)`) —
  rotation is heavier than the DATA_STALE flag; the connectivity watchdog + freshness gate own short gaps.
- **Execution private streams** — `execution_service/trade_execution/private_stream_guard.py`: resync-before-trust —
  after EVERY connection generation the REST snapshot resync is awaited BEFORE any update is yielded; a failed resync
  withholds updates and pages.

### 4. Recovery + alerting integration

- **Freshness-registry binding vocabulary** (`internal/reference/data_freshness.py`): `refetch-feed:<source>` (REST
  re-pull) or `rotate-websocket:<source>` (ws-session rotation) — the ws-sourced CeFi market-tick venues bind
  rotation, because a REST re-pull cannot revive a dead socket. `alerting-service/rules/feed_refetch_rules.py`
  resolves the bound action from the contract (legacy refetch id as fallback for unknown feeds).
- **Layer-0 action**: `ActionType.ROTATE_WEBSOCKET` → `deployment-service/scripts/recovery/rotate_websocket.py`
  (RB-CONN-001; storm guards mirror `refetch_feed`; drops the rotation-request sentinel — SUCCEEDED means "rotation
  requested"; completion is observable as the manager's ROTATION_COMPLETED + the feed's freshness recovering).
- **Alert family**: `WS_ROTATION_COMPLETED` (INFO, log/digest — one event per rotation EPISODE, never per-tick),
  `WS_ROTATION_FAILED` (HIGH, pages), `PRIVATE_STREAM_RESYNC_FAILED` (CRITICAL, pages). Feed-stale itself rides the
  existing DATA_STALE / FEED_UNHEALTHY criticality-tiered rules.
- **Kill-switch escalation**: ≥3 consecutive rotation OR resync failures in the `PrivateStreamGuard` emit
  `KILL_SWITCH_VENUE_DISCONNECT` (VENUE-scope protective kill; arming autonomous, resume per
  `/codex/04-architecture/autonomous-recovery-matrix.md` — G8 row).

## Invariants

1. A rotation gap is ALWAYS surfaced (STALE window / gap_backfill request) — never silently spanned.
2. No private-stream update is yielded from an un-resynced connection generation.
3. Registry facts are doc-cited or `None` — never guessed; declaration typos fail at import (`extra="forbid"`).
4. Rotation policy derives from the venue's declared `WsProtocolSpec`, never per-service hardcodes.
5. The out-of-process rotation path (Layer-0 sentinel) reuses the SAME in-process policy — one rotation code path.

## Playbooks

`/codex/15-runbooks/alerting/ws_rotation_failed.md` · `/codex/15-runbooks/alerting/private_stream_resync_failed.md` ·
`/codex/15-runbooks/incidents/rb_conn_001.md`.
