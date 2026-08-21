---
doc_type: plan
title: agent1-shell-navigation
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-22'
overview: Remove card landing pages, wire direct-to-tab routing, restore orphaned components, add Debug Footer with Reset Demo
todos:
- {id: a1-p0-remove-key-landing, content: '- [x] [AGENT] P0. Delete `app/(platform)/services/[key]/page.tsx` (dynamic card landing page) and the `SERVICE_SECTIONS` / `SERVICE_REGISTRY` definitions it uses. Each lifecycle nav dropdown item should link DIRECTLY to the first tab of that service (e.g. "Trading" → `/services/trading/overview`, NOT `/services/trading`).

    ', status: done}
- {id: a1-p0-remove-overview-hub, content: '- [x] [AGENT] P0. Remove `/services/overview` as a route. Update all references to point to `/dashboard` instead. The post-login landing page for internal users is `/dashboard` (Command Center).

    ', status: done}
- {id: a1-p0-remove-portal-redirects, content: '- [x] [AGENT] P0. Remove all `/portal/*` pages (portal/page.tsx, portal/dashboard, portal/backtesting, portal/data, portal/execution, portal/investment, portal/login, portal/regulatory, portal/whitelabel). These are all dead redirects. Client personas land on `/dashboard` or `/services/data/overview` depending on entitlement tier.

    ', status: done}
- {id: a1-p1-wire-batch-live-rail, content: '- [x] [AGENT] P0. Wire `components/platform/batch-live-rail.tsx` (currently zero imports — dead code). Import and render it in the Trading Terminal page (`services/trading/overview`) and the Dashboard page. It should toggle `useGlobalScope().setMode("live" | "batch")` and when in batch mode, show a date picker that sets `useGlobalScope().setAsOfDatetime(date)`. The existing `LiveBatchComparison` component on the dashboard already reads this state — verify it works end-to-end.

    ', status: done}
- {id: a1-p1-wire-filter-bar, content: '- [x] [AGENT] P1. Wire `components/platform/filter-bar.tsx` (currently zero imports — dead code). Import and render it on data table pages: Positions, Orders, Alerts, Fills. It should provide quick filters (venue, status, instrument, date range) that filter the table data.

    ', status: done}
- {id: a1-p1-wire-candidate-basket, content: '- [x] [AGENT] P0. Wire `components/platform/candidate-basket.tsx` (currently dead code). Import and render it on the Promote > Review Queue page (`services/research/strategy/candidates`). It should show strategies selected for promotion review, with approve/reject actions.

    ', status: done}
- {id: a1-p1-wire-live-asof-toggle, content: '- [x] [AGENT] P1. Verify `components/platform/live-asof-toggle.tsx` is rendered in every service layout that has `LIVE_ASOF_VISIBLE[stage] = true`. Currently wired in trading layout — verify data, research, execute, and observe layouts also include it.

    ', status: done}
- {id: a1-p1-verify-global-scope-filters, content: "- [x] [AGENT] P0. Verify `components/platform/global-scope-filters.tsx` renders Org, Client, and Strategy dropdowns in the lifecycle nav center section. These MUST be visible on EVERY authenticated page. Verify:\n  1. Org dropdown shows all orgs for admin, only the client's org for client personas\n  2. Client dropdown cascades from org selection\n  3. Strategy dropdown shows strategies filtered by selected org/client\n  4. ALL service pages read from `useGlobalScope()` and filter their data accordingly\n  5. The orphaned `OrgClientSelector` component is either wired into GlobalScopeFilters or its functionality is confirmed covered\n  6. Changing a filter updates data on the current page without navigation (React Query refetch)\n", status: done}
- {id: a1-p2-debug-footer, content: "- [x] [AGENT] P0. Create a `components/shell/debug-footer.tsx` component that is ONLY visible when `NEXT_PUBLIC_MOCK_API=true` or when the API returns `mock_mode: true` in its health check. The footer should contain:\n  1. \"Reset Demo\" button — calls `resetDemo()` from `lib/reset-demo.ts` AND calls `POST /admin/reset` on the API to reset backend mock state\n  2. Current persona display (from `useAuth().user.role`)\n  3. \"Mock Mode\" indicator badge\n  4. Persona switcher dropdown (same options as the existing user menu sub-menu, but more visible)\nRender this footer in `components/shell/unified-shell.tsx` at the bottom of the page.\n", status: done}
- {id: a1-p2b-runtime-mode-shell, content: "- [x] [AGENT] P0. **Runtime truthfulness (SSOT: CITADEL_VISION § Runtime mode: env vars, CLI, health, and UI truthfulness).** Implement in `unified-shell.tsx` (or dedicated `components/shell/runtime-mode-strip.tsx`):\n  1. **Environment badge** — always visible in dev/staging/prod: `NEXT_PUBLIC_APP_ENV` → DEV | STAGING | PROD (distinct colors; prod subtle).\n  2. **Runtime strip** — compact line: integration profile (`NEXT_PUBLIC_UI_INTEGRATION`: slim | full_mesh | tier0_offline), **effective tier** + **declared tier** if they differ (from API `GET /readiness` once Agent 5 lands; until then parse minimal health or show \"unknown\").\n  3. **API / readiness poll** — interval poll `unified-trading-api` readiness; show Reachable | Degraded | Offline; on Degraded, show **first** `degraded_reasons` or failed `upstream_checks[].name`.\n  4. **Blocking banner** — when declared tier > effective tier (e.g. wants Tier 2, upstream missing), non-dismissible\
    \ banner naming missing service + hint (env var / port / run `dev-start.sh --profile`).\n  5. **`NEXT_PUBLIC_DEBUG_RUNTIME=true`** — link or drawer to pretty-print readiness JSON for developers.\n  DEPENDENCY: readiness JSON shape from Agent 5; until merged, stub UI with env-only display + TODO.\n", status: done}
- {id: a1-p3-fix-lifecycle-nav-links, content: "- [x] [AGENT] P0. Update `buildLifecycleNav()` in `lib/lifecycle-mapping.ts`:\n  1. Add \"execute\" as a new lifecycle stage between \"run\" and \"observe\" (label: \"Execute\", icon: Zap, color: text-orange-400, description: \"Execution algos, venue connectivity, TCA (Execution)\")\n  2. For \"Run\" stage: \"Command Center\" → /dashboard, \"Trading Terminal\" → /services/trading/overview\n  3. For \"Execute\" stage: \"Execution Analytics\" → /services/execution/overview\n  4. Remove \"Execution Analytics\" from Run dropdown (it's now under Execute)\n  5. Ensure clicking any dropdown item goes directly to the first tab — no intermediate landing\n  6. Add EXECUTE_TABS to service-tabs.tsx: Analytics | Algos | Venues | TCA | Benchmarks | Candidates | Handoff\n", status: done}
- {id: a1-p3-fix-breadcrumbs, content: '- [x] [AGENT] P1. Update `components/shell/breadcrumbs.tsx` to show: Home > Service > Tab for every service page. Ensure "Home" always links to `/dashboard`. Add a "← Back to Command Center" quick-link at the top of every service page.

    ', status: done}
- {id: a1-p3-service-tab-routing, content: '- [x] [AGENT] P0. Ensure every service area has a layout.tsx that renders `ServiceTabs` with the correct tab set. Verify/create: data/layout.tsx (DATA_TABS), research/layout.tsx (BUILD_TABS), execution/layout.tsx (EXECUTE_TABS — new), trading/layout.tsx (TRADING_TABS — remove Execution Analytics tab), manage/layout.tsx (MANAGE_TABS), reports/layout.tsx (REPORTS_TABS). For observe: either create observe/layout.tsx or ensure trading/risk and trading/alerts use OBSERVE_TABS when accessed from the Observe lifecycle stage. ALL service pages use tabs — NO card-based landing pages for any service.

    ', status: done}
- {id: a1-p3b-wire-cmdk, content: '- [x] [AGENT] P0. Wire the existing `components/ui/command.tsx` (cmdk library) to a global `Cmd+K` / `Ctrl+K` keyboard shortcut. Register the shortcut in the shell layout (`components/shell/unified-shell.tsx`). The command palette should search across: service names (navigate to service), strategy names (navigate to strategy detail), instrument names, and quick actions (Reset Demo, Toggle Batch/Live). Use the existing `CommandDialog` wrapper. This is a key institutional UX feature — every Bloomberg/Citadel terminal has keyboard-driven navigation.

    ', status: done}
- {id: a1-p3b-notification-bell, content: "- [x] [AGENT] P0. Wire the notification bell icon in `components/shell/lifecycle-nav.tsx` to show real alerts. Currently hardcoded to \"3\". Replace with:\n  1. Call `GET /alerts/active?acknowledged=false` via `useAlerts()` hook to get actual count\n  2. Show count as badge (or hide badge if 0)\n  3. On click: open a DropdownMenu with the 5 most recent alerts (severity badge, message, relative timestamp)\n  4. Each alert has an \"Acknowledge\" button that calls `POST /alerts/{id}/acknowledge`\n  5. \"View All Alerts\" link at bottom navigates to `/services/observe/alerts`\n", status: done}
- {id: a1-p3b-skeleton-loading, content: "- [x] [AGENT] P1. Create reusable skeleton loading components for common page patterns. The existing `components/ui/skeleton.tsx` is underutilized — most pages show \"Loading...\" text instead of shimmer placeholders. Create:\n  1. `components/ui/table-skeleton.tsx` — renders N skeleton rows matching table column widths\n  2. `components/ui/card-grid-skeleton.tsx` — renders N skeleton cards in a grid\n  3. `components/ui/chart-skeleton.tsx` — renders a chart-shaped skeleton area\n  Then update the pattern in ALL service pages: replace `if (isLoading) return <div>Loading...</div>` with the appropriate skeleton component. This is mandatory per CITADEL_VISION visual polish standards.\n", status: done}
- {id: a1-p3b-persona-relogin, content: '- [x] [AGENT] P0. Update the persona switcher in the debug footer (and any persona dropdown in the user menu). When a user clicks a different persona, it MUST redirect to the login page (`/login`) with the new persona pre-selected (e.g. `/login?persona=client-full`). It must NOT instant-swap the token in memory. The user clicks "Sign In" on the login page to complete the switch. This ensures the JWT is properly re-issued by auth-api and all API calls use the new token. Update `lib/reset-demo.ts` or the debug footer component accordingly.

    ', status: done}
- {id: a1-p4-smoke-build, content: '- [x] [AGENT] P1. Run `NEXT_PUBLIC_MOCK_API=true npx next build` and fix any build errors. All removed routes should not cause 404s during build — add redirects in next.config.mjs where needed.

    ', status: done}
- {id: a1-p4-test-navigation, content: '- [x] [AGENT] P1. Add/update Playwright tests: 1) Login as admin → verify all 7 lifecycle stages visible. 2) Login as client-data-only → verify only Acquire visible, rest shows "Upgrade". 3) Click each lifecycle dropdown → verify lands on correct first tab (not card landing). 4) Click Reset Demo → verify page reloads to clean state.

    ', status: done}
- {id: a1-p5-error-boundary, content: "- [x] [AGENT] P0. Create shared error/empty state components:\n  1. `components/ui/error-boundary.tsx` — React error boundary wrapping service pages. Catches render errors, shows \"Something went wrong\" with Retry button and \"Return to Dashboard\" link. Logs error to console.\n  2. `components/ui/api-error.tsx` — Standard API error display. Props: error object, onRetry callback. Shows: error icon, message, \"Retry\" button. Used as: `if (isError) return <ApiError error={error} onRetry={refetch} />`\n  3. `components/ui/empty-state.tsx` — Standard empty state. Props: icon, title, description, optional action (label + onClick). Used as: `if (data.length === 0) return <EmptyState title=\"No positions\" description=\"Open the Trading Terminal to place your first trade\" action={{ label: \"Open Terminal\", onClick: ... }} />`\n  4. Wrap every service layout.tsx with `<ErrorBoundary>` so individual pages don't white-screen the whole app.\n", status: done}
- {id: a1-p5-access-denied, content: '- [x] [AGENT] P0. Create `components/platform/upgrade-card.tsx` — shown when a client persona lacks entitlements for a service. Props: serviceName, description. Shows service icon, "Upgrade to access {serviceName}", description of what they''d get, "Contact Sales" button. Wire into each service layout: if `!userEntitlements.includes(requiredEntitlement)`, show UpgradeCard instead of page content. Non-admin accessing /admin routes: redirect to /dashboard via middleware or layout check.

    ', status: done}
- {id: a1-p5-responsive-shell, content: "- [x] [AGENT] P1. Make the shell responsive:\n  1. `lifecycle-nav.tsx`: Add hamburger menu icon (visible at `md:hidden`). On click, open a slide-out drawer with the same lifecycle stages. Desktop nav hidden below md breakpoint.\n  2. `global-scope-filters.tsx`: Stack filters vertically below lg breakpoint. Use collapsible panel on tablet.\n  3. `service-tabs.tsx`: On narrow screens, tabs should horizontally scroll (not wrap to multiple lines). Add `overflow-x-auto` with `-webkit-overflow-scrolling: touch`.\n  4. `debug-footer.tsx`: Stack items vertically on narrow screens.\n  5. Add `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />` if not already in layout.\n", status: done}
- {id: a1-p5-code-splitting, content: "- [x] [AGENT] P1. Add dynamic imports for heavy service page components to reduce initial bundle:\n  1. All charting components (candlestick, equity curve, heatmap, order book visualization) MUST use `dynamic(() => import(...), { ssr: false })` since they depend on browser APIs.\n  2. Deployment form components (from deployment-ui absorption) — dynamically imported.\n  3. Data grid components with complex filtering — dynamically imported.\n  4. Run `NEXT_PUBLIC_MOCK_API=true npx next build` and check chunk sizes in output. Flag any chunk > 500KB.\n", status: done}
- {id: a1-p5-ws-reconnect, content: '- [x] [AGENT] P1. Create `components/ui/ws-reconnect-banner.tsx` — a subtle top banner that appears when the WebSocket connection drops. Shows "Connection lost — reconnecting..." with a spinner. Auto-hides when reconnected. Wire into unified-shell.tsx. The WebSocket hook should implement exponential backoff reconnection (1s, 2s, 4s, max 30s) and emit connection state changes.

    ', status: done}
- {id: a1-p6-tanstack-table, content: "- [x] [AGENT] P0. Install TanStack Table and create reusable DataTable component:\n  1. Run `npm install @tanstack/react-table @tanstack/react-virtual` in unified-trading-system-ui\n  2. Create `components/ui/data-table.tsx` — wraps TanStack Table with: column sorting (click header), column visibility toggle (dropdown), column resizing (drag borders), row virtualization for 1000+ rows (via @tanstack/react-virtual), persistent column preferences (save to Zustand `ui-prefs-store.ts` via localStorage)\n  3. This component replaces the current shadcn `<Table>` for ALL data-heavy pages\n  4. Export as `DataTable` — other agents (2-4, 7) adopt it for positions, orders, fills, alerts, settlements, experiments, audit trail, deployments\n  DEPENDENCY: None — can start immediately. All table-using agents depend on this.\n", status: done}
- {id: a1-p6-workspace-persistence, content: "- [x] [AGENT] P1. Extend Zustand `ui-prefs-store.ts` for workspace persistence:\n  1. Add zustand `persist` middleware to save to localStorage\n  2. Persist: global scope filters (org, client, strategy, mode), per-table column visibility/order (TanStack Table state), panel sizes (react-resizable-panels — already installed), last visited service page\n  3. On page reload, all filters and layout preferences are restored\n  4. Add `resetPreferences()` method called by Reset Demo\n  DEPENDENCY: None — zustand and react-resizable-panels already installed.\n", status: done}
- {id: a1-p6-guided-tour, content: "- [x] [AGENT] P1. Add guided tour for first-time users and demo walkthroughs:\n  1. Run `npm install react-joyride`\n  2. Create `components/platform/guided-tour.tsx` wrapping react-joyride\n  3. Steps: Global scope filters → Lifecycle nav → Trading Terminal → Cmd+K → Batch/Live toggle → Reset Demo\n  4. Triggered on first login (localStorage check) OR \"Take Tour\" button in debug footer\n  5. Tour completion persisted — don't re-show unless clicked\n  DEPENDENCY: Navigation (Phase 3) and debug footer (Phase 2) must be done first.\n", status: done}
- {id: a1-p6-desktop-notifications, content: "- [x] [AGENT] P1. Wire desktop notifications and Sonner toasts:\n  1. Request browser Notification API permission on first login\n  2. For critical/high alerts from `useAlerts()`, push desktop notification (even when tab unfocused)\n  3. Wire Sonner (already at `components/ui/sonner.tsx`) for ALL mutations: order placed, alert acknowledged, reset demo, API errors\n  4. Add notification sound toggle in ui-prefs-store (default: on for critical only)\n  DEPENDENCY: Agent 5's alert endpoints must be working.\n", status: done}
- {id: a1-p7-data-freshness, content: "- [x] [AGENT] P0. Create `components/ui/data-freshness.tsx` — shows data staleness on every data panel header:\n  1. Props: `lastUpdated: Date | null`, `isWebSocket?: boolean`\n  2. WebSocket-connected: green dot + \"Live\" badge\n  3. REST-fetched: \"Updated Xs ago\" — green (<5s), yellow (5-30s), red (>30s)\n  4. Disconnected: red dot + \"Disconnected\"\n  5. Batch mode: \"As of {date}\" badge (no staleness — batch is a snapshot by definition)\n  Render on every data panel header that shows real-time or fetched data. This makes WebSocket-fed panels (Trading Terminal, Positions, Dashboard PnL) visually distinct from batch data panels — reinforcing the batch/live story.\n  DEPENDENCY: None — can start immediately.\n", status: done}
- {id: a1-p7-xlsx-utility, content: "- [x] [AGENT] P0. Install SheetJS and create shared export utility:\n  1. Run `npm install xlsx` in unified-trading-system-ui\n  2. Create `lib/utils/export.ts` with three functions:\n     - `exportTableToCsv(data, columns, filename)` — CSV download\n     - `exportTableToXlsx(data, columns, filename)` — single-sheet Excel with bold headers, right-aligned numbers, formatted dates, sheet name = filename\n     - `exportMultiSheetXlsx(sheets: {name, data, columns}[], filename)` — multi-sheet workbook (for Reports: P&L on sheet 1, positions on sheet 2, orders on sheet 3)\n  3. Create `components/ui/export-button.tsx` — split button `[Export ▾]` with dropdown: CSV | Excel\n  4. All agents (2-4, 7) use this component instead of building their own export buttons\n  NOTE: If Agent 2 has already created export.ts (a2-p7-export-tables), Agent 1 should verify and enhance rather than duplicate. Check first.\n  DEPENDENCY: None — can start immediately.\n", status: done}
- {id: a1-p8-refresh-manifest, content: "- [x] [AGENT] P0. Refresh `UI_STRUCTURE_MANIFEST.json` to match actual wiring state after all agents completed. The manifest currently says BatchLiveRail has \"zero imports\" but it's wired in 4 files (dashboard, trading/overview, research/strategy/compare, research/strategy/results). FilterBar is wired in 3 files (trading/alerts, positions, orders). Update:\n  1. Set BatchLiveRail imports to 4 (list the files)\n  2. Set FilterBar imports to 3 (list the files)\n  3. Update dead tab sets status: verify if PROMOTE_TABS, OBSERVE_TABS, MANAGE_TABS now have layouts rendering them (agents created layouts)\n  4. Update page states: pages that were STUB are now REAL after agent work\n  5. Update `pages_needing_api_wiring` count — most pages are now wired\n  6. Update any satellite absorption status (deployment-ui, settlement-ui, etc. patterns absorbed)\n  This manifest is the SSOT for UI structure — it must reflect the current reality.\n", status: done}
- {id: a1-p8-clean-worktrees, content: "- [x] [AGENT] P1. Remove `.claude/worktrees/` remnants from old agent sessions in unified-trading-system-ui. These contain duplicate/stale copies of components and pages from prior agent runs (agent-a18a06ab, agent-a9aade31, etc.). They are not referenced by the build and just add confusion.\n  1. `rm -rf unified-trading-system-ui/.claude/worktrees/`\n  2. Verify `npx next build` still succeeds after removal\n  3. Add `.claude/worktrees/` to `.gitignore` if not already there\n", status: done}
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — SSOT for all page states, routes, and source files
2. Read `unified-trading-pm/plans/archive/CITADEL_VISION_2026_03_22.md` — system-wide vision

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
(platform)/services/manage/ for tabs to work. MITIGATION: Either move pages or create a redirect layout. Document
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
- **Workspace persistence** (P1): Zustand persist middleware for filters, columns, panel sizes. Foundation already
  exists.
- **Guided tour** (P1): react-joyride for first-time users and demo walkthroughs. Requires navigation to be stable.
- **Desktop notifications + Sonner toasts** (P1): Browser notifications for critical alerts. Sonner already installed.
- Dark mode ALREADY EXISTS (Citadel-inspired cyan theme in globals.css) — no work needed.
