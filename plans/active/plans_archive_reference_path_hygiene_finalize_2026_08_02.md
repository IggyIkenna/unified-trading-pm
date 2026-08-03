---
doc_type: plan
title: Scoped reference-path hygiene pass over plans/archive/ — finalize
summary: >-
  Gated closeout for plans_archive_reference_path_hygiene_2026_08_02.md — machine-held via depends_on + gate_on_depends:
  true until ALL of that plan's own todos are done (6 as of 2026-08-02: the original 4, now closed, plus 2 new P3
  follow-ups the parent's own work surfaced). Reconciles the parent's own checkboxes against real evidence
  (self-contained plan, no external source docs to flip back), re-checks the 2 deferred findings for whether their
  blocker has cleared, and archives the parent via the standard 6-step ritual.
status: superseded
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
last_updated: "2026-08-03"
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
superseded_by: plans_archive_reference_path_hygiene_2026_08_02_finalize
depends_on: [plans_archive_reference_path_hygiene_2026_08_02]
gate_on_depends: true
source: >-
  Authored 2026-08-02 (slot-10) to close a check_finalize_plan_coverage.py regression (1 > baseline 0) found while
  shipping an unrelated fix in the same repo — plans_archive_reference_path_hygiene_2026_08_02.md (assigned_vm:
  planning) shipped without a companion gated finalize plan, per plans/active/task_template.md §4's mandatory-pairing
  rule. Updated 2026-08-02 (slot-8, concurrent session) after the parent plan's own work surfaced 2 new P3 follow-up
  todos (duplicate-named archived docs; a pre-existing +1 existence-ratchet gap) — this doc's gate already covers them
  automatically (gate_on_depends reads the parent's live todo state), only the prose needed updating.
assigned_role: review
sequential: true
drift_direction: advance-code
---

# Scoped reference-path hygiene pass over `plans/archive/` — finalize

> **✅ ARCHIVED 2026-08-03, `status: superseded`.** This was one of THREE independent finalize-plan authorings that all
> gated on the same parent (`plans_archive_reference_path_hygiene_2026_08_02.md`) — a duplicate-plan-authoring defect
> discovered by `plans_archive_reference_path_hygiene_2026_08_02_finalize.md` while executing its own archival ritual's
> referrer-fix step. That doc actually did the reconciliation + archival work (all 3 of its todos done, evidence in its
> own Progress Log); this doc's 2 todos below are now redundant with that work and are closed as superseded rather than
> executed a second time. See `plans_archive_reference_path_hygiene_2026_08_02_finalize.md` for the real done-when
> evidence.

## Todos

- [x] ✅ [REVIEW] P2. **SUPERSEDED — see banner above.** Reconciliation was independently completed by
      `plans_archive_reference_path_hygiene_2026_08_02_finalize.md`'s own todos 1-2 (ratchet re-verified format 81/81,
      existence 87/87, exact match to baseline; AMBIGUOUS/UNRESOLVED triage spot-checked with 0 drift). Not re-done
      here.
- [x] ✅ [DOC] P2. **SUPERSEDED — see banner above.** Archival was independently completed by
      `plans_archive_reference_path_hygiene_2026_08_02_finalize.md`'s own todo 3 (parent + all 4 finalize-plan
      duplicates archived together, referrers fixed, INDEX regenerated). Not re-done here.

## Codex SSOTs

- `/codex/11-project-management/cross-reference-path-convention.md` — the ratchet the parent plan's work targets
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-02 (slot-10)** — Authored after-the-fact to close a `check_finalize_plan_coverage.py` regression discovered
  while shipping an unrelated fix in the same repo (the parent plan had already shipped without its required companion).
  `status: active` (not `draft`) per the established no-double-gate precedent — `gate_on_depends: true` already
  machine-holds every todo here until the parent's own todos are `done`.
- **2026-08-02 (slot-8, concurrent)** — Independently hit the same coverage gap while working the parent plan itself
  (which by this point had grown from 4 to 6 todos — 2 new P3 follow-ups surfaced by the parent's own investigation).
  Rebase surfaced slot-10's already-landed version of this exact file; reconciled by updating the stale "4 todos"
  wording and folding the 2 new findings' specific re-check steps into todo 1, rather than shipping a second competing
  copy. No functional gap existed in slot-10's version — `gate_on_depends` already reads the parent's live todo state
  regardless of what the prose says — this is a prose-accuracy fix only.
