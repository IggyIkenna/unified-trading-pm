---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-06-27)"
summary: "data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-06-27: total=14 passed=7 failed=7 ambiguous=0 skipped=0"
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mdps]
related: []
created: 2026-07-22
audited_scope:
  "data_pipeline_e2e_check_mdps real-VM force/skip/live pipeline check for day=2026-06-27, legs=force,canonical"
date: 2026-07-22
auditor: data_pipeline_e2e_check_mdps (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mdps
run_date: 2026-06-27
generated_at: 2026-07-22T01:13:44.608101+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-06-27)

**Legs:** force, canonical **Started:** 2026-07-22T01:08:06.071968+00:00 **Finished:** 2026-07-22T01:13:44.607805+00:00

**Summary:** data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-06-27: total=14 passed=7 failed=7 ambiguous=0
skipped=0

## Results

| Shard                   | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                           |
| ----------------------- | --------- | ------ | -------------- | ---- | ------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:DERIBIT:trades:15s | force     | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                 |
| CEFI:DERIBIT:trades:1m  | force     | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                 |
| CEFI:DERIBIT:trades:5m  | force     | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                 |
| CEFI:DERIBIT:trades:15m | force     | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                 |
| CEFI:DERIBIT:trades:1h  | force     | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                 |
| CEFI:DERIBIT:trades:4h  | force     | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                 |
| CEFI:DERIBIT:trades:24h | force     | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1                                                                                                                                 |
| CEFI:DERIBIT:trades:15s | canonical | passed | not_applicable | -    | 29      | -        | content_check=canonical — objects found=29 (on_measured_template=29, off_template=0); ids checked=29 canonical=29 (declared-SSOT template; checked per_vm_shard) |
| CEFI:DERIBIT:trades:1m  | canonical | passed | not_applicable | -    | 29      | -        | content_check=canonical — objects found=29 (on_measured_template=29, off_template=0); ids checked=29 canonical=29 (declared-SSOT template; checked per_vm_shard) |
| CEFI:DERIBIT:trades:5m  | canonical | passed | not_applicable | -    | 29      | -        | content_check=canonical — objects found=29 (on_measured_template=29, off_template=0); ids checked=29 canonical=29 (declared-SSOT template; checked per_vm_shard) |
| CEFI:DERIBIT:trades:15m | canonical | passed | not_applicable | -    | 29      | -        | content_check=canonical — objects found=29 (on_measured_template=29, off_template=0); ids checked=29 canonical=29 (declared-SSOT template; checked per_vm_shard) |
| CEFI:DERIBIT:trades:1h  | canonical | passed | not_applicable | -    | 29      | -        | content_check=canonical — objects found=29 (on_measured_template=29, off_template=0); ids checked=29 canonical=29 (declared-SSOT template; checked per_vm_shard) |
| CEFI:DERIBIT:trades:4h  | canonical | passed | not_applicable | -    | 29      | -        | content_check=canonical — objects found=29 (on_measured_template=29, off_template=0); ids checked=29 canonical=29 (declared-SSOT template; checked per_vm_shard) |
| CEFI:DERIBIT:trades:24h | canonical | passed | not_applicable | -    | 0       | -        | content_check=canonical — objects found=29 (on_measured_template=0, off_template=29); ids checked=29 canonical=29 (declared-SSOT template; checked per_vm_shard) |

## Bucket paths (where each write/read actually landed)

| Shard                   | Leg       | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| ----------------------- | --------- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:DERIBIT:trades:15s | force     | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:1m  | force     | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:5m  | force     | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:15m | force     | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:1h  | force     | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:4h  | force     | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:24h | force     | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:15s | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:1m  | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:5m  | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:15m | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:1h  | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:4h  | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades:24h | canonical | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |

## Failed cells

| Shard                   | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                           |
| ----------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------- |
| CEFI:DERIBIT:trades:15s | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
| CEFI:DERIBIT:trades:1m  | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
| CEFI:DERIBIT:trades:5m  | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
| CEFI:DERIBIT:trades:15m | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
| CEFI:DERIBIT:trades:1h  | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
| CEFI:DERIBIT:trades:4h  | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |
| CEFI:DERIBIT:trades:24h | force | failed | not_applicable | 1    | 0       | -        | vm_not_success:vm_exit_nonzero=1 |

## Migration worklist (canonical-shape gaps)

Cells whose data EXISTS but diverges from the DECLARED SSOT template, plus genuinely-malformed objects. These are NOT
passes and the declared template is deliberately never relaxed to absorb them. Note these rows are INDEPENDENT of the
force/skip verdict: a cell can be force-green (the writer wrote where it really writes) and still appear here (the
emitted path is not the declared one). Each row is migration work: bring the object path / input shard atom onto the
declared template, then re-run. Grep: `non_canonical` / `content_check=non_canonical`.

_(none — every checked cell was canonically shaped)_
