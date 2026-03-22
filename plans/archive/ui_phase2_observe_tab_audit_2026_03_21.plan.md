# Phase 2e: Observe Lifecycle Tab — Deep Audit

**Created:** 2026-03-21 **Type:** audit | **Status:** complete (22/22) | **Scope:** Deep audit of all UI components,
navigation, data wiring, and UX under the Observe lifecycle tab (OBSERVE_TABS — 5 routes, NO layout wired).

**Repo:** `unified-trading-system-ui` **Parent plan:** `ui_lifecycle_service_tab_cross_reference_2026_03_21.plan.md`
(Phase 1)

---

## Scope

**Lifecycle stage:** Observe — "Risk monitoring, alerts, news & system health (Risk / Ops)" **Color:** `text-cyan-400` |
**Icon:** Eye **Layout:** NONE — OBSERVE_TABS is defined but no layout.tsx imports it **Tab set:** OBSERVE_TABS (5 tabs,
no entitlement gating)

**Critical structural issue:** Like PROMOTE_TABS, OBSERVE_TABS exists as a constant but is never rendered. Routes fall
through to trading layout (risk, alerts) or have no layout at all (news, strategy-health, health).

### Routes Under Audit

| #   | Tab Label       | Route                              | Actual Layout Used | Actual Tabs Shown |
| --- | --------------- | ---------------------------------- | ------------------ | ----------------- |
| 1   | Risk Dashboard  | `/service/trading/risk`            | trading            | TRADING_TABS      |
| 2   | Alerts          | `/service/trading/alerts`          | trading            | TRADING_TABS      |
| 3   | News            | `/service/observe/news`            | NONE               | NO tabs           |
| 4   | Strategy Health | `/service/observe/strategy-health` | NONE               | NO tabs           |
| 5   | System Health   | `/health`                          | NONE               | NO tabs           |

---

## Phase 1 Confirmed Findings

| ID   | Finding                                                                                                                                                                                                 | Severity   | Impact on Phase 2e                                                      |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------------------------------- |
| C7   | OBSERVE_TABS never rendered — confirmed no layout.tsx imports it. `/service/observe/` directory exists but has NO layout.tsx                                                                            | P1-fix     | A1, A3 pre-confirmed                                                    |
| C7   | `/service/observe/news` and `/service/observe/strategy-health` fall through to platform layout only — NO Row 2 tabs at all                                                                              | P1-fix     | A2 pre-confirmed; B3-B4 must audit standalone UX                        |
| SR1  | `/service/trading/risk` shows TRADING_TABS when accessed from Observe dropdown — lifecycle nav highlights Observe (correct via primaryStage) but tab bar is wrong                                       | P1-fix     | F1 pre-confirmed                                                        |
| SR3  | `/service/trading/alerts` shows TRADING_TABS with no tab highlighted — "Alerts" not in TRADING_TABS                                                                                                     | P1-fix     | F2 pre-confirmed                                                        |
| Gap2 | `/service/observe/*` prefix not checked by isItemAccessible — always returns true. Any authenticated user can access news and strategy-health                                                           | P2-improve | Add verification task — should strategy-health require `strategy-full`? |
| Gap4 | All 5 OBSERVE_TABS routes have zero requiredEntitlement                                                                                                                                                 | P2-improve | Combined with Gap2, these pages are completely unprotected              |
| D3   | `/service/observe/news` and `/service/observe/strategy-health` have NO routeMappings entries — lifecycle nav cannot detect correct stage                                                                | P2-improve | C2 must verify lifecycle highlight behavior                             |
| B4   | stageServiceMap for "observe" includes `/service/trading/risk`, `/service/trading/alerts`, `/health` — but observe dropdown also reaches `/service/observe/news` and `/service/observe/strategy-health` | INFO       | C1 must document all entry points                                       |

---

## Audit Tasks

### A. Structural Issues (3 tasks)

- [x] **A1. No layout renders OBSERVE_TABS** — CONFIRMED: No layout.tsx imports OBSERVE_TABS. Dead code. P1-fix.
- [x] **A2. Split context** — CONFIRMED: Pattern A (wrong tabs for risk/alerts) + Pattern B (no tabs for
      news/strategy-health/health). P1-fix.
- [x] **A3. /service/observe/ directory** — CONFIRMED: Directory exists with news/ and strategy-health/ but NO
      layout.tsx. P2-improve.

### B. Component Inventory (5 tasks)

- [x] **B1. Risk Dashboard** (`/service/trading/risk`) — 1,089 lines, 7 internal tabs, 6 state vars, ~350 lines mock
      data. INFO.
- [x] **B2. Alerts** (`/service/trading/alerts`) — 378 lines, Kill Switch panel, 7 mock alerts, 2 filter states. INFO.
- [x] **B3. News** (`/service/observe/news`) — 25-line "Coming Soon" placeholder. No data. P2-improve.
- [x] **B4. Strategy Health** (`/service/observe/strategy-health`) — 24-line "Coming Soon" placeholder. PASS.
- [x] **B5. System Health** (`/health`) — 318 lines, 3 internal tabs, 10 mock services, 7 freshness entries. PASS.

### C. Navigation & Routing (4 tasks)

- [x] **C1. Lifecycle nav entry points** — News and Strategy Health MISSING from stageServiceMap and dropdown. P1-fix.
- [x] **C2. Stage detection for shared routes** — News and Strategy Health MISSING from routeMappings — no stage
      detection. Risk/Alerts/Health correct. P2-improve.
- [x] **C3. Observe-internal navigation** — CONFIRMED: No inter-page navigation. Must use lifecycle dropdown for every
      page switch. P1-fix.
- [x] **C4. Cross-lifecycle links** — No cross-links exist between any Observe pages. P2-improve.

### D. Data Wiring (3 tasks)

- [x] **D1. Risk/Alerts data** — All inline mock data. No hooks, no API calls. Risk: ~350 lines of mock constants.
      Alerts: 7 mock entries. PASS.
- [x] **D2. News data** — Zero data. "Coming Soon" placeholder with description text only. PASS.
- [x] **D3. Health data** — Inline mock data: 10 services, 7 freshness entries. Well-structured models. INFO.

### E. UX Audit (4 tasks)

- [x] **E1. Loading/error/empty states** — NONE on any implemented page. No skeletons, error boundaries, or empty state
      messages. P2-improve.
- [x] **E2. Monitoring workflow** — No logical flow. All 5 pages are isolated with no drill-through or linking.
      P3-cosmetic.
- [x] **E3. Responsive behavior** — Risk/Alerts not responsive (hard-coded grids). News/Strategy-Health trivially
      responsive. Health partially responsive. P3-cosmetic.
- [x] **E4. Live/As-Of toggle** — LIVE_ASOF_VISIBLE.observe=true is dead config. Toggle shows on Risk/Alerts via trading
      layout (Run context, not Observe). Not shown on remaining 3 pages. P2-improve.

### F. Cross-Reference Markers (3 tasks)

- [x] **F1. /service/trading/risk triple ownership** — Every navigation path produces incorrect UX. Always shows
      TRADING_TABS, never highlights Risk. 3 architectural fix options documented. P1-fix.
- [x] **F2. /service/trading/alerts in TRADING_TABS?** — NOT in TRADING_TABS. Shows trading tabs with NO tab
      highlighted. Navigation dead-end. P1-fix.
- [x] **F3. Observe pages with no tab context** — News/Strategy-Health fixable by observe layout. /health at top-level
      needs route decision (move to /service/observe/health recommended). P2-improve.

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

Phase 1 findings (A5, B1-B3, C7)

## Output

- `unified-trading-system-ui/docs/phase2/OBSERVE_TAB_AUDIT.md` — 14 issues found (6 P1-fix, 6 P2-improve, 2 P3-cosmetic)
- `unified-trading-system-ui/docs/phase2/OBSERVE_TAB_COMPONENT_ALIGNMENT.md` — Supplement: component alignment
  assessment, two-tab-layer consolidation plan, OBSERVE_TABS redesign (5→10 tabs), mock data readiness check, migration
  path

## Feeds Into

Phase 3 cross-reference audit (F1-F3, C4)
