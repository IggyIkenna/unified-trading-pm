---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2025-12-20)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2025-12-20: total=2 passed=1 failed=0 ambiguous=0 skipped=1"
status: pass
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
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2025-12-20
generated_at: 2026-08-01T11:15:01.316133+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2025-12-20)

**Legs:** force, skip **Started:** 2026-08-01T11:05:13.896956+00:00 **Finished:** 2026-08-01T11:15:01.315917+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2025-12-20: total=2 passed=1 failed=0 ambiguous=0
skipped=1

## Results

| Shard         | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest        | Content     | Reason                                                                |
| ------------- | ----- | ------- | -------------- | ---- | ------- | --------------- | ----------- | --------------------------------------------------------------------- |
| SPORTS:sports | force | passed  | not_applicable | 0    | 0       | empty_confirmed | not_checked | ok (empty_confirmed: source legitimately had no data for this window) |
| SPORTS:sports | skip  | skipped | not_applicable | 0    | 0       | -               | not_checked | no_force_fingerprint_to_compare (no_skip_signal)                      |

## Bucket paths (where each write/read actually landed)

| Shard         | Leg   | Parquet bucket                                | Manifest bucket                               | Same bucket? |
| ------------- | ----- | --------------------------------------------- | --------------------------------------------- | ------------ |
| SPORTS:sports | force | `features-sports-test-central-element-323112` | `features-sports-test-central-element-323112` | yes          |
| SPORTS:sports | skip  | `features-sports-test-central-element-323112` | `features-sports-test-central-element-323112` | yes          |
