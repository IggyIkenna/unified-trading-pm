---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-03-15)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-03-15: total=18 passed=0 failed=8 ambiguous=0 skipped=10"
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
generated_at: 2026-08-03T15:36:18.697906+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-03-15)

**Legs:** force, skip **Started:** 2026-08-03T14:54:22.788581+00:00 **Finished:** 2026-08-03T15:36:18.440703+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-03-15: total=18 passed=0 failed=8 ambiguous=0
skipped=10

## Results

| Shard                        | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                      |
| ---------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:ASTER:trades            | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-03-15/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/                                                                        |
| CEFI:ASTER:trades            | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-03-15/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:book_snapshot_5   | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-03/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/                                                                        |
| CEFI:ASTER:book_snapshot_5   | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-03/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:derivative_ticker | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-03-15/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/                                                                        |
| CEFI:ASTER:derivative_ticker | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-03-15/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:liquidations      | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-02/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/                                                                        |
| CEFI:ASTER:liquidations      | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-02/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:options_chain     | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:options_chain     | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:futures_chain     | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:futures_chain     | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:ohlcv_1m          | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:ohlcv_1m          | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:perp_funding      | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:perp_funding      | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:volatility_index  | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |
| CEFI:ASTER:volatility_index  | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                   |

## Bucket paths (where each write/read actually landed)

| Shard                        | Leg   | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| ---------------------------- | ----- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:ASTER:trades            | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:trades            | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:book_snapshot_5   | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:book_snapshot_5   | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:derivative_ticker | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:derivative_ticker | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:liquidations      | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:liquidations      | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:options_chain     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:options_chain     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:futures_chain     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:futures_chain     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:ohlcv_1m          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:ohlcv_1m          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:perp_funding      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:perp_funding      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:volatility_index  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:volatility_index  | skip  | `-`                                                 | `-`                                                 | -            |

## Failed cells

| Shard                        | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                      |
| ---------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:ASTER:trades            | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-03-15/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/                                                                        |
| CEFI:ASTER:trades            | skip  | failed | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-03-15/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:book_snapshot_5   | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-03/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/                                                                        |
| CEFI:ASTER:book_snapshot_5   | skip  | failed | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-03/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:derivative_ticker | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-03-15/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/                                                                        |
| CEFI:ASTER:derivative_ticker | skip  | failed | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-03-15/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:liquidations      | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-02/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/                                                                        |
| CEFI:ASTER:liquidations      | skip  | failed | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-08-02/pipeline_mode=batch_aster/asset_group=cefi/venue=ASTER/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
