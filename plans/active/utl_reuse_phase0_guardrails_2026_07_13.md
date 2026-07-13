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
- [x] ✅ [VERIFY] P0. Snapshot pre-change behaviour: for strategy risk + ml registry + features builders, capture a
      golden-output fixture (one client risk eval, one inference-date model selection, one `resolve_build_order` per
      family) so each merge is provably behaviour-preserving, not just compiling. — strategy-service@ffa363e,
      ml-service@3f18fa0, features-service@35d6b3a5. Found + fixed in passing: onchain's `resolve_build_order()` leaked
      cross-family calculators via the shared UTL registry (issue:
      `onchain_builder_registry_cross_family_pollution_2026_07_13.md`); ml-service `quality-gates.sh` was RED on
      pre-existing pip-audit CVEs (pillow/cryptography/pydantic-settings fixed, starlette honestly ignore-vuln'd pending
      a `fastapi` ceiling bump — issue: `ml_service_pip_audit_red_pillow_cryptography_starlette_2026_07_13.md`).
- [x] ✅ [SPEC] P0. Confirm UTL/UAC are the SSOT targets for every extension in Phases 1/3/4 and that no parallel
      old+new path is left behind (CLAUDE.md "delete deprecated code"). — CONFIRMED, verified against live code
      (2026-07-13, slot 7):
  - **Phase 1** (strategy-service): UTL `risk.rule_evaluator`/`risk_preflight`/`family_aggregator` exist as claimed;
    `preflight.py:226 _run_legacy_portfolio_gates` and `risk_calculator.py:account_equity_proxy` confirmed at the cited
    locations. UTL is the correct SSOT target for the comparison/aggregation layer; the 3 local computation engines are
    correctly NOT migrated (different layer, verified-reality note is accurate). Gap found + fixed in-plan: Todo 3's
    deletion of the superseded `RiskLimits`-config comparison path was implicit — made explicit.
  - **Phase 3** (ml-service): UTL `ModelRegistry` exists; writegate/manifest/allowlist controls genuinely absent from
    UTL (matches "carry in" scope, not already done); local manifest-match bug (`... or training_period == ""` at
    `model_registry.py:531,646`) confirmed real — UTL's `== training_period` is correct, migration fixes it. Explicit
    "delete local registry" instruction present — no parallel old+new. Stale finding fixed in-plan: the "delete dead
    `ModelMetadata` TypedDict" todo target was already deleted by `ml-service@00855f6` — struck with citation.
  - **Phase 4** (features-service): UTL `BuilderEntry`/`resolve_build_order`/`transformations.boxcox_transform` all
    confirmed exported. The "already-shipped calendar/delta_one pattern" claim verified accurate — both already import
    `BuilderEntry` from UTL and delegate `resolve_build_order()` to UTL's canonical implementation (thin local wrapper,
    not a duplicate); mt/volatility/onchain/sports/cross_instrument still carry local `class BuilderEntry` as claimed
    (correctly identified as unmigrated). Bucket mis-marked `# CORRECT-LOCAL` at `volatility/io/writer.py:35` confirmed
    real. Explicit deletion instructions present for every genuine-duplicate migration target; items kept local (sports
    dataclass, most of `delta_one/base.py`) are documented with a no-UTL-equivalent rationale, not left as deprecated
    duplicates.
  - **Net**: no parallel old+new path is planned across Phases 1/3/4 for genuine duplicates; two small drift items found
    and corrected directly in the downstream plans (adjacent-scope fix per CLAUDE.md findings triage) rather than filed
    as a separate issue doc.

## Downstream gate

Phases 1, 3, and 4 (`utl_reuse_phase1_strategy_risk_hwm_2026_07_13`, `utl_reuse_phase3_ml_model_registry_2026_07_13`,
`utl_reuse_phase4_features_builder_registry_2026_07_13`) each declare
`depends_on: [utl_reuse_phase0_guardrails_2026_07_13]`

- `gate_on_depends: true` — they're ingested now but machine-held until this plan's last todo is done.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
- Paste `SUB_AGENT_MANDATORY_RULES.md` for any sub-agent fan-out within this plan.
