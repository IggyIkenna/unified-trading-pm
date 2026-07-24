---
doc_type: plan
title: Wallet / Treasury — Phase 1+3 PULLED FORWARD pre-May-15; Phase 2 DESCOPED (Copper/CEFFU is client-side)
summary:
status: phase-1-3-pulled-forward + phase-2-descoped-client-side
nature: record
asset_group: [defi]
stage: [meta]
repos: [deployment-api, deployment-service, execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-13
updated: 2026-05-13
type: plan
deadline: 2026-05-15 (Phase 1 + Phase 3 only)
horizon: 2 days pre-freeze for Phase 1+3
predecessor: wallet_treasury_client_flow_2026_05_10.md (deferred Q3 + Q5 from design decisions 2026-05-13)
companion_to: master_to_live_defi_2026_05_23.md Group G (post-cutover operator UX + compliance)
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
parent_epic: master_to_live_defi_2026_05_23.md
priority: P1 (Phase 1+3 pulled-forward)
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-19** — Phase 1 + Phase 3 100% complete (7 checkboxes checked). Phase 2 (Copper + CEFFU) is
> client-side per operator decision 2026-05-13; no agent todos. Preserved for archaeology.

## 🟢 PULL-FORWARD UPDATE 2026-05-13 ~17:00 UTC (slot 1 main) — CORRECTED ~18:00 UTC

Per density-push capacity assessment, **Phase 1 (Real HMAC withdrawal approval chain) and Phase 3 (Audit log
immutability + 7-year retention) PULLED FORWARD to pre-May-15 freeze window**.

**Phase 2 (Real Copper + CEFFU integrations) DESCOPED from this plan**. Per Harsh-side 1M-context audit slot ping
2026-05-13 14:50 UTC (PM@`e1e67656`): _"Copper / CEFFU → marked client-side, NOT our blocker per operator direction
2026-05-13. Master plan Group F Week 2 Treasury row + api_keys_wallets 3.A/3.B flipped."_

The Copper / CEFFU integration is the **client's** responsibility (their account provisioning + key management), not
ours. We don't build the integration; if/when the client provisions Copper or CEFFU, we wire the existing UTL custody
adapter to their credentials — which is a config-only flip on `WalletProvisioningConfig.signing_surface` per
`/codex/04-architecture/custody-providers.md`. No standalone Phase 2 build required.

**Slot assignments (corrected)**:

- **Phase 1** → Ikenna slot 6 (Cloud-KMS withdrawal signing + deployment-api endpoint + 8 unit tests, ~3.2 cal days =
  hours)
- **Phase 2** → DESCOPED (client-side, no Ikenna/Harsh work needed; config flip only when credentials arrive)
- **Phase 3** → Ikenna slot 7 (GCS Object Versioning + 7-year retention lock + Cloud Audit Logs + 4 compliance tests,
  ~1.6 cal days = hours)

Phase 1 + Phase 3 are fully independent — touch different code paths — parallel across slots 6+7. ~4.8 cal AI-days
combined → ~hours calendar time at density-push pace (~100-200 cal AI-days/side/day).

**Rationale**: workspace remaining backlog ≈ 530 cal AI-days (corrected per Harsh audit slot TBD-backfill); combined
idle capacity ≈ 15 slots at ~5-7× compression; operator guidance "well over halfway to May-23 already"

- "100-200 AI-days per day" + "more to the 15th deadline".

---

# Wallet / Treasury — Post-Cutover Custody + Signing (June 1+)

**Deferred from May-23 cutover**: Operator decision 2026-05-13 to ship May-23 with stubs (button-click withdrawal
approval, Cloud-KMS-only signing). This plan executes the real integrations post-cutover.

---

## Design Decisions Acked (2026-05-13)

**From `wallet_treasury_client_flow_2026_05_10.md` design phase**:

- ✅ **Q1**: Slot 4 Phase 3.D `/api/treasury/rollup` ready by 2026-05-13 18:00 ✅
- ✅ **Q2**: Require backend Phase 6.A live before UI (safer sequencing) ✅
- ✅ **Q3**: **DEFERRED** — Simple button-click stub for May-23; real HMAC-signed approval chain post-cutover (THIS
  PLAN)
- ✅ **Q4**: Daily HWM crystallization confirmed ✅
- ✅ **Q5**: **DEFERRED** — Stubs for May-23; real Copper + CEFFU integration post-cutover (THIS PLAN)

---

## Scope: Q3 + Q5 Deferred Work

### Phase 1: Real Withdrawal Approval Chain (Q3 Fulfillment)

**What May-23 shipped**: Button-click withdrawal request → operator confirms → funds flow (no cryptographic signing).

**What this plan delivers**:

1. **UAC contracts** — Real `WithdrawalApprovalSignature` (HMAC-SHA256), `WithdrawalApprovalChain` (2-of-N multisig,
   M-of-N for large withdrawals)
2. **execution-service** — Wire `sign_withdrawal_approval()` using Cloud-KMS (May-23 path) + future Copper/Fireblocks
   (June-1+ path)
3. **deployment-api** — `/api/clients/{id}/withdrawal/{id}/approve` endpoint accepts signature + executes signed
   withdrawal
4. **Tests** — 8 unit tests (single-sig, 2-of-2, M-of-N multisig scenarios)

**Dependency**: Copper signing surface (operator-provisioned post-cutover; Cloud-KMS pre-Copper). This plan assumes
Cloud-KMS available; Copper path is June-15+ scope.

#### Phase 1 Implementation Todos

- [x] [SCRIPT] P0. 1.1 — UAC `WithdrawalApprovalSignature` (frozen dataclass, HMAC-SHA256 `create()`/`verify()`) +
      `WithdrawalApprovalChain` (mutable, N-of-M quorum) in `unified_api_contracts/internal/domain/treasury.py` + 9 unit
      tests in `tests/internal/unit/test_withdrawal_approval_signature.py` (unified-api-contracts@0fa2b59)
- [x] [SCRIPT] P0. 1.2 — `execution_service/custody/withdrawal_signing.py`: `sign_withdrawal_approval()` via Secret
      Manager lazy-cached HMAC key; GCP + AWS paths; `_injected_key` test seam (execution-service@b4fb55f); 5 unit tests
      via `_injected_key` seam (no Secret Manager calls) in `tests/unit/custody/test_withdrawal_signing.py`
      (execution-service@98ecfdf)
- [x] [SCRIPT] P0. 1.3 — `deployment_api/routes/client_treasury.py`:
      `POST /clients/{client_id}/withdrawal/{withdrawal_id}/approve` real HMAC chain endpoint +
      `WithdrawalApproveRequest`/`WithdrawalApproveResponse` models + `_WITHDRAWAL_CHAINS` in-memory store; integrates
      `_emit_cloud_audit_log()` from LDR; removes stub `post_client_treasury_withdraw` (deployment-api@4282d6a)
- [x] [SCRIPT] P0. 1.4 — 10 compliance tests in `tests/unit/test_treasury_compliance.py`: happy path, quorum
      accumulation, 404/400 validation, PB-1/PB-3 audit-log compliance (deployment-api@4282d6a)

**Phase 1 SHIPPED 2026-05-14 (ikenna slot 6)**.

---

### Phase 2: Real Custody Integrations (Q5 Fulfillment)

**What May-23 shipped**: Mocked Copper + CEFFU calls; real Cloud-KMS wallet operations only.

**What this plan delivers**:

1. **Copper integration** — DeFi wallet MPC signing (replace Cloud-KMS stub with real Copper calls for
   staking/lending/swapping)
2. **CEFFU integration** — CeFi account connectivity (venue credentials, withdrawal approvals, settlement)
3. **execution-service** — Real `CustodyPinger` for health checks; replace mock `CustodyEndpoint` responses with live
   pings
4. **Tests** — 6 integration tests (Copper staking, CEFFU withdrawal, cross-custody fallback scenarios)

**Dependency**: Operator-provided Copper API key + CEFFU institutional account. Wire-in assumes credentials provisioned
between May-23 and June-1.

---

### Phase 3: Compliance + Audit Log Immutability (Regulatory)

**What May-23 shipped**: Audit log in GCS (mutable PUT, no retention lock, no versioning).

**What this plan delivers** (PER PB-1/PB-3 audit findings):

1. **GCS Object Versioning** — Enable on audit bucket; immutable after write
2. **Retention Lock** — 7-year retention policy (regulatory requirement)
3. **CloudAudit** — Wire deployment-api withdrawal calls into Cloud Audit Logs (for compliance audits)
4. **Tests** — 4 compliance tests (lock enforcement, version history, audit log retrieval)

#### Phase 3 Implementation Todos

- [x] [SCRIPT] P0. 3.1 — GCS Object Versioning enabled on audit bucket via `--versioning` flag in
      `provision_audit_records_retention_lock.sh` (deployment-service@5f721ab)
- [x] [SCRIPT] P0. 3.2 — `_emit_cloud_audit_log()` helper + `POST /api/clients/{id}/treasury/withdraw` stub wired into
      `deployment_api/routes/client_treasury.py` with Cloud Audit Log emission (deployment-api@5cf2fa1)
- [x] [SCRIPT] P0. 3.3 — 4 compliance tests in `tests/unit/test_treasury_compliance.py`; 6/6 pass
      (deployment-api@5cf2fa1)

**Gate**: Pre-June-15 (compliance deadline for live trading). Links to `api_keys_wallets_accounts_readiness` Phase 8.D
pre-cutover gate.

---

## Phasing + Dependencies

| Phase                         | Owner                   | Dependency                                        | Milestone | Cal Days |
| ----------------------------- | ----------------------- | ------------------------------------------------- | --------- | -------- |
| 1 (Real withdrawal approval)  | deployment-api owner    | Cloud-KMS live (May-23 ✅)                        | June 3    | 3.2      |
| 2 (Real custody integrations) | execution-service owner | Copper + CEFFU provisioned (June-1 operator task) | June 10   | 4.8      |
| 3 (Audit log immutability)    | deployment-api owner    | GCS bucket ready (May-23)                         | June 12   | 1.6      |

**Total**: ~9.6 calibrated AI-days across 15-day post-cutover window.

---

## Success Criteria

✅ **Phase 1 complete** when:

- Real HMAC withdrawal approval wired end-to-end (API → Cloud-KMS signature → funds transfer)
- 8 unit tests pass
- QG checks pass (lint / basedpyright / import-patterns)

✅ **Phase 2 complete** when:

- Copper + CEFFU live calls in execution-service (no mocks)
- 6 integration tests pass against Copper testnet
- Real CustodyPinger returns live status

✅ **Phase 3 complete** when:

- GCS audit bucket has versioning + 7-year retention lock enabled
- Cloud Audit Logs linked
- 4 compliance tests pass

**Phase 3 SHIPPED 2026-05-14 (ikenna slot 7)**:

- `deployment-service@f0f2c83` — `scripts/infra/configure_audit_bucket_versioning.sh` (GCS versioning + 7-year retention
  lock; prod-only lock gate; idempotent)
- `deployment-api@df36ef4` — `tests/unit/test_audit_log_compliance.py` (10 tests / 10 pass: versioning assertion,
  retention lock 220752000s + isLocked, audit log emission via log_event, immutable append-only path pattern)

✅ **Successor unblocked**: Next operator decision (Fireblocks June-15+ for institutional custody).

---

## Cross-References

- **Predecessor plan**: `wallet_treasury_client_flow_2026_05_10.md` § "Design Decisions — Q3, Q5 Deferred"
- **Related audit findings**: `plans/active/issues/codex_audit_pb_*.md` (PB-1, PB-3)
- **Custody provisioning**: `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 8.D
- **Copper interface**: `/codex/04-architecture/interface-credential-convention.md` (DeFi execution path)
- **Master plan**: `master_to_live_defi_2026_05_23.md` Group G item 23 (operator UX for withdrawals)

---

## Notes

**Why deferred from May-23**: Operator risk appetite for cutover was real-money May-23 smoke with simple button
approvals + Cloud-KMS-only signing. Real Copper + CEFFU integrations (multi-sig, institutional custody) are valuable but
not critical for the 7-day live smoke test. Deferral allows 2-week hardening post-cutover before full
institutional-grade custody goes live.

**Handoff trigger**: May-23 cutover completion + 48-hour live smoke green. Operator signals go-ahead for Phase 1 (real
signing) once live traffic stabilizes.
