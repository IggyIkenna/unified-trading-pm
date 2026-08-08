---
doc_type: issue
title:
  solana_dex_pool_swaps_indexer-002 wedged 4 different slots in ~25min via the fleet-wide post-compact respawn signature
  — durably parked
summary: >-
  Task `solana_dex_pool_swaps_indexer-002` wedged 4 consecutive slots that picked it up (11, 9, 33, 7) between ~17:31Z
  and ~18:00Z on 2026-08-08, each hitting the identical `slot_boot`->`forced_precompact`->`forced_compact` ->silent
  (`worker_alive:false`) signature within 1-2min of boot — the same fleet-wide crash-loop pattern tracked in
  `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md`, but this ONE task is uniquely re-triggering it on
  every slot that claims it. Neither `reassign` (affinity=high requeue) nor `skip-current-task` (per-slot skip only)
  durably excluded it from fleet-wide redispatch — it kept getting re-picked by the next free slot within minutes each
  time. Durably parked via `POST /api/backlog/{task_id}/park` (condition
  `auto_unpark__solana_dex_pool_swaps_indexer-002`) to stop the churn while this is root-caused.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, tmux, crash-loop, task-affinity, live-incident, spawn-overhead, park]
related:
  - /plans/active/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md
  - /plans/active/issues/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md
  - /plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md
created: 2026-08-08
author: agt-22de53 (main)
parent_epic: infrastructure_master
priority: P1
source: >-
  Main-agent routine stale-slot sweep (STEP 2.4/2.6), 2026-08-08 17:36Z-18:01Z window. Escalated from generic fleet-wide
  wedge evidence (logged in the TmuxPruner doc) to a dedicated task-specific issue once the SAME task wedged a 4th
  distinct slot despite two different mitigation attempts.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-08
locked_since:
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/routes/slots_ops.py,
    agent-orchestrator/server/auto_park.py,
  ]
---

# solana_dex_pool_swaps_indexer-002 repeat-wedge — durably parked pending root cause

## What was found

Live, directly-observed during routine stale-slot sweeps (not a self-report):

| #   | Slot | `slot_boot` | `forced_precompact` | `forced_compact`                                         | Outcome                                                                                                     |
| --- | ---- | ----------- | ------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| 1   | 11   | ~17:27Z     | ~17:31Z             | ~17:31:53Z                                               | 2x `worker_kick_failed` (17:33:54Z, 17:35:50Z) -> `reassign kill_worker:true`                               |
| 2   | 9    | 17:41:55Z   | ~17:42Z             | 17:43:28Z (after `forced_compact_ineffective` 17:42:22Z) | silent, `worker_alive:false` -> `reassign kill_worker:true`                                                 |
| 3   | 33   | 17:53:09Z   | 17:53:42Z           | 17:55:28Z                                                | silent, `worker_alive:false` -> `skip-current-task` (first attempt at breaking the affinity-reposion cycle) |
| 4   | 7    | 17:58:17Z   | 17:59:25Z           | 18:00:30Z                                                | silent, `worker_alive:false` -> `skip-current-task` + durable `park` (this doc)                             |

Every occurrence is the identical signature already tracked fleet-wide in
`review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` todo 1 (root-cause read of TmuxPruner/keeper kill logic)
— this doc does NOT duplicate that investigation. What's new here: **this one task has now wedged 4 of the ~6-8
fleet-wide wedges observed in the same window**, i.e. it is disproportionately represented, suggesting either (a)
something about this specific task's workload (long-running indexer backfill, particular tool call pattern, memory
profile) interacts badly with whatever the fleet-wide root cause is, or (b) a `reassign` `affinity=high`-style poisoning
mechanism that `skip-current-task` did NOT actually break (occurrence 4 happened one tick after occurrence 3's
`skip-current-task`, which the skip-current-task response's own `next_step` text scopes as "excluding the skipped task"
only for **that slot's** next heartbeat, not a fleet-wide exclusion — so the task simply flowed back into the general
tier=1/priority=20 pool and got re-picked by the very next free slot).

## Why it matters

- Same spawn-overhead/continuity cost as the tracked fleet-wide pattern, but concentrated: 4 wedge/respawn cycles on ONE
  task in ~30 minutes is a much tighter loop than the general fleet rate, and none of it made forward progress on the
  actual indexer work.
- `reassign` and `skip-current-task` are the two standard main-agent mitigation levers for a wedged slot, and neither
  stopped this task from immediately re-wedging the next slot — `park` was the only lever that actually removed it from
  rotation. Worth checking whether `skip-current-task`'s per-slot-only scoping is itself a gap (a task that reliably
  wedges every slot that touches it should probably auto-park after N skips, not just move to the next victim) — see
  todo 2 below.

## Todos

- [ ] [BACKEND] P1. Once `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` todo 1 identifies the fleet-wide
      TmuxPruner/keeper kill root cause, check specifically whether `solana_dex_pool_swaps_indexer-002` has a workload
      characteristic (prompt size, tool-call pattern, repo state, worktree size) that makes it disproportionately likely
      to trigger that root cause vs. other tasks. Repo: agent-orchestrator.
- [ ] [BACKEND] P2. Independent of the root cause above: consider whether `skip-current-task` should auto-escalate to a
      durable `park` after N repeat skips of the SAME task across DIFFERENT slots within a short window (mirrors the
      existing auto-park threshold logic in `auto_park.py` for BLOCKED/PARKED/GATED declines, per
      `ao_dispatch_cooldown_and_park_2026_07_20`) rather than relying on a human/main-agent to notice the pattern and
      call `/api/backlog/{task_id}/park` manually as was done here. Repo: agent-orchestrator.
- [ ] [OPERATOR] P2. Decide whether to `unpark` (`POST /api/backlog/solana_dex_pool_swaps_indexer-002/unpark`) once todo
      1's root cause is fixed, or whether the underlying indexer task itself needs rescoping/splitting first (check
      `/plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md` for whether this is a long-running/heavy
      task that may need a smaller unit size regardless of the wedge root cause).
- [ ] [REVIEW] P3. Once unparked and re-dispatched, independently verify via
      `GET /api/activity?task=solana_dex_pool_swaps_indexer-002` (or per-slot) that it completes a full boot->work->done
      cycle without re-wedging. Repo: unified-trading-pm (verification + checkbox flip only).

## Progress log

- 2026-08-08 ~18:02Z (main agt-22de53): Filed after the 4th confirmed same-task wedge (slot 7), following the standing
  threshold set in `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md`'s progress log ("if this task wedges a
  THIRD slot, switch to skip-current-task... and consider filing a dedicated task-specific issue") — slot 33 was the 3rd
  instance (skip-current-task applied then), slot 7 is the 4th (skip-current-task again, plus this doc, plus a durable
  `park` since skip alone clearly did not stop redispatch). Task parked via
  `POST /api/backlog/solana_dex_pool_swaps_indexer-002/park` — condition
  `auto_unpark__solana_dex_pool_swaps_indexer-002` confirmed set in the response.
