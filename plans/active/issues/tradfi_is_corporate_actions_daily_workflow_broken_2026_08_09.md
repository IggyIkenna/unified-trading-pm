---
doc_type: issue
title:
  "instruments-service-daily Cloud Scheduler → Workflow chain 404s daily; TradFi corporate_actions has no other
  scheduled path"
summary: >-
  While closing a mechanical Cloud Run revision ops-check (defi_satellite_ao_dispatch_batch11-ead9fc97e94a), found the
  `instruments-service-daily-trigger` Cloud Scheduler job → `instruments-service-daily` Workflow chain fails every time
  it fires (both days it has logged in the last 90d: 2026-08-08 and 2026-08-09, both 08:30 UTC) with an HTTP 404 — it
  targets a bare Cloud Run Job named `instruments-service` that no longer exists (superseded by the per-asset-group
  `is-daily-enum-<ag>` jobs, which ARE live and current). The Workflow's `run_corporate_actions` step (TradFi
  dividends/splits/earnings, `--mode corporate_actions --upload-to-gcs`) has no equivalent scheduled job anywhere else
  in the live fleet — unlike its `run_instruments` step, which IS functionally covered by the working `is-daily-enum-*`
  jobs, so corporate_actions ingestion looks like it may be silently unscheduled.
status: open
nature: issue
asset_group: [tradfi, defi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [infra, cloud-run, cloud-scheduler, workflows, instruments-service, corporate-actions, tradfi, broken-automation]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch11_2026_08_09.md,
    /plans/active/issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md,
  ]
created: 2026-08-09
author: slot-20 (data_engineering craft)
parent_epic: defi_master
priority: P2
source:
  "worker analysis (slot-20, data_engineering craft) while closing defi_satellite_ao_dispatch_batch11's Cloud Run
  revision ops-check todo, 2026-08-09"
assigned_vm: NA
execution_scope: local-only
estimate_class: design
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope: [/codex/05-infrastructure/deployment-observability.md, /codex/05-infrastructure/vm-launcher-runbook.md]
---

# instruments-service-daily Workflow is broken; TradFi corporate_actions may be silently unscheduled

## What I found

While closing `defi_satellite_ao_dispatch_batch11-ead9fc97e94a` (confirm the live instruments-service Cloud Run revision
serves `origin/main` HEAD), I checked the Cloud Scheduler job the todo itself named, `instruments-service-daily-trigger`
(`30 8 * * *`, `httpTarget.uri` = the Workflows Executions API for `instruments-service-daily`).

- `gcloud workflows describe instruments-service-daily --location asia-northeast1` — `revisionId: 000001-b4d`,
  `updateTime: 2026-01-26T08:39:19Z` (never updated since creation), `managed-by: terraform` label. Its `main.steps`
  hardcode `job_name: "instruments-service"` and POST to
  `https://asia-northeast1-run.googleapis.com/v2/.../jobs/instruments-service:run` for two steps: `run_instruments`
  (CEFI+TRADFI+DEFI, `--mode instruments`) then `run_corporate_actions` (TradFi only,
  `--mode corporate_actions --upload-to-gcs`).
- `gcloud logging read 'resource.type="workflows.googleapis.com/Workflow" AND resource.labels.workflow_id="instruments-service-daily"' --freshness=90d`
  returns exactly 4 entries total — 2 `ACTIVE`→`FAILED` pairs, 2026-08-08T08:30Z and 2026-08-09T08:30Z (no other days
  logged in the 90-day window at all). Both failures are identical:
  ```
  HTTP server responded with error code 404
  in step "run_instruments", routine "main", line: 22:
  {"body":{"error":{"code":404,"message":"Resource 'instruments-service' of kind 'JOB' in region
  'asia-northeast1' in project 'central-element-323112' does not exist.","status":"NOT_FOUND"}} ...}
  ```
- `gcloud run jobs list` (all regions checked: asia-northeast1, us-central1, asia-northeast3, us-east1) — no Cloud Run
  Job named exactly `instruments-service` exists anywhere. The live IS enumeration path is a family of per-asset-group
  jobs instead: `is-daily-enum-{cefi,defi,prediction,sports,tradfi}` (each its own Cloud Scheduler entry, each running
  `daily_is_enumeration.py --asset-group <ag>`) plus `uts-prod-instruments-service-{ag}-t1-recon` reconciliation jobs.
  These ARE live and current — `is-daily-enum-defi`'s deployed image resolves to `origin/main` HEAD exactly (see the
  batch11 plan's Progress Log entry this issue was filed alongside).
- The dead Workflow's `run_instruments` step is therefore functionally redundant/superseded by the working
  `is-daily-enum-*` jobs (CEFI/TRADFI/DEFI instrument enumeration already happens via a different, healthy path). Its
  `run_corporate_actions` step is NOT — `gcloud scheduler jobs list` and `gcloud run jobs list` (fleet-wide, both
  checked) show no job with `corporate_actions`/`dividend`/`earning` in its name or args, and neither
  `is-daily-enum-tradfi` nor any sibling job passes `--mode corporate_actions`. I did not find a second, hidden path.

## Why it matters

- If corporate_actions truly has no other scheduled path, TradFi dividends/splits/earnings ingestion has been silently
  broken since whenever the bare `instruments-service` Cloud Run Job was removed/renamed (unknown from what I checked —
  the log window only covers the last 2 days this Workflow has fired at all; I did not attempt to date the job
  rename/removal itself, e.g. via Cloud Build/Artifact Registry history for the old job name, which is out of this
  todo's scope).
- A `managed-by: terraform` Workflow silently 404ing daily for at least 2 days (possibly longer — outside my 90d log
  window's actual firing history) with no alert observed is itself a monitoring gap worth checking against
  `/codex/05-infrastructure/data-pipeline-alerts.md`'s registry.
- Per CLAUDE.md's data-pipeline-correctness HARD RULE, this is a real, unresolved gap — filed rather than force-fixed
  inline because the correct fix is a genuine design call (see below), not a mechanical rename, and this todo's own
  scope was a narrow ops-check, not this workflow's repair.

## Recommended decision (needs an operator/design ruling — not a bounded worker fix)

Two non-exclusive directions:

1. **Delete the dead Workflow + its Scheduler trigger entirely for the `run_instruments` half** (superseded, confirmed
   redundant with the live `is-daily-enum-*` jobs) — but this can't happen until direction 2 below covers
   `run_corporate_actions`, or that ingestion path disappears too.
2. **Give corporate_actions a real scheduled home** — either fix the dead Workflow to target a Cloud Run Job that
   actually exists (repoint `job_name` — check which live job, if any, exposes a `--mode corporate_actions` CLI path
   today), or add a new per-asset-group-style Scheduler + Job entry mirroring `is-daily-enum-tradfi`'s pattern but with
   `--mode corporate_actions --upload-to-gcs`.

Both directions need someone to first confirm what actually consumes TradFi corporate_actions data downstream (if
anything currently does) to judge real priority/urgency — I did not chase that consumer-side question, it's outside this
task's scope.

## Todos

- [ ] [DATA] P2. Determine whether anything downstream currently consumes TradFi `corporate_actions` data (grep
      consumers across features-service/strategy-service/UI for the data_type) and how long this Workflow has actually
      been 404ing (check Artifact Registry / Cloud Build history for when the bare `instruments-service` Cloud Run Job
      was last deployed/removed, if recoverable). Repo: instruments-service. Done when: a dated Progress Log entry
      states the consumer answer + the best-available broken-since date (or "undeterminable, evidence cited").
- [ ] [INFRA] P2. Once the consumer/urgency question above is answered, either (a) repoint the
      `instruments-service-daily` Workflow's `job_name` to a real Cloud Run Job that supports
      `--mode corporate_actions --upload-to-gcs` and re-verify a live execution succeeds, or (b) if corporate_actions is
      confirmed unused/deprecated, delete the dead Workflow + its Cloud Scheduler trigger
      (`gcloud workflows delete     instruments-service-daily`,
      `gcloud scheduler jobs delete instruments-service-daily-trigger`) with the deletion justification cited in the
      Progress Log. Repo: deployment-service (or wherever this Workflow's Terraform actually lives — locate it first).
      Done when: the daily 08:30 UTC trigger either succeeds (`gcloud logging read` shows a `SUCCEEDED` state on the
      next natural fire) or is confirmed removed with no further Scheduler entry.

## Progress Log

- 2026-08-09 (slot-20, data_engineering craft): Filed while closing `defi_satellite_ao_dispatch_batch11-ead9fc97e94a`
  (the Cloud Run revision ops-check todo) — full evidence for the finding is also cross-referenced in that plan's
  Progress Log. Not investigated further (consumer-side / broken-since-when questions) — left as the todos above.
