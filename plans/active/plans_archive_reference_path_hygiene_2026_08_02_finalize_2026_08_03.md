---
doc_type: plan
title: >-
  plans_archive_reference_path_hygiene_2026_08_02 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for plans_archive_reference_path_hygiene_2026_08_02.md — machine-held via depends_on + gate_on_depends:
  true until all of that plan's todos are done. A self-contained plan (its own todos ARE the work, no separate source
  doc to reconcile), so this finalize plan's job is simply: confirm the checkboxes are genuinely flipped with evidence,
  then run the standard 6-step archival ritual. Authored 2026-08-03 to close the finalize-plan-coverage gate
  (check_finalize_plan_coverage.py) that the original plan's shipping without a companion finalize tripped —
  task_template.md §4, "Every AO-dispatched plan needs a gated finalize plan."
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, reference-paths, close-out, finalize]
related:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.08
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [plans_archive_reference_path_hygiene_2026_08_02]
gate_on_depends: true
sequential: true
source: >-
  check_finalize_plan_coverage.py regression (2026-08-03, discovered while shipping an unrelated agent-orchestrator
  fix): plans_archive_reference_path_hygiene_2026_08_02.md is assigned_vm: planning with no gated finalize companion,
  blocking quickmerge for the whole corpus. This doc closes that gate.
assigned_role: review
drift_direction: correct-codex
context_scope:
  [
    /plans/active/plans_archive_reference_path_hygiene_2026_08_02.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# plans_archive_reference_path_hygiene_2026_08_02 — finalize

> **Held by `gate_on_depends: true`, not `status`.** Not dispatched until
> `plans_archive_reference_path_hygiene_2026_08_02` is fully done (or on explicit operator direction to start
> reconciling early).

## Todos

- [ ] [REVIEW] P2. **Reconcile `plans_archive_reference_path_hygiene_2026_08_02.md`'s checkboxes** against whatever
      shipped — flip each `- [ ]` to `- [x]` citing the landing commit(s), confirm the `check_reference_paths`
      format/exist counts genuinely dropped back toward the 161/901 baseline per that plan's own todo 4 done-when (not
      an exact match — allow for legitimate new refs added elsewhere in the corpus since 2026-08-02), then run the
      standard 6-step archival ritual (migrate any DEFERRED items, banner, codex-alignment check, update any
      CLAUDE.md/codex pointer on a new contract, fix every referrer's path corpus-wide, clear lock) since the plan is
      self-contained (no separate source doc to reconcile). If real work remains, leave
      `plans_archive_reference_path_hygiene_2026_08_02.md` active and note what's still open here instead.

## Progress Log

- **2026-08-03**: authored to close the finalize-plan-coverage gate the original plan's shipping tripped.
