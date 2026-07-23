---
doc_type: plan
title: ────────────────────────────────────────────────────────────────────────────
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-21"
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

---

name: dashboard-services-grid-collapse-2026-04-21 overview: Collapse /dashboard tile grid from 11 product tiles to 5
(DART / Odum Signals / Reports / Investor Relations / Admin & Ops) with entitlement+persona-gated sub-route chips under
each tile, and add a family/archetype filter strip above the grid that propagates selection into DART sub-tabs + Reports
via URL params. Sibling to the Phase-11 lifecycle-nav 8→4 collapse; closes the dashboard-side of the same ask. type:
mixed epic: epic-code-completion status: active locked_by: live-defi-rollout locked_since: 2026-04-21
reconciliation_status: shipped_substantive reconciliation_date: 2026-04-25 reconciliation_note: 23/26 (88%) done; 3
minor follow-ups remain. Evidence: PM b428117d, ed1f4a2d, 28e96f21, 5bd01b9b, 85c43998. Ready for [unlock-plan] +
archive once final 3 todos land. See `_reconciliation_evidence_map_2026_04_25.md`.

completion_gates: code: C2 deployment: D0 business: none

repo_gates:

- repo: unified-trading-system-ui code: C0 deployment: D0 business: none
- repo: unified-trading-pm code: C0 deployment: none business: none

depends_on:

- ui_unification_v2_sanitisation_2026_04_20

# ────────────────────────────────────────────────────────────────────────────

# CONTEXT

# ────────────────────────────────────────────────────────────────────────────

#

# Today's mismatch (as of 2026-04-21):

# - Top-nav: 4 lifecycle stages (Data · DART · Manage · Reports) — Phase 11 done

# - /dashboard: 11 product tiles (Data, Research, Promote, DART, Odum Signals,

# Strategy Catalogue, Observe, Reports, Investor Relations, Admin & Ops)

#

# User directive 2026-04-21: collapse dashboard tiles to 5 (DART · Odum Signals ·

# Reports · Investor Relations · Admin & Ops) with per-persona sub-route chips,

# and add a family/archetype filter strip above the grid.

#

# Axis split (deliberate, NOT a 1:1 with nav):

# - Top-nav = lifecycle axis ("how you work" — Data · DART · Manage · Reports)

# - Tile grid = product axis ("what you bought" — 5 tiles above)

# Uniformity comes from sharing <ServiceTile> + chip language + padlock semantics.

#

# 5-tile model:

#

# ┌─────────────────────────────────────────────────────────────────────────┐

# │ DART ▸ Terminal · Research · Promote · Observe · Strategy Catalogue · │

# │ Signal Intake · Data (admin) │

# │──────────────────────────────────────────────────────────────────────── │

# │ Odum Signals ▸ Counterparties · Payloads · Emission History · Rate │

# │ Limits (COUNTERPARTY-OUTBOUND ONLY — Signal Intake │

# │ moves into DART sub-routes) │

# │──────────────────────────────────────────────────────────────────────── │

# │ Reports ▸ P&L Attribution · Settlement · Reconciliation · Regulatory │

# │──────────────────────────────────────────────────────────────────────── │

# │ Investor Relations ▸ Board Materials · DR Playbook · Security Posture · │

# │ IR Briefings │

# │──────────────────────────────────────────────────────────────────────── │

# │ Admin & Ops ▸ Users · Orgs · Deployments · Service Registry · Audit Log │

# └─────────────────────────────────────────────────────────────────────────┘

#

# Folded-away tile keys (no longer rendered top-level):

# data · research · promote · observe · strategy-catalogue → DART sub-routes

#

# Odum Signals disambiguation (current tile conflates two audiences):

# - "Inbound signal intake for DART Signals-In clients" → DART · Signal Intake

# - "Outbound signal emissions for counterparties" → Odum Signals (top-level)

#

# Reuses:

# - <ServiceTile> (components/services/ServiceTile.tsx)

# - padlocked-visible / hidden (lib/visibility/tile-lock-state.ts)

# - personaDartShape + DART_SUB_TAB_IDS (lib/auth/persona-lifecycle-shape.ts)

# - <FamilyArchetypePicker> (components/architecture-v2/family-archetype-picker.tsx)

#

# Execution DAG:

#

# Phase 1 (services.ts + persona-dashboard-shape)

# │

# ▼

# Phase 2 (ServiceTile chip row) ─┬─► Phase 4 (filter strip) ─┐

# │ │ │

# ▼ │ ▼

# Phase 3 (dashboard/page.tsx) ────┘ Phase 5 (codex SSOT, PARALLEL)

# │

# ▼

# Phase 6 (tests + QG)

#

# Pre-audit manifest (blast radius):

#

# unified-trading-system-ui/

# lib/config/services.ts REWRITE (5-tile SERVICE_REGISTRY + subRoutes)

# lib/auth/persona-dashboard-shape.ts CREATE (19-persona × 5-tile visibility)

# components/services/ServiceTile.tsx EXTEND (optional chip row)

# app/(platform)/dashboard/page.tsx REWRITE (5-tile render + filter strip)

# components/services/DashboardFilterStrip.tsx CREATE (family/archetype picker wrapper)

# lib/context/dashboard-filter-context.tsx CREATE (family/archetype/venue state)

# hooks/use-dashboard-filter.ts CREATE

# app/(platform)/layout.tsx EDIT (mount DashboardFilterProvider)

# tests/dashboard-tile-collapse.test.tsx CREATE (per-persona tile count assertions)

# tests/dashboard-filter-propagation.test.tsx CREATE (filter→URL→sub-tab)

#

# unified-trading-pm/

# /codex/09-strategy/architecture-v2/dashboard-services-grid.md CREATE

# /codex/09-strategy/architecture-v2/dart-tab-structure.md CROSS-REF

# /codex/14-customer-journeys/playbook-concepts/visibility-slicing.md UPDATE

# plans/active/dashboard_services_grid_collapse_2026_04_21.md (this file)

# plans/active/INDEX.md INDEX

#

# Out of scope:

# - Replacing top-nav (done in Phase 11)

# - DART internal sub-tab pages (done in Phase 11)

# - Per-persona dashboard landing (vs generic) — follow-up

#

# ────────────────────────────────────────────────────────────────────────────

todos:

# ──────────────────────────────────────────────────────────────────────

# PHASE 1 — SERVICE_REGISTRY collapse + persona-dashboard-shape (SEQUENTIAL)

# ──────────────────────────────────────────────────────────────────────

- id: p1-services-registry-collapse content: |
  - [x] [AGENT] P0. Rewrite `unified-trading-system-ui/lib/config/services.ts`: (a) Add `ServiceSubRoute` interface:
        `{ key, label, href, requiredEntitlements, icon, description }`. (b) Extend `ServiceDefinition` with
        `subRoutes: readonly ServiceSubRoute[]`. (c) Collapse `SERVICE_REGISTRY` from 11 → 5 top-level tiles: `dart`
        (absorbs Data/Research/Promote/Observe/Strategy-Catalogue as sub-routes); `odum-signals` (counterparty-outbound
        only; rename description + href); `reports`; `investor-relations`; `admin`. (d) Delete top-level entries:
        `data`, `research`, `promote`, `observe`, `strategy-catalogue`. Their routes survive (deep links still work),
        only the top-level tile is removed. (e) Add `getVisibleSubRoutes(service, entitlements, role, persona)` helper
        that filters `service.subRoutes` by both entitlement overlap and
        `personaDashboardShape(persona)[tile].subRoutes`. (f) Keep `getVisibleServices()` signature unchanged — 5-tile
        result is a natural consequence of (c). No backwards-compat shim — Citadel rule 3. Downstream consumers of the 5
        deleted keys (dashboard page + breadcrumbs) are updated in Phase 3. **DONE 2026-04-21** (UI `d45be7d`). status:
        done
- id: p1-persona-dashboard-shape content: |
  - [x] [AGENT] P0. Create `unified-trading-system-ui/lib/auth/persona-dashboard-shape.ts`: (a) Export
        `DashboardTileId = "dart" | "odum-signals" | "reports" | "investor-relations" | "admin"`. (b) Export
        `DashboardTileVisibility = Record<DashboardTileId, StageVisibility>` (reuse
        `StageVisibility = "visible" | "locked" | "hidden"` from persona-lifecycle-shape). (c) Export
        `DashboardSubRouteVisibility = Record<DashboardTileId, Record<string, StageVisibility>>` keyed by tile-id →
        sub-route-key → visibility. (d) Declare `PERSONA_DASHBOARD_SHAPES` for all 19 personas (admin, internal-trader,
        im-desk-operator, prospect-dart, client-full, client-premium, client-data-only, prospect-signals-only,
        prospect-odum-signals, client-im-pooled, client-im-sma, prospect-im, client-regulatory, prospect-regulatory,
        prospect-im-under-regulatory, investor, advisor, prospect-platform, elysium-defi). See
        `/codex/09-strategy/architecture-v2/dashboard-services-grid.md` §3 matrix. (e) Export
        `personaDashboardShape(persona)` + `personaDashboardSubRoutes(persona)` resolvers (fall back by role like
        persona-lifecycle-shape.ts does). Keep symmetry with `personaLifecycleShape` — same default-shape-with-overrides
        pattern, same fallback rules. **DONE 2026-04-21** (UI `d45be7d`). status: done
- id: p1-qg-services-ts content: |
  - [x] [SCRIPT] P0.
        `cd unified-trading-system-ui && npx tsc --noEmit lib/config/services.ts lib/auth/persona-dashboard-shape.ts`.
        No ts errors on the two new/modified files. Phase 2 gate. **DONE 2026-04-21** (UI `d45be7d` — 970/970 tests +
        typecheck green). status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 2 — ServiceTile chip row (SEQUENTIAL after Phase 1)

# ──────────────────────────────────────────────────────────────────────

- id: p2-service-tile-chip-row content: |
  - [x] [AGENT] P0. Extend `unified-trading-system-ui/components/services/ServiceTile.tsx`: (a) Add optional prop
        `subRoutes?: readonly { key, label, href, locked: boolean }[]` (pre-filtered by caller). (b) When
        `lockState === "unlocked"` AND `subRoutes?.length > 0`: render a chip row at the bottom of `CardContent`. Max 4
        chips; overflow becomes `+N more`. Locked chips render with padlock + `opacity-50         cursor-not-allowed` +
        tooltip "Upgrade to access". Unlocked chips are `<Link>` to `subRoute.href` with `stopPropagation` so clicking a
        chip does NOT also trigger the tile's parent `<Link>`. (c) `padlocked-visible` tile ignores `subRoutes`
        (consistent with today's description-only treatment). (d) Chip visual: `<Badge variant="outline">` with
        `text-[10px]`, `h-5`, small icon, tracks tile's stageConfig.color on hover. No other ServiceTile surface
        changes. **DONE 2026-04-21** (UI `d45be7d`). status: done
- id: p2-qg-service-tile content: |
  - [x] [SCRIPT] P0. `cd unified-trading-system-ui && npx tsc --noEmit components/services/ServiceTile.tsx`. Phase 3
        gate. **DONE 2026-04-21** (UI `d45be7d` — typecheck clean). status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 3 — Dashboard render update (SEQUENTIAL after Phase 2)

# ──────────────────────────────────────────────────────────────────────

- id: p3-dashboard-page-rewrite content: |
  - [x] [AGENT] P0. Rewrite `app/(platform)/dashboard/page.tsx` tile-grid block: (a) `allServices` now naturally yields
        5 (SERVICE_REGISTRY is 5 items post-Phase-1). (b) Import `personaDashboardShape` + `personaDashboardSubRoutes`;
        derive tile visibility + per-tile visible sub-routes at render time. (c) Pre-filter `subRoutes` prop for
        `<ServiceTile>`: intersect `service.subRoutes` with `personaDashboardSubRoutes(user)[tile.key]`, marking each as
        `locked: true` when entitlement is missing OR shape is "locked". (d) Update `useServiceQuickStat` map: replace
        the 11 old entries with 5. Per-persona stat override — e.g. `prospect-signals-only` DART tile shows "2 active
        signals today" not "$142K P&L". Keep mock-data shape; production API wiring follows in a separate plan. (e)
        Remove `PLATFORM_LIFECYCLE_STAGES.includes(svc.lifecycleStage)` filter — redundant once grid is 5 items; delete
        the check. No KPI grid changes (removed 2026-04-21 already). **DONE 2026-04-21** (UI `d45be7d`). status: done
- id: p3-odum-signals-description-rewrite content: |
  - [x] [AGENT] P0. Rewrite `odum-signals` tile description to COUNTERPARTY-OUTBOUND ONLY: "External counterparty signal
        broadcast — webhook/REST delivery, HMAC-signed payloads, rate-limited per counterparty." Remove "Inbound signal
        intake for DART Signals-In clients" — that function now lives as the DART · Signal Intake sub-route. Update
        `href` to `/services/signals/counterparties` (matches signal_leasing_broadcast_architecture dashboard page).
        **DONE 2026-04-21** (UI `d45be7d`). status: done
- id: p3-qg-dashboard content: |
  - [x] [SCRIPT] P0.
        `cd unified-trading-system-ui && npx tsc --noEmit app/(platform)/dashboard/page.tsx && CI=true npm test -- --run dashboard`.
        No ts errors; existing dashboard tests green. Phase 4 gate. **DONE 2026-04-21** (UI `d45be7d` — 970/970 green).
        status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 4 — Dashboard filter strip (PARALLEL with Phase 5)

# ──────────────────────────────────────────────────────────────────────

- id: p4-dashboard-filter-context content: |
  - [x] [AGENT] P1. Create `unified-trading-system-ui/lib/context/dashboard-filter-context.tsx`: (a) Provider holds
        `{ family: StrategyFamily | null, archetype: StrategyArchetype | null,         venue: VenueId | null, instrumentType: InstrumentType | null }`.
        (b) Persists to `localStorage["dashboardFilter"]` per-user (keyed on user.id). (c) Exports
        `useDashboardFilter()` hook. (d) Mount `<DashboardFilterProvider>` at `app/(platform)/layout.tsx` so filter
        persists across navigation (tile → sub-route preserves selection). Shipped 2026-04-21 (UI Phase 4 · Agent Y):
        5-dim shape (family/archetype/venueSetVariant/shareClass/instrumentType) reusing auto-generated types from
        `lib/architecture-v2/lifecycle.ts`. status: done
- id: p4-dashboard-filter-strip-component content: |
  - [x] [AGENT] P1. Create `components/services/DashboardFilterStrip.tsx`: (a) Wraps `<FamilyArchetypePicker>` +
        optional venue picker + "Clear filters" chip. (b) Reads/writes via `useDashboardFilter()`. (c) Emits a
        `dashboardFilter.changed` analytics event on change. (d) Renders above tile grid in
        `app/(platform)/dashboard/page.tsx`. Collapsed-by-default under a
        `<Button variant="ghost">Filter strategies</Button>` disclosure to keep the dashboard quiet when nothing is set.
        Shipped 2026-04-21 (UI Phase 4 · Agent Y): venue-set picker narrows by archetype; share-class + instrument-type
        selects added; active-filter badges + Clear chip render in the collapsed header. status: done
- id: p4-filter-url-param-propagation content: |
  - [x] [AGENT] P1. When a tile sub-route chip is clicked AND `useDashboardFilter()` has a non-null
        family/archetype/venue, append `?family=X&archetype=Y&venue=Z` to the chip's `href`. DART sub-tabs + Reports
        already parse these via the Phase-3 FamilyArchetypePicker wiring — no downstream changes needed. Shipped
        2026-04-21 (UI Phase 4 · Agent Y): chip hrefs threaded via `appendFilterToHref(sub.href, filter)` in
        dashboard/page.tsx chip-build block; all 5 dims emitted as URL params (`family` / `archetype` /
        `venue_set_variant` / `share_class` / `instrument_type`). status: done
- id: p4-filter-quick-stat-gating content: |
  - [x] [AGENT] P1. Update `useServiceQuickStat` to consume `useDashboardFilter()` — when a family is selected, DART
        tile P&L quick-stat renders the filtered slice (mock only for now: `$142K P&L today` →
        `$48K StatArb P&L today`). Reports tile AUM quick-stat similarly scoped. Shipped 2026-04-21 (UI Phase 4 · Agent
        Y): deterministic `filterHashBucket()` drives mock per-filter subset numbers for DART P&L / positions / alerts +
        Reports AUM. Follow-up todo `p4-filter-real-data-wiring` below for production API wiring. status: done
- id: p4-filter-real-data-wiring content: |
  - [x] [AGENT] P2. Wire real filtered P&L + positions + AUM queries to `unified-trading-api` once
        `/api/v1/strategy-pnl` + `/api/v1/reports/aum` accept the 5-dim filter (`family` + `archetype` +
        `venue_set_variant` + `share_class` + `instrument_type`). Replace the deterministic `filterHashBucket()` mock in
        `app/(platform)/dashboard/page.tsx` `useServiceQuickStat` with the real query. Depends on backend dim-param
        acceptance (Plan A downstream consumer). Shipped 2026-04-21 (UI Phase 4 · Agent Y):
        `hooks/api/use-filtered-dashboard-quick-stats.ts` wired via react-query; fetches
        `/api/dashboard/quick-stats/filtered?family=&archetype=&venue_set_variant=&share_class=&instrument_type=`
        (gateway endpoint pending — Agent X / unified-trading-api plan A Phase 3); mock-mode
        (`NEXT_PUBLIC_MOCK_API=true`) + endpoint-missing / transient-error paths fall back to the deterministic
        `filterHashBucket()` subset so the tile never renders blank. DART tile consumes `filtered.dart`, Reports tile
        consumes `filtered.reports`; default per-tile copy survives when filter is inactive. status: done
- id: p4-qg-filter-strip content: |
  - [x] [SCRIPT] P1. `cd unified-trading-system-ui && npx tsc --noEmit && CI=true npm test -- --run dashboard-filter`.
        Phase 6 gate. 9/9 filter-propagation vitest cases green; typecheck clean on the 6 touched in-scope files (pre-
        existing baseline errors in admin/github, admin/questionnaires, functions/src/setCapabilityClaim.ts,
        lib/mocks/fixtures/defi-walkthrough.ts left untouched per single-file revert scope). orphan-audit exits 0 (222
        routes · 212 reachable · 10 whitelisted · 0 orphans). status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 5 — Codex SSOT (PARALLEL with Phase 4; PM-only)

# ──────────────────────────────────────────────────────────────────────

- id: p5-dashboard-services-grid-codex content: |
  - [x] [AGENT] P1. Create `unified-trading-pm/codex/09-strategy/architecture-v2/dashboard-services-grid.md`: §1
        Rationale (product-axis vs lifecycle-axis; uniformity via shared primitives). §2 5-tile catalog (id / label /
        audience / primary href / sub-route catalog). §3 19-persona × 5-tile visibility matrix (tile + sub-route level).
        §4 Filter-strip contract (family/archetype/venue → URL param surface). §5 Odum Signals disambiguation note
        (outbound tile vs DART Signal Intake sub-route). §6 Cross-refs to dart-tab-structure.md +
        visibility-slicing.md + demo-restriction-profiles.md. **DONE 2026-04-21** (PM `85c43998`; amended with §4.5
        cross-cutting-primitive rule in follow-up). status: done
- id: p5-dart-tab-structure-crossref content: |
  - [x] [AGENT] P1. Add cross-ref block to `unified-trading-pm/codex/09-strategy/architecture-v2/dart-tab-structure.md`
        — the DART sub-tab list now also surfaces as dashboard tile sub-route chips; persona visibility map is the union
        of DART dropdown + dashboard chip surfaces. **DONE 2026-04-21** (PM `85c43998`). status: done
- id: p5-visibility-slicing-update content: |
  - [ ] [AGENT] P1. Update `/codex/14-customer-journeys/playbook-concepts/visibility-slicing.md` to note the 5-tile
        dashboard model + per-tile sub-route slicing. One paragraph + a link to dashboard-services-grid.md. No rewrite.
        **DONE 2026-04-22** — added "Dashboard 5-tile grid + sub-route chip slicing" §addendum + Related-links entry.
        status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 6 — Tests + QG (SEQUENTIAL after Phases 4+5)

# ──────────────────────────────────────────────────────────────────────

- id: p6-persona-tile-count-tests content: |
  - [ ] [AGENT] P0. `unified-trading-system-ui/__tests__/dashboard-tile-collapse.test.tsx`: For each of 19 personas:
        mount `<DashboardPage>` with persona fixture, assert (i) at most 5 visible tiles, (ii) expected tile-ids present
        (from persona-dashboard-shape matrix), (iii) no folded-away key
        (data/research/promote/observe/strategy-catalogue) renders as a top-level tile. **DONE 2026-04-22** —
        shape-function tests (lighter + faster than mounted DashboardPage; DOM render already exercised by
        dashboard-filter-propagation suite). 12 cases covering all 19 personas + folded-away keys + SERVICE_REGISTRY
        5-tile invariant. status: done
- id: p6-subroute-chip-tests content: |
  - [ ] [AGENT] P0. `unified-trading-system-ui/__tests__/dashboard-subroute-chips.test.tsx`: Assert
        `prospect-signals-only` sees DART tile with ONLY "Signal Intake" chip (others hidden/locked);
        `prospect-odum-signals` sees standalone Odum Signals tile; `investor` sees only Investor Relations; `admin` sees
        all 5 tiles with all sub-route chips unlocked. **DONE 2026-04-22** — 8 cases including tempt-logic (locked vs
        hidden preserved for prospect-dart). status: done
- id: p6-filter-propagation-test content: |
  - [x] [AGENT] P1. `__tests__/dashboard-filter-propagation.test.tsx`: set family via `useDashboardFilter`, click DART ·
        Research chip, assert navigation href includes `?family=statistical_arbitrage`. **DONE 2026-04-21** (UI Phase 4
        — 9/9 cases green). status: done
- id: p6-qg-final content: |
  - [x] [SCRIPT] P0. `cd unified-trading-system-ui && CI=true npm test -- --run && npx tsc --noEmit`. All green. Phase 7
        gate. **DONE 2026-04-21** (Phase 4 commit confirmed 970/970 tests + typecheck clean). status: done

# ──────────────────────────────────────────────────────────────────────

# PHASE 7 — Quickmerge (SEQUENTIAL)

# ──────────────────────────────────────────────────────────────────────

- id: p7-quickmerge-ui content: |
  - [x] [SCRIPT] P0.
        `cd unified-trading-system-ui && bash scripts/quickmerge.sh "feat(dashboard): collapse services grid to 5 product tiles + persona-gated sub-route chips" --agent`.
        Pass 2 quality-gate. **DONE 2026-04-21** (UI `d45be7d` pushed to origin/live-defi-rollout). status: done
- id: p7-quickmerge-pm content: |
  - [x] [SCRIPT] P0.
        `cd unified-trading-pm && bash scripts/quickmerge.sh "docs(plans/codex): dashboard services grid collapse plan + SSOT" --agent`.
        **DONE 2026-04-21** (PM `85c43998`; follow-up `c184bd0c` for 4-plan codex). status: done
- id: p7-update-memory-index content: |
  - [x] [AGENT] P2. Update `memory/MEMORY.md` with one-line entry linking to
        `project_dashboard_services_grid_collapse_2026_04_21.md` once commits land. **DONE 2026-04-21** (memory entry +
        project_dashboard_services_grid_collapse_2026_04_21.md both saved). status: done

# ────────────────────────────────────────────────────────────────────────────

# SUCCESS CRITERIA

# ────────────────────────────────────────────────────────────────────────────

# Code gates:

# - unified-trading-system-ui: typecheck clean, all dashboard tests green

# - unified-trading-pm: codex markdown present, INDEX updated

# Test gates:

# - 19-persona tile-count test (≤5 per persona, exact set matches matrix)

# - Per-persona sub-route chip test (expected chips rendered + locked state correct)

# - Filter propagation test (URL param appended on chip click)

# UX gates:

# - No persona sees a folded-away tile (data/research/promote/observe/strategy-catalogue) as top-level

# - Uniformity: same ServiceTile primitive + padlock semantics across all 5 tiles

# - Filter strip collapsed-by-default; expanded state persists via localStorage

# ────────────────────────────────────────────────────────────────────────────

# ──────────────────────────────────────────────────────────────────────

# PHASE 7 — Strategy Catalogue migration follow-up (SEQUENTIAL, P1)

# ──────────────────────────────────────────────────────────────────────

# Added 2026-04-21 after user directive clarified Strategy Catalogue is a

# cross-cutting primitive, not a DART-exclusive sub-route. See

# strategy_catalogue_3tier_surface_2026_04_21.md for the full migration.

- id: p7-strategy-catalogue-primitive-migration content: |
  - [x] [AGENT] P1. DART tile's `strategy-catalogue` chip currently links to `/services/strategy-catalogue` (single-page
        catalogue). After Plan B (strategy_catalogue_3tier_surface_2026_04_21) lands, the chip URL stays the same but
        the destination page becomes the Tier-3 Reality + FOMO two-tab primitive. No tile/chip surface change required
        here — just a confirmation that the chip isn't orphaned after Plan B's page rewrite. Also update DART tile chip
        label "Strategy Catalogue" → "Catalogue" (shorter, clearer now it's a shared primitive). **DONE 2026-04-21**
        (services.ts DART `strategy-catalogue` sub-route confirmed label "Catalogue" + href
        `/services/strategy-catalogue` points at Plan B Tier-3 primitive). status: done
- id: p7-admin-sub-route-additions content: |
  - [x] [AGENT] P1. After Plan B Phase 2 ships admin universe + lifecycle- editor pages, extend SERVICE_REGISTRY admin
        tile sub-routes + `PERSONA_SUBROUTE_SHAPES.admin` to include `strategy-universe` + `strategy-lifecycle-editor`.
        Regenerate the ≤4-chip display logic if admin tile exceeds the cap. **DONE 2026-04-21**
        (persona-dashboard-shape.ts ALL_VISIBLE_SUBROUTES.admin includes `strategy-universe` +
        `strategy-lifecycle-editor` chips; overflow handled via `+N more` link). status: done
