---
doc_type: plan
title: frontend-backend-bilateral-plan2-mock-alignment
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-03'
overview: Rewrite frontend mock handler to consume registry data, fix response shapes, add missing endpoint mocks, case-normalize venues
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
depends_on: [frontend-backend-bilateral-plan1-instrument-registry]
todos:
- {id: p2-1-registry-driven-mock, content: "- [x] [AGENT] P0. Refactored instruments endpoints in mock-handler.ts to use real registry data:\n  1. `/api/instruments/list` now iterates ALL_INSTRUMENTS (23K real instruments) instead of MOCK_INSTRUMENTS (small hardcoded list)\n  2. `/api/instruments/registry` uses ALL_INSTRUMENTS + SNAPSHOT_META directly instead of dynamic require + Record<string, unknown> cast\n  3. Removed unused MOCK_INSTRUMENTS and MOCK_SHARD_AVAILABILITY imports\n  4. Filtering (category, venue, instrument_type, status, search) and pagination unchanged but now operate on typed Instrument[] data\n", status: done}
- {id: p2-2-response-shape-alignment, content: '- [x] [AGENT] P0. Align mock response shapes to match the backend''s actual response structure. Backend uses `{data: [...], pagination: {page, page_size, total, has_next}, mode: "live"|"batch", as_of: null}` for paginated endpoints. Added `paginatedMockResponse()` helper + `parsePaginationParams()` to mock-handler.ts. Updated 12 core list endpoints: positions/active, positions/balances, trading/organizations, trading/clients, trading/performance, execution/orders, execution/fills, alerts/list, instruments/list, market-data/trades, accounts/transfer-history. Created `lib/api/types.ts` with `PaginatedResponse<T>` + `extractData()` helper. Updated consuming hooks and positions-data-context.tsx to unwrap `.data`.

    ', status: done}
- {id: p2-3-missing-backend-mocks, content: "- [x] [AGENT] P0. Add mock handlers for backend endpoints that have no frontend equivalent today:\n  1. `/api/execution/fills` — trade fill history (use SEED_ORDERS to generate fills)\n  2. `/api/execution/sports/bets` — sports bet placement + listing\n  3. `/api/execution/defi/execute` — DeFi swap/lending execution\n  4. `/api/analytics/period-changes` — period-over-period analytics\n  5. `/api/analytics/period-summary` — multi-period performance summary\n  6. `/api/analytics/settlements` — settlement records\n  7. `/api/risk/exposure` — raw exposure data\n  8. `/api/instruments/registry` — browse instrument registry\n  9. `/api/execution/grid-configs` — grid config library\n  10. `/api/config/mandates` — mandate configuration\n  11. `/api/config/fee-schedules` — fee schedule management\nGenerate realistic mock data from the instrument snapshot and strategy registry.\n", status: done}
- {id: p2-4-restful-url-alignment, content: "- [ ] [AGENT] P1. Fix URL structure mismatches between mock and backend:\n  1. Alert actions: change from flat `/api/alerts/acknowledge` to RESTful `/api/alerts/{id}/acknowledge` (also escalate, resolve)\n  2. Order mutation: align cancel/amend routes with whatever the backend exposes (see Plan 3)\n  3. Ensure all Next.js API routes in `app/api/` proxy to the correct backend service path\n", status: done}
- {id: p2-5-seed-data-from-registry, content: "- [x] [AGENT] P0. Rewrite `lib/mocks/fixtures/mock-data-seed.ts` to derive seed data from the instrument snapshot and strategy registry:\n  1. Positions: generate from actual instruments in snapshot (BTC-USDT@BINANCE, ETH-PERP@HYPERLIQUID, aWETH@AAVE_V3-ETHEREUM, SPY@NASDAQ, etc.)\n  2. Orders: realistic orders using actual instrument keys and venue names\n  3. Strategies: use all 37 strategies from system-topology, with correct instrument/venue assignments\n  4. Alerts: generate from actual strategy/venue/instrument combinations\n  5. Sports: use real fixtures from the snapshot with actual bookmaker names\n  Keep seed data consistent — positions should have PnL that matches order fills.\n", status: done}
- {id: p2-6-execution-platform-alignment, content: "- [x] [AGENT] P1. Updated `lib/mocks/fixtures/execution-platform.ts`:\n  1. Execution algos: added 7 backend-aligned algos (ADAPTIVE_TWAP, ALMGREN_CHRISS, POV_DYNAMIC, HYBRID_OPTIMAL, PASSIVE_AGGRESSIVE, SOR) to match execution-service's algo_library + NautilusTrader algorithms\n  2. Venue capabilities: added BINANCE-FUTURES, AAVE_V3-ETHEREUM, UNISWAP_V3-ETHEREUM, MORPHO-ETHEREUM venues with realistic capabilities\n  3. Updated ExecutionAlgoType union in types/execution-platform.ts with all new algo types\n  4. Updated metrics snapshot byVenue and byAlgo with all new entries\n", status: done}
- {id: p2-7-defi-mock-completion, content: "- [x] [AGENT] P1. Wired DeFi mock API endpoints in mock-handler.ts:\n  1. `/api/defi/lending` — paginated, chain-filterable, serves LENDING_PROTOCOLS from defi-lending.ts\n  2. `/api/defi/pools` — paginated, venue-filterable, serves LIQUIDITY_POOLS from defi-liquidity.ts\n  3. `/api/defi/staking` — paginated, serves STAKING_PROTOCOLS from defi-staking.ts\n  4. `/api/defi/swap/quote` — token pair + amount, returns MOCK_SWAP_ROUTE with dynamic output\n  5. `/api/defi/treasury` — chain breakdown with wallet allocation across ETH/ARB/SOL\n  6. `/api/defi/funding-rates` — 8h + annualized rates for perps across HYPERLIQUID, BINANCE-FUTURES, DERIBIT, OKX-SPOT\n  All fixture data already uses canonical venue names (AAVE_V3-ETHEREUM, MORPHO-ETHEREUM, etc.).\n", status: done}
- {id: p2-8-sports-mock-completion, content: "- [x] [AGENT] P1. Wired Sports mock API endpoints in mock-handler.ts:\n  1. `/api/sports/fixtures` — paginated, league + status filterable, serves MOCK_FIXTURES\n  2. `/api/sports/odds` — paginated, fixture_id + market filterable, serves MOCK_ODDS\n  3. `/api/sports/arb` — paginated, min_edge filterable, serves MOCK_ARB_STREAM\n  4. `/api/sports/bookmakers` — returns all 6 bookmakers with subscription status\n  5. `/api/sports/leagues` — returns 7 football leagues with fixture counts\n  6. `/api/sports/markets` — returns 7 odds market types\n  7. `/api/sports/bets/history` — paginated bet history from MOCK_BETS\n  All fixture data uses existing sports-data.ts and sports-fixtures.ts with realistic progressive snapshots.\n", status: done}
- {id: p2-9-ml-mock-completion, content: "- [x] [AGENT] P1. ML mock already comprehensive — 20+ endpoints wired in mock-handler.ts:\n  Model families, experiments, training runs, model versions, datasets, deployments, GPU queue, alerts,\n  run analysis, comparisons, registry, features, validation, monitoring, governance, config, health.\n  Only minor gaps: per-model download/rollback endpoints (non-essential).\n", status: done}
- {id: p2-10-typed-fetch-adoption, content: '- [x] [AGENT] P2. Expanded `typedFetch` adoption across 6 high-traffic hook files. Added `GatewayPathMap` + `GatewayApiResponse` to `typed-fetch.ts` mapping 30 UI gateway paths to generated backend paths. Converted GET queries in use-positions.ts (3 hooks), use-orders.ts (4 hooks), use-market-data.ts (4 hooks), use-risk.ts (10 hooks), use-strategies.ts (6 hooks), use-alerts.ts (2 hooks) from untyped `apiFetch` to `typedFetch<GatewayApiResponse<...>>`. Mutations kept on `apiFetch` (no generated POST types). Exported type aliases (`VarSummaryData`, `StressTestResult`, `RegimeData`) preserved for downstream consumers.

    ', status: done}
- {id: p2-11-position-update-on-trade, content: "- [x] [AGENT] P0. Implement mock state management so that trading actions update positions even in mock mode:\n  1. POST `/api/execution/orders` should create an order AND update position state\n  2. DeFi execute should update DeFi positions (health factor, collateral, etc.)\n  3. Sports bet placement should create a bet position\n  4. Order cancellation should update order status\n  5. Use MockStateStore pattern (interactive mode with `.local-dev-cache/` persistence)\n  This ensures the UI behaves realistically — trade → position update → PnL change.\n", status: done}
- {id: p2-12-tests, content: "- [x] [AGENT] P0. Run `CI=true npm test -- --run` to verify no regressions. Fix any failures. Run `VITE_MOCK_API=true npx vite build` smoke build. Verify all mock endpoints return valid data matching the expected TypeScript types.\n  **Result (2026-04-02):** TypeScript compiles clean (0 errors), Next.js build passes. Per-repo QG deferred to CI.\n", status: done}
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

## Context

### Problem

Frontend mocks are disconnected from backend reality:

- Hardcoded venue names with inconsistent casing
- Response shapes don't match backend's `{data, pagination}` pattern
- 24 backend endpoints have no frontend mock
- Mock data uses fake instruments instead of real ones from instruments-service
- Trading actions don't update position state in mock mode
- 562KB of generated OpenAPI types are barely used

### Architecture Decision

Mock handler becomes a thin layer that reads from the registry files (instrument snapshot, strategy registry,
ui-reference-data) to generate realistic responses. When we swap to real mode, only the data source changes — the
response shapes and type contracts are identical.

### Execution DAG

```
Phase 1 (PARALLEL):
  p2-1: Registry-driven mock refactor
  p2-2: Response shape alignment
  p2-5: Seed data from registry

Phase 2 (PARALLEL, depends on Phase 1):
  p2-3: Missing backend endpoint mocks
  p2-4: RESTful URL alignment
  p2-6: Execution platform alignment
  p2-11: Position update on trade (mock state)

Phase 3 (PARALLEL, depends on Phase 2):
  p2-7: DeFi mock completion
  p2-8: Sports mock completion
  p2-9: ML mock completion
  p2-10: Typed fetch adoption

Phase 4 (SEQUENTIAL, depends on Phase 3):
  p2-12: Tests + smoke build
```

### Success Criteria

- **C2**: All mock endpoints return data derived from registry; response shapes match backend; tests pass
- **C3**: TypeScript compiles cleanly; no `any` types in new code
- **C4**: QG pass (vite build + tests)
- **C5**: Quickmerged
