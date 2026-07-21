---
doc_type: codex-ssot
title: Agent Orchestrator — Worker Liveness Watchdog
summary:
  WorkerLivenessWatchdog — 60s daemon that KILLS tmux sessions invisible to AutoSpawn on 3 triggers (stuck-at-prompt
  180s / heartbeat-silent 900s / context-full immediate); usage-cap context-preserving failover; anti-thrash 5-min
  cooldown + 20/day cap; AutoSpawn respawns within 60s.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [orchestrator, self-healing, watchdog, slack, infrastructure]
related: [agent-orchestrator-autospawn.md, agent-orchestrator-overview.md]
created: 2026-06-01
authoritative_for: [agent-orchestrator worker-liveness watchdog]
referenced_by:
  [
    codex/04-architecture/agent-orchestrator-autospawn.md,
    codex/04-architecture/agent-orchestrator-overview.md,
    plans/audit/instructions/orchestrator_master_audit_instructions.md,
  ]
owner:
last_reviewed: 2026-07-21
code_refs:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/orphan_reap.py,
  ]
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

| Variable                                      | Code default | Notes / Purpose                                                                                                                 |
| --------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED`        | `false`      | **Systemd-deployed default: `true`** (drop-in at `/etc/systemd/system/orchestrator.service.d/watchdog.conf` on the central VM). |
| `ORCHESTRATOR_WATCHDOG_INTERVAL_SECONDS`      | `60`         | Tick cadence                                                                                                                    |
| `ORCHESTRATOR_WATCHDOG_STUCK_TICKS`           | `3`          | Consecutive frozen ticks before kill (3 × interval = 180s)                                                                      |
| `ORCHESTRATOR_WATCHDOG_HEARTBEAT_TIMEOUT`     | `900`        | Heartbeat-silent threshold (15 min)                                                                                             |
| `ORCHESTRATOR_WATCHDOG_KILL_COOLDOWN_SECONDS` | `300`        | Per-slot kill cooldown (5 min)                                                                                                  |
| `ORCHESTRATOR_WATCHDOG_DAILY_CAP`             | `20`         | Per-VM kills before dormancy                                                                                                    |

---

## Rollout procedure

Enable the flag on the central orchestrator VM (id `planning`) and watch the false-positive kill rate — abort if it
exceeds >5% (i.e., a legitimately-thinking worker gets killed):

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
curl -s http://localhost:8765/api/state | jq '.watchdog_enabled'

# 2. Leave a slot idle until stuck-at-prompt (or inject via tmux send-keys without C-m)
# 3. Wait ≤ 3 ticks (180s); confirm kill event in activity log
curl -s http://localhost:8765/api/activity?limit=5 | jq '.[] | select(.event_type=="watchdog_slot_killed")'

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

---

## One-off / scheduled completion contract — the finished-immortal failure mode (2026-07-21)

The three wedge modes above (stuck / silent / context-full) are all a worker that is STILL SUPPOSED to be working. There
is a **fourth** mode the watchdog was blind to: a `one_shot`/`scheduled` agent that has **finished** its work but never
dies.

**Symptom (measured 2026-07-21).** 15 finished typed agents (9 `cicd` one_shot + 6 `plan_health` scheduled) sat
`status=active` for up to 19 h, pinning 15/16 slots → the daily reconciler got `503 no free slot`. Their JSONLs show
none errored — each completed its task, then idle-polled forever. The role docs already say _"then EXIT, do NOT loop"_,
but **"EXIT" only ends the Claude _turn_**; the tmux session lingers at an idle `❯` prompt, `WorkerLivenessKicker`
re-nudges it, and it responds → idles → is nudged again (one agent logged its "179th poll").

**Why every cleanup path is blind.** The finish is NOT a session death, so:

- `has_session()==True` → `TmuxPruner` / `reap_orphan_agents` (session-death-gated) never fire;
- the mandated `/progress` heartbeat keeps `SlotRow.last_ping` fresh → the heartbeat-silent + working-stale reapers
  never fire (verified: a slot's `last_ping` stayed fresh while its bound AgentRow's froze at claim);
- the two idle-scanning reapers (`_reclaim_idle_lingering_sessions`, `_release_prereq_blocked_slots`) are
  carve-out-exempted for typed agents (`f641968` / `1e7fec0`, added 2026-07-20 to stop them reaping typed agents
  MID-work) — and because a one-off never `/done`s, the carve-out cannot tell _finished_ from _working_, so it protects
  finished ones forever.

**A finished one-off is therefore immortal** — it is archived only by a manual `tmux kill-session` (which the backend
then reaps `lifecycle-complete` in <45 s, proving the cleanup path is correct; it simply never receives the
session-death signal).

**The contract (LANDED 2026-07-21, `agent-orchestrator@0d510e9` →
[`ao_uniform_agent_liveness_contract`](../../plans/active/ao_uniform_agent_liveness_contract_2026_07_20.md)).** A
`one_shot`/`scheduled` agent, on completing, POSTs an explicit **role-aware `/done`** (task-less for a task-less one-off
— today's `/done` is task + plan-flip gated and must be extended to accept a task-less completion). The backend then (a)
archives the AgentRow `lifecycle-complete`, (b) frees the slot, (c) flags it so `WorkerLivenessKicker` stops nudging it.
The agent then stops; the next reap cleans the now-dead session. This makes "finished" an **explicit signal** instead of
an inference from a session death that never happens — and let the `f641968`/`1e7fec0` carve-outs be **DELETED** (done —
C1, `agent-orchestrator@0d510e9`; a booted one-off is `working`, never `idle`, so idle-scanners skip it by construction;
on `/done` it is archived, not reaped). Only `5907317` (the boot-gate `spawn_base_role` recognition) is kept — B1
depends on it, so it was not subsumed.

> **"One-off" here = an event-spawned CRAFT** (escalation/scheduled). A **plan-backlog worker is persistent** and DOES
> go `idle` when it has no ready task — the idle-reclaimer reaping it is then correct (a fresh worker picks up later
> work; durable state lives in the plan/Progress Log). See the next section, § "Dispatch-context-driven lifecycle".

---

## Dispatch-context-driven lifecycle — persistent plan-backlog workers vs event-spawned one-shots (2026-07-21)

> **SSOT for: which workers are reaped on `/done` and which persist.** The completion contract above answers "how does a
> _finished_ one-off die?"; this section answers "**which** workers are one-offs in the first place?" — and corrects a
> defect where plan-backlog workers were wrongly reaped after every task. **Implementation plan**:
> [`ao_worker_lifecycle_dispatch_context_2026_07_21`](../../plans/active/ao_worker_lifecycle_dispatch_context_2026_07_21.md).

### The principle — lifecycle is a property of the DISPATCH, not of the role

A worker's role (`backend_engineer`, `cicd`, `data_engineering`, …) is **just a boot prompt** — the same prompt can be
handed to a plan-backlog worker OR an event-spawned craft. So **the role's declared `lifecycle` field cannot decide
whether to reap a worker on `/done`.** The authoritative signal is **who fired the worker**:

| Dispatch context        | How it's fired                                                                                                                                                                                                                            | How the backend knows                                                                                                             | Lifecycle on `/done`                                                                                         |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Plan-backlog worker** | AutoSpawn dispatches a `backlog.yaml` task to a free slot (drains the backlog by `(tier, priority, plan_order)`/affinity)                                                                                                                 | **No** `one_shot`/`scheduled` `AgentRow` — a SlotRow-only worker (verified: the `agents` table is empty for plan-task dispatches) | **persistent** — drains ready tasks in one session; when none is ready, goes idle → the reclaimer retires it |
| **Event-spawned craft** | An escalation wall (`escalate()` → QG→`cicd`, pipeline→`data_pipeline_failure`, conflict→`conflict_resolver`) or a scheduled tick registers a bound `AgentRow` with `lifecycle` `one_shot`/`scheduled` (`escalation.py` register pattern) | **Yes** — a live `one_shot`/`scheduled` `AgentRow` owns the session                                                               | **one-shot** — reap on `/done`; its whole life is that one job                                               |

### The defect this corrects (2026-07-21, live)

The reap-on-done gate keyed on **`role_one_shot OR agent_one_shot`**, where `role_one_shot` read the **static role
field** (`role_registry.get_role(assigned_role).is_one_shot`). Four plan-worker roles were declared `one_shot`
(`backend_engineer`, `ui_developer`, `quant_dev`, `infra`), so a plan-backlog worker was reaped **after every task** —
"a fresh-context session per task." Observed: one plan's tasks sprayed across slots (cost_per_day tasks ran on slots 3
_and_ 4), and slots churned spawn→task→reap→respawn every few minutes. Each task completed + verified (no work lost),
but the churn is pure waste and defeats intra-plan context.

**The fix: the reap-on-done gate drops `role_one_shot` and keys only on the dispatch context** (`agent_one_shot` — the
event-spawned `AgentRow`) plus the plan-worker retire condition below. Robust even when a role's field is wrong — which
is why role-field reclassification is **deliberately deferred** (roles are boot prompts; a later pass may align the
fields, but reaping no longer depends on them).

### The lifecycle (plan-backlog worker, at `/done`)

The plan model (per `task_template.md` §4): a plan's independent same-priority todos dispatch **concurrently to any free
slot** (`regen` sets no affinity; `_task_is_routable_to` → any free slot); `sequential: true` serialises a whole plan;
prereqs come only from `sequential`/`depends_on`+`gate_on_depends`, enforced by `dispatch.py::_prereqs_met`. Against
that, a worker **persistently drains the backlog** (any routable task):

| #                           | Situation at `/done`                                                                                    | Action                                                                                                                                                                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **1 — next task ready**     | `pick_next_task` returns a task for this slot                                                           | Hand it over — the **same live session drains it**. No reap. This is the win over the old per-task reap: consecutive ready tasks (e.g. a `sequential` plan's chain, each ready as its predecessor `/done`s) run in ONE session.      |
| **2 — no ready task**       | Nothing dispatchable to this slot now (backlog drained, OR the only remaining tasks are prereq-blocked) | Worker goes **idle** → the idle-reclaimer reaps its session (`~watchdog_idle_session_ticks` ticks, default 2×60s) → the slot retires. AutoSpawn respawns a **fresh** worker when a blocked task later clears (it re-reads the plan). |
| **3 — event-spawned craft** | The session owns a `one_shot`/`scheduled` `AgentRow`                                                    | Reap on `/done`, always (the completion contract above).                                                                                                                                                                             |

The reaper reaping an idle plan-worker (case 2) is what makes "retire when the work is done" true without a per-`/done`
kill — a finished-plan worker simply stops getting tasks, goes idle, and is reaped ~2 min later; it never idle-loops
forever (the finished-immortal bug), and it never churns per task (the reap-per-task defect).

### Conversational context-resume is an explicit NON-GOAL (operator ruling 2026-07-21)

We deliberately do **not** carry a plan-worker's Claude conversation across an idle/retire boundary — no
`--resume`-with-context, no session-per-plan binding, no `target_slot` pinning of a plan to a slot. **Durable state
lives in the plan items + Progress Log** (the operator-facing SSOT a worker writes as it goes) and in the shipped
commits; a fresh worker re-reads those and continues correctly. Conversational memory is a nice-to-have efficiency, not
a correctness requirement — losing it re-reads a plan, it does not lose work. (The dead-worker `--resume` for a MID-task
crash — `resume_lifecycle.py`, `ao_task_lifecycle` Phase B — is a different mechanism and stays.)

### Interaction with the C1 carve-out deletion — still correct

The finished-immortal contract deleted the idle-scanner carve-outs (`f641968`/`1e7fec0`, C1) on the premise that every
idle-lingering session was a finished one-off to reap. Under this model a plan-backlog worker **legitimately goes idle**
when it has no ready task (case 2) — and the idle-reclaimer reaping it is **exactly right**: it frees the slot, and a
fresh worker picks up later work. So: **crafts** stay `working` until `/done` (never idle → carve-out unneeded);
**plan-backlog workers** may go idle → reaped → a fresh worker respawns on new work. No carve-out is re-introduced.

### Deferred (revisit later, not required for correctness)

- **Role-field reclassification** (`backend_engineer`/`ui_developer`/`quant_dev`/`infra` `one_shot → persistent`;
  `data_engineering` scheduled-vs-persistent). Reaping keys on dispatch context, not the field, so this is cosmetic.
- **Sequential-plan context-continuity** (pin a `sequential` plan to one slot for conversational continuity across a
  cross-plan gate). A nice-to-have only — the durable state above already carries what matters. Explicitly out of scope.

---

## Orphaned singleton-agent process — the two-mains-on-the-dashboard failure mode (2026-07-21)

`KillMode=process` (deliberate — workers survive a backend redeploy) means a `systemctl restart` kills only uvicorn; a
main's `claude` process keeps running. If that main's tmux server has meanwhile lost the default socket (a fresh server
took `/tmp/tmux-<uid>/default`; the old server is left alive but socketless, invisible to `tmux ls`), the keeper's
`has_session("orch-agent-main")` reads False → it reaps the record and spawns a **replacement** main beside the
still-running orphan. `kill_session` can never reach the orphan (it only talks to the current socket). The orphan keeps
`/poll`-ing, and `update_agent_ping`'s **restore-on-ping** flips its archived row back to `active` every tick → **two
mains on the dashboard + a second account burning** (incident 2026-07-21;
`plans/active/issues/ao_orphaned_main_duplicate_2026_07_21.md`).

Two closures (`agent-orchestrator@4f34391`):

- **Process-level reap** — `orphan_reap.reap_orphan_agent_session(<singleton session>)` SIGTERMs any `claude` whose
  `CLAUDE_CONFIG_DIR` is that session's config dir but which is NOT the live-pane occupant
  (`pid_belongs_to_live_session`), anchored on a live session so a transient tmux hiccup can't misfire, honouring
  `boot_grace_seconds`. Always-live (a singleton has exactly one legit occupant). Wired into `AgentKeeper.tick_once` for
  `main`; review is a residual todo in the issue doc.
- **Restore-on-ping guard** — `update_agent_ping` never resurrects a `main` that has a newer-registered sibling
  (definitionally superseded). The old comment's claim that "a superseded main can't resurrect itself — it isn't
  pinging" is false when the process leaks; the newest-registered main is the singleton, everywhere.

**Invariant:** the live occupant of a singleton agent session is identified per-PID (config-dir + pane-tree membership),
never by `has_session` name alone or by `last_ping` recency (which flaps between an orphan and the real main).

---

## Self-healing hardening (2026-06-21 — `orchestrator_self_healing_hardening_2026_06_21`)

Five robustness closures (all in `agent-orchestrator`, tested) for the operator's "always pick accounts with usage left,
rotate inline when they run out, re-trigger anything dirty / rolled-back / stale":

- **Deterministic rotation-failure recovery** — `server.server._recover_slot_after_failed_rotation`: when
  `spawn_with_account_bg` fails AFTER the old session is killed, the slot was left half-dead (`working` + dead
  `tmux_session` + bound `current_task`), relying on a later `TmuxPruner` grace-tick. It now immediately releases the
  task to the queue (never stranded `dispatched`) + flips the slot `killed` for an AutoSpawn re-pick on a fresh account;
  `paused` is preserved (operator intent).
- **`stale`-lingering reclaim** — `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` now reaps `stale` (not only
  `idle`) lingering live sessions, with an `_is_actively_thinking` pane guard. A finished/wedged worker the
  HealthMonitor flipped idle→`stale` no longer occupies its slot until the 15-min heartbeat-silent kill; queued work
  resumes in ~`_IDLE_SESSION_RECLAIM_TICKS`.
- **Provably-dead branch-quarantine auto-heal** — `worktree_clean_check.heal_dead_slot_branch_quarantine`, called from
  `_do_spawn` when the FM5/FM7 branch gate would quarantine. For a provably-DEAD slot only (never stomps a live peer),
  it PRESERVES every commit not on `origin/<base>` to a durable `origin/wip-preserve/...` ref FIRST (refuses to realign
  if the preserve push fails), then realigns HEAD to `origin/<base>` via `git checkout -B` — so a diverged/wrong-branch/
  detached dead slot recovers instead of wedging `killed` forever. This is also the recurring "Spawn failure — branch
  quarantine" recovery; the escalate worker's leftover `_escalation_work` branch is now ALSO prevented at the source by
  `agents/escalate.md`'s mandatory leave-the-slot-clean step before EXIT.
- **Orphan-wip realign via `checkout`, not `reset`** — `worktree_clean_check/_orphan.py` realigns an inherited
  dead-predecessor WIP slot with `git checkout -B <base> origin/<base>` instead of `git reset --hard origin/<base>`. The
  reset emitted the `reset: moving to origin/<base>` reflog signature the audit-reflog guard pages on, so every WIP
  inherit re-armed "Audit Reflog — High Risk" even though the WIP was preserved — the chronic central-VM ~11-min spam. A
  checkout reaches the same clean end-state with a `checkout:` reflog the audit ignores: the spam is fixed at SOURCE.
- **`LoopSupervisor`** (`server/loop_supervisor.py`) — checks every background daemon loop's thread liveness every 120s
  and revives a dead one via its idempotent `start()` (no-op when alive, recreates the thread when dead). A crashed
  `WorkerLivenessWatchdog`/`AutoSpawnLoop`/`TmuxPruner`/`HealthMonitor`/`UsagePoller`/etc no longer silently stops the
  fleet self-healing without a full backend restart; only the supervisor itself (root) needs a process restart.
  Env-disabled loops are not registered.

Account-selection closures (same plan): a **late-binding account re-check** in `_do_spawn` (refuse to spawn onto an
account that went unusable in the pick→spawn window; next tick re-picks) + a **load-spread tiebreaker** in
`_pick_headroom_account` (active-slot-count as the 3rd sort key after 5h%/weekly%). SSOT:
`plans/active/orchestrator_consolidated_remaining_2026_06_25.md`.

## Account auth-failure eviction + outage-safe detection (2026-06-22)

When an account is disabled (org turns off Claude Code, or its OAuth token is rejected) the orchestrator must stop using
it for NEW spawns AND divert the agents already running on it — without ever mistaking a transient Claude-backend outage
for an account fault.

**Design invariant — "account-bad" is a POLLER verdict, never a heartbeat inference.** The `usage_poller` is the sole
authority on account health: it probes `/usage` per account per tick and CLASSIFIES the failure — HTTP **401/403 →
`mark_account_auth_failed`** (token rejected/disabled); **429 → `mark_account_rate_limited`**; **5xx / network / timeout
→ nothing** ("transient; do NOT auth-alert"). A missing `/heartbeat` is NEVER treated as an auth fault. This is the
operator caveat (2026-06-22): Claude's servers have outages, and a good account must not be sidelined on a blip — it is
reused automatically once the servers recover.

Flow:

- **Detection (poller):** on a classified 401/403, `_mark_auth_failed_db` persists `account_status='auth_failed'` THEN
  fans out the eviction via `_evict_slots_on_auth_failed` →
  `rotate_all_slots_off_account(account_id, trigger="poller-auth-failed", reason=RotationReason.auth_failed)`. Re-marked
  each tick the token stays bad; cleared instantly by the next successful probe (`_clear_auth_failed_db`) or a worker
  heartbeat (`slots_worker` healing path).
- **Worker eviction:** `rotate_all_slots_off_account` (now `reason`-parametrized; default `rate_limit` for the cap
  callers) diverts every running slot bound to the account onto the next usable one (`spawn_with_account_bg`). Its
  **global-outage guard is built in**: `pick_next_account is None` → logs `account_rotation_no_fallback`, does NOT kill.
  No-op once the slots have moved off, so it is safe to call on every re-mark.
- **Main-agent eviction:** `main_agent_keeper._handle_auth_failed_account` (runs each tick BEFORE the usage-cap modal
  check — auth failure is more fundamental) fails the main agent over off a poller-confirmed auth_failed account: kill +
  `--resume` on a usable account when a `claude_session_id` is stored (context intact) / kill-for-fresh when not / leave
  in place when no usable account exists. The resumed main uses an empty boot prompt + nudge (no re-registration), so
  the keeper **re-points the main `AgentRow.account_id` to the new account** to stop the auth check re-firing next tick.
- **Spawn-heartbeat watchdog hardened:** `_auth_failover.check_spawn_heartbeat_timeouts` NO LONGER marks an account
  auth_failed on a bare spawn timeout. It DEFERS to the poller's eviction when the account is already poller-confirmed
  auth_failed, otherwise RETRIES the spawn on the SAME account (transient spawn failure: slow start / worktree / OOM),
  bounded by `spawn_retry_count`. This removes the false-fail-during-outage class.
- **Auto-recovery:** an auth_failed account is held out of the pool only for an exponential cooldown
  (`AUTH_FAILED_COOLDOWN_BASE_SECONDS=600` → 6h cap), re-probed after, and cleared on the next success — so a recovered
  account rejoins the pool with no human action.
- **All-accounts-down page:** `_fire_all_accounts_down_if_needed` + `all_accounts_unusable` fire one Slack page when
  every account is MARKED unusable (rate-limited / auth-failed / disabled).
- **Likely-Claude-outage page:** a purely transient fleet-wide outage (all `/usage` probes timing out / 5xx in a tick,
  none classified 401/403/429) leaves accounts healthy-status, so the all-accounts-down page above can't fire. The
  poller tallies per-tick reachability (`n_probed` / `n_success` / `n_transient_fail`) and `_check_likely_outage` fires
  a distinct disk-deduped `notify_likely_claude_outage` page on the clean all-transient signature
  (`n_probed > 0 and n_success == 0 and n_transient_fail == n_probed`), re-arming on the next successful probe. A mixed
  tick (some 401/403 + some transient) neither fires nor re-arms. NO account is marked (a transient outage is not an
  account fault); agents auto-resume — it is an awareness page, not an action item unless it persists. Routes to Slack
  #agent-orchestrator-alerts with an `/accounts` deep-link (sibling of `notify_all_accounts_unusable`).

SSOT: `plans/active/orchestrator_consolidated_remaining_2026_06_25.md` § "Operator follow-up (2026-06-22)".
