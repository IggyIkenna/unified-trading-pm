---
doc_type: issue
title: Polymarket book_snapshot_5 live stream dead since 2026-06-23 18:09 UTC
summary:
  The `prediction-live-polymarket-book-snapshot-5-20260623-130258` VM has been running since 2026-06-23 13:06 UTC but
  has captured NO `book_snapshot_5` data since 2026-06-23 18:09 UTC (2+ days of gap...
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [prediction, live-trading, monitoring, book-microstructure, data-status, observability, self-healing]
related: [prediction_venue_perps_and_live_clob_depth_2026_06_20]
created: 2026-06-26
parent_epic: predictions_master
priority: P1
source: [live prediction-VM data-gap monitoring finding 2026-06-26]
assigned_vm:
resolved_by: >-
  deployment-service live_stream_watcher.py check_live_stream_stale() DP-LIVE-001 monitoring (2026-06-26, LDR CI green)
  + all 5 prediction live VMs relaunched on fresh MTDS tarball 05e84bc5
locked_by: live-defi-rollout
severity: P1
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## Summary

The `prediction-live-polymarket-book-snapshot-5-20260623-130258` VM has been running since 2026-06-23 13:06 UTC but has
captured NO `book_snapshot_5` data since 2026-06-23 18:09 UTC (2+ days of gap). No alert is firing.

## Evidence

- GCS files: 468 parquet files captured on 2026-06-23 between 13:06..18:09 UTC
- Days 2026-06-24, 2026-06-25, 2026-06-26: **0 files**
- VM heartbeat: `PIPELINE_HEARTBEAT` every 60s — VM IS alive
- Manifest shard: 17,737 entries all with
  `capture_status=empty_confirmed, row_count=0, attempted_at=2026-06-23T18:09:01`
- VM log: only ManifestWriter updates + repeated aiohttp DeprecationWarnings (no ERROR lines)

## Root Cause (likely)

The Polymarket CLOB websocket subscriptions for `book_snapshot_5` dropped after ~5h of operation and the MTDS reconnect
logic failed to re-establish them. The aiohttp DeprecationWarning
(`parameter 'timeout' of type 'float' is deprecated, please use 'timeout=ClientWSTimeout(ws_close=...)'`) may indicate a
deeper websocket lifecycle issue.

The VM is healthy at the OS level (heartbeat firing) but the Python event loop's websocket subscriptions are silently
dead — no new WS messages → no new parquet files.

## Alert Gap

The existing monitoring only checks:

1. `availability_index.parquet` freshness (mtime < 180 min) — the prediction consolidator IS updating this regularly, so
   the cron-fired check passes
2. VM heartbeat presence — the VM IS heartbeating

MISSING: A check that a live VM's data_type has received new rows within a reasonable window (e.g., `book_snapshot_5`
should have data every hour for at least some instruments).

## Recommended Actions

### Operator Decision Required (relaunch risk)

- **Relaunch `prediction-live-polymarket-book-snapshot-5-20260623-130258`** with the latest MTDS tarball
  (2026-06-26T17:30:46Z, sha `1e525d21`). This will cause a brief gap on the `book_snapshot_5` stream but restore
  coverage.
- **Also relaunch** the other 4 live prediction VMs (trades/Kalshi/Polymarket) that are running 3-day-old tarballs, per
  the operator's "latest code" requirement.

### Monitoring Fix (agent-executable)

Add a `DP_LIVE_DATA_STALE` alert check in `meta_watchers.py` that:

- Reads the per-VM shard for each live VM running a `book_snapshot_5` or `trades` shard
- Alerts if `MAX(attempted_at)` for any key data_type is older than `max_stale_hours` (e.g., 4h for live streams)
- This catches the "VM alive but data dead" failure mode that heartbeat checks miss

## Resolution (2026-06-26)

1. **DP-LIVE-001 monitoring shipped** — `deployment-service` `live_stream_watcher.py` `check_live_stream_stale()` reads
   `_index/per_vm/<vm>.parquet` `MAX(attempted_at)` and alerts via `DP_CRON_DID_NOT_FIRE` (label
   `live-data-stale::<vm_name>`) when data is silent >4h. Wired into `cli.py` meta sweep. LDR commit shipped 2026-06-26,
   CI green.
2. **All 5 prediction live VMs relaunched** with fresh tarball `05e84bc5` (2026-06-26T20:07Z from MTDS LDR `05e84bc5`):
   - `prediction-live-polymarket-book-snapshot-5-20260626-201038`
   - `prediction-live-polymarket-trades-20260626-201051`
   - `prediction-live-kalshi-book-snapshot-5-20260626-201105`
   - `prediction-live-kalshi-trades-20260626-201119`
   - `prediction-arb-detector-20260626-201140`
3. **T+10 VERIFIED (2026-07-12 correction)** — was: "T+10 verification pending (VMs booting)." A deeper
   `InMemoryTransport` data-loss bug was found AFTER the 2026-06-26 20:10Z relaunch above (plan commit `3b956b70`
   silently routed ALL book_snapshot_5 ticks to InMemoryTransport instead of GCS — confirmed zero GCS files that day,
   manifest showing only 26/148162 `captured` rows, all with `pubsub://persist-*` blob_path, not `gs://`); fixed in
   `market-tick-data-service@3043f2dc`, and both VMs were relaunched a SECOND time on that fixed tarball:
   - `prediction-live-polymarket-book-snapshot-5-20260626-224659` — T+10 VERIFIED 23:20Z 2026-06-26: writing GCS
     parquets (5 parquets growing, 148162-token subscription progressing ~21/s).
   - `prediction-live-kalshi-book-snapshot-5-20260626-224718` — T+10 VERIFIED 23:20Z 2026-06-26: **2107 GCS parquets**
     written.

   Evidence: `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` Progress Log § "2026-06-26 (autonomous
   /autonomous) — Plan04 InMemoryTransport bug fixed, DP-LIVE-002 alert shipped, VMs verified" (source lines ~380-399).
   Finding #242, plan-reconciliation `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50
   reclassified" blanket ruling.

## Related

- `prediction_venue_perps_and_live_clob_depth_2026_06_20.md` — parent plan
- VM launched 2026-06-23 before latest MTDS code (sha `1e525d21`, 2026-06-26)
