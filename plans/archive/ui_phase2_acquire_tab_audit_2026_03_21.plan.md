# Phase 2a: Acquire Lifecycle Tab — Deep Audit

**Created:** 2026-03-21 **Type:** audit | **Status:** complete (24/24) | **Scope:** Deep audit of all UI components,
navigation, data wiring, and UX under the Acquire lifecycle tab (DATA_TABS — 6 routes). **Completed:** 2026-03-21 |
**Output:** `unified-trading-system-ui/docs/phase2/`

**Repo:** `unified-trading-system-ui` **Parent plan:** `ui_lifecycle_service_tab_cross_reference_2026_03_21.md`
(Phase 1)

---

## Scope

**Lifecycle stage:** Acquire — "Data acquisition, ETL pipelines & venue coverage (Data Science)" **Color:**
`text-sky-400` | **Icon:** Database **Layout:** `app/(platform)/service/data/layout.tsx` **Tab set:** DATA_TABS (6 tabs,
no entitlement gating)

### Routes Under Audit

| #   | Tab Label       | Route                       | Page File                                          |
| --- | --------------- | --------------------------- | -------------------------------------------------- |
| 1   | Pipeline Status | `/service/data/overview`    | `app/(platform)/service/data/overview/page.tsx`    |
| 2   | Coverage Matrix | `/service/data/coverage`    | `app/(platform)/service/data/coverage/page.tsx`    |
| 3   | Missing Data    | `/service/data/missing`     | `app/(platform)/service/data/missing/page.tsx`     |
| 4   | Venue Health    | `/service/data/venues`      | `app/(platform)/service/data/venues/page.tsx`      |
| 5   | Markets         | `/service/data/markets`     | `app/(platform)/service/data/markets/page.tsx`     |
| 6   | ETL Logs        | `/service/data/logs`        | `app/(platform)/service/data/logs/page.tsx`        |
| —   | (orphan)        | `/service/data/markets/pnl` | `app/(platform)/service/data/markets/pnl/page.tsx` |

---

## Phase 1 Confirmed Findings

| ID   | Finding                                                                                                                                        | Severity   | Impact on Phase 2a                                                                      |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------- |
| C1   | DATA_TABS correctly wired — layout imports DATA_TABS, passes entitlements, shows LiveAsOfToggle                                                | PASS       | No structural issues to investigate                                                     |
| D1   | `/service/data/markets/pnl` confirmed orphan — no tab entry, no routeMappings                                                                  | INFO       | Task B5 must determine access path                                                      |
| D4   | 4 DATA_TABS routes missing from routeMappings: `/service/data/coverage`, `/service/data/missing`, `/service/data/venues`, `/service/data/logs` | P2-improve | These pages won't highlight Acquire in lifecycle nav correctly — add to B2 verification |
| E1   | DATA_TABS has zero requiredEntitlement fields — all accessible to every persona                                                                | INFO       | Confirms E1 scope                                                                       |
| Gap1 | URL bypass: no server-side entitlement enforcement                                                                                             | P1-fix     | Even though DATA_TABS has no gates, verify no data-scoping issues in E2                 |

---

## Audit Tasks

### A. Component Inventory (6 tasks)

- [x] **A1. Pipeline Status page** — PASS: Well-aligned to Acquire domain. Shows real service names
      (market-tick-data-service, market-data-processing-service), shard progress, venue coverage, freshness heatmaps.
      Mock data matches backend schema. Minor: no remediation actions on data gaps.
- [x] **A2. Coverage Matrix page** — P0-BLOCKING: Page file does NOT exist. Tab leads to 404. Concept is core Acquire —
      venue × instrument × date coverage grid.
- [x] **A3. Missing Data page** — PLACEHOLDER: Correct concept for Acquire (gap detection, backfill tracking, SLA
      breach). Awaiting backend.
- [x] **A4. Venue Health page** — PLACEHOLDER: Correct concept for Acquire (venue connectivity, latency, rate limits).
      Awaiting backend.
- [x] **A5. Markets page** — P1-MISALIGNED: Page is "Market Intelligence — P&L attribution, reconciliation, and
      post-trade analytics" with P&L/Desk/Recon/Latency tabs. This is Report/Run/Observe content, NOT data acquisition.
      Should be repurposed as "Market Data Explorer" or relocated.
- [x] **A6. ETL Logs page** — P0-BLOCKING: Page file does NOT exist. Tab leads to 404. Concept is core Acquire —
      pipeline run history and debugging.

### B. Navigation & Routing (5 tasks)

- [x] **B1. Tab active state** — PASS: Tab highlighting works correctly for all existing pages via pathname === href
      matching.
- [x] **B2. Lifecycle nav highlight** — ISSUE (P1): 4 of 6 routes missing from routeMappings. getRouteMapping() prefix
      fallback does NOT cover sibling routes (only children). Lifecycle nav broken on coverage, missing, venues, logs.
- [x] **B3. Internal navigation** — INFO: Minimal cross-links. Overview → /service/data-catalogue. markets/pnl →
      /service/data/markets (back). No cross-links between data tab pages.
- [x] **B4. Cross-lifecycle links** — ISSUE (P1): Markets pages link to /strategies/_ (Build), /ops/services/_ (Ops) via
      EntityLink. Overview links to /service/data-catalogue (Service Hub). Feeds Phase 3.
- [x] **B5. Orphan page /service/data/markets/pnl** — ISSUE (P1): Orphan confirmed. Accessible via EntityLink redirect,
      pnl-attribution-panel, service hub, direct URL. No direct link from markets page.

### C. Data Wiring (4 tasks)

- [x] **C1. React Query hooks inventory** — ISSUE (P2): ZERO React Query hooks used on any data page. useInstruments,
      useCatalogue, useMarketData exist in hooks/api/ but are not imported.
- [x] **C2. Flat mock files** — ISSUE (P2): 3 pages import from lib/\*.ts: overview (data-service-mock-data,
      platform-stats), markets (reference-data, trading-data), markets/pnl (reference-data). ~2,400 lines of flat mocks.
- [x] **C3. MSW handler coverage** — ISSUE (P2): 7 MSW handlers exist in lib/mocks/handlers/data.ts with persona
      scoping, but NONE are called by data pages. Pages bypass the API layer.
- [x] **C4. Data freshness** — INFO: Static "last refreshed: just now" badge on overview. Refresh button exists but
      non-functional (no onClick). No auto-refresh or polling anywhere.

### D. UX Audit (5 tasks)

- [x] **D1. Loading states** — ISSUE (P1): NO page has loading state handling. Overview returns null if !user. No
      skeletons, spinners, or shimmer.
- [x] **D2. Error states** — ISSUE (P1): NO page has error handling. No error boundaries, toasts, or inline error
      messages.
- [x] **D3. Empty states** — ISSUE (P1): Only markets has partial empty state ("No clients match filters"). All other
      pages show nothing for empty data.
- [x] **D4. Responsive behavior** — INFO: Code-level only (no runtime test). Uses Tailwind responsive utilities. Markets
      page complex layouts may overflow at mobile. Runtime testing needed.
- [x] **D5. Live/As-Of toggle** — PASS: LiveAsOfToggle rendered in layout (LIVE_ASOF_VISIBLE.acquire = true). However,
      no page reads the toggle state — purely cosmetic. Markets has independent custom Live/Batch toggle.

### E. Entitlement & Access (2 tasks)

- [x] **E1. No entitlement gating** — PASS: Confirmed all 6 DATA_TABS entries have no requiredEntitlement. All personas
      can access all tabs. Intentional — data is base tier.
- [x] **E2. Data scoping** — INFO: Overview page implements UI-level scoping (isInternal/hasEntitlement → all vs
      CEFI-only venues). MSW handlers support API-level scoping but are unused. Markets page has NO persona scoping —
      all users see identical data.

### F. Cross-Reference Markers (2 tasks)

- [x] **F1. Shared components** — ISSUE (P1): PnLValue, PnLChange, EntityLink used on data pages AND
      trading/reports/strategies pages. ShardCatalogue, FreshnessHeatmap unique to data. Phase 3 targets documented.
- [x] **F2. Domain lane accuracy** — PASS: lanes: ["data"] is acceptable. Markets page has P&L/strategy content but
      viewed through data lens. Consider secondary lanes ["data", "execution"] if Phase 3 confirms significant overlap.

---

## Output Format

Per task:

```
Task: [ID]
Status: PASS | ISSUE | INFO
Component/Route: [name]
Finding: [description]
Data source: hook | flat-mock | hardcoded
Recommendation: [action]
```

## Depends On

Phase 1 findings (relevance check A1, shared route check B1-B5)

## Feeds Into

Phase 3 cross-reference audit (findings from F1, F2, B4)
