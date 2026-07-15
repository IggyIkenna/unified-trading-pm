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

- [ ] [INFRA] P0. Confirm a build against current dependency versions genuinely resolves a wheel containing
      `unified_api_contracts.internal` — verify with a real
      `docker run --rm --entrypoint python <image> -c "import unified_api_contracts.internal.schemas.rbac"`, not just an
      inference from version constraints, before wiring up any new deployment.
- [ ] [INFRA] P0. Stand up a real Cloud Run job (+ any Workflow terraform resources mirroring the old
      `daily_workflow`/`backfill_workflow` definitions) for `features-service`'s `features_service/sports/*` sub-package
      — new terraform in `deployment-service/terraform/**`, reusing the existing `features-service` `cloudbuild.yaml`
      image.
- [ ] [SCRIPT] P0. Map CLI flags/entrypoint: confirm `features_service/sports/*`'s CLI surface matches what the old
      job's Cloud Run args/schedule expected (per this workspace's `--operation`/`--mode`/`--asset-group` CLI
      convention); adjust the new job's args if the consolidated CLI shape differs.
- [ ] [INFRA] P1. Repoint the existing GCS-FUSE mount / bucket wiring (canonical
      `features-sports-prd-central-element-323112`, already correct per the 2026-07-15 bucket-flattening sweep) to the
      new job.
- [ ] [INFRA] P1. Deploy the new Cloud Run job; manually trigger a real execution and watch it reach a genuine
      `SUCCEEDED` terminal state (not just "past the import line") before trusting it.
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
