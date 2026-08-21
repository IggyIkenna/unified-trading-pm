---
doc_type: codex-runbook
title: PRIVATE_STREAM_RESYNC_FAILED — execution private-stream resync failed
summary:
  Operator playbook for PRIVATE_STREAM_RESYNC_FAILED (CRITICAL, pages) — after a private-stream reconnect/rotation the
  REST snapshot resync failed, so the PrivateStreamGuard withholds ALL order/position updates (resync-before-trust);
  repeated consecutive failures auto-escalate to KILL_SWITCH_VENUE_DISCONNECT.
status: current
nature: process
asset_group: [meta]
stage: [execution, live]
repos: [execution-service, unified-trading-library]
scope: [admin, engineer]
tags: [runbook, alerting, websocket, execution, positions, resync]
related: [/codex/15-runbooks/incidents/rb_conn_001.md, /codex/04-architecture/autonomous-recovery-matrix.md]
created: 2026-08-21
owner: ikenna@odum-research.com
cadence: Pre-cutover
verifier: execution-service tests/trade_execution/unit/test_private_stream_guard.py
last_executed: never
authoritative_for: [PRIVATE_STREAM_RESYNC_FAILED operator playbook]
referenced_by: []
code_refs: [execution-service/execution_service/trade_execution/private_stream_guard.py]
---

# PRIVATE_STREAM_RESYNC_FAILED — execution private-stream resync failed

## What fired

Execution's `PrivateStreamGuard` opened a new private-stream connection generation (initial / reconnect / rotation)
but the venue REST snapshot resync (positions + open orders) FAILED. The guard is withholding stream updates — the
position view is NOT being stale-trusted; order flow is protected by the freshness gate on the last verified snapshot.

## First 60 seconds

1. Venue + cause from the payload (`details["venue"]`, `details["error"]`, `details["consecutive_failures"]`).
2. Is the venue REST API down (status page / manual snapshot call)? Are the API credentials valid?
3. ≥ 3 consecutive failures → the venue-scoped protective kill is already armed (KILL_SWITCH_VENUE_DISCONNECT).

## Resolve

- Venue REST outage → the guard retries every watchdog interval; recovery is automatic on the first successful resync
  (updates resume only after it — no operator action needed beyond monitoring).
- Credential/permission failure → rotate/repair the API key; the next resync attempt picks it up.
- Killed venue → follow `/codex/15-runbooks/incidents/rb_conn_001.md`; resume ONLY per the autonomous-recovery matrix
  (`manual_unkill` is human-only).

## Success criteria

Resync succeeds (guard logs "snapshot resync complete"), updates flowing again, positions reconcile.
