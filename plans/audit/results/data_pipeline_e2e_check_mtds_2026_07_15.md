---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-15)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-15: total=15 passed=8 failed=4 ambiguous=0 skipped=3"
status: partial
nature: record
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-20
audited_scope:
  "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-07-15, legs=force,skip,canonical"
date: 2026-07-20
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-07-15
generated_at: 2026-07-20T10:07:00.847929+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-15)

**Legs:** force, skip, canonical **Started:** 2026-07-20T09:33:41.791031+00:00 **Finished:**
2026-07-20T10:07:00.847632+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-15: total=15 passed=8 failed=4 ambiguous=0
skipped=3

## Results

| Shard                  | Leg       | Status  | Skip proof     | Exit | Parquet | Manifest        | Reason                                                                       |
| ---------------------- | --------- | ------- | -------------- | ---- | ------- | --------------- | ---------------------------------------------------------------------------- |
| TRADFI:NASDAQ:ohlcv_1m | force     | passed  | not_applicable | 0    | 1       | empty_confirmed | -                                                                            |
| TRADFI:NASDAQ:ohlcv_1m | canonical | passed  | not_applicable | -    | 1       | -               | no derivative (FUTURE/OPTION) ids in this shard, n=1 (checked per_vm_shard)  |
| TRADFI:NASDAQ:ohlcv_1m | skip      | failed  | genuine        | 0    | 1       | empty_confirmed | skip_signal_not_found_in_run_log                                             |
| TRADFI:NYSE:ohlcv_1m   | force     | passed  | not_applicable | 0    | 1       | empty_confirmed | -                                                                            |
| TRADFI:NYSE:ohlcv_1m   | canonical | passed  | not_applicable | -    | 1       | -               | no derivative (FUTURE/OPTION) ids in this shard, n=1 (checked per_vm_shard)  |
| TRADFI:NYSE:ohlcv_1m   | skip      | failed  | genuine        | 0    | 1       | empty_confirmed | skip_signal_not_found_in_run_log                                             |
| TRADFI:CME:ohlcv_1m    | force     | failed  | not_applicable | 0    | 21      | no_matching_row | manifest_status_invalid:no_matching_row                                      |
| TRADFI:CME:ohlcv_1m    | canonical | passed  | not_applicable | -    | 1       | -               | no derivative (FUTURE/OPTION) ids in this shard, n=1 (checked per_vm_shard)  |
| TRADFI:CME:ohlcv_1m    | skip      | failed  | genuine        | 0    | 21      | no_matching_row | manifest_status_invalid:no_matching_row; skip_signal_not_found_in_run_log    |
| TRADFI:CBOE:ohlcv_24h  | force     | skipped | not_applicable | -    | 0       | -               | no_captured_data_for_cell                                                    |
| TRADFI:CBOE:ohlcv_24h  | skip      | skipped | not_applicable | -    | 0       | -               | no_captured_data_for_cell                                                    |
| TRADFI:CBOE:ohlcv_24h  | canonical | skipped | not_applicable | -    | 0       | -               | no_captured_data_for_cell                                                    |
| TRADFI:FX:ohlcv_24h    | force     | passed  | not_applicable | 0    | 22      | captured        | -                                                                            |
| TRADFI:FX:ohlcv_24h    | canonical | passed  | not_applicable | -    | 11      | -               | no derivative (FUTURE/OPTION) ids in this shard, n=11 (checked per_vm_shard) |
| TRADFI:FX:ohlcv_24h    | skip      | passed  | genuine        | 0    | 22      | captured        | -                                                                            |

## Bucket paths (where each write/read actually landed)

| Shard                  | Leg       | Parquet bucket                                        | Manifest bucket                                       | Same bucket? |
| ---------------------- | --------- | ----------------------------------------------------- | ----------------------------------------------------- | ------------ |
| TRADFI:NASDAQ:ohlcv_1m | force     | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:NASDAQ:ohlcv_1m | canonical | `-`                                                   | `market-data-tick-tradfi-test-central-element-323112` | -            |
| TRADFI:NASDAQ:ohlcv_1m | skip      | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:NYSE:ohlcv_1m   | force     | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:NYSE:ohlcv_1m   | canonical | `-`                                                   | `market-data-tick-tradfi-test-central-element-323112` | -            |
| TRADFI:NYSE:ohlcv_1m   | skip      | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CME:ohlcv_1m    | force     | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CME:ohlcv_1m    | canonical | `-`                                                   | `market-data-tick-tradfi-test-central-element-323112` | -            |
| TRADFI:CME:ohlcv_1m    | skip      | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CBOE:ohlcv_24h  | force     | `-`                                                   | `-`                                                   | -            |
| TRADFI:CBOE:ohlcv_24h  | skip      | `-`                                                   | `-`                                                   | -            |
| TRADFI:CBOE:ohlcv_24h  | canonical | `-`                                                   | `-`                                                   | -            |
| TRADFI:FX:ohlcv_24h    | force     | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:FX:ohlcv_24h    | canonical | `-`                                                   | `market-data-tick-tradfi-test-central-element-323112` | -            |
| TRADFI:FX:ohlcv_24h    | skip      | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |

## Failed cells

| Shard                  | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Reason                                                                    |
| ---------------------- | ----- | ------ | -------------- | ---- | ------- | --------------- | ------------------------------------------------------------------------- |
| TRADFI:NASDAQ:ohlcv_1m | skip  | failed | genuine        | 0    | 1       | empty_confirmed | skip_signal_not_found_in_run_log                                          |
| TRADFI:NYSE:ohlcv_1m   | skip  | failed | genuine        | 0    | 1       | empty_confirmed | skip_signal_not_found_in_run_log                                          |
| TRADFI:CME:ohlcv_1m    | force | failed | not_applicable | 0    | 21      | no_matching_row | manifest_status_invalid:no_matching_row                                   |
| TRADFI:CME:ohlcv_1m    | skip  | failed | genuine        | 0    | 21      | no_matching_row | manifest_status_invalid:no_matching_row; skip_signal_not_found_in_run_log |
