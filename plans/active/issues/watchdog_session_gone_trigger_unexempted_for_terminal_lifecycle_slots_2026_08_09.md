---
doc_type: issue
title: >-
  `WorkerLivenessWatchdog`'s "session gone" reap trigger uses the bare non-debounced `has_session()` and is NOT
  exempted for terminal-lifecycle (scheduled/one_shot) slots -- the likely mechanism behind the previously-observed
  typed-agent slot `working`→`idle` flip around a service restart
summary: >-
  Root-cause investigation for `ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 4 (R1: "pin the exact code path
  that flips a typed agent's slot working→idle... already checked & excluded: seed-from-tabs, claim_slot, the
  dispatch-ack requeue, the 25-min health stale-timeout"). Found in `agent-orchestrator/server/worker_liveness_watchdog.py`:
  the per-tick active-slot reap loop's "session gone" check (`if not has_session(tmux_session): ...
  self._reclaim_exited_slot(slot_id)`, ~line 931, `_reclaim_exited_slot` at ~line 1311) calls the BARE, non-debounced
  `tmux_spawn.has_session()` -- not `has_session_debounced()` / `is_session_genuinely_alive()`, the two safer variants
  this SAME codebase already introduced elsewhere specifically to fix a documented transient-false-negative class under
  concurrent tmux-server load (`review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08`, wired into
  `TmuxPruner`/`reap_orphan_agents` via `main_agent_keeper.py:1040`). Critically, this "session gone" check runs
  UNCONDITIONALLY for every active slot (working/dispatched/stale) BEFORE the terminal-lifecycle exemption
  (`_terminal_lifecycle_slot_ids` + `_heartbeat_timeout_for`, ~line 903/1088) is ever consulted -- that exemption only
  widens the SEPARATE heartbeat-SILENCE timeout (Trigger 3, further down the same loop) from 900s to 3600s for a
  scheduled/one_shot agent's slot. A typed agent like `plan_reconciler` gets zero protection from the "session gone"
  trigger specifically. The orchestrator restarts extremely frequently (28 restarts observed in ~14h via
  `journalctl -u orchestrator.service | grep 'PlanReconcilerLivenessCanary started'`, each line = a fresh PID) -- every
  restart causes every watcher loop's FIRST tick to fire near-simultaneously, which is exactly the "concurrent
  command load on a shared tmux server" condition the debounce fix was built for. NOT empirically confirmed against a
  live incident: grepping today's journal for the reap loop's own log line
  (`worker session gone post-spawn → reclaimed to idle (clean exit)`) found 7 instances, none of which time-correlate
  with a slot that was hosting an active `plan_reconciler`/`plan_health` dispatch at that moment -- so this is a
  plausible, code-verified GAP (the guard can be defeated), not a confirmed-live false-positive kill. Separately
  confirmed NOT the cause of the high `reaped-stale` AgentRow-exit_reason rate observed for `plan_reconciler`
  dispatches today (16/20) -- that mechanism (`state_store/agents.py::reap_orphan_agents`, wired via
  `main_agent_keeper.py` with the ALREADY-debounced `is_session_genuinely_alive`) is a separate, independently-gated
  code path and its high hit rate looks like the documented EXPECTED end-of-task archival for a typed agent whose
  Claude CLI session simply exits with no explicit completion call, not a bug.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, worker-liveness-watchdog, plan-reconciler, tmux, has-session, false-negative, typed-agent, scheduled-lifecycle]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/server/state_store/agents.py,
    agent-orchestrator/server/main_agent_keeper.py,
  ]
created: "2026-08-09"
author: ikennaigboaka [slot-20]
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
estimate_class: refactor
depends_on: []
parent_epic: orchestrator_master
resolved_by:
source:
  [
    "batch10 todo 4 (R1/R2) investigation, 2026-08-09 -- code archaeology in worker_liveness_watchdog.py cross-referenced
    against journalctl restart cadence + today's plan_reconciler agent/slot dispatch history in state.db",
  ]
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/server/state_store/agents.py,
  ]
---

# `WorkerLivenessWatchdog`'s "session gone" trigger is unexempted + uses the flaky bare `has_session()`

## What I found

`server/worker_liveness_watchdog.py`'s `_tick_once` reap loop, for every slot with `status in {"working", "dispatched",
"stale"}`:

1. ~Line 903: computes `terminal_lifecycle_slots` (slots bound to a `scheduled`/`one_shot` agent — the
   `plan_health`/`plan_reconciler`/`docs_reconciler`/... family) via `_terminal_lifecycle_slot_ids`.
2. ~Line 931 (BEFORE any per-trigger dispatch, and NOT gated on `terminal_lifecycle_slots` membership):
   `if not has_session(tmux_session): ... self._reclaim_exited_slot(slot_id)` once `spawn_age >
   _SESSION_GONE_GRACE_SECONDS`. `_reclaim_exited_slot` (~line 1311) resets the slot to `idle` (via
   `reset_slot_worker_state(db, slot_id, new_status="idle")`) and, if the slot still held a `dispatched` task,
   requeues or resume-pends it.
3. ~Line 1088 (only reached for a slot that survived step 2): `heartbeat_timeout =
   self._heartbeat_timeout_for(slot_id in terminal_lifecycle_slots)` — THIS is the only place the terminal-lifecycle
   exemption applies, widening the heartbeat-SILENCE budget from 900s to 3600s
   (`tuning.watchdog_scheduled_heartbeat_timeout`, operator ruling 2026-08-08).

So the exemption a `plan_reconciler` dispatch gets is real, but narrow: it only protects against the SILENCE trigger
(Trigger 3). The "session gone" check at step 2 runs first, for every slot, with no lifecycle awareness at all — a
`plan_reconciler` slot is exactly as exposed to it as an ordinary backlog-worker slot.

`has_session()` (`server/tmux_spawn.py:114`) is a single un-retried `tmux has-session` subprocess call. This exact
codebase already documents (in `tmux_spawn.py`'s own module comments, citing
`review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08`) that a bare `has_session()` miss can be a TRANSIENT
false-negative "under concurrent command load" on a shared tmux server, and built two safer wrappers to fix it:
`has_session_debounced()` (retries once after a 0.25s sleep) and `is_session_genuinely_alive()` (debounced + confirms
the pane itself hasn't exited, catching the `remain-on-exit` zombie case too). Per that incident's own fix,
`TmuxPruner`/`reap_orphan_agents`'s liveness check is wired to `is_session_genuinely_alive` (`main_agent_keeper.py:1040`).
`_reclaim_exited_slot`'s check (and its main-loop caller at line 931) were NOT updated to use either safer variant —
confirmed via `grep -n has_session server/worker_liveness_watchdog.py`, every call site in this file (lines 842, 931,
1257, 1333, 1438, 1567, 1680, 1793, 1910) uses the bare form.

The orchestrator process itself restarts very frequently — `journalctl -u orchestrator.service | grep
'PlanReconcilerLivenessCanary started'` shows 28 distinct restarts between 08:31 and 22:45 UTC today (2026-08-09), each
a fresh PID. Every restart re-arms every background loop (`TmuxPruner`, `WorkerLivenessWatchdog`, `AutoSpawnLoop`,
`HealthMonitor`, ...), so their first ticks fire close together — a plausible trigger for the "concurrent tmux-server
load" condition the debounce fix targets, and a plausible match for the task's own framing ("previously empirically
observed around a service restart").

**Not confirmed as a live incident today**: grepping `journalctl -u orchestrator.service` since 00:00 UTC for the
exact log line `_reclaim_exited_slot` emits on a clean-exit reclaim (`worker session gone post-spawn → reclaimed to
idle (clean exit)`) found exactly 7 hits (slots 8×2, 33, 9×2, 4). Cross-referencing each against the plan_reconciler
agent/slot occupancy windows in `state.db`'s `agents` table (20 `plan_reconciler`-kind rows today, spanning slots
2/3/4/6/8/9/12/13/14/15/18/21/23/25/26/27/29/30), none of the 7 reclaim events time-overlap a slot's active
`plan_reconciler` window. So this is a real, code-verified GAP (the exemption can be defeated by this specific
trigger), not a proven-live false-positive kill — the plan_reconciler completions/reaps observed today look
attributable to normal task duration + the (correctly debounced) AgentRow-level reaper instead.

## Why it matters

If this trigger DOES fire against a live typed-agent dispatch (transient tmux flakiness at the wrong moment, most
likely right after one of the frequent restarts), the effect is silent: the slot flips to `idle` and any
`current_task` gets released/requeued, but the actual Claude CLI process and its `plan_reconciler`/`plan_health`/etc.
skill run keep executing in the still-live tmux session, orphaned from the orchestrator's own bookkeeping. The
dashboard would show the slot as free/idle while real work (and API spend) continues unseen, and — for a `reconcile`
dispatch specifically — nothing would notice a MISSED completion signal until `PlanReconcilerLivenessCanary`'s 26h
staleness threshold (or a human) catches it.

## Recommended decision

Two independent, small fixes, either of which closes the gap:

1. Swap `_reclaim_exited_slot`'s (and its line-931 caller's) bare `has_session()` for `has_session_debounced()` or
   `is_session_genuinely_alive()` — consistent with the fix already applied to `TmuxPruner`/`reap_orphan_agents` for
   the identical documented failure class.
2. Gate the "session gone" trigger itself on `terminal_lifecycle_slots` membership the same way the heartbeat-silence
   trigger already is (e.g. a longer `_SESSION_GONE_GRACE_SECONDS` for a scheduled/one_shot slot, or a debounced
   recheck before reclaiming one) — a `plan_reconciler` run legitimately holds its slot for hours, so an extra
   confirmation cost is cheap relative to the failure mode.

Recommend (1) as the minimal, most consistent fix (mirrors the sibling fix exactly); (2) as a belt-and-suspenders
addition if the operator wants defense in depth for terminal-lifecycle slots specifically.

## Todos

- [ ] [BACKEND] P2. In `agent-orchestrator/server/worker_liveness_watchdog.py`, replace the bare `has_session()` call
      that feeds the "session gone" reap trigger (~line 931) and `_reclaim_exited_slot`'s own re-check (~line 1333)
      with `has_session_debounced()` (or `is_session_genuinely_alive()` for parity with `TmuxPruner`). Add/update a
      unit test asserting a single transient `has_session` miss no longer reclaims a slot. Repo: agent-orchestrator.
- [ ] [BACKEND] P3. Consider whether the "session gone" trigger should also consult `terminal_lifecycle_slots` (matching
      the heartbeat-silence exemption) for defense in depth — operator/reviewer judgment call on whether the debounce
      fix alone (todo 1) is sufficient. Repo: agent-orchestrator.

## Progress Log

- **2026-08-09** — Filed from `ao_satellite_ao_dispatch_batch10_2026_08_09.md` todo 4's R1/R2 investigation. See that
  plan's own todo-4 evidence for the live-run observation this finding was cross-checked against.
