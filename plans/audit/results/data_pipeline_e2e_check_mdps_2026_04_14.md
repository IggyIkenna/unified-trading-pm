---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-04-14)"
summary: "data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-04-14: total=6 passed=2 failed=2 ambiguous=0 skipped=2"
status: partial
nature: record
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mdps]
related: []
created: 2026-08-16
audited_scope: "data_pipeline_e2e_check_mdps real-VM force/skip/live pipeline check for day=2026-04-14, legs=force,skip"
date: 2026-08-16
auditor: data_pipeline_e2e_check_mdps (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mdps
run_date: 2026-04-14
generated_at: 2026-08-16T11:12:19.320803+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-04-14)

**Legs:** force, skip
**Started:** 2026-08-09T22:14:47.844846+00:00  **Finished:** 2026-08-16T11:12:19.319823+00:00

**Summary:** data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-04-14: total=6 passed=2 failed=2 ambiguous=0 skipped=2

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:15m | force | passed | not_applicable | 0 | 572 | captured | unreadable | ok |
| SPORTS:*:odds_horizon_bucket:1h | force | passed | not_applicable | 0 | 572 | captured | unreadable | ok |
| SPORTS:*:odds_horizon_bucket:4h | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:*:odds_horizon_bucket:24h | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:*:odds_horizon_bucket:15m | skip | skipped | not_applicable | - | 0 | - | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260816-110550-d0c755 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:1h | skip | skipped | not_applicable | - | 0 | - | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260816-110550-d0c755 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:15m | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:1h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:4h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:24h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:15m | skip | `-` | `-` | - |
| SPORTS:*:odds_horizon_bucket:1h | skip | `-` | `-` | - |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:4h | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:*:odds_horizon_bucket:24h | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |


## Migration worklist (canonical-shape gaps)

Cells whose data EXISTS but diverges from the DECLARED SSOT template, plus
genuinely-malformed objects. These are NOT passes and the declared template is
deliberately never relaxed to absorb them. Note these rows are INDEPENDENT of the
force/skip verdict: a cell can be force-green (the writer wrote where it really
writes) and still appear here (the emitted path is not the declared one). Each row
is migration work: bring the object path / input shard atom onto the declared
template, then re-run. Grep: `non_canonical` / `content_check=non_canonical`.

_(none — every checked cell was canonically shaped)_
