---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-05)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-05: total=1 passed=1 failed=0 ambiguous=0 skipped=0"
status: pass
nature: record
asset_group: [tradfi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-06
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-08-05, legs=benchmark"
date: 2026-08-06
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-08-05
generated_at: 2026-08-06T02:53:26.701560+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-05)

**Legs:** benchmark **Started:** 2026-08-06T02:43:13.094700+00:00 **Finished:** 2026-08-06T02:53:26.701307+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-05: total=1 passed=1 failed=0 ambiguous=0
skipped=0

## Results

| Shard            | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                      |
| ---------------- | --------- | ------ | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------- |
| TRADFI:commodity | benchmark | passed | not_applicable | 0    | 2       | -        | not_checked | window=2026-07-29..2026-08-05 (7d) wall_clock=273s ~39s/shard-day objects=2 |

## Bucket paths (where each write/read actually landed)

| Shard            | Leg       | Parquet bucket                                        | Manifest bucket | Same bucket? |
| ---------------- | --------- | ----------------------------------------------------- | --------------- | ------------ |
| TRADFI:commodity | benchmark | `commodity-signals-batch-test-central-element-323112` | `-`             | -            |
