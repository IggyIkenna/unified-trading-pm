---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-01)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-01: total=12 passed=0 failed=12 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-08-15
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-07-01, legs=force,skip"
date: 2026-08-15
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-07-01
generated_at: 2026-08-15T00:32:34.489460+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-01)

**Legs:** force, skip **Started:** 2026-08-14T23:45:46.971454+00:00 **Finished:** 2026-08-15T00:32:34.488467+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-01: total=12 passed=0 failed=12 ambiguous=0
skipped=0

## Results

| Shard                  | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Content     | Reason                                                                                                                                                                                                                                                                                 |
| ---------------------- | ----- | ------ | -------------- | ---- | ------- | --------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TRADFI:NASDAQ:ohlcv_1m | force | failed | not_applicable | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NASDAQ/                                                                                                          |
| TRADFI:NASDAQ:ohlcv_1m | skip  | failed | genuine        | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NASDAQ/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                   |
| TRADFI:NYSE:ohlcv_1m   | force | failed | not_applicable | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NYSE/                                                                                                            |
| TRADFI:NYSE:ohlcv_1m   | skip  | failed | genuine        | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NYSE/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                     |
| TRADFI:CME:ohlcv_1m    | force | failed | not_applicable | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/data_type=ohlcv_1m/underlying=CL-MCL/                                                                        |
| TRADFI:CME:ohlcv_1m    | skip  | failed | genuine        | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/data_type=ohlcv_1m/underlying=CL-MCL/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| TRADFI:ICE:ohlcv_24h   | force | failed | not_applicable | 0    | 1       | no_matching_row | not_checked | manifest_status_invalid:no_matching_row                                                                                                                                                                                                                                                |
| TRADFI:ICE:ohlcv_24h   | skip  | failed | genuine        | 0    | 1       | no_matching_row | not_checked | manifest_status_invalid:no_matching_row; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                                                                                                                                                         |
| TRADFI:CBOE:ohlcv_24h  | force | failed | not_applicable | 0    | 5       | no_matching_row | not_checked | manifest_status_invalid:no_matching_row                                                                                                                                                                                                                                                |
| TRADFI:CBOE:ohlcv_24h  | skip  | failed | ambiguous      | 0    | 5       | no_matching_row | not_checked | manifest_status_invalid:no_matching_row; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                                                                                                                                                         |
| TRADFI:FX:ohlcv_24h    | force | failed | not_applicable | 0    | 11      | no_matching_row | not_checked | manifest_status_invalid:no_matching_row                                                                                                                                                                                                                                                |
| TRADFI:FX:ohlcv_24h    | skip  | failed | ambiguous      | 0    | 11      | no_matching_row | not_checked | manifest_status_invalid:no_matching_row; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                                                                                                                                                         |

## Bucket paths (where each write/read actually landed)

| Shard                  | Leg   | Parquet bucket                                        | Manifest bucket                                       | Same bucket? |
| ---------------------- | ----- | ----------------------------------------------------- | ----------------------------------------------------- | ------------ |
| TRADFI:NASDAQ:ohlcv_1m | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:NASDAQ:ohlcv_1m | skip  | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:NYSE:ohlcv_1m   | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:NYSE:ohlcv_1m   | skip  | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CME:ohlcv_1m    | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CME:ohlcv_1m    | skip  | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:ICE:ohlcv_24h   | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:ICE:ohlcv_24h   | skip  | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CBOE:ohlcv_24h  | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CBOE:ohlcv_24h  | skip  | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:FX:ohlcv_24h    | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:FX:ohlcv_24h    | skip  | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |

## Failed cells

| Shard                  | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Content     | Reason                                                                                                                                                                                                                                                                                 |
| ---------------------- | ----- | ------ | -------------- | ---- | ------- | --------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TRADFI:NASDAQ:ohlcv_1m | force | failed | not_applicable | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NASDAQ/                                                                                                          |
| TRADFI:NASDAQ:ohlcv_1m | skip  | failed | genuine        | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NASDAQ/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                   |
| TRADFI:NYSE:ohlcv_1m   | force | failed | not_applicable | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NYSE/                                                                                                            |
| TRADFI:NYSE:ohlcv_1m   | skip  | failed | genuine        | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=NYSE/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                     |
| TRADFI:CME:ohlcv_1m    | force | failed | not_applicable | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/data_type=ohlcv_1m/underlying=CL-MCL/                                                                        |
| TRADFI:CME:ohlcv_1m    | skip  | failed | genuine        | 0    | 0       | -               | not_checked | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/data_type=ohlcv_1m/underlying=CL-MCL/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| TRADFI:ICE:ohlcv_24h   | force | failed | not_applicable | 0    | 1       | no_matching_row | not_checked | manifest_status_invalid:no_matching_row                                                                                                                                                                                                                                                |
| TRADFI:ICE:ohlcv_24h   | skip  | failed | genuine        | 0    | 1       | no_matching_row | not_checked | manifest_status_invalid:no_matching_row; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                                                                                                                                                         |
| TRADFI:CBOE:ohlcv_24h  | force | failed | not_applicable | 0    | 5       | no_matching_row | not_checked | manifest_status_invalid:no_matching_row                                                                                                                                                                                                                                                |
| TRADFI:CBOE:ohlcv_24h  | skip  | failed | ambiguous      | 0    | 5       | no_matching_row | not_checked | manifest_status_invalid:no_matching_row; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                                                                                                                                                         |
| TRADFI:FX:ohlcv_24h    | force | failed | not_applicable | 0    | 11      | no_matching_row | not_checked | manifest_status_invalid:no_matching_row                                                                                                                                                                                                                                                |
| TRADFI:FX:ohlcv_24h    | skip  | failed | ambiguous      | 0    | 11      | no_matching_row | not_checked | manifest_status_invalid:no_matching_row; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                                                                                                                                                                         |
