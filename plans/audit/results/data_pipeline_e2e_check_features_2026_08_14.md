---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-14)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-14: total=1 passed=0 failed=1 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [tradfi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-15
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-08-14, legs=benchmark"
date: 2026-08-15
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-08-14
generated_at: 2026-08-15T09:59:03.474697+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-14)

**Legs:** benchmark **Started:** 2026-08-15T09:38:25.891397+00:00 **Finished:** 2026-08-15T09:59:03.303000+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-14: total=1 passed=0 failed=1 ambiguous=0
skipped=0

## Results

| Shard             | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                      |
| ----------------- | --------- | ------ | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------- |
| TRADFI:volatility | benchmark | failed | not_applicable | -    | 0       | -        | not_checked | window=2026-08-07..2026-08-14 (7d) wall_clock=317s ~45s/shard-day objects=0 |

## Bucket paths (where each write/read actually landed)

| Shard             | Leg       | Parquet bucket                                | Manifest bucket | Same bucket? |
| ----------------- | --------- | --------------------------------------------- | --------------- | ------------ |
| TRADFI:volatility | benchmark | `features-tradfi-test-central-element-323112` | `-`             | -            |

## Failed cells

| Shard             | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                      |
| ----------------- | --------- | ------ | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------- |
| TRADFI:volatility | benchmark | failed | not_applicable | -    | 0       | -        | not_checked | window=2026-08-07..2026-08-14 (7d) wall_clock=317s ~45s/shard-day objects=0 |
