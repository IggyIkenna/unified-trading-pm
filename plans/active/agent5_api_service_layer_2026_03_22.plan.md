---
name: agent5-api-service-layer
overview:
  Refactor unified-trading-api from mock/real if-else to service layer pattern, wire MockStateStore from UTL, add POST
  /admin/reset
todos:
  - id: a5-p0-service-interfaces
    content: |
      - [ ] [AGENT] P0. Create `unified_trading_api/services/` directory with service interface definitions using Python Protocol classes. Create one Protocol per domain: ExecutionService, PositionService, MarketDataService, AnalyticsService, MLService, ReportingService, AuditService, ConfigService, AlertService, RiskService, InstrumentService, DocumentService, DeploymentService, ServiceStatusService, UserService. Each Protocol defines the methods that the route handlers call (e.g., `async def list_orders(self, filters: OrderFilters) -> PaginatedResponse`).
    status: todo
  - id: a5-p0-mock-implementations
    content: |
      - [ ] [AGENT] P0. Create mock implementations for each service Protocol in `unified_trading_api/services/mock/`. Each mock service takes a `MockStateStore` instance and implements the Protocol methods by reading/writing to the store. CRITICAL: the mock implementations must apply the SAME filtering, pagination, sorting, and validation logic that real implementations would. The only difference is the data source (store.list() vs service_client.get()).
    status: todo
  - id: a5-p0-live-stubs
    content: |
      - [ ] [AGENT] P1. Create stub real implementations for each service Protocol in `unified_trading_api/services/live/`. Each stub raises `NotImplementedError("Wire to {service_name}")` but has the correct method signatures. This makes it clear what needs wiring later without breaking the code.
    status: todo
  - id: a5-p0-factory
    content: |
      - [ ] [AGENT] P0. Create `unified_trading_api/services/factory.py` with `get_{domain}_service(request: Request)` factory functions that return mock or real implementation based on `request.app.state.mock_mode`. These are used as FastAPI `Depends()` in route handlers.
    status: todo
  - id: a5-p1-execution-routes
    content: |
      - [ ] [AGENT] P0. Refactor `routes/execution.py` to use service layer. Replace all `if mock_mode: mock_store.list("orders")` with `service.list_orders(filters)`. The route handler should ONLY handle HTTP concerns (parsing query params, building response). All business logic lives in the service. Add POST /execution/orders endpoint for manual order placement.
    status: todo
  - id: a5-p1-positions-routes
    content: |
      - [ ] [AGENT] P0. Refactor `routes/positions.py` to use service layer. Add org-scoped filtering: positions should be filtered by the org_id from the auth token (in mock mode, filter by org_id field in mock data).
    status: todo
  - id: a5-p1-market-data-routes
    content: |
      - [ ] [AGENT] P0. Refactor `routes/market_data.py` to use service layer.
    status: todo
  - id: a5-p1-analytics-routes
    content: |
      - [ ] [AGENT] P0. Refactor `routes/trading_analytics.py` to use service layer. This is the largest route file (182 lines). Add `GET /analytics/strategies/{id}` for strategy detail, `POST /analytics/strategies/{id}/promote` and `POST /analytics/strategies/{id}/reject` for promotion workflow.
    status: todo
  - id: a5-p1-ml-routes
    content: |
      - [ ] [AGENT] P0. Refactor `routes/ml.py` to use service layer. Add endpoints: GET /ml/experiments, GET /ml/training-jobs, POST /ml/training-jobs, GET /ml/features, GET /ml/validation-results, POST /ml/models/{id}/promote.
    status: todo
  - id: a5-p1-remaining-routes
    content: |
      - [ ] [AGENT] P1. Refactor remaining route files to use service layer: alerts.py, audit.py, config.py, deployment.py, documents.py, instruments.py, reporting.py, risk.py, service_status.py, users.py. Each follows the same pattern: replace if/else mock check with service dependency injection.
    status: todo
  - id: a5-p2-use-utl-store
    content: |
      - [ ] [AGENT] P0. Replace the simple `unified_trading_api/mock_data/state_store.py` (69 lines, in-memory only) with the UTL `MockStateStore` from `unified_trading_library/core/mock_state_store.py` (314 lines, JSONL persistence in .local-dev-cache/). This gives us: persistence across restarts, thread safety, proper mutation tracking, reset capability. Import and use UTL's store instead of the local one.
    status: todo
  - id: a5-p2-admin-reset
    content: |
      - [ ] [AGENT] P0. Add `POST /admin/reset` endpoint (unauthenticated in mock mode, forbidden in real mode). This calls `mock_store.reset()` to clear all mutations and re-seed from `seed_all_domains()`. The UI's "Reset Demo" button will call this endpoint.
    status: todo
  - id: a5-p3-enhance-seeds
    content: |
      - [ ] [AGENT] P0. Enhance `mock_data/seed.py` to seed ALL domains comprehensively. Current seed has: orders (4), fills (3), execution_venues (5), algos (4), backtests (partial). Need to add/enhance:
        - positions: 12-15 positions across 5 venues, with org_id field for scoping
        - strategies: 18 strategies matching the `lib/trading-data.ts` STRATEGIES registry (same IDs, names, asset classes)
        - organizations: 4 orgs matching auth-api (odum-internal, acme/alpha-capital, beta, vertex)
        - clients: 6 clients across 4 orgs
        - alerts: 10-15 alerts with varying severity (critical, high, medium, low)
        - risk_limits: per-strategy risk limits (max exposure, VaR limit, drawdown limit)
        - ml_models: 5-8 models with versions, metrics, status
        - ml_experiments: 10 experiments with training metrics
        - settlements: 5-8 settlement records
        - invoices: 3-5 invoices
        - documents: 4-6 documents (compliance docs, trade confirmations)
        - services: 21 service health records matching actual service names
        - fee_schedules: 3 fee schedules (one per client tier)
        - mandates: 4 investment mandates
    status: todo
  - id: a5-p3-org-scoping
    content: |
      - [ ] [AGENT] P0. Add org_id field to ALL seed data records. Mock services filter by org_id extracted from the auth token (or from X-Demo-Persona header in mock mode). When persona is "admin" or "internal", return all data. When persona is a client, return only data matching their org_id.
    status: todo
  - id: a5-p4-websocket
    content: |
      - [ ] [AGENT] P2. Enhance `routes/websocket.py` to support mock tick generation. In mock mode, the WebSocket should emit simulated price ticks (using Brownian motion or similar) for subscribed instruments. This replaces the client-side Brownian motion simulation in the UI.
    status: todo
  - id: a5-p5-integration-tests
    content: |
      - [ ] [AGENT] P0. Add integration tests for every route in mock mode. For each of the 15 route files, add a test file in `tests/integration/` that:
        1. Creates the app with `mock_mode=True`
        2. Calls each endpoint
        3. Verifies response structure matches expected schema
        4. Verifies filtering works (e.g., `GET /execution/orders?venue=binance` returns only binance orders)
        5. Verifies pagination works
        6. Verifies org scoping works (request with client persona only sees their data)
    status: todo
  - id: a5-p5-admin-reset-test
    content: |
      - [ ] [AGENT] P0. Add test for POST /admin/reset: seed data → mutate (add order) → verify order exists → reset → verify order gone, original seed data restored.
    status: todo
  - id: a5-p5-quality-gates
    content: |
      - [ ] [AGENT] P0. Ensure `bash scripts/quality-gates.sh` passes with all new code. Fix any basedpyright errors, ruff violations, or test failures.
    status: todo
isProject: false
---

# Notes & Context

## Current state of unified-trading-api

- 16 domain routers, ~1,538 lines total
- Every route has `if mock_mode: return mock_store.list(domain)` / `else: return NOT_IMPLEMENTED`
- Simple MockStateStore (69 lines, in-memory, no persistence)
- 1 test file (test_health.py)
- seed.py has ~400 lines of seed data (partial coverage)

## UTL MockStateStore features (to adopt)

- JSONL persistence in .local-dev-cache/{service}/{collection}.jsonl
- Thread-safe with locking
- CRUD with merge semantics
- Reset capability (clear mutations, keep seed)
- Already used by: trading-analytics-api, config-api, batch-audit-api, client-reporting-api

## Absorbed from prior plans

- plan_h_api_consolidation: Full API consolidation plan (0% done, 49 todos) — this plan supersedes it
- plan_c_domain_data_api: Mock mode completeness (36% done) — absorbed
- plan_a_registry_schema_sync: Registry extraction (87.5% done) — incorporate finished work
- plan_b_config_hot_reload: Config schemas (32% done) — incorporate into config service
- mock_data_rollout_2026_03_18: Mock data enhancement (46% done) — absorbed into Phase 3

## Key constraint

- No MSW in the UI anymore. The UI always calls the real API at port 8030.
- The API handles mock/real internally via the service layer.
- This means ALL API endpoints must return realistic data in mock mode.
