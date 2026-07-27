---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-21)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-21: total=2 passed=0 failed=2 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-07-27
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-21, legs=force,skip"
date: 2026-07-27
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-21
generated_at: 2026-07-27T06:25:08.510798+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-21)

**Legs:** force, skip  
**Started:** 2026-07-27T06:17:00.428453+00:00 **Finished:** 2026-07-27T06:25:08.510615+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-21: total=2 passed=0 failed=2 ambiguous=0
skipped=0

## Results

| Shard          | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                           |
| -------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------- |
| CEFI:delta_one | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
| CEFI:delta_one | skip  | failed | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)          |

## Bucket paths (where each write/read actually landed)

| Shard          | Leg   | Parquet bucket                              | Manifest bucket                             | Same bucket? |
| -------------- | ----- | ------------------------------------------- | ------------------------------------------- | ------------ |
| CEFI:delta_one | force | `features-cefi-test-central-element-323112` | `features-cefi-test-central-element-323112` | yes          |
| CEFI:delta_one | skip  | `features-cefi-test-central-element-323112` | `features-cefi-test-central-element-323112` | yes          |

## Failed cells

| Shard          | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                           |
| -------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------- |
| CEFI:delta_one | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
| CEFI:delta_one | skip  | failed | not_applicable | 1    | 0       | -        | vm_not_success (exit=1)          |
