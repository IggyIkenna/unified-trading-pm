---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-13)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-13: total=4 passed=4 failed=0 ambiguous=0 skipped=0"
status: pass
nature: record
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-24
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-07-13, legs=force,skip"
date: 2026-07-24
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-07-13
generated_at: 2026-07-24T13:03:32.083278+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-13)

**Legs:** force, skip **Started:** 2026-07-24T12:43:20.796778+00:00 **Finished:** 2026-07-24T13:03:32.078321+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-13: total=4 passed=4 failed=0 ambiguous=0 skipped=0

## Results

| Shard                | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason |
| -------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ------ |
| TRADFI:CBOE:ohlcv_1s | force | passed | not_applicable | 0    | 2       | captured | -      |
| TRADFI:CBOE:ohlcv_1s | skip  | passed | genuine        | 0    | 2       | captured | -      |
| TRADFI:CBOE:ohlcv_1m | force | passed | not_applicable | 0    | 2       | captured | -      |
| TRADFI:CBOE:ohlcv_1m | skip  | passed | genuine        | 0    | 2       | captured | -      |

## Bucket paths (where each write/read actually landed)

| Shard                | Leg   | Parquet bucket                                        | Manifest bucket                                       | Same bucket? |
| -------------------- | ----- | ----------------------------------------------------- | ----------------------------------------------------- | ------------ |
| TRADFI:CBOE:ohlcv_1s | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CBOE:ohlcv_1s | skip  | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CBOE:ohlcv_1m | force | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
| TRADFI:CBOE:ohlcv_1m | skip  | `market-data-tick-tradfi-test-central-element-323112` | `market-data-tick-tradfi-test-central-element-323112` | yes          |
