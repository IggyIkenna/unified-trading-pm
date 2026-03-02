# Independent Architecture Audit -- 2026-03-01

**Date:** 2026-03-01
**Auditor:** Architecture audit agent (independent of prior workspace audits)
**Scope:** All 62 repositories in the `unified-trading-system-repos` workspace
**Method:** Full codebase inspection -- workspace-manifest.json, TIER-ARCHITECTURE.md, sports-integration-plan.md,
deployment-topology-diagrams.md, LIBRARY-DEPENDENCY-MATRIX.md, INTERNAL_DEPENDENCY_GRAPH.md, coding standards,
quality gates, and cross-repo grep analysis.
**Exclusions:** `.venv*`, `node_modules/`, `build/`, `dist/`, `*.egg-info/`, `sports-betting-services` (external).

---

## Executive Summary

- **62 repos audited** (workspace-manifest.json canonical count).
- **5-tier library architecture** (T0 pure leaves through T4 services) plus API, UI, DevOps, and integration layers.
- **Key finding:** 5 standalone sports services (sports-reference-data-service, sports-odds-data-service,
  sports-odds-processing-service, sports-strategy-service, sports-execution-service) duplicate the existing trading
  pipeline, violating the codex principle: **"sports is an asset class, not a separate system."**
- **Consolidation mandate:** The sports-integration-plan.md explicitly states that existing services should be
  AUGMENTED, not duplicated. Only `features-sports-service` (new domain-specific feature engineering) and
  `unified-sports-execution-interface` (T2 library for betting venue adapters) are architecturally justified as
  new repos.
- **Architecture compliance:** 10 layering violations found, 6 tiering misclassifications, 4 service-to-service
  import violations, 1 critical import-time crash (UMI), and 1 ML schema duplication across 5 repos.
- **Code quality:** basedpyright strict mode target is defined but only partially enforced (8 repos missing config,
  2 repos on "basic" mode, 27+ files excluded from checking). 440+ type suppressions remain.
- **Overall assessment:** The architecture is sound in design but has significant implementation gaps between the
  codex specification and actual codebase state. Phase 1 is approximately 70% complete, Phase 2 approximately 30%,
  and Phase 3 has not started.

---

## 1. Repo Inventory

### Summary Counts

| Category         | Count | Notes                                              |
| ---------------- | :---: | -------------------------------------------------- |
| **Libraries**    |  17   | 8 T0 + 1 T1 + 7 T2 + 1 T3                         |
| **Services**     |  24   | 14 core pipeline + 5 sports + 5 auxiliary           |
| **API Services** |   4   | 3 data APIs + 1 deployment API                     |
| **UIs**          |  11   | React/Vite/TypeScript frontends                    |
| **Infrastructure** | 4  | codex, deployment-v3, deployment-engine, ibkr-infra |
| **DevOps/PM**    |   1   | unified-trading-pm                                 |
| **Test Harness** |   1   | system-integration-tests                           |
| **Total**        |  62   |                                                    |

### Complete Repo Registry (by Merge Level)

```
L0  T0  library          unified-api-contracts              active
L0  T0  library          unified-internal-contracts         active
L0  T0  library          unified-reference-data-interface   active
L0  T0  library          unified-config-interface           active
L0  T0  library          unified-events-interface           active
L0  T0  library          unified-cloud-interface            active
L0  T0  library          matching-engine-library            active
L0  --  infrastructure   unified-trading-codex              active
L0  --  devops           unified-trading-pm                 active
L0  --  infrastructure   ibkr-gateway-infra                 archived

L1  T1  library          unified-trading-services           active

L2  T0  library          execution-algo-library             active
L2  T2  library          unified-feature-calculator-library active

L3  T3  library          unified-domain-client              active
L3  T2  library          unified-market-interface           active
L3  T2  library          unified-ml-interface               active
L3  T2  library          unified-trade-execution-interface  active
L3  T2  library          unified-position-interface         future

L4  T2  library          unified-sports-execution-interface scaffolded
L4  T2  library          unified-defi-execution-interface   active
L4  T4  service          sports-reference-data-service      active
L4  T4  service          sports-odds-data-service           active
L4  T4  service          sports-odds-processing-service     active
L4  T4  service          sports-strategy-service            active
L4  T4  service          sports-execution-service           active

L5  svc service          instruments-service                active
L5  svc service          market-tick-data-service           active
L5  svc service          ml-training-service                active

L6  --  infrastructure   deployment-engine                  scaffolded
L6  --  api-service      deployment-api                     active

L7  svc service          market-data-processing-service     active
L7  svc service          features-calendar-service          active
L7  svc service          features-delta-one-service         active
L7  svc service          features-volatility-service        active
L7  svc service          features-onchain-service           active
L7  svc service          features-sports-service            scaffolded
L7  svc service          features-multi-timeframe-service   active
L7  svc service          features-cross-instrument-service  active
L7  svc service          ml-inference-service               active
L7  svc service          strategy-service                   active
L7  svc service          execution-service                  active
L7  svc service          alerting-service                   active
L7  svc service          pnl-attribution-service            active

L8  svc service          position-balance-monitor-service   active
L8  svc service          risk-and-exposure-service          active
L8  svc service          strategy-validation-service        scaffolded
L8  api api-service      execution-results-api              active
L8  api api-service      market-data-api                    active
L8  api api-service      client-reporting-api               active

L9  ui  ui               strategy-ui                        active
L9  ui  ui               deployment-ui                      scaffolded
L9  ui  ui               batch-audit-ui                     active
L9  ui  ui               trading-analytics-ui               active
L9  ui  ui               live-health-monitor-ui             active
L9  ui  ui               client-reporting-ui                active
L9  ui  ui               logs-dashboard-ui                  active
L9  ui  ui               onboarding-ui                      active
L9  ui  ui               settlement-ui                      active
L9  ui  ui               execution-analytics-ui             active
L9  ui  ui               ml-training-ui                     active

L10 --  infrastructure   unified-trading-deployment-v3      deprecated-splitting
L10 --  test-harness     system-integration-tests           scaffolded
```

---

## 2. Tier Architecture Compliance

### Tier Model (Canonical: TIER-ARCHITECTURE.md)

```
+==============================================================================+
|  TIER 0 -- Pure Leaves (zero unified-* imports; stdlib + externals only)      |
|                                                                              |
|  unified-api-contracts (AC)          unified-cloud-interface (UCLI)           |
|  unified-internal-contracts (UIC)    unified-config-interface (UCI)           |
|  unified-events-interface (UEI)      unified-reference-data-interface (URDI)  |
|  execution-algo-library (EAL)        matching-engine-library (MEL)            |
+======================================+=======================================+
                                       | T0 imports only
+======================================v=======================================+
|  TIER 1 -- Shared Cloud Runtime (imports T0 only)                            |
|                                                                              |
|  unified-trading-services (UTS)                                              |
|  ConfigStore, GCSEventSink, PubSubEventSink, ServiceCLI, BatchOrchestrator   |
|  setup_service, @with_retry, StateStore, GracefulShutdownHandler             |
+=============+========================================+======================+
              | T0+T1                                   | T0+T1
+=============v=================+   +==================v======================+
|  TIER 3 -- Domain Data Client |   |  TIER 2 -- Domain/Market Interfaces      |
|                               |   |                                          |
|  unified-domain-client (UDC)  |   |  unified-market-interface (UMI)          |
|  PATH_REGISTRY, 20 datasets   |   |  unified-trade-execution-interface (UTEI)|
|  14 typed domain clients      |   |  unified-defi-execution-interface (UDEI) |
|  DirectReader/Writer          |   |  unified-sports-execution-interface(USEI)|
|  BigQueryCatalog, GlueCatalog |   |  unified-ml-interface (UML)              |
|  DataCompletionChecker        |   |  unified-feature-calculator-library(UFC) |
|                               |   |  unified-position-interface (UPI)        |
+===============================+   +==========================================+
              |                                         |
              +====================+====================+
                                   | T0-T3 imports (never svc->svc)
              +====================v====================================+
              |  TIER 4 / SERVICES -- 24 service repos                   |
              |  instruments-service, market-tick-data-service            |
              |  market-data-processing-service, features-*              |
              |  ml-training-service, ml-inference-service                |
              |  strategy-service, execution-service, alerting-service    |
              |  pnl-attribution, position-balance-monitor, risk-exposure |
              |  strategy-validation-service                             |
              |  + 5 sports services (consolidation candidates)          |
              +==========================================================+
```

### Import Rules

| Tier    | May import from              | Violation check                                |
| ------- | ---------------------------- | ---------------------------------------------- |
| T0      | stdlib + external only       | Zero `from unified_` imports                   |
| T1      | T0 only                      | No T2/T3 imports                               |
| T2      | T0 + T1                      | No `from unified_domain_client` (T3)           |
| T3      | T0 + T1                      | No T2 imports                                  |
| Service | T0 + T1 + T2 + T3            | Never imports another service                  |
| API/UI  | T0 only (no internal libs)   | Call services via REST/SSE only                |

### Tier Compliance Assessment

**T0 (8 pure leaves):** PARTIALLY COMPLIANT

- 5 of 8 are true pure leaves (AC, UCI, UEI, EAL -- zero unified-* imports).
- UCLI has inter-T0 dep on AC (minor -- both are T0).
- URDI has 4 workspace deps -- should be reclassified to T1.
- MEL has inter-T0 dep on UIC_INT (minor).
- UFC is classified T2 in manifest but has zero unified-* deps -- should be T0.

**T1 (1 shared infra):** COMPLIANT

- UTS correctly imports only from T0 (UCLI, UCI, UEI, UIC_INT).
- No T2 or T3 imports found.

**T2 (7 domain interfaces):** 2 VIOLATIONS

| Violation | Severity | Status  |
| --------- | -------- | ------- |
| UMI imports UDC (T2 -> T3 lateral) | HIGH | Tracked as `cohesion-umi-udc-dep-violation` |
| UML imports UDC (T2 -> T3 upward) | HIGH | NOT tracked -- newly discovered |

**T3 (1 domain client):** 1 VIOLATION

| Violation | Severity | Status |
| --------- | -------- | ------ |
| UDC depends on UTS (T3 -> T1) | CRITICAL | Known -- Phase 2 done criterion not met |

**T4 Services:** 4 SERVICE-TO-SERVICE VIOLATIONS

| Source Service           | Imports From               | Severity | Status  |
| ------------------------ | -------------------------- | -------- | ------- |
| execution-service        | market-tick-data-service    | CRITICAL | Tracked |
| execution-service        | risk-and-exposure-service   | CRITICAL | Tracked |
| market-tick-data-service | instruments-service         | HIGH     | Tracked |
| ml-inference-service     | ml-training-service         | HIGH     | NOT tracked |

**Sports-specific repos:**

| Repo | Tier | Status | Compliant |
| ---- | ---- | ------ | --------- |
| features-sports-service | Tservice (L7) | scaffolded | YES -- correct placement as a new feature service |
| unified-sports-execution-interface | T2 (L4) | scaffolded | YES -- correct T2 library for venue adapters |
| sports-reference-data-service | T4 (L4) | active | VIOLATION -- duplicates instruments-service |
| sports-odds-data-service | T4 (L4) | active | VIOLATION -- duplicates market-tick-data-service |
| sports-odds-processing-service | T4 (L4) | active | VIOLATION -- duplicates market-data-processing-service |
| sports-strategy-service | T4 (L4) | active | VIOLATION -- duplicates strategy-service |
| sports-execution-service | T4 (L4) | active | VIOLATION -- duplicates execution-service |

---

## 3. Sports Consolidation

### Problem Statement

The codex sports-integration-plan.md explicitly defines the core principle:

> **"Sports is an asset class, not a separate system."**

The plan states that existing services should be **AUGMENTED** with sports capabilities, not duplicated.
The service integration summary table in the plan marks every existing pipeline service as "AUGMENT" (change type),
with only `features-sports-service` marked as "CREATE" (new service).

Despite this, 5 standalone sports service repos were created (all at arch_tier T4, merge_level 4):

```
BEFORE (current state -- violates codex principle):
+============================================================+
|  Core Pipeline Services         |  Sports-Specific Services |
|  (CEFI/TRADFI/DEFI)             |  (parallel pipeline)      |
|---------------------------------|---------------------------|
|  instruments-service            |  sports-reference-data    |
|  market-tick-data-service       |  sports-odds-data         |
|  market-data-processing-service |  sports-odds-processing   |
|  strategy-service               |  sports-strategy          |
|  execution-service              |  sports-execution         |
+=================================+===========================+
     ^^ Two parallel pipelines -- DRY violation ^^
```

### Codex Mandate (sports-integration-plan.md, Service Integration Summary)

| Service                        | Change Type | What Should Happen                             |
| ------------------------------ | ----------- | ---------------------------------------------- |
| instruments-service            | AUGMENT     | Add sports parser, fixture matching            |
| market-data-processing-service | AUGMENT     | Add Odds API (batch), Betfair Stream (live)    |
| **features-sports-service**    | **CREATE**  | New: 19 feature categories, time horizons      |
| ml-training-service            | AUGMENT     | Add sports configs, walk-forward validation    |
| ml-inference-service           | AUGMENT     | Add sports model loading                       |
| strategy-service               | AUGMENT     | Add arbitrage, value betting, Kelly criterion  |
| execution-service              | AUGMENT     | Add Betfair, Pinnacle, Polymarket API clients  |

### Consolidation Action Required

```
AFTER (target state -- codex-compliant):
+=============================================================+
|  Unified Pipeline Services (ALL asset classes)               |
|--------------------------------------------------------------|
|  instruments-service        + sports parser, fixtures        |
|  market-tick-data-service   + odds data ingestion            |
|  market-data-processing     + odds processing               |
|  features-sports-service    (NEW -- sports-only features)    |
|  ml-training-service        + sports configs                 |
|  ml-inference-service       + sports model loading           |
|  strategy-service           + sports strategies              |
|  execution-service          + betting venue adapters         |
+==============================================================+
|  Sports Libraries (retained)                                 |
|  unified-sports-execution-interface (T2 adapter protocols)   |
+==============================================================+
```

**Repos to merge / archive:**

| Sports Repo                   | Merge Target                    | Rationale                                  |
| ----------------------------- | ------------------------------- | ------------------------------------------ |
| sports-reference-data-service | instruments-service             | Fixture/team data is instrument data       |
| sports-odds-data-service      | market-tick-data-service        | Odds snapshots are market tick data        |
| sports-odds-processing-service| market-data-processing-service  | Odds aggregation is data processing        |
| sports-strategy-service       | strategy-service                | Betting strategies are trading strategies  |
| sports-execution-service      | execution-service               | Bet placement is order execution           |

**Repos retained (architecturally correct):**

| Repo                              | Reason                                              |
| --------------------------------- | --------------------------------------------------- |
| features-sports-service           | New domain -- 19 sports-specific feature categories |
| unified-sports-execution-interface| T2 library -- venue adapter protocols for Betfair, Pinnacle |

### Phase 3 Batch Ordering (from sports-integration-plan.md)

The plan defines a 5-batch ordering for the sports pipeline, but this ordering should apply to
AUGMENTATION of existing services, not creation of separate repos:

```
Batch A: instruments-service      + sports parser/fixtures
Batch B: market-tick-data-service  + odds ingestion
         market-data-processing    + odds processing
Batch C: features-sports-service   (new service -- connect to Batch B)
Batch D: strategy-service          + sports strategies
Batch E: execution-service         + betting venue execution
```

---

## 4. Deployment Topology

### Batch Mode: 12-Service Pipeline DAG via GCS

In batch mode, every service runs as an independent container. Communication is exclusively through
GCS Parquet files. No inter-service RPCs. No PubSub for data flow.

```
Layer 1: Data Ingestion (root -- no upstream deps)
  +---------------------+     +------------------------+
  | instruments-service  |     | features-calendar-svc  |
  +----------+----------+     +----------+-------------+
             |                            |
             v write to GCS               v write to GCS
  +----------+----------------------------+-------------+
  |                    GCS (Parquet)                     |
  +---+-----------+-------------+-----------+-----------+
      |           |             |           |
      v           v             v           v
Layer 2: Raw Market Data
  +----------------+
  | market-tick-   |
  | data-service   |
  +-------+--------+
          |
          v write to GCS
Layer 3: Processed Data
  +---------------------+
  | market-data-         |
  | processing-service   |
  +----------+----------+
             |
             v write to GCS
Layer 4: Feature Engineering (parallel)
  +------------------+  +------------------+  +------------------+
  | features-delta-  |  | features-        |  | features-        |
  | one-service      |  | volatility-svc   |  | onchain-service  |
  +--------+---------+  +--------+---------+  +--------+---------+
           |                      |                      |
           v                      v                      v
           +----------+-----------+----------+-----------+
                      | write to GCS
Layer 5: Machine Learning
  +------------------+     +------------------+
  | ml-training-svc  | --> | ml-inference-svc |
  +--------+---------+     +--------+---------+
           |                         |
           v                         v
Layer 6: Strategy & Execution
  +------------------+     +------------------+
  | strategy-service | --> | execution-service|
  +------------------+     +------------------+
```

**Key characteristics:**
- Each box is an independent container (VM or Cloud Run job).
- Containers start, read input from GCS, process, write output to GCS, and exit.
- GCS is the only communication mechanism between services.
- Sharding: `category x venue x date` -- each shard is a separate container.
- Sports data flows through the SAME pipeline (with `asset_class=SPORTS` label).

### Live Mode: 7-8 Deployments with Package Embedding

In live mode, upstream services are embedded as Python packages to avoid network hops on
the latency-critical path (target: <2 seconds end-to-end).

```
Deploy 1: TARDIS Persistence (not latency-critical)
  +---------------------------------------------+
  | market-tick-data-service (standalone)        |
  | Source: TARDIS stream --> Sink: GCS          |
  +---------------------------------------------+

Deploy 2: Instruments (standalone)
  +---------------------------------------------+
  | instruments-service (venue APIs)             |
  +---------------------------------------------+

Deploy 3: Calendar Features (standalone, daily timer)
  +---------------------------------------------+
  | features-calendar-service                    |
  +---------------------------------------------+

Deploy 4: Delta-One Features
  +---------------------------------------------+
  | features-delta-one-service                   |
  |   imports market-data-processing  [EMBEDDED] |
  |     imports market-tick-data-svc  [EMBEDDED] |
  +---------------------------------------------+
        |
        | Exchange WebSocket --> ticks --> candles --> features
        v

Deploy 5: Volatility Features (same embedding pattern as Deploy 4)
Deploy 6: Onchain Features (same embedding pattern as Deploy 4)

Deploy 7: Strategy
  +---------------------------------------------+
  | strategy-service                             |
  |   imports features-delta-one     [EMBEDDED]  |
  |   imports ml-inference           [EMBEDDED]  |
  +---------------------------------------------+
        |
        v in-process signals

Deploy 8: Execution (per-client instance)
  +---------------------------------------------+
  | execution-service                            |
  |   imports market-tick-data-svc   [EMBEDDED]  |
  | Exchange WebSocket for live ticks            |
  +---------------------------------------------+
```

**Key characteristics:**
- Solid boxes = separate deployments (containers/VMs).
- `[EMBEDDED]` = Python package imported in-process (zero network hops).
- GCS is for async persistence only, NOT for inter-service communication.
- Each deployment only initializes venues it needs (selective venue initialization).
- TARDIS persistence is separate from the latency path.

### Where Sports Fits (Codex Target)

Sports fits into the EXISTING deployment topology -- not a separate pipeline:

```
Batch:
  instruments-service      (+ sports fixtures as instrument data)
  market-tick-data-service (+ odds snapshots as tick data)
  market-data-processing   (+ odds aggregation as data processing)
  features-sports-service  (NEW container in Layer 4, parallel with delta-one/vol/onchain)
  strategy-service         (+ sports strategies)
  execution-service        (+ betting venue execution via USEI adapters)

Live:
  Deploy 2: instruments-service (+ sports venue APIs -- Betfair, Pinnacle)
  Deploy 9: Sports Features (NEW -- features-sports-service with embedded odds processing)
  Deploy 7: strategy-service (+ sports signals)
  Deploy 8: execution-service (+ Betfair/Pinnacle order placement)
```

---

## 5. Code Quality

### Type Checking (basedpyright)

| Metric                           | Current State | Target |
| -------------------------------- | ------------- | ------ |
| Repos with pyrightconfig.json    | 34/62 (55%)   | 100%   |
| Repos on `strict` mode           | 32/34 (94%)   | 100%   |
| Repos on `basic` mode (violation)| 2 (risk-and-exposure, deployment-v3) | 0 |
| Repos missing pyrightconfig      | 8 (see below) | 0      |
| Production files excluded from checking | 27+ files | 0 |
| `# type: ignore` count           | ~152 (execution-service alone) | <50 total |
| `# noqa` count                   | ~108 across repos | <30 total |
| `# pyright: ignore` count        | ~9 (instruments-service) | 0 |
| **Total type suppressions**      | **~440**      | **<100** |

**Missing pyrightconfig.json:** features-cross-instrument-service, features-multi-timeframe-service,
position-balance-monitor-service, execution-results-api, market-data-api, unified-api-contracts,
unified-events-interface, unified-market-interface.

**Critical:** execution-service pyrightconfig.json includes directory `execution_services` (plural) but
the actual source directory is `execution_service` (singular) -- type checking silently runs on nothing.

### Linting (ruff)

| Metric                          | Current State | Target |
| ------------------------------- | ------------- | ------ |
| Line-length standard            | 120           | 120    |
| Repos using non-standard length | 10 (use 100)  | 0      |
| Repos with minimal rule set     | 3 (`select = ["I"]` only) | 0 |
| Standard rule set               | `["E", "F", "W", "I"]` | All repos |

### Pydantic Response Models

| Area | Status | Notes |
| ---- | ------ | ----- |
| External API boundaries (AC schemas) | PARTIALLY IMPLEMENTED | unified-api-contracts has canonical schemas |
| `dict[str, Any]` at boundaries | 50+ files | UMI, USEI, deployment-v3, execution-service |
| `response.json()` without validation | 12+ occurrences | UMI DeFi adapters, USEI, Deribit |
| `reportAny` setting | "error" in most repos | 3 repos still at "warning" |

### Quality Gate Enforcement

| Metric | Current State | Target |
| ------ | ------------- | ------ |
| Repos with quality-gates.yml CI | 44/62 (71%) | 100% |
| Repos with `\|\| true` bypasses | 4 repos | 0 |
| Repos with no CI enforcement | 13 repos | 0 |
| Min test coverage (quality-gates.sh) | 70% | 70% (enforced) |
| Max file lines | 900 (warn at 700) | 900 |
| Max function lines | 100 | 100 |
| Max method lines | 50 | 50 |
| Max class lines | 500 | 500 |
| McCabe complexity | 10 | 10 |

**`|| true` bypass repos (BLOCKING -- all quality gate steps are non-blocking):**
- matching-engine-library
- unified-defi-execution-interface
- unified-ml-interface
- unified-trade-execution-interface

### Coverage

| Repo | Coverage | Status |
| ---- | -------: | ------ |
| features-sports-service | 84.87% | GOOD |
| instruments-service | ~70% | MEETS GATE |
| unified-trading-services | 29.69% | FAILING (3 test failures) |
| execution-service | N/A | Collection fails without full venv |
| All 5 sports services | 0% | No tests |
| 12 UI repos | 0% | No unit tests in any UI repo |

---

## 6. Discrepancies Found

### Critical Discrepancies

| # | Discrepancy | Severity | Tracked? | Fix |
|---|-------------|----------|----------|-----|
| D1 | 5 standalone sports services duplicate existing pipeline | CRITICAL | Partially (Phase 3 plan exists) | Merge into existing services per codex mandate |
| D2 | 4 service-to-service Python imports break independent deployment | CRITICAL | Yes (P1) | Extract shared schemas to libraries |
| D3 | UMI crashes at import (`os.environ["DEFI_MVP_TOKENS"]`) | CRITICAL | Yes | Replace with config class or `.get()` |
| D4 | UDC depends on UTS (T3 -> T1 violation) | CRITICAL | Yes (Phase 2) | Remove UTS dep, use T0 libs only |
| D5 | execution-service pyrightconfig points to wrong directory | CRITICAL | Yes | Fix `execution_services` -> `execution_service` |
| D6 | ML schemas duplicated across 5 repos with conflicting enums | CRITICAL | Yes | Consolidate to unified-ml-interface |
| D7 | deployment-engine is vendored copy of deployment-v3 (~3,659 lines) | HIGH | No | Delete or make deployment-v3 import from it |
| D8 | 19 repos have pyproject.toml >= 1.0.0 while manifest says 0.x.x | HIGH | Yes | Downgrade versions to match manifest |

### Architecture Discrepancies

| # | Discrepancy | Severity | Fix |
|---|-------------|----------|-----|
| A1 | UML (T2) imports UDC (T3) -- upward tier violation | HIGH | Remove UDC from UML deps |
| A2 | UMI (T2) imports UDC (T3) -- lateral tier violation | HIGH | Remove UDC from UMI deps |
| A3 | URDI classified T0 but has 4 workspace deps | MEDIUM | Reclassify to T1 |
| A4 | UFC classified T2 but has zero unified-* deps | MEDIUM | Reclassify to T0 |
| A5 | MEL (T0) depends on UIC_INT (T0) -- inter-T0 dep | LOW | Acknowledge or inline types |
| A6 | UCLI (T0) depends on AC (T0) -- inter-T0 dep | LOW | Acknowledge or inline types |

### Code Quality Discrepancies

| # | Discrepancy | Severity | Scope |
|---|-------------|----------|-------|
| Q1 | 9+ production files with empty env fallbacks | HIGH | UTS, UDC, execution-service, deployment-v3 |
| Q2 | 16+ files with hardcoded project IDs | HIGH | execution-service, deployment-v3 |
| Q3 | 50+ files with `dict[str, Any]` at boundaries | HIGH | UMI, USEI, deployment-v3 |
| Q4 | 12+ production files with unlogged `except: pass` | MEDIUM | execution-service, UMI, deployment-v3 |
| Q5 | 17+ production files with imports inside functions | MEDIUM | execution-service, UDC, deployment-v3 |
| Q6 | 5+ files exceeding 1500 lines | MEDIUM | execution-service (serializer 2085, config_builder 2006) |
| Q7 | 7 services with direct `google.cloud.pubsub_v1` imports | MEDIUM | Cloud-agnostic violation |
| Q8 | 8 Dockerfiles using old base image name | MEDIUM | `unified-cloud-services` -> `unified-trading-services` |
| Q9 | 208 references to `unified-trading-deployment-v2` (does not exist) | LOW | Codex documentation drift |
| Q10 | 231 skipped tests across 23 repos | MEDIUM | Top: execution-service (49), strategy-service (22) |

### Deployment Discrepancies

| # | Discrepancy | Severity | Scope |
|---|-------------|----------|-------|
| P1 | 5 core services lack Terraform configs | HIGH | cross-instrument, PBM, RAE, PnL, alerting |
| P2 | 23/27 Dockerfiles missing .dockerignore | MEDIUM | All service repos |
| P3 | 12/27 Dockerfiles missing HEALTHCHECK | MEDIUM | All service repos |
| P4 | 2 Dockerfiles use `pip install` instead of `uv pip install` | MEDIUM | ml-training, market-data-processing |
| P5 | Only 4/35 repos notify deployment dashboard | LOW | All repos with cloudbuild.yaml |
| P6 | 22 repos missing AWS buildspec | MEDIUM | Cross-cloud deployment gap |

---

## 7. Recommendations

### Short-Term (P0 -- Blocks Architecture, fix within 1 week)

| # | Action | Impact |
|---|--------|--------|
| S1 | **Freeze 5 sports service repos.** Do not add features. Plan merge into existing services. | Prevents further DRY violations |
| S2 | Remove 4 service-to-service Python deps (extract shared schemas to unified-* libs) | Restores independent deployment |
| S3 | Fix UMI import-time crash (replace `os.environ["DEFI_MVP_TOKENS"]`) | Unblocks all UMI consumers |
| S4 | Fix execution-service pyrightconfig (plural -> singular directory) | Restores type checking on largest service |
| S5 | Fix UTS 3 failing tests (ConfigReloader) and raise coverage above 40% | Core library stability |
| S6 | Remove all `os.environ.get(..., "")` for required config values -- fail fast | Silent misconfiguration prevention |

### Medium-Term (P1 -- Quality, fix within 2-4 weeks)

| # | Action | Impact |
|---|--------|--------|
| M1 | Execute sports consolidation: merge 5 sports repos into existing pipeline services | Codex compliance, DRY |
| M2 | Consolidate ML schemas to unified-ml-interface (5 copies -> 1) | Eliminates runtime type mismatches |
| M3 | Remove UDC -> UTS dependency (Phase 2 completion criterion) | Tier model compliance |
| M4 | Remove UMI -> UDC and UML -> UDC dependencies | T2 purity |
| M5 | Add Pydantic response models at all external API boundaries | Type safety at boundaries |
| M6 | Add pyrightconfig.json to 8 missing repos; upgrade 2 repos to strict mode | Full type checking coverage |
| M7 | Split 5 files exceeding 1500 lines by responsibility | Maintainability |
| M8 | Remove `\|\| true` CI bypasses in 4 library repos | Honest quality gates |
| M9 | Standardize ruff config (line-length=120, full rule set) across all 62 repos | Consistent formatting |
| M10 | Downgrade 19 repo versions to 0.x.x to match manifest | Version policy compliance |

### Long-Term (P2 -- Polish, fix within 4-8 weeks)

| # | Action | Impact |
|---|--------|--------|
| L1 | Add unit tests to all 12 UI repos | Frontend quality |
| L2 | Create shared `@unified-trading/ui-auth` package (8 repos copy-paste GoogleAuth) | DRY for UIs |
| L3 | Add .dockerignore, HEALTHCHECK, tini to all Dockerfiles | Production hardening |
| L4 | Create AWS buildspec for 22 repos | Cross-cloud deployment |
| L5 | Reduce type suppressions from ~440 to <100 | Type safety |
| L6 | Archive sports-betting-services-previous | Clean workspace |
| L7 | Global codex find-replace: `deployment-v2` -> `v3`, remove stale repo refs | Documentation accuracy |
| L8 | Add specs/ folders and 8 canonical docs to all repos | Documentation standardization |
| L9 | Resolve deployment-engine / deployment-v3 duplication | Single source of truth |
| L10 | Complete Phase 2 + Phase 3 service hardening (CDC tests, kill switch, readiness probes) | Production readiness |

---

## 8. SSOT Document Index

All canonical Single Source of Truth documents and their locations.

### Machine-Readable SSOTs

| Document | Location | Owner Repo | Purpose |
| -------- | -------- | ---------- | ------- |
| Repo registry + dependency DAG | `workspace-manifest.json` | unified-trading-pm | Canonical registry, tiers, repo deps, merge ordering |
| Runtime interaction topology | `configs/runtime-topology.yaml` | unified-trading-deployment-v3 | Messaging/storage/API interaction policy by mode |
| Service readiness checks | `configs/dependencies.yaml` | unified-trading-deployment-v3 | Derived from runtime topology + contracts |
| Venue catalog | `configs/venues.yaml` | unified-trading-deployment-v3 | All supported venues |
| Event required fields | `events.py` REQUIRED_EVENT_FIELDS | unified-internal-contracts | Event schema enforcement |
| Audit trail schema | `schemas/audit.py` | unified-internal-contracts | Audit trail data model |
| Error categories + retry | `schemas/errors.py` | unified-internal-contracts | Error taxonomy |

### Documentation SSOTs

| Document | Location | Owner Repo | Purpose |
| -------- | -------- | ---------- | ------- |
| SSOT Master Index | `00-SSOT-INDEX.md` | unified-trading-codex | Navigation hub for all SSOTs |
| Tier Architecture | `04-architecture/TIER-ARCHITECTURE.md` | unified-trading-codex | T0-T3 library tiers + service layer |
| Sports Integration Plan | `04-architecture/sports-integration-plan.md` | unified-trading-codex | Sports as asset class roadmap |
| Deployment Topology | `04-architecture/deployment-topology-diagrams.md` | unified-trading-codex | Batch vs live deployment models |
| Library Dependency Matrix | `05-infrastructure/unified-libraries/LIBRARY-DEPENDENCY-MATRIX.md` | unified-trading-codex | Library import rules + matrix |
| Internal Dependency Graph | `05-infrastructure/unified-libraries/INTERNAL_DEPENDENCY_GRAPH.md` | unified-trading-codex | Full library + service dependency graph |
| Coding Standards | `06-coding-standards/README.md` | unified-trading-codex | All coding rules + document map |
| Quality Gates | `06-coding-standards/quality-gates.md` | unified-trading-codex | QG template + canonical limits |
| Lifecycle Events | `03-observability/lifecycle-events.md` | unified-trading-codex | 11 batch / 12 live required events |
| Instrument Format Spec | `01-domain/` + `instruments-service/docs/` | unified-trading-codex + instruments-service | Canonical instrument schema |
| External API Schemas | `unified_api_contracts/` | unified-api-contracts | 18 venue API dirs, VCR cassettes |
| GCS Bucket Naming | `docs/GCS_AND_SCHEMA.md` | unified-trading-deployment-v3 | Bucket naming conventions |
| Security + Secrets | `07-security/secrets-management.md` | unified-trading-codex | Secret Manager patterns |
| Active Remaining Work | `plans/cursor-plans/consolidated_remaining_work.plan.md` | unified-trading-pm | Current pending tasks |
| Cursor Rules | `cursor-rules/` | unified-trading-pm | Synced to `.cursor/rules/` |
| CI/CD Templates | `05-infrastructure/quickmerge-templates/` | unified-trading-codex | Quickmerge scripts, Cloud Build |

### Visual Artifacts (Generated)

| Artifact | Location | Generated From |
| -------- | -------- | -------------- |
| Workspace DAG (57-repo, 11 levels) | `WORKSPACE_MANIFEST_DAG.svg` | unified-trading-pm/scripts/generate_workspace_dag.py |
| Runtime Topology DAG | `configs/RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg` | unified-trading-deployment-v3/runtime-topology.yaml |

### Layer Ownership

```
unified-trading-codex/          -- Standards (WHAT): architecture decisions, audit methodology
unified-trading-pm/             -- Ops & Tracking: workspace-manifest.json, active plans
unified-trading-deployment-v3/  -- Implementation (HOW): Terraform, configs, deployment delta
Each service repo               -- Service-specific docs (8 canonical docs + specs/)
```

---

## Appendix A: Sports Consolidation -- Detailed Before/After

### Before (5 separate sports repos)

```
CORE PIPELINE (14 services)          SPORTS PIPELINE (5 services)
================================     ================================
instruments-service                  sports-reference-data-service
  |                                    |
  v                                    v
market-tick-data-service             sports-odds-data-service
  |                                    |
  v                                    v
market-data-processing-service       sports-odds-processing-service
  |                                    |
  v                                    v
features-delta-one-service           features-sports-service (correct)
features-volatility-service
features-onchain-service
  |                                    |
  v                                    v
ml-training-service                  (no sports ML service yet)
ml-inference-service
  |                                    |
  v                                    v
strategy-service                     sports-strategy-service
  |                                    |
  v                                    v
execution-service                    sports-execution-service

PROBLEMS:
  - 5 repos duplicating pipeline patterns (ServiceCLI, BatchOrchestrator, GCS I/O)
  - Separate deployment infrastructure needed
  - Separate monitoring, alerting, quality gates
  - Violates "sports is an asset class" principle
  - Each sports service re-implements: config, paths, schemas, CLI, orchestration
```

### After (consolidated -- 2 sports-specific repos retained)

```
UNIFIED PIPELINE (14 services, augmented)
==============================================
instruments-service
  + SportsInstrumentParser, fixture matching, team normalization
  + asset_class=SPORTS label for sports instruments
  |
  v
market-tick-data-service
  + OddsAPI adapter (batch), Betfair Stream adapter (live)
  + asset_class=SPORTS label for odds tick data
  |
  v
market-data-processing-service
  + Odds aggregation, ProcessedOddsOutput
  + asset_class=SPORTS label for processed odds
  |
  v
features-sports-service                    <-- NEW (retained)
  19 feature categories x 4 time horizons
  (T-24h, T-60m, T-0, HT)
  Anti-leakage validation
  |
  v
ml-training-service
  + Sports configs, walk-forward validation, Brier score
  |
  v
ml-inference-service
  + Sports model loading, prediction endpoint
  |
  v
strategy-service
  + Arbitrage, value betting, Kelly criterion
  + Sports-specific backtesting
  |
  v
execution-service
  + Betfair Exchange API (via USEI adapters)
  + Pinnacle Line API (via USEI adapters)
  + Polymarket CLOB API (via USEI adapters)

SPORTS LIBRARIES (retained):
  unified-sports-execution-interface (T2)
    BaseSportsAdapter protocol
    Betfair, Pinnacle, Polymarket adapters
```

---

## Appendix B: Tier Violation Summary Diagram

```
TIER 0  [AC] [UIC] [UCI] [UEI] [UCLI*] [URDI**] [EAL] [MEL*]
         |                        ^  ^       |              |
         |    * inter-T0 dep on AC+--+       |  ** 4 deps   |
         |    * inter-T0 dep on UIC----------+--------------+
         |
TIER 1  [UTS] <-- correctly imports T0 only
         ^
         |
TIER 2  [UMI*] [UTEI] [UDEI] [USEI] [UML*] [UFC**] [UPI]
         |                            |
         | * imports UDC (T3)         | * imports UDC (T3)
         v                            v
TIER 3  [UDC***]
         |
         | *** still depends on UTS (T1) -- should only use T0
         v
TIER 4  [24 services]
         |
         | 4 services import other services:
         |   execution -> market-tick-data, risk-and-exposure
         |   market-tick-data -> instruments
         |   ml-inference -> ml-training
         v

** UFC has zero deps -- should be reclassified to T0
```

---

*Report generated 2026-03-01 by independent architecture audit agent. All findings verified against
workspace-manifest.json (62 repos), codebase grep analysis, and codex canonical documents.*
