---
scope: [engineer, admin]
---

# Omnichain Transfers Strategy

> **Asset class:** DeFi **Strategy type:** Cross-chain infrastructure (bridge routing, not yield) **Phase:** 2E

## Overview

Cross-chain asset movement via bridge protocols. This is NOT a yield strategy -- it is infrastructure for multi-chain
deployment. Other strategies (multi-chain lending, cross-chain yield arb, L2 basis trade) depend on omnichain transfers
to move capital between chains.

## Architecture

- TRANSFER instruction with chain routing: Ethereum -> Arbitrum -> Base
- Multi-leg execution (NOT atomic -- bridge confirmation wait required)
- Bridge cost model: gas + bridge fee + time estimate
- Strategy emits transfer instructions; execution-service handles bridge protocol interaction

## Bridge Protocols

| Protocol      | Type                    | Finality        | Notes                                                   |
| ------------- | ----------------------- | --------------- | ------------------------------------------------------- |
| **Socket**    | Multi-bridge aggregator | Route-dependent | Finds cheapest route across Across, Stargate, Hop, etc. |
| **LayerZero** | Direct message passing  | ~2-10 min       | OFT standard for token transfers                        |
| **Across**    | Optimistic bridge       | ~2 min          | Fast finality via optimistic verification               |

## Instruction Flow

1. Strategy emits TRANSFER instruction: `from_chain=ETHEREUM, to_chain=ARBITRUM, token=USDC, amount=X`
2. Execution-service routes to bridge handler based on `bridge_protocol` config
3. Bridge handler: approve token -> initiate bridge -> wait for confirmation -> verify receipt
4. Position-balance-monitor tracks cross-chain: same wallet address, multiple chains

Each step is logged as a separate event. The strategy does NOT poll for completion -- execution-service publishes a
`BRIDGE_COMPLETE` event when the destination chain confirms receipt.

## Cost Model

| Route            | Gas (source) | Bridge Fee | Time     |
| ---------------- | ------------ | ---------- | -------- |
| ETH -> Arbitrum  | ~$2-5        | 0.01-0.05% | 2-15 min |
| ETH -> Base      | ~$2-5        | 0.01-0.05% | 2-15 min |
| ETH -> Optimism  | ~$2-5        | 0.01-0.05% | 2-15 min |
| Arbitrum -> Base | ~$0.10       | 0.01-0.05% | 2-10 min |

Gas costs are L1-dominated for L1->L2 routes. L2->L2 routes are significantly cheaper due to low L2 gas.

## Cross-Chain Position Tracking

- Same EOA wallet on all EVM chains
- Position-balance-monitor polls per-chain balances via chain-specific RPC endpoints
- Consolidated view: `total_balance = sum(chain_balances)`
- Chain allocation weights tracked for rebalancing decisions
- In-flight capital (mid-bridge) tracked as `PENDING_BRIDGE` position type with timeout alert

## Config

| Parameter             | Type      | Default    | Description                                       |
| --------------------- | --------- | ---------- | ------------------------------------------------- |
| `bridge_protocol`     | str       | `"socket"` | `"socket"` / `"layerzero"` / `"across"`           |
| `destination_chains`  | list[str] | `[]`       | Target chains: `["ARBITRUM", "BASE", "OPTIMISM"]` |
| `max_bridge_fee_bps`  | int       | `10`       | Max 0.1% bridge fee tolerance                     |
| `min_transfer_amount` | float     | `1000`     | Don't bridge dust amounts                         |
| `bridge_timeout_s`    | int       | `1800`     | Alert if bridge not confirmed in 30 min           |

## Risk

| Risk                       | Severity | Mitigation                                               |
| -------------------------- | -------- | -------------------------------------------------------- |
| Bridge smart contract risk | HIGH     | Use only audited protocols (Socket, LayerZero, Across)   |
| Finality delay             | MEDIUM   | Strategy accounts for in-flight capital; no double-spend |
| Gas price volatility       | LOW      | Gas estimation with buffer; abort if gas > threshold     |
| Bridge censorship          | LOW      | Multiple bridge protocols as fallback                    |

## Wallet & Capital Flow

| Component        | Value                                                    |
| ---------------- | -------------------------------------------------------- |
| Treasury reserve | 20% of AUM (managed by parent strategy)                  |
| Hot wallet       | Multi-chain (one per destination chain)                  |
| CeFi sub-account | No                                                       |
| Bridge required  | Yes (core function -- this IS the bridge infrastructure) |
| Custody          | Copper MPC                                               |

Capital flow: treasury-ETH --> BRIDGE (Socket/LayerZero/Across) --> treasury-DEST --> hot-wallet-DEST. In-flight capital
tracked as `PENDING_BRIDGE` position type with 30-minute timeout alert. Same EOA wallet address on all EVM chains
(deterministic derivation). See
[wallet-hierarchy-and-capital-flow.md](../../../04-architecture/wallet-hierarchy-and-capital-flow.md).

## Gas Fee Tracking

Gas costs are tracked per-chain via Alchemy RPC:

- **EVM chains**: `eth_feeHistory` for real-time gas prices on all 19 supported EVM mainnets
- **Solana**: `getRecentPrioritizationFees` for priority fee estimation
- **BTC**: `estimatesmartfee` for fee-rate estimation

The MTDS `gas_fee_handler` fetches gas prices and writes them as features. Gas hits P&L immediately as a realized
transaction cost -- not estimated. Gas cost is a key component of the bridge cost model:
`total_bridge_cost = source_gas + bridge_protocol_fee + destination_gas`.

**Reference:** `market-tick-data-service/market_tick_data_service/gas_fee_handler.py`

## Multi-Chain Support

All 19 EVM mainnets plus Solana are supported for transfers. All chains have Alchemy RPC endpoints configured via
`CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py` (12 EVM mainnets + 10 testnets + Solana
mainnet/devnet + BTC). Gas token balances (ETH, MATIC, AVAX, BNB, SOL, etc.) are tracked per chain via
`GasTokenBalanceTracker`.

## Instrument Filtering

This is infrastructure, not a yield strategy -- instrument filtering is handled by the parent strategies (lending,
basis, yield arb) that consume omnichain transfers. See
[instrument-filtering.md](../../operational/instrument-filtering.md).

## Bridge Costs

Bridge cost is a **one-time P&L hit** per transfer -- not amortized. The fee is deducted from principal at the time of
the bridge transaction. Across API provides live fee quotes for supported routes; static estimates from historical
averages serve as fallback when the API is unavailable. Parent strategies (lending, basis, yield arb) check whether the
yield improvement on the target chain recovers the bridge cost within the expected holding period before requesting a
transfer.

## Implementation

**Source:** `strategy-service/strategy_service/engine/strategies/omnichain_transfer.py`

**Class:** `OmnichainTransferStrategy` extends `DeFiBaseStrategy`

**Factory:** `create_omnichain_transfer_strategy(token="USDC", source_chain="ETHEREUM")`

**Config:** `strategy-service/strategy_service/configs/omnichain_transfer.yaml`

**Registered in:** `batch_utils.py` as `OMNICHAIN_TRANSFER` strategy type

### Key Methods

| Method                        | Purpose                                                        |
| ----------------------------- | -------------------------------------------------------------- |
| `generate_signal()`           | Batch mode: evaluates gas differentials across chains          |
| `generate_defi_signal()`      | Emits TRANSFER instructions to rebalance chain allocation      |
| `generate_transfer_signal()`  | Composable API: parent strategies call this to request bridges |
| `create_bridge_instruction()` | Builds a single TRANSFER instruction with bridge metadata      |
| `mark_transfer_complete()`    | Called on BRIDGE_COMPLETE event to update pending state        |

### Composable Usage

Parent strategies invoke `generate_transfer_signal()` directly:

```python
transfer_strategy = create_omnichain_transfer_strategy(token="USDT")
signal = transfer_strategy.generate_transfer_signal(
    timestamp=now,
    token="USDT",
    amount=Decimal("50000"),
    from_chain="ETHEREUM",
    to_chain="ARBITRUM",
)
# signal.instructions contains a single TRANSFER instruction
# execution-service routes to BridgeConnector (Socket API)
```

## References

- **RPC URL templates:** `CHAIN_RPC_TEMPLATES` in UAC `registry/capability_declarations/_defi.py`
- **Bridge connector:** `execution-service/execution_service/defi_execution/protocols/bridge.py`
- **Position tracking:** `position-balance-monitor-service/` (cross-chain balances)
- **Related strategies:** [multi-chain-lending-yield.md](multi-chain-lending-yield.md),
  [cross-chain-yield-arb.md](cross-chain-yield-arb.md), [l2-basis-trade.md](l2-basis-trade.md)
