---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)"
summary:
  "data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05: total=2 passed=0 failed=0 ambiguous=0 skipped=2"
status: pass
nature: record
asset_group: [defi]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-07-27
audited_scope:
  "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-07-27
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2026-07-05
generated_at: 2026-07-27T05:40:35.289767+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2026-07-05)

**Legs:** force, skip **Started:** 2026-07-27T05:40:24.276745+00:00 **Finished:** 2026-07-27T05:40:35.289590+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2026-07-05: total=2 passed=0 failed=0 ambiguous=0
skipped=2

## Results

| Shard          | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Reason                                                                    |
| -------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ------------------------------------------------------------------------- |
| DEFI:delta_one | force | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d) |
| DEFI:delta_one | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_input_for_window (window 2026-07-04..2026-07-05, lookback=1d) |

## Bucket paths (where each write/read actually landed)

| Shard          | Leg   | Parquet bucket | Manifest bucket | Same bucket? |
| -------------- | ----- | -------------- | --------------- | ------------ |
| DEFI:delta_one | force | `-`            | `-`             | -            |
| DEFI:delta_one | skip  | `-`            | `-`             | -            |
