---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# DeFi Basis Trade

> **Asset class:** DeFi **Strategy type:** Basis (delta-neutral funding rate arbitrage) **Strategy IDs:**
> `DEFI_ETH_BASIS_HYPER_SCE_1H` (single-coin ETH basis, original) / `DEFI_MULTI_BASIS_HUF_1H_V1` (multi-coin multi-venue
> basis, current default)
>
> The multi-coin variant (`DEFI_MULTI_BASIS_HUF_1H_V1`) supersedes the single-coin for production use. The single-coin
> ID is still used for testing and client configs with `fixed_basis_coin`.

## Overview

Long spot ETH + short ETH perpetual on Hyperliquid. Delta-neutral: collects funding rate when perps trade at a premium
to spot. The simplest DeFi strategy — no staking, no lending, no flash loans.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDT  (100% USDT)

Step 1 - SWAP:     USDT --> ETH          (90% of capital, via Uniswap/Curve SOR)
Step 2 - TRANSFER: USDT --> USDC         (10% to Hyperliquid as margin)
Step 3 - TRADE:    Short ETH-USDC perp   (size = ETH amount from step 1)

Wallet after deploy:
  - WALLET:SPOT_ASSET:ETH              = eth_amount  (long)
  - HYPERLIQUID:PERPETUAL:ETH-USDC     = -eth_amount (short)
  - HYPERLIQUID margin                 = 10% USDC

Net delta = 0 (long spot + short perp cancel)
```

## Instruments

| Instrument Key                                   | Venue       | Type | Role              |
| ------------------------------------------------ | ----------- | ---- | ----------------- |
| `WALLET:SPOT_ASSET:USDT`                         | Wallet      | Spot | Initial capital   |
| `WALLET:SPOT_ASSET:ETH`                          | Wallet      | Spot | Long leg          |
| `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` | Hyperliquid | Perp | Short leg (hedge) |

## Key Features Consumed

| Feature        | Source Service     | SLA | Used For                               |
| -------------- | ------------------ | --- | -------------------------------------- |
| `funding_rate` | features-delta-one | 10s | Signal: entry when funding > threshold |
| `eth_price`    | market-tick-data   | 1s  | Position sizing, PnL                   |
| `basis_bps`    | features-delta-one | 10s | Spread monitoring                      |

## Data Architecture

| Dimension              | Value                                                        | SSOT                                |
| ---------------------- | ------------------------------------------------------------ | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)    | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: `eth_price`, `funding_rate`              | Features hydrated alongside candles |
| **Features**           | `features` dict: `funding_rate`, `basis_bps`                 | `features-delta-one-service`        |
| **Interval**           | Time-driven (candle-based), not event-driven                 | `timeframe` in strategy config      |
| **Lowest granularity** | 1H (currently hardcoded in factory, not configurable)        | `defi_basis.py` factory             |
| **Execution mode**     | `same_candle_exit` — entry and exit can occur in same candle | Strategy config                     |

**Gap:** Timeframe is hardcoded to 1H. Should be configurable via strategy config to support 15m/4H/1D.

## Instrument Selection

**Currently: STATIC (hardcoded per config, no dynamic selection)**

Instruments are set at strategy initialisation and never change:

- Spot: `WALLET:SPOT_ASSET:ETH` — always ETH
- Perp: `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` — always ETH-USDC on Hyperliquid

There is **no instrument SOR** — the strategy does NOT dynamically pick BTC vs ETH vs SOL perps based on which has the
best funding rate. This is a gap: an "instrument selection" layer could scan all perp instruments and pick the one with
the highest funding rate above threshold.

**This is different from execution SOR**, which picks the best DEX venue for the same instrument.

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON by default for the swap leg only.**

| Leg                    | SOR? | Allowed Venues                                          | SSOT                 |
| ---------------------- | ---- | ------------------------------------------------------- | -------------------- |
| Step 1 (USDT→ETH swap) | YES  | `UNISWAP_V3-ETHEREUM`, `CURVE-ETHEREUM`, `BALANCER-ETH` | `defi_base.py:84-86` |
| Step 3 (Short perp)    | NO   | Hyperliquid only (CLOB, no alternative)                 | —                    |

SOR picks the best price across DEX venues for the same ERC-20 token on the same chain. The `allowed_venues` list is
passed in `StrategyInstruction` to execution-service, which handles the actual routing. Strategy-service does NOT pick
the venue — it provides the allowed set.

**Same-wallet constraint:** All SOR venues must be on the same blockchain (Ethereum mainnet). SSOT:
[`SHARED_WALLET_GROUPS`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

**Execution boundary:** Strategy sends `StrategyInstruction` with `allowed_venues` and `max_slippage_bps`.
Execution-service converts to `ExecutionInstruction`, picks venue, chooses order type (MARKET/LIMIT/TWAP), executes, and
measures alpha vs benchmark.

## PnL Attribution

| Component           | Settlement Type             | Mechanism                                           |
| ------------------- | --------------------------- | --------------------------------------------------- |
| `funding_pnl`       | `FUNDING_8H` (00/08/16 UTC) | `+notional * funding_rate` (positive when rate > 0) |
| `basis_spread_pnl`  | Mark-to-market              | `abs(perp_size) * (last_premium - current_premium)` |
| `trading_pnl`       | Entry/exit fills            | Realized price difference on swap + perp close      |
| `transaction_costs` | Per-fill                    | Swap fee + gas + Hyperliquid taker fee              |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based).

## Risk Profile

| Metric               | Target | Notes                                             |
| -------------------- | ------ | ------------------------------------------------- |
| Target annual return | 8-15%  | Depends on funding rate regime                    |
| Target Sharpe ratio  | 2.0+   | High Sharpe due to delta neutrality               |
| Max drawdown         | 5%     | Primarily from basis spread widening              |
| Max leverage         | 1x     | No leverage (spot + perp hedge)                   |
| Capital scalability  | $5M    | Above this, Hyperliquid funding rate impact grows |

## Latency Profile

| Segment                   | p50 Target | p99 Target | Co-location Needed?   |
| ------------------------- | ---------- | ---------- | --------------------- |
| Market data → feature     | 50ms       | 200ms      | No                    |
| Feature → signal          | 10ms       | 50ms       | No                    |
| Signal → instruction      | 5ms        | 20ms       | No                    |
| Instruction → fill (swap) | 2s         | 15s        | No (on-chain)         |
| Instruction → fill (perp) | 100ms      | 500ms      | No (Hyperliquid CLOB) |
| **End-to-end**            | **~3s**    | **~16s**   | **No**                |

This is a low-frequency strategy (1h candles). Co-location provides no benefit.

## Execution Details

- **Venues:** Uniswap V3 (swap), Hyperliquid (perp)
- **Order types:** Market (swap via SOR), Limit (perp)
- **Atomic execution required?** No — legs are independent
- **Gas budget:** ~200k gas for swap, 0 gas for Hyperliquid (off-chain CLOB)

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). No rebalance without new signal/market data.

| Level    | Position Deviation | Action         | Notes                                     |
| -------- | ------------------ | -------------- | ----------------------------------------- |
| Minor    | >2% delta drift    | LOG_ONLY       | Log deviation, no action                  |
| Major    | >5% delta drift    | REBALANCE      | Adjust perp size to restore delta-neutral |
| Critical | >10% delta drift   | EMERGENCY_EXIT | Full exit both legs                       |

Delta = `abs(spot_exposure + perp_exposure) / notional`. Target = 0. Thresholds from `defi_base.py:_parse_thresholds()`.
SSOT: [`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions → exposures) → RiskMonitor (exposures → risk assessment) → Strategy (risk
assessment → rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern        | Exposure Type         | Used For          |
| ------------------------- | --------------------- | ----------------- |
| `WALLET:SPOT_ASSET:ETH`   | Spot value (long)     | Delta calculation |
| `HYPERLIQUID:PERPETUAL:*` | Perp notional (short) | Delta calculation |

Config: `defi_mode.enabled=True`, `ml_mode.track_perp_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type        | Subscribed?       | Threshold                          | Action on Breach    |
| ---------------- | ----------------- | ---------------------------------- | ------------------- |
| `delta`          | YES               | 2% net delta drift                 | Adjust perp size    |
| `funding`        | YES (signal only) | `min_funding_rate` config param    | Entry/exit decision |
| `basis`          | YES (signal only) | `max_basis_deviation` config param | Entry/exit decision |
| `venue_protocol` | YES               | Hyperliquid circuit breaker state  | Pause trading       |
| `liquidity`      | NO                | —                                  | —                   |
| `protocol_risk`  | NO                | —                                  | No Aave positions   |
| `staking_yield`  | NO                | —                                  | No staking          |
| `borrow_cost`    | NO                | —                                  | No borrowing        |

Config: `enabled_risk_types: ["cex_margin"]`, `defi_risk.enabled=False`, `cex_risk.enabled=True` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults, not in a machine-readable YAML registry. Plan item
`p5-risk-strategy-subscription` will create `StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk               | What It Measures                                   | Evaluation Method  |
| ------------------------- | -------------------------------------------------- | ------------------ |
| Funding rate regime shift | Sustained negative funding → strategy unprofitable | `threshold_breach` |
| Basis spread blow-out     | Spot-perp spread exceeds historical norms          | `threshold_breach` |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** Hyperliquid cross-margin on perp side
- **Health factor threshold:** N/A (no Aave positions)
- **Liquidation risk:** Only on Hyperliquid if margin depleted (extreme basis widening)
- **Monitoring:** Margin usage checked per candle, alert at >80%

## Authentication & Credentials

| Venue       | Secret Name                   | Testnet Available?                  | Notes                                   |
| ----------- | ----------------------------- | ----------------------------------- | --------------------------------------- |
| Uniswap V3  | `alchemy-api-key` (RPC)       | Yes (Sepolia)                       | Read: public. Write: wallet private key |
| Hyperliquid | `hyperliquid-api-credentials` | Yes (`api.hyperliquid-testnet.xyz`) | API key + secret                        |
| Wallet      | `wallet-{client}-private-key` | Yes (dev wallet)                    | Signs swap transactions                 |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Hyperliquid account per client (separate margin)
2. Wallet per client (separate ETH holdings)
3. Config: `initial_capital`, `min_funding_rate`, `max_basis_deviation`
4. **Restart required?** No — hot-reload via GCS config

## UI Visualisation

### Standard views

- PnL waterfall, margin health, position breakdown (from monitoring UI plans)

### Strategy-specific views

- **Funding rate vs basis spread overlay** — time series showing when funding justifies the spread
- **Delta drift chart** — shows how far from delta-neutral over time
- **Funding collection timeline** — 8h settlement markers with cumulative funding

## Testing Stage Status

| Stage        | Status  | Notes                                                 |
| ------------ | ------- | ----------------------------------------------------- |
| MOCK         | Pending | Need MockDeFiDynamics with funding rate oscillation   |
| HISTORICAL   | Pending | Need Hyperliquid funding rate history from Tardis.dev |
| LIVE_MOCK    | Pending | Blocked by feature computation (#6)                   |
| LIVE_TESTNET | Pending | Blocked by Hyperliquid testnet integration            |
| BATCH_REAL   | Pending | Blocked by historical APY storage (#4)                |
| STAGING      | Pending | Tenderly fork + Hyperliquid testnet                   |
| LIVE_REAL    | Pending | All above + real capital approval                     |

## Wallet & Capital Flow

| Component        | Value                            |
| ---------------- | -------------------------------- |
| Treasury reserve | 20% of AUM                       |
| Hot wallet       | Per-chain, per-strategy isolated |
| CeFi sub-account | Yes (Hyperliquid -- perp margin) |
| Bridge required  | No (single-chain for spot leg)   |
| Custody          | Copper MPC                       |

Capital flow: Client deposit --> treasury --> hot wallet --> SWAP to ETH (spot leg) + TRANSFER USDC to Hyperliquid
(margin). Rebalance: treasury < 10% --> strategy reduces position --> close perp + SWAP ETH back --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM). The MTDS `gas_fee_handler` fetches
real-time gas prices and writes them as features consumed by the strategy. Gas hits P&L immediately as a realized
transaction cost -- not estimated. For the swap leg on Ethereum mainnet, gas is ~$15-25 per rebalance at 30 gwei. The
Hyperliquid perp leg has zero gas cost (off-chain CLOB).

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). DEX
pools (swap leg) require BOTH sides to be in `DEFI_MAJOR_ASSET_SYMBOLS`. Perps use the CeFi base asset universe
(`hyperliquid_aster_mvp_base_assets`, 21 coins).

## Underlying Families / Basis Coins

The `basis_coins` config parameter defines which coins the strategy can deploy on. This is a **two-waterfall weighting**
system: coins are ranked by funding rate magnitude, and capital is allocated proportionally to the top N coins that pass
the minimum funding rate threshold. Currently deployed on ETH only, but the config supports multi-coin expansion.

- **Tier 1 (highest weight):** ETH -- deepest perp liquidity, most stable funding
- **Tier 2:** BTC, SOL -- strong funding rates, good perp depth

The basis_coins list is a **fixed** strategy config parameter from UAC registry -- it is NOT gridded. Other parameters
(funding rate thresholds, delta drift tolerances, rebalance frequency) are gridded around it.

## E2E Manual Trading Workflow

Step-by-step manual recreation of the multi-venue basis trade. Spot leg on-chain (DEX), perp legs on CeFi venues.

### Prerequisites

- Treasury wallet funded with USDC on Ethereum
- CeFi venue accounts (Hyperliquid, Binance, OKX, Bybit, Aster) with API keys
- Trading wallet created

### Step-by-Step

| Step | Action                                              | Instruction Type | Service                                 | Instant P&L                         |
| ---- | --------------------------------------------------- | ---------------- | --------------------------------------- | ----------------------------------- |
| 1    | Observe treasury balance                            | —                | position-balance-monitor                | —                                   |
| 2    | Transfer $100K USDC treasury → trading wallet       | TRANSFER         | execution-service                       | Gas: ~$2                            |
| 3    | Swap $90K USDC → ETH (SOR picks best DEX)           | SWAP             | execution-service (SOR → Uniswap/Curve) | Gas: ~$15. Slippage: ~5 bps ($4.50) |
| 4    | Transfer $2K USDC margin → Hyperliquid              | TRANSFER         | execution-service                       | Gas: ~$0 (off-chain)                |
| 5    | Transfer $2K USDC margin → Binance                  | TRANSFER         | execution-service                       | Gas: ~$0 (exchange internal)        |
| 6    | Transfer $2K USDC margin → OKX                      | TRANSFER         | execution-service                       | Gas: ~$0                            |
| 7    | Transfer $2K USDC margin → Bybit                    | TRANSFER         | execution-service                       | Gas: ~$0                            |
| 8    | Transfer $2K USDC margin → Aster                    | TRANSFER         | execution-service                       | Gas: ~$0                            |
| 9    | SHORT ETH perp on Hyperliquid (weighted by funding) | TRADE            | execution-service (API)                 | Trading fee: ~3-8 bps               |
| 10   | SHORT ETH perp on Binance (weighted)                | TRADE            | execution-service                       | Trading fee: ~3-8 bps               |
| 11   | SHORT ETH perp on OKX (weighted)                    | TRADE            | execution-service                       | Trading fee: ~3-8 bps               |
| 12   | SHORT ETH perp on Bybit (weighted)                  | TRADE            | execution-service                       | Trading fee: ~3-8 bps               |
| 13   | SHORT ETH perp on Aster (weighted)                  | TRADE            | execution-service                       | Trading fee: ~3-8 bps               |

### Two-Waterfall Weighting (Decision Logic)

Strategy determines allocation via:

1. **Pillar 1 (Coin weight)**: avg funding rate per coin across venues. Min 2.5% annualized.
2. **Pillar 2 (Venue weight)**: per-venue funding rate for that coin. Max 50% per venue.

### Position State After Deployment

- Trading wallet: ~30 ETH LONG (spot)
- Hyperliquid: ~8 ETH SHORT (30% weight at 6.5% funding)
- Binance: ~8 ETH SHORT (25% weight at 5.8% funding)
- OKX: ~6 ETH SHORT (20% weight at 5.2% funding)
- Bybit: ~5 ETH SHORT (15% weight at 4.8% funding)
- Aster: ~3 ETH SHORT (10% weight at 4.2% funding)
- Net delta: ~0 (market neutral)

### Instant P&L

- Swap slippage: ~$4.50 (5 bps on $90K)
- Gas (swap): ~$15
- Trading fees (5 perp trades): ~$27 (avg 6 bps on $90K total)
- Total entry cost: ~$46.50

### Ongoing P&L (Daily)

- Funding income: weighted average ~5.5% APY on $90K notional = ~$13.56/day
- Cost recovery: ~3.4 days

### Risk Metrics

- Net delta: 0 (±2% tolerance before rebalance)
- Venue concentration: max 50% per venue
- Liquidation risk: per-venue margin requirements
- Funding rate risk: if all venues go negative, strategy exits

### Exit Workflow

| Step | Action                                  | Instruction Type |
| ---- | --------------------------------------- | ---------------- |
| 1    | Close all perp SHORTs (buy to close)    | TRADE × 5 venues |
| 2    | Swap ETH → USDC                         | SWAP             |
| 3    | Withdraw margin from each CeFi venue    | TRANSFER × 5     |
| 4    | Transfer USDC trading wallet → treasury | TRANSFER         |

### Trade History (Expected Output)

| #   | Time  | Type     | Venue       | Amount       | Gas | Slippage | Fee   | Running P&L |
| --- | ----- | -------- | ----------- | ------------ | --- | -------- | ----- | ----------- |
| 1   | 10:01 | TRANSFER | WALLET      | 100,000 USDC | $2  | —        | —     | -$2         |
| 2   | 10:02 | SWAP     | Uniswap V3  | 30 ETH       | $15 | -$4.50   | —     | -$21.50     |
| 3   | 10:03 | TRANSFER | Hyperliquid | 2,000 USDC   | $0  | —        | —     | -$21.50     |
| 4   | 10:03 | TRADE    | Hyperliquid | -8 ETH SHORT | $0  | —        | $5.40 | -$26.90     |
| ... | ...   | ...      | ...         | ...          | ... | ...      | ...   | ...         |
| EOD | —     | FUNDING  | All venues  | +$13.56      | $0  | —        | —     | -$32.94     |

## Share Class

The basis trade supports multiple share classes via `ShareClassMixin`. The share class determines the base currency
denomination of P&L and the delta neutrality target.

| Share Class | Target Delta             | P&L Currency | Notes                                                                                     |
| ----------- | ------------------------ | ------------ | ----------------------------------------------------------------------------------------- |
| `USDT`      | 0 (fully market neutral) | USD          | Default. Long spot + short perp cancel completely.                                        |
| `ETH`       | total_equity_in_eth      | ETH          | Crypto exposure matches portfolio. Perp hedge only offsets the basis spread, not the ETH. |
| `BTC`       | total_equity_in_btc      | BTC          | Same pattern as ETH. Used for BTC-denominated clients.                                    |

For `USDT` share class, delta neutrality means zero net market exposure -- the strategy is purely a funding rate
harvester. For `ETH` share class, delta neutrality means the portfolio's ETH-denominated value is stable -- the perp
hedge removes basis risk but preserves the ETH exposure. The FX factor (USD/ETH conversion) is separated from trading
P&L in attribution.

Rebalancing thresholds apply to the delta deviation from the share-class-specific target, not from zero. For `ETH` share
class, `|current_delta - total_equity_in_eth| / notional > threshold` triggers rebalance.

See [cross-cutting/share-classes.md](../cross-cutting/share-classes.md) for the full cross-strategy specification.

## Client Config Overrides

Client-specific configuration is supported via per-client GCS config overlays. Key override patterns:

| Override                  | Example (Patrick config)      | Notes                                                                    |
| ------------------------- | ----------------------------- | ------------------------------------------------------------------------ |
| `allowed_perp_venues`     | `["OKX", "BYBIT", "BINANCE"]` | Restricts perp venues. Default: all 5 (+ Hyperliquid, Aster).            |
| `fixed_basis_coin`        | `"ETH"`                       | Locks to single coin. Disables multi-coin waterfall.                     |
| `venue_weighting`         | `"EQUAL"`                     | Equal weight across allowed venues instead of funding-rate-proportional. |
| `share_class`             | `"USDT"`                      | Base currency denomination.                                              |
| `min_funding_rate_annual` | `0.025`                       | Minimum annualized funding rate for entry (default 2.5%).                |

When `fixed_basis_coin` is set, Pillar 1 of the two-waterfall weighting is skipped entirely -- the strategy deploys only
on the specified coin. When `venue_weighting="EQUAL"`, Pillar 2 assigns equal weight to all allowed venues instead of
weighting by per-venue funding rate.

## Two-Waterfall Weighting (Detail)

Capital allocation uses a two-pillar waterfall system:

**Pillar 1 -- Coin-Level Weights (across coins):**

1. For each coin in `basis_coins`, compute `avg_funding_rate` as the weighted average funding rate across all allowed
   perp venues for that coin.
2. Filter: coins with `avg_funding_rate < 2.5%` annualized are excluded (floor configurable via
   `min_funding_rate_annual`).
3. Weight: remaining coins weighted proportionally to their `avg_funding_rate`. Example: ETH at 6% and SOL at 4% yield
   weights 60%/40%.

**Pillar 2 -- Venue Weights (within each coin):**

1. For each coin's allocation, distribute across allowed perp venues by per-venue funding rate for that coin.
2. Max 50% per venue (configurable via `max_venue_concentration`).
3. Venues with funding rate below 1% annualized are excluded from that coin's allocation.

The two-waterfall ensures diversification across both coins and venues. The strategy re-evaluates weights on each signal
candle and rebalances only if the benefit exceeds cost (see Rebalance Cost-Benefit below).

## Rebalance Cost-Benefit

Rebalancing is gated by a cost-benefit check. The strategy only rebalances when:

```
expected_benefit > rebalance_cost * 1.5
```

Where:

- `expected_benefit` = incremental funding income from improved allocation over the rebalance horizon (default: 7 days)
- `rebalance_cost` = gas fees (swap leg) + slippage (30 bps estimated for swaps) + exchange fees (5 bps for perp trades)

This prevents churn when funding rates shift marginally. The 1.5x multiplier is configurable via
`rebalance_cost_multiplier` in strategy config. Higher values make the strategy more conservative about rebalancing.

## Venue Collateral

Each venue accepts specific collateral tokens. The strategy must ensure margin is posted in the correct token before
opening perp positions.

| Venue       | Accepted Collateral | Pre-Processing Required                       |
| ----------- | ------------------- | --------------------------------------------- |
| Hyperliquid | USDC only           | USDT must be swapped to USDC before transfer. |
| Binance     | USDT, BTC, ETH      | No swap needed for USDT margin.               |
| OKX         | USDT, BTC, ETH      | No swap needed for USDT margin.               |
| Bybit       | USDT, BTC, ETH      | No swap needed for USDT margin.               |
| Aster       | USDT, BTC, ETH      | No swap needed for USDT margin.               |

For Hyperliquid, the strategy automatically emits a SWAP instruction (USDT to USDC) before the TRANSFER instruction.
This is handled by the `CollateralValidationMixin` which checks venue collateral requirements before instruction
emission.

See [cross-cutting/venue-collateral-and-wrapping.md](../cross-cutting/venue-collateral-and-wrapping.md) for the full
collateral matrix.

## Enhanced Basis Trade (Cross-Venue, Cross-Coin, LST Collateral, Bidirectional)

> **Strategy IDs:** `DEFI_ENHANCED_BASIS_MULTI_VENUE_HUF_1H_V1` / `DEFI_ENHANCED_BASIS_MULTI_COIN_HUF_1H_V1`
>
> **Implementation:** `strategy-service/strategy_service/engine/strategies/enhanced_basis.py`
>
> The enhanced variant extends `BasisTradeStrategy` with four capabilities below.

### Cross-Venue Basket

For the same coin (e.g. ETH), the strategy distributes the perp short across multiple venues (Hyperliquid, Binance, OKX,
Bybit, Aster) weighted by per-venue funding rate. Venues are additionally filtered by orderbook depth — any venue below
`min_venue_depth_usd` (default $100K) is excluded.

**Config:**

| Parameter                    | Default            | Description                                      |
| ---------------------------- | ------------------ | ------------------------------------------------ |
| `perp_venues`                | 5 venues           | List of eligible perp venues                     |
| `min_venue_depth_usd`        | 100000             | Minimum orderbook depth (USD) to include venue   |
| `venue_depth_feature_prefix` | `orderbook_depth_` | Feature key prefix for depth data per coin/venue |

Depth features are consumed as `orderbook_depth_{coin}_{venue}` from features-delta-one-service. When no depth data is
available, all venues pass (graceful degradation).

### Cross-Coin Basket

The strategy ranks all coins in `basis_coins` by absolute funding rate magnitude, selects the top N (configured via
`max_basket_size`), and allocates capital using the existing two-waterfall weighting system (Pillar 1: coin weights,
Pillar 2: venue weights within each coin).

**Config:**

| Parameter                      | Default | Description                                           |
| ------------------------------ | ------- | ----------------------------------------------------- |
| `basis_coins`                  | 7 coins | Candidate coins: ETH, BTC, SOL, AVAX, DOGE, LINK, ADA |
| `max_basket_size`              | 5       | Maximum number of coins in the basket                 |
| `min_funding_threshold_annual` | 0.025   | Minimum annualized funding rate to include a coin     |

### LST Collateral Decision Tree

For each (coin, venue) pair, the strategy evaluates whether to:

1. **Stake spot into LST, then post LST as collateral** (higher capital efficiency at some venues)
2. **Post base asset directly as margin** (simpler, no staking gas cost)

The decision mirrors execution-service's `LSTCollateralResolver.resolve_collateral_path()` logic: if
`lst_collateral_factor > 1/leverage`, the LST path is more capital-efficient.

**Decision flow:**

```
For each (coin, venue):
  1. Look up LST acceptance at venue (e.g. Bybit accepts wstETH at 0.90 factor)
  2. Compute direct margin efficiency = 1/leverage (e.g. 0.20 at 5x)
  3. If LST factor > direct efficiency:
     → Emit SWAP (coin → LST) + TRANSFER (LST as collateral)
     → Instruction metadata: collateral_path=LST, lst_token, staking_apy
  4. Else:
     → Emit TRANSFER (USDC as margin)
     → Instruction metadata: collateral_path=DIRECT
```

**Supported LST paths:**

| Base Coin | LST Options                     | Best Venue Factor   |
| --------- | ------------------------------- | ------------------- |
| ETH       | wstETH (Lido), weETH (EtherFi)  | 0.95 (Hyperliquid)  |
| SOL       | mSOL (Marinade), jitoSOL (Jito) | 0.85 (Drift/Kamino) |

The strategy only makes the collateral _decision_ and annotates instruction metadata. Execution-service performs the
actual staking via `LSTCollateralResolver`.

**Config:**

| Parameter                | Default | Description                                           |
| ------------------------ | ------- | ----------------------------------------------------- |
| `lst_collateral_enabled` | true    | Enable LST collateral path evaluation                 |
| `lst_leverage`           | 5       | Leverage assumption for direct margin efficiency calc |

### Bidirectional Funding

When the funding rate is negative, the strategy inverts the trade: **short spot + long perp** (inverse basis). This
captures the funding payment that flows from shorts to longs when perps trade at a discount to spot.

**Direction logic:**

| Funding Rate | Spot Leg   | Perp Leg   | Funding Flow               |
| ------------ | ---------- | ---------- | -------------------------- |
| Positive     | LONG spot  | SHORT perp | Longs pay shorts (collect) |
| Negative     | SHORT spot | LONG perp  | Shorts pay longs (collect) |

The direction is determined per-coin based on the sign of the best funding rate. Coins with positive funding use
standard basis; coins with negative funding use inverse basis. Both can coexist in the same basket.

**Config:**

| Parameter                  | Default | Description                                      |
| -------------------------- | ------- | ------------------------------------------------ |
| `bidirectional_funding`    | true    | Enable inverse basis for negative funding        |
| `inverse_min_funding_rate` | -0.0001 | Minimum negative rate (per 8h) for inverse entry |
| `inverse_max_funding_rate` | -0.005  | Maximum negative rate cap (runaway protection)   |

### Factory Functions

| Factory                                     | Strategy Type                | Focus                        |
| ------------------------------------------- | ---------------------------- | ---------------------------- |
| `create_basis_trade_multi_venue_strategy()` | `ENHANCED_BASIS_MULTI_VENUE` | Single coin, venue diversity |
| `create_basis_trade_multi_coin_strategy()`  | `ENHANCED_BASIS_MULTI_COIN`  | Multi-coin basket            |

### Config Files

- `configs/basis_trade_multi_venue.yaml` — cross-venue focus (single coin)
- `configs/basis_trade_multi_coin.yaml` — cross-coin focus (up to 5 coins)

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_basis.py`
- **Enhanced implementation:** `strategy-service/strategy_service/engine/strategies/enhanced_basis.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md` § DeFi Basis
- **Execution adapter:** `execution-service/protocols/uniswap.py` + `hyperliquid.py`
- **LST Collateral Resolver:** `execution-service/execution_service/services/lst_collateral_resolver.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
