---
doc_type: epic
title: Strategy Master (L2)
summary: >-
  L2 everlasting epic owning strategy-service post-2026-05-19 consolidation (engine + portfolio_allocator + risk +
  position + pnl + 59 archetype engines (was: 53 — see 2026-07-12 count-drift note in "Scope inherited" below)),
  per-client subprocess isolation, and archetype lifecycle; inherits the strategy side of the split
  strategy_and_dart_master umbrella (v2 factory cutover, shadow deployment registry/ledger, capability gaps,
  cross-domain alpha).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, defi, execution, consolidation, reconciliation, ssot-audit]
related:
  [
    ../active/capability_wizard_and_manifest_2026_06_11.md,
    ../active/compute_optimization_mock_data_2026_05_13.md,
    ../archive/2026_05/config_grid_archetype_extend_2026_05_20.md,
    ../active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md,
    ../active/defi_recursive_borrow_archetypes_2026_05_10.md,
    ../archive/2026_05/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md,
    ../archive/2026_05/strategy_archetype_taxonomy_2026_05_12.md,
    ../archive/2026_05/strategy_execution_contract_remediation_2026_05_20.md,
    ../archive/2026_05/strategy_repo_consolidation_2026_05_19.md,
    ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md,
  ]
created: 2026-05-21
name: strategy_master
tier: L2
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md
  - ../active/carry_staked_basis_funding_scan_experiment_2026_06_16.md
  - ../active/carry_strategy_ensemble_productionization_2026_07_24.md
  - ../active/cefi_satellite_ao_dispatch_batch13_2026_08_09.md
  - ../active/cefi_satellite_ao_dispatch_batch13_2026_08_09_finalize.md
  - ../active/cross_venue_funding_reversion_research_2026_07_24.md
  - ../active/crypto_alpha_research_2026_07_24.md
  - ../active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md
  - ../active/family2_position_registry_unwind_consumption_2026_08_09.md
  - ../active/l2_book_microstructure_capture_2026_07_13.md
  - ../active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md
  - ../active/strategy_service_family2_close_unwind_emission_2026_08_09.md
  - ../active/v2_engine_venue_buildout_2026_06_15.md
last_updated: 2026-06-11
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Strategy Master (L2)

> **🟡 IN-FLIGHT REFACTOR — UTL/UAC reuse consolidation** (guardrails phase:
> [`utl_reuse_phase0_guardrails_2026_07_13`](../archive/2026_07/utl_reuse_phase0_guardrails_2026_07_13.md); compose
> phases: `utl_reuse_phase1_strategy_risk_hwm_2026_07_13` (strategy risk/HWM),
> `utl_reuse_phase3_ml_model_registry_2026_07_13` (ml ModelRegistry),
> `utl_reuse_phase4_features_builder_registry_2026_07_13` (features builder_registry)). Concurrent slots: do not
> re-touch the strategy risk-eval, ml-registry, or features-builder-registry surfaces until those phase plans land —
> check them first.

**Owns**: strategy-service post-consolidation 2026-05-19 (engine + portfolio_allocator + risk + position + pnl + 59
(was: 53) archetype engines); per-client subprocess isolation; archetype lifecycle.

**Assigned VM**: `vm-trading-core` (co-located with `execution_master` + `trading_agent_master`).

## Scope inherited from `strategy_and_dart_master_SUPERSEDED_2026_05_21` (split 2026-05-21)

The pre-2026-05-21 `strategy_and_dart_master` umbrella was split into two everlasting epics. **This epic owns the
strategy side**:

- **Archetype engine v2 finalization** — factory cutover, shadow deployment registry + ledger, 18-archetype shadow
  observation, capability gaps (SOR, hold-policy mixin, transfer-rebalance integration, benchmark-fills, dated-future
  roll, IM/Trading allocator split).
- **Cross-domain alpha + strategy lifecycle visibility** — UAC schemas + UTL SLA engine + DataQualityScorer +
  cross-domain calc + DeFi alpha features + execution cost prediction.
- **59 archetypes** (was: 53) per `codex/09-strategy/architecture-v2/archetypes/` — NOT a fixed constant: the count is a
  live code figure that grew 53→55→57→58→59 between 2026-06-01 and 2026-06-22 as new archetypes landed (verified against
  `unified-api-contracts` `StrategyArchetype` enum on `live-defi-rollout` HEAD as of 2026-07-12 — 59 members, docstring
  self-declares "59 archetypes"; last addition `TSMOM_BTC_CTA` @61ac3ad2 2026-06-22). Only 28 engines are implemented
  for the May-23 rollout subset (F-34 below, operator decision 2026-06-01) — taxonomy-count and implemented-engine-count
  are different numbers, do not conflate. [Doc-reconciliation 2026-07-12, findings 287/290/294/333/295, §A2 B-queue
  ruling — `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`.]
- **Portfolio allocator** + risk_rules + position-balance-monitor + pnl-attribution (consolidated into strategy-service
  2026-05-19).

DART operator UX + promote workflow scope went to [`dart_and_promote_master.md`](dart_and_promote_master.md) (L3). Full
archaeology: [`strategy_and_dart_master_SUPERSEDED_2026_05_21.md`](strategy_and_dart_master_SUPERSEDED_2026_05_21.md).

## Codex SSOTs

- [`codex/09-strategy/architecture-v2/`](../../codex/09-strategy/architecture-v2/) — strategy v2 SSOT (archetype count
  is a live code figure, see the "59 archetypes (was: 53)" note above — 7 axes + 11 cross-cutting + 2 architecture docs;
  corrected 2026-08-10 to drop the stale hardcoded "53" this same section's own remedy warns against restating)
- [`/codex/04-architecture/shadow-deployment-pattern.md`](/codex/04-architecture/shadow-deployment-pattern.md) — shadow
  window contract for archetype builds
- [`/codex/11-project-management/epic-execution-with-sub-agents.md`](/codex/11-project-management/epic-execution-with-sub-agents.md)
  — epic-flow SSOT (pointer to [`README.md`](README.md))

## Composition with other epics

- **Upstream**: `mtds_mdps_master` (raw market data) + `features_and_ml_master` (features + ML inference) +
  `instruments_master` (universe SSOT) + `manifest_master` (data completeness gate)
- **Downstream**: `execution_master` (handlers + transfers) + `trading_agent_master` (closed-loop allocator directives)
- **Operator surfaces**: `dart_and_promote_master` (DART UI + promote workflow consumes strategy maturity phases)
- **Cross-cutting**: `client_isolation_and_governance_master` (per-client isolation + share-class registry +
  jurisdiction restrictions affect strategy emit)

## Assigned active plans

_13 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

_(no plans currently assigned at this priority)_

## P1 — important; post-current-gate

### [`capability_wizard_client_lite_and_ci_regen_followup_2026_07_24`](../active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md)

**status**: active · **estimate**: 1.0 cal AI-days (class: brand-new) **title**: Capability wizard — client-lite
successor + CI-runner openapi regen follow-up

### [`carry_staked_basis_funding_scan_experiment_2026_06_16`](../active/carry_staked_basis_funding_scan_experiment_2026_06_16.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: research) **title**: carry_staked_basis funding-carry scan —
exploratory analysis harness + journal

### [`carry_strategy_ensemble_productionization_2026_07_24`](../active/carry_strategy_ensemble_productionization_2026_07_24.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: research) **title**: carry_staked_basis — ensemble
orchestrator engine + strategy-service productionization

### [`crypto_alpha_research_2026_07_24`](../active/crypto_alpha_research_2026_07_24.md)

**status**: active · **estimate**: 18 cal AI-days (class: research) **title**: Crypto Alpha Research — Book
Construction, Signal Research & Paper-Trading POC

### [`recursive_loop_orchestrator_wiring_finalize_2026_08_09`](../active/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.2 cal AI-days (class: refactor) **title**: Finalize — RecursiveLoopOrchestrator
wiring plan reconciliation + archival

## P2 — useful; opportunistic

### [`cefi_satellite_ao_dispatch_batch13_2026_08_09`](../active/cefi_satellite_ao_dispatch_batch13_2026_08_09.md)

**status**: active · **estimate**: 0.48 cal AI-days (class: infra) **title**: CeFi satellite AO batch 13 — item-level
extraction from 19 non-qualifying NA docs (strategy_master group)

### [`cefi_satellite_ao_dispatch_batch13_2026_08_09_finalize`](../active/cefi_satellite_ao_dispatch_batch13_2026_08_09_finalize.md)

**status**: active · **estimate**: 0.24 cal AI-days (class: infra) **title**: CeFi satellite AO batch 13 — finalize
(reconcile source docs + archive)

### [`cross_venue_funding_reversion_research_2026_07_24`](../active/cross_venue_funding_reversion_research_2026_07_24.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: research) **title**: carry_staked_basis — cross-venue
funding-reversion research (Pass-B reconciliation + deployable book)

### [`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17`](../active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md)

**status**: active · **estimate**: 18.0 cal AI-days (class: brand-new) **title**: Collateral-aware sizing +
opportunity-checker + wizard full-parameterization

### [`l2_book_microstructure_capture_2026_07_13`](../active/l2_book_microstructure_capture_2026_07_13.md)

**status**: active · **estimate**: 5.0 cal AI-days (class: brand-new) **title**: Deeper-Than-L5 Order Book Capture —
populate queue_position_* for MARKET_MAKING_QUEUE_MICROSTRUCTURE

### [`strategy_service_family2_close_unwind_emission_2026_08_09`](../active/strategy_service_family2_close_unwind_emission_2026_08_09.md)

**status**: active · **estimate**: 0.6 cal AI-days (class: design) **title**: Family-2 (CARRY_BASIS_PERP_INV)
close/unwind instruction emission — strategy-service

### [`v2_engine_venue_buildout_2026_06_15`](../active/v2_engine_venue_buildout_2026_06_15.md)

**status**: active · **estimate**: 66.0 cal AI-days (class: research) **title**: v2 Engine + Venue Build-Out — 22
engineless archetypes + 9 unwired venues

## P3 — backlog; revisit quarterly

### [`family2_position_registry_unwind_consumption_2026_08_09`](../active/family2_position_registry_unwind_consumption_2026_08_09.md)

**status**: active · **estimate**: 0.2 cal AI-days (class: refactor) **title**: Family2PositionRegistry — consume the
Family-2 close/unwind event once it exists

## Archived plans

### [`defi_recursive_borrow_archetypes_post_cutover_2026_06_01`](../archive/2026_05/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 4/5/7/8/9/11/12/13 all DEFERRED-SERVICE-REPOS or DEFERRED-POST-CUTOVER (slot
6 sweep). Phase 6 (Hyperliquid LIVE) missed by slot 6, deferred here.

**Deferred (migrated):**

- **Phase 6 — Hyperliquid LIVE perp connector (7 items, DEFERRED-SERVICE-REPOS)**: execution-service work — DELETE
  `venues/hyperliquid.py` + replace simulation logic + NEW `_hyperliquid_signing.py` (EIP-712) + `ApiKeyReloader` + 8 HL
  `VENUE_ERRORS_DEFI` error codes + `hyperliquid_bridge.py` helpers + available-margin placeholder fix.
- **Phase 13 — Live deploy (BLOCKED-OPERATOR)**: Treasury allocation + 7-day live VM + plan archival, all gated on
  operator DeFi live deployment authorization.

### [`strategy_execution_contract_remediation_2026_05_20`](../archive/2026_05/strategy_execution_contract_remediation_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-5+Q done: strategy manifest emission (`record_captured`/`record_failed`),
`resolve_bucket_name(kind="strategy-store")` bucket SSOT, preflight gate via `validate_config_can_run()`, error
classification (`ADAPTER_FETCH_FAILED`), QG ratchet, codex SSOT updated. · **estimate**: 3.0 cal AI-days

**Deferred (MIGRATED FROM archived plan)** — P0 operator-decision:

- **4c. Per-AG → unified bucket migration**: CeFi bucket has 237 files (~19MB) dev backtest data (2025-01-01). All prod
  per-AG buckets are 0-byte. Operator choose: (a) abandon old dev data + delete per-AG buckets, OR (b) write migration
  script (old `strategy_instructions/<id>/<date>.parquet` → new `strategy_instructions/client_id=/.../`).
  BLOCKED-OPERATOR-DECISION. Ping filed slot-6 2026-05-23.
