---
doc_type: plan
title: ExecutionOrchestrator OMS-persistence design — finalize
summary: >-
  Gated finalize for w_execution_orchestrator_oms_persistence_2026_08_20 — confirm the design is genuinely
  complete and followable (not a partial decision dressed up as done), reconcile evidence back to the epic,
  the T4 plan, and w_state_recovery_real_wiring_2026_08_20's own Close-out section, archive once done.
status: active
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

- [ ] [AGENT] P0. **Re-verify the design is genuinely complete and followable** — don't trust the parent
      plan's own "done" claim: read its final write contract / persistence-backend / latency-tradeoff /
      `submitted_orders`-interaction decisions and confirm a follow-up implementer could start coding from
      them without needing to ask a design question the parent plan should have already resolved. This is the
      single highest-value check for this finalize.
- [ ] [AGENT] P0. Reconcile every completed todo's evidence back to the epic's state-recovery / order-lifecycle
      bullet (`/plans/epics/system_readiness_master.md`), to
      `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`'s own "Build state recovery" todo,
      and to `/plans/active/w_state_recovery_real_wiring_2026_08_20.md`'s Close-out section (its
      "wire ExecutionOrchestrator" todo should point here, not carry duplicate detail) — all three should
      point here as the real design surface.
- [ ] [AGENT] P1. Confirm the follow-up IMPLEMENTATION plan this design's own Close-out section calls for was
      actually authored and correctly scoped against the final decisions (not against an earlier draft of
      them) before this plan archives.
- [ ] [AGENT] P1. Run the archival ritual once every parent-plan todo is done and unlocked: confirm zero open
      items (or explicit `BLOCKED-*` tags on the remainder), move both this plan and the parent to
      `plans/archive/2026_08/`, and update any doc that still points at the active path.
