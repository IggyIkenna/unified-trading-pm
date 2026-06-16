---
scope: [admin, engineer]
last_reviewed: 2026-05-17
execution:
  owner: "credential-ops (operator) + per-class secondary owner declared in body"
  cadence: "per-class (see body table — typically 90d/30d/event-driven)"
  verifier:
    "gh secret list --repo IggyIkenna/<repo> + Secret Manager versions API (verify latest enabled version date within
    cadence)"
  last_executed: "see per-class rotation log appended in body"
---

# Credential rotation runbook — per-class cadence + execution-owner

> **Created 2026-05-12** by slot 4 per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 9.D + Phase 5.A.2. Codifies rotation cadence per credential class + the execution-owner per Runbook
> Execution-Owner SSOT HARD RULE.

---

## § 1 — Rotation discipline overview

Every credential in the workspace lives in GCP Secret Manager (`central-element-323112`) + AWS Secrets Manager mirror
(`ap-northeast-1`). Rotation is the periodic re-issuance of a credential — even when not compromised — to limit
blast-radius of unknown-unknown compromise.

Per-class cadence is tuned to risk:

| Class                                                                                 | Cadence                      | Rationale                                                                |
| ------------------------------------------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------ |
| Cloud HSM CMK                                                                         | 90d (automatic)              | Cloud HSM auto-rotation; legacy ciphertexts re-wrapped on rotation event |
| Wallet wrapped PK                                                                     | NEVER (cold-laptop ceremony) | Re-key requires fresh cold-laptop key-gen + on-chain treasury migration  |
| Custody (Copper / Fireblocks / CEFFU) HMAC + JWT                                      | 60d                          | High-value; aligned with custodian rotation API                          |
| Per-venue trade-scope                                                                 | 30d                          | Highest exposure to per-venue compromise (trades possible)               |
| Per-venue read-scope                                                                  | 60d                          | Lower exposure (market data only)                                        |
| Per-venue withdraw-scope                                                              | per-use                      | Manual rotation post-each-withdrawal (operator runbook)                  |
| Prediction venues                                                                     | 60d                          | Polymarket / Kalshi                                                      |
| Data sources (api-football, footystats, helius, coingecko, tenderly, barchart, yahoo) | 90d                          | Data only; lower risk                                                    |
| Aux services (Telegram, Firebase SA, Anthropic)                                       | 90d                          | No trading authority                                                     |
| GHA Workload Identity Federation                                                      | indefinite                   | OIDC-trust; no long-lived PAT to rotate                                  |

---

## § 2 — Cloud HSM CMK rotation (May-23 cutover gate)

```yaml
execution:
  owner: deployment-service maintainer + ikennaigboaka (operator)
  cadence: 90d automatic
  verifier: `gcloud kms keys describe ${cmk} --project=...` returns rotated version > prior; ciphertext re-wrap log
  last_executed: NEVER (operator first invocation post Phase B.1.2 in custody-onboarding-checklist.md)
```

GCP Cloud HSM (and AWS CloudHSM) supports automatic rotation. Cadence declared at CMK-creation time per
[`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) § B.1.2:

```bash
gcloud kms keys create "trading-${ag}-master-v1" \
  --keyring=wallets-prod --location=asia-northeast1 \
  --purpose=encryption --protection-level=hsm --rotation-period=90d \
  --next-rotation=$(date -u -v+90d +%Y-%m-%dT%H:%M:%SZ) \
  --project=central-element-323112
```

### 2.1 Per-rotation re-wrap (wallet PK ciphertext)

When a CMK rotates to a new version (e.g. `v1 → v2`), every wallet PK ciphertext wrapped by the old version must be
re-wrapped under the new version BEFORE the old version is destroyed. Otherwise wallets become inaccessible
post-destroy.

Operator runbook (manual one-shot per rotation event):

1. List affected secrets: `gcloud secrets list --filter='name:*-wrapped'`.
2. For each: `gcloud kms decrypt --key=trading-${ag}-master-v1 --version=v1 ciphertext.bin → plaintext`. Held in memory
   ONLY during re-wrap; never logged.
3. `gcloud kms encrypt --key=trading-${ag}-master-v1 --version=v2 plaintext → ciphertext-v2.bin`. Securely wipe
   plaintext.
4. Update Secret Manager: `gcloud secrets versions add ${secret} --data-file=ciphertext-v2.bin`.
5. Verify trading-VM SA can decrypt the new ciphertext via the new CMK version.
6. After 7-day grace + verification across all wallets, destroy CMK v1 via `gcloud kms keys versions destroy v1`.

### 2.2 Continuous verification

Daily cron `credential-probe.sh --mode live` includes `cloud_kms_cmk_*` probes (see
[`credentials-matrix.md`](credentials-matrix.md) § 6) — fails if KMS Decrypt returns version mismatch.

---

## § 3 — Custody MPC creds (Copper + Fireblocks + CEFFU)

```yaml
execution:
  owner: operator + custodian-side rotation API
  cadence: 60d
  verifier: `python -m execution_service.scripts.copper_smoke --sandbox` returns success
  last_executed: NEVER (pending operator first cycle)
```

### 3.1 Copper rotation (HMAC api_key + api_secret)

Per Copper documentation + [`custody-providers.md`](../04-architecture/custody-providers.md) § 2.3:

1. Operator generates new api_key + api_secret via Copper dashboard (Account → API Keys → Generate New).
2. Provision new values in Secret Manager: `gcloud secrets versions add copper-api-key --data-file=- <<< "$NEW_KEY"`.
3. Allow 1-hour grace window (both old + new keys active per Copper-side policy) for trading-VM `ApiKeyReloader` to pick
   up new values.
4. Verify via sandbox:
   `CUSTODY_PROVIDER=copper COPPER_SANDBOX=true python -m execution_service.scripts.copper_smoke --list-wallets`. Should
   return ≥1 wallet.
5. Revoke old api_key in Copper dashboard.
6. Verify via production: `CUSTODY_PROVIDER=copper python -m execution_service.scripts.copper_smoke --balance-only`
   (read-only) returns balances.

### 3.2 Fireblocks rotation (RSA PEM + API user)

Per [`fireblocks-integration-spec.md`](fireblocks-integration-spec.md) § 2.3:

1. Operator generates new RSA keypair on cold laptop: `openssl genrsa -out fireblocks-private-new.pem 4096`.
2. Upload public key half to Fireblocks dashboard (Settings → API Users → Edit → New Public Key).
3. Provision private PEM in Secret Manager (base64-encoded):
   `base64 fireblocks-private-new.pem | gcloud secrets versions add fireblocks-api-secret --data-file=-`.
4. Verify via sandbox: `fireblocks_smoke.py --sandbox --vault-list` returns expected vaults.
5. Revoke old public key in Fireblocks dashboard.

### 3.3 CEFFU rotation

Pending CEFFU API spec ingestion per [`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) § D.2.
Expected to mirror Copper HMAC pattern.

---

## § 4 — Per-venue trade-scope rotation (30d)

```yaml
execution:
  owner: operator (per-venue web UI flow)
  cadence: 30d
  verifier: `credential-probe.sh --mode live --archetype carry_staked_basis` returns 100% pass
  last_executed: NEVER
```

For each of the 10 venues (Bybit / Binance / OKX / Deribit / Hyperliquid / Aster / Upbit / Kraken / Bitfinex / Bitget):

1. Operator logs into venue dashboard + generates new trade-scope sub-key (IP whitelist pinned to VM egress IPs where
   supported).
2. Provision in Secret Manager per [`secret-manager-naming.md`](secret-manager-naming.md) § 2.2:
   `<venue>-trade-{api-key,api-secret,passphrase}`.
3. Trading-VM `ApiKeyReloader` (from UTL) picks up new keys within reload interval (default 60s).
4. Revoke old trade-scope key in venue dashboard.
5. Verify trade execution end-to-end via paper-trade smoke (`launch-paper-trade-vm.sh --venue=<venue>`).

Per-venue API key revocation is a P0 operator-action — leaving old keys active triples the compromise surface area for
the rotation window.

---

## § 5 — Data + auxiliary credential rotation (60-90d)

```yaml
execution:
  owner: operator + deployment-service per-secret refresh script
  cadence: 60-90d per class
  verifier: `credential-probe.sh --mode live` per-data-source PASS
  last_executed: NEVER
```

Per [`credentials-matrix.md`](credentials-matrix.md) § 1, data + aux creds:

- Sports (api-football, footystats, soccer-football-info): 90d.
- DeFi data (helius, coingecko, tenderly): 90d.
- VIX 15m sources (barchart, yahoo): 90d.
- Telegram bot tokens (dev / staging / prod): 90d.
- Anthropic API: 90d (per-workflow budget cap applies, see Plan Phase 6.D).
- Firebase SA JSON: 90d (Workload Identity Federation preferred where possible).
- Prediction (polymarket, kalshi): 60d.

Rotation runbook for any data API key:

1. Operator generates new key via provider dashboard.
2. `gcloud secrets versions add <secret-name> --data-file=- <<< "$NEW_KEY"`.
3. Wait 1-cycle for consumer services to reload via `ApiKeyReloader`.
4. Revoke old key in provider dashboard.
5. Verify via service health endpoint: `curl ${service}/health/credentials` (Phase 8.B Health Endpoint Credential
   Probes).

---

## § 6 — Pre-cutover rotation gate (one-shot 2026-05-22)

Before live-trading kill-switch is disarmed for May-23 cutover, operator MUST rotate every credential that has been in
production for >90 days.

Pre-cutover acceptance:

- ✅ `credential-probe.sh --mode live --archetype carry_staked_basis` returns 100% pass.
- ✅ `credential-probe.sh --mode live --archetype ARBITRAGE_PRICE_DISPERSION` returns 100% pass.
- ✅ Every CMK shows `creation_timestamp > 2026-05-12` (post-Plan-Phase-3.C.1 re-key) OR ≥1 rotation event in audit log
  since 2026-05-12.
- ✅ No human principal has `cloudkms.cryptoKeyDecrypter` role on any `wallets-prod` CMK (verified via
  `gcloud kms keys get-iam-policy`).

Operator sign-off recorded in
[`plans/active/master_to_live_defi_2026_05_23.md`](../../plans/active/master_to_live_defi_2026_05_23.md) Group F
continuous-verification column.

---

## § 7 — Post-cutover rotation calendar

Cycle 1: 2026-05-23 → 2026-06-23 (30d). First trade-scope rotation 2026-06-22. First custody MPC rotation 2026-07-22.

Cycle 2: 2026-06-23 → 2026-07-23. Per-class cadence as § 1 above.

CMK 90d auto-rotation: first event 2026-08-12 (90d after 2026-05-14 first provisioning). Re-wrap operator-action per §
2.1.

Anniversary review every 6 months: operator + slot 4 successor jointly audit rotation cadence + bump any class showing
zero rotation events.

---

## § 8 — References

- [`credentials-matrix.md`](credentials-matrix.md) — workspace credential SSOT.
- [`secret-manager-naming.md`](secret-manager-naming.md) — naming convention.
- [`custody-providers.md`](../04-architecture/custody-providers.md) — Copper + CEFFU + Fireblocks architecture.
- [`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) — § A
  - B + C operator-action runbooks per surface.
- [`hsm-wallet-signing.md`](hsm-wallet-signing.md) — § 6 acceptance criteria.
- [`fireblocks-integration-spec.md`](fireblocks-integration-spec.md) — § 2.3 RS256 JWT auth + rotation pattern.
- [`deployment-service/scripts/audit/credential-probe.sh`](../../deployment-service/scripts/audit/credential-probe.sh) —
  audit harness used in pre-cutover gate + daily cron.
