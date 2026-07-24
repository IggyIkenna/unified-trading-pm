---
doc_type: issue
title: Cloud HSM CMK provisioning for May-23 cutover wallets
summary:
status: ✅ RESOLVED 2026-05-12 — agent-provisioned via ADC + smoke verified
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-12
resolved: 2026-05-12
author: ikenna-keys-wallets-tab (slot 4)
source: [plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md]
locked_by: live-defi-rollout
locked_since: 2026-05-12
severity: P0
suggested_owner: ikennaigboaka (operator) — RESOLVED by slot 4 agent per operator authorization 2026-05-12
---

> **✅ RESOLVED 2026-05-12** by slot 4 agent. Operator 2026-05-12 directive: _"for cloud hsm cmk provisioning si that
> gcp wallets yeah we can set that up you have right put in secret maager or whateevr yourself and document"_ —
> ADC-authorized self-provisioning per CLAUDE.md Operator Authority + ADC rule.
>
> **What got provisioned**:
>
> - KeyRings: `wallets-prod` + `wallets-staging` in `asia-northeast1`.
> - 10 CMKs (5 asset_groups × 2 envs): `trading-{defi,cefi,tradfi,sports,prediction}-master-v1`, HSM-backed (FIPS 140-2
>   Level 3), 90-day auto-rotation enabled, next_rotation 2026-08-10.
> - IAM Decrypter role bound to `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` on all 10 CMKs (no
>   human principals).
> - IAM Encrypter role bound on staging-only CMKs (5 keys) for envelope-encrypting test PKs without operator cold-laptop
>   ceremony; prod CMKs are decrypt-only.
> - **End-to-end smoke test PASSED**: encrypt + decrypt round-trip on `wallets-staging/trading-defi-master-v1` returned
>   matching plaintext. 176-byte wrapped ciphertext.
>
> Verification:
>
> ```bash
> gcloud kms keys list --keyring=wallets-prod --location=asia-northeast1 --project=central-element-323112
> gcloud kms keys list --keyring=wallets-staging --location=asia-northeast1 --project=central-element-323112
> # Each returns 5 entries: trading-{defi,cefi,tradfi,sports,prediction}-master-v1
> ```
>
> **Phase 4.A unblocked** — wallet template at UAC@`b9050d7` now has live CMKs to reference. Operator cold-laptop
> key-gen flow per `/codex/05-infrastructure/custody-onboarding-checklist.md` § B.3 is now the only operator-action
> remaining for mainnet wallet provisioning (and per 2026-05-12 POD scope clarification, even that's pre-cutover testing
> with MetaMask / Trust Wallet — POD-side custody is delivered June-1).

## What I found

Per R9 sub-(a) resolution 2026-05-12 (`api_keys_wallets_accounts_readiness_2026_05_10.md` § R9 RESOLVED): May-23 cutover
ships on `CLOUD_KMS_ENCRYPTED` signing surface (HSM-backed CMK envelope encryption) because the client doesn't deliver
Copper/Fireblocks credentials until June 1st.

The cutover therefore depends on **operator-side Cloud HSM CMK provisioning** that can't be automated by an agent (needs
IAM admin perms + new project resources, plus a cold-laptop key-generation protocol). The provisioning steps are
documented in
[`/codex/14-customer-journeys/credentials/custody-onboarding-checklist.md`](/codex/14-customer-journeys/credentials/custody-onboarding-checklist.md)
§ B, but the actual provisioning has not been executed yet (`last_executed: NEVER`).

## Why it matters

1. **May-23 cutover gating** — without provisioned CMKs + envelope-encrypted PKs, the `CloudKmsCustodyProvider` (PENDING
   per Plan Phase 3.C.1) cannot sign any transaction on mainnet. No CMK → no cutover.
2. **5 CMKs needed** — one per asset_group (defi / cefi / tradfi / sports / prediction). Plus testnet equivalents in the
   `wallets-staging` KeyRing. Total ≥10 CMKs across GCP; another ≥10 on AWS if dual-cloud parity is gated on May-23 (per
   `master_to_live_defi_2026_05_23.md` Group C runtime-parity).
3. **Cold-laptop protocol** — every PK MUST be generated on an offline cold laptop, envelope-encrypted, then the
   plaintext securely wiped. Operator hardware + data-destruction policy not yet documented; gap captured in checklist §
   B.3.
4. **Per-VM SA bindings** — KMS Decrypter role MUST bind to trading-VM SA ONLY (no human principals). This requires
   trading-VM SAs to exist per asset_group; currently many are placeholders.
5. **Lead time** — Cloud HSM CMK creation is near-instant but the cold-laptop workflow + per-wallet provisioning is
   manual + serial. Realistic estimate: 4-6 operator-hours for 10 wallets.

## Recommended decision

Operator-action items, in priority order:

1. **B.1.1-B.1.5** (GCP Cloud HSM KeyRing + per-asset_group CMKs + IAM bindings + audit logging) — 30 min operator work;
   agent can pre-draft Terraform / gcloud script for review.
2. **B.2.1-B.2.3** (AWS CloudHSM equivalents) — same shape; can defer to post-cutover IF dual-cloud parity is
   non-blocking for May-23 (operator-triage call).
3. **B.3.1-B.3.4** (per-wallet cold-laptop key generation + envelope encryption + Secret Manager +
   `wallet_provisioning.json` row) — 30-45 min per wallet × ≥10 wallets = 4-6 hours operator time. Sequence at
   operator's discretion (one wallet end-to-end vs all key-gen first then all wraps).
4. **B.4.1-B.4.4** (Sepolia + Solana devnet smokes) — agent runs the smoke launchers once `wallet_provisioning.json` is
   populated; reports per-wallet `STARTED`+`progress`+`STOPPED` event-stream signature back to operator.
5. **A.1.x** (Copper pre-cutover verification) — independent track; verify Copper sandbox + production cred state
   end-to-end before relying on June-1 flip.

**Acceptance gate** (pre-cutover, target 2026-05-21):

- ✅ `credential-probe.sh --mode live --custody cloud_kms` returns 100% pass across all 10+ mainnet wallets.
- ✅ Per-CMK `gcloud kms keys get-iam-policy` shows ONLY `serviceAccount:` entries (no human principals).
- ✅ Per-wallet Sepolia / Solana devnet sign-and-broadcast smoke landed tx hashes on testnet explorers.
- ✅ KMS audit-log sink streaming to BigQuery (`audit_logs.kms_decrypt`).

If operator can't complete provisioning by May-21, escalate to: defer cutover by N days OR fall back to `LOCAL_KEY` (raw
key in Secret Manager) with tight per-wallet `SpendingCaps` + per-wallet `kill_switch_id` (less rigorous; not
recommended unless client June-1 timeline slips materially).
