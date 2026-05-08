---
scope: [engineer, admin]
---

# Copper Custody Integration

## Overview

The system uses a pluggable custody provider interface. Currently configured: **Copper.co** (MPC). The custodian is
configurable — switching from Copper to Fireblocks, Anchorage, or any other MPC provider requires only a new
`CustodyProvider` implementation + config change. No strategy or service code changes.

Copper.co provides institutional-grade MPC (Multi-Party Computation) custody for digital assets. The private key is
split across multiple parties (Copper, client, backup) and never assembled — signing requires coordinated computation.

**Why Copper:** Regulatory compliance, insurance, no single point of key compromise, sub-2-second signing latency.

## API Architecture

### Authentication (HMAC-SHA256)

Every request is signed with HMAC-SHA256. The `CopperCustodyProvider._sign_request()` method generates headers:

```
message = "{timestamp_ms}{METHOD}{path}{body}"
signature = HMAC-SHA256(api_secret, message)

Headers:
  ApiKey: {api_key}
  Signature: {hmac_hex}
  Timestamp: {unix_ms}
  Content-Type: application/json
```

API endpoints:

- Production: `https://api.copper.co/platform`
- Sandbox: `https://api.sandbox.copper.co/platform`

API credentials stored in Secret Manager:

- `copper-api-key` -- API key for authentication
- `copper-api-secret` -- HMAC signing secret
- `copper-org-id` -- Organization identifier

### Core Endpoints

| Endpoint                         | Method | Purpose                           |
| -------------------------------- | ------ | --------------------------------- |
| `/platform/wallets`              | GET    | List all wallets (treasury + hot) |
| `/platform/wallets/{id}/balance` | GET    | Get wallet balance per token      |
| `/platform/orders`               | POST   | Create transfer/withdrawal order  |
| `/platform/orders/{id}`          | GET    | Check order status                |
| `/platform/orders/{id}/sign`     | POST   | Initiate MPC signing              |
| `/platform/transactions`         | GET    | Transaction history               |

### Wallet Types in Copper

| Copper Term    | Our Term        | Purpose                             |
| -------------- | --------------- | ----------------------------------- |
| Vault          | Treasury wallet | Client-facing, deposits/withdrawals |
| Trading wallet | Hot wallet      | Strategy execution, per-strategy    |
| Archive        | Cold storage    | Long-term, rarely accessed          |

### Transaction Signing Flow (CopperCustodyProvider.sign_transaction)

Implemented in `execution_service/custody/copper.py`:

```
1. execution-service builds raw transaction (unsigned bytes)
2. POST /orders -- create order with rawTransaction (hex-encoded),
   organizationId, portfolioId (wallet_id), orderType="withdraw",
   extra={"chain": chain}
3. Copper validates: amount limits, whitelist, policy checks
4. POST /orders/{orderId}/sign -- initiate MPC signing
5. GET /orders/{orderId} -- poll every 1s, max 30 attempts
   - status "completed"/"signed" -> return SignedTransaction
   - status "failed"/"rejected"/"cancelled" -> return SignedTransaction with error
   - timeout after 30s -> return SignedTransaction with error="timeout"
6. execution-service submits signed tx to blockchain RPC
```

Events emitted:

- `COPPER_TX_SIGNED` on success (includes order_id, tx_hash, wallet_id)
- `COPPER_TX_FAILED` on failure (includes order_id, reason from statusDescription)

### Supported Chains

| Chain     | Copper Support | Our Integration    |
| --------- | -------------- | ------------------ |
| Ethereum  | Full (EVM)     | Production ready   |
| Arbitrum  | Full (EVM)     | Production ready   |
| Base      | Full (EVM)     | Production ready   |
| Optimism  | Full (EVM)     | Production ready   |
| Polygon   | Full (EVM)     | Production ready   |
| BSC       | Full (EVM)     | Production ready   |
| Avalanche | Full (EVM)     | Production ready   |
| Solana    | In progress    | Track availability |

### Transfer Policies (Configurable in Copper Dashboard)

- **Whitelist**: Only pre-approved destination addresses
- **Amount limits**: Max per-tx, max per-hour, max per-day
- **Auto-approve**: Transfers below threshold signed without human intervention
- **Multi-approve**: Large transfers require N-of-M human approvals
- **Time locks**: Withdrawals to new addresses delayed 24h

## Integration in execution-service

Full protocol, implementations, and factory details: [Custody Providers](custody-providers.md).

### CopperCustodyProvider Constructor

```python
class CopperCustodyProvider:
    def __init__(
        self,
        api_key: str,       # Copper API key
        api_secret: str,    # HMAC-SHA256 signing secret
        organization_id: str,  # Copper org ID
        sandbox: bool = False, # True -> sandbox API endpoint
    ) -> None: ...
```

### CopperCustodyProvider Methods

| Method             | Copper API                                                      | Details                                                              |
| ------------------ | --------------------------------------------------------------- | -------------------------------------------------------------------- |
| `sign_transaction` | POST /orders + POST /orders/{id}/sign + GET /orders/{id} (poll) | Creates order, initiates MPC, polls for completion                   |
| `get_balance`      | GET /wallets/{id}/balances                                      | Filters response by currency, returns available balance              |
| `create_transfer`  | POST /orders (orderType="withdraw")                             | Creates withdraw order with toAddress and amount                     |
| `list_wallets`     | GET /wallets                                                    | Maps Copper portfolioId/address/mainCurrency to standard dict format |

### Factory

```python
def get_custody_provider(config: CustodyConfig) -> CustodyProvider:
    # config.provider == "copper" -> CopperCustodyProvider(api_key, api_secret, organization_id, sandbox)
    # config.provider == "local_key" -> LocalKeyCustodyProvider(private_key, rpc_url)
    # config.provider == "mock" or unknown -> MockCustodyProvider()
```

HTTP timeouts: 30s for signing/transfers, 10s for balance queries and wallet listing.

## Testing

### Mock Mode (`CLOUD_MOCK_MODE=true`)

`MockCustodyProvider` used in all tests:

- `sign_transaction()` returns deterministic bytes (SHA256 of input)
- `get_balance()` returns configured mock balance
- `create_transfer()` returns fake tx hash, logs the transfer
- No network calls, no credentials needed

### Integration Tests (`@pytest.mark.allow_network`)

Against Copper **sandbox environment**:

- Sandbox API: `https://api.sandbox.copper.co/platform/...`
- Sandbox credentials in Secret Manager: `copper-sandbox-api-key`
- Real MPC signing but on testnet wallets
- Skipped if sandbox credentials unavailable

### VCR Cassettes

Record Copper API responses for replay in CI:

- `tests/cassettes/copper/sign_transfer.yaml`
- `tests/cassettes/copper/get_balance.yaml`
- Validated via `test_cassette_schema_parity.py`

## Configuration

### Environment Variables (via UnifiedCloudConfig)

| Variable           | Default     | Description                               |
| ------------------ | ----------- | ----------------------------------------- |
| `CUSTODY_PROVIDER` | `mock`      | `copper`, `local_key`, or `mock`          |
| `COPPER_API_URL`   | sandbox URL | `https://api.copper.co/platform` for prod |

### Secret Manager Keys

| Secret                      | Environment  | Purpose            |
| --------------------------- | ------------ | ------------------ |
| `copper-api-key`            | Production   | API authentication |
| `copper-api-secret`         | Production   | HMAC signing       |
| `copper-org-id`             | Production   | Organization ID    |
| `copper-sandbox-api-key`    | Staging/Test | Sandbox API key    |
| `copper-sandbox-api-secret` | Staging/Test | Sandbox HMAC       |

### Per-Strategy Wallet Mapping

Wallet mappings are now managed via `WalletMappingConfig` in UAC (`internal/domain/defi/wallet_config.py`). The config
is loaded from GCS at `wallet-config/{chain_env}/wallet_mapping.json` and maps custodian wallets (treasury + trading)
per chain. Each `TradingWalletConfig` includes a `strategy_id` for per-strategy isolation and an optional
`max_allocation_usd` cap.

The `custodian` field is a reference to the system-level custody config. Changing custodians (e.g. Copper → Fireblocks)
requires only updating `custody.provider` + adding a new `CustodyProvider` implementation. Wallet IDs and strategy
configs remain unchanged.

See [Wallet Hierarchy and Capital Flow](wallet-hierarchy-and-capital-flow.md) for the full `WalletMappingConfig` schema
and example JSON.

## Cross-Strategy Wallet Concerns

| Strategy Type      | Treasury? | Hot Wallet?       | CeFi Sub-Account?                | Bridge?           |
| ------------------ | --------- | ----------------- | -------------------------------- | ----------------- |
| AAVE_LENDING       | Yes (20%) | Yes (ETH)         | No                               | No                |
| BASIS_TRADE        | Yes (20%) | Yes (ETH)         | Yes (HL/Binance/OKX/Bybit/Aster) | No                |
| RECURSIVE_STAKED   | Yes (20%) | Yes (ETH)         | Yes (HL for hedge)               | No                |
| STAKED_BASIS       | Yes (20%) | Yes (ETH)         | Yes (HL for hedge)               | No                |
| L2_BASIS           | Yes (20%) | Yes (Arbitrum)    | Yes (HL)                         | Yes (ETH→ARB)     |
| MULTICHAIN_LENDING | Yes (20%) | Yes (multi-chain) | No                               | Yes (cross-chain) |
| SOL_BASIS          | Yes (20%) | Yes (Solana)      | Yes (Drift)                      | Yes (ETH→SOL)     |
| ETHENA_BENCHMARK   | Yes (20%) | Yes (ETH)         | No                               | No                |
| AMM_LP             | Yes (20%) | Yes (ETH)         | No                               | No                |
| BTC_BASIS          | Yes (20%) | Yes (ETH)         | Yes (Binance)                    | No                |
| CROSS_CHAIN_SOR    | Yes (20%) | Yes (multi-chain) | No                               | Yes               |
| Sports strategies  | No        | Single wallet     | Yes (Betfair/exchange)           | No                |

## References

- [Custody Providers](custody-providers.md) -- full protocol, all implementations, pipeline mode matrix
- [Tenderly Execution Provider](tenderly-execution-provider.md) -- fork-based execution for batch/paper
- [Wallet Hierarchy](wallet-hierarchy-and-capital-flow.md) -- capital flow architecture
- [Interface Credential Convention](interface-credential-convention.md) -- how services get keys
- [Flash Loan Receiver](flash-loan-receiver.md) -- DeFi atomic execution
