---
doc_type: plan
title: ExecutionOrchestrator OMS-persistence implementation — finalize
summary: >-
  Gated finalize for w_execution_orchestrator_oms_persistence_impl_2026_08_21 -- confirm the implementation
  genuinely closes the gap the design plan named (an order submitted via ExecutionOrchestrator is durably
  persisted and visible to OrderRecoveryEngine's OrderBook on the same running OMS instance), reconcile
  evidence back to the design plan, the epic, the T4 plan, and w_state_recovery_real_wiring_2026_08_20's own
  Close-out section, archive once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution, oms, order-state, persistence, finalize, implementation]
related:
  [
    /plans/active/w_execution_orchestrator_oms_persistence_impl_2026_08_21.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
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
depends_on: [w_execution_orchestrator_oms_persistence_impl_2026_08_21]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
sequential: true
source: Mandatory companion finalize per task_template.md's AO-plan rule (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/w_execution_orchestrator_oms_persistence_impl_2026_08_21.md,
    /plans/archive/2026_08/w_execution_orchestrator_oms_persistence_2026_08_20.md,
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# ExecutionOrchestrator OMS-persistence implementation — finalize

## Todos

- [ ] [REVIEW] P0. **Re-verify the implementation actually closes the gap, not just that tests pass** — read
      `_run_live_async`'s startup wiring and confirm, live-in-code, that the SAME `UnifiedOrderManager`
      instance backs both `_create_startup_order_recovery`'s `OrderBook` and every venue's `OrderAdapter`; do
      not trust the parent plan's own "done" claim without reading the actual diff. This is the single
      highest-value check for this finalize.
- [ ] [REVIEW] P0. Reconcile every completed todo's evidence back to
      `w_execution_orchestrator_oms_persistence_2026_08_20`'s own Close-out section, the epic's state-recovery
      / order-lifecycle bullet (`/plans/epics/system_readiness_master.md`), and
      `w_state_recovery_real_wiring_2026_08_20`'s Close-out section's still-open "run real recovery against
      every wired venue" `BLOCKED-OPERATOR`/`BLOCKED-CREDENTIALS` todo — confirm whether landing this
      implementation clears the `BLOCKED-OPERATOR` half of that gate (it should: `OrderBook` is no longer
      structurally guaranteed empty once this implementation plan lands) while the `BLOCKED-CREDENTIALS` half
      remains genuinely gated on real venue credentials, unaffected by this plan.
- [ ] [REVIEW] P1. Confirm `quality-gates.sh` is green on the final landed state and every cited
      `execution-service@<sha>` resolves to a real, merged commit (re-verify via `git log`, do not trust the
      plan doc's own copy of the sha).
- [ ] [DOC] P1. Run the standard 6-step archival ritual once every parent-plan todo is genuinely `- [x]` and
      `locked_by` is unset — per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. Move
      both this plan and the parent to `plans/archive/2026_08/`, and update any doc that still points at the
      active path.

## Progress Log

> Append-only.
