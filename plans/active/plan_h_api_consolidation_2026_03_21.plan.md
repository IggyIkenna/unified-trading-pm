---
name: plan-h-api-consolidation
overview:
  "Consolidate 9 domain data API repos into one unified-trading-api with entitlement middleware, WebSocket multiplexing,
  and unified OpenAPI spec"
type: mixed
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-21
completion_gates:
  code: C5
  deployment: D3
  business: none
repo_gates:
  - repo: unified-trading-api
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
depends_on:
  - plan-a-registry-schema-sync
todos:
  # ── Phase 0: Scaffold unified-trading-api repo (SEQUENTIAL) ──
  - id: h-p0-scaffold-repo
    content: |
      - [ ] [AGENT] P0. Create unified-trading-api repo with FastAPI, same structure as existing API repos (main.py, routes/, middleware/, models/)
    status: todo
  - id: h-p0-pyproject
    content: |
      - [ ] [AGENT] P0. Set up pyproject.toml with flat deps (unified-trading-library, unified-internal-contracts, unified-api-contracts, unified-config-interface, unified-cloud-interface, unified-events-interface)
    status: todo
  - id: h-p0-quality-gates
    content: |
      - [ ] [AGENT] P0. Add quality-gates.sh, pre-commit hooks, basedpyright config matching existing API repo standards
    status: todo
  - id: h-p0-health-endpoint
    content: |
      - [ ] [AGENT] P0. Add /health endpoint with mock_mode reporting, version, uptime, dependency status
    status: todo
  - id: h-p0-entitlement-middleware
    content: |
      - [ ] [AGENT] P0. Add entitlement middleware (reads org/role from auth token, filters responses by tier: internal=all, external=scoped per Plan G tiers)
    status: todo
  - id: h-p0-mock-state-store
    content: |
      - [ ] [AGENT] P0. Add MockStateStore integration with shared seed data, DATA_MODE=mock/real switching at app level
    status: todo
  - id: h-p1-workspace-integration
    content: |
      - [ ] [AGENT] P1. Add unified-trading-api to workspace-manifest.json, ui-api-mapping.json (port 8020), dev-start.sh
    status: todo
  # ── Phase 1: Migrate route modules (PARALLEL — each domain independent) ──
  - id: h-p1-market-data
    content: |
      - [ ] [AGENT] P0. market-data domain (from market-data-api): GET /market-data/candles, /market-data/orderbook, /market-data/trades, /market-data/tickers (4 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-execution
    content: |
      - [ ] [AGENT] P0. execution domain (from execution-results-api): GET /execution/orders, /execution/fills, /execution/venues, /execution/algos, /execution/backtests (5 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-positions
    content: |
      - [ ] [AGENT] P0. positions domain (from execution-results-api): GET /positions/active, /positions/summary, /positions/balances (3 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-trading-analytics
    content: |
      - [ ] [AGENT] P0. trading/analytics domain (from trading-analytics-api): GET /analytics/pnl, /analytics/timeseries, /analytics/performance, /analytics/organizations, /analytics/settlements, /analytics/instruments, plus POST/PUT variants (10 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-ml
    content: |
      - [ ] [AGENT] P0. ml domain (from ml-training-api + ml-inference-api): GET /ml/model-families, /ml/experiments, /ml/training-runs, /ml/versions, /ml/deployments, /ml/features, /ml/datasets (7 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-reporting
    content: |
      - [ ] [AGENT] P0. reporting domain (from client-reporting-api): GET /reporting/reports, /reporting/settlements, /reporting/reconciliation (3 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-audit
    content: |
      - [ ] [AGENT] P0. audit domain (from batch-audit-api): GET /audit/events, /audit/compliance, /audit/data-health, /audit/logs (4 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-config
    content: |
      - [ ] [AGENT] P0. config domain (from config-api): GET/PUT /config/system, /config/venues, /config/feature-flags (3 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-alerts
    content: |
      - [ ] [AGENT] P0. alerts domain (NEW, from alerting-service): GET /alerts/list, /alerts/summary, POST /alerts/acknowledge, /alerts/resolve (4 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-risk
    content: |
      - [ ] [AGENT] P0. risk domain (NEW, from risk-and-exposure-service): GET /risk/limits, /risk/var, /risk/greeks, /risk/stress (4 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-instruments
    content: |
      - [ ] [AGENT] P0. data/instruments domain (NEW, from instruments-service): GET /instruments/list, /instruments/catalogue (2 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-deployment
    content: |
      - [ ] [AGENT] P0. deployment domain (proxy to deployment-api): GET /deployment/services, /deployment/deployments, /deployment/builds — reverse proxy to deployment-api backend (3 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-service-status
    content: |
      - [ ] [AGENT] P0. service-status domain (NEW): GET /service-status/health (aggregated), /service-status/feature-freshness (2 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  - id: h-p1-users
    content: |
      - [ ] [AGENT] P1. users domain (NEW): GET /users/organizations, /users/members, /users/subscriptions (3 endpoints)
    status: todo
    blocked_by: h-p0-scaffold-repo
  # ── Phase 2: WebSocket endpoint (SEQUENTIAL after Phase 1) ──
  - id: h-p2-ws-endpoint
    content: |
      - [ ] [AGENT] P0. Add /ws WebSocket endpoint with channel-based multiplexing (subscribe/unsubscribe messages, channel routing)
    status: todo
    blocked_by: h-p1-market-data
  - id: h-p2-ws-channels
    content: |
      - [ ] [AGENT] P0. Implement channels: market-data (ticks), positions (updates), alerts (notifications), health (service status), execution (order updates)
    status: todo
    blocked_by: h-p2-ws-endpoint
  - id: h-p2-ws-mock
    content: |
      - [ ] [AGENT] P0. In mock mode: synthetic ticks from SyntheticDataGenerator, periodic mock alerts, position change simulation
    status: todo
    blocked_by: h-p2-ws-endpoint
  - id: h-p2-ws-real
    content: |
      - [ ] [AGENT] P0. In real mode: subscribe to PubSub topics via UCI get_pubsub_client(), forward events to connected WebSocket clients
    status: todo
    blocked_by: h-p2-ws-endpoint
  - id: h-p2-ws-auth
    content: |
      - [ ] [AGENT] P1. Auth on WebSocket: token validation on connect, reject unauthorized, refresh token support
    status: todo
    blocked_by: h-p2-ws-endpoint
  # ── Phase 3: Seed data + mock mode (SEQUENTIAL after Phase 1) ──
  - id: h-p3-seed-data
    content: |
      - [ ] [AGENT] P0. Create seed_mock_data.py that populates MockStateStore for all 14 domains with realistic data
    status: todo
    blocked_by: h-p1-market-data
  - id: h-p3-reuse-mock
    content: |
      - [ ] [AGENT] P0. Reuse existing API mock_data.py files from 9 repos as starting point, consolidate into unified seed
    status: todo
    blocked_by: h-p3-seed-data
  - id: h-p3-schema-parity
    content: |
      - [ ] [AGENT] P0. Ensure mock responses match real response schemas exactly (same Pydantic models, same field types, no mock-only fields)
    status: todo
    blocked_by: h-p3-seed-data
  - id: h-p3-scenarios
    content: |
      - [ ] [AGENT] P1. Scenario support: MockStateStore seed data varies by MOCK_SCENARIO env var (default, stress, error, empty)
    status: todo
    blocked_by: h-p3-seed-data
  # ── Phase 4: OpenAPI spec generation (SEQUENTIAL after Phase 1) ──
  - id: h-p4-openapi-spec
    content: |
      - [ ] [AGENT] P0. Auto-generate unified OpenAPI spec from FastAPI (all 47+ endpoints in ONE spec, tagged by domain)
    status: todo
    blocked_by: h-p1-market-data
  - id: h-p4-typescript-codegen
    content: |
      - [ ] [AGENT] P0. Run openapi-typescript codegen to produce TypeScript types from unified spec, output to unified-trading-system-ui
    status: todo
    blocked_by: h-p4-openapi-spec
  - id: h-p4-replaces-fragmented
    content: |
      - [ ] [AGENT] P0. Verify unified spec covers all endpoints from 9 old API repos, document any gaps
    status: todo
    blocked_by: h-p4-openapi-spec
  - id: h-p4-ci-drift
    content: |
      - [ ] [AGENT] P1. CI: on commit, regenerate spec + types, fail if drift detected (spec must be committed, not generated at deploy time)
    status: todo
    blocked_by: h-p4-openapi-spec
  # ── Phase 5: Deprecate old API repos (SEQUENTIAL after Phase 4) ──
  - id: h-p5-verify
    content: |
      - [ ] [HUMAN] P1. Verify unified-trading-api covers all endpoints from old repos (market-data-api, execution-results-api, trading-analytics-api, ml-training-api, ml-inference-api, client-reporting-api, batch-audit-api, config-api)
    status: todo
    blocked_by: h-p4-openapi-spec
  - id: h-p5-dev-start
    content: |
      - [ ] [AGENT] P1. Update dev-start.sh to start unified-trading-api instead of 9 separate APIs, update port mapping
    status: todo
    blocked_by: h-p5-verify
  - id: h-p5-ui-api-mapping
    content: |
      - [ ] [AGENT] P1. Update ui-api-mapping.json: one API entry for unified-trading-system-ui pointing to unified-trading-api
    status: todo
    blocked_by: h-p5-verify
  - id: h-p5-deprecate-manifest
    content: |
      - [ ] [AGENT] P2. Mark old API repos as deprecated in workspace-manifest.json (set status: deprecated, note: replaced-by-unified-trading-api)
    status: todo
    blocked_by: h-p5-verify
  - id: h-p5-archive
    content: |
      - [ ] [HUMAN] P2. Archive old API repos (after verification period)
    status: todo
    blocked_by: h-p5-deprecate-manifest
  # ── Phase 6: QG sweep (SEQUENTIAL after all phases) ──
  - id: h-p6-qg
    content: |
      - [ ] [AGENT] P0. Run quality-gates.sh on unified-trading-api — full Pass 1
    status: todo
    blocked_by: h-p4-openapi-spec
  - id: h-p6-basedpyright
    content: |
      - [ ] [AGENT] P0. Run basedpyright on all route modules — zero errors
    status: todo
    blocked_by: h-p6-qg
  - id: h-p6-mock-verify
    content: |
      - [ ] [AGENT] P0. Verify all 47+ endpoints return correct mock data with correct response schemas
    status: todo
    blocked_by: h-p6-qg
  - id: h-p6-entitlement-verify
    content: |
      - [ ] [AGENT] P0. Verify entitlement filtering works (internal=all fields, external=scoped per org tier)
    status: todo
    blocked_by: h-p6-qg
isProject: false
---

# Notes & Context

## Architecture Decision

ONE `unified-trading-api` repo absorbs all 9 domain data API repos. The UI integrates with a single API origin instead
of 9 separate services.

**What stays separate and why:**

- **auth-api** — cross-cutting security concern, token issuance/refresh/RBAC, different lifecycle
- **deployment-api** — mature, own CI/CD, infrastructure orchestration; but proxied through unified-trading-api so the
  UI sees one endpoint

**What gets consolidated (9 repos):**

- market-data-api (4 endpoints)
- execution-results-api (8 endpoints: 5 execution + 3 positions)
- trading-analytics-api (10 endpoints)
- ml-training-api + ml-inference-api (7 endpoints combined)
- client-reporting-api (3 endpoints)
- batch-audit-api (4 endpoints)
- config-api (3 endpoints)

**New domains added (no existing repo):**

- alerts (4 endpoints, from alerting-service)
- risk (4 endpoints, from risk-and-exposure-service)
- instruments (2 endpoints, from instruments-service)
- deployment proxy (3 endpoints, reverse proxy to deployment-api)
- service-status (2 endpoints, health aggregation)
- users (3 endpoints)

**Total: 57 endpoints across 14 domains.**

## Pre-Audit Manifest

| Source Repo           | Domain               | Endpoints                                                                | Action                    |
| --------------------- | -------------------- | ------------------------------------------------------------------------ | ------------------------- |
| market-data-api       | market-data          | candles, orderbook, trades, tickers                                      | Absorb routes + mock data |
| execution-results-api | execution, positions | orders, fills, venues, algos, backtests, positions, summary, balances    | Absorb routes + mock data |
| trading-analytics-api | analytics            | pnl, timeseries, performance, organizations, settlements, instruments    | Absorb routes + mock data |
| ml-training-api       | ml                   | model-families, experiments, training-runs, versions, features, datasets | Absorb routes + mock data |
| ml-inference-api      | ml                   | deployments                                                              | Absorb routes + mock data |
| client-reporting-api  | reporting            | reports, settlements, reconciliation                                     | Absorb routes + mock data |
| batch-audit-api       | audit                | events, compliance, data-health, logs                                    | Absorb routes + mock data |
| config-api            | config               | system, venues, feature-flags                                            | Absorb routes + mock data |
| deployment-api        | deployment           | services, deployments, builds                                            | Proxy only (keep backend) |

## Execution DAG

```
Phase 0: Scaffold (SEQUENTIAL)
  h-p0-scaffold-repo
  h-p0-pyproject
  h-p0-quality-gates
  h-p0-health-endpoint
  h-p0-entitlement-middleware
  h-p0-mock-state-store
  h-p1-workspace-integration
       │
       ▼
Phase 1: Route Modules (ALL PARALLEL)
  h-p1-market-data ─────────┐
  h-p1-execution ────────────┤
  h-p1-positions ────────────┤
  h-p1-trading-analytics ────┤
  h-p1-ml ───────────────────┤
  h-p1-reporting ────────────┤
  h-p1-audit ────────────────┤
  h-p1-config ──────────────┤
  h-p1-alerts ──────────────┤
  h-p1-risk ────────────────┤
  h-p1-instruments ─────────┤
  h-p1-deployment ──────────┤
  h-p1-service-status ──────┤
  h-p1-users ───────────────┘
       │
       ▼ (QG gate: all Phase 1 items pass)
Phase 2: WebSocket (SEQUENTIAL)     Phase 3: Seed Data (SEQUENTIAL)     Phase 4: OpenAPI (SEQUENTIAL)
  h-p2-ws-endpoint                    h-p3-seed-data                      h-p4-openapi-spec
  h-p2-ws-channels                    h-p3-reuse-mock                     h-p4-typescript-codegen
  h-p2-ws-mock                        h-p3-schema-parity                  h-p4-replaces-fragmented
  h-p2-ws-real                        h-p3-scenarios                      h-p4-ci-drift
  h-p2-ws-auth
       │                                    │                                   │
       └────────────────────────────────────┴───────────────────────────────────┘
                                            │
                                            ▼ (QG gate: all Phase 2-4 items pass)
Phase 5: Deprecate Old Repos (SEQUENTIAL)
  h-p5-verify (HUMAN)
  h-p5-dev-start
  h-p5-ui-api-mapping
  h-p5-deprecate-manifest
  h-p5-archive (HUMAN)
       │
       ▼
Phase 6: QG Sweep (SEQUENTIAL)
  h-p6-qg
  h-p6-basedpyright
  h-p6-mock-verify
  h-p6-entitlement-verify
```

## Parallelization Strategy

- **Phase 1** is maximally parallel: all 14 domain route modules are independent and can be implemented by separate
  agents
- **Phases 2, 3, 4** are parallel with each other (WebSocket, seed data, OpenAPI are independent concerns)
- **Phase 5** is sequential (must verify before deprecating)
- **Phase 6** is sequential (must pass QG before verifying endpoints)

## Success Criteria

- **Phase 0:** unified-trading-api scaffolded, `quality-gates.sh` passes with health endpoint only
- **Phase 1:** All 14 route modules return mock data, basedpyright clean per module
- **Phase 2:** WebSocket connects, subscribes to channels, receives mock data in mock mode
- **Phase 3:** `seed_mock_data.py` populates all 14 domains, mock responses match Pydantic schemas
- **Phase 4:** Single OpenAPI spec covers all 57 endpoints, TypeScript types generated
- **Phase 5:** dev-start.sh launches unified-trading-api, old APIs no longer started
- **Phase 6:** Full quality-gates.sh pass, all endpoints verified, entitlement filtering tested

## Impact on Plan E (UI Backend Integration)

Plan E currently assumes integration with 9 separate API repos via a BFF layer. With Plan H, Plan E simplifies:

- No BFF needed — unified-trading-api IS the single API origin
- UI hooks point to one base URL, not 9
- WebSocket is built into unified-trading-api (no separate WS server)
- OpenAPI types come from one spec (Plan A codegen feeds into Plan H's spec)

Plan E's `blocked_by` is updated to include `plan-h-api-consolidation`.

## Plan File References

| Plan | File                                          | Slug                       |
| ---- | --------------------------------------------- | -------------------------- |
| H    | `plan_h_api_consolidation_2026_03_21.plan.md` | `plan-h-api-consolidation` |
