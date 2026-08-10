---
doc_type: issue
title: "deployment-service QG red — test_main_meta_mode_dry_run timeout regression in meta_watchers index_reader change"
summary: >-
  deployment-service quality-gates-v2 on live-defi-rollout (SHA d85832ba) failed with qg_red_reason=pytest. The single
  failing test is test_main_meta_mode_dry_run in test_data_pipeline_monitors_cli.py, which times out (>300s) in
  check_high_attempted_failed → all_cells.extend(cells) at meta_watchers.py:624. The serial retry (for xdist-contention
  timeout flake class) also timed out at 1175s. Root cause: the 2026-08-10 change introducing the index_reader parameter
  to _read_attempted_failed_cells / check_high_attempted_failed (defi index ~6 GiB OOM-prevention) changed the test
  execution path — the --dry-run mock path no longer fast-paths correctly and takes ~20 min wall-clock.
status: active
nature: issue
asset_group: [cross-cutting]
stage: [ci-cd]
repos: [deployment-service]
scope: [engineer]
tags: [ci-reconcile, deployment-service, qg-failure, pytest-timeout, meta_watchers, data-pipeline-monitors]
related: [/codex/08-workflows/ci-cd-flow.md]
created: 2026-08-10
source: ci_reconciler sweep 2026-08-10T20:15Z
---

## Evidence

- **Failing QG run**: `https://github.com/IggyIkenna/deployment-service/actions/runs/31423759669` (databaseId 31423759669)
- **Last green**: run 31423748548 on SHA `391e214c` (18:17 UTC)
- **Failing SHA**: `d85832ba7d65c0c7ed9ac1a1222ff7c7a184084d`
- **Diff**: `deployment_service/data_pipeline_monitors/{_gcs,cli,exit_code_fleet_monitor,launcher_registry,meta_watchers}.py` modified, `deployment_service/vm_prefix_registry.py` modified, new script `scripts/vm/launch-funding-ensemble-daily-cron-host.sh`
- **Failure**: `FAILED tests/unit/test_data_pipeline_monitors_cli.py::test_main_meta_mode_dry_run - Failed: Timeout (>300.0s) from pytest-timeout.`
- **Trace**: `cli.main(["--mode", "meta", "--dry-run"]) → meta_watchers.check_high_attempted_failed() → all_cells.extend(cells)` at meta_watchers.py:624
- **Timing**: First run 3107 passed / 1 timeout in 1204s; serial retry 1 timeout in 1175s

## Root cause

The `index_reader` parameter addition to `_read_attempted_failed_cells()` and `check_high_attempted_failed()` (preventing a 6 GiB defi index OOM) changed the test's execution path. In `--dry-run` mode with `CLOUD_MOCK_MODE=true`, the test was previously fast; the new code path likely bypasses the mock/fast-path and does real (slow/blocked) work instead.

## Classification

**(b) Genuine code regression** — the meta_watchers refactor changed test behavior causing a 20+ minute wall-clock test run that times out.

## Fix direction

1. Ensure the `--dry-run` mode in `cli.py` properly wires the test mock for the new `index_reader` path
2. Or the test mock needs to provide a no-op `index_reader` that returns an empty DataFrame
3. Or the `check_high_attempted_failed` function should short-circuit in `--dry-run` mode before iterating

## Disposition

Filed by ci_reconciler hourly sweep. Not auto-fixed — the refactor's design intent (index_reader for OOM prevention) needs the original author's context. Deployment-service LDR→main is 1328 commits lagged.

- [ ] Fix test_main_meta_mode_dry_run timeout — restore fast mocked path with index_reader parameter
- [ ] Verify deployment-service QG goes green after fix
- [ ] Check whether the 1328-commit promotion lag is structural or just the normal LDR accumulation
