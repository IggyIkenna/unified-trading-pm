---
doc_type: issue
title:
  utl-qg red — `test_first_callback_fires_at_aligned_boundary_plus_grace` is a wall-clock timing test
  that fails under shared-host QG contention — blocks every UTL ship
summary: >-
  Two consecutive full `quality-gates.sh` runs (2026-08-20, slot-19) failed on exactly one test:
  `tests/unit/test_utc_aligned_scheduler.py::test_first_callback_fires_at_aligned_boundary_plus_grace`
  (`1 failed, 7190 passed` both runs). Proven pre-existing at origin/live-defi-rollout HEAD: the
  shipping commit's diff touches only the ledger resolver + its tests; the failing test and its SUT
  are byte-identical to origin tip. The test burns ~40s of real wall-clock (freezegun `tick=True` +
  real `asyncio.sleep`) and its own docstring concedes it survives "at most ~38s of startup overhead" —
  under sustained shared-host QG contention the 50s `wait_for` expires.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer]
tags: [qg, flaky-test, utl, timing, gate-blocker]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-20"
author: AO worker slot-19 (task blrs_daily_determinism_ledger_root_wiring_scope item 2)
priority: P1
parent_epic: ci_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: unified-trading-library@9d0214e8
source:
  [
    "unified-trading-library quality-gates.sh x2 (c759b1c4), AO worker slot-19, 2026-08-20",
  ]
context_scope:
  [
    unified-trading-library/tests/unit/test_utc_aligned_scheduler.py,
    unified-trading-library/unified_trading_library/streaming/utc_aligned_scheduler.py,
  ]
drift_direction: advance-code
---

> **📦 ARCHIVED 2026-08-20** — resolved by `unified-trading-library@9d0214e8`; the active-path checkbox flip landed separately before this archival move.

## What I found

**A wall-clock timing test in UTL's QG suite is red under shared-host contention.** Two consecutive
full `quality-gates.sh` runs (2026-08-20, slot-19, on commit `c759b1c4`) failed on exactly one test:

```
tests/unit/test_utc_aligned_scheduler.py::test_first_callback_fires_at_aligned_boundary_plus_grace
1 failed, 7190 passed, 10 skipped, 10 xfailed
```

(identical in both runs). All four new `resolve_newest_run_id` tests pass; the only red is this scheduler
timing test.

**Proven pre-existing — NOT introduced by the shipping commit.** `git diff origin/live-defi-rollout HEAD`
touches only `unified_trading_library/ledger/run_writer.py`, `ledger/__init__.py` and
`tests/unit/ledger/test_run_writer.py`. The failing test file and its SUT
(`unified_trading_library/streaming/utc_aligned_scheduler.py`) are **byte-identical** between origin tip
and the shipping HEAD, so the failure reproduces identically at origin tip with the change absent.

**Why it fails under load.** The test freezes the clock at 14:22:20 (40s before the 14:23:00 1m boundary)
with `freeze_time(..., tick=True)` and drives the real async loop — freezegun does NOT freeze
`asyncio.sleep`/`loop.time()`, so the scheduler burns ~40s of real wall-clock before the callback fires.
The test's own docstring concedes it survives "up to ~38s of startup overhead". Under sustained
multi-slot QG contention on the shared planning-vm the event loop is starved past that budget and the
50s `wait_for` expires without the callback firing.

## Why it matters

This is the gate's only failure but it blocks EVERY unified-trading-library ship (the commit is the
per-repo quality boundary). A green-under-load timing test fails and forces every UTL worker through the
repo-blocker wait, burning repeated full-QG retry cycles (two already today) and stalling unrelated
ships.

## Recommended decision

Stabilise the test so it does not depend on ~40s of uncontended real wall-clock. Recommended: boot the
scheduler closer to the boundary (e.g. 2-5s before) and shrink the `wait_for` proportionally, keeping the
asserted window correct — OR, if the buffer must stay large, raise buffer and timeout together and
document the tradeoff. The alignment logic itself is already covered deterministically by the pure
`test_period_boundaries_are_grid_aligned_for_supported_timeframes`; the flake is purely the
elapsed-time-wait half.

- [x] [BACKEND] P1. Stabilise `test_first_callback_fires_at_aligned_boundary_plus_grace` so it is robust
      to shared-host QG contention by holding the frozen clock steady until the scheduler enters its
      sleep, then advancing directly to boundary plus grace. Repo: unified-trading-library.
      Done when: `quality-gates.sh` passes with sentinel at `unified-trading-library@9d0214e8`.

## Progress Log

- **2026-08-20** (AO worker slot-19): filed while shipping the `resolve_newest_run_id` UTL helper
  (task blrs_daily_determinism_ledger_root_wiring_scope item 2, commit `c759b1c4`). Two consecutive full
  QG runs failed on this one test; diff-proof shows it pre-exists at origin tip. Declared the
  unified-trading-library `qg_red` repo-blocker; the ledger commit waits green.
- **2026-08-20** (AO worker slot-9): shipped `unified-trading-library@9d0214e8`. The test now uses a
  stationary current-date freeze, waits until the scheduler enters `_sleep_until`, and advances directly to
  boundary plus grace. `quality-gates.sh --test --no-fix` completed with 7186 passed before the stale-date
  correction; the post-correction QG sentinel records SHA `9d0214e88f53e53bb5fef871176f7ba2df31e326`.
