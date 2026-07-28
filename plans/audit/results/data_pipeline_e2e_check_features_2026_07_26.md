---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-26)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-26: total=1 passed=0 failed=1 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [prediction]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-07-28
audited_scope: "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-26, legs=force"
date: 2026-07-28
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-26
generated_at: 2026-07-28T13:33:07.751301+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-26)

**Legs:** force **Started:** 2026-07-28T13:29:14.223564+00:00 **Finished:** 2026-07-28T13:33:07.750988+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-26: total=1 passed=0 failed=1 ambiguous=0
skipped=0

## Results

| Shard                | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                           |
| -------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------- |
| PREDICTION:delta_one | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |

## Bucket paths (where each write/read actually landed)

| Shard                | Leg   | Parquet bucket                              | Manifest bucket                             | Same bucket? |
| -------------------- | ----- | ------------------------------------------- | ------------------------------------------- | ------------ |
| PREDICTION:delta_one | force | `features-pred-test-central-element-323112` | `features-pred-test-central-element-323112` | yes          |

## Failed cells

| Shard                | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                           |
| -------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------- |
| PREDICTION:delta_one | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
