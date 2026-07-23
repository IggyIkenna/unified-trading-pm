---
doc_type: codex-ssot
title: Fund administration and custody — Odum-never-custodies rule + POD affiliate
summary:
  Hard invariant — Odum Research Ltd (the investment manager) never custodies client capital in any structure. Per-path
  custody model — Pooled uses a qualified 3rd-party custodian (Copper crypto / TradFi bank) + asset-class-specific fund
  admin (POD crypto-only, internal-only on public copy); SMA/DART/Reg-Umbrella use client-owned venue accounts + scoped
  execute+read keys.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, fund-administration-service]
scope: [admin, sales]
tags: [custody, cefi, tradfi, defi, sales, execution]
related:
  [
    /codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md,
    /codex/14-customer-journeys/shared-core/org-fund-client-entity-model.md,
    ../experience/im-decision-journey.md,
    ../../06-coding-standards/config-reloader-pattern.md,
  ]
created: 2026-04-20
authoritative_for: [Odum-never-custodies invariant + per-commercial-path fund-admin/custody model]
referenced_by:
  [
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/shared-core/treasury-and-subaccount-model.md,
  ]
owner:
last_reviewed:
code_refs:
visibility: internal-only
---

# Fund administration and custody — Odum-never-custodies rule + POD affiliate

> Internal-only. The POD affiliate is NOT named on any public-facing surface (briefings, marketing pages, decks for
> prospects). Public copy says "regulated affiliate" or "fund administrator"; sales leadership names POD only in
> bilateral conversations with prospects on the way to mandate. Qualified third-party custodians (Copper, equivalents)
> MAY be named on public surfaces — that is a selling point, not a competitive disclosure.

## Invariant

**Odum Research Ltd (the investment manager / trading entity) never custodies client capital — in any structure.**

This is a hard invariant, not a feature per structure. Confusion historically arose because public surfaces framed SMA
as "you keep custody" and left Fund structure unclear — making it sound like Fund = Odum-custodies. Not true. Fund
custody is handled by a **qualified third-party custodian** (Copper for crypto; equivalent regulated custody banks for
TradFi) under their own regulatory permissions. The **fund administrator** (NAV accounting, subscription / redemption
processing, investor AML/KYC) is asset-class-specific:

- **Crypto-denominated funds** — POD (the regulated affiliate of Odum). POD is crypto-only; it does **not** administer
  TradFi-denominated funds.
- **TradFi-denominated funds** — a separate regulated fund administrator (SS&C / Citco / Apex / equivalent, to be
  selected per mandate). TBD per engagement.
- **Mixed / multi-asset funds** — structure depends on dominant asset class; typically one administrator per sub-fund
  rather than mixing within a single vehicle.

Odum Research Ltd is the investment manager only in every case.

## Custody model per path

| Path                             | Who holds the venue account / fund assets                                                                                                                                                                                                                    | How capital moves                                                                                             |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| IM — Pooled (Fund, crypto-denom) | Qualified 3rd-party custodian (Copper / equivalent) holds fund assets; **POD** is fund administrator (crypto-only)                                                                                                                                           | Client subscribes / redeems via Odum portal (UI + REST API)                                                   |
| IM — Pooled (Fund, TradFi-denom) | Qualified 3rd-party TradFi custody bank (prime broker / regulated custodian) holds fund assets; separate regulated fund administrator (SS&C / Citco / Apex / equivalent, TBD per mandate)                                                                    | Client subscribes / redeems via Odum portal (UI + REST API)                                                   |
| IM — SMA                         | Client, in their own entity name                                                                                                                                                                                                                             | Client funds the venue directly; Odum has scoped execute+read API keys                                        |
| DART — Signals-In                | **Default**: segregated sub-account inside Odum's venue accounts, held in the client's name via the exchange sub-account primitive (fast onboarding, avoids multi-week direct exchange onboarding). **Opt-out**: client's own venue or prime-broker account. | Client funds their sub-account (or own account) directly; Odum holds scoped execute+read API keys either way. |
| DART — Full Pipeline             | Same dual option as Signals-In                                                                                                                                                                                                                               | Same as Signals-In                                                                                            |
| Regulatory Umbrella              | Client, in their own entity name                                                                                                                                                                                                                             | Client funds direct; Odum has read-only+read-transaction keys only                                            |
| Odum Signals                     | Counterparty (their own stack)                                                                                                                                                                                                                               | N/A — Odum sees no fills, no positions, no venues                                                             |

## Structures and how custody works in each

### IM — SMA (Separately Managed Account)

- Client holds their own venue account(s) in their own entity name, funded directly with the venue.
- Client issues Odum a scoped API key with **execute + read** permissions only — no withdrawal authority, ever.
- Key lives in Odum's Secret Manager, hot-reloaded into `execution-service` at runtime via `ApiKeyReloader`
  ([config-reloader-pattern.md](../../06-coding-standards/config-reloader-pattern.md)).
- Client can revoke the key at any time; execution on that venue stops inside the key's next reload cycle (seconds).
  Capital stays with the client throughout.
- Applies to CeFi, DeFi (wallet keys equivalent), and TradFi brokerage keys.

### IM — Pooled (Fund) — asset-class-specific administrator + 3rd-party custodian

Same mechanic, two asset-class tracks:

**Crypto-denominated pooled funds** (primary engagement as of 2026-04):

- Assets at a qualified crypto custodian (Copper the reference; Fireblocks / BitGo / equivalent as alternatives).
- **POD** is the fund administrator — crypto-only. POD handles NAV accounting, subscription / redemption processing, and
  investor AML/KYC.
- This is the track the `fund-administration-service` repo integrates against in Phase 6+.

**TradFi-denominated pooled funds** (post-cutover engagement — not yet live):

> **[DELTA 2026-05-22]** **Current state:** TradFi-denominated pooled fund structures are not live. May-23 cutover ships
> crypto-only pooled fund support (Copper custody + POD administration). TradFi pooled fund structure (SS&C / Citco /
> Apex fund admin + TradFi prime-broker custody) is a future mandate shape — no engagement is currently scoped.
> **Planned delta:** TradFi pooled fund onboarding is driven by the first TradFi IM mandate; fund admin and custodian
> selection happens at that engagement. **Target:** post-cutover, tied to CME S&P co-invest mandate (Sept 2026) or
> equivalent TradFi Pooled engagement.

- Assets at a qualified TradFi custody bank (prime broker / regulated custodian — specific entity TBD per mandate).
- Fund administrator is a traditional regulated fund-admin firm (SS&C / Citco / Apex / equivalent — TBD per mandate).
  **Not POD.** Selecting the TradFi administrator is an onboarding step once the first TradFi-Pooled mandate is scoped.

**Common to both tracks:**

- The custodian holds assets under their own regulatory permissions.
- Odum Research Ltd is the investment manager (FCA 975797). Odum Research Ltd never holds principal, never touches
  client capital, and does not have custodial permissions.
- Trading credentials: Odum operates strategies via execute+read API keys that the fund administrator provisions against
  the custodian's execution interfaces — mirroring the SMA mechanic from Odum's side, with the administrator as the
  counterparty instead of the end-client.
- Clients see share-class NAV and position attribution via the Odum portal (entitlement-filtered). Subscriptions and
  redemptions submit through the portal — automated via the client dashboard UI and via REST API. Every state transition
  (subscription requested, subscribed, redemption requested, redeemed, settled) is a lifecycle event visible to the
  client and to ops.
- Why this matters to sales positioning: the offering supports pooled vehicles, share classes, regulated wrappers, and
  cross-border structures with a qualified custodian and a regulated fund administrator — standard
  regulated-fund-manager architecture, not a bespoke custody scheme.

### DART — Signals-In and Full Pipeline

Two execution-account options resolve at onboarding per DART engagement:

**Default — segregated sub-account at Odum's venue accounts (fast onboarding).** Odum maintains master venue accounts
across CeFi exchanges, TradFi brokers, and on-chain wallets. Each DART client is issued a native exchange sub-account /
sub-wallet within those master accounts, held in the client's own name at the exchange's sub-account primitive (Binance
sub-account, Hyperliquid sub-wallet, TradFi brokerage sub-account, wallet-per-client on-chain). This skips the
multi-week direct exchange onboarding every new venue otherwise requires. Odum operates via scoped execute+read API keys
kept in Secret Manager — no withdrawal authority, ever. Odum Research Ltd never holds principal.

**Opt-out — client's own venue or prime-broker account.** If the client already holds (or prefers to hold) the venue
relationship directly, they issue Odum the same scoped execute+read API keys against their own account. Same trading
loop, same Secret Manager, same no-withdrawal-authority posture; just a different account owner on the exchange's books.

- Instruction routing: the 8-field instruction schema carries a `client_id`; `execution-service` routes the order to the
  correct sub-account / account via the scoped key. Sub-mandate partitioning (one DART engagement with N internal
  sub-clients) uses further per-sub-mandate sub-accounts under the same mechanic.
- If a DART client later wants a fund wrapper (share-class mechanics, third-party custody, regulated administrator) that
  pivots to IM Pooled mechanics; it is a separate commercial engagement, not a DART feature.

### Regulatory Umbrella — client-owned venue accounts

- Reg Umbrella client operates their own regulated activity under Odum's FCA permissions. Capital sits on the client's
  own venue accounts (which the client holds directly or via their own fund administrator).
- Odum receives **read-only + read-transaction** venue API keys for reporting and supervisory purposes. Odum never
  executes on Reg Umbrella client venues and never touches capital.
- The regulatory overlay (MLRO, compliance monitoring, transaction reporting, best-execution evidence) runs through
  Odum; the custody overlay stays with the client.
- See [../experience/regulatory-umbrella-briefing.md](../experience/regulatory-umbrella-briefing.md).

## Why POD is internal-only on public surfaces

- POD branding is separate from Odum Research branding. Public UI is Odum Research; POD operates in the background.
- Naming POD on marketing pages adds a character with no narrative payoff for the prospect at pre-commitment stage. They
  care about the custody mechanic and the custodian (Copper or equivalent), not the entity that operates NAV accounting.
- The second call surfaces POD by name when structure selection turns operational.

## Public-copy rules

| Surface                                                            | Allowed phrasing                                                                                                                                                                                                                                                                                                                                                    | Forbidden                                                                                                    |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `/investment-management`, `/strategies.html`, homepage             | "Pooled: fund assets at a qualified third-party custodian such as Copper, regulated fund administrator, subscriptions and redemptions via Odum portal (API + UI)"; "SMA: you hold your own venue accounts in your own entity name, scoped execute+read keys to Odum, no withdrawal authority"; "Odum Research Ltd — the investment manager — never holds principal" | "POD"; "Odum holds the account"; conflating Pooled and SMA mechanics                                         |
| `/briefings/investment-management`                                 | Same as above; may say "fund administrator" or "regulated administrator"                                                                                                                                                                                                                                                                                            | "POD"; legal-entity names for the administrator beyond "fund administrator"                                  |
| `/briefings/dart-signals-in`, `/briefings/dart-full`, DART landing | "You hold your own venue accounts in your own entity name; Odum executes via scoped execute+read API keys in Secret Manager, no withdrawal authority"                                                                                                                                                                                                               | Claiming DART uses Odum-held accounts; treasury-wallet / sub-account mechanics (those belong to Pooled only) |
| `/briefings/regulatory`                                            | "Client-owned venue accounts; Odum has read-only+read-transaction keys; Odum never executes or touches capital"                                                                                                                                                                                                                                                     | "POD"; treasury-wallet mechanics; mixing Reg Umbrella with IM/DART custody language                          |
| Platform UI `/services/treasury/` (Pooled only)                    | Subscription + redemption mechanics; share-class NAV; history ledger                                                                                                                                                                                                                                                                                                | Describing SMA / DART capital flow here (those clients don't have a treasury surface)                        |
| Internal decks                                                     | POD named (for IM Pooled); custodian-specific detail                                                                                                                                                                                                                                                                                                                | —                                                                                                            |
| Second-call walkthrough                                            | POD named; custodian named; structural mechanics in full                                                                                                                                                                                                                                                                                                            | —                                                                                                            |

## Related docs

- [treasury-and-subaccount-model.md](./treasury-and-subaccount-model.md) — Pooled subscription / redemption mechanic;
  portal surface; UAC contract sketch.
- [im-decision-journey.md](../experience/im-decision-journey.md) — pb2a IM briefing; Structure section references this
  doc.
- [../\_ssot-rules/02-tone-and-posture.md](../_ssot-rules/02-tone-and-posture.md) — voice rules.
- [../\_ssot-rules/06-show-dont-show-discipline.md](../_ssot-rules/06-show-dont-show-discipline.md) — rule governing
  what stays internal.
- [../../06-coding-standards/config-reloader-pattern.md](../../06-coding-standards/config-reloader-pattern.md) — API-key
  hot-reload pattern (`ApiKeyReloader` from UTL).

## Follow-ups

- [ ] Confirm POD jurisdictional scope with compliance (which fund structures POD is licensed to administer; what
      cross-border overlap exists with Odum's FCA permissions).
- [ ] Confirm the specific qualified custodians per asset class — Copper for crypto is the default reference; TradFi and
      on-chain equivalents to be named in [treasury-and-subaccount-model.md](./treasury-and-subaccount-model.md).
- [ ] Update [treasury-and-subaccount-model.md](./treasury-and-subaccount-model.md) to reflect the corrected scoping —
      treasury wallet mechanic is Pooled-only (fund administrator's subscription / redemption rail), NOT a universal
      Odum-held master-account+sub-account story across all paths.
- [ ] Add custodian reference to `/codex/05-infrastructure/` if any infra docs reference the fund-administration
      boundary.
- [ ] Brief sales on the corrected public-vs-internal phrasing rule before the next prospect cycle: Pooled = 3rd-party
      custody + Odum portal for subs/redemptions; SMA + DART = client-owned venue + scoped Odum keys.
