---

name: strategy-catalogue-3tier-surface-2026-04-21 overview: Rebuild Strategy Catalogue as a cross-cutting shared
primitive surfaced from admin + DART + IM + Reports with three tiers: Tier 1 (admin universe — every instance UAC
expresses), Tier 2 (admin routing + maturity-phase editor), Tier 3 (client view — Reality + FOMO split, with
subscription/allocation request CTA). Replaces the current single-surface `/services/strategy-catalogue` page. Depends
on Plan A (strategy lifecycle maturity model). type: ui epic: epic-code-completion status: active locked_by:
live-defi-rollout locked_since: 2026-04-21

completion_gates: code: C3 deployment: D0 business: none

repo_gates:

- repo: unified-trading-system-ui code: C0 deployment: D0 business: none
- repo: unified-trading-pm code: C0 deployment: none business: none

depends_on:

- strategy_lifecycle_maturity_model_2026_04_21
- dashboard_services_grid_collapse_2026_04_21

# ────────────────────────────────────────────────────────────────────────────

# CONTEXT

# ────────────────────────────────────────────────────────────────────────────

#

# User directive 2026-04-21: Strategy Catalogue is a cross-cutting primitive,

# not a DART sub-route. Three tiers with different viewModes:

#

# Tier 1 — Admin universe (read-only)

# Surface: /services/admin/strategy-universe

# Shows: every UAC-expressed instance (5-dim: family × archetype × venue-set ×

# instrument-type-set × share-class), ~200-300 entries post-Plan-A

# Affordances: filter/search/sort; no mutations; shows current maturity phase

# + product routing + odum-paper run status for each row

#

# Tier 2 — Admin routing + maturity editor

# Surface: /services/admin/strategy-lifecycle-editor

# Shows: same universe, but each row is editable

# Affordances: change maturity phase (forward-only + retire), change product

# routing, bulk-edit via filter+apply, audit-log per change

# Backend: PATCH /api/v1/registry/strategy-instances/{id}/lifecycle (Plan A)

#

# Tier 3 — Client view (Reality + FOMO)

# Surface: /services/strategy-catalogue (shared for DART + IM clients)

# Two tabs:

# "Your Subscriptions" (Reality) — only instances this org subscribes to;

# rendered as tile grid with live P&L + allocation info.

# "Explore" (FOMO) — instances available via product routing to this org's

# tier but NOT yet subscribed; rendered as tearsheet teaser cards with

# backtest/paper/live overlay (from odum-paper series) + "Request

# allocation" CTA.

# Gates: filter by FamilyArchetypePicker + venue-set + share-class; admin

# sees all, clients see scoped subset.

#

# Shared primitive:

# <StrategyCatalogueSurface viewMode={"admin-universe"|"admin-editor"|"client-reality"|"client-fomo"} />

# Single component, three views = prop value. Invoked from admin + DART +

# IM + Reports.

#

# Orphan-audit compliance:

# Current /services/strategy-catalogue page stays reachable (becomes the

# default Tier 3 view). Admin tiers accessible from Admin & Ops tile sub-

# routes. No orphaned pages.

#

# ────────────────────────────────────────────────────────────────────────────

todos:

# ──────────────────────────────────────────────────────────────────────

# PHASE 1 — Shared primitive (SEQUENTIAL, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p1-strategy-catalogue-surface-component content: |
  - [ ] [AGENT] P0. Create `components/strategy-catalogue/StrategyCatalogueSurface.tsx`: Props:
        `{ viewMode: "admin-universe"|"admin-editor"|"client-reality"|"client-fomo",               filter?: StrategyCatalogueFilter,               onInstanceSelect?: (id: string) => void }`.
        Renders a virtualised grid (~300 rows admin; scoped subset client-side). Per-row: family+archetype label,
        venue-set variant chip, maturity-phase badge (from Plan A enum), product-routing badge, live P&L spark (from
        odum-paper series), allocation-status badge (Tier 3 only). Integrates `<FamilyArchetypePicker>` at top +
        venue-set + share-class pickers + maturity-phase filter + product-routing filter. status: pending

- id: p1-strategy-catalogue-filter-types content: |
  - [ ] [AGENT] P0. Add `lib/architecture-v2/catalogue-filter.ts` — typed filter state
        `{family?, archetype?, venue_set_variant?, share_class?,     maturity_phase?, product_routing?, allocation_status?}`.
        URL-serializable for deep-links. Syncs with existing DashboardFilterContext (Plan
        dashboard_services_grid_collapse Phase 4) when mounted under /dashboard. status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 2 — Admin tiers (SEQUENTIAL after Phase 1, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p2-admin-universe-page content: |
  - [ ] [AGENT] P0. Create `app/(ops)/admin/strategy-universe/page.tsx` — mounts
        `<StrategyCatalogueSurface viewMode="admin-universe" />`. Read- only catalogue of all ~300 instances. Link from
        Admin & Ops tile sub-route "Strategy Universe". status: pending

- id: p2-admin-editor-page content: |
  - [ ] [AGENT] P0. Create `app/(ops)/admin/strategy-lifecycle-editor/page.tsx` — mounts
        `<StrategyCatalogueSurface viewMode="admin-editor" />`. Each row has inline editors for `maturity_phase` +
        `product_routing`, posts to the Plan A PATCH endpoint. Bulk-edit via selection + apply. Audit toast with "undo
        5s" affordance. status: pending

- id: p2-admin-sub-routes content: |
  - [ ] [AGENT] P0. Extend `SERVICE_REGISTRY` admin tile sub-routes to add `strategy-universe` +
        `strategy-lifecycle-editor`. Update `persona-dashboard-shape.ts` — visible to `admin` + `internal-trader`
        (editor); `im-desk-operator` gets read-only `strategy-universe` access. status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 3 — Client Tier 3 (SEQUENTIAL after Phase 2, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p3-client-catalogue-two-tab-layout content: |
  - [ ] [AGENT] P0. Rewrite `app/(platform)/services/strategy-catalogue/page.tsx` as a two-tab surface: "Your
        Subscriptions" (`viewMode="client-reality"`) + "Explore" (`viewMode="client-fomo"`). Tab persistence via URL
        `?tab=reality|explore`. Default: Reality tab if user has ≥1 subscribed instance, else Explore. status: pending

- id: p3-fomo-tearsheet-cards content: |
  - [ ] [AGENT] P0. `components/strategy-catalogue/FomoTearsheetCard.tsx` — renders per-instance in the Explore tab:
        header (family/archetype/venue- set/share-class), backtest+paper+live overlay chart (uses Plan C
        `<PerformanceOverlay>`), key stats (Sharpe/MDD/CAGR from odum-paper series), "Request allocation" CTA (POSTs to
        allocation-requests collection). CTA gated by product-routing. status: pending

- id: p3-reality-position-cards content: |
  - [ ] [AGENT] P0. `components/strategy-catalogue/RealityPositionCard.tsx` — per-subscribed-instance: live P&L, current
        allocation, venues actively executing, maturity-phase badge. Drill-through to DART terminal + Reports
        attribution for that instance. status: pending

- id: p3-orphan-audit-preserve-route content: |
  - [ ] [AGENT] P0. Confirm `/services/strategy-catalogue` route remains mounted (was a DART sub-route chip; now the
        Tier 3 page). Update DART tile's `strategy-catalogue` chip in `services.ts` to point at this same URL — no
        orphan. Chip label changes to "Catalogue" (shorter). status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 4 — Tile cross-wiring (SEQUENTIAL after Phase 3, P1)

# ──────────────────────────────────────────────────────────────────────

- id: p4-dashboard-dart-chip-wiring content: |
  - [ ] [AGENT] P1. DART tile sub-route chip now surfaces Tier 3 client view (no change — same URL). Confirm
        persona-dashboard-shape keeps the chip visible for DART personas only. status: pending

- id: p4-dashboard-im-access content: |
  - [ ] [AGENT] P1. Add `strategy-catalogue` access for IM personas (`client-im-pooled`, `client-im-sma`). Option: add
        `strategy-catalogue` chip to Investor Relations tile OR Reports tile (TBD — user preference check during
        implementation). My lean: Reports tile chip "Catalogue" linking to `/services/strategy-catalogue?tab=explore` so
        IM clients land on the tearsheet view. status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 5 — Tests + QG (SEQUENTIAL, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p5-catalogue-surface-tests content: |
  - [ ] [AGENT] P0. `__tests__/strategy-catalogue-surface.test.tsx`: per-viewMode rendering (admin-universe read-only,
        admin-editor has editors, client-reality hides unsubscribed, client-fomo hides subscribed). Filter cascade
        tests. status: pending

- id: p5-fomo-cta-gating-test content: |
  - [ ] [AGENT] P0. Verify FOMO "Request allocation" CTA only enabled when instance's product-routing permits this org's
        tier, and maturity ≥ `paper_stable` (don't offer allocation on smoke/minimal). status: pending

- id: p5-qg-final content: |
  - [ ] [SCRIPT] P0. UI typecheck + full test suite + PM codex compliance gates green. status: pending

# ──────────────────────────────────────────────────────────────────────

# PHASE 6 — Codex SSOT (PARALLEL with Phases 1-5)

# ──────────────────────────────────────────────────────────────────────

- id: p6-codex-strategy-catalogue-3tier-doc content: |
  - [x] [AGENT] P1. Create `codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md`: 3 tiers + per-persona
        view-mode matrix + Reality/FOMO split rationale + allocation-request flow. Cross-ref
        dashboard-services-grid.md + strategy-lifecycle-maturity.md. status: done

- id: p6-amend-dashboard-grid-codex content: |
  - [ ] [AGENT] P1. Amend `dashboard-services-grid.md` §2.1 DART sub- routes — clarify `strategy-catalogue` chip is a
        link to the shared Tier-3 primitive, not a DART-exclusive page. Add §2.5 admin sub- route update + §3
        persona-matrix update for Tier 3 access scope. status: pending

# ────────────────────────────────────────────────────────────────────────────

# SUCCESS CRITERIA

# ────────────────────────────────────────────────────────────────────────────

# - <StrategyCatalogueSurface> renders 4 view modes correctly

# - Admin universe + editor pages ship, admin tile chips link to them

# - Client strategy-catalogue has Reality + FOMO tabs; FOMO tearsheets show

# backtest+paper+live overlay sourced from odum-paper

# - /services/strategy-catalogue stays reachable (orphan-audit compliant)

# - Per-persona viewMode matrix matches codex SSOT

# - Allocation-request CTA respects product-routing + maturity-phase gates

# ────────────────────────────────────────────────────────────────────────────
