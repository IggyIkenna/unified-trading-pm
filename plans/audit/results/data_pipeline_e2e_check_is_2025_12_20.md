---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_is (2025-12-20)"
summary: "data_pipeline_e2e_check_is pipeline-e2e-check 2025-12-20: total=1 passed=1 failed=0 ambiguous=0 skipped=0"
status: pass
nature: record
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_is]
related: []
created: 2026-08-01
audited_scope: "data_pipeline_e2e_check_is real-VM force/skip/live pipeline check for day=2025-12-20, legs=force"
date: 2026-08-01
auditor: data_pipeline_e2e_check_is (real-VM automated run)
parent_epic: infrastructure_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_is
run_date: 2025-12-20
generated_at: 2026-08-01T11:39:37.654272+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_is (2025-12-20)

**Legs:** force **Started:** 2026-08-01T11:24:05.851689+00:00 **Finished:** 2026-08-01T11:39:37.627347+00:00

**Summary:** data_pipeline_e2e_check_is pipeline-e2e-check 2025-12-20: total=1 passed=1 failed=0 ambiguous=0 skipped=0

## Results

| Shard                          | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Content     | Reason |
| ------------------------------ | ----- | ------ | -------------- | ---- | ------- | -------- | ----------- | ------ |
| SPORTS/API_FOOTBALL/2025-12-20 | force | passed | not_applicable | 0    | 669     | captured | not_checked | ok     |

## Bucket paths (where each write/read actually landed)

| Shard                          | Leg   | Parquet bucket                                         | Manifest bucket                                        | Same bucket? |
| ------------------------------ | ----- | ------------------------------------------------------ | ------------------------------------------------------ | ------------ |
| SPORTS/API_FOOTBALL/2025-12-20 | force | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
