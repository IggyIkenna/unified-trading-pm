---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-03-15)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-03-15: total=18 passed=0 failed=2 ambiguous=0 skipped=16"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-08-03
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-03-15, legs=force,skip"
date: 2026-08-03
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-03-15
generated_at: 2026-08-03T15:01:30.728373+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-03-15)

**Legs:** force, skip **Started:** 2026-08-03T14:54:34.810144+00:00 **Finished:** 2026-08-03T15:01:30.728090+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-03-15: total=18 passed=0 failed=2 ambiguous=0
skipped=16

## Results

| Shard                               | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                              |
| ----------------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:COINBASE-CDE:trades            | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_tardis/asset_group=cefi/venue=COINBASE-CDE/                                                                        |
| CEFI:COINBASE-CDE:trades            | skip  | failed  | ambiguous      | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_tardis/asset_group=cefi/venue=COINBASE-CDE/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-CDE:book_snapshot_5   | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:book_snapshot_5   | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:derivative_ticker | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:derivative_ticker | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:liquidations      | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:liquidations      | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:options_chain     | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:options_chain     | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:futures_chain     | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:futures_chain     | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:ohlcv_1m          | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:ohlcv_1m          | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:perp_funding      | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:perp_funding      | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:volatility_index  | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |
| CEFI:COINBASE-CDE:volatility_index  | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                           |

## Bucket paths (where each write/read actually landed)

| Shard                               | Leg   | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| ----------------------------------- | ----- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:COINBASE-CDE:trades            | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-CDE:trades            | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-CDE:book_snapshot_5   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:book_snapshot_5   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:derivative_ticker | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:derivative_ticker | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:liquidations      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:liquidations      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:options_chain     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:options_chain     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:futures_chain     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:futures_chain     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:ohlcv_1m          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:ohlcv_1m          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:perp_funding      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:perp_funding      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:volatility_index  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:volatility_index  | skip  | `-`                                                 | `-`                                                 | -            |

## Failed cells

| Shard                    | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                              |
| ------------------------ | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:COINBASE-CDE:trades | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_tardis/asset_group=cefi/venue=COINBASE-CDE/                                                                        |
| CEFI:COINBASE-CDE:trades | skip  | failed | ambiguous      | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_tardis/asset_group=cefi/venue=COINBASE-CDE/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
