---
title: Cloud HSM CMK provisioning for May-23 cutover wallets
created: 2026-05-12
author: ikenna-keys-wallets-tab (slot 4)
source: [plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md]
locked_by: live-defi-rollout
locked_since: 2026-05-12
severity: P0
suggested_owner: ikennaigboaka (operator) — ADC perms confirmed on central-element-323112 + AWS 427895769566
---

# Cloud HSM CMK provisioning for May-23 cutover wallets

## What I found

Per R9 sub-(a) resolution 2026-05-12 (`api_keys_wallets_accounts_readiness_2026_05_10.md` § R9 RESOLVED): May-23
cutover ships on `CLOUD_KMS_ENCRYPTED` signing surface (HSM-backed CMK envelope encryption) because the client doesn't
deliver Copper/Fireblocks credentials until June 1st.

The cutover therefore depends on **operator-side Cloud HSM CMK provisioning** that can't be automated by an agent
(needs IAM admin perms + new project resources, plus a cold-laptop key-generation protocol). The provisioning steps are
documented in
[`codex/14-customer-journeys/credentials/custody-onboarding-checklist.md`](../../codex/14-customer-journeys/credentials/custody-onboarding-checklist.md)
§ B, but the actual provisioning has not been executed yet (`last_executed: NEVER`).

## Why it matters

1. **May-23 cutover gating** — without provisioned CMKs + envelope-encrypted PKs, the `CloudKmsCustodyProvider`
   (PENDING per Plan Phase 3.C.1) cannot sign any transaction on mainnet. No CMK → no cutover.
2. **5 CMKs needed** — one per asset_group (defi / cefi / tradfi / sports / prediction). Plus testnet equivalents in
   the `wallets-staging` KeyRing. Total ≥10 CMKs across GCP; another ≥10 on AWS if dual-cloud parity is gated on
   May-23 (per `master_to_live_defi_2026_05_23.md` Group C runtime-parity).
3. **Cold-laptop protocol** — every PK MUST be generated on an offline cold laptop, envelope-encrypted, then the
   plaintext securely wiped. Operator hardware + data-destruction policy not yet documented; gap captured in checklist
   § B.3.
4. **Per-VM SA bindings** — KMS Decrypter role MUST bind to trading-VM SA ONLY (no human principals). This requires
   trading-VM SAs to exist per asset_group; currently many are placeholders.
5. **Lead time** — Cloud HSM CMK creation is near-instant but the cold-laptop workflow + per-wallet provisioning is
   manual + serial. Realistic estimate: 4-6 operator-hours for 10 wallets.

## Recommended decision

Operator-action items, in priority order:

1. **B.1.1-B.1.5** (GCP Cloud HSM KeyRing + per-asset_group CMKs + IAM bindings + audit logging) — 30 min operator
   work; agent can pre-draft Terraform / gcloud script for review.
2. **B.2.1-B.2.3** (AWS CloudHSM equivalents) — same shape; can defer to post-cutover IF dual-cloud parity is
   non-blocking for May-23 (operator-triage call).
3. **B.3.1-B.3.4** (per-wallet cold-laptop key generation + envelope encryption + Secret Manager + `wallet_provisioning.json`
   row) — 30-45 min per wallet × ≥10 wallets = 4-6 hours operator time. Sequence at operator's discretion (one
   wallet end-to-end vs all key-gen first then all wraps).
4. **B.4.1-B.4.4** (Sepolia + Solana devnet smokes) — agent runs the smoke launchers once `wallet_provisioning.json`
   is populated; reports per-wallet `STARTED`+`progress`+`STOPPED` event-stream signature back to operator.
5. **A.1.x** (Copper pre-cutover verification) — independent track; verify Copper sandbox + production cred state
   end-to-end before relying on June-1 flip.

**Acceptance gate** (pre-cutover, target 2026-05-21):

- ✅ `credential-probe.sh --mode live --custody cloud_kms` returns 100% pass across all 10+ mainnet wallets.
- ✅ Per-CMK `gcloud kms keys get-iam-policy` shows ONLY `serviceAccount:` entries (no human principals).
- ✅ Per-wallet Sepolia / Solana devnet sign-and-broadcast smoke landed tx hashes on testnet explorers.
- ✅ KMS audit-log sink streaming to BigQuery (`audit_logs.kms_decrypt`).

If operator can't complete provisioning by May-21, escalate to: defer cutover by N days OR fall back to `LOCAL_KEY`
(raw key in Secret Manager) with tight per-wallet `SpendingCaps` + per-wallet `kill_switch_id` (less rigorous; not
recommended unless client June-1 timeline slips materially).
