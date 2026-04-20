---
scope: [engineer, admin]
---

# MEV Protection

MEV (Maximal Extractable Value) is the profit that block builders or validators can extract by reordering, inserting, or
censoring transactions within a block. For DeFi swap transactions this most often manifests as **sandwich attacks**: a
bot front-runs your swap with a buy, pushing the price up, then sells immediately after your trade is included.

This document describes the MEV protection architecture used by execution-service for all on-chain DeFi transactions.

## Threat Model

| Attack type        | Description                                                         | Affected operations         |
| ------------------ | ------------------------------------------------------------------- | --------------------------- |
| Sandwich attack    | Front-run + back-run around a swap tx                               | SWAP (Uniswap V2/V3, Curve) |
| Front-running      | Copy + beat a profitable tx to the same block                       | Flash loans, large swaps    |
| Liquidation racing | Competing bots racing to liquidate an under-collateralised position | Aave/Compound liquidations  |
| Time-bandit        | Reorg attack to steal profits from committed txs                    | Any (extremely rare)        |

**Scope**: MEV protection is **only active on Ethereum mainnet** (`chain_id = 1`). On L2s (Arbitrum, Base, Optimism,
Polygon) the sequencer is centralised and there is no public mempool, making MEV extraction structurally infeasible.

## Architecture

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

`get_mev_provider(mode, chain_id, ...)` in the same module selects the appropriate provider:

| Condition                             | Provider                 | Behaviour                             |
| ------------------------------------- | ------------------------ | ------------------------------------- |
| `mode` in `paper`, `batch`, `testnet` | `NoProtectionProvider`   | No-op; logs only                      |
| `chain_id == 1` and `relay_url` set   | `FlashbotsProvider`      | Bundle relay via custom URL           |
| `chain_id == 1` (default)             | `PrivateMempoolProvider` | `https://rpc.flashbots.net` (Protect) |
| `chain_id != 1`                       | `NoProtectionProvider`   | L2 sequencer, no public mempool       |

### Protected RPC URLs (SSOT)

`PROTECTED_RPC_URLS` in `unified_api_contracts.registry.capability_declarations._defi` is the single source of truth for
all MEV-resistant RPC endpoints. Connectors **must** import from UAC and never hardcode these URLs.

```python
from unified_api_contracts.registry import PROTECTED_RPC_URLS

# PROTECTED_RPC_URLS = {
#     "ETHEREUM":        "https://rpc.flashbots.net",       # Flashbots Protect
#     "ETHEREUM_BUNDLE": "https://relay.flashbots.net",     # Flashbots Bundle relay
#     "MEV_BLOCKER":     "https://rpc.mevblocker.io",       # CoW Protocol MEV Blocker
# }
```

### Handler Integration

`SwapHandler` (execution-service) holds a `_mev_provider` instance created from `MEVProtectionConfig`:

1. `__init__` builds the provider from the `"mev_protection"` key in handler config.
2. `_execute_with_matching_engine` logs the active provider for observability.
3. The actual **transaction signing and submission** is done by `UniswapConnector.swap_exact_input()`, which must call
   `self._mev_provider.submit_transaction(signed_tx, chain_id)` after constructing the signed calldata.

This separation keeps the matching logic in the handler and the on-chain I/O in the connector.

## Provider Implementations

### NoProtectionProvider

Located at `execution_service.defi_execution.mev.no_protection`. Used for paper/batch/testnet modes and all non-Ethereum
chains. `submit_transaction` and `submit_bundle` are stubs that return a mock `TxSubmissionResult`.

### PrivateMempoolProvider

Located at `execution_service.defi_execution.mev.private_mempool`. Submits transactions to `https://rpc.flashbots.net`
(Flashbots Protect RPC). Transactions go directly to Flashbots block builders bypassing the public mempool — invisible
to searcher bots.

- No auth required (unlike full Flashbots bundles)
- Single tx only (no atomicity guarantees)
- Best for simple swaps and collateral deposits

### FlashbotsProvider

Located at `execution_service.defi_execution.mev.flashbots`. Submits **signed bundles** to the Flashbots relay endpoint
(`https://relay.flashbots.net` or custom). Requires `eth_sign` from a searcher key (not the trading wallet key).

- Atomic multi-tx bundles
- Explicit target block number
- Used for flash loan sequences where atomicity is required
- Higher complexity; use only when `NoProtectionProvider` or `PrivateMempoolProvider` are insufficient

## Slippage as MEV Defence

MEV protection reduces but does not eliminate slippage attacks. `SwapHandler.validate()` enforces a 500 bps (5%) hard
cap on `max_slippage_bps`. Tighter slippage settings reduce sandwich profitability:

- Recommended: `max_slippage_bps ≤ 30` (0.3%) for liquid pairs
- Large orders: `max_slippage_bps ≤ 100` (1%) with position split via `AlgoComparisonRunner`

## Testing

- **Unit tests**: mock `MEVProtectionProvider` via `unittest.mock.AsyncMock`. Never call real RPCs.
- **Integration tests**: use the Tenderly fork fixtures in `execution-service/tests/integration/conftest.py`. These are
  `@pytest.mark.allow_network` and skipped without SM credentials.
- **Paper mode**: set `MEVProtectionConfig(mode="paper")` — routes to `NoProtectionProvider`.

## Operational Run-Book

1. **Mainnet swap reverts** — check if `max_slippage_bps` is too tight. Increase to 50–100 bps.
2. **Bundle not included after 12s** — increase `max_block_offset` to 5 and retry.
3. **Flashbots relay unreachable** — fall back to `PrivateMempoolProvider` by removing `relay_url` from config.
4. **L2 deployment** — confirm `chain_id != 1`; MEV protection auto-disables (no action needed).

## Related Docs

- `codex/04-architecture/interface-credential-convention.md` — wallet key injection
- `codex/04-architecture/flash-loan-receiver.md` — Aave flash loan receiver contract
- `codex/07-security/secrets-management.md` — Secret Manager key naming
