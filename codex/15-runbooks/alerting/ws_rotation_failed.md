---
doc_type: codex-runbook
title: WS_ROTATION_FAILED — websocket session rotation failed
summary: Operator playbook for WS_ROTATION_FAILED (HIGH, pages) and its INFO sibling WS_ROTATION_COMPLETED — the
  WsSessionManager could not replace a stale websocket session after the reconnect ladder; repeated consecutive
  failures auto-escalate to the venue-scoped protective kill (KILL_SWITCH_VENUE_DISCONNECT).
status: current
nature: process
asset_group: [meta]
stage: [live]
repos: [market-tick-data-service, execution-service, unified-trading-library, deployment-service]
scope: [admin, engineer]
tags: [runbook, alerting, websocket, rotation, connectivity]
related: [/codex/15-runbooks/incidents/rb_conn_001.md, /codex/04-architecture/autonomous-recovery-matrix.md]
created: 2026-08-21
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: unified-api-contracts tests/internal/unit/test_ws_resilience_alert_rules.py
last_executed: never
authoritative_for: [WS_ROTATION_FAILED operator playbook]
referenced_by: []
code_refs:
  [
    unified-trading-library/unified_trading_library/streaming/ws_session_manager.py,
    deployment-service/scripts/recovery/rotate_websocket.py,
  ]
---

# WS_ROTATION_FAILED — websocket session rotation failed

## What fired

The owning `WsSessionManager` (MTDS live ws-session bridge or execution `PrivateStreamGuard`) exhausted the reconnect
ladder on a silently-stale websocket and the replacement connection ALSO failed. The blind window is growing; the
enclosing capture window is already marked STALE (honest gap accounting).

## First 60 seconds

1. Identify venue + producer from the alert payload (`details["venue"]`; MTDS shard vs private stream).
2. Check the venue's status page for a ws outage; probe REST reachability for the same venue.
3. Check the repeat count — `consecutive_failures` ≥ 3 auto-escalates to KILL_SWITCH_VENUE_DISCONNECT (venue-scoped
   protective kill; `/codex/15-runbooks/incidents/rb_conn_001.md` owns that flow).

## Resolve

- Venue-side outage → wait it out; the manager keeps retrying; data gaps are recorded honestly and re-pulled per the
  freshness registry's Layer-0 ladder (`refetch_feed` / `rotate_websocket`).
- Our-side cause (auth expiry, IP ban, subscription cap — check the venue's `WsProtocolSpec` limits) → fix the
  credential/limit, then request a rotation explicitly:
  `deployment-service/scripts/recovery/rotate_websocket.py --feed_id <source>`.
- Escalated to a venue kill → follow `/codex/15-runbooks/incidents/rb_conn_001.md`; resume ONLY per the
  autonomous-recovery matrix (`manual_unkill` is human-only).

## Success criteria

WS_ROTATION_COMPLETED observed for the venue; feed freshness back under its SLA; no repeat within the breaker window.
