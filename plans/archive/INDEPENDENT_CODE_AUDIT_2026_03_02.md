# INDEPENDENT CODE AUDIT REPORT

## Unified Trading System -- 59 Repos, 3,827 Python Files, 779,052 Lines

### Date: 2026-03-02 16:18 GMT | Auditor: External Independent Review (Claude Opus 4.6)

---

## EXECUTIVE SUMMARY

| Audit Category                          | Grade  | Findings           | Critical           | High                | Medium            | Low |
| --------------------------------------- | ------ | ------------------ | ------------------ | ------------------- | ----------------- | --- |
| 1. Exception Handling & Silent Failures | **D**  | 195                | 49                 | 35                  | 74                | 37  |
| 2. File Size & Complexity               | **C+** | 316                | 1                  | 4                   | 40                | 271 |
| 3. Import Hygiene                       | **D+** | 805                | 170                | 146                 | 22                | 467 |
| 4. Security (OWASP)                     | **D**  | 17                 | 0                  | 6                   | 5                 | 6   |
| 5. DRY & Abstraction                    | **D+** | 10 systemic        | 1                  | 4                   | 5                 | 0   |
| 6. Test Coverage & Quality              | **D-** | 17 repos w/o tests | --                 | --                  | --                | --  |
| 7. Logging, Dead Code, Type Safety      | **D**  | ~3,700+            | 335 files w/ `Any` | 661 est. dead funcs | 2,811 unused vars | --  |
| 8. Dependencies & Config                | **C**  | 51+                | 1                  | 3                   | 6                 | 41  |

### **OVERALL GRADE: D (31/100) -- Needs significant remediation to reach A**

---

## CATEGORY 1: EXCEPTION HANDLING & SILENT FAILURES -- Grade: D

### Critical Findings (49)

- **49 `try/except ImportError` fallback patterns** in production code -- directly violates the fail-loud principle.
  `features-delta-one-service` alone has 16 occurrences including **MockTalib stubs** that return garbage data silently.
- **37 `except Exception: pass`** blocks across 22 files, including core libraries
  (`unified_cloud_services/__init__.py`, `gcp_clients.py`, `dependency_checker.py`).
- **10 silent `return None`** patterns where exceptions are caught and None is returned without logging.

### Key Offenders

| Repo                          | Count | Worst Pattern                                             |
| ----------------------------- | ----- | --------------------------------------------------------- |
| `features-delta-one-service`  | 16    | MockTalib stubs produce wrong calculations silently       |
| `unified-trading-services`    | 12    | Core library swallows GCS/storage failures                |
| `execution-service/scripts`   | 5     | Upload script silently discards data extraction failures  |
| `features-volatility-service` | 1     | `get_storage_client = None` -- NoneType errors downstream |

### Specific Files

**CRITICAL -- MockTalib (features-delta-one-service)**

- `features_delta_one_service/app/calculators/volatility.py:14`
- `features_delta_one_service/app/calculators/momentum.py:15`
- `features_delta_one_service/app/calculators/oscillators.py:15`
- `features_delta_one_service/app/calculators/technical.py:16`
- `features_delta_one_service/app/calculators/moving_averages.py:14`

Each creates a MockTalib that returns `np.full(...)` garbage data when talib is unavailable.

**CRITICAL -- Core Library (unified-trading-services)**

- `unified_cloud_services/__init__.py:52-53` -- `except Exception: pass  # Don't fail import`
- `unified_cloud_services/core/gcp_clients.py:279-280` -- silently ignores GCS blob deletion failures
- `unified_cloud_services/core/dependency_checker.py:236-237` -- storage client creation failure swallowed
- `unified_cloud_services/core/logging.py:268-283` -- three `except Exception: pass` during shutdown
- `unified_cloud_services/core/signal_handler.py:116-171` -- four `except Exception: pass` in signal handling

**HIGH -- Execution Service Scripts**

- `execution-service/scripts/utils/upload_backtest_results_to_gcs.py:167-432` -- five separate `except Exception: pass`
  blocks silently discarding data

**25 `os.getenv()` calls in production code** (should use `UnifiedCloudConfig`)

- `unified-trading-deployment-v3/scripts/download_instruments.py:77,90,96`
- `instruments-service/scripts/run_quality_gates.py:50-297` (10 occurrences)
- `instruments-service/pytest_load_env.py:43-78` (4 occurrences)
- `unified-api-contracts/scripts/collect_responses.py:61-257`

---

## CATEGORY 2: FILE SIZE & COMPLEXITY -- Grade: C+

### Oversized Files (>1,500 lines): 5 files

| File                                                              | Lines | Issue                                               |
| ----------------------------------------------------------------- | ----- | --------------------------------------------------- |
| `instruments-service/.../league_classification.py`                | 1,865 | ~1,700 lines of static data dict -- extract to YAML |
| `features-sports-service/.../tracking/team_features.py`           | 1,825 | Pure data list (218 FeatureEntry) -- no logic       |
| `execution-service/tests/live/.../test_binance_live_execution.py` | 1,646 | **Single 1,608-line function** -- unmaintainable    |
| `features-sports-service/.../scripts/table_exporters.py`          | 1,613 | 21 copy-paste exporter functions                    |
| `features-sports-service/tests/unit/test_migration_scripts.py`    | 1,553 | 19 test classes                                     |

### Top 20 Largest Files

| Rank | Lines | File                                                                | Classes | Functions |
| ---- | ----- | ------------------------------------------------------------------- | ------- | --------- |
| 1    | 1,865 | `instruments-service/.../league_classification.py`                  | 3       | 8         |
| 2    | 1,825 | `features-sports-service/.../tracking/team_features.py`             | 0       | 0         |
| 3    | 1,646 | `execution-service/tests/.../test_binance_live_execution.py`        | 0       | 1         |
| 4    | 1,613 | `features-sports-service/.../scripts/table_exporters.py`            | 0       | 21        |
| 5    | 1,553 | `features-sports-service/tests/unit/test_migration_scripts.py`      | 19      | 78        |
| 6    | 1,494 | `market-tick-data-service/.../config.py`                            | 11      | 35        |
| 7    | 1,489 | `unified-trading-deployment-v3/tests/.../test_data_status_turbo.py` | 22      | 66        |
| 8    | 1,478 | `execution-service/.../data/loader.py`                              | 1       | 12        |
| 9    | 1,400 | `execution-service/.../data/converter.py`                           | 1       | 5         |
| 10   | 1,335 | `market-tick-data-service/.../models.py`                            | 15      | 37        |
| 11   | 1,318 | `execution-service/.../backtest/actors/signal_driven_v3.py`         | 2       | 31        |
| 12   | 1,281 | `execution-service/.../venues/deribit.py`                           | 1       | 9         |
| 13   | 1,274 | `market-data-processing-service/.../orchestration_service.py`       | 1       | 16        |
| 14   | 1,242 | `execution-service/.../algorithms/impl/vwap.py`                     | 2       | 15        |
| 15   | 1,224 | `execution-service/.../algorithms/impl/passive_aggressive.py`       | 2       | 19        |
| 16   | 1,222 | `market-tick-data-service/.../validation_service.py` (engine)       | 1       | 27        |
| 17   | 1,219 | `market-tick-data-service/.../validation_service.py` (app)          | 1       | 27        |
| 18   | 1,187 | `strategy-service/presentation/create_presentation.py`              | 0       | 8         |
| 19   | 1,184 | `features-sports-service/.../clients/soccer_football.py`            | 1       | 1         |
| 20   | 1,167 | `unified-trading-pm/.../04-create-service-epics.py`                 | 3       | 23        |

### Oversized Functions: 271 functions over 100 lines

| Lines     | File                                                         | Function                           | Severity     |
| --------- | ------------------------------------------------------------ | ---------------------------------- | ------------ |
| **1,608** | `execution-service/tests/.../test_binance_live_execution.py` | `test_order_execution()`           | **EXTREME**  |
| **811**   | `unified-trading-deployment-v3/.../generate_topology_svg.py` | `build()`                          | **EXTREME**  |
| **536**   | `execution-service/tests/.../test_predefined_orders.py`      | `test_option_predefined()`         | **CRITICAL** |
| **419**   | `unified-trading-deployment-v3/.../auto_sync.py`             | `_auto_sync_running_deployments()` | **CRITICAL** |
| **417**   | `deployment-api/.../auto_sync.py`                            | `_auto_sync_running_deployments()` | **CRITICAL** |
| **411**   | `execution-service/.../benchmark/comparison.py`              | `_get_algorithm_configs()`         | **CRITICAL** |
| **351**   | `execution-service/.../results/timeline.py`                  | `build_timeline()`                 | **CRITICAL** |
| **329**   | `execution-service/.../algorithms/impl/vwap.py`              | `on_order()`                       | **HIGH**     |
| **302**   | `execution-service/.../algorithms/impl/twap.py`              | `on_order()`                       | **HIGH**     |

### Near-Duplicate Files

- `validation_service.py` exists in two locations (1,222 and 1,219 lines) -- near-identical
- `deployment-api` and `unified-trading-deployment-v3` share multiple duplicate files

---

## CATEGORY 3: IMPORT HYGIENE -- Grade: D+

### `Any` Type Usage -- **335 files** (most widespread violation)

| Repo                             | Files with `Any` | Total `Any` refs | Severity |
| -------------------------------- | ---------------- | ---------------- | -------- |
| `execution-service`              | 169              | ~800+            | CRITICAL |
| `market-tick-data-service`       | 45               | ~200+            | HIGH     |
| `market-data-processing-service` | 31               | ~150+            | HIGH     |
| `unified-trading-library`        | 25               | ~100+            | HIGH     |
| `ml-training-service`            | 13               | ~60+             | MEDIUM   |

**Total**: 332 files, ~1,626 `Any` references. Project standard explicitly prohibits `Any`.

### Imports Inside Functions: 339 occurrences in production code

- `unified-trading-deployment-v3/api/utils/storage_facade.py`: Same import repeated **7 times** in 7 separate functions
- `unified-trading-deployment-v3/api/routes/deployment_caching.py`: Same cache import in 5 functions
- `unified-trading-deployment-v3/api/utils/data_status_checkers.py`: 4 imports repeated in 3 functions

### Wildcard Imports: 30 across 5 files

| File                                                   | Count                   | Severity |
| ------------------------------------------------------ | ----------------------- | -------- |
| `unified-api-contracts/.../cloud_sdks/aws/__init__.py` | **18 wildcard imports** | CRITICAL |
| `unified-api-contracts/.../binance/schemas.py`         | 4                       | HIGH     |
| `unified-api-contracts/.../binance/__init__.py`        | 4                       | HIGH     |
| `execution-service/.../instruments/__init__.py`        | 2                       | HIGH     |
| `execution-service/execution_service/__init__.py`      | 2                       | HIGH     |

### `try/except ImportError` Fallbacks: 94 across 70 files (29 in production)

### `# type: ignore` Suppressions: 395 total

| Suppressed Error | Count |
| ---------------- | ----- |
| `reportAny`      | 79    |
| `attr-defined`   | 63    |
| `union-attr`     | 54    |
| `arg-type`       | 52    |
| `misc`           | 38    |
| `assignment`     | 37    |
| Bare (no reason) | 9     |

### Missing Return Type Annotations: 1,884 functions (48% of all public functions)

| Repo                            | Missing |
| ------------------------------- | ------- |
| `execution-service`             | 266     |
| `unified-trading-library`       | 257     |
| `unified-trading-deployment-v3` | 242     |
| `market-tick-data-service`      | 191     |
| `deployment-api`                | 129     |

---

## CATEGORY 4: SECURITY -- Grade: D

### HIGH Severity (6)

**F1: Missing API Authentication**

- `execution-results-api`: All 30+ endpoints unauthenticated (POST /backtest/run, /backtest/mass-deploy, etc.)
- `deployment-api` / `unified-trading-deployment-v3`: All deployment management endpoints unauthenticated (POST
  /deployments, DELETE /deployments/{id})
- `market-data-api`, `client-reporting-api`, `alerting-service`: All unauthenticated

**F3: Insecure Deserialization -- pickle.load from GCS**

- `unified-trading-services/unified_cloud_services/core/cloud_storage_service.py:218`
- `unified-trading-services/unified_trading_services/core/cloud_storage_service.py:218`

**F4: Insecure Deserialization -- joblib.load from GCS/Disk (6 files)**

- `unified-trading-services/.../cloud_storage_service.py:220`
- `unified-trading-services/.../ml/model_registry.py:225`
- `unified-ml-interface/.../model_registry.py:630`
- `ml-training-service/.../ml/model_registry.py:229`
- `features-sports-service/.../ml/synthetic_xg/inference.py:33`
- `features-sports-service/.../ml/synthetic_xg/train.py:147`

**F5: Insecure Deserialization -- jsonpickle.decode from Redis**

- `unified-trading-deployment-v3/api/utils/cache.py:58`
- `deployment-api/deployment_api/utils/cache.py:58`

**F1/F2: Command Injection via Unsanitized Parameters**

- `unified-trading-deployment-v3/api/routes/service_status_checkers.py:299-308` -- user `service` param in gcloud
  subprocess
- `unified-trading-deployment-v3/.../services/log_service.py:71-85` -- `deployment_id`, `service`, `shard_id` in gcloud
  filter

**F14: Mock Authentication in Production**

- `position-balance-monitor-service/.../api/main.py:124-146` -- accepts any `"client-{anything}-key"` as valid

### MEDIUM Severity (5)

**F6/F7: SQL Injection via f-string**

- `features-sports-service/.../scripts/validation.py:127,171,184` -- table name interpolation with `# noqa: S608`
- `ml-inference-service/.../prediction_publisher.py:224` -- BigQuery table name via f-string

**F8: .env Files Tracked in Git (12+ repos)**

- Contains GCP project IDs, service account emails, Secret Manager names

**F10: Verbose Error Messages / Tracebacks Returned to Client**

- `position-balance-monitor-service/.../api/main.py:87` -- `str(exc)` in 500 response
- `strategy-service/.../archive_backtest_adapter.py:379-385` -- `traceback.format_exc()` in response
- `unified-trading-deployment-v3/api/routes/deployments.py:379` -- exception in HTTP detail

**F13: Insecure HTTP Defaults**

- `execution-service/.../risk_checker.py:32` -- `http://localhost:8081`
- `execution-service/.../orchestrator.py:75` -- `http://localhost:8080`
- `risk-and-exposure-service/.../config.py:44` -- `http://position-balance-monitor-service:8000`

**F16: FastAPI Swagger/OpenAPI Docs Exposed in Production**

- None of the FastAPI apps disable docs in production

### Positive Security Notes

- No hardcoded real secrets (API keys in Secret Manager)
- No `verify=False`, no `eval()`/`exec()`, no `shell=True`, no `os.system()`
- `execution-service` has proper OIDC auth with group-based permissions
- Rate limiting implemented on multiple services

---

## CATEGORY 5: DRY & ABSTRACTION -- Grade: D+

### CRITICAL (1)

**Dual Package Identity Crisis** Two packages provide overlapping cloud service abstractions:

- `unified-trading-services` (v0.3.7) -> `unified_trading_services` namespace
- `unified-cloud-services` (v1.5.23) -> `unified_cloud_services` namespace

15+ repos confused about which to import. Some import from both. 3 `pyproject.toml` files + 25 CI configs still
reference old name.

### HIGH (4)

**Test File Copy-Paste** | Template | Copies | Repos | |---|---|---| | `test_shard_combinatorics.py` | 11 | All major
services | | `test_event_logging.py` | 18 | All services | | `test_cloud_agnostic_paths.py` | 9 | Data services | |
`check-import-patterns.py` | 25 (6 divergent variants) | All repos under .cursor/scripts/ |

**Sports Domain Client Duplication**: 5 near-identical classes in `unified-domain-client/sports/`

- `SportsFixturesDomainClient`, `SportsFeaturesDomainClient`, `SportsTickDataDomainClient`, `SportsOddsDomainClient`,
  `SportsMappingsDomainClient`
- All share identical `__init__`, `read_*`, `write_*`, `get_available_*` methods

**DeFi Adapter Boilerplate**: 8+ adapters with identical `_ensure_session`, `_ensure_graph_client`,
`_ensure_alchemy_client`

**`quality-gates.sh` Duplicated Across 60 Repos** with drift

### MEDIUM (5)

- Config singleton boilerplate duplicated in 8+ services (`get_config()` / `get_settings()`)
- Health check response format inconsistent (`"ok"` vs `"healthy"`, `/health` vs `/api/health`)
- God config in `market-tick-data-service` (2,200 lines across 4 files, 3 different config approaches)
- Inconsistent config modeling: Pydantic vs dataclass vs TypedDict vs pydantic_settings
- Non-sports UDC client duplication (3 more copy-paste classes: PnL, Risk, Positions)

---

## CATEGORY 6: TEST COVERAGE & QUALITY -- Grade: D-

### Repos with NO Test Files: 13

| Repo                     | Source Files | Risk                                      |
| ------------------------ | ------------ | ----------------------------------------- |
| `deployment-api/`        | 62           | **CRITICAL** -- large service, zero tests |
| `unified-trading-codex/` | 58           | LOW (validators repo)                     |
| `unified-trading-pm/`    | 56           | LOW (PM tooling)                          |
| 9 UI repos               | 0-1 each     | LOW (TypeScript/JS)                       |

### Test Quality

| Metric                              | Value                   |
| ----------------------------------- | ----------------------- |
| Total test files                    | 851                     |
| Overall test-to-source ratio        | 0.33                    |
| Tests with NO assertions            | **186**                 |
| Dummy `assert True` tests           | **28**                  |
| Repos below 0.3 test ratio          | **19 of 45** with tests |
| Repos with conftest.py              | 27                      |
| Repos with tests but no conftest.py | **17**                  |

### Worst Test-to-Source Ratios (Critical Repos)

| Repo                       | Test Files | Source Files | Ratio    |
| -------------------------- | ---------- | ------------ | -------- |
| `deployment-api`           | 0          | 62           | **0.00** |
| `deployment-engine`        | 1          | 20           | 0.05     |
| `execution-results-api`    | 2          | 30           | 0.07     |
| `unified-domain-client`    | 6          | 49           | 0.12     |
| `unified-market-interface` | 18         | 111          | 0.16     |
| `unified-api-contracts`    | 43         | 251          | 0.17     |
| `unified-trading-services` | 27         | 125          | 0.22     |

### Dummy Tests Highlight

`unified-api-contracts/tests/unit/test_config.py` -- **entire file is placeholder tests** written to pass quality gates:

```python
def test_config_defaults(self):
    """Test that configuration has reasonable defaults."""
    assert True  # Placeholder for actual config tests
```

### Coverage Thresholds

- 22 repos: `fail_under = 70`
- **15 repos: `fail_under = 40`** (including `execution-service` with 456 source files)
- 8 repos: no coverage config at all

### Integration Tests

- `system-integration-tests/`: **Only 10 tests covering 5 of 58 services**
- No cross-service data flow tests
- No sports pipeline tests
- No ML pipeline tests

---

## CATEGORY 7: LOGGING, DEAD CODE, TYPE SAFETY -- Grade: D

### Logging Issues

| Finding                                      | Count                                | Impact                                             |
| -------------------------------------------- | ------------------------------------ | -------------------------------------------------- |
| **F-string logging** (`logger.info(f"...")`) | **2,842 calls** (25% of all logging) | Defeats lazy evaluation, breaks structured logging |
| **Exception logging without traceback**      | **1,357 instances**                  | 72% of exception logs lose stack traces            |
| `print()` in service/library code            | 429 calls                            | Not captured in cloud logging                      |
| `logging.basicConfig()` in library code      | 21 files                             | Clobbers root logger for consumers                 |

**Worst repos for f-string logging**: `execution-service` (145 files), `market-tick-data-service` (67 files),
`unified-trading-library` (33 files)

### Type Safety

| Finding                         | Count                  |
| ------------------------------- | ---------------------- |
| Files importing `Any`           | 332 (1,626 total refs) |
| Missing return type annotations | 1,884 functions (48%)  |
| `# type: ignore` suppressions   | 395                    |
| Bare `dict`/`list` annotations  | 647                    |
| `cast()` calls                  | 1,000                  |

### Dead Code

| Finding                                            | Count                  |
| -------------------------------------------------- | ---------------------- |
| Estimated unused public functions                  | ~662 (17% sample rate) |
| Unused local variables (heuristic)                 | ~2,811                 |
| Commented-out code blocks (4+ lines)               | 206                    |
| Empty non-`__init__` files                         | 5                      |
| `try/except ImportError` fallbacks in library code | 27                     |

---

## CATEGORY 8: DEPENDENCIES & CONFIG -- Grade: C

### Dependency Pinning (473 entries)

| Strategy                           | Count   | %       |
| ---------------------------------- | ------- | ------- |
| Properly bounded (`>=X,<Y`)        | 183     | 38%     |
| Floor only, no upper bound (`>=X`) | **281** | **59%** |
| Completely unpinned                | **9**   | 2%      |

### Version Conflicts: 35 packages

| Package    | Different Specs | Risk   |
| ---------- | --------------- | ------ |
| `pydantic` | 6               | HIGH   |
| `aiohttp`  | 6               | HIGH   |
| `pyyaml`   | 5               | MEDIUM |
| `scipy`    | 5               | MEDIUM |
| `httpx`    | 5               | MEDIUM |
| `pyarrow`  | 4               | HIGH   |
| `numpy`    | 3               | MEDIUM |

### Docker Security

| Issue                                  | Count  | % of 26 Dockerfiles |
| -------------------------------------- | ------ | ------------------- |
| **Runs as root** (no `USER` directive) | **14** | **54%**             |
| **No `.dockerignore`**                 | **23** | **88%**             |
| Single-stage build                     | 18     | 69%                 |
| Dev deps in production image           | Most   | --                  |

### Build System Fragmentation

- 8 different setuptools version requirements (`>=45` to `>=80.9.0`)
- 4 repos use hatchling, 38 use setuptools, 3 have no build system
- Python version: 43 repos `>=3.13,<3.14`, 2 outliers

### Configuration Safety

- 21 repos missing `.env.example` files
- 5 repos track `.env` in git (GCP project IDs, service account emails)
- Hardcoded CORS origins in 4+ files
- `os.environ` reads in 15+ library files

### Positive Notes

- All 45 Python repos use `pyproject.toml` (consistent)
- 42 of 45 repos have `uv.lock` files
- Quality gates enforced via GitHub Actions (100% coverage)
- `UnifiedCloudConfig` architecture is well-designed

---

## SCORING BREAKDOWN

| Category             | Weight   | Score      | Notes                                          |
| -------------------- | -------- | ---------- | ---------------------------------------------- |
| Security             | 20%      | 40/100     | Unauthenticated APIs, pickle/joblib, mock auth |
| Exception Handling   | 15%      | 30/100     | 195 findings, silent failures pervasive        |
| Type Safety          | 15%      | 20/100     | 335 files with `Any`, 48% missing return types |
| Test Coverage        | 15%      | 25/100     | 13 untested repos, 186 assertion-free tests    |
| Logging Quality      | 5%       | 20/100     | 2,842 f-string logs, 1,357 lost tracebacks     |
| DRY/Abstraction      | 10%      | 40/100     | Dual package identity, mass copy-paste         |
| Import Hygiene       | 5%       | 35/100     | 335 files with `Any`, 94 fallback patterns     |
| File Size/Complexity | 5%       | 65/100     | 271 oversized functions, 5 oversized files     |
| Dependencies/Config  | 5%       | 35/100     | 59% unbounded deps, Docker security            |
| Deployment/Docker    | 5%       | 30/100     | Root containers, no dockerignore               |
| **Weighted Total**   | **100%** | **31/100** |                                                |

### **FINAL GRADE: D (31/100)**

---

## RECOMMENDATIONS TO REACH A GRADE

### P0 -- Security (Fix Immediately)

1. **Add authentication to ALL API services** -- deployment-api, execution-results-api, market-data-api,
   client-reporting-api, alerting-service
2. **Replace pickle/joblib/jsonpickle** with safe serialization (JSON, Parquet, ONNX, safetensors)
3. **Remove .env files from git** (`git rm --cached`); add to `.gitignore`
4. **Replace mock auth** in position-balance-monitor-service with real Secret Manager validation
5. **Validate all user input** to subprocess/SQL against allowlists
6. **Disable OpenAPI docs** in production environments

### P1 -- Reliability (Fix This Sprint)

7. **Remove ALL `try/except ImportError` fallback patterns** -- fail loud
8. **Replace ALL `except Exception: pass`** with specific exception types + logging
9. **Fix exception logging** -- adopt `logger.exception()` in all except blocks; eliminate f-string logging (2,842
   calls)
10. **Resolve dual package identity** (`unified_cloud_services` vs `unified_trading_services`)

### P2 -- Maintainability (Fix This Month)

11. **Eliminate `Any` type** systematically -- 332 files. Start with `execution-service` (169 files)
12. **Add return type annotations** -- 1,884 functions (48%) missing
13. **Create `BaseDomainClient`** to replace 8 copy-paste domain client classes
14. **Move shared test templates** to shared conftest/pytest plugin
15. **Break up oversized functions** -- target 30 production functions >200 lines

### P3 -- Quality Gates (Fix This Quarter)

16. **Enforce test coverage >60%** in CI for all repos
17. **Add real tests to `deployment-api`** (62 source files, 0 tests)
18. **Remove 28 dummy `assert True` tests** and replace with real assertions
19. **Standardize build system** -- one setuptools version, one `requires-python` spec
20. **Fix Docker security** -- add non-root USER to 14 Dockerfiles, add .dockerignore to 23 repos

### Impact Estimate

| Action Group         | Grade Impact          |
| -------------------- | --------------------- |
| P0 (Security)        | D -> D+ (+10 pts)     |
| P1 (Reliability)     | D+ -> C (+15 pts)     |
| P2 (Maintainability) | C -> B- (+12 pts)     |
| P3 (Quality Gates)   | B- -> A- (+15 pts)    |
| **Total**            | **D (31) -> A- (83)** |
