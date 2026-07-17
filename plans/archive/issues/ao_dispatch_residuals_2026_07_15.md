---
doc_type: issue
title:
  AO dispatch/autospawn residuals — the genuinely-open dispatch items that sit in NO in-flight plan (tracking index +
  suggested owner)
summary: |
  Surfaced by the AO documentation reconciliation (ao_docs_reconciliation_2026_07_15, finding X4). A handful of
  genuinely-open agent-orchestrator dispatch/autospawn defects are real and code-confirmed but are tracked in NO active
  plan — none of the three in-flight dispatch plans (ao_dispatch_correctness / ao_worker_lifecycle / ao_task_lifecycle)
  reference them (grep-verified). Left as-is they fall out of active execution tracking. This doc is a lightweight INDEX
  that collects them, points at each one's canonical source doc + code location, and proposes a single owner
  (`ao_dispatch_correctness_regen_reconcile` — it already owns `dispatch.py` + `autospawn.py` tier logic + the
  `slot_skips` table). It does NOT duplicate the source docs; it makes them collectively visible. Read-only; no code
  changed.
status: resolved # ACKED — R1/R2/R5/R6 shipped, R3/R4 shipped as prompt guards, R7 re-homed (see superseded_by)
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, autospawn, dispatch, slot-skips, orphaned-todos, tracking-index]
related:
  [
    ao_docs_reconciliation_2026_07_15.md,
    ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md,
    ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md,
    ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md,
    dispatcher_role_eligibility_gap_review_slots_2026_07_13.md,
    backlog_regen_drops_handtuned_prereqs_2026_07_12.md,
    ../ao_dispatch_correctness_regen_reconcile_2026_07_07.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: orchestrator_master
priority: P1
source:
  - ao_docs_reconciliation_2026_07_15 Wave-1 (dispatch/spawn issue cluster), code-verified
assigned_vm: NA
execution_scope: local-only
resolved_by:
  - "R1 — agent-orchestrator@7baeedc (eligibility-aware budget) + @bf9a61b (_FILTERS scope table) + @6c778e6 (candidate
    set gated on slot_is_spawnable) + @f8ace1f (slot_has_claimable_task). Proven on the LIVE rate, not on tests: pre-fix
    15:00-17:00 = 87 spawns / 0 dispatches; post-fix 19:00-21:00 = 31 spawns / 37 dispatches."
  - "R2 — agent-orchestrator@6ae43b5 (_spawn_param_plan, per-slot tier/role; _top_queued_task_params DELETED)"
  - "R3/R4 — unified-trading-pm@5a79c4c23 (agents/main.md STEP 2.4/2.6 + monitor.md prompt guards)"
  - "R5 — agent-orchestrator@860eaf7 (liveness-aware high-affinity spill, 600s threshold)"
  - "R6 — agent-orchestrator@962e676 (review_slot SLOT-scope filter; deliberately NOT the slot_role fix this index's
    source doc recommended — that variant would have broken worker dispatch fleet-wide)"
  - "R7 — dangerous half fixed at agent-orchestrator@4695db6 (TaskRow.brief_hash + reset-on-mismatch); surviving half
    re-homed to regen_positional_task_ids_not_content_stable_2026_07_17 (see superseded_by)"
locked_by:
locked_since:
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
supersedes:
superseded_by: regen_positional_task_ids_not_content_stable_2026_07_17.md # R7's surviving half ONLY; R1-R6 are shipped
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
---

> **✅ ACKED 2026-07-17 — this index did its job; every residual now has a home. Archived.**
> [`ao_dispatch_hardening_2026_07_16`](../../active/ao_dispatch_hardening_2026_07_16.md) absorbed and SHIPPED R1, R2,
> R5, R6 (code) and R3, R4 (prompt guards) — and R1 was closed on the **live dispatch rate**, not on a green suite. R7's
> dangerous half was already fixed at `agent-orchestrator@4695db6`; its **surviving half is re-homed to
> [`regen_positional_task_ids_not_content_stable_2026_07_17`](regen_positional_task_ids_not_content_stable_2026_07_17.md)**,
> which also corrects R7's wording below (see that doc — the one-line framing in the table is imprecise). Per-residual
> SHAs are in `resolved_by`.
>
> **Why the re-home rather than archiving R7 with the rest**: this index was the ONLY doc carrying R7, and its own
> suggested owner (`ao_dispatch_correctness_regen_reconcile_2026_07_07`) is itself archived. Archiving with a live
> residual and no `superseded_by` is exactly what
> [`ao_autospawn_role_blind_dispatch_starvation_2026_07_14`](ao_autospawn_role_blind_dispatch_starvation_2026_07_14.md)
> did on 2026-07-14 — its banner records that it orphaned two live bugs for two days until a later plan rediscovered
> them. Not repeating that.

> **Historical — the index as filed 2026-07-15.** Tracking index, not a duplicate. Each residual has a canonical source
> doc; this collects the orphans so they're visible to active execution. Suggested resolution: fold these into
> `ao_dispatch_correctness_regen_reconcile` as todos (it owns the code), OR execute as one small batch. Nothing here is
> fixed yet; all read-only-verified.

## The residuals (all code-confirmed open; none tracked in an in-flight plan)

| #   | residual                                                                                                                                                                                                                           | canonical source                                                           | code location                                                               | priority |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------- | -------- |
| R1  | **Skip-blind spawn budget** — `_queued_undispatched_count`/`_has_queued_work` count a task the whole eligible fleet has skipped within TTL as spawnable → respawn churn, account-pool burn (triple-corroborated)                   | [[ao_skip_blind_spawn_budget_phantom_churn_2026_07_15]] (canonical)        | `server/autospawn.py:340` (budget) vs `server/dispatch.py:74` (skip filter) | **P1**   |
| R2  | **Mixed-tier spawn** — a mixed-tier queue spawns the whole tick at the top task's tier (`_top_queued_task_params` "Known limitation")                                                                                              | ao_fleet_stall todo #4                                                     | `server/autospawn.py:415`                                                   | P2       |
| R3  | **Monitor/main over-generalization** — extrapolating one task's gate to "whole fleet deadlocked" → passive                                                                                                                         | ao_fleet_stall todo                                                        | main/monitor prompts                                                        | P2       |
| R4  | **Opus/Sonnet plan-mixing guidance** — a single high-pri Opus plan drags every spawn to Opus                                                                                                                                       | ao_fleet_stall todo                                                        | operating guidance                                                          | P3       |
| R5  | **High-affinity task pinned to a DEAD slot never spills** — `_task_is_routable_to` returns False for every non-target slot with no dead-target fallback (worked around manually 2026-07-14, not code-fixed)                        | ao_autospawn_role_blind open bullet                                        | `server/dispatch.py` `_task_is_routable_to`                                 | P2       |
| R6  | **Non-worker (review/main) slots unfiltered** — review/main slots never set `slot_role` (they don't traverse `render_worker()`), so `pick_next_task`'s role gate is a no-op for them → a review slot can be assigned a worker task | [[dispatcher_role_eligibility_gap_review_slots_2026_07_13]] (own open doc) | `server/prompts.py:176/195`, `server/dispatch.py:97`                        | P2       |
| R7  | **Task-ID instability across regen** — a checked-off `[x]` todo can be re-derived under a fresh task id and re-dispatched (spun out of backlog_regen's Addendum)                                                                   | backlog_regen Addendum                                                     | `server/regen_backlog_from_plan.py` (id derivation)                         | P2       |

## Suggested action

1. **R1** stays canonically tracked in `ao_skip_blind…2026_07_15` (fullest evidence); this index just links it. It also
   **supersedes** the "Skip-exhaustion churn" open bullet inside
   `ao_autospawn_role_blind_dispatch_starvation_2026_07_14` — annotate that bullet
   `superseded-by → ao_skip_blind…2026_07_15`.
2. R2-R7: add as `- [ ]` todos under `ao_dispatch_correctness_regen_reconcile` (the code owner) in one pass, or keep
   this index as their home if the operator prefers not to expand that plan.

## Progress Log

- **2026-07-15** — Filed from the AO doc reconciliation (X4) as a tracking home for 7 code-confirmed orphaned
  dispatch/autospawn residuals. No code changed; each links to its canonical source + code location.
