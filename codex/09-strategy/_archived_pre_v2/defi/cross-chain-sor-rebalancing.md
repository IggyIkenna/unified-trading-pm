---
scope: [engineer, admin]
---

# Cross-Chain Smart Order Routing Rebalancing

> **Asset class:** DeFi **Strategy type:** Meta-Strategy (Capital Allocation / Yield Optimisation across chains)
> **Strategy ID pattern:** `DEFI_CROSSCHAIN_SOR_REBALANCE_{GRANULARITY}`

## Overview

Continuously monitor lending/borrowing APYs, LP yields, and basis trade returns across all 19 supported EVM chains plus
Solana. When a superior yield opportunity appears on a different chain, evaluate whether bridging capital is profitable
after accounting for gas fees, bridge fees, and opportunity cost during transit time. If the net APY improvement exceeds
the rebalance cost threshold, execute the bridge + deposit atomically via the CrossChainSOR engine.

This is a META-STRATEGY that manages capital allocation across chains, not a standalone alpha-generating strategy. It
works alongside and on top of lending yield, basis trade, LP, and staked basis strategies -- deciding WHERE capital
should be deployed, while those strategies decide HOW capital is deployed on each chain.

## How This Fits the Unified Trading System

The CrossChainSOR strategy sits above individual chain strategies in the strategy hierarchy. It consumes aggregated
yield features from all chains, compares risk-adjusted net returns, and emits TRANSFER instructions (not SWAP or TRADE)
that are routed through the TransferHandler in execution-service.

```
features-onchain-service (publishes: per-chain APYs, gas_prices, utilization_rates)
  + features-delta-one (publishes: per-chain funding_rates, basis_spreads)
    -> strategy-service CrossChainSOR aggregates all chain yields
      -> scoring: net_APY = gross_APY - annualized(gas + bridge_fee) / holding_period
        -> decision: STAY / EVALUATE / EXECUTE
          -> emit StrategyInstruction (TRANSFER: bridge + deposit on target chain)
            -> execution-service TransferHandler -> SocketBridgeConnector
```

## Decision Framework

### CrossChainSOR Scoring

For each potential rebalance opportunity:

```
net_APY = gross_APY_target - annualized(gas_withdraw + bridge_fee + gas_deposit) / expected_holding_period
spread  = net_APY_target - current_APY_source
```

### Decision Matrix

| Condition                                    | Decision | Action                               |
| -------------------------------------------- | -------- | ------------------------------------ |
| `current_APY >= target_APY - rebalance_cost` | STAY     | No action, current chain is optimal  |
| `spread > 2% annualized after costs`         | EVALUATE | Log opportunity, check bridge status |
| `spread > 3% AND bridge_time < 15min`        | EXECUTE  | Initiate bridge + deposit            |
| `spread > 5% AND bridge_time < 30min`        | EXECUTE  | Higher threshold for slower bridges  |
| `spread > 10%`                               | EXECUTE  | Any bridge acceptable (high urgency) |
| `capital_in_transit > 20% of portfolio`      | HOLD     | Too much capital already bridging    |

### Bridge Protocol Selection

| Bridge   | Typical Time | Fee (% of amount) | Best For                    | Chains Supported           |
| -------- | ------------ | ----------------- | --------------------------- | -------------------------- |
| Across   | ~2 min       | 0.04-0.12%        | Speed, lowest fees          | ETH, ARB, OP, BASE, POLY   |
| Stargate | ~5 min       | 0.06-0.15%        | Deep liquidity, many chains | 15+ EVM chains             |
| CCTP     | ~15 min      | 0%                | USDC-only, zero fee         | ETH, ARB, OP, AVAX, BASE   |
| Hop      | ~8 min       | 0.05-0.10%        | L2-to-L2 direct             | ETH, ARB, OP, POLY, GNOSIS |

Bridge selection is part of the SOR scoring: `bridge_cost = fee_pct * amount + gas_cost`. For USDC transfers, CCTP is
always cheapest (zero fee) but slowest. The strategy picks the bridge that maximises
`net_APY - annualized(bridge_cost)`.

## Token / Position Flow

```
Start:  AAVE_V3-ETHEREUM:A_TOKEN:USDC (lending USDC on Ethereum Aave, earning 4% APY)

Trigger: Aave V3 on Arbitrum APY rises to 9% (spread = 5% > 3% threshold)

Step 1 - WITHDRAW:
  Withdraw USDC from Aave V3 on Ethereum
  Gas: ~0.003 ETH (~$9)
  Result: WALLET:SPOT_ASSET:USDC on Ethereum

Step 2 - BRIDGE (via Across):
  Bridge USDC from Ethereum -> Arbitrum
  Fee: 0.06% of amount
  Time: ~2 minutes
  Result: WALLET:SPOT_ASSET:USDC on Arbitrum

Step 3 - DEPOSIT:
  Deposit USDC into Aave V3 on Arbitrum
  Gas: ~0.0001 ETH (~$0.30 on Arbitrum)
  Result: AAVE_V3-ARBITRUM:A_TOKEN:USDC (earning 9% APY)

Wallet after rebalance:
  - AAVE_V3-ARBITRUM:A_TOKEN:USDC = full position (9% APY)
  - Ethereum position: closed
  - Capital in transit: 0 (bridge completed)

Cost analysis for $100,000 rebalance:
  - Gas (withdraw + deposit): ~$9.30
  - Bridge fee (0.06%): $60
  - Total cost: ~$69.30
  - Annualised cost (if held 30 days): ~$69.30 * (365/30) = ~$843
  - APY improvement: 5% * $100,000 = $5,000/year
  - Net benefit: $5,000 - $843 = $4,157/year
```

## Instruments

| Instrument Key                      | Venue        | Type     | Role                            |
| ----------------------------------- | ------------ | -------- | ------------------------------- |
| `AAVE_V3-ETHEREUM:A_TOKEN:USDC`     | Aave V3 ETH  | aToken   | Lending position (source chain) |
| `AAVE_V3-ARBITRUM:A_TOKEN:USDC`     | Aave V3 ARB  | aToken   | Lending position (target chain) |
| `AAVE_V3-OPTIMISM:A_TOKEN:USDC`     | Aave V3 OP   | aToken   | Lending position (target chain) |
| `AAVE_V3-BASE:A_TOKEN:USDC`         | Aave V3 BASE | aToken   | Lending position (target chain) |
| `AAVE_V3-POLYGON:A_TOKEN:USDC`      | Aave V3 POLY | aToken   | Lending position (target chain) |
| `AAVE_V3-AVALANCHE:A_TOKEN:USDC`    | Aave V3 AVAX | aToken   | Lending position (target chain) |
| `UNISWAP_V3-ETHEREUM:LP_POSITION:*` | Uniswap V3   | LP NFT   | LP position (source/target)     |
| `WALLET:SPOT_ASSET:USDC`            | Wallet       | Spot     | In-transit / undeployed capital |
| `WALLET:SPOT_ASSET:ETH`             | Wallet       | Spot     | Gas token (Ethereum)            |
| `WALLET:SPOT_ASSET:MATIC`           | Wallet       | Spot     | Gas token (Polygon)             |
| `SOCKET-BRIDGE:TRANSFER:*`          | Socket       | Transfer | Bridge transaction in flight    |

## Key Features Consumed

| Feature               | Source Service     | SLA  | Used For                                             |
| --------------------- | ------------------ | ---- | ---------------------------------------------------- |
| `all_chain_apys`      | features-onchain   | 60s  | Cross-chain yield comparison                         |
| `gas_prices`          | features-onchain   | 30s  | Rebalance cost estimation per chain                  |
| `bridge_fees`         | features-onchain   | 300s | Bridge cost estimation per protocol                  |
| `bridge_times`        | features-onchain   | 300s | Bridge duration estimation per protocol              |
| `utilization_rates`   | features-onchain   | 60s  | APY sustainability signal (high util = volatile APY) |
| `pool_tvl_all_chains` | features-onchain   | 300s | LP opportunity sizing across chains                  |
| `funding_rates`       | features-delta-one | 60s  | Basis strategy yield comparison                      |
| `basis_spreads`       | features-delta-one | 60s  | Basis strategy yield comparison                      |
| `chain_health`        | features-onchain   | 30s  | Chain liveness / congestion detection                |

## Data Architecture

| Dimension              | Value                                                             | SSOT                          |
| ---------------------- | ----------------------------------------------------------------- | ----------------------------- |
| **Raw data source**    | NEVER direct -- via features-onchain-service (all chains)         | Hard rule                     |
| **Features consumed**  | Aggregated APYs, gas prices, bridge fees from all 19 EVM + Solana | `features-onchain-service`    |
| **Interval**           | Periodic 1H evaluation cycle with emergency override on APY spike | Strategy trigger subscription |
| **Lowest granularity** | Per-block per chain via feature service                           | Feature service config        |

## Instruction Types Needed

| Operation  | What It Does                            | Parameters                                              | Exists? |
| ---------- | --------------------------------------- | ------------------------------------------------------- | ------- |
| `WITHDRAW` | Remove capital from lending/LP protocol | protocol, chain, asset, amount                          | EXISTS  |
| `TRANSFER` | Bridge assets cross-chain via Socket    | source_chain, target_chain, asset, amount, bridge_proto | EXISTS  |
| `DEPOSIT`  | Deploy capital into target protocol     | protocol, chain, asset, amount                          | EXISTS  |

All instruction types already exist. This strategy composes existing operations into a withdraw -> bridge -> deposit
sequence. The TransferHandler in execution-service manages the bridge lifecycle (submit, monitor, confirm).

## Smart Order Routing (SOR)

**SOR is the core of this strategy.** The CrossChainSOR engine evaluates:

1. **Yield ranking:** All chains ranked by risk-adjusted net APY for each asset
2. **Bridge path optimisation:** For each source -> target pair, select cheapest bridge that meets time constraint
3. **Gas optimisation:** Factor in gas token prices per chain (ETH, MATIC, AVAX, BNB, etc.)
4. **Capital allocation:** Distribute across top N chains to avoid concentration risk
5. **Rebalance batching:** If multiple positions need rebalancing, batch to reduce total bridge transactions

The SOR output is a ranked list of rebalance instructions with expected net benefit, ordered by urgency.

## PnL Attribution

| Component               | Settlement Type | Mechanism                                                  |
| ----------------------- | --------------- | ---------------------------------------------------------- |
| `yield_improvement_pnl` | Mark-to-market  | APY difference between new chain and old chain             |
| `bridge_cost_pnl`       | Per-transfer    | Bridge fees paid (deducted from principal)                 |
| `gas_cost_pnl`          | Per-transfer    | Gas for withdraw + bridge + deposit across chains          |
| `opportunity_cost_pnl`  | Time-weighted   | Yield foregone during bridge transit time                  |
| `slippage_pnl`          | Per-transfer    | Bridge price impact for large transfers                    |
| `underlying_yield_pnl`  | Accrual-based   | Actual yield earned on deployed capital (from child strat) |

**Source of truth:**
`total_pnl = sum(yield_earned_all_chains) - sum(bridge_costs) - sum(gas_costs) - sum(opportunity_costs)`

The strategy's value-add is measured by comparing portfolio-wide yield WITH CrossChainSOR vs a static single-chain
baseline: `sor_alpha = portfolio_yield_with_sor - best_single_chain_yield`.

## Risk & Exposure Subscriptions

**Flow:** ExposureMonitor (positions -> exposures) -> RiskMonitor (exposures -> risk assessment) -> Strategy (risk
assessment -> rebalance/exit decisions)

### Exposure Subscriptions

| Instrument Pattern           | Exposure Type             | Used For                              |
| ---------------------------- | ------------------------- | ------------------------------------- |
| `AAVE_V3-*:A_TOKEN:*`        | Lending position value    | Per-chain capital deployment tracking |
| `UNISWAP_V3-*:LP_POSITION:*` | LP position value         | Per-chain LP capital tracking         |
| `WALLET:SPOT_ASSET:*`        | Undeployed capital        | Idle capital detection                |
| `SOCKET-BRIDGE:TRANSFER:*`   | In-transit capital        | Capital stuck in bridge monitoring    |
| `WALLET:SPOT_ASSET:ETH`      | Gas token balance (ETH)   | Ensure sufficient gas on Ethereum     |
| `WALLET:SPOT_ASSET:MATIC`    | Gas token balance (MATIC) | Ensure sufficient gas on Polygon      |

**SSOT:** `component_config.exposure_monitor.instrument_subscriptions` in strategy config. Schema:
[`ExposureMonitorConfig`](../../strategy-service/strategy_service/config.py)

### Risk Type Subscriptions

| Risk Type            | Subscribed? | Threshold                             | Action on Breach                            |
| -------------------- | ----------- | ------------------------------------- | ------------------------------------------- |
| `bridge_failure`     | YES         | Bridge tx pending > 30 min            | Cancel + retry via alternative bridge       |
| `capital_in_transit` | YES         | > 20% of portfolio in transit         | Pause new rebalances until bridges settle   |
| `chain_congestion`   | YES         | Gas price > 5x 7-day average          | Delay non-urgent rebalances                 |
| `protocol_risk`      | YES         | Target protocol TVL drop > 20% in 1h  | Abort pending rebalance to that chain       |
| `apy_volatility`     | YES         | Target APY drops > 50% during bridge  | Reroute capital on arrival, do not deposit  |
| `concentration`      | YES         | > 40% of capital on single chain      | Force diversification rebalance             |
| `gas_token_balance`  | YES         | < 2x expected gas cost on any chain   | Top up gas token before next rebalance      |
| `liquidity`          | YES         | Bridge liquidity < 2x transfer amount | Use smaller transfer or alternative bridge  |
| `delta`              | NO          | --                                    | -- (meta-strategy, no directional exposure) |
| `funding`            | NO          | --                                    | -- (managed by child strategies)            |
| `impermanent_loss`   | NO          | --                                    | -- (managed by child LP strategies)         |

**SSOT:** `component_config.risk_monitor.enabled_risk_types` in strategy config. Schema:
[`RiskMonitorConfig`](../../strategy-service/strategy_service/config.py) Formal subscription type:
[`StrategyRiskProfile`](../../unified-api-contracts/unified_api_contracts/internal/risk.py)

### Custom Strategy Risk Types

| Custom Risk              | What It Measures                                       | Evaluation Method  | SSOT            |
| ------------------------ | ------------------------------------------------------ | ------------------ | --------------- |
| Bridge completion rate   | % of bridges that complete within expected time        | `rate_sensitivity` | Strategy logs   |
| APY decay during transit | How much target APY dropped while capital was bridging | monitoring         | Strategy logs   |
| Rebalance profitability  | % of rebalances that produced positive net APY gain    | `threshold_breach` | Strategy logs   |
| Chain concentration HHI  | Herfindahl index of capital across chains              | `threshold_breach` | Portfolio state |
| Gas token adequacy       | Days of gas runway remaining per chain                 | `threshold_breach` | Wallet balances |
| Idle capital ratio       | % of portfolio not earning yield (in wallet/bridge)    | `threshold_breach` | Portfolio state |

## Risk Profile

| Metric               | Target          | Notes                                                           |
| -------------------- | --------------- | --------------------------------------------------------------- |
| Target annual return | +2-5% over base | Incremental yield vs static single-chain deployment             |
| Target Sharpe ratio  | N/A (overlay)   | Measured as information ratio vs single-chain baseline          |
| Max drawdown         | 1% from transit | Capital loss only from bridge failure or gas costs, not market  |
| Max leverage         | 1x              | No leverage -- fully funded transfers                           |
| Capital scalability  | $10M+           | Scales well -- bridge liquidity is the bottleneck, not on-chain |

## Latency Profile

| Segment                          | p50 Target | p99 Target | Co-location Needed? |
| -------------------------------- | ---------- | ---------- | ------------------- |
| Feature aggregation (all chains) | 5s         | 15s        | No                  |
| SOR scoring + decision           | 500ms      | 2s         | No                  |
| Withdraw from source protocol    | 15s        | 60s        | No (gas-dependent)  |
| Bridge transit (Across)          | 2min       | 10min      | No                  |
| Bridge transit (CCTP)            | 15min      | 30min      | No                  |
| Deposit to target protocol       | 15s        | 60s        | No (gas-dependent)  |
| **End-to-end (Across)**          | **~3min**  | **~12min** | **No**              |
| **End-to-end (CCTP)**            | **~16min** | **~32min** | **No**              |

This is a slow strategy by design. The 1H evaluation cycle means latency is not critical. What matters is reliability of
the bridge + deposit sequence, not speed.

## Execution Details

- **Venues:** All lending/borrowing venues (Aave V3 on 10 chains), LP venues (Uniswap V3 on 4 chains), Socket bridge
  aggregator
- **Order types:** Protocol interactions (withdraw, bridge, deposit) -- not order book
- **Atomic execution required?** No -- the withdraw-bridge-deposit sequence is inherently non-atomic (cross-chain). Each
  step is confirmed before the next begins. The TransferHandler manages the state machine.
- **Gas budget:** Varies by chain. Ethereum: ~$9 withdraw. L2s: ~$0.10-0.50. Bridge: protocol-dependent fee.

### Rebalancing

**Trigger type:** Periodic evaluation every 1 hour. Emergency trigger on APY spike > 5% absolute.

| Level     | Condition                               | Action                                            |
| --------- | --------------------------------------- | ------------------------------------------------- |
| Normal    | All chains within 2% APY of each other  | No action, portfolio is balanced                  |
| Minor     | Spread > 2% but < 3% after costs        | Log opportunity, monitor for persistence          |
| Major     | Spread > 3% after costs, bridge < 15min | Execute rebalance (withdraw -> bridge -> deposit) |
| Critical  | Target chain APY drops during bridge    | Reroute capital to next best chain on arrival     |
| Emergency | Bridge stuck > 30min                    | Escalate to manual review, attempt cancel/retry   |

### Capital Allocation Rules

- **Minimum per chain:** $10,000 (below this, gas costs eat too much of the yield improvement)
- **Maximum per chain:** 40% of portfolio (diversification constraint)
- **Maximum in transit:** 20% of portfolio at any time
- **Minimum holding period:** 7 days (prevents churning on volatile APYs)
- **Gas reserve:** Maintain 2x expected gas cost in native token on each active chain

## Margin & Liquidation

- **Margin model:** None -- fully funded transfers, no leverage, no borrowing
- **Liquidation risk:** None (this strategy only moves capital, does not borrow)
- **Bridge risk:** Capital stuck in bridge if protocol fails. Mitigated by bridge diversification and amount limits.
- **Smart contract risk:** Bridge exploit (historical: Wormhole $320M, Ronin $625M). Mitigated by: per-bridge amount
  caps, using Socket aggregator for bridge selection, avoiding newest/unaudited bridges.
- **Health factor monitoring:** Delegated to child strategies (Aave lending, LP). This strategy only monitors
  transit-related risks.

## Authentication & Credentials

Links to SSOT -- do not duplicate:

- **API keys needed:** See [credentials-registry.yaml](../../unified-trading-pm/credentials-registry.yaml)
- **Secret names:** See
  [CredentialsRegistry](../../unified-cloud-interface/unified_cloud_interface/credentials_registry.py)
- **Venue capabilities:** See
  [capability_declarations/](../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/)

| Venue         | Secret Name               | Testnet Available? | Notes                         |
| ------------- | ------------------------- | ------------------ | ----------------------------- |
| Socket Bridge | `socket-api-key`          | Yes                | Bridge aggregator API         |
| Aave V3 (all) | `defi-wallet-private-key` | Yes (Sepolia)      | Same wallet across EVM chains |
| Uniswap V3    | `defi-wallet-private-key` | Yes (Sepolia)      | Same wallet across EVM chains |
| Alchemy RPC   | `alchemy-api-key`         | Yes                | RPC provider for all chains   |

## Client Onboarding

### Adding a new client to this strategy

1. **Execution accounts:** Single EVM wallet (same address across all chains via deterministic derivation)
2. **Secret Manager:** `defi-wallet-private-key-{client}` -- same key works across all EVM chains
3. **Config:** New entry in strategy config YAML with: target chains, min spread threshold, preferred bridges, max
   capital per chain, holding period
4. **Gas provisioning:** Fund native gas tokens on each target chain (ETH, MATIC, AVAX, BNB, etc.)
5. **Position isolation:** One strategy instance per client (capital allocation decisions are client-specific)
6. **Restart required?** No -- hot-reload via UCI config watcher

### Services requiring per-client configuration

| Service           | What Changes                            | Restart?        |
| ----------------- | --------------------------------------- | --------------- |
| strategy-service  | New CrossChainSOR config entry          | No (hot-reload) |
| execution-service | New client wallet routing + bridge auth | No (hot-reload) |
| features-onchain  | May need new chain subscriptions        | No (hot-reload) |

## UI Visualisation

### Standard views (already in plans)

- PnL waterfall (risk matrix plan Stream D)
- Position breakdown (per-chain capital allocation)

### Strategy-specific views (extensions)

- Cross-chain capital allocation sunburst chart: portfolio % per chain, colour-coded by current APY
- Yield heatmap: matrix of chains x assets, cell colour = current APY, annotations for recent rebalances
- Bridge transaction tracker: in-flight transfers with progress bar (submitted -> confirmed -> arrived -> deployed)
- Rebalance history timeline: when capital moved, from where, to where, net benefit realised
- SOR decision log: evaluated opportunities with STAY/EVALUATE/EXECUTE decisions and reasoning
- Gas token runway dashboard: days of gas remaining per chain, alerts when low

## Testing Stage Status

| Stage        | Status  | Notes                                                                |
| ------------ | ------- | -------------------------------------------------------------------- |
| MOCK         | Pending | Multi-chain APY simulation with mock bridge delays                   |
| HISTORICAL   | Pending | Historical APY data from DeFi Llama + on-chain archives              |
| LIVE_MOCK    | Pending | Real APY feeds + paper bridge execution                              |
| LIVE_TESTNET | Pending | Sepolia Aave + testnet bridges (limited testnet bridge availability) |
| BATCH_REAL   | Pending | Historical backtest: what would SOR have done over last 90 days?     |
| STAGING      | Pending | Tenderly forks on multiple chains + real Socket API                  |
| LIVE_REAL    | Pending | All above + bridge risk accepted + gas tokens funded on all chains   |

## Wallet & Capital Flow

| Component        | Value                                                                       |
| ---------------- | --------------------------------------------------------------------------- |
| Treasury reserve | 20% of AUM                                                                  |
| Hot wallet       | Multi-chain (one per destination chain), per-strategy isolated              |
| CeFi sub-account | No                                                                          |
| Bridge required  | Yes (core operation -- capital moves between chains via Socket/Across/CCTP) |
| Custody          | Copper MPC                                                                  |

Capital flow: treasury-ETH --> BRIDGE via Socket --> treasury-DEST --> hot-wallet-DEST --> DEPOSIT to protocol. Gas
token reserves maintained on each active chain (2x expected gas cost in native token). Maximum 20% of portfolio in
transit at any time. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC using `eth_feeHistory` (EVM chains). The MTDS `gas_fee_handler` fetches
real-time gas prices for all 19 supported EVM chains and writes them as features consumed by the CrossChainSOR scoring
engine. Gas hits P&L immediately as a realized transaction cost -- not estimated. Gas cost differentials between chains
are a primary input to the SOR scoring formula and the decision of whether to rebalance.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Multi-Chain Support

All 19 EVM mainnets plus Solana are supported. All chains have Alchemy RPC endpoints configured via
`CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py` (12 EVM mainnets + 10 testnets + Solana
mainnet/devnet + BTC in the system). Gas token balances (ETH, MATIC, AVAX, BNB, etc.) are tracked per chain via
`GasTokenBalanceTracker`.

## Instrument Filtering

Pool and market discovery follows the rules in [instrument-filtering.md](../../operational/instrument-filtering.md). The
CrossChainSOR only evaluates instruments that pass the filtering pipeline. For lending markets, the base asset must be
in `DEFI_MAJOR_ASSET_SYMBOLS`. For DEX pools, BOTH sides must be major assets with TVL minimums enforced.

## Bridge Costs

Bridge cost is a **one-time P&L hit** -- not amortized over the holding period. The bridge fee is deducted from
principal at the time of the transfer. Across API provides live fee quotes for bridge selection; static estimates from
historical averages serve as fallback. The CrossChainSOR entry decision checks whether the yield improvement on the
target chain recovers the total migration cost (gas + bridge fee) within the expected holding period before executing.

## References

- **Strategy ID:** `DEFI_CROSSCHAIN_SOR_REBALANCE_1H`
- **Implementation:** `strategy-service/strategy_service/engine/strategies/` (CrossChainSOR -- TBD)
- **CrossChainSOR engine:** `strategy-service/strategy_service/sor/` (scoring + bridge selection)
- **SocketBridgeConnector:** `execution-service/execution_service/defi_execution/` (bridge execution)
- **TransferHandler:** `execution-service/execution_service/` (withdraw-bridge-deposit state machine)
- **RPC URL templates:** `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py`
- **Bridge protocols:** Socket aggregator API (routes across Across, Stargate, CCTP, Hop)
- **Venue capabilities:** `venue_constants.py` -- `CROSS_CHAIN_TRANSFER` capability
- **Hard rules:** [config-architecture.md](../cross-cutting/config-architecture.md)
