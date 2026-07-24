---
doc_type: issue
title: "AutoSpawn role-blind spawn stranded infra/backend/cicd dispatchable work (2026_07_14)"
created: 2026-07-14
parent_epic: agent_operating_framework_master
assigned_vm: NA
source:
  - server/autospawn.py
  - server/dispatch.py
locked_by:
summary:
  "AutoSpawn spawned every worker in a tick at ONE role — the global (tier,priority)-top queued task's assigned_role.
  With a data_engineering task on top, the whole fleet respawned as data_engineering while 19 infra + 11
  backend-engineer + 1 cicd dispatchable tasks (incl. the deployment_registry Firestore P0 migration) sat unclaimable
  behind the dispatch role-gate. Reviving dead slots did not help — they came up as the same wrong role (fleet-wide idle
  churn: 6 dispatches vs ~60 respawns/kicks per window). FIXED: _top_queued_task_params now prefers a STARVED role
  (dispatchable work, no live worker). Two related dispatch gaps remain open (operator decision)."
status: resolved
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, autospawn, dispatch, role-gate, dispatch-correctness]
related:
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
priority: P1
resolved_by: agent-orchestrator@8a423bb
superseded_by: ../../active/ao_dispatch_hardening_2026_07_16.md # 2026-07-16: the two open follow-up gaps (skip-exhaustion churn -> R1, dead-slot affinity spill -> R5) were re-verified STILL-BROKEN and absorbed by that plan. This pointer was MISSING at archival, which orphaned the work and caused it to be re-discovered + re-filed a day later as ao_skip_blind_spawn_budget_phantom_churn_2026_07_15. The headline fix (ao@8a423bb) stands and is live.
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-16
---

# AutoSpawn role-blind spawn stranded infra/backend/cicd dispatchable work

## Symptom (operator report, 2026-07-14)

The deployment_registry Firestore migration plans were "not being picked up." Deeper: idle slots weren't getting work
and dead slots weren't being revived, while ~60 tasks sat queued. Only 2–3 slots did real work; the rest churned (spawn
→ boot → "no dispatchable work" → watchdog kill → respawn). In one ~400-event window: **6 `task_dispatched` vs 29
`autospawn_succeeded` + 34 `worker_kicked` + 26 `worker_polling_dead`.**

## Root cause

Dispatch is role-gated ([dispatch.py](../../../agent-orchestrator/server/dispatch.py) `pick_next_task`): a slot with a
`slot_role` never claims a task whose `assigned_role` differs. AutoSpawn's spawn planner
([autospawn.py](../../../agent-orchestrator/server/autospawn.py) `_top_queued_task_params`) picked **one** role per tick
— the global `min(tier, priority)` queued task's `assigned_role` — and booted **every** spawned worker at it (the
documented "Known limitation"). Measured live demand vs supply at report time:

| assigned_role        | dispatchable queued | live workers |
| -------------------- | ------------------: | -----------: |
| data_engineering     |                  31 |            6 |
| **infra**            |              **19** |        **0** |
| **backend-engineer** |              **11** |        **0** |
| **cicd**             |               **1** |        **0** |
| review               |                   2 |            1 |

With a data_engineering task on top, AutoSpawn kept respawning data_engineering workers (incl. reviving dead slots as
data_engineering), so the 31 infra/backend/cicd/review tasks — including deployment_registry P0 todos (per-task roles:
`backend-engineer` / `infra` / `review`) — could never be claimed. The fleet-worker cap (10) was consumed by the
churning data_engineering slots, so dead higher slots (incl. the `backend-engineer` slot 13) were never reached.

## Fix (shipped — agent-orchestrator@8a423bb)

`_top_queued_task_params(session, backlog, alive_roles=None)` now, when `alive_roles` is supplied, prefers a
dispatchable task whose `assigned_role` has **no live worker** — so AutoSpawn stands up each role the queue needs, one
starved role per tick, with dead/idle slots respawning AT that role (repurposing churn). `alive_roles` absent ⇒ prior
global-top behaviour (back-compat). Unit test: `test_top_queued_params_prefers_starved_role`. QG green (1251 passed).

**Verified live on the planning VM** (`--reload` picked it up): within two ticks, `backend-engineer` workers came up
(slots 3, 11) and `deployment_registry_firestore_p0_unblock-001` dispatched to slot 3. Role mix shifted from
all-`data_engineering` to a diversified fleet.

## Open follow-up gaps (NOT dispatched — operator decision)

> **✅ ACKED-INTO-PLAN 2026-07-16 — both follow-ups re-verified STILL-BROKEN and absorbed by
> [`ao_dispatch_hardening_2026_07_16`](../../active/ao_dispatch_hardening_2026_07_16.md) as R1 and R5.** Archiving this
> doc on 2026-07-14 with these two `- [ ]` live-code bugs still open, and **no `superseded_by` pointer**, orphaned the
> work: it was not tracked forward, it was **independently re-discovered a day later** and re-filed as
> `ao_skip_blind_spawn_budget_phantom_churn_2026_07_15` (P1, escalated with a live measurement). That duplicate-by-
> rediscovery is the exact cost of archiving a doc whose todos aren't closed or forwarded — see the AO issue register in
> [`epics/orchestrator_master.md`](../../epics/orchestrator_master.md).
>
> Both re-verified against code 2026-07-16 (this doc's headline fix, `agent-orchestrator@8a423bb`, IS genuinely live at
> `server/autospawn.py:388-451` — the archival was right about that, only incomplete):
>
> - **Skip-exhaustion churn → R1.** Still broken: `rg slot_skip server/autospawn.py` → **0 hits**;
>   `_queued_undispatched_count` (`autospawn.py:340-385`) has no skip/role/collision/affinity check, vs
>   `dispatch.py:74,126` which does. Measured 2026-07-15: budget=6, claimable=1, 5 phantom.
> - **Dead-slot affinity spill → R5.** Still broken: `dispatch.py:289-290` `if affinity == "high": return False` —
>   unconditional, no liveness fallback (contrast the `low` branch at :291-294 and the medium timeout at :295-304, both
>   of which DO fall back).
>
> The todos are struck below rather than deleted, so the provenance survives. **Do not fix from this doc** — the plan's
> R1/R5 carry the sharper spec (shared eligibility predicate, per-item unit-test gates) and a dead-slot threshold
> modelled on `failover.py`'s 600s pattern rather than a naive "slot missing → spill immediately", which would defeat
> the session-continuity guarantee `affinity=high` exists to provide.

- [x] [BACKEND] P2. ~~**Skip-exhaustion churn**~~ → **R1 of `ao_dispatch_hardening_2026_07_16`** (re-verified
      STILL-BROKEN 2026-07-16). `slot_skips` (TTL `slot_skip_ttl_hours=24h`) survives respawn, so a slot that skips its
      role-matched tasks (as already-done / BLOCKED-PREREQ) boots straight back to "no dispatchable work" → watchdog
      kill → respawn. `_has_queued_work` / spawn budget count these skip-exhausted tasks as spawnable, so the fleet
      still churns on them. Make the spawn gate/budget slot-skip-aware (don't count a task no live+eligible slot can
      take).
- [x] [BACKEND] P2. ~~**High-affinity task pinned to a DEAD slot never spills**~~ → **R5 of
      `ao_dispatch_hardening_2026_07_16`** (re-verified STILL-BROKEN 2026-07-16) —
      [dispatch.py](../../../agent-orchestrator/server/dispatch.py) `_task_is_routable_to`: `affinity == "high"` returns
      False for every non-target slot, with no dead-target fallback. Two tasks were stranded this way
      (`mvp_backfill_defi_onchain_v10-002` → slot 15 dead; `bybit_futures_chain_write_shape_migration-007` → slot 14
      dead) and were **manually unblocked 2026-07-14** (runtime `release_task_to_queue(affinity="none")` + cleared
      `target_slot`; both immediately dispatched to slots 8 and 3). The **code gap is still open**: add a spill when the
      pinned target slot has been dead/absent beyond a threshold, so this doesn't recur.
- [x] [BACKEND] P1. **Context-saturation resume loop (FIXED)** — a dead worker with a (near-)full context window was
      `--resume`d into the SAME saturated conversation, which re-wedged instantly; AutoSpawn retried the resume until
      the spawn-retry cap, then gave up ("stays down until manual respawn or reclaim") — the slot-2 100%-context /
      38-compaction heartbeat-silent wedge that needed a manual reclaim. **Fix (agent-orchestrator, 2026-07-14):**
      `resume_lifecycle.classify_dead_worker` now requeues (fresh spawn) when `context_used_pct >=`
      `resume_fresh_context_pct` (default **95** — a saturated session is un-continuable), and `autospawn._do_spawn`
      leads the resume nudge with an explicit `/compact`-FIRST instruction when the resumed context is `>=`
      `resume_compact_first_context_pct` (default **80**) so it preserves a summary of the prior run instead of
      re-saturating. Also surfaced **model + context%** columns in the dashboard AgentTypesPanel (parity with the fleet
      slot view) so an approaching-saturation main/review/typed agent is visible before it wedges. Remaining hardening
      (optional): also force a fresh session when a worker goes heartbeat-silent at high context even outside the resume
      path.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (role-based dispatch)
- `/codex/04-architecture/runtime-deployment-topology.md` </content>

</invoke>
