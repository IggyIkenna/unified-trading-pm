---
name: plan-c-domain-data-api
overview:
  Backend-only: ensure all 9 API repos + 3 service APIs have complete mock mode, consistent response schemas,
  proper health endpoints, and OpenAPI spec coverage. Prepares backend APIs for UI integration (Plan E).
type: code
epic: epic-code-completion
status: active
locked_by: null
locked_since: null

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
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
    readiness_note: "WebSocket alert push source — must expose HTTP push endpoint."
  - repo: execution-service
    code: C0
    deployment: none
    business: none
    readiness_note: "Kill switch endpoint must be sub-second."

depends_on:
  - registry-completeness-implementation-detail

todos:
  # ── Phase 0: API Mock Mode Audit (PARALLEL) ──
  - id: p0-audit-mock-mode
    content: |
      - [x] [AGENT] P0. Audit all 9 API repos + 3 service HTTP APIs for mock mode completeness. Result: deployment-api, config-api, trading-analytics-api, batch-audit-api, market-data-api, alerting-service = COMPLETE. execution-results-api = PARTIAL (has mock_data.py). client-reporting-api, ml-training-api, ml-inference-api = needs verification. risk-management-service = actually risk-and-exposure-service.
    status: done
  - id: p0-audit-health-endpoints
    content: |
      - [x] [AGENT] P0. Audit all 12 APIs/services for health endpoints. Result: ALL 12 have /health and /readiness endpoints. 5 use make_health_router (best practice), 3 have manual routes, 4 have custom implementations.
    status: done

  # ── Phase 1: API Mock Mode Fixes (PARALLEL) ──
  - id: p1-fix-execution-results-api
    content: |
      - [x] [AGENT] P0. execution-results-api already has mock_data.py, mock_state.py, /health, /readiness. OpenAPI spec coverage is Session 1's responsibility.
    status: done
    blocked_by: p0-audit-mock-mode
  - id: p1-fix-api-mock-gaps
    content: |
      - [ ] [AGENT] P0. AUDIT CORRECTION: 18/21 service mock providers are HOLLOW STUBS — mock_data.py files exist but return trivial/empty data or do not exercise real service logic. Must rework mock providers with realistic data shapes that match Pydantic response models, exercise actual service logic paths (not just return hardcoded dicts), and produce data sufficient for UI rendering. Previously marked done incorrectly.
    status: todo
    blocked_by: p0-audit-mock-mode
  - id: p1-fix-health-gaps
    content: |
      - [x] [AGENT] P1. All 12 APIs/services have /health and /readiness endpoints. No gaps to fix. 5 use make_health_router, 3 have manual routes, 4 have custom implementations.
    status: done
    blocked_by: p0-audit-health-endpoints

  # ── Phase 2: Response Schema Consistency (SEQUENTIAL after Phase 1) ──
  - id: p2-standardize-error-shape
    content: |
      - [ ] [AGENT] P0. Standardize error response shape across all 12 APIs. Every error must return: {"error": {"code": str, "message": str, "details": dict|null}, "request_id": str}. Audit current error responses and fix inconsistencies.
    status: todo
    blocked_by: p1-fix-api-mock-gaps
  - id: p2-standardize-pagination
    content: |
      - [ ] [AGENT] P1. Standardize pagination response shape across all APIs that return lists. Shape: {"data": [...], "pagination": {"total": int, "page": int, "page_size": int, "has_next": bool}}. Audit and fix inconsistencies.
    status: todo
    blocked_by: p1-fix-api-mock-gaps
  - id: p2-data-granularity-labelling
    content: |
      - [ ] [AGENT] P1. Add data granularity labelling to instrument/data type metadata.
      Absorbed from backend_frontend_alignment: add `granularity` field to instrument metadata (tick, block, sampled_5m, timeframe_configurable). CeFi OHLCV=time-sampled, CeFi trades=tick-level, DeFi pool_state=per-block, DeFi swaps=per-block, Sports odds_tick=sampled 5-10m, Sports odds_change=event-driven. Update relevant API responses to include granularity alongside data type.
    status: todo
    blocked_by: p1-fix-api-mock-gaps
  - id: p2-data-history-start-dates
    content: |
      - [ ] [AGENT] P2. Expose per-venue data start dates via API.
      Absorbed from backend_frontend_alignment: deployment-service already has `expected-start-dates` per service. Expose via API: GET /config/expected-start-dates/{service_name}. Show "Data available since Sep 2019" per venue in catalogue. Cloud location per instrument: add cloud_locations field (["gcp", "aws"]) to instrument metadata.
    status: todo
    blocked_by: p1-fix-api-mock-gaps
  - id: p2-openapi-schema-parity
    content: |
      - [ ] [AGENT] P0. Verify OpenAPI spec matches actual API responses. For each API: call every endpoint in mock mode, validate response against OpenAPI schema. Fix any schema mismatches. Run cassette parity tests: cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py.
    status: todo
    blocked_by: p1-fix-execution-results-api

  # ── Phase 3: QG Sweep (SEQUENTIAL after Phase 2) ──
  - id: p3-qg-sweep
    content: |
      - [ ] [SCRIPT] P0. QG sweep across all 12 affected repos. Run quality-gates.sh on each: unified-api-contracts, deployment-api, config-api, execution-results-api, trading-analytics-api, batch-audit-api, client-reporting-api, ml-training-api, ml-inference-api, market-data-api, alerting-service, execution-service. All must pass.
    status: todo
    blocked_by: p2-openapi-schema-parity

isProject: false
---

# Plan C: Domain Data API Backend Readiness

## Context

Backend API audit findings (2026-03-21):

- **12 APIs/services** need mock mode verification (9 API repos + 3 service HTTP APIs)
- **execution-results-api** entirely missing from OpenAPI spec (serves 3 UIs)
- **541 orphan domain models** in backend not exposed via API
- Inconsistent error response shapes across APIs
- Missing health/ready endpoints in some services

**CITADEL AUDIT UPDATE (2026-03-21):** 18/21 service mock providers are hollow stubs — mock_data.py files were created
but return trivial/empty data that does not exercise real service logic. The "all 9 API repos have mock mode" finding
was premature; the files exist but the data quality is insufficient for UI rendering or realistic testing. Phase 1
p1-fix-api-mock-gaps has been reset to NOT DONE.

NOTE: All UI work (BFF scaffold, BFF routes, hook rewire, inline mock deletion, WebSocket server/client, MSW alignment,
page migration waves) has been moved to Plan E (UI Backend Integration). This plan ensures the backend APIs are ready
for that integration.

## Execution DAG

```
Phase 0 (PARALLEL — audit mock mode + health endpoints)
    |
    v
Phase 1 (PARALLEL — fix mock mode gaps + health gaps)
    |
    v  [QG gate: all APIs green]
Phase 2 (SEQUENTIAL — standardize response schemas, OpenAPI parity)
    |
    v  [QG gate: all 12 repos green]
Phase 3 (QG sweep)
    |
    v
  DONE
```

## API Registry (Backend Readiness Targets)

| Backend Service         | Port | Key Endpoints            | Mock Mode | Health |
| ----------------------- | ---- | ------------------------ | --------- | ------ |
| deployment-api          | 8004 | deploy, status, rollback | TBD       | TBD    |
| config-api              | 8006 | CRUD, publish, history   | TBD       | TBD    |
| execution-results-api   | 8008 | backtest, analysis       | TBD       | TBD    |
| trading-analytics-api   | 8010 | PnL, positions, risk     | TBD       | TBD    |
| batch-audit-api         | 8012 | batch status, audit      | TBD       | TBD    |
| client-reporting-api    | 8014 | reports, exports         | TBD       | TBD    |
| ml-training-api         | TBD  | experiments, models      | TBD       | TBD    |
| ml-inference-api        | TBD  | predictions, status      | TBD       | TBD    |
| market-data-api         | TBD  | OHLCV, trades, book      | TBD       | TBD    |
| alerting-service        | TBD  | rules, history, ack      | TBD       | TBD    |
| execution-service       | TBD  | orders, fills, kill      | TBD       | TBD    |
| risk-management-service | TBD  | metrics, limits          | TBD       | TBD    |

Port SSOT: `unified-trading-pm/scripts/dev/ui-api-mapping.json` TBD values will be populated by Phase 0 audit tasks.

## Cross-Plan Note: client-reporting-api Enhancement

client-reporting-api enhancement (invoicing, compliance reporting, DocuSign integration, document management) is owned
by **Plan I** (`plan_i_client_reporting_docs_2026_03_21.md`). Plan C ensures client-reporting-api has proper mock mode
and consistent response schemas. Plan I builds the business features on top of that foundation.

## Success Criteria

| Phase | Gate  | Criteria                                                                                  |
| ----- | ----- | ----------------------------------------------------------------------------------------- |
| 0     | Audit | Gap manifest for mock mode and health endpoints across all 12 APIs                        |
| 1     | C4    | All APIs return valid mock data, all have /health + /ready, execution-results-api in spec |
| 2     | C4    | Standard error shape, standard pagination, OpenAPI schema parity verified                 |
| 3     | C5    | All 12 repos pass quality-gates.sh                                                        |
