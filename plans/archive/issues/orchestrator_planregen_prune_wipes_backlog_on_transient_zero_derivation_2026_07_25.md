---
doc_type: issue
title:
  PlanRegenLoop prune_stale wipes the ENTIRE backlog (cancels in-flight tasks) when a single regen transiently derives 0
  tasks from 569 plans — no circuit-breaker guards a catastrophic total=0 derivation caused by a transient DB/snapshot
  failure (observed triggered by the DB-pool wedge)
summary: >-
  On 2026-07-25 at 05:42:56Z the orchestrator's PlanRegenLoop completed a tick with `scanned=569 new=0 reconciled=0
  skipped=0 total=0` and then `prune_stale: removed 43 orphan yaml entries, 22 state.db rows … cancelled 5
  dispatched-orphan task(s) (removed while in-flight)`, taking the backlog from 43 tasks (healthy at 05:38:35: total=43)
  to 0 (queued 0 / dispatched 0). The `pruned_orphan_ids` list was the entire live backlog — ao_worker_context_lifecycle
  _gap-001..010, sports_satellite_ao_dispatch_batch2-001..013 (+finalize), deployment_api_sigabrt_crash_loop-001..003,
  deployment_promote_squash_ancestry_false_negative-001..003, sports_curated_universe_domestic_selection_remaining-001,
  sports_fixture_events_refetch_progress-001, sports_fixtures_schedule_wrong_schema_day-001,
  sports_post_backfill_relabel _premise_resolved_residual_gap-001..003, infra_capture_and_devops_leftovers_finalize-001,
  ao_fleet_throughput_incident -001 (+finalize). The regen deriving 0 tasks from 569 plans is not a real "all work done"
  signal — it coincided exactly with DB-pool-wedge occurrence #8 (QueuePool TimeoutError 05:42:31-37Z, see the
  pool-exhaustion issue), i.e. the regen ran while the DB was wedged, got an empty/partial derivation, and prune_stale
  then treated the whole existing backlog as orphaned and wiped it — including cancelling 5 tasks that were mid-flight.
  The backlog self-recovered over the next regen ticks (05:44:50Z: queued 1 / done 102 and climbing as tasks
  re-derived), so this is not a permanent data loss of plan-defined work, but any in-flight worker progress on the 5
  cancelled tasks was needlessly discarded and dispatch briefly went fully idle. Confirmed on-host by main (agt-52bb99)
  reading the PlanRegenLoop journal.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog, plan-regen, prune-stale, dispatch, robustness, circuit-breaker, db-pool]
related:
  [
    /plans/archive/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-07-25
author: unknown
last_updated: 2026-08-06
priority: P2
parent_epic: orchestrator_master
source: "main orchestrator (agt-52bb99) on-host diagnosis during poll loop, 2026-07-25 ~05:44"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by: "AO issue-doc sweep 2026-08-06 — re-verified both circuit-breaker todos live in agent-orchestrator/server/regen_backlog_from_plan.py (_PRUNE_COLLAPSE_FRACTION + ZERO/COLLAPSE circuit breaker, citing this doc by name); sole remaining todo closed as a routed duplicate."
locked_by:
context_scope:
  [
    /plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md,
  ]
depends_on: []
---

> **🗄️ ARCHIVED 2026-08-06** — fully resolved. Both circuit-breaker todos shipped live in
> `agent-orchestrator/server/regen_backlog_from_plan.py` (`_PRUNE_COLLAPSE_FRACTION` + a "ZERO/COLLAPSE CIRCUIT BREAKER"
> block that cites this doc by name), verified present in current code, not just checkbox-flipped historically. The sole
> remaining todo was a duplicate of `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`'s
> own open work — closed here as routed, not re-solved. No open todos, no Deferred items. Surfaced by the 2026-08-06 AO
> issue-doc sweep.

# PlanRegenLoop prune_stale wipes the whole backlog on a transient total=0 derivation (no zero-derivation circuit-breaker)

## What happened (on-host evidence, ip-172-31-5-118 :8765, 2026-07-25)

Journal timeline of the PlanRegenLoop (interval 300s), all "dispatching from origin/live-defi-rollout plan snapshot
(PM-main-independent)":

- **05:37:17Z** — `Plan regen complete: scanned=569 new=0 reconciled=0 skipped=0 total=42 pruned_yaml=1 pruned_db=0`
  (healthy, 42 tasks).
- **05:38:35Z** — `scanned=569 new=1 reconciled=4 skipped=0 total=43 pruned_yaml=0 pruned_db=0` (healthy, 43 tasks).
- **05:42:18–05:42:56Z** — a burst of rapid regen "dispatching" lines interleaved with the DB-pool wedge (QueuePool
  `TimeoutError` at 05:42:31, :33, :35, :37Z — the `_do_spawn` write-lock wedge, occurrence #8 in the pool-exhaustion
  issue). The regen was thrashing while the DB could not hand out connections.
- **05:42:56Z** — `Plan regen complete: scanned=569 new=0 reconciled=0 skipped=0 total=0 pruned_yaml=43 pruned_db=22`
  followed by
  `prune_stale: removed 43 orphan yaml entries, 22 state.db rows (queued+undispatched absent from current backlog, incl zombies); cancelled 5 dispatched-orphan task(s) (removed while in-flight)`
  and `PlanRegenLoop: in-process backlog refreshed (0 tasks)`. **The entire backlog was wiped** (queued 0 / dispatched
  0); `pruned_orphan_ids` = every live task (full list in the summary above).
- **Recovery**: by 05:44:50Z `/api/state` showed `{queued:1, dispatched:0, done:102, cancelled:8}` and climbing — the
  subsequent regen ticks re-derived the plan tasks, so the plan-defined backlog is repopulating on its own.

Also at **05:41:16Z**, two
`sync_backlog_to_db: REFUSING to reset task id … — it is done … Incoming checkbox content disagrees … investigate the regen/positional-id collision instead of resetting`
errors (deployment_api_sigabrt_crash _loop-001, sports_curated_universe_domestic_selection_remaining-001) — a
regen/positional-id collision symptom in the same window, consistent with the regen reading a shifting/partial plan
snapshot.

## Root cause / the gap

`prune_stale` treats "task present in the DB backlog but absent from the freshly-derived task set" as an orphan to
remove — which is correct when the derivation is trustworthy. But it has **no sanity guard against a catastrophic,
almost-certainly-spurious `total=0` derivation**: 0 tasks derived from 569 scanned plans (down from 43 one tick earlier)
is overwhelmingly a _derivation failure_ (here: the DB pool was wedged so the regen could not read/resolve state), not a
real "all work is done" state. Acting on it cancelled 5 in-flight tasks and pruned 65 rows. The regen should **fail
safe**: a derivation that collapses to 0 (or drops by more than some large fraction vs. the prior successful tick)
should **skip the prune and keep the last-good backlog**, log loudly, and retry — never cancel in-flight work off a zero
result.

## Todos

- [x] [BACKEND] P2. Add a zero/collapse circuit-breaker to the PlanRegenLoop prune path: if a regen derives `total=0`
      (or total drops by > a large fraction, e.g. >75%, vs. the last successful tick) while `scanned` is non-trivial,
      **skip prune_stale entirely, keep the prior backlog, log a loud WARNING, and do not cancel any in-flight tasks**;
      let the next tick re-derive. **Done when**: a simulated empty/failed derivation leaves the existing backlog intact
      and cancels nothing, with a test. — already covered by plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md
      (agent-orchestrator@d66fbf2) (see that doc for execution).
- [x] [BACKEND] P2. Make regen robust to a wedged/unavailable DB: if the derivation cannot complete because DB reads are
      failing (pool exhaustion / timeouts), abort the tick WITHOUT pruning rather than completing with a partial/empty
      task set. Cross-ref the pool-wedge root cause in
      `/plans/archive/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` (fixing that removes the
      trigger; this guard removes the blast radius). — already covered by
      plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md (agent-orchestrator@d66fbf2) (see that doc for
      execution).
- [x] [BACKEND] P3. **CLOSED 2026-08-06 — duplicate, not this doc's to fix.** ⚠️ **ALREADY OWNED by an active
      `assigned_vm: planning` doc — do NOT dispatch from here (citation
      added by `/na-eligibility-audit ao` 2026-07-30).** This item duplicates
      `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`'s open `[BACKEND] P2`, which was
      **RULED 2026-07-28** (operator gated-decision closeout pass) from a parked decision into a normal, fully-scoped
      AO-dispatchable todo: do the content-hash task-id rewrite now, full blast radius (`existing_ids`/`existing_briefs`
      bookkeeping in `regen_backlog_from_plan.py`, `slot_skips` keyed by `task_id`, every dashboard/API id reference,
      and a migration path for already-`done` rows).
      `/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred section records the same routing
      verbatim: "Do NOT draft a competing batch todo here — dispatch that issue doc's todo directly once picked up."
      This doc's own answer ("confirm task IDs are content-anchored, not purely positional") is exactly that rewrite's
      outcome. Original text follows. Investigate the 05:41:16Z regen/positional-id collisions
      (`sync_backlog_to_db: REFUSING to reset …`) — positional task-id assignment appears to shift under a partial
      snapshot, which both logs scary errors and risks mis-identifying tasks. Confirm task IDs are content-anchored, not
      purely positional, so a partial plan snapshot cannot collide a new brief onto a done row's id.
      **na-eligibility-audit 2026-08-03 (blocker-currency check): the "owned by an active `assigned_vm: planning` doc"
      framing above is now STALE.** `regen_positional_task_ids_not_content_stable_2026_07_17.md`'s `assigned_vm` was
      RECLASSIFIED to `planning` by the 2026-07-30 na-audit cited above, but has since been **REVERTED to `NA` on
      2026-07-31** (per `BLK-29884333`, its third mis-dispatch) with an explicit banner: "NOT AO-dispatchable:
      banner-guarded, local-only-homed fleet-core rewrite." The conclusion here is unchanged (do NOT dispatch this P3
      item — the duplicated content is a banner-guarded local-only rewrite, not merely "claimed elsewhere"), but the
      reasoning should cite BLK-29884333 / the current `NA` status, not the superseded "active planning doc" framing.
      `assigned_vm` untouched.

## Triage / charter note

Self-recovered (backlog repopulating), so non-blocking right now — filed P2, not P1. But the blast radius (whole-backlog
wipe + in-flight cancellation off a single spurious regen) is large, and it is directly coupled to the P1 pool wedge as
its trigger, so the circuit-breaker is worth landing alongside the pool fix. Main (agt-52bb99) diagnosed read-only and
is charter-barred from shipping the code fix (routes via a BACKEND worker + quickmerge) and from editing backlog.yaml /
task state by hand. Cross-linked to the pool-exhaustion and (separately) the missing-migration issues from the same
incident window.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA-STALE (citation fixed, no reclassification) — the sole open
  `[BACKEND] P3` duplicates the open `[BACKEND] P2` in the active `assigned_vm: planning` doc
  `/plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`, which was RULED 2026-07-28 into
  normal fully-scoped AO work (content-hash task-id rewrite, full blast radius).
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md` records the same routing: 'Do NOT draft a competing batch todo here —
  dispatch that issue doc's todo directly.' Annotated in place; `assigned_vm` untouched.
- **na-eligibility-audit 2026-08-03** (reclassify pass): KEEP-NA, valid (blocker-currency only) — the referenced doc's
  `assigned_vm` was reverted `planning`->`NA` on 2026-07-31 (`BLK-29884333`, a recurring mis-dispatch trap:
  banner-guarded, local-only-homed fleet-core rewrite). Annotated in place so the next reader cites the current status
  instead of the now-superseded "active planning doc" framing. Conclusion unchanged (do not dispatch). `assigned_vm`
  untouched.
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged from prior scout — still accurate: the
  duplicated-content doc, the archived batch1 plan that shipped the two DONE todos, and the pool-exhaustion trigger
  doc).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
