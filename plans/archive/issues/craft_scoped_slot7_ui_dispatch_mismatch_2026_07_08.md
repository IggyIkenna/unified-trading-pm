---
doc_type: issue
title: Slot 7 (data_engineering craft-scoped) dispatched a ui-developer task
summary: |
  A data_engineering-craft-scoped worker slot (7) received a pure UI task
  (`cost_obs_ui_unified_breakdown-008`, role `ui-developer`, repo `deployment-ui`)
  on `/boot`. Filed so the dispatcher's role-affinity routing can be checked for
  why a UI-tagged task reached a data-only slot; slot 7 skipped the task rather
  than cross craft lines.
status: resolved
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [dispatch, role-routing, craft-scoping, worker-lifecycle]
related: [/plans/archive/2026_07/cost_obs_ui_unified_breakdown_2026_07_08.md]
created: "2026-07-08"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
source: [cost_obs_ui_unified_breakdown_2026_07_08.md]
resolved_by: agent-orchestrator@69870f4
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

Slot 7's session is craft-scoped to `data_engineering` (pipeline code only: manifests, capture_status,
sourcing/pipeline_mode, GCS writers/readers, backfills — UI/infra/strategy math explicitly out of scope per this slot's
boot instructions). On `/boot`, the dispatcher handed slot 7 task `cost_obs_ui_unified_breakdown-008` —
`assigned_role: ui-developer`, `repos: [deployment-ui]`, TS/Playwright work in
`plans/active/cost_obs_ui_unified_breakdown_2026_07_08.md` (item 8, "Stale-during-refetch fix",
`src/pages/CostObservability.tsx`). This is pure UI craft with no data-pipeline component.

## Why it matters

Slot 7's craft-scoping is a hard boundary (not a preference) — its boot instructions say a mis-scoped dispatch should be
escalated, not absorbed. Doing UI work from this slot would violate that boundary and skip the UI craft's `pw:L2` gate
discipline this task actually needs. The dispatcher's role-affinity routing let a `ui-developer` task reach a
`data_engineering`-only slot — either slot 7's role tag isn't registered/considered by the dispatcher's role-based
routing, or no `ui-developer`-capable slot was free and it fell through to any-slot dispatch.

## Recommended decision

- Slot 7 is calling `/skip-current-task` on `cost_obs_ui_unified_breakdown-008` (reason: craft mismatch) so it returns
  to `queued` for a UI-capable worker.
- [x] ✅ [INFRA] P2. Check the role-dispatch routing (`agent-orchestrator/server/`, role registry) for why a
      `ui-developer`-tagged task was offered to a slot without that role registered — confirm slot-role registration is
      wired for slot 7, or tighten the any-slot fallback so data-only slots aren't offered UI tasks (repo:
      agent-orchestrator) — agent-orchestrator@`69870f4`.

      **Confirmed root cause**: slot-role registration was NOT wired anywhere — `SlotRow` (orm.py) had no
                                                                          role/craft column, `BootRequest` (models/worker_api.py) accepted no such field, and `pick_next_task()`
                                                                          (dispatch.py) never read one; the ONLY affinity mechanism (`target_slot`/`affinity`) binds a task to a specific
                                                                          slot ID, not to a craft category. The `role_registry.py` + `GET /api/roles` surface is a read-only dashboard
                                                                          view of `agents/*.md`, never consulted at dispatch time. So a craft-scoped persona's "you are CRAFT-SCOPED"
                                                                          text was the ONLY thing enforcing its boundary — purely a prompt-level convention, invisible server-side,
                                                                          exactly matching how slot 3 (this same session, on the sibling `cost_obs_ui_unified_breakdown` plan) had
                                                                          earlier ADOPTED a mismatched ui-developer task rather than skipping it like slot 7 did — two data_engineering
                                                                          slots, two different outcomes, because nothing server-side disambiguated the "correct" behavior.

                                                                          **Fix shipped**: an optional, backward-compatible `slots.slot_role` column (migrated via the existing
                                                                          `_add_missing_columns` idempotent-ALTER pattern) + `BootRequest.slot_role`. `None` (the default for the vast
                                                                          majority of slots) leaves `pick_next_task()` fully unfiltered — unchanged behavior. `prompts.render_worker()`
                                                                          now auto-injects `slot_role=assigned_role` into the rendered `<SLOT_ROLE>` boot-curl placeholder (worker.md)
                                                                          whenever a craft-role template actually renders (an unknown/typo'd role gets `slot_role=""`, never the bogus
                                                                          string — else a retired role name would permanently lock a slot out of every role-tagged task). `pick_next_task`
                                                                          skips any queued task whose `assigned_role` doesn't match a set `slot_role`. Also fixed `spawn_preview`
                                                                          (dashboard "Worker" tab, which has no craft-role selector) so `<SLOT_ROLE>` renders `""` instead of leaking as
                                                                          literal placeholder text. basedpyright/ruff/pytest (1115 passed, incl. 7 new — 5 dispatch-gate tests + 2
                                                                          `render_worker` regression tests for the bogus-role fix) all green.

                                                                          **Not in scope for this fix (adjacent, separate gap — not fixed here)**: `spawn_agent_preview`
                                                                          (`GET /api/spawn/agent-preview`) renders a bare `agents/<role>.md` template via `prompts.render(role, ...)` for
                                                                          ANY role name including the 5 craft-scoped personas — unlike `render_worker`, it never prepends the generic
                                                                          `worker.md` lifecycle (the actual `/boot` curl), so previewing a craft role directly through that endpoint
                                                                          would produce an incomplete prompt with no lifecycle section. This looks pre-existing and independent of the
                                                                          dispatch-routing gap this task closes (it predates my change and my change doesn't worsen it) — flagging for a
                                                                          follow-up, not fixing here to stay in scope.
