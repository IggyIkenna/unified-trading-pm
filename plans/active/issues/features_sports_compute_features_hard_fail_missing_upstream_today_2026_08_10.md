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
