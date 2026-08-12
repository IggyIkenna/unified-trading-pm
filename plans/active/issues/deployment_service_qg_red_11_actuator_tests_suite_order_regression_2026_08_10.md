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
status: open
nature: issue
asset_group: cross-cutting
stage: meta
repos: [deployment-service]
scope: [engineer, admin]
parent_epic: infrastructure_master
priority: P1
assigned_vm: NA
tags: [ci, qg, test-flake, test-isolation, fleet-blocking]
related:
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
  - /plans/active/issues/mtds_backfill_odds_smallchunk10_relaunch_budget_bug_and_oom_2026_08_09.md
source: >-
  slot-25 4b-iii (prediction shape #4 migration) deploy-service QG runs, 2026-08-10 19:55Z + 20:25Z (2× stable
  full-suite failures); standalone 59/59 pass; regression window post-6e6f509f.
locked_by:
resolved_by:
created: 2026-08-10
supersedes: null
superseded_by: null
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

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

- [ ] [BACKEND] P1. **ADDED 2026-08-12 (/plan-reconcile) — this doc held a P1 FLEET-BLOCKING claim with zero tracked
      todos, violating the "every follow-up is a `- [ ]` todo, never prose" HARD RULE.** Bisect
      `test_dp_recovery_actuators.py`'s full-suite state contamination against its predecessor test files (candidates:
      `*_relaunch*` / fleet-monitor / dp-alerts suites; regression window commits `b501a5e5`, `b34e85a2`, `4ca051ea`,
      `dd7b62e1`), find the shared-state leak (module-level mock/registry/env an earlier test file doesn't restore), add
      the missing cleanup. Before starting: re-run `quality-gates.sh` full to confirm this is still live — 2 days have
      passed since filing and it may have self-resolved via an unrelated fix. Done when: full-suite QG passes with all
      11 named tests green, or the regression is confirmed already fixed with a cited commit sha. Repo:
      deployment-service.

## Status

- 2026-08-10: filed by slot 25 (data_engineering, 4b-iii) — QG-blocked on shipping `e25dcfb3`. Not slot-25's fix to make
  (foreign test area, outside dispatch scope). Operator/recovery-area owner to pick up or explicitly delegate.
