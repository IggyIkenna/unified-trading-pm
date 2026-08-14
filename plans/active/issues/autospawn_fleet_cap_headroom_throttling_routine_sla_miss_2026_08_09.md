---
doc_type: issue
title:
  "AutoSpawn ~60s refill SLA is routinely missed by 1-2 orders of magnitude — fleet_worker_cap headroom throttling, not
  a code defect"
summary: >-
  Live-recheck (2026-08-09, filed while closing
  autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md) found the documented ~60s AutoSpawn
  refill SLA (worker.md) is routinely missed today, well after `agent-orchestrator@dfef970`'s within-tick
  spawn-parallelization fix landed: slot 10, 18 measured kill->respawn cycles over ~9h, gaps 0.6-35.3 min (median ~13
  min); slot 11, 14 cycles, gaps 1.1-43.0 min; slot 16 up to 83 min; slot 21 one measured gap of 3h11min. Root cause
  (code-confirmed): `_apply_fleet_cap()`'s `fleet_headroom = effective_cap - active_workers` throttles how many slots a
  tick may spawn at all — `dfef970` only parallelizes the spawns a tick already chose, it never touched this count. With
  the fleet running 20-25 concurrent active workers against a live `ORCHESTRATOR_FLEET_WORKER_CAP=25` (was 15 on
  2026-08-08), headroom is frequently 0-2, so a newly-idle slot can only respawn once ANOTHER active slot's own churn
  frees a headroom unit — this is DESIGNED capacity throttling (deliberate VM-load safety cap), not a bug. This doc
  exists to hand the resulting capacity/tuning decision to the operator — raising the cap further, adding priority-aware
  headroom allocation for long-idle slots, or accepting the current SLA-vs-safety trade-off — none of which is a
  bounded/deterministic code fix a worker should make unilaterally.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, sla, worker-liveness, capacity, fleet-cap, operator-decision]
related:
  [
    /plans/archive/2026_08/issues/autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md,
    /plans/archive/2026_08/issues/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md,
    /plans/archive/2026_08/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize_2026_08_08.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
created: 2026-08-09
author: slot-5-backend_engineer
priority: P3
parent_epic: orchestrator_master
source: "slot-5, backend_engineer, 2026-08-09 — surfaced during live-recheck todo of the sibling follow-up doc"
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
locked_by:
context_scope: [agent-orchestrator/server/autospawn.py, agent-orchestrator/server/config.py, /agents/worker.md]
---

# AutoSpawn ~60s refill SLA is routinely missed — fleet_worker_cap headroom throttling

## Evidence (2026-08-09, live `/api/activity` + `/api/state` on the `planning` VM itself)

- **Slot 10**: 18 measured `tmux_session_lost` -> `autospawn_succeeded` cycles between 09:00-21:32Z today. Gaps: 0.6,
  0.8, 1.2, 2.3, 2.7, 5.0, 5.2, 8.9, 11.5, 15.4, 15.7, 15.8, 16.6, 18.8, 19.9, 19.9, 31.8, 35.3 minutes. Median ~13 min.
- **Slot 11**: 14 measured cycles. Gaps: 1.1, 1.2, 6.6, 7.0, 12.4, 14.5, 15.7, 17.3, 22.1, 25.1, 29.4, 31.5, 39.8, 43.0
  minutes. Median ~17 min.
- **Slot 16**: gaps up to 83 min (13:44:41Z `tmux_session_lost` -> 15:07:51Z `autospawn_succeeded`).
- **Slot 21**: one measured gap of **3h11min** (05:15:49Z -> 08:27:01Z).
- Live config: `ORCHESTRATOR_FLEET_WORKER_CAP=25` today (`agent-orchestrator/.env.local`); was `15` on 2026-08-08
  (`.env.local.bak-20260808-030522`). `/api/state` measured 23/34 slots `status=working` at check time — i.e. the fleet
  runs routinely within 0-2 of its cap, so `_apply_fleet_cap()`'s `fleet_headroom = effective_cap - active_workers` is
  frequently near zero.

## Why this is not the same issue as `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md`

That doc's fix (`agent-orchestrator@dfef970`, `_do_spawns_concurrently()`) parallelizes the `_do_spawn()` calls a single
tick has ALREADY decided to make (bounded by `spawn_budget`). It does not change `spawn_budget` itself, which
`_apply_fleet_cap()` derives from `fleet_headroom = effective_cap - active_workers`. When the fleet is already near its
worker cap (the routine, not exceptional, state per the measurements above), a newly-idle slot can only be chosen for a
spawn once headroom frees up — which happens only when some OTHER already-active worker's session ends (task
completion + one-task-per-session reset, a crash, a context-wedge kill, etc.), not on a fixed cadence. This is why gaps
are irregular (0.6 min to 3h11min) rather than clustered around a fixed per-tick throttle value.

## Recommended decision (operator judgment — not resolvable as a bounded worker todo)

1. **Raise `ORCHESTRATOR_FLEET_WORKER_CAP` further** — simplest, but this VM's actual resource ceiling (CPU/RAM/disk,
   `/codex/05-infrastructure/vm-launcher-runbook.md` § disk pressure backstop) needs verifying before pushing past 25;
   this is exactly the tension `_apply_fleet_cap`'s own docstring calls out (a too-generous cap risks host-wide
   degradation, the underlying reason the cap exists at all).
2. **Priority-aware headroom allocation** — when a slot has been dead longer than some threshold (e.g. >5 min), let it
   preempt a share of headroom ahead of a slot dying with only in the last tick. Would need design (this is the kind of
   "figure out how it should behave" call `task_template.md`'s dispatch-scope-eligibility rule reserves for a human
   plan, not a worker todo).
3. **Accept as-is** — document the real SLA (minutes-to-hours under load, not the ~60s figure in `worker.md`) so
   `worker.md`'s documented number stops contradicting measured reality, and treat idle-capacity gaps as the accepted
   cost of the safety cap (bounded blast radius: no task is lost, no data-loss impact — confirmed in the parent
   2026-08-08 doc's own framing).

## Todos

- [ ] [OPERATOR] P3. Decide the fleet_worker_cap/SLA trade-off above (raise cap further / design priority-aware headroom
      allocation / accept + correct worker.md's documented SLA number) — the actual code/doc change is a quick follow-up
      once the decision is made, but the decision itself is a capacity/judgment call. Repo: agent-orchestrator +
      unified-trading-pm (worker.md correction, if option 3).

## Progress Log

- **2026-08-09 (slot 5, backend_engineer)**: Filed while closing
  `autospawn_refill_sla_data_points_1_2_and_live_recheck_followup_2026_08_09.md`'s live-recheck todo — the recheck
  surfaced a live, ongoing, much larger-magnitude version of the same SLA-miss class than either archived doc
  investigated, root-caused to `_apply_fleet_cap()` headroom throttling (not the `dfef970` batch-parallelization case).
  No code change here — the fix requires an operator capacity/tuning decision per
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" (an open-ended
  judgment call, not a bounded worker todo).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — first audit pass on this doc
  (no prior marker). The sole open item is a 3-way capacity/tuning tradeoff decision (raise
  `ORCHESTRATOR_FLEET_WORKER_CAP` further / design priority-aware headroom allocation / accept-and-document) with real
  host-resource-degradation risk if the wrong branch is picked unilaterally — the doc's own text explicitly frames this
  as 'not resolvable as a bounded worker todo.' Genuine capacity/operator judgment call.
