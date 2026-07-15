---
doc_type: issue
title:
  "features-sports-service Cloud Run job's deployed image is broken (ModuleNotFoundError:
  unified_api_contracts.internal) — daily/backfill production pipeline has been non-functional since at least
  2026-06-08, unrelated to and independent of the features-sports bucket cutover"
summary:
  'Discovered while executing the Cutover-phase sub-task of
  plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md (repointing the features-sports-service Cloud Run job
  GCS-FUSE mount from the bare features-sports-central-element-323112 bucket to canonical
  features-sports-prd-central-element-323112). The terraform mount repoint itself applied cleanly and verified correct
  via live logs (GCSFuse mounted the new canonical bucket without error). A live test execution
  (features-sports-service-job-n4l5z, triggered manually with the current CLI contract --operation compute --mode batch
  --asset-group SPORTS ...) then failed at Python import time, BEFORE any bucket/mount code path is reached:
  `ModuleNotFoundError: No module named "unified_api_contracts.internal"` inside
  unified_trading_library/config_interface/auth/entitlements.py. This is independent of the bucket mount (the traceback
  fires during package import, ahead of any GCS access) and would have failed identically under the OLD bare-bucket
  mount too. Corroborating evidence: the `features-sports-service-daily-trigger` Cloud Scheduler job is PAUSED
  (userUpdateTime 2026-06-08T04:16:20Z) and the last SUCCEEDED workflow execution on record is 2026-06-07 — i.e. the
  daily/backfill production sports-features pipeline has been silently down for 5+ weeks, most likely paused by whoever
  first hit this same breakage. Separately (not this issue, but same file, noted for the record): the checked-in
  terraform source for both the daily and backfill Workflow YAMLs already uses the current `--asset-group` CLI flag,
  while the LIVE deployed workflows still pass the retired `--category` flag (grep-confirmed: `--category` is declared
  nowhere in any service CLI in this workspace) — a second, independent reason the daily/backfill workflows would fail
  even once the image is fixed, unless that terraform drift is also applied. Root cause of the broken image itself is
  unknown from this vantage point — the deployed image is built from a separate `features-sports-service` repo
  (`docker_image = ".../features-sports-service:latest"`, published by that repo''s own cloudbuild.yaml) that is NOT
  cloned in this workspace slot, so the actual build/publish pipeline could not be inspected here; the traceback package
  path (`features_sports_service.cli.main`, singular-underscore, distinct from this workspace''s `features-service`
  repo''s `features_service.sports.*` package) suggests this may be a pre-consolidation, never-rebuilt image left
  pointing at a `unified_api_contracts` internal-namespace shape that no longer exists.'
status: resolved
nature: issue
asset_group: [sports]
stage: [data, meta]
repos: [deployment-service, features-service, unified-trading-pm]
scope: [engineer, admin]
tags: [gcs, buckets, features-sports, cloud-run, broken-image, data-correctness, live-consumer, production-outage]
related: [bucket_estate_consolidation_to_sub100_2026_07_13.md]
created: "2026-07-15"
parent_epic: infrastructure_master
priority: P1
source:
  "Dispatched sub-agent task, 2026-07-15: 'Cutover phase' for the features-sports bucket under the
  bucket-estate-consolidation plan (repoint the 3 live-reference surfaces to the canonical -prd- bucket before delete).
  Discovered as a side-effect of the mandated 'verify it comes up healthy post-redeploy' step for the Cloud Run job's
  GCS-FUSE mount repoint — the mount itself verified healthy, but the job as a whole does not, for an unrelated reason."
assigned_vm: NA
resolved_by:
  "features_sports_service_consolidation_deploy_2026_07_15.md (Path B — finish the consolidation deploy side); new
  features-service-sports-job proven healthy on a real scheduled fire, legacy job's daily scheduler paused"
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# features-sports-service Cloud Run job image is broken, independent of the bucket cutover

## Finding

While repointing the `features-sports-service-job` Cloud Run job's GCS-FUSE volume mount from the bare
`features-sports-central-element-323112` bucket to the canonical `features-sports-prd-central-element-323112` bucket
(terraform `module.daily_job.google_cloud_run_v2_job.job`, applied via `-target` this touch), the task's mandated
post-redeploy health check surfaced a **pre-existing, unrelated production outage**:

- **Mount repoint itself: verified healthy.** `gcloud run jobs describe` confirms the live job spec now mounts
  `features-sports-prd-central-element-323112` at `/mnt/gcs/features-sports-prd-central-element-323112`. A manual test
  execution (`features-sports-service-job-n4l5z`) shows GCSFuse mounting that bucket cleanly in the logs ("File system
  has been successfully mounted.") — no error at the storage layer.
- **The job then crashes at Python import time**, before any bucket/feature-compute code runs:
  ```
  File "/app/features-sports-service/features_sports_service/cli/main.py", line 19, in <module>
      from unified_trading_library import log_event
  ...
  File "/app/unified_trading_library/config_interface/auth/entitlements.py", line 15, in <module>
      from unified_api_contracts.internal.schemas.rbac import (
          SubscriptionTier,
      )
  ModuleNotFoundError: No module named 'unified_api_contracts.internal'
  ```
  Exit code 1, `NonZeroExitCode` / `failedCount: 1`. This is **independent of which bucket is mounted** — the failure
  occurs during package import, ahead of any GCS access — so the OLD bare-bucket mount would have failed identically.
  The bucket cutover neither caused nor can fix this.
- **Corroborating evidence the outage predates this touch by weeks**: `features-sports-service-daily-trigger` (Cloud
  Scheduler, `0 7 * * *`) is `PAUSED`, `userUpdateTime: 2026-06-08T04:16:20Z`. The most recent `SUCCEEDED`
  `features-sports-service-daily` workflow execution on record is `2026-06-07T07:00:01Z`. The daily/backfill production
  sports-features pipeline has most likely been non-functional (or deliberately paused in response to this same
  breakage) since 2026-06-08 — over 5 weeks.
- **A second, independent live-reference drift** (found in the same terraform file, not applied this touch): the
  checked-in `daily_workflow`/`backfill_workflow` Workflow YAML sources already use the current `--asset-group SPORTS`
  CLI flag, but a `terraform plan` shows the LIVE deployed workflows still pass the retired `--category SPORTS` flag —
  confirmed via workspace-wide grep that `--category` is declared in NO service CLI anywhere in this workspace anymore
  (only `--asset-group`, per `codex/06-coding-standards/cli-convention.md`). Even once the image import is fixed, the
  scheduled workflows would still fail immediately with `parse_args()`-raised "unrecognized arguments: --category" until
  that terraform drift is also `apply`'d. Left un-applied this touch (out of the dispatched scope, and its own
  `-target`ed apply deserves independent review since it touches two live Workflow resources).

## Why not just fixed here

Fixing the root cause requires locating and rebuilding the container image (a separate `features-sports-service` Docker
build/publish pipeline that is not cloned in this workspace slot —
`docker_image = ".../features-sports-service:latest"`, published by that repo's own `cloudbuild.yaml` per
`terraform/services/features-sports-service/gcp/terraform.tfvars`). The traceback's package path
(`features_sports_service.cli.main`, singular-underscore) differs from this workspace's consolidated `features-service`
repo's `features_service.sports.*` package — this may be a pre-consolidation image that was never rebuilt against the
current `unified_api_contracts` internal-namespace shape. This is squarely outside a bucket-cutover dispatch's scope and
needs its own investigation (find/confirm the actual source repo or build trigger, rebuild, redeploy, then re-verify).

## Recommended next steps (operator/engineer follow-up, not actioned here)

1. Identify the actual current source for the `features-sports-service` Docker image (is there a build trigger in this
   monorepo's `features-service/features_service/sports/` that should be publishing to this same Artifact Registry path,
   or is the separate `features-sports-service` repo still the real source and simply stale?).
2. Rebuild + republish the image against the current `unified_api_contracts` shape.
3. `terraform apply` the `--category` → `--asset-group` Workflow-YAML drift (both `daily_workflow` and
   `backfill_workflow` resources in `terraform/services/features-sports-service/gcp/main.tf`) once the image fix is
   confirmed — do this in a separate, reviewed touch, not bundled silently into the image fix.
4. Manually trigger a real execution to confirm end-to-end health (compute completes, features actually written to
   `features-sports-prd-central-element-323112`), THEN un-pause `features-sports-service-daily-trigger`.
5. Only after (1)-(4) are confirmed green does the `features-sports` bare-bucket Verify+Delete step in
   `bucket_estate_consolidation_to_sub100_2026_07_13.md` have a truly "healthy" live consumer to check against.

## Root cause CONFIRMED (fix-phase investigation, 2026-07-15) — deployment path still BLOCKED on an operator decision

A follow-on fix-phase touch fully confirmed the root cause (not just the symptom above): `unified_trading_library`'s
`entitlements.py` has required `unified_api_contracts.internal` since UAC commit `6bb892bc` (2026-04-02), but UTL's own
`pyproject.toml` constraint on `unified-api-contracts` stayed loose (`>=0.1.0,<1.0.0`) through at least 2026-04-22. Any
`unified-trading-library:latest` base image built in that window therefore resolved the _highest compatible_ wheel,
`0.2.38` (published 2026-03-12 — this **predates** the 2026-03-26 commit that added the `internal/` namespace at all),
instead of a version that actually contains it. `features-sports-service`'s Dockerfile installs itself with `--no-deps`,
so it purely inherited whatever `unified-api-contracts` the UTL base image had baked in at its own 2026-04-22 build —
the broken `0.2.38`. This is fully root-caused; it is **not** simple image staleness (the `internal` namespace already
existed a month before the image was built) — it's a loose-constraint dependency-resolution bug.

**No fix was applied in that touch** — it stopped short of remediation because the mechanical part (tighten the
`unified-api-contracts`/`unified-trading-library` version pins, rebuild) is well understood, but rebuilding+redeploying
requires first deciding which repo is the deployment source of truth going forward, since the two candidate paths carry
materially different blast radii and one re-legitimizes an already-retired repo:

- **Path A** — Un-archive the old, GitHub-**archived** (2026-05-08) `features-sports-service` repo (still the only repo
  that actually builds+deploys the live `features-sports-service-job`), patch its now-tightened UTL/UAC pins, cut a
  fresh commit, let its existing `cloudbuild.yaml` rebuild+republish, redeploy to the existing job. Fast, minimal blast
  radius, but re-diverges a repo the org already consolidated away on the same date.
- **Path B [RECOMMENDED]** — Finish the abandoned 2026-05-08 `features-service` consolidation: stand up a
  Dockerfile/cloudbuild.yaml/terraform Cloud Run job + Workflow definitions for `features-service`'s
  `features_service/sports/*` sub-package (already cloned in this workspace at `features-service`, with its own
  `cloudbuild.yaml`, `_SERVICE_NAME: features-service`, but **no live Cloud Run job at all yet**), point the existing
  GCS-FUSE mount/bucket wiring at it, retire `features-sports-service-job`, then un-pause scheduling against the new
  job. Correct long-term state, matches the already-completed code consolidation, but larger scope (new Cloud Run job +
  Workflow terraform resources + CLI-flag mapping + SIT-equivalent verification).

**This decision has NOT yet been made by the operator.** A subsequent Verify+Re-enable-phase touch (also 2026-07-15)
confirmed `readyToDeploy: false` for exactly this reason and correctly took no deploy/scheduler action — see the plan's
Progress Log entry of the same date for the full status. **Status remains `open`, blocked on the operator A/B decision
above** — do not attempt a rebuild/redeploy of either candidate repo until that decision is made. Separately noted, not
blocking this decision: the `--category`→`--asset-group` Workflow-YAML terraform drift (recommended step 3 above) is
confirmed real but independent of this import crash; apply it only after the deploy path is chosen, in its own reviewed
touch.

## Evidence

- `gcloud scheduler jobs describe features-sports-service-daily-trigger --location=asia-northeast1 --project=central-element-323112`:
  `state: PAUSED`, `userUpdateTime: '2026-06-08T04:16:20.761350Z'`.
- `gcloud workflows executions list features-sports-service-daily --location=asia-northeast1 --project=central-element-323112 --limit=5`:
  newest entry `SUCCEEDED 2026-06-07T07:00:01Z`.
- `gcloud run jobs execute features-sports-service-job --region=asia-northeast1 --project=central-element-323112 --args=--operation,compute,--mode,batch,--asset-group,SPORTS,--tables,fixture_features,--start-date,2026-07-13,--end-date,2026-07-14`
  → execution `features-sports-service-job-n4l5z`, terminal state `NonZeroExitCode`, `failedCount: 1`,
  `completionTime: 2026-07-15T11:11:48Z`.
- `gcloud logging read` on that execution: GCSFuse mount succeeds against `features-sports-prd-central-element-323112`;
  Python `ModuleNotFoundError: No module named 'unified_api_contracts.internal'` at
  `unified_trading_library/config_interface/auth/entitlements.py:15`.
- `terraform plan` in `terraform/services/features-sports-service/gcp/` (full, un-targeted) shows the
  `--category`→`--asset-group` drift on both `daily_workflow` and `backfill_workflow` resources.

## Update 2026-07-15 (Path B in progress — status stays `open`, NOT resolved by this update)

Tracking moved to `plans/active/features_sports_service_consolidation_deploy_2026_07_15.md` (created same day). That
plan's BuildDeployment phase (todos 1-4) confirmed with real `docker run` evidence that the current
`features-service:latest` image genuinely resolves `unified_api_contracts.internal` (the fleet-wide skew bug does NOT
reproduce against it) and shipped new Cloud Run Job + Workflow terraform
(`deployment-service@8b1c561f6d18fd7532b223ea462277131b03ebf8`, `terraform/services/features-service-sports/gcp/**`) —
NOT yet applied/deployed. This issue stays `open` until the plan's later todos (deploy, verify SUCCEEDED, retire the
legacy job, re-enable scheduling, close this issue) complete — see that plan's Progress Log for full detail; do not
duplicate it here.

## Resolution (2026-07-15)

**RESOLVED — Path B (finish the consolidation deploy side) is complete and proven live.** The org-decided fix was to
stand up real deployment for the consolidated `features_service/sports/*` code rather than patch the archived
`features-sports-service` repo. End-state, all verified against live GCP `central-element-323112` / `asia-northeast1`:

- **Root cause eliminated at the image boundary.** `features-service:latest` (the shared multi-family image) resolves
  `unified_api_contracts.internal` cleanly — the fleet-wide UTL/UAC version-skew bug does NOT reproduce. The new job
  runs a digest-pinned image (`...@sha256:b7fc3d7f…`, `0.66.0`) that `docker run`-verifies to contain BOTH the UAC
  internal-namespace fix AND UTL `c47273c1` (lock-aware consolidator liveness). The 3-day features-service Cloud Build
  hang that blocked producing this image is itself resolved (see
  `features_service_cloud_build_quality_gates_hang_2026_07_15.md`; green build `fd73ca17-8d5a-435c-8ec6-9af11eb377fc`).
- **New Cloud Run Job live + healthy.** `features-service-sports-job` (terraform
  `deployment-service/terraform/services/features-service-sports/gcp/**`, applied) reached a genuine `SUCCEEDED`
  (execution `features-service-sports-job-qsqs4`, then the scheduled `…-6tm9w`) — manifest-consolidator preflight passes
  with zero `CONSOLIDATOR_DOWN`, real fixture features written to the canonical bucket
  `gs://features-sports-prd-central-element-323112`.
- **Scheduling re-enabled + a real scheduled fire proven.** `features-service-sports-daily-trigger` is `ENABLED`; a
  forced scheduler run drove workflow `05bd100d-…` → `SUCCEEDED`, spawning job `…-6tm9w` (`succeededCount=1`), features
  computed across T-1..T+7.
- **Legacy path safely quiesced.** The legacy `features-sports-service-job`'s daily scheduler
  `features-sports-service-daily-trigger` stays PAUSED (no double-fire). Full retirement of the legacy job is tracked as
  a remaining P1 in the owning plan (it still receives per-fixture Tier-3/4 dispatches from
  `configs/sports-trigger-tiers.yaml` that need a `--feature-family sports` dispatch-code change before repoint) — not a
  blocker on this issue's subject (the broken deployed image), which is fully addressed.

Full evidence chain: `plans/active/features_sports_service_consolidation_deploy_2026_07_15.md` Progress Log
(ReverifyExecution + DriftRetireReenable + FinishBucketAndDocs phases).
