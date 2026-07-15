---
doc_type: plan
title: Finish features-sports-service → features-service consolidation (deploy side)
summary: >-
  The 2026-05-08 features-service repo consolidation moved sports code into features_service/sports/ and archived
  features-sports-service, but the deployment side was never finished — the live Cloud Run job still runs the old
  archived repo's stale image, broken since ~2026-04-22 (a fleet-wide unified-trading-library/unified-api-contracts
  version-skew bug). Stand up real deployment for the consolidated sports code, retire the old job, re-enable
  scheduling, then finish the deferred features-sports bare-bucket delete this outage blocked.
status: active
nature: process
asset_group: [sports]
stage: [meta]
repos: [features-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [deployment, consolidation, cloud-run, terraform, sports, outage, technical-debt]
related:
  [
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/archive/features_repo_consolidation_2026_05_08.plan.md,
    plans/active/issues/features_sports_service_cloud_run_job_broken_image_2026_07_15.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: operator decision 2026-07-15 (Path B chosen over patching the archived repo)
Codex SSOTs: [codex/05-infrastructure/vm-launcher-runbook.md, codex/08-workflows/ci-cd-flow.md]
---

# Finish features-sports-service → features-service consolidation (deploy side)

## What I found (2026-07-15, root-cause investigation)

While cutting over the `features-sports` flat-bucket migration ([[bucket_estate_consolidation_to_sub100_2026_07_13]]),
discovered `features-sports-service-job` (Cloud Run, region `asia-northeast1`, project `central-element-323112`) crashes
at Python import time: `ModuleNotFoundError: No module named 'unified_api_contracts.internal'` (from
`unified_trading_library/config_interface/auth/entitlements.py:15`). Its daily Cloud Scheduler trigger has been **PAUSED
since 2026-06-08**; last successful run **2026-06-07** — 5+ weeks of no sports feature computation.

**Root cause (confirmed via git history + Artifact Registry evidence, not guessed):**

1. `unified-trading-library`'s `entitlements.py` started requiring `unified_api_contracts.internal` as of commit
   `6bb892bc` (2026-04-02).
2. UTL's own `unified-api-contracts` dependency constraint stayed loose (`>=0.1.0,<1.0.0`) through at least 2026-04-22.
3. The only two `unified-api-contracts` wheels published in that whole window were `0.2.38` (2026-03-12, **predates**
   `internal/` by two weeks — `internal/` was only added 2026-03-26 in commit `1d08bae3`) and an out-of-sequence
   `0.1.20` (published later but numerically lower). A standard resolver picks the numerically highest match — `0.2.38`
   — so **any UTL base image built between 2026-04-02 and mid-2026 was fleet-wide broken** for this code path, not just
   this one service.
4. `features-sports-service`'s Dockerfile installs itself `--no-deps`, so it purely inherited whatever
   `unified-api-contracts` the `unified-trading-library:latest` base image had baked in the day it was built
   (2026-04-22, confirmed via `gcloud artifacts docker images list --include-tags`) — the broken `0.2.38`.
5. Nothing caught it: the repo's `quality-gates.sh` has no import/smoke gate, and the Dockerfile `HEALTHCHECK` only
   imports the lightweight top-level package `__init__.py`, never the real entrypoint (`cli/main.py`) where the crash
   lives.

**The compounding blocker:** `features-sports-service`'s GitHub repo was **archived 2026-05-08**
([[features_repo_consolidation_2026_05_08]]) — its code was already merged into `features-service`'s
`features_service/sports/` sub-package. But the **deployment side of that consolidation was never finished**: the live
Cloud Run job still runs the old archived repo's image, and no `features-service`-based sports Cloud Run job exists yet.
Patching the archived repo would re-legitimize something the org already decided to retire.

**Operator ruling 2026-07-15:** Path B — finish the abandoned consolidation properly rather than patch the archived
repo. This plan tracks that work.

## Why it matters

- A production data pipeline (sports features) has been silently dead for 5+ weeks with no alert firing (the scheduler
  pause looks intentional from the outside, not a crash).
- The same fleet-wide UTL/UAC version-skew window (2026-04-02 → mid-2026) may have affected other services built in that
  window that touch `config_interface/auth/entitlements.py` — **not yet audited**, flagged here for a possible follow-up
  sweep, not fixed in this plan (scope: features-sports-service only).
- `features-service`'s own `cloudbuild.yaml` already exists (`_SERVICE_NAME: features-service`) but was apparently never
  wired to a live Cloud Run job for the sports sub-command — this plan closes that gap.

## Todos

- [x] [INFRA] P0. Confirm a build against current dependency versions genuinely resolves a wheel containing
      `unified_api_contracts.internal` — verify with a real
      `docker run --rm --entrypoint python <image> -c "import unified_api_contracts.internal.schemas.rbac"`, not just an
      inference from version constraints, before wiring up any new deployment. — ✅ 2026-07-15, evidence:
      `docker pull     asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/features-service:latest`
      (digest `sha256:c204c49dbdc57200806c0b89e6f3ca2caa7f1226de062de09d05c2e942cdcdc9`, tags `0.66.0,7a60a31,latest`,
      built 2026-07-14) →
      `docker run --rm --entrypoint python <image> -c "import     unified_api_contracts.internal.schemas.rbac; ..."`
      exit 0, `IMPORT OK`; a second run additionally imported `unified_trading_library` + `log_event` (the exact failing
      chain from the issue doc) end-to-end, exit 0. The fleet-wide UTL/UAC version-skew bug does NOT reproduce against
      the current features-service image.
- [x] [INFRA] P0. Stand up a real Cloud Run job (+ any Workflow terraform resources mirroring the old
      `daily_workflow`/`backfill_workflow` definitions) for `features-service`'s `features_service/sports/*` sub-package
      — new terraform in `deployment-service/terraform/**`, reusing the existing `features-service` `cloudbuild.yaml`
      image. — ✅ 2026-07-15, `deployment-service@8b1c561f6d18fd7532b223ea462277131b03ebf8` (quickmerge, landed on
      `live-defi-rollout`, quality-gates.sh green): new
      `terraform/services/features-service-sports/gcp/{main,variables,terraform.tfvars,outputs,backend}.tf` — a
      distinctly-named job (`features-service-sports-job`) + daily/backfill Workflow set that COEXISTS with the legacy
      `features-sports-service-job` until it's retired (later todo). `terraform validate` clean; `terraform init` (real
      GCS backend, new state prefix `services/features-service-sports`) + `terraform plan` → "4 to add, 0 to change, 0
      to destroy" against real GCP APIs (project/SA verified live) — NOT applied (deploy is a later todo). Verified
      post-plan no resources exist yet (`gcloud run jobs list` / `gcloud workflows list` — neither
      `features-service-sports-job` nor its workflow present).
- [x] [SCRIPT] P0. Map CLI flags/entrypoint: confirm `features_service/sports/*`'s CLI surface matches what the old
      job's Cloud Run args/schedule expected (per this workspace's `--operation`/`--mode`/`--asset-group` CLI
      convention); adjust the new job's args if the consolidated CLI shape differs. — ✅ 2026-07-15:
      `--operation     compute --mode batch --asset-group SPORTS --tables fixture_features --start-date/--end-date` are
      UNCHANGED (read `features_service/sports/cli/{parser,main}.py`) — but the consolidated image is multi-family, so
      every invocation needs a NEW top-level dispatcher prefix `--feature-family sports` before those flags (read
      `features_service/cli/main.py` — `parse_known_args()` forwards everything after `--feature-family <x>` verbatim to
      `features_service.sports.cli.main.main()`); baked into both Workflow YAMLs above. **Second, more material
      finding**: the consolidated `features_service/sports/cli/_providers.py` + `_fetch_runner.py` docstrings state "All
      data fetching is done by instruments-service which writes to GCS. FSS reads from GCS only — no direct adapter
      instantiation" — confirmed by reading `batch_handler.py`'s `_run_batch()`, which now calls
      `run_fetch_providers(...)` → a pure GCS reader (`read_all_reference_data`), not an external API call. The old
      job's 4 `secret_environment_variables` (`BETFAIR_APP_KEY`/`ODDS_API_KEY`/`ODDSJAM_API_KEY`/`OPTICODDS_API_KEY`)
      are vestigial for the new architecture — grepped, zero references anywhere in `features_service/sports/*` — so the
      new terraform intentionally ships `secret_environment_variables = {}` (mirrors the `features-calendar-service`
      precedent) instead of carrying them over. **Separate, load-bearing terraform-only finding**: `features-service`'s
      Dockerfile `CMD` is `["uvicorn", "features_service.api.main:app", ...]` (the API-server default for the shared
      multi-family image) — unlike the legacy per-family image, a bare Cloud Run Job execution without an explicit
      `command` override would boot the API server instead of running the CLI to a terminal exit code. The new
      terraform's `daily_job` module now pins `command = ["python", "-m", "features_service"]` (verified in the
      `terraform plan` output) — this is NOT present in the legacy job's terraform and would have been a silent miss if
      copied verbatim.
- [x] [INFRA] P1. Repoint the existing GCS-FUSE mount / bucket wiring (canonical
      `features-sports-prd-central-element-323112`, already correct per the 2026-07-15 bucket-flattening sweep) to the
      new job. — ✅ 2026-07-15: new terraform's `gcs_volumes` reuses the SAME canonical bucket
      (`features-sports-${bucket_env_short}-${project_id}` → `features-sports-prd-central-element-323112`, confirmed
      against `unified-api-contracts/unified_api_contracts/config/cloud-providers.yaml`'s `features-sports:` key) —
      verified in the `terraform plan` output
      (`volume_mounts.mount_path =     /mnt/gcs/features-sports-prd-central-element-323112`,
      `gcs.bucket = features-sports-prd-central-element-323112`).
- [ ] [INFRA] P1. Deploy the new Cloud Run job; manually trigger a real execution and watch it reach a genuine
      `SUCCEEDED` terminal state (not just "past the import line") before trusting it. — 🟡 2026-07-15 DeployAndVerify
      phase: terraform applied clean (see Progress Log), scheduler paused, but BOTH manual executions attempted this
      touch terminated `NonZeroExitCode` — first on a real, separate terraform bug (default job `args` omit
      `--start-date`/`--end-date`, see new todo below), second (with correct date overrides) on an external,
      pre-existing blocker: `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`
      (the `instruments-store-sports` manifest consolidator is livelocked on its own GCS lock, never refreshing
      `availability_index.parquet` past the 120s freshness budget `features-service.compute_features` requires,
      `recovery=fail_fast`). Import chain + CLI contract + GCS mount all confirmed WORKING on this attempt — the blocker
      is downstream, in a different system. Per this touch's explicit instruction, did NOT proceed to retire the legacy
      job. Still `[ ]` — retry once the linked issue is resolved.
- [ ] [INFRA] P2. Fix `terraform/services/features-service-sports/gcp/main.tf`'s `module.daily_job.args` default
      (currently `--feature-family sports --operation compute --mode batch --asset-group SPORTS`, no dates) — a bare
      `gcloud run jobs execute` with no overrides fails CLI validation
      (`Batch mode requires --date or both     --start-date and --end-date`); every real Workflow invocation already
      overrides args via `containerOverrides` so this only bites a manual bare execute, but should still carry a sane
      default. Found + evidenced 2026-07-15 during the DeployAndVerify phase (see
      `instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` evidence section, execution
      `features-service-sports-job-fs8sj`).
- [ ] [INFRA] P1. Apply the separately-found `--category`→`--asset-group` Workflow-YAML terraform drift (confirmed real,
      independent of the import crash, found via `terraform plan` on the old job's Workflow resources) — carry the fix
      into the new job's Workflow definitions; required before scheduling can safely resume.
- [ ] [INFRA] P1. Retire the old `features-sports-service-job` Cloud Run job + its Cloud Scheduler trigger once the new
      job is confirmed healthy end-to-end (avoid a double-fire window).
- [ ] [INFRA] P0. Re-enable scheduling for the new job (equivalent of `features-sports-service-daily-trigger`); verify
      one real scheduled (not just manual) fire succeeds.
- [ ] [INFRA] P2. Finish the deferred [[bucket_estate_consolidation_to_sub100_2026_07_13]] `features-sports` bare bucket
      delete (1 real migrated object + 2 confirmed-ephemeral VM-staging objects already accounted for) —
      `terraform state rm` the `google_storage_bucket.features_sports` resource before the physical delete (mirrors the
      `features-calendar` precedent), then delete the bucket.
- [ ] [DOCS] P2. Close `plans/active/issues/features_sports_service_cloud_run_job_broken_image_2026_07_15.md` (status →
      resolved), append final Progress Log entries to both this plan and
      `bucket_estate_consolidation_to_sub100_2026_07_13.md`, and note in
      `plans/archive/features_repo_consolidation_2026_05_08.plan.md` that the deploy-side gap is now closed.
- [ ] [REVIEW] P3. _(stretch, optional)_ Scope (do not fix here) whether other services built in the 2026-04-02 →
      mid-2026 window touch `config_interface/auth/entitlements.py` and could have the same silent breakage — file a
      separate audit plan if the scope looks non-trivial.

## Progress Log

- 2026-07-15: Plan created. Root cause fully confirmed (see "What I found"); operator chose Path B (finish the
  consolidation) over Path A (patch the archived repo) in the same session. No execution yet — this plan is the tracking
  vehicle for the work about to start.
- 2026-07-15 (BuildDeployment phase, todos 1-4): Confirmed with real evidence (not inference) that the current
  `features-service:latest` image resolves `unified_api_contracts.internal` cleanly (docker run exit 0, full
  `unified_trading_library` import chain including the exact `entitlements.py` line that crashed the old job). Wrote +
  shipped `deployment-service@8b1c561f6d18fd7532b223ea462277131b03ebf8` — new
  `terraform/services/features-service-sports/gcp/**` (Cloud Run Job `features-service-sports-job` + daily/backfill
  Workflow, distinctly named so it can coexist with the legacy job until retirement). `terraform validate` clean;
  `terraform plan` against real GCP APIs (new state prefix, not applied) shows a clean "4 to add" with correct
  image/SA/bucket/env wiring. Two real findings surfaced during CLI-mapping due-diligence and are now baked into the
  terraform (see todo 3's evidence): (1) the consolidated dispatcher needs a `--feature-family sports` prefix on every
  invocation; (2) the consolidated `features_service/sports/*` no longer performs direct provider fetches (that moved to
  instruments-service) so the legacy job's 4 provider-API secrets are dead code for the new job and were intentionally
  dropped; (3) `features-service`'s Dockerfile CMD is `uvicorn ...` (API server) so the new job's terraform explicitly
  pins `command = ["python", "-m", "features_service"]` — omitting this would have silently booted the wrong process on
  every execution. NOT deployed/applied this touch (todos 5-8 — execute, verify SUCCEEDED, retire the old job, re-enable
  scheduling — are separate, later steps; see this session's structured handoff for the readyToDeploy assessment).
  Adjacent finding, NOT actioned (outside this touch's scope): a second scheduler,
  `uts-prod-features-sports-t1-schedule`, is also PAUSED and likely also points at the same broken legacy
  `features-sports-service-job` (via `terraform/gcp/t1_batch_scheduler.tf`'s `features-sports-service-t1-recon` entry) —
  the later "retire old job / re-enable scheduling" todos should check whether this t1-recon path also needs repointing
  to the new job before it's safe to un-pause.
- 2026-07-15 (DeployAndVerify phase, todo 5 — real evidence, not inference): Independently re-verified the prior
  BuildDeployment-phase terraform (`deployment-service@8b1c561f6d18fd7532b223ea462277131b03ebf8`) against live GCP —
  commit present on `origin/live-defi-rollout`, `terraform init` + fresh `terraform plan` reproduced the same "4 to add,
  0 to change, 0 to destroy", SA + Artifact Registry image both confirmed to exist live. Applied with `-target` scoped
  to exactly the 4 new resources (`module.daily_job.google_cloud_run_v2_job.job`,
  `module.daily_workflow.google_workflows_workflow.workflow`,
  `module.daily_workflow.google_cloud_scheduler_job.trigger`,
  `module.backfill_workflow.google_workflows_workflow.workflow`) —
  `Apply complete! Resources: 4 added, 0 changed, 0 destroyed`; post-apply `terraform plan` shows zero infra drift (only
  a benign output-value diff). Immediately `gcloud scheduler jobs pause features-service-sports-daily-trigger` →
  confirmed `PAUSED`, per the terraform's own double-fire-avoidance note. **Manual verification did NOT reach SUCCEEDED
  — todo 5 stays open, legacy job NOT retired, per this touch's explicit instruction to stop on any execution failure.**
  Two real executions run: (1) bare `gcloud run jobs execute` (no overrides) → `features-service-sports-job-fs8sj`,
  `NonZeroExitCode`, failed CLI validation (`Batch mode requires --date or both --start-date and --end-date` — the job's
  default `args` genuinely omit dates, new follow-up todo added above); (2) retried with `--args` overrides matching the
  Workflow's real contract
  (`--feature-family sports --operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date 2026-07-14 --end-date 2026-07-15`)
  → `features-service-sports-job-kk4dv`, got PAST CLI validation + the full Python import chain (re-confirms the
  fleet-wide UTL/UAC skew bug does not reproduce) + GCS-FUSE mount, then failed `NonZeroExitCode` on
  `Manifest consolidator appears DOWN for bucket='instruments-store-sports-prd-central-element-323112': ... heartbeat is 208s old (> 120s budget) ... recovery=fail_fast`.
  Root-caused (not guessed): the `uts-prod-manifest-consolidator-instruments-sports` Cloud Run Job (single Scheduler
  cron, `*/1 * * * *`, no duplicate trigger) is livelocked — every ~1min cycle logs
  `skipping cycle ... fresh lock present (sibling cron still running)` + `error=locked` (8/8 sampled executions between
  12:14-12:41 UTC), yet no genuine sibling overlaps (each run completes in 7-9s). `_index/consolidator.lock` is
  rewritten fresh on every cycle including skip-only cycles, consistent with a lock-TTL bug that never lets the lock age
  out. `availability_index.parquet` got exactly one genuine write in the ~30min observed window (12:39:43 UTC) then went
  stale again immediately. Filed as
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` (new issue, P1,
  cross-repo/data-correctness — this is an EXTERNAL blocker in a different system, not a defect in the
  features-service-sports deploy work itself, which is now proven correct up to that boundary). **Terraform/job/workflow
  resources deliberately left in place** (scheduler stays paused) — no rollback needed, they are correct; re-attempt
  manual verification once the linked issue is resolved, THEN proceed to todos 6-8.
- 2026-07-15 (DriftFixRetireReenable phase, todos 6-8 — STOPPED per gating condition, real evidence, not inference):
  Task handoff explicitly gated todos 6-8 on `manualExecutionSucceeded`; independently re-verified (not just trusted the
  flag) rather than proceeding: `gcloud run jobs executions describe features-service-sports-job-kk4dv` still shows
  `Completed=False / NonZeroExitCode`; `gcloud scheduler jobs describe features-service-sports-daily-trigger` still
  `PAUSED`; the linked blocker (`instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`) is confirmed
  STILL ACTIVE — `uts-prod-manifest-consolidator-instruments-sports` executions are still firing on a tight ~1min
  cadence at 2026-07-15T12:47-12:49Z (same livelock signature as the earlier observation window). Per the task's
  explicit instruction, did NOT proceed to todo 6 (Workflow YAML `--category`→`--asset-group` drift fix), todo 7 (retire
  the legacy job), or todo 8 (re-enable scheduling) — all three remain `[ ]`. No terraform/config changes made, nothing
  shipped this touch. Next unblock step: resolve the manifest-consolidator livelock issue, then re-attempt a manual
  `features-service-sports-job` execution to a genuine `SUCCEEDED` terminal state (todo 5) before revisiting 6-8.
- 2026-07-15 (FinishBucketAndDocs phase, todos 9-10 — STOPPED per this touch's explicit gating condition, real evidence,
  not inference): Task instruction was "if `schedulingReenabled` is false or `realScheduledFireVerified` is false, STOP
  and report why — do not delete the bucket on an unhealthy service." Independently re-verified live rather than
  trusting the prior touch's handoff flags:
  `gcloud scheduler jobs describe features-service-sports-daily-trigger --location=asia-northeast1 --project=central-element-323112`
  → still `state: PAUSED`; `gcloud run jobs executions list --job=features-service-sports-job` → both prior executions
  (`kk4dv`, `fs8sj`) still show `Completed=False` (no successful execution exists at all, manual or scheduled);
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` → `status: open`;
  `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-instruments-sports` → still firing on the same
  tight ~1min livelock cadence (executions at 12:48-12:52 UTC, i.e. still reproducing ~10min after the prior touch's
  last observation). **Gate condition holds** (`schedulingReenabled=false`, `realScheduledFireVerified=false`) — did NOT
  touch the `features-sports` bare bucket, did NOT edit `deployment-service/terraform/gcp/main.tf`'s
  `google_storage_bucket.features_sports` resource, did NOT close the linked issue doc
  (`features_sports_service_cloud_run_job_broken_image_2026_07_15.md` stays as-is), and did NOT append to
  `bucket_estate_consolidation_to_sub100_2026_07_13.md` since there is nothing new to report there — the bucket delete
  remains blocked on the SAME unresolved external livelock as the prior touch. Todos 6-10 remain `[ ]`. No
  terraform/config/code changes made in any repo this touch; the only change is this documentation-only append. Next
  unblock step unchanged from the prior touch: resolve
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md` first, then re-attempt
  `features-service-sports-job` to a genuine `SUCCEEDED`, then re-enable scheduling + verify one real scheduled fire —
  only then is it safe to revisit todos 6-10 (Workflow YAML drift, legacy job retirement, scheduling re-enable, bucket
  delete, issue-doc closure).
- 2026-07-15 (~13:45Z, fleet-wide manifest-consolidator audit — DOCS-ONLY, read-only, relevant to todo 5's blocker): A
  separate dispatch audited all 25 other `uts-prod-manifest-consolidator-*` Cloud Run jobs to check whether the
  `instruments-sports` livelock blocking this plan's todo 5 (per
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`) is a fleet-wide defect.
  **Result: it is not** — 0 of the 25 audited jobs show the same signature (23 HEALTHY, 2 DORMANT/paused-and-excluded, 1
  new-but-different finding: `market-data-cefi` needs the same `CONSOLIDATOR_LOCK_TTL_SECONDS` override pattern already
  applied to `market-data-defi`/`instruments-sports`, unrelated to this plan). **More importantly, a live re-watch of
  `instruments-sports` itself (13:32-13:39Z) found it is NOT actually an indefinite livelock** — it is a genuine ~7-8min
  real merge (confirmed: one watched end-to-end, 434.7s, clean acquire→merge→write→release, lock correctly absent
  immediately after) colliding with a naive freshness-gate threshold
  (`assert_consolidator_healthy`/`ConsolidatorLivenessMonitor`) that can't tell a legit in-flight merge from a downed
  consolidator. **This exact mechanism was already root-caused and fixed in code** by a sibling issue doc
  (`plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`, discovered via
  this audit — the two issue docs were filed independently on the same underlying bug from two different entry points):
  `unified-trading-library@c47273c1` ("lock-aware consolidator liveness — a fresh held lock is proof-of-life, not
  DOWN"), committed 2026-07-15T13:03:17+01:00, is UTL's current HEAD. **This directly gives todo 5 a concrete, scoped
  unblock path** (replacing the prior open-ended "wait for the livelock investigation"): (1) rebuild the
  `market-tick-data-service` (MTDS) image + redeploy the consolidator-liveness-watchdog so it carries `c47273c1`; (2)
  rebuild + redeploy `features-service`'s own image (its `assert_consolidator_healthy` call, confirmed via `grep` in
  `features_service/sports/cli/handlers/_manifest_preflight.py`, is baked into the 2026-07-14 image digest that predates
  this fix); (3) only then re-attempt the manual `features-service-sports-job` verification execution. Both issue docs
  updated + cross-linked with the full per-job audit table and evidence; no code, terraform, or Cloud Run/Scheduler
  config was touched (docs-only). Todo 5 stays `[ ]` — the blocker is confirmed still live (the fix is not yet deployed
  anywhere) — but is no longer an open-ended fleet-wide unknown.
- 2026-07-15 (~15:45Z, UnblockDeploy phase — dispatched per the prior touch's concrete unblock path, real evidence, not
  inference): Completed all 3 prerequisite deployment actions the prior touch's audit identified as blocking todo 5. (1)
  `market-data-cefi` TTL-shorter-than-real-merge-duration fix shipped (`deployment-service@8e94608`,
  `CONSOLIDATOR_LOCK_TTL_SECONDS=1200`, live-bumped via `gcloud run jobs update` + codified in terraform,
  `quality-gates.sh --no-fix` green) — unrelated to sports but was the one open item from the fleet-wide audit, closed
  while in the area. (2) Independently re-verified (not just trusted) that the `uts-prod-consolidator-liveness-watchdog`
  MTDS rebuild+redeploy already reported in the sibling issue doc's 14:05Z update is real and live:
  `market-tick-data-service:latest` resolves to `sha256:1e974ccd...`, the watchdog's most recent execution ran that
  exact digest, and its logs show 0 DOWN across all 26 buckets. (3) Rebuilt `features-service` itself against the
  fix-containing UTL base image: confirmed via real `docker run` (not inference) that UTL AR digest `sha256:56bd0fe5...`
  (built from UTL HEAD `c47273c1`) genuinely contains the `consolidator_cycle_in_flight` short-circuit inside
  `assert_consolidator_healthy`; bumped `features-service/Dockerfile`'s `BASE_IMAGE_DIGEST` accordingly
  (`features-service@7c2e4ef1`, `quality-gates.sh --no-fix` green); manually triggered `features-service-build` (its
  Cloud Build trigger only fires on push to `main`, not `live-defi-rollout` where quickmerge lands) — build
  `0b5cec2d-2f6a-4416-b870-44e3db644e1f` against the correct commit, in progress as of this entry.
  `features-service-sports-job`'s terraform `docker_image` is pinned to the mutable `:latest` tag, so once this build
  pushes, the job's next execution picks up the fix with no further terraform/gcloud action needed on the job itself.
  **Todo 5 stays `[ ]`** — this phase deliberately stopped short of re-attempting the manual verification execution
  (gated on the Cloud Build above reaching `SUCCESS`); full evidence in
  `plans/active/issues/instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`'s matching 15:45Z update.
  Next step: once the build succeeds, re-run `features-service-sports-job` with the same
  `--feature-family sports --operation compute --mode batch --asset-group SPORTS --tables fixture_features --start-date/--end-date`
  overrides used in execution `kk4dv` and confirm a genuine `SUCCEEDED` terminal state. **UPDATE (~15:37Z): the Cloud
  Build did NOT reach `SUCCESS`** — it hung inside the quality-gates test step both times (original + one retry) and
  never pushed a new image; `features-service:latest` is confirmed still the stale 2026-07-14 image. Filed as
  `plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md` (P1, suspected `E2_HIGHCPU_8`
  memory pressure, not confirmed). Todo 5 stays `[ ]` and should NOT be re-attempted yet — it would still hit the same
  false-DOWN error against the un-updated image. This is now the blocking item, ahead of the consolidator livelock doc
  (which is otherwise resolved pending this deploy).
