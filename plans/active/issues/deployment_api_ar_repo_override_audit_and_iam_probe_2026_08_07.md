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
last_updated: "2026-08-08"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
archive_exempt: true
resolved_by:
drift_direction: advance-code
depends_on: []
source:
  "cicd wall-resolution (agt-6f2b99), migrated forward while archiving the parent issue for
  check_terminal_status_archived ratchet fix"
locked_by:
locked_since:
context_scope:
  [
    /plans/archive/2026_08/issues/deploy_api_cloud_run_deploy_iam_and_ar_repo_gaps_2026_08_07.md,
    deployment-api/deployment_api/routes/builds.py,
    alerting-service/alerting_service/notifiers/pagerduty.py,
    /plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md,
  ]
---

# deployment-api: AR-repo-override audit + IAM capability probe

## Open

- [x] ✅ [INFRA] P2. `_AR_REPO_OVERRIDES` is a hand-maintained allowlist that silently produces a
      wrong-but-plausible-looking path when a service is missing (no fast-fail) — audit the remaining ~20+ services NOT
      in the override dict to confirm each one's actual AR repo matches its own service name (the assumption the
      fallback makes), the same way the parent issue confirmed `alerting-service` didn't. A quick sweep: for each repo,
      compare its own `cloudbuild.yaml`'s `_REGISTRY_REPO` substitution against what `_get_ar_repo_name()` would compute
      — any mismatch is a repo that will hit this exact bug the first time something calls `deploy_build` for it. —
      deployment-api@661c080: ALL 13 remaining services with cloudbuild.yaml use _REGISTRY_REPO=unified-trading-system
      but _get_ar_repo_name() fallback returned service-name (a non-existent repo). Fixed by changing the default to
      _CB_REGISTRY_REPO; removed alerting-service override (redundant with new default).
- [x] ✅ [INFRA] P3. Consider a startup/health-check-time IAM capability probe for deployment-api (analogous to
      `alerting_service/notifiers/pagerduty.py`'s `lru_cache`-wrapped capability probe fixed earlier in the same
      deploy-chain chase) that verifies `run.developer`-class permissions on its own runtime SA and surfaces a clear
      error/alert BEFORE the first real deploy attempt discovers it via a live 502 — this exact class of "IAM migration
      silently drops a needed role" recurred at least twice in one day (see
      `/plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`, same root shape:
      a migration/extraction event drops something a downstream consumer needed, undetected until first real use). —
      deployment-api@374b6757fc: new module iam_capability_probe.py (lru_cache-wrapped probe + is_available()), wired
      into lifespan.py startup + health_routes.py detailed health check; tests updated.

## Progress Log

- **2026-08-07**: migrated forward from the parent issue doc during its archival (both bugs the parent tracked are
  fixed + live-verified; these two items were explicitly flagged there as not yet chased).

- **na-eligibility-audit 2026-08-08 (Phase 2/3, sub-agent conflict-check + apply)**: **RECLASSIFY, applied.**
  Re-verified the whole-doc bar: todo 1 is a precisely-scoped audit with a stated done-when (compare each remaining
  service's `cloudbuild.yaml` `_REGISTRY_REPO` against what `_get_ar_repo_name()` computes; a mismatch is a finding).
  Todo 2 names a concrete, already-shipped analog to mirror (`alerting_service/notifiers/pagerduty.py`'s
  `lru_cache`-wrapped capability probe, fixed earlier in the same deploy-chain chase) and a concrete technical target
  (verify `run.developer`-class permissions on deployment-api's own runtime SA at startup, fail loud before a live 502
  discovers the gap) — a scoped code change with a known pattern to follow, not an open design question. Neither item
  needs a judgment call resolved first. Ran the shared conflict-check protocol
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3): grepped every `status: active`,
  `assigned_vm: planning` doc under `parent_epic: infrastructure_master` (and corpus-wide) for
  `_AR_REPO_OVERRIDES`/`_get_ar_repo_name`/`run.developer` — the only other hit,
  `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md`, is about the GCP **default
  compute SA**'s project-wide IAM roles across 155 VM launchers (a completely different mechanism/target: deployment-api
  never appears in it) — topically adjacent (both IAM-flavored), not a real claim on the same ground. No sibling
  batch/finalize doc or consolidated-closeout doc references
  `deploy_api_cloud_run_deploy_iam_and_ar_repo_gaps_2026_08_07` either. Verdict: clear. Applied: `assigned_vm: NA` ->
  `planning`, `execution_scope: local-only` -> `orchestrator-agent`. **Also fixed a pre-existing frontmatter defect
  while in the doc**: `assigned_role: devops` was not a valid role — `devops` does not exist in the live `agents/*.md`
  registry (valid roles: `ag_closeout_auditor`, `backend_engineer`, `cefi_mtds_smoke_tester`,
  `cefi_reconciliation_auditor`, `cicd`, `conflict_resolver`, `context_scout_auditor`, `data_engineering`,
  `data_pipeline_failure`, `docs_reconciler`, `infra`, `main`, `monitor`, `na_eligibility_auditor`, `plan_health`,
  `plan_reconciler`, `quant_dev`, `review`, `ui_developer`, `worker`) — corrected to `infra`, matching both open todos'
  `[INFRA]` tag per `task_template.md` §3's `[TAG]` -> craft-role mapping. **No separate finalize-plan twin authored**:
  `scripts/quality_gates/check_finalize_plan_coverage.py::_find_violations` scans `plans/active/*.md` only
  (non-recursive), never `plans/active/issues/*.md` (confirmed by direct code read) — this doc, `doc_type: issue` in
  `plans/active/issues/`, is structurally outside that gate's scanned population, same as ~110 other live
  `assigned_vm: planning` issue docs in this corpus with no finalize-plan companion. Archival will be handled directly
  once both todos clear.

- **2026-08-08 (slot-11, deployment_api_ar_repo_override_audit_and_iam_probe-001)**: P2 todo done. Swept all 13 services
  with `cloudbuild.yaml` NOT in `_AR_REPO_OVERRIDES` — every one has `_REGISTRY_REPO=unified-trading-system`, while
  `_get_ar_repo_name()` would return the service name (a nonexistent AR repo → deploy failure on first call). Fix:
  changed default in `_get_ar_repo_name()` from `service` to `_CB_REGISTRY_REPO`; removed `alerting-service` override
  (now redundant since the default matches). `_list_ar_tags`'s dual-repo check for legacy services (instruments,
  execution, market-data-processing) is unaffected. Test updated. Shipped deployment-api@661c080.

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries) — expanded from 1 to include the
  `_get_ar_repo_name()` source (`deployment-api/deployment_api/routes/builds.py`), the remaining P3's cited capability-
  probe analog (`alerting-service/alerting_service/notifiers/pagerduty.py`), and its cited same-root-shape sibling issue
  doc.
