# Phase 3: Cross-Reference & Consistency Audit

**Created:** 2026-03-21
**Type:** audit | **Status:** active (0/20) | **Scope:** Cross-lifecycle validation of shared routes, shared components, domain lane accuracy, and navigation consistency across all 7 lifecycle tabs.

**Repo:** `unified-trading-system-ui`
**Parent plan:** `ui_lifecycle_service_tab_cross_reference_2026_03_21.plan.md` (Phase 1)

---

## Context

This plan is driven by Phase 1 and Phase 2 findings. The specific scope items below are based on known cross-reference points. **After Phase 2 completes, update this plan** with additional cross-reference items discovered during per-tab audits (items tagged as "Phase 3 target" in F-section tasks).

---

## Known Cross-Reference Points (Pre-Phase 2)

### Shared Routes (same href in 2+ tab sets or lifecycle stages)

| Route | Tab Sets | Lifecycle Stages | Issue |
|-------|----------|------------------|-------|
| `/service/trading/risk` | PROMOTE_TABS ("Risk Review"), OBSERVE_TABS ("Risk Dashboard") | promote, observe | Same page, different labels, different lifecycle contexts |
| `/service/execution/overview` | TRADING_TABS ("Execution Analytics"), EXECUTION_TABS ("Analytics") | run | Same page, two tab bars depending on nav path |
| `/service/trading/alerts` | OBSERVE_TABS ("Alerts") | observe | Page uses trading layout → shows TRADING_TABS, not OBSERVE_TABS |
| `/service/research/execution/tca` | PROMOTE_TABS ("Execution Analysis") | promote (but routeMappings says observe) | Lifecycle stage mismatch |

### Shared Route Patterns (same URL prefix serves multiple lifecycle tabs)

| URL Prefix | Lifecycle Stages Served | Tab Sets |
|------------|-------------------------|----------|
| `/service/research/*` | Build, Promote | BUILD_TABS, PROMOTE_TABS |
| `/service/trading/*` | Run, Promote, Observe | TRADING_TABS, PROMOTE_TABS, OBSERVE_TABS |
| `/service/execution/*` | Run | TRADING_TABS, EXECUTION_TABS |

### Shared Components (suspected — to confirm in Phase 2)

| Component Area | Lifecycle Tabs Sharing | Verification |
|----------------|------------------------|--------------|
| Markets view | Acquire (DATA_TABS), Run (TRADING_TABS) | Different routes: /service/data/markets vs /service/trading/markets |
| Risk dashboard | Promote, Observe | Same route: /service/trading/risk |
| TCA view | Build, Promote, Run | Different routes: /service/research/execution/tca vs /service/execution/tca |

---

## Audit Tasks

### A. Shared Route Behavior (5 tasks)

- [ ] **A1. /service/trading/risk — context-aware rendering?** — Navigate to this page from Promote dropdown vs Observe dropdown. Does the page render any context-specific content (different header, filtered data, modified layout)? Or is it identical regardless of navigation path?
- [ ] **A2. /service/execution/overview — tab bar switching** — Navigate from /service/trading/overview ("Terminal" tab) → click "Execution Analytics" tab → land on /service/execution/overview. Does the tab bar switch from TRADING_TABS to EXECUTION_TABS? Is there a visual transition? Can user navigate back?
- [ ] **A3. /service/trading/alerts — orphaned from Observe** — This page shows TRADING_TABS but is conceptually an Observe page. When accessed from Observe lifecycle dropdown, lifecycle nav highlights Observe but tab bar shows Trading. Document UX confusion.
- [ ] **A4. /service/research/execution/tca — stage mismatch** — PROMOTE_TABS lists this as "Execution Analysis" but routeMappings primaryStage is "observe". When navigating here, which lifecycle tab highlights?
- [ ] **A5. Shared route navigation loops** — Can a user get into a confusing loop? E.g., Observe → Risk Dashboard (/service/trading/risk) → tab bar shows TRADING_TABS → user clicks "Terminal" → now in Run lifecycle but lifecycle nav may still show Observe.

### B. Shared Component Verification (4 tasks)

- [ ] **B1. Markets component comparison** — Compare `/service/data/markets/page.tsx` vs `/service/trading/markets/page.tsx`. Same component with different props? Different components entirely? Shared sub-components?
- [ ] **B2. TCA component comparison** — Compare `/service/research/execution/tca/page.tsx` vs `/service/execution/tca/page.tsx`. Same or different?
- [ ] **B3. Risk components** — Is the risk dashboard on /service/trading/risk a single component? Does it import components shared with report pages (P&L has risk elements)?
- [ ] **B4. Aggregate shared component list** — Compile final list of components used across 2+ lifecycle tabs from all Phase 2 F1 findings.

### C. Domain Lane Accuracy (3 tasks)

- [ ] **C1. Lane badge audit** — For every routeMappings entry, verify the `lanes` array is accurate. E.g., does `/service/research/ml/governance` (lanes: ["ml", "compliance"]) actually show compliance-related content?
- [ ] **C2. Lane visual rendering** — Are lane badges (colored dots/badges in lifecycle dropdown) actually rendered? Verify in lifecycle-nav.tsx.
- [ ] **C3. Lane coverage completeness** — Are any routes missing lane assignments that should have them? E.g., /dashboard has lanes ["execution", "strategy", "capital"] — does it also show data/ML content?

### D. Navigation Consistency (4 tasks)

- [ ] **D1. Lifecycle stage detection accuracy** — Test getRouteMapping() for all routes. Verify the returned primaryStage matches what lifecycle-nav.tsx highlights. Log any mismatches.
- [ ] **D2. Back navigation** — After cross-lifecycle navigation (e.g., Build → link to Trading page), does browser back button return to correct lifecycle context?
- [ ] **D3. Direct URL access** — Type each shared route directly in URL bar. Does lifecycle nav highlight the correct stage? (Should use primaryStage from routeMappings.)
- [ ] **D4. Breadcrumb accuracy** — If breadcrumbs exist, do they correctly show the lifecycle context? Or do they show the file-system route hierarchy (which may differ)?

### E. Entitlement Consistency Across Lifecycle Tabs (2 tasks)

- [ ] **E1. Same route, different entitlements?** — /service/trading/risk appears in PROMOTE_TABS (no entitlement) and OBSERVE_TABS (no entitlement). Consistent. But does isItemAccessible apply different rules when accessed from different lifecycle contexts?
- [ ] **E2. Entitlement gap at lifecycle nav level** — isItemAccessible has broad prefix matching (e.g., /service/research/* → strategy-full OR ml-full). But tab-level entitlements are more granular (individual tabs require specific entitlements). Document any gaps where lifecycle dropdown shows a route as accessible but tab shows it locked.

### F. Findings Consolidation (2 tasks)

- [ ] **F1. Severity-ranked findings** — Aggregate all P0/P1/P2/P3 findings from Phase 1, Phase 2, and Phase 3 into a single prioritized list.
- [ ] **F2. Fix recommendations** — For each P0/P1 finding, propose a specific fix (code change, layout addition, route reorganization, or configuration update).

---

## Output Format

Per task:
```
Task: [ID]
Status: PASS | ISSUE | INFO
Severity: P0-blocking | P1-fix | P2-improve | P3-cosmetic
Lifecycle tabs affected: [list]
Finding: [description]
Recommendation: [action]
```

## Depends On

- Phase 1 (all findings)
- Phase 2a-2g (cross-reference markers from F-section tasks)

## Feeds Into

Implementation plan (fix plan created from F2 recommendations)
