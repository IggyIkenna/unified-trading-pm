---
doc_type: codex-ssot
title: v2 Migration Audit — Legacy → Architecture-v2 Mapping
summary:
  Complete legacy→architecture-v2 mapping audit — every legacy cefi/defi/sports/tradfi strategy doc, strategy-service
  class, and e2e config mapped to a v2 archetype+instance; includes the load-bearing legacy-code deletion schedule gated
  on the batch-factory cutover.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [e2e-testing, execution-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, migration, refactor, ssot-audit, cefi, defi, sports]

  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
  ]
created: 2026-04-17
authoritative_for: [legacy strategy doc-and-code to architecture-v2 mapping audit]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/_archived_pre_v2/README.md,
    /codex/09-strategy/_archived_pre_v2/STRATEGY_CATALOG_pre_v2.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
    /codex/09-strategy/architecture-v2/promote-workflow.md,
    /codex/09-strategy/strategy-summary.md,
  ]
owner:
last_reviewed:
code_refs:
---

# v2 Migration Audit — Legacy → Architecture-v2 Mapping

> **Purpose:** Every existing strategy doc, code module, and config must map to a placement in architecture-v2. This
> document is the complete audit. No functionality is lost — it's either carried forward as-is or enhanced under the new
> structure.
>
> **Rule:** If a legacy strategy isn't in this table, it's a bug. Flag it, don't silently drop it.

> **Phase 9 update note (codex audit ST-3 2026-05-12)**: this migration audit describes the original v2 cutover
> targeting **18 archetype engines**. Phase 9 (2026-04-25) expanded that to **55 archetypes** (UAC enum count per slot 8
> audit ST-1); subsequently to **57** per taxonomy V-1 2026-05-18 (added `CARRY_STAKED_BASIS_DATED` +
> `CARRY_BASIS_DATED_INV`; renamed `CARRY_RECURSIVE_BORROW_PERP_HEDGED` → `CARRY_BASIS_PERP_INV`). The 18-engine framing
> below + the "53 strategy classes → 18 archetype engines" / "18 archetype engines need to clear their 14- or 28-day
> shadow" cells reflect the original migration plan, NOT the current archetype population. For the canonical archetype
> count + family list, see UAC `unified_api_contracts/internal/architecture_v2/enums.py:StrategyArchetype` (57
> members) + [`README.md`](./README.md) "the enum wins" note.

## Status Key

- ✓ **Mapped** — legacy doc/code has a clear target archetype + instance
- ~ **Partial** — legacy doc partially covered; residual content merged into a cross-cutting doc or axis
- - **Enhanced** — legacy functionality preserved + extended in v2
- R **Retired** — legacy doc marked as stale/superseded; functionality absorbed without new doc
- ! **Routing default** — pre-decided default route in § 14; overrides require a plan amendment

## 1. Legacy cefi/ Strategy Docs → v2

| Legacy doc               | Target archetype                                                                             | Example v2 instances                                         | Status | Notes                                                                                                  |
| ------------------------ | -------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------------------------------ |
| `cefi/market-making.md`  | `MARKET_MAKING_CONTINUOUS`                                                                   | `@binance-btc-usdt-mm-prod`, `@hyperliquid-eth-usdt-mm-prod` | +      | Enhanced: now shares delta-proxy repricer + inventory-skew primitives with sports MM via family engine |
| `cefi/mean-reversion.md` | `RULES_DIRECTIONAL_CONTINUOUS` (if TA-based) or `ML_DIRECTIONAL_CONTINUOUS` (if model-based) | `@binance-btc-5m-usdt-prod`, `@binance-eth-1h-usdt-prod`     | ✓      | Archetype depends on signal source — see config                                                        |
| `cefi/momentum.md`       | `RULES_DIRECTIONAL_CONTINUOUS`                                                               | `@binance-btc-5m-usdt-prod`                                  | ✓      | Rule-based TA (z-score + momentum)                                                                     |

## 2. Legacy defi/ Strategy Docs → v2

| Legacy doc                            | Target archetype                                                                                       | Example v2 instances                                                                     | Status | Notes                                                                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------- |
| `defi/aave-lending.md`                | `YIELD_ROTATION_LENDING`                                                                               | `@aave-multichain-usdc-prod`, `@aave-ethereum-usdt-prod`                                 | +      | Enhanced: multi-protocol eligible set (Aave + Compound + Euler + Morpho)                                                   |
| `defi/basis-trade.md`                 | `CARRY_BASIS_PERP`                                                                                     | `@uniswap-hyperliquid-eth-usdt-prod`                                                     | ✓      | Generic basis archetype                                                                                                    |
| `defi/btc-basis-trade.md`             | `CARRY_BASIS_PERP`                                                                                     | `@uniswap-hyperliquid-btc-usdt-prod`                                                     | ✓      | Instance of same archetype, BTC-specific config                                                                            |
| `defi/btc-lending-yield.md`           | `YIELD_ROTATION_LENDING`                                                                               | `@aave-multichain-wbtc-prod`                                                             | ✓      | WBTC lending rotation                                                                                                      |
| `defi/cross-chain-sor-rebalancing.md` | **Cross-cutting**                                                                                      | `cross-cutting/transfer-rebalance.md` + SOR primitive in execution                       | +      | Split: SOR arb → `ARBITRAGE_PRICE_DISPERSION` archetype; rebalancing → Transfer/Rebalance service                          |
| `defi/cross-chain-yield-arb.md`       | `YIELD_ROTATION_LENDING` (multi-chain) + `ARBITRAGE_PRICE_DISPERSION` (when yield spread is arb-style) | `@aave-multichain-usdc-arb-prod`                                                         | ✓      | Depends whether it's rotation (alpha = rate spread) or arb (alpha = structural dispersion)                                 |
| `defi/ethena-benchmark.md`            | `CARRY_BASIS_PERP` (Ethena's USDe synthetic dollar is hedged basis)                                    | Reference / benchmark strategy, not a deployed instance                                  | ~      | Used as benchmark reference for our basis strategies; doc moves to `archetypes/carry-basis-perp.md` as a benchmark section |
| `defi/l2-basis-trade.md`              | `CARRY_BASIS_PERP`                                                                                     | `@uniswap-arbitrum-hyperliquid-eth-usdt-prod`                                            | ✓      | Instance with L2 spot + CEX perp                                                                                           |
| `defi/market-making-lp.md`            | `MARKET_MAKING_CONTINUOUS` (LP variant)                                                                | `@uniswap-v3-eth-usdc-active-lp-prod`                                                    | +      | Concentrated LP brought into same family as orderbook MM; shared inventory-skew primitives                                 |
| `defi/multi-chain-lending-yield.md`   | `YIELD_ROTATION_LENDING`                                                                               | `@aave-multichain-usdc-prod`                                                             | ✓      | Same as aave-lending with chain rotation explicit                                                                          |
| `defi/omnichain-transfers.md`         | **Cross-cutting**                                                                                      | `cross-cutting/transfer-rebalance.md` (service)                                          | +      | Not a strategy — it's a transfer/rebalance service. Moved out of strategies                                                |
| `defi/recursive-staked-basis.md`      | `CARRY_RECURSIVE_STAKED`                                                                               | `@lido-aave-eth-prod`, `@jito-kamino-sol-prod`                                           | +      | Recursive loop archetype; captures LTV/haircut from venue capability registry                                              |
| `defi/reward-lifecycle.md`            | **Cross-cutting**                                                                                      | Stays at `cross-cutting/reward-lifecycle.md`; referenced by all Carry & Yield archetypes | ~      | Not a strategy — supporting cross-cutting concern for reward harvesting                                                    |
| `defi/sol-basis-trade.md`             | `CARRY_BASIS_PERP`                                                                                     | `@kamino-drift-sol-usdc-prod`                                                            | ✓      | SOL basis instance                                                                                                         |
| `defi/sol-concentrated-lp.md`         | `MARKET_MAKING_CONTINUOUS`                                                                             | `@orca-sol-usdc-active-lp-prod`                                                          | ✓      | Solana active LP instance                                                                                                  |
| `defi/sol-lending-yield.md`           | `YIELD_ROTATION_LENDING`                                                                               | `@kamino-sol-usdc-prod`                                                                  | ✓      | Solana lending                                                                                                             |
| `defi/sol-staked-basis.md`            | `CARRY_STAKED_BASIS`                                                                                   | `@jito-kamino-drift-sol-prod`                                                            | ✓      | Solana staked basis                                                                                                        |
| `defi/staked-basis.md`                | `CARRY_STAKED_BASIS`                                                                                   | `@lido-aave-hyperliquid-eth-prod`                                                        | ✓      | ETH staked basis generic archetype                                                                                         |

## 3. Legacy sports/ Strategy Docs → v2

| Legacy doc                        | Target archetype                                               | Example v2 instances                                           | Status | Notes                                                                                                                       |
| --------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------- |
| `sports/arbitrage.md`             | `ARBITRAGE_PRICE_DISPERSION`                                   | `@unity-epl-1x2-usd-prod`, `@unity-nba-moneyline-usd-prod`     | +      | Now routed primarily through Unity (meta-broker); cross-book arb much simpler operationally                                 |
| `sports/first-half-prediction.md` | `ML_DIRECTIONAL_EVENT_SETTLED`                                 | `@unity-epl-1h-1x2-usd-prod`, `@unity-la-liga-1h-1x2-usd-prod` | ✓      | 1H market config variant; pairs with halftime ML for phase-1/phase-2 capital utilization                                    |
| `sports/halftime-ml.md`           | `ML_DIRECTIONAL_EVENT_SETTLED`                                 | `@unity-epl-ht-2h-usd-prod`                                    | ✓      | HT market config variant                                                                                                    |
| `sports/market-making.md`         | `MARKET_MAKING_EVENT_SETTLED`                                  | `@betfair-epl-mm-gbp-prod`, `@smarkets-epl-mm-gbp-prod`        | +      | Now uses same inventory-skew + delta-proxy primitives as CeFi MM                                                            |
| `sports/odds-drift.md`            | `ML_DIRECTIONAL_EVENT_SETTLED` (with odds-drift signal source) | `@unity-epl-drift-usd-prod`                                    | +      | Drift model is a signal source variant within ML directional family                                                         |
| `sports/pre-game-ml.md`           | `ML_DIRECTIONAL_EVENT_SETTLED`                                 | `@unity-epl-1x2-usd-prod`, `@unity-nba-moneyline-usd-prod`     | ✓      | Full-match ML prediction archetype                                                                                          |
| `sports/staking-methods.md`       | **Axis doc**                                                   | `axes/staking-methods.md`                                      | ~      | Not a strategy — it's the staking axis. Content merges into axes/staking-methods.md with sports-specific examples           |
| `sports/value-betting.md`         | `ML_DIRECTIONAL_EVENT_SETTLED` (generic)                       | Reference doc for the family, not a deployed instance          | ~      | The generic edge method (value betting) is covered in `axes/edge-methods.md`; sports-specific examples in the archetype doc |

## 4. Legacy tradfi/ Strategy Docs → v2

| Legacy doc                        | Target archetype                                                                                             | Example v2 instances                                                                                   | Status | Notes                                                                                                                      |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ | ------ | -------------------------------------------------------------------------------------------------------------------------- |
| `tradfi/market-making-options.md` | `MARKET_MAKING_CONTINUOUS` or `VOL_TRADING_OPTIONS`                                                          | `@deribit-btc-options-mm-usdt-prod` if spread-capture alpha; `@deribit-btc-vol-usdt-prod` if vol alpha | !      | Depends on alpha thesis — if primary alpha is spread, goes to MM family; if primary is vol mispricing, goes to Vol Trading |
| `tradfi/ml-directional.md`        | `ML_DIRECTIONAL_CONTINUOUS`                                                                                  | `@ibkr-spy-5m-usd-prod`, `@ibkr-eur-usd-5m-usd-prod`                                                   | ✓      | Generic ML directional archetype; TradFi is just a venue-config choice                                                     |
| `tradfi/options-ml.md`            | `VOL_TRADING_OPTIONS` (if vol alpha) or `ML_DIRECTIONAL_CONTINUOUS` with options expression (if delta alpha) | `@deribit-btc-delta-ml-usdt-prod` (delta) or `@deribit-btc-vol-ml-usdt-prod` (vol)                     | !      | Depends on alpha thesis                                                                                                    |

## 5. Legacy prediction/ Strategy Docs → v2

(No `prediction/` directory currently exists in the codex. Prediction market strategies are handled under:)

- `ML_DIRECTIONAL_EVENT_SETTLED` for binary prediction markets → `@polymarket-binary-usdc-prod`
- `ARBITRAGE_PRICE_DISPERSION` for cross-event arb → `@polymarket-cross-event-usdc-prod`

Prediction-market specifics covered in `cross-cutting/prediction-markets.md` (legacy, preserved).

## 6. Legacy cross-cutting/ Docs → v2

| Legacy doc                                       | v2 placement                                                                                                                                  | Status | Notes                                                                        |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- | ------ | ---------------------------------------------------------------------------- |
| `cross-cutting/client-onboarding.md`             | Stays at legacy path; linked from `architecture-v2/cross-cutting/capital-client-isolation.md`                                                 | ✓      | Preserved as-is                                                              |
| `cross-cutting/client-strategy-config.md`        | Stays at legacy path; content partially absorbed into `architecture-v2/cross-cutting/portfolio-allocator.md`                                  | ✓      | Allocator subscriptions extend this                                          |
| `cross-cutting/config-architecture.md`           | Split: naming/versioning → `06-coding-standards/strategy-identity-versioning.md`; UAC schema parts → `04-architecture/artifact-versioning.md` | +      | Enhanced with 3-axis versioning model                                        |
| `cross-cutting/cost-modeling.md`                 | Merges into `04-architecture/execution-policy.md` (algo cost) + `cross-cutting/benchmark-fills.md` (alpha attribution)                        | +      | Cost model is now a facet of execution policies + attribution                |
| `cross-cutting/instrument-filtering.md`          | Stays at legacy path; linked from archetype docs (especially DeFi-touching archetypes)                                                        | ✓      | Referenced by v2 archetypes                                                  |
| `cross-cutting/latency-profiles.md`              | Merges into `04-architecture/execution-policy.md` + `02-venues/venue-registry-reference.md`                                                   | +      | Per-venue latency is a venue capability field                                |
| `cross-cutting/margin-health.md`                 | Merges into `architecture-v2/cross-cutting/venue-account-coordination.md` + `cross-cutting/risk-gates.md`                                     | +      | Margin health becomes part of venue-account pre-flight                       |
| `cross-cutting/ml-pipeline.md`                   | Merges into `04-architecture/backtest-groups.md` (Group A)                                                                                    | +      | ML training is now explicitly one of the three backtest groups               |
| `cross-cutting/onboarding-checklist.md`          | Stays at legacy path                                                                                                                          | ✓      | Preserved                                                                    |
| `cross-cutting/operational-modes-matrix.md`      | Stays; referenced from `cross-cutting/benchmark-fills.md`                                                                                     | ✓      | Batch/live mode matrix                                                       |
| `cross-cutting/pnl-attribution.md`               | Stays; enhanced with benchmark-fills contract reference                                                                                       | +      | PnL attribution now explicitly separates strategy alpha from execution alpha |
| `cross-cutting/prediction-markets.md`            | Stays at legacy path; referenced from prediction archetype docs                                                                               | ✓      | Preserved                                                                    |
| `cross-cutting/rate-impact-model.md`             | Stays; referenced from Carry & Yield archetypes                                                                                               | ✓      | Preserved                                                                    |
| `cross-cutting/reward-lifecycle.md`              | Stays at legacy path; referenced from Carry & Yield archetypes                                                                                | ✓      | Preserved                                                                    |
| `cross-cutting/share-classes.md`                 | Absorbed into `architecture-v2/axes/share-class.md`                                                                                           | +      | Share class is now a first-class axis                                        |
| `cross-cutting/venue-collateral-and-wrapping.md` | Absorbed into `02-venues/venue-capability-registry.md` (collateral rules + haircuts)                                                          | +      | Now structured data in UAC, not prose                                        |

## 7. Legacy Top-Level Docs → v2

| Legacy doc                                               | v2 placement                                                                                                       | Status | Notes                                                                           |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | ------ | ------------------------------------------------------------------------------- |
| `09-strategy/README.md`                                  | Updated to point to `architecture-v2/README.md`                                                                    | ✓      | Legacy README stays as index/pointer; adds link to v2                           |
| `09-strategy/strategy-registry.md`                       | Reinterpreted as strategy instance registry; content split between archetype registry and instance registry in UAC | +      | Now backed by UAC schemas (StrategyArchetype, StrategyInstance, StrategyConfig) |
| `09-strategy/STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md` | Reinterpreted as migration checklist; content folded into this MIGRATION.md doc                                    | ~      | Superseded by MIGRATION.md                                                      |
| `09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md`            | Stays at legacy path; referenced from UI docs                                                                      | ✓      | UI Tier-0 playbook preserved                                                    |
| `09-strategy/execution-modes.md`                         | Merges into `cross-cutting/benchmark-fills.md` + `04-architecture/backtest-groups.md`                              | +      | Execution modes concept now formalized as batch/live plus backtest groups       |

## 8. Legacy Strategy Code (strategy-service) → v2

The `strategy-service` has ~53 concrete strategy classes today. Under v2, these become **instances of 18 archetype
engines**. The migration audit per strategy class:

### strategy-service/engine/strategies/cefi/ → v2

| Legacy file                                          | Target archetype class                                                | Target instance(s)                                           | Status                                                  |
| ---------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------- |
| `cefi/market_making.py` (`CeFiMarketMakingStrategy`) | `MarketMakingContinuousEngine`                                        | `@binance-btc-usdt-mm-prod`, `@hyperliquid-eth-usdt-mm-prod` | ✓ Functionality preserved; engine shared with sports MM |
| `cefi/mean_reversion.py`                             | `RulesDirectionalContinuousEngine` or `MLDirectionalContinuousEngine` | `@binance-btc-5m-usdt-prod`                                  | ✓                                                       |
| `cefi/momentum.py`                                   | `RulesDirectionalContinuousEngine`                                    | `@binance-btc-5m-usdt-prod`                                  | ✓                                                       |

### strategy-service/engine/strategies/defi/ → v2

| Legacy file                             | Target archetype class                                                                                          | Target instance(s)                             | Status                                |
| --------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------- |
| `defi/basis_trade.py`                   | `CarryBasisPerpEngine`                                                                                          | `@uniswap-hyperliquid-eth-usdt-prod`           | ✓                                     |
| `defi/btc_basis_trade.py`               | `CarryBasisPerpEngine`                                                                                          | `@uniswap-hyperliquid-btc-usdt-prod`           | ✓                                     |
| `defi/l2_basis.py`                      | `CarryBasisPerpEngine`                                                                                          | `@uniswap-arbitrum-hyperliquid-eth-usdt-prod`  | ✓                                     |
| `defi/sol_basis.py`                     | `CarryBasisPerpEngine`                                                                                          | `@kamino-drift-sol-usdc-prod`                  | ✓                                     |
| `defi/staked_basis.py`                  | `CarryStakedBasisEngine`                                                                                        | `@lido-aave-hyperliquid-eth-prod`              | ✓                                     |
| `defi/sol_staked_basis.py`              | `CarryStakedBasisEngine`                                                                                        | `@jito-kamino-drift-sol-prod`                  | ✓                                     |
| `defi/recursive_staked_basis.py`        | `CarryRecursiveStakedEngine`                                                                                    | `@lido-aave-eth-prod`                          | ✓                                     |
| `defi/aave_lending.py`                  | `YieldRotationLendingEngine`                                                                                    | `@aave-multichain-usdc-prod`                   | ✓                                     |
| `defi/btc_lending_yield.py`             | `YieldRotationLendingEngine`                                                                                    | `@aave-multichain-wbtc-prod`                   | ✓                                     |
| `defi/multi_chain_lending_yield.py`     | `YieldRotationLendingEngine`                                                                                    | `@aave-multichain-usdc-prod`                   | ✓ (consolidates with aave_lending.py) |
| `defi/sol_lending_yield.py`             | `YieldRotationLendingEngine`                                                                                    | `@kamino-sol-usdc-prod`                        | ✓                                     |
| `defi/cross_chain_yield_arb.py`         | `YieldRotationLendingEngine` or `ArbitragePriceDispersionEngine`                                                | Config-dependent                               | !                                     |
| `defi/cross_chain_sor.py`               | **Cross-cutting** — moves out of strategy-service to either execution-service SOR or transfer-rebalance service | n/a                                            | +                                     |
| `defi/active_defi_mm.py` (LP provision) | `MarketMakingContinuousEngine`                                                                                  | `@uniswap-v3-eth-usdc-active-lp-prod`          | ✓                                     |
| `defi/sol_concentrated_lp.py`           | `MarketMakingContinuousEngine`                                                                                  | `@orca-sol-usdc-active-lp-prod`                | ✓                                     |
| `defi/lending_protocol_arb.py`          | `ArbitragePriceDispersionEngine`                                                                                | `@aave-compound-ethereum-usdc-arb-prod`        | ✓                                     |
| `defi/liquidation_capture.py`           | `LiquidationCaptureEngine`                                                                                      | `@aave-ethereum-prod`, `@aave-multichain-prod` | ✓                                     |
| `defi/enhanced_basis.py`                | `CarryStakedBasisEngine` or `CarryRecursiveStakedEngine`                                                        | Config-dependent                               | !                                     |
| `defi/omnichain_transfer.py`            | **Cross-cutting** — moves to transfer-rebalance service                                                         | n/a                                            | +                                     |

### strategy-service/engine/strategies/sports/ → v2

| Legacy file                       | Target archetype class                                                                               | Target instance(s)           | Status                           |
| --------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------- | -------------------------------- |
| `sports/arbitrage.py`             | `ArbitragePriceDispersionEngine`                                                                     | `@unity-epl-1x2-usd-prod`    | + Unity-first routing            |
| `sports/value_betting.py`         | `MLDirectionalEventSettledEngine`                                                                    | `@unity-epl-1x2-usd-prod`    | ✓                                |
| `sports/kelly.py`                 | **Axis** — merges into `axes/staking-methods.md` implementation; code moves to shared sizing utility | n/a                          | ~                                |
| `sports/ml_sports_strategy.py`    | `MLDirectionalEventSettledEngine`                                                                    | `@unity-epl-1x2-usd-prod`    | ✓                                |
| `sports/halftime_ml.py`           | `MLDirectionalEventSettledEngine`                                                                    | `@unity-epl-ht-2h-usd-prod`  | ✓                                |
| `sports/first_half_prediction.py` | `MLDirectionalEventSettledEngine`                                                                    | `@unity-epl-1h-1x2-usd-prod` | ✓ (already written this session) |
| `sports/odds_drift.py`            | `MLDirectionalEventSettledEngine`                                                                    | `@unity-epl-drift-usd-prod`  | ✓ (already written this session) |
| `sports/market_making.py`         | `MarketMakingEventSettledEngine`                                                                     | `@betfair-epl-mm-gbp-prod`   | ✓                                |
| `sports/venue_allocator.py`       | **Cross-cutting** — now part of execution-service's SOR for sports                                   | n/a                          | +                                |
| `sports/backtest_engine.py`       | **Superseded** by shared strategy-service batch runner using benchmark fills contract                | n/a                          | + Unified with Group B backtests |

### strategy-service/engine/strategies/tradfi/ → v2

(No dedicated tradfi/ directory in strategy-service today; TradFi strategies live in cefi/ or root.)

| Legacy file | Target archetype class | Target instance(s) | Status | |
------------------------------------------------ |
--------------------------------------------------------------------------------------------------------------------------------------------------

| ------------------------------------------------------------------------------------------------- |
-------------------------------------------------------------- | ------------------------------------------------- | |
`tradfi_ml_swing_strategy.py` / `tradfi_ml_*.py` | `MLDirectionalContinuousEngine` | `@ibkr-spy-5m-usd-prod` | ✓ | |
`event_driven_macro.py` | `EventDrivenEngine` | `@multi-cex-macro-crypto-usdt-prod`, `@cme-macro-equities-usd-prod` | ✓
| | `commodity_regime.py` | `RulesDirectionalContinuousEngine` (regime-switching config) | `@ibkr-cl-futures-usd-prod` |
✓ | | `options_ml_*.py` (delta, strike, vol) | `MLDirectionalContinuousEngine` (delta/strike) or
`VolTradingOptionsEngine` (vol) | Config-dependent | ! | | `vol_surface_btc.py` | `ArbitragePriceDispersionEngine` (if
hard no-arb violations or cross-venue IV dispersion) OR `VolTradingOptionsEngine` (if soft surface residuals) |
`@deribit-okx-btc-vol-usdt-prod` (arb) or `@deribit-btc-surface-residual-usdt-prod` (vol trading) | ! | Decision
criteria: mechanical vs statistical edge | | `rel_vol_btc_eth.py` | `StatArbPairsFixedEngine` (vol-pair variant) |
`@deribit-btc-eth-relvol-usdt-prod` | ✓ | | `stat_arb_btc_eth.py` | `StatArbPairsFixedEngine` |
`@binance-btc-eth-usdt-prod` | ✓ | | `cross_exchange_btc.py` | `ArbitragePriceDispersionEngine` |
`@binance-bybit-btc-usdt-prod` | ✓ | | `basis_trade_multi_coin.py` | `CarryBasisPerpEngine` (multi-instrument rotation)
| `@binance-multicoin-usdt-prod` | ✓ | | `basis_trade_multi_venue.py` | `CarryBasisPerpEngine` (multi-venue eligibility)
| `@multi-cex-eth-usdt-prod` | ✓ | | `prediction_arb_btc.py` | `ArbitragePriceDispersionEngine` |
`@polymarket-binance-btc-usdc-prod` | ✓ | | `cefi_market_making.py` | `MarketMakingContinuousEngine` |
`@binance-btc-usdt-mm-prod` | ✓ (already uses position reconciliation we added this session) |

## 9. e2e-testing Strategy Configs → v2

18 DeFi strategy configs in `e2e-testing/configs/defi/strategies/` are instance-level configs — each maps to an
archetype:

| Legacy config                     | Target archetype                                         | Target instance                                                         |
| --------------------------------- | -------------------------------------------------------- | ----------------------------------------------------------------------- |
| `defi_amm_lp.yaml`                | `MARKET_MAKING_CONTINUOUS`                               | `@uniswap-v3-eth-usdc-active-lp-prod`                                   |
| `defi_basis_eth.yaml`             | `CARRY_BASIS_PERP`                                       | `@uniswap-hyperliquid-eth-usdt-prod`                                    |
| `defi_btc_basis.yaml`             | `CARRY_BASIS_PERP`                                       | `@hyperliquid-btc-usdt-prod`                                            |
| `defi_btc_lending.yaml`           | `YIELD_ROTATION_LENDING`                                 | `@aave-multichain-wbtc-prod`                                            |
| `defi_btc_share_class.yaml`       | Axis / share-class config, not a strategy                | Shared across BTC-share-class instances                                 |
| `defi_cross_chain_sor.yaml`       | Cross-cutting — SOR config for execution                 | n/a                                                                     |
| `defi_cross_chain_yield_arb.yaml` | `YIELD_ROTATION_LENDING` or `ARBITRAGE_PRICE_DISPERSION` | Config-dependent                                                        |
| `defi_eth_share_class.yaml`       | Axis / share-class config                                | Shared across ETH-share-class instances                                 |
| `defi_l2_basis.yaml`              | `CARRY_BASIS_PERP`                                       | `@uniswap-arbitrum-hyperliquid-eth-usdt-prod`                           |
| `defi_lending_aave.yaml`          | `YIELD_ROTATION_LENDING`                                 | `@aave-multichain-usdc-prod`                                            |
| `defi_multichain_lending.yaml`    | `YIELD_ROTATION_LENDING`                                 | `@aave-multichain-usdc-prod` (consolidates)                             |
| `defi_recursive_basis.yaml`       | `CARRY_RECURSIVE_STAKED`                                 | `@lido-aave-eth-prod`                                                   |
| `defi_sol_basis_drift.yaml`       | `CARRY_BASIS_PERP`                                       | `@kamino-drift-sol-usdc-prod`                                           |
| `defi_sol_concentrated_lp.yaml`   | `MARKET_MAKING_CONTINUOUS`                               | `@orca-sol-usdc-active-lp-prod`                                         |
| `defi_sol_lending_kamino.yaml`    | `YIELD_ROTATION_LENDING`                                 | `@kamino-sol-usdc-prod`                                                 |
| `defi_sol_staked_basis.yaml`      | `CARRY_STAKED_BASIS`                                     | `@jito-kamino-drift-sol-prod`                                           |
| `defi_staked_basis.yaml`          | `CARRY_STAKED_BASIS`                                     | `@lido-aave-hyperliquid-eth-prod`                                       |
| `defi_staked_basis_lido.yaml`     | `CARRY_STAKED_BASIS`                                     | `@lido-aave-hyperliquid-eth-prod` (consolidates with defi_staked_basis) |

TradFi + Prediction configs (18 added in prior session at `e2e-testing/configs/{tradfi,prediction}/strategies/`) already
map cleanly to v2 archetypes.

## 10. Functional Enhancement Inventory

For each archetype, v2 adds capabilities the legacy docs didn't have. Track these explicitly so we know what's
"enhanced":

| Archetype                         | Legacy capability                                       | v2 enhancement                                                                                                                                             |
| --------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ML_DIRECTIONAL_CONTINUOUS`       | Per-venue ML strategy classes                           | Shared engine; venues = config; options expression supported (delta-1 via ATM call); share class first-class                                               |
| `ML_DIRECTIONAL_EVENT_SETTLED`    | Per-league sports ML                                    | Unity-first routing; odds-drift signal as variant; 1H + halftime as market config variants; rules-based signal source variant                              |
| `CARRY_BASIS_PERP`                | Per-chain/per-coin basis classes                        | Shared engine; single-venue netted (Binance cross-margin) as valid config; multi-venue pair also valid                                                     |
| `CARRY_STAKED_BASIS`              | ETH staked basis only                                   | Generalized to any (staking protocol, lending protocol, perp venue) triple; includes Solana (Jito+Kamino+Drift)                                            |
| `CARRY_RECURSIVE_STAKED`          | Single-chain recursive                                  | Multi-chain recursive; LTV/haircut from venue capability registry; cascading liquidation risk modeled                                                      |
| `YIELD_ROTATION_LENDING`          | Aave-only                                               | Multi-protocol eligible (Aave + Compound + Euler + Morpho + Kamino); multi-chain rotation with bridge-cost-aware rebalance                                 |
| `ARBITRAGE_PRICE_DISPERSION`      | Sports cross-book + DEX arb as separate strategies      | Unified archetype covering sports (Unity meta-broker), DEX (multi-venue SOR + flash-loan), CEX (cross-exchange), cross-category (Polymarket-Betfair)       |
| `LIQUIDATION_CAPTURE`             | Aave Ethereum only                                      | Multi-chain Aave + other lending protocols; gas auction via Flashbots                                                                                      |
| `MARKET_MAKING_CONTINUOUS`        | Per-venue MM classes                                    | Unified engine covering CeFi spot MM, CeFi perp MM, options MM, DeFi active LP, cross-venue MM; delta-proxy repricer + inventory skew + kill switch shared |
| `MARKET_MAKING_EVENT_SETTLED`     | Sports MM only                                          | Same engine, sports-specific settlement semantics                                                                                                          |
| `VOL_TRADING_OPTIONS`             | Separate per-trade-type (straddle, butterfly, calendar) | Unified engine with vol edge methods (IV/RV, skew, term, cross-asset vol) as config                                                                        |
| `STAT_ARB_PAIRS_FIXED`            | Single pair classes                                     | Generic cointegration engine; any pair of underlyings, any venue combination                                                                               |
| `STAT_ARB_CROSS_SECTIONAL`        | Not yet implemented in legacy                           | New archetype for cross-sectional ML ranking (Russell 1000 daily, crypto top-50, etc.)                                                                     |
| `EVENT_DRIVEN`                    | Per-event-type classes                                  | Shared engine with event calendar registry + surprise computer; venue-agnostic                                                                             |
| `RULES_DIRECTIONAL_CONTINUOUS`    | Momentum + mean-reversion TA classes                    | Unified rules engine; config-defined rule tables; regime-switching as config                                                                               |
| `RULES_DIRECTIONAL_EVENT_SETTLED` | Not yet implemented in legacy                           | New archetype for sports rules-based (scored-first, comeback, HT-lead triggers)                                                                            |

## 11. What's Being Retired Without a New Doc

| Legacy content                                                                                                   | Reason                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md`                                                                     | Superseded by this MIGRATION.md                                                                                                   |
| `strategy-registry.md` (top-level)                                                                               | Reinterpreted: strategy registry is now UAC types (StrategyArchetype, StrategyInstance, StrategyConfig); doc describes the schema |
| Separate per-venue basis docs (`btc-basis-trade.md`, `sol-basis-trade.md`, `l2-basis-trade.md`)                  | All collapse into single `archetypes/carry-basis-perp.md` with per-instance examples                                              |
| Separate per-chain lending docs (`btc-lending-yield.md`, `sol-lending-yield.md`, `multi-chain-lending-yield.md`) | All collapse into single `archetypes/yield-rotation-lending.md`                                                                   |

## 12. Migration Phases

| Phase                                                   | Scope                                                                                                                   | Status                     |
| ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | -------------------------- |
| **Phase 1: v2 docs written**                            | All 35 v2 docs + MIGRATION.md + UAC schemas drafted                                                                     | in progress (this session) |
| **Phase 2: UAC schemas added**                          | Polymorphic StrategyInstruction, archetype/instance/config tiers, venue capability + child venues, compatibility matrix | pending                    |
| **Phase 3: Strategy-service refactor**                  | 53 existing strategy classes → 18 archetype engines + per-instance configs                                              | pending                    |
| **Phase 4: Execution-service polymorphic orchestrator** | 11 action handlers, execution policy registry, venue-account pre-flight, ATOMIC multi-leg                               | pending                    |
| **Phase 5: New services**                               | portfolio-allocator-service + venue-capability-registry populated                                                       | pending                    |
| **Phase 6: PBMS + R&E extensions**                      | Venue-account aggregation + pre-flight + margin simulation                                                              | pending                    |
| **Phase 7: Backtest runners**                           | Group A (ML) + Group B (strategy) + Group C (execution) with fixed/dynamic grids                                        | pending                    |
| **Phase 8: UI navigation**                              | Family-first + category-as-filter + family dashboards + allocator UI                                                    | pending                    |
| **Phase 9: Strategy migration**                         | Map each of 53 existing strategies → (archetype, instance, config) triple; shadow deploy; cutover                       | pending                    |
| **Phase 10: Retire legacy docs**                        | After cutover, archive legacy category-based docs with pointers to v2                                                   | pending                    |

## 13. Migration Validation Rules

Before any strategy is considered migrated, check:

1. **Functional parity**: backtest of legacy strategy vs v2 instance on same historical period produces P&L within 2%
   annualised tolerance (accounting for unavoidable differences in rebalance timing, benchmark fills, etc.)
2. **Signal parity**: signal generation produces the same fire/no-fire decisions on ≥99% of historical candles
3. **Execution parity**: instructions emitted match (action type, target, venues) — allowing for target-state vs
   delta-based differences
4. **Audit trail**: every fill in v2 carries the full 9-field event tag
5. **UI parity**: legacy strategy's operational dashboard data is visible in v2's family + strategy-instance views
6. **Config roundtrip**: legacy YAML config can be losslessly transformed to v2 StrategyConfig (with enhancements noted)

## 14. Routing defaults for ambiguous legacy files

Each item below has a **default routing** that applies unless a backtest or product decision overrides it. These are not
open questions — they are pre-decided defaults. Any override ships as a plan amendment.

1. **`defi/ethena-benchmark.md`** — benchmark reference only. Captured as a reference section in
   [carry-basis-perp.md](archetypes/carry-basis-perp.md); not deployed as a strategy.
2. **`tradfi/market-making-options.md`** — routes to MM family (primary alpha: spread capture). Override requires a
   backtest showing vol-driven alpha dominates.
3. **`tradfi/options-ml.md`** — three ML options strategies; each routes per its alpha thesis (directional → ML
   directional family; vol → VOL_TRADING_OPTIONS).
4. **`defi/cross_chain_yield_arb.py`** — routes to `YIELD_ROTATION_LENDING` if alpha is a rate spread sustained over
   hours; `ARBITRAGE_PRICE_DISPERSION` if alpha is transient structural dispersion.
5. **`defi/enhanced_basis.py`** — routes to `CARRY_RECURSIVE_STAKED` if the loop is recursive; `CARRY_STAKED_BASIS` if
   single-step.

## 15. Legacy Code Deletion Schedule

### Docs (DONE — 2026-04-18)

43 legacy docs archived to `codex/09-strategy/_archived_pre_v2/` with pointers to their v2 placement. See
[`../_archived_pre_v2/README.md`](../_archived_pre_v2/README.md). Top-level `README.md` rewritten to point at v2.

### Code (BLOCKED — factory cutover is the gate)

Legacy strategy code in `strategy-service/strategy_service/engine/strategies/{cefi,defi,sports,tradfi,...}/` is still
**load-bearing**. The batch-dispatch factory `strategy_service/cli/handlers/batch_utils.create_strategy_instance()` maps
62 legacy strategy-type strings (e.g. `"BTC_MARKET_MAKING"`, `"BASIS_TRADE"`, `"SPORTS_VALUE_BETTING"`) directly to the
legacy classes. That factory is the hot path for every Group B strategy backtest + every live batch run — deleting the
classes now would break production.

**Deletion prerequisites (in order):**

1. **Flip the factory to v2 engines.** `create_strategy_instance()` currently imports the legacy class and constructs
   it. Replace with `V2EngineOrchestrator` lookup by `archetype_id` derived from a new `STRATEGY_TYPE_TO_SLOT_LABEL`
   mapping that reuses the slot labels produced by `LegacyStrategyMapping` / `TARGET_UNIVERSE`. Every legacy type-string
   must resolve to an archetype engine.
2. **Shadow-promote each archetype per `ShadowDeploymentPolicy`.** The 18 archetype engines need to clear their 14- or
   21-day shadow observation window with `PROMOTE` decisions before prod reads from v2 (see
   [`../../04-architecture/shadow-deployment-pattern.md`](../../04-architecture/shadow-deployment-pattern.md)).
3. **Cut over the factory dispatch** to v2 in production. One commit, all archetypes at once — partial cutover is
   disallowed by the "archetype-wide promotion" rule in the shadow-deployment doc.
4. **Validate.** Group B backtest + live batch runs produce identical instructions for ≥ 99% of historical candles
   (migration validation rule #2 in § 13 above) across every migrated strategy.
5. **Delete.** Only then is it safe to remove `strategy-service/engine/strategies/*.py` (non-v2 files) + the 10 legacy
   sub-packages (`cross_exchange/`, `mean_reversion/`, `options_ml/`, `options_market_making/`, `prediction/`,
   `prediction_arb/`, `rel_vol/`, `sports/`, `stat_arb/`, `tradfi_ml/`, `volatility/`).

### Known load-bearing dependency chains (cannot delete mid-sequence)

- `defi_base.py` is the base class for `defi_basis.py`, `btc_basis.py`, `sol_basis.py`, `l2_basis.py`,
  `defi_staked_basis.py`, `sol_staked_basis.py`, `defi_recursive_basis.py`, and `active_defi_mm.py`. Delete together or
  not at all.
- `defi_enhancements.py` is imported by `defi_basis.py` (and transitively everything above).
- `defi_amm_lp.py` is imported by `active_defi_mm.py`.
- `base_strategy.py` is imported by `cefi_market_making.py` + all sports strategies.

### Legacy YAML configs + e2e-testing configs

- `strategy_service/configs/` → retire in favor of UAC `StrategyInstanceDefinition` + content-hashed `ConfigRegistry`
  slots; deletion gated on the same factory cutover above.
- `e2e-testing/configs/` → convert to archetype integration tests (the in-process roundtrip test at
  `e2e-testing/tests/integration/test_architecture_v2_roundtrip.py` is the target shape).

### Legacy audit metadata kept on purpose

`LegacyStrategyMapping.legacy_module: str` (dotted path) is kept as audit provenance — it's never imported via
`importlib`, only inspected by operators. Safe to keep indefinitely; useful as a "who did this strategy use to be?"
index.

## Reference — Full Legacy Inventory

For reference, the complete list of legacy docs as of 2026-04-17:

**Category strategy docs (32):**

- cefi/: market-making, mean-reversion, momentum (3)
- defi/: aave-lending, basis-trade, btc-basis-trade, btc-lending-yield, cross-chain-sor-rebalancing,
  cross-chain-yield-arb, ethena-benchmark, l2-basis-trade, market-making-lp, multi-chain-lending-yield,
  omnichain-transfers, recursive-staked-basis, reward-lifecycle, sol-basis-trade, sol-concentrated-lp,
  sol-lending-yield, sol-staked-basis, staked-basis (18)
- sports/: arbitrage, first-half-prediction, halftime-ml, market-making, odds-drift, pre-game-ml, staking-methods,
  value-betting (8)
- tradfi/: market-making-options, ml-directional, options-ml (3)

**Cross-cutting docs (16):**

- client-onboarding, client-strategy-config, config-architecture, cost-modeling, instrument-filtering, latency-profiles,
  margin-health, ml-pipeline, onboarding-checklist, operational-modes-matrix, pnl-attribution, prediction-markets,
  rate-impact-model, reward-lifecycle, share-classes, venue-collateral-and-wrapping

**Top-level strategy docs (4):**

- README.md, strategy-registry.md, STRATEGY_CATALOG_AND_WORKFLOW_ALIGNMENT.md, TIER_ZERO_UI_DEMO_AND_PARITY.md,
  execution-modes.md

**Total: 56 legacy docs** — all mapped to v2 placement above.

Nothing is discarded. Everything is either migrated, enhanced, absorbed, or preserved as reference.
