---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_is (2026-06-28)"
summary: "data_pipeline_e2e_check_is pipeline-e2e-check 2026-06-28: total=14 passed=11 failed=3 ambiguous=0 skipped=0"
status: partial
nature: record
asset_group: [prediction]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_is]
related: []
created: 2026-07-19
audited_scope:
  "data_pipeline_e2e_check_is real-VM force/skip/live pipeline check for day=2026-06-28, legs=force,skip,canonical"
date: 2026-07-19
auditor: data_pipeline_e2e_check_is (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_is
run_date: 2026-06-28
generated_at: 2026-07-19T13:16:44.908721+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_is (2026-06-28)

**Legs:** force, skip, canonical **Started:** 2026-07-19T12:52:22.023107+00:00 **Finished:**
2026-07-19T13:16:44.903330+00:00

**Summary:** data_pipeline_e2e_check_is pipeline-e2e-check 2026-06-28: total=14 passed=11 failed=3 ambiguous=0 skipped=0

## Results

| Shard                                                                | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                         |
| -------------------------------------------------------------------- | --------- | ------ | -------------- | ---- | ------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PREDICTION/POLYMARKET/2026-06-28                                     | force     | failed | not_applicable | -    | 0       | -        | vm_run_not_successful:vm_self_deleted_no_exit_status                                                                                                           |
| PREDICTION/POLYMARKET/prediction_canonical_question_group/2026-06-28 | force     | passed | not_applicable | -    | 0       | -        | cqg_bundle_present_and_canonical                                                                                                                               |
| PREDICTION/POLYMARKET/market_lifecycle/2026-06-28                    | force     | passed | not_applicable | -    | 57      | -        | market_lifecycle_present (57 object(s))                                                                                                                        |
| PREDICTION/POLYMARKET/2026-06-28                                     | skip      | passed | genuine        | 0    | 57      | captured | ok                                                                                                                                                             |
| PREDICTION/POLYMARKET/prediction_canonical_question_group/2026-06-28 | skip      | passed | genuine        | -    | 0       | -        | cqg_bundle_present_and_canonical                                                                                                                               |
| PREDICTION/POLYMARKET/market_lifecycle/2026-06-28                    | skip      | passed | genuine        | -    | 57      | -        | market_lifecycle_present (57 object(s))                                                                                                                        |
| PREDICTION/POLYMARKET/2026-06-28                                     | canonical | failed | not_applicable | -    | 0       | -        | canonical_no_instruments_parquet_at:gs://instruments-store-pred-test-central-element-323112/instrument_availability/by_date/ (day=2026-06-28 venue=POLYMARKET) |
| PREDICTION/KALSHI/2026-06-28                                         | force     | passed | not_applicable | 0    | 1       | captured | ok                                                                                                                                                             |
| PREDICTION/KALSHI/prediction_canonical_question_group/2026-06-28     | force     | passed | not_applicable | -    | 0       | -        | cqg_bundle_present_and_canonical                                                                                                                               |
| PREDICTION/KALSHI/market_lifecycle/2026-06-28                        | force     | passed | not_applicable | -    | 1       | -        | market_lifecycle_present (1 object(s))                                                                                                                         |
| PREDICTION/KALSHI/2026-06-28                                         | skip      | passed | genuine        | 0    | 1       | captured | ok                                                                                                                                                             |
| PREDICTION/KALSHI/prediction_canonical_question_group/2026-06-28     | skip      | passed | genuine        | -    | 0       | -        | cqg_bundle_present_and_canonical                                                                                                                               |
| PREDICTION/KALSHI/market_lifecycle/2026-06-28                        | skip      | passed | genuine        | -    | 1       | -        | market_lifecycle_present (1 object(s))                                                                                                                         |
| PREDICTION/KALSHI/2026-06-28                                         | canonical | failed | not_applicable | -    | 0       | -        | canonical_no_instruments_parquet_at:gs://instruments-store-pred-test-central-element-323112/instrument_availability/by_date/ (day=2026-06-28 venue=KALSHI)     |

## Bucket paths (where each write/read actually landed)

| Shard                                                                | Leg       | Parquet bucket                                       | Manifest bucket                                      | Same bucket? |
| -------------------------------------------------------------------- | --------- | ---------------------------------------------------- | ---------------------------------------------------- | ------------ |
| PREDICTION/POLYMARKET/2026-06-28                                     | force     | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/POLYMARKET/prediction_canonical_question_group/2026-06-28 | force     | `-`                                                  | `instruments-store-pred-test-central-element-323112` | -            |
| PREDICTION/POLYMARKET/market_lifecycle/2026-06-28                    | force     | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/POLYMARKET/2026-06-28                                     | skip      | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/POLYMARKET/prediction_canonical_question_group/2026-06-28 | skip      | `-`                                                  | `instruments-store-pred-test-central-element-323112` | -            |
| PREDICTION/POLYMARKET/market_lifecycle/2026-06-28                    | skip      | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/POLYMARKET/2026-06-28                                     | canonical | `-`                                                  | `instruments-store-pred-test-central-element-323112` | -            |
| PREDICTION/KALSHI/2026-06-28                                         | force     | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/KALSHI/prediction_canonical_question_group/2026-06-28     | force     | `-`                                                  | `instruments-store-pred-test-central-element-323112` | -            |
| PREDICTION/KALSHI/market_lifecycle/2026-06-28                        | force     | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/KALSHI/2026-06-28                                         | skip      | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/KALSHI/prediction_canonical_question_group/2026-06-28     | skip      | `-`                                                  | `instruments-store-pred-test-central-element-323112` | -            |
| PREDICTION/KALSHI/market_lifecycle/2026-06-28                        | skip      | `instruments-store-pred-test-central-element-323112` | `instruments-store-pred-test-central-element-323112` | yes          |
| PREDICTION/KALSHI/2026-06-28                                         | canonical | `-`                                                  | `instruments-store-pred-test-central-element-323112` | -            |

## Failed cells

| Shard                            | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                         |
| -------------------------------- | --------- | ------ | -------------- | ---- | ------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PREDICTION/POLYMARKET/2026-06-28 | force     | failed | not_applicable | -    | 0       | -        | vm_run_not_successful:vm_self_deleted_no_exit_status                                                                                                           |
| PREDICTION/POLYMARKET/2026-06-28 | canonical | failed | not_applicable | -    | 0       | -        | canonical_no_instruments_parquet_at:gs://instruments-store-pred-test-central-element-323112/instrument_availability/by_date/ (day=2026-06-28 venue=POLYMARKET) |
| PREDICTION/KALSHI/2026-06-28     | canonical | failed | not_applicable | -    | 0       | -        | canonical_no_instruments_parquet_at:gs://instruments-store-pred-test-central-element-323112/instrument_availability/by_date/ (day=2026-06-28 venue=KALSHI)     |
