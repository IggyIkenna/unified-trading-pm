---
name: Repo Hardening Framework
overview: Implement a 5-pillar hardening framework (GCS standardization, unit tests, E2E tests, data catalog, dependency tracking) across all 12 repos, working upstream to downstream following the data dependency flow.
todos:
  - id: phase1-deployment
    content: "Phase 1: unified-trading-deployment-v3 - Add unit tests, data catalog CLI, dependency graph config"
    status: in_progress
  - id: phase2-instruments
    content: "Phase 2a: instruments-service - Add data_catalog.py script, document GCS paths"
    status: pending
  - id: phase2-tick-handler
    content: "Phase 2b: market-tick-data-handler - Add E2E tests, data_catalog.py, dependency_checker.py"
    status: pending
  - id: phase2-processing
    content: "Phase 2c: market-data-processing-service - Add E2E tests, data_catalog.py, dependency_checker.py"
    status: pending
  - id: phase3-calendar
    content: "Phase 3a: features-calendar-service - Expand unit tests (library only)"
    status: pending
  - id: phase3-delta-one
    content: "Phase 3b: features-delta-one-service - Add data_catalog.py, dependency_checker.py"
    status: pending
  - id: phase3-volatility
    content: "Phase 3c: features-volatility-service - Add unit tests, E2E, data_catalog.py, dependency_checker.py"
    status: pending
  - id: phase3-onchain
    content: "Phase 3d: features-onchain-service - Add unit tests, E2E, data_catalog.py, dependency_checker.py"
    status: pending
  - id: phase4-training
    content: "Phase 4a: ml-training-service - Add E2E, data_catalog.py, dependency_checker.py"
    status: pending
  - id: phase4-inference
    content: "Phase 4b: ml-inference-service - Add unit tests, E2E, data_catalog.py, dependency_checker.py"
    status: pending
  - id: phase5-strategy
    content: "Phase 5a: strategy-service - Add data_catalog.py, dependency_checker.py"
    status: pending
  - id: phase5-execution
    content: "Phase 5b: execution-service - Add unit tests, E2E for cefi/tradfi, data_catalog.py, dependency_checker.py"
    status: pending
isProject: false
---

# Repo Hardening Framework Implementation

## Architecture Overview

The hardening framework adds 5 capabilities to each service repo:

1. **GCS Path Standards** - Document current paths, validate at runtime
2. **Unit Tests** - Cover all CLI arg paths and combinatorics
3. **E2E Tests** - Generate one output per combinatoric (mock for speed, test buckets for quality gates)
4. **Data Catalog** - Per-service scripts aggregating to deployment repo
5. **Dependency Flow** - Declarative config + runtime checks

---

## Phase 1: Foundation (unified-trading-deployment-v3)

This repo drives everything. It needs tests, data catalog aggregation, and dependency graph tooling.

### 1.1 Add Unit Tests for Sharding System

File: [`tests/unit/test_shard_calculator.py`](unified-trading-deployment-v3/tests/unit/test_shard_calculator.py) (new)

Test all dimension types:

- Fixed dimensions (category values)
- Hierarchical dimensions (venue-category mappings)
- Date range dimensions (daily/weekly/monthly granularity)
- GCS dynamic dimensions (mock cloud client)

File: [`tests/unit/test_config_loader.py`](unified-trading-deployment-v3/tests/unit/test_config_loader.py) (new)

Test config loading for all 11 sharding configs.

### 1.2 Add Data Catalog Aggregation CLI

New command: `python -m unified_trading_deployment.cli catalog`

```python
# New file: unified_trading_deployment/catalog.py
def catalog_service(service: str, start_date: date, end_date: date) -> dict:
    """
    List GCS files for each combinatoric and return counts.
    Returns: {combinatoric: file_count} e.g., {"CEFI/BINANCE-FUTURES/2024-01-01": 15}
    """
```

Output: JSON/table showing completion percentage per combinatoric.

### 1.3 Add Dependency Graph CLI

New command: `python -m unified_trading_deployment.cli dependencies`

File: [`configs/dependencies.yaml`](unified-trading-deployment-v3/configs/dependencies.yaml) (new)

```yaml
services:
  instruments-service:
    upstream: []
    outputs:
      - bucket_template: "instruments-store-{category_lower}-{project_id}"
        path: "instrument_availability/by_date/day-{date}/instruments.parquet"
  
  market-tick-data-handler:
    upstream:
      - service: instruments-service
        required: true
        check: "instrument_availability/by_date/day-{date}/instruments.parquet"
    outputs:
      - bucket_template: "market-data-tick-{category_lower}-{project_id}"
        path: "raw_tick_data/by_date/day-{date}/data_type-{data_type}/{asset_class}/"
  # ... all 11 services
```

---

## Phase 2: Data I/O Layer (Upstream)

### 2.1 instruments-service (Already Well-Tested)

**Current State:** 25+ unit tests, 1 E2E test, test buckets exist

**Actions:**

- [ ] Add `scripts/data_catalog.py` - count instruments per category/venue/date
- [ ] Add `src/dependency_checker.py` - no upstream deps (root service)
- [ ] Document GCS paths in `docs/GCS_PATHS.md`
- [ ] Ensure all CLI arg paths have unit test coverage (audit existing tests)

**GCS Path Standard (document current):**

```
gs://instruments-store-{category}-{project_id}/
  instrument_availability/by_date/day-{YYYY-MM-DD}/instruments.parquet
```

### 2.2 market-tick-data-handler

**Current State:** ~40 test files but many archived/deprecated

**Actions:**

- [ ] Add missing unit tests for each venue adapter (TARDIS, Databento, DeFi protocols)
- [ ] Add E2E test using test bucket with fixture data for 1 representative date
- [ ] Add `scripts/data_catalog.py` - count files per category/venue/data_type/date
- [ ] Add `src/dependency_checker.py` - check instruments-service outputs exist
- [ ] Document GCS paths

**GCS Path Standard (document current):**

```
gs://market-data-tick-{category}-{project_id}/
  raw_tick_data/by_date/day-{YYYY-MM-DD}/data_type-{TYPE}/{asset_class}/{instrument}.parquet
```

**Dependency Check (runtime):**

```python
# In src/dependency_checker.py
def check_upstream_dependencies(date: str, category: str) -> bool:
    """Check instruments-service output exists for this date/category."""
    bucket = f"instruments-store-{category.lower()}-{project_id}"
    path = f"instrument_availability/by_date/day-{date}/instruments.parquet"
    return cloud_client.file_exists(f"gs://{bucket}/{path}")
```

### 2.3 market-data-processing-service

**Current State:** 17 unit tests, minimal E2E

**Actions:**

- [ ] Add E2E test processing 1 day of test data (1 category, 1 venue, 1 data_type)
- [ ] Add `scripts/data_catalog.py` - count candles per category/timeframe/date
- [ ] Add `src/dependency_checker.py` - check market-tick-data-handler outputs
- [ ] Document GCS paths

**GCS Path Standard:**

```
gs://market-data-tick-{category}-{project_id}/
  processed_candles/by_date/day-{YYYY-MM-DD}/timeframe-{TF}/data_type-{TYPE}/{asset_class}/{instrument}.parquet
```

---

## Phase 3: Feature Layer

### 3.1 features-calendar-service (Library - No CLI)

**Current State:** Library used by features-delta-one-service, 2 test files

**Actions:**

- [ ] Expand unit tests for all temporal/economic event calculations
- [ ] No E2E needed (library, not standalone)
- [ ] No data catalog needed (no GCS output)
- [ ] Document that this is a library dependency

### 3.2 features-delta-one-service (Best Feature Test Coverage)

**Current State:** 6+ unit tests, has E2E, 22 feature groups

**Actions:**

- [ ] Add `scripts/data_catalog.py` - count features per category/feature_group/instrument/date
- [ ] Add `src/dependency_checker.py` - check market-data-processing-service outputs
- [ ] Document GCS paths
- [ ] Ensure E2E covers at least 1 feature group per category

**GCS Path Standard:**

```
gs://features-delta-one-{category}-{project_id}/
  by_date/day-{YYYY-MM-DD}/feature_group-{GROUP}/timeframe-{TF}/{instrument}.parquet
```

### 3.3 features-volatility-service

**Current State:** Basic (2 unit tests), no E2E

**Actions:**

- [ ] Add unit tests for each feature group (options_iv, futures_basis, term_structure)
- [ ] Add E2E test for 1 representative combinatoric
- [ ] Add `scripts/data_catalog.py`
- [ ] Add `src/dependency_checker.py` - reads raw chain data from market-tick-data-handler

**GCS Path Standard:**

```
gs://features-volatility-{category}-{project_id}/
  by_date/day-{YYYY-MM-DD}/feature_group-{GROUP}/timeframe-{TF}/{underlying}.parquet
```

### 3.4 features-onchain-service

**Current State:** Basic (2 unit tests), no E2E

**Actions:**

- [ ] Add unit tests for each feature group (macro_sentiment, lending_rates, lst_yields, onchain_perps)
- [ ] Add E2E test for 1 representative combinatoric
- [ ] Add `scripts/data_catalog.py`
- [ ] Add `src/dependency_checker.py` - check market-data-processing-service (DeFi candles)

**GCS Path Standard:**

```
gs://features-onchain-{category}-{project_id}/
  by_date/day-{YYYY-MM-DD}/feature_group-{GROUP}/features.parquet
```

---

## Phase 4: ML Layer

### 4.1 ml-training-service (Comprehensive Tests)

**Current State:** 47 test files, integration tests

**Actions:**

- [ ] Add E2E test training a minimal model on 1 instrument/timeframe
- [ ] Add `scripts/data_catalog.py` - list models in registry per instrument/timeframe/target
- [ ] Add `src/dependency_checker.py` - check all feature service outputs
- [ ] Document GCS paths

**GCS Path Standard:**

```
gs://ml-models-store-{project_id}/
  models/{model_id}/{version}/model.joblib
  model_registry/metadata/{model_id}/{version}/metadata.json
```

### 4.2 ml-inference-service

**Current State:** Minimal (2 unit tests), no E2E

**Actions:**

- [ ] Add unit tests for batch/live modes
- [ ] Add E2E test generating predictions for 1 instrument/1 date
- [ ] Add `scripts/data_catalog.py` - count predictions per instrument/date
- [ ] Add `src/dependency_checker.py` - check ml-training-service models + feature outputs

**GCS Path Standard:**

```
gs://ml-predictions-store-{project_id}/
  predictions/{mode}/{YYYY/MM/DD}/{event_id}.json
```

---

## Phase 5: Backtesting Layer (Downstream)

### 5.1 strategy-service (Strong E2E)

**Current State:** 27 tests, multiple E2E files

**Actions:**

- [ ] Add `scripts/data_catalog.py` - count signals/backtest results per strategy/date
- [ ] Add `src/dependency_checker.py` - check ML predictions + features
- [ ] Document GCS paths

**GCS Path Standard:**

```
gs://strategy-store-{domain}-{project_id}/
  signals/{strategy_id}/day-{date}/instructions.parquet
  backtest_results/{strategy_id}/{run_id}/summary.json
```

### 5.2 execution-service

**Current State:** Minimal (2 unit tests), 1 DeFi E2E

**Actions:**

- [ ] Add unit tests for each domain (cefi, tradfi, defi)
- [ ] Add E2E tests for cefi and tradfi (defi exists)
- [ ] Add `scripts/data_catalog.py` - count execution results per domain/config/date
- [ ] Add `src/dependency_checker.py` - check strategy-service signals + market data

**GCS Path Standard:**

```
gs://execution-store-{domain}-{project_id}/
  backtest_results/{strategy_id}/{run_id}/
  grid_configs/{grid_id}/{config}.json
```

---

## Phase 6: Integration

### 6.1 Quality Gates Integration

Each repo's CI workflow (`.github/workflows/quality-gates.yml`) should:

1. Run unit tests (mock GCS)
2. Run E2E tests against test buckets
3. Check dependency declarations match actual imports

### 6.2 Data Catalog Aggregation

In unified-trading-deployment-v3, add:

```bash
# Run catalog across all services
python -m unified_trading_deployment.cli catalog-all \
  --start-date 2020-01-01 \
  --end-date 2026-01-26 \
  --output catalog_report.json
```

This calls each service's `scripts/data_catalog.py` and aggregates results.

---

## Repo Processing Order

Based on dependency flow (upstream to downstream):

1. **unified-trading-deployment-v3** - Foundation (sharding tests, catalog CLI, dependency graph)
2. **instruments-service** - Root service (add catalog script)
3. **market-tick-data-handler** - Depends on instruments (add E2E, catalog, dependency check)
4. **market-data-processing-service** - Depends on tick handler (add E2E, catalog)
5. **features-calendar-service** - Library (expand unit tests only)
6. **features-delta-one-service** - Depends on processing + calendar (add catalog, dependency check)
7. **features-volatility-service** - Depends on tick handler (add tests, E2E, catalog)
8. **features-onchain-service** - Depends on processing (add tests, E2E, catalog)
9. **ml-training-service** - Depends on all features (add E2E, catalog, dependency check)
10. **ml-inference-service** - Depends on training + features (add tests, E2E, catalog)
11. **strategy-service** - Depends on inference + features (add catalog, dependency check)
12. **execution-service** - Depends on strategy + market data (add tests, E2E, catalog)

---

## Standard File Structure Per Repo

Each service repo should have:

```
{service}/
  src/
    dependency_checker.py  # NEW - Runtime dependency validation
  scripts/
    data_catalog.py        # NEW - Count outputs per combinatoric
  docs/
    GCS_PATHS.md           # NEW - Document output paths
    DEPENDENCIES.md        # NEW - Upstream requirements
  tests/
    unit/
      test_*.py            # All CLI arg paths covered
    e2e/
      test_*_e2e.py        # 1 output per combinatoric (test buckets)
    conftest.py            # Fixtures with mock GCS + test bucket config
```

---

## Representative Samples for Dynamic Combinatorics

For GCS-dynamic configs (ML/strategy/execution):

- **Unit tests:** Mock 2-3 config files
- **E2E tests:** Use 1 fixed config from test bucket
- **Data catalog:** Enumerate all configs in production buckets

For date ranges:

- **Unit tests:** 1-2 dates
- **E2E tests:** 1 representative date per category
- **Data catalog:** Full range specified by user