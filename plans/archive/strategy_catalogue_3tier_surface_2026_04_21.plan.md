---
doc_type: plan
title: ────────────────────────────────────────────────────────────────────────────
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

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

# Surface: /admin/strategy-universe

# Shows: every UAC-expressed instance (5-dim: family × archetype × venue-set ×

# instrument-type-set × share-class), 84 entries at Plan A seed, ~200-300

# post-expansion.

# Affordances: filter/search/sort; no mutations; shows current maturity phase

# + product routing + odum-paper run status for each row

#

# Tier 2 — Admin routing + maturity editor

# Surface: /admin/strategy-lifecycle-editor

# Shows: same universe, but each row is editable

# Affordances: change maturity phase (forward-only + retire), change product

# routing, bulk-edit via filter+apply, audit-log per change

# Backend: PATCH /api/v1/registry/strategy-instances/{id}/lifecycle (Plan A Phase 3)

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
  - [x] [AGENT] P0. Create `components/strategy-catalogue/StrategyCatalogueSurface.tsx`: shared 4-viewMode primitive.
        Reads the real 84-instance 5-dim catalogue from `lib/registry/ui-reference-data.json` via
        `loadStrategyCatalogue()`. Integrates `<FamilyArchetypePicker>`. Maturity + routing hash-synthesised until Plan
        A Phase 3 Firestore lifecycle doc ships. status: done

- id: p1-strategy-catalogue-filter-types content: |
  - [x] [AGENT] P0. `lib/architecture-v2/catalogue-filter.ts` — typed filter state URL-serialisable for deep-links.
        Shipped with `serialiseCatalogueFilter` / `parseCatalogueFilter` / `matchesFilter` helpers +
        `EMPTY_CATALOGUE_FILTER` constant. status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 2 — Admin tiers (SEQUENTIAL after Phase 1, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p2-admin-universe-page content: |
  - [x] [AGENT] P0. Create `app/(ops)/admin/strategy-universe/page.tsx` mounting
        `<StrategyCatalogueSurface viewMode="admin-universe" />`. Read-only catalogue of 84 (Plan A seed) → ~300
        instances. Linked from Admin & Ops tile sub-route "Strategy Universe". status: done

- id: p2-admin-editor-page content: |
  - [x] [AGENT] P0. Create `app/(ops)/admin/strategy-lifecycle-editor/page.tsx` mounting
        `<StrategyCatalogueSurface viewMode="admin-editor" />`. Inline editor buttons rendered but disabled with tooltip
        "Enabled when Plan A Phase 3 PATCH endpoint ships". PATCH wiring deferred to follow-up
        `p2-followup-enable-editor`. status: done

- id: p2-followup-enable-editor content: |
  - [x] [AGENT] P1. Enable inline `maturity_phase` + `product_routing` dropdowns, wire
        `PATCH /api/v1/registry/strategy-instances/{id}/lifecycle`, add audit toast on
        `/admin/strategy-lifecycle-editor`. status: done notes: | Shipped across 3 commits on live-defi-rollout: UTA
        `3d9b96e` (added 2 GET endpoints + 4 tests, 14/14 pass), UI `8962928` (new `useLifecycleEditor` hook +
        `AdminEditorGrid` with live `<select>` dropdowns + optimistic update + sonner toast + error rollback + 11 new
        tests). Forward-only transitions enforced client-side via `isValidMaturityTransition` helper (mirror of UAC
        `lifecycle.py`); server re-validates and rolls back on reject. Bulk-edit + 5-second-undo affordance deferred as
        `p2-followup-bulk-edit` — current impl toasts but has no undo button (sonner default 5s dismiss). Rows without a
        server-side lifecycle record stay disabled with tooltip prompting seed.

- id: p2-followup-bulk-edit content: |
  - [x] [AGENT] P2. Bulk-edit bar lives above the editor grid — checkbox per row + "select all" header checkbox, target
        maturity + routing `<select>`s, "Apply to N" button. Runs concurrent PATCHes via `bulkApply(ids, body)` with a
        worker-pool cap of 5 parallel. Each per-row success raises a 5-second-undo sonner toast with an actual Undo
        button that issues a reverse PATCH restoring prior maturity / routing. Failures surface aggregated in the error
        toast with a console.error breakdown. status: done

- id: p2-admin-sub-routes content: |
  - [x] [AGENT] P0. Extend `SERVICE_REGISTRY` admin tile sub-routes with `strategy-universe` +
        `strategy-lifecycle-editor`. `persona-dashboard-shape.ts` updated — `admin` + `internal-trader` see both;
        `im-desk-operator` gets read-only `strategy-universe`. status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 3 — Client Tier 3 (SEQUENTIAL after Phase 2, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p3-client-catalogue-two-tab-layout content: |
  - [x] [AGENT] P0. Rewrite `app/(platform)/services/strategy-catalogue/page.tsx` as a two-tab surface: "Your
        Subscriptions" (`viewMode="client-reality"`) + "Explore" (`viewMode="client-fomo"`). Default: Reality if the org
        has ≥1 subscribed instance, else Explore. Subscriptions keyed on `instanceId`. status: done

- id: p3-fomo-tearsheet-cards content: |
  - [x] [AGENT] P0. `components/strategy-catalogue/FomoTearsheetCard.tsx` — per-instance header (family / archetype /
        venue-set / share-class), `<PerformanceOverlayPlaceholder>` (prop shape matches Plan C `<PerformanceOverlay>`
        for 1-line swap), key stats (Sharpe / MDD / CAGR synthesised until Plan C `odum-paper` series wires in),
        "Request allocation" CTA gated by `allowsAllocationCta(maturity_phase)`. status: done

- id: p3-reality-position-cards content: |
  - [x] [AGENT] P0. `components/strategy-catalogue/RealityPositionCard.tsx` — per-subscribed-instance live P&L,
        allocation, active venues, maturity badge; drill-through to DART terminal + Reports attribution. status: done

- id: p3-orphan-audit-preserve-route content: |
  - [x] [AGENT] P0. `/services/strategy-catalogue` route stays mounted. DART tile `strategy-catalogue` chip label
        renamed to "Catalogue" via Phase 4. `npm run orphan-audit -- --blocking` exits 0 (221/208 reachable with the 2
        new admin pages, 0 new orphans). status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 4 — Tile cross-wiring (SEQUENTIAL after Phase 3, P1)

# ──────────────────────────────────────────────────────────────────────

- id: p4-dashboard-dart-chip-wiring content: |
  - [x] [AGENT] P1. DART tile `strategy-catalogue` chip relabelled "Catalogue" in `lib/config/services.ts`; still points
        at `/services/strategy-catalogue` (same URL — no orphan). DART personas keep the chip visible via existing
        `PERSONA_SUBROUTE_SHAPES` entries. status: done

- id: p4-dashboard-im-access content: |
  - [x] [AGENT] P1. Reports tile gains a new "Catalogue" chip linking to `/services/strategy-catalogue?tab=explore`.
        `client-im-pooled` + `client-im-sma` personas get the chip visible under `reports.catalogue`. IM clients land on
        the FOMO tearsheet view directly from Reports. status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 5 — Tests + QG (SEQUENTIAL, P0)

# ──────────────────────────────────────────────────────────────────────

- id: p5-catalogue-surface-tests content: |
  - [x] [AGENT] P0. `tests/unit/components/strategy-catalogue/strategy-catalogue-surface.test.tsx`: per-viewMode
        rendering (admin-universe read-only, admin-editor buttons disabled, client-reality hides unsubscribed,
        client-fomo hides subscribed) + family/archetype filter cascade. 5 tests, all green. status: done

- id: p5-fomo-cta-gating-test content: |
  - [x] [AGENT] P0. `tests/unit/components/strategy-catalogue/fomo-cta-gating.test.tsx`: `allowsAllocationCta` enables
        only for `paper_stable` / `live_early` / `live_stable`; exhaustive across every maturity phase.
        `<FomoTearsheetCard>` CTA disabled below paper_stable, disabled without handler, disabled on retired. 6 tests,
        all green. status: done

- id: p5-qg-final content: |
  - [x] [SCRIPT] P0. `cd unified-trading-system-ui && npx tsc --noEmit` clean for Plan-B files (remaining 17 errors are
        pre-existing, unrelated). `npm run orphan-audit -- --blocking` exits 0. `CI=true npm test -- --run` 975/976
        green — single flake (trading-data `getLiveBatchDelta` 5-second timeout under parallel load) unrelated and
        passes deterministic when run in isolation. status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 6 — Codex SSOT (PARALLEL with Phases 1-5)

# ──────────────────────────────────────────────────────────────────────

- id: p6-codex-strategy-catalogue-3tier-doc content: |
  - [x] [AGENT] P1. `/codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md` — 3 tiers + per-persona matrix +
        Reality/FOMO split + allocation-request flow. §9 amended post-Plan-A-Phase-2 from "scaffold handoff" to "data
        wiring" documenting catalogue/variants/enums live + maturity/routing synthesised + Plan-C overlay pending.
        status: done

- id: p6-amend-dashboard-grid-codex content: |
  - [x] [AGENT] P1. `dashboard-services-grid.md` §4.5 already documents the cross-cutting primitive; admin paths updated
        `/services/admin/...` → `/admin/...` to match the actual `(ops)` group routing. status: done

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
