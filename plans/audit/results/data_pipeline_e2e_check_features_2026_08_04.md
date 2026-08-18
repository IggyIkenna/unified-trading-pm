---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-04)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-04: total=3 passed=0 failed=1 ambiguous=0 skipped=2"
status: fail
nature: record
asset_group: [prediction, tradfi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-05
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-08-04, legs=force,skip,benchmark"
date: 2026-08-05
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-08-04
generated_at: 2026-08-05T22:38:44.770466+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-08-04)

**Legs:** force, skip, benchmark **Started:** 2026-08-05T12:23:44.642745+00:00 **Finished:**
2026-08-05T22:38:44.769618+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-08-04: total=3 passed=0 failed=1 ambiguous=0
skipped=2

## Results

| Shard                | Leg       | Status  | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                      |
| -------------------- | --------- | ------- | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------- |
| PREDICTION:delta_one | force     | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_input_for_window (window 2026-08-03..2026-08-04, lookback=1d)   |
| PREDICTION:delta_one | skip      | skipped | not_applicable | -    | 0       | -        | not_checked | no_captured_input_for_window (window 2026-08-03..2026-08-04, lookback=1d)   |
| TRADFI:volatility    | benchmark | failed  | not_applicable | 1    | 0       | -        | not_checked | window=2026-07-28..2026-08-04 (7d) wall_clock=171s ~24s/shard-day objects=0 |

## Bucket paths (where each write/read actually landed)

| Shard                | Leg       | Parquet bucket                                | Manifest bucket | Same bucket? |
| -------------------- | --------- | --------------------------------------------- | --------------- | ------------ |
| PREDICTION:delta_one | force     | `-`                                           | `-`             | -            |
| PREDICTION:delta_one | skip      | `-`                                           | `-`             | -            |
| TRADFI:volatility    | benchmark | `features-tradfi-test-central-element-323112` | `-`             | -            |

## Failed cells

| Shard             | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason                                                                      |
| ----------------- | --------- | ------ | -------------- | ---- | ------- | -------- | ----------- | --------------------------------------------------------------------------- |
| TRADFI:volatility | benchmark | failed | not_applicable | 1    | 0       | -        | not_checked | window=2026-07-28..2026-08-04 (7d) wall_clock=171s ~24s/shard-day objects=0 |
