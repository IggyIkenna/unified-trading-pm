---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Custody Providers

## Overview

The execution-service uses a pluggable `CustodyProvider` protocol to abstract transaction signing and wallet management.
The custodian is selected by configuration -- switching from Copper to Fireblocks (or any other MPC provider) requires
only a new implementation and a config change. Zero strategy or service code changes.

Location: `execution-service/execution_service/custody/`

## CustodyProvider Protocol

Defined in `custody/base.py`. All custody implementations satisfy this protocol.

```python
class CustodyProvider(Protocol):
    async def sign_transaction(self, wallet_id: str, chain: str, raw_tx: bytes) -> SignedTransaction: ...
    async def get_balance(self, wallet_id: str, token: str, chain: str) -> Decimal: ...
    async def create_transfer(self, from_wallet_id: str, to_address: str, token: str, amount: Decimal, chain: str) -> str: ...
    async def list_wallets(self, chain: str | None = None) -> list[dict[str, str]]: ...
```

| Method             | Returns                     | Purpose                                              |
| ------------------ | --------------------------- | ---------------------------------------------------- |
| `sign_transaction` | `SignedTransaction`         | Sign raw tx bytes via the custodian                  |
| `get_balance`      | `Decimal`                   | Query wallet balance for a token on a chain          |
| `create_transfer`  | `str` (tx hash or order ID) | Build, sign, and submit a token transfer             |
| `list_wallets`     | `list[dict]`                | List available wallets, optionally filtered by chain |

### SignedTransaction

Returned by `sign_transaction`:

| Field        | Type          | Description                                            |
| ------------ | ------------- | ------------------------------------------------------ |
| `raw_signed` | `bytes`       | Signed transaction bytes, ready for RPC submission     |
| `tx_hash`    | `str`         | Transaction hash (hex)                                 |
| `wallet_id`  | `str`         | Custodian wallet ID that signed                        |
| `chain`      | `str`         | Target chain                                           |
| `provider`   | `str`         | Custody provider name (e.g. `"copper"`, `"local_key"`) |
| `error`      | `str \| None` | Error message if signing failed; `None` on success     |

### CustodyConfig

Frozen dataclass controlling provider selection and credentials:

| Field                | Type   | Default  | Description                                    |
| -------------------- | ------ | -------- | ---------------------------------------------- |
| `provider`           | `str`  | `"mock"` | Provider name: `copper`, `local_key`, `mock`   |
| `api_url`            | `str`  | `""`     | Custodian API endpoint                         |
| `credentials_secret` | `str`  | `""`     | Secret Manager key name                        |
| `api_key`            | `str`  | `""`     | Custodian API key (Copper HMAC key)            |
| `api_secret`         | `str`  | `""`     | Custodian API secret (Copper HMAC secret)      |
| `organization_id`    | `str`  | `""`     | Custodian org/account ID                       |
| `private_key`        | `str`  | `""`     | Raw private key (local_key provider, dev only) |
| `rpc_url`            | `str`  | `""`     | RPC endpoint (local_key provider)              |
| `sandbox`            | `bool` | `False`  | Use sandbox/testnet endpoint                   |

## Implementations

### MockCustodyProvider

For testing and local development. No credentials, no network calls.

- `sign_transaction` -- returns SHA256 of input bytes as deterministic fake signature
- `get_balance` -- returns configurable default balance (`Decimal("100000")`)
- `create_transfer` -- records the transfer in an internal list, returns fake tx hash
- `list_wallets` -- returns hardcoded mock wallets (vault-eth-main, trading-aave-eth, trading-basis-eth)
- `set_balance(wallet_id, token, chain, balance)` -- configure mock balance for specific wallet/token
- `transfer_history` -- property exposing all recorded transfers for test assertions

### CopperCustodyProvider

Production MPC signing via the Copper.co API. Private keys never leave the HSM.

Constructor:

| Parameter         | Type   | Description                                                                                          |
| ----------------- | ------ | ---------------------------------------------------------------------------------------------------- |
| `api_key`         | `str`  | Copper API key                                                                                       |
| `api_secret`      | `str`  | Copper HMAC-SHA256 secret                                                                            |
| `organization_id` | `str`  | Copper organization ID                                                                               |
| `sandbox`         | `bool` | If `True`, uses `https://api.sandbox.copper.co/platform`; otherwise `https://api.copper.co/platform` |

HMAC-SHA256 authentication on every request:

```
message = "{timestamp_ms}{METHOD}{path}{body}"
signature = HMAC-SHA256(api_secret, message)
Headers: ApiKey, Signature, Timestamp, Content-Type
```

Transaction signing flow:

1. `POST /orders` -- create an order with the raw unsigned transaction
2. `POST /orders/{id}/sign` -- initiate MPC signing across key shards
3. `GET /orders/{id}` -- poll until status is `completed`/`signed` or `failed`/`rejected`/`cancelled`

Polling: 1-second interval, max 30 attempts (30s timeout). On timeout, returns `SignedTransaction` with
`error="timeout"`.

Events emitted:

- `COPPER_TX_SIGNED` -- successful signing (includes order_id, tx_hash, wallet_id)
- `COPPER_TX_FAILED` -- signing failed or rejected (includes order_id, reason)
- `COPPER_TRANSFER_CREATED` -- transfer order created (includes order_id, from, to, token, amount)

### LocalKeyCustodyProvider

Development-only provider. Signs with a raw private key held in memory (fetched from Secret Manager at startup). Uses
Web3.py for signing and RPC interaction.

Constructor:

| Parameter     | Type  | Description                                           |
| ------------- | ----- | ----------------------------------------------------- |
| `private_key` | `str` | Hex-encoded private key (with or without `0x` prefix) |
| `rpc_url`     | `str` | JSON-RPC endpoint (Tenderly fork or testnet)          |

Capabilities:

- `sign_transaction` -- signs via `web3.eth.account.sign_transaction`, submits via `send_raw_transaction`
- `get_balance` -- queries native gas token balance via RPC (`eth_getBalance`)
- `create_transfer` -- builds a native token transfer tx, signs, and submits
- `list_wallets` -- returns single wallet derived from the private key

Supports chain ID resolution for: ETHEREUM (1), GOERLI (5), SEPOLIA (11155111), ARBITRUM (42161), OPTIMISM (10), POLYGON
(137), BSC (56), AVALANCHE (43114), BASE (8453). Numeric chain ID strings are also accepted.

Event: `LOCAL_KEY_TX_SIGNED`, `LOCAL_KEY_TRANSFER_SENT`

## Factory

`get_custody_provider(config: CustodyConfig)` in `custody/factory.py` routes on `config.provider`:

| `config.provider` | Implementation                       | Credentials required                       |
| ----------------- | ------------------------------------ | ------------------------------------------ |
| `"mock"`          | `MockCustodyProvider`                | None                                       |
| `"local_key"`     | `LocalKeyCustodyProvider`            | `private_key`, `rpc_url`                   |
| `"copper"`        | `CopperCustodyProvider`              | `api_key`, `api_secret`, `organization_id` |
| unknown           | `MockCustodyProvider` (with warning) | None                                       |

Imports for `local_key` and `copper` are deferred (inside the `if` branch) to avoid importing `web3` or `httpx` when
they are not needed.

## Pipeline Modes vs Providers

| Pipeline Mode     | Custody Provider      | Execution Provider                    | Chain interaction                                   |
| ----------------- | --------------------- | ------------------------------------- | --------------------------------------------------- |
| batch (benchmark) | `mock`                | `BenchmarkFillProvider`               | None -- oracle-price fills                          |
| batch (fork)      | `mock`                | `TenderlyExecutionProvider`           | Fork at historical block, `advance_time` per candle |
| paper             | `mock` or `local_key` | `TenderlyExecutionProvider`           | Fork at latest block, real-time execution           |
| live (dev)        | `local_key`           | Mainnet RPC (via CHAIN_RPC_TEMPLATES) | Real chain, raw key signing                         |
| live (prod)       | `copper`              | Mainnet RPC (via CHAIN_RPC_TEMPLATES) | Real chain, MPC signing                             |

In batch and paper modes, the mock custody provider is sufficient because the Tenderly fork does not require real
signatures -- transactions are executed directly on the fork. In live mode, CopperCustodyProvider signs transactions via
MPC before they are submitted to the real chain.

## Security

- **Copper MPC**: Private keys are split across multiple parties (Copper, client, backup) and never reassembled. Signing
  requires coordinated multi-party computation. Sub-2-second signing latency.
- **LocalKeyCustodyProvider**: Raw private key in memory. Acceptable for development against Tenderly forks or testnets.
  Never use in production.
- **MockCustodyProvider**: Deterministic SHA256 signatures. No cryptographic security. Test-only.
- **Credential injection**: execution-service fetches all custody credentials from Secret Manager at startup and passes
  them to the factory via `CustodyConfig`. No credentials in environment variables or `.env` files.

## Adding a New Custodian

1. Create `execution_service/custody/{name}.py` implementing the `CustodyProvider` protocol
2. Add a case to `get_custody_provider()` in `custody/factory.py`
3. Update `CustodyConfig` if new fields are needed
4. Update deployment configs to set `provider: "{name}"`
5. No strategy, connector, or service code changes required

## References

- [Copper Custody Integration](copper-custody-integration.md) -- Copper API details, endpoints, policies
- [Tenderly Execution Provider](tenderly-execution-provider.md) -- fork-based execution
- [Wallet Hierarchy and Capital Flow](wallet-hierarchy-and-capital-flow.md) -- treasury/trading wallet architecture
- [Interface Credential Convention](interface-credential-convention.md) -- how services get API keys
