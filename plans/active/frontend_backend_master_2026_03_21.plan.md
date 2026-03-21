---
name: frontend-backend-master
overview: "Master plan for frontend-backend integration across registry, config, and domain data"
type: mixed
epic: epic-code-completion
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-21
completion_gates:
  code: C5
  deployment: D3
  business: none
depends_on: []
todos:
  - id: master-plan-a
    content: |
      - [ ] [AGENT] P0. Complete Plan A: Registry & Schema Sync Pipeline — extract 9 missing registries, fix OpenAPI spec, build codegen pipeline, delete 3,561 lines of hand-maintained TS, harden error codes, wire CI triggers
    status: todo
  - id: master-plan-b
    content: |
      - [ ] [AGENT] P0. Complete Plan B: Config Hot-Reload & UI Wiring — unified config API surface, hot-reload via SSE/polling, UI settings panels wired to real config endpoints, env-var matrix (mock/real) propagation
    status: todo
    blocked_by: plan-a-registry-schema-sync
  - id: master-plan-c
    content: |
      - [ ] [AGENT] P0. Complete Plan C: Domain Data API + BFF + Real-Time — Next.js BFF layer, React Query hooks for all 151 pages, WebSocket/SSE push for live data, dual-mode mock/real routing at BFF layer
    status: todo
    blocked_by: plan-a-registry-schema-sync
  - id: master-plan-d
    content: |
      - [ ] [AGENT] P1. Complete Plan D: Testnet & Stress Testing — mock-mode stress tests, edge-case scenario injection, latency simulation, full end-to-end testnet validation across all 9 APIs
    status: todo
    blocked_by: plan-c-domain-data-api
isProject: false
---

# Notes & Context

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
Plan A: Registry & Schema Sync
    |
    +---> Plan B: Config Hot-Reload (PARALLEL with C after A)
    |
    +---> Plan C: Domain Data + BFF + Real-Time (PARALLEL with B after A)
              |
              +---> Plan D: Testnet & Stress Testing
```

```
Phase execution order:

  [Plan A] ──┬──> [Plan B]
             │              ──> [Plan D]
             └──> [Plan C] ─┘
```

Plan A must complete first because:

- Codegen pipeline produces the TypeScript types that Plans B and C consume
- OpenAPI spec fixes are prerequisite for correct API client generation
- Error code hardening ensures Plan C's BFF layer has correct error handling

Plans B and C are independent of each other and run in PARALLEL after Plan A. Plan D depends on Plan C (needs working
BFF + real-time to stress test).

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

### Audit C: Domain Data + BFF

- 151 pages, 0% real backend connectivity
- 14 React Query hooks exist but only 3 pages use them
- URL mismatch: hooks hit `/api/*` but services are at `/{service-name}/api/*`
- Two independent mock systems (7,100 lines inline TS + 16 MSW handlers)
- No WebSocket/SSE for real-time push, only 2-10s polling
- 541 orphan domain models in internal contracts not exposed via API

### Audit D: Testnet & Stress Testing

- Mock mode is "production" (`NEXT_PUBLIC_MOCK_API=true` in `.env.production`)
- No stress test suite for frontend
- No latency simulation capability
- No edge-case scenario injection (empty lists, error states, rate limits)
- Mock data is static, no lifecycle simulation (instrument listing/delisting)

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

| Plan | File                                             | Slug                            |
| ---- | ------------------------------------------------ | ------------------------------- |
| A    | `plan_a_registry_schema_sync_2026_03_21.plan.md` | `plan-a-registry-schema-sync`   |
| B    | (to be created)                                  | `plan-b-config-hot-reload`      |
| C    | (to be created)                                  | `plan-c-domain-data-api`        |
| D    | (to be created)                                  | `plan-d-testnet-stress-testing` |
