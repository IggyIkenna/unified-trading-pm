---
doc_type: codex-ssot
title: Same-System Principle — Implementation Map
summary:
  Implementation map pinning rule-03's five sub-claims (partitioned views, research≡live infra, terminal as live/batch
  toggle, catalogue phase tags, paper==live look) to concrete UI routes, services, and catalogue data — plus the
  anti-pattern grep signals (audience-prefixed routes, duplicate metric modules) that surface drift.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-trading-system-ui]
scope: [engineer, admin, sales]
tags: [same-system, ui, strategy, execution, catalogue, verification]
related:
  [
    ../_ssot-rules/03-same-system-principle.md,
    ../_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/shared-core/shared-reporting-core.md,
    /codex/14-customer-journeys/shared-core/client-reporting-demo-walkthrough.md,
  ]
created: 2026-04-20
authoritative_for: [same-system-principle implementation map (UI routes/services/anti-pattern greps)]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/experience/dart-demo.md,
    /codex/14-customer-journeys/experience/im-decision-journey.md,
    /codex/14-customer-journeys/implementation-mapping/route-mapping.md,
    /codex/14-customer-journeys/shared-core/README.md,
    /codex/14-customer-journeys/shared-core/client-reporting-demo-walkthrough.md,
    /codex/14-customer-journeys/shared-core/competitive-landscape.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Same-System Principle — Implementation Map

> Implementation map for [rule 03](../_ssot-rules/03-same-system-principle.md). Names the UI routes, component trees,
> services, and data bindings that make the rule-03 claim "one operating system, partitioned views" load-bearing rather
> than aspirational.

**Rule source:** [rule 03 — The same-system principle](../_ssot-rules/03-same-system-principle.md) **Derived identifiers
used by Stage 3:** `lifecycle_phase`, `maturity`, `component tree`, `access_control(user, route, item, phase)`

## Why this doc exists

Rule 03 declares five sub-claims: (a) partitioned-view audiences, (b) research ≡ live infrastructure, (c) trading
terminal as live/batch toggle over one component tree, (d) strategy catalogue rows carry phase tags, (e) paper trading
shares look-and-feel with live. Every claim is checkable against UI routes, service code, and the catalogue data model.
This doc pins each sub-claim to the concrete implementation surface. Drift surfaces through the grep patterns in
§Anti-patterns, not through review-time vigilance.

This is the SSOT for "same system, partitioned view." Experience docs cite this file; they do not restate the mechanism.

## The five sub-claims, pinned

### (a) Client surfaces are partitioned views, not separate products

DART, IM, and Reg Umbrella land on the same `/services/*` routes. The audience differs; the route does not. The
partition lives in the entitlement layer, not the route layer.

| Claim                      | Implementation                                                                                                                             |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| One reporting landing page | `/services/reports/overview` in `unified-trading-system-ui` — same page for IM, Reg Umbrella, DART; entitlement filter applied via persona |
| One positions / P&L view   | `/services/trading/pnl` + `/services/trading/positions`                                                                                    |
| One strategy catalogue     | `/services/strategy-catalogue/*` (Phase 10 landed)                                                                                         |
| One execution / TCA view   | `/services/execution/*`                                                                                                                    |
| Shared component tree      | `unified-trading-system-ui/components/` — no `im-reporting-*`, no `dart-reporting-*` forks                                                 |
| Persona-driven filter      | `lib/auth/personas.ts` persona fixtures + visibility-slicing lib; admin sees all, each demo persona sees the slice rule 06 specifies       |

**Violation signal:** any new repo or top-level route prefixed with an audience name (`im-*`, `dart-*`, `reg-*`).
Resolve by consolidating under `/services/*` with persona-scoped entitlements.

### (b) Research infrastructure ≡ live infrastructure

Every metric that appears in a research view is computed by the same service as the live metric. The service binds to
different data sources (historical vs live); the logic is identical.

| Metric / artifact  | Service that produces it (research + live)                                                                                                |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| P&L attribution    | `execution-service` attribution module — research binds to historical fills; live binds to matching-engine fills from `execution-service` |
| Exposure analytics | `features-*` exposure analytics — same computation, phase-tagged data source                                                              |
| Reconciliation     | `execution-service` reconciliation module — research simulates, live runs against venue feeds                                             |
| TCA                | `execution-service` TCA — research runs against matching-engine fills; live runs against actual                                           |

**Audit:** grep for any service that claims to compute "backtest attribution" or "paper P&L" separately from the live
attribution pipeline. Any duplicate logic is a rule-03 violation.

### (c) DART is a live/batch toggle over the same component tree

`/services/trading/terminal` accepts a `phase` prop / URL parameter. The component tree is identical across phases; the
data binding differs.

| Component       | Binding in research phase | Binding in live phase |
| --------------- | ------------------------- | --------------------- |
| Positions table | Historical positions      | Live positions        |
| Risk panel      | Historical risk           | Live risk             |
| Fills stream    | Matching-engine fills     | Venue fills           |
| Orders panel    | Matching-engine orders    | Venue order book      |

**Violation signal:** a separate `/research/backtester/` route that renders a distinct positions-table component.
Resolve by consolidating onto the terminal with a `phase` parameter.

### (d) Strategy catalogue rows carry phase tags

One catalogue, one row per slot. The row carries `phase` metadata (`research` / `paper` / `live`) and `maturity`
metadata (`CODE_NOT_WRITTEN` → `LIVE_ALLOCATED`). The UI filters by both but does not fork into phase-specific
catalogues.

Implementation reference: `unified-trading-system-ui/lib/architecture-v2/availability.ts` +
`lib/architecture-v2/availability-store.tsx` (Phase 10 landed). Catalogue row type carries both fields; the catalogue
route renders one list filtered by persona visibility.

**Violation signal:** separate `/catalogue/research/` and `/catalogue/live/` routes rendering different row sets.
Resolve by consolidating to one route with phase + maturity filtering.

### (e) Paper trading has same look-and-feel as live

Paper is a phase, not a product. The paper view lives at the same route as the live view; the only difference is the
execution-fill source.

| Surface       | Paper binding                         | Live binding   |
| ------------- | ------------------------------------- | -------------- |
| Terminal      | Matching-engine fills over live data  | Venue fills    |
| P&L dashboard | Same component, matching-engine fills | Venue fills    |
| Reporting     | Same component, paper flag            | Same component |

**Violation signal:** a `/paper-trading/*` route tree separate from `/services/*`. Resolve by merging under the
phase-aware `/services/*` routes.

## Phase and maturity are orthogonal

Two independent axes on every strategy slot. Rule 03 requires both to hold — the distinction is load-bearing, not
rhetorical.

| Dimension    | Values                                                                                                                             | Set by                                          |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Maturity** | CODE_NOT_WRITTEN → CODE_WRITTEN → CODE_AUDITED → BACKTESTED → PAPER_TRADING → PAPER_TRADING_VALIDATED → LIVE_TINY → LIVE_ALLOCATED | promote-pipeline watchdog in `strategy-service` |
| **Phase**    | research / paper / live                                                                                                            | user context (which view they've opened)        |

A `LIVE_ALLOCATED` slot can be opened in `research` phase by a researcher re-running it over historical data. Same slot,
same metadata, different phase view. The catalogue row is one row; the phase pill updates per view.

**Worked example** (from rule 03): `CARRY_BASIS_PERP/binance-perp/USDT` is `LIVE_ALLOCATED`. An analyst opens it in
research phase to study historical behaviour. A live trader opens the same slot in live phase. A QA engineer opens it in
paper phase. All three see the same catalogue row, the same metadata, the same components — each with their phase
binding applied.

## Orthogonality implications for Stage 3

Stage 3B's UAC combo registry declares `lifecycle_phase` as a named dimension on every block. Stage 3C's derivation
engine computes `access_control(user, route, item, phase)`: the same combo can be visible or not depending on phase
context. Block 11 (analytics packs) may scope differently per phase (research analytics vs live analytics) even when the
route is shared.

## Anti-patterns to grep for

Regular audit patterns. Any hit is a rule-03 drift signal.

- `im-reporting-*`, `dart-reporting-*`, `reg-reporting-*` — audience-name-prefixed routes or repos.
- `/research/backtests`, `/paper-trading/`, `/backtest/` — phase-prefixed top-level routes.
- Duplicate metric-computation modules: `research_attribution.py` + `live_attribution.py`, etc.
- UI components named `*BacktestTable`, `*PaperPositions`, `*ResearchChart`. Canonical form:
  `<PositionsTable phase={...}>`.
- Route files ending `-research.tsx` or `-backtest.tsx`. Consolidate to the phase-aware route.

## Relationship to rule 06

Rule 06 (show / don't-show discipline) is the visibility layer on top of the rule-03 surface. Rule 03 ensures there is
only one surface; rule 06 ensures each audience sees the right slice. The pair is commutative: without rule 03, rule 06
becomes a permission matrix over many products; without rule 06, rule 03's single surface leaks cross-audience data.

## Cross-references

- [rule 03 — same-system principle](../_ssot-rules/03-same-system-principle.md)
- [rule 06 — show / don't-show discipline](../_ssot-rules/06-show-dont-show-discipline.md)
- [../../09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md](../../09-strategy/TIER_ZERO_UI_DEMO_AND_PARITY.md) — prior codex
  SSOT on demo/live parity
- [../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md](../../09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md)
  — maturity ladder
- [shared-reporting-core.md](shared-reporting-core.md) — concrete implementation of claim (a) for reporting
- [client-reporting-demo-walkthrough.md](client-reporting-demo-walkthrough.md) — the shared walkthrough claim (a)
  generates
