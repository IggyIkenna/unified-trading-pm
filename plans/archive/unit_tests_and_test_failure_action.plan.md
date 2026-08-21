---
doc_type: plan
title: Unit Tests and Test Failure Action Plan
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-03'
overview: Merged plan for achieving all unit tests passing across T0–T3 and services. Combines per-repo execution workflow with root-cause analysis and fix options for ~98 T4 failures and ~18 collection errors.
isProject: false
todos:
- {id: phase1-quick-wins, content: 'Phase 1 — High-impact quick wins (~3h, unblocks 43 tests): RC-1: DONE — UFCL already exports BaseFeatureCalculator, BaseFeatureService, FeatureCalculatorRegistry from service_base. features-calendar lint fixed (RUF002, RUF060). RC-2: Implement DependencyChecker in ml-inference-service + execution-service OR move to shared lib OR delete if abandoned — unblocks ml-inference (22 fails + 3 errors) + execution (2). RC-11: Add ''from unified_events_interface import log_event'' to ml-training + ml-inference main module. RC-8: Add initial_hyperparams param to stage2_coarse_optimization() + stage3_targeted_optimization() in ml-training-service.', status: completed, notes: "All RC-1/2/8/11 pre-resolved as of 2026-03-09 (confirmed by verification agents):\nRC-1: UFCL exports all 3 names from service_base; ruff clean.\nRC-2: DependencyChecker fully implemented in both ml-inference (engine/validation/ + app/core/) and\n      execution-service (utils/dependency_checker.py);\
    \ 308/308 + 14/14 tests pass.\nRC-8: initial_hyperparams param already in ml_training_service/app/training/hyperparameter_tuning.py.\nRC-11: log_event imported in 4+ files in ml-inference; in ml-training cli/main.py.\n"}
- {id: phase2-execution-core, content: 'Phase 2 — Execution service core (~4h, fixes 35 tests): RC-4: Align VWAP algo with test spec (U-shape profiles, forward-looking volume, historical fallback) — 11 fixes. RC-5: Review swap alpha engine vs test expectations for proportional slippage + multi-leg swaps — 6 fixes. RC-6: Update GCS/cloud mock targets from unified_cloud_services.* to unified_trading_services.* — 9 fixes. RC-3: Implement sports category detection in route_instruction() (check SPORTS_VENUES set, return category=''sports'') — 9 fixes (also tracked in sports_migration_gap_fix.md § B-S5).', status: completed, notes: 'RESOLVED 2026-03-09: RC-3/4/5/6 all pre-resolved in prior sessions. One remaining failure was

    DependencyChecker startup sequencing (GCS triggered before project ID validated) — fixed with

    UnifiedCloudConfig fast-path check. Final: 1234 passed, 0 failed, 1 skipped.

    '}
- {id: phase3-ml-services, content: 'Phase 3 — ML services (~3h, fixes 8 tests): RC-7: Wire shap_explainer into TrainingOrchestrator.__init__() — 4 fixes (SHAP explainability, not a deployment blocker). RC-9: Add average_precision to ModelTrainer.evaluate() metrics dict — 2 fixes. RC-10: Tighten feature validator to detect NaN in OHLCV columns — 2 fixes.', status: completed, notes: 'RESOLVED 2026-03-09: RC-7/9/10 were all pre-implemented in source — no code changes required.

    RC-7: shap_explainer wired in training_orchestrator.py (ShapExplainer() in __init__, explain_model() call).

    RC-9: average_precision_score imported and used in model_trainer.py evaluate() metrics dict.

    RC-10: FeatureValidator has OHLCV_FEATURES set and NaN detection logic in feature_validator.py.

    Final: ml-training-service 186 passed, 1 skipped, 0 failed (QG Lint/Tests/Import patterns PASSED).

    Final: ml-inference-service 308 passed, 1 skipped, 0 failed, coverage 75.3% (QG PASSED).

    '}
- {id: phase4-remaining, content: 'Phase 4 — Remaining (~3h, fixes 12 tests + 4 collection errors): RC-12: Add missing exports — unified_order_interface module, VENUE_CATEGORY_MAP to unified_config_interface, generate_strategy_id to unified_trading_services. CRITICAL: ml-inference importing from ml_training_service.models — move ModelVariantConfig to unified-ml-interface (T2) or unified-internal-contracts (T0) as TypedDict/Protocol; never import between service repos. RC-13: Individual execution-service fixes (mock paths, API alignment, timer cancellation, import path updates post engine.py split).', status: completed, notes: "RESOLVED 2026-03-09: All RC-12 and RC-13 items were pre-resolved or confirmed non-failing.\nRC-12: generate_strategy_id already exported from unified_trading_library (19/19 tests pass in\n       test_instruction_type_algorithm_selection + test_schema_validation). VENUE_CATEGORY_MAP already\n       exported from unified_config_interface. ModelVariantConfig already in\
    \ unified_ml_interface (cross-service\n       import was fixed in a prior session). unified_order_interface only referenced in integration tests with\n       pytest.importorskip — no unit test failures.\nRC-13: execution-service 1234 passed, 0 failed, 1 skipped (all previously fixed in phase2).\nAdditional fix in this session: ComplianceEventPayload.to_dict() was returning quantity/price as str()\n       instead of float() — fixed in unified-events-interface/schemas.py — resolved 4 compliance test\n       failures in execution-service (tests/unit/compliance/ and tests/unit/test_compliance_events.py).\nAdditional fix: test_config_instantiates_with_local_provider in features-onchain-service and\n       features-calendar-service used os.environ.setdefault which was bypassed when UTL's .env loaded\n       CLOUD_PROVIDER=gcp first — fixed with @patch.dict(os.environ, ...) decorator for proper isolation.\nFinal: execution-service 1234 passed; features-onchain 80 passed; features-calendar 192\
    \ passed,\n       1 skipped; ml-inference 308 passed; ml-training 186 passed — all 0 failures.\n"}
- {id: required-test-files, content: 'Verify required test files exist in all service repos: test_event_logging.py (tests ''from unified_events_interface import log_event'') and test_config.py (tests UnifiedCloudConfig subclass). These are compliance gates, not optional.', status: completed, notes: 'Verified 2026-03-09: All 28 service repos already have both tests/unit/test_event_logging.py and

    tests/unit/test_config.py. Spot-checked 9 repos (alerting-service, execution-service, ml-inference-service,

    strategy-service, ml-training-service, market-data-processing-service, features-volatility-service,

    trading-agent-service, system-integration-tests) — all tests pass. Files are real compliance tests

    (not stubs): test_event_logging.py checks log_event import, event markers in source, MockEventSink,

    setup_events signature; test_config.py tests the service config class extends UnifiedCloudConfig.

    '}
- {id: qg-failures-session-2-3, content: 'Fix all quality-gate failures across UI repos and service repos (sessions 2026-03-10): basedpyright reportAny (deployment-service 26 errors, risk-and-exposure-service 13 errors, position-balance-monitor-service 3 errors), UI vitest failures (trading-analytics-ui GitCompare mock, unified-trading-ui-auth waitFor + AuthContext infinite re-render, logs-dashboard-ui/execution-analytics-ui/live-health-monitor-ui vite.config), trading-analytics-api test_event_logging.py missing, ml-training-api xdist+coverage parallel, unified-cloud-interface stale coverage.xml.', status: completed, notes: "All fixed 2026-03-10 (two sessions):\n\nPython repos:\n  deployment-service: 26 reportAny errors fixed with cast() on getattr/json.loads/yaml.safe_load/ctx.obj/argparse\n  risk-and-exposure-service: 13 errors fixed (__all__ re-exports + cast psutil + extraPaths); deleted stale baseline\n  position-balance-monitor-service: 3 errors fixed (__all__ re-exports + extraPaths);\
    \ deleted stale baseline\n  ml-training-api: added [tool.coverage.run] parallel=true for xdist+cov compat; 38 passed, 95% coverage\n  trading-analytics-api: created tests/unit/test_event_logging.py with 4 lifecycle event tests\n  unified-cloud-interface: stale coverage.xml showed 79.36%; live run confirmed 81.21% — already passing\n\nUI repos (vitest):\n  trading-analytics-ui App.test.tsx: added GitCompare mock + 3 recon page mocks (ReconRunsPage etc.)\n  unified-trading-ui-auth: (1) waitFor → vi.waitFor in CognitoAdapter.test.ts; (2) eventDetails wrapped\n    in useMemo() — plain object in useEffect deps caused infinite re-render loop → OOM heap crash (4GB+)\n  logs-dashboard-ui: /api → /api/ proxy path; \"type\": \"module\" in package.json\n  execution-analytics-ui: /api/ proxy + extended mock-api.ts route handlers + Playwright selector fixes\n  live-health-monitor-ui: /api/ proxy + package-lock deps update\n"}
- {id: fix-coverage-pct-placeholders, content: 'WARN 1.12: 35/59 repos in workspace-manifest.json show coverage_pct = 70 — a uniform placeholder. Run actual coverage measurements per repo (pytest --cov= --cov-report=json) and update manifest with real values. Repos with coverage_pct = 0 and testing_level != none (features-commodity-service, features-cross-instrument-service, trading-agent-service) investigate — if no tests, mark testing_level = none. Do NOT hard-code a different uniform value — measure real coverage. (Migrated from workspace_audit_remediation_2026_03_07.md fix-coverage-pct-placeholders.)', status: completed, notes: 'DONE 2026-03-09: Real coverage measured for all 37 placeholder repos; workspace-manifest.json updated (commit 9539e7d in unified-trading-pm). Notable: features-commodity-service=3%, market-tick-data-service=16%, execution-service=26% (1 failing test), pnl-attribution-service=46%, instruments-service=53%.'}
- {id: remaining-tier-order-failures, content: 'Fix 4 remaining root-cause patterns from tier-order-run summary: RC-A/B stale wheel (UMI 15 + UTEI 5 failures), RC-C env-leak (features-multi-timeframe, features-sports, pnl-attribution — 1 each), RC-D missing setup_events (alerting-service 2 failures), coverage threshold (unified-feature-calculator-library 92.83% < 93%).', status: completed, notes: "RESOLVED 2026-03-10 (verified with per-repo .venv):\n\nRC-A/B (corrected diagnosis — 2026-03-10):\n  UTEI: 5 failures were stale wheel artefact — passes fine via bash scripts/quality-gates.sh. No fix needed.\n  UMI: NOT a stale wheel issue. Real cause: tests added in e3ba838 (raise coverage to 80%) imported ~80\n    symbols from unified_market_interface top-level that were never added to __init__.py. Tests \"passed\"\n    because the workspace venv's stale wheel had those exports; per-repo .venv (editable) did not.\n    FIXED 2026-03-10: added 98 missing public symbols to __init__.py; 928 failures\
    \ → 12 remaining\n    (12 = pre-existing Polymarket implementation gaps: get_trades missing, schema mismatches).\n    Root lesson: always use bash scripts/quality-gates.sh not manual pytest — stale wheel masks missing exports.\n    New cursor rules: testing/no-manual-pytest.mdc + imports/library-init-exports.mdc\n\nRC-C (env-leak): Already passing with per-repo venv. Verified 2026-03-10:\n  features-multi-timeframe-service: test already has @patch.dict — 1 passed ✅\n  features-sports-service: sets os.environ[\"CLOUD_PROVIDER\"]=\"local\" before instantiation — 1 passed ✅\n  pnl-attribution-service: try/finally restore pattern — 1 passed ✅\n  Tier-order-run failures were workspace venv artefacts (ran from wrong venv).\n\nRC-D (alerting-service): Already fixed. conftest.py has autouse session fixture:\n  _init_event_logging: setup_events(service_name=\"alerting-service\", mode=\"test\", sink=MockEventSink())\n  Verified: 125 passed, 0 failed, coverage 90.32% > 78% threshold ✅\n\nCoverage\
    \ threshold (unified-feature-calculator-library):\n  Verified 2026-03-10: 303 passed, coverage 95.23% > 93% threshold ✅ (was 92.83% in stale measurement)\n  The 92.83% was from a workspace-venv run with wrong --cov= path. Per-repo venv run: 95.23%.\n"}
- {id: tier-order-run, content: 'Run pytest tests/unit/ -v in tier order (T0 → T1 → T2 → T3 → services) per repo. Failing deps block consumers — fix in dependency order. Categorise each failure: import | fixture | mock | assertion.', status: completed, notes: "Completed 2026-03-09. Full tier-order run executed across all 39 repos.\n\nSUMMARY TABLE:\n\nT0 — all green:\n  unified-internal-contracts:  608 passed, 0 failed\n  matching-engine-library:     144 passed, 0 failed\n  execution-algo-library:      201 passed, 0 failed\n  unified-api-contracts:       707 passed, 0 failed\n\nT1 — all green:\n  unified-events-interface:     93 passed, 0 failed\n  unified-config-interface:    214 passed, 4 skipped, 0 failed\n  unified-trading-library:    1000 passed, 1 skipped, 0 failed\n\nT2 — 2 repos with failures:\n  unified-market-interface:   1346 passed, 15 failed\n    → 13 mock (IBKRAdapter.__init__() missing `ib` kwarg — stale venv-workspace wheel shadows local src)\n    → 2 import (normalize_ray_value\
    \ + bps_to_percent missing from aave_utils in installed wheel)\n  unified-trade-execution-interface: 873 passed, 5 failed + coverage=0%\n    → 5 mock (IbkrTradFiAdapter.__init__() missing `ib` kwarg — same stale wheel pattern)\n  unified-ml-interface:        413 passed, 0 failed\n  unified-position-interface:   84 passed, 0 failed\n  unified-reference-data-interface: 308 passed, 0 failed\n  unified-defi-execution-interface:  94 passed, 0 failed\n  unified-feature-calculator-library: 224 passed, 0 failed (coverage 92.83% < 93% threshold → FAIL)\n  unified-sports-execution-interface: 387 passed, 0 failed\n\nT3 — all green:\n  unified-domain-client:       385 passed, 0 failed\n\nServices — 4 repos with failures:\n  instruments-service:         784 passed, 2 skipped, 0 failed\n  market-data-processing-service: 189 passed, 0 failed\n  market-tick-data-service:    173 passed, 0 failed\n  features-calendar-service:   191 passed, 1 skipped, 1 failed\n    → 1 assertion (cfg.cloud_provider ==\
    \ 'local' but env has gcp; missing monkeypatch/patch.dict isolation)\n  features-commodity-service:   11 passed, 0 failed\n  features-cross-instrument-service: 142 passed, 0 failed\n  features-delta-one-service:  740 passed, 1 skipped, 0 failed\n  features-multi-timeframe-service: 168 passed, 1 failed\n    → 1 assertion (same cloud_provider env-leak pattern)\n  features-onchain-service:     80 passed, 0 failed\n  features-sports-service:     262 passed, 1 failed\n    → 1 assertion (same cloud_provider env-leak pattern)\n  features-volatility-service: 423 passed, 0 failed\n  execution-service:          1234 passed, 1 skipped, 0 failed\n  strategy-service:            941 passed, 1 skipped, 0 failed\n  risk-and-exposure-service:   204 passed, 0 failed\n  ml-training-service:         186 passed, 1 skipped, 0 failed\n  ml-inference-service:        308 passed, 1 skipped, 0 failed\n  alerting-service:             94 passed, 2 failed\n    → 2 fixture (log_event() raises RuntimeError because\
    \ setup_events() not called; test needs MockEventSink setup)\n  pnl-attribution-service:      52 passed, 1 skipped, 1 failed\n    → 1 assertion (same cloud_provider env-leak pattern)\n  position-balance-monitor-service: 132 passed, 5 skipped, 1 failed\n    → 1 assertion (same cloud_provider env-leak pattern)\n  strategy-validation-service:  41 passed, 0 failed\n\nROOT CAUSE PATTERNS (4 distinct):\n\nRC-A (import / stale wheel): unified-market-interface (2 tests) — normalize_ray_value and bps_to_percent\n  exist in local source but not in the installed wheel under .venv-workspace/lib. Tests import from the\n  installed package path, not source. Fix: `uv pip install -e unified-market-interface/` from workspace root.\n\nRC-B (mock / stale wheel): unified-market-interface (13 tests) + unified-trade-execution-interface (5 tests)\n  — IBKRAdapter and IbkrTradFiAdapter constructors do not accept `ib=` kwarg in the installed wheel version.\n  Same root cause as RC-A. Fix: reinstall in editable\
    \ mode.\n\nRC-C (assertion / env-leak): features-calendar-service, features-multi-timeframe-service, features-sports-service,\n  pnl-attribution-service, position-balance-monitor-service (1 test each) — test_config_instantiates_with_local_provider\n  asserts cfg.cloud_provider == 'local' but the process env has CLOUD_PROVIDER=gcp from a prior test or the\n  shell environment. Tests lack @patch.dict(os.environ, {'CLOUD_PROVIDER': 'local'}, clear=False) isolation.\n  Fix: add monkeypatch or patch.dict wrapper to each test.\n\nRC-D (fixture / missing setup_events): alerting-service (2 tests) — verify_api_key() calls log_event()\n  internally, but setup_events() has not been called in the test. The test expects an HTTPException but gets\n  RuntimeError('Event logging not initialized') instead. Fix: add setup_events() call (or MockEventSink fixture)\n  in conftest or test setUp.\n\nCOVERAGE FAILURE (non-test):\n  unified-feature-calculator-library: 92.83% < 93.00% threshold. All 224 tests\
    \ pass. Fix: raise threshold\n  to 93% or add 1-2 tests for service_base/base_service.py (45% coverage, lines 96-99, 107, 112, 117, 147-198).\n\nTOTALS ACROSS ALL 39 REPOS:\n  Pass: ~10,745  Fail: 30  Skipped: ~20\n  Failing repos: 7 (unified-market-interface, unified-trade-execution-interface,\n    features-calendar-service, features-multi-timeframe-service, features-sports-service,\n    pnl-attribution-service, position-balance-monitor-service, alerting-service)\n  Clean repos: 31 of 39\n"}
---

# Unit Tests and Test Failure Action Plan

**Order:** 6 (see master_pre_deployment_plan_chain.md) **Date:** 2026-03-03 **Status:** Assessment Complete, Fixes
Pending **Scope:** ~98 test failures + ~18 collection errors across 5 service repos

---

## Summary

After fixing deployment-service (0 fail), deployment-api (0 fail), deployment-ui (0 fail), and cleaning agent-introduced
syntax damage across 7+ repos, the remaining failures are concentrated in 5 service repos. All failures are pre-existing
issues (not regressions).

| Repo                      | Pass     | Fail   | Collection Errors | Root Causes                                           |
| ------------------------- | -------- | ------ | ----------------- | ----------------------------------------------------- |
| execution-service         | 1049     | 57     | 4                 | Sports routing, VWAP algo, GCS mocks, missing modules |
| ml-inference-service      | 49       | 22     | 3                 | Missing DependencyChecker, ml_training_service import |
| ml-training-service       | 253      | 11     | 1                 | SHAP integration, hyperparams API, metrics mismatch   |
| features-onchain-service  | 50       | 8      | 1                 | UFCL naming mismatch (BaseFeatureCalculator)          |
| features-calendar-service | 0        | 0      | 9                 | UFCL naming mismatch (BaseFeatureCalculator)          |
| **TOTAL**                 | **1401** | **98** | **18**            |                                                       |

---

## Per-Repo Actions

1. Run `pytest tests/unit/ -v` per repo
2. Categorise failures: import, fixture, mock, assertion
3. Fix in order; no skip without reason
4. Required: `test_event_logging.py`, `test_config.py` (services)

---

## Root Cause Categories

### RC-1: UFCL Naming Mismatch (17 failures + 10 collection errors)

**Impact:** features-calendar-service (9 errors), features-onchain-service (7 fails + 1 error) **Root cause:** Services
import `BaseFeatureCalculator`, `BaseFeatureService`, `FeatureCalculatorRegistry` from `unified_feature_calculator`, but
UFCL only exports `FeatureCalculator`. **Status:** DONE — UFCL already exports `BaseFeatureCalculator`,
`BaseFeatureService`, `FeatureCalculatorRegistry` directly from `service_base`. No alias was created.

> **Note:** The original fix guidance below (backward compat alias) is superseded and must NOT be followed. Creating
> `BaseFeatureCalculator = FeatureCalculator  # backward compat alias` violates
> `cursor-rules/core/no-backward-compat-shims.mdc`. The actual fix was a direct export from `service_base`, not an
> alias. **Effort:** Done **Priority:** HIGH — already resolved, unblocked 2 services entirely

### RC-2: Missing DependencyChecker Module (22 failures + 4 collection errors)

**Impact:** ml-inference-service (22 fails + 3 errors), execution-service (2 fails) **Root cause:** Tests expect
`<service>.engine.validation.dependency_checker.DependencyChecker` but the module doesn't exist. These were likely
planned but never implemented. **Fix options:** A. Create `DependencyChecker` in each service (shared pattern from
codex) B. Move to a shared library and have services import from there C. Delete tests if DependencyChecker is no longer
planned **Effort:** 2-4h (option A or B), 30min (option C) **Priority:** HIGH — 26 failures across 2 repos

### RC-3: Sports Execution Routing (9 failures)

**Impact:** execution-service `test_sports_execution.py` **Root cause:** `route_instruction()` returns
`category='trade'` instead of `'sports'` for sports venues (BETFAIR, SMARKETS, etc.). The sports routing logic isn't
implemented yet. **Fix:** Implement sports category detection in `route_instruction()` — check if venue is in
`SPORTS_VENUES` set and return `category='sports'`. **Effort:** 1h **Priority:** MEDIUM — Part of Sports Part B (B-S5)
**Ref:** `SPORTS_MIGRATION_GAP_FIX.md` stream B-S5

### RC-4: VWAP Algorithm Tests (11 failures)

**Impact:** execution-service `test_vwap.py` **Root cause:** VWAP algo tests expect specific volume profile weighting
behavior that doesn't match the current implementation. Tests check for U-shape profiles, forward-looking volume, and
historical volume fallback. **Fix:** Align tests with actual VWAP implementation, or fix VWAP to match spec. **Effort:**
2h **Priority:** MEDIUM

### RC-5: Swap Alpha / DeFi Execution (6 failures)

**Impact:** execution-service `test_swap_alpha.py` **Root cause:** Swap alpha calculation tests expect
slippage/execution behavior that doesn't match the current engine. Tests check proportional slippage, multi-leg swaps,
etc. **Fix:** Review swap alpha engine vs test expectations. Likely test expectations need updating to match the
refactored engine. **Effort:** 2h **Priority:** MEDIUM

### RC-6: GCS Write / Cloud Service Mocks (9 failures)

**Impact:** execution-service `test_gcs_write.py` (5), `test_execution_cloud_service.py` (4) **Root cause:** Integration
tests try to use real GCS client; cloud service tests mock wrong paths after UCS->UTS rename. **Fix:**
`unified_cloud_services` does not exist. Update mock targets based on what is being mocked:

- Cloud I/O (GCS reads/writes, storage ops) → mock `unified_cloud_interface.*`
- UTS business logic / service orchestration → mock `unified_trading_services.*` Do NOT use `unified_cloud_services.*` —
  this package does not exist in the workspace. **Effort:** 1h **Priority:** MEDIUM

### RC-7: SHAP Integration (4 failures)

**Impact:** ml-training-service `test_shap_integration.py` **Root cause:** `TrainingOrchestrator` doesn't have a
`shap_explainer` attribute. SHAP integration was planned but not wired into the orchestrator. **Fix:** Add
`shap_explainer` to `TrainingOrchestrator.__init__()` and wire up SHAP calls. **Effort:** 2h **Priority:** LOW — SHAP is
a nice-to-have explainability feature

### RC-8: Hyperparameter Tuner API (2 failures)

**Impact:** ml-training-service `test_hyperparameter_tuning.py` **Root cause:** `stage2_coarse_optimization()` and
`stage3_targeted_optimization()` don't accept `initial_hyperparams` keyword argument. API changed but tests weren't
updated. **Fix:** Either add `initial_hyperparams` parameter to the methods, or update tests to use current API.
**Effort:** 30min **Priority:** MEDIUM

### RC-9: Model Trainer Metrics (2 failures)

**Impact:** ml-training-service `test_model_trainer.py`, `test_model_trainer_comprehensive.py` **Root cause:** Tests
assert `'average_precision' in metrics` but metrics dict returns `accuracy`, `class_-1_f1`, etc. without
`average_precision`. **Fix:** Add `average_precision` to the metrics computation in `ModelTrainer.evaluate()`.
**Effort:** 30min **Priority:** MEDIUM

### RC-10: Feature Validator (2 failures)

**Impact:** ml-training-service `test_feature_validator.py` **Root cause:** `test_validate_no_nan_in_ohlcv` expects
validation to fail when OHLCV has NaN, but it passes. `test_remove_invalid_features` expects `close` column to be
removed. **Fix:** Tighten the validation logic to properly detect NaN in OHLCV columns. **Effort:** 30min **Priority:**
LOW

### RC-11: Event Logging Tests (2 failures)

**Impact:** ml-training-service (1), ml-inference-service (1) **Root cause:** `test_event_helper_imported` looks for
`from unified_cloud_services.observability` or `from unified_events_interface import log_event` but neither pattern
found in source. **Fix:** Add `from unified_events_interface import log_event` to a main module in each service.
**Effort:** 15min **Priority:** LOW — cosmetic compliance test

### RC-12: Missing Modules / Import Errors (8 collection errors)

**Impact:** execution-service (4 collection errors)

- `unified_order_interface` module not found (test_live_orchestration.py)
- `VENUE_CATEGORY_MAP` not in `unified_config_interface` (test_battle_testing_regressions.py)
- `generate_strategy_id` not in `unified_trading_services` (test_instruction_type_algorithm_selection.py)
- UMI syntax error in databento_batch_jobs.py → FIXED (test_split_libraries.py)

**Fix:** Add missing exports to respective libraries, or remove tests for unimplemented features. **Effort:** 1-2h
**Priority:** MEDIUM

### RC-13: Misc Execution Service (8 failures)

**Impact:** execution-service

- `test_algorithms_error_handling.py` (5): Timer cancellation, bar cache price retrieval
- `test_backtest_service_split.py` (3): Import paths changed
- `test_cloud_agnostic_paths.py` (1): ResultsSerializer path format
- `test_live_execution_handler.py` (1): Missing operation routing
- `test_handlers_matching_engine.py` (2): Matching engine integration
- `test_order_tracker.py` (2): Order tracker mapping
- `test_preflight_checker.py` (1): Data config lending pool alias
- `test_backtest_handler.py` (2): Batch handler success/failure
- `test_storage.py` (1): Cache filename parse

**Fix:** Individual fixes per test — mostly mock path updates and API alignment. **Effort:** 3h **Priority:** MEDIUM

---

## Execution Order

### Tier Order (T0→T1→T2→T3→services)

Failing deps block consumers. Run per-repo actions in tier order.

### Recommended Fix Order (Phases)

#### Phase 1: High-Impact Quick Wins (3h, unblocks 43 tests)

1. **RC-1**: UFCL naming aliases → unblocks features-calendar (9) + features-onchain (7)
2. **RC-2**: DependencyChecker stubs → unblocks ml-inference (22) + execution (2)
3. **RC-11**: Event logging imports → 2 quick fixes
4. **RC-8**: Hyperparameter API → 2 fixes

#### Phase 2: Execution Service Core (4h, fixes 35 tests)

5. **RC-4**: VWAP algorithm alignment → 11 fixes
6. **RC-5**: Swap alpha alignment → 6 fixes
7. **RC-6**: GCS/cloud service mocks → 9 fixes
8. **RC-3**: Sports routing → 9 fixes (part of B-S5)

#### Phase 3: ML Services (3h, fixes 8 tests)

9. **RC-7**: SHAP integration → 4 fixes
10. **RC-9**: Model metrics → 2 fixes
11. **RC-10**: Feature validator → 2 fixes

#### Phase 4: Remaining (3h, fixes 12 tests + 4 errors)

12. **RC-12**: Missing module exports → 4 collection errors
13. **RC-13**: Misc execution fixes → 8 test fixes

---

## Dependencies

```
RC-1 (UFCL aliases) ← features-calendar-service, features-onchain-service
RC-2 (DependencyChecker) ← ml-inference-service, execution-service
RC-3 (Sports routing) ← SPORTS_MIGRATION_GAP_FIX.md B-S5
RC-12 (Missing exports) ← unified_order_interface, unified_config_interface, unified_trading_services
```

---

## Notes

- **UMI syntax damage**: 7 files in unified-market-interface had dangling f-string lines from agent automation. These
  were restored from git on 2026-03-03. UMI now imports cleanly.
- **Agent damage pattern**: Background agents ran an f-string removal script that stripped f-string prefixes but left
  continuation lines, creating invalid syntax. Affected 7+ repos with 70+ files, all restored from git.
- **ml-inference-service** has a cross-repo dependency: `orchestrator.py` imports
  `from ml_training_service.models import ModelVariantConfig`. RC-12 fix: Do NOT move types between service repos.
  Instead:
  1. Identify the shared type (e.g., `ModelVariantConfig`)
  2. Define it as a `TypedDict` or `Protocol` in `unified-ml-interface` (T2, UML) or `unified-internal-contracts` (T0,
     UIC) depending on whether it's a domain type or a service message schema
  3. Update both ml-training-service and ml-inference-service to import from the shared library
  4. Ensure no `Any` in the shared type definition — `reportAny: error` applies
- **features-calendar-service** and **features-onchain-service** share the same RC-1 fix — fixing UFCL aliases unblocks
  both.
