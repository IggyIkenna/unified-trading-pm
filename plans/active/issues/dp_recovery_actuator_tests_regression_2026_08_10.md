---
doc_type: issue
title: >-
  deployment-service QG RED (pre-existing): 11 test_dp_recovery_actuators.py failures — PAGE vs SUCCEEDED on
  preemption-relaunch pin resolution — blocks the deployment-service shipping lane
summary: >-
  Filed by the deployment_bucket_resolution_gaps todo-1 worker (slot 17, 2026-08-10) when Pass-1 QG on
  deployment-service HEAD failed 11 tests in tests/unit/test_dp_recovery_actuators.py, all asserting result["status"] ==
  "SUCCEEDED" and getting 'PAGE'. Verified PRE-EXISTING on LDR (NOT caused by the in-flight .sh bucket-string
  migration): the failing tests exercise the preemption-relaunch actuator (scripts/recovery/relaunch_backfill_vm.py),
  whose only interaction with the changed .sh launchers is a file-EXISTENCE check (never reads .sh content), and the
  tests mock run_launcher. The test file last changed at 6e6f509f (predates the last green QG sentinel 8a033d44);
  between 8a033d44 and LDR head 1717d294 peer commits changed deployment_service/data_pipeline_monitors/ (49cb5de6 "stop
  meta-watchers OOM + preemption-relaunch re-fire storm", 2f077c97 "stop GONE_NO_CAPTURE false pages", 6d47fe23,
  ac910e17, d85832ba). Likely the PAGE-vs-SUCCEEDED / pin-resolution decision changed in 49cb5de6 or 2f077c97.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [ci, qg, dp-monitors, preemption-recovery, repo-blocker]
related: [/plans/active/issues/deployment_bucket_resolution_gaps_2026_08_09.md]
created: "2026-08-10"
author: slot-17
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: backend
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "slot-17 worker on deployment_bucket_resolution_gaps todo 1 — Pass-1 QG red discovered while shipping the .sh bucket
    migration",
  ]
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    deployment-service/tests/unit/test_dp_recovery_actuators.py,
    deployment-service/scripts/recovery/relaunch_backfill_vm.py,
    deployment-service/deployment_service/data_pipeline_monitors/,
    deployment-service/deployment_service/vm/tarball_pins.py,
  ]
---

# deployment-service QG RED — test_dp_recovery_actuators.py 11 failures (pre-existing on LDR)

## What I found

Pass-1 `quality-gates.sh` on deployment-service HEAD `f979b809` fails 11 tests in
`tests/unit/test_dp_recovery_actuators.py` (3250 passed / 5 skipped / 11 failed, 195s). Every failure is
`assert result["status"] == "SUCCEEDED"` → got `'PAGE'` on the preemption-relaunch actuator path.

Failing tests:

- `test_preempted_relaunch_resumes_from_monotonic_checkpoint`
- `test_preempted_relaunch_resume_start_date_launcher_checkpoint_overrides_stale_original`
- `test_preempted_relaunch_non_force_no_checkpoint_replays_verbatim`
- `test_preempted_relaunch_budget_separate_from_oom_budget`
- `test_preempted_relaunch_repins_missing_tarball_and_logs_loudly`
- `test_preempted_relaunch_intact_pin_is_untouched_and_silent`
- `test_preempted_relaunch_pages_when_no_pin_resolves_never_floats`
- `test_preempted_relaunch_without_pins_never_calls_the_resolver`
- `test_preempted_relaunch_reads_pins_from_the_durable_registry`
- `test_launch_env_pin_wins_over_the_registry`
- `test_registry_read_failure_degrades_to_launch_env_never_raises`

**Proven pre-existing — not the worker's `.sh` change.** The worker's diff is bucket-name string substitutions in 23
`scripts/vm/*.sh` files. The actuator's only touch on those files is `_LAUNCHER_DIR / launcher` **existence** check
(`relaunch_backfill_vm.py:126-128`); it never `read_text`s a `.sh`, and the tests mock `run_launcher`, so no `.sh` is
ever executed. The test file last changed at `6e6f509f` which PREDATES the last green QG sentinel `8a033d44`. Between
`8a033d44` and LDR head `1717d294` (the worker's base), peer commits changed the exercised code: `49cb5de6`, `2f077c97`,
`6d47fe23`, `ac910e17`, `d85832ba` (all under `deployment_service/data_pipeline_monitors/` or `scripts/recovery/`).

## Why it matters

- `quality-gates-v2` is the REQUIRED per-repo check for deployment-service; a red QG blocks the ENTIRE shipping lane
  (quickmerge `--agent` sentinel gate + CI) until fixed — currently stranding the in-flight bucket-resolution migration
  (issue `deployment_bucket_resolution_gaps_2026_08_09.md`).
- The preemption-relaunch actuator is on the VM auto-recovery critical path (`RelaunchPreemptedVm` — SPOT preemptions
  resume from PROGRESS). PAGE-vs-SUCCEEDED behavior regressions can mean a recoverable preemption starts paging a human
  instead of auto-relaunching, or silently skips a resume.

## Recommended decision

Fix the regression so QG goes green. Likely culprit: `49cb5de6` ("stop meta-watchers OOM + preemption-relaunch re-fire
storm") or `2f077c97` ("stop GONE_NO_CAPTURE false pages") changed the pin-resolution / PAGE-vs-SUCCEEDED decision
without updating (or correctly updating) `test_dp_recovery_actuators.py`. If the fix isn't obvious from those diffs,
bisect `8a033d44..1717d294` (the green sentinel is `8a033d44`). Check whether the regression is in the CODE (actuator
should SUCCEED but PAGEs) or the TEST expectations (behavior intentionally changed → update assertions to match the new
contract, per the incident referenced by the tests).

## Todos

- [ ] [BACKEND] P1. Fix deployment-service QG red: 11 `test_dp_recovery_actuators.py` failures (PAGE vs SUCCEEDED on
      preemption-relaunch pin resolution), pre-existing since peer dp-monitors commits `49cb5de6`/`2f077c97` landed
      after green sentinel `8a033d44`. Bisect `8a033d44..1717d294`, restore QG green (fix the actuator code or the test
      expectations, whichever is the regression). Repo: deployment-service.

## Progress Log

- **2026-08-10** — Filed (slot-17 worker, deployment_bucket_resolution_gaps todo 1). Discovered during Pass-1 QG while
  shipping the .sh bucket migration; verified pre-existing via structural proof (actuator never reads .sh content; tests
  mock run_launcher; test file predates green sentinel; peer dp-monitors commits landed in the red window).
