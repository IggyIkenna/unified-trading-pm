---
doc_type: codex-ssot
title: Secret Manager naming convention — SSOT
summary: >-
  Secret Manager naming-convention SSOT — merged 2026-07-23 with the former
  codex/07-security/secret-naming-convention.md (superseded, redirects here). States the two-axis model verified against
  real GCP inventory — private/client-owned execution credentials use exec-{client}-{venue}-{field} (client, venue, api
  all present — confirmed live for OKX's 8 clients + Binance's 2 clients); public market-data and pooled/house
  credentials share one key per venue, no client segment (read/trade-split for Binance/Deribit, single unscoped key for
  Bybit/Aster, wallet-style for Hyperliquid). Also covers the <class>-<surface>-<env>-<role>-<version> provisioning
  pattern for custody/CMK/wrapped-wallet/data/aux secrets, the AWS mirror, and the bybit_api_key/bybit_api_secret
  underscore-violation fix (cloned to bybit-api-key/ bybit-api-secret 2026-07-23).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-api-contracts, execution-service, unified-trading-library, strategy-service]
scope: [engineer, admin]
tags: [secret-manager, security, canonicalisation, credentials, defi, cefi, execution]
related:
  [
    ../15-runbooks/credential-rotation-runbook.md,
    credentials-matrix.md,
    ../04-architecture/custody-providers.md,
    ../07-security/secret-naming-convention.md,
    ../07-security/client-credentials.md,
    ../07-security/service-to-service-auth.md,
  ]
created: 2026-05-11
authoritative_for: [Secret Manager secret naming convention]
referenced_by:
  [
    codex/05-infrastructure/aws-iam-matrix.md,
    codex/05-infrastructure/credentials-matrix.md,
    codex/05-infrastructure/hsm-wallet-signing.md,
    codex/05-infrastructure/per-archetype-wallet-isolation.md,
    codex/15-runbooks/credential-rotation-runbook.md,
    codex/14-customer-journeys/authentication/firebase-local.md,
    codex/15-runbooks/per-source-credential-rotation-runbook.md,
  ]
owner:
last_reviewed: 2026-07-23
code_refs:
  [
    unified-trading-library/unified_trading_library/cloud_interface/credentials_registry.py,
    execution-service/execution_service/data/tranche_router.py,
    execution-service/execution_service/cli/handlers/live_execution_handler.py,
    execution-service/execution_service/service_config.py,
    execution-service/execution_service/sports_execution/prediction_markets/kalshi.py,
    execution-service/execution_service/sports_execution/prediction_markets/polymarket.py,
    market-tick-data-service/market_tick_data_service/market_interface/clients/thegraph_base_client.py,
  ]
---

# Secret Manager naming convention — SSOT

> **Created 2026-05-12** by slot 4 per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 9.C. Codifies the workspace naming pattern for every secret in GCP Secret Manager + AWS Secrets Manager.
>
> **Merged 2026-07-23** (doc-reconciliation, operator-approved) with the former
> [`codex/07-security/secret-naming-convention.md`](../07-security/secret-naming-convention.md) — both docs carried
> `authoritative_for: [Secret Manager secret naming convention]` verbatim, a retrieval-layer collision. That doc is now
> `status: superseded` and redirects here.
>
> **The initial merge (§ 1.3/§ 1.4 as first written) found four _documented_ conventions and called it an unresolved
> fragmentation.** A follow-up pass the same day queried the live GCP Secret Manager inventory directly (project
> `central-element-323112`, 194 secrets) instead of trusting any doc or code comment, and found the real picture is
> simpler than that: **one client-owned pattern (already correct in GCP, just wrongly described everywhere) and one
> pooled/house pattern per venue** — see § 1 below for the resolved model. The operator's own rule, verified against the
> evidence: _"private feed orders/trades need to split per client; market data (public) can always use the same key
> shared."_ That is exactly what the GCP inventory already does — the mess was entirely in the CODE and CONFIG that
> describe it (wrong field name, wrong currency-suffixed example names, one true underscore violation), not in the
> secrets themselves.

---

## § 1 — The two-axis model (verified against live GCP inventory, 2026-07-23)

Two independent axes decide a credential's shape. Get these right and the name follows mechanically — no separate
"general pattern" table to memorise.

**Axis 1 — whose money is it?**

- **Private / client-owned** (an external client's own funds — orders, trades, account-specific balances): MUST carry
  the client. Pattern: `exec-{client}-{venue}-{field}`, `field` ∈ `api-key` / `api-secret` / `passphrase` (passphrase
  only where the venue requires 3-field auth, e.g. OKX). This is **already correct in live GCP** — confirmed for OKX (8
  clients: `pr`, `nn`, `std`, `gp`, `sl`, `sl2`, `anu`, `ik` × 3 fields = 24 secrets) and Binance (2 clients: `et`,
  `odum-prop` × 2 fields). No client-scoped secrets exist yet for Deribit, Bybit, or Hyperliquid — those venues are not
  yet onboarded for per-client live trading.
- **Public market data, or pooled/house execution** (the firm's own capital, or read-only observation — no external
  client to isolate from): shared, ONE key per venue, no client segment. See § 1.1 for the real per-venue shape, which
  varies by venue capability (this is Axis 2).

**Axis 2 — does the venue split read vs. trade capability?** (applies only within the pooled/house category)

- **Splits**: Binance, Deribit — `{venue}-read-api-key`, `{venue}-trade-api-key`, `{venue}-write-api-key` (+ matching
  `-secret` siblings). Real, live, intentional — not leftover experimentation.
- **Doesn't split**: Bybit, Aster — one unscoped key does both (`bybit-api-key` / `bybit-api-secret` as of 2026-07-23;
  see § 1.2's rename below). Aster: `aster-api-key` / `aster-secret-key`.
- **Wallet-style**: Hyperliquid — `hyperliquid-trade-key`, but note this is the ONE exception to "one key per venue =
  flat string": the secret VALUE is a JSON blob (`private_key`, `wallet_address`, `main_wallet` — agent wallet
  authorized by a main wallet for EIP-712 signing; see `codex/07-security/secrets-management.md` § On-Chain/DeFi for the
  field meanings), verified live 2026-07-23. A first pass at wiring this into
  `execution-service/execution_service/cli/handlers/live_execution_handler.py` assumed a flat private-key string
  (matching every other venue's shape) and had to be corrected after fetching the real secret and finding it parses as
  JSON — don't repeat that assumption.
- **Single system-wide blob**: Kalshi (`kalshi-api-credentials`), IBKR (`ibkr-account-credentials` — a physical
  single-Gateway-process constraint, not a "read-only" designation).
- **Ad hoc multi-field, not yet normalised**: Betfair (`betfair-api-key` + `betfair-app-key` + `betfair-username` — 3
  separate secrets, all already correctly hyphenated — the ad hoc-ness is the 3-way SPLIT, not a naming violation, so
  there's nothing to rename here), Polymarket (`polymarket-api-key` / `-passphrase` / `-private-key` / `-secret`, same
  situation). Consolidating either into one blob (like Kalshi/IBKR) is a real code change across 3+ consumer
  files/repos, not a naming fix; out of scope for this pass, flagged for a future cleanup, not touched. GCP also has a
  4th, UPPERCASE `BETFAIR_APP_KEY` secret alongside the 3 real ones — checked 2026-07-23, this is NOT the same
  underscore violation `bybit_api_key` was: zero code calls `get_secret_client().get_secret("BETFAIR_APP_KEY")`; all 4
  references are `os.environ.get("BETFAIR_APP_KEY")` in e2e-testing scripts + test conftest, and
  `unified-api-contracts/tests/vcr/test_betfair_auth_vcr.py` documents it as intentionally provisioned for direct
  secret-to-env injection at deploy time (a different, legitimate mechanism from the CredentialsRegistry-resolved path)
  — left untouched.
- **Data-vendor key pool (not client-scoped, orthogonal to Axis 1/2)**: The Graph is a rate-limited 9-key rotation pool
  — `thegraph-api-key` + `thegraph-api-key-2`..`-9` — **intentional, live, correctly named** (matches
  `market-tick-data-service/market_tick_data_service/market_interface/clients/thegraph_base_client.py`'s
  `_THEGRAPH_NUM_API_KEYS = 9` + 429-aware round-robin, not naming drift). Fixed 2026-07-23 (see § 1.2).

**Never add a client segment to a pooled/house/read-only secret** — there is no client to isolate from, and doing so
would misrepresent what the secret is.

---

## § 1.1 — Client-owned execution: `exec-{client}-{venue}-{field}`

The canonical, already-live pattern for private per-client trading credentials. `client` is lowercase, hyphenated (the
YAML registry key downcased, e.g. `ODUM_PROP` → `odum-prop`). `field` is one of `api-key`, `api-secret`, `passphrase`
(OKX only — 3-field auth).

Resolved via `CredentialsRegistry.exec_secret_for_client(client, venue, field) -> str` in
`unified_trading_library.cloud_interface.credentials_registry` (fixed 2026-07-23 — previously took a nonsensical
`account_type` parameter and produced `exec-{client}-{venue}-{account_type}`, a shape matching zero real secrets).
Consumed by `execution-service/execution_service/data/tranche_router.py`'s `TrancheRouter` (Tranche B / "managed"
clients) — this class previously had a hardcoded `_load_client_registry() -> {}` stub (fixed 2026-07-23) and had zero
external callers as of this writing, so wiring it up did not change any live behavior, only made previously-dead code
correct.

The per-client registry (`unified-trading-pm/credentials-registry.yaml`, mirrored in
`execution-service/configs/credentials-registry.yaml` and `client-reporting-api/configs/credentials-registry.yaml`)
declares each client's `venue` + a `secret_names:` mapping (fixed 2026-07-23 — previously a single wrong
`secret_name: exec-{client}-{venue}-{currency}` field that matched no real secret in any of the 3 copies).

## § 1.2 — Known naming violations

| Name in use        | Canonical target                           | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| ------------------ | ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bybit_api_key`    | `bybit-api-key`                            | **FIXED 2026-07-23** — cloned in GCP (value verified byte-identical via hash), all code/config references updated across 5 repos, old underscored secret deleted from GCP after verifying zero remaining references workspace-wide.                                                                                                                                                                                                                                                                                                       |
| `bybit_api_secret` | `bybit-api-secret`                         | **FIXED 2026-07-23** — same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `ibkr-tws-key`     | `ibkr-account-credentials`                 | **Fixed** (pre-existing) — real code uses `ibkr-account-credentials` (`ibkr_credentials.py:4,113`).                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `betfair_app_key`  | `betfair-app-key` (NOT `-api-credentials`) | **Partially fixed, target corrected 2026-07-23** — real code already uses hyphenated `betfair-app-key`; the OLD target `betfair-api-credentials` was itself wrong (doesn't exist in GCP; Betfair is 3 separate ad hoc secrets, see § 1 above) — no further action needed on this one.                                                                                                                                                                                                                                                     |
| `graph-api-key`    | `thegraph-api-key`                         | **FIXED 2026-07-23** — was mischaracterized as "unresolved fragmentation"; ground truth is simpler: `thegraph-api-key`(-2..9) is a correct, intentional 9-key rotation pool (see § 1), `graph-api-key` was a genuinely orphaned GCP secret (zero live code references, deleted after verification), and `the-graph-api-key` was a real BUG — 4 MTDS handlers fetched that nonexistent name every run (api_key=missing, 0 rows silently); migrated to `load_thegraph_key_pool()`, matching the fix `position_data_handler.py` already had. |

---

## § 2 — Per-class patterns

### 2.1 Custody (Copper / CEFFU / Fireblocks)

```
copper-api-key
copper-api-secret
copper-org-id
copper-sandbox-api-key
copper-sandbox-api-secret

ceffu-api-key
ceffu-api-secret
ceffu-org-id
ceffu-sandbox-api-key
ceffu-sandbox-api-secret

fireblocks-api-key          # Fireblocks API user UUID
fireblocks-api-secret       # Fireblocks RSA PEM (base64 envelope)
fireblocks-vault-account-id # vault account UUID
```

### 2.2 Per-venue read/trade/write split (pooled/house credentials — corrected 2026-07-23)

**Real for Binance and Deribit** (verified live in GCP): `{venue}-read-api-key`, `{venue}-trade-api-key`,
`{venue}-write-api-key` (+ matching `-secret` siblings) — pooled/house-level keys, no client segment (per § 1's Axis 1:
this is the firm's own capital or read-only market data, not a specific client's funds). This is § 1.1's sibling
category, not a separate/aspirational design — see § 1 for the two-axis model.

```
binance-read-api-key        binance-trade-api-key        binance-write-api-key
binance-read-api-key-secret binance-trade-api-key-secret

deribit-read-api-key        deribit-trade-api-key        deribit-write-api-key
deribit-read-api-key-secret deribit-trade-api-key-secret
```

**NOT real for OKX, Bybit, or client-scoped secrets in general**: the earlier draft of this doc described a
`<venue>-{read,trade,withdraw}-{api-key,api-secret,passphrase}` design intended as a general **per-client** scope-
separation model (the "R8" plan, `plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md`) — a real,
still-plausible security idea (a compromised read-key shouldn't be able to withdraw funds), whose enforcement half
shipped (`execution-service`'s `ScopedCLOBAdapter`/`AdapterScope`) but whose Secret-Manager-provisioning half was
deferred 2026-05-12 and never resumed. No client-scoped `exec-{client}-{venue}-{read,trade,withdraw}-*` secret exists in
GCP. Do not confuse this dead per-client design with the real, live, non-client Binance/Deribit split above.

### 2.3 Prediction venues

Corrected 2026-07-23 against live GCP inventory:

```
kalshi-api-credentials      # single system-wide blob (matches § 1's CredentialsRegistry.VENUE_SECRET_MAP)

polymarket-api-key          # 4 separate ad hoc secrets, not yet normalised — flagged for future cleanup
polymarket-passphrase
polymarket-private-key
polymarket-secret
```

Both `KalshiAdapterConfig`/`PolymarketAdapterConfig` in
`execution-service/execution_service/sports_execution/prediction_markets/{kalshi,polymarket}.py` are documented-but-
not-yet-wired NautilusTrader adapter config STUBS (no code anywhere calls `get_secret_client().get_secret(...)` on their
`secret_name*` fields yet) — both had wrong defaults, fixed 2026-07-23 after actually querying GCP rather than trusting
the stub's own comments: `KalshiAdapterConfig` split into two fields (`kalshi-api-key` + `kalshi-api-secret`, neither
exists) when the real secret is the ONE blob above — collapsed to a single `secret_name = "kalshi-api-credentials"`
field. `PolymarketAdapterConfig.secret_name_api_secret` / `secret_name_api_passphrase` defaulted to
`polymarket-api-secret` / `polymarket-api-passphrase` (neither exists, the "-api-" infix doesn't apply to these two
fields even though it does for `secret_name_api_key`) — fixed to `polymarket-secret` / `polymarket-passphrase`.
`secret_name_funder` (`polymarket-funder-address`) is NOT a naming bug — it is a real field for a secret that is simply
not yet provisioned in GCP.

### 2.4 Cloud KMS CMKs

```
cloud_kms_cmk_defi          # GCP CMK URI alias
cloud_kms_cmk_cefi
cloud_kms_cmk_tradfi
cloud_kms_cmk_sports
cloud_kms_cmk_prediction
```

Full URI: `projects/{pid}/locations/asia-northeast1/keyRings/wallets-{env}/cryptoKeys/trading-{asset_group}-master-v1`

### 2.5 Per-wallet wrapped private keys (production cutover wallets)

```
<archetype>-<chain>-<role>-v<n>-wrapped
```

Examples:

```
csb-eth-hot-lido-v1-wrapped       # carry_staked_basis Ethereum hot wallet (Lido leg)
csb-sol-hot-jito-v1-wrapped       # carry_staked_basis Solana (Jito leg)
apd-arb-hot-uniswap-v1-wrapped    # ARBITRAGE_PRICE_DISPERSION Arbitrum Uniswap
gas-reserve-eth-v1-wrapped        # per-chain gas reserve
```

Note: wrapped ciphertext lives in Secret Manager; CMK URI carried separately on `WalletProvisioningConfig.kms_key_uri`.
The wrapper-pattern is `gcloud kms encrypt --key=<cmk_uri> --plaintext-file=<pk>` → base64 ciphertext → Secret Manager.

### 2.5.A Pre-cutover test wallets (Trust Wallet canonical — provisioned 2026-05-12)

Pre-cutover test wallets use a separate naming pattern (less structured than the per-archetype-per-chain prod pattern
above) because they cover all chains under a single operator-managed wallet:

```
defi-wallet-<provider>           # public EVM/Solana address
defi-wallet-<provider>-private-key            # raw PK (LOCAL_KEY surface)
defi-wallet-<provider>-private-key-wrapped    # envelope-encrypted PK (CLOUD_KMS_ENCRYPTED surface)
```

| Pattern                                  | Live entry                                                 | Status                                         |
| ---------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------- |
| `defi-wallet-trust`                      | EVM `0x992ebFe04DB...` (canonical per operator 2026-05-12) | ✅ Live                                        |
| `defi-wallet-private-key`                | EVM 0x-hex Trust Wallet PK                                 | ✅ Live                                        |
| `defi-wallet-private-key-wrapped`        | Wrapped via `wallets-staging/trading-defi-master-v1` CMK   | ✅ Live; end-to-end smoke verified 2026-05-12  |
| `defi-wallet-metamask`                   | EVM address `0x0056801778F9...`                            | ✅ Live (address only — no PK)                 |
| `defi-wallet-solana`                     | Solana base58 address                                      | 🟡 PENDING operator Trust Wallet Solana export |
| `defi-wallet-solana-private-key`         | Solana base58 PK                                           | 🟡 PENDING                                     |
| `defi-wallet-solana-private-key-wrapped` | Wrapped via same CMK                                       | 🟡 PENDING                                     |

**Why the different pattern**: prod cutover wallets are per-archetype-per-chain isolated (N×M model per
[`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md)) so the structured
`<archetype>-<chain>-<role>-vN-wrapped` naming carries the archetype + chain attribution in the secret name itself.
Pre-cutover test wallets cover ALL chains under one operator-managed wallet (Trust Wallet) so the secret name only
carries the provider attribution (`-trust` / `-metamask` / `-solana`).

Reader contract: services consuming `defi-wallet-*` secrets MUST also read the corresponding `WalletProvisioningConfig`
row in
[`test_wallet_provisioning_pre_cutover.json`](../../unified-api-contracts/unified_api_contracts/config/test_wallet_provisioning_pre_cutover.json)
for chain + signing_surface + allowed_protocols + spending_caps context.

Pattern is NOT EXPECTED to grow much — operator-managed test wallets stay 1-2 entries per provider. Production cutover
wallets follow § 2.5 prod pattern strictly.

### 2.6 Data sources

```
api-football-key
footystats-key
soccer-football-info-key
helius-key                # Solana RPC
coingecko-key             # DeFi prices
tenderly-access-key       # Tenderly fork
barchart-key              # VIX 15m preload
yahoo-key                 # VIX 15m rolling 60d
```

### 2.7 Aux services

```
telegram-bot-token-dev
telegram-bot-token-staging
telegram-bot-token-prod

firebase-sa-json          # Service account JSON for Cloud Run → Firebase auth

anthropic-api-key
```

---

## § 3 — Sandbox vs production split

Suffix-based:

- Production: bare name (e.g. `copper-api-key`).
- Sandbox / staging: `-sandbox` suffix (e.g. `copper-sandbox-api-key`).
- Per-env: `-dev` / `-staging` / `-prod` for aux services (e.g. telegram bot tokens).

Paper-trade smokes MUST use sandbox-suffixed creds; production VMs MUST use bare-name creds. Operator enforces via
per-VM SA IAM bindings (sandbox SA has access to `-sandbox` secrets only).

---

## § 4 — AWS Secrets Manager mirror

Per Plan Phase 1.E, AWS Secrets Manager (`ap-northeast-1`) mirrors GCP Secret Manager 1:1 by name.
`UnifiedCloudConfig(provider="aws").get_secret("copper-api-key")` round-trips against AWS-side; same name semantics.

AWS-specific naming additions:

- ARNs auto-generated; UAC code references secrets by canonical name only.
- KMS keys also dual-cloud (GCP CMK ↔ AWS CMK pair per asset_group).

---

## § 5 — Validation

Per-PR check via QG `STEP 5.69` ratchet (bucket-name SSOT) + per-PR check on Secret Manager paths via
`secret-name-pattern-check.py` (NEW per Plan Phase 0.D, integrated into deployment-service QG).

Closed-set enforcement: any new secret name MUST match one of the patterns above OR be added to this SSOT with rationale
before merging.

---

## § 6 — References

- [`credentials-matrix.md`](credentials-matrix.md) — workspace credential SSOT (which secrets each mode + archetype
  consumes).
- [`../15-runbooks/custody-onboarding-checklist.md`](../15-runbooks/custody-onboarding-checklist.md) — operator-action
  provisioning runbook.
- [`fireblocks-integration-spec.md`](fireblocks-integration-spec.md) — Fireblocks-specific naming (RSA PEM + vault
  account).
- [`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md) — per-wallet wrapped PK naming pattern
  derivation.
- [`../07-security/secret-naming-convention.md`](../07-security/secret-naming-convention.md) — superseded by this doc
  (2026-07-23); retained for history.
- `unified-trading-library/unified_trading_library/cloud_interface/credentials_registry.py` — the real
  `CredentialsRegistry` implementation backing § 1.1.
