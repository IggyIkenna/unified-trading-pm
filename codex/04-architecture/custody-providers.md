---
doc_type: codex-ssot
title: Custody Providers — single SSOT
summary: "Single SSOT for custody integration: the pluggable CustodyProvider protocol + all implementations
  (mock/local_key/cloud_kms/copper/ceffu/fireblocks), factory + SigningSurface mapping, per-(asset_group,venue) coverage
  matrix, mode matrix, and the §10A custody-ping health-check contract. May-23 default is CLOUD_KMS_ENCRYPTED."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: [custody, copper, ceffu, cloud-kms, execution, health-check]
related:
  [
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
    /codex/04-architecture/interface-credential-convention.md,
    /codex/04-architecture/circuit-breaker-rule-taxonomy.md,
    /codex/15-runbooks/custody-onboarding-checklist.md,
  ]
created: 2026-03-30
authoritative_for: [custody provider protocol and implementations, custody-ping health-check contract]
referenced_by:
  [
    /codex/04-architecture/client-funds-isolation.md,
    /codex/04-architecture/custody-architecture.md,
    /codex/04-architecture/defi-execution-overview.md,
    /codex/04-architecture/defi-phase3-infrastructure.md,
    /codex/04-architecture/execution-modes-and-chain-resolution.md,
    /codex/04-architecture/interface-credential-convention.md,
    /codex/04-architecture/separation-of-concerns.md,
    /codex/04-architecture/strategy-ensemble-topology.md,
  ]
owner:
last_reviewed: 2026-08-19
code_refs:
---

# Custody Providers — single SSOT

> **🟢 R9 sub-(a) RESOLVED 2026-05-12** — per
> [`/plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md`](/plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md)
> § R9 RESOLVED: **May-23 cutover ships on `CLOUD_KMS_ENCRYPTED`** (HSM-backed CMK envelope encryption); **June-1 flips
> per-wallet to `COPPER_MPC` / CEFFU** on POD-provided creds. Per-wallet `signing_surface` field on
> `WalletProvisioningConfig` (`unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py`)
> supports config-only flips with no recompile.
>
> **🟢 Cloud HSM CMKs PROVISIONED 2026-05-12** by slot 4 agent (operator-authorized ADC): 10 HSM-backed CMKs (5
> asset_groups × `wallets-prod` + `wallets-staging` KeyRings) in `asia-northeast1`, 90-day auto-rotation, IAM Decrypter
> bound to `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` only. **End-to-end smoke test PASSED**:
> encrypt + decrypt round-trip on staging CMK returned matching plaintext. Issue doc closed at
> [`/plans/archive/issues/cloud_kms_cmk_provisioning_for_may23_cutover_2026_05_12.md`](/plans/archive/issues/cloud_kms_cmk_provisioning_for_may23_cutover_2026_05_12.md).
>
> **🟢 POD client scope clarified 2026-05-12** — see
> [`/codex/14-customer-journeys/pod-elysium-client-onboarding.md`](/codex/14-customer-journeys/pod-elysium-client-onboarding.md).
> POD (AIFM Ireland; BVI Fund) is our first DeFi allocator client. POD manages Copper + CEFFU KYB directly. **Fireblocks
> is OUT OF SCOPE per POD stack choice** — POD uses Copper + CEFFU only. `SigningSurface.FIREBLOCKS_MPC` stays in UAC
> enum for future-flexibility but is NOT a May-23 / June-1 target.
>
> Operator-runbook for every cutover + June-1 onboarding step:
> [`/codex/15-runbooks/custody-onboarding-checklist.md`](/codex/15-runbooks/custody-onboarding-checklist.md).
>
> Cloud-KMS adapter (§ B in checklist) — `CloudKmsCustodyProvider` **SHIPPED** at execution-service@`d45d24b4` per Plan
> Phase 3.C.1 (envelope-encrypted PK via Cloud HSM CMK). Bridge function `custody_config_from_wallet_provisioning`
> **SHIPPED** at execution-service@`fdd82def` (B-012 Phase 8.A) — maps `WalletProvisioningConfig.signing_surface` →
> `CustodyConfig` at config-parse time; see §2.5 + §1 factory table. Fireblocks adapter (§ C) —
> `FireblocksCustodyProvider` PENDING per Plan Phase 3.C.2 DEFERRED-AFTER-CUTOVER.

This is the single SSOT for custody integration in the Unified Trading System. It folds in the previous per-provider
docs (`copper-custody-integration.md` + `ceffu-custody-integration.md`, both deleted 2026-05-08 per
[`/plans/archive/codex_refactor_2026_05_08.plan.md`](/plans/archive/codex_refactor_2026_05_08.plan.md) Phase D.4) so the
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

| `config.provider` | Implementation                                                                  | Credentials required                                         | UAC `SigningSurface`                               |
| ----------------- | ------------------------------------------------------------------------------- | ------------------------------------------------------------ | -------------------------------------------------- |
| `"mock"`          | `MockCustodyProvider`                                                           | None                                                         | `MOCK`                                             |
| `"local_key"`     | `LocalKeyCustodyProvider`                                                       | `private_key`, `rpc_url`                                     | `LOCAL_KEY`                                        |
| `"cloud_kms"`     | `CloudKmsCustodyProvider` (SHIPPED execution-service@`d45d24b4`; see §2.5)      | `kms_key_uri`, `private_key_secret_ref` (wrapped ciphertext) | `CLOUD_KMS_ENCRYPTED` **(May-23 cutover default)** |
| `"copper"`        | `CopperCustodyProvider`                                                         | `api_key`, `api_secret`, `organization_id`                   | `COPPER_MPC`                                       |
| `"fireblocks"`    | `FireblocksCustodyProvider` (PENDING — Plan Phase 3.C.2 DEFERRED-AFTER-CUTOVER) | `api_key`, `api_secret`, `vault_account_id`                  | `FIREBLOCKS_MPC`                                   |
| `"ceffu"`         | `CeffuCustodyProvider` (stub-shipped, methods raise)                            | `api_key`, `api_secret`, `organization_id`                   | _(routes via Copper; CEFFU stub-only)_             |
| unknown           | `MockCustodyProvider` (with warning)                                            | None                                                         | —                                                  |

Imports for `local_key`, `copper`, `ceffu`, `cloud_kms`, and `fireblocks` are deferred (inside the routing branch) to
avoid importing `web3` / `httpx` / `google-cloud-kms` / `fireblocks-sdk-python` when not needed.

**Per-wallet flippability** — each wallet row in `gs://wallet-config-{pid}/{chain_env}/wallet_provisioning.json` carries
its own `WalletProvisioningConfig.signing_surface`
(`unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py`), overriding the top-level
`CustodyConfig.provider` default per-call. Operator flips the field in the JSON; deployment-UI Live-Cluster button
reloads via `ApiKeyReloader` pattern. No service restart, no recompile.

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

> **⚪ DEFERRED to June-1+ flip per
> [`/plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md`](/plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 3.C SPLIT (R9 RESOLVED 2026-05-12).** **CEFFU is OUT-OF-SCOPE for the May-23 cutover.** May-23 ships on
> `CLOUD_KMS_ENCRYPTED` (HSM-backed CMK envelope encryption per § 2.5 / Plan Phase 3.C.1); the per-wallet
> `SigningSurface` flip to `COPPER_MPC` / CEFFU happens June-1+ when POD (BVI Fund) delivers institutional KYB-approved
> credentials. The §2.4 subsection content below (CEFFU OES architecture, onboarding flow, expected API integration
> shape) is preserved as **design intent for the June-1+ flip** — it is NOT a May-23 implementation gate. Master plan
> Group F Item 19's "Copper + CEFFU treasury wired" criterion is correspondingly deferred to the June-1+ checkpoint.
> Codified per slot 4 audit refresh
> [`/codex/04-architecture/interface-credential-convention.md`](interface-credential-convention.md) 2026-05-12.
>
> **STATUS: STUB SHIPPED 2026-05-10** (the stub envelope is what reaches factory + supports the eventual June-1+ flip).
> `CeffuCustodyProvider` exists in `execution-service/execution_service/custody/ceffu.py` with a fully-wired
> constructor, factory registration, HMAC-SHA256 signing skeleton, and async-method stubs that raise
> `NotImplementedError("CEFFU API spec pending — ...")`. The pluggable interface envelope is in place so the eventual
> real implementation drops in as a tightly-scoped diff. Real REST endpoints + sandbox URL + sub-account model are
> pending operator confirmation per the open questions below — **all such "pending" / "TBD" markers in §2.4 sub-sections
> are deferred-after-cutover (June-1+), not May-23 blockers.**
>
> **[STATUS UPDATE 2026-06-01]** The June-1 target window has now arrived. The CEFFU API spec
> (`<TBD-OPERATOR-PROVIDES-API-SPEC>` markers throughout this section), REST endpoints, sandbox URL, and sub-account
> model details remain **pending operator input** as of this date. The `<TBD>` markers below are **blocking the
> implementation gate** — no production CEFFU calls can be made until these are populated. Master plan Group F Item 19
> ("Copper + CEFFU treasury wired") remains BLOCKED-OPERATOR-DECISION. Operator action required: provide API spec,
> sandbox credentials, and endpoint catalogue to unblock `CeffuCustodyProvider` implementation from stub → real. Do NOT
> invent endpoints — this note records the revised status accurately.

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

The custody-side balance at CEFFU is the source of truth for available collateral; the venue-side margin at Binance is a
mirror. position-balance-monitor reads custody balance per `(venue=binance, asset)` from the CEFFU provider and
reconciles against Binance's reported margin to detect mirror drift.

#### Onboarding flow (operator runbook)

1. **Binance institutional account.** Operator signs the Binance Institutional Services agreement, opening an OES-
   eligible Binance Futures account. CEFFU is named as the off-exchange custodian.
2. **CEFFU institutional account.** Operator signs the CEFFU custody agreement, receives institutional account ID + API
   credentials (HMAC key + secret, parity expectations with Copper). CEFFU enables the OES bilateral mirror to the
   Binance account opened in step 1.
3. **Sandbox onboarding.** Operator requests CEFFU sandbox credentials separately. Sandbox base URL + sub-account-model
   details are <TBD-OPERATOR-PROVIDES-API-SPEC> — populate once received.
4. **Secret Manager wiring.** Credentials stored under `ceffu-api-key` / `ceffu-api-secret` / `ceffu-org-id`
   (production) and `ceffu-sandbox-api-key` / `ceffu-sandbox-api-secret` (staging/test). `ApiKeyReloader` from UTL
   handles hot-reload per workspace standard.
5. **execution-service config flip.** Set `CUSTODY_PROVIDER=ceffu` for the Binance institutional execution flow;
   non-Binance CeFi + DeFi continue routing through Copper. Wallet mapping in
   `gs://wallet-config-{pid}/wallet_mapping.json` declares `custodian: ceffu` for Binance treasury + trading sub-
   accounts.
6. **Dry-run + paper-trade.** Sandbox flow validates onboarding before any production capital moves. Master plan Group F
   Item 19 paper-trade smoke validates this end-to-end.

#### API integration — PENDING SPEC

The exact REST endpoint catalogue is <TBD-OPERATOR-PROVIDES-API-SPEC>. Expected shape (mirror Copper § 2.3.5 once
confirmed):

| Capability        | Expected method | Path                             | Notes                                           |
| ----------------- | --------------- | -------------------------------- | ----------------------------------------------- |
| Balance query     | GET             | `/<TBD>/accounts/{id}/balances`  | Per token, per chain                            |
| Collateral move   | POST            | `/<TBD>/oes/transfers`           | Custody → Binance margin and reverse            |
| Settlement query  | GET             | `/<TBD>/oes/settlements?from&to` | Daily P&L reconciliation                        |
| Sign transaction  | POST            | `/<TBD>/orders` + `/<TBD>/sign`  | Parity with Copper's two-step MPC signing       |
| List sub-accounts | GET             | `/<TBD>/accounts`                | Sub-account-per-strategy model decision pending |

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

| Phase             | Time (UTC)               | Action                                                                                       |
| ----------------- | ------------------------ | -------------------------------------------------------------------------------------------- |
| Mark-to-market    | Continuous (per Binance) | Binance recalculates margin per tick; mirror credit at CEFFU updates intraday                |
| Settlement window | <TBD> daily              | CEFFU finalises end-of-day P&L; custody balance adjusted; alerting-service confirms          |
| Margin recall     | On threshold breach      | Position-balance-monitor triggers transfer from CEFFU treasury → Binance trading sub-account |
| Reconciliation    | Post-settlement          | batch-vs-live reconciler asserts `custody_balance + position_unrealised == ledger_total`     |

The exact settlement window timing is <TBD-OPERATOR-PROVIDES-API-SPEC> — populate once CEFFU confirms.

#### Risk controls

- **Credit-utilisation cap** — kill-switch rule fires when `position_notional / custody_balance > threshold` per the
  alerting-service `LIVE_RISK_KILL_SWITCH` ruleset (see
  [`kill-switch-circuit-breaker.md`](kill-switch-circuit-breaker.md)).
- **Automatic margin recall threshold** — position-balance-monitor triggers proactive collateral transfer when the
  Binance-side margin ratio drops below `recall_threshold` (default 1.5x maintenance).
- **Withdrawal whitelist** — destination addresses must be pre-approved. Whitelist management is API-driven vs operator-
  driven via the CEFFU dashboard: <TBD-OPERATOR-PROVIDES-API-SPEC> — populate once the CEFFU account model is confirmed.
- **Rate-limit + backoff** — every CEFFU API call routes through UAC `classify_venue_error()` per workspace adapter
  rule; transient 5xx + 429 retried with exponential backoff; 4xx auth/whitelist errors surface as
  `ADAPTER_FETCH_FAILED` events without retry (per the no-fire-and-forget principle).

#### CeffuCustodyProvider implementation reference

`execution-service/execution_service/custody/ceffu.py` (stub shipped 2026-05-10):

| Component            | Status                 | Detail                                                                                      |
| -------------------- | ---------------------- | ------------------------------------------------------------------------------------------- |
| Constructor          | ✅ Wired               | Accepts `api_key` / `api_secret` / `organization_id` / `sandbox` parity with Copper         |
| `_sign_request`      | ✅ Skeleton wired      | HMAC-SHA256 placeholder; final header names + canonicalisation pending API spec             |
| `sign_transaction`   | ❌ NotImplementedError | Raises with operator-action prompt + reference to this codex doc                            |
| `get_balance`        | ❌ NotImplementedError | Same                                                                                        |
| `create_transfer`    | ❌ NotImplementedError | Same                                                                                        |
| `list_wallets`       | ❌ NotImplementedError | Same                                                                                        |
| Factory registration | ✅ Live                | `get_custody_provider(CustodyConfig(provider="ceffu", ...))` returns `CeffuCustodyProvider` |

Tests: `execution-service/tests/unit/custody/test_ceffu_provider.py` — 11 tests covering construction + factory
registration + every async method's NotImplementedError contract.

#### Configuration

| Variable           | Default                            | Description                                             |
| ------------------ | ---------------------------------- | ------------------------------------------------------- |
| `CUSTODY_PROVIDER` | `mock`                             | Set to `ceffu` for Binance institutional flow           |
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

### §2.5 CloudKmsCustodyProvider — SHIPPED (execution-service@`d45d24b4`)

Cloud HSM CMK envelope-encrypted private key signing. The **May-23 cutover default** for DeFi execution. No keys in
memory beyond the signing window; envelope decrypted via Cloud KMS API at signing call time.

Constructor fields (resolved from `CustodyConfig`):

| Field                    | Type  | Description                                                                          |
| ------------------------ | ----- | ------------------------------------------------------------------------------------ |
| `kms_key_uri`            | `str` | Full Cloud KMS key URI (`projects/.../cryptoKeyVersions/...`) for the HSM-backed CMK |
| `private_key_secret_ref` | `str` | Secret Manager ref to the CMK-encrypted private key ciphertext                       |
| `rpc_url`                | `str` | JSON-RPC endpoint (resolved from UAC `CHAIN_RPC_TEMPLATES` at service startup)       |
| `cloud_provider`         | `str` | `"gcp"` (default) or `"aws"` — routes to the correct KMS client implementation       |

Flow (sign_transaction):

```
1. Fetch encrypted ciphertext from Secret Manager (private_key_secret_ref)
2. Decrypt ciphertext via Cloud KMS decrypt API (kms_key_uri) — plaintext PK available for signing window only
3. Sign raw tx bytes via web3.eth.account.sign_transaction
4. Wipe plaintext PK from local scope immediately after signing
5. Return SignedTransaction with raw_signed + tx_hash
```

HSM CMKs provisioned 2026-05-12 (5 asset_groups × `wallets-prod` + `wallets-staging` KeyRings, `asia-northeast1`, 90-day
auto-rotation). IAM Decrypter bound to `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` only.

#### Bridge function `custody_config_from_wallet_provisioning` (execution-service@`fdd82def`, B-012 Phase 8.A)

`execution_service/custody/factory.py::custody_config_from_wallet_provisioning(wallet, rpc_url, cloud_provider)`.

Maps a `WalletProvisioningConfig` (loaded from GCS `wallet_provisioning.json`) to a `CustodyConfig` for
`get_custody_provider()`. Calls `wallet.validate()` first — credential mismatches raise at config-parse time, not at
trade time.

```python
# Caller pattern (execution-service startup / ApiKeyReloader reload):
config = custody_config_from_wallet_provisioning(wallet_provisioning, rpc_url=resolved_rpc)
provider = get_custody_provider(config)
```

Internal dispatch via `_SURFACE_TO_PROVIDER` dict:

| `WalletProvisioningConfig.signing_surface` | `CustodyConfig.provider` |
| ------------------------------------------ | ------------------------ |
| `CLOUD_KMS_ENCRYPTED`                      | `"cloud_kms"`            |
| `COPPER_MPC`                               | `"copper"`               |
| `FIREBLOCKS_MPC`                           | `"fireblocks"`           |
| `LOCAL_KEY`                                | `"local_key"`            |
| `MOCK`                                     | `"mock"`                 |

Test coverage: `tests/unit/custody/test_cloud_kms_provider.py` — 11 tests covering all 5 `SigningSurface` mappings,
`validate()`-at-bridge-time enforcement, and end-to-end KMS mock decrypt (no real keys; `unittest.mock.patch` on KMS
client).

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

## §10A Custody-ping / health-check protocol (codified 2026-05-12 per slot 8 audit PB-18)

> **Contract** for the periodic health check + balance-pull loop that keeps PBMS's balances projection honest against
> Copper + CEFFU. Upstream signal for `BALANCE_DRIFT` (see
> [`/codex/15-runbooks/alerting/balance_drift.md`](/codex/15-runbooks/alerting/balance_drift.md)) and
> `CUSTODY_DISCONNECT_SECONDS` circuit-breaker (see
> [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md)).

Foundation: `CloudKmsCustodyProvider` shipped at execution-service@d45d24b4 per Plan Phase 3.C.1; Copper + CEFFU
production custody flips on June-1 per `WalletProvisioningConfig.signing_surface`.

### §10A.1 Protocol surface

Every `CustodyProvider` implementation MUST satisfy `health_check()` in addition to the `sign_transaction` /
`get_balance` / `create_transfer` / `list_wallets` protocol methods declared in §1.

```python
class CustodyProvider(Protocol):
    async def health_check(self) -> CustodyHealth: ...
```

`CustodyHealth` shape (canonical in UAC `unified_api_contracts.canonical.crosscutting.custody`):

| Field                  | Type          | Description                                                                                                                                                              |
| ---------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `healthy`              | `bool`        | `True` iff backend reachable AND last key-material rotation within freshness window                                                                                      |
| `last_key_rotation_at` | `datetime`    | Wall-clock of last successful CMK / key-material rotation (per [`/codex/15-runbooks/credential-rotation-runbook.md`](/codex/15-runbooks/credential-rotation-runbook.md)) |
| `next_rotation_due_at` | `datetime`    | Wall-clock of next scheduled rotation (`last + cadence` per rotation-runbook per-class table)                                                                            |
| `provider`             | `str`         | Provider name (e.g. `"copper"`, `"ceffu"`, `"cloud_kms"`) — for routing alerts                                                                                           |
| `last_round_trip_ms`   | `int \| None` | Latency observed on the last successful ping; `None` if last ping failed                                                                                                 |
| `error`                | `str \| None` | Error message if `healthy == False`; `None` on success                                                                                                                   |

### §10A.2 Cadence + emitter

| Loop                        | Cadence                                                                 | Emitter                                                                                                                                 | Consumer                                                                                 |
| --------------------------- | ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Health-check ping           | every **60s** (mirrors `make_health_router` heartbeat pattern from UTL) | each `CustodyProvider` instance in execution-service custody-runtime                                                                    | execution-service `/health` endpoint + circuit-breaker `CUSTODY_DISCONNECT_SECONDS` rule |
| Balance-pull reconciliation | every **5 min** (per `balance_drift.md`)                                | `position-balance-monitor-service` per-(wallet, asset) reconciler — pulls `CustodyProvider.get_balance()` + diffs against PBMS expected | PBMS balances projection + `BALANCE_DRIFT` alert                                         |

Health-ping and balance-pull are **separate loops** by design: health-ping is high-frequency / cheap (proves the custody
backend is reachable + creds fresh); balance-pull is lower-frequency / authoritative (proves PBMS state matches what
custody actually holds). The two together give us both **liveness** (60s) and **correctness** (5min) signals.

### §10A.3 Provider-to-(venue, asset) routing

Per §3 coverage matrix and `wallet-config/{chain_env}/wallet_mapping.json`:

- **Copper**: every DeFi chain + non-Binance CeFi (Bybit, OKX, Deribit, Kraken, Aster, Hyperliquid).
- **CEFFU**: Binance institutional custody only (Binance treasury + Binance trading sub-accounts).

PBMS reads `wallet_mapping.json` at startup, builds the (venue, asset) → provider routing table, then runs the 5-min
balance-pull against the correct provider per wallet. The routing table hot-reloads per
[`/codex/06-coding-standards/config-reloader-pattern.md`](/codex/06-coding-standards/config-reloader-pattern.md).

### §10A.4 Failure modes + routing

Closed set; mirrors the existing alerting taxonomy.

> **⛔ ALERT CODES NOT SHIPPED — verified 2026-07-30.** Both `CUSTODY_HEALTH_DEGRADED` and `CREDENTIAL_ROTATION_OVERDUE`
> are **absent from the `AlertCode` enum** (`unified_api_contracts/canonical/crosscutting/alerting/codes.py` — it
> currently has **zero** custody-, rotation- or wallet-prefixed codes). The routing table below is the intended design;
> the emitters do not exist yet. Anyone wiring custody health alerts must add the codes to the UAC closed set first.
> (`CUSTODY_ENDPOINT_HALT` **does** exist — but it is a `RiskRuleId`, not an `AlertCode`; don't conflate the two enums.)

| Failure                                                                                                         | Detection                                                  | Action                                                                                                                                                                                                                          |
| --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Single missed health-ping (transient)                                                                           | `last_round_trip_ms is None` on one tick                   | log debug; no alert (de-dup over 600s window per `balance_drift.md` pattern)                                                                                                                                                    |
| Health-ping failed ≥ `CUSTODY_DISCONNECT_SECONDS` (default **300s** per `circuit-breaker-rule-taxonomy.md:228`) | rolling 5-tick failure window                              | emit `CUSTODY_HEALTH_DEGRADED` AlertCode → circuit-breaker `CUSTODY_DISCONNECT_SECONDS` rule fires `BLOCK_NEW` + CRITICAL severity (PagerDuty + Telegram). Slot 4 cred-rotation alert taxonomy AL-15 cross-references this code |
| Balance-pull diff > `balance_drift_usd` threshold                                                               | per-(wallet, asset) reconciler, every 5 min                | emit `BALANCE_DRIFT` AlertCode → operator runbook per [`balance_drift.md`](/codex/15-runbooks/alerting/balance_drift.md). Does NOT pause trading by default; pages tier-3 on `drift > 10x`                                      |
| Key material stale (`now > next_rotation_due_at`)                                                               | health-check decision (`healthy = False` if past due-date) | emit `CREDENTIAL_ROTATION_OVERDUE` AlertCode → rotation runbook owner per [`/codex/15-runbooks/credential-rotation-runbook.md`](/codex/15-runbooks/credential-rotation-runbook.md) per-class table                              |

`CUSTODY_HEALTH_DEGRADED` is the AlertCode name; the underlying circuit-breaker rule code is
`CUSTODY_DISCONNECT_SECONDS` per `circuit-breaker-rule-taxonomy.md` (the two compose: emitter →
`CUSTODY_HEALTH_DEGRADED` AlertCode → circuit-breaker subscribes → `CUSTODY_DISCONNECT_SECONDS` rule fires `BLOCK_NEW`).

### §10A.5 Relationship to `treasury_monitor.py`

The custody-ping loop is **upstream of** `position-balance-monitor-service/core/treasury_monitor.py`'s `TREASURY_LOW` /
`TREASURY_HIGH` thresholds — treasury*monitor reads the \_post-reconciliation* PBMS balance state, so it inherits the
freshness of the most recent successful balance-pull. If the custody-ping loop is degraded, treasury_monitor alerts may
go stale; the `CUSTODY_HEALTH_DEGRADED` alert is the canonical "PBMS state may be drifting from reality" signal during
that window.

### §10A.6 PBMS is mode-blind (per `batch = live` invariant)

The custody-ping loop runs identically in batch / paper / live — in batch + paper modes against the mock / local-key /
tenderly providers (per §4 mode matrix), in live mode against Copper + CEFFU. PBMS does NOT branch on `OperationalMode`
for the ping cadence or the alert routing (per [`separation-of-concerns.md`](separation-of-concerns.md) § "Positions
SSOT" invariant + slot 8 audit PB-19 deferred QG ratchet).

### §10A.7 Open design questions (PRE_CUTOVER — operator gate)

- **Specific failure thresholds for CEFFU** — CEFFU adapter is still stub per §2.4; the 300s
  `CUSTODY_DISCONNECT_SECONDS` default is appropriate for Copper but operator may want a tighter band for Binance
  institutional flows (CEFFU = sole signing path for Binance-side hedge legs of every DeFi archetype). Routed as a
  follow-up P2 for the operator to decide alongside the CEFFU in-scope-for-May-23 call (slot 8 audit PB-14).
- **Should `auto-pause-live` fire on `CUSTODY_HEALTH_DEGRADED` or just alert?** Today the circuit-breaker taxonomy says
  `BLOCK_NEW` (no new orders; existing positions held). Operator/Ikenna call on whether long-running hedge legs need a
  tighter response (e.g. `KILL_ALL` after N consecutive degraded windows).

### §10A.8 Composes with

- [`/codex/15-runbooks/credential-rotation-runbook.md`](/codex/15-runbooks/credential-rotation-runbook.md) — per-class
  rotation cadence (Cloud HSM CMK 90d / Copper-JWT 60d / CEFFU-JWT 60d) drives `next_rotation_due_at`.
- [`circuit-breaker-rule-taxonomy.md`](circuit-breaker-rule-taxonomy.md) `CUSTODY_DISCONNECT_SECONDS` rule.
- [`/codex/15-runbooks/alerting/balance_drift.md`](/codex/15-runbooks/alerting/balance_drift.md) — the 5-min
  balance-pull failure runbook.
- [`separation-of-concerns.md`](separation-of-concerns.md) § "Positions SSOT" — PBMS is the sole consumer of the
  balance-pull stream; the ping loop is how the balances projection stays honest.

---

## §10 References

- **POD collateral delegation is NOT a `CustodyProvider`** — POD's API instructs a cross-venue move and confirms it
  without us ever signing or seeing a wallet address, mechanically distinct from every provider in §2. See
  [Transfer Architecture § Custodian-mediated collateral delegation](transfer-architecture.md#custodian-mediated-collateral-delegation-custodian_collateral_delegation-2026-08-22)
  for the design + proposed external API, and
  [`/plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md`](/plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md)
  for the build.
- [Tenderly Execution Provider](tenderly-execution-provider.md) -- fork-based execution for batch/paper
- [Wallet Hierarchy and Capital Flow](wallet-hierarchy-and-capital-flow.md) -- treasury/trading wallet architecture
- [Interface Credential Convention](interface-credential-convention.md) -- how services get API keys
- [Flash Loan Receiver](flash-loan-receiver.md) -- DeFi atomic execution
- [`/plans/archive/2026_07/master_to_live_defi_2026_05_23.md`](/plans/archive/2026_07/master_to_live_defi_2026_05_23.md)
  Group F item 19 — live-trading prereq tracking (CEFFU integration)
- [`/plans/epics/defi_master.md`](/plans/epics/defi_master.md) Fork 1 — Binance perp hedging-leg ownership
