---
doc_type: codex-ssot
title: Information Architecture
summary:
  "Top-down canonical IA tree for the Odum platform (PUBLIC / DEEP DIVE / PLATFORM / OPS route groups) — every page must
  fit — naming the nav SSOTs (spaces-nav-sections.tsx, site-header.tsx, service-tabs.tsx) and the four parallel
  catalogue surfaces."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [ui, customer-journey, information-architecture, catalogue, navigation]
related: [/codex/14-customer-journeys/audiences-and-journeys.md, /codex/14-customer-journeys/glossary.md]
created: 2026-04-19
authoritative_for: [platform information architecture (route-group tree + nav SSOTs)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/audiences-and-journeys.md,
    /codex/14-customer-journeys/glossary.md,
    /codex/14-customer-journeys/page-triage/README.md,
    /codex/14-customer-journeys/page-triage/broken-links.md,
    /codex/14-customer-journeys/playbook-concepts/bloomberg-style-aesthetic.md,
    /codex/14-customer-journeys/playbooks/README.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Information Architecture

Top-down canonical IA for the Odum platform. Every page in the UI must fit into this tree; orphans are triaged in
[page-triage/triage-matrix.md](page-triage/triage-matrix.md).

## Anchoring principle

**Click-click-click to detail.** Initial state of every page assumes the user KNOWS what they want. Collapsing boxes
default to collapsed only when 90%+ of users wouldn't care. The Bloomberg-terminal aesthetic applies throughout — see
[cross-cutting/bloomberg-style-aesthetic.md](playbook-concepts/bloomberg-style-aesthetic.md).

## Top-level tree

```
Odum Platform
├── PUBLIC (unauthenticated — pb1)
│   ├── / (homepage — three-services pitch)
│   ├── /investment-management (IM service landing)
│   ├── /platform (DART service landing)
│   ├── /signals (Odum Signals service landing)
│   ├── /regulatory (Reg Umbrella service landing)
│   ├── /who-we-are (firm)
│   ├── /story (timeline — public; long-form essay /our-story moved into DEEP DIVE 2026-04-25)
│   ├── /contact (mandate / demo enquiry form)
│   ├── /questionnaire (standalone brief questionnaire — also embedded inline on DEEP DIVE lock screen)
│   ├── /demo (book a demo)
│   ├── /privacy, /terms (legal)
│   ├── /login (Firebase + demo persona sign-in)
│   └── /signup (mock-signup flow for staging)
│
├── DEEP DIVE (light-auth gated — pb2; formerly "Briefings")
│   ├── /briefings (hub — six pillar tiles + "How to use this page" intro)
│   ├── /briefings/investment-management (pb2-im)
│   ├── /briefings/platform (DART Start Here — pb2-dart)
│   ├── /briefings/dart-signals-in (DART Signals-In path)
│   ├── /briefings/dart-full (DART Full pipeline)
│   ├── /briefings/signals-out (Odum Signals — inverse direction)
│   ├── /briefings/regulatory (pb2-reg)
│   ├── /docs (developer documentation — moved here from PUBLIC, gated 2026-04-25)
│   ├── /our-story (long-form founder narrative — moved here from PUBLIC, gated 2026-04-25)
│   └── /faq (gated 2026-04-25)
│
├── PLATFORM (Firebase-auth gated — pb3 demos + real clients)
│   ├── /dashboard (post-login landing; role-aware quick-actions)
│   ├── /services/ (the primary product surface)
│   │   ├── data/          (Data Catalogue + data service)
│   │   ├── research/      (Research surface — iteration)
│   │   ├── strategy-catalogue/   (Strategy Catalogue — fixed universe SSOT)
│   │   ├── ml-model-catalogue/   (ML Model Catalogue — PROPOSED, see roadmap)
│   │   ├── execution-algo-catalogue/ (Execution Algo Catalogue — PROPOSED, see roadmap)
│   │   ├── trading/       (DART trading terminal + positions + orders)
│   │   ├── execution/     (Execution quality + TCA + algos)
│   │   ├── promote/       (Strategy promotion lifecycle)
│   │   ├── observe/       (Observation — health, risk, alerts, reconciliation)
│   │   ├── reports/       (Client reporting — SHARED by IM + Reg Umbrella)
│   │   └── manage/        (Clients, compliance, fees, mandates — internal-only)
│   ├── /investor-relations/ (board/plan/IM/platform/regulatory presentations — Odum investors, not prospects)
│   ├── /settings/ (per-user: api-keys, notifications)
│   └── /onboarding (post-signup wizard)
│
└── OPS (admin/internal-only — not in any playbook)
    ├── /admin/ (user management, orgs, data, users CRUD)
    ├── /ops/ (services dashboard, jobs)
    ├── /config, /devops, /approvals, /engagement, /internal (internal control panels)
    └── /health (dev-only service status)
```

## Audience-to-route mapping

| Audience             | Route-group                       | Auth gate                                                                  | Entry point                                         |
| -------------------- | --------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------- |
| Anonymous visitor    | `(public)`                        | None                                                                       | `/`                                                 |
| Deep Dive prospect   | Deep Dive routes (see tree above) | Light auth — questionnaire IS access path; secondary code-entry disclosure | Any `/briefings/*`, `/docs`, `/our-story`, `/faq`   |
| Warm prospect (demo) | `(platform)`                      | Staging Firebase, demo persona                                             | `/dashboard` → services portal                      |
| Paying client        | `(platform)`                      | Production Firebase, real persona                                          | `/dashboard` → services portal (entitlement-sliced) |
| Odum investor        | `(platform)/investor-relations`   | Staging/Prod Firebase, investor persona                                    | `/investor-relations`                               |
| Odum internal admin  | `(platform)` + `(ops)`            | Production Firebase, admin persona                                         | `/admin`                                            |
| Odum internal trader | `(platform)`                      | Production Firebase, internal persona                                      | `/dashboard` (services portal, no ops)              |

## Top-level nav

Public marketing nav lives in TWO surfaces (intentionally duplicated — different concerns, different breakpoints):

### Surface 1 — Site-header Sheet drawer (every public page)

Component: [components/shell/site-header.tsx](unified-trading-system-ui/components/shell/site-header.tsx). Click the
"Menu" pill in the header to open a left-side sheet with the full marketing nav. **Deep Dive collapses behind a single
toggle button** — click "Deep Dive ▾" to expand inline. Each item shows an amber lock icon when the visitor is
signed-out and has no cached briefing session. Hardcoded constants `DEEP_DIVE_HEADLINE` + `DEEP_DIVE_BRIEFINGS` in the
file (NOT shared with `spaces-nav-sections.tsx`).

### Surface 2 — Spaces dropdown (in-app playbook switcher)

Component:
[components/shell/spaces-nav-sections.tsx](unified-trading-system-ui/components/shell/spaces-nav-sections.tsx). Shown in
the header on signed-in surfaces.

```
Spaces
├── Overview (pb1) — public
│   ├── Home /
│   ├── Investment Management /investment-management
│   ├── Data Analytics, Research & Trading (DART) /platform
│   ├── Odum Signals /signals
│   ├── Regulatory /regulatory
│   ├── Who We Are /who-we-are
│   └── Story (timeline) /story
├── Deep Dive (pb2) — light-auth-gated (questionnaire IS access path)
│   ├── Briefings Hub /briefings
│   ├── Developer Documentation /docs
│   ├── FAQ /faq
│   ├── Investment Management /briefings/investment-management
│   ├── DART — Start here /briefings/platform
│   ├── DART — Signals In /briefings/dart-signals-in
│   ├── DART — Full Pipeline /briefings/dart-full
│   ├── Odum Signals /briefings/signals-out
│   ├── Regulatory Umbrella /briefings/regulatory
│   └── Our Story (long-form essay) /our-story
├── Client Access (pb3) — Firebase-gated
│   ├── Client Reporting /services/reports/overview
│   ├── DART /dashboard (Research, Trading, Execution)
│   ├── Odum Signals — Counterparty Dashboard /services/signals/dashboard
│   ├── Funds (IM) /services/im/funds
│   ├── Strategy Catalogue (IM) /services/research/strategy/catalog
│   └── Investor Relations /investor-relations
└── Admin (Odum-internal only — visibility-sliced)
```

The Spaces dropdown is the **authoritative top-nav SSOT for signed-in surfaces** — if the IA changes, this file changes
first and the codex docs track the change. **When restructuring marketing nav (Deep Dive renames, additions, lock
indicators), edit BOTH `site-header.tsx` AND `spaces-nav-sections.tsx`** — they don't share code.

## Per-service nav SSOT

Per-service tab bars are defined in
[components/shell/service-tabs.tsx](unified-trading-system-ui/components/shell/service-tabs.tsx) — one const per service
(`DATA_TABS`, `BUILD_TABS`, `STRATEGY_SUB_TABS`, `STRATEGY_CATALOGUE_SUB_TABS`, `TRADING_TABS`, `OBSERVE_TABS`,
`MANAGE_TABS`, `REPORTS_TABS`, `ADMIN_TABS`, `EXECUTE_TABS`, plus `ML_SUB_TABS`). Editing one of these constants updates
every in-page tab bar for that service.

**Rule:** cross-service navigation (e.g., Data → Research) lives in spaces-nav-sections.tsx OR the lifecycle-nav.
Service-local navigation (e.g., Data → Data Instruments → Data Coverage) lives in service-tabs.tsx. No third place.

## Four catalogues — parallel surfaces

Each catalogue is a fixed-universe SSOT surfaced under `/services/<catalogue-name>/`. All four follow the same pattern
(see [cross-cutting/catalogues.md](playbook-concepts/catalogues.md)):

- overview page (landing)
- coverage matrix (all entries × classification dimensions)
- by-combination or filtered view
- per-entry detail page
- admin surface (lock-state / entitlement edit — admin-only)

Current state:

- Strategy Catalogue `/services/strategy-catalogue/` — SHIPPED (Phase 10, 2026-04-19)
- Data Catalogue `/services/data/` — exists as data service, needs catalogue-surface unification (roadmap)
- ML Model Catalogue `/services/research/ml/` — exists as ML pages, needs catalogue-surface unification (roadmap)
- Execution Algo Catalogue `/services/execution/` — exists as orphan pages, needs catalogue-surface unification
  (roadmap)

## Client reporting is a SHARED surface

The `/services/reports/*` tree is the ONE client-reporting surface. It's the primary walkthrough in BOTH pb3a (Reg
Umbrella demo) and pb3b (IM demo) — same pages, same features, same data. Only the narrative framing differs. See
[cross-cutting/client-reporting.md](playbook-concepts/client-reporting.md).

## Investor Relations is NOT for prospects

`/investor-relations/*` is for Odum investors and advisors — NOT for demo prospects. The presentations (board, plan, IM,
platform, regulatory, disaster recovery) are sales/fundraising assets, not product walkthroughs. See
[cross-cutting/investor-relations.md](playbook-concepts/investor-relations.md).

## Related

- Full page inventory: [page-triage/triage-matrix.md](page-triage/triage-matrix.md)
- Playbook families: [audiences-and-journeys.md](audiences-and-journeys.md)
- Visibility slicing: [cross-cutting/visibility-slicing.md](playbook-concepts/visibility-slicing.md)
