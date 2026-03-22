# Phase 1: Lifecycle ↔ Service Tab Cross-Reference Audit

**Created:** 2026-03-21 **Type:** audit | **Status:** complete (28/28) | **Scope:** Systematic alignment check between 7
lifecycle tabs (Row 1) and 8 service tab sets (Row 2) in unified-trading-system-ui.

**Repo:** `unified-trading-system-ui` **Key files:**

- `lib/lifecycle-mapping.ts` — SSOT for route→lifecycle stage mapping (routeMappings array, buildLifecycleNav
  stageServiceMap)
- `components/shell/service-tabs.tsx` — SSOT for Row 2 tab definitions (7 \*\_TABS constants + 1 legacy alias)
- `components/shell/lifecycle-nav.tsx` — Row 1 lifecycle navigation component
- `lib/config/auth.ts` — entitlement definitions
- `app/(platform)/service/*/layout.tsx` — layout files that wire tab sets to routes

---

## Context

Row 1 = 7 lifecycle tabs: Acquire, Build, Promote, Run, Observe, Manage, Report Row 2 = service tabs that change per
active lifecycle tab

**Known issues pre-audit:**

- PROMOTE_TABS and OBSERVE_TABS defined but no layout.tsx imports them
- MANAGE_TABS pages live in app/(ops)/ not app/(platform)/
- 14+ orphan pages have no tab entry
- Routes shared across lifecycle tabs (e.g. /service/trading/risk in both Promote and Observe)
- lifecycle-mapping.ts routeMappings and service-tabs.tsx \*\_TABS are independent — no validation

---

## Audit Tasks

### A. Relevance Check — Are service tabs relevant to their lifecycle stage? (7 tasks)

- [x] **A1. Acquire ↔ DATA_TABS relevance** — For each of the 6 DATA_TABS entries, verify the tab makes sense in the
      "Acquire" lifecycle context (data acquisition, ETL, venue coverage). Flag any tab that belongs in a different
      stage.
- [x] **A2. Build ↔ BUILD_TABS relevance** — For each of the 7 BUILD_TABS entries, verify alignment with "Build"
      lifecycle (research, ML, strategy dev, backtesting). Check if "Execution Research" tab belongs here or in
      Run/Promote.
- [x] **A3. Promote ↔ PROMOTE_TABS relevance** — For each of the 4 PROMOTE_TABS entries, verify alignment with
      "Promote" lifecycle (strategy review, risk analysis, approval). Check if "Risk Review" pointing to
      /service/trading/risk is correct.
- [x] **A4. Run ↔ TRADING_TABS relevance** — For each of the 6 TRADING_TABS entries, verify alignment with "Run"
      lifecycle (live trading, execution, accounts). Check if "Execution Analytics" (/service/execution/overview)
      belongs here or in its own lifecycle context.
- [x] **A5. Observe ↔ OBSERVE_TABS relevance** — For each of the 5 OBSERVE_TABS entries, verify alignment with
      "Observe" lifecycle (risk monitoring, alerts, health). Check if "News" and "Strategy Health" are relevant here.
- [x] **A6. Manage ↔ MANAGE_TABS relevance** — For each of the 5 MANAGE_TABS entries, verify alignment with "Manage"
      lifecycle (clients, mandates, fees, onboarding). All pages in (ops) — is that intentional?
- [x] **A7. Report ↔ REPORTS_TABS relevance** — For each of the 5 REPORTS_TABS entries, verify alignment with "Report"
      lifecycle (P&L, settlement, regulatory).

### B. Cross-Reference — Shared routes across lifecycle tabs (5 tasks)

- [x] **B1. Map all shared routes** — Identify every route href that appears in 2+ \*\_TABS constants. Currently known:
      `/service/trading/risk` (PROMOTE + OBSERVE), `/service/execution/overview` (TRADING matchPrefix).
- [x] **B2. Validate shared route context** — For each shared route, does the page render context-appropriate content
      depending on which lifecycle tab the user navigated from? Or is it identical?
- [x] **B3. Check lifecycle-mapping.ts primaryStage for shared routes** — A route can only have one primaryStage. If
      `/service/trading/risk` is primaryStage "observe", does it make sense also being in PROMOTE_TABS? Document each
      case.
- [x] **B4. Check stageServiceMap vs \*\_TABS alignment** — buildLifecycleNav() has its own stageServiceMap (entry
      points per stage). Verify these entry points exist in the corresponding \*\_TABS constant.
- [x] **B5. Verify routeMappings coverage** — Every href in _\_TABS should have a corresponding entry in routeMappings.
      Every routeMappings entry with requiresAuth should be reachable from at least one _\_TABS set.

### C. Layout Wiring Audit (7 tasks)

- [x] **C1. Data layout wiring** — Verify `app/(platform)/service/data/layout.tsx` imports DATA_TABS, passes
      entitlements correctly.
- [x] **C2. Research layout wiring** — Verify `app/(platform)/service/research/layout.tsx` imports BUILD_TABS, passes
      entitlements correctly.
- [x] **C3. Trading layout wiring** — Verify `app/(platform)/service/trading/layout.tsx` imports TRADING_TABS, passes
      entitlements correctly.
- [x] **C4. Execution layout wiring** — Verify `app/(platform)/service/execution/layout.tsx` imports EXECUTION_TABS,
      passes entitlements correctly.
- [x] **C5. Reports layout wiring** — Verify `app/(platform)/service/reports/layout.tsx` imports REPORTS_TABS, passes
      entitlements correctly.
- [x] **C6. PROMOTE_TABS — missing layout** — No layout imports PROMOTE_TABS. Document impact: which layout do promote
      routes actually render under? Do users see the correct Row 2 tabs?
- [x] **C7. OBSERVE_TABS — missing layout** — No layout imports OBSERVE_TABS. Document impact: /service/observe/news and
      /service/observe/strategy-health have no layout at all. /health is standalone.

### D. Orphan & Missing Route Detection (4 tasks)

- [x] **D1. Pages without tab entries** — List all page.tsx files under app/(platform)/ that are NOT referenced by any
      \*\_TABS href. Categorize: intentional standalone vs missing tab entry.
- [x] **D2. Tab entries without pages** — List all \*\_TABS hrefs that do NOT have a corresponding page.tsx. These are
      broken navigation links.
- [x] **D3. routeMappings without pages** — List all routeMappings entries that do NOT have a corresponding page.tsx.
- [x] **D4. Pages without routeMappings** — List all page.tsx files that do NOT have a routeMappings entry. These pages
      won't highlight the correct lifecycle tab.

### E. Entitlement Consistency (3 tasks)

- [x] **E1. Tab-level entitlements audit** — List every tab with requiredEntitlement. Verify the entitlement name exists
      in ENTITLEMENTS constant in auth.ts.
- [x] **E2. Cross-tab entitlement consistency** — If the same route appears in multiple tab sets, does it have the same
      requiredEntitlement in each? (e.g., /service/trading/risk has no entitlement in either PROMOTE or OBSERVE —
      consistent but is that correct?)
- [x] **E3. lifecycle-nav.tsx isItemAccessible vs tab entitlements** — The lifecycle nav has its own access control
      logic (isItemAccessible). Does it agree with the tab-level entitlements? Example: isItemAccessible gates
      /service/research/\* on strategy-full OR ml-full, but individual BUILD_TABS have specific entitlements per tab.

### F. Legacy & Cleanup (2 tasks)

- [x] **F1. RESEARCH_TABS alias** — `RESEARCH_TABS = BUILD_TABS` exists as a legacy alias. Find all imports of
      RESEARCH_TABS. Should it be removed?
- [x] **F2. EXECUTION_TABS status** — EXECUTION_TABS is labeled "legacy" in comments but has its own layout. Is it truly
      legacy or actively used? Clarify relationship with TRADING_TABS "Execution Analytics" tab.

---

## Output Format

Each task produces a structured finding:

```
Task: [ID]
Status: PASS | ISSUE | INFO
Severity: P0-blocking | P1-fix | P2-improve | P3-cosmetic
Finding: [description]
Affected routes: [list]
Recommendation: [action]
```

## Results

**Completed:** 2026-03-21 **Results location:** `unified-trading-system-ui/docs/phase1/`

| Document                       | Content                                                        |
| ------------------------------ | -------------------------------------------------------------- |
| `PHASE1_AUDIT_RESULTS.md`      | Main findings — 28 tasks, 12 PASS, 12 ISSUE, 4 INFO            |
| `ROUTE_COVERAGE_MATRIX.md`     | Every route mapped against page, tab set, routeMappings, stage |
| `ENTITLEMENT_ACCESS_MATRIX.md` | Per-persona access analysis across 3 control layers            |
| `SHARED_ROUTES_ANALYSIS.md`    | Detailed analysis of 4 shared routes with navigation flows     |
| `LAYOUT_WIRING_AUDIT.md`       | Every layout.tsx with imports, entitlements, Live/As-Of wiring |

**Summary:** 6 P1-fix issues, 4 P2-improve issues, 2 P3-cosmetic issues. Key systemic finding: PROMOTE_TABS,
OBSERVE_TABS, MANAGE_TABS are defined but never rendered — 3 of 7 lifecycle stages have no Row 2 tab navigation.

## Depends On

Nothing — this is the entry point.

## Feeds Into

- Phase 2 plans (per-lifecycle-tab deep audits) — findings here determine scope adjustments
- Phase 3 plan (cross-reference audit) — shared route findings feed directly into Phase 3
