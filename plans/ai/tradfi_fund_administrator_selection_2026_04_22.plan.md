---
name: TradFi Pooled fund — administrator selection + integration scoping
overview:
  POD administers Odum's crypto-denominated Pooled funds. For **TradFi-denominated** Pooled funds we need a separate
  regulated fund administrator. This plan scopes the selection (SS&C, Citco, Apex, Bolder, or another) and captures the
  integration contract once a preferred partner is selected. Prerequisite for any TradFi-Pooled client engagement.
type: business
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-22

completion_gates:
  business: B6

repo_gates:
  - repo: unified-trading-pm
    code: C0
    deployment: none

depends_on:
  - fund_administration_service_and_pooled_subscription_redemption_2026_04_20.plan.md
---

# Context

The 2026-04-22 POD clarification: POD is crypto-only. TradFi-denominated pooled funds (equities, futures, fixed-income,
commodities) need a different regulated fund administrator. No selection has been made yet.

The `fund-administration-service` repo currently has one integration surface (targetting POD). Once a TradFi
administrator is selected, we either:

- **Option A** — extend the existing `fund-administration-service` with a per-administrator dispatch (POD for crypto
  share classes, $TRADFI_ADMIN for TradFi share classes). Fund admin is determined from the share-class's asset-class
  metadata.
- **Option B** — stand up a sibling service `fund-administration-service-tradfi` with a separate deployment target and a
  shared UAC contract surface.

Option A is cleaner for the platform; Option B is cleaner if administrator-specific compliance (SOC2 boundary,
regulatory jurisdiction) means we can't co-locate integrations.

# Scope (business-first, code second)

## Stage 1 — selection (operator + compliance)

- [ ] Shortlist 3-4 fund administrators with trading-strategy / quant-fund experience — candidates:
  - SS&C GlobeOp (largest, has crypto-adjacent practice)
  - Citco (premium, traditional hedge fund focus)
  - Apex Group (mid-market, flexible)
  - Bolder Group (smaller, Cayman/BVI-focused)
  - Others at operator's discretion.
- [ ] RFP / discovery calls. Capture: fee model, minimum AUM, supported jurisdictions, API / file-drop integration
      modes, SLA, reference clients.
- [ ] Decision note in `/codex/14-playbooks/commercial-model/tradfi-fund-administrator-selection.md` (internal-only)
      recording selection + rationale.

## Stage 2 — integration scoping

- [ ] Once selected, obtain integration spec (similar to the POD plan).
- [ ] Decide Option A vs B (single-service dispatch vs sibling service). Capture decision.
- [ ] Estimate engineering cost for each option.
- [ ] Write the implementation plan `plans/active/tradfi_administrator_integration_<selected>_2026_MM_DD.plan.md`
      similar to the POD plan.

## Stage 3 — execution

Out of this plan's scope — lands in the implementation plan from Stage 2.

# Out of scope

- Crypto fund administrator — POD is locked (see `pod_crypto_administrator_integration_2026_04_22.plan.md`).
- TradFi SMA or DART — those paths don't need a fund administrator (clients hold their own venue accounts).

# Gate

Business sign-off (B6) gated on administrator selected + contract engagement letter signed.
