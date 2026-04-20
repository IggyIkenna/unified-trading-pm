---
scope: [admin, sales, engineer]
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
permissions — Copper for crypto, equivalent regulated custody banks for TradFi, wallet-based custody solutions for
on-chain. POD is the fund administrator running NAV accounting and the subscription / redemption rail. Odum Research Ltd
is the investment manager and the client-facing product surface.

## Which commercial paths use this model

| Path                 | Uses this mechanic? | Custody                                     | Capital-movement rail                    |
| -------------------- | ------------------- | ------------------------------------------- | ---------------------------------------- |
| IM — Pooled (Fund)   | YES                 | Qualified 3rd-party custodian (Copper etc.) | Portal subscription / redemption via POD |
| IM — SMA             | NO                  | Client-owned venue accounts                 | Client funds venue directly              |
| DART — Signals-In    | NO                  | Client-owned venue accounts                 | Client funds venue directly              |
| DART — Full Pipeline | NO                  | Client-owned venue accounts                 | Client funds venue directly              |
| Regulatory Umbrella  | NO                  | Client-owned venue accounts                 | Client funds venue directly              |
| Odum Signals-Out     | N/A                 | Counterparty (their own stack)              | N/A                                      |

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

## Contract surface (to be built — Pooled scope only)

The Pooled subscription / redemption mechanic needs the following UAC contracts. As of 2026-04-20 these are NOT yet in
UAC. Implementation plan lives in `plans/active/` (see follow-ups).

- **Domain types** (`unified_api_contracts.fund_administration`):
  - `ShareClass` — share_class_id, fund_id, isin, currency, mgmt_fee, perf_fee, current_nav
  - `AllocatorSubscription` — subscription_id, client_id, share_class_id, amount, currency, state, requested_at,
    settled_at
  - `AllocatorRedemption` — redemption_id, client_id, share_class_id, units_or_notional, destination, state,
    requested_at, settled_at
  - `NavSnapshot` — fund_id, share_class_id, as_of, nav_per_unit, aum
- **Events** (in UTL `STANDARD_LIFECYCLE_EVENTS`):
  - `SUBSCRIPTION_REQUESTED`
  - `SUBSCRIPTION_APPROVED` / `SUBSCRIPTION_REJECTED`
  - `SUBSCRIPTION_SETTLED`
  - `REDEMPTION_REQUESTED`
  - `REDEMPTION_APPROVED` / `REDEMPTION_REJECTED`
  - `REDEMPTION_PROCESSED` / `REDEMPTION_SETTLED`
- **Service**: `fund-administration-service` (new, in the SaaS tier). Acts as the integration boundary between the Odum
  portal and POD's fund-administration systems. Owns subscription / redemption state machine from the client's
  perspective; delegates AML / KYC / custody orchestration to POD.

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
- [ ] Write the implementation plan `plans/active/pooled-fund-subscription-redemption-service_2026_04_20.plan.md`
      covering: UAC contracts, `fund-administration-service` scaffolding, platform UI subscription / redemption pages,
      POD integration boundary, event / webhook surface.
- [ ] Platform UI: scaffold `app/(platform)/services/im/funds/` with subscription, redemption, and ledger pages using
      mock data until `fund-administration-service` is available.
