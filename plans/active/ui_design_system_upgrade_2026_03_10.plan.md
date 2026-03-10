---
id: ui_design_system_upgrade_2026_03_10
title: UI Design System Upgrade — Institutional Dark Terminal Aesthetic Across All UI Repos
status: IN_PROGRESS
priority: P1
created: 2026-03-10
owner: agent
---

# UI Design System Upgrade — 2026-03-10

## Goal

Apply the deployment-ui institutional dark terminal aesthetic uniformly across all 10 UI repos. Create a shared
@unified-trading/ui-kit component library as the SSOT for all UI styling. Add mock mode infrastructure to every UI so
that full E2E smoke tests can run without a real backend.

## Status: IN PROGRESS

## Repos in scope

1. unified-trading-ui-kit (NEW — shared library, SSOT for design tokens + components)
2. onboarding-ui (DONE — upgraded to ui-kit, 16 smoke tests)
3. execution-analytics-ui (TODO)
4. strategy-ui (TODO)
5. settlement-ui (TODO)
6. live-health-monitor-ui (TODO)
7. logs-dashboard-ui (TODO)
8. ml-training-ui (TODO)
9. trading-analytics-ui (TODO)
10. batch-audit-ui (TODO)
11. client-reporting-ui (TODO)
12. deployment-ui (TODO — add mock mode + mock mode banner)

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

### T3 — execution-analytics-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for execution analytics routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

### T4 — strategy-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for strategy routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

### T5 — settlement-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for settlement routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

### T6 — deployment-ui (mock mode addition)

- [ ] src/lib/mock-api.ts: mock handlers for all deployment API routes
- [ ] src/components/MockModeBanner.tsx: amber banner when `VITE_MOCK_API=true`
- [ ] App.tsx: wire mock mode provider
- [ ] .env.test: `VITE_MOCK_API=true`
- [ ] playwright tests: run in mock mode

### T7 — live-health-monitor-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for health monitor routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

### T8 — logs-dashboard-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for logs dashboard routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

### T9 — ml-training-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for ML training routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

### T10 — trading-analytics-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for trading analytics routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

### T11 — batch-audit-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for batch audit routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

### T12 — client-reporting-ui

- [ ] package.json: Tailwind v4 + @unified-trading/ui-kit
- [ ] vite.config.ts: @tailwindcss/vite plugin
- [ ] src/index.css: `@import "@unified-trading/ui-kit/globals.css"`
- [ ] App.tsx: ui-kit layout + mock mode provider
- [ ] src/lib/mock-api.ts: mock handlers for client reporting routes
- [ ] src/components/MockModeBanner.tsx
- [ ] All pages: use ui-kit components
- [ ] e2e/smoke.spec.ts: 15+ smoke tests
- [ ] .env.test: `VITE_MOCK_API=true`

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
