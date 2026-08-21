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
  - /plans/archive/2026_08/issues/review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md
  - /plans/archive/2026_08/tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md
  - /plans/active/issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md
created: 2026-08-08
author: agt-22de53 (main)
parent_epic: security_and_cross_cutting_master
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

- [x] ✅ [BACKEND] P1. **DONE — unified-trading-pm (reconciled via
      `/plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md`) — no workload-intrinsic factor found.**
      Read both closed root-cause docs for the fleet-wide crash-loop; neither identified mechanism is
      workload/content-gated (both are host-timing/tmux-target bugs, content-agnostic). The 4-in-30min concentration is
      best explained by redispatch-timing bad luck landing inside the pre-2026-08-09-fix detection-bug window, not a
      property of this task's prompt size/tool-call pattern/worktree size. No code change indicated. Once
      `review_slot1_tmuxpruner_unexplained_crash_loop_2026_08_08.md` todo 1 identifies the fleet-wide TmuxPruner/keeper
      kill root cause, check specifically whether `solana_dex_pool_swaps_indexer-002` has a workload characteristic
      (prompt size, tool-call pattern, repo state, worktree size) that makes it disproportionately likely to trigger
      that root cause vs. other tasks. Repo: agent-orchestrator.
- [ ] [BACKEND] P2. Independent of the root cause above: consider whether `skip-current-task` should auto-escalate to a
      durable `park` after N repeat skips of the SAME task across DIFFERENT slots within a short window (mirrors the
      existing auto-park threshold logic in `auto_park.py` for BLOCKED/PARKED/GATED declines, per
      `ao_dispatch_cooldown_and_park_2026_07_20`) rather than relying on a human/main-agent to notice the pattern and
      call `/api/backlog/{task_id}/park` manually as was done here. Repo: agent-orchestrator.
- [x] ✅ [OPERATOR] P2. **MOOT 2026-08-09 (operator, interactive session)** — no unpark decision needed. The underlying
      indexer task already shipped: the ~18:15Z pre-park race (Progress Log below) landed
      `market-tick-data-service@3619f9e2` (ORCA Whirlpool fetch+decoder, 24 tests, QG green), and
      `/plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md` item 2 is already checked off. There is nothing left
      to redispatch — `unpark` would just release a parked-but-already-complete task back into rotation for no reason.
- [x] ✅ [REVIEW] P3. **CLOSED 2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0), alongside todo 3 per
      this todo's own stated reasoning.** **CORRECTED 2026-08-12 (/plan-reconcile)**: the todo above (todo 3) already
      established there is nothing left to unpark — the underlying indexer task shipped and `unpark` would just
      release a parked-but-already-complete task back into rotation for no reason. This todo's premise ("once
      unparked") therefore does not currently apply; only relevant if `solana_dex_pool_swaps_indexer-002` is
      independently unparked/reused for unrelated future work. If that never happens, this todo is moot and should be
      closed alongside todo 3. Once unparked and re-dispatched, independently verify via
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
- 2026-08-08 ~18:15Z (slot-33, fresh boot): dispatched this exact task (`solana_dex_pool_swaps_indexer-002`) via
  `already_in_progress: true` — the dispatch evidently landed just before the ~18:02Z `park` took effect. Completed a
  full `boot -> work -> done` cycle with **no wedge**: built the ORCA Whirlpool per-signature fetch + swap decoder, 24
  new unit tests, `quality-gates.sh` green, shipped `market-tick-data-service@3619f9e2`, plan checkbox flipped
  (`/plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md` item 2). Relevant to two open todos, though not checked
  off here since neither's stated condition is exactly met: todo 4 wants a POST-unpark verification (this run was
  pre-park) but the observation is the same — this exact task, on this exact slot number that was the 3rd wedge
  instance, ran clean end-to-end when NOT hitting the crash-loop signature, so the wedge looks environment/timing-
  triggered rather than an inherent property of this task's workload; todo 3's rescoping question is also informed — the
  actual indexer work (the fetch+decode implementation) completed in one normal session with no sign of being oversized.
  Leaving both open for BACKEND/OPERATOR to close with full context once todo 1's root cause lands.
- 2026-08-08 ~18:16Z (slot-7, fresh boot): a SECOND slot-7 respawn (distinct from the 17:58:17Z wedge instance in the
  table above) was independently dispatched this exact task via `already_in_progress: true` in the same narrow pre-park
  landing window as slot-33's occurrence above. Unaware of slot-33's concurrent work, this session independently
  implemented the identical capability from scratch (own module layout: `cli/handlers/_orca_whirlpool_swap_decoder.py` +
  a real captured-transaction fixture, vs. slot-33's `scripts/_orca_swap_decoder.py` +
  `scripts/_dex_swap_tx_helpers.py`) and reached a fully working, quality-gates-clean, basedpyright-strict-clean local
  commit before discovering — only at push time, via a branch-drift rejection — that slot-33 had already landed
  `market-tick-data-service@3619f9e2` for the SAME plan todo minutes earlier. No git conflict occurred (the two
  implementations used disjoint file paths), so this could have silently shipped as duplicate/competing code for the
  same capability had the branch-drift check not caught it. Recovered cleanly: soft-reset + stashed the redundant local
  commit (`orchestrator-slot-7-solana_dex_pool_swaps_indexer-002-superseded-by-mtds@3619f9e2` in this slot's
  market-tick-data-service stash), fast-forwarded to origin's shipped version, filed this entry, and returned the task
  via `/skip-current-task` (reason: duplicate — already completed). **New information beyond the slot-33 entry above**:
  this proves the same-task race in the ~18:02Z park-landing window duplicated a FULL unit of engineering work across
  two slots simultaneously (not just repeat wedge/crash-loop cycles) — a second, higher-cost failure mode of the same
  underlying gap (a dispatched-but-not-yet-`done` task isn't excluded from being handed to a second free slot). Relevant
  to todo 2's `skip-current-task` gap discussion: the fix there should also cover "already dispatched to another live
  slot," not just "repeat-skipped," since this case never skipped once before duplicating.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- Live-incident doc: task wedged 4 different slots
  via the fleet-wide TmuxPruner crash-loop, durably parked. 4 open todos -- todo 1's named prerequisite
  (`review_slot1_tmuxpruner...`'s root-cause todo) is now done, unblocking investigation; todo 3 is an explicit
  `[OPERATOR]` unpark decision with no ruling yet; todo 4 depends on todo 3. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-16** [body-hash:9beeb273044eb7c1]: KEEP-NA, valid — This is a resolved live-incident doc (agent-orchestrator fleet-wide crash-loop wedging one task across 4 slots on 2026-08-08, root-caused and durably parked).
- **na-eligibility-audit 2026-08-17**: KEEP-NA, valid — re-assessed the carried-forward "auto-escalate skip-current-task to durable park after N repeats" item (todo 2) per the close-the-loop rule: still needs a genuine design call (N threshold, count-vs-time window semantics, fleet-wide-vs-task-type scope) for a core dispatch-safety mechanism — not a pure copy of the cited auto_park.py precedent, since the trigger condition differs materially (repeat skips across slots vs. BLOCKED/PARKED/GATED declines). Stays KEEP-NA on that item; doc otherwise unchanged. Doc stays assigned_vm: NA.

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries).
