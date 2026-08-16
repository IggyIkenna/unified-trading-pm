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
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service]
scope: [engineer, admin]
tags: [defi, data-pipeline-health, capture-cron, instruments-service, staleness]
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
resolved_by:
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

- [ ] [DIAG] P1. **Diagnose why the DeFi `instrument_availability/by_date/` capture job has produced no new
      `day=` partitions since 2026-07-26** — check the Cloud Scheduler/Cloud Run job that populates this bucket
      (likely `instruments-daily-backfill` or `instruments-service-daily-trigger`, per the RESUME-runbook
      scheduler list in `master_data_canonicalisation_migration_catalogue_2026_06_07.md`) for its enabled/paused
      state, recent execution history, and error logs. Repo: instruments-service + deployment-service (scheduler
      config). parent_epic: defi_master.
- [ ] [DATA] P1. **Once root-caused, resume/fix the capture job and backfill the 2026-07-26→now gap** for DeFi
      instrument availability, following the same honest-absence (`record_captured`/`record_zero_rows`/
      `record_failed`) contract every other capture job uses. Repo: instruments-service. parent_epic: defi_master.
      Done-when: `build_instrument_catalogue --asset-group defi --dry-run` no longer fires
      `CATALOGUE_STALE_BY_DATE`.

## Progress Log

- **2026-08-16 (slot-13, GATE C re-verify side-finding)**: filed from a live GCS read while re-verifying GATE C's
  by_date-emptiness gate; not investigated further this session (out of scope for the dispatching DIAG task).
