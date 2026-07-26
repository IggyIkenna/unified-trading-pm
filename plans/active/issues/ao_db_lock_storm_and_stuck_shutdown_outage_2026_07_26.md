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
priority: P2
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

- [ ] [BACKEND] P2. **Determine whether the 18:50–18:53 db-lock storm is a discrete bug or pure load.** Grep for other
      callers matching the `ensure_review_agents` anti-pattern (a `session_scope()` write transaction held across a slow
      subprocess/tmux call) — `TmuxPruner`, `WorkerLivenessKicker`, and `AgentKeeper` are the three loops that hit
      `subprocess.TimeoutExpired` on `tmux has-session` in this exact window; check whether any of them call
      `tmux has-session`/`capture_pane` from INSIDE an open `session_scope()` rather than outside it (the same class of
      fix already applied once this session). If none are found, measure whether the concurrent worker count at the time
      (15 slots, mostly WORKING) is sufficient to explain the storm via ordinary `busy_timeout` exhaustion under load,
      and if so, consider whether `busy_timeout` (currently 120s, `server/db.py`) needs raising further or whether a
      different mitigation (e.g. reducing background-loop concurrency, batching writes) is warranted. Report findings
      before choosing a fix — do not guess at a fix without first confirming which of the two this actually is.
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
