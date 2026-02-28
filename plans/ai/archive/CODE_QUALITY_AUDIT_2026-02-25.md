# Code Quality Audit — unified-trading-system-repos

**Date:** 2026-02-25  
**Scope:** 14 Python service repos (instruments-service, market-tick-data-handler, market-data-processing-service, strategy-service, ml-training-service, ml-inference-service, risk-and-exposure-service, execution-services, features-*, pnl-attribution-service, position-balance-monitor-service)

---

## Executive Summary

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| File size violations | 2 | 16 | — | — | 18 |
| Function complexity (>100 lines) | 8 | 17 | — | — | 25+ |
| Class complexity (>500 lines) | 5 | 15 | — | — | 20+ |
| DRY / duplicate code | 4 | 6 | — | — | 10 |
| Import violations | — | — | ~50 | ~350 | ~400 |
| Deprecated files (_old, _original) | 5 | — | — | — | 5 |

---

## 1. File Size Violations

**Codex rule:** Files >1500 lines = critical; >900 lines = warning. Target: <500 for most modules.

### 1.1 CRITICAL (>1500 lines)

| Lines | File |
|-------|------|
| 3016 | `execution-services/visualizer-api/app/services/backtest_service.py` |
| 1510 | `execution-services/tests/live/venues/cefi/test_binance_live_execution.py` |

### 1.2 HIGH (>900 lines)

| Lines | File |
|-------|------|
| 1280 | `execution-services/visualizer-ui/backend/instruction_api.py` |
| 1208 | `market-tick-data-handler/market_data_tick_handler/engine/validation/validation_service.py` |
| 1192 | `instruments-service/instruments_service/app/core/instruments_service.py` |
| 1182 | `strategy-service/presentation/create_presentation.py` |
| 1175 | `market-tick-data-handler/market_data_tick_handler/app/venues/databento/databento_client_original.py` |
| 1175 | `market-tick-data-handler/market_data_tick_handler/engine/venues/databento/databento_client.py` |
| 1130 | `strategy-service/tests/e2e/test_modernized_strategies_e2e.py` |
| 1124 | `instruments-service/instruments_service/config/instrument_definitions.py` |
| 1064 | `execution-services/execution_services/config/grid_generator_old.py` |
| 1058 | `execution-services/execution_services/cli/backtest_old.py` |
| 1042 | `execution-services/visualizer-api/app/services/results_service.py` |
| 1025 | `execution-services/execution_services/benchmark/comparison.py` |
| 1024 | `execution-services/tests/live/deribit/test_predefined_orders.py` |
| 1015 | `market-tick-data-handler/market_data_tick_handler/cli/handlers/download_handler_original.py` |
| 1013 | `instruments-service/tests/unit/test_instruments_service.py` |
| 1008 | `execution-services/execution_services/data/config/trades_builder_old.py` |

---

## 2. Function Complexity (>100 lines)

**Target:** Functions <100 lines. Extract helpers, split by responsibility.

### 2.1 CRITICAL (>400 lines)

| Lines | Function | File:Line |
|-------|----------|-----------|
| 975 | `build_trades_config_impl` | `execution-services/execution_services/data/config/trades_builder_old.py:34` |
| 689 | `_format_human_readable_error` | `execution-services/visualizer-api/app/services/backtest_service.py:2088` |
| 600 | `_parse_error` | `execution-services/visualizer-api/app/services/backtest_service.py:736` |
| 422 | `generate_benchmark_html_report` | `execution-services/execution_services/benchmark/html_report.py:13` |
| 416 | `generate_html_report` | `execution-services/scripts/benchmark_runners/populate_benchmark_html.py:191` |
| 410 | `_get_algorithm_configs` | `execution-services/execution_services/benchmark/comparison.py:241` |

### 2.2 HIGH (100–400 lines)

| Lines | Function | File:Line |
|-------|----------|-----------|
| 374 | `create_timeframe_candles` | `market-data-processing-service/.../timeframe_candles.py:55` |
| 339 | `generate_comprehensive_instruction_stream` | `execution-services/scripts/instruction_generation/.../comprehensive_generation.py:7` |
| 333 | `create_implementation_section` | `strategy-service/presentation/create_presentation.py:526` |
| 329 | `build_timeline` | `execution-services/execution_services/results/timeline.py:171` |
| 326 | `_parse_preflight_error` | `execution-services/visualizer-api/app/services/backtest_service.py:1413` |
| 305 | `run_strategy_backtest` | `strategy-service/.../full_pipeline_backtest_service.py:62` |
| 303 | `run_backtest` | `strategy-service/.../backtest_service.py:58` |
| 299 | `_execute_instrument_generation` | `instruments-service/.../instrument_handler.py:122` |
| 292 | `main` | `instruments-service/scripts/test_batch_cost_comparison.py:52` |
| 291 | `store_instruments` | `instruments-service/.../cloud_instrument_storage.py:125` |
| 288 | `parse_arguments` | `market-tick-data-handler/.../parser.py:21` |
| 283 | `_get_css_styles` | `market-tick-data-handler/scripts/generate_test_report.py:59` |
| 281 | `main` | `execution-services/execution_services/config/grid_generator_old.py:780` |
| 281 | `_build_cases` | `execution-services/scripts/runners/run_phasee_fullpath_matrix.py:278` |
| 279 | `_load_and_filter_instruments_for_date` | `market-tick-data-handler/.../download_handler_original.py:737` |
| 276 | `_execute_download` | `market-tick-data-handler/.../download_handler_original.py:460` |
| 272 | `create_html_presentation` | `strategy-service/presentation/create_presentation.py:861` |
| 271 | `save_report` | `execution-services/execution_services/results/serializer.py:283` |
| 263 | `fetch_defi_instruments` | `instruments-service/.../defi_processor.py:97` |

---

## 3. Class Complexity (>500 lines)

**Target:** Classes <500 lines. Split by SRP; extract mixins or helpers.

### 3.1 CRITICAL (>1000 lines)

| Lines | Class | File:Line |
|-------|-------|-----------|
| 2982 | `BacktestService` | `execution-services/visualizer-api/app/services/backtest_service.py:35` |
| 1135 | `InstrumentsService` | `instruments-service/.../instruments_service.py:58` |
| 1115 | `ValidationService` | `market-tick-data-handler/.../validation_service.py:35` |
| 1110 | `DatabentoClient` | `market-tick-data-handler/.../databento_client_original.py:49` |
| 1110 | `DatabentoClient` | `market-tick-data-handler/.../databento_client.py:49` |

### 3.2 HIGH (500–1000 lines)

| Lines | Class | File:Line |
|-------|-------|-----------|
| 1012 | `ResultsService` | `execution-services/visualizer-api/app/services/results_service.py:31` |
| 993 | `BenchmarkComparator` | `execution-services/execution_services/benchmark/comparison.py:33` |
| 864 | `DownloadHandler` | `market-tick-data-handler/.../download_handler_original.py:152` |
| 830 | `CCXTService` | `instruments-service/.../engine/venues/ccxt_service.py:31` |
| 813 | `CCXTService` | `instruments-service/.../utils/ccxt_service.py:31` |
| 801 | `CandleProcessingService` | `market-data-processing-service/.../candle_processing_service.py:48` |
| 725 | `RecursiveStakedBasisStrategy` | `strategy-service/.../defi_recursive_basis.py:30` |
| 721 | `DeFiDataLoader` | `execution-services/execution_services/data/defi_data_loader.py:76` |
| 716 | `HybridOptimalExecAlgorithm` | `execution-services/.../hybrid_optimal.py:38` |
| 715 | `CeFiInstrumentProcessor` | `instruments-service/.../cefi_processor.py:35` |
| 714 | `ROECalculator` | `strategy-service/strategy_analysis_presentation/code/roe/calculations.py:18` |
| 704 | `CandleOrchestrationService` | `market-data-processing-service/.../orchestration_service.py:46` |
| 700 | `BigQueryQualityGates` | `market-tick-data-handler/.../gcs_quality_gates.py:24` |
| 687 | `OnChainOrchestrationService` | `features-onchain-service/.../onchain_orchestration.py:17` |
| 684 | `NodeBuilder` | `execution-services/execution_services/engine/backtest/node_builder.py:26` |
| 673 | `DataService` | `execution-services/visualizer-api/app/services/data_service.py:52` |
| 663 | `MarketDataTickHandlerConfig` | `market-tick-data-handler/.../config_settings.py:20` |
| 657 | `ConfigManager` | `market-tick-data-handler/.../config_manager.py:59` |
| 626 | `ComprehensiveBacktestService` | `strategy-service/.../comprehensive_backtest_service.py:38` |
| 626 | `ResultExtractor` | `execution-services/execution_services/results/extractor.py:15` |

---

## 4. DRY Violations / Duplicate Code

### 4.1 CRITICAL — Duplicate implementations (delete one, keep canonical)

| Canonical Location | Duplicate | Notes |
|--------------------|-----------|-------|
| `instruments-service/.../engine/venues/ccxt_service.py` | `instruments-service/.../utils/ccxt_service.py` | Same `CCXTService` class (830 vs 813 lines). Consolidate to single location. |
| `market-tick-data-handler/.../engine/venues/databento/databento_client.py` | `.../app/venues/databento/databento_client_original.py` | Same `DatabentoClient` (1110 lines each). Delete `_original`. |
| `market-tick-data-handler/.../engine/orchestrators/*` | `.../app/core/orchestrators/*` | `venue_downloaders.py` uses engine; `__init__.py` exports app.core. Pick one. |
| `market-tick-data-handler/.../cli/handlers/download_handler.py` | `.../download_handler_original.py` | 864-line `DownloadHandler` in `_original`. Consolidate. |

### 4.2 Deprecated / legacy files (per delete-deprecated rule)

| File | Action |
|------|--------|
| `execution-services/execution_services/config/grid_generator_old.py` | Delete; migrate to new implementation |
| `execution-services/execution_services/cli/backtest_old.py` | Delete; migrate to new implementation |
| `execution-services/execution_services/data/config/trades_builder_old.py` | Delete; migrate to new implementation |

---

## 5. Import Violations

**Rule:** Imports at top of file only. Lazy imports only for optional deps (whitelisted in QUALITY_GATE_BYPASS_AUDIT.md).

### 5.1 Scope

- **~398 files** contain indented `import` or `from ... import` (inside functions/methods).
- Many are **whitelisted** (dependency_checker, config, optional deps, circular-import avoidance).
- **~50 source files** (excluding tests/scripts) have non-whitelisted inline imports.

### 5.2 Sample source files with inline imports

| File |
|------|
| `instruments-service/instruments_service/config/service_config.py` |
| `instruments-service/instruments_service/engine/venues/ccxt_service.py` |
| `instruments-service/instruments_service/engine/operations/instruments/orchestration/cefi_orchestration.py` |
| `instruments-service/instruments_service/app/core/processors/canonical_key_generator.py` |
| `instruments-service/instruments_service/app/core/cloud_instrument_storage.py` |
| `strategy-service/presentation/create_presentation.py` |
| `ml-training-service/ml_training_service/app/core/config_loader.py` |
| `ml-inference-service/ml_inference_service/app/core/feature_subscriber.py` |

**Note:** Per-repo `QUALITY_GATE_BYPASS_AUDIT.md` documents whitelisted files. Non-whitelisted inline imports should be moved to top of file.

---

## 6. Severity Scoring

| Severity | Criteria |
|----------|----------|
| **Critical** | Blocks maintainability; immediate refactor needed. Files >1500 lines, functions >400 lines, classes >1000 lines, duplicate implementations, deprecated `_old`/`_original` files. |
| **High** | Significant technical debt. Files >900 lines, functions 100–400 lines, classes 500–1000 lines. |
| **Medium** | Should be addressed in normal refactor cycle. Import violations in source (non-whitelisted). |
| **Low** | Informational. Import violations in tests/scripts; many whitelisted. |

---

## 7. Top 10 Worst Offenders

| Rank | File | Lines | Issues |
|------|------|-------|--------|
| 1 | `execution-services/visualizer-api/app/services/backtest_service.py` | 3016 | Critical file size; God class (2982 lines); 3 functions 326–689 lines |
| 2 | `execution-services/tests/live/venues/cefi/test_binance_live_execution.py` | 1510 | Critical file size |
| 3 | `execution-services/visualizer-ui/backend/instruction_api.py` | 1280 | High file size |
| 4 | `market-tick-data-handler/.../validation_service.py` | 1208 | High file size; God class (1115 lines) |
| 5 | `instruments-service/.../instruments_service.py` | 1192 | High file size; God class (1135 lines) |
| 6 | `strategy-service/presentation/create_presentation.py` | 1182 | High file size; 2 functions 272–333 lines |
| 7 | `market-tick-data-handler/.../databento_client.py` + `_original` | 1175×2 | DRY violation; God class (1110 lines each) |
| 8 | `execution-services/execution_services/data/config/trades_builder_old.py` | 1008 | Deprecated; function 975 lines |
| 9 | `execution-services/execution_services/config/grid_generator_old.py` | 1064 | Deprecated |
| 10 | `instruments-service/.../engine/venues/ccxt_service.py` + `utils/ccxt_service.py` | 860+843 | DRY violation; duplicate CCXTService |

---

## 8. Recommended Actions

### Immediate (P0)

1. **Split `backtest_service.py`** — Extract error parsing, formatting, and subprocess logic into separate modules.
2. **Delete deprecated files** — `grid_generator_old.py`, `backtest_old.py`, `trades_builder_old.py`; migrate callers to new implementations.
3. **Consolidate CCXTService** — Keep one location (`engine/venues/ccxt_service.py`); delete `utils/ccxt_service.py`; update imports.
4. **Consolidate DatabentoClient** — Delete `databento_client_original.py`; use `engine/venues/databento/databento_client.py`.

### Short-term (P1)

5. **Unify orchestrators** — Pick `app/core` or `engine` as canonical; delete duplicate orchestrator copies.
6. **Split `build_trades_config_impl`** — Break 975-line function into smaller helpers.
7. **Split `InstrumentsService`** — Extract venue-specific logic into adapters.
8. **Split `ValidationService`** — Extract validation rules into separate modules.

### Medium-term (P2)

9. **Address remaining >900-line files** — Per `file-splitting-guide.md`.
10. **Audit import violations** — Move non-whitelisted inline imports to top of file.

---

## References

- Codex: `06-coding-standards/file-splitting-guide.md`
- Rule: `.cursor/rules/file-size-limit.mdc` (900 lines max)
- Rule: `.cursor/rules/delete-deprecated.mdc`
- Per-repo: `QUALITY_GATE_BYPASS_AUDIT.md` (import whitelist)
