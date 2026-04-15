---
title: "Responsive Zoom Pass — 100%→200% Graceful Degradation"
created: 2026-03-23
status: done
locked_by: live-defi-rollout
locked_since: 2026-03-23
priority: P1
---

# Responsive Zoom Pass — Every Page 100%→200%

## Context

At 100% zoom the lifecycle nav overflows. At 200% zoom, text disappears instead of shrinking to icons. The principle:
**every page must work from 100% to 200% zoom**. Components should gracefully degrade — labels shrink to icons, grids
collapse to stacks, tables become scrollable, dropdowns stay accessible.

## Principle

- At standard width: full labels + descriptions
- At medium width: labels only (no descriptions)
- At narrow/zoomed: icons only with tooltips
- Never disappear — always accessible via icon or collapsed menu
- Tables: horizontal scroll, sticky first column
- Cards: stack vertically
- KPI grids: reduce columns (4→2→1)

## Phase 1: Shell Components (PARALLEL)

- [x] [AGENT] P0. **lifecycle-nav.tsx** — stage labels `hidden md:inline`, icon-only below md, org name
      `hidden lg:inline`, search label `hidden sm:inline`
- [x] [AGENT] P0. **breadcrumbs.tsx** — scope filters wrap below breadcrumbs at narrow widths (`flex-wrap`), breadcrumb
      text truncates
- [x] [AGENT] P0. **service-tabs.tsx** — tabs scroll horizontally at narrow widths, `overflow-x-auto`, right slot wraps
      below
- [x] [AGENT] P0. **debug-footer.tsx** — footer items wrap, persona name `hidden sm:inline`
- [x] [AGENT] P0. **notification-bell.tsx** — badge count stays visible, dropdown positions correctly at edges

## Phase 2: Platform Components (PARALLEL)

- [x] [AGENT] P0. **batch-live-rail.tsx** — pipeline stages shrink: labels `hidden lg:inline`, show numbered dots below
      lg, toggle stays full
- [x] [AGENT] P0. **global-scope-filters.tsx** — filter labels `hidden md:inline`, icon-only below md, dropdown trigger
      shows icon + count badge
- [x] [AGENT] P0. **filter-bar.tsx** — filters wrap into rows, search shrinks
- [x] [AGENT] P0. **live-asof-toggle.tsx** — date input `hidden sm:inline`, presets `hidden md:inline`
- [x] [AGENT] P0. **candidate-basket.tsx** — basket items stack vertically at narrow

## Phase 3: Trading Pages (PARALLEL)

- [x] [AGENT] P1. **trading/overview** — KPI grid 5→3→2→1 columns, strategy table horizontal scroll, bottom panel grid
      4→2→1
- [x] [AGENT] P1. **trading/terminal** — resizable panels collapse to stack at narrow, order entry below chart, order
      book horizontal scroll
- [x] [AGENT] P1. **trading/positions** — table horizontal scroll with sticky instrument column
- [x] [AGENT] P1. **trading/orders** — table horizontal scroll with sticky order ID
- [x] [AGENT] P1. **trading/pnl** — chart container respects container width, tabs wrap
- [x] [AGENT] P1. **trading/layout** — sidebar collapses at narrow widths (already `collapsible`)

## Phase 4: Data/Research/Execution/Observe Pages (PARALLEL)

- [x] [AGENT] P1. **data/coverage** — matrix table horizontal scroll, filter row wraps
- [x] [AGENT] P1. **data/venues** — venue cards 3→2→1 columns
- [x] [AGENT] P1. **data/missing** — table horizontal scroll
- [x] [AGENT] P1. **research/ml** pages — tab lists wrap, experiment tables scroll
- [x] [AGENT] P1. **execution/overview** — KPI grid 6→3→2, venue matrix scrolls
- [x] [AGENT] P1. **observe/risk** — risk cards stack, stress table scrolls, greeks grid 4→2

## Phase 5: Reports/Manage/Admin (PARALLEL)

- [x] [AGENT] P2. **reports/overview** — attribution waterfall stacks
- [x] [AGENT] P2. **manage/clients** — client detail tabs wrap, onboarding checklist stacks
- [x] [AGENT] P2. **admin** — KPI grid reduces columns, tables scroll

## Phase 6: Dashboard + Public Pages

- [x] [AGENT] P2. **dashboard** — service cards 4→2→1 columns, KPIs stack
- [x] [AGENT] P2. **login** — persona cards 2→1 column
- [x] [AGENT] P2. **landing** — hero sections stack, feature grids reduce

## Success Criteria

- [ ] All 81 smoke test pages pass at 200% zoom (Playwright viewport 640x480)
- [ ] No horizontal overflow on any page at 100% zoom on 1920px viewport
- [ ] No text clipped or invisible at 150% zoom
- [ ] All interactive elements (buttons, dropdowns, inputs) remain clickable at 200%
- [ ] Lighthouse mobile score > 80 on all pages
