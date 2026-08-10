---
doc_type: issue
title: "Features-Sports: compute_features hard-fails on missing upstream fixtures for today's date"
summary: >-
  VM features-sports-sports-2026-20260810-051126 (backfill: 2026-01-01 → 2026-08-10) terminated exit_code=1 because
  compute_features hard-fails on missing upstream fixtures for today's date (2026-08-10) while
  gcs_read_reference_fixtures handles it gracefully with recovery=skip. Relaunched with end_date=2026-08-09 as
  mitigation.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [issue, dp-vm-001, features, sports, honest-absence, exit-code-1]
related:
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
created: "2026-08-10"
author: slot-26
source:
  - agt-af22dd (DP-VM-001 escalation)
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
parent_epic: infrastructure_master
assigned_role: data_engineering
drift_direction: fix
resolved_by: ""
locked_by: ""
depends_on: []
---

# Features-Sports: compute_features hard-fails on missing upstream fixtures for today's date

**Created**: 2026-08-10 | **Severity**: P1 | **Escalation**: agt-af22dd

## What I found

VM `features-sports-sports-2026-20260810-051126` (backfill: 2026-01-01 → 2026-08-10) terminated `exit_code=1` at
2026-08-10T08:02:33Z after ~2h45m runtime.

**Root cause**: The VM successfully processed dates 2026-08-08 and 2026-08-09, but when it reached **2026-08-10**
(today), ALL 17/17 upstream reference-data entities from instruments-service were missing (not yet written for today).
Two code paths handled this differently:

- `gcs_read_reference_fixtures`: **graceful** — logged `ERROR [HIGH]` with `recovery=skip`, continued to next entity
- `compute_features`: **hard-fail** — logged `ERROR [HIGH]` then `Processing failed` → `exit_code=1`

This is an inconsistent error-handling contract: the same missing-upstream condition is recoverable in one path and
fatal in another. `compute_features` should treat missing upstream fixtures for today's date the same way — record
honest absence and continue, not halt the entire run.

## Why it matters

Every backfill VM whose `end_date` includes today will fail with `exit_code=1` if the instruments-service hasn't written
today's reference data yet. This is a deterministic failure that will recur daily and trigger spurious DP-VM-001 alerts.

## What I did (immediate mitigation)

Relaunched as `features-sports-sports-20260810-120320` with `--end-date 2026-08-09` (yesterday) — RUNNING as of
2026-08-10T12:04 UTC. The VM will complete cleanly on dates through yesterday. Today's data will be captured by
tomorrow's run once upstream data exists.

## Recommended fix

In `features-service`, `compute_features` should handle missing upstream fixtures for today's date with honest-absence
recording (`record_empty` / `EMPTY`) rather than a hard error — consistent with how `gcs_read_reference_fixtures`
already handles the same condition. Target repo: `features-service`.

## Resolution (slot-18, escalation agt-af22dd, 2026-08-10)

**Root cause confirmed at the code site.** `DependencyError` (a plain `Exception` subclass from UTL) escapes the
per-shard isolation in `features-service/.../batch_handler.py`: `_run_feature_group` / `_run_reference_tables` catch
`(ValueError, TypeError, KeyError, AttributeError, RuntimeError)` per table, so the `DependencyError` raised by
`gcs_reader` for the REQUIRED `fixtures` entity propagates out of the day shard → `compute_features` returns
success=False → `run()` → `Processing failed` → exit_code=1. That is why the same missing-upstream condition is graceful
in the reference-load path but fatal in the feature-group compute path.

**Fix committed (features-service @ `305d897a`, quickmerge pending QG):** add `DependencyError` to
`_run_feature_group`'s per-shard failure tuple — the generic handler already routes to `manifest.record_failed(...)`
(retryable `attempted_failed`, never `record_empty` — the upstream is merely lagging, not confirmed-absent) + `continue`
(shard isolation). A backfill whose `end_date` includes today now records today's feature groups as retryable-failed and
completes exit 0; tomorrow's run recomputes them once upstream exists. (The reference-table phase needs no change — its
exports read in-memory fetched data and never raise DependencyError; the escape was from the feature-group compute path
re-reading fixtures via `read_reference_entity`.) Regression test added in `tests/sports/unit/test_batch_handler.py`
(`test_run_feature_group_records_failed_on_dependency_error`). This supersedes the earlier `record_empty` suggestion —
`record_failed` is the honest route for a lagging upstream (a false `empty_confirmed` would block the recompute).

**Relaunch — COMPLETED SUCCESSFULLY.** The 12:03 mitigation attempt (`features-sports-sports-20260810-120320`) never
actually launched — only `TARBALL_PINS.json` exists in its log dir (no instance, no run.log; aborted at the launcher
preflight/tarball gate — the `features-service` code tarball was stale and the launch aborted; the 13:52 relaunch
republished it). Relaunch #1 (`features-sports-sports-20260810-135246`, SPOT, `--end-date 2026-08-09`) was **PREEMPTED
3.5 min after creation** (`compute.instances.preempted`, before any compute or forensics — GCP SPOT reclaim during the
boot window). Relaunch #2 (`features-sports-sports-20260810-140033`, ON-DEMAND, `--end-date 2026-08-09`) registered
deployment `e1802a4d`, pruned 194/221 dates (27 pending), processed them, and **COMPLETED SUCCESSFULLY** at
2026-08-10T14:11:09Z — `Processing completed successfully` / `command exited rc=0`, deployment archived
`status=completed, exit_code=0`, VM self-deleted (`VM_SHUTDOWN_ON_COMPLETION`). The backfill through yesterday (08-09)
is now confirmed complete; today (08-10) has NO upstream reference data (0/17 entities) and is correctly deferred to
tomorrow's run once instruments-service writes it. (A mid-run read of the run.log/deployment heartbeat appeared stale at
~14:06 and suggested a stall; the authoritative archived-deployment record shows a clean completion at 14:11.)

**Follow-ups (not this escalation's scope):**

- 2026-08-10 reference tables were recorded `empty_confirmed(SOURCE_RETURNED_ZERO)` by the aborted run — false honest
  absence (upstream merely lagging). Once instruments-service writes 2026-08-10 reference data, those need a `--force`
  recompute of the sports features backfill to fill 08-10 reference tables/features.
- The reference-table exporter classifies a GCS-missing upstream as `SOURCE_RETURNED_ZERO` with a fabricated
  `http_status=200` fetch-evidence — a real evidence-semantics defect worth its own fix (thread an upstream-missing
  signal rather than reporting a clean 2xx+0).
