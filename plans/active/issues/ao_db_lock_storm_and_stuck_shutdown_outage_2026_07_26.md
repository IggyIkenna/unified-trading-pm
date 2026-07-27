---
doc_type: issue
title:
  A severe SQLite database-is-locked storm across nearly every background loop preceded a stuck graceful shutdown that
  forced a SIGKILL — a real ~23 second orchestrator outage
summary:
  Diagnosed live while investigating an operator-reported dashboard hang (stuck on LOADING, connection indicator
  red/off). journalctl showed a database-is-locked storm hitting TmuxPruner, WorkerLivenessKicker, AgentKeeper,
  HealthMonitor, and /api/state itself (returning 500) between 18:50:53 and 18:53:27 UTC, then uvicorn's --reload
  watcher triggered a restart whose graceful shutdown hung for ~20s before systemd SIGKILLed it. The service recovered
  on its own once restarted; this doc tracks the two real open questions the incident raises rather than letting the
  diagnosis live only in chat.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, sqlite, database-locked, outage, uvicorn, reload, shutdown]
related:
  [
    /plans/archive/issues/ao_review_agent_spawn_db_lock_under_load_2026_07_26.md,
    /plans/archive/issues/ao_dispatch_health_idle_slot_thrash_2026_07_26.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
source:
  Operator screenshot of the dashboard stuck on "LOADING... Fetching dashboard state" with the connection indicator
  showing off/red, at a moment coinciding with a fleet-wide burst of concurrent AO worker activity (15 slots, most
  WORKING). journalctl on the VM confirmed the exact timeline within the same session.
resolved_by:
locked_by:
supersedes:
superseded_by:
drift_direction: advance-code
depends_on: []
---

# DB-lock storm + stuck-shutdown outage — 2026-07-26 18:50–18:54 UTC

## What I found

Real journal excerpt (`journalctl -u orchestrator`), timestamps UTC:

```
18:50:58  ERROR TmuxPruner tick failed (continuing)
          subprocess.TimeoutExpired: tmux has-session ... timed out after 2 seconds
18:51:04  ERROR Exception in ASGI application
          sqlite3.OperationalError: database is locked  [SQL: BEGIN IMMEDIATE]
18:51:07  GET /api/state HTTP/1.1" 500 Internal Server Error
18:51:32  ERROR Health check tick failed
          sqlite3.OperationalError: database is locked
18:51:52  ERROR WorkerLivenessKicker tick failed (continuing)
          subprocess.TimeoutExpired: tmux has-session ...
18:52:02  GET /api/state HTTP/1.1" 500 Internal Server Error
18:52:07  ERROR AgentKeeper tick failed (continuing)
          subprocess.TimeoutExpired: tmux has-session -t =orch-agent-main ...
18:52:11  GET /api/state HTTP/1.1" 500 Internal Server Error
18:52:56  ERROR Health check tick failed
18:53:27  Application shutdown complete... Finished server process [2748679]
18:53:28  Stopping reloader process [2705957]
          (~20s gap — nothing logged)
18:53:49  systemd: orchestrator.service: State 'stop-sigterm' timed out. Killing.
18:53:49  systemd: Killing process 2705957 (python3) with signal SIGKILL.
18:53:50  systemd: Main process exited, code=killed, status=9/KILL
18:53:50  systemd: Found left-over process 2961831 (sh), 2961834 (node), 2958093 (npm exec
          prettier) in control group while starting unit. Ignoring.
18:53:50  systemd: Started orchestrator.service
```

Two distinct, compounding problems:

1. **The lock storm (18:50:53–18:53:27, ~2.5 min)**: `database is locked` / `tmux has-session` timeouts hit FOUR
   separate background loops (TmuxPruner, WorkerLivenessKicker, AgentKeeper, HealthMonitor) essentially simultaneously,
   plus `/api/state` (the dashboard's own core fetch) returned `500` at least 3 times in the window. This is the SAME
   error signature (`sqlite3.OperationalError: database is locked`, `[SQL: BEGIN IMMEDIATE]`) as
   `ao_review_agent_spawn_db_lock_under_load_2026_07_26` (fixed earlier the same day, `agent-orchestrator@222a4be`) —
   but that fix targeted ONE specific caller (`ensure_review_agents`). This storm's breadth (4+ subsystems at once) is
   either (a) a DIFFERENT function with the same held-transaction-across-a-slow-call pattern, still undiagnosed, or (b)
   genuine extreme concurrent-write contention under a real load spike (15 slots, most WORKING, during a large backlog
   surge) that even the fixed code can't fully absorb. **Not yet distinguished — this is the open question.**
2. **The stuck shutdown (18:53:27–18:53:49, ~22s)**: uvicorn's `--reload` file-watcher (the service runs
   `uvicorn server.server:app --reload --reload-dir server`) triggered a restart — likely from a code push landing in
   `server/` during this window. The graceful shutdown (`SIGTERM`) then hung for ~20s with ZERO log output, until
   systemd's stop-sigterm timeout forced a `SIGKILL`. Left-over orphaned processes (`sh`, `node`, `npm exec prettier`)
   were found in the cgroup on the NEXT start — systemd just logged a warning and ignored them. This produced a real,
   measurable **outage of the whole API** (every dashboard fetch — `/api/state`, `/api/healthz`, activity, roles,
   agents, accounts — would have failed with a connection error) for roughly the 18:53:27–18:53:50 window. Matches the
   operator's own screenshot (dashboard stuck on "LOADING...", connection indicator red/off) exactly.

The service self-recovered at 18:53:50 and has served real operator traffic cleanly since (confirmed via live `200 OK`
responses in the journal immediately after). This doc exists so the two real open questions don't just live in chat.

## UPDATE 2026-07-27 01:00–01:22 UTC — the storm is ONGOING and now caused a real functional failure, not just noise

Checked live (per an operator request to verify the daily scheduler) whether `plan-reconciler.timer`'s 01:00 UTC fire
actually dispatched. It DID fire (the systemd timer + curl mechanism work) — `POST /api/plan-health/dispatch` was called
at 01:12:53 UTC (13 min late — separately worth noting, timer jitter or contention-delayed) — but the handler returned
**`500 Internal Server Error`**, root cause `sqlite3.OperationalError: database is locked`. The dispatch script's own
case statement (`install-plan-reconciler-timer.sh`) has NO retry path for an unexpected HTTP code — only `503` retries
(next timer run); a `500` just logs `UNEXPECTED HTTP 500` and exits 1. **Today's plan-reconciler run did not happen and
will not retry until tomorrow's 01:00 UTC fire.**

Widened the check: `journalctl -u orchestrator --since '00:50 UTC' --until '01:22 UTC'` shows **143** occurrences of
`database is locked` in this 32-minute window alone — essentially every background loop hit it at least once:
`TmuxPruner`, `WorkerLivenessKicker`, `AgentKeeper` (review-ensure/agent-record/orphan-main sub-tasks), `Health check`,
`UsagePoller`, `AutoParkReconciler`, `RepoHealthWatcher`, **`PlanReconcilerLivenessCanary`** (the purpose-built monitor
for exactly this failure mode — also hitting the same lock error on its own tick, at 01:20:36 UTC),
`BlockedQueueReconciler`, `AutoSpawnLoop`, and `context-lifecycle`. This is not a one-off blip from the 2026-07-26
incident — it is a live, sustained, systemic condition affecting essentially the whole background-loop ecosystem,
confirmed still happening at the time of this update. Raised priority P2 → **P1** on this basis: this is no longer
"recurring noise," it is causing real scheduled work to silently fail with a day's delay.

## Why it matters

- A stuck-shutdown-forcing-SIGKILL is a genuine robustness gap on a service the WHOLE fleet (15 slots + the operator's
  own dashboard) depends on. If the graceful shutdown routinely hangs this long under load, every code push that lands
  during a busy window risks another ~20-30s outage — worse if the orphaned-process pattern
  (`sh`/`node`/`npm exec prettier` surviving the kill) ever leaves something that actually interferes with the fresh
  start, rather than just being ignored.
- If the lock storm is a genuine SECOND undiagnosed bug (not just load), it's directly the same class of defect
  `ensure_review_agents` was — worth finding and fixing the same way, rather than accepting recurring "database is
  locked" noise as normal.

## Todos

- [ ] [BACKEND] P1. **CONFIRMED 2026-07-27 — `TmuxPruner.prune_once()` (`server/tmux_pruner.py:190-333`) IS an instance
      of the `ensure_review_agents` anti-pattern.** It opens ONE `session_scope()` write transaction, then inside it:
      (1) loops every `SlotRow` with a `tmux_session` set, calling `has_session(name)` (a `tmux` subprocess) per row,
      plus `resume_lifecycle.classify_dead_worker(...)` and — for each dead slot — `reap_dead_slot_worker_tree(...)`
      (more subprocess work); (2) loops every `AgentRow` with a `tmux_session` set, calling `has_session(name)` again
      per row. All of this — potentially dozens of subprocess calls — runs with the SQLite write lock held the whole
      time, scaling with fleet size (15+ slots + several one-shot agent rows at the time of the storm). This is the
      exact class already fixed once in `ensure_review_agents` (`ao_review_agent_spawn_db_lock_under_load_2026_07_26`,
      agent-orchestrator@222a4be) — same repo, same session, not yet applied here. Corroborating LIVE evidence
      (2026-07-27, separate from the original storm): 3 one-shot `cicd` agents (`agt-b3f1d1`, `agt-cf325c`,
      `agt-def412`) sitting `ACTIVE` with `0%` context and no progress message for 1-9 minutes — `TmuxPruner`'s own
      dead-session reaper (`GRACE_PERIOD=30s`, `tmux_prune_interval_seconds=60` default) should catch and archive a
      genuinely-dead one-shot agent's session within ~90s (`server/tmux_pruner.py:328-357`, the
      `archive_agent(..., exit_reason="lifecycle-complete")` path) — a 9-minute lingering `ACTIVE` state is consistent
      with this exact tick either failing/timing out under load or being starved by lock contention, though it could
      also just be a slow cold-start; not independently confirmed via a live tmux-pane check in this session.
  - [ ] [BACKEND] P1. **Fix**: restructure `prune_once()` to collect the slot/agent rows needing a liveness check in a
        read-only pass, close that session, run all `has_session()` / `classify_dead_worker()` /
        `reap_dead_slot_worker_tree()` calls WITHOUT a session open, then open a fresh `session_scope()` only for the
        actual field writes + activity logging — mirroring the `ensure_review_agents` fix's shape. This function is
        larger and more stateful than `ensure_review_agents` was (task-release, resume classification, orphan reaping,
        context-saturation event logging all interleave with the row mutations) — read the WHOLE function first, plan
        the read/act/write split before editing, and re-run the existing `tmux_pruner` test suite plus add a regression
        asserting no `session_scope()` is open during the `has_session()` calls (patch `has_session` to assert
        `db.in_transaction()` is False, or equivalent).
- [ ] [BACKEND] P2. **Investigate why the graceful shutdown hung for ~20s with zero log output** before systemd's
      SIGKILL. Check whether any of the orphaned processes found on the next start (`sh`, `node`, `npm exec prettier` —
      PIDs 2961831/2961834/2958093 at the time) correlate with a specific in-flight operation (a worker's own
      quickmerge/prettier run, dispatched from inside this same orchestrator process's tmux sessions) that the shutdown
      sequence should have detached from cleanly but didn't. Consider whether `KillMode=process` (already set per
      `/codex/05-infrastructure/agent-orchestrator-deploy.md`, specifically to avoid nuking spawned workers on restart)
      is interacting with the reload/shutdown sequence in a way that makes the PARENT uvicorn process wait on children
      it shouldn't be waiting on. Definition of done: either a concrete root cause + fix, or a documented conclusion
      that the shutdown hang is inherent to `KillMode=process`'s tradeoff (protects workers, costs shutdown latency) and
      not worth changing.

## Codex SSOTs

- `/codex/05-infrastructure/agent-orchestrator-deploy.md` — the systemd unit's `KillMode=process` rationale (protects
  spawned workers from a restart, cited above as a possible interaction).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — background-loop model
  (TmuxPruner/WorkerLivenessKicker/AgentKeeper/HealthMonitor) this incident spans.
