---
title: features-service volatility unit tests — 48 pre-existing failures surfaced by PYTEST_UNIT_DIR fix
created: 2026-05-15
author: slot-4 (harsh)
resolved: 2026-05-17
resolution: MOSTLY-SHIPPED — 48 → 13 failures (73% reduction) at features-service@070985c0 + 2425ecf8. Root causes fixed: VolatilityOrchestrationService import path (engine/orchestrator → engine/feature_group_service), BroadcastSink + LiveDataSource moved into UTL feature_service_base, smoke_matrix per-family layout. Remaining 13 are smaller per-test API drifts (test_cli_and_tradfi 2, test_mock_data_provider 1, test_feature_touchup 6 errors) — slot-4 picks up the long tail.
source:
  - bash scripts/quality-gates.sh → 202 failed (all families), 48 in volatility/
  - tests/volatility/unit/ — failures surfaced when PYTEST_UNIT_DIR="tests/" picked up all per-family tests
locked_by: live-defi-rollout
---

> **🟢 RESOLUTION VERIFIED 2026-05-20** — superseded by full-suite fix at `features-service@0e73bc90` ("fix all failing
> tests in features-service — 0 failures from 74") which explicitly covers volatility (`asyncio.get_event_loop()` →
> `asyncio.run()`) plus orchestration/live_seams API drift. 73% reduction at original `features-service@070985c0` +
> `2425ecf8` was the partial; the long tail closed at `0e73bc90`. Archiving.

## What I found

After the PYTEST_UNIT_DIR fix (PM@c7786b2f + features@ccd44d97) brought all 350 per-family unit tests into QG scope,
`bash scripts/quality-gates.sh` now reveals **48 pre-existing failures** in `tests/volatility/unit/` (across 7 test
files). These were previously invisible — QG only ran `tests/unit/` (46 tests, 5 files).

Additionally, 1 sports test was fixed in this cycle (`features@7ef55a7f`).

## Root causes (3 distinct)

### 1. Class renamed: `VolatilityOrchestrationService` → `VolatilityFeaturesOrchestrator`

`features_service/volatility/engine/orchestrator.py` no longer exports `VolatilityOrchestrationService`. Current class:
`VolatilityFeaturesOrchestrator` with a completely different constructor:

```python
# Old API (what tests expect):
VolatilityOrchestrationService(data_loader=loader, feature_writer=writer, asset_group="CEFI")

# New API (what exists):
VolatilityFeaturesOrchestrator(config: VolatilityServiceConfig | None = None)
```

Affected test files (import error at collection):

- `tests/volatility/unit/test_orchestration_service.py` (~28 tests)
- `tests/volatility/unit/test_volatility_advanced.py` (some tests)
- `tests/volatility/unit/test_data_leakage_prevention.py` (some tests)

### 2. Module deleted: `features_service.volatility.adapters.live_data_source`

`tests/volatility/unit/test_live_seams.py` imports:

```python
from features_service.volatility.adapters.live_data_source import LiveDataSource
```

This module no longer exists → `ModuleNotFoundError`.

### 3. xdist test interference (parallel execution)

Some tests pass in isolation (confirmed: `test_data_loader.py::test_custom_timeframe` passes alone) but fail when run in
parallel via `pytest-xdist`. Likely affects `test_data_loader.py`, `test_feature_writer.py`,
`test_mock_data_provider.py`, `test_smoke_matrix.py`.

## Why it matters

1. **Coverage blindspot**: 48 tests covering the volatility engine were never run by QG. Breakage in the volatility
   compute path was invisible to automated gates.
2. **API drift confirmed**: `VolatilityFeaturesOrchestrator` is used in production but the test suite is still written
   against the old API. Integration coverage is effectively zero for this class.
3. **May-23 critical path**: volatility features are used by `arbitrage_price_dispersion` archetype (DeFi gate). Broken
   volatility tests = no automated confidence in this path.

## Recommended decision

**Fix ownership**: volatility tests were not part of any slot-4 task. Requires understanding the full
`VolatilityFeaturesOrchestrator` API to rewrite test fixtures.

**Priority actions**:

1. **P0**: Assign to slot that owns volatility feature engine. Rewrite `test_orchestration_service.py` and
   `test_volatility_advanced.py` for the new `VolatilityFeaturesOrchestrator` API.
2. **P1**: Find where `LiveDataSource` moved or was replaced; fix `test_live_seams.py`.
3. **P2**: Add `@pytest.mark.no_xdist` markers or fix shared state for xdist-sensitive tests.

**Workaround**: slot-4 fixed the 1 sports test failure (`LookaheadBiasError` message update, `features@7ef55a7f`). The
volatility failures remain as pre-existing issues.

---

## Triage — 2026-05-18

**Status**: OPEN  
**Triaged by**: slot-8 triage sweep  
**Reason**: 35% failures (13/48) remain unresolved
