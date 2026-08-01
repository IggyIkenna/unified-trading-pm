---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_features (2025-12-18)"
summary: "data_pipeline_e2e_check_features pipeline-e2e-check 2025-12-18: total=2 passed=2 failed=0 ambiguous=0 skipped=0"
status: pass
nature: record
asset_group: [sports]
stage: [data]
repos: [features-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_features]
related: []
created: 2026-08-01
audited_scope: "data_pipeline_e2e_check_features real-VM force/skip/live pipeline check for day=2025-12-18, legs=force,skip"
date: 2026-08-01
auditor: data_pipeline_e2e_check_features (real-VM automated run)
parent_epic: infrastructure_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_features
run_date: 2025-12-18
generated_at: 2026-08-01T13:32:18.406081+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_features (2025-12-18)

**Legs:** force, skip  
**Started:** 2026-08-01T13:24:49.831017+00:00  **Finished:** 2026-08-01T13:32:18.405837+00:00

**Summary:** data_pipeline_e2e_check_features pipeline-e2e-check 2025-12-18: total=2 passed=2 failed=0 ambiguous=0 skipped=0

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:sports | force | passed | not_applicable | 0 | 6 | captured | not_applicable | ok (data: parquet + manifest captured) |
| SPORTS:sports | skip | passed | genuine | 0 | 0 | - | not_checked | ok (object byte-unchanged -> genuine skip; skip log DEBUG-level (absent, expected)) |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| SPORTS:sports | force | `features-sports-test-central-element-323112` | `features-sports-test-central-element-323112` | yes |
| SPORTS:sports | skip | `features-sports-test-central-element-323112` | `features-sports-test-central-element-323112` | yes |

