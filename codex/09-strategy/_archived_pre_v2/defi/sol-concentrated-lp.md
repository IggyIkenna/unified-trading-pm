---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Solana Concentrated Liquidity LP (Raydium / Orca)

> **Asset class:** DeFi **Strategy type:** Market Making via Concentrated LP (fee collection, active range management)
> **Strategy ID pattern:** `DEFI_SOL_LP_{VENUE}_{GRANULARITY}`

## Overview

Provide concentrated liquidity on Solana DEXs (Raydium CLMM pools, Orca Whirlpools) within a tight price range around
the current spot price. Earns trading fees from swap volume flowing through the position's active tick range. Solana's
high throughput (400ms block times, ~4000 TPS) generates significantly more swaps per second than Ethereum, translating
to higher fee revenue per unit of liquidity deployed. Low rebalancing cost (~0.002 SOL / ~$0.30) enables aggressive
range management that would be uneconomical on Ethereum L1.

## How This Fits the Unified Trading System

Same event-driven architecture as Ethereum LP strategies. Strategy receives features (pool metrics, SOL price,
volatility), decides when to add/remove/rebalance liquidity, and emits instructions. Strategy NEVER reads pool state
directly -- features-onchain-service computes pool metrics from on-chain data and publishes them.

```
features-onchain-service (publishes: pool_price, pool_volume_24h, pool_tvl, pool_fee_rate, pool_tick_range, position_in_range)
  -> pub/sub event (on price move > threshold OR every 15M periodic)
    -> strategy-service receives event
      -> strategy.generate_signal(features, positions, risk)
        -> emit StrategyInstruction (ADD_LIQUIDITY / REMOVE_LIQUIDITY / REBALANCE_RANGE)
```

## Pool Types & Mechanics

| Pool Type      | Venue          | Liquidity Model                    | LP Token           | IL Profile             |
| -------------- | -------------- | ---------------------------------- | ------------------ | ---------------------- |
| Raydium CLMM   | RAYDIUM-SOLANA | Concentrated (tick range, V3-like) | NFT position (SPL) | Amplified within range |
| Orca Whirlpool | ORCA-SOLANA    | Concentrated (tick range)          | NFT position (SPL) | Amplified within range |

### Raydium CLMM (primary venue)

Raydium's Concentrated Liquidity Market Maker is architecturally equivalent to Uniswap V3 but built on Solana:

- Same tick-based price range model: `[tickLower, tickUpper]`
- Within range: liquidity earns fees on every swap routed through the pool
- Outside range: earns zero fees, holds 100% of the depreciating token
- Key advantage over Ethereum V3: rebalancing costs ~0.002 SOL vs ~$5-50 on Ethereum, enabling tighter ranges
- Fee tiers: 0.01%, 0.05%, 0.25%, 1%

### Orca Whirlpools

Orca's concentrated liquidity implementation with additional reward incentives:

- Same concentrated liquidity mechanics as Raydium CLMM
- Built-in reward distribution (ORCA token incentives on select pools)
- Slightly different tick spacing configuration per fee tier
- Fee tiers: 0.01%, 0.02%, 0.04%, 0.08%, 0.16%, 0.64%, 1.28%

### Top Pools by Strategy Suitability

| Pool        | Venue   | Fee Tier | 24h Volume (typical) | TVL (typical) | IL Profile                    |
| ----------- | ------- | -------- | -------------------- | ------------- | ----------------------------- |
| SOL/USDC    | Raydium | 0.25%    | $50-200M             | $30-80M       | Standard (volatile pair)      |
| USDC/USDT   | Raydium | 0.01%    | $10-50M              | $20-40M       | Minimal (stable-stable)       |
| mSOL/SOL    | Orca    | 0.01%    | $5-20M               | $15-30M       | Very low (liquid staking arb) |
| SOL/USDC    | Orca    | 0.04%    | $20-80M              | $20-50M       | Standard (volatile pair)      |
| jitoSOL/SOL | Orca    | 0.01%    | $3-10M               | $10-20M       | Very low (liquid staking arb) |

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:SOL + WALLET:SPOT_ASSET:USDC

Step 1 - ADD_LIQUIDITY:
  Deposit SOL + USDC into Raydium CLMM pool within [tickLower, tickUpper]
  Range example: SOL @ $150, range = [$142.50, $157.50] (+/- 5%)
  Receive: SPL NFT position token representing LP position

Wallet after deploy:
  - RAYDIUM-SOLANA:LP_POSITION:SOL-USDC@SOLANA = NFT position
  - Accruing: swap fees in SOL + USDC (claimable via COLLECT_FEES)

On rebalance (price exits range, checked every 15M):
Step 2 - REMOVE_LIQUIDITY: burn NFT, receive SOL + USDC
Step 3 - ADD_LIQUIDITY: deposit at new range centered on current price
  Gas cost: ~0.004 SOL total (~$0.60 for remove + re-add)

On exit:
Step 4 - REMOVE_LIQUIDITY + COLLECT_FEES: burn NFT, claim all accrued fees

Optional IL hedge (delta-neutral variant):
Step 5 - OPEN_SHORT: short SOL-PERP on Drift Protocol to hedge directional exposure
  This converts the LP from directional to delta-neutral, isolating fee income from price risk
```

## Instruments

| Instrument Key                               | Venue   | Type      | Role                     |
| -------------------------------------------- | ------- | --------- | ------------------------ |
| `RAYDIUM-SOLANA:LP_POSITION:SOL-USDC@SOLANA` | Raydium | LP NFT    | Active LP position       |
| `ORCA-SOLANA:LP_POSITION:SOL-USDC@SOLANA`    | Orca    | LP NFT    | Active LP position (alt) |
| `RAYDIUM-SOLANA:POOL:SOL/USDC`               | Raydium | Pool      | Pool reference           |
| `ORCA-SOLANA:POOL:SOL/USDC`                  | Orca    | Pool      | Pool reference (alt)     |
| `WALLET:SPOT_ASSET:SOL`                      | Wallet  | Spot      | Deposited asset          |
| `WALLET:SPOT_ASSET:USDC`                     | Wallet  | Spot      | Deposited asset          |
| `DRIFT-SOLANA:PERP:SOL-PERP`                 | Drift   | Perpetual | IL hedge (optional)      |

## Key Features Consumed

| Feature             | Source Service      | SLA | Used For                                    |
| ------------------- | ------------------- | --- | ------------------------------------------- |
| `pool_volume_24h`   | features-onchain    | 60s | Fee APY estimation, pool selection          |
| `pool_tvl`          | features-onchain    | 60s | Concentration risk, capital efficiency      |
| `pool_fee_rate`     | features-onchain    | 60s | Revenue calculation                         |
| `sol_price`         | features-onchain    | 5s  | Rebalance trigger, range boundary check     |
| `pool_tick_range`   | features-onchain    | 15s | Current active tick vs position range       |
| `position_in_range` | features-onchain    | 15s | Boolean: is position earning fees?          |
| `realized_vol_1h`   | features-volatility | 60s | Range width sizing (wider range in vol)     |
| `sol_funding_rate`  | features-delta-one  | 60s | Drift hedge cost (if delta-neutral variant) |

## Data Architecture

| Dimension              | Value                                                      | SSOT                          |
| ---------------------- | ---------------------------------------------------------- | ----------------------------- |
| **Raw data source**    | NEVER direct -- via features-onchain-service               | Hard rule                     |
| **Features consumed**  | Pool metrics from Raydium/Orca on-chain programs via RPC   | `features-onchain-service`    |
| **Interval**           | Event-driven on price move OR periodic 15M rebalance check | Strategy trigger subscription |
| **Lowest granularity** | Per-slot (~400ms on Solana) via feature service            | Feature service config        |

## Instruction Types Needed

| Operation          | What It Does                            | Parameters                                                      | Exists?                    |
| ------------------ | --------------------------------------- | --------------------------------------------------------------- | -------------------------- |
| `ADD_LIQUIDITY`    | Deposit tokens into CLMM/Whirlpool      | pool_id, token_amounts[], tick_lower, tick_upper, min_amounts[] | **NO -- needs adding**     |
| `REMOVE_LIQUIDITY` | Burn LP NFT, withdraw assets            | pool_id, position_nft_id, min_amounts[]                         | **NO -- needs adding**     |
| `COLLECT_FEES`     | Claim accrued fees from LP position     | position_nft_id                                                 | **NO -- needs adding**     |
| `REBALANCE`        | Remove + re-add at new range (compound) | old_position_id, new_tick_lower, new_tick_upper                 | EXISTS (needs LP metadata) |
| `OPEN_SHORT`       | Hedge via Drift perpetual               | instrument_key, size, leverage                                  | EXISTS                     |

## Smart Order Routing (SOR)

**SOR applies to POOL SELECTION across venues and fee tiers:**

For SOL/USDC, multiple pools exist across both Raydium and Orca with different fee tiers. Strategy selects based on:

- **Volume-to-TVL ratio:** higher ratio = more fee revenue per dollar of liquidity
- **Fee tier match:** volatile pairs benefit from higher fee tiers (0.25%), stable pairs from lower (0.01%)
- **Reward incentives:** Orca Whirlpools may offer additional ORCA rewards that shift the optimal venue
- **Existing position concentration:** avoid being >5% of pool TVL (adverse selection risk)

> Strategy-service handles pool selection. Execution-service just executes the add/remove instruction against the
> selected pool.

## PnL Attribution

| Component           | Settlement Type               | Mechanism                                            |
| ------------------- | ----------------------------- | ---------------------------------------------------- |
| `fee_income_pnl`    | `LP_FEE_ACCRUAL` (per period) | Fees earned from swappers trading through position   |
| `il_pnl`            | Mark-to-market                | Impermanent loss from SOL price divergence           |
| `inventory_pnl`     | Mark-to-market                | Value change of SOL + USDC held in pool              |
| `reward_pnl`        | Claim-based                   | ORCA/RAY reward token incentives (if applicable)     |
| `hedge_pnl`         | Funding settlement            | Drift perp funding payments (delta-neutral variant)  |
| `transaction_costs` | Per-fill                      | Gas for add/remove/rebalance (~0.002-0.004 SOL each) |

**Source of truth:**
`total_pnl = (current_position_value + collected_fees + claimed_rewards) - initial_deposit - hedge_cost`

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern             | Exposure Type       | Used For                            |
| ------------------------------ | ------------------- | ----------------------------------- |
| `RAYDIUM-SOLANA:LP_POSITION:*` | LP position value   | Total deployed capital tracking     |
| `ORCA-SOLANA:LP_POSITION:*`    | LP position value   | Total deployed capital tracking     |
| `WALLET:SPOT_ASSET:SOL`        | Spot SOL balance    | Available capital for rebalance     |
| `WALLET:SPOT_ASSET:USDC`       | Spot USDC balance   | Available capital for rebalance     |
| `DRIFT-SOLANA:PERP:SOL-PERP`   | Short perp notional | Hedge delta (delta-neutral variant) |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type          | Subscribed? | Threshold                           | Action on Breach                          |
| ------------------ | ----------- | ----------------------------------- | ----------------------------------------- |
| `impermanent_loss` | YES         | IL > 5% of position value           | Widen range or exit position              |
| `delta`            | YES         | Net delta drift > 3% (hedged mode)  | Adjust Drift short size                   |
| `protocol_risk`    | YES         | Smart contract exploit, pool freeze | Emergency exit all positions              |
| `liquidity`        | YES         | Pool TVL drops > 30% in 24h         | Exit (liquidity flight signal)            |
| `concentration`    | YES         | Our share of pool TVL > 5%          | Reduce position size                      |
| `mev`              | YES         | Sandwich loss > 50bps per rebalance | Switch to Jito bundles for MEV protection |
| `funding`          | YES (hedge) | Drift funding > -20% annualized     | Close hedge, accept directional exposure  |
| `basis`            | NO          | --                                  | --                                        |

**SSOT:** `component_config.risk_monitor.enabled_risk_types` in strategy config. Schema:
[`RiskMonitorConfig`](../../strategy-service/strategy_service/config.py) Formal subscription type:
[`StrategyRiskProfile`](../../unified-api-contracts/unified_api_contracts/internal/risk.py)

### Custom Strategy Risk Types

| Custom Risk            | What It Measures                                     | Evaluation Method  | SSOT          |
| ---------------------- | ---------------------------------------------------- | ------------------ | ------------- |
| Range utilisation      | % of time price stays within LP range (target: >85%) | `rate_sensitivity` | Strategy logs |
| Fee APY vs IL          | Net profitability: fee_apy - annualized_IL           | `threshold_breach` | Strategy logs |
| MEV sandwich loss      | Cost of sandwich attacks on rebalance transactions   | monitoring         | Jito explorer |
| Pool TVL concentration | Our % of pool TVL -- adverse selection if too high   | `threshold_breach` | On-chain      |
| Rebalance frequency    | Rebalances per day -- too many = gas drag            | monitoring         | Strategy logs |

## Risk Profile

| Metric               | Target       | Notes                                                         |
| -------------------- | ------------ | ------------------------------------------------------------- |
| Target annual return | 20-60%       | Highly variable: depends on SOL volatility and pool volume    |
| Target Sharpe ratio  | 1.2-2.0      | Higher with delta-neutral hedge, lower without                |
| Max drawdown         | 20%          | Primarily from IL during large SOL price moves                |
| Max leverage         | 1x (LP) / 2x | 1x for LP, optional 1x short on Drift for hedge               |
| Capital scalability  | $2M per pool | Solana pools have lower TVL than Ethereum -- smaller capacity |

## Latency Profile

| Segment                              | p50 Target | p99 Target | Co-location Needed? |
| ------------------------------------ | ---------- | ---------- | ------------------- |
| Market data -> feature               | 200ms      | 800ms      | No                  |
| Feature -> signal                    | 30ms       | 100ms      | No                  |
| Signal -> instruction                | 10ms       | 50ms       | No                  |
| Instruction -> on-chain (add/remove) | 500ms      | 3s         | No                  |
| **End-to-end**                       | **~750ms** | **~4s**    | **No**              |

Solana's 400ms block times mean on-chain confirmation is much faster than Ethereum (~12s). Rebalancing is not
latency-critical -- the 15M check interval means a few seconds of delay is acceptable.

## Execution Details

- **Venues:** Raydium CLMM (RAYDIUM-SOLANA, primary), Orca Whirlpools (ORCA-SOLANA, secondary)
- **Order types:** Protocol interactions (not order book) -- Solana program invocations
- **Atomic execution required?** No for standard LP. Yes for delta-neutral variant (LP add + Drift short should be
  near-atomic to avoid delta exposure window)
- **Gas budget:** ~0.002 SOL per add/remove (~$0.30), ~0.004 SOL per full rebalance (~$0.60)

### Rebalancing

**Trigger type:** Periodic check every 15 minutes. Event-driven emergency rebalance on large price moves.

| Level    | Condition                             | Action                                                 |
| -------- | ------------------------------------- | ------------------------------------------------------ |
| Normal   | Price within range, fees accruing     | No action                                              |
| Minor    | Price near range edge (within 2%)     | Log, prepare rebalance parameters                      |
| Major    | Price exits range (earning 0 fees)    | Remove + re-add at new range centered on current price |
| Critical | IL exceeds 5% OR pool TVL drops > 30% | Full exit, return to flat (SOL + USDC in wallet)       |

**Range width sizing:** Based on realized volatility. Low vol -> +/- 3% range (higher capital efficiency). High vol ->
+/- 8% range (fewer rebalances, lower gas drag). Formula: `range_half_width = 2.5 * realized_vol_1h * sqrt(15/60)`.

### IL Hedging (Optional Delta-Neutral Variant)

When enabled, the strategy opens a short SOL-PERP position on Drift Protocol sized to offset the SOL delta of the LP
position. This converts the strategy from directional to delta-neutral, isolating fee income from SOL price movements.

- Hedge ratio: dynamically adjusted as LP position's SOL delta changes with price
- Cost: Drift funding rate (typically positive = short pays, negative = short receives)
- Net effect: reduces return variance, may reduce or increase absolute return depending on funding

## Margin & Liquidation

- **Margin model:** None for LP position (fully funded, no leverage, no debt)
- **Drift hedge margin:** Cross margin on Drift, initial margin 5%, maintenance margin 3.125%
- **Liquidation risk:** None for LP. For Drift hedge: liquidation if SOL moves against short by >30x leverage
- **IL risk:** Position value can decrease vs holding -- not liquidation but real economic loss
- **Smart contract risk:** Raydium/Orca program exploit, Solana runtime bug, oracle manipulation
- **Health factor monitoring:** N/A for LP (no borrowing). Drift: monitored via features-delta-one

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue          | Secret Name                      | Testnet Available? | Notes                          |
| -------------- | -------------------------------- | ------------------ | ------------------------------ |
| RAYDIUM-SOLANA | `defi-wallet-private-key-solana` | Yes (devnet)       | Solana wallet keypair          |
| ORCA-SOLANA    | `defi-wallet-private-key-solana` | Yes (devnet)       | Same wallet, different program |
| DRIFT-SOLANA   | `defi-wallet-private-key-solana` | Yes (devnet)       | Same wallet for hedge          |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Solana wallet (same keypair works across all Solana venues)
2. **Secret Manager:** `defi-wallet-private-key-solana-{client}` -- Solana keypair JSON
3. **Config:** New entry in strategy config YAML with client-specific params (pool selection, range width, hedge flag)
4. **Position isolation:** One strategy instance per client (positions diverge due to execution timing and range
   choices)
5. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                        | Restart?        |
| ----------------- | ----------------------------------- | --------------- |
| strategy-service  | New config entry with pool + params | No (hot-reload) |
| execution-service | New client Solana wallet routing    | No (hot-reload) |
| features-onchain  | Pool subscription (if new pool)     | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Position breakdown (LP position value, accrued fees, IL)
- Margin health time series (Drift hedge only)

### Strategy-specific views (extensions)

- LP range visualisation: current price vs position range boundaries (candlestick with shaded range overlay)
- Fee APY vs IL real-time chart: fee income accrual rate vs impermanent loss accumulation
- Range utilisation heatmap: historical % of time price was within range per hour
- Rebalance event log: timestamp, old range, new range, gas cost, reason
- Pool comparison dashboard: volume/TVL ratio across Raydium vs Orca pools for same pair

## Testing Stage Status

| Stage        | Status  | Notes                                                         |
| ------------ | ------- | ------------------------------------------------------------- |
| MOCK         | Pending | Need MockCLMMPool with price simulation + fee accrual on SOL  |
| HISTORICAL   | Pending | Raydium/Orca pool data available via Solana RPC + indexers    |
| LIVE_MOCK    | Pending | Blocked by ADD_LIQUIDITY operation type + Solana adapter gaps |
| LIVE_TESTNET | Pending | Raydium devnet, Orca devnet available                         |
| BATCH_REAL   | Pending | Historical pool data backfill needed from Solana indexers     |
| STAGING      | Pending | Solana devnet fork or Bankrun simulation                      |
| LIVE_REAL    | Pending | All above + IL risk accepted + Solana wallet funded           |

## Wallet & Capital Flow

| Component        | Value                                                           |
| ---------------- | --------------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                      |
| Hot wallet       | Solana wallet, per-strategy isolated                            |
| CeFi sub-account | No (optional Drift sub-account for delta-neutral hedge variant) |
| Bridge required  | No (single-chain -- Solana only)                                |
| Custody          | Copper MPC                                                      |

Capital flow: Client deposit --> treasury --> hot wallet (Solana) --> ADD_LIQUIDITY to Raydium/Orca pool (SOL + USDC
from wallet). Rebalance: REMOVE_LIQUIDITY + re-ADD_LIQUIDITY at new range (all on Solana, ~$0.60 total gas). Exit:
REMOVE_LIQUIDITY + COLLECT_FEES --> TRANSFER --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked via Alchemy RPC using `getRecentPrioritizationFees` (Solana). The MTDS `gas_fee_handler` fetches
real-time priority fees and writes them as features. Gas hits P&L immediately as a realized transaction cost -- not
estimated. Solana LP operations cost ~0.002-0.004 SOL per add/remove (~$0.30-0.60), enabling aggressive range management
that would be uneconomical on Ethereum L1 (~$50-100 per rebalance).

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md).
Solana DEX pools (Raydium, Orca) require BOTH sides to be in `DEFI_MAJOR_ASSET_SYMBOLS` with a **$10k TVL minimum**
(client-side filter -- Solana DEXes return all pools via REST API). Solana tokens now include LSTs and ecosystem tokens
(35+ in `SOLANA_TOKEN_ADDRESSES`), enabling LP on pairs like SOL/USDC, mSOL/SOL, jitoSOL/SOL.

## References

- **Implementation:** TBD -- Solana LP strategy not yet implemented
- **Strategy ID:** `DEFI_SOL_LP_RAYDIUM_15M` (Raydium primary), `DEFI_SOL_LP_ORCA_15M` (Orca variant)
- **Pool data adapters:** TBD -- Solana on-chain adapters for Raydium CLMM / Orca Whirlpool programs
- **Venue capabilities:** `VENUE_CAPABILITIES.PROVIDE_LIQUIDITY` in `venue_constants.py`
- **Drift hedge:** `execution-service/execution_service/defi_execution/` (Solana perp connectors)
- **Hard rules:** [config-architecture.md](../cross-cutting/config-architecture.md)
