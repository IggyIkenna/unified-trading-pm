---
scope: [engineer, admin]
---

# Custody Providers — single SSOT

This is the single SSOT for custody integration in the Unified Trading System. It folds in the previous per-provider
docs (`copper-custody-integration.md` + `ceffu-custody-integration.md`, both deleted 2026-05-08 per
[`../../plans/active/codex_refactor_2026_05_08.md`](../../plans/active/codex_refactor_2026_05_08.md) Phase D.4) so the
protocol + every provider implementation + coverage matrix + mode matrix all live in one file.

---

## §1 Overview / pluggable interface

The execution-service uses a pluggable `CustodyProvider` protocol to abstract transaction signing and wallet management.
The custodian is selected by configuration -- switching from Copper to Fireblocks (or any other MPC provider) requires
only a new implementation and a config change. Zero strategy or service code changes.

Location: `execution-service/execution_service/custody/`

The workspace runs **two production custody integrations in parallel**:

- **Copper.co** — covers DeFi (every chain) + non-Binance CeFi (Bybit, OKX, Deribit, Kraken, Aster, Hyperliquid). MPC
  signing.
- **CEFFU** — covers Binance institutional CeFi custody. Different protocol, different signing flow, but same
  `CustodyProvider` interface. Required because Binance routes institutional flows through CEFFU rather than Copper.

A position can be backed by either provider depending on venue. position-balance-monitor reads custody per (venue,
asset) pair from the registry; strategy + execution code never branch on provider. Adding a new custodian (e.g.
Fireblocks, Anchorage) means a new `CustodyProvider` implementation + a registry entry; zero strategy changes.

### CustodyProvider protocol

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

| Field                | Type   | Default  | Description                                           |
| -------------------- | ------ | -------- | ----------------------------------------------------- |
| `provider`           | `str`  | `"mock"` | Provider name: `copper`, `ceffu`, `local_key`, `mock` |
| `api_url`            | `str`  | `""`     | Custodian API endpoint                                |
| `credentials_secret` | `str`  | `""`     | Secret Manager key name                               |
| `api_key`            | `str`  | `""`     | Custodian API key (Copper / CEFFU HMAC key)           |
| `api_secret`         | `str`  | `""`     | Custodian API secret (Copper / CEFFU HMAC secret)     |
| `organization_id`    | `str`  | `""`     | Custodian org/account ID                              |
| `private_key`        | `str`  | `""`     | Raw private key (local_key provider, dev only)        |
| `rpc_url`            | `str`  | `""`     | RPC endpoint (local_key provider)                     |
| `sandbox`            | `bool` | `False`  | Use sandbox/testnet endpoint                          |

### Factory

`get_custody_provider(config: CustodyConfig)` in `custody/factory.py` routes on `config.provider`:

| `config.provider` | Implementation                       | Credentials required                       |
| ----------------- | ------------------------------------ | ------------------------------------------ |
| `"mock"`          | `MockCustodyProvider`                | None                                       |
| `"local_key"`     | `LocalKeyCustodyProvider`            | `private_key`, `rpc_url`                   |
| `"copper"`        | `CopperCustodyProvider`              | `api_key`, `api_secret`, `organization_id` |
| `"ceffu"`         | `CeffuCustodyProvider` (planned)     | `api_key`, `api_secret`, `organization_id` |
| unknown           | `MockCustodyProvider` (with warning) | None                                       |

Imports for `local_key`, `copper`, and `ceffu` are deferred (inside the routing branch) to avoid importing `web3` or
`httpx` when they are not needed.

---

## §2 Provider implementations

### §2.1 MockCustodyProvider

For testing and local development. No credentials, no network calls.

- `sign_transaction` -- returns SHA256 of input bytes as deterministic fake signature
- `get_balance` -- returns configurable default balance (`Decimal("100000")`)
- `create_transfer` -- records the transfer in an internal list, returns fake tx hash
- `list_wallets` -- returns hardcoded mock wallets (vault-eth-main, trading-aave-eth, trading-basis-eth)
- `set_balance(wallet_id, token, chain, balance)` -- configure mock balance for specific wallet/token
- `transfer_history` -- property exposing all recorded transfers for test assertions

### §2.2 LocalKeyCustodyProvider

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

Events: `LOCAL_KEY_TX_SIGNED`, `LOCAL_KEY_TRANSFER_SENT`.

### §2.3 CopperCustodyProvider

Production MPC signing via the Copper.co API. Private keys never leave the HSM. Copper.co provides institutional-grade
MPC (Multi-Party Computation) custody for digital assets — the private key is split across multiple parties (Copper,
client, backup) and never assembled. Signing requires coordinated computation.

**Why Copper:** Regulatory compliance, insurance, no single point of key compromise, sub-2-second signing latency.

Constructor:

| Parameter         | Type   | Description                                                                                          |
| ----------------- | ------ | ---------------------------------------------------------------------------------------------------- |
| `api_key`         | `str`  | Copper API key                                                                                       |
| `api_secret`      | `str`  | Copper HMAC-SHA256 secret                                                                            |
| `organization_id` | `str`  | Copper organization ID                                                                               |
| `sandbox`         | `bool` | If `True`, uses `https://api.sandbox.copper.co/platform`; otherwise `https://api.copper.co/platform` |

#### Authentication (HMAC-SHA256)

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

#### Core endpoints

| Endpoint                         | Method | Purpose                           |
| -------------------------------- | ------ | --------------------------------- |
| `/platform/wallets`              | GET    | List all wallets (treasury + hot) |
| `/platform/wallets/{id}/balance` | GET    | Get wallet balance per token      |
| `/platform/orders`               | POST   | Create transfer/withdrawal order  |
| `/platform/orders/{id}`          | GET    | Check order status                |
| `/platform/orders/{id}/sign`     | POST   | Initiate MPC signing              |
| `/platform/transactions`         | GET    | Transaction history               |

#### Wallet types in Copper

| Copper Term    | Our Term        | Purpose                             |
| -------------- | --------------- | ----------------------------------- |
| Vault          | Treasury wallet | Client-facing, deposits/withdrawals |
| Trading wallet | Hot wallet      | Strategy execution, per-strategy    |
| Archive        | Cold storage    | Long-term, rarely accessed          |

#### Transaction signing flow (CopperCustodyProvider.sign_transaction)

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

Polling: 1-second interval, max 30 attempts (30s timeout). On timeout, returns `SignedTransaction` with
`error="timeout"`.

Events emitted:

- `COPPER_TX_SIGNED` -- successful signing (includes order_id, tx_hash, wallet_id)
- `COPPER_TX_FAILED` -- signing failed or rejected (includes order_id, reason from statusDescription)
- `COPPER_TRANSFER_CREATED` -- transfer order created (includes order_id, from, to, token, amount)

#### CopperCustodyProvider methods

| Method             | Copper API                                                      | Details                                                              |
| ------------------ | --------------------------------------------------------------- | -------------------------------------------------------------------- |
| `sign_transaction` | POST /orders + POST /orders/{id}/sign + GET /orders/{id} (poll) | Creates order, initiates MPC, polls for completion                   |
| `get_balance`      | GET /wallets/{id}/balances                                      | Filters response by currency, returns available balance              |
| `create_transfer`  | POST /orders (orderType="withdraw")                             | Creates withdraw order with toAddress and amount                     |
| `list_wallets`     | GET /wallets                                                    | Maps Copper portfolioId/address/mainCurrency to standard dict format |

HTTP timeouts: 30s for signing/transfers, 10s for balance queries and wallet listing.

#### Supported chains (Copper)

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

#### Transfer policies (configurable in Copper dashboard)

- **Whitelist**: Only pre-approved destination addresses
- **Amount limits**: Max per-tx, max per-hour, max per-day
- **Auto-approve**: Transfers below threshold signed without human intervention
- **Multi-approve**: Large transfers require N-of-M human approvals
- **Time locks**: Withdrawals to new addresses delayed 24h

### §2.4 CeffuCustodyProvider — PLANNED

> **STATUS: STUB / PLANNED.** Created 2026-05-07 as a deep-audit follow-up to
> [`../../plans/active/master_to_live_defi_2026_05_23.md`](../../plans/active/master_to_live_defi_2026_05_23.md) Group F
> item 19 (Treasury / custody integration). Section content is pending — owners are whoever owns Binance institutional
> wiring (defi_master Fork 1 hedging-leg + master plan Group F item 19). Sub-headings below mirror the Copper section so
> the two can be read side-by-side once populated.

CEFFU (formerly Binance Custody) is the **institutional custody provider for Binance perp / spot exposure** in the
6-venue perp universe (Bybit / Deribit / Binance / OKX / Hyperliquid / Aster). The same pluggable `CustodyProvider`
interface used for Copper applies here — switching providers is a config change, not a code change.

**Why CEFFU:**

- AWS-compatible — wallet hosts can run AWS-resident (per master plan §"Decisions taken in-session" point 4 — custody
  provider AWS-compat is a precondition for the dual-cloud-active steady state).
- Native integration with Binance institutional flow (deposit/withdrawal via Binance APIs without bridging from a
  separate MPC provider).
- Sub-account model maps cleanly to per-strategy wallet hierarchy (see
  [`wallet-hierarchy-and-capital-flow.md`](wallet-hierarchy-and-capital-flow.md)).

**Scope of this integration:**

- Binance perp (carry_staked_basis hedge leg + leveraged_funding_arb cross-venue funding spread).
- Binance spot (collateral movement between perp and spot accounts).
- (Out of scope) Bybit, Deribit, OKX use their own institutional custody — Hyperliquid + Aster are on-chain-direct (no
  CEFFU equivalent, wallets sit at the smart-contract level).

#### Authentication / API architecture — PENDING

> CEFFU API auth shape, request signing, endpoint catalogue. Mirror the Copper subsection (Authentication, Core
> Endpoints, Wallet Types, Transaction Signing Flow, Supported Chains, Transfer Policies) when content authors populate.
> Reference: <https://www.ceffu.com/docs> (validate against current CEFFU institutional-API documentation).

#### CeffuCustodyProvider — PENDING

> `CeffuCustodyProvider` class in `execution-service/execution_service/custody/`. Mirror the Copper subsection
> (Constructor / Methods / Factory). The pluggable `CustodyProvider` interface in
> `unified-config-interface/testnet_contracts.py` drives the factory pattern.

#### Testing — PENDING

> Mock mode + integration tests + VCR cassettes — mirror Copper's `tests/integration/test_copper_custody_provider.py`
> shape under `tests/integration/test_ceffu_custody_provider.py`. Per CLAUDE.md "Testing Infrastructure" rule:
> credential-free local tests via `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`; cassette parity test in
> `unified-api-contracts/tests/test_cassette_schema_parity.py`.

#### Configuration — PENDING

> Environment variables, Secret Manager keys, per-strategy wallet mapping. Mirror Copper subsection. CEFFU credentials
> should follow the workspace HMAC-SHA256 pattern + `ApiKeyReloader` from UTL (per CLAUDE.md "Service Infrastructure
> Requirements" rule).

#### Open questions (CEFFU content authors)

- [ ] Does CEFFU expose a sub-account-per-strategy model out-of-the-box, or do we manage strategy-attribution ourselves
      at the application layer (PBMS) on top of a single CEFFU account?
- [ ] Is there a CEFFU-side equivalent to Copper's MPC + transfer-policy "circuit breaker" or do we rely on Binance
      account-level withdrawal limits + alerting-service kill switches?
- [ ] AWS-region pinning: is CEFFU's API endpoint region-specific (must we deploy to a particular AWS region for low
      latency) or is it global edge-cached?
- [ ] What's the cost / fee model? (Copper charges by AUM band; CEFFU's institutional pricing is bespoke per client.)
- [ ] Withdrawal whitelist management — is it API-driven or operator-driven via the CEFFU dashboard?

---

## §3 Coverage matrix per (asset_group, venue)

Which custody provider backs which venue / asset_group:

| asset_group | Venue                    | Custody Provider | Notes                                                             |
| ----------- | ------------------------ | ---------------- | ----------------------------------------------------------------- |
| cefi        | Binance (spot + perp)    | CEFFU (planned)  | Institutional flow routes through CEFFU, not Copper               |
| cefi        | Bybit                    | Copper           | MPC signing, sub-2s latency                                       |
| cefi        | OKX                      | Copper           | MPC signing                                                       |
| cefi        | Deribit                  | Copper           | MPC signing                                                       |
| cefi        | Kraken                   | Copper           | MPC signing                                                       |
| cefi        | Aster                    | Copper           | MPC signing                                                       |
| defi        | Hyperliquid              | Copper           | On-chain direct; wallets at the smart-contract level              |
| defi        | Aave / Uniswap / others  | Copper           | MPC signing per chain (ETH / ARB / Base / Optimism / Polygon)     |
| defi        | Solana DEXes (Pacifica…) | Copper           | In progress — Solana on Copper is "track availability" (see §2.3) |
| tradfi      | Future tradfi venues     | Copper or local  | TBD per venue                                                     |
| sports      | Betfair / exchanges      | per-venue        | Single sportsbook wallet; bookmaker handles custody natively      |
| prediction  | Polymarket / Kalshi      | Copper or local  | Wallet-managed; non-MPC for low-amount markets is acceptable      |

position-balance-monitor reads per-(venue, asset) custody from the registry; strategy + execution code never branch on
provider.

---

## §4 Mode matrix (testnet / paper / live)

| Pipeline Mode                        | Custody Provider      | Execution Provider                    | Chain interaction                                   |
| ------------------------------------ | --------------------- | ------------------------------------- | --------------------------------------------------- |
| batch (benchmark)                    | `mock`                | `BenchmarkFillProvider`               | None -- oracle-price fills                          |
| batch (fork)                         | `mock`                | `TenderlyExecutionProvider`           | Fork at historical block, `advance_time` per candle |
| paper                                | `mock` or `local_key` | `TenderlyExecutionProvider`           | Fork at latest block, real-time execution           |
| live (dev)                           | `local_key`           | Mainnet RPC (via CHAIN_RPC_TEMPLATES) | Real chain, raw key signing                         |
| live (prod, DeFi + non-Binance CeFi) | `copper`              | Mainnet RPC (via CHAIN_RPC_TEMPLATES) | Real chain, MPC signing                             |
| live (prod, Binance institutional)   | `ceffu` (planned)     | Binance institutional API             | Real venue, CEFFU signing                           |

In batch and paper modes, the mock custody provider is sufficient because the Tenderly fork does not require real
signatures -- transactions are executed directly on the fork. In live mode, the appropriate production provider signs
transactions before they are submitted to the real chain or institutional venue.

---

## §5 Per-strategy wallet mapping

Wallet mappings are managed via `WalletMappingConfig` in UAC (`internal/domain/defi/wallet_config.py`). The config is
loaded from GCS at `wallet-config/{chain_env}/wallet_mapping.json` and maps custodian wallets (treasury + trading) per
chain. Each `TradingWalletConfig` includes a `strategy_id` for per-strategy isolation and an optional
`max_allocation_usd` cap.

The `custodian` field is a reference to the system-level custody config. Changing custodians (e.g. Copper → Fireblocks,
or DeFi-side Copper → Binance-side CEFFU per venue) requires only updating `custody.provider` + adding a new
`CustodyProvider` implementation. Wallet IDs and strategy configs remain unchanged.

See [Wallet Hierarchy and Capital Flow](wallet-hierarchy-and-capital-flow.md) for the full `WalletMappingConfig` schema
and example JSON.

### Cross-strategy wallet concerns (DeFi)

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

---

## §6 Security

- **Copper MPC**: Private keys are split across multiple parties (Copper, client, backup) and never reassembled. Signing
  requires coordinated multi-party computation. Sub-2-second signing latency.
- **CEFFU (planned)**: Binance-institutional MPC equivalent. Same security model as Copper from the consumer's POV;
  exact key-shard topology + signing latency pending CEFFU integration spec.
- **LocalKeyCustodyProvider**: Raw private key in memory. Acceptable for development against Tenderly forks or testnets.
  Never use in production.
- **MockCustodyProvider**: Deterministic SHA256 signatures. No cryptographic security. Test-only.
- **Credential injection**: execution-service fetches all custody credentials from Secret Manager at startup and passes
  them to the factory via `CustodyConfig`. No credentials in environment variables or `.env` files.

---

## §7 Testing

### Mock mode (`CLOUD_MOCK_MODE=true`)

`MockCustodyProvider` used in all tests:

- `sign_transaction()` returns deterministic bytes (SHA256 of input)
- `get_balance()` returns configured mock balance
- `create_transfer()` returns fake tx hash, logs the transfer
- No network calls, no credentials needed

### Integration tests (`@pytest.mark.allow_network`)

Against Copper **sandbox environment**:

- Sandbox API: `https://api.sandbox.copper.co/platform/...`
- Sandbox credentials in Secret Manager: `copper-sandbox-api-key`
- Real MPC signing but on testnet wallets
- Skipped if sandbox credentials unavailable

CEFFU integration tests pending integration spec.

### VCR cassettes

Record provider API responses for replay in CI:

- `tests/cassettes/copper/sign_transfer.yaml`
- `tests/cassettes/copper/get_balance.yaml`
- Validated via `test_cassette_schema_parity.py`

---

## §8 Configuration

### Environment variables (via UnifiedCloudConfig)

| Variable           | Default     | Description                               |
| ------------------ | ----------- | ----------------------------------------- |
| `CUSTODY_PROVIDER` | `mock`      | `copper`, `ceffu`, `local_key`, or `mock` |
| `COPPER_API_URL`   | sandbox URL | `https://api.copper.co/platform` for prod |
| `CEFFU_API_URL`    | TBD         | CEFFU API endpoint per integration spec   |

### Secret Manager keys

| Secret                      | Environment  | Purpose                        |
| --------------------------- | ------------ | ------------------------------ |
| `copper-api-key`            | Production   | API authentication             |
| `copper-api-secret`         | Production   | HMAC signing                   |
| `copper-org-id`             | Production   | Organization ID                |
| `copper-sandbox-api-key`    | Staging/Test | Sandbox API key                |
| `copper-sandbox-api-secret` | Staging/Test | Sandbox HMAC                   |
| `ceffu-api-key`             | Production   | CEFFU authentication (planned) |
| `ceffu-api-secret`          | Production   | CEFFU HMAC signing (planned)   |

---

## §9 Adding a new custodian

1. Create `execution_service/custody/{name}.py` implementing the `CustodyProvider` protocol
2. Add a case to `get_custody_provider()` in `custody/factory.py`
3. Update `CustodyConfig` if new fields are needed
4. Update deployment configs to set `provider: "{name}"`
5. No strategy, connector, or service code changes required

---

## §10 References

- [Tenderly Execution Provider](tenderly-execution-provider.md) -- fork-based execution for batch/paper
- [Wallet Hierarchy and Capital Flow](wallet-hierarchy-and-capital-flow.md) -- treasury/trading wallet architecture
- [Interface Credential Convention](interface-credential-convention.md) -- how services get API keys
- [Flash Loan Receiver](flash-loan-receiver.md) -- DeFi atomic execution
- [`../../plans/active/master_to_live_defi_2026_05_23.md`](../../plans/active/master_to_live_defi_2026_05_23.md) Group F
  item 19 — live-trading prereq tracking (CEFFU integration)
- [`../../plans/active/defi_master_2026_05_07.md`](../../plans/active/defi_master_2026_05_07.md) Fork 1 — Binance perp
  hedging-leg ownership
