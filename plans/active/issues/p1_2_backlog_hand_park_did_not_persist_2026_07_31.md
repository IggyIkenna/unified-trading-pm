---
doc_type: issue
title:
  "Main's hand-applied park (priority:999 + priority_override:true + false prereq p1-2-preconditions-met) on
  live_event_log_warm_sink_recovery_and_cold_compaction-011 did not persist — task redispatched to a 4th/5th worker
  within ~25 minutes of the park being recorded as applied"
summary: >-
  Main answered BLK-085fef5e at 2026-07-31T22:30:26Z with a "final" disposition applying the sanctioned RULES.md §4 park
  recipe to `live_event_log_warm_sink_recovery_and_cold_compaction-011` (the P1.2 daily-determinism-recheck todo, doubly
  time-gated + paper-run-gated, already redispatched to 3 workers in ~90 minutes with zero possible progress). The
  activity log records the park as applied (`priority:999 + priority_override:true`, condition `p1-2-preconditions-met`
  set `false` by main at 22:29:54Z) and a slot-13 session was then killed with `resume_decision: requeue` at 22:41:01Z.
  As of this worker's dispatch at ~22:55:42Z (slot 15, `dispatch_reason: "resume"`, `already_in_progress: true`), the
  LIVE `agent-orchestrator/data/config/backlog.yaml` entry for this task id reads `priority: 20`, `priority_override:
  false`, `prereqs.prerequisites: []` — i.e. the park is fully absent, not partially reverted. This is either a
  recurrence of the `priority_override`-not-durable class fixed in `backlog_regen_drops_handtuned_prereqs_2026_07_12.md`
  (Defect B, `agent-orchestrator@8dd5763`), or the hand-edit simply never reached disk despite main's blocked-answer
  text claiming it had. Either way, the ONE documented mechanism for stopping this exact redispatch-churn class did not
  hold, and the underlying decision (BLK-085fef5e, Option A, disposition: final) is at risk of continuing to burn
  worker-slot cycles until re-applied and its durability actually re-verified.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [backlog, regen, prereqs, park, redispatch-churn, orchestrator-bug, priority_override]
related:
  [
    /plans/archive/issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md,
    /plans/active/live_event_log_warm_sink_recovery_and_cold_compaction_2026_07_31.md,
    /plans/active/issues/no_active_paper_run_blocks_p1_2_determinism_recheck_2026_07_31.md,
  ]
created: "2026-07-31"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Observed 2026-07-31T22:55Z (slot 15) on dispatch of live_event_log_warm_sink_recovery_and_cold_compaction-011: live
  read of agent-orchestrator/data/config/backlog.yaml shows priority=20/priority_override=false/prereqs=[] despite
  main's 22:30:26Z blocked-answer (BLK-085fef5e) stating the park (priority:999/priority_override:true/false prereq
  p1-2-preconditions-met) had been applied and verified via the blockers endpoint.
---

# P1.2's hand-applied backlog park did not persist

## What I found

Timeline (all `2026-07-31`, all times UTC, reconstructed from `/api/activity`):

- `22:20Z` — slot-6 re-confirms both P1.2 preconditions still unmet (66 min elapsed of the required 24h; zero active
  paper/colocated compute+Cloud-Run trading BINANCE-FUTURES/ASTER/OKX-FUTURES) and files `/blocked` (`BLK-085fef5e`)
  citing 3 consecutive zero-progress dispatches (slot-14→8→6) in ~90 min.
- `22:29:54Z` — main creates prerequisite condition `p1-2-preconditions-met = false` (`set_by: "main"`).
- `22:30:26Z` — main answers `BLK-085fef5e` with **Option A, disposition: final**: "Applied the backlog park to
  `live_event_log_warm_sink_recovery_and_cold_compaction-011`: `priority:999` + `priority_override:true` + false prereq
  `p1-2-preconditions-met` (blockers endpoint confirms gated). This stops the fleet churn."
- `22:35:46Z` — slot-6 releases the slot citing the park as applied.
- `22:38:49Z` — task redispatched
  (`dispatch_reason: "tier=1 priority=20 plan_order=0 — highest-rank queued task with prereqs met and no collision"`) —
  **already priority 20, not 999**, only 8 minutes after main's park.
- `22:41:01Z` — slot-13's session killed by the server,
  `released_task: live_event_log_warm_sink_recovery_and_cold_compaction-011`, `resume_decision: "requeue"`.
- `22:55:42Z` — task redispatched again, same `dispatch_reason` text (`priority=20`, "prereqs met").
- **This worker (slot 15), on `/boot` at ~22:56Z**: live-read `agent-orchestrator/data/config/backlog.yaml` (task id
  `live_event_log_warm_sink_recovery_and_cold_compaction-011`, line 21384): `priority: 20`, `priority_override: false`,
  `prereqs: {completed_tasks: [], prerequisites: []}`. No trace of `999` / `true` / `p1-2-preconditions-met` anywhere in
  the entry.

So the park was gone **within 8 minutes** of being recorded as applied — before this worker was even dispatched to
observe it directly. This worker did not itself apply, then watch revert, the park (unlike the 2026-07-12
investigation's live reproduction) — the absence was already complete by the first post-park dispatch. The
`p1-2-preconditions-met` condition itself is presumably still `false` in the prerequisites table (nothing in the
activity log shows anyone flipping it `true`), so the task should be gated by it — except it was never actually attached
to this task's `prereqs.prerequisites` list, so there is nothing to gate on.

## Why it matters

- This is the exact failure mode `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` was filed and "resolved" for.
  That doc's fix (Defect B: `BacklogTask.priority_override` + `_reconcile_task_fields()` respecting it,
  `agent-orchestrator@8dd5763`) is present in the current code (`server/regen_backlog_from_plan.py:1938`:
  `if not task.priority_override and task.priority != priority:`) — so if the park genuinely reached disk with
  `priority_override: true` and then reverted anyway, that would be a **new** regression of a previously-fixed defect,
  not the same code path. Equally plausible: main's blocked-answer text describes an edit that, for whatever reason
  (concurrent write from another process, a `save_backlog()` call that didn't fire, a typo in the field path), **never
  actually landed on disk** — main's own text says "blockers endpoint confirms gated," which checks the
  `p1-2-preconditions-met` _condition value_ (true/false in the prerequisites table), not that the _task_ was actually
  gated behind it (`prereqs.prerequisites` attachment is a separate write). Both are plausible; this doc does not have
  enough evidence from the activity log alone to pick one.
- Regardless of cause, the ONE documented, sanctioned mechanism for stopping known-unsatisfiable-task redispatch churn
  (RULES.md §4 "Park a task") failed silently again, continuing to burn worker-slot cycles on
  `live_event_log_warm_sink_recovery_and_cold_compaction-011` despite an operator-equivalent "final" ruling already
  existing (`BLK-085fef5e`).
- The `auto_park` subsystem (`server/auto_park.py`, `dispatch_cooldown_auto_park_skip_threshold=3`) exists precisely to
  durably park a task after repeated BLOCKED/PARKED/GATED skips — but every skip recorded against this task so far used
  `reason_code: "OTHER"` (which does not count toward the escalating threshold), so `auto_park` never engaged as a
  fallback either.

## Recommended decision

1. Main/operator re-applies the park (`priority: 999` + `priority_override: true` +
   `prereqs.prerequisites: [p1-2-preconditions-met]` on this task's `backlog.yaml` entry, then
   `POST /api/backlog/reload`), and **actually re-checks the entry survives the next `PlanRegenLoop` tick or
   `POST /api/backlog/regen`** (not just `/reload`) before treating it as durable this time — the exact verification
   step `backlog_regen_drops_handtuned_prereqs_2026_07_12.md`'s own P2 todo added to RULES.md §4 for this exact
   scenario.
2. Whoever picks up the investigation todo below should determine which of the two candidate causes actually happened
   (edit never landed vs. genuine `priority_override` regression) before concluding this is "the same bug again" or "a
   new one" — the fix differs (process discipline vs. a code fix).
3. This worker is skipping `live_event_log_warm_sink_recovery_and_cold_compaction-011` back to the queue with
   `reason_code: "PARKED"` (an escalating code) rather than `"OTHER"`, to actually feed the `auto_park` skip counter
   this time — if 2 more PARKED/BLOCKED/GATED skips land within the 24h counting window, the system will durably park it
   itself via a code path, independent of whether the hand-edit mechanism above is trusted.

## Todos

- [ ] [SCRIPT] P0. Read `agent-orchestrator`'s activity/audit trail (or add temporary logging) around `22:30Z`-`22:39Z`
      on 2026-07-31 to determine whether main's park edit actually called `save_backlog()` with
      `priority_override: true` written to disk, or whether the write never happened / was immediately overwritten by a
      concurrent `regen()`/`reload()` call. Repo: agent-orchestrator.
- [ ] [SCRIPT] P1. If the write DID land and then reverted: reproduce in an isolated sandbox (per the
      `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` methodology — temp PM repo + temp backlog.yaml, no live
      state touched) hand-tuning `priority_override: true` on a throwaway task, then running a full `regen()` tick
      immediately after a `PlanRegenLoop`-triggered `prune_stale`/orphan-migration pass, to check whether the
      `prune_stale` path (lines ~2316-2367 of `regen_backlog_from_plan.py`) can clobber `priority_override` on a
      STILL-current (non-orphaned) task id under some condition the original 2026-07-12 fix didn't cover. Repo:
      agent-orchestrator.
- [ ] [OPERATOR] P1. Re-apply the park to `live_event_log_warm_sink_recovery_and_cold_compaction-011` per "Recommended
      decision" #1 above, and verify it survives one full `PlanRegenLoop` cycle before considering this resolved for
      that specific task.

## Progress Log

- **2026-07-31**: Filed by slot 15 on dispatch to `live_event_log_warm_sink_recovery_and_cold_compaction-011` — observed
  the park absent from `backlog.yaml` on a routine `/boot`, cross-referenced the activity log to reconstruct the
  timeline above. Did not hand-edit `backlog.yaml` (worker-scope precedent: that edit path is main/operator-only);
  skipped the task with `reason_code: "PARKED"` instead so the `auto_park` skip-counter has a chance to durably park it
  via its own code path. No code changed this session — investigation-only.
