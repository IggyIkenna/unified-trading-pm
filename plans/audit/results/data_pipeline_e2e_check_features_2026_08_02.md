---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-02)"
summary: "data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-02: total=1 passed=0 failed=1 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-02
audited_scope: "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-08-02, legs=benchmark"
date: 2026-08-02
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-08-02
generated_at: 2026-08-02T14:44:14.370923+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-02)

**Legs:** benchmark  
**Started:** 2026-08-02T14:40:12.931121+00:00  **Finished:** 2026-08-02T14:44:14.370724+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-02: total=1 passed=0 failed=1 ambiguous=0 skipped=0

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| CEFI:delta_one | benchmark | failed | not_applicable | 1 | 0 | - | not_checked | window=2026-07-03..2026-08-02 (30d) wall_clock=221s ~7s/shard-day objects=0 |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| CEFI:delta_one | benchmark | `features-cefi-test-central-element-323112` | `-` | - |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| CEFI:delta_one | benchmark | failed | not_applicable | 1 | 0 | - | not_checked | window=2026-07-03..2026-08-02 (30d) wall_clock=221s ~7s/shard-day objects=0 |

