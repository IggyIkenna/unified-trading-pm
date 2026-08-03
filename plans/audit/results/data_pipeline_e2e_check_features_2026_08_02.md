---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-02)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-02: total=2 passed=0 failed=1 ambiguous=0 skipped=1"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-02
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-08-02, legs=force,skip"
date: 2026-08-02
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-08-02
generated_at: 2026-08-02T23:31:28.327354+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-02)

**Legs:** force, skip **Started:** 2026-08-02T19:20:28.092424+00:00 **Finished:** 2026-08-02T23:31:28.117685+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-02: total=2 passed=0 failed=1 ambiguous=0
skipped=1

## Results

| Shard          | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                           |
| -------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ----------- | ------------------------------------------------ |
| CEFI:delta_one | force | failed  | not_applicable | 1    | 0       | -        | not_checked | vm_not_success:vm_exit_nonzero=1                 |
| CEFI:delta_one | skip  | skipped | not_applicable | 0    | 0       | -        | not_checked | no_force_fingerprint_to_compare (no_skip_signal) |

## Bucket paths (where each write/read actually landed)

| Shard          | Leg   | Parquet bucket                              | Manifest bucket                             | Same bucket? |
| -------------- | ----- | ------------------------------------------- | ------------------------------------------- | ------------ |
| CEFI:delta_one | force | `features-cefi-test-central-element-323112` | `features-cefi-test-central-element-323112` | yes          |
| CEFI:delta_one | skip  | `features-cefi-test-central-element-323112` | `features-cefi-test-central-element-323112` | yes          |

## Failed cells

| Shard          | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                           |
| -------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | -------------------------------- |
| CEFI:delta_one | force | failed | not_applicable | 1    | 0       | -        | not_checked | vm_not_success:vm_exit_nonzero=1 |
