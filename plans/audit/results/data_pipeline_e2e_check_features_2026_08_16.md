---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-16)"
summary: "data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-16: total=2 passed=0 failed=2 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [tradfi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-16
audited_scope: "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-08-16, legs=force,skip"
date: 2026-08-16
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-08-16
generated_at: 2026-08-16T01:10:43.985014+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-16)

**Legs:** force, skip
**Started:** 2026-08-16T00:39:41.109675+00:00  **Finished:** 2026-08-16T01:10:43.984677+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-16: total=2 passed=0 failed=2 ambiguous=0 skipped=0

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| TRADFI:delta_one | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| TRADFI:delta_one | skip | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success (exit=1) |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| TRADFI:delta_one | force | `features-tradfi-test-central-element-323112` | `features-tradfi-test-central-element-323112` | yes |
| TRADFI:delta_one | skip | `features-tradfi-test-central-element-323112` | `features-tradfi-test-central-element-323112` | yes |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| TRADFI:delta_one | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| TRADFI:delta_one | skip | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success (exit=1) |
