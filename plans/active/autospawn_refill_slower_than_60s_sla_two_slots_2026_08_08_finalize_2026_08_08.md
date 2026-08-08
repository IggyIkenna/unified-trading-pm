---
doc_type: plan
title: AutoSpawn refill SLA gap — finalize
summary: >-
  Gated closeout for `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until its sole todo (root-cause the AutoSpawn refill SLA gap) is done. Reconciles the
  investigation's evidence quality before archiving.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, autospawn, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/issues/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md,
    /plans/epics/orchestrator_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# AutoSpawn refill SLA gap — finalize

> **Machine-gated on `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until the parent doc's sole todo is `done`.

## Todos

- [ ] [REVIEW] P3. **Verify the root-cause claim is evidence-backed, not asserted.** Confirm the parent doc's
      done-when was actually met: either a named root cause with live evidence (AutoSpawn scheduling/concurrency
      code citation + a reproduced timing gap), or a documented decision with a 10+-sample dataset showing the
      original 2 data points were not representative. **Done when**: the evidence trail is independently checked,
      not just the parent doc's own claim taken at face value. Repo: unified-trading-pm.
- [ ] [DOCS] P3. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08` and repoint every referrer; clear any lock if set.
      Then physically move the parent doc under `plans/archive/2026_08/`. **Done when**: `bash
      scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py` shows no NEW
      dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans for this
      doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually
  dispatching via `depends_on` + `gate_on_depends: true` until the parent doc's sole todo is done.
