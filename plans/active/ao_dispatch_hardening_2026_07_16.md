---
doc_type: plan
title:
  AO dispatch hardening — eligibility-aware spawn budget, per-task tier spawn, dead-slot spill, worker-role gate
  (R1/R2/R5/R6)
summary: |
  Fix the four code-confirmed dispatch/autospawn residuals that keep the AO fleet running below designed capacity —
  dead slots respawned onto un-claimable work (credit burn), mixed-tier queues starved, high-affinity tasks stranded on
  dead slots, and review/main slots claiming worker tasks. All four live in two files (server/autospawn.py +
  server/dispatch.py) so they share one plan and one QG sweep. Human-executed — AO itself is too degraded to be trusted
  to dispatch its own fix.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, autospawn, spawn-budget, role-gate, affinity, credit-burn, fleet-capacity]
related:
  [
    issues/ao_dispatch_residuals_2026_07_15.md,
    issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md,
    issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md,
    issues/dispatcher_role_eligibility_gap_review_slots_2026_07_13.md,
    ../archive/issues/ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md,
    ../epics/orchestrator_master.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  - operator 2026-07-16 — "our current immediate scope is to make the AO work properly ... it finished some tasks and
    left others undone, worker agents might work or they just sit idle in the loop burning credits ... it doesn't work
    at the capacity it was designed for"
  - issues/ao_dispatch_residuals_2026_07_15.md (R1-R7 index; R1/R2/R5/R6 code-confirmed)
  - AO issue-doc audit 2026-07-16 (10 parallel verification agents)
---

# AO dispatch hardening (R1/R2/R5/R6)

> **Human plan — I execute it** (`assigned_vm: NA`). Deliberately NOT AO-dispatched: this fixes the very machinery that
> dispatches, and the bugs below can starve/skip the fix itself. Ships via `quickmerge.sh --agent --files`.

## Why

Operator (2026-07-16): _"there are so many issues and bugs that it's hard to allocate the plan to it. It finished some
tasks and left others undone, worker agents might work or they just sit idle in the loop burning credits. We think work
is being done but it doesn't work at the capacity it was designed for."_

Those symptoms are not vague — they map 1:1 onto four **code-confirmed** residuals, all verified against live code on
2026-07-16:

| Symptom (operator)                           | Residual | Root cause (verified)                                                                                                                                              |
| -------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| workers sit idle in the loop burning credits | **R1**   | spawn budget is **skip-blind** — `rg slot_skip server/autospawn.py` → **0 hits**; fleet-skipped tasks still inflate it → respawn dead slots onto un-claimable work |
| we think work is being done but it isn't     | **R6**   | `pick_next_task` has no **agent-role** gate; review/main slots never set `slot_role` → read as generic → claim worker tasks, then skip them                        |
| doesn't work at designed capacity            | **R2**   | AutoSpawn resolves ONE `(model, role)` tuple per tick and spawns every slot at it → a mixed-tier queue starves everything but the top task's tier                  |
| finishes some tasks, leaves others undone    | **R5**   | a task pinned `affinity=high` to a **dead** slot never spills → silently stranded forever                                                                          |

Measured blast radius (from `ao_skip_blind_spawn_budget_phantom_churn`, 24h window): **~1014 autospawns / 1184 boots /
954 deaths → 217 dispatches / 101 done**; budget=6 vs claimable=1 (5 phantom); pushed 2 of 4 accounts past the 95%
weekly ceiling on 2026-07-15, shrinking usable rotation to 2. (Accounts had recovered to 0–7% by 2026-07-16 — the burn
is intermittent, the code defect is permanent.)

## Verified code anchors (2026-07-16, current HEAD)

- **R1** — `server/autospawn.py:317` `_has_queued_work` / `:340` `_queued_undispatched_count` filter only
  `status=="queued"` + `dispatched_to is None` + `prereqs_met`. `server/dispatch.py:52` `pick_next_task` additionally
  filters model-tier, craft/role gate, affinity (`_task_is_routable_to`), repo/collision-group, and **`slot_skips`**
  (24h TTL). The asymmetry IS the bug.
- **R2** — `server/autospawn.py:388` `_top_queued_task_params`, called ONCE per tick at `:1646`, before the per-slot
  spawn loop. Its own docstring (`:415`) still admits: _"Known limitation: in a MIXED-tier / MIXED-role queue, all slots
  spawned in one tick use the top task's tier + role."_
- **R5** — `server/dispatch.py:257` `_task_is_routable_to`; `:289` `if affinity == "high": return False` — unconditional
  for every non-target slot, no dead/absent-target fallback.
- **R6** — `server/dispatch.py:79` reads `slot_row.slot_role`; the gate at `:97` no-ops when it's `None`.
  `server/prompts.py:206` sets `slot_role` **only** in `render_worker()`; `render()` (review/main) never does.
  `SlotRow.slot_role` is written only from `req.slot_role` at `server/routes/slots_worker.py:114`. True agent identity
  lives on `AgentRow.role` (`server/orm.py:290`, values `main`/`review`/`custom`), which `dispatch.py` never joins. Both
  `/boot` and `/heartbeat` call `pick_next_task` (`slots_worker.py:204,408,957`) → one shared fix covers both.

## Todos

### Phase 1 — stop the burn (P0)

- [ ] [BACKEND] P0. **R1 — eligibility-aware spawn budget.** Extract `pick_next_task`'s eligibility predicate into one
      shared helper (single SSOT for "is this task claimable by any live slot?") and make
      `_has_queued_work`/`_queued_undispatched_count` (`server/autospawn.py:317,340`) use it, so skip-exhausted /
      role-ineligible / collision-blocked / affinity-pinned tasks stop inflating the spawn budget. **Gate**: a task
      skipped by every eligible slot counts 0 toward the budget; existing autospawn tests stay green. Closes R1 + the
      `Skip-exhaustion churn` carry-forward stranded in archived `ao_autospawn_role_blind_dispatch_starvation`.
- [ ] [BACKEND] P0. **R6 — worker-role dispatch gate.** Gate `pick_next_task` (`server/dispatch.py:52`) so only slots
      whose **agent** role is a worker receive a backlog `task_id` (join slot→`AgentRow.role`, or thread the role
      through boot/heartbeat — pick whichever avoids a per-call join in the hot path). Keep the existing craft
      `slot_role` check as-is; this is a distinct, upstream gate. **Gate**: regression test dispatching a backlog task
      to a `review`-role and a `main`-role slot via BOTH `/boot` and `/heartbeat`, asserting no `task_id` is returned.

### Phase 2 — restore designed capacity (P1)

- [ ] [BACKEND] P1. **R2 — per-task tier/role spawn.** Resolve the spawn `(model, effort, thinking, role)` **per slot
      being spawned** instead of once per tick (`server/autospawn.py:1646` + `_top_queued_task_params:388`), so a
      mixed-tier queue stands up the right tier per slot. Delete the now-false "Known limitation" docstring at `:415`.
      **Gate**: unit test — a queue holding one opus task + one sonnet task spawns one slot per tier in a single tick.
- [ ] [BACKEND] P1. **R5 — high-affinity dead-slot spill.** In `_task_is_routable_to` (`server/dispatch.py:257`),
      replace the unconditional `if affinity == "high": return False` (`:289`) with a liveness-aware check — a
      high-affinity task whose `target_slot` is dead/absent must spill to another eligible slot; a task whose target is
      alive must still NOT spill. **Gate**: two unit tests (dead target → spills; live target → does not).

### Phase 3 — prove it (P0)

- [ ] [BACKEND] P0. Regression suite green + full `bash scripts/quality-gates.sh` on agent-orchestrator; ship via
      `quickmerge.sh "fix(dispatch): ..." --agent --files '<paths>'`. **Gate**: QG green + `Quickmerge:` trailer + LDR
      landed.
- [ ] [OPERATOR] P0. **Runtime verification — the real bar.** After the ship, measure the churn ratio over a live window
      and compare to the 24h pre-fix baseline (**1014 autospawns / 954 deaths → 217 dispatches / 101 done**). **Gate**:
      autospawn:dispatch ratio materially down + no idle-respawn loop on a fleet-skipped task. Code-shipped ≠ fixed —
      this plan is not done until the burn is measured to have stopped.

### Phase 4 — close the paper trail (P2)

- [ ] [BACKEND] P2. Document the (now-fixed) spawn-budget contract in
      `codex/04-architecture/agent-orchestrator-autospawn.md` — the doc-gap flagged as X3's third corroboration in
      `ao_docs_reconciliation_2026_07_15`.
- [ ] [BACKEND] P2. Clean the stale `recovery-audit` comment at `server/routes/agents.py:146` (carried from the
      recovery-audit ruling — a one-line cleanup deliberately batched here to avoid a separate code ship).
- [ ] [REVIEW] P2. Close out the source issue docs once Phase 3's runtime gate passes — archive
      `ao_skip_blind_spawn_budget_phantom_churn` (R1), `dispatcher_role_eligibility_gap_review_slots` (R6),
      `ao_dispatch_residuals` (R1-R7 index; note R3/R4/R7 disposition explicitly, don't let them go dark), and flip
      `ao_fleet_stall_opus_spawn_and_skip_thrash`'s R2 todo. **Gate**: no residual left without a home.
- [ ] [REVIEW] P2. Fix the F5 epic seam: `ao_skip_blind_spawn_budget_phantom_churn` carries
      `parent_epic: agent_operating_framework_master` while every other dispatch-code doc/plan uses
      `orchestrator_master`. Repoint it. (Surfaced by this plan's authoring; `ao_docs_reconciliation` F5 = "cross-epic
      dispatch-code ownership seam fuzzy".)

### Phase 5 — process residuals (P2, from ao_fleet_stall)

- [ ] [OPERATOR] P2. Monitor/main-agent guard — don't extrapolate one gate to "fleet deadlocked"; re-check
      `/api/backlog/{id}/blockers` before declaring a stall.
- [ ] [OPERATOR] P2. Operating guidance — mixing a high-priority Opus plan with Sonnet plans in one queue is a
      known-degraded shape; R2 reduces but does not eliminate it. Capture the guidance once R2 lands.

## Out of scope (named successors — nothing goes dark)

- **R3/R4** (`ao_dispatch_residuals`) — prompt/heuristic guidance, not grep-able code claims; disposition recorded in
  Phase 4 rather than fixed here.
- **R7** — narrower code gap; fold into Phase 4's close-out decision.
- **Recovery-audit Layer-1 producer rewire** — operator ruling B, DEFERRED behind this plan.
  `issues/ao_recovery_audit_layer1_deleted_2026_07_15.md`.
- **`ao_operator_message_silent_drop`'s P2 nudge idempotency** — adjacent (tmux nudge), separate mechanism; left in its
  own doc.

## Codex SSOTs

- `codex/04-architecture/agent-orchestrator-autospawn.md` — autospawn/spawn-budget contract (Phase 4 updates it).
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — single-VM + role-based dispatch.
- `codex/04-architecture/agent-orchestrator-overview.md` — runtime overview.
- `codex/06-coding-standards/quality-gates.md` — the ship gate.

## Progress Log

- **2026-07-16** — Plan created from the AO open-issue audit (10 parallel verification agents). All four residuals
  re-verified against current HEAD before authoring (anchors above); `rg slot_skip server/autospawn.py` → 0 hits
  confirms R1's skip-blindness firsthand. Operator chose: one human plan, all four in one pass. Home =
  `orchestrator_master` (matches all 3 archived dispatch-family plans + 3 of 4 source issue docs).
