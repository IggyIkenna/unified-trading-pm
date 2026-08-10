---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-04-14)"
summary: "data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-04-14: total=6 passed=2 failed=4 ambiguous=0 skipped=0"
status: partial
nature: record
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mdps]
related: []
created: 2026-08-10
audited_scope: "data_pipeline_e2e_check_mdps real-VM force/skip/live pipeline check for day=2026-04-14, legs=force,skip"
date: 2026-08-10
auditor: data_pipeline_e2e_check_mdps (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mdps
run_date: 2026-04-14
generated_at: 2026-08-10T02:37:34.724641+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-04-14)

**Legs:** force, skip  
**Started:** 2026-08-09T22:14:47.844846+00:00  **Finished:** 2026-08-10T02:37:34.665184+00:00

**Summary:** data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-04-14: total=6 passed=2 failed=4 ambiguous=0 skipped=0

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:15m | force | passed | not_applicable | 0 | 477 | captured | unreadable | ok |
| SPORTS:*:odds_horizon_bucket:1h | force | passed | not_applicable | 0 | 477 | captured | unreadable | ok |
| SPORTS:*:odds_horizon_bucket:4h | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:*:odds_horizon_bucket:24h | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:*:odds_horizon_bucket:15m | skip | failed | genuine | 0 | 0 | - | not_checked | skip_signal_not_found_in_run_log |
| SPORTS:*:odds_horizon_bucket:1h | skip | failed | genuine | 0 | 0 | - | not_checked | skip_signal_not_found_in_run_log |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:15m | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:1h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:4h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:24h | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:15m | skip | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |
| SPORTS:*:odds_horizon_bucket:1h | skip | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Content | Reason |
|---|---|---|---|---|---|---|---|---|
| SPORTS:*:odds_horizon_bucket:4h | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:*:odds_horizon_bucket:24h | force | failed | not_applicable | 1 | 0 | - | not_checked | vm_not_success:vm_exit_nonzero=1 |
| SPORTS:*:odds_horizon_bucket:15m | skip | failed | genuine | 0 | 0 | - | not_checked | skip_signal_not_found_in_run_log |
| SPORTS:*:odds_horizon_bucket:1h | skip | failed | genuine | 0 | 0 | - | not_checked | skip_signal_not_found_in_run_log |


## Migration worklist (canonical-shape gaps)

Cells whose data EXISTS but diverges from the DECLARED SSOT template, plus
genuinely-malformed objects. These are NOT passes and the declared template is
deliberately never relaxed to absorb them. Note these rows are INDEPENDENT of the
force/skip verdict: a cell can be force-green (the writer wrote where it really
writes) and still appear here (the emitted path is not the declared one). Each row
is migration work: bring the object path / input shard atom onto the declared
template, then re-run. Grep: `non_canonical` / `content_check=non_canonical`.

_(none — every checked cell was canonically shaped)_
