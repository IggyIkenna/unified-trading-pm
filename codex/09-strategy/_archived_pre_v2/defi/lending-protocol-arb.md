---
scope: [engineer, admin]
---

# Lending Protocol Arbitrage

> **Asset class:** DeFi **Strategy type:** Arbitrage (cross-protocol APY spread capture on same chain) **Strategy ID
> pattern:** `DEFI_LENDING_ARB_{CHAIN}_{TOKEN}_SCE_1H`

## Overview

Captures the APY spread between lending protocols on the same chain by borrowing cheap on one protocol and lending
expensive on another. For example, borrow USDC on Compound V3 at 3% and supply USDC to Aave V3 at 5%, netting a 2%
annualized spread. Uses rate impact simulation (UAC `simulate_rate_impact`) to ensure spreads persist after our trade
size, and flash-loan-assisted atomic rebalancing when the optimal pair shifts.

## Token / Position Flow

```
Start:  WALLET:SPOT_ASSET:USDC  (100% USDC)

Step 1 - SCAN:       Query supply_apy and borrow_apy across all protocols on chain
                     (Aave V3, Morpho Blue, Compound V3)
Step 2 - SIMULATE:   Run rate impact model per protocol to project post-trade APYs
Step 3 - SELECT:     Pick (borrow_protocol, supply_protocol) pair with max net spread
Step 4 - DEPOSIT:    Supply USDC as collateral on borrow_protocol
Step 5 - BORROW:     Borrow USDC from borrow_protocol (60% LTV)
Step 6 - LEND:       Supply borrowed USDC to supply_protocol

Wallet after deploy:
  - {BORROW_VENUE}:A_TOKEN:AUSDC@{CHAIN}   = collateral_amount (collateral)
  - {BORROW_VENUE}:DEBT_TOKEN:DEBTUSDC@{CHAIN} = borrow_amount (debt)
  - {SUPPLY_VENUE}:A_TOKEN:AUSDC@{CHAIN}   = borrow_amount (yield-bearing)

On flash-loan-assisted rebalance:
Step 7 - FLASH_BORROW: Flash borrow from Morpho (zero fee)
Step 8 - REPAY:        Repay old borrow position
Step 9 - WITHDRAW:     Withdraw from old supply position
Step 10 - LEND:        Supply to new best protocol
Step 11 - BORROW:      Borrow from new cheapest protocol
Step 12 - FLASH_REPAY: Repay flash loan

Recursive staking variant:
Step 1 - DEPOSIT:    Supply wstETH as collateral on borrow_protocol
Step 2 - BORROW:     Borrow USDC against wstETH (60% LTV)
Step 3 - LEND:       Supply USDC on supply_protocol
```

## Instruments

| Instrument Key                                   | Venue       | Type       | Role                    |
| ------------------------------------------------ | ----------- | ---------- | ----------------------- |
| `WALLET:SPOT_ASSET:USDC`                         | Wallet      | Spot       | Initial capital         |
| `AAVEV3-{CHAIN}:A_TOKEN:AUSDC@{CHAIN}`           | Aave V3     | aToken     | Collateral / supply     |
| `AAVEV3-{CHAIN}:DEBT_TOKEN:DEBTUSDC@{CHAIN}`     | Aave V3     | debtToken  | Borrow position         |
| `MORPHO-{CHAIN}:A_TOKEN:AUSDC@{CHAIN}`           | Morpho      | mToken     | Collateral / supply     |
| `MORPHO-{CHAIN}:DEBT_TOKEN:DEBTUSDC@{CHAIN}`     | Morpho      | debtToken  | Borrow position         |
| `COMPOUNDV3-{CHAIN}:A_TOKEN:AUSDC@{CHAIN}`       | Compound V3 | cToken     | Collateral / supply     |
| `COMPOUNDV3-{CHAIN}:DEBT_TOKEN:DEBTUSDC@{CHAIN}` | Compound V3 | debtToken  | Borrow position         |
| `MORPHO:FLASH_LOAN:USDC@{CHAIN}`                 | Morpho      | Flash loan | Atomic rebalance source |

## Key Features Consumed

| Feature                       | Source Service   | SLA | Used For                              |
| ----------------------------- | ---------------- | --- | ------------------------------------- |
| `{protocol}_supply_apy`       | features-onchain | 60s | Signal: identify best supply protocol |
| `{protocol}_borrow_apy`       | features-onchain | 60s | Signal: identify cheapest borrow      |
| `{protocol}_total_supply_usd` | features-onchain | 60s | Rate impact: pool size for simulation |
| `{protocol}_total_borrow_usd` | features-onchain | 60s | Rate impact: utilization calculation  |
| `health_factor`               | features-onchain | 30s | Risk: emergency exit trigger          |

## PnL Attribution

| Component          | Settlement Type | Mechanism                                              |
| ------------------ | --------------- | ------------------------------------------------------ |
| `spread_yield_pnl` | `RATE_ACCRUAL`  | Supply APY earned minus borrow APY paid                |
| `flash_loan_cost`  | Per-rebalance   | Flash loan fee (0 for Morpho, 0.05% for Aave)          |
| `gas_costs`        | Per-transaction | Gas for deposit + borrow + supply + rebalance on-chain |
| `rate_drift_drag`  | Mark-to-market  | Spread compression between evaluation and execution    |

**Source of truth:** `total_pnl = equity_current - equity_initial` (balance-based). All attribution components must sum
to match within 2% annualized tolerance.

## Risk Profile

| Metric               | Target | Notes                                                    |
| -------------------- | ------ | -------------------------------------------------------- |
| Target annual return | 2-6%   | Pure spread capture, no directional exposure             |
| Target Sharpe ratio  | 2.0+   | Stable spreads with known cost structure                 |
| Max drawdown         | 3%     | Spread compression + flash loan fees during rapid shifts |
| Max leverage         | 3x     | Conservative LTV (60%) with HF monitoring                |
| Capital scalability  | $20M   | Rate impact limits size per protocol pool                |

## Latency Profile

| Segment                | p50 Target | p99 Target | Co-location Needed? |
| ---------------------- | ---------- | ---------- | ------------------- |
| Market data -> feature | 150ms      | 800ms      | No                  |
| Feature -> spread calc | 20ms       | 100ms      | No                  |
| Spread -> signal       | 10ms       | 50ms       | No                  |
| Signal -> instruction  | 5ms        | 20ms       | No                  |
| Instruction -> fill    | 3s         | 30s        | No (on-chain)       |
| **End-to-end**         | **~4s**    | **~31s**   | **No**              |

Not latency-sensitive. APY spreads shift over minutes/hours driven by utilization changes. Flash loans execute
atomically within a single block.

## Execution Details

- **Venues:** Aave V3, Morpho Blue, Compound V3 (all on same chain)
- **Order types:** Deposit, Borrow, Supply, Withdraw, Repay, Flash Loan
- **Atomic execution required?** Yes for rebalancing (flash-loan-assisted); No for initial deploy
- **Rebalancing:** When a different protocol pair offers > 1.5% better net spread
- **Gas budget:** ~300k gas for deploy (3 txns), ~500k for flash rebalance (6 operations in 1 txn on flash loan)

## Risk & Exposure Subscriptions

### Exposure Subscriptions

| Instrument Pattern        | Exposure Type   | Used For                      |
| ------------------------- | --------------- | ----------------------------- |
| `*:A_TOKEN:AUSDC@*`       | Supply position | Yield tracking                |
| `*:DEBT_TOKEN:DEBTUSDC@*` | Borrow position | Cost tracking, HF calculation |
| `WALLET:SPOT_ASSET:USDC`  | Wallet balance  | Available capital             |

### Risk Type Subscriptions

| Risk Type          | Subscribed? | Threshold       | Action on Breach        |
| ------------------ | ----------- | --------------- | ----------------------- |
| `protocol_risk`    | YES         | Utilization>95% | Emergency withdraw      |
| `aave_liquidation` | YES         | HF < 1.3        | Emergency exit all      |
| `rate_compression` | YES         | Spread < 0.5%   | Orderly exit            |
| `delta`            | NO          | --              | No directional exposure |
| `funding`          | NO          | --              | No perp positions       |
| `bridge_risk`      | NO          | --              | Same-chain only         |

## Margin & Liquidation

- **Margin model:** Health Factor (DeFi lending protocol native)
- **Health factor threshold:** 1.3 minimum before emergency exit
- **Liquidation penalty:** Protocol-specific (5% Aave, varies Compound/Morpho)
- **Monitoring:** Health factor checked every candle (1h) and on every rebalance decision
- **Conservative LTV:** 60% target vs 80%+ max to maintain safety buffer

## Authentication & Credentials

| Venue                 | Secret Name                   | Testnet Available? | Notes                  |
| --------------------- | ----------------------------- | ------------------ | ---------------------- |
| Aave V3 (via RPC)     | `alchemy-api-key`             | Yes (Sepolia)      | RPC for all EVM chains |
| Compound V3 (via RPC) | `alchemy-api-key`             | Yes (Sepolia)      | Same RPC provider      |
| Morpho (via RPC)      | `alchemy-api-key`             | Yes (Sepolia)      | Same RPC provider      |
| Wallet                | `wallet-{client}-private-key` | Yes (dev wallet)   | Signs all transactions |

## Client Onboarding

See [cross-cutting/client-onboarding.md](../cross-cutting/client-onboarding.md) for the standard flow.

**Strategy-specific:**

1. Wallet per client (capital isolation)
2. No venue accounts needed (all protocols are permissionless)
3. Config: `supply_token`, `min_spread_threshold` (default 1.5%), `exit_spread_threshold` (default 0.5%),
   `use_flash_loans` (default true), `protocols_to_scan`, `recursive_staking_enabled` (default false)
4. **Restart required?** No -- hot-reload via GCS config

## UI Visualisation

### Standard views

- PnL waterfall, position breakdown
- Health factor time series with liquidation threshold line

### Strategy-specific views

- **Protocol spread matrix** -- supply APY vs borrow APY per protocol, highlight active pair
- **Rate impact waterfall** -- pre-trade vs post-trade APY projections
- **Spread time series** -- historical net spread with entry/exit threshold lines
- **Flash loan event log** -- rebalance events with old/new pair, cost, and spread improvement

## Testing Stage Status

| Stage        | Status  | Notes                                                    |
| ------------ | ------- | -------------------------------------------------------- |
| MOCK         | Pending | Static seed data + paper execution                       |
| HISTORICAL   | Pending | Need historical per-protocol APYs (The Graph archives)   |
| LIVE_MOCK    | Pending | Blocked by features-onchain multi-protocol APY pipeline  |
| LIVE_TESTNET | Pending | Aave V3 + Compound V3 on Sepolia; Morpho testnet limited |
| BATCH_REAL   | Pending | Need >90 days of multi-protocol APY history              |
| STAGING      | Pending | Tenderly fork with flash loan testing                    |
| LIVE_REAL    | Pending | All above + capital approval                             |

## References

- **Implementation:** `strategy-service/strategy_service/engine/strategies/lending_protocol_arb.py`
- **Rate impact model:** `unified-api-contracts/unified_api_contracts/internal/domain/defi/rate_model.py`
- **Flash loan infra:** `execution-service/protocols/aave.py` (flash loan execution)
- **Config (ETH):** `strategy-service/strategy_service/configs/lending_arb_eth.yaml`
- **Config (ARB):** `strategy-service/strategy_service/configs/lending_arb_arbitrum.yaml`
- **DeFi base strategy:** `strategy-service/strategy_service/engine/strategies/defi_base.py`
- **Aave connector:** `execution-service/protocols/aave.py`
- **Compound connector:** `execution-service/protocols/compound.py`
- **Morpho connector:** `execution-service/protocols/morpho.py`
