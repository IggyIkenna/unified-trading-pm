---
doc_type: issue
title: "DP-LIVE-004 sports ODDS_API fan-out productivity false positive"
created: 2026-08-20
author: data-pipeline-failure
parent_epic: observability_master
assigned_vm: vm-cross-cutting
source:
  - DP-LIVE-004
locked_by: live-defi-rollout
summary: "DP-LIVE-004 flags the productive sports ODDS_API live VM because the detector groups fan-out rows by bookmaker venue while the source attempt rows remain under ODDS_API."
status: resolved
nature: process
asset_group: [sports]
stage: [meta]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-alerts, dp-live-004, sports, odds-api, fan-out]
related:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/sports_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
priority: P1
resolved_by: deployment-service@c4f2b1d048 + market-tick-data-service@9097603c86
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    deployment-service/deployment_service/data_pipeline_monitors/live_stream_watcher.py,
    market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    /plans/active/sports_satellite_ao_dispatch_batch15_2026_08_17.md,
  ]
---

# DP-LIVE-004 sports ODDS_API fan-out productivity false positive

> **ARCHIVED 2026-08-21** — Duplicate closure record; canonical resolution is
> `/plans/archive/2026_08/issues/dp_live_004_odds_api_control_shard_unproductive_2026_08_20.md`.

## What I found

The exact alert target `mtds-live-sports-odds-api-odds-20260816-145019` is healthy and productive in production:

- GCE status is `RUNNING` in `asia-northeast1-c`.
- Its `run.log` has `PIPELINE_HEARTBEAT` entries every minute and per-VM manifest updates every ~10 seconds through 2026-08-20 18:29 UTC.
- Warm event-log objects under `live-events/warm/sports/odds/` continue to arrive, including objects created through 18:28 UTC.
- The MTDS connector explicitly polls source instruments named `ODDS_API:SPORT:{sport_key}`, then emits one tick per `(bookmaker, fixture)` and lazily assigns the bookmaker as the manifest venue.

The DP-LIVE-004 detector in `/deployment-service/deployment_service/data_pipeline_monitors/live_stream_watcher.py` groups the per-VM manifest by `(venue, data_type)`. That creates a legitimate `venue=ODDS_API, data_type=odds` attempt group, but captured ticks are recorded under bookmaker venues (for example `BETRIVERS`, `LIVESCOREBET`, and `VIRGINBET`). The detector therefore sees the source-level attempt group as “never captured” even while bookmaker-level groups are actively captured and GCS objects are advancing.

## Why it matters

This is an alert correctness failure, not evidence of missing sports data. Repeated pages can trigger an unnecessary credential/escalation response against a live producer that is writing successfully. Suppressing the alert globally would hide genuine dead feeds, so the fix must preserve DP-LIVE-004 for non-fan-out shards.

## Recommended decision

Update the productivity oracle in `deployment-service` to model source-to-output fan-out explicitly. For the registered sports `ODDS_API` live shard, treat recent captured bookmaker rows with the same VM, `data_type`, and live source/pipeline mode as productivity evidence for the source group, or emit productivity findings at the fan-out output-group grain. Add a regression fixture matching the exact `ODDS_API` source rows plus bookmaker captured rows. No MTDS writer change is indicated by this investigation.

## Evidence

- MTDS source fan-out: `/market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py` (`_parse_fixture_response`) and `/market-tick-data-service/market_tick_data_service/live/websocket_runner.py` (`_register_lazy_buffer`).
- Detector grouping: `/deployment-service/deployment_service/data_pipeline_monitors/live_stream_watcher.py` (`_read_vm_shard_group_activity`, `check_live_capture_productivity`).
- Runtime VM: `mtds-live-sports-odds-api-odds-20260816-145019`; per-VM shard `_index/per_vm/mtds-live-sports-odds-api-odds-20260816-145019.parquet`.

## Todos

- [x] [CODE] P1. Fix DP-LIVE-004 productivity accounting for sports ODDS_API source-to-bookmaker fan-out in deployment-service; preserve non-fan-out detection and add focused regression tests. — deployment-service@c4f2b1d048 + Evidence: quality-gates.sh --no-fix ALL QUALITY GATES PASSED; 3652 passed, 5 skipped
- [x] [DATA] P1. Re-run the live productivity audit against the exact VM and verify the false page clears while bookmaker-level capture remains fresh. — deployment-service monitor read-only exact-VM check at 2026-08-20T23:43Z; running=true, bookmaker groups had fresh last-captured timestamps through 23:43Z, and the ODDS_API/odds source group was credited with fan-out capture at 23:43Z. Evidence: bounded direct invocation of cli._list_running_vms(), build_running_live_shards(), and _read_vm_shard_group_activity(); no productivity finding for the target.

## Progress Log

- 2026-08-20T23:43Z — Verified the exact VM is RUNNING and productive. The per-VM shard contained fresh captured odds rows for 30 bookmaker venues; the patched ODDS_API/odds source group reported last_captured_at=2026-08-20 23:43:03Z, so the false positive is cleared. The check ran read-only under a 2 GiB cap and 120-second timeout.

- 2026-08-21T02:36Z — The latest successful `uts-prod-dp-meta-watchers-gsj6w` execution completed with `meta sweep complete`
  and emitted no DP-LIVE-004 finding for the exact VM. This record is resolved and superseded by the archived canonical
  fan-out false-positive record at `/plans/archive/2026_08/issues/dp_live_004_odds_api_control_shard_unproductive_2026_08_20.md`.
