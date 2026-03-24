**Naming note (2026-03-24):** Historical snapshot. Active API/UI surface: `scripts/dev/ui-api-mapping.json`,
`workspace-manifest.json`, and workspace-root `archive/README.md`.

---

# System Audit Report — 2026-03-08

**Auditor:** Claude Code (automated codebase scan) **Date:** 2026-03-08 **Scope:** All active service repos in workspace
(excl. archive/, .venv*, typings/, test*) **Prior audit:** audit_remediation_2026_03_08 (all 21 Wave 1/2 todos
completed)

---

## Section Scores

| Section                 | Score               | Result | Notes                                                                             |
| ----------------------- | ------------------- | ------ | --------------------------------------------------------------------------------- |
| 1. Workspace Governance | (see prior session) | PASS   | Completed in previous session                                                     |
| 2. Code Quality         | see below           | WARN   | 10 large files (all archive/build), 2 active bare excepts                         |
| 3. Security             | see below           | WARN   | S2S auth on 3/4 external APIs; exec-service gcs_service.py still uses os.getenv   |
| 4. Architecture         | see below           | WARN   | 1 UTL boto3 import; deployment-service/api use direct cloud SDK at boundary       |
| 5. Schema Governance    | see below           | WARN   | Float prices in prediction_market_arb.py; naive datetime in websocket/derivatives |
| 6. Observability        | see below           | WARN   | /health missing on 7 of 14 services; OTel init on 4 of 14 services                |
| 7. Deployment           | N/A                 | N/A    | Requires live infra — not assessable from codebase                                |
| 8. Technical Debt       | see below           | WARN   | 48 TODO/FIXME; 5 except ImportError; 107 deprecated refs                          |

**Overall Grade: CONDITIONAL PASS** — 0 FAILs, 6 WARNs across assessable sections.

---

## Section 2 — Code Quality

| Criterion                            | Target | Actual                                                                                  | Result |
| ------------------------------------ | ------ | --------------------------------------------------------------------------------------- | ------ |
| `# type: ignore` count               | < 20   | 12 (all in UCI typings stubs)                                                           | PASS   |
| `os.getenv` / `os.environ` in prod   | 0      | 15 violations (excl. approved bootstrap, UCI constants, providers, archive, pm scripts) | WARN   |
| Bare `except:` / `except Exception:` | 0      | 2 (strategy-service signal_publisher.py)                                                | WARN   |
| Files > 900 lines (prod source)      | 0      | 1 (deployment-service/configs/generate_topology_svg.py: 974L)                           | WARN   |

**Key violations:**

- `execution-service/execution_service/utils/gcs_service.py` — 9 `os.getenv` calls still present (remnant of Wave 1
  remediation, dual-path file in `execution_service/` directory)
- `ml-training-service/ml_training_service/config.py` — `os.environ["USE_MOCK_FEATURES"]` setter
- `strategy-service/strategy_service/engine/core/signal_publisher.py` — 2 bare `except Exception:` blocks
- `deployment-service/configs/generate_topology_svg.py` — 974 lines (just above 900L threshold; is a config/script not a
  service module)

**Code Quality Score: WARN** (target is 0 violations; 3 minor breaches, 0 architectural violations)

---

## Section 3 — Security

| Criterion                                             | Target  | Actual                                                                                                     | Result |
| ----------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------- | ------ |
| Hardcoded API keys                                    | 0       | 0                                                                                                          | PASS   |
| os.getenv with KEY/SECRET/TOKEN in prod               | 0       | 3 (instruments-service scripts only — GITHUB_TOKEN for CI)                                                 | PASS   |
| S2S auth (`verify_service_token` / `X-Service-Token`) | present | 26 occurrences across client-reporting-api, unified-trading-api, market-data-api, unified-config-interface | WARN   |

**Notes:**

- No hardcoded secrets found in any production source file.
- `instruments-service/scripts/run_quality_gates.py` uses `os.getenv("GITHUB_TOKEN")` — this is in a CI helper script,
  not service source, so acceptable.
- S2S auth is implemented on **3 of 4 external-facing APIs** (client-reporting-api, unified-trading-api,
  market-data-api). `deployment-api` does not have `verify_service_token`; it uses a different auth mechanism. Needs
  verification.
- `AUTH_FAILURE`, `SECRET_ACCESSED`, `CONFIG_CHANGED` event logging — not spot-checked in this pass (requires UEI event
  type enumeration).

**Security Score: WARN** (no hard fails; S2S auth coverage needs confirmation on deployment-api)

---

## Section 4 — Architecture

| Criterion                                              | Target       | Actual                       | Result |
| ------------------------------------------------------ | ------------ | ---------------------------- | ------ |
| T0 not importing T3 (exec/strategy from T0 libs)       | 0 violations | 0                            | PASS   |
| No cross-service Python imports (strategy → execution) | 0 violations | 0                            | PASS   |
| No direct `google.cloud` / `boto3` outside UCI         | 0 violations | 2 files outside UCI boundary | WARN   |

**Boundary violations found:**

1. `unified-trading-library/unified_trading_library/core/logging.py` — `import boto3  # noqa: F401`
   - UTL is T1; boto3 import is a side-effect probe (noqa suppressed), not production usage. Should be removed or moved
     to UCI.
2. `unified-api-contracts/unified_api_contracts/unified_api_contracts_external/cloud_sdks/schemas/compute.py`
   - Contains a docstring reference to `google.cloud.compute_v1` — not a code import, just documentation text.
     Technically a false positive.

**Note:** `deployment-service` and `deployment-api` have deliberate direct cloud SDK usage at the **deployment
control-plane boundary** — this is architecturally justified as deployment is the cloud orchestration boundary, not a
business service. These are excluded from the violation count.

**Architecture Score: WARN** (1 real violation in UTL logging.py; T0→T3 boundary intact; no cross-service imports)

---

## Section 5 — Schema Governance

| Criterion                                    | Target | Actual                                           | Result |
| -------------------------------------------- | ------ | ------------------------------------------------ | ------ |
| No `float` price fields in canonical schemas | 0      | Violations in prediction_market_arb.py           | WARN   |
| All timestamps use `AwareDatetime`           | all    | Naive `datetime` in websocket.py, derivatives.py | WARN   |

**Float price violations** (`unified-api-contracts/unified_api_contracts/schemas/`):

- `prediction_market_arb.py`: `yes_bid: float`, `yes_ask: float`, `no_bid: float | None`, `no_ask: float | None`,
  `sportsbook_implied_prob: float`, `polymarket_yes_mid: float`, `discrepancy_bps: float`
- `websocket.py`: `latency_ms: float | None`, `ping_interval_seconds: float` (non-price floats — acceptable)

**Canonical price schemas using Decimal correctly:** `derivatives.py`, `defi.py`, `analytics.py` all use
`price: Decimal`. The float issue is isolated to the prediction market arbitrage schema.

**Naive datetime violations** (`unified-api-contracts/unified_api_contracts/schemas/`):

- `websocket.py`: 5 fields typed as `datetime` (not `AwareDatetime`)
- `derivatives.py`: `timestamp: datetime`, `next_funding_time: datetime | None`, `timestamp: datetime`

**Schema Governance Score: WARN** (isolated to prediction_market_arb.py floats and websocket/derivatives naive
timestamps; core CeFi/TradFi schemas are correct)

---

## Section 6 — Observability

| Criterion                        | Target       | Actual                                                      | Result |
| -------------------------------- | ------------ | ----------------------------------------------------------- | ------ |
| `/health` on all API services    | 14/14        | 7/14                                                        | WARN   |
| `/readiness` on all API services | 14/14        | 6/14                                                        | WARN   |
| Prometheus metrics               | all services | 12/14 (deployment-api=0, unified-trading-api=0)             | WARN   |
| OTel `init_tracing` at startup   | all services | 4/14 (execution, strategy, risk-and-exposure, ml-inference) | WARN   |

**`/health` endpoint coverage:**

| Service                          | /health              | /readiness |
| -------------------------------- | -------------------- | ---------- |
| alerting-service                 | YES                  | YES        |
| client-reporting-api             | YES                  | YES        |
| deployment-api                   | YES (at /api/health) | NO         |
| unified-trading-api              | YES                  | YES        |
| market-data-api                  | YES                  | YES        |
| risk-and-exposure-service        | YES                  | YES        |
| position-balance-monitor-service | YES                  | YES        |
| execution-service                | NO                   | NO         |
| strategy-service                 | NO                   | NO         |
| instruments-service              | NO                   | NO         |
| market-data-processing-service   | NO                   | NO         |
| market-tick-data-service         | NO                   | NO         |
| ml-inference-service             | NO                   | NO         |
| ml-training-service              | NO                   | NO         |

**Prometheus gaps:** `deployment-api` and `unified-trading-api` have 0 Prometheus usage.

**OTel gaps:** Only 4 services have `init_tracing` at startup; 10 services have no OTel instrumentation.

**Observability Score: WARN** (significant gap — 7 services missing health endpoint; OTel coverage at 29%)

---

## Section 8 — Technical Debt

| Criterion                                       | Target  | Actual                                                            | Result |
| ----------------------------------------------- | ------- | ----------------------------------------------------------------- | ------ |
| `TODO` / `FIXME` count (prod, excl. GH-BACKLOG) | minimal | 48                                                                | WARN   |
| Deprecated symbol references                    | minimal | 107 (most in UCI typings stubs and DeFi adapters — legitimate)    | PASS   |
| `try/except ImportError` fallbacks              | 0       | 5 (execution_service/ symlinked dir + unified-trading-pm scripts) | WARN   |

**TODO breakdown (top clusters):**

- `instruments-service/instruments_service/app/core/adapter_loader.py` — 9 TODOs (deferred adapter imports)
- `ml-training-service/ml_training_service/ml/model_registry.py` — 2 TODOs (explicit import mapping)
- `unified-market-interface` (venue_config.py) — 3 TODOs (Balancer future implementation)
- `deployment-api` — 1 TODO (Prometheus middleware pending)
- `unified-trading-api` — 1 TODO (extraction HTTP boundary)

**`except ImportError` violations:**

- `execution_service/utils/gcs_service.py` — 2 blocks (this is the `execution_service/` symlinked/duplicate directory;
  main `execution-service/` was remediated in Wave 1/2)

**Deprecated references:** 107 total; majority in `unified-cloud-interface/typings/` (Google stub files — not production
code) and `unified-market-interface` DeFi adapters where external APIs have been deprecated. No production service code
raises `DeprecationWarning` inappropriately.

**Technical Debt Score: WARN** (48 TODOs above threshold; ImportError fallbacks in execution_service/ symlink dir need
cleanup)

---

## Overall Grade

**CONDITIONAL PASS**

- 0 FAILs
- 6 WARNs (Code Quality, Security, Architecture, Schema Governance, Observability, Technical Debt)
- 1 N/A (Deployment — requires live infra)
- 1 PASS carry-forward (Workspace Governance — prior session)

---

## Top 5 Remaining Concerns

### 1. Observability Gap — Health/Readiness/OTel Missing on 7+ Services [WARN]

**Impact:** Services have no standardized health probes — Kubernetes liveness/readiness checks will fail; OTel traces
are absent for most of the pipeline. **Files:**

- `execution-service/execution_service/api/app.py` — no `/health` route
- `strategy-service/strategy_service/` — no `/health` route
- `instruments-service/`, `market-data-processing-service/`, `market-tick-data-service/`, `ml-inference-service/`,
  `ml-training-service/` — all missing `/health` **Fix:** Add a `@app.get("/health")` returning `{"status": "ok"}` and
  `@app.get("/readiness")` to each CLI-driven service's FastAPI/ASGI app.

### 2. `execution_service/utils/gcs_service.py` — Dual Directory with os.getenv + ImportError [WARN]

**Impact:** `execution_service/` (at workspace root) appears to be a stale copy or symlink of `execution-service/`; it
still contains the pre-remediation `gcs_service.py` with 9 `os.getenv` calls and 2 `except ImportError` blocks that were
supposed to be cleaned in Wave 1. **File:**
`/Users/ikennaigboaka/Code/unified-trading-system-repos/execution_service/utils/gcs_service.py` **Fix:** Determine if
`execution_service/` is a symlink or stale copy; if stale, delete or sync it with the remediated `execution-service/`
version.

### 3. Float Price Fields in prediction_market_arb.py Schema [WARN]

**Impact:** Prediction market arbitrage schema uses `float` for bid/ask prices — susceptible to precision loss in
financial calculations. Violates schema governance rule requiring `Decimal` for all price fields. **File:**
`unified-api-contracts/unified_api_contracts/schemas/prediction_market_arb.py` **Fix:** Replace `float` with `Decimal`
for all price/probability fields; `discrepancy_bps: float` may remain as it is a metric not a financial price.

### 4. Naive `datetime` in websocket.py and derivatives.py [WARN]

**Impact:** Timezone-naive `datetime` fields in canonical schemas risk silent UTC assumption failures across venue
adapters. Violates the AwareDatetime standard. **Files:**

- `unified-api-contracts/unified_api_contracts/schemas/websocket.py` — 5 naive datetime fields
- `unified-api-contracts/unified_api_contracts/schemas/derivatives.py` — 3 naive datetime fields **Fix:** Replace
  `datetime` with `AwareDatetime` from `pydantic` in all timestamp fields.

### 5. 48 TODOs in Production Code — Deferred Adapter Imports in instruments-service [WARN]

**Impact:** `instruments-service/instruments_service/app/core/adapter_loader.py` has 9 deferred adapter imports wrapped
in `TODO` comments (Uniswap V2/V3/V4, Aave, Curve, Balancer, Morpho, Euler, Fluid). These are lazy imports that could
silently fail at runtime if the adapter is loaded but the import path has changed. **File:**
`instruments-service/instruments_service/app/core/adapter_loader.py` **Fix:** Convert to explicit top-level imports with
proper error handling, or raise a structured `NotImplementedError` with adapter name — not silent `TODO` comments.

---

## Metrics Summary

| Metric                                  | Count | Threshold | Status |
| --------------------------------------- | ----- | --------- | ------ |
| `# type: ignore`                        | 12    | < 20      | PASS   |
| `os.getenv` violations (active prod)    | 15    | 0         | WARN   |
| Bare `except` / `except Exception:`     | 2     | 0         | WARN   |
| Files > 900 lines (prod source only)    | 1     | 0         | WARN   |
| Hardcoded secrets                       | 0     | 0         | PASS   |
| S2S auth implementations                | 26    | all APIs  | WARN   |
| T0→T3 boundary violations               | 0     | 0         | PASS   |
| Cross-service Python imports            | 0     | 0         | PASS   |
| Direct cloud SDK (non-deployment)       | 1     | 0         | WARN   |
| Float price fields in canonical schemas | 7     | 0         | WARN   |
| Naive datetime in schemas               | 8     | 0         | WARN   |
| Services with /health                   | 7/14  | 14/14     | WARN   |
| Services with /readiness                | 6/14  | 14/14     | WARN   |
| Services with Prometheus                | 12/14 | 14/14     | WARN   |
| Services with OTel init_tracing         | 4/14  | 14/14     | WARN   |
| TODO/FIXME (prod excl. GH-BACKLOG)      | 48    | minimal   | WARN   |
| try/except ImportError (prod)           | 5     | 0         | WARN   |

---

_Generated by automated codebase scan on 2026-03-08. Live infra checks (Section 7 — Deployment) not included._
