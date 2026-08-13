---
doc_type: issue
title:
  deployment-service QG red — 11 stable test_dp_recovery_actuators.py failures in full-suite (pass standalone);
  regression since 6e6f509f
summary: >-
  deployment-service quality-gates.sh fails the SAME 11 `test_dp_recovery_actuators.py` tests on two consecutive full
  runs while all 59 pass when the file runs standalone — a deterministic suite-ordering/state-contamination regression
  introduced by peer recovery-actuator commits after 6e6f509f (2026-08-09 full-QG green). FLEET-BLOCKING: no
  deployment-service commit can ship while this stands.
status: resolved
nature: issue
asset_group: cross-cutting
stage: meta
repos: [deployment-service]
scope: [engineer, admin]
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
tags: [ci, qg, test-flake, test-isolation, fleet-blocking]
related:
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
  - /plans/active/issues/mtds_backfill_odds_smallchunk10_relaunch_budget_bug_and_oom_2026_08_09.md
source: >-
  slot-25 4b-iii (prediction shape #4 migration) deploy-service QG runs, 2026-08-10 19:55Z + 20:25Z (2× stable
  full-suite failures); standalone 59/59 pass; regression window post-6e6f509f.
locked_by:
resolved_by: slot-15@2026-08-13 (deployment-service@0c38c00d)
created: 2026-08-10
supersedes: null
superseded_by: null
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-08-13 — RESOLVED** (status: resolved, 0 open todos, unlocked). Already fixed by
> `deployment-service@0c38c00d` (2026-08-11); confirmed live via full `quality-gates.sh` on HEAD `74c2ae26` (3332
> passed, 0 failed).

# deployment-service QG red — 11 stable actuator-test failures (full-suite only)

## Summary

`deployment-service` `quality-gates.sh` (full, `--no-fix`) fails the **SAME 11 tests** in
`tests/unit/test_dp_recovery_actuators.py` on **two consecutive runs** (2026-08-10 ~19:55 and ~20:25, slot 25):

```
test_preempted_relaunch_resumes_from_monotonic_checkpoint
test_preempted_relaunch_resume_start_date_launcher_checkpoint_overrides_stale_original
test_preempted_relaunch_non_force_no_checkpoint_replays_verbatim
test_preempted_relaunch_budget_separate_from_oom_budget
test_preempted_relaunch_repins_missing_tarball_and_logs_loudly
test_preempted_relaunch_intact_pin_is_untouched_and_silent
test_preempted_relaunch_pages_when_no_pin_resolves_never_floats
test_preempted_relaunch_without_pins_never_calls_the_resolver
test_preempted_relaunch_reads_pins_from_the_durable_registry
test_launch_env_pin_wins_over_the_registry
test_registry_read_failure_degrades_to_launch_env_never_raises
```

`11 failed, 3250 passed, 5 skipped`. The SAME set both times → **stable/deterministic, NOT flaky**.

## Evidence it's suite-ordering contamination, not a real defect

- **All 59 tests in the file PASS standalone** (`.venv/bin/python -m pytest tests/unit/test_dp_recovery_actuators.py` →
  `59 passed in 2.45s`).
- The file's tests are internally consistent; the contamination comes from state left by an EARLIER test file in the
  full suite (the file itself uses no leaked env vars per grep — a subtler shared-state leak).
- **Full QG was green at `6e6f509f` (2026-08-09)** for the same tests (see
  `mtds_backfill_odds_smallchunk10_relaunch_budget_bug_and_oom_2026_08_09.md` todo 1: "targeted
  `test_dp_recovery_actuators.py` tests (11/11, `vm_prefix`/`stalled_relaunch` selection) + full `quality-gates.sh`
  green, sentinel=6e6f509f").
- Regression window = commits AFTER `6e6f509f` touching the recovery/actuator area: `b501a5e5`, `b34e85a2`, `4ca051ea`,
  `dd7b62e1` (recovery-actuator / fleet-monitor / dp-alerts changes).
- The triggering commit under test (slot 25 `e25dcfb3`, a bash-only launcher category add) **cannot** affect Python
  actuator tests.

## Impact — FLEET-BLOCKING

deployment-service QG is red on the branch for EVERY commit (pre-existing, not slot-25's change). No deployment-service
push can ship via quickmerge until the contamination is fixed. This blocks slot-25's `e25dcfb3` launcher category
(`prediction-shape4-merge`) which is otherwise verified working (3 successful VM launches using it).

## Suggested fix (owner: recovery-actuator area, whoever's post-6e6f509f change introduced the leak)

Bisect `test_dp_recovery_actuators.py` against its suite predecessors to find the state leak (a shared module-level
mock/registry/env that an earlier test file doesn't restore), then add the missing cleanup. Likely candidates to run the
actuator file after: the `*_relaunch*` / fleet-monitor / dp-alerts test files.

## Todos

- [x] [BACKEND] P1. ✅ **RESOLVED 2026-08-13 (slot-15)** — already fixed by `deployment-service@0c38c00d` (landed
      2026-08-11, "fix(dp-monitors): race-free relaunch state, alert-accuracy quartet, windowed attempted_failed ratio,
      test hermeticity"), which added an `autouse` `tests/conftest.py` fixture
      (`_isolate_local_storage_provider_default_root`) monkeypatching `LocalStorageProvider`'s
      `_default_local_storage_root` seam to a per-test `tmp_path`, closing exactly the cross-test shared-tempdir leak
      this doc's evidence pointed at (see
      `/plans/archive/issues/local_storage_provider_shared_tempdir_test_state_leak_2026_07_20.md`). Verified live, not
      just read: re-ran `bash scripts/quality-gates.sh --no-fix` full (no skip flags) on `deployment-service` HEAD
      `74c2ae26` (current LDR tip) — `3332 passed, 5 skipped, 9 warnings in 253.59s`, zero failures, all 11 named
      `test_dp_recovery_actuators.py` tests green in the full suite, sentinel written
      (`.qg_last_passed_sha=74c2ae2605ad0d7380dec2143de054731638e862`), exit 0. Bisection was unnecessary — the fix
      predates this pickup by ~2 days. Repo: deployment-service.

## Status

- 2026-08-10: filed by slot 25 (data_engineering, 4b-iii) — QG-blocked on shipping `e25dcfb3`. Not slot-25's fix to make
  (foreign test area, outside dispatch scope). Operator/recovery-area owner to pick up or explicitly delegate.

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

**slot-15 2026-08-13**: RESOLVED — confirmed already fixed by `deployment-service@0c38c00d` (2026-08-11), which is prior
work by a different session, not something shipped in this task. Ran full `quality-gates.sh --no-fix` live on
`deployment-service` HEAD `74c2ae26`: `3332 passed, 5 skipped`, exit 0, all 11 named actuator tests green, sentinel
written. No bisection needed. Archiving this doc in the same commit (single-repo finalize — plan-of-record lives in this
same worktree, no cross-repo split).
