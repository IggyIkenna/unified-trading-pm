---
doc_type: issue
title: >-
  deployment-api follow-ups from the IAM + AR-repo-mapping gaps fix — audit remaining `_AR_REPO_OVERRIDES` entries and
  add a startup-time IAM capability probe
summary: >-
  Two scoped follow-up items migrated forward from
  `/plans/archive/2026_08/issues/deploy_api_cloud_run_deploy_iam_and_ar_repo_gaps_2026_08_07.md` (archived — its own two
  live bugs are fixed + verified, but these two audit/hardening items were explicitly flagged as NOT chased in that
  session). Per the archival ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 1 step 1),
  a deferred item must migrate into a real tracked todo, not evaporate with the archived doc.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [ci-cd, deploy-chain, iam, artifact-registry, cloud-run, follow-up]
related: [/plans/archive/2026_08/issues/deploy_api_cloud_run_deploy_iam_and_ar_repo_gaps_2026_08_07.md]
created: 2026-08-07
last_updated: "2026-08-07"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: devops
resolved_by:
drift_direction: advance-code
depends_on: []
source:
  "cicd wall-resolution (agt-6f2b99), migrated forward while archiving the parent issue for
  check_terminal_status_archived ratchet fix"
locked_by:
locked_since:
context_scope: [/plans/archive/2026_08/issues/deploy_api_cloud_run_deploy_iam_and_ar_repo_gaps_2026_08_07.md]
---

# deployment-api: AR-repo-override audit + IAM capability probe

## Open

- [ ] [INFRA] P2. `_AR_REPO_OVERRIDES` is a hand-maintained allowlist that silently produces a
      wrong-but-plausible-looking path when a service is missing (no fast-fail) — audit the remaining ~20+ services NOT
      in the override dict to confirm each one's actual AR repo matches its own service name (the assumption the
      fallback makes), the same way the parent issue confirmed `alerting-service` didn't. A quick sweep: for each repo,
      compare its own `cloudbuild.yaml`'s `_REGISTRY_REPO` substitution against what `_get_ar_repo_name()` would compute
      — any mismatch is a repo that will hit this exact bug the first time something calls `deploy_build` for it.
- [ ] [INFRA] P3. Consider a startup/health-check-time IAM capability probe for deployment-api (analogous to
      `alerting_service/notifiers/pagerduty.py`'s `lru_cache`-wrapped capability probe fixed earlier in the same
      deploy-chain chase) that verifies `run.developer`-class permissions on its own runtime SA and surfaces a clear
      error/alert BEFORE the first real deploy attempt discovers it via a live 502 — this exact class of "IAM migration
      silently drops a needed role" recurred at least twice in one day (see
      `/plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`, same root shape:
      a migration/extraction event drops something a downstream consumer needed, undetected until first real use).

## Progress Log

- **2026-08-07**: migrated forward from the parent issue doc during its archival (both bugs the parent tracked are
  fixed + live-verified; these two items were explicitly flagged there as not yet chased).
