---
scope: [engineer, admin]
---

# Secret Manager naming convention — SSOT

> **Created 2026-05-12** by slot 4 per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 9.C. Codifies the workspace naming pattern for every secret in GCP
> Secret Manager + AWS Secrets Manager.

---

## § 1 — General pattern

```
<class>-<surface>-<env>-<role>-<version>
```

| Token | Closed set | Examples |
|---|---|---|
| `class` | `custody` / `venue` / `data` / `aux` / `cloud_kms_cmk` / `wallet` | `copper-` / `bybit-` / `helius-` / `telegram-` / `cloud_kms_cmk_defi` |
| `surface` | provider name (`copper` / `bybit` / `helius` / `fireblocks` / `ceffu` / `binance` / `okx` / `deribit` / `hyperliquid` / `aster` / `upbit` / `kraken` / `bitfinex` / `bitget` / `polymarket` / `kalshi` / `api-football` / `footystats` / `soccer-football-info` / `coingecko` / `tenderly` / `barchart` / `yahoo` / `telegram` / `firebase` / `anthropic`) | n/a |
| `env` | `testnet` / `live` for venue trade creds (paper-mode reads testnet, live-mode reads live; one Secret Manager entry per env per venue). Omitted for surfaces that don't have a testnet/live split (most non-venue creds). | `bybit-testnet-trade-api-key` / `bybit-live-trade-api-key` / `deribit-testnet-trade-api-secret` / `binance-testnet-trade-api-key` / `okx-testnet-trade-api-key` |
| `role` | `api-key` / `api-secret` / `passphrase` / `org-id` / `pem` (Fireblocks) / `read` / `trade` / `withdraw` (per-scope) | `api-key` / `read-api-key` / `trade-api-secret` / `read-passphrase` |
| `version` | optional `v1` / `v2` / `sandbox` / `prod` suffix when ambiguous | `-v1` / `-sandbox` / (omitted = current) |

**2026-05-12 PM operator clarification — testnet vs live for CeFi 4**: paper-trading mode (`--mode paper` per
`credentials_per_mode.yaml`) reads `<venue>-testnet-<role>` keys from Secret Manager; live-trading mode reads
`<venue>-live-<role>`. Operator generates 8 credential bundles for May-23 (Bybit/Deribit/Binance/OKX × testnet +
live). Venue testnet endpoints: `testnet.bybit.com` / `test.deribit.com` / `testnet.binancefuture.com` / OKX
demo-trading toggle in production app. Routing is config-only via `credentials_per_mode.yaml` keys on `paper`
vs `live`.

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

### 2.2 Per-venue per-scope (R8 separation)

```
<venue>-{read,trade,withdraw}-{api-key,api-secret,passphrase}
```

Examples:
```
bybit-read-api-key       bybit-trade-api-key       bybit-withdraw-api-key
bybit-read-api-secret    bybit-trade-api-secret    bybit-withdraw-api-secret

okx-trade-api-key
okx-trade-api-secret
okx-trade-passphrase     # OKX requires 3-field auth

deribit-read-api-key
deribit-trade-api-key
deribit-trade-api-secret
```

Total: 10 venues × 3 scopes × 2-3 fields per scope = ~60-90 secrets.

### 2.3 Prediction venues

```
polymarket-api-key
kalshi-api-key
manifold-api-key      # only if archetype scope adds Manifold
```

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

Note: wrapped ciphertext lives in Secret Manager; CMK URI carried separately
on `WalletProvisioningConfig.kms_key_uri`. The wrapper-pattern is
`gcloud kms encrypt --key=<cmk_uri> --plaintext-file=<pk>` → base64
ciphertext → Secret Manager.

### 2.5.A Pre-cutover test wallets (Trust Wallet canonical — provisioned 2026-05-12)

Pre-cutover test wallets use a separate naming pattern (less structured than
the per-archetype-per-chain prod pattern above) because they cover all
chains under a single operator-managed wallet:

```
defi-wallet-<provider>           # public EVM/Solana address
defi-wallet-<provider>-private-key            # raw PK (LOCAL_KEY surface)
defi-wallet-<provider>-private-key-wrapped    # envelope-encrypted PK (CLOUD_KMS_ENCRYPTED surface)
```

| Pattern | Live entry | Status |
|---|---|---|
| `defi-wallet-trust` | EVM `0x992ebFe04DB...` (canonical per operator 2026-05-12) | ✅ Live |
| `defi-wallet-private-key` | EVM 0x-hex Trust Wallet PK | ✅ Live |
| `defi-wallet-private-key-wrapped` | Wrapped via `wallets-staging/trading-defi-master-v1` CMK | ✅ Live; end-to-end smoke verified 2026-05-12 |
| `defi-wallet-metamask` | EVM address `0x0056801778F9...` | ✅ Live (address only — no PK) |
| `defi-wallet-solana` | Solana base58 address | 🟡 PENDING operator Trust Wallet Solana export |
| `defi-wallet-solana-private-key` | Solana base58 PK | 🟡 PENDING |
| `defi-wallet-solana-private-key-wrapped` | Wrapped via same CMK | 🟡 PENDING |

**Why the different pattern**: prod cutover wallets are per-archetype-per-chain
isolated (N×M model per
[`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md)) so
the structured `<archetype>-<chain>-<role>-vN-wrapped` naming carries the
archetype + chain attribution in the secret name itself. Pre-cutover test
wallets cover ALL chains under one operator-managed wallet (Trust Wallet) so
the secret name only carries the provider attribution (`-trust` / `-metamask`
/ `-solana`).

Reader contract: services consuming `defi-wallet-*` secrets MUST also read
the corresponding `WalletProvisioningConfig` row in
[`test_wallet_provisioning_pre_cutover.json`](../../unified-api-contracts/unified_api_contracts/config/test_wallet_provisioning_pre_cutover.json)
for chain + signing_surface + allowed_protocols + spending_caps context.

Pattern is NOT EXPECTED to grow much — operator-managed test wallets stay
1-2 entries per provider. Production cutover wallets follow § 2.5 prod
pattern strictly.

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

Paper-trade smokes MUST use sandbox-suffixed creds; production VMs MUST use
bare-name creds. Operator enforces via per-VM SA IAM bindings (sandbox SA
has access to `-sandbox` secrets only).

---

## § 4 — AWS Secrets Manager mirror

Per Plan Phase 1.E, AWS Secrets Manager (`ap-northeast-1`) mirrors GCP Secret
Manager 1:1 by name. `UnifiedCloudConfig(provider="aws").get_secret("copper-api-key")`
round-trips against AWS-side; same name semantics.

AWS-specific naming additions:
- ARNs auto-generated; UAC code references secrets by canonical name only.
- KMS keys also dual-cloud (GCP CMK ↔ AWS CMK pair per asset_group).

---

## § 5 — Validation

Per-PR check via QG `STEP 5.69` ratchet (bucket-name SSOT) + per-PR check on
Secret Manager paths via `secret-name-pattern-check.py` (NEW per Plan
Phase 0.D, integrated into deployment-service QG).

Closed-set enforcement: any new secret name MUST match one of the patterns
above OR be added to this SSOT with rationale before merging.

---

## § 6 — References

- [`credentials-matrix.md`](credentials-matrix.md) — workspace credential
  SSOT (which secrets each mode + archetype consumes).
- [`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) —
  operator-action provisioning runbook.
- [`fireblocks-integration-spec.md`](fireblocks-integration-spec.md) —
  Fireblocks-specific naming (RSA PEM + vault account).
- [`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md) —
  per-wallet wrapped PK naming pattern derivation.
