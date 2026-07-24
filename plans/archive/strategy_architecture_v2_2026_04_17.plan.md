---
doc_type: plan
title: Strategy Architecture v2 — Family / Archetype / Axes / Cross-Cutting
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, execution-service, strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-17"
owner: iggy
started: 2026-04-17
locked_by: live-defi-rollout
locked_since: 2026-04-17
---

# Strategy Architecture v2 — Implementation Plan

## Context

Canonical architecture converged across two prior sessions (2026-04-16 → 2026-04-17):

- **8 families** (orthogonal alpha styles): ML Directional, Rules Directional, Carry & Yield, Arbitrage/Structural,
  Market Making, Event-Driven, Vol Trading, Stat Arb/Pairs
- **18 archetypes** (code paths under families)
- **7 axes of composition**: signal source, edge method, staking method, venue eligibility, expression, hold policy,
  share class
- **10 cross-cutting concerns**: risk gates (4-layer), venue selection split, execution policies, transfer/rebalance,
  portfolio allocator, MEV protection, benchmark fills, capital/client isolation, trade expression, venue-account
  coordination
- **5-layer identity**: family → archetype → instance → config → derived categories
- **3-axis versioning**: code/build, artifact, schema
- **Polymorphic StrategyInstruction** (11 actions) + parallel AccountInstruction
- **3 backtest groups**: A (ML training), B (strategy alpha), C (execution alpha)
- **Batch = live** (benchmark fills contract)
- **Capital custody models** per category (CeFi SMA, CeFi fund future, DeFi client wallet, DeFi firm, Unity pool, sports
  direct, TradFi IBKR, TradFi counterparty)
- **Fund-client framing**: we face ONE client which may itself be a fund
- **Unity meta-broker**: 10 child books, single TCP, USD share class, Java Feed Connector sidecar
- **Kraken removed everywhere**

Supersedes legacy category-based organization in `09-strategy/{cefi,defi,sports,tradfi,prediction}/`. See
`/codex/09-strategy/architecture-v2/MIGRATION.md` for complete old-doc → new-archetype mapping.

## Doc-writing progress (Phase 1)

- [x] [DOC] P0. Inventory existing strategy docs (cefi/defi/tradfi/sports/prediction + cross-cutting) to build migration
      reference
- [x] [DOC] P0. Create /codex/09-strategy/architecture-v2/README.md (full taxonomy + Capital Flow Lifecycle section)
- [x] [DOC] P0. Create /codex/09-strategy/architecture-v2/MIGRATION.md (56 legacy docs → v2 placement audit)
- [x] [DOC] P0. Update /codex/04-architecture/capital-structure-and-regulatory.md with fund-client framing +
      per-category custody
- [x] [DOC] P0. Write 8 family docs in architecture-v2/families/ (ml-directional, rules-directional, carry-and-yield,
      arbitrage-structural, market-making, event-driven, vol-trading, stat-arb-pairs) — all include "Not in this family"
- [x] [DOC] P0. Write 18 archetype docs in architecture-v2/archetypes/ — all include "Not in this archetype"
- [x] [DOC] P0. Write axes/signal-sources.md
- [x] [DOC] P0. Write axes/edge-methods.md
- [x] [DOC] P0. Write axes/staking-methods.md
- [x] [DOC] P0. Write axes/venue-eligibility.md
- [x] [DOC] P0. Write axes/expression.md
- [x] [DOC] P0. Write axes/hold-policy.md
- [x] [DOC] P0. Write axes/share-class.md
- [x] [DOC] P0. Write cross-cutting/risk-gates.md
- [x] [DOC] P0. Write cross-cutting/venue-selection-split.md
- [x] [DOC] P0. Write cross-cutting/execution-policies.md
- [x] [DOC] P0. Write cross-cutting/transfer-rebalance.md
- [x] [DOC] P0. Write cross-cutting/portfolio-allocator.md
- [x] [DOC] P0. Write cross-cutting/mev-protection.md
- [x] [DOC] P0. Write cross-cutting/benchmark-fills.md
- [x] [DOC] P0. Write cross-cutting/capital-client-isolation.md
- [x] [DOC] P0. Write cross-cutting/trade-expression.md
- [x] [DOC] P0. Write cross-cutting/venue-account-coordination.md
- [x] [DOC] P0. Write /codex/04-architecture/strategy-execution-protocol.md
- [x] [DOC] P0. Write /codex/04-architecture/artifact-versioning.md
- [x] [DOC] P0. Write /codex/04-architecture/execution-policy.md
- [x] [DOC] P0. Write /codex/04-architecture/backtest-groups.md
- [x] [DOC] P0. Write /codex/04-architecture/capital-flow-model.md
- [x] [DOC] P0. Write /codex/04-architecture/schema-versioning.md
- [x] [DOC] P0. Write /codex/04-architecture/slow-fast-routing-split.md
- [x] [DOC] P0. Write /codex/04-architecture/capital-efficiency-patterns.md
- [x] [DOC] P0. Write /codex/04-architecture/account-instructions.md
- [x] [DOC] P0. Write /codex/02-venues/venue-registry-reference.md
- [x] [DOC] P0. Write /codex/02-venues/prime-brokers.md
- [x] [DOC] P0. Write /codex/02-venues/unity-integration.md
- [x] [DOC] P0. Write /codex/03-services/portfolio-allocator.md
- [x] [DOC] P0. Write /codex/03-services/venue-capability-registry.md
- [x] [DOC] P0. Write /codex/06-coding-standards/strategy-identity-versioning.md
- [x] [DOC] P0. Write /codex/06-coding-standards/artifact-naming.md

## Apply consistently to all remaining docs

- [x] [RULE] Every family, archetype, axis, and cross-cutting doc MUST have a "Not in this X" section — DONE. All 18
      archetype docs in `codex/09-strategy/architecture-v2/archetypes/` now have a `## Not in this archetype` section
      listing the common mis-classifications and where those cases actually live. All 8 family docs + all 11
      cross-cutting docs already had "Not in this family/X" lines in the intro. Verified via
      `find codex/09-strategy/architecture-v2/ -name "*.md" | xargs grep -Li "Not in this"` → zero missing.

## Outstanding architectural decisions (TBDs)

- [x] [TBD] Unity 10 child books — all 10 confirmed with real commissions from quant-portal on 2026-04-17. UAC
      `UNITY_CHILD_BOOKS` now holds VX/SHARPBET (0.2% COMMISSION_ON_WIN), 3ET (0.5%), BETDEX (1.6%), MATCHBOOK (2.2%),
      IBC (2.5%), BETFAIR (2.8%), BROKER5 (3.0%), CROWN + SBO commission-free. Retired placeholders guarded by
      `test_get_by_id_returns_none_for_retired_placeholders`. Commits: UAC `9efce04`/`1a5a40b`/`652a301`, PM `2bd06bd7`.
- [x] [TBD] Exact Kelly fraction defaults per archetype — `strategy-service@28167d7`
      `engine/strategies/v2/archetype_defaults.py` `KELLY_FRACTION_BY_ARCHETYPE`. Five-tier bucketing by risk profile:
      0.75 for passive yield (YIELD*ROTATION_LENDING, YIELD_STAKING_SIMPLE), 0.50 for stable structural (CARRY_BASIS*_,
      ARBITRAGE*PRICE_DISPERSION, MARKET_MAKING_CONTINUOUS), 0.375 for mid-variance (CARRY_STAKED_BASIS,
      MM_EVENT_SETTLED, STAT_ARB*_), 0.25 for directional with estimation error (ML*DIRECTIONAL*\*,
      RULES_DIRECTIONAL_CONTINUOUS, VOL_TRADING_OPTIONS), 0.125 for high-variance / atomicity-risk
      (RULES_DIRECTIONAL_EVENT_SETTLED, EVENT_DRIVEN, CARRY_RECURSIVE_STAKED, LIQUIDATION_CAPTURE). 8 tests enforce
      every archetype is covered + tier assignments match the risk story. Per-strategy configs override via
      `initial_config["kelly_fraction"]`.
- [x] [TBD] Allocator cadence defaults per client size — `strategy-service@28167d7` `portfolio_allocator/cadence.py`
      `build_default_allocator_cadence(total_client_equity_usd)`. Tiered by AUM: WEEKLY Monday 00:00 UTC below
      $500k,
      DAILY 00:00 UTC for $500k-$5M, HOURLY every 4h for $5M-$50M, HOURLY every 2h at $50M+. 11 tests cover
      each boundary + monotonic tightening. Per-client configs override by passing an explicit `AllocationCadence` to
      `ClientAllocatorInstance` at registration.
- [x] [TBD] Shadow deployment pattern specifics for archetype upgrades — codified. New codex doc
      `/codex/04-architecture/shadow-deployment-pattern.md` + `strategy-service@0b94e8c`
      `engine/strategies/v2/shadow_deployment.py` with `ShadowDeploymentPolicy` (content-hashed, versioned per
      archetype), `ShadowComparisonMetrics`, `ShadowDecision` (PROMOTE/EXTEND/REJECT/ROLLBACK),
      `evaluate_shadow_deployment()` priority-ordered evaluator, tight-defaults for MM/vol/liquidation/recursive
      archetypes. 16 unit tests.
- [x] [TBD] Delta-neutral exit pathway when kill-switch fires on one venue but another eligible venue is alive —
      confirmed + shipped. Default is delta-neutral exit (cheapest); reductions-only on DATA_STALE; HUMAN_REQUIRED on
      recon + exec dual failure. Codified in `risk-and-exposure-service@7f9a1df` `v2/kill_switch_rules.py`
      (`KillSwitchRulesEngine`) + codex `04-architecture/kill-switch-circuit-breaker.md` + memory
      `feedback_kill_switch_multi_venue_rules.md`.

## Phase 2 — UAC schema additions (LANDED)

Commit: `unified-api-contracts@4bc83bc` on `live-defi-rollout`.

- [x] [CODE] P1. Polymorphic StrategyInstruction (11 action variants + AccountInstruction) —
      `internal.architecture_v2.schemas`
- [x] [CODE] P1. Archetype / Instance / Config tiers as typed registry — `StrategyInstanceIdentity` +
      `StrategyInstanceDefinition`
- [x] [CODE] P1. Venue capability with haircuts, LTV, collateral, portfolio margin spec — `VenueCapabilityV2`,
      `LtvAndHaircut`, `CollateralRulesV2`, `MarginSpec`, `NettingRule`, `CommissionStructureV2`
- [x] [CODE] P1. Compatibility matrix (archetype, venue-category, action, instrument-type) — `CompatibilityEntry` +
      `COMPATIBILITY_SEED`
- [x] [CODE] P1. AllocationDirective schema (portfolio allocator → strategy equity) — `AllocationDirective` +
      `StrategyEquityDirective`
- [x] [CODE] P1. Child venue schema (Unity child books) — `UnityChildVenue` + `UNITY_CHILD_BOOKS` (10: 8 confirmed + 2
      TBD)
- [x] [CODE] P1. venue_type enum (SINGLE_VENUE, META_BROKER, DATA_AGGREGATOR) — `VenueType`
- [x] [CODE] P1. Remove Kraken from UAC venue registry + adapters + credentials registry — external/kraken/ deleted,
      \_KRAKEN SourceCapability removed, endpoint registry purged. External-provider-inventory mocks (tardis, defillama)
      retain Kraken in recorded responses (cassette parity).
- [x] [CODE] P1. Remove Kraken from downstream consumers — Phase 12 sweep across 6 repos done (UAC `6693e29`, UI
      `0daef23`, MTDS, deployment, client-reporting, UTL). `grep -r KRAKEN` in code returns zero matches outside UAC
      external-provider cassettes. Test `test_no_row_uses_kraken` in strategy-service's legacy mapping guards
      regression.

## Phase 3 — Strategy-service refactor

- [x] [CODE] P1. 18 family engines + archetype handlers + instance registry + config hash/version (strategy-service) —
      `strategy-service@ec4ea26`/`96aae04`/`05a916e`/`d2c9780` on `live-defi-rollout`. Every archetype has a real
      `on_tick` body (no stubs); `StrategyInstanceRegistry` + `ConfigRegistry` (SHA-256 16-hex content hash + monotonic
      version) in `v2/registry.py`; `V2EngineOrchestrator` + `v2_shadow_runner` expose per-env shadow mode to legacy
      `BaseStrategyManager`. 41/41 unit tests pass, QG green.

## Phase 4 — Execution-service polymorphic orchestrator

- [x] [CODE] P1. 11 action handlers (TRADE, SWAP, LEND, BORROW, STAKE, UNSTAKE, QUOTE, TRANSFER, BRIDGE, ATOMIC, CANCEL)
      — `execution-service@5e58477` / `f5eee2b1`. All in `v2/handlers.py`, dispatched by `V2InstructionRouter`.
- [x] [CODE] P1. Execution policy registry (rule-table per venue × action × condition, artifact-versioned) —
      `execution-service@76499fa8` `v2/execution_policies.py`. `AppliesTo` gate + `PolicyRule` +
      `ExecutionPolicyArtifact` (content-hashed, versioned) + `ExecutionPolicyRegistry` (append-only, monotonic
      version) + `resolve_algo()` document-order / first-match-wins / default-deny evaluator. Supports scalar operators
      (`<`, `<=`, `>`, `>=`, `==`, `in`, `not_in`) + compound groups (`any_of` / `all_of`). Mirrors the codex contract
      in `/codex/04-architecture/execution-policy.md` exactly, including the canonical small/medium/large TWAP ramp
      example. 23 unit tests.
- [x] [CODE] P1. Venue-account pre-flight — `risk-and-exposure-service@7f9a1df` `v2/preflight.py`
      `run_layer3_venue_account_preflight`. Includes haircuts, LTV, liquidation distance, utilisation.
- [x] [CODE] P1. ATOMIC multi-leg + LEADER_HEDGE sequencing — `execution-service@5e58477` `v2/handlers.py`
      `AtomicHandler` + `v2/account_orchestrator.py` for multi-venue sequencing.
- [x] [CODE] P1. Benchmark fills per action type — `execution-service@5e58477` `v2/benchmark_fills.py`
      `BenchmarkFillRegistry` (7 modes: ARRIVAL_MID / POOL_MID_AT_BLOCK / FUNDING_SNAPSHOT / EVENT_SETTLEMENT_MID / VWAP
      / TWAP / BOOK_TOP_AT_ACK).
- [x] [CODE] P1. META_BROKER child-venue SOR (Unity) — our side ships child-venue targeting (`UnityMultiplex` tags each
      outbound by `child_venue_id`; `UnityBridge.place_bet` resolves the child book); Unity's internal SOR picks the
      executing book on their side per `/codex/02-venues/unity-integration.md` line 156.
- [x] [CODE] P1. Unity adapter: TCP feed connector sidecar, Python bridge, all 3 sports enabled, bet placement, wallet
      sync, rollover tracking, turnover for subscription waiver — `execution-service@5e58477` shipped the adapter
      skeleton; `execution-service@207f3266` shipped the mock Feed Connector + real stdin/stdout IPC (send/recv,
      heartbeat round-trip, pump, auth/subscribe/place/cancel), so the full stack is runnable locally without Unity
      creds. 30/30 unit tests. Live UAT smoke still gated on Unity creds + $550 connection fee.

## Phase 5 — Portfolio-allocator-service (new)

- [x] [CODE] P1. 8 allocator archetypes: FIXED, PNL, SHARPE, RISK_PARITY, KELLY, MIN_CVAR, REGIME, MANUAL —
      `strategy-service@5525188` `portfolio_allocator/archetypes.py` (pragmatic sub-package placement; designed to be
      relocatable if we later split it into its own repo).
- [x] [CODE] P1. Per-client instances + AllocationDirective events — `strategy-service@5525188` / `426c02e`
      `portfolio_allocator/service.py` (`ClientAllocatorInstance` / `PortfolioAllocatorService`) +
      `portfolio_allocator/emitter.py` (builds `AllocationDirective` with cross-share-class FX conversion via
      `ShareClassFxMatrix` in `share_class_fx.py`).

## Phase 6 — PBMS

- [x] [CODE] P1. Venue-account aggregation view — `position-balance-monitor-service@16db8bb` / `cd25d7d`
      `v2/projections.py` `VenueAccountProjection` with per-`(venue, account_id)` position + fees aggregation.
- [x] [CODE] P1. Strategy + venue-account dual projections — same commit, `DualProjection` with sum-equality invariant
      checker emitting `VENUE_ACCOUNT_STRATEGY_SUM_DRIFT` on any divergence.
- [x] [CODE] P1. Fill reconciliation — `position-balance-monitor-service@16db8bb` `v2/attribution.py` `FillAttributor`
      (instruction_id → identity + client_order_id fallback).
- [x] [CODE] P1. Unity child-book position attribution — `position-balance-monitor-service@cd25d7d`
      `V2Fill.child_venue_id` + `VenueAccountProjection.by_child_venue` give per-book exposure inside the Unity wallet.

## Phase 7 — Risk-and-exposure-service

- [x] [CODE] P1. Venue-account pre-flight checks — `risk-and-exposure-service@7f9a1df` Layer 3
      (`run_layer3_venue_account_preflight`), `FourLayerGateOrchestrator` composes Layer 2 + Layer 3 with
      most-restrictive-wins precedence.
- [x] [CODE] P1. Margin simulation with haircuts — `risk-and-exposure-service@7f9a1df` / `a18bfbc` `v2/margin_sim.py`
      `simulate_margin_after_instruction` (VenueCapabilityV2 haircut + LTV + MarginSpec init/maint + NettingRule
      hedged-pair). `v2/greek_model.py` (`a18bfbc`) adds `PortfolioGreekModelRegistry` (DERIBIT_PM / SPAN / REG_T) —
      when `MarginSpec.portfolio_margin_greek_model` is set, greek IM replaces gross × init_pct.
- [x] [CODE] P1. Family-level limits — `risk-and-exposure-service@7f9a1df` Layer 2 preflight (`run_layer2_preflight`):
      daily loss / drawdown / per-family exposure cap with headroom-aware checks. Aggregate cross-family correlation cap
      landed in `v2/correlation_cap.py` (`a18bfbc`).
- [x] [CODE] P1. Kill switch coordination (multi-venue rules: delta-neutral exit default) — `v2/kill_switch_rules.py`
      `KillSwitchRulesEngine` (DELTA_NEUTRAL_EXIT default / DATA_STALE REDUCTIONS_ONLY / recon+exec dual-failure
      HUMAN_REQUIRED). 21/21 tests pass.

## Phase 8 — Features + ML

- [x] [CODE] P1. Feature group versioning + artifact registry emission — UAC `ArtifactMetadata` schemas (`c542b32`) +
      features-\* wiring (`d1f60c4`/`145bd17`/`c38f37e`). Every feature parquet emits an artifact_id + build_version.
- [x] [CODE] P1. Model versioning + artifact registry emission — `ml-inference-service@ab8b522` wires the same
      `ArtifactMetadata` contract for trained models; `ml-training-service` emits the artifact on training complete.

## Phase 9 — UI

- [x] [CODE] P2. Family-first navigation, category-as-filter — `unified-trading-system-ui@4195bba`/`0daef23`
      `lib/architecture-v2/` TS module mirrors UAC v2 enums (8 families / 18 archetypes / 8 allocator archetypes / Unity
      books / commercial).
- [x] [CODE] P2. 8 family dashboards + archetype/instance/config views + dependency tab — `/families` + 8 static routes
      `/families/[family]`. Catalog page has multi-select category filter.
- [x] [CODE] P2. Allocator UI — `/allocator` with 4 tabs (instances, directive history, shadow compare, MANUAL
      approvals).
- [x] [CODE] P2. Venue capability view + execution policy view — `/venues` (VenueCapabilityV2 table) +
      `/execution-policies` (ALLOW / REJECT / RESIZE / DEFER rows).
- [x] [CODE] P2. Unity dashboard — `/unity` (10 child books + turnover waiver + deposit refund progress bars).

## Phase 10 — Backtest runners

- [x] [CODE] P2. Group A (ML training) — `ml-training-service@d53c2ea` / `ed9456b` Group A backtest runner.
- [x] [CODE] P2. Group B (strategy) — uses benchmark fills — `strategy-service@aa3c6c0` `engine/backtest_v2/runner.py`
      `GroupBRunner`.
- [x] [CODE] P2. Group C (execution alpha) — measures alpha vs benchmark — `execution-service@f5eee2b1` scaffold in
      `backtest_v2/runner.py` `GroupCRunner`.

## Phase 11 — Strategy migration

- [x] [CODE] P1. Map existing 53 strategies to archetype + instance + config — `strategy-service@740f2ba` + `d2c9780`.
      58 `LegacyStrategyMapping` rows cover 17 of 18 archetypes (only `CARRY_BASIS_DATED` has no legacy row —
      dated-expiry futures basis was never implemented). 7 rows flagged `NEEDS_REVIEW` for operator decision (Drift
      perps x2, cross-exchange ML, cross_chain_sor meta-allocator, rel_vol archetype choice, staking library,
      omnichain_transfer infra). 18/18 migration tests pass.
- [x] [CODE] P1. Emit v1 configs; retire legacy naming — same commit. `load_legacy_strategies_into_registries()`
      deterministically produces a populated `StrategyInstanceRegistry` + `ConfigRegistry` with content-hashed v1 slots.
      Determinism test proves two loads produce identical content hashes.
- [x] [CODE] P2. Build remaining strategy instances to fill target universe (~240-250 v1, ceiling ~300-350) —
      `strategy-service@62721e7`. New `engine/strategies/v2/target_universe/` sub-package ships 240 `TargetInstanceSpec`
      rows covering all 18 archetypes, disjoint from legacy migration by construction. Combined total = 298 (58 legacy +
      240 target). `load_combined_instance_catalog()` is the single SSOT for "what strategies does the firm run?" Every
      row anchored to its archetype's "Supported venues / instruments" table in
      `codex/09-strategy/architecture-v2/archetypes/<archetype>.md`. 19 unit tests enforce slot-label parse fidelity,
      intra-catalog uniqueness, legacy disjointness, archetype coverage, no-Kraken regression, and deterministic
      content-hashing. QG green 59s.

## Success criteria

- All ~60 docs written + QG pass on PM repo
- Every archetype has a typed engine with tests
- Every instruction action has a handler with benchmark-fills contract
- All 53 legacy strategies mapped to archetype + instance + config
- UAC schema additions pass QG in all consumer repos
- UI navigates by family-first
- Kraken fully removed from codebase (grep returns zero matches)
- Docs wave: every family/archetype/axis/cross-cutting doc has "Not in this X" section

## Reference points for migration

- Legacy docs remain at `codex/09-strategy/{cefi,defi,sports,tradfi}/` and `codex/09-strategy/cross-cutting/` —
  referenced from MIGRATION.md, deleted only after each legacy doc's functionality is verified in v2
- Legacy code modules enumerated in MIGRATION.md with target archetype mapping
- e2e-testing configs enumerated with archetype assignment per strategy

## Related prior plans (partial overlap, do not duplicate)

- `strategy_docs_vs_system_audit_2026_04_15.plan.md` — closed gaps in codex/09-strategy docs vs backend implementations
- `identity_registry_and_shard_enrichment_2026_04_16.plan.md` — UAC strategy registry SSOT, unified TradingAccount
  model, SCE enforcement
- `consolidated_strategy_and_ui_2026_04_15.plan.md` — strategy lifecycle UI integration
- `autonomous_recovery_and_transfer_architecture_2026_04_16.plan.md` — G1-G5 recovery, transfer type router
- `strategy_system_citadel_master_2026_03_15.plan.md` (ai/) — prior citadel-grade master; superseded by v2 architecture
