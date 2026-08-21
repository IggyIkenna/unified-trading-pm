---
doc_type: plan
title: State recovery real wiring — finalize
summary: >-
  Gated finalize for w_state_recovery_real_wiring_2026_08_20 — independently re-verify recovery actually
  reconciles real state (not a stub dressed up as real), reconcile evidence back to the epic and T4 plan,
  archive once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution, state-recovery, order-recovery, finalize]
related:
  [
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
depends_on: [w_state_recovery_real_wiring_2026_08_20]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
sequential: true
source: Mandatory companion finalize per task_template.md's AO-plan rule (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/w_state_recovery_real_wiring_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# State recovery real wiring — finalize

## Todos

- [ ] [AGENT] P0. **Independently re-verify recovery reconciles REAL state, not stub-shaped state dressed up as
      real.** Don't trust the parent plan's own "done" claim: construct `OrderRecoveryEngine` with its real
      `OrderBook`/`_VenueAdapter` yourself, and confirm `fetch_open_orders()` genuinely calls a live/credentialed
      adapter method (not a hardcoded empty list still masquerading as "real"). This is the single highest-value
      check for this finalize — the whole point of the parent plan was closing exactly this gap.
- [ ] [AGENT] P0. Reconcile every completed todo's evidence back to the epic's state-recovery section
      (`/plans/epics/system_readiness_master.md`) and to
      `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`'s own "Build state recovery" todo —
      both should point here as the real dispatch surface, not carry duplicate detail.
- [ ] [AGENT] P1. Check whether any `BLOCKED-CREDENTIALS` venues the parent plan filed are still genuinely
      blocked, or whether credentials have since become available — retag if resolved.
- [ ] [AGENT] P1. Run the archival ritual once every parent-plan todo is done and unlocked: confirm zero open
      items (or explicit `BLOCKED-*` tags on the remainder), move both this plan and the parent to
      `plans/archive/2026_08/`, and update any doc that still points at the active path.
