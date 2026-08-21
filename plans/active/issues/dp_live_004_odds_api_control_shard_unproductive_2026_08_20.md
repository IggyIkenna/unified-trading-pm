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
status: open
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
resolved_by:
last_updated: 2026-08-20
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
