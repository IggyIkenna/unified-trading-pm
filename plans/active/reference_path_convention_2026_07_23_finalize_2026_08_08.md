---
doc_type: plan
title: Cross-reference path convention cleanup backlog — finalize
summary: >-
  Gated closeout for `reference_path_convention_2026_07_23.md` — machine-held via `depends_on` + `gate_on_depends: true`
  until all 4 of that doc's remaining todos (format-violation backlog, existence-violation backlog, the
  sports_satellite_batch2 body-prose fix, and the 2026-08-03 baseline-drift re-measurement) are done. Confirms both
  shrinking-ratchet baselines actually reached (or were re-baselined toward) zero before archiving.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, cross-doc-links, close-out, archival]
related:
  [
    /plans/active/issues/reference_path_convention_2026_07_23.md,
    /plans/epics/agent_operating_framework_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/reference_path_convention_2026_07_23.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [reference_path_convention_2026_07_23]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# Cross-reference path convention cleanup backlog — finalize

> **Machine-gated on `reference_path_convention_2026_07_23.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 4 of the parent doc's remaining todos are `done`.

## Todos

- [ ] [REVIEW] P2. **Confirm the two shrinking-ratchet baselines (`format_count`/`existence_count` in
      `scripts/plan-hygiene/reference_paths_baseline.yaml`) actually moved, and by how much.** The parent doc's own
      todos aim for 0 on both, or an explicitly re-baselined residue with a stated per-entry reason (never a blanket
      re-baseline). **Done when**: a live post-fix run of `check_reference_paths.py` is cited with real numbers, not the
      parent doc's own claim taken at face value. Repo: unified-trading-pm.
- [ ] [REVIEW] P2. **Verify the sports_satellite_batch2 body-prose fix was applied AFTER the file's split landed** (per
      the parent doc's own noted dependency on sports batch 3/5's line-cap split), not as a premature edit that then got
      clobbered by the split. **Done when**: confirmed the fix and the split coexist cleanly at HEAD.
- [ ] [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `reference_path_convention_2026_07_23` and repoint every referrer; clear any lock if set. Then physically move the
      parent doc under `plans/archive/2026_08/`. **Done when**:
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py` shows
      no NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans for this
      doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's 4 remaining todos are done.
