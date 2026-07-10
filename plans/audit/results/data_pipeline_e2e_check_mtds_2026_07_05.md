---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-05)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-05: total=2 passed=0 failed=2 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-10
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-07-10
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-07-05
generated_at: 2026-07-10T14:24:15.770246+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-05)

**Legs:** force, skip **Started:** 2026-07-10T13:34:46.652852+00:00 **Finished:** 2026-07-10T13:44:44.873635+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-05: total=2 passed=0 failed=2 ambiguous=0 skipped=0

## Results

| Shard                       | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                    |
| --------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:BINANCE-FUTURES:trades | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-05/asset_group=cefi/venue=BINANCE-FUTURES/                                      |
| CEFI:BINANCE-FUTURES:trades | skip  | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-05/asset_group=cefi/venue=BINANCE-FUTURES/; object_signature_changed_or_missing |

## Failed cells

| Shard                       | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                    |
| --------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:BINANCE-FUTURES:trades | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-05/asset_group=cefi/venue=BINANCE-FUTURES/                                      |
| CEFI:BINANCE-FUTURES:trades | skip  | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-05/asset_group=cefi/venue=BINANCE-FUTURES/; object_signature_changed_or_missing |
