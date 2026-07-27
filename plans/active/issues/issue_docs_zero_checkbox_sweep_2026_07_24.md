---
doc_type: issue
title: Corpus-wide sweep of plans/active/issues/ for status:open docs with zero checkboxes (prose-only deferrals)
summary: >-
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §7 sampled 10 issue docs referenced by the 5 asset-group
  consolidated closeouts — 8/10 passed (had real bounded todos), 2/10 failed (prose-only "suggested next steps" with no
  real `- [ ]` checkbox). One of the two, `plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`, is
  now fixed (a real todo added). The second named FAIL,
  `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`, now also fixed (4 real todos added). The full corpus
  beyond the original 10-doc sample still needs a sweep.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-quality, issue-docs, todo-format, hygiene-sweep]
related:
  [
    /plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md,
    /plans/active/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md,
    /plans/active/task_template.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §7
depends_on: []
---

# Zero-checkbox issue-doc sweep

## Todos

- [x] 1. [DOCS] P2. ✅ **DONE 2026-07-24** — `plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`
      converted its prose-only "Suggested fix direction" into a real bounded `- [ ] [CODE] P2.` todo with a stated
      definition-of-done.
- [x] 2. [DOCS] P2. ✅ **DONE 2026-07-24** — `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`'s
      prose-only "Suggested next steps" converted into 4 real bounded todos, splitting the undecided "Decide
      fold-vs-migrate" judgment call into a fact-gathering todo + a separate `[OPERATOR]`-tagged decision todo per
      task_template.md's bounded-outcome rule.
- [ ] 3. [DOCS] P2. Sweep every remaining `status: open` issue doc under `plans/active/issues/` referenced by any of the
      5 asset-group consolidated closeouts (not just the original 10-doc sample) for zero-checkbox docs; classify + fix
      each genuine gap found, following the same conversion pattern as todos 1-2 above.
