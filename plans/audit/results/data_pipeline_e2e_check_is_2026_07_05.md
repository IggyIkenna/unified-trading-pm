---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_is (2026-07-05)"
summary: "data_pipeline_e2e_check_is pipeline-e2e-check 2026-07-05: total=2 passed=2 failed=0 ambiguous=0 skipped=0"
status: pass
nature: record
asset_group: [cefi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_is]
related: []
created: 2026-07-10
audited_scope: "data_pipeline_e2e_check_is real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-07-10
auditor: data_pipeline_e2e_check_is (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_is
run_date: 2026-07-05
generated_at: 2026-07-10T14:24:15.769322+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_is (2026-07-05)

**Legs:** force, skip **Started:** 2026-07-10T12:57:24.519142+00:00 **Finished:** 2026-07-10T13:03:37.437461+00:00

**Summary:** data_pipeline_e2e_check_is pipeline-e2e-check 2026-07-05: total=2 passed=2 failed=0 ambiguous=0 skipped=0

## Results

| Shard                           | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason |
| ------------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ------ |
| CEFI/BINANCE-FUTURES/2026-07-05 | force | passed | not_applicable | 0    | 1       | captured | ok     |
| CEFI/BINANCE-FUTURES/2026-07-05 | skip  | passed | genuine        | 0    | 1       | captured | ok     |
