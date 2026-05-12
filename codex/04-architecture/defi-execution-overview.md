---
scope: [engineer, admin]
---

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
execution-service fetches credentials from SM (single SSOT — codex audit EX-23 2026-05-12):
    The canonical SM-secret-name map is in
    `execution-service/.../cli/handlers/live_execution_handler.py` + extended by `interface-credential-convention.md`
    § "Custody" (`private_key_secret_ref` / `kms_key_uri` for the cloud_kms cutover path per EX-10/EX-23 reconciliation).
    Examples below are illustrative — refer to the live_execution_handler.py source for the actual fetch list.
    wallet_private_key  → defi-wallet-private-key  (or `kms_key_uri` for cloud_kms_encrypted cutover default)
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

### Core Connectors (Phase 1–3)

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

### Phase 4 Connectors — LST/LRT, Restaking, Yield, Solana

Shipped 2026-05-12 (`defi_catalogue_chain_primitives_2026_05_10.md` Phase 4).

**LST / Liquid Restaking Tokens (EVM)**

| Connector           | venue_id            | Chain    | Operations                    |
| ------------------- | ------------------- | -------- | ----------------------------- |
| RocketPoolConnector | ROCKETPOOL-ETHEREUM | Ethereum | stake / unstake               |
| RenzoConnector      | RENZO-ETHEREUM      | Ethereum | deposit / withdraw / delegate |
| KelpDAOConnector    | KELPDAO-ETHEREUM    | Ethereum | deposit / withdraw / delegate |
| PufferConnector     | PUFFER-ETHEREUM     | Ethereum | deposit / withdraw            |

**Restaking Middleware (EVM)**

| Connector          | venue_id           | Chain    | Operations                    |
| ------------------ | ------------------ | -------- | ----------------------------- |
| SymbioticConnector | SYMBIOTIC-ETHEREUM | Ethereum | deposit / withdraw / delegate |
| KarakConnector     | KARAK-ETHEREUM     | Ethereum | deposit / withdraw / delegate |

**Yield Optimizers (EVM)**

| Connector       | venue_id        | Chain    | Operations                         |
| --------------- | --------------- | -------- | ---------------------------------- |
| YearnConnector  | YEARN-ETHEREUM  | Ethereum | deposit / withdraw                 |
| ConvexConnector | CONVEX-ETHEREUM | Ethereum | deposit / withdraw / claim_rewards |
| BeefyConnector  | BEEFY-POLYGON   | Polygon  | deposit / withdraw                 |

**Yield Derivatives (EVM)**

| Connector       | venue_id        | Chain    | Operations         |
| --------------- | --------------- | -------- | ------------------ |
| PendleConnector | PENDLE-ETHEREUM | Ethereum | deposit / withdraw |
| IdleConnector   | IDLE-ETHEREUM   | Ethereum | deposit / withdraw |

**Solana LST / Restaking**

| Connector              | venue_id              | Chain  | Operations                    |
| ---------------------- | --------------------- | ------ | ----------------------------- |
| SolBlazeConnector      | SOLBLAZE-SOLANA       | Solana | stake / unstake               |
| JitoRestakingConnector | JITO-RESTAKING-SOLANA | Solana | deposit / withdraw / delegate |

All Phase 4 connectors follow the same `connector.connect(config={...})` credential injection shape as the Phase 1–3
connectors (see `interface-credential-convention.md`). Testnet validation (Sepolia/Holesky/devnet) and Tenderly fork
integration tests are tracked in `defi_catalogue_chain_primitives_2026_05_10.md` Phase 4 full-execution criterion.

## Error Classification

Every on-chain revert maps to a structured error code with an action. SSOT for the closed set: UAC
`unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode` (13 codes; see CLAUDE.md § "DeFi Execution
Architecture"). Table refreshed 2026-05-12 per slot 8 exec audit EX-7 — earlier count was 11.

| Code                              | Action | When                    |
| --------------------------------- | ------ | ----------------------- |
| INSUFFICIENT_COLLATERAL           | FAIL   | Borrow exceeds LTV      |
| INSUFFICIENT_BALANCE              | FAIL   | Not enough tokens       |
| NO_COLLATERAL_DEPOSITED           | FAIL   | Can't borrow            |
| ASSET_NOT_SUPPORTED               | FAIL   | Token not in pool       |
| ZERO_AMOUNT                       | FAIL   | Amount must be > 0      |
| TX_REVERTED                       | FAIL   | Generic revert          |
| GAS_ESTIMATION_FAILED             | RETRY  | Node congestion         |
| SLIPPAGE_EXCEEDED                 | RETRY  | Price moved             |
| FLASH_LOAN_RECEIVER_INVALID       | FAIL   | Receiver not a contract |
| FLASH_LOAN_INSUFFICIENT_LIQUIDITY | FAIL   | Pool drained            |
| NO_OUTSTANDING_DEBT               | SKIP   | Nothing to repay        |
| BORROW_CAP_EXCEEDED               | FAIL   | Pool borrow-cap reached |
| SUPPLY_CAP_EXCEEDED               | FAIL   | Pool supply-cap reached |

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
4. Default slippage tolerance: see code SSOT in `execution-service/.../defi_execution/protocols/uniswap.py`
   (`max_slippage_bps` default; reconcile codex narrative against the code default on next exec audit pass — slot 8
   audit EX-9 2026-05-12 flagged drift across mev-protection.md = 20 bps, this doc = 50 bps, execution-policy.md
   examples = 10/20/30/50 bps; the per-rule examples are correct, the doc-narrative defaults need alignment to the
   single code default). Configurable via `config["max_slippage_bps"]`.

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

> **SUPERSEDED 2026-05-10 by `cross_asset_group_catalogue_audit_2026_05_10.md` Phase 4 — canonical MEV-protection SSOT
> is [`mev-protection.md`](mev-protection.md). The legacy 3-provider table that previously lived here inverted the
> mainnet/L2 provider selection (per slot 8 audit EX-8 / EX-20) and is replaced by the canonical `MevSubmissionMode`
> enum + chain-aware default policies documented in `mev-protection.md` § "Provider Selection (Factory)". This section
> retained as a redirect stub only.**

The provider is selected via `mev_protection` in strategy config, not hardcoded; execution-service resolves the provider
at runtime per the canonical `_DEFAULT_POLICIES` in `execution_service/v2/mev_router.py`. See
[`mev-protection.md`](mev-protection.md) for the full provider matrix, the chain-aware default mode per asset, the
`MevSubmissionMode` UAC enum, and the per-strategy artifact-versioned policy contract.

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

## Strategy Architecture: DeFi Long + CeFi Short (Hybrid Venue Model)

DeFi strategies combine an **on-chain long leg** (staking, lending, providing liquidity) with a **CeFi perp short leg**
(hedge). The "DeFi" label refers to the strategy family, not venue restriction.

```
DeFi strategy = on-chain long (LST staking / Aave lending / AMM LP)
              + CeFi perp short (hedge leg)
```

ALL CeFi perp venues are candidates for the short leg. Eligibility is archetype-specific:

| Archetype                    | Margin mode   | Eligible CeFi venues                                                             |
| ---------------------------- | ------------- | -------------------------------------------------------------------------------- |
| `carry_staked_basis`         | LST_AS_MARGIN | Bybit UTA (stETH/METH/USDe), Deribit (stETH), OKX (wstETH), DRIFT (JitoSOL/mSOL) |
| `arbitrage_price_dispersion` | USDC          | All venues: Binance, Bybit, OKX, Deribit, Kraken, Hyperliquid, Aster, DRIFT      |

The venue-collateral matrix in UAC + per-archetype docs is the authoritative eligibility gate. Preflight rejects venues
that fail the margin-mode check at strategy runtime — no hardcoded allowlist in code.

SSOT: `codex/09-strategy/architecture-v2/archetypes/` (per-archetype venue matrices).

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
