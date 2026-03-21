---
name: plan-e-ui-backend-integration
overview:
  UI integration with backend APIs. BFF scaffold + routes, React Query hook rewire, inline mock deletion, WebSocket
  server/client, MSW alignment, hand-written TS type replacement with generated types, UI config CRUD, UI scenario
  panel, external testnet deployment, and page migration waves.
type: code
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-21

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none
    readiness_note: "Primary target — all UI integration work lives here."

depends_on:
  - plan-a-registry-schema-sync
  - plan-b-config-hot-reload
  - plan-c-domain-data-api
  - plan-d-testnet-stress-testing

todos:
  # ── Phase 0: Generated Type Consumption (from Plan A) ──
  - id: p0-generate-ts-constants
    content: |
      - [ ] [AGENT] P0. Generate TypeScript constants from ui-reference-data.json. Create a codegen script (scripts/generate-ts-from-registry.ts or .py) that reads ui-reference-data.json and outputs typed TS constants to src/generated/registry-constants.ts. Each registry becomes a typed const with as const assertion. Output must include JSDoc comments with source repo and version.
    status: todo
  - id: p0-delete-hand-maintained-ts
    content: |
      - [ ] [AGENT] P0. Delete 3,561 lines of hand-maintained TS constants (taxonomy.ts, reference-data.ts, and similar files). Replace all imports across the codebase to use src/generated/registry-constants.ts and src/generated/api-types.ts. Must grep entire UI codebase for old import paths and update every consumer.
    status: todo
    blocked_by: p0-generate-ts-constants
  - id: p0-verify-ui-build
    content: |
      - [ ] [SCRIPT] P0. Verify UI builds cleanly after type replacement: cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build — must succeed with zero type errors. Also run: CI=true npm test -- --run.
    status: todo
    blocked_by: p0-delete-hand-maintained-ts

  # ── Phase 1: BFF Scaffold (SEQUENTIAL after Phase 0) ──
  - id: p1-bff-scaffold
    content: |
      - [ ] [AGENT] P0. Scaffold BFF layer in unified-trading-system-ui — Next.js API route directory (app/api/), server-side HTTP client with retry/timeout, auth token forwarding from session, error normalization (backend errors -> standard UI error shape).
    status: todo
    blocked_by: p0-verify-ui-build
  - id: p1-service-registry
    content: |
      - [ ] [AGENT] P0. Create BFF service registry — map domain names to backend URLs using port registry from unified-trading-pm/scripts/dev/ui-api-mapping.json. Support env-based override (NEXT_PUBLIC_API_BASE_URL).
    status: todo
    blocked_by: p0-verify-ui-build
  - id: p1-qg-scaffold
    content: |
      - [ ] [SCRIPT] P0. QG gate: run `cd unified-trading-system-ui && CI=true npm test -- --run` — BFF scaffold passes.
    status: todo
    blocked_by: p1-bff-scaffold

  # ── Phase 2: BFF Routes + Hook Rewire (PARALLEL) ──
  - id: p2-bff-deployment
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/deployment/[...path] — proxy to deployment-api (port 8004). Handles: deploy, status, rollback, shard management.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-config
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/config/[...path] — proxy to config-api (port 8006). Handles: config CRUD, publish, history.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-execution-results
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/execution-results/[...path] — proxy to execution-results-api (port 8008). Handles: backtest results, analysis, config generation.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-trading-analytics
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/trading-analytics/[...path] — proxy to trading-analytics-api (port 8010). Handles: PnL, positions, risk metrics.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-batch-audit
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/batch-audit/[...path] — proxy to batch-audit-api (port 8012). Handles: batch run status, audit logs.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-client-reporting
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/client-reporting/[...path] — proxy to client-reporting-api (port 8014). Handles: reports, exports.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-ml-training
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/ml-training/[...path] — proxy to ml-training-api. Handles: experiments, training runs, model registry.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-ml-inference
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/ml-inference/[...path] — proxy to ml-inference-api. Handles: predictions, model status.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-market-data
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/market-data/[...path] — proxy to market-data-api. Handles: OHLCV, trades, orderbook snapshots.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-alerting
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/alerting/[...path] — proxy to alerting-service HTTP endpoint. Handles: alert rules, alert history, acknowledge.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-execution
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/execution/[...path] — proxy to execution-service HTTP endpoint. Handles: orders, fills, kill switch.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-risk
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/risk/[...path] — proxy to risk-management-service HTTP endpoint. Handles: risk metrics, limits, breaches.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-positions
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/positions/[...path] — proxy to position-balance-monitor-service HTTP endpoint. Handles: positions, balances, reconciliation.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-bff-instruments
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/instruments/[...path] — proxy to instruments-service HTTP endpoint. Handles: instrument catalogue, venue mappings.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-rewire-hooks
    content: |
      - [ ] [AGENT] P1. Update all 14 React Query hooks in hooks/api/ to call BFF routes (/api/{domain}/...) instead of direct service URLs. Remove port-based URLs. Ensure queryKey includes domain prefix for cache isolation.
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-add-missing-hooks
    content: |
      - [ ] [AGENT] P1. Add missing React Query hooks for domains not yet covered — instruments, risk, positions, market-data, ML inference. Follow existing hook patterns (useQuery/useMutation, error handling, loading states).
    status: todo
    blocked_by: p1-qg-scaffold
  - id: p2-qg-routes-hooks
    content: |
      - [ ] [SCRIPT] P1. QG gate: run `cd unified-trading-system-ui && CI=true npm test -- --run` — all BFF routes and hooks pass with MSW intercepting BFF paths.
    status: todo
    blocked_by: p2-rewire-hooks

  # ── Phase 3: Delete Inline Mocks + MSW Alignment (SEQUENTIAL after Phase 2) ──
  - id: p3-delete-inline-mocks
    content: |
      - [ ] [AGENT] P0. Delete all inline mock data files (7,100 lines) — remove mock-data/, lib/mock/, and any inline mock objects in page components. Identify all 68 pages importing mock data.
    status: todo
    blocked_by: p2-qg-routes-hooks
  - id: p3-msw-bff-paths
    content: |
      - [ ] [AGENT] P1. Update all MSW handlers to intercept BFF paths (/api/{domain}/...) instead of direct service URLs. Remove duplicate handlers. Use generated types from OpenAPI codegen.
    status: todo
    blocked_by: p2-qg-routes-hooks
  - id: p3-msw-ws-mock
    content: |
      - [ ] [AGENT] P2. Add MSW WebSocket mock handler — mock WS server for tests, simulate channel messages (market ticks, alert push, fill confirmations).
    status: todo
    blocked_by: p3-msw-bff-paths
  - id: p3-qg-mocks
    content: |
      - [ ] [SCRIPT] P0. QG gate: grep for mock data imports — zero remaining inline mock imports. Run `cd unified-trading-system-ui && CI=true npm test -- --run`.
    status: todo
    blocked_by: p3-delete-inline-mocks

  # ── Phase 4: WebSocket Server + Client (SEQUENTIAL after Phase 3) ──
  - id: p4-ws-server
    content: |
      - [ ] [AGENT] P0. Add WebSocket server endpoint /api/ws in unified-trading-system-ui BFF — channel multiplexing (market-data, positions, alerts, execution, risk), PubSub subscription on server side, JSON message framing with channel + payload.
    status: todo
    blocked_by: p3-qg-mocks
  - id: p4-ws-auth
    content: |
      - [ ] [AGENT] P0. Add WebSocket auth — validate session token on connection upgrade, reject unauthorized. Support DISABLE_AUTH=true for local dev.
    status: todo
    blocked_by: p3-qg-mocks
  - id: p4-ws-channels
    content: |
      - [ ] [AGENT] P1. Implement channel handlers — market-data (subscribe to instruments, receive OHLCV/trades/orderbook), positions (balance updates), alerts (new/resolved), execution (fill confirmations, kill switch ack), risk (threshold breaches).
    status: todo
    blocked_by: p4-ws-server
  - id: p4-ws-heartbeat
    content: |
      - [ ] [AGENT] P1. Add WebSocket heartbeat + reconnection — server sends ping every 30s, client auto-reconnects with exponential backoff, re-subscribes to channels on reconnect.
    status: todo
    blocked_by: p4-ws-server
  - id: p4-ws-provider
    content: |
      - [ ] [AGENT] P0. Build WebSocketProvider React context — single connection per session, channel subscription API, auto-reconnect, connection status indicator.
    status: todo
    blocked_by: p4-ws-server
  - id: p4-use-market-data
    content: |
      - [ ] [AGENT] P1. Build useMarketData hook — subscribe to market-data channel with instrument filter, return latest tick/OHLCV, integrate with React Query cache for seamless REST+WS.
    status: todo
    blocked_by: p4-ws-provider
  - id: p4-use-alerts
    content: |
      - [ ] [AGENT] P1. Build useAlerts hook — subscribe to alerts channel, return live alert feed, toast notifications for critical alerts.
    status: todo
    blocked_by: p4-ws-provider
  - id: p4-use-positions
    content: |
      - [ ] [AGENT] P1. Build usePositions hook — subscribe to positions channel, return live position/balance updates, merge with REST query cache.
    status: todo
    blocked_by: p4-ws-provider
  - id: p4-use-execution
    content: |
      - [ ] [AGENT] P1. Build useExecution hook — subscribe to execution channel, return fill confirmations, kill switch status. Sub-second feedback for trade actions.
    status: todo
    blocked_by: p4-ws-provider
  - id: p4-use-risk
    content: |
      - [ ] [AGENT] P1. Build useRisk hook — subscribe to risk channel, return threshold breach alerts, live VaR/drawdown updates.
    status: todo
    blocked_by: p4-ws-provider
  - id: p4-qg-ws
    content: |
      - [ ] [SCRIPT] P1. QG gate: WebSocket server + client tests pass — connection, auth, channel subscribe/unsubscribe, heartbeat, reconnection, all hooks pass with mock WS server.
    status: todo
    blocked_by: p4-ws-heartbeat

  # ── Phase 5: UI Config CRUD (from Plan B) ──
  - id: p5-bff-config-routes
    content: |
      - [ ] [AGENT] P1. Add BFF routes for config CRUD — GET /api/config/{domain}, PUT /api/config/{domain}, POST /api/config/{domain}/publish. Proxy to config-api.
    status: todo
    blocked_by: p2-qg-routes-hooks
  - id: p5-config-editor-page
    content: |
      - [ ] [AGENT] P1. Build config editor page in unified-trading-system-ui — domain selector, JSON/YAML editor with schema validation, diff view, publish button with confirmation dialog.
    status: todo
    blocked_by: p5-bff-config-routes
  - id: p5-config-history
    content: |
      - [ ] [AGENT] P2. Add config version history panel — show last N config changes per domain with timestamp, user, diff. Read from config-api GET /config/{domain}/history.
    status: todo
    blocked_by: p5-config-editor-page
  - id: p5-qg-config
    content: |
      - [ ] [SCRIPT] P1. QG gate: run `cd unified-trading-system-ui && CI=true npm test -- --run` — config pages pass vitest.
    status: todo
    blocked_by: p5-config-editor-page

  # ── Phase 6: UI Scenario Panel (from Plan D) ──
  - id: p6-scenario-selector-ui
    content: |
      - [ ] [AGENT] P0. Add scenario selector dropdown to admin/devops page. Dropdown lists all MockScenario values (NORMAL, HEAVY, LIGHT, BIG_RANGES, BUST, NO_SYSTEM_OVERLOAD, MISSING_DATA, DELAYED_DATA, BAD_SCHEMA, ERROR_STORM, FLASH_CRASH, HIGH_LATENCY). Selection calls POST /api/v1/scenarios/activate via BFF. Only visible when VITE_MOCK_API=true.
    status: todo
    blocked_by: p2-qg-routes-hooks
  - id: p6-scenario-status-indicator
    content: |
      - [ ] [AGENT] P0. Add current scenario indicator to UI header/status bar. Shows active scenario name + seed number. Color-coded: NORMAL=green, BUST/FLASH_CRASH=red, ERROR_STORM=orange, others=yellow. Updates via WebSocket when scenario changes.
    status: todo
    blocked_by: p4-qg-ws
  - id: p6-scenario-realtime-switch
    content: |
      - [ ] [AGENT] P1. Real-time scenario switching without page reload. When scenario changes via dropdown, WebSocket pushes new scenario to all connected clients. SyntheticDataGenerator adjusts tick patterns immediately. UI components react to scenario change event.
    status: todo
    blocked_by: p6-scenario-status-indicator
  - id: p6-custom-scenario-builder
    content: |
      - [ ] [AGENT] P2. Add custom scenario builder modal on admin page. Adjustable parameters: volatility multiplier (0.1x-10x), volume multiplier (0.1x-10x), missing data rate (0-50%), error injection rate (0-100%), instrument count (45-10000), tick frequency (0.1-100 Hz). Saves as custom ScenarioConfig YAML, selectable in dropdown.
    status: todo
    blocked_by: p6-scenario-realtime-switch
  - id: p6-perf-dashboard
    content: |
      - [ ] [AGENT] P2. Add performance trend page to admin section. Shows historical P99 latencies per service from CI runs. Visual regression indicator (green/yellow/red). Data source: performance-baselines.json committed to PM.
    status: todo
    blocked_by: p2-qg-routes-hooks

  # ── Phase 7: External Testnet Deployment (from Plan D) ──
  - id: p7-testnet-deployment-config
    content: |
      - [ ] [HUMAN] P1. Create testnet.odum.io deployment config in deployment-service. Same infrastructure as production but with CLOUD_MOCK_MODE=true, MOCK_SCENARIO=NORMAL, seed=42. Data isolation: separate GCS bucket prefix (testnet-*), separate PubSub topic prefix (testnet-*). Cloud Run services with min-instances=0 (scale to zero when unused).
    status: todo
    blocked_by: p4-qg-ws
  - id: p7-testnet-demo-preset
    content: |
      - [ ] [AGENT] P1. Create demo preset for external users. Read-only access (no POST/PUT/DELETE on execution endpoints). Rate limiting: 60 req/min per IP. No auth required (DISABLE_AUTH=true, VITE_SKIP_AUTH=true). Scenario locked to NORMAL (no scenario switching for external users). Add demo mode detection in BFF: if TESTNET_MODE=demo, enforce read-only.
    status: todo
    blocked_by: p7-testnet-deployment-config
  - id: p7-testnet-monitoring
    content: |
      - [ ] [AGENT] P2. Add testnet-specific monitoring. Track: external user sessions (count, duration), API usage by endpoint, error rates, scenario health. Emit to Prometheus metrics. Add testnet health page at testnet.odum.io/health showing system status, active scenario, data freshness.
    status: todo
    blocked_by: p7-testnet-deployment-config
  - id: p7-testnet-data-refresh
    content: |
      - [ ] [AGENT] P2. Scheduled daily data refresh for testnet. Cron job runs seed_mock_data.py --seed 42 for all services. Ensures testnet data stays fresh (timestamps within 24h) while maintaining determinism. GHA scheduled workflow or Cloud Scheduler.
    status: todo
    blocked_by: p7-testnet-deployment-config

  # ── Phase 8: Page Migration Waves (SEQUENTIAL after all above) ──
  - id: p8-wave1-dashboard-trading
    content: |
      - [ ] [AGENT] P0. Wave 1 migration — dashboard, trading, positions, risk, alerts pages: fully wired to BFF + WebSocket, zero inline mocks, MSW handlers aligned. These 5 page groups are the critical path.
    status: todo
    blocked_by: p4-qg-ws
  - id: p8-wave2-strategy-ml
    content: |
      - [ ] [AGENT] P1. Wave 2 migration — strategies, ML training, ML inference, reports, PnL attribution pages: fully wired to BFF, REST-only (no WebSocket needed for historical data).
    status: todo
    blocked_by: p8-wave1-dashboard-trading
  - id: p8-wave3-backtest-admin
    content: |
      - [ ] [AGENT] P2. Wave 3 migration — backtest, portal, admin, config, deployment pages: fully wired to BFF, config pages integrate with config CRUD from Phase 5.
    status: todo
    blocked_by: p8-wave2-strategy-ml
  - id: p8-qg-final
    content: |
      - [ ] [SCRIPT] P0. QG gate: full suite — `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` succeeds, `CI=true npm test -- --run` passes, zero inline mock imports, all 151 pages render.
    status: todo
    blocked_by: p8-wave3-backtest-admin

isProject: false
---

# Plan E: UI Backend Integration

## Context

This plan consolidates all UI-side work that was extracted from Plans A-D (backend-only) into a single UI integration
plan. It depends on all four backend plans completing first, ensuring that backend APIs, registries, config
infrastructure, and testing infrastructure are ready before UI integration begins.

## Source Mapping

| Phase | Source Plan | What was moved                                                                   |
| ----- | ----------- | -------------------------------------------------------------------------------- |
| 0     | Plan A      | Generate TS constants, delete hand-maintained TS, verify UI build                |
| 1-4   | Plan C      | BFF scaffold, BFF routes, hook rewire, inline mock deletion, WebSocket, MSW      |
| 5     | Plan B      | UI config CRUD (BFF config routes, editor page, history panel)                   |
| 6     | Plan D      | UI scenario panel (selector, status indicator, real-time switch, custom builder) |
| 7     | Plan D      | External testnet deployment (testnet.odum.io, demo preset, monitoring, refresh)  |
| 8     | Plan C      | Page migration waves (3 waves covering all 151 pages)                            |

## Execution DAG

```
Phase 0 (TS type replacement)
    |
    v
Phase 1 (BFF scaffold)
    |
    v
Phase 2 (PARALLEL — 14 BFF routes + hook rewire)
    |
    v  [QG gate]
Phase 3 (delete inline mocks + MSW alignment)
    |
    v  [QG gate]
Phase 4 (WebSocket server + client hooks)    Phase 5 (config CRUD) [PARALLEL]
    |                                             |
    v  [QG gate]                                  v  [QG gate]
Phase 6 (UI scenario panel)                 Phase 7 (testnet deployment)
    |                                             |
    +─────────────────┬───────────────────────────┘
                      v
               Phase 8 (page migration waves)
                      |
                      v  [QG gate]
                    DONE
```

## Success Criteria

| Phase | Gate | Criteria                                                                      |
| ----- | ---- | ----------------------------------------------------------------------------- |
| 0     | C4   | Hand-maintained TS deleted, generated types compile, vite build succeeds      |
| 1     | C3   | BFF scaffold, service registry, auth forwarding                               |
| 2     | C3   | All 14 BFF routes proxy correctly, all hooks rewired to BFF paths             |
| 3     | C4   | Zero inline mock imports, MSW handlers match BFF paths, 7,100 lines deleted   |
| 4     | C4   | WebSocket server with 5 channels + 5 client hooks, auth, heartbeat, reconnect |
| 5     | C4   | Config editor page, BFF config routes, version history panel                  |
| 6     | C4   | Scenario selector, status indicator, real-time switching                      |
| 7     | D3   | testnet.odum.io accessible, demo preset enforces read-only                    |
| 8     | C5   | All 151 pages render, full test suite green, vite build succeeds              |
