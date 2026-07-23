---
doc_type: issue
title: slot 4 repeatedly spawns claude processes that go orphan within minutes
summary:
  While verifying the newly-shipped periodic orphan sweep (ao_worker_lifecycle_reap_2026_07_20.md) live on the central
  VM, slot 4 produced TWO fresh orphaned claude processes within 15 minutes of each other (ages 338s/473s when reaped) —
  every other slot's orphans were multi-day-old debris, not actively recurring. The reap mechanism now catches these
  within minutes regardless, so there is no active harm, but something specific to slot 4's spawn/teardown path is
  producing orphans at a rate no other slot shows.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, worker-lifecycle, tmux, orphan-process, slot4]
related: [/plans/archive/2026_07/ao_worker_lifecycle_reap_2026_07_20.md]
created: 2026-07-20
parent_epic: orchestrator_master
priority: P3
source: [agent-orchestrator central VM activity_log, 2026-07-20 11:15-11:30 UTC]
assigned_vm: NA # filled 2026-07-23 (plan-reconcile Phase 0) — was EMPTY, which is not a valid value; every sibling AO issue doc is NA and this doc is not AO-dispatched
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-20
---

# slot 4 repeatedly spawns claude processes that go orphan within minutes

## What was observed (2026-07-20, live VM)

Live-verifying `orphan_reap.sweep_orphan_processes()` after flipping it to a real (non-dry-run) run
(`agent-orchestrator@95fdf9d`), the `orphan_process_reaped` activity log showed:

- The expected backlog cleanup: 7 multi-day-old orphans across 6 slots (1, 2, 3, 4, 5, 6, 9), ages 21min-72h — the
  ~10-orphan bleed the plan was written to fix.
- Then, within the following 15 minutes, **two more** reaped on slot 4 specifically — PID 3515869 (age 473s) at
  11:21:16, then PID 3609598 (age 338s) at 11:27:18. Both well past `boot_grace_seconds` (300s default) but nowhere near
  multi-day debris — these are FRESH processes that went orphan almost immediately after spawning.

No other slot showed this pattern in the same window. Slot 4 was `status=working` on task
`sports_p2_history_apifootball_2015_to_present-001` at the time (confirmed via the live `slots` table), so its actual
occupant was healthy and untouched by the reap — the orphans are SIBLING processes under the same reused config dir, not
the working occupant itself.

## Why this is worth a look (not urgent)

The periodic sweep (todo 1b of `ao_worker_lifecycle_reap_2026_07_20.md`) now catches these within one tick (~60s)
regardless of root cause, so there is no unaddressed live bleed. But a slot producing short-lived orphans repeatedly,
while no other slot does, points at something slot-4-specific in the spawn/teardown path — worth understanding rather
than just relying on the reap to keep mopping it up.

## Possible directions (not investigated)

- Check slot 4's spawn history (`slot_resume_respawned` / `autospawn_failed` / `watchdog_slot_killed` events scoped to
  slot 4 over a longer window) for a pattern — e.g. a flapping resume, a kick-then-respawn loop, or a role/craft
  mismatch causing repeated re-spawns.
- Check whether slot 4 is unusually prone to the tmux-session-loss class (`tmux_session_lost` events) that leaves a
  process behind when `_reap_pane_tree`'s ancestry walk misses a detached grandchild.
- Compare slot 4's assigned task cadence / plan_ref against other slots — is it simply getting dispatched to far more
  often (more spawn attempts = more chances for the leak), or is the RATE (orphans per spawn) actually higher?

## Acceptance criteria

- Root cause identified (or ruled out as "just cadence") for why slot 4 produces short-lived orphans at a measurably
  higher rate than other slots.
- If a fixable root cause is found (e.g. a kick/respawn race, a pane-tree-reap gap), fix it; if it's just "slot 4 gets
  dispatched more," record that and close as expected/self-mitigated by the periodic sweep.

## Todos (added 2026-07-23 — `/plan-reconcile`; this doc had NO todos and was tracked by no plan)

> **Re-verified 2026-07-23: the MITIGATION is live, the ROOT CAUSE was never investigated.** The periodic orphan-process
> sweep this doc relies on is real and running (`tuning.orphan_sweep_dry_run` flipped to `False` at
> `agent-orchestrator@95fdf9d`, live-verified reaping orphans within ~60s, per the archived
> `ao_worker_lifecycle_reap_2026_07_20.md`). But that same plan records the slot-4-specific cause as "follow-up filed,
> not actioned this session" and points back at THIS doc — which then had no todo, so the follow-up existed nowhere.
> `git log` since 2026-07-20 shows no commit touching slot-4 spawn/teardown.

- [ ] [BACKEND] P3. **Root-cause slot 4's elevated short-lived-orphan rate, or explicitly accept it.** The sweep reaps
      the symptom within ~60s regardless of cause, so this is about knowing whether slot 4 is structurally different.
      Compare `slot_resume_respawned` / `autospawn_failed` / `watchdog_slot_killed` / `tmux_session_lost` rates for slot
      4 against the other slots **normalised per dispatch** (not raw counts — slot 4's volume differs) over a multi-day
      window. **Gate**: either a fixed root cause (code diff + a measured slot-4 orphan-rate drop over 24h) **or** a
      recorded "just cadence, self-mitigated by the periodic sweep" verdict citing the comparison data. Silence is not
      an outcome.
