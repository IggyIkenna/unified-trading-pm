---
name: agent1-shell-navigation
overview:
  Remove card landing pages, wire direct-to-tab routing, restore orphaned components, add Debug Footer with Reset Demo
todos:
  # ── NO UPSTREAM DEPENDENCIES — all phases can start immediately ──────────
  # This agent has NO deps on other agents. All work is in unified-trading-system-ui.
  # Other agents (2, 6, 8) depend on YOUR output (layouts, tab sets, debug footer).
  # Complete Phase 0-3 as fast as possible to unblock them.
  # ─────────────────────────────────────────────────────────────────────────────
  # ── Phase 0: Remove Card Landing Pages (SEQUENTIAL) ──
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
  # ── Phase 5: Error States, Responsive, Code Splitting (Gap-Closing) ──
  - id: a1-p5-error-boundary
    content: |
      - [ ] [AGENT] P0. Create shared error/empty state components:
        1. `components/ui/error-boundary.tsx` — React error boundary wrapping service pages. Catches render errors, shows "Something went wrong" with Retry button and "Return to Dashboard" link. Logs error to console.
        2. `components/ui/api-error.tsx` — Standard API error display. Props: error object, onRetry callback. Shows: error icon, message, "Retry" button. Used as: `if (isError) return <ApiError error={error} onRetry={refetch} />`
        3. `components/ui/empty-state.tsx` — Standard empty state. Props: icon, title, description, optional action (label + onClick). Used as: `if (data.length === 0) return <EmptyState title="No positions" description="Open the Trading Terminal to place your first trade" action={{ label: "Open Terminal", onClick: ... }} />`
        4. Wrap every service layout.tsx with `<ErrorBoundary>` so individual pages don't white-screen the whole app.
    status: todo
  - id: a1-p5-access-denied
    content: |
      - [ ] [AGENT] P0. Create `components/platform/upgrade-card.tsx` — shown when a client persona lacks entitlements for a service. Props: serviceName, description. Shows service icon, "Upgrade to access {serviceName}", description of what they'd get, "Contact Sales" button. Wire into each service layout: if `!userEntitlements.includes(requiredEntitlement)`, show UpgradeCard instead of page content. Non-admin accessing /admin routes: redirect to /dashboard via middleware or layout check.
    status: todo
  - id: a1-p5-responsive-shell
    content: |
      - [ ] [AGENT] P1. Make the shell responsive:
        1. `lifecycle-nav.tsx`: Add hamburger menu icon (visible at `md:hidden`). On click, open a slide-out drawer with the same lifecycle stages. Desktop nav hidden below md breakpoint.
        2. `global-scope-filters.tsx`: Stack filters vertically below lg breakpoint. Use collapsible panel on tablet.
        3. `service-tabs.tsx`: On narrow screens, tabs should horizontally scroll (not wrap to multiple lines). Add `overflow-x-auto` with `-webkit-overflow-scrolling: touch`.
        4. `debug-footer.tsx`: Stack items vertically on narrow screens.
        5. Add `<meta name="viewport" content="width=device-width, initial-scale=1" />` if not already in layout.
    status: todo
  - id: a1-p5-code-splitting
    content: |
      - [ ] [AGENT] P1. Add dynamic imports for heavy service page components to reduce initial bundle:
        1. All charting components (candlestick, equity curve, heatmap, order book visualization) MUST use `dynamic(() => import(...), { ssr: false })` since they depend on browser APIs.
        2. Deployment form components (from deployment-ui absorption) — dynamically imported.
        3. Data grid components with complex filtering — dynamically imported.
        4. Run `NEXT_PUBLIC_MOCK_API=true npx next build` and check chunk sizes in output. Flag any chunk > 500KB.
    status: todo
  - id: a1-p5-ws-reconnect
    content: |
      - [ ] [AGENT] P1. Create `components/ui/ws-reconnect-banner.tsx` — a subtle top banner that appears when the WebSocket connection drops. Shows "Connection lost — reconnecting..." with a spinner. Auto-hides when reconnected. Wire into unified-shell.tsx. The WebSocket hook should implement exponential backoff reconnection (1s, 2s, 4s, max 30s) and emit connection state changes.
    status: todo
  # ── Phase 6: Institutional UX Gap-Closing ──
  - id: a1-p6-tanstack-table
    content: |
      - [ ] [AGENT] P0. Install TanStack Table and create reusable DataTable component:
        1. Run `npm install @tanstack/react-table @tanstack/react-virtual` in unified-trading-system-ui
        2. Create `components/ui/data-table.tsx` — wraps TanStack Table with: column sorting (click header), column visibility toggle (dropdown), column resizing (drag borders), row virtualization for 1000+ rows (via @tanstack/react-virtual), persistent column preferences (save to Zustand `ui-prefs-store.ts` via localStorage)
        3. This component replaces the current shadcn `<Table>` for ALL data-heavy pages
        4. Export as `DataTable` — other agents (2-4, 7) adopt it for positions, orders, fills, alerts, settlements, experiments, audit trail, deployments
        DEPENDENCY: None — can start immediately. All table-using agents depend on this.
    status: todo
  - id: a1-p6-workspace-persistence
    content: |
      - [ ] [AGENT] P1. Extend Zustand `ui-prefs-store.ts` for workspace persistence:
        1. Add zustand `persist` middleware to save to localStorage
        2. Persist: global scope filters (org, client, strategy, mode), per-table column visibility/order (TanStack Table state), panel sizes (react-resizable-panels — already installed), last visited service page
        3. On page reload, all filters and layout preferences are restored
        4. Add `resetPreferences()` method called by Reset Demo
        DEPENDENCY: None — zustand and react-resizable-panels already installed.
    status: todo
  - id: a1-p6-guided-tour
    content: |
      - [ ] [AGENT] P1. Add guided tour for first-time users and demo walkthroughs:
        1. Run `npm install react-joyride`
        2. Create `components/platform/guided-tour.tsx` wrapping react-joyride
        3. Steps: Global scope filters → Lifecycle nav → Trading Terminal → Cmd+K → Batch/Live toggle → Reset Demo
        4. Triggered on first login (localStorage check) OR "Take Tour" button in debug footer
        5. Tour completion persisted — don't re-show unless clicked
        DEPENDENCY: Navigation (Phase 3) and debug footer (Phase 2) must be done first.
    status: todo
  - id: a1-p6-desktop-notifications
    content: |
      - [ ] [AGENT] P1. Wire desktop notifications and Sonner toasts:
        1. Request browser Notification API permission on first login
        2. For critical/high alerts from `useAlerts()`, push desktop notification (even when tab unfocused)
        3. Wire Sonner (already at `components/ui/sonner.tsx`) for ALL mutations: order placed, alert acknowledged, reset demo, API errors
        4. Add notification sound toggle in ui-prefs-store (default: on for critical only)
        DEPENDENCY: Agent 5's alert endpoints must be working.
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

## Risk Factors & Mitigations

**RISK 1: Observe layout is a cross-agent blocker.** Agent 7 cannot render observe pages correctly until this agent
creates observe/layout.tsx with OBSERVE_TABS. Risk/alerts currently show TRADING_TABS (wrong). MITIGATION: Create
observe/layout.tsx in Phase 3 (a1-p3-service-tab-routing) BEFORE Phase 4. Prioritize this.

**RISK 2: Manage pages live in (ops) route group, not (platform).** MANAGE*TABS is defined but never rendered because
manage pages are in app/(ops)/manage/*. The (ops) layout may enforce admin-only access. Agent 4 needs pages in
(platform)/services/manage/\_ for tabs to work. MITIGATION: Either move pages or create a redirect layout. Document
decision for Agent 4.

**RISK 3: Skeleton components created but not adopted by other agents.** MITIGATION: Use EXACT names from CITADEL_VISION
§ Interface Contracts (TableSkeleton, CardGridSkeleton, ChartSkeleton). Add comment at top: "IMPORT THIS — do not create
custom loading states."

**RISK 4: Orphaned components may have stale prop types.** batch-live-rail.tsx, filter-bar.tsx etc. were written for an
older API shape. Props may reference types/stores that no longer exist. MITIGATION: Read each component fully before
wiring. Check every import and prop type. Fix type errors first.

**RISK 5: Persona switcher may not properly clear auth state.** Redirecting to /login is not enough if JWT is cached in
localStorage. Stale tokens = wrong org data. MITIGATION: Explicitly clear token (`localStorage.removeItem("token")`),
clear React auth context, THEN `router.push("/login?persona=X")`.

## Orphaned components (exist on disk, zero imports)

- `components/platform/batch-live-rail.tsx`
- `components/platform/filter-bar.tsx`
- `components/platform/candidate-basket.tsx`
- `components/platform/live-asof-toggle.tsx`
- `components/trading/context-bar.tsx` (trading version — can stay dead, platform version covers it)
- `components/trading/org-client-selector.tsx` (functionality in GlobalScopeFilters)

## New scope (added 2026-03-22 gap analysis)

- Error boundary, API error, and empty state components are NEW P0 requirements — every service page must use them
- Responsive layout: hamburger nav on tablet, stacked panels, horizontal-scroll tabs
- Code splitting: dynamic imports for charts and heavy components
- WebSocket reconnection banner
- Access denied / upgrade card for entitlement-gated services
- These are the gap between "prototype" and "production-grade demo"

## Phase 6 scope (added gap-closing analysis)

- **TanStack Table DataTable component** (P0): ALL data tables across the platform use this. Agents 2-4, 7 depend on it.
- **Workspace persistence** (P1): Zustand persist middleware for filters, columns, panel sizes. Foundation already exists.
- **Guided tour** (P1): react-joyride for first-time users and demo walkthroughs. Requires navigation to be stable.
- **Desktop notifications + Sonner toasts** (P1): Browser notifications for critical alerts. Sonner already installed.
- Dark mode ALREADY EXISTS (Citadel-inspired cyan theme in globals.css) — no work needed.
