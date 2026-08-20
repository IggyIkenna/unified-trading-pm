---
doc_type: plan
title: W22 messaging/external-API — finalize
summary: >-
  Gated finalize for w22_strategy_execution_messaging_external_api_2026_08_20 — reconcile evidence back to the
  epic and T4 plan, re-check the delta-proxy issue doc's dependency on the features-service subscription todo,
  archive once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution, messaging, w22, finalize]
related:
  [
    /plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
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
depends_on: [w22_strategy_execution_messaging_external_api_2026_08_20]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
sequential: true
source: Mandatory companion finalize per task_template.md's AO-plan rule (operator ruling 2026-07-24).
context_scope:
  [
    /plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md,
    /plans/epics/system_readiness_master.md,
  ]
---

# W22 messaging/external-API — finalize

## Todos

- [ ] [AGENT] P0. Reconcile every completed todo's evidence in
      `w22_strategy_execution_messaging_external_api_2026_08_20.md` back to its true source docs — flip the
      corresponding `## W22` items in `/plans/epics/system_readiness_master.md` to `[x]` with a pointer to this
      plan's own evidence (re-verify each cited commit sha exists and is an ancestor of `origin/live-defi-rollout`
      before trusting the source plan's own copy of the evidence line).
- [ ] [AGENT] P0. Re-check the features-service-subscription todo's landing against
      `/plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md` — if the underlying-tick
      loop it names as missing is now real, cross-link both docs and spin any still-open delta-proxy todo that was
      gated on it into a newly-tracked, now-unblocked todo.
- [ ] [AGENT] P0. Update `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md`'s own W22/external-
      instruction-API todos to point at this plan (now the real dispatch surface) rather than carrying duplicate
      detail — a pointer + landed-sha citation, not a second copy.
- [ ] [AGENT] P0. Run the standard 6-step archival ritual on
      `w22_strategy_execution_messaging_external_api_2026_08_20.md` once every one of its own todos is `[x]` or
      correctly re-scoped, including the corpus-wide referrer-path fixup.
