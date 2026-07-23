---
doc_type: codex-ssot
title: Audiences and Journeys
summary:
  "The full persona × playbook (pb1 marketing / pb2 deep-dive / pb3 demo / real-client / admin) × environment matrix —
  every UI route must map to at least one cell — plus the canonical anonymous-visitor → cold/warm prospect → demo →
  real-client journey sequence."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [ui, customer-journey, personas, playbooks, sales, prospect]
related: [/codex/14-customer-journeys/information-architecture.md, /codex/14-customer-journeys/glossary.md]
created: 2026-04-19
authoritative_for: [persona × playbook × environment matrix (customer-journey audiences)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/glossary.md,
    /codex/14-customer-journeys/information-architecture.md,
    /codex/14-customer-journeys/page-triage/README.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Audiences and Journeys

The full matrix of WHO uses the platform, WHERE they start, and HOW they progress. Every UI route must belong to at
least one cell of this matrix.

## The three axes

1. **Audience / persona** — who the user is
2. **Playbook family** — which journey applies (pre-call / post-call / warm / paying / admin)
3. **Environment** — local dev / staging / production

## Persona × playbook matrix

| Persona                              | pb1 Marketing |  pb2 Deep Dive  | pb3 Demo  | Real client |           Admin           | Reference fixture                                                                                                                 |
| ------------------------------------ | :-----------: | :-------------: | :-------: | :---------: | :-----------------------: | --------------------------------------------------------------------------------------------------------------------------------- |
| Anonymous visitor                    |      ✅       |        —        |     —     |      —      |             —             | (no auth)                                                                                                                         |
| Cold-inbound prospect                |      ✅       | ✅ (light auth) |     —     |      —      |             —             | Brief questionnaire submit (channel A — most common)                                                                              |
| Warm hand-off prospect               |      ✅       | ✅ (light auth) |     —     |      —      |             —             | Per-path access code from sales (channel B)                                                                                       |
| Warm prospect — IM flavour           |      ✅       |       ✅        | ✅ (pb3b) |      —      |             —             | persona `prospect-im`                                                                                                             |
| Warm prospect — DART flavour         |      ✅       |       ✅        | ✅ (pb3c) |      —      |             —             | persona `prospect-dart` (to add)                                                                                                  |
| Warm prospect — Reg Umbrella flavour |      ✅       |       ✅        | ✅ (pb3a) |      —      |             —             | persona `prospect-reg` (to add)                                                                                                   |
| Real client — IM                     |      ✅       |       ✅        |     —     |     ✅      |             —             | [lib/auth/personas.ts:38](unified-trading-system-ui/lib/auth/personas.ts#L38) `client-full`, `client-data-only`, `client-premium` |
| Real client — DART (platform-only)   |      ✅       |       ✅        |     —     |     ✅      |             —             | (subset of `client-full` entitlements, no IM reporting)                                                                           |
| Real client — Reg Umbrella           |      ✅       |       ✅        |     —     |     ✅      |             —             | TBD — needs dedicated persona                                                                                                     |
| Odum investor                        |       —       |        —        |     —     |      —      | via `/investor-relations` | persona `investor`, `advisor`                                                                                                     |
| Odum internal trader                 |       —       |        —        |     —     |      —      |            ✅             | persona `internal-trader`                                                                                                         |
| Odum admin                           |      ✅       |       ✅        |    ✅     |     ✅      |            ✅             | persona `admin`                                                                                                                   |

## Environment × playbook matrix

| Playbook    | Local dev                                   | Staging (`odum-research.co.uk`)                   | Production (`odum-research.com`)             |
| ----------- | ------------------------------------------- | ------------------------------------------------- | -------------------------------------------- |
| pb1         | ✅ homepage live                            | ✅                                                | ✅                                           |
| pb2         | ✅ briefings with test password             | ✅ briefings with rotating prospect password      | ✅ briefings with rotating prospect password |
| pb3         | ✅ demo persona via localStorage or sign-in | ✅ demo Firebase account per prospect             | n/a — prospects never use prod               |
| Real client | —                                           | —                                                 | ✅ real Firebase                             |
| Admin       | ✅ admin persona                            | ✅ real admin Firebase account                    | ✅ real admin Firebase account               |
| Investor    | —                                           | ✅ (on staging with rotated password for reviews) | ✅                                           |

## Canonical journey sequence

A typical prospect progresses through this sequence:

```
Anonymous visitor
    ↓ (stumbles on homepage or is referred)
    → Opens / — sees three-service pitch (Invest / Build & Run / Regulate)
    → Clicks a service tile → lands on /investment-management or /platform or /regulatory
    → Either: clicks a Deep Dive item in the side-nav (Briefings / Docs / Our Story / FAQ),
              OR clicks "Book a Call" → Calendly,
              OR clicks "Contact / Discuss a Mandate" → /contact form
    ↓
Cold-inbound prospect (channel A — most common since 2026-04-25)
    → Hits Deep Dive route → <BriefingAccessGate> renders with brief questionnaire embedded inline
    → Fills questionnaire → setBriefingSessionActive() + email-back (code + Next steps + Calendly + Strategy Eval)
    → Lands on /briefings → reads the relevant pillar(s) + sibling docs
    ↓
Warm hand-off prospect (channel B — sales-led)
    → Odum sends direct briefing link + per-path access code
    → Uses "I already have a code" disclosure on the gate → unlocks
    → Reads briefings; sales arranges call directly
    ↓
Both channels converge here:
    → Books 30-min Calendly walk-through call
    → Submits Strategy Evaluation DDQ at /strategy-evaluation (mandatory before Sandbox demo)
    ↓ (Odum schedules Sandbox demo)
Warm prospect (Tier 2 demo)
    → Odum provisions demo user in user-management-ui on staging
    → Odum sends link to uat.odum-research.com + demo credentials
    → Prospect signs in → lands on /dashboard → services portal
    → Experience sliced to their flavour (pb3a / pb3b / pb3c) using their DDQ answers
    ↓ (prospect commits)
Real client
    → Odum provisions real user in user-management-ui against production Firebase
    → Entitlements set to match paid package
    → Client signs in at odum-research.com → same services portal, sliced to paid entitlements
```

## Related

- Per-journey playbook docs: [playbooks/](playbooks/)
- Auth-tier details: [authentication/](authentication/)
- Environment-specific details: [environments/](environments/)
- Visibility slicing mechanism: [cross-cutting/visibility-slicing.md](playbook-concepts/visibility-slicing.md)
- Demo persona fixtures: [lib/auth/personas.ts](unified-trading-system-ui/lib/auth/personas.ts)
