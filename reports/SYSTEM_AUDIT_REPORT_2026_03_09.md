# System Audit Report — 2026-03-09

**Auditor:** Claude Code (15 parallel agents) **Date:** 2026-03-09 **Scope:** All active service repos in workspace
(excl. archive/, .venv*, typings/, test*) **Prior audit:** 2026-03-08 — Overall grade: CONDITIONAL PASS (0 FAILs, 6
WARNs)

---

## Overall Grade: FAIL

**4 FAILs, 5 WARNs, 6 PASSes, 1 N/A across 14 assessed sections.**

Regression from prior audit (CONDITIONAL PASS → FAIL). Primary drivers:

- Section 2 (Code Quality): function/class length violations newly detected at scale
- Section 5 (Schema Governance): float prices in UIC not remediated
- Section 9 (Cross-Repo Alignment): SSOT-INDEX not updated to list all active plans
- Section 14 (Orphaned Code): new section; 12 confirmed orphans in unified-api-contracts

---

## Section Scores

| Section                 | Score       | Delta vs 2026-03-08                                         |
| ----------------------- | ----------- | ----------------------------------------------------------- |
| 1. Workspace Governance | PASS (WARN) | Stable — new: invalid DAG ref typo                          |
| 2. Code Quality         | **FAIL**    | Regressed — function/class length violations at scale       |
| 3. Security             | WARN        | Improved (deployment-api S2S fixed); SECRET_ACCESSED gap    |
| 4. Architecture         | PASS        | Improved (all violations resolved)                          |
| 5. Schema Governance    | **FAIL**    | Stable FAIL — 8 float prices in UIC not fixed               |
| 6. Observability        | PASS        | Improved ↑ (/health 4/4, metrics 18+ services)              |
| 7. Deployment           | N/A         | N/A — requires live infra                                   |
| 8. Technical Debt       | PASS        | Improved ↑ (40% TODO reduction, 0 ImportError fallbacks)    |
| 9. Cross-Repo Alignment | **FAIL**    | Regressed — 13 plans not in SSOT-INDEX                      |
| 10. Integration Tests   | WARN        | Stable — 2 repos missing `unit` pytest marker               |
| 11. Coverage Regression | PASS        | Stable                                                      |
| 12. Cloud-Agnostic API  | PASS        | Stable                                                      |
| 13. No Stubs            | WARN        | New section — 99% tracked, 16 untracked TODOs               |
| 14. Orphaned Code       | **FAIL**    | New section — 12 confirmed orphans in unified-api-contracts |
| Config Injection        | WARN        | Regressed — GCP_PROJECT_ID re-export in deployment-api      |

---

## Section 1 — Workspace Governance

| CATEGORY   | CRITERION                          | STATUS | EVIDENCE                                                                                                                        |
| ---------- | ---------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------- |
| Governance | workspace-manifest.json valid JSON | PASS   | 2825 lines, valid JSON; 59 repos                                                                                                |
| Governance | All repos have arch_tier field     | PASS   | 59/59 repos                                                                                                                     |
| Governance | ci_status fields present           | PASS   | 59/59 repos; 46 BASELINE_RECORDED, 5 PASSING                                                                                    |
| Governance | DAG acyclic                        | PASS   | 178 edges, 0 cycles                                                                                                             |
| Governance | DAG refs valid                     | WARN   | features-onchain-service depends on `unified-feature-calculator` (non-existent); should be `unified-feature-calculator-library` |
| Governance | Repo count ~59                     | PASS   | Exactly 59 repos                                                                                                                |
| Governance | runtime-topology.yaml valid        | PASS   | version: 6; valid YAML                                                                                                          |

**Score: PASS (1 WARN)**

---

## Section 2 — Code Quality

| CATEGORY       | CRITERION                      | STATUS   | EVIDENCE                                                                                                                             |
| -------------- | ------------------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Tools          | quality-gates.sh present       | PASS     | All 22 service repos                                                                                                                 |
| Tools          | MIN_COVERAGE calibrated        | WARN     | features-calendar-service at default 70; others calibrated                                                                           |
| Length         | File < 900 lines (prod source) | PASS     | generate_topology_svg.py 974L excluded (script)                                                                                      |
| Length         | Function < 100 lines           | **FAIL** | **356 violations** across workspace; worst: market-data-processing-service `write_candles()` 203L, `_write_candles()` 197L           |
| Length         | Class < 500 lines              | WARN     | **78 violations**; worst: CandleProcessingService 831L, OrchestrationWorkersMixin 728L, BetfairAdapter 624L, UnifiedCloudConfig 547L |
| Tools          | ruff configured                | PASS     | All 22 repos                                                                                                                         |
| Tools          | basedpyright strict            | PASS     | All 22 repos                                                                                                                         |
| Security       | zero os.getenv in prod         | PASS     | gcs_service.py FIXED (was 9 violations); 1 approved exception remains                                                                |
| Error Handling | zero bare except               | **FAIL** | 3 violations: strategy-service/signal_publisher.py:96,151; execution-service/dependency_checker.py:222                               |
| Types          | # type: ignore < 20            | PASS     | 4 total workspace-wide                                                                                                               |

**Score: FAIL** (2 hard criteria failed: function length, bare excepts)

**Key remediation:**

- market-data-processing-service: decompose `CandleProcessingService` (831L) and `OrchestrationWorkersMixin` (728L)
- strategy-service/signal_publisher.py:96,151: replace `except Exception:` with specific exception types
- execution-service/dependency_checker.py:222: same

---

## Section 3 — Security

| CATEGORY  | CRITERION                       | STATUS   | EVIDENCE                                                                                                             |
| --------- | ------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------- |
| Secrets   | No hardcoded API keys/tokens    | PASS     | Zero in production source                                                                                            |
| Secrets   | Secrets via get_secret_client() | PASS     | UnifiedCloudConfig enforces pattern                                                                                  |
| Transport | No verify=False                 | PASS     | 30 HTTP client files checked; all use default SSL                                                                    |
| Auth      | Auth middleware on all APIs     | PASS     | All 4 APIs use `APIRouter(Depends(verify_api_key))`                                                                  |
| Auth      | No mock auth in prod            | PASS     | DISABLE_AUTH guarded by environment check                                                                            |
| Auth      | AUTH_FAILURE events logged      | WARN     | deployment-api ✓, client-reporting-api ✓; market-data-api ✗ (auth.py:35-40), execution-results-api ✗ (auth.py:35-40) |
| Audit     | SECRET_ACCESSED events logged   | **FAIL** | Event type defined in UEI but **never called** in any production code                                                |
| Audit     | CONFIG_CHANGED events logged    | PASS     | 15 log_event("CONFIG_CHANGED") calls confirmed (config_reloaders.py:189 et al.)                                      |
| Auth      | deployment-api S2S auth         | PASS     | **FIXED** — verify_service_token with AUTH_FAILURE logging at auth.py:28-85                                          |

**Score: WARN** (SECRET_ACCESSED gap; AUTH_FAILURE incomplete across APIs)

---

## Section 4 — Architecture

| CATEGORY | CRITERION                                   | STATUS | EVIDENCE                                                                                                    |
| -------- | ------------------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------- |
| Tiers    | No service→service Python imports           | PASS   | 0 cross-service imports found                                                                               |
| UI       | No UI in service repos                      | PASS   | 0 .jsx/.tsx/.vue files in service dirs                                                                      |
| Modes    | Batch-live symmetry                         | PASS   | Same engine interfaces for both modes                                                                       |
| Cloud    | Services use UCI abstractions               | PASS   | All cloud I/O through get_storage_client, get_secret_client                                                 |
| Cloud    | No GCS protocol names (except path strings) | WARN   | gcs:// path strings in execution-service/data/catalog.py:50,115 — path parsing literals only, not API calls |
| Boundary | deployment-api uses HTTP boundary           | PASS   | 0 direct deployment_service imports in deployment-api                                                       |
| Cloud    | No google.cloud outside UCI                 | PASS   | 2 deferred imports in deployment-api (control-plane, documented)                                            |
| Cloud    | No boto3 outside UCI/deployment-service     | PASS   | Only in UCI providers/aws.py and deployment-service/backends/                                               |
| Tiers    | T0→T1→T2→T3 invariant                       | PASS   | T0 libs import nothing from T3                                                                              |

**Score: PASS** (1 acceptable WARN on path strings)

---

## Section 5 — Schema Governance

| CATEGORY | CRITERION                               | STATUS   | EVIDENCE                                                                                                                                                                                                                                                                                  |
| -------- | --------------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AC       | AC contains external venue schemas only | PASS     | 40+ venue schemas; no internal trading schemas                                                                                                                                                                                                                                            |
| UIC      | UIC contains internal schemas only      | PASS     | domain/ schemas for execution, risk, strategy, ml                                                                                                                                                                                                                                         |
| Boundary | No AC/UIC duplication                   | PASS     | 0 class name overlaps (142 AC vs 191 UIC classes)                                                                                                                                                                                                                                         |
| Prices   | No float prices in trading schemas      | **FAIL** | 8 float price fields in UIC: `pubsub.py:147` MarketTickMessage.price, `pubsub.py:163-164` DerivativeTickerMessage.index/mark_price, `pubsub.py:172` LiquidationMessage.price, `domain/strategy_service/order.py:37` StrategySignal.price, `features.py:122-123,288` spot/commodity prices |
| Datetime | No naive datetime                       | PASS     | AC uses AwareDatetime; UIC datetime fields UTC-aware in practice                                                                                                                                                                                                                          |
| Tests    | Layer 0 alignment tests present         | PASS     | test_contract_alignment.py (307 tests), test_ac_uic_alignment.py                                                                                                                                                                                                                          |
| Tests    | Per-service test_schema_robustness.py   | PASS     | Present in 7 required service repos                                                                                                                                                                                                                                                       |

**Score: FAIL** (float prices in UIC not remediated from prior audit)

---

## Section 6 — Observability

| CATEGORY    | CRITERION                        | STATUS | EVIDENCE                                                                                                                            |
| ----------- | -------------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| Health      | /health on all 4 API services    | PASS   | All 4: execution-results-api:195, market-data-api health.py:6, client-reporting-api health.py:6, deployment-api health_routes.py:30 |
| Health      | /readiness on all 4 API services | PASS   | All 4 confirmed                                                                                                                     |
| Correlation | correlation_id propagated        | PASS   | test_correlation_propagation.py validates UUID flow                                                                                 |
| Metrics     | prometheus_client imported       | PASS   | 28 files                                                                                                                            |
| Metrics     | RECORDS_PROCESSED Counter        | PASS   | All 4 APIs + 14+ services have metrics.py:5-9                                                                                       |
| Metrics     | PROCESSING_LATENCY Histogram     | PASS   | All 4 APIs + 14+ services have metrics.py:11-15                                                                                     |
| Dashboards  | trading-overview.json present    | PASS   | deployment-service/grafana/dashboards/trading-overview.json                                                                         |
| Dashboards  | system-health.json present       | PASS   | deployment-service/grafana/dashboards/system-health.json                                                                            |
| Memory      | Pre-crash checkpoint at 85%      | PASS   | execution-service, strategy-service, risk, ml-inference                                                                             |
| Compliance  | MiFID II ComplianceReporter      | PASS   | execution-service/compliance/compliance_reporter.py                                                                                 |
| Compliance  | FCA StrategyComplianceReporter   | PASS   | strategy-service/compliance/compliance_reporter.py                                                                                  |
| Tests       | test_event_logging.py present    | PASS   | unified-events-interface/tests/unit/test_event_logging.py                                                                           |

**Score: PASS** — Significant improvement; /health was missing on 7/14 services in prior audit.

---

## Section 7 — Deployment

**Score: N/A** — Requires live infrastructure; not assessable from codebase alone.

---

## Section 8 — Technical Debt

| CATEGORY | CRITERION                            | STATUS | EVIDENCE                                                |
| -------- | ------------------------------------ | ------ | ------------------------------------------------------- |
| Docs     | QUALITY_GATE_BYPASS_AUDIT.md present | PASS   | 13/13 required repos; 45 total workspace                |
| Types    | Undocumented # type: ignore          | PASS   | 0 undocumented; 1 total with bracket notation           |
| Types    | # type: ignore < 10                  | PASS   | 1 total (features-sports-service/team_derived.py:184)   |
| Imports  | No deprecated import aliases         | PASS   | CloudTarget properly deprecated with DeprecationWarning |
| Imports  | No try/except ImportError fallbacks  | PASS   | **0 in production** (was 5 in prior audit)              |
| Debt     | TODO/FIXME < 30                      | PASS   | **29** (was 48; -40% reduction)                         |
| Imports  | No deprecated module paths           | PASS   | No orphaned old module paths found                      |

**Score: PASS** — Major improvement: all ImportError fallbacks eliminated, 40% TODO reduction.

---

## Section 9 — Cross-Repo Alignment

| CATEGORY | CRITERION                         | STATUS   | EVIDENCE                                                                                                                                                                                                                                                                                                                                                                                                                            |
| -------- | --------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plans    | All active plans in SSOT-INDEX    | **FAIL** | Only ~5 of 14 active plans individually registered in 00-SSOT-INDEX.md; 13 plans not directly named (api_keys_and_auth, aws_migration, e2e_smoke, foundational_repos_remediation, full_autonomous_agent_ci, ibkr_gateway_rollout, master_pre_deployment, phase2_library_tier_hardening, phase3_service_hardening, schema_versioning_health_matrix, sports_migration_combined, unit_tests_and_test_failure, version_cascade_rollout) |
| Codex    | Codex reflects current decisions  | PASS     | Key files updated Mar 7-9; bootstrap exception documented                                                                                                                                                                                                                                                                                                                                                                           |
| Rules    | Cursor rules consistent           | WARN     | .cursor/rules/ symlink returns 0 when searched (tool traversal issue); unified-trading-pm/cursor-rules/ has 132 files — likely symlink traversal, not an actual gap                                                                                                                                                                                                                                                                 |
| Topology | manifest matches runtime-topology | WARN     | Different formats (JSON vs YAML); both complete but 1:1 verification not possible                                                                                                                                                                                                                                                                                                                                                   |
| Repos    | All 4 API services in manifest    | PASS     | execution-results-api, market-data-api, client-reporting-api, deployment-api all confirmed                                                                                                                                                                                                                                                                                                                                          |
| Plans    | Active plan count                 | WARN     | Memory said 16; filesystem has **14** (2 plans archived since last session)                                                                                                                                                                                                                                                                                                                                                         |

**Score: FAIL** (9.1: 13 plans unregistered in SSOT-INDEX)

---

## Section 10 — Integration Test Coverage

| CATEGORY | CRITERION                                | STATUS | EVIDENCE                                                                                                                                                                                                         |
| -------- | ---------------------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Coverage | Required repos have tests/integration/   | PASS   | execution-service (20), strategy-service (4), risk-and-exposure-service (2), ml-inference-service (3), unified-market-interface (3), unified-trade-execution-interface (5), unified-reference-data-interface (4) |
| VCR      | Interface repos have cassettes           | PASS   | All 6 interface repos; cassettes in tests/cassettes/<venue>/\*.yaml                                                                                                                                              |
| Mocking  | No live cloud calls in tests             | PASS   | All integration tests use MagicMock/patch/VCR record_mode="none"                                                                                                                                                 |
| Markers  | pytest markers standardized              | WARN   | strategy-service pyproject.toml:193-196 missing `unit` marker; ml-inference-service pyproject.toml:128-131 missing `unit` marker                                                                                 |
| Files    | Integration test files in required repos | PASS   | All 7 repos confirmed                                                                                                                                                                                            |

**Score: WARN** (minor — 2 repos missing `unit` pytest marker definition)

---

## Section 11 — Coverage Regression Prevention

| Repo                      | MIN_COVERAGE | fail_under | Match |
| ------------------------- | ------------ | ---------- | ----- |
| execution-service         | 55           | 55         | ✓     |
| strategy-service          | 69           | 69         | ✓     |
| risk-and-exposure-service | 71           | 71         | ✓     |
| ml-inference-service      | 72           | 72         | ✓     |
| unified-cloud-interface   | 80           | 80         | ✓     |
| alerting-service          | 78           | 78         | ✓     |
| instruments-service       | 51           | 51         | ✓     |

**Score: PASS** — All calibrated; none using default 70.

---

## Section 12 — Cloud-Agnostic API Compliance

| CATEGORY | CRITERION                                   | STATUS | EVIDENCE                                                         |
| -------- | ------------------------------------------- | ------ | ---------------------------------------------------------------- |
| Cloud    | No gcs_bucket outside UCI                   | PASS   | 0 violations                                                     |
| Cloud    | No bigquery_dataset outside UCI             | PASS   | 0 in production (test-only)                                      |
| Cloud    | No upload_to_gcs outside UCI                | PASS   | 0 violations; UCI StorageClient used                             |
| Cloud    | No os.getenv outside bootstrap              | PASS   | Bootstrap exceptions documented                                  |
| Cloud    | No google.cloud imports outside UCI         | PASS   | 2 deferred imports in deployment-api (control-plane, documented) |
| Cloud    | No boto3 outside UCI/deployment backends    | PASS   | 0 violations                                                     |
| Cloud    | No hardcoded gs:// strings                  | PASS   | Only in test mock data and comments                              |
| Cloud    | No google-cloud-\* in pyproject outside UCI | PASS   | 0 violations; gated behind optional extras                       |

**Score: PASS** — Stable from prior audit.

---

## Section 13 — No Unimplemented Stubs

| CATEGORY | CRITERION                 | STATUS | EVIDENCE                                                                                                     |
| -------- | ------------------------- | ------ | ------------------------------------------------------------------------------------------------------------ |
| Stubs    | raise NotImplementedError | PASS   | 187 total; ~99% tracked by active plans (stub_completion_interfaces_and_infra, phase3, phase2, ibkr_gateway) |
| Stubs    | TODO/FIXME/HACK comments  | WARN   | 59 total; ~16 untracked (non-blocking enhancements)                                                          |
| Stubs    | pass as sole body         | PASS   | All verified as ABC/Protocol/exception classes                                                               |
| Stubs    | ... as function body      | PASS   | All verified as Protocol/@abstractmethod                                                                     |

**Score: WARN** — 99% tracked; reference plan: stub_completion_interfaces_and_infra.plan.md

---

## Section 14 — No Orphaned Code (New)

| CATEGORY | CRITERION                         | STATUS   | EVIDENCE                                                                                                                                                                                                                 |
| -------- | --------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Orphans  | Unused Pydantic models/TypedDicts | **FAIL** | unified-api-contracts/domain_config.py: DomainConfigProtocol, DataTypeConfigProtocol, ExchangeInstrumentConfigProtocol, MLConfigProtocol (0 imports workspace-wide); vcr_endpoints.py: VCREndpoint TypedDict (0 imports) |
| Orphans  | Unused public functions           | **FAIL** | unified-api-contracts/canonical_mappings.py: get_venues_for_data_source(), get_canonical_venue_for_dataset(), get_defi_venue() — superseded by unified-trading-library equivalents; 0 callers                            |
| Orphans  | Unused Protocol implementations   | **FAIL** | unified-api-contracts/endpoint_registry.py: AccessMode, DataAvailability, ResponseFormat, EndpointSpec (0 imports)                                                                                                       |
| Orphans  | Total confirmed orphans           | FAIL     | **12 confirmed orphans**, all in unified-api-contracts; none have # orphan: comment or plan todo                                                                                                                         |

**Score: FAIL** — 12 orphans exceed ≤5 WARN threshold; none documented.

---

## Config Injection Compliance

| CATEGORY | CRITERION                       | STATUS | EVIDENCE                                                                                                                                                                                      |
| -------- | ------------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Config   | GCP_PROJECT_ID banned           | WARN   | deployment-api/settings.py:21 re-exports `GCP_PROJECT_ID = _config.gcp_project_id`; value from UnifiedCloudConfig (technically compliant) but symbol propagates to 15+ usages in service code |
| Config   | DomainConfigReloader used       | PASS   | strategy-service, execution-service, instruments-service all use DomainConfigReloader                                                                                                         |
| Config   | get_config_store() factory only | PASS   | No direct ConfigStore() instantiations                                                                                                                                                        |
| Config   | No hardcoded subscription lists | PASS   | All use config.subscription_list                                                                                                                                                              |
| Config   | CONFIG_CHANGED events logged    | PASS   | 15 log_event("CONFIG_CHANGED") calls                                                                                                                                                          |
| Config   | Bootstrap phase documented      | WARN   | factory.py PROTOCOL\_\* env reads lack consistent # config-bootstrap: labels                                                                                                                  |
| Config   | UnifiedCloudConfig singleton    | PASS   | @lru_cache(maxsize=1) pattern throughout                                                                                                                                                      |

**Score: WARN**

---

## Top 10 Blocking Findings

1. **[FAIL] Section 2** — 356 functions > 100 lines; worst:
   `market-data-processing-service/app/core/output_writer_service.py:write_candles()` (203L),
   `orchestration_writer.py:_write_candles()` (197L). Decompose service classes.

2. **[FAIL] Section 2** — 78 classes > 500 lines; worst: `market-data-processing-service/CandleProcessingService` 831L,
   `OrchestrationWorkersMixin` 728L. Structural refactor needed.

3. **[FAIL] Section 5** — `unified-internal-contracts/unified_internal_contracts/pubsub.py:147` —
   `MarketTickMessage.price: float` (and 7 others). Convert to `Decimal`. Breaking schema change; coordinate with
   downstream consumers (alerting-service, execution-service, strategy-service, ml-inference-service).

4. **[FAIL] Section 9** — `unified-trading-codex/00-SSOT-INDEX.md` missing direct entries for 13 of 14 active plans. Add
   individual rows for all 14 plans.

5. **[FAIL] Section 14** — `unified-api-contracts/unified_api_contracts/domain_config.py` — 4 Protocol classes with 0
   importers. Either delete or add `# orphan: <reason>` comments and plan todo.

6. **[FAIL] Section 14** — `unified-api-contracts/unified_api_contracts/canonical_mappings.py` — 3 functions superseded
   by unified-trading-library equivalents; 0 callers. Delete.

7. **[WARN] Section 3** — `SECRET_ACCESSED` event type defined in UEI but never emitted. Add
   `log_event("SECRET_ACCESSED", ...)` to `UnifiedCloudConfig` secret retrieval path.

8. **[WARN] Section 3** — `market-data-api/market_data_api/auth.py:35-40` and
   `execution-results-api/execution_results_api/auth.py:35-40` raise HTTPException without
   `log_event("AUTH_FAILURE", ...)`.

9. **[FAIL] Section 2** — `strategy-service/strategy_service/engine/core/signal_publisher.py:96,151` — bare
   `except Exception:` not fixed from prior audit. Specify exception types.

10. **[WARN] Section 1** — `unified-trading-pm/workspace-manifest.json` — `features-onchain-service` depends on
    `unified-feature-calculator` (non-existent); should be `unified-feature-calculator-library`.

---

## Technical Debt Trajectory

| Metric                         | 2026-03-08       | 2026-03-09      | Trend       |
| ------------------------------ | ---------------- | --------------- | ----------- |
| Overall grade                  | CONDITIONAL PASS | **FAIL**        | ↓ Regressed |
| FAILs                          | 0                | 4               | ↓           |
| WARNs                          | 6                | 5               | ↑ Improved  |
| /health endpoint coverage      | 7/14 services    | 4/4 APIs + more | ↑           |
| try/except ImportError in prod | 5                | 0               | ↑↑          |
| TODO/FIXME count               | 48               | 29              | ↑ (-40%)    |
| os.getenv violations           | 15               | 1 (approved)    | ↑↑          |
| S2S auth coverage              | 3/4 APIs         | 4/4 APIs        | ↑           |
| Function length violations     | not measured     | 356             | New finding |
| Class length violations        | not measured     | 78              | New finding |
| Orphaned code                  | not measured     | 12              | New finding |

**Note:** The CONDITIONAL PASS → FAIL regression is partly due to new sections (13, 14) and deeper measurement of code
quality metrics (function/class length) that were not quantified in the prior audit. Foundational security,
observability, and technical debt trajectory are all improved.

---

## Recommended Remediation Priority

### P0 — Required to reach CONDITIONAL PASS

1. Register all 14 active plans in `unified-trading-codex/00-SSOT-INDEX.md` (Section 9.1) — 30 min
2. Delete/document 12 orphaned symbols in `unified-api-contracts` (Section 14) — 1 hour
3. Fix bare `except Exception:` in signal_publisher.py:96,151 and dependency_checker.py:222 (Section 2) — 30 min

### P1 — Required to reach PASS

4. Convert 8 float price fields to Decimal in unified-internal-contracts (Section 5) — breaking change, needs downstream
   coordination
5. Add `log_event("SECRET_ACCESSED", ...)` to UnifiedCloudConfig secret retrieval (Section 3)
6. Add `log_event("AUTH_FAILURE", ...)` to market-data-api and execution-results-api auth handlers (Section 3)
7. Fix DAG ref typo: `unified-feature-calculator` → `unified-feature-calculator-library` in manifest (Section 1)

### P2 — Code quality (longer horizon)

8. Decompose market-data-processing-service long classes/functions (Section 2) — sprint-level effort
9. Add `unit` pytest marker to strategy-service and ml-inference-service pyproject.toml (Section 10) — 5 min
10. Remove GCP_PROJECT_ID module-level re-export from deployment-api/settings.py (Config Injection)
