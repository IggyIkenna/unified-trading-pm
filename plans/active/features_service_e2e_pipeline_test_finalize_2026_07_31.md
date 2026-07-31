---
doc_type: plan
title: Finalize — features-service e2e pipeline test (na-eligibility-audit reclassify)
summary: >-
  Gated finalize twin for features_service_e2e_pipeline_test_2026_05_26.md's 2026-07-31 na-eligibility-audit RECLASSIFY
  (NA -> planning, partial: 3 of 4 Open Track-1 todos). Reconciles the 3 dispatched todos' evidence and runs the 6-step
  archival ritual once the source plan is genuinely done (its own remaining `[OPERATOR]` judgment call notwithstanding —
  archive once the 3 dispatched items are done and either the 4th is separately resolved or this plan's scope is
  re-split).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, na-eligibility-audit, finalize, features, plan-hygiene]
related:
  [
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: features_and_ml_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
depends_on: [features_service_e2e_pipeline_test_2026_05_26]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
drift_direction: none
source: >-
  na-eligibility-audit cross-cutting run 2026-07-31 (dispatch agt-845699) — Phase 3 apply, finalize-plan-coverage rule
  (task_template.md § 4).
---

# Finalize — features-service e2e pipeline test

> Gated on `features_service_e2e_pipeline_test_2026_05_26.md`'s 3 reclassified Track-1 todos (Phase A onchain e2e, Phase
> B CeFi MDPS top-up+delta_one re-verify, DEFERRED-fan-out MDPS backfill) all reaching `[x]`. The doc's 4th todo
> (`usdc_idle_yield_apy_bps` stub, `[OPERATOR]`) is independent and does not gate this finalize.

## Todos

- [ ] [REVIEW] P2. Re-verify each of the 3 dispatched Track-1 todos' evidence citation is real (a resolvable commit SHA
      or read-back assertion report, not just a checkmark) before treating the source plan as done.
- [ ] [DOC] P3. Once the 3 dispatched todos are `[x]` — regardless of whether the `[OPERATOR]` `usdc_idle_yield_apy_bps`
      todo has been separately resolved — run the standard 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `features_service_e2e_pipeline_test_2026_05_26.md` if the `[OPERATOR]` todo is ALSO resolved by then; otherwise
      leave the source plan active with only that one item open and note here why archival is deferred. **Done when**:
      either the source doc is archived + every referrer fixed, or this todo records the specific reason it's still open
      (the `[OPERATOR]` item unresolved).
