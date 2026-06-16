---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# DeFi Staked Basis

> **Asset class:** DeFi **Strategy type:** Basis + LST Yield (delta-neutral with staking enhancement) **Strategy ID
> pattern:** `DEFI_ETH_STAKED_BASIS_SCE_1H`

## Overview

Enhanced basis trade: swap USDT into weETH (EtherFi liquid staking token) instead of raw ETH, then short ETH perp on
Hyperliquid. Collects staking yield (~3.5% from weETH appreciation) on top of funding rate. Delta-neutral with higher
combined APY than plain basis.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDT  (100% USDT)

Step 1 - SWAP:     USDT --> weETH        (90% of capital, via SOR: Uniswap/Curve/Balancer)
                   Amount: wallet_usdt * 0.9 / eth_price / weeth_rate
Step 2 - TRANSFER: USDT --> USDC         (10% to Hyperliquid as margin)
Step 3 - TRADE:    Short ETH-USDC perp   (size = weeth_amount * weeth_rate = full ETH exposure)

Wallet after deploy:
  - ETHERFI:LST:WEETH@ETHEREUM           = weeth_amount  (long, appreciating)
  - HYPERLIQUID:PERPETUAL:ETH-USDC       = -eth_exposure (short)
  - HYPERLIQUID margin                   = 10% USDC

Net delta = 0 (long weETH exposure + short perp cancel)
```

## Instruments

| Instrument Key                                   | Venue       | Type | Role                    |
| ------------------------------------------------ | ----------- | ---- | ----------------------- |
| `WALLET:SPOT_ASSET:USDT`                         | Wallet      | Spot | Initial capital         |
| `ETHERFI:LST:WEETH@ETHEREUM`                     | EtherFi     | LST  | Long leg (appreciating) |
| `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` | Hyperliquid | Perp | Short leg (hedge)       |

## Key Features Consumed

| Feature           | Source Service     | SLA | Used For                               |
| ----------------- | ------------------ | --- | -------------------------------------- |
| `lst_staking_apy` | features-onchain   | 60s | Signal: entry if staking APY >= 3%     |
| `funding_rate`    | features-delta-one | 10s | Signal: entry if combined APY >= 5%    |
| `weeth_eth_rate`  | features-onchain   | 60s | Position sizing, rebalancing trigger   |
| `weekly_rewards`  | features-onchain   | 24h | EtherFi loyalty points / EIGEN rewards |
| `eth_price`       | market-tick-data   | 1s  | PnL, sizing                            |

## Data Architecture

| Dimension              | Value                                                                                  | SSOT                                                      |
| ---------------------- | -------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                              | `strategy-service/config.py`                              |
| **Processed data**     | `market_data` dict: `eth_price`, `funding_rate`, `weeth_eth_rate`, `weekly_rewards`    | Features hydrated alongside candles                       |
| **Features**           | `features` dict: `lst_staking_apy`, `funding_rate`, `weeth_eth_rate`, `weekly_rewards` | `features-onchain-service` + `features-delta-one-service` |
| **Interval**           | Time-driven (candle-based), not event-driven                                           | `timeframe` in strategy config                            |
| **Lowest granularity** | 1H (currently hardcoded in factory, not configurable)                                  | `defi_staked_basis.py` factory                            |
| **Execution mode**     | `same_candle_exit` — entry and exit can occur in same candle                           | Strategy config                                           |

**Gap:** Timeframe is hardcoded to 1H. Should be configurable via strategy config.

## Instrument Selection

**Currently: STATIC (hardcoded per config, no dynamic selection)**

Instruments are set at strategy initialisation and never change:

- LST: `ETHERFI:LST:WEETH@ETHEREUM` — always weETH (not wstETH, not rETH)
- Perp: `{perp_venue}:PERPETUAL:ETH-USDC@LIN@{perp_venue}` — venue configurable, instrument fixed

There is **no dynamic LST selection** — the strategy does NOT compare weETH vs wstETH vs rETH staking yields and pick
the best one. This is a gap: an "LST SOR" could select the highest-yielding LST that meets liquidity and depeg risk
thresholds.

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON by default for the swap leg only.**

| Leg                      | SOR? | Allowed Venues                                          | SSOT                 |
| ------------------------ | ---- | ------------------------------------------------------- | -------------------- |
| Step 1 (USDT→weETH swap) | YES  | `UNISWAP_V3-ETHEREUM`, `CURVE-ETHEREUM`, `BALANCER-ETH` | `defi_base.py:84-86` |
| Step 3 (Short perp)      | NO   | Hyperliquid only (CLOB, no alternative)                 | —                    |

SOR picks the best price across DEX venues for the USDT→weETH swap. May route multi-hop (USDT→WETH→weETH) for better
pricing. The `allowed_venues` list is passed in `StrategyInstruction` to execution-service, which handles the actual
routing.

**Same-wallet constraint:** All SOR venues must be on Ethereum mainnet (same ERC-20 wallet). SSOT:
[`SHARED_WALLET_GROUPS`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

**Execution boundary:** Strategy sends `StrategyInstruction` with `allowed_venues`, `max_slippage_bps`, and
`benchmark_price`. Execution-service converts to `ExecutionInstruction`, picks venue, chooses order type, executes, and
measures alpha vs benchmark.

## weETH Mechanics

weETH is **non-rebasing**: your token count stays fixed after purchase. The weETH/ETH exchange rate increases over time
as staking rewards accrue (~0.01% per day).

- **Rate tracking:** `weeth_eth_rate` starts at ~1.035 and grows monotonically
- **Yield source:** ETH staking rewards (consensus + execution layer) paid to EtherFi validators
- **Wrap/unwrap:** eETH (rebasing) is wrapped to weETH for DeFi compatibility
- **Rate appreciation != balance change** -- yield shows up in the price, not the token count

This means delta drift: as weETH appreciates vs ETH, the ETH-equivalent exposure grows, creating a mismatch against the
fixed-size perp short. Strategy rebalances by adjusting perp size:
`target_perp_size = -(weeth_balance * current_weeth_rate)`.

## PnL Attribution

| Component           | Settlement Type                       | Mechanism                                                            |
| ------------------- | ------------------------------------- | -------------------------------------------------------------------- |
| `staking_yield_pnl` | `LST_YIELD` (per candle)              | `position_size * (weeth_rate_new - weeth_rate_old) / weeth_rate_old` |
| `funding_pnl`       | `FUNDING_8H` (00/08/16 UTC)           | Short perp receives positive funding                                 |
| `rewards_pnl`       | `SEASONAL_WEEKLY` (Mondays 00:00 UTC) | EtherFi loyalty points, EIGEN airdrop rewards                        |
| `trading_pnl`       | Entry/exit fills                      | Price difference on swaps                                            |
| `transaction_costs` | Per-fill                              | Swap fee + gas + Hyperliquid taker fee                               |

**Source of truth:** `total_pnl = weeth_amount * weeth_rate * eth_price - perp_loss + margin - initial`

**Combined APY calculation (signal generation only, NOT used for PnL):**

```
combined_apy = staking_apy + (funding_rate * 3 * 365) + (weekly_rewards * 52)
Entry: combined_apy >= 5% AND staking_apy >= 3%
Exit:  combined_apy drops 70% OR weETH depegs > 2%
```

**Double-counting prevention:** LST_YIELD settlement does NOT adjust position size -- it only records yield for
attribution. The actual value change comes through weETH rate (price) updates. Balance-based equity is the
reconciliation anchor.

## Risk Profile

| Metric               | Target | Notes                                                 |
| -------------------- | ------ | ----------------------------------------------------- |
| Target annual return | 12-20% | Staking ~3.5% + funding ~8% + rewards ~2%             |
| Target Sharpe ratio  | 2.5+   | Higher than plain basis due to staking floor          |
| Max drawdown         | 5%     | weETH depeg is primary risk                           |
| Max leverage         | 1x     | No leverage (spot LST + perp hedge)                   |
| Capital scalability  | $10M   | weETH liquidity deeper than raw ETH for this use case |

## Latency Profile

| Segment                    | p50 Target | p99 Target | Co-location Needed?                    |
| -------------------------- | ---------- | ---------- | -------------------------------------- |
| Market data -> feature     | 50ms       | 200ms      | No                                     |
| Feature -> signal          | 10ms       | 50ms       | No                                     |
| Signal -> instruction      | 5ms        | 20ms       | No                                     |
| Instruction -> fill (swap) | 3s         | 20s        | No (on-chain, SOR may route multi-hop) |
| Instruction -> fill (perp) | 100ms      | 500ms      | No (Hyperliquid CLOB)                  |
| **End-to-end**             | **~4s**    | **~21s**   | **No**                                 |

Low-frequency (1h candles). Rebalancing is time-insensitive.

## Execution Details

- **Venues:** Uniswap V3 / Curve / Balancer (swap via SOR), Hyperliquid (perp)
- **Order types:** Market (swap via SOR with slippage protection), Limit (perp)
- **Atomic execution required?** No -- swap and perp are independent legs
- **Gas budget:** ~250k gas for weETH swap (may require multi-hop through WETH)

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). No rebalance without new market data.

| Level    | Position Deviation | Action         | Notes                                          |
| -------- | ------------------ | -------------- | ---------------------------------------------- |
| Minor    | >2% delta drift    | LOG_ONLY       | Log deviation, no action                       |
| Major    | >5% delta drift    | REBALANCE      | Adjust perp size via `_rebalance_perp_hedge()` |
| Critical | >10% delta drift   | EMERGENCY_EXIT | Full exit both legs                            |

**Delta drift source:** weETH appreciation causes ETH-equivalent exposure to grow while perp size stays fixed. Target
perp size = `-(weeth_balance * current_weeth_rate)`.

**Rebalance action:** Minor rebalance adjusts perp size only (cheap, Hyperliquid order). Major rebalance may partial
unwind + re-enter if weETH depegs.

Thresholds from `defi_base.py:_parse_thresholds()`. SSOT:
[`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions → exposures) → RiskMonitor (exposures → risk assessment) → Strategy (risk
assessment → rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern           | Exposure Type                  | Used For                                  |
| ---------------------------- | ------------------------------ | ----------------------------------------- |
| `ETHERFI:LST:WEETH@ETHEREUM` | LST value (long, appreciating) | Delta calculation, staking yield tracking |
| `HYPERLIQUID:PERPETUAL:*`    | Perp notional (short)          | Delta calculation                         |
| `WALLET:LST:*`               | Staking position               | weETH rate monitoring                     |

Config: `defi_mode.enabled=True`, `defi_mode.track_staking_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type          | Subscribed?       | Threshold                                    | Action on Breach                          |
| ------------------ | ----------------- | -------------------------------------------- | ----------------------------------------- |
| `delta`            | YES               | 2% net delta drift (from weETH appreciation) | Adjust perp size                          |
| `funding`          | YES (signal only) | `min_combined_apy` config param              | Entry/exit decision                       |
| `staking_yield`    | YES               | `min_staking_apy` config param (default 3%)  | Exit if yield collapses                   |
| `protocol_risk`    | YES               | weETH depeg > 2%                             | Emergency exit                            |
| `venue_protocol`   | YES               | Hyperliquid circuit breaker state            | Pause trading                             |
| `liquidity`        | NO                | —                                            | —                                         |
| `borrow_cost`      | NO                | —                                            | No borrowing                              |
| `aave_liquidation` | NO                | —                                            | No Aave collateral (weETH held in wallet) |

Config: `enabled_risk_types: ["cex_margin"]`, `defi_risk.enabled=True`, `defi_risk.aave_liquidation=False` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults. Plan item `p5-risk-strategy-subscription` will create
`StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk            | What It Measures                               | Evaluation Method  |
| ---------------------- | ---------------------------------------------- | ------------------ |
| weETH depeg risk       | weETH/ETH rate drops below 1.0 (loss of peg)   | `threshold_breach` |
| Combined APY collapse  | Staking + funding falls below min_combined_apy | `rate_sensitivity` |
| EtherFi slashing event | Validator penalties reduce staking yield       | `threshold_breach` |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** Hyperliquid cross-margin on perp side only
- **Health factor threshold:** N/A (no Aave positions -- weETH is held in wallet, not as collateral)
- **Liquidation risk:** Hyperliquid margin depletion if extreme basis widening + weETH depeg
- **weETH depeg risk:** If weETH/ETH rate drops > 2%, strategy exits immediately
- **Monitoring:** weETH rate + margin usage checked per candle

## Authentication & Credentials

| Venue                 | Secret Name                   | Testnet Available?                             | Notes                   |
| --------------------- | ----------------------------- | ---------------------------------------------- | ----------------------- |
| EtherFi (via Uniswap) | `alchemy-api-key` (RPC)       | Yes (Holesky for EtherFi, Sepolia for Uniswap) | weETH swap on DEX       |
| Hyperliquid           | `hyperliquid-api-credentials` | Yes (`api.hyperliquid-testnet.xyz`)            | API key + secret        |
| Wallet                | `wallet-{client}-private-key` | Yes (dev wallet)                               | Signs swap transactions |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Hyperliquid account per client (separate margin)
2. Wallet per client (separate weETH holdings)
3. Config: `initial_capital`, `min_staking_apy` (default 3%), `min_combined_apy` (default 5%)
4. **Restart required?** No -- hot-reload via GCS config

## UI Visualisation

### Standard views

- PnL waterfall, margin health, position breakdown (from monitoring UI plans)

### Strategy-specific views

- **Combined APY decomposition** -- stacked bar: staking + funding + rewards = combined
- **weETH/ETH rate chart** -- with appreciation trend line and depeg alert threshold (2%)
- **Funding rate overlay** -- funding rate vs combined APY threshold line
- **Delta drift indicator** -- shows current delta mismatch and next rebalance trigger
- **Weekly rewards tracker** -- cumulative EtherFi/EIGEN rewards with expected vs actual

## Testing Stage Status

| Stage        | Status  | Notes                                                                    |
| ------------ | ------- | ------------------------------------------------------------------------ |
| MOCK         | Pending | Need MockDeFiDynamics with weETH rate appreciation + funding oscillation |
| HISTORICAL   | Pending | Need weETH rate history (EtherFi launched ~2023, ~2yr available)         |
| LIVE_MOCK    | Pending | Blocked by features-onchain lst_staking_apy calculator (#6)              |
| LIVE_TESTNET | Pending | Blocked by EtherFi Holesky integration + Hyperliquid testnet             |
| BATCH_REAL   | Pending | Blocked by historical APY storage (#4)                                   |
| STAGING      | Pending | Tenderly fork + Hyperliquid testnet                                      |
| LIVE_REAL    | Pending | All above + real capital approval                                        |

## Wallet & Capital Flow

| Component        | Value                                 |
| ---------------- | ------------------------------------- |
| Treasury reserve | 20% of AUM                            |
| Hot wallet       | Per-chain, per-strategy isolated      |
| CeFi sub-account | Yes (Hyperliquid -- perp margin)      |
| Bridge required  | No (single-chain -- Ethereum mainnet) |
| Custody          | Copper MPC                            |

Capital flow: Client deposit --> treasury --> hot wallet --> SWAP to weETH (spot LST leg) + TRANSFER USDC to Hyperliquid
(margin). Rebalance: treasury < 10% --> strategy reduces position --> close perp + SWAP weETH back --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked via Alchemy RPC using `eth_feeHistory` (Ethereum mainnet). The MTDS `gas_fee_handler` fetches
real-time gas prices and writes them as features. Gas hits P&L immediately as a realized transaction cost -- not
estimated. The weETH swap may route multi-hop (USDT->WETH->weETH) which increases gas to ~250k. The Hyperliquid perp leg
has zero gas cost.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). DEX
pools (swap leg) require BOTH sides to be in `DEFI_MAJOR_ASSET_SYMBOLS`. weETH is in the ETH LST category of the
whitelist. Perps use the CeFi base asset universe.

## E2E Manual Trading Workflow

Step-by-step manual recreation of the staked basis strategy. Each step maps to a StrategyInstruction type and a backend
service interaction. This is delta-neutral: weETH LONG (spot LST) + ETH SHORT (perp) = net zero delta + staking yield +
funding income.

### Prerequisites

- Treasury wallet funded with USDC on Ethereum
- Trading wallet created (per-strategy, per-chain)
- Hyperliquid sub-account with API credentials
- Alchemy RPC configured for Ethereum

### Step-by-Step

| Step | Action                                              | Instruction Type | Service                                      | Instant P&L                                  |
| ---- | --------------------------------------------------- | ---------------- | -------------------------------------------- | -------------------------------------------- |
| 1    | Observe treasury balance                            | --               | position-balance-monitor (treasury_monitor)  | --                                           |
| 2    | Transfer $100K USDC from treasury to trading wallet | TRANSFER         | execution-service (custody provider)         | Gas: ~$2                                     |
| 3    | Swap $90K USDC to ETH via SOR                       | SWAP             | execution-service (UniswapConnector via SOR) | Gas: ~$15. Slippage: ~$4.50 (5bps on $90K)   |
| 4    | Swap ETH to weETH (EtherFi staking)                 | SWAP             | execution-service (UniswapConnector)         | Gas: ~$15. Slippage: ~$22.50 (25bps on $90K) |
| 5    | Transfer $10K USDC to Hyperliquid as margin         | TRANSFER         | execution-service (Hyperliquid deposit)      | Gas: ~$2                                     |
| 6    | Short ETH perp (size = weETH_amount \* weETH_rate)  | TRADE            | execution-service (HyperliquidConnector)     | Fee: ~$5.40 (6bps on $90K notional)          |

### Position State After Deployment

- Trading wallet: weETH (worth ~$90K ETH-equivalent, appreciating via staking yield)
- Hyperliquid: SHORT ETH-USDC perp (~$90K notional), $10K margin
- Net delta: 0 (long weETH exposure + short perp cancel)
- No Aave debt, no leverage

### Instant P&L Decomposition

| Component                  | Amount      | Notes                                               |
| -------------------------- | ----------- | --------------------------------------------------- |
| Gas (steps 2-5)            | -$34.00     | 4 on-chain txns (transfer + 2 swaps + transfer)     |
| Swap slippage USDC to ETH  | -$4.50      | ~5bps on $90K, benchmarked vs oracle price          |
| Swap slippage ETH to weETH | -$22.50     | ~25bps on $90K, weETH liquidity thinner than ETH    |
| Perp trading fee           | -$5.40      | Hyperliquid taker 6bps on $90K notional             |
| **Total entry cost**       | **-$66.40** |                                                     |
| Gross instant P&L          | $0          | actual_output - expected_output (perfect execution) |
| Net instant P&L            | -$66.40     | gross - all costs                                   |

Strategy instruction carries `benchmark_price` (oracle ETH price at signal time) and `max_slippage_bps` (30bps for weETH
leg). Execution-service rejects if slippage exceeds threshold.

### Ongoing P&L (Daily)

- Staking yield: weETH rate appreciation ~3.5% APY on $90K = ~$8.63/day
- Funding income: positive funding on short perp ~5% APY on $90K = ~$12.33/day
- No borrow cost (weETH held in wallet, not collateral)
- **Combined daily income: ~$20.96/day (~8.5% APY)**
- Cost recovery: ~3.2 days

### Risk Metrics

- Net delta target: 0 (rebalance if drift > 5%)
- weETH/ETH depeg threshold: 2% (emergency exit)
- Funding rate reversal: exit if combined APY drops below 5%
- Hyperliquid margin: cross-margin, monitor for depletion during extreme basis widening
- Health Factor: N/A (no Aave positions)

### Exit Workflow

| Step | Action                                            | Instruction Type | Instant P&L                          |
| ---- | ------------------------------------------------- | ---------------- | ------------------------------------ |
| 1    | Close short ETH perp on Hyperliquid               | TRADE            | Fee: ~$5.40                          |
| 2    | Swap weETH to ETH                                 | SWAP             | Gas: ~$15. Slippage: ~$22.50 (25bps) |
| 3    | Swap ETH to USDC                                  | SWAP             | Gas: ~$15. Slippage: ~$4.50 (5bps)   |
| 4    | Withdraw USDC from Hyperliquid to trading wallet  | TRANSFER         | Gas: ~$2                             |
| 5    | Transfer all USDC from trading wallet to treasury | TRANSFER         | Gas: ~$2                             |
|      | **Total exit cost**                               |                  | **~$66.40**                          |

### Service Interaction Diagram

```
User (UI)
  |
  +---> position-balance-monitor: read treasury balance
  +---> execution-service: TRANSFER USDC (custody signs tx)
  +---> execution-service: SWAP USDC->ETH (SOR picks best DEX)
  +---> execution-service: SWAP ETH->weETH (EtherFi via Uniswap)
  +---> execution-service: TRANSFER USDC to Hyperliquid
  +---> execution-service: TRADE short ETH perp (Hyperliquid CLOB)
  +---> position-balance-monitor: read weETH balance + perp position
  +---> pnl-attribution-service: compute staking_yield_pnl + funding_pnl
  +---> risk-and-exposure-service: compute delta drift
```

### Trade History (Expected Output)

| #   | Time  | Type            | Instrument    | Amount          | Price  | Gas    | Slippage | Fee   | Running P&L |
| --- | ----- | --------------- | ------------- | --------------- | ------ | ------ | -------- | ----- | ----------- |
| 1   | 10:01 | TRANSFER        | USDC          | 100,000         | $1.00  | $2.00  | $0       | $0    | -$2.00      |
| 2   | 10:02 | SWAP            | USDC->ETH     | 90,000          | $3,200 | $15.00 | $4.50    | $0    | -$21.50     |
| 3   | 10:03 | SWAP            | ETH->weETH    | 28.125 ETH      | $3,200 | $15.00 | $22.50   | $0    | -$59.00     |
| 4   | 10:04 | TRANSFER        | USDC          | 10,000          | $1.00  | $2.00  | $0       | $0    | -$61.00     |
| 5   | 10:05 | TRADE           | ETH-USDC perp | -28.125 (short) | $3,200 | $0     | $0       | $5.40 | -$66.40     |
| 6   | EOD   | STAKING_YIELD   | weETH         | +0.0027         | $3,200 | $0     | $0       | $0    | -$57.77     |
| 7   | EOD   | FUNDING         | ETH perp      | +$12.33         | --     | $0     | $0       | $0    | -$45.44     |
| 8   | Day 2 | STAKING+FUNDING | --            | --              | --     | $0     | $0       | $0    | -$24.48     |
| 9   | Day 4 | STAKING+FUNDING | --            | --              | --     | $0     | $0       | $0    | +$17.44     |

## Configurable Staking Protocol

The staking protocol is configurable via `staking_protocol` in strategy config. Each protocol has different yield
characteristics, reward tokens, and Aave compatibility.

| Protocol | LST Token | Aave Collateral? | Reward Tokens     | APY Key               | Notes                          |
| -------- | --------- | ---------------- | ----------------- | --------------------- | ------------------------------ |
| EtherFi  | weETH     | Yes (LTV 72.5%)  | EIGEN + ETHFI     | `etherfi_staking_apy` | Default. Highest combined APY. |
| Lido     | wstETH    | Yes (LTV 79.5%)  | None (yield-only) | `lido_staking_apy`    | Simpler. No reward tokens.     |

When `staking_protocol="LIDO"`, the strategy swaps into wstETH instead of weETH, and the reward lifecycle (EIGEN/ETHFI
claiming and selling) is disabled entirely. The features consumed change accordingly -- `weeth_eth_rate` becomes
`wsteth_eth_rate`, and `weekly_rewards` is not consumed.

Protocol selection is a fixed config parameter, not gridded. A client chooses EtherFi or Lido at onboarding based on
risk/reward preference.

## Reward Lifecycle

For EtherFi staking, the strategy manages two reward token streams:

| Reward Token | Distribution Frequency | Claim Contract | Min Claim Threshold | Min Sell Threshold |
| ------------ | ---------------------- | -------------- | ------------------- | ------------------ |
| EIGEN        | Weekly (Mondays)       | EigenLayer     | $50                 | $100               |
| ETHFI        | Quarterly              | EtherFi        | $50                 | $100               |

**Lifecycle stages:**

1. **Accrue** -- rewards accumulate in the protocol. Tracked as `PNL_FACTOR_REWARD_UNREALISED`.
2. **Claim** -- on-chain transaction to the claim contract. Operation type: `CLAIM_REWARD`. Auto-triggered when accrued
   value exceeds $50. Max once per 24h.
3. **Sell** -- swap reward tokens to WETH via Binance spot or Uniswap V3. Operation type: `SELL_REWARD`. Auto-triggered
   when wallet balance exceeds $100.
4. **Attribute** -- realized proceeds split into `PNL_FACTOR_RESTAKING_REWARD` (EIGEN) and `PNL_FACTOR_SEASONAL_REWARD`
   (ETHFI) for P&L attribution.

For Lido (`staking_protocol="LIDO"`), there are no separate reward tokens -- yield accrues entirely through wstETH/ETH
rate appreciation. The reward lifecycle is inactive.

See [cross-cutting/reward-lifecycle.md](../../architecture-v2/cross-cutting/reward-lifecycle.md) for the full
cross-strategy specification.

## Token Wrapping

DeFi protocols require specific wrapped token forms. The strategy handles wrapping automatically via
`CollateralValidationMixin`:

| Source Token | Wrapped Token | When Required                       | Wrapping Contract |
| ------------ | ------------- | ----------------------------------- | ----------------- |
| ETH          | WETH          | Uniswap V3 swaps, Aave deposits     | WETH9             |
| eETH         | weETH         | Aave collateral (eETH is rebasing)  | EtherFi weETH     |
| stETH        | wstETH        | Aave collateral (stETH is rebasing) | Lido wstETH       |

Rebasing tokens (eETH, stETH) cannot be used as Aave collateral directly because their balance changes break Aave's
scaled balance accounting. Wrapping converts them to non-rebasing equivalents where yield accrues via exchange rate
appreciation instead of balance changes.

The `CollateralValidationMixin` checks the target venue's accepted collateral and emits WRAP instructions before LEND
instructions when needed. This is transparent to the strategy logic -- it only deals with the wrapped form.

See [cross-cutting/venue-collateral-and-wrapping.md](../cross-cutting/venue-collateral-and-wrapping.md) for the full
wrapping matrix.

## Share Class

The staked basis trade supports the same share classes as the plain basis trade. The share class determines the base
currency for P&L and the delta neutrality target.

| Share Class | Target Delta             | P&L Currency | Notes                                                           |
| ----------- | ------------------------ | ------------ | --------------------------------------------------------------- |
| `USDT`      | 0 (fully market neutral) | USD          | Default. weETH long + perp short cancel. Pure yield harvesting. |
| `ETH`       | total_equity_in_eth      | ETH          | Perp hedge removes basis risk but preserves ETH exposure.       |
| `BTC`       | total_equity_in_btc      | BTC          | Same pattern. Less common for staked basis.                     |

For `ETH` share class with staked basis, delta neutrality means the weETH appreciation (staking yield) accrues as
additional ETH-denominated return on top of the share class baseline. The FX factor separates base-currency conversion
from staking + funding P&L in attribution.

See [cross-cutting/share-classes.md](../cross-cutting/share-classes.md) for the full cross-strategy specification.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_staked_basis.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **EtherFi connector:** `execution-service/protocols/etherfi.py`
- **Hyperliquid connector:** `execution-service/protocols/hyperliquid.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
