---
title: "Frontend-Backend Integration & Testnet Architecture"
status: active
priority: P0
owner: human
locked_by: live-defi-rollout
locked_since: 2026-03-21
created: 2026-03-21
updated: 2026-03-21
affects:
  - unified-trading-system-ui
  - unified-api-contracts
  - unified-trading-library
  - unified-internal-contracts
  - unified-cloud-interface
  - deployment-api
  - config-api
  - execution-results-api
  - trading-analytics-api
  - batch-audit-api
  - client-reporting-api
  - ml-training-api
  - ml-inference-api
  - market-data-api
  - alerting-service
  - execution-service
  - position-balance-monitor-service
  - unified-trading-pm
---

# Frontend-Backend Integration & Testnet Architecture

## Problem Statement

The unified-trading-system-ui has 151 pages but **0% real backend connectivity**. Two independent mock systems exist
(7,100 lines of inline TypeScript mock data + MSW handlers), neither connected to the 21-service backend. Schema changes
don't propagate. Mock data is duplicated across Python and TypeScript. There's no real-time push (only polling).
Production runs on mock data (`NEXT_PUBLIC_MOCK_API=true`).

The goal: make the frontend work identically in mock and real modes, where switching is **just env vars**. Mock mode
becomes a "testnet" — complete with stress tests, edge cases, and realistic instrument lifecycles.

## Current State Audit

### What Exists

| Layer                | State                                     | Detail                                              |
| -------------------- | ----------------------------------------- | --------------------------------------------------- |
| **Backend services** | 21 services, all with `seed_mock_data.py` | Mock data pipeline operational (11GB, all 7 layers) |
| **Backend APIs**     | 9 API repos + 3 services with HTTP        | All have `is_mock_mode()` branching                 |
| **OpenAPI spec**     | 223 paths, 68 schemas                     | execution-results-api MISSING, many empty schemas   |
| **UI framework**     | Next.js 16 + React 19 + MSW + React Query | Good foundation, poorly wired                       |
| **UI mock data**     | 7,100 lines inline TS + 16 MSW handlers   | Duplicates backend mock data                        |
| **UI→API hooks**     | 14 React Query hooks in `hooks/api/`      | Only 3 pages use them (ops section)                 |
| **OpenAPI codegen**  | `openapi-typescript` script exists        | Generated types in `.bak` file, unused              |
| **Real-time**        | Polling only (2-10s intervals)            | No WebSocket/SSE except deployment-ui SSE           |
| **Auth**             | Client-side persona selection             | No real OAuth/OIDC wiring                           |

### Critical Gaps

1. **Dual mock layers bypass each other** — UI mocks and API mocks are independent
2. **No OpenAPI→TypeScript codegen pipeline** — backend changes don't propagate
3. **Hooks hit `/api/*` but real services are at `/{service-name}/api/*`** — URL mismatch
4. **541 orphan domain models** — rich internal schemas not exposed via API
5. **execution-results-api missing from OpenAPI spec** — serves 3 UIs
6. **No real-time push** — only polling (2-10s intervals)
7. **Production runs on mock data** — `.env.production` has `NEXT_PUBLIC_MOCK_API=true`
8. **Two mock architectures** — Vite UIs use fetch monkey-patching, Next.js uses MSW

## Architecture Decision: API Gateway + Shared Mock Layer

### Decision 1: Single API Gateway (BFF Pattern)

Instead of the UI calling 12 different API backends directly, introduce a **Next.js API route layer** that acts as a
Backend-for-Frontend (BFF):

```
UI Component → React Query hook → /api/{domain}/{endpoint}
                                       ↓
                              Next.js API Route (BFF)
                                       ↓
                    ┌──────────────────┼──────────────────┐
                    ↓                  ↓                  ↓
              Service A API      Service B API     Service C API
              (port 8004)        (port 8006)       (port 8012)
```

**Why BFF over direct calls:**

- Single origin for all API calls (no CORS, no port management)
- Server-side auth token injection (no client-side token handling)
- Response aggregation (dashboard needs data from 5 APIs)
- Mock/real switch at ONE layer (BFF routes, not 151 pages)
- Consistent error handling and rate limiting

**In mock mode:** BFF routes call the same backend APIs running with `DATA_MODE=mock`. **In real mode:** BFF routes call
real backend APIs. Same code path.

### Decision 2: OpenAPI → TypeScript Codegen Pipeline

```
Pydantic model (UIC/UAC)
  → FastAPI auto-generates OpenAPI spec
    → `openapi-typescript` generates TypeScript types
      → React Query hooks use generated types
        → MSW handlers validate against same types
```

**Trigger:** Any commit to an API repo runs the codegen pipeline. CI fails if types drift.

### Decision 3: Shared Mock Data Source

Backend `seed_mock_data.py` scripts already generate realistic data. Instead of maintaining separate TypeScript mock
data, the BFF layer reads from the **same MockStateStore** that backend APIs use. In mock mode:

```
seed_mock_data.py → MockStateStore → API route → BFF → React Query → Component
```

The 7,100 lines of inline TypeScript mock data get deleted. MSW handlers become thin wrappers around the BFF endpoints
(for client-side-only dev without starting APIs).

### Decision 4: WebSocket for Real-Time Data

Add a WebSocket endpoint at `/api/ws` in the BFF that multiplexes:

- Market data ticks (from UMI feeds or mock generators)
- Position updates (from execution-service events)
- Alert notifications (from alerting-service)
- System health (from service health checks)

In mock mode: WebSocket sends synthetic ticks from `SyntheticDataGenerator.generate_tick_trades()` at configurable
frequency. Same generator, same scenarios (normal/heavy/bust).

## Execution Phases

### Phase 0: Foundation — OpenAPI + Codegen Pipeline [PARALLEL]

```
p0-openapi-fix ──→ p0-codegen ──→ p0-types-import
                                        ↓
                                   [QG GATE]
```

#### p0-openapi-fix

- [ ] [AGENT] P0. Add execution-results-api to OpenAPI spec generation script
- [ ] [AGENT] P0. Fix empty response schemas in deployment-api OpenAPI paths
- [ ] [AGENT] P0. Add pnl-attribution-service and risk-and-exposure-service API endpoints to spec
- [ ] [AGENT] P0. Regenerate unified-trading-system.openapi.json with all 12 API surfaces
- [ ] [AGENT] P1. Add schema parity CI test: mock_data.py seed data validates against FastAPI response models

#### p0-codegen

- [ ] [AGENT] P0. Fix `openapi-typescript` codegen script in unified-trading-system-ui
- [ ] [AGENT] P0. Generate `lib/types/api-generated.ts` from updated OpenAPI spec
- [ ] [AGENT] P0. Create `scripts/generate-api-types.sh` that pulls latest spec from UAC and runs codegen
- [ ] [AGENT] P1. Add CI step: on any API repo commit, regenerate types and fail if drift detected

#### p0-types-import

- [ ] [AGENT] P0. Replace hand-written types in `lib/*-types.ts` with imports from `api-generated.ts`
- [ ] [AGENT] P0. Update all 14 React Query hooks to use generated types for request/response
- [ ] [AGENT] P1. Delete `api-generated.ts.bak` and unused hand-written type files

**QG Gate:** `openapi-typescript` runs clean, all hooks compile with generated types.

### Phase 1: BFF Layer — Next.js API Routes [SEQUENTIAL after Phase 0]

```
p1-bff-scaffold ──→ p1-bff-routes ──→ p1-bff-mock ──→ p1-hook-rewire
                                                            ↓
                                                       [QG GATE]
```

#### p1-bff-scaffold

- [ ] [AGENT] P0. Create `app/api/` directory structure matching domain layout
- [ ] [AGENT] P0. Create `lib/api-client.ts` — server-side HTTP client with service discovery
- [ ] [AGENT] P0. Implement service URL resolution from `SERVICE_ENDPOINTS` config (env-driven)
- [ ] [AGENT] P0. Add auth token forwarding middleware (pass-through from client → backend)
- [ ] [AGENT] P1. Add request/response logging middleware for debugging

#### p1-bff-routes

Create Next.js API routes for each domain. Each route proxies to the real backend API:

- [ ] [AGENT] P0. `/api/instruments/[...path]` → instruments endpoints (config-api + instruments-service)
- [ ] [AGENT] P0. `/api/execution/[...path]` → execution-results-api (port 8006)
- [ ] [AGENT] P0. `/api/market-data/[...path]` → market-data-api (port 8016)
- [ ] [AGENT] P0. `/api/positions/[...path]` → position-balance-monitor-service (port 8020)
- [ ] [AGENT] P0. `/api/risk/[...path]` → risk-and-exposure-service
- [ ] [AGENT] P0. `/api/pnl/[...path]` → pnl-attribution-service
- [ ] [AGENT] P0. `/api/strategies/[...path]` → execution-results-api (backtests)
- [ ] [AGENT] P0. `/api/ml/[...path]` → ml-training-api + ml-inference-api
- [ ] [AGENT] P0. `/api/alerts/[...path]` → alerting-service (port 8021)
- [ ] [AGENT] P0. `/api/analytics/[...path]` → trading-analytics-api (port 8012)
- [ ] [AGENT] P0. `/api/deployments/[...path]` → deployment-api (port 8004)
- [ ] [AGENT] P0. `/api/audit/[...path]` → batch-audit-api (port 8013)
- [ ] [AGENT] P0. `/api/reports/[...path]` → client-reporting-api (port 8014)
- [ ] [AGENT] P0. `/api/config/[...path]` → config-api (port 8005)
- [ ] [AGENT] P1. `/api/health` → aggregate health from all backends

#### p1-bff-mock

- [ ] [AGENT] P0. When `DATA_MODE=mock`, BFF routes call backend APIs running in mock mode (same path)
- [ ] [AGENT] P0. No special mock logic in BFF — mock/real is a backend concern, BFF is always a passthrough
- [ ] [AGENT] P1. Add `NEXT_PUBLIC_API_MODE` env var: `bff` (default) vs `direct` (legacy multi-port)

#### p1-hook-rewire

- [ ] [AGENT] P0. Update all 14 React Query hooks to call `/api/{domain}/...` (BFF routes)
- [ ] [AGENT] P0. Remove hardcoded port numbers and `SERVICE_ENDPOINTS` from client-side code
- [ ] [AGENT] P0. All API calls go through BFF — single origin, no CORS

**QG Gate:** All hooks call BFF routes. `npm run build` succeeds. No direct backend URLs in client code.

### Phase 2: Delete Inline Mock Data + Wire MSW to BFF [PARALLEL with Phase 1 BFF routes]

```
p2-delete-inline ──→ p2-msw-bff ──→ p2-verify
                                        ↓
                                   [QG GATE]
```

#### p2-delete-inline

- [ ] [AGENT] P0. Delete `lib/trading-data.ts` (1,200+ lines of inline mock data)
- [ ] [AGENT] P0. Delete `lib/ml-mock-data.ts`, `lib/strategy-platform-mock-data.ts`
- [ ] [AGENT] P0. Delete `lib/execution-platform-mock-data.ts`, `lib/data-service-mock-data.ts`
- [ ] [AGENT] P0. Update all 68 pages that import from deleted files → use React Query hooks instead
- [ ] [AGENT] P1. Delete unused `lib/reference-data.ts` inline data (move to BFF reference endpoint)

#### p2-msw-bff

- [ ] [AGENT] P0. Update MSW handlers to intercept `/api/{domain}/...` paths (matching BFF routes)
- [ ] [AGENT] P0. MSW handler responses use generated TypeScript types (not hand-crafted literals)
- [ ] [AGENT] P0. MSW handlers call `SyntheticDataGenerator` patterns for market data (GBM prices)
- [ ] [AGENT] P1. MSW handlers support scenario selection (`normal`, `heavy`, `bust`, etc.)
- [ ] [AGENT] P1. Add MSW handler for `/api/ws` mock WebSocket (synthetic ticks)

#### p2-verify

- [ ] [AGENT] P0. Verify all 151 pages render with BFF + backend mock mode (no inline data)
- [ ] [AGENT] P0. Verify all 151 pages render with MSW only (no backend needed, for pure frontend dev)
- [ ] [AGENT] P1. Add Playwright smoke tests for top 20 pages in both modes

**QG Gate:** Zero inline mock data files. All pages render in both BFF-mock and MSW-only modes.

### Phase 3: Real-Time Data — WebSocket + SSE [PARALLEL after Phase 1]

```
p3-ws-server ──→ p3-ws-client ──→ p3-ws-mock
                                      ↓
                                 [QG GATE]
```

#### p3-ws-server

- [ ] [AGENT] P0. Create `/api/ws` WebSocket endpoint in BFF (Next.js WebSocket support)
- [ ] [AGENT] P0. Multiplex channels: `market-data`, `positions`, `alerts`, `health`
- [ ] [AGENT] P0. Server subscribes to backend PubSub topics (via UCI `get_pubsub_client()`)
- [ ] [AGENT] P0. Forward events to connected WebSocket clients with channel-based routing
- [ ] [AGENT] P1. Add SSE fallback at `/api/events` for environments that block WebSocket

#### p3-ws-client

- [ ] [AGENT] P0. Create `hooks/useWebSocket.ts` — auto-reconnect, channel subscription, typed messages
- [ ] [AGENT] P0. Create `hooks/useMarketData.ts` — real-time price ticks via WebSocket
- [ ] [AGENT] P0. Create `hooks/useAlerts.ts` — real-time alert notifications
- [ ] [AGENT] P0. Create `hooks/usePositions.ts` — real-time position updates
- [ ] [AGENT] P0. Wire trading page to `useMarketData` (replace Brownian motion simulation)
- [ ] [AGENT] P1. Wire dashboard to `useAlerts` + `usePositions` (replace polling intervals)

#### p3-ws-mock

- [ ] [AGENT] P0. In mock mode, WebSocket server generates synthetic ticks from `SyntheticDataGenerator`
- [ ] [AGENT] P0. Tick frequency configurable (1/s normal, 10/s heavy, 100/s stress test)
- [ ] [AGENT] P0. Mock alert injection: periodic synthetic alerts matching `AlertEvent` schema
- [ ] [AGENT] P1. Scenario-driven: `bust` scenario sends rapid price drops + circuit breaker alerts

**QG Gate:** Trading page shows live ticks via WebSocket. Dashboard shows real-time alerts.

### Phase 4: Structural Change Propagation — CI/CD Pipeline [SEQUENTIAL after Phase 0]

```
p4-ci-codegen ──→ p4-ci-parity ──→ p4-ci-msw
                                       ↓
                                  [QG GATE]
```

#### p4-ci-codegen

- [ ] [AGENT] P0. GHA workflow: on API repo push → regenerate OpenAPI spec → run codegen → open PR on UI repo
- [ ] [AGENT] P0. Pre-commit hook in API repos: `openapi-diff` checks for breaking changes
- [ ] [AGENT] P1. Semantic versioning for API changes: breaking change = major bump = approval required

#### p4-ci-parity

- [ ] [AGENT] P0. CI test: MSW handler response shapes match OpenAPI spec (automated schema validation)
- [ ] [AGENT] P0. CI test: `mock_data.py` seed data validates against FastAPI response Pydantic models
- [ ] [AGENT] P1. CI test: generated TypeScript types match MSW handler return types (type-level test)

#### p4-ci-msw

- [ ] [AGENT] P0. When backend adds new field → codegen updates types → MSW handler type error → fix MSW
- [ ] [AGENT] P0. When backend removes field → codegen updates types → UI component type error → fix UI
- [ ] [AGENT] P1. Dashboard showing API version drift across all services (in deployment-ui or ops page)

**QG Gate:** Any API schema change triggers automated type updates. No manual sync needed.

### Phase 5: Testnet Experience — Scenarios + Edge Cases [PARALLEL after Phase 3]

```
p5-scenario-ui ──→ p5-edge-cases ──→ p5-external-testnet
                                          ↓
                                     [QG GATE]
```

#### p5-scenario-ui

- [ ] [AGENT] P0. Add scenario selector to admin/devops page (dropdown: normal/heavy/bust/etc.)
- [ ] [AGENT] P0. Scenario change updates `MOCK_SCENARIO` env var → backends regenerate mock state
- [ ] [AGENT] P0. UI shows current scenario in header/status bar
- [ ] [AGENT] P1. Add custom scenario builder (adjust vol, volume, missing data rate, fault injection)

#### p5-edge-cases

- [ ] [AGENT] P0. Instrument lifecycle testing: create/delist/expire instruments via admin panel
- [ ] [AGENT] P0. Bad schema injection: send malformed data through pipeline, verify UI error handling
- [ ] [AGENT] P0. Circuit breaker simulation: trigger kill switch, verify UI shows degraded state
- [ ] [AGENT] P0. DeFi health factor breach: simulate liquidation threshold approach, verify alerts
- [ ] [AGENT] P1. Flash crash simulation: `bust` scenario with 50% price drop in 5 minutes

#### p5-external-testnet

- [ ] [AGENT] P1. External user access via `demo` preset (read-only, rate-limited, no auth)
- [ ] [AGENT] P1. Testnet URL: `testnet.odum.io` → same UI, `DATA_MODE=mock` backend
- [ ] [AGENT] P2. Testnet data isolation: separate GCS bucket prefix, separate PubSub topics
- [ ] [AGENT] P2. Testnet monitoring: track external user sessions, API usage, error rates

**QG Gate:** Scenario selector works. Edge cases trigger visible UI responses. Testnet accessible.

### Phase 6: Page Migration — Wire Remaining Pages [SEQUENTIAL after Phases 1-2]

Priority order based on backend readiness and user value:

#### p6-wave-1 (Backend fully ready)

- [ ] [AGENT] P0. Dashboard page — aggregate data from 5+ APIs
- [ ] [AGENT] P0. Trading page — positions, orders, market data, risk
- [ ] [AGENT] P0. Positions page — position-balance-monitor-service
- [ ] [AGENT] P0. Risk page — risk-and-exposure-service
- [ ] [AGENT] P0. Alerts page — alerting-service
- [ ] [AGENT] P0. Markets page — market-data-api + instruments

#### p6-wave-2 (Backend partially ready)

- [ ] [AGENT] P0. Strategies page — execution-results-api backtests
- [ ] [AGENT] P0. ML pages — ml-training-api + ml-inference-api
- [ ] [AGENT] P0. Reports page — client-reporting-api
- [ ] [AGENT] P0. Analytics page — trading-analytics-api
- [ ] [AGENT] P0. Execution pages — execution-results-api

#### p6-wave-3 (Backend needs work)

- [ ] [AGENT] P1. Backtest builder — needs restructured execution-results-api
- [ ] [AGENT] P1. Client portal — needs multi-tenant auth + client-reporting-api
- [ ] [AGENT] P1. Admin/config pages — config-api
- [ ] [AGENT] P2. Deployment pages — deployment-api (already has SSE)

**QG Gate:** Wave 1 pages work end-to-end with real backend. Wave 2 works with mock backend.

## Dependency DAG

```
Phase 0 (OpenAPI + Codegen)
    ↓
Phase 1 (BFF Layer)  ←──── Phase 2 (Delete inline mocks) [parallel within]
    ↓                           ↓
Phase 3 (WebSocket)        Phase 4 (CI/CD propagation)
    ↓                           ↓
Phase 5 (Testnet)          Phase 6 (Page migration)
```

Phases 0→1 are sequential (codegen before BFF). Phases 1+2 run in parallel (BFF routes + mock deletion). Phases 3+4 run
in parallel after Phase 1. Phases 5+6 run in parallel after Phase 3.

## Success Criteria

### Per-Phase Gates

- **Phase 0:** OpenAPI spec covers all 12 API surfaces. Codegen produces clean TypeScript types.
- **Phase 1:** All UI API calls go through BFF. Zero direct backend URLs in client code.
- **Phase 2:** Zero inline mock data files. All pages render in BFF-mock and MSW-only modes.
- **Phase 3:** Trading page shows live WebSocket ticks. Dashboard shows real-time alerts.
- **Phase 4:** Any API schema change triggers automated type update PR on UI repo.
- **Phase 5:** Scenario selector works. External testnet accessible.
- **Phase 6:** Wave 1 pages (dashboard, trading, positions, risk, alerts) work with real backend.

### Final Success

- `--mode mock` → full testnet experience with scenarios and edge cases
- `--mode real` → production with real data, same UI code, just env vars
- Backend schema change → automated codegen → UI type update → MSW update → zero manual sync
- External users can access testnet at `testnet.odum.io`

## Key Design Decisions

| Decision      | Choice                                                | Rationale                                             |
| ------------- | ----------------------------------------------------- | ----------------------------------------------------- |
| API pattern   | BFF (Next.js API routes)                              | Single origin, server-side auth, response aggregation |
| Mock strategy | Backend mock mode via BFF (not client-side mock data) | Same code path mock/real, no dual maintenance         |
| Real-time     | WebSocket with SSE fallback                           | Sub-second updates for trading, graceful degradation  |
| Type safety   | OpenAPI → `openapi-typescript` codegen                | Automated, CI-enforced, zero manual sync              |
| Testnet       | Same infrastructure, `DATA_MODE=mock`                 | No separate deployment, just env vars                 |
| MSW role      | Development-only (no backend needed)                  | Quick frontend iteration, not the primary mock layer  |

## Out of Scope (Separate Plans)

- OAuth/OIDC real auth integration (separate auth plan)
- API rate limiting and throttling (infrastructure plan)
- CDN and edge caching for static assets
- Mobile responsive design
- Accessibility (a11y) compliance
- Performance optimization (code splitting, lazy loading)

## Risk Register

| Risk                                                  | Impact                                        | Mitigation                                       |
| ----------------------------------------------------- | --------------------------------------------- | ------------------------------------------------ |
| Next.js 16 WebSocket support is experimental          | WebSocket endpoint may not work in production | SSE fallback endpoint, test in staging           |
| 68 pages importing inline mock data — large migration | Breaking many pages at once                   | Wave-based migration, keep MSW as fallback       |
| OpenAPI spec has empty schemas                        | Codegen produces `unknown` types              | Fix schemas in Phase 0 before codegen            |
| execution-results-api missing from spec               | 3 UIs have no typed API contract              | Add to spec in Phase 0                           |
| Backend backtesting structure subject to change       | BFF routes may need refactoring               | Abstract backtesting behind stable BFF interface |
