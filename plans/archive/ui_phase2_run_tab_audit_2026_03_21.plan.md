# Phase 2d: Run Lifecycle Tab — Deep Audit

**Created:** 2026-03-21 **Type:** audit | **Status:** complete (28/28) | **Scope:** Deep audit of all UI components,
navigation, data wiring, and UX under the Run lifecycle tab (TRADING_TABS — 6 routes + EXECUTION_TABS — 5 routes +
standalone pages).

**Repo:** `unified-trading-system-ui` **Parent plan:** `ui_lifecycle_service_tab_cross_reference_2026_03_21.plan.md`
(Phase 1)

---

## Scope

**Lifecycle stage:** Run — "Live trading, execution & account management (Trader)" **Color:** `text-emerald-400` |
**Icon:** Play **Layouts:** `app/(platform)/service/trading/layout.tsx` (TRADING_TABS) +
`app/(platform)/service/execution/layout.tsx` (EXECUTION_TABS) **Tab sets:** TRADING_TABS (6 tabs) + EXECUTION_TABS (5
tabs, legacy)

**Structural note:** The Run lifecycle has TWO service layouts (trading + execution) with separate tab sets. The
TRADING_TABS set includes an "Execution Analytics" tab that cross-references into the execution layout via matchPrefix.

### Routes Under Audit

#### TRADING_TABS (6 tabs)

| #   | Tab Label           | Route                         | matchPrefix          |
| --- | ------------------- | ----------------------------- | -------------------- |
| 1   | Terminal            | `/service/trading/overview`   | —                    |
| 2   | Positions           | `/service/trading/positions`  | —                    |
| 3   | Orders              | `/service/trading/orders`     | —                    |
| 4   | Execution Analytics | `/service/execution/overview` | `/service/execution` |
| 5   | Accounts            | `/service/trading/accounts`   | —                    |
| 6   | Markets             | `/service/trading/markets`    | —                    |

#### EXECUTION_TABS (5 tabs, legacy)

| #   | Tab Label  | Route                           |
| --- | ---------- | ------------------------------- |
| 7   | Analytics  | `/service/execution/overview`   |
| 8   | Algos      | `/service/execution/algos`      |
| 9   | Venues     | `/service/execution/venues`     |
| 10  | TCA        | `/service/execution/tca`        |
| 11  | Benchmarks | `/service/execution/benchmarks` |

#### Orphan Pages (no tab entry)

| #   | Route                           | Notes                 |
| --- | ------------------------------- | --------------------- |
| 12  | `/service/execution/candidates` | Not in EXECUTION_TABS |
| 13  | `/service/execution/handoff`    | Not in EXECUTION_TABS |

#### Standalone Pages (lifecycle nav entry points, no service tab set)

| #   | Route               | Notes                                          |
| --- | ------------------- | ---------------------------------------------- |
| 14  | `/dashboard`        | Command Center — entry point for Run lifecycle |
| 15  | `/service/overview` | Service Hub                                    |

---

## Phase 1 Confirmed Findings

| ID   | Finding                                                                                                                                                                       | Severity    | Impact on Phase 2d                                    |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------- |
| C3   | TRADING_TABS correctly wired — trading layout imports TRADING_TABS                                                                                                            | PASS        | Layout itself is correct                              |
| C4   | EXECUTION_TABS correctly wired — execution layout imports EXECUTION_TABS                                                                                                      | PASS        | Layout itself is correct                              |
| F2   | EXECUTION_TABS labeled "Legacy aliases" in service-tabs.tsx but actively used by execution layout                                                                             | P3-cosmetic | Note: comment is misleading, should be cleaned up     |
| SR2  | `/service/execution/overview` in both TRADING_TABS and EXECUTION_TABS — clicking "Execution Analytics" from trading causes abrupt layout switch, entire Row 2 tab bar changes | P1-fix      | C3 is pre-confirmed; document severity                |
| SR2  | Navigation asymmetry: TRADING_TABS has "Execution Analytics" entry, but EXECUTION_TABS has no "Back to Trading"                                                               | P2-improve  | Add to C3 findings                                    |
| SR3  | `/service/trading/alerts` is in OBSERVE_TABS but NOT in TRADING_TABS — shows TRADING_TABS with no tab highlighted                                                             | P1-fix      | F4 is pre-confirmed                                   |
| SR1  | `/service/trading/risk` is in PROMOTE_TABS + OBSERVE_TABS but NOT in TRADING_TABS — shows TRADING_TABS with no tab highlighted                                                | P1-fix      | F4 is pre-confirmed                                   |
| D1   | `/service/execution/candidates` and `/service/execution/handoff` confirmed orphans — no tab entry, no routeMappings                                                           | P2-improve  | F3 must determine access path                         |
| Gap1 | TRADING_TABS has zero requiredEntitlement on any tab — URL bypass possible for `client-data-only` user                                                                        | P1-fix      | Add new task to verify URL bypass                     |
| D4   | `/service/trading/orders`, `/service/trading/accounts`, `/service/trading/markets` missing from routeMappings                                                                 | P2-improve  | C4 must verify lifecycle nav highlight on these pages |

---

## Audit Tasks

### A. Component Inventory — Trading (6 tasks)

- [x] **A1. Terminal** (`/service/trading/overview`) — Full component inventory: name, source, props, data source. This
      is the primary trading view — likely the most complex page.
- [x] **A2. Positions** (`/service/trading/positions`) — Component inventory.
- [x] **A3. Orders** (`/service/trading/orders`) — Component inventory.
- [x] **A4. Accounts** (`/service/trading/accounts`) — Component inventory.
- [x] **A5. Markets** (`/service/trading/markets`) — Component inventory. Note: DATA_TABS also has a Markets tab at
      `/service/data/markets` — are these the same component?
- [x] **A6. Dashboard / Command Center** (`/dashboard`) — Component inventory. Entry point for Run lifecycle per
      stageServiceMap.

### B. Component Inventory — Execution (5 tasks)

- [x] **B1. Analytics** (`/service/execution/overview`) — Component inventory.
- [x] **B2. Algos** (`/service/execution/algos`) — Component inventory.
- [x] **B3. Venues** (`/service/execution/venues`) — Component inventory.
- [x] **B4. TCA** (`/service/execution/tca`) — Component inventory.
- [x] **B5. Benchmarks** (`/service/execution/benchmarks`) — Component inventory.

### C. Navigation & Routing (5 tasks)

- [x] **C1. Tab active state — TRADING_TABS** — Verify all 6 tabs highlight correctly. Special attention: "Execution
      Analytics" tab has matchPrefix `/service/execution` — this means ALL /service/execution/\* pages would highlight
      this tab in the trading layout. But those pages have their OWN layout with EXECUTION_TABS.
- [x] **C2. Tab active state — EXECUTION_TABS** — Verify all 5 tabs highlight correctly.
- [x] **C3. Layout switching** — When navigating from /service/trading/overview to /service/execution/overview (via
      "Execution Analytics" tab), does the Row 2 tab bar switch from TRADING_TABS to EXECUTION_TABS? Is this jarring?
      **Phase 1 confirmed:** Yes, layout switches abruptly. TRADING_TABS includes "Execution Analytics" entry but
      EXECUTION_TABS has NO "Back to Trading" link — navigation asymmetry. Browser back button works but is not
      discoverable.
- [x] **C4. Lifecycle nav** — Verify Run lifecycle highlights for all trading AND execution routes. stageServiceMap has
      3 entries: /dashboard, /service/trading/overview, /service/execution/overview.
- [x] **C5. Cross-lifecycle links** — Document links from trading/execution pages to other lifecycle tabs.

### D. Data Wiring (4 tasks)

- [x] **D1. Trading hooks** — Which React Query hooks feed trading pages? List: hook → page → endpoint.
- [x] **D2. Execution hooks** — Which React Query hooks feed execution pages?
- [x] **D3. Flat mock usage** — Which pages still use flat mocks?
- [x] **D4. Real-time data** — Trading Terminal and Positions likely need real-time updates. Are WebSocket hooks or
      polling implemented?

### E. UX Audit (4 tasks)

- [x] **E1. Loading/error/empty states** — For all 11 tab pages + dashboard.
- [x] **E2. Trading workflow** — Is there a clear flow from Terminal → place order → see in Orders → see in Positions?
      Or isolated pages?
- [x] **E3. Responsive behavior** — All pages at mobile/tablet/desktop.
- [x] **E4. Live/As-Of toggle** — LIVE_ASOF_VISIBLE shows `run: true`. Is toggle rendered? Does it switch data source
      for trading pages?

### F. Cross-Reference Markers (4 tasks)

- [x] **F1. Trading Markets vs Data Markets** — `/service/trading/markets` (TRADING_TABS) vs `/service/data/markets`
      (DATA_TABS). Are these the same component rendered in different contexts? Or different pages entirely?
- [x] **F2. Execution overlap** — EXECUTION_TABS pages at `/service/execution/*` also accessible via TRADING_TABS
      "Execution Analytics" matchPrefix. User sees different tab bars depending on navigation path.
- [x] **F3. Orphan execution pages** — `/service/execution/candidates` and `/service/execution/handoff` exist but aren't
      in any tab set. How are they accessed?
- [x] **F4. /service/trading/risk and /service/trading/alerts** — These are NOT in TRADING_TABS but are in
      OBSERVE_TABS/PROMOTE_TABS. Yet they use the trading layout. Does the tab bar make sense when visiting these pages?
      **Phase 1 confirmed:** Both show TRADING_TABS with NO tab highlighted. `/service/trading/risk` lifecycle nav shows
      Observe (correct), but Promote context is lost. `/service/trading/alerts` lifecycle nav shows Observe (correct),
      but user sees Run-context tabs.

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

## Depends On

Phase 1 findings (A4, B1-B5, C3-C4, F2)

## Feeds Into

Phase 3 cross-reference audit (F1-F4, C5)
