---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# DeFi Market Making (AMM Liquidity Provision)

> **Asset class:** DeFi **Strategy type:** Market Making via AMM LP (concentrated liquidity, fee collection) **Strategy
> ID pattern:** `DEFI_{PAIR}_MM_LP_{POOL_TYPE}_EVT_{GRANULARITY}`

## Overview

Provide liquidity to AMM pools (Uniswap V2/V3/V4, Curve, Balancer) and earn swap fees. The DeFi equivalent of
market-making: instead of posting bid/ask on an order book, you deposit assets into a pool within a price range.
Swappers trade against your liquidity and you earn fees.

Key difference from CeFi MM: no order book, no bid/ask quotes. Instead you define a price RANGE and the AMM
automatically makes markets for you within that range.

## How This Fits the Unified Trading System

Same event-driven architecture. Strategy receives features (pool metrics, price, volatility), decides when to
add/remove/rebalance liquidity, and emits instructions. Strategy NEVER reads pool state directly —
features-onchain-service computes pool metrics and publishes them.

```
features-onchain-service (publishes: pool_price, tick, fee_apy, IL_pct, utilization)
  → pub/sub event (on price move > threshold OR periodic)
    → strategy-service receives event
      → strategy.generate_signal(features, positions, risk)
        → emit StrategyInstruction (ADD_LIQUIDITY / REMOVE_LIQUIDITY / REBALANCE_RANGE)
```

## Pool Types & Mechanics

| Pool Type  | Venue               | Liquidity Model                         | LP Token                       | IL Profile                       |
| ---------- | ------------------- | --------------------------------------- | ------------------------------ | -------------------------------- |
| Uniswap V2 | UNISWAP_V2-ETHEREUM | Uniform (0→∞)                           | ERC-20 (fungible)              | Standard (~5.7% at 2x move)      |
| Uniswap V3 | UNISWAP_V3-ETHEREUM | Concentrated (tick range)               | ERC-721 NFT (unique per range) | Amplified within range           |
| Uniswap V4 | UNISWAP_V4-ETHEREUM | Concentrated + hooks                    | ERC-721 NFT                    | Hook-dependent                   |
| Curve      | CURVE-ETHEREUM      | StableSwap (auto-concentrated near peg) | ERC-20 (fungible)              | Very low for like-kind assets    |
| Balancer   | BALANCER-ETH        | Weighted (custom weights 2-8 tokens)    | ERC-20 (fungible)              | Weight-dependent (80/20 < 50/50) |

### Uniswap V3 Concentrated Liquidity (primary use case)

Strategy provides liquidity in a specific price range `[tickLower, tickUpper]`:

- Within range: your liquidity earns fees on every swap
- Outside range: earns zero fees, holds 100% of the depreciating token
- Rebalancing: when price exits range, must remove + re-add at new range

Capital efficiency: up to 4000x vs V2 for tight ranges. Trade-off: higher IL within range.

### Curve StableSwap

For like-kind assets (USDT/USDC/DAI, ETH/stETH, ETH/weETH):

- Amplification parameter `A` concentrates liquidity near peg automatically
- LP cannot choose custom range — the algorithm does it
- Much lower IL for pegged assets (100-1000x less slippage than Uniswap V2)

## Token / Position Flow (Uniswap V3 Example)

```
Start:  WALLET:SPOT_ASSET:USDT + WALLET:SPOT_ASSET:ETH

Step 1 - ADD_LIQUIDITY:
  Deposit ETH + USDT into Uniswap V3 pool within [tickLower, tickUpper]
  Receive: NFT position token representing your LP position

Wallet after deploy:
  - UNISWAP_V3-ETHEREUM:LP_POSITION:ETH-USDT@ETHEREUM = NFT position
  - Accruing: swap fees in ETH + USDT (claimable via COLLECT_FEES)

On rebalance (price exits range):
Step 2 - REMOVE_LIQUIDITY: burn NFT, receive ETH + USDT
Step 3 - ADD_LIQUIDITY: deposit at new range [newTickLower, newTickUpper]

On exit:
Step 4 - REMOVE_LIQUIDITY + COLLECT_FEES: burn NFT, claim all fees
```

## Instruments

| Instrument Key                                      | Venue      | Type   | Role               |
| --------------------------------------------------- | ---------- | ------ | ------------------ |
| `UNISWAP_V3-ETHEREUM:LP_POSITION:ETH-USDT@ETHEREUM` | Uniswap V3 | LP NFT | Active LP position |
| `WALLET:SPOT_ASSET:ETH`                             | Wallet     | Spot   | Deposited asset    |
| `WALLET:SPOT_ASSET:USDT`                            | Wallet     | Spot   | Deposited asset    |

## Key Features Consumed

| Feature        | Source Service      | Trigger                | Used For                        |
| -------------- | ------------------- | ---------------------- | ------------------------------- |
| `pool_price`   | features-onchain    | Price move > threshold | Rebalance trigger               |
| `current_tick` | features-onchain    | Tick change            | Range vs current position check |
| `fee_apy_24h`  | features-onchain    | Periodic (1h)          | Is LP profitable?               |
| `il_pct`       | features-onchain    | Price move             | IL monitoring                   |
| `pool_tvl`     | features-onchain    | Periodic (1h)          | Concentration / crowding risk   |
| `realized_vol` | features-volatility | Periodic (5m)          | Range width decision            |

## Data Architecture

| Dimension              | Value                                                      | SSOT                          |
| ---------------------- | ---------------------------------------------------------- | ----------------------------- |
| **Raw data source**    | NEVER direct — via features-onchain-service                | Hard rule                     |
| **Features consumed**  | Pool metrics computed from The Graph + RPC                 | `features-onchain-service`    |
| **Interval**           | Event-driven on price move OR periodic for rebalance check | Strategy trigger subscription |
| **Lowest granularity** | Per-block (~12s on Ethereum) via feature service           | Feature service config        |

## Instruction Types Needed

> **TODO — CODIFY:** New `OperationType` values needed in both UAC and UDEI:

| Operation          | What It Does                            | Parameters                                                      | Exists?                        |
| ------------------ | --------------------------------------- | --------------------------------------------------------------- | ------------------------------ |
| `ADD_LIQUIDITY`    | Deposit tokens into AMM pool            | pool_id, token_amounts[], tick_lower, tick_upper, min_amounts[] | **NO — needs adding**          |
| `REMOVE_LIQUIDITY` | Burn LP token, withdraw assets          | pool_id, lp_token_id/amount, min_amounts[]                      | **NO — needs adding**          |
| `COLLECT_FEES`     | Claim accrued fees from LP position     | position_id                                                     | **NO — needs adding**          |
| `REBALANCE`        | Remove + re-add at new range (compound) | old_position_id, new_ticks                                      | EXISTS (but needs LP metadata) |

`VenueCapability.PROVIDE_LIQUIDITY` already exists in `venue_constants.py` and is tagged on Uniswap V2/V3/V4, Curve,
Aerodrome. But the instruction path lacks corresponding operation types.

> **TODO — CODIFY:** Also add `INSTRUCTION_VALID_DOMAINS` mapping: `ADD_LIQUIDITY` → `defi` domain, `LP_POSITION`
> instrument type. Update venue_constants.py accordingly.

## Smart Order Routing (SOR)

**SOR applies to POOL SELECTION, not venue selection:**

For the same token pair (ETH-USDT), multiple pools exist with different fee tiers:

- Uniswap V3: 0.01%, 0.05%, 0.3%, 1% fee tiers
- Curve: 0.04% for stableswaps
- Balancer: custom fees

Strategy decides which pool(s) to LP based on: fee tier, TVL, volume, IL risk. This is an "LP SOR" — selecting the best
pool to provide liquidity to.

> **TODO — CODIFY:** LP pool selection logic should be in strategy-service, not execution. Strategy evaluates pool
> metrics and selects target pool(s). Execution just executes the add/remove.

## PnL Attribution

| Component           | Settlement Type               | Mechanism                                          |
| ------------------- | ----------------------------- | -------------------------------------------------- |
| `fee_income_pnl`    | `LP_FEE_ACCRUAL` (per period) | Fees earned from swappers trading through position |
| `il_pnl`            | Mark-to-market                | Impermanent loss from price divergence             |
| `inventory_pnl`     | Mark-to-market                | Value change of underlying tokens in pool          |
| `transaction_costs` | Per-fill                      | Gas for add/remove/rebalance (~300k-500k gas each) |

**Source of truth:** `total_pnl = (current_position_value + collected_fees) - initial_deposit`

> **TODO — CODIFY:** `LP_FEE_ACCRUAL` settlement type doesn't exist. Add to `SettlementType` enum. IL calculation needs:
> `il_pnl = position_value_if_held - position_value_in_pool`.

## Risk & Exposure Subscriptions

### Risk Type Subscriptions

| Risk Type          | Subscribed? | Threshold                              | Action on Breach             |
| ------------------ | ----------- | -------------------------------------- | ---------------------------- |
| `impermanent_loss` | YES         | IL > X% of position                    | Widen range or exit          |
| `protocol_risk`    | YES         | Smart contract risk, pool manipulation | Emergency exit               |
| `liquidity`        | YES         | Pool TVL drops significantly           | Exit (crowding risk inverts) |
| `delta`            | YES (V3)    | Price exits range → 100% single-sided  | Rebalance to new range       |
| `concentration`    | YES         | Our share of pool TVL > X%             | Reduce position              |
| `venue_protocol`   | YES         | Pool pause, governance attack          | Emergency exit               |

### Custom Strategy Risk Types

| Custom Risk            | What It Measures                              | Evaluation Method  |
| ---------------------- | --------------------------------------------- | ------------------ |
| Range utilisation      | % of time price is within our LP range        | `rate_sensitivity` |
| Fee APY vs IL          | Net of fees minus IL — is LP profitable?      | `threshold_breach` |
| MEV extraction risk    | Are sandwich attacks eating our LP position?  | monitoring         |
| Pool TVL concentration | Our % of pool — adverse selection if too high | `threshold_breach` |

## Risk Profile

| Metric               | Target       | Notes                                                 |
| -------------------- | ------------ | ----------------------------------------------------- |
| Target annual return | 10-25%       | Fee APY minus IL, depends on pool                     |
| Target Sharpe ratio  | 1.5+         | Lower than delta-neutral strategies due to IL         |
| Max drawdown         | 15%          | Primarily from IL during large price moves            |
| Max leverage         | 1x           | No leverage                                           |
| Capital scalability  | $5M per pool | Larger = higher share of pool TVL = adverse selection |

## Latency Profile

| Segment                             | p50 Target | p99 Target | Co-location Needed? |
| ----------------------------------- | ---------- | ---------- | ------------------- |
| Feature → signal                    | 50ms       | 200ms      | No                  |
| Signal → instruction                | 10ms       | 50ms       | No                  |
| Instruction → on-chain (add/remove) | 5s         | 60s        | No (gas-dependent)  |
| **End-to-end**                      | **~6s**    | **~61s**   | **No**              |

Rebalancing is not time-critical — a few blocks delay is acceptable. However, during high volatility when rapid
rebalancing is needed, priority gas may help.

## Execution Details

- **Venues:** Uniswap V3 (primary), Curve (stableswaps), Balancer (weighted)
- **Order types:** Protocol interactions (not order book)
- **Atomic execution required?** No (single tx per add/remove), unless combining with hedge
- **Gas budget:** ~300k (add V3), ~200k (remove V3), ~150k (collect fees)

### Rebalancing

**Trigger type:** Event-driven on price exiting LP range.

| Level    | Condition                          | Action                                                 |
| -------- | ---------------------------------- | ------------------------------------------------------ |
| Normal   | Price within range, fees accruing  | No action                                              |
| Minor    | Price near range edge (within 5%)  | Log, prepare rebalance                                 |
| Major    | Price exits range (earning 0 fees) | Remove + re-add at new range centered on current price |
| Critical | IL exceeds threshold               | Full exit, return to flat                              |

## Margin & Liquidation

- **Margin model:** None — fully funded LP (no leverage)
- **Liquidation risk:** None (no debt)
- **IL risk:** Position value can decrease vs holding — not liquidation but real loss
- **Smart contract risk:** Pool exploit, governance attack, oracle manipulation

## Impermanent Loss -- Real V3/V4 Concentrated Math

NOT the V2 approximation (`2*sqrt(r)/(1+r) - 1`). V3 concentrated IL is amplified by range width. Narrower ranges earn
more fees but suffer more IL per unit of price movement.

### Formula for Range [tick_lower, tick_upper]

```
pa = 1.0001^tick_lower   # lower price bound
pb = 1.0001^tick_upper   # upper price bound

# Initial token amounts per unit liquidity at entry price p0:
amount0_entry = 1/sqrt(p0) - 1/sqrt(pb)
amount1_entry = sqrt(p0) - sqrt(pa)

# Current token amounts at price p1 (clamped to [pa, pb]):
if p1 <= pa:
    amount0_now = 1/sqrt(pa) - 1/sqrt(pb)
    amount1_now = 0
elif p1 >= pb:
    amount0_now = 0
    amount1_now = sqrt(pb) - sqrt(pa)
else:
    amount0_now = 1/sqrt(p1) - 1/sqrt(pb)
    amount1_now = sqrt(p1) - sqrt(pa)

# IL = (value_lp - value_hold) / value_hold
value_lp = amount0_now * p1 + amount1_now
value_hold = amount0_entry * p1 + amount1_entry
IL = (value_lp - value_hold) / value_hold
```

Key properties:

- IL is always <= 0 (LP always underperforms hold for non-zero price movement)
- At `p1 = p0` (no movement), IL = 0 exactly
- Outside range (`p1 < pa` or `p1 > pb`), IL grows linearly with price -- the LP is 100% in one token
- V3 concentrated IL can be 10-100x worse than V2 IL for the same price move, depending on range width

### Data Requirements -- No Assumptions

| Data                       | Source (Historical)          | Source (Live)                            | Purpose                                           |
| -------------------------- | ---------------------------- | ---------------------------------------- | ------------------------------------------------- |
| `sqrtPriceX96` / `tick`    | Uniswap subgraph pool entity | `eth_call slot0()`                       | Exact pool price for IL calculation               |
| `feeGrowthGlobal0X128`     | Subgraph pool entity         | `eth_call` on pool contract              | Cumulative fee per unit liquidity (token0)        |
| `feeGrowthGlobal1X128`     | Subgraph pool entity         | `eth_call` on pool contract              | Cumulative fee per unit liquidity (token1)        |
| `feeGrowthInside0LastX128` | Subgraph position entity     | `NonfungiblePositionManager.positions()` | EXACT fees earned by our position (not estimated) |
| `feeGrowthInside1LastX128` | Subgraph position entity     | `NonfungiblePositionManager.positions()` | EXACT fees earned by our position (token1)        |
| `tickLower` / `tickUpper`  | Subgraph position entity     | Position NFT                             | Our range boundaries                              |
| `liquidity`                | Subgraph position entity     | Position NFT                             | Our liquidity share in the pool                   |
| `volumeUSD`                | Subgraph `poolDayData`       | Subgraph                                 | Fee APY estimation (pre-entry forecasting only)   |

### Real Data vs Simulation

- **Fee income**: ALWAYS from `feeGrowthInside` (exact on-chain accounting). Volume-based estimation is used only for
  pre-entry APY forecasting to decide whether to enter a pool.
- **IL**: Always calculated from the concentrated formula above. Inputs (`sqrtPriceX96`, tick) come from on-chain data.
  Never use the V2 approximation for V3/V4 positions.
- **Range utilization**: Calculated from `current_tick` vs our `[tickLower, tickUpper]` over time. Tracks what
  percentage of candles our position was in range and earning fees.

### PnL Attribution (Detailed)

| Component               | Source                         | Calculation                                            |
| ----------------------- | ------------------------------ | ------------------------------------------------------ |
| `fee_pnl`               | `feeGrowthInside` deltas       | Exact from on-chain fee accounting                     |
| `il_pnl`                | Price movement within range    | Real V3 concentrated formula (see above)               |
| `rebalance_cost`        | Gas receipts + swap execution  | Gas used \* gas price + swap slippage on remove/re-add |
| `range_utilization_pct` | Tick history vs position range | `count(in_range_candles) / total_candles * 100`        |
| `net_lp_pnl`            | Aggregation                    | `fee_pnl + il_pnl - rebalance_cost`                    |

### IL Mitigation (Best Practices)

Proven techniques from professional LP managers (Gamma, Arrakis, Bunni):

1. **Volatility-adjusted range**: `width = base_width * (1 + realized_vol / target_vol)`. High vol = wider range (less
   IL, less fee concentration). Low vol = tighter range (more fees, acceptable IL).

2. **IL/fee monitoring**: If cumulative IL exceeds cumulative fees, the LP position is net-negative. Action: widen range
   (reduce IL rate) or exit entirely. Threshold is configurable via `max_il_to_fee_ratio` (default: 1.5 -- exit if IL >
   150% of fees).

3. **Asymmetric ranges**: Shift range directionally based on trend signals from features-volatility-service. Bullish
   trend = shift range upward (less downside IL exposure). This is the LP equivalent of skewing quotes.

4. **Rebalance cost threshold**: Only rebalance when `expected_IL_savings > rebalance_cost`. A $50 gas cost to rebalance
   is not justified by $10 of IL reduction. The strategy calculates the break-even horizon before emitting a rebalance
   instruction.

### V3 vs V4 Differences

| Dimension      | V3                                   | V4                                                   |
| -------------- | ------------------------------------ | ---------------------------------------------------- |
| IL math        | Same concentrated formula            | Same -- hooks don't change the bonding curve         |
| Fee tracking   | `feeGrowthInside` from position NFT  | Same via PoolManager singleton                       |
| Gas cost       | Higher (per-pool deployed contracts) | Lower (singleton PoolManager, flash accounting)      |
| Dynamic fees   | Fixed per pool (set at creation)     | Hook can adjust fee per swap dynamically             |
| Auto-rebalance | External keeper/bot needed           | Hook can auto-rebalance on tick crossing             |
| Customisation  | None -- protocol is fixed            | Hooks enable custom logic (TWAP, limit orders, etc.) |

V4 hooks do NOT change the fundamental IL math -- the x\*y=k (concentrated) curve is identical. Hooks only affect fee
collection, access control, and auxiliary logic around swaps. The concentrated formula above applies to both V3 and V4.

## Testing Stage Status

| Stage        | Status  | Notes                                                |
| ------------ | ------- | ---------------------------------------------------- |
| MOCK         | Pending | Need MockAMMPool with price simulation + fee accrual |
| HISTORICAL   | Pending | Uniswap V3 pool data available via The Graph         |
| LIVE_MOCK    | Pending | Blocked by ADD_LIQUIDITY operation type gap          |
| LIVE_TESTNET | Pending | Uniswap V3 on Sepolia, Curve on Sepolia              |
| BATCH_REAL   | Pending | Historical pool data backfill needed                 |
| STAGING      | Pending | Tenderly fork                                        |
| LIVE_REAL    | Pending | All above + IL risk accepted                         |

## Wallet & Capital Flow

| Component        | Value                                 |
| ---------------- | ------------------------------------- |
| Treasury reserve | 20% of AUM                            |
| Hot wallet       | Per-chain, per-strategy isolated      |
| CeFi sub-account | No                                    |
| Bridge required  | No (single-chain -- Ethereum mainnet) |
| Custody          | Copper MPC                            |

Capital flow: Client deposit --> treasury --> hot wallet --> ADD_LIQUIDITY to AMM pool (token pair from wallet).
Rebalance: REMOVE_LIQUIDITY + re-ADD_LIQUIDITY at new range (all on same chain). Exit: REMOVE_LIQUIDITY + COLLECT_FEES
--> TRANSFER --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM). The MTDS `gas_fee_handler` fetches
real-time gas prices and writes them as features. Gas hits P&L immediately as a realized transaction cost -- not
estimated. LP operations are gas-intensive: ~300k gas for add (~$27 at 30 gwei on L1), ~200k for remove (~$18), ~150k
for fee collection (~$14). Frequent rebalancing on L1 can erode fee income -- the strategy checks that
`expected_IL_savings > rebalance_gas_cost` before emitting any rebalance instruction. L2 deployments (Arbitrum, Base)
reduce gas by ~100x.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). DEX
pools require **BOTH sides** to be in `DEFI_MAJOR_ASSET_SYMBOLS` (~65 tokens). TVL minimums: $100k for EVM (Uniswap V3
subgraph `minTvl` param), $10k for Solana DEXes (client-side filter). Multi-token pools (Balancer) require **ALL**
tokens to be major assets.

## E2E Manual Trading Workflow

Step-by-step manual recreation of the Uniswap V3 concentrated liquidity LP strategy. LP earns fees when price is in
range; must rebalance when price drifts out of range. More operationally complex than other DeFi strategies due to
active range management.

### Prerequisites

- Treasury wallet funded with ETH + USDC on Ethereum (or single token to be split)
- Trading wallet created (per-strategy, per-chain)
- Alchemy RPC configured for Ethereum
- Target pool identified (e.g., ETH-USDC 0.3% fee tier on Uniswap V3)

### Step-by-Step (Initial Deployment)

| Step | Action                                                            | Instruction Type | Service                                      | Instant P&L                                |
| ---- | ----------------------------------------------------------------- | ---------------- | -------------------------------------------- | ------------------------------------------ |
| 1    | Observe treasury balance                                          | --               | position-balance-monitor (treasury_monitor)  | --                                         |
| 2    | Transfer $100K (ETH + USDC) from treasury to trading wallet       | TRANSFER         | execution-service (custody provider)         | Gas: ~$2                                   |
| 3    | Calculate 50/50 split at current ETH price ($3,200)               | --               | strategy-service (range calculation)         | --                                         |
| 4    | Swap to rebalance 50/50 if needed (e.g., swap excess USDC to ETH) | SWAP             | execution-service (UniswapConnector)         | Gas: ~$15. Slippage: ~$2.50 (5bps on $50K) |
| 5    | Set tick range: tickLower/tickUpper around current price          | --               | strategy-service (volatility-adjusted width) | --                                         |
| 6    | Add liquidity to Uniswap V3 pool (ETH + USDC within tick range)   | ADD_LIQUIDITY    | execution-service (UniswapV3Connector)       | Gas: ~$25. Receive: LP NFT position        |
| 7    | Verify LP position NFT in trading wallet                          | --               | position-balance-monitor                     | NFT token ID, liquidity amount, tick range |

### Position State After Deployment

- Trading wallet: Uniswap V3 LP NFT (ETH-USDC, tickLower/tickUpper)
- ~$50K ETH + ~$50K USDC deposited in pool within the specified tick range
- Earning swap fees when price is within range
- No debt, no perp, no leverage

### Instant P&L Decomposition

| Component                         | Amount      | Notes                                                       |
| --------------------------------- | ----------- | ----------------------------------------------------------- |
| Gas (steps 2, 4, 6)               | -$42.00     | 3 on-chain txns (transfer + rebalance swap + add liquidity) |
| Swap slippage for 50/50 rebalance | -$2.50      | ~5bps on $50K swap to rebalance                             |
| **Total entry cost**              | **-$44.50** |                                                             |
| Gross instant P&L                 | $0          | actual_output - expected_output (perfect execution)         |
| Net instant P&L                   | -$44.50     | gross - all costs                                           |

Strategy instruction carries `benchmark_price` (pool spot price at signal time) and `max_slippage_bps` (10bps for
rebalance swap). Execution-service rejects if slippage exceeds threshold.

### Ongoing P&L (Daily -- In Range)

- Fee income: from `feeGrowthInside` (EXACT on-chain accounting, not estimated)
- Impermanent loss: V3 concentrated formula (see IL section above), tracked per candle
- At ~15% fee APY on $100K, in-range 80% of the time: ~$32.88/day gross
- IL offset: depends on price volatility and range width
- **Net daily income (typical): ~$20-30/day (fee_pnl + il_pnl)**
- Cost recovery: ~1.5-2.2 days

### Risk Metrics

- Impermanent loss: amplified by concentration (10-100x worse than V2 for tight ranges)
- Out-of-range: earning zero fees, 100% single-sided exposure
- Range utilization: target >80% of candles in range
- Rebalancing gas: ~$43 per rebalance (remove + swap + add)
- Pool TVL concentration: if our share > 5% of pool, adverse selection risk increases

### Rebalance Workflow (When Price Drifts to 80% of Range Edge)

| Step | Action                                                    | Instruction Type | Instant P&L                    |
| ---- | --------------------------------------------------------- | ---------------- | ------------------------------ |
| 1    | Check: IL savings from rebalance > rebalance gas cost?    | --               | If NO, skip rebalance          |
| 2    | Remove liquidity from current position (burn NFT)         | REMOVE_LIQUIDITY | Gas: ~$18                      |
| 3    | Collect accrued fees                                      | COLLECT_FEES     | Gas: ~$0 (bundled with remove) |
| 4    | Swap to rebalance 50/50 at new price                      | SWAP             | Gas: ~$15. Slippage: ~5bps     |
| 5    | Add liquidity at new tick range centered on current price | ADD_LIQUIDITY    | Gas: ~$25. Receive: new LP NFT |
|      | **Total rebalance cost**                                  |                  | **~$60-65**                    |

**Rebalance cost check:** only rebalance if `expected_IL_savings > rebalance_gas_cost`. A $60 gas cost is not justified
by $10 of IL reduction. Strategy calculates break-even horizon before emitting instruction.

### Exit Workflow

| Step | Action                                          | Instruction Type | Instant P&L                |
| ---- | ----------------------------------------------- | ---------------- | -------------------------- |
| 1    | Remove liquidity (burn NFT, receive ETH + USDC) | REMOVE_LIQUIDITY | Gas: ~$18                  |
| 2    | Collect all accrued fees                        | COLLECT_FEES     | Gas: ~$0 (bundled)         |
| 3    | Swap all to single token (e.g., ETH to USDC)    | SWAP             | Gas: ~$15. Slippage: ~5bps |
| 4    | Transfer USDC from trading wallet to treasury   | TRANSFER         | Gas: ~$2                   |
|      | **Total exit cost**                             |                  | **~$37.50**                |

### Service Interaction Diagram

```
User (UI)
  |
  +---> position-balance-monitor: read treasury balance
  +---> execution-service: TRANSFER ETH+USDC (custody signs tx)
  +---> execution-service: SWAP to rebalance 50/50 (SOR)
  +---> strategy-service: calculate tick range from realized_vol
  +---> execution-service: ADD_LIQUIDITY (UniswapV3 NonfungiblePositionManager)
  +---> position-balance-monitor: read LP NFT position
  +---> features-onchain-service: publish pool_price, current_tick, feeGrowthInside
  +---> pnl-attribution-service: compute fee_pnl, il_pnl, range_utilization_pct
  +---> risk-and-exposure-service: monitor IL threshold, out-of-range status
  |
  [On rebalance trigger: price at 80% of range edge]
  +---> execution-service: REMOVE_LIQUIDITY + COLLECT_FEES
  +---> execution-service: SWAP to rebalance 50/50
  +---> execution-service: ADD_LIQUIDITY at new range
```

### Trade History (Expected Output)

| #   | Time  | Type          | Instrument  | Amount   | Price              | Gas    | Slippage | Fee/IL      | Running P&L   |
| --- | ----- | ------------- | ----------- | -------- | ------------------ | ------ | -------- | ----------- | ------------- |
| 1   | 10:01 | TRANSFER      | ETH+USDC    | $100,000 | --                 | $2.00  | $0       | --          | -$2.00        |
| 2   | 10:02 | SWAP          | USDC->ETH   | $50,000  | $3,200             | $15.00 | $2.50    | --          | -$19.50       |
| 3   | 10:03 | ADD_LIQUIDITY | ETH-USDC LP | $100,000 | tick 196200-196800 | $25.00 | $0       | --          | -$44.50       |
| 4   | EOD   | FEE_ACCRUAL   | LP position | +$32.88  | feeGrowthInside    | $0     | $0       | +$32.88 fee | -$11.62       |
| 5   | EOD   | IL_MARK       | LP position | -$8.20   | ETH $3,220 (+0.6%) | $0     | $0       | -$8.20 IL   | -$19.82       |
| 6   | Day 2 | FEE_ACCRUAL   | LP position | +$32.88  | feeGrowthInside    | $0     | $0       | +$32.88 fee | -$11.94 (cum) |
| 7   | Day 2 | IL_MARK       | LP position | -$5.10   | ETH $3,240         | $0     | $0       | -$5.10 IL   | +$15.84       |
| 8   | Day 5 | REBALANCE     | LP position | --       | ETH $3,350         | $58.00 | $2.50    | --          | +$42.20       |
| 9   | Day 7 | FEE_ACCRUAL   | LP position | +$32.88  | feeGrowthInside    | $0     | $0       | +$32.88 fee | +$108.50      |

### P&L Attribution Summary (Running Totals)

| Component                        | Day 1       | Day 7       | Day 30       |
| -------------------------------- | ----------- | ----------- | ------------ |
| fee_pnl (from feeGrowthInside)   | +$32.88     | +$213.72    | +$986.40     |
| il_pnl (V3 concentrated formula) | -$8.20      | -$45.00     | -$180.00     |
| rebalance_cost                   | $0          | -$60.50     | -$181.50     |
| entry_cost                       | -$44.50     | -$44.50     | -$44.50      |
| range_utilization_pct            | 100%        | 82%         | 78%          |
| **net_lp_pnl**                   | **-$19.82** | **+$63.72** | **+$580.40** |

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_amm_lp.py`
- **Matching engine (simulation):** `matching-engine-library/hooks.py` (V4 hooks)
- **Pool data adapters:**
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/uniswap_v3_adapter.py`
- **Venue capabilities:** `VENUE_CAPABILITIES.PROVIDE_LIQUIDITY` in `venue_constants.py`
- **Hard rules:** [config-architecture.md](../cross-cutting/config-architecture.md)
