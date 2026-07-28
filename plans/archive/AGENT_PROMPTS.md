---
doc_type: plan
title: 8 Agent Prompts for Citadel-Grade System Refactor
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, deployment-ui, unified-api-contracts, unified-trading-api, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-22'
---

# 8 Agent Prompts for Citadel-Grade System Refactor

Each prompt below is self-contained. Copy-paste one prompt per agent session. Every agent gets the full vision context +
their specific workstream.

---

## SHARED PREAMBLE (included in every prompt below)

```
You are executing one workstream of an 8-agent parallel refactor of the Unified Trading System.

BEFORE ANY CODE: Read these files in order:
1. unified-trading-pm/plans/archive/CITADEL_VISION_2026_03_22.md — the complete system vision
2. Your specific plan file (identified below) — your detailed todos
3. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — mandatory coding rules
4. .cursorrules — workspace standards

WORKSPACE: /Users/ikennaigboaka/Code/unified-trading-system-repos/
Each subdirectory is an INDEPENDENT git repo. Only commit to repos you modify.

KEY RULES:
- `uv pip install` not `pip install`
- `bash scripts/quality-gates.sh` for tests (never pytest directly)
- `basedpyright` not `pyright`
- No `os.getenv()` — use `UnifiedCloudConfig`
- Flat deps only in pyproject.toml (no optional-dependencies)
- Do NOT run `bash scripts/quickmerge.sh` unless explicitly told to
- Do NOT run `git reset --hard` under any circumstances

THE BIG PICTURE:
- ONE UI: unified-trading-system-ui (Next.js) — all 13 satellite UIs are being archived
- THREE APIs: auth-api (port 8200, SSO/tokens), client-reporting-api (port 8014, client reports/invoices), unified-trading-api (port 8030, trading system)
- 9 SERVICES: Data, Research, Promote, Trading, Execution, Observe, Manage, Reports, Admin/Ops
- DIRECT-TO-TABS: No card landing pages. Lifecycle nav → first tab of service
- 90% CODE SHARING: Mock and real modes share same route handlers + service layer
- NO MSW: UI always calls real APIs. APIs handle mock/real via service layer internally
- REPORTS → unified-trading-api proxies /reporting/* to client-reporting-api (port 8014). UI only knows port 8030.
- AUTH → UI calls auth-api (port 8200) via Next.js rewrite /api/auth/* → localhost:8200
- VISIBLE UX: Every function has a visible button. Reset Demo, Live/Batch toggle, persona switcher all visible in shell

SEPARATION OF CONCERNS (CRITICAL):
- UI is VISUAL ONLY. No service logic, no PnL calculation, no data generation, no mock fixtures.
- ALL data comes from the API. The API reads from MockStateStore (mock) or real services (live).
- If you can't demonstrate it with `curl`, the logic is in the WRONG LAYER.
- No two sources of truth: if the API seeds strategies, the UI does NOT also hardcode strategies.
- Missing service functionality? Add it to the service/API — don't work around it in the UI.
- Instruments: imported from UAC representative_sample.py (50+ specs). Seed generators read the registry.
- Strategies: CONFIG, not code. 50+ strategies via archetype x asset_group config expansion.

LIVE/BATCH COEXISTENCE (applies to ALL domain data):
- Live mode: `?mode=live` → reads `{domain}_live` collections. WebSocket updates tickers/positions/PnL in real-time.
- Batch mode: `?mode=batch&as_of=DATE` → reads `{domain}_batch` collections. Immutable T+1 reconciled snapshots. NOT affected by WebSocket ticks.
- Same API endpoint serves both — different collection based on query param.
- Real-time PnL recalculation (server-side) ONLY mutates _live collections. Batch data is never touched by ticks.
- The toggle lives in `useGlobalScope().scope.mode`. ALL API hooks pass mode as query param.
- This applies to: positions, orders, fills, PnL, tickers, timeseries — everything with live/batch variants.
- Risk exposure and reconciliation can show BOTH simultaneously (live vs batch drift = the reconciliation view).

REAL-TIME FEEL (CRITICAL for demo):
- WebSocket mock tick generator: prices move every 500-2000ms on the Trading Terminal
- OHLCV candle data: 200 candles per instrument per interval for candlestick charts
- Order book depth: 20 bid + 20 ask levels for order book display
- PnL time-series: 180 daily data points per strategy for equity curve charts
- Live data persists to .local-dev-cache/ (survive restarts). Batch data is immutable snapshots.
- Batch/live switch reads from different MockStateStore collections (_live vs _batch)

AUTH FLOW:
- Persona switching redirects to login page (requires re-sign-in), does NOT instant-swap tokens
- auth-api must be running in dev stack (added to dev-start.sh and ui-api-mapping.json)
- All 3 APIs must use identical org_id, persona name, and entitlement key values

VISUAL POLISH (mandatory across all agents):
- Skeleton loading states (shimmer placeholders), NOT "Loading..." text
- Use existing components/ui/skeleton.tsx — create table/card/chart skeleton variants
- Cmd+K command palette wired to global shortcut (component exists, needs shell wiring)
- Notification bell shows real alert count and dropdown (not hardcoded "3")

CURRENT STATE (verified 2026-03-22 — do NOT redo work that's already done):
- API service layer EXISTS: services/ has DomainService Protocol, MockDomainService, LiveDomainService, factory.py. All 19 routes already use get_service(request) DI — NO if/else mock checks.
- WebSocket EXISTS: routes/websocket.py is 4,859 lines with channel-based multiplexing and synthetic tick generator.
- personas.py EXISTS: 121 lines, 4 orgs, 5 personas. Matches auth-api mock_data.py.
- auth-api EXISTS: port 8200, JWT (HS256), mock login, 5 users. But NOT in ui-api-mapping.json or dev-start.sh yet.
- Execution service pages ALL EXIST: 7 tabs, 298-405 lines each, with layout.tsx.
- 49 of 60 service pages are REAL (100-2000+ lines). Only 11 are stubs (24 lines).
- STILL NEEDED: MockStateStore migration (in-memory → UTL JSONL), seed enrichment (PnL timeseries, OHLCV, tickers, batch/live, org-scoped), MSW removal, debug footer, skeleton variants, auth-api in dev stack, E2E tests, API tests.

ERROR STATES (mandatory across all agents):
- Create and use: error-boundary.tsx (React error boundary), api-error.tsx (failed API display + retry), empty-state.tsx (contextual empty states for tables/lists)
- Every useQuery hook: handle isLoading (skeleton), isError (ApiError + retry), data.length===0 (EmptyState)
- Access denied: show "Upgrade" card for missing entitlements, redirect non-admin from /admin to /dashboard
- WebSocket disconnect: "Reconnecting..." banner with exponential backoff (1s, 2s, 4s, max 30s)

RESPONSIVE LAYOUT (mandatory across all agents):
- Desktop (1440px+): full layout. Laptop (1280px): scroll instead of side-by-side. Tablet (768px): hamburger nav, stacked panels, horizontal-scroll tables
- Use Tailwind responsive prefixes (md:, lg:) — no custom media queries
- Dashboard: 4-col → 2-col → 1-col grid. Tables: always overflow-x-auto wrapper

LATENCY SIMULATION (Agent 5 implements, all agents benefit):
- MOCK_LATENCY_MS env var (default 0 in CI, 150 in interactive). Makes skeletons visible and demo feel real.
- Without this, skeletons flash for 0ms and the demo feels fake.

INSTITUTIONAL UX GAP-CLOSING (mandatory across all agents — Phase 6+ todos):

FULL INSTRUMENT COVERAGE:
- UAC has 128 venues, ~40 representative instruments in representative_sample.py
- Seed data, API endpoints, and UI instrument selectors must cover ALL instruments — not a hardcoded 10
- generate_ui_reference_data.py syncs UAC registries to ui-reference-data.json (2,297 lines)
- UI reads instruments from ui-reference-data.json, NOT from hardcoded arrays

50+ STRATEGIES (config-driven expansion):
- 10 archetypes × 5 asset classes. Currently 18 seeded, expanding to 50+
- Same engine handles all strategies — expansion is data/config, not new code paths
- strategy-registry.ts (1,863 lines) and strategy-manifest.json must both be updated

TANSTACK TABLE (Agent 1 creates base component, all agents adopt):
- Install: @tanstack/react-table + @tanstack/react-virtual
- Agent 1 creates DataTable in components/ui/data-table.tsx: sorting, column visibility, resizing, virtualization
- ALL data tables across ALL services MUST use DataTable (not shadcn <Table>)

TECHNICAL INDICATORS (Agent 2 implements):
- lightweight-charts v5.1.0 already installed. Use addLineSeries() for SMA, EMA, Bollinger Bands
- Indicator toolbar toggles above chart. State persisted in ui-prefs-store

EXCEL EXPORT (Agent 2 creates utility, all agents use):
- Install: xlsx (SheetJS). Create lib/utils/export.ts with exportTableToXlsx()
- Every "Export" button becomes split: CSV + Excel options

DARK MODE: ALREADY EXISTS — Citadel-inspired cyan theme in globals.css. No work needed.

SONNER TOASTS: Already installed at components/ui/sonner.tsx. Wire for ALL mutations.

WORKSPACE PERSISTENCE: Zustand ui-prefs-store.ts exists. Add persist middleware for filters, columns, panel sizes.

GUIDED TOUR: react-joyride for first-time users. Agent 1 creates after navigation is stable.

PRINT CSS: Agent 4 adds @media print styles for Reports pages.

SSOT SYNC PIPELINE (Agent 8 runs after Agents 5-6):
- generate_ui_reference_data.py — sync UAC → UI reference data
- generate_unified_spec.py → openapi.json → npm run generate:types → TypeScript types
- validate-strategy-manifest.py — verify 50+ strategies
- check-strategy-instruments.py — verify instrument references
- check_ui_api_flow_coverage.py — verify UI→API coverage
- These scripts are in unified-trading-pm/scripts/. They are CENTRAL to the expansion.

CODE SPLITTING (Agent 1 implements, all agents follow):
- Use Next.js dynamic() imports for heavy components (charts, data grids, deployment forms)
- Charts MUST use dynamic(() => import(...), { ssr: false })

MANDATORY COMPLETION PROTOCOL (after EVERY todo):
When you finish a todo or group of todos, you MUST do ALL of the following:

1. TICK THE PLAN — Mark the todo as done (change `- [ ]` to `- [x]`) in your plan file.

2. RUN TESTS — Run `bash scripts/quality-gates.sh` in every repo you modified. If a test breaks:
   - If the test logic is WRONG (tests an old pattern your refactor correctly replaced): fix the test.
   - If the test logic is RIGHT (catches a real bug in your refactor): fix your refactor, not the test.
   - The refactor plan is canonical, but tests provide quality guidance you MUST respect.

3. HARDEN THE RULES — For every structural change you make, add a rule or constraint that prevents
   future agents from undoing it. Specifically:
   a. If you DELETE a route/page/component: add it to `redirects_only` in next.config.mjs so it
      can't be recreated at the old path. Add a comment explaining why it was removed.
   b. If you CREATE a new pattern (e.g., service layout with tabs): add a comment at the top of
      the file explaining the architectural constraint ("This layout renders EXECUTE_TABS. Do NOT
      add card-based sub-pages within this service — use tabs only.").
   c. If you WIRE an orphaned component: remove it from the `orphaned_components_to_wire` list in
      UI_STRUCTURE_MANIFEST.json and update the page's state from "STUB" to "REAL".
   d. If you ADD an API endpoint: update the OpenAPI spec and run the codegen pipeline:
      `cd unified-trading-system-ui && npm run generate:types`

4. UPDATE THE MANIFEST — After each phase, update `UI_STRUCTURE_MANIFEST.json`:
   - Change page states (STUB → REAL, REDIRECT → deleted)
   - Add new API hooks to the hooks list
   - Update line counts if substantially changed
   - Remove items from `routes_to_delete` once deleted
   - Remove items from `orphaned_components_to_wire` once wired
   - Remove items from `dead_tab_sets` once fixed

5. UPDATE DOCS — If your change affects architecture described in any of these docs, update them:
   - `CODEBASE_STRUCTURE.md` — if you add/remove components or change folder structure
   - `ROUTES.md` — if you add/remove/rename routes
   - `SERVICE_COMPLETION_STATUS.md` — if you change a service's completion level
   - `.cursorrules` or repo-level CLAUDE.md — if you establish a pattern that must be followed

6. COMMIT WITH CONTEXT — Every commit message must explain WHY, not just what. Include:
   - Which plan todo ID it completes (e.g., "completes a1-p0-remove-key-landing")
   - What architectural constraint it enforces (e.g., "direct-to-tabs: no card landing pages")

If you skip any of these steps, your work can be undone by the next agent who doesn't understand
why you made the change. The rule base IS the institutional memory.

SSOT CODEGEN PIPELINES (run when you change schemas/registries):
- After UAC registry changes: `cd unified-api-contracts && .venv/bin/python scripts/generate_ui_reference_data.py --output ../unified-trading-system-ui/lib/registry/ui-reference-data.json`
- After API route changes: fetch OpenAPI spec from running API, then `cd unified-trading-system-ui && npm run generate:types`
- See CITADEL_VISION_2026_03_22.md "SSOT Codegen Pipeline" section for full details.

7 OTHER AGENTS are working in parallel on other workstreams. Do not touch files outside your scope unless absolutely necessary. If you need something from another agent's scope, document it as a dependency.
```

---

## PROMPT 1: Shell & Navigation Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 1 — Shell & Navigation
YOUR PLAN: unified-trading-pm/plans/active/agent1_shell_navigation_2026_03_22.md

YOUR SCOPE:
- unified-trading-system-ui only
- Shell components: components/shell/*, components/platform/*
- Routing: app/(platform)/services/[key]/, app/(platform)/portal/*, app/(platform)/services/overview/
- Navigation: lib/lifecycle-mapping.ts, lib/reset-demo.ts
- Stores: lib/stores/global-scope-store.ts

YOUR MISSION:
1. DELETE the card-based service landing page (app/(platform)/services/[key]/page.tsx)
2. DELETE all /portal/* redirect pages (8 files)
3. DELETE /services/overview hub page
4. WIRE orphaned components: batch-live-rail.tsx, filter-bar.tsx, candidate-basket.tsx, live-asof-toggle.tsx
5. CREATE debug-footer.tsx with Reset Demo button, persona display, mock mode indicator
6. FIX lifecycle-nav links to go direct-to-tab (no intermediate landings)
7. FIX breadcrumbs to show Home > Service > Tab
8. VERIFY every service has a layout.tsx with correct ServiceTabs
9. WIRE Cmd+K command palette (component exists in components/ui/command.tsx — add global shortcut in shell)
10. WIRE notification bell to show real alert count + dropdown (currently hardcoded "3" in lifecycle-nav.tsx)
11. CREATE skeleton loading components (table-skeleton, card-grid-skeleton, chart-skeleton) from existing Skeleton component
12. FIX persona switcher: redirect to /login?persona=X (requires re-sign-in, NOT instant-swap)
13. FIX build: NEXT_PUBLIC_MOCK_API=true npx next build must pass
14. ADD Playwright tests for navigation flows

DO NOT TOUCH: page content within service tabs (that's Agent 2-4, 7's job)
DO NOT TOUCH: API code (that's Agent 5-6's job)

Read your plan file for detailed todos with acceptance criteria.
Execute todos in order (Phase 0 → Phase 1 → Phase 2 → Phase 3 → Phase 4).
Mark each todo as done in the plan file when complete (change - [ ] to - [x]).
```

---

## PROMPT 2: Trading Service Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 2 — Trading Service (Run)
YOUR PLAN: unified-trading-pm/plans/active/agent2_trading_service_2026_03_22.md

YOUR SCOPE:
- unified-trading-system-ui: app/(platform)/dashboard/, app/(platform)/services/trading/*, app/(platform)/services/execution/*
- unified-trading-system-ui: components/trading/*
- unified-trading-system-ui: hooks/api/use-positions.ts, use-orders.ts, use-market-data.ts, use-alerts.ts, use-trading.ts
- live-health-monitor-ui (read-only — restore ManualTradingPanel from git history)

YOUR MISSION:
1. Wire Dashboard ↔ Terminal navigation (prominent buttons both ways)
2. RESTORE ManualTradingPanel from git (commit 5c24fa2 in live-health-monitor-ui) as drawer in Terminal
3. VERIFY all 6 Trading tabs have real content (Terminal, Positions, Orders, Execution, Accounts, Markets)
4. WIRE batch/live mode switching on Terminal (banner, different data based on global scope mode)
5. WIRE WebSocket feed: terminal subscribes to ws://localhost:8030/ws, receives live price ticks, updates chart + order book
6. WIRE candlestick chart to GET /market-data/candles (historical) + WebSocket ticks (real-time append)
7. WIRE order book to GET /market-data/orderbook (depth levels)
8. VERIFY strategy detail and list pages work
9. ADD Playwright tests for trading flows

DO NOT TOUCH: Shell/navigation components (Agent 1's scope)
DO NOT TOUCH: API route handlers (Agent 5's scope)
DO NOT TOUCH: Seed data (Agent 6's scope)

Key files to read first:
- app/(platform)/dashboard/page.tsx (460 lines — the Command Center)
- app/(platform)/services/trading/overview/page.tsx (818 lines — the Terminal)
- components/trading/ (31 components)
- hooks/api/ (14 API hook files)

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 3: Research & Build Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 3 — Research & Build + Promote Services
YOUR PLAN: unified-trading-pm/plans/active/agent3_research_build_2026_03_22.md

YOUR SCOPE:
- unified-trading-system-ui: app/(platform)/services/research/*, app/(platform)/services/execution/*
- strategy-ui (read-only — extract wizard patterns)
- ml-training-ui (read-only — extract experiment tracking patterns)
- _reference/versa-execution-analytics-ui/ (read-only — reference patterns)

YOUR MISSION:
1. VERIFY all Research Hub, ML sub-tabs, Strategy sub-tabs have real content (not placeholders)
2. Wire all pages to API hooks (GET /ml/*, GET /execution/backtests, etc.)
3. ABSORB strategy-ui wizard as modal/drawer within Strategies tab
4. ABSORB ml-training-ui experiment tracking into ML Models tab
5. VERIFY Promote service (candidates, handoff) works with approve/reject actions
6. ADD Playwright tests for research flows

DO NOT TOUCH: Shell/navigation (Agent 1), Trading pages (Agent 2), API code (Agent 5-6)

Key repos to reference:
- strategy-ui/src/components/wizard/ — multi-step wizard with CSV upload
- ml-training-ui/src/ — experiment tracking UI
- _reference/versa-execution-analytics-ui/ — execution analytics patterns

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 4: Reports & Manage Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 4 — Reports & Manage Services
YOUR PLAN: unified-trading-pm/plans/active/agent4_reports_manage_2026_03_22.md

YOUR SCOPE:
- unified-trading-system-ui: app/(platform)/services/reports/*, app/(platform)/services/manage/*
- settlement-ui (read-only — extract settlement/invoice patterns)
- client-reporting-ui (read-only — extract reporting patterns)
- onboarding-ui (read-only — extract onboarding flow patterns)
- user-management-ui (read-only — extract user management patterns)
- _reference/versa-client-reporting/, versa-invoicing/, versa-onboarding/ (read-only)

YOUR MISSION:
1. VERIFY all 5 Reports tabs have real content (P&L, Executive, Settlement, Reconciliation, Regulatory)
2. VERIFY all 5 Manage tabs have real content (Clients, Mandates, Fees, Users, Compliance)
3. ABSORB settlement-ui pages into Reports > Settlement
4. ABSORB client-reporting-ui patterns into Reports > P&L
5. ABSORB onboarding-ui flows as modals in Manage > Clients
6. ABSORB user-management-ui into Manage > Users
7. ADD document upload/download section in Reports
8. ADD Playwright tests

DO NOT TOUCH: Shell (Agent 1), Trading (Agent 2), Research (Agent 3), API code (Agent 5-6)

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 5: API Service Layer Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 5 — Backend API Service Layer
YOUR PLAN: unified-trading-pm/plans/active/agent5_api_service_layer_2026_03_22.md

YOUR SCOPE:
- unified-trading-api (primary — full write access)
- unified-trading-library (read MockStateStore, may need minor imports)

YOUR MISSION:
1. CREATE services/ directory with Protocol interfaces for all 15 domains
2. CREATE services/mock/ with MockStateStore-backed implementations
3. CREATE services/live/ with stub implementations (NotImplementedError)
4. CREATE services/factory.py with Depends() factories
5. REFACTOR all 15 route files to use service layer (eliminate if/else mock checks)
6. REPLACE local state_store.py with UTL MockStateStore (JSONL persistence to .local-dev-cache/)
7. ADD POST /admin/reset endpoint
8. ADD POST /execution/orders endpoint (for manual trading)
9. ADD new API endpoints: GET /ml/experiments, GET /market-data/candles, GET /market-data/orderbook
10. IMPLEMENT WebSocket mock tick generator (P0 — critical for real-time demo feel)
11. WIRE reporting proxy: /reporting/* forwards to client-reporting-api (port 8014) in real mode
12. WIRE auth: validate JWTs from auth-api, extract persona/org_id for data scoping
13. UPDATE dev stack: add auth-api to ui-api-mapping.json and dev-start.sh
14. CONFIGURE live data persistence: _live collections persist to .local-dev-cache/, _batch immutable
15. ADD integration tests for every route (mock mode)
16. ENSURE quality-gates.sh passes

DO NOT TOUCH: UI code (Agents 1-4, 7), seed data content (Agent 6)

Current state of unified-trading-api:
- 17 domain routers, ~1,538 lines
- Every route: `if mock_mode: return mock_store.list(domain)` else `return NOT_IMPLEMENTED`
- Simple state_store.py (68 lines, in-memory only, no persistence)
- 1 test file (test_health.py)
- seed.py: 1,309 lines (partial coverage)
- No services/ directory, no admin reset, no WebSocket ticks, no auth-api integration

The service layer pattern and real-time data architecture are explained in CITADEL_VISION_2026_03_22.md.
Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 6: Mock Data Quality Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 6 — Mock Data Quality & Migration
YOUR PLAN: unified-trading-pm/plans/active/agent6_mock_data_quality_2026_03_22.md

YOUR SCOPE:
- unified-trading-api: mock_data/seed.py, mock_data/personas.py (create)
- unified-trading-system-ui: lib/mocks/ (delete), lib/trading-data.ts (reference for alignment)
- auth-api: mock_data.py (reference for persona alignment)

YOUR MISSION:
1. CREATE personas.py as SSOT for org/persona definitions (matching auth-api and UI)
2. ENHANCE seed.py with comprehensive, realistic data across ALL domains
3. ADD org_id to every seed record for persona-based scoping
4. ALIGN seed strategies with UI's trading-data.ts (same IDs, names, asset classes)
5. SEED PnL time-series: 180 daily data points per strategy (3,240 total) for equity curve charts
6. SEED OHLCV candle data: 10 instruments * 4 intervals * 200 candles = 8,000 records
7. SEED initial ticker prices for 10 instruments (starting point for WebSocket ticks)
8. SEED batch AND live data variants: _live collections (mutable, persisted) and _batch collections (immutable snapshots)
9. ADD seed versioning and CI/deterministic mode
10. REMOVE MSW from the UI (lib/mocks/ directory, ~1,411 lines)
11. MIGRATE Dashboard from client-side trading-data.ts to API hooks
12. ADD seed data quality tests

CRITICAL CONSTRAINT: The seed data MUST produce visually identical results to the current
client-side trading-data.ts when rendered on the Dashboard. Same strategy names, similar PnL
ranges, same 4 organizations. The user should not notice a difference after migration.

DEPENDENCY: Agent 5 must create the service layer first. Your seed data feeds into their
MockStateStore. Coordinate: your seed.py structure must match Agent 5's service method expectations.

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 7: Observe & Admin Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 7 — Observe & Admin/Ops Services
YOUR PLAN: unified-trading-pm/plans/active/agent7_observe_admin_2026_03_22.md

YOUR SCOPE:
- unified-trading-system-ui: app/(platform)/services/observe/*, app/(ops)/*
- deployment-ui (read-only — extract 8-tab patterns)
- batch-audit-ui (read-only — extract audit patterns)
- live-health-monitor-ui (read-only — extract monitoring patterns)
- logs-dashboard-ui (read-only — extract log viewer patterns)
- _reference/versa-audit-ui/, versa-admin-ui/, deployment-ui/ (read-only)

YOUR MISSION:
1. VERIFY all 5 Observe tabs have real content (Risk, Alerts, News, Strategy Health, System Health)
2. ABSORB live-health-monitor-ui monitoring into System Health
3. ABSORB logs-dashboard-ui log viewer into System Health
4. VERIFY Admin dashboard has real content
5. ABSORB deployment-ui's 8-tab richness into Admin > DevOps
6. ABSORB batch-audit-ui audit trail into Admin > Audit/Compliance
7. VERIFY ops pages have content (Jobs, Services)
8. ADD Playwright tests

DO NOT TOUCH: Shell (Agent 1), Trading (Agent 2), Research (Agent 3), Reports/Manage (Agent 4), API (Agent 5-6)

deployment-ui has the RICHEST satellite UI (9/10 score, 8 tabs). Its patterns are the gold
standard for what the DevOps page should look like.

Read your plan file for detailed todos. Execute in phase order.
```

---

## PROMPT 8: E2E Tests & Quality Agent

```
{SHARED PREAMBLE}

YOUR WORKSTREAM: Agent 8 — E2E Tests & Quality Gates
YOUR PLAN: unified-trading-pm/plans/active/agent8_e2e_tests_quality_2026_03_22.md

YOUR SCOPE:
- unified-trading-api: scripts/quality-gates.sh, tests/
- unified-trading-system-ui: playwright.config.ts, e2e/, scripts/

YOUR MISSION:
1. FIX unified-trading-api quality-gates.sh (ruff, basedpyright, pytest with coverage ≥ 80%)
2. FIX unified-trading-system-ui build (TypeScript strict, no MSW references)
3. SET UP Playwright E2E infrastructure (start auth-api + unified-trading-api + UI, POST /admin/reset before each suite)
4. WRITE Playwright tests for EVERY service: Auth flow, Trading flow, Research flow, Data flow, Reports flow, Manage flow, Observe flow, Admin flow, Reset Demo flow
5. WRITE real-time feel tests: WebSocket ticks update terminal, batch/live switch changes data
6. RUN SSOT codegen pipelines after Agents 5-6 finish: OpenAPI → TypeScript types, UAC → reference data
7. ADD auth alignment test: verify persona org IDs match across auth-api and unified-trading-api
8. VERIFY API integration tests cover all routes
9. ADD OpenAPI schema parity test
10. CREATE smoke test script (bash scripts/e2e-smoke.sh)

DEPENDENCY: This agent depends on Agents 5-6 (API + data) being substantially complete.
Start with Phases 0-1 (quality gates, build fixes) which can run immediately.
Phases 2-5 (Playwright, integration tests) should run after API service layer is in place.

DO NOT TOUCH: Page content, API route logic, seed data — only tests and quality infrastructure.

Read your plan file for detailed todos. Execute in phase order.
```

---

## Execution Order & Dependencies

```
PARALLEL GROUP 1 (start immediately — ALL agents can start now):
  Agent 1: Shell & Navigation (UI only)
  Agent 2: Trading Service (execution pages already exist, API hooks ready)
  Agent 3: Research & Build (UI only, pages exist, need API wiring)
  Agent 4: Reports & Manage (UI only, satellite absorption)
  Agent 5: API Enhancement (service layer exists — focus on MockStateStore, seeds, latency, auth-api)
  Agent 6: Mock Data Quality (personas.py exists — focus on seed enrichment, consistency, MSW removal)
  Agent 7: Observe & Admin (UI only, satellite absorption)

PARALLEL GROUP 2 (after Agents 1-7 substantially complete):
  Agent 8: E2E Tests & Quality (needs all services to have content + codegen pipelines)
```
