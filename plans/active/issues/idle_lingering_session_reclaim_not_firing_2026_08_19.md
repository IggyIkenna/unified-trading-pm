---
doc_type: issue
title: >-
  `_reclaim_idle_lingering_sessions` not firing — completed one-shot dispatches leave live
  tmux sessions running for hours, silently shrinking the scheduled-task slot reserve
summary: >-
  Confirmed live 2026-08-19: three scheduled-job (`ag_closeout_auditor`) dispatches on slots
  28/29/30 completed successfully hours earlier (results shipped to
  `unified-trading-pm@ae65a23c08`, each worker's own log says "Completion signaled to the
  orchestrator; slot freed") — the SlotRow status correctly flipped to `idle`, but the
  underlying tmux session was never torn down. `tmux list-sessions` shows all three sessions
  still alive 4+ hours later (created 13:22-13:24 UTC, observed live at ~17:40 UTC), each
  sitting at an interactive Claude Code prompt. This is NOT a missing-teardown bug — reading
  `server/routes/slots_worker.py::_done_one_off`'s own docstring, async teardown is deliberate
  design: "the agent stops on its own after this returns... it reaps the lingering session on
  its next tick." The dedicated reclaim mechanism for exactly this case,
  `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` (`server/worker_liveness_watchdog.py`),
  already exists, is already generic across every one-shot dispatch family (its own docstring
  names review/escalate/conflict_resolver, and the query itself is un-filtered by agent_kind so
  scheduled/plan_health dispatches are in scope by construction) — but is confirmed NOT
  reclaiming these 3 within a timeframe that matters. Root cause not yet found — this is the
  open investigation.

  Operational impact discovered alongside: this is WHY the 4-slot scheduled-task reserve
  (`scheduled_task_reserved_slot_ids()`, slots 27-30 at time of writing) was only delivering 1
  effective slot (27) — `_pick_free_slot`'s live `tmux_spawn.has_session()` check correctly (from
  its own narrow view) treats 28/29/30 as occupied, so new scheduled-job dispatches fell through
  to the general slot pool instead (confirmed: `ag_closeout_auditor` tranches ao/ui/ci/sports
  landed on ordinary slots 1/4/7/14, competing with regular plan-task throughput instead of using
  the reserve built specifically to avoid that).

  2026-08-19 follow-up (same investigation, operator asked for the full intended 3-tier dispatch
  model): re-reading `escalation.py`/`dispatch.py`/`config.py` end-to-end surfaced 2 more
  code-confirmed gaps, distinct from the reclaim bug above and each other — see "Additional
  findings" below. Gap A: `escalation._pick_free_slot` has ZERO reserve-preference logic at all
  (confirmed zero matches for `reserved_slot_ids` in the whole file) — unlike `plan_health`'s
  picker, it never mirrored the 2026-08-16 Finding-1 fix. Gap B: neither picker's general-pool
  fallback checks for competing queued plan-item demand before claiming a non-reserved slot.

  2026-08-19 second follow-up (operator: "we are not hunting the review agent slot 2
  specifically, this is happening with other slots as well"): a fleet-wide 24h kill-reason audit
  (`journalctl -u orchestrator.service`, every `SESSION-TEARDOWN kill_session` line) found the
  "slots getting killed / agents dying mid-task" symptom spans at least 3 distinct mechanisms —
  only ONE confirmed as a destructive bug so far. **CONFIRMED root cause**:
  `ensure_review_agents`'s successful-respawn path (`server/autospawn.py:483-494`) never sets
  `SlotRow.status` back to `working`, so a respawned review slot keeps reading `status=="killed"`
  even while genuinely alive — `WorkerLivenessWatchdog`'s `orphan_session_reclaim` sweep then
  trusts that stale status ~30+ min later and kills the actually-alive session. Confirmed via
  direct log proof on slot 2 (18 kills/24h, clean repeating cycle). See "CONFIRMED:
  orphan_session_reclaim kills genuinely-alive workers" below for the full breakdown, evidence,
  and one-line fix.
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, tmux, slot-lifecycle, worker-liveness-watchdog, scheduled-jobs, orphaned-session, escalation-dispatch, reserve-preference, orphan-session-reclaim, account-failover]
related:
  [
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/server.py,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Interactive session 2026-08-19 (slot 3) — surfaced while investigating why the scheduled-task
  slot reserve (27-30) wasn't being used for new `ag_closeout_auditor` dispatches; operator asked
  directly why the reserve wasn't working, which led to finding 3 of the 4 reserved slots had
  orphaned live sessions from earlier completed work. Escalated by the operator into a fleet-wide
  "unpaused slots idle, agents dying mid-task, slots getting killed" root-cause request, then
  further corrected ("not just slot 2") into the full 24h multi-mechanism audit below.
assigned_role: infra
drift_direction: correct-codex
---

# `_reclaim_idle_lingering_sessions` not firing — orphaned sessions on completed dispatches

## What was measured

Live state as of 2026-08-19 ~17:40 UTC (SSM read-only queries against the orchestrator VM's
`state.db`, plus a direct `tmux list-sessions`/`capture-pane` check):

| slot | `SlotRow.status` | `tmux_session` (DB) | live tmux session? | session created | age at observation |
| ---- | ----------------- | -------------------- | ------------------- | ----------------- | ------------------- |
| 28   | `idle`            | `orch-slot-28`        | **yes**              | 13:22:18 UTC       | ~4h18m               |
| 29   | `idle`            | `orch-slot-29`        | **yes**              | 13:23:18 UTC       | ~4h17m               |
| 30   | `idle`            | `orch-slot-30`        | **yes**              | 13:24:57 UTC       | ~4h15m               |

`tmux capture-pane -t orch-slot-28` shows the worker's OWN log confirming a clean completion:

```
All three docs passed frontmatter/todo-format/line-cap/delete-safety/finalize-coverage
validation and shipped to unified-trading-pm@ae65a23c08. Completion signaled to the
orchestrator; slot freed.

✻ Baked for 35m 22s
────────────────────────────────────────────────────────────────
❯ check status
────────────────────────────────────────────────────────────────
  ⏵⏵ bypass permissions on (shift+tab to cycle) · ← for agents
```

The worker genuinely finished, genuinely signaled `/done`, and the SlotRow genuinely shows
`idle` — but the Claude Code CLI process is still running, sitting at an interactive prompt,
hours later.

## Why this isn't a "missing teardown" bug

`server/routes/slots_worker.py::_done_one_off` (the completion handler) documents the async
teardown as deliberate:

> It deliberately does NOT kill the tmux session synchronously: the agent stops on its own
> after this returns, and because the AgentRow is now `archived` the idle-lingering reclaim is
> no longer carve-out-exempted (`f641968`) — it reaps the lingering session on its next tick and
> AutoSpawn reuses the slot.

The catch-mechanism this refers to, `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions`
(`server/worker_liveness_watchdog.py:1452`), is real, already-shipped code:

- Queries every `SlotRow` with `status IN ('idle', 'stale')` — no `agent_kind`/dispatch-family
  filter, so review, escalate, conflict_resolver, AND scheduled/plan_health one-offs
  (`ag_closeout_auditor` etc.) are ALL in scope by construction, per its own docstring
  ("A one-shot review/escalate/conflict_resolver posts /done... the claude process does NOT
  exit").
- Skips review slots, the fresh-spawn boot-grace window, and (for `stale` only) a pane that's
  actively thinking.
- Increments a disk-persisted per-`(slot_id, last_spawned_at)` tick counter every time it finds
  the SAME lingering session; once the counter reaches `_IDLE_SESSION_RECLAIM_TICKS`, it calls
  `kill_session()` and resets the slot via `reset_slot_worker_state`.

Given slots 28/29/30's `last_spawned_at` has stayed constant across multiple checks spanning
over an hour (ruling out the key silently changing and resetting the counter), and given
4+ hours is far longer than any reasonable tick-count threshold should take to reach, this
points at one of a few real possibilities — **partially updated by the 2026-08-19 second
follow-up below**:

1. ~~The `WorkerLivenessWatchdog` loop itself may not be ticking~~ — **less likely now**: the
   fleet-wide 24h kill audit (see the new section below) confirms `idle_lingering_session_reclaim`
   DOES fire periodically, hitting 9 slots (16,21,27,28,29,30,31,32,33) 46 times in 24h in
   batched ticks roughly every 1-6 hours. The loop is alive; the open question is why the
   INTER-TICK gap leaves genuinely-idle slots looking falsely occupied for that long, not
   whether it ticks at all.
2. `_IDLE_SESSION_RECLAIM_TICKS` may be set far higher than intended, or a per-tick interval
   change elsewhere may have silently stretched the effective wait far past what the
   original design assumed.
3. Something specific to `ag_closeout_auditor`/`plan_health`-family one-offs (as opposed to
   review/escalate) may exempt them from this reclaim despite the query itself being generic —
   e.g. `spawn_base_role` still being set (checked at `_pick_free_slot` time) is a DIFFERENT
   field with a DIFFERENT release-point set than what this reclaimer checks; worth confirming
   these don't interact unexpectedly.

## Operational impact

This is the confirmed root cause of a separate live symptom: the scheduled-task slot reserve
(`config.scheduled_task_reserved_slot_ids()`, currently resolving to slots 27-30) was only
delivering 1 of its 4 slots (27) to new scheduled-job dispatches. `_pick_free_slot`
(`server/plan_health.py`) already has a same-day fix (`ao_fleet_regression_triad_2026_08_16`
Finding 1) to PREFER the reserved pool when free — but 28/29/30 never look free to it, because
`tmux_spawn.has_session()` is a live, real-time check and these sessions are genuinely still
alive. New `ag_closeout_auditor` tranches (ao/ui/ci/sports) fell through to the general slot
pool instead — landing on slots 1/4/7/14, competing with ordinary plan-task throughput instead
of using the capacity specifically reserved to avoid that competition.

## Additional findings (2026-08-19 follow-up) — the reserve-preference model has 2 more gaps

Prompted by the operator asking for the full intended dispatch-priority model: plan items go to
normal slots; scheduled tasks prefer their own reserve and only spill into normal slots when
nothing else needs them; escalations follow the identical rule. Re-reading `escalation.py`,
`dispatch.py`, and `config.py` end-to-end (not just the slice this doc already covered) surfaced
two more, code-confirmed gaps distinct from the tmux-reclaim bug above — both are dispatch-LOGIC
gaps that would exist even with `_reclaim_idle_lingering_sessions` fully fixed, not liveness bugs.

**Gap A — `escalation._pick_free_slot` has ZERO reserve-preference logic, unlike its
`plan_health` sibling.** Confirmed via `grep -n "reserved_slot_ids" server/escalation.py` — zero
matches in the entire file. The function (`server/escalation.py:408`) walks `list_slots(session)`
in plain ascending `slot_id` order and returns the first genuinely-idle candidate; it never
computes or prefers `config.ci_escalation_reserved_slot_ids()`. This is the same class of bug
`ao_fleet_regression_triad_2026_08_16` Finding 1 fixed in `plan_health._pick_free_slot` (see
`server/plan_health.py:212-223`), but that fix was never mirrored onto escalation's own picker.
Net effect: a CI/CD-failure escalation will happily claim a low-numbered "normal" plan-worker
slot while its own dedicated reserve (`DEFAULT_CI_ESCALATION_SLOT_RESERVE = 3`, `config.py:476`)
sits idle, purely because the normal slot sorts first. Distinct from
`ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`, which found the reserve slots themselves
paused/account-exhausted (an availability problem) — this is a preference-ordering problem that
applies even when every reserved slot is healthy and free.

**Gap B — the general-pool fallback (both pickers) is not demand-aware.** Once a reserve is
fully busy, both `plan_health._pick_free_slot` (today) and `escalation._pick_free_slot` (once Gap
A is fixed) fall back to "any other slot that is currently idle," full stop — neither checks
whether the backlog has queued plan-item work waiting on that same slot. A scheduled or
escalation dispatch can therefore win a race against a plan item for a normal slot purely on
pick-order timing, which doesn't match the intended model ("only spill into a normal slot when
plan items don't also want it right now"). A fix would need the fallback to consult existing
queued-backlog-demand signals (`autospawn._has_queued_work`/`_queued_undispatched_count`,
`server/autospawn.py:578,606`) before claiming a non-reserved slot, instead of only checking
physical idleness. Also confirmed while investigating: plan items are already correctly kept OFF
both reserves today — the scheduled reserve via an explicit `_FILTERS` row
(`sched_reserve_dispatch_exclusion_gap_2026_08_16`, `server/dispatch.py:139-177,360-371`) and the
CI reserve via `autospawn._apply_fleet_cap`'s count clamp (`server/autospawn.py:4208`) — so this
gap is one-directional: scheduled/escalation tasks can wrongly land on normal slots, never the
reverse.

**RESOLVED (operator ruling, 2026-08-20)**: the 3-tier dispatch priority is **escalation > plan
items > scheduled tasks** — not symmetric. "If escalator agents' reserved slots are full and
there are still some queued tasks, then they can be dispatched to fleet workers. Scheduled
workers['] reserved slots [being] full, then they should wait and be dispatched when a slot is
available." So the demand-aware gate applies ONLY to `plan_health._pick_free_slot` (scheduled
tasks rank below plan items, must wait) — `escalation._pick_free_slot` is deliberately left
unchanged (escalation outranks plan items, keeps its existing "claim any free slot" fallback).
Shipped: `agent-orchestrator@c63ba376cc`.

## CONFIRMED (2026-08-19, second follow-up): `orphan_session_reclaim` kills genuinely-alive workers — fleet-wide kill audit

Operator pushed back on scoping this to slot 2 alone: "we are not hunting the review agent slot
2 specifically, this is happening with other slots as well." A fleet-wide 24h kill-reason audit
(`journalctl -u orchestrator.service --since "-24 hours" | grep "SESSION-TEARDOWN kill_session"`)
found the "slots getting killed / agents dying mid-task" symptom spans **at least 3 distinct
mechanisms**, graded by confidence:

| `kill_session(reason=...)` | slots hit (24h) | count | confidence |
| --- | --- | --- | --- |
| `orphan_session_reclaim` | slot 2 only | 18 | **CONFIRMED destructive bug** — see below |
| `idle_lingering_session_reclaim` | 16,21,27,28,29,30,31,32,33 | 46 | likely legitimate — this status is set only via an explicit `/done`, unlike `killed` below (see "Why this isn't a missing teardown bug" above for the same mechanism's OTHER symptom, the reserve-starvation delay) |
| `worker_account_unusable_failover` | nearly every slot (1,3,4,7,10,11,14,16,21,28-33) | ~20 | by-design failover; resume-success not yet verified |
| `account_rotation_canonical` | 7,14,21,32,33 | 7 | not yet traced |

### The confirmed bug

`ensure_review_agents`'s successful-respawn path (`server/autospawn.py:483-494`) persists
`claude_session_id`/`tmux_session`/`account_id`/`last_spawned_at` on a successful spawn — but
**never sets `slot_row.status`**. Compare the RESUME-specific path
(`server/autospawn.py:4105-4135`), which correctly does `if slot_row.status == "killed":
slot_row.status = "working"` — `ensure_review_agents` has no equivalent line. So a review slot
that gets killed and successfully respawned keeps reading `status=="killed"` in the DB
indefinitely, even though a genuine, healthy, working agent now occupies it.

`WorkerLivenessWatchdog`'s orphan-session-reclaim sweep (`server/worker_liveness_watchdog.py:
888-918`) is built on exactly one assumption, stated in its own comment: *"status=killed + tmux
still alive" always means a respawn whose boot-paste raised — an empty stuck pane, safe to
kill.* That assumption is false whenever `ensure_review_agents` is the reason `status` is stale.
Roughly 30+ minutes after every successful respawn, the sweep finds the (wrongly) stale
`status=="killed"` row, sees the session is still alive, and kills it — destroying genuinely
in-flight work.

**Direct log proof** (slot 2, the currently-active review slot):

```
13:21:38  agentkeeper_review_succeeded          <- respawn succeeds; status stays "killed" (the bug)
  ... genuinely alive, genuinely working for the next 34 minutes ...
13:56:03  WorkerLivenessWatchdog slot 2: reclaiming orphan session orch-slot-2
          (status=killed + live, spawn_age=2067s)
13:56:03  SESSION-TEARDOWN kill_session session=orch-slot-2 reason=orphan_session_reclaim
```

That single kill cascades exactly as observed: `tmux_session_lost` -> `unexplained_death_forensics`
(correctly finds no OOM — `cgroup_oom_counters` all zero — and no external kill, because there
wasn't one; the orchestrator killed its own worker on purpose, a category `death_forensics.py`
doesn't check) -> `spawn_retry_cap_reached` -> `agentkeeper_review_succeeded` (new respawn, same
bug, status stuck at "killed" again) -> repeat. Confirmed via the full 24h log: this exact cycle
fired 18 times in 24h on slot 2 alone, roughly every 35 minutes to a few hours depending on how
long each respawn survives before the next reclaim tick catches it — not 18 separate mysteries,
one bug on a repeating cadence.

**The fix** is one line: add `slot_row.status = "working"` inside the existing
`if slot_row is not None:` block in `ensure_review_agents`'s success branch (`server/autospawn.py`
around line 490), mirroring the pattern already used at `server/autospawn.py:4120`.

### Why 1/4/10/11 showing idle + "died mid-task" is a SEPARATE story, not this bug

Dashboard showed slots 1/4/10/11 idle with a red "died mid-task" badge and last-message "idle:
447 task(s) blocked on gate-upstream-open:sports_taxonomy_p2_migration_2026_...". Verified both
halves separately — they are two unrelated facts:

- **Why idle right now — legitimate, not a bug.** Slot 1's own `idle_blocker_inferred` diagnostic
  shows 446 blocked tasks, top blockers `gate-upstream-open:sports_taxonomy_p2_migration_2026_08_08`
  (14), `gate-upstream-open:sports_satellite_ao_dispatch_batch14_2026_08_16` (11), and a stuck
  `sports_taxonomy_p4_backfill` task (7). `gate-upstream-open:*` is `regen_backlog_from_plan.py`'s
  real, intentional `depends_on`-derived prerequisite — it stays closed until the referenced
  upstream plan completes. The backlog genuinely has nothing eligible for a generic slot right
  now; this is correct behavior.
- **Why "died mid-task" (historical) — a third, distinct, by-design mechanism.**
  `worker_account_unusable_failover` (`server/autospawn.py:3844-3881`) — confirmed via direct log
  evidence, 3 separate batch-kills today (14:34:23 slots 1/3/4 on account `sub-b-iggy2london`;
  14:43:15 slots 1/4/7/10/11/14/31/32 on account `sub-a-ikenna`; 14:48:37 slots 10/11 on
  `sub-b-iggy2london` again). This mechanism correctly checks `has_session()` before killing and
  only fires when the bound account is confirmed over its dispatch-headroom ceiling —
  **operator-confirmed both accounts are legitimately capacity-blocked right now, not a
  false-positive detection bug**: `sub-a` (ikennaigboaka@gmail.com) is on its 5-hour usage limit,
  `sub-b` is on its weekly usage limit. What's NOT yet verified: whether the worker's in-flight
  WIP actually gets resumed on a fresh account afterward
  (`resume_lifecycle.classify_dead_worker` + the resume-respawn path at
  `server/autospawn.py:4105-4135`), or whether it's effectively lost/requeued-from-scratch — that
  determines whether this by-design mechanism is actually safe in practice, tracked as a
  follow-up below.

## Follow-up

- [x] N. ✅ [BACKEND] P2. **Root-cause + fix for the inter-tick reclaim delay — DONE, shipped
      2026-08-20 (interactive session, slot 3): `agent-orchestrator@b6ca7d1730`.** Live SSM diagnostic (sqlite query + tmux
      list-sessions on the orchestrator VM, ~04:18 UTC) found the symptom was fleet-wide, not
      scoped to 27-30: 10 of 34 real slots (1, 4, 7[review-exempt], 11, 14, 15, 27, 28, 29, 30) were
      simultaneously `idle`/`stale` with a genuinely-live orphaned tmux session, and 18/34 more were
      `paused` (mostly on genuinely weekly-exhausted sub-accounts, confirmed via `account_usage`:
      sub-b/c/d/f all `overage_status=rejected` with `rate_limited_until` spanning 2026-08-20
      through 08-23) — leaving effectively ZERO free slots fleet-wide despite 2 Anthropic
      sub-accounts (sub-a-ikenna at 11%/5%, sub-e-odum2default at 3%/14%) having real headroom.
      `journalctl` for the same window showed `AutoSpawnLoop` repeatedly logging
      `escalation ... queued (no capacity)` — directly matching the operator-reported symptom
      ("2 accounts available, slots available, but nothing dispatching").
      Root-cause (not "loop not ticking" — 0 `tick failed` exceptions in 6h, ruling that out):
      `_tick_once()` ran `_sweep_dirty_slots()`/`_sweep_unpushed_slots()`/
      `_flag_orphaned_sibling_dirty_repos()` — each invoking git subprocesses, several confirmed via
      grep to have NO `subprocess.run` timeout (`_branch_state.py`, `_ahead_push.py`, `_stash.py`)
      — BEFORE `_reclaim_idle_lingering_sessions()` and the other capacity-recovery calls in the
      SAME function. A single lock-contended git op on ANY one slot's worktree (a documented,
      recurring failure mode on this shared multi-agent VM) could stall the whole tick, delaying
      reclaim for every OTHER lingering slot too — matching both the live observation (8 slots with
      wildly different `last_spawned_at` — 00:47 to 03:30 UTC — all reclaiming in the exact SAME
      tick, 04:20:14) and this doc's own earlier audit finding (`idle_lingering_session_reclaim`
      firing in irregular 1-6h batches instead of the ~2-minute cadence `_IDLE_SESSION_RECLAIM_TICKS
      =2` implies). **Fix**: reordered `_tick_once()` so the reclaim/reconcile passes run BEFORE the
      dirty/unpushed git sweeps — a pure reorder, no logic change to any individual function, 114/114
      existing tests still pass. Does not fix a slow git op itself, but stops that unrelated
      slowness from starving capacity-recovery for the rest of the fleet.
- [x] N. ✅ [BACKEND] P2. **Add regression test coverage for the `_tick_once` reorder fix
      (`agent-orchestrator@b6ca7d1730`) — DONE, shipped `agent-orchestrator@c63ba376cc`.**
      That fix's own shipped evidence was "114/114 existing tests still pass" — which only
      proves the reorder didn't break anything ELSE, not that the specific ORDER (the 5
      capacity-recovery reclaim/reconcile calls before the 3 git sweeps) is enforced going
      forward; nothing would fail if a future edit innocently added a call back before the
      reclaim passes. Added `test_tick_once_runs_capacity_recovery_before_git_sweeps`
      (`tests/test_worker_liveness_watchdog.py`) — mocks all 8 calls with a shared
      call-order-recording list, short-circuits via `_daily_cap_reached=True` to stay scoped to
      the ordering question only (not the separately-tested active_slots reap loop), and
      asserts every reclaim/reconcile call's index precedes every git-sweep call's index.
- [x] N. ✅ [OPERATOR] P3. **Kill the 3 currently-orphaned sessions — STALE, moot.** Live-checked
      2026-08-20 ~14:35 UTC: slots 28/29/30 no longer hold the 2026-08-19 orphaned sessions —
      `tmux list-sessions` shows no `orch-slot-28/29/30` session at all, `SlotRow.tmux_session`
      is blank for all three, and `last_spawned_at` is 2026-08-20 (today), not the 08-19
      timestamps this todo was written against. The specific sessions this todo targeted are
      long gone (reclaimed or cycled through since); no manual kill needed.
- [x] N. ✅ [BACKEND] P3. **Sweep for other slots in the same state — STALE, superseded by
      today's spot-check.** Not a full fresh fleet-wide sweep, but the equivalent question was
      re-asked live 2026-08-20: an operator-directed check of slots 10 and 12 (both idle with a
      lingering one-off session, ages 2h+ and 2 days respectively at time of check) found both
      self-resolved within ~20-30 minutes — no live session on either afterward. Live proof the
      reclaim mechanism is actively working, not stuck: the persisted tick-counter
      (`data/state/watchdog_idle_session_ticks.dedup.json`) was fresh (written seconds prior)
      and showed 10 different slots (1,7,8,9,13,22,29,31,32,33) mid-count at `ticks=1`, one tick
      short of the `_IDLE_SESSION_RECLAIM_TICKS=2` threshold — normal in-progress state. The
      original 08-19 symptom (multi-hour orphans) is not reproducing under the now-shipped
      fixes; closing this rather than re-running a redundant full sweep against a moved target.
- [x] N. ✅ [BACKEND] P2. **Give `escalation._pick_free_slot` the same reserve-preference logic
      `plan_health._pick_free_slot` already has — DONE, shipped 2026-08-20 (interactive session,
      slot 3): `agent-orchestrator@aa34262886`.**
      Mirrored `server/plan_health.py:212-223`'s pattern exactly, symmetric: excludes
      `config.scheduled_task_reserved_slot_ids()` (protects that reserve, which had ZERO protection
      from escalations before this fix, not just zero preference) and PREFERS
      `config.ci_escalation_reserved_slot_ids()` among remaining candidates, falling back to any
      other eligible slot when the CI reserve is fully busy. 3 new tests added
      (`tests/test_escalation.py`): prefers-CI-reserve-when-free, excludes-scheduled-reserve, and
      falls-back-past-CI-reserve-when-busy.
- [x] N. ✅ [BACKEND] P2. **Coverage-ratchet blocker resolved + real coverage raised — DONE
      2026-08-20.** The initial 81.32%-vs-82.68%-baseline failure that briefly blocked shipping the
      two fixes above was confirmed a MEASUREMENT FLAKE (a coverage-data merge artifact from
      concurrent pytest/coverage runs sharing this checkout — a clean solo re-run measured 82.87%,
      already above baseline). Per operator direction, raised real coverage anyway rather than just
      re-baselining: 5 parallel agents (server.py 52%→89% + 2 real bugs fixed — 3 background loops
      missing shutdown registration, 17 loops missing from `LoopSupervisor`'s auto-revival list;
      notifications/slack.py 62%→87%; routes/accounts.py 52%→100%; routes/slots_ops.py 55%→97%;
      worker_liveness_watchdog.py 81%→92%) plus `tests/test_slot0_self_clean.py` (0%→covered)
      myself. Final clean full-suite run: 5172 passed, **86.10% total coverage**. Baseline ratcheted
      up 82.68%→86.10% (`agent-orchestrator@29c9f69a`). All 8 commits shipped + synced with origin
      (ahead=0/behind=0): `b6ca7d1730` (watchdog reorder), `aa34262886` (escalation Gap A),
      `d7bc082a`/`c3e61462` (slot0 tests — the latter from a DIFFERENT concurrent AO-dispatched
      agent on the same `slot0_self_cleaning_daemon_2026_08_18.md` plan implementing real `_tick()`
      logic mid-session), `b74c8433` (server.py bugs+tests), `d09344d7` (slack.py tests),
      `91c881ee` (slots_ops.py tests), `0e1def35` (watchdog.py tests), `d2bc7687` (accounts.py
      tests), `29c9f69a` (baseline ratchet).
      **Separate finding — RESOLVED (operator confirmed 2026-08-20)**: an untracked `keys.env`
      (plaintext NVIDIA API key) was found sitting in the agent-orchestrator repo root during this
      session, not gitignored, unrelated to this session's diff — pre-existing debris, likely from
      the NVIDIA/Gemma wiring work (`86cd2066`). Never staged/committed by this session; flagged to
      the operator rather than deleted/moved without authorization. Operator has since moved the
      file — no longer present, nothing further to do here.
- [x] N. ✅ [BACKEND] P2. **Make the scheduled-task fallback demand-aware (Gap B)** — DONE,
      shipped `agent-orchestrator@c63ba376cc`. Resolved per the "RESOLVED (operator ruling,
      2026-08-20)" note under Gap B above, in this same doc
      (`/plans/active/issues/idle_lingering_session_reclaim_not_firing_2026_08_19.md`) —
      asymmetrically (escalation > plan items > scheduled): only `plan_health._pick_free_slot`'s
      fallback got the demand check
      (`autospawn.has_queued_backlog_work(session)`, a new public wrapper around the
      already-private `_has_queued_work` — added to avoid a `basedpyright reportPrivateUsage`
      cross-module violation, never a `# type: ignore` suppression); when the scheduled reserve
      is full AND the backlog has queued plan-item work, `_pick_free_slot` now returns `None`
      (the caller's existing no-capacity queue path takes over) instead of stealing a normal
      slot. `escalation._pick_free_slot` deliberately left unchanged. 2 new tests
      (`tests/test_plan_health.py`): waits when plan items are queued, still uses a normal slot
      when nothing competes for it. 6 pre-existing tests needed a
      `has_queued_backlog_work=MagicMock(return_value=False)` default added to their patch
      blocks (the shared `_patches()` fixture plus 5 tests with their own inline blocks) so the
      new gate didn't silently change their unrelated scenarios.
- [x] N. ✅ [BACKEND] P1. **Fix the confirmed `ensure_review_agents` bug** — DONE:
      `agent-orchestrator@ad70a9465f`. Added `slot_row.status = "working"` to the
      successful-respawn branch (`server/autospawn.py`, inside the `if spawn_ok:` block),
      mirroring the resume-respawn path's existing `if slot_row.status == "killed": ...`
      pattern (`server/autospawn.py:4120`) but set unconditionally, since any prior status is
      superseded by "a live worker now exists". Added
      `test_ensure_review_agents_flips_status_to_working_on_successful_respawn`
      (`tests/test_autospawn.py`), pinning the regression directly: sets `configured_slot.status
      = "killed"` before a mocked successful respawn, asserts it flips to `"working"`. Full
      fleet quality-gates green (4901 passed, coverage 82.73%, ratchet up available) before
      shipping.
- [ ] [BACKEND] P2. **Finish tracing `worker_account_unusable_failover`'s resume-success —
      partially confirmed working, not fully proven for every case.** Live-checked 2026-08-20
      ~00:20 UTC after the account pool churned further (a 3rd account, `sub-h-igboestates`,
      joined `sub-a`/`sub-b` as exhausted, at 20:20:03 — confirming this is genuine multi-account
      pool pressure, not a one-off): `classify_dead_worker` (`server/resume_lifecycle.py:47`) DID
      fire and correctly mark `slot_resume_pending` for slot 11 (23:45:29) and slot 10
      (00:15:49), both `trigger: "tmux_pruner"`, both carrying `dirty_repos` (WIP-aware),
      `max_attempts: 2`. Both slots currently still show their `current_task` bound (not
      released/lost) and slot 11 is `status: working` again — consistent with a successful
      resume, not data loss. **Not yet fully confirmed**: slots 1 and 4 show NO
      `slot_resume_pending` event in the same 8h window despite also being failover-killed
      repeatedly — need to determine whether that's because they had no task in flight at kill
      time (`classify_dead_worker`'s first check, `task_id is None -> requeue`, a benign
      no-op case) or a genuine gap. Also worth noting: all 4 slots are currently running on
      `codex-luna` (a non-Anthropic bridge account), not a healthy Anthropic sub-account — at
      last check 5 of 8 Anthropic sub-accounts were `rate_limited`/`high_usage`
      (only `sub-a`/`sub-e` healthy) — real pool-wide pressure, matching operator confirmation.
- [ ] [BACKEND] P3. **Trace `account_rotation_canonical`** (7 kills/24h across slots
      7,14,21,32,33) — not yet investigated at all; lowest priority of the 4 mechanisms in the
      breakdown table above since its volume is smallest, but still unconfirmed.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` — capacity sizing / reserve
  mechanism this bug's operational impact hits.
- **context-scout 2026-08-20**: populated context_scope (7 entries).
- **context-scout 2026-08-20 (correction)**: COUNT_MISMATCH resolved — the prior marker claimed 7 entries but the
  live frontmatter actually held 9, all source-only. Fully re-derived: now 6 entries, trimmed to the files each
  still-open priority item (root-cause fix, demand-aware fallback, account_rotation_canonical trace) actually
  edits, plus the doc's own "## Codex SSOTs" citation which had been missing from context_scope entirely.
- **na-eligibility-audit 2026-08-21 (ao tranche batch 3/3)**: KEEP-NA, valid — read end-to-end. The 2 remaining open items (finish tracing `worker_account_unusable_failover`'s resume-success for slots 1/4; trace `account_rotation_canonical`) are live-dispatch-critical-path AO account-failover/resume investigations, still genuinely mid-characterization per the doc's own 2026-08-20 entry ("not yet fully confirmed... need to determine whether that's because they had no task in flight... or a genuine gap"). Not bounded to a single determinable outcome without further live infra tracing — err toward KEEP-NA per this class of AO-internals investigation.
