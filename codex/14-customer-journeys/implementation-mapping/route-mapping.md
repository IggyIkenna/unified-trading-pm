---
doc_type: codex-ssot
title: Route Mapping — Experience Section → UI Route
summary:
  Index binding each experience-playbook walkthrough section to concrete unified-trading-system-ui routes (pb1 public
  5-path, pb2 briefings, pb3 demo) plus cross-playbook shared routes and the rule-03 audience/phase-prefixed routes that
  must NOT exist.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [route, ui, playbook, navigation, refactor, testing]
related:
  [
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    ../shared-core/same-system-principle.md,
    ../shared-core/shared-reporting-core.md,
  ]
created: 2026-04-20
authoritative_for: [experience-section -> UI-route mapping]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/authentication/light-auth-briefings.md,
    /codex/14-customer-journeys/demo-ops/upsell-overlays.md,
    /codex/14-customer-journeys/experience/marketing-journey.md,
    /codex/14-customer-journeys/implementation-mapping/README.md,
    /codex/14-customer-journeys/implementation-mapping/demo-email-and-provisioning-flow.md,
    /codex/14-customer-journeys/implementation-mapping/persona-and-user-prototype-mapping.md,
    /codex/14-customer-journeys/implementation-mapping/playbook-to-qa-coverage.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Route Mapping — Experience Section → UI Route

> Every experience-playbook walkthrough section maps to concrete UI routes. This doc is the index. Drives Playwright
> spec coverage and consolidation decisions in Stage 3E.

## Why this map

Experience-layer walkthroughs (rule 01 §5) reference routes implicitly ("the reporting surface", "the catalogue
landing"). This doc pins each walkthrough beat to a named route in `unified-trading-system-ui` so testing, maintenance,
and refactor decisions all reference the same identifier.

Routes change over time. When a route moves, the mapping here updates and the Playwright spec updates in the same PR
(rule 01 enforcement rule 3 — engineering traceability).

## Per-playbook mapping

### pb1 — Marketing Journey ([`../experience/marketing-journey.md`](../experience/marketing-journey.md))

5-path public surface, locked 2026-04-20. Every route below has an inbound link from `/` (homepage path tiles + nav) so
no orphan pages exist.

| Walkthrough section               | Route                    | Inbound link path (parent)                               |
| --------------------------------- | ------------------------ | -------------------------------------------------------- |
| Home-page frame                   | `/` (public)             | _(root)_                                                 |
| DART umbrella path tile           | `/platform`              | `/` (homepage tile + header nav "DART")                  |
| DART Signals-In (direction arrow) | `/platform/signals-in`   | `/platform` (sub-path card) + `/` (homepage DART tile)   |
| DART Full pipeline                | `/platform/full`         | `/platform` (sub-path card) + `/` (homepage DART tile)   |
| Odum Signals (signals-out path)   | `/signals`               | `/` (homepage tile + header nav "Odum Signals")          |
| Investment Management             | `/investment-management` | `/` (homepage tile + header nav "Investment Management") |
| Regulatory Umbrella               | `/regulatory`            | `/` (homepage tile + header nav "Regulatory")            |
| Firm (alias: `/who-we-are`)       | `/who-we-are`            | `/` (homepage tile + header nav "Who We Are")            |
| Bottom CTA booking flow           | `/contact`               | `/` + every path page's footer + header "Book a call"    |

Route alias: the "Firm" nav label resolves to `/who-we-are`. The existing slug pre-dates the 5-path rename and has not
been renamed to avoid breaking external inbound links.

Services sub-routes (public descriptor pages under `/services/`):

| Service descriptor | Route                   | Inbound link path                                         |
| ------------------ | ----------------------- | --------------------------------------------------------- |
| Backtesting        | `/services/backtesting` | `/platform/full` (services strip)                         |
| Data               | `/services/data`        | `/platform` umbrella (services strip)                     |
| Engagement         | `/services/engagement`  | `/investment-management` + `/regulatory` (services strip) |
| Execution          | `/services/execution`   | `/platform/signals-in` + `/signals` (services strip)      |
| Investment         | `/services/investment`  | `/investment-management` (services strip)                 |
| Platform           | `/services/platform`    | `/platform` umbrella (services strip)                     |
| Regulatory         | `/services/regulatory`  | `/regulatory` (services strip)                            |

### pb2 — Deep Dive ([`../experience/briefings-hub.md`](../experience/briefings-hub.md))

Light-auth gate (Tier 1 — see [`../authentication/light-auth-briefings.md`](../authentication/light-auth-briefings.md)).
Six briefing pillars + developer docs + founder long-form + FAQ. One unlock covers all routes in this section.

| Walkthrough section            | Route                                             | Inbound link path                                        |
| ------------------------------ | ------------------------------------------------- | -------------------------------------------------------- |
| Hub landing                    | `/briefings` (gated)                              | Side-nav Deep Dive item OR direct URL                    |
| DART umbrella briefing         | `/briefings/platform`                             | `/briefings` hub card + side-nav                         |
| DART Signals-In briefing       | `/briefings/dart-signals-in`                      | `/briefings` hub card + platform pillar + side-nav       |
| DART Full briefing             | `/briefings/dart-full`                            | `/briefings` hub card + platform pillar + side-nav       |
| Odum Signals briefing          | `/briefings/signals-out`                          | `/briefings` hub card + side-nav                         |
| Investment Management briefing | `/briefings/investment-management`                | `/briefings` hub card + side-nav                         |
| Regulatory briefing            | `/briefings/regulatory`                           | `/briefings` hub card + side-nav                         |
| Developer documentation        | `/docs` (gated)                                   | Side-nav Deep Dive item                                  |
| Founder long-form story        | `/our-story` (gated; timeline `/story` is public) | Side-nav Deep Dive item                                  |
| FAQ                            | `/faq` (gated)                                    | Side-nav Deep Dive item                                  |
| Calendly CTA (post-read)       | `https://calendly.com/odum-ikenna`                | `/briefings` "Next steps" CTA + post-questionnaire email |

### pb2a — IM Decision Journey ([`../experience/im-decision-journey.md`](../experience/im-decision-journey.md))

Reference playbook — narrative only (no separate UI beyond briefing route `/briefings/im`).

### pb2b — DART Briefing ([`../experience/dart-briefing.md`](../experience/dart-briefing.md))

| Walkthrough section                   | Route                                                     |
| ------------------------------------- | --------------------------------------------------------- |
| Briefing landing + rule 10 fit-check  | `/briefings/dart` (includes "Does DART fit you?" section) |
| Strategy catalogue (view in briefing) | `/briefings/dart#catalogue-walk` (in-page anchor)         |
| Commitment + structure section        | `/briefings/dart#commitment`                              |

### pb2c — Regulatory Umbrella Briefing ([`../experience/regulatory-umbrella-briefing.md`](../experience/regulatory-umbrella-briefing.md))

| Walkthrough section | Route                                       |
| ------------------- | ------------------------------------------- |
| Briefing landing    | `/briefings/regulatory-umbrella`            |
| Onboarding path     | `/briefings/regulatory-umbrella#onboarding` |

### pb3 — Staging Demo Hub ([`../experience/staging-demo-journey.md`](../experience/staging-demo-journey.md))

| Walkthrough section                        | Route                                                                       |
| ------------------------------------------ | --------------------------------------------------------------------------- |
| Hub landing (demo-user sign-in lands here) | `/demo` (Firebase-staging-gated)                                            |
| Flavour navigation blocks                  | `/demo#im`, `/demo#reg-umbrella`, `/demo#dart` (LOCKED-VISIBLE per profile) |
| Demo controls (admin pane)                 | `/demo/admin` (HIDDEN from prospect)                                        |

### pb3a — Regulatory Demo ([`../experience/regulatory-demo.md`](../experience/regulatory-demo.md))

| Walkthrough section                  | Route                                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| Regulated-activity reporting landing | `/services/reports/overview` (Reg Umbrella profile applied)                                                        |
| Transaction reporting                | `/services/regulatory/transaction-reporting`                                                                       |
| Best-execution evidence              | `/services/regulatory/best-ex-evidence`                                                                            |
| Supervisory-artifact index           | `/services/regulatory/supervisory-artifacts`                                                                       |
| Shared reporting walkthrough         | (see [`../shared-core/client-reporting-demo-walkthrough.md`](../shared-core/client-reporting-demo-walkthrough.md)) |

### pb3b — Investment Management Demo ([`../experience/investment-management-demo.md`](../experience/investment-management-demo.md))

| Walkthrough section              | Route                                                                         |
| -------------------------------- | ----------------------------------------------------------------------------- |
| Strategy catalogue (IM-filtered) | `/services/strategy-catalogue` (IM profile applied)                           |
| Positions + P&L                  | `/services/trading/positions`, `/services/trading/pnl`                        |
| Allocator-side NAV / fee accrual | `/services/investment-management/nav`, `/services/investment-management/fees` |
| Reconciliation + audit trail     | `/services/reports/reconciliation`, `/services/reports/audit-trail`           |
| Shared reporting walkthrough     | See shared-core doc                                                           |

### pb3c — DART Demo ([`../experience/dart-demo.md`](../experience/dart-demo.md))

#### Signals-only walkthrough

| Walkthrough section         | Route                                                              |
| --------------------------- | ------------------------------------------------------------------ |
| Strategy catalogue (scoped) | `/services/strategy-catalogue` (signals-only profile applied)      |
| Strategy-service entry      | `/services/strategy-service`                                       |
| Execution + reconciliation  | `/services/execution/terminal`, `/services/reports/reconciliation` |
| Reporting surface           | `/services/reports/overview`                                       |
| LOCKED-VISIBLE research     | `/services/research/*` (locked; upgrade overlay)                   |

#### Full-pipeline walkthrough

| Walkthrough section     | Route                                    |
| ----------------------- | ---------------------------------------- |
| Research surface        | `/services/research`                     |
| Promote-pipeline ledger | `/services/strategy-catalogue/promote`   |
| Paper-trading view      | `/services/trading/terminal?phase=paper` |
| Strategy-service entry  | `/services/strategy-service`             |
| Execution + reporting   | As signals-only                          |

## Cross-playbook shared routes

Routes referenced by multiple playbooks:

| Route                              | Playbooks that reference it                    |
| ---------------------------------- | ---------------------------------------------- |
| `/services/reports/overview`       | pb3a, pb3b, pb3c — rule 03 same-system surface |
| `/services/strategy-catalogue`     | pb2a, pb2b, pb3b, pb3c                         |
| `/services/trading/positions`      | pb3a, pb3b, pb3c                               |
| `/services/reports/reconciliation` | pb3a, pb3b, pb3c                               |
| `/services/reports/audit-trail`    | pb3a, pb3b, pb3c                               |

## Routes that should NOT exist (rule 03 enforcement)

Any route matching these patterns is a rule-03 violation and should be consolidated:

- `/im-reporting/*`, `/dart-reporting/*`, `/reg-reporting/*` — audience-prefixed routes.
- `/research/backtests/*`, `/paper-trading/*`, `/backtest/*` — phase-prefixed top-level routes.
- `*-research.tsx`, `*-backtest.tsx` — phase-named component files.

Stage 3E's refactor plan reads this list for consolidation targets.

## Stage 3E refactor hooks

When Stage 3E refactor lands, this doc updates in the same PR to reflect the new route names. Any Playwright spec
referencing the old route is updated in the same PR.

## Cross-references

- [`../experience/`](../experience/) — each playbook references routes
- [playbook-to-qa-coverage.md](playbook-to-qa-coverage.md) — Playwright specs test the routes
- [persona-and-user-prototype-mapping.md](persona-and-user-prototype-mapping.md) — who signs in for each route
- [../shared-core/same-system-principle.md](../shared-core/same-system-principle.md) — rule 03 implementation
- [../shared-core/shared-reporting-core.md](../shared-core/shared-reporting-core.md) — shared route per audience
- [../infra-spec/stage-3c-derivation-engine.md](../../16-strategy-playbooks/infra-spec/stage-3c-derivation-engine.md) —
  derivation per route
