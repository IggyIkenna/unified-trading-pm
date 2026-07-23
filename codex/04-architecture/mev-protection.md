---
doc_type: codex-ssot
title: MEV Protection
summary:
  "Canonical SSOT for MEV protection — slippage / price-impact caps, private-mempool (Flashbots Protect) routing above
  MEV_PROTECTION_THRESHOLD_USD, Jito bundles on Solana, Tenderly pre-flight sim, and a get_mev_provider(mode, chain_id)
  factory; PROTECTED_RPC_URLS in UAC is the endpoint SSOT (never hardcode). Active only on Ethereum mainnet + Solana."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [e2e-testing, execution-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, execution, mev, uac, circuit-breaker, ssot]
related:
  [
    /codex/05-infrastructure/chain-rpc-mev-tenderly.md,
    /codex/04-architecture/tenderly-execution-provider.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/kill-switch-event-bus.md,
  ]
created: 2026-04-03
authoritative_for:
  [
    MEV protection architecture,
    MEV submission modes and provider selection,
    MevSubmissionMode policy registry,
    MEV-driven breaker trigger,
  ]
referenced_by:
  [
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/05-infrastructure/chain-rpc-mev-tenderly.md,
    /codex/07-security/mev-protection.md,
    /codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# MEV Protection

> Canonical SSOT for MEV protection across the system. Consolidates content from `07-security/mev-protection.md`
> (implementation detail) and `09-strategy/architecture-v2/cross-cutting/mev-protection.md` (strategy-side policy
> narrative) per `cross_asset_group_catalogue_audit_2026_05_10` Phase 4. Last updated 2026-05-10.

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

## Threat Model

| Attack type        | Description                                                         | Affected operations                              |
| ------------------ | ------------------------------------------------------------------- | ------------------------------------------------ |
| Sandwich attack    | Front-run + back-run around a swap tx                               | SWAP (Uniswap V2/V3, Curve, Balancer, all DEXes) |
| Front-running      | Copy + beat a profitable tx to the same block                       | Flash loans, large swaps                         |
| Liquidation racing | Competing bots racing to liquidate an under-collateralised position | Aave/Compound liquidations                       |
| Time-bandit        | Reorg attack to steal profits from committed txs                    | Any (extremely rare)                             |

**Scope**: MEV protection is **only active on Ethereum mainnet** (`chain_id = 1`) and **Solana** (Jito bundle submission
per [`chain-rpc-mev-tenderly.md`](/codex/05-infrastructure/chain-rpc-mev-tenderly.md)). On L2s (Arbitrum, Base,
Optimism, Linea, Scroll, ZkSync) the sequencer is centralised and there is no public mempool, making MEV extraction
structurally infeasible. On Polygon / Avalanche / BSC there is no Flashbots-equivalent yet — operator decision to accept
exposure with tighter slippage or skip these chains.

## How the System Protects Against MEV

### 1. Slippage Tolerance + Price Impact Checks (DEX swaps)

All DEX swaps via `UniswapConnector.swap_exact_input()` (and equivalent for other DEXes — Phase 4 catalogue plan)
enforce a `slippage_tolerance_bps` parameter. This sets the `amountOutMinimum` in the `exactInputSingle` call:

```python
amount_out_minimum = int(quote_amount_out * (1 - slippage_tolerance / 10000))
params["amountOutMinimum"] = amount_out_minimum
```

Default: `20 bps` (0.2%). If a sandwich attack moves the price beyond 0.2%, the transaction reverts on-chain and the
`TX_REVERTED` error code is returned.

`SwapHandler.validate()` enforces a 500 bps (5%) hard cap on `max_slippage_bps`. Tighter slippage settings reduce
sandwich profitability:

- Recommended: `max_slippage_bps ≤ 30` (0.3%) for liquid pairs
- Large orders: `max_slippage_bps ≤ 100` (1%) with position split via `AlgoComparisonRunner`
- For large EIGEN/ETHFI reward sells, a tighter tolerance (10 bps) is recommended

MEV protection reduces but does not eliminate slippage attacks — slippage tolerance is the last line of defence when the
private mempool path fails.

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

Private RPC endpoints by chain (per [`chain-rpc-mev-tenderly.md`](/codex/05-infrastructure/chain-rpc-mev-tenderly.md)):

- **Ethereum mainnet**: Flashbots Protect (`https://rpc.flashbots.net`) + MEV Blocker (`https://rpc.mevblocker.io`) +
  Manifold (partial).
- **Arbitrum / Base / Optimism / Linea / Scroll / ZkSync**: sequencer-only (centralised; no public mempool).
- **Solana**: Jito bundle submission (Phase 5A `JitoBundleProvider`).

**Bundle relay vs private RPC distinction** (clarified 2026-05-10):

- **Flashbots Protect (`rpc.flashbots.net`)**: public-facing **private RPC endpoint**. Free, no auth signer. Bypasses
  public mempool. Adequate for sandwich protection. **WIRED via `PrivateMempoolProvider`.**
- **Flashbots Bundle Relay (`relay.flashbots.net`, `eth_sendBundle`)**: paid auth-signer subscription. Used for **atomic
  multi-tx bundles**. Currently **STUBBED**. NOT NEEDED for May-23 archetypes (Aave flash loans are single-tx atomic by
  design; cross-chain carry legs can't bundle). Out of scope per operator 2026-05-10.

### 3. Gas Price Strategy

Execution-service uses `GasPriceAdapter` to set competitive gas prices without overpaying. For time-sensitive
transactions (reward claims, liquidation-avoidance rebalancing):

```python
gas_price = gas_adapter.get_fast_gas_price()  # EIP-1559: maxFeePerGas + maxPriorityFeePerGas
```

Overpaying gas is itself an MEV vector (priority gas auctions). The adapter caps `maxPriorityFeePerGas` at 3 gwei for
non-urgent transactions.

### 4. L2 Deployment (Structural MEV Reduction)

DeFi strategies prefer L2 venues (Arbitrum, Base, Optimism) where possible:

- Centralised sequencers eliminate front-running from mempool observers
- Gas costs are 10-100x cheaper, making small rebalances economical
- Reward selling on Arbitrum Uniswap V3 has near-zero MEV exposure

The `CrossChainSORStrategy` factors in MEV risk as part of venue selection:

- L2 venues get a lower effective slippage estimate vs Ethereum mainnet
- Bridge costs must be less than MEV savings for cross-chain routing to be worth it

### 5. On-Chain Simulation (Pre-flight via Tenderly)

Before submitting transactions, execution-service pre-simulates via the Tenderly fork connector per
[`tenderly-execution-provider.md`](tenderly-execution-provider.md):

```python
simulation_result = tenderly_fork.simulate_transaction(tx_params)
if simulation_result.reverted:
    raise DeFiError(DefiErrorCode.TX_REVERTED, simulation_result.revert_reason)
```

Per `defi_catalogue_chain_primitives` Phase 5C: every live order goes through bundle-sim by default, BLOCK on revert,
advisory-log on slippage > threshold. Daily Tenderly budget = $50/day per archetype default. Budget exhaustion
downgrades to advisory-only.

## Implementation: MEVProtectionConfig + Provider Factory

### MEVProtectionConfig

Defined in `execution_service.defi_execution.mev.protection.MEVProtectionConfig` (Pydantic `BaseModel`). Configured
per-handler or per-strategy at instantiation time.

```python
MEVProtectionConfig(
    enabled=True,         # False → standard public RPC submission
    mode="live",          # live | paper | batch | testnet
    chain_id=1,           # Only chain_id=1 activates real MEV protection
    relay_url=None,       # Custom Flashbots relay (optional)
    private_rpc_url=None, # Custom private mempool RPC (optional)
    max_block_offset=3,   # Target block = current_block + offset
    bundle_timeout_seconds=12.0,
)
```

### Provider Selection (Factory)

`get_mev_provider(mode, chain_id, ...)` selects the appropriate provider:

| Condition                             | Provider                 | Behaviour                                       |
| ------------------------------------- | ------------------------ | ----------------------------------------------- |
| `mode` in `paper`, `batch`, `testnet` | `NoProtectionProvider`   | No-op; logs only                                |
| `chain_id == 1` and `relay_url` set   | `FlashbotsProvider`      | Bundle relay via custom URL (currently STUBBED) |
| `chain_id == 1` (default)             | `PrivateMempoolProvider` | `https://rpc.flashbots.net` (Protect)           |
| Solana (per Phase 5A)                 | `JitoBundleProvider`     | Jito block-engine bundle submission             |
| L2 chains                             | `NoProtectionProvider`   | Sequencer; no public mempool                    |

### Protected RPC URLs (SSOT)

`PROTECTED_RPC_URLS` in
[`unified_api_contracts.registry.capability_declarations._defi`](../../../unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py)
is the single source of truth for all MEV-resistant RPC endpoints. Connectors **must** import from UAC and never
hardcode these URLs.

> **Static enforcement (codex audit EX-14 2026-05-12)**: a new QG ratchet (planned —
> `unified-trading-pm/scripts/quality_gates/check_no_inline_defi_addresses_or_rpcs.py`) AST-walks `defi_execution/` for
> hex contract-address literals (`0x[a-fA-F0-9]{40}`) + `https://...rpc...` URL literals outside the UAC-import path.
> Today a new connector pasting either inline would pass QG. Analogous to QG STEP 5.69 (`resolve_bucket_name()`
> inline-f-string ratchet). Owner: governance + execution-service maintainer. Until shipped, reviewers must check by
> hand on every new `defi_execution/protocols/*.py` PR.

```python
from unified_api_contracts.registry import PROTECTED_RPC_URLS

# PROTECTED_RPC_URLS = {
#     "ETHEREUM":        "https://rpc.flashbots.net",       # Flashbots Protect
#     "ETHEREUM_BUNDLE": "https://relay.flashbots.net",     # Flashbots Bundle relay (stubbed)
#     "MEV_BLOCKER":     "https://rpc.mevblocker.io",       # CoW Protocol MEV Blocker
#     "SOLANA_JITO":     "<jito_block_engine_endpoint>",    # Phase 5A
# }
```

### MEV submission modes (UAC `MevSubmissionMode`)

Per [`mev_router.py`](../../../execution-service/execution_service/v2/mev_router.py) `_DEFAULT_POLICIES` registry:

| Mode                         | Relay                                        | Protection                       | Speed               |
| ---------------------------- | -------------------------------------------- | -------------------------------- | ------------------- |
| `PUBLIC_MEMPOOL`             | standard `eth_sendRawTransaction`            | None                             | Fastest propagation |
| `FLASHBOTS_PROTECT`          | Flashbots private RPC                        | Strong (bundle-only inclusion)   | +200-1000ms typical |
| `MEV_BLOCKER`                | MEV Blocker RPC                              | Strong                           | +200-1000ms         |
| `MANIFOLD`                   | Manifold relay                               | Strong; revenue share on backrun | +200-1000ms         |
| `CUSTOM_PRIVATE_RPC`         | Operator-provided RPC URL                    | Varies (per relay)               | Varies              |
| `JITO_BUNDLE` (NEW Phase 5A) | Jito block-engine RPC                        | Strong (Solana)                  | Solana-specific     |
| `BLOXROUTE`                  | (REMOVED per CLAUDE.md; do not re-introduce) | n/a                              | n/a                 |

### Handler Integration

`SwapHandler` (execution-service) holds a `_mev_provider` instance created from `MEVProtectionConfig`:

1. `__init__` builds the provider from the `"mev_protection"` key in handler config.
2. `_execute_with_matching_engine` logs the active provider for observability.
3. The actual **transaction signing and submission** is done by `UniswapConnector.swap_exact_input()` (or equivalent per
   protocol), which must call `self._mev_provider.submit_transaction(signed_tx, chain_id)` after constructing the signed
   calldata.

This separation keeps the matching logic in the handler and the on-chain I/O in the connector.

## Provider Implementations

### NoProtectionProvider

Located at `execution_service.defi_execution.mev.no_protection`. Used for paper/batch/testnet modes and all non-Ethereum
/ non-Solana chains. `submit_transaction` and `submit_bundle` are stubs returning a mock `TxSubmissionResult`.

### PrivateMempoolProvider

Located at
[`execution_service.defi_execution.mev.private_mempool`](../../../execution-service/execution_service/defi_execution/mev/private_mempool.py).
Submits transactions to `https://rpc.flashbots.net` (Flashbots Protect RPC). Transactions go directly to Flashbots block
builders bypassing the public mempool — invisible to searcher bots.

- No auth required (free, public-facing private RPC)
- Single tx only (no atomicity guarantees)
- Best for simple swaps and collateral deposits

### FlashbotsProvider

Located at
[`execution_service.defi_execution.mev.flashbots`](../../../execution-service/execution_service/defi_execution/mev/flashbots.py).
Submits **signed bundles** to the Flashbots relay endpoint (`https://relay.flashbots.net` or custom). Requires
`eth_sign` from a searcher key (not the trading wallet key).

- Atomic multi-tx bundles
- Explicit target block number
- Used for flash loan sequences where atomicity is required (BUT Aave flash loans are single-tx atomic by Aave design —
  bundle relay typically not needed for our archetypes)
- Higher complexity; **currently STUBBED** until paid Flashbots subscription. Module docstring line 1: "Relay
  integration is stubbed until a paid Flashbots subscription is available. Falls back to direct submission with
  logging."

### JitoBundleProvider (NEW Phase 5A)

Located at `execution_service.defi_execution.mev.jito_bundle` (Phase 5A). Submits Solana tx bundles via Jito block-
engine RPC for prioritised + MEV-protected inclusion on Solana. Wired into `mev_router.py` via
`MevSubmissionMode.JITO_BUNDLE`.

## Per-strategy MEV policy (artifact-versioned)

Strategies reference a MEV policy artifact:

```yaml
mev_policy_id: mainnet-swap-standard-v3
version: 3
rules:
  - when:
      chain: ETHEREUM
      notional_usd: { ">=": 10_000 }
    then:
      submission_mode: FLASHBOTS_PROTECT
      max_blocks_to_wait: 25
      slippage_bps_max: 30
      backrun_share: accept_up_to_50_percent

  - when:
      chain: ETHEREUM
      notional_usd: { "<": 10_000 }
    then:
      submission_mode: PUBLIC_MEMPOOL
      slippage_bps_max: 50

  - when:
      chain: ARBITRUM
    then:
      submission_mode: PUBLIC_MEMPOOL # less MEV on L2
      slippage_bps_max: 20

  - when:
      chain: SOLANA
      notional_usd: { ">=": 5_000 }
    then:
      submission_mode: JITO_BUNDLE
      slippage_bps_max: 30

  - when:
      chain: BSC
    then:
      submission_mode: PUBLIC_MEMPOOL # BSC has validator extraction; different profile
```

## MEV modes × action type

| Action            | Typical MEV exposure     | Default mode                                        |
| ----------------- | ------------------------ | --------------------------------------------------- |
| SWAP (DEX, large) | High — sandwich risk     | FLASHBOTS_PROTECT (Ethereum) / JITO_BUNDLE (Solana) |
| SWAP (DEX, small) | Low                      | PUBLIC_MEMPOOL                                      |
| LEND / BORROW     | Low                      | PUBLIC_MEMPOOL                                      |
| STAKE / UNSTAKE   | Low                      | PUBLIC_MEMPOOL                                      |
| LIQUIDATION       | Competitive — WE extract | PUBLIC_MEMPOOL with flash-loan atomic bundle        |
| TRANSFER / BRIDGE | Low                      | PUBLIC_MEMPOOL                                      |

## Error Codes (MEV-Related)

From UAC `unified_api_contracts.canonical.crosscutting.errors.defi.DefiErrorCode` (13 codes total), consumed by
execution-service DeFi connectors (e.g. `execution_service.defi_execution.protocols.aave` imports `DefiErrorCode` from
UAC):

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
mev_policy_id: mainnet-swap-standard-v3 # Reference to artifact-versioned policy
```

## Monitoring

- **MEV capture rate**: fraction of our txns that detected a sandwich attempt that was blocked
- **Private-relay success rate**: fraction of submitted bundles that got included within deadline
- **Cost of protection**: delay (ms) per successful private-relay submission
- **Revenue from backrun sharing** (Manifold / MEV-share): per-tx capture
- **Provider-fallback rate**: per-chain fail-over count from Phase 5B `RpcProviderFallback`

## Provider operational notes

| Provider                | Status            | Notes                                              |
| ----------------------- | ----------------- | -------------------------------------------------- |
| Flashbots Protect (RPC) | Active            | Free public RPC; default for Ethereum mainnet      |
| Flashbots Bundle Relay  | STUBBED           | Paid auth-signer; not needed for May-23 archetypes |
| MEV Blocker             | Active            | Available as fallback / alternative                |
| Manifold                | Opt-in            | Use when backrun revenue share valuable            |
| Jito Bundle (Solana)    | Phase 5A buildout | New Solana MEV protection mode                     |
| Eden                    | Not active        | Consider if Flashbots congested                    |

## Operational Run-Book

1. **Mainnet swap reverts** — check if `max_slippage_bps` is too tight. Increase to 50-100 bps.
2. **Bundle not included after 12s** — increase `max_block_offset` to 5 and retry.
3. **Flashbots relay unreachable** — fall back to `PrivateMempoolProvider` by removing `relay_url` from config.
4. **L2 deployment** — confirm `chain_id != 1`; MEV protection auto-disables (no action needed).
5. **Solana Jito unreachable** — fall back to `PUBLIC_MEMPOOL` per `RpcProviderFallback` Phase 5B.
6. **Tenderly bundle-sim budget exhausted** — execution downgrades to advisory-only; alert fires.

## Testing

- **Unit tests**: mock `MEVProtectionProvider` via `unittest.mock.AsyncMock`. Never call real RPCs.
- **Integration tests**: use the Tenderly fork fixtures in `execution-service/tests/integration/conftest.py`. These are
  `@pytest.mark.allow_network` and skipped without SM credentials.
- **Paper mode**: set `MEVProtectionConfig(mode="paper")` — routes to `NoProtectionProvider`.

## Key Files

| File                                                      | Purpose                                       |
| --------------------------------------------------------- | --------------------------------------------- |
| `execution_service/defi_execution/mev/protection.py`      | `MEVProtectionConfig` + provider factory      |
| `execution_service/defi_execution/mev/private_mempool.py` | `PrivateMempoolProvider` (Flashbots Protect)  |
| `execution_service/defi_execution/mev/flashbots.py`       | `FlashbotsProvider` (bundle relay; stubbed)   |
| `execution_service/defi_execution/mev/jito_bundle.py`     | `JitoBundleProvider` (Solana; Phase 5A)       |
| `execution_service/v2/mev_router.py`                      | `MevSubmissionPolicy` registry                |
| `execution_service/defi_execution/protocols/uniswap.py`   | `swap_exact_input()` with slippage guard      |
| `execution_service/defi_execution/protocols/aave.py`      | `DefiErrorCode` enum with SLIPPAGE_EXCEEDED   |
| `execution_service/defi_execution/gas_price_adapter.py`   | EIP-1559 gas price strategy                   |
| `execution_service/config/chain_config.yaml`              | MEV protection threshold + private RPC config |
| UAC `registry/capability_declarations/_defi.py`           | `PROTECTED_RPC_URLS` SSOT                     |

## MEV-driven breaker trigger

When MEV protection's mempool watch detects a sandwich or front-run pattern against in-flight transactions, the
execution-service emits a typed `MEV_DETECTED` event consumed by the **circuit breaker state machine** per the DR plan
Phase 8 taxonomy. The breaker fires `BreakerAction.BLOCK_NEW` (UAC@a7a99b5 closed-set value) with
`BreakerRecoveryMode.AUTO_COOLDOWN` recovery: cooldown expires once the MEV-watch window stays quiet for N seconds
(configurable per chain — typical defaults: 60s on EVM mainnet, 30s on L2s).

**Trigger conditions** (any one fires `MEV_DETECTED`):

- Sandwich pattern detected: tx pair with same `tx_recipient` flanking ours within ±2 blocks + opposite direction
- Front-run pattern: pending tx with same `to` + higher `gas_price` than ours, submitted ≤500ms after we broadcast
- Stale-quote attack: post-broadcast price deviation > MEV protection threshold (default 50 bps) within next 3 blocks

**Recovery semantics**: per the BreakerRecoveryMode auto-cooldown contract (see
[`autonomous-recovery-matrix.md`](autonomous-recovery-matrix.md) § "Layer-3 BreakerRecoveryMode composes with Layer-4
ErrorAction" for the per-action defaults table), the BLOCK_NEW action defaults to auto-cooldown. Once N consecutive
mempool-watch windows clear, the breaker auto-disarms and emits `KILL_SWITCH_AUTO_RECOVERED` (alerting AlertCode Round 1
ship at UAC@945ad5d).

**Cross-references**: [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md) — full `BreakerAction` +
`BreakerRecoveryMode` enum. [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) — integrated breaker
state machine including MEV-driven entry. [`kill-switch-event-bus.md`](kill-switch-event-bus.md) — event-bus shape for
`MEV_DETECTED` consumption.

## Related Docs

- [`chain-rpc-mev-tenderly.md`](/codex/05-infrastructure/chain-rpc-mev-tenderly.md) — per-chain RPC + MEV + Tenderly +
  gas oracle SSOT.
- [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md) — `BreakerAction` + `BreakerRecoveryMode`
  closed sets consumed by the MEV-driven breaker trigger above.
- [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md) — full breaker state machine including
  MEV-detection entry.
- [`kill-switch-event-bus.md`](kill-switch-event-bus.md) — `KillSwitchBus` event vocab for `MEV_DETECTED`.
- [`tenderly-execution-provider.md`](tenderly-execution-provider.md) — pre-flight simulation provider.
- [`interface-credential-convention.md`](interface-credential-convention.md) — wallet key injection.
- [`flash-loan-receiver.md`](flash-loan-receiver.md) — Aave flash loan receiver contract.
- [`defi-execution-overview.md`](defi-execution-overview.md) — full execution flow.
- [`execution-modes-and-chain-resolution.md`](execution-modes-and-chain-resolution.md) — chain environment resolution.
- [`/codex/07-security/secrets-management.md`](/codex/07-security/secrets-management.md) — Secret Manager key naming.
- [`/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md`](/codex/09-strategy/architecture-v2/cross-cutting/mev-protection.md)
  — strategy-side narrative on MEV policy + per-strategy config.

## Update protocol

- **Adding a new submission mode**: add to UAC `MevSubmissionMode` + `mev_router.py:_DEFAULT_POLICIES` +
  `defi_execution/mev/<provider>.py` + this doc's "MEV submission modes" + "Provider Implementations" + "Provider
  operational notes" tables.
- **Adding a new chain with MEV protection**: add to UAC `PROTECTED_RPC_URLS` + this doc's "Scope" + "How the System
  Protects" § 2 "Private RPC endpoints by chain" + `chain_config.yaml` + Phase 5B `RpcProviderFallback` config.
