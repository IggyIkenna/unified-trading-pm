---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-19)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-19 (merged across multiple driver invocations — see
  merge_pipeline_e2e_report.py): total=30 passed=3 failed=13 ambiguous=0 skipped=14"
status: fail
nature: record
asset_group: [cefi, cross-cutting, defi, prediction, sports, tradfi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-07-27
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-19, legs=force,skip"
date: 2026-07-27
auditor: data_pipeline_e2e_check_features (real-VM automated run, merged)
parent_epic: infrastructure_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-19
generated_at: "2026-07-27T13:10:51.024225+00:00"
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-19)

**Legs:** force, skip

**Note — merged across multiple driver invocations** via `merge_pipeline_e2e_report.py` (the driver overwrites its
report per-invocation, does not append across separate `--asset-group`/`--family`-scoped processes).

**Summary:** total=30 passed=3 failed=13 ambiguous=0 skipped=14

## Results

| Shard                       | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                                                                                                 |
| --------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:cross_instrument       | force | failed  | not_applicable | 137  | 0       | -        | vm_not_success:vm_exit_nonzero=137                                                                                                                                                                                                                                     |
| CEFI:cross_instrument       | skip  | failed  | not_applicable | 137  | 0       | -        | vm_not_success (exit=137)                                                                                                                                                                                                                                              |
| CEFI:multi_timeframe        | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                                                                                                                       |
| CEFI:multi_timeframe        | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                                                                                                                                                                                                                |
| CEFI:volatility             | force | skipped | not_applicable | None | 0       | -        | non_canonical_input (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                                       |
| CEFI:volatility             | skip  | skipped | not_applicable | None | 0       | -        | non_canonical_input (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                                       |
| DEFI:delta_one              | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| DEFI:delta_one              | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| DEFI:multi_timeframe        | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| DEFI:multi_timeframe        | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| DEFI:onchain                | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| DEFI:onchain                | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| GLOBAL:calendar             | force | passed  | not_applicable | 0    | 1       | ok       | ok (data: parquet + manifest captured)                                                                                                                                                                                                                                 |
| GLOBAL:calendar             | skip  | passed  | genuine        | 0    | 0       | -        | ok (object byte-unchanged -> genuine skip; skip log DEBUG-level (absent, expected))                                                                                                                                                                                    |
| PREDICTION:cross_instrument | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| PREDICTION:cross_instrument | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| PREDICTION:delta_one        | force | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| PREDICTION:delta_one        | skip  | skipped | not_applicable | None | 0       | -        | no_captured_input_for_window (window 2026-07-18..2026-07-19, lookback=1d)                                                                                                                                                                                              |
| SPORTS:sports               | force | passed  | not_applicable | 0    | 23      | ok       | ok (data: parquet + manifest captured)                                                                                                                                                                                                                                 |
| SPORTS:sports               | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                                                                                                                                                                                                                |
| TRADFI:commodity            | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                                                                                                                       |
| TRADFI:commodity            | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                                                                                                                                                                                                                |
| TRADFI:cross_instrument     | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                                                                                                                       |
| TRADFI:cross_instrument     | skip  | skipped | not_applicable | None | 0       | -        | duplicate_in_flight: features-e2e-tradfi-20260727-130744-ae15cd is already RUNNING this (family=cross_instrument, asset_group=TRADFI) cell — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| TRADFI:delta_one            | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                                                                                                                       |
| TRADFI:delta_one            | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                                                                                                                                                                                                                |
| TRADFI:multi_timeframe      | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                                                                                                                       |
| TRADFI:multi_timeframe      | skip  | skipped | not_applicable | None | 0       | -        | duplicate_in_flight: features-e2e-tradfi-20260727-125224-48b254 is already RUNNING this (family=multi_timeframe, asset_group=TRADFI) cell — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md)  |
| TRADFI:volatility           | force | failed  | not_applicable | None | 0       | -        | vm_not_success:timeout_no_exit_status                                                                                                                                                                                                                                  |
| TRADFI:volatility           | skip  | failed  | not_applicable | None | 0       | -        | vm_not_success (exit=None)                                                                                                                                                                                                                                             |

## Bucket paths (where each write/read actually landed)

| Shard                       | Leg   | Parquet bucket                                        | Manifest bucket                                       | Same bucket? |
| --------------------------- | ----- | ----------------------------------------------------- | ----------------------------------------------------- | ------------ |
| CEFI:cross_instrument       | force | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| CEFI:cross_instrument       | skip  | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| CEFI:multi_timeframe        | force | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| CEFI:multi_timeframe        | skip  | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| CEFI:volatility             | force | `-`                                                   | `-`                                                   | -            |
| CEFI:volatility             | skip  | `-`                                                   | `-`                                                   | -            |
| DEFI:delta_one              | force | `-`                                                   | `-`                                                   | -            |
| DEFI:delta_one              | skip  | `-`                                                   | `-`                                                   | -            |
| DEFI:multi_timeframe        | force | `-`                                                   | `-`                                                   | -            |
| DEFI:multi_timeframe        | skip  | `-`                                                   | `-`                                                   | -            |
| DEFI:onchain                | force | `-`                                                   | `-`                                                   | -            |
| DEFI:onchain                | skip  | `-`                                                   | `-`                                                   | -            |
| GLOBAL:calendar             | force | `features-calendar-test-central-element-323112`       | `features-calendar-test-central-element-323112`       | yes          |
| GLOBAL:calendar             | skip  | `features-calendar-test-central-element-323112`       | `features-calendar-test-central-element-323112`       | yes          |
| PREDICTION:cross_instrument | force | `-`                                                   | `-`                                                   | -            |
| PREDICTION:cross_instrument | skip  | `-`                                                   | `-`                                                   | -            |
| PREDICTION:delta_one        | force | `-`                                                   | `-`                                                   | -            |
| PREDICTION:delta_one        | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:sports               | force | `features-sports-test-central-element-323112`         | `features-sports-test-central-element-323112`         | yes          |
| SPORTS:sports               | skip  | `features-sports-test-central-element-323112`         | `features-sports-test-central-element-323112`         | yes          |
| TRADFI:commodity            | force | `commodity-signals-batch-test-central-element-323112` | `commodity-signals-batch-test-central-element-323112` | yes          |
| TRADFI:commodity            | skip  | `commodity-signals-batch-test-central-element-323112` | `commodity-signals-batch-test-central-element-323112` | yes          |
| TRADFI:cross_instrument     | force | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:cross_instrument     | skip  | `-`                                                   | `-`                                                   | -            |
| TRADFI:delta_one            | force | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:delta_one            | skip  | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:multi_timeframe      | force | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:multi_timeframe      | skip  | `-`                                                   | `-`                                                   | -            |
| TRADFI:volatility           | force | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:volatility           | skip  | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
