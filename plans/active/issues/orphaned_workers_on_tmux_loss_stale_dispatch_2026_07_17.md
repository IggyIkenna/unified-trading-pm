---
doc_type: issue
title: tmux-session-loss orphans worker processes + leaves their tasks stuck `dispatched` on killed slots
summary:
  A ~14:00 UTC tmux/backend hiccup (5× tmux_session_lost) killed the panes of workers on slots 2/3/9 but their claude
  processes survived as untracked orphans (kept running quality-gates.sh locally, stopped heartbeating). The server
  marked slots 2/3 `killed` but did NOT release their in-flight `current_task`, so sports_manifest_canonicalisation-002
  (slot 3) and -010 (slot 2) stayed `dispatched` on dead slots — backlog showed 3-4 dispatched with only 1-2 live
  workers. Immediate re-queue applied; root-cause code fix still needed.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, slot-lifecycle, tmux, orphan-process, stale-dispatch, watchdog, self-healing, observability]
related: [plans/active/sports_manifest_canonicalisation_2026_06_01.md]
created: 2026-07-17
parent_epic: infrastructure_master
priority: P1
source: [agent-orchestrator server slot-lifecycle / TmuxPruner / dead-session handling]
assigned_vm:
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-17
---

## What the operator saw

> "backlog says 3 tasks are dispatched but there is only one active worker running in the fleet? why? there was also a
> hiccup in the backend, it was showing not reachable."

Both symptoms share one root event.

## What happened (timeline, 2026-07-17 UTC)

- **~14:00:07** — the activity feed records **5× `tmux_session_lost`** in the same second (slots incl. 5, plus several
  with `slot_id=None`). This is the "backend not reachable" hiccup — the tmux server / backend blipped and multiple
  worker panes were torn down at once.
- **~14:00:11** — `slot_resume_pending` fired for slots 2 and 3 (the pruner noticed their sessions were gone).
- **14:03:58** — `main_agent_autospawned` + a fresh `orch-agent-main` tmux was created (the main agent itself was
  respawned by the keeper after the blip).
- **Net state at 14:05–14:09** — slots 2 and 3 were left `status=killed`, `worker_alive=false`, `tmux_session=null`, but
  **still holding `current_task`**:
  - `sports_manifest_canonicalisation-002` → dispatched to (dead) slot 3
  - `sports_manifest_canonicalisation-010` → dispatched to (dead) slot 2

  So the backlog read 3–4 `dispatched` while only slots 5 and 7 had live workers.

## The two defects

### Defect A — a killed slot does not release its in-flight task (stale dispatch)

`agents/main.md` documents the intended behaviour: _"the TmuxPruner's auto-kill-on-dead-session case … sets
status=killed and releases any in-flight `current_task` back to the queue."_ That release did **not** happen here —
slots 2/3 went to `killed` with `current_task` still set and the task row still `status=dispatched`. Result: the tasks
are stranded on dead slots forever (no live worker can `/heartbeat` them to completion, and the dispatcher won't
re-offer a task that is still marked `dispatched`). The fleet also looks busier than it is, which masks idle capacity.

**Fix direction:** the slot→`killed` transition (both the TmuxPruner dead-session path and the `tmux_session_lost`
handler) MUST atomically re-queue `current_task` (`status→queued`, `dispatched_to=null`, clear `slot.current_task`) —
the same release `/reassign` performs. Add a reconciler invariant: **no task may be `dispatched` to a slot whose
`worker_alive=false` AND `tmux_session=null`**; on violation, auto-release and emit `stale_dispatch_reclaimed`.

### Defect B — worker processes survive tmux-session loss as untracked orphans

When the panes were torn down, the `claude` worker processes were **not** reaped. They kept running
`scripts/quality-gates.sh` locally and **stopped heartbeating** (last_ping: slot 2 14:03, slot 3 13:59, slot 9 13:59 —
well past the 5-min liveness window). They are invisible to the server (their slots read `killed`/`idle`) yet consume
compute and mutate their `.tabs/N` worktrees. Any work they finish cannot reach the server cleanly (they can't `/done`
into a killed slot), so it is effectively lost — and it races any fresh worker that re-picks the re-queued task.

Orphan roots observed at time of writing (claude worker processes, tmux gone, not heartbeating):

| slot | claude PID | session id | note                                                                                                                    |
| ---- | ---------- | ---------- | ----------------------------------------------------------------------------------------------------------------------- |
| 3    | 294936     | 9e443386   | ~1.8h old, still spawning QG                                                                                            |
| 2    | 1934909    | aee3e476   | relaunched `qg_run4` mid-incident                                                                                       |
| 9    | 1863748    | 6cf84cea   | still running features-service QG; also holds the stranded local commit 58b0a318 the review agent flagged (BLK context) |

**Fix direction:** the pruner must reap the orphaned process tree when it tears down / detects a lost session (kill the
`claude` PID whose slot config dir matches, not just the tmux session), OR the worker's own heartbeat loop must
self-terminate the process when it detects its tmux session / slot registration is gone (fail-fast rather than churn
detached). A periodic "orphan-process" sweep (config-dir → PID → is the slot live?) would catch the residue either way.

## Immediate correction already applied (main agent, 2026-07-17)

Re-queued the two stranded tasks so the fleet is no longer showing phantom dispatches:

```
POST /api/slots/2/reassign {"kill_worker": true}   # released sports_manifest_canonicalisation-010
POST /api/slots/3/reassign {"kill_worker": true}   # released sports_manifest_canonicalisation-002
```

After the correction: **2 dispatched (slots 5, 7) / 2 live workers** — matched. Both tasks are back `queued` for
re-dispatch to tracked workers. Re-queue is safe wrt files because a fresh worker boots into a _different_ `.tabs/N`
worktree; quickmerge rebase reconciles at the LDR push boundary.

**Still outstanding (needs operator / watchdog, NOT auto-killed by main):** the orphan processes 294936 / 1934909 /
1863748 are still alive and should be reaped so they don't race the re-dispatched work or waste an account's compute.
Main does not kill processes; flagged here + in operator chat.

## Acceptance criteria for the fix

- Slot→`killed` (pruner dead-session path AND `tmux_session_lost` handler) atomically re-queues `current_task`; add a
  reconciler invariant + `stale_dispatch_reclaimed` event.
- Orphaned worker processes are reaped on session loss (pruner-side kill or worker-side self-terminate), verified by a
  config-dir→PID→slot-liveness sweep leaving zero orphans.
- Regression: simulate a `tmux_session_lost` for a working slot and assert (a) its task returns to `queued` within one
  pruner tick and (b) no detached `claude` process for that slot remains.
