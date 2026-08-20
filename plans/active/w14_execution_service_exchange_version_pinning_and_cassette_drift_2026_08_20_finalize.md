---
doc_type: plan
title: W14 exchange-version pinning and cassette drift — finalize
summary: >-
  Gated finalize for w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20 — confirm the
  drift-detection mechanism actually runs and reports real state (not just that code exists), reconcile evidence
  back to the epic and T4 plan, archive once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution, cassettes, versioning, w14, finalize]
related:
  [
    /plans/active/w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20.md,
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
depends_on: [w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
sequential: true
source: Mandatory companion finalize per task_template.md's AO-plan rule (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/w14_execution_service_exchange_version_pinning_and_cassette_drift_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# W14 exchange-version pinning and cassette drift — finalize

## Todos

- [ ] [AGENT] P0. **Re-verify the drift check actually runs and reports real state** — don't trust the parent
      plan's own "built" claim; independently invoke the drift-detection mechanism and confirm it produces a real
      per-venue verdict (stale/current), not a stub that always reports green. This is the single highest-value
      check for this finalize, since a drift detector that silently never detects anything is worse than no
      detector (false confidence).
- [ ] [AGENT] P0. Reconcile every completed todo's evidence back to the epic's `## W14` section
      (`/plans/epics/system_readiness_master.md`) and to
      `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`'s own W14 todo — both should point
      here as the real dispatch surface, not carry duplicate detail.
- [ ] [AGENT] P1. Check whether any `BLOCKED-CREDENTIALS` follow-ups the parent plan filed (per-venue stale
      cassettes needing re-record access) are still genuinely blocked, or whether credentials have since become
      available — retag if resolved, per the "the moment an OPERATOR tag resolves, retag in the same edit" rule.
- [ ] [AGENT] P1. Run the archival ritual once every parent-plan todo is done and unlocked: confirm zero open
      items (or explicit `BLOCKED-*` tags on the remainder), move both this plan and the parent to
      `plans/archive/2026_08/`, and update any doc that still points at the active path.
