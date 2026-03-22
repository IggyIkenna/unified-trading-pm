---
title: UI Routing Refactor & Navigation Consistency
type: code
status: done
priority: P1
repo: unified-trading-system-ui
locked_by: null
locked_since: null
---

# UI Routing Refactor & Navigation Consistency

## Context

Full audit of unified-trading-system-ui revealed 14 routing/navigation issues:

- **URL prefix inconsistencies**: `/manage/*`, `/health`, `/compliance` sit outside the `/service/{service}/{page}`
  convention
- **Duplicate routes**: Execution exists under both `/service/research/execution/` and `/service/execution/`
- **Orphaned routes**: `/data`, `/trading/promotions`, `/client-portal/[org]`, `/portal/*`, `/strategies/` — unreachable
  or dead code
- **Missing pages/layouts**: `/service/reports/settlement`, `/service/research/strategy/overview`, execution & ML
  layouts
- **Navigation flow breaks**: Going deeper into a service jumps to a different URL prefix (e.g., Build→Run changes
  `/research/` to `/execution/`)
- **Admin vs internal visibility**: Internal traders currently see everything admin sees — future: add admin-only gates

### Target URL Structure

```
/service/data/*             ← Acquire
/service/research/*         ← Build (ML, strategy, quant)
/service/execution/*        ← Execution (consolidated — used in Build + Run tabs)
/service/trading/*          ← Run (positions, orders, accounts, markets)
/service/observe/*          ← Observe (risk, alerts, news, strategy-health, system-health)
/service/manage/*           ← Manage (clients, mandates, fees, users, compliance)
/service/reports/*          ← Report (P&L, executive, settlement, reconciliation, regulatory)
/dashboard                  ← Command Center (kept as top-level shortcut)
```

### Dependency DAG

```
Phase 1 (prefix moves) ──┐
Phase 2 (execution)    ───┤
Phase 3 (delete orphans)──┼── Phase 7 (nav updates) ── Phase 8 (verify build)
Phase 4 (missing pages) ──┤
Phase 5 (strategies)   ───┤
Phase 6 (portal)       ───┘
```

Phases 1-6 are PARALLEL (independent file moves/deletes). Phase 7 depends on all of 1-6 (updates all nav links). Phase 8
depends on 7 (final verification).

---

## Phase 1: Fix Prefix Inconsistencies [PARALLEL]

Move routes that break the `/service/{service}/{page}` convention.

- [x] [AGENT] P0. Move `/manage/clients/page.tsx` → `/service/manage/clients/page.tsx`
- [x] [AGENT] P0. Move `/manage/mandates/page.tsx` → `/service/manage/mandates/page.tsx`
- [x] [AGENT] P0. Move `/manage/fees/page.tsx` → `/service/manage/fees/page.tsx`
- [x] [AGENT] P0. Move `/manage/users/page.tsx` → `/service/manage/users/page.tsx`
- [x] [AGENT] P0. Move `/manage/layout.tsx` → `/service/manage/layout.tsx`
- [x] [AGENT] P0. Move `/health/page.tsx` → `/service/observe/health/page.tsx`
- [x] [AGENT] P0. Move `/(ops)/compliance/page.tsx` → `/service/manage/compliance/page.tsx` (keep ops route as redirect)

## Phase 2: Consolidate Execution Routes [PARALLEL]

Execution pages exist under both `/service/research/execution/` and `/service/execution/`. Consolidate to
`/service/execution/` only.

- [x] [AGENT] P0. Verify `/service/execution/` pages cover all content from `/service/research/execution/` (algos,
      venues, tca, benchmarks)
- [x] [AGENT] P0. Delete `/service/research/execution/` directory (algos, venues, tca, benchmarks, candidates, handoff)
- [x] [AGENT] P0. Update BUILD_TABS "Execution Research" href from `/service/research/execution/algos` to
      `/service/execution/algos`
- [x] [AGENT] P0. Add execution layout `/service/execution/layout.tsx` with EXECUTION_TABS

## Phase 3: Delete Orphaned Routes [PARALLEL]

Routes with no navigation links and no known purpose.

- [x] [AGENT] P1. Delete `/(platform)/data/page.tsx` (shadows `/service/data/`)
- [x] [AGENT] P1. Delete `/(platform)/trading/promotions/page.tsx` (unknown purpose)
- [x] [AGENT] P1. Delete `/(platform)/client-portal/[org]/page.tsx` (unknown purpose)

## Phase 4: Create Missing Pages & Layouts [PARALLEL]

Pages referenced by nav tabs but missing from the filesystem.

- [x] [AGENT] P0. Create `/service/reports/settlement/page.tsx` (REPORTS_TABS references it)
- [x] [AGENT] P0. Create `/service/research/strategy/overview/page.tsx` (no overview page — users land on backtests)
- [x] [AGENT] P1. Create `/service/research/ml/layout.tsx` (missing layout for ML sub-nav)
- [x] [AGENT] P1. Wire `/service/observe/news/` and `/service/observe/strategy-health/` into OBSERVE_TABS display

## Phase 5: Integrate /strategies/ [PARALLEL]

Strategy grid/detail pages exist at `/strategies/` outside the lifecycle nav.

- [x] [AGENT] P1. Move `/strategies/page.tsx` → `/service/trading/strategies/page.tsx`
- [x] [AGENT] P1. Move `/strategies/grid/page.tsx` → `/service/trading/strategies/grid/page.tsx`
- [x] [AGENT] P1. Move `/strategies/[id]/page.tsx` → `/service/trading/strategies/[id]/page.tsx`
- [x] [AGENT] P1. Update `/dashboard` "View All" link to new path

## Phase 6: Deprecate Portal Routes [PARALLEL]

Portal is a parallel UI nobody can reach from main nav. Redirect to `/service/*`.

- [x] [AGENT] P2. Add redirect pages in `/portal/*` that redirect to corresponding `/service/*` routes
- [x] [AGENT] P2. Add redirect: `/portal/data` → `/service/data/overview`, `/portal/execution` →
      `/service/execution/overview`, etc.
- [x] [AGENT] P2. Keep `/portal/page.tsx` as a redirect to `/service/overview`

## Phase 7: Update Navigation Components [SEQUENTIAL — depends on 1-6]

Update all navigation links to match new routing.

- [x] [AGENT] P0. Update `lifecycle-nav.tsx` — change opsRoutes array from `["/manage", "/compliance"]` to
      `["/admin", "/ops", "/devops", "/config"]`; manage routes now under `/service/manage/`
- [x] [AGENT] P0. Update `service-tabs.tsx` — MANAGE_TABS hrefs from `/manage/*` to `/service/manage/*`; OBSERVE_TABS
      `/health` to `/service/observe/health`
- [x] [AGENT] P0. Update `lifecycle-mapping.ts` (if it contains route paths)
- [x] [AGENT] P0. Grep all pages for `href="/manage/` and `href="/health"` and `href="/strategies"` and update
- [x] [AGENT] P1. Update `(ops)/manage/` layout/pages to use `/service/manage/` links (or deprecate ops/manage as
      duplicate)

## Phase 8: Verify Build [SEQUENTIAL — depends on 7]

- [x] [AGENT] P0. Run `VITE_MOCK_API=true npx next build` and fix any broken imports/links
- [x] [AGENT] P0. Verify all pages render without 404s in dev mode
- [x] [AGENT] P1. Commit and push

---

## Future (Not This Plan)

- [x] [HUMAN] P3. Add admin-only gates (internal trader should not see all admin pages)
- [x] [HUMAN] P3. Add breadcrumb component showing Stage → Service → Page
- [x] [HUMAN] P3. Unify `/services/` (public, plural) and `/service/` (platform, singular) naming
