---
doc_type: plan
title: plan-e-ui-backend-integration
summary: UI integration with unified-trading-api gateway. TS type generation, proxy config, auth header, React Query hook
  rewire, page migration waves (26 pages with inline mocks), inline mock file deletion, WebSocket client, MSW alignment,
  UI config CRUD, UI scenario panel, and external testnet deployment.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-api, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-21'
type: code
epic: epic-code-completion
locked_by:
locked_since:
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none, readiness_note: Primary target — all UI integration work lives here.}
depends_on: [plan-a-registry-schema-sync, plan-b-config-hot-reload, plan-c-domain-data-api, plan-d-testnet-stress-testing]
todos:
- {id: p0-generate-ts-types, content: '- [x] [AGENT] P0. DONE. `npm run generate:types` outputs `lib/types/api-generated.ts` (3.2K lines from unified-trading-api). `typed-fetch.ts` provides `ApiResponse<P>` utility type.

    ', status: done}
- {id: p0-generate-ts-constants, content: '- [ ] [AGENT] P0. Generate TypeScript constants from ui-reference-data.json. Create a codegen script (scripts/generate-ts-from-registry.ts or .py) that reads ui-reference-data.json and outputs typed TS constants to src/generated/registry-constants.ts. Each registry becomes a typed const with as const assertion. Output must include JSDoc comments with source repo and version.

    ', status: todo}
- {id: p0-delete-hand-maintained-ts, content: '- [ ] [AGENT] P0. Delete 3,561 lines of hand-maintained TS constants (taxonomy.ts, reference-data.ts, and similar files). Replace all imports across the codebase to use src/generated/registry-constants.ts and src/generated/api-types.ts. Must grep entire UI codebase for old import paths and update every consumer.

    ', status: todo, blocked_by: p0-generate-ts-constants}
- {id: p0-verify-ui-build, content: '- [ ] [SCRIPT] P0. Verify UI builds cleanly after type replacement: cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build — must succeed with zero type errors. Also run: CI=true npm test -- --run.

    ', status: todo, blocked_by: p0-delete-hand-maintained-ts}
- {id: p0b-fix-next-config-rewrites, content: '- [x] [AGENT] P0. DONE. next.config.mjs now proxies /api/* to localhost:8030 (unified-trading-api gateway). Single rewrite rule replaces per-service proxy rules. No BFF needed — the gateway IS the aggregation layer.

    ', status: done}
- {id: p0b-fix-auth-header, content: '- [x] [AGENT] P0. DONE. Auth header now uses Authorization: Bearer <token>. Mock persona header removed.

    ', status: done}
- {id: p1-bff-scaffold, content: '- [x] [AGENT] P0. OBSOLETE — No BFF needed. unified-trading-api is the single gateway (port 8030). Next.js /api/* rewrite proxies directly to it. All 62 endpoints accessible through one gateway.

    ', status: done}
- {id: p1-service-registry, content: '- [x] [AGENT] P0. OBSOLETE — No BFF service registry needed. Single gateway URL replaces per-service port mapping.

    ', status: done}
- {id: p1-qg-scaffold, content: '- [x] [SCRIPT] P0. OBSOLETE — BFF scaffold not needed, gate not applicable.

    ', status: done}
- {id: p2-bff-routes-obsolete, content: '- [x] [AGENT] P1. OBSOLETE — All 14 BFF routes replaced by single Next.js rewrite rule: /api/:path* -> localhost:8030/:path*. unified-trading-api gateway handles all domain routing internally. Individual route items (deployment, config, execution-results, trading-analytics, batch-audit, client-reporting, ml-training, ml-inference, market-data, alerting, execution, risk, positions, instruments) are all subsumed.

    ', status: done}
- {id: p2-hooks-done, content: '- [x] [AGENT] P1. DONE. 3 hooks wired with typed responses: usePositions, useAlerts, useRisk. These use generated types and call the gateway API.

    ', status: done}
- {id: p2-rewire-remaining-hooks, content: '- [ ] [AGENT] P1. Rewire remaining 11 hooks that still use untyped apiFetch. Each hook must: (a) use generated types from api-generated.ts, (b) call gateway paths /api/*, (c) have proper queryKey for cache isolation. Hooks to rewire: useStrategies, useTrading, useServiceStatus, useInstruments, useMarketData, useMlModels, useOrders, useReports, useOrganizationsList, useAudit, useVaR/useGreeks/useStressScenarios/useRiskLimits (risk sub-hooks).

    ', status: todo, blocked_by: p0-verify-ui-build}
- {id: p2-qg-hooks, content: '- [ ] [SCRIPT] P1. QG gate: run `cd unified-trading-system-ui && CI=true npm test -- --run` — all hooks pass with MSW intercepting gateway paths.

    ', status: todo, blocked_by: p2-rewire-remaining-hooks}
- {id: p3-w1-dashboard, content: '- [ ] [AGENT] P0. Migrate dashboard page — replace 5 inline arrays with usePositions, useAlerts, useServiceStatus hooks. Remove all mock data imports.

    ', status: todo, blocked_by: p2-qg-hooks}
- {id: p3-w1-trading-overview, content: '- [ ] [AGENT] P0. Migrate services/trading/overview — replace 6 inline arrays with usePositions, useStrategies, useTrading hooks.

    ', status: todo, blocked_by: p2-qg-hooks}
- {id: p3-w1-trading-risk, content: '- [ ] [AGENT] P0. Migrate services/trading/risk — replace 12 inline arrays with useRiskLimits, useVaR, useGreeks, useStressScenarios hooks.

    ', status: todo, blocked_by: p2-qg-hooks}
- {id: p3-w1-trading-alerts, content: '- [ ] [AGENT] P0. Migrate services/trading/alerts — replace 1 inline array with useAlerts hook.

    ', status: todo, blocked_by: p2-qg-hooks}
- {id: p3-w1-data-overview, content: '- [ ] [AGENT] P0. Migrate services/data/overview — replace 2 arrays + imports with useServiceStatus, useInstruments hooks.

    ', status: todo, blocked_by: p2-qg-hooks}
- {id: p3-w1-data-markets, content: '- [ ] [AGENT] P0. Migrate services/data/markets — replace 17 inline arrays with useMarketData hook.

    ', status: todo, blocked_by: p2-qg-hooks}
- {id: p3-w1-qg, content: '- [ ] [SCRIPT] P0. QG gate Wave 1: `cd unified-trading-system-ui && CI=true npm test -- --run` — all 6 Wave 1 pages pass. Grep confirms zero inline mock imports in Wave 1 pages.

    ', status: todo, blocked_by: p3-w1-dashboard}
- {id: p3-w2-trading-strategies, content: '- [ ] [AGENT] P1. Migrate services/trading/strategies — replace 5 inline arrays with useStrategies hook.

    ', status: todo, blocked_by: p3-w1-qg}
- {id: p3-w2-trading-strategies-id, content: '- [ ] [AGENT] P1. Migrate services/trading/strategies/[id] — replace 4 inline arrays with useStrategies hook (single strategy fetch).

    ', status: todo, blocked_by: p3-w1-qg}
- {id: p3-w2-trading-strategies-grid, content: '- [ ] [AGENT] P1. Migrate services/trading/strategies/grid — replace 6 inline arrays with useStrategies hook (grid view).

    ', status: todo, blocked_by: p3-w1-qg}
- {id: p3-w2-research-overview, content: '- [ ] [AGENT] P1. Migrate services/research/overview — replace 3 inline arrays with useMlModels, useStrategies hooks.

    ', status: todo, blocked_by: p3-w1-qg}
- {id: p3-w2-research-candidates, content: '- [ ] [AGENT] P1. Migrate services/research/strategy/candidates — replace 4 inline arrays with useStrategies hook.

    ', status: todo, blocked_by: p3-w1-qg}
- {id: p3-w2-research-results, content: '- [ ] [AGENT] P1. Migrate services/research/strategy/results — replace 4 inline arrays with useStrategies hook.

    ', status: todo, blocked_by: p3-w1-qg}
- {id: p3-w2-research-ml-features, content: '- [ ] [AGENT] P1. Migrate services/research/ml/features — replace 2 inline arrays with useMlModels hook.

    ', status: todo, blocked_by: p3-w1-qg}
- {id: p3-w2-qg, content: '- [ ] [SCRIPT] P1. QG gate Wave 2: `cd unified-trading-system-ui && CI=true npm test -- --run` — all 7 Wave 2 pages pass. Grep confirms zero inline mock imports in Wave 2 pages.

    ', status: todo, blocked_by: p3-w2-trading-strategies}
- {id: p3-w3-research-ml-config, content: '- [ ] [AGENT] P1. Migrate services/research/ml/config — replace 9 inline arrays with useMlModels hook.

    ', status: todo, blocked_by: p3-w2-qg}
- {id: p3-w3-research-ml-governance, content: '- [ ] [AGENT] P1. Migrate services/research/ml/governance — replace 4 inline arrays with useAudit hook.

    ', status: todo, blocked_by: p3-w2-qg}
- {id: p3-w3-research-ml-monitoring, content: '- [ ] [AGENT] P1. Migrate services/research/ml/monitoring — replace 3 inline arrays with useMlModels hook.

    ', status: todo, blocked_by: p3-w2-qg}
- {id: p3-w3-research-ml-overview, content: '- [ ] [AGENT] P1. Migrate services/research/ml/overview — replace 1 inline array with useMlModels hook.

    ', status: todo, blocked_by: p3-w2-qg}
- {id: p3-w3-research-ml-registry, content: '- [ ] [AGENT] P1. Migrate services/research/ml/registry — replace 3 inline arrays with useMlModels hook.

    ', status: todo, blocked_by: p3-w2-qg}
- {id: p3-w3-execution-algos, content: '- [ ] [AGENT] P1. Migrate services/execution/algos — replace 1 inline array with useOrders hook.

    ', status: todo, blocked_by: p3-w2-qg}
- {id: p3-w3-execution-benchmarks, content: '- [ ] [AGENT] P1. Migrate services/execution/benchmarks — replace 3 inline arrays with useOrders hook.

    ', status: todo, blocked_by: p3-w2-qg}
- {id: p3-w3-execution-tca, content: '- [ ] [AGENT] P1. Migrate services/execution/tca — replace 3 inline arrays with useOrders hook.

    ', status: todo, blocked_by: p3-w2-qg}
- {id: p3-w3-qg, content: '- [ ] [SCRIPT] P1. QG gate Wave 3: `cd unified-trading-system-ui && CI=true npm test -- --run` — all 8 Wave 3 pages pass.

    ', status: todo, blocked_by: p3-w3-research-ml-config}
- {id: p3-w4-reports-overview, content: '- [ ] [AGENT] P1. Migrate services/reports/overview — replace 6 inline arrays with useReports hook.

    ', status: todo, blocked_by: p3-w3-qg}
- {id: p3-w4-manage-clients, content: '- [ ] [AGENT] P1. Migrate services/manage/clients — replace 8 inline arrays with useOrganizationsList hook.

    ', status: todo, blocked_by: p3-w3-qg}
- {id: p3-w4-manage-users, content: '- [ ] [AGENT] P1. Migrate services/manage/users — fix partial migration (already has hook but also inline data). Remove remaining inline arrays.

    ', status: todo, blocked_by: p3-w3-qg}
- {id: p3-w4-observe-health, content: '- [ ] [AGENT] P1. Migrate services/observe/health — replace 2 inline arrays with useServiceStatus hook.

    ', status: todo, blocked_by: p3-w3-qg}
- {id: p3-w4-trading-markets, content: '- [ ] [AGENT] P1. Migrate services/trading/markets — replace 17 inline arrays with useMarketData hook.

    ', status: todo, blocked_by: p3-w3-qg}
- {id: p3-w4-qg, content: '- [ ] [SCRIPT] P1. QG gate Wave 4: `cd unified-trading-system-ui && CI=true npm test -- --run` — all 5 Wave 4 pages pass.

    ', status: todo, blocked_by: p3-w4-reports-overview}
- {id: p4-delete-mock-files, content: '- [ ] [AGENT] P0. Delete all inline mock data files: lib/trading-data.ts, lib/strategy-registry.ts, lib/ml-mock-data.ts, lib/data-service-mock-data.ts, lib/execution-platform-mock-data.ts, and any other mock data modules. Grep entire codebase to confirm zero remaining imports of deleted files.

    ', status: todo, blocked_by: p3-w4-qg}
- {id: p4-msw-alignment, content: '- [ ] [AGENT] P1. Update all MSW handlers to intercept gateway paths (/api/*) instead of any legacy paths. Remove duplicate handlers. Use generated types from api-generated.ts for response shapes.

    ', status: todo, blocked_by: p3-w4-qg}
- {id: p4-qg-clean, content: '- [ ] [SCRIPT] P0. QG gate: grep for mock data imports — zero remaining inline mock imports across all page files. Run `cd unified-trading-system-ui && CI=true npm test -- --run`. Run `VITE_MOCK_API=true npx vite build` — must succeed.

    ', status: todo, blocked_by: p4-delete-mock-files}
- {id: p5-ws-provider, content: '- [ ] [AGENT] P0. Build WebSocketProvider React context — single connection per session to unified-trading-api WS endpoint, channel subscription API, auto-reconnect with exponential backoff, connection status indicator.

    ', status: todo, blocked_by: p4-qg-clean}
- {id: p5-ws-channels, content: '- [ ] [AGENT] P1. Implement channel subscription hooks — useMarketDataWS (subscribe to instruments, receive OHLCV/trades/orderbook), usePositionsWS (balance updates), useAlertsWS (new/resolved), useExecutionWS (fill confirmations, kill switch ack), useRiskWS (threshold breaches). Each hook merges WS updates into React Query cache.

    ', status: todo, blocked_by: p5-ws-provider}
- {id: p5-ws-heartbeat, content: '- [ ] [AGENT] P1. Add WebSocket heartbeat + reconnection — server sends ping every 30s, client auto-reconnects with exponential backoff, re-subscribes to channels on reconnect.

    ', status: todo, blocked_by: p5-ws-provider}
- {id: p5-msw-ws-mock, content: '- [ ] [AGENT] P2. Add MSW WebSocket mock handler — mock WS server for tests, simulate channel messages (market ticks, alert push, fill confirmations).

    ', status: todo, blocked_by: p5-ws-channels}
- {id: p5-qg-ws, content: '- [ ] [SCRIPT] P1. QG gate: WebSocket client tests pass — connection, channel subscribe/unsubscribe, heartbeat, reconnection, all hooks pass with mock WS server.

    ', status: todo, blocked_by: p5-ws-heartbeat}
- {id: p6-config-editor-page, content: '- [ ] [AGENT] P1. Build config editor page — domain selector, JSON/YAML editor with schema validation, diff view, publish button with confirmation dialog. Calls gateway /api/config/* endpoints.

    ', status: todo, blocked_by: p4-qg-clean}
- {id: p6-config-history, content: '- [ ] [AGENT] P2. Add config version history panel — show last N config changes per domain with timestamp, user, diff. Read from gateway GET /api/config/{domain}/history.

    ', status: todo, blocked_by: p6-config-editor-page}
- {id: p6-qg-config, content: '- [ ] [SCRIPT] P1. QG gate: run `cd unified-trading-system-ui && CI=true npm test -- --run` — config pages pass vitest.

    ', status: todo, blocked_by: p6-config-editor-page}
- {id: p7-scenario-selector-ui, content: '- [ ] [AGENT] P0. Add scenario selector dropdown to admin/devops page. Dropdown lists all MockScenario values (NORMAL, HEAVY, LIGHT, BIG_RANGES, BUST, NO_SYSTEM_OVERLOAD, MISSING_DATA, DELAYED_DATA, BAD_SCHEMA, ERROR_STORM, FLASH_CRASH, HIGH_LATENCY). Selection calls POST /api/scenarios/activate via gateway. Only visible when VITE_MOCK_API=true.

    ', status: todo, blocked_by: p4-qg-clean}
- {id: p7-scenario-status-indicator, content: '- [ ] [AGENT] P0. Add current scenario indicator to UI header/status bar. Shows active scenario name + seed number. Color-coded: NORMAL=green, BUST/FLASH_CRASH=red, ERROR_STORM=orange, others=yellow. Updates via WebSocket when scenario changes.

    ', status: todo, blocked_by: p5-qg-ws}
- {id: p7-scenario-realtime-switch, content: '- [ ] [AGENT] P1. Real-time scenario switching without page reload. When scenario changes via dropdown, WebSocket pushes new scenario to all connected clients. UI components react to scenario change event.

    ', status: todo, blocked_by: p7-scenario-status-indicator}
- {id: p7-custom-scenario-builder, content: '- [ ] [AGENT] P2. Add custom scenario builder modal on admin page. Adjustable parameters: volatility multiplier (0.1x-10x), volume multiplier (0.1x-10x), missing data rate (0-50%), error injection rate (0-100%), instrument count (45-10000), tick frequency (0.1-100 Hz). Saves as custom ScenarioConfig YAML, selectable in dropdown.

    ', status: todo, blocked_by: p7-scenario-realtime-switch}
- {id: p7-perf-dashboard, content: '- [ ] [AGENT] P2. Add performance trend page to admin section. Shows historical P99 latencies per service from CI runs. Visual regression indicator (green/yellow/red). Data source: performance-baselines.json committed to PM.

    ', status: todo, blocked_by: p4-qg-clean}
- {id: p8-testnet-deployment-config, content: '- [ ] [HUMAN] P1. Create testnet.odum.io deployment config in deployment-service. Same infrastructure as production but with CLOUD_MOCK_MODE=true, MOCK_SCENARIO=NORMAL, seed=42. Data isolation: separate GCS bucket prefix (testnet-*), separate PubSub topic prefix (testnet-*). Cloud Run services with min-instances=0 (scale to zero when unused).

    ', status: todo, blocked_by: p5-qg-ws}
- {id: p8-testnet-demo-preset, content: '- [ ] [AGENT] P1. Create demo preset for external users. Read-only access (no POST/PUT/DELETE on execution endpoints). Rate limiting: 60 req/min per IP. No auth required (DISABLE_AUTH=true, VITE_SKIP_AUTH=true). Scenario locked to NORMAL (no scenario switching for external users).

    ', status: todo, blocked_by: p8-testnet-deployment-config}
- {id: p8-testnet-monitoring, content: '- [ ] [AGENT] P2. Add testnet-specific monitoring. Track: external user sessions (count, duration), API usage by endpoint, error rates, scenario health. Emit to Prometheus metrics. Add testnet health page at testnet.odum.io/health showing system status, active scenario, data freshness.

    ', status: todo, blocked_by: p8-testnet-deployment-config}
- {id: p8-testnet-data-refresh, content: '- [ ] [AGENT] P2. Scheduled daily data refresh for testnet. Cron job runs seed_mock_data.py --seed 42 for all services. Ensures testnet data stays fresh (timestamps within 24h) while maintaining determinism. GHA scheduled workflow or Cloud Scheduler.

    ', status: todo, blocked_by: p8-testnet-deployment-config}
- {id: p9-final-qg, content: '- [ ] [SCRIPT] P0. Final QG gate: full suite — `cd unified-trading-system-ui && VITE_MOCK_API=true npx vite build` succeeds, `CI=true npm test -- --run` passes, zero inline mock imports, all pages render with API data.

    ', status: todo, blocked_by: p4-qg-clean}
isProject: false
---

# Plan E: UI Backend Integration

## Context

This plan covers all UI-side integration work for unified-trading-system-ui. The original plan assumed a BFF (Backend
For Frontend) layer with 14 separate proxy routes. That architecture is now **obsolete** -- unified-trading-api absorbs
all 9 domain APIs into a single FastAPI gateway on port 8030. Next.js rewrites proxy `/api/*` directly to the gateway.

The primary remaining work is **migrating 26 pages from inline mock data to API hooks**, then cleaning up mock data
files.

## What Changed (Architecture Shift)

| Old Architecture                       | New Architecture                                  |
| -------------------------------------- | ------------------------------------------------- |
| 14 BFF routes in Next.js API directory | Single rewrite: `/api/:path*` -> `localhost:8030` |
| Per-service port mapping + registry    | One gateway URL                                   |
| Hand-wired proxy with auth forwarding  | Next.js rewrite + `Authorization: Bearer` header  |
| Separate BFF scaffold phase            | No BFF -- gateway is the aggregation layer        |

**Already done:** TS type generation (3.2K lines), proxy path fix, auth header fix, 3 typed hooks (positions, alerts,
risk).

## Source Mapping

| Phase | Source    | What                                                                             |
| ----- | --------- | -------------------------------------------------------------------------------- |
| 0     | Plan A    | Generate TS constants, delete hand-maintained TS, verify UI build                |
| 0B    | Audit fix | DONE -- proxy paths + auth header                                                |
| 1-2   | Plan C    | OBSOLETE (BFF) / Hook rewire (remaining 11 hooks)                                |
| 3     | New       | 4 page migration waves (26 pages total)                                          |
| 4     | Plan C    | Delete inline mock files + MSW alignment                                         |
| 5     | Plan C    | WebSocket client hooks                                                           |
| 6     | Plan B    | UI config CRUD (editor page, history panel)                                      |
| 7     | Plan D    | UI scenario panel (selector, status indicator, real-time switch, custom builder) |
| 8     | Plan D    | External testnet deployment (testnet.odum.io, demo preset, monitoring, refresh)  |

## Execution DAG

```
Phase 0 (TS constants + hand-maintained deletion)
    |
    v  [QG gate]
Phase 2 (rewire remaining 11 hooks)
    |
    v  [QG gate]
Phase 3 — Wave 1 (6 high-traffic pages, PARALLEL)
    |
    v  [QG gate]
Phase 3 — Wave 2 (7 strategy/ML pages, PARALLEL)
    |
    v  [QG gate]
Phase 3 — Wave 3 (8 remaining pages, PARALLEL)
    |
    v  [QG gate]
Phase 3 — Wave 4 (5 reports/manage pages, PARALLEL)
    |
    v  [QG gate]
Phase 4 (delete mock files + MSW alignment)
    |
    v  [QG gate]
    +---------------------------+---------------------------+
    |                           |                           |
Phase 5 (WebSocket)       Phase 6 (config CRUD)      Phase 7 (scenario panel)
    |                           |                           |
    v  [QG gate]                v  [QG gate]                v
Phase 8 (testnet deployment)    |                           |
    |                           |                           |
    +---------------------------+---------------------------+
    |
    v
Phase 9 (final verification)
    |
    v
  DONE
```

## Success Criteria

| Phase | Gate | Criteria                                                                        |
| ----- | ---- | ------------------------------------------------------------------------------- |
| 0     | C4   | Hand-maintained TS deleted, generated types compile, vite build succeeds        |
| 0B    | DONE | Proxy paths correct, auth header correct                                        |
| 1     | DONE | OBSOLETE -- no BFF needed                                                       |
| 2     | C3   | All 14 hooks use generated types and call gateway /api/\* paths                 |
| 3     | C4   | All 26 pages migrated, zero inline mock arrays in page components               |
| 4     | C4   | Mock data files deleted, zero mock imports, MSW aligned, build + tests pass     |
| 5     | C4   | WebSocket provider + 5 channel hooks, heartbeat, reconnect, MSW WS mock         |
| 6     | C4   | Config editor page, version history panel                                       |
| 7     | C4   | Scenario selector, status indicator, real-time switching                        |
| 8     | D3   | testnet.odum.io accessible, demo preset enforces read-only                      |
| 9     | C5   | All pages render, full test suite green, vite build succeeds, zero mock imports |
