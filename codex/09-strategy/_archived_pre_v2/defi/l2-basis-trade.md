---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# L2 Basis Trade (Reduced Gas Costs)

> **Asset class:** DeFi **Strategy type:** Basis (delta-neutral funding rate arbitrage on L2) **Strategy ID pattern:**
> `DEFI_ETH_L2_BASIS_ARB_1H`

## Overview

Same delta-neutral funding rate strategy as the ETH basis trade but executed entirely on L2 chains for dramatically
lower gas costs. Long spot ETH on Arbitrum or Base (via Uniswap V3 on L2) plus short ETH-PERP on Hyperliquid (also
L2-native). Gas costs drop from ~$20/rebalance on Ethereum mainnet to ~$0.10 on L2, making positions as small as $500
profitable. This opens the basis trade to smaller capital allocations and enables more frequent rebalancing without gas
cost erosion.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDC  (100% USDC on Arbitrum or Base)

Step 1 - SWAP:     USDC --> ETH          (90% of capital, via Uniswap V3 on ARB/BASE)
                   Gas: ~0.0001 ETH (~$0.10) vs ~0.005 ETH (~$15) on mainnet
Step 2 - TRANSFER: USDC --> Hyperliquid  (10% as margin deposit)
Step 3 - TRADE:    Short ETH-USDC perp   (size = ETH amount from step 1)

Wallet after deploy:
  - WALLET:SPOT_ASSET:ETH              = eth_amount  (long, on ARB/BASE chain)
  - HYPERLIQUID:PERPETUAL:ETH-USDC     = -eth_amount (short)
  - HYPERLIQUID margin                 = 10% USDC

Net delta = 0 (long spot + short perp cancel)

On rebalance:
Step 4 - ADJUST:   Adjust perp size on Hyperliquid (0 gas -- off-chain CLOB)
                   OR swap spot on L2 DEX (~$0.10 gas)

On exit:
Step 5 - CLOSE:    Close short perp on Hyperliquid
Step 6 - SWAP:     ETH --> USDC on ARB/BASE via Uniswap V3
```

## Instruments

| Instrument Key                                   | Venue       | Type | Role              |
| ------------------------------------------------ | ----------- | ---- | ----------------- |
| `WALLET:SPOT_ASSET:USDC`                         | Wallet      | Spot | Initial capital   |
| `WALLET:SPOT_ASSET:ETH`                          | Wallet      | Spot | Long leg (on L2)  |
| `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` | Hyperliquid | Perp | Short leg (hedge) |

**Chain selection:** Spot ETH held on Arbitrum (primary) or Base (secondary). Selected at deployment based on gas cost
and DEX liquidity. Hyperliquid is chain-agnostic (its own L1/Arbitrum-based settlement).

## Data Architecture

| Dimension              | Value                                                         | SSOT                                |
| ---------------------- | ------------------------------------------------------------- | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)     | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: `eth_price`, `funding_rate`, `gas_l2`     | Features hydrated alongside candles |
| **Features**           | `features` dict: `funding_rate`, `basis_bps`, `gas_price_l2`  | `features-delta-one-service`        |
| **Interval**           | Time-driven (candle-based), not event-driven                  | `timeframe` in strategy config      |
| **Lowest granularity** | 1H (same as mainnet basis, but cheaper to rebalance)          | Strategy factory                    |
| **Execution mode**     | `same_candle_exit` -- entry and exit can occur in same candle | Strategy config                     |

## Instrument Selection

**Currently: STATIC (hardcoded per config, same as mainnet basis trade)**

Instruments are set at strategy initialisation and never change:

- Spot: `WALLET:SPOT_ASSET:ETH` -- always ETH, held on ARB or BASE (configured at init)
- Perp: `HYPERLIQUID:PERPETUAL:ETH-USDC@LIN@HYPERLIQUID` -- always ETH-USDC on Hyperliquid

**L2 chain selection is static** -- the deployment target (ARB vs BASE) is a config parameter, not dynamically chosen.
Future enhancement: auto-select L2 chain based on gas cost and DEX liquidity.

**Future L2-native perp venues (when supported):**

- Drift (Solana) -- fully on-chain perps
- GMX (Arbitrum) -- on-chain perps with GLP liquidity

**SSOT for instrument types per venue:** See
[`INSTRUMENT_TYPES_BY_VENUE`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**SOR is ON for the swap leg only (same as mainnet basis trade, but L2 venues).**

| Leg                 | SOR? | Allowed Venues                                                 | SSOT            |
| ------------------- | ---- | -------------------------------------------------------------- | --------------- |
| Step 1 (USDC-->ETH) | YES  | `UNISWAP_V3-ARBITRUM`, `UNISWAP_V3-BASE`, `SUSHISWAP-ARBITRUM` | Strategy config |
| Step 3 (Short perp) | NO   | Hyperliquid only (CLOB, no alternative)                        | --              |

SOR picks the best price across L2 DEX venues. The `allowed_venues` list is passed in `StrategyInstruction` to
execution-service. Strategy-service does NOT pick the venue -- it provides the allowed set.

**Same-wallet constraint:** All SOR venues must be on the same L2 chain. If spot is on Arbitrum, only Arbitrum DEXes are
eligible. SSOT:
[`SHARED_WALLET_GROUPS`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Key Features Consumed

| Feature         | Source Service     | SLA | Used For                               |
| --------------- | ------------------ | --- | -------------------------------------- |
| `funding_rate`  | features-delta-one | 10s | Signal: entry when funding > threshold |
| `eth_price`     | market-tick-data   | 1s  | Position sizing, PnL                   |
| `basis_bps`     | features-delta-one | 10s | Spread monitoring                      |
| `gas_price_l2`  | features-onchain   | 30s | Cost estimation for rebalancing        |
| `bridge_status` | features-onchain   | 60s | Risk: bridge health for capital entry  |

## PnL Attribution

| Component           | Settlement Type             | Mechanism                                            |
| ------------------- | --------------------------- | ---------------------------------------------------- |
| `funding_pnl`       | `FUNDING_8H` (00/08/16 UTC) | `+notional * funding_rate` (positive when rate > 0)  |
| `basis_spread_pnl`  | Mark-to-market              | `abs(perp_size) * (last_premium - current_premium)`  |
| `trading_pnl`       | Entry/exit fills            | Realized price difference on L2 swap + perp close    |
| `transaction_costs` | Per-fill                    | L2 swap fee + L2 gas + Hyperliquid taker fee         |
| `gas_savings`       | Attribution (vs mainnet)    | Benchmark: mainnet gas cost minus actual L2 gas cost |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

**Gas cost comparison (per rebalance):**

| Chain    | Swap Gas Cost | Perp Adjustment | Total per Rebalance |
| -------- | ------------- | --------------- | ------------------- |
| Ethereum | ~$15-25       | $0 (off-chain)  | ~$15-25             |
| Arbitrum | ~$0.05-0.15   | $0 (off-chain)  | ~$0.05-0.15         |
| Base     | ~$0.03-0.10   | $0 (off-chain)  | ~$0.03-0.10         |

At 2 rebalances/day over a year: mainnet = ~$15,000/year vs L2 = ~$75/year in gas.

## Risk Profile

| Metric               | Target | Notes                                                  |
| -------------------- | ------ | ------------------------------------------------------ |
| Target annual return | 12-25% | Same funding rate as mainnet, lower costs = higher net |
| Target Sharpe ratio  | 2.5+   | Higher Sharpe than mainnet basis (lower cost drag)     |
| Max drawdown         | 5%     | Same as mainnet basis (basis spread widening)          |
| Max leverage         | 1x     | No leverage (spot + perp hedge)                        |
| Capital scalability  | $5M    | Same Hyperliquid funding rate impact as mainnet basis  |

**Minimum profitable position:** $500 (vs $10,000 on mainnet). Gas costs are negligible relative to position size, so
even small positions earn meaningful net yield.

## Latency Profile

| Segment                       | p50 Target | p99 Target | Co-location Needed?   |
| ----------------------------- | ---------- | ---------- | --------------------- |
| Market data -> feature        | 50ms       | 200ms      | No                    |
| Feature -> signal             | 10ms       | 50ms       | No                    |
| Signal -> instruction         | 5ms        | 20ms       | No                    |
| Instruction -> fill (L2 swap) | 500ms      | 5s         | No (L2 block time)    |
| Instruction -> fill (perp)    | 100ms      | 500ms      | No (Hyperliquid CLOB) |
| **End-to-end**                | **~700ms** | **~6s**    | **No**                |

Faster than mainnet basis trade due to L2 block times (~250ms on Arbitrum vs ~12s on Ethereum). Still a low-frequency
strategy (1h candles) where speed provides no edge.

## Execution Details

- **Venues:** Uniswap V3 on Arbitrum/Base (swap), Hyperliquid (perp)
- **Order types:** Market (swap via L2 SOR), Limit (perp)
- **Atomic execution required?** No -- legs are independent
- **Gas budget:** ~0.0001 ETH per swap on ARB/BASE, 0 gas for Hyperliquid (off-chain CLOB)

### Rebalancing

**Trigger type:** Event-driven (NOT periodic). No rebalance without new signal/market data.

| Level    | Position Deviation | Action         | Notes                                     |
| -------- | ------------------ | -------------- | ----------------------------------------- |
| Minor    | >2% delta drift    | LOG_ONLY       | Log deviation, no action                  |
| Major    | >5% delta drift    | REBALANCE      | Adjust perp size to restore delta-neutral |
| Critical | >10% delta drift   | EMERGENCY_EXIT | Full exit both legs                       |

Delta = `abs(spot_exposure + perp_exposure) / notional`. Target = 0.

**Key advantage:** L2 gas costs make rebalancing ~200x cheaper, so tighter delta tolerance is economically viable (could
tighten to 1% drift if desired without cost concern).

SSOT: [`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern        | Exposure Type         | Used For          |
| ------------------------- | --------------------- | ----------------- |
| `WALLET:SPOT_ASSET:ETH`   | Spot value (long)     | Delta calculation |
| `HYPERLIQUID:PERPETUAL:*` | Perp notional (short) | Delta calculation |

Config: `defi_mode.enabled=True`, `ml_mode.track_perp_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type        | Subscribed?       | Threshold                          | Action on Breach               |
| ---------------- | ----------------- | ---------------------------------- | ------------------------------ |
| `delta`          | YES               | 2% net delta drift                 | Adjust perp size               |
| `funding`        | YES (signal only) | `min_funding_rate` config param    | Entry/exit decision            |
| `basis`          | YES (signal only) | `max_basis_deviation` config param | Entry/exit decision            |
| `venue_protocol` | YES               | Hyperliquid circuit breaker state  | Pause trading                  |
| `bridge_risk`    | YES               | L2 bridge health degradation       | Halt new entries, don't exit   |
| `liquidity`      | NO                | --                                 | L2 DEX liquidity is sufficient |
| `protocol_risk`  | NO                | --                                 | No lending positions           |
| `staking_yield`  | NO                | --                                 | No staking                     |
| `borrow_cost`    | NO                | --                                 | No borrowing                   |

Config: `enabled_risk_types: ["cex_margin", "bridge_risk"]`, `defi_risk.enabled=False`, `cex_risk.enabled=True` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults. Plan item `p5-risk-strategy-subscription` will create
`StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk               | What It Measures                                        | Evaluation Method  | SSOT            |
| ------------------------- | ------------------------------------------------------- | ------------------ | --------------- |
| Funding rate regime shift | Sustained negative funding -> strategy unprofitable     | `threshold_breach` | Strategy config |
| Basis spread blow-out     | Spot-perp spread exceeds historical norms               | `threshold_breach` | Strategy config |
| L2 sequencer downtime     | Arbitrum/Base sequencer goes offline -> can't swap spot | `health_check`     | L2 RPC endpoint |
| Bridge capital isolation  | Capital stuck on L2 if bridge is paused/exploited       | `health_check`     | Socket API      |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** Hyperliquid cross-margin on perp side (same as mainnet basis trade)
- **Health factor threshold:** N/A (no Aave/lending positions)
- **Liquidation risk:** Only on Hyperliquid if margin depleted (extreme basis widening). Same risk profile as mainnet
  basis trade -- the L2 spot leg does not change the perp margin mechanics.
- **Minimum margin ratio:** 5% on Hyperliquid (maintenance margin). Strategy targets 10% initial margin for safety.
- **Monitoring:** Margin usage checked per candle, alert at >80% utilization
- **L2-specific risk:** If the L2 sequencer goes down, the spot leg cannot be adjusted. The perp leg on Hyperliquid
  remains accessible. This creates temporary delta exposure until the sequencer recovers. Mitigation: monitor sequencer
  uptime via L2 RPC health checks.

## Authentication & Credentials

| Venue                     | Secret Name                   | Testnet Available?                  | Notes                      |
| ------------------------- | ----------------------------- | ----------------------------------- | -------------------------- |
| Uniswap V3 (ARB/BASE RPC) | `alchemy-api-key`             | Yes (Arbitrum Sepolia)              | L2 RPC for swap execution  |
| Hyperliquid               | `hyperliquid-api-credentials` | Yes (`api.hyperliquid-testnet.xyz`) | API key + secret           |
| Wallet                    | `wallet-{client}-private-key` | Yes (dev wallet)                    | Signs L2 swap transactions |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Hyperliquid account per client (separate margin)
2. Wallet per client with ETH on chosen L2 chain (Arbitrum or Base)
3. Small ETH balance on L2 for gas (~0.01 ETH, enough for ~100 rebalances)
4. Config: `initial_capital`, `l2_chain` (ARB or BASE), `min_funding_rate`, `max_basis_deviation`
5. **Restart required?** No -- hot-reload via GCS config

### Services requiring per-client configuration

| Service           | What Changes                        | Restart?        |
| ----------------- | ----------------------------------- | --------------- |
| strategy-service  | New config entry in GCS             | No (hot-reload) |
| execution-service | New client wallet + L2 chain config | No (hot-reload) |
| features-onchain  | No change (shared feature pipeline) | No              |

## UI Visualisation

### Standard views

- PnL waterfall, margin health, position breakdown (from monitoring UI plans)

### Strategy-specific views

- **Funding rate vs basis spread overlay** -- same as mainnet basis, with L2 gas cost annotations
- **Delta drift chart** -- shows how far from delta-neutral over time
- **Funding collection timeline** -- 8h settlement markers with cumulative funding
- **Gas cost comparison** -- actual L2 gas vs estimated mainnet gas (shows savings)
- **L2 sequencer status** -- uptime indicator for Arbitrum/Base with historical downtime events
- **Minimum position size tracker** -- breakeven position size at current gas costs (L2 vs mainnet)

## Testing Stage Status

| Stage        | Status  | Notes                                                       |
| ------------ | ------- | ----------------------------------------------------------- |
| MOCK         | Pending | Reuse mainnet basis mock with L2 gas cost model             |
| HISTORICAL   | Pending | Same funding rate data as mainnet basis; add L2 gas history |
| LIVE_MOCK    | Pending | Blocked by L2 feature computation (gas_price_l2)            |
| LIVE_TESTNET | Pending | Uniswap V3 on Arbitrum Sepolia + Hyperliquid testnet        |
| BATCH_REAL   | Pending | Blocked by historical L2 gas cost data                      |
| STAGING      | Pending | Tenderly fork on Arbitrum + Hyperliquid testnet             |
| LIVE_REAL    | Pending | All above + real capital + L2 wallet funded with gas ETH    |

## Wallet & Capital Flow

| Component        | Value                                                          |
| ---------------- | -------------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                     |
| Hot wallet       | L2-chain wallet (Arbitrum or Base), per-strategy isolated      |
| CeFi sub-account | Yes (Hyperliquid -- perp margin)                               |
| Bridge required  | Yes (capital must be bridged to L2 if originating on Ethereum) |
| Custody          | Copper MPC                                                     |

Capital flow: Client deposit --> treasury --> BRIDGE to L2 --> hot wallet (L2) --> SWAP to ETH (spot leg) + TRANSFER
USDC to Hyperliquid (margin). Rebalance: treasury < 10% --> strategy reduces position --> close perp + SWAP ETH back -->
BRIDGE to L1 --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM). The MTDS `gas_fee_handler` fetches
real-time gas prices for the L2 chain and writes them as features. Gas hits P&L immediately as a realized transaction
cost -- not estimated. L2 gas is the key differentiator vs mainnet basis: ~$0.05-0.15 per rebalance on Arbitrum/Base vs
~$15-25 on Ethereum mainnet. This makes positions as small as $500 profitable.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). DEX
pools on L2 require BOTH sides to be in `DEFI_MAJOR_ASSET_SYMBOLS`. Perps use the CeFi base asset universe.

## Bridge Costs

Initial capital must be bridged from Ethereum to the L2 chain. This bridge cost is a **one-time P&L hit** -- not
amortized. Across API provides live fee quotes (typically 0.04-0.12% for ETH to Arbitrum/Base). The entry decision
factors this one-time cost into the minimum holding period: strategy only enters if expected funding yield recovers
bridge cost within the first week. Ongoing rebalancing incurs no bridge cost (all on same L2 chain).

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_l2_basis.py`
- **Mainnet basis (reference):** `strategy-service/strategy_service/engine/strategies/defi_basis.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md` -- L2 Basis
- **Execution adapter (swap):** `execution-service/protocols/uniswap.py` (L2 chain config)
- **Execution adapter (perp):** `execution-service/protocols/hyperliquid.py`
- **L2 RPC templates:** `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
