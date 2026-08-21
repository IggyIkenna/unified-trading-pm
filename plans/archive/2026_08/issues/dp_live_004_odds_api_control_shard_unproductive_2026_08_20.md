---
doc_type: issue
title: >-
  DP-LIVE-004 / DP_CRON_DID_NOT_FIRE reports an unproductive live ODDS_API control
  shard while fan-out data is emitted under child bookmaker/fixture ids
summary: >-
  The live sports shard `mtds-live-sports-odds-api-odds-20260816-145019`
  (ODDS_API, data_type=odds) is actively attempting but has never captured a row.
  The Odds API websocket uses coarse `ODDS_API:SPORT:*` subscription ids as
  polling controls and emits actual data under bookmaker/fixture ids. The live
  runner currently treats an empty coarse control buffer as a real shard, which
  creates misleading empty manifest cells and triggers DP-LIVE-004. The fix must
  suppress only healthy fan-out control empties and retain failure recording.
status: resolved
nature: process
asset_group: [sports]
stage: [live, data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-live-004, dp-cron-did-not-fire, sports, odds-api, fanout]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/sports_satellite_ao_dispatch_batch15_2026_08_17.md,
  ]
created: 2026-08-20
parent_epic: sports_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: slot-10 (data_engineering), 2026-08-21
last_updated: 2026-08-21
locked_since:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/tests/unit/test_websocket_runner.py,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
source: >-
  DP-LIVE-004 escalation agt-a1445b: live shard
  mtds-live-sports-odds-api-odds-20260816-145019, venue=ODDS_API,
  data_type=odds, attempted 0.7h ago, never captured within the 3-day
  staleness budget.
---

# DP-LIVE-004: live Odds API fan-out control buffer is mistaken for a data shard

> **🟢 RESOLVED / ARCHIVED 2026-08-21 (slot-10, data_engineering).** The targeted MTDS fix is shipped at `market-tick-data-service@9097603c86`; the production DP-LIVE-004 dry-run against the named RUNNING shard observed fresh bookmaker fan-out captures and returned `FIRED=[]`. Both todos are complete and no successor work remains.

## What I found

The live sports Odds API connector subscribes using coarse `ODDS_API:SPORT:*`
ids, then fans out incoming data to bookmaker/fixture ids. The runner keeps the
coarse ids as buffers and flushes an empty buffer as an ordinary shard. That
creates an unproductive `ODDS_API` cell even when child shards are the actual
data producers.

## Why it matters

This is false shard accounting, not evidence that the upstream source produced
no data. Suppressing all empty buffers would hide authentication or upstream
failures, so the healthy-control case must be distinguished from a connector
failure and honest-absence handling must remain intact.

## Recommended decision

Land the existing targeted runner/connector fix: mark fan-out connectors,
track their control ids, skip only empty control buffers when no connectivity
gap or upstream failure is present, and add regression tests for both healthy
and failed control buffers. Re-run the focused websocket tests and the MTDS
quality gate before shipping.

## Verification

- [x] [CODE] P1. Ship and verify the fan-out control-buffer fix — `market-tick-data-service@9097603c86` is an
  ancestor of `origin/live-defi-rollout`; the required quality gate completed green with 11,108 passed, 28 skipped,
  1 xpassed, and 17 warnings.
- [x] ✅ [VERIFY] P1. Re-run the DP-LIVE-004 candidate check against the named live shard and confirm no new false
  empty-confirmed rows — `deployment-service`'s production `check_live_capture_productivity` reader ran in dry-run mode
  against `mtds-live-sports-odds-api-odds-20260816-145019` on 2026-08-21. The VM was RUNNING in `asia-northeast1-c`;
  its `ODDS_API/odds` group had `last_captured_at=2026-08-21T02:20:50.647175+00:00` via bookmaker fan-out, 30
  bookmaker groups were also fresh, and the checker returned `FIRED=[]` with exit code 0.

## Progress Log

**2026-08-21 — escalation `agt-a1445b`.** The MTDS fix landed through quickmerge on `origin/live-defi-rollout` as
`9097603c86` (including the connector marker, control-id tracking, healthy-empty suppression, and failure-preserving
regressions). The read-only live candidate check was attempted but timed out before a terminal result; no fresh live
pass is asserted.


**2026-08-21 — verification `dp_live_004_odds_api_control_shard_unproductive-31eee91d7f93`.** Re-ran the production
`deployment-service` DP-LIVE-004 reader in dry-run mode against the named shard. It resolved the running VM and its
per-VM parquet shard, observed fresh captured bookmaker fan-out rows (including the `ODDS_API/odds` source group), and
returned `FIRED=[]` with exit code 0. No new false `empty_confirmed` candidate was emitted.
