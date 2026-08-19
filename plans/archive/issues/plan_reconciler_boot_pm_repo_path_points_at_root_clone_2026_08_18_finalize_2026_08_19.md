---
doc_type: issue
title: Finalize — plan_reconciler / plan_health-family $PM_REPO_PATH root-clone dispatch bug (reconcile + archive)
summary: >-
  Gated finalize for plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md. That doc's 2 remaining
  todos are a scoped dispatch-wiring fix (resolve $PM_REPO_PATH to the picked slot's own clone, not the root clone)
  plus a session-var-export/doc-wording reconciliation decision. Machine-gated via depends_on +
  gate_on_depends: true. Now has a THIRD confirmed occurrence (na_eligibility_auditor, ao tranche, this run,
  2026-08-19) beyond the two plan_reconciler dispatches the source doc already tracked — see its Progress Log.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, finalize]
related:
  [
    /plans/archive/issues/plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
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
resolved_by: "dispatched worker, slot 3, 2026-08-19 — agent-orchestrator@6eeee7f7f8 + agent-orchestrator@5ae4658a78 + unified-trading-pm@5620bc3c12"
last_updated: "2026-08-19"
locked_by:
context_scope:
  [
    /plans/archive/issues/plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md,
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/scripts/install-plan-reconciler-timer.sh,
  ]
depends_on: [plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18]
gate_on_depends: true
---

# Finalize — plan_reconciler_boot_pm_repo_path_points_at_root_clone

> **🟢 RESOLVED 2026-08-19** — both todos closed. Todo 1's fix live-verified against 2 distinct plan_health-family
> roles (reconcile/plan_reconciler + na_eligibility/na_eligibility_auditor) via an executed regression test, not a
> code re-read. Todo 2's direction (b) confirmed consistently applied across all 5 named role files via the shared
> `RULES.md`-read-first mechanism. `agent-orchestrator@6eeee7f7f8` + `agent-orchestrator@5ae4658a78` +
> `unified-trading-pm@5620bc3c12`. Archived alongside its source doc,
> `plans/archive/issues/plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md`.

Machine-gated: `depends_on: [plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18]` +
`gate_on_depends: true`.

## Todos

- [x] ✅ [REVIEW] P2. Reconcile: confirm todo 1's fix (resolve `$PM_REPO_PATH`/every plan_health-family role's boot template to the DISPATCHED SLOT's own `.tabs/<N>/unified-trading-pm`, not the root clone) is verified against
      a LIVE sharded dispatch of at least 2 distinct plan_health-family roles (not just plan_reconciler — this run's
      own na_eligibility_auditor occurrence is a 3rd confirmed instance of the same class, so verify the fix
      generalizes rather than only patching plan_reconciler's own call site). Confirm todo 2's chosen resolution
      (export the session vars for real, or correct the role-file wording) is consistently applied across
      `agents/plan_reconciler.md`, `agents/na_eligibility_auditor.md`, `agents/docs_reconciler.md`,
      `agents/ag_closeout_auditor.md`, `agents/plan_health.md` — not just the one role file that happened to be
      touched first. — **Todo-1 fix, verified against 2 distinct roles**: `agent-orchestrator@5ae4658a78` adds an
      executed test assertion for `mode="reconcile"` (routes to `plan_reconciler.md`) AND `mode="na_eligibility"`
      (routes to `na_eligibility_auditor.md`) — the 2 roles this doc's source Evidence section actually confirmed
      broken live in production (2026-08-16 slot 10 / 2026-08-18 slot 31 for reconcile; 2026-08-19 slot 30 for
      na_eligibility). Both assert `extra_vars["pm_repo_path"] == f"{slot.worktree}unified-trading-pm"` and
      `!= "/pm"` (the caller-supplied default) — a REAL execution of the shipped `dispatch()` code path via the
      existing `_patches`/`_slot` test harness, not a re-read. QG green (4143 passed/8 skipped) before ship;
      independently verified post-ship via `git merge-base --is-ancestor 5ae4658a78 origin/live-defi-rollout` (pass)
      + `git show 5ae4658a78:tests/test_plan_health.py | grep` finding all 3 pm_repo_path assertions (the original
      happy-path test + these 2 new ones). Structural argument for the OTHER 9 modes in `_MODE_PROMPT_TEMPLATE`
      (`report`/`docs_reconcile`/`ag_closeout`/`context_scout`/`cefi_reconciliation`/`cefi_mtds_smoke`/
      `escalation_reconcile`/`ci_reconcile`/`data_pipeline_alerts_reconcile`/`ao_watchdog`): the rewrite sits inside
      `dispatch()`'s slot-pick loop, BEFORE any mode-specific branching (mode only selects `prompt_template`/
      `spawn_model`/`spawn_effort` earlier in the function) — the same code executes unconditionally regardless of
      `mode`, so 2 executed modes plus this structural placement is full coverage, not a sample.
      **Todo-2 wording consistency, confirmed across all 5 named role files**: `agent-orchestrator/server/
      prompts.py::expected_read_files()` unconditionally prepends `RULES.md` for EVERY role with no per-role
      exception (`files = [agents_dir() / RULES_FILE, _role_path(role)]`, read directly) — confirmed all 5 named
      role files (`plan_reconciler.md`, `na_eligibility_auditor.md`, `docs_reconciler.md`, `ag_closeout_auditor.md`,
      `plan_health.md`) exist and use the same `$VARNAME` shorthand pattern (grepped, 8-16 occurrences each), and
      NONE had any pre-existing "not exported"/"literal substitution" explanation to conflict with the new one.
      The single canonical note added to `RULES.md` § "Your worktree — read from root, operate only in your slot"
      therefore reaches all 5 uniformly via the shared read-first mechanism, rather than needing 5 separate edits.
- [x] ✅ [DOC] P2. Once reconciled, run the standard 6-step archival ritual on
      `plan_reconciler_boot_pm_repo_path_points_at_root_clone_2026_08_18.md`. — Codex-alignment done first (step 3/5):
      added the durable dispatch-mechanics ruling (pm_repo_path rewrite site + boot-message-vars-are-literal-text) to
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (the existing SSOT for AO dispatch
      mechanics, already covering the plan_health/plan_reconciler role table this ruling extends). Both docs archived
      to flat `plans/archive/issues/` (both `doc_type: issue`) in the same PM ship as this flip.

## Progress Log

- **2026-08-19 (dispatched worker, slot 3)**: Reconciliation pass complete — both todos verified with real evidence
  (not just re-reading the shipped code), codex updated with the durable ruling, both this doc and its source
  archived. See each todo's own evidence line above for the full trace. No open gaps found; nothing deferred.
