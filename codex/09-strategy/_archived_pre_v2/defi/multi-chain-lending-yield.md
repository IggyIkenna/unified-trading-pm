---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Multi-Chain Lending Yield Optimization

> **Asset class:** DeFi **Strategy type:** Yield (cross-chain lending optimization) **Strategy ID pattern:**
> `DEFI_MULTICHAIN_LENDING_SOR_4H`

## Overview

Supply stablecoins (USDC/USDT/DAI) or ETH to lending protocols across multiple EVM chains, using CrossChainSOR to find
the best risk-adjusted APY. Automatically bridges capital to the chain with the highest net yield (gross APY minus gas
and bridge costs). The strategy continuously monitors APYs across all supported chains and protocols, rebalancing when
the differential exceeds the cost of moving capital.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDC  (100% USDC on Ethereum)

Step 1 - EVALUATE:  CrossChainSOR scores all (chain, protocol, asset) tuples
                    net_apy = gross_apy - annualized(gas_cost + bridge_fee) / holding_period
Step 2 - BRIDGE:    USDC --> USDC on target chain (via Socket, if not already on best chain)
Step 3 - APPROVE:   Approve lending pool contract for USDC on target chain
Step 4 - LEND:      USDC --> aUSDC / cUSDC / mUSDC (supply to winning protocol)

Wallet after deploy:
  - {PROTOCOL}_{CHAIN}:A_TOKEN:{ATOKEN}@{CHAIN} = supplied_amount (yield-bearing)

On rebalance (APY differential > 2% annualized after costs):
Step 5 - WITHDRAW:  Redeem from current protocol on current chain
Step 6 - BRIDGE:    Bridge to new best chain (via Socket)
Step 7 - LEND:      Supply to new best protocol on new chain

On exit:
Step 8 - WITHDRAW:  Redeem all from current protocol
Step 9 - BRIDGE:    Bridge back to Ethereum (if on another chain)
```

## Instruments

| Instrument Key                             | Venue       | Type   | Role                                |
| ------------------------------------------ | ----------- | ------ | ----------------------------------- |
| `WALLET:SPOT_ASSET:USDC`                   | Wallet      | Spot   | Initial capital                     |
| `WALLET:SPOT_ASSET:USDT`                   | Wallet      | Spot   | Alternative initial capital         |
| `WALLET:SPOT_ASSET:DAI`                    | Wallet      | Spot   | Alternative initial capital         |
| `WALLET:SPOT_ASSET:ETH`                    | Wallet      | Spot   | Alternative initial capital         |
| `AAVE_V3_{CHAIN}:A_TOKEN:A{ASSET}@{CHAIN}` | Aave V3     | aToken | Yield-bearing position (Aave)       |
| `COMPOUND_V3_{CHAIN}:C_TOKEN:C{ASSET}`     | Compound V3 | cToken | Yield-bearing position (Compound)   |
| `MORPHO_{CHAIN}:M_TOKEN:M{ASSET}`          | Morpho      | mToken | Yield-bearing position (Morpho)     |
| `KAMINO_SOLANA:K_TOKEN:K{ASSET}`           | Kamino      | kToken | Yield-bearing position (Kamino/SOL) |
| `SOCKET:BRIDGE:{ASSET}`                    | Socket      | Bridge | Cross-chain capital transfer        |

**Supported chains (Aave V3):** Ethereum, Arbitrum, Optimism, Polygon, Avalanche, Base, Gnosis, Metis, Scroll, zkSync

**Supported chains (Compound V3):** Ethereum, Arbitrum, Optimism, Polygon, Base, Scroll

**Supported chains (Morpho):** Ethereum, Base, Arbitrum, Optimism, Polygon, Scroll

## Data Architecture

| Dimension              | Value                                                                             | SSOT                                |
| ---------------------- | --------------------------------------------------------------------------------- | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)                         | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: per-chain APY, utilization, gas price, bridge fee             | Features hydrated alongside candles |
| **Features**           | `features` dict: `supply_apy_per_chain_per_protocol`, `gas_price_per_chain`, etc. | `features-onchain-service`          |
| **Interval**           | Time-driven (candle-based), not event-driven                                      | `timeframe` in strategy config      |
| **Lowest granularity** | 4H (longer than single-chain lending due to bridge latency and rebalance costs)   | Strategy factory                    |
| **Execution mode**     | `same_candle_exit` -- entry and exit can occur in same candle                     | Strategy config                     |

## Instrument Selection

**Currently: DYNAMIC via CrossChainSOR (protocol + chain selection)**

CrossChainSOR evaluates all (protocol, chain, asset) tuples and scores them:

```
net_apy = gross_apy - annualized(gas_cost + bridge_fee) / expected_holding_period
score = net_apy * (1 - protocol_risk_weight) * (1 - utilization_penalty)
```

- `protocol_risk_weight`: Aave V3 = 0.05, Compound V3 = 0.05, Morpho = 0.10, Kamino = 0.15
- `utilization_penalty`: 0 below 85%, linear ramp to 1.0 at 100% utilization

**SSOT for venue capabilities:** See
[`VENUE_CAPABILITIES`](../../../unified-api-contracts/unified_api_contracts/registry/venue_constants.py)

## Smart Order Routing (SOR)

**CrossChainSOR is the core of this strategy.** Unlike single-chain strategies, the SOR here selects both the chain and
the protocol simultaneously.

| Decision         | SOR? | Candidates                                              | SSOT                           |
| ---------------- | ---- | ------------------------------------------------------- | ------------------------------ |
| Protocol + chain | YES  | 22+ (protocol, chain) tuples                            | `CrossChainSOR` scoring engine |
| Bridge route     | YES  | Socket API evaluates bridge routes (cost, speed, trust) | `execution-service/socket.py`  |
| Asset selection  | NO   | Set at init (USDC, USDT, DAI, or ETH)                   | Strategy config                |

## Key Features Consumed

| Feature                             | Source Service   | SLA  | Used For                            |
| ----------------------------------- | ---------------- | ---- | ----------------------------------- |
| `supply_apy_per_chain_per_protocol` | features-onchain | 120s | SOR scoring: gross APY per tuple    |
| `utilization_per_chain`             | features-onchain | 120s | Risk: withdrawal risk assessment    |
| `gas_price_per_chain`               | features-onchain | 60s  | SOR scoring: gas cost component     |
| `bridge_fee`                        | features-onchain | 300s | SOR scoring: bridge cost component  |
| `aave_liquidity_index`              | features-onchain | 60s  | PnL: actual yield via index delta   |
| `compound_exchange_rate`            | features-onchain | 60s  | PnL: actual yield via exchange rate |

## PnL Attribution

| Component            | Settlement Type            | Mechanism                                                   |
| -------------------- | -------------------------- | ----------------------------------------------------------- |
| `lending_yield_pnl`  | `AAVE_INDEX` / `COMP_RATE` | `position_size * (current_index - last_index) / last_index` |
| `bridge_costs`       | Per-bridge event           | Socket bridge fee (flat or % of transfer amount)            |
| `gas_costs`          | Per-transaction            | Gas for supply/withdraw/approve on each chain               |
| `rebalance_slippage` | Per-rebalance              | Price impact from withdraw + bridge + re-supply             |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

**Net APY calculation:**

```
net_apy = gross_apy - annualized(gas_cost + bridge_fee) / expected_holding_period
```

A rebalance is only profitable when `apy_differential * remaining_holding_period > bridge_fee + 2 * gas_cost`.

## Risk Profile

| Metric               | Target | Notes                                                           |
| -------------------- | ------ | --------------------------------------------------------------- |
| Target annual return | 5-12%  | Varies by market conditions and cross-chain APY landscape       |
| Target Sharpe ratio  | 2.5+   | High Sharpe from diversified lending yield                      |
| Max drawdown         | 3%     | Primarily from bridge fees during rapid rebalancing             |
| Max leverage         | 1x     | No leverage (supply-only positions)                             |
| Capital scalability  | $50M+  | Spread across multiple chains and protocols reduces pool impact |

## Latency Profile

| Segment                                | p50 Target | p99 Target | Co-location Needed?          |
| -------------------------------------- | ---------- | ---------- | ---------------------------- |
| Market data -> feature                 | 200ms      | 1s         | No                           |
| Feature -> SOR scoring                 | 50ms       | 200ms      | No                           |
| SOR scoring -> instruction             | 10ms       | 50ms       | No                           |
| Instruction -> fill (withdraw)         | 3s         | 30s        | No (on-chain, gas dependent) |
| Bridge transit (Socket)                | 2min       | 15min      | No (cross-chain finality)    |
| Instruction -> fill (supply on target) | 3s         | 30s        | No (on-chain, gas dependent) |
| **End-to-end (no bridge)**             | **~6s**    | **~60s**   | **No**                       |
| **End-to-end (with bridge)**           | **~3min**  | **~16min** | **No**                       |

Very low-frequency strategy (4h candles). Bridge transit dominates latency. Co-location is irrelevant.

## Execution Details

- **Venues:** Aave V3 (10 chains), Compound V3 (6 chains), Morpho (6 chains), Kamino (Solana), Socket (bridge)
- **Order types:** Supply (deposit), Withdraw (redeem), Bridge (Socket cross-chain transfer)
- **Atomic execution required?** No -- withdraw, bridge, and supply are sequential but independent
- **Gas budget:** ~200k gas for supply, ~250k for withdraw, varies by chain (L2s ~10x cheaper)

### Gas Cost Multipliers (per chain, relative to Ethereum mainnet)

| Chain     | Gas Multiplier | Approx Supply Cost |
| --------- | -------------- | ------------------ |
| Ethereum  | 1.0x           | ~$15-25            |
| Arbitrum  | 0.01x          | ~$0.10-0.25        |
| Optimism  | 0.01x          | ~$0.10-0.25        |
| Base      | 0.005x         | ~$0.05-0.15        |
| Polygon   | 0.005x         | ~$0.05-0.10        |
| Avalanche | 0.02x          | ~$0.20-0.50        |
| Scroll    | 0.02x          | ~$0.20-0.50        |
| zkSync    | 0.01x          | ~$0.10-0.30        |

### Rebalancing

**Trigger type:** Threshold-driven. Rebalance when APY differential > 2% annualized (after bridge + gas costs).

| Level    | APY Differential (after costs) | Action         | Notes                                 |
| -------- | ------------------------------ | -------------- | ------------------------------------- |
| Minor    | 1-2% annualized                | LOG_ONLY       | Log opportunity, no action            |
| Major    | 2-5% annualized                | REBALANCE      | Migrate capital to higher-yield venue |
| Critical | Protocol utilization > 95%     | EMERGENCY_EXIT | Withdraw regardless of APY            |

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
| `WALLET:SPOT_ASSET:*`     | Wallet balance (pre/post deploy)   | Capital tracking           |
| `SOCKET:BRIDGE:*`         | In-transit capital                 | Bridge exposure monitoring |

Config: `defi_mode.enabled=True`, `defi_mode.track_aave_positions=True`, `defi_mode.track_compound_positions=True` SSOT:
[`ExposureMonitorConfig`](../../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type          | Subscribed? | Threshold                            | Action on Breach                        |
| ------------------ | ----------- | ------------------------------------ | --------------------------------------- |
| `protocol_risk`    | YES         | Any protocol utilization > 95%       | Emergency withdraw from that protocol   |
| `liquidity`        | YES         | Protocol utilization > 90%           | Alert, consider exit from that chain    |
| `bridge_risk`      | YES         | Bridge delay > 30min or bridge pause | Halt rebalancing, stay on current chain |
| `oracle_risk`      | YES         | Price feed deviation > 1%            | Halt rebalancing until resolved         |
| `smart_contract`   | YES         | Protocol exploit alert               | Emergency withdraw from affected chain  |
| `delta`            | NO          | --                                   | No delta exposure (supply-only)         |
| `funding`          | NO          | --                                   | No perp positions                       |
| `basis`            | NO          | --                                   | No basis trade                          |
| `borrow_cost`      | NO          | --                                   | No borrowing                            |
| `aave_liquidation` | NO          | --                                   | No debt = no liquidation risk           |

Config: `enabled_risk_types: ["aave_liquidation", "bridge_risk"]`, `defi_risk.enabled=True` SSOT:
[`RiskMonitorConfig`](../../../strategy-service/strategy_service/config.py)

**Gap:** Risk subscriptions are implicit in code defaults. Plan item `p5-risk-strategy-subscription` will create
`StrategyRiskProfile` per strategy type.

### Custom Strategy Risk Types

| Custom Risk               | What It Measures                                         | Evaluation Method  | SSOT             |
| ------------------------- | -------------------------------------------------------- | ------------------ | ---------------- |
| Cross-chain concentration | >60% capital on a single chain                           | `threshold_breach` | Strategy config  |
| Bridge liveness           | Socket bridge operational status per route               | `health_check`     | Socket API       |
| APY regime shift          | All-chain average APY drops below 2% for >24h            | `rate_sensitivity` | features-onchain |
| Protocol TVL cliff        | Protocol TVL drops >30% in 24h (potential exploit/panic) | `threshold_breach` | features-onchain |

**Gap:** Custom risk types planned (`p5-risk-custom-risk-types`) but not yet implemented.

## Margin & Liquidation

- **Margin model:** None -- all positions are supply-only (no borrowing, no leverage)
- **Health factor threshold:** N/A (no debt on any protocol)
- **Liquidation risk:** Zero across all protocols (no collateral/debt relationship)
- **Withdrawal risk:** If a protocol's utilization hits 100%, cannot withdraw until borrowers repay
- **Bridge risk:** Capital in transit during bridge is temporarily illiquid (2-15 min)
- **Smart contract risk:** Diversified across 3-4 protocols and multiple chains; single protocol exploit affects only
  the allocated fraction
- **Monitoring:** Per-chain utilization checked every 4h candle; alerts at >90% utilization on any chain

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

1. Wallet per client (separate positions across chains)
2. No venue accounts needed (all protocols are permissionless -- interact via wallet)
3. Config: `initial_capital`, `asset` (USDC/USDT/DAI/ETH), `allowed_chains`, `allowed_protocols`, `min_apy_threshold`
   (default 3%), `rebalance_threshold` (default 2%), `expected_holding_period_days` (default 30)
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

- **Cross-chain APY heatmap** -- grid of (protocol x chain) with current APY color-coded
- **Net APY time series** -- gross APY vs net APY (after gas + bridge costs) per chain
- **Capital allocation sankey diagram** -- showing capital flow across chains over time
- **Bridge transit monitor** -- in-flight capital with estimated arrival time
- **Rebalance cost tracker** -- cumulative gas + bridge fees vs yield improvement

## Testing Stage Status

| Stage        | Status  | Notes                                                                 |
| ------------ | ------- | --------------------------------------------------------------------- |
| MOCK         | Pending | Need MockDeFiDynamics with multi-chain APY divergence scenarios       |
| HISTORICAL   | Pending | Aave/Compound liquidity indices available on-chain; need multi-chain  |
| LIVE_MOCK    | Pending | Blocked by features-onchain multi-chain APY calculators               |
| LIVE_TESTNET | Pending | Aave V3 on Sepolia + Socket testnet bridge routes                     |
| BATCH_REAL   | Pending | Need historical APYs across all chains (The Graph + Alchemy archives) |
| STAGING      | Pending | Tenderly fork per chain + Socket testnet bridge                       |
| LIVE_REAL    | Pending | All above + real capital approval + multi-chain wallet setup          |

## Wallet & Capital Flow

| Component        | Value                                                          |
| ---------------- | -------------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                     |
| Hot wallet       | Multi-chain (one per destination chain), per-strategy isolated |
| CeFi sub-account | No                                                             |
| Bridge required  | Yes (multi-chain -- Socket bridge between chains)              |
| Custody          | Copper MPC                                                     |

Capital flow: Client deposit --> treasury --> hot wallet --> BRIDGE to best chain --> TRANSFER + LEND to protocol.
Rebalance: treasury < 10% --> strategy reduces position --> WITHDRAW + BRIDGE back --> treasury. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM). The MTDS `gas_fee_handler` fetches
real-time gas prices for all supported chains and writes them as features consumed by CrossChainSOR. Gas hits P&L
immediately as a realized transaction cost -- not estimated. The gas cost differential between chains (L1 ~$15-25 vs L2
~$0.10-0.25) is a key input to the SOR scoring formula.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Multi-Chain Support

Operates across 22+ (protocol, chain) tuples: Aave V3 (10 chains), Compound V3 (6 chains), Morpho (6 chains), Kamino
(Solana). All EVM chains have Alchemy RPC endpoints configured via `CHAIN_RPC_TEMPLATES` in UAC
`registry/capability_declarations/_defi.py` (12 EVM mainnets + 10 testnets + Solana mainnet/devnet + BTC in the system).

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). For
lending markets, the **base asset must be in `DEFI_MAJOR_ASSET_SYMBOLS`** (~65 tokens). The strategy only evaluates
reserves that pass the filtering pipeline.

## Bridge Costs

Cross-chain migration via Socket bridge incurs a **one-time P&L hit** -- not amortized over the holding period. The
bridge fee is deducted from principal at the time of the transfer. Across API provides live fee quotes; static estimates
serve as fallback. The rebalance decision checks whether
`apy_differential * remaining_holding_period > bridge_fee + 2 * gas_cost` before initiating any migration.

## Underlying Families / Lending Basket

The `lending_basket` config parameter defines which tokens are interchangeable for lending. Tokens within a family can
be swapped to chase higher APY across chains:

- **Stablecoin family:** USDC, USDT, DAI -- all USD-pegged, interchangeable
- **ETH family:** ETH, WETH -- same underlying value
- **BTC family:** WBTC, CBBTC -- cross-chain BTC exposure

The lending basket is a **fixed** strategy config parameter from UAC registry -- not gridded. Validated against the UAC
whitelist at strategy init.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_multichain_lending.py`
- **CrossChainSOR:** `strategy-service/strategy_service/engine/sor/cross_chain_sor.py`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Aave connector:** `execution-service/protocols/aave.py`
- **Compound connector:** `execution-service/protocols/compound.py`
- **Morpho connector:** `execution-service/protocols/morpho.py`
- **Socket bridge:** `execution-service/protocols/socket_bridge.py`
- **RPC templates:** `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py`
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
