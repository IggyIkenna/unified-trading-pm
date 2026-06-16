---
type: audit-result
title: Strategy archetype logic audit — separate from data-sanity mega audit + strategy MAP
epic: strategy_master
auditor: claude + operator
date: "2026-05-20"
status:
  ENRICHED 2026-05-21 — added §0 MAP (operator-requested full overview synthesised from 7 parallel research sub-agents)
  + §15-20 new dimensions + active plans inventory + master-strategy-plan deliverable. ACKED — operator authorised
  2026-05-20 round 5 to run TONIGHT in parallel with strategy/ml consolidation tail. Requires **Opus 4.7 (1M context)**
  — cross-archetype + cross-codebase scope demands the full graph in one session per
  `codex/06-coding-standards/model-tier-selection.md` opus-required tier.
instructions_ref: plans/audit/instructions/strategy_master_audit_instructions.md
updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P0
parent_epic: strategy_master
related_plans:
  - mega_audit_and_plan_beefup_progression_2026_05_20.md
  - trading_agent_service_architecture_unlock_2026_05_22.md
  - strategy_and_dart_master_SUPERSEDED_2026_05_21.md
  - mtds_mdps_master.md
  - per_client_isolation_and_venue_fanout_topology_2026_05_20.md
  - strategy_execution_contract_remediation_2026_05_20.md
  - phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md
  - api_keys_wallets_accounts_readiness_2026_05_10.md
  - cross_client_funds_isolation_retroactive_audit_2026_05_20.md
  - promote_workflow_may23_cli_path_2026_05_10.md
  - promote_workflow_post_cutover_ui_pipeline_2026_05_10.md
  - defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md
  - defi_recursive_borrow_archetypes_2026_05_10.md
  - strategy_repo_consolidation_2026_05_19.md
estimate_class: research
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 21.6
---

## Why this is a separate audit from the mega audit

The mega audit (`mega_audit_and_plan_beefup_progression_2026_05_20.md`) focuses on **data sanity** — contract pairs
between services, manifest correctness, expected_coverage, etc. It does NOT audit the strategy logic itself.

This issue captures the **strategy archetype logic audit** that must follow. The two are sequenced:

1. Mega audit (Phase A → B → C → D) lands first — gives clean data substrate
2. Strategy archetype audit runs against the now-clean substrate
3. Trading-agent-service architecture unlock (`trading_agent_service_architecture_unlock_2026_05_22.md`) gets the
   directive/PnL contracts wired
4. Strategy archetype audit findings flow into a Phase 2 (post-cutover) operational plan for the closed-loop allocator

## §0 — Map overview (the operator-requested "full map", 2026-05-21)

Synthesised from 7 parallel research sub-agents (code reality, codex SSOTs, active plans, data flow, axes/hard-rule
tables, treasury+execution, batch/paper/live). This section is the **substrate for the per-archetype audits** in §1-20
below and the foundation for the master strategy plan that this audit feeds.

### 0.1 Closed-set archetype inventory (53 archetypes)

SSOT: `unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype` (StrEnum, 53 values) +
`ARCHETYPE_TO_FAMILY` map. Code reality in
[`strategy-service/strategy_service/engine/strategies/v2/`](../../../strategy-service/strategy_service/engine/strategies/v2/):

| Archetype                                                                                                             | Code path                                                                                          | Status (2026-05-21)                                                       | Asset group(s)                 | Multi-leg?                   | May-23?                                 |
| --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------ | ---------------------------- | --------------------------------------- |
| `CARRY_STAKED_BASIS`                                                                                                  | `carry_and_yield/staked_basis.py` (699 LOC)                                                        | **Implemented but ALWAYS RETURNS [] — empty `VENUE_COLLATERAL_MATRIX`**   | DeFi+CeFi (hedge)              | 4-leg                        | YES (paper VM running since 2026-05-18) |
| `ARBITRAGE_PRICE_DISPERSION` (price variant)                                                                          | `arbitrage_structural/price_dispersion.py` (616 LOC)                                               | **Fully implemented**                                                     | DeFi+CeFi+Sports+Prediction    | 2-leg ATOMIC or LEADER_HEDGE | YES                                     |
| `ARBITRAGE_PRICE_DISPERSION` (funding-rate variant)                                                                   | same file                                                                                          | **Implemented BUT uncaught `raise ValueError` in per-pair loop** (P0-2)   | CeFi                           | 2-leg LEADER_HEDGE           | YES                                     |
| `CARRY_RECURSIVE_STAKED` (staking path)                                                                               | `carry_and_yield/recursive_staked.py` (408 LOC)                                                    | **Implemented**; no rebalance path                                        | DeFi                           | recursive N-cycle            | READY-TO-GO, toggle OFF                 |
| `CARRY_RECURSIVE_BORROW_LENDING_ONLY`                                                                                 | same file (shared)                                                                                 | **Stubbed — silently returns []** behind `staking_yield_enabled` gate     | DeFi                           | recursive                    | NO                                      |
| `CARRY_BASIS_PERP_INV` (renamed from `CARRY_RECURSIVE_BORROW_PERP_HEDGED` 2026-05-18)                                 | same file                                                                                          | **Stubbed — silently returns []**                                         | DeFi+CeFi                      | 3-leg                        | NO                                      |
| `ML_DIRECTIONAL_CONTINUOUS`                                                                                           | `ml_directional/continuous.py` (171 LOC)                                                           | **Fully wired — first end-to-end archetype**                              | CeFi/DeFi                      | 1-leg                        | post-cutover                            |
| `CARRY_BASIS_DATED_INV`                                                                                               | `carry_and_yield/dated_basis.py` (~150)                                                            | Scaffolded — NOT in factory registry                                      | CeFi+TradFi                    | 2-leg                        | NO                                      |
| `ML_DIRECTIONAL_REGIME`/`_ENSEMBLE`, `ML_MEAN_REVERSION_STAT_ARB`/`_PAIRS`                                            | `ml_directional/`, `ml_mean_reversion/`                                                            | Scaffolded (`on_tick` returns `[]`)                                       | CeFi                           | 1-2 leg                      | NO                                      |
| `ARBITRAGE_MEV_SANDWICH`                                                                                              | `mev/sandwich_theoretical.py` (147 LOC)                                                            | **NOT a live engine** — theoretical tracer; NEVER emits AtomicInstruction | DeFi                           | N/A                          | research only                           |
| `ARBITRAGE_MEV_BACKRUN`/`_JIT_LIQUIDITY`/`_LIQUIDATION_BUNDLE`                                                        | `mev/`                                                                                             | Scaffolded; mempool feed deferred (Bloxroute removed)                     | DeFi                           | bundle                       | NO                                      |
| `CARRY_YIELD_LENDING`, `CARRY_YIELD_LP_PROVISION`, `LIQUIDATION_CAPTURE`                                              | `carry_and_yield/`, `liquidation_capture.py`                                                       | Scaffolded                                                                | DeFi(+CeFi)                    | 1-2 leg                      | NO                                      |
| `DEFI_LP_CONCENTRATED`/`_POOL`/`_VAULT`                                                                               | `defi_lp/`                                                                                         | Scaffolded                                                                | DeFi                           | 1-2 leg                      | NO                                      |
| `VOL_*` (18 variants — IV/RV arb, term structure, dispersion, gamma scalp, LEAPS, ratio spreads)                      | `vol_trading/`                                                                                     | Scaffolded                                                                | CeFi (Deribit) + TradFi (CBOE) | options multi-leg            | NO                                      |
| `MARKET_MAKING_*` (8 variants)                                                                                        | `market_making/`                                                                                   | Scaffolded                                                                | CeFi+DeFi+Sports               | QUOTE                        | NO                                      |
| `STAT_ARB_PAIRS_FIXED`/`_CROSS_SECTIONAL`                                                                             | `stat_arb/`                                                                                        | Scaffolded                                                                | CeFi+TradFi                    | 2-leg                        | NO                                      |
| `RULES_DIRECTIONAL_*`, `ML_DIRECTIONAL_EVENT_SETTLED`, `EVENT_DRIVEN`, `ARBITRAGE_CROSS_DOMAIN_EVENT`                 | `rules_directional/`, `ml_directional/`, `event_driven.py`, `arbitrage_structural/cross_domain.py` | Scaffolded                                                                | various                        | 1-2 leg                      | NO                                      |
| `PORTFOLIO_MULTI_STRATEGY`/`_RISK_PARITY`/`_FACTOR_ALLOCATION`/`_TACTICAL_OVERLAY`                                    | `portfolio/`                                                                                       | Scaffolded — sleeve allocators with sub-strategies                        | Cross-category                 | N                            | post-cutover allocator-level            |
| `YIELD_STAKING_SIMPLE`, `YIELD_ROTATION_LENDING`, `CARRY_BASIS_DATED`, `CARRY_STAKED_BASIS_DATED`, `CARRY_BASIS_PERP` | `carry_and_yield/`                                                                                 | Scaffolded                                                                | DeFi(+TradFi+CeFi)             | 1-4 leg                      | NO                                      |

**Outliers / stale state**:

- `ArbitragePriceDispersionHierarchicalEngine` (~300 LOC, `arbitrage_structural/price_dispersion_hierarchical.py`) —
  implemented but NOT in factory registry. Cannot be instantiated via `ArchetypeEngineFactory.build()`. Status unknown.
- `__init__.py` docstring still reads "18 archetype engines (one fully wired)" — stale; should be updated in Phase 11
  consolidation tail.
- `V2ShadowRunner.shadow_mode=True` is the default. The flip to live for the colocated engine path has NOT happened —
  **no archetype is currently running in live mode via the Phase 3 colocated engine path**.
- `SportsArbDutchingEngine` (NOT in registry) sets `ARCHETYPE = StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` —
  collision risk if ever added via config mistake (P0-4).

### 0.2 Axes — closed sets + hard-rule tables (operator: "hard rule the venue universe, share class universe, leverage capabilities, instrument types")

10 axes inventoried. Per-axis SSOT status:

| Axis                                                    | SSOT location                                                                                                                                                                                                     | Status                                                                                                                                                                                                                                           | Gap                                                                                                                                      |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 1. Asset group × archetype validity                     | `internal.architecture_v2.enums` (53 archetypes) + `archetype_capability_matrix.py` (per-group ontology)                                                                                                          | **PARTIAL** — no machine-readable cross-product                                                                                                                                                                                                  | Need `ARCHETYPE_ASSET_GROUP_MATRIX: dict[StrategyArchetype, dict[MarketAssetGroup, Literal["SUPPORTED","PARTIAL","BLOCKED"]]]`           |
| 2. Venue universe per asset group                       | `archetype_capability_matrix.ASSET_GROUP_ONTOLOGY` frozensets + `venue_manifest/cefi.py`/`defi.py`/`tradfi.py`/`betting_sports.py`                                                                                | **INCONSISTENT** — CeFi frozenset missing aster, coinbase, upbit, extended, kraken, binance-futures, GMX, drift, pacifica-solana                                                                                                                 | Fix frozensets; add `venue → asset_group` reverse map                                                                                    |
| 3. Share class universe                                 | `canonical.crosscutting.share_class.ShareClass` (USDT/ETH/BTC) + `registry/client_share_classes.py` (1 demo seed)                                                                                                 | **THIN** — 3 classes; no GBP for Sports (settlement GBP); `USDC_CUTOVER_V1` perf-fee uses `share_class_id` strings unlinked to enum; potential collision with `internal/architecture_v2/enums.ShareClass` (btc_neutral/eth_neutral/usd_only/any) | Add GBP; reconcile collision; populate `CLIENT_SHARE_CLASS_REGISTRY`                                                                     |
| 4. Leverage capability per (venue, instrument_type)     | `cefi_margin_tiers.CEFI_MARGIN_TIERS` + `defi_reserve_params.py` (Aave V3/Compound V3/Morpho LTV) + `risk_rules/archetype.MaxLeverageTrigger`                                                                     | **GOOD (CeFi+DeFi)** BUT Kraken tiers missing; no `margin_mode: CROSS/ISOLATED/PORTFOLIO/UNIFIED` field; no unified cross-protocol DeFi lookup                                                                                                   | Add Kraken; add `margin_mode`; add `get_max_ltv(venue, collateral, debt)`                                                                |
| 5. Instrument type taxonomy                             | `registry.taxonomy.InstrumentTypeFamily` (SPOT/PERP/FUTURE/OPTION/LENDING_POSITION/BORROW_POSITION/LP_POSITION/STAKED_POSITION/SPORTS_MARKET/PREDICTION_MARKET)                                                   | **GOOD**                                                                                                                                                                                                                                         | Add `RESTAKING_POSITION` (EigenLayer/Karak/Symbiotic); add `CREDIT_POSITION` (Morpho isolated); disambiguate on-chain vs off-chain perps |
| 6. Collateral type + LTV + haircut per (venue, asset)   | `registry/venue_collateral.VENUE_COLLATERAL_MATRIX` (CeFi) + `defi_reserve_params.py` (DeFi)                                                                                                                      | **STALE FLAGS** — `STALENESS_FLAG_2026_05_07` on DERIBIT/BYBIT/OKX LST rows pending live-API probe; no Compound V3 haircuts; no GMX V2 per-market; Kraken spot missing                                                                           | Resolve staleness probes; unify lookup; add missing rows                                                                                 |
| 7. **Jurisdiction restrictions per (venue, client_id)** | **MISSING** — only inline comment in `_cefi.py` L680 ("Odum Research UK is on Extended's restricted territory list")                                                                                              | **MISSING — P0 PRE-LIVE GAP**                                                                                                                                                                                                                    | Create `registry/venue_jurisdiction_restrictions.py`                                                                                     |
| 8. Credential requirements per (venue, archetype)       | `capability_declarations/_cefi.py` per-venue `auth_scope` + `OperationDetail` + `signing_scheme` + `codex/04-architecture/interface-credential-convention.md`                                                     | **PARTIAL** — `config_secret_field` empty for most venues; no closed-set `archetype → required_credential_types`; Hyperliquid wallet-based (EIP-712 agent key) not "api_key"                                                                     | Populate `config_secret_field`; add per-archetype credential type table                                                                  |
| 9. Treasury vs trading wallet split per asset_group     | `internal.domain.account.WalletRole` (TREASURY/TRADING/RESERVE) + `internal.domain.execution_service.transfer_types.WalletType` (FUNDING/TRADING/SPOT/UNIFIED/ON_CHAIN) + `VENUE_WALLET_CAPABILITIES` (CeFi-only) | **GOOD CeFi; PARTIAL DeFi (codex prose only); MISSING TradFi**                                                                                                                                                                                   | Extend `VENUE_WALLET_CAPABILITIES` to DeFi+TradFi; add `TREASURY_MODEL_BY_ASSET_GROUP` constant                                          |
| 10. Risk parameters per archetype                       | `risk_rules/archetype.ARCHETYPE_RULES` (12 rules × 2 archetypes only) + venue/account/client/asset_group/global/strategy_family modules                                                                           | **THIN COVERAGE** — only `CARRY_STAKED_BASIS` + `ARBITRAGE_PRICE_DISPERSION` have full rule tuples; 51 archetypes uncovered; `ARCHETYPE_CONCENTRATION_MULTIPLIER` 10/53 seeded                                                                   | Extend `ARCHETYPE_RULES` to all 53 archetypes                                                                                            |

**Proposed master-strategy-plan hard-rule tables (8 — all SSOT in UAC)**:

1. `ARCHETYPE_ASSET_GROUP_MATRIX` (cross-product validity) — **NEW**
2. `VENUES_BY_ASSET_GROUP` (fix inconsistency) — extend existing
3. `CLIENT_SHARE_CLASS_REGISTRY` (production clients) — extend existing
4. `VENUE_LEVERAGE_CAPS` with `margin_mode` field — extend `cefi_margin_tiers.py`
5. Unified DeFi+CeFi collateral lookup `get_max_ltv(venue, collateral, debt) -> Decimal` — bridge function
6. `VENUE_JURISDICTION_RESTRICTIONS` — **NEW (P0)**
7. `VENUE_CREDENTIAL_REQUIREMENTS` — extend `venue_manifest`
8. `TREASURY_MODEL_BY_ASSET_GROUP` — **NEW**

### 0.3 Strategy service post-consolidation map

Consolidation (`strategy_repo_consolidation_2026_05_19.md`, 94% done, Phase 11 stale-ref cleanup in progress) merged:

- `risk-and-exposure-service` → [`strategy_service/risk/`](../../../strategy-service/strategy_service/risk/)
- `position-balance-monitor-service` →
  [`strategy_service/position/`](../../../strategy-service/strategy_service/position/)
- `pnl-attribution-service` → [`strategy_service/pnl/`](../../../strategy-service/strategy_service/pnl/)

**Shared infrastructure**:

| Component                   | Path                                         | Purpose                                                                                 |
| --------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------- |
| `BaseArchetypeEngineV2`     | `engine/strategies/v2/base.py`               | ABC; `on_tick()` contract; dust basket + reward attribution hooks                       |
| `ARCHETYPE_ENGINE_REGISTRY` | `engine/strategies/v2/factory.py`            | `dict[StrategyArchetype, type[BaseArchetypeEngineV2]]` (28 entries)                     |
| `_params.py`                | `engine/strategies/v2/_params.py`            | `decimal_param`/`int_param`/`str_param`/`float_param` fail-soft helpers                 |
| `AllocationSizer`           | `engine/strategies/v2/allocation_sizer.py`   | Per-client fan-out via UTL `AllocationEngine.allocate_per_client()`; drawdown gate      |
| `GCSFeatureProvider`        | `engine/core/gcs_feature_provider.py`        | Reads `gs://{features-onchain-bucket}/by_date/day={}/feature_group={}/features.parquet` |
| `V2EngineOrchestrator`      | `engine/strategies/v2/orchestrator.py`       | Shadow vs live; fan-out ticks; wraps `AllocationSizer`                                  |
| `V2ShadowRunner`            | `engine/core/engine/v2_shadow_runner.py`     | Legacy-path bridge; `shadow_mode=True` default                                          |
| `LeveragedLegController`    | `engine/strategies/v2/leveraged_leg.py`      | Multi-leg rebalancing via `LegPortfolioState`                                           |
| `PortfolioAllocatorService` | `portfolio_allocator/service.py`             | Per-client allocation; `AllocationGateDeniedError` fail-loud                            |
| `ShareClassFxMatrix`        | `portfolio_allocator/share_class_fx.py`      | Hub triangulation (USDT/USD) for cross-share-class FX                                   |
| `TreasuryMonitor`           | `position/core/treasury_monitor.py`          | Treasury vs trading wallet; emits `TREASURY_LOW`/`TREASURY_HIGH`                        |
| `StrategySupervisor`        | `engine/core/colocated_engine.py`            | One per (archetype × shard) VM; `MarkPriceAggregator`; `ClientAdmissionController`      |
| `archetype_defaults.py`     | `engine/strategies/v2/archetype_defaults.py` | Kelly fractions by risk tier; `V1_ARCHETYPES_IN_SCOPE` frozenset                        |
| PnL orchestrator            | `pnl/engine/orchestrator.py`                 | Per-instrument shard-level isolation; emits `StrategyPnlStreamEvent`                    |

**Duplication candidates** (5 prioritised; consolidation targets):

1. `accepted_perp_collateral()` call pattern identical in `staked_basis.py` + `recursive_staked.py` → shared
   `_resolve_lst_perp_structure(cfg)`
2. `StrategyPnlStreamEvent` zero-stub emission boilerplate duplicated in `staked_basis.py` + `price_dispersion.py` →
   `_emit_zero_pnl_stub()` on `BaseArchetypeEngineV2`
3. Funding-rate vs price-dispersion sizing (`stake_fraction * target_equity / mid_price`) duplicated twice in
   `price_dispersion.py`
4. `ArbitragePriceDispersionHierarchicalEngine` vs `ArbitragePriceDispersionEngine` — extract `_rank_venues()` shared
5. `TransferHandler` (instruction-driven) vs `TransferCoordinator` (event-driven) — two parallel transfer adapter
   hierarchies; neither calls the other; both will duplicate CeFi withdrawal logic once CCXT stubs wired

**P0 silent-failure risks** (5 prioritised):

1. **`staked_basis.py` always returns []** — `_derive_structure()` returns `None` when
   `cfg.lst_asset not in accepted_perp_collateral(cfg.perp_venue)`. Current `VENUE_COLLATERAL_MATRIX` has NO venue
   accepting any LST as perp margin. Result: passes unit tests, never produces a trade on real or paper infra. Mock-test
   instruction: patch `strategy_service.engine.strategies.v2.carry_and_yield.staked_basis.accepted_perp_collateral` to
   return `frozenset(["stETH"])`.
2. **Funding-rate-dispersion `raise ValueError`** in per-pair emission loop — single stale venue → aborts all remaining
   pairs. Violates `codex/04-architecture/shard-level-failure-isolation.md`. Should be `continue` with `logger.warning`.
   Price-dispersion path does NOT have this bug.
3. **`CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_BASIS_PERP_INV` silent stubs** — registered, `staking_yield_enabled`
   gate silently returns `[]`. Misconfigured client → "silent healthy" paper trade with no activity.
4. **`SportsArbDutchingEngine` ARCHETYPE collision** — uses `ARBITRAGE_PRICE_DISPERSION` enum value; if ever added to
   registry via config mistake, shadows primary engine.
5. **`StrategyPnlStreamEvent` emits zeros workspace-wide** — `pnl_realized=Decimal("0")`, `pnl_unrealized=Decimal("0")`,
   `TODO(post-cutover)` comments in both May-23 archetypes. Trading-agent-service allocator gets valid-looking zero-PnL
   events. **Mock-tests must not assert on PnL stream values for correctness.**

### 0.4 Data flow into strategy (MTDS → MDPS → features → ML → strategy)

Pipeline: **instruments-service** (reference) → **MTDS** (raw ticks) → **MDPS** (candles) → **features-service**
(`onchain/`, `delta_one/`, `volatility/`, `sports/`, `cross_instrument/`, `multi_timeframe/`, `calendar/`, `commodity/`)
→ **ml-service** (optional) → **strategy-service**.

**MTDS data_types** (closed set, ~30+):

- **CeFi**: `trades`, `book_snapshot`, `liquidations`, `ohlcv_1m`, `funding_rate`/`derivative_ticker`, `options_chain`,
  `futures_chain`, `perpetual`
- **DeFi**: `lst_yields`/`lst_rates`, `lending_indices`, `dex_pools`/`swap`/`liquidity`, `oracle_prices`,
  `staking_yields`/`eigenlayer_rewards`, `risk_params`, `rewards`, `flash_loan_events`, `perp_funding`, `position_data`,
  `vault_share_price`, `governance_events`, `bridge_events`, `token_transfers`, `mev_events`, `liquidation_events`,
  `native_staking_rates`, `solana_defi`, `gas_fees`, `hedge_ratio_snapshot`, `strategy_decision_context`,
  `feature_observation_snapshot`
- **TradFi**: `trades` (Databento CME), `tbbo` (OPRA), `ohlcv_1m`/`ohlcv_15m` (Barchart + Yahoo VIX), `options_chain`
  (OPRA), `futures_chain` (CME), `energy_data` (EIA)
- **Sports**: `ODDS_SNAPSHOT`, `ODDS_MOVEMENT`, `FIXTURES`, `FIXTURE_LINEUPS`, `FIXTURE_EVENTS`, `FIXTURE_STATS`,
  `FIXTURE_PLAYER_STATS`, `ODDS_ARBITRAGE`
- **Prediction**: `trades`, `book_snapshot`, `prediction_canonical_question_group`, `MARKET_LIFECYCLE`

**Per-archetype data dependency** (May-23 archetypes + ML reference):

| Archetype                                   | MTDS data_types                                                                                                                                                                    | features streams                                                                                                                                                                                                                                                            | ML outputs                                      | Required vs optional                                                                                      |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `carry_staked_basis`                        | `(defi,lst_yields)`, `(defi,lending_indices)`, `(defi,risk_params)`, `(defi,rewards)`, `(defi,flash_loan_events)`, `(defi,perp_funding)`, `(cefi,funding_rate)`, `(cefi,ohlcv_1m)` | `lst_staking_yields → staking_apy_bps`, `aave_lending_rates → lending_rate_apy_bps`, `aave_utilization`, `aave_risk_params → health_factor`, `aave_rate_impact`, `onchain_regime`, `defillama_tvl`; optional `flash_loan_availability`, `eigen_rewards`, `protocol_rewards` | optional `MLPrediction` entry-timing gate       | REQUIRED: `staking_apy_bps`, `funding_rate_apy_bps`; OPTIONAL: `usdc_idle_yield_apy_bps`, `health_factor` |
| `arbitrage_price_dispersion` (price)        | `(cefi,ohlcv_1m)` per venue; `(defi,dex_pools)`/`(defi,swap)` for DEX legs                                                                                                         | `cross_venue_spreads → mid_price_{venue}`; `onchain_regime`; `liquidation_band_prediction` (optional)                                                                                                                                                                       | optional (hierarchical variant uses)            | REQUIRED: `mid_price_{venue}` for ≥2 venues                                                               |
| `arbitrage_price_dispersion` (funding-rate) | `(cefi,funding_rate)` for each of 7 candidate venues; `(cefi,ohlcv_1m)` for mid                                                                                                    | `cross_venue_spreads`; per-venue funding feeds                                                                                                                                                                                                                              | optional                                        | REQUIRED: `funding_rate_{venue}` for ≥2 venues                                                            |
| `ml_directional_continuous`                 | `(cefi,ohlcv_1m)`, `(cefi,book_snapshot)`, `(cefi,trades)`, `(cefi,liquidations)`, `(cefi,funding_rate)`                                                                           | `technical_indicators`, `moving_averages`, `oscillators`, `volatility_realized`, `momentum`, `microstructure`, `volume_flow`, `liquidation_clusters`, `liquidation_band_prediction`, `order_flow_inference`                                                                 | `MLPrediction` (swing_high/swing_low, REQUIRED) | ML prediction is the primary signal                                                                       |

**ML services (post-consolidation 2026-05-20)**: repo `ml-service/` (do NOT reference legacy `ml-inference-service` /
`ml-training-service`). Models: swing-high/low classifiers (LightGBM/XGBoost/CatBoost/Ensemble), sports
(CLV/xG/HT_delta), cross_venue_spread. Output: `MLPrediction` (UAC
`unified_api_contracts.internal.domain.ml.schemas.MLPrediction`). Wiring: PubSub `model-promotions-{env}` →
`CascadeSubscriber` in strategy-service → injected as `MLPrediction`. Freshness SLA: `ml-inference-api` max_age=120s,
criticality=critical → blocks signal on stale ML. Artifact path:
`gs://ml-models-{category}-central-element-323112/models/{family}/{exp_id}/model.joblib`. Hot-reload 7d default.

**`available_at` + freshness**: per-row write-time stamping via `StreamingParquetWriter(strict=True)` +
`ManifestWriter.record_captured()`. **Never** derived at read-time (HARD RULE). Lookahead-bias guard:
`LookaheadBiasError.assert_no_lookahead(...)` driven by `FEATURE_REQUIRED_INPUTS` DAG. Per-source freshness from
`internal/reference/data_freshness.py` `ALL_FRESHNESS_CONTRACTS`.

### 0.5 Decision-making logic per archetype

Operator-asked: **"how do we decide what the best funding rate is to ARB?"** + **"how we weight our stuff across coins
across venues"**.

**`carry_staked_basis` decision**:

- Entry: `net_carry = f*(staking_apy_bps + funding_rate_apy_bps) + (1-f)*usdc_idle_yield_bps >= entry_bps` (default 200
  bps)
- Exit: `<= exit_bps` (default 50 bps)
- Structure: `_derive_structure()` → `accepted_perp_collateral(cfg.perp_venue)` (currently always empty)
- Sizing: `stake_fraction = 1.0` hardcoded post-2026-05-05 (LST IS the perp margin; SPLIT_STAKE deleted)
- Hedge ratio (Phase 6B DYNAMIC): `eth_qty × lst_native_rate_now × (1 - margin_haircut)` via
  `compute_dynamic_hedge_ratio()`; staleness guard 300s; last rebalance rate persisted
- Neutrality: `target_net_delta = 0.0`; Phase 6B rebalances within `peg_drift_threshold_bps = 25`
- 4-leg sequence: SWAP(USDC→ETH) + STAKE(ETH→LST) + TRANSFER(LST→perp venue) + TRADE(short perp) via
  `AtomicExecutionMode.LEADER_HEDGE`

**`arbitrage_price_dispersion` (price)**: read `mid_price_{venue}` for all `candidate_venues` → cheapest buy / most
expensive sell → trigger when `(sell-buy)/buy*10000 - cost_bps >= dispersion_bps` (default 30 bps) → size =
`target_equity * stake_fraction / buy_mid` → LEADER_HEDGE with `hedge_deadline_ms=5000`, `CLOSE_LEADER_IF_HEDGE_FAILS`
compensation; abort if `abort_on_adverse_move_bps` breached; max 10 concurrent.

**`arbitrage_price_dispersion` (funding-rate) — the "how to pick best funding rate to ARB" answer**:

- Read `funding_rate_{venue}` + `mid_price_{venue}` per venue-universe (7 candidate CeFi perp venues:
  Binance/Bybit/OKX/Deribit/Hyperliquid/Aster/Kraken)
- `PairSelectionMode` (closed set): `single_best` (top long×short pair by net spread minus costs) | `top_k` (top K
  configurable) | `all_above_threshold` (every pair where spread > min_edge)
- Filters: `sign_match_filter` (oppositely-signed funding pairs only) + `min_spread_filter` (gross > min_edge_bps) +
  `VolCapClampConfig` vol-cap clamp (caps notional when `realized_vol_20` high)
- Sizing: `target_leverage = 5.0` (vs `1.0` for price variant); per-leg notional =
  `target_equity * stake_fraction * target_leverage / mid_price`
- Emit long+short `TradeInstruction` pair with `LEADER_HEDGE`

**`ml_directional_continuous`**: read `predictions` dict (injected from PubSub via `CascadeSubscriber`) → pick
max-confidence prediction → emit `TradeInstruction` sized by `AllocationSizer.size()` if
`confidence > confidence_threshold` → direction from prediction sign (1=breakout=long, -1=reversion=short).

**Cross-venue + cross-coin weighting**:

- Per-archetype: `venue_universe` config field in `__init__`; iterated in `on_tick`
- Per-asset/coin: `AllocationSizer` via `AllocationEngine.allocate_per_client()` reads share-class config +
  per-archetype Kelly fractions from `archetype_defaults.py`
- Cross-archetype: `PortfolioAllocatorService` via hub-triangulation (USDT/USD) `ShareClassFxMatrix` for
  cross-share-class FX

### 0.6 Treasury wallet vs trading wallet (operator explicit focus)

**Two parallel concept hierarchies** (rationalisation needed in master strategy plan):

- **Fund-admin rail** (`internal.domain.account.WalletRole`): `TREASURY` | `TRADING` | `RESERVE`
- **Execution-side rail** (`internal.domain.execution_service.transfer_types.WalletType`): `FUNDING` | `TRADING` |
  `SPOT` | `UNIFIED` | `ON_CHAIN`

**Per-asset_group split**:

| Asset group | Treasury concept                                                                                                    | Trading concept                                   | Sweep initiator                                                                                   | Hot-reload path                                                                                                 |
| ----------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| DeFi        | **Per-share-class Copper Vault** (USDC/ETH/SOL/BTC), 20% AUM target; `TreasuryConfig.reserve_pct` 10% min / 30% max | Per-strategy, per-chain hot wallets, 80% AUM      | strategy-service `TreasuryMonitor` (watches Copper balance; emits `TREASURY_HIGH`/`TREASURY_LOW`) | `gs://wallet-config-{pid}/{chain_env}/wallet_provisioning.json` via `custody_config_from_wallet_provisioning()` |
| CeFi        | Exchange funding/spot account                                                                                       | Trading sub-account (Bybit=UNIFIED single-wallet) | `TransferHandler.auto_funding_to_trading()` — **CCXT wiring is logged stub** ("not yet wired")    | `VENUE_WALLET_CAPABILITIES` registry                                                                            |
| Sports      | Single bookmaker balance (no split)                                                                                 | same                                              | —                                                                                                 | per-venue config                                                                                                |
| TradFi      | UNIFIED broker (no live wallet architecture today)                                                                  | same                                              | —                                                                                                 | TBD                                                                                                             |
| Prediction  | On-chain USDC wallet                                                                                                | same                                              | —                                                                                                 | Copper or local key                                                                                             |

**Transfer pathway inventory** (10 paths):

| Transfer                                            | From                    | To                        | Speed                           | Cost                                   | Reconciler                                   | Failed path                                                                              |
| --------------------------------------------------- | ----------------------- | ------------------------- | ------------------------------- | -------------------------------------- | -------------------------------------------- | ---------------------------------------------------------------------------------------- |
| CEX_INTERNAL (spot→futures)                         | Funding                 | Trading sub-account       | sync instant                    | zero                                   | `CEX_INTERNAL_TRANSFER_COMPLETED` event      | FAILED; caller retries                                                                   |
| CEX_WITHDRAWAL                                      | CEX                     | external on-chain         | async min-hrs                   | hardcoded `_WITHDRAWAL_FEES` table     | `TRANSFER_CONFIRMED` event + PENDING         | `TRANSFER_FAILED`; no auto-retry                                                         |
| CUSTODY_TRANSFER / ON_CHAIN                         | Copper/KMS hot wallet   | on-chain                  | sync (poll 1s×30)               | gas (21K @ 30 gwei STUB)               | `CopperCustodyProvider` polls status         | `SignedTransaction.error`; 30s timeout                                                   |
| BRIDGE (cross-chain)                                | EVM/Sol                 | other chain               | async 5-30 min                  | protocol-specific                      | BridgeConnector (Socket API v2)              | NOT_IMPLEMENTED for `TransferHandler._execute_bridge_transfer`; HL-specific bridge works |
| HL USDC bridge                                      | Arbitrum                | HL account                | async ~300s                     | gas (approve+sendDeposit)              | `BridgeTxResult` + `get_bridge_pending()`    | Exception → `success=False`                                                              |
| DeFi same-chain (Aave supply/borrow/repay/withdraw) | hot wallet              | protocol                  | sync tx                         | gas 200K-300K via `DefiCostAggregator` | Manifest record_captured/record_failed       | `classify_venue_error()` → FAIL/RETRY/SKIP                                               |
| Treasury→trading sweep                              | Share-class treasury    | per-strategy hot wallet   | sync on-chain                   | gas                                    | `TREASURY_REBALANCE_NEEDED` event            | `TRANSFER_INITIATED → TRANSFER_FAILED`                                                   |
| SUBACCOUNT_MOVE                                     | Binance/OKX sub-account | same exchange sub-account | sync instant                    | zero                                   | `TransferCoordinator._SubaccountMoveHandler` | `SUBMITTED`; no confirmation poll                                                        |
| TradFi (ACH/wire)                                   | —                       | —                         | —                               | —                                      | **NOT YET IMPLEMENTED**                      | —                                                                                        |
| PnL settlement (trading→treasury)                   | hot wallet              | treasury                  | strategy-driven on TREASURY_LOW | gas                                    | event bus                                    | deleverage → unwind → transfer                                                           |

**Custody integration**:

- `CLOUD_KMS_ENCRYPTED` — **SHIPPED** at execution-service@`d45d24b4`. 5 asset_group × wallets-prod + wallets-staging
  KeyRings in asia-northeast1, 90-day auto-rotation. Default May-23.
- `COPPER_MPC` — **SHIPPED**. 7 env × venue combos: DeFi (all EVM) + non-Binance CeFi
  (Bybit/OKX/Deribit/Kraken/Aster/HL). HMAC-SHA256. 30s timeout. June-1 flip.
- `CEFFU` — **STUB ONLY**. Constructor wired; all async methods raise `NotImplementedError("CEFFU API spec pending")`.
  **HARD BLOCKER for Binance perp hedge leg** of every DeFi archetype. June-1 target. Blockers: REST endpoints, auth
  header names, sandbox URL, sub-account model — operator-action-required.

**Cross-client isolation enforcement (HARD RULE — 3 layers)**:

1. **UAC schema (construction)**: `TransferIntent` validates `source.client_id == dest.client_id` →
   `CrossClientTransferForbiddenError`
2. **strategy-service emit (Phase E.3)**: `IntraClientRebalanceCoordinator` — **NOT YET SHIPPED**
3. **execution-service consume**: `TransferCoordinator.validate_intent()` → `CrossClientTransferForbiddenError`; also
   `isolation_policy.assert_client_allowed()` via process-level `CLIENT_ID`

### 0.7 Batch vs paper vs live (HARD RULE: Batch = Live)

**Mode taxonomy** (4 closed values):

| Mode             | Scope                                                      | Fills                                                                               | Data source                                           | Risk gate                                                           | Monitoring                                |
| ---------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------- | ----------------------------------------- |
| batch            | historical replay                                          | Benchmark (oracle, zero slippage) or DEXFillModel (AMM constant-product)            | Pre-computed GCS parquets via `_generate_batch_ticks` | None — research only                                                | None required                             |
| paper (paper_1d) | live data, no capital                                      | Tenderly fork on mainnet state (real slippage / real EVM gas) or benchmark fallback | Live GCS feature fetch                                | Sharpe/Calmar gate vs backtest; ≥7d paper before live               | Full event archive; DART DartThreeWayView |
| live_early       | real capital, Copper/KMS custody, manual gate first 3 days | Real chain via `execution_provider=copper`                                          | Same as paper                                         | ≥7d paper + Sharpe gate + pre-flight; operator types "CONFIRM LIVE" | ManualTradeGateDialog every fill days 1-3 |
| live_full        | real capital, no manual gate                               | Same as live_early                                                                  | Same                                                  | post-cutover only                                                   | post-cutover only                         |

Valid May-23 transitions: `CANDIDATE → PAPER_1D → LIVE_EARLY` only. `LIVE_FULL` post-cutover.

**Legitimate code-path differences (HARD RULE = only 3)**:

1. Tick source (batch = pre-computed GCS; paper/live = live GCS feature fetch at `datetime.now(UTC)`)
2. Execution provider (`benchmark` / `tenderly` / `copper`) — `_execute_instruction()` dispatches; strategy output
   identical
3. Continuous vs replay loop (batch iterates fixed list; paper/live `while True: await asyncio.sleep(tick_interval)`)

**Mode-leak bug hide locations (5 — audit dim §18)**:

1. `colocated_engine.py` L1253-1256 — Tenderly fork time advancement gated on `execution_provider`; structurally fragile
2. **`execution_service/engine/modes/batch/` vs `live/` split** — separate `factory.py`, `orchestrator.py`, `router.py`.
   **No automated test asserts both paths produce same `CanonicalFill` schema**
3. `_load_features_for_date` empty-features silent passthrough — both modes emit `{}` and proceed; not manifested →
   invisible
4. `OperationalMode.MANUAL` in `manual_pending_queue.py` — legitimate post-decision gate (NOT batch=live violation)
5. `features["available_trading_capital_usd"]` sizing divergence — batch starts at initial_capital and depletes via gas;
   live is real. Expected, but not documented.

**QG STEP 5.77 audit gap**: writegate plan declares it active workspace-wide, but **no corresponding script found** in
`quality-gates-base/`. If non-existent, mode-conditional branches in consumer code are not mechanically blocked.

**MinimalCandidateManifest** (UAC `internal/domain/strategy_service/candidate_manifest.py`):

| IN (May-23)                                                                                                                                                                                                                                                                                                              | OUT (post-cutover; all `None`)                                                                                                                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `manifest_id` (UUID4), `strategy_instance_id`, `version_id`, `archetype: StrategyArchetype`, `config_json: dict`, `score_vector: GroupBMetrics` (Sharpe/Calmar/max_drawdown/win_rate/backtest_days/total_return), `target_phase: StrategyMaturityPhase` (PAPER_1D/LIVE_EARLY only), `created_at`, `created_by`, `reason` | `pinned_shas: dict[str, str]` (git SHAs all repos), `model_refs: list[ModelRef]` (ML artifact refs — May-23 archetypes are rule-based), `features_manifest_version: str` (writegate Phase 6.x incomplete for 3 services), `chain_rpc_pins: dict[str, str]` (pinned RPC URLs) |

Named successor for OUT enrichment: `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`.

### 0.8 Execution flow handoff (strategy → execution)

**Strategy emits** `StrategyInstruction`/`ExecutionInstruction` (UAC) → GCS `data_type="strategy_instructions"` via
`StrategyManifestRecorder`. **Execution reads** via `execution_service/strategy_instructions/gcs.py`
`download_instructions_df()` using `ExecutionManifestRecorder`. Both sides use 3-state manifest emission.

**HandlerRegistry dispatch** (`engine/routing/handler_registry.py` — 12 OperationTypes):

| OperationType                | Handler                                  | Asset group                      |
| ---------------------------- | ---------------------------------------- | -------------------------------- |
| `TRADE`                      | `TradeHandler`                           | CLOB (CeFi + DeFi perp HL/Aster) |
| `SWAP`                       | `SwapHandler`                            | DEX                              |
| `LEND`/`WITHDRAW`            | `LendHandler`                            | DeFi (Aave/Morpho)               |
| `BORROW`/`REPAY`             | `BorrowHandler`                          | DeFi                             |
| `STAKE`/`UNSTAKE`            | `StakeHandler`                           | DeFi (Lido/EtherFi)              |
| `TRANSFER`                   | `TransferHandler`                        | All                              |
| `FLASH_BORROW`/`FLASH_REPAY` | `FlashLoanHandler`                       | DeFi                             |
| `CLAIM_REWARD`/`SELL_REWARD` | `ClaimRewardHandler`/`SellRewardHandler` | DeFi                             |
| `BET`/`SPORTS_EXCHANGE`      | `SportsHandler`                          | Sports                           |
| `PREDICTION_BET`             | `PredictionBetHandler`                   | Prediction                       |

**Fill report path**: manifest recorder + event bus. PnL realization per-fill (NOT per-cycle aggregated).
`DefiCostAggregator` (`matching_engine/defi/cost_aggregator.py`) models
`gas_cost_usd + flash_premium_usd → FillAttributionContext.fee_amount_modelled`. Slippage via
`MatchResult.price_impact_bps` attributed to execution layer.

**Position reconciliation**: `HealthFactorMonitor` per-chain (Ethereum 12s, Base 2s, Arbitrum 1s); polls Aave
`getUserAccountData`; emits `HEALTH_FACTOR_OBSERVED` + alerts. Position-balance-monitor reads custody balances every
5min and diffs against PBMS expected.

**Margin/collateral pre-liquidation actions (closed set of 5)** via `DeleverageExecutor`:

1. `top_up_collateral` (DeFi)
2. `repay_debt` (DeFi)
3. `close_risky_leg` (CeFi reduce-only)
4. `unwind_to_mm` (TradFi)
5. `cap_bound_block` (Sports/Prediction)

DeFi thresholds: `HF < 1.10 → DEFI_HEALTH_FACTOR_CRITICAL`; `HF < 1.05 → DEFI_LIQUIDATION_IMMINENT`. 60s idempotency
dedup per `(strategy_id, severity, threshold_breached)`. **Liquidation cascade detection NOT explicitly present in
code** — open gap. Oracle freshness gate codes exist (`ORACLE_STALE`/`ORACLE_DEVIATION_EXCEEDED`) but **no QG-enforced
check at transaction time** — open gap.

### 0.9 Credentials + custody inventory

Per `codex/04-architecture/interface-credential-convention.md`:

| Adapter type     | Factory signature                                                                                                                                  |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi execution   | `get_order_adapter(venue, api_key, api_secret, ...)` — HMAC-SHA256                                                                                 |
| DeFi execution   | `connector.connect(config={"wallet_private_key": pk, "rpc_url": url})` — per-request KMS-decrypted; never cached beyond signing window (HARD RULE) |
| Sports execution | `adapter(credentials={"api_key": key, ...})`                                                                                                       |
| Custody          | `get_custody_provider(CustodyConfig(provider, ...))`                                                                                               |

Auth scopes (`SourceCapability.auth_scope` closed set): `api_key` (Binance/Bybit/OKX/Kraken/Aster HMAC);
`api_key + wallet_private_key` (Extended Starknet, SNIP-12/EIP-712); Hyperliquid wallet-based EIP-712 agent key (no API
key); DeFi via `CLOUD_KMS_ENCRYPTED` (May-23) → Copper/Fireblocks (June-1).

**Per-archetype custody (May-23)**:

- `carry_staked_basis`: CLOUD_KMS for DeFi long + non-Binance perp hedge; CEFFU (June-1) for Binance perp hedge —
  **blocked**
- `arbitrage_price_dispersion`: same split — **blocked**

Per-client custody choice: `WalletProvisioningConfig.signing_surface` in
`gs://wallet-config-{pid}/{chain_env}/wallet_provisioning.json`. Per-wallet granularity. Hot-reloads via
`ApiKeyReloader`.

### 0.10 Mock-data plug-in surface (enables strategy/execution e2e testing)

Operator goal: **"fill in mock data... so we can still test the strategy service and execution"**. Activated by
`CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`.

**5 injection levels** (earliest to latest):

1. **MDPS seed**: write synthetic parquets to `.local-dev-cache/mock-seed/market-data-processing-service/` matching
   `lending_indices` / `oracle_prices` / `staking_rates`. Features-onchain picks up + runs REAL calculators.
2. **Feature seed** (skip MDPS): write to `.local-dev-cache/mock-seed/features-service/` with cols `timestamp`,
   `feature_name`, `value`, `available_at`.
3. **ML seed**: write `MLPrediction` records directly (cols: `instrument_id`, `timeframe`, `predicted_class`,
   `confidence`). Patch `cascade_subscriber.py` to pull from seed.
4. **Strategy mock pipeline** (full mock e2e): `strategy_service/engine/mock_data_provider.py` `run_mock_pipeline()`
   generates deterministic signals (seed=42) for 5 representative strategies — no upstream dependencies.
5. **Tenderly fork for DeFi execution**: `execution-service/tests/defi_execution/integration/conftest.py` — real EVM
   environment for SWAP→STAKE→HEDGE legs without mainnet wallet.

**Per-archetype mock-test prerequisites**:

1. **`ARBITRAGE_PRICE_DISPERSION` (price)**: inject `mid_price_{venue}` ≥2 venues with ≥30bps spread above `cost_bps`.
   **Fully runnable — no patching.**
2. **`CARRY_STAKED_BASIS`**: patch `accepted_perp_collateral()` to return a test LST. Without this, engine always
   returns `[]`.
3. **Funding-rate-dispersion**: **fix P0-2 (`raise ValueError → continue`)** first; otherwise single missing feature
   aborts entire tick.
4. **PnL stream assertions**: do not assert on values — both archetypes hardcode zeros.
5. **Shadow mode**: set `V2ShadowRunner(shadow_mode=False)` explicitly; default suppresses live instruction dispatch.

### 0.11 Centralisation map — risk / PnL / exposure / liquidation / treasury

Operator-asked: **"what's centralised, what's strategy-agnostic, what's in what code path"** + **"is risk like
liquidation risk managed in one place"**. Post-consolidation 2026-05-19 (risk + position-balance-monitor +
pnl-attribution merged into strategy-service).

**CENTRALISED — one place; archetypes inherit for free**:

| Component                           | File / Module                                                                                                          | Interface                                                                                                                                                                                               |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Risk rules registry (7 axes)        | `unified-api-contracts/.../registry/risk_rules/{global,venue,account,asset_group,client,strategy_family,archetype}.py` | All rule files in UAC; loaded into `RiskRuleRegistry` at import                                                                                                                                         |
| PnL attribution engine              | `strategy_service/pnl/engine/breakdown.py` `compute_pnl_breakdown()`                                                   | 13 components: realized, unrealized, delta, basis, funding, interest, gamma/theta/vega, gas, slippage, residual, share_class, fx, lst_yield + DeFi-specific (`STAKING_YIELD`/`RESTAKING_REWARD`/etc.)   |
| Risk monitor                        | `strategy_service/risk/core/risk_monitor.py` `RiskMonitor.monitor_all_clients()`                                       | Single timer; delegates to `RiskCalculator` (same calc as batch — batch=live in code)                                                                                                                   |
| Pre-trade check engine              | `strategy_service/risk/core/pre_trade_check_engine.py`                                                                 | 7 universal checks: stale_price, market_hours (TradFi only), position_limit, exposure_limit, capital_limit, leverage_limit, var_limit                                                                   |
| Deleverage / margin action dispatch | `execution-service/.../algo_library/deleverage_executor.py` `DeleverageExecutor`                                       | Single subscriber to `MarginEvent`; 5 closed-set actions × 5 asset_groups; 60s in-memory dedup                                                                                                          |
| Treasury monitor                    | `strategy_service/position/core/treasury_monitor.py` `TreasuryMonitor`                                                 | Universal across share classes (USDC/ETH/SOL/BTC); per-share-class min 10% / target 20% / max 30%; `compute_unified_nav()` aggregates 4 sources (COPPER + CEFFU = stub; venue_margin + on_chain = live) |
| Kill-switch rules engine            | `strategy_service/risk/v2/kill_switch_rules.py` `KillSwitchRulesEngine`                                                | 3 decisions (DELTA_NEUTRAL_EXIT, REDUCTIONS_ONLY, HUMAN_REQUIRED); centralised trigger ladder                                                                                                           |
| MarginEvent canonical producer      | `strategy_service/position/core/margin_event_emitter.py` `emit_margin_event_for_health()`                              | Replaces prior pattern where each downstream service re-derived HF                                                                                                                                      |

**PER-ARCHETYPE — each archetype must provide its own**:

| Component                                                                                  | Why per-archetype                                                                                                                          | Risk if missing                                                                                                             |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Kill-switch thresholds (`ARCHETYPE_KILL_SWITCH_THRESHOLDS` dict in `kill_switch_rules.py`) | Service-local dict (not in UAC); new archetype absent → `evaluate_archetype_breach()` returns `None` → **kill-switch silently never arms** | **NOT ENFORCED**; no QG step audits coverage                                                                                |
| Archetype risk rules (`ARCHETYPE_RULES` tuple in UAC `risk_rules/archetype.py`)            | New archetype with zero rules → Layer 2 evaluator silently skips it                                                                        | Only 2/53 archetypes have rules (CARRY_STAKED_BASIS + ARBITRAGE_PRICE_DISPERSION)                                           |
| Concentration multiplier (`ARCHETYPE_CONCENTRATION_MULTIPLIER` dict)                       | Defaults to `Decimal("1.0")` silently for unknown archetypes                                                                               | Recursive-borrow 1.5× penalty only applies if explicitly listed                                                             |
| Per-archetype liquidation detection (Solana lending: Marginfi/Kamino/Sanctum)              | `HealthFactorMonitor` is Aave/EVM ONLY; non-Aave protocols have no HF-polling equivalent                                                   | **CRITICAL GAP** — Solana lending archetypes will not fire `DEFI_LIQUIDATION_IMMINENT`                                      |
| Multi-leg cascade unwind                                                                   | Centralised dispatcher fires correct first action; cross-leg chain is per-archetype                                                        | DeFi long + CeFi hedge: liquidation on DeFi → `repay_debt` fires; whether CeFi hedge unwinds depends on per-archetype logic |
| Entry/exit signal (per-`on_tick`)                                                          | Per-archetype by design                                                                                                                    | —                                                                                                                           |
| Universe enumeration (per-archetype `_build_X` in catalog.py)                              | Per-archetype                                                                                                                              | —                                                                                                                           |
| Hedge ratio derivation (e.g. `compute_dynamic_hedge_ratio()` for staked_basis only)        | Per-archetype                                                                                                                              | —                                                                                                                           |
| PnL stream emission (currently zero-stub per-archetype — should consolidate)               | Duplication candidate (§0.3 P0-5)                                                                                                          | Workspace-wide TODO                                                                                                         |

**STRATEGY-AGNOSTIC infrastructure** (inherited free):

`StrategySupervisor` + per-client subprocess isolation; `MarkPriceAggregator` (shared-memory MTM); `AllocationSizer`
(universal — operates on UAC portfolio constraints); `position-balance-monitor` (post-consolidation; archetypes read,
don't maintain own position ledgers); `MarginEvent` producer; `PreTradeCheckEngine` 7-check gate;
ClientAdmissionController; ShardCapacitySensor.

**Liquidation risk — is it managed in ONE place? PARTIAL — two gaps**:

1. **Gap 1: Solana lending protocols unmonitored**. `HealthFactorMonitor` polls Aave only (Ethereum 12s / Base 2s /
   Arbitrum 1s). Marinade / Jito / Sanctum / Marginfi / Kamino covered by venue rules (`venue.py` OI cap, position size,
   concentration MONITOR) but no HF-polling equivalent. Solana borrow archetypes will not fire liquidation alerts.
2. **Gap 2: Multi-leg cascade not automatic**. Dispatcher fires action for the leg that generated `MarginEvent`.
   Cross-leg unwind (`carry_staked_basis`: DeFi long + CeFi perp short, where DeFi leg fires LIQUIDATION but CeFi hedge
   must also unwind) is per-archetype logic. No framework-level "unwind all legs atomically" primitive.

**New-archetype risk inheritance test** (if `XYZ_FOO` added):

| Capability                                                              | Inherited free?  | Condition / Gap                                                          |
| ----------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------ |
| PnL attribution (13 components)                                         | YES              | `compute_pnl_breakdown()` universal                                      |
| Global risk rules (drawdown halt, data-staleness halt, $2M CaR ceiling) | YES              | GLOBAL scope, `applies_to="*"`                                           |
| Venue-level position caps                                               | YES              | Execution-service reads `get_max_position_size_usd_for_venue()` from UAC |
| Account-level gross/net/drawdown limits                                 | YES              | `paper_default` + `live_cutover_2026_05_23` apply to all archetypes      |
| Asset-group concentration + gas budget                                  | YES              | Rules fire by asset_group, not archetype                                 |
| Treasury sweep + NAV compute                                            | YES              | If archetype declares TREASURY/TRADING wallet split in `TreasuryConfig`  |
| Pre-trade 7-check gate                                                  | YES              | `PreTradeCheckEngine` architecture-universal                             |
| Margin event / deleverage dispatch                                      | YES for Aave/EVM | **NO for Solana or non-Aave protocols**                                  |
| Kill-switch thresholds                                                  | NO               | Must add to `ARCHETYPE_KILL_SWITCH_THRESHOLDS` dict                      |
| Archetype-specific risk rules                                           | NO               | Must add 12-rule block to `archetype.py` in UAC                          |
| Concentration multiplier                                                | NO               | Defaults to 1.0 silently                                                 |
| Client subscription cap                                                 | NO               | `client.py` has only `cutover_demo_client_2026_05_23`                    |
| Strategy-family cross-correlation detection                             | PARTIAL          | Only 2 of 7 family slots filled                                          |

**Verdict**: a new archetype inherits ~60% of the risk stack for free. Non-inherited: kill-switch arming thresholds,
per-archetype UAC rule registration, Solana liquidation monitoring, multi-leg cascade unwind.

### 0.12 Asset-group ↔ archetype binding matrix (operator: "where and how asset groups tied into strategies and where they don't")

**Binding mechanism — implicit via archetype design, no explicit `asset_group` config field**:

Three layers (no single "supported_asset_groups" Python field on archetype):

1. **`archetype_capability_manifest.json`** in UAC: each archetype has cells typed as
   `(asset_group: VenueCategoryV2, instrument_type: ArchetypeInstrumentType, status: SUPPORTED|PARTIAL|BLOCKED)`.
   `archetypes_for_pair(asset_group, instrument_type)` is the canonical query.
2. **Per-archetype codex doc `venue_universe:` frontmatter**: implies asset_group via venue list (e.g.
   `[LIDO, JITO, DRIFT, DERIBIT, BYBIT]` → DeFi + CeFi). No `asset_group:` key in any archetype frontmatter.
3. **`ASSET_GROUP_ONTOLOGY` in `archetype_capability_matrix.py`**: per-asset-group fill/margin/settlement model;
   archetype capability registry uses `VenueCategoryV2` as the binding key.

**Can one archetype operate in multiple asset_groups? YES, several cross-asset-group archetypes**:

- `ARBITRAGE_PRICE_DISPERSION` — spans CEFI + DEFI + SPORTS + PREDICTION + partial TRADFI (most cross-cutting)
- `CARRY_STAKED_BASIS` + `CARRY_STAKED_BASIS_DATED` + `CARRY_RECURSIVE_STAKED` — DeFi+CeFi hybrid by design (DeFi stake
  leg + CeFi perp hedge)
- `ML_DIRECTIONAL_CONTINUOUS` + `ML_DIRECTIONAL_EVENT_SETTLED` — CEFI + DEFI + TRADFI (+ SPORTS/PREDICTION for event
  variant)
- `ARBITRAGE_CROSS_DOMAIN_EVENT` — `primary_category: CROSS_CATEGORY` (sports + prediction)
- `PORTFOLIO_*` family — CROSS_CATEGORY by design

**Closed-set archetype × asset_group matrix** (family-level abridgement; full 57-archetype table in per-archetype
audits):

| Archetype family                                                                              | CeFi                   | DeFi                            | TradFi          | Sports                    | Prediction             | Cross-AG?              |
| --------------------------------------------------------------------------------------------- | ---------------------- | ------------------------------- | --------------- | ------------------------- | ---------------------- | ---------------------- |
| ML_DIRECTIONAL / RULES_DIRECTIONAL (continuous)                                               | SUPPORTED              | SUPPORTED                       | SUPPORTED       | PARTIAL                   | PARTIAL                | Yes                    |
| ML_DIRECTIONAL / RULES_DIRECTIONAL (event_settled)                                            | PARTIAL                | NOT_APPLICABLE                  | NOT_APPLICABLE  | SUPPORTED                 | SUPPORTED              | Yes                    |
| CARRY_AND_YIELD (staked_basis, recursive_staked)                                              | SUPPORTED (hedge)      | SUPPORTED (stake/lend)          | NOT_APPLICABLE  | NOT_APPLICABLE            | NOT_APPLICABLE         | Yes (DeFi+CeFi hybrid) |
| CARRY_AND_YIELD (basis_perp, basis_dated)                                                     | SUPPORTED              | PARTIAL/NA                      | PARTIAL (dated) | NA                        | NA                     | No                     |
| CARRY_AND_YIELD (recursive_borrow_lending_only, yield_rotation_lending, yield_staking_simple) | NA                     | SUPPORTED                       | NA              | NA                        | NA                     | No                     |
| ARBITRAGE_PRICE_DISPERSION                                                                    | SUPPORTED              | SUPPORTED                       | PARTIAL         | SUPPORTED                 | SUPPORTED              | Yes                    |
| ARBITRAGE*MEV*\* (sandwich/JIT/backrun/liquidation_bundle)                                    | NA                     | SUPPORTED                       | NA              | NA                        | NA                     | No                     |
| ARBITRAGE_CROSS_DOMAIN_EVENT                                                                  | NA                     | NA                              | NA              | SUPPORTED                 | SUPPORTED              | Yes (CROSS_CATEGORY)   |
| LIQUIDATION_CAPTURE                                                                           | SUPPORTED              | SUPPORTED                       | NA              | NA                        | NA                     | Yes                    |
| MARKET*MAKING*\* (8 variants)                                                                 | SUPPORTED (5 variants) | SUPPORTED (DEFI*LP*\* variants) | NA              | SUPPORTED (event_settled) | SUPPORTED (prediction) | per-variant            |
| DEFI_LP_CONCENTRATED / POOL / VAULT                                                           | NA                     | SUPPORTED                       | NA              | NA                        | NA                     | No                     |
| EVENT_DRIVEN                                                                                  | SUPPORTED              | NA                              | NA              | NA                        | NA                     | No                     |
| VOL\_\* (18 variants — CeFi Deribit + TradFi CBOE)                                            | SUPPORTED              | NA (no DeFi options today)      | PARTIAL         | NA (no options on sports) | NA (binary ≠ options)  | No                     |
| STAT_ARB_PAIRS_FIXED / CROSS_SECTIONAL                                                        | SUPPORTED              | NA                              | SUPPORTED       | NA                        | NA                     | No                     |
| PORTFOLIO\_\* (4 sleeve allocators)                                                           | SUPPORTED              | SUPPORTED                       | SUPPORTED       | SUPPORTED                 | SUPPORTED              | Yes (CROSS_CATEGORY)   |

**Invalid combos with rationale**:

| INVALID combo                                             | Rationale                                                                                                                                 |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Sports + any CARRY archetype                              | No funding rate mechanism; sports settle on discrete outcomes, not continuous rate accrual; `has_funding=False`, `has_liquidations=False` |
| Prediction + spot/perp/dated_future                       | Polymarket/Kalshi are binary outcome markets; no continuous underlying                                                                    |
| DeFi + listed options                                     | No DeFi options protocol in venue registry today (Lyra/Premia/Dopex not yet)                                                              |
| TradFi + LST staking / LENDING_POSITION / BORROW_POSITION | TradFi instrument set is `{SPOT, FUTURE, OPTION}` only                                                                                    |
| MEV sandwich + any live trading                           | `ARBITRAGE_MEV_SANDWICH` is theoretical-only tracer; not in `ARCHETYPE_ENGINE_REGISTRY`                                                   |
| PORTFOLIO\_\* + direct execution                          | No engine registration for any `PORTFOLIO_*` archetype — sleeve allocator only                                                            |
| MARKET_MAKING_PREDICTION + live trading                   | No engine registered for this archetype yet                                                                                               |

**Enforcement**: closed-set constraints are catchable by `ARCHETYPE_ENGINE_REGISTRY` (raises `KeyError`),
`test_subdir_family_alignment.py`, `test_archetype_capability_manifest_parity.py`, Pydantic `ArchetypeCapabilityCell`
validation. NOT enforced: risk-rule coverage for all archetypes, concentration multiplier coverage, allocator-archetype
binding, codex doc existence.

### 0.13 Share class × archetype matrix (operator: "what share classes each archetype can handle")

**Foundational axiom** (`strategy_archetype_taxonomy_2026_05_12.md`): **"Share class determines what market-neutral
means."** Strategy is market-neutral to its share class.

**Per-archetype share class declarations** (from each codex `share_class:` config schema):

| Archetype family                           | Primary share class | Permitted others                                        | Notes                                                                                                               |
| ------------------------------------------ | ------------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ---- |
| `CARRY_STAKED_BASIS`                       | USDC                | USDT (Bybit slot)                                       | Operator axiom: always USD\* (USD-neutral). ETH share class would be a different archetype (`YIELD_STAKING_SIMPLE`) |
| `CARRY_RECURSIVE_STAKED`                   | not declared        | ETH / SOL / USDC                                        | ETH share class → no perp hedge (ETH-neutral by construction); USDC → perp hedge required                           |
| `CARRY_RECURSIVE_BORROW_LENDING_ONLY`      | not declared        | USDC / USD                                              | Market-neutral by construction (rate spread)                                                                        |
| `CARRY_BASIS_PERP` / `_INV`                | USDT                | USDC, USD                                               | CeFi perp-native                                                                                                    |
| `CARRY_BASIS_DATED` / `_INV`               | USD                 | USDT, USDC                                              | Doc declares `share_class: USD`                                                                                     |
| `YIELD_STAKING_SIMPLE`                     | not declared        | ETH / SOL / USDC                                        | Passive hold — natural native-token share class                                                                     |
| `YIELD_ROTATION_LENDING`                   | USDC                | USDT, USD                                               | —                                                                                                                   |
| `ARBITRAGE_PRICE_DISPERSION`               | USD                 | USDT, USDC, GBP                                         | Sports cross-book slots show `gbp` (e.g. `...epl-gbp-v2`); always USD\*                                             |
| `ARBITRAGE_CROSS_DOMAIN_EVENT`             | USD\*               | USD, GBP, USDC                                          | "Always fiat-denominated to match binary payoff"                                                                    |
| `LIQUIDATION_CAPTURE`                      | USD                 | USDC, USDT                                              | —                                                                                                                   |
| All `MEV_*`                                | USDC                | depends on chain (ETH for Ethereum MEV, SOL for Solana) | —                                                                                                                   |
| `MARKET_MAKING_EVENT_SETTLED`              | GBP                 | USD, EUR                                                | Sports books settle GBP                                                                                             |
| `MARKET_MAKING_PREDICTION`                 | USDC                | —                                                       | Polymarket/Kalshi native                                                                                            |
| `MARKET_MAKING_*` (4 CeFi variants)        | USDT or USD         | USDC                                                    | —                                                                                                                   |
| `DEFI_LP_*`                                | USDC                | USDT, ETH                                               | DeFi protocols primary in USDC                                                                                      |
| `EVENT_DRIVEN`                             | USDT                | USDC                                                    | —                                                                                                                   |
| All `VOL_*` (CeFi options)                 | USDT                | USDC, USD                                               | LEAPS/TERM_STRUCTURE/DISPERSION: `USDT                                                                              | USD` |
| `STAT_ARB_PAIRS_FIXED` / `CROSS_SECTIONAL` | USD                 | USDT                                                    | —                                                                                                                   |
| `PORTFOLIO_*`                              | USD                 | any                                                     | Portfolio layer converts each sub-strategy NAV to reporting currency                                                |
| `ML_DIRECTIONAL_CONTINUOUS`                | USDT or ETH or USD  | any                                                     | Doc states "BANKROLL in share_class currency (e.g., USDT, ETH, USD)" — currency-agnostic                            |
| `ML_DIRECTIONAL_EVENT_SETTLED`             | USD or GBP or EUR   | USDC                                                    | —                                                                                                                   |
| `RULES_DIRECTIONAL_CONTINUOUS`             | USD                 | USDT, ETH                                               | —                                                                                                                   |
| `RULES_DIRECTIONAL_EVENT_SETTLED`          | USD                 | GBP                                                     | —                                                                                                                   |

**Share class enum collision** (P1 — affects sports + TradFi tracks):

- **Enum A** — `unified_api_contracts.canonical.crosscutting.share_class.ShareClass`: 3 values (USDT/ETH/BTC).
  Legacy/MVP; root UAC facade `from unified_api_contracts import ShareClass` exports this.
- **Enum B** — `unified_api_contracts.internal.architecture_v2.enums.ShareClass`: 9 values
  (USDT/USDC/FDUSD/USD/GBP/EUR/ETH/BTC/SOL). All archetype docs + `ShareClassFxMatrix` + `share-class.md` SSOT use this.

`canonical.crosscutting.ShareClass` is the legacy 3-value MVP scoped to LIVE_DEFI_CUTOVER (May-23). Reconciliation
needed: deprecate Enum A or document its scope as "MVP client-subscription only — internal/architecture_v2 is operative
for everything else." Any code importing `from unified_api_contracts import ShareClass` silently drops
GBP/EUR/USD/SOL/USDC/FDUSD.

**Stale reference**: `LIVE_DEFI_CUTOVER_ARCHETYPES = ["carry_staked_basis", "leveraged_funding_arb"]` in
`client_share_classes.py`. The second archetype was renamed to `arbitrage_price_dispersion` per
`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`. **Fix before May-23**.

**Neutrality derivation rule** (foundational axiom — currently hardcoded per-instance config field `target_net_delta`,
NOT runtime-derived):

- USDT/USDC/USD share class → `target_net_delta = 0.0` (USD-neutral; requires hedge leg for native long exposures)
- ETH/SOL/BTC share class → native-token-neutral (passive long; no perp hedge — perp would break in-class neutrality)

**Gap**: no function `derive_neutrality_target(archetype, share_class) -> float`. When a new share-class instance is
created (e.g. ETH share class `CARRY_RECURSIVE_STAKED`), operator must know to remove perp hedge — system does not
enforce it.

**`ShareClassFxMatrix`** (`strategy-service/strategy_service/portfolio_allocator/share_class_fx.py`):

- Keyed by `(from_class, to_class)` pair
- Supports implicit inversion + hub triangulation
- Default hubs: `(ShareClass.USDT, ShareClass.USD)` — USDT-side stablecoins
- Triangulation example: `BTC → GBP` = `BTC → USDT × USDT → USD × USD → GBP` (inverse of GBP→USD)
- **Freshness/cadence**: caller's responsibility (`last_updated_utc(pair)` exposes oldest constituent rate); no TTL
  enforcement in matrix itself

**Sports GBP gap**: `MARKET_MAKING_EVENT_SETTLED` declares `share_class: GBP` + cross-book sports arb slots use `gbp` in
label. `ShareClassFxMatrix` supports GBP triangulation via USD hub IN THEORY, but no integration test or catalog slot
demonstrates the full `MARKET_MAKING_EVENT_SETTLED → NAV → GBP → USDT` conversion cycle. `SHARE_CLASS_PERF_FEE_CONFIGS`
dict has `USDC_CUTOVER_V1` + `ETH_FLAGSHIP` but no `GBP_SPORTS` entry.

### 0.14 Options viability + vol fitter status (operator: "do we even have an options vol fitter to derive normalised strikes")

**Short answer**: NO parametric fitter (SVI/SSVI). TWO interpolation-based surface calculators exist. Greeks are venue
passthrough. NormalisedStrikeCoordinate works in delta space.

**Vol surface calculators (features-service)**:

- [`features_service/volatility/calculators/tradfi_vol_surface.py`](../../../features-service/features_service/volatility/calculators/tradfi_vol_surface.py)
  `TradFiVolSurfaceCalculator` — ingests DataFrame with `mark_iv`, `strike_price`, `expiry_days`, `option_type`. Uses
  `scipy.interpolate.CubicSpline` (1D single expiry) or `griddata` (2D multi-expiry). Outputs ATM IV, 25d skew, risk
  reversal, butterfly, term structure slope/curvature. **No parametric model.**
- [`features_service/volatility/calculators/vol_surface_term_structure.py`](../../../features-service/features_service/volatility/calculators/vol_surface_term_structure.py)
  `VolSurfaceTermStructureCalculator` — delta-pillar × expiry-tenor grid (10d/25d/50d × 7d/30d/60d/90d/180d). VRP =
  `realized_vol_20d − atm_iv_30d`; IV percentile on 252-day rolling.

Neither implements SVI / SABR / SSVI. Both consume `mark_iv` as pre-computed input — they do NOT invert mark prices to
IV themselves. The `VOL_TRADING_OPTIONS` archetype doc explicitly describes step 1 as "fit IV surface (SVI or SSVI) to
current option prices" + references a `surface_model_ref: svi-btc-v3` config key — **this fitter does not exist** in any
service source tree.

**Normalised strike derivation — delta space (not surface-derived moneyness)**:

Canonical UAC type: `NormalizedStrikeCoordinate` in `unified-api-contracts/.../canonical/domain/derivatives/options.py`.
Fields: `delta: float ∈ (0,1]`, `expiry_days: int > 0`, `option_type: Literal["call","put"]`, `moneyness: float | None`.

Resolution at execution time: `StrikeMapper` in `execution-service/.../instruments/strike_mapping.py`. Two paths:

1. **Delta path** (`resolve()`): scans live options chain, minimises `|contract.delta − coordinate.delta|`. Returns
   nearest listed strike.
2. **Moneyness fallback** (`resolve_moneyness()`): approximates strike from `ln(K/F)` when delta absent from chain.

Strategies express views in delta space; strike pinning happens inside `OptionsComboHandler` at order submission.
Architecturally clean. **Gap**: without parametric surface, cannot ask "what delta corresponds to moneyness X at 30d
tenor" in model-consistent way — rely entirely on delta column supplied by venue or Tardis.

**Greeks computation — venue-provided passthrough**:

`CefiOptionsChainAdapter` (`market-data-processing-service/.../adapters/cefi/options_chain_adapter.py`) ingests Tardis
CSV fields `delta, gamma, vega, theta, rho, mark_iv, bid_iv, ask_iv, mid_iv` and writes directly into candle output.
`OptionGreeks` UAC schema carries delta/gamma/theta/vega/rho/vanna/volga — all venue passthrough.
`PortfolioGreekModelRegistry` (`strategy_service/risk/v2/greek_model.py`) implements 3 margin models (`DERIBIT_PM`,
`SPAN`, `REG_T`) — consumes Greek exposures to compute IM, does NOT price options or compute Greeks from first
principles.

**Critical gaps**: (a) no risk-free rate source wired into any calculator (no `UnifiedCloudConfig` key for RFR, no IS
endpoint, no SSOT constant); (b) no `mark_price → implied_vol` inversion anywhere in Python source; (c) vanna + volga in
schema but not computed locally.

**Options-capable archetypes** — **1 of ~18 vol design docs implemented**:

- `VolTradingOptionsEngine` (`strategy-service/.../engine/strategies/v2/vol_trading/options.py`) — `VOL_TRADING_OPTIONS`
  archetype. Reads `iv_bps` + `rv_bps`, computes `divergence = iv − rv`, emits 2-leg `AtomicInstruction` (call + put) if
  `abs(divergence) >= divergence_threshold` (default 500 bps). **Critical limitation**: `call_instrument` +
  `put_instrument` are pre-configured fixed instrument IDs in strategy params — engine does NOT dynamically select
  strikes via vol surface or `StrikeMapper`. Cannot trade calendars, butterflies, or iron condors despite design doc.
- All other vol archetypes (skew trading, gamma scalping, calendar, diagonal, etc.) — design docs only, no engine
  implementation.

**Per-venue options support state**:

| Venue                                | Data ingestion                           | Live feed                                    | Execution handler              | Status                    |
| ------------------------------------ | ---------------------------------------- | -------------------------------------------- | ------------------------------ | ------------------------- |
| Deribit                              | Tardis CSV via `CefiOptionsChainAdapter` | MTDS adapter exists; live wiring unconfirmed | `OptionsComboHandler` scaffold | Partial — historical only |
| CBOE (SPX/VIX)                       | Databento OPRA converter exists          | No live handler confirmed                    | `OptionsComboHandler` scaffold | Data side only            |
| CME                                  | Databento CME converter exists           | No live handler confirmed                    | No handler                     | Data ingestion only       |
| OKX Options                          | Referenced in design doc                 | No adapter                                   | Not implemented                | Design only               |
| DeFi options (Lyra / Premia / Dopex) | No adapter                               | —                                            | —                              | Not present               |

`OptionsComboHandler` (`execution-service/.../engine/handlers/options_handler.py`) is scaffold-level: flat 5 bps spread
cost, hard-coded fee defaults (Deribit 0.02%/0.05%, CBOE 0.003%/0.003%), no real execution routing logic. Supported
venues: `{"DERIBIT", "CBOE"}`.

**Cross-cutting: options viable for non-vol archetypes? NO today.** Both May-23 archetypes (`carry_staked_basis`,
`arbitrage_price_dispersion`) operate in spot/perp space with no options legs. Infrastructure
(`NormalizedStrikeCoordinate`, `StrikeMapper`, `OptionsComboHandler`) is generic enough to be reused for tail-hedging on
a carry position, but only `VolTradingOptionsEngine` emits `OPTIONS_COMBO` instructions today.

**P0/P1 gaps for master strategy plan**:

1. **P0**: No SVI/SSVI surface fitter — blocks dynamic strike selection, spread structures, model vol pricing
2. **P0**: No `mark_price → IV` inversion — any venue not providing pre-computed `mark_iv` is unusable
3. **P0**: `VolTradingOptionsEngine` uses fixed instrument IDs — cannot roll to nearest liquid strike at trade time
4. **P0**: Live options chain pipeline unconfirmed — historical Tardis path works; live equivalent needs verification
5. **P1**: No centralised risk-free rate source
6. **P1**: `OptionsComboHandler` is scaffold-only — no real order routing
7. **P2**: 1 of ~18 vol engines implemented (skew, gamma scalping, calendar, diagonal, etc.)
8. **P2**: No DeFi options support (Lyra/Premia/Dopex)

### 0.15 Topology per archetype (operator: "do different archetypes need different topology")

**Closed-set topology patterns**:

| Pattern                                                | When used                                                                                                                                                      | Archetypes                                                                             |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **Per-archetype VM**                                   | Canonical production for paper/live; one VM per archetype                                                                                                      | All May-23 archetypes; singleton-locked per `{mode}-{archetype}`                       |
| **Per-(archetype, shard) VM** (Phase 8 target)         | Post-Phase-8 evolution; VM name `strategy-{mode}-{archetype}-shard{N}-{ts}`; singleton key becomes triplet                                                     | Codex SSOT exists (`strategy-shard-vm-topology.md`); Phase 8 code **NOT yet merged**   |
| **Per-(archetype, asset_group) ensemble VM**           | DeFi VM hosts both `carry_staked_basis` + `arbitrage_price_dispersion` as separate OS processes; CeFi VM hosts hedge legs                                      | `strategy-ensemble-topology.md` SSOT                                                   |
| **Per-(archetype, client) subprocess** (May-23 active) | `StrategySupervisor` spawns 1 `ClientWorker` `multiprocessing.Process` per client × archetype on shard 0; hard crash isolation                                 | All May-23 archetypes                                                                  |
| **Co-located services**                                | One VM runs strategy-service (one per archetype) + position-balance-monitor + risk-and-exposure + execution-service via local Redis Stream at `127.0.0.1:6379` | colocated_engine.py model                                                              |
| **Batch fleet** (ephemeral one-shot VMs)               | Complete + write GCS + self-delete (`VM_SHUTDOWN_ON_COMPLETION=true`); singleton-locked per archetype                                                          | All backtests via `launch-defi-backtest-vm.sh` / `launch-strategy-backtest-grid-vm.sh` |
| **Paper fleet** (long-lived recurring VMs)             | Tenderly fork fills; runs until operator-stopped                                                                                                               | `launch-strategy-paper-vm.sh` / `launch-defi-paper-trading-vm.sh`                      |
| **Live fleet** (long-lived live VMs)                   | `CLOUD_KMS_ENCRYPTED` signing against mainnet; mandatory `--dry-run-live-cutover-passed` gate                                                                  | `launch-strategy-live-vm.sh`                                                           |

**Per-archetype topology**:

| Archetype                    | Batch VM                                                                                                               | Paper VM                                                                               | Live VM                                           | Per-shard?                                               | Per-client subprocess?  |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------- | ----------------------- |
| `carry_staked_basis`         | `defi-backtest-{slug}-{ts}` or `strategy-backtest-grid-{slug}-{ts}` (`n2-standard-4`, 16GB, 100GB)                     | `strategy-paper-{slug}-{ts}` (`LONG_LIVED_LIVE`, `n2-standard-4`, 50GB, Tenderly fork) | `strategy-live-{slug}-{ts}` (same shape, mainnet) | `MANIFEST_PER_VM_SHARDS=true`; shard-suffix post-Phase 8 | YES                     |
| `arbitrage_price_dispersion` | Same with `arb-price-dispersion` slug                                                                                  | Same                                                                                   | Same                                              | Same                                                     | Same                    |
| ML-Directional family        | `ml-{instrument}-{ts}` via `launch-ml-vm.sh` (`n2-highmem-8`/`n2-highmem-16`/`n1-standard-8+T4`); NOT singleton-locked | No paper equivalent — ML inference co-runs on strategy VM                              | Same                                              | Per-instrument; `MANIFEST_PER_VM_SHARDS=true`            | At strategy layer above |
| Vol-Trading family (19)      | Config-grid backtest, singleton per archetype                                                                          | Paper VM `n2-standard-4` default                                                       | Same                                              | YES                                                      | YES                     |
| Market-Making family (10)    | Per-archetype batch                                                                                                    | Per-archetype paper                                                                    | Per-archetype live                                | YES                                                      | YES                     |
| Arbitrage-Structural (7)     | Per-archetype batch; MEV requires Tenderly-MEV fork (NOT WIRED)                                                        | Per-archetype paper                                                                    | Per-archetype live                                | YES                                                      | YES                     |
| Carry-and-Yield (10)         | Per-archetype batch                                                                                                    | Per-archetype paper                                                                    | Per-archetype live                                | YES                                                      | YES                     |
| Sports archetypes            | Sports ensemble VM (`sports-strategy-` prefix)                                                                         | Same                                                                                   | Same                                              | YES                                                      | YES                     |
| Prediction archetypes        | Prediction ensemble VM (`prediction-strategy-` prefix)                                                                 | Same                                                                                   | Same                                              | YES                                                      | YES                     |

**LifecycleClass per archetype**:

- `EPHEMERAL_BATCH` — all data-pipeline backfill/forward-poll VMs (CeFi/DeFi/TradFi/Sports/Prediction
  MTDS+instruments+features backfill)
- `LONG_LIVED_LIVE` — ALL strategy paper + live VMs (`strategy-paper-`, `strategy-live-`, `defi-paper-`,
  `defi-recursive-`); all live-pipeline MTDS+MDPS+features VMs
- `SCHEDULED_RECURRING` — `strategy-shard-vm-topology.md` target post-Phase 8; current watchdog still has
  `strategy-paper-` as `LONG_LIVED_LIVE` (pre-Phase 8)
- `EPHEMERAL_EXPERIMENT` (reserved) — `exp-ml-`, `exp-strategy-`, `exp-execution-` prefixes registered; NO launchers use
  these in production yet

**Per-client subprocess isolation status** (May-23): Phase E.0 + E.1 SHIPPED. `StrategySupervisor` +
`ClientAdmissionController` + `ClientWorker` (one subprocess per client) + `MarkPriceAggregator` (supervisor-owned;
shared-memory broadcast) + restart loop (exp backoff 1s→16s, then `CLIENT_QUARANTINED` after 5 failures) +
`ShardCapacitySensor` (10s poll; fires `SPAWN_NEW_SHARD` at memory≥70% / CPU≥80% / clients≥`shard_capacity_max` for 3
samples). **2 clients live May-23**: `odum-research-uk` + `defi-client-1`, both shard_id=0. Phase E.2 (auto-spawn)
post-cutover 2026-05-28. Phase E.3 (intra-client rebalancer) post-cutover 2026-06-01.

**Per-asset-group fleet split**: DeFi isolated from CeFi at VM level for long/stake/lend leg; CeFi VM owns hedge/short
perp leg. Cross-VM communication via Pub/Sub (NEVER direct HTTP). **GAP**: cross-VM coordination bus NOT yet wired
(`strategy-ensemble-topology.md` spec exists; no code; DeFi paper VM runs fully standalone today — CeFi hedge leg not
coordinated at VM level).

**Topology gaps for master strategy plan**:

1. **Gap 1 — Phase 8 launcher + watchdog wiring NOT merged**. `launch-strategy-live-vm.sh` +
   `launch-strategy-paper-vm.sh` don't accept `--shard N` or `--clients-yaml-path`. Watchdog doesn't recognise
   `strategy-{mode}-{archetype}-shard{N}-` prefix. `/api/strategy/shard/spawn` endpoint missing.
2. **Gap 2 — No dedicated launchers for 55 of 57 archetypes**. `launch-strategy-live-vm.sh` hard-validates `--archetype`
   against 2-entry allowlist (`carry_staked_basis | ARBITRAGE_PRICE_DISPERSION`); 55 others rejected. Expand allowlist +
   `VM_PREFIX_TO_BUCKET` entries.
3. **Gap 3 — MEV archetypes lack Tenderly-MEV fork + dedicated launchers**. 4 MEV archetypes
   (sandwich/JIT/backrun/liquidation_bundle) have no launch scripts, no watchdog prefix entries, require
   bundle-submission infra (Flashbots / Eden relay). Effectively blocked at topology layer.
4. **Gap 4 — Vol archetypes need machine-type benchmarking before sizing known**. Synthetic-data benchmarking harness
   blocked on Phase-4-tail. Deploying vol archetypes with default `n2-standard-4` may cause OOM for continuous
   delta-hedging across multi-expiry chains.
5. **Gap 5 — Cross-VM DeFi+CeFi coordination bus NOT yet wired**. Pub/Sub topic naming, subscription pattern, failure
   propagation between DeFi VM ↔ CeFi VM all undefined. Blocks any DeFi archetype with active hedge leg from running
   full topology in paper/live.

### 0.16 New-archetype touch surface + closed-set constraints (operator: "does someone need to touch only one set of modules or several")

**Touch surface — adding `XYZ_FOO` archetype, ordered list**:

| #   | File                                                                                                                                 | Type                      | Required for                                                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------- | ----------------------------------------------------------- |
| 1   | `uac/internal/architecture_v2/enums.py` (`StrategyArchetype` + `ARCHETYPE_TO_FAMILY`)                                                | REQUIRED                  | Canonical enum                                              |
| 2   | `uac/internal/architecture_v2/archetype_capability_manifest.json`                                                                    | REQUIRED                  | Per-(asset_group, instrument_type) cells; UI sync source    |
| 3   | `uac/internal/__init__.py`                                                                                                           | REQUIRED                  | Re-export of new enum value                                 |
| 4   | `uac/registry/archetype_capability_matrix.py` (`ASSET_GROUP_ONTOLOGY`)                                                               | CONDITIONAL               | Only if new asset_group introduced                          |
| 5   | `uac/registry/risk_rules/archetype.py` (`ARCHETYPE_RULES`, `ARCHETYPE_CONCENTRATION_MULTIPLIER`)                                     | REQUIRED for cutover      | ≥10 rules per cutover archetype                             |
| 6   | `strategy_service/.../v2/factory.py` (`ARCHETYPE_ENGINE_REGISTRY`)                                                                   | REQUIRED                  | Engine class binding                                        |
| 7   | `strategy_service/.../v2/<family>/xyz_foo.py` (new engine class extending `BaseArchetypeEngineV2`)                                   | REQUIRED                  | Family subdir enforced by `test_subdir_family_alignment.py` |
| 8   | `strategy_service/.../v2/<family>/__init__.py`                                                                                       | REQUIRED                  | Module re-export                                            |
| 9   | `strategy_service/.../v2/archetype_defaults.py` (`KELLY_FRACTION_BY_ARCHETYPE`, `V1_ARCHETYPES_IN_SCOPE` or `GREENFIELD_ARCHETYPES`) | REQUIRED                  | `KeyError` raised if archetype in scope but missing Kelly   |
| 10  | `strategy_service/.../v2/target_universe/catalog.py` (`_BUILDERS_BY_ARCHETYPE`)                                                      | REQUIRED                  | `KeyError` from `specs_for_archetype()` if absent           |
| 11  | `strategy_service/portfolio_allocator/archetypes.py`                                                                                 | CONDITIONAL               | If archetype needs custom rank allocator                    |
| 12  | `uac/internal/architecture_v2/enums.py` (`AllocatorArchetype`)                                                                       | CONDITIONAL               | If new allocator needed                                     |
| 13  | Run `scripts/propagation/sync-archetype-capability-to-ui.sh`                                                                         | REQUIRED                  | Regenerates `coverage.ts`; UI QG diffs                      |
| 14  | `unified-trading-system-ui/lib/architecture-v2/coverage.ts`                                                                          | REQUIRED (auto-generated) | UI capability matrix                                        |
| 15  | `unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/xyz-foo.md`                                                         | REQUIRED                  | Per-archetype design SSOT (doc → plan → code)               |
| 16  | `deployment-service/scripts/vm/<launcher>.sh`                                                                                        | CONDITIONAL               | If new VM topology / new prefix                             |
| 17  | `deployment-service/scripts/vm/vm_zombie_watchdog.py` (`VM_PREFIX_TO_BUCKET`)                                                        | CONDITIONAL               | If new VM prefix                                            |

**Total: 11 REQUIRED + 6 CONDITIONAL** across **4 repos** (`unified-api-contracts`, `strategy-service`,
`unified-trading-system-ui`, `unified-trading-pm`).

**Verdict: partially centralised, scattered at margins**. Core spine (enum → family → manifest → factory → Kelly →
universe) is disciplined. Touch surface wider than ideal:

1. Manifest is JSON — no type-safe builder; required fields enforced by Pydantic load but no
   `add_archetype_to_manifest()` helper
2. Risk rules are hardcoded tuples; only 2/53 archetypes covered; no QG test requiring `≥1 rule` per archetype
3. Allocator-archetype linkage has no compile-time check between `AllocatorArchetype` and `StrategyArchetype`
4. UI `coverage.ts` sync via external propagation script — possible to update manifest + push without triggering UI
   drift check unless UI's own QG runs

**Consolidation opportunity**: a single `ArchetypeDescriptor` dataclass in UAC capturing family + capability cells +
Kelly tier + risk rules + allocator type in one declaration would reduce touch surface from 11 REQUIRED to 3-4 (enum
value + descriptor + engine class + codex doc).

**Closed-set constraints per archetype family** (where rules are encoded — UAC):

| Family                             | Valid Asset Groups                                                         | Valid Instrument Types                                                   | Settlement Mode                                                  | Required Custody    | INVALID combos                                                                                                                                           |
| ---------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ML_DIRECTIONAL / RULES_DIRECTIONAL | CeFi/DeFi/TradFi/Sports/Prediction                                         | spot, perp, dated_future, option, event_settled                          | continuous (CeFi/TradFi/DeFi) + event_driven (Sports/Prediction) | CLOUD_KMS_ENCRYPTED | No native staking; no LP_POSITION; no LENDING_POSITION                                                                                                   |
| CARRY_AND_YIELD                    | DeFi (stake/lend) + CeFi (perp hedge) + TradFi (dated futures basis)       | staking, lending, perp, dated_future, LP_POSITION (recursive variants)   | continuous; expiry_driven (dated)                                | CLOUD_KMS_ENCRYPTED | **Sports INVALID** (no funding rate). **Prediction INVALID** (no underlying asset). TradFi options not in scope. DeFi listed options NOT YET in manifest |
| ARBITRAGE_STRUCTURAL               | CeFi + DeFi + CROSS_CATEGORY (cross_domain_event)                          | spot, perp, dated_future, lp, option, event_settled (cross-domain)       | immediate; event_driven                                          | CLOUD_KMS_ENCRYPTED | MEV sandwich theoretical-only — NOT in `ARCHETYPE_ENGINE_REGISTRY`                                                                                       |
| MARKET_MAKING                      | CeFi (continuous) + Sports/Prediction (event_settled) + DeFi (LP variants) | perp/spot/option (CeFi); event_settled (Sports/Prediction); lp (DeFi LP) | continuous + event_driven                                        | CLOUD_KMS_ENCRYPTED | TradFi MM in manifest as PARTIAL; Prediction MM has no engine registration                                                                               |
| VOL_TRADING                        | CeFi + DeFi (future) + TradFi                                              | option primary; spot/perp as overlay legs                                | expiry_driven                                                    | CLOUD_KMS_ENCRYPTED | **Sports INVALID** (no options). **Prediction INVALID** (binary ≠ options). No DeFi native options today                                                 |
| STAT_ARB                           | CeFi + DeFi + TradFi                                                       | spot, perp, dated_future                                                 | continuous                                                       | CLOUD_KMS_ENCRYPTED | **Sports/Prediction INVALID** (no mean-reverting price series for event markets)                                                                         |
| PORTFOLIO                          | CROSS_CATEGORY (all 5)                                                     | All (sleeve-level)                                                       | N/A meta-layer                                                   | CLOUD_KMS_ENCRYPTED | No engine registered for any PORTFOLIO\_\* archetype                                                                                                     |
| EVENT_DRIVEN                       | CeFi/DeFi/TradFi/Sports/Prediction (broadest)                              | All                                                                      | mixed                                                            | CLOUD_KMS_ENCRYPTED | None structurally blocked                                                                                                                                |

**Where closed-set constraints are ENFORCED**:

| Enforcement point                                              | What it catches                       | Strength                                                  |
| -------------------------------------------------------------- | ------------------------------------- | --------------------------------------------------------- |
| `ARCHETYPE_ENGINE_REGISTRY` `KeyError`                         | Archetype with no engine              | Runtime — strategy load                                   |
| `V1_ARCHETYPES_IN_SCOPE` + test coverage                       | In-scope but missing Kelly            | Test fails at `quality-gates.sh`                          |
| `test_subdir_family_alignment.py`                              | Engine file in wrong subdir           | Test failure                                              |
| `test_archetype_capability_manifest_parity.py`                 | Manifest family drift from enum map   | Test failure                                              |
| `archetype_capability.py` `_load_registry()` Pydantic validate | Missing/wrong-typed manifest fields   | Module-import `ValidationError` (earliest catch)          |
| `sync-archetype-capability-to-ui.sh` diff in UI QG             | `coverage.ts` out of sync             | UI quality-gates CI                                       |
| `ARCHETYPE_CONCENTRATION_MULTIPLIER`                           | Unknown archetype → silently gets 1.0 | **NOT ENFORCED**                                          |
| `ARCHETYPE_RULES` coverage                                     | New archetype with no risk rules      | **NOT ENFORCED** — no test requires ≥1 rule per archetype |
| `_BUILDERS_BY_ARCHETYPE` `KeyError`                            | Archetype with no catalog builder     | Runtime — universe load                                   |
| `AllocatorArchetype` ↔ archetype binding                      | New archetype with no rank allocator  | **NOT ENFORCED** — falls back to generic                  |
| Codex doc existence                                            | Missing codex doc                     | **NOT ENFORCED**                                          |

### 0.17 Config architecture — hot-reload vs restart + hardcoded value inventory (operator: "any hardcoded values outside config")

**Hot-reload inventory (reloads without VM restart)**:

| Reloader                                                              | File                                                                                                       | Cadence                               | What reloads                                                                                                                                                       |
| --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `ApiKeyReloader` (UTL)                                                | `execution-service/.../config_reloaders.py` L175-217                                                       | **300s (5min) periodic re-fetch**     | Per-venue API keys; callback updates live connector via `connector.update_credentials(...)`                                                                        |
| `DomainConfigReloader` (strategy + instrument + client + rate-limits) | `strategy-service/.../config_reloaders.py` L150-186 + `execution-service/.../config_reloaders.py` L119-157 | **PubSub object change (push)**       | Strategy + instrument domain configs; atomic module-level swap; delta-diff for added/removed instruments → notifies `_instrument_change_callbacks`                 |
| `VersionGovernanceReloader`                                           | `strategy-service/.../config_reloaders.py` L215-305                                                        | 300s poll                             | Strategy version promotion (`ROLLED_OUT` versions with `rolled_out_at > _last_poll`)                                                                               |
| `StrategyDirectiveReloader` (push-based)                              | `strategy-service/.../config_reloaders.py` L328-427                                                        | 60s TTL eviction poll                 | `ArchetypeAllocationDirective` from trading-agent-service; `inject_directive(directive)` push from subscriber; absent directive leaves static `weight()` unchanged |
| `WalletCustodyReloader`                                               | `execution-service/.../custody/cloud_kms.py`                                                               | GCS poll via `ApiKeyReloader` pattern | Per-wallet signing surface flip (CLOUD_KMS_ENCRYPTED → COPPER_MPC); emits `WALLET_CUSTODY_PROVIDER_RELOADED`                                                       |
| Instrument universe deltas (Phase 2B)                                 | `strategy-service/.../config_reloaders.py` `_on_instruments_reload`                                        | Triggered by `DomainConfigReloader`   | Engines receive `_instrument_change_callbacks(added, removed)` — add new DeFi pools, remove expiring futures in-process                                            |
| ML model artifact hot-reload                                          | `MinimalCandidateManifest` field `live_hot_reload_cadence_days: int = 7`                                   | Per-archetype configurable            | **Scheduling hint, NOT in-process model-weight hot-swap.** Reload goes through redeployment or batch artifact rewrite + DomainConfigReloader                       |

**Restart-required surfaces (require VM redeploy)**:

| Surface                                                                                                            | Why                                                                              |
| ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| New `StrategyArchetype` enum value                                                                                 | UAC version bump → strategy-service redeploy                                     |
| New `DefiErrorCode`                                                                                                | Error classification dispatch built at import                                    |
| New venue capability declarations (`CHAIN_RPC_TEMPLATES`, `VENUE_COLLATERAL_MATRIX`, `accepted_perp_collateral()`) | Module-level constants in UAC                                                    |
| New risk rule class / circuit-breaker type                                                                         | Per-class dispatch registered at import                                          |
| Manifest schema changes (schema_version bump)                                                                      | Schema frozen at write path compile time                                         |
| `data_type` registration                                                                                           | Factory/dispatcher registries built at import                                    |
| Python archetype engine code changes (e.g. `staked_basis.py`)                                                      | Process-loaded; only re-applies on restart                                       |
| `DEFAULT_INTERVAL_SECONDS` changes in reloaders                                                                    | Compile-time constants                                                           |
| `ArchetypeSlotMapping` entries in `archetype_slot_resolver.py`                                                     | Catalog built at service boot                                                    |
| `KELLY_FRACTION_BY_ARCHETYPE`                                                                                      | Module constant; no live-reload path                                             |
| Mode flag (`--mode`, `--execution-provider`)                                                                       | CLI flag at startup; cannot be hot-flipped (per HARD RULE batch=live structural) |

**Hardcoded value inventory (outside config; should be config-driven)**:

| File:line                                                                                                                                                                            | Value                                                                                                             | Classification                                                                                            | Should own                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| [`execution-service/.../transfer_handler.py:150-152`](../../../execution-service/execution_service/engine/handlers/transfer_handler.py#L150)                                         | `gas_estimate = Decimal("21000")`, `gas_price_gwei = Decimal("30")`                                               | **BUG**                                                                                                   | `GasEstimateConfig` with per-chain default gas units + `gas_oracle_url`, hot-loaded from domain config |
| [`execution-service/.../transfer_handler.py:44-66`](../../../execution-service/execution_service/engine/handlers/transfer_handler.py#L44)                                            | `_WITHDRAWAL_FEES` flat dict (BINANCE/BYBIT/OKX hardcoded)                                                        | **BUG** — file comment says "would be fetched dynamically"                                                | CCXT `fetch_withdrawal_fees()` or `RateLimitDomainConfig` hot-reload                                   |
| [`alerting-service/.../rules/defi_rules.py:137`](../../../alerting-service/alerting_service/rules/defi_rules.py#L137)                                                                | `_WEETH_DEPEG_THRESHOLD_PCT = Decimal("2.0")`                                                                     | **BUG** — Aave utilization was migrated to `ALERT_THRESHOLDS` in UAC but these were not                   | Migrate to UAC `ALERT_THRESHOLDS`                                                                      |
| [`alerting-service/.../rules/defi_rules.py:240-241`](../../../alerting-service/alerting_service/rules/defi_rules.py#L240)                                                            | `_RATE_DEVIATION_WARNING_BPS = Decimal("50")`, `_RATE_DEVIATION_CRITICAL_BPS = Decimal("200")`                    | **BUG**                                                                                                   | UAC `ALERT_THRESHOLDS`                                                                                 |
| [`strategy-service/.../carry_and_yield/staked_basis.py:251-252`](../../../strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py#L251)               | `entry_bps = Decimal("200")`, `exit_bps = Decimal("50")` defaults                                                 | **DEFAULT** (correct pattern via `decimal_param`; overridable per instance)                               | —                                                                                                      |
| [`strategy-service/.../arbitrage_structural/price_dispersion.py:201`](../../../strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py#L201) | `min_bps = Decimal("30")` default                                                                                 | **DEFAULT** (overridable)                                                                                 | —                                                                                                      |
| `strategy-service/.../carry_and_yield/dynamic_hedge_ratio.py:81`                                                                                                                     | `DEFAULT_PEG_DRIFT_THRESHOLD_BPS = Decimal("25")`                                                                 | **DEFAULT** (injected as param; overridable)                                                              | —                                                                                                      |
| `strategy-service/.../carry_and_yield/staked_basis.py:214`                                                                                                                           | `stake_fraction = Decimal("1.0")`                                                                                 | **DEFAULT (intentional)** — LST_AS_MARGIN structure has no reason for `f < 1.0`                           | —                                                                                                      |
| [`strategy-service/.../archetype_slot_resolver.py:109,519,551,873`](../../../strategy-service/strategy_service/engine/strategies/v2/archetype_slot_resolver.py#L109)                 | `"target_leverage": "5.0"` in `initial_config` for APD                                                            | **CONFIGURABLE BUT INLINE** — should be promoted to operator-editable `StrategyDomainConfig` override key | `archetype_overrides.arbitrage_price_dispersion.target_leverage`                                       |
| `strategy-service/.../shadow_deployment.py:58-59,269-270`                                                                                                                            | `max_pnl_dispersion_bps = Decimal("50")`, `max_fill_dispersion_bps = Decimal("15")` defaults; strict variant 25/8 | **DEFAULT** (dataclass overridable)                                                                       | —                                                                                                      |
| `alerting-service/.../rules/defi_rules.py:51-53` HF thresholds                                                                                                                       | Health factor thresholds via `get_liquidation_params(margin_model)` from UAC `LIQUIDATION_PARAMS_REGISTRY`        | **CORRECT** (not inlined; comment is explicit)                                                            | —                                                                                                      |
| `strategy-service/.../archetype_defaults.py` Kelly tiers                                                                                                                             | Named constants (`_TIER_STABLE_STRUCTURAL=0.500`, etc.) overridable via `initial_config`                          | **CORRECT** (intentional firm-wide defaults)                                                              | —                                                                                                      |

**`os.getenv` violations** (per HARD RULE "No `os.getenv()` — use `UnifiedCloudConfig`"):

- Legitimate exemptions annotated `# config-bootstrap:` (UTL `_env_bootstrap.py`, cloud factory, event_sink,
  manifest_writer for VM identity)
- **Actual violations** (unannotated, prod code):
  - `unified-trading-api/.../routes/health.py:112,128` — `os.environ.get("LIVE_SERVICE_BASE_URL")` in live route handler
    — should use `UnifiedCloudConfig`
  - `unified-trading-api/.../main.py:88,94,160` — `DART_EXCLUSIVE_ENABLED`, `MOCK_STATE_MODE`, `MOCK_LATENCY_MS` —
    dev-only flags, borderline
  - `market-tick-data-service/.../tardis_adapter.py:1531` — `TARDIS_STREAMING_FINALIZE` — should be `TardisConfig` field

**Config-driven hot-reload happy path** (worked example — `entry_bps` 200→250 for `carry_staked_basis`):

1. Operator writes updated config to GCS `gs://<config_store_bucket>/domains/strategies/`
2. GCS object change → PubSub `config-updates` topic
3. `DomainConfigReloader` receives PubSub message → `_on_strategies_reload(config)`
4. Module-level `_active_strategy_config` atomically swapped
5. Next `on_tick()`: `V2EngineOrchestrator._tick_one_engine()` reads `self.params` from refreshed instance definition
6. `_preflight()` in `staked_basis.py` calls `decimal_param(params, "entry_bps", Decimal("200"))` → picks up 250

**Time to pick up**: <5s in prod (PubSub p99 delivery).

**Failure modes**:

- **PubSub delivery failure → config NEVER reloads until next restart**. No polling fallback for `DomainConfigReloader`
  (contrast: `ApiKeyReloader` has 300s periodic). **P1 reliability gap.**
- Invalid YAML → `classify_and_emit_error` per shard isolation; old `_active_strategy_config` remains; **silent stale**.
  No loud failure to operator.
- Partial reload: not possible per atomic GCS object semantics; each domain has own object.

**No `CONFIG_DRIFT_DETECTED` event** — if intended change fails to propagate (PubSub miss, GCS write failed, invalid
YAML silently rejected), strategy continues stale with no operator-visible signal beyond absence of `CONFIG_CHANGED`.
Master plan should codify continuous-verification contract: emit `CONFIG_STALENESS_WARNING` when active config
`last_reloaded_at` exceeds 2× expected reload cadence.

---

## Audit dimensions — per archetype

For EVERY archetype in `codex/09-strategy/architecture-v2/archetypes/` (and any in
`strategy_service/strategy_service/engine/strategies/v2/`), produce a 20-dim audit row:

### 1. WHAT + WHERE

- Canonical archetype name + alpha hypothesis (one paragraph)
- File path (strategy-service implementation)
- Codex doc path (the archetype's design SSOT)
- Active / paper / shadow / scaffolded / archived status

### 2. DATA INPUTS

- Per-feature dependency (which features-service streams consumed)
- Per-MTDS data_type dependency (raw market data needs)
- Per-IS reference dependency (instrument metadata needs)
- Required vs optional inputs (graceful degradation behavior)
- `available_at` discipline (does it respect point-in-time? backtest-safe?)
- Per-input freshness threshold (when is data too stale to act on?)

### 3. PnL + BALANCES + ATTRIBUTION

- PnL calculation: realized + unrealized, per-leg + per-pair
- Balance tracking: how positions are reconciled with venue/wallet state
- Attribution rules: how PnL is split when multi-leg / multi-venue / multi-allocation
- Emission contract: does the archetype publish PnL on the new `strategy_pnl_stream` shape (per trading-agent unlock
  plan)?
- Drift detection: does internal balance state get reconciled against on-chain / venue state? Cadence?

### 4. CAPITAL HANDLING

- **Fund-style** (pooled capital across all clients):
  - How is gross exposure capped?
  - How are entry/exit timed to minimize market impact across pool?
  - How are realized PnL distributions allocated to client units?
- **SMA-style** (per-client segregated accounts):
  - How is per-client capital tracked?
  - How are orders split across accounts (proportional / threshold / sequential)?
  - How are fees + slippage attributed per-account?
- **Treasury flows**:
  - Deposit handling (how does new capital enter the strategy?)
  - Withdrawal handling (how is capital released back?)
  - Rebalance flows (how are inter-archetype allocations moved?)
  - Fee + funding flows (where does fee revenue / funding payment land?)

### 5. UNIVERSE ENUMERATION

- At decision time T, what's the set of viable instrument-tuples?
- Multi-venue example (funding rate arb): list of CEX venues × set of symbols = candidate pairs
- Multi-archetype universe: what's the cross-product across LST pools × CEX perp venues for staked basis?
- Filter rules: liquidity floor, freshness floor, event filter (depeg, funding cap, etc.)
- Is the universe enumeration WHERE? — in features-service (per the cross-asset decision) or in the strategy itself?

### 6. SIZING + RISK

- Sizing rule: Kelly / fixed-frac / risk-parity / volatility-targeted / equal-weight
- Per-leg size derivation (how is the leg ratio computed for multi-leg?)
- Max position size + max gross exposure
- Per-trade risk budget (% of capital at risk per trade)
- Stop-loss / take-profit logic if any
- Correlation aware? (do positions across archetypes adjust for cross-correlation?)

### 7. REBALANCING + LIFECYCLE

- Entry signal + entry cadence
- Hold period (continuous re-evaluation vs fixed-tenure)
- Rebalance triggers (drift % / time / regime change / volatility breach)
- Unwind triggers (PnL exit / stop / archetype turn-off via directive)
- Roll handling (for futures + perp expiries)

### 8. NEUTRALITY + DIRECTIONALITY

- Delta neutrality: how is it computed + maintained?
- Asset-class neutrality: is the archetype neutral across crypto / FX / commodity / equity?
- Direction: long-only / short-only / market-neutral / dynamic?
- Hedge leg specification: who chooses the hedge venue + hedge instrument?
- Beta-to-market / beta-to-asset-class: what's the residual?

### 9. VENUE RESTRICTIONS (operator focus 2026-05-20 round 6 — "the math is easy")

- Per-venue allow-list / deny-list per client_id (UK clients can't access Extended Starknet; Cayman clients can; etc.)
- Per-venue jurisdiction tags + auto-enforcement at order-construction time (UAC `client_funds_isolation` rule extends)
- Per-venue MAX position limit + MAX gross exposure
- Per-venue trading hours overlay (which archetypes can run during which venue's session?)
- Per-venue credential health gate (if API key revoked or rate-limited mid-day, what happens?)
- Per-(venue, instrument) blacklist (e.g. delisted, paused, low-liquidity)
- **Test**: what does the archetype do when 2/3 venues for a multi-venue arb are restricted for the active client?

### 10. COLLATERAL MANAGEMENT (operator focus)

- Per-venue collateral type registry (stablecoin / native / LST-as-collateral)
- Collateral haircut + LTV per venue (matches venue's actual risk params)
- Cross-margin vs isolated-margin choice per archetype × venue
- Collateral substitution (when can stETH replace ETH as collateral?)
- Collateral rebalancing triggers (LTV drift > X% → top up / reduce)
- DeFi-specific: liquidation health factor monitoring (Aave / Compound `getUserAccountData` reads)
- CeFi-specific: maintenance margin proximity alerts
- **Test**: at decision time, does the archetype know its current collateral position per venue + can it size correctly?

### 11. LIQUIDATION MANAGEMENT (operator focus)

- Per-archetype liquidation distance threshold (health factor ≤ X.X triggers action)
- Pre-liquidation action: deleverage / top-up collateral / unwind position
- Liquidation cascade detection: if one leg liquidates, what happens to the hedge leg?
- Mark-price vs index-price awareness (perp venues liquidate on mark; on-chain liquidates on oracle)
- Oracle freshness gate (Chainlink heartbeat < N min for the archetype's collateral assets)
- Per-venue liquidation fee + skip risk
- Recursive-loop archetypes: per-iteration liquidation health calc (e.g. Aave looping)
- **Test**: under flash-crash scenario, what's the archetype's pre-liquidation playbook + does the directive bus get the
  right signals fast enough?

### 12. CROSS-VENUE TRANSFERS (operator focus)

- Permitted transfer pairs per client (intra-client only per CLAUDE.md `Client funds isolation` HARD RULE)
- Transfer-window awareness (e.g. CEX withdrawal blackouts on Mondays UTC)
- Bridge-time tolerance per chain (Ethereum withdraw 7d challenge period, Arbitrum 7d, Optimism 7d, etc.)
- Stablecoin vs native asset transfer-cost calculus (USDC bridge vs ETH bridge)
- Failed-transfer reconciler (transfer initiated but didn't arrive within window → alert + manual ack)
- Sub-account move logic (CEFI internal: Binance spot → Binance futures sub-account)
- Per-leg dependency: if archetype needs cross-venue transfer to size correctly, what's the fallback if transfer fails?
- **Test**: a multi-venue staked-basis archetype needs to move stETH from Lido custody to a CEX as collateral — does the
  cross-venue transfer path exist + is it auditable?

### 13. ALLOCATION-BASED REBALANCING (operator focus — "most of the focus")

- Per-archetype target allocation % (of total client capital)
- Cross-archetype rebalance trigger: drift % / time / regime
- Allocation source-of-truth: `portfolio_allocator` (strategy-service)? `client_share_classes`? both?
- Per-(client, archetype) override (a client opts out of `recursive_lending` but in for `staked_basis`)
- Closed-loop feedback: realised PnL flows back to update allocations? Cadence?
- Cross-asset-group allocation (cefi 50% / defi 30% / sports 20% per client) — how surfaced in deployment?
- Forced-deallocation when an archetype is paused (capital returns to cash; what's the holding venue?)
- **Test**: when operator adds a new client mid-day with target allocation (40% cefi, 60% defi), does the allocator
  detect + rebalance without manual intervention?

### 14. DEPLOYMENT TOPOLOGY — DYNAMIC CONFIG + ACCOUNTS / CLIENTS (operator focus)

- Adding a new client mid-day: which configs hot-reload? Which require VM restart?
- Adding a new account (sub-account) to existing client: account discovery path + credential injection
- Removing a client: graceful unwind (don't strand positions); position liquidation pathway
- Removing an account: ditto
- Adding a new venue: config hot-reload OR VM redeploy?
- Per-archetype enable/disable from operator UI (directive bus): cadence to take effect
- Per-(archetype, asset_group) enable/disable (e.g. pause arb_price_dispersion on DeFi but keep CeFi running)
- Config drift detection: if `cloud-providers.yaml` or `client_share_classes.yaml` changes, do running VMs reload?
- Health-API endpoint per service reflects current client/account count + per-archetype state
- **Test**: with 3 archetypes running on 2 clients, operator adds a 3rd client + a new archetype simultaneously — does
  deployment topology absorb without restart?

### 15. DECISION-MAKING ALGORITHM (verification — operator focus 2026-05-21)

- The exact code path from feature input → signal generation → instruction emission per archetype at tick T
- For "best funding rate to ARB" type questions: which `PairSelectionMode` is used, what filters, what sizing
- Multi-coin weighting: per-archetype Kelly fraction (from `archetype_defaults.py`), per-asset `AllocationSizer`
  fan-out, share-class FX via `ShareClassFxMatrix`
- Cross-venue weighting: how `venue_universe` config field maps to per-venue notional
- Reproducibility: given identical features, does the archetype produce identical instructions across runs? Any
  non-determinism (`dict` ordering, random tie-break)?
- **Test**: replay 5 identical feature dicts through the archetype's `on_tick`; assert instruction lists are
  byte-identical.

### 16. UNIVERSE ENUMERATION ARCHITECTURE

- Per-archetype universe entry point (`target_universe/catalog.py` `_build_carry_staked_basis()` /
  `_build_arbitrage_price_dispersion()`)
- Is the universe derived from `instruments-service` `InstrumentRecord` (HARD RULE) or directly from UAC
  `VENUE_COLLATERAL_MATRIX` (current implementation outlier)?
- Per-(asset_group, archetype) pre-flight gate before a slot appears in allocator's eligible universe
- **Gap**: no features-service universe contract codified (one of 5 missing design contracts identified in §0.5)
- **Test**: enumerate slots for `carry_staked_basis` + `arbitrage_price_dispersion`; verify each slot has a
  corresponding `InstrumentRecord` in IS; flag orphans

### 17. CAPITAL HANDLING ARCHITECTURE (fund-style vs SMA-style + treasury sweep — operator focus)

- **Fund-style** (pooled): gross exposure cap, entry/exit timing for market impact, realized PnL → client unit
  distribution
- **SMA-style** (per-client segregated): per-client capital tracking, order split (proportional/threshold/sequential),
  per-account fees+slippage attribution
- **Treasury flows** (3 capital-flow scopes per codex):
  - **Venue scope** (intra-strategy): Transfer/Rebalance service via TRANSFER/BRIDGE instructions
  - **Strategy scope** (intra-client): Portfolio Allocator via `AllocationDirective`
  - **Client scope** (deposits/withdrawals): Platform treasury + onboarding events (`CLIENT_DEPOSIT`,
    `CLIENT_WITHDRAWAL`)
- **Capital event interface**: uniform `deposit/withdraw/rebalance` contract consumed by every archetype? If not, who
  currently implements each shape?
- **Cross-share-class NAV conversion**: who computes? cadence?
- **Test**: a $1M deposit at T=0 lands as TREASURY → triggers sweep → arrives at hot wallets → strategy sees increased
  `trading_balance_usd`. End-to-end auditable in event archive within 1 tick.

### 18. BATCH=LIVE PARITY (mode-leak audit)

- For every code path in strategy + execution, does ANY logic depend on `mode == "batch"` / `mode == "live"` /
  `execution_provider`?
- Where do separate `batch/` vs `live/` directories exist (e.g. `execution_service/engine/modes/`)? For each, is parity
  tested?
- Mock-mode pollution: is `CLOUD_MOCK_MODE=true` legitimately scoped (storage emulator only) or does it leak into
  business logic?
- Empty-features silent passthrough (`{}` continues): is there a monitoring signal for feature-fetch failures?
- `available_trading_capital_usd` sizing divergence between batch and live (gas depletion patterns differ) — is this
  documented?
- **QG STEP 5.77 audit**: declared "active workspace-wide" but no script found — verify or land the script
- **Test**: run identical strategy + identical features through batch mode and paper mode (Tenderly fork dry-run);
  assert emitted `TradeInstruction` lists are identical (modulo `executed_at` timestamp)

### 19. MOCK-DATA TESTING SURFACE (per archetype)

- For each archetype, can a synthetic feature dict be constructed that drives a non-trivial `on_tick` decision?
- For multi-leg archetypes: is the leg ratio derivation testable with mock data alone, or does it require live oracle
  reads?
- For DeFi archetypes: can Tenderly fork fixtures cover the SWAP→STAKE→HEDGE path end-to-end?
- For CeFi archetypes: are CCXT mock adapters wired (vs CCXT live)? — **CURRENT GAP**: `LiveCcxtTransferAdapter` methods
  are stubs ("not yet wired") — P0 blocker for live CeFi
- For ML-dependent archetypes (`ml_directional_continuous`): can `MLPrediction` be injected via mock seed bypassing
  PubSub?
- **Required artifacts per archetype**: (a) synthetic feature factory, (b) golden-input → golden-output fixture, (c)
  Tenderly fork setup if DeFi-leg, (d) mock CCXT adapter if CeFi-leg

### 20. STRATEGY SERVICE POST-CONSOLIDATION CLEANLINESS

- Stale comments / docstrings post-consolidation (e.g. `__init__.py` stale "18 archetype engines" claim)
- Dead code from removed structures (e.g. `SPLIT_STAKE` removed 2026-05-05 — any orphan references?)
- Half-consolidated state (risk/position/pnl services merged 2026-05-19 — Phase 11 stale-ref cleanup status)
- Shadow mode default (`V2ShadowRunner.shadow_mode=True`) — when does it flip? what's the test?
- Outlier engines (`ArbitragePriceDispersionHierarchicalEngine` — in code but not in registry)
- Duplication candidates (5 listed in §0.3 above)
- **Test**: workspace-wide grep for `_archived_pre_v2`, `SPLIT_STAKE`, `COLLATERAL_BORROW`, `leveraged_funding_arb`,
  `URDI`, `Elysium`, `Arkham`, `Bloxroute`, `Infura` — any hits in `live/` code are stale and must be removed

### 21. CENTRALISATION + INHERITANCE VERIFICATION (operator focus 2026-05-21 — "is risk like liquidation risk managed in one place")

Per §0.11 above, the strategy service post-consolidation has a CENTRALISED / PER-ARCHETYPE / STRATEGY-AGNOSTIC split.
For each archetype, verify:

- Does it correctly inherit the 7-axis risk registry
  (global/venue/account/asset_group/client/strategy_family/archetype)?
- Does it use `compute_pnl_breakdown()` for PnL attribution (universal) or roll its own?
- Does it use `TreasuryMonitor` for treasury/trading wallet split, or maintain own ledger?
- Does it correctly publish `MarginEvent` via the central `margin_event_emitter`, or emit its own?
- Does it use the central `DeleverageExecutor` for pre-liquidation actions, or per-archetype handler?
- Does it have an entry in `ARCHETYPE_RULES` (UAC)? In `ARCHETYPE_KILL_SWITCH_THRESHOLDS` (service-local)? In
  `ARCHETYPE_CONCENTRATION_MULTIPLIER`?
- For DeFi archetypes: is liquidation monitored by `HealthFactorMonitor` (Aave/EVM only) or does it need a per-protocol
  monitor (Solana lending: Marginfi/Kamino/Sanctum)?
- For multi-leg archetypes: how is cross-leg cascade unwind handled? (per-archetype today; no framework primitive)
- **Test**: grep for archetype-local risk / PnL / treasury / margin logic; should be near-empty post-consolidation. Any
  per-archetype helpers that re-implement central infrastructure → consolidation candidate.

### 22. MODULARITY + NEW-ARCHETYPE TOUCH SURFACE (operator focus — "does someone need to touch only one set of modules or several")

Per §0.16 above, adding a new archetype touches **11 REQUIRED + 6 CONDITIONAL files across 4 repos**. Verify:

- Is the engine class in the correct family subdirectory (enforced by `test_subdir_family_alignment.py`)?
- Is the manifest cell consistent with `ARCHETYPE_TO_FAMILY` (enforced by
  `test_archetype_capability_manifest_parity.py`)?
- Does it have a Kelly fraction (`KELLY_FRACTION_BY_ARCHETYPE`)?
- Does it have a catalog `_build_X` function (`_BUILDERS_BY_ARCHETYPE`)?
- Does it have a codex doc (NOT enforced — gap)?
- Does it have risk rules (NOT enforced — gap; only 2/53 archetypes covered)?
- Does it have a concentration multiplier (defaults to 1.0 silently — gap)?
- Are closed-set constraints (asset_group / instrument_type / share class / venue) declared in the capability manifest
  cells? Are INVALID combos enforced at preflight (instruction validator via
  `capability_for(archetype).supported_pairs`)?
- **Test**: simulate adding a hypothetical `XYZ_FOO` archetype + verify exactly which files raise on import / test
  runtime errors. Document the failure cascade. Identify gaps where the system should fail-loud but silently accepts
  defaults.

### 23. CONFIG DRIVE-ABILITY + HOT-RELOAD vs RESTART (operator focus — "any hardcoded values outside config, how does config drive things with hot reload, what requires service restart")

Per §0.17 above, the workspace has hot-reload paths (`ApiKeyReloader` / `DomainConfigReloader` /
`StrategyDirectiveReloader` / `WalletCustodyReloader`) and restart-required surfaces. Verify per archetype:

- Every threshold / fee / leverage / timeout / BPs constant in archetype source: is it `decimal_param`-overridable (via
  `StrategyInstanceDefinition.params`) or hardcoded?
- For each hardcoded value: is it CORRECT (protocol-defined, immutable), DEFAULT (reasonable default + overridable), or
  BUG (should be config-driven)?
- Where do archetype params live? (UAC strategy domain config / per-instance YAML / inline catalog default?)
- Does the archetype use any `os.getenv()` outside `# config-bootstrap:` annotated paths? (HARD RULE violation per
  CLAUDE.md)
- Hot-reload propagation: a config change from operator should reach the running engine in <5s via PubSub →
  `DomainConfigReloader` → atomic config swap. Verify this path per archetype.
- Restart-required changes: enum additions, schema changes, Python code changes, manifest schema bumps, data_type
  registrations, ArchetypeSlotMapping. Verify the archetype's params don't accidentally require restart for what should
  be hot-reloadable.
- **`CONFIG_DRIFT_DETECTED` observability gap**: there is no event emitted when a config change fails to propagate.
  Verify whether the archetype emits `CONFIG_CHANGED` events on reload; if absent, a silent-stale config bug is
  invisible to monitoring.
- **`DomainConfigReloader` polling-fallback gap**: PubSub-only push; if delivery fails, config never reloads until
  restart. P1 reliability gap. Verify per archetype: does the archetype tolerate a 5-minute stale config window without
  silently mispricing?
- **Test**: enumerate every BPs / timeout / leverage / fee constant in the archetype file; classify each as CORRECT /
  DEFAULT / BUG. Any BUG entries are remediation items for the master strategy plan.

## Audit findings shape (per dimension, per archetype)

1. **Design vs implementation gap table**: per dimension (1-23), what does the design SSOT say vs what does the code do?
   Surface every drift.
2. **Per-dimension risk register**: list every "missing handler" / "wrong default" / "silent fallback" the archetype has
   that would surface as a P0 in live trading.
3. **R-items for operator delegation**: each gap → a remediation item with target slot + estimated effort. Matches the
   mega-audit § 6 delegation SSOT format.
4. **Pre-live trading gate**: any gap in dimensions 9-14 (venue restrictions / collateral / liquidation / cross-venue
   transfer / allocation rebalancing / deployment topology) OR dimensions 15-18 (decision algo / universe enum / capital
   handling / batch=live parity) OR dimensions 21-23 (centralisation inheritance / modularity / config drive-ability) is
   **P0 cutover-blocking** for the affected archetype.

## Archetype inventory (to be confirmed during audit Phase 0)

Provisional list from codex + strategy-service:

| Archetype                                 | Asset group(s)          | Status      | Live mode by 2026-05-23? |
| ----------------------------------------- | ----------------------- | ----------- | ------------------------ |
| `carry_staked_basis`                      | DeFi + CeFi (hedge leg) | live target | YES                      |
| `arbitrage_price_dispersion`              | DeFi or CeFi or cross   | live target | YES                      |
| Multi-venue funding rate arb              | CeFi (cross-venue)      | scaffolded? | post-cutover             |
| Calendar / term basis                     | CeFi futures            | scaffolded? | post-cutover             |
| Stat arb / pairs (CeFi)                   | CeFi                    | scaffolded? | post-cutover             |
| Sports arb (e.g. inter-book arb)          | Sports                  | scaffolded? | post-cutover             |
| Sports value (model edge)                 | Sports                  | scaffolded? | post-cutover             |
| Polymarket / Kalshi arb                   | Prediction              | scaffolded? | post-cutover             |
| TradFi carry (e.g. VX term structure)     | TradFi                  | scaffolded? | post-cutover             |
| TradFi vol (e.g. variance / VIX)          | TradFi                  | scaffolded? | post-cutover             |
| TradFi momentum / trend                   | TradFi                  | scaffolded? | post-cutover             |
| LST yield arb (DeFi-internal)             | DeFi                    | scaffolded? | post-cutover             |
| Lending rate arb (Aave / Compound / etc.) | DeFi                    | scaffolded? | post-cutover             |

Phase 0 of this audit = enumerate the actual inventory + confirm status. Codex `architecture-v2/archetypes/` directory
is the SSOT.

## Cross-cutting questions (expanded 2026-05-21)

Beyond per-archetype audits, surface workspace-wide patterns:

- **Universe-enumeration consistency**: do all multi-venue archetypes get their universe from features-service (per the
  cross-asset decision)? Any outliers re-deriving from raw MTDS / IS / directly from UAC?
- **PnL emission uniformity**: do all archetypes use the same emission shape (`StrategyPnlStreamEvent` /
  `PnLAttributionRow`)? Or do they roll their own? **Current state: both May-23 archetypes emit zeros TODO
  post-cutover.**
- **Sizing rule diversity**: how many distinct sizing implementations exist? Any duplication? Any that should be
  promoted to a shared lib?
- **Attribution split logic**: is per-leg PnL attribution implemented uniformly, or are there inconsistencies?
- **Fund vs SMA handling**: is there a single shared client-split layer, or does each archetype implement its own?
- **Treasury flow contract**: is there a uniform "capital event" interface (deposit/withdraw/rebalance) consumed by
  every archetype?
- **Allocator pipeline contract** (NEW): `trading-agent-service → strategy-service → execution-service` — is the
  directive shape canonical? No codex contract for post-cutover production allocation logic.
- **Decision loop SSOT per archetype** (NEW): no doc specifies the canonical "on_tick" path per archetype at paper vs
  live mode.
- **Instrument type × leverage matrix** (NEW): no machine-verifiable
  `archetype × asset_group × instrument_type → (venue, max_leverage, expression, settlement)` table.
- **Treasury / trading wallet / client wallet isolation per asset class** (NEW): no single doc establishes the
  audit-verifiable invariant: "for each live strategy at any instant, what wallet address is the strategy's capital at,
  who has signing authority, what's the max capital exposure".

## Active plans inventory + dependencies (added 2026-05-21)

**Spine plans for strategy archetype work (10 most important)**:

1. [strategy_and_dart_master_SUPERSEDED_2026_05_21.md](../../epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md) —
   primary epic SSOT; Phases 1.2/1.4/1.6/1.7/1.8/1.9 all open
2. THIS DOC — `strategy_archetype_logic_audit_2026_05_20.md`
3. [trading_agent_service_architecture_unlock_2026_05_22.md](../trading_agent_service_architecture_unlock_2026_05_22.md)
   — closed-loop allocator wiring; deadline 2026-05-22; trading-agent QG currently RED
4. [defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md](../defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
   — completed; venue-collateral matrix foundation
5. [per_client_isolation_and_venue_fanout_topology_2026_05_20.md](../per_client_isolation_and_venue_fanout_topology_2026_05_20.md)
   — only 1/12 done, critical for cutover; owns Phase E.3 `IntraClientRebalanceCoordinator`
6. [strategy_execution_contract_remediation_2026_05_20.md](../strategy_execution_contract_remediation_2026_05_20.md) —
   manifest emission gap (orphan in master plan); 81% done
7. [defi_recursive_borrow_archetypes_2026_05_10.md](../defi_recursive_borrow_archetypes_2026_05_10.md) — 100% done but
   READY-TO-GO at cutover (live toggle OFF)
8. [phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md](../phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md)
   — 32/37 done; blocks paper VM fills>0
9. [strategy_archetype_taxonomy_2026_05_12.md](../strategy_archetype_taxonomy_2026_05_12.md) — shipped; "share class
   determines neutrality" foundational axiom
10. [promote_workflow_may23_cli_path_2026_05_10.md](../promote_workflow_may23_cli_path_2026_05_10.md) — 66% done; CLI
    cutover vehicle

**In-flight risks** (Phase -1 prereqs):

- `strategy_dydx_venue_token_regression_2026_05_20` — UAC@df2c754 removed dydx from `_DEFI_PERP_TOKENS` but strategy
  catalog still has dydx → 5 test failures → **blocks Phase -1 (workspace QG green)**
- `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16` — trading-agent-service QG RED; unblocking required
  for 2026-05-22 architecture deadline

**Duplications / contradictions across plans**:

- Allocator ownership split across 3 plans (`strategy_and_dart_master` §1.7,
  `trading_agent_service_architecture_unlock`, `per_client_isolation` E.3)
- Rebalancing referenced in 4 plans without single SSOT
- `StrategyPnlStreamEvent` "TODO post-cutover" banners in 3 plans without back-link to the unlock plan that creates the
  contract
- `defi_recursive_borrow` parent plan (100% done) vs post-cutover plan (scope-narrowed) — audit must verify Phase 4
  (Solidity) + Phase 5 (orchestrator) actually landed

**Missing plans** (8 — for a master-strategy-plan equivalent to data pipeline master):

1. `strategy_archetype_master_coordination_YYYY_MM_DD.md` — sequence: Phase -1 (QG green) → Phase 0 (this audit) → Phase
   1 (per-archetype P0 remediation) → Phase 2 (trading-agent allocator dataflow verified) → Phase 3 (per-client
   isolation + venue fanout green) → Phase 4 (paper trade) → Phase 5 (live cutover) → Phase 6 (post-cutover backlog)
2. `capital_handling_and_share_class_ssot_YYYY_MM_DD.md` — fund-style vs SMA-style vs treasury flows;
   deposit/withdraw/rebalance contract; share class × archetype × neutrality derivation
3. `rebalancing_and_allocation_trigger_ssot_YYYY_MM_DD.md` — rebalance trigger taxonomy, closed-loop feedback cadence,
   forced-deallocation
4. `venue_restrictions_and_jurisdiction_enforcement_YYYY_MM_DD.md` — jurisdiction-aware order routing; UK vs Cayman
   entity per venue (P0 pre-live gap)
5. **NEW** `risk_centralisation_and_liquidation_solana_2026_05_2X.md` — extend `HealthFactorMonitor` to Solana lending
   (Marginfi/Kamino/Sanctum); add `ARCHETYPE_KILL_SWITCH_THRESHOLDS` coverage QG step; codify multi-leg cascade unwind
   primitive
6. **NEW** `options_vol_fitter_and_normalised_strike_2026_05_2X.md` — SVI/SSVI parametric fitter; `mark_price → IV`
   inversion; risk-free rate source; `VolTradingOptionsEngine` dynamic strike selection via `StrikeMapper`; live options
   chain pipeline verification; unblocks 17 of 18 vol archetypes
7. **NEW** `archetype_descriptor_consolidation_2026_05_2X.md` — single `ArchetypeDescriptor` dataclass in UAC
   consolidating family + capability cells + Kelly tier + risk rules + allocator type; reduces new-archetype touch
   surface from 11 REQUIRED to 3-4 files; closes the `ARCHETYPE_RULES`/`ARCHETYPE_KILL_SWITCH_THRESHOLDS`/
   `ARCHETYPE_CONCENTRATION_MULTIPLIER`/codex-doc enforcement gaps
8. **NEW** `config_hot_reload_observability_and_polling_fallback_2026_05_2X.md` — `DomainConfigReloader` polling
   fallback (P1 reliability gap — currently PubSub-only push); `CONFIG_STALENESS_WARNING` emission when
   `last_reloaded_at` exceeds 2× cadence; hardcoded-value cleanup (gas estimate / withdrawal fees / WEETH depeg / rate
   deviation thresholds — 4 BUGs in §0.17)

## Audit deliverables (consolidated 2026-05-21)

### Per-archetype audit docs (one per archetype, ~13-28 total depending on scope cut)

- Location: `plans/audit/archetypes/<archetype_name>_2026_05_2X.md`
- Mirrors mega-audit C-audit shape — now **20-dimensional matrix** per archetype (was 14)
- ~1.5-2 calibrated AI-days each for live/paper archetypes; ~0.5d for scaffolded archetypes (smaller scope)

### Cross-cutting findings audit doc (one)

- Location: `plans/audit/cross_cutting_strategy_logic_findings_2026_05_2X.md`
- Workspace-wide patterns + outlier flags + 5 duplication candidates + 5 P0 silent-failure risks (carry-forward from
  §0.3)
- ~2 calibrated AI-days

### Master strategy plan (NEW — parallel to data pipeline master)

- Location: `plans/active/strategy_archetype_master_coordination_YYYY_MM_DD.md`
- Sequences: Phase -1 (workspace QG green prereqs — dydx regression fix, trading-agent QG green) → Phase 0 (this audit)
  → Phase 1 (per-archetype P0 remediation) → Phase 2 (trading-agent allocator dataflow end-to-end) → Phase 3 (per-client
  isolation + venue fanout green) → Phase 4 (paper trade) → Phase 5 (live cutover) → Phase 6 (post-cutover backlog: PnL
  stream enrichment, full CandidateManifest, CEFFU, jurisdiction enforcement)
- Owns the 4 missing plans listed above (capital handling, rebalancing+allocation trigger, venue
  restrictions+jurisdiction, axes hard-rule tables)
- Each phase: owner slot + plan-of-record + verification criterion + Codex SSOT updates
- ~3-4 calibrated AI-days to draft (operator-reviewed; not a sub-agent write)

### Axes hard-rule tables (NEW)

- 8 tables to codify in UAC (per §0.2 above)
- Each: target SSOT file + closed-set members + enforcement (QG step / runtime check) + tests
- Operator-reviewed (axes are decisions, not just collation)

### Codex SSOT updates (MANDATORY — review-blocking if missing)

Codex doc paths this audit will touch:

- `codex/09-strategy/architecture-v2/README.md` — add §0 Map link
- `codex/09-strategy/architecture-v2/category-instrument-coverage.md` — verify completeness vs 53-archetype taxonomy
- `codex/09-strategy/architecture-v2/cross-cutting/strategy-execution-runtime.md` (NEW) — decision loop SSOT per
  archetype
- `codex/09-strategy/architecture-v2/cross-cutting/universe-enumeration-contract.md` (NEW) — features-service ×
  instruments-service × strategy-catalog
- `codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md` (NEW) — trading-agent-service →
  strategy-service post-cutover production logic
- `codex/09-strategy/architecture-v2/cross-cutting/treasury-trading-wallet-invariant.md` (NEW) — audit-verifiable
  wallet/signing/exposure invariant
- `codex/09-strategy/architecture-v2/cross-cutting/instrument-type-leverage-matrix.md` (NEW) —
  `archetype × asset_group × instrument_type → (venue, max_leverage, ...)` table
- `codex/04-architecture/share-class-architecture.md` — un-stale (currently lists 3 share classes; v2 axes doc lists 8)
- `codex/09-strategy/architecture-v2/uac-registry-gaps.md` — resolve 12 unactioned proposals or downgrade to non-binding
- `codex/09-strategy/strategy-summary.md` — remove `vscode-webview://` URL artifact

## Sequencing — when this audit can run (revised 2026-05-21)

**Blocked-on (Phase -1 prereqs — workspace QG green)**:

1. **`strategy_dydx_venue_token_regression_2026_05_20` resolved** — UAC dydx removal needs strategy catalog mirror;
   current state: strategy-service QG FAILING with 5 test failures in `test_target_universe.py`
2. **trading-agent-service QG green** — `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16` unblocked;
   required for 2026-05-22 architecture deadline
3. **Mega audit Phase A (diagnostics)** lands first — gives clean data substrate. Strategy logic audit can't separate
   strategy bugs from data bugs without this.
4. **Mega audit Phase C6 (features→strategy contract audit)** lands — surfaces the per-pair viability + pricing
   ownership contract this audit consumes.
5. **Trading-agent unlock plan Phase 1 (May-23 architecture)** lands — the `strategy_pnl_stream` emission shape is the
   canonical PnL contract the strategy audit uses for dim-3.

**Unblocked-by** (once above land):

- Strategy audit can spawn 13-28 parallel agents (one per archetype), each filling its audit doc against the now-locked
  contracts.
- Cross-cutting findings agent runs after per-archetype agents land, consolidating.
- Master strategy plan written by ikenna (operator judgment on consolidations + 8 hard-rule tables).
- Phase 1 per-archetype P0 remediation (5 P0 items from §0.3) can run in parallel post-audit.

## Foundation-gate alignment

This audit is **layer 6** (strategy + execution) per
`codex/11-project-management/foundation-completion-gate-discipline.md`. Prereqs:

- Layer 1 GREEN (IS hardening — C0/C1/C2/C3 audits)
- Layer 5 GREEN (features → strategy contract — C6 audit)
- Layer 7 architecture unlocked (trading-agent unlock plan Phase 1)

When prereqs green, this audit can run safely. Until then, surfacing strategy bugs would conflate with upstream-data
bugs.

## Out of scope (explicit; some revised 2026-05-21)

- Strategy DEPLOYMENT logic (already in `strategy_and_dart_master` epic)
- Allocator service production logic (covered by trading-agent unlock Phase 1 scaffold + Phase 2 operational)
- Backtest infrastructure (this audit USES backtest results but doesn't build them)
- New archetype design (this audits EXISTING archetypes; new alpha hypotheses are separate work)
- ~~Execution-service logic (the strategy → execution boundary is covered by mega audit C7)~~ **REVISED 2026-05-21**:
  the execution-service **strategy-handoff INTERFACE** (HandlerRegistry dispatch, fill report path, PnL realization
  timing, margin/collateral management for pre-liquidation actions) IS IN SCOPE per §0.8 + §17 + §11. Deep
  execution-service internals (per-venue order routing details, matching engine, CCXT live wiring stubs) remain out of
  scope.
- Live trading risk limits (operator-set; not strategy-internal — but the **AXES of risk per archetype** IS in §10 +
  axis 10)

## Ack triggers (when this issue archives)

Per `codex/11-project-management/issue-doc-lifecycle.md`, this issue archives when:

1. Per-archetype audit docs land in `plans/audit/archetypes/` (~13-28 docs depending on scope cut; 23-dim per archetype)
2. Cross-cutting findings doc lands
3. Master strategy plan lands in `plans/active/strategy_archetype_master_coordination_YYYY_MM_DD.md`
4. 8 axes hard-rule tables codified in UAC (or scoped as DEFERRED in the master strategy plan with operator [ack])
5. 5 P0 silent-failure risks (§0.3) either fixed in code or scoped as `BLOCKED-*` per
   `External Data Is Always Available` rule
6. The 8 "Missing plans" listed in §"Active plans inventory" are either drafted or absorbed into existing plans with
   operator [ack]
7. 4 hardcoded-value BUGs from §0.17 either fixed or filed as remediation items (gas estimate; `_WITHDRAWAL_FEES`;
   `_WEETH_DEPEG_THRESHOLD_PCT`; `_RATE_DEVIATION_*_BPS`)
8. Share class enum collision (§0.13: Enum A 3-value vs Enum B 9-value) reconciled or scoped with operator [ack]
9. `LIVE_DEFI_CUTOVER_ARCHETYPES` stale entry (`leveraged_funding_arb` → `arbitrage_price_dispersion`) fixed in
   `client_share_classes.py` (P0 — pre-May-23)

## Map appendix: code / codex / plan reference

Key paths cited throughout this audit (for fast navigation):

**Code (strategy service)**:

- [`strategy-service/strategy_service/engine/strategies/v2/`](../../../strategy-service/strategy_service/engine/strategies/v2/)
  — archetype implementations
- [`strategy-service/strategy_service/portfolio_allocator/`](../../../strategy-service/strategy_service/portfolio_allocator/)
  — allocator code
- [`strategy-service/strategy_service/position/core/treasury_monitor.py`](../../../strategy-service/strategy_service/position/core/treasury_monitor.py)
  — `TreasuryMonitor`
- [`strategy-service/strategy_service/pnl/engine/orchestrator.py`](../../../strategy-service/strategy_service/pnl/engine/orchestrator.py)
  — PnL orchestrator
- [`strategy-service/strategy_service/engine/mock_data_provider.py`](../../../strategy-service/strategy_service/engine/mock_data_provider.py)
  — full mock e2e pipeline
- [`e2e-testing/scripts/defi/colocated_engine.py`](../../../e2e-testing/scripts/defi/colocated_engine.py) —
  single-process engine; mode dispatch

**Code (execution + UAC)**:

- [`execution-service/execution_service/transfer_coordinator.py`](../../../execution-service/execution_service/transfer_coordinator.py)
- [`execution-service/execution_service/engine/handlers/transfer_handler.py`](../../../execution-service/execution_service/engine/handlers/transfer_handler.py)
- [`execution-service/execution_service/engine/routing/handler_registry.py`](../../../execution-service/execution_service/engine/routing/handler_registry.py)
- [`execution-service/execution_service/custody/factory.py`](../../../execution-service/execution_service/custody/factory.py)
- [`execution-service/execution_service/algo_library/deleverage_executor.py`](../../../execution-service/execution_service/algo_library/deleverage_executor.py)
- [`unified-api-contracts/unified_api_contracts/canonical/crosscutting/availability_semantics.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/availability_semantics.py)
- [`unified-api-contracts/unified_api_contracts/canonical/domain/features/required_inputs.py`](../../../unified-api-contracts/unified_api_contracts/canonical/domain/features/required_inputs.py)
- [`unified-api-contracts/unified_api_contracts/registry/venue_collateral.py`](../../../unified-api-contracts/unified_api_contracts/registry/venue_collateral.py)
- [`unified-api-contracts/unified_api_contracts/registry/cefi_margin_tiers.py`](../../../unified-api-contracts/unified_api_contracts/registry/cefi_margin_tiers.py)
- [`unified-api-contracts/unified_api_contracts/registry/risk_rules/archetype.py`](../../../unified-api-contracts/unified_api_contracts/registry/risk_rules/archetype.py)
- [`unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py`](../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py)
- [`unified-api-contracts/unified_api_contracts/registry/archetype_capability_matrix.py`](../../../unified-api-contracts/unified_api_contracts/registry/archetype_capability_matrix.py)
- [`unified-api-contracts/unified_api_contracts/registry/taxonomy.py`](../../../unified-api-contracts/unified_api_contracts/registry/taxonomy.py)
- [`unified-api-contracts/unified_api_contracts/canonical/crosscutting/share_class.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/share_class.py)
- [`unified-api-contracts/unified_api_contracts/registry/client_share_classes.py`](../../../unified-api-contracts/unified_api_contracts/registry/client_share_classes.py)
- [`unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/candidate_manifest.py`](../../../unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/candidate_manifest.py)
- [`unified-api-contracts/unified_api_contracts/internal/domain/ml/schemas.py`](../../../unified-api-contracts/unified_api_contracts/internal/domain/ml/schemas.py)
- [`unified-api-contracts/unified_api_contracts/internal/reference/data_freshness.py`](../../../unified-api-contracts/unified_api_contracts/internal/reference/data_freshness.py)

**Codex SSOTs**:

- [codex/09-strategy/architecture-v2/](../../../unified-trading-pm/codex/09-strategy/architecture-v2/) — strategy
  architecture v2
- [codex/09-strategy/architecture-v2/archetypes/](../../../unified-trading-pm/codex/09-strategy/architecture-v2/archetypes/)
  — per-archetype design SSOTs (28+ docs)
- [codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md](../../../unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md)
  — `PnLAttributionRow` + factor enum
- [codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md](../../../unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md)
  — 8 allocator archetypes
- [codex/09-strategy/architecture-v2/axes/share-class.md](../../../unified-trading-pm/codex/09-strategy/architecture-v2/axes/share-class.md)
- [codex/04-architecture/promote-workflow-architecture.md](../../../unified-trading-pm/codex/04-architecture/promote-workflow-architecture.md)
- [codex/04-architecture/custody-providers.md](../../../unified-trading-pm/codex/04-architecture/custody-providers.md)
- [codex/04-architecture/interface-credential-convention.md](../../../unified-trading-pm/codex/04-architecture/interface-credential-convention.md)
- [codex/04-architecture/client-funds-isolation.md](../../../unified-trading-pm/codex/04-architecture/client-funds-isolation.md)
- [codex/04-architecture/treasury-custody-flow.md](../../../unified-trading-pm/codex/04-architecture/treasury-custody-flow.md)
- [codex/04-architecture/wallet-hierarchy-and-capital-flow.md](../../../unified-trading-pm/codex/04-architecture/wallet-hierarchy-and-capital-flow.md)
- [codex/04-architecture/defi-execution-overview.md](../../../unified-trading-pm/codex/04-architecture/defi-execution-overview.md)
- [codex/04-architecture/flash-loan-receiver.md](../../../unified-trading-pm/codex/04-architecture/flash-loan-receiver.md)
- [codex/04-architecture/trading-agent-service-directive-pipeline.md](../../../unified-trading-pm/codex/04-architecture/trading-agent-service-directive-pipeline.md)
- [codex/09-strategy/operational/cli-promote-paths.md](../../../unified-trading-pm/codex/09-strategy/operational/cli-promote-paths.md)
- [codex/04-architecture/shard-level-failure-isolation.md](../../../unified-trading-pm/codex/04-architecture/shard-level-failure-isolation.md)

**Plans (spine — 10 most important)**: see §"Active plans inventory" above.
