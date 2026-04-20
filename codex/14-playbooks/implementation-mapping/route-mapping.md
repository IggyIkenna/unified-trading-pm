---
scope: [engineer, admin, sales]
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

| Walkthrough section                          | Route                                                                                                          |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Home-page frame                              | `/` (public)                                                                                                   |
| Three service tiles (DART, IM, Reg Umbrella) | `/services/dart`, `/services/investment-management`, `/services/regulatory-umbrella` (public descriptor pages) |
| Bottom CTA booking flows                     | `/book/dart`, `/book/im`, `/book/regulatory-umbrella` (calendar integration)                                   |

### pb2 — Briefings Hub ([`../experience/briefings-hub.md`](../experience/briefings-hub.md))

| Walkthrough section  | Route                                                                |
| -------------------- | -------------------------------------------------------------------- |
| Hub landing          | `/briefings` (light-auth gated)                                      |
| Three briefing cards | `/briefings/im`, `/briefings/dart`, `/briefings/regulatory-umbrella` |
| Second-call booking  | Calendar iframe embedded on briefing footer                          |

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
- [../infra-spec/stage-3c-derivation-engine.md](../infra-spec/stage-3c-derivation-engine.md) — derivation per route
