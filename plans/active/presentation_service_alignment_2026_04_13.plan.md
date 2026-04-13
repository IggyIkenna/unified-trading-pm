---
title: Presentation & Service Alignment — Full Plan
created: 2026-04-13
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-13
---

# Presentation & Service Alignment

## Context

This session refactored the board presentation and built 5 investor relations decks with entitlement-gated access.
During the process, we identified that service naming is inconsistent across the website, presentations, and in-app
navigation. The three commercial services (Trading Platform as a Service, Investment Management, Regulatory Umbrella)
need to be consistently represented everywhere.

### The Service Model

Three commercial services. Reports/reporting is a shared capability included in all three — not a standalone product.

| Service                       | What the client gets                                     | Reports? |
| ----------------------------- | -------------------------------------------------------- | -------- |
| Trading Platform as a Service | Bespoke scope: data, research, trading, observe, reports | Yes      |
| Investment Management         | We run capital + full reporting portal                   | Yes      |
| Regulatory Umbrella           | Regulatory coverage + full reporting/compliance portal   | Yes      |

Data and Research are not separate commercial products today — they are capabilities within the Trading Platform as a
Service offering. They could become standalone in future but the commercial focus now is bespoke platform deals.

### Naming SSOT (taxonomy.ts)

In-app nav labels (capabilities, not products):

- Data, Research, Trading, Observe, Manage, Reports

Commercial service names (for website + presentations):

- Trading Platform as a Service
- Investment Management
- Regulatory Umbrella

---

## Phase 0 — Deploy Current Work + Verify

All presentation code, entitlement gating, and Firebase users are built. Deploy and verify.

### Todo 0.1 — Deploy unified-trading-system-ui

- [x] [SCRIPT] P0. Run quality gates: `cd unified-trading-system-ui && bash scripts/quality-gates.sh`
- [ ] [HUMAN] P0. Deploy:
      `cd unified-trading-system-ui && bash scripts/quickmerge.sh "feat: board presentations refactor — 5 decks, entitlement gating, shared shell" --agent`

### Todo 0.2 — Deploy user-management-ui

- [ ] [HUMAN] P0. Deploy:
      `cd user-management-ui && bash scripts/quickmerge.sh "feat: add provision-presentation-users script for investor relations access" --agent`

### Todo 0.3 — Verify on production

- [ ] [HUMAN] P0. Go to `odum-research.com/login?redirect=/investor-relations`
- [ ] [HUMAN] P0. Test `investor@odum-research.co.uk` / `OdumIR2026!` — should see all 6 cards
- [ ] [HUMAN] P0. Test `advisor@odum-research.co.uk` / `OdumAdvisor2026!` — should see only Board + Plan
- [ ] [HUMAN] P0. Test `prospect-platform@odum-research.co.uk` / `OdumPlatform2026!` — should see only Platform deck
- [ ] [HUMAN] P0. Test `prospect-im@odum-research.co.uk` / `OdumIM2026!` — should see only Investment Management deck
- [ ] [HUMAN] P0. Test `prospect-regulatory@odum-research.co.uk` / `OdumReg2026!` — should see only Regulatory deck
- [ ] [HUMAN] P0. Verify demo links from presentations open correct platform pages
- [ ] [HUMAN] P0. Verify frosted overlay appears when navigating to a presentation without entitlement

---

## Phase 1 — Public Website Service Pages (3 services, not 5)

### Current state

5 public service pages:

- `/services/data` — standalone data provision page
- `/services/backtesting` — standalone research page (called "Research & Build")
- `/services/platform` — trading terminal page (called "Trading Terminal")
- `/services/investment` — investment management page
- `/services/regulatory` — regulatory umbrella page

### Target state

3 commercial service pages + capability descriptions within platform page:

**`/services/platform`** — "Trading Platform as a Service"

- Reframe as the main product page
- Include Data, Research, Trading, Observe, Reports as capabilities within the platform
- Engagement levels (scope options, not separate products)
- Link to the platform presentation

**`/services/investment`** — "Investment Management"

- Keep, update to clarify Reports included as part of the service
- Clarify that clients get the same reporting tools (trade history, settlement, compliance)
- Link to the investment presentation

**`/services/regulatory`** — "Regulatory Umbrella"

- Keep, update to clarify Reports included as part of the service
- Same reporting tools as investment management
- Link to the regulatory presentation

**`/services/data`** and **`/services/backtesting`** — redirect or reframe

- Option A: Redirect to `/services/platform` with anchor to relevant section
- Option B: Keep as capability description pages but add "Part of Trading Platform as a Service" framing
- Recommendation: Option B — keep the pages for SEO and detailed capability description, but add a banner/header that
  frames them as capabilities within the platform offering

### Todos

- [ ] [AGENT] P0. Update `/services/platform` (public) — reframe as "Trading Platform as a Service", include capability
      sections for Data, Research, Trading, Observe, Reports
- [ ] [AGENT] P0. Update `/services/investment` (public) — add "Reports included" section, align content with investment
      presentation
- [ ] [AGENT] P0. Update `/services/regulatory` (public) — add "Reports included" section, align content with regulatory
      presentation
- [ ] [AGENT] P1. Update `/services/data` (public) — add "Part of Trading Platform as a Service" banner, reframe as
      capability description
- [ ] [AGENT] P1. Update `/services/backtesting` (public) — rename to "Research", add "Part of Trading Platform as a
      Service" banner
- [ ] [AGENT] P1. Update website navigation to reflect 3 primary services (platform, investment, regulatory) with
      data/research as sub-items

---

## Phase 2 — Presentation Consistency

### Current state

Presentations describe 3 services correctly but use different naming in some places. The "engagement levels" in the
platform deck (Data Only, Data + Research, etc.) could be misread as separate products.

### Target state

Consistent naming across all 5 presentations. Engagement levels clearly framed as "scope within one service" not
"separate products".

### Todos

- [ ] [AGENT] P0. Audit all 5 presentation data files for service name consistency — every reference to a service should
      use the canonical three names
- [ ] [AGENT] P0. Reframe engagement levels in platform presentation slide 4 — from "5 separate products" feel to "scope
      options within one bespoke service"
- [ ] [AGENT] P1. Ensure all demo links from presentations point to the right in-app pages based on service context

---

## Phase 3 — In-App Navigation Descriptions

### Current state

In-app nav uses capability labels (Data, Research, Trading, Observe, Reports) which is correct for platform clients. But
there is no service-context-aware landing — all users land on the same dashboard regardless of their service type.

### Target state

- Capability labels stay as-is (Data, Research, Trading, Observe, Reports) — they describe what the platform does
- But the descriptions and landing experience should be contextual:
  - Platform clients → full dashboard with all capabilities
  - Investment management clients → Reports landing (their reporting portal)
  - Regulatory coverage clients → Reports landing (their compliance portal)

### Todos

- [ ] [AGENT] P1. Update taxonomy.ts descriptions to make clear these are platform capabilities, not standalone services
- [ ] [AGENT] P1. Add service-context-aware redirect on login — based on entitlements, redirect to:
  - `investor-platform` entitlement → `/dashboard`
  - `investor-im` entitlement (without platform) → `/services/reports/executive`
  - `investor-regulatory` entitlement (without platform) → `/services/reports/executive`
- [ ] [AGENT] P2. Add contextual header/banner on Reports pages for IM and regulatory clients — e.g., "Your Investment
      Management Portal" or "Your Regulatory Compliance Portal" based on user entitlements

---

## Phase 4 — Regulatory Umbrella and Investment Management Reporting Overlap

### Context

Both Regulatory Umbrella and Investment Management clients get reporting tools. The reporting tools show the same
underlying data (trade history, settlement, compliance, audit trail) but the framing should be different:

- IM clients see it as "your portfolio performance and reporting"
- Regulatory clients see it as "your compliance and audit documentation"

### Todos

- [ ] [AGENT] P2. Add persona-aware labels/headers to the Reports section — show "Investment Portfolio" vs "Compliance
      Portal" based on user entitlements
- [ ] [AGENT] P2. Ensure both service types get access to: executive dashboard, trade history, settlement tracking,
      compliance reports, reconciliation
- [ ] [AGENT] P2. IM clients additionally see: returns attribution (10-factor waterfall), strategy performance
- [ ] [AGENT] P2. Regulatory clients additionally see: transaction reporting, best execution documentation, financial
      promotions log

---

## Phase 5 — Website ↔ In-App Handoff

### Context

When a regulatory umbrella or investment management client clicks through from the website to log in, their experience
should be seamless:

1. They visit `odum-research.com/services/regulatory` (or `/services/investment`)
2. They click "Sign In" or "Get Started"
3. After login, they land directly in their relevant portal (Reports)
4. The nav shows only what they're entitled to

### Todos

- [ ] [AGENT] P1. Add `?redirect=/services/reports/executive` to Sign In links on regulatory and investment public pages
- [ ] [AGENT] P1. Add `?redirect=/dashboard` to Sign In links on platform public page
- [ ] [AGENT] P2. Ensure nav filtering works correctly — IM/regulatory clients should see Reports + relevant sub-pages,
      not the full platform nav

---

## Success Criteria

### Phase 0 (deploy)

- [ ] All 5 presentations accessible at `odum-research.com/investor-relations/*`
- [ ] Entitlement gating works — each test user sees only their assigned decks
- [ ] Demo links from presentations open correct platform pages

### Phase 1 (website)

- [ ] 3 primary service pages (Platform, Investment Management, Regulatory Umbrella)
- [ ] Data and Research pages reframed as capabilities within Platform
- [ ] All public pages link to the correct presentation
- [ ] QG passes on unified-trading-system-ui

### Phase 2 (presentations)

- [ ] Zero naming inconsistencies across 5 presentation data files
- [ ] Engagement levels in platform deck clearly communicate "scope options" not "separate products"

### Phase 3 (in-app)

- [ ] Login redirect is service-context-aware
- [ ] IM clients land on Reports after login
- [ ] Regulatory clients land on Reports after login
- [ ] Platform clients land on full dashboard

### Phase 4 (reporting overlap)

- [ ] Both IM and regulatory clients see reporting tools
- [ ] Labels are persona-aware ("Investment Portfolio" vs "Compliance Portal")

### Phase 5 (handoff)

- [ ] Website → login → correct landing page flow works for all 3 service types
- [ ] Nav shows only entitled capabilities per user type
