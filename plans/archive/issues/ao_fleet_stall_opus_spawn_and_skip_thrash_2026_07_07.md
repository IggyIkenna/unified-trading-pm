---
doc_type: issue
title:
  AO fleet stalled idle with ready tasks — backlog tier/role frozen (regen no-propagate) + no craft filter + slot_skips
  thrash
summary:
  On 2026-07-07 the agent-orchestrator fleet sat idle (0 working, 14 idle slots) while 30 tasks were queued and
  blocker-free. Not a crash — the server + VM were healthy and AutoSpawn was spawning workers every ~30s. Root causes
  compounded — the whole backlog was frozen at model=opus/effort=max (regen does not propagate plan frontmatter
  tier/role changes to already-queued tasks), so every spawn was Opus/max (a cost inefficiency — the accounts themselves
  are healthy, verified live); pick_next_task has no assigned_role craft filter, so infra tasks dispatched to
  data_engineering slots and were skipped; 326 per-(slot,task) slot_skips accumulated and persist across respawns,
  starving dispatch; and the monitor agents over-generalized one sports gate to the whole backlog and went passive. This
  doc records the failure mode + the prevention fixes so it does not recur.
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, autospawn, slot-skips, model-tier, craft-routing, fleet-stall, incident]
related:
  [
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    ../infra_capture_and_devops_leftovers_2026_07_06.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/issues/ao_blocked_queue_operator_ruling_sync_gap_2026_07_13.md,
  ]
created: 2026-07-07
last_updated: 2026-07-16
parent_epic: orchestrator_master
priority: P0
source: fleet-idle investigation 2026-07-07 (operator-reported no workers running)
assigned_vm: NA
resolved_by:
  - "agent-orchestrator@ff6100ad + @c6a31ed6 — RC-1: `_reconcile_task_fields` propagates a plan retier (model/effort/
    thinking/assigned_role/priority) onto already-queued tasks, auto-healing the frozen opus/max backlog on the next
    regen tick (regen_backlog_from_plan.py:1256 call site, :1398 definition)"
  - "agent-orchestrator@f976b6e4 — RC-2: `_blocks_craft_role` is a live FilterScope.CAPABILITY row in the `_FILTERS`
    table (dispatch.py:142); a slot with a declared craft never claims a mismatched task"
  - "agent-orchestrator@07035aba — RC-3: slot_skips hygiene — `slot_skip_ttl_hours` (config.py:643) consumed at
    dispatch.py:300, plus `clear_slot_skips_for_task` + /unskip-task + /clear-skips routes"
  - "agent-orchestrator@6ae43b5 — R2: `_spawn_param_plan` resolves per-slot spawn params starved-role-first;
    `_top_queued_task_params` DELETED (zero hits repo-wide — removed, not shimmed)"
  - "unified-trading-pm@5a79c4c23 — R3/R4 prompt guards in agents/main.md STEP 2.4/2.6 + monitor.md: never conclude
    fleet-deadlock from ONE gated task; a stall belief is a HYPOTHESIS until measured per-task"
  - "VERIFIED 2026-07-17 by independent skeptical audit: all 5 SHAs reachable on origin/live-defi-rollout and every
    claimed fix confirmed PRESENT at HEAD (not reverted by later refactors)"
locked_by:
locked_since:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: high
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
---

> **✅ ACKED-INTO-CODE 2026-07-17 — all 6 todos closed; archived.** R2 (mixed-tier spawn) shipped at
> `agent-orchestrator@6ae43b5`; R3/R4 (the monitor/main prompt guards) at `unified-trading-pm@5a79c4c23`. Absorbed by
> [`ao_dispatch_hardening_2026_07_16`](../../active/ao_dispatch_hardening_2026_07_16.md), whose Phase 3 gate has since
> passed **on the live dispatch rate** — the bar this doc's incident deserved: spawns now TRACK dispatches (last 12h 3/3
> = 1.00:1) against the 44:1 baseline that produced this stall. `resolved_by` carries all 5 SHAs + an independent
> 2026-07-17 audit confirming each is present at HEAD and not reverted by later refactors.
>
> **The correction worth carrying**: this doc's root cause blamed `_top_queued_task_params` picking the top task's tier
> — true, and R2 DELETED that function. But the fleet-stall class survived R2 and took two more fixes to actually kill
> (`@6c778e6`, `@f8ace1f`), because the spawn budget is a COUNT and could be satisfied by a slot that was not the slot
> being spawned. If you are here to understand why the fleet stalled, the full arc is in that plan's Phase 3, not here.

> **Historical — the incident as filed.** **NOTIFY-OPERATOR incident (fleet availability).** 2026-07-07: the AO fleet
> went idle overnight with ~30 ready tasks queued. Investigated live (SSH + `state.db` + `/api/*`). NOT a crash — a
> compounded dispatch stall. This doc is the root-cause + prevention record.

## Symptom

- `/api/fleet/summary`: `slots_working=0`, `slots_idle=14`, `backlog_queued=30`, `backlog_dispatched=1`.
- `/api/backlog/{id}/blockers` for the queued tasks: **"ready (no blockers)"**.
- VM healthy (24d uptime, 53 GiB free RAM, 111 GiB free disk); server up on `127.0.0.1:8765`; AutoSpawn firing
  `autospawn_succeeded` every ~30s (journalctl: `--model opus --effort max --max-thinking-tokens 31999`).
- The main + monitor agents looped `"fleet deadlocked"` /
  `"30 tasks queued all gated on understat prereq → continue monitoring"`.

## Root causes (compounded — no single bug)

1. **Backlog tier/role FROZEN — regen does not propagate plan frontmatter changes (PRIMARY).** The DB `tasks` table
   stores neither `model` nor `assigned_role`; those live on the `backlog.yaml` `BacklogTask`, set by
   `regen_backlog_from_plan.py` at task CREATION. Regen is idempotent-by-brief
   (`if description in existing_briefs: skip`), so when a plan's `model_tier` / `thinking_tier` / `assigned_role` change
   later, the **already-queued tasks keep their original tier/role**. Evidence: after retiering all 6 plans to
   Sonnet/high, every queued task still read `model=opus effort=max` (incl. `tradfi_v9_stage1_finish-004`, whose plan
   was Sonnet since 2026-07-06), and `infra_capture_and_devops_leftovers-001` still read `role=infra` after the plan was
   re-homed to `data_engineering`. → **Every spawn is Opus/max** (`_top_queued_task_params` picks the top task's tier) —
   a cost inefficiency (burns Opus quota for tasks the plans intended to run cheap on Sonnet), though NOT an
   availability blocker since the accounts are healthy (RC-5).

2. **`pick_next_task` has NO `assigned_role` craft filter.** `server/dispatch.py::pick_next_task` filters on status,
   model-tier, deferred-prefix, prereqs, affinity(target_slot), repo-collision, collision_group, and slot_skips — but
   **not craft/role**. So an `assigned_role: infra` task is dispatched to a `data_engineering` slot, which then refuses
   it at the worker level ("role mismatch — data_engineering slot cannot execute infra-scoped task") and calls
   `/skip-current-task`. The `long_lived_vm_logs` infra task was re-dispatched to the wrong craft **6 times in one day**
   (the plan's own Progress Log recommends "land the AO dispatcher-side `assigned_role` filter").

3. **`slot_skips` accumulate and persist across respawns.** Each craft-mismatch / prereq-park / context-limit skip
   writes a per-(slot_id, task_id) row (`slot_skips`), and `pick_next_task` excludes them (filter 6). Skips are keyed by
   **slot_id, not worker session** — so when AutoSpawn respawns a worker on the same slot, it INHERITS the slot's old
   skips. Overnight this reached **326 rows across 95 tasks × 13 slots (~30/slot)** and starved dispatch (though not to
   a full deadlock — every slot could still take 15-30 of the 30 queued; it was thrash + partial starvation, not a hard
   lock).

4. **Monitor agents over-generalized one real gate.** One genuine sports gate (understat backfill VM incomplete) was
   extrapolated by the main + monitor agents to `"30 tasks all gated on understat prereq"`, and they dropped into
   passive monitoring instead of dispatching — even though the blockers API said the tasks were ready.

5. **Account status — VERIFIED HEALTHY 2026-07-07, NOT a root cause.** A live `claude /usage` refresh on all 4 accounts
   (each via its own `oauth_token_env_file`; probe SUCCEEDED = tokens authenticate) returned `unified_status: allowed`
   for all 4, none rate-limited (`rate_limited_until` all stale at 2026-07-01, expired), with subscription headroom
   (weekly 25-78%, 5h 12-19%). The `overage_status: rejected` (sub-c `out_of_credits`; sub-a/b/d `org_level_disabled`)
   governs only PAID OVERAGE beyond the subscription — it does NOT block normal in-quota use. Earlier framing of
   accounts as a blocker was WRONG; corrected here. The Opus/max load (RC-1) is a COST/efficiency problem, not an
   availability one.

## Immediate remediation applied 2026-07-07

- ✅ Retiered all 6 instruments-completion plans to Sonnet/high (Plan 1 was the last Opus one; its C2 justification
  shipped `is@2170d9a3`) — `unified-trading-pm@65e5d01ee`. _(Plan-level; inert on existing backlog tasks until RC-1 is
  addressed — see below.)_
- ✅ Re-homed `infra_capture_and_devops_leftovers` role `infra` → `data_engineering` + `[INFRA]`→`[DATA]` retag — same
  commit. _(Same RC-1 caveat.)_
- ✅ Cleared the 145 `slot_skips` rows tied to the 30 queued tasks (backup: VM `/tmp/slot_skips_backup.json`) — fleet
  began resuming (`working` 0→1, `dispatched` 1→2).
- ✅ **RESOLVED by option (b) — no operator decision needed after all (closed out 2026-07-17).** This item asked the
  operator to choose how to make the retier effective on the frozen backlog: (a) one-time scoped hand-correction of the
  6 plans' tasks — which crosses the **"never hand-edit backlog.yaml"** HARD RULE; (b) fix RC-1 in regen + reload; or
  (c) delete+regen (new IDs, lost dispatch state). **Option (b) shipped** (`agent-orchestrator@ff6100ad` + `@c6a31ed6` —
  `_reconcile_task_fields`), and it auto-heals the frozen backlog on every regen tick, so (a)'s rule-crossing and (c)'s
  state loss were both avoided. The marker was simply never cleared: it sat here for 10 days as a phantom decision
  request that the code had already answered — found by the 2026-07-17 verification audit, not by a reader. **Kept
  visible rather than deleted**: a stale "PENDING OPERATOR DECISION" is exactly the kind of false signal that makes a
  doc corpus untrustworthy, so the correction is recorded in place.
- ✅ Accounts verified HEALTHY (live `/usage` refresh 2026-07-07) — all 4 `unified_status: allowed`, authenticated, not
  rate-limited, subscription headroom. The overage-rejected flags are not a blocker. NO operator action needed on
  accounts.

## Prevention (the fix-so-it-doesn't-recur todos)

- [x] [CODE] P0. **regen must propagate tier/role changes to existing queued tasks** — when a plan's
      `model_tier`/`thinking_tier`/`assigned_role` changes, update the matching `backlog.yaml` tasks (match by
      `plan_ref` + brief) instead of skip-on-dedup. Or add an explicit `POST /api/backlog/retier-from-plans` refresh op.
      This is the PRIMARY gap — without it, every plan retier is silently inert on in-flight work. —
      agent-orchestrator@ff6100ad + agent-orchestrator@c6a31ed6 (RC-1 reconcile, Phase 2 Batch A+B:
      `_reconcile_task_fields` brief-matches queued/blocked/dispatched tasks and updates
      model/effort/thinking/assigned_role/priority in place — "auto-heals the frozen opus/max backlog on the next tick")
      per ../ao_dispatch_correctness_regen_reconcile_2026_07_07.md Progress Log (2026-07-07 entries); flipped 2026-07-12
      per operator ruling (finding 218, plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md §A2).
- [x] [CODE] P0. **Add an `assigned_role` craft filter to `pick_next_task`** — a task whose `assigned_role` has no
      matching-craft idle slot should NOT be dispatched to a mismatched slot (leave it queued, like the model-tier
      gate). Kills the dispatch→skip→re-dispatch craft-mismatch thrash (6× in one day on one task). —
      agent-orchestrator@f976b6e4 (RC-2 dynamic craft routing + stickiness, Phase 4: per-task role from `[TAG]`,
      `SlotRow.last_role`, "ADOPT, don't refuse" HARD RULE replacing the worker-level role-refusal →
      `/skip-current-task` path — kills the craft-mismatch thrash via dynamic boot-load rather than a queue-side filter,
      same effect) per ../ao_dispatch_correctness_regen_reconcile_2026_07_07.md Progress Log; flipped 2026-07-12 per
      operator ruling (finding 218).
- [x] [CODE] P1. **`slot_skips` hygiene** — expire skips after N hours, and/or clear a task's skips when its plan
      changes (tier/role/brief) or a prereq lands, and/or scope craft-mismatch skips so a re-home clears them. Persisted
      per-slot skips inheriting across respawns is the starvation multiplier. — agent-orchestrator@07035aba (RC-3, Phase
      5: `slot_skip_ttl_hours` TTL expiry default 24h + regen-prune clears on GC'd/cancelled tasks +
      `clear_slot_skips_for_task` primitive for plan-change clears + `/unskip-task`/`/clear-skips` APIs) per
      ../ao_dispatch_correctness_regen_reconcile_2026_07_07.md Progress Log; flipped 2026-07-12 per operator ruling
      (finding 218).
- [x] [CODE] P1. ✅ **DONE 2026-07-16 — `agent-orchestrator@6ae43b5` (R2).** `_spawn_param_plan` yields one
      `(model, effort, thinking, role)` entry per CLAIMABLE task; the i-th slot spawned takes the i-th entry, so 1 opus
      P0 above 29 sonnet tasks now boots ONE opus worker, not the whole tick. `assigned_role` travels per-slot too (it
      was a tick-wide value closed over by the slow section). The old "Known limitation" docstring is deleted;
      `_top_queued_task_params` was DELETED rather than shimmed. ~~**AutoSpawn should not spawn the whole tick at the
      top task's tier when the queue is mixed-tier**~~ — spawn per-task-tier (or at least don't force Opus for a queue
      that is 29/30 Sonnet). Ref `_top_queued_task_params` "known limitation".
- [x] [DESIGN] P2. ✅ **DONE 2026-07-16 (R3).** `agents/main.md` STEP 2.4 — never conclude "the fleet is deadlocked"
      from ONE gated task; PROVE it per task via `GET /api/backlog/{task_id}/blockers` before stopping dispatch (≥1
      `ready (no blockers)` ⇒ NOT deadlocked ⇒ the problem is spawn/dispatch-side). `agents/monitor.md` — alert on what
      you MEASURED, never on what you infer; a fleet-stall belief is a HYPOTHESIS, not a breach, and must never be the
      reason dispatch stops. ~~**Monitor/main agent guard**~~ — do not extrapolate a single task's gate to the whole
      backlog; re-check `/api/backlog/{id}/blockers` before declaring "fleet deadlocked" and going passive.
- [x] [ADMIN] P2. ✅ **DONE 2026-07-16 (R4).** `agents/main.md` STEP 2.6. Note the framing CHANGED with R2: per-slot
      spawn params remove the COST blow-up (one opus plan no longer drags every worker up a tier), so the residual
      guidance is about queue SHAPE, not cost — and it explicitly forbids the tempting wrong fix of re-tiering plans to
      smooth the queue, which would trip the worker's own SSOT self-check on "Sonnet on opus-required". ~~**Operating
      guidance**~~ — avoid a single high-priority Opus plan mixed with Sonnet plans in the same queue (it drags every
      spawn to Opus until RC-4 is fixed); if a plan genuinely needs Opus, isolate it.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-13** — Checked against a separate operator-reported gap ("operator rulings never reach the AO
  blocked-question queue", proven on `BLK-f2bb67c2`). Confirmed the 3 remaining open prevention todos here (AutoSpawn
  per-task-tier spawning, monitor/main-agent gate over-generalization, Opus/Sonnet plan-mixing guidance) are all about
  dispatch/tiering, NOT `blocked_queue` — none satisfied by the fix. Filed + shipped as its own issue:
  `ao_blocked_queue_operator_ruling_sync_gap_2026_07_13.md` (`BlockedQueueReconciler`,
  agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009). No todos here flipped — genuinely a different gap.
- **2026-07-07** — Filed from the fleet-idle investigation. RC-1 (regen no-propagate → whole backlog frozen Opus/max) is
  the primary finding; RC-2 (no craft filter) + RC-3 (slot_skips thrash) compound it. Remediation applied: plans
  retiered/re-homed (`pm@65e5d01ee`), 145 queued-task slot_skips cleared (fleet resuming). Backlog tier-correction +
  account credits pending operator.
