---
name: frontend-backend-bilateral-plan3-backend-gap-fill
overview:
  Add missing backend API endpoints, fix data shape mismatches, wire all strategies to API, complete
  monitoring/governance
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-api
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: risk-and-exposure-service
    code: C0
    deployment: none
    business: none
  - repo: pnl-attribution-service
    code: C0
    deployment: none
    business: none
  - repo: ml-inference-service
    code: C0
    deployment: none
    business: none
  - repo: position-balance-monitor-service
    code: C0
    deployment: none
    business: none

depends_on: []

todos:
  - id: p3-1-execution-order-mutation
    content: |
      - [ ] [AGENT] P0. Add order mutation endpoints to execution-service and unified-trading-api:
        1. `PUT /execution/orders/{order_id}/cancel` — cancel an open order
        2. `PUT /execution/orders/{order_id}/amend` — amend quantity/price of open order
        3. `GET /execution/fills` — must be exposed in unified-trading-api router (it exists in execution-service but may not be proxied)
        4. `GET /execution/grid-configs` — expose grid config library
        Pre-audit: check if these exist in execution-service but aren't routed in unified-trading-api.
    status: todo
  - id: p3-2-sports-execution-endpoints
    content: |
      - [ ] [AGENT] P0. Ensure sports bet endpoints are fully wired end-to-end:
        1. `POST /execution/sports/bets` — place a sports bet (already in backend, verify mock mode works)
        2. `GET /execution/sports/bets` — list sports bets with filtering
        3. `DELETE /execution/sports/bets/{bet_id}/cancel` — cancel pending bet
        4. Verify the mock state store returns realistic bet data matching UAC canonical sports instrument format
        5. Wire sports venue adapters (BETFAIR, PINNACLE, BET365) in execution-service for mock mode
    status: todo
  - id: p3-3-defi-execution-endpoints
    content: |
      - [ ] [AGENT] P0. Ensure DeFi execution endpoints work end-to-end in mock mode:
        1. `POST /execution/defi/execute` — execute DeFi operation (swap, lend, borrow, stake, etc.)
        2. Response should include all OperationType values (SWAP, LEND, BORROW, REPAY, STAKE, UNSTAKE, ADD_LIQUIDITY, etc.)
        3. Verify it handles all DeFi venues: AAVEV3-ETHEREUM, MORPHO-ETHEREUM, UNISWAPV3-ETHEREUM, CURVE-ETHEREUM, LIDO, ETHERFI
        4. Mock mode should simulate gas costs, health factor changes, position updates
        5. Ensure DeFiSwapResult type is returned with tx_hash, gas_used, effective_price in mock mode
    status: todo
  - id: p3-4-analytics-gap-fill
    content: |
      - [ ] [AGENT] P1. Add missing analytics endpoints to unified-trading-api:
        1. Verify `/analytics/period-changes` is routed (exists in backend, may not be proxied)
        2. Verify `/analytics/period-summary` is routed
        3. Verify `/analytics/settlements` is routed with CRUD (GET + POST)
        4. Add `/analytics/live-batch-delta` — reconciliation view comparing live vs batch positions/PnL
        5. Ensure all analytics endpoints support `mode` (live/batch) and `as_of` params
    status: todo
  - id: p3-5-risk-gap-fill
    content: |
      - [ ] [AGENT] P1. Add missing risk endpoints:
        1. Verify `/risk/exposure` is routed in unified-trading-api
        2. Add `/risk/exposure-types` — breakdown of exposure by type (delta, vega, gamma, funding, basis, etc.)
        3. Add `/risk/defi-health` — DeFi-specific health metrics (health factor, LTV, liquidation distance per protocol)
        4. Verify `/risk/stress-test` is routed (distinct from `/risk/stress`)
        5. Ensure risk endpoints accept category filter (cefi/defi/tradfi/sports) to scope results
    status: todo
  - id: p3-6-strategy-all-37
    content: |
      - [ ] [AGENT] P0. Verify all 37 strategies from system-topology.json are accessible via the API:
        1. `GET /analytics/strategies` should return all 37 with correct metadata
        2. `GET /analytics/strategy-configs` should return config definitions for all 37
        3. Each strategy should have: instruments, venues, timeframe, risk profile, PnL attribution rules
        4. Strategy statuses should reflect actual implementation state (from codex 09-strategy)
        5. Strategies without complete backend implementation should show status=development
        Pre-audit: cross-reference system-topology.json strategies with strategy-service exported strategies.
    status: todo
  - id: p3-7-ml-monitoring-governance
    content: |
      - [ ] [AGENT] P1. Add ML monitoring and governance endpoints:
        1. `GET /ml/monitoring` — model performance monitoring (drift detection, accuracy tracking, prediction distribution)
        2. `GET /ml/governance` — model governance (approval status, audit trail, compliance)
        3. `GET /ml/config` — ML pipeline configuration (feature importance, hyperparameters, training schedule)
        These are needed by the ML section of the UI. Implement in ml-inference-service and route via unified-trading-api.
    status: todo
  - id: p3-8-response-pagination-wrapper
    content: |
      - [ ] [AGENT] P0. Standardise ALL paginated endpoint responses across unified-trading-api to use consistent wrapper:
        ```python
        {
          "data": [...],
          "pagination": {"page": 1, "page_size": 50, "total": 100},
          "mode": "live",  # or "batch"
          "as_of": null    # or ISO datetime for batch mode
        }
        ```
        Audit every router in unified-trading-api. Any endpoint returning a bare list or inconsistent wrapper must be updated. This is the contract the frontend depends on (Plan 2 aligns mock shapes to this).
    status: todo
  - id: p3-9-instrument-registry-endpoint
    content: |
      - [ ] [AGENT] P1. Enhance `/instruments/registry` endpoint:
        1. Return full instrument catalogue with filtering by venue, category, instrument_type, status
        2. Include trading hours, tick size, lot size, fee structure where available
        3. Include `available_since` from instruments-service data
        4. Support pagination
        5. This endpoint is the backend equivalent of the UI's instrument snapshot — must serve the same data.
    status: todo
  - id: p3-10-config-endpoints
    content: |
      - [ ] [AGENT] P2. Add config management endpoints:
        1. `GET /config/mandates` — client mandate definitions
        2. `GET /config/fee-schedules` — fee schedules per venue/instrument type
        3. `POST /config/reload` — trigger config hot-reload (already exists in services, expose via API)
        4. `GET /config/strategies` — strategy configuration (distinct from analytics/strategy-configs)
    status: todo
  - id: p3-11-position-update-flow
    content: |
      - [ ] [AGENT] P0. Ensure the backend updates positions after execution in mock mode:
        1. POST /execution/orders (with fill) → position-balance-monitor-service creates/updates position
        2. POST /execution/defi/execute → updates DeFi position (collateral, debt, health factor)
        3. POST /execution/sports/bets → creates sports bet position
        4. In mock mode with MockStateStore, the state must be consistent: get positions returns positions created by execution
        5. PnL should update accordingly — pnl-attribution-service should reflect new positions
    status: todo
  - id: p3-12-tests-qg
    content: |
      - [ ] [AGENT] P0. Run QG on all affected repos:
        1. `cd unified-trading-api && bash scripts/quality-gates.sh`
        2. `cd execution-service && bash scripts/quality-gates.sh`
        3. `cd strategy-service && bash scripts/quality-gates.sh`
        4. `cd risk-and-exposure-service && bash scripts/quality-gates.sh`
        5. `cd ml-inference-service && bash scripts/quality-gates.sh`
        6. `cd position-balance-monitor-service && bash scripts/quality-gates.sh`
        7. `cd pnl-attribution-service && bash scripts/quality-gates.sh`
        Fix all failures. No regressions in existing tests.
    status: todo
---

## Context

### Problem

17 frontend-expected endpoints have no backend equivalent. 24 backend endpoints have no frontend mock. Response shapes
are inconsistent — some return bare lists, some use `{data, pagination}`. The 37 registered strategies may not all be
accessible via the API. Position state doesn't update after mock execution.

### Pre-Audit Manifest (to be built during execution)

Before modifying each repo, the executing agent must:

1. Read the existing routers in unified-trading-api to verify which endpoints are already wired
2. Check execution-service for existing order mutation, sports bet, DeFi execute implementations
3. Cross-reference system-topology.json strategies with strategy-service `__init__.py` exports
4. Document which endpoints exist but aren't routed vs which need full implementation

### Execution DAG

```
Phase 1 — Pre-Audit (SEQUENTIAL):
  Build manifest of existing vs missing endpoints per service

Phase 2 — Core Execution (PARALLEL):
  p3-1: Order mutation endpoints
  p3-2: Sports execution endpoints
  p3-3: DeFi execution endpoints
  p3-8: Response pagination wrapper

Phase 3 — Analytics & Risk (PARALLEL, depends on Phase 2):
  p3-4: Analytics gap fill
  p3-5: Risk gap fill
  p3-6: Strategy all-37 verification
  p3-9: Instrument registry endpoint

Phase 4 — Supporting (PARALLEL, depends on Phase 3):
  p3-7: ML monitoring/governance
  p3-10: Config endpoints
  p3-11: Position update flow

Phase 5 — Validation (SEQUENTIAL, depends on Phase 4):
  p3-12: QG on all repos
```

### Success Criteria

- **C2**: All endpoints return correct shapes; tests pass per repo
- **C3**: basedpyright + ruff clean on all repos
- **C4**: QG pass on all 7 repos
- **C5**: Quickmerged

### Downstream Impact

Plan 2 (mock alignment) depends on knowing the exact endpoint shapes from this plan. The response wrapper
standardisation (p3-8) defines the contract both sides use.
