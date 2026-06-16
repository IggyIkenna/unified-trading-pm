---
scope: [admin, engineer]
execution:
  owner: operator (custody portal logins, KYC + approval flows are human-attended)
  cadence: one-shot (May-23 cutover) + per-onboarding (June-1 client-credential integration repeats per new client)
  verifier:
    each section's "verification" sub-step (custody portal confirmation, exchange-side balance pull match, signed
    approval doc in compliance vault); cross-ref `master_to_live_defi_2026_05_23.md` Group F-19.
  last_executed: NEVER (May-23 cutover + June-1 client onboarding pending)
last_reviewed: 2026-05-17
---

# Custody onboarding operator-action checklist

> **Created 2026-05-12** by slot 4 (`ikenna-keys-wallets-tab`) per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 1 — operator-action checklist for the May-23 cutover + June-1 client-credential integration. Pairs with
> [`codex/04-architecture/custody-providers.md`](../04-architecture/custody-providers.md) (architectural SSOT) +
> [`codex/04-architecture/wallet-hierarchy-and-capital-flow.md`](../04-architecture/wallet-hierarchy-and-capital-flow.md)
> (capital-flow model).

This is the **operator-runnable** checklist for every custody-onboarding human action that cannot be automated by an
agent. Each section declares: required form fields / document uploads / portal logins / approval steps + SLA + the
execution-owner field per the `Runbook Execution-Owner SSOT` HARD RULE.

---

## 2026-05-12 PM scope contraction — May-23 = operator-self only

Operator clarifications 2026-05-12 PM: **all custody-provider onboarding is post-cutover (June-1+).** May-23 ships on
the Cloud-KMS path with the operator's own wallet — no client funds, no Copper, no CEFFU, no Fireblocks for the ≥7-day
live smoke.

What this means for this checklist:

- **§ A (Copper KYB)**: deferred to June-1+ window. Operator does NOT need to complete the Copper sandbox
  sign-and-broadcast smoke (§ A.1.5) for May-23. The Copper code path (`COPPER_MPC` signing_surface) stays wired for
  per-wallet flippability post-June-1.
- **§ B (Cloud HSM CMK provisioning)**: stays in scope for May-23. Already ✅ DONE (10 HSM-backed CMKs in
  `asia-northeast1` 2026-05-12, smoke PASSED).
- **§ C (Fireblocks)**: deferred to June-1+. Successor plan
  [`fireblocks_copper_client_integration_2026_06_01.md`](../../plans/active/fireblocks_copper_client_integration_2026_06_01.md).
- **§ D (CEFFU KYB)**: deferred to June-1+. The 2-4 week SLA does NOT gate May-23 anymore — KYB submission can wait
  until client-credential window is firm.

**Operator pre-cutover-2026-05-22 work for May-23 reduces to**: run
`credential-probe.sh --mode live --archetype carry_staked_basis` (Phase 8.D gate) + verify own-wallet test transactions
sign cleanly via CloudKmsCustodyProvider.

---

## R9 sub-(a) — RESOLVED 2026-05-12 (HSM-grade signing tier choice)

**Operator direction 2026-05-12** (verbatim): _"client gives us [Copper/Fireblocks] credentials June 1st when we go live
with them — we need best equivalent to test earlier or use our trust wallet but be ready for integration with them June
1st."_

| Window                         | Signing tier                                                | UAC `SigningSurface` value                             | Operator action                                                        |
| ------------------------------ | ----------------------------------------------------------- | ------------------------------------------------------ | ---------------------------------------------------------------------- |
| **2026-05-12 → 05-23 cutover** | Cloud-KMS-encrypted PK                                      | `CLOUD_KMS_ENCRYPTED`                                  | Provision GCP Cloud HSM / AWS CloudHSM CMK per asset_group (§ B below) |
| **2026-06-01 onwards**         | Copper.co MPC (DeFi + non-Binance CeFi)                     | `COPPER_MPC`                                           | Receive client-provided creds + flip per-wallet config (§ C below)     |
| **2026-06-01 onwards**         | Fireblocks MPC (carry strategies + HSM-grade hedge wallets) | `FIREBLOCKS_MPC`                                       | Receive client-provided creds + flip per-wallet config (§ D below)     |
| **2026-06-01 onwards**         | CEFFU (Binance institutional spot + perp)                   | `COPPER_MPC` _(CEFFU stub-shipped; awaiting API spec)_ | KYB completion + CEFFU API spec ingestion (§ E below)                  |

**Per-wallet flippability**: each
[`WalletProvisioningConfig`](../../unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py)
row carries its own `signing_surface` — flips are **config-only, no recompile, no service restart** (factory routing per
[`custody-providers.md`](../04-architecture/custody-providers.md) § 1).

---

## § A — Copper.co (already wired — verification checklist only)

**Status**: ✅ wired since 2026-05-10 at
[`execution-service/.../custody/copper.py`](../../execution-service/execution_service/custody/copper.py). HMAC-SHA256
signing, sandbox + production endpoints configured. Pre-cutover task is **verification of operator-side Copper account
state**, not new onboarding.

### A.1 Pre-cutover verification (operator-runnable)

```yaml
execution:
  owner: ikennaigboaka (operator) + main agent
  cadence: one-shot pre-cutover (target 2026-05-20)
  verifier: `python -m execution_service.scripts.copper_smoke --sandbox --tx-hash-on-sepolia`
  last_executed: NEVER
```

Operator-action items:

- [ ] **A.1.1** Confirm Copper organisation ID + production API key + HMAC secret are in GCP Secret Manager at
      `copper-api-key` / `copper-api-secret` / `copper-org-id`. Verify via
      `gcloud secrets versions access latest --secret=copper-api-key --project=central-element-323112` returns a
      non-placeholder value (length > 20 chars).
- [ ] **A.1.2** Sandbox creds in `copper-sandbox-api-key` / `copper-sandbox-api-secret`. Smoke via
      `CUSTODY_PROVIDER=copper COPPER_SANDBOX=true python -m execution_service.scripts.copper_smoke --list-wallets`
      returns ≥ 1 wallet.
- [ ] **A.1.3** Withdrawal whitelist populated for the May-23 cutover archetypes — operator logs into Copper dashboard →
      Compliance → Whitelisted Addresses → ensures every `allowed_destinations` entry in production
      `wallet_provisioning.json` matches a Copper-side whitelist entry. Mismatch =
      `OrderError("destination_not_whitelisted")` at first live withdraw attempt.
- [ ] **A.1.4** Transfer policies (per Copper dashboard): max per-tx + max per-hour + max per-day caps set per wallet.
      MUST match `SpendingCaps` values in `WalletProvisioningConfig`. Reconcile via deployment-UI Treasury tab once
      shipped (slot 8 cross_cutting #4 scope).
- [ ] **A.1.5** Real sign-and-broadcast smoke test on Sepolia:
      `CopperCustodyProvider.sign_transaction(wallet_id=<test>,     chain="ethereum-sepolia", raw_tx=<test>)` → POST
      `/platform/orders` → POST `/orders/{id}/sign` → MPC signing → on-chain broadcast → confirm tx hash on Sepolia
      Etherscan. **Per Plan Phase 3.A**: tx.from == copper_wallet_address; round-trip latency ≤30s.

### A.2 Per-wallet flip from Cloud-KMS → Copper (June-1)

When client delivers Copper creds June-1:

- [ ] **A.2.1** Operator updates Secret Manager with client-provided creds (overwrite the placeholder values used during
      cutover): `gcloud secrets versions add copper-api-key --data-file=...`.
- [ ] **A.2.2** Operator edits `gs://wallet-config-{pid}/{chain_env}/wallet_provisioning.json` per affected wallet:
      `signing_surface: COPPER_MPC` + `custodian_wallet_id: <Copper portfolioId>` + clear `kms_key_uri`.
- [ ] **A.2.3** Singleton-locked `launch-defi-paper-trade-vm.sh --copper-flip-smoke` rolls per-wallet flip on testnet
      first; production flip via deployment-UI Live-Cluster button (per Phase 11.4 button shipped 2026-05-11).

---

## § B — Cloud-KMS-encrypted private key (May-23 cutover path — NEW provisioning)

> **[DELTA 2026-05-22]** **Current state:** GCP Cloud HSM CMKs are DONE — 10 HSM-backed CMKs provisioned in
> `asia-northeast1` 2026-05-12, smoke PASSED. AWS KMS CMK provisioning and wallet envelope-encryption are PENDING
> operator-action (pre-cutover). **Planned delta:** AWS KMS + wallet-PK encryption tracked as pre-cutover operator
> actions under `plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 3.C. **Target architecture:** All
> CMKs provisioned on both clouds; all trading wallet PKs envelope-encrypted at rest.

**Status**: GCP CMKs ✅ DONE (2026-05-12, smoke PASSED). AWS KMS provisioning PENDING. Implementation path:
`execution-service/execution_service/custody/cloud_kms.py` (NEW per Plan Phase 3.C.1).

### B.1 GCP Cloud HSM CMK provisioning (asia-northeast1)

```yaml
execution:
  owner: ikennaigboaka (operator) — ADC perms confirmed for central-element-323112
  cadence: one-shot per asset_group (5 CMKs target: defi / cefi / tradfi / sports / prediction)
  verifier: `gcloud kms keys describe <key> --keyring=wallets-prod --location=asia-northeast1`
  last_executed: NEVER
```

Operator-action items:

- [ ] **B.1.1** Create KeyRing per environment:
      `gcloud kms keyrings create wallets-prod --location=asia-northeast1 --project=central-element-323112`
      (production); `wallets-staging` for staging.
- [ ] **B.1.2** Create per-asset_group HSM-backed CMK:
      `bash     for ag in defi cefi tradfi sports prediction; do       gcloud kms keys create "trading-${ag}-master-v1" \         --keyring=wallets-prod --location=asia-northeast1 \         --purpose=encryption --protection-level=hsm --rotation-period=90d \         --next-rotation=$(date -u -v+90d +%Y-%m-%dT%H:%M:%SZ) \         --project=central-element-323112     done     `
- [ ] **B.1.3** Bind KMS Decrypter to trading-VM SA **only** (no human principals):
      `bash     for ag in defi cefi tradfi sports prediction; do       gcloud kms keys add-iam-policy-binding "trading-${ag}-master-v1" \         --keyring=wallets-prod --location=asia-northeast1 \         --member="serviceAccount:trading-vm-${ag}@central-element-323112.iam.gserviceaccount.com" \         --role=roles/cloudkms.cryptoKeyDecrypter \         --project=central-element-323112     done     `
- [ ] **B.1.4** Verify NO `roles/cloudkms.cryptoKeyEncrypterDecrypter` is granted to ANY human principal:
      `gcloud kms keys get-iam-policy ... | grep -v "serviceAccount:"`. Should return only `serviceAccount:` entries.
- [ ] **B.1.5** Enable Cloud KMS audit logging for every `kms.decrypt` call:
      `gcloud logging sinks create kms-decrypt-audit --log-filter='protoPayload.methodName="Decrypt"     protoPayload.serviceName="cloudkms.googleapis.com"' bigquery.googleapis.com/projects/.../datasets/audit_logs`.

### B.2 AWS KMS CMK provisioning (ap-northeast-1)

Same shape for AWS, region-pinned to ap-northeast-1 per Tokyo same-metro egress rule.

> **Origin note**: `--origin AWS_CLOUDHSM` (FIPS 140-2 Level 3) requires a provisioned CloudHSM cluster (~$1.60/hour per
> HSM). For May-23 without a cluster, use `--origin AWS_KMS` (FIPS 140-2 Level 2, multi-tenant HSM-backed). The
> `CloudKmsCustodyProvider` code works identically with both origins — the ARN format is the same.

```yaml
execution:
  owner: operator (admin_od IAM role on AWS account 427895769566)
  cadence: one-shot per asset_group (5 CMKs target: defi / cefi / tradfi / sports / prediction)
  verifier: `aws kms describe-key --key-id <key-id> --region ap-northeast-1`
  last_executed: NEVER
```

- [ ] **B.2.1** Create CMK per asset_group (use `AWS_KMS` for May-23; swap `AWS_CLOUDHSM` post-cluster-provisioning):
      `bash     for ag in defi cefi tradfi sports prediction; do       aws kms create-key \         --description "trading-${ag}-master-v1" \         --key-usage ENCRYPT_DECRYPT \         --customer-master-key-spec SYMMETRIC_DEFAULT \         --origin AWS_KMS \         --region ap-northeast-1     done     `
      Note the `KeyId` (UUID) returned per key — needed for alias + ARN construction.
- [ ] **B.2.2** Create human-readable aliases (required for `kms_key_uri` ARN in `WalletProvisioningConfig`):
      `bash     for ag in defi cefi tradfi sports prediction; do       aws kms create-alias \         --alias-name "alias/trading-${ag}-master-v1" \         --target-key-id <key-id-from-B.2.1-for-${ag}> \         --region ap-northeast-1     done     `
      The full ARN form used in code: `arn:aws:kms:ap-northeast-1:427895769566:key/<key-id>`.
- [ ] **B.2.3** Bind `kms:Decrypt` to trading-VM EC2 instance role **only**. NO human IAM principals:
      `bash     aws kms put-key-policy \       --key-id <key-id> \       --policy-name default \       --policy '{"Version":"2012-10-17","Statement":[{"Sid":"AllowDecryptByTradingVMRoleOnly","Effect":"Allow","Principal":{"AWS":"arn:aws:iam::427895769566:role/trading-vm-role"},"Action":["kms:Decrypt"],"Resource":"*"}]}' \       --region ap-northeast-1     `
      Verify:
      `aws kms get-key-policy --key-id <key-id> --policy-name default --region ap-northeast-1 | grep -v "trading-vm-role"`
      should return only the KMS service principle, no human principals.
- [ ] **B.2.4** CloudTrail logging enabled for all CMK actions. Verify via AWS Console → CloudTrail → Event history
      filter: `eventSource=kms.amazonaws.com, eventName=Decrypt`.
- [ ] **B.2.5** Envelope-encrypt the wallet PK + store wrapped ciphertext in AWS Secrets Manager (AWS equivalent of GCP
      B.3.2): ```bash # Step 1: encrypt PK with AWS KMS (offline cold laptop with AWS CLI configured) echo -n "$RAW_PK"
      | \
       aws kms encrypt \
       --key-id arn:aws:kms:ap-northeast-1:427895769566:key/<defi-key-id> \
       --plaintext fileb:///dev/stdin \
       --query CiphertextBlob \
       --output text \
       --region ap-northeast-1 > /tmp/wrapped.b64

      # Step 2: store wrapped ciphertext as-is in Secrets Manager (SecretString = base64-encoded ciphertext blob)
      aws secretsmanager create-secret \
        --name "defi-eth-hot-aave-v1-wrapped" \
        --secret-string "$(cat /tmp/wrapped.b64)" \
        --region ap-northeast-1

      # Step 3: wipe temp file immediately
      shred -u /tmp/wrapped.b64
      ```
      Secret name must match byte-for-byte with `WalletProvisioningConfig.private_key_secret_ref`.

- [ ] **B.2.6** Populate `WalletProvisioningConfig` row with AWS ARN form for `kms_key_uri`:
      `python     WalletProvisioningConfig(         wallet_id="defi-eth-hot-aave-v1",         chain="ETHEREUM",         kind=WalletKind.HOT_TRADING,         signing_surface=SigningSurface.CLOUD_KMS_ENCRYPTED,         kms_key_uri="arn:aws:kms:ap-northeast-1:427895769566:key/<defi-key-id>",         private_key_secret_ref="defi-eth-hot-aave-v1-wrapped",         archetype_id="carry_staked_basis",     )     `
      The `CloudKmsCustodyProvider` detects `cloud_provider="aws"` and routes to `boto3.client("kms")` +
      `client.decrypt(CiphertextBlob=wrapped, KeyId=kms_key_uri)` automatically (no code change needed).

### B.3 Per-wallet envelope-encrypted PK provisioning

For each May-23 cutover wallet (≥10 mainnet wallets per Plan Phase 4.A: 2 archetypes × 5 chains):

- [ ] **B.3.1** Generate fresh EVM / Solana key pair via offline cold laptop (NOT the trading VM). Operator records the
      address; PK never touches networked machine in plaintext form after this step.
- [ ] **B.3.2** Envelope-encrypt the PK:
      `bash     gcloud kms encrypt \       --key=trading-defi-master-v1 --keyring=wallets-prod --location=asia-northeast1 \       --plaintext-file=/dev/stdin --ciphertext-file=- \       --project=central-element-323112 <<< "$RAW_PK" | base64 > /tmp/wrapped.b64     `
      Then store the wrapped ciphertext in Secret Manager:
      `gcloud secrets create defi-eth-hot-aave-v1-wrapped --data-file=/tmp/wrapped.b64`.
- [ ] **B.3.3** Securely wipe the cold-laptop key material per data-destruction policy (operator-runbook).
- [ ] **B.3.4** Populate `WalletProvisioningConfig` row in `gs://wallet-config-{pid}/mainnet/wallet_provisioning.json`:
      `python     WalletProvisioningConfig(         wallet_id="defi-eth-hot-aave-v1",         chain="ETHEREUM",         kind=WalletKind.HOT_TRADING,         signing_surface=SigningSurface.CLOUD_KMS_ENCRYPTED,         kms_key_uri="projects/central-element-323112/locations/asia-northeast1/keyRings/wallets-prod/cryptoKeys/trading-defi-master-v1",         private_key_secret_ref="defi-eth-hot-aave-v1-wrapped",  # Secret Manager ref to wrapped ciphertext         allowed_protocols=frozenset({"AAVE_V3", "UNISWAP_V3"}),         spending_caps=SpendingCaps(             per_tx_usd=Decimal("50000"),             per_day_usd=Decimal("1000000"),             per_protocol_usd={"AAVE_V3": Decimal("500000")},         ),         kill_switch_id="KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS",         archetype_id="carry_staked_basis",     )     `
      Note: `private_key_secret_ref` is OVERLOADED for CLOUD_KMS_ENCRYPTED (wrapped ciphertext lives in Secret Manager;
      CMK decrypts at runtime). Adapter-side wiring per Plan Phase 3.C.1.

### B.4 Sepolia + Solana devnet smoke (pre-cutover gate)

- [ ] **B.4.1** Provision testnet equivalents of every mainnet wallet in
      `gs://wallet-config-{pid}/testnet/wallet_provisioning.json`.
- [ ] **B.4.2** Fund each via Sepolia faucet (Alchemy / QuickNode) + Solana devnet airdrop.
- [ ] **B.4.3** Singleton-locked
      `launch-defi-paper-trade-vm.sh --signing-surface=CLOUD_KMS_ENCRYPTED --testnet --asset-group=defi` signs a
      transaction; verify event-stream emits per-wallet `CLOUD_KMS_TX_SIGNED` + tx hash visible on Sepolia Etherscan (or
      Solana Explorer for SOL).
- [ ] **B.4.4** Decrypt latency probe: ≤200ms per `kms.decrypt` call (GCP Cloud HSM SLA budget). Log to event-stream per
      `STARTED`+`progress`+`STOPPED` cycle (`no fire-and-forget` rule).

---

## § C — Fireblocks (June-1 path — DEFERRED-AFTER-CUTOVER 2026-06-01)

**Status**: 🟡 DEFERRED-AFTER-CUTOVER. Client provides Fireblocks vault credentials June-1. Adapter implementation per
Plan Phase 3.C.2 (`execution-service/execution_service/custody/fireblocks.py` NEW) is gated on creds delivery.

```yaml
execution:
  owner: operator + Ikenna slot 4 successor (post-cutover)
  cadence: one-shot June-1 → ongoing flip per-wallet
  verifier: `fireblocks_smoke.py --sandbox --tx-hash-on-sepolia`
  last_executed: NEVER
```

### C.1 Pre-June-1 (operator-coordinated with client)

- [ ] **C.1.1** Confirm with client which Fireblocks vault accounts are allocated to UTS strategies. Get vault IDs +
      addresses + supported chains.
- [ ] **C.1.2** Client provisions Fireblocks API user + key + secret. Stored in client-side Fireblocks dashboard;
      transferred to UTS GCP Secret Manager at `fireblocks-api-key` / `fireblocks-api-secret` /
      `fireblocks-vault-account-id`.
- [ ] **C.1.3** Withdrawal whitelist (Fireblocks AddressBook) populated by client per the `allowed_destinations`
      requirement.
- [ ] **C.1.4** Co-signer policy reviewed with client: who can approve per-tx? Default = automated for amounts <
      `SpendingCaps.per_tx_usd`; manual co-sign for amounts ≥ that.

### C.2 June-1 implementation (Plan Phase 3.C.2)

- [ ] **C.2.1** Implement `FireblocksCustodyProvider` at `execution-service/execution_service/custody/fireblocks.py`
      mirroring Copper factory shape. Reference: Fireblocks Python SDK (`fireblocks-sdk-python` — pin version in
      `pyproject.toml`).
- [ ] **C.2.2** Register in `custody/factory.py` for `"fireblocks"` key. Test via unit + integration tests in
      `tests/unit/custody/test_fireblocks_provider.py` + `tests/integration/test_fireblocks_custody_provider.py`.
- [ ] **C.2.3** Per-wallet flip from `CLOUD_KMS_ENCRYPTED` → `FIREBLOCKS_MPC`: operator edits `wallet_provisioning.json`
      row: `signing_surface: FIREBLOCKS_MPC` + `custodian_wallet_id: <vaultAccountId>` + clear `kms_key_uri` + clear
      `private_key_secret_ref`.
- [ ] **C.2.4** HD derivation under Fireblocks-protected master key for N×M wallet expansion (per Plan Phase 4.A
      sub-residual). Validate every derivation path resolves via `fireblocks.get_vault_account_assets(vault_id)`.

---

## § D — CEFFU (Binance institutional — DEFERRED-AFTER-CUTOVER)

**Status**: 🟡 KYB ONGOING — longest single lead time per Plan Phase 3.B (2-4 weeks operator-side). Adapter
**stub-shipped** at `execution-service/execution_service/custody/ceffu.py` per
[`custody-providers.md`](../04-architecture/custody-providers.md) § 2.4. Async methods raise
`NotImplementedError("CEFFU API spec pending")` — flip to real implementation gated on operator-provided API spec.

```yaml
execution:
  owner: operator (KYB) + Ikenna slot 4 successor (adapter completion)
  cadence: one-shot KYB → ongoing per-flow
  verifier: `ceffu_smoke.py --sandbox --binance-perp-collateral-move`
  last_executed: NEVER
```

### D.1 CEFFU institutional KYB onboarding

- [ ] **D.1.1** Operator signs Binance Institutional Services agreement, opening an OES-eligible Binance Futures
      account. CEFFU named as off-exchange custodian. **Required documents**: corporate registration / ultimate
      beneficial owner declaration / AML compliance certification / proof of office address / board resolution
      authorising the trading mandate. Operator collects + uploads per Binance Institutional onboarding portal.
- [ ] **D.1.2** Operator signs CEFFU custody agreement (separate from Binance). Receives CEFFU institutional account
      ID + API credentials (HMAC key + secret, parity expectations with Copper).
- [ ] **D.1.3** CEFFU enables OES bilateral mirror to the Binance account from step D.1.1. ETA: 2-4 weeks post-KYB
      submission per operator field experience.
- [ ] **D.1.4** Operator requests CEFFU **sandbox** credentials separately (allows paper-trade smoke before any prod
      capital moves).

### D.2 CEFFU API spec ingestion (Plan Phase 3.B.3)

When CEFFU delivers API spec:

- [ ] **D.2.1** Operator drops the spec at `unified-trading-pm/codex/04-architecture/_ceffu-api-spec.pdf` (or yaml
      equivalent).
- [ ] **D.2.2** Agent (slot 4 successor) replaces every `NotImplementedError("CEFFU API spec pending")` in
      `custody/ceffu.py` with the real REST endpoint shape. Cassette path: `tests/cassettes/ceffu/{sign,balance}.yaml`
      via `unified-api-contracts/tests/test_cassette_schema_parity.py`.
- [ ] **D.2.3** Update `custody-providers.md` § 2.4 — replace the 8 `<TBD-OPERATOR-PROVIDES-API-SPEC>` markers + close
      out the 8 open questions in that file.
- [ ] **D.2.4** Integration test against CEFFU sandbox: `tests/integration/test_ceffu_custody_provider.py` shipped +
      green.

### D.3 CEFFU operational decisions still pending operator triage

(Mirrors `custody-providers.md` § 2.4 open questions — repeated here as operator-action items.)

- [ ] **D.3.1** Does CEFFU expose a sub-account-per-strategy model out-of-the-box, OR do we manage strategy-attribution
      at PBMS layer?
- [ ] **D.3.2** Is there a CEFFU-side "circuit breaker" or do we rely on Binance account-level withdrawal limits + our
      `KillSwitchBus` rules?
- [ ] **D.3.3** AWS-region pinning: CEFFU API endpoint region-specific or global edge-cached?
- [ ] **D.3.4** Cost / fee model (CEFFU institutional pricing is bespoke per client).
- [ ] **D.3.5** Withdrawal whitelist management: API-driven or operator-driven via CEFFU dashboard?
- [ ] **D.3.6** Daily settlement window UTC hour.
- [ ] **D.3.7** Exact REST endpoint paths + auth header naming convention.
- [ ] **D.3.8** Sandbox base URL for staging-only paper-trade smokes.

---

## § E — Multi-tier risk wiring (per-wallet kill-switch + spending caps)

Every wallet in `wallet_provisioning.json` MUST declare `kill_switch_id` + `spending_caps`. These are pre-flight risk
controls + post-trade kill-switch triggers — wallet-tier is the FINEST-grain switch beyond per-venue + per-archetype.

### E.1 Per-wallet kill-switch binding (operator-runbook)

- [ ] **E.1.1** For every HOT*TRADING wallet, pick a kill_switch_id from the closed set in
      [`kill_switch.py`](../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/kill_switch.py)
      `KillSwitchId` enum. Typical:
      `KILL_PER_ARCHETYPE*<ARCHETYPE>`(freezes all wallets for one archetype).     Per-wallet finer freezes are POST-cutover (no`KILL*PER_WALLET*\*`
      exists yet — open follow-up).
- [ ] **E.1.2** Wire wallet-tier button into deployment-UI Live-Cluster button per slot 8 cross_cutting #4 (in progress
      2026-05-12).
- [ ] **E.1.3** Operator smoke-tests:
      `python -m execution_service.scripts.kill_switch_smoke --wallet-id=defi-eth-hot-aave-v1     --provenance=OPERATOR_MANUAL`
      → confirm `KILL_SWITCH_ARMED` event + adapter rejects subsequent orders with `WalletKillSwitchActiveError`.

### E.2 Per-wallet spending caps SSOT

- [ ] **E.2.1** Populate `SpendingCaps(per_tx_usd, per_hour_usd, per_day_usd, per_protocol_usd)` per wallet at
      provisioning time. Source: per-archetype risk budget per
      [`risk_simulations_limits_alerting_2026_05_10.md`](../../plans/archive/risk_simulations_limits_alerting_2026_05_10.md).
- [ ] **E.2.2** Reconcile caps against per-venue / per-archetype caps. Per-wallet must be `≤` per-archetype cap;
      per-archetype must be `≤` per-asset_group cap (closed-set hierarchy).
- [ ] **E.2.3** Verify position-balance-monitor rolling-window accumulators consume `SpendingCaps`. (Plan Phase 4.A
      sub-residual: nonce queue + rolling-window cap enforcement.)

---

## § F — Continuous-verification cadence (per `Runbook Execution-Owner SSOT` HARD RULE)

| Surface                     | Cron / Tab                                       | Cadence         | Verifier                                                             |
| --------------------------- | ------------------------------------------------ | --------------- | -------------------------------------------------------------------- |
| Copper (post-cutover)       | Daily cron VM `credential-probe-vm`              | daily 06:00 UTC | `credential-probe.sh --mode live --custody copper` returns 100% pass |
| Cloud-KMS (May-23 → June-1) | Same cron                                        | daily           | `kms.decrypt` smoke per CMK ≤200ms                                   |
| Fireblocks (post-June-1)    | Same cron                                        | daily           | `fireblocks_smoke.py --vault-list` returns expected vault count      |
| CEFFU (post-KYB)            | Same cron                                        | daily           | `ceffu_smoke.py --balance` returns non-empty per-account             |
| All wallets                 | `position-balance-monitor` continuous reconciler | every 60s       | on-chain balance matches `WalletProvisioningConfig.address`          |

Pre-cutover (May-22) gate: full `credential-probe.sh` MUST return 100% pass before live-trading kill-switch is disarmed.
Per Plan Phase 8.D.

---

## § G — Open operator-action issues filed (per Findings Triage HARD RULE)

| Status     | Issue                                                                                       | Owner                                | Filed      |
| ---------- | ------------------------------------------------------------------------------------------- | ------------------------------------ | ---------- |
| 🟡 OPEN    | Cloud HSM CMK provisioning per asset_group (§ B.1 / B.2) — operator runs gcloud + aws CLIs  | operator + slot 4                    | 2026-05-12 |
| 🟡 OPEN    | Cold-laptop key-generation protocol (§ B.3.1) — operator hardware + data-destruction policy | operator                             | 2026-05-12 |
| 🟡 BLOCKED | CEFFU KYB submission (§ D.1) — operator-side, 2-4 week SLA                                  | operator                             | 2026-05-10 |
| 🟡 BLOCKED | CEFFU API spec ingestion (§ D.2) — gated on D.1 + CEFFU delivery                            | operator → slot 4 successor          | 2026-05-10 |
| 🟡 BLOCKED | Fireblocks credentials (§ C.1) — gated on client June-1 delivery                            | client → operator → slot 4 successor | 2026-05-12 |
| 🟡 BLOCKED | Copper credentials live confirmation (§ A.2) — gated on client June-1 delivery              | client → operator                    | 2026-05-12 |

---

## § H — References

- [`codex/04-architecture/custody-providers.md`](../04-architecture/custody-providers.md) — architectural SSOT for
  Copper / CEFFU / Fireblocks / LocalKey / Mock providers.
- [`codex/04-architecture/wallet-hierarchy-and-capital-flow.md`](../04-architecture/wallet-hierarchy-and-capital-flow.md)
  — treasury / hot wallet capital model.
- [`codex/04-architecture/interface-credential-convention.md`](../04-architecture/interface-credential-convention.md) —
  service-side credential injection convention.
- [`codex/04-architecture/kill-switch-circuit-breaker.md`](../04-architecture/kill-switch-circuit-breaker.md) —
  kill-switch arm/disarm lifecycle.
- [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
  — parent plan; this doc operationalizes Phases 3.A + 3.B + 3.C + 4.A.
- [`unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py`](../../unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py)
  — `WalletProvisioningConfig` + `SigningSurface` + `WalletKind` + `SpendingCaps` SSOT.
- [`unified-api-contracts/tests/internal/unit/test_wallet_provisioning_schema.py`](../../unified-api-contracts/tests/internal/unit/test_wallet_provisioning_schema.py)
  — 27 schema-validation tests.
