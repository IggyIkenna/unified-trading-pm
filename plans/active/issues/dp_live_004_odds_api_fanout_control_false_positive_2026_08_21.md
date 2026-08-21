---
doc_type: issue
title: "DP-LIVE-004 false-positive for live Odds API fan-out control shards"
summary: >-
  The live Odds API shard was reported as still attempting but never captured because the productivity watcher
  compared the coarse ODDS_API polling control instrument with captured bookmaker fan-out rows. The writer was
  producing data; healthy control buffers were being materialised as misleading empty manifest cells.
status: open
nature: process
asset_group: [sports]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, DP-LIVE-004, DP_CRON_DID_NOT_FIRE, sports, odds-api, false-positive]
related:
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
created: 2026-08-21
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P1
resolved_by:
locked_by:
context_scope:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/honest-absence-downstream-handling.md
  - market-tick-data-service/market_tick_data_service/live/websocket_runner.py
source:
  - DP-LIVE-004
  - agt-a1445b
---

# DP-LIVE-004 false-positive for live Odds API fan-out control shards

## What I found

The alert named `mtds-live-sports-odds-api-odds-20260816-145019`, `venue=ODDS_API`, and `data_type=odds` as
unproductive. The live writer's own verification shows fresh bookmaker-fanout parquet objects and manifest rows.
The connector uses coarse `ODDS_API:SPORT:<league>` instrument IDs to drive polling, but emitted ticks are keyed by
bookmaker/fixture IDs. The runner therefore created healthy zero-row manifest entries for polling control IDs and
the productivity watcher did not credit the fan-out rows to the source group.

The inherited slot fix records that distinction explicitly: healthy fan-out control buffers are omitted, while a
non-null upstream failure reason still records `attempted_failed` rather than hiding a real outage.

## Why it matters

This violates the honest-absence contract by turning an internal polling control ID into a user-visible empty shard,
and it can page `DP-LIVE-004` while the live writer is healthy. Suppressing the alert without fixing the writer would
hide a real source failure, so the control-buffer path must preserve failure recording.

## Recommended decision

Ship and verify the fan-out control-buffer fix in `market-tick-data-service`, then re-run the DP-LIVE-004 productivity
check against the live shard. Close the issue only after the healthy control ID no longer creates an empty row and a
simulated upstream failure still creates `attempted_failed`.

## Todos

- [x] [CODE] P1. Ship and verify the fan-out control-buffer fix in `market-tick-data-service` — `market-tick-data-service@9097603c86` + Evidence: `bash scripts/quality-gates.sh --no-fix` passed (11,108 passed, 28 skipped, 82.02% coverage); targeted DP-LIVE-004 read-only check returned `fired=[]` for VM `mtds-live-sports-odds-api-odds-20260816-145019` and showed fresh bookmaker captures through 2026-08-21T01:07:14Z.

## Progress Log

- 2026-08-21T01:07Z — Read the exact per-VM shard from `market-data-tick-sports-prd-central-element-323112` under an 8 GiB/30-second bound. The ODDS_API source group was credited with bookmaker fan-out capture through 01:07:14Z; `check_live_capture_productivity(..., dry_run=True)` returned `fired=[]`. Healthy control buffers are no longer reported as unproductive, while the shipped regression covers preservation of upstream failure recording.
- [ ] [DOCS] P3. Archive this resolved issue under `plans/archive/issues/` after the completion checkbox is shipped.
