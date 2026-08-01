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
status: resolved
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
  "slot 14, 2026-08-01 — root-caused to a single transient GCS ConnectionResetError on 1-of-27175 by_date blobs killing
  the whole multi-hour --mode full walk; fixed via a per-blob retry wrapper (instruments-service@cdf41538/@0a14b313,
  QG-green, quickmerge-shipped) + a producer image rebuild (Cloud Build 9314b1bb, :latest->8f16345b); manually
  re-triggered lifecycle-catalogue-full-tradfi-89jlj, which completed clean (Completed=True, 967675 rows, monotonic
  guard ACCEPT, promoted to catalog.parquet) in 2h25m."
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Surfaced while executing tradfi_consolidated_native_ao_extract-009 (KRX name-column "STILL OPEN" tracking, slot 6,
  2026-07-31) — a side finding from `gcloud run jobs executions list --job=lifecycle-catalogue-regen-tradfi` /
  `--job=lifecycle-catalogue-full-tradfi`, tangential to that todo's own scope.
drift_direction: advance-code
last_updated: 2026-08-01
---

> **🟢 ARCHIVED 2026-08-01** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule. The fix (per-blob GCS download retry) lives in
> instruments-service/scripts/build_instrument_catalogue.py; no new durable codex contract was established (existing UTL
> with_retry primitive reused, no new pattern to document).

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

- [x] ✅ [BACKEND] P2. Pull execution logs for `lifecycle-catalogue-full-tradfi-hlvh9` (2026-07-25, most recent failure)
      via `gcloud logging read` / Cloud Run execution log, identify the actual failure mode (timeout, OOM, exception,
      exit code), and determine whether it's a `--mode full` code-path bug in `build_instrument_catalogue.py` or an
      infra/resource issue. (repo: instruments-service) — **2026-07-31 (slot 14, backend_engineer)**:
      `gcloud run jobs     executions describe lifecycle-catalogue-full-tradfi-hlvh9` confirms `NonZeroExitCode`/exit
      code 1 ("The container exited with an error"), ran `05:00:08Z`→`09:02:22Z` (~4h02m of the 6h `timeoutSeconds`
      budget — **NOT a timeout**). `gcloud logging read` across every log name/severity for this exact execution
      (`labels."run.googleapis.com/execution_name"="lifecycle-catalogue-full-tradfi-hlvh9"`, no filter narrower than
      that) returns **exactly ONE entry total**: the platform's own completion audit event — **zero application
      stdout/stderr for the entire ~4h run**, including no `[BISECT-A]` (the very first `print(..., flush=True)` in
      `run_rollup()`, `build_instrument_catalogue.py:4763`) and no `logger.exception` traceback from the
      `if __name__ == "__main__":` safety net (`:5122-5130`, itself written specifically to survive Cloud Logging's
      multi-line-traceback truncation — see its own comment citing this exact truncation history). No
      `"Memory limit exceeded"`/OOM-style system log line found in the surrounding `varlog/system` window either — **not
      a classic OOM signature**. **Corroborated as a real, repeatable pattern, not a one-off**: the PRIOR weekly failure
      (`lifecycle-catalogue-full-tradfi-8m6wx`, 2026-07-18) shows the identical signature — `NonZeroExitCode`/exit 1,
      ran `05:00:03Z`→`09:49:31Z` (~4h49m), zero log output. By contrast the daily incremental job
      (`lifecycle-catalogue-regen-tradfi-hdpmq`, same script/image family, same project) logs profusely from
      `[BISECT-A]` onward and completed cleanly. **Conclusion**: not a timeout, not a classic OOM-kill (no memory-limit
      log line), and — critically — not a clean, traceable Python exception either (the safety net built specifically to
      surface exactly this class of failure produced nothing, twice). The complete absence of even the FIRST-line print
      statement across two separate multi-hour `--mode full` runs points toward an infra/resource-level termination
      (silently discards buffered output) rather than an in-app code-path bug — but the EXACT external mechanism is not
      pinned from logs alone; no Cloud Monitoring `container/memory/utilizations` time series exists for this Cloud Run
      JOB resource type (queried, zero series returned — jobs don't populate that metric the same way services do), so a
      definitive memory-pressure correlation could not be drawn either way this session. Runtime SA is
      `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com` (unrelated to the concurrent
      `uts-prd-sa` migration investigation elsewhere in the corpus — different SA, different service, ruled out as a
      connection). Handoff for the next `[BACKEND]` todo (fix + re-verify): since app-level logs don't exist to debug
      against, the highest-leverage next step is likely a manual
      `gcloud run jobs execute lifecycle-catalogue-full-tradfi` re-run WHILE actively tailing `gcloud logging tail` in
      real time (catches output a post-hoc `read` might still be missing) or a scoped diagnostic sink (mirroring the
      pattern used in `deployment_api_sigabrt_crash_loop_2026_07_24.md`'s cold-container investigation) — NOT another
      blind re-trigger without first arming a way to observe it.
- [x] ✅ [BACKEND] P2. Fix the identified root cause and manually re-trigger
      `gcloud run jobs execute lifecycle-catalogue-full-tradfi` to confirm green before the next scheduled Saturday
      05:00 UTC run. (repo: instruments-service, deployment-service) — **2026-08-01 (slot 14, backend_engineer)**: Root
      cause was a single transient `requests.exceptions.ConnectionError` ("Connection reset by peer") on any ONE of the
      27,175 `by_date` blob downloads propagating through `_bounded_parallel_load` and killing the entire multi-hour run
      — at this blob count, hitting at least one transient network blip over a run's lifetime is the expected case, not
      the exception (confirmed via the newly-armed `[BISECT-C-PROGRESS]` heartbeat from todo 1's fix: the prior `-mczhg`
      retry attempt this session produced a full application-level traceback for the FIRST time, pinning the exact
      exception + call site). Fix: added `_download_by_date_blob()` (UTL `with_retry`, 5 attempts, exp. backoff)
      wrapping the GCS download in all 4 `by_date` `_load` closures (tradfi/cefi/defi/ prediction, sports leagues,
      sports FTP) — `instruments-service@cdf41538` (+ import-path correction `@0a14b313`, QG-green, quickmerge-shipped,
      verified on origin). Deployed image `:latest` predated the fix (built 23:03:34Z, before these commits), so
      rebuilt+pushed via `gcloud builds submit --config=cloudbuild.yaml     --substitutions=_RUN_INIMAGE_QG=false`
      (in-image QG step needs the PM harness not present in the built image — documented producer-rebuild toggle in the
      file's own header comment; QG was already enforced at quickmerge) — build `9314b1bb-1ed0-4ece-83bb-3345ab12ee46`,
      SUCCESS, `:latest`→`8f16345b`. Manually re-triggered: `lifecycle-catalogue-full-tradfi-89jlj` (started
      2026-08-01T00:13:39Z) ran the full 27,175-blob walk to completion with ZERO further failures — `Completed=True`,
      `succeededCount=1`, "Execution completed successfully in 2h25m4.94s", 967,675 rows, monotonic guard `ACCEPT`
      (`new=967675 current=967675`), promoted cleanly to
      `gs://instruments-store-tradfi-prd-central-element-323112/prod/catalog.parquet`. Job is GREEN and will run clean
      at the next scheduled Saturday 05:00 UTC self-heal.
