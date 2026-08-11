---
doc_type: codex-ssot
title: Staking Reward Lifecycle -- Cross-Cutting Concern
summary:
  "Staking reward-token lifecycle — accrue → claim (`CLAIM_REWARD`) → sell (`SELL_REWARD`) → attribute — for EigenLayer
  (EIGEN, weekly) and EtherFi (ETHFI, quarterly); Lido has no reward token (yield via wstETH rate only). Thresholds $50
  claim / $100 sell, 24h claim cooldown; `CLAIM_REWARD`/`SELL_REWARD` distinct from `COLLECT_FEES`/`SWAP`."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, features-service, strategy-service]
scope: [engineer, admin]
tags: [defi, strategy, execution, features, pnl-attribution]
related: [/codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md, /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md]
created: 2026-04-03
authoritative_for: [staking-reward lifecycle (accrue/claim/sell/attribute) + CLAIM_REWARD/SELL_REWARD operation types]
referenced_by:
  [
    /codex/02-data/instrument-pipeline-defi.md,
    /codex/04-architecture/client-config-and-risk-dimensions.md,
    /codex/09-strategy/README.md,
    /codex/09-strategy/_archived_pre_v2/defi/staked-basis.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /codex/09-strategy/architecture-v2/cross-cutting/restaking-reward-economics.md,
    /codex/09-strategy/architecture-v2/families/carry-and-yield.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Staking Reward Lifecycle -- Cross-Cutting Concern

## Overview

Staking protocols distribute reward tokens alongside their base yield. These rewards follow a lifecycle: accrue on the
protocol, claim via on-chain transaction, sell for base currency, and attribute to P&L. The reward lifecycle is relevant
to any strategy that holds liquid staking tokens (weETH, wstETH) or deposits collateral into lending/restaking
protocols.

## Supported Protocols

| Protocol   | Reward Token | Distribution Frequency | Claim Contract      | Notes                                   |
| ---------- | ------------ | ---------------------- | ------------------- | --------------------------------------- |
| EigenLayer | EIGEN        | Weekly (Mondays)       | EigenLayer Claiming | Restaking rewards. Requires delegation. |
| EtherFi    | ETHFI        | Quarterly              | EtherFi Claiming    | Protocol governance token.              |
| Lido       | None         | N/A                    | N/A                 | Yield accrues via wstETH/ETH rate only. |

Lido does not distribute separate reward tokens. All yield flows through the stETH/wstETH exchange rate appreciation.
Strategies using Lido skip the reward lifecycle entirely.

## Lifecycle Stages

### 1. Accrue

Rewards accumulate on the protocol between distribution events. The strategy tracks expected accrual via the
`weekly_rewards` feature from `features-service (onchain family)`. During this stage, rewards are attributed to
`PNL_FACTOR_REWARD_UNREALISED` in P&L reporting.

No on-chain action is required during accrual. The unrealised reward amount is estimated from protocol distribution
schedules and the strategy's share of the staking pool.

### 2. Claim

Claiming transfers accrued reward tokens from the protocol to the strategy's wallet.

- **Operation type:** `CLAIM_REWARD` (distinct from `COLLECT_FEES` which is LP fee harvest)
- **Min claim threshold:** $50 (configurable via `min_claim_threshold_usd`)
- **Max frequency:** Once per 24 hours (configurable via `claim_cooldown_hours`)
- **Gas cost:** ~150k gas for EigenLayer claim, ~100k gas for EtherFi claim

The claim is triggered automatically when the accrued value exceeds the threshold. The strategy emits a
`StrategyInstruction` with `operation_type=CLAIM_REWARD` and `reward_token=EIGEN` or `ETHFI`. Execution-service handles
the on-chain transaction.

### 3. Sell

Selling converts claimed reward tokens to the strategy's base currency (WETH for DeFi strategies, USDT for stablecoin
strategies).

- **Operation type:** `SELL_REWARD` (distinct from regular SWAP)
- **Min sell threshold:** $100 (configurable via `min_sell_threshold_usd`)
- **Sell venue:** Binance spot (for liquid tokens with CEX listing) or Uniswap V3 (for on-chain-only tokens)
- **Slippage protection:** `max_slippage_bps` from strategy config (default: 100 bps for reward tokens due to lower
  liquidity)

The sell is triggered when wallet balance of the reward token exceeds the threshold. For small amounts, batching
multiple claims before selling reduces gas cost per unit sold.

### 4. Attribute

Once sold, the realized proceeds are attributed to P&L:

| Reward Token | P&L Factor                     | Attribution Notes                                 |
| ------------ | ------------------------------ | ------------------------------------------------- |
| EIGEN        | `PNL_FACTOR_RESTAKING_REWARD`  | Restaking protocol reward. Weekly.                |
| ETHFI        | `PNL_FACTOR_SEASONAL_REWARD`   | Protocol governance token. Quarterly.             |
| Unrealised   | `PNL_FACTOR_REWARD_UNREALISED` | Estimated value of accrued but unclaimed rewards. |

The `PNL_FACTOR_STAKING_YIELD` factor is reserved for the base LST yield (weETH/wstETH rate appreciation) and is NOT
used for reward tokens. This separation ensures clear attribution: base yield vs bonus rewards.

## Operation Types

The reward lifecycle introduces two operation types that are distinct from regular trading operations:

| Operation Type | What It Does                                 | Distinct From       |
| -------------- | -------------------------------------------- | ------------------- |
| `CLAIM_REWARD` | Claims accrued reward tokens from a protocol | `COLLECT_FEES` (LP) |
| `SELL_REWARD`  | Sells reward tokens for base currency        | `SWAP` (regular)    |

`COLLECT_FEES` is used for AMM LP fee harvesting (Uniswap V3 fee collection). `CLAIM_REWARD` is exclusively for staking
protocol reward tokens. `SELL_REWARD` is tracked separately from `SWAP` so that P&L attribution can distinguish reward
token sales from regular position rebalancing.

## Frequency and Scheduling

- **Claim check:** Every candle (1H default). If accrued > threshold and cooldown elapsed, emit claim instruction.
- **Sell check:** Every candle. If wallet balance > threshold, emit sell instruction.
- **Max claim frequency:** Once per 24 hours (prevents gas waste on frequent small claims).
- **Configurable via:** `staking_rewards` section in strategy config:
  ```
  staking_rewards:
    enabled: true
    min_claim_threshold_usd: 50
    min_sell_threshold_usd: 100
    claim_cooldown_hours: 24
    sell_venue: "BINANCE"    # or "UNISWAP_V3-ETHEREUM"
    max_slippage_bps: 100
  ```

## Implementation

- **Strategy-side:** `RewardClaimMixin` in `strategy-service/strategy_service/engine/strategies/defi_enhancements.py`
  - Tracks accrued rewards from features
  - Emits `CLAIM_REWARD` and `SELL_REWARD` instructions when thresholds met
  - Enforces cooldown between claims
- **Execution-side:**
  - `ClaimRewardHandler` in execution-service -- handles on-chain claim transactions for EigenLayer/EtherFi
  - `SellRewardHandler` in execution-service -- handles reward token sales (CEX or DEX)
- **Contracts:** `RewardPosition` in UAC -- tracks reward token balances and accrual state
- **P&L:** `PnLCalculator` reads reward sell proceeds and maps to the correct P&L factor based on token type

## Strategy Applicability

| Strategy               | Reward Lifecycle Active? | Reward Tokens | Notes                           |
| ---------------------- | ------------------------ | ------------- | ------------------------------- |
| Basis Trade            | No                       | None          | No staking positions.           |
| Staked Basis (EtherFi) | Yes                      | EIGEN, ETHFI  | Full lifecycle.                 |
| Staked Basis (Lido)    | No                       | None          | Lido has no separate rewards.   |
| Recursive Staked Basis | Yes                      | EIGEN, ETHFI  | Leveraged rewards (higher APY). |
| AAVE Lending           | No                       | None          | Pure lending, no staking.       |
