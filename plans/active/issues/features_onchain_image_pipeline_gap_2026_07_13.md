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
status: open
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
    ../../../codex/15-runbooks/lst-seasonal-rewards-smoke.md,
    ../../../codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md,
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
- Remaining operational caveat: the smoke runbook (`codex/15-runbooks/lst-seasonal-rewards-smoke.md`,
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
   schedulers paused/deleted.
2. **Stale docstring**: `features-service/scripts/onchain/collect_lst_seasonal_rewards_daily.py` usage block still says
   `python -m scripts.collect_lst_seasonal_rewards_daily` (pre-consolidation path; also the `-m` form is broken per the
   shadowing note above).
3. **Stale runbook module paths**: `codex/15-runbooks/lst-seasonal-rewards-smoke.md` references
   `features_onchain_service.collectors.…` — the consolidated home is `features_service.onchain.collectors.…`.
4. **Stale per-service terraform**: `deployment-service/terraform/services/features-onchain-service/` +
   `scripts/setup-cloud-build-triggers.sh` still enumerate the retired standalone repos
   (features-delta-one/-volatility/-onchain/-calendar-service etc.) — candidates for deletion in a deployment-service
   governance sweep.

## Progress Log

- 2026-07-13 22:42Z — terraform fix `deployment-service@5c114aa`; live job updated; verification execution `t9zl9`
  SUCCEEDED (40.68s, exit 0). GCS `gs://features-onchain-central-element-323112/seasonal_rewards/` not yet present —
  consistent with 0 events for 2026-07-12 (write is skipped on empty event list per script `_write_events`); execution
  log detail pending Cloud Logging propagation at doc-write time.
