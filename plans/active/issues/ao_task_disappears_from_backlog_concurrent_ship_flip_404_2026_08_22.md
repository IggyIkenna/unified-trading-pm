---
doc_type: issue
title: Task disappears from backlog after concurrent ship + plan-flip — /done 404s, one_shot_complete rejected
summary: >-
  Slot 13 received a stale accumulated message showing task
  w22_strategy_execution_messaging_external_api-a61a9972d6a4 completed its real deliverable (code shipped
  execution-service@79e951ea, PM checkbox flipped unified-trading-pm@c1226d47c0, both confirmed reachable on
  origin/live-defi-rollout) but the orchestrator's own backlog row for the task vanished mid-flight — a
  task-scoped /done returned 404 and a one_shot_complete retry was rejected because "slot 13 has no active
  agent owner". The real work landed correctly; only the server's own completion bookkeeping desynced.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog, done-endpoint, race-condition, bookkeeping]
related: []
created: "2026-08-22"
parent_epic: orchestrator_master
assigned_vm: planning
priority: P2
source: [slot-13-accumulated-message]
author: slot-13 (data_engineering/backend_engineer)
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  - agent-orchestrator/server/routes/slots_worker.py
  - agent-orchestrator/server/regen_backlog_from_plan.py
---

# Task disappears from backlog after concurrent ship + plan-flip — /done 404s, one_shot_complete rejected

## What I found

A `/heartbeat` call on slot 13 (2026-08-22) surfaced a queue of accumulated messages, including this one verbatim:

> "Completion verified but task w22_strategy_execution_messaging_external_api-a61a9972d6a4 disappeared from
> backlog after concurrent ship/plan flip. execution-service@79e951ea is on origin; full QG passed; PM flip is
> unified-trading-pm@c1226d47c0. Task-specific /done returned 404, and one_shot_complete was rejected because
> slot 13 has no active agent owner."

I independently re-verified the underlying claim rather than trusting the message: `execution-service@79e951ea`
is confirmed an ancestor of `origin/live-defi-rollout` (`git merge-base --is-ancestor` true), `unified-trading-pm@c1226d47c0`
is likewise confirmed on origin, and `plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md`
line 103's `[BACKEND] P0` todo (the `EventTransport` subscriber item) is already flipped `[x]` with the matching
SHA + QG evidence cited inline. So the real deliverable landed correctly and completely — this is purely an
orchestrator-side desync: the backlog row for the task was removed (presumably by the concurrent
`regen_backlog_from_plan.py` re-derivation noticing the plan checkbox had flipped) before the worker's own
`/done` call reached the server, so the task-scoped completion endpoint had nothing to mark done, and the
fallback `one_shot_complete` path also refused because the slot's active-agent-owner tracking had already been
cleared.

An earlier accumulated message in the same queue (a "REVIEW:" note) claims "PM checkbox remains [ ]" for the
same task/SHA — that claim is now stale/wrong (checkbox is confirmed `[x]` in the current live PM tree), most
likely because the reviewer's snapshot raced the same regen/flip window described above.

## Why it matters

This is a real orchestrator bookkeeping bug, not a data-correctness or deliverable-completeness issue — the
underlying work in both cases (code + plan-flip) landed intact. But an agent hitting this mid-task, without
independently re-verifying against origin the way this pass did, could easily mistake a 404'd `/done` for
"my work didn't land" and either re-do already-shipped work or file a false-negative escalation. A worker
should never have to manually reconstruct completion state from a stale message queue.

## Recommended decision

Harden the `/done` → backlog-regen race: either (a) have `regen_backlog_from_plan.py`'s re-derivation leave a
tombstone/completed marker instead of a hard row-delete when a checkbox flip is observed mid-flight, so a
slightly-late `/done` from the worker that actually did the work still resolves cleanly, or (b) have the
task-scoped `/done` 404 path fall back to a plan-checkbox + origin-SHA verification (the same check this issue
doc's investigation just did by hand) before rejecting, so a genuinely-completed-but-desynced task self-heals
instead of dead-ending in a 404 + owner-rejected combo with no recovery path for the worker.

## Todos

- [ ] [BACKEND] P2. In `agent-orchestrator/server/routes/slots_worker.py`'s `/done` handler, when the task_id is
      not found in the live backlog, before returning 404 check whether the plan checkbox (`plan_ref` + evidence
      SHA, if resolvable from the request body) is already flipped on origin — if so, respond as an idempotent
      success instead of 404, logging a `task_completion_desync_self_healed` activity event. Repo:
      agent-orchestrator.
- [ ] [BACKEND] P2. In `regen_backlog_from_plan.py`, avoid hard-deleting a backlog row for a task whose checkbox
      just flipped while the row is still `dispatched` to a live slot — prefer marking it `done` in place (or a
      short-lived tombstone) so a slightly-late `/done` from the owning slot resolves instead of racing the
      regen. Add a regression test simulating the flip-then-/done ordering. Repo: agent-orchestrator.

## Progress Log

- **2026-08-22 (slot-13)**: Filed from a stale accumulated slot-13 message describing the desync. Independently
  re-verified both SHAs are on origin and the plan checkbox is `[x]` — the underlying deliverable is confirmed
  complete; only the server-side completion bookkeeping needs a fix. No code changes made (out of current
  craft-scope task; filed for AO-dispatch pickup).
