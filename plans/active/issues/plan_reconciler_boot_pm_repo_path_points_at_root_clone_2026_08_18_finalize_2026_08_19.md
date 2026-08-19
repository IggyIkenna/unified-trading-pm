---
doc_type: issue
title: Finalize — plan_reconciler / plan_health-family $PM_REPO_PATH root-clone dispatch bug (reconcile + archive)
summary: >-
  Gated finalize for plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md. That doc's 2 remaining
  todos are a scoped dispatch-wiring fix (resolve $PM_REPO_PATH to the picked slot's own clone, not the root clone)
  plus a session-var-export/doc-wording reconciliation decision. Machine-gated via depends_on +
  gate_on_depends: true. Now has a THIRD confirmed occurrence (na_eligibility_auditor, ao tranche, this run,
  2026-08-19) beyond the two plan_reconciler dispatches the source doc already tracked — see its Progress Log.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, finalize]
related:
  [
    /plans/active/issues/plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-19"
author: na_eligibility_auditor
source: >-
  Authored alongside plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md's RECLASSIFY per the mandatory finalize-twin rule (task_template.md
  Section 4) -- na-eligibility-audit 2026-08-19, ao tranche.
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md,
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/scripts/install-plan-reconciler-timer.sh,
  ]
depends_on: [plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18]
gate_on_depends: true
---

# Finalize — plan_reconciler_boot_pm_repo_path_points_at_root_clone

Machine-gated: `depends_on: [plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18]` +
`gate_on_depends: true`.

## Todos

- [ ] [REVIEW] P2. Reconcile: confirm todo 1's fix (resolve `$PM_REPO_PATH`/every plan_health-family role's boot
      template to the DISPATCHED SLOT's own `.tabs/<N>/unified-trading-pm`, not the root clone) is verified against
      a LIVE sharded dispatch of at least 2 distinct plan_health-family roles (not just plan_reconciler — this run's
      own na_eligibility_auditor occurrence is a 3rd confirmed instance of the same class, so verify the fix
      generalizes rather than only patching plan_reconciler's own call site). Confirm todo 2's chosen resolution
      (export the session vars for real, or correct the role-file wording) is consistently applied across
      `agents/plan_reconciler.md`, `agents/na_eligibility_auditor.md`, `agents/docs_reconciler.md`,
      `agents/ag_closeout_auditor.md`, `agents/plan_health.md` — not just the one role file that happened to be
      touched first.
- [ ] [DOC] P2. Once reconciled, run the standard 6-step archival ritual on
      `plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md`.

## Progress Log
