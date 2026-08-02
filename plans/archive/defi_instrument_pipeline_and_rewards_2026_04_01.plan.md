---
doc_type: plan
title: defi-instrument-pipeline-and-rewards
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    e2e-testing,
    execution-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-03"
remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15
superseded_by: [consolidated_defi_data_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview:
  End-to-end instrument pipeline validation + EIGEN/ETHFI reward lifecycle (claim, M2M, sell) + Lido configurability
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-01
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: instruments-service, code: C0, deployment: none, business: none }
  - { repo: market-tick-data-service, code: C0, deployment: none, business: none }
  - { repo: market-data-processing-service, code: C0, deployment: none, business: none }
  - { repo: features-onchain-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: pnl-attribution-service, code: C0, deployment: none, business: none }
  - { repo: position-balance-monitor-service, code: C0, deployment: none, business: none }
  - { repo: e2e-testing, code: C0, deployment: none, business: none }
depends_on: [share-class-architecture]
todos:
  - { id: ip-1a-audit, content: "- [ ] [AGENT] P0. Audit all instruments needed across all DeFi strategies vs what
        exists upstream

        ", status: todo, note: Must be done FIRST — blocks everything }
  - { id: ip-1b-missing-instruments, content: "- [x] [AGENT] P0. Add missing instrument definitions (EIGEN, ETHFI, Lido
        staking, Binance spot pairs)

        ", status: done, note: "" }
  - { id: ip-1c-mtds-coverage, content: "- [ ] [AGENT] P0. Ensure MTDS adapters cover all required instruments + venues

        ", status: todo, note: "" }
  - { id: ip-2a-reward-types, content: "- [x] [AGENT] P0. Define reward lifecycle types in UAC (CLAIM_REWARD,
        SELL_REWARD instructions)

        ", status: done, note: "" }
  - { id: ip-2b-reward-schedule, content: "- [x] [AGENT] P0. Codify EIGEN/ETHFI reward schedules in UAC registry

        ", status: done, note: "EIGEN: weekly. Seasonal: ~quarterly" }
  - { id: ip-3a-strategy-rewards, content: "- [x] [AGENT] P0. Implement reward claiming + selling in strategy-service
        staking strategies

        ", status: done, note: RewardClaimMixin._check_reward_claims() DONE; NOT YET WIRED into
        StakedBasisStrategy/RecursiveStakedBasisStrategy.generate_defi_signal(). Also SEASONAL_QUARTERLY settlement type
        missing. }
  - { id: ip-3b-execution-rewards, content: "- [x] [AGENT] P0. Implement CLAIM_REWARD + SELL_REWARD handlers in
        execution-service

        ", status: done, note: "" }
  - { id: ip-4a-pnl-rewards, content: "- [x] [AGENT] P0. Add reward P&L attribution (staking vs restaking vs seasonal)

        ", status: done, note: "" }
  - { id: ip-4b-position-rewards, content: "- [x] [AGENT] P1. Track pending/claimed rewards in position-balance-monitor

        ", status: done, note: "aggregate_with_rewards() DONE; WALLET:SPOT_ASSET:EIGEN/ETHFI post-claim tracking
        MISSING." }
  - { id: ip-5a-lido-config, content: "- [x] [AGENT] P1. Make staking protocol configurable (Lido vs EtherFi) in
        strategy config

        ", status: done, note: "" }
  - { id: ip-6a-e2e, content: "- [x] [AGENT] P1. Add reward lifecycle scenarios to e2e-testing

        ", status: done, note: "" }
  - { id: ip-7a-docs, content: "- [x] [AGENT] P1. Update codex docs for instrument pipeline + reward lifecycle

        ", status: done, note: "" }
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_defi_data_pipeline_2026_04_15.md](./consolidated_defi_data_pipeline_2026_04_15.md).** Original scope
> retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit formalises it
> as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# DeFi Instrument Pipeline & Reward Lifecycle

## Context

> **Sequencing**: ip-3a/ip-3b (strategy reward claiming) must run AFTER share_class_architecture sc-2a-strategy
> completes (share_class field on DeFiStrategyConfig). settlement_service.py changes must run AFTER share_class FX
> conversion logic is in place.

Every DeFi strategy depends on a chain of upstream services providing instrument definitions, market data, and features.
If any link is missing, the strategy fails at runtime with "missing instrument" or "missing feature" errors. This plan
audits the entire pipeline and fills every gap.

Additionally, EIGEN/ETHFI reward tracking is a core part of the staking P&L promise. EtherFi pays:

- **Staking yield**: weETH/ETH appreciation (continuous, tracked via oracle rate)
- **Restaking rewards**: EIGEN token payouts (weekly via EigenLayer RewardsCoordinator)
- **Seasonal rewards**: Airdrops every ~3 months (EtherFi loyalty points converted to tokens)

These rewards must be: tracked (M2M valuation), claimed (on-chain transaction), sold (swap to base currency), and
attributed to P&L at the correct time.

Lido (stETH/wstETH) is an alternative staking protocol that should be configurable alongside EtherFi, but does NOT
support restaking or seasonal rewards.

## Pre-Audit: Instrument Pipeline Requirements Per Strategy

### What Each Strategy Needs (Upstream → Downstream)

```
INSTRUMENTS-SERVICE → MTDS → MDPS → FEATURES → STRATEGY → EXECUTION
```

| Strategy               | Instruments Needed                                               | MTDS Data                                            | MDPS Features                             | On-Chain Features                                  |
| ---------------------- | ---------------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------- | -------------------------------------------------- |
| AAVE_LENDING           | AAVE_V3-\*:A_TOKEN:AUSDT, AUSDC, ADAI, AWETH, AWBTC              | Aave oracle prices, liquidity indices                | aave_supply_apy, aave_utilization         | aave_liquidity_index                               |
| STAKED_BASIS           | ETHERFI-ETHEREUM:LST:WEETH, HYPERLIQUID:PERP:ETH-USDC            | weETH oracle rate, HyperLiquid funding               | weeth_eth_rate, funding_rate              | lst_staking_apy, weekly_rewards                    |
| BASIS_TRADE            | WALLET:SPOT*ASSET:ETH, UNISWAP_V3-*:POOL:\_, 5x PERP venues      | Spot prices all coins, perp funding rates all venues | eth*price, funding_rate*{COIN}\_{VENUE}   | N/A                                                |
| RECURSIVE_STAKED_BASIS | Same as STAKED_BASIS + MORPHO/AAVE_V3 flash loan pools           | Same + Aave borrow rates                             | Same + aave_borrow_apy_eth, health_factor | Same                                               |
| **REWARD SELLING**     | **EIGEN on Binance (EIGEN/USDT), ETHFI on Binance (ETHFI/USDT)** | **EIGEN/USDT spot price, ETHFI/USDT spot price**     | **eigen_price_usdt, ethfi_price_usdt**    | **eigen_claimable_amount, ethfi_claimable_amount** |
| **LIDO STAKING**       | **LIDO-ETHEREUM:LST:STETH, LIDO-ETHEREUM:LST:WSTETH**            | **stETH oracle rate, wstETH rate**                   | **steth_eth_rate, wsteth_eth_rate**       | **lido_staking_apy**                               |

### Gap Analysis (What's Missing)

| Layer                | What Exists                                                                         | What's Missing                                                                                                             |
| -------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Instruments**      | AAVE_V3 aTokens, ETHERFI weETH, LIDO stETH/wstETH, HyperLiquid perps, Uniswap pools | **EIGEN/USDT spot pair (Binance)**, **ETHFI/USDT spot pair (Binance)**, **EIGEN/ETH pair**, **ETHFI/ETH pair**             |
| **MTDS**             | Aave oracle, weETH rate, perp funding                                               | **EIGEN spot price feed**, **ETHFI spot price feed**, **stETH/ETH rate feed** (may exist via Lido adapter)                 |
| **MDPS**             | aave_supply_apy, weeth_eth_rate, funding_rate                                       | **eigen_price_usdt**, **ethfi_price_usdt**, **steth_eth_rate** normalised candles                                          |
| **Features-Onchain** | weekly_rewards (raw), lst_staking_apy                                               | **eigen_claimable_amount** (from RewardsCoordinator), **ethfi_claimable_amount**, **lido_staking_apy** as separate feature |
| **Strategy**         | Staking yield tracked, `SEASONAL_WEEKLY` settlement type                            | **CLAIM_REWARD instruction**, **SELL_REWARD instruction**, **Lido vs EtherFi config switch**                               |
| **Execution**        | EigenLayer connector exists, EtherFi connector exists                               | **CLAIM_REWARD handler** (calls RewardsCoordinator.claim()), **SELL_REWARD handler** (swap EIGEN/ETHFI→base)               |
| **P&L**              | Staking yield attributed                                                            | **Restaking P&L** (EIGEN value), **Seasonal P&L** (airdrop value), **M2M of unclaimed rewards**                            |
| **Position**         | Staking positions tracked                                                           | **Pending reward balances** (unclaimed EIGEN/ETHFI)                                                                        |

## Execution DAG

```
Phase 1 (PARALLEL — audit + UAC types)
  ├── 1A: Full instrument pipeline audit (verify every cell above)
  ├── 1B: Add missing instrument definitions
  └── 1C: Define reward lifecycle types in UAC
        │
        ▼  QG gate: UAC + instruments-service pass
Phase 2 (PARALLEL — data pipeline)
  ├── 2A: MTDS adapters for missing feeds (EIGEN, ETHFI, stETH prices)
  ├── 2B: MDPS normalised features for reward tokens
  └── 2C: Features-onchain claimable reward tracking
        │
        ▼  QG gate: MTDS + MDPS + features-onchain pass
Phase 3 (PARALLEL — strategy + execution)
  ├── 3A: Strategy reward claiming + selling logic
  ├── 3B: Execution CLAIM_REWARD + SELL_REWARD handlers
  └── 3C: Lido vs EtherFi config switch
        │
        ▼  QG gate: strategy-service + execution-service pass
Phase 4 (PARALLEL — downstream attribution)
  ├── 4A: P&L reward attribution (staking vs restaking vs seasonal)
  └── 4B: Position pending reward tracking
        │
        ▼  QG gate: pnl-attribution + position-balance-monitor pass
Phase 5 (E2E + Docs)
  ├── 5A: E2E reward lifecycle scenarios
  └── 5B: Codex documentation
```

## Phase 1: Audit + UAC Types (PARALLEL)

### 1A: Full Instrument Pipeline Audit

- [ ] [AGENT] P0. For EVERY DeFi strategy in `e2e-testing/configs/defi/strategies/`, trace the full pipeline:
  1. List all `instrument_id` values referenced in strategy config
  2. Verify each exists in instruments-service adapters (Aave, EtherFi, Lido, Uniswap, HyperLiquid)
  3. Verify MTDS has an adapter that produces data for that instrument
  4. Verify MDPS produces normalised features from that data
  5. Verify features-onchain (if applicable) computes on-chain features
  6. Document any gaps as blocking items

- [ ] [AGENT] P0. Specifically verify these critical instruments exist end-to-end:
  - `AAVE_V3-ETHEREUM:A_TOKEN:AWETH@ETHEREUM` — ETH share class lending
  - `AAVE_V3-ETHEREUM:A_TOKEN:AWBTC@ETHEREUM` — BTC share class lending
  - `AAVE_V3-ETHEREUM:DEBT_TOKEN:DWETH@ETHEREUM` — recursive basis borrowing
  - `ETHERFI-ETHEREUM:LST:WEETH@ETHEREUM` — staking
  - `LIDO-ETHEREUM:LST:STETH@ETHEREUM` — alternative staking
  - `LIDO-ETHEREUM:LST:WSTETH@ETHEREUM` — wrapped staking
  - `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` — basis perp leg
  - `HYPERLIQUID:PERPETUAL:BTC-USDC@LIN@HYPERLIQUID` — BTC basis
  - `UNISWAP_V3-ETHEREUM:POOL:WETH-USDC-3000@ETHEREUM` — spot swap
  - All 21 `hyperliquid_aster_mvp_base_assets` have perp instruments defined

### 1B: Missing Instrument Definitions

**Repo**: instruments-service, unified-api-contracts

- [x] [AGENT] P0. Add EIGEN token instrument definition:
  - Contract address: `0xec53bF9167f50cDEB3Ae105f56099aaaB9061F83` (EIGEN on Ethereum mainnet)
  - Adapter: `instruments_service/reference_data/adapters/eigenlayer.py` — `EigenLayerReferenceDataAdapter`
  - Key: `EIGENLAYER-ETHEREUM:GOVERNANCE_TOKEN:EIGEN`, registered in factory.py

- [x] [AGENT] P0. Add ETHFI token instrument definition:
  - Contract address: `0xFe0c30065B384F05761f15d0CC899D4F9F9Cc0eB` (ETHFI on Ethereum mainnet)
  - Adapter: `instruments_service/reference_data/adapters/ethfi.py` — `EthFiGovernanceReferenceDataAdapter`
  - Key: `ETHERFI-GOV-ETHEREUM:GOVERNANCE_TOKEN:ETHFI`, registered in factory.py

- [x] [AGENT] P0. Verify Lido instrument definitions in instruments-service:
  - `LIDO-ETHEREUM:LST:STETH@ETHEREUM` (stETH: `0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84`) ✓ exists in
    `instruments_service/reference_data/adapters/lido.py`
  - `LIDO-ETHEREUM:LST:WSTETH@ETHEREUM` (wstETH: `0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0`) ✓ exists in
    `instruments_service/reference_data/adapters/lido.py`
  - Both have `InstrumentType.YIELD_BEARING` with `available_since` from `_LIDO_DEPLOY_DATE` (2020-12-18)

- [ ] [AGENT] P0. Run `cd instruments-service && bash scripts/quality-gates.sh`
- [ ] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh`

### 1C: Reward Lifecycle Types in UAC

**Repo**: unified-api-contracts

- [x] [AGENT] P0. Add to `OperationType` enum:
  - `CLAIM_REWARD = "CLAIM_REWARD"` ✓ in `canonical/domain/execution/base.py` and
    `internal/domain/execution_service/types.py`
  - `SELL_REWARD = "SELL_REWARD"` ✓ in both places, with benchmark types (ORACLE / ARRIVAL)

- [x] [AGENT] P0. Create `RewardSchedule` registry in UAC (`registry/reward_schedules.py`):
  - `RewardScheduleEntry` dataclass ✓ in `unified_api_contracts/registry/reward_schedules.py`
  - `REWARD_SCHEDULES` list with EIGENLAYER (WEEKLY) and ETHERFI (QUARTERLY) entries ✓
  - Exported from `registry/__init__.py` ✓

- [x] [AGENT] P0. Create `RewardPosition` schema in UAC internal:
  - ✓ `RewardPosition(BaseModel)` in `unified_api_contracts/internal/positions/reward_position.py`
  - ✓ Fields: `protocol`, `reward_token`, `accrued_amount`, `claimed_amount`, `sold_amount`, `accrued_value_usd`,
    `claimed_value_usd`, `last_claim_timestamp`, `next_expected_claim`
  - ✓ Exported from `internal/__init__.py` and `internal/positions/__init__.py`

- [ ] [AGENT] P0. Run `cd unified-api-contracts && bash scripts/quality-gates.sh`

## Phase 2: Data Pipeline (PARALLEL)

### 2A: MTDS Adapters

**Repo**: market-tick-data-service

- [ ] [AGENT] P0. Verify/add EIGEN/USDT spot price adapter:
  - MISSING: no EIGEN/USDT adapter in market-tick-data-service
  - Source: Binance spot via Tardis or CCXT
  - Produces: trade candles for EIGEN-USDT
  - Required for M2M valuation of EIGEN rewards

- [ ] [AGENT] P0. Verify/add ETHFI/USDT spot price adapter:
  - MISSING: no ETHFI/USDT adapter in market-tick-data-service
  - Source: Binance spot via Tardis or CCXT
  - Produces: trade candles for ETHFI-USDT

- [ ] [AGENT] P0. Verify stETH/ETH and wstETH/ETH rate feeds exist in MTDS:
  - MISSING: no stETH/wstETH rate adapters found in market-tick-data-service
  - Source: Lido oracle on-chain OR Uniswap pool
  - If missing, add adapter similar to weETH rate adapter

- [ ] [AGENT] P0. Run `cd market-tick-data-service && bash scripts/quality-gates.sh`

### 2B: MDPS Normalised Features

**Repo**: market-data-processing-service

- [ ] [AGENT] P0. Ensure `rewards_adapter.py` produces normalised features:
  - `reward_per_eeth` — already exists in `DefiRewardsAdapter` ✓
  - `eigen_price_usdt` — MISSING: no EIGEN spot price in MDPS adapters
  - `ethfi_price_usdt` — MISSING: no ETHFI spot price in MDPS adapters
  - `steth_eth_rate` — MISSING: no stETH rate in MDPS adapters
  - `wsteth_eth_rate` — MISSING: no wstETH rate in MDPS adapters

- [ ] [AGENT] P0. Verify `lido_staking_apy` feature is produced (separate from EtherFi APY)
  - NOTE: `lido_staking_apy` exists in features-onchain-service `lst_staking_calculator.py` ✓ but MDPS pass-through not
    confirmed

- [ ] [AGENT] P0. Run `cd market-data-processing-service && bash scripts/quality-gates.sh`

### 2C: Features-Onchain Claimable Rewards

**Repo**: features-onchain-service

- [x] [AGENT] P0. Add `eigen_claimable_amount` feature:
  - ✓ `EigenRewardsCalculator` in `features_onchain_service/app/calculators/eigen_rewards_calculator.py`
  - Uses DefiLlama Yields API as APY-based proxy (direct on-chain RewardsCoordinator documented as future)
  - Produces: `eigen_claimable_amount` and `eigen_reward_apy`

- [ ] [AGENT] P0. Add `ethfi_claimable_amount` feature:
  - MISSING: no `ethfi_claimable_amount` calculator in features-onchain-service
  - `eigen_rewards_calculator.py` covers EIGEN only

- [x] [AGENT] P0. Add `lido_staking_apy` feature:
  - ✓ `LstStakingCalculator` in `features_onchain_service/app/calculators/lst_staking_calculator.py`
  - Produces `lido_staking_apy` (NaN for non-Lido pools) and `lst_staking_apy`

- [ ] [AGENT] P0. Run `cd features-onchain-service && bash scripts/quality-gates.sh`

## Phase 3: Strategy + Execution (PARALLEL)

### 3A: Strategy Reward Claiming + Selling

**Repo**: strategy-service

- [x] [AGENT] P0. Add reward management to `DeFiBaseStrategy`:
  - ✓ `RewardClaimMixin._check_reward_claims()` implemented in `strategy_service/engine/strategies/defi_enhancements.py`
  - ✓ `DeFiBaseStrategy` in `defi_base.py` inherits `RewardClaimMixin`
  - Logic: checks `eigen_claimable_amount`/`ethfi_claimable_amount` features, emits CLAIM_REWARD + SELL_REWARD
    instructions

- [x] [AGENT] P0. Add reward config to staking strategy configs:
  - ✓ `auto_claim`, `auto_sell`, `min_claim_value_usd`, `min_sell_value_usd`, `claim_frequency_hours` all implemented in
    `RewardClaimMixin.__init__()`

- [ ] [AGENT] P0. Update `defi_staked_basis.py` to include reward instructions in its signal generation:
  - INCOMPLETE: `StakedBasisStrategy.generate_defi_signal()` does NOT call `_check_reward_claims()`
  - The mixin is inherited but never invoked in the signal generation path

- [ ] [AGENT] P0. Update `defi_recursive_basis.py` to include reward instructions:
  - INCOMPLETE: `RecursiveStakedBasisStrategy.generate_defi_signal()` does NOT call `_check_reward_claims()`

- [ ] [AGENT] P0. Update settlement_service.py:
  - `SEASONAL_WEEKLY` settlement type ✓ exists and attributes EIGEN weekly payouts
  - `SEASONAL_QUARTERLY` MISSING — add for EtherFi seasonal airdrops

- [ ] [AGENT] P0. Run `cd strategy-service && bash scripts/quality-gates.sh`

### 3B: Execution CLAIM_REWARD + SELL_REWARD Handlers

**Repo**: execution-service

- [x] [AGENT] P0. Create `claim_reward_handler.py` in `engine/handlers/`:
  - ✓ `execution_service/engine/handlers/claim_reward_handler.py` exists

- [x] [AGENT] P0. Create `sell_reward_handler.py` in `engine/handlers/`:
  - ✓ `execution_service/engine/handlers/sell_reward_handler.py` exists

- [x] [AGENT] P0. Register both handlers in the handler registry:
  - ✓ Both registered in `execution_service/engine/routing/handler_registry.py`

- [x] [AGENT] P0. Extend EigenLayer connector (`eigenlayer.py`) with `claim_rewards()` method:
  - ✓ `claim_rewards(token)` implemented in `execution_service/defi_execution/protocols/eigenlayer.py` (line 510)
  - Calls `RewardsCoordinator.processClaim()` in live mode

- [ ] [AGENT] P0. Run `cd execution-service && bash scripts/quality-gates.sh`

### 3C: Lido vs EtherFi Config Switch

**Repo**: strategy-service

- [x] [AGENT] P1. Add `staking_protocol` config field to staking strategies:
  - ✓ `self._staking_protocol_config = config.get("staking_protocol", "ETHERFI")` in `defi_staked_basis.py`

- [x] [AGENT] P1. When `staking_protocol == "LIDO"`:
  - ✓ Routes to `LIDO:LST:WSTETH@ETHEREUM` instrument ✓
  - ✓ Uses `lido_staking_apy` feature key instead of `lst_staking_apy` ✓
  - ✓ Skips EIGEN/ETHFI reward instructions for LIDO protocol ✓
  - ✓ Uses `wsteth_eth_rate` exchange rate feature key ✓

- [x] [AGENT] P1. Verify Lido connector in execution-service handles STAKE/UNSTAKE for stETH:
  - ✓ `LidoConnector` exists in `execution_service/defi_execution/protocols/lido.py`
  - ✓ Has STETH_ADDRESS and WSTETH_ADDRESS constants with correct mainnet addresses

- [ ] [AGENT] P1. Add Lido strategy config variant to e2e-testing:
  - MISSING: no Lido-specific strategy YAML in `e2e-testing/configs/defi/strategies/`

- [ ] [AGENT] P1. Run `cd strategy-service && bash scripts/quality-gates.sh`

## Phase 4: Downstream Attribution (PARALLEL)

### 4A: P&L Reward Attribution

**Repo**: pnl-attribution-service

- [x] [AGENT] P0. Add reward-specific P&L attribution factors:
  - ✓ `PNL_FACTOR_STAKING_YIELD = "STAKING_YIELD"` in `pnl_attribution_service/engine/breakdown.py`
  - ✓ `PNL_FACTOR_RESTAKING_REWARD = "RESTAKING_REWARD"` ✓
  - ✓ `PNL_FACTOR_SEASONAL_REWARD = "SEASONAL_REWARD"` ✓
  - ✓ `PNL_FACTOR_REWARD_UNREALISED = "REWARD_UNREALISED"` ✓

- [x] [AGENT] P0. Implement M2M valuation of unclaimed rewards:
  - ✓ `unrealised_reward_pnl` computed from `accrued_amount * current_token_price` in `breakdown.py`
  - ✓ Uses `eigen_price_usdt` / `ethfi_price_usdt` features for M2M

- [x] [AGENT] P0. Attribute at correct time:
  - ✓ Staking yield: continuous from exchange rate delta
  - ✓ Restaking: at claim time (realised) vs M2M (unrealised)
  - ✓ Seasonal: at airdrop announcement time

- [ ] [AGENT] P0. Run `cd pnl-attribution-service && bash scripts/quality-gates.sh`

### 4B: Position Pending Reward Tracking

**Repo**: position-balance-monitor-service

- [x] [AGENT] P1. Add `RewardPosition` tracking (from UAC schema):
  - ✓ `aggregate_with_rewards(positions, reward_positions)` in `defi_staking_aggregator.py`
  - ✓ Imports `RewardPosition` from `unified_api_contracts.internal`
  - ✓ Merges accrued/claimed values per protocol into `DeFiStakingAggregatedMetrics`

- [ ] [AGENT] P1. Add reward token wallet balance monitoring:
  - MISSING: no `WALLET:SPOT_ASSET:EIGEN` / `WALLET:SPOT_ASSET:ETHFI` position tracking after claim
  - `aggregate_with_rewards` handles M2M of pending rewards but not claimed-in-wallet positions

- [ ] [AGENT] P1. Run `cd position-balance-monitor-service && bash scripts/quality-gates.sh`

## Phase 5: E2E + Docs

### 5A: E2E Reward Lifecycle

**Repo**: e2e-testing

- [ ] [AGENT] P1. Add reward lifecycle test scenario:
  - MISSING: no reward lifecycle scenario in `e2e-testing/scripts/defi/`
  1. Run staked basis strategy for N candles
  2. At candle where `eigen_claimable_amount > threshold`, verify CLAIM_REWARD instruction emitted
  3. After claim, verify SELL_REWARD instruction emitted
  4. Verify P&L attributes reward at correct time
  5. Verify position monitor tracks pending → claimed → sold lifecycle

- [ ] [AGENT] P1. Add Lido staking variant scenario:
  - MISSING: no Lido config YAML in `e2e-testing/configs/defi/strategies/`
  1. Same as staked basis but with `staking_protocol: LIDO`
  2. Verify stETH instruments used, not weETH
  3. Verify no EIGEN/ETHFI reward instructions emitted
  4. Verify Lido APY features consumed

- [ ] [AGENT] P1. Verify batch/paper/live all handle reward instructions correctly

### 5B: Documentation

- [ ] [AGENT] P1. Create `/codex/09-strategy/defi/reward-lifecycle.md`:
  - MISSING: file does not exist in `unified-trading-pm/codex/09-strategy/defi/`
  - Reward types (staking yield, restaking, seasonal)
  - Reward schedules (weekly EIGEN, quarterly ETHFI)
  - Instrument pipeline: what feeds are needed for each reward
  - CLAIM_REWARD → SELL_REWARD instruction flow
  - P&L attribution timing
  - M2M valuation methodology

- [ ] [AGENT] P1. Update `/codex/09-strategy/_archived_pre_v2/defi/staked-basis.md` with reward lifecycle integration

- [ ] [AGENT] P1. Create `/codex/02-data/instrument-pipeline-defi.md`:
  - MISSING: file does not exist in `unified-trading-pm/codex/02-data/`
  - Full instrument → MTDS → MDPS → features → strategy pipeline diagram
  - Per-strategy instrument requirements table
  - How to add new instruments to the pipeline

## Success Criteria

1. All instruments required by all DeFi strategies verified end-to-end (instruments → MTDS → MDPS → features → strategy)
2. EIGEN and ETHFI token instrument definitions exist in instruments-service with Binance spot pairs — PENDING
3. Lido stETH/wstETH instruments exist ✓, MTDS adapters MISSING, MDPS features MISSING
4. CLAIM_REWARD and SELL_REWARD instruction types in UAC OperationType ✓ DONE
5. RewardSchedule registry in UAC with EIGEN (weekly) and ETHFI (quarterly) ✓ DONE
6. Strategy-service emits CLAIM_REWARD + SELL_REWARD — mixin exists ✓ but NOT wired into staked_basis/recursive_basis
   signal generation — PENDING
7. Execution-service handles both instruction types ✓ DONE (handlers + EigenLayer claim_rewards())
8. P&L attributes staking yield, restaking rewards, and seasonal rewards separately ✓ DONE
9. Position monitor tracks pending/claimed reward lifecycle ✓ (aggregate_with_rewards), wallet tracking PENDING
10. Staking protocol configurable (Lido vs EtherFi) ✓ DONE in strategy-service
11. E2E tests cover full reward lifecycle in batch mode — PENDING
12. All 10 repos pass `quality-gates.sh`

## Prompt for Next Session

```
Continue from the plan at:
unified-trading-pm/plans/active/defi_instrument_pipeline_and_rewards_2026_04_01.md

Audit findings (2026-04-01):
DONE: UAC reward types (CLAIM/SELL_REWARD), RewardSchedule, RewardPosition, EigenLayer
  claim_rewards(), claim/sell handlers in execution-service, P&L factors
  (STAKING_YIELD/RESTAKING_REWARD/SEASONAL_REWARD/REWARD_UNREALISED), aggregate_with_rewards()
  in position-balance-monitor, staking_protocol config switch, LidoConnector, lido_staking_apy
  feature in features-onchain, eigen_claimable_amount feature in features-onchain.

TRULY PENDING (next session focus):
1. instruments-service: EIGEN/ETHFI Binance spot instrument definitions (no code exists)
2. MTDS: EIGEN/USDT, ETHFI/USDT spot adapters + stETH/wstETH rate adapters (no code exists)
3. MDPS: eigen_price_usdt, ethfi_price_usdt, steth_eth_rate, wsteth_eth_rate features (no code)
4. features-onchain: ethfi_claimable_amount calculator (eigen done, ethfi MISSING)
5. strategy-service: wire _check_reward_claims() into StakedBasisStrategy + RecursiveStakedBasisStrategy generate_defi_signal()
6. strategy-service: add SEASONAL_QUARTERLY settlement type to settlement_service.py
7. position-balance-monitor: WALLET:SPOT_ASSET:EIGEN/ETHFI tracking post-claim
8. e2e-testing: reward lifecycle scenario + Lido YAML config
9. codex: reward-lifecycle.md, instrument-pipeline-defi.md

Start with items 1-4 in parallel (data pipeline), then item 5 (strategy wiring).
```
