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

## Key Technical Rules

- `uv pip install` not `pip install`
- `bash scripts/quality-gates.sh` for tests (never pytest directly)
- `bash scripts/quickmerge.sh "message" --agent` for commits (never git push directly)
- `basedpyright` not `pyright`
- No `os.getenv()` — use `UnifiedCloudConfig`
- Flat deps only in pyproject.toml (no optional-dependencies)
- Each repo has its own .venv for quality gates
