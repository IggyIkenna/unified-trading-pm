---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-26)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-26: total=2 passed=0 failed=2 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [prediction]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-05
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-26, legs=force,skip"
date: 2026-08-05
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-26
generated_at: 2026-08-05T12:32:23.990022+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-26)

**Legs:** force, skip **Started:** 2026-07-28T13:29:14.223564+00:00 **Finished:** 2026-08-05T12:32:23.989149+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-26: total=2 passed=0 failed=2 ambiguous=0
skipped=0

## Results

| Shard                | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                           |
| -------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | -------------------------------- |
| PREDICTION:delta_one | force | failed | not_applicable | 1    | 0       | -        | not_checked | vm_not_success:vm_exit_nonzero=1 |
| PREDICTION:delta_one | skip  | failed | not_applicable | -    | 0       | -        | not_checked | vm_not_success (exit=None)       |

## Bucket paths (where each write/read actually landed)

| Shard                | Leg   | Parquet bucket                              | Manifest bucket                             | Same bucket? |
| -------------------- | ----- | ------------------------------------------- | ------------------------------------------- | ------------ |
| PREDICTION:delta_one | force | `features-pred-test-central-element-323112` | `features-pred-test-central-element-323112` | yes          |
| PREDICTION:delta_one | skip  | `features-pred-test-central-element-323112` | `features-pred-test-central-element-323112` | yes          |

## Failed cells

| Shard                | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                           |
| -------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | -------------------------------- |
| PREDICTION:delta_one | force | failed | not_applicable | 1    | 0       | -        | not_checked | vm_not_success:vm_exit_nonzero=1 |
| PREDICTION:delta_one | skip  | failed | not_applicable | -    | 0       | -        | not_checked | vm_not_success (exit=None)       |
