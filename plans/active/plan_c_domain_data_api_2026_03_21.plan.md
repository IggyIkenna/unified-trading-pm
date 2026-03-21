---
name: plan-c-domain-data-api
overview:
  Wire the unified-trading-system-ui to real backend APIs via BFF pattern, delete 7,100 lines of inline mock data, add
  WebSocket real-time push for market data / positions / alerts, and align MSW handlers to BFF paths.
type: code
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-21

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none
    readiness_note: "Primary target — BFF routes, hook rewire, mock deletion, WebSocket client."
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
    readiness_note: "WebSocket server utilities if shared across APIs."
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
    readiness_note: "OpenAPI spec completeness — execution-results-api missing."
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: config-api
    code: C0
    deployment: none
    business: none
  - repo: execution-results-api
    code: C0
    deployment: none
    business: none
    readiness_note: "Missing from OpenAPI spec; serves 3 UIs."
  - repo: trading-analytics-api
    code: C0
    deployment: none
    business: none
  - repo: batch-audit-api
    code: C0
    deployment: none
    business: none
  - repo: client-reporting-api
    code: C0
    deployment: none
    business: none
  - repo: ml-training-api
    code: C0
    deployment: none
    business: none
  - repo: ml-inference-api
    code: C0
    deployment: none
    business: none
  - repo: market-data-api
    code: C0
    deployment: none
    business: none
  - repo: alerting-service
    code: C0
    deployment: none
    business: none
    readiness_note: "WebSocket alert push source."
  - repo: execution-service
    code: C0
    deployment: none
    business: none
    readiness_note: "Kill switch endpoint must be sub-second via WebSocket."

depends_on:
  - registry-completeness-implementation-detail

todos:
  # ── Phase 0: BFF Scaffold ──
  - id: p0-bff-scaffold
    content: |
      - [ ] [AGENT] P0. Scaffold BFF layer in unified-trading-system-ui — Next.js API route directory (app/api/), server-side HTTP client with retry/timeout, auth token forwarding from session, error normalization (backend errors -> standard UI error shape).
    status: todo
  - id: p0-service-registry
    content: |
      - [ ] [AGENT] P0. Create BFF service registry — map domain names to backend URLs using port registry from unified-trading-pm/scripts/dev/ui-api-mapping.json. Support env-based override (NEXT_PUBLIC_API_BASE_URL).
    status: todo
  - id: p0-qg-scaffold
    content: |
      - [ ] [SCRIPT] P0. QG gate: run `cd unified-trading-system-ui && CI=true npm test -- --run` — BFF scaffold passes.
    status: todo

  # ── Phase 1: BFF Routes (PARALLEL — 14 domain catch-all routes) ──
  - id: p1-bff-deployment
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/deployment/[...path] — proxy to deployment-api (port 8004). Handles: deploy, status, rollback, shard management.
    status: todo
  - id: p1-bff-config
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/config/[...path] — proxy to config-api (port 8006). Handles: config CRUD, publish, history.
    status: todo
  - id: p1-bff-execution-results
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/execution-results/[...path] — proxy to execution-results-api (port 8008). Handles: backtest results, analysis, config generation.
    status: todo
  - id: p1-bff-trading-analytics
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/trading-analytics/[...path] — proxy to trading-analytics-api (port 8010). Handles: PnL, positions, risk metrics.
    status: todo
  - id: p1-bff-batch-audit
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/batch-audit/[...path] — proxy to batch-audit-api (port 8012). Handles: batch run status, audit logs.
    status: todo
  - id: p1-bff-client-reporting
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/client-reporting/[...path] — proxy to client-reporting-api (port 8014). Handles: reports, exports.
    status: todo
  - id: p1-bff-ml-training
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/ml-training/[...path] — proxy to ml-training-api. Handles: experiments, training runs, model registry.
    status: todo
  - id: p1-bff-ml-inference
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/ml-inference/[...path] — proxy to ml-inference-api. Handles: predictions, model status.
    status: todo
  - id: p1-bff-market-data
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/market-data/[...path] — proxy to market-data-api. Handles: OHLCV, trades, orderbook snapshots.
    status: todo
  - id: p1-bff-alerting
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/alerting/[...path] — proxy to alerting-service HTTP endpoint. Handles: alert rules, alert history, acknowledge.
    status: todo
  - id: p1-bff-execution
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/execution/[...path] — proxy to execution-service HTTP endpoint. Handles: orders, fills, kill switch.
    status: todo
  - id: p1-bff-risk
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/risk/[...path] — proxy to risk-management-service HTTP endpoint. Handles: risk metrics, limits, breaches.
    status: todo
  - id: p1-bff-positions
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/positions/[...path] — proxy to position-balance-monitor-service HTTP endpoint. Handles: positions, balances, reconciliation.
    status: todo
  - id: p1-bff-instruments
    content: |
      - [ ] [AGENT] P1. Add BFF route /api/instruments/[...path] — proxy to instruments-service HTTP endpoint. Handles: instrument catalogue, venue mappings.
    status: todo

  # ── Phase 2: Hook Rewire (PARALLEL with Phase 1) ──
  - id: p2-rewire-hooks
    content: |
      - [ ] [AGENT] P1. Update all 14 React Query hooks in hooks/api/ to call BFF routes (/api/{domain}/...) instead of direct service URLs. Remove port-based URLs. Ensure queryKey includes domain prefix for cache isolation.
    status: todo
  - id: p2-add-missing-hooks
    content: |
      - [ ] [AGENT] P1. Add missing React Query hooks for domains not yet covered — instruments, risk, positions, market-data, ML inference. Follow existing hook patterns (useQuery/useMutation, error handling, loading states).
    status: todo
  - id: p2-qg-hooks
    content: |
      - [ ] [SCRIPT] P1. QG gate: run `cd unified-trading-system-ui && CI=true npm test -- --run` — all hooks pass with MSW intercepting BFF routes.
    status: todo

  # ── Phase 3: Delete Inline Mocks (SEQUENTIAL — after Phases 1+2) ──
  - id: p3-delete-inline-mocks
    content: |
      - [ ] [AGENT] P0. Delete all inline mock data files (7,100 lines) — remove mock-data/, lib/mock/, and any inline mock objects in page components. Identify all 68 pages importing mock data.
    status: todo
  - id: p3-rewire-pages-wave1
    content: |
      - [ ] [AGENT] P0. Rewire Wave 1 pages (dashboard, trading, positions, risk, alerts) — replace mock imports with React Query hooks. These are the most-used pages.
    status: todo
  - id: p3-rewire-pages-wave2
    content: |
      - [ ] [AGENT] P1. Rewire Wave 2 pages (strategies, ML training/inference, reports, PnL) — replace mock imports with React Query hooks.
    status: todo
  - id: p3-rewire-pages-wave3
    content: |
      - [ ] [AGENT] P2. Rewire Wave 3 pages (backtest, portal, admin, config, deployment) — replace mock imports with React Query hooks.
    status: todo
  - id: p3-qg-no-mocks
    content: |
      - [ ] [SCRIPT] P0. QG gate: grep for mock data imports — zero remaining inline mock imports across all pages. Run `cd unified-trading-system-ui && CI=true npm test -- --run`.
    status: todo

  # ── Phase 4: WebSocket Server ──
  - id: p4-ws-server
    content: |
      - [ ] [AGENT] P0. Add WebSocket server endpoint /api/ws in unified-trading-system-ui BFF — channel multiplexing (market-data, positions, alerts, execution, risk), PubSub subscription on server side, JSON message framing with channel + payload.
    status: todo
  - id: p4-ws-auth
    content: |
      - [ ] [AGENT] P0. Add WebSocket auth — validate session token on connection upgrade, reject unauthorized. Support DISABLE_AUTH=true for local dev.
    status: todo
  - id: p4-ws-channels
    content: |
      - [ ] [AGENT] P1. Implement channel handlers — market-data (subscribe to instruments, receive OHLCV/trades/orderbook), positions (balance updates), alerts (new/resolved), execution (fill confirmations, kill switch ack), risk (threshold breaches).
    status: todo
  - id: p4-ws-heartbeat
    content: |
      - [ ] [AGENT] P1. Add WebSocket heartbeat + reconnection — server sends ping every 30s, client auto-reconnects with exponential backoff, re-subscribes to channels on reconnect.
    status: todo
  - id: p4-qg-ws-server
    content: |
      - [ ] [SCRIPT] P1. QG gate: WebSocket server tests pass — connection, auth, channel subscribe/unsubscribe, heartbeat, reconnection.
    status: todo

  # ── Phase 5: WebSocket Client Hooks ──
  - id: p5-ws-provider
    content: |
      - [ ] [AGENT] P0. Build WebSocketProvider React context — single connection per session, channel subscription API, auto-reconnect, connection status indicator.
    status: todo
  - id: p5-use-market-data
    content: |
      - [ ] [AGENT] P1. Build useMarketData hook — subscribe to market-data channel with instrument filter, return latest tick/OHLCV, integrate with React Query cache for seamless REST+WS.
    status: todo
  - id: p5-use-alerts
    content: |
      - [ ] [AGENT] P1. Build useAlerts hook — subscribe to alerts channel, return live alert feed, toast notifications for critical alerts.
    status: todo
  - id: p5-use-positions
    content: |
      - [ ] [AGENT] P1. Build usePositions hook — subscribe to positions channel, return live position/balance updates, merge with REST query cache.
    status: todo
  - id: p5-use-execution
    content: |
      - [ ] [AGENT] P1. Build useExecution hook — subscribe to execution channel, return fill confirmations, kill switch status. Sub-second feedback for trade actions.
    status: todo
  - id: p5-use-risk
    content: |
      - [ ] [AGENT] P1. Build useRisk hook — subscribe to risk channel, return threshold breach alerts, live VaR/drawdown updates.
    status: todo
  - id: p5-wire-pages
    content: |
      - [ ] [AGENT] P1. Wire WebSocket hooks to pages — dashboard (market data + positions + alerts), trading (execution + market data), risk (risk + positions), alerts (alerts).
    status: todo
  - id: p5-qg-ws-client
    content: |
      - [ ] [SCRIPT] P1. QG gate: run `cd unified-trading-system-ui && CI=true npm test -- --run` — all WebSocket hooks pass with mock WS server.
    status: todo

  # ── Phase 6: MSW Alignment ──
  - id: p6-msw-bff-paths
    content: |
      - [ ] [AGENT] P1. Update all MSW handlers to intercept BFF paths (/api/{domain}/...) instead of direct service URLs. Remove duplicate handlers. Use generated types from OpenAPI codegen.
    status: todo
  - id: p6-msw-ws-mock
    content: |
      - [ ] [AGENT] P2. Add MSW WebSocket mock handler — mock WS server for tests, simulate channel messages (market ticks, alert push, fill confirmations).
    status: todo
  - id: p6-qg-msw
    content: |
      - [ ] [SCRIPT] P1. QG gate: run full test suite with MSW — all pages render in mock mode with BFF-path MSW handlers.
    status: todo

  # ── Phase 7: Page Migration Waves ──
  - id: p7-wave1-dashboard-trading
    content: |
      - [ ] [AGENT] P0. Wave 1 migration — dashboard, trading, positions, risk, alerts pages: fully wired to BFF + WebSocket, zero inline mocks, MSW handlers aligned. These 5 page groups are the critical path.
    status: todo
  - id: p7-wave2-strategy-ml
    content: |
      - [ ] [AGENT] P1. Wave 2 migration — strategies, ML training, ML inference, reports, PnL attribution pages: fully wired to BFF, REST-only (no WebSocket needed for historical data).
    status: todo
  - id: p7-wave3-backtest-admin
    content: |
      - [ ] [AGENT] P2. Wave 3 migration — backtest, portal, admin, config, deployment pages: fully wired to BFF, config pages integrate with Plan B config CRUD.
    status: todo
  - id: p7-qg-final
    content: |
      - [ ] [SCRIPT] P0. QG gate: full suite — `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` succeeds, `CI=true npm test -- --run` passes, zero inline mock imports, all 151 pages render.
    status: todo

isProject: false
---

# Plan C: Domain Data API + BFF + Real-Time

## Context

UI research findings (2026-03-21):

- **151 pages**, 0% real backend connectivity
- **7,100 lines** inline mock data across 68 pages
- **14 React Query hooks** exist but only 3 pages use them
- Hooks hit `/api/*` but real services are at `/{service}/api/*` — URL mismatch
- **No WebSocket/SSE** — only polling at 2-10s intervals
- **MSW exists** but only 16 handlers, not aligned with actual API paths
- **541 orphan domain models** in backend not exposed via API

## Execution DAG

```
Phase 0 (BFF scaffold)
    |
    +---> Phase 1 (14 BFF routes) ──────────┐
    |         [PARALLEL]                     |
    +---> Phase 2 (hook rewire) ─────────────+
              [PARALLEL with Phase 1]        |
                                             v  [QG gate]
                                        Phase 3 (delete inline mocks)
                                             |   [SEQUENTIAL]
                                             v  [QG gate]
                              +--------------+---------------+
                              |                              |
                         Phase 4                        Phase 6
                      (WS server)                    (MSW alignment)
                              |                        [PARALLEL]
                              v
                         Phase 5
                      (WS client hooks)
                              |
                              v  [QG gate]
                         Phase 7
                    (page migration waves)
                              |
                              v  [QG gate]
                            DONE
```

## Communication Model Decision

| Data Type                          | Transport         | Latency Target | Rationale                                |
| ---------------------------------- | ----------------- | -------------- | ---------------------------------------- |
| Kill switch / trade execution      | WebSocket         | < 500ms        | Sub-second feedback critical for risk    |
| Live market data                   | WebSocket         | 1-5s           | Continuous stream, polling too expensive |
| Position / balance updates         | WebSocket         | 1-5s           | Must reflect fills immediately           |
| Alert notifications                | WebSocket         | 1-5s           | Real-time push, toast notifications      |
| Risk threshold breaches            | WebSocket         | 1-5s           | Urgent, must not wait for poll cycle     |
| Historical data / backtest results | REST via BFF      | N/A            | Request-response, no streaming needed    |
| Reports / exports                  | REST via BFF      | N/A            | Batch data, download pattern             |
| Config changes                     | REST + hot-reload | N/A            | See Plan B for config lifecycle          |

## BFF Route Registry

| BFF Path                | Backend Service          | Port | Key Endpoints            |
| ----------------------- | ------------------------ | ---- | ------------------------ |
| /api/deployment/        | deployment-api           | 8004 | deploy, status, rollback |
| /api/config/            | config-api               | 8006 | CRUD, publish, history   |
| /api/execution-results/ | execution-results-api    | 8008 | backtest, analysis       |
| /api/trading-analytics/ | trading-analytics-api    | 8010 | PnL, positions, risk     |
| /api/batch-audit/       | batch-audit-api          | 8012 | batch status, audit      |
| /api/client-reporting/  | client-reporting-api     | 8014 | reports, exports         |
| /api/ml-training/       | ml-training-api          | TBD  | experiments, models      |
| /api/ml-inference/      | ml-inference-api         | TBD  | predictions, status      |
| /api/market-data/       | market-data-api          | TBD  | OHLCV, trades, book      |
| /api/alerting/          | alerting-service         | TBD  | rules, history, ack      |
| /api/execution/         | execution-service        | TBD  | orders, fills, kill      |
| /api/risk/              | risk-management-service  | TBD  | metrics, limits          |
| /api/positions/         | position-balance-monitor | TBD  | positions, balances      |
| /api/instruments/       | instruments-service      | TBD  | catalogue, mappings      |

Port SSOT: `unified-trading-pm/scripts/dev/ui-api-mapping.json`

## Mock Mode Architecture (Post-Migration)

```
                    NEXT_PUBLIC_MOCK_API=true           NEXT_PUBLIC_MOCK_API=false
                           |                                    |
                    MSW intercepts                        BFF API routes
                    /api/{domain}/*                       /api/{domain}/*
                           |                                    |
                    Mock handlers                     Backend services
                    (generated types)                  (DATA_MODE=mock or real)
```

Single code path for both modes. Mock/real switch is env vars only — no conditional imports in pages.

## Success Criteria

| Phase | Gate | Criteria                                                           |
| ----- | ---- | ------------------------------------------------------------------ |
| 0     | C3   | BFF scaffold, service registry, auth forwarding                    |
| 1     | C3   | All 14 BFF routes proxy correctly, integration tests               |
| 2     | C3   | All hooks rewired to BFF paths, React Query tests pass             |
| 3     | C4   | Zero inline mock imports, all pages use hooks, 7,100 lines deleted |
| 4     | C4   | WebSocket server with 5 channels, auth, heartbeat, reconnection    |
| 5     | C4   | 5 WebSocket client hooks, wired to dashboard/trading/risk/alerts   |
| 6     | C3   | MSW handlers match BFF paths, use generated types                  |
| 7     | C5   | All 151 pages render, full test suite green, vite build succeeds   |
