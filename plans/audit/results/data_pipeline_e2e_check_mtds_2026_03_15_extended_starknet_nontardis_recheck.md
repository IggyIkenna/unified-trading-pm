---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-03-15)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-03-15: total=18 passed=0 failed=6 ambiguous=0 skipped=12"
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
generated_at: 2026-08-03T15:24:56.019612+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-03-15)

**Legs:** force, skip **Started:** 2026-08-03T14:54:28.834227+00:00 **Finished:** 2026-08-03T15:24:55.828910+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-03-15: total=18 passed=0 failed=6 ambiguous=0
skipped=12

## Results

| Shard                                    | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                                     |
| ---------------------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:EXTENDED-STARKNET:trades            | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/                                                                        |
| CEFI:EXTENDED-STARKNET:trades            | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:book_snapshot_5   | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:book_snapshot_5   | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:derivative_ticker | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/                                                                        |
| CEFI:EXTENDED-STARKNET:derivative_ticker | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:liquidations      | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:liquidations      | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:options_chain     | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:options_chain     | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:futures_chain     | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:futures_chain     | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/                                                                        |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:perp_funding      | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:perp_funding      | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:volatility_index  | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |
| CEFI:EXTENDED-STARKNET:volatility_index  | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                  |

## Bucket paths (where each write/read actually landed)

| Shard                                    | Leg   | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| ---------------------------------------- | ----- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:EXTENDED-STARKNET:trades            | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:trades            | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:book_snapshot_5   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:book_snapshot_5   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:derivative_ticker | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:derivative_ticker | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:liquidations      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:liquidations      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:options_chain     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:options_chain     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:futures_chain     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:futures_chain     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:perp_funding      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:perp_funding      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:volatility_index  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:volatility_index  | skip  | `-`                                                 | `-`                                                 | -            |

## Failed cells

| Shard                                    | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                                     |
| ---------------------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:EXTENDED-STARKNET:trades            | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/                                                                        |
| CEFI:EXTENDED-STARKNET:trades            | skip  | failed | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:derivative_ticker | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/                                                                        |
| CEFI:EXTENDED-STARKNET:derivative_ticker | skip  | failed | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/                                                                        |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | skip  | failed | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-28/pipeline_mode=batch_extended/asset_group=cefi/venue=EXTENDED-STARKNET/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
