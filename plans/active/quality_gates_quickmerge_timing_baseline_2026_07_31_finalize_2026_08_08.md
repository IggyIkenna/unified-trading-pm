---
doc_type: plan
title: quality-gates.sh / quickmerge.sh timing baseline — finalize
summary: >-
  Gated closeout for `quality_gates_quickmerge_timing_baseline_2026_07_31.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until the 1 remaining open todo (P3 `profile_qg_resources.py` on planning-vm; 14 of 15 are
  `[x]` done as of 2026-08-09) is resolved. Confirms the Phase-2 planning-vm concurrent-load numbers were actually
  captured before archiving.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, quickmerge, timing, performance, close-out, archival]
related:
  [
    /plans/active/quality_gates_quickmerge_timing_baseline_2026_07_31.md,
    /plans/epics/orchestrator_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/quality_gates_quickmerge_timing_baseline_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [quality_gates_quickmerge_timing_baseline_2026_07_31]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# quality-gates.sh / quickmerge.sh timing baseline — finalize

> **Machine-gated on `quality_gates_quickmerge_timing_baseline_2026_07_31.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue any todo below until the parent doc's remaining real todos are `done`. The
> `check_pm_script_path_refs.py` optimization item on the parent doc is a non-checkbox digest pointer to
> `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 11 — do not wait on it here, it ships via that plan.

## Todos

- [ ] [REVIEW] P2. **Confirm Phase 2's planning-vm concurrent-load numbers were actually captured, not skipped.** The
      parent doc's own frontmatter notes Phase 2 was `BLOCKED-OPERATOR-DECISION` on access mechanism until the
      2026-08-08 round5 investigation ruled AO-dispatch; verify a real second results table (same shape as Phase 1's)
      exists with a stated concurrent-agent-count. **Done when**: the table is cited here with a link/quote, not assumed
      done because the todo is checked. Repo: unified-trading-pm.
- [ ] [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos remain
      (the digest-pointer line does not count as open — it is intentionally non-checkbox); add the archival banner + set
      `status: complete`; grep the corpus for `quality_gates_quickmerge_timing_baseline_2026_07_31` and repoint every
      referrer; clear any lock if set. Then physically move the parent doc under `plans/archive/2026_08/`. **Done
      when**: `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py`
      shows no NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans
      for this doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/06-coding-standards/quality-gates.md` · `plans/PLAN_FORMAT.md` · `plans/active/task_template.md` §4
(finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's remaining todos are done.
