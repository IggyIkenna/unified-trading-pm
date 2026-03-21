# Phase 2b: Build Lifecycle Tab — Deep Audit

**Created:** 2026-03-21
**Type:** audit | **Status:** complete (30/30) | **Scope:** Deep audit of all UI components, navigation, data wiring, and UX under the Build lifecycle tab (BUILD_TABS — 7 tabs + 14 orphan sub-pages).

**Repo:** `unified-trading-system-ui`
**Parent plan:** `ui_lifecycle_service_tab_cross_reference_2026_03_21.plan.md` (Phase 1)

---

## Scope

**Lifecycle stage:** Build — "Features, ML models, strategies & backtesting (Quant)"
**Color:** `text-violet-400` | **Icon:** Wrench
**Layout:** `app/(platform)/service/research/layout.tsx`
**Tab set:** BUILD_TABS (7 tabs, 3 entitlements: ml-full, strategy-full, execution-basic)

### Routes Under Audit

#### Tabs (in BUILD_TABS)

| # | Tab Label | Route | Entitlement | matchPrefix |
|---|-----------|-------|-------------|-------------|
| 1 | Research Hub | `/service/research/overview` | None | — |
| 2 | Features | `/service/research/ml/features` | ml-full | — |
| 3 | ML Models | `/service/research/ml` | ml-full | `/service/research/ml` |
| 4 | Strategies | `/service/research/strategy/backtests` | strategy-full | `/service/research/strategy` |
| 5 | Backtests | `/service/research/strategy/compare` | strategy-full | — |
| 6 | Signals | `/service/research/ml/validation` | ml-full | — |
| 7 | Execution Research | `/service/research/execution/algos` | execution-basic | `/service/research/execution` |

#### Orphan Pages (no tab entry, inherit research layout)

| # | Route | Primary Stage (routeMappings) |
|---|-------|-------------------------------|
| 8 | `/service/research/ml/overview` | build |
| 9 | `/service/research/ml/experiments` | build |
| 10 | `/service/research/ml/experiments/[id]` | build |
| 11 | `/service/research/ml/training` | build |
| 12 | `/service/research/ml/registry` | build (secondary: promote) |
| 13 | `/service/research/ml/monitoring` | observe |
| 14 | `/service/research/ml/deploy` | promote |
| 15 | `/service/research/ml/governance` | manage |
| 16 | `/service/research/ml/config` | — (not in routeMappings) |
| 17 | `/service/research/strategy/overview` | — (not in routeMappings) |
| 18 | `/service/research/strategy/results` | build |
| 19 | `/service/research/strategy/heatmap` | build |
| 20 | `/service/research/execution/venues` | build (secondary: acquire) |
| 21 | `/service/research/execution/benchmarks` | build |
| 22 | `/service/research/quant` | — (not in routeMappings) |

---

## Phase 1 Confirmed Findings

| ID | Finding | Severity | Impact on Phase 2b |
|----|---------|----------|--------------------|
| C2 | BUILD_TABS correctly wired — research layout imports BUILD_TABS | PASS | Layout itself is correct |
| C6 | PROMOTE_TABS routes (`/service/research/strategy/candidates`, `/service/research/execution/tca`, `/service/research/strategy/handoff`) fall through to research layout → show BUILD_TABS instead of PROMOTE_TABS | P1-fix | G2 must document exact UX impact of wrong tab context |
| D1 | 14 orphan pages under `/service/research/*` confirmed — no tab entry but inherit research layout | P2-improve | B1-B3 must map discoverability of each orphan |
| D4 | Multi-stage orphans confirmed: `/service/research/ml/monitoring` (observe), `/service/research/ml/deploy` (promote), `/service/research/ml/governance` (manage) — lifecycle nav may show wrong stage | P2-improve | G3 must verify lifecycle highlight behavior |
| E3 | Nav gates research on `strategy-full OR ml-full`, but individual BUILD_TABS have specific per-tab entitlements (`ml-full`, `strategy-full`, `execution-basic`) — user with only `execution-basic` locked at nav but could URL-bypass to `/service/research/execution/algos` | P2-improve | F1-F3 must test this exact scenario |
| F1 | RESEARCH_TABS alias (`RESEARCH_TABS = BUILD_TABS`) is dead code — no imports anywhere | P3-cosmetic | Note in output, not a separate task |
| B5 | routeMappings coverage: `/service/research/ml/experiments/[id]`, `/service/research/ml/config`, `/service/research/strategy/overview`, `/service/research/quant` have no routeMappings entry | P2-improve | C3 must verify lifecycle nav behavior on these pages |

---

## Audit Tasks

### A. Component Inventory (7 tab pages)

- [x] **A1. Research Hub** (`/service/research/overview`) — Full component inventory: name, source, props, data source.
- [x] **A2. Features** (`/service/research/ml/features`) — Component inventory.
- [x] **A3. ML Models** (`/service/research/ml`) — Component inventory. Note: matchPrefix `/service/research/ml` means all ML sub-pages highlight this tab.
- [x] **A4. Strategies** (`/service/research/strategy/backtests`) — Component inventory.
- [x] **A5. Backtests** (`/service/research/strategy/compare`) — Component inventory.
- [x] **A6. Signals** (`/service/research/ml/validation`) — Component inventory.
- [x] **A7. Execution Research** (`/service/research/execution/algos`) — Component inventory.

### B. Orphan Pages Audit (3 tasks)

- [x] **B1. ML orphan pages (9 pages)** — For routes 8-16: document how each is accessed (in-page link? sidebar? URL-only?). Are they discoverable from the BUILD_TABS navigation?
- [x] **B2. Strategy orphan pages (3 pages)** — For routes 17-19: same discovery audit. Note: /service/research/strategy/overview and /service/research/strategy/results are NOT in routeMappings.
- [x] **B3. Execution & quant orphan pages (3 pages)** — For routes 20-22: same discovery audit.

### C. Navigation & Routing (5 tasks)

- [x] **C1. Tab active state** — Verify correct tab highlights for all 7 tabs. Special attention to matchPrefix conflicts: `/service/research/ml` prefix matches Features, ML Models, AND Signals tabs.
- [x] **C2. matchPrefix overlap** — ML Models has matchPrefix `/service/research/ml`. Features href is `/service/research/ml/features` (starts with that prefix). Does Features tab ever highlight? Or does ML Models always win?
- [x] **C3. Lifecycle nav highlight** — On any /service/research/* route, verify Build lifecycle tab highlights. Exception: routeMappings maps some research routes to promote/observe/manage stages — does lifecycle nav handle this?
- [x] **C4. Internal navigation** — Map all links between research sub-pages. Document navigation flow from Research Hub → sub-pages → detail views.
- [x] **C5. Cross-lifecycle links** — Document links from research pages to pages in other lifecycle tabs (trading, execution, data).

### D. Data Wiring (4 tasks)

- [x] **D1. React Query hooks** — Which hooks feed research pages? List: hook → page → endpoint.
- [x] **D2. Flat mock files** — Which research pages still use flat mocks from lib/*.ts?
- [x] **D3. MSW handler coverage** — For each hook, does a corresponding MSW handler exist?
- [x] **D4. Strategy/ML data model** — Do research pages use shared data models? Are models imported from context/ (internal contracts)?

### E. UX Audit (5 tasks)

- [x] **E1. Loading states** — Per page: skeleton, spinner, blank, shimmer?
- [x] **E2. Error states** — Per page: error boundary, toast, inline?
- [x] **E3. Empty states** — Per page: empty illustration, message, CTA?
- [x] **E4. Responsive behavior** — Mobile/tablet/desktop checks for all 7 tab pages.
- [x] **E5. Live/As-Of toggle** — LIVE_ASOF_VISIBLE shows `build: true`. Is toggle rendered? Functional?

### F. Entitlement Gating (3 tasks)

- [x] **F1. ml-full gating** — Login as client-data-only (no ml-full). Verify Features, ML Models, Signals tabs show lock icon. Verify locked tabs are not clickable links. **Phase 1 note:** isItemAccessible gates ALL of `/service/research/*` on `strategy-full OR ml-full` — a user with only `execution-basic` can't reach Research Hub via nav but could URL-bypass to `/service/research/execution/algos`. Test this scenario.
- [x] **F2. strategy-full gating** — Login as client-premium (has strategy-full, no ml-full). Verify Strategies and Backtests are unlocked, but ML tabs are locked.
- [x] **F3. execution-basic gating** — Verify Execution Research tab lock/unlock behavior per persona.

### G. Cross-Reference Markers (3 tasks)

- [x] **G1. Shared components** — Components on research pages that also appear elsewhere. Phase 3 targets.
- [x] **G2. Promote-stage routes** — /service/research/strategy/candidates and /service/research/strategy/handoff are in PROMOTE_TABS but served by research layout. Document the user experience of this dual-stage ownership. **Phase 1 confirmed:** These show BUILD_TABS (not PROMOTE_TABS). Lifecycle nav highlights Promote (correct via routeMappings primaryStage) but Row 2 tabs show Build context — user sees mismatched navigation layers.
- [x] **G3. Multi-stage orphans** — Routes like /service/research/ml/monitoring (primaryStage: observe) and /service/research/ml/governance (primaryStage: manage) are under /service/research/ but mapped to different lifecycle stages. Does lifecycle nav correctly show Observe/Manage when on these pages?

---

## Output Format

Per task:
```
Task: [ID]
Status: PASS | ISSUE | INFO
Component/Route: [name]
Finding: [description]
Severity: P0-blocking | P1-fix | P2-improve | P3-cosmetic
Recommendation: [action]
```

## Output Documents

All in `unified-trading-system-ui/docs/phase2/`:

- `BUILD_TAB_AUDIT_RESULTS.md` — Main audit results (30 tasks, per-task findings)
- `BUILD_COMPONENT_INVENTORY.md` — Component inventory for all 22 pages
- `BUILD_DATA_WIRING_MATRIX.md` — Data layer analysis (hooks, mocks, MSW, types)
- `BUILD_NAVIGATION_AUDIT.md` — Navigation and routing deep analysis
- `BUILD_UX_ENTITLEMENT_AUDIT.md` — UX states and entitlement gating audit

## Depends On

Phase 1 findings (A2, B1-B5, C2, C6)

## Feeds Into

Phase 3 cross-reference audit (G1-G3, C5)
