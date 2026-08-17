---
doc_type: issue
title: DeFi instruments-store by_date capture cron appears stalled — newest day is 21 days old
summary: >-
  Discovered while re-verifying GATE C (defi_instruments_store_v9_gate_c_reverify_ao_dispatch_2026_08_16.md):
  `build_instrument_catalogue --asset-group defi --dry-run` self-reports a CATALOGUE_STALE_BY_DATE warning —
  the newest `instrument_availability/by_date/` day in the `instruments-store-defi-prd-{pid}` bucket is
  2026-07-26, 21 days old as of 2026-08-16, with the tool's own log line calling out "upstream download cron
  unhealthy". This is a live data-pipeline health issue (data-pipeline-correctness-hard-rule heartbeat), separate
  from GATE C's `_index` schema-version status.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [defi, data-pipeline-health, capture-cron, instruments-service, staleness, false-positive]
related:
  [
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
  ]
created: 2026-08-16
author: slot-13 (Claude Code session, dispatched via defi_instruments_store_v9_gate_c_reverify_ao_dispatch_2026_08_16.md)
parent_epic: defi_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: none
depends_on: []
locked_by:
resolved_by: slot-32
last_updated: 2026-08-16
locked_since:
context_scope:
  [
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    instruments-service/scripts/build_instrument_catalogue.py,
  ]
source: >-
  Live re-verify of defi GATE C (defi_instruments_store_v9_gate_c_reverify_ao_dispatch_2026_08_16.md's
  [DIAG] P1 todo), run against real prod GCS 2026-08-16.
---

# DeFi instruments-store by_date capture cron appears stalled

> **🟢 RESOLVED 2026-08-16 (slot-32) — FALSE POSITIVE, capture cron was never unhealthy.** The `latest_day=2026-07-26
> (21d old)` staleness signal below was an artifact of running the diagnostic `--max-blobs 5` flag: the by_date walk
> is path-sorted starting at the incremental window's start day, and a single day has far more than 5 per-venue
> parquets — so a 5-blob-truncated sample can NEVER contain a day past the window start, regardless of how fresh the
> real data is. A real (untruncated) `build_instrument_catalogue --asset-group defi --dry-run` run the same day found
> 1903 by_date parquets covering every day through 2026-08-16 (today) with **zero** `CATALOGUE_STALE_BY_DATE`
> signal, and a direct per-day GCS check confirmed populated `day=` partitions for 2026-07-26, 07-27, 08-14, 08-15,
> AND 08-16. The `is-daily-enum-defi` Cloud Scheduler job (13:30 UTC daily) has completed successfully every day
> checked (2026-08-08 through 2026-08-16), each run writing thousands of records (e.g. 6215 records/82 venues for
> 2026-08-16). **Root cause + fix**: `_warn_coverage_horizon` (the staleness check) was being fed `window_day_counts`
> from the truncated walk with no truncation awareness — fixed in `instruments-service@01a2c186` to skip the check
> when `--max-blobs` is set (a truncated sample is diagnostic-only and structurally cannot support a staleness
> verdict). See Progress Log for full evidence. **No backfill needed** — there was never a gap.

## What I found

Running `build_instrument_catalogue.py --asset-group defi --dry-run --max-blobs 5` against the live
`instruments-store-defi-prd-central-element-323112` bucket produced:

```
Incremental window: day>=2026-07-26 (prev catalogue rows=78449 mtime=2026-08-16T01:01:55.541000+00:00)
Found 5 by_date parquet(s) to roll up (workers=16)
EVENT {'event': 'CATALOGUE_STALE_BY_DATE', 'reason': 'latest_day_too_old', 'latest_day': '2026-07-26', 'age_days': 21}
WARNING CATALOGUE_STALE_BY_DATE: defi newest by_date day is 2026-07-26 (21d old) — upstream download cron unhealthy
```

The catalogue builder's OWN staleness guard is firing — as of 2026-08-16, the newest `day=` partition under
`instrument_availability/by_date/` in the prd bucket is 2026-07-26, meaning no new DeFi instrument-availability
snapshot has been captured in 21 days. This is a distinct signal from GATE C's `_index/availability_index.parquet`
manifest file, which IS being actively rewritten (routine hourly consolidator, last write 2026-08-16T22:01Z) —
the manifest consolidator is healthy, but the raw upstream CAPTURE job that produces the `by_date/` snapshots
the manifest consolidates FROM appears to have stopped producing new days.

This was NOT the subject of my dispatch (`defi_instruments_store_v9_gate_c_reverify_ao_dispatch_2026_08_16.md`,
scoped to GATE C re-verification only) — surfaced as a side-finding while checking whether
`instrument_availability/by_date/` was empty (it is not; 78,449 rows already rolled up), so I did not
investigate the capture-job root cause further this session.

## Why it matters

Per CLAUDE.md's data-pipeline-correctness HARD RULE ("data pipeline correctness is the heartbeat... an audit's
issues are fixed in FULL, no deadline deferrals"), a 3-week-stalled capture pipeline for an entire asset_group's
instrument-availability data is a live correctness gap, not a cosmetic staleness note — every day since
2026-07-26 that DeFi instruments should have new availability rows recorded is silently NOT being captured,
which will show up downstream as false `expected_unattempted`/gap cells once GATE C's `--apply-write` seed
eventually runs (the seed candidate-count reads from this same by_date corpus).

## Recommended decision

- [x] ✅ [DIAG] P1. **CLOSED 2026-08-16 (slot-32) — FALSE POSITIVE, not a broken cron.** Checked
      `is-daily-enum-defi` (the actual capture job — `deployment-service/terraform/gcp/daily_is_enumeration_scheduler.tf`,
      NOT `instruments-daily-backfill`/`instruments-service-daily-trigger`, both of which are unrelated/legacy):
      Cloud Scheduler ENABLED (`30 13 * * *` UTC), Cloud Run Job execution history 100% `Completed=True` every day
      2026-08-08→2026-08-16 (`gcloud run jobs executions list`), and today's execution log shows
      `instruments: date=2026-08-16 wrote 6215 records across 82 venues`. Root cause of the false alarm: the
      original diagnosis ran `build_instrument_catalogue.py --dry-run --max-blobs 5` — the diagnostic
      `--max-blobs` flag truncates the by_date walk to 5 path-sorted parquets, which (since paths sort by day and
      a day has 80+ per-venue shards) can never contain a day past the incremental window's start — so the
      staleness heuristic's `latest_day` was mechanically pinned to `2026-07-26` (the window start) regardless of
      real freshness. Repo: instruments-service (root-cause), deployment-service (scheduler config, confirmed
      healthy, no change needed). parent_epic: defi_master.
- [x] ✅ [DATA] P1. **CLOSED 2026-08-16 (slot-32) — no gap existed, no backfill needed; done-when condition
      independently verified.** Direct per-day GCS checks (`instrument_availability/by_date/day=<D>/...` under
      `instruments-store-defi-prd-central-element-323112`) confirmed populated partitions for 2026-07-26, 07-27,
      08-14, 08-15, and 08-16 — every day sampled has data, there was never a 2026-07-26→now gap to backfill.
      Done-when condition met and reverified: a real (untruncated) `build_instrument_catalogue.py --asset-group
      defi --dry-run` (1903 by_date parquets rolled up, 78449→78797 rows, monotonic guard ACCEPT) emitted **zero**
      `CATALOGUE_STALE_BY_DATE` events. Shipped the actual fix (root cause: the staleness check had no truncation
      awareness) — **instruments-service@01a2c186** (`_warn_coverage_horizon` now skipped when `--max-blobs` is
      set, with a log line explaining why, so a future diagnostic-truncated dry-run can't manufacture the same
      false alarm). Repo: instruments-service. parent_epic: defi_master.

## Progress Log

- **2026-08-16 (slot-13, GATE C re-verify side-finding)**: filed from a live GCS read while re-verifying GATE C's
  by_date-emptiness gate; not investigated further this session (out of scope for the dispatching DIAG task).
- **2026-08-16 (slot-32, DIAG+DATA closure)**: Root-caused as a false positive, not a real capture-cron outage.
  Evidence trail: (1) `gcloud scheduler jobs list` confirmed `is-daily-enum-defi` ENABLED (the real capture job per
  `daily_is_enumeration_scheduler.tf`'s own docstring — writes `instrument_availability/by_date/` + `_index/per_vm/`
  shards; `instruments-daily-backfill`, the job the todo's RESUME-runbook pointer suggested checking, is a separate
  PAUSED legacy job unrelated to this bucket/prefix). (2) `gcloud run jobs executions list --job=is-daily-enum-defi`
  showed 10/10 recent executions `Completed=True`. (3) `gcloud logging read` on today's (2026-08-16) execution
  showed a clean run ending `instruments: date=2026-08-16 wrote 6215 records across 82 venues` /
  `IS daily enumeration DONE OK`. (4) Direct GCS prefix checks (via UTL `cloud_interface.get_storage_client()`,
  never a raw `gcloud storage`/`gsutil` CLI call per the storage-code HARD RULE) on
  `instrument_availability/by_date/day=<D>/` for 2026-07-26, 07-27, 08-14, 08-15, 08-16 all returned populated
  blobs. (5) Traced the false alarm to `build_instrument_catalogue.py`'s `--max-blobs` diagnostic flag: the by_date
  walk is path-sorted, so a 5-blob truncation can only ever see the incremental window's start day
  (`_iter_by_date_snapshots(..., max_blobs=max_blobs)` feeds `_tee_day_counts` → `window_day_counts`, which
  `_warn_coverage_horizon` then reads as if it were the full window). (6) Confirmed via a real untruncated dry-run
  (wrapped under `run-bounded-analysis.sh` per the memory-bounding HARD RULE): 1903 parquets found, 78449→78797
  rows, monotonic guard ACCEPT, **no** `CATALOGUE_STALE_BY_DATE` event. Shipped the fix — guard
  `_warn_coverage_horizon`'s call site on `max_blobs is None`, with an explanatory log line on skip — QG green,
  landed **instruments-service@01a2c186** (verified ancestor of `origin/live-defi-rollout`). Both todos closed;
  issue fully resolved.
