---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Cross-Chain Yield Arbitrage

> **Asset class:** DeFi **Strategy type:** Arbitrage (cross-chain APY spread capture) **Strategy ID pattern:**
> `DEFI_CROSSCHAIN_YIELD_ARB_1H`

## Overview

Exploit APY differentials between the same protocol on different chains, or between different protocols on different
chains for the same asset. When Aave V3 USDC supply APY on Arbitrum is 8% but only 3% on Ethereum, bridge capital to
Arbitrum to capture the 5% spread. The strategy monitors all supported chains continuously and rebalances when the
spread exceeds bridge plus gas costs for the expected holding period.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDC  (100% USDC on Ethereum)

Step 1 - SCAN:      Query all (protocol, chain) APYs for target asset
                    Identify highest APY venue and current venue
Step 2 - EVALUATE:  spread = high_apy - current_apy
                    cost = annualized(bridge_fee + gas_withdraw + gas_supply)
                    entry if: spread > 3% annualized after costs
Step 3 - WITHDRAW:  Redeem from current protocol (if already deployed)
Step 4 - BRIDGE:    USDC on source chain --> USDC on target chain (via Socket)
Step 5 - APPROVE:   Approve lending pool on target chain
Step 6 - LEND:      USDC --> aUSDC/cUSDC/mUSDC on target chain

Wallet after deploy:
  - {PROTOCOL}_{CHAIN}:A_TOKEN:{ATOKEN}@{CHAIN} = supplied_amount (yield-bearing)

On rebalance (spread narrows or better opportunity found):
Step 7 - WITHDRAW:  Redeem from current chain
Step 8 - BRIDGE:    Bridge to new best chain
Step 9 - LEND:      Supply to new best protocol

Exit signal: spread narrows below 1% annualized (no venue offers sufficient edge)
```

## Instruments

| Instrument Key                          | Venue       | Type   | Role                             |
| --------------------------------------- | ----------- | ------ | -------------------------------- |
| `WALLET:SPOT_ASSET:USDC`                | Wallet      | Spot   | Initial capital                  |
| `AAVE_V3_{CHAIN}:A_TOKEN:AUSDC@{CHAIN}` | Aave V3     | aToken | Yield position (Aave, any chain) |
| `COMPOUND_V3_{CHAIN}:C_TOKEN:CUSDC`     | Compound V3 | cToken | Yield position (Compound)        |
| `MORPHO_{CHAIN}:M_TOKEN:MUSDC`          | Morpho      | mToken | Yield position (Morpho)          |
| `SOCKET:BRIDGE:USDC`                    | Socket      | Bridge | Cross-chain capital transfer     |

**Same-protocol arb pairs (Aave V3 USDC):**

- AAVE_V3-ETHEREUM vs AAVE_V3-ARBITRUM vs AAVE_V3-BASE vs AAVE_V3-OPTIMISM vs AAVE_V3-POLYGON vs AAVE_V3-AVALANCHE vs
  AAVE_V3-SCROLL vs AAVE_V3-ZKSYNC vs AAVE_V3-GNOSIS vs AAVE_V3-METIS

**Cross-protocol arb pairs (same asset, different protocols, different chains):**

- Aave V3 USDC on ETH vs Compound V3 USDC on ARB vs Morpho USDC on BASE

## Data Architecture

| Dimension              | Value                                                                           | SSOT                                |
| ---------------------- | ------------------------------------------------------------------------------- | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                       | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: per-chain per-protocol APY, utilization, gas, bridge costs  | Features hydrated alongside candles |
| **Features**           | `features` dict: `apy_spread_matrix`, `gas_price_per_chain`, `bridge_fee`, etc. | `features-onchain-service`          |
| **Interval**           | Time-driven (candle-based), not event-driven                                    | `timeframe` in strategy config      |
| **Lowest granularity** | 1H (APYs can shift rapidly with utilization changes)                            | Strategy factory                    |
| **Execution mode**     | `same_candle_exit` -- entry and exit can occur in same candle                   | Strategy config                     |

## Instrument Selection

**Currently: DYNAMIC via spread scanning across all (protocol, chain) tuples**

The strategy maintains a live spread matrix:

```
spread_matrix[i][j] = apy[venue_i] - apy[venue_j]  for all venue pairs
best_pair = max(spread_matrix) where spread > entry_threshold after costs
```

Venue selection changes dynamically based on which pair offers the highest net spread. Capital is always in exactly one
venue at a time (no splitting).

**SSOT for venue capabilities:** See
[`VENUE_CAPABILITIES`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**CrossChainSOR is used for venue selection but NOT for trade execution.** The SOR here compares APY spreads, not trade
prices.

| Decision         | SOR? | Candidates                                  | SSOT                           |
| ---------------- | ---- | ------------------------------------------- | ------------------------------ |
| Yield venue pick | YES  | All (protocol, chain) tuples for the asset  | `CrossChainSOR` scoring engine |
| Bridge route     | YES  | Socket evaluates bridge routes per transfer | `execution-service/socket.py`  |
| Execution venue  | NO   | Direct protocol interaction (no swap SOR)   | --                             |

## Key Features Consumed

| Feature                             | Source Service   | SLA  | Used For                                  |
| ----------------------------------- | ---------------- | ---- | ----------------------------------------- |
| `supply_apy_per_chain_per_protocol` | features-onchain | 60s  | Signal: identify highest and lowest APYs  |
| `utilization_per_chain`             | features-onchain | 60s  | Risk: withdrawal risk per venue           |
| `gas_price_per_chain`               | features-onchain | 30s  | Cost: rebalance gas estimation            |
| `bridge_fee`                        | features-onchain | 300s | Cost: bridge cost for rebalance decision  |
| `aave_liquidity_index`              | features-onchain | 60s  | PnL: actual yield from Aave positions     |
| `compound_exchange_rate`            | features-onchain | 60s  | PnL: actual yield from Compound positions |
| `protocol_tvl`                      | features-onchain | 300s | Risk: TVL cliff detection                 |

## PnL Attribution

| Component          | Settlement Type            | Mechanism                                                            |
| ------------------ | -------------------------- | -------------------------------------------------------------------- |
| `spread_yield_pnl` | `AAVE_INDEX` / `COMP_RATE` | Yield earned on the high-APY side of the spread                      |
| `opportunity_cost` | Mark-to-market             | Yield forgone from the low-APY venue (attribution benchmark)         |
| `bridge_costs`     | Per-bridge event           | Socket bridge fee deducted on each rebalance                         |
| `gas_costs`        | Per-transaction            | Gas for withdraw + approve + supply on both source and target chains |
| `rebalance_drag`   | Per-rebalance              | Time in transit (2-15 min bridge) earning zero yield                 |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

**Spread capture economics:**

```
gross_spread = high_apy - low_apy  (or high_apy - 0 if entering from cash)
cost_per_rebalance = gas_withdraw + bridge_fee + gas_supply
annualized_cost = cost_per_rebalance * (365 / avg_holding_days) / capital
net_spread = gross_spread - annualized_cost
```

## Risk Profile

| Metric               | Target | Notes                                                   |
| -------------------- | ------ | ------------------------------------------------------- |
| Target annual return | 3-8%   | Pure spread capture between venues                      |
| Target Sharpe ratio  | 1.5+   | Lower Sharpe than single-venue lending (rebalance drag) |
| Max drawdown         | 4%     | Bridge fees + gas during rapid APY convergence          |
| Max leverage         | 1x     | No leverage (supply-only)                               |
| Capital scalability  | $30M   | Limited by APY impact on smaller pools                  |

## Latency Profile

| Segment                                | p50 Target | p99 Target | Co-location Needed?          |
| -------------------------------------- | ---------- | ---------- | ---------------------------- |
| Market data -> feature                 | 150ms      | 800ms      | No                           |
| Feature -> spread calculation          | 20ms       | 100ms      | No                           |
| Spread -> rebalance decision           | 10ms       | 50ms       | No                           |
| Instruction -> fill (withdraw)         | 3s         | 30s        | No (on-chain, gas dependent) |
| Bridge transit (Socket)                | 2min       | 15min      | No (cross-chain finality)    |
| Instruction -> fill (supply on target) | 3s         | 30s        | No (on-chain, gas dependent) |
| **End-to-end (no bridge)**             | **~6s**    | **~60s**   | **No**                       |
| **End-to-end (with bridge)**           | **~3min**  | **~16min** | **No**                       |

Not latency-sensitive. APYs change over minutes/hours (driven by utilization), not milliseconds. Bridge transit
dominates execution time. The risk is APY changing during bridge transit, not execution speed.

## Execution Details

- **Venues:** All Aave V3 chains, all Compound V3 chains, all Morpho chains, Socket bridge
- **Order types:** Supply (deposit), Withdraw (redeem), Bridge (Socket cross-chain transfer)
- **Atomic execution required?** No -- sequential withdraw-bridge-supply flow
- **Gas budget:** ~200k gas for supply, ~250k for withdraw per chain; L2 chains ~100x cheaper

### Rebalancing

**Trigger type:** Spread-driven. Rebalance when net spread between current venue and best venue exceeds threshold.

| Level    | Spread (after costs)               | Action         | Notes                                |
| -------- | ---------------------------------- | -------------- | ------------------------------------ |
| Minor    | 1-3% annualized                    | LOG_ONLY       | Log opportunity, continue monitoring |
| Major    | >3% annualized                     | REBALANCE      | Migrate to higher-yield venue        |
| Exit     | Best available APY < 1% annualized | EXIT           | Return capital to wallet (no yield)  |
| Critical | Protocol utilization > 95%         | EMERGENCY_EXIT | Withdraw regardless of spread        |

**Entry signal:** APY spread > 3% annualized after bridge + gas costs for expected holding period.

**Exit signal:** Spread narrows below 1% annualized, OR protocol risk increases (utilization spike, TVL drop).

SSOT: [`rebalancing_config.yaml`](../../../strategy-service/strategy_service/configs/rebalancing_config.yaml)

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern        | Exposure Type                      | Used For                   |
| ------------------------- | ---------------------------------- | -------------------------- |
| `AAVE_V3_*:A_TOKEN:*`     | aToken balance (growing via index) | Yield tracking per chain   |
| `COMPOUND_V3_*:C_TOKEN:*` | cToken balance (via exchange rate) | Yield tracking per chain   |
| `MORPHO_*:M_TOKEN:*`      | mToken balance                     | Yield tracking per chain   |
| `WALLET:SPOT_ASSET:*`     | Wallet balance (idle capital)      | Capital tracking           |
| `SOCKET:BRIDGE:*`         | In-transit capital                 | Bridge exposure monitoring |

Config: `defi_mode.enabled=True`, `defi_mode.track_aave_positions=True`, `defi_mode.track_compound_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type          | Subscribed? | Threshold                        | Action on Breach                        |
| ------------------ | ----------- | -------------------------------- | --------------------------------------- |
| `protocol_risk`    | YES         | Protocol utilization > 95%       | Emergency withdraw                      |
| `liquidity`        | YES         | Protocol utilization > 90%       | Alert, prepare exit from that venue     |
| `bridge_risk`      | YES         | Bridge delay > 30min or paused   | Halt rebalancing, stay on current venue |
| `oracle_risk`      | YES         | Cross-chain price deviation > 1% | Halt rebalancing until resolved         |
| `smart_contract`   | YES         | Protocol exploit alert           | Emergency withdraw from affected venue  |
| `delta`            | NO          | --                               | No delta exposure                       |
| `funding`          | NO          | --                               | No perp positions                       |
| `basis`            | NO          | --                               | No basis trade                          |
| `borrow_cost`      | NO          | --                               | No borrowing                            |
| `aave_liquidation` | NO          | --                               | No debt = no liquidation                |

Config: `enabled_risk_types: ["aave_liquidation", "bridge_risk"]`, `defi_risk.enabled=True` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults. Plan item `p5-risk-strategy-subscription` will create
`StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk              | What It Measures                                         | Evaluation Method  | SSOT             |
| ------------------------ | -------------------------------------------------------- | ------------------ | ---------------- |
| APY convergence speed    | Rate at which spread narrows after capital inflow        | `rate_sensitivity` | features-onchain |
| Bridge transit exposure  | Capital earning zero yield during bridge transit         | `threshold_breach` | Socket API       |
| APY manipulation risk    | Sudden APY spike from whale withdrawal (bait-and-switch) | `anomaly_detect`   | features-onchain |
| Rebalance frequency drag | Too-frequent rebalancing eroding yield via costs         | `threshold_breach` | Strategy config  |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** None -- all positions are supply-only (no borrowing, no leverage)
- **Health factor threshold:** N/A (no debt on any protocol)
- **Liquidation risk:** Zero across all protocols (no collateral/debt relationship)
- **Withdrawal risk:** If a protocol's utilization hits 100%, cannot withdraw until borrowers repay; capital is locked
  until utilization drops
- **Bridge risk:** Capital in transit during bridge is temporarily illiquid (2-15 min typical, up to 30 min in
  congestion); APY may change during transit
- **Smart contract risk:** Concentrated in one protocol at a time (unlike multi-chain-lending which diversifies);
  mitigated by protocol selection criteria (min TVL, audit history)
- **Monitoring:** APY spread matrix updated every candle (1h); utilization per venue checked continuously; bridge
  liveness checked before every rebalance

## Authentication & Credentials

| Venue                 | Secret Name                   | Testnet Available? | Notes                             |
| --------------------- | ----------------------------- | ------------------ | --------------------------------- |
| Aave V3 (via RPC)     | `alchemy-api-key`             | Yes (Sepolia)      | RPC for all EVM chains            |
| Compound V3 (via RPC) | `alchemy-api-key`             | Yes (Sepolia)      | Same RPC provider                 |
| Morpho (via RPC)      | `alchemy-api-key`             | Yes (Sepolia)      | Same RPC provider                 |
| Socket bridge         | `socket-api-key`              | Yes (testnet)      | Bridge route quotes and execution |
| Wallet                | `wallet-{client}-private-key` | Yes (dev wallet)   | Signs supply/withdraw/bridge txns |

See: [credentials-registry.yaml](../../../unified-trading-pm/credentials-registry.yaml)

## Client Onboarding

See [cross-cutting/client-onboarding.md](../../../08-workflows/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Wallet per client (capital isolation per chain)
2. No venue accounts needed (all protocols are permissionless)
3. Config: `initial_capital`, `asset` (default USDC), `allowed_chains`, `allowed_protocols`, `entry_spread_threshold`
   (default 3%), `exit_spread_threshold` (default 1%), `expected_holding_period_days` (default 14),
   `max_rebalances_per_month` (default 4)
4. **Restart required?** No -- hot-reload via GCS config

### Services requiring per-client configuration

| Service           | What Changes                        | Restart?        |
| ----------------- | ----------------------------------- | --------------- |
| strategy-service  | New config entry in GCS             | No (hot-reload) |
| execution-service | New client wallet routing           | No (hot-reload) |
| features-onchain  | No change (shared feature pipeline) | No              |

## UI Visualisation

### Standard views

- PnL waterfall, position breakdown (from monitoring UI plans)
- Margin health is N/A for this strategy (no debt)

### Strategy-specific views

- **APY spread matrix heatmap** -- all (protocol, chain) pairs with current APY and pairwise spread
- **Spread time series** -- historical spread between current and best venue, with entry/exit lines
- **Rebalance event timeline** -- when capital moved, from where to where, cost vs yield improvement
- **Bridge transit tracker** -- capital in flight with estimated arrival and APY opportunity cost
- **Cost-adjusted yield curve** -- net yield after gas + bridge vs gross APY over time

## Testing Stage Status

| Stage        | Status  | Notes                                                                      |
| ------------ | ------- | -------------------------------------------------------------------------- |
| MOCK         | Pending | Need MockDeFiDynamics with divergent APY scenarios across chains           |
| HISTORICAL   | Pending | Need historical APYs per protocol per chain (The Graph + Alchemy archives) |
| LIVE_MOCK    | Pending | Blocked by features-onchain multi-chain APY calculators                    |
| LIVE_TESTNET | Pending | Aave V3 on Sepolia + Socket testnet; limited cross-chain testnet support   |
| BATCH_REAL   | Pending | Need >90 days of multi-chain APY history for backtest validity             |
| STAGING      | Pending | Tenderly fork per chain + Socket testnet bridge                            |
| LIVE_REAL    | Pending | All above + real capital approval + bridge risk acceptance                 |

## Wallet & Capital Flow

| Component        | Value                                                          |
| ---------------- | -------------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                     |
| Hot wallet       | Multi-chain (one per destination chain), per-strategy isolated |
| CeFi sub-account | No                                                             |
| Bridge required  | Yes (capital moves to highest-APY chain via Socket bridge)     |
| Custody          | Copper MPC                                                     |

Capital flow: treasury-ETH --> BRIDGE via Socket --> treasury-DEST --> hot-wallet-DEST --> LEND to highest-APY protocol.
On rebalance: WITHDRAW --> BRIDGE to new best chain --> LEND. Gas token reserves maintained on each active chain. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM chains). The MTDS `gas_fee_handler` fetches
real-time gas prices for all supported chains and writes them as features. Gas hits P&L immediately as a realized
transaction cost -- not estimated. Gas costs are factored into the spread calculation:
`net_spread = gross_spread - annualized(gas_withdraw + bridge_fee + gas_supply)`.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Multi-Chain Support

Operates across all chains where supported lending protocols are deployed (Aave V3: 10 chains, Compound V3: 6 chains,
Morpho: 6 chains). All chains have Alchemy RPC endpoints configured via `CHAIN_RPC_TEMPLATES` in UAC
`registry/capability_declarations/_defi.py`.

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). For
lending markets, the **base asset must be in `DEFI_MAJOR_ASSET_SYMBOLS`**. The strategy only evaluates venues that pass
the filtering pipeline -- no shitcoin pools or illiquid markets reach the spread matrix.

## Bridge Costs

Bridge cost is a **one-time P&L hit** -- not amortized. The bridge fee is deducted from principal at the time of each
rebalance. Across API provides live fee quotes; static estimates serve as fallback. The entry decision checks whether
the yield spread recovers the total rebalance cost (gas + bridge fee) within the expected holding period.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_yield_arb.py`
- **CrossChainSOR:** `strategy-service/strategy_service/engine/sor/cross_chain_sor.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Aave connector:** `execution-service/protocols/aave.py`
- **Compound connector:** `execution-service/protocols/compound.py`
- **Morpho connector:** `execution-service/protocols/morpho.py`
- **Socket bridge:** `execution-service/protocols/socket_bridge.py`
- **RPC templates:** `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
