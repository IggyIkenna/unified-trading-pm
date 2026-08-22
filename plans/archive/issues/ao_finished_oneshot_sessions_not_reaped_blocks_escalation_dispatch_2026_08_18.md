---
doc_type: issue
title: >-
  Finished one-shot escalation sessions (slots 31/32/33) never torn down — `_pick_free_slot` sees them
  as occupied, so new escalations retry "no free configured slot" indefinitely despite a genuinely
  finished, idle worker sitting in every reserved slot
summary: >-
  Live-confirmed 2026-08-18: escalation `agt-3896a8` (market-tick-data-service, data_pipeline_failure)
  sat `status=queued`, `last_error="no free configured slot to dispatch escalation onto"` for 28
  attempts / ~28 minutes while the CI-escalation reserve (slots 32/33) and the sched reserve (29-31)
  all showed `status: idle` / `worker_alive: false` in the dashboard. Direct SSM `tmux list-sessions`
  + `tmux capture-pane` on the orchestrator VM showed all 5 slots have a LIVE tmux session right now,
  each one sitting at an idle interactive prompt (`❯`) having already finished real one-shot work
  (a `plan_reconciler` run on 31, a DP-monitor redeploy fix on 32, the exact `DP-WATCHER-006`
  escalation `agt-0c542c` on 33). `escalation.py::_pick_free_slot` requires
  `not tmux_spawn.has_session(...)` to treat a slot as free — by design, correctly refusing to hijack
  an occupied slot — but the boot prompt's own "COMPLETE THEN STOP" contract states `/done` triggers
  "the reaper cleans your session," and that isn't happening: a genuinely-finished one-shot worker's
  tmux session survives indefinitely, permanently removing that slot from the free pool until
  something else notices and kills it.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, escalation, slot-reclaim, reaper, tmux, one-shot-lifecycle, capacity]
related:
  [
    /plans/archive/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-18"
parent_epic: agent_operating_framework_master
# reclassified NA -> planning 2026-08-19 (na-eligibility-audit, ao tranche) — conflict-check CLEAR
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: none
source: >-
  Interactive session 2026-08-18, slot 3 — operator noticed a live dashboard screenshot showing
  slots #28-33/#9001 all IDLE with "✓ done" badges while a real escalation sat queued 28 attempts
  waiting for a free slot, and pushed back on my earlier (incomplete) account-exhaustion framing.
  Direct code read of `escalation.py::_pick_free_slot` + live `tmux list-sessions`/`capture-pane`
  on the orchestrator VM confirmed the real mechanism.
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/dedup_state.py,
    agent-orchestrator/server/escalation.py,
    /plans/archive/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
    /plans/active/issues/ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18_finalize_2026_08_19.md,
  ]
---

> **📦 ARCHIVED 2026-08-22** (issues-corpus executable-queue dispatch, running the finalize twin's own gated
> archival todo) — all 3 todos done, live re-verified 2026-08-20. 0 open todos, no lock.

# Finished one-shot sessions never reaped — blocks escalation dispatch onto their own slots

## What I found

`escalation.py::_pick_free_slot`'s docstring is explicit about its own contract: a slot is "free" only
when it has **no** `orch-slot-N` tmux session at all — `killed` status is fine (that's exactly the
capacity a watchdog reap frees), but a live session, regardless of what's happening inside it,
disqualifies the slot unconditionally. This is correct, deliberate design (protects against
hijacking a slot mid-work).

The gap is on the OTHER side: `agents/data_pipeline_failure.md`'s boot prompt (and presumably every
other one-shot escalation boot prompt) tells the worker that calling `/done` with
`one_shot_complete: true` causes "the backend archives your AgentRow `lifecycle-complete`, frees
your slot, and the reaper cleans your session" — i.e., the WORKER's job is just to call `/done`;
tearing down the tmux session is supposed to be someone else's (the reaper's) job, asynchronously.

Live-confirmed this isn't happening reliably. All three reserve-pool slots I inspected
(`orch-slot-31`, `orch-slot-32`, `orch-slot-33`) have live tmux sessions RIGHT NOW, each sitting at
an idle `❯` prompt having already finished a real piece of work:

- **Slot 31**: finished a `plan_reconciler` dispatch (shipped `unified-trading-pm@e1c1634518`),
  ended with `✻ Sautéed for 15m 56s`, sitting at an empty prompt since.
- **Slot 32**: finished a DP-monitor Cloud Build redeploy fix, then received a FOLLOW-UP interactive
  prompt ("check the agent-orchestrator dashboard for any other open escalations") — not just idle,
  actually mid-conversation with something/someone.
- **Slot 33**: finished escalation `agt-0c542c` (DP-WATCHER-006, `deployment-service@03be2c2ada` +
  `unified-trading-pm@81a76ef37c`), sitting at an empty prompt since.

Meanwhile `GET /api/escalations/active` showed a genuinely NEW escalation, `agt-3896a8`
(market-tick-data-service, `data_pipeline_failure`), stuck `status=queued`, `attempts=28`,
`last_error="no free configured slot to dispatch escalation onto"` — every one of its 28 dispatch
attempts correctly found zero slots satisfying `_pick_free_slot`'s no-live-session requirement,
because the pool's actual free capacity is smaller than the dashboard's `status`/`worker_alive`
fields suggest. The DB fields say "idle"; the physical tmux state says "occupied" — the two have
drifted apart.

## Why it matters

This silently shrinks the effective escalation-reserve pool over time: every one-shot worker that
finishes cleanly (the GOOD outcome) still permanently removes its own slot from the free pool unless
something else notices and kills the leftover session. Under sustained load this can degrade toward
the exact "no free configured slot" starvation already documented in the sibling issue
(`ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`) — but THAT doc's root cause was the reserve
slots being administratively `paused` on an exhausted account; THIS is a distinct mechanism (slots
that were never paused, never exhausted, just never reaped after finishing) producing the identical
user-visible symptom. Conflating the two would misdiagnose a future recurrence.

## Recommended decision

Needs a real investigation into "the reaper," not a guess:

- Identify the actual reaper/pruner mechanism this boot-prompt comment refers to (`tmux_pruner.py`
  is the obvious candidate — confirm it's the right module, not assumed) and determine why it isn't
  clearing these three sessions: is it not running/ticking, does it require a signal this `/done`
  call isn't sending, or does it deliberately leave a session alive for some reason (e.g. giving an
  operator a window to review the transcript) that conflicts with the free-pool's needs?
- Slot 32's mid-conversation follow-up prompt suggests at least SOME of these sessions are being
  kept alive deliberately (an operator or another process continuing to use them) rather than purely
  a reaper bug — worth distinguishing "reaper isn't running" from "reaper is correctly NOT killing a
  session someone is still using" before proposing a fix, since a blind more-aggressive reaper could
  kill a session mid-legitimate-use.
- Consider whether a stuck-escalation retry (`agt-3896a8`-style, N attempts with the identical
  no-free-slot error) should itself trigger a check for exactly this condition (idle-at-prompt,
  post-`/done`, tmux-still-alive) as a distinct, page-worthy signal, separate from genuine account
  exhaustion.

## Root cause investigation (2026-08-18, later same day)

**`tmux_pruner.py` is confirmed NOT the reaper the boot prompt refers to** — it only clears the
`tmux_session` DB field for a session already confirmed DEAD (`has_session()` returns false); it
never proactively kills a live-but-finished session. The real reaper for "finished one-shot, /done
called, tmux still alive" is `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions`
(`server/worker_liveness_watchdog.py`), gated by `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED`
(`server/config.py`) and ticked from `_tick_once` every `watchdog_interval_seconds` (default 60s).
It requires `tuning.watchdog_idle_session_ticks` (default 2) CONSECUTIVE ticks of
status-in-(idle,stale)-with-a-live-tmux-session before it tmux-kills the session and resets the row.

**Live-confirmed via read-only SSM on the `planning` VM (i-0c9b283b31d6b5ca7)**:

- `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true` is explicitly set in both the systemd unit's
  `Environment=` and the live process's own `/proc/<pid>/environ` — the watchdog is genuinely
  enabled and ticking (many `WorkerLivenessWatchdog started (interval=60s)` journal lines all day).
  No `ORCHESTRATOR_REVIEW_SLOTS` / idle-tick-threshold override is set — config on this VM matches
  code defaults exactly (rules out a review-slot or threshold misconfiguration).
- The reclaim mechanism DOES fire successfully at times — journalctl shows bursts of
  `reclaiming idle lingering session ... ticks=2 -> freeing slot` hitting multiple slots at once
  (e.g. 02:06, 14:18, 15:30, 17:20 UTC on 2026-08-18), including slots 31/32/33 more than once.
- **But right now (22:11 UTC, same day), slots 29 and 30 are STILL `status=idle` with a confirmed-
  LIVE tmux session** (`tmux has-session` exit=0, direct check, not just the DB field) — sitting
  idle since `last_spawned_at` 06:21:40 / 06:22:41 UTC, i.e. **~15h50m and ~15h49m respectively**,
  never reclaimed despite being far past every eligibility check. Slots 31/32 have been idle+live
  since 17:24:30 / 17:35:59 (~4h35m/~4h25m at check time). The queued escalation `agt-3896a8`
  (market-tick-data-service) was STILL retrying `no free configured slot` continuously from
  18:35:13 through at least 22:03:11 — the starvation this issue describes is not a one-off snapshot,
  it is ongoing, hours later, while the watchdog is confirmed running.
- **Confirmed root-causeable contributing bug**: `WorkerLivenessWatchdog._idle_session_ticks` (the
  counter that must reach 2 before a lingering session is killed) was a PURE in-memory `dict`, never
  persisted to disk. `ao-self-pull.sh` restarts `orchestrator.service` on every LDR HEAD move (root
  cron every 2 min) — live journalctl shows the orchestrator process restarting roughly 15-30+ times
  over the day, at intervals ranging from a few minutes to a couple of hours. Every restart wiped
  ALL in-flight reclaim progress back to zero, so a slot's tick counter had to survive an
  UNINTERRUPTED ~60-120s window post-restart to ever cross the threshold. This is the **exact same
  bug class already fixed once in this same file** for `_heartbeat_resume_count` and `_burn_flagged`
  (`ao_worker_context_saturation_unrecoverable_2026_08_06`: "Prod slot 3 hit exactly that... resumed
  at 12:41:15Z and the server restarted at 12:45:22Z, re-arming an unbounded resume loop four
  minutes later") — `_idle_session_ticks` was simply never given the same treatment.
- **Also confirmed and fixed as a same-turn finding** (HARD RULE: a misleading doc/comment is a
  finding): three separate comments — `config.py`'s field comment, this module's own docstring, and
  `server.py`'s inline comment at the `watchdog.start()` call site — all claimed
  `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED` "defaults OFF/false". The actual code default has been
  `True` (`BoolEnvTrue`, unset/blank resolves True) since commit `33d0696b` (2026-07-29, "enable
  worker watchdog by default") — the comments simply never got updated across three weeks. Not
  itself the bug (the live VM explicitly sets the env var anyway), but exactly the kind of stale
  claim that costs the next investigator a live-verification detour, so corrected in the same commit.

**Honest caveat — NOT fully closed**: persisting the tick counter directly closes a confirmed,
real, restart-interrupted-progress bug and should measurably shrink how often a slot's reclaim
progress is discarded. It does **not** fully explain every observation above on its own — e.g. one
observed reclaim burst (14:18:51) fired ~70 minutes into a SINGLE uninterrupted process lifetime
(PID `989629`, started 13:08:28) rather than within the first ~2 minutes, which the restart-wipe
theory alone does not account for. If slots keep sitting idle+live for many hours AFTER this fix has
had time to deploy (`ao-self-pull.sh` picks it up on its next 2-min cron tick), the next
investigator should add temporary DEBUG-level per-tick logging of `ticks` progress inside
`_reclaim_idle_lingering_sessions` — today there is ZERO observability into sub-threshold
accumulation from outside (no log line fires until the kill itself), which was the single biggest
blind spot in this investigation.

**Fix shipped**: `agent-orchestrator@89ca5609e0` (quickmerge, landed on `live-defi-rollout`) —
`server/worker_liveness_watchdog.py` + `server/dedup_state.py` (new
`watchdog_idle_session_ticks_path()` + disk-backed load/persist, mirroring the existing
`_heartbeat_resume_count` pattern exactly) + `server/config.py` + `server/server.py` (stale-comment
corrections). Quality gate green (4118 passed) before shipping.

## Todos

- [x] [SCRIPT] P1. Identify why the finished one-shot sessions on slots 31/32/33 (and check the rest
      of the fleet for the same pattern, not just these three) still have live tmux sessions after
      `/done` — read `tmux_pruner.py` (or whichever module is actually responsible) and determine
      root cause live, not from the docstring's stated intent alone. Repo: agent-orchestrator. —
      DONE: `tmux_pruner.py` is NOT it; the real mechanism is
      `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions`, confirmed enabled+ticking live but
      failing to reclaim genuinely-eligible slots for many hours at a stretch (see Root cause
      investigation above). agent-orchestrator (no code change for this todo — investigation only).
- [x] [SCRIPT] P2. Once root-caused, fix it so a one-shot worker's slot genuinely returns to
      `_pick_free_slot`'s free pool promptly after `/done` (bounded by whatever grace period, if any,
      is intentional for post-completion review) — cite the fix + a live re-verification that a
      subsequently-queued escalation actually claims a freshly-reaped slot. Repo: agent-orchestrator.
      — PARTIAL: fixed the confirmed in-memory-counter-wiped-by-restart bug at
      `agent-orchestrator@89ca5609e0` (disk-persists `_idle_session_ticks`, mirroring the
      already-fixed `_heartbeat_resume_count` sibling bug). NOT yet live-re-verified post-deploy
      (this session did not wait out `ao-self-pull.sh`'s next cron tick + a subsequent multi-hour
      observation window) — per the Honest caveat above, this fix may not be the complete
      explanation. See follow-up todo below.
- [x] ✅ [SCRIPT] P2. Live re-verify AFTER `agent-orchestrator@89ca5609e0` has deployed to the
      `planning` VM (`ao-self-pull.sh` picks it up within ~2min of the LDR HEAD move) — confirm via
      SSM that slots sitting idle+live for >2 reclaim-ticks worth of uninterrupted uptime are
      actually being torn down, and that a queued escalation reliably claims a freshly-reaped
      reserve slot. If the multi-hour stalls recur despite the fix, add temporary DEBUG-level
      per-tick logging of `ticks` progress in `_reclaim_idle_lingering_sessions` (currently zero
      observability into sub-threshold accumulation) as the next diagnostic step. Repo:
      agent-orchestrator. — VERIFIED 2026-08-20 (worker slot 21, live on the planning VM, not
      SSM — colocated): fix deployed + running — orchestrator PID 2004993 at
      `47e1b04e` (⊇ `89ca5609e0`), started 14:42:35 UTC, `ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true`
      in process env; disk-persisted `watchdog_idle_session_ticks.dedup.json` live with
      per-occupant `(slot_id, last_spawned_at)` keys (slots 11/4 at tick 1 at check time). Reclaim
      post-restart PROVEN: the restarted process's first tick (14:42:51–55) tore down 10 lingering
      idle+live sessions (`SESSION-TEARDOWN kill_session ... reason=idle_lingering_session_reclaim`)
      incl. the CI-escalation reserve slots 31/32/33 — pre-restart tick accumulation survived the
      14:42:35 restart via the persisted counter (old in-memory-only code would have wiped it,
      exactly the 15h-stall mechanism). Escalation claims healthy: active rows = 2 dispatched
      (agt-483032→slot 11, agt-500b74→slot 8) + 2 queued on repo-collision guard
      (`execution-service already active on another slot`), NOT `no free configured slot`; reserve
      slot 31 freshly-reaped then re-claimed (re-spawned 14:54:43, now working). Multi-hour stalls
      did NOT recur, so the conditional DEBUG-logging was NOT added. Residual observation (not this
      fix's domain): `_tick_once` persist mtime frozen ~14min at check point to a slow git-sweep
      stall — already tracked in `plans/active/issues/idle_lingering_session_reclaim_not_firing_2026_08_19.md`.
- **na-eligibility-audit 2026-08-19 (ao tranche)**: RECLASSIFY (whole-doc) -> `assigned_vm: planning`. 2 of 3 todos already shipped with evidence; sole remaining todo (live re-verify + conditional DEBUG logging) is bounded/deterministic. Conflict-check clear: no active planning doc in agent_operating_framework_master claims this ground; the naming-adjacent `one_shot_complete_session_ownership_desync_2026_08_08.md` covers a DIFFERENT, opposite-direction reaper bug (idle-reap over-reclaiming vs. this doc's under-reclaiming) and is already fully shipped/gated by its own finalize plan. Companion gated finalize: `ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18_finalize_2026_08_19.md`.
- **context-scout 2026-08-19**: populated context_scope (5 entries).

## Progress Log

- **2026-08-20 (worker slot 21, AO-dispatched P2 live re-verify)**: ALL three todos now DONE.
  The P2 re-verify is flipped above with full evidence — fix deployed + running (PID 2004993 @
  `47e1b04e` ⊇ `89ca5609e0`), disk-persisted tick counter live, first tick post-restart tore down
  the lingering CI-escalation reserve slots 31/32/33 (+7 others), escalation dispatch healthy (no
  `no free configured slot` starvation), freshly-reaped reserve slot 31 re-claimed. Multi-hour
  stalls did not recur, so the conditional DEBUG-logging step was correctly NOT taken. Residual
  (separate, pre-tracked): slow git-sweep stalls can delay `_tick_once` — see
  `plans/active/issues/idle_lingering_session_reclaim_not_firing_2026_08_19.md`; not a blocker to
  this doc closing. This issue gates
  `ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18_finalize_2026_08_19.md`
  (depends_on + gate_on_depends) — that finalize can now run its reconcile + archival steps.
