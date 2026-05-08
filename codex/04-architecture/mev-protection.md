---
scope: [engineer, admin]
---

# MEV Protection

## What Is MEV?

Miner/Maximal Extractable Value (MEV) refers to profits extracted by block producers (miners, validators) or searchers
by reordering, inserting, or censoring transactions within a block. For DeFi trading strategies, MEV manifests as:

- **Front-running**: A searcher sees a pending swap and inserts a transaction before it, moving the price against the
  strategy.
- **Sandwich attacks**: A searcher inserts a buy before and a sell after a pending swap, profiting from the price
  impact.
- **Back-running**: A searcher executes immediately after a large transaction to capture favorable price.
- **Liquidation sniping**: A searcher monitors under-collateralised positions and submits liquidation transactions at
  the optimal gas price.

## How the System Protects Against MEV

### 1. Slippage Tolerance + Price Impact Checks (Uniswap swaps)

All Uniswap swaps via `UniswapConnector.swap_exact_input()` enforce a `slippage_tolerance_bps` parameter. This sets the
`amountOutMinimum` in the `exactInputSingle` call:

```python
amount_out_minimum = int(quote_amount_out * (1 - slippage_tolerance / 10000))
params["amountOutMinimum"] = amount_out_minimum
```

Default: `20 bps` (0.2%). If a sandwich attack moves the price beyond 0.2%, the transaction reverts on-chain and the
`TX_REVERTED` error code is returned.

For large EIGEN/ETHFI reward sells, a tighter tolerance (10 bps) is recommended to reduce sandwich attack exposure.

### 2. Flashbots / Private Mempool (Production Configuration)

For high-value swaps (above `MEV_PROTECTION_THRESHOLD_USD`, default $10,000), the execution-service routes through a
private RPC endpoint rather than the public mempool. This prevents searchers from seeing the transaction before it is
included in a block.

**Configuration** (via `execution_service/config/chain_config.yaml`):

```yaml
mev_protection:
  enabled: true
  threshold_usd: 10000
  private_rpc_url: "https://rpc.flashbots.net" # fetched from Secret Manager
  fallback_to_public: false # fail loud if private RPC unavailable
```

Private RPC endpoints by chain:

- Ethereum mainnet: Flashbots `https://rpc.flashbots.net`
- Arbitrum: No dedicated Flashbots; use `arb_sequencer_rpc` (sequencer = centralized, no mempool MEV)
- Base/Optimism: L2 sequencers are centralised — no mempool-based MEV

### 3. Gas Price Strategy

Execution-service uses `GasPriceAdapter` to set competitive gas prices without overpaying. For time-sensitive
transactions (reward claims, liquidation-avoidance rebalancing):

```python
gas_price = gas_adapter.get_fast_gas_price()  # EIP-1559: maxFeePerGas + maxPriorityFeePerGas
```

Overpaying gas is itself an MEV vector (priority gas auctions). The adapter caps `maxPriorityFeePerGas` at 3 gwei for
non-urgent transactions.

### 4. L2 Deployment (Structural MEV Reduction)

DeFi strategies prefer L2 venues (Arbitrum, Base) where possible:

- Centralised sequencers eliminate front-running from mempool observers
- Gas costs are 10-100x cheaper, making small rebalances economical
- Reward selling on Arbitrum Uniswap V3 has near-zero MEV exposure

The `CrossChainSORStrategy` factors in MEV risk as part of venue selection:

- L2 venues get a lower effective slippage estimate vs Ethereum mainnet
- Bridge costs must be less than MEV savings for cross-chain routing to be worth it

### 5. On-Chain Simulation (Pre-flight via Tenderly)

Before submitting high-value transactions, execution-service pre-simulates via the Tenderly fork connector:

```python
simulation_result = tenderly_fork.simulate_transaction(tx_params)
if simulation_result.reverted:
    raise DeFiError(DefiErrorCode.TX_REVERTED, simulation_result.revert_reason)
```

This catches slippage violations, insufficient collateral, and other revert conditions without wasting gas on a failed
on-chain transaction.

## Error Codes (MEV-Related)

From `execution_service.defi_execution.protocols.aave.DefiErrorCode`:

| Code                | Cause                             | Action                              |
| ------------------- | --------------------------------- | ----------------------------------- |
| `SLIPPAGE_EXCEEDED` | Sandwich attack / high volatility | RETRY with wider tolerance or delay |
| `TX_REVERTED`       | Generic revert (includes MEV)     | RETRY once, then SKIP               |
| `GAS_PRICE_SPIKE`   | Gas auction / network congestion  | RETRY after 30s                     |

## Strategy Config (MEV-Related Fields)

```yaml
# In e2e-testing/configs/defi/strategies/*.yaml
slippage_tolerance_bps: 20 # 0.2% — tighter = more MEV protection but more reverts
gas_price_gwei: 30 # Max gas price willing to pay
mev_protection_threshold_usd: 10000 # Use private RPC above this size
```

## Key Files

| File                                                    | Purpose                                               |
| ------------------------------------------------------- | ----------------------------------------------------- |
| `execution_service/defi_execution/protocols/uniswap.py` | `swap_exact_input()` with slippage guard              |
| `execution_service/defi_execution/protocols/aave.py`    | `DefiErrorCode` enum with SLIPPAGE_EXCEEDED           |
| `execution_service/defi_execution/gas_price_adapter.py` | EIP-1559 gas price strategy                           |
| `execution_service/defi_execution/protocols/bridge.py`  | `SocketBridgeConnector` for cross-chain MEV avoidance |
| `execution_service/config/chain_config.yaml`            | MEV protection threshold + private RPC config         |

## Related Docs

- `codex/04-architecture/tenderly-execution-provider.md` — Pre-flight simulation
- `codex/04-architecture/defi-execution-overview.md` — Full execution flow
- `codex/04-architecture/execution-modes-and-chain-resolution.md` — Chain environment resolution
