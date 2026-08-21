---
doc_type: codex-ssot
title: DeFi Execution Overview
summary: "SSOT for DeFi execution: strategy→execution manifest handoff (3-state emission), operation routing
  (TRADE/LEND/BORROW/SWAP/STAKE/FLASH_* + Phase-4 LST/restaking/yield/Solana connectors), credential fetch,
  DefiErrorCode (35 codes), cost models (gas/slippage/flash), wrap preprocessor, and the DeFi-long+CeFi-short hybrid
  model."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, execution, connectors, cost, mev, aave, uniswap]
related:
  [
    /codex/04-architecture/mev-protection.md,
    /codex/04-architecture/interface-credential-convention.md,
    /codex/04-architecture/custody-providers.md,
  ]
created: 2026-03-27
authoritative_for: [DeFi execution overview and strategy-to-execution operation routing]
referenced_by:
  [
    /codex/02-data/carry-venue-live-integration-reference.md,
    /codex/02-data/defi-data-pipeline.md,
    /codex/04-architecture/chain-environment-resolution.md,
    /codex/04-architecture/interface-credential-convention.md,
    /codex/04-architecture/mev-protection.md,
    /codex/04-architecture/research-service-and-dart-integration.md,
    /codex/04-architecture/solana-defi-coverage.md,
    /codex/04-architecture/strategy-ensemble-topology.md,
  ]
owner:
last_reviewed: 2026-10-07
code_refs:
---

# DeFi Execution Overview

## Data Pipeline — Strategy→Execution Manifest Handoff

The strategy→execution boundary has explicit manifest emission on both sides for the `strategy_instructions` data_type.

**Writer (strategy-service)**:

- `strategy_service/engine/core/gcs_storage_service.py` emits via `StrategyManifestRecorder`
- Emits `record_captured(row_count=N)` on successful upload, `record_empty(reason=SOURCE_RETURNED_ZERO)` on hold-day,
  `record_failed(error_message=...)` on error
- `PipelineMode.BATCH_STRATEGY_SERVICE`; shard atom: `(client_id, strategy_id, day)`;
  `data_type="strategy_instructions"`

**Reader (execution-service)**:

- `execution_service/strategy_instructions/gcs.py` `download_instructions_df()` emits via `ExecutionManifestRecorder`
- Same 3-state emission: `record_captured` / `record_empty(SOURCE_RETURNED_ZERO)` / `record_failed`
- 404 / NotFound / No such object → `record_empty(SOURCE_RETURNED_ZERO)` (hold day — no action)
- Non-404 error → `record_failed` + `ADAPTER_FETCH_FAILED` event + re-raise

**QG enforcement**: `unified-trading-pm/scripts/qg/no_silent_absence_handlers.sh` Phase Qa/Qb explicitly checks both
files for presence of `record_captured|record_empty|record_failed`.

Origin record (not an SSOT — plans archive, codex owns the durable rule):
[`/plans/archive/2026_05/strategy_execution_contract_remediation_2026_05_20.md`](/plans/archive/2026_05/strategy_execution_contract_remediation_2026_05_20.md)
(`status: complete`).

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

    CUSTODY STATE (2026-05-22):
    May-23 cutover ships on `CLOUD_KMS_ENCRYPTED` (HSM-backed CMK; CloudKmsCustodyProvider SHIPPED at
    execution-service@d45d24b4; 10 HSM CMKs provisioned 2026-05-12 in asia-northeast1, 90-day auto-rotation).
    June-1+: per-wallet `signing_surface` field on WalletProvisioningConfig flips to `COPPER_MPC` / `CEFFU`
    (POD-provided credentials). `FIREBLOCKS_MPC` is in the UAC enum but is OUT OF SCOPE for May-23 + June-1.
    Full provider spec: `/codex/04-architecture/custody-providers.md`.

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
`unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode` (StrEnum; 35 codes; refreshed 2026-05-22 — grew
from 13 original Aave codes to 35 as HL perp + recursive-loop + oracle codes added 2026-05-12/13 + 5 CCTP codes added
2026-05-19). Import: `from unified_api_contracts import DefiErrorCode, OracleStaleError, OracleDeviationError`.
Distinct from this runtime enum, the venue-error REGISTRY (`errors/defi.py` + `errors/_defi_aave_codes.py`) carries
the protocols' PUBLISHED error tables transcribed in full for `classify_venue_error()` (e.g. Aave v3's 84-code
`Errors.sol` table, doc-cited, added 2026-08-21) — SSOT `/codex/04-architecture/venue-websocket-resilience.md` §2.

### Aave V3 / on-chain DeFi codes (13)

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

### Recursive-loop orchestrator codes (7)

Used by `execution-service/execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py` — emitted
directly (not via `classify_venue_error`). Added 2026-05-12 per Phase 5 design. (The module lives under
`orchestrators/`, not `protocols/`.)

| Code                                        | Action | When                                              |
| ------------------------------------------- | ------ | ------------------------------------------------- |
| RECURSIVE_LOOP_ABORTED_HF                   | SKIP   | Pre-iter HF gate triggered; caller gets partial   |
| RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED          | SKIP   | Gas-budget gate mid-loop; caller gets partial     |
| RECURSIVE_LOOP_SLIPPAGE_REVERT              | RETRY  | Cross-asset swap slippage; retry with wider tol   |
| RECURSIVE_LOOP_FLASH_RECEIVER_NOT_FOUND     | FAIL   | UAC flash_loan_receiver_for() returned None       |
| RECURSIVE_LOOP_FLASH_REPAYMENT_INSUFFICIENT | FAIL   | Receiver InsufficientRepaymentBalance revert      |
| RECURSIVE_LOOP_FLASH_ACTION_FAILED          | FAIL   | Receiver ActionFailed(idx, ret) revert            |
| RECURSIVE_LOOP_PARTIAL_OPEN_NO_UNWIND_FUNDS | FAIL   | Persistent driver aborted; HF too tight to unwind |

### Hyperliquid CeFi perp codes (8)

Used by `VENUE_ERRORS_DEFI["hyperliquid"]` → `classify_venue_error("hyperliquid", code)`. Added 2026-05-12 per Phase 6.

| Code                        | Action | When                                            |
| --------------------------- | ------ | ----------------------------------------------- |
| HL_INSUFFICIENT_MARGIN      | FAIL   | place_order rejected — insufficient USDC margin |
| HL_REDUCE_ONLY_VIOLATION    | FAIL   | reduce_only=True on size-increasing order       |
| HL_INVALID_TIF              | FAIL   | TIF mismatch — HL accepts Alo/Ioc/Gtc only      |
| HL_RATE_LIMITED             | RETRY  | 429 or 1-req/s breach — exponential backoff     |
| HL_NONCE_TOO_LOW            | RETRY  | EIP-712 nonce race — re-read from /info         |
| HL_SIGNATURE_INVALID        | FAIL   | Wallet config / chainId drift — alert operator  |
| HL_POSITION_CLOSED          | SKIP   | Auto-liquidation race — ghost position          |
| HL_FILL_CONFIRMATION_MISSED | RETRY  | WS fill timeout — re-query /info userFills      |

### Oracle codes (2)

Raised as typed exceptions (`OracleStaleError`, `OracleDeviationError`). Added 2026-05-13 per writegate Phase 2.A.

| Code                      | Exception            | Action | When                                             |
| ------------------------- | -------------------- | ------ | ------------------------------------------------ |
| ORACLE_STALE              | OracleStaleError     | SKIP   | Chainlink/Pyth feed heartbeat exceeded threshold |
| ORACLE_DEVIATION_EXCEEDED | OracleDeviationError | FAIL   | Multi-source prices diverge ≥ sigma threshold    |

### CCTP bridge codes (5)

Added 2026-05-19 per api_keys Phase 4.C.

| Code                     | Action | When                                              |
| ------------------------ | ------ | ------------------------------------------------- |
| CCTP_BURN_FAILED         | FAIL   | depositForBurn reverted — check balance/allowance |
| CCTP_ATTESTATION_TIMEOUT | RETRY  | Circle Iris attestation not ready                 |
| CCTP_RECEIVE_FAILED      | FAIL   | receiveMessage reverted — may be already consumed |
| CCTP_UNSUPPORTED_CHAIN   | FAIL   | Chain not in CCTP contract registry               |
| CCTP_NON_USDC_TOKEN      | FAIL   | CCTP only bridges USDC                            |

## Modes

| Mode              | What happens                   | Contract needed?         |
| ----------------- | ------------------------------ | ------------------------ |
| Backtest          | In-memory simulation, no Web3  | No                       |
| Paper trade       | Signs tx but doesn't broadcast | No                       |
| Testnet (Sepolia) | Real chain, test tokens        | Yes (deployed)           |
| Fork (Tenderly)   | Mainnet state snapshot         | Yes (deploy per fork)    |
| Live (mainnet)    | Real execution, real money     | Yes (deployed, verified) |

## Connector liveness standard — code-complete, credentials-gated (operator ruling 2026-08-14)

**Every protocol connector must be LIVE-CAPABLE in code. The only thing allowed to be missing at rest is credentials.**
A connector whose write path exists only as an in-memory simulation is not "a connector we haven't configured yet" — it
is an unbuilt connector, and it must not be counted as coverage in any audit, plan or client-facing statement.

This is the connector-level instance of the standing
[external-data-always-available rule](/codex/02-data/external-data-always-available-rule.md): running out of credentials
is a credential ask, never a descope. Build the full path; let it fail loudly at `connect()` when the key is absent.

### `supports_live` — the declaration, and why it fails closed

`BaseConnector` carries the live machinery already — `_load_wallet_credentials()`, `_require_wallet_config()`,
`sign_and_send_transaction()` (nonce, signing, broadcast, receipt wait), and `get_defi_rpc_url()`. A subclass becomes
live by USING it, then declaring:

```python
class LidoConnector(BaseConnector):
    venue_id = "LIDO-ETHEREUM"
    supports_live = True   # only once the write path really builds and sends a tx
```

`supports_live` defaults to **`False`**, and `BaseConnector.__init__` raises `SimulationOnlyConnectorError` when
`is_live=True` reaches a connector that has not declared it.

**The default is fail-closed for a specific reason.** Before this guard, 18 of 38 protocol modules accepted `is_live`
and never read it: `LidoConnector(config, is_live=True).stake(...)` subtracted from `self._balances["WETH"]`, added to
`self._balances["wstETH"]`, and returned `{"success": True}`. **A simulated success on a live path is the worst failure
this code can produce** — it is indistinguishable from a real fill to every downstream consumer, including the four
ledgers and reconciliation, so it surfaces as an unexplained position discrepancy long after the trade, if at all. An
exception at construction is strictly better than a fill that never happened.

Solana connectors split across two base classes, not one, and are not uniformly live (corrected 2026-08-21 per the W15
venue-adaptor security audit, `w15_execution_service_venue_adaptor_security_audit_2026_08_20.md`, which found this
claim stale on both counts). `OrcaConnector`, `RaydiumConnector`, and `MarinadeConnector` inherit `BaseSolanaConnector`
(`solana_base.py`), which already mirrors the same `supports_live: bool = False` fail-closed default declared on
`BaseConnector` (the mirroring described as still-pending here has since landed) — these three declare
`supports_live = True` and are live today. `JitoConnector`, `JitoRestakingConnector`, and `SolBlazeConnector` instead
inherit `BaseConnector` directly and stay `supports_live = False` by design: their target programs (SPL stake-pool
`DepositSol`/`WithdrawSol`, and Jito's Anchor-based restaking vault) take fixed, protocol-specific account lists that
need an SDK (`spl-stake-pool` or an Anchor IDL decoder) this repo does not yet depend on — hand-rolling the raw
instruction bytes was judged too risky to fabricate. This is the fail-closed guard working as intended, not an
unmirrored declaration; see each module's own "Live-capability status" docstring for the per-connector detail.

### What "live-capable" requires per connector

Most of these are not bespoke integrations — the shared shape dominates, so build the shared thing first (the
generic-first ruling, `/codex/06-coding-standards/integration-testing-layers.md` § the venue-coverage cascade):

| Shape                 | Read side                                                                               | Write side                                                    |
| --------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| LST / restaking token | ERC-20 `balanceOf` (SPL equivalent on Solana)                                           | protocol deposit/stake method + `sign_and_send_transaction()` |
| Vault share           | share `balanceOf` + a `pricePerShare`-style view call                                   | deposit/withdraw method                                       |
| Genuinely stateful    | protocol-specific — health factors, PT/YT maturities, CL tick ranges, withdrawal queues | protocol-specific                                             |

**Simulation stays.** It is a designed mode (backtest, and `_simulated_tx_result()` in `BaseConnector` supports paper
trade), not an accident to delete. The requirement is that `is_live` genuinely ROUTES between the two, rather than being
accepted and ignored.

Provenance and the full per-module tier table:
[`/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`](/plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md).

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

| Archetype                    | Margin mode   | Eligible CeFi venues                                                 |
| ---------------------------- | ------------- | -------------------------------------------------------------------- |
| `carry_staked_basis`         | LST_AS_MARGIN | Bybit UTA (stETH/METH/USDe), Deribit (stETH), OKX (wstETH)           |
| `arbitrage_price_dispersion` | USDC          | All venues: Binance, Bybit, OKX, Deribit, Kraken, Hyperliquid, Aster |

The venue-collateral matrix in UAC + per-archetype docs is the authoritative eligibility gate. Preflight rejects venues
that fail the margin-mode check at strategy runtime — no hardcoded allowlist in code.

SSOT: `codex/09-strategy/architecture-v2/archetypes/` (per-archetype venue matrices).

## Phase 9 DeFi Cost Models (gas + slippage + flash premium)

Phase 9 of `defi_recursive_borrow_archetypes_2026_05_10.md` shipped three cost models and an aggregator in
`execution-service/execution_service/matching_engine/defi/`. These are the **canonical** pre-trade cost estimation path
for both batch backtest replay and live execution.

### Entry point

```python
from execution_service.matching_engine.defi import (
    DefiCostAggregator,
    DefiCostEstimate,
    build_defi_fill_context,
)

cost: DefiCostEstimate = DefiCostAggregator().estimate_recursive_loop_cost(
    chain="ethereum",
    opening_mode="FLASH",           # or "PERSISTENT"
    gas_price_gwei=gas_gwei,        # from MTDS gas_fee_data (batch) or live RPC
    native_token_usd=eth_usd,
    flash_principal_usd=principal,
    swap_notional_usd=notional,
    pool_matcher=pool_snapshot,     # None → analytical fallback
    swap_amount_in=amount_in,
    swap_side=OrderSide.BUY,
    pool_tvl_usd=None,
)
ctx = build_defi_fill_context(cost, strategy_id=..., ...)
```

### Three cost components

| Component         | Model file                                         | Key constants / surface                                                                                                                                                |
| ----------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Gas**           | `matching_engine/defi/gas_cost_model.py`           | `GasAction` (SUPPLY/BORROW/REPAY/WITHDRAW/UNISWAP_V3_SWAP/FLASH_OPEN/FLASH_CLOSE); `GAS_UNITS` (calibrated p50 mainnet 2024–2026); `FALLBACK_GAS_PRICE_GWEI` per chain |
| **Slippage**      | `matching_engine/defi/slippage_cost_model.py`      | Pool-matcher path (preferred, `PoolMatcher.quote()` → `price_impact_bps`) or analytical fallback (`≈ amount_in_usd / pool_tvl_usd × 10_000`)                           |
| **Flash premium** | `matching_engine/defi/flash_premium_cost_model.py` | `FlashLoanProvider` (AAVE_V3 = 5 bps, BALANCER = 0 bps, NONE = 0 bps); only applies in `FLASH` opening mode                                                            |

### Batch = Live contract

- Batch callers pass per-day median `gas_price_gwei` from MTDS `gas_fee_data` parquet + a `PoolMatcher` snapshot
  reconstructed from historical pool state.
- Live callers pass a live RPC gas price + a freshly-fetched pool snapshot.
- No other difference — single code path, no live-only forks.

### P&L attribution wiring

`gas_cost_usd + flash_premium_usd` → `FillAttributionContext.fee_amount_modelled` (STRATEGY layer / FEES factor,
deterministic).

Slippage is captured via `MatchResult.price_impact_bps` on the live/simulated fill and attributed to EXECUTION layer /
SLIPPAGE factor by `build_attribution_rows`.

### L2 gas overhead

L2 chains (Arbitrum / Base / Optimism) carry an additional L1 data-posting overhead (`_L1_DATA_OVERHEAD_USD`: Arbitrum
$0.02, Base/Optimism $0.01). Pass via `estimate_l1_data_cost_usd(chain)`.

### Backtest replay status

Phase 9 item 3 (backtest replay with real cost gates) is `BLOCKED-DATA` until the ≥1-year lending-indices window
backfill lands. Original target window: 2026-05-19 → 2026-05-23 (May-23 cutover). Status as of 2026-05-22: backfill
still in-progress per `code_freeze_migrate_backfill_sequencing_2026_05_10.md` — lending-indices data_types in MTDS
depend on `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3. Update this status when backfill completes.

## Key Files

| File                                                                 | What                                                            |
| -------------------------------------------------------------------- | --------------------------------------------------------------- |
| execution-service DeFi `protocols/aave.py`                           | Aave supply/borrow/repay/flash_loan                             |
| execution-service DeFi `protocols/uniswap.py`                        | Uniswap swap (SwapRouter02)                                     |
| execution-service DeFi `protocols/base.py`                           | BaseConnector, Web3 signing, credential loading                 |
| UAC `registry/capability_declarations/_defi.py`                      | CHAIN_RPC_TEMPLATES, capabilities                               |
| UAC `config/testnet_contracts.yaml`                                  | Contract addresses per chain                                    |
| deployment-service `contracts/FlashLoanReceiver.sol`                 | Flash loan receiver source                                      |
| deployment-service `scripts/deploy-flash-loan-receiver.sh`           | Deploy script                                                   |
| execution-service `cli/handlers/live_execution_handler.py`           | SM fetch + execution-service DeFi injection                     |
| execution-service `matching_engine/defi/gas_cost_model.py`           | GasAction enum + GAS_UNITS + estimate_gas_cost_usd              |
| execution-service `matching_engine/defi/slippage_cost_model.py`      | Pool-matcher + analytical slippage estimation                   |
| execution-service `matching_engine/defi/flash_premium_cost_model.py` | FlashLoanProvider + FLASH_PREMIUM_BPS                           |
| execution-service `matching_engine/defi/cost_aggregator.py`          | DefiCostAggregator + DefiCostEstimate + build_defi_fill_context |

## Removed vendors — the ban is FLEET-WIDE, not DeFi-execution-only (ruled 2026-08-10)

Never scaffold an adapter, a registry entry, a `PLANNED_VENUES`/`SourceCapability` declaration, or a credential ask for:
**Elysium · Arkham · Bloxroute · Infura · Kaiko · Massive (formerly Polygon.io)**. (The `polygon` that appears in DeFi
code is the CHAIN, not the vendor — that one is fine.)

**Why this section exists.** Until 2026-08-10 this list lived only in `cursor-configs/CLAUDE.md`'s _"Working on DeFi
EXECUTION?"_ conditional bullet. On 2026-08-09 a session scaffolded a brand-new **Kaiko on-chain analytics** adapter in
market-tick-data-service (`adapters/onchain/kaiko.py` + test + a `PLANNED_VENUES` entry + a UAC `SourceCapability`) and
filed a credential ask for `kaiko-api-key` — entirely in good faith, because writing an MTDS _analytics_ adapter is not
"working on DeFi execution", so the conditional bullet did not obviously bind it. The operator ruled the ban is
workspace-wide, the scaffold was removed under `/plans/archive/2026_08/kaiko_provider_removal_2026_08_10.md`, and the
rule was promoted into CLAUDE.md's **always-on** section so no subsystem can read itself out of scope again.

**The generalisable lesson**: a ban that applies to every subsystem must not live under a conditional
`§ When your task touches X` heading — the conditional index is explicitly "open this only when your task touches that
domain", so anything filed there is invisible to every other domain by design.
