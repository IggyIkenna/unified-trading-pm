---
doc_type: plan
title: Scoped reference-path hygiene pass over plans/archive/ — finalize
summary: >-
  Gated closeout for plans_archive_reference_path_hygiene_2026_08_02.md — machine-held via depends_on + gate_on_depends:
  true until all 4 of that plan's todos are done. Reconciles the parent's own checkboxes against real evidence
  (self-contained plan, no external source docs to flip back), re-confirms the reference-path baseline actually dropped,
  and archives the parent via the standard 6-step ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reference-paths, ratchet, mechanical, finalize]
related:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /plans/active/issues/plan_reconcile_parked_operator_decisions_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/active/task_template.md,
  ]
created: "2026-08-02"
last_updated: "2026-08-02"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [plans_archive_reference_path_hygiene_2026_08_02]
gate_on_depends: true
source: >-
  Authored 2026-08-02 to close a check_finalize_plan_coverage.py regression (1 > baseline 0) found while shipping an
  unrelated fix in the same repo — plans_archive_reference_path_hygiene_2026_08_02.md (assigned_vm: planning) shipped
  without a companion gated finalize plan, per plans/active/task_template.md §4's mandatory-pairing rule.
assigned_role: review
sequential: true
drift_direction: advance-code
---

# Scoped reference-path hygiene pass over `plans/archive/` — finalize

> **🔒 GATED, not draft.** `depends_on: [plans_archive_reference_path_hygiene_2026_08_02]` + `gate_on_depends: true`
> holds every todo below until all 4 of that plan's own todos are `done`. No separate flip needed for THIS doc.
> `sequential: true` because todo 2 (archival) must run after todo 1 (reconciliation) confirms there is nothing left
> open.

## Todos

- [ ] [REVIEW] P2. **Reconcile the parent plan's own checkboxes against real evidence.** The parent plan is
      self-contained (no external `Source:` docs to flip back — its 4 todos are the work, not an extraction from other
      docs). For each of its 4 todos: verify the cited shipping commit exists and is an ancestor of
      `origin/live-defi-rollout` (`git merge-base --is-ancestor`), and confirm todo 4's own claim (the
      `check_reference_paths` format/exist counts dropped back toward the 161/901 baseline) against a fresh
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` run rather than trusting the recorded number. **Done when**:
      all 4 checkboxes are confirmed evidence-backed and the reference-path ratchet is verified actually cleared (not
      just claimed).
- [ ] [DOC] P2. **Archive `plans_archive_reference_path_hygiene_2026_08_02.md`** via the standard 6-step ritual
      (CLAUDE.md § plan archival): add the archive banner → confirm no codex contract needs updating (this plan only
      runs an existing script over an existing population; it does not establish a new contract) → grep the corpus for
      every referrer of `plans_archive_reference_path_hygiene_2026_08_02` and repoint each to the archived path → move
      to `plans/archive/2026_08/` → clear `locked_by` (already empty; confirm) → archive this finalize doc alongside it
      in the same commit. **Done when**: the plan is in `plans/archive/2026_08/`, every corpus referrer resolves,
      `check_reference_paths.py` has not regressed, and this finalize doc is archived alongside it.

## Codex SSOTs

- `/codex/11-project-management/cross-reference-path-convention.md` — the ratchet the parent plan's work targets
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-02** — Authored after-the-fact to close a `check_finalize_plan_coverage.py` regression discovered while
  shipping an unrelated `ci_satellite_ao_dispatch_batch1` fix in the same repo (the parent plan had already shipped
  without its required companion). `status: active` (not `draft`) per the established no-double-gate precedent —
  `gate_on_depends: true` already machine-holds every todo here until the parent's own 4 todos are `done`.
