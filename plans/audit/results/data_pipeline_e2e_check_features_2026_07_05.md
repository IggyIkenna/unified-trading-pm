---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)"
summary: "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05: total=1 passed=0 failed=1 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-07-27
audited_scope: "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-05, legs=benchmark"
date: 2026-07-27
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-05
generated_at: 2026-07-27T23:49:05.999010+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)

**Legs:** benchmark  
**Started:** 2026-07-27T23:45:02.685394+00:00  **Finished:** 2026-07-27T23:49:05.998847+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05: total=1 passed=0 failed=1 ambiguous=0 skipped=0

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Reason |
|---|---|---|---|---|---|---|---|
| CEFI:delta_one | benchmark | failed | not_applicable | 1 | 0 | - | window=2026-06-21..2026-07-05 (14d) wall_clock=224s ~16s/shard-day objects=0 |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| CEFI:delta_one | benchmark | `features-cefi-test-central-element-323112` | `-` | - |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Reason |
|---|---|---|---|---|---|---|---|
| CEFI:delta_one | benchmark | failed | not_applicable | 1 | 0 | - | window=2026-06-21..2026-07-05 (14d) wall_clock=224s ~16s/shard-day objects=0 |

