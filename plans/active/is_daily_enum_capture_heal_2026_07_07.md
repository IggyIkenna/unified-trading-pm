---
doc_type: plan
title: is-daily-enum-{prediction,sports} capture heal — observability fix → real diagnosis → backfill
summary:
  is-daily-enum-prediction (dead 07-01→) and is-daily-enum-sports (dead 06-28→, longer, previously undetected) both
  still exit(1) in the cloud even though the deployed image now carries the UTL write-side dtype coercion — a SECOND,
  different failure the total observability gap hides. Ship exc_info=True on the swallowing catch, redeploy, re-run to
  finally see the real traceback, fix whatever it reveals, then backfill the missed windows.
status: active
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
assigned_vm: planning
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

- `/codex/05-infrastructure/manifest-consolidator-ssot.md` §"Recovery when a deployed consolidator is on a bad image" —
  the SAME class of problem (fix lands in UTL, but a service image's `BASE_IMAGE_DIGEST` pin must be bumped + rebuilt
  before the fix reaches production) as instruments-service@1098731c4 fixed for the perp-guard image yesterday. Use that
  exact recipe if this turns out to be a pin issue again.
- `/codex/02-data/availability-manifest-and-data-status.md` — ManifestRow schema + write-side contract.

## Todos — SEQUENTIAL (one continuous thread: unblock → diagnose → fix → backfill)

- [x] ✅ [CODE] P0. **VERIFIED 2026-07-27 (slot-10)**: this plan carried forward a stale pre-completion snapshot — the
      referenced handoff issue doc (`issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`) is
      already **`status: resolved`** and ARCHIVED (`plans/archive/issues/…`), resolved 2026-07-14. Direct code read
      confirms `exc_info=exc` is already on both UTL shard-isolation catch sites
      (`unified_trading_library/service_framework/_adapter.py:61` serial driver, `:97` concurrent driver) — shipped
      `unified-trading-library@b7925334` (2026-07-07, same day this plan was created) as part of the pd.NA
      nullable-Boolean fix's commit. The stdout/stderr-to-Cloud-Logging gap was separately root-caused (2026-07-13) as a
      project `_Default` logging sink exclusion (`severity <= "DEBUG"` was dropping ALL `resource.type="cloud_run_job"`
      stdout, unrelated to `exc_info`) — fixed via a sink-exclusion carve-out
      (`severity <= "DEBUG" AND NOT resource.type="cloud_run_job"`, Cloud Build `9a838983-464c-4f45-b703-c436e8ad058e`
      SUCCESS) and verified working (fresh `is-daily-enum-prediction` execution streamed full app stdout to Cloud
      Logging same day). No code change needed here — closing as verified-already-shipped.
- [x] ✅ [CODE] P0. **VERIFIED 2026-07-27 (slot-10)**: per the same archived issue doc, the real root cause (once logs
      were visible) was **SIGKILL/OOM** (`exit_code=-9` at 8Gi/4cpu, prediction's CLOB scan past "page 1000, 1,001,000
      markets total"), not `ArrowTypeError`. Fixed via memory bumps (prediction 8Gi→16Gi; sports 8Gi→16Gi→**32Gi/8cpu**,
      sports OOM'd even at 16Gi) + a memory-frugal code fix (`instruments-service@633d7af4`, column-projected manifest
      reads, measured 6.7GB→1.6GB peak RSS, semantics proven byte-identical old-vs-new). Both jobs confirmed green on
      real **scheduled** cron executions (not just manual retriggers, matching this todo's own gate): prediction
      `is-daily-enum-prediction-wrbsm` `succeededCount=1` @ 2026-07-13T23:54:52Z; sports `is-daily-enum-sports-5vchf`
      (the 13:30Z scheduled cron) `succeededCount=1` @ 2026-07-14T15:02:44Z, each field read explicitly per this todo's
      own single-field-read caution. Standing follow-up noted in the archived doc (not re-added here, tracked there): a
      durable chunked-scan fix so 16Gi/32Gi isn't a ceiling race against universe growth, and a bump-back evaluation
      once a few scheduled runs stay green.
- [ ] [VERIFY] P1. Backfill the missed windows: prediction 07-01→07-06, sports 06-28→07-06. **RE-MEASURED 2026-07-27
      (slot-10) — genuine gap CONFIRMED, still open**, read-only `read_availability_index` on
      `instruments-store-pred-prd-central-element-323112` / `instruments-store-sports-prd-central-element-323112`: -
      **prediction: 2026-07-01, 07-02, 07-03 — ZERO manifest rows** (data resumes 07-04, 44 distinct instruments that
      day, climbing). - **sports: 2026-06-28, 06-29, 06-30, 07-01, 07-02 — ZERO manifest rows** (data resumes 07-03,
      `captured`=278 that day, `empty_confirmed`≈3.8k, `expected_unattempted`≈3.3k — the real per-day capture_status
      distribution, i.e. the daily job's normal steady state). This is the daily job's normal forward-only cadence (no
      `--days-back` catch-up ran) — the archived doc's own "standing follow-up" list (2026-07-14) already flagged this
      as NOT yet done and it still isn't, 13 days later. Confirm the healed daily job's `--days-back` reach covers the
      gap days' by_date + manifest rows, or run a targeted backfill for the 3 (pred) / 5 (sports) uncovered dates above.
      Then confirm the catalogue picks up the post-gap listings (`max(available_from)` advances,
      `CATALOGUE_STALE_BY_DATE` clears) on the next daily catalogue run. Gate: the exact day lists above show real
      (non-zero) manifest rows; both catalogues' `available_from` advance past their respective freeze dates. Coordinate
      with `plans/archive/issues/sports_gw_enrichment_false_empty_manifest_and_dropped_rows_2026_07_14.md` (same index,
      avoid double-writing) per the archived doc's own note.

## Done definition

Both `is-daily-enum-{prediction,sports}` cloud jobs succeed on 2 consecutive scheduled runs (not just a manual
re-trigger) — **VERIFIED done 2026-07-13/14**, see todos above; the missed-window backfill is verified complete —
**STILL OPEN**, see remaining todo above; `quality-gates.sh`-green + quickmerge on every code change;
`Evidence: cloudbuild=<id>` cited for any image rebuild claimed done.
