---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2025-03-12)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2025-03-12: total=2 passed=0 failed=2 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-20
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2025-03-12, legs=force,skip"
date: 2026-07-20
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2025-03-12
generated_at: 2026-07-20T20:14:32.486661+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2025-03-12)

**Legs:** force, skip  
**Started:** 2026-07-20T20:04:13.642182+00:00  **Finished:** 2026-07-20T20:14:32.471730+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2025-03-12: total=2 passed=0 failed=2 ambiguous=0 skipped=0

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Reason |
|---|---|---|---|---|---|---|---|
| DEFI:AAVE_V3:lending_indices | force | failed | not_applicable | 0 | 0 | - | no_parquet_under:gs://market-data-tick-defi-test-central-element-323112/raw_tick_data/by_date/day=2025-12-31/pipeline_mode=batch_onchain_subgraph/asset_group=defi/ |
| DEFI:AAVE_V3:lending_indices | skip | failed | genuine | 0 | 0 | - | no_parquet_under:gs://market-data-tick-defi-test-central-element-323112/raw_tick_data/by_date/day=2025-12-31/pipeline_mode=batch_onchain_subgraph/asset_group=defi/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| DEFI:AAVE_V3:lending_indices | force | `market-data-tick-defi-test-central-element-323112` | `market-data-tick-defi-test-central-element-323112` | yes |
| DEFI:AAVE_V3:lending_indices | skip | `market-data-tick-defi-test-central-element-323112` | `market-data-tick-defi-test-central-element-323112` | yes |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Reason |
|---|---|---|---|---|---|---|---|
| DEFI:AAVE_V3:lending_indices | force | failed | not_applicable | 0 | 0 | - | no_parquet_under:gs://market-data-tick-defi-test-central-element-323112/raw_tick_data/by_date/day=2025-12-31/pipeline_mode=batch_onchain_subgraph/asset_group=defi/ |
| DEFI:AAVE_V3:lending_indices | skip | failed | genuine | 0 | 0 | - | no_parquet_under:gs://market-data-tick-defi-test-central-element-323112/raw_tick_data/by_date/day=2025-12-31/pipeline_mode=batch_onchain_subgraph/asset_group=defi/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |

