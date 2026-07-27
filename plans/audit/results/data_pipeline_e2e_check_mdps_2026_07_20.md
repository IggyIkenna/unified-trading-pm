---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-07-20)"
summary: "data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-07-20: total=21 passed=7 failed=14 ambiguous=0 skipped=0"
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mdps]
related: []
created: 2026-07-27
audited_scope: "data_pipeline_e2e_check_mdps real-VM force/skip/live pipeline check for day=2026-07-20, legs=force,skip,canonical"
date: 2026-07-27
auditor: data_pipeline_e2e_check_mdps (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mdps
run_date: 2026-07-20
generated_at: 2026-07-27T02:08:24.118037+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-07-20)

**Legs:** force, skip, canonical  
**Started:** 2026-07-27T01:57:34.578454+00:00  **Finished:** 2026-07-27T02:08:23.702710+00:00

**Summary:** data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-07-20: total=21 passed=7 failed=14 ambiguous=0 skipped=0

## Results

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Reason |
|---|---|---|---|---|---|---|---|
| CEFI:BINANCE-FUTURES:trades:15s | force | passed | not_applicable | 0 | 2 | captured | ok |
| CEFI:BINANCE-FUTURES:trades:1m | force | passed | not_applicable | 0 | 2 | captured | ok |
| CEFI:BINANCE-FUTURES:trades:5m | force | passed | not_applicable | 0 | 2 | captured | ok |
| CEFI:BINANCE-FUTURES:trades:15m | force | passed | not_applicable | 0 | 2 | captured | ok |
| CEFI:BINANCE-FUTURES:trades:1h | force | passed | not_applicable | 0 | 2 | captured | ok |
| CEFI:BINANCE-FUTURES:trades:4h | force | passed | not_applicable | 0 | 2 | captured | ok |
| CEFI:BINANCE-FUTURES:trades:24h | force | passed | not_applicable | 0 | 1 | captured | ok |
| CEFI:BINANCE-FUTURES:trades:15s | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:1m | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:5m | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:15m | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:1h | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:4h | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:24h | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:15s | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:1m | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:5m | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:15m | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:1h | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:4h | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:24h | canonical | failed | not_applicable | - | 1 | - | content_check=non_canonical: missing_segment=instrument_type; timeframe=24h!=1d — objects found=2 (on_measured_template=1, off_template=1); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |


## Bucket paths (where each write/read actually landed)

| Shard | Leg | Parquet bucket | Manifest bucket | Same bucket? |
|---|---|---|---|---|
| CEFI:BINANCE-FUTURES:trades:15s | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:1m | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:5m | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:15m | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:1h | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:4h | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:24h | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:15s | skip | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:1m | skip | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:5m | skip | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:15m | skip | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:1h | skip | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:4h | skip | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:24h | skip | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:15s | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:1m | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:5m | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:15m | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:1h | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:4h | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |
| CEFI:BINANCE-FUTURES:trades:24h | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes |

## Failed cells

| Shard | Leg | Status | Skip proof | Exit | Parquet | Manifest | Reason |
|---|---|---|---|---|---|---|---|
| CEFI:BINANCE-FUTURES:trades:15s | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:1m | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:5m | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:15m | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:1h | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:4h | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:24h | skip | failed | ambiguous | - | 0 | - | vm_not_success:vm_self_deleted_no_exit_status |
| CEFI:BINANCE-FUTURES:trades:15s | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:1m | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:5m | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:15m | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:1h | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:4h | canonical | failed | not_applicable | - | 2 | - | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:24h | canonical | failed | not_applicable | - | 1 | - | content_check=non_canonical: missing_segment=instrument_type; timeframe=24h!=1d — objects found=2 (on_measured_template=1, off_template=1); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |


## Migration worklist (canonical-shape gaps)

Cells whose data EXISTS but diverges from the DECLARED SSOT template, plus
genuinely-malformed objects. These are NOT passes and the declared template is
deliberately never relaxed to absorb them. Note these rows are INDEPENDENT of the
force/skip verdict: a cell can be force-green (the writer wrote where it really
writes) and still appear here (the emitted path is not the declared one). Each row
is migration work: bring the object path / input shard atom onto the declared
template, then re-run. Grep: `non_canonical` / `content_check=non_canonical`.

| Shard | Leg | Status | Reason |
|---|---|---|---|
| CEFI:BINANCE-FUTURES:trades:15s | canonical | failed | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:1m | canonical | failed | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:5m | canonical | failed | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:15m | canonical | failed | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:1h | canonical | failed | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:4h | canonical | failed | content_check=non_canonical: missing_segment=instrument_type — objects found=2 (on_measured_template=2, off_template=0); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
| CEFI:BINANCE-FUTURES:trades:24h | canonical | failed | content_check=non_canonical: missing_segment=instrument_type; timeframe=24h!=1d — objects found=2 (on_measured_template=1, off_template=1); ids checked=1 canonical=1 (declared-SSOT template; checked per_vm_shard) |
