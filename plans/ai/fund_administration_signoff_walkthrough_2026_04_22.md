---
name: fund-administration-service — Phase 6 sign-off walkthrough
overview:
  45-minute structured walkthrough script for the Phase 6 UAT / business sign-off of the IM Pooled subscription +
  redemption rail. Use after Cloud Run staging deploy lands.
type: business
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-22
---

# Fund administration — sign-off walkthrough

**Plan SSOT:** `plans/active/fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md` Phase 6.

**Preconditions** (all must be green before the walkthrough starts):

1. fund-administration-service deployed to Cloud Run staging, health endpoint returning 200.
2. UAC on `staging` has the fund_administration types including `AllocatorCashAccountView` + `CashAccountMovement`.
3. client-reporting-api on `staging` has the allocator routes landed.
4. unified-trading-system-ui on `staging` has the `/services/im/funds/*` routes rendering under mock-mode AND real-mode.

**Walkthrough seats** (who):

- Iggy / product — driving the review
- Ops / compliance — sign-off on flow + regulated admin selection
- Engineering back-up — ready to capture gotchas, not driving

---

## Script — 45 minutes

### 1. Framing — 5 min

- Read aloud: "Today confirms the IM Pooled subscription / redemption rail. Crypto-only first pass. POD is the
  administrator. Clients see one portal, one flow, NAV-strike-driven settlement. TradFi Pooled needs a separate
  administrator (SS&C / Citco / Apex — TBD) and is out of today's scope."
- Screen-share: open `/codex/14-customer-journeys/shared-core/fund-administration-and-custody.md` §Decision table.
- Confirm custody model per path matches what sales is saying in briefings.

### 2. UI walkthrough — mock mode — 10 min

Open `https://staging.odum-research.com/services/im/funds/` (or the staging URL equivalent) with
`NEXT_PUBLIC_MOCK_API=true` in effect.

**Overview page** — confirm:

- [ ] Pending subscriptions count matches mock fixture (3 subs across PENDING / APPROVED / SETTLED)
- [ ] Pending redemptions count matches (2 reds PENDING + SETTLED)
- [ ] Share-class NAV card renders (mock value)
- [ ] Four sub-tab links (Subscriptions / Redemptions / Allocations / History) work

**Subscriptions page** — happy path:

- [ ] Open "New subscription" dialog
- [ ] Fill amount, currency, share-class → submit
- [ ] Toast success with subscription_id; new row appears PENDING
- [ ] Confirm the SUBSCRIPTION_REQUESTED lifecycle event posted to mock audit trail

**Redemptions page** — happy path:

- [ ] Open "New redemption" dialog; confirm grace-period notice reads "settlement at next NAV strike, typically 5
      business days"
- [ ] Submit → new PENDING row

**Allocations page** — treasury-health dashboard:

- [ ] Each share class gauge renders (reserve_pct vs current)
- [ ] Allocation-delta table populated per strategy
- [ ] "Rebalance" button visible to ops-role user (via `useIsOpsUser()` hook — `admin`/`internal` roles)

**History page** — per-allocator ledger:

- [ ] Allocator picker
- [ ] Cash-account view loads (current balance, YTD subs/reds, last settlement timestamp)
- [ ] Movements table sorted chronologically

### 3. REST API walkthrough — 10 min

In a terminal with staging platform API key:

```bash
# 1. Subscription round-trip
curl -X POST "$FAS_URL/subscriptions" -H "Authorization: Bearer $API_KEY" \
  -d '{"fund_id":"odum-alpha","allocator_id":"test-alloc","share_class":"USDC","requested_amount_usd":"100000"}'
# → 200 + subscription_id; SUBSCRIPTION_REQUESTED emitted

curl -X POST "$FAS_URL/subscriptions/$SUB_ID/approve" ...
# → 200; SUBSCRIPTION_APPROVED; units_issued populated from NAV strike stub

curl -X POST "$FAS_URL/subscriptions/$SUB_ID/settle" ...
# → 200; SUBSCRIPTION_SETTLED

# 2. Allocator view (entitlement-enforced)
curl "$CRA_URL/allocators/test-alloc/subscriptions" -H "Authorization: Bearer $ALLOC_KEY"
# → 200 with the SETTLED subscription

curl "$CRA_URL/allocators/test-alloc/cash-account?share_class=USDC" -H "Authorization: Bearer $ALLOC_KEY"
# → 200 with current_balance_usd + movements

# 3. Entitlement rejection
curl "$CRA_URL/allocators/OTHER-alloc/subscriptions" -H "Authorization: Bearer $ALLOC_KEY"
# → 403 (org_id mismatch)

# 4. Redemption happy path
curl -X POST "$FAS_URL/redemptions" ...
# → 200; REDEMPTION_REQUESTED

curl -X POST "$FAS_URL/redemptions/$RED_ID/approve" ... → REDEMPTION_APPROVED
curl -X POST "$FAS_URL/redemptions/$RED_ID/process" ... → REDEMPTION_PROCESSED
curl -X POST "$FAS_URL/redemptions/$RED_ID/settle" ... → REDEMPTION_SETTLED
```

Checklist:

- [ ] All 10 lifecycle events fire in order
- [ ] Entitlement returns 403 for cross-client reads
- [ ] Event payloads include fund_id, share_class, allocator_id correctly
- [ ] Health endpoint (`/healthz`) returns 200

### 4. Custody + regulated-admin posture — 10 min

- [ ] Confirm with compliance: crypto engagements go through POD as administrator, assets at Copper custodian.
- [ ] Confirm the TradFi-admin selection is a named follow-up — NOT in today's scope. Walk the follow-up plan
      (`plans/active/tradfi_fund_administrator_selection_2026_04_22.md`).
- [ ] Confirm public-copy rules are being respected — "POD" never on public surfaces; Copper can be named.
- [ ] Walk the briefing copy live at `https://odum-research.com/briefings/investment-management` — confirm the Pooled
      section reads correctly (custodian named; administrator described generically).

### 5. Open-defect + sign-off — 10 min

- [ ] Capture any defects found above into the plan's Phase-7 defect-fix section.
- [ ] Explicit sign-off on:
  - Subscription flow reads correctly for an IM Pooled allocator
  - Redemption grace-period framing matches the commercial model
  - Treasury-health dashboard is useful to ops
  - Codex + briefings are internally consistent with shipped behaviour
  - POD scoped to crypto only; TradFi admin is a named follow-up, not a gap.
- [ ] B6 business sign-off recorded in the plan's `repo_gates` table for fund-administration-service.

---

## Post-walkthrough

1. Close the Phase 6 item in the parent plan.
2. Open whichever follow-up plans the walkthrough flagged.
3. Share the recording / decisions summary with the wider team.

## URLs (fill in once staging lands)

- fund-administration-service health: `TBD`
- UI `/services/im/funds/`: `TBD`
- client-reporting-api allocator routes: `TBD`
- Staging Cloud Build trigger: `https://console.cloud.google.com/cloud-build/triggers?project=central-element-323112`
- Artifact Registry:
  `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-system/fund-administration-service`

## Reference

- `plans/active/fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md` — parent plan
- `/codex/14-customer-journeys/shared-core/fund-administration-and-custody.md` — custody SSOT
- `/codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md` — subscription / redemption mechanic
