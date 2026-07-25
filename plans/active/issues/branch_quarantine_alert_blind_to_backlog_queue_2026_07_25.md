---
doc_type: issue
title: Branch-quarantine STARVATION alert only counts escalation walls, not queued backlog tasks
status: open
nature: record
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, autospawn, alerting, branch-quarantine]
created: "2026-07-25"
source: [/plans/active/ao_fleet_throughput_incident_2026_07_25.md]
assigned_vm: planning
summary: >-
  The branch-quarantine STARVATION Slack alert (`notify_slot_quarantined`) only checks queued CI-escalation walls
  (`count_queued_walls()`), never the backlog-task queue — a future quarantine with queued backlog work but zero queued
  escalation walls would silently page the quiet path instead.
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
parent_epic: orchestrator_master
locked_by:
locked_since:
resolved_by:
---

# Branch-quarantine STARVATION alert only counts escalation walls, not queued backlog tasks

## What I found

`_alert_branch_quarantine` (`agent-orchestrator/server/autospawn.py:1112`) decides whether a quarantined slot fires the
loud STARVATION page (`notify_slot_quarantined`) or the quiet routine alert (`notify_spawn_failure`) based entirely on
`escalation.count_queued_walls()` (`server/escalation.py:578`), which counts rows in the `EscalationQueueRow` table
(CI-failure fix walls only). It never looks at the ~140-row backlog-task queue (`GET /api/backlog`, the `queued` tasks a
normal `AutoSpawnLoop` tick dispatches).

Verified live during the 2026-07-25 04:33-04:52 UTC incident (`ao_fleet_throughput_incident_2026_07_25.md` todo 1): the
alert DID correctly page for slots 4/5/9 because an escalation wall (`agt-8ab986` / `agt-23b3a6`) happened to also be
queued at each alert moment — but that was coincidental to this episode, not a property of the alert correctly detecting
the 25 genuinely queued BACKLOG tasks the plan's `source` field cites as the actual starvation signal.

## Why it matters

A future branch-quarantine episode with queued backlog tasks but ZERO queued escalation walls would silently take the
lighter `notify_spawn_failure` path (informational log only, no Slack page) despite genuine dispatch starvation — the
exact failure mode `notify_slot_quarantined` was built to catch (incident 2026-06-18, cited in the function's own
docstring).

## Recommended decision

Extend the starvation condition in `_alert_branch_quarantine` to
`count_queued_walls() > 0 or count_queued_backlog_tasks() > 0` (a new small helper counting `BacklogTaskRow`/backlog
rows with `status="queued"` and no blocking `blocked_reason`, mirroring `count_queued_walls()`'s shape). Update
`notify_slot_quarantined`'s message text to name whichever queue(s) are non-empty rather than hardcoding "N escalation
walls starved".

- [ ] [INFRA] P2. Add `count_queued_backlog_tasks()` (or equivalent) to `server/escalation.py` or a shared module, and
      change `_alert_branch_quarantine`'s starvation condition (`server/autospawn.py:1140-1146`) to
      `count_queued_walls() > 0 or count_queued_backlog_tasks() > 0`. Update `notify_slot_quarantined`'s Slack copy to
      reflect whichever queue(s) triggered it. Add a regression test (mirroring
      `tests/test_alert_quality_overhaul.py::test_branch_quarantine_pages_starvation_when_walls_queued`) covering: zero
      escalation walls + nonzero queued backlog tasks → STARVATION page still fires. (repo: agent-orchestrator)
