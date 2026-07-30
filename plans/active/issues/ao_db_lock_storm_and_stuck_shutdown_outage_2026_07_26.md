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
last_updated: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
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
- [ ] [OPERATOR] P2. **Apply `agent-orchestrator@ee98ccb`'s `--reload` removal to the LIVE deployed
      `/etc/systemd/system/orchestrator.service`** on this VM — re-run `install-orchestrator-service.sh` (or manually
      remove `--reload --reload-dir server` from the `ExecStart` line), then
      `sudo systemctl daemon-reload && sudo     systemctl restart orchestrator`. Safe per `KillMode=process` (kills only
      the uvicorn main PID; tmux/claude worker sessions in the cgroup survive, confirmed in this doc's Progress Log). No
      worker has privileged access to do this from a sandboxed slot session (`NoNewPrivileges=yes`). (repo:
      agent-orchestrator, infra action)
- [ ] [REVIEW] P2. **PARKED 2026-07-30 (slot-15) — gated on prerequisite `ao_orchestrator_reload_removed_live=false`
      (backlog.yaml: `priority: 999`, `priority_override: true`,
      `prereqs.prerequisites: [ao_orchestrator_reload_removed_live]`; survived a live `/api/backlog/regen` tick).**
      Verified directly on the orchestrator VM (ip-172-31-5-118): the live `/etc/systemd/system/orchestrator.service`
      `ExecStart` still carries `--reload --reload-dir server` — the `[OPERATOR]` todo above (`-004`) is genuinely
      undeployed, and no worker can apply it (root-owned unit file, `sudo` blocked by `NoNewPrivileges=yes`). Do NOT
      retry this todo until `ao_orchestrator_reload_removed_live` flips `true` (flip it via
      `POST /api/prerequisites/ao_orchestrator_reload_removed_live {"value": true}` once `-004` is applied + verified
      live, then this todo re-dispatches automatically). Once unparked: **Once the live unit is updated (prior todo),
      confirm via `journalctl` that the `"Started reloader process"` / `"Stopping reloader process"` log lines stop
      appearing on future restarts** (proves `--reload` is actually off in the running process, not just the repo), then
      watch the next several `ao-self-pull.sh`-triggered or explicit restarts for the previously-observed
      `"State 'stop-sigterm' timed out.     Killing."` pattern — if it stops recurring across several restarts, close
      this issue with that evidence; if it still recurs even without the reload-supervisor layer, the root cause is
      elsewhere (do not re-guess — the resource_tracker/spawn-context teardown lead in the `[BACKEND]` todo above
      becomes the next thing to check directly, e.g. via `py-spy dump` on a hung process before SIGKILL fires). (repo:
      agent-orchestrator)

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
