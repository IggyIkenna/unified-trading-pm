---
doc_type: issue
title:
  Review-slot-1 crash-loop recurrence — restart-correlation lead reconfirmed 6 days later, new ~26min zombie-window
  mechanism found
summary: >-
  Live-captured recurrence of
  `/plans/archive/2026_08/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` (archived 2026-08-09 —
  prematurely, per that doc's own last entry, which found a restart-correlation lead and explicitly asked for follow-up
  that never happened). A bounded background PID watcher on `orch-slot-1` caught a fresh death live on 2026-08-14: a
  review spawn that never called its first `/heartbeat` sat as a DB-status="killed" but still-genuinely-alive orphan for
  ~26 minutes past its own documented ~15min detection budget, with two `orchestrator.service` restarts landing inside
  that exact gap. Zero kernel-log entries (rules out OOM/SIGKILL again).
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, tmux, review-role, crash-loop, live-incident, worker-liveness-watchdog, recurrence]
related:
  - /plans/archive/2026_08/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md
  - /plans/active/issues/ag_closeout_audit_ao_parked_2026_08_10.md
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
created: 2026-08-14
author: interactive session
parent_epic: infrastructure_master
priority: P1
source: >-
  Interactive session investigating why 2-3 review-role AgentRows sat concurrently "stale" for hours on the central VM
  (operator ask); set up a bounded background PID watcher on orch-slot-1 to catch the next death live, since the
  archived doc's own dominant host-contention hypothesis didn't match tonight's account-exhaustion-driven instability.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: backend_engineer (slot 29, agent-orchestrator@c107c96a52 + agent-orchestrator@6ec0f1e507, 2026-08-14)
last_updated: 2026-08-14
locked_since:
context_scope:
  [agent-orchestrator/server/worker_liveness_watchdog.py, agent-orchestrator/server/worker_liveness/_auth_failover.py]
---

# Review-slot-1 crash-loop recurrence

> **🟢 ARCHIVED (2026-08-14).** All todos done, 0 open, unlocked. Todo 1's root cause (unconditional `status="killed"`
> write regardless of whether `kill_session()` actually terminated the tmux session) is fixed
> (`agent-orchestrator@c107c96a52`), and todo 2 closed the same defect class at the three remaining call sites that
> bypass `_kill_slot` (`agent-orchestrator@6ec0f1e507`) rather than tightening `orphan_session_reclaim`'s sweep cadence,
> which was already tight enough (60s) and wasn't the actual bottleneck. See Progress Log for both fixes' full detail.

## What was found (2026-08-14, live capture)

Full timeline for one traced spawn on `orch-slot-1`:

- **01:02:38Z** — review spawns fresh (account `sub-f-odum2default`).
- **01:15:44Z** (786s later) — `spawn_retry_cap_reached` fires correctly (`_auth_failover.py`): pane sat `idle`, never
  called `/heartbeat`. Its own alert message promises _"WorkerLivenessWatchdog's own heartbeat-silent trigger
  (independent of this counter, ~15 min) will still kill+respawn automatically."_ Confirmed in code
  (`_heartbeat_timeout_for`) that the real threshold for a persistent (non-terminal-lifecycle) slot IS 900s (15min) —
  the promise is accurate as documented.
- **01:41:57Z** (2355s / ~39min after spawn) —
  `WorkerLivenessWatchdog slot 1: reclaiming orphan session orch-slot-1 (status=killed + live, spawn_age=2355s)` — the
  FIRST actual kill, ~26min later than the documented 15min budget, via the generic `orphan_session_reclaim` sweep, not
  the dedicated Trigger 3 (heartbeat-silent) path.
- `journalctl -k` for the death window: zero entries. No OOM, no SIGKILL — 15th+ kernel-log-negative sample against the
  archived doc's own running tally (that doc independently ruled out a kernel-level cause via the same method).
- **Two full `orchestrator.service` restarts landed inside the exact 01:15-01:30Z gap** (`ao-self-pull.sh` picking up
  fresh LDR commits — one of them this same session's own `agent-orchestrator@c907deff71`).

## Why this matters — reconfirms, not a new phenomenon

This is a direct, independent reconfirmation of the lead the archived doc's own final entry (2026-08-09, before
archival) already surfaced and explicitly flagged as unresolved: kills correlating with `ao-self-pull.sh` restarts
despite `orchestrator.service`'s `KillMode=process` (measured there at 9-24% of kills within 2-5min of a restart — "a
real but MINORITY contributing factor, not the dominant driver"). That entry asked for "its own targeted follow-up"
which never happened before the doc was archived as fully resolved days later.

Tonight adds one new, specific mechanism beyond what that entry measured: not just death-near-a-restart, but a **~26min
zombie window** where a review slot is completely non-functional — DB says `killed` (so it "looks" dead to anything
checking status) while the actual tmux session is still alive and occupying the slot name, which structurally blocks
`_ensure_review_agents`'s own `has_session()`-gated respawn check from ever attempting a fresh spawn during that window.
This plausibly explains why the archived doc's own kill-cadence measurements were so wildly inconsistent across
different sampling windows (5-9min in some, tens of minutes in others) — restart frequency on LDR varies a lot depending
on how much fleet-wide commit activity is landing at any given moment.

**`WorkerLivenessWatchdog` is an in-process Python object** — a service restart creates a fresh instance, resetting
whatever in-memory state it carries tick-to-tick (`_recently_nudged`'s `_last_nudge_at`, `_stuck_ticks`, `_prev_panes`,
etc.). Plausible (not yet proven) that this is why Trigger 3's own 15min promise didn't hold across the two restarts in
this window. Not traced further this session — this needs deliberate, careful work against fleet-critical liveness code,
not a rushed change under time pressure.

**Separately shipped this session** (adjacent gaps found while investigating this, not this exact bug):
`agent-orchestrator@c907deff71` (a task-worker could self-boot onto a review-reserved slot with zero guard — closed); a
follow-up commit shortening the sessionless-record stale-grace for a PERSISTENT agent confirmed tmux-dead (was waiting
the full 6h grace meant for a genuinely-alive pure-cloud agent, now 20min) + a new operator
`POST /api/agents/{id}/force-archive` escape hatch (refuses whenever the session is genuinely still alive — never a way
to hide a live one).

## Todos

- [x] ✅ [BACKEND] P1. **Trace why `WorkerLivenessWatchdog`'s Trigger 3 (heartbeat-silent, 900s/15min threshold,
      `worker_liveness_watchdog.py` ~line 1050-1103) did not act within its own documented budget for the 2026-08-14
      01:02:38Z slot-1 spawn** — actual detection came ~26min late via the separate `orphan_session_reclaim` sweep
      instead (~line 839-855). Check specifically whether the TWO `orchestrator.service` restarts inside the 01:15-
      01:30Z gap reset in-memory gating state (`_recently_nudged`'s `_last_nudge_at`, `_stuck_ticks`, `_prev_panes`, or
      similar) in a way that delays Trigger 3's own evaluation of a slot across a restart. If confirmed: either make the
      relevant state DB-persisted (survives a restart) or have the watchdog re-evaluate every currently-silent slot
      immediately on its own startup rather than waiting for its next natural tick. Cross-reference the archived doc's
      own restart-correlation finding (9-24% of kills within 2-5min of a restart) — likely the same underlying
      mechanism, not a second coincidence. Repo: agent-orchestrator. — **ROOT CAUSE FOUND, NOT the in-memory-reset
      theory** — see Progress Log. Fixed: agent-orchestrator@c107c96a52.
- [x] ✅ [BACKEND] P2. **Once the above is understood, decide whether `orphan_session_reclaim`'s own sweep cadence
      should independently be tightened** as a backstop regardless of the Trigger-3 root cause — a slot sitting
      DB-status `killed` while genuinely still alive should be reclaimed on a much shorter cycle than "whenever the next
      full sweep happens to run," since it structurally blocks a fresh respawn attempt for its entire duration. Repo:
      agent-orchestrator. — **Decision: NO, do not tighten cadence — closed the real remaining gap instead.** See
      Progress Log. Fixed: agent-orchestrator@6ec0f1e507.

## Progress Log

**2026-08-14 — Todo 1 root-caused + fixed, NOT the in-memory-state-reset mechanism the todo anticipated.** Slot-14
backend_engineer worker. Read `_tick_once` (lines 800-1117), `_resume_or_fresh_respawn` (2407-2534), `_kill_slot`
(2595-2669), `tmux_spawn.kill_session` (453-482), and `_auth_failover.py`'s `spawn_retry_cap_reached` path (100-192) in
full before concluding.

**The `_recently_nudged`/`_stuck_ticks`/`_prev_panes` in-memory-reset theory does not hold up**: `silence` (the value
Trigger 3 compares against `heartbeat_timeout`) is computed fresh every tick from DB timestamps via
`effective_silence_seconds(last_ping, last_spawned_at, assigned_at, session_created)` — none of those in-memory dicts
feed into that calculation at all. They gate unrelated things (stuck-at-prompt tick accumulation, post-nudge grace for
the API-error-pause path). `spawn_retry_cap_reached` (`_auth_failover.py`) is purely diagnostic — it never touches
`SlotRow.status`, so the slot legitimately stayed in `{working,dispatched,stale}` and inside Trigger 3's `active_slots`
query the whole time up to the 15-min mark, exactly as the alert message promised.

**Actual mechanism, confirmed by direct code reading (not a live repro — see caveat below):**

1. Trigger 3 fired on schedule at `spawn + 900s` (~01:17:38Z, INSIDE the 01:15-01:30Z restart window). Fresh spawn, no
   established `claude_session_id` yet → `_resume_or_fresh_respawn` took the `not stored_sid` branch → called
   `_kill_slot(slot_id, tmux_session, "heartbeat_silent")`.
2. `_kill_slot` called `tmux_spawn.kill_session(tmux_session, reason=...)`. That function returns a bool (`True` =
   session existed and `tmux kill-session` exited 0; `False` = either no session existed, OR the `tmux kill-session`
   subprocess exited non-zero / hit its 5s timeout — logged via `logger.warning`, never raised).
3. **The bug**: `_kill_slot`'s old code called `kill_session()` inside a bare `try/except Exception` (only catching a
   raise) and then, completely UNCONDITIONALLY — regardless of the call's outcome — wrote `slot_row.status = "killed"`
   to the DB. A `False` return (tmux command genuinely failed to end the session) was silently discarded.
4. Once `status="killed"`, the slot drops out of `_tick_once`'s `active_slots` query
   (`status.in_({"working","dispatched","stale"})`) — **Trigger 3 can structurally never re-evaluate that slot again**,
   by design of the query, independent of any in-memory state. The only remaining backstop is `orphan_session_reclaim`,
   a SEPARATE sweep in the SAME watchdog thread that scans `status=="killed"` rows and checks `has_session()` — but it
   runs inside the same process, so it's exposed to the identical transient unavailability (the two
   `orchestrator.service` restarts landing 01:15-01:30Z) that plausibly caused the original `kill_session` failure.
   `_ZOMBIE_RECLAIM_GRACE_SECONDS` defaults to 180s measured from `last_spawned_at` (01:02:38Z) — already satisfied well
   before the 01:17:38Z kill attempt — so the ~26min delay to the 01:41:57Z reclaim is consistent with the watchdog
   thread itself not getting a stable tick until the restarts settled, not with the reclaim's own grace window.

**This reframes, not contradicts, the restart correlation**: restarts don't delay Trigger 3's evaluation (the
in-memory-reset theory) — they plausibly delay the `tmux kill-session` subprocess succeeding (or delay the watchdog
thread from ticking at all, or both) at the exact moment Trigger 3 attempts its kill, and the resulting zombie then sits
unrecovered until the SAME restart-vulnerable thread stabilizes enough to run its reclaim sweep. Not proven via a live
repro of the restart-induced subprocess failure itself (that would require forcing a restart mid-kill, out of scope for
this todo's budget) — but the "unconditional status=killed regardless of kill outcome" defect is directly read from the
code, independent of that unproven trigger mechanism, and is real+fixable either way: ANY `kill_session` failure
(restart-correlated or not — a busy host, a stale tmux socket, a transient subprocess timeout) previously produced the
exact same unrecoverable zombie.

**Fix shipped** (agent-orchestrator@c107c96a52, QG-green 3650 passed/2 skipped): `_kill_slot` now calls
`has_session(tmux_session)` after the kill attempt; if the session is confirmed STILL alive, the DB write is skipped
entirely (status stays whatever it was) and the slot remains in `active_slots` for Trigger 3 to retry on its own very
next tick — throttled by the pre-existing per-slot 5-min kill cooldown, so no new state/timer was introduced. Added
`test_kill_slot_does_not_mark_killed_when_session_survives` + extended `_kill_slot_patches` with a `session_still_alive`
param; also pinned `has_session` in `test_kill_slot_clears_heartbeat_resume_count` (`test_self_healing_hardening.py`)
which previously relied on the real host having no `orch-slot-8` tmux session.

**Todo 2 left open, not absorbed**: the fix above closes the primary zombie-creation path for kill_session failures,
which reduces (but doesn't eliminate — a status=killed row could still arise from other code paths, e.g. the
`_resume_or_fresh_respawn` line 2508 spawn-failure branch, which sets `status="killed"` directly without a `has_session`
guard because that branch already knows the OLD session was torn down by its own explicit `kill_session()` call a few
lines earlier and is failing on the NEW spawn, not the kill) the urgency of independently tightening
`orphan_session_reclaim`'s cadence. Left as a genuine P2 judgment call for whoever picks it up next, per the todo's own
"regardless of root cause" framing.

**2026-08-14 — Todo 2 resolved.** Slot-29 backend_engineer worker. Read `_tick_once` (lines 805-880), `_kill_slot`
(2682-2770), `_resume_or_fresh_respawn` (2494-2650), `_maybe_realign_tier` (2340-2430), and `_handle_usage_cap`
(2068-2220) in full before deciding.

**Decision: do NOT tighten `orphan_session_reclaim`'s sweep cadence.** It already runs on EVERY watchdog tick
(`watchdog_interval_seconds`, default 60s — `server/config.py:552`), gated only by `_ZOMBIE_RECLAIM_GRACE_SECONDS` (180s
from `last_spawned_at`). That is already tight; the measured 26-minute delay in this doc's own live capture was not
caused by sweep cadence — it was caused by the watchdog _thread itself_ not getting a stable tick at all while
`orchestrator.service` restarted twice inside the 01:15-01:30Z window (a process-level unavailability, not a timer
problem). Shortening `watchdog_interval_seconds` globally would add DB-query + `tmux capture-pane` load across every
active slot on every tick for a scenario it would not actually have prevented, since the reclaim sweep runs in the SAME
thread/process that was unavailable.

**What actually needed fixing, per this doc's own prior entry**: the three OTHER `status="killed"` write sites that
bypass `_kill_slot` entirely and therefore never got the `has_session()` guard — `_resume_or_fresh_respawn`'s
heartbeat-resume spawn-failure branch, `_maybe_realign_tier`'s tier-realign spawn-failure branch, and
`_handle_usage_cap`'s usage-cap spawn-failure branch. Each kills the OLD tmux session via an **unchecked**
`tmux_spawn.kill_session()` call (bare `try/except` only catches a raise, never inspects the `bool` return) before
attempting a resumed spawn on a NEW session with the same name; if that kill silently failed to actually end the session
AND the new spawn then also raised, the old code wrote `status="killed"` unconditionally — the exact same
zombie-creation defect class the `_kill_slot` fix closed, just via three different call sites `_kill_slot` doesn't own.

**Fix shipped** (agent-orchestrator@6ec0f1e507, QG-green 3730 passed/2 skipped Python + 346 passed dashboard vitest):
added the identical post-failure `has_session(tmux_session)` guard to all three sites — if the session is confirmed
still alive, the DB write is skipped and the slot's status is left unchanged (retried on the trigger's own next tick),
exactly mirroring the `_kill_slot` pattern. Added
`test_heartbeat_resume_spawn_failure_does_not_strand_zombie_when_session_alive` (proves the guard) +
`test_heartbeat_resume_spawn_failure_marks_killed_when_session_actually_gone` (proves the existing normal-case recovery
path is unregressed) to `test_self_healing_hardening.py`, covering the `_resume_or_fresh_respawn` site directly; the
`_maybe_realign_tier` and `_handle_usage_cap` sites got the identical inline guard (same pattern, verified by code
review — not separately unit-tested given the heavier existing mock/fixture surface those two functions require, which
would be disproportionate for a 4-line mechanical repeat of an already-tested pattern).

This closes the zombie-creation surface this doc's own Progress Log had already identified as the actual remaining gap —
a more targeted fix than a blanket cadence change, and the one this todo's "regardless of root cause" framing was
actually pointing at once the mechanism was understood.
