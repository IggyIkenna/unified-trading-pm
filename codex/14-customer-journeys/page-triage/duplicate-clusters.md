---
doc_type: codex-ssot
title: Duplicate clusters
summary:
  Ten overlap clusters where multiple unified-trading-system-ui routes serve one concept (strategy-catalogue legacy,
  data gaps/completeness/missing, reports-vs-observe reconciliation, IR site-navigation, ...) each with a merge-into /
  keep-separate / defer decision.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [ui, duplicate, page-triage, refactor, consolidation, navigation]
related:
  [/codex/14-customer-journeys/page-triage/triage-matrix.md, /codex/14-customer-journeys/page-triage/partial-archive.md]
created: 2026-04-19
authoritative_for: [UI duplicate-route cluster merge decisions]
referenced_by:
  [
    /codex/14-customer-journeys/README.md,
    /codex/14-customer-journeys/page-triage/README.md,
    /codex/14-customer-journeys/page-triage/triage-matrix.md,
    /codex/14-customer-journeys/playbooks/01-marketing-pre-first-call.md,
    /codex/14-customer-journeys/roadmap/plan-references.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3a-current-infra-audit.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Duplicate clusters

Overlap groups where multiple routes serve the same concept. Each cluster gets a merge decision.

## 1. Strategy catalogue legacy vs canonical

- **Legacy**: `/services/research/strategy/catalog`, `/services/research/strategy/catalog/[strategyId]`,
  `/services/research/strategy/families`, `/services/research/strategy/families/[family]`,
  `/services/research/strategy/overview`
- **Canonical**: `/services/strategy-catalogue/` tree (Phase 10 shipped 2026-04-19)
- **Decision**: `merge-into:/services/strategy-catalogue`. Legacy routes redirect. Phase 10.6 of the
  strategy-architecture-v2 finalization plan handles this.
- **Status**: in flight — not this plan's scope. This plan wires the canonical route from Spaces dropdown.

## 2. Strategy allocator split (Phase 10.7)

- Route: `/services/research/strategy/allocator`
- **Decision**: `defer` — Phase 10.7 of the strategy-architecture-v2 finalization plan splits this into IM-side +
  DART-side pages. Don't touch here.

## 3. Data gaps / completeness / missing

- Routes: `/services/data/gaps`, `/services/data/completeness`, `/services/data/missing`
- Same concept (data availability gaps) from three angles
- **Decision**: `merge-into:/services/data/gaps` with tabs inside the page. Content from completeness + missing folds
  into gaps as sub-views.

## 4. Trading strategies vs strategy catalogue

- `/services/trading/strategies`, `/services/trading/strategies/[id]`, `/services/trading/strategies/basis-trade`,
  `/services/trading/strategies/grid`, `/services/trading/strategies/model-portfolios`,
  `/services/trading/strategies/staked-basis`
- **Decision**: `merge-into:/services/strategy-catalogue/strategies/[archetype]/[slot]`. Trading service shows
  "strategies I'm actively running" as a filter on strategy-catalogue, not a separate surface.

## 5. Admin users in unified-ui vs user-management-ui

- `(ops)/admin/users/*` (in unified-trading-system-ui) vs entire user-management-ui repo
- **Decision**: per user directive, `keep-separate`. Document both. user-management-ui may never be publicly deployed;
  unified-trading-system-ui has admin surfaces for Odum ops use.

## 6. Public service pages vs marketing static

- React routes: `/services/backtesting`, `/services/data` (public), `/services/investment`, `/services/platform`
  (public), `/services/regulatory`
- Marketing static: `/investment-management`, `/platform`, `/regulatory`
- **Decision**: `merge-into` the marketing static equivalents for all except `/services/regulatory` (which is linked
  from footer). The React public routes either (a) render the same marketing HTML, or (b) are redundant and redirect.

## 7. Observe audit cluster

- `/services/observe/event-audit`, `/services/observe/reconciliation`, `/services/observe/recovery`,
  `/services/observe/registry`
- All touch audit-adjacent concerns
- **Decision**: `merge-into:/services/observe/health` with tabs. Health becomes the single "observability landing" with
  sub-tabs for audit, recon, recovery, registry.

## 8. Reports reconciliation vs Observe reconciliation

- `/services/reports/reconciliation` AND `/services/observe/reconciliation`
- Same noun, different owners
- **Decision**: Authority = Reports (client-facing). Observe reconciliation becomes an internal ops-audit view only.
  Keep both but rename the observe one to `/services/observe/reconciliation-ops` for clarity. (Or
  `merge-into:/services/reports/reconciliation` with an ops filter.)

## 9. Investor Relations site-navigation vs landing

- `/investor-relations/site-navigation` vs `/investor-relations`
- The site-nav page is redundant — it's just a list of links that the landing covers.
- **Decision**: `merge-into:/investor-relations`. Delete site-navigation route.

## 10. Onboarding vs signup

- `/onboarding` vs `/signup`
- Overlap in post-signup flow
- **Decision**: `defer`. Both exist in early-stage form; will consolidate as part of pb3 demo-provisioning plan.

## Cross-cluster principle

When merging, if the destination route is a HUB (per triage matrix), tabs can be added cheaply via the service-tabs.tsx
pattern. When the destination is a LINKED route, a full page redesign may be needed — flag in the merge action for the
per-cluster follow-up plan.

## Related

- Triage matrix: [triage-matrix.md](triage-matrix.md)
- Partial-archive (IR presentations): [partial-archive.md](partial-archive.md)
- Phase 10.6/10.7 of strategy architecture v2: see MEMORY.md "Strategy Architecture v2 — finalization"
