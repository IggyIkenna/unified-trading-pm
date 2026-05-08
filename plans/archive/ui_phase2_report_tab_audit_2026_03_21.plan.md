# Phase 2g: Report Lifecycle Tab — Deep Audit

**Created:** 2026-03-21 **Type:** audit | **Status:** complete (20/20) | **Scope:** Deep audit of all UI components,
navigation, data wiring, and UX under the Report lifecycle tab (REPORTS_TABS — 5 routes). **Completed:** 2026-03-21
**Output:** `unified-trading-system-ui/docs/phase2/REPORT_TAB_AUDIT.md` (main results),
`REPORT_TAB_COMPONENT_INVENTORY.md`, `REPORT_TAB_ENTITLEMENT_AUDIT.md`, `REPORT_TAB_DATA_WIRING.md`

**Repo:** `unified-trading-system-ui` **Parent plan:** `ui_lifecycle_service_tab_cross_reference_2026_03_21.md`
(Phase 1)

---

## Scope

**Lifecycle stage:** Report — "P&L, settlement, invoicing & regulatory (Executive)" **Color:** `text-slate-400` |
**Icon:** FileText **Layout:** `app/(platform)/service/reports/layout.tsx` **Tab set:** REPORTS_TABS (5 tabs, no
entitlement gating)

### Routes Under Audit

| #   | Tab Label      | Route                             | Page File                                                |
| --- | -------------- | --------------------------------- | -------------------------------------------------------- |
| 1   | P&L            | `/service/reports/overview`       | `app/(platform)/service/reports/overview/page.tsx`       |
| 2   | Executive      | `/service/reports/executive`      | `app/(platform)/service/reports/executive/page.tsx`      |
| 3   | Settlement     | `/service/reports/settlement`     | `app/(platform)/service/reports/settlement/page.tsx`     |
| 4   | Reconciliation | `/service/reports/reconciliation` | `app/(platform)/service/reports/reconciliation/page.tsx` |
| 5   | Regulatory     | `/service/reports/regulatory`     | `app/(platform)/service/reports/regulatory/page.tsx`     |

---

## Phase 1 Confirmed Findings

| ID   | Finding                                                                                                                                           | Severity   | Impact on Phase 2g                                                |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------- |
| C5   | REPORTS_TABS correctly wired — reports layout imports REPORTS_TABS. Simplest layout — no Live/As-Of toggle                                        | PASS       | No structural issues                                              |
| D4   | 3 REPORTS_TABS routes missing from routeMappings: `/service/reports/settlement`, `/service/reports/reconciliation`, `/service/reports/regulatory` | P2-improve | B2 must verify lifecycle nav highlight on these pages             |
| E1   | REPORTS_TABS has zero requiredEntitlement on any tab, BUT isItemAccessible gates `/service/reports/*` on "reporting" entitlement                  | P1-fix     | E1-E2 must verify: nav locks it, tabs don't — URL bypass possible |
| Gap1 | `client-data-only` user (no "reporting" entitlement) can type `/service/reports/overview` directly — L1 allows (platform group), L3 has no gate   | P1-fix     | E2 must test this exact scenario                                  |
| A7   | Phase 1 confirmed all 5 REPORTS_TABS are relevant to Report lifecycle stage                                                                       | PASS       | No relevance issues                                               |

---

## Audit Tasks

### A. Component Inventory (5 tasks)

- [x] **A1. P&L page** (`/service/reports/overview`) — 553 lines, 16 components, 6 inline mock arrays, 5 in-page tabs.
      Uses EntityLink, PnLValue, useContextState.
- [x] **A2. Executive page** (`/service/reports/executive`) — Thin wrapper (9 lines) → ExecutiveDashboard (511 lines).
      recharts, NL query demo. secondaryStage "observe" confirmed.
- [x] **A3. Settlement page** (`/service/reports/settlement`) — Placeholder (25 lines). "Coming Soon" badge. Server
      component.
- [x] **A4. Reconciliation page** (`/service/reports/reconciliation`) — Placeholder (24 lines). "Coming Soon" badge.
      Server component.
- [x] **A5. Regulatory page** (`/service/reports/regulatory`) — Placeholder (24 lines). "Coming Soon" badge. Server
      component.

### B. Navigation & Routing (4 tasks)

- [x] **B1. Tab active state** — PASS. All 5 tabs highlight correctly (pathname === href matching).
- [x] **B2. Lifecycle nav** — ISSUE P2. 3 routes missing from routeMappings: settlement, reconciliation, regulatory →
      Report stage not highlighted on those pages.
- [x] **B3. Internal navigation** — PASS. All 5 tabs are Link components. No dead links. overflow-x-auto handles tab
      overflow.
- [x] **B4. Cross-lifecycle links** — ISSUE P2. EntityLink on P&L (client, settlement). 11+ action buttons (Download,
      Export, Generate) unwired.

### C. Data Wiring (3 tasks)

- [x] **C1. React Query hooks** — INFO. Zero React Query hooks on any report page. All data from inline mocks +
      useContextState (filter state only).
- [x] **C2. Flat mock usage** — INFO. P&L: 6 inline arrays (~150 lines). Executive: 6 inline arrays (~52 lines).
      Settlement/Reconciliation/Regulatory: no data (placeholders).
- [x] **C3. Report generation** — INFO. No PDF/CSV/Excel export wired. 11+ action buttons exist but none have onClick
      handlers.

### D. UX Audit (4 tasks)

- [x] **D1. Loading/error/empty states** — ISSUE P1. P&L: no loading/error/empty states. Executive: loading spinner for
      NL query only; empty state for strategy allocation. Placeholders: "Coming Soon" (appropriate).
- [x] **D2. Report workflow** — INFO. All 5 pages are isolated. No drill-down paths between them. P&L has internal
      sub-tabs (Settlements, Invoices, Treasury) that overlap with dedicated tab pages.
- [x] **D3. Responsive behavior** — ISSUE P2. Both P&L and Executive use grid-cols-4 without responsive breakpoints.
      Treasury table overflows on mobile.
- [x] **D4. Live/As-Of toggle** — PASS. report: false in LIVE_ASOF_VISIBLE. No toggle rendered. No rightSlot in reports
      layout.

### E. Entitlement & Access (2 tasks)

- [x] **E1. No tab-level entitlements** — ISSUE P1. Confirmed: L2 (nav) gated on "reporting", L3 (tabs) ungated, L4
      (layout) ungated. URL bypass works. Recommended fix: layout-level redirect + tab requiredEntitlement.
- [x] **E2. Persona access test** — ISSUE P1. Confirmed: client-data-only (entitlements: ["data-basic"]) CAN access all
      5 report pages via direct URL. No server-side protection exists. Systemic gap across all tab sets.

### F. Cross-Reference Markers (2 tasks)

- [x] **F1. Executive page dual stage** — INFO. ExecutiveDashboard has 1 consumer (executive page only). No shared
      components with Observe pages. secondaryStage "observe" is informational only.
- [x] **F2. Shared components** — INFO. EntityLink used on 11 pages total. PnLValue/PnLChange on 7 pages.
      useContextState unique to P&L page. ExecutiveDashboard unique to executive page. All shared components correctly
      centralized in components/trading/.

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

Phase 1 findings (A7, B1-B5, C5)

## Feeds Into

Phase 3 cross-reference audit (F1, F2, B4)
