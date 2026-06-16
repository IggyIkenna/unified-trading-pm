---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# SOL Basis Trade (Drift Protocol)

> **Asset class:** DeFi **Strategy type:** Basis (delta-neutral funding rate arbitrage) **Strategy ID pattern:**
> `DEFI_SOL_BASIS_DRIFT_1H`

## Overview

Long spot SOL + short SOL-PERP on Drift Protocol (Solana). Delta-neutral: collects Drift funding rate when perps trade
at a premium to spot. Solana's low gas (~$0.001 per tx) and fast blocks (400ms) make rebalancing cheap and responsive
compared to Ethereum-based basis trades.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDC  (100% USDC)

Step 1 - SWAP:     USDC --> SOL          (85% of capital, via Jupiter aggregator on Solana)
Step 2 - DEPOSIT:  USDC --> Drift margin (15% to Drift as perp margin)
Step 3 - TRADE:    Short SOL-PERP        (size = SOL amount from step 1, on Drift)

Wallet after deploy:
  - WALLET:SPOT_ASSET:SOL                = sol_amount   (long)
  - DRIFT-SOLANA:PERPETUAL:SOL-PERP      = -sol_amount  (short)
  - Drift margin                         = 15% USDC

Net delta = 0 (long spot + short perp cancel)
```

## Instruments

| Instrument Key                    | Venue  | Type | Role              |
| --------------------------------- | ------ | ---- | ----------------- |
| `WALLET:SPOT_ASSET:USDC`          | Wallet | Spot | Initial capital   |
| `WALLET:SPOT_ASSET:SOL`           | Wallet | Spot | Long leg          |
| `DRIFT-SOLANA:PERPETUAL:SOL-PERP` | Drift  | Perp | Short leg (hedge) |

## Key Features Consumed

| Feature              | Source Service     | SLA | Used For                               |
| -------------------- | ------------------ | --- | -------------------------------------- |
| `drift_funding_rate` | features-delta-one | 30s | Signal: entry when funding > threshold |
| `sol_price`          | market-tick-data   | 1s  | Position sizing, PnL                   |
| `basis_bps`          | features-delta-one | 30s | Spread monitoring, entry/exit trigger  |

## Data Architecture

| Dimension              | Value                                                         | SSOT                                |
| ---------------------- | ------------------------------------------------------------- | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)     | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: `sol_price`, `drift_funding_rate`         | Features hydrated alongside candles |
| **Features**           | `features` dict: `drift_funding_rate`, `basis_bps`            | `features-delta-one-service`        |
| **Interval**           | Time-driven (candle-based), not event-driven                  | `timeframe` in strategy config      |
| **Lowest granularity** | 1H (configurable via strategy config)                         | `defi_sol_basis.py` factory         |
| **Execution mode**     | `same_candle_exit` -- entry and exit can occur in same candle | Strategy config                     |

## Instrument Selection

**Currently: STATIC (hardcoded per config, no dynamic selection)**

Instruments are set at strategy initialisation and never change:

- Spot: `WALLET:SPOT_ASSET:SOL` -- always SOL
- Perp: `DRIFT-SOLANA:PERPETUAL:SOL-PERP` -- always SOL-PERP on Drift

There is **no instrument SOR** -- the strategy does NOT dynamically pick SOL vs ETH vs BTC perps based on which has the
best funding rate. This is a gap: an "instrument selection" layer could scan all Drift perp markets and pick the one
with the highest funding rate above threshold.

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON by default for the swap leg only.**

| Leg                     | SOR? | Allowed Venues                | SSOT                       |
| ----------------------- | ---- | ----------------------------- | -------------------------- |
| Step 1 (USDC->SOL swap) | YES  | `JUPITER-SOLANA` (aggregator) | `defi_sol_basis.py:swap()` |
| Step 3 (Short perp)     | NO   | Drift only (on-chain CLOB)    | --                         |

Jupiter is an aggregator that routes across Raydium, Orca, and other Solana DEXes. It functions as SOR natively -- no
multi-venue routing needed at the strategy level.

**Same-wallet constraint:** All Solana operations use the same wallet (Solana native SPL token accounts). SSOT:
[`SHARED_WALLET_GROUPS`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

**Execution boundary:** Strategy sends `StrategyInstruction` with `allowed_venues` and `max_slippage_bps`.
Execution-service converts to `ExecutionInstruction`, routes via Jupiter, executes, and measures alpha vs benchmark.

## PnL Attribution

| Component           | Settlement Type       | Mechanism                                                    |
| ------------------- | --------------------- | ------------------------------------------------------------ |
| `funding_pnl`       | `FUNDING_1H` (hourly) | `+notional * funding_rate` (positive when rate > 0)          |
| `basis_spread_pnl`  | Mark-to-market        | `abs(perp_size) * (last_premium - current_premium)`          |
| `trading_pnl`       | Entry/exit fills      | Realized price difference on swap + perp close               |
| `transaction_costs` | Per-fill              | Jupiter swap fee + Solana gas (~0.001 SOL) + Drift taker fee |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

**Note:** Drift uses hourly funding (not 8H like Hyperliquid/Binance). Funding rate is typically 15-40% APY annualized
when positive, making SOL basis on Drift more profitable than ETH basis on Hyperliquid in bull markets.

## Risk Profile

| Metric               | Target | Notes                                                      |
| -------------------- | ------ | ---------------------------------------------------------- |
| Target annual return | 15-30% | Depends on Drift funding rate regime (historically higher) |
| Target Sharpe ratio  | 2.0+   | High Sharpe due to delta neutrality                        |
| Max drawdown         | 5%     | Primarily from basis spread widening or negative funding   |
| Max leverage         | 1x     | No leverage (spot + perp hedge)                            |
| Capital scalability  | $3M    | Above this, Drift SOL-PERP depth may degrade fill quality  |

## Latency Profile

| Segment                    | p50 Target | p99 Target | Co-location Needed?  |
| -------------------------- | ---------- | ---------- | -------------------- |
| Market data -> feature     | 30ms       | 150ms      | No                   |
| Feature -> signal          | 10ms       | 50ms       | No                   |
| Signal -> instruction      | 5ms        | 20ms       | No                   |
| Instruction -> fill (swap) | 500ms      | 3s         | No (Solana on-chain) |
| Instruction -> fill (perp) | 500ms      | 3s         | No (Drift on-chain)  |
| **End-to-end**             | **~1.5s**  | **~6s**    | **No**               |

This is a low-frequency strategy (1H candles). Solana's 400ms block time makes fills faster than Ethereum. Co-location
provides no benefit.

## Execution Details

- **Venues:** Jupiter (spot swap aggregator), Drift (perp)
- **Order types:** Market (swap via Jupiter aggregator), Limit (perp on Drift CLOB)
- **Atomic execution required?** No -- legs are independent (different programs on Solana)
- **Gas budget:** ~0.001 SOL per transaction (~$0.15 at SOL=$150), ~0.003 SOL per full rebalance (swap + perp adjust +
  margin top-up)

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

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern                | Exposure Type         | Used For          |
| --------------------------------- | --------------------- | ----------------- |
| `WALLET:SPOT_ASSET:SOL`           | Spot value (long)     | Delta calculation |
| `DRIFT-SOLANA:PERPETUAL:SOL-PERP` | Perp notional (short) | Delta calculation |

Config: `defi_mode.enabled=True`, `solana_mode.enabled=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type        | Subscribed?       | Threshold                          | Action on Breach    |
| ---------------- | ----------------- | ---------------------------------- | ------------------- |
| `delta`          | YES               | 2% net delta drift                 | Adjust perp size    |
| `funding`        | YES (signal only) | `min_funding_rate` config param    | Entry/exit decision |
| `basis`          | YES (signal only) | `max_basis_deviation` config param | Entry/exit decision |
| `venue_protocol` | YES               | Drift program halt / Solana outage | Pause trading       |
| `liquidity`      | NO                | --                                 | --                  |
| `protocol_risk`  | YES               | Drift smart contract exploit       | Emergency exit      |
| `staking_yield`  | NO                | --                                 | No staking          |
| `borrow_cost`    | NO                | --                                 | No borrowing        |

Config: `enabled_risk_types: ["solana_defi"]`, `defi_risk.enabled=True` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults, not in a machine-readable YAML registry. Plan item
`p5-risk-strategy-subscription` will create `StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk                    | What It Measures                                     | Evaluation Method  | SSOT          |
| ------------------------------ | ---------------------------------------------------- | ------------------ | ------------- |
| Drift funding rate regime flip | Sustained negative funding -> strategy unprofitable  | `threshold_breach` | Strategy YAML |
| Solana network congestion      | Tx landing rate drops below 80% (degraded execution) | `threshold_breach` | Strategy YAML |
| Basis spread blow-out          | Spot-perp spread exceeds 200bps (historical 3-sigma) | `threshold_breach` | Strategy YAML |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** Drift cross-margin on perp side
- **Health factor threshold:** N/A (no lending positions)
- **Liquidation risk:** Drift margin liquidation if basis widens beyond margin buffer (15% USDC)
- **Liquidation penalty:** ~5% of position value on Drift
- **Monitoring:** Margin usage checked per candle, alert at >75% utilisation

## Authentication & Credentials

| Venue   | Secret Name                      | Testnet Available? | Notes                                    |
| ------- | -------------------------------- | ------------------ | ---------------------------------------- |
| Jupiter | `solana-rpc-url` (Helius/Triton) | Yes (devnet)       | Read: public RPC. Write: wallet signs tx |
| Drift   | `drift-authority-keypair`        | Yes (devnet)       | Solana keypair for Drift program calls   |
| Wallet  | `wallet-{client}-solana-keypair` | Yes (dev wallet)   | Signs all Solana transactions            |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Solana wallet per client (separate SOL holdings + SPL token accounts)
2. Drift sub-account per client (separate margin and positions)
3. Config: `initial_capital`, `min_funding_rate` (default 10% APY), `max_basis_deviation` (default 150bps)
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

- **Drift funding rate vs basis spread overlay** -- time series showing when funding justifies the spread
- **Delta drift chart** -- shows how far from delta-neutral over time
- **Funding collection timeline** -- hourly settlement markers with cumulative funding (Drift settles hourly, not 8H)
- **Solana tx success rate** -- monitors tx landing rate during network congestion

## Testing Stage Status

| Stage        | Status  | Notes                                                        |
| ------------ | ------- | ------------------------------------------------------------ |
| MOCK         | Pending | Need MockSolanaDeFiDynamics with Drift funding oscillation   |
| HISTORICAL   | Pending | Need Drift SOL-PERP funding rate history (available via API) |
| LIVE_MOCK    | Pending | Blocked by Solana feature computation pipeline               |
| LIVE_TESTNET | Pending | Blocked by Drift devnet integration + Jupiter devnet         |
| BATCH_REAL   | Pending | Blocked by historical APY storage                            |
| STAGING      | Pending | Drift devnet + funded devnet wallet                          |
| LIVE_REAL    | Pending | All above + real capital approval                            |

## Wallet & Capital Flow

| Component        | Value                                                       |
| ---------------- | ----------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                  |
| Hot wallet       | Solana wallet, per-strategy isolated                        |
| CeFi sub-account | Yes (Drift sub-account -- perp margin)                      |
| Bridge required  | Yes (if capital originates on EVM; No if already on Solana) |
| Custody          | Copper MPC                                                  |

Capital flow: Client deposit --> treasury --> hot wallet (Solana) --> SWAP to SOL (spot leg) + DEPOSIT USDC to Drift
(margin). Rebalance: treasury < 10% --> strategy reduces position --> close perp + SWAP SOL back --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked via Alchemy RPC using `getRecentPrioritizationFees` (Solana). The MTDS `gas_fee_handler` fetches
real-time priority fees and writes them as features. Gas hits P&L immediately as a realized transaction cost -- not
estimated. Solana gas is negligible (~0.001 SOL / ~$0.15 per transaction), making this strategy profitable at much
smaller position sizes than Ethereum equivalents.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md).
Jupiter swap routing uses SOL and USDC which are both in `DEFI_MAJOR_ASSET_SYMBOLS`. Solana tokens now include LSTs
(WSOL, MSOL, STSOL, JITOSOL, BSOL, JSOL) and ecosystem tokens (JUP, RAY, ORCA, BONK, PYTH, JTO, WIF, HNT, MNDE -- 35+ in
`SOLANA_TOKEN_ADDRESSES`).

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_sol_basis.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Execution adapter (Jupiter):** `execution-service/protocols/jupiter.py`
- **Execution adapter (Drift):** `execution-service/protocols/drift.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
- **Contracts:** `unified-api-contracts/` (canonical/external + `unified_api_contracts.internal` subpackage)
