---
scope: [engineer, admin]
---

# DeFi Ethena sUSDe Benchmark

> **Asset class:** DeFi **Strategy type:** Passive Benchmark (buy-and-hold yield tracker) **Strategy ID pattern:**
> `DEFI_ETH_YLD_ETHENA_SUSDE_{TOKEN}_BENCH_1H`

## Overview

Passive buy-and-hold benchmark that deploys 100% of capital into Ethena sUSDe on the first candle, then holds
indefinitely. This is NOT a trading strategy -- it never exits, never rebalances, and never makes active decisions after
the initial deployment. P&L accrues entirely from sUSDe exchange-rate appreciation (yield-bearing token).

Used as the comparison baseline for all active DeFi yield strategies. Ethena sUSDe delivers approximately 9.8% APY
through its delta-neutral synthetic dollar backing mechanism. Any active strategy (lending, basis, recursive) must
outperform this benchmark on a risk-adjusted basis to justify its additional complexity and gas costs.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDT  (100% USDT)

Step 1 - TRANSFER: USDT --> ETHENA-ETHEREUM    (move full wallet balance to Ethena)
Step 2 - STAKE:    USDe --> sUSDe              (stake USDe into sUSDe yield vault)

Wallet after deploy:
  - ETHENA-ETHEREUM:YIELD_BEARING:SUSDE@ETHEREUM = full_amount (appreciating)

Lifecycle:
  - First candle: DEPLOY (TRANSFER + STAKE)
  - Every subsequent candle: hold (no instructions emitted)
  - Never exits -- buy-and-hold forever
```

## Instruments

| Instrument Key                                 | Venue  | Type          | Role                   |
| ---------------------------------------------- | ------ | ------------- | ---------------------- |
| `WALLET:SPOT_ASSET:USDT`                       | Wallet | Spot          | Initial capital        |
| `ETHENA-ETHEREUM:YIELD_BEARING:SUSDE@ETHEREUM` | Ethena | Yield Bearing | Yield-bearing position |

## Data Architecture

| Dimension              | Value                                                                  | SSOT                                |
| ---------------------- | ---------------------------------------------------------------------- | ----------------------------------- |
| **Raw data source**    | `CloudDataProvider` (live) / `CSVDataProvider` (backtest)              | `strategy-service/config.py`        |
| **Processed data**     | `market_data` dict: `susde_exchange_rate`, `ethena_susde_apy`          | Features hydrated alongside candles |
| **Features**           | `lending_rates` group: `susde_exchange_rate`, `ethena_susde_apy`       | `features-onchain-service`          |
| **Interval**           | Time-driven (candle-based), not event-driven                           | `timeframe` in strategy config      |
| **Lowest granularity** | 1H (factory default)                                                   | `defi_ethena_benchmark.py` factory  |
| **Execution mode**     | `same_candle_exit` -- but exit never triggers (this is a buy-and-hold) | Strategy config                     |

## Key Features Consumed

| Feature               | Source Service   | SLA | Used For                        |
| --------------------- | ---------------- | --- | ------------------------------- |
| `ethena_susde_apy`    | features-onchain | 60s | Display: current sUSDe APY      |
| `susde_exchange_rate` | features-onchain | 60s | P&L: exchange rate appreciation |
| `susde_yield`         | features-onchain | 60s | Fallback for `ethena_susde_apy` |

The strategy reads `ethena_susde_apy` first, falling back to `susde_yield` if unavailable. The exchange rate is tracked
every candle for P&L attribution even though no trading action occurs.

## Signal Generation

```python
# First candle: always DEPLOY (benchmark deploys unconditionally)
if not self.is_deployed:
    return {"action": "DEPLOY", "reason": "benchmark_initial_deploy"}

# All subsequent candles: return None (hold forever)
return None
```

The benchmark has no entry conditions, no exit conditions, no APY thresholds. It deploys on the first candle that has
wallet funds and holds forever. This ensures a clean baseline comparison.

## Instruction Flow

```mermaid
flowchart LR
    A[Wallet: USDT] -->|TRANSFER| B[ETHENA-ETHEREUM]
    B -->|STAKE USDe→sUSDe| C[ETHENA-ETHEREUM:YIELD_BEARING:SUSDE@ETHEREUM]
    C -->|Hold forever| C
```

### Deploy Instructions (emitted once)

1. **TRANSFER**: Move full wallet balance from `WALLET` to `ETHENA-ETHEREUM`
   - `operation=OperationType.TRANSFER`
   - `token_in=USDT`
   - `from_venue=WALLET`, `to_venue=ETHENA-ETHEREUM`

2. **STAKE**: Convert USDe to sUSDe via Ethena staking contract
   - `operation=OperationType.STAKE`
   - `token_in=USDE`, `token_out=SUSDE`
   - `instrument_id=ETHENA-ETHEREUM:YIELD_BEARING:SUSDE@ETHEREUM`
   - `benchmark_type=BenchmarkType.ORACLE`

Both instructions are linked via `linked_instruction`/`linked_transfer` metadata for fill correlation.

## PnL Attribution

| Component                 | Settlement Type | Mechanism                                             |
| ------------------------- | --------------- | ----------------------------------------------------- |
| `exchange_rate_yield_pnl` | Mark-to-market  | `position * (current_rate - entry_rate) / entry_rate` |
| `transaction_costs`       | Per-fill        | Gas for TRANSFER + STAKE (~200k gas total)            |

**Source of truth:** `total_pnl = sUSDe_balance * current_rate - initial_deposit`

The strategy tracks `entry_exchange_rate` and `last_exchange_rate` on every candle. Since sUSDe is a rebasing
yield-bearing token, the exchange rate monotonically increases (barring protocol failure), producing smooth P&L growth.

## Risk Profile

| Metric               | Target | Notes                                               |
| -------------------- | ------ | --------------------------------------------------- |
| Target annual return | ~9.8%  | Based on Ethena sUSDe historical yield              |
| Target Sharpe ratio  | 5.0+   | Extremely stable -- yield accrues monotonically     |
| Max drawdown         | <1%    | Only from gas costs and potential exchange rate lag |
| Max leverage         | 1x     | No leverage                                         |
| Capital scalability  | $100M+ | Ethena TVL exceeds $3B                              |

## Latency Profile

| Segment                     | p50 Target | p99 Target | Co-location Needed? |
| --------------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature      | 100ms      | 500ms      | No                  |
| Feature -> signal           | 1ms        | 5ms        | No                  |
| Signal -> instruction       | 1ms        | 5ms        | No                  |
| Instruction -> fill (stake) | 2s         | 30s        | No (on-chain)       |
| **End-to-end**              | **~3s**    | **~31s**   | **No**              |

Latency is irrelevant for a benchmark. The strategy deploys once and then does nothing.

## Execution Details

- **Venues:** Ethena (Ethereum mainnet)
- **Order types:** TRANSFER + STAKE (protocol interactions, not order book)
- **Atomic execution required?** No -- two sequential transactions
- **Gas budget:** ~200k gas total (TRANSFER ~100k + STAKE ~100k)

### Rebalancing

**No rebalancing.** This is a passive benchmark. All rebalancing thresholds are set to 100% (effectively disabled):

```python
"thresholds": {
    "minor":    {"position_deviation_pct": 100.0, "action": "log_only"},
    "major":    {"position_deviation_pct": 100.0, "action": "log_only"},
    "critical": {"position_deviation_pct": 100.0, "action": "log_only"},
}
```

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern                     | Exposure Type          | Used For        |
| -------------------------------------- | ---------------------- | --------------- |
| `ETHENA-ETHEREUM:YIELD_BEARING:SUSDE*` | Yield-bearing position | Yield tracking  |
| `WALLET:SPOT_ASSET:USDT`               | Wallet balance         | Pre-deploy only |

### Risk Type Subscriptions

| Risk Type       | Subscribed? | Notes                             |
| --------------- | ----------- | --------------------------------- |
| `protocol_risk` | YES         | Ethena depeg or sUSDe rate freeze |
| All others      | NO          | No leverage, no debt, no hedging  |

## Margin & Liquidation

- **Margin model:** None -- fully funded single position
- **Liquidation risk:** Zero (no debt, no collateral relationship)
- **Protocol risk:** Ethena backing mechanism failure (delta-neutral synthetic dollar) -- tail risk only
- **Smart contract risk:** Ethena contracts are audited; protocol risk from USDe depegging

## Authentication & Credentials

| Venue            | Secret Name                   | Testnet Available? | Notes                           |
| ---------------- | ----------------------------- | ------------------ | ------------------------------- |
| Ethena (via RPC) | `alchemy-api-key`             | Yes (Sepolia)      | Read: public. Write: wallet key |
| Wallet           | `wallet-{client}-private-key` | Yes (dev wallet)   | Signs TRANSFER + STAKE txns     |

## Factory Function

```python
from strategy_service.engine.strategies.defi_ethena_benchmark import (
    create_ethena_benchmark_strategy,
)

# Create default Ethena benchmark (USDT supply token)
strategy = create_ethena_benchmark_strategy(supply_token="USDT")

# Strategy ID: DEFI_ETH_YLD_ETHENA_SUSDE_USDT_BENCH_1H
```

### Config Parameters

| Parameter      | Type | Default | Description                                  |
| -------------- | ---- | ------- | -------------------------------------------- |
| `supply_token` | str  | `USDT`  | Token to convert to USDe then stake to sUSDe |

## Benchmark Comparison Usage

All active DeFi strategies reference the Ethena benchmark via `benchmark_config.comparison_benchmark`:

```yaml
benchmark_config:
  comparison_benchmark: ETHENA_SUSDE_APY
```

The batch orchestrator runs the benchmark alongside active strategies for side-by-side P&L comparison:

```bash
python -m strategy_service --operation batch \
  --strategy AAVE_LENDING,BASIS_TRADE,RECURSIVE_STAKED_BASIS,ETHENA_BENCHMARK \
  --start-date 2026-03-22 --end-date 2026-03-29
```

Every `DeFiSignal` includes `ethena_benchmark_apy` for real-time alpha measurement:

```
strategy_alpha = strategy_expected_apy - ethena_benchmark_apy
```

## Testing Stage Status

| Stage        | Status        | Notes                                             |
| ------------ | ------------- | ------------------------------------------------- |
| MOCK         | Code complete | Deterministic -- always deploys, always holds     |
| HISTORICAL   | Code complete | sUSDe exchange rate history from on-chain data    |
| LIVE_MOCK    | Code complete | Features provide susde_exchange_rate in mock mode |
| LIVE_TESTNET | Code complete | Ethena on Sepolia testnet                         |
| BATCH_REAL   | Code complete | 7-day validated run alongside active strategies   |
| STAGING      | Code complete | Tenderly fork execution                           |
| LIVE_REAL    | Code complete | Deployed as comparison benchmark                  |

## Wallet & Capital Flow

| Component        | Value                                 |
| ---------------- | ------------------------------------- |
| Treasury reserve | 20% of AUM                            |
| Hot wallet       | Per-chain, per-strategy isolated      |
| CeFi sub-account | No                                    |
| Bridge required  | No (single-chain -- Ethereum mainnet) |
| Custody          | Copper MPC                            |

Capital flow: Client deposit --> treasury --> hot wallet --> TRANSFER to Ethena --> STAKE USDe to sUSDe. Hold forever.
Simplest capital flow of all DeFi strategies -- deploy once, no rebalancing. See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked via Alchemy RPC using `eth_feeHistory`. For this benchmark, gas is paid only once on the initial
TRANSFER + STAKE deployment (~200k gas total, ~$18 at 30 gwei). Since the benchmark never rebalances, gas is a trivial
one-time cost. Gas hits P&L immediately as a realized transaction cost.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Instrument Filtering

Ethena sUSDe is a yield-bearing token with a curated instrument set (1-3 instruments). Per
[instrument-filtering.md](../../operational/instrument-filtering.md), LST/yield protocols have **no filtering needed**
-- the adapter returns all instruments.

## E2E Manual Trading Workflow

Step-by-step manual recreation of the Ethena sUSDe benchmark. Simplest DeFi strategy: buy sUSDe and hold forever. No
rebalancing, no exit, no active decisions after initial deployment.

### Prerequisites

- Treasury wallet funded with USDC on Ethereum
- Trading wallet created (per-strategy, per-chain)
- Alchemy RPC configured for Ethereum

### Step-by-Step

| Step | Action                                              | Instruction Type | Service                                      | Instant P&L                                |
| ---- | --------------------------------------------------- | ---------------- | -------------------------------------------- | ------------------------------------------ |
| 1    | Observe treasury balance                            | --               | position-balance-monitor (treasury_monitor)  | --                                         |
| 2    | Transfer $100K USDC from treasury to trading wallet | TRANSFER         | execution-service (custody provider)         | Gas: ~$2                                   |
| 3    | Swap USDC to USDe (if wallet holds USDC, not USDe)  | SWAP             | execution-service (UniswapConnector via SOR) | Gas: ~$8. Slippage: ~$2.00 (2bps on $100K) |
| 4    | Stake USDe to sUSDe via Ethena staking contract     | STAKE            | execution-service (EthenaConnector)          | Gas: ~$5                                   |
| 5    | Verify sUSDe balance in trading wallet              | --               | position-balance-monitor                     | sUSDe balance = USDe / exchange_rate       |

### Position State After Deployment

- Trading wallet: sUSDe (yield-bearing, appreciates via exchange rate)
- No debt, no perp, no hedge
- Single position, single chain
- Never exits (benchmark -- hold forever)

### Instant P&L Decomposition

| Component                  | Amount      | Notes                                               |
| -------------------------- | ----------- | --------------------------------------------------- |
| Gas (steps 2-4)            | -$15.00     | 3 on-chain txns (transfer + swap + stake)           |
| Swap slippage USDC to USDe | -$2.00      | ~2bps on $100K, USDC/USDe is near-peg pair          |
| **Total entry cost**       | **-$17.00** |                                                     |
| Gross instant P&L          | $0          | actual_output - expected_output (perfect execution) |
| Net instant P&L            | -$17.00     | gross - all costs                                   |

Strategy instruction carries `benchmark_price` (USDe oracle price at signal time) and `max_slippage_bps` (5bps for
stablecoin swap). Execution-service rejects if slippage exceeds threshold.

### Ongoing P&L (Daily)

- sUSDe yield: ~9.8% APY on $100K = ~$26.85/day (accrues via exchange rate appreciation)
- No borrow cost, no funding, no rebalancing cost
- **Daily income: ~$26.85/day**
- Cost recovery: <1 day

### Risk Metrics

- USDe depeg: tail risk (Ethena delta-neutral backing mechanism failure)
- Ethena protocol risk: smart contract exploit, governance failure
- No liquidation risk (no debt, no collateral)
- No delta risk (single stablecoin position)
- Health Factor: N/A

### Exit Workflow

The benchmark never exits automatically. If a manual exit is needed:

| Step | Action                                           | Instruction Type | Instant P&L                       |
| ---- | ------------------------------------------------ | ---------------- | --------------------------------- |
| 1    | Unstake sUSDe to USDe (may have cooldown period) | UNSTAKE          | Gas: ~$5                          |
| 2    | Swap USDe to USDC                                | SWAP             | Gas: ~$8. Slippage: ~$2.00 (2bps) |
| 3    | Transfer USDC from trading wallet to treasury    | TRANSFER         | Gas: ~$2                          |
|      | **Total exit cost**                              |                  | **~$17.00**                       |

### Service Interaction Diagram

```
User (UI)
  |
  +---> position-balance-monitor: read treasury balance
  +---> execution-service: TRANSFER USDC (custody signs tx)
  +---> execution-service: SWAP USDC->USDe (SOR, near-peg pair)
  +---> execution-service: STAKE USDe->sUSDe (Ethena staking contract)
  +---> position-balance-monitor: read sUSDe balance
  +---> pnl-attribution-service: compute exchange_rate_yield_pnl
  +---> [no risk service needed -- no leverage, no delta, no debt]
```

### Trade History (Expected Output)

| #   | Time   | Type     | Instrument  | Amount       | Price        | Gas   | Slippage | Running P&L |
| --- | ------ | -------- | ----------- | ------------ | ------------ | ----- | -------- | ----------- |
| 1   | 10:01  | TRANSFER | USDC        | 100,000      | $1.00        | $2.00 | $0       | -$2.00      |
| 2   | 10:02  | SWAP     | USDC->USDe  | 100,000      | $1.00        | $8.00 | $2.00    | -$12.00     |
| 3   | 10:03  | STAKE    | USDe->sUSDe | 100,000 USDe | $1.00        | $5.00 | $0       | -$17.00     |
| 4   | EOD    | YIELD    | sUSDe       | +$26.85      | rate +0.027% | $0    | $0       | +$9.85      |
| 5   | Day 2  | YIELD    | sUSDe       | +$26.85      | rate +0.027% | $0    | $0       | +$36.70     |
| 6   | Day 7  | YIELD    | sUSDe       | +$26.85      | rate +0.027% | $0    | $0       | +$170.95    |
| 7   | Day 30 | YIELD    | sUSDe       | +$26.85      | rate +0.027% | $0    | $0       | +$788.50    |

Note: the benchmark holds forever -- row 7 and beyond continue indefinitely with no exit.

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/defi_ethena_benchmark.py`
- **Factory:** `create_ethena_benchmark_strategy()`
- **Config schema:** `strategy-service/docs/STRATEGY_MODES.md`
- **Ethena protocol:** [ethena.fi](https://ethena.fi) -- sUSDe staking vault
- **Settlement:** `strategy-service/strategy_service/engine/core/settlement_service.py`
- **PnL calculator:** `strategy-service/strategy_service/engine/core/pnl_calculator.py`
