---
title: "Wallet / Treasury — Post-Cutover Custody + Signing (June 1+)"
created: 2026-05-13
type: plan
status: pending-gate
deadline: 2026-06-15
horizon: 15-day post-cutover sprint
predecessor: wallet_treasury_client_flow_2026_05_10.md (deferred Q3 + Q5 from design decisions 2026-05-13)
companion_to: master_to_live_defi_2026_05_23.md Group G (post-cutover operator UX + compliance)
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: infra
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 9.6
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

✅ **Successor unblocked**: Next operator decision (Fireblocks June-15+ for institutional custody).

---

## Cross-References

- **Predecessor plan**: `wallet_treasury_client_flow_2026_05_10.md` § "Design Decisions — Q3, Q5 Deferred"
- **Related audit findings**: `plans/active/issues/codex_audit_pb_*.md` (PB-1, PB-3)
- **Custody provisioning**: `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 8.D
- **Copper interface**: `codex/04-architecture/interface-credential-convention.md` (DeFi execution path)
- **Master plan**: `master_to_live_defi_2026_05_23.md` Group G item 23 (operator UX for withdrawals)

---

## Notes

**Why deferred from May-23**: Operator risk appetite for cutover was real-money May-23 smoke with simple button
approvals + Cloud-KMS-only signing. Real Copper + CEFFU integrations (multi-sig, institutional custody) are valuable but
not critical for the 7-day live smoke test. Deferral allows 2-week hardening post-cutover before full
institutional-grade custody goes live.

**Handoff trigger**: May-23 cutover completion + 48-hour live smoke green. Operator signals go-ahead for Phase 1 (real
signing) once live traffic stabilizes.
