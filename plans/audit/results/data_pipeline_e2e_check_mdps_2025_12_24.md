---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mdps (2025-12-24)"
summary: "data_pipeline_e2e_check_mdps pipeline-e2e-check 2025-12-24: total=8 passed=0 failed=4 ambiguous=0 skipped=4"
status: fail
nature: record
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mdps]
related: []
created: 2026-08-01
audited_scope: "data_pipeline_e2e_check_mdps real-VM force/skip/live pipeline check for day=2025-12-24, legs=force,skip"
date: 2026-08-01
auditor: data_pipeline_e2e_check_mdps (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mdps
run_date: 2025-12-24
generated_at: 2026-08-01T11:39:09.027430+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mdps (2025-12-24)

**Legs:** force, skip  
**Started:** 2026-08-01T11:09:01.326651+00:00  **Finished:** 2026-08-01T11:39:08.936834+00:00

**Summary:** data_pipeline_e2e_check_mdps pipeline-e2e-check 2025-12-24: total=8 passed=0 failed=4 ambiguous=0 skipped=4

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:15m | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:timeout_no_exit_status |
| SPORTS:*:odds_horizon_bucket:1h | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:timeout_no_exit_status |
| SPORTS:*:odds_horizon_bucket:4h | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:timeout_no_exit_status |
| SPORTS:*:odds_horizon_bucket:24h | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:timeout_no_exit_status |
| SPORTS:*:odds_horizon_bucket:15m | skip | skipped | not_applicable | - | 0 | - | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-110907-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:1h | skip | skipped | not_applicable | - | 0 | - | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-110907-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:4h | skip | skipped | not_applicable | - | 0 | - | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-110907-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:24h | skip | skipped | not_applicable | - | 0 | - | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-110907-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:15m | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:1h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:4h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:24h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:15m | skip | `-` | `-` | - |
| SPORTS:*:odds_horizon_bucket:1h | skip | `-` | `-` | - |
| SPORTS:*:odds_horizon_bucket:4h | skip | `-` | `-` | - |
| SPORTS:*:odds_horizon_bucket:24h | skip | `-` | `-` | - |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:15m | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:timeout_no_exit_status |
| SPORTS:*:odds_horizon_bucket:1h | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:timeout_no_exit_status |
| SPORTS:*:odds_horizon_bucket:4h | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:timeout_no_exit_status |
| SPORTS:*:odds_horizon_bucket:24h | force | failed | not_applicable | - | 0 | - | not_checked | vm_not_success:timeout_no_exit_status |


## Migration worklist (canonical-shape gaps)

Cells whose data EXISTS but diverges from the DECLARED SSOT template, plus
genuinely-malformed objects. These are NOT passes and the declared template is
deliberately never relaxed to absorb them. Note these rows are INDEPENDENT of the
force/skip verdict: a cell can be force-green (the writer wrote where it really
writes) and still appear here (the emitted path is not the declared one). Each row
is migration work: bring the object path / input shard atom onto the declared
template, then re-run. Grep: `non_canonical` / `content_check=non_canonical`.

_(none — every checked cell was canonically shaped)_
