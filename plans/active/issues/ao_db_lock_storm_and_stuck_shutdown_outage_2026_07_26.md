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
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, sqlite, database-locked, outage, uvicorn, reload, shutdown]
related:
  [
    /plans/archive/issues/ao_review_agent_spawn_db_lock_under_load_2026_07_26.md,
    /plans/archive/issues/ao_dispatch_health_idle_slot_thrash_2026_07_26.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md,
    /plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md,
  ]
created: 2026-07-26
author: unknown
last_updated: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
assigned_role: backend_engineer
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
context_scope:
  [
    agent-orchestrator/server/db.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/tmux_pruner.py,
    /plans/archive/issues/ao_review_agent_spawn_db_lock_under_load_2026_07_26.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
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

- [x] ✅ [BACKEND] P1. **CONFIRMED 2026-07-27 — `TmuxPruner.prune_once()` (`server/tmux_pruner.py:190-333`) IS an
      instance of the `ensure_review_agents` anti-pattern.** It opens ONE `session_scope()` write transaction, then
      inside it: (1) loops every `SlotRow` with a `tmux_session` set, calling `has_session(name)` (a `tmux` subprocess)
      per row, plus `resume_lifecycle.classify_dead_worker(...)` and — for each dead slot —
      `reap_dead_slot_worker_tree(...)` (more subprocess work); (2) loops every `AgentRow` with a `tmux_session` set,
      calling `has_session(name)` again per row. All of this — potentially dozens of subprocess calls — runs with the
      SQLite write lock held the whole time, scaling with fleet size (15+ slots + several one-shot agent rows at the
      time of the storm). This is the exact class already fixed once in `ensure_review_agents`
      (`ao_review_agent_spawn_db_lock_under_load_2026_07_26`, agent-orchestrator@222a4be) — same repo, same session, not
      yet applied here. Corroborating LIVE evidence (2026-07-27, separate from the original storm): 3 one-shot `cicd`
      agents (`agt-b3f1d1`, `agt-cf325c`, `agt-def412`) sitting `ACTIVE` with `0%` context and no progress message for
      1-9 minutes — `TmuxPruner`'s own dead-session reaper (`GRACE_PERIOD=30s`, `tmux_prune_interval_seconds=60`
      default) should catch and archive a genuinely-dead one-shot agent's session within ~90s
      (`server/tmux_pruner.py:328-357`, the `archive_agent(..., exit_reason="lifecycle-complete")` path) — a 9-minute
      lingering `ACTIVE` state is consistent with this exact tick either failing/timing out under load or being starved
      by lock contention, though it could also just be a slow cold-start; not independently confirmed via a live
      tmux-pane check in this session.
  - [x] ✅ [BACKEND] P1. **Fix**: restructure `prune_once()` to collect the slot/agent rows needing a liveness check in
        a read-only pass, close that session, run all `has_session()` / `classify_dead_worker()` /
        `reap_dead_slot_worker_tree()` calls WITHOUT a session open, then open a fresh `session_scope()` only for the
        actual field writes + activity logging — mirroring the `ensure_review_agents` fix's shape. This function is
        larger and more stateful than `ensure_review_agents` was (task-release, resume classification, orphan reaping,
        context-saturation event logging all interleave with the row mutations) — read the WHOLE function first, plan
        the read/act/write split before editing, and re-run the existing `tmux_pruner` test suite plus add a regression
        asserting no `session_scope()` is open during the `has_session()` calls (patch `has_session` to assert
        `db.in_transaction()` is False, or equivalent). — agent-orchestrator@b6f95a0 (2026-07-27T02:36:34+01:00, already
        an ancestor of current LDR HEAD, pre-dates this dispatch). Verified this session (slot-9): read the shipped
        `prune_once()` and confirmed it matches this todo's exact prescription (read-only pass → session-free
        `has_session()`/`reap_dead_slot_worker_tree()` acts → fresh write session for mutations); the regression test
        this todo calls for already exists
        (`tests/test_tmux_pruner_agent_reap.py::test_prune_once_never_holds_a_session_across_has_session_or_reap`,
        asserts `has_session()` is never called while a `session_scope()` is open) — re-ran the full
        `test_tmux_pruner_agent_reap.py` suite fresh (`TMPDIR` routed to scratchpad around the unrelated,
        separately-tracked `shared_host_tmp_tmpfs_full_2026_07_26` full-`/tmp` condition): 5/5 passed. No new code
        change needed; checkbox was stale relative to already-shipped work.
- [x] ✅ [BACKEND] P2. **Investigate why the graceful shutdown hung for ~20s with zero log output** before systemd's
      SIGKILL. Check whether any of the orphaned processes found on the next start (`sh`, `node`, `npm exec prettier` —
      PIDs 2961831/2961834/2958093 at the time) correlate with a specific in-flight operation (a worker's own
      quickmerge/prettier run, dispatched from inside this same orchestrator process's tmux sessions) that the shutdown
      sequence should have detached from cleanly but didn't. Consider whether `KillMode=process` (already set per
      `/codex/05-infrastructure/agent-orchestrator-deploy.md`, specifically to avoid nuking spawned workers on restart)
      is interacting with the reload/shutdown sequence in a way that makes the PARENT uvicorn process wait on children
      it shouldn't be waiting on. Definition of done: either a concrete root cause + fix, or a documented conclusion
      that the shutdown hang is inherent to `KillMode=process`'s tradeoff (protects workers, costs shutdown latency) and
      not worth changing. — **agent-orchestrator@ee98ccb.** Caught a FRESH live recurrence
      (`2026-07-30T01:00:06-01:01:36 UTC`, exactly the full 90s `TimeoutStopSec` before SIGKILL) via direct
      `journalctl -u orchestrator.service` access on this VM (I'm running on it) and isolated the hang to a
      previously-unexamined 15s window: the ASGI worker (`pid 246276`) fully completes its OWN shutdown at `01:01:21`
      (connection-drain, 24s state-snapshot write + S3 upload — both accounted for, not the mystery), the reload
      supervisor then logs its own `"Stopping reloader process [pid]"` (uvicorn's `BaseReload.shutdown()`,
      `uvicorn/supervisors/basereload.py:103-115` — the function's LAST line), and then **zero further log output for
      15s** until SIGKILL. Not the orphaned-process theory this todo named (no correlating in-flight quickmerge/prettier
      process found this time) — the hang is specifically in Python/uvicorn's post-`shutdown()` interpreter-teardown
      path for the RELOAD SUPERVISOR's `multiprocessing.get_context("spawn")` child (confirmed via
      `uvicorn/_subprocess.py`: `get_subprocess()` uses `spawn.Process`, which starts a `resource_tracker` subprocess —
      found one live, parented directly under the reloader PID, on this VM right now). **Fix**: removed
      `--reload --reload-dir server` from `scripts/orchestrator.service`'s `ExecStart` entirely, rather than chasing the
      exact interpreter-teardown mechanism further — confirmed via `scripts/ao-self-pull.sh:207,228`
      (`systemctl restart orchestrator`) that the reload-cron already runs an EXPLICIT, strictly more complete restart
      on every FF pull that changes HEAD (plus a stale-process self-heal branch `--reload` can't provide), making
      `--reload`'s own file-watcher pure redundant overhead — it never added restart coverage, only a race (two
      independent restart triggers on the same file-change event) and this extra process-supervision layer.
      Corroborating evidence beyond the shutdown hang itself: `--reload`'s excess restart cadence ("every 15-70min in
      prod", far more than any reasonable expectation) was already the CONFIRMED root cause of two prior, separately
      fixed bugs — the SQLite-backup wall-clock-cadence gap and the daily-summary boot-fire dedup bug
      (`tests/test_sqlite_backup_wallclock_cadence.py`, `tests/test_daily_summary.py`) — both fixed by making state
      survive a restart rather than by addressing the restart frequency itself. `orchestrator-demo.service` (the sibling
      unit) never used `--reload`; `scripts/dev.sh` keeps its OWN separate `--reload` for local dev, unaffected. Full
      repo QG green (2003 passed, 1 skipped, 78.97s + dashboard 165 passed), shipped via quickmerge --agent. **Honest
      caveat**: this does not 100%-prove the exact bytecode-level cause of the 15s interpreter-teardown stall — but
      removing the entire redundant reload-supervisor layer is correct on its own architectural merits regardless, and
      it eliminates the precise layer where the hang was isolated. **Also not yet live**: the fix is on
      `live-defi-rollout` in the repo, but the DEPLOYED `/etc/systemd/system/orchestrator.service` on this VM is a
      separately-installed copy (substituted paths/user at install time via `install-orchestrator-service.sh`) that does
      not auto-sync from the repo — I do not have privileged access from this sandboxed session (`NoNewPrivileges=yes`
      on the very unit I'd need to edit; confirmed via `sudo -n true` failing with "no new privileges flag is set").
      **Applying it live needs an operator/infra action**: re-run `install-orchestrator-service.sh` (or manually update
      the `ExecStart` line + `daemon-reload` + `restart`) — safe to do at any time per `KillMode=process` (confirmed:
      kills only the uvicorn main PID, tmux/claude worker sessions survive). Added the `[REVIEW]` follow-up below to
      verify the live deploy + confirm the hang stops recurring.
- [x] ✅ [OPERATOR] P2. **Apply `agent-orchestrator@ee98ccb`'s `--reload` removal to the LIVE deployed
      `/etc/systemd/system/orchestrator.service`** on this VM — re-run `install-orchestrator-service.sh` (or manually
      remove `--reload --reload-dir server` from the `ExecStart` line), then
      `sudo systemctl daemon-reload && sudo systemctl restart orchestrator`. Safe per `KillMode=process` (kills only
      the uvicorn main PID; tmux/claude worker sessions in the cgroup survive, confirmed in this doc's Progress Log). No
      worker has privileged access to do this from a sandboxed slot session (`NoNewPrivileges=yes`). (repo:
      agent-orchestrator, infra action) — **✅ DONE 2026-07-30, VERIFIED LIVE 2026-08-06.** Operator flagged this as
      already applied; confirmed against the running planning VM (`i-0c9b283b31d6b5ca7`, ap-northeast-1) by read-only
      SSM rather than taken on trust. Evidence, four ways: (1) the loaded unit's `ExecStart` is
      `…/.venv/bin/python3 -m uvicorn server.server:app --host 0.0.0.0 --port 8765 --log-level info` — **no `--reload`,
      no `--reload-dir`**; (2) `NeedDaemonReload=no`, so the on-disk unit and the loaded unit agree — this is not an
      edited-but-never-reloaded file; (3) the service is `SubState=running` since 2026-08-06 16:13:41 UTC, i.e. it has
      restarted since the change and came up clean; (4) `/etc/systemd/system/orchestrator.service` does still contain
      the literal string `--reload` **3 times, but all three are COMMENTS documenting the removal** — line 83 reads
      `# NO --reload here (removed 2026-07-30, ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md P2 todo)`, and
      lines 84/100 explain why (it was redundant: `scripts/ao-self-pull.sh` already runs `systemctl restart`, and the
      sibling unit never used it). **Trap for whoever re-verifies this**: a bare `grep -c -- '--reload'` on the unit
      file returns `3` and reads like the fix was never applied. It is a false positive — check `ExecStart` via
      `systemctl show orchestrator -p ExecStart`, not the raw file. **Why this sat unflipped**: the work shipped
      2026-07-30 and the checkbox was never flipped in the same turn, so it kept re-surfacing as an open operator
      decision for a week — the false-unchecked class CLAUDE.md's commit+push+flip rule exists to prevent.
- [x] ✅ [REVIEW] P2. **Once the live unit is updated (prior todo), confirm via `journalctl` that the
      `"Started reloader process"` / `"Stopping reloader process"` log lines stop appearing on future restarts** (proves
      `--reload` is actually off in the running process, not just the repo), then watch the next several
      `ao-self-pull.sh`-triggered or explicit restarts for the previously-observed
      `"State 'stop-sigterm' timed out. Killing."` pattern — if it stops recurring across several restarts, close
      this issue with that evidence; if it still recurs even without the reload-supervisor layer, the root cause is
      elsewhere (do not re-guess — the resource_tracker/spawn-context teardown lead in the `[BACKEND]` todo above
      becomes the next thing to check directly, e.g. via `py-spy dump` on a hung process before SIGKILL fires). (repo:
      agent-orchestrator) — **✅ BOTH HALVES VERIFIED 2026-08-06** by read-only SSM `journalctl` on the planning VM.
      **Half 1 (reloader lines stop): PROVEN** — `0` occurrences of `"reloader process"` across **26 real systemd unit
      starts** in the retained journal. **Half 2 (`"State 'stop-sigterm' timed out. Killing."` stops recurring): PROVEN
      by absence across restarts** — `0` occurrences of `stop-sigterm` and `0` of `timed out. Killing` anywhere in the
      retained journal, across those same 26 restarts. Since the failure mode manifested _on shutdown/restart_, 26 clean
      restarts is a real sample, not a quiet window.

      **Stated limitation — do not over-read this as a before/after comparison.** This VM's journald retention is only
      ~15 hours (oldest retained `orchestrator` entry at measurement time: `2026-08-06T00:45:03Z`, ~220 MB total
      journal). A pre-fix baseline is therefore **unavailable** — querying `--since 2026-07-20 --until 2026-07-30`
      silently returns `0` too, not because the pattern was absent then but because those logs are rotated away. So
      the evidence here is "the failure mode does not occur across 26 post-fix restarts", which is strong on its own
      terms; it is NOT "occurrences went from N to 0". Anyone re-verifying should measure the retained window first
      (`journalctl -u orchestrator -o short-iso | head -1`) before trusting a `--since` date that predates it — a
      `--since` older than retention produces a confident-looking zero that means nothing.

      **Incidental observation, not part of this todo**: those 26 unit starts fall inside a ~15-hour window (~1.7
      restarts/hour). Some are legitimate `ao-self-pull.sh` deploy restarts, but the rate is high enough to be worth a
      glance against
      `/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`'s crash-loop concern.
      Not investigated here and NOT claimed to be a fault — recorded so the number is not lost.

- [x] ✅ [BACKEND] P2. **Second, independent contributing-latency finding + fix, 2026-07-30** (downstream of Problem 1
      above, NOT a duplicate of the `--reload`/`ee98ccb` finding two todos up — both are real, `ee98ccb` is the one that
      actually explains the specific incidents named in this doc). Chased two leads before the `ee98ccb` journalctl
      trace was available: (1) `TimeoutStopSec` deploy-drift — RULED OUT (the repo's value was raised `30→90` on
      2026-06-02, well before this incident; live-verified via read-only SSM that the deployed unit already carries 90
      too — no config change made). (2) A genuine, separate code smell: `server/server.py`'s `lifespan` shutdown handler
      stopped ~19 background loops SEQUENTIALLY, and every loop's own `.stop()` blocks on `thread.join(timeout=5-10s)` —
      under this doc's own Problem-1 DB-lock-storm/tmux-timeout contention this could genuinely slow the
      PRE-"Application shutdown complete" portion of shutdown. **Honest scoping**: the `ee98ccb` journalctl trace two
      todos up shows the ~15-20s hang happens AFTER "Application shutdown complete" is logged — i.e. after these
      loop-stop() calls have already finished — so this is NOT what caused the specific incidents this doc documents.
      Still a real, verified latency improvement on its own merits (worst case `sum(per-loop timeout)` →
      `max(per-loop timeout)`), shipped harmlessly: `agent-orchestrator@61b7a4f` — new `_stop_loops_concurrently()`
      helper (`ThreadPoolExecutor`, one loop's raised exception logged + doesn't block the others) + 4 regression tests
      (`tests/test_server_shutdown.py`); `loop_supervisor.stop()` stays sequential/first per its own pre-existing
      must-complete-before-the-rest comment. `ruff`/`basedpyright` clean; full local `quality-gates.sh` green (2006
      passed, 2 skipped). Left in place as a genuine improvement, not reverted.

## Recurrence + memory-footprint evidence — 2026-07-27 (main agt-498659)

The shutdown-hang → SIGKILL is **not a one-off** — it recurred **3× on 2026-07-27** and the service restarted **7× that
day** at the unit level. `journalctl -u orchestrator.service --since today`:

```
Started:  08:31:10, 09:01:38, 10:48:30, 11:01:42, 13:01:36, 13:15:23, 14:31:37
Stop→SIGKILL (code=killed status=9/KILL, "Failed with result 'timeout'"):
          11:01:42, 13:01:36, 14:31:37   ← graceful stop timed out, systemd SIGKILLed
Clean deactivate:  13:15:23
Per-cycle resource line (every restart):  28.8G memory peak, 15.4G memory swap peak
```

Two things this adds to the open P2 shutdown-hang todo:

1. **Recurring, ~1–2h cadence** — this is now a daily-recurring restart+SIGKILL pattern, not the single 07-26 incident.
   Each `deactivating` phase drains ~50–90s (observed live: one cycle sat `deactivating`/`stop-sigterm` for ~51s before
   going `active`, then another ~50s before uvicorn rebound and the port bound). During that window `/api/state` and
   `/poll` are unreachable (connection refused) — a real, if brief, recurring outage the fleet rides through.
2. **28.8G RSS + 15.4G swap peak per cycle** — the orchestrator's own memory footprint is enormous and heavily swapped.
   This is very likely _why_ the graceful stop hangs (a swapped-out process is slow to respond to SIGTERM → systemd hits
   `TimeoutStopSec` → SIGKILL), and it plausibly links this doc to the host-RAM-exhaustion cluster
   (`/plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md`): an orchestrator peaking at
   28.8G + 15.4G swap on a shared host is a prime contributor to the low-FREE-RAM condition that's been reaping
   background QG/quickmerge processes. Worth investigating the two together — the memory footprint may be the common
   root, not two independent problems.

`NRestarts=0` in `systemctl show` throughout — i.e. these are watchdog/self-heal `systemctl restart`s (or reload-driven
stops), not systemd `Restart=` auto-restarts, consistent with the backend-owned memory-cap/watchdog self-heal path.

## Codex SSOTs

- `/codex/05-infrastructure/agent-orchestrator-deploy.md` — the systemd unit's `KillMode=process` rationale (protects
  spawned workers from a restart, cited above as a possible interaction).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — background-loop model
  (TmuxPruner/WorkerLivenessKicker/AgentKeeper/HealthMonitor) this incident spans.

## Progress Log

- **2026-07-30T12:14Z (slot 8, review)** — Dispatched `ao_db_lock_storm_and_stuck_shutdown_outage-007` (this `[REVIEW]`
  todo). Running directly on the orchestrator VM (`ip-172-31-5-118`) gave direct access: confirmed via
  `systemctl status orchestrator.service`'s own process listing that the live `ExecStart` STILL carries
  `--reload --reload-dir server` — the `[OPERATOR]` todo is still genuinely not applied. Confirmed `sudo -n true` still
  fails (`NoNewPrivileges=yes`) even from a session running on the VM itself — no more privileged access than prior
  sandboxed sessions had. Also discovered slot-15's earlier park (`-005`/`-006`, priority 999 + prereqs gate) had
  silently reverted to a fresh, ungated `-007` — NOT the same bug slot-15 already fixed (todo-text-edit fingerprint
  drift), but a related gap: the park didn't carry forward across an unrelated SIBLING todo being added to this same doc
  afterward. Re-applied the same park recipe to `-007` directly on the live `backlog.yaml` (this session has filesystem
  access on the VM) and verified it survives BOTH `/reload` and a real `/regen` tick this time. Filed a scoped follow-up
  issue for the underlying gap:
  [backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md](/plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md).
  Not flipping this todo's checkbox — its own precondition (live unit updated) is still unmet. No code shipped this
  entry.

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **2026-07-30 (slot-9, `backend_engineer` craft for this todo)**: dispatched the P1 `prune_once()` todo. Found the fix
  ALREADY SHIPPED — `agent-orchestrator@b6f95a0` (2026-07-27T02:36:34+01:00, an ancestor of current LDR HEAD) implements
  exactly the prescribed read/act/write split, and the prescribed regression test already exists
  (`test_prune_once_never_holds_a_session_across_has_session_or_reap`). Re-ran the full
  `tests/test_tmux_pruner_agent_reap.py` suite fresh this session: 5/5 passed (TMPDIR routed around the unrelated,
  separately-owned `shared_host_tmp_tmpfs_full_2026_07_26` full-`/tmp` condition, not touched here). No code change
  needed — flipping both checkboxes as stale-relative-to-shipped-work. The P2 shutdown-hang todo remains open and
  untouched (out of this dispatch's scope).
- **2026-07-30T05:00-05:25Z (slot 16, `backend_engineer`)**: dispatched the P2 shutdown-hang todo. Running directly on
  the orchestrator VM gave direct `journalctl -u orchestrator.service` + live `systemctl status` access — caught a fresh
  recurrence today (`01:00:06-01:01:36 UTC`) and, unlike prior sessions, had enough log detail this time to isolate the
  ~15s unexplained gap to a SPECIFIC location: after uvicorn's reload supervisor (`BaseReload.shutdown()`) logs its own
  final line and returns, with nothing further until SIGKILL — i.e. Python/uvicorn interpreter-teardown for the
  reload-supervisor's `multiprocessing.get_context("spawn")` child, not app code. Traced this to `--reload` being
  architecturally redundant (`ao-self-pull.sh` already does an explicit, more-complete `systemctl restart` on every
  code-changing pull) and shipped its removal (`agent-orchestrator@ee98ccb`), also fixing the excess restart-cadence
  root cause behind two OTHER previously-fixed bugs in this same repo. Full QG green, shipped via quickmerge. Could NOT
  apply the fix to the LIVE deployed systemd unit myself (`NoNewPrivileges=yes` blocks `sudo` from this sandboxed
  session) — filed a `[OPERATOR]` todo for that + a `[REVIEW]` todo to verify post-deploy that the hang actually stops.
- **2026-07-30 (slot-15, `review` craft)**: dispatched the `[REVIEW]` `-005` todo. Re-confirmed directly on the
  orchestrator VM (ip-172-31-5-118) that the live `/etc/systemd/system/orchestrator.service` `ExecStart` still carries
  `--reload --reload-dir server` — the `[OPERATOR]` `-004` todo is genuinely undeployed, and this session hit the exact
  same `NoNewPrivileges=yes`/root-owned-file blocker the prior session (slot 16) already documented, so there was
  nothing new to confirm yet. Filed `BLK-eb2ee2ff`; main answered **B — park it**. Registered prerequisite
  `ao_orchestrator_reload_removed_live=false` via `POST /api/prerequisites/...`, hand-tuned the derived
  `ao_db_lock_storm_and_stuck_shutdown_outage-005` backlog.yaml entry (`priority: 999`, `priority_override: true`,
  `prereqs.prerequisites: [ao_orchestrator_reload_removed_live]`), and verified the park survived a live
  `POST /api/backlog/regen` tick (not just `/reload`, which doesn't exercise the historical revert path) — the entry
  still shows all three fields set after regen. `-005` will not re-dispatch until the condition flips `true`, which
  should happen once `-004` is applied + verified live.
- **2026-07-30 (slot-15, correction, same session)**: the park above initially prepended the "PARKED..." annotation
  INSIDE this todo's own bold lead-in text. That changed the checkbox's content fingerprint, so `skip-current-task` /
  the next regen tick treated it as remove-old-add-new: `-005` (with my priority/prereqs gate) vanished from
  `backlog.yaml` and a fresh, UN-gated `-006` appeared with the annotation text itself as its `title`/`brief` — silently
  defeating the park (any worker landing on `-006` would have hit the exact same wall again, undetected). **Fixed**:
  reverted this todo's checkbox text to its exact original wording (the annotation now lives ONLY in this Progress Log,
  which regen doesn't fingerprint) and re-applied the same `priority: 999` / `priority_override: true` /
  `prereqs.prerequisites: [ao_orchestrator_reload_removed_live]` gate to whatever id regen restores for this todo,
  verified to survive a fresh `POST /api/backlog/regen`; deleted the stray `-006` row. Lesson for future parks: annotate
  in the Progress Log or a note OUTSIDE the checkbox's own text, never inside the todo's own bold lead-in — editing that
  text is indistinguishable from editing the todo itself.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified (6 entries, unchanged) — all still resolve and cover the two remaining open
  todos (apply the live `--reload` removal + confirm via journalctl).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **2026-08-06 (`/plan-reconcile ao`, operator-flagged, interactive)** — **⚠️ ARCHIVAL NOTE: this doc now has 0 open
  `- [ ]` todos but MUST NOT be archived on that signal alone.** Both remaining todos closed this pass (the live
  `--reload` removal, verified by SSM; and its journalctl follow-up, verified across 26 restarts). That drops the
  checkbox count to zero, which makes this doc surface in `scripts/plan-hygiene/check_archive_candidates.sh` — but
  **Problem 1 of the two this doc tracks, the SQLite `database is locked` storm, is not closed by anything above.** The
  `--reload` work only ever addressed Problem 2 (the stuck shutdown / SIGKILL). The 2026-07-27 update in this doc
  records the storm as ONGOING and causing a real functional failure (143 `database is locked` occurrences in a
  32-minute window; the plan-reconciler's `POST /api/plan-health/dispatch` returning `500` and silently not retrying
  until the next day's fire).

  This is precisely the failure mode
  `/plans/archive/issues/archive_candidates_content_verification_backlog_2026_08_06.md` warns about — "a doc can have
  every listed `- [ ]` checked while its own summary/Progress Log still describes an open question" — and it is why that
  backlog requires a per-doc content read rather than a mechanical batch archive. **Before archiving**: confirm the
  lock-storm question is resolved (or re-opened as its own tracked todo/doc), not merely that the checkboxes are ticked.
  `status:` is deliberately left `open`.

- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries) — re-pointed away from the
  now-fully-shipped Problem 2 (`--reload` removal: dropped `agent-orchestrator-deploy.md`, `ao-self-pull.sh`,
  `install-orchestrator-service.sh`) toward the sole remaining open item, the Follow-ups DO-NOT-ARCHIVE guard's Problem
  1 (DB-lock storm): added `server/db.py` (`session_scope`, the mechanism at the heart of the contention) and
  `server/autospawn.py` (`ensure_review_agents`, the already-fixed reference pattern a future fix should mirror); kept
  `tmux_pruner.py` (the confirmed second instance of the same anti-pattern) and both the original fix's archived issue
  doc and the background-loop architecture codex.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. Sole open item (Follow-ups: DB-lock-storm root-cause, DO-NOT-ARCHIVE guard) remains a genuine,
  still-unresolved live-incident investigation ("genuine SECOND undiagnosed bug, or genuine extreme concurrent-write
  contention" — not yet distinguished per the doc's own open question).

- **2026-08-08 (slot-10, `[REVIEW]` bookkeeping dispatch, `ao_satellite_ao_dispatch_batch5-002`)**: Dispatched to flip
  the `[OPERATOR] P2` and `[REVIEW] P2` checkboxes and archive this doc, per the batch5 plan's todo 2 (drafted
  2026-08-03). Found both checkboxes already `[x]` — they were closed by other sessions on 2026-08-06, before this doc's
  own `/plan-reconcile ao` pass that same day added the DO-NOT-ARCHIVE guard below them (Problem 1, the SQLite lock
  storm, still open). The batch5 todo's archival instruction therefore predates and is superseded by this doc's own
  more-recent, explicit guard — **did not archive, did not set `status: resolved`**. Performed only the safe subset of
  the requested bookkeeping: added the operator-fix doc
  (`/plans/archive/issues/orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31.md`) and the
  backlog-park follow-up (`/plans/active/issues/backlog_park_lost_across_sibling_todo_insertion_2026_07_30.md`) to
  `related:` as the todo asked. No new investigation performed into Problem 1 (out of this bookkeeping-only dispatch's
  scope) — the Follow-ups guard and its `[AO] P0` todo stand as the reason this doc stays open and un-archived.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.

## Follow-ups

- [ ] [AO] P0. Resolve the SQLite 'database is locked' storm (Problem 1 — 143 locks in 32 min killing plan-reconciler
      runs) — DO-NOT-ARCHIVE guard: this live incident is not closed by the todos above.

> **2026-08-06 archive-candidate audit**: Explicit DO-NOT-ARCHIVE guard in the doc's own Progress Log (2026-08-06):
> 'this doc now has 0 open - [ ] todos but MUST NOT be archived on that signal alone... Problem 1... the SQLite database
> is locked storm, is not closed by anything above' — status deliberately left open. [KEEP_OPEN todo synthesized from
> justification by archive sweep]
