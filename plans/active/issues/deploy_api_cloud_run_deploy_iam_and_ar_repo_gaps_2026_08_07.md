---
doc_type: issue
title: >-
  deployment-api's own deploy_build endpoint had two latent bugs — uts-prd-sa missing Cloud Run deploy IAM roles, and a
  missing Artifact Registry repo override for alerting-service — both found only when the service-deployed listener made
  its first real "deploy a DIFFERENT target" call
summary: >-
  Two independent, previously-latent bugs in `deployment-api`'s `deploy_build` endpoint
  (`deployment_api/routes/builds.py`), found while doing the final live end-to-end verification of the
  `alerting-service` deploy chain (see `alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md` — this
  is that doc's 6th and 7th layers). Neither was ever exercised before today because nothing had called `deploy_build`
  for a target OTHER than deployment-api's own self-deploy until the new service-deployed auto-deploy listener's first
  real dispatch.

  1. **IAM**: `uts-prd-sa@central-element-323112.iam.gserviceaccount.com` (deployment-api's own
     runtime identity since the 2026-07-31 SA migration, `deployment-service@118ad9e`) held only
     `roles/run.invoker` at the project level — never `roles/run.developer`/`run.admin`. The
     migration's predecessor identity (`unified-trading-sa`) held both; the migration moved the
     runtime identity but never re-granted the deploy-capable roles the endpoint's
     `gcloud run deploy <target>` subprocess call needs. First real failure:
     `PERMISSION_DENIED: Permission 'run.services.get' denied on resource
     'namespaces/central-element-323112/services/dp-alerting-subscriber'`.
  2. **AR repo mapping**: `_get_ar_repo_name()`'s override dict (`_AR_REPO_OVERRIDES`) had no entry
     for `alerting-service`, so it fell back to the default (repo name == service name), producing
     `asia-northeast1-docker.pkg.dev/central-element-323112/alerting-service/alerting-service:<tag>`
     — but `alerting-service`'s actual published images live under the shared canonical repo,
     `unified-trading-system` (confirmed via its own `cloudbuild.yaml`'s `_REGISTRY_REPO`
     substitution and the real Cloud Build push logs). Second real failure (after fixing #1):
     `Image '...alerting-service/alerting-service:0.61.0' not found`.

  **Both fixed and live-verified end-to-end**: the alerting-service deploy call now succeeds and
  `dp-alerting-subscriber`'s live revision was confirmed serving 100% traffic on the fresh image.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service]
scope: [engineer, admin]
tags: [ci-cd, deploy-chain, iam, artifact-registry, cloud-run, alerting-service, latent-bug]
related:
  [
    /plans/active/issues/alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: devops
drift_direction: advance-code
depends_on: []
source: "main-session /autonomous loop, live end-to-end verification of the alerting-service deploy chain, 2026-08-07"
resolved_by:
  "deployment-service@83a95678 (Terraform IAM), deployment-api@a547b43 (AR repo override), gcloud IAM live-grant applied
  first to unblock the in-flight deploy"
locked_by:
locked_since:
context_scope: [/plans/active/issues/alerting_service_deploy_chain_blocked_by_layered_cicd_bugs_2026_08_06.md]
---

# deployment-api deploy_build: IAM + AR-repo-mapping gaps

## Fixes applied

1. **IAM** — granted `roles/run.developer` to `uts-prd-sa`/`uts-test-sa`/`uts-migration-sa` at project scope, mirroring
   the existing `uts_tier_sa_run_invoker` Terraform pattern exactly
   (`deployment-service/terraform/gcp/bucket_iam_per_tier_sa.tf`). Live-applied via
   `gcloud projects add-iam-policy-binding` first (to unblock the in-flight verification), then declared in Terraform
   (`deployment-service@83a95678`) so a future `tofu apply` doesn't drift from live state.
2. **AR repo mapping** — added `"alerting-service": "unified-trading-system"` to `_AR_REPO_OVERRIDES` in
   `deployment_api/routes/builds.py` (`deployment-api@a547b43`).

**Live end-to-end verification** (not just shipped-and-assumed): after both fixes landed on `main` and deployment-api's
own Cloud Build + Cloud Run redeploy completed (`uts-shared-deployment-api-00456-5sw`), re-called the deploy endpoint
directly — `{"status": "deploying", ...}`, no error. Confirmed via `gcloud run revisions describe`:
`dp-alerting-subscriber-00019-96h`, condition `Ready=True`, `status.traffic` shows
`{"latestRevision": true, "percent": 100}`, image digest matches the fresh build.

## Still open

- [ ] [INFRA] P2. `_AR_REPO_OVERRIDES` is a hand-maintained allowlist that silently produces a
      wrong-but-plausible-looking path when a service is missing (no fast-fail) — audit the remaining ~20+ services NOT
      in the override dict to confirm each one's actual AR repo matches its own service name (the assumption the
      fallback makes), the same way this issue confirmed `alerting-service` didn't. A quick sweep: for each repo,
      compare its own `cloudbuild.yaml`'s `_REGISTRY_REPO` substitution against what `_get_ar_repo_name()` would compute
      — any mismatch is a repo that will hit this exact bug the first time something calls `deploy_build` for it.
- [ ] [INFRA] P3. Consider a startup/health-check-time IAM capability probe for deployment-api (analogous to
      `alerting_service/notifiers/pagerduty.py`'s `lru_cache`-wrapped capability probe fixed earlier in this same
      deploy-chain chase) that verifies `run.developer`-class permissions on its own runtime SA and surfaces a clear
      error/alert BEFORE the first real deploy attempt discovers it via a live 502 — this exact class of "IAM migration
      silently drops a needed role" has now recurred at least twice in one day (see the sibling
      `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md` finding, same root shape: a
      migration/extraction event drops something a downstream consumer needed, undetected until first real use).

## Progress Log

- **2026-08-07 ~08:10-08:41 UTC**: found, root-caused, and fixed both bugs sequentially during the live
  final-verification step of the alerting-service deploy chain (this is that chain's 6th and 7th layered blocker, filed
  separately per the tracking doc's own convention). Investigated via a dispatched read-only sub-agent for bug #1
  (comparing deployment-api's deploy code path against a working example) before self-servicing the IAM grant, per the
  workspace's IAM-self-service policy. Did not chase the broader `_AR_REPO_OVERRIDES` audit in this session (see open
  todo 1) — fixed the specific blocking case, flagged the general pattern for follow-up.
