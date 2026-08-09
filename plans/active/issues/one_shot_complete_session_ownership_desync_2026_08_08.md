---
doc_type: issue
title: "one_shot_complete /done rejects with 400 — idle-reap watchdog reclassifies slot mid-async-wait"
summary: >-
  Two confirmed live occurrences (BLK-dc3f8317 + BLK-af6cef6a, 2026-08-08) where a one-shot dispatch that included long
  ScheduleWakeup-spaced async waits was misclassified as idle/abandoned by the liveness watchdog mid-wait, causing POST
  /api/slots/{id}/done with one_shot_complete:true to return HTTP 400 "no active agent owns its session" after the
  agent's real work was already correctly shipped. Root cause confirmed in occurrence 2: idle-reap fires during a
  legitimate ScheduleWakeup gap, reassigns the slot's session identity server-side, and the original agent can no longer
  signal completion.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [backend, agent-orchestrator, one-shot-dispatch, idle-reap, session-ownership, async-wait]
related: []
created: 2026-08-08
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
source: [direct instruction from main agent, BLK-dc3f8317 + BLK-af6cef6a]
depends_on: []
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/worker_liveness/_respawn.py,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
---

# one_shot_complete session-ownership desync — idle-reap during async-wait

## What I found

Two live occurrences on 2026-08-08 where a one-shot agent dispatch completed its real work and shipped the commits
correctly, but could not signal completion to the orchestrator server.

**Occurrence 1** (BLK-dc3f8317, ~2026-08-08T02:00Z):

- Dispatch: `ag_closeout_auditor` one-shot, agent ID `agt-379688`, slot 4, tranche=ci.
- Real work shipped: `unified-trading-pm@7cc6569c7` (verified ancestor of `origin/live-defi-rollout`).
- `POST /api/slots/4/done` with `one_shot_complete: true` returned HTTP 400:
  `"one_shot_complete on slot 4 but no active agent owns its session ...orch-slot-4... a Class-A worker must /done with a task_id."`
- Reproduced with empty `task_id`, with `task_id=agt-379688`, and after a fresh heartbeat + `skip-current-task`.
- Suspected root cause at the time: an earlier Workflow task-notification reported stopped/not-found, possibly crossing
  a process boundary.

**Occurrence 2** (BLK-af6cef6a, 2026-08-08T04:32Z) — CONFIRMED ROOT CAUSE:

- Dispatch: `cefi_mtds_smoke_tester` one-shot, agent ID `agt-9e871f`, slot 8.
- Real work shipped: `unified-trading-pm@444cc4f3b` + `@476cbd294` (both verified ancestors of
  `origin/live-defi-rollout` — smoke-test report + a new P1 follow-up todo).
- Same `"no active agent owns its session"` 400 on `/done`.
- **Confirmed root cause**: the smoke test ran ~3h across several `ScheduleWakeup`-spaced async waits (real VM polling
  for a multi-phase pipeline check). During one of those legitimate wait gaps, the idle-reap watchdog reclassified slot
  8 as abandoned and handed it an unrelated backlog task (`sports_arb_operator_group_and_commission_bugfix-005`). The
  agent correctly released that task via `/skip-current-task`, then found that re-`POST /boot` demanded `worker.md` (a
  role-class change from the original one-shot boot) — confirming the reclassification had already flipped the slot's
  session identity server-side before `/done` was ever called.

## Why it matters

Any one-shot dispatch whose actual work involves long external waits (VM polling, multi-phase pipeline checks) spanning
enough real time to trigger idle-reap is affected. Both confirmed instances completed their real work correctly and
shipped it, so this is NOT a data-loss risk — but it IS a dispatch-completion-tracking bug that:

- Burns a blocked-question + main-agent verification cycle every time it fires.
- Would mislead anyone who skips the independent git verification into thinking a one-shot dispatch failed when it
  actually succeeded.

## Resolution applied both times (workaround, not a fix)

Main independently re-verified the shipped commits via `git merge-base --is-ancestor`, answered the blocked-question
confirming the work as done, and the slot returned to normal dispatch afterward. The underlying one_shot_complete /
session-ownership-vs-idle-reap-watchdog interaction was never fixed.

## Recommended decision

Fix the idle-reap watchdog to not reclassify a slot mid-one-shot-dispatch while it has a pending `ScheduleWakeup` or
other tracked async-wait in flight. Alternatively (or additionally), harden `POST /api/slots/{id}/done`'s
`one_shot_complete` path to accept completion from the ORIGINAL one-shot `agent_id` even if the backend's
session-ownership record was reassigned in the interim — the actual work-completion evidence (a verified git commit that
is an ancestor of `origin/live-defi-rollout`) is a stronger correctness signal than session-ownership bookkeeping.

## Todos

- [x] ✅ [BACKEND] P1. Fix the idle-reap watchdog to NOT reclassify/reassign a slot mid-one-shot-dispatch while it has a
      pending `ScheduleWakeup` or other tracked async-wait in flight — the watchdog needs to check for an active
      one-shot session's own wait-state before treating slot silence as abandonment. Alternatively/additionally, harden
      `POST /api/slots/{id}/done`'s `one_shot_complete` path to accept completion from the ORIGINAL one-shot `agent_id`
      even if the backend's session-ownership record was reassigned in the interim, since the actual work-completion
      evidence (a verified git commit ancestor of origin) is a stronger signal of legitimacy than session-ownership
      bookkeeping. Reproduce via a one-shot dispatch that includes a `ScheduleWakeup` gap long enough to trigger
      idle-reap (both confirmed instances tonight were ~2-3h span dispatches). (repo: agent-orchestrator) —
      agent-orchestrator@43fc142. Took the hardening path: `tmux_pruner`'s `reaped-stale` archive now snapshots
      `AgentRow.last_tmux_session` before nulling `tmux_session`; `_done_one_off` falls back to
      `find_reaped_stale_agent_for_session` (or an explicit self-reported `agent_id` on `DoneRequest`) and corrects
      `exit_reason` to `lifecycle-complete` — deliberately never touching `SlotRow`, since by the time this fires the
      slot may already be reassigned to unrelated live work. 6 new regression tests in `tests/test_done_one_off.py`
      cover the recovery-via-tmux_session, recovery-via-agent_id (+ cross-slot agent_id mismatch rejection),
      evidence-persistence, and duplicate-call-409 paths. Full `quality-gates.sh` green (2760 passed, 2 skipped).

## Progress Log

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: RECLASSIFY -> `assigned_vm: planning`. Sole open item
  (`[BACKEND] P1`) is a bounded backend bug fix with a confirmed root cause (idle-reap watchdog reclassifying a slot
  mid-`ScheduleWakeup`-gap, verified live twice the same day) and a concrete repro recipe already stated in-doc
  ("reproduce via a one-shot dispatch that includes a `ScheduleWakeup` gap long enough to trigger idle-reap"). No design
  fork requiring an operator -- both candidate fixes named in-doc are complementary, not competing, and the todo does
  not ask for a choice between them. Conflict-check clear: grepped `plans/active/*.md` for
  "idle-reap"/"ScheduleWakeup"/"session-ownership desync" -- zero hits outside this doc.
  `execution_scope: local-only -> orchestrator-agent`. Companion gated finalize:
  `one_shot_complete_session_ownership_desync_2026_08_08_finalize_2026_08_08.md`.

## Progress Log (context-scout)

- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
