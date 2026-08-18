---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-07)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-07: total=1 passed=0 failed=1 ambiguous=0 skipped=0"
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
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-08-07, legs=benchmark"
date: 2026-08-15
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-08-07
generated_at: 2026-08-15T10:36:32.662439+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-07)

**Legs:** benchmark **Started:** 2026-08-15T10:33:23.705609+00:00 **Finished:** 2026-08-15T10:36:32.662077+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-07: total=1 passed=0 failed=1 ambiguous=0
skipped=0

## Results

| Shard             | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                      |
| ----------------- | --------- | ------ | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------- |
| TRADFI:volatility | benchmark | failed | not_applicable | -1   | 0       | -        | not_checked | window=2026-07-31..2026-08-07 (7d) wall_clock=176s ~25s/shard-day objects=0 |

## Bucket paths (where each write/read actually landed)

| Shard             | Leg       | Parquet bucket                                | Manifest bucket | Same bucket? |
| ----------------- | --------- | --------------------------------------------- | --------------- | ------------ |
| TRADFI:volatility | benchmark | `features-tradfi-test-central-element-323112` | `-`             | -            |

## Failed cells

| Shard             | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                      |
| ----------------- | --------- | ------ | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------- |
| TRADFI:volatility | benchmark | failed | not_applicable | -1   | 0       | -        | not_checked | window=2026-07-31..2026-08-07 (7d) wall_clock=176s ~25s/shard-day objects=0 |
