---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 0 guardrails (banner + golden fixtures)
summary:
  Pre-work gate for the still-unstarted strategy-risk / ml-registry / features-builder compose phases — cross-plan
  banner + golden-output fixtures so those merges are provably behaviour-preserving.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service, ml-service, features-service]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, guardrails, split]
related:
  [
    plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md,
    plans/active/utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md,
    plans/active/utl_reuse_phase3_ml_model_registry_2026_07_13.md,
    plans/active/utl_reuse_phase4_features_builder_registry_2026_07_13.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on:
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend-engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 0 guardrails

> **Split provenance (2026-07-13):** this is Phase 0 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md),
> carved out per operator-approved split so AO can dispatch it directly (the tracker itself is no longer AO-ingestible —
> `execution_scope: local-only` — it stays the reference SSOT for the full severity ledger + phase DAG +
> verified-reality writeups). **Scope note:** Phases 2 (auth dedup), 5 (cloud-SDK-direct), 6 (venue-err/health/retry),
> and 9 (service-dep violations) already shipped real code without this gate — that precedent stands for what's already
> landed. This plan's golden-fixture item is scoped to what the tracker originally targeted and what genuinely remains
> unstarted: strategy risk-eval (Phase 1's core compose work is still 100% open), ml-service ModelRegistry (Phase 3,
> fully unstarted), and features-service builder_registry (Phase 4, fully unstarted).

## What this is

Guardrails before the strategy/ml/features compose-and-extend work starts: a cross-plan banner so concurrent slots don't
re-touch the same risk/auth/registry surfaces, and a golden-output fixture per surface so each merge is provably
behaviour-preserving, not just compiling.

## Todos

- [x] ✅ [AUDIT] P0. Add the cross-plan banner `> **🟡 IN-FLIGHT REFACTOR — UTL/UAC reuse consolidation**` to the 5 epic
      plans previously in the tracker's `related_plans` (`infrastructure_master`, `strategy_master`,
      `features_and_ml_master`, `execution_master`, `orchestrator_master`), so concurrent slots don't re-touch the same
      risk/auth/registry surfaces. — unified-trading-pm (this commit)
- [ ] [VERIFY] P0. Snapshot pre-change behaviour: for strategy risk + ml registry + features builders, capture a
      golden-output fixture (one client risk eval, one inference-date model selection, one `resolve_build_order` per
      family) so each merge is provably behaviour-preserving, not just compiling.
- [ ] [SPEC] P0. Confirm UTL/UAC are the SSOT targets for every extension in Phases 1/3/4 and that no parallel old+new
      path is left behind (CLAUDE.md "delete deprecated code").

## Downstream gate

Phases 1, 3, and 4 (`utl_reuse_phase1_strategy_risk_hwm_2026_07_13`, `utl_reuse_phase3_ml_model_registry_2026_07_13`,
`utl_reuse_phase4_features_builder_registry_2026_07_13`) each declare
`depends_on: [utl_reuse_phase0_guardrails_2026_07_13]`

- `gate_on_depends: true` — they're ingested now but machine-held until this plan's last todo is done.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
- Paste `SUB_AGENT_MANDATORY_RULES.md` for any sub-agent fan-out within this plan.
