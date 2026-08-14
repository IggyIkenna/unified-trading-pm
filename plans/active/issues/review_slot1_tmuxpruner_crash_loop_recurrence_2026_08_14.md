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
status: open
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
resolved_by:
last_updated: 2026-08-14
locked_since:
context_scope:
  [agent-orchestrator/server/worker_liveness_watchdog.py, agent-orchestrator/server/worker_liveness/_auth_failover.py]
---

# Review-slot-1 crash-loop recurrence

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

- [ ] [BACKEND] P1. **Trace why `WorkerLivenessWatchdog`'s Trigger 3 (heartbeat-silent, 900s/15min threshold,
      `worker_liveness_watchdog.py` ~line 1050-1103) did not act within its own documented budget for the 2026-08-14
      01:02:38Z slot-1 spawn** — actual detection came ~26min late via the separate `orphan_session_reclaim` sweep
      instead (~line 839-855). Check specifically whether the TWO `orchestrator.service` restarts inside the 01:15-
      01:30Z gap reset in-memory gating state (`_recently_nudged`'s `_last_nudge_at`, `_stuck_ticks`, `_prev_panes`, or
      similar) in a way that delays Trigger 3's own evaluation of a slot across a restart. If confirmed: either make the
      relevant state DB-persisted (survives a restart) or have the watchdog re-evaluate every currently-silent slot
      immediately on its own startup rather than waiting for its next natural tick. Cross-reference the archived doc's
      own restart-correlation finding (9-24% of kills within 2-5min of a restart) — likely the same underlying
      mechanism, not a second coincidence. Repo: agent-orchestrator.
- [ ] [BACKEND] P2. **Once the above is understood, decide whether `orphan_session_reclaim`'s own sweep cadence should
      independently be tightened** as a backstop regardless of the Trigger-3 root cause — a slot sitting DB-status
      `killed` while genuinely still alive should be reclaimed on a much shorter cycle than "whenever the next full
      sweep happens to run," since it structurally blocks a fresh respawn attempt for its entire duration. Repo:
      agent-orchestrator.
