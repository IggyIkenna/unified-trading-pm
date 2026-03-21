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
      - [ ] [AGENT] P0. Audit all 9 API repos + 3 service HTTP APIs for mock mode completeness. For each API: verify CLOUD_MOCK_MODE=true returns valid sample data, response schemas match OpenAPI spec, error responses use standard error shape. APIs: deployment-api, config-api, execution-results-api, trading-analytics-api, batch-audit-api, client-reporting-api, ml-training-api, ml-inference-api, market-data-api. Service APIs: alerting-service, execution-service, risk-management-service. Output: gap manifest per API.
    status: todo
  - id: p0-audit-health-endpoints
    content: |
      - [ ] [AGENT] P0. Audit all 12 APIs/services for health endpoints. Each must expose GET /health (200 OK) and GET /ready (checks downstream deps). Verify: health endpoints work in mock mode, return correct status when dependencies are unavailable.
    status: todo

  # ── Phase 1: API Mock Mode Fixes (PARALLEL) ──
  - id: p1-fix-execution-results-api
    content: |
      - [ ] [AGENT] P0. Fix execution-results-api: add complete mock mode (CLOUD_MOCK_MODE=true returns sample backtest results, analysis data). Add OpenAPI spec coverage (currently missing entirely from spec). Ensure response schemas match Pydantic models.
    status: todo
    blocked_by: p0-audit-mock-mode
  - id: p1-fix-api-mock-gaps
    content: |
      - [ ] [AGENT] P0. Fix mock mode gaps identified in p0-audit-mock-mode for remaining APIs. Each API must return realistic sample data shape-matching production responses when CLOUD_MOCK_MODE=true.
    status: todo
    blocked_by: p0-audit-mock-mode
  - id: p1-fix-health-gaps
    content: |
      - [ ] [AGENT] P1. Fix health endpoint gaps identified in p0-audit-health-endpoints. Add missing /health and /ready endpoints. Standardize response shape: {"status": "ok"|"degraded"|"error", "checks": {...}}.
    status: todo
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
by **Plan I** (`plan_i_client_reporting_docs_2026_03_21.plan.md`). Plan C ensures client-reporting-api has proper mock
mode and consistent response schemas. Plan I builds the business features on top of that foundation.

## Success Criteria

| Phase | Gate  | Criteria                                                                                  |
| ----- | ----- | ----------------------------------------------------------------------------------------- |
| 0     | Audit | Gap manifest for mock mode and health endpoints across all 12 APIs                        |
| 1     | C4    | All APIs return valid mock data, all have /health + /ready, execution-results-api in spec |
| 2     | C4    | Standard error shape, standard pagination, OpenAPI schema parity verified                 |
| 3     | C5    | All 12 repos pass quality-gates.sh                                                        |
