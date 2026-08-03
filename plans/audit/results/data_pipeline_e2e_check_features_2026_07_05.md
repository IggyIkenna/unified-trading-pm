---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)"
summary: "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05: total=2 passed=0 failed=0 ambiguous=0 skipped=2"
status: pass
nature: record
asset_group: [cefi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-03
audited_scope: "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-08-03
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-05
generated_at: 2026-08-03T14:57:45.214440+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)

**Legs:** force, skip  
**Started:** 2026-08-03T14:45:06.366321+00:00  **Finished:** 2026-08-03T14:57:45.178338+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05: total=2 passed=0 failed=0 ambiguous=0 skipped=2

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| CEFI:multi_timeframe | force | skipped | not_applicable | 0 | 0 | no_matching_row | not_checked | non_canonical_object_path: output exists off-template, e.g. gs://features-cefi-test-central-element-323112/delta_one/by_date/day=2026-07-05/feature_group=candlestick_patterns/feature_group_version=1/timeframe=15m/HYPERLIQUID:PERPETUAL:0G-USD@LIN.parquet |
| CEFI:multi_timeframe | skip | skipped | not_applicable | 0 | 0 | - | not_checked | no_force_fingerprint_to_compare (no_skip_signal) |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| CEFI:multi_timeframe | force | `features-cefi-test-central-element-323112` | `features-cefi-test-central-element-323112` | yes |
| CEFI:multi_timeframe | skip | `features-cefi-test-central-element-323112` | `features-cefi-test-central-element-323112` | yes |

