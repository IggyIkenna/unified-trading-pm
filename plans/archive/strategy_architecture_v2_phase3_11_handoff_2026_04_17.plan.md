---
doc_type: plan
title: Strategy Architecture v2 — Phases 3-11 Handoff
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-17"
owner: iggy
started: 2026-04-17
depends_on: strategy_architecture_v2_2026_04_17.md
parent_docs: codex/09-strategy/architecture-v2/
locked_by: live-defi-rollout
locked_since: 2026-04-17
---

## Deferred work — migrated to: `plans/epics/strategy_master.md` — successor:

strategy_master (the active L2 epic owning strategy-service post-consolidation: engine + portfolio_allocator + risk +
position + pnl + the archetype engines). Content match verified — the residual action-handler/allocator-archetype/
Unity-adapter/MEV-router/shadow-mode items here are the exact domain strategy_master.md's "Owns" section declares.

# Strategy Architecture v2 — Phases 3-11 Handoff Plan

## Status

- **Phase 1 (docs)** — DONE (~60 docs, see parent plan).
- **Phase 2 (UAC schemas)** — DONE (commit `4bc83bc` on `live-defi-rollout`). Bybit removed from UAC itself (external/
  mocks retained per cassette parity); downstream Bybit removal still TODO.
- **Phases 3-11 (service implementation)** — PLANNED, not yet started. This doc is the handoff.

## Context for executing agents

- Import the v2 schemas via `unified_api_contracts.internal` facade:

```python
from unified_api_contracts.internal import (
    StrategyFamilyV2, StrategyArchetypeV2, ARCHETYPE_TO_FAMILY,
    AllocatorArchetype, AllocationDirective, StrategyEquityDirective,
    AccountInstruction, AccountActionV2,
    TradeInstruction, SwapInstruction, LendInstruction, BorrowInstruction,
    StakeInstruction, UnstakeInstruction, QuoteInstruction,
    TransferInstructionV2, BridgeInstructionV2, AtomicInstruction, CancelInstruction,
    AtomicLeg, AtomicExecutionMode, CompensationPolicy,
    StrategyInstanceIdentity, StrategyInstanceDefinition,
    VenueType, VenueCategoryV2, VenueCapabilityV2,
    CollateralRulesV2, LtvAndHaircut, MarginSpec, NettingRule,
    CommissionStructureV2, CommissionTier, CommissionStructureType,
    UnityChildVenue, UNITY_CHILD_BOOKS, unity_child_books_confirmed,
    HoldPolicy, ShareClass, VenueRoutingMode, StakingMethod, EdgeMethod,
    MevSubmissionMode, TransferType, KillSwitchReason,
    FillSource, BenchmarkFillMode, BacktestGroup,
    RiskGateLayer, RiskGateDecision, RiskGateResult,
    CompatibilityEntry, COMPATIBILITY_SEED,
)
```

- Every new/migrated code path MUST:
  - Pin artifact refs explicitly (`@v{N}`), never implicit-latest
  - Tag every event with the full identity tuple (family, archetype_id, archetype_build_version, strategy_instance_id,
    slot_version, config_hash, config_version, client_id, share_class)
  - Preserve batch=live code path (benchmark_fill contract in every algo)

- DO NOT delete the legacy `internal.domain.strategy_service.instruction.StrategyInstruction` dataclass — existing
  services still use it. Migration is incremental via shadow deployment; retire legacy after all consumers migrated.

## Phase 3 — Strategy-service refactor

Repo: `strategy-service`. Scaffold landed on `live-defi-rollout` at `strategy-service@ec4ea26`.

- [x] [CODE] P1. Introduce archetype engine factory keyed by `StrategyArchetypeV2` —
      `strategy_service/engine/strategies/v2/factory.py`, 18 entries.
- [x] [CODE] P1. Scaffold 18 engine classes under `strategy_service/engine/strategies/v2/{family}/{archetype}.py` (one
      fully wired — ML_DIRECTIONAL_CONTINUOUS — remaining 17 are stubs pending continuation work).
- [x] [CODE] P1. Implement `BaseArchetypeEngineV2` with: `on_tick`, `on_allocation_directive`, `on_kill_switch`,
      `on_restart`, `self_check`, `react_to_equity_change`, `emit_instructions` —
      `strategy_service/engine/strategies/v2/base.py`.
- [x] [CODE] P1. Instance registry reading `StrategyInstanceDefinition` — in-memory `StrategyInstanceRegistry` in
      `strategy_service/engine/strategies/v2/registry.py`; hand-written STRATEGY_REGISTRY list is NOT present in this
      repo, so no retirement needed here (UI still has its own `strategy-registry.ts` — that retirement belongs to Phase
      9).
- [x] [CODE] P1. Config registry with content-hash + monotonic version per slot — `ConfigRegistry` in `registry.py`
      (SHA-256 truncated to 16 hex per `codex/06-coding-standards/strategy-identity-versioning.md`).
- [x] [CODE] P1. Slot-label parser + validator matching grammar from
      `codex/06-coding-standards/strategy-identity-versioning.md` —
      `strategy_service/engine/strategies/v2/slot_label.py`. `SlotLabelParts` now exposes typed `venue_tokens` +
      `instrument_tokens` (split via UAC `split_scope_tokens` from `unified-api-contracts@2ccb356`) with a back-compat
      `scope_tokens` property. Covered by 4 dedicated tests (multi-venue, Unity sports, stat-arb basket, unknown-first
      rejection).
- [x] [CODE] P1. Emit instructions as `StrategyInstructionV2` variants (ML_DIRECTIONAL_CONTINUOUS emits
      `TradeInstruction`; other archetypes return `[]` until filled).
- [x] [CODE] P1. Subscribe to `AllocationDirective` events; rescale positions on delta —
      `BaseArchetypeEngineV2.on_allocation_directive` updates `target_equity` when
      `StrategyEquityDirective.strategy_instance_id` matches.
- [x] [CODE] P1. Fill in the other 17 archetype `on_tick` bodies — **17/17 implemented**. Phase 3 follow-up
      (`strategy-service@96aae04`) wired 6 (RulesDirectionalContinuous, CarryBasisPerp, YieldRotationLending,
      MarketMakingContinuous, VolTradingOptions, ArbitragePriceDispersion); Phase 3 fill (`strategy-service@05a916e`)
      added the remaining 11: MLDirectionalEventSettled (TradeInstruction, fractional Kelly on edge-vs-implied),
      RulesDirectionalEventSettled (TradeInstruction per fired rule), CarryBasisDated (AtomicInstruction LEADER_HEDGE
      spot+future), CarryStakedBasis (AtomicInstruction LEADER_HEDGE STAKE+LEND+PERP), CarryRecursiveStaked
      (AtomicInstruction ATOMIC_ON_CHAIN LEVERAGED_LENDING_LOOP), YieldStakingSimple (StakeInstruction),
      LiquidationCapture (AtomicInstruction ATOMIC_ON_CHAIN FLASH_LOAN), MarketMakingEventSettled (2× QuoteInstruction
      BET_BACK/BET_LAY), EventDriven (TradeInstruction HIGH urgency + time-box exit), StatArbPairsFixed
      (AtomicInstruction LEADER_HEDGE cointegrated pair + COINTEGRATION_BREAKDOWN kill), StatArbCrossSectional
      (AtomicInstruction SEQUENCED_WITH_PACING BASKET).
- [ ] [CODE] P1. Migrate 53 existing strategies to (archetype, instance, config) triples (deferred to Phase 11 per the
      plan's own structure).
- [x] [CODE] P2. Shadow mode runner — `strategy_service/engine/core/engine/v2_shadow_runner.py` hosts a per-env
      `V2EngineOrchestrator(shadow_mode=True)` (keyed by prod/paper/dev). Module-level helpers `register_v2_instance()`
      / `run_v2_on_tick()` / `apply_v2_allocation_directive()` / `apply_v2_kill_switch()` /
      `get_v2_shadow_orchestrator()` / `reset_v2_shadow_orchestrator()` expose the surface to the legacy
      `BaseStrategyManager` path. Shadow mode suppresses emission while recording each engine's output on
      `engine.emitted_instructions` for offline comparison. Two integration smoke tests in
      `tests/unit/engine/core/engine/test_v2_shadow_runner.py` prove register → tick → allocation directive → kill
      switch round-trips end-to-end.
- [x] [CODE] P2. Wire the v2 engine surface into the existing strategy-service — landed as
      `strategy_service/engine/strategies/v2/orchestrator.py` (`V2EngineOrchestrator` + `V2Subscription`) and
      re-exported alongside `TriggerRouter` from `strategy_service/engine/core/engine/__init__.py`. The legacy
      `BaseStrategyManager` can now call `run_v2_on_tick(...)` alongside its own decision flow without forwarding v2
      instructions to execution-service (shadow). Full production cut-over (shadow → dual-run → live) is explicit — the
      shadow runner never auto-transitions.
- [x] [CODE] P2. Split `slot_label.parse_slot_label.scope_tokens` into venue/instrument — **DONE**. UAC
      `split_scope_tokens` (`unified-api-contracts@2ccb356`, already on `origin/live-defi-rollout`) resolves venue
      tokens against the venue SSOT; strategy-service `SlotLabelParts` now carries `venue_tokens` and
      `instrument_tokens` as separate typed tuples. `scope_tokens` is retained as a back-compat property returning
      `venue_tokens + instrument_tokens`.

### Phase 3 commits

- `strategy-service@ec4ea26` on `live-defi-rollout` — scaffold 18 family engines + ML directional continuous
- `strategy-service@96aae04` on `live-defi-rollout` — 6 additional archetype engines + V2EngineOrchestrator + 10 new
  smoke tests
- `strategy-service@05a916e` on `live-defi-rollout` — 11 final archetype engines + v2_shadow_runner + 16 new tests
- Quality gates pass (53s, 7 codex violations within tolerance of 8). basedpyright clean on the v2 and core/engine
  sub-packages. 41 total unit tests pass under `tests/unit/engine/strategies/v2/` (35) +
  `tests/unit/engine/core/engine/` (2) + prior slot-label tests (4).

## Phase 4 — Execution-service polymorphic orchestrator

Repo: `execution-service`.

- [ ] [CODE] P1. 11 action handlers, one per `InstructionActionV2`
- [ ] [CODE] P1. Policy registry reading artifact-versioned `ExecutionPolicy` docs
- [ ] [CODE] P1. Algo library registration with mandatory `benchmark_fill()` method
- [ ] [CODE] P1. Venue-account pre-flight (Layer 3 of 4-layer risk model) consuming PBMS + `VenueCapabilityV2`
- [ ] [CODE] P1. ATOMIC handler with sub-modes: same-venue native, LEADER_HEDGE cross-venue, SEQUENCED_WITH_PACING
      basket, ATOMIC_ON_CHAIN DeFi composite
- [ ] [CODE] P1. `BenchmarkFillMode` implementations per action type (arrival_mid, twap_window, pool_mid_at_block, etc.)
- [ ] [CODE] P1. META_BROKER router for Unity with child-book attribution
- [ ] [CODE] P1. Unity TCP adapter:
  - Sidecar: Java Feed Connector (binary delivered by Unity)
  - Python bridge managing sidecar lifecycle (subprocess, health pings, reconnect)
  - Single TCP connection multiplexed across all strategies
  - All 3 sports (Soccer + Tennis + Basketball)
  - Bet placement, wallet sync, rollover tracking, turnover tracking for subscription waiver
- [ ] [CODE] P1. MEV router (Flashbots + MEV Blocker + Manifold; Bloxroute excluded)
- [ ] [CODE] P1. Cost-model artifact loader (`cost_model/*` registry)
- [ ] [CODE] P1. `AccountInstruction` orchestrator (non-benchmarked, operator-driven path)

## Phase 5 — Portfolio-allocator-service (new)

New repo: `portfolio-allocator-service`.

- [ ] [CODE] P1. 8 allocator archetype engines (FIXED, PNL_WEIGHTED, SHARPE_WEIGHTED, RISK_PARITY, KELLY, MIN_CVAR,
      REGIME_AWARE, MANUAL)
- [ ] [CODE] P1. Per-client instance registry
- [ ] [CODE] P1. Cadence scheduler (DAILY/HOURLY/WEEKLY/ON_EVENT)
- [ ] [CODE] P1. Guard rails (max_weight, min_weight, max_turnover, correlation_cap, family_diversification,
      category_diversification)
- [ ] [CODE] P1. Shadow mode (primary + shadow instance per client)
- [ ] [CODE] P1. Emits `AllocationDirective` events
- [ ] [CODE] P1. Reads NAVs + returns from PBMS, kill switches from risk-service
- [ ] [CODE] P1. Cross-share-class NAV conversion
- [ ] [CODE] P1. Audit log retention per directive
- [ ] [CODE] P1. Service scaffolding: ServiceBootstrap, Health API with data_freshness, typed config reloader, Secret
      Manager integration

## Phase 6 — PBMS (position-balance-monitor-service)

Repo: `position-balance-monitor-service`.

- [ ] [CODE] P1. Dual projection: strategy-instance view + venue-account view
- [ ] [CODE] P1. Sum-equality invariant check; emit `VENUE_ACCOUNT_STRATEGY_SUM_DRIFT` on violation
- [ ] [CODE] P1. Fill attribution: match (fill_id → instruction_id → strategy_instance_id)
- [ ] [CODE] P1. Unity child-book parse from Unity fill reports → child_venue attribution
- [ ] [CODE] P1. Venue-account balance reconciliation + freshness signal for risk-service
- [ ] [CODE] P1. Historical NAV series per strategy_instance_id for allocator consumption
- [ ] [CODE] P1. Cross-share-class NAV reporting helpers

## Phase 7 — Risk-and-exposure-service

Repo: `risk-and-exposure-service`.

- [ ] [CODE] P1. 4-layer risk model: Layer 2 pre-flight + Layer 3 venue-account pre-flight
- [ ] [CODE] P1. Margin simulation using `VenueCapabilityV2.collateral_rules` + `MarginSpec` (haircut + LTV +
      portfolio-margin greek model)
- [ ] [CODE] P1. Family-level limits (e.g., total vol-trading vega across all vol strategies)
- [ ] [CODE] P1. Instance kill switches with `KillSwitchReason` persistence
- [ ] [CODE] P1. Multi-venue kill switch rules (delta-neutral exit default; reductions-only on DATA_STALE)
- [ ] [CODE] P1. Recon-gate coordination with PBMS (require reconciliation freshness for Layer 2+3)
- [ ] [CODE] P1. Correlation-cap computation across strategies
- [ ] [CODE] P1. `RiskGateResult` response contract

## Phase 8 — Features + ML versioning wiring

Repos: `features-onchain-service`, `features-ohlc-service`, `features-sports-service`, `ml-training-service`,
`ml-inference-service`.

- [ ] [CODE] P1. Artifact registry emission on publish (`ARTIFACT_PUBLISHED` event)
- [ ] [CODE] P1. Content-hash + monotonic version per feature group
- [ ] [CODE] P1. Content-hash + monotonic version per model; model family naming per
      `codex/06-coding-standards/artifact-naming.md`
- [ ] [CODE] P1. Consumer-pin `@v{N}` resolution at feature/model fetch time
- [ ] [CODE] P1. Dependency graph (strategy config → model → feature groups) queryable via registry
- [ ] [CODE] P1. Attestations: emit `(model_version, feature_group_versions)` back on inference so they ride on
      `StrategyInstruction.attestations`

## Phase 9 — UI family-first navigation

Repos: `unified-trading-system-ui`, all 13 existing UIs.

- [x] [CODE] P2. Navigation restructure: family → archetype → instance → config. `unified-trading-system-ui@<phase-9>` —
      new routes `/services/research/strategy/families`, `/families/[family]`, `/allocator`, `/unity`, `/venues`,
      `/execution-policies` added; `STRATEGY_SUB_TABS` updated to surface them. `[family]` uses `generateStaticParams`
      so all 8 families are pre-rendered. The instance detail (layer 4 = config) still lives at `/catalog/[strategyId]`
      and will be moved under `/families/[family]/[archetype]/[instance]` in phase 11 once UAC
      `StrategyInstanceDefinition` rows exist.
- [x] [CODE] P2. 8 family dashboards. `FamilyGridClient` aggregates over `STRATEGY_CATALOG` via the legacy→v2 mapping
      (`legacyFamilyToV2`); `FamilyDashboard` renders per-family archetype cards + aggregated metrics + instance table.
      Family metadata (label, alpha source, short description, icon, accent colour, doc href, slug) lives in
      `lib/architecture-v2/families.ts`.
- [ ] [CODE] P2. Instance detail: 6 tabs (performance, risk, money ops, config, readiness, security) consume v2 identity
      tuple. **Deferred** — the existing `/catalog/[strategyId]` tabs already render performance / risk / money_ops /
      config / readiness / security, but still consume legacy `StrategyCatalogEntry`. Swap the props to
      `StrategyInstanceDefinition` in phase 11 migration.
- [x] [CODE] P2. Allocator UI (per-client instances, directive history, shadow comparison, MANUAL approval queue) —
      `/services/research/strategy/allocator` with 4 tabs (Instances, Directive history, Shadow vs primary, Approvals).
      Drives off `MOCK_ALLOCATOR_INSTANCES`, `MOCK_DIRECTIVE_HISTORY`, `MOCK_SHADOW_COMPARE`, `MOCK_APPROVAL_QUEUE` in
      `lib/mocks/fixtures/architecture-v2-fixtures.ts`; shape is locked to the allocator types in
      `lib/architecture-v2/allocator.ts` so the API can land with a straight data swap once phase 5
      portfolio-allocator-service is live.
- [x] [CODE] P2. Venue capability viewer (drives from UAC `VenueCapabilityV2`) — `/services/research/strategy/venues`
      renders a 5-venue comparison (Binance, Hyperliquid, Aave V3, Unity, IBKR) with LTV range, margin mode, max
      leverage, and commission-tier summary. TS view-model (`VenueCapabilityView`) mirrors the UAC dataclass structure
      pending the `/api/v1/venues/capabilities` gateway endpoint.
- [x] [CODE] P2. Execution policy viewer — `/services/research/strategy/execution-policies` lists 6 sample
      `(venue × action × condition)` rows with ALLOW / REJECT / RESIZE / DEFER decisions and policy version.
- [x] [CODE] P2. Unity dashboard — `/services/research/strategy/unity` with the 10 child books, avg commission KPI, 3
      sport chips, turnover-waiver progress bar against the
      $260k/month target, and deposit-refund progress bar against
      the $5.3M lifetime target. Commercial parameters
      are asserted in `unity.test.ts` so they cannot be silently drifted.
- [x] [CODE] P2. Strategy registry is auto-generated from UAC — `lib/strategy-registry.ts` is now flagged `@deprecated`
      in its JSDoc with instructions to import from `@/lib/architecture-v2` for taxonomy and to swap to the gateway API
      once phase 11 migration lands. v2 taxonomy (8 families, 18 archetypes, 8 allocator archetypes, 5 venue categories,
      Unity books, commercial terms, margin / commission / risk enums) is available from `@/lib/architecture-v2`.
      **Follow-up:** wire `unified-api-contracts/scripts/generate_ui_reference_data.py` to emit these enums into
      `lib/registry/generated.ts` and delete `lib/architecture-v2/enums.ts` (the only file that duplicates Python). The
      other architecture-v2 TS files are view-models, not Python mirrors.
- [x] [CODE] P2. Category filter as multi-select (not single-category routing) — catalog page now uses a
      `Set<StrategyCategory>` with an "All" chip that clears the selection. `aria-pressed` is set for screen readers;
      toggle behaviour keyed by `data-testid="category-filter-*"` for E2E.

## Phase 10 — Backtest runners

Repos: `strategy-service`, `ml-training-service`, `execution-service`.

- [ ] [CODE] P2. Group A runner (ml-training-service): dedicated VMs, walk-forward purged CV, emits versioned model
      artifacts
- [ ] [CODE] P2. Group B runner (strategy-service): uses `BenchmarkFillMode` fills (zero exec alpha); produces
      deployable config candidates
- [ ] [CODE] P2. Group C runner (execution-service): matching engine with realistic microstructure; measures
      `execution_alpha = matching_engine - benchmark`
- [ ] [CODE] P2. Same code path as live (batch=live); only fill source differs
- [ ] [CODE] P2. Determinism tests for benchmark_fill per algo
- [ ] [CODE] P2. Sports matching engine: bookmaker cost model (commission, no market impact at small size)

## Phase 11 — Strategy migration

- [ ] [CODE] P1. Audit existing 53 strategies; write archetype+instance+config for each
- [ ] [CODE] P1. Emit v1 `StrategyInstanceDefinition` rows into strategy-service registry
- [ ] [CODE] P1. Cut over live-traffic strategies via shadow-mode (parallel old+new for N days)
- [ ] [CODE] P2. Retire legacy `STRATEGY_REGISTRY` hand-written list
- [ ] [CODE] P2. Fill remaining target universe (~70-100 additional instances): paper-trade → promote on positive Group
      B Sharpe

## Phase 12 — Bybit downstream sweep

Workspace-wide.

- [ ] [CODE] P1. grep for `bybit|BYBIT|Bybit` outside UAC external mocks; remove from:
  - execution-service adapters
  - market-tick-data-service adapters
  - instruments-service reference data
  - credentials registry (unified-config-interface)
  - deployment-service scripts
  - all \*.md docs
- [ ] [CODE] P1. grep for `LSE|TSX` and verify those are only routed via IBKR (remove direct adapters if any)

## Phase 13 — Unity final details (user-assisted)

- [ ] [TBD] Pull books 9 and 10 from https://quant-portal.olesportsresearch.com/unity (user-authenticated)
- [ ] [CODE] P1. Update `UNITY_CHILD_BOOKS` in UAC with confirmed names + commissions
- [ ] [CODE] P1. Confirm commercial parameters: $10.8k deposit, $5.3M volume threshold, $2.6k/mo fee, $260k turnover
      waiver, 1x rollover

## Dependency graph

```
Phase 2 (UAC) ── DONE ──┐
                        ├──► Phase 3 (strategy-service)
                        ├──► Phase 4 (execution-service)
                        ├──► Phase 5 (portfolio-allocator)
                        ├──► Phase 6 (PBMS)
                        ├──► Phase 7 (risk-and-exposure)
                        └──► Phase 8 (features + ML)

Phases 3-8 must all be in place before:
    └──► Phase 9 (UI refactor, consumes all services)
    └──► Phase 10 (backtest runners — depend on strategy+execution)
    └──► Phase 11 (strategy migration — depends on strategy+execution+allocator+PBMS+risk)
    └──► Phase 12 (Bybit sweep — parallelizable with all phases)
    └──► Phase 13 (Unity final — requires user action to unblock)
```

## Success criteria

- Every service refactor passes `bash scripts/quality-gates.sh`
- `basedpyright` clean on every consumer repo after v2 schema adoption
- 53 legacy strategies mapped with zero live P&L disruption (shadow-mode parity within 5 bps for N days)
- Allocator emits its first live `AllocationDirective` to a shadow instance
- Unity TCP adapter passes integration test against Unity UAT
- First end-to-end fill with full identity tuple tagged from tick → instruction → fill → PBMS → allocator
- Bybit grep returns zero matches outside UAC external-provider cassettes

## Quickmerge convention

Every phase creates its own plan (or shares this one) and commits use:

```
feat(architecture-v2-phase-{N}): {description}
```

Branch: `live-defi-rollout` (current active feature branch per CLAUDE.md).
