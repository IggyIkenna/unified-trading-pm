---
doc_type: codex-ssot
title: Credentials matrix — workspace SSOT
summary:
  Workspace SSOT for every credential across paper/batch/live modes + cloud / venue / custody / data / aux surfaces —
  credential classes with storage + rotation cadence, the live pre-cutover inventory (10 Cloud-HSM CMKs, wallet entries,
  Tenderly/RPC keys), per-mode + per-archetype credential subsets, and GCP-to-AWS Secret Manager parity.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, cefi, custody, credentials, verification]
related:
  [
    /codex/15-runbooks/custody-onboarding-checklist.md,
    /codex/05-infrastructure/secret-manager-naming.md,
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/interface-credential-convention.md,
  ]
created: 2026-05-11
authoritative_for:
  [
    workspace credential matrix — credential classes + storage + rotation cadence,
    per-mode and per-archetype credential subsets,
  ]
referenced_by:
  [
    /codex/05-infrastructure/aws-iam-matrix.md,
    /codex/15-runbooks/custody-onboarding-checklist.md,
    /codex/05-infrastructure/hsm-wallet-signing.md,
    /codex/05-infrastructure/per-archetype-wallet-isolation.md,
    /codex/15-runbooks/credential-rotation-runbook.md,
    /codex/05-infrastructure/secret-manager-naming.md,
    /codex/07-security/gha-wif-migration.md,
    /codex/14-customer-journeys/authentication/firebase-local.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Credentials matrix — workspace SSOT

> **Created 2026-05-12** by slot 4 per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 9.A. Closes out 6 stub codex docs declared in Phase 0.D.

This is the workspace SSOT for **every credential** the system uses across all modes (paper / batch / live) and all
surfaces (cloud / venue / custody / data / aux). Reader: `credential-probe.sh` audit script + per-service health
endpoints + operator runbook.

---

## 2026-05-12 PM — May-23 scope contraction (operator directive)

Operator clarifications consolidated this date contract the May-23 credential surface significantly:

1. **Custody for May-23 = operator's own real money.** Copper, CEFFU, Fireblocks all stay as **June-1+ work**
   (post-cutover). Cloud-KMS path (`CLOUD_KMS_ENCRYPTED` signing_surface) covers May-23 live. Per-wallet flippability
   via `WalletProvisioningConfig.signing_surface` means flip to client-provided MPC creds is config-only post-June-1.
2. **Venue credentials for May-23 = the 4 CeFi perp accounts operator already holds** (Bybit, Deribit, Binance, OKX).
   Per venue: **both testnet AND live API keys** required (testnet for paper-trading mode, live for live-trading mode).
   8 credential bundles total (4 venues × 2 envs). The 6 native-adapter rebuild + per-scope key split + account-limits
   SSOT + rate-limit token bucket sub-work all **DEFERRED post-cutover**; CCXT pass-through acceptable for
   operator-funds ≥7-day live smoke.
3. **DeFi 2 venues (Hyperliquid, Aster)** use the shipped CloudKmsCustodyProvider wallet path; no separate API-key
   credentials needed (signing is EVM-format on operator wallet).
4. **Firebase fully DEFERRED from May-23**. Operator: "we don't wanna pay for Firebase at all by May-23; DeFi client
   doesn't want Firebase so we need a non-Firebase auth path anyway." Firebase code stays as feature-flag toggle (off by
   default). The `firebase-sa-json` row in § 1 below stays as a class definition but is not provisioned for May-23.
5. **Phase 1.B-H AWS↔GCP parity provisioning** stays a deferred 7-10 AI-day workstream — dual-cloud-active steady state
   is the target, not May-23 gate.

Net effect on the credential surface:

- **Live custody**: `CLOUD_KMS_ENCRYPTED` only (per-wallet flippable to MPC June-1+).
- **Venue trade**: 4 CeFi × 2 envs = 8 bundles. Other 6 venues (Upbit/Kraken/Bitfinex/Bitget/Hyperliquid/Aster) either
  DEFERRED (CCXT pass-through Q1-Q2) or wallet-only (DeFi DEXes).
- **Aux**: Anthropic budget cap shipped; Firebase deferred; Telegram per-env + GHA WIF still in scope as hygiene.

---

## § 1 — Credential classes

| Class                | Examples                                                                                                           | Storage                                                 | Rotation cadence                                 |
| -------------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- | ------------------------------------------------ |
| **Cloud infra**      | GCP service accounts, AWS IAM roles, Cloud HSM CMKs, KMS keys                                                      | GCP IAM + AWS IAM + Secret Manager                      | per-CMK 90d (auto); IAM roles indefinite         |
| **Custody**          | Copper API key + secret + org-id, CEFFU equivalents, Fireblocks API key + RSA PEM, wallet PKs (envelope-encrypted) | GCP Secret Manager (`<service>-api-key` paths)          | 60d for HMAC creds; quarterly for Fireblocks RSA |
| **Venue trade**      | Per-venue per-scope `<venue>-{read,trade,withdraw}-{api-key,api-secret,passphrase}` for 10 venues × 3 scopes       | GCP Secret Manager                                      | 30d trade-scope; 60d read-scope                  |
| **Venue prediction** | polymarket / kalshi                                                                                                | GCP Secret Manager                                      | 60d                                              |
| **Data sources**     | api-football / footystats / soccer-football-info / helius / coingecko / tenderly-access-key / barchart / yahoo     | GCP Secret Manager                                      | 90d (data only — lower risk)                     |
| **Aux services**     | telegram-bot-token-{dev,staging,prod} / firebase-sa-json / anthropic-api-key                                       | GCP Secret Manager                                      | 90d                                              |
| **GHA WIF**          | GCP/AWS → GitHub OIDC trust pool                                                                                   | GCP Workload Identity Federation + AWS STS trust policy | indefinite (no long-lived PAT)                   |

---

## § 1.A — LIVE pre-cutover inventory (provisioned 2026-05-12 by slot 4 agent ADC)

Codified after agent-authorized ADC self-provisioning + end-to-end signing pipeline smoke verification. **Real, live
entries in GCP Secret Manager + Cloud HSM today** (`central-element-323112`, `asia-northeast1`).

### Cloud HSM CMKs (10 keys; 90-day auto-rotation; HSM-backed FIPS 140-2 L3)

| KeyRing           | CMK                                                      | Purpose                      | IAM bindings                                |
| ----------------- | -------------------------------------------------------- | ---------------------------- | ------------------------------------------- |
| `wallets-prod`    | `trading-defi-master-v1`                                 | DeFi wallets cutover-prod    | `unified-trading-sa`: Decrypter             |
| `wallets-prod`    | `trading-cefi-master-v1`                                 | CeFi wallets                 | `unified-trading-sa`: Decrypter             |
| `wallets-prod`    | `trading-tradfi-master-v1`                               | TradFi wallets               | `unified-trading-sa`: Decrypter             |
| `wallets-prod`    | `trading-sports-master-v1`                               | Sports archetype wallets     | `unified-trading-sa`: Decrypter             |
| `wallets-prod`    | `trading-prediction-master-v1`                           | Prediction archetype wallets | `unified-trading-sa`: Decrypter             |
| `wallets-staging` | `trading-{defi,cefi,tradfi,sports,prediction}-master-v1` | Test wallets                 | `unified-trading-sa`: Decrypter + Encrypter |

Full URI pattern:
`projects/central-element-323112/locations/asia-northeast1/keyRings/wallets-{env}/cryptoKeys/trading-{asset_group}-master-v1`.

### Pre-cutover test wallet entries (Trust Wallet canonical)

| Secret Manager entry                     | Type                          | Value                                                                     | Status                                        |
| ---------------------------------------- | ----------------------------- | ------------------------------------------------------------------------- | --------------------------------------------- |
| `defi-wallet-trust`                      | EVM address (canonical)       | `0x992ebFe04DB05f964C45BCE3D73Ca4c81715a79f`                              | ✅ Live                                       |
| `defi-wallet-private-key`                | EVM 0x-hex PK (raw, 66 chars) | (Trust Wallet PK — never logged)                                          | ✅ Live                                       |
| `defi-wallet-private-key-wrapped`        | Envelope-encrypted EVM PK     | (233-byte base64 ciphertext via `wallets-staging/trading-defi-master-v1`) | ✅ Live; end-to-end smoke verified 2026-05-12 |
| `defi-wallet-metamask`                   | EVM address (secondary)       | `0x0056801778F9A5dE5C8a5225B676859b797fA88B`                              | ✅ Live (address only — no PK provisioned)    |
| `defi-wallet-solana`                     | Solana base58 address         | (pending Trust Wallet Solana export)                                      | 🟡 PENDING operator-action                    |
| `defi-wallet-solana-private-key`         | Solana base58 PK              | (pending operator export)                                                 | 🟡 PENDING                                    |
| `defi-wallet-solana-private-key-wrapped` | Envelope-encrypted Solana PK  | (pending)                                                                 | 🟡 PENDING                                    |

**End-to-end signing pipeline smoke** (verified 2026-05-12 by slot 4 agent): `CloudKmsCustodyProvider` fetched
`defi-wallet-private-key-wrapped` from Secret Manager → Cloud HSM KMS Decrypt → web3.py `from_key` derived address →
matched `defi-wallet-trust` value. The May-23 cutover `CLOUD_KMS_ENCRYPTED` signing path is **operationally verified**.

Operator runbook:
[`/codex/15-runbooks/pre-cutover-test-wallets-runbook.md`](/codex/15-runbooks/pre-cutover-test-wallets-runbook.md) § 0
(canonical lookup) + § 3 (Solana via Trust Wallet operator-export flow).

### Tenderly + chain RPC credentials (✅ SORTED 2026-05-12)

| Secret Manager entry    | Use                                                                    |
| ----------------------- | ---------------------------------------------------------------------- |
| `tenderly-api-key`      | Tenderly API auth (fork creation + simulation)                         |
| `tenderly-fork-rpc-url` | RPC endpoint for batch/paper mode                                      |
| `alchemy-api-key`       | EVM chain RPCs (ETH / Arb / Base / Polygon mainnet + Sepolia variants) |
| `helius-key`            | Solana mainnet RPC (production-grade Solana RPC P1 follow-up)          |

### POD-managed credentials (delivered 2026-06-01)

Per [`pod-elysium-client-onboarding.md`](/codex/14-customer-journeys/pod-elysium-client-onboarding.md):

| Secret Manager entry                                     | Provisioned by                                              | Status                  |
| -------------------------------------------------------- | ----------------------------------------------------------- | ----------------------- |
| `copper-api-key` / `copper-api-secret` / `copper-org-id` | POD → operator (June-1)                                     | 🟡 PENDING POD delivery |
| `copper-sandbox-api-key` / `copper-sandbox-api-secret`   | POD pre-cutover sandbox                                     | 🟡 PENDING              |
| `ceffu-api-key` / `ceffu-api-secret` / `ceffu-org-id`    | POD → operator (June-1)                                     | 🟡 PENDING POD delivery |
| `fireblocks-*`                                           | **OUT OF SCOPE** per POD stack choice (Copper + CEFFU only) | ❌ Not provisioning     |

---

## § 2 — Per-mode credential subsets

SSOT YAML:
[`unified-api-contracts/config/credentials_per_mode.yaml`](../../unified-api-contracts/config/credentials_per_mode.yaml).

| Mode    | Custody                                         | Venue               | Data                      | Aux           |
| ------- | ----------------------------------------------- | ------------------- | ------------------------- | ------------- |
| `paper` | sandbox + mock                                  | (none — fork fills) | live read-only            | dev telegram  |
| `batch` | mock                                            | read-scope only     | live (historical sources) | dev telegram  |
| `live`  | CLOUD_KMS (May-23) → COPPER/FIREBLOCKS (June-1) | trade-scope (full)  | live                      | prod telegram |

---

## § 3 — Per-archetype credential subsets

SSOT YAML:
[`unified-api-contracts/config/credentials_per_archetype.yaml`](../../unified-api-contracts/config/credentials_per_archetype.yaml).

Cutover archetypes:

- `carry_staked_basis` — 5 wallet wrapped PKs + 6 perp hedge venues + cloud_kms_cmk_defi + helius + coingecko +
  telegram.
- `ARBITRAGE_PRICE_DISPERSION` (config variants: funding_rate_dispersion + cross_venue_price_dispersion) — same wallet
  shape + relevant venue keys.

---

## § 4 — Per-cloud parity

GCP Secret Manager (prod project `central-element-323112`) is canonical; AWS Secrets Manager (`ap-northeast-1` account
`427895769566`) mirrors per Plan Phase 1.E. Cross-cloud abstraction via `UnifiedCloudConfig` — service code never
branches on cloud.

```python
config = UnifiedCloudConfig(provider="gcp")  # or "aws"
value = config.get_secret("copper-api-key")  # round-trips on both
```

---

## § 5 — Naming convention

SSOT: [`secret-manager-naming.md`](secret-manager-naming.md).

Pattern: `<class>-<surface>-<role>-<version>` (per § 2 of naming SSOT).

---

## § 6 — Continuous verification

Every credential class declares cadence + execution-owner per `Runbook Execution-Owner SSOT` HARD RULE:

```yaml
execution:
  owner: deployment-service maintainer + ikennaigboaka (operator)
  cadence: daily cron VM `credential-probe-vm`
  verifier: credential-probe.sh --mode live returns 100% pass
  last_executed: NEVER
```

Pre-cutover gate (2026-05-22): full probe MUST return 100% pass before live-trading kill-switch disarms.

---

## § 7 — References

- [`secret-manager-naming.md`](secret-manager-naming.md) — naming SSOT.
- [`/codex/15-runbooks/custody-onboarding-checklist.md`](/codex/15-runbooks/custody-onboarding-checklist.md) — operator
  runbook.
- [`fireblocks-integration-spec.md`](fireblocks-integration-spec.md) — June-1 paste-ready spec.
- [`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md) — multi-wallet model.
- [`hsm-wallet-signing.md`](hsm-wallet-signing.md) — HSM tier discipline.
- [`aws-iam-matrix.md`](aws-iam-matrix.md) — per-service AWS IAM SSOT (PENDING Phase 1.B).
