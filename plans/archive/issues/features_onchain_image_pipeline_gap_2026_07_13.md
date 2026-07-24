---
doc_type: issue
title:
  "features-onchain-service image pipeline gap: repo archived 2026-05-08 (consolidated into features-service) but two
  Cloud Run jobs still referenced the dead image name — prod lst-seasonal-rewards cron failed EVERY day since
  2026-06-19; fixed by repointing job+terraform at features-service:latest; orphan job decommission proposed"
summary:
  "Deployment-sync leg, 2026-07-13. Investigation: features-onchain-service has no build pipeline because the REPO was
  deliberately retired — consolidated into features-service (onchain family) and archived on GitHub 2026-05-08 (see
  plans/archive/issues/features_repo_consolidation_preaudit_2026_05_08.md); features-service-build is the live trigger
  and unified-trading-system/features-service:latest is fresh (built 2026-07-13). The expected image path
  unified-trading-system/features-onchain-service:latest NEVER existed (AR path empty — the archived repo's cloudbuild
  targeting it never ran via trigger); the only image is the pre-consolidation legacy AR repo
  features-onchain-service/features-onchain-service:latest (sha256:d7874899, 2026-02-10, source 2ec6391). Job 1
  uts-prod-features-onchain-collect-lst-seasonal-rewards (terraform lst_seasonal_rewards_scheduler.tf, cron ENABLED 25 2
  * * *) failed execution-creation with INVALID_ARGUMENT every day since creation 2026-06-19 — zero executions ever.
  FIXED: terraform repointed to features-service:latest + consolidated script path (deployment-service@5c114aa via
  quickmerge), live job updated to match, verification execution
  uts-prod-features-onchain-collect-lst-seasonal-rewards-t9zl9 EXECUTION_SUCCEEDED in 40.68s (exit 0). Job 2
  features-onchain-service-job (created 2026-01-27, one run, NO scheduler targets it, legacy image) is a dead orphan —
  decommission proposed (operator decision packet). Adjacent: uts-dev/uts-staging features-onchain T1-recon schedulers
  are ENABLED but target NONEXISTENT Cloud Run jobs (uts-{dev,staging}-features-onchain-service-t1-recon not found) —
  failing daily."
status: resolved
nature: notes
asset_group: [defi]
stage: [features]
repos: [features-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    features-onchain,
    cloud-run-jobs,
    cloud-build,
    artifact-registry,
    lst-seasonal-rewards,
    repo-consolidation,
    deployment-sync,
    decommission,
  ]
related:
  [
    ../../archive/issues/features_repo_consolidation_preaudit_2026_05_08.md,
    /codex/15-runbooks/lst-seasonal-rewards-smoke.md,
    /codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P2
source:
  "Operator deployment-sync sweep 2026-07-13, leg features-onchain-pipeline: newest AR image Feb-10 (sha256:d7874899,
  source 2ec6391, 260 commits behind main); jobs uts-prod-features-onchain-collect-lst-seasonal-rewards +
  features-onchain-service-job reference :latest. Leg instruction: investigate deliberate-removal vs gap, rebuild or
  decommission."
assigned_vm: NA
resolved_by:
  "2026-07-13: prod job fix shipped (deployment-service@5c114aa, verification execution t9zl9 + scheduler-path h7vbq
  SUCCEEDED) + full decommission executed per explicit operator ruling (job/schedulers/workflow/AR repo all deleted,
  each verified NOT_FOUND — see Decommission checklist). Residual adjacent findings 2-4 remain listed as candidates for
  a deployment-service governance sweep."
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# features-onchain-service image pipeline gap — investigation + fix + decommission proposals

## Why there is no build pipeline (deliberate, but with an unmigrated tail)

- The standalone `features-onchain-service` repo was **consolidated into `features-service`** (subtree-merged as the
  `features_service.onchain` family) and **archived on GitHub 2026-05-08** (`gh repo view` → `isArchived: true`, last
  push 2026-05-08). Pre-audit: `plans/archive/issues/features_repo_consolidation_preaudit_2026_05_08.md`.
- Its Cloud Build trigger does not exist in `gcloud builds triggers list` (asia-northeast1) — `features-service-build`
  is the live trigger for the consolidated repo. Trigger removal was part of the deliberate repo retirement.
- The archived repo's final `cloudbuild.yaml` (substitutions `_SERVICE_NAME=features-onchain-service`,
  `_REGISTRY_REPO=unified-trading-system`) targeted `unified-trading-system/features-onchain-service` — but that AR path
  is **EMPTY** (verified: `gcloud artifacts docker images list` returns zero rows). No image was ever published there.
  The only images live in the legacy per-service AR repo `features-onchain-service/features-onchain-service` (newest
  `sha256:d7874899…`, tags `2ec6391,latest`, 2026-02-10).
- The consolidated `features-service` pipeline is HEALTHY: `unified-trading-system/features-service:latest` =
  `0.66.0`/`08fd0d8` built 2026-07-13T14:44Z. Fleet promotion: `features-service` `main...live-defi-rollout` compare →
  `files: 0` (content-identical).

**Verdict: the trigger removal was deliberate (repo retirement), but the Cloud Run job surfaces that referenced the
`features-onchain-service` image name were never migrated — that is the gap.**

## Job 1 (LIVE, was broken): uts-prod-features-onchain-collect-lst-seasonal-rewards — FIXED

- Terraform-managed: `deployment-service/terraform/gcp/lst_seasonal_rewards_scheduler.tf` (Phase 6
  leveraged-leg-controller, restaking-reward realisation). Job created 2026-06-19 by terraform apply.
- Cron `uts-prod-features-onchain-collect-lst-seasonal-rewards-cron` **ENABLED**, `25 2 * * *` UTC. Scheduler
  `status.code: 3` (INVALID_ARGUMENT) — last attempt 2026-07-13T02:25Z. **Zero executions ever created** (image
  `unified-trading-system/features-onchain-service:latest` did not exist → execution-creation failed daily since
  2026-06-19). The Phase 6 pipeline has therefore NEVER produced `lst_seasonal_rewards` data; strategy-service degrades
  gracefully (`ParquetDustLoader` returns `None` — see the smoke runbook's rollback section).
- **Fix shipped (2026-07-13)** — first-principles: repoint at the continuously-built consolidated image rather than
  resurrecting a duplicate image name that would rot again (no trigger would rebuild `features-onchain-service:latest`;
  `features-service:latest` is rebuilt on every merge and Cloud Run jobs resolve `:latest` at execution-creation time,
  so the job now self-updates):
  - Terraform: image → `…/unified-trading-system/features-service:latest`; args →
    `python scripts/onchain/collect_lst_seasonal_rewards_daily.py …` (consolidated layout; invoked by FILE PATH because
    the editable-installed `unified-api-contracts` sibling also exposes a top-level `scripts` package which shadows
    `python -m scripts.…` — verified locally: `-m` form → `ModuleNotFoundError`, file-path form → argparse help OK).
    Shipped `deployment-service@5c114aa` (quickmerge, QG green 95s).
  - Live job updated to match via `gcloud run jobs update` (spec verified — same image/command/args as terraform, so the
    next `terraform apply` is a content no-op).
  - **Verification execution**: `uts-prod-features-onchain-collect-lst-seasonal-rewards-t9zl9` →
    `Execution completed successfully in 40.68s`, container exit(0), `succeededCount: 1` (2026-07-13T22:42Z).
  - Run outcome detail: see Progress Log below (event counts / chains wired from execution logs).
- Remaining operational caveat: the smoke runbook (`/codex/15-runbooks/lst-seasonal-rewards-smoke.md`,
  `last_executed: never`) requires 9 Secret Manager keys (ALCHEMY/HELIUS/…SCAN); presence could not be verified from
  this session (secretmanager PERMISSION_DENIED for `unified-trading-sa`). If per-chain scanners fail on missing keys
  the job exits 0 with 0 events (D10 shard isolation) — silent under-collection. Operator should run the runbook's
  pre-flight checklist once.

## Job 2 (DEAD): features-onchain-service-job — DECOMMISSION PROPOSED

- Created 2026-01-27T19:28Z, ran exactly once (same minute, EXECUTION_SUCCEEDED, execution deleted 2026-02-08).
- **No Cloud Scheduler cron targets it.** The only adjacent scheduler, `features-onchain-service-daily-trigger`
  (Workflows), is **PAUSED**.
- References the legacy AR path `features-onchain-service/features-onchain-service:latest` (frozen 2026-02-10 image,
  source 260 commits behind the archived repo's final main — i.e., pre-consolidation code).
- **Recommendation: decommission** — delete the Cloud Run job, the PAUSED `features-onchain-service-daily-trigger`
  scheduler + its `features-onchain-service-daily` workflow, and (optionally) the legacy AR repo
  `features-onchain-service/…` after a retention grace. Not executed autonomously — infra deletion is an operator ruling
  (decision packet returned by the leg).

## Adjacent findings (report-only)

1. **uts-dev/uts-staging features-onchain T1-recon schedulers fire at nonexistent jobs**: schedulers
   `uts-dev-features-onchain-t1-schedule` + `uts-staging-features-onchain-t1-schedule` are **ENABLED** (30 2 \* \* \*)
   but their targets `uts-{dev,staging}-features-onchain-service-t1-recon` do not exist (`gcloud run jobs describe` →
   Cannot find job); `uts-prod-features-onchain-t1-schedule` is PAUSED and its prod job is also absent. Either the T1
   recon jobs should be provisioned from `t1_batch_scheduler.tf` against the features-service image, or the dev/staging
   schedulers paused/deleted. **RESOLVED 2026-07-13: operator ruled deletion — both broken schedulers deleted + verified
   NOT_FOUND (see Decommission checklist below).** The PAUSED `uts-prod-features-onchain-t1-schedule` was NOT in the
   ruling and remains.
2. **Stale docstring**: `features-service/scripts/onchain/collect_lst_seasonal_rewards_daily.py` usage block still says
   `python -m scripts.collect_lst_seasonal_rewards_daily` (pre-consolidation path; also the `-m` form is broken per the
   shadowing note above).
3. **Stale runbook module paths**: `/codex/15-runbooks/lst-seasonal-rewards-smoke.md` references
   `features_onchain_service.collectors.…` — the consolidated home is `features_service.onchain.collectors.…`.
4. **Stale per-service terraform**: `deployment-service/terraform/services/features-onchain-service/` +
   `scripts/setup-cloud-build-triggers.sh` still enumerate the retired standalone repos
   (features-delta-one/-volatility/-onchain/-calendar-service etc.) — candidates for deletion in a deployment-service
   governance sweep.

## Progress Log

- 2026-07-13 22:42Z — terraform fix `deployment-service@5c114aa`; live job updated; verification execution `t9zl9`
  SUCCEEDED (40.68s, exit 0). GCS `gs://features-onchain-central-element-323112/seasonal_rewards/` not yet present —
  consistent with 0 events for 2026-07-12 (write is skipped on empty event list per script `_write_events`).
- 2026-07-13 22:47Z — **scheduler-path verification**: forced `gcloud scheduler jobs run …-cron` → execution `h7vbq`
  SUCCEEDED (completed 22:47:32Z) and the scheduler's standing error status CLEARED (`status.code: 3` → `{}`). The exact
  cron→`:run`→execution-creation path that failed daily since 2026-06-19 is healed end-to-end. Fresh-image provenance:
  `unified-trading-system/features-service:latest` = `0.66.0`/`08fd0d8`, Evidence:
  cloudbuild=5e720778-fad2-4c60-a4b3-cd930b9b49ce (SUCCESS, 2026-07-13T14:35Z, trigger-built — no manual rebuild
  needed).
- Why no app-log lines are visible for either execution: the project `_Default` logging sink carries exclusion
  `severity <= "DEBUG"` (`debug-filter`) which drops unstructured container stdout/stderr (ingested at severity
  DEFAULT=0 < DEBUG=100) — only the `varlog/system` "Container called exit(0)." (INFO) survives. Event-count
  observability for this job therefore requires structured logging or an exclusion carve-out; per-shard failures still
  surface via `ADAPTER_FETCH_FAILED` events / availability index per the runbook.

## Operator ruling 2026-07-13 (explicit, interactive Q&A): DELETE EVERYTHING NOW — pre-delete state capture

Ruling: decommission immediately (no grace) — Cloud Run job `features-onchain-service-job`, PAUSED scheduler
`features-onchain-service-daily-trigger` + its workflow `features-onchain-service-daily`, broken schedulers
`uts-{dev,staging}-features-onchain-t1-schedule` (targets nonexistent jobs), and the legacy AR repo
`features-onchain-service/*`. DO NOT touch `uts-prod-features-onchain-collect-lst-seasonal-rewards` (live, just fixed)
or anything in `features-service`. Full pre-delete state captured below (all `gcloud … describe` 2026-07-13, project
`central-element-323112`, asia-northeast1) so every surface is re-creatable.

### 1. Cloud Run job `features-onchain-service-job` (full spec)

```yaml
apiVersion: run.googleapis.com/v1
kind: Job
metadata:
  annotations:
    run.googleapis.com/creator: ikenna@odum-research.com
    run.googleapis.com/lastModifier: ikenna@odum-research.com
  creationTimestamp: "2026-01-27T19:28:56.909429Z"
  labels:
    app: features-onchain-service
    cloud.googleapis.com/location: asia-northeast1
    environment: prod
    goog-terraform-provisioned: "true"
    managed-by: terraform
    service: features-onchain-service
    version: v2
  name: features-onchain-service-job
  namespace: "1060025368044"
  uid: a634d534-353c-458a-a1f3-7e471d983f27
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
    spec:
      parallelism: 1
      taskCount: 1
      template:
        spec:
          containers:
            - env:
                - { name: GCP_PROJECT_ID, value: central-element-323112 }
                - { name: GCS_REGION, value: asia-northeast1 }
                - { name: UCS_SKIP_GCSFUSE_CHECK, value: "1" }
                - { name: GCS_LOCATION, value: asia-northeast1 }
                - name: GRAPH_API_KEY
                  valueFrom: { secretKeyRef: { key: latest, name: graph-api-key } }
                - { name: PYTHONUNBUFFERED, value: "1" }
                - name: ALCHEMY_API_KEY
                  valueFrom: { secretKeyRef: { key: latest, name: alchemy-api-key } }
                - { name: ENVIRONMENT, value: prod }
              image: asia-northeast1-docker.pkg.dev/central-element-323112/features-onchain-service/features-onchain-service:latest
              resources: { limits: { cpu: "2", memory: 4Gi } }
          maxRetries: 3
          serviceAccountName: features-onchain-sa@central-element-323112.iam.gserviceaccount.com
          timeoutSeconds: "86400"
# status at capture: executionCount: 4; latestCreatedExecution features-onchain-service-job-xssn7
#   EXECUTION_SUCCEEDED 2026-01-27T19:30:12Z (execution deleted 2026-02-08)
```

### 2. Scheduler `features-onchain-service-daily-trigger` (PAUSED; full spec)

```yaml
attemptDeadline: 180s
description: Triggers features-onchain-service-daily workflow
httpTarget:
  body: eyJhcmd1bWVudCI6IntcInRyaWdnZXJcIjpcInNjaGVkdWxlZFwifSJ9 # {"argument":"{\"trigger\":\"scheduled\"}"}
  headers: { Content-Type: application/octet-stream, User-Agent: Google-Cloud-Scheduler }
  httpMethod: POST
  oauthToken:
    scope: https://www.googleapis.com/auth/cloud-platform
    serviceAccountEmail: features-onchain-sa@central-element-323112.iam.gserviceaccount.com
  uri: https://workflowexecutions.googleapis.com/v1/projects/central-element-323112/locations/asia-northeast1/workflows/features-onchain-service-daily/executions
name: projects/central-element-323112/locations/asia-northeast1/jobs/features-onchain-service-daily-trigger
retryConfig: { maxBackoffDuration: 300s, maxDoublings: 5, maxRetryDuration: 0s, minBackoffDuration: 5s, retryCount: 3 }
schedule: 30 11 * * *
state: PAUSED
timeZone: UTC
userUpdateTime: "2026-06-08T04:13:33.512569Z"
```

### 3. Workflow `features-onchain-service-daily`

`workflows.workflows.get` is DENIED for every identity available to this session (`unified-trading-sa` direct + ADC;
impersonation of github-actions-deploy/github-deploy/features-onchain-sa denied — no serviceAccountTokenCreator), so the
live spec could not be read via API. The workflow is terraform-provisioned and its FULL source is git-tracked:
`deployment-service/terraform/services/features-onchain-service/gcp/main.tf` (`locals.workflow_yaml`, module
`daily_workflow`, name from `terraform.tfvars` `workflow_name = "features-onchain-service-daily"`) — fully re-creatable
from source. Sibling `features-onchain-service-backfill` (module `backfill_workflow`) is NOT in the ruling and is left
untouched.

### 4. Broken T1-recon schedulers (ENABLED, targets nonexistent jobs; full specs)

```yaml
# uts-dev-features-onchain-t1-schedule
attemptDeadline: 180s
description: features-onchain-service T+1 recon batch — writes to t1-recon/features/onchain/
httpTarget:
  headers: { User-Agent: Google-Cloud-Scheduler }
  httpMethod: POST
  oauthToken:
    scope: https://www.googleapis.com/auth/cloud-platform
    serviceAccountEmail: uts-dev-batch-sa@central-element-323112.iam.gserviceaccount.com
  uri: https://asia-northeast1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/central-element-323112/jobs/uts-dev-features-onchain-service-t1-recon:run
name: projects/central-element-323112/locations/asia-northeast1/jobs/uts-dev-features-onchain-t1-schedule
retryConfig: { maxBackoffDuration: 3600s, maxDoublings: 5, maxRetryDuration: 0s, minBackoffDuration: 5s, retryCount: 1 }
schedule: 30 2 * * *
state: ENABLED # status.code: 5 NOT_FOUND daily; lastAttemptTime 2026-07-13T02:30:19Z
timeZone: UTC
userUpdateTime: "2026-03-12T17:52:54.003335Z"
---
# uts-staging-features-onchain-t1-schedule — IDENTICAL shape except:
#   serviceAccountEmail: uts-staging-batch-sa@central-element-323112.iam.gserviceaccount.com
#   uri target job: uts-staging-features-onchain-service-t1-recon
#   userUpdateTime: "2026-03-12T17:59:20.584838Z"; lastAttemptTime 2026-07-13T02:30:20Z; status.code: 5
```

### 5. Legacy AR repo `features-onchain-service` (14444.221 MB, 32 image digests)

```yaml
name: projects/central-element-323112/locations/asia-northeast1/repositories/features-onchain-service
format: DOCKER
mode: STANDARD_REPOSITORY
description: Docker repository for features-onchain-service
createTime: "2026-01-27T18:48:43.183623Z"
updateTime: "2026-02-10T17:32:50.494355Z"
labels:
  {
    environment: prod,
    goog-terraform-provisioned: "true",
    managed-by: terraform,
    project: unified-trading,
    service: features-onchain-service,
  }
registryUri: asia-northeast1-docker.pkg.dev/central-element-323112/features-onchain-service
```

All images under package `features-onchain-service/features-onchain-service` (digest → tags → createTime):

| digest (sha256:…) | tags             | created             |
| ----------------- | ---------------- | ------------------- |
| d7874899c19e27eb  | `2ec6391,latest` | 2026-02-10T17:32:46 |
| e400de137d9b53ef  | `96a8367`        | 2026-02-10T11:30:27 |
| 98805d35361f89d6  | `542690c`        | 2026-02-10T06:23:06 |
| 41ca125783f06da9  | `8286b33`        | 2026-02-09T23:07:36 |
| 8e7c997771d2ca5f  | `e422bae`        | 2026-02-09T22:09:18 |
| 1c8103a49d0e16cd  | `cf3cc2a`        | 2026-02-09T15:35:02 |
| 2ea96b814da060f8  | `2ddaeda`        | 2026-02-09T14:54:42 |
| fc884fd4103806bc  | `172cccf`        | 2026-02-08T12:02:07 |
| 0a701ac3f1748849  | `e1a6395`        | 2026-02-08T09:15:44 |
| 27d6b7637bd2bdd9  | `08e29d6`        | 2026-02-08T09:04:51 |
| c6730dde9209c7f1  | `63b36f8`        | 2026-02-08T08:52:29 |
| f6e2a049a3a226d2  | `be57d3a`        | 2026-02-08T08:46:56 |
| 42a8e55490ab2c5c  | `76c93b9`        | 2026-02-08T08:10:19 |
| af6ac6ded6bf1e0f  | `37fc99f`        | 2026-02-07T13:01:09 |
| c10ff06f6fd1baac  | `65fb1f4`        | 2026-02-07T07:59:40 |
| 3f4ec4e84e688cb9  | `292fa15`        | 2026-02-06T20:23:30 |
| 17eab784ba44ae1d  | `b665631`        | 2026-02-06T16:13:57 |
| fc2b4cba1990c5d7  | `38802b1`        | 2026-02-05T18:40:50 |
| 0d736aae983b87c4  | `aef1f7b`        | 2026-02-05T18:31:33 |
| 4b682826352832f4  | `f4cd884`        | 2026-02-05T18:27:09 |
| 41e2af14498e440f  | `7d35352`        | 2026-02-05T18:27:03 |
| e8e98b8d95778968  | `6d16ac5`        | 2026-02-05T17:11:47 |
| edcfc4ccfdd7cca5  | `4de7a5f`        | 2026-02-05T16:40:13 |
| 775d89790c987bf7  | `1584fdc`        | 2026-02-05T16:22:22 |
| e42ea653db5ac789  | `abcd20b`        | 2026-02-05T15:32:49 |
| 2ac7787e04153c31  | `7253143`        | 2026-02-05T15:32:11 |
| cf4701d3242ae2f9  | `c195bec`        | 2026-02-05T15:21:44 |
| 065a4bc299c5aa92  | `dac4172`        | 2026-02-05T14:20:57 |
| d0f86da1c0b90748  | `16947bb`        | 2026-02-05T13:25:45 |
| 1b5c2aabeec549ca  | `4bc4e23`        | 2026-01-28T11:33:26 |
| 7199c3265a348345  | `5ac4d82`        | 2026-01-27T19:14:56 |
| 09aadac9c89036eb  | `c18b163`        | 2026-02-04T13:18:28 |

(Digests truncated to 16 hex chars for the table; the `:latest` head in full =
`sha256:d7874899c19e27eb6f82cde11f362ec119b863a5f44f186c91f7124cfc3d9fef`, source commit `2ec6391` of the archived
standalone repo.)

Cross-checked before AR-repo deletion: the ONLY Cloud Run job whose container image references
`…/features-onchain-service/…` is `features-onchain-service-job` itself (deleted by this same ruling);
`uts-prod-features-onchain-collect-lst-seasonal-rewards` runs `unified-trading-system/features-service:latest` and the
two `uts-prod-manifest-consolidator-features-onchain-{cefi,defi}` jobs use other images.

### Decommission checklist (execute after this capture is committed)

- [x] P1. ✅ Delete Cloud Run job `features-onchain-service-job` (asia-northeast1) + verify NOT_FOUND — executed
      2026-07-13T23:19Z; `gcloud run jobs describe` → "Cannot find job [features-onchain-service-job]"
- [x] P1. ✅ Delete scheduler `features-onchain-service-daily-trigger` + verify NOT_FOUND — executed 2026-07-13;
      `gcloud scheduler jobs describe` → NOT_FOUND
- [x] P1. ✅ Delete workflow `features-onchain-service-daily` + verify NOT_FOUND — direct delete PERMISSION_DENIED for
      `unified-trading-sa`, executed via Cloud Build executor (Evidence: cloudbuild=3da70942-d49f-4ad4-870f-ba9fedbdff0e
      SUCCESS); verified via second build (Evidence: cloudbuild=db3b655a-efd0-45ac-a369-b8f20e21fbf5 SUCCESS) whose
      `workflows describe` as `1060025368044@cloudbuild.gserviceaccount.com` → NOT_FOUND and `workflows list` no longer
      contains the daily workflow (`features-onchain-service-backfill` intact — not in ruling)
- [x] P1. ✅ Delete schedulers `uts-dev-features-onchain-t1-schedule` + `uts-staging-features-onchain-t1-schedule` +
      verify NOT_FOUND — executed 2026-07-13; both `gcloud scheduler jobs describe` → NOT_FOUND
- [x] P1. ✅ Delete AR repo `features-onchain-service` (asia-northeast1, 14.4 GB / 32 digests) + verify NOT_FOUND —
      direct delete PERMISSION_DENIED for `unified-trading-sa`, executed via Cloud Build executor (Evidence:
      cloudbuild=d571bed5-a3d8-4828-86ed-954ff2f3308e SUCCESS): "Deleted repository [features-onchain-service]",
      in-build `describe` → NOT_FOUND

Decommission COMPLETE 2026-07-13. Untouched per ruling: `uts-prod-features-onchain-collect-lst-seasonal-rewards` (live,
fixed same day), everything in `features-service`, and workflow `features-onchain-service-backfill`. NOTE for a future
deployment-service governance sweep: the terraform sources for the deleted surfaces still exist
(`deployment-service/terraform/services/features-onchain-service/gcp/` — daily workflow + job; the T1 schedulers'
`t1_batch_scheduler.tf` scope) — a `terraform apply` of those roots would RE-CREATE the deleted surfaces; adjacent
finding 4 above already lists them as deletion candidates.

- 2026-07-13 (terraform prune + ruling completion, operator: "do this then"): (1) The backfill workflow
  `features-onchain-service-backfill` — initially left intact — was found to be NON-FUNCTIONAL post-ruling (its YAML
  invokes the deleted `features-onchain-service-job` by name), so it falls under the "delete everything now" ruling:
  deleted via Cloud Build executor **623e38b9** (capture + delete + NOT_FOUND verify in the build log). (2) The PAUSED
  `uts-prod-features-onchain-t1-schedule` scheduler (target job nonexistent — same orphan class as the deleted
  dev/staging pair) deleted + NOT_FOUND verified. (3) TERRAFORM PRUNED — deployment-service@b13f79b: deleted
  `terraform/services/features-onchain-service/` entirely (gcp + aws, incl. committed tfplan artifacts), removed the
  `features-onchain` t1_batch_scheduler.tf map entry, removed `features-onchain-service` from the shared/gcp services
  list with a dated comment mandating `terraform state rm` for the RETAINED live bucket (`features-onchain-<project>` —
  written by the fixed lst-seasonal-rewards job) before the next shared apply. A blind `terraform apply` can no longer
  resurrect any deleted resource. Residual noted, not in scope: stale repo-name references in peripheral
  deployment-service scripts (bootstrap/setup lists — existence-guarded, no infra effect) and AWS shared tf (nothing
  deleted on AWS; S3 buckets hold data).
