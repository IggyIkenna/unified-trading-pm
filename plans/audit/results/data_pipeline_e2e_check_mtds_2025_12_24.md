---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2025-12-24)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2025-12-24: total=20 passed=0 failed=4 ambiguous=0 skipped=16"
status: fail
nature: record
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-08-01
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2025-12-24, legs=force,skip"
date: 2026-08-01
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2025-12-24
generated_at: 2026-08-01T14:43:21.986043+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2025-12-24)

**Legs:** force, skip **Started:** 2026-08-01T14:28:49.654401+00:00 **Finished:** 2026-08-01T14:43:21.985820+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2025-12-24: total=20 passed=0 failed=4 ambiguous=0
skipped=16

## Results

| Shard                                 | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                                                |
| ------------------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SPORTS:ODDS_API:odds                  | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:odds                  | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:odds_snapshot         | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:odds_snapshot         | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:odds_movement         | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:odds_movement         | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:arbitrage_opportunity | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:arbitrage_opportunity | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:odds_horizon_bucket   | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2025-12-24/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/venue=ODDS_API/                                                                        |
| SPORTS:ODDS_API:odds_horizon_bucket   | skip  | failed  | ambiguous      | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2025-12-24/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/venue=ODDS_API/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| SPORTS:ODDS_API:markets               | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:markets               | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:outcomes              | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:outcomes              | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:settlements           | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:settlements           | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:trades                | force | failed  | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2026-06-24/pipeline_mode=batch_odds_api/asset_group=sports/venue=ODDS_API/                                                                                        |
| SPORTS:ODDS_API:trades                | skip  | failed  | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2026-06-24/pipeline_mode=batch_odds_api/asset_group=sports/venue=ODDS_API/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                 |
| SPORTS:ODDS_API:trades_inplay         | force | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |
| SPORTS:ODDS_API:trades_inplay         | skip  | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_data_for_cell                                                                                                                                                                                                                                             |

## Bucket paths (where each write/read actually landed)

| Shard                                 | Leg   | Parquet bucket                                        | Manifest bucket                                       | Same bucket? |
| ------------------------------------- | ----- | ----------------------------------------------------- | ----------------------------------------------------- | ------------ |
| SPORTS:ODDS_API:odds                  | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:odds                  | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:odds_snapshot         | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:odds_snapshot         | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:odds_movement         | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:odds_movement         | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:arbitrage_opportunity | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:arbitrage_opportunity | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:odds_horizon_bucket   | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:ODDS_API:odds_horizon_bucket   | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:ODDS_API:markets               | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:markets               | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:outcomes              | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:outcomes              | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:settlements           | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:settlements           | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:trades                | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:ODDS_API:trades                | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:ODDS_API:trades_inplay         | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:ODDS_API:trades_inplay         | skip  | `-`                                                   | `-`                                                   | -            |

## Failed cells

| Shard                               | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                                                                                                                                                                                                                |
| ----------------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SPORTS:ODDS_API:odds_horizon_bucket | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2025-12-24/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/venue=ODDS_API/                                                                        |
| SPORTS:ODDS_API:odds_horizon_bucket | skip  | failed | ambiguous      | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2025-12-24/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/venue=ODDS_API/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| SPORTS:ODDS_API:trades              | force | failed | not_applicable | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2026-06-24/pipeline_mode=batch_odds_api/asset_group=sports/venue=ODDS_API/                                                                                        |
| SPORTS:ODDS_API:trades              | skip  | failed | genuine        | 0    | 0       | -        | not_checked | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2026-06-24/pipeline_mode=batch_odds_api/asset_group=sports/venue=ODDS_API/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                 |
