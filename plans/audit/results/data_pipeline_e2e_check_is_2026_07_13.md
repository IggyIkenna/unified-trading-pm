---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_is (2026-07-13)"
summary: "data_pipeline_e2e_check_is pipeline-e2e-check 2026-07-13: total=14 passed=11 failed=3 ambiguous=0 skipped=0"
status: partial
nature: record
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_is]
related: []
created: 2026-07-23
audited_scope: "data_pipeline_e2e_check_is real-VM force/skip/live pipeline check for day=2026-07-13, legs=force,skip"
date: 2026-07-23
auditor: data_pipeline_e2e_check_is (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_is
run_date: 2026-07-13
generated_at: 2026-07-23T11:58:04.896988+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_is (2026-07-13)

**Legs:** force, skip **Started:** 2026-07-23T11:00:25.680889+00:00 **Finished:** 2026-07-23T11:58:04.895346+00:00

**Summary:** data_pipeline_e2e_check_is pipeline-e2e-check 2026-07-13: total=14 passed=11 failed=3 ambiguous=0 skipped=0

## Results

| Shard                    | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Reason                                                                                                                                                                                      |
| ------------------------ | ----- | ------ | -------------- | ---- | ------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TRADFI/NASDAQ/2026-07-13 | force | passed | not_applicable | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/NASDAQ/2026-07-13 | skip  | passed | genuine        | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/NYSE/2026-07-13   | force | passed | not_applicable | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/NYSE/2026-07-13   | skip  | passed | genuine        | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/CME/2026-07-13    | force | passed | not_applicable | 0    | 2       | captured        | ok                                                                                                                                                                                          |
| TRADFI/CME/2026-07-13    | skip  | passed | genuine        | 0    | 2       | captured        | ok                                                                                                                                                                                          |
| TRADFI/ICE/2026-07-13    | force | passed | not_applicable | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/ICE/2026-07-13    | skip  | passed | genuine        | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/CBOE/2026-07-13   | force | passed | not_applicable | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/CBOE/2026-07-13   | skip  | passed | genuine        | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/KRX/2026-07-13    | force | passed | not_applicable | 0    | 1       | captured        | ok                                                                                                                                                                                          |
| TRADFI/KRX/2026-07-13    | skip  | failed | not_applicable | -    | 0       | -               | vm_run_not_successful:vm_self_deleted_no_exit_status                                                                                                                                        |
| TRADFI/FX/2026-07-13     | force | failed | not_applicable | 0    | 0       | empty_confirmed | no_parquet_at:gs://instruments-store-tradfi-test-central-element-323112/instrument_availability/by_date/day=2026-07-13/pipeline_mode=batch_instruments_service/asset_group=tradfi/venue=FX/ |
| TRADFI/FX/2026-07-13     | skip  | failed | not_applicable | 0    | 0       | empty_confirmed | no_parquet_at:gs://instruments-store-tradfi-test-central-element-323112/instrument_availability/by_date/day=2026-07-13/pipeline_mode=batch_instruments_service/asset_group=tradfi/venue=FX/ |

## Bucket paths (where each write/read actually landed)

| Shard                    | Leg   | Parquet bucket                                         | Manifest bucket                                        | Same bucket? |
| ------------------------ | ----- | ------------------------------------------------------ | ------------------------------------------------------ | ------------ |
| TRADFI/NASDAQ/2026-07-13 | force | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/NASDAQ/2026-07-13 | skip  | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/NYSE/2026-07-13   | force | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/NYSE/2026-07-13   | skip  | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/CME/2026-07-13    | force | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/CME/2026-07-13    | skip  | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/ICE/2026-07-13    | force | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/ICE/2026-07-13    | skip  | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/CBOE/2026-07-13   | force | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/CBOE/2026-07-13   | skip  | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/KRX/2026-07-13    | force | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/KRX/2026-07-13    | skip  | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/FX/2026-07-13     | force | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |
| TRADFI/FX/2026-07-13     | skip  | `instruments-store-tradfi-test-central-element-323112` | `instruments-store-tradfi-test-central-element-323112` | yes          |

## Failed cells

| Shard                 | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Reason                                                                                                                                                                                      |
| --------------------- | ----- | ------ | -------------- | ---- | ------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TRADFI/KRX/2026-07-13 | skip  | failed | not_applicable | -    | 0       | -               | vm_run_not_successful:vm_self_deleted_no_exit_status                                                                                                                                        |
| TRADFI/FX/2026-07-13  | force | failed | not_applicable | 0    | 0       | empty_confirmed | no_parquet_at:gs://instruments-store-tradfi-test-central-element-323112/instrument_availability/by_date/day=2026-07-13/pipeline_mode=batch_instruments_service/asset_group=tradfi/venue=FX/ |
| TRADFI/FX/2026-07-13  | skip  | failed | not_applicable | 0    | 0       | empty_confirmed | no_parquet_at:gs://instruments-store-tradfi-test-central-element-323112/instrument_availability/by_date/day=2026-07-13/pipeline_mode=batch_instruments_service/asset_group=tradfi/venue=FX/ |
