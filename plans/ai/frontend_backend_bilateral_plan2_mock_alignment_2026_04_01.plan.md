---
name: frontend-backend-bilateral-plan2-mock-alignment
overview:
  Rewrite frontend mock handler to consume registry data, fix response shapes, add missing endpoint mocks,
  case-normalize venues
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: none
    business: none

depends_on:
  - frontend-backend-bilateral-plan1-instrument-registry

todos:
  - id: p2-1-registry-driven-mock
    content: |
      - [ ] [AGENT] P0. Refactor `lib/api/mock-handler.ts` to pull venue lists, instrument lists, and strategy definitions from the registry files (`lib/registry/generated.ts`, `lib/registry/instruments.ts`, `lib/strategy-registry.ts`) instead of hardcoded data. Remove all hardcoded venue/instrument/strategy string matching (e.g., `if (n.includes("btc"))` patterns). Instead, use registry lookups. All venue names UPPERCASE consistently (BINANCE, not "Binance" or "binance").
    status: todo
  - id: p2-2-response-shape-alignment
    content: |
      - [ ] [AGENT] P0. Align mock response shapes to match the backend's actual response structure. Backend uses `{data: [...], pagination: {page, page_size, total}, mode: "live"|"batch", as_of: null}` for paginated endpoints. Update ALL mock responses to match: positions, orders, fills, strategies, alerts, ML models, reports, market-data. Update the consuming components/hooks to expect the new shape. This is the contract — when we swap mock for real, the shapes must match.
    status: todo
  - id: p2-3-missing-backend-mocks
    content: |
      - [ ] [AGENT] P0. Add mock handlers for backend endpoints that have no frontend equivalent today:
        1. `/api/execution/fills` — trade fill history (use SEED_ORDERS to generate fills)
        2. `/api/execution/sports/bets` — sports bet placement + listing
        3. `/api/execution/defi/execute` — DeFi swap/lending execution
        4. `/api/analytics/period-changes` — period-over-period analytics
        5. `/api/analytics/period-summary` — multi-period performance summary
        6. `/api/analytics/settlements` — settlement records
        7. `/api/risk/exposure` — raw exposure data
        8. `/api/instruments/registry` — browse instrument registry
        9. `/api/execution/grid-configs` — grid config library
        10. `/api/config/mandates` — mandate configuration
        11. `/api/config/fee-schedules` — fee schedule management
      Generate realistic mock data from the instrument snapshot and strategy registry.
    status: todo
  - id: p2-4-restful-url-alignment
    content: |
      - [ ] [AGENT] P1. Fix URL structure mismatches between mock and backend:
        1. Alert actions: change from flat `/api/alerts/acknowledge` to RESTful `/api/alerts/{id}/acknowledge` (also escalate, resolve)
        2. Order mutation: align cancel/amend routes with whatever the backend exposes (see Plan 3)
        3. Ensure all Next.js API routes in `app/api/` proxy to the correct backend service path
    status: todo
  - id: p2-5-seed-data-from-registry
    content: |
      - [ ] [AGENT] P0. Rewrite `lib/mocks/fixtures/mock-data-seed.ts` to derive seed data from the instrument snapshot and strategy registry:
        1. Positions: generate from actual instruments in snapshot (BTC-USDT@BINANCE, ETH-PERP@HYPERLIQUID, aWETH@AAVEV3-ETHEREUM, SPY@NASDAQ, etc.)
        2. Orders: realistic orders using actual instrument keys and venue names
        3. Strategies: use all 37 strategies from system-topology, with correct instrument/venue assignments
        4. Alerts: generate from actual strategy/venue/instrument combinations
        5. Sports: use real fixtures from the snapshot with actual bookmaker names
        Keep seed data consistent — positions should have PnL that matches order fills.
    status: todo
  - id: p2-6-execution-platform-alignment
    content: |
      - [ ] [AGENT] P1. Update `lib/mocks/fixtures/execution-platform.ts`:
        1. Execution algos: align with backend's algo definitions (TWAP, VWAP, IS, SNIPER, ICEBERG plus any from backend)
        2. Venue capabilities: pull from ui-reference-data.json INSTRUMENT_TYPES_BY_VENUE instead of hardcoded
        3. Strategy→algo mapping: use the per-instruction algo mapping from strategy-registry.ts
        4. Recent orders: generate from actual instruments in snapshot
    status: todo
  - id: p2-7-defi-mock-completion
    content: |
      - [ ] [AGENT] P1. Complete DeFi mock data across all DeFi fixture files:
        1. `defi-walkthrough.ts`: Use actual DeFi instruments from snapshot (AAVEV3-ETHEREUM, MORPHO-ETHEREUM, UNISWAPV3-ETHEREUM, etc.)
        2. `defi-swap.ts`: Use real token pairs from snapshot
        3. `defi-lending.ts`: Use actual lending instruments with realistic APY/health factor
        4. `defi-staking.ts`: Use LIDO, ETHERFI, ETHENA instruments from snapshot
        5. `defi-risk.ts`: Realistic health factor, liquidation thresholds from Aave V3 params
        6. `defi-liquidity.ts`: Real pool data from Uniswap/Curve instruments
        All venue names must match UAC canonical names (AAVEV3-ETHEREUM not "Aave").
    status: todo
  - id: p2-8-sports-mock-completion
    content: |
      - [ ] [AGENT] P1. Complete sports mock data:
        1. Use real fixtures from instrument snapshot (EPL, La Liga, Bundesliga, NBA, NFL)
        2. Use actual bookmaker names from UAC (BETFAIR, PINNACLE, BET365, DRAFTKINGS, etc.)
        3. Mock arb opportunities using real fixture structure
        4. Include back/lay odds for exchange venues (Betfair)
        5. Sports ML predictions with realistic model names matching strategy-service
    status: todo
  - id: p2-9-ml-mock-completion
    content: |
      - [ ] [AGENT] P1. Complete ML mock data in `lib/mocks/fixtures/ml-data.ts`:
        1. Model families matching actual strategy types (momentum, basis, sports_ml, options_ml, etc.)
        2. Feature sets from actual feature service outputs
        3. Training runs with realistic metrics (accuracy, Sharpe, etc.)
        4. Deployment status matching testing stages from taxonomy (MOCK→HISTORICAL→LIVE_MOCK→LIVE_TESTNET→STAGING→LIVE_REAL)
    status: todo
  - id: p2-10-typed-fetch-adoption
    content: |
      - [ ] [AGENT] P2. Expand usage of `api-generated.ts` types via the `typedFetch` wrapper. For each Next.js API route in `app/api/`, add type annotations using `ApiResponse<"/path">` from api-generated.ts so that when mock mode is swapped for real, TypeScript catches shape mismatches. Prioritize the high-traffic routes: positions, orders, strategies, market-data, risk.
    status: todo
  - id: p2-11-position-update-on-trade
    content: |
      - [ ] [AGENT] P0. Implement mock state management so that trading actions update positions even in mock mode:
        1. POST `/api/execution/orders` should create an order AND update position state
        2. DeFi execute should update DeFi positions (health factor, collateral, etc.)
        3. Sports bet placement should create a bet position
        4. Order cancellation should update order status
        5. Use MockStateStore pattern (interactive mode with `.local-dev-cache/` persistence)
        This ensures the UI behaves realistically — trade → position update → PnL change.
    status: todo
  - id: p2-12-tests
    content: |
      - [ ] [AGENT] P0. Run `CI=true npm test -- --run` to verify no regressions. Fix any failures. Run `VITE_MOCK_API=true npx vite build` smoke build. Verify all mock endpoints return valid data matching the expected TypeScript types.
    status: todo
---

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
