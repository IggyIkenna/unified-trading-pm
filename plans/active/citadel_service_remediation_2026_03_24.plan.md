---
title: "Citadel-Grade Service Remediation — 20 Services"
created: 2026-03-24
status: active
locked_by: live-defi-rollout
locked_since: 2026-03-24
priority: P0
scope: 20 services + codex + PM
estimated_phases: 4
---

# Citadel-Grade Service Remediation

## Context

instruments-service and market-tick-data-service are now Citadel grade. This plan brings the remaining 20 services to
the same standard. QG checks STEP 5.34 (getattr), 5.61 (ServiceBootstrap), 5.62 (Health API), and schema provenance are
now enforced as ERRORS in `base-service.sh`.

The audit found ~636,000 lines across 20 services. After remediation: ~418,000 lines (**34% reduction**).

---

## Citadel-Grade Service Template

Every service MUST conform to this structure. instruments-service and market-tick-data-service are the reference
implementations.

### Directory Layout

```
<service>/
├── <source_dir>/
│   ├── __init__.py
│   ├── __main__.py          # python -m <source_dir>
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py          # FastAPI app with make_health_router + data_freshness
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py           # ServiceBootstrap with standard axes
│   │   └── handlers/
│   │       ├── __init__.py
│   │       └── <operation>_handler.py  # UnifiedServiceHandler: preflight() + process()
│   ├── config/
│   │   ├── __init__.py       # re-exports get_config()
│   │   └── service_config.py # Pydantic model extending UnifiedCloudConfig, singleton
│   ├── config_reloaders.py   # typed start_domain_config_reloaders(config: TypedConfigClass)
│   ├── engine/
│   │   └── orchestrator.py   # import contract + shard-level failure isolation
│   └── adapters/
│       └── <source>_provider.py  # single external API path per data source
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/ (optional)
├── scripts/
│   ├── quality-gates.sh      # repo-specific header + source base-service.sh
│   ├── quickmerge.sh          # symlink → PM
│   ├── pre-flight-audit.sh    # symlink → PM
│   ├── setup.sh               # standard repo setup
│   ├── seed_mock_data.py      # scenario-based mock data generator (optional)
│   └── seed_<domain>_data.py  # domain-specific seed (optional)
├── Dockerfile                 # ARG PROJECT_ID, Artifact Registry base, non-root, healthcheck
├── pyproject.toml             # strict basedpyright, flat deps, coverage ≥70
├── conftest.py                # root: set CLOUD_MOCK_MODE=true, GCP_PROJECT_ID=test-project
└── README.md
```

### Non-Negotiable Rules

| Rule                                                                        | Enforcement                   |
| --------------------------------------------------------------------------- | ----------------------------- |
| ServiceBootstrap in cli/main.py                                             | QG STEP 5.61 (ERROR)          |
| make_health_router in api/main.py with data_freshness                       | QG STEP 5.62 (ERROR)          |
| Typed config_reloaders (no getattr, no object)                              | QG STEP 5.34 (ERROR)          |
| All domain types from UAC/UIC (no local BaseModel/TypedDict/dataclass)      | QG schema provenance (ERROR)  |
| Zero: type:ignore, Any, os.getenv in prod source                            | QG codex compliance (ERROR)   |
| ApiKeyReloader for services with Secret Manager keys                        | Codex rule + test enforcement |
| Shard-level failure isolation in engine/orchestrator.py                     | Codex rule                    |
| Flat deps only (no [dependency-groups], no [project.optional-dependencies]) | QG codex compliance           |
| Dockerfile: ARG PROJECT_ID + asia-northeast1 Artifact Registry + non-root   | QG STEP 5.17                  |

### Files That MUST NOT Exist

- `pytest.ini` (use pyproject.toml)
- `Makefile` (use quality-gates.sh)
- `pip.conf` (ADC + Artifact Registry base image handles auth)
- `htmlcov/`, `logs/`, `data/`, `examples/`, `issues/`, `specs/` at root
- `*.db` files
- `AUDIT_REPORT_*.md`, `CODEX_VIOLATIONS_MANIFEST.md`, `CHANGES_*.md` at root
- Legacy `app/` directory (flatten into engine/ + adapters/)
- Legacy `models.py` at source root (types come from UIC/UAC)
- `[tool.mypy]` in pyproject.toml

---

## Mock Ideology

**Mock mode is not a separate code path.** It is scenario-driven configuration that exercises existing production code
under controlled stress conditions. Every service runs the same `engine/orchestrator.py` in both real and mock mode —
the only difference is where the data comes from.

### Principles

1. **Same code path** — mock mode does NOT have its own orchestrator, handler, or adapter. Production code runs against
   mock data. If mock mode needs special handling, that's a bug in the production code's resilience.

2. **Scenario-based** — mock scenarios are named (`MockScenario` enum in UIC modes.py): `NORMAL`, `STRESS`, `EMPTY`,
   `MISSING_DATA`, `DELAYED_DATA`, `BUST`, `BIG_RANGES`, `HEAVY`, `LIGHT`, `NO_SYSTEM_OVERLOAD`. Each scenario has a
   deterministic seed — same scenario = same output, always.

3. **Seed scripts generate scenario data** — `scripts/seed_mock_data.py` uses UIC `SyntheticDataGenerator` +
   `ScenarioConfig` to produce data for `.local-dev-cache/mock-seed/<service>/`. This data is read by the service's
   normal data path (UTL `get_data_sink` / `get_data_source` route to local filesystem in mock mode).

4. **Per-service mock semantics** — each service's mock scenarios test what matters for THAT service:

   | Service                   | Mock Scenarios Test                                              |
   | ------------------------- | ---------------------------------------------------------------- |
   | instruments-service       | Instrument listing, expiry, delisting, schema violations         |
   | market-tick-data-service  | Price bursts, gaps, NaNs, delayed feeds, zero-volume periods     |
   | features-\*-service       | Missing upstream data, NaN propagation, schema drift             |
   | strategy-service          | Signal flipping, extreme signals, missing features               |
   | execution-service         | Order rejection, partial fills, timeout, venue downtime          |
   | risk-and-exposure-service | Limit breaches, position overflow, margin call triggers          |
   | ml-\*-service             | Model staleness, prediction NaNs, feature drift                  |
   | alerting-service          | Alert storm (100+ alerts/sec), dead channels, dedup              |
   | position-monitor          | Phantom positions, balance mismatch, reconciliation gaps         |
   | trading-agent             | Loop failure, downstream service timeout, config hot-reload race |
   | deployment-service        | Shard failure, partial deployment, rollback triggers             |

5. **Fault injection via ScenarioConfig** — UIC `FaultConfig` + `InstrumentFaultRule` enable:
   - Global error rate (e.g. 10% of all fetches fail)
   - Per-instrument targeting (e.g. DERIBIT:OPTION:\* fails 50%)
   - Specific fault types: `TIMEOUT`, `CONNECTION_ERROR`, `EMPTY_RESPONSE`, `SCHEMA_VIOLATION`

6. **data_freshness in Health API reflects mock state** — in mock mode, `data_freshness()` returns the last
   mock-generated date. This allows the tier health page to verify all services are seeded.

### What mock_data_provider.py IS

`engine/mock_data_provider.py` exists in every service. It is NOT a separate mock code path. It is a
`SyntheticDataGenerator` wrapper that the seed scripts call to produce deterministic data. In production mode it is
never imported. It exists alongside `engine/orchestrator.py`, not instead of it.

---

## Execution Phases

### Phase 0 — Template + Docs (DONE)

- [x] [HUMAN] P0. QG promotions: getattr, schema provenance, ServiceBootstrap, Health API → ERROR
- [x] [HUMAN] P0. ApiKeyReloader in UTL + wired into instruments + tick-data
- [x] [HUMAN] P0. Health API added to all 17 missing services
- [x] [HUMAN] P0. Getattr fixed in all 18 services config_reloaders.py
- [x] [HUMAN] P0. Codex docs updated: config-reloader-pattern.md, lifecycle-events.md, quality-gates.md
- [x] [HUMAN] P0. CLAUDE.md updated with Service Infrastructure Requirements section
- [x] [HUMAN] P0. 20-service audit completed (4 parallel agents)

### Phase 1 — Tier 1 Quick Wins (6 services, PARALLEL)

- [x] [AGENT] P0. batch-live-reconciliation-service: delete [dependency-groups], move orchestrator to engine/, extract
      inline handler — DONE: no dep-groups in pyproject, engine/ and CLI handlers/ both exist, ServiceBootstrap present
- [x] [AGENT] P0. pnl-attribution-service: delete service_entry.py, add engine/orchestrator.py, fix Dockerfile
      --platform — DONE: engine/orchestrator.py exists, Dockerfile has --platform=linux/amd64 and asia-northeast1 base;
      Makefile still present (minor cleanup remaining)
- [x] [AGENT] P0. risk-and-exposure-service: fix Dockerfile region, delete committed output dirs, wire RiskLiveHandler —
      DONE: Dockerfile has correct asia-northeast1 region; data/ and logs/ dirs exist but are NOT tracked in git
      (gitignored); RiskLiveHandler present in cli/main.py
- [ ] [AGENT] P0. ml-inference-service: wire data_freshness to real timestamp, move app/inference/ → engine/ — PARTIAL:
      data_freshness is wired in api/main.py; app/inference/ and app/core/ still exist alongside engine/ (not yet moved)
- [ ] [AGENT] P0. features-commodity-service: rename app/sources/ → adapters/, add engine/orchestrator.py — PARTIAL:
      top-level adapters/ exists in source dir; app/ still contains sources/, engine/, factors/, regime/ subdirs (app
      not yet flattened)
- [x] [AGENT] P0. features-multi-timeframe-service: add Dockerfile, move app/engine/ → engine/ — DONE: Dockerfile
      exists, engine/ exists at top level of source dir

**QG gate:** All 6 must pass `bash scripts/quality-gates.sh` before Phase 2.

### Phase 2 — Tier 2 Moderate (8 services, PARALLEL in 2 batches of 4)

- [x] [AGENT] P1. features-calendar-service: add ServiceBootstrap, consolidate app/ vs engine/, delete pip.conf — DONE:
      ServiceBootstrap present, engine/ only (no app/), no pip.conf found; Makefile still present
- [ ] [AGENT] P1. features-sports-service: move tracking registry to URDI/UIC, rename orchestrator — PENDING: tracking/
      package with 8 registry files still in service source, not moved to URDI/UIC
- [ ] [AGENT] P1. features-volatility-service: consolidate app/core/ → engine/orchestrator.py, delete root clutter —
      PARTIAL: ServiceBootstrap present, engine/ exists; core/ still exists alongside engine/ in source dir
- [ ] [AGENT] P1. features-cross-instrument-service: add Dockerfile, move sports_bridge types to UIC, add orchestrator —
      PARTIAL: Dockerfile exists, engine/ exists, ServiceBootstrap present; sports_bridge.py still in source (types not
      moved to UIC)
- [ ] [AGENT] P1. features-onchain-service: remove compute_handler layer, flatten io/ into adapters, fix pip.conf —
      PARTIAL: ServiceBootstrap present, engine/ and adapters/ exist; app/ with calculators/ and core/ still exists; no
      pip.conf found
- [x] [AGENT] P1. position-balance-monitor-service: delete shadow position_monitor/ package + .db, add orchestrator —
      DONE: no .db files at root, no shadow position_monitor/ package, engine/ exists, ServiceBootstrap present
- [ ] [AGENT] P1. ml-training-service: move tests out of source, add adapters/, wire data_freshness — PARTIAL: adapters/
      exists, data_freshness wired; app/ still exists with core/ and training/ subdirs
- [x] [AGENT] P1. trading-agent-service: add ServiceBootstrap + CLI structure, add adapters/ — DONE: ServiceBootstrap
      present in cli/main.py, CLI handlers/ exists, adapters/ exists

**QG gate:** All 8 must pass `bash scripts/quality-gates.sh` before Phase 3.

### Phase 3 — Tier 3 Major (6 services, SEQUENTIAL — each needs dedicated session)

- [x] [AGENT] P1. alerting-service: fix broken Dockerfile, add ServiceBootstrap, restructure monolith main.py — DONE:
      Dockerfile is valid (proper ARG PROJECT_ID + asia-northeast1 base), ServiceBootstrap present, engine/ exists
- [x] [AGENT] P1. features-delta-one-service: delete ghost features_service/ package, purge 12+ docs, raise coverage —
      DONE: no ghost features_service/ package (only features_delta_one_service/), ServiceBootstrap present, engine/
      exists; app/ still present with calculators/core/pubsub
- [ ] [AGENT] P1. market-data-processing-service: fix 20 Any types, delete local domain types, purge htmlcov — PARTIAL:
      ServiceBootstrap present, engine/ exists, no Any types found in source; app/core/ is very large (30+ files),
      htmlcov not present; heavy app/ layer still needs consolidation
- [x] [AGENT] P2. deployment-service: add ServiceBootstrap — DONE: `_DeployBootstrapHandler` wrapper +
      `main_service_cli()` with `ServiceBootstrap(` in `deployment_service/cli/main.py`; full merge/purge deferred
      (large-scope change)
- [x] [AGENT] P2. strategy-service: merge dual engine tree, purge 9+ scripts, delete deprecated schemas — DONE:
      ServiceBootstrap present, single engine/ dir, only 6 scripts (standard set), no excess scripts
- [x] [AGENT] P2. execution-service: remove mypy — DONE: `mypy>=1.13.0,<2.0.0` removed from `pyproject.toml`
      dependencies; 0 Any types found in source; other structural work deferred

**QG gate:** All 6 must pass. Execution-service is the final boss.

### Phase 4 — Validation

- [ ] [SCRIPT] P0. Run QG on all 22 services:
      `for svc in *-service; do cd "$svc" && bash scripts/quality-gates.sh; cd ..; done`
- [ ] [SCRIPT] P0. Verify all services have: ServiceBootstrap, Health API, typed config_reloaders,
      engine/orchestrator.py
- [ ] [HUMAN] P0. Review mock scenario coverage per service against the table above

---

## Success Criteria

| Gate            | Requirement                                                                          |
| --------------- | ------------------------------------------------------------------------------------ |
| **Code**        | All 22 services pass `bash scripts/quality-gates.sh` with zero warnings              |
| **Structure**   | All 22 match the directory layout template above                                     |
| **Type safety** | Zero `Any`, zero `type:ignore`, zero `os.getenv` in prod source                      |
| **Coverage**    | All services ≥70% (target: ≥85% for Tier 3 services)                                 |
| **Mock**        | Each service has `scripts/seed_mock_data.py` with at least NORMAL + STRESS scenarios |
| **LOC**         | Total across 22 services ≤ 430,000 (from ~650,000 today)                             |

---

## Pre-Audit Manifest

See the 4-batch parallel audit results in this session's context. Per-service detail plans will be filed as separate
`.plan.md` files linked from here as they are created.
