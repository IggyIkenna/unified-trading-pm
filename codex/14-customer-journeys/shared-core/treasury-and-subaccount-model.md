---
doc_type: codex-ssot
title: Pooled fund subscription / redemption mechanic — portal surface
summary:
  IM-Pooled-only subscription/redemption portal mechanic — client subs/redeems via UI or REST against
  fund-administration-service, POD runs AML/KYC + NAV-strike gates, qualified 3rd-party custodian holds assets.
  Invariant — client capital never commingles with Odum operating funds. Enumerates the shipped UAC types, 10 lifecycle
  events, and service/UI routes.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [client-reporting-api, execution-service, fund-administration-service, unified-trading-pm, unified-trading-system-ui]
scope: [admin, sales, engineer]
tags: [custody, uac, execution, reporting, ui, sales]
related:
  [
    /codex/14-customer-journeys/shared-core/fund-administration-and-custody.md,
    /codex/14-customer-journeys/shared-core/org-fund-client-entity-model.md,
    ../experience/im-decision-journey.md,
  ]
created: 2026-04-20
authoritative_for: [pooled fund subscription/redemption portal mechanic]
referenced_by: [/codex/14-customer-journeys/shared-core/fund-administration-and-custody.md]
owner:
last_reviewed:
code_refs:
visibility: internal-only
---

# Pooled fund subscription / redemption mechanic — portal surface

> Internal-only. Qualified custodian names (Copper, Fireblocks, regulated TradFi custody banks) MAY appear on public
> surfaces as selling points; POD (the fund administrator) stays internal per
> [fund-administration-and-custody.md](./fund-administration-and-custody.md).
>
> **Scope note**: this mechanic applies to **IM Pooled only**. SMA + DART clients hold their own venue accounts in their
> own entity name — see the custody decision table in the parent custody doc. Do not apply treasury / sub-account
> mechanics to SMA or DART public copy.

## Invariant

**Client capital never commingles with Odum Research Ltd's operating funds. Odum Research Ltd (the investment manager)
never holds principal.**

The Pooled fund's assets sit with a **qualified third-party custodian** under that custodian's own regulatory
permissions — Copper (primary reference) for crypto, Fireblocks / BitGo as crypto alternatives; qualified TradFi custody
banks (prime broker / regulated bank, TBD per mandate) for TradFi-denominated funds. The **fund administrator** is
asset-class-specific: **POD is the crypto-only administrator** (the first and currently only integration); TradFi Pooled
funds require a separate regulated fund-admin firm (SS&C / Citco / Apex / equivalent — TBD per mandate). Odum Research
Ltd is the investment manager and the client-facing product surface in every case.

## Which commercial paths use this model

| Path                 | Uses this mechanic? | Custody                                     | Capital-movement rail                    |
| -------------------- | ------------------- | ------------------------------------------- | ---------------------------------------- |
| IM — Pooled (Fund)   | YES                 | Qualified 3rd-party custodian (Copper etc.) | Portal subscription / redemption via POD |
| IM — SMA             | NO                  | Client-owned venue accounts                 | Client funds venue directly              |
| DART — Signals-In    | NO                  | Client-owned venue accounts                 | Client funds venue directly              |
| DART — Full Pipeline | NO                  | Client-owned venue accounts                 | Client funds venue directly              |
| Regulatory Umbrella  | NO                  | Client-owned venue accounts                 | Client funds venue directly              |
| Odum Signals         | N/A                 | Counterparty (their own stack)              | N/A                                      |

## Structure — how Pooled custody and administration compose

```
Fund vehicle (legal entity — UCITS / Cayman SPC / BVI SPC / LuxSIF / etc.)
│
├── Assets held by qualified 3rd-party custodian (e.g. Copper for crypto)
│       ├── Custodian operates under their own regulatory permissions
│       ├── Custodian provides execution interfaces to the fund administrator
│       └── Custodian's books track fund holdings at venue level
│
├── NAV + subscriptions + redemptions administered by POD (fund administrator)
│       ├── Per-client share class accounting (per-investor NAV attribution)
│       ├── Subscription request lifecycle (requested → subscribed → settled)
│       ├── Redemption request lifecycle (requested → approved → settled)
│       └── AML / KYC on investors at onboarding + refresh
│
├── Investment management by Odum Research Ltd (FCA 975797)
│       ├── Strategy selection, allocation, risk, execution
│       ├── Credentials to execute on custodian-held assets provisioned by POD
│       └── Never holds principal
│
└── Client-facing surface: Odum portal
        ├── Share-class NAV + P&L attribution per allocator
        ├── Subscription / redemption request UI
        └── Same surface exposed as REST API for allocators who script flows
```

## Subscription flow

```
Client → client dashboard (UI) or REST API → subscription request
        │  (SUBSCRIPTION_REQUESTED emitted, includes amount, currency, share-class)
        ▼
POD (fund administrator) runs AML / KYC refresh + subscription gate
        │  (SUBSCRIPTION_APPROVED or _REJECTED)
        ▼
Client wires / transfers funds to custodian per POD's instructions
        │  (custodian confirms receipt; POD credits at next NAV strike)
        ▼
Share class issued to client at the published NAV point
        │  (SUBSCRIPTION_SETTLED with share-class units + NAV per unit)
        ▼
Position attribution visible in client portal from next reporting cycle
```

## Redemption flow

```
Client → client dashboard (UI) or REST API → redemption request
        │  (REDEMPTION_REQUESTED, includes units or notional, destination bank / wallet)
        ▼
POD runs liquidity, AML, and mandate gates (lock-up, notice period, gate limits)
        │  (REDEMPTION_APPROVED or _REJECTED)
        ▼
Custodian liquidates / unwinds proportional share at next NAV strike
        │  (REDEMPTION_PROCESSED at custodian)
        ▼
Proceeds wired to client's declared destination by POD
        │  (REDEMPTION_SETTLED with final NAV, units redeemed, proceeds)
        ▼
Client portal ledger updated
```

## Automation surface — Odum portal

- **UI**: Under `/services/im/` or `/services/funds/` on the platform UI. Pages: share-class NAV + attribution,
  subscription request form, redemption request form, history ledger with state per request, AML / KYC refresh prompts
  at renewal.
- **REST API**: `POST /funds/subscriptions`, `POST /funds/redemptions`, `GET /funds/balances`, `GET /funds/history`.
  Authenticated via the allocator's platform API key (issued at onboarding). Webhook callbacks on state transitions.
- **Both UI and API drive the same underlying fund-administration-service bridge to POD** — one source of truth for
  subscription / redemption state.

## Contract surface (shipped 2026-04-20 — Pooled scope only)

Phase 0–4 landed on `live-defi-rollout`; Phase 5 docs + Phase 6 staging deploy pending per
[fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md](../../../plans/archive/fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md).

- **Domain types** — `from unified_api_contracts.fund_administration import ...` (public facade; also re-exported
  top-level from `unified_api_contracts`). Internal canonical definitions live under
  `unified_api_contracts/internal/domain/fund_administration/`.
  - `AllocatorSubscription` — subscription_id, fund_id, allocator_id, share_class, requested_amount_usd,
    requested_timestamp, status (SubscriptionStatus), nav_strike_snapshot_id, units_issued, approval_timestamp,
    rejection_reason.
  - `AllocatorRedemption` — redemption_id, fund_id, allocator_id, share_class, units_to_redeem, destination,
    requested_timestamp, status (RedemptionStatus), grace_period_days, redemption_nav_snapshot_id, cash_amount_due_usd,
    settlement_timestamp, settlement_reference, rejection_reason.
  - `FundAllocation` — allocation_id, fund_id, share_class, strategy_id, target_amount_usd, allocation_timestamp,
    execution_status (AllocationExecutionStatus), executed_amount_usd, executed_timestamp.
  - `AllocatorCashAccountView` + `CashAccountMovement` — derived reporting projection consumed by client-reporting-api +
    platform UI history page.
  - Enums: `SubscriptionStatus` (PENDING / APPROVED / REJECTED / SETTLED), `RedemptionStatus` (PENDING / APPROVED /
    REJECTED / PROCESSED / SETTLED), `AllocationExecutionStatus` (PENDING / IN_PROGRESS / COMPLETED / FAILED).
  - FastAPI request bodies (also in UAC so request-body schemas stay single-source): `SubscribeRequest`,
    `RedeemRequest`, `ApproveSubscriptionRequest`, `ProcessRedemptionRequest`, `RejectRequest`, `RebalanceRequest`.
  - NAV snapshots reuse existing `unified_api_contracts.internal.domain.client_reporting.FundNAVSnapshot`.
- **Events** — registered in `unified_trading_library.events.STANDARD_LIFECYCLE_EVENTS` (grouping set
  `FUND_ADMINISTRATION_EVENT_TYPES`, payload-type map `FUND_ADMINISTRATION_EVENT_PAYLOAD_TYPES`):
  - `SUBSCRIPTION_REQUESTED` / `SUBSCRIPTION_APPROVED` / `SUBSCRIPTION_REJECTED` / `SUBSCRIPTION_SETTLED`
  - `REDEMPTION_REQUESTED` / `REDEMPTION_APPROVED` / `REDEMPTION_REJECTED` / `REDEMPTION_PROCESSED` /
    `REDEMPTION_SETTLED`
  - `FUND_ALLOCATION_REBALANCED`
- **Service**: `fund-administration-service` (SaaS tier, tier 3, registered in `workspace-manifest.json`). REST routes:
  `POST /subscriptions`, `GET /subscriptions/{id}`, `POST /subscriptions/{id}/approve|reject|settle`,
  `POST /redemptions`, `GET /redemptions/{id}`, `POST /redemptions/{id}/approve|reject|process|settle`,
  `GET /funds/{fund_id}/allocations`, `POST /funds/{fund_id}/allocations/rebalance`, `GET /funds/{fund_id}/nav/history`.
  Subscription + redemption state machines are pure functions; `CapitalRouter` drives TransferAdapter transfers tagged
  with `FundTransferContext(fund_id, share_class, allocation_id)`. Background tasks handle grace-period expiry +
  NAV-strike scheduling. In-memory persistence store is the local-dev default; SQL / Firestore swap-in is a follow-up.
  Service emits the 10 lifecycle events above via `emit_fund_admin_event` helper wrapping UTL `log_event`.
- **Platform UI** — `unified-trading-system-ui` routes under `app/(platform)/services/im/funds/`: `/` (overview),
  `/subscriptions`, `/redemptions`, `/allocations` (treasury-health dashboard + rebalance for ops), `/history`
  (per-allocator cash-account ledger). Mock mode (`NEXT_PUBLIC_MOCK_API=true`) drives an in-memory fixture store for
  local dev. Typed REST client at `lib/api/fund-administration.ts`.
- **Client-reporting API** — `client-reporting-api` routes: `GET /allocators/{client_id}/subscriptions`,
  `GET /allocators/{client_id}/redemptions`, `GET /allocators/{client_id}/cash-account`. Entitlement enforced via
  `_enforce_entitlement(auth, client_id)` — external callers must match `auth.org_id`, internal callers bypass.
- **TransferAdapter routing** — `execution-service` `TransferAdapter.execute_internal_transfer` / `execute_withdrawal` /
  `execute_onchain_transfer` accept optional `fund_context: FundTransferContext | None`. `FundTransferContext` is
  currently a local dataclass in execution-service
  - a structural mirror in fund-administration-service (follow-up: promote to UAC `fund_administration` facade to
    eliminate the mirror).
- **TreasuryMonitor** — `position-balance-monitor-service` `TreasuryConfig` has optional `target_allocations`,
  `share_class`, `fund_id` fields. `TreasurySnapshot` now surfaces `allocation_deltas` per strategy when targets are
  set; `TREASURY_LOW` / `TREASURY_HIGH` events carry fund_id context.

## Public-copy rules (Pooled mechanic)

| Surface                                             | Allowed phrasing                                                                                                                                                                                                                                                                                                                               | Forbidden                                                                                                                                        |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/briefings/investment-management` (Pooled section) | "Fund assets at a qualified third-party custodian (Copper for crypto; equivalent regulated custodians for other asset classes); regulated fund administrator handles NAV, subscriptions, redemptions; subscriptions + redemptions automated via Odum portal (UI + API)"; "Odum Research Ltd is the investment manager — never holds principal" | "POD" (the administrator entity); "Odum-held sub-account" (wrong framing — the sub-account is the share class at POD, not an Odum-held position) |
| `/briefings/dart-*` + `/briefings/regulatory`       | None of this mechanic applies — SMA / DART / Reg Umbrella clients hold their own venue accounts                                                                                                                                                                                                                                                | Treasury wallet language; sub-account-inside-Odum language                                                                                       |
| Platform UI `/services/im/` or `/services/funds/`   | Subscription + redemption; share-class NAV; history ledger                                                                                                                                                                                                                                                                                     | —                                                                                                                                                |

## Related docs

- [fund-administration-and-custody.md](./fund-administration-and-custody.md) — the parent custody rule. Custody model
  per path.
- [org-fund-client-entity-model.md](./org-fund-client-entity-model.md) — four-level entity hierarchy (org → fund →
  client → position slice).
- [../experience/im-decision-journey.md](../experience/im-decision-journey.md) — pb2a IM briefing.

## Follow-ups

- [ ] Name the specific qualified custodians per asset class with compliance review. Copper (crypto) is the reference;
      TradFi and on-chain custodians to be confirmed.
- [x] Write the implementation plan — shipped as
      [fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md](../../../plans/archive/fund_administration_service_and_pooled_subscription_redemption_2026_04_20.md).
- [x] Platform UI: scaffold `app/(platform)/services/im/funds/` with subscription, redemption, and ledger pages using
      mock data until `fund-administration-service` is available.
- [ ] **Promote `FundTransferContext` to UAC** — currently a local dataclass in
      `execution-service/execution_service/engine/transfers/adapter.py` + a structural mirror tagged
      `SCHEMA_PROVENANCE_EXEMPT` in
      `fund-administration-service/fund_administration_service/allocation/transfer_protocol.py`. Move to
      `unified_api_contracts/fund_administration.py` so both services share one definition. Small, blast-radius ~2
      repos.
- [ ] **Existing reporting-api entitlement gap** — `client-reporting-api` routes (`reporting/settlements.py`,
      `reporting/trades.py`, etc.) trust the `client_id` query param blindly. Only the new allocator routes
      (`allocators.py`) enforce `_enforce_entitlement(auth, client_id)`. Backfill the entitlement check on the existing
      reporting routes.
- [ ] **Persistence swap-in** — `fund-administration-service` currently uses an in-memory `PersistenceStore` for local
      dev. Ship SQL / Firestore impl as a follow-up, with migration story from the in-memory default.
- [ ] **Real POD integration** — subscription approval AML/KYC gate + NAV strike resolution currently stub through mock
      providers. Wire the real POD fund-administration API once POD's endpoints are confirmed.
- [ ] **fund-administration-service GitHub repo creation + staging deploy** — local-only until Phase 6.
      `gh repo create IggyIkenna/fund-administration-service --private --source ./fund-administration-service`, push
      `live-defi-rollout`, propagate PM workflow templates via
      `bash unified-trading-pm/scripts/propagation/rollout-workflow-templates.sh`, then deploy to staging Cloud Run.
