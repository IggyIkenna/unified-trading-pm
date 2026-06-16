---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# DeFi BTC Lending Yield

> **Asset class:** DeFi **Strategy type:** Yield (multi-chain lending with optional leverage) **Strategy ID pattern:**
> `DEFI_BTC_LENDING_AAVE_4H`

## Overview

Supply WBTC or cbBTC to Aave V3 across multiple EVM chains to earn lending yield. Uses CrossChainSOR to find the best
APY across Ethereum, Arbitrum, Polygon, Optimism, and Base. In its simple form, this is a single-sided supply earning
1-5% APY. In its leveraged form, WBTC is supplied as collateral, stablecoins are borrowed against it, and the borrowed
stablecoins are re-supplied to earn the spread between supply and borrow rates multiplied by leverage.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDT  (100% USDT)

=== Simple (Unleveraged) Variant ===

Step 1 - SWAP:     USDT --> WBTC         (100% of capital, via Uniswap/Curve SOR)
Step 2 - SUPPLY:   WBTC --> Aave V3      (supply WBTC, receive aWBTC)

Wallet after deploy:
  - AAVE_V3-{CHAIN}:A_TOKEN:AWBTC        = wbtc_amount  (earning supply APY)

=== Leveraged Variant (2x example) ===

Step 1 - SWAP:     USDT --> WBTC         (100% of capital, via Uniswap/Curve SOR)
Step 2 - SUPPLY:   WBTC --> Aave V3      (supply WBTC as collateral, receive aWBTC)
Step 3 - BORROW:   Borrow USDC from Aave (borrow up to 50% LTV against WBTC)
Step 4 - SWAP:     USDC --> WBTC         (swap borrowed USDC to WBTC)
Step 5 - SUPPLY:   WBTC --> Aave V3      (supply additional WBTC)

Wallet after deploy (2x leveraged):
  - AAVE_V3-{CHAIN}:A_TOKEN:AWBTC        = 2 * wbtc_amount  (earning supply APY)
  - AAVE_V3-{CHAIN}:DEBT_TOKEN:DEBTUSDC  = borrow_amount    (paying borrow APY)

Net yield = (supply_apy * 2) - (borrow_apy * 1) = spread * leverage

=== Cross-Chain Migration ===

Step M1 - WITHDRAW: aWBTC --> WBTC       (from low-APY chain)
Step M2 - BRIDGE:   WBTC via Socket      (to high-APY chain)
Step M3 - SUPPLY:   WBTC --> Aave V3     (on high-APY chain)

Only triggers when: net_APY_new - net_APY_current > annualized(gas_cost + bridge_fee)
```

## Instruments

| Instrument Key                        | Venue   | Type      | Role                           |
| ------------------------------------- | ------- | --------- | ------------------------------ |
| `WALLET:SPOT_ASSET:USDT`              | Wallet  | Spot      | Initial capital                |
| `AAVE_V3-ETHEREUM:A_TOKEN:AWBTC`      | Aave V3 | aToken    | Supply position (Ethereum)     |
| `AAVE_V3-ARBITRUM:A_TOKEN:AWBTC`      | Aave V3 | aToken    | Supply position (Arbitrum)     |
| `AAVE_V3-OPTIMISM:A_TOKEN:AWBTC`      | Aave V3 | aToken    | Supply position (Optimism)     |
| `AAVE_V3-POLYGON:A_TOKEN:AWBTC`       | Aave V3 | aToken    | Supply position (Polygon)      |
| `AAVE_V3-BASE:A_TOKEN:ACBBTC`         | Aave V3 | aToken    | Supply position (Base, cbBTC)  |
| `AAVE_V3-{CHAIN}:DEBT_TOKEN:DEBTUSDC` | Aave V3 | debtToken | Borrow position (if leveraged) |

## Key Features Consumed

| Feature                      | Source Service   | SLA | Used For                                      |
| ---------------------------- | ---------------- | --- | --------------------------------------------- |
| `aave_wbtc_supply_apy`       | features-onchain | 60s | Per-chain supply APY for CrossChainSOR        |
| `aave_usdc_borrow_apy`       | features-onchain | 60s | Borrow cost calculation (leveraged variant)   |
| `btc_price`                  | market-tick-data | 1s  | Position valuation, health factor calculation |
| `gas_price_per_chain`        | features-onchain | 30s | CrossChainSOR cost comparison                 |
| `aave_wbtc_utilization_rate` | features-onchain | 60s | APY stability indicator                       |

## Data Architecture

| Dimension              | Value                                                                                  | SSOT                                |
| ---------------------- | -------------------------------------------------------------------------------------- | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                              | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: `btc_price`, `aave_wbtc_supply_apy` (per chain), `gas_price`       | Features hydrated alongside candles |
| **Features**           | `features` dict: `aave_wbtc_supply_apy`, `aave_usdc_borrow_apy`, `gas_price_per_chain` | `features-onchain-service`          |
| **Interval**           | Time-driven (candle-based), not event-driven                                           | `timeframe` in strategy config      |
| **Lowest granularity** | 4H (APY changes slowly, no benefit from more frequent checks)                          | `defi_btc_lending.py` factory       |
| **Execution mode**     | `same_candle_exit` -- entry and exit can occur in same candle                          | Strategy config                     |

## Instrument Selection

**Currently: DYNAMIC via CrossChainSOR**

Unlike most DeFi strategies, this strategy dynamically selects which chain to deploy on:

- **CrossChainSOR** evaluates all 5 chains every 4H
- Selects chain with highest `net_APY = gross_APY - annualized(gas_cost + bridge_fee)`
- Only migrates if net APY improvement exceeds annualized migration cost
- Prefers L2s (Arbitrum, Optimism, Base) due to lower gas for rebalancing

**WBTC vs cbBTC selection:** cbBTC is used on Base (native asset); WBTC is used on all other chains.

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**Two SOR layers operate in this strategy:**

### Layer 1: DEX SOR (swap leg)

| Leg                       | SOR? | Allowed Venues                                                  | SSOT                 |
| ------------------------- | ---- | --------------------------------------------------------------- | -------------------- |
| Step 1 (USDT-->WBTC swap) | YES  | Chain-dependent (e.g., `UNISWAP_V3-ETHEREUM`, `CURVE-ETHEREUM`) | `defi_base.py:84-86` |

### Layer 2: CrossChainSOR (chain selection)

| Decision                    | SOR?          | Evaluated Chains                            | SSOT                 |
| --------------------------- | ------------- | ------------------------------------------- | -------------------- |
| Which chain to supply WBTC? | YES (4H tick) | Ethereum, Arbitrum, Optimism, Polygon, Base | CrossChainSOR config |

CrossChainSOR formula:

```
net_APY(chain) = aave_wbtc_supply_apy(chain) - annualized_gas(chain) - annualized_bridge_fee
best_chain     = argmax(net_APY)
migrate_if     = net_APY(best_chain) - net_APY(current_chain) > annualized(migration_cost)
```

**Execution boundary:** Strategy sends `StrategyInstruction` with `target_chain`, `allowed_venues`, `max_slippage_bps`.
Execution-service handles swap, bridge (via Socket), and Aave supply/withdraw.

## PnL Attribution

| Component           | Settlement Type            | Mechanism                                                        |
| ------------------- | -------------------------- | ---------------------------------------------------------------- |
| `supply_yield_pnl`  | `AAVE_SUPPLY` (per candle) | aWBTC balance growth from supply APY                             |
| `borrow_cost_pnl`   | `AAVE_BORROW` (per candle) | USDC debt growth from borrow APY (negative, leveraged only)      |
| `btc_price_pnl`     | Mark-to-market             | BTC price change (NOT delta-neutral -- directional BTC exposure) |
| `bridge_cost`       | Per-migration              | Socket bridge fee for cross-chain migration                      |
| `transaction_costs` | Per-fill                   | Swap fee + gas + Aave supply/withdraw gas                        |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

**Important:** This strategy has **directional BTC exposure**. Unlike the basis trade, there is no perp hedge. BTC price
movements are the dominant PnL driver. The lending yield is an enhancement on top of a long-BTC position.

**Yield calculation:**

```
unleveraged_apy = aave_wbtc_supply_apy
leveraged_apy   = (aave_wbtc_supply_apy * leverage) - (aave_usdc_borrow_apy * (leverage - 1))
net_apy         = leveraged_apy - annualized(gas + bridge_fees)

Example (2x leverage, Arbitrum):
  supply_apy = 3.0%, borrow_apy = 5.0%, leverage = 2x
  leveraged_apy = (3.0% * 2) - (5.0% * 1) = 1.0%
  + BTC price appreciation (variable)
```

## Risk Profile

| Metric               | Target                                        | Notes                                               |
| -------------------- | --------------------------------------------- | --------------------------------------------------- |
| Target annual return | 3-8% (unleveraged), 8-15% (2x leveraged)      | Excludes BTC price appreciation                     |
| Target Sharpe ratio  | 0.8+ (yield only), higher with BTC bull trend | Directional BTC exposure                            |
| Max drawdown         | 15%                                           | Primarily from BTC price decline                    |
| Max leverage         | 3x                                            | Conservative LTV to maintain health factor > 2.0    |
| Capital scalability  | $50M                                          | Aave WBTC supply caps vary by chain ($10-100M each) |

## Latency Profile

| Segment                       | p50 Target | p99 Target | Co-location Needed?           |
| ----------------------------- | ---------- | ---------- | ----------------------------- |
| Market data --> feature       | 100ms      | 500ms      | No                            |
| Feature --> signal            | 20ms       | 100ms      | No                            |
| Signal --> instruction        | 10ms       | 50ms       | No                            |
| Instruction --> fill (supply) | 3s         | 20s        | No (on-chain)                 |
| Instruction --> fill (bridge) | 30s        | 120s       | No (cross-chain, block times) |
| **End-to-end**                | **~35s**   | **~140s**  | **No**                        |

Very low-frequency strategy (4h candles). Cross-chain migration adds latency from bridge confirmations (1-5 minutes
depending on chain). Co-location provides no benefit.

## Execution Details

- **Venues:** Uniswap V3 / Curve (swap via SOR), Aave V3 (supply/borrow), Socket (bridge)
- **Order types:** Market (swap via SOR), Supply/Withdraw/Borrow/Repay (Aave), Bridge (Socket)
- **Atomic execution required?** No -- each step is independent. Bridge is inherently async.
- **Gas budget:** ~0.005 ETH on Ethereum mainnet per supply/withdraw, ~0.0002 ETH on L2s

### Rebalancing

**Trigger type:** Time-driven (4H candle) + event-driven (health factor breach).

| Level       | Trigger                                 | Action                    | Notes                                 |
| ----------- | --------------------------------------- | ------------------------- | ------------------------------------- |
| APY check   | Every 4H candle                         | Evaluate CrossChainSOR    | Migrate if net APY improvement > cost |
| Leverage    | Spread narrows (supply - borrow < 50bp) | Deleverage                | Repay USDC, withdraw excess WBTC      |
| Health warn | HF < 1.5                                | Partial deleverage        | Repay 25% of debt to restore HF > 2.0 |
| Health crit | HF < 1.2                                | Emergency full deleverage | Repay all debt immediately            |
| BTC crash   | BTC price drops > 20% in 24h            | Full exit                 | Withdraw all, convert to stables      |

SSOT: [`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions --> exposures) --> RiskMonitor (exposures --> risk assessment) --> Strategy (risk
assessment --> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern              | Exposure Type    | Used For                       |
| ------------------------------- | ---------------- | ------------------------------ |
| `AAVE_V3-*:A_TOKEN:AWBTC`       | Collateral value | Health factor numerator        |
| `AAVE_V3-*:A_TOKEN:ACBBTC`      | Collateral value | Health factor numerator (Base) |
| `AAVE_V3-*:DEBT_TOKEN:DEBTUSDC` | Debt value       | Health factor denominator      |

Config: `defi_mode.enabled=True`, `defi_mode.track_aave_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type       | Subscribed?        | Threshold                          | Action on Breach            |
| --------------- | ------------------ | ---------------------------------- | --------------------------- |
| `protocol_risk` | YES                | Aave HF < 1.5 (warn), < 1.2 (crit) | Deleverage / emergency exit |
| `borrow_cost`   | YES (if leveraged) | Spread < 50bp                      | Deleverage                  |
| `liquidity`     | YES                | Aave utilization > 90%             | Prepare to withdraw         |
| `wbtc_premium`  | YES                | WBTC/BTC premium < -1%             | Exit to stables             |
| `bridge_risk`   | YES                | Socket bridge failure/delay        | Stay on current chain       |
| `delta`         | NO                 | --                                 | Directional, no hedge       |
| `funding`       | NO                 | --                                 | No perp positions           |
| `staking_yield` | NO                 | --                                 | No staking (lending only)   |

Config: `enabled_risk_types: ["aave_liquidation"]`, `defi_risk.enabled=True`, `defi_risk.aave_liquidation=True` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults, not in a machine-readable YAML registry. Plan item
`p5-risk-strategy-subscription` will create `StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk                | What It Measures                                             | Evaluation Method  |
| -------------------------- | ------------------------------------------------------------ | ------------------ |
| Cross-chain bridge failure | Socket bridge tx stuck or reverted during migration          | `threshold_breach` |
| APY regime shift           | Sustained sub-1% WBTC supply APY across all chains           | `rate_sensitivity` |
| Aave utilization spike     | Utilization > 90% (withdrawals may fail due to no liquidity) | `threshold_breach` |
| WBTC custodial event       | BitGo operational incident affecting WBTC backing            | `manual_review`    |
| Leverage cascade risk      | Multiple leveraged users deleverage simultaneously           | `threshold_breach` |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** Aave V3 Health Factor (DeFi native)
- **Health factor target:** 2.0 (conservative)
- **Health factor deleverage:** 1.5 (begin partial repayment)
- **Health factor emergency:** 1.2 (full debt repayment)
- **Liquidation penalty:** 5% of collateral (Aave WBTC liquidation bonus)
- **Liquidation threshold:** ~78% LTV for WBTC on Aave V3 (chain-dependent)
- **Monitoring:** Health factor checked per candle (4H) + event-driven on BTC price moves > 5%
- **Unleveraged variant:** No liquidation risk (supply only, no debt)

## Authentication & Credentials

| Venue      | Secret Name                   | Testnet Available?              | Notes                           |
| ---------- | ----------------------------- | ------------------------------- | ------------------------------- |
| Aave V3    | `alchemy-api-key` (RPC)       | Yes (Sepolia for Ethereum)      | Supply/borrow on each chain     |
| Uniswap V3 | `alchemy-api-key` (RPC)       | Yes (Sepolia)                   | USDT-->WBTC swap                |
| Socket     | `socket-api-key`              | Yes (testnet bridges available) | Cross-chain bridging            |
| Wallet     | `wallet-{client}-private-key` | Yes (dev wallet)                | Signs all on-chain transactions |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Wallet per client (separate WBTC/aWBTC holdings per chain)
2. Config: `initial_capital`, `max_leverage` (default 1x), `target_health_factor` (default 2.0), `allowed_chains`
   (default all 5)
3. Config: `enable_cross_chain_sor` (default true), `min_apy_improvement_bps` (default 50bp to trigger migration)
4. **Restart required?** No -- hot-reload via GCS config

### Services requiring per-client configuration

| Service           | What Changes                    | Restart?        |
| ----------------- | ------------------------------- | --------------- |
| strategy-service  | New config entry in GCS         | No (hot-reload) |
| execution-service | New client routing rule + chain | No (hot-reload) |

## UI Visualisation

### Standard views

- PnL waterfall, margin health, position breakdown (from monitoring UI plans)

### Strategy-specific views

- **Cross-chain APY heatmap** -- 5 chains with current WBTC supply APY, utilization, and net APY after gas
- **Health factor gauge** -- real-time HF with threshold lines at 2.0 (target), 1.5 (warn), 1.2 (crit)
- **Leverage waterfall** -- collateral, debt, net equity, and effective leverage ratio
- **Chain migration history** -- timeline of cross-chain moves with cost and APY improvement
- **Supply APY time series** -- per-chain APY over last 30 days to identify trends
- **Gas cost tracker** -- per-chain gas expenditure with annualized cost impact on net yield

## Testing Stage Status

| Stage        | Status  | Notes                                                                        |
| ------------ | ------- | ---------------------------------------------------------------------------- |
| MOCK         | Pending | Need MockDeFiDynamics with per-chain APY oscillation                         |
| HISTORICAL   | Pending | Need Aave V3 WBTC supply APY history per chain (available via Aave subgraph) |
| LIVE_MOCK    | Pending | Blocked by features-onchain aave_wbtc_supply_apy calculator                  |
| LIVE_TESTNET | Pending | Blocked by Aave V3 Sepolia WBTC market + Socket testnet bridge               |
| BATCH_REAL   | Pending | Blocked by historical per-chain APY storage                                  |
| STAGING      | Pending | Tenderly fork with multi-chain Aave V3 positions                             |
| LIVE_REAL    | Pending | All above + real capital approval                                            |

## Wallet & Capital Flow

| Component        | Value                                                          |
| ---------------- | -------------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                     |
| Hot wallet       | Multi-chain (one per destination chain), per-strategy isolated |
| CeFi sub-account | No                                                             |
| Bridge required  | Yes (multi-chain -- CrossChainSOR selects best chain)          |
| Custody          | Copper MPC                                                     |

Capital flow: Client deposit --> treasury --> hot wallet --> BRIDGE to best chain --> SWAP + LEND WBTC to Aave V3.
Rebalance: treasury < 10% --> strategy reduces position --> WITHDRAW + BRIDGE back --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM). The MTDS `gas_fee_handler` fetches
real-time gas prices per chain and writes them as features consumed by CrossChainSOR. Gas hits P&L immediately as a
realized transaction cost -- not estimated. Gas costs are a key input to the CrossChainSOR scoring formula:
`net_APY = gross_APY - annualized(gas_cost + bridge_fee)`. L2 chains (Arbitrum, Optimism, Base) have ~100x lower gas
than Ethereum mainnet, which the SOR correctly factors into chain selection.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Multi-Chain Support

This strategy operates across 5 EVM chains where Aave V3 supports WBTC markets: Ethereum, Arbitrum, Optimism, Polygon,
Base. All chains have Alchemy RPC endpoints configured via `CHAIN_RPC_TEMPLATES` in UAC
`registry/capability_declarations/_defi.py` (12 EVM mainnets + 10 testnets total in the system).

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). For
lending markets, the **base asset must be in `DEFI_MAJOR_ASSET_SYMBOLS`**. WBTC and CBBTC are both in the BTC family
within the whitelist.

## Bridge Costs

Cross-chain migration via Socket bridge incurs a **one-time P&L hit** (not amortized over the holding period). The
bridge fee (typically 0.04-0.15% depending on route and protocol) is deducted from principal at the time of the bridge
transaction. The CrossChainSOR entry decision checks whether the yield improvement on the target chain recovers the
bridge cost within the expected holding period before initiating a migration. Across API provides live fee quotes;
static estimates from historical averages serve as fallback.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_btc_lending.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md` -- DeFi BTC Lending
- **Execution adapter (Aave):** `execution-service/protocols/aave.py`
- **Execution adapter (swap):** `execution-service/protocols/uniswap.py`
- **Execution adapter (bridge):** `execution-service/protocols/socket_bridge.py`
- **CrossChainSOR:** `strategy-service/strategy_service/engine/sor/cross_chain_sor.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
