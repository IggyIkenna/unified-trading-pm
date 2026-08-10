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
related: [/codex/04-architecture/agent-orchestrator-autospawn.md, /codex/04-architecture/agent-orchestrator-overview.md]
created: 2026-06-01
authoritative_for: [agent-orchestrator worker-liveness watchdog]
referenced_by:
  [
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    plans/audit/instructions/orchestrator_master_audit_instructions.md,
  ]
owner:
last_reviewed: 2026-08-09
code_refs:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/tmux_pruner.py,
    agent-orchestrator/server/orphan_reap.py,
    agent-orchestrator/server/context_probe.py,
    agent-orchestrator/server/context_lifecycle.py,
  ]
---

# Agent Orchestrator — Worker Liveness Watchdog

> **SSOT**: `agent-orchestrator/server/worker_liveness_watchdog.py` **Plan**:
> `plans/active/agent_orchestrator_worker_liveness_watchdog_2026_06_01.md` **Related**:
> `/codex/04-architecture/agent-orchestrator-autospawn.md` § "Failure modes" **Composes with**: `WorkerLivenessKicker`
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

| Pattern                                                         | Detection signal                                                                                                                                                                                                                                                                                                                                  | Threshold                                                                                                                                                                                                                                                                                                      | False-positive guard                                                                                                                                                       |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Stuck-at-prompt**                                             | `capture_pane(session)` shows non-empty text after `❯ ` prompt AND pane content unchanged between consecutive ticks                                                                                                                                                                                                                               | N=3 ticks at 60s = **180s** of no pane delta                                                                                                                                                                                                                                                                   | Skip if pane content matches `Crunched for\|Cogitated for\|Worked for\|Baked for` (legitimate thinking); also skip if `WorkerLivenessKicker` kicked within debounce window |
| **Heartbeat-silent**                                            | `slot.last_heartbeat_at` older than threshold AND `tmux has-session = True` AND `slot.status != 'blocked'`                                                                                                                                                                                                                                        | **>900s** (15 min)                                                                                                                                                                                                                                                                                             | Skip if `slot.status == 'blocked'` — worker is legitimately polling `/messages` for operator answer                                                                        |
| **Context-full**                                                | Pane content matches regex `/clear to save .{1,10}k tokens/i`                                                                                                                                                                                                                                                                                     | **Immediate** (1 tick)                                                                                                                                                                                                                                                                                         | Per-slot daily cap of 3 kills (Slack alert if exceeded — operator-actionable)                                                                                              |
| **Context-burn** (`ao_worker_context_lifecycle_gap_2026_07_25`) | `context_pct >= context_burn_min_pct` (default 80) OR `compactions_total >= context_burn_min_compactions` (default 3), combined with `hours_since_session_reset >= context_burn_hours` (default 4.0) — anchored on whichever of `last_spawned_at`/`last_compacted_at` is MORE RECENT, so a task reassignment alone can no longer reset this clock | Flags `context_burn_suspected`; the actual **kill** additionally requires `context_pct >= context_burn_kill_min_pct` (default 98) AND a grace window — a compact `directive` was already issued to this slot AND `context_directive_grace_reports >= 2` consecutive no-drop `/progress`\|`/done` reports since | `context_burn_kill` config flag (default **True** as of 2026-07-25, operator-approved) — a saturated session already declined ≥2 chances to compact before this fires      |

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
| Per-VM daily cap       | 50 kills total across all slots before dormancy | UTC midnight reset               |

On daily-cap hit: Slack alert fires + the 5 live NEW-kill triggers go dormant on that VM until UTC midnight (forces
operator investigation of root cause rather than masking it with repeated auto-kill). **Cleanup/reconcile mechanisms are
NOT gated by the cap** (`agent-orchestrator@bc37d03`/`53492cb`, 2026-08-06/08 — `_tick_once()`'s reorder moved
orphan-session reclaim + the other sweep/reconcile calls ahead of the cap early-return, since they clean up already-dead
work rather than making a new kill decision): `_sweep_dirty_slots`, `_sweep_unpushed_slots`, orphan-session reclaim,
`_reclaim_idle_lingering_sessions`, `_release_prereq_blocked_slots`, `_reclaim_orphaned_dispatched_tasks`,
`_reclaim_stale_resume_pending_dispatches`, and `_reconcile_unacked_dispatches` all keep running on a cap-hit day — only
the 5 live kill triggers themselves (and `WorkerLivenessKicker`'s separate nudge layer, which was never cap-gated) stop.

State is in-memory (`_last_kill_at: dict[int, datetime]`, `_kills_today: int`) — lost on orchestrator restart, which is
intentional (fresh state = conservative on restart day).

---

## Kill execution

```python
def _kill_slot(self, slot_id: int, tmux_session: str, reason: str) -> None:
    """Kill tmux session + log event. AutoSpawnLoop respawns on next tick."""
    self._preserve_wip_before_kill(slot_id, tmux_session)  # stash, mode="stash" — never commit_and_push
    kill_session(tmux_session)
    slot_row.status = "killed"  # set in DB before respawn fires
    log_activity(db, "watchdog_slot_killed", slot_id=slot_id,
                 details={"reason": reason, "session": tmux_session,
                          "kills_today": self._kills_today, "cap": _DAILY_KILL_CAP})
    # Slack alert: fires for context_full kills or on daily-cap hit
    if reason == "context_full" or self._kills_today >= _DAILY_KILL_CAP:
        slack_notify.notify_watchdog_kill(slot_id, reason, self._kills_today, _DAILY_KILL_CAP)
```

**Updated (`ao_worker_context_lifecycle_gap_2026_07_25`, was: "no WIP commit happens at kill time").** Every
`_kill_slot` call, for EVERY trigger reason (not just context-burn), now runs `_preserve_wip_before_kill` — a
`worktree_clean_check.resolve_dirty_state(mode="stash", replacing_session=tmux_session, ...)` call — before
`kill_session` fires. `replacing_session` is required: at the instant this runs, the slot's OWN claim still shows a live
tmux session, so without it `classify_maker_liveness` sees a live peer and refuses to stash anything. Best-effort (any
failure here never blocks the kill); logs `slot_dirty_state_resolved` (`trigger: "watchdog_kill"`) when there was
something to stash. This closes the prior gap where a genuine uncommitted change sitting on a stuck/silent/context-full
slot was discarded outright by the kill.

**`kill_session` ALSO reaps the pane's entire descendant process tree, not just the tmux session (added
`ao_worker_lifecycle` 2026-07-10 Phase B, `server/tmux_spawn.py:_reap_pane_tree`, called from every `kill_session`
before the actual `tmux kill-session`).** tmux only SIGHUPs the pane's own process group — a worker's DELIBERATELY
detached background job (`nohup`/`disown`/`setsid`, or the harness's own `run_in_background` Bash) reparents to init and
would otherwise survive a plain session kill as an orphan. `_reap_pane_tree` walks ppid ancestry while the pane is still
alive (the last moment the soon-to-be orphans are enumerable), SIGTERMs every strict descendant, then SIGKILLs
0.5s-later survivors — deliberately, to close the 10-17-day orphan-monitor class. **Blast-radius implication for
long-running skills**: any heartbeat-silent watchdog kill (>900s/15min of no `/progress`/`/done`, the trigger #3 above)
does NOT just end the Claude session — it also kills any LEGITIMATELY-running backgrounded task the worker started (e.g.
a `/data-pipeline-check-*` driver launched via `run_in_background`), even though that background task was correctly
progressing and would have re-invoked the worker on its own completion. A worker whose turn is blocked on a long,
synchronous, multi-minute foreground wait (rather than truly backgrounding it AND continuing to `/progress` every ~10min
per the worker heartbeat HARD RULE) is exactly the scenario this reaps — confirmed root cause for
`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`'s ~19-minute reproduction.

---

## WorkerLivenessKicker — host-load-aware grace shield + hard-kill escalation (2026-07-29/30)

The nudge layer (`server/worker_liveness/__init__.py`, `WorkerLivenessKicker._tick_once`) fires `worker_kicked` on a
frozen/idle pane read. Under sustained host saturation, a single stale pane read can misclassify a worker that is
genuinely still progressing (OS scheduler delays pane I/O past the read) — resolved by operator ruling 2026-07-29 (fix
false-positive detection first, then escalation speed), per
`plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md`'s two sequenced todos:

- **Progress-marker grace shield** (`agent-orchestrator@64b5310`) —
  `_progress_marker_shields_kick(last_ping_ts, now, grace_seconds)` suppresses `worker_kicked` when `slot.last_ping`
  advanced within `kick_progress_grace_seconds` (config default **90s**), even when the pane read classifies
  frozen/idle. A worker demonstrably still progressing (recent heartbeat) is never kicked on a single bad pane sample.
- **Hard-kill escalation is unchanged and already correct** (`agent-orchestrator@77fc60a` — audit finding, no new
  mechanism needed): `kick_escalation_threshold` (default **3**) forces
  `_maybe_auto_respawn_stuck_slot(..., force=True)` — kills the wedged tmux session and resumes the in-flight task via
  `--resume` — once `_consecutive_kick_failures` reaches the threshold, gated on `genuinely_recovered` (pane verified
  'working'). With the grace shield now in place, a genuinely-wedged slot (no ping progress, beyond grace) still reaches
  N=3 at the same real-world cadence as the original incident spec (~5-6 min/kick × 3 ≈ 15-18 min) — no threshold/timing
  re-scope was warranted.

Composition regression coverage lives in `tests/test_worker_liveness.py`:
`test_pane_read_latency_with_advancing_progress_markers_produces_zero_kicks` (grace shield alone) and
`test_genuinely_wedged_slot_still_escalates_after_grace_fix` (grace shield + escalation together — a beyond-grace slot
still hits `force=True` at exactly `kick_escalation_threshold` kicks).

---

## `_typed_occupant_liveness` dispatch-ordering race (2026-07-30) — a DIFFERENT gap, same lookup function

A one-shot/typed escalation worker's mandated STEP-0 heartbeat could land in the window between `do_spawn()` returning
(the boot prompt is pasted, worker executing) and `escalation.escalate()`/`plan_health.dispatch()` opening the
`_register_agent`+`claim_slot_for_typed_agent` session — `do_spawn` runs deliberately OUTSIDE any DB session
(`orchestrator_spawn_reliability_db_lock_2026_06_10`, so the multi-second boot wait never holds the SQLite write lock).
In that window the slot looks fully unclaimed to `find_active_agent_for_session` (no AgentRow yet), so
`_typed_occupant_liveness` resolves `"stale"` and the heartbeat handler falls through to the ordinary
`pick_next_task`/`assign_task_to_slot` idle-dispatch path — silently binding a foreign Class-A backlog task to a slot
that is actually mid-dispatch of a typed one-shot occupant. **This is NOT the same gap as the `/done` 400 family above**
(an AgentRow that existed and was later archived out from under a live session) — here the row never existed yet at
lookup time; the two share `find_active_agent_for_session`'s query shape but not a root cause, so a single fix does not
close both. Fixed (`agent-orchestrator@3d993fb`): both dispatchers now pre-stamp `SlotRow.status="working"` +
`last_spawned_at=now` in their PRE-spawn session (rolled back to `idle` on a failed spawn), and `heartbeat_slot` holds
the slot for a bounded 45s grace window when it sees that pre-stamp with no live typed occupant resolved yet — self-
healing to normal dispatch if the window elapses on a genuinely stuck/failed spawn. Full incident + fleet-audit detail:
`/plans/archive/issues/cicd_heartbeat_steals_slot_regression_immediate_dispatch_2026_07_29.md`.

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

## Dead-worker resume-vs-requeue gate (`server/resume_lifecycle.py::classify_dead_worker`)

Once a session is dead (killed above, or vanished on its own — `TmuxPruner` catches both), one more decision remains:
does the slot's in-flight task get **resumed** (`claude --resume <session_id>`, same conversation, WIP intact) or
**requeued** (fresh spawn, zero conversational context, WIP still preserved via the handoff path)?
`classify_dead_worker` is the SSOT — resume iff ALL hold: a task is bound to the slot, a `claude_session_id` exists
(resume target), the slot dir carries uncommitted WIP (a clean tree has nothing a resume would preserve that a fresh
spawn loses), and `resume_attempts < resume_max_attempts`.

**Context-saturation gate** (`ao_autospawn_role_blind…/gap-3`, 2026-07-14; threshold lowered
`ao_worker_session_continuity_and_resume_threshold_2026_07_27`): a `--resume` reloads the SAME conversation, so resuming
an already-(near-)saturated session just re-wedges it instantly. At/above `resume_fresh_context_pct` (**80**, lowered
from 90 — operator-directed) the classifier returns `requeue` regardless of dirty WIP; the WIP files are still
preserved, only the un-continuable conversation is dropped. Below that, resume proceeds — and if
`context_used_pct >= resume_compact_first_context_pct` (also **80** as of the same change — this collapses the old 80–90
"resume but tell the worker to compact first" band to zero width, so that middle path no longer fires; a resumed session
is now always either clearly-fresh-enough-to-just-continue or saturated-enough-to-requeue-instead), `autospawn.py`'s
resume nudge prefixes an explicit "run `/compact` first" instruction (`_do_spawn`, not the classifier itself).

Since a session the context-burn trigger just killed is, by construction, at/above `context_burn_kill_min_pct` (98) —
always well above even the lowered 80% — lowering `resume_fresh_context_pct` cannot regress the context-burn-kill →
dead-worker → resume-classification chain: a context-burn kill is always followed by a requeue, never a resume.

---

## Held-behind-a-`/blocked`-gate merge pattern — failure mode + the gate-aware unpushed sweep (2026-07-26/31)

**The pattern this protects.** A worker sometimes deliberately commits locally but WITHHOLDS the push, pending an
operator sign-off gate raised via `/blocked` (e.g. a design doc's "OPERATOR RATIFICATION REQUIRED BEFORE MERGE"). The
commit sits ahead-of-origin on an otherwise clean tree until the operator answers. This is a legitimate hold, not
stuck/orphaned WIP.

**The failure mode (2026-07-26 incident, `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`).**
`_sweep_unpushed_slots` (below) exists specifically to rescue a dead session's committed-but-unpushed HEAD so it is
never silently lost. Before the fix, it was **unconditional** — it had zero awareness that the exact commits it was
about to push might be the subject of an OPEN, task-linked `/blocked` entry acting as an operator merge gate. Sequence
observed: a worker filed a `/blocked` merge-sign-off question, got only an interim "HOLD, do NOT quickmerge yet" (never
finally ratified), froze, was reclaimed dead by the watchdog, and ~6 minutes later the unpushed-sweep pushed the held
commits to `live-defi-rollout` anyway — defeating the operator gate purely through automation, with the standing `*/15`
LDR→main auto-promote then poised to carry the unratified change to `main`. The lesson generalizes: **any "push held
pending human sign-off" pattern is silently defeatable by a rescue-on-death sweep unless that sweep is taught to
recognize the hold.**

**The gate-aware fix (`agent-orchestrator@49c919d`).** `_sweep_unpushed_slots` (`worker_liveness_watchdog.py:1499`) now
checks, per slot, whether the slot's `current_task` has an OPEN task-linked `BlockedRow` (`answered_at IS NULL` — this
single predicate covers unanswered AND partial/`operator_pending` answers, since a partial/interim answer intentionally
leaves `answered_at` unset per `state_store.activity`'s own `partial_answer_blocked` semantics) before calling
`push_or_preserve_ahead_commits`. If gated, the WHOLE slot's ahead commits (every repo, not just the one under
discussion — the block is keyed on the task, which can span repos) are **preserved on a
`wip-preserve/orchestrator-slot-<N>-<sha>` ref instead of pushed to `origin/<base>`**, even when they would otherwise
pass the ordinary QG-sentinel + trailer checks that let a normal rescue proceed (`push_or_preserve_ahead_commits`'s
`gated: bool` param, `server/worktree_clean_check/_ahead_push.py`). Every resulting `OrphanCommit` carries `gated=True`,
and the sweep fires a **distinct** `unpushed_held_behind_open_gate` activity event (slot_id + task_id + repo + sha) in
addition to the ordinary `slot_unpushed_commits_reclaimed` event — so "a merge gate held a push" is never silently
indistinguishable from an ordinary push-rejection-then-preserve in the activity log; a human decides the actual
ratify/discard call from there. Nothing is discarded — the point is "don't auto-ship held work," not "lose it."

**Contract for future gated-merge workflows.** A worker (or a future automation) that wants to hold a commit behind a
human sign-off should route the hold through a **task-linked, unanswered `/blocked` entry** — that is the ONE signal the
unpushed sweep (and any future rescue-on-death path built the same way) recognizes as "do not auto-ship." A hold
implemented any other way (e.g. a code comment, a Slack thread, an unlinked doc note) is invisible to this mechanism and
remains exactly as defeatable as the 2026-07-26 incident. Regression coverage: `tests/test_watchdog_unpushed_sweep.py` —
`test_sweep_gates_push_behind_open_operator_blocked_entry`,
`test_sweep_gates_push_behind_partial_answered_blocked_entry`, `test_sweep_pushes_when_blocked_entry_already_answered`
(a FINAL-answered historical row does not false-positive gate).

---

## Fleet-wide in-flight-task double-dispatch guard + abandoned-claim threshold (2026-08-06/09)

**The gap this closes.** A resumable long-running todo (a GCS backfill/migration whose real-world work can outlive its
owning slot's tracked session — the triggering incident, `prediction_trades_migration_concurrent_dispatch_2026_07_28.md`
— a slot's session ended with no closing Progress Log entry) could be re-dispatched to a SECOND slot while the first was
still genuinely working, because the backlog dispatcher's existing `status == 'queued'` precondition doesn't by itself
catch a task whose `TaskRow` bookkeeping reads free but whose owning `SlotRow` is still actively working it.

**The guard (`agent-orchestrator@9e28a36`, 2026-08-06).** A FLEET-scope `in_flight_elsewhere` eligibility filter in
`server/dispatch.py`'s `_FILTERS` table: if a `SlotRow` still shows a task as its `current_task` with a live heartbeat,
no OTHER slot may claim the same task id, even if the `TaskRow`'s own `status`/`dispatched_to` reads free. Wired into
`_detailed_fleet_reasons` so `/api/backlog/{id}/blockers` reports the block by name. The staleness threshold is an
INJECTED tuning parameter, `tuning.in_flight_task_owner_stale_after_seconds` (env-free — change the code default +
redeploy, `.env.local` silently no-ops) — never hardcoded into the filter logic. Regression:
`tests/ test_dispatch_in_flight_elsewhere.py` (live-owner blocks a second slot; stale-owner releases it; the owning slot
may still claim its own task; threshold configurable via `set_tuning`; a live-owned in-flight task excluded from the
spawn budget).

**Operator ruling 2026-08-09 (`prediction_trades_migration_concurrent_dispatch_2026_07_28.md` todo 3) — both open
questions now resolved:**

1. **Threshold: 900s, ratified.** The shipped default was already this value — it's the exact number BOTH the precedents
   that motivated the knob (`TuningDefaults.watchdog_heartbeat_timeout`, `server/config.py:473`, and
   `one_shot_stale_grace_minutes`=15min, `…/config.py:664`) independently agree on. No code change required — the ruling
   confirms the existing default is correct, it doesn't change it.
2. **Stale-claim takeover rule: merge, preferring the higher-progress checkpoint.** When a second slot resumes a task
   whose prior owner went stale, it does NOT blindly adopt the dead slot's checkpoint as-is, and does NOT always
   re-verify from zero — it merges the available checkpoint(s) and prefers the entry with the higher progress count.
   This mirrors the triggering incident's own ad-hoc fix (three report files merged by day, preferring the higher
   `canonical_enriched` count) — a working pattern already proven under the exact failure this guard exists for, rather
   than a fresh design. Any resumable todo whose checkpoint format supports a monotonic progress count should implement
   takeover this way; a format without one should state its own equivalent (e.g. latest-mtime-wins) rather than
   defaulting to blind adopt-or-discard.

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
| `ORCHESTRATOR_WATCHDOG_DAILY_CAP`             | `50`         | Per-VM kills before dormancy                                                                                                    |

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
- **Do NOT bypass the per-VM 50-kills-per-day cap** — at cap, Slack alert fires + watchdog goes dormant; operator must
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

**Symptom (measured 2026-07-21).** 15 finished typed agents (9 `cicd` one*shot + 6 `plan_health` scheduled) sat
`status=active` for up to 19 h, pinning 15/16 slots → the daily reconciler got `503 no free slot`. Their JSONLs show
none errored — each completed its task, then idle-polled forever. The role docs already say *"then EXIT, do NOT loop"_,
but \*\*"EXIT" only ends the Claude \_turn_\*\*; the tmux session lingers at an idle `❯` prompt, `WorkerLivenessKicker`
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
[`ao_uniform_agent_liveness_contract`](../../plans/archive/2026_07/ao_uniform_agent_liveness_contract_2026_07_20.md)).**
A `one_shot`/`scheduled` agent, on completing, POSTs an explicit **role-aware `/done`** (task-less for a task-less
one-off — today's `/done` is task + plan-flip gated and must be extended to accept a task-less completion). The backend
then (a) archives the AgentRow `lifecycle-complete`, (b) frees the slot, (c) flags it so `WorkerLivenessKicker` stops
nudging it. The agent then stops; the next reap cleans the now-dead session. This makes "finished" an **explicit
signal** instead of an inference from a session death that never happens — and let the `f641968`/`1e7fec0` carve-outs be
**DELETED** (done — C1, `agent-orchestrator@0d510e9`; a booted one-off is `working`, never `idle`, so idle-scanners skip
it by construction; on `/done` it is archived, not reaped). Only `5907317` (the boot-gate `spawn_base_role` recognition)
is kept — B1 depends on it, so it was not subsumed.

> **"One-off" here = an event-spawned CRAFT** (escalation/scheduled). A **plan-backlog worker is persistent** and DOES
> go `idle` when it has no ready task — the idle-reclaimer reaping it is then correct (a fresh worker picks up later
> work; durable state lives in the plan/Progress Log). See the next section, § "Dispatch-context-driven lifecycle".

---

## Dispatch-context-driven lifecycle — persistent plan-backlog workers vs event-spawned one-shots (2026-07-21)

> **SSOT for: which workers are reaped on `/done` and which persist.** The completion contract above answers "how does a
> _finished_ one-off die?"; this section answers "**which** workers are one-offs in the first place?" — and corrects a
> defect where plan-backlog workers were wrongly reaped after every task. **Implementation plan**:
> [`ao_worker_lifecycle_dispatch_context_2026_07_21`](../../plans/archive/2026_07/ao_worker_lifecycle_dispatch_context_2026_07_21.md).

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
"a fresh-context session per task." Observed: one plan's tasks sprayed across slots (cost*per_day tasks ran on slots 3
\_and* 4), and slots churned spawn→task→reap→respawn every few minutes. Each task completed + verified (no work lost),
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

This is the philosophical basis the 2026-08-04 one-task-per-session hard rule (`tuning.one_task_per_session_enabled`,
default True) acts on directly: since conversational carry-over was never load-bearing, forcing a fresh session on EVERY
task boundary (not just idle/retire) costs nothing but respawn overhead — see
[agent-orchestrator-single-vm-architecture.md's worker-lifecycle bullets](/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md)
for the full mechanism. The "same live session drains the next task" claim earlier in this doc's own lifecycle
description is now the NON-default path (`one_task_per_session_enabled=False` only).

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

---

## Calibration-source contract: only CLI-rendered percentages may calibrate a learned window (2026-08-09)

**The rule.** `context_probe.observe(model, tokens, *, pane_pct=...)` treats `pane_pct` as an AUTHORITATIVE calibration
source — the exact denominator the CLI itself is dividing by — and latches `tokens / (pane_pct/100)` into
`calibrated_window`. That field is **monotonic** (only ever grows) and **outranks every other signal** (the watermark,
the `model_tier` prior), so a single bad write permanently inflates a model's learned window for the whole fleet. A
caller may therefore pass `pane_pct` to `observe()` ONLY when it is a percentage the CLI **itself rendered** — never a
heuristic estimate of one.

`server/worker_liveness/__init__.py::derive_context_used_pct()` (a general-purpose "how full is it" READING) has three
branches, in priority order: (1) `_CONTEXT_USED_RE` — "N% context used", CLI-rendered, authoritative; (2)
`_AUTO_COMPACT_RE` — "N% until auto-compact" (inverted), CLI-rendered, authoritative; (3) `_TOKEN_USAGE_RE` — a
mid-spinner "↑ N.Nk tokens" readout divided by a hardcoded `_DEFAULT_CONTEXT_WINDOW_K` assumption — a **guess**, not a
CLI-rendered fact. Branch 3 calibrates the window against an assumption about the window — circular, and the `observe()`
contract above means it is unsafe to ever feed as `pane_pct`.

**The fix**: `derive_calibration_pct()` (same module) is split out to cover ONLY branches 1–2 — CLI-rendered
percentages, never the heuristic. Both calibration call sites (`context_lifecycle.py::_pane_readings()`, which returns
`(reading_pct, calibration_pct)` from one pane capture and passes `calibration_pct` — never `reading_pct` — to
`context_probe.context_used_pct(..., pane_pct=calibration_pct)`) now pass this narrower value;
`derive_context_used_pct()` (all three branches) remains available as a plain reading, never as a calibration input.
**Any future caller of `context_probe.observe()`/`context_used_pct()` must follow the same rule: pass a calibration
value only if it came from a CLI-rendered percentage, never from a token-count/window-size heuristic.**

**Defense-in-depth**: `context_probe._calibration_is_plausible()` independently rejects a calibration exceeding
`_MAX_CALIBRATION_OVERSHOOT` (1.5×) of `max(model_tier.context_window(model), watermark_tokens)` — so even a future
caller that gets the source wrong cannot inflate a model's window past a bounded multiple of its prior/watermark. This
does not depend on every caller honoring the calibration-source contract above; it is the backstop, not a substitute for
it.

**Main's `AgentRow` floor — the other half of the fix.** Every WORKER already had a self-reported floor: `_read_pct`
took `max(SlotRow.context_used_pct, probe)`, so a poisoned/under-reading probe could only ever be overridden upward by
the worker's own `/progress`-reported percentage. **Main has no `SlotRow`** (it is not a slot-bound worker), so before
this fix it relied on the measured probe ALONE — no self-report floor at all. `context_lifecycle.py::_main_pct()` closes
that asymmetry: it takes the measured probe, then floors it on main's own `AgentRow.context_used_pct` (the CLI's own
self-reported figure, posted by main on every tick) via the same ratchet-and-persist pattern as the worker path —
`max(measured, self_reported)` wins and is written back. A learned- window error can therefore only ever make the
compaction policy fire EARLY (over-report), never blind it (under-report), for every target in the fleet — worker or
main.

**The incident this closes.** `claude-sonnet-5`'s `calibrated_window` was latched to 2,614,639 (true window ~937K, a
2.8x overshoot) because a `_TOKEN_USAGE_RE` heuristic reading was fed to `observe()` as if it were authoritative. Main's
real 99%-context session measured as 26% against the poisoned window, no `context_lifecycle` threshold ever fired
(`proactive_compact_guidance` = 0 for `role=main` across a 4.3-hour activity window), and main ran to the model's hard
limit with the compaction safety net silently disarmed — while the worker fleet was unaffected because every worker
still had its `SlotRow` self-report floor. Full root-cause detail, live-verification evidence, and the
plausibility-audit results:
`plans/active/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md`. Regression
coverage: `tests/test_context_probe.py::test_the_measured_poisoning_case_is_rejected` and siblings.

---

## Context-window learning is per-model; per-session divergence is expected and already floored (2026-08-09)

`context_probe.py`'s learned-window registry (`data/state/learned_context_windows.json`, `context_window_for(model)`) is
keyed **only by model string** — no account or session dimension. Follow-up to
`ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md`: with the poisoning fixed, main's own
CLI-rendered figure still showed its TRUE usable window as ~696K (99% at 689,570 tokens) — BELOW both the sonnet-5
corpus watermark (937,882, the largest context any sonnet-5 session has demonstrably reached) and the `model_tier`
cold-start prior (1,000,000). Investigated whether the effective window is genuinely per-account/per-session rather than
per-model.

**Account tier ruled out for this instance, but a real registry blind spot.** `agents/accounts.json`'s `AccountTier`
field (`pro`/`max5`/`max20`/`team`/`enterprise`/`api`) is declared once per Claude subscription and never reaches
`context_probe` — every account's sessions blend into one per-model figure regardless of tier. Checked directly against
the live registry: main's account at the time (`sub-f-odum2default`) is `max20`, the SAME tier as the large majority of
fleet accounts that built the 937,882 sonnet-5 watermark — so a downgraded account tier does not explain this specific
gap. The blind spot itself is still real: the fleet carries one `pro`-tier account (`sub-a-ikenna`) whose sessions feed
the same undifferentiated per-model watermark, so a future genuine tier-driven window difference (if Anthropic's own CLI
enforces one) would be silently averaged away rather than surfaced.

**`effort`/`thinking` is the better-supported per-session driver.** `agents/main.md` runs `thinking: high`, while the
ordinary `worker.md` default is `thinking: medium` (confirmed via each role's own frontmatter) — main's session
population differs systematically in effort/thinking depth from the mostly-worker sessions that built the corpus
watermark. Higher effort/thinking plausibly reserves more of the CLI's own internal turn budget, which would make the
CLI itself decide a session is "full" — and render its own "N% context used" — at a lower absolute input-token count
than an otherwise-identical lower-effort session on the same model. This is Anthropic's own Claude Code CLI internal
budgeting, opaque to this codebase, so it is the best-supported hypothesis rather than a proven mechanism.

**Conclusion — documented as expected divergence, not a defect; no registry change made.** The per-model
`context_window_for(model)` figure is intentionally coarse: a COLD-START / no-better-signal fallback, never an override,
for any target carrying its own self-report. Main's `AgentRow.context_used_pct` (the CLI's own figure, reported every
tick) already floors the measured probe in `_main_pct()` (`context_lifecycle.py`), and every worker already floors its
probe with `SlotRow.context_used_pct` the same way — so whatever per-session/per-account variance produces a session's
true window, the ONE target it matters for (that session) already gets the accurate number via the self-report ratchet,
not the corpus/model-level estimate. The residual risk is a target with no self-report at all silently under-compacting
on a smaller-than-average window; none exists in the fleet today (main and every worker/review slot carries a
self-report). A future per-model-only registry key should stay that way unless a NEW target class appears with no
self-report of its own.

---

## main/review stay COOPERATIVE-first — the idle gate is intended, not a defect (operator ruling 2026-08-10)

**The ruling.** main and review keep the cooperative-first compaction path with its idle-verified forced fallback. The
worker-style UNCONDITIONAL force (`context_worker_force_compact_pct`, no idle check, operator ruling 2026-08-05) is
**not** extended to them. This reaffirms the 2026-08-05 rationale — _"never compact mid-work — a single pane-snapshot
'looks idle' is untrustworthy on a days-long loop"_ — against live measurement.

**What the idle gate actually costs.** The forced fallback needs `classify_pane == "idle"` on `_FORCE_IDLE_OBSERVATIONS`
(3) consecutive keeper ticks, plus an empty input box, plus ≤1 child process under the pane shell. The keeper ticks
every `main_agent_interval_seconds` (**60s**), so the requirement is **~3 minutes of continuous quiet** — not hours. A
recurring misreading is to treat the ≥6h instrumentation OBSERVATION WINDOW as an idle expectancy; it is not.

**The measurement that decided it** (read-only `GET /api/activity?limit=4000`, 3.7h window 2026-08-09 19:50Z→23:30Z,
live fleet, taken after the idle-gate instrumentation landed):

| path                        | events                                                                                  | effectiveness    |
| --------------------------- | --------------------------------------------------------------------------------------- | ---------------- |
| COOPERATIVE (main + review) | main: guidance 1 → compaction 1, idle gate blocked 1 · review: 16 compactions, 0 forces | **17/17 = 100%** |
| FORCED (workers)            | `forced_precompact` 68 · `forced_compact` 65 · `forced_compact_ineffective` 51          | **14/65 = 22%**  |

The cooperative nudge lands before the force is needed: main and review are not starved of the 3-minute idle window,
they mostly never reach the fallback at all. Extending the unconditional force to them would move the two roles that
compact reliably onto the path that currently fails ~78% of the time
(`/plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md`; its decisive "verify by
EFFECT, not submission" fix was still unlanded when this was measured, so 22% is a pre-fix baseline, not a regression).

**Consequences for future work — read before "fixing" the idle gate:**

- The gate refusing to open is **not** by itself a bug report. Judge the path by whether the target actually compacts
  (`context_compact_observed`), never by whether the force fired.
- A silent main/review — zero context-lifecycle events — is still a real alarm, because that is exactly what the
  2026-08-09 poisoned-window incident looked like. The silent-disarm detector, not the force, is the control for it.
- If the forced path's effectiveness is ever fixed to approach the cooperative path's, this ruling may be revisited —
  with a fresh measurement, not from first principles.

### Anti-pattern (adds to the list above)

- **Do NOT extend the worker unconditional force-compact to main/review while the forced path measures WORSE than the
  cooperative one.** This is a DATA gate, not an operator gate (operator ruling 2026-08-10, deliberately relaxed from
  "requires a new operator ruling" so a worker can act on evidence without waking a human). The bar is stated and
  checkable — a worker may extend the force to main/review, without any further ruling, once a fresh measurement over a
  window of **>=6h of live fleet activity** shows BOTH:

  1. forced-path effectiveness (`context_compact_observed` following a `forced_compact`, divided by `forced_compact`) is
     **>= the cooperative path's** over the same window, and
  2. forced-path effectiveness is **>= 90%** in absolute terms.

  Baseline to beat, measured 2026-08-09 over 3.7h: cooperative **17/17 = 100%**, forced **14/65 = 22%**. Below that bar
  the ruling stands and the idle gate stays. Record the new measurement in this section when you change it, so the next
  reader sees the numbers that moved it rather than an assertion.

  Two things this gate does NOT accept as evidence: the force _submitting_ (`submitted=True` is what
  `forced_compact_ineffective` exists to disprove — see
  `/plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md`), and the idle gate merely
  _refusing to open_ (judge the path by whether the target compacts, never by whether the force fired).

  Machine guard: `tests/test_context_lifecycle.py` asserts main/review route through the idle-gated
  `_maybe_force_compact`, so a change that bypasses it fails the suite rather than shipping silently. Changing the
  policy therefore means deliberately updating that test WITH the measurement above in the commit message — which is the
  intended friction, not a blocker.
