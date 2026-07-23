---
doc_type: codex-ssot
title: Fireblocks integration spec — June-1 paste-ready implementation
summary:
  "Paste-ready engineering spec for the FireblocksCustodyProvider adapter (execution-service custody/fireblocks.py):
  mirrors the Copper adapter, swaps to RS256-JWT auth + Fireblocks REST endpoints, adds HD derivation + per-tx TAP
  co-signer policy. Per-wallet config-only flip CLOUD_KMS_ENCRYPTED → FIREBLOCKS_MPC. Implementation gated on client
  June-1 credential delivery; no code shipped yet."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, deployment-service, deployment-ui, execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, execution, custody, wallet, hsm, infrastructure]
related:
  [
    /codex/04-architecture/custody-providers.md,
    /codex/15-runbooks/custody-onboarding-checklist.md,
    /codex/05-infrastructure/hsm-wallet-signing.md,
    /codex/05-infrastructure/per-archetype-wallet-isolation.md,
  ]
created: 2026-05-11
authoritative_for: [fireblocks custody provider spec]
referenced_by:
  [
    /codex/05-infrastructure/credentials-matrix.md,
    /codex/05-infrastructure/hsm-wallet-signing.md,
    /codex/15-runbooks/credential-rotation-runbook.md,
    /codex/05-infrastructure/secret-manager-naming.md,
    /codex/14-customer-journeys/pod-elysium-client-onboarding.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Fireblocks integration spec — June-1 paste-ready implementation

> **Created 2026-05-12** by slot 4 (`ikenna-keys-wallets-tab`) per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 3.C.2 (Fireblocks signer integration, DEFERRED-AFTER-CUTOVER 2026-06-01). Status: **paste-ready design** —
> implementation gated on client June-1 credential delivery. Successor plan when work starts:
> `plans/active/fireblocks_copper_client_integration_2026_06_01.md` (operator-spawned when creds land).

This document is the **paste-ready engineering spec** for the `FireblocksCustodyProvider` adapter. Drop-in equivalent of
the Copper adapter: mirror its factory shape, swap signing protocol + REST endpoints, add HD derivation + per-tx
co-signer policy. No new service-side primitives needed.

> **[DELTA 2026-05-22]** **Current state:** `CLOUD_KMS_ENCRYPTED` is SHIPPED and verified for May-23 live. Copper +
> CEFFU target June-1. Fireblocks is further out (client credential delivery gates implementation). This doc is a
> paste-ready engineering spec; no `FireblocksCustodyProvider` code is shipped yet. **Planned delta:**
> `FireblocksCustodyProvider` adapter tracked under `plans/epics/defi_master.md` § custody. **Target architecture:**
> Per-wallet config-only flip from `CLOUD_KMS_ENCRYPTED` → `FIREBLOCKS_MPC` post-June-1 credential delivery.

---

## § 1 — Architecture (mirrors Copper § 2.3)

`execution-service/execution_service/custody/fireblocks.py` (NEW) implements the existing `CustodyProvider` protocol
from `custody/base.py`. Zero strategy code changes; only adapter + factory registration.

```python
from typing import Protocol
from decimal import Decimal


class CustodyProvider(Protocol):
    async def sign_transaction(self, wallet_id: str, chain: str, raw_tx: bytes) -> SignedTransaction: ...
    async def get_balance(self, wallet_id: str, token: str, chain: str) -> Decimal: ...
    async def create_transfer(self, from_wallet_id: str, to_address: str, token: str, amount: Decimal, chain: str) -> str: ...
    async def list_wallets(self, chain: str | None = None) -> list[dict[str, str]]: ...
```

### 1.1 Factory registration

`execution-service/execution_service/custody/factory.py` — add `"fireblocks"` key alongside existing `"copper"` /
`"cloud_kms"` / `"local_key"` / `"mock"` / `"ceffu"`:

```python
def get_custody_provider(config: CustodyConfig) -> CustodyProvider:
    if config.provider == "fireblocks":
        from execution_service.custody.fireblocks import FireblocksCustodyProvider
        return FireblocksCustodyProvider(
            api_key=config.api_key,
            api_secret=config.api_secret,
            vault_account_id=config.organization_id,  # repurposed field per CustodyConfig
            sandbox=config.sandbox,
        )
    ...
```

### 1.2 Per-wallet flip (config-only, no recompile)

Operator edits `gs://wallet-config-{pid}/{chain_env}/wallet_provisioning.json` per-wallet row to flip from
`CLOUD_KMS_ENCRYPTED` → `FIREBLOCKS_MPC`:

```diff
 {
   "wallet_id": "csb-eth-hot-lido-v1",
   "chain": "ETHEREUM",
   "kind": "HOT_TRADING",
-  "signing_surface": "CLOUD_KMS_ENCRYPTED",
-  "kms_key_uri": "projects/.../keyRings/wallets-prod/cryptoKeys/...",
-  "private_key_secret_ref": "csb-eth-hot-lido-v1-wrapped",
+  "signing_surface": "FIREBLOCKS_MPC",
+  "custodian_wallet_id": "<Fireblocks vaultAccountId>",
   ...
 }
```

Deployment-UI Live-Cluster button (shipped 2026-05-11 by slot 4) reloads config via `ApiKeyReloader` — no service
restart.

---

## § 2 — Fireblocks SDK + authentication

### 2.1 Dependencies

```toml
# execution-service/pyproject.toml [project.dependencies]
"fireblocks-sdk>=2.6.0",  # pin to latest stable at June-1 implementation time
"PyJWT>=2.8.0",            # Fireblocks SDK uses RS256 JWT for auth
"cryptography>=42.0.0",    # for RSA private key handling
```

### 2.2 Authentication shape

Fireblocks uses **RS256 JWT** (not HMAC-SHA256 like Copper). The "API secret" is a `.pem` RSA private key file; the API
key is the JWT subject claim. Every request signs a JWT with:

```python
import jwt
from datetime import datetime, timedelta
from uuid import uuid4
import hashlib

def _sign_request(self, path: str, body: dict | None) -> str:
    now = int(datetime.utcnow().timestamp())
    body_str = json.dumps(body, sort_keys=True) if body else ""
    body_hash = hashlib.sha256(body_str.encode()).hexdigest()
    claims = {
        "uri": path,
        "nonce": str(uuid4()),
        "iat": now,
        "exp": now + 55,  # short-lived; Fireblocks enforces ≤60s window
        "sub": self.api_key,
        "bodyHash": body_hash,
    }
    return jwt.encode(claims, self._private_key_pem, algorithm="RS256")
```

Headers emitted:

- `X-API-Key: <api_key>`
- `Authorization: Bearer <jwt>`

### 2.3 Secret Manager paths

Per `/codex/15-runbooks/custody-onboarding-checklist.md` § C:

- `fireblocks-api-key` — Fireblocks API user identifier (UUID).
- `fireblocks-api-secret` — RSA private key PEM (multi-line, base64-encoded for Secret Manager storage; PEM-decoded at
  startup via `cryptography.hazmat`).

---

## § 3 — Core endpoints + method mapping

| `CustodyProvider` method | Fireblocks REST path                             | Body shape                                                                                                          |
| ------------------------ | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| `list_wallets`           | `GET /v1/vault/accounts_paged`                   | Pagination via `before` cursor                                                                                      |
| `get_balance`            | `GET /v1/vault/accounts/{vaultAccountId}/assets` | Returns `available` + `pending` + `frozen`                                                                          |
| `create_transfer`        | `POST /v1/transactions`                          | `operation=TRANSFER` + `source` + `destination` + `assetId` + `amount`                                              |
| `sign_transaction`       | `POST /v1/transactions`                          | `operation=RAW` + `extraParameters={"rawMessageData": {"messages": [{"content": <hex>}]}}` for arbitrary tx signing |

Polling on transaction status:

```python
async def _poll_until_signed(self, tx_id: str, timeout_s: float = 30.0) -> str:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        resp = await self._get(f"/v1/transactions/{tx_id}")
        status = resp["status"]
        if status == "COMPLETED":
            return resp["signedMessages"][0]["signature"]["fullSig"]  # hex
        if status in {"FAILED", "BLOCKED", "REJECTED", "CANCELLED"}:
            raise CustodySigningError(
                provider="fireblocks", reason=resp.get("subStatus", status),
            )
        await asyncio.sleep(1.0)
    raise CustodySigningError(provider="fireblocks", reason="timeout_30s")
```

### 3.1 Event taxonomy (mirror Copper)

- `FIREBLOCKS_TX_SIGNED` — successful signing (includes `tx_id`, `signature`, `vaultAccountId`).
- `FIREBLOCKS_TX_FAILED` — signing failed (includes `tx_id`, `sub_status`, `reason`).
- `FIREBLOCKS_TRANSFER_CREATED` — transfer order created (includes `tx_id`, `from`, `to`, `assetId`, `amount`).

Subscribers: position-balance-monitor + alerting-service + deployment-ui.

---

## § 4 — HD-wallet derivation (N × M wallet expansion)

Plan Phase 4.A specifies N archetypes × M chains = N×M wallets. Fireblocks supports HD derivation under a master vault
account. Two implementation paths:

### 4.1 Vault-account-per-wallet (recommended for May-23 cutover scope)

Each wallet in `wallet_provisioning.json` maps to a distinct Fireblocks vault account ID. Operator pre-creates ≥10 vault
accounts (2 archetypes × 5 chains). Each vault account holds the assets for that wallet only.

Pros: each `WalletProvisioningConfig.custodian_wallet_id` is a stable UUID; no derivation path required. Cons: 10+ vault
accounts to manage in Fireblocks dashboard.

### 4.2 BIP-44 HD derivation under a single master vault account

Single Fireblocks vault account; derived addresses per `derivation_path` in `WalletProvisioningConfig` (already in UAC
schema as `derivation_path: str = ""`).

```python
# Fireblocks SDK call
vault_assets = client.get_vault_account_assets(
    vault_account_id=self.vault_account_id,
    asset_id="ETH",
    derivation_path="m/44'/60'/0'/0/<index>",
)
```

Pros: single vault account; per-archetype-per-chain derived addresses under one master. Cons: requires Fireblocks
Treasury / Connect-style account tier — confirm with client June-1.

### 4.3 Decision gate

Operator confirms with client June-1: vault-account-per-wallet (4.1) vs HD derivation under master (4.2). Default to 4.1
if unclear; switch to 4.2 post-cutover if 10+ vault accounts become operationally tedious.

---

## § 5 — Per-wallet policy controls + co-signing

Fireblocks Transaction Authorization Policy (TAP) implements the security envelope. Per-wallet policy rules:

| Rule                   | Source                                              | Enforcement                                                              |
| ---------------------- | --------------------------------------------------- | ------------------------------------------------------------------------ |
| `max_amount_per_tx`    | UAC `SpendingCaps.per_tx_usd`                       | TAP rule: amount > threshold → require co-signer                         |
| `allowed_destinations` | UAC `WalletProvisioningConfig.allowed_destinations` | TAP rule: destination ∈ AddressBook → auto-approve; else block           |
| `time_of_day_window`   | (NEW) per-archetype trading hours                   | TAP rule per UTC hour-of-day                                             |
| `kill_switch_id`       | UAC `WalletProvisioningConfig.kill_switch_id`       | TAP rule: vault frozen if kill_switch armed via `freezeVaultAccount` API |

### 5.1 Co-signer policy

For `amount > SpendingCaps.per_tx_usd`, require Fireblocks co-signer approval (typically operator + client signatures).
For `SpendingCaps.per_hour_usd` breach, auto-block via TAP. For `SpendingCaps.per_day_usd` breach, auto-block via TAP +
emit `WALLET_CAP_EXCEEDED_DAY` alert.

### 5.2 AddressBook integration

`allowed_destinations` from `WalletProvisioningConfig` MUST be pre-populated in the Fireblocks AddressBook
(operator-side via dashboard or `POST /v1/internal_wallets/{walletContainerId}/addresses`). TAP rule:
`destination ∈ AddressBook` → auto-approve; else block.

For TREASURY wallets (client-deposit-source whitelist), AddressBook entries are tagged `category=CLIENT_DEPOSIT`. For
HOT_TRADING + GAS_RESERVE (empty allowed_destinations per schema invariant), AddressBook is empty — only internal
vault-to-vault transfers permitted.

---

## § 6 — Latency budget + load testing

| Operation                            | Budget        | Notes                           |
| ------------------------------------ | ------------- | ------------------------------- |
| JWT signing (local)                  | <5ms          | RS256 via PyJWT                 |
| `POST /v1/transactions` round-trip   | 200-500ms     | network + Fireblocks API        |
| Co-signer approval (if required)     | 1-30s         | human-in-loop for large amounts |
| Total signing latency (no co-sign)   | 100-500ms p95 | mirrors Copper                  |
| Total signing latency (with co-sign) | 1-30s p95     | for amounts ≥ per_tx_usd        |

Pre-cutover Sepolia + mainnet smoke (small balance) MUST validate p95 within budget under 10 concurrent signing requests
(load test via `locust` or similar).

---

## § 7 — Error taxonomy + UAC `classify_venue_error` integration

Add to UAC `venue_errors_defi.py` (or appropriate location):

```python
class FireblocksErrorCode(StrEnum):
    """Closed-set Fireblocks-specific error classifications."""

    # Routing prefix per CLAUDE.md DefiErrorCode convention
    FIREBLOCKS_TX_FAILED_RETRY_NETWORK_TIMEOUT = "FIREBLOCKS_RETRY_NETWORK_TIMEOUT"
    FIREBLOCKS_TX_FAILED_RETRY_RATE_LIMIT = "FIREBLOCKS_RETRY_RATE_LIMIT"
    FIREBLOCKS_TX_FAIL_AUTHORIZATION_DENIED = "FIREBLOCKS_FAIL_AUTHORIZATION_DENIED"  # TAP rule rejection
    FIREBLOCKS_TX_FAIL_INSUFFICIENT_BALANCE = "FIREBLOCKS_FAIL_INSUFFICIENT_BALANCE"
    FIREBLOCKS_TX_FAIL_VAULT_FROZEN = "FIREBLOCKS_FAIL_VAULT_FROZEN"  # kill-switch armed
    FIREBLOCKS_TX_FAIL_ADDRESS_NOT_WHITELISTED = "FIREBLOCKS_FAIL_ADDRESS_NOT_WHITELISTED"
    FIREBLOCKS_TX_FAIL_COSIGNER_TIMEOUT = "FIREBLOCKS_FAIL_COSIGNER_TIMEOUT"
    FIREBLOCKS_TX_SKIP_DUPLICATE_NONCE = "FIREBLOCKS_SKIP_DUPLICATE_NONCE"
```

Route on `FAIL`/`RETRY`/`SKIP` prefix per existing DefiErrorCode pattern. 8 codes minimum — extend as Fireblocks API
surface expands.

---

## § 8 — Testing strategy

### 8.1 Unit tests (`tests/unit/custody/test_fireblocks_provider.py`)

- Construction: `FireblocksCustodyProvider(...)` with valid + invalid creds.
- Factory registration: `get_custody_provider(CustodyConfig(provider="fireblocks", ...))` returns instance.
- `_sign_request` JWT: claims structure matches Fireblocks spec, signed with RS256.
- Method contract: every async method raises `NotImplementedError` if creds not provided (pre-June-1 grace shape; mirror
  CEFFU stub).

### 8.2 Integration tests (`tests/integration/test_fireblocks_custody_provider.py`)

- Tagged `@pytest.mark.allow_network`.
- Against Fireblocks **sandbox environment** (separate API endpoint + creds).
- Real JWT signing but on testnet vault accounts.
- Skipped if sandbox credentials unavailable (CI default).

### 8.3 VCR cassettes (`tests/cassettes/fireblocks/`)

- `sign_transaction.yaml`
- `get_balance.yaml`
- `create_transfer.yaml`
- Validated via `unified-api-contracts/tests/test_cassette_schema_parity.py`.

### 8.4 Smoke test (Sepolia + mainnet small balance)

Singleton-locked launcher `deployment-service/scripts/vm/launch-fireblocks-smoke-vm.sh` (NEW):

- `--testnet` flag: signs on Sepolia + Solana devnet.
- `--mainnet` flag: signs single dust-amount tx on Ethereum mainnet to confirm production wiring.
- Event-stream verification per CLAUDE.md "No fire-and-forget VM launches": STARTED + per-wallet `FIREBLOCKS_TX_SIGNED`
  event + STOPPED.

---

## § 9 — Operator-action items (per `Runbook Execution-Owner SSOT` HARD RULE)

```yaml
execution:
  owner: ikennaigboaka (operator) + slot 4 successor (post-June-1)
  cadence: one-shot June-1 → ongoing flip per-wallet
  verifier: fireblocks_smoke.py --vault-list returns expected vault count
  last_executed: NEVER
```

- [ ] **C.2.1** Implement `FireblocksCustodyProvider` per § 1 + § 2.
- [ ] **C.2.2** Register in `custody/factory.py` per § 1.1.
- [ ] **C.2.3** Per-wallet flip per § 1.2 (operator runbook).
- [ ] **C.2.4** HD derivation choice (4.1 vs 4.2) per § 4.3 — operator + client.
- [ ] **C.2.5** TAP rules per § 5 — operator configures via Fireblocks dashboard.
- [ ] **C.2.6** AddressBook populated per § 5.2 — operator.
- [ ] **C.2.7** Sandbox smoke + Sepolia + mainnet small balance per § 8.4.
- [ ] **C.2.8** UAC `FireblocksErrorCode` enum per § 7 — bundled with adapter PR.
- [ ] **C.2.9** Update `/codex/04-architecture/custody-providers.md` § 2.5 (NEW Fireblocks subsection mirroring Copper §
      2.3).

---

## § 10 — References

- [`/codex/04-architecture/custody-providers.md`](/codex/04-architecture/custody-providers.md) §2.3 (Copper reference
  architecture this spec mirrors).
- [`/codex/15-runbooks/custody-onboarding-checklist.md`](/codex/15-runbooks/custody-onboarding-checklist.md) § C
  (operator-action runbook).
- [`unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py`](../../unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py)
  (`SigningSurface.FIREBLOCKS_MPC` enum value + `WalletProvisioningConfig` schema fields consumed).
- [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
  Phase 3.C.2 (parent plan).
- Fireblocks API docs: <https://developers.fireblocks.com/reference/> (operator-side reference; not for agent fetch —
  agent uses Context7 MCP if needed).
- Fireblocks SDK Python: <https://github.com/fireblocks/fireblocks-sdk-py> (operator-side reference).
