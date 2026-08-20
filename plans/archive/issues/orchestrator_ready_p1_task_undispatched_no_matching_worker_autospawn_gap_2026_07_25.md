---
doc_type: issue
title:
  A ready P1 DATA task (sports_satellite_ao_dispatch_batch2-011, fixture_events re-fetch) sat queued+undispatched for
  ~33min with the fleet idle — no matching-skill worker was alive and AutoSpawn did not spawn one; the one live worker
  (slot 3) self-reported the task as "blocked", and the three batch2 finalize tasks that depend on it stayed blocked
summary: >-
  On 2026-07-25 the orchestrator backlog held steady at done=118 / queued=6 / dispatched=0 for >30 minutes. Main
  (agt-52bb99) proved per-task that this was NOT a dependency deadlock: sports_satellite_ao_dispatch_batch2-011 — a P1
  [DATA] task ("fixture_events re-fetch into the canonical 13-col schema", queued_at 2026-07-25T07:31:48Z) — reads
  "ready (no blockers)" via /api/backlog/<id>/blockers, has target_slot=None, affinity=none, failover_allowed=True,
  collision_group=None, orphan=False (i.e. no affinity pin, no collision, no unmet prereq). Yet it never dispatched. The
  three finalize tasks (batch2_finalize-001/002/003) correctly report "prereq task ...batch2-011 not done" and stay
  queued behind it. At the time only ONE worker was alive (slot 3, worker_alive=true, idle, fresh last_ping) and it
  self-reported "idle: 4 task(s) blocked on task ...batch2-011" — meaning the live worker's own dispatch evaluation did
  NOT consider batch2-011 dispatchable to itself (consistent with a role/skill-routing mismatch: batch2-011 is a [DATA]
  task and slot 3 is a different skill). Slots 1 and 2 were stale (worker_alive=false, tmux_alive=true) — slot 1 a
  benign task-less cicd one-off (last_ping 07:35), slot 2 recently stale (last_ping 08:05). Net: a ready P1 task could
  not dispatch because no matching-skill worker was alive, and AutoSpawn did not spin up a matching worker over ~33min,
  leaving the fleet idle with pending P1 work. This is a runtime dispatch/AutoSpawn throughput gap, NOT a plan-data
  defect and NOT a prereq deadlock. Distinct from (but same incident family as) the DB-pool wedge and the
  PlanRegenLoop-prune backlog-wipe issues from the same window.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, autospawn, role-routing, throughput, fleet-idle, watchdog, stale-slot]
related:
  [
    /plans/archive/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md,
    /plans/active/issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P2
parent_epic: orchestrator_master
source: "main orchestrator (agt-52bb99) read-only per-task diagnosis during poll loop, 2026-07-25 ~08:12"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by: diagnosis complete; all 3 todos delegated to ao_satellite_ao_dispatch_batch1_2026_07_26.md
locked_by:
depends_on: []
---

> **🟢 RESOLVED 2026-07-25 -- root-cause diagnosis complete, follow-up fix work assigned to and tracked in an active AO
> dispatch plan. Archived per issue-doc-lifecycle.**

# Ready P1 DATA task undispatched ~33min — no matching-skill worker alive, AutoSpawn did not spawn one

## Evidence (read-only, on-host ip-172-31-5-118 :8765, 2026-07-25 ~08:12Z, main agt-52bb99)

- Backlog flat for >30min: `{queued: 6, dispatched: 0, done: 118, cancelled: 4, auto_parked: 2}`.
- The 6 queued: `batch2-011` (P1 DATA, ready), `batch2_finalize-001/002/003` (blocked on batch2-011),
  `infra_capture_and_devops_leftovers_finalize-001` (ready), `deployment_api_sigabrt_crash_loop-003` (parked on an unset
  `auto_unpark` prereq — legitimate).
- **`sports_satellite_ao_dispatch_batch2-011`** raw record: `status=queued`,
  `title="fixture_events re-fetch into the canonical 13-col schema"` (P1 [DATA]), `queued_at=2026-07-25T07:31:48Z`,
  `target_slot=None`, `affinity=none`, `failover_allowed=True`, `collision_group=None`, `orphan=False`,
  `dispatched_to=None`. `/blockers` → "ready (no blockers)". So nothing in the task's own record explains non-dispatch.
- **Fleet at diagnosis**: exactly one alive worker — slot 3 (`worker_alive=true, tmux_alive=true, idle`, fresh
  `last_ping 08:11:55Z`) whose `last_msg` = "idle: 4 task(s) blocked on task ...batch2-011". Slots 1 & 2 stale
  (`worker_alive=false, tmux_alive=true`): slot 1 = benign task-less cicd one-off (`last_ping 07:35:51Z`), slot 2 =
  recently stale (`last_ping 08:05:28Z`). All other slots down/paused.
- The live worker (slot 3) evaluating the queue and reporting the tasks as "blocked on batch2-011" — while batch2-011
  itself reads ready — indicates **the dispatcher did not consider batch2-011 dispatchable to slot 3**, most consistent
  with a **role/skill-routing mismatch** ([DATA] task vs slot 3's skill) combined with **no [DATA]-skilled worker alive
  and no AutoSpawn of one**.

## Root-cause hypothesis / the gap

A ready, unpinned, failover-allowed P1 task should either (a) dispatch to an eligible alive worker, or (b) trigger
AutoSpawn of a worker whose skill matches the task's role, within a bounded time. Here neither happened for ~33min: the
only alive worker was the wrong skill, and no matching worker was spawned. Candidate causes (for a BACKEND owner to
confirm against `server/autospawn.py` + the role-routing/dispatch path):

1. AutoSpawn skill-derivation may not map this [DATA] task to a spawnable role (task `assigned_role` surfaces as None;
   the required skill is presumably derived from the `[DATA]` brief tag / plan_ref — if that derivation yields no role,
   AutoSpawn may not know what to spawn).
2. AutoSpawn may be gated/back-off’d after the earlier DB-pool wedge occurrences in the same window (the `_do_spawn`
   write-lock wedge — see the pool-exhaustion issue), and not have retried once the wedge cleared.
3. A stale-slot reap gap: slot 2 went stale at 08:05 but was not respawned into an eligible worker.

## Todos

- [x] [BACKEND] P2. Ensure a ready, unpinned, failover-allowed task that has waited > (target_slot_timeout_seconds, 600s
      here) with no eligible alive worker triggers AutoSpawn of a matching-skill worker — or, if the required skill
      cannot be derived, loud-logs a WARNING naming the task id and the missing skill rather than silently leaving it
      queued. **Done when**: a ready P1 task with no matching alive worker causes a matching worker to be spawned (or a
      loud, actionable log) within a bounded time, with a test. — already covered by
      plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md (earmarked there as batch-2 material, gated on that
      batch's own todo 1 landing first) (see that doc for execution).

- [x] [BACKEND] P3. Confirm skill/role derivation for `[DATA]`-tagged briefs whose `assigned_role` is None resolves to a
      spawnable role (trace `batch2-011` through the derivation). Cross-ref the role-routing design in
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`. — already covered by
      plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md (earmarked as batch-2 material) (see that doc for
      execution).
- [x] [BACKEND] P3. Verify the stale-slot reaper respawns a stale slot (worker_alive=false, tmux_alive=true) into an
      eligible worker when ready matching work exists (slot 2 here stayed stale while a matching-ish P1 task waited). —
      already covered by plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md (earmarked there as batch-2
      material) (see that doc for execution).

## Triage / charter note

Main (agt-52bb99) diagnosed read-only and is **charter-barred from spawning/killing/respawning slots** (runtime
self-heals via AutoSpawn/failover/watchdog) and from editing backlog/task state by hand. Severity P2: the stalled task
is P1 sports-DATA (fixture_events re-fetch) — important but not trading-/funds-critical, no data-correctness defect in
landed data, self-recoverable the moment a matching worker comes up. Filed per the big-finding triage rule (fleet-idle
throughput stall on a ready P1 task) and cross-linked to the DB-pool-wedge and PlanRegenLoop-prune issues from the same
incident window. Recommend a BACKEND worker confirm the AutoSpawn/role-derivation path.
