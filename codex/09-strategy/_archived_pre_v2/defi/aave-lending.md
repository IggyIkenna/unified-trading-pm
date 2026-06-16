---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# DeFi AAVE Lending

> **Asset class:** DeFi **Strategy type:** Pure Lending Yield **Strategy ID pattern:** `DEFI_USDT_LENDING_SCE_1H`

## Overview

Deposit USDT into Aave V3 to earn lending yield. The simplest DeFi yield strategy -- no hedging, no staking, no
leverage. PnL comes entirely from Aave liquidity index growth as borrowers pay interest.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDT  (100% USDT)

Step 1 - LEND:  USDT --> aUSDT   (supply to AAVE_V3_ETHEREUM)
                You send USDT to Aave Pool contract.
                Aave mints aUSDT to your wallet.
                Records entry_liquidity_index.

Wallet after deploy:
  - AAVE_V3_ETHEREUM:A_TOKEN:AUSDT@ETHEREUM = initial_amount (but growing via index)

On exit:
Step 2 - WITHDRAW: aUSDT --> USDT  (burn aUSDT, receive USDT + accrued interest)
```

## Instruments

| Instrument Key                            | Venue   | Type   | Role                   |
| ----------------------------------------- | ------- | ------ | ---------------------- |
| `WALLET:SPOT_ASSET:USDT`                  | Wallet  | Spot   | Initial capital        |
| `AAVE_V3_ETHEREUM:A_TOKEN:AUSDT@ETHEREUM` | Aave V3 | aToken | Yield-bearing position |

## Data Architecture

| Dimension              | Value                                                                             | SSOT                                |
| ---------------------- | --------------------------------------------------------------------------------- | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                         | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: `aave_supply_apy`, `aave_utilization`, `aave_liquidity_index` | Features hydrated alongside candles |
| **Features**           | `features` dict: `aave_supply_apy`, `aave_utilization`, `aave_liquidity_index`    | `features-onchain-service`          |
| **Interval**           | Time-driven (candle-based), not event-driven                                      | `timeframe` in strategy config      |
| **Lowest granularity** | 1H (currently hardcoded in factory, not configurable)                             | `defi_lending.py` factory           |
| **Execution mode**     | `same_candle_exit` — entry and exit can occur in same candle                      | Strategy config                     |

**Gap:** Timeframe is hardcoded to 1H. For a pure lending strategy, longer timeframes (4H/1D) would reduce gas costs.

## Instrument Selection

**Currently: STATIC (supply token configurable at init, not dynamic)**

The supply token is a factory parameter (`supply_token="USDT"`) set once at initialisation:

- Instrument: `AAVE_V3_ETHEREUM:A_TOKEN:A{supply_token}@ETHEREUM`

There is **no dynamic token selection** — the strategy does NOT compare USDT vs USDC vs DAI supply APYs and pick the
best one. This is a gap: a "lending SOR" could select the highest-yielding stablecoin that meets utilization and
withdrawal risk thresholds.

**SSOT for venue capabilities:** See
[`VENUE_CAPABILITIES`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is NOT used for this strategy.** Pure lending has no swap leg — only LEND/WITHDRAW operations directly with Aave
V3. There are no alternative venues for the same aToken.

**Future consideration:** If the strategy expanded to compare Aave vs Morpho vs Compound for the same stablecoin,
SOR-like logic could pick the highest-yielding protocol. This would be "protocol SOR" rather than "venue SOR".

## Aave V3 aToken Mechanics

aUSDT is internally tracked using **scaled balances** and a **liquidity index**:

- **At deposit:** `scaledBalance = amount / liquidityIndex_at_deposit`
- **At any time:** `actualBalance = scaledBalance * currentLiquidityIndex`
- **RAY = 10^27** (Aave precision unit)
- `liquidityIndex` starts at 1.0 \* RAY and **monotonically increases** as borrowers pay interest
- Your visible balance grows with every block -- no claim action needed
- When you withdraw: burn aUSDT, receive USDT (now > initial amount)

**This is NOT an APY approximation.** The system reads `liquidityIndex` directly from on-chain
(`pool.functions.getReserveData(token).call()`) and calculates yield from actual index changes:

```
yield = position_size * (current_index - last_index) / last_index
```

## Key Features Consumed

| Feature                | Source Service   | SLA | Used For                                 |
| ---------------------- | ---------------- | --- | ---------------------------------------- |
| `aave_supply_apy`      | features-onchain | 60s | Signal: deploy if APY >= threshold       |
| `aave_utilization`     | features-onchain | 60s | Risk: high utilization = withdrawal risk |
| `aave_liquidity_index` | features-onchain | 60s | PnL: actual yield calculation            |

## PnL Attribution

| Component           | Settlement Type           | Mechanism                                                   |
| ------------------- | ------------------------- | ----------------------------------------------------------- |
| `lending_yield_pnl` | `AAVE_INDEX` (per candle) | `position_size * (current_index - last_index) / last_index` |
| `transaction_costs` | Per-fill                  | Gas for supply (~200k) and withdraw (~250k)                 |

**Source of truth:** `total_pnl = aUSDT_balance * price - initial_deposit` (balance-based).

Settlement service applies AAVE_INDEX events directly to position sizes -- the position balance grows to reflect actual
on-chain aToken balance. The `lending_yield_pnl` attribution bucket captures the same delta for PnL reporting.

**Entry/exit logic (signal generation only, NOT PnL):**

```
Deploy if: aave_supply_apy >= MIN_APY_THRESHOLD (e.g., 3%)
Exit if:   aave_supply_apy < 50% of MIN_APY_THRESHOLD
           OR aave_utilization > 95% (withdrawal risk)
```

## Risk Profile

| Metric               | Target | Notes                                                         |
| -------------------- | ------ | ------------------------------------------------------------- |
| Target annual return | 3-8%   | Varies with Aave utilization and market demand                |
| Target Sharpe ratio  | 3.0+   | Very stable -- yield accrues monotonically                    |
| Max drawdown         | 1%     | Primarily from gas costs on entry/exit during low-APY periods |
| Max leverage         | 1x     | No leverage                                                   |
| Capital scalability  | $50M+  | Aave V3 USDT pool has $1B+ TVL                                |

## Latency Profile

| Segment                               | p50 Target | p99 Target | Co-location Needed?          |
| ------------------------------------- | ---------- | ---------- | ---------------------------- |
| Market data -> feature                | 100ms      | 500ms      | No                           |
| Feature -> signal                     | 10ms       | 50ms       | No                           |
| Signal -> instruction                 | 5ms        | 20ms       | No                           |
| Instruction -> fill (supply/withdraw) | 2s         | 30s        | No (on-chain, gas dependent) |
| **End-to-end**                        | **~3s**    | **~31s**   | **No**                       |

Extremely low-frequency. Decisions made on 1h+ candles. Speed is irrelevant.

## Execution Details

- **Venues:** Aave V3 (Ethereum mainnet)
- **Order types:** Supply (deposit), Withdraw (redeem)
- **Atomic execution required?** No -- single transaction per operation
- **Gas budget:** ~200k gas for supply, ~250k for withdraw

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). No rebalance without new market data.

This strategy has **no delta to rebalance** — it's a single lending position. Rebalancing only applies to entry/exit
decisions based on APY and utilization thresholds.

| Level    | Condition                          | Action         | Notes                |
| -------- | ---------------------------------- | -------------- | -------------------- |
| Minor    | >5% APY drift from entry           | LOG_ONLY       | Log APY change       |
| Major    | >10% APY drift OR utilization >90% | REBALANCE      | Consider exit        |
| Critical | >20% APY drift OR utilization >95% | EMERGENCY_EXIT | Withdraw immediately |

Thresholds from `defi_base.py:_parse_thresholds()` — wider than basis strategies because lending is lower risk. SSOT:
[`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions → exposures) → RiskMonitor (exposures → risk assessment) → Strategy (risk
assessment → rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern       | Exposure Type                      | Used For         |
| ------------------------ | ---------------------------------- | ---------------- |
| `AAVE_V3:A_TOKEN:*`      | aToken balance (growing via index) | Yield tracking   |
| `WALLET:SPOT_ASSET:USDT` | Wallet balance (pre/post deploy)   | Capital tracking |

Config: `defi_mode.enabled=True`, `defi_mode.track_aave_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type          | Subscribed? | Threshold              | Action on Breach                    |
| ------------------ | ----------- | ---------------------- | ----------------------------------- |
| `protocol_risk`    | YES         | Aave utilization > 95% | Emergency withdraw                  |
| `liquidity`        | YES         | Aave utilization > 90% | Alert, consider exit                |
| `staking_yield`    | NO          | —                      | No staking                          |
| `delta`            | NO          | —                      | No delta exposure (single position) |
| `funding`          | NO          | —                      | No perp positions                   |
| `basis`            | NO          | —                      | No basis trade                      |
| `borrow_cost`      | NO          | —                      | No borrowing                        |
| `aave_liquidation` | NO          | —                      | No debt = no liquidation risk       |
| `venue_protocol`   | NO          | —                      | Single venue (Aave V3)              |

Config: `enabled_risk_types: ["aave_liquidation"]` (for utilization monitoring), `defi_risk.enabled=True`,
`defi_risk.aave_liquidation=True` SSOT: [`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

Note: `aave_liquidation` is enabled in config even though there's no debt — the RiskMonitor uses this flag to also
monitor utilization risk (which affects withdrawal ability).

**Gap:** Risk subscriptions are implicit in code defaults. Plan item `p5-risk-strategy-subscription` will create
`StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk              | What It Measures                                     | Evaluation Method  |
| ------------------------ | ---------------------------------------------------- | ------------------ |
| Utilization spike risk   | Aave utilization approaches 100% → can't withdraw    | `threshold_breach` |
| Supply APY collapse      | APY drops below profitable threshold after gas costs | `rate_sensitivity` |
| Protocol governance risk | Aave governance changes reserve parameters           | monitoring only    |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** None -- this is a supply-only position (no borrowing)
- **Health factor threshold:** N/A (no debt)
- **Liquidation risk:** Zero (no collateral/debt relationship)
- **Withdrawal risk:** If Aave utilization hits 100%, cannot withdraw until borrowers repay
- **Smart contract risk:** Aave V3 has been audited extensively but protocol risk always exists
- **Monitoring:** Utilization rate checked per candle; alert at >90%

## Authentication & Credentials

| Venue             | Secret Name                   | Testnet Available? | Notes                               |
| ----------------- | ----------------------------- | ------------------ | ----------------------------------- |
| Aave V3 (via RPC) | `alchemy-api-key`             | Yes (Sepolia)      | Aave V3 deployed on Sepolia testnet |
| Wallet            | `wallet-{client}-private-key` | Yes (dev wallet)   | Signs supply/withdraw transactions  |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Wallet per client (separate aUSDT holdings)
2. No venue accounts needed (Aave is permissionless -- interact via wallet)
3. Config: `initial_capital`, `min_apy_threshold` (default 3%)
4. **Restart required?** No -- hot-reload via GCS config

## UI Visualisation

### Standard views

- PnL waterfall, position breakdown (from monitoring UI plans)
- Margin health is N/A for this strategy (no debt)

### Strategy-specific views

- **Aave supply APY time series** -- current APY vs threshold, with utilization overlay
- **Liquidity index growth chart** -- monotonically increasing, shows compounding
- **Utilization rate monitor** -- with 90% and 95% alert zones
- **Yield comparison panel** -- Aave vs Morpho vs Euler vs Compound (which has best rate now)

## Testing Stage Status

| Stage        | Status  | Notes                                                                 |
| ------------ | ------- | --------------------------------------------------------------------- |
| MOCK         | Pending | Need MockDeFiDynamics with utilization-driven APY spikes              |
| HISTORICAL   | Pending | Aave liquidity_index available since V3 launch via AaveScan/Graph     |
| LIVE_MOCK    | Pending | Blocked by features-onchain aave_supply_apy calculator (#6)           |
| LIVE_TESTNET | Pending | Aave V3 on Sepolia -- testnet contract addresses needed (#3)          |
| BATCH_REAL   | Pending | Best data availability of all DeFi strategies (full on-chain history) |
| STAGING      | Pending | Tenderly fork                                                         |
| LIVE_REAL    | Pending | All above + real capital approval                                     |

## Underlying Families / Lending Basket

The `lending_basket` config parameter defines a list of correlated tokens forming a family. Tokens within a family are
interchangeable from a lending perspective -- the strategy treats them as equivalent collateral and switches between
them based on real-time APY.

### Defined Families

- **Stablecoin family:** `["USDC", "USDT", "DAI"]` -- all USD-pegged, interchangeable for lending yield
- **ETH family:** `["ETH", "WETH"]` -- native ETH and wrapped ETH, same underlying value

### Registry and Configuration

- **Possible universe** is defined in UAC (`unified-api-contracts`) as registry data. This is the SSOT for which tokens
  can form families and which Aave reserve pools exist per chain.
- **Configured family** lives in the strategy config as a **fixed** parameter. The basket is NOT gridded -- you don't
  grid USDC/USDT/DAI combinations. You grid other parameters (APY thresholds, utilization limits, rebalance frequency)
  around the family.
- At strategy init, the configured `lending_basket` is validated against the UAC registry. If a token in the basket has
  no corresponding Aave reserve on the target chain, init fails loud with a clear error message.

## Smart Routing Within Family

On each candle, the strategy performs intra-family APY comparison to maximise yield:

1. Read `aave_supply_apy_{TOKEN}` for each token in the basket (e.g., `aave_supply_apy_USDC`, `aave_supply_apy_USDT`,
   `aave_supply_apy_DAI`)
2. Pick the highest APY token in the family
3. If the wallet currently holds a different token from the family, emit a SWAP instruction first (same-chain DEX SOR
   via execution-service)
4. Then emit TRANSFER + LEND instructions as normal

**SOR constraint:** routing is always same-chain. Cross-chain transfers require bridging, which is a multi-leg
non-atomic operation and belongs to the omnichain-transfers strategy, not the lending strategy.

**Cost guard:** the swap is only emitted if the APY improvement exceeds the swap cost (gas + slippage). A 0.01% APY
improvement on a $10K position does not justify a $5 swap cost. The threshold is configurable via
`min_apy_improvement_bps` (default: 50 bps).

## ETH Lending Variant

A dedicated factory function creates the ETH-denominated lending strategy:

- **Factory:** `create_eth_lending_strategy()` with `lending_basket=["ETH", "WETH"]`
- **Instrument:** `AAVE_V3-ETHEREUM:A_TOKEN:AWETH@ETHEREUM`
- **Target APY:** ~2% (lower than stablecoins due to lower borrow demand for ETH)
- **Use case:** ETH-denominated returns for ETH share class clients. Avoids USD/ETH FX risk -- returns accrue in the
  same denomination as the capital base.

The same smart routing logic applies: if ETH has higher supply APY than WETH (rare but possible during high wrapping
activity), the strategy routes accordingly.

## Wallet & Capital Flow

| Component        | Value                            |
| ---------------- | -------------------------------- |
| Treasury reserve | 20% of AUM                       |
| Hot wallet       | Per-chain, per-strategy isolated |
| CeFi sub-account | No                               |
| Bridge required  | No (single-chain)                |
| Custody          | Copper MPC                       |

Capital flow: Client deposit --> treasury --> hot wallet --> TRANSFER + LEND to Aave V3. Rebalance: treasury < 10% -->
strategy reduces position --> WITHDRAW + TRANSFER --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM chains). The MTDS `gas_fee_handler` fetches
real-time gas prices and writes them as features consumed by the strategy. Gas hits P&L immediately as a realized
transaction cost -- not estimated or amortized. For this single-chain strategy (Ethereum mainnet), gas costs are the
primary cost drag (~$15-25 per supply/withdraw at 30 gwei).

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). For
lending markets, the **base asset must be in `DEFI_MAJOR_ASSET_SYMBOLS`** (~65 tokens). The lending basket tokens (USDC,
USDT, DAI for stablecoin family; ETH, WETH for ETH family) are all in the whitelist. Validated at strategy init.

## E2E Manual Trading Workflow

Step-by-step manual recreation of the AAVE lending strategy. Each step maps to a StrategyInstruction type and a backend
service interaction.

### Prerequisites

- Treasury wallet funded with USDC/USDT/DAI on Ethereum
- Trading wallet created (per-strategy, per-chain)
- Alchemy RPC configured for Ethereum

### Step-by-Step

| Step | Action                                             | Instruction Type | Service                                     | Instant P&L                        |
| ---- | -------------------------------------------------- | ---------------- | ------------------------------------------- | ---------------------------------- |
| 1    | Observe treasury balance                           | —                | position-balance-monitor (treasury_monitor) | —                                  |
| 2    | Transfer $100K USDC from treasury → trading wallet | TRANSFER         | execution-service (custody provider)        | Gas: ~$2                           |
| 3    | Approve USDC spend on AAVE V3                      | —                | execution-service (ERC-20 approve)          | Gas: ~$5                           |
| 4    | Supply USDC to AAVE V3 pool                        | LEND             | execution-service (AaveConnector.supply)    | Gas: ~$12. Expected: 100,000 aUSDC |
| 5    | Verify aUSDC balance in trading wallet             | —                | position-balance-monitor                    | aUSDC balance = supplied amount    |

### Position State After Deployment

- Trading wallet: 100,000 aUSDC (yield-bearing)
- Treasury: reduced by $100K + gas costs
- No debt, no perp position
- Health Factor: N/A (no borrowing)

### Instant P&L Per Step

- Step 2: -$2 (gas for transfer)
- Step 4: -$12 (gas for AAVE supply). aUSDC received = USDC supplied (1:1 at entry via liquidity index)
- Total entry cost: ~$14

### Ongoing P&L (Daily)

- Interest accrues via AAVE liquidity index: `daily_interest = position * (index_today / index_yesterday - 1)`
- At 4.8% APY on $100K: ~$13.15/day
- Cost recovery: ~1.1 days

### Risk Metrics

- Health Factor: N/A (pure lending, no debt)
- Liquidation risk: None
- Protocol risk: AAVE V3 smart contract risk
- Utilization risk: if pool utilization > 90%, withdrawal may be delayed

### Exit Workflow

| Step | Action                                                          | Instruction Type | Instant P&L |
| ---- | --------------------------------------------------------------- | ---------------- | ----------- |
| 1    | Withdraw aUSDC from AAVE (burns aUSDC, returns USDC + interest) | WITHDRAW         | Gas: ~$12   |
| 2    | Transfer USDC from trading wallet → treasury                    | TRANSFER         | Gas: ~$2    |
| 3    | Total exit cost: ~$14                                           | —                | —           |

### Service Interaction Diagram

```
User (UI)
  │
  ├──→ position-balance-monitor: read treasury balance
  ├──→ execution-service: TRANSFER (custody signs tx)
  ├──→ execution-service: LEND (AaveConnector.supply via RPC)
  ├──→ position-balance-monitor: read aUSDC balance
  ├──→ pnl-attribution-service: compute daily interest P&L
  └──→ risk-and-exposure-service: compute HF/LTV (N/A for pure lending)
```

### Trade History (Expected Output)

| #   | Time  | Type     | Instrument | Amount  | Price | Gas    | Slippage | Running P&L |
| --- | ----- | -------- | ---------- | ------- | ----- | ------ | -------- | ----------- |
| 1   | 10:01 | TRANSFER | USDC       | 100,000 | $1.00 | $2.00  | $0       | -$2.00      |
| 2   | 10:02 | LEND     | aUSDC      | 100,000 | $1.00 | $12.00 | $0       | -$14.00     |
| 3   | EOD   | INTEREST | aUSDC      | +13.15  | $1.00 | $0     | $0       | -$0.85      |
| 4   | Day 2 | INTEREST | aUSDC      | +13.15  | $1.00 | $0     | $0       | +$12.30     |

## Oracle Depeg Risk

Aave V3 uses Chainlink oracles for asset pricing. If the protocol oracle price diverges from the market price, the
on-chain health factor and liquidation thresholds become unreliable. The strategy monitors oracle accuracy as a risk
signal.

| Divergence (oracle vs market) | Severity  | Action                                                       |
| ----------------------------- | --------- | ------------------------------------------------------------ |
| < 1%                          | NORMAL    | No action. Expected noise.                                   |
| 1% - 2%                       | WARNING   | Log alert. Increase monitoring frequency to every 5 minutes. |
| 2% - 3%                       | CRITICAL  | Reduce position by 50%. Alert sent to client.                |
| > 3%                          | EMERGENCY | Full withdrawal. Oracle may be stale or manipulated.         |

Oracle price is read from Chainlink aggregator via `features-onchain-service`. Market price comes from
`market-tick-data-service` (aggregated across CEX venues). The divergence check runs on every candle.

For the pure lending strategy (no debt), oracle depeg does not cause liquidation directly -- but it signals broader
protocol instability. If Aave's oracle misprices the supplied asset, other users' positions may be liquidated
incorrectly, causing cascade effects on utilization and withdrawal availability.

## Borrow-Staking Spread

When the lending strategy is combined with staking (ETH lending variant), the net spread between staking yield and
borrow cost determines profitability after leverage.

```
net_spread = staking_apy - borrow_apy
effective_yield = net_spread * leverage + base_supply_apy
```

| Condition                                    | Severity | Action                                           |
| -------------------------------------------- | -------- | ------------------------------------------------ |
| `net_spread > 0` after leverage              | NORMAL   | Strategy is profitable. Continue.                |
| `net_spread > 0` but negative after leverage | WARNING  | Leverage cost exceeds spread. Reduce leverage.   |
| `net_spread < 0`                             | CRITICAL | Borrow rate exceeds staking yield. Exit staking. |

This monitoring applies only when the lending strategy is used in conjunction with a staking position (ETH family). For
the pure stablecoin lending variant, borrow-staking spread is not applicable.

## Stablecoin Depeg Monitoring

For stablecoin lending (USDC, USDT, DAI family), the strategy monitors the peg stability of the supplied asset. A depeg
event can cause bank-run dynamics on Aave -- other users rush to withdraw, pushing utilization to 100% and blocking
further withdrawals.

| Depeg (vs $1.00) | Severity  | Action                                                           |
| ---------------- | --------- | ---------------------------------------------------------------- |
| < 0.5%           | NORMAL    | No action. Normal fluctuation.                                   |
| 0.5% - 1.0%      | WARNING   | Log alert. Prepare withdrawal instructions.                      |
| 1.0% - 2.0%      | CRITICAL  | Withdraw 50% of position. Monitor utilization.                   |
| > 2.0%           | EMERGENCY | Full withdrawal. Accept slippage to exit before utilization cap. |

Depeg is measured as `abs(1.0 - token_price_usd)` using market-tick-data-service prices (CEX aggregated, not Aave
oracle). The strategy checks depeg on every candle for the currently supplied token.

If the strategy holds a diversified basket (USDC + USDT + DAI), a depeg in one token triggers rebalancing to the
non-depegged tokens before considering full exit. This is handled by the smart routing within family logic (see above).

## Share Class

The lending strategy supports share classes primarily for the ETH lending variant.

| Share Class | Supply Token  | P&L Currency | Notes                                                  |
| ----------- | ------------- | ------------ | ------------------------------------------------------ |
| `USDT`      | USDC/USDT/DAI | USD          | Default for stablecoin family. P&L is straightforward. |
| `ETH`       | ETH/WETH      | ETH          | ETH lending variant. Returns denominated in ETH.       |

For `USDT` share class, the lending yield is denominated in the same currency as the capital (USD stablecoins), so no FX
factor applies. For `ETH` share class, the supply APY accrues in ETH-denominated terms. The FX factor separates ETH/USD
price movements from the lending yield in P&L attribution.

When a `USDT` share class client holds ETH family lending positions (rare but possible as a hedge component), the ETH
price exposure is an additional delta that must be managed. In practice, the lending strategy defaults to matching the
share class with the lending family: USDT share class uses stablecoin family, ETH share class uses ETH family.

See [cross-cutting/share-classes.md](../cross-cutting/share-classes.md) for the full cross-strategy specification.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_lending.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Aave connector:** `execution-service/protocols/aave.py`
- **Aave positions:**
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/aave_positions.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
- **UAC token registry:** `unified-api-contracts/registry/` (lending basket universe)
