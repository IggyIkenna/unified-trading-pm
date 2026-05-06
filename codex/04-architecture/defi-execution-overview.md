---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# DeFi Execution Overview

## Live Execution Flow

```
Strategy emits ExecutionInstruction
    ↓
execution-service routes by operation type:
    TRADE    → execution-service (CeFi adapters, CCXT, Hyperliquid/Aster)
    LEND     → execution-service DeFi AAVEConnector.supply()
    BORROW   → execution-service DeFi AAVEConnector.borrow()
    REPAY    → execution-service DeFi AAVEConnector.repay()
    SWAP     → execution-service DeFi UniswapConnector.swap_exact_input()
    STAKE    → execution-service DeFi LidoConnector / EtherFiConnector
    FLASH_*  → execution-service DeFi AAVEConnector.flash_loan()
    ↓
execution-service fetches credentials from SM:
    wallet_private_key  → defi-wallet-private-key
    alchemy_api_key     → alchemy-api-key
    ↓
Resolves RPC URL from UAC CHAIN_RPC_TEMPLATES[chain_id]
    ↓
Passes config dict to execution-service DeFi connector:
    config = {
        "wallet_private_key": pk,
        "rpc_url": resolved_url,
        "flash_loan_receiver": receiver_address,  # from UAC testnet_contracts
        "chain_id": 1,
        "paper_trade": False,
    }
    ↓
execution-service DeFi connector.connect(config):
    1. Initialize Web3 provider
    2. Derive wallet address from private key
    3. Resolve flash_loan_receiver from config or UAC registry
    4. Validate receiver on-chain (eth_getCode) — fail loud if missing
    ↓
execution-service DeFi connector executes:
    1. Build transaction (ABI encode)
    2. Sign with private key
    3. Broadcast via RPC
    4. Wait for receipt
    5. Return structured result with gas_used, tx_hash, error classification
```

## Supported Operations

| Operation     | Connector        | Contract                         | Gas Estimate        |
| ------------- | ---------------- | -------------------------------- | ------------------- |
| Supply (lend) | AAVEConnector    | Aave V3 Pool                     | 200K                |
| Borrow        | AAVEConnector    | Aave V3 Pool                     | 300K                |
| Repay         | AAVEConnector    | Aave V3 Pool                     | 200K                |
| Withdraw      | AAVEConnector    | Aave V3 Pool                     | 250K                |
| Flash loan    | AAVEConnector    | Aave V3 Pool + FlashLoanReceiver | 600K                |
| Swap          | UniswapConnector | SwapRouter02                     | 300K + 100K approve |
| Stake         | LidoConnector    | Lido stETH                       | 150K                |
| Unstake       | EtherFiConnector | EtherFi weETH                    | 200K                |

## Error Classification

Every on-chain revert maps to a structured error code with an action:

| Code                              | Action | When                    |
| --------------------------------- | ------ | ----------------------- |
| INSUFFICIENT_COLLATERAL           | FAIL   | Borrow exceeds LTV      |
| INSUFFICIENT_BALANCE              | FAIL   | Not enough tokens       |
| ASSET_NOT_SUPPORTED               | FAIL   | Token not in pool       |
| ZERO_AMOUNT                       | FAIL   | Amount must be > 0      |
| TX_REVERTED                       | FAIL   | Generic revert          |
| GAS_ESTIMATION_FAILED             | RETRY  | Node congestion         |
| SLIPPAGE_EXCEEDED                 | RETRY  | Price moved             |
| FLASH_LOAN_RECEIVER_INVALID       | FAIL   | Receiver not a contract |
| FLASH_LOAN_INSUFFICIENT_LIQUIDITY | FAIL   | Pool drained            |
| NO_OUTSTANDING_DEBT               | SKIP   | Nothing to repay        |
| NO_COLLATERAL_DEPOSITED           | FAIL   | Can't borrow            |

Error format: `ERROR_CODE: AAVE V3 transaction failed -- <raw message>`

## Modes

| Mode              | What happens                   | Contract needed?         |
| ----------------- | ------------------------------ | ------------------------ |
| Backtest          | In-memory simulation, no Web3  | No                       |
| Paper trade       | Signs tx but doesn't broadcast | No                       |
| Testnet (Sepolia) | Real chain, test tokens        | Yes (deployed)           |
| Fork (Tenderly)   | Mainnet state snapshot         | Yes (deploy per fork)    |
| Live (mainnet)    | Real execution, real money     | Yes (deployed, verified) |

## Slippage Protection

Uniswap swaps use on-chain slippage protection:

1. Quote via Quoter contract → `expectedAmountOut`
2. Apply tolerance: `minAmountOut = expected * (1 - slippage_bps / 10000)`
3. SwapRouter02 reverts if actual output < minAmountOut
4. Default: 50 bps (0.5%). Configurable via `config["max_slippage_bps"]`

## Integration Testing

Reusable fixtures in `execution-service/tests/integration/conftest.py`:

```python
async def test_my_defi_operation(self, aave_connector):
    result = await aave_connector.supply(token="USDC", amount=Decimal("100"))
    assert result["success"] is True
```

Fixtures handle: fork creation, wallet funding, receiver deployment, connector wiring, fork cleanup.

## New Operation Types

Two additional operation types for DeFi reward management:

| Operation      | Handler            | What It Does                                                                       | Gas Estimate               |
| -------------- | ------------------ | ---------------------------------------------------------------------------------- | -------------------------- |
| `CLAIM_REWARD` | RewardClaimHandler | On-chain reward claim from EigenLayer/EtherFi/Lido claim contracts.                | 150K                       |
| `SELL_REWARD`  | RewardSellHandler  | Swap reward tokens (EIGEN, ETHFI) to base currency via Binance spot or Uniswap V3. | 300K (on-chain) or 0 (CEX) |

Both operations are routed through the execution-service handler registry alongside existing operation types (TRADE,
LEND, BORROW, SWAP, etc.). The strategy emits `StrategyInstruction` with the appropriate operation type, and
execution-service dispatches to the correct handler.

**Trigger conditions:**

- `CLAIM_REWARD`: auto-triggered when accrued reward value >= $50. Max once per 24h per reward token.
- `SELL_REWARD`: auto-triggered when wallet reward token balance \* price >= $100. Sell venue configurable (default:
  Binance spot for liquid tokens, Uniswap V3 for on-chain-only tokens).

## MEV Protection Framework

Atomic bundles (flash loan entry/exit) are vulnerable to MEV extraction. Three interchangeable providers handle
protection based on the execution environment:

| Provider                 | Method                          | When Used                                                                             |
| ------------------------ | ------------------------------- | ------------------------------------------------------------------------------------- |
| `FlashbotsProvider`      | Relay submission                | Mainnet live execution. Bundles submitted via `eth_sendBundle` to Flashbots builders. |
| `PrivateMempoolProvider` | Flashbots Protect / MEV Blocker | L2 deployments. Routes via `rpc.mevblocker.io` or Flashbots Protect RPC.              |
| `NoProtectionProvider`   | Standard broadcast              | Batch, paper trade, testnet. No MEV risk in these environments.                       |

The provider is selected via `mev_protection` in strategy config, not hardcoded. Execution-service resolves the provider
at runtime and wraps the transaction submission accordingly.

## Wrap Preprocessor

Before executing DeFi operations, the wrap preprocessor auto-detects token wrapping requirements and emits WRAP
instructions when needed. This is transparent to the strategy layer.

| Source Token | Wrapped Token | When Required                       | Wrapping Contract |
| ------------ | ------------- | ----------------------------------- | ----------------- |
| ETH          | WETH          | Uniswap V3 swaps, Aave deposits     | WETH9             |
| eETH         | weETH         | Aave collateral (eETH is rebasing)  | EtherFi weETH     |
| stETH        | wstETH        | Aave collateral (stETH is rebasing) | Lido wstETH       |

The preprocessor checks the target venue's accepted collateral list (from UAC registry) and rejects unsupported
collateral at the venue level. If the source token has a known wrapped equivalent that the venue accepts, a WRAP
instruction is automatically prepended to the instruction sequence.

Rebasing tokens (eETH, stETH) cannot be used as Aave collateral directly because their balance changes break Aave's
scaled balance accounting. Wrapping converts them to non-rebasing equivalents where yield accrues via exchange rate
appreciation instead of balance changes.

## Key Files

| File                                                       | What                                            |
| ---------------------------------------------------------- | ----------------------------------------------- |
| execution-service DeFi `protocols/aave.py`                 | Aave supply/borrow/repay/flash_loan             |
| execution-service DeFi `protocols/uniswap.py`              | Uniswap swap (SwapRouter02)                     |
| execution-service DeFi `protocols/base.py`                 | BaseConnector, Web3 signing, credential loading |
| UAC `registry/capability_declarations/_defi.py`            | CHAIN_RPC_TEMPLATES, capabilities               |
| UAC `config/testnet_contracts.yaml`                        | Contract addresses per chain                    |
| deployment-service `contracts/FlashLoanReceiver.sol`       | Flash loan receiver source                      |
| deployment-service `scripts/deploy-flash-loan-receiver.sh` | Deploy script                                   |
| execution-service `cli/handlers/live_execution_handler.py` | SM fetch + execution-service DeFi injection     |
