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
last_updated: 2026-06-11
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Strategy Master (L2)

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

- [`codex/09-strategy/architecture-v2/`](../../codex/09-strategy/architecture-v2/) — strategy v2 SSOT (53 archetypes
  - 7 axes + 11 cross-cutting + 2 architecture docs)
- [`codex/04-architecture/shadow-deployment-pattern.md`](../../codex/04-architecture/shadow-deployment-pattern.md) —
  shadow window contract for archetype builds
- [`codex/11-project-management/epic-execution-with-sub-agents.md`](../../codex/11-project-management/epic-execution-with-sub-agents.md)
  — epic-flow SSOT (pointer to [`README.md`](README.md))

## Composition with other epics

- **Upstream**: `mtds_mdps_master` (raw market data) + `features_and_ml_master` (features + ML inference) +
  `instruments_master` (universe SSOT) + `manifest_master` (data completeness gate)
- **Downstream**: `execution_master` (handlers + transfers) + `trading_agent_master` (closed-loop allocator directives)
- **Operator surfaces**: `dart_and_promote_master` (DART UI + promote workflow consumes strategy maturity phases)
- **Cross-cutting**: `client_isolation_and_governance_master` (per-client isolation + share-class registry +
  jurisdiction restrictions affect strategy emit)

## Assigned active plans

_8 active plans declare `parent_epic: strategy_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

> **🟡 STALE INDEX (annotated 2026-07-12)** — (was: "8 active plans", unchanged since the script last ran 2026-05-21). A
> `parent_epic: strategy_master` frontmatter grep on 2026-07-12 returns **9** files, of which the following declare
> `parent_epic: strategy_master` but are NOT reflected anywhere in the P0/P1/P2 sections below:
> `capability_wizard_and_manifest_2026_06_11` (created 2026-06-11),
> `carry_staked_basis_funding_scan_experiment_2026_06_16` (2026-06-16), `v2_engine_venue_buildout_2026_06_15`
> (2026-06-15), `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17` (2026-06-17) — all real active
> plans with open P1-P3 todos. (The remaining 5 of the 9 frontmatter hits are `active/issues/*` docs, not P0-P3
> dispatchable plans.) Separately, of the 8 plans that ARE itemized below, 4 (`strategy_archetype_taxonomy_2026_05_12`,
> `strategy_repo_consolidation_2026_05_19`, `config_grid_archetype_extend_2026_05_20`,
> `defi_recursive_borrow_archetypes_post_cutover_2026_06_01`) are already ✅ ARCHIVED — the "8 active" headline
> undercounts new plans and overcounts archived ones simultaneously. Durable fix is re-running
> `scripts/plans/populate_epic_bodies_2026_05_21.py`; not run as part of this doc-reconciliation pass (out of the
> named-files edit scope). [Doc-reconciliation 2026-07-12, findings 288/298/335, same pass as the Scope § note above.]

## P0 — must complete before next foundation gate

### [`workspace_qg_sweep_2026_05_23`](../archive/2026_05/workspace_qg_sweep_2026_05_23.md) — strategy-service cluster

**status**: 🟠 ACTIVE — QG sweep for strategy-service (11 ruff errors). [vm: vm-trading-core]

> **🟢 LOGIC FREEZE LIFTED 2026-07-12** (operator ruling, plan-reconciliation Q&A findings 286/292 — see
> `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2). Full logic changes to
> `engine/strategies/v2/`, `engine/allocator/`, collateral, liquidation, cross-venue transfer are permitted again under
> normal QG/ship discipline. Historical freeze text: (was: "🟠 ACTIVE — QG sweep for strategy-service (11 ruff errors,
> SURFACE ONLY — LOGIC FREEZE in effect). Only ruff/pyright surface fixes. No changes to `engine/strategies/v2/`,
> `engine/allocator/`, collateral, liquidation, cross-venue transfer. Resume full logic fixes after 🟢 STRATEGY-LOGIC
> UNFREEZE ping lands."). Retroactively ratified under this ruling: funding_dispersion.py (strategy-service@6b285fad) +
> the USDC-collateral down-size branch (strategy-service@6e9164b1). Previously freeze-gated items (e.g.
> capability-wizard F27) are dispatchable.

### [`defi_recursive_borrow_archetypes_2026_05_10`](../active/defi_recursive_borrow_archetypes_2026_05_10.md)

**status**: active · **estimate**: 42.3 cal AI-days (class: design)

### [`strategy_archetype_taxonomy_2026_05_12`](../archive/2026_05/strategy_archetype_taxonomy_2026_05_12.md)

**status**: ✅ ARCHIVED 2026-05-21 — 100% complete (0 open todos); taxonomy + share-class neutrality + recursive carry
rename shipped

### [`strategy_repo_consolidation_2026_05_19`](../archive/2026_05/strategy_repo_consolidation_2026_05_19.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases 1-11 done (3-repo merge + all cleanup); P2 StrategyDirectiveReloader
DEFERRED-POST-CUTOVER · **estimate**: 12 cal AI-days (class: infra)

## P1 — important; post-current-gate

### AUDIT-03 operator-decision dispatch (slot 7, 2026-06-01 — from `archive/issues/audit03_ikenna_review_routing_2026_05_22.md`)

- [ ] [CODE] P1. **F-14 — 1h price-move abort is a SAFETY GAP (NOT equivalent to vol_cap_clamp).** Slot-7 investigation
      (2026-06-01) confirmed: codex `codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md:129`
      specs `max_underlying_move_pct: 3.0 # abort/skip if realized move > X% in 1h window` (a circuit-breaker that HALTS
      trading on a sudden 1h directional move). The implemented `apply_vol_cap_clamp()`
      (`strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/funding_rate_dispersion.py:286-333` +
      `price_dispersion.py:420-480`) only CLAMPS leverage when realized-vol > 80% OR vol-zscore > 2.0 — it does NOT
      abort on a 1h directional price move (different trigger, different action). Implement a separate guard in
      strategy-service that aborts (returns 0 instructions) when |1h realized price move| > threshold. Repo:
      strategy-service.
- [ ] [DOCS] P1. **F-13 / F-15 — reconcile codex strategy-spec → implemented mechanism (code is truth).** Route the
      actual codex doc edit to `codex_vs_repo_docs_ssot_audit_2026_06_01.md` (do not edit codex from strategy work);
      this todo tracks the strategy-side reconciliation decision. Repo: codex (via codex_vs_repo_docs owner).
- [ ] [CODE] P1. **F-34 — add `SUPPORTED_ARCHETYPES` allowlist + typed-error guard + fix docstring.** Operator decision
      2026-06-01: the 28 implemented archetype engines are the intended May-23 rollout subset (NOT a regression vs the
      (was: 55-member) `StrategyArchetype` enum — stale as of 2026-06-01; the enum grew to 57 by 2026-06-11 and is
      59-member as of 2026-07-12, see "Scope inherited" § count-drift note above). In `factory.py`, replace the bare
      `KeyError` ("every enum value must have an engine") with a guard that returns a typed "archetype not in rollout"
      error against an explicit `SUPPORTED_ARCHETYPES` allowlist; fix the stale docstring/count against the CURRENT enum
      size at land-time (59 as of 2026-07-12, not "53"→55 — the number keeps moving; prefer citing
      `len(StrategyArchetype)` over a hardcoded literal, per `capability_wizard_analysis_findings_2026_06_11.md` F9
      remedy). Supersedes the per-archetype `ARBITRAGE_CROSS_DOMAIN_EVENT` note in `config_grid_archetype_extend`. Repo:
      strategy-service. **NB**: respect the active strategy-service LOGIC-FREEZE (lifted 2026-07-12 — see banner) — this
      lives in `factory.py`/registry, not `engine/strategies/v2/`; land after confirming the freeze does not cover the
      factory, else hold for the `🟢 STRATEGY-LOGIC UNFREEZE` ping (lifted 2026-07-12 — see banner). **VERIFIED STILL
      OPEN 2026-07-12**: `strategy-service/strategy_service/engine/strategies/v2/factory.py` still raises a bare
      `KeyError` at the "no engine registered" branch (no `SUPPORTED_ARCHETYPES` allowlist in the engine registry) —
      this todo has not been implemented; checkbox correctly remains unflipped. (2026-07-12 doc-reconciliation, same
      pass as the Scope § note above.)

### [`compute_optimization_mock_data_2026_05_13`](../active/compute_optimization_mock_data_2026_05_13.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: design)

### [`config_grid_archetype_extend_2026_05_20`](../archive/2026_05/config_grid_archetype_extend_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 3 items DEFERRED-OPERATOR-DECISION (critical mismatch between plan's proposed
dimension names and actual engine params; no operator response since 2026-05-20). · **estimate**: 2.4 cal AI-days

**Deferred (MIGRATED FROM archived plan)** — post-cutover backlog:

- **Confirm per-archetype grid dimension names (P0, BLOCKED-OPERATOR-DECISION)**: Operator must align dims with actual
  engine params or add proposed params to engines first. `ARBITRAGE_CROSS_DOMAIN_EVENT` needs engine factory entry.
- **Implement grid branches + smoke tests (P0)**: Gate: operator decision above.

## P2 — useful; opportunistic

### [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07`](../active/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)

**status**: active · **estimate**: 12 cal AI-days (class: design)

### [`defi_recursive_borrow_archetypes_post_cutover_2026_06_01`](../archive/2026_05/defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phase 6 (7 items) DEFERRED-SERVICE-REPOS; Phase 13 (3 items) BLOCKED-OPERATOR; all
other phases DEFERRED-SERVICE-REPOS/DEFERRED-POST-CUTOVER per slot 6 sweep. · **estimate**: 24 cal AI-days (class:
brand-new)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

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
