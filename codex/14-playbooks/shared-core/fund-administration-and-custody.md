---
scope: [internal, compliance, sales]
visibility: internal-only
---

# Fund administration and custody — Odum-never-custodies rule + POD affiliate

> Internal-only. The POD affiliate is NOT named on any public-facing surface (briefings, marketing pages, decks for
> prospects). Public copy says "regulated affiliate" or "fund administrator"; sales leadership names POD only in
> bilateral conversations with prospects on the way to mandate.

## Invariant

**Odum Research Ltd (the investment manager / trading entity) never custodies client capital — in either structure.**

This is a hard invariant, not a feature per structure. Confusion arises because public surfaces historically framed SMA
as "you keep custody" and left Fund structure unclear — making it sound like Fund = Odum-custodies. Not true. Fund
custody is handled by a regulated affiliate (POD); Odum-the- trading-entity is never the custodian.

**Operational mechanic (2026-04 onward):** across IM (both Pooled and SMA) and DART (Signals-In and Full Pipeline), the
administrator operates a **master account per venue with a ring-fenced sub-account per client**, and a single **treasury
wallet** is the rail for client deposits and withdrawals. Client capital never commingles with Odum Research Ltd's
operating funds. See [treasury-and-subaccount-model.md](./treasury-and-subaccount-model.md) for the full mechanic. Reg
Umbrella remains the exception — the Reg Umbrella client operates their own venue accounts directly, see the decision
table below.

## Decision table — which path uses which mechanic

| Path                 | Who holds the venue account                                        | Capital-movement rail     |
| -------------------- | ------------------------------------------------------------------ | ------------------------- |
| IM — Pooled          | POD (fund administrator) — sub-account per client (= share class)  | POD treasury wallet       |
| IM — SMA             | POD (fund administrator) — sub-account per client                  | POD treasury wallet       |
| DART — Signals-In    | Odum-affiliated administrator — sub-account per client             | Administrator treasury    |
| DART — Full Pipeline | Odum-affiliated administrator — sub-account per client             | Administrator treasury    |
| Regulatory Umbrella  | Client, on their own venue account(s) — Odum never touches capital | N/A (client flows direct) |
| Odum Signals-Out     | Counterparty (on their own stack) — no capital at Odum             | N/A                       |

## Structures and how custody works in each

### IM — SMA (Separately Managed Account) — via administrator sub-account

- **Administrator holds the venue account** in the administrator's name; the client holds a **dedicated sub-account**
  within the master account, identified by `client_id`. Positions, fills, and balances are tracked per-sub-account and
  isolated from other clients.
- Client funds by depositing into the administrator's **treasury wallet**; the administrator credits the client's
  sub-account. Withdrawals go the reverse — client requests, administrator executes from sub-account back through the
  treasury wallet to the client's declared destination. All automated via API and via the platform UI. See
  [treasury-and-subaccount-model.md](./treasury-and-subaccount-model.md).
- Odum Research Ltd operates the trading loop via credentials the administrator holds for the master account. Odum never
  holds principal.
- Applies to CeFi, DeFi (wallet-per-client equivalent), and TradFi brokerage sub-accounts.

### IM — Pooled (Fund) — via POD administrator

- Pooled fund administered by **POD**. Capital flows client → POD treasury wallet → sub-account (identified by share
  class per client) within the fund's venue master accounts.
- Odum Research Ltd is the investment manager (FCA 975797); POD is the fund administrator / corporate-services provider.
  Separation of investment manager and fund administrator is the regulated-fund-manager standard model.
- Odum Research Ltd still never holds principal. Odum operates the trading loop via credentials POD holds for the fund's
  venue master accounts.
- Share-class accounting within POD's books tracks per-client NAV; the venue sub-account model tracks per-client
  positions.
- Why this matters to sales positioning: the offering supports pooled vehicles, share classes, regulated wrappers, and
  cross-border structures without Odum needing to operate its own fund-administration licence stack — POD does that,
  with regulatory cover appropriate to the jurisdiction.

### DART — Signals-In and Full Pipeline — via administrator sub-account

- Same mechanic as IM SMA: administrator holds the venue master account; each DART client holds a dedicated sub-account
  within it. Capital moves in and out via the administrator's treasury wallet, automated via the platform API and UI.
- Instruction routing: the 8-field instruction schema carries a `client_id`; `execution-service` routes the order to the
  correct sub-account via the venue's native sub-account primitive (Binance sub-account, Hyperliquid sub-wallet,
  separate chain wallet, etc.).
- Administrator identity for the DART track is TBD per the follow-up in
  [treasury-and-subaccount-model.md](./treasury-and-subaccount-model.md) — may be POD, may be a separate administrator
  specific to SaaS engagements. Public copy: "Odum's regulated administrator".

### Regulatory Umbrella — client-owned venue accounts

- Reg Umbrella is the exception to the administrator-sub-account mechanic. The Reg Umbrella client operates their own
  regulated activity under Odum's FCA permissions. Capital sits on the client's own venue accounts (which the client
  holds directly or via their own fund administrator).
- Odum receives **read-only + read-transaction** venue API keys for reporting and supervisory purposes. Odum never
  executes on Reg Umbrella client venues and never touches capital.
- The regulatory overlay (MLRO, compliance monitoring, transaction reporting, best-execution evidence) runs through
  Odum; the custody overlay stays with the client.
- See [../experience/regulatory-umbrella-briefing.md](../experience/regulatory-umbrella-briefing.md).

## Why POD is internal-only on public surfaces

- POD branding is separate from Odum Research branding. Public UI is Odum Research; POD operates in the background.
- Naming POD on marketing pages adds a character with no narrative payoff for the prospect at pre-commitment stage. They
  care about the custody mechanic, not the entity that operates it.
- The second call surfaces POD by name when structure selection turns operational.

## Public-copy rules

| Surface                                                            | Allowed phrasing                                                                                                                                                                                                                                                                                  | Forbidden                                                                                                                                                                      |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `/investment-management`, `/strategies.html`, homepage             | "Pooled fund administered by a regulated fund administrator"; "sub-account per client inside the administrator's venue master account"; "deposits and withdrawals flow through the administrator's treasury wallet, automated via API and UI"; "Odum Research Ltd never custodies client capital" | "POD" (the named administrator entity); "Odum Research Ltd holds the account"; "read-only API keys" (factually wrong for IM — Odum executes on the administrator-held account) |
| `/briefings/investment-management`                                 | Same as above; may say "fund administrator" or "regulated administrator"                                                                                                                                                                                                                          | "POD"; administrator-legal-entity naming; internal custody workflow detail                                                                                                     |
| `/briefings/dart-signals-in`, `/briefings/dart-full`, DART landing | "Odum's regulated administrator holds the venue account; your capital sits in a ring-fenced sub-account"; "deposits and withdrawals automated via API and via the platform UI"                                                                                                                    | Legal-entity names for the administrator                                                                                                                                       |
| `/briefings/regulatory`                                            | Reg Umbrella uses **read-only + read-transaction** venue keys (client executes themselves on their own venue accounts) — distinct mechanic; capital stays with the client; no treasury wallet in the Reg Umbrella path                                                                            | "POD"; treasury-wallet mechanics (not applicable to Reg Umbrella); mixing Reg Umbrella mechanics with IM/DART mechanics                                                        |
| Platform UI `/services/treasury/`                                  | Deposit and withdrawal mechanics; balance per sub-account; ledger                                                                                                                                                                                                                                 | —                                                                                                                                                                              |
| Internal decks                                                     | POD named (for IM); specific DART administrator named                                                                                                                                                                                                                                             | —                                                                                                                                                                              |
| Second-call walkthrough                                            | POD named, structure mechanics detailed                                                                                                                                                                                                                                                           | —                                                                                                                                                                              |

## Related docs

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
- [ ] Add POD legal-entity reference + permissions citation to `/codex/05-infrastructure/` if any infra docs reference
      the fund-administration boundary.
- [ ] Brief sales on the public-vs-internal phrasing rule before the next prospect cycle.
