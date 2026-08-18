---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-09)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-09: total=1 passed=0 failed=1 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-13
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-07-09, legs=force"
date: 2026-07-13
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-07-09
generated_at: 2026-07-13T00:21:53.920820+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-09)

**Legs:** force **Started:** 2026-07-13T00:16:41.920900+00:00 **Finished:** 2026-07-13T00:21:53.920555+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-09: total=1 passed=0 failed=1 ambiguous=0 skipped=0

## Results

| Shard               | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                     |
| ------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TRADFI:CME:ohlcv_1m | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-09/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/ |

## Bucket paths (where each write/read actually landed)

| Shard               | Leg   | Parquet bucket                                        | Manifest bucket                                       | Same bucket? |
| ------------------- | ----- | ----------------------------------------------------- | ----------------------------------------------------- | ------------ |
| TRADFI:CME:ohlcv_1m | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |

## Failed cells

| Shard               | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                     |
| ------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TRADFI:CME:ohlcv_1m | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-tradfi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-09/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/ |
