---
doc_type: plan
title: deployment-service / deployment-api integration cleanup — finalize
summary: >-
  Gated finalize plan for deployment_service_api_integration_cleanup_2026_08_18.md — reconciles every todo's cited
  evidence, re-checks the 2 deferred-item gates it may have opened (a follow-up broken-function issue doc; a
  redundant-terraform-local deletion check), then runs the 6-step archival ritual.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, deployment-api, deployment-ui, unified-trading-pm]
scope: [engineer, admin]
tags: [deployment, terraform, cloud-run, launcher-registry, finalize, archival]
related:
  [
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-18
last_updated: 2026-08-20
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
effort: medium
drift_direction: advance-code
depends_on: [deployment_service_api_integration_cleanup_2026_08_18]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/deployment_service_api_integration_cleanup_2026_08_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/PLAN_FORMAT.md,
  ]
supersedes:
superseded_by:
source:
  ["companion mandatory finalize plan, authored alongside deployment_service_api_integration_cleanup_2026_08_18.md per task_template.md §4"]
locked_by:
locked_since:
---

# deployment-service / deployment-api integration cleanup — finalize

Gated on every todo in
[`deployment_service_api_integration_cleanup_2026_08_18.md`](/plans/active/deployment_service_api_integration_cleanup_2026_08_18.md)
being `done` (`depends_on` + `gate_on_depends: true`); runs strictly serially (`sequential: true`) since each step
depends on the prior one's findings.

## Todos

- [ ] [REVIEW] P1. Reconcile every todo's cited evidence in the main plan back to real artifacts — for each
      `- [x]` todo, re-verify its citation independently rather than trusting the self-report: any `<repo>@<sha>`
      resolves via `git cat-file -t <sha>` in that repo's clone; the terraform-rename todo's cited
      `gcloud run jobs executions list` execution IDs actually show `SUCCEEDED` when re-queried; the
      `deployment_service_client.py` fix todo's staging DeployConsole submit result is real (re-run it if cheap, or
      re-verify the cited deployment_id exists); the sibling-function audit todo's filed issue doc (if any) exists
      at its stated path with the table actually populated, not a stub. Done-when: a written per-todo confirmation
      table, zero unresolved citations — any citation that fails to resolve gets its source todo's `- [x]` reverted
      to `- [ ]` in the main plan with a note, not silently waved through.

- [ ] [REVIEW] P2. Re-check the 2 deferred-item gates the main plan may have opened: (a) if the sibling-function
      audit todo found additional live-broken functions in `deployment_service_client.py` beyond `create_deployment`,
      confirm the filed `plans/active/issues/deployment_service_client_broken_functions_<date>.md` doc states clear
      next steps and hasn't gone stale since filing; (b) if the image-naming todo took the "repoint to
      `deployment-service:latest`" branch, confirm the 3 now-redundant `data_pipeline_monitor_image` /
      `deployment_digest_image` / `monitoring_deadman_image` terraform locals were fully DELETED (not left dangling
      unused) via `grep -rn "_image\s*=" deployment-service/terraform/gcp/{data_pipeline_fleet_monitor,deployment_digest,monitoring_deadman}_scheduler.tf`.
      Done-when: both checks resolved; any newly-cleared gate or newly-found gap is spun into a tracked `- [ ]`
      follow-up todo or a new issue doc per the findings-triage HARD RULE (never a prose "next steps" note).

- [ ] [DOC] P1. Run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `deployment_service_api_integration_cleanup_2026_08_18.md`: banner, corpus-wide referrer repoint (this
      finalize plan's own `related:`, `infrastructure_master.md`'s `related_plans:`, and any other doc that came to
      cite it during execution), `git mv` into `plans/archive/2026_08/`. Done-when: main plan archived with zero
      broken corpus referrers, verified via `bash scripts/plan-hygiene/run_hygiene_sweep.sh` (or the equivalent
      referrer check) showing no dangling reference to the pre-archival path.

## Progress Log

- **2026-08-18 (authoring)**: Drafted alongside the main plan per task_template.md §4's mandatory-finalize-plan rule.
  `status: draft` pending operator review.
- **context-scout 2026-08-20**: refreshed context_scope (3 entries)
