---
title:
  "features-service full QG red — cross-family test pollution (leaked cross_instrument global manifest writer w/
  MagicMock get_settings poisons calendar capture_status test)"
created: 2026-06-03
author: ikenna (slot-3)
source:
  - features-service tests/calendar/unit/test_calendar_orchestrator_capture_status.py
  - features-service tests/cross_instrument/ (global/singleton manifest writer + get_settings mock)
locked_by: live-defi-rollout
priority: P1
---

## What I found

Running the full features-service `bash scripts/quality-gates.sh --no-fix` (slot-3, 2026-06-03, local macOS): **1
failed, 15992 passed, 217 skipped in 1216s (20m16s)**. The single failure:
`tests/calendar/unit/test_calendar_orchestrator_capture_status.py::TestRecordEmptyOnZeroEventDay::test_empty_economic_events_day_records_empty`.

It is a **cross-family test-POLLUTION flake, not a real regression** — proven:

- The test PASSES in isolation (6.4s) and its whole file passes (5/5).
- The whole `tests/calendar/unit/` family PASSES **373/373** on CLEAN HEAD (with the slot-3 residual-#1 diff stashed).
- It fails ONLY when the FULL `tests/` suite runs together (serial, `PYTEST_UNIT_DIR=tests/`).
- Suite-end symptom:
  `atexit manifest flush failed for features-cross-instrument-cefi-test-project (4 rows lost): ("Could not convert <MagicMock name='get_settings().base_timeframe' ...> ... Conversion failed for column timeframe with type object")`.

**Diagnosis:** a global/singleton manifest writer created by the **cross_instrument** test family retains a **MagicMock
`get_settings`** that is never torn down → (a) its atexit flush fails, and (b) the leaked global poisons the calendar
`record_empty`/capture_status assertion when both families run in one process. Many families (`onchain`, `commodity`,
`multi_timeframe`, `cross_instrument`) patch `get_settings` / pass `MagicMock()` manifest writers; the leak is the
un-scoped global, not the per-test mocks.

## Why it matters

The features-service LOCAL full QG cannot go green → no `.qg_last_passed_sha` sentinel is written → **quickmerge is
blocked for ANY change shipped from a local slot** (repo-gate-health bug, not specific to one change). Composes with the
"Quality Gates Are A Merge Prerequisite" HARD RULE — a red gate from a foreign flake stalls every local ship.

**NOT the cause:** the slot-3 residual-#1 fix in flight (`dependency_checker.py` lookback candle `data_type` filter +
regression test) is verified correct — delta_one 20/20 incl. the new test, type-clean (3 basedpyright errors pre-exist
on HEAD outside the diff). It lives in an unrelated family with no module-level side effects.

## Recommended decision

Scope the cross_instrument global/singleton manifest writer behind a **function-scoped fixture with teardown** (or reset
the singleton + restore `get_settings` in `tests/cross_instrument/conftest.py`), so no MagicMock leaks past that family.
Then the full QG goes green and residual #1 ships via quickmerge. Owner: **features-service (vm-ml)**. Interim: local
features-service ships are blocked until green — route via a Linux QG VM (different process/order may not trip it) OR
fix the leak first. Repro: `bash scripts/quality-gates.sh --no-fix` (full) fails; `tests/calendar/unit/` alone passes.
