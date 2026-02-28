# Test Coverage and Quality Audit — Unified Trading System

**Date:** 2026-02-25  
**Scope:** All Python repos in unified-trading-system-repos workspace  
**Method:** Pytest execution with coverage, static analysis, dependency chain inspection

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **Repos audited** | 28 Python repos |
| **Repos with passing tests** | 6 |
| **Repos blocked by dependency errors** | 18+ |
| **Critical coverage (<40%)** | 4 repos |
| **Warning coverage (40–60%)** | 2 repos |
| **Good coverage (≥60%)** | 2 repos |

**Root cause of most failures:** `unified-trading-services` has circular import (`MarketDataDomainClient`), and several repos have `IndentationError` in conftest (line 40). Fixing these will unblock ~18 repos.

---

## 1. Coverage Metrics by Repo

### 1.1 Repos with Executable Tests

| Repo | Coverage | Status | Passed | Failed | Skipped |
|------|----------|--------|--------|--------|---------|
| api-contracts | **87.3%** | ✅ Good | 142 | 17 | 1 |
| execution-algo-library | **78.6%** | ✅ Good | 71 | 0 | 0 |
| alerting-system | **57.9%** | ⚠️ Warning | 2 | 2 | 0 |
| pnl-attribution-service | **40.7%** | ⚠️ At threshold | 7 | 0 | 1 |
| risk-and-exposure-service | **40.0%** | ⚠️ At threshold | 36 | 1 | 0 |
| unified-feature-calculator-library | **25.0%** | 🔴 Critical | 5 | 7 | 0 |

### 1.2 Critical (<40% Coverage)

- **unified-feature-calculator-library** — 25.0%, 7 failing tests

### 1.3 Warning (40–60% Coverage)

- **pnl-attribution-service** — 40.7%
- **risk-and-exposure-service** — 40.0%
- **alerting-system** — 57.9%

### 1.4 Repos Blocked (No Coverage Data)

| Repo | Error |
|------|-------|
| unified-trading-services | Circular import: `cannot import name 'MarketDataDomainClient'` |
| unified-config-interface | 9 collection errors (unified_trading_services dependency) |
| unified-events-interface | 5 collection errors |
| unified-domain-client | 9 collection errors |
| unified-market-interface | 18 collection errors |
| unified-trade-execution-interface | 18 collection errors; venv points to non-existent `unified-order-interface` |
| unified-ml-interface | Circular import: `cannot import REQUIRED_ML_CONFIG_FIELDS` |
| unified-defi-execution-interface | Circular import: `cannot import GasCostModel` |
| instruments-service | IndentationError in conftest.py line 40 |
| market-data-processing-service | IndentationError in conftest.py line 40 |
| position-balance-monitor-service | IndentationError in conftest.py line 40 |
| market-tick-data-handler | 8 collection errors |
| strategy-service | 27 collection errors |
| features-delta-one-service | 7 collection errors |
| features-volatility-service | 2 collection errors |
| features-onchain-service | 5 collection errors |
| features-calendar-service | 3 collection errors |
| ml-training-service | 52 collection errors |
| ml-inference-service | 3 collection errors |
| execution-service | ImportError: MarketDataDomainClient |
| unified-trading-deployment-v3 | `setup_events()` missing 2 required positional arguments |
| matching-engine-library | ImportError: cannot import AMMCalculator |

---

## 2. Failed and Skipped Tests

| Repo | Failed | Skipped | Notes |
|------|--------|---------|------|
| api-contracts | 17 | 1 | High failure count despite good coverage |
| alerting-system | 2 | 0 | Small test suite |
| risk-and-exposure-service | 1 | 0 | Single failure |
| unified-feature-calculator-library | 7 | 0 | Needs investigation |

---

## 3. Test Quality Issues

### 3.1 Tests Without Assertions

| Repo | File | Issue |
|------|------|-------|
| alerting-system | tests/unit/test_event_logging.py | `test_service_specific_events` — `pass` only, no assertion |
| api-contracts | tests/unit/test_api_contracts.py | `test_schema_validation_structure` — `assert True` placeholder |
| api-contracts | tests/unit/test_api_contracts.py | `test_venue_schema_availability` — weak `assert True` in loop |

### 3.2 Missing conftest.py

| Repo | Impact |
|------|--------|
| api-contracts | No shared fixtures; potential fixture duplication |
| execution-algo-library | No shared fixtures; each test file may define own mocks |

### 3.3 Duplicate Test Files

- No `test_*_extended.py` or `test_*_additional.py` files found — compliant with `.cursor/rules/no-duplicate-tests.mdc`

### 3.4 Happy-Path Only

- **api-contracts**: Several tests use `assert True` or minimal validation; error paths and edge cases not exercised
- **alerting-system**: `test_service_specific_events` is a stub

### 3.5 Hardcoded Values vs Fixtures

- api-contracts: `test_contract_validation_success` uses hardcoded `{"name": "test", "age": 25}` instead of fixtures
- Many tests use inline dicts/lists rather than conftest fixtures

---

## 4. Missing Tests

### 4.1 Critical Functions Without Tests (Top 10)

Based on codebase search, these high-value functions need dedicated tests:

| Repo | Function/Class | Risk |
|------|---------------|------|
| execution-algo-library | `SmartOrderRouter.get_optimal_route` | Core routing logic |
| execution-algo-library | `SmartOrderRouter._get_all_quotes` | Multi-venue quote aggregation |
| execution-algo-library | `SORAlgorithm.execute` | Order routing |
| execution-algo-library | `IcebergAlgorithm.get_child_orders` | Display quantity logic |
| execution-algo-library | `POVAlgorithm` (volume participation) | Participation rate logic |
| unified-trading-services | Storage/secret client factory | Used by all services |
| instruments-service | CCXT/CEFI processor pipeline | Instrument generation |
| strategy-service | Signal generation and validation | Trading logic |
| risk-and-exposure-service | Exposure calculation | Risk limits |
| market-tick-data-handler | Tick aggregation and normalization | Data quality |

### 4.2 Error Handling Paths Not Tested

- `pytest.raises` usage is sparse; many `try/except` branches lack tests
- Connection/timeout error paths in `SmartOrderRouter._get_venue_quote` not covered
- Config validation failure paths often untested

### 4.3 Integration Points Not Tested

- Adapter interfaces (unified-market-interface, unified-trade-execution-interface) — blocked by dependency chain
- Event logging integration — `setup_events`/`log_event` tested in isolation, not with real pipeline

---

## 5. Test Organization

### 5.1 Naming Conventions

- Most repos follow `test_*.py` and `def test_*` — compliant
- Event logging: `test_event_logging.py` present in service repos (instruments-service, market-tick-data-handler, strategy-service, risk-and-exposure-service, pnl-attribution-service)
- **unified-trading-services**: No `test_event_logging.py` (library; codex requires it for services only)

### 5.2 conftest.py Presence

| Has conftest | Repos |
|--------------|-------|
| ✅ Yes | instruments-service, unified-trading-services, risk-and-exposure-service, pnl-attribution-service, market-tick-data-handler, strategy-service |
| ❌ No | api-contracts, execution-algo-library |

### 5.3 Test Directory Structure

- **4-tier structure** (unit, integration, e2e, smoke) present in: instruments-service, market-tick-data-handler, strategy-service
- **2-tier** (unit only or unit + integration): api-contracts, execution-algo-library, risk-and-exposure-service, pnl-attribution-service

---

## 6. Test Performance

- Subagent did not capture per-test timing
- Codex: unit tests <60s each; integration <120s; e2e <180s
- **Recommendation:** Run `pytest --durations=10` per repo to identify slow tests (>5s)

---

## 7. Mock Quality

- **Overmocking:** Not systematically audited; manual review needed
- **Undermocking:** Several services import real `unified_trading_services` in conftest — causes cascade failures when UCS is broken
- **Mocks not matching reality:** api-contracts uses `assert True` placeholders; mocks may not reflect real API responses

---

## 8. Recommendations by Repo

### 8.1 P0 — Fix Blocking Issues

1. **unified-trading-services**
   - Fix circular import (`MarketDataDomainClient`)
   - Fix IndentationError in `__init__.py` (line 40–47) if present
   - Add `test_event_logging.py` if treated as a service

2. **instruments-service, market-data-processing-service, position-balance-monitor-service**
   - Fix IndentationError in conftest.py line 40 (likely from `unified_trading_services` import)

3. **unified-trading-deployment-v3**
   - Fix `setup_events()` call — add required `mode` and `service_name` arguments

4. **unified-trade-execution-interface**
   - Fix venv/dependency: remove or replace reference to non-existent `unified-order-interface`

### 8.2 P1 — Coverage and Failures

1. **unified-feature-calculator-library**
   - Investigate 7 failing tests; fix or skip with documented reason
   - Raise coverage from 25% toward 35% minimum

2. **api-contracts**
   - Fix 17 failing tests
   - Replace `assert True` placeholders with real assertions

3. **risk-and-exposure-service, pnl-attribution-service**
   - Raise coverage from ~40% to 50% (production target)

4. **alerting-system**
   - Fix 2 failing tests
   - Implement `test_service_specific_events` with real assertions

### 8.3 P2 — Test Quality

1. **api-contracts, execution-algo-library**
   - Add `conftest.py` with shared fixtures

2. **All repos**
   - Add `pytest.raises` tests for error paths
   - Replace hardcoded test data with fixtures where repeated

3. **execution-algo-library**
   - Add tests for `SmartOrderRouter.get_optimal_route`, `_get_all_quotes`, error handling in `_get_venue_quote`

---

## 9. Coverage Threshold Reference

| Source | Threshold |
|--------|-----------|
| Codex minimum | 35% |
| Production recommended | 50% |
| Audit goal | 80% |
| instruments-service quality-gates.sh | MIN_COVERAGE=35 |

---

## 10. Next Steps

1. Fix unified-trading-services circular import and IndentationError — unblocks 18+ repos
2. Run `pytest --durations=10` across all repos to identify slow tests
3. Add conftest.py to api-contracts and execution-algo-library
4. Replace placeholder assertions in api-contracts and alerting-system
5. Track rollout in `unified-trading-pm` per `.cursor/rules/rollout-tracking.mdc`
