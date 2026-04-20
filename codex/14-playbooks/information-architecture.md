---
scope: [engineer, admin, sales]
---

# Information Architecture

Top-down canonical IA for the Odum platform. Every page in the UI must fit into this tree; orphans are triaged in
[page-triage/triage-matrix.md](page-triage/triage-matrix.md).

## Anchoring principle

**Click-click-click to detail.** Initial state of every page assumes the user KNOWS what they want. Collapsing boxes
default to collapsed only when 90%+ of users wouldn't care. The Bloomberg-terminal aesthetic applies throughout — see
[cross-cutting/bloomberg-style-aesthetic.md](cross-cutting/bloomberg-style-aesthetic.md).

## Top-level tree

```
Odum Platform
├── PUBLIC (unauthenticated — pb1)
│   ├── / (homepage — three-services pitch)
│   ├── /investment-management (IM service landing)
│   ├── /platform (DART service landing)
│   ├── /regulatory (Reg Umbrella service landing)
│   ├── /firm (who we are)
│   ├── /contact (mandate / demo enquiry form)
│   ├── /demo (book a demo)
│   ├── /docs (developer documentation)
│   ├── /privacy, /terms (legal)
│   ├── /login (Firebase + demo persona sign-in)
│   └── /signup (mock-signup flow for staging)
│
├── BRIEFINGS (light-auth gated — pb2)
│   ├── /briefings (hub)
│   ├── /briefings/investment-management (pb2-im)
│   ├── /briefings/platform (pb2-dart)
│   └── /briefings/regulatory (pb2-reg)
│
├── PLATFORM (Firebase-auth gated — pb3 demos + real clients)
│   ├── /dashboard (post-login landing; role-aware quick-actions)
│   ├── /services/ (the primary product surface)
│   │   ├── data/          (Data Catalogue + data service)
│   │   ├── research/      (Research surface — iteration)
│   │   ├── strategy-catalogue/   (Strategy Catalogue — fixed universe SSOT)
│   │   ├── ml-model-catalogue/   (ML Model Catalogue — PROPOSED, see roadmap)
│   │   ├── execution-algo-catalogue/ (Execution Algo Catalogue — PROPOSED, see roadmap)
│   │   ├── trading/       (Trading terminal + positions + orders)
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

| Audience                 | Route-group                     | Auth gate                               | Entry point                                         |
| ------------------------ | ------------------------------- | --------------------------------------- | --------------------------------------------------- |
| Anonymous visitor        | `(public)`                      | None                                    | `/`                                                 |
| Post-first-call prospect | `(public)/briefings/*`          | Light auth (briefing access code)       | `/briefings`                                        |
| Warm prospect (demo)     | `(platform)`                    | Staging Firebase, demo persona          | `/dashboard` → services portal                      |
| Paying client            | `(platform)`                    | Production Firebase, real persona       | `/dashboard` → services portal (entitlement-sliced) |
| Odum investor            | `(platform)/investor-relations` | Staging/Prod Firebase, investor persona | `/investor-relations`                               |
| Odum internal admin      | `(platform)` + `(ops)`          | Production Firebase, admin persona      | `/admin`                                            |
| Odum internal trader     | `(platform)`                    | Production Firebase, internal persona   | `/dashboard` (services portal, no ops)              |

## Top-level nav

Single SSOT for the Spaces dropdown (in-app playbook switcher):

```
Spaces
├── Marketing (pb1) — public
│   ├── Home /
│   ├── Investment Management /investment-management
│   ├── Data Analytics, Research & Trading (DART) /platform
│   ├── Regulatory Umbrella /regulatory
│   ├── Who We Are /firm
│   └── Contact /contact
├── Research & Documentation (pb2) — briefings-gated
│   ├── Briefings Hub /briefings
│   ├── IM Briefing /briefings/investment-management
│   ├── DART Briefing /briefings/platform
│   ├── Regulatory Briefing /briefings/regulatory
│   └── Developer Documentation /docs
├── Client Access (pb3) — Firebase-gated
│   ├── Dashboard /dashboard
│   ├── Services Portal /services/... (entitlement-sliced; see visibility-slicing.md)
│   └── Investor Relations /investor-relations
└── Admin (Odum-internal only)
    ├── User Management /admin/users
    ├── Orgs /admin/organizations
    ├── Ops /ops/services
    └── Config /config
```

The Spaces dropdown component is
[components/shell/spaces-nav-sections.tsx](unified-trading-system-ui/components/shell/spaces-nav-sections.tsx). This
file is the **authoritative top-nav SSOT** — if the IA changes, this file changes first and the codex docs track the
change.

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
(see [cross-cutting/catalogues.md](cross-cutting/catalogues.md)):

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
[cross-cutting/client-reporting.md](cross-cutting/client-reporting.md).

## Investor Relations is NOT for prospects

`/investor-relations/*` is for Odum investors and advisors — NOT for demo prospects. The presentations (board, plan, IM,
platform, regulatory, disaster recovery) are sales/fundraising assets, not product walkthroughs. See
[cross-cutting/investor-relations.md](cross-cutting/investor-relations.md).

## Related

- Full page inventory: [page-triage/triage-matrix.md](page-triage/triage-matrix.md)
- Playbook families: [audiences-and-journeys.md](audiences-and-journeys.md)
- Visibility slicing: [cross-cutting/visibility-slicing.md](cross-cutting/visibility-slicing.md)
