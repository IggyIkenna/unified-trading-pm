---
doc_type: codex-ssot
title: HSM-grade wallet signing — tier discipline
summary:
  "5-tier SigningSurface security ladder (UAC StrEnum), loosest→strictest: MOCK (test) · LOCAL_KEY (dev/testnet only) ·
  CLOUD_KMS_ENCRYPTED (May-23 cutover default, HSM-backed CMK envelope) · COPPER_MPC (June-1, 2-of-3 shards) ·
  FIREBLOCKS_MPC (June-1, MPC + TAP rules). Per-tier threats/mitigations, per-wallet tier selection, latency budget, and
  pre-cutover acceptance criteria."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: [defi, custody, wallet, hsm, execution, infrastructure]
related:
  [
    /codex/04-architecture/custody-providers.md,
    /codex/15-runbooks/custody-onboarding-checklist.md,
    /codex/05-infrastructure/fireblocks-integration-spec.md,
    /codex/05-infrastructure/per-archetype-wallet-isolation.md,
    /codex/05-infrastructure/secret-manager-naming.md,
  ]
created: 2026-05-11
authoritative_for: [wallet signing surface tier ladder]
referenced_by:
  [
    /codex/05-infrastructure/aws-iam-matrix.md,
    /codex/05-infrastructure/credentials-matrix.md,
    /codex/05-infrastructure/fireblocks-integration-spec.md,
    /codex/05-infrastructure/per-archetype-wallet-isolation.md,
    /codex/15-runbooks/pre-cutover-test-wallets-runbook.md,
    /codex/15-runbooks/credential-rotation-runbook.md,
    /codex/05-infrastructure/runtime-tiers-and-deployment.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# HSM-grade wallet signing — tier discipline

> **Created 2026-05-12** by slot 4 per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 9.F. Codifies the per-tier security envelope after R9 sub-(a) RESOLVED 2026-05-12.

---

## § 1 — Tier ladder

5 tiers, ordered loosest → strictest. UAC SSOT:
[`SigningSurface`](../../unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py) StrEnum.

| Tier | `SigningSurface`      | Cryptographic primitive           | Key custody                                | Insurance      | Latency                                       | Acceptable for                                          |
| ---- | --------------------- | --------------------------------- | ------------------------------------------ | -------------- | --------------------------------------------- | ------------------------------------------------------- |
| 1    | `MOCK`                | SHA256 deterministic              | None                                       | —              | <1ms                                          | Test-only                                               |
| 2    | `LOCAL_KEY`           | web3.py raw signing               | Raw PK in Secret Manager                   | None           | <10ms                                         | Dev + testnet ONLY                                      |
| 3    | `CLOUD_KMS_ENCRYPTED` | RSA envelope + chain signing      | Envelope-encrypted PK; CMK in HSM          | KMS provider's | 100-200ms                                     | **May-23 cutover default** (≤7-day live smoke)          |
| 4    | `COPPER_MPC`          | MPC threshold signing             | Key shards across Copper + client + backup | Copper's       | 1-2s                                          | Post-June-1; institutional DeFi + non-Binance CeFi      |
| 5    | `FIREBLOCKS_MPC`      | MPC threshold signing + TAP rules | Key shards within Fireblocks vault         | Fireblocks'    | 100-500ms (no co-sign) / 1-30s (with co-sign) | Post-June-1; carry strategies + HSM-grade hedge wallets |

---

## § 2 — Per-tier security properties

### 2.1 `MOCK`

Test-only. Returns SHA256 of input bytes. No security guarantees. Used in unit tests + paper-trade fork mode + CI
emulator runs.

### 2.2 `LOCAL_KEY`

Raw private key fetched from Secret Manager at startup, held in process memory. Web3.py signs locally; no remote
signing.

**Threats**: process memory dump exposes PK; Secret Manager IAM mis-configuration exposes PK to unauthorized human
principal. **Mitigations**: trading-VM SA-only IAM binding on Secret Manager; no human principal has
`secretmanager.secretAccessor`; process runs in non-root container with seccomp.

**Acceptable scope**: dev workstation against Tenderly fork; testnet wallets. **Forbidden scope**: any mainnet wallet
ever.

### 2.3 `CLOUD_KMS_ENCRYPTED` — May-23 cutover default

PK is envelope-encrypted at rest in Secret Manager using a Cloud HSM-backed CMK. The CMK itself never leaves the HSM
module (FIPS 140-2 Level 3). At signing time, the trading-VM SA calls `kms.Decrypt(ciphertext, cmk_uri)` → plaintext PK
held in memory only for the signing operation → web3.py / solana-py signs → plaintext PK discarded (Python garbage
collection; no explicit zero-fill but memory pool reuse is a high-probability mitigation).

**Threats**:

1. KMS Decrypter IAM granted to compromised principal → PK decrypted by attacker.
2. Plaintext PK in process memory dump.
3. CMK key rotation gap (decrypt with old CMK version still possible).

**Mitigations**:

1. IAM bound to trading-VM SA ONLY. No human principal. Audited via Cloud KMS audit logs → BigQuery sink → alerting on
   any non-VM-SA decrypt event.
2. Plaintext PK in memory for ≤100ms per sign call; no swap to disk (`mlock`-eligible if needed); no logging of
   plaintext.
3. Per-CMK 90-day automatic rotation. Re-wrap legacy ciphertexts at rotation time + delete prior CMK version.

**Acceptable scope**: 7-day live smoke 2026-05-23 → 2026-05-30. **Forbidden scope post-June-1**: any wallet that
received Copper / Fireblocks creds.

### 2.4 `COPPER_MPC`

PK shards split across Copper + client + backup; never reassembled. Signing requires coordinated MPC computation across
≥2-of-3 shards. Sub-2s end-to-end.

**Threats**: Copper API compromise (signed-tx interception); transfer-policy bypass via dashboard manipulation;
sandbox/production credential confusion. **Mitigations**: HMAC-signed REST + cluster-policy enforcement (per Copper
dashboard); paper-trade smoke against sandbox endpoint; separate prod/sandbox Secret Manager paths.

**Acceptable scope**: production DeFi + non-Binance CeFi from June-1 onwards. Operator pre-confirms with client which
wallets flip.

### 2.5 `FIREBLOCKS_MPC`

Similar MPC primitive to Copper but with Fireblocks-specific TAP (Transaction Authorization Policy) layer: per-tx
amount + destination + time-of-day rules enforced before the MPC signing even initiates.

**Threats + mitigations** mirror Copper, plus:

1. JWT-RS256 key compromise → Fireblocks-side rotation + immediate revoke via admin dashboard.
2. TAP rule misconfiguration → operator dashboard review + paste-ready `fireblocks_tap_smoke.py` (Phase 3.C.2 sub-item).

**Acceptable scope**: production carry strategies + HSM-grade hedge wallets from June-1 onwards. Recommended over Copper
for archetypes with co-signer-required amounts.

---

## § 3 — Tier selection per wallet

Default `signing_surface` for May-23 cutover wallets: `CLOUD_KMS_ENCRYPTED`.

Per-wallet override post-June-1 (per [`fireblocks-integration-spec.md`](fireblocks-integration-spec.md) § 1.2):

```python
# Pre-June-1 (May-23 cutover)
wallet = WalletProvisioningConfig(
    wallet_id="csb-eth-hot-lido-v1",
    signing_surface=SigningSurface.CLOUD_KMS_ENCRYPTED,
    kms_key_uri="projects/.../keyRings/wallets-prod/cryptoKeys/trading-defi-master-v1",
    private_key_secret_ref="csb-eth-hot-lido-v1-wrapped",
    ...
)

# Post-June-1 flip (same wallet, swap surface)
wallet = WalletProvisioningConfig(
    wallet_id="csb-eth-hot-lido-v1",
    signing_surface=SigningSurface.FIREBLOCKS_MPC,
    custodian_wallet_id="<Fireblocks vaultAccountId>",
    # kms_key_uri + private_key_secret_ref cleared; envelope ciphertext can be
    # archived to GCS cold storage or destroyed post-flip verification
    ...
)
```

---

## § 4 — Operator runbook

Provisioning + flipping wallets between tiers:
[`/codex/15-runbooks/custody-onboarding-checklist.md`](/codex/15-runbooks/custody-onboarding-checklist.md).

§ B: Cloud-KMS provisioning (May-23). § C: Fireblocks flip (June-1). § A: Copper verification (pre-cutover gate).

---

## § 5 — Latency budget (production)

Aggregate end-to-end signing-to-broadcast must fit strategy execution latency budget:

| Stage                        | CLOUD_KMS                          | COPPER                       | FIREBLOCKS (no co-sign)      |
| ---------------------------- | ---------------------------------- | ---------------------------- | ---------------------------- |
| Secret Manager fetch         | 50ms                               | 50ms (HMAC key)              | 50ms (RSA PEM)               |
| Decrypt / sign               | 150ms                              | 1500ms                       | 300ms                        |
| RPC broadcast                | 200-500ms                          | 200-500ms                    | 200-500ms                    |
| Confirmation (1 block)       | 12s ETH / 2s ARB / 400ms SOL       | same                         | same                         |
| **Total (no co-sign)**       | ~12.5s ETH / ~2.5s ARB / ~0.7s SOL | ~14s ETH / ~4s ARB / ~2s SOL | ~13s ETH / ~3s ARB / ~1s SOL |
| **Total (co-sign required)** | n/a                                | n/a                          | 1-30s extra (human-in-loop)  |

Per-strategy budget: `carry_staked_basis` rebalances tolerate up to 30s end-to-end. `ARBITRAGE_PRICE_DISPERSION`
rebalances need ≤5s ARB (L2) for arbitrage windows — CLOUD_KMS on L2 well within budget; Fireblocks without-co-sign also
fits.

---

## § 6 — Acceptance criteria

Pre-cutover (2026-05-22) MUST satisfy:

- ✅ All 10+ HOT_TRADING wallets on `CLOUD_KMS_ENCRYPTED` per cutover template.
- ✅ Cloud HSM CMK provisioned per asset_group; IAM Decrypter bound to VM SA only.
- ✅ Sepolia + Solana devnet sign-and-broadcast smokes green per checklist § B.4.
- ✅ Latency p95 within budget per § 5 above.
- ✅ KMS audit log streaming + alerting on non-VM-SA decrypt.

Post-June-1 acceptance for COPPER/FIREBLOCKS flip MUST satisfy:

- ✅ Client creds delivered to operator + provisioned in Secret Manager.
- ✅ Per-wallet flip via deployment-UI Live-Cluster button (no service restart).
- ✅ Sepolia smoke green per wallet post-flip.
- ✅ Latency p95 within budget per § 5 above.
- ✅ AddressBook / transfer-policy / TAP rules reviewed by operator in custodian dashboard.

---

## § 7 — References

- [`custody-providers.md`](/codex/04-architecture/custody-providers.md) — full factory architecture.
- [`/codex/15-runbooks/custody-onboarding-checklist.md`](/codex/15-runbooks/custody-onboarding-checklist.md) —
  operator-action runbook.
- [`fireblocks-integration-spec.md`](fireblocks-integration-spec.md) — June-1 paste-ready spec.
- [`credentials-matrix.md`](credentials-matrix.md) — workspace credential SSOT.
- [`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md) — multi-wallet model.
- [`secret-manager-naming.md`](secret-manager-naming.md) — naming SSOT.
- [`unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py`](../../unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py)
  — `SigningSurface` enum SSOT.
