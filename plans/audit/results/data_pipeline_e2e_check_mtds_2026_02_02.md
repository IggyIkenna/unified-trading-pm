---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-02-02)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-02-02: total=1 passed=0 failed=1 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-18
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-02-02, legs=force"
date: 2026-07-18
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-02-02
generated_at: 2026-07-18T14:20:08.516716+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-02-02)

**Legs:** force **Started:** 2026-07-18T14:16:25.859749+00:00 **Finished:** 2026-07-18T14:20:08.516539+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-02-02: total=1 passed=0 failed=1 ambiguous=0 skipped=0

## Results

| Shard           | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                              |
| --------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:OKX:trades | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-01-01/pipeline_mode=batch_tardis/asset_group=cefi/venue=OKX/ |

## Bucket paths (where each write/read actually landed)

| Shard           | Leg   | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| --------------- | ----- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:OKX:trades | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |

## Failed cells

| Shard           | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                              |
| --------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:OKX:trades | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-01-01/pipeline_mode=batch_tardis/asset_group=cefi/venue=OKX/ |
