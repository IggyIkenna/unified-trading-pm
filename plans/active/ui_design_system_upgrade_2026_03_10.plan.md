---
id: ui_design_system_upgrade_2026_03_10
title: UI Design System Upgrade — Institutional Dark Terminal Aesthetic Across All UI Repos
status: DONE
priority: P1
created: 2026-03-10
owner: agent
---

# UI Design System Upgrade — 2026-03-10

## Goal

Apply the deployment-ui institutional dark terminal aesthetic uniformly across all 10 UI repos. Create a shared
@unified-trading/ui-kit component library as the SSOT for all UI styling. Add mock mode infrastructure to every UI so
that full E2E smoke tests can run without a real backend.

## Status: DONE (2026-03-10)

## Repos in scope

1. unified-trading-ui-kit ✅ (NEW — shared library, 19 files, dist/ built)
2. onboarding-ui ✅ (16 smoke tests, mock mode, all 6 pages)
3. execution-analytics-ui ✅ (13 smoke tests, mock mode, all 11 pages)
4. strategy-ui ✅ (13 smoke tests, mock mode, all 4 pages)
5. settlement-ui ✅ (9 smoke tests, mock mode, positions/invoices/reports)
6. live-health-monitor-ui ✅ (9 smoke tests, mock mode, dashboard/health)
7. logs-dashboard-ui ✅ (9 smoke tests, mock mode, log stream/detail)
8. ml-training-ui ✅ (14 smoke tests, mock mode, experiments/models)
9. trading-analytics-ui ✅ (14 smoke tests, mock mode, orderbook/latency)
10. batch-audit-ui ✅ (13 smoke tests, mock mode, jobs/job-detail)
11. client-reporting-ui ✅ (11 smoke tests, mock mode, reports/performance/generate)
12. deployment-ui ✅ (13 new smoke tests, full mock API handlers, MockModeBanner)

## Design System (SSOT: unified-trading-ui-kit)

- Dark industrial terminal aesthetic matching deployment-ui
- IBM Plex Sans + JetBrains Mono fonts
- Cyan (#22d3ee) accent, dark backgrounds (#0a0a0b / #111113 / #18181b)
- Status colors: success (#4ade80), warning (#fbbf24), error (#f87171), running (#a78bfa)
- All base components: Button, Card, Badge, Input, Label, Select, Tabs, Checkbox, Dialog
- Layout: PageLayout, AppHeader, SidebarNav, StatusDot

## Mock Mode Requirements (CRITICAL)

Every UI must support mock mode:

- `VITE_MOCK_API=true` env var enables mock mode
- When mock mode is active: bright amber banner at top "MOCK MODE — using simulated data"
- All API calls intercepted and return realistic mock data (no real backend needed)
- Mock data must be rich enough to test all UI features
- Smoke tests always run in mock mode (no real backend dependency)
- Mock mode must be clearly visible so developers/testers know it's active

## Per-UI Tasks

Each UI needs:

1. package.json: Tailwind v4 + @unified-trading/ui-kit + Radix UI + mock mode deps
2. vite.config.ts: @tailwindcss/vite plugin + API proxy
3. src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
4. App.tsx: PageLayout + AppHeader + SidebarNav from ui-kit + mock mode provider
5. src/lib/mock-api.ts: MSW or fetch intercept handlers for all API routes
6. src/components/MockModeBanner.tsx: visible amber banner when `VITE_MOCK_API=true`
7. All pages: use ui-kit components, institutional table/card/form patterns
8. playwright.config.ts: e2e test config
9. e2e/smoke.spec.ts: 15+ smoke tests covering all major features
10. .env.test: `VITE_MOCK_API=true` (used by playwright)

## Mock Mode Implementation Pattern

```typescript
// src/lib/mock-api.ts - per-UI mock handlers
export const MOCK_MODE = import.meta.env.VITE_MOCK_API === "true";

// Install fetch interceptor in dev/test mode
export function installMockHandlers() {
  if (!MOCK_MODE) return;
  // Override global fetch for /api/* routes
  const originalFetch = window.fetch;
  window.fetch = async (input, init) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    if (url.startsWith("/api/")) {
      return handleMockRoute(url, init);
    }
    return originalFetch(input, init);
  };
}
```

## Smoke Test Pattern

```typescript
// e2e/smoke.spec.ts - all tests use mock mode
test.use({ baseURL: "http://localhost:5173" });

test.beforeEach(async ({ page }) => {
  // Intercept all API calls with Playwright route mocking
  await page.route("/api/**", mockApiHandler);
});
```

## Priorities

- P0: unified-trading-ui-kit (DONE)
- P0: onboarding-ui (DONE)
- P1: execution-analytics-ui, strategy-ui, settlement-ui
- P1: deployment-ui mock mode
- P2: live-health-monitor-ui, logs-dashboard-ui, ml-training-ui
- P3: trading-analytics-ui, batch-audit-ui, client-reporting-ui

## Tasks

### T1 — unified-trading-ui-kit ✅

- [x] Create package: `@unified-trading/ui-kit`
- [x] Design tokens: CSS variables for all colors, fonts, spacing
- [x] Base components: Button, Card, Badge, Input, Label, Select, Tabs, Checkbox, Dialog
- [x] Layout components: PageLayout, AppHeader, SidebarNav, StatusDot
- [x] `globals.css`: @import fonts + CSS variable declarations
- [x] `npm run build` passes; `tsc --noEmit` passes

### T2 — onboarding-ui ✅

- [x] package.json: Tailwind v4 + @unified-trading/ui-kit
- [x] vite.config.ts: @tailwindcss/vite plugin
- [x] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [x] App.tsx: PageLayout + AppHeader + SidebarNav
- [x] src/lib/mock-api.ts: mock handlers for onboarding API routes
- [x] src/components/MockModeBanner.tsx
- [x] e2e/smoke.spec.ts: 16 smoke tests (all passing)
- [x] .env.test: `VITE_MOCK_API=true`

### T3 — execution-analytics-ui ✅

- [x] All tasks complete — 13 smoke tests, 11 pages, mock mode active

### T4 — strategy-ui ✅

- [x] All tasks complete — 13 smoke tests, 4 pages, mock mode active

### T5 — settlement-ui ✅

- [x] All tasks complete — 9 smoke tests, positions/invoices/reports, mock mode active

### T6 — deployment-ui (mock mode addition) ✅

- [x] src/lib/mock-api.ts: full handlers for all deployment API routes
- [x] src/components/MockModeBanner.tsx: amber banner
- [x] App.tsx: MockModeBanner wired
- [x] .env.test: VITE_MOCK_API=true
- [x] playwright.config.ts: VITE_MOCK_API env injected; 13 new tests added

### T7 — live-health-monitor-ui ✅

- [x] All tasks complete — 9 smoke tests, dashboard/health pages, mock mode active

### T8 — logs-dashboard-ui ✅

- [x] All tasks complete — 9 smoke tests, log stream/detail, mock mode active

### T9 — ml-training-ui ✅

- [x] All tasks complete — 14 smoke tests, experiments/models/detail, mock mode active

### T10 — trading-analytics-ui ✅

- [x] All tasks complete — 14 smoke tests, orderbook (live depth bars, symbol selector) + latency, mock mode active

### T11 — batch-audit-ui ✅

- [x] All tasks complete — 13 smoke tests, jobs table + job detail + error banner, mock mode active

### T12 — client-reporting-ui ✅

- [x] All tasks complete — 11 smoke tests, reports/performance/generate tabs, mock mode active

### T13 — Registration + Codex

- [x] Write plan to `plans/active/ui_design_system_upgrade_2026_03_10.plan.md`
- [x] Add entry #36 to `plans/active/INDEX.md`
- [x] Register in `unified-trading-codex/00-SSOT-INDEX.md`

## Quality Gates

- Each UI: `npm run build` must pass
- Each UI: `tsc --noEmit` must pass
- Each UI: `playwright test` must pass (in mock mode)
- No real backend dependency for any test

## Verification

```bash
# ui-kit — build passes
cd unified-trading-ui-kit && npm run build

# Per-UI — build + typecheck
cd <ui-repo> && npm run build && tsc --noEmit

# Per-UI — smoke tests in mock mode
cd <ui-repo> && VITE_MOCK_API=true npx playwright test

# Confirm mock banner renders
# All smoke tests should assert: await expect(page.locator('[data-testid="mock-mode-banner"]')).toBeVisible()
```

## Notes

- `VITE_MOCK_API=true` is the single env var that gates mock mode — no code-path divergence in production.
- The amber mock mode banner (`data-testid="mock-mode-banner"`) must be asserted in the first smoke test of every
  `smoke.spec.ts` file to guarantee mock mode is actually active during test runs.
- All fetch interceptors in `mock-api.ts` must be installed before the first render — call `installMockHandlers()` at
  the top of `main.tsx` (before `ReactDOM.createRoot`).
- `@unified-trading/ui-kit` is a local workspace package — reference it via `file:../unified-trading-ui-kit` in each
  UI's `package.json` for local development.
