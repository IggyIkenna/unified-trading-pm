---
name: agent5-api-service-layer
overview:
  Refactor unified-trading-api from mock/real if-else to service layer pattern, wire MockStateStore from UTL, add POST
  /admin/reset
todos:
  - id: a5-p0-service-interfaces
    content: |
      - [x] [AGENT] P0. DONE — services/ directory already exists with DomainService Protocol in base.py, MockDomainService in mock_service.py, LiveDomainService in live_service.py, factory.py with get_service(). VERIFY the Protocol covers all 15 domains listed. If any domain methods are missing, ADD them to the existing Protocol — do NOT recreate.
    status: done
  - id: a5-p0-mock-implementations
    content: |
      - [x] [AGENT] P0. DONE — MockDomainService exists in services/mock_service.py using MockStateStore. VERIFY it covers all 15 domains. If domain-specific logic is missing (e.g., filtering, pagination), ADD it to the existing implementation.
    status: done
  - id: a5-p0-live-stubs
    content: |
      - [x] [AGENT] P1. DONE — LiveDomainService exists in services/live_service.py with NotImplementedError stubs. VERIFY method signatures match Protocol.
    status: done
  - id: a5-p0-factory
    content: |
      - [x] [AGENT] P0. DONE — factory.py exists with get_service(request) used as FastAPI Depends(). VERIFY it handles mock/real switching correctly.
    status: done
  - id: a5-p1-execution-routes
    content: |
      - [ ] [AGENT] P0. VERIFY routes/execution.py uses service layer (already does). ADD missing endpoints: POST /execution/orders (manual order placement). Verify filtering and pagination work correctly.
    status: todo
  - id: a5-p1-positions-routes
    content: |
      - [ ] [AGENT] P0. Refactor `routes/positions.py` to use service layer. Add org-scoped filtering: positions should be filtered by the org_id from the auth token (in mock mode, filter by org_id field in mock data).
    status: todo
  - id: a5-p1-market-data-routes
    content: |
      - [ ] [AGENT] P0. VERIFY routes/market_data.py uses service layer. ADD missing endpoints: GET /market-data/candles, GET /market-data/orderbook (moved from Phase 4 — these are P0 for demo).
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
      - [ ] [AGENT] P0. VERIFY routes/websocket.py (4,859 lines, already has synthetic tick generator and channel multiplexing). Ensure: 1) Ticks update tickers_live collection in MockStateStore on each tick 2) Subscribe/unsubscribe protocol works 3) Multiple concurrent clients supported. ADD if missing: Brownian motion price drift, configurable tick intervals.
    status: todo
  - id: a5-p4-candles-endpoint
    content: |
      - [ ] [AGENT] P0. Add `GET /market-data/candles` endpoint. Parameters: `instrument` (required), `interval` (1m/5m/1h/1d, default 1h), `limit` (default 200). In mock mode, serve from MockStateStore `candles_{interval}` collection (seeded by Agent 6). Response: `[{ open, high, low, close, volume, timestamp }, ...]`.
    status: todo
  - id: a5-p4-orderbook-endpoint
    content: |
      - [ ] [AGENT] P0. Add `GET /market-data/orderbook` endpoint. Parameters: `instrument` (required). In mock mode, generate order book on-the-fly: 20 bid + 20 ask levels based on last ticker price from MockStateStore. Spread: 0.01-0.05% of price. Depth: decreasing away from mid. Add slight randomization on each request to simulate market movement. Response: `{ bids: [{ price, quantity }], asks: [{ price, quantity }], mid_price, spread }`.
    status: todo
  # ── Phase 4B: Auth-API & Client-Reporting-API Integration ──
  - id: a5-p4b-reporting-proxy
    content: |
      - [ ] [AGENT] P0. In unified-trading-api, make `routes/reporting.py` act as a proxy to client-reporting-api (port 8014) in real mode. In mock mode, continue serving from MockStateStore. Implementation:
        1. In mock mode: `return await service.list_reports(filters)` (from MockStateStore, same as before)
        2. In real mode: `return await httpx.AsyncClient().get(f"http://localhost:8014/api/reports", params=filters)`
        3. This means the UI only ever calls port 8030 — it never needs to know about port 8014
        4. Add `/reporting/pnl-attribution`, `/reporting/executive-summary`, `/reporting/invoices`, `/reporting/regulatory` if not already present
    status: todo
  - id: a5-p4b-auth-api-alignment
    content: |
      - [ ] [AGENT] P0. Ensure unified-trading-api can validate JWTs issued by auth-api. In mock mode with `DISABLE_AUTH=true`, skip validation but still extract persona from the token (or from `X-Demo-Persona` header as fallback). In real mode, validate JWT signature against auth-api's public key. The persona/org_id extracted from the token drives org-scoped data filtering. Verify:
        1. Auth-api's `mock_data.py` persona org IDs match unified-trading-api's `personas.py` org IDs
        2. Token claims include: `user_id`, `org_id`, `role`, `entitlements[]`
        3. Add a `get_current_user()` FastAPI dependency that extracts this from the request
    status: todo
  - id: a5-p4b-dev-stack-wiring
    content: |
      - [ ] [AGENT] P1. Update `unified-trading-pm/scripts/dev/ui-api-mapping.json` to add auth-api:
        `{ "name": "auth-api", "api_port": 8200, "module": "auth_api" }`
        Verify auth-api is started by `dev-start.sh --all`. Verify the UI's `next.config.mjs` rewrite (`/api/auth/*` → `http://localhost:8200/*`) works when auth-api is running.
    status: todo
  # ── Phase 4C: Live Data Persistence ──
  - id: a5-p4c-live-persistence
    content: |
      - [ ] [AGENT] P0. Configure MockStateStore to persist live-domain collections to `.local-dev-cache/unified-trading-api/`. All collections with `_live` suffix persist as JSONL files. Both mock and production modes read from the same directory structure — the only difference is what writes to it (mock tick generator vs real service). Batch collections (`_batch` suffix) are seeded once and immutable. Ensure:
        1. WebSocket tick generator updates `tickers_live.jsonl` on each tick
        2. Manual order placement updates `orders_live.jsonl`
        3. `POST /admin/reset` clears live mutations and re-seeds both live and batch collections
        4. On startup, if `.local-dev-cache/` has existing data (MOCK_STATE_MODE=interactive), load it instead of re-seeding
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
  # ── Phase 6: Latency Simulation, PDF Endpoints, Codegen (Gap-Closing) ──
  - id: a5-p6-latency-sim
    content: |
      - [ ] [AGENT] P0. Add latency simulation to MockDomainService. Without this, mock APIs return in <1ms and the demo feels fake — skeletons flash invisibly, loading states can't be verified.
        1. Read `MOCK_LATENCY_MS` env var (default: 0 in CI/deterministic, 150 in interactive mode)
        2. In MockDomainService.list() and .get(), add `await asyncio.sleep((base_ms + random.randint(0, base_ms // 2)) / 1000)`
        3. POST endpoints (create order, acknowledge): lower latency (50-100ms) for snappy feel
        4. POST /admin/reset: zero latency
        5. WebSocket ticks: NOT delayed (already have 500-2000ms intervals)
    status: todo
  - id: a5-p6-pdf-endpoints
    content: |
      - [ ] [AGENT] P1. Add PDF report generation endpoints for Reports service:
        1. `POST /reporting/generate` — accepts { type, client_id, date_range, format }. In mock mode: create a record in MockStateStore "generated_reports" with status "ready" and a report_id. Return { report_id, status: "ready" }.
        2. `GET /reporting/download/{report_id}` — serves a sample PDF file. Create `mock_data/sample_reports/` directory with 1-2 sample PDFs (can be minimal: title page + one table). Return with Content-Type: application/pdf.
        3. In real mode: proxy to client-reporting-api's generation endpoint.
    status: todo
  - id: a5-p6-codegen-verify
    content: |
      - [ ] [AGENT] P1. Verify and create codegen pipeline scripts if missing:
        1. Check if `npm run generate:types` exists in unified-trading-system-ui/package.json. If not, add: `"generate:types": "openapi-typescript lib/registry/openapi.json -o lib/types/api-generated.ts"` and add `openapi-typescript` to devDependencies.
        2. Create `scripts/verify_persona_alignment.py` — reads auth-api mock_data.py and unified-trading-api personas.py, verifies org IDs and persona names match. Exit 1 on mismatch.
        3. Verify unified-trading-api generates valid OpenAPI spec: `curl http://localhost:8030/openapi.json` should return complete spec with all routes documented.
    status: todo
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-pm/plans/active/CITADEL_VISION_2026_03_22.md` — system-wide vision
2. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — see `pages_needing_api_wiring` (18 pages) and
   per-service API endpoint requirements
3. The UI has 18 REAL pages using inline mock data that need API wiring. Your service layer must serve ALL endpoints
   those pages expect.

## 3-API Architecture

- `auth-api` (port 8200) — stays separate, handles SSO/tokens
- `client-reporting-api` (port 8014) — stays separate, handles client reports/invoices
- `unified-trading-api` (port 8030) — YOUR scope. Absorbs 8 domain APIs. Routes reporting/\* to client-reporting-api in
  real mode.

## Current state of unified-trading-api (verified 2026-03-22)

- 19 domain routers using service layer DI (get_service(request)) — NO if/else mock checks
- services/ EXISTS: DomainService Protocol (base.py), MockDomainService (mock_service.py), LiveDomainService
  (live_service.py), factory.py
- WebSocket: 4,859 lines with channel-based multiplexing and synthetic tick generator
- personas.py: 121 lines, 4 orgs, 5 personas, matches auth-api
- state_store.py: 68 lines, in-memory only — NEEDS UTL MockStateStore migration
- seed.py: 1,323 lines covering basic domains — NEEDS enrichment
- 3 test files (minimal) — NEEDS expansion to 80%+ coverage
- auth-api: EXISTS at port 8200 with JWT — NOT in dev stack yet

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

## New scope (added 2026-03-22 gap analysis)

- WebSocket mock tick generator is now P0 (was P2) — critical for demo feel
- OHLCV candle and order book endpoints are new P0 requirements
- Reporting routes proxy to client-reporting-api (port 8014) in real mode
- Auth-api JWT validation and persona extraction
- Live data persistence to .local-dev-cache/ via MockStateStore JSONL
- Batch/live collection separation: `{domain}_live` vs `{domain}_batch`
- auth-api must be added to dev-start.sh and ui-api-mapping.json
