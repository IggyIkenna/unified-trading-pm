---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05: total=32 passed=3 failed=17 ambiguous=0 skipped=12"
status: partial
nature: record
asset_group: [cefi, defi, prediction, sports, tradfi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-07-27
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-07-27
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-05
generated_at: 2026-07-27T15:15:07.990230+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)

**Legs:** force, skip **Started:** 2026-07-27T11:21:49.583441+00:00 **Finished:** 2026-07-27T15:15:07.044807+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05: total=32 passed=3 failed=17 ambiguous=0
skipped=12

## Results

| Shard                       | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Reason                                                                              |
| --------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------------------------------------------------------------------------------- |
| CEFI:delta_one              | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:timeout_no_exit_status                                               |
| CEFI:delta_one              | skip  | failed  | not_applicable | -    | 0       | -        | vm_not_success (exit=None)                                                          |
| DEFI:delta_one              | force | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| DEFI:delta_one              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| TRADFI:delta_one            | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                    |
| TRADFI:delta_one            | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                             |
| PREDICTION:delta_one        | force | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| PREDICTION:delta_one        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| CEFI:volatility             | force | skipped | not_applicable | -    | 0       | -        | non_canonical_input (window 2026-07-04..2026-07-05, lookback=1d)                    |
| CEFI:volatility             | skip  | skipped | not_applicable | -    | 0       | -        | non_canonical_input (window 2026-07-04..2026-07-05, lookback=1d)                    |
| TRADFI:volatility           | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:timeout_no_exit_status                                               |
| TRADFI:volatility           | skip  | failed  | not_applicable | -    | 0       | -        | vm_not_success (exit=None)                                                          |
| DEFI:onchain                | force | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| DEFI:onchain                | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| CEFI:cross_instrument       | force | failed  | not_applicable | 137  | 0       | -        | vm_not_success:vm_exit_nonzero=137                                                  |
| CEFI:cross_instrument       | skip  | failed  | not_applicable | 137  | 0       | -        | vm_not_success (exit=137)                                                           |
| TRADFI:cross_instrument     | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                    |
| TRADFI:cross_instrument     | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                             |
| PREDICTION:cross_instrument | force | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| PREDICTION:cross_instrument | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| CEFI:multi_timeframe        | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                    |
| CEFI:multi_timeframe        | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                             |
| DEFI:multi_timeframe        | force | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| DEFI:multi_timeframe        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d)           |
| TRADFI:multi_timeframe      | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                    |
| TRADFI:multi_timeframe      | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                             |
| SPORTS:sports               | force | passed  | not_applicable | 0    | 25      | captured | ok (data: parquet + manifest captured)                                              |
| SPORTS:sports               | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                             |
| GLOBAL:calendar             | force | passed  | not_applicable | 0    | 1       | captured | ok (data: parquet + manifest captured)                                              |
| GLOBAL:calendar             | skip  | passed  | genuine        | 0    | 0       | -        | ok (object byte-unchanged -> genuine skip; skip log DEBUG-level (absent, expected)) |
| TRADFI:commodity            | force | failed  | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                    |
| TRADFI:commodity            | skip  | failed  | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)                                                             |

## Bucket paths (where each write/read actually landed)

| Shard                       | Leg   | Parquet bucket                                        | Manifest bucket                                       | Same bucket? |
| --------------------------- | ----- | ----------------------------------------------------- | ----------------------------------------------------- | ------------ |
| CEFI:delta_one              | force | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| CEFI:delta_one              | skip  | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| DEFI:delta_one              | force | `-`                                                   | `-`                                                   | -            |
| DEFI:delta_one              | skip  | `-`                                                   | `-`                                                   | -            |
| TRADFI:delta_one            | force | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:delta_one            | skip  | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| PREDICTION:delta_one        | force | `-`                                                   | `-`                                                   | -            |
| PREDICTION:delta_one        | skip  | `-`                                                   | `-`                                                   | -            |
| CEFI:volatility             | force | `-`                                                   | `-`                                                   | -            |
| CEFI:volatility             | skip  | `-`                                                   | `-`                                                   | -            |
| TRADFI:volatility           | force | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:volatility           | skip  | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| DEFI:onchain                | force | `-`                                                   | `-`                                                   | -            |
| DEFI:onchain                | skip  | `-`                                                   | `-`                                                   | -            |
| CEFI:cross_instrument       | force | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| CEFI:cross_instrument       | skip  | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| TRADFI:cross_instrument     | force | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:cross_instrument     | skip  | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| PREDICTION:cross_instrument | force | `-`                                                   | `-`                                                   | -            |
| PREDICTION:cross_instrument | skip  | `-`                                                   | `-`                                                   | -            |
| CEFI:multi_timeframe        | force | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| CEFI:multi_timeframe        | skip  | `features-cefi-test-central-element-323112`           | `features-cefi-test-central-element-323112`           | yes          |
| DEFI:multi_timeframe        | force | `-`                                                   | `-`                                                   | -            |
| DEFI:multi_timeframe        | skip  | `-`                                                   | `-`                                                   | -            |
| TRADFI:multi_timeframe      | force | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| TRADFI:multi_timeframe      | skip  | `features-tradfi-test-central-element-323112`         | `features-tradfi-test-central-element-323112`         | yes          |
| SPORTS:sports               | force | `features-sports-test-central-element-323112`         | `features-sports-test-central-element-323112`         | yes          |
| SPORTS:sports               | skip  | `features-sports-test-central-element-323112`         | `features-sports-test-central-element-323112`         | yes          |
| GLOBAL:calendar             | force | `features-calendar-test-central-element-323112`       | `features-calendar-test-central-element-323112`       | yes          |
| GLOBAL:calendar             | skip  | `features-calendar-test-central-element-323112`       | `features-calendar-test-central-element-323112`       | yes          |
| TRADFI:commodity            | force | `commodity-signals-batch-test-central-element-323112` | `commodity-signals-batch-test-central-element-323112` | yes          |
| TRADFI:commodity            | skip  | `commodity-signals-batch-test-central-element-323112` | `commodity-signals-batch-test-central-element-323112` | yes          |

## Failed cells

| Shard                   | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                |
| ----------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ------------------------------------- |
| CEFI:delta_one          | force | failed | not_applicable | -    | 0       | -        | vm_not_success:timeout_no_exit_status |
| CEFI:delta_one          | skip  | failed | not_applicable | -    | 0       | -        | vm_not_success (exit=None)            |
| TRADFI:delta_one        | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1      |
| TRADFI:delta_one        | skip  | failed | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)               |
| TRADFI:volatility       | force | failed | not_applicable | -    | 0       | -        | vm_not_success:timeout_no_exit_status |
| TRADFI:volatility       | skip  | failed | not_applicable | -    | 0       | -        | vm_not_success (exit=None)            |
| CEFI:cross_instrument   | force | failed | not_applicable | 137  | 0       | -        | vm_not_success:vm_exit_nonzero=137    |
| CEFI:cross_instrument   | skip  | failed | not_applicable | 137  | 0       | -        | vm_not_success (exit=137)             |
| TRADFI:cross_instrument | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1      |
| TRADFI:cross_instrument | skip  | failed | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)               |
| CEFI:multi_timeframe    | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1      |
| CEFI:multi_timeframe    | skip  | failed | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)               |
| TRADFI:multi_timeframe  | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1      |
| TRADFI:multi_timeframe  | skip  | failed | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)               |
| SPORTS:sports           | skip  | failed | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)               |
| TRADFI:commodity        | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1      |
| TRADFI:commodity        | skip  | failed | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)               |
