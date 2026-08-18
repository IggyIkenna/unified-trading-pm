---
doc_type: issue
title: "AO dashboard Activity Log 'Done' tab undercounts — event-vocabulary gap, not a role filter"
summary: >-
  Investigating why the operator's 5-hour rate-limit hit overnight (2026-08-17/18) showed only ~20 "done" tasks in
  the Activity Log despite the fleet having clearly done much more work: the Done tab's `DONE_ACTIVITY_TYPES`
  allowlist (`dashboard/src/App.tsx`) only recognizes `slot_done`-family event types. Escalation completions log as
  `escalation_resolved`/`escalation_resolved_pre_dispatch`/`escalation_unresolved` (`server/escalation.py`) and
  scheduled-task-family completions log as `plan_health_result` (`server/plan_health.py`) — neither vocabulary is in
  the allowlist, so real completions are invisible to the tab even though `activity_log` has them. Live-measured in
  the investigated window: 23 `slot_done` vs 32 additional real completions (7 escalation_resolved + 1
  escalation_unresolved + 21 escalation_resolved_pre_dispatch + 3 plan_health_result) that never appeared — the
  fleet did 55 tasks, the tab showed ~20.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, activity-log, ui, escalation, scheduled-jobs, undercounting]
related:
  [
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
  ]
context_scope:
  [
    agent-orchestrator/dashboard/src/App.tsx,
    agent-orchestrator/server/routes/state.py,
    agent-orchestrator/server/state_store/activity.py,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/plan_health.py,
  ]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: orchestrator_master
priority: P2
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Surfaced investigating a 2026-08-17/18 overnight 5-hour rate-limit hit (interactive session) — the operator asked
  why the Activity Log showed only ~20 done tasks when the actual fleet volume was clearly higher. A background
  agent traced it to `DONE_ACTIVITY_TYPES` (`dashboard/src/App.tsx:116`) and confirmed live via a read-only SSM SQL
  query against the production `activity_log` table (`server/orm.py:447-455`, event-type-only, no role column).
execution_scope: local-only
drift_direction: advance-code
---

# AO dashboard Activity Log "Done" tab undercounts — event-vocabulary gap, not a role filter

## What's wrong

`server/routes/state.py`'s `GET /api/activity` and `server/state_store/activity.py::list_activity()` filter purely
on `event_type`. The dashboard's Done tab (`dashboard/src/App.tsx`) hardcodes:

```
DONE_ACTIVITY_TYPES = ["slot_done", ...DONE_FAILED_TYPES, "tmux_session_lost"]
```

`"slot_done"` is emitted only by the numbered-slot `/done` handler (`server/routes/slots_worker.py:2686-2698`).
Escalation-role completions use a disjoint vocabulary: `"escalation_resolved"` (`server/escalation.py:2565`),
`"escalation_resolved_pre_dispatch"` (`:1887`), `"escalation_unresolved"` (`:2796`). Scheduled-task-family
(`plan_health`/`plan_reconciler`/etc.) completions log `"plan_health_result"` (`server/plan_health.py:1030`). None
of these are in `DONE_ACTIVITY_TYPES`, so the Done tab is structurally blind to two of the fleet's three dispatch
roles (scheduled_task, escalation) — it only ever shows `planning`/backlog-worker completions.

This is NOT a role filter anyone chose deliberately — there's no role column on `ActivityRow`/`activity_log` at
all. It's a vocabulary gap: whoever wrote the tab's allowlist covered the one event type they were looking at
(`slot_done`) and the other two roles' distinct completion-event names were never added.

## Real measured impact

2026-08-17T20:00Z–2026-08-18T03:00Z window (the one investigated for the rate-limit incident): 23 `slot_done`
events (matches the operator's observed "~20 done") vs. 32 additional real completions across escalation and
scheduled-task roles that never rendered. Actual fleet completions: 55. Displayed: ~23. A ~58% undercount in that
window, and structural (not a one-off) — it undercounts by this same mechanism every time the fleet does
meaningful escalation/scheduled work.

## Todos

- [ ] [UI] P2. Extend `DONE_ACTIVITY_TYPES` (`dashboard/src/App.tsx`) to include the escalation and scheduled-task
      completion vocabularies named above (`escalation_resolved`, `escalation_resolved_pre_dispatch`,
      `plan_health_result` — decide whether `escalation_unresolved` counts as "done" or belongs in a distinct
      "failed/unresolved" bucket, it is NOT a success). Verify against the SAME live window this issue was found in
      (or a fresh one) that the Done tab's count now matches a direct `activity_log` query. `pw:L2 ✓` required per
      `/codex/06-coding-standards/ui-testing-layers.md` — a fixture with all three completion vocabularies seeded,
      asserting the tab shows all three, not just `slot_done`.
- [ ] [REVIEW] P3. Check whether any OTHER dashboard surface (KPI panels, fleet-efficiency rollups) shares this same
      `DONE_ACTIVITY_TYPES`-style allowlist and has the identical gap — this was found on one tab, not audited
      fleet-wide across the dashboard.

## Progress Log

- **2026-08-18 (created, /pre-compact)**: extracted from a same-session chat finding (background-agent SSM
  investigation) that had not yet been written to a durable, tracked doc — converting per this workspace's "every
  deferral becomes a `- [ ]` todo, not prose" hard rule before context compacts.
