---
name: Unit Tests and Test Failure Action Plan
overview: Merged plan for achieving all unit tests passing across T0–T3 and services. Combines per-repo execution workflow with root-cause analysis and fix options for ~98 T4 failures and ~18 collection errors.
isProject: false
todos:
  - id: phase1-quick-wins
    content: "Phase 1 — High-impact quick wins (~3h, unblocks 43 tests): RC-1: DONE — UFCL already exports BaseFeatureCalculator, BaseFeatureService, FeatureCalculatorRegistry from service_base. features-calendar lint fixed (RUF002, RUF060). RC-2: Implement DependencyChecker in ml-inference-service + execution-service OR move to shared lib OR delete if abandoned — unblocks ml-inference (22 fails + 3 errors) + execution (2). RC-11: Add 'from unified_events_interface import log_event' to ml-training + ml-inference main module. RC-8: Add initial_hyperparams param to stage2_coarse_optimization() + stage3_targeted_optimization() in ml-training-service."
    status: pending
  - id: phase2-execution-core
    content: "Phase 2 — Execution service core (~4h, fixes 35 tests): RC-4: Align VWAP algo with test spec (U-shape profiles, forward-looking volume, historical fallback) — 11 fixes. RC-5: Review swap alpha engine vs test expectations for proportional slippage + multi-leg swaps — 6 fixes. RC-6: Update GCS/cloud mock targets from unified_cloud_services.* to unified_trading_services.* — 9 fixes. RC-3: Implement sports category detection in route_instruction() (check SPORTS_VENUES set, return category='sports') — 9 fixes (also tracked in sports_migration_gap_fix.plan.md § B-S5)."
    status: pending
  - id: phase3-ml-services
    content: "Phase 3 — ML services (~3h, fixes 8 tests): RC-7: Wire shap_explainer into TrainingOrchestrator.__init__() — 4 fixes (SHAP explainability, not a deployment blocker). RC-9: Add average_precision to ModelTrainer.evaluate() metrics dict — 2 fixes. RC-10: Tighten feature validator to detect NaN in OHLCV columns — 2 fixes."
    status: pending
  - id: phase4-remaining
    content: "Phase 4 — Remaining (~3h, fixes 12 tests + 4 collection errors): RC-12: Add missing exports — unified_order_interface module, VENUE_CATEGORY_MAP to unified_config_interface, generate_strategy_id to unified_trading_services. CRITICAL: ml-inference importing from ml_training_service.models — move ModelVariantConfig to unified-ml-interface (T2) or unified-internal-contracts (T0) as TypedDict/Protocol; never import between service repos. RC-13: Individual execution-service fixes (mock paths, API alignment, timer cancellation, import path updates post engine.py split)."
    status: pending
  - id: required-test-files
    content: "Verify required test files exist in all service repos: test_event_logging.py (tests 'from unified_events_interface import log_event') and test_config.py (tests UnifiedCloudConfig subclass). These are compliance gates, not optional."
    status: pending
  - id: tier-order-run
    content: "Run pytest tests/unit/ -v in tier order (T0 → T1 → T2 → T3 → services) per repo. Failing deps block consumers — fix in dependency order. Categorise each failure: import | fixture | mock | assertion."
    status: pending
---

# Unit Tests and Test Failure Action Plan

**Order:** 6 (see master_pre_deployment_plan_chain.plan.md)
**Date:** 2026-03-03
**Status:** Assessment Complete, Fixes Pending
**Scope:** ~98 test failures + ~18 collection errors across 5 service repos

---

## Summary

After fixing deployment-service (0 fail), deployment-api (0 fail), deployment-ui (0 fail), and cleaning agent-introduced syntax damage across 7+ repos, the remaining failures are concentrated in 5 service repos. All failures are pre-existing issues (not regressions).

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

**Impact:** features-calendar-service (9 errors), features-onchain-service (7 fails + 1 error)
**Root cause:** Services import `BaseFeatureCalculator`, `BaseFeatureService`, `FeatureCalculatorRegistry` from `unified_feature_calculator`, but UFCL only exports `FeatureCalculator`.
**Fix:** Add aliases in UFCL `__init__.py`:

```python
BaseFeatureCalculator = FeatureCalculator  # backward compat alias
```

Or create `BaseFeatureService` and `FeatureCalculatorRegistry` as proper classes.
**Effort:** 1h
**Priority:** HIGH — unblocks 2 services entirely

### RC-2: Missing DependencyChecker Module (22 failures + 4 collection errors)

**Impact:** ml-inference-service (22 fails + 3 errors), execution-service (2 fails)
**Root cause:** Tests expect `<service>.engine.validation.dependency_checker.DependencyChecker` but the module doesn't exist. These were likely planned but never implemented.
**Fix options:**
A. Create `DependencyChecker` in each service (shared pattern from codex)
B. Move to a shared library and have services import from there
C. Delete tests if DependencyChecker is no longer planned
**Effort:** 2-4h (option A or B), 30min (option C)
**Priority:** HIGH — 26 failures across 2 repos

### RC-3: Sports Execution Routing (9 failures)

**Impact:** execution-service `test_sports_execution.py`
**Root cause:** `route_instruction()` returns `category='trade'` instead of `'sports'` for sports venues (BETFAIR, SMARKETS, etc.). The sports routing logic isn't implemented yet.
**Fix:** Implement sports category detection in `route_instruction()` — check if venue is in `SPORTS_VENUES` set and return `category='sports'`.
**Effort:** 1h
**Priority:** MEDIUM — Part of Sports Part B (B-S5)
**Ref:** `SPORTS_MIGRATION_GAP_FIX.md` stream B-S5

### RC-4: VWAP Algorithm Tests (11 failures)

**Impact:** execution-service `test_vwap.py`
**Root cause:** VWAP algo tests expect specific volume profile weighting behavior that doesn't match the current implementation. Tests check for U-shape profiles, forward-looking volume, and historical volume fallback.
**Fix:** Align tests with actual VWAP implementation, or fix VWAP to match spec.
**Effort:** 2h
**Priority:** MEDIUM

### RC-5: Swap Alpha / DeFi Execution (6 failures)

**Impact:** execution-service `test_swap_alpha.py`
**Root cause:** Swap alpha calculation tests expect slippage/execution behavior that doesn't match the current engine. Tests check proportional slippage, multi-leg swaps, etc.
**Fix:** Review swap alpha engine vs test expectations. Likely test expectations need updating to match the refactored engine.
**Effort:** 2h
**Priority:** MEDIUM

### RC-6: GCS Write / Cloud Service Mocks (9 failures)

**Impact:** execution-service `test_gcs_write.py` (5), `test_execution_cloud_service.py` (4)
**Root cause:** Integration tests try to use real GCS client; cloud service tests mock wrong paths after UCS->UTS rename.
**Fix:** Update mock targets from `unified_cloud_services.*` to `unified_trading_services.*` or mock at the correct abstraction level.
**Effort:** 1h
**Priority:** MEDIUM

### RC-7: SHAP Integration (4 failures)

**Impact:** ml-training-service `test_shap_integration.py`
**Root cause:** `TrainingOrchestrator` doesn't have a `shap_explainer` attribute. SHAP integration was planned but not wired into the orchestrator.
**Fix:** Add `shap_explainer` to `TrainingOrchestrator.__init__()` and wire up SHAP calls.
**Effort:** 2h
**Priority:** LOW — SHAP is a nice-to-have explainability feature

### RC-8: Hyperparameter Tuner API (2 failures)

**Impact:** ml-training-service `test_hyperparameter_tuning.py`
**Root cause:** `stage2_coarse_optimization()` and `stage3_targeted_optimization()` don't accept `initial_hyperparams` keyword argument. API changed but tests weren't updated.
**Fix:** Either add `initial_hyperparams` parameter to the methods, or update tests to use current API.
**Effort:** 30min
**Priority:** MEDIUM

### RC-9: Model Trainer Metrics (2 failures)

**Impact:** ml-training-service `test_model_trainer.py`, `test_model_trainer_comprehensive.py`
**Root cause:** Tests assert `'average_precision' in metrics` but metrics dict returns `accuracy`, `class_-1_f1`, etc. without `average_precision`.
**Fix:** Add `average_precision` to the metrics computation in `ModelTrainer.evaluate()`.
**Effort:** 30min
**Priority:** MEDIUM

### RC-10: Feature Validator (2 failures)

**Impact:** ml-training-service `test_feature_validator.py`
**Root cause:** `test_validate_no_nan_in_ohlcv` expects validation to fail when OHLCV has NaN, but it passes. `test_remove_invalid_features` expects `close` column to be removed.
**Fix:** Tighten the validation logic to properly detect NaN in OHLCV columns.
**Effort:** 30min
**Priority:** LOW

### RC-11: Event Logging Tests (2 failures)

**Impact:** ml-training-service (1), ml-inference-service (1)
**Root cause:** `test_event_helper_imported` looks for `from unified_cloud_services.observability` or `from unified_events_interface import log_event` but neither pattern found in source.
**Fix:** Add `from unified_events_interface import log_event` to a main module in each service.
**Effort:** 15min
**Priority:** LOW — cosmetic compliance test

### RC-12: Missing Modules / Import Errors (8 collection errors)

**Impact:** execution-service (4 collection errors)

- `unified_order_interface` module not found (test_live_orchestration.py)
- `VENUE_CATEGORY_MAP` not in `unified_config_interface` (test_battle_testing_regressions.py)
- `generate_strategy_id` not in `unified_trading_services` (test_instruction_type_algorithm_selection.py)
- UMI syntax error in databento_batch_jobs.py → FIXED (test_split_libraries.py)

**Fix:** Add missing exports to respective libraries, or remove tests for unimplemented features.
**Effort:** 1-2h
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

**Fix:** Individual fixes per test — mostly mock path updates and API alignment.
**Effort:** 3h
**Priority:** MEDIUM

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

- **UMI syntax damage**: 7 files in unified-market-interface had dangling f-string lines from agent automation. These were restored from git on 2026-03-03. UMI now imports cleanly.
- **Agent damage pattern**: Background agents ran an f-string removal script that stripped f-string prefixes but left continuation lines, creating invalid syntax. Affected 7+ repos with 70+ files, all restored from git.
- **ml-inference-service** has a cross-repo dependency: `orchestrator.py` imports `from ml_training_service.models import ModelVariantConfig`. RC-12 fix: Do NOT move types between service repos. Instead:
  1. Identify the shared type (e.g., `ModelVariantConfig`)
  2. Define it as a `TypedDict` or `Protocol` in `unified-ml-interface` (T2, UML) or `unified-internal-contracts` (T0, UIC) depending on whether it's a domain type or a service message schema
  3. Update both ml-training-service and ml-inference-service to import from the shared library
  4. Ensure no `Any` in the shared type definition — `reportAny: error` applies
- **features-calendar-service** and **features-onchain-service** share the same RC-1 fix — fixing UFCL aliases unblocks both.
