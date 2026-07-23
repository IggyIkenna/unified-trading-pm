---
doc_type: plan
title: is-daily-enum-{prediction,sports} capture heal — observability fix → real diagnosis → backfill
summary:
  is-daily-enum-prediction (dead 07-01→) and is-daily-enum-sports (dead 06-28→, longer, previously undetected) both
  still exit(1) in the cloud even though the deployed image now carries the UTL write-side dtype coercion — a SECOND,
  different failure the total observability gap hides. Ship exc_info=True on the swallowing catch, redeploy, re-run to
  finally see the real traceback, fix whatever it reveals, then backfill the missed windows.
status: draft
nature: process
asset_group: [prediction, cefi]
stage: [data]
repos: [instruments-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [manifest, capture, dtype, arrow, observability, exc-info, is-daily-enum, cloud-run, backfill]
related:
  [
    plans/active/issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md,
    plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    plans/active/issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md,
  ]
created: 2026-07-07
last_updated: 2026-07-07
parent_epic: instruments_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  [
    split from prediction_capture_incident_remediation_2026_07_06.md Workstream A residuals,
    2026-07-07 — operator requested AO-ready split; born draft,
    flip to active once AO updates land,
  ]
---

# is-daily-enum-{prediction,sports} capture heal

> **Full diagnosis + everything already tried (chronological, so you don't repeat it) is in the handoff issue doc — read
> it FIRST, this plan does not duplicate it:**
> [`issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`](issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md).
> Short version: the deployed image (`instruments-service:latest`) is docker-confirmed to carry the UTL coercion fix
> (UTL 1.6.0), yet both jobs still exit(1) after a full ~31-51min enumeration. Cloud Logging shows ONLY "Container
> called exit(1)" — no traceback. A local `.venv` run of the exact same command on the exact same UTL succeeded, so the
> remaining failure is cloud-image/environment-specific, not a code bug reproducible locally as-is.

## Codex SSOTs

- `codex/05-infrastructure/manifest-consolidator-ssot.md` §"Recovery when a deployed consolidator is on a bad image" —
  the SAME class of problem (fix lands in UTL, but a service image's `BASE_IMAGE_DIGEST` pin must be bumped + rebuilt
  before the fix reaches production) as instruments-service@1098731c4 fixed for the perp-guard image yesterday. Use that
  exact recipe if this turns out to be a pin issue again.
- `codex/02-data/availability-manifest-and-data-status.md` — ManifestRow schema + write-side contract.

## Todos — SEQUENTIAL (one continuous thread: unblock → diagnose → fix → backfill)

- [ ] [CODE] P0. Add `exc_info=True` to the UTL shard-isolation catch (`service_framework/_adapter.py`, "Handler %s
      failed on payload") so the swallowed exception surfaces in logs. Separately root-cause why Cloud Run job
      stdout/stderr does not reach Cloud Logging at all for these jobs (only the audit-log "RunJob" event and "Container
      called exit(1)" appear — confirmed on both `is-daily-enum-prediction` AND `is-daily-enum-cefi`, so this affects
      every lifecycle-catalogue/enum job, not just the two dead ones). Get the fix into the `is-daily-enum-*` image
      (rebuild/redeploy — mirror the `Dockerfile` `BASE_IMAGE_DIGEST` bump recipe from instruments-service@1098731c4 if
      the fix lands in UTL and needs a pin bump to reach the image). Gate: a forced handler exception logs the full
      traceback in Cloud Logging; verified on a real `is-daily-enum-prediction` or `-sports` run.
- [ ] [CODE] P0. With the real traceback now visible, re-run `is-daily-enum-{prediction,sports}` and read the ACTUAL
      error (NOT the already-ruled-out `ArrowTypeError` — that's fixed; see "what is NOT the cause" in the issue doc).
      Fix the real root cause. Gate: `is-daily-enum-prediction` AND `is-daily-enum-sports` cloud executions both show
      `succeededCount=1` — verified via
      `gcloud run jobs executions describe <exec> --format='value(status.succeededCount)'` read as an EXPLICIT
      single-field call, never a combined `value(a,b)` call parsed by a script (a prior attempt on this exact
      investigation misread gcloud's tab-collapsed output and wrongly reported two failed runs as succeeded — verify
      with `executions describe`, one field at a time, before claiming green).
- [ ] [VERIFY] P1. Backfill the missed windows: prediction 07-01→07-06, sports 06-28→07-06. Confirm the healed daily
      job's `--days-back` reach covers the gap days' by_date + manifest rows, or run a targeted backfill for the
      uncovered dates. Then confirm the catalogue picks up the post-gap listings (`max(available_from)` advances,
      `CATALOGUE_STALE_BY_DATE` clears) on the next daily catalogue run. Gate: no by_date/manifest holes in either AG's
      07-01(pred)/06-28(sports)→07-06 window; both catalogues' `available_from` advance past their respective freeze
      dates.

## Done definition

Both `is-daily-enum-{prediction,sports}` cloud jobs succeed on 2 consecutive scheduled runs (not just a manual
re-trigger); the missed-window backfill is verified complete; `quality-gates.sh`-green + quickmerge on every code
change; `Evidence: cloudbuild=<id>` cited for any image rebuild claimed done.
