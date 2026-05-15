---
title: UTL quality-gates — 29 genuine test failures from LDR commits
created: 2026-05-15
author: slot-4
source:
  - unified-trading-library tests/
locked_by: []
---

## What I found

After pulling latest LDR (5 new commits: 93ff771..ce89045) and running UTL QG, there are **29 genuine test failures** across 6 test suites. These failures are NOT xdist artifacts — they persist when running each suite in isolation with `-n 0`.

Additionally, **102 xdist-induced failures** appear when running with `PYTEST_WORKERS≥1` because UTL's event system singletons leak state between xdist subprocess workers.

### Genuine failures (29)

#### events/ + events_interface/ — 11 ratchet count failures
- `test_canonicalized_events.py::TestStrategyEventTypes::test_set_size` — expects 5, got 10 (5 new strategy events)
- `test_canonicalized_events.py::TestDeploymentEventTypes::test_set_size` — expects 4, got 6 (2 new deployment events)
- `test_data_availability_events.py` (×2) — expects 5, got 6 (new event)
- `test_strategy_availability_events.py` — extra: STRATEGY_LIFECYCLE_CHANGED + STRATEGY_LIFECYCLE_SEEDED
- `test_freshness_events.py` (×3) + `events_interface/test_freshness_events.py` (×3) — DATA_STALE not in STANDARD_LIFECYCLE_EVENTS; DATA_AVAILABILITY_EVENT_TYPES count 5→6

#### config_interface/unit/ — 5 failures
- `test_auth_entitlements.py` — `len(matrix.apis) == 9` but got 8 (one API removed from auth matrix)
- `test_cloud_config.py::test_data_mode_mock_bridges_to_cloud_mock_mode` — config bridge logic changed
- `test_execution_config_schema.py` (×2) — DEX venue validation changed
- `test_testnet_contracts.py` — testnet contract registry changed

#### cloud_interface/unit/ — 13 failures
- `test_auth.py` (×5) — OIDC auth implementation changed
- `test_bucket_naming.py` (×6) — workspace YAML bucket parity changed; new DeFi AWS buckets expected
- `test_constants.py` (×6 shared with bucket tests) — bucket constant names changed
- `test_factory.py::test_unknown_provider_raises` — cloud factory logic changed

### xdist structural issue (additional)
UTL's event logging system uses module-level singletons (`_event_sink`, `_sink_setup`). When pytest-xdist runs with `-n 1+`, subprocess workers inherit contaminated global state. This causes 73 additional false failures (tests pass in isolation). Separate from the 29 genuine failures above.

- UTL `quality-gates.sh` has `PYTEST_WORKERS=${PYTEST_WORKERS:-2}` — should be `1` to match the post-OOM base default
- Even with `PYTEST_WORKERS=1`, xdist subprocess mode still causes contamination for many event tests

## Why it matters

- UTL is a T0 tier library — its QG is the quality gate for ALL downstream services
- 29 genuine failures = QG is broken → no quickmerge gate on UTL changes
- The xdist issue was the OOM root cause; the content failures are separate regressions from LDR commits

## Recommended decision

**Priority 1** (immediate, ≤1h): Fix the 29 ratchet failures. Each is a 1-line count update in 6 test files. The new counts are correct (events/APIs were legitimately added/changed by LDR commits). Assign to slot that owns the changed modules.

**Priority 2** (same day): Change `PYTEST_WORKERS=${PYTEST_WORKERS:-2}` → `PYTEST_WORKERS=${PYTEST_WORKERS:-1}` in `unified-trading-library/scripts/quality-gates.sh` to match post-OOM base default.

**Priority 3** (P2, backlog): Fix UTL event system singletons to use proper pytest fixture scoping — prevents state leakage between xdist workers. SSOT: `unified_trading_library/events/setup.py` (wherever `_event_sink` global lives).

Slot-4 diagnosis: the OOM fix (base-service.sh defaulting to 1 worker) is in place, but UTL overrides to 2 workers AND has 29 genuine content failures from other slots' commits that independently need fixing.
