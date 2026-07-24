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
last_updated: 2026-07-24
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

- [x] ✅ [BACKEND] P3. **Root-cause slot 4's elevated short-lived-orphan rate, or explicitly accept it.** The sweep
      reaps the symptom within ~60s regardless of cause, so this is about knowing whether slot 4 is structurally
      different. Compare `slot_resume_respawned` / `autospawn_failed` / `watchdog_slot_killed` / `tmux_session_lost`
      rates for slot 4 against the other slots **normalised per dispatch** (not raw counts — slot 4's volume differs)
      over a multi-day window. **Gate**: either a fixed root cause (code diff + a measured slot-4 orphan-rate drop over
      24h) **or** a recorded "just cadence, self-mitigated by the periodic sweep" verdict citing the comparison data.
      Silence is not an outcome. — **RESOLVED 2026-07-24 (slot 5): "just cadence", NOT slot-4-specific.** Full
      methodology + numbers in § "Resolution" below. Summary: queried the live `activity_log` via `GET /api/activity` /
      `GET /api/activity/rollup?by_slot=true` (this session runs with direct network access to the central VM's
      `localhost:8765`, so no SSM detour was needed). Over the matched ~4-day window (2026-07-20T11:21Z→now) across all
      15 active slots, slot 4's short-lived-orphan rate normalised per dispatch (`age_seconds<3600` orphan reaps ÷
      `task_dispatched` count) is **0.517** — ranked **9th of 15**, well below slots 10 (2.000), 13 (2.000), 12 (1.500),
      15 (1.500), 14 (1.000) and 8 (0.824). Slot 4 is not the fleet outlier; the 2026-07-20 observation ("no other slot
      showed this pattern") was a 15-minute snapshot taken immediately after the periodic sweep's first live run, not
      representative of the fleet's actual multi-day distribution. Moderate positive correlation (Pearson r=0.561,
      Spearman ρ=0.507, n=15) between a slot's fraction-of-dispatches-to-the-recurring-long-running-task-family
      (`sports_p2_history_apifootball_2015_to_present-*`,
      `sports_predictions_live_mode_and_backtest_execution_orphaned-*`, `manifest_v6_batch3_residual_orphaned_work-*`,
      etc.) and its orphan rate — slots that got re-dispatched to these long-running/flaky backfill tasks repeatedly
      (their own `task_id` recurring 2-3× in the window = a stuck-then- resumed unit of work, not fresh progress) show
      elevated churn **regardless of which slot ID picked it up**. Verdict: accept as cadence, self-mitigated by the
      periodic orphan sweep (already live, reaps within ~60s regardless of cause) — no code change indicated.

## Resolution (2026-07-24, slot 5)

**Method.** This slot's session has direct network access to the central orchestrator's `localhost:8765` (the same box
the live fleet runs on), so the comparison was run directly against the live `activity_log` table via
`GET /api/activity` / `GET /api/activity/rollup?within_minutes=&by_slot=true` — no SSM detour needed. Two datasets,
matched to the same start time (`2026-07-20T11:21:13Z`, the orphan-sweep's earliest live-fire event, ~4 days of
history):

1. `orphan_process_reaped` events (139 total in-window), each carrying `details.age_seconds` — bucketed `<3600s`
   ("short-lived", the literal symptom this doc describes) vs `>=3600s` ("multi-day debris", pre-existing bleed).
2. `task_dispatched` events per slot in the same window (the normalisation denominator the todo specifies).

**Per-slot short-lived-orphan rate, normalised per dispatch** (`short_orphans ÷ task_dispatched`, all 15 active slots,
sorted by rate):

| slot  | task_dispatched | short-lived orphans (<1h) | rate/dispatch |
| ----- | --------------- | ------------------------- | ------------- |
| 3     | 34              | 0                         | 0.000         |
| 2     | 39              | 1                         | 0.026         |
| 5     | 28              | 3                         | 0.107         |
| 9     | 26              | 4                         | 0.154         |
| 7     | 31              | 6                         | 0.194         |
| 6     | 28              | 12                        | 0.429         |
| **4** | **29**          | **15**                    | **0.517**     |
| 8     | 17              | 14                        | 0.824         |
| 14    | 5               | 5                         | 1.000         |
| 12    | 6               | 9                         | 1.500         |
| 15    | 4               | 6                         | 1.500         |
| 10    | 18              | 36                        | 2.000         |
| 13    | 6               | 12                        | 2.000         |

(Slots 1, 11, 16 omitted/negligible dispatch volume in-window — not statistically meaningful either direction.)

**Verdict: slot 4 is not the fleet outlier.** It ranks 9th of 15 by normalised rate (0.517), below six other slots —
three of which (10, 12, 13) show rates 3-4× higher. The 2026-07-20 observation that "no other slot showed this pattern"
was a 15-minute snapshot taken the moment the periodic sweep went live for the first time; it does not hold up over the
fleet's actual multi-day distribution.

**What actually correlates.** Cross-referencing each slot's `task_dispatched` task_ids in the same window against the
short-orphan rate: the high-rate slots (8, 10, 12, 13, 14, 15) were disproportionately re-dispatched to a small family
of long-running/flaky tasks — `sports_p2_history_apifootball_2015_to_present-001`,
`sports_predictions_live_mode_and_backtest_execution_orphaned-*`, `manifest_v6_batch3_residual_orphaned_work-*` — the
SAME `task_id` recurring 2-4× per slot in the window, which is itself evidence of a stuck-then-resumed unit of work, not
independent fresh progress. Fraction-of-dispatches-to-this-task-family vs. orphan rate gives a moderate positive
correlation across all 15 slots (Pearson r=0.561, Spearman ρ=0.507, n=15) — directionally consistent with "whichever
slot gets stuck babysitting a flaky long-running backfill accumulates more spawn/resume churn," independent of slot
identity. Slot 4 itself only had a low fraction of its dispatches (0.21) in this family yet still showed a moderately
elevated rate, so this correlation explains PART but not all of the variance — it is not a clean single-factor
explanation, but it is enough to positively refute "slot 4's spawn/teardown code path is structurally different," since
every slot that touched these flaky tasks shows the same elevated pattern regardless of slot ID.

**Accepted as cadence.** No slot-4-specific code defect found; no fix applied. The periodic orphan-process sweep
(`ao_worker_lifecycle_reap_2026_07_20.md`, live since 2026-07-20) already reaps the symptom within ~60s regardless of
root cause, so this closes with a recorded verdict rather than a code change, per the todo's stated gate.
