---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-05)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-05: total=2 passed=2 failed=0 ambiguous=0 skipped=0"
status: pass
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-10
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-07-10
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P3
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-07-05
generated_at: 2026-07-10T16:14:59.052588+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-07-05)

**Legs:** force, skip **Started:** 2026-07-10T16:05:17.808922+00:00 **Finished:** 2026-07-10T16:14:59.048315+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-07-05: total=2 passed=2 failed=0 ambiguous=0 skipped=0

## Results

| Shard                       | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Reason |
| --------------------------- | ----- | ------ | -------------- | ---- | ------- | --------------- | ------ |
| CEFI:BINANCE-FUTURES:trades | force | passed | not_applicable | 0    | 1       | empty_confirmed | -      |
| CEFI:BINANCE-FUTURES:trades | skip  | passed | genuine        | 0    | 1       | empty_confirmed | -      |
