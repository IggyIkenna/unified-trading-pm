# Citadel-Grade System Vision — 2026-03-22

## Shared Context for All Agents

This document is the SSOT for the system-wide refactor. Every agent executing any of the 8 workstreams MUST read and
follow this vision. No agent should make decisions that conflict with this document.

---

## Core Principles

1. **ONE UI** — `unified-trading-system-ui` is the only consumer-facing frontend. All 13 satellite UIs (batch-audit-ui,
   client-reporting-ui, deployment-ui, execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui,
   ml-training-ui, onboarding-ui, settlement-ui, strategy-ui, trading-analytics-ui, user-management-ui) are archived.
   Their functionality is absorbed into the main UI.

2. **THREE APIs** — The system has 3 API gateways:
   - `auth-api` — SSO/token issuance, user/org management, entitlements (no core trading logic)
   - `client-reporting-api` — Client-facing reporting, invoicing, regulatory, document management (needs only API keys
     and reporting logic, no core system services)
   - `unified-trading-api` — Trading system gateway (all internal + external trading functionality) The 8 remaining
     domain data APIs (batch-audit-api, config-api, deployment-api, execution-results-api, market-data-api,
     ml-inference-api, ml-training-api, trading-analytics-api) are absorbed into unified-trading-api.

3. **90% CODE SHARING** — Mock and real modes share the same route handlers, the same service layer, the same
   filtering/pagination logic. Only the data source differs (MockStateStore vs backend service calls). No MSW in the UI
   — the UI always calls the real API. The API handles mock/real internally.

4. **DIRECT-TO-TABS** — No intermediate landing pages with feature cards. Clicking a lifecycle nav item goes directly to
   the first tab of that service. Tabs ARE the navigation within a service.

5. **VISIBLE UX** — Every function must have a visible button/control. No hidden functionality. Reset Demo, Live/Batch
   toggle, Persona switcher, Org selector — all visible in the shell at all times.

6. **9 SERVICES** — The platform has exactly 9 service areas, each with tabbed navigation: Data, Research, Promote,
   Trading, Execution, Observe, Manage, Reports, Admin/Ops. Execution is separate from Trading because it's a distinct
   commercial offering — clients can subscribe to execution (algos, venue connectivity, TCA) independently.

---

## Service Architecture

### Global Shell (Every Authenticated Page)

```
Row 1 LEFT:   [Logo] Acquire | Build | Promote | Run | Execute | Observe | Manage | Report
Row 1 CENTER: [All Orgs ▾] [All Clients ▾] [All Strategies ▾] [$41M] [28.9M exposed]
Row 1 RIGHT:  [Search ⌘K] [🔔] [Odum Internal ▾] [User ▾]
Row 2:        Tab1 | Tab2 | Tab3 | Tab4 | Tab5          [Live ◉ / As-Of 📅]
Breadcrumbs:  Trading > Terminal
Debug Footer: [Reset Demo] [Mock Mode ◉] [Persona: Admin ▾]  (mock mode only)
```

### Global Scope Filters (Row 1 Center — EVERY service page)

- **Org dropdown** — filter all data by organization. Admin sees all orgs; clients see only theirs.
- **Client dropdown** — filter by client within the selected org. Cascading from org selection.
- **Strategy dropdown** — filter by strategy. Most services support this. Admin/Ops may not.
- These filters are in `components/platform/global-scope-filters.tsx` (already exists, wired in lifecycle-nav.tsx center
  section)
- The orphaned `OrgClientSelector` component should be verified as wired into GlobalScopeFilters
- Every service tab reads from `useGlobalScope()` store and filters its data accordingly
- Service-specific filters (venue, instrument, date range, severity) appear in Row 2 or within the tab content using the
  `FilterBar` component — same UX look and feel across all services

### Service 1: DATA (Acquire)

- Entry: `/services/data/overview`
- Tabs: Pipeline Status | Coverage Matrix | Missing Data | Venue Health | Markets | ETL Logs
- All pages EXIST and are kept as-is

### Service 2: RESEARCH & BACKTESTING (Build)

- Entry: `/services/research/overview`
- Tabs: Research Hub | Features | ML Models | Strategies | Compare | Signals | Execution Research
- ML Models tab has sub-tabs: Overview | Experiments | Training | Validation | Registry | Monitoring | Deploy |
  Governance
- ABSORBS: strategy-ui wizard, ml-training-ui experiment tracking

### Service 3: PROMOTE (Promote)

- Entry: `/services/research/strategy/candidates`
- Tabs: Review Queue | Execution Analysis | Risk Review | Approval Status
- RESTORE: CandidateBasket component (orphaned, exists on disk)

### Service 4: TRADING (Run)

- Entry: `/services/trading/overview` (the terminal — NOT a card landing)
- Tabs: Terminal | Positions | Orders | Accounts | Markets | Strategies
- ALSO: /dashboard (Command Center) as separate entry under Run
- RESTORE: BatchLiveRail (orphaned), ManualTradingPanel (deleted in 5c24fa2)
- NOTE: Execution Analytics moved to its own service (Service 5)

### Service 5: EXECUTION (Execute)

- Entry: `/services/execution/overview`
- Tabs: Analytics | Algos | Venues | TCA | Benchmarks | Candidates | Handoff
- Lifecycle stage: "Execute" (between Run and Observe)
- Distinct commercial offering: clients subscribe to execution algos, venue connectivity, and TCA independently. Basic
  clients can observe trades on the terminal; execution subscribers get access to advanced algos, custom execution
  strategies, and venue analytics.
- ABSORBS: execution-analytics-ui, trading-analytics-ui
- Entitlement: `execution-basic` (venue status, fill quality) or `execution-full` (algos, TCA, custom strategies)

### Service 6: OBSERVE (Observe)

- Entry: `/services/observe/risk` (or `/services/trading/risk` — shared route)
- Tabs: Risk Dashboard | Alerts | News | Strategy Health | System Health
- ABSORBS: live-health-monitor-ui, logs-dashboard-ui

### Service 7: MANAGE (Manage)

- Entry: `/services/manage/clients`
- Tabs: Clients | Mandates | Fees | Users | Compliance
- ABSORBS: onboarding-ui, user-management-ui

### Service 8: REPORTS (Report)

- Entry: `/services/reports/overview`
- Tabs: P&L Attribution | Executive | Settlement | Reconciliation | Regulatory
- ABSORBS: client-reporting-ui, settlement-ui

### Service 9: ADMIN/OPS (Internal Only)

- Entry: `/admin`
- Tabs: Admin Dashboard | Config | DevOps | Jobs | Services | Data ETL
- ABSORBS: deployment-ui (8-tab richness), batch-audit-ui
- HIDDEN from client personas

---

## Routes to REMOVE

- `/services/[key]` dynamic card landing page
- `/services/overview` hub page (replace with `/dashboard` as post-login landing)
- `/portal/*` (all 8 pages — dead redirects)
- SERVICE_SECTIONS and SERVICE_REGISTRY card definitions

## Components to RESTORE (from orphaned code or git history)

- `BatchLiveRail` — components/platform/batch-live-rail.tsx (zero imports, wire it)
- `FilterBar` — components/platform/filter-bar.tsx (zero imports, wire it)
- `CandidateBasket` — components/platform/candidate-basket.tsx (wire it)
- `LiveAsOfToggle` — components/platform/live-asof-toggle.tsx (verify wired in service layouts)
- `ManualTradingPanel` — restore from git commit 5c24fa2 (live-health-monitor-ui)
- `resetDemo()` — lib/reset-demo.ts (exists, wire to visible Debug Footer button)

## Satellite UIs to ARCHIVE

batch-audit-ui, client-reporting-ui, deployment-ui, execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui,
ml-training-ui, onboarding-ui, settlement-ui, strategy-ui, trading-analytics-ui, user-management-ui

## Reference Material

- `_reference/` folder in unified-trading-system-ui has versa-\* repos with patterns to absorb
- REFERENCE_MAPPING.md documents which reference maps to which service area

---

## API Architecture

### 3 API Gateways

#### auth-api (Port 8200)

- OAuth providers (Google, Microsoft, Slack), JWT issuance, session management
- User/org/entitlement CRUD, API key management
- No core trading logic — purely auth/admin
- UI routes: `/login`, `/signup`, persona switching

#### client-reporting-api (Port 8014)

- Client-facing: P&L reports, invoices, compliance, documents, DocuSign
- Routes: /reports, /pnl, /alerts, /invoices, /compliance, /documents, /docusign, /sports, /streaming
- Auth: API key + JWT Bearer (client-scoped, no system access)
- UI routes: `/services/reports/*` (P&L, Executive, Settlement, Regulatory)
- Separate because: client-facing, needs only API keys + reporting logic, no core services

#### unified-trading-api (Port 8030)

- Trading system gateway: all internal + external trading functionality
- 14 domain routers: market-data, execution, positions, analytics, ml, audit, config, alerts, risk, instruments,
  deployment, service-status, users, websocket
- UI routes: everything except /services/reports/\* and auth flows

### Service Layer Pattern (MANDATORY)

```python
# Route (shared, identical for mock and real):
@router.get("/orders")
async def get_orders(service: OrderService = Depends(get_order_service)):
    return await service.list_orders(filters)

# Service interface:
class OrderService(Protocol):
    async def list_orders(self, filters) -> PaginatedResponse: ...

# Mock implementation:
class MockOrderService:
    def __init__(self, store: MockStateStore): ...
    async def list_orders(self, filters):
        records = self.store.list("orders")
        # SAME filtering, pagination, sorting logic as real
        return paginate(apply_filters(records, filters))

# Real implementation:
class LiveOrderService:
    async def list_orders(self, filters):
        response = await self.execution_service_client.get_orders(filters)
        return paginate(response)

# Factory (injected via Depends):
def get_order_service(request: Request) -> OrderService:
    if request.app.state.mock_mode:
        return MockOrderService(mock_store)
    return LiveOrderService()
```

### Mock State

- Uses UTL MockStateStore (JSONL persistence in .local-dev-cache/)
- `POST /admin/reset` endpoint to reset all mock state to seed values
- Org-scoped filtering: mock data filtered by org from JWT token
- Deterministic seeding for CI (MOCK_STATE_MODE=deterministic)

---

## Auth & Personas

### Personas (same in auth-api and UI)

- Admin: Full system access, all services visible
- Internal Trader: Platform + wildcard, admin/manage hidden
- Client Full (Alpha Capital): All services except manage/admin
- Client Premium (Vertex Partners): Data + Execution + Strategy
- Client Data Only (Beta Fund): Data service only, rest shows "Upgrade" badges

### Post-Login Flow

- Admin/Internal → /dashboard (Command Center)
- Client Full/Premium → /dashboard (filtered to their org)
- Client Data Only → /services/data/overview

---

## SSOT Codegen Pipeline (CRITICAL — run after any schema/registry change)

### Pipeline 1: UAC → UI Reference Data

```bash
# 1. Generate reference data from UAC registries (14 registries)
cd unified-api-contracts
.venv/bin/python scripts/generate_ui_reference_data.py --output ../unified-trading-system-ui/lib/registry/ui-reference-data.json

# 2. UI auto-imports via lib/registry/generated.ts (typed re-exports)
# No manual step needed — generated.ts reads the JSON at build time
```

**When to run:** After ANY change to UAC registries (venues, instruments, enums, config schemas, error codes) **SSOT
chain:** UAC registry Python → ui-reference-data.json → generated.ts → UI components

### Pipeline 2: API → UI TypeScript Types

```bash
# 1. Start unified-trading-api to get current OpenAPI spec
cd unified-trading-api && CLOUD_MOCK_MODE=true .venv/bin/python -m unified_trading_api.main &
sleep 3

# 2. Fetch OpenAPI spec
curl http://localhost:8030/openapi.json > ../unified-trading-system-ui/lib/registry/openapi.json

# 3. Generate TypeScript types from OpenAPI
cd ../unified-trading-system-ui
npm run generate:types
# Runs: openapi-typescript lib/registry/openapi.json -o lib/types/api-generated.ts

# 4. Kill API server
kill %1
```

**When to run:** After ANY change to unified-trading-api route signatures, request/response models **SSOT chain:**
FastAPI routes → OpenAPI spec → openapi-typescript → api-generated.ts → UI hooks

### Pipeline 3: Persona/Org Alignment

**SSOT:** unified-trading-api/mock_data/personas.py (to be created by Agent 6)

- auth-api mock_data.py must use same org IDs and entitlement keys
- UI hooks/use-auth.ts persona definitions must match
- Run seed data tests to verify alignment

### Current Drift Status (2026-03-22)

- ui-reference-data.json is OUT OF SYNC with UAC (generator output changed)
- OpenAPI spec in UI may not match current API routes
- These MUST be re-synced before agents start UI→API integration work

---

## Real-Time Data Architecture (CRITICAL for Demo Feel)

### Live Data Persistence

Both mock and production modes read live data from the **same directory structure**:
`.local-dev-cache/unified-trading-api/`. The MockStateStore (from UTL) persists all live-domain collections as JSONL
files here. In production, the same directory structure would be populated by real service writes. This means:

- `positions_live.jsonl` — real-time positions (updated by WebSocket or polling)
- `orders_live.jsonl` — real-time orders
- `pnl_live.jsonl` — real-time PnL snapshots
- `tickers_live.jsonl` — latest ticker prices

### Batch/Live Switch

The **only difference** between batch and live mode is which collection the API reads from:

- **Live mode** (`mode=live`): reads from `{domain}_live` collections — real-time, mutable, updated by WebSocket feed
- **Batch mode** (`mode=batch&as_of=2026-03-21`): reads from `{domain}_batch` collections — T+1 reconciled, immutable
  snapshots

The switch is clean because both live in the same `.local-dev-cache/` directory. The UI sends `mode` and `as_of` query
params; the API reads from the correct collection. No separate data stores, no environment variable changes.

### Batch Data Characteristics (vs Live)

- Batch PnL includes reconciliation adjustments (slightly different from live)
- Batch positions may lag by 1-2 fills (unreconciled fills not yet in batch)
- Batch prices are official close prices, live prices are last tick
- Batch has exact fee breakdowns, live has estimated fees

### WebSocket Mock Feed

The unified-trading-api WebSocket endpoint (`/ws`) MUST emit simulated price ticks in mock mode:

- **Brownian motion** price generator for subscribed instruments (BTC-USDT, ETH-USDT, SOL-USDT, etc.)
- **Tick interval**: 500ms-2000ms (randomized for realism)
- **Data**: `{ instrument, price, volume, bid, ask, timestamp }`
- Ticks update the `tickers_live` collection in MockStateStore (so REST endpoints reflect current prices)
- The UI Trading Terminal subscribes on mount, unsubscribes on unmount
- This is what makes the terminal feel **alive** — prices moving, charts updating, order book shifting

### OHLCV Candle Data

The API must serve historical candle data (`GET /market-data/candles?instrument=BTC-USDT&interval=1h&limit=200`):

- Seed 200 candles per instrument per interval (1m, 5m, 1h, 1d)
- Generated procedurally: Brownian motion with realistic volume profiles (higher volume at opens/closes)
- At least 10 instruments with candle data

### Order Book Depth

The API must serve order book snapshots (`GET /market-data/orderbook?instrument=BTC-USDT`):

- 20 bid levels + 20 ask levels per instrument
- Realistic spread (0.01-0.05% of price)
- Depth decreasing away from mid-price
- In mock mode, regenerated with slight randomization on each request (simulates market movement)

---

## Auth Architecture (3-API Integration)

### Auth Flow

- **Login**: UI redirects to `/login` → user picks persona (mock) or OAuth provider (real) → auth-api issues JWT → UI
  stores token → UI reads entitlements from token claims → UI renders appropriate service access
- **Persona switching**: Clicking a different persona in the debug footer **redirects to login page** with the new
  persona pre-selected. It does NOT instant-swap — the user must click "Sign In" to complete the switch. This ensures
  the JWT is properly re-issued and all API calls use the new token.
- **Logout**: UI clears token → redirects to `/login`

### auth-api Integration (Port 8200)

- **MUST be added to** `ui-api-mapping.json` and `dev-start.sh` service_workers
- UI's `next.config.mjs` already has rewrite: `/api/auth/:path*` → `http://localhost:8200/:path*`
- In mock mode with `DISABLE_AUTH=true`: auth-api still runs but skips token validation, issues demo JWTs
- **Remove MSW auth handlers** — the UI should call auth-api directly, even in mock mode. Auth-api has its own
  `mock_data.py` with demo personas that must align with unified-trading-api's `personas.py`

### client-reporting-api Integration (Port 8014)

Reports service routes MUST go to client-reporting-api, not unified-trading-api:

- **Option A (recommended)**: unified-trading-api acts as proxy — `/reporting/*` routes forward to
  `http://localhost:8014/api/*`. This keeps the UI simple (one API base URL).
- **Option B**: UI has separate base URL for reports. Add `NEXT_PUBLIC_REPORTING_URL=http://localhost:8014` env var and
  update `lib/api/fetch.ts` to route `/reporting/*` and `/reports/*` paths to this URL.

Choose Option A for simplicity. unified-trading-api's `routes/reporting.py` becomes a thin proxy in real mode and serves
from MockStateStore in mock mode (mirroring client-reporting-api's data).

### Dev Stack Changes Required

1. Add auth-api to `ui-api-mapping.json`: `{ "name": "auth-api", "api_port": 8200, "module": "auth_api" }`
2. Add auth-api to `dev-start.sh` service_workers section
3. Remove MSW auth handlers from UI (`lib/mocks/handlers/auth.ts`)
4. Verify auth-api `mock_data.py` persona IDs match unified-trading-api `personas.py`

---

## Visual Polish Standards (Agents MUST Follow)

### Loading States (MANDATORY)

Every page that fetches data from the API MUST show **skeleton placeholders** (not "Loading..." text) while data loads:

- Use the existing `<Skeleton>` component from `components/ui/skeleton.tsx`
- Pattern: `if (isLoading) return <PageSkeleton />` where `PageSkeleton` mimics the page layout with shimmer bars
- Tables: show 5 skeleton rows with column-width-appropriate shimmer bars
- Cards: show card outline with shimmer content
- Charts: show chart area outline with shimmer
- This is the difference between "prototype" and "production" feel

### Command Palette (Wire Existing Component)

The `<Command>` component from `components/ui/command.tsx` (cmdk library) MUST be wired to:

- Global `Cmd+K` / `Ctrl+K` keyboard shortcut
- Search across: services, strategies, instruments, recent pages
- Quick actions: Reset Demo, Switch Persona, Toggle Batch/Live
- Render in the shell layout so it's available on every page

### Notification Bell (Wire to Real Alerts)

The bell icon in `lifecycle-nav.tsx` MUST:

- Show actual alert count from `GET /alerts/active?acknowledged=false` (not hardcoded "3")
- Open a dropdown with the 5 most recent alerts (severity badge + message + timestamp)
- "View All" link navigates to `/services/observe/alerts`
- Acknowledge action calls `POST /alerts/{id}/acknowledge` inline

---

## Current State Baseline (Verified 2026-03-22)

Agents MUST read this before planning work. Several areas are further along than initial estimates:

### Already Done (Do NOT redo)

- **API service layer**: `services/` exists with `DomainService` Protocol (base.py), `MockDomainService`
  (mock_service.py), `LiveDomainService` (live_service.py), factory.py with `get_service(request)` DI. All 19 routes
  already use this pattern — NO if/else mock checks remain.
- **WebSocket**: `routes/websocket.py` is 4,859 lines with channel-based multiplexing (market-data, positions, alerts,
  health, execution), synthetic tick generator, per-client subscription tracking.
- **personas.py**: 121 lines in `unified_trading_api/mock_data/personas.py` — 4 orgs, 5 personas, entitlements. Matches
  auth-api's `mock_data.py`.
- **auth-api**: Fully implemented — port 8200, JWT issuance (HS256, 1h access / 7d refresh), 5 mock users, mock login
  flow. Has `mock_data.py` and `mock_state.py`.
- **Execution service pages**: All 7 tabs exist as real pages (298-405 lines each): overview, algos, venues, tca,
  benchmarks, candidates, handoff. Layout exists.
- **UI page richness**: 49 of 60 service pages are real (100-2000+ lines). Only 11 are stubs (24 lines each).

### Still Needed (Confirmed gaps)

- **MockStateStore migration**: state_store.py is still 68 lines, in-memory only. UTL MockStateStore (JSONL persistence,
  .local-dev-cache/) NOT yet adopted.
- **Seed data enrichment**: No PnL time-series, no OHLCV candles, no ticker seeds, no batch/live separation, no
  org-scoped data. seed.py is 1,323 lines covering basic domains only.
- **MSW removal**: `lib/mocks/` (18 handlers + fixtures) still exists. `lib/trading-data.ts` (1000+ lines) still used by
  Dashboard.
- **Debug footer**: Does not exist.
- **Skeleton loading variants**: Only base `skeleton.tsx` exists. No table/card/chart variants.
- **auth-api dev stack**: NOT in ui-api-mapping.json, NOT started by dev-start.sh.
- **E2E tests**: Only 2 Playwright specs (smoke.spec.ts, trader.spec.ts).
- **API tests**: Only 3 test files. Coverage far below 80%.
- **11 stub pages**: orders, accounts, settlement, reconciliation, regulatory, news, strategy-health, coverage, missing,
  venues (data), logs — all 24 lines.
- **Orphaned components**: filter-bar (0 imports), candidate-basket (0 imports). batch-live-rail partially wired (2
  imports). live-asof-toggle partially wired (4 imports).
- **Portal pages**: 9 dead redirect pages still exist.
- **Card landing [key]**: Still exists.

---

## Error States & Empty States (MANDATORY — All Agents)

Every page and component that loads data MUST handle these states. This is the difference between a prototype and a
production-grade demo.

### Error Boundaries

- Create `components/ui/error-boundary.tsx` — React error boundary that catches render errors, shows recovery UI (not
  white screen)
- Create `components/ui/api-error.tsx` — standard error display for failed API calls: icon, message, "Retry" button
- Pattern: `if (isError) return <ApiError error={error} onRetry={refetch} />`
- Toast notifications for non-blocking errors (failed acknowledge, failed order placement)

### Empty States

- Create `components/ui/empty-state.tsx` — standard empty state: icon, title, description, optional action button
- Pattern: `if (data.length === 0) return <EmptyState title="No positions" description="..." />`
- Every table, list, and grid MUST show an empty state — not a blank area
- Empty states should be contextual: "No alerts — all systems normal" (positive), "No orders yet — place your first
  trade" (actionable)

### Access Denied States

- Client persona navigating to a service they lack entitlements for: show "Upgrade" card with service description and
  "Contact Sales" button — NOT a 403 or blank page
- Non-admin accessing /admin: redirect to /dashboard

### WebSocket Disconnection

- Subtle banner "Reconnecting..." when WebSocket disconnects
- Auto-reconnect with exponential backoff (1s, 2s, 4s, max 30s)
- On reconnect, refetch latest data to catch up on missed ticks

---

## Responsive Layout (MANDATORY for Demo)

Primary target is desktop (1440px+), but demo MUST be presentable on:

- **Laptop** (1280px): All content visible, may scroll instead of side-by-side panels
- **Tablet** (768px-1024px): Lifecycle nav collapses to hamburger. Global scope filters stack vertically. Tables use
  horizontal scroll. Charts resize.
- **Below 768px**: Not required — show "Best viewed on desktop" message

### Key Responsive Rules

- Lifecycle nav: desktop = full horizontal bar; tablet = hamburger with slide-out drawer
- Global scope filters: desktop = inline in nav center; tablet = collapsible filter panel below nav
- Trading Terminal: desktop = chart + order book + order form side-by-side; tablet = stacked vertically
- Data tables: always use `overflow-x-auto` wrapper — never break table layout
- Dashboard cards: desktop = 4-column grid; tablet = 2-column; mobile = 1-column
- Use Tailwind responsive prefixes (`md:`, `lg:`) — no custom media queries

---

## Latency Simulation (MANDATORY for Demo Realism)

Mock APIs returning data in <1ms makes the demo feel fake. Loading skeletons flash invisibly.

### Implementation

- Add `MOCK_LATENCY_MS` environment variable (default: 0 in CI/deterministic, 150 in interactive mode)
- In `MockDomainService`, add `await asyncio.sleep(latency_ms / 1000)` before returning data
- Latency slightly randomized: `base_ms + random.randint(0, base_ms // 2)` (e.g., 150-225ms)
- WebSocket ticks are NOT delayed (already have 500-2000ms intervals)
- POST endpoints (create order, acknowledge alert) use lower latency (50-100ms) for snappy feel
- `POST /admin/reset` has zero latency

---

## PDF/CSV Report Generation (Reports Service)

Reports service MUST support downloading, not just viewing data on screen.

### CSV Export (Client-Side — All Data Tables)

- Add "Export CSV" button on every data table (P&L, settlements, orders, positions)
- Use client-side CSV generation from already-loaded data — no API endpoint needed
- Pattern: serialize visible columns → Blob → trigger download

### PDF Report (API-Side — Reports Service Only)

- "Generate PDF Report" button on P&L Attribution and Executive tabs
- API endpoint `POST /reporting/generate` accepts `{ type, client_id, date_range, format }`
- In mock mode: return a pre-generated sample PDF from `mock_data/sample_reports/`
- UX: click "Generate" → spinner → "Download Ready" toast with download link

---

## Cross-Domain Data Consistency (Seed Data Quality)

Mock data MUST be internally consistent. Inconsistencies destroy credibility in demos.

### Rules

1. **Price consistency**: OHLCV candle close prices MUST match prices used for that day's PnL calculation
2. **Reference integrity**: Every `strategy_id` in positions/orders MUST exist in strategies. Every `order_id` in fills
   MUST exist in orders. Every `org_id` MUST exist in organizations.
3. **Temporal consistency**: No position `opened_at` before strategy `inception_date`. No fills after market close. PnL
   time-series starts at strategy inception.
4. **Aggregation consistency**: Sum of position-level PnL per strategy approximately equals strategy reported PnL
5. **Batch/live consistency**: Batch = slightly stale version of live — not completely different data

### Validation

- `seed.py` MUST include `validate_consistency()` that checks all rules above
- Runs automatically after `seed_all_domains()`, raises on violation
- Agent 8's seed quality tests MUST verify consistency

---

## Codegen Pipeline Scripts (Create If Missing)

The SSOT Codegen Pipelines require scripts that may not yet exist. Agents MUST verify and create:

### Pipeline 1: UAC → UI Reference Data

- **Script**: `unified-api-contracts/scripts/generate_ui_reference_data.py`
- **If missing**: Create it — reads UAC registries (venues, instruments, enums, config schemas, error codes), outputs
  JSON consumable by UI
- **Output**: `unified-trading-system-ui/lib/registry/ui-reference-data.json`

### Pipeline 2: API → UI TypeScript Types

- **Verify**: `npm run generate:types` in `unified-trading-system-ui/package.json`
- **If missing**: Add: `"generate:types": "openapi-typescript lib/registry/openapi.json -o lib/types/api-generated.ts"`
- **Dependency**: `openapi-typescript` must be in devDependencies

### Pipeline 3: Persona Alignment

- **Script**: Create `unified-trading-api/scripts/verify_persona_alignment.py`
- **Checks**: auth-api org IDs == unified-trading-api personas.py org IDs == UI use-auth.ts persona names

---

## Code Splitting & Performance (ONE UI Consolidation)

Consolidating 13 UIs into one creates bundle size risk. Mitigate:

- Use Next.js `dynamic()` imports for heavy components (charting libraries, data grids, deployment forms)
- Each service area's page components should be lazily loaded
- Charts (candlestick, equity curve, heatmap) MUST use dynamic imports with `ssr: false`
- Target: initial bundle < 500KB, per-service chunks < 200KB each
- Verify with `NEXT_PUBLIC_MOCK_API=true npx next build` — check output for chunk sizes

---

## Agent Completion Protocol (MANDATORY after every todo)

Every agent MUST follow this protocol after completing work:

1. **TICK THE PLAN** — Change `- [ ]` to `- [x]` in the plan file for completed todos.

2. **RUN TESTS** — `bash scripts/quality-gates.sh` in every repo modified. If a test breaks:
   - Test logic WRONG (tests old pattern your refactor correctly replaced) → fix the test
   - Test logic RIGHT (catches real bug in refactor) → fix the refactor, not the test
   - The refactor plan is canonical, but tests provide quality guidance you MUST respect.

3. **HARDEN THE RULES** — Prevent future agents from undoing your work:
   - Deleted route? Add to `redirects_only` in next.config.mjs with comment explaining why.
   - Created new pattern? Add architectural comment at top of file.
   - Wired orphaned component? Remove from `orphaned_components_to_wire` in manifest.
   - Added API endpoint? Run `npm run generate:types` to update TypeScript types.

4. **UPDATE THE MANIFEST** — `UI_STRUCTURE_MANIFEST.json`:
   - Change page states (STUB → REAL), update line counts, add API hooks.
   - Remove completed items from `routes_to_delete`, `orphaned_components_to_wire`, `dead_tab_sets`.

5. **UPDATE DOCS** — If your change affects architecture: update CODEBASE_STRUCTURE.md, ROUTES.md,
   SERVICE_COMPLETION_STATUS.md, or repo-level CLAUDE.md/.cursorrules as needed.

6. **COMMIT WITH CONTEXT** — Every commit message must explain WHY and reference the plan todo ID.

---

## Cross-Agent Interface Contracts (BINDING — All Agents Must Follow)

These are the exact names, shapes, and conventions that multiple agents depend on. If any agent deviates, the
integration breaks silently. Treat these as immutable contracts.

### MockStateStore Collection Names (Agent 5 creates, Agent 6 seeds, Agents 2-4/7 read via API)

```
# Live collections (mutable, persisted to .local-dev-cache/)
positions_live, orders_live, fills_live, tickers_live, pnl_live,
strategies, organizations, clients, alerts, risk_limits,
ml_models, ml_experiments, ml_features, ml_training_jobs,
settlements, invoices, documents, services_health, fee_schedules,
mandates, users, compliance_rules, news, audit_trail, batch_jobs,
candles_1m, candles_5m, candles_1h, candles_1d, pnl_timeseries_live

# Batch collections (immutable, re-seeded on reset)
positions_batch, orders_batch, fills_batch, tickers_batch,
pnl_batch, pnl_timeseries_batch
```

### Org IDs (Agent 6 defines in personas.py, auth-api must match, UI must match)

```
odum-internal   — Odum Internal (admin + internal-trader personas)
acme            — Alpha Capital (client-full persona)
vertex          — Vertex Partners (client-premium persona)
beta            — Beta Fund (client-data-only persona)
```

### Persona Names (must be identical across auth-api, unified-trading-api, UI)

```
admin           — org: odum-internal, entitlements: ["*"]
internal-trader — org: odum-internal, entitlements: ["platform", "wildcard"]
client-full     — org: acme, entitlements: ["data", "research", "trading", "execution", "observe", "reports"]
client-premium  — org: vertex, entitlements: ["data", "execution", "research"]
client-data-only — org: beta, entitlements: ["data"]
```

### WebSocket Message Format (Agent 5 sends, Agent 2 consumes)

```jsonc
// Client → Server (subscribe)
{ "action": "subscribe", "channel": "market-data", "instruments": ["BTC-USDT", "ETH-USDT"] }

// Client → Server (unsubscribe)
{ "action": "unsubscribe", "channel": "market-data", "instruments": ["BTC-USDT"] }

// Server → Client (tick)
{ "channel": "market-data", "type": "tick", "data": {
    "instrument": "BTC-USDT", "price": 67234.50, "volume": 1.23,
    "bid": 67230.00, "ask": 67239.00, "timestamp": "2026-03-22T14:30:00Z"
}}

// Server → Client (alert)
{ "channel": "alerts", "type": "new_alert", "data": {
    "id": "alert-001", "severity": "high", "message": "...", "timestamp": "..."
}}
```

### API Query Params for Batch/Live (Agent 5 implements, Agents 2-4/7 send from UI)

```
GET /positions/active?mode=live                    → reads positions_live
GET /positions/active?mode=batch&as_of=2026-03-21  → reads positions_batch
GET /analytics/timeseries?mode=live                → reads pnl_timeseries_live
GET /analytics/timeseries?mode=batch               → reads pnl_timeseries_batch
```

Default (no mode param) = live. The UI sends the mode from `useGlobalScope().scope.mode`.

### Skeleton Component Names (Agent 1 creates, Agents 2-4/7 import)

```
components/ui/table-skeleton.tsx      — export TableSkeleton({ rows?: number, columns?: number })
components/ui/card-grid-skeleton.tsx   — export CardGridSkeleton({ cards?: number })
components/ui/chart-skeleton.tsx       — export ChartSkeleton({ height?: number })
```

### Debug Footer Props (Agent 1 creates, used in unified-shell.tsx)

```tsx
// The debug footer reads from these sources:
const { user } = useAuth(); // persona name, org
const { scope, setMode } = useGlobalScope(); // live/batch mode
const mockMode = process.env.NEXT_PUBLIC_MOCK_API === "true";

// Reset Demo calls:
// 1. POST /admin/reset (API — clears MockStateStore)
// 2. resetDemo() from lib/reset-demo.ts (UI — clears local state)
// 3. router.refresh() (reloads current page data)
```

### Entitlement Checks (All UI agents must use this pattern)

```tsx
// In any service page that needs entitlement gating:
const { hasEntitlement } = useAuth();
if (!hasEntitlement("execution")) return <UpgradeCard service="Execution" />;
```

---

## Key Technical Rules

- `uv pip install` not `pip install`
- `bash scripts/quality-gates.sh` for tests (never pytest directly)
- `bash scripts/quickmerge.sh "message" --agent` for commits (never git push directly)
- `basedpyright` not `pyright`
- No `os.getenv()` — use `UnifiedCloudConfig`
- Flat deps only in pyproject.toml (no optional-dependencies)
- Each repo has its own .venv for quality gates
