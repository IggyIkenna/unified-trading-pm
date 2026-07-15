---
doc_type: issue
title:
  "instruments-sports manifest consolidator is livelocked on its own GCS lock — availability_index.parquet never
  refreshes past the 120s freshness budget consumers require, blocking features-service-sports (and likely every other
  consumer of instruments-store-sports-prd-central-element-323112)"
summary:
  'Discovered while executing the DeployAndVerify phase of
  plans/active/features_sports_service_consolidation_deploy_2026_07_15.md (plan todo 5 — apply terraform, deploy the new
  features-service-sports-job Cloud Run job, manually trigger and watch a real execution to SUCCEEDED). Terraform apply
  succeeded cleanly (4 resources: Cloud Run Job + daily/backfill Workflow + Scheduler trigger, `terraform plan`
  pre/post-apply clean). Scheduler paused immediately per the terraform''s own note (avoid double-fire). A bare manual
  `gcloud run jobs execute` (no overrides) failed fast on a genuine, separate terraform bug (default job args omit
  `--start-date`/`--end-date`, which the sports CLI''s batch-mode validation requires) — logged as a follow-up fix, not
  this issue. A second manual execution with correct `--start-date`/`--end-date` overrides got PAST that (proving the
  fleet-wide UTL/UAC import bug genuinely does not reproduce on the new image, and the CLI arg contract is otherwise
  correct) but then failed with `[HIGH] application error in features-service.compute_features: Manifest consolidator
  appears DOWN for bucket=''instruments-store-sports-prd-central-element-323112'': consolidated
  _index/availability_index.parquet heartbeat is 208s old (> 120s budget) while per-VM shards exist...
  recovery=fail_fast`. Direct inspection of `uts-prod-manifest-consolidator-instruments-sports`''s own execution history
  (Cloud Scheduler cron `*/1 * * * *`, single trigger, no duplicate scheduler) shows it has been running successfully
  (exit 0) every ~1 minute continuously since at least 12:14 UTC, but its OWN logs on every single cycle read
  `ManifestConsolidator: skipping cycle for bucket=instruments-store-sports-prd-central-element-323112 — fresh lock
  present (sibling cron still running)` and write `manifest-consolidator ... success=True shards=0 rows_in=0 rows_out=0
  ... error=locked` — i.e. it perpetually no-ops because it always sees the immediately-prior run''s lock as still
  "fresh", even though that prior run itself also just no-op-skipped (no actual sibling is running concurrently — there
  is only one scheduler, one cron, jobs complete in ~8-9s).
  `gs://instruments-store-sports-prd-central-element-323112/_index/consolidator.lock` is a real GCS object whose
  `started_at`/`instance` fields get rewritten fresh on every single cycle (skip or not), which is consistent with a
  lock-TTL misconfiguration (TTL apparently ≥ the ~60-70s cron cadence) creating a self-perpetuating livelock: every run
  renews the lock timestamp even when it only skipped, so the NEXT run always finds it "fresh" too, forever.
  `availability_index.parquet` shows exactly ONE real write in the observed window (12:39:43 UTC) sandwiched between
  skip-only cycles before and after it (12:37:48 and 12:41:38 both logged `error=locked`) — by the time of the 2nd retry
  (12:43:37 UTC, index now 234s old and climbing) the index had not refreshed again. This is the SAME
  manifest-consolidator codebase/pattern used for 4 other instruments-* buckets (cefi/defi/tradfi/prediction) and likely
  the features-*/market-data-*/execution-*/ml-training-artifacts/strategy consolidators too
  (`uts-prod-manifest-consolidator-*`, ~29 total jobs share this pattern per `gcloud run jobs list`) — none of the
  others were checked in this touch, so whether they exhibit the same livelock (vs. just not currently being probed by a
  120s-budget consumer) is unknown and flagged as a follow-up, not this issue''s scope.'
status: open
nature: issue
asset_group: [sports]
stage: [data, meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    gcs,
    manifest-consolidator,
    livelock,
    lock-contention,
    data-correctness,
    production-outage,
    instruments-service,
    features-sports,
  ]
related: [plans/active/features_sports_service_consolidation_deploy_2026_07_15.md]
created: "2026-07-15"
parent_epic: infrastructure_master
priority: P1
source:
  "Dispatched sub-agent task, 2026-07-15: DeployAndVerify phase (plan todo 5) of
  features_sports_service_consolidation_deploy_2026_07_15.md — apply terraform, deploy the new
  features-service-sports-job, manually trigger + watch to SUCCEEDED. The new job/terraform themselves verified correct;
  the manual execution failed on this separate, pre-existing infra condition discovered as a direct consequence of the
  mandated 'watch to a genuine SUCCEEDED terminal state' verification step."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# instruments-sports manifest consolidator livelock — blocks features-service-sports (and possibly other consumers)

## Finding

Executing `plans/active/features_sports_service_consolidation_deploy_2026_07_15.md`'s todo 5 (deploy + verify), the new
`features-service-sports-job` Cloud Run Job + Workflow terraform applied cleanly (`terraform plan`: 4 to add, 0 changed,
0 destroyed; `-target`ed apply for all 4 new resources; post-apply `terraform plan` shows only a harmless output-only
diff — no drift). The daily scheduler trigger was immediately paused per the terraform's own guidance
(`gcloud scheduler jobs pause features-service-sports-daily-trigger` → confirmed `PAUSED`), avoiding a double-fire
window against the still-live legacy job.

Two manual `gcloud run jobs execute` attempts against the new job:

1. **Bare execute (no overrides)** — execution `features-service-sports-job-fs8sj`. Failed fast with
   `ERROR Validation failed: Batch mode requires --date or both --start-date and --end-date` — a **separate, real
   terraform bug**: the Cloud Run Job's default `args` (`terraform/services/features-service-sports/gcp/main.tf`,
   `module.daily_job`) omit `--start-date`/`--end-date`, which the consolidated sports CLI's batch-mode validation
   requires. This only affects a bare execute with no overrides (every real Workflow invocation supplies dates via
   `containerOverrides`), but is a real gap — flagged as a follow-up fix, not blocking this issue.
2. **Execute with `--args` overrides matching the Workflow's contract**
   (`--feature-family sports --operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date 2026-07-14 --end-date 2026-07-15`)
   — execution `features-service-sports-job-kk4dv`. This got **past** the CLI validation, the Python import chain
   (confirming the fleet-wide UTL/UAC version-skew bug genuinely does not reproduce on the current image), and GCS-FUSE
   mount setup — then failed with:
   ```
   ERROR [HIGH] application error in features-service.compute_features: Manifest consolidator appears DOWN for
   bucket='instruments-store-sports-prd-central-element-323112': consolidated _index/availability_index.parquet
   heartbeat is 208s old (> 120s budget) while per-VM shards exist. Remediation: check the consolidator Cloud Run Job +
   Scheduler for this bucket; do NOT fall back to the per-VM merge (can OOM on large buckets). Set
   MANIFEST_ALLOW_STALE_FALLBACK=true to force the recovery merge. (recovery=fail_fast, correlation=...)
   ```
   Terminal state: `NonZeroExitCode`, `failedCount: 1`, `completionTime: 2026-07-15T12:37:32Z`.

## Root cause — a livelock in `uts-prod-manifest-consolidator-instruments-sports`, not a features-service-sports bug

Direct inspection of the consolidator job that owns this bucket's index:

- **Scheduling is not duplicated**: `gcloud scheduler jobs list` shows exactly one trigger,
  `uts-prod-manifest-consolidator-instruments-sports-cron`, `*/1 * * * *` (UTC), `ENABLED` — no second/orphaned
  scheduler racing it.
- **Every execution completes in ~8-9s** (`latency_ms` 7343–9094 across 10+ sampled executions between 12:14 and 12:41
  UTC) — far shorter than the 60-70s cron cadence, so there is no genuine overlap window.
- **Yet every single execution's own log reads**:
  `ManifestConsolidator: skipping cycle for bucket=instruments-store-sports-prd-central-element-323112 — fresh lock present (sibling cron still running)`,
  followed by a structured `success=True shards=0 rows_in=0 rows_out=0 ... error=locked` line. Sampled 8 consecutive
  executions (`qz4kr`, `4k224`, `5nbt9`, `9stvl`, `kb4d5`, `5jgfx`, `m7zhf`/`2rjjn`) — **100% skip rate**,
  `error=locked` every time, despite no real sibling running.
- **`gs://instruments-store-sports-prd-central-element-323112/_index/consolidator.lock`** is a real GCS object; its
  `started_at`/`instance` fields are freshly rewritten on every cycle (confirmed via `gsutil cat`, e.g.
  `{"started_at": "2026-07-15T12:40:44...", "instance": "1-6fbaef6f"}`), including cycles that themselves only skipped.
  This is consistent with a lock-TTL bug: if the "is this lock fresh" check treats any lock younger than the cron
  cadence as fresh, and a SKIP cycle still renews the lock's timestamp (rather than leaving the prior lock's original
  timestamp untouched), the lock can never age past its own TTL — a self-perpetuating livelock, not a transient
  contention.
- **`availability_index.parquet` shows exactly one genuine write in the ~30 min observed**
  (`Update time: 2026-07-15 12:39:43 GMT`), bracketed by skip-only cycles immediately before (`12:37:48`,
  `error=locked`) and after (`12:39:41`, `12:41:38`, both `error=locked`). By the second manual retry (`12:43:37 UTC`)
  the index was 234s old and climbing — the livelock had resumed, not self-healed.
- **`consolidator_stall_state.json`** (`{"streak": 0, "baseline_shards": 5}`) confirms this exact condition already has
  a dedicated stall-detection field in this system — i.e. this is a recognized failure mode of the consolidator design,
  not a novel one, though `streak: 0` at inspection time suggests whatever detector owns that field had not yet flagged
  the current episode as a sustained stall.

## Why not fixed here

The consolidator code (`uts-prod-manifest-consolidator-instruments-sports`, part of the shared `manifest-consolidator`
pattern per `codex/05-infrastructure/manifest-consolidator-ssot.md`) is a different system from
`features-service-sports` — this dispatch's scope was the sports Cloud Run Job deploy, not the consolidator. The
lock/TTL logic likely lives in a shared library or a Batch/Cloud-Run-Job image used by **~29**
`uts-prod-manifest-consolidator-*` jobs (`gcloud run jobs list | grep consolidator` — cefi/defi/tradfi/prediction
instruments, features-_, market-data-_, execution-*, ml-training-artifacts, strategy) — a fix here has fleet-wide blast
radius and deserves its own investigation, not a same-touch patch under time/scope pressure for an unrelated deploy
task.

## Impact

- **Immediate**: `features-service-sports-job`'s manual verification execution cannot reach `SUCCEEDED` while this
  livelock persists — plan todo 5 of `features_sports_service_consolidation_deploy_2026_07_15.md` is BLOCKED, not
  failed-and-abandoned. The terraform/job/workflow resources created this touch are otherwise verified correct (import
  chain, CLI contract, GCS mount all confirmed working) and were deliberately left in place with scheduling paused — no
  rollback needed once this is fixed.
- **Broader, unconfirmed**: if the same livelock affects the other ~28 `manifest-consolidator` jobs (untested this
  touch), any consumer with a similarly tight freshness budget reading any of those buckets could be silently
  fail-fasting the same way, undetected until something like this touch's execution surfaces it. **Not confirmed** —
  flagged for a follow-up audit, not asserted as fact.

## Recommended next steps (operator/engineer follow-up, not actioned here)

1. Locate the manifest-consolidator's lock-freshness/TTL logic (shared code path across all
   `uts-prod-manifest-consolidator-*` jobs) and confirm/fix the suspected bug: a skip-cycle should not renew the lock's
   `started_at`, and/or the TTL should be shorter than the cron cadence so a genuinely idle lock ages out.
2. Once fixed, re-run `features-service-sports-job` manually with the same `--start-date`/`--end-date` overrides used in
   execution `kk4dv` above and confirm it reaches a genuine `SUCCEEDED` terminal state with real `fixture_features`
   output objects landed in `features-sports-prd-central-element-323112` (not just exit 0) — this is plan todo 5's
   actual completion bar, still open.
3. Separately, fix the bare-execute default-args gap found in step 1 above
   (`terraform/services/features-service-sports/gcp/main.tf` `module.daily_job.args` should include a sane default
   `--start-date`/`--end-date` or `--date`, matching how the Workflow's `containerOverrides` already do it) — small,
   independent, low-risk fix.
4. Only after (1)-(2) succeed does `features_sports_service_consolidation_deploy_2026_07_15.md` todo 5 flip to done, and
   only then do todos 6-8 (retire the legacy job, re-enable scheduling, close the other issue doc) become safe to
   attempt.
5. Consider a fleet-wide spot-check of the other ~28 `uts-prod-manifest-consolidator-*` jobs' recent execution logs for
   the same `error=locked`/100%-skip pattern, scoped as its own audit plan if warranted — not scoped here.

## Evidence

- `terraform plan`/`apply` in `terraform/services/features-service-sports/gcp/` (deployment-service repo): clean 4
  resources added, 0 changed, 0 destroyed; post-apply `terraform plan` shows only a benign output-value diff.
- `gcloud scheduler jobs pause features-service-sports-daily-trigger --location=asia-northeast1 --project=central-element-323112`
  → confirmed `state: PAUSED`.
- `gcloud run jobs execute features-service-sports-job ...` (no args) → execution `features-service-sports-job-fs8sj`,
  `NonZeroExitCode`, log: `Validation failed: Batch mode requires --date or both --start-date and --end-date`.
- `gcloud run jobs execute features-service-sports-job --args="--feature-family,sports,--operation,compute,--mode,batch,--asset-group,SPORTS,--tables,fixture_features,--start-date,2026-07-14,--end-date,2026-07-15"`
  → execution `features-service-sports-job-kk4dv`, `NonZeroExitCode`, `failedCount: 1`, log:
  `Manifest consolidator appears DOWN for bucket='instruments-store-sports-prd-central-element-323112': ... heartbeat is 208s old (> 120s budget) ... recovery=fail_fast`.
- `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-instruments-sports --region=asia-northeast1 --project=central-element-323112 --limit=30`
  — continuous ~1/min executions since ≥12:14 UTC, all completing in 7.3–9.1s.
- `gcloud logging read` on 8 sampled consolidator executions (`qz4kr`, `4k224`, `5nbt9`, `9stvl`, `kb4d5`, `5jgfx`,
  `m7zhf`, `2rjjn`) — 100% show `skipping cycle ... fresh lock present (sibling cron still running)` + `error=locked`.
- `gcloud scheduler jobs list --location=asia-northeast1 --project=central-element-323112 | grep instruments-sports` →
  exactly one trigger, `ENABLED`, `*/1 * * * *`.
- `gsutil ls -l gs://instruments-store-sports-prd-central-element-323112/_index/` + `gsutil cat .../consolidator.lock` +
  `.../consolidator_stall_state.json` + `.../latest.json` — lock/latest.json rewritten every cycle with
  `error_reason: "locked"`; `availability_index.parquet` last genuine write `2026-07-15T12:39:43Z`, stale again (234s
  old) by `2026-07-15T12:43:37Z`.
