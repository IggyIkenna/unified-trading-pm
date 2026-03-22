---
name: agent1-shell-navigation
overview:
  Remove card landing pages, wire direct-to-tab routing, restore orphaned components, add Debug Footer with Reset Demo
todos:
  - id: a1-p0-remove-key-landing
    content: |
      - [ ] [AGENT] P0. Delete `app/(platform)/services/[key]/page.tsx` (dynamic card landing page) and the `SERVICE_SECTIONS` / `SERVICE_REGISTRY` definitions it uses. Each lifecycle nav dropdown item should link DIRECTLY to the first tab of that service (e.g. "Trading" → `/services/trading/overview`, NOT `/services/trading`).
    status: todo
  - id: a1-p0-remove-overview-hub
    content: |
      - [ ] [AGENT] P0. Remove `/services/overview` as a route. Update all references to point to `/dashboard` instead. The post-login landing page for internal users is `/dashboard` (Command Center).
    status: todo
  - id: a1-p0-remove-portal-redirects
    content: |
      - [ ] [AGENT] P0. Remove all `/portal/*` pages (portal/page.tsx, portal/dashboard, portal/backtesting, portal/data, portal/execution, portal/investment, portal/login, portal/regulatory, portal/whitelabel). These are all dead redirects. Client personas land on `/dashboard` or `/services/data/overview` depending on entitlement tier.
    status: todo
  - id: a1-p1-wire-batch-live-rail
    content: |
      - [ ] [AGENT] P0. Wire `components/platform/batch-live-rail.tsx` (currently zero imports — dead code). Import and render it in the Trading Terminal page (`services/trading/overview`) and the Dashboard page. It should toggle `useGlobalScope().setMode("live" | "batch")` and when in batch mode, show a date picker that sets `useGlobalScope().setAsOfDatetime(date)`. The existing `LiveBatchComparison` component on the dashboard already reads this state — verify it works end-to-end.
    status: todo
  - id: a1-p1-wire-filter-bar
    content: |
      - [ ] [AGENT] P1. Wire `components/platform/filter-bar.tsx` (currently zero imports — dead code). Import and render it on data table pages: Positions, Orders, Alerts, Fills. It should provide quick filters (venue, status, instrument, date range) that filter the table data.
    status: todo
  - id: a1-p1-wire-candidate-basket
    content: |
      - [ ] [AGENT] P0. Wire `components/platform/candidate-basket.tsx` (currently dead code). Import and render it on the Promote > Review Queue page (`services/research/strategy/candidates`). It should show strategies selected for promotion review, with approve/reject actions.
    status: todo
  - id: a1-p1-wire-live-asof-toggle
    content: |
      - [ ] [AGENT] P1. Verify `components/platform/live-asof-toggle.tsx` is rendered in every service layout that has `LIVE_ASOF_VISIBLE[stage] = true`. Currently wired in trading layout — verify data, research, execute, and observe layouts also include it.
    status: todo
  - id: a1-p1-verify-global-scope-filters
    content: |
      - [ ] [AGENT] P0. Verify `components/platform/global-scope-filters.tsx` renders Org, Client, and Strategy dropdowns in the lifecycle nav center section. These MUST be visible on EVERY authenticated page. Verify:
        1. Org dropdown shows all orgs for admin, only the client's org for client personas
        2. Client dropdown cascades from org selection
        3. Strategy dropdown shows strategies filtered by selected org/client
        4. ALL service pages read from `useGlobalScope()` and filter their data accordingly
        5. The orphaned `OrgClientSelector` component is either wired into GlobalScopeFilters or its functionality is confirmed covered
        6. Changing a filter updates data on the current page without navigation (React Query refetch)
    status: todo
  - id: a1-p2-debug-footer
    content: |
      - [ ] [AGENT] P0. Create a `components/shell/debug-footer.tsx` component that is ONLY visible when `NEXT_PUBLIC_MOCK_API=true` or when the API returns `mock_mode: true` in its health check. The footer should contain:
        1. "Reset Demo" button — calls `resetDemo()` from `lib/reset-demo.ts` AND calls `POST /admin/reset` on the API to reset backend mock state
        2. Current persona display (from `useAuth().user.role`)
        3. "Mock Mode" indicator badge
        4. Persona switcher dropdown (same options as the existing user menu sub-menu, but more visible)
      Render this footer in `components/shell/unified-shell.tsx` at the bottom of the page.
    status: todo
  - id: a1-p3-fix-lifecycle-nav-links
    content: |
      - [ ] [AGENT] P0. Update `buildLifecycleNav()` in `lib/lifecycle-mapping.ts`:
        1. Add "execute" as a new lifecycle stage between "run" and "observe" (label: "Execute", icon: Zap, color: text-orange-400, description: "Execution algos, venue connectivity, TCA (Execution)")
        2. For "Run" stage: "Command Center" → /dashboard, "Trading Terminal" → /services/trading/overview
        3. For "Execute" stage: "Execution Analytics" → /services/execution/overview
        4. Remove "Execution Analytics" from Run dropdown (it's now under Execute)
        5. Ensure clicking any dropdown item goes directly to the first tab — no intermediate landing
        6. Add EXECUTE_TABS to service-tabs.tsx: Analytics | Algos | Venues | TCA | Benchmarks | Candidates | Handoff
    status: todo
  - id: a1-p3-fix-breadcrumbs
    content: |
      - [ ] [AGENT] P1. Update `components/shell/breadcrumbs.tsx` to show: Home > Service > Tab for every service page. Ensure "Home" always links to `/dashboard`. Add a "← Back to Command Center" quick-link at the top of every service page.
    status: todo
  - id: a1-p3-service-tab-routing
    content: |
      - [ ] [AGENT] P0. Ensure every service area has a layout.tsx that renders `ServiceTabs` with the correct tab set. Verify/create: data/layout.tsx (DATA_TABS), research/layout.tsx (BUILD_TABS), execution/layout.tsx (EXECUTE_TABS — new), trading/layout.tsx (TRADING_TABS — remove Execution Analytics tab), manage/layout.tsx (MANAGE_TABS), reports/layout.tsx (REPORTS_TABS). For observe: either create observe/layout.tsx or ensure trading/risk and trading/alerts use OBSERVE_TABS when accessed from the Observe lifecycle stage. ALL service pages use tabs — NO card-based landing pages for any service.
    status: todo
  # ── Phase 3B: Visual Polish (Real-Time Feel) ──
  - id: a1-p3b-wire-cmdk
    content: |
      - [ ] [AGENT] P0. Wire the existing `components/ui/command.tsx` (cmdk library) to a global `Cmd+K` / `Ctrl+K` keyboard shortcut. Register the shortcut in the shell layout (`components/shell/unified-shell.tsx`). The command palette should search across: service names (navigate to service), strategy names (navigate to strategy detail), instrument names, and quick actions (Reset Demo, Toggle Batch/Live). Use the existing `CommandDialog` wrapper. This is a key institutional UX feature — every Bloomberg/Citadel terminal has keyboard-driven navigation.
    status: todo
  - id: a1-p3b-notification-bell
    content: |
      - [ ] [AGENT] P0. Wire the notification bell icon in `components/shell/lifecycle-nav.tsx` to show real alerts. Currently hardcoded to "3". Replace with:
        1. Call `GET /alerts/active?acknowledged=false` via `useAlerts()` hook to get actual count
        2. Show count as badge (or hide badge if 0)
        3. On click: open a DropdownMenu with the 5 most recent alerts (severity badge, message, relative timestamp)
        4. Each alert has an "Acknowledge" button that calls `POST /alerts/{id}/acknowledge`
        5. "View All Alerts" link at bottom navigates to `/services/observe/alerts`
    status: todo
  - id: a1-p3b-skeleton-loading
    content: |
      - [ ] [AGENT] P1. Create reusable skeleton loading components for common page patterns. The existing `components/ui/skeleton.tsx` is underutilized — most pages show "Loading..." text instead of shimmer placeholders. Create:
        1. `components/ui/table-skeleton.tsx` — renders N skeleton rows matching table column widths
        2. `components/ui/card-grid-skeleton.tsx` — renders N skeleton cards in a grid
        3. `components/ui/chart-skeleton.tsx` — renders a chart-shaped skeleton area
        Then update the pattern in ALL service pages: replace `if (isLoading) return <div>Loading...</div>` with the appropriate skeleton component. This is mandatory per CITADEL_VISION visual polish standards.
    status: todo
  - id: a1-p3b-persona-relogin
    content: |
      - [ ] [AGENT] P0. Update the persona switcher in the debug footer (and any persona dropdown in the user menu). When a user clicks a different persona, it MUST redirect to the login page (`/login`) with the new persona pre-selected (e.g. `/login?persona=client-full`). It must NOT instant-swap the token in memory. The user clicks "Sign In" on the login page to complete the switch. This ensures the JWT is properly re-issued by auth-api and all API calls use the new token. Update `lib/reset-demo.ts` or the debug footer component accordingly.
    status: todo
  - id: a1-p4-smoke-build
    content: |
      - [ ] [AGENT] P1. Run `NEXT_PUBLIC_MOCK_API=true npx next build` and fix any build errors. All removed routes should not cause 404s during build — add redirects in next.config.mjs where needed.
    status: todo
  - id: a1-p4-test-navigation
    content: |
      - [ ] [AGENT] P1. Add/update Playwright tests: 1) Login as admin → verify all 7 lifecycle stages visible. 2) Login as client-data-only → verify only Acquire visible, rest shows "Upgrade". 3) Click each lifecycle dropdown → verify lands on correct first tab (not card landing). 4) Click Reset Demo → verify page reloads to clean state.
    status: todo
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — SSOT for all page states, routes, and source files
2. Read `unified-trading-pm/plans/active/CITADEL_VISION_2026_03_22.md` — system-wide vision

## TABS-ONLY RULE (enforced by this agent)

- Login → `/dashboard` (Command Center — 9 service cards grouped by lifecycle stage)
- Click any service → lands on ONE page with tabs (the first tab of that service)
- ALL content within a service is via tab switching — NO card-based sub-pages, NO nested landing pages
- The `/services/[key]` dynamic card page (240L) is the ANTI-PATTERN being deleted
- After this agent's work: every service has a layout.tsx rendering its tab set, every lifecycle nav item links to the
  first tab

## Dead Tab Sets to Fix (Agent 1 owns this)

- PROMOTE_TABS: defined in service-tabs.tsx but NO layout renders it → create promote layout or contextual tab switching
- OBSERVE_TABS: defined but NO layout renders it → risk/alerts show TRADING_TABS (wrong) → create observe layout
- MANAGE_TABS: defined but pages live in (ops) route group → fix routing so manage tabs are visible
- EXECUTE_TABS: does not exist yet → create it with: Analytics | Algos | Venues | TCA | Benchmarks | Candidates |
  Handoff

## Absorbed from prior plans

- ui_routing_refactor_2026_03_21: Route deduplication and /service/{service}/{page} convention — DONE, but card landings
  still exist
- ui_lifecycle_service_tab_cross_reference_2026_03_21: Tab definitions per service — DONE in service-tabs.tsx
- plan_e_ui_backend_integration: Phase 0B fix todos for UI->API path mismatch — incorporate into Phase 3
- plan_f_ui_quality_hardening: TypeScript strict mode, build fixes — incorporate into Phase 4

## Key files

- `components/shell/unified-shell.tsx` — main shell wrapper
- `components/shell/lifecycle-nav.tsx` — Row 1 navigation with persona/org switching
- `components/shell/service-tabs.tsx` — Row 2 tab definitions per service
- `lib/lifecycle-mapping.ts` — route-to-lifecycle mapping
- `lib/reset-demo.ts` — existing resetDemo() function
- `lib/stores/global-scope-store.ts` — live/batch mode, org/client/strategy scope

## Orphaned components (exist on disk, zero imports)

- `components/platform/batch-live-rail.tsx`
- `components/platform/filter-bar.tsx`
- `components/platform/candidate-basket.tsx`
- `components/platform/live-asof-toggle.tsx`
- `components/trading/context-bar.tsx` (trading version — can stay dead, platform version covers it)
- `components/trading/org-client-selector.tsx` (functionality in GlobalScopeFilters)
