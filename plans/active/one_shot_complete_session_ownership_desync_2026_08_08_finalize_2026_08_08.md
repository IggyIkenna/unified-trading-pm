---
doc_type: plan
title: one_shot_complete session-ownership desync — finalize
summary: >-
  Gated closeout for `one_shot_complete_session_ownership_desync_2026_08_08.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until its sole todo (fix idle-reap reclassifying a slot mid-`ScheduleWakeup`-gap) is done.
  Reconciles the shipped fix against the two confirmed live occurrences before archiving.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, one-shot-dispatch, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/issues/one_shot_complete_session_ownership_desync_2026_08_08.md,
    /plans/epics/agent_operating_framework_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/one_shot_complete_session_ownership_desync_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [one_shot_complete_session_ownership_desync_2026_08_08]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# one_shot_complete session-ownership desync — finalize

> **Machine-gated on `one_shot_complete_session_ownership_desync_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until the parent doc's sole todo is `done`.

## Todos

- [ ] [REVIEW] P1. **Reproduce the fix against the exact repro recipe the parent doc names** — a one-shot dispatch
      including a `ScheduleWakeup` gap long enough to trigger idle-reap (both confirmed instances were ~2-3h span
      dispatches) — and confirm `POST /api/slots/{id}/done` with `one_shot_complete: true` no longer 400s after the
      fix. **Done when**: a live or test-simulated reproduction is cited, not just a code-review pass. Repo:
      unified-trading-pm.
- [ ] [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `one_shot_complete_session_ownership_desync_2026_08_08` and repoint every referrer; clear any lock if set.
      Then physically move the parent doc under `plans/archive/2026_08/`. **Done when**: `bash
      scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py` shows no NEW
      dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0 orphans for this
      doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/04-architecture/agent-orchestrator-worker-liveness.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually
  dispatching via `depends_on` + `gate_on_depends: true` until the parent doc's sole todo is done.
