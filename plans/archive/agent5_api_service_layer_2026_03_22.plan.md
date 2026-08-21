---
doc_type: plan
title: agent5-api-service-layer
summary: Refactor unified-trading-api from mock/real if-else to service layer pattern, wire MockStateStore from UTL, add
  POST /admin/reset
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [client-reporting-api, unified-trading-api, unified-trading-pm, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-22'
todos:
- {id: a5-p0-service-interfaces, content: '- [x] [AGENT] P0. DONE — services/ directory already exists with DomainService Protocol in base.py, MockDomainService in mock_service.py, LiveDomainService in live_service.py, factory.py with get_service(). VERIFY the Protocol covers all 15 domains listed. If any domain methods are missing, ADD them to the existing Protocol — do NOT recreate.

    ', status: done}
- {id: a5-p0-mock-implementations, content: '- [x] [AGENT] P0. DONE — MockDomainService exists in services/mock_service.py using MockStateStore. VERIFY it covers all 15 domains. If domain-specific logic is missing (e.g., filtering, pagination), ADD it to the existing implementation.

    ', status: done}
- {id: a5-p0-live-stubs, content: '- [x] [AGENT] P1. DONE — LiveDomainService exists in services/live_service.py with NotImplementedError stubs. VERIFY method signatures match Protocol.

    ', status: done}
- {id: a5-p0-factory, content: '- [x] [AGENT] P0. DONE — factory.py exists with get_service(request) used as FastAPI Depends(). VERIFY it handles mock/real switching correctly.

    ', status: done}
- {id: a5-p0-readiness-runtime-contract, content: "- [x] [AGENT] P0. **Readiness + runtime mode (SSOT: CITADEL_VISION § Runtime mode: env vars, CLI, health, and UI truthfulness).** On `unified-trading-api`:\n  1. Implement `GET /readiness` (or extend existing health) returning JSON: `app_env`, `declared_runtime_tier`, `effective_runtime_tier`, `mock_domain_service`, `external_data_mocked`, `upstream_checks[]` (name, required_for_tier, ok, url, error), `degraded_reasons[]`.\n  2. **Declared tier** from env (e.g. `RUNTIME_TIER_DECLARED=0|1|2` or derive from `LIVE_SERVICE_*` URLs non-empty → tier 2 intent).\n  3. **Effective tier** — probe configured upstream URLs when `LiveDomainService` / non-mock; if required upstream down, set effective < declared and populate `degraded_reasons`.\n  4. **503 vs 200** — pick one policy document in OpenAPI; recommend 503 when effective < declared for automation, 200 + `ok: false` for UI polling (choose and document).\n  5. **Startup** — log WARN when mock\
    \ gateway env conflicts with non-empty live service URLs; log INFO one-line effective summary.\n  6. Optional: aggregate sibling readiness by HTTP for System Health (Agent 7) — behind flag to avoid thundering herd.\n", status: done}
- {id: a5-p1-execution-routes, content: '- [x] [AGENT] P0. VERIFY routes/execution.py uses service layer (already does). ADD missing endpoints: POST /execution/orders (manual order placement). Verify filtering and pagination work correctly.

    ', status: done}
- {id: a5-p1-positions-routes, content: '- [x] [AGENT] P0. Refactor `routes/positions.py` to use service layer. Add org-scoped filtering: positions should be filtered by the org_id from the auth token (in mock mode, filter by org_id field in mock data).

    ', status: done}
- {id: a5-p1-market-data-routes, content: '- [x] [AGENT] P0. VERIFY routes/market_data.py uses service layer. ADD missing endpoints: GET /market-data/candles, GET /market-data/orderbook (moved from Phase 4 — these are P0 for demo).

    ', status: done}
- {id: a5-p1-analytics-routes, content: '- [x] [AGENT] P0. Refactor `routes/trading_analytics.py` to use service layer. This is the largest route file (182 lines). Add `GET /analytics/strategies/{id}` for strategy detail, `POST /analytics/strategies/{id}/promote` and `POST /analytics/strategies/{id}/reject` for promotion workflow.

    ', status: done}
- {id: a5-p1-ml-routes, content: '- [x] [AGENT] P0. Refactor `routes/ml.py` to use service layer. Add endpoints: GET /ml/experiments, GET /ml/training-jobs, POST /ml/training-jobs, GET /ml/features, GET /ml/validation-results, POST /ml/models/{id}/promote.

    ', status: done}
- {id: a5-p1-remaining-routes, content: "- [x] [AGENT] P1. Refactor remaining route files to use service layer: alerts.py, audit.py, config.py, deployment.py, documents.py, instruments.py, reporting.py, risk.py, service_status.py, users.py. Each follows the same pattern: replace if/else mock check with service dependency injection.\n  CRITICAL: alerts.py and risk.py MUST support live/batch mode via `?mode=live|batch` query param, same as positions/orders/PnL. In mock mode:\n  - `GET /alerts/active?mode=live` → reads `alerts_live` (mutable, new alerts arrive via WebSocket, can be acknowledged)\n  - `GET /alerts/active?mode=batch` → reads `alerts_batch` (immutable T+1 reconciled alert snapshot — all alerts have final status)\n  - `GET /risk/exposure?mode=live` → reads `risk_live` (updated as positions change from ticks)\n  - `GET /risk/exposure?mode=batch` → reads `risk_batch` (end-of-day risk snapshot)\n  The service layer code for filtering, pagination, and org-scoping is >90% identical\
    \ between modes. The ONLY branching is the collection name suffix. No mode-specific business logic.\n", status: done}
- {id: a5-p1-operational-actions, content: "- [x] [AGENT] P0. Add operational action endpoints that MUTATE MockStateStore state — not just read-only views. Every action button in the UI must call a real API endpoint that changes server-side state:\n  1. `POST /alerts/{id}/acknowledge` — sets `acknowledged: true`, `acknowledged_by: user_id`, `acknowledged_at: timestamp` in `alerts_live`. Returns updated alert. Verify via: `curl -X POST /alerts/alert-001/acknowledge` then `curl /alerts/active?acknowledged=false` shows one fewer alert.\n  2. `POST /alerts/{id}/escalate` — sets `severity` up one level (medium→high, high→critical), adds `escalated_at` timestamp. Returns updated alert.\n  3. `POST /risk/circuit-breaker` — accepts `{ strategy_id, action: \"trip\" | \"reset\" }`. In mock mode: updates `strategies` collection setting `circuit_breaker_status: \"tripped\"` or `\"active\"`. A tripped circuit breaker means: the strategy card shows \"HALTED\" badge, no new orders are generated for that\
    \ strategy. Verify via: trip a breaker → `curl /analytics/strategies/{id}` shows `circuit_breaker_status: \"tripped\"` → reset → shows `\"active\"`.\n  4. `POST /risk/kill-switch` — accepts `{ scope: \"strategy\" | \"venue\" | \"global\", target_id }`. Sets `kill_switch_active: true` on the target. Kill switch is the emergency version of circuit breaker — stops all activity for that scope.\n  5. `POST /analytics/strategies/{id}/scale` — accepts `{ scale_factor: 0.5 }`. Updates strategy's `position_scale` field. Demonstrates dynamic risk management: ops can scale a strategy down to 50% without stopping it.\n  All of these MUST mutate MockStateStore so subsequent GET calls reflect the change. The UI shows the result of the mutation, not a local toggle. `POST /admin/reset` restores all to initial state.\n  In production, these would call the real service engines (risk-and-exposure-service circuit breaker, execution-service kill switch). The mock versions simulate the same state transitions.\n",
  status: done}
- {id: a5-p2-use-utl-store, content: '- [x] [AGENT] P0. Replace the simple `unified_trading_api/mock_data/state_store.py` (69 lines, in-memory only) with the UTL `MockStateStore` from `unified_trading_library/core/mock_state_store.py` (314 lines, JSONL persistence in .local-dev-cache/). This gives us: persistence across restarts, thread safety, proper mutation tracking, reset capability. Import and use UTL''s store instead of the local one.

    ', status: done}
- {id: a5-p2-admin-reset, content: '- [x] [AGENT] P0. Add `POST /admin/reset` endpoint (unauthenticated in mock mode, forbidden in real mode). This calls `mock_store.reset()` to clear all mutations and re-seed from `seed_all_domains()`. The UI''s "Reset Demo" button will call this endpoint.

    ', status: done}
- {id: a5-p3-enhance-seeds, content: "- [x] [AGENT] P0. Enhance `mock_data/seed.py` to seed ALL domains comprehensively. Current seed has: orders (4), fills (3), execution_venues (5), algos (4), backtests (partial). Need to add/enhance:\n  - positions: 12-15 positions across 5 venues, with org_id field for scoping\n  - strategies: 18 strategies matching the `lib/trading-data.ts` STRATEGIES registry (same IDs, names, asset classes)\n  - organizations: 4 orgs matching auth-api (odum-internal, acme/alpha-capital, beta, vertex)\n  - clients: 6 clients across 4 orgs\n  - alerts: 10-15 alerts with varying severity (critical, high, medium, low)\n  - risk_limits: per-strategy risk limits (max exposure, VaR limit, drawdown limit)\n  - ml_models: 5-8 models with versions, metrics, status\n  - ml_experiments: 10 experiments with training metrics\n  - settlements: 5-8 settlement records\n  - invoices: 3-5 invoices\n  - documents: 4-6 documents (compliance docs, trade confirmations)\n  - services: 21\
    \ service health records matching actual service names\n  - fee_schedules: 3 fee schedules (one per client tier)\n  - mandates: 4 investment mandates\n", status: done}
- {id: a5-p3-org-scoping, content: '- [x] [AGENT] P0. Add org_id field to ALL seed data records. Mock services filter by org_id extracted from the auth token (or from X-Demo-Persona header in mock mode). When persona is "admin" or "internal", return all data. When persona is a client, return only data matching their org_id.

    ', status: done}
- {id: a5-p4-websocket, content: '- [x] [AGENT] P0. VERIFY routes/websocket.py (4,859 lines, already has synthetic tick generator and channel multiplexing). Ensure: 1) Ticks update tickers_live collection in MockStateStore on each tick 2) Subscribe/unsubscribe protocol works 3) Multiple concurrent clients supported. ADD if missing: Brownian motion price drift, configurable tick intervals. CRITICAL: The tick generator must iterate ALL instruments from UAC `representative_sample.py` (import the spec lists), not a hardcoded list. If the registry expands, ticks expand automatically.

    ', status: done}
- {id: a5-p4-realtime-pnl, content: "- [x] [AGENT] P0. ADD real-time PnL recalculation to the mock service layer. This is CRITICAL for demo feel — the dashboard must come alive as prices move. The calculation MUST happen server-side (in MockDomainService), NOT in the UI.\n  On each WebSocket tick batch:\n  1. Update `tickers_live` collection with new prices (already planned above)\n  2. Recalculate positions in `positions_live`: For each position where `instrument == tick.instrument`, compute `unrealized_pnl = (tick.price - position.entry_price) * position.quantity * side_multiplier`. Write updated positions back to MockStateStore.\n  3. Aggregate strategy-level PnL: Group `positions_live` by strategy_id, sum unrealized_pnl per strategy. Update `pnl_live` collection.\n  4. Emit WebSocket messages on dedicated channels: `{ channel: \"positions\", type: \"pnl_update\", data: { positions } }` and `{ channel: \"analytics\", type: \"pnl_snapshot\", data: { strategies } }`.\n  The curl test: `wscat\
    \ -c ws://localhost:8030/ws` subscribe to positions channel, observe PnL values changing as ticks arrive. If this works via wscat, the UI just renders it.\n  DEPENDENCY: a5-p2-use-utl-store (MockStateStore), a5-p3-enhance-seeds (positions with entry_price + strategy_id).\n", status: done}
- {id: a5-p4-candles-endpoint, content: '- [x] [AGENT] P0. Add `GET /market-data/candles` endpoint. Parameters: `instrument` (required), `interval` (1m/5m/1h/1d, default 1h), `limit` (default 200). In mock mode, serve from MockStateStore `candles_{interval}` collection (seeded by Agent 6). Response: `[{ open, high, low, close, volume, timestamp }, ...]`.

    ', status: done}
- {id: a5-p4-orderbook-endpoint, content: '- [x] [AGENT] P0. Add `GET /market-data/orderbook` endpoint. Parameters: `instrument` (required). In mock mode, generate order book on-the-fly: 20 bid + 20 ask levels based on last ticker price from MockStateStore. Spread: 0.01-0.05% of price. Depth: decreasing away from mid. Add slight randomization on each request to simulate market movement. Response: `{ bids: [{ price, quantity }], asks: [{ price, quantity }], mid_price, spread }`.

    ', status: done}
- {id: a5-p4b-reporting-proxy, content: "- [x] [AGENT] P0. In unified-trading-api, make `routes/reporting.py` act as a proxy to client-reporting-api (port 8014) in real mode. In mock mode, continue serving from MockStateStore. Implementation:\n  1. In mock mode: `return await service.list_reports(filters)` (from MockStateStore, same as before)\n  2. In real mode: `return await httpx.AsyncClient().get(f\"http://localhost:8014/api/reports\", params=filters)`\n  3. This means the UI only ever calls port 8030 — it never needs to know about port 8014\n  4. Add `/reporting/pnl-attribution`, `/reporting/executive-summary`, `/reporting/invoices`, `/reporting/regulatory` if not already present\n", status: done}
- {id: a5-p4b-auth-api-alignment, content: "- [x] [AGENT] P0. Ensure unified-trading-api can validate JWTs issued by auth-api. In mock mode with `DISABLE_AUTH=true`, skip validation but still extract persona from the token (or from `X-Demo-Persona` header as fallback). In real mode, validate JWT signature against auth-api's public key. The persona/org_id extracted from the token drives org-scoped data filtering. Verify:\n  1. Auth-api's `mock_data.py` persona org IDs match unified-trading-api's `personas.py` org IDs\n  2. Token claims include: `user_id`, `org_id`, `role`, `entitlements[]`\n  3. Add a `get_current_user()` FastAPI dependency that extracts this from the request\n", status: done}
- {id: a5-p4b-dev-stack-wiring, content: "- [x] [AGENT] P1. Update `unified-trading-pm/scripts/dev/ui-api-mapping.json` to add auth-api:\n  `{ \"name\": \"auth-api\", \"api_port\": 8200, \"module\": \"auth_api\" }`\n  Verify auth-api is started by `dev-start.sh --all`. Verify the UI's `next.config.mjs` rewrite (`/api/auth/*` → `http://localhost:8200/*`) works when auth-api is running.\n", status: done}
- {id: a5-p4c-live-persistence, content: "- [x] [AGENT] P0. Configure MockStateStore to persist live-domain collections to `.local-dev-cache/unified-trading-api/`. All collections with `_live` suffix persist as JSONL files. Both mock and production modes read from the same directory structure — the only difference is what writes to it (mock tick generator vs real service). Batch collections (`_batch` suffix) are seeded once and immutable. Ensure:\n  1. WebSocket tick generator updates `tickers_live.jsonl` on each tick\n  2. Manual order placement updates `orders_live.jsonl`\n  3. `POST /admin/reset` clears live mutations and re-seeds both live and batch collections\n  4. On startup, if `.local-dev-cache/` has existing data (MOCK_STATE_MODE=interactive), load it instead of re-seeding\n", status: done}
- {id: a5-p5-integration-tests, content: "- [x] [AGENT] P0. Add integration tests for every route in mock mode. For each of the 15 route files, add a test file in `tests/integration/` that:\n  1. Creates the app with `mock_mode=True`\n  2. Calls each endpoint\n  3. Verifies response structure matches expected schema\n  4. Verifies filtering works (e.g., `GET /execution/orders?venue=binance` returns only binance orders)\n  5. Verifies pagination works\n  6. Verifies org scoping works (request with client persona only sees their data)\n", status: done}
- {id: a5-p5-admin-reset-test, content: '- [x] [AGENT] P0. Add test for POST /admin/reset: seed data → mutate (add order) → verify order exists → reset → verify order gone, original seed data restored.

    ', status: done}
- {id: a5-p5-quality-gates, content: '- [x] [AGENT] P0. Ensure `bash scripts/quality-gates.sh` passes with all new code. Fix any basedpyright errors, ruff violations, or test failures.

    ', status: done}
- {id: a5-p6-latency-sim, content: "- [x] [AGENT] P0. Add latency simulation to MockDomainService. Without this, mock APIs return in <1ms and the demo feels fake — skeletons flash invisibly, loading states can't be verified.\n  1. Read `MOCK_LATENCY_MS` env var (default: 0 in CI/deterministic, 150 in interactive mode)\n  2. In MockDomainService.list() and .get(), add `await asyncio.sleep((base_ms + random.randint(0, base_ms // 2)) / 1000)`\n  3. POST endpoints (create order, acknowledge): lower latency (50-100ms) for snappy feel\n  4. POST /admin/reset: zero latency\n  5. WebSocket ticks: NOT delayed (already have 500-2000ms intervals)\n", status: done}
- {id: a5-p6-pdf-endpoints, content: "- [x] [AGENT] P1. Add PDF report generation endpoints for Reports service:\n  1. `POST /reporting/generate` — accepts { type, client_id, date_range, format }. In mock mode: create a record in MockStateStore \"generated_reports\" with status \"ready\" and a report_id. Return { report_id, status: \"ready\" }.\n  2. `GET /reporting/download/{report_id}` — serves a sample PDF file. Create `mock_data/sample_reports/` directory with 1-2 sample PDFs (can be minimal: title page + one table). Return with Content-Type: application/pdf.\n  3. In real mode: proxy to client-reporting-api's generation endpoint.\n", status: done}
- {id: a5-p6-codegen-verify, content: "- [x] [AGENT] P1. Verify and create codegen pipeline scripts if missing:\n  1. Check if `npm run generate:types` exists in unified-trading-system-ui/package.json. If not, add: `\"generate:types\": \"openapi-typescript lib/registry/openapi.json -o lib/types/api-generated.ts\"` and add `openapi-typescript` to devDependencies.\n  2. Create `scripts/verify_persona_alignment.py` — reads auth-api mock_data.py and unified-trading-api personas.py, verifies org IDs and persona names match. Exit 1 on mismatch.\n  3. Verify unified-trading-api generates valid OpenAPI spec: `curl http://localhost:8030/openapi.json` should return complete spec with all routes documented.\n", status: done}
- {id: a5-p7-full-instrument-coverage, content: "- [x] [AGENT] P0. Expand API to serve ALL instruments from UAC representative_sample.py — not a hardcoded subset:\n  1. Import `from unified_api_contracts.registry.representative_sample import ...` to get the full instrument list\n  2. Candles endpoint (`GET /market-data/candles`) must serve data for ALL instruments in the registry (seeded by Agent 6)\n  3. Tickers endpoint (`GET /market-data/tickers`) must return tickers for ALL instruments\n  4. Order book endpoint (`GET /market-data/orderbook`) must generate depth for ANY requested instrument\n  5. WebSocket tick generator must support subscriptions for ANY instrument in the registry\n  6. Instrument list endpoint (`GET /instruments/list`) must return the full registry with category grouping\n  DEPENDENCY: Agent 6 must seed data for all instruments. UAC representative_sample.py is the SSOT.\n", status: done}
- {id: a5-p7-strategy-capacity, content: "- [x] [AGENT] P0. Ensure all strategy-related endpoints handle 50+ strategies from expanded seed data:\n  1. `GET /analytics/strategies` — must paginate and filter efficiently for 50+ strategies\n  2. `GET /analytics/timeseries` — must serve PnL time-series for any of 50+ strategy IDs\n  3. `GET /positions/active` — positions across 50+ strategies must support strategy_id filter\n  4. No new code paths needed — the service layer is config-driven, not strategy-type-driven\n  5. Verify no hardcoded strategy counts or assumptions in the service layer\n  DEPENDENCY: Agent 6 must expand seed data to 50+ strategies first.\n", status: done}
- {id: a5-p7-scheduled-reports-endpoint, content: "- [x] [AGENT] P1. Add `POST /reporting/schedules` and `GET /reporting/schedules` endpoints for scheduled report configuration:\n  1. POST accepts: { frequency, recipients, report_type, format }. In mock mode: creates record in MockStateStore \"scheduled_reports\"\n  2. GET returns all scheduled reports for the authenticated org\n  3. In mock mode, no actual emails sent — just persists configuration\n  DEPENDENCY: None — Agent 4 will wire the UI to these endpoints.\n", status: done}
- {id: a5-p8-pre-trade-check, content: "- [x] [AGENT] P0. Add `POST /compliance/pre-trade-check` endpoint. GAP CATEGORY: Type 2+3 (service has it, mock doesn't simulate it).\n  The REAL implementation lives in:\n  - `risk-and-exposure-service/core/pre_trade_check_engine.py` — 6 checks (position limit, exposure limit, capital limit, leverage limit, VaR limit, stale price guard)\n  - `execution-service/engine/live/risk.py` — PreTradeRiskEngine.check_order()\n  In MockDomainService, SIMULATE these checks against seeded data:\n  1. Accept: `{ instrument, side, quantity, price, strategy_id }`\n  2. Read `risk_limits` collection for the strategy's limits (seeded by Agent 6)\n  3. Read `positions_live` to get current exposure for that strategy\n  4. Run simplified checks: proposed_position + existing_positions vs max_position_size, current_leverage vs max_leverage, etc.\n  5. Return: `{ approved: bool, checks: [{ name: \"position_limit\", status: \"pass\"|\"fail\", limit: 100000, current: 45000,\
    \ proposed: 55000 }] }`\n  6. If ANY check fails, approved=false. Include all check results regardless.\n  The curl test: `curl -X POST /compliance/pre-trade-check -d '{\"instrument\":\"BTC-USDT\",\"side\":\"BUY\",\"quantity\":1,\"price\":67000,\"strategy_id\":\"alpha-btc-momentum\"}'` must return check results.\n  DEPENDENCY: Agent 6 must seed `risk_limits` collection with per-strategy limits.\n", status: done}
- {id: a5-p8-derivatives-endpoints, content: "- [x] [AGENT] P0. Add derivatives/options endpoints. GAP CATEGORY: Type 2+3 (services have full options pricing — mock doesn't expose it).\n  The REAL implementations live in:\n  - `features-volatility-service/app/calculators/second_order_greeks.py` — Black-Scholes + Black-76 Greeks\n  - `features-volatility-service/app/calculators/tradfi_vol_surface.py` — Full vol surface computation\n  - `position-balance-monitor-service/core/greeks_aggregator.py` — Portfolio Greeks aggregation\n  - `unified-api-contracts/canonical/domain/derivatives/` — CanonicalOptionsChainEntry, VolSurface schemas\n  In MockDomainService, serve SEEDED data that matches these services' output shapes:\n  1. `GET /derivatives/options-chain?underlying=BTC&venue=deribit` — returns seeded options chain from `options_chain` collection. Each entry: strike, option_type (call/put), expiration, bid, ask, implied_vol, delta, gamma, theta, vega. Agent 6 seeds this using Deribit specs\
    \ from representative_sample.py.\n  2. `GET /derivatives/vol-surface?underlying=BTC` — returns seeded vol surface from `vol_surfaces` collection. Shape: { slices: [{ expiry, smile: [{ strike, iv }] }], term_structure: [{ expiry, atm_iv }], atm_iv, skew_25d, butterfly_25d }.\n  3. `GET /derivatives/portfolio-greeks` — returns aggregated portfolio Greeks from options positions. Sum delta/gamma/theta/vega/rho across all options positions in `positions_live` that have Greeks fields.\n  DO NOT implement Black-Scholes in the gateway — just serve seeded data. The real pricing lives in features-volatility-service.\n", status: done}
- {id: a5-p8-risk-analytics-endpoints, content: "- [x] [AGENT] P0. Add risk analytics endpoints. GAP CATEGORY: Type 2+3 (risk-and-exposure-service has VaR, stress, correlation — mock doesn't expose it).\n  The REAL implementations live in:\n  - `risk-and-exposure-service/core/var_calculator.py` — 6 VaR methods + stress scenarios (GFC_2008=3.5x, COVID_2020=2.5x, CRYPTO_BLACK_THURSDAY=5.0x)\n  - `risk-and-exposure-service/core/correlation_matrix.py` — Pearson correlation matrix\n  - `risk-and-exposure-service/core/regime_detector.py` — normal/stressed/crisis regime detection\n  - `risk-and-exposure-service/scripts/seed_mock_data.py` — 548L deterministic seed generator (IMPORT FORMAT FROM THIS)\n  In MockDomainService, serve SEEDED data:\n  1. `GET /risk/var-summary` — returns pre-computed VaR per strategy from `var_metrics` collection. Fields: strategy_id, historical_var_99, parametric_var_99, cvar_99, cornish_fisher_var_99, monte_carlo_var_99. Agent 6 seeds this.\n  2. `GET /risk/stress-test?scenario=GFC_2008`\
    \ — returns portfolio impact. Mock: read `stress_test_results` collection (seeded per scenario). Fields: scenario, portfolio_impact_pct, worst_strategy, expected_loss_usd.\n  3. `GET /risk/correlation-matrix` — returns NxN correlation matrix from `correlation_matrix` collection. Agent 6 seeds a realistic matrix (crypto correlated ~0.6, tradfi ~0.3, defi/sports ~0).\n  4. `GET /risk/regime` — returns current regime: { regime: \"normal\"|\"stressed\"|\"crisis\", multiplier: 1.0|1.5|2.5, signals: { volatility, correlation, drawdown_velocity } }.\n", status: done}
- {id: a5-p8-fx-rates, content: "- [x] [AGENT] P0. Add FX rates endpoint and apply conversion in PnL aggregation. GAP CATEGORY: Type 1+3 (NO service has FX — genuinely missing. Trivial to mock).\n  1. `GET /market-data/fx-rates` — returns static FX rates from `fx_rates` collection: { \"BTC/USD\": 67000, \"ETH/USD\": 3500, \"USDT/USD\": 1.0001, \"EUR/USD\": 1.08, \"GBP/USD\": 1.27 }\n  2. In MockDomainService PnL aggregation (real-time PnL recalculation from a5-p4-realtime-pnl): when summing unrealized_pnl across positions, apply FX conversion: `usd_pnl = position.unrealized_pnl * position.fx_rate_to_usd`. Agent 6 seeds `fx_rate_to_usd` on each position (1.0 for USD, 67000 for BTC-denominated Deribit, etc.).\n  3. Dashboard KPI cards (Total AUM, Total PnL) must show USD-converted aggregates.\n  This is ~10 lines of code in the PnL aggregation function + a simple endpoint.\n", status: done}
- {id: a5-p8-regulatory-reports, content: "- [x] [AGENT] P1. Add `GET /reporting/regulatory` endpoint. GAP CATEGORY: Type 2+3 (execution-service has MiFID II/FCA compliance reporter — mock doesn't simulate it).\n  The REAL implementation lives in:\n  - `execution-service/compliance/mifid_reporter.py` — MiFIDReporter with best execution checks\n  - `execution-service/compliance/compliance_reporter.py` — EU_MIFID_II and UK_FCA jurisdiction\n  In MockDomainService, serve seeded regulatory report records from `regulatory_reports` collection:\n  Fields: report_id, report_type (MIFID_II_BEST_EXECUTION / FCA_TRANSACTION / EMIR_DERIVATIVE), jurisdiction, status (submitted/pending/overdue), filing_date, next_due_date, instruments_covered[], summary.\n  Agent 6 seeds 8-10 realistic records.\n", status: done}
- {id: a5-p9-quarantine-legacy-state-store, content: "- [x] [AGENT] P0. Remove or quarantine legacy `unified_trading_api/mock_data/state_store.py` (68 lines, in-memory only). Agent 5 migrated to UTL `MockStateStore` (a5-p2-use-utl-store) but the old file still exists in the repo. Either:\n  1. DELETE the file if nothing imports it (grep for `from .state_store import` and `from unified_trading_api.mock_data.state_store import`)\n  2. If something still imports it, update those imports to use UTL MockStateStore, THEN delete\n  3. Verify `POST /admin/reset` still works after removal\n  This is the last piece of technical debt from the migration.\n", status: todo}
- {id: a5-p9-readiness-upstream-probes, content: "- [x] [AGENT] P1. Finish readiness upstream probes if Tier 2 / ops UX is required. Currently `GET /readiness` returns `upstream_checks: []` (empty). For Tier 2 operations:\n  1. Add actual probe logic for configured upstream services (check env vars like `LIVE_SERVICE_*` URLs)\n  2. If upstream URL configured but unreachable, add to `degraded_reasons[]`\n  3. Set `effective_runtime_tier < declared_runtime_tier` when upstream missing\n  4. This is optional for Tier 1 (mock-only) but required before Tier 2 deployment\n", status: todo}
isProject: false
---

# Notes & Context

## CRITICAL: Read Before Any Work

1. Read `unified-trading-pm/plans/archive/CITADEL_VISION_2026_03_22.md` — system-wide vision
2. Read `unified-trading-system-ui/UI_STRUCTURE_MANIFEST.json` — see `pages_needing_api_wiring` (18 pages) and
   per-service API endpoint requirements
3. The UI has 18 REAL pages using inline mock data that need API wiring. Your service layer must serve ALL endpoints
   those pages expect.

## 3-API Architecture

- `auth-api` (port 8200) — stays separate, handles SSO/tokens
- `client-reporting-api` (port 8014) — stays separate, handles client reports/invoices
- `unified-trading-api` (port 8030) — YOUR scope. Absorbs 8 domain APIs. Routes reporting/\* to client-reporting-api in
  real mode.

## Runtime tiers (read CITADEL_VISION)

- **Tier 0:** UI-only; no HTTP to `:8030`; in-browser store + optional cloud-fetched reference data; must track
  OpenAPI + mock service semantics.
- **Tier 1 (this plan):** Gateway + `MockDomainService` / `LiveDomainService`; minimal cross-service HTTP; curl is the
  curl test SSOT.
- **Tier 2:** Full microservice fleet; gateway calls services at **configured URLs** — **localhost** (sibling clones on
  the same machine) or **remote** (staging/cloud); same code path. Services may use `mock_mode` / testnet; topology
  matches prod, adapters differ.

**LiveDomainService target modes:** Co-located fleet (env → localhost ports from `setup-workspace`-style clones) vs
networked fleet (env → remote base URLs). See CITADEL_VISION § **Gateway → downstream target modes** and **Local dev
mesh**.

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

- **Default:** the UI calls the real `unified-trading-api` (port 8030). The API handles mock/real internally via the
  service layer. ALL endpoints must return realistic data in mock mode on the gateway.
- **Tier 0 exception (SSOT: CITADEL_VISION § Runtime convergence tiers):** when the gateway is unavailable or not yet
  implemented, the UI may use an **in-browser mock** that implements the **same OpenAPI** operations — no ad-hoc MSW
  payloads that diverge from `MockDomainService`. This agent owns **Tier 1** truth; UI agents own Tier 0 alignment via
  codegen + shared fixtures.

## Risk Factors & Mitigations (HIGHEST RISK AGENT)

**RISK 1 (CRITICAL): Scope is enormous — this agent has 25+ todos across 7 phases.** Service layer + WebSocket + auth +
reporting proxy + persistence + dev stack + tests. Agent may run out of context window or lose coherence mid-execution.
MITIGATION: Execute in STRICT phase order. Complete Phase 0 (service interfaces) → Phase 1 (refactor routes) → Phase 2
(MockStateStore migration) → Phase 3 (seed enrichment) → Phase 4 (WebSocket + candles + auth) → Phase 5 (tests) → Phase
6 (PDF + codegen). Do NOT jump ahead. If context runs out, the earlier phases (service layer, MockStateStore) are more
important than later ones (PDF, codegen).

**RISK 2: Service layer already exists — don't rebuild it.** Current state baseline says services/ EXISTS with
DomainService Protocol, MockDomainService, factory.py. All 19 routes already use service layer DI. MITIGATION: Read
services/ directory FIRST. If the pattern matches the plan, SKIP Phase 0 and Phase 1. Focus on the gaps (MockStateStore
migration, new endpoints, auth, persistence).

**RISK 3: WebSocket already has 4,859 lines — don't break what works.** The existing WebSocket has channel-based
multiplexing and synthetic tick generator. MITIGATION: Read routes/websocket.py FIRST. Verify tick generation matches
CITADEL_VISION § Interface Contracts. If format differs, update the contract in CITADEL_VISION (since the server is
already built) and notify Agent 2 to adapt. Don't rewrite 4,859 lines.

**RISK 4: MockStateStore migration may break existing seed.py.** seed.py is 1,323 lines. Switching from the simple
68-line store to UTL's MockStateStore changes the API for seeding (different method signatures, different storage
format). MITIGATION: Create a migration wrapper. Keep the seed() function signature the same. Internally, translate
calls from the old API to UTL MockStateStore API. Run seed.py after migration and verify all domains are populated. Do
NOT rewrite seed.py — Agent 6 owns seed data content.

**RISK 5: Collection naming mismatch between Agent 5 and Agent 6.** If Agent 5 reads from `positions_live` but Agent 6
seeds into `positions`, data is invisible. MITIGATION: Use EXACT collection names from CITADEL_VISION § Interface
Contracts. Both agents must read that section. Agent 5 must NOT invent new collection names.

**RISK 6: Auth-api JWT format may not match expectations.** auth-api issues JWTs with specific claims. If
unified-trading-api expects different claim names (e.g., `org_id` vs `organization_id`), auth breaks silently.
MITIGATION: Read auth-api/auth_api/app.py to find JWT payload structure. Match claim names exactly in
`get_current_user()` dependency. Add a test that decodes an auth-api JWT and verifies claim names.

**RISK 7: Reporting proxy adds httpx dependency and async complexity.** httpx AsyncClient needs proper lifecycle
management (startup/shutdown). MITIGATION: Create httpx client in FastAPI lifespan handler. Store on app.state. Close on
shutdown. Use existing pattern from any other service that makes outbound HTTP calls.

## Separation of Concerns (CRITICAL — read CITADEL_VISION § Separation of Concerns)

**The curl test:** If a feature can't be demonstrated via `curl` or `wscat` against the API alone, the logic is in the
wrong layer. PnL recalculation, org filtering, batch/live switching — all MUST work at the API level before the UI
touches it.

**No two sources of truth:** The UI's `lib/trading-data.ts` and `lib/strategy-registry.ts` contain client-side mock data
that duplicates what the API should return. After Agent 5 + Agent 6 are done, these client-side data sources MUST be
replaceable by API calls. Agent 6 handles the removal (Phase 4), but Agent 5 must ensure the API serves equivalent data.

**Missing service functionality:** MockDomainService simulates what real services would return. If a feature needs
server-side logic (PnL recalculation, alert severity escalation, strategy config validation), implement it in
MockDomainService with the SAME interface that LiveDomainService would use. This way, when LiveDomainService is wired to
real microservices (Phase 9, post-sprint), the mock path has already validated the interface.

## New scope (added 2026-03-22 gap analysis + amendments)

- WebSocket mock tick generator is now P0 (was P2) — critical for demo feel
- OHLCV candle and order book endpoints are new P0 requirements
- Reporting routes proxy to client-reporting-api (port 8014) in real mode
- Auth-api JWT validation and persona extraction
- Live data persistence to .local-dev-cache/ via MockStateStore JSONL
- Batch/live collection separation: `{domain}_live` vs `{domain}_batch`
- auth-api must be added to dev-start.sh and ui-api-mapping.json
- **Real-time PnL recalculation (Amendment 3):** Server-side position PnL update on each tick batch, with WebSocket
  emission on positions + analytics channels. This is what makes the dashboard come alive.
- **Full instrument coverage (Amendment 1):** ALL endpoints import from UAC representative_sample.py — no hardcoded
  instrument lists
- **Strategy config API (Amendment 2):** New `GET /analytics/strategy-configs` endpoint serving 50+ strategy configs
  from expanded seed registry
- **Phase 7 added:** Full registry coverage, strategy config API, real-time PnL test
- **Phase 8 added (Gap Classification):** Pre-trade compliance check simulation, derivatives/options endpoints, risk
  analytics (VaR/stress/correlation), FX conversion, regulatory reports. READ
  `.cursor/plans/archive/GAP_CLASSIFICATION_2026_03_22.md` for the 3-category framework. Every Phase 8 todo identifies its gap
  category (Type 1/2/3) and points to the REAL service implementation it's replicating. DO NOT rebuild service logic —
  simulate output shapes from seeded data.
