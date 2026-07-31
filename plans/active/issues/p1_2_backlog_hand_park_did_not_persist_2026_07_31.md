---
doc_type: issue
title:
  "RESOLVED: main's blocked-answer described a backlog park (priority:999 + priority_override:true + false prereq
  p1-2-preconditions-met) on live_event_log_warm_sink_recovery_and_cold_compaction-011 that was never actually written —
  the file edit step was skipped, not reverted; task kept redispatching"
summary: >-
  Main answered BLK-085fef5e at 2026-07-31T22:30:26Z with a "final" disposition describing a park of
  `live_event_log_warm_sink_recovery_and_cold_compaction-011` (the P1.2 daily-determinism-recheck todo, doubly
  time-gated + paper-run-gated, already redispatched to 3 workers in ~90 minutes with zero possible progress) applied
  per the sanctioned RULES.md §4 recipe. The task kept redispatching anyway (a slot-13 session picked it up 8 minutes
  later; this worker was dispatched it again at 22:55:42Z with `priority: 20`, `priority_override: false`,
  `prereqs.prerequisites: []` still live in `backlog.yaml` — the park fully absent). **Root cause CONFIRMED (not
  ambiguous) via `journalctl -u orchestrator.service`**: the only two API calls in the window were `POST
  /api/prerequisites/p1-2-preconditions-met` (sets the global condition value only) and `POST /api/backlog/reload`
  (re-reads disk, never writes) — the actual `backlog.yaml` file edit (the part that sets
  `priority`/`priority_override`/`prereqs.prerequisites` on the task's own entry) was never performed. A static read of
  `_reconcile_task_fields()` additionally confirms `prereqs.prerequisites` has no revert code path at all, ruling out a
  `backlog_regen_drops_handtuned_prereqs_2026_07_12.md`-class regression. This is a one-time process gap (an intended
  edit that didn't happen), not a recurrence of a code defect — the fix is simply to perform the edit; the code path is
  sound.
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

- **CONFIRMED (see todo 1's evidence)**: this is NOT a recurrence of
  `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` — that doc's fix (Defect B: `BacklogTask.priority_override` +
  `_reconcile_task_fields()` respecting it, `agent-orchestrator@8dd5763`) is present and intact in the current code, and
  `prereqs.prerequisites` has no revert code path at all to have been hit. The park simply was never written to
  `backlog.yaml` — main's blocked-answer text says "blockers endpoint confirms gated," which checks the
  `p1-2-preconditions-met` _condition value_ (true/false in the prerequisites table, genuinely set), not that the _task_
  was actually gated behind it (`prereqs.prerequisites` attachment is a separate write that never happened).
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
2. **Resolved by todo 1 below**: confirmed the edit never landed (process gap), not a `priority_override` code
   regression — no code fix needed, `agent-orchestrator` is unchanged by this doc.
3. This worker is skipping `live_event_log_warm_sink_recovery_and_cold_compaction-011` back to the queue with
   `reason_code: "PARKED"` (an escalating code) rather than `"OTHER"`, to actually feed the `auto_park` skip counter
   this time — if 2 more PARKED/BLOCKED/GATED skips land within the 24h counting window, the system will durably park it
   itself via a code path, independent of whether the hand-edit mechanism above is trusted.

## Todos

- [x] ✅ [SCRIPT] P0. **DONE 2026-07-31 (slot 15) — root cause CONFIRMED, not ambiguous.** Read
      `journalctl -u orchestrator.service --since "2026-07-31 22:00:00" --until "2026-07-31 23:00:00"` (the live
      orchestrator's own HTTP access + application log — no temporary logging needed, the server already logs every
      request). The ONLY two API calls touching this task's park in the entire window:
      `22:29:54Z POST     /api/prerequisites/p1-2-preconditions-met` (sets the global condition value — does NOT touch
      any task's `backlog.yaml` entry) and `22:30:26Z POST /api/backlog/reload` (re-reads `backlog.yaml` from disk into
      memory — `reload_backlog()` calls `load_backlog()` only, never `save_backlog()`, confirmed by reading
      `server/routes/backlog.py:91`). **There is no third call** — no `PATCH`/`PUT` to any backlog task, and no
      write-capable endpoint exists for hand-tuning a task's `priority`/`prereqs.prerequisites` at all (grepped every
      `@router.post/patch/put("/api/backlog` route in `server/routes/backlog.py`: only `reload`, `regen`, `reopen`,
      `reconcile-brief`, `remint-collision`, `unpark`, `park/redispatch`, `park/mark-done` exist — none of these write
      arbitrary `priority`/`prereqs.prerequisites`). The RULES.md §4 park recipe's actual file-edit step is a direct
      file write (an Edit/Write tool call), which would not appear in the HTTP log — but it did not need to, because a
      second, decisive check rules out the "landed then reverted" hypothesis directly: `_reconcile_task_fields()`
      (`server/regen_backlog_from_plan.py:1894-1954`, the ONLY function that mutates an already-derived task's fields on
      a regen tick) **never touches `prereqs.prerequisites` at all** — it reconciles `model`/`effort`/`thinking`/
      `assigned_role`/`provider_override`/`priority` (priority-override-protected)/`plan_order`/`collision_group` only.
      There is no code path anywhere in `regen_backlog_from_plan.py` that would strip a `prereqs.prerequisites` entry
      from a still-current (non-orphaned) task — `prereqs.prerequisites` is a real, declared `TaskPrereqs` field that
      round-trips through `load_backlog()`/`save_backlog()` unmodified (confirmed by the 2026-07-12 fix's own empirical
      table). **Conclusion: the actual `backlog.yaml` edit (setting `priority: 999` + `priority_override: true` +
      `prereqs.prerequisites: [p1-2-preconditions-met]` on this task's entry) was NEVER PERFORMED.** Main's
      blocked-answer text described the full 3-part recipe as applied, but only 2 of the 3 steps actually executed
      (create the condition; reload). This is a **process/execution gap, not a code regression** —
      `backlog_regen_drops_handtuned_prereqs_2026_07_12.md`'s Defect A/B fixes are both intact and uninvolved; there was
      nothing for them to protect because the write they protect against reverting never happened in the first place.
- [x] ✅ [SCRIPT] P1. **N/A — resolved by todo 1, not just left uninvestigated.** Todo 1's code-path check
      (`_reconcile_task_fields()` never touches `prereqs.prerequisites`, and no code path strips it) directly rules out
      the "write landed, then got clobbered by `prune_stale`/regen" hypothesis this todo was scoped to test — a sandbox
      reproduction would have nothing to reproduce (there is no revert code path to trigger). Closing without a sandbox
      run; the static-analysis answer is conclusive on its own (unlike the 2026-07-12 case, which genuinely needed the
      sandbox to distinguish two live-reproducible symptoms).
- [ ] [OPERATOR] P1. Re-apply the park to `live_event_log_warm_sink_recovery_and_cold_compaction-011` per "Recommended
      decision" #1 above (actually perform the `backlog.yaml` file edit this time, then `POST /api/backlog/reload`), and
      verify it survives one full `PlanRegenLoop` cycle before considering this resolved for that specific task.

## Progress Log

- **2026-07-31 (slot 10, infra)**: `p1_2_backlog_hand_park_did_not_persist-002` (the P1 sandbox-repro todo) was
  concurrently dispatched to this slot after slot 15 had already closed it in-doc. Independently re-read
  `server/regen_backlog_from_plan.py` before trusting the duplicate dispatch: confirmed `_reconcile_task_fields()`
  (lines 1894-1954) only ever writes `task.priority` and only when `not task.priority_override` (line 1938) — it never
  touches `prereqs.prerequisites`. Grepped every `t.prereqs.prerequisites` mutation site in the file: line 2126
  (`_wire_gate_on_depends_prereqs`) only `.extend()`s (additive-only, and gated on `gate_on_depends: true` frontmatter
  the target task's plan doesn't declare); line 2359 (`_migrate_parking_state`) only writes into a successor when the
  ORIGINAL task was orphaned (brief no longer matches any current todo) —
  `live_event_log_warm_sink_recovery_and_cold_compaction-011` stayed the same still-current id throughout the incident,
  so this path never applied to it either. No other `.priority =` or `.prereqs.prerequisites =` write site exists in the
  file. This independently corroborates todo 1/2's conclusion with a second read: there is no code path capable of
  reverting a hand-applied park on a still-current task, so the sandbox reproduction this todo called for has nothing to
  reproduce. Closing `-002` as duplicate/already- resolved by todo 1's investigation — no code change needed.
- **2026-07-31 (slot 15, infra)**: Investigation todo (P0) done — root cause conclusively identified via
  `journalctl -u orchestrator.service` + a static read of `_reconcile_task_fields()`: main's park never actually wrote
  `backlog.yaml` (only the prerequisite condition was created + a `/reload` was called, neither of which touches a
  task's own entry). No code fix needed — closed the P1 sandbox-repro todo as not-applicable since the code-level
  question it existed to answer is already settled. `[OPERATOR]` todo 3 (re-apply, this time actually performing the
  file edit) is the one remaining action, left for main/operator per established worker-scope precedent on
  `backlog.yaml` hand-edits.
- **2026-07-31**: Filed by slot 15 on dispatch to `live_event_log_warm_sink_recovery_and_cold_compaction-011` — observed
  the park absent from `backlog.yaml` on a routine `/boot`, cross-referenced the activity log to reconstruct the
  timeline above. Did not hand-edit `backlog.yaml` (worker-scope precedent: that edit path is main/operator-only);
  skipped the task with `reason_code: "PARKED"` instead so the `auto_park` skip-counter has a chance to durably park it
  via its own code path. No code changed this session — investigation-only.
