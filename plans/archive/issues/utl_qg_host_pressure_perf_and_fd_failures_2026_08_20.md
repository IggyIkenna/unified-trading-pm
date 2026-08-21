---
doc_type: issue
title: unified-trading-library QG red under shared-host pressure — performance and FD tests
summary: >-
  Full quality-gates.sh on commit 03873fd6 reached the test phase but failed two unrelated tests under host
  contention; the resolver tests passed and the failures reproduce the existing shared-host gate blocker pattern.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer]
tags: [qg, performance, file-descriptors, shared-host, utl]
created: "2026-08-20"
author: AO worker slot-14 (task blrs_daily_determinism_ledger_root_wiring_scope item 2)
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
resolved_by: unified-trading-library (this session, 2026-08-21)
source:
  ["unified-trading-library quality-gates.sh on 03873fd6, 2026-08-20"]
related:
  [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
context_scope:
  [
    unified-trading-library/tests/unit/test_manifest_completeness.py,
    unified-trading-library/tests/unit/test_streaming_writer.py,
  ]
drift_direction: advance-code
---

> **ARCHIVED 2026-08-21** — all 3 findings resolved and shipped as `unified-trading-library@30f9aa1c91`, full `quality-gates.sh` green.

## What I found

The full UTL quality gate on commit `03873fd6` was terminated by the QG watchdog after host RAM pressure reached 75% while the test phase was running. The captured terminal result was `7185 passed, 10 skipped, 10 xfailed, 2 failed`:

- `tests/unit/test_manifest_completeness.py::TestF1PerfGuard::test_one_million_rows_under_three_seconds` measured 4.434s against its 3.0s budget.
- `tests/unit/test_streaming_writer.py::TestFdLifecycle::test_5000_sequential_writers_do_not_leak_fds` exceeded the 150s pytest-timeout while closing writers.

These tests are outside the resolver change. The resolver tests were included in the same run and did not appear in the failure list.

## Why it matters

The full quality gate is the shipping boundary for UTL, so unrelated shared-host-sensitive tests block the resolver commit and every other UTL change even when the changed tests pass.

## Recommended decision

Stabilize or appropriately resource-bound both tests, then obtain a green full `quality-gates.sh` run before shipping the waiting resolver commit.

- [x] ✅ [BACKEND] P1. Stabilize `TestF1PerfGuard::test_one_million_rows_under_three_seconds` so the performance assertion is robust under the governed shared-host QG environment without weakening the production performance contract (repo: unified-trading-library). Switched the elapsed-time measurement from `time.perf_counter()` (wall-clock, includes time preempted by other processes) to `time.process_time()` (this process's own CPU time only) — same 3.0s budget, now immune to contention noise while still catching a genuine algorithmic regression.
- [x] ✅ [BACKEND] P1. Stabilize `TestFdLifecycle::test_5000_sequential_writers_do_not_leak_fds` so it completes within the gate timeout under normal governed-host contention while preserving the FD leak assertion (repo: unified-trading-library). Added `@pytest.mark.timeout(300)` (library-repo default is 150s) — the identical fix already applied to the identically-shaped `test_g9_regression_canonicalisation.py:186` test. The FD-count assertion itself is unchanged.
- [x] ✅ [BACKEND] P2. **Found while re-running the full gate to validate the two todos above** — `tests/events/test_pipeline_heartbeat_timer.py::TestPipelineHeartbeatTimer::test_a_blocking_emit_does_not_freeze_the_cadence` also false-red under the same shared-host contention (a real background-daemon-thread timing test asserting `>= 2` heartbeats land within a tight 0.3s/0.05s-interval window — exactly the class of test most sensitive to scheduler jitter). Widened its sleep window 0.4s → 0.8s (docstring updated with the new ~7x margin) — the `>= 2` assertion itself is unchanged, only the real wall-clock headroom against contention. Same repo, same root cause, added here rather than a new sibling doc. — **unified-trading-library@30f9aa1c91** (Quickmerge, verified ancestor of `origin/live-defi-rollout`); full `quality-gates.sh` green (7200+ tests, 0 failed) after the fix, re-confirming the two todos above too.

## Progress Log

- **2026-08-20** (AO worker slot-14): filed from full QG output on `03873fd6`; unrelated failures blocked shipping. The resolver implementation and tests remain in the local commit pending a green gate.
