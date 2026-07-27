---
doc_type: issue
title:
  deployment-service QG RED — TestQgSnapshotLauncher's --dry-run-scheduler-body asserts on live gcloud singleton-lock
  state, flakes whenever the real daily qg-snapshot VM is running
summary: >-
  3 of TestQgSnapshotLauncher's tests (test_scheduler_body_has_startup_script_url,
  test_scheduler_body_required_metadata_keys, test_vm_backfill_cmd_uses_correct_workspace) invoke
  launch-qg-snapshot-vm.sh --dry-run-scheduler-body, which still runs the launcher's live singleton-lock preflight
  (gcloud compute instances list) before emitting the dry-run JSON. Verified pre-existing on a clean tree (unrelated to
  any local change) — the real daily qg-snapshot cron VM (qg-snapshot-20260727-232717, terraform schedule "0 6 * * *")
  was genuinely RUNNING at test time, so the launcher's own singleton-lock refusal fired and the "dry run" exited 1
  instead of emitting JSON.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [infra, quality-gates, flaky-test, vm-launcher, qg-snapshot]
related: []
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source:
  "slot-4, discovered while shipping features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md Root cause D"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# deployment-service QG RED — TestQgSnapshotLauncher flakes against live qg-snapshot VM state

## What I found

While shipping an unrelated fix (`launch-features-vm.sh` env-propagation, Root cause D of
`issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`), `bash scripts/quality-gates.sh` in
`deployment-service` failed with 3 test failures, all in
`tests/unit/test_vm_launcher_scripts.py::TestQgSnapshotLauncher`:

- `test_scheduler_body_has_startup_script_url`
- `test_scheduler_body_required_metadata_keys`
- `test_vm_backfill_cmd_uses_correct_workspace`

All three shell out to `bash scripts/vm/launch-qg-snapshot-vm.sh --dry-run-scheduler-body` and assert `returncode == 0`.
The actual failure:

```
ERROR: VM with prefix 'qg-snapshot-' already running in asia-northeast1-c: qg-snapshot-20260727-232717
Refusing duplicate launch (singleton lock).
```

**Verified pre-existing, not caused by my change**: stashed my diff, re-ran
`TestQgSnapshotLauncher::test_scheduler_body_has_startup_script_url` alone on a clean HEAD — byte-identical failure.
Confirmed via `gcloud compute instances describe qg-snapshot-20260727-232717` that this is a REAL, genuinely-RUNNING VM
(created 2026-07-27T10:57:40-07:00, i.e. the actual daily `qg_snapshot_scheduler.tf` cron, `schedule = "0 6 * * *"`),
not stale garbage — so this is not a "someone forgot to delete their test VM" situation, it's the launcher's own
singleton-lock preflight correctly refusing a genuine concurrent launch.

**Root cause**: `launch-qg-snapshot-vm.sh --dry-run-scheduler-body` is meant to be a pure, side-effect-free dry-run (its
whole purpose per the test class docstring is regression-testing the Cloud Scheduler body JSON), but the singleton-lock
check (`gcloud compute instances list` against a live `qg-snapshot-` prefix filter) runs unconditionally BEFORE the
dry-run short-circuits — so a `--dry-run-scheduler-body` invocation is not actually side-effect-free/state-independent;
it inherits the real launcher's live-fleet-state dependency. Any time the real daily cron VM happens to still be running
when this test suite executes (entirely plausible — the cron fires once a day and the VM can run for a while), these 3
unit tests go red for a reason that has nothing to do with the code under test.

## Why it matters

- This is a repo-QG-RED class that will recur every day around the cron's run window, blocking ANY unrelated commit in
  `deployment-service` from shipping during that window (quickmerge --agent requires a fully clean `quality-gates.sh`
  sentinel).
- It's a genuine test-design gap (a "dry run" that isn't state-independent), not a code defect in the launcher itself —
  the singleton-lock refusal is CORRECT launcher behavior in production; the test just shouldn't be asserting a
  live-cloud-state-dependent path as if it were pure.

## Recommended fix path

- [ ] [SCRIPT] P2. Make `launch-qg-snapshot-vm.sh --dry-run-scheduler-body` genuinely side-effect/state-independent —
      either (a) move the `--dry-run-scheduler-body` short-circuit BEFORE the singleton-lock preflight (the
      scheduler-body JSON doesn't need to know whether a VM is currently running to be constructed), or (b) have the 3
      `TestQgSnapshotLauncher` tests above stub/mock `gcloud` (they already do this pattern themselves in
      `test_preflight_check_exits_when_gsutil_fails` via a fake `gcloud()` bash function) instead of hitting the real
      project's live fleet state. Repo: deployment-service (`scripts/vm/launch-qg-snapshot-vm.sh` +
      `tests/unit/test_vm_launcher_scripts.py`). **Done when**: the 3 tests pass regardless of whether a real
      `qg-snapshot-` VM happens to be running in the project at test time (verify by running the suite while a real
      qg-snapshot VM is live, or by mocking `gcloud compute instances list` to return a running instance).

## Progress Log

- 2026-07-27 (slot-4): Filed after verifying byte-identical pre-existing failure on a clean tree while trying to ship an
  unrelated `launch-features-vm.sh` fix. Not fixed inline (out of scope for the task in progress) — will retry
  `quality-gates.sh` once the real `qg-snapshot-20260727-232717` VM completes its run (auto-shutdown on completion per
  `VM_SHUTDOWN_ON_COMPLETION=true`), which resolves this occurrence without needing the code fix above; the code fix
  above still needs to land so this doesn't recur on the NEXT daily cron window.
