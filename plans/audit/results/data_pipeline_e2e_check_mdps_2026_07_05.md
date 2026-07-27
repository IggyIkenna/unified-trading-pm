---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-07-05)"
summary: "data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-07-05: total=14 passed=0 failed=7 ambiguous=0 skipped=7"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mdps]
related: []
created: 2026-07-27
audited_scope: "data_pipeline_e2e_check_mdps real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-07-27
auditor: data_pipeline_e2e_check_mdps (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mdps
run_date: 2026-07-05
generated_at: 2026-07-27T03:21:33.333370+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-07-05)

**Legs:** force, skip **Started:** 2026-07-27T03:05:22.934661+00:00 **Finished:** 2026-07-27T03:21:33.242724+00:00

**Summary:** data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-07-05: total=14 passed=0 failed=7 ambiguous=0
skipped=7

## Results

| Shard                           | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Reason                                                   |
| ------------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | -------------------------------------------------------- |
| CEFI:BINANCE-FUTURES:trades:15s | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:1m  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:5m  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:15m | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:1h  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:4h  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:24h | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:15s | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:1m  | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:5m  | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:15m | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:1h  | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:4h  | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:24h | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |

## Bucket paths (where each write/read actually landed)

| Shard                           | Leg   | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| ------------------------------- | ----- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:BINANCE-FUTURES:trades:15s | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:1m  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:5m  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:15m | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:1h  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:4h  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:24h | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:15s | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:1m  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:5m  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:15m | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:1h  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:4h  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:24h | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |

## Failed cells

| Shard                           | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                 |
| ------------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------------- |
| CEFI:BINANCE-FUTURES:trades:15s | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:1m  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:5m  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:15m | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:1h  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:4h  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:24h | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |

## Migration worklist (canonical-shape gaps)

Cells whose data EXISTS but diverges from the DECLARED SSOT template, plus genuinely-malformed objects. These are NOT
passes and the declared template is deliberately never relaxed to absorb them. Note these rows are INDEPENDENT of the
force/skip verdict: a cell can be force-green (the writer wrote where it really writes) and still appear here (the
emitted path is not the declared one). Each row is migration work: bring the object path / input shard atom onto the
declared template, then re-run. Grep: `non_canonical` / `content_check=non_canonical`.

_(none — every checked cell was canonically shaped)_
