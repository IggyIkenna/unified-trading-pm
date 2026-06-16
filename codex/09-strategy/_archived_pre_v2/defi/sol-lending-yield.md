---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Solana Lending Yield (Kamino Finance)

> **Asset class:** DeFi **Strategy type:** Yield (lending + optional leverage) **Strategy ID pattern:**
> `DEFI_SOL_LENDING_KAMINO_4H`

## Overview

Supply USDC, SOL, or USDT to Kamino Finance lending reserves on Solana to earn 5-15% APY (higher than Aave on Ethereum
due to less competition and higher Solana DeFi activity). Can be combined with recursive borrowing for leverage: deposit
SOL, borrow USDC, deposit USDC again, amplifying yield to 15-25% APY at the cost of liquidation risk. Health factor
monitoring mirrors the Aave lending strategy pattern.

## Token / Position Flow

```
=== UNLEVERAGED MODE (default) ===

Start:  WALLET:SPOT_ASSET:USDC  (100% USDC)

Step 1 - DEPOSIT:  USDC --> Kamino reserve    (100% of capital)
         Receive:  kUSDC receipt tokens

Wallet after deploy:
  - KAMINO-SOLANA:A_TOKEN:KUSDC          = kusdc_amount  (earning supply APY)

=== LEVERAGED MODE (optional, 2x target leverage) ===

Start:  WALLET:SPOT_ASSET:USDC  (100% USDC)

Step 1 - SWAP:     USDC --> SOL              (100% of capital, via Jupiter)
Step 2 - DEPOSIT:  SOL --> Kamino reserve     (collateral)
         Receive:  kSOL receipt tokens
Step 3 - BORROW:   USDC from Kamino          (50% LTV = borrow up to 50% of SOL collateral value)
Step 4 - DEPOSIT:  USDC --> Kamino reserve    (re-deposit borrowed USDC for additional yield)
         Receive:  kUSDC receipt tokens

Wallet after deploy:
  - KAMINO-SOLANA:A_TOKEN:KSOL           = ksol_amount   (collateral, earning SOL supply APY)
  - KAMINO-SOLANA:A_TOKEN:KUSDC          = kusdc_amount  (earning USDC supply APY)
  - KAMINO-SOLANA:DEBT_TOKEN:BORROWUSDC  = usdc_debt     (debt, paying borrow APY)

Health Factor = (SOL_collateral_value * liquidation_threshold) / debt_value
Target HF = 2.0 (conservative), minimum 1.5, emergency exit at 1.2
```

## Instruments

| Instrument Key                        | Venue  | Type   | Role                          |
| ------------------------------------- | ------ | ------ | ----------------------------- |
| `WALLET:SPOT_ASSET:USDC`              | Wallet | Spot   | Initial capital               |
| `WALLET:SPOT_ASSET:SOL`               | Wallet | Spot   | Intermediate (leveraged mode) |
| `KAMINO-SOLANA:A_TOKEN:KUSDC`         | Kamino | Supply | USDC supply position          |
| `KAMINO-SOLANA:A_TOKEN:KSOL`          | Kamino | Supply | SOL collateral (leveraged)    |
| `KAMINO-SOLANA:DEBT_TOKEN:BORROWUSDC` | Kamino | Debt   | USDC borrow (leveraged)       |

## Key Features Consumed

| Feature              | Source Service   | SLA | Used For                                       |
| -------------------- | ---------------- | --- | ---------------------------------------------- |
| `kamino_supply_apy`  | features-onchain | 60s | Signal: entry when supply APY > threshold      |
| `kamino_borrow_apy`  | features-onchain | 60s | Leveraged mode: net yield calculation          |
| `kamino_utilization` | features-onchain | 60s | Risk: high utilization = withdrawal difficulty |
| `sol_price`          | market-tick-data | 1s  | HF calculation, position sizing (leveraged)    |
| `health_factor`      | features-onchain | 30s | Leveraged mode: liquidation risk monitoring    |

## Data Architecture

| Dimension              | Value                                                                                            | SSOT                                |
| ---------------------- | ------------------------------------------------------------------------------------------------ | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                                        | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: `sol_price`, `kamino_supply_apy`, `kamino_borrow_apy`, `health_factor`       | Features hydrated alongside candles |
| **Features**           | `features` dict: `kamino_supply_apy`, `kamino_borrow_apy`, `kamino_utilization`, `health_factor` | `features-onchain-service`          |
| **Interval**           | Time-driven (candle-based), not event-driven                                                     | `timeframe` in strategy config      |
| **Lowest granularity** | 4H (configurable via strategy config)                                                            | `defi_sol_lending.py` factory       |
| **Execution mode**     | `same_candle_exit` -- entry and exit can occur in same candle                                    | Strategy config                     |

## Instrument Selection

**Currently: STATIC (hardcoded per config, no dynamic selection)**

Instruments are set at strategy initialisation and never change:

- Supply: `KAMINO-SOLANA:A_TOKEN:KUSDC` (unleveraged) or `KAMINO-SOLANA:A_TOKEN:KSOL` + `KUSDC` (leveraged)
- Borrow: `KAMINO-SOLANA:DEBT_TOKEN:BORROWUSDC` (leveraged mode only)

There is **no dynamic asset selection** -- the strategy does NOT compare USDC vs SOL vs USDT supply rates and pick the
best one. This is a gap: an "asset SOR" could select the reserve with the highest net yield (supply APY - borrow APY if
leveraged) that meets liquidity thresholds.

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON only for the initial swap (leveraged mode).**

| Leg                         | SOR? | Allowed Venues                 | SSOT                         |
| --------------------------- | ---- | ------------------------------ | ---------------------------- |
| Step 1 (USDC->SOL swap)     | YES  | `JUPITER-SOLANA` (aggregator)  | `defi_sol_lending.py:swap()` |
| Step 2 (Deposit to Kamino)  | NO   | Kamino only (direct lending)   | --                           |
| Step 3 (Borrow from Kamino) | NO   | Kamino only (direct borrowing) | --                           |

Jupiter handles multi-venue routing natively. Kamino lending/borrowing is direct -- no SOR needed.

**Same-wallet constraint:** All Solana operations use the same wallet. SSOT:
[`SHARED_WALLET_GROUPS`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## PnL Attribution

| Component           | Settlement Type  | Mechanism                                                       |
| ------------------- | ---------------- | --------------------------------------------------------------- |
| `supply_yield_pnl`  | `LENDING_YIELD`  | kToken exchange rate appreciation (supply APY accrual)          |
| `borrow_cost_pnl`   | `BORROW_COST`    | Debt growth from borrow APY (negative PnL, leveraged mode only) |
| `price_pnl`         | Mark-to-market   | SOL price change affecting collateral value (leveraged mode)    |
| `trading_pnl`       | Entry/exit fills | Price difference on Jupiter swaps                               |
| `transaction_costs` | Per-fill         | Jupiter swap fee + Solana gas (~0.001 SOL per tx)               |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). For leveraged mode:
`equity = collateral_value + supply_value - debt_value`.

**Net APY calculation (signal generation):**

```
=== Unleveraged ===
net_apy = kamino_supply_apy
Entry: net_apy >= 5%
Exit:  net_apy < 3% for > 24h

=== Leveraged (2x target) ===
net_apy = (supply_apy * leverage) - (borrow_apy * (leverage - 1))
Example: (8% * 2) - (5% * 1) = 11% net
Entry: net_apy >= 10% AND health_factor > 2.0
Exit:  net_apy < 5% OR health_factor < 1.5
```

## Risk Profile

| Metric               | Target (unleveraged) | Target (leveraged) | Notes                                        |
| -------------------- | -------------------- | ------------------ | -------------------------------------------- |
| Target annual return | 8-15%                | 15-25%             | Depends on Kamino utilization rates          |
| Target Sharpe ratio  | 3.0+                 | 2.0+               | Unleveraged is very stable                   |
| Max drawdown         | 2%                   | 8%                 | Leveraged: SOL price drop + liquidation risk |
| Max leverage         | 1x                   | 2x                 | Conservative leverage cap                    |
| Capital scalability  | $10M                 | $5M                | Kamino TVL ~$1.5B, deep reserves             |

## Latency Profile

| Segment                      | p50 Target | p99 Target | Co-location Needed?  |
| ---------------------------- | ---------- | ---------- | -------------------- |
| Market data -> feature       | 50ms       | 200ms      | No                   |
| Feature -> signal            | 10ms       | 50ms       | No                   |
| Signal -> instruction        | 5ms        | 20ms       | No                   |
| Instruction -> fill (supply) | 500ms      | 3s         | No (Solana on-chain) |
| Instruction -> fill (borrow) | 500ms      | 3s         | No (Solana on-chain) |
| **End-to-end**               | **~1.5s**  | **~6s**    | **No**               |

Low-frequency strategy (4H candles). Lending rates change slowly. Co-location provides no benefit.

## Execution Details

- **Venues:** Kamino Finance (lending/borrowing), Jupiter (swap for leveraged mode)
- **Order types:** Direct (Kamino supply/borrow via program invocation), Market (Jupiter swap)
- **Atomic execution required?** No -- each operation is independent. However, leveraged loop steps should execute in
  rapid succession to avoid price drift between deposit and borrow.
- **Gas budget:** ~0.001 SOL per supply/withdraw (~$0.15), ~0.004 SOL for full leveraged deploy (swap + deposit +
  borrow + re-deposit)

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). Driven by health factor changes (leveraged) or APY changes (unleveraged).

| Level    | Condition            | Action         | Notes                                   |
| -------- | -------------------- | -------------- | --------------------------------------- |
| Minor    | HF < 2.0 (leveraged) | LOG_ONLY       | Log health factor drift                 |
| Major    | HF < 1.5 (leveraged) | DELEVERAGE     | Repay partial debt to restore HF > 2.0  |
| Critical | HF < 1.2 (leveraged) | EMERGENCY_EXIT | Repay all debt, withdraw all collateral |
| Yield    | Supply APY < 3%      | EXIT           | Yield too low to justify gas + risk     |

**Deleveraging action:** Withdraw kUSDC -> repay USDC debt -> HF increases. If SOL drops 20%+, may need to sell some
kSOL collateral to repay debt.

SSOT: [`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> deleverage/exit decisions)

### Exposure Subscriptions

| Instrument Pattern                    | Exposure Type    | Used For                  |
| ------------------------------------- | ---------------- | ------------------------- |
| `KAMINO-SOLANA:A_TOKEN:KSOL`          | Collateral value | Health factor numerator   |
| `KAMINO-SOLANA:A_TOKEN:KUSDC`         | Supply value     | Yield tracking            |
| `KAMINO-SOLANA:DEBT_TOKEN:BORROWUSDC` | Debt value       | Health factor denominator |

Config: `defi_mode.enabled=True`, `solana_mode.enabled=True`, `defi_mode.track_lending_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type        | Subscribed?     | Threshold                                      | Action on Breach  |
| ---------------- | --------------- | ---------------------------------------------- | ----------------- |
| `protocol_risk`  | YES             | Kamino smart contract exploit / oracle failure | Emergency exit    |
| `liquidity`      | YES             | Kamino utilization > 95% (can't withdraw)      | Reduce position   |
| `borrow_cost`    | YES (leveraged) | Borrow APY > supply APY (negative yield)       | Deleverage        |
| `venue_protocol` | YES             | Solana outage / Kamino program halt            | Pause trading     |
| `delta`          | NO              | --                                             | Not delta-neutral |
| `funding`        | NO              | --                                             | No perps          |
| `staking_yield`  | NO              | --                                             | No staking        |

Config: `enabled_risk_types: ["solana_defi", "lending"]`, `defi_risk.enabled=True`,
`defi_risk.health_factor_monitoring=True` (leveraged mode) SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults, not in a machine-readable YAML registry. Plan item
`p5-risk-strategy-subscription` will create `StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk               | What It Measures                                           | Evaluation Method  | SSOT          |
| ------------------------- | ---------------------------------------------------------- | ------------------ | ------------- |
| Kamino utilization spike  | Reserve utilization > 95% (withdrawal difficulty)          | `threshold_breach` | Strategy YAML |
| Oracle price staleness    | Kamino oracle price age > 60s (stale pricing)              | `threshold_breach` | Strategy YAML |
| Borrow rate volatility    | Borrow APY swings > 5% in 1H (unpredictable cost)          | `rate_sensitivity` | Strategy YAML |
| Solana network congestion | Tx landing rate drops below 80% (can't deleverage in time) | `threshold_breach` | Strategy YAML |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** Kamino health factor (same concept as Aave: collateral \* LTV / debt)
- **Health factor threshold:** Target HF > 2.0, deleverage at HF < 1.5, emergency exit at HF < 1.2
- **Liquidation threshold:** SOL LTV ~65% on Kamino, liquidation at ~80% LTV
- **Liquidation penalty:** ~5% of liquidated collateral (Kamino liquidation bonus to liquidators)
- **Monitoring:** Health factor checked every candle (4H), with 30s feature SLA for real-time HF updates
- **Unleveraged mode:** No liquidation risk (no debt), HF monitoring disabled

## Authentication & Credentials

| Venue   | Secret Name                      | Testnet Available? | Notes                                    |
| ------- | -------------------------------- | ------------------ | ---------------------------------------- |
| Kamino  | `solana-rpc-url` (Helius/Triton) | Yes (devnet)       | Kamino program on-chain, wallet signs tx |
| Jupiter | `solana-rpc-url` (same)          | Yes (devnet)       | Same RPC -- Jupiter program on-chain     |
| Wallet  | `wallet-{client}-solana-keypair` | Yes (dev wallet)   | Signs all Solana transactions            |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Solana wallet per client (separate SOL, USDC, kSOL, kUSDC token accounts)
2. Kamino obligation account per client (tracks deposits and borrows)
3. Config: `initial_capital`, `mode` (unleveraged/leveraged), `target_leverage` (default 2x), `min_supply_apy` (default
   5%), `target_health_factor` (default 2.0), `emergency_health_factor` (default 1.2)
4. **Restart required?** No -- hot-reload via GCS config

### Services requiring per-client configuration

| Service           | What Changes                   | Restart?        |
| ----------------- | ------------------------------ | --------------- |
| strategy-service  | New config entry in GCS        | No (hot-reload) |
| execution-service | New Solana wallet routing rule | No (hot-reload) |

## UI Visualisation

### Standard views

- PnL waterfall, margin health, position breakdown (from monitoring UI plans)

### Strategy-specific views

- **Health factor time series** -- with liquidation threshold line (1.0) and target line (2.0), alert zone shaded
- **Supply APY vs borrow APY** -- dual-axis chart showing net yield spread over time
- **Kamino utilization gauge** -- per-reserve utilization with withdrawal difficulty warning at 90%+
- **Leverage ratio tracker** -- actual vs target leverage with deleverage trigger markers
- **Yield decomposition** -- stacked bar: supply yield - borrow cost = net yield (unleveraged shows supply only)

## Testing Stage Status

| Stage        | Status  | Notes                                                                 |
| ------------ | ------- | --------------------------------------------------------------------- |
| MOCK         | Pending | Need MockSolanaLendingDynamics with APY oscillation + HF simulation   |
| HISTORICAL   | Pending | Need Kamino historical supply/borrow rates (available via Kamino API) |
| LIVE_MOCK    | Pending | Blocked by features-onchain kamino_supply_apy calculator              |
| LIVE_TESTNET | Pending | Blocked by Kamino devnet integration + Jupiter devnet                 |
| BATCH_REAL   | Pending | Blocked by historical APY storage                                     |
| STAGING      | Pending | Kamino devnet + funded devnet wallet with test USDC/SOL               |
| LIVE_REAL    | Pending | All above + real capital approval                                     |

## Wallet & Capital Flow

| Component        | Value                                |
| ---------------- | ------------------------------------ |
| Treasury reserve | 20% of AUM                           |
| Hot wallet       | Solana wallet, per-strategy isolated |
| CeFi sub-account | No                                   |
| Bridge required  | No (single-chain -- Solana only)     |
| Custody          | Copper MPC                           |

Capital flow: Client deposit --> treasury --> hot wallet (Solana) --> TRANSFER + LEND to Kamino. Rebalance: treasury <
10% --> strategy reduces position --> WITHDRAW + TRANSFER --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked via Alchemy RPC using `getRecentPrioritizationFees` (Solana). The MTDS `gas_fee_handler` fetches
real-time priority fees and writes them as features. Gas hits P&L immediately as a realized transaction cost -- not
estimated. Solana gas is negligible (~0.001 SOL / ~$0.15 per transaction), making even the leveraged variant (4
transactions for full deploy) cost only ~$0.60 total.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). For
Kamino lending markets, the **base asset must be in `DEFI_MAJOR_ASSET_SYMBOLS`**. SOL, USDC, and USDT are all in the
whitelist. Solana tokens now include LSTs and ecosystem tokens (35+ in `SOLANA_TOKEN_ADDRESSES`).

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_sol_lending.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Execution adapter (Kamino):** `execution-service/protocols/kamino.py`
- **Execution adapter (Jupiter):** `execution-service/protocols/jupiter.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
- **Health factor pattern:** See [aave-lending.md](./aave-lending.md) for the equivalent Ethereum pattern
