---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-20)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-08-20: total=8 passed=1 failed=3 ambiguous=0 skipped=4"
status: partial
nature: record
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-08-20
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-08-20, legs=force,skip"
date: 2026-08-20
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-08-20
generated_at: 2026-08-20T23:08:58.898279+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-08-20)

**Legs:** force, skip
**Started:** 2026-08-20T22:48:40.669127+00:00  **Finished:** 2026-08-20T23:08:58.831237+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-08-20: total=8 passed=1 failed=3 ambiguous=0 skipped=4

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| PREDICTION:POLYMARKET:trades | force | passed | not_applicable | 0 | 1 | captured | not_checked | - |
| PREDICTION:POLYMARKET:trades | skip | failed | ambiguous | 0 | 1 | empty_confirmed | not_checked | skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| PREDICTION:POLYMARKET:book_snapshot_5 | force | skipped | not_applicable | - | 0 | - | not_checked | live_only_data_type: batch cannot fetch a historical order-book snapshot |
| PREDICTION:POLYMARKET:book_snapshot_5 | skip | skipped | not_applicable | - | 0 | - | not_checked | live_only_data_type: batch cannot fetch a historical order-book snapshot |
| PREDICTION:KALSHI:trades | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:launcher_script_client_timeout_120s_exhausted_retries |
| PREDICTION:KALSHI:trades | skip | failed | genuine | 0 | 0 | - | not_checked | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-08-07/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| PREDICTION:KALSHI:book_snapshot_5 | force | skipped | not_applicable | - | 0 | - | not_checked | live_only_data_type: batch cannot fetch a historical order-book snapshot |
| PREDICTION:KALSHI:book_snapshot_5 | skip | skipped | not_applicable | - | 0 | - | not_checked | live_only_data_type: batch cannot fetch a historical order-book snapshot |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| PREDICTION:POLYMARKET:trades | force | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes |
| PREDICTION:POLYMARKET:trades | skip | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes |
| PREDICTION:POLYMARKET:book_snapshot_5 | force | `-` | `-` | - |
| PREDICTION:POLYMARKET:book_snapshot_5 | skip | `-` | `-` | - |
| PREDICTION:KALSHI:trades | force | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes |
| PREDICTION:KALSHI:trades | skip | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes |
| PREDICTION:KALSHI:book_snapshot_5 | force | `-` | `-` | - |
| PREDICTION:KALSHI:book_snapshot_5 | skip | `-` | `-` | - |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| PREDICTION:POLYMARKET:trades | skip | failed | ambiguous | 0 | 1 | empty_confirmed | not_checked | skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| PREDICTION:KALSHI:trades | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:launcher_script_client_timeout_120s_exhausted_retries |
| PREDICTION:KALSHI:trades | skip | failed | genuine | 0 | 0 | - | not_checked | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-08-07/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
