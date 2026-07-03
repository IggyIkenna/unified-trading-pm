---
doc_type: plan
title: frontend-backend-master
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, unified-trading-api]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-21'
overview: 'Master plan for frontend-backend integration: backend Plans A-D+H, then UI Plans E-F'
type: mixed
epic: epic-code-completion
locked_by:
locked_since:
completion_gates: {code: C5, deployment: D3, business: none}
depends_on: []
todos:
- {id: master-plan-a, content: '- [ ] [AGENT] P0. Complete Plan A: Registry & Schema Sync Pipeline (backend-only) — extract 9 missing registries, fix OpenAPI spec, build codegen pipeline, harden error codes, wire CI triggers

    ', status: todo}
- {id: master-plan-b, content: '- [ ] [AGENT] P0. Complete Plan B: Config Hot-Reload (backend-only) — domain config schemas, hot-reload callbacks in 20 services, config publish API, placement remediation

    ', status: todo, blocked_by: plan-a-registry-schema-sync}
- {id: master-plan-c, content: '- [ ] [AGENT] P0. Complete Plan C: Domain Data API Readiness (backend-only) — mock mode completeness, response schema consistency, health endpoints, OpenAPI parity across 12 APIs

    ', status: todo, blocked_by: plan-a-registry-schema-sync}
- {id: master-plan-d, content: '- [ ] [AGENT] P1. Complete Plan D: Testnet & Stress Testing (backend-only) — seed hardening, scenario infrastructure, error code stress tests, performance gates, load testing

    ', status: todo, blocked_by: plan-c-domain-data-api}
- {id: master-plan-h, content: '- [ ] [AGENT] P0. Complete Plan H: API Consolidation — scaffold unified-trading-api, absorb 9 domain data API repos into one, entitlement middleware, WebSocket multiplexing, unified OpenAPI spec, deprecate old API repos

    ', status: todo, blocked_by: plan-a-registry-schema-sync}
- {id: master-plan-g, content: '- [ ] [AGENT] P0. Complete Plan G: Auth & Entitlement Hardening — service access matrix, S2S auth enrollment (all 21 services), API auth standardization (9 API repos), backend entitlement enforcement (7 tiers server-side), org-level data filtering

    ', status: todo}
- {id: master-plan-i, content: '- [ ] [AGENT] P0. Complete Plan I: Client Reporting & Document Management — document infrastructure in UIC/UCI, P&L/settlement/compliance reporting, invoicing with fee calculation, DocuSign integration, document upload/download API, MiFID II regulatory reporting

    ', status: todo, blocked_by: plan-g-auth-entitlement}
- {id: master-plan-e, content: '- [ ] [AGENT] P0. Complete Plan E: UI Backend Integration — BFF scaffold + routes, hook rewire, inline mock deletion, WebSocket server/client, config CRUD, scenario panel, testnet deployment, page migration waves, document management components

    ', status: todo, blocked_by: 'plan-d-testnet-stress-testing, plan-g-auth-entitlement, plan-h-api-consolidation, plan-i-client-reporting-docs'}
- {id: master-plan-f, content: '- [ ] [AGENT] P1. Complete Plan F: UI Quality Gate Hardening — CI/CD pipeline, quality-gates.sh, TypeScript strict mode, 4-mode startup, auth integration, OpenAPI type consumption, Playwright tests

    ', status: todo, blocked_by: plan-e-ui-backend-integration}
isProject: false
---

# Notes & Context

## AUDIT STATUS (Citadel Audit 2026-03-21)

| Plan | Name                      | Claimed Status | Actual Status    | Key Finding                                                                       |
| ---- | ------------------------- | -------------- | ---------------- | --------------------------------------------------------------------------------- |
| A    | Registry & Schema Sync    | Phase 0 done   | Phase 0 done     | Correct. 0/9 new registries extracted (Phase 1 NOT STARTED). 66 empty schemas.    |
| B    | Config Hot-Reload         | Phase 1 done   | Phase 1 NOT DONE | 18/21 services have hollow stub callbacks. 0/21 read getters. Reset to todo.      |
| C    | Domain Data API Readiness | Phase 1 done   | Phase 1 PARTIAL  | 18/21 mock providers are hollow stubs. Reset p1-fix-api-mock-gaps to todo.        |
| D    | Testnet & Stress Testing  | Phase 3 done   | Phase 3 NOT DONE | PerformanceGate/MemoryGate exist in UTL but NOT activated in QG scripts.          |
| E    | UI Backend Integration    | Not started    | Not started      | NEW: UI->API path mismatch + wrong auth header. Added Phase 0B fix todos.         |
| F    | UI Quality Hardening      | Not started    | Not started      | Correct. No changes needed.                                                       |
| G    | Auth & Entitlement        | Phase 1 done   | Phase 1 NOT DONE | 19/21 services have auth files but NOT applied to routes. auth-api is P2 DEV.     |
| H    | API Consolidation         | Not started    | Not started      | unified-trading-api is P3 SCAFFOLD — route modules return mock/stub data. 1 test. |
| I    | Client Reporting & Docs   | Phase 2 done   | Phase 2 done     | Correct. Plan I status is accurate.                                               |

### P0-P4 Maturity Ratings

| Component           | Rating      | Notes                                                    |
| ------------------- | ----------- | -------------------------------------------------------- |
| unified-trading-api | P3 SCAFFOLD | Route modules exist but return mock/stub data. 0 schemas |
| auth-api            | P2 DEV      | No OAuth impl, no production guard, no RBAC              |
| S2S auth enrollment | P2 DEV      | Files exist in 19 services but not applied to routes     |
| Config hot-reload   | P2 DEV      | Boilerplate files exist but not activated at startup     |
| Mock providers      | P2 DEV      | 18/21 are hollow stubs with trivial data                 |
| Perf/Memory gates   | P2 DEV      | Classes exist in UTL, tests exist, but not in QG scripts |
| Registry extraction | P1 STUB     | Script extracts 4/13 categories                          |
| OpenAPI spec        | P1 STUB     | 7 services missing, 66 empty schemas                     |

## 3-Category Data Model

All data flowing between backend and frontend falls into exactly three categories, each with a distinct communication
style and update cadence.

### Category 1: Registry / Fixtures (Build-Time Codegen)

**What:** Venue lists, error classifications, instrument constraints, DeFi protocol registry, risk taxonomy, market data
categories, chain RPC templates, subgraph IDs, capability declarations.

**Properties:**

- Changes only on code deploy (not at runtime)
- Dozens of registries totalling ~3,500 lines of hand-maintained TypeScript
- Current state: duplicated between Python (UAC/UIC) and TypeScript (UI)

**Communication style:** Build-time codegen. UAC/UIC commit triggers CI pipeline that regenerates
`ui-reference-data.json` and runs `openapi-typescript` to produce TS types. No runtime API calls needed for this data.

**Owned by:** Plan A (Registry & Schema Sync Pipeline)

### Category 2: Config (REST + Hot-Reload)

**What:** Feature flags, risk limits, strategy parameters, alerting thresholds, operational toggles, deployment config.

**Properties:**

- Changes at runtime (human edits config, system reloads)
- Needs hot-reload without restart (SSE or short-poll)
- Currently: config-api exists but UI settings panels are hardcoded

**Communication style:** REST endpoints for read/write + SSE or short-poll for change notifications. Config changes
propagate to UI within seconds.

**Owned by:** Plan B (Config Hot-Reload & UI Wiring)

### Category 3: Domain Data (REST + WebSocket)

**What:** Positions, orders, fills, PnL, market data ticks, alerts, execution results, batch audit results, ML
predictions, instrument snapshots.

**Properties:**

- High-frequency updates (sub-second for market data, seconds for positions)
- Requires real-time push for live trading views
- Currently: 14 React Query hooks exist but only 3 pages use them; polling only

**Communication style:** REST for initial load + pagination, WebSocket/SSE for real-time push. BFF layer aggregates
across 9+ backend APIs into a single origin.

**Owned by:** Plan C (Domain Data API + BFF + Real-Time)

## Dependency DAG

```
             Backend Plans                          UI Plans
             ─────────────                          ────────

Plan A (Registry & Schema Sync) ──┐
                                  ├──> Plan B (Config Hot-Reload)
                                  │         [PARALLEL with C, H]
                                  ├──> Plan C (Domain Data API Readiness)
                                  │         [PARALLEL with B, H]
                                  │              │
                                  │              v
                                  │         Plan D (Testnet & Stress)
                                  │              │
                                  ├──> Plan H (API Consolidation)
                                  │         [PARALLEL with B, C, I]
                                  │              │
                                  └──────────────┤
                                                 │
Plan G (Auth & Entitlement) ──┬──> Plan I (Client Reporting & Docs)
       [PARALLEL with A-D]    │         [PARALLEL with H]
                              │              │
                              └──────────────┤
                                             v
                                  Plan E (UI Backend Integration)
                                             │
                                             v
                                  Plan F (UI Quality Hardening)
```

**Backend-first principle:** Plans A-D contain zero UI code. They prepare registries, config infrastructure, API
readiness, and testing infrastructure. Plan E then integrates the UI with all backend work. Plan F hardens the UI
quality to match deployment-ui standards.

Plan A must complete first because:

- Codegen pipeline produces the TypeScript types that Plan E consumes
- OpenAPI spec fixes are prerequisite for correct API client generation
- Error code hardening ensures Plan E's BFF layer has correct error handling

Plans B, C, and H are independent of each other and run in PARALLEL after Plan A. Plan D depends on Plan C (needs
working APIs to stress test). Plan H consolidates 9 domain data API repos into one unified-trading-api. Plan G (Auth &
Entitlement) runs in PARALLEL with Plans A-D+H (no dependencies). Plan I (Client Reporting & Docs) depends on Plan G
(needs org-level auth for document scoping) and runs in PARALLEL with Plan H. Plan E depends on ALL backend plans
(A+B+C+D+H+I) AND Plan G (needs auth integration + document management components). Plan F depends on Plan E.

## Audit Findings Summary

### Audit A: Registry & Schema Sync

- 9 registries in UAC/UIC have NO corresponding TypeScript representation
- `generate_ui_reference_data.py` only extracts 4 of 13 registry categories
- OpenAPI spec missing execution-results-api entirely (serves 3 UIs)
- 68 schemas declared, 11 are empty `{}` objects
- `openapi-typescript` codegen script exists but output is in a `.bak` file, unused
- 3,561 lines of hand-maintained TS constants duplicate Python SSOT
- 18 venue error maps missing from `VENUE_ERROR_MAP`; `aave_plasma` bug in error classifier

### Audit B: Config Hot-Reload

- config-api has endpoints but UI settings panels use hardcoded defaults
- No hot-reload mechanism (config changes require page refresh)
- Feature flags scattered across 6 different env var files
- No config change audit trail in UI
- **CITADEL AUDIT:** 18/21 services have hollow stub callbacks (files exist, not activated at startup, 0 read getters)

### Audit C: Domain Data + BFF

- 151 pages, 0% real backend connectivity
- 14 React Query hooks exist but only 3 pages use them
- URL mismatch: hooks hit `/api/*` but services are at `/{service-name}/api/*`
- Two independent mock systems (7,100 lines inline TS + 16 MSW handlers)
- No WebSocket/SSE for real-time push, only 2-10s polling
- 541 orphan domain models in internal contracts not exposed via API
- **CITADEL AUDIT:** 18/21 service mock providers are hollow stubs; UI sends x-demo-persona instead of JWT Bearer

### Audit D: Testnet & Stress Testing

- Mock mode is "production" (`NEXT_PUBLIC_MOCK_API=true` in `.env.production`)
- No stress test suite for frontend
- No latency simulation capability
- No edge-case scenario injection (empty lists, error states, rate limits)
- Mock data is static, no lifecycle simulation (instrument listing/delisting)
- **CITADEL AUDIT:** PerformanceGate/MemoryGate exist in UTL but NOT activated in any service's QG scripts

### Audit G: Auth & Entitlement (CITADEL AUDIT)

- **S2S auth: 19/21 services have auth files but NOT applied to routes** — dead code
- **auth-api is P2 DEV** — no OAuth implementation, no production guard, no RBAC enforcement
- **unified-trading-api is P3 SCAFFOLD** — route modules return mock/stub data, zero response schemas, 1 test

## Key Architectural Decisions

1. **BFF pattern over direct API calls** — single origin, server-side auth, response aggregation, mock/real switch at
   ONE layer instead of 151 pages
2. **Build-time codegen for registries** — no runtime cost, eliminates drift between Python SSOT and TypeScript
   consumers
3. **SSE for config hot-reload** — lighter than WebSocket for low-frequency updates, already proven in deployment-ui
4. **WebSocket for domain data push** — necessary for sub-second market data and position updates in live trading views
5. **Dual-mode at BFF layer** — `DATA_MODE=mock` vs `DATA_MODE=real` switches the entire stack; no per-page mock/real
   branching

## Plan File References

| Plan | File                                          | Slug                            | Scope        |
| ---- | --------------------------------------------- | ------------------------------- | ------------ |
| A    | `plan_a_registry_schema_sync_2026_03_21.md`   | `plan-a-registry-schema-sync`   | Backend-only |
| B    | `plan_b_config_hot_reload_2026_03_21.md`      | `plan-b-config-hot-reload`      | Backend-only |
| C    | `plan_c_domain_data_api_2026_03_21.md`        | `plan-c-domain-data-api`        | Backend-only |
| D    | `plan_d_testnet_stress_testing_2026_03_21.md` | `plan-d-testnet-stress-testing` | Backend-only |
| E    | `plan_e_ui_backend_integration_2026_03_21.md` | `plan-e-ui-backend-integration` | UI-only      |
| F    | `plan_f_ui_quality_hardening_2026_03_21.md`   | `plan-f-ui-quality-hardening`   | UI-only      |
| G    | `plan_g_auth_entitlement_2026_03_21.md`       | `plan-g-auth-entitlement`       | Backend-only |
| H    | `plan_h_api_consolidation_2026_03_21.md`      | `plan-h-api-consolidation`      | Backend-only |
| I    | `plan_i_client_reporting_docs_2026_03_21.md`  | `plan-i-client-reporting-docs`  | Backend-only |
