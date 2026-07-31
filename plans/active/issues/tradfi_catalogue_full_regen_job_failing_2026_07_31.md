---
doc_type: issue
title: "lifecycle-catalogue-full-tradfi weekly self-heal Cloud Run Job has failed its last 3 consecutive runs"
summary: >-
  While confirming the KRX name-column catalogue todo (tradfi_consolidated_native_ao_extract-009), verified the DAILY
  lifecycle-catalogue-regen-tradfi Cloud Run Job (--mode incremental) is green every day 2026-07-22 through 2026-07-31
  and correctly landed the `name` column live. But its weekly self-heal sibling, lifecycle-catalogue-full-tradfi (--mode
  full, Saturday 05:00 UTC), shows Completed=False on its last 3 executions (2026-07-11, 2026-07-18, 2026-07-25) — only
  the 2026-07-04 run succeeded. The daily incremental job is unaffected and tradfi catalogue reads are currently
  correct, so this is not user-visible yet, but the weekly full-mode self-heal (the mechanism that would catch/repair
  drift the incremental mode can't) has been silently broken for 3 weeks.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [tradfi, catalogue, cloud-run-job, instruments-service, self-heal]
related:
  [
    /plans/active/tradfi_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-31
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.3
assigned_role: backend_engineer
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Surfaced while executing tradfi_consolidated_native_ao_extract-009 (KRX name-column "STILL OPEN" tracking, slot 6,
  2026-07-31) — a side finding from `gcloud run jobs executions list --job=lifecycle-catalogue-regen-tradfi` /
  `--job=lifecycle-catalogue-full-tradfi`, tangential to that todo's own scope.
drift_direction: advance-code
---

# lifecycle-catalogue-full-tradfi weekly job failing — daily incremental unaffected

## What I found

`gcloud run jobs executions list --job=lifecycle-catalogue-full-tradfi --project=central-element-323112 --region=asia-northeast1`
shows `Completed=False` for `lifecycle-catalogue-full-tradfi-hlvh9` (2026-07-25), `-8m6wx` (2026-07-18), and `-z574m`
(2026-07-11) — 3 consecutive weekly runs. Only `-mh959` (2026-07-04) succeeded. By contrast, the daily
`lifecycle-catalogue-regen-tradfi` job (`--mode incremental`) is green every day 2026-07-22 through 2026-07-31 (most
recently `lifecycle-catalogue-regen-tradfi-hdpmq`, Completed 2026-07-31T01:05:32Z) and correctly landed the KRX `name`
column live (verified via a direct read of
`gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`).

Both jobs are defined in `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf`, both run the same
`instruments-service/scripts/build_instrument_catalogue.py --asset-group tradfi`, differing only in `--mode`
(`incremental` daily vs `full` weekly) and the weekly job's longer 6h timeout. No log content was pulled this session
(time-boxed to the KRX todo) — only the execution-list `Completed` status was checked, so root cause is unknown (could
be a `--mode full` code path regression, a resource/timeout issue at the larger full-mode row-count, or unrelated infra
flakiness).

## Why it matters

Tradfi catalogue correctness currently rides entirely on the daily incremental job. The weekly full-mode run exists
specifically as a self-heal (re-derives from the full `by_date` corpus rather than incrementally patching), so if the
incremental mode ever silently drifts or corrupts a row, there is currently no working safety net to catch it — the
mechanism designed to catch that class of bug has itself been broken for 3 weeks.

## Recommended next steps

- [ ] [BACKEND] P2. Pull execution logs for `lifecycle-catalogue-full-tradfi-hlvh9` (2026-07-25, most recent failure)
      via `gcloud logging read` / Cloud Run execution log, identify the actual failure mode (timeout, OOM, exception,
      exit code), and determine whether it's a `--mode full` code-path bug in `build_instrument_catalogue.py` or an
      infra/resource issue. (repo: instruments-service)
- [ ] [BACKEND] P2. Fix the identified root cause and manually re-trigger
      `gcloud run jobs execute lifecycle-catalogue-full-tradfi` to confirm green before the next scheduled Saturday
      05:00 UTC run. (repo: instruments-service, deployment-service)
