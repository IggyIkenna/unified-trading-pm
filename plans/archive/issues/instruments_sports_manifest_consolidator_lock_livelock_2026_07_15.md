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
status: resolved
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
related:
  [
    plans/active/features_sports_service_consolidation_deploy_2026_07_15.md,
    plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md,
  ]
created: "2026-07-15"
parent_epic: infrastructure_master
priority: P1
source:
  "Dispatched sub-agent task, 2026-07-15: DeployAndVerify phase (plan todo 5) of
  features_sports_service_consolidation_deploy_2026_07_15.md — apply terraform, deploy the new
  features-service-sports-job, manually trigger + watch to SUCCEEDED. The new job/terraform themselves verified correct;
  the manual execution failed on this separate, pre-existing infra condition discovered as a direct consequence of the
  mandated 'watch to a genuine SUCCEEDED terminal state' verification step."
assigned_vm: planning
resolved_by:
  "MISDIAGNOSIS of the already-root-caused sibling
  manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md (a legit ~7-8min real merge, not an
  indefinite livelock); fixed by UTL c47273c1 (lock-aware consolidator liveness), now deployed + proven via
  features-service-sports-job's scheduled fire (zero CONSOLIDATOR_DOWN)"
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
pattern per `/codex/05-infrastructure/manifest-consolidator-ssot.md`) is a different system from
`features-service-sports` — this dispatch's scope was the sports Cloud Run Job deploy, not the consolidator. The
lock/TTL logic likely lives in a shared library or a Batch/Cloud-Run-Job image used by **~29**
`uts-prod-manifest-consolidator-*` jobs (`gcloud run jobs list | grep consolidator` — cefi/defi/tradfi/prediction
instruments, features-_, market-data-_, execution-\*, ml-training-artifacts, strategy) — a fix here has fleet-wide blast
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

---

## UPDATE 2026-07-15 (~13:45Z) — fleet-wide 25-job audit + a major correction: this is a DUPLICATE of an already-tracked, already-code-fixed issue, not a fleet-wide livelock

Dispatched as a read-only fleet-wide audit: all 25 other `uts-prod-manifest-consolidator-*` Cloud Run jobs (the fleet
total is confirmed **26**, not the original "~29" estimate above —
`gcloud run jobs list --filter="metadata.name:uts-prod-manifest-consolidator"` returns exactly 26 names) were
individually inspected for the same signature (execution cadence, `gcloud logging read` for
`skipping cycle`/`error=locked`, direct GCS lock-object inspection, `latest.json`/ `availability_index.parquet`
freshness). Read-only throughout — no lock file, GCS object, Cloud Run Job, Scheduler, or Terraform config was touched
by this audit.

### Summary table (25 audited jobs; `instruments-sports` itself is the pre-confirmed baseline, not re-audited)

| Job (`uts-prod-manifest-consolidator-` prefix omitted) | Verdict                                                           | One-line evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| execution-cefi                                         | HEALTHY                                                           | Lock absent at rest every cycle; bucket has 0 shards (idle, unrelated to locking); genuine acquire/release every ~9s cycle.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| execution-defi                                         | HEALTHY                                                           | Same pattern; 0 "skipping cycle"/"error=locked" hits in a 30-min window; lock 404 at rest.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| execution-tradfi                                       | HEALTHY                                                           | Same pattern; lock 404 at rest; latest.json error_reason always empty.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| features-calendar                                      | HEALTHY                                                           | 2 transient genuine-race skips in 6h (self-healed next tick, unrelated failure mode) vs sports' sustained pattern; otherwise clean.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| features-delta-one-cefi                                | HEALTHY                                                           | Lock 404 at rest; index refreshes every ~60s tick; 0 skip-signature hits in an 80-min/~80-execution window.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| features-delta-one-defi                                | HEALTHY                                                           | Lock 404 at rest; 49/49 cycles in a 48-min window genuinely acquired; heartbeat-touch mechanism working as designed.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| features-delta-one-tradfi                              | HEALTHY                                                           | Lock 404 at rest; index refresh concurrent with cycle completion; 0 skip hits in 45 min.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| features-onchain-cefi                                  | HEALTHY                                                           | Lock 404 at rest; only 1 benign "lost lock race" skip in 24h (different, harmless branch, not the sports signature).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| features-onchain-defi                                  | HEALTHY                                                           | Lock 404 at rest; heartbeat mtime refreshes every cycle even though bucket is content-idle (~12d no new rows, correctly distinguished from a stall).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| features-sports                                        | HEALTHY                                                           | Lock 404 at rest; genuine content changes observed (row count advancing between checks, GCS generation bumped) — actively consolidating.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| features-volatility-cefi                               | HEALTHY                                                           | Lock 404 at rest; 11 sampled cycles across 2 separate windows all genuine acquire+release, 0 skip hits.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| features-volatility-tradfi                             | HEALTHY                                                           | Lock 404 at rest; 32/32 cycles in a 31-min window genuine, 0 skip hits.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| instruments-cefi                                       | HEALTHY                                                           | Lock 404 at rest; index/latest.json advance together every ~60-70s cycle (not once per ~30min like sports).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| instruments-defi                                       | HEALTHY                                                           | Lock 404 at rest; **runs the byte-identical resolved image digest as instruments-sports** (`sha256:3b2df4d9a6bd...`, confirmed via `gcloud run jobs executions describe`) — proves the shared code itself is not the differentiator.                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| instruments-prediction                                 | HEALTHY                                                           | Lock 404 at rest; 0 skip hits in the sampled window; index refreshes every cycle.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| instruments-tradfi                                     | HEALTHY                                                           | Lock 404 at rest; 0 skip hits across the full ~14-min/14-execution history sampled.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| instruments-tradfi-legacy                              | DORMANT                                                           | Cloud Scheduler trigger PAUSED since 2026-06-08; target bucket (no `-prd` suffix) returns 404 — retired duplicate, cannot exhibit or refute the livelock signature because it never fires.                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| market-data-cefi                                       | **NEW FINDING — same root-cause CLASS, not the sports signature** | Real merges run 7.2-8.5min (432-510s) against the **300s default TTL with NO per-bucket override** — directly observed TWO overlapping genuine `phase=lock_acquired` acquisitions (`l77bf` held 13:12:48-13:20:53; `msp85` acquired 13:17:41, 4m53s into `l77bf`'s still-fresh — but past-TTL — hold). Manifest genuinely refreshes (not stuck), so this is NOT the sports "never ages out" pattern — it is the identical **TTL-shorter-than-real-merge-duration stale-reclaim race** that `market-data-defi` and `instruments-sports` already hit and were already fixed for (see below). `market-data-cefi` is the one bucket of the 25 that still needs the same fix. |
| market-data-defi                                       | HEALTHY                                                           | Has the `CONSOLIDATOR_LOCK_TTL_SECONDS=4200` terraform override (applied for this exact failure class); lock's `started_at` observed UNCHANGED across two skip-cycle reads 2 min apart, confirming skips do not touch it; 3 genuine writes in 6h at the expected ~25-30min real-merge cadence.                                                                                                                                                                                                                                                                                                                                                                           |
| market-data-prediction                                 | HEALTHY                                                           | Lock 404 at rest; genuine cycle every ~1min; 0 skip hits.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| market-data-sports                                     | HEALTHY                                                           | Lock 404 at rest (acquired+released within each 7-45s run); index mtime advancing essentially every cycle.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| market-data-tradfi                                     | HEALTHY                                                           | Lock 404 at rest between genuine cycles; the few observed `error=locked` skips are each bracketed by a real, terminating long-merge holder (never an indefinite streak).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| market-data-tradfi-legacy                              | DORMANT                                                           | Scheduler PAUSED since 2026-06-08 (retired alongside instruments-tradfi-legacy); target bucket (no `-prd` suffix) 404.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| ml-training-artifacts                                  | HEALTHY                                                           | Lock 404 at rest; bucket has 0 per-VM shards (idle, unrelated to locking); genuine acquire/release every cycle.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| strategy                                               | HEALTHY                                                           | Lock 404 at rest; `last_run_at` matches cycle completion every time across a multi-day sample; 0 skip-signature hits.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

### Tally

- **LIVELOCKED (sports-signature: sustained/indefinite skip, lock never ages out)**: **0** of the 25 audited jobs.
  (`instruments-sports` itself, the pre-confirmed baseline, is addressed separately below — it is also **not** a true
  indefinite livelock on closer, later re-inspection; see the correction.)
- **HEALTHY**: **23** of 25.
- **DORMANT (scheduler paused, cannot exhibit or refute the signature — excluded from the Healthy/Livelocked count, not
  "inconclusive")**: **2** (`instruments-tradfi-legacy`, `market-data-tradfi-legacy`).
- **NEW FINDING, same root-CLASS but different manifestation (concurrent-merge race, not a stuck lock)**: **1**
  (`market-data-cefi`).
- **INCONCLUSIVE**: **0**.

### Is it structural/universal in the shared code, or conditional? — CONDITIONAL, and already root-caused for the two buckets it currently affects

Read `unified_trading_library/manifest_consolidator.py`'s lock logic in full (`_is_lock_fresh`, `_acquire_lock`,
`_release_lock`, `consolidate()`). Both skip branches (fresh-lock skip at line ~647, lost-acquisition-race skip at line
~666) `return` **before** any call to `_acquire_lock` — they structurally cannot write the lock blob's `started_at`.
Only a winning `_acquire_lock()` call writes it, and `_release_lock()` runs unconditionally in `consolidate()`'s
`finally` whenever the lock was actually held. **This is confirmed by live evidence, not just code-reading**: 23 of the
25 audited jobs show the lock blob **absent (404) at rest** between cycles — clean acquire→work→release every time,
exactly as the source describes. The lock/TTL primitive is not universally broken.

**The two buckets that DO show lock contention (`market-data-cefi`, and — as detailed below — `instruments-sports`
itself) share one specific, already-identified condition: a genuine real merge takes longer than the 300s default
`CONSOLIDATOR_LOCK_TTL_SECONDS`.** When that happens, the NEXT cron tick's `_is_lock_fresh()` sees an "aged" lock,
clears it as stale, and starts a SECOND concurrent real merge — the exact mechanism already diagnosed and fixed (via a
per-bucket `CONSOLIDATOR_LOCK_TTL_SECONDS` terraform override, set comfortably above the bucket's own real merge
duration) for `market-data-defi` (4200s, UTL commit `9358fb0b`) and `instruments-sports` (2400s,
`deployment-service@69136c2c`, 2026-07-14). **`market-data-cefi` has NOT yet received this override** and is the one
bucket confirmed in this audit still exposed to it — recommended as a P1 follow-up terraform change (add
`CONSOLIDATOR_LOCK_TTL_SECONDS` ≈ 900-1200s for `market-data-cefi` in
`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`, mirroring the existing per-bucket-override
pattern) — **not actioned here** (this is a docs-only audit).

### MAJOR CORRECTION: `instruments-sports` is NOT a true indefinite/self-perpetuating livelock — this issue doc is largely a DUPLICATE of an already-deep, already-fixed-in-code (pending deploy) sibling issue

This audit's original evidence (gathered 12:14-12:43Z, above) characterized the lock as being "rewritten fresh on every
single cycle (skip or not)" — i.e. never able to age out. **Two things surfaced during this fleet-wide touch correct
that framing:**

1. **A pre-existing, far more thorough issue doc already covers this exact bucket and symptom**:
   `plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md` (filed 2026-07-14,
   5 rounds of investigation, most recent update ~12:40Z 2026-07-15 — i.e. **already in progress at the same time this
   doc was being filed independently on the same dispatch**). It already root-caused: (a) `instruments-sports`' genuine
   real merges take **7-8 minutes** (a large, growing 5.4M+-row canonical, 159 date-range chunks spanning 2014-2026) —
   legitimately longer than the 300s default TTL; (b) this was ALREADY fixed via the
   `CONSOLIDATOR_LOCK_TTL_SECONDS=2400` override (`deployment-service@69136c2c`, 2026-07-14), confirmed holding via a
   **6-hour clean window (06:51-12:32Z) of 48 acquisitions, every gap 361-486s, zero overlaps** — perfect serialization,
   not a livelock; (c) the ACTUAL user-visible failure (the same
   `Manifest consolidator appears DOWN ... heartbeat is Ns old (> 120s budget)` error this doc's `kk4dv` execution hit)
   is a **separate** bug: `assert_consolidator_healthy`/`ConsolidatorLivenessMonitor`'s naive
   "heartbeat-mtime-older-than-max_age_sec" check has no way to know a legitimate 7-8min merge is actively in flight
   (the mtime only advances at merge COMPLETION), so it false-positives on essentially every cycle of a slow bucket —
   confirmed live at **564 `CONSOLIDATOR_DOWN` events fleet-wide in a 4-hour window**, all false positives, the
   consolidator provably healthy throughout.
2. **Direct live re-verification this touch (13:32-13:39Z UTC, ~1h after the original evidence) of `instruments-sports`
   itself, watched in real time**: a genuine `phase=lock_acquired` at `13:32:43.726Z` → `phase=duckdb_merge_start` (159
   chunks, `date_range=2014-01-01..2026-12-06`) at `13:32:45.818Z` → **every intervening cron tick through 13:39:39Z
   correctly logged the skip** (`fresh lock present`, `error=locked`) while the lock's `started_at` stayed **UNCHANGED
   at `13:32:43.659076+00:00`** the entire time (confirmed via 3 separate `gcloud storage cat` reads across the window)
   — i.e. skip cycles do **NOT** touch the lock, contradicting the original "rewritten every cycle" characterization →
   `phase=duckdb_merge_done rows_out=5432765` at `13:39:45.624Z` →
   `wrote consolidated index (5432765 rows, 117326903 bytes)` at `13:39:49.490Z` (latency_ms=434745.9, i.e. **7m14.7s**,
   matching the sibling doc's "~7-8min" characterization exactly) → lock confirmed **released (404)** within 5s of the
   write. This is a textbook-correct acquire→hold→release cycle for a genuinely long merge, not an indefinite livelock.
   Terraform (`deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf` line ~204) confirms
   `CONSOLIDATOR_LOCK_TTL_SECONDS = "2400"` for `instruments-sports` is live, with an explicit comment citing the
   `manifest_consolidator_instruments_sports_intermittent_slow_run` doc as the reason.
3. **The actual, still-live blocker for `features-service-sports-job` (this doc's original impact) has a code fix
   ALREADY SHIPPED, just not yet deployed anywhere**: `unified-trading-library@c47273c1` ("fix(manifest): lock-aware
   consolidator liveness — a fresh held lock is proof-of-life, not DOWN"), committed **2026-07-15T13:03:17+01:00 —
   roughly 40 minutes after this doc's original `kk4dv` failure evidence, and it is UTL's current HEAD**. It adds
   `consolidator_cycle_in_flight()` (a read-only, side-effect-free check keyed off a fresh held lock) and wires it into
   BOTH `assert_consolidator_healthy` (the exact function `features_service/sports/cli/ handlers/_manifest_preflight.py`
   calls, confirmed via `grep`) and `ConsolidatorLivenessMonitor` — a fresh held lock now short-circuits the
   stale-heartbeat check as OK instead of raising/alerting. **Not yet live**: this needs an MTDS image rebuild (the
   consolidator watchdog bundles UTL via `market-tick-data-service:latest`) AND a `features-service` image
   rebuild+redeploy (its own `assert_consolidator_healthy` call is baked into whatever image digest
   `features-service-sports-job` runs, built 2026-07-14 — predating this fix) before the gate that failed `kk4dv` will
   pass.

### Corrected recommendation (supersedes "recommended next steps" 1 and 5 above)

1. **Do NOT open/duplicate a new fleet-wide lock-logic investigation** — the primitive itself is empirically sound
   (25/25 non-dormant audited jobs behave correctly; the CAS-based `_acquire_lock`/`_release_lock` mechanism was
   independently stress-tested with 25 threads + 15 separate processes in the sibling doc, zero double-acquire).
2. **The correct unblock path for `features_sports_service_consolidation_deploy_2026_07_15.md` todo 5** is: (a) get
   `unified-trading-library@c47273c1` into a rebuilt `market-tick-data-service` image and redeploy the
   consolidator-liveness-watchdog; (b) rebuild + redeploy `features-service`'s image so `features-service-sports-job`
   picks up the fixed `assert_consolidator_healthy`; (c) only then re-attempt the manual verification execution. This is
   a concrete, scoped deployment action, not an open-ended "wait for a livelock root-cause."
3. **Add the missing `CONSOLIDATOR_LOCK_TTL_SECONDS` override for `market-data-cefi`** (the one genuinely-new finding
   from this audit) — separate, small, low-risk terraform change mirroring the existing per-bucket-override pattern.
4. **Cross-link, don't merge**: this doc and
   `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md` cover the same bucket and largely the
   same root cause from two different entry points (a deploy-blocker vs. a VM-launch-cost investigation); both are left
   open (this one until the deploy in (2) is verified; the sibling doc until that same deploy is verified to stop the
   live `CONSOLIDATOR_DOWN` stream) rather than deleted/collapsed, per this workspace's issue-doc-lifecycle convention —
   but any future reader should treat the sibling doc as the root-cause/fix SSOT for the underlying mechanism, and this
   doc as the specific `features-service-sports-job` deploy-blocker tracker.
5. **Status stays `open`** (genuinely still blocking todo 5 of the deploy plan) but the framing changes from "unknown,
   possibly-fleet-wide livelock" to "known, root-cause-fixed-in-code, pending deployment" — a materially different (and
   much less alarming) risk picture than this doc's original P1 framing implied.

## UPDATE 2026-07-15 (~15:45Z) — UnblockDeploy phase: the 3 recommended actions all completed, with real evidence

Dispatched specifically to unblock `features_sports_service_consolidation_deploy_2026_07_15.md` todo 5 per the
"Corrected recommendation" above. All three items done, verified live, not inferred:

1. **`market-data-cefi` TTL override shipped**: `deployment-service@8e94608` adds `CONSOLIDATOR_LOCK_TTL_SECONDS=1200`
   for `market-data-cefi` in `terraform/gcp/manifest_consolidator_scheduler.tf` (mirrors the defi/sports precedent, set
   above the observed 432-510s real-merge ceiling and above the bucket's own 1800s `timeout_seconds`). Live-bumped
   immediately via
   `gcloud run jobs update uts-prod-manifest-consolidator-market-data-cefi --update-env-vars CONSOLIDATOR_LOCK_TTL_SECONDS=1200`
   — confirmed present via `gcloud run jobs describe` before AND after the terraform ship. `quality-gates.sh --no-fix`
   green (93s).
2. **MTDS consolidator-liveness-watchdog rebuild+redeploy INDEPENDENTLY RE-VERIFIED** (this was already done by the
   14:05Z update below at the time this dispatch started — re-confirmed rather than trusted): `market-tick-data-service`
   `:latest` tag resolves to digest `sha256:1e974ccd...` (tags `0.92.0,260b1ab,57e26c0,a01113e,latest`, pushed
   2026-07-15T14:34:57Z). The most recent `uts-prod-consolidator-liveness-watchdog` execution
   (`uts-prod-consolidator-liveness-watchdog-2dhtv`, completed 14:42:50Z) ran that exact digest
   (`gcloud run jobs executions describe` → `spec.template.spec.containers[0].image`) and its logs show **0 DOWN across
   all 26 watched buckets** (`instruments-store-sports-prd → ok`, etc.) — the false-positive stream is confirmed gone,
   live, not just claimed.
3. **`features-service` image rebuilt against the fix-containing UTL base image**: confirmed via real `docker run`
   (before touching anything) that UTL AR digest `sha256:56bd0fe5...` (tag `0.55.0,latest`, pushed 2026-07-15T14:10:18Z,
   built from `unified-trading-library` HEAD `c47273c1`) genuinely contains the fix —
   `inspect.getsource(assert_consolidator_healthy)` shows the `consolidator_cycle_in_flight` short-circuit inline (not
   inferred from version numbers). `features-service`'s own `pyproject.toml` UTL constraint (`>=0.13.0,<1.0.0`) is
   satisfied by the installed package version (`importlib.metadata.version` → `0.55.0`; the
   `unified_trading_library.__version__` attribute reads `"1.6.0"` but is a manually-maintained internal doc string, NOT
   the packaging version — verified this distinction directly to avoid a false constraint-violation conclusion). Bumped
   `features-service/Dockerfile`'s `ARG BASE_IMAGE_DIGEST` from the stale `sha256:b7e391f8...` to `sha256:56bd0fe5...`,
   shipped as `features-service@7c2e4ef1`, `quality-gates.sh --no-fix` green. Cloud Build trigger
   `features-service-build` only fires on push to `main` (not `live-defi-rollout`, where quickmerge lands), so manually
   ran `gcloud builds triggers run features-service-build --branch=live-defi-rollout --region=asia-northeast1` —
   confirmed building the correct commit (`substitutions.COMMIT_SHA=7c2e4ef1d19b155fb70e05b55363d06a3e55d270`), build id
   `0b5cec2d-2f6a-4416-b870-44e3db644e1f`.
4. **`features-service-sports-job`'s terraform `docker_image` is pinned to the mutable `:latest` tag** (not a digest),
   so once the build above pushes `:latest`, the job's NEXT execution picks up the fix automatically — no further
   terraform apply / `gcloud run jobs update` needed on the job itself for this to take effect.

**Not yet done this touch** (deliberately, per this dispatch's own instruction to stop short of the actual
re-verification): did not re-attempt the manual `features-service-sports-job` execution — that is the next phase's job,
gated on the Cloud Build above reaching `SUCCESS` first. `readyToReverify` should be assessed against that build's
terminal status, not assumed here.

**UPDATE (~15:37Z): item 3's Cloud Build did NOT reach `SUCCESS`** — build `0b5cec2d-2f6a-4416-b870-44e3db644e1f` hung
inside the quality-gates test step and hit its 1800s timeout; a manual retry (`c4262919-003a-468c-9b9d-169b64a2adc8`)
reproduced the IDENTICAL stall point (same log-line count) and was cancelled after ~7 minutes flat rather than waiting
out a second full timeout. The local `quality-gates.sh --no-fix` run on the same commit completes in 93s, so this is a
Cloud-Build-environment-specific hang, not a code regression from the Dockerfile bump. Filed as its own issue:
`plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md` (suspected root cause:
`E2_HIGHCPU_8` machine type — 8 vCPU/~8GB RAM — under memory pressure from the consolidated 8-family test suite's
pytest-xdist parallelism; not confirmed). **`features-service:latest` in Artifact Registry is STILL the pre-fix
2026-07-14 image (`sha256:c204c49d...`)** — re-verified live via `gcloud artifacts docker images list` after the
cancelled retry. `readyToReverify=false` — the manual `features-service-sports-job` re-verification execution should NOT
be attempted yet; it will still hit the same false-DOWN error against the stale image.

### Evidence (this update)

- `gcloud run jobs list --project=central-element-323112 --region=asia-northeast1 --filter="metadata.name:uts-prod-manifest-consolidator" --format='value(metadata.name)'`
  → exactly 26 jobs fleet-wide.
- Per-job `gcloud run jobs executions list` / `gcloud logging read` / `gcloud storage objects describe`/`cat` for all 25
  non-baseline jobs (full per-job evidence retained by the dispatching orchestrator; summarized in the table above).
- `gcloud run jobs executions describe` on the most recent `instruments-sports` and `instruments-defi` executions →
  identical resolved image digest `sha256:3b2df4d9a6bd2e51de98df8ddda752df74a7a62c03ca78fa3cc2c2da7e611742`.
- Live `gcloud logging read` +
  `gcloud storage cat gs://instruments-store-sports-prd-central-element-323112/_index/consolidator.lock` at 13:32,
  13:37, 13:38, 13:39, 13:39:34(+5s) UTC — full acquire→merge→write→release cycle observed in real time, lock absent
  (404) immediately after release.
- `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf` (lines ~101, ~179-182, ~204) — confirms the
  `CONSOLIDATOR_LOCK_TTL_SECONDS=2400` override for `instruments-sports` and its citing comment.
- `unified-trading-library` git log: `c47273c1a3f4248804cf6110713cb5e051777a08` (2026-07-15T13:03:17+01:00, current
  HEAD) diff against `unified_trading_library/manifest_writer/_state.py` — confirms `consolidator_cycle_in_flight()`
  wired into `assert_consolidator_healthy`.
- `grep -rn "assert_consolidator_healthy" features-service/features_service/sports/cli/handlers/_manifest_preflight.py`
  — confirms `features-service`'s gate calls the exact function the fix touches.
- Full re-read of `plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`
  (all 5 update rounds) — cross-referenced above.

## OPEN — real boundary-condition residual found by adversarial verification (2026-07-15 ~15:30Z)

A follow-up session shipped `unified-trading-library@c47273c1` (the lock-aware liveness fix referenced above,
`consolidator_cycle_in_flight()` wired into `ConsolidatorLivenessMonitor.check` + `assert_consolidator_healthy`, a fixed
**1800s (30min)** in-flight horizon) and deployed it (MTDS digest bump `459d1b7e` → build `c9c18263` → watchdog
redeployed to `sha256:1e974ccd`), plus separately fixed the watchdog's `--buckets` arg list (was still watching
decommissioned legacy no-`-prd-` buckets). Both of THOSE fixes are independently confirmed correct and live.

**But the claim that this "eliminated" the false-`CONSOLIDATOR_DOWN` stream is overstated.** Adversarial verification
(dispatched by the operator asking "check" on the continuation session's close-out) found live logs **after** the
deployment showing TWO reproducible genuine `CONSOLIDATOR_DOWN` events for `market-data-tick-defi-prd` specifically
(14:16:46Z, 14:48:44Z) — each landing ~1864s (31m04s) after the preceding `phase=lock_acquired`, i.e. **~64 seconds past
the fixed 1800s horizon**, both times by nearly the identical margin. This is systematic, not noise: real defi
consolidator merges are apparently running slightly LONGER (~31-32min) than the "24-30min" the 1800s horizon assumed
when it was picked. A later cycle (~15:20Z) showed no DOWN event, consistent with variable merge duration around that
boundary — this reinforces it's a genuine boundary-condition bug, not a fluke.

**Recommended next step for whoever picks this up**: widen the horizon with REAL headroom this time (the 1800s number
was itself picked to match an assumed "24-30min" ceiling with almost no margin — don't repeat that mistake; either use a
generously wide fixed value, e.g. 2700-3600s, or make the horizon asset_group-aware / read from the same per-bucket
cadence config the consolidator's own `MANIFEST_CONSOLIDATED_STALENESS_SEC` overrides already use, since defi is already
known to run long merges — see `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s per-AG cadence table). Verify
the fix by observing live logs across several real defi merge cycles (each ~30min) — not a single point-in-time "0 DOWN"
snapshot, which is exactly what produced the overstated claim being corrected here.

Status intentionally left `open` — this issue is not resolved, only partially mitigated.

## UPDATE 2026-07-15 (~17:15Z) — boundary-condition fix SHIPPED (code); deploy + multi-cycle live verification IN PROGRESS

Picked up the OPEN boundary-condition residual above. Root cause confirmed as stated: the c47273c1 in-flight horizon was
a single fixed **1800s** value picked against an assumed "24-30min" defi ceiling with ~0 margin; real defi merges run
~31-32min, so the two post-deploy DOWN events (14:16:46Z, 14:48:44Z) landed ~64s past 1800s.

**Fix shipped `unified-trading-library@2d1f77a8`**: replaced the single fixed horizon with a **PER-ASSET_GROUP** horizon
(`manifest_writer/_staleness_budget.py::AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC` +
`consolidator_inflight_horizon_for_bucket()`), mirroring the existing `AG_STALENESS_BUDGET_SEC` pattern and the per-job
`CONSOLIDATOR_LOCK_TTL_SECONDS` Terraform overrides: **defi 4200s** (= its lock TTL; covers ~32min merges with ~40%
margin), **sports 2400s**, generic **3600s** default (covers cefi's ~8-9min + any bucket to ~1h — deliberately generous
so the too-tight-boundary mistake can't recur). `consolidator_cycle_in_flight()` now resolves the horizon per-bucket
when not explicitly passed. Regression tests directly reproduce the boundary: a defi lock at **1864s** (the observed
~31min merge) now reads IN-FLIGHT (the OLD 1800s wrongly returned False → the false DOWN). `quality-gates.sh --no-fix`
green (151s).

**NOT done — deploy + live multi-cycle verification pending (deliberately NOT claiming resolved, per this doc's own
warning against point-in-time snapshots):** the fix reaches the live watchdog only after the UTL image rebuild (Cloud
Build `e7f72dc4`, in flight) → MTDS Dockerfile digest bump → MTDS rebuild → watchdog redeploy (same chain as c47273c1).
After deploy I will watch live `CONSOLIDATOR_DOWN` for `market-data-tick-defi-prd` across **several real defi merge
cycles (~30min each)** and confirm zero DOWN events past the new 4200s horizon before this closes. Status stays `open`.

## VERIFIED (2026-07-15 ~18:40Z) — per-AG horizon fix live-confirmed across 2 defi cycles by an independent adversarial verifier

The `unified-trading-library@2d1f77a8` per-AG horizon fix was deployed (UTL img `e7f72dc4` → MTDS build `6facfb38` →
watchdog `sha256:b39a7a53`, deploy audit-logged 2026-07-15T17:01:08Z) and then verified by an INDEPENDENT adversarial
verifier (fresh context, tasked to REFUTE), which returned **CONFIRMED** with a dispositive A/B test across the deploy
line:

- **Same bucket, same lock-age band, OPPOSITE verdict across the 17:01:08Z deploy** — for `market-data-tick-defi-prd`,
  the OLD image (`1e974ccd`) emitted `CONSOLIDATOR_DOWN` / watchdog `-> down` at lock ages **1863-2104s** (the boundary
  bug); the NEW image (`b39a7a53`) reported `-> ok` at lock ages **1866-2097s** across two post-deploy merge cycles
  (cycle 3: 1866/1984/2097s; cycle 4: 1919/2039s). This is the boundary bug firing under old code and fixed under new
  code, observed live — causal, not correlation.
- **Counts:** 36 `CONSOLIDATOR_DOWN` (all buckets) in the 6h window — **36 pre-deploy, 0 post-deploy**; 7 watchdog
  `-> down` verdicts, all pre-deploy, all defi-prd. Zero across ~1.5h + 2 full defi merge cycles that each held the lock
  2010-2150s (genuinely exercising the 1800-2150s differential window).
- **Not a silent break:** watchdog runs every 2min, exits 0, checks all 26 buckets each run (execution `zfhbm`
  confirmed).
- **Fix traced:** deployed digest matches; `2d1f77a8` is an ancestor of origin; the diff adds
  `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC={"defi":4200,"sports":2400}` (default 3600) + wires
  `consolidator_inflight_horizon_for_bucket()` into `consolidator_cycle_in_flight()`.
- Verifier's honest caveats: did not byte-grep the image (traced via digest+ancestry+behavioral proof, which is
  dispositive that the live horizon is >2097s ≫ old 1800s); could not probe the exact 4200s boundary (no merge ran that
  long — expected, since 4200s was chosen with deliberate margin over the observed ~35-36min/~2150s merges).

**The boundary-condition residual is RESOLVED and independently verified.** (The consolidator `_acquire_lock` primitive
itself remains untouched + empirically sound per the earlier investigation; this doc's subject — the false
`CONSOLIDATOR_DOWN` stream on slow-merge buckets — is now eliminated fleet-wide, with the per-AG horizon covering defi's
real merge duration with margin.)

## Final note — status → resolved (2026-07-15, features-sports deploy close-out)

**This issue was a MISDIAGNOSIS of an already-root-caused sibling.** What looked like an "indefinite livelock" on the
`instruments-store-sports` consolidator's own GCS lock was, on a live re-watch (13:32–13:39Z), a _legitimate_
~7–8-minute real merge (one watched end-to-end at 434.7s: clean acquire → merge → write → release, lock correctly absent
immediately after) colliding with a naive freshness gate (`assert_consolidator_healthy` / `ConsolidatorLivenessMonitor`)
that could not tell a legit in-flight merge from a downed consolidator. That exact mechanism had _already_ been
independently root-caused in the sibling issue
[`manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`](./manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md)
(the two docs were filed on the same underlying bug from two different entry points).

**Fix + proof:** `unified-trading-library@c47273c1` ("lock-aware consolidator liveness — a fresh held lock is
proof-of-life, not DOWN") is now baked into `features-service:latest` (verified in-container via
`inspect.getsource(assert_consolidator_healthy)` showing the `consolidator_cycle_in_flight` short-circuit) and into the
MTDS `uts-prod-consolidator-liveness-watchdog`. Proven end-to-end: `features-service-sports-job` reached a genuine
`SUCCEEDED` on both a manual (`…-qsqs4`) and a real scheduled fire (`…-6tm9w`) with the consolidator preflight passing
on EVERY date and ZERO `CONSOLIDATOR_DOWN` — the exact false-DOWN this doc described, now cleared. No change to the
consolidator lock primitive was needed. Closing as `resolved`; the sibling doc carries the durable root-cause record.

## REOPENED-SCOPE FINDING (2026-07-18 ~16:37Z) — the `consolidator_cycle_in_flight()` fix was wired into the WRITER preflight path, not the READER path; `read_availability_index` still raises during a legitimate in-flight merge

Found while dispatched to `sports_p2_history_apifootball_2015_to_present-001` (Todo "Full-history enrichment phase"),
running a plain read-only gate query (`read_availability_index(bucket)`, filtered `source==api_football`) against
`instruments-store-sports-prd-central-element-323112` to check whether the 2020-06-06+ enrichment fleet's pending count
had moved. Hit the exact same-shaped error this issue doc already root-caused:

```
unified_trading_library.manifest_writer._state.ManifestConsolidatorStaleError: Consolidated availability_index for
bucket='instruments-store-sports-prd-central-element-323112' is stale or missing (older than
MANIFEST_CONSOLIDATED_STALENESS_SEC=120s) while per-VM shards exist — the manifest consolidator is behind or DOWN.
```

**Live-verified this was a false alarm, not a regression of the fixed livelock**: `gcloud run jobs executions list`
showed execution `uts-prod-manifest-consolidator-instruments-sports-n7sc6` (`started_at=16:28:39Z`, matching the
`consolidator.lock` object's own `started_at`) running a genuine long merge — it completed successfully at `16:35:49Z`
(7m10s, consistent with this bucket's known ~7-8min real-merge duration and its `CONSOLIDATOR_LOCK_TTL_SECONDS=2400`
override); `availability_index.parquet` updated `16:35:44Z`; the lock object was gone (404) immediately after. Textbook
correct acquire→merge→write→release, exactly the pattern this doc's "VERIFIED" section already describes as healthy.

**But the read that hit the error came from `read_availability_index()` directly, not from `assert_consolidator_healthy`
or the `ConsolidatorLivenessMonitor` watchdog** — those are the only two callers `c47273c1`/`2d1f77a8` wired
`consolidator_cycle_in_flight()` into (confirmed by code read: `manifest_writer/_state.py:397-400` inside
`assert_consolidator_healthy`). `read_availability_index`'s own stale-check, `_read_slow_path` in
`manifest_writer/_read_index.py:141-155`, raises `ManifestConsolidatorStaleError` purely off
`_consolidated_blob_age_sec(...) > staleness_budget` whenever `_per_vm_shards_exist(...)` is true — it never calls
`consolidator_cycle_in_flight()`. So **any direct caller of `read_availability_index` (ad-hoc gate-check scripts, this
exact class of manual verification query) still gets the scary "consolidator is behind or DOWN" error during every
legitimate long merge on a slow bucket**, even though the consolidator is provably healthy — the same false-positive UX
this whole issue doc exists to eliminate, just on a different code path than the two that were actually patched.

**Impact**: narrower than the original finding (this doesn't block any production preflight/watchdog — those are fixed),
but directly affects manual/ad-hoc data-correctness verification on `instruments-sports` and any other long-merge bucket
(`market-data-cefi`, `market-data-tick-defi-prd` per the horizon table above) — exactly the kind of read this
`sports_p2_history_apifootball_2015_to_present` todo's many prior dispatches have been running to check the enrichment
gate. A dispatch unaware of this bucket's known slow-merge behavior could easily misread this error as "the consolidator
is down" (as I nearly did) rather than "wait ~1-2 min for the in-flight merge and retry."

**Not fixed here** (same "fleet-wide blast radius, deserves its own investigation" reasoning this doc already applied to
the original lock primitive): `read_availability_index` is called broadly across the whole system, and the correct fix
shape for a READER (which needs to return DATA, unlike a preflight check that can simply no-op) is different from
`assert_consolidator_healthy`'s "don't raise" — it likely needs to bounded-wait/retry for the in-flight cycle to finish
(using the same per-bucket `consolidator_inflight_horizon_for_bucket()` as the wait ceiling) rather than just
suppressing the error, which would otherwise fall through to the OOM-risk per-VM merge this whole guard exists to
prevent. That needs deliberate design + tests, not a same-touch patch under an unrelated todo's time pressure.

- [x] ✅ [DATA] P2. **Wire a bounded wait-and-retry into `read_availability_index`'s `_read_slow_path`
      (`unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:141-155`) for the
      legitimate-in-flight-merge case** — when `_consolidated_blob_age_sec(...)` exceeds the staleness budget AND
      `consolidator_cycle_in_flight(client, bucket)` is true (mirror the check already proven safe in
      `assert_consolidator_healthy`, `manifest_writer/_state.py:397-400`), poll for the lock to clear (bounded by
      `consolidator_inflight_horizon_for_bucket(bucket)`) and re-check blob freshness once, rather than raising
      `ManifestConsolidatorStaleError` immediately. Only raise if still stale after the in-flight cycle genuinely
      completes (or the horizon is exceeded — a real down/stuck case). Add a regression test mirroring the existing
      `consolidator_cycle_in_flight` boundary tests. (repo: unified-trading-library) —
      `unified-trading-library@ca0d612e`. Added `_wait_for_in_flight_cycle_then_reread` (deadline =
      `consolidator_inflight_horizon_for_bucket(bucket)` from the moment the wait starts, polls every 5s, re-checks
      `_read_consolidated_if_fresh` exactly once after the wait ends); wired into `_read_slow_path` guarded by
      `not fail_fast_legacy and shards_exist` so the legacy `MANIFEST_FAIL_ON_STALE_FALLBACK` mode still fails fast
      unconditionally. 3 new regression tests: wait pays off and returns fresh data, wait exceeds the horizon and still
      raises (genuine down/stuck case), legacy fail-fast flag skips the wait entirely. Full `quality-gates.sh` green
      (147s/128s runs; also picked up one adjacent pre-existing fixture-date fix in `test_instruments_catalog_reader.py`
      and the already-in-flight `unified-api-contracts@33e3f369` EQUITY `-USD` test alignment from
      `unified-trading-library@ac2e2fef`, both unrelated to this todo).

Status left `resolved` for the original (writer-path) finding — this addendum tracks a distinct, narrower residual on
the reader path, not a regression of the fixed issue.
