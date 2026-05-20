---
title: execution-service — 30 unit tests failing due to test harness missing methods
created: 2026-05-18
author: slot-2
source:
  - execution_service/algorithms/impl/hybrid_optimal_spawn.py:120
  - execution_service/algorithms/impl/passive_aggressive_core.py:129
  - execution_service/algorithms/impl/adaptive_twap_spawn.py (related)
locked_by: live-defi-rollout
---

> **🟡 SUBSUMED BY MEGA AUDIT** — findings absorbed by **Phase C7 (strategy → execution contract audit)** per [mega_audit_and_plan_beefup_progression_2026_05_20.md](mega_audit_and_plan_beefup_progression_2026_05_20.md) (slot-1 triage 2026-05-20). Do NOT work standalone; banner removed when C7 closes this scope.

## What I found

30 unit tests failing as of execution-service@ab2fbe80 (pre-slot-2 batch 98). Confirmed pre-existing — failures exist on
LDR state before any slot-2 lint changes. Two failure patterns:

1. `test_algo_impl_hybrid_optimal.py` — `AttributeError: '_HybridHarness' object has no attribute '_read_book_metrics'`
   at `hybrid_optimal_spawn.py:120`. Method `_read_book_metrics` was added to the implementation but not to the test
   harness class `_HybridHarness` in the test file.

2. `test_algo_impl_passive_aggressive.py` —
   `AttributeError: '_PAHCoreHarness' object has no attribute '_parse_candle_horizon_secs'` at
   `passive_aggressive_core.py:129`. Same pattern — new method added without updating test harness.

3. `test_algo_impl_adaptive_twap.py` — `TestATWAPParseParams::test_string_values_rejected` + others.

Affected tests: 30 total (7177 passing, 30 failing), seen in QG with `bash scripts/quality-gates.sh`.

## Why it matters

Tests are pre-existing failures that predate slot-2 lint work. The QG passes lint but fails tests. For quickmerge
`--agent` (Pass 2), tests are skipped, so this won't block deployment. However, it represents real functional test
coverage gaps that should be fixed before paper trading smoke tests.

## Recommended decision

- **Owner**: slot 5 (execution-service test surface per work-split conflict rules).
- **Fix**: update `_HybridHarness` test mock to include `_read_book_metrics` method; update `_PAHCoreHarness` to include
  `_parse_candle_horizon_secs` method; audit other harness classes for missing delegated methods.
- **Priority**: P2 — doesn't block May-23 cutover (paper VM is running) but should be fixed before Cycle 3 smoke tests.
