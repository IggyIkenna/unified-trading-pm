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
| `"ceffu"`         | `CeffuCustodyProvider` (stub-shipped, methods raise) | `api_key`, `api_secret`, `organization_id` |
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

### §2.4 CeffuCustodyProvider — STUB SHIPPED, API spec pending

> **STATUS: STUB SHIPPED 2026-05-10.** `CeffuCustodyProvider` exists in
> `execution-service/execution_service/custody/ceffu.py` with a fully-wired constructor, factory registration,
> HMAC-SHA256 signing skeleton, and async-method stubs that raise `NotImplementedError("CEFFU API spec pending — ...")`.
> The pluggable interface envelope is in place so the eventual real implementation drops in as a tightly-scoped diff.
> Real REST endpoints + sandbox URL + sub-account model are pending operator confirmation per the open questions below.
> Master plan Group F Item 19 reflects: stub-shipped (CeFi institutional flow envelope reachable from factory) +
> live-only run-to-completion blocked on operator-provided API spec.

CEFFU (formerly Binance Custody) is the **institutional custody provider for Binance perp / spot exposure** in the
6-venue perp universe (Bybit / Deribit / Binance / OKX / Hyperliquid / Aster). The same pluggable `CustodyProvider`
interface used for Copper applies here — switching providers is a config change, not a code change.

**Why CEFFU:**

- AWS-compatible — wallet hosts can run AWS-resident (per master plan §"Decisions taken in-session" point 4 — custody
  provider AWS-compat is a precondition for the dual-cloud-active steady state).
- Native integration with Binance institutional flow (deposit/withdrawal via Binance APIs without bridging from a
  separate MPC provider).
- Off-exchange settlement (OES) — institutional clients hold collateral at CEFFU custody accounts and trade on Binance
  Futures with that collateral as margin. Collateral never leaves custody; daily settlement of P&L mirrors back to CEFFU
  per the bilateral / triparty model.
- Sub-account model maps cleanly to per-strategy wallet hierarchy (see
  [`wallet-hierarchy-and-capital-flow.md`](wallet-hierarchy-and-capital-flow.md)).

**Scope of this integration:**

- Binance perp (carry_staked_basis hedge leg + leveraged_funding_arb cross-venue funding spread).
- Binance spot (collateral movement between perp and spot accounts).
- (Out of scope) Bybit, Deribit, OKX use their own institutional custody — Hyperliquid + Aster are on-chain-direct (no
  CEFFU equivalent, wallets sit at the smart-contract level).

#### Architecture overview

End-to-end flow for a Binance institutional position backed by CEFFU OES:

```
Client → CEFFU custody account → Binance Futures (via OES bilateral mirror)
                                       │
                                       ├── Strategy issues order via execution-service
                                       │
                                       ├── Position entered on Binance Futures
                                       │   (collateral remains at CEFFU; mirror credit at Binance)
                                       │
                                       └── Daily mark-to-market + P&L settlement
                                            ↑
                                            └── CEFFU adjusts custody balance to reflect
                                                realised + unrealised P&L (settlement window)
```

The custody-side balance at CEFFU is the source of truth for available collateral; the venue-side margin at Binance is
a mirror. position-balance-monitor reads custody balance per `(venue=binance, asset)` from the CEFFU provider and
reconciles against Binance's reported margin to detect mirror drift.

#### Onboarding flow (operator runbook)

1. **Binance institutional account.** Operator signs the Binance Institutional Services agreement, opening an OES-
   eligible Binance Futures account. CEFFU is named as the off-exchange custodian.
2. **CEFFU institutional account.** Operator signs the CEFFU custody agreement, receives institutional account ID +
   API credentials (HMAC key + secret, parity expectations with Copper). CEFFU enables the OES bilateral mirror to the
   Binance account opened in step 1.
3. **Sandbox onboarding.** Operator requests CEFFU sandbox credentials separately. Sandbox base URL +
   sub-account-model details are <TBD-OPERATOR-PROVIDES-API-SPEC> — populate once received.
4. **Secret Manager wiring.** Credentials stored under `ceffu-api-key` / `ceffu-api-secret` / `ceffu-org-id` (production)
   and `ceffu-sandbox-api-key` / `ceffu-sandbox-api-secret` (staging/test). `ApiKeyReloader` from UTL handles hot-reload
   per workspace standard.
5. **execution-service config flip.** Set `CUSTODY_PROVIDER=ceffu` for the Binance institutional execution flow;
   non-Binance CeFi + DeFi continue routing through Copper. Wallet mapping in
   `gs://wallet-config-{pid}/wallet_mapping.json` declares `custodian: ceffu` for Binance treasury + trading sub-
   accounts.
6. **Dry-run + paper-trade.** Sandbox flow validates onboarding before any production capital moves. Master plan
   Group F Item 19 paper-trade smoke validates this end-to-end.

#### API integration — PENDING SPEC

The exact REST endpoint catalogue is <TBD-OPERATOR-PROVIDES-API-SPEC>. Expected shape (mirror Copper § 2.3.5 once
confirmed):

| Capability         | Expected method | Path                                | Notes                                              |
| ------------------ | --------------- | ----------------------------------- | -------------------------------------------------- |
| Balance query      | GET             | `/<TBD>/accounts/{id}/balances`     | Per token, per chain                               |
| Collateral move    | POST            | `/<TBD>/oes/transfers`              | Custody → Binance margin and reverse               |
| Settlement query   | GET             | `/<TBD>/oes/settlements?from&to`    | Daily P&L reconciliation                           |
| Sign transaction   | POST            | `/<TBD>/orders` + `/<TBD>/sign`     | Parity with Copper's two-step MPC signing          |
| List sub-accounts  | GET             | `/<TBD>/accounts`                   | Sub-account-per-strategy model decision pending    |

#### Authentication / signing — skeleton in place, header names TBD

`CeffuCustodyProvider._sign_request()` currently uses HMAC-SHA256 over `{timestamp_ms}{METHOD}{path}{body}` and emits
Copper-style headers (`ApiKey` / `Signature` / `Timestamp` / `Content-Type`). This is a placeholder shape — the final
header naming convention is <TBD-OPERATOR-PROVIDES-API-SPEC> (CEFFU may use `X-CEFFU-*` style or a different signing
canonicalisation). The skeleton is wired in advance so the eventual real wiring is a header-rename diff plus a base-URL
fill, not an architecture change.

#### Sandbox / staging — PENDING

Sandbox base URL: `<TBD-OPERATOR-PROVIDES-API-SPEC>`. Sandbox credentials are kept separate in Secret Manager
(`ceffu-sandbox-api-key` / `ceffu-sandbox-api-secret`) so paper-trade smokes never accidentally hit production. Set
`CustodyConfig.sandbox=True` to route to sandbox at provider construction.

#### Daily operational flow

| Phase             | Time (UTC)               | Action                                                                                  |
| ----------------- | ------------------------ | --------------------------------------------------------------------------------------- |
| Mark-to-market    | Continuous (per Binance) | Binance recalculates margin per tick; mirror credit at CEFFU updates intraday           |
| Settlement window | <TBD> daily              | CEFFU finalises end-of-day P&L; custody balance adjusted; alerting-service confirms     |
| Margin recall     | On threshold breach      | Position-balance-monitor triggers transfer from CEFFU treasury → Binance trading sub-account |
| Reconciliation    | Post-settlement          | batch-vs-live reconciler asserts `custody_balance + position_unrealised == ledger_total`    |

The exact settlement window timing is <TBD-OPERATOR-PROVIDES-API-SPEC> — populate once CEFFU confirms.

#### Risk controls

- **Credit-utilisation cap** — kill-switch rule fires when `position_notional / custody_balance > threshold` per the
  alerting-service `LIVE_RISK_KILL_SWITCH` ruleset (see [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md)).
- **Automatic margin recall threshold** — position-balance-monitor triggers proactive collateral transfer when the
  Binance-side margin ratio drops below `recall_threshold` (default 1.5x maintenance).
- **Withdrawal whitelist** — destination addresses must be pre-approved. Whitelist management is API-driven vs operator-
  driven via the CEFFU dashboard: <TBD-OPERATOR-PROVIDES-API-SPEC> — populate once the CEFFU account model is confirmed.
- **Rate-limit + backoff** — every CEFFU API call routes through UAC `classify_venue_error()` per workspace adapter
  rule; transient 5xx + 429 retried with exponential backoff; 4xx auth/whitelist errors surface as `ADAPTER_FETCH_FAILED`
  events without retry (per the no-fire-and-forget principle).

#### CeffuCustodyProvider implementation reference

`execution-service/execution_service/custody/ceffu.py` (stub shipped 2026-05-10):

| Component            | Status                | Detail                                                                                          |
| -------------------- | --------------------- | ----------------------------------------------------------------------------------------------- |
| Constructor          | ✅ Wired              | Accepts `api_key` / `api_secret` / `organization_id` / `sandbox` parity with Copper             |
| `_sign_request`      | ✅ Skeleton wired     | HMAC-SHA256 placeholder; final header names + canonicalisation pending API spec                 |
| `sign_transaction`   | ❌ NotImplementedError | Raises with operator-action prompt + reference to this codex doc                                |
| `get_balance`        | ❌ NotImplementedError | Same                                                                                            |
| `create_transfer`    | ❌ NotImplementedError | Same                                                                                            |
| `list_wallets`       | ❌ NotImplementedError | Same                                                                                            |
| Factory registration | ✅ Live               | `get_custody_provider(CustodyConfig(provider="ceffu", ...))` returns `CeffuCustodyProvider`     |

Tests: `execution-service/tests/unit/custody/test_ceffu_provider.py` — 11 tests covering construction + factory
registration + every async method's NotImplementedError contract.

#### Configuration

| Variable           | Default                       | Description                                            |
| ------------------ | ----------------------------- | ------------------------------------------------------ |
| `CUSTODY_PROVIDER` | `mock`                        | Set to `ceffu` for Binance institutional flow         |
| `CEFFU_API_URL`    | `<TBD-OPERATOR-PROVIDES-API-SPEC>` | Production endpoint; sandbox toggled via `sandbox=True` |

Secret Manager keys are listed in §8 Configuration below alongside Copper's.

#### Testing

- **Mock mode** — `MockCustodyProvider` covers every test path that doesn't specifically exercise CEFFU's signing
  surface; CEFFU is only constructed when integration tests are explicitly tagged with `@pytest.mark.allow_network` and
  CEFFU sandbox credentials are wired in CI.
- **Stub-state unit tests** — every async method's NotImplementedError contract is asserted in
  `tests/unit/custody/test_ceffu_provider.py` so a future agent can't silently flip a method to a partial implementation
  without paired test updates.
- **Sandbox integration tests** — `tests/integration/test_ceffu_custody_provider.py` is **PENDING** until CEFFU sandbox
  credentials + API spec land. Cassette path will be `tests/cassettes/ceffu/{sign,balance}.yaml` validated via
  `unified-api-contracts/tests/test_cassette_schema_parity.py`.

#### Open questions (CEFFU content authors / operator triage)

- [ ] Does CEFFU expose a sub-account-per-strategy model out-of-the-box, or do we manage strategy-attribution ourselves
      at the application layer (PBMS) on top of a single CEFFU account?
- [ ] Is there a CEFFU-side equivalent to Copper's MPC + transfer-policy "circuit breaker" or do we rely on Binance
      account-level withdrawal limits + alerting-service kill switches?
- [ ] AWS-region pinning: is CEFFU's API endpoint region-specific (must we deploy to a particular AWS region for low
      latency) or is it global edge-cached?
- [ ] What's the cost / fee model? (Copper charges by AUM band; CEFFU's institutional pricing is bespoke per client.)
- [ ] Withdrawal whitelist management — is it API-driven or operator-driven via the CEFFU dashboard?
- [ ] Daily settlement window timing — what UTC hour does CEFFU finalise end-of-day P&L?
- [ ] Exact REST endpoint paths + authentication header naming convention (Copper-style vs CEFFU-specific).
- [ ] Sandbox base URL for staging-only paper-trade smokes.

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
- **CEFFU (stub-shipped, API spec pending)**: Binance-institutional MPC for OES (off-exchange settlement). Same security
  model as Copper from the consumer's POV; exact key-shard topology + signing latency pending CEFFU integration spec.
  Provider envelope + factory registration + HMAC signing skeleton are wired in `execution_service/custody/ceffu.py`;
  async methods raise `NotImplementedError("CEFFU API spec pending")` until the operator confirms REST endpoints +
  sandbox URL + sub-account model.
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

CEFFU integration tests pending integration spec — `tests/integration/test_ceffu_custody_provider.py` will mirror the
Copper integration shape once sandbox credentials + REST endpoints are confirmed (see § 2.4 Open questions). Stub-state
unit tests covering construction + factory registration + NotImplementedError contracts already live at
`tests/unit/custody/test_ceffu_provider.py`.

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
