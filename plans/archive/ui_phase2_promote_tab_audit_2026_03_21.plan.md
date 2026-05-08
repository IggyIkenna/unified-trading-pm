# Phase 2c: Promote Lifecycle Tab — Deep Audit

**Created:** 2026-03-21 **Type:** audit | **Status:** complete (22/22) | **Scope:** Deep audit of all UI components,
navigation, data wiring, and UX under the Promote lifecycle tab (PROMOTE_TABS — 4 routes, NO layout wired).

**Repo:** `unified-trading-system-ui` **Parent plan:** `ui_lifecycle_service_tab_cross_reference_2026_03_21.md`
(Phase 1)

---

## Scope

**Lifecycle stage:** Promote — "Multi-day strategy review & risk analysis (Trader + Risk)" **Color:** `text-amber-400` |
**Icon:** ArrowUpCircle **Layout:** NONE — PROMOTE_TABS is defined but no layout.tsx imports it **Tab set:**
PROMOTE_TABS (4 tabs, no entitlement gating)

**Critical structural issue:** PROMOTE_TABS exists as a constant but is never rendered. Routes fall through to their
parent service layouts (research or trading), so users navigating to "Promote" see the wrong Row 2 tabs.

### Routes Under Audit

| #   | Tab Label          | Route                                   | Actual Layout Used | Actual Tabs Shown |
| --- | ------------------ | --------------------------------------- | ------------------ | ----------------- |
| 1   | Review Queue       | `/service/research/strategy/candidates` | research           | BUILD_TABS        |
| 2   | Execution Analysis | `/service/research/execution/tca`       | research           | BUILD_TABS        |
| 3   | Risk Review        | `/service/trading/risk`                 | trading            | TRADING_TABS      |
| 4   | Approval Status    | `/service/research/strategy/handoff`    | research           | BUILD_TABS        |

---

## Phase 1 Confirmed Findings

| ID   | Finding                                                                                                                                                     | Severity   | Impact on Phase 2c                                                   |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------------------------------------------------------------------- |
| C6   | PROMOTE_TABS never rendered — confirmed no layout.tsx imports it anywhere                                                                                   | P1-fix     | A1 is pre-confirmed; focus A2-A3 on UX impact                        |
| SR1  | `/service/trading/risk` navigation flow: Promote dropdown → navigate → lifecycle nav highlights **Observe** (not Promote) because primaryStage is "observe" | P1-fix     | C2 is pre-confirmed broken; document in F1                           |
| SR1  | `/service/trading/risk` shows TRADING_TABS (not PROMOTE_TABS or OBSERVE_TABS) — tab bar mismatch                                                            | P1-fix     | B3 must document this exact experience                               |
| SR4  | `/service/research/execution/tca` has primaryStage "observe" in routeMappings, not "promote" — confirmed mismap                                             | P2-improve | F2 is pre-confirmed; decide if intentional                           |
| SR1  | Flow 2: clicking Risk Review from Promote causes layout switch from research→trading — confirmed jarring                                                    | P1-fix     | A3 is pre-confirmed                                                  |
| Gap4 | All 4 PROMOTE_TABS routes have zero requiredEntitlement — accessible to any user who can navigate there                                                     | P2-improve | Add new task to verify if these pages should require `strategy-full` |
| C4   | Dead navigation: no Row 2 tabs for Promote means users can only reach Promote pages via lifecycle dropdown or direct URL                                    | P1-fix     | C4 is pre-confirmed                                                  |

---

## Audit Tasks

### A. Structural Issues (3 tasks)

- [x] **A1. No layout renders PROMOTE_TABS** — Confirmed: no layout imports PROMOTE_TABS. User sees BUILD_TABS (research
      routes) or TRADING_TABS (risk route). Severity: P1-fix.
- [x] **A2. Tab context mismatch** — Confirmed: page title says "Promotion Pipeline" but Row 2 shows BUILD_TABS.
      Cognitive dissonance. Severity: P2-improve.
- [x] **A3. Split layout problem** — Confirmed: 3 routes use research layout, 1 uses trading layout. Tab navigation
      would cause 2 layout switches. Severity: P1-fix.

### B. Component Inventory (4 tasks)

- [x] **B1. Review Queue page** (`/service/research/strategy/candidates`) — 488 lines, 17 UI + 8 icon imports, mock data
      from strategy-platform-mock-data. Has empty state. No sub-nav.
- [x] **B2. Execution Analysis page** (`/service/research/execution/tca`) — 407 lines, 14 UI + 9 chart imports, mixed
      mock sources. ExecutionNav sub-nav. primaryStage: observe (not promote).
- [x] **B3. Risk Review page** (`/service/trading/risk`) — 1071+ lines, 17 UI + 14 icon + 10 chart + 3 domain imports.
      ~400 lines inline mock data. 7 internal tabs. Shared with OBSERVE_TABS. No sub-nav.
- [x] **B4. Approval Status page** (`/service/research/strategy/handoff`) — 405 lines, 12 UI + 12 icon imports, single
      inline mock object. StrategyPlatformNav sub-nav. Approval chain + deployment options.

### C. Navigation & Routing (4 tasks)

- [x] **C1. Lifecycle nav entry point** — PASS. stageServiceMap promote has single entry. Lifecycle nav correctly
      highlights Promote for candidates route.
- [x] **C2. Lifecycle nav stage detection** — ISSUE P1-fix. 2 of 4 routes (TCA, risk) have primaryStage "observe" not
      "promote" — lifecycle nav highlights wrong stage.
- [x] **C3. Cross-tab navigation** — ISSUE P2-improve. No cross-links between the 4 Promote pages. Each has different
      (or no) sub-nav. Pages are isolated.
- [x] **C4. Dead navigation paths** — ISSUE P1-fix. Handoff page completely undiscoverable. Only candidates reachable
      via Promote dropdown. TCA/risk only via Observe or direct URL.

### D. Data Wiring (3 tasks)

- [x] **D1. Strategy candidates data** — Mock module: STRATEGY_CANDIDATES + BACKTEST_RUNS from
      strategy-platform-mock-data. useState only, no hooks/API.
- [x] **D2. TCA data** — Mixed: MOCK_RECENT_ORDERS from execution-platform-mock-data + 3 inline constants (one uses
      Math.random()).
- [x] **D3. Strategy handoff data** — Single inline mock object HANDOFF_CANDIDATE. useState for toggles/notes, no API.

### E. UX Audit (4 tasks)

- [x] **E1. Loading/error/empty states** — Only candidates has empty state. Zero loading/error states across all 4
      pages.
- [x] **E2. Promote workflow UX** — ISSUE P2-improve. No workflow flow. Pages are isolated. Handoff "Return to
      Candidates" button not wired.
- [x] **E3. Responsive behavior** — PASS. All pages use Tailwind grids with ResponsiveContainer for charts. Risk page
      has lg: breakpoints.
- [x] **E4. Live/As-Of toggle** — ISSUE P2-improve. promote:false is dead code. All 4 pages show toggle via inherited
      layouts (build/run).

### F. Cross-Reference Markers (2 tasks)

- [x] **F1. /service/trading/risk shared** — ISSUE P1-fix. Page is identical in both contexts. No context detection.
      Promote users want strategy-specific risk; Observe users want portfolio health. Needs context-aware default tab.
- [x] **F2. /service/research/execution/tca mapping** — ISSUE P2-improve. Likely a bug: page renders ExecutionNav
      (observe context), but PROMOTE_TABS includes it. Recommend adding secondaryStage: "promote".

### G. Recommendation (2 tasks)

- [x] **G1. Create promote layout?** — Evaluated. Medium effort: 4 route moves, 1 new layout, redirect handling. Clean
      separation but creates duplicate routes for shared pages. See PROMOTE_TAB_AUDIT.md §G1.
- [x] **G2. Alternative: contextual tab switching** — Evaluated. Lower effort, higher feasibility. Research+trading
      layouts detect primaryStage and switch tabs. Works for 3/4 routes without changes; requires F2 fix for TCA +
      trading layout change for Risk. Recommended approach. See PROMOTE_TAB_AUDIT.md §G2.

---

## Output Format

Per task:

```
Task: [ID]
Status: PASS | ISSUE | INFO
Severity: P0-blocking | P1-fix | P2-improve | P3-cosmetic
Finding: [description]
Recommendation: [action]
```

## Output Documents

- `unified-trading-system-ui/docs/phase2/PROMOTE_TAB_AUDIT.md` — Full audit results (22 tasks, 10 issues, 10 info)
- `unified-trading-system-ui/docs/phase2/PROMOTE_WORKFLOW_UX_ASSESSMENT.md` — Workflow-focused assessment: do the
  components actually serve the promote process (review → testnet → backtest vs live comparison → approval → live)?
- `unified-trading-system-ui/docs/phase2/PROMOTE_COMPONENT_INVENTORY.md` — Detailed component/import/data inventory
- `unified-trading-system-ui/docs/phase2/PROMOTE_CROSS_REFERENCE_MARKERS.md` — F1/F2 markers for Phase 3

## Depends On

Phase 1 findings (A3, B1-B3, C6)

## Feeds Into

Phase 3 cross-reference audit (F1, F2)
