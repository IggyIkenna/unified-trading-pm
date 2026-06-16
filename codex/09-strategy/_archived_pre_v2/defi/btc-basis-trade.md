---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# DeFi BTC Basis Trade

> **Asset class:** DeFi **Strategy type:** Basis (delta-neutral funding rate arbitrage on Bitcoin) **Strategy ID
> pattern:** `DEFI_BTC_BASIS_SCE_1H`

## Overview

Long WBTC (or cbBTC) on EVM chains + short BTC-PERP on Hyperliquid. Delta-neutral funding rate arbitrage on Bitcoin. BTC
funding rates are typically lower than ETH (~5-15% APY) but BTC is the largest crypto asset with the deepest perp
liquidity. Optionally supply WBTC to Aave V3 for additional lending yield (~1-3% APY), stacking yield on top of funding.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDT  (100% USDT)

Step 1 - SWAP:     USDT --> WBTC         (85% of capital, via Uniswap/Curve SOR)
Step 2 - TRANSFER: USDT --> USDC         (15% to Hyperliquid as margin)
Step 3 - TRADE:    Short BTC-USDC perp   (size = BTC amount from step 1)

Optional (stacked yield variant):
Step 1b - SUPPLY:  WBTC --> Aave V3      (supply WBTC as collateral, receive aWBTC)

Wallet after deploy (basic):
  - WALLET:SPOT_ASSET:WBTC               = wbtc_amount  (long)
  - HYPERLIQUID:PERPETUAL:BTC-USDC       = -btc_amount  (short)
  - HYPERLIQUID margin                   = 15% USDC

Wallet after deploy (stacked yield):
  - AAVE_V3-ETHEREUM:A_TOKEN:AWBTC        = wbtc_amount  (long, earning supply APY)
  - HYPERLIQUID:PERPETUAL:BTC-USDC       = -btc_amount  (short)
  - HYPERLIQUID margin                   = 15% USDC

Net delta = 0 (long WBTC + short perp cancel)
```

## Instruments

| Instrument Key                                   | Venue       | Type   | Role                       |
| ------------------------------------------------ | ----------- | ------ | -------------------------- |
| `WALLET:SPOT_ASSET:USDT`                         | Wallet      | Spot   | Initial capital            |
| `WALLET:SPOT_ASSET:WBTC`                         | Wallet      | Spot   | Long leg (basic variant)   |
| `AAVE_V3-ETHEREUM:A_TOKEN:AWBTC`                 | Aave V3     | aToken | Long leg (stacked variant) |
| `HYPERLIQUID:PERPETUAL:BTC-USDC@LIN@HYPERLIQUID` | Hyperliquid | Perp   | Short leg (hedge)          |

**Multi-chain option:** Can also use cbBTC (Coinbase wrapped BTC) on Base or Arbitrum for lower gas costs:

| Instrument Key (alternative)     | Venue   | Type   | Role                    |
| -------------------------------- | ------- | ------ | ----------------------- |
| `WALLET:SPOT_ASSET:CBBTC`        | Wallet  | Spot   | Long leg (Base/Arb)     |
| `AAVE_V3-ARBITRUM:A_TOKEN:AWBTC` | Aave V3 | aToken | Long leg (Arb, stacked) |

## Key Features Consumed

| Feature            | Source Service     | SLA | Used For                                    |
| ------------------ | ------------------ | --- | ------------------------------------------- |
| `btc_funding_rate` | features-delta-one | 10s | Signal: entry when funding > threshold      |
| `btc_price`        | market-tick-data   | 1s  | Position sizing, PnL                        |
| `wbtc_premium`     | features-onchain   | 60s | WBTC vs BTC price gap monitoring            |
| `aave_wbtc_apy`    | features-onchain   | 60s | Stacked yield calculation (optional supply) |
| `basis_bps`        | features-delta-one | 10s | BTC basis spread monitoring                 |

## Data Architecture

| Dimension              | Value                                                                             | SSOT                                                      |
| ---------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                         | `strategy-service/config.py`                              |
| **Processed data**     | `market_data` dict: `btc_price`, `btc_funding_rate`, `wbtc_premium`               | Features hydrated alongside candles                       |
| **Features**           | `features` dict: `btc_funding_rate`, `basis_bps`, `wbtc_premium`, `aave_wbtc_apy` | `features-delta-one-service` + `features-onchain-service` |
| **Interval**           | Time-driven (candle-based), not event-driven                                      | `timeframe` in strategy config                            |
| **Lowest granularity** | 1H (currently hardcoded in factory, not configurable)                             | `defi_btc_basis.py` factory                               |
| **Execution mode**     | `same_candle_exit` -- entry and exit can occur in same candle                     | Strategy config                                           |

**Gap:** Timeframe is hardcoded to 1H. Should be configurable via strategy config to support 15m/4H/1D.

## Instrument Selection

**Currently: STATIC (hardcoded per config, no dynamic selection)**

Instruments are set at strategy initialisation and never change:

- Spot: `WALLET:SPOT_ASSET:WBTC` -- always WBTC (or cbBTC via config)
- Perp: `HYPERLIQUID:PERPETUAL:BTC-USDC@LIN@HYPERLIQUID` -- always BTC-USDC on Hyperliquid

There is **no instrument SOR** -- the strategy does NOT dynamically pick between WBTC and cbBTC based on premium/gas.
This is a gap: a "wrapped BTC SOR" could compare WBTC premium, cbBTC premium, and gas costs to select the optimal
wrapped BTC variant.

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON by default for the swap leg only.**

| Leg                       | SOR? | Allowed Venues                                          | SSOT                 |
| ------------------------- | ---- | ------------------------------------------------------- | -------------------- |
| Step 1 (USDT-->WBTC swap) | YES  | `UNISWAP_V3-ETHEREUM`, `CURVE-ETHEREUM`, `BALANCER-ETH` | `defi_base.py:84-86` |
| Step 3 (Short perp)       | NO   | Hyperliquid only (CLOB, no alternative)                 | --                   |

SOR picks the best price across DEX venues for the USDT-->WBTC swap. May route multi-hop (USDT-->WETH-->WBTC) for better
pricing. The `allowed_venues` list is passed in `StrategyInstruction` to execution-service, which handles the actual
routing.

**Multi-chain SOR:** When using Arbitrum, allowed venues change to `UNISWAP_V3-ARBITRUM`, `CURVE-ARBITRUM`.

**Same-wallet constraint:** All SOR venues must be on the same blockchain (same chain as WBTC holding). SSOT:
[`SHARED_WALLET_GROUPS`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

**Execution boundary:** Strategy sends `StrategyInstruction` with `allowed_venues`, `max_slippage_bps`, and
`benchmark_price`. Execution-service converts to `ExecutionInstruction`, picks venue, chooses order type, executes, and
measures alpha vs benchmark.

## WBTC / cbBTC Mechanics

**WBTC (Wrapped Bitcoin):** Custodial wrapped BTC on Ethereum, managed by BitGo. 1:1 backed by BTC held in BitGo
custody. WBTC trades at a small premium or discount to BTC (~0.1-0.5%) depending on demand.

- **Custodial risk:** BitGo holds the underlying BTC. If BitGo is compromised, WBTC loses backing.
- **Depeg history:** Brief depeg to ~0.98 during FTX collapse (Nov 2022) due to rumours about Alameda's WBTC holdings.
- **Premium tracking:** `wbtc_premium` feature monitors WBTC/BTC price ratio. Exit if premium < -1%.

**cbBTC (Coinbase Wrapped BTC):** Coinbase-issued wrapped BTC on Base and Arbitrum. Newer, lower gas, no BitGo
dependency but Coinbase custodial risk instead.

- **Advantage:** Native to Base L2 (low gas), Coinbase institutional backing.
- **Disadvantage:** Less liquidity than WBTC, fewer DeFi integrations.

## PnL Attribution

| Component           | Settlement Type             | Mechanism                                           |
| ------------------- | --------------------------- | --------------------------------------------------- |
| `funding_pnl`       | `FUNDING_8H` (00/08/16 UTC) | `+notional * funding_rate` (positive when rate > 0) |
| `lending_yield_pnl` | `AAVE_SUPPLY` (per candle)  | Aave supply APY on WBTC (only if stacked variant)   |
| `basis_spread_pnl`  | Mark-to-market              | `abs(perp_size) * (last_premium - current_premium)` |
| `wbtc_premium_pnl`  | Mark-to-market              | WBTC/BTC premium change since entry                 |
| `trading_pnl`       | Entry/exit fills            | Realized price difference on swap + perp close      |
| `transaction_costs` | Per-fill                    | Swap fee + gas + Hyperliquid taker fee              |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

**APY calculation (signal generation only, NOT used for PnL):**

```
basic_apy     = funding_rate * 3 * 365
stacked_apy   = basic_apy + aave_wbtc_supply_apy
Entry: basic_apy >= 5% (or stacked_apy >= 6% if Aave variant)
Exit:  funding goes negative for > 24h OR wbtc_premium < -1%
```

## Risk Profile

| Metric               | Target | Notes                                                  |
| -------------------- | ------ | ------------------------------------------------------ |
| Target annual return | 8-18%  | 5-15% funding + 1-3% Aave supply (if stacked)          |
| Target Sharpe ratio  | 1.5+   | Lower Sharpe than ETH basis due to lower funding rates |
| Max drawdown         | 5%     | WBTC depeg or funding reversal                         |
| Max leverage         | 1x     | No leverage (spot + perp hedge)                        |
| Capital scalability  | $20M   | BTC perp liquidity deeper than ETH on Hyperliquid      |

## Latency Profile

| Segment                     | p50 Target | p99 Target | Co-location Needed?   |
| --------------------------- | ---------- | ---------- | --------------------- |
| Market data --> feature     | 50ms       | 200ms      | No                    |
| Feature --> signal          | 10ms       | 50ms       | No                    |
| Signal --> instruction      | 5ms        | 20ms       | No                    |
| Instruction --> fill (swap) | 2s         | 15s        | No (on-chain)         |
| Instruction --> fill (perp) | 100ms      | 500ms      | No (Hyperliquid CLOB) |
| **End-to-end**              | **~3s**    | **~16s**   | **No**                |

Low-frequency strategy (1h candles). Co-location provides no benefit.

## Execution Details

- **Venues:** Uniswap V3 / Curve (swap via SOR), Aave V3 (optional supply), Hyperliquid (perp)
- **Order types:** Market (swap via SOR with slippage protection), Limit (perp)
- **Atomic execution required?** No -- swap, supply, and perp are independent legs
- **Gas budget:** ~0.003 ETH per rebalance on Ethereum mainnet, ~0.0001 ETH on Arbitrum

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). No rebalance without new signal/market data.

| Level    | Position Deviation | Action         | Notes                                     |
| -------- | ------------------ | -------------- | ----------------------------------------- |
| Minor    | >2% delta drift    | LOG_ONLY       | Log deviation, no action                  |
| Major    | >5% delta drift    | REBALANCE      | Adjust perp size to restore delta-neutral |
| Critical | >10% delta drift   | EMERGENCY_EXIT | Full exit both legs                       |
| WBTC     | premium < -1%      | EMERGENCY_EXIT | WBTC depeg -- exit immediately            |

Delta = `abs(spot_exposure + perp_exposure) / notional`. Target = 0. Thresholds from `defi_base.py:_parse_thresholds()`.
SSOT: [`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions --> exposures) --> RiskMonitor (exposures --> risk assessment) --> Strategy (risk
assessment --> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern               | Exposure Type           | Used For                                  |
| -------------------------------- | ----------------------- | ----------------------------------------- |
| `WALLET:SPOT_ASSET:WBTC`         | Spot value (long)       | Delta calculation                         |
| `AAVE_V3-ETHEREUM:A_TOKEN:AWBTC` | Collateral value (long) | Delta calculation + Aave health (stacked) |
| `HYPERLIQUID:PERPETUAL:*`        | Perp notional (short)   | Delta calculation                         |

Config: `defi_mode.enabled=True`, `ml_mode.track_perp_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type        | Subscribed?       | Threshold                          | Action on Breach    |
| ---------------- | ----------------- | ---------------------------------- | ------------------- |
| `delta`          | YES               | 2% net delta drift                 | Adjust perp size    |
| `funding`        | YES (signal only) | `min_funding_rate` config param    | Entry/exit decision |
| `basis`          | YES (signal only) | `max_basis_deviation` config param | Entry/exit decision |
| `wbtc_premium`   | YES               | WBTC/BTC premium < -1%             | Emergency exit      |
| `venue_protocol` | YES               | Hyperliquid circuit breaker state  | Pause trading       |
| `protocol_risk`  | YES (if stacked)  | Aave HF < 2.0 (WBTC as supply)     | Withdraw from Aave  |
| `liquidity`      | NO                | --                                 | --                  |
| `staking_yield`  | NO                | --                                 | No staking          |
| `borrow_cost`    | NO                | --                                 | No borrowing        |

Config: `enabled_risk_types: ["cex_margin"]`, `defi_risk.enabled=True` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults, not in a machine-readable YAML registry. Plan item
`p5-risk-strategy-subscription` will create `StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk               | What It Measures                              | Evaluation Method  |
| ------------------------- | --------------------------------------------- | ------------------ |
| WBTC depeg risk           | WBTC/BTC price ratio drops below 0.99         | `threshold_breach` |
| WBTC custodial risk       | BitGo operational status (manual monitoring)  | `manual_review`    |
| BTC funding regime shift  | Sustained negative BTC funding > 24h          | `threshold_breach` |
| BTC basis spread blow-out | BTC spot-perp spread exceeds historical norms | `threshold_breach` |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** Hyperliquid cross-margin on perp side; 15% capital allocation to margin
- **Health factor threshold:** N/A for basic variant. For stacked (Aave supply) variant: Aave HF is effectively infinite
  since WBTC is supplied but nothing is borrowed
- **Liquidation risk:** Only on Hyperliquid if margin depleted (extreme basis widening + BTC price spike)
- **WBTC depeg risk:** If WBTC/BTC ratio drops > 1%, long leg loses value while perp tracks BTC -- creates PnL drag
- **Monitoring:** WBTC premium + margin usage checked per candle, alert at >80% margin usage

## Authentication & Credentials

| Venue       | Secret Name                   | Testnet Available?                  | Notes                                   |
| ----------- | ----------------------------- | ----------------------------------- | --------------------------------------- |
| Uniswap V3  | `alchemy-api-key` (RPC)       | Yes (Sepolia)                       | Read: public. Write: wallet private key |
| Aave V3     | `alchemy-api-key` (RPC)       | Yes (Sepolia)                       | Supply WBTC (stacked variant)           |
| Hyperliquid | `hyperliquid-api-credentials` | Yes (`api.hyperliquid-testnet.xyz`) | API key + secret                        |
| Wallet      | `wallet-{client}-private-key` | Yes (dev wallet)                    | Signs swap/supply transactions          |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Hyperliquid account per client (separate margin, 15% capital allocation)
2. Wallet per client (separate WBTC holdings)
3. Config: `initial_capital`, `min_funding_rate`, `max_basis_deviation`, `use_aave_supply` (boolean), `chain`
   (ethereum/arbitrum)
4. **Restart required?** No -- hot-reload via GCS config

### Services requiring per-client configuration

| Service           | What Changes            | Restart?        |
| ----------------- | ----------------------- | --------------- |
| strategy-service  | New config entry in GCS | No (hot-reload) |
| execution-service | New client routing rule | No (hot-reload) |

## UI Visualisation

### Standard views

- PnL waterfall, margin health, position breakdown (from monitoring UI plans)

### Strategy-specific views

- **BTC funding rate vs basis spread overlay** -- time series showing when funding justifies the trade
- **WBTC/BTC premium chart** -- with depeg alert threshold line at -1%
- **Delta drift chart** -- shows how far from delta-neutral over time
- **Funding collection timeline** -- 8h settlement markers with cumulative BTC funding
- **Chain comparison panel** -- Ethereum vs Arbitrum gas costs and WBTC/cbBTC premium comparison
- **Stacked yield decomposition** -- funding + Aave supply APY stacked bar (if stacked variant)

## Testing Stage Status

| Stage        | Status  | Notes                                                     |
| ------------ | ------- | --------------------------------------------------------- |
| MOCK         | Pending | Need MockDeFiDynamics with BTC funding rate oscillation   |
| HISTORICAL   | Pending | Need Hyperliquid BTC funding rate history from Tardis.dev |
| LIVE_MOCK    | Pending | Blocked by BTC feature computation                        |
| LIVE_TESTNET | Pending | Blocked by Hyperliquid testnet BTC-USDC perp availability |
| BATCH_REAL   | Pending | Blocked by historical BTC APY storage                     |
| STAGING      | Pending | Tenderly fork + Hyperliquid testnet                       |
| LIVE_REAL    | Pending | All above + real capital approval                         |

## Wallet & Capital Flow

| Component        | Value                                                                   |
| ---------------- | ----------------------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                              |
| Hot wallet       | Per-chain, per-strategy isolated                                        |
| CeFi sub-account | Yes (Hyperliquid -- perp margin)                                        |
| Bridge required  | No (single-chain for spot leg; Arbitrum variant uses same-chain wallet) |
| Custody          | Copper MPC                                                              |

Capital flow: Client deposit --> treasury --> hot wallet --> SWAP to WBTC (spot leg) + TRANSFER USDC to Hyperliquid
(margin). Optional stacked variant adds SUPPLY WBTC to Aave V3 for additional yield. Rebalance: treasury < 10% -->
strategy reduces position --> close perp + SWAP WBTC back --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM). The MTDS `gas_fee_handler` fetches
real-time gas prices and writes them as features consumed by the strategy. Gas hits P&L immediately as a realized
transaction cost -- not estimated. For Ethereum mainnet: ~$15-25 per swap. For Arbitrum: ~$0.10-0.25 per swap. The
Hyperliquid perp leg has zero gas cost (off-chain CLOB).

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). DEX
pools (swap leg) require BOTH sides to be in `DEFI_MAJOR_ASSET_SYMBOLS`. Both WBTC and CBBTC are in the BTC family
within the whitelist. Perps use the CeFi base asset universe.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_btc_basis.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md` -- DeFi BTC Basis
- **Execution adapter (swap):** `execution-service/protocols/uniswap.py`
- **Execution adapter (perp):** `execution-service/protocols/hyperliquid.py`
- **Execution adapter (Aave):** `execution-service/protocols/aave.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
