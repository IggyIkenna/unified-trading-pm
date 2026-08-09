---
doc_type: plan
title: CI satellite AO batch 7 — finalize (reconcile source doc, archive)
summary: >-
  Gated closeout for `ci_satellite_ao_dispatch_batch7_2026_08_09.md` — machine-held via `depends_on` + `gate_on_depends:
  true` until that plan's one todo is done. Reconciles the source doc's checkbox and archives batch 7 via the standard
  6-step ritual.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-7, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch7_2026_08_09.md,
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
    /plans/active/ci_satellite_ao_dispatch_batch6_2026_08_08.md,
    /plans/active/ci_satellite_ao_dispatch_batch6_finalize_2026_08_08.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch7_2026_08_09]
gate_on_depends: true
source: >-
  Authored alongside `ci_satellite_ao_dispatch_batch7_2026_08_09.md` per `plans/active/task_template.md` §4's
  finalize-plan-coverage rule. Authored `status: active` (not `draft`) per the established no-double-gate finding
  (batch4/5/6's finalize plans record the same): `gate_on_depends: true` already machine-holds every task here until
  batch 7's own todo is `done`.
assigned_role: cicd
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch7_2026_08_09.md,
    /plans/active/issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 7 — finalize

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch7_2026_08_09]` + `gate_on_depends: true` holds
> both todos below until batch 7's one todo is `done`. `sequential: true` because todo 2 (archival) must run after todo
> 1's reconciliation, and must also re-confirm todo 1 didn't leave the source doc newly-archivable.

## Todos

- [ ] [REVIEW] P1. **Reconcile batch-7 todo 1's source doc.** Batch-7 todo 1 ends with `Source:` naming
      `issues/ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md` (Part 8, `[DOC] P2`, "Update stale
      codex docs"). Flip that doc's checkbox to `[x]` citing the batch-7 commit that shipped it — **verify the cited
      commit exists and is an ancestor of `origin/live-defi-rollout` before citing it**
      (`git merge-base --is-ancestor`). Then re-check whether the source doc now has zero open work in checkbox AND
      prose form — it will not (many other open items remain in that doc, all deliberately left behind by batch 7's own
      Progress Log), so do NOT set `status: resolved` on it. **Done when**: the checkbox is flipped with verified
      evidence and the doc's overall open-item count is re-confirmed unchanged apart from this one item.
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch7_2026_08_09.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): confirm no unresolved Deferred item was silently dropped (batch 7 has none — it extracted exactly
      one item and left everything else explicitly in its source docs) → add the archive banner → run the
      codex-alignment check (confirm the 3 codex docs batch-7 todo 1 rewrote are internally consistent with each other
      and with `/codex/08-workflows/ci-cd-flow.md`) → grep the corpus for every referrer of
      `ci_satellite_ao_dispatch_batch7_2026_08_09` and repoint each to the archived path → clear `locked_by` (already
      empty; confirm). **Done when**: the plan is in `plans/archive/2026_08/`, every corpus referrer resolves,
      `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it in the same commit.

## Codex SSOTs

- `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md` — one of the 3 docs batch-7 todo 1 rewrites
- `/codex/07-security/self-hosted-runner-security-posture.md` — one of the 3 docs batch-7 todo 1 rewrites
- `/codex/05-infrastructure/agent-orchestrator-deploy.md` — one of the 3 docs batch-7 todo 1 rewrites
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-09** — Drafted alongside `ci_satellite_ao_dispatch_batch7_2026_08_09.md`. Authored `status: active` per the
  established no-double-gate precedent; batch 7 itself is also authored `status: active` (not `draft`) per this task's
  explicit dispatch instructions.
