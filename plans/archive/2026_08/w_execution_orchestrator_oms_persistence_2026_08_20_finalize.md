---
doc_type: plan
title: ExecutionOrchestrator OMS-persistence design — finalize
summary: >-
  Gated finalize for w_execution_orchestrator_oms_persistence_2026_08_20 — confirm the design is genuinely
  complete and followable (not a partial decision dressed up as done), reconcile evidence back to the epic,
  the T4 plan, and w_state_recovery_real_wiring_2026_08_20's own Close-out section, archive once done.
status: complete # archived 2026-08-21 — every todo done; parent design plan closed
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution, oms, order-state, persistence, finalize]
related:
  [
    /plans/active/w_execution_orchestrator_oms_persistence_2026_08_20.md,
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: [w_execution_orchestrator_oms_persistence_2026_08_20]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
sequential: true
source: Mandatory companion finalize per task_template.md's AO-plan rule (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/w_execution_orchestrator_oms_persistence_2026_08_20.md,
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# ExecutionOrchestrator OMS-persistence design — finalize

## Todos

- [x] 1. ✅ [AGENT] P0. **Re-verified the design is genuinely complete and followable.** All 10 parent-plan
      todos closed 2026-08-21 with symbol-level citations: exact call chain
      (`ExecutionOrchestrator._submit_single_child_order`/`_submit_algo_follow_orders`/`cancel_order`/
      `amend_order` → `OrderAdapterMatchingEngine` → `OrderAdapter`), exact hook points inside
      `OrderAdapter.submit_order`/`cancel_order`/`amend_order`, a concrete Postgres schema (`oms_orders` table
      + 3 indexes) mapped 1:1 onto `PostgreSQLOrderPersistence`'s 6 currently-`NotImplementedError` methods, a
      named new interface method (`update_order_quantity_price`) for the amend gap, and an explicit fail-open
      exception contract for the hot-path write. A follow-up implementer does not need to ask a single design
      question — confirmed by authoring the follow-up plan (todo 3 below) entirely from the parent's Progress
      Log without any new judgment call.
- [x] 2. ✅ [AGENT] P0. Evidence reconciled: epic (`/plans/epics/system_readiness_master.md`, new 2026-08-21
      Progress Log entry under W11/W20) and `/plans/active/w_state_recovery_real_wiring_2026_08_20.md`'s
      Close-out section (scoped edit, points to both the closed design and the new implementation plan) both
      updated `unified-trading-pm` this session. `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`'s
      "Build state recovery" todo is already `[x]` closed and already points at `w_state_recovery_real_wiring_
      2026_08_20` (verified read-only) — NOT edited: that file was explicitly on this dispatch's
      collision-avoidance list (two other concurrent sub-agents touching different sections of it same
      session); its own `related:` frontmatter does not cite this design plan's path (verified via corpus-wide
      grep), so no archival-referrer fix is owed there either.
- [x] 3. ✅ [AGENT] P1. Follow-up implementation plan confirmed authored + correctly scoped against the FINAL
      decisions (not an earlier draft — it was authored in the same session immediately after the parent
      closed, copying the final Progress Log verbatim):
      `/plans/active/w_execution_orchestrator_oms_persistence_impl_2026_08_21.md` (15 todos, `assigned_vm:
      planning`, `depends_on`+`gate_on_depends` on the parent) + mandatory finalize companion
      `..._impl_2026_08_21_finalize.md`.
- [x] 4. ✅ [AGENT] P1. **6-step archival ritual run 2026-08-21**: (1) no deferred items — the one adjacent
      finding (mislabeled `getattr(instruction, "exchange", ...)` in `engine/orchestrator.py`) is a tracked P3
      todo in the new implementation plan, not left as prose; (2) archived-banner added to both this plan and
      the parent (see below); (3)+(4) codex-alignment done —
      `/codex/04-architecture/cross-domain-state-fabric.md`'s `OrderRecoveryEngine` note updated with the
      concrete plan pointer; (5) corpus-wide grep for both plans' paths found only this session's OWN two new
      docs (`w_execution_orchestrator_oms_persistence_impl_2026_08_21.md`/`_finalize.md`) citing the parent in
      `related:` frontmatter — both repointed at the codex doc instead, per the rule (every other referrer
      found was prose/Progress-Log, not structural `related:`, so no further fix owed); (6) both plans moved to
      `plans/archive/2026_08/` in the same commit as this entry.
