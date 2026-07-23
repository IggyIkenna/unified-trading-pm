---
doc_type: issue
title:
  AO respawn churn — the AutoSpawn spawn-budget is slot-skip-blind, so fleet-wide-skipped (genuinely blocked) tasks read
  as spawnable work and the fleet respawns onto them all day
summary: |
  2026-07-15 live re-confirmation (operator-reported: "backend spawned slot #14, worker booted, no dispatchable task —
  all blocked"). Root cause is the OPEN `[BACKEND] P2 Skip-exhaustion churn` gap already recorded in
  ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md: AutoSpawn's spawn-budget (`_queued_undispatched_count` /
  `_has_queued_work`, server/autospawn.py) counts a queued task as spawnable when only its formal `prereqs` are met,
  while dispatch (`pick_next_task`, server/dispatch.py) additionally filters on per-slot `slot_skips` (24h TTL), role,
  collision and affinity. The two gates are asymmetric, so a task every live+eligible slot has skipped within the TTL
  still inflates the spawn budget. Measured at rest (state.db 05:15Z): spawn-budget=6 but only 1 task is claimable by any
  live slot — 5 phantom, each skipped by 14–15 distinct slots WITHIN the 24h TTL. Autospawn therefore keeps the ~13-slot
  data_engineering fleet at/near the worker cap and respawns dead slots straight back onto un-claimable work: 24h =
  ~1014 autospawns / 1184 boots / 954 worker-deaths for 217 dispatches and 101 done. Compounded by two OTHER open gaps
  that keep these tasks un-parkable: backlog_regen_drops_handtuned_prereqs_2026_07_12.md (regen silently reverts the
  sanctioned false-`prereqs.conditions` park) and the BLOCKED-* orphan-on-skip path only firing on a PLAN-TEXT marker,
  not a skip-reason. Compounding CONSEQUENCE (new here): the churn has burned 2 of 4 accounts past the 95% weekly spawn
  ceiling (sub-c 99%, sub-d 97%), shrinking the usable rotation. This doc is the verified root-cause + evidence record;
  the fix decision (skip-aware spawn budget only, vs also auto-park repeatedly-skipped tasks) is deferred to the operator.
status: resolved # (was: open) 2026-07-23 plan-reconcile — last open todo verified DONE; all 3 todos now [x]
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    autospawn,
    dispatch,
    slot-skips,
    spawn-budget,
    respawn-churn,
    fleet-stall,
    account-burn,
    incident,
  ]
related:
  [
    /plans/archive/issues/ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md,
    /plans/archive/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md,
    /plans/archive/issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md,
    /plans/archive/issues/backlog_blocked_marker_stale_brief_redispatch_2026_07_08.md,
  ]
created: 2026-07-15
last_updated: 2026-07-23
parent_epic: orchestrator_master # was: agent_operating_framework_master — repointed 2026-07-16 (ao_docs_reconciliation F5, "cross-epic dispatch-code ownership seam fuzzy"). Every other dispatch-code doc/plan homes at orchestrator_master (ao_dispatch_residuals, ao_fleet_stall_opus_spawn_and_skip_thrash, dispatcher_role_eligibility_gap_review_slots, ao_dispatch_hardening); this one was the outlier. orchestrator_master owns the AO RUNTIME (dispatch/autospawn/slots); agent_operating_framework_master owns how agents WORK (retrieval, role charters, plan format) — a skip-blind spawn budget is runtime.
priority: P1
source:
  - operator-reported 2026-07-15 (slot #14 booted, "no dispatchable task — all blocked behind prerequisites")
  - server/autospawn.py (_queued_undispatched_count / _has_queued_work)
  - server/dispatch.py (pick_next_task)
  - live at-rest DB /var/lib/orchestrator/state.db (read-only), backlog.yaml, slot-14 transcript
assigned_vm: NA
execution_scope: local-only
resolved_by: agent-orchestrator@cfb211c # fleet-scoped cooldown store + durable auto-park; verified ancestor of origin/live-defi-rollout and code-read (auto_park.py::maybe_auto_park, auto_park_reconcile.py::AutoParkReconciler) on 2026-07-23
locked_by:
locked_since:
model_tier: sonnet-doable
thinking_tier: high
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
---

> **🟢 EXECUTION CONSOLIDATED 2026-07-17** — this doc's open items are now tracked and executed via
> [`ao_open_issues_consolidated_close_out_2026_07_17`](../ao_open_issues_consolidated_close_out_2026_07_17.md)
> (operator-session local plan; verified-live classification table there). Do NOT start work from this doc alone — flip
> items in the plan and mirror them here. This doc stays the detail/evidence record.

> **NOTIFY-OPERATOR — fleet efficiency + account-budget burn.** Not a crash. The AO fleet spends the large majority of
> its spawns booting workers that immediately park on tasks no worker can complete, and the resulting churn is now
> eroding the usable account pool. This doc records the VERIFIED root cause and cross-references the three existing open
> gaps it is composed of. **No code was changed** — all live inspection was read-only (`state.db` opened `mode=ro`).

## Symptom (operator report, 2026-07-15)

The backend spawned workers (e.g. slot #14); each booted, asked for a task, and got
`no eligible task (prereqs/collisions block all candidates)` (the two worker-idle paths,
[slots_worker.py:216](../../../agent-orchestrator/server/routes/slots_worker.py#L216) /
[slots_worker.py:417](../../../agent-orchestrator/server/routes/slots_worker.py#L417)). Confirmed in slot-14's own
transcript (`~/.claude-configs/orch-slot-14/projects/.../*.jsonl`): a `/heartbeat` returned
`"no eligible task (prereqs/collisions block all candidates)","status":"idle"`. The operator's question: **why does the
backend spawn workers when the queue is blocked?**

## Root cause — the spawn gate is weaker than the dispatch gate (skip/role/collision-blind)

AutoSpawn decides "is there work worth spawning a worker for?" with a **strict subset** of the checks dispatch uses to
actually hand that work out:

| check                              | dispatch `pick_next_task` ([dispatch.py:52](../../../agent-orchestrator/server/dispatch.py#L52)) | AutoSpawn budget `_queued_undispatched_count` ([autospawn.py:340](../../../agent-orchestrator/server/autospawn.py#L340)) |
| ---------------------------------- | :----------------------------------------------------------------------------------------------: | :----------------------------------------------------------------------------------------------------------------------: |
| status == queued, undispatched     |                                                ✅                                                |                                                            ✅                                                            |
| formal `prereqs` met               |                                                ✅                                                |                                                            ✅                                                            |
| per-slot `slot_skips` (24h TTL)    |                                                ✅                                                |                                                            ❌                                                            |
| `assigned_role` craft gate         |                                                ✅                                                |                                  ❌ (only picks a spawn ROLE; budget counts all roles)                                   |
| repo / `collision_group` collision |                                                ✅                                                |                                                            ❌                                                            |
| affinity / `target_slot` routable  |                                                ✅                                                |                                                            ❌                                                            |

The most impactful omission is **`slot_skips`**. A task the whole eligible fleet has skipped (within the 24h TTL) is
effectively un-dispatchable, but the budget still counts it. So AutoSpawn keeps the worker pool at/near
`ORCHESTRATOR_FLEET_WORKER_CAP` (=14 here) and, every time a parked worker is reaped for idleness, **respawns it onto
the same un-claimable queue**. A freshly-spawned slot has an empty skip set, so it _can_ claim one of the fleet-skipped
tasks — boots, discovers the real blocker, calls `/skip-current-task`, parks. Cycle repeats.

This is **not a new finding**: it is the already-filed OPEN todo
`ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md` →
`[ ] [BACKEND] P2. Skip-exhaustion churn … Make the spawn gate/budget slot-skip-aware (don't count a task no live+eligible slot can take).`
This doc adds the live 2026-07-15 measurement + the compounding chain, and raises it to P1 because it is actively
burning the account pool (below).

## Evidence (live at-rest DB `/var/lib/orchestrator/state.db`, read-only; ref = last activity 05:15Z)

**Budget vs reality (within-TTL, replicating the dispatcher exactly):**

- `backlog.yaml` = 24 tasks (16 data_engineering, 7 backend_engineer, 1 generic); 15/31 `prerequisites` true → 16 false.
- **Spawn budget (prereq-met, queued, undispatched) = 6**, all `data_engineering`.
- **Claimable by any live slot (within-TTL skips + role + collision + affinity) = 1.**
- **Phantom (counted by the budget, claimable by nobody) = 5** — each skipped by **14–15 distinct slots within the 24h
  TTL** (every live DE slot has skipped all 5):
  - `mvp_backfill_defi_onchain_v10-002`, `mvp_backfill_defi_onchain_v10-003`
  - `sports_p2_features_history_to_ml_ready-001`, `-002`
  - `sports_travel_calculator_tz_aware_kickoff_crash-001`
- Skip reasons on these are genuine upstream gates, e.g. _"G2 gate NOT met on the 6 MVP defi data_types"_, _"3 gap-fill
  VMs still mid-migration"_, _"BLOCKED-PREREQ on parent plan sports_p2_features"_ — real blocks, recorded as per-slot
  skip reasons rather than as a park that removes them from the queue.

**Fleet + churn (activity_log, last 24h):**

| metric                   |                                                                    value |
| ------------------------ | -----------------------------------------------------------------------: |
| live slots               | 16 (13× data_engineering, 2× plan_health, 1× review; slot 0 main paused) |
| data_engineering workers |                               **13** — all `idle`, `current_task = NULL` |
| `autospawn_succeeded`    |                                                                 **1014** |
| `slot_boot`              |                                                                     1184 |
| `worker_polling_dead`    |                                                                      954 |
| `worker_kicked`          |                                                                     1548 |
| `task_dispatched`        |                                                                      217 |
| `slot_task_skipped`      |                                                                       98 |
| `slot_done`              |                                                                  **101** |

~10 spawns per completion; a ~1:1 worker-death→respawn loop refilling the pool onto 5 phantom + 1 real task. (The
snapshot's _all-idle_ is a moment during shutdown; the robust signal is the 24h churn ratio, not the instant.)

**Role starvation — NOT a current factor (checked to avoid mis-attribution):** zero `backend_engineer` tasks are
prereq-met right now (all 7 are prereq-blocked), so the all-`data_engineering` fleet is not stranding cross-role work
today. The 2026-07-14 role-starved-spawn fix (`agent-orchestrator@8a423bb`) is not contradicted by this snapshot.

**Compounding CONSEQUENCE — account-pool burn (new here):** the churn has driven weekly usage up; at snapshot,
`sub-c-ikenna-odum = 99%`, `sub-d-odum1default = 97%` — both **over the 95/95 spawn ceiling**
([autospawn.py:61](../../../agent-orchestrator/server/autospawn.py#L61)) → excluded from spawning. Only `sub-a` (84%)
and `sub-b` (68%) remain usable. Unlike 2026-07-07 (accounts verified healthy), the churn is now shrinking the rotation.
The model is `sonnet` fleet-wide (the 07-07 Opus/max freeze IS fixed), so this is Sonnet-weekly burn, not Opus — but it
is still real budget spent on boots that produce nothing.

## Why it keeps regenerating

> **CORRECTION (2026-07-15, reconciliation code-verify — supersedes an earlier draft of this section).** An earlier
> draft claimed the park mechanism was itself broken (`backlog_regen_drops_handtuned_prereqs_2026_07_12.md` "OPEN —
> regen silently reverts the park"). **That is stale.** That fix shipped `agent-orchestrator@8dd5763` on 2026-07-12 (the
> `priority_override` field; guard live at `regen_backlog_from_plan.py:1419` — `if not task.priority_override and …`),
> three days before this doc. I had reused the pre-fix evidence verbatim. The park mechanism now WORKS and survives
> regen. Corrected framing below.

The skip-blind budget would matter far less if the 5 genuinely-blocked tasks left the queue. What actually keeps them in
the queue:

1. **The working park was never APPLIED to these 5 (operational gap, not a code bug).** The sanctioned park — attach a
   false-valued prerequisite / raise `priority_override` (RULES.md §4) — now sticks across regen (`ao@8dd5763`). But
   nobody parked these tasks; they sit as plain `queued` rows with only per-slot _skip reasons_ recording the block.
2. **Skipping-with-a-reason doesn't remove them (gap boundary).** The orphan-on-skip path (`task_still_dispatchable()` →
   delete the `TaskRow`, `agent-orchestrator@3995384`, `backlog_blocked_marker_stale_brief_redispatch_2026_07_08.md`)
   only fires when the worker edits the **plan todo text** to add a `BLOCKED-*` marker. A skip carrying only a _reason_
   string (what these 5 show) doesn't trip it → the row stays `queued` and re-enters the budget.
3. **The spawn budget can't see they're fleet-skipped (this doc, genuinely unfixed).**

So the durable failure is: a working park exists but wasn't applied (1), skipping alone doesn't park (2), and the spawn
budget over-counts the un-parked fleet-skipped tasks (3). Fixing (3) is the general safety net; (1)/(2) determine
whether it needs to re-fire every ~24h.

## Fix options (NOT implemented — operator decision)

Core (needed either way): **make the spawn budget skip/role/collision-aware.** The exact predicate matters, because a
brand-new slot has an empty skip set:

- A "could a _hypothetical fresh_ slot claim it" predicate still counts all 6 (fresh slots carry no skips) → does NOT
  fix the churn.
- The correct predicate is "does an **existing live eligible** slot exist that has NOT skipped it within the TTL, with
  role/collision/affinity OK" — i.e. a task the whole live eligible fleet has already skipped is fleet-saturated and
  must NOT count. This is the open todo's phrasing ("no live+eligible slot can take it") and is what drops the live
  budget **6→1**, stopping the respawn engine.

Lowest-risk, directly closes the reported bug. It leaves the tasks retriable after the 24h TTL (a skip expires and one
slot becomes eligible again), so a short burst can recur every ~24h until the real blocker clears — which is why a
durable park (below) is the second half.

Durable (the park mechanism already works — `ao@8dd5763`; these APPLY it):

- **Auto-park in code:** when a task is skipped by ≥N distinct slots within the TTL with a `BLOCKED|PARKED|GATED`
  reason, set a false prerequisite / raise `priority_override` (with an unpark path when the condition clears). Makes
  the park survive the TTL automatically; introduces a threshold + reason-match policy.
- **Apply the park recipe operationally:** have the main agent (or an operator step) park a task once it's been
  fleet-skipped-with-blocked-reason, using the now-durable `priority_override`/false-prereq recipe. No new code; relies
  on someone actually doing it (the reason these 5 weren't parked).

## Recommended prevention todos (for a backend_engineer session; NOT auto-dispatched)

- [x] [BACKEND] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@7baeedc` (+ `bf9a61b` hardening).** Both functions now
      delegate to ONE shared SSOT, `dispatch.claimable_queued_task_ids`, derived from a `_FILTERS` table whose rows
      declare a `FilterScope` — so the budget and the dispatcher can no longer drift (sharing primitives alone was not
      enough; each caller composed its own list). Model tier + craft role are deliberately EXCLUDED from the budget
      (AutoSpawn chooses them at spawn time; filtering them in would starve the fleet — 4 tests pin it, 2 of them
      pre-existing). ~~**Skip/eligibility-aware spawn budget.**~~ Make `_queued_undispatched_count` + `_has_queued_work`
      ([autospawn.py](../../../agent-orchestrator/server/autospawn.py)) count a queued task only if some live eligible
      slot could claim it (reuse the `pick_next_task` predicate: within-TTL `slot_skips` + role + collision + affinity),
      not `prereqs_met` alone. Add a regression test: N tasks, all skipped by every live slot within TTL → budget 0 → no
      spawn. Closes the OPEN `Skip-exhaustion churn` todo in
      `ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md`.
- [x] [BACKEND] P2. ✅ **DONE — SHIPPED 2026-07-20, verified 2026-07-23 (`agent-orchestrator@cfb211c`, confirmed
      ancestor of `origin/live-defi-rollout`).** Delivered by `ao_dispatch_cooldown_and_park_2026_07_20.md` (archived
      2026_07) as the ONE fleet-scoped cooldown store this todo asked for — not a second mechanism. Verified by READING
      the code, not by trusting the commit message: `server/auto_park.py::maybe_auto_park` parks a task once
      `skip_count >= tuning.dispatch_cooldown_auto_park_skip_threshold` (default 3) on a `BLOCKED|PARKED|GATED`
      reason_code, applying exactly the recipe named below — `priority = 999`, `priority_override = True`, and a
      synthetic prereq `auto_unpark__<task_id>`; and `server/auto_park_reconcile.py::AutoParkReconciler` provides the
      condition-driven unpark path on a poll loop. So the visibility half this todo existed for is real: the give-up is
      now explicit and operator-visible rather than silent. **Doc drift, not a wrong verdict** — the tracker
      (`ao_open_issues_consolidated_close_out_2026_07_17.md`) has carried the authoritative DONE marker since
      2026-07-20; this doc was simply never updated to mirror it. Original item: **Durable park for repeatedly-skipped-
      with-blocked-reason tasks** — **was STILL OPEN, and R1 made it MORE important, not less (note added 2026-07-16).**
      R1 fixed the churn half: a task every slot has skipped now counts 0 toward the spawn budget, so the fleet stops
      respawning workers onto it. But that converts a LOUD failure (visible spawn churn) into a SILENT one — the task
      simply never spawns anything and nobody is told it is stuck. That is the same shape as `needs_operator_count`
      being computed and rendered nowhere. Durable park is the visibility half: make the give-up explicit and
      operator-visible rather than merely quiet. Out of scope for `ao_dispatch_hardening_2026_07_16` (that plan fixed
      dispatch correctness); this doc stays OPEN for it. Auto-park at ≥N distinct within-TTL skips carrying a
      `BLOCKED|PARKED|GATED` reason, via the now-durable `priority_override`/false-prereq recipe (park fix already
      shipped `ao@8dd5763`), with an unpark path when the condition clears. (The alternative is purely operational: have
      the main agent apply that recipe — no new code, but relies on it actually being done.)
- [x] [ADMIN] P2. ✅ **DONE 2026-07-16 — both halves.** (a) **Rotation recovered**: all 4 accounts probed directly via
      the live usage path 2026-07-16 ~08:12 UTC — sub-a 37%/7%, sub-b 25%/5%, sub-c 14%/3%, sub-d 0%/0% (5h/7d), all
      HTTP 200 `allowed`, binding window `five_hour`. Nothing near the 95% ceiling; the burn was intermittent, driven by
      the churn, and cleared when it stopped. (b) **Fleet-cap floor tied to CLAIMABLE work**: shipped as R1
      (`agent-orchestrator@7baeedc`) — the spawn budget IS the claimable count now, so an un-claimable queue yields
      budget 0 and cannot hold the pool at cap. The exact ask, implemented. ~~**Account-burn watch**~~ — the churn
      pushed sub-c/sub-d past the 95% weekly spawn ceiling; confirm the rotation recovers once the churn stops, and
      consider a fleet-cap floor tied to _claimable_ (not budget) work so an un-claimable queue can't hold the pool at
      cap.

## Verification / scrutiny performed (what was checked, and the corrections it forced)

Done specifically to avoid a mis-diagnosis (all reads `mode=ro`):

- ✅ **Within-TTL recompute.** Re-ran the fleet-skip count using the dispatcher's exact 24h-TTL filter
  (`slot_skipped_tasks`, [slots.py](../../../agent-orchestrator/server/state_store/slots.py)) against the snapshot's
  reference time — the 5 phantom tasks are skipped by 14–15 distinct slots _within_ the TTL, so this is live skip
  exhaustion, not stale-skip noise. (Corrected my first pass, which used all-time skips.)
- ✅ **Prereq parse.** Confirmed the `prerequisites` table (`name,value,set_by,set_at`) parse — 15/31 true; the 10
  prereq-blocked DE tasks are correctly excluded from the budget, so the formal prereq gate itself works.
- ✅ **Role-starvation ruled OUT for now.** No `backend_engineer` task is prereq-met, so I do **not** claim active
  cross-role starvation (my earlier hypothesis) — the all-DE fleet matches the only prereq-met role today.
- ✅ **Prior-art cross-reference.** Confirmed the core is the OPEN `Skip-exhaustion churn` P2 todo (independent
  agreement = corroboration, not novelty), and that the 07-07 fixes (tier propagation, craft filter, skip TTL) are IN —
  the fleet is Sonnet now, not the 07-07 Opus/max freeze — yet the churn persists because none of them touched the spawn
  budget.
- ✅ **Account health.** Read `account_usage`: sub-c 99% / sub-d 97% weekly (> 95% ceiling) → compounding burn, recorded
  as a consequence, not a root cause.
- ⚠️ **Snapshot caveat.** The at-rest DB shows all 13 DE slots idle including the 1 claimable task unclaimed — a
  shutdown-moment artifact, not steady state. The durable evidence is the 24h activity ratio (1014 spawns / 101 done),
  which does not depend on the instant.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-15** — Filed from an operator-reported slot-#14 "no dispatchable task" investigation. Root-caused via
  read-only inspection of `/var/lib/orchestrator/state.db` + backlog.yaml + slot-14 transcript + the autospawn/dispatch
  source. Confirmed = the OPEN `Skip-exhaustion churn` P2 in
  `ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md`; added live measurement (6 budget / 1 claimable / 5
  phantom, 14–15 within-TTL skippers; 1014 spawns vs 101 done/24h) + the regen-park-revert (gap 1) and
  skip-reason-vs-plan-marker (gap 2) compounding chain + the account-burn consequence. No code changed. Fix scope
  deferred to operator (skip-aware budget only vs also auto-park).
