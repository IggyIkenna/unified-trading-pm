---
doc_type: issue
title: Slot stuck task-less on stale spawn_base_role — /done one_shot_complete rejected, self-heal impossible
summary:
  A slot whose SlotRow.spawn_base_role is a stale typed-agent craft (e.g. "cicd") with no matching live AgentRow loops
  forever reporting status=working with task=null — boot_slot's task-less-one-off branch never clears it, and
  _done_one_off's one_shot_complete rejects because no AgentRow exists to archive; only a normal task dispatch clears
  spawn_base_role, which cannot happen while the slot is misrouted into the one-off branch.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, slot-lifecycle, spawn_base_role, one-shot, self-heal]
related: []
created: 2026-07-25
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: NA
priority: P2
estimate_class: refactor
source: slot-2 boot investigation, discovered live 2026-07-25
resolved_by:
locked_by:
drift_direction: advance-code
author: worker-slot-2
---

## What I found

Slot 2 (this session, spawned by the orchestrator as a respawn after a predecessor went stuck >15 min) booted and hit
`428 boot requires read confirmation` demanding `unified-trading-pm/agents/cicd.md` — i.e. `SlotRow.spawn_base_role` for
slot 2 was already `"cicd"` before this session ever POSTed `/boot`. After reading `cicd.md` and re-booting, the
response was:

```json
{ "task": null, "dispatch_reason": "one-off cicd booted — no backlog task; slot held working (not idle)" }
```

But `GET /api/escalations/active` → `[]` and `GET /api/repo-blockers` → `{"open": []}` — there is no live CI/CD wall for
this slot to resolve. Per `agents/cicd.md`'s one-shot contract ("Complete then stop"), I POSTed:

```json
POST /api/slots/2/done {"task_id": "", "sha": "", "evidence": "...", "one_shot_complete": true}
```

which was rejected:

```json
{"detail": "one_shot_complete on slot 2 but no active agent owns its session 'orch-slot-2' —
a Class-A worker must /done with a task_id."}
```

Root cause (read `server/routes/slots_worker.py` + `server/state_store/slots.py`):

- `boot_slot` treats a task-less slot as a "typed one-off" purely off `SlotRow.spawn_base_role`
  (`server/routes/slots_worker.py:249-269`) and holds it `status="working"` (not idle) — by design, so idle-reaper
  scanners skip it.
- `_done_one_off` (`server/routes/slots_worker.py:718`) requires a live `AgentRow` with
  `lifecycle in ("one_shot", "scheduled")` tied to the slot's tmux session before it will archive + free the slot. If
  that AgentRow was already archived/never created (e.g. the predecessor session that originally claimed this slot as a
  cicd escalation died/was killed and its AgentRow got cleaned up, OR the watchdog respawn never re-ran
  `claim_slot_for_typed_agent`), there is nothing for `_done_one_off` to find.
- `spawn_base_role` is ONLY cleared by `assign_task_to_slot` (`server/state_store/slots.py`, comment ~line 100: "clear
  any spawn_base_role a PRIOR typed-agent occupant left behind"), which runs ONLY when `pick_next_task` actually
  dispatches a normal backlog task to this slot. If no normal task is currently dispatchable to this slot (true right
  now — all 17 queued backlog tasks are blocked by prereqs/collisions per `pick_next_task`'s `first_blocking_filter`),
  the slot is stuck in this task-less "cicd" state indefinitely: every `/boot` re-confirms `cicd.md` and returns
  `task: null`, and `/done` with `one_shot_complete` 400s because there's no AgentRow to archive.

## Why it matters

A slot in this state can never self-clear via the documented worker/cicd lifecycle contract (`worker.md` boot loop /
`cicd.md` "complete then stop"). It will sit reporting `status=working` with no actual task — invisible to the
idle-reaper, invisible to `/skip-current-task` (no current_task to skip), and only escapable by an operator manually
hitting some other endpoint (or a raw DB edit) to reset `spawn_base_role`/status. This is the same defect class the
code's own comments warn about (stale `spawn_base_role` surviving past its owning AgentRow).

## Recommended decision

- [ ] [BACKEND] P1. In `server/routes/slots_worker.py::boot_slot`'s task-less-one-off branch (~line 249-269), when
      `spawn_base_role` is set but `ss.find_active_agent_for_session(...)` finds no matching live `AgentRow` for this
      slot's tmux session, treat it as STALE: clear `slot.spawn_base_role = None` and fall through to the normal
      idle/dispatch path instead of reporting "held working" forever. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. Add a regression test in `agent-orchestrator/tests/` that boots a slot with a stale
      `spawn_base_role` and no corresponding `AgentRow`, and asserts the slot recovers to `idle`/normal dispatch instead
      of looping the task-less-one-off branch forever. (repo: agent-orchestrator)
- [ ] [OPERATOR] P2. Until the above ships, an operator hitting this state should reset the slot manually (there is no
      clean self-service endpoint today) — flag this as a UX gap in the same PR: the fix in P1 covers the self-heal
      path, but consider also exposing a `POST /api/slots/{id}/clear-spawn-role` escape hatch for support cases where
      the AgentRow legitimately still exists but the operator wants to force a reset.

## Current slot-2 status (informational, not part of the fix)

At time of filing, `GET /api/escalations/active` = `[]`, `GET /api/repo-blockers` = `{"open": []}`, and all 17 queued
backlog tasks are blocked on prereqs/collisions per `pick_next_task`. There is genuinely no dispatchable work for this
slot right now — this is NOT a symptom of the bug above, just the reason the bug is currently visible (a slot that never
got a normal task dispatched never clears `spawn_base_role`).
