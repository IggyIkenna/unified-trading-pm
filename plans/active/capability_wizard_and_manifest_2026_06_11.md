---
title:
  "Capability wizard + manifest — strategy/venue/instrument/execution/risk capability SSOT, strategy prospectus
  generator, walkthrough wizard UI"
parent_epic: strategy_master
assigned_vm: vm-trading-core
priority: P1
status: active
execution_scope: local-only # design sign-off pending — flip to orchestrator-agent per-phase once operator approves scope
estimate_class: brand-new
estimate_baseline_ai_days: 24.0
estimate_calibrated_ai_days: 24.0
created: 2026-06-11
source:
  - operator direction 2026-06-11 (capability-wizard discussion — ikenna + harsh; session covered availability Q&A,
    walkthrough chaining, collateral/fees/sim-assumption gaps, prospectus generation, two-sided codex audit)
related_plans:
  - plans/epics/strategy_master.md
  - plans/epics/deployment_and_user_management_master.md
  - plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md
  - plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md
locked_by: live-defi-rollout
locked_since: 2026-06-11
---

# Capability wizard + manifest

## Scope

A **capability manifest** (machine-generated SSOT of everything the system can do, edge-by-edge) + a **strategy
prospectus generator** (script that renders a per-configured-strategy document: mechanics, decision logic, exposures,
fund-flow mermaid, risk scenarios, circuit breakers, backtest Sharpe/drawdown) + a **walkthrough wizard UI**
(progressive configuration where every dropdown IS the availability answer). Codex SSOT for the concept:
[`codex/09-strategy/architecture-v2/capability-wizard.md`](../../codex/09-strategy/architecture-v2/capability-wizard.md).

**Four use cases (operator-stated 2026-06-11):**

1. **Visibility** — internal lens into strategy capabilities from instruments/venues/actual data availability through
   risk/margining/execution to fund flows and configurable decision-making per archetype.
2. **End-to-end parameterization** — drive the whole system from a stated execution preference; expose whether we are
   flexible enough, and surface questions the wizard cannot answer (each one = system expansion candidate).
3. **Two-sided audit** — verify what the wizard _thinks_ is possible is _actually_ possible in code; classify dead ends
   as **logical** (options-on-sports — fine) vs **unbuilt** (missing adapter/registry — gap). Orphan + dead-end-path
   detection across all registries.
4. **Client-lite wizard** — eventual client-facing configurator (successor of the public strategy questionnaire in
   `unified-trading-system-ui/app/(public)/questionnaire/`), ending in a config + credentials checklist + on-demand
   backtest ("here is what I need from you: these API keys; want a 5-year backtest of your configured preference?").

**Architecture decisions (operator-confirmed this session):**

- The manifest exporter is a **new generator in the existing PM openapi family**
  (`unified-trading-pm/scripts/openapi/`), reusing its deterministic-output/CI-drift/UI-delivery pipeline. The suite
  must be **repaired first** (Phase 0) — it has CRITICAL drift (phantom pre-consolidation services, architecture_v2
  never extracted; see pre-audit below).
- **Static capability vs runtime data availability stay separate**: the manifest answers "does the code support it";
  runtime "is the data actually there" questions delegate to deployment-api `/api/data-status/*` (drilldown, schema,
  shard-info). The wizard composes both (e.g. min-history-to-run check). Do NOT rebuild the data-status drilldown.
- **Escalation order: script → test → agent.** Every unanswerable question is logged as a typed gap (`missing_registry`
  | `missing_extraction` | `needs_code_scan`); only `needs_code_scan` goes to agent-orchestrator, and agent answers are
  written back into the manifest as annotations (credits spent once). Gaps tracked in
  [`issues/capability_wizard_gap_discovery_2026_06_11.md`](issues/capability_wizard_gap_discovery_2026_06_11.md).
- **UI placement**: wizard = new route group in `unified-trading-system-ui` (DNS/auth/deploy/Firestore already solved;
  self-contained route group keeps iteration context small). Capability matrix = tab in `deployment-ui` next to the
  existing Data Status tab (same ops audience).
- **Prospectus gives away full alpha for now** (debugging mode); curtailment is a later config flag.

## Pre-audit manifest (audited 2026-06-11, this session)

Generator-suite drift (blast radius for Phase 0 — all in `unified-trading-pm/scripts/openapi/`):

| Component                                                                     | Finding                                                                                                                                                                                                                                                                                                   | Severity |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `generate_unified_spec.py:48-78` SERVICE_REGISTRY                             | 10+ phantom services (8× `features-*-service`, `ml-inference/-training`, `pnl-attribution`, `position-balance-monitor`, `risk-and-exposure`) consolidated away; missing `features-service`, `ml-service`, `fund-administration-service`, `greeks-service`                                                 | CRITICAL |
| `generate_ui_reference_data.py`                                               | architecture_v2 NEVER extracted: `StrategyArchetype` (53), `StrategyFamily` (9), `ARCHETYPE_CAPABILITY_REGISTRY`, `AtomicExecutionMode`, `VenueCategoryV2`, `MarginMode`, `KillSwitchReason`, `VenueFeature`, `RiskGateLayer/Decision`, etc. — extraction only walks package-root exports, not submodules | HIGH     |
| `generate_config_registry.py:38-123`                                          | same phantom/missing service configs                                                                                                                                                                                                                                                                      | HIGH     |
| Outputs (`unified-api-contracts/openapi/*.json`)                              | stale May 22–Jun 1; `_validate_service_coverage()` warns but does not FAIL                                                                                                                                                                                                                                | MEDIUM   |
| Source-mode capability matrix (`source-mode-capability-matrix_2026-06-07.md`) | documented manually, not generator-extracted                                                                                                                                                                                                                                                              | HIGH     |

Key code anchors: `unified_api_contracts/internal/architecture_v2/{enums,archetype_capability}.py` ·
`unified_api_contracts/internal/domain/strategy_service/registry.py` (STRATEGY_REGISTRY) ·
`execution_service/algorithms/registry.py` + `utils/instruction_type.py` + `trade_execution/order_types.py` ·
`features_service/delta_one/app/features/registry.py` (~1,382 specs / 34 groups, `features-status` CLI) ·
`ml_service/training/ml/model_registry.py` · `fund_administration_service/allocation/capital_router.py` ·
`unified_trading_library/performance_metrics.py` · `strategy_service/engine/backtest/runner.py` ·
`codex/09-strategy/architecture-v2/archetypes/` (59 files) ·
`codex/04-architecture/wallet-hierarchy-and-capital-flow.md`.

## Dependency DAG

```mermaid
graph LR
  P0[Phase 0 repair generators] --> P1[Phase 1 capability manifest v1]
  P1 --> P2[Phase 2 gap registries in UAC]
  P1 --> P3[Phase 3 prospectus generator]
  P2 --> P3
  P1 --> P4[Phase 4 wizard UI + matrix tab]
  P2 --> P4
  P3 --> P4
  P4 --> P5[Phase 5 agent escalation + backtest-on-demand]
  P2 -. parallel with .-> P3
```

Phase 2 and Phase 3 run PARALLEL after Phase 1 (prospectus consumes gap-registry stubs as `not_registered` until
backfilled). Phase 4 UI work is PARALLEL across the two repos.

## Phase 0 — repair the generator truth layer (`unified-trading-pm/scripts/openapi/`)

- [x] ✅ [IMPLEMENT] P0. SERVICE_REGISTRY: remove phantom pre-consolidation services; add `features-service`,
      `ml-service`, `fund-administration-service`, `greeks-service`; same sweep for CONFIG_REGISTRY in
      `generate_config_registry.py`. DONE 2026-06-11 — unified-trading-pm@50bdbcd36 (PR #268). Removed 13 phantom
      services; added fund-administration-service + greeks-service with verified config class names; instruments-service
      path fixed to `config.service_config`; market-tick-data-service path fixed to `market_interface.config`.
      features-service + ml-service: no root config.py exists (per-family only) — documented in registry comment.
- [x] ✅ [IMPLEMENT] P0. Auto-discover services from `workspace-manifest.json` instead of hardcoded lists;
      `_validate_service_coverage()` FAILS the run on disk-vs-registry mismatch (today it only warns). DONE 2026-06-11 —
      unified-trading-pm@50bdbcd36. Added `_load_service_registry(workspace_root)` + `_OVERRIDE_MODULE_PATHS` +
      `_NO_API_REPOS`; `_validate_service_coverage()` now calls `sys.exit(1)` on mismatch.
- [x] ✅ [IMPLEMENT] P0. Extend `extract_uic_enums()` to recursively walk `unified_api_contracts.internal` submodules
      (`architecture_v2.*`) so all 53-archetype/9-family enums + ARCHETYPE_CAPABILITY_REGISTRY land in
      `ui-reference-data.json`. DONE 2026-06-11 — unified-trading-pm@50bdbcd36. Added architecture_v2 submodule walk +
      `extract_architecture_v2_capability_registry()`. Verified output: StrategyArchetype 57 values (count grew from
      audited 53 — 4 new archetypes landed), StrategyFamily 9 values, ARCHETYPE_CAPABILITY_REGISTRY 22 archetypes / 98
      cells, total UIC enums 227 (up from single-digits).
- [ ] [SCRIPT] P1. Fresh full run of `generate-unified-openapi.sh`; commit regenerated outputs; verify
      `check_openapi_drift.py` quality gate is green and actually fires on synthetic drift. **PARTIAL 2026-06-11
      (capability-exporter, slot-4):** UAC-importable outputs regenerated + committed — `ui-reference-data.json`
      (byte-identical to committed = already current post-Phase-0), `capability-manifest.json` (new,
      unified-api-contracts@1bc2f07). **STILL BLOCKED ON-HOST:** `config-registry.json` +
      `unified-trading-system.openapi.json` need every service importable in ONE interpreter (`.venv-workspace`), which
      is ABSENT on this host — `generate_config_registry.py` extracts 0/32 and would EMPTY the registry if committed
      (restored via `git checkout`; finding F12). The per-service `.venv`s exist (the capability exporter uses them via
      subprocess), but the aggregate spec generator does not yet do per-service-venv extraction. Full run must happen on
      the laptop / CI runner with `.venv-workspace`; the `uic-openapi-sync` CI regenerates TS types on its runner
      regardless.
- [x] ✅ [VERIFY] P0. Drift CI gate: `_validate_service_coverage()` now exits nonzero on mismatch (fail-on-drift
      implemented in-run). DONE 2026-06-11 — unified-trading-pm@50bdbcd36. Scheduled workflow is a Phase 1 item
      (deferred — fail-on-run counts as the enforcement gate for now).

## Phase 1 — capability manifest exporter v1 (`generate_capability_manifest.py`)

- [x] ✅ [SPEC] P0. `CapabilityManifest` pydantic schema in unified-api-contracts: nodes (archetype, family, venue,
      chain, instrument_type, algo, feature_group, model, data_source, fund_structure, wallet, broker) + typed edges
      with status `available | partial | not_available | not_registered` + gap type
      `missing_registry | missing_extraction | needs_code_scan | logical_dead_end` + `agent_annotation` field for
      written-back agent answers. DONE 2026-06-11 — unified-api-contracts@6f31f59 (capability_manifest.py: 14 node
      kinds, deterministic to_canonical_dict(), 40 unit tests green, QG exit 0).
- [x] ✅ [IMPLEMENT] P0. Extract: STRATEGY*REGISTRY + ARCHETYPE_CAPABILITY_REGISTRY (archetype × venue_category ×
      instrument_type), venue/instrument universe (ENDPOINT_REGISTRY incl. per-venue access_mode/auth requirements +
      VENUE_CATEGORY_MAP/INSTRUMENT_TYPES_BY_VENUE/DEFI_VENUE_TO_PROTOCOL/CHAIN_RPC_TEMPLATES), execution algos
      (per-service venv), feature groups (34, per-group lookback), ML model registry, KillSwitchReason + RiskGateLayer,
      data sources + transports, gap registries (collateral/fees/sim/fund/order/agent + treasury split). DONE 2026-06-11
      — unified-trading-pm@78b2e893a (generate_capability_manifest.py + \_capability*{extract,gaps,orphan}.py) →
      unified-api-contracts@1bc2f07 (capability-manifest.json: 409 nodes, 663 edges). NOTE: instruments-service
      `InstrumentRecord` / sports-leagues-from-snapshot / deployments-topology NOT yet wired (venue/instrument universe
      comes from UAC registries, which is sufficient for v1); those are v2 enrichments. instruction-types/order-type/TIF
      enums surface via the order_semantics gap-registry node (honest-empty until backfill).
- [x] ✅ [IMPLEMENT] P1. Source-mode matrix extraction: batch is emitted `available` per source; live/replay per source
      emit typed `missing_registry` gap edges (the matrix lives in the manual
      `source-mode-capability-matrix_2026-06-07.md` audit, NOT a UAC registry — per task direction, gap rather than
      parse the markdown). Transport edges use `default_transport_for_source`. DONE 2026-06-11 —
      unified-trading-pm@78b2e893a (\_capability_extract.py extract_data_sources). The matrix→UAC-registry codification
      is the gap-close follow-up (tracked in gap-discovery doc 2026-06-11 entry).
- [x] ✅ [IMPLEMENT] P1. Derived edges: **min-data-to-run** — feature-lookback component IS derived (max feature-group
      bar `period`, from features-service); the ML training-window factor is a runtime config with NO static registry
      constant, so the full `feature_lookback × training_window` edge is emitted `partial` + typed `missing_extraction`
      (honest typed-gap state per task direction). DONE 2026-06-11 — unified-trading-pm@78b2e893a
      (\_capability_gaps.py).
- [x] ✅ [IMPLEMENT] P1. Orphan + dead-end report: orphan nodes (no edges) + unbuilt dead-ends (registry-available
      archetype/instrument with no supporting venue) vs logical dead-ends (registry-blocked combos). Folded into the
      manifest gaps summary AND a human-readable `capability-orphan-report.txt` beside the existing `orphan-report.txt`.
      DONE 2026-06-11 — unified-trading-pm@78b2e893a (\_capability_orphan.py) → unified-api-contracts@1bc2f07 (124
      orphans, 25 unbuilt, 16 logical).
- [x] ✅ [VERIFY] P1. Determinism: generator runs twice → byte-identical capability-manifest.json + orphan report
      (verified). `generated_from_commit` = UAC HEAD sha via git (no timestamps). Wired into
      `generate-unified-openapi.sh` after the audits + into the UI-sync block. DONE 2026-06-11 —
      unified-trading-pm@78b2e893a. **NOTE (F14): the uic-openapi-sync workflow ships TS types ONLY, NOT registry
      JSONs** — capability-manifest.json reaches `unified-trading-system-ui/lib/registry/` via the
      generate-unified-openapi.sh sync block, not that workflow. The "ships via uic-openapi-sync" framing is inaccurate;
      UNticked sub-claim re-homed to the generator sync block (see F14 + Progress Log).

## Phase 2 — gap registries in unified-api-contracts (schema first = forcing function; PARALLEL items)

- [x] ✅ [SPEC] P0. **Collateral registry** schema. DONE 2026-06-11 — unified-api-contracts@6f31f59
      (collateral_registry.py: CollateralPolicy/AssetHaircut/BrokerEntry/TreasurySplitPolicy; TREASURY_SPLIT_POLICIES
      seeded — DeFi 20/80, CeFi 0/100, Sports no-split, sourced from wallet-hierarchy codex; COLLATERAL_REGISTRY +
      BROKER_REGISTRY honest-empty — per-venue haircuts/LTVs are a backfill, numbers never invented).
- [x] ✅ [SPEC] P1. **Fees registry** schema. DONE 2026-06-11 — unified-api-contracts@6f31f59 (fees_registry.py:
      FeeComponent/FeeUnit/FeeSchedule; FEES_REGISTRY honest-empty — backfill).
- [x] ✅ [SPEC] P1. **Simulation-assumptions registry** schema. DONE 2026-06-11 — unified-api-contracts@6f31f59
      (simulation_assumptions.py: MatchingModel mapped to existing BenchmarkFillMode; SIM_ASSUMPTIONS_REGISTRY
      honest-empty — needs_code_scan of backtest runner, see finding F11).
- [x] ✅ [SPEC] P1. **Fund-structure manifest** schema. DONE 2026-06-11 — unified-api-contracts@6f31f59
      (fund_structures.py: FundStructureKind/CadenceKind/FundStructureOffering, reuses existing ShareClass enum;
      OFFERED_FUND_STRUCTURES honest-empty).
- [x] ✅ [SPEC] P1. **Order-semantics-per-venue-adapter declarations** schema. DONE 2026-06-11 —
      unified-api-contracts@6f31f59 (order_semantics.py: canonical TimeInForce (none pre-existed in UAC — F10),
      RefPricingMode fixed|delta_adjusted_to_underlying, MultiLegDeltaOwner, VenueOrderSemantics with auth_wired;
      VENUE_ORDER_SEMANTICS honest-empty — per-adapter honor matrix is a code-scan backfill).
- [x] ✅ [SPEC] P2. **Trading-agent/LLM capability declarations** schema. DONE 2026-06-11 —
      unified-api-contracts@6f31f59 (trading_agent_capability.py; TRADING_AGENT_CAPABILITIES honest-empty).
- [ ] [IMPLEMENT] P2. **Registry backfills** (split from the schema todos above, which shipped honest-empty): per-venue
      collateral/haircut/LTV/maintenance-margin entries, fee tiers, per-adapter order-semantics honor matrices, sim
      assumptions from backtest-runner scan, offerable fund structures — each backfill PR cites its source of truth;
      `needs_code_scan` items route through Phase 5 agent escalation. **COLLATERAL DONE 2026-06-12 —
      unified-api-contracts@f997f3b**: COLLATERAL_REGISTRY backfilled for the MVP venue universe (7 perp + 2 lending, 9
      policies / 53 asset rows) sourced IN-REPO-FIRST from `venue_collateral.py` (haircuts + accept/reject) +
      `defi_reserve_params.py` (Aave per-asset LTV/liq-threshold) + `cefi_margin_tiers.py` (tier-1 MMR) +
      execution-service `lst_collateral_resolver.py` (Kamino LST haircut), cross-checked against official venue docs
      (Hyperliquid USDC-only, Deribit stETH 7.5% eff. 2026-01-13, Aave dashboard, Kamino risk dashboard) — every numeric
      cites its `source_of_truth`/`source_note`; Kamino per-asset LTV honestly None (live-dashboard-only). Schema
      extended ADDITIVELY: `VenueCollateralKind`, per-asset `max_ltv`/`liquidation_threshold`/`liquidation_bonus` +
      `accepted` flag on `AssetHaircut`, `venue_kind`/`collateral_notes` on `CollateralPolicy`,
      `STAKING_VENUES_NO_COLLATERAL_POLICY` (staking venues take no margin/LTV policy — documented). 23 backfill tests +
      stale `==[]` test corrected. Findings F27 (strategy-service lowercase `perp_venue` ≠ uppercase
      `VENUE_COLLATERAL_MATRIX` keys → carry blocked) + F28 (in-repo collateral SSOTs disagree: `venue_collateral.py` vs
      `lst_collateral_resolver.py` haircuts). **STILL OPEN: fees / order-semantics / sim / fund-structure backfills.**
- [x] ✅ [IMPLEMENT] P1. Manifest exporter consumes each new registry as it lands; until then emits honest
      `not_registered` edges (never silently omits the dimension). DONE 2026-06-12 — exporter now emits per-venue
      collateral nodes + per-asset `accepts_collateral` edges carrying the sourced haircut/LTV metadata
      (unified-trading-pm@5b5f2fe80, `_capability_gaps.py`); regenerated manifest (unified-api-contracts@cc269c2):
      `gap_registry:collateral` edge flipped `not_registered`→**`available`** ("9 entries registered"), 9 collateral
      venue nodes + 53 accepts_collateral edges (39 accepted / 14 documented-rejected). Deterministic (byte-identical on
      two runs). Other registries still emit `not_registered` until their backfills land.

## Phase 2.6 — leg-level restriction model (operator-caught F22, 2026-06-11 third message)

Multi-leg archetypes (staked basis = stake + lend + perp hedge) must be modeled structurally: per-leg role, instrument
types, asset groups, venue eligibility, and conditional constraints (LST accepted as perp collateral on venue V → staked
variant; else straight basis within the archetype). Restrictions exhaustive — never prose in `notes`.

- [x] ✅ [SPEC] P0. `ArchetypeLegSpec` in UAC architecture_v2: leg_id, role StrEnum (stake, lend, hedge_short,
      spot_long, perp_long, lp, …), required bool, instrument_types, asset_groups, venue eligibility,
      conditional_constraints (typed: e.g. requires_collateral_acceptance(lst, perp_venue) with fallback_variant
      "straight_basis"), per-leg signal variants. Extends/wraps ARCHETYPE_CAPABILITY_REGISTRY without breaking existing
      consumers. **uac@c17a6be** — `archetype_leg_spec.py` (888L): `ArchetypeLegRole` (11 closed roles),
      `LegConstraintKind` (3 kinds incl. `requires_collateral_acceptance`), `LegConstraint` (params +
      `fallback_variant` + description), `ArchetypeLegSpec` (reuses `ArchetypeInstrumentType`/`VenueCategoryV2`),
      `ArchetypeLegStructure` (reuses `AtomicExecutionMode`), `ARCHETYPE_LEG_STRUCTURES` registry. Decimal-not-float,
      basedpyright-strict, additive exports via `architecture_v2/__init__.py` (matching the `capability_manifest`
      sibling pattern; `internal/__init__` untouched). Dual-representation documented in the module docstring (leg-truth
      SSOT alongside the flat cell registry; F4 cells NOT rewritten). 9 unit tests green.
- [x] ✅ [IMPLEMENT] P0. Seed leg specs for the carry family (CARRY*STAKED_BASIS + CARRY_BASIS_PERP/DATED variants +
      CARRY_RECURSIVE*\*) and ARBITRAGE_PRICE_DISPERSION, sourced from engine code structure + codex archetype docs +
      existing cells' notes/venue lists (cite source per leg). All other archetypes emit honest `not_registered` leg
      specs + one gap edge each (exhaustive backfill = tracked follow-up tranche). **uac@c17a6be** — 11 archetypes
      seeded (CARRY_STAKED_BASIS spot+stake+lend+hedge_short w/ `requires_collateral_acceptance(lst,hedge_venue)` →
      `straight_basis` fallback + CeFi binance/bybit/deribit/okx + DeFi hyperliquid/gmx_v2/drift hedge venues;
      CARRY_STAKED_BASIS_DATED; CARRY_BASIS_PERP/\_INV; CARRY_BASIS_DATED/\_INV; CARRY_RECURSIVE_STAKED;
      CARRY_RECURSIVE_BORROW_LENDING_ONLY; YIELD_STAKING_SIMPLE; YIELD_ROTATION_LENDING; ARBITRAGE_PRICE_DISPERSION).
      Every leg cites engine path + codex doc + manifest cell. 46 archetypes WITHOUT leg structures honestly enumerated
      by `archetypes_without_leg_structures()` (test asserts the gap set is explicit, not silent).
- [x] ✅ [IMPLEMENT] P1. Exporter emits leg nodes/edges (archetype→leg→instrument_type/venue with role + conditional
      metadata); two-sided audit extended: archetype cells whose notes mention legs ("ATOMIC", "hedge", "+") but have no
      leg spec = flagged drift. **pm@8a0fdd1 + uac outputs (manifest generated_from_commit=c17a6be)** —
      `CapabilityNodeKind.LEG` added; `extract_leg_structures()` emits 25 leg nodes + `has_leg` (role/required
      metadata) + `trades_instrument` + `supports` (per-leg venue) + `leg_constraint:<kind>|<params>|fallback_variant=…`
      edges; 46 archetypes w/o leg specs → one `not_registered` `has_leg:legs` gap edge each. Two-sided audit (d)
      legs-in-prose drift heuristic flags 6 archetypes (EVENT_DRIVEN, LIQUIDATION_CAPTURE, MARKET_MAKING_CONTINUOUS,
      RULES_DIRECTIONAL_EVENT_SETTLED, STAT_ARB_CROSS_SECTIONAL, VOL_TRADING_OPTIONS). Prospectus "Leg Structure" table
      per archetype (honest gap line where absent). Manifest 409→435 nodes / 663→902 edges. Deterministic (twice
      byte-identical).
- [x] ✅ [AGENT][UI] P1. Wizard Instruments/Venues stages become leg-aware: mandatory legs pre-selected and
      non-deselectable, instrument types grouped by leg role with the conditional surfaced ("on venues where the LST is
      not accepted as perp collateral, this archetype runs straight basis"), cross-category legs break the
      single-category assumption from Stage A (show + auto-include the hedge leg's category). pw:L2 gate. — ui@85f27c46
      | pw:L2 ✓ (13/13 smoke tests green) | regression: tests/smoke/wizard.spec.ts

## Phase 3 — strategy prospectus generator (script first, UI later; PARALLEL with Phase 2)

- [x] ✅ [IMPLEMENT] P0. `generate_strategy_prospectus.py`: input = strategy config + capability manifest → markdown:
      what the strategy does, decision logic (FULL alpha disclosure — debugging mode; curtailment flag later),
      position-by-scenario table ("in this scenario the strategy will be positioned…"), expected
      returns/Sharpe/max-drawdown (from `performance_metrics.py` over backtest output), written as if presenting to the
      internal allocation team / a potential investor. PM@(see PR#272) + UAC@fe37eae — 57 archetype prospectus docs in
      `openapi/prospectus/`, 7 sections each, deterministic (byte-identical on two runs). 57/57 archetypes have codex
      docs.
- [x] ✅ [IMPLEMENT] P1. Exposure section: per-leg exposures and normalization — staked-ETH vs ETH equivalence,
      base-currency-neutral views; pull from greeks-service / ledger exposure models where available, else emit
      `not_registered` gap. Shipped: Section 3 "Exposures & Normalization" renders codex risk/PnL content + honest gap
      line for staked-vs-spot equivalence (F-class finding, cites gap tracker). UAC@fe37eae.
- [x] ✅ [IMPLEMENT] P1. **Fund-flow mermaid**: venues/wallets as boxes (treasury vs trading/hot per
      `wallet-hierarchy-and-capital-flow.md` + `capital_router.py` AllocationTargets), deposit→conversion→venue paths
      (e.g. deposit ETH → receive stETH → post to CeFi venue → short perp), cross-balance movement arrows. Shipped:
      Section 4 "Fund Flow" — `build_fund_flow_mermaid()` in `_prospectus_manifest.py`; staked-basis archetypes include
      deposit→STAKING→LST→CEFI_VENUE→PERP_SHORT legs; TREASURY_SPLIT_POLICIES seeded from UAC collateral_registry.py
      (DeFi 20/80, CeFi 0/100, Sports 0/100). UAC@fe37eae.
- [x] ✅ [IMPLEMENT] P1. Risk section: applicable KillSwitchReason set + RiskGateLayer placement for the configured
      archetype/venues, configurable circuit-breaker parameters, liquidation monitoring surface. Shipped: Section 5
      "Risk & Circuit Breakers" — full KillSwitchReason enum + RiskGateLayer placement + codex config-schema parameter
      extraction. UAC@fe37eae.
- [x] ✅ [AUDIT] P1. **Two-sided audit**: diff generated prospectus vs the hand-written codex archetype doc
      (`codex/09-strategy/architecture-v2/archetypes/<archetype>.md`) for all 57 archetypes; discrepancy report feeds
      the gap tracker (wizard-thinks vs codex-says vs code-does). Shipped: `audit_prospectus_vs_codex.py` →
      `openapi/prospectus/prospectus-codex-audit.md` (deterministic). Results: (a) 0 enum-without-doc, (b) 2 orphan
      docs, (c) 1 venue-category contradiction (F15 filed). PM@(see PR#272) + UAC@fe37eae.
- [x] ✅ [VERIFY] P2. Pin a regression test per fixed discrepancy (operator rule: as issues are found, build tests
      around them). Shipped: `tests/unit/test_prospectus_generators.py` — 19 tests (16 unit + 3 integration):
      determinism x2, audit 57-archetype count, codex doc count, all 7 sections present, honesty labels, fund-flow
      mermaid structure. PM@(see PR#272).

## Phase 3.5 — interactive scenario stepper (operator direction 2026-06-11, second session message)

After the wizard produces a config, the user can **step through the strategy like a paper run without real data**: the
stepper drives the REAL strategy engine loop (batch=live HARD RULE — never a parallel engine) with a
**SyntheticMarketState** the user steers — key numbers fed by hand (funding rate, prices, quotes, feature values) or
seeded-random fillers — and mock fills via the existing BenchmarkFillMode. Each step reports: instructions emitted,
fills, positions, PnL delta, **which triggers/predicates evaluated and how they resolved** (entry, exit, stop loss,
rebalance, each KillSwitchReason), and **distance-to-trigger** for every armed threshold ("DAILY_LOSS_BREACH arms at
−5%, you are at −1.2%"). This is decision-tree auditing: walking the archetype's code-path branches by steering inputs,
viable TODAY (pre-backfill/pre-migration), upgrading to the Phase 5 real-data backtest when data lands. Per-archetype,
post-config (combinatorial explosion is avoided because the wizard fixed the config first).

- [x] ✅ [SPEC] P1. Stepper contract in UAC architecture_v2. DONE 2026-06-11 — unified-api-contracts@6262c3f
      (scenario_step.py: StepInput/TriggerEvaluation/RiskGateDecisionRecord/StepFill/StepReport/ScenarioConfigRef/
      ScenarioSession/TriggerKind; reuses StrategyInstructionEnvelope + RiskGateLayer/Decision/KillSwitchReason/
      BenchmarkFillMode — no duplicates; 12 unit tests; QG green).
- [x] ✅ [IMPLEMENT] P1. `e2e-testing/scripts/strategy/scenario_stepper.py`. DONE 2026-06-11 — e2e-testing@3e41ecb
      (scenario_stepper.py + \_stepper_engine.py; --steps JSON + --interactive REPL; drives real V2BatchHarness.on_tick
      credential-free; introspection_gap reported for runtime-fired kill/stop predicates per LOGIC FREEZE) +
      strategy-service@e0ed11c (peripheral QG wiring, surface-only, replicates scripts/defi block).
- [x] ✅ [IMPLEMENT] P1. Trigger map + distance-to-trigger. DONE 2026-06-11 — e2e-testing@3e41ecb
      (build_trigger_evaluations: entry/exit/rebalance from config thresholds + emitted events; signed
      distance_to_trigger; kill_switch/stop_loss honest introspection_gap until post-unfreeze engine tracing).
- [x] ✅ [AGENT][UI] P2. Wizard "Step through it" stage after config: feed key numbers, render StepReports as a timeline
      (trades/positions/PnL/triggers). pw:L2 gate. — unified-trading-system-ui@9f087aa8 | pw:L2 ✓ (12/12 smoke) |
      regression: tests/smoke/wizard-stepper.spec.ts + tests/smoke/wizard.spec.ts + tests/unit/wizard/stepper.test.ts.
      SessionViewer: CLI handoff (copy-to-clipboard), paste/file-drop JSON, "Load example" fixture, timeline per step
      (instructions collapsed JSON, fills, PnL delta/cumulative, trigger-eval bars, risk-gate decisions per layer,
      kill-switch banner + post-kill suppression). Help-panel markdown fix: bold+lists render correctly.
- [x] ✅ [VERIFY] P1. Stepper smoke per MVP archetype. DONE 2026-06-11 — e2e-testing@3e41ecb
      (test_scenario_stepper_smoke.py 3/3; apd_price_dispersion_btc.json 6-step: ATOMIC entries @50/70bps → +250/+350
      PnL, forced DAILY_LOSS_BREACH @step4 → killed+REJECTED, post-kill above-threshold emits NOTHING;
      csb_staked_basis_eth.json 5-step entry/exit/rebalance/kill coherent. carry_staked_basis entry-EMISSION blocked
      on-host by empty perp collateral registry — the Phase 2 collateral gap made concrete, not a stepper bug).

## Phase 4 — wizard UI + capability matrix tab (PARALLEL across repos)

- [x] ✅ [AGENT][UI] P1. `unified-trading-system-ui`: new self-contained route group `app/(wizard)/` + `lib/wizard/` —
      manifest-driven progressive walkthrough (stages A–J subset: category→family→archetype→instruments→venues→
      sources→execution→risk→capital→review), greyed-not-hidden unavailable options with status+gap_type chips, side
      help per stage. — unified-trading-system-ui@9f40331 | pw:L2 ✓ (8/8 smoke) | regression:
      tests/smoke/wizard.spec.ts + tests/unit/wizard/graph.test.ts (41 tests). Route: /wizard.
- [x] ✅ [AGENT][UI] P1. Wizard output: strategy configuration artifact (download + localStorage) + onboarding checklist
      from selected venues' auth metadata + "Step through it" stub panel (stepper UI = Phase 3.5 leftover). —
      unified-trading-system-ui@9f40331 | pw:L2 ✓ | regression: tests/smoke/wizard.spec.ts.
- [x] [AGENT][UI] P1. `deployment-ui`: **Capability tab** next to Data Status — full matrix view (archetype × venue ×
      instrument × mode × algo), orphan/dead-end report, batch-live symmetry view; leaf data-availability questions call
      existing `/api/data-status/*` (drilldown/schema/shard-info) — no rebuild. pw:L2 gate. — deployment-ui@13ac831 |
      pw:L2 ✓ (6/6 tests pass) | regression: tests/smoke/capability_tab.spec.ts + tests/unit/capability-helpers.test.ts
      (22 tests)
- [x] ✅ [IMPLEMENT] P2. Wizard "isolation mode": flat "Ask one thing" queries (strategies/venues/algos/sources tables
      with filters) alongside the walkthrough — same manifest accessors. — unified-trading-system-ui@9f40331 | pw:L2 ✓ |
      regression: tests/smoke/wizard.spec.ts.

## Phase 5 — agent escalation + backtest-on-demand

- [x] ✅ [IMPLEMENT] P1. `needs_code_scan` gap → agent-orchestrator task (existing planning-VM workflow); agent answer
      written back as manifest `agent_annotation` so the question is never paid for twice. Strict gating: agents only
      when script/registry cannot answer (operator rule). DONE 2026-06-11 — PM@f84a119 (capability-annotations.yaml
      sidecar + \_capability_annotations.py + generate_capability_manifest.py merge step; emit_capability_gap_todos.py
      escalation emitter; 2 gap edges annotated + 1 P2 todo emitted; 0 annotation orphans).
- [x] ✅ [IMPLEMENT] P2. Backtest-on-demand: wizard config → `strategy_service/engine/backtest/runner.py` over last N
      years → metrics into the prospectus ("want to see a 5-year backtest of your configured preference?"). Depends on
      data-availability precheck via deployment-api. DONE 2026-06-11 — e2e-testing@194d66b
      (backtest_from_wizard_config.py; GroupBRunner wired; honest data precheck; PRECHECK_UNAVAILABLE{cloud data
      unavailable on this host} verdict confirmed on apd_price_dispersion_btc.json).
- [ ] [DEFERRED] P3. Client-lite wizard mode (use case 4) — named successor plan once internal wizard is hardened.

## Phase 6 — exhaustive combinatorics, parity gates, data-availability wiring (operator direction 2026-06-12)

Operator: restrictions must exist for EVERY combination (archetype × venue × instrument × instruction × execution algo),
impossible combinations must be BLOCKED with a reason, the UI must provably follow the same rules as the codebase, and
the parity must be a QUALITY GATE so it cannot regress. Plus: the wizard must show whether the data the config needs
actually exists (which data_types missing, over which timeframes) via the existing deployment-api data-status endpoints.

### 6A — registry truth to full coverage

- [x] ✅ [IMPLEMENT] P0. Leg-spec backfill: ALL 57 archetypes get ArchetypeLegStructure entries (sourced per leg from
      engine code + codex archetype docs; where genuinely underivable, an explicit not_registered leg structure with a
      reason — enumerated, never absent). unified-api-contracts. DONE 2026-06-12 — **unified-api-contracts@180fb56**.
      `ARCHETYPE_LEG_STRUCTURES` now enumerates all **57/57** archetypes: **51 real leg structures** (engined +
      doc/cell-derived: carry/yield 10 + arbitrage/MEV/liquidation 6 + DeFi-LP 3 + directional/ML/rules 5 +
      market-making 8 + stat-arb 2 + vol-trading 17) + **6 explicit `not_registered`** (ARBITRAGE_MEV_SANDWICH
      theoretical-only tracer; 4 PORTFOLIO\_\* meta-allocation overlays with no instrument legs; VOL_0DTE_PIN_RISK
      risk-management overlay) — each with `legs=()` + a cited `not_registered_reason` (validator enforces the
      invariant; registry build asserts all 57 keys present). Seeds split into `archetype_leg_spec_seeds.py` (900-line
      cap; allowlisted as a declarative seed registry); schema extended additively
      (`not_registered`/`not_registered_reason` fields). Per leg cites engine path + codex doc + manifest cell. Tests:
      57-key completeness, not_registered explicitness + partition, per-family role sanity,
      validator-rejects-bad-invariant (12 tests). basedpyright clean, QG green.
- [x] ✅ [SPEC] P0. **Archetype→execution-algo compatibility registry** in UAC architecture_v2: which algos
      (SOR/sor_twap/swap_twap/atomic_bundle/selector) are valid per (instruction type × venue kind × leg coupling),
      sourced from execution-service algorithms/selector code + codex; honest gaps typed. Today NOTHING declares this —
      the wizard cannot block what no registry states (operator-caught). DONE 2026-06-12 —
      **unified-api-contracts@180fb56** (`algo_compatibility.py`). Transcribes the execution-service selector
      DECLARATIVELY (file:line cited): `ALGORITHMS_BY_INSTRUCTION_TYPE` + `DEFAULT_ALGORITHM` + `select_algorithm`
      4-step chain (selector.py:25-167) + venue→InstructionType classification (instruction_type.py:69-112) — NO service
      import (reuses UAC `InstructionType` + `CLOB/DEX/ZERO_ALPHA_VENUES`). `ARCHETYPE_ALGO_COMPATIBILITY` maps each of
      the 57 archetypes (via its legs' instrument-types × venue-kinds → induced InstructionTypes) to its valid/invalid
      algo set with reasons. **Impossible combos BLOCKED** (verified: pure-staking/recursive → ONLY BENCHMARK_FILL; LP →
      SWAP algos, no TWAP; event-settled → bet algos, no TWAP). Ghost algorithms
      (SEQUENTIAL_LEGS/SPREAD_ROLL/BEST_PRICE/KELLY_STAKE + BENCHMARK_FILL/ MAX_SLIPPAGE) flagged `implemented=False`. 5
      `SELECTOR_CONTRADICTIONS` carried (F33–F37 below). 11 tests; QG green.
- [x] ✅ [IMPLEMENT] P0. **Exhaustive verdict matrix generator** (PM exporter): full cross-join archetype × venue ×
      instrument_type × instruction × algo → every cell gets an explicit verdict (available | blocked(reason) |
      not_registered) — no absent cells; counts reported; ships as openapi/capability-verdict-matrix.json (+ summary in
      the orphan report). DONE 2026-06-12 — **unified-trading-pm@9a9278a4a** (`generate_capability_verdict_matrix.py`) →
      **unified-api-contracts@c9ab62e** (`openapi/capability-verdict-matrix.json`). Hierarchical per-archetype blocks;
      grounded in `ARCHETYPE_LEG_STRUCTURES` × `ARCHETYPE_ALGO_COMPATIBILITY`. **Headline: 22,448 total cells — 15,093
      available (67.2%) / 7,259 blocked (32.3%) / 96 not_registered (0.4%)**; every cell an explicit verdict, no absent
      cells. Size 2.2 MB (< 20 MB budget — available cells rolled up per cell, blocked/not_registered in full). Count
      summary appended (idempotently) to `capability-orphan-report.txt`. Deterministic (two runs byte-identical). Wired
      into `generate-unified-openapi.sh` + UI-sync; algo-compat edges also folded into the capability manifest
      (`_capability_gaps.extract_algo_compatibility`). 5 PM tests. **Manifest regenerated** (Item 4): 435→558 nodes /
      902→2287 edges (+74 leg nodes from 11→51 real structures, +21 execution_algo nodes + per-archetype algo verdict
      edges); orphans 89→87, deterministic.

- [x] ✅ [IMPLEMENT] P0. **Broker-vs-venue modeling (F38)**: manifest classifies ibkr (and any future broker) as a `broker`
      node with venue⇠routed_via⇢broker edges (TradFi venues = CME/ICE/CBOE); wizard Venues stage renders brokers as a
      routing choice under the venue, never as a peer venue option. ENDPOINT_REGISTRY pipeline-key migration = named
      follow-up (venue-axis vocabulary plan), not this todo.
      — Implemented: `REL_ROUTED_VIA` + `broker:ibkr` node in `_capability_extract.py`; `NodeKind.broker` + `EdgeRelation.routed_via` in `capability-manifest.ts`; `getBrokersForVenue()` in `graph.ts`. PRs: unified-trading-system-ui (feat(capability-manifest): classify ibkr as broker node with routed_via edges (F38)); unified-trading-pm PR #298. 2026-06-12.
- [x] ✅ [AUDIT] P0. **Venue-coverage audit + eligibility widening (F39)**: per asset_group, cross-reference instruments
      universe × ENDPOINT_REGISTRY × execution-service adapter inventory × archetype/leg eligibility; report per venue
      (adapter exists? eligible anywhere? orphan?); widen eligible_venue_ids from adapter inventory with citations;
      remaining orphans typed (unbuilt vs logical).
      — audit_venue_coverage.py (pm@613ee27c) + leg seed widening uac@def855c (kraken/bitget/coinbase added to
      _CEFI_CLOB_VENUES + ARBITRAGE_PRICE_DISPERSION + CARRY_BASIS_PERP/DATED); venue-coverage-report.md generated:
      22 wired, 6 adapter-no-eligibility, 15 registered-no-adapter, 102 orphan (145 total). Orphan delta: 0 (unchanged
      from prior manifest run). ARBITRAGE_PRICE_DISPERSION eligible-venue-count delta: 14→17 (+bitget, +coinbase, +kraken).
      Broker filter added to extract_archetypes_and_families + extract_leg_structures (broker_classed_venues 1→0). 2026-06-12.

- [ ] [AGENT][UI] P0. **Full-universe debug rendering (operator direction 2026-06-12 third message)**: EVERY wizard
      stage renders the COMPLETE dimension universe from the registries — all 57 archetypes (including
      blocked-for-this-category, with reason), all venues (including orphans/unbuilt dead-ends), all instrument types
      (including impossible-for-this-archetype) — verdict chips sourced from the verdict matrix; nothing filtered out,
      only greyed + reasoned ("could be a venue, but: no adapter"). Same for the deployment-ui capability tab. A
      `client mode` flag (hide-junk, curated) is the named successor for client-facing use — debugging mode is the
      default now. pw:L2 gate; property test: per stage, rendered option count == dimension universe count.

- [ ] [AGENT][UI] P2. **uts-ui broker rendering + bundled manifest refresh (F38/F39 follow-up)**: wizard Venues stage
      renders brokers as a routing choice under their routed venues (not peer venues); reads `routed_via` edges from the
      capability manifest to build broker-grouped venue choices. Bundle the regenerated capability-manifest.json
      (uac@238e58f, broker:ibkr node + routed_via edges, 563 nodes / 2325 edges) into the uts-ui static assets to
      eliminate drift with the UAC committed copy. QG: bundled manifest HASH == UAC openapi/capability-manifest.json.
      NOTE: do NOT touch this file from the registry/exporter wave — UI agent owns this.

- [ ] [AGENT][UI] P2. **deployment-ui capability tab bundle refresh (F38/F39 follow-up)**: refresh the bundled
      capability-manifest.json + capability-verdict-matrix.json in deployment-ui assets to reflect the new broker
      node classification and widened eligible_venue_ids (uac@238e58f). QG: bundled manifest HASH == UAC committed copy.
      NOTE: do NOT touch this file from the registry/exporter wave — UI agent owns this.

### 6B — parity quality gates (regression-blocking)

- [ ] [VERIFY] P0. UAC QG step: ARCHETYPE_CAPABILITY_REGISTRY ↔ archetype_capability_manifest.json parity pytest (F4
      remedy) + leg-spec/verdict-matrix determinism tests.
- [ ] [VERIFY] P0. uts-ui QG step: bundled lib/registry/capability-manifest.json HASH-matches the UAC committed copy
      (drift = fail) + vitest property tests asserting the wizard filter functions reproduce the verdict matrix for
      every archetype (sampled venues/instruments at minimum, full where tractable).
- [ ] [VERIFY] P1. PM QG step: two-sided audit (prospectus vs codex) runs as a gate — NEW contradictions fail (existing
      findings baselined).

### 6C — data-availability wiring (deployment-api)

- [x] [AGENT][UI] P1. Wizard Data stage queries deployment-api `/api/data-status/drilldown` + `/schema` for the config's
      derived requirements (per selected venue × data_type × timeframe): render captured/missing windows, missing
      data_types, and the min-data-to-run check against ACTUAL coverage. Env-gated base URL (local/ops: deployment-api
      :8004; UAT: honest "data-status backend not configured" banner). pw:L2 gate. — unified-trading-system-ui@9db31842
      | pw:L2 ✓ 15/15 | regression: tests/smoke/wizard-data-coverage.spec.ts
- [x] ✅ [AGENT][UI] P2. Capability tab: dead-end/orphan rows link through to the same coverage answer (already cross-links
      routes; add the per-cell coverage fetch). — deployment-ui@e02e4c4 | pw:L2 ✓ | regression: tests/smoke/capability_tab.spec.ts

## Wave 2 — proposed enhancements (Claude 2026-06-11; PENDING OPERATOR SIGN-OFF, do not dispatch)

Question bank SSOT (every wizard question pinned to its code anchor):
[`codex/09-strategy/architecture-v2/capability-wizard-question-bank.md`](../../codex/09-strategy/architecture-v2/capability-wizard-question-bank.md).

- [ ] [DESIGN] P2. **Counterfactual "minimal unlock set" engine** — every unavailable edge computes the smallest set of
      missing pieces that would make it available ("Hyperliquid perps: adapter ✓, auth ✗ — 1 edge away"); wizard counts
      demand per blocked edge; weekly demand-weighted gap report auto-emits canonical todos into the gap tracker (same
      ingestion path as `regen_backlog_from_plan.py`). The wizard becomes a roadmap generator.
- [ ] [DESIGN] P2. **Readiness badges per edge** — stamp every capability edge with operational maturity derived from
      the deployments registry + shadow ledger + archived plans:
      `backtest-only | shadow-observed | staging-proven |     live-proven`, mapped to the C/D/B gate model in
      PLAN_FORMAT.md. "Available" without "ever ran" is a different answer.
- [ ] [DESIGN] P2. **Config-space fuzzer → generated smoke tests** — mechanically enumerate reachable wizard configs,
      sample, compile each to a system-integration-tests batch mock-fill scenario. Use-case-3 audit by _execution_, not
      inspection: every reachable config must at least smoke-run; failures are mechanical dead-end findings.
- [ ] [DESIGN] P2. **Manifest as MCP server + conversational wizard agent** — tools: `query_manifest`, `data_status`
      (deployment-api), `run_backtest`, `render_prospectus`; agent-orchestrator hosts it. Powers the "what I need from
      you is these API keys — want a 5-year backtest?" dialogue with answers grounded in registry paths, not model
      memory.
- [ ] [DESIGN] P2. **Versioned manifest + capability changelog + regression CI** — manifest generated per commit; diffs
      = "what the system learned to do this month" (investor-update material); CI FAILS when an edge regresses
      `available → not_available` without a plan reference.
- [ ] [DESIGN] P2. **Inverse wizard / screener** — start from holdings ("I have BTC today, USDT tomorrow") or targets
      (Sharpe ≥ 1.5, max DD ≤ 10%, carry ≥ 8%) and search the manifest + backtest metrics for qualifying archetypes,
      ranked.
- [ ] [DESIGN] P2. **Portfolio mode** — compose multiple configured strategies: aggregate/netted exposures
      (internalization detection when one leg longs what another shorts), correlation from backtests, capital routing
      across pools/SMA via portfolio_allocator + capital_router. Directly models the two-pooled-investors-now /
      SMA-next-year scenario.
- [ ] [DESIGN] P2. **Cost & capacity model** — full fee stack (exchange/gas/broker/clearing + funding + slippage via
      execution cost prediction) + infra cost per lifecycle_class → **breakeven AUM** per configured strategy; capacity
      ceiling vs venue liquidity/min-ticket constraints.
- [ ] [DESIGN] P3. **Wizard sessions as reproducible artifacts** — session JSON (answers + manifest version + config +
      prospectus hash); nightly replay of saved sessions against the fresh manifest (batch-live-reconciliation pattern)
      alerts when an old answer silently changes; doubles as the client-onboarding compliance record.
- [ ] [DESIGN] P3. **Dual-register copy** — every question/config field carries engineer copy (config path, code anchor)
      AND allocator/investor copy (plain English), reusing the existing glossary Term components; prospectus renders in
      either register.
- [ ] [DESIGN] P3. **Named stress-scenario library** — curated historical windows (May-2021 crash, FTX week, Shapella, a
      funding-flip regime) replayed through the backtest runner per configured strategy; positions/PnL/triggered
      kill-switches become the prospectus risk slides.
- [ ] [DESIGN] P3. **Jurisdiction overlay** — investor entity/jurisdiction filters venues/instruments at Stage A
      (client_isolation_and_governance restrictions), so a config can never include a venue the investor cannot legally
      touch.

## Success criteria

- Phase 0: fresh generator run green; zero phantom/missing services; architecture_v2 enums + capability registry present
  in `ui-reference-data.json`; drift gate FAILS on synthetic mismatch.
- Phase 1: manifest covers all 53 archetypes × all registered venues/instruments/algos/sources; every dimension either
  populated or carries a typed gap — **no silent omissions**; orphan/dead-end report distinguishes logical vs unbuilt.
- Phase 2: each gap registry has UAC schema + at least MVP-universe backfill; manifest consumes them.
- Phase 3: prospectus renders for all 53 archetypes; two-sided audit report produced; discrepancies filed as gaps.
- Phase 4: wizard walkthrough reaches a complete strategy config for ≥3 real archetypes (e.g. carry spot-vs-perp BTC,
  LST-stake-and-short-perp, an options vol archetype) with only-valid-options filtering; capability tab live in
  deployment-ui; pw:L2 green both repos.
- Phase 5: one real `needs_code_scan` gap round-tripped through the orchestrator into a manifest annotation; one
  backtest-on-demand round trip from wizard config to prospectus metrics.

## Full-execution criterion

`bash scripts/openapi/generate-unified-openapi.sh && python scripts/openapi/generate_capability_manifest.py && python scripts/openapi/generate_strategy_prospectus.py --archetype carry_basis_perp`
on the laptop (full workspace) completes end-to-end: regenerated registries, manifest with 0 untyped unknowns, rendered
prospectus whose two-sided audit section diffs against
`codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md`. Wizard verified via Playwright L2 on both UI repos
against the committed manifest.

## Codex SSOT updates

- NEW
  [`codex/09-strategy/architecture-v2/capability-wizard.md`](../../codex/09-strategy/architecture-v2/capability-wizard.md)
  — concept SSOT (shipped with this plan).
- `codex/14-customer-journeys/` — strategy-onboarding journey update when Phase 4 lands.
- `plans/audit/instructions/strategy_master_audit_instructions.md` — add recurring two-sided-audit criterion (wizard vs
  codex vs code) once Phase 3 ships.

## Findings discipline (operator direction 2026-06-11)

Autonomous build dispatched 2026-06-11 under `cursor-configs/AUTONOMOUS_AGENT_RULES.md`. Two side-docs, both mandatory
for every agent on this plan:

- **Capability gaps** (missing registries/extractions) →
  [`issues/capability_wizard_gap_discovery_2026_06_11.md`](issues/capability_wizard_gap_discovery_2026_06_11.md)
- **Bugs / conflicting truths / dual implementations / understanding gaps** →
  [`issues/capability_wizard_analysis_findings_2026_06_11.md`](issues/capability_wizard_analysis_findings_2026_06_11.md)

## Progress Log (append-only — survives context compression)

- 2026-06-11 — Plan + codex SSOT (`capability-wizard.md`) + question bank + gap tracker + findings doc authored;
  strategy_master related_plans updated (+ duplicate section fix = F6). Autonomous execution started: Wave 1 = Phase 0
  generator repair (PM, sub-agent) ∥ UAC capability/gap schemas (sub-agent). Wave 2 = exporter → prospectus → UI.
- 2026-06-11 — **Wave 1 DONE.** Phase 0 shipped (unified-trading-pm@50bdbcd36, PR #268: manifest-driven service
  auto-discovery + sys.exit(1) on drift; architecture_v2 extraction — 57 archetypes/227 UIC enums/22-archetype
  capability registry now in ui-reference-data.json; findings F4-confirmed/F8/F9 appended @706e1196a). UAC schemas
  shipped (unified-api-contracts@6f31f59: capability_manifest + 6 gap-registry modules, TREASURY_SPLIT_POLICIES seeded,
  rest honest-empty, 40 tests, QG 216s green). Open from Phase 0: full-suite regeneration commit (host lacks full
  .venv-workspace — exporter wave handles what it can, else documented). **Operator added Phase 3.5 (scenario stepper)
  mid-flight — baked into plan.** Wave 2 dispatching: capability manifest exporter (PM) + UAC output commit.
- 2026-06-11 — **Phase 0 COMPLETE** (unified-trading-pm@50bdbcd36, PR #268). Three generator files repaired:
  `generate_unified_spec.py` — SERVICE_REGISTRY auto-derived from workspace-manifest.json, 13 phantom services removed,
  fail-on-drift enforcement; `generate_config_registry.py` — phantom services removed, 4 real services added with
  verified import paths, 2 consolidated-monorepo services documented (no root config); `generate_ui_reference_data.py` —
  architecture_v2 submodule walk added, ARCHETYPE_CAPABILITY_REGISTRY serialised deterministically, StrategyArchetype
  (57), StrategyFamily (9), total UIC enums 227. Quality gates passed. Generator run verified with UAC venv. Finding F4
  confirmed (archetype_capability_manifest.json hand-maintained alongside Python registry, no drift check). One Phase 0
  item deferred: scheduled workflow for drift CI gate (fail-on-run is the current gate).
- 2026-06-11 — **Phase 1 capability-manifest exporter v1 SHIPPED** (capability-exporter, slot-4).
  `generate_capability_manifest.py` + `_capability_{extract,gaps,orphan}.py` (PM@78b2e893a, PR #270) → consumes the UAC
  `CapabilityManifest` schema (imported, never redefined). Output `capability-manifest.json` (UAC@1bc2f07): **409 nodes
  / 663 edges** (available 441, partial 140, not_registered 63, not_available 19; typed gaps: 60 missing_registry, 3
  needs_code_scan, 1 missing_extraction, 19 logical_dead_end). Orphan report `capability-orphan-report.txt`: **124
  orphans, 25 unbuilt dead-ends, 16 logical dead-ends**. Coverage: (a) archetypes/families +
  ARCHETYPE_CAPABILITY_REGISTRY, (b) venues/chains/instrument-types + auth/access from ENDPOINT_REGISTRY, (c) data
  sources + transports + modes (live/ replay = typed gap, NOT markdown-parsed), (d) all 6 gap registries + treasury
  split → real wallet nodes, (e) risk surface (KillSwitchReason × RiskGateLayer), (f) **service-resident registries
  imported via per-service `.venv` subprocess — exec algos (7), feature groups (34 w/ lookback), ML model variant config
  ALL imported OK on this host** (no gap'd source). Determinism verified (run twice = byte-identical);
  `generated_from_commit` = UAC HEAD via git, no timestamps. Wired into `generate-unified-openapi.sh` + its UI-sync
  block. Min-data-to-run: feature-lookback derived, ML-training-window factor is `missing_extraction` (runtime config,
  no static constant). Findings F12 (config-registry un-regenerable on non-workspace-venv host — destructive empty), F13
  (SOURCE_PRIORITY no clean facade), F14 (uic-openapi-sync ships TS types only, NOT registry JSONs) appended.
  Gap-discovery 2026-06-11 entry quantifies the surface. **Unticked**: Phase-0 full-suite regen (config-registry.json +
  full openapi spec need `.venv-workspace`, absent on-host — F12; partial UAC-output regen done);
  uic-openapi-sync-shipping sub-claim (F14 — wrong workflow; manifest ships via the generator sync block).

- 2026-06-11 — **Phase 3 strategy prospectus generator SHIPPED** (capability-wizard Phase 3, slot-5).
  `generate_strategy_prospectus.py` + `_prospectus_{codex,manifest}.py` + `audit_prospectus_vs_codex.py` (PM PR #272) →
  57 archetype prospectus docs + `prospectus-codex-audit.md` (UAC@fe37eae, `openapi/prospectus/`). All 4 helper modules
  under 900-line cap; quality gates exit 0. Determinism verified (byte-identical on two full runs). **Per-section
  honesty stats**: 57/57 archetypes have codex docs (0 machine-only); all 57 render 7 sections including
  [MACHINE-DERIVED] + [CODEX-DERIVED] labels, honest no-backtest performance block, fund-flow mermaid with
  TREASURY_SPLIT_POLICIES (DeFi 20/80, CeFi 0/100, Sports 0/100), KillSwitchReason + RiskGateLayer risk section. **Audit
  headline**: (a) 0 enum-without-doc, (b) 2 orphan codex docs (doc-without-enum), (c) 1 venue-category contradiction
  filed as F15. Gap tracker: 2 orphan docs appended. 19 regression tests (determinism, 57-archetype count, all 7
  sections, honesty labels, fund-flow LST legs, mermaid fence). Wired into `generate-unified-openapi.sh`. SHAs: PM PR
  #272 + UAC@fe37eae.

## Out of scope / named successors

- Client-facing lite wizard + alpha-curtailment tiers (use case 4) — successor plan.
- Replacing the public strategy questionnaire — it stays as demand capture; wizard supersedes it only for onboarding.
- Rebuilding any part of the data-status drilldown — delegation only.
- Live integration beyond deployment-api data-status + backtest runner calls (wizard is registry/code-driven by design).
- 2026-06-11 — **Wave 2+3 DONE.** Exporter shipped (PM@78b2e893a PR#270 MERGED; UAC@1bc2f07: capability-manifest.json
  409 nodes/663 edges, all service registries imported via per-service venvs, orphan report: 124 orphans / 25 unbuilt
  dead-ends / 16 logical; F12–F14). Prospectus shipped (PM PR#272 + UAC@fe37eae: 57/57 archetype docs, two-sided audit →
  0 enum-without-doc, 2 orphan docs, 1 contradiction = F15; 19 tests). Scenario stepper shipped (UAC@6262c3f +
  strategy-service@e0ed11c + e2e-testing@3e41ecb: real V2BatchHarness, apd full-emission proof + forced
  DAILY_LOSS_BREACH kill trips, 3/3 smoke; carry entry-emission blocked by empty collateral registry = the Phase 2 gap
  made concrete; F16/F17). Wizard UI shipped (unified-trading-system-ui@9f40331, /wizard, pw:L2 8/8, 41 unit tests).
  Capability tab shipped (deployment-ui@13ac831, pw:L2 6/6, 22 unit tests; F18/F19). Remaining: Phase 3.5 UI stepper
  stage, Phase 5 (escalation write-back + backtest-on-demand), registry backfills, Wave-2 enhancements (operator
  sign-off pending).
- 2026-06-11 — Phase 5 dispatch (annotation write-back sidecar + needs_code_scan escalation emitter +
  backtest-from-wizard-config) was STOPPED by the operator mid-run before any commit landed; trees verified clean. The
  two Phase 5 [IMPLEMENT] todos remain open and fully specified in the dispatch record. NOTE: fleet-wide GitHub Actions
  billing outage filed @bf83fe7ec — this plan's in-flight promotion PRs (uts-ui@9f40331, dep-ui@13ac831, UAC drains)
  self-merge once billing is restored. Dev servers for operator review: wizard http://localhost:3100/wizard, capability
  tab http://localhost:5183.

- 2026-06-11 — **Phase 5 DONE.** Both [IMPLEMENT] todos shipped. (1) Annotation write-back: PM@f84a119 —
  `capability-annotations.yaml` sidecar (2 session-evidenced entries for kill/stop predicates + carry_staked_basis);
  `_capability_annotations.py` loader + merge helper; `generate_capability_manifest.py` step-7 sidecar integration;
  `emit_capability_gap_todos.py` escalation emitter (reads manifest, finds unannotated needs_code_scan edges, appends
  dedup-idempotent `[AGENT] P2.` todos). Regenerated UAC outputs: 2 annotated edges, 0 annotation orphans, 1 P2 todo
  emitted for gap_registry:order_semantics → execution-service. UAC outputs re-committed via quickmerge. (2) Backtest-
  on-demand: e2e-testing@194d66b — `backtest_from_wizard_config.py`; data-availability precheck via
  `read_availability_index` + `resolve_bucket_name`; GroupBRunner wired (real code path, batch=live HARD RULE); honest
  typed verdict `PRECHECK_UNAVAILABLE{...}` confirmed on `apd_price_dispersion_btc.json` (30 synthetic ticks, 0 fills, 0
  pnl — expected in CLOUD_MOCK_MODE); results JSON + markdown written. QG passes: strategy-service peripheral
  (basedpyright + ruff) green; e2e-testing QG green. See F20 for GroupBRunner API findings.
- 2026-06-11 — Phase 5 SHIPPED (PM@507d14f: capability-annotations.yaml sidecar + write-back merge + escalation emitter,
  2 edges annotated; UAC@c3a3494 regenerated outputs; e2e-testing@194d66b backtest-on-demand with honest precheck).
  Wizard stepper stage SHIPPED (uts-ui@9f087aa8, pw:L2 12/12; help-text markdown fix). Operator walkthrough caught F22
  (multi-leg restrictions collapsed to single staking cell) → Phase 2.6 added (leg-level restriction model); dispatching
  UAC leg-spec schema + exporter + leg-aware wizard stages.
- 2026-06-11 — **Phase 2.6 SCHEMA + SEED + EXPORTER SHIPPED (F22 leg-truth model).** Absorbed a dead predecessor's
  PARTIAL uncommitted work: its `archetype_leg_spec.py` (888L) + test were sound and finished as-is; its
  `internal/__init__` export was reversed in favour of `architecture_v2/__init__` (matching the `capability_manifest`
  sibling); its PM "exporter edits" were actually pure `# noqa: qg-empty-fallback` QG-autofix churn (NOT leg logic) →
  restored + the leg-aware exporter written fresh. **uac@c17a6be** = `ARCHETYPE_LEG_STRUCTURES` SSOT (11 archetypes,
  `ArchetypeLegRole`×11 / `LegConstraintKind`×3 / `LegConstraint`+`fallback_variant`; staked-basis
  `requires_collateral_acceptance(lst,hedge_venue)`→`straight_basis` conditional; CeFi+DeFi hedge venues per-leg) +
  `CapabilityNodeKind.LEG`; basedpyright-strict, 9 tests. **pm@8a0fdd1** = `extract_leg_structures()` (25 leg nodes +
  has_leg/trades_instrument/supports/leg_constraint edges; 46 archetypes→gap edges), audit (d) legs-in-prose drift
  heuristic (6 flagged), prospectus "Leg Structure" table (honest gap line where absent). UAC outputs regenerated
  deterministically (manifest 435 nodes/902 edges, generated_from_commit=c17a6be; twice byte-identical). Dual
  representation (leg registry = leg-truth SSOT; flat cell registry/JSON unchanged per F4) documented in the module
  docstring; follow-up "cells should derive from leg specs" appended to findings F22. **Remaining open: the [AGENT][UI]
  P1 leg-aware wizard stages** (Instruments/Venues grouped by leg role, conditional surfaced, cross-category hedge leg
  auto-included; pw:L2 gate) — dispatched, not done this turn. Churned foreign PM files restored as pure noqa-churn:
  `tier_c_promotion_gate.py`, `validate-buildspec.py`, `workflow_template_drift_baseline.json` (verified cosmetic).
- 2026-06-11 — **Phase 2.6 COMPLETE — F22 closed end-to-end.** Leg-spec registry UAC@c17a6be (10 archetypes seeded with
  citations; constraint kinds incl. requires_collateral_acceptance + fallback_variant straight_basis) → leg-aware
  exporter PM@8a0fdd1c8 → regenerated manifest UAC@b1a5419 (435 nodes / 902 edges; +26 leg nodes; orphans 124→89;
  unbuilt dead-ends 25→54 — leg edges exposed more unbuilt paths) → leg-aware wizard ui@85f27c46 (pw:L2 13/13;
  carry/staked-basis now renders 4 leg groups incl. perp hedge, required-locked, straight-basis fallback text from
  constraint metadata; cross-category legs auto-included; flat fallback + honest banner for archetypes without leg
  specs). F25/F26 filed. Remaining open scope: registry backfills (Phase 2 tranche), needs_code_scan escalations
  (auto-emitted in gap tracker), Wave-2 enhancements (operator sign-off), client-lite successor plan.

- 2026-06-12 — **Phase 2 COLLATERAL backfill COMPLETE (operator direction "empty collateral registry — fill it up").**
  COLLATERAL_REGISTRY filled for the MVP venue universe from `archetype_leg_spec.py` eligible venues (perp:
  hyperliquid/gmx_v2/drift/binance/bybit/deribit/okx; lending: aave_v3/kamino; staking: lido/rocketpool/jito/marinade →
  NO policy by design). **IN-REPO-FIRST sourcing (the registries were NOT actually empty fleet-wide — only the new
  `COLLATERAL_REGISTRY` was)**: transcribed haircuts/accept-reject from
  `unified_api_contracts/registry/venue_collateral.py` (Stream A audit 2026-05-07/08), Aave per-asset
  LTV/liq-threshold/bonus from `defi_reserve_params.py` (on-chain getConfiguration, 2026-05-15), tier-1 MMR from
  `cefi_margin_tiers.py`, Kamino LST haircut from execution-service `lst_collateral_resolver.py`. Cross-checked official
  docs (Hyperliquid USDC-only + MM=½IM@maxlev; Deribit stETH 7.5% reduced-from-15% eff. 2026-01-13 X:PM-only;
  Aave/Kamino dashboards) — as_of 2026-06-12, every numeric cited; Kamino per-asset LTV honestly None. **SHAs**: UAC
  source `f997f3b` (schema additive-extend + 9 policies + 23 tests; QG green 205s), UAC outputs `cc269c2` (manifest
  collateral edge `not_registered`→`available`, 9 venue nodes + 53 per-asset edges; orphan report regen), PM exporter
  `5b5f2fe80` (`_capability_gaps.py` per-venue/per-asset emission; PM QG green). **Schema extensions (additive, no
  break)**: `VenueCollateralKind` enum; `AssetHaircut.{accepted,max_ltv, liquidation_threshold,liquidation_bonus}`;
  `CollateralPolicy.{venue_kind,collateral_notes}` + `accepted_assets()`; `STAKING_VENUES_NO_COLLATERAL_POLICY`.
  **STRETCH LANDED (e2e-testing `7075bd1`)**: `_stepper_engine.py` `_config_overrides` now seeds
  accepted-perp-collateral from the UAC registry for CARRY_STAKED_BASIS — selects a hedge venue that accepts the LST +
  passes it UPPERCASE (the F27 case-fix). New scenario `csb_staked_basis_eth_lst_accepted.json` (lido stETH + DERIBIT
  @7.5%) EMITS the staked carry entry — step 0 `instruction_count: 1`, `structure: LST_AS_MARGIN`, 4 fills — closing the
  loop the Phase-3.5 csb scenario flagged. Original `etherfi-hyperliquid` (USDC-only) scenario correctly still emits 0
  (straight-basis). Smoke 4/4 green. **F27/F28 filed below.** STILL OPEN: fees / order-semantics / sim / fund-structure
  backfills (separate tranches).
- 2026-06-12 — Collateral registry BACKFILLED (UAC@f997f3b: 9 venue policies, 53 accepts_collateral edges incl. 14
  documented rejections, all numbers cited in-repo or official docs; gap edge not_registered→available; UAC@cc269c2
  outputs; PM@5b5f2fe80 exporter; e2e@7075bd1 stretch: stepper seeds collateral from UAC registry — LST-accepted Deribit
  scenario now EMITS the staked carry leg). **BIG findings: F27 — carry entry-emission was never the empty registry;
  strategy-service \_derive_structure calls accepted_perp_collateral with lowercase venue ids against an UPPERCASE-keyed
  VENUE_COLLATERAL_MATRIX → always [] for EVERY venue (May-23 critical path; service frozen — owner fix recommended).
  F28 — venue_collateral.py vs execution-service lst_collateral_resolver.py disagree on LST haircuts (dual SSOT).** UAT
  deploy of the wizard: exposed + fixed F29 (deploy-ui.sh REPO_ROOT drift, deployment-service@dcb5fdb); Cloud Build →
  odum-portal-staging in flight → uat.odum-research.com/wizard.
- 2026-06-12 — **Wizard DEPLOYED: https://uat.odum-research.com/wizard (build 7, exit 0, HTTP 200).** Getting there
  exposed + fixed three pre-existing deploy-path rots: F29 deploy-ui.sh REPO_ROOT migration drift
  (deployment-service@f84ccd8), F30 unpinned pnpm@latest in the Dockerfile (uts-ui@0f8f00d6, pinned 9.15.9), F31
  dangling .gitleaks.toml symlink breaking next build in docker context (same commit). F32 host gotcha documented
  (cursor-server node 20.18 shadows system node 22 → UI QG needs PATH=/usr/bin first). Full-suite openapi regen remains
  a CI-runner job (F12) — on-host UAC-importable outputs stay the local path.
- 2026-06-12 — Operator review: stepper exists (CLI-interactive + UI viewer; live-driving UI = follow-up), but
  combinatorics NOT exhaustive (leg specs 10/57; no archetype→algo compatibility registry → wizard cannot block algo
  mismatches) and data-availability not yet wired into the UI. **Phase 6 added** (6A full-coverage registries + verdict
  matrix, 6B parity quality gates so UI==registry==code cannot regress, 6C deployment-api data-status wiring).
  Dispatching 6A (UAC+PM) ∥ 6C (uts-ui); 6B after 6A lands.
- 2026-06-12 — Phase 6A (registry/exporter wave) complete. UNIT 1: broker_routes.py (BrokerRoute/BROKER_ROUTES/broker_for_venue/is_broker/routed_via) + __init__.py exports + test_broker_routes.py + _endpoint_registry_data.py F38 comment — uac@cdb59bb. UNIT 2: PM exporter broker node kind + routed_via edges (_capability_extract.py extract_brokers + extract_venues broker filter + _capability_orphan.py find_broker_classed_venues + generate_capability_manifest.py) — pm@4948325c/613ee27c. UNIT 3: audit_venue_coverage.py (F39) — 22 wired, 6 adapter-no-eligibility, 15 registered-no-adapter, 102 orphan — pm@4074e49c. UNIT 4: eligible_venue_ids widening — kraken/bitget added to _CEFI_CLOB_VENUES + CARRY_BASIS_PERP/DATED; coinbase/kraken/bitget to ARBITRAGE_PRICE_DISPERSION spot; bybit/okx/bitget/kraken to CARRY_BASIS_DATED spot leg — uac@def855c. UNIT 5: regenerated capability-manifest.json (563 nodes / 2325 edges, broker_classed_venues 0) + capability-verdict-matrix.json (24752 cells, 16913 available) + venue-coverage-report.md + capability-orphan-report.txt — uac@238e58f. Adapter-vs-registry mismatches found: FX/BITFINEX-SPOT/KRAKEN-FUTURES/KRAKEN-SPOT/BITGET-FUTURES/BITGET-SPOT have adapters but were not in VENUE_CATEGORY_MAP or ENDPOINT_REGISTRY (adapter-no-eligibility); NASDAQ/NYSE have adapters (ibkr-routed) but not in any eligible_venue_ids. uts-ui + deployment-ui bundle refresh noted as [AGENT][UI] P2 follow-up todos.
