---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2025-12-20)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2025-12-20: total=2 passed=0 failed=2 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [sports]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-01
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2025-12-20, legs=force,skip"
date: 2026-08-01
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2025-12-20
generated_at: 2026-08-01T10:33:13.195521+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2025-12-20)

**Legs:** force, skip **Started:** 2026-08-01T10:25:38.984653+00:00 **Finished:** 2026-08-01T10:33:13.195332+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2025-12-20: total=2 passed=0 failed=2 ambiguous=0
skipped=0

## Results

| Shard         | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                           |
| ------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | -------------------------------- |
| SPORTS:sports | force | failed | not_applicable | 1    | 0       | -        | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:sports | skip  | failed | not_applicable | 1    | 0       | -        | not_checked | vm_not_success (exit=1)          |

## Bucket paths (where each write/read actually landed)

| Shard         | Leg   | Parquet bucket                                | Manifest bucket                               | Same bucket? |
| ------------- | ----- | --------------------------------------------- | --------------------------------------------- | ------------ |
| SPORTS:sports | force | `features-sports-test-central-element-323112` | `features-sports-test-central-element-323112` | yes          |
| SPORTS:sports | skip  | `features-sports-test-central-element-323112` | `features-sports-test-central-element-323112` | yes          |

## Failed cells

| Shard         | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                           |
| ------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | -------------------------------- |
| SPORTS:sports | force | failed | not_applicable | 1    | 0       | -        | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:sports | skip  | failed | not_applicable | 1    | 0       | -        | not_checked | vm_not_success (exit=1)          |
