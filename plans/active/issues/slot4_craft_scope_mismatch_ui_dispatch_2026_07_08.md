---
doc_type: issue
title: Slot 4 (craft-scoped data_engineering) was dispatched a ui-developer task — role-based routing gap
summary:
  Slot 4's boot prompt craft-scopes it to data_engineering (manifests/capture_status/pipeline_mode/GCS backfills) and
  instructs it to escalate rather than cross into UI/infra/strategy work. /boot dispatched
  cost_obs_ui_unified_breakdown-004 (assigned_role ui-developer, plan cost_obs_ui_unified_breakdown_2026_07_08.md, repos
  [deployment-ui], TS/React/Playwright) with no target_slot/affinity gating it away from a craft-scoped slot.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [dispatch, role-routing, scope, agent-orchestrator, backlog]
related: [cost_obs_ui_unified_breakdown_2026_07_08.md]
created: 2026-07-08
parent_epic: orchestrator_master
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
priority: P3
drift_direction: advance-code
depends_on: []
source:
  [
    slot 4 /boot response 2026-07-08,
    agent-orchestrator/agents/RULES.md,
    agent-orchestrator/agents/worker.md § "Per-task craft role",
  ]
---

## What I found

Slot 4's operator-provided boot instructions explicitly craft-scope it to `data_engineering` ("You do NOT touch UI,
infra, or strategy math — if the plan needs those, it was mis-scoped: file an issue doc and escalate"). The first
`/boot` call of the session
(`dispatch_reason: "tier=1 priority=50 plan_order=3 — highest-rank queued task with prereqs met and no collision"`)
returned `cost_obs_ui_unified_breakdown-004`:

- `assigned_role: "ui-developer"`
- `repos: []` (task metadata carries no repo, but the plan's frontmatter says `repos: [deployment-ui]`)
- Plan `cost_obs_ui_unified_breakdown_2026_07_08.md` is explicitly TS/React/Playwright-only ("TS strict; tsc / ESLint /
  Vitest / Playwright only (no Python tools)").

CLAUDE.md's system map says "role-dispatch routes tasks to spawned workers by skill (central + role registry)", and
`agent-orchestrator/agents/RULES.md` § 4 documents `target_slot`/`affinity` fields for binding tasks to specific slots —
but this task carried neither, so the dispatcher's "highest-rank queued task with no collision" fallback handed a UI
task to a data_engineering-scoped slot. I used `/skip-current-task` to release it back to the queue (reason: wrong
scope) rather than doing UI work outside this slot's craft.

## Why it matters

This is a routing gap, not a data-correctness issue, so it's low severity — but if slot craft-scoping (per-slot boot
prompts naming a specific craft + "do not cross lines") is meant to be enforced, the dispatcher needs either (a)
`assigned_role`-aware slot matching so a `ui-developer` task only offers to UI-capable slots, or (b) explicit
`target_slot`/`affinity` on every task derived from a single-craft plan. Otherwise every craft-scoped slot will
periodically skip-loop through unrelated tasks before finding one in-scope, wasting a `/boot`→`/skip` round trip per
mismatch and leaving `slot_skips` rows that only exclude that one (slot, task) pair rather than fixing the class of
mismatch.

## Recommended decision

Operator/dispatcher-owner decision — not a data_engineering fix, so not resolving inline:

- [ ] [BACKEND] P3. In the dispatcher's `pick_next_task()` (agent-orchestrator), consider `assigned_role` vs the
      requesting slot's declared craft (if slots come to declare one) before offering a task, OR
- [ ] [BACKEND] P3. Have `regen_backlog_from_plan.py` derive `target_slot`/`affinity` for single-craft plans (e.g.
      `assigned_role: ui-developer` → `affinity: low` toward whichever slot most recently worked a `ui-developer` task)
      so craft-scoped slots skip past these without a live `/skip` round trip.

Neither is urgent (the `/skip-current-task` mechanism already handles it correctly per-instance); filing so the pattern
is tracked if it recurs across slots.
