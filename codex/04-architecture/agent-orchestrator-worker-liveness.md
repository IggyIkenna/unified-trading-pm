---
scope: [engineer, admin]
last_reviewed: 2026-06-01
status: final
---

# Agent Orchestrator — Worker Liveness Watchdog

> **SSOT**: `agent-orchestrator/server/worker_liveness_watchdog.py` **Plan**:
> `plans/active/agent_orchestrator_worker_liveness_watchdog_2026_06_01.md` **Related**:
> `codex/04-architecture/agent-orchestrator-autospawn.md` § "Failure modes" **Composes with**: `WorkerLivenessKicker`
> (`server/worker_liveness.py`) — kicker nudges; watchdog kills

## Problem statement

With AutoSpawnLoop + prune-stale + failover all live, the fleet **still goes silent for hours at a time**. Three failure
modes are invisible to the existing recovery stack because all three look identical to `AutoSpawnLoop`: tmux session
alive, accounts healthy, slot configured → `worker_active` gate skips respawn.

Observed pattern (2026-05-30 / 2026-06-01 operator kill cycles):

| Failure mode            | Observable symptom                                                                                                                                      | Why existing recovery misses it                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **Stuck-at-prompt**     | tmux pane shows `❯ pick up the next task` (or similar) typed by worker but never submitted; pane content frozen                                         | `tmux has-session` = True → AutoSpawnLoop `worker_active` skip |
| **Heartbeat-silent**    | Claude session alive, executing nothing, no `/heartbeat` ping in >30 min, task claimed but worker dropped; `slots_working=0` but `dispatched_to=<slot>` | Same: tmux alive → `worker_active` skip                        |
| **Context-window full** | Pane shows `new task? /clear to save 119.9k tokens`; Claude refuses further work until operator clears manually                                         | Same: tmux alive → `worker_active` skip                        |

Two manual kill bursts (09:48Z May 31 + 22:14Z May 31) restored velocity for ~1 hour each before refilling with wedged
workers — confirming that **kill → AutoSpawnLoop respawn** is the correct recovery path, and the missing piece is
automated kill detection.

---

## WorkerLivenessWatchdog design

`WorkerLivenessWatchdog` is a daemon thread that ticks every 60 s, scans all slots, and **kills** the tmux session when
any of three trigger contracts fire. AutoSpawnLoop then respawns within the next 60 s tick.

This is distinct from `WorkerLivenessKicker` (which **nudges** via keystroke injection and only kills as a last resort
after a failed kick + stuck threshold). The watchdog layer operates on independent thresholds and kills directly — the
two components compose:

```
WorkerLivenessKicker  →  nudge (frozen/idle) → auto-respawn if kick fails + stuck >15min
WorkerLivenessWatchdog → kill directly on context-full (immediate) / stuck-at-prompt (180s) / heartbeat-silent (900s)
```

---

## Trigger contracts (closed set)

A tmux session is **killed** when ANY of the following fires:

| Pattern              | Detection signal                                                                                                    | Threshold                                    | False-positive guard                                                                                                                                                       |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Stuck-at-prompt**  | `capture_pane(session)` shows non-empty text after `❯ ` prompt AND pane content unchanged between consecutive ticks | N=3 ticks at 60s = **180s** of no pane delta | Skip if pane content matches `Crunched for\|Cogitated for\|Worked for\|Baked for` (legitimate thinking); also skip if `WorkerLivenessKicker` kicked within debounce window |
| **Heartbeat-silent** | `slot.last_heartbeat_at` older than threshold AND `tmux has-session = True` AND `slot.status != 'blocked'`          | **>900s** (15 min)                           | Skip if `slot.status == 'blocked'` — worker is legitimately polling `/messages` for operator answer                                                                        |
| **Context-full**     | Pane content matches regex `/clear to save .{1,10}k tokens/i`                                                       | **Immediate** (1 tick)                       | Per-slot daily cap of 3 kills (Slack alert if exceeded — operator-actionable)                                                                                              |

### Pane-content regex anchors

```python
# Allow-list: actively-thinking pane (do NOT kill)
_THINKING_RE = re.compile(
    r"Crunched for|Cogitated for|Worked for|Baked for",
    re.IGNORECASE,
)

# Context-full kill trigger
_CONTEXT_FULL_RE = re.compile(r"/clear to save .{1,10}k tokens", re.IGNORECASE)

# Stuck-at-prompt detection: prompt has non-empty text
_PROMPT_NONEMPTY_RE = re.compile(r"^\s*❯\s+\S", re.MULTILINE)  # noqa: RUF001
```

### Tick-to-tick pane comparison (stuck-at-prompt)

The watchdog maintains `_prev_panes: dict[int, str]` (slot_id → last captured pane) and `_stuck_ticks: dict[int, int]`.
On each tick:

1. Capture current pane (`capture_pane(session, history_lines=30)`).
2. If pane has non-empty text after `❯` AND pane == `_prev_panes[slot_id]` → increment `_stuck_ticks[slot_id]`.
3. If `_stuck_ticks[slot_id] >= 3` AND pane does NOT match `_ACTIVELY_THINKING_RE` → kill.
4. On any pane change (content differs from prev) → reset `_stuck_ticks.pop(slot_id, None)`.

---

## Anti-thrash gates

These prevent a misconfigured or flapping watchdog from kill-looping a slot:

| Gate                   | Threshold                                       | Reset                            |
| ---------------------- | ----------------------------------------------- | -------------------------------- |
| Per-slot kill cooldown | 5 min between kills on the same slot            | Auto-reset after cooldown window |
| Per-VM daily cap       | 20 kills total across all slots before dormancy | UTC midnight reset               |

On daily-cap hit: Slack alert fires + watchdog goes dormant on that VM until manual operator reset (forces operator to
investigate root cause rather than mask it with repeated auto-recovery).

State is in-memory (`_last_kill_at: dict[int, datetime]`, `_kills_today: int`) — lost on orchestrator restart, which is
intentional (fresh state = conservative on restart day).

---

## Kill execution

```python
def _kill_slot(self, slot_id: int, tmux_session: str, reason: str) -> None:
    """Kill tmux session + log event. AutoSpawnLoop respawns on next tick."""
    kill_session(tmux_session)
    slot_row.status = "killed"  # set in DB before respawn fires
    log_activity(db, "watchdog_slot_killed", slot_id=slot_id,
                 details={"reason": reason, "session": tmux_session,
                          "kills_today": self._kills_today, "cap": _DAILY_KILL_CAP})
    # Slack alert: fires for context_full kills or on daily-cap hit
    if reason == "context_full" or self._kills_today >= _DAILY_KILL_CAP:
        slack_notify.notify_watchdog_kill(slot_id, reason, self._kills_today, _DAILY_KILL_CAP)
```

No WIP commit happens at kill time — unlike `WorkerLivenessKicker`'s auto-respawn path (which runs
`worktree_clean_check.commit_and_push_dirty_repos` before kill). Rationale: the watchdog's three patterns are detectable
early enough that the worker has not necessarily produced dirty WIP. If WIP is present, the operator sees an
`orphan-wip` commit on the slot branch (produced by any subsequent respawn + re-kill cycle via `WorkerLivenessKicker`'s
Phase 3A path).

---

## Interaction with AutoSpawnLoop

```
[Watchdog tick] → kill_session(session)
     ↓
[TmuxPruner tick, next ~30s] → marks slot tmux_alive=False
     ↓
[AutoSpawnLoop tick, next ~60s] → gate 2 "no active worker" passes → _do_spawn()
     ↓
Fresh worker /boot → claims next queued task
```

Expected end-to-end time from kill to fresh-worker-with-task: **60–180 s**.

The watchdog sets `SlotRow.status = "killed"` before AutoSpawnLoop fires, so the prune-stale guard doesn't reclaim the
task during the respawn window. Slot state then transitions to `idle` → `dispatched` on the next AutoSpawnLoop +
dispatch cycle.

---

## Slack alert paths

| Event                   | Alert                                                                                                | Severity                        |
| ----------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------- |
| Context-full kill fires | `notify_watchdog_kill(slot_id, "context_full", kills_today, cap)` — immediate Slack DM to operator   | P0 — always operator-actionable |
| Per-VM daily cap hit    | `notify_watchdog_kill(slot_id, reason, kills_today, cap)` — watchdog goes dormant until UTC midnight | P0 — runaway loop signal        |

Slack alerts use the same channel + format as `notify_autospawn_flap` and `notify_account_rotated`. No new Slack
infrastructure required.

---

## Environment variables

| Variable                                      | Default | Purpose                                                    |
| --------------------------------------------- | ------- | ---------------------------------------------------------- |
| `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED`        | `false` | Master on/off — must be `true` to enable                   |
| `ORCHESTRATOR_WATCHDOG_INTERVAL_SECONDS`      | `60`    | Tick cadence                                               |
| `ORCHESTRATOR_WATCHDOG_STUCK_TICKS`           | `3`     | Consecutive frozen ticks before kill (3 × interval = 180s) |
| `ORCHESTRATOR_WATCHDOG_HEARTBEAT_TIMEOUT`     | `900`   | Heartbeat-silent threshold (15 min)                        |
| `ORCHESTRATOR_WATCHDOG_KILL_COOLDOWN_SECONDS` | `300`   | Per-slot kill cooldown (5 min)                             |
| `ORCHESTRATOR_WATCHDOG_DAILY_CAP`             | `20`    | Per-VM kills before dormancy                               |

---

## Rollout procedure

Roll the flag **sequentially** (canary on vm-orchestrator first; abort if false-positive kill rate is >5% — i.e., a
legitimately-thinking worker gets killed):

```ini
# /etc/systemd/system/orchestrator.service.d/watchdog.conf
[Service]
Environment=ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true
```

Script: `unified-trading-pm/scripts/orchestrator/enable_worker_watchdog.sh`

Fleet rollout: sequential, same canary-abort discipline as `enable_autospawn.sh`. Document each VM's enable-time + first
legitimate kill in `plans/active/agent_orchestrator_worker_liveness_watchdog_2026_06_01.md`.

---

## Verification

End-to-end test (Phase 3 verification item):

```bash
# 1. Confirm watchdog is enabled on target VM
curl -s http://localhost:8026/api/state | jq '.watchdog_enabled'

# 2. Leave a slot idle until stuck-at-prompt (or inject via tmux send-keys without C-m)
# 3. Wait ≤ 3 ticks (180s); confirm kill event in activity log
curl -s http://localhost:8026/api/activity?limit=5 | jq '.[] | select(.event_type=="watchdog_slot_killed")'

# 4. Confirm AutoSpawnLoop respawns within 60–120s of kill
sleep 120 && tmux ls | grep orch-slot-<N>
```

Expected: kill event within 180s, fresh tmux session within 300s total.

---

## Anti-patterns (explicitly forbidden)

- **Do NOT kill a worker whose status is `blocked`** — they are legitimately polling `/messages` for operator answer.
  The `failover_origin` / `blocked_id` audit trail must be preserved.
- **Do NOT kill during `Crunched for / Cogitated for / Worked for / Baked for` pane state** — Claude is actively
  thinking and will produce real output. The allow-list regex must match these phrases verbatim (case-insensitive).
- **Do NOT roll Phase 3 in parallel across all VMs** — canary-first, same discipline as autospawn.
- **Do NOT bypass the per-slot 5-min cooldown** — without it, a misconfigured watchdog could kill+respawn the same slot
  every 60s indefinitely.
- **Do NOT bypass the per-VM 20-kills-per-day cap** — at cap, Slack alert fires + watchdog goes dormant; operator must
  investigate root cause, not mask it.

---

## Relationship to related systems

| System                                       | Layer                                  | Interaction                                                                                                                               |
| -------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `WorkerLivenessKicker`                       | Slot-level nudge (keystroke injection) | Kicks first; watchdog kills. Different thresholds, composable.                                                                            |
| `AutoSpawnLoop`                              | Cold-start + respawn after kill        | Respawns within 60s of kill. Together they close the warm-recovery loop.                                                                  |
| `harsh_pc_dispatch_failover`                 | Host-level offline detection (>10 min) | Different granularity: this plan handles slot-level liveness (180s–15min). Both required for full self-healing.                           |
| `agent_orchestrator_backlog_state_alignment` | Prune-stale / zombie cleanup           | Ensures workers always have honest queue state to `/boot` against; without it, watchdog would respawn workers into zombie-task purgatory. |
