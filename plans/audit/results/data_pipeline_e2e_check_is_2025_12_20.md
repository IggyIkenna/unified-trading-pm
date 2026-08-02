---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_is (2025-12-20)"
summary: "data_pipeline_e2e_check_is pipeline-e2e-check 2025-12-20: total=21 passed=12 failed=9 ambiguous=0 skipped=0"
status: partial
nature: record
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_is]
related: []
created: 2026-08-02
audited_scope:
  "data_pipeline_e2e_check_is real-VM force/skip/live pipeline check for day=2025-12-20, legs=force,skip,live"
date: 2026-08-02
auditor: data_pipeline_e2e_check_is (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_is
run_date: 2025-12-20
generated_at: 2026-08-02T15:35:00.281515+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_is (2025-12-20)

**Legs:** force, skip, live **Started:** 2026-08-02T13:33:14.829813+00:00 **Finished:** 2026-08-02T15:35:00.061386+00:00

**Summary:** data_pipeline_e2e_check_is pipeline-e2e-check 2025-12-20: total=21 passed=12 failed=9 ambiguous=0 skipped=0

## Results

| Shard                                  | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Content     | Reason                                                                                                                                                                                                                                                           |
| -------------------------------------- | ----- | ------ | -------------- | ---- | ------- | --------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SPORTS/API_FOOTBALL/2025-12-20         | force | passed | not_applicable | 0    | 852     | captured        | not_checked | ok                                                                                                                                                                                                                                                               |
| SPORTS/API_FOOTBALL/2025-12-20         | skip  | failed | not_applicable | 0    | 852     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/API_FOOTBALL/2025-12-20         | live  | passed | not_applicable | 0    | 852     | captured        | not_checked | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                                        |
| SPORTS/OPEN_METEO/2025-12-20           | force | passed | not_applicable | 0    | 852     | captured        | not_checked | ok                                                                                                                                                                                                                                                               |
| SPORTS/OPEN_METEO/2025-12-20           | skip  | failed | not_applicable | -    | 0       | -               | not_checked | vm_run_not_successful:launcher_script_nonzero_rc=1                                                                                                                                                                                                               |
| SPORTS/OPEN_METEO/2025-12-20           | live  | passed | not_applicable | 0    | 852     | captured        | not_checked | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                                        |
| SPORTS/TRANSFERMARKT/2025-12-20        | force | passed | not_applicable | 0    | 852     | captured        | not_checked | ok                                                                                                                                                                                                                                                               |
| SPORTS/TRANSFERMARKT/2025-12-20        | skip  | failed | not_applicable | 0    | 852     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/TRANSFERMARKT/2025-12-20        | live  | passed | not_applicable | 0    | 852     | captured        | not_checked | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                                        |
| SPORTS/SOCCER_FOOTBALL_INFO/2025-12-20 | force | passed | not_applicable | 0    | 852     | captured        | not_checked | ok                                                                                                                                                                                                                                                               |
| SPORTS/SOCCER_FOOTBALL_INFO/2025-12-20 | skip  | failed | not_applicable | 0    | 852     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/SOCCER_FOOTBALL_INFO/2025-12-20 | live  | passed | not_applicable | 0    | 852     | captured        | not_checked | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                                        |
| SPORTS/UNDERSTAT/2025-12-20            | force | passed | not_applicable | 0    | 852     | captured        | not_checked | ok                                                                                                                                                                                                                                                               |
| SPORTS/UNDERSTAT/2025-12-20            | skip  | failed | not_applicable | 0    | 852     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/UNDERSTAT/2025-12-20            | live  | passed | not_applicable | 0    | 852     | captured        | not_checked | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                                        |
| SPORTS/FOOTYSTATS/2025-12-20           | force | passed | not_applicable | 0    | 888     | captured        | not_checked | ok                                                                                                                                                                                                                                                               |
| SPORTS/FOOTYSTATS/2025-12-20           | skip  | failed | not_applicable | 0    | 888     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/FOOTYSTATS/2025-12-20           | live  | passed | not_applicable | 0    | 888     | captured        | not_checked | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                                        |
| SPORTS/BETFAIR/2025-12-20              | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_parquet_at:gs://instruments-store-sports-test-central-element-323112/instrument_availability/by_date/day=2025-12-20/pipeline_mode=batch_instruments_service/asset_group=sports/venue=BETFAIR/; manifest_status_invalid:no_matching_row                        |
| SPORTS/BETFAIR/2025-12-20              | skip  | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_parquet_at:gs://instruments-store-sports-test-central-element-323112/instrument_availability/by_date/day=2025-12-20/pipeline_mode=batch_instruments_service/asset_group=sports/venue=BETFAIR/; manifest_status_invalid:no_matching_row; skip_signal_not_found |
| SPORTS/BETFAIR/2025-12-20              | live  | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_parquet_at:gs://instruments-store-sports-test-central-element-323112/instrument_availability/by_date/day=2025-12-20/pipeline_mode=batch_instruments_service/asset_group=sports/venue=BETFAIR/; manifest_status_invalid:no_matching_row                        |

## Bucket paths (where each write/read actually landed)

| Shard                                  | Leg   | Parquet bucket                                         | Manifest bucket                                        | Same bucket? |
| -------------------------------------- | ----- | ------------------------------------------------------ | ------------------------------------------------------ | ------------ |
| SPORTS/API_FOOTBALL/2025-12-20         | force | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/API_FOOTBALL/2025-12-20         | skip  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/API_FOOTBALL/2025-12-20         | live  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/OPEN_METEO/2025-12-20           | force | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/OPEN_METEO/2025-12-20           | skip  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/OPEN_METEO/2025-12-20           | live  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/TRANSFERMARKT/2025-12-20        | force | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/TRANSFERMARKT/2025-12-20        | skip  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/TRANSFERMARKT/2025-12-20        | live  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/SOCCER_FOOTBALL_INFO/2025-12-20 | force | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/SOCCER_FOOTBALL_INFO/2025-12-20 | skip  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/SOCCER_FOOTBALL_INFO/2025-12-20 | live  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/UNDERSTAT/2025-12-20            | force | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/UNDERSTAT/2025-12-20            | skip  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/UNDERSTAT/2025-12-20            | live  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/FOOTYSTATS/2025-12-20           | force | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/FOOTYSTATS/2025-12-20           | skip  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/FOOTYSTATS/2025-12-20           | live  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/BETFAIR/2025-12-20              | force | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/BETFAIR/2025-12-20              | skip  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |
| SPORTS/BETFAIR/2025-12-20              | live  | `instruments-store-sports-test-central-element-323112` | `instruments-store-sports-test-central-element-323112` | yes          |

## Failed cells

| Shard                                  | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Content     | Reason                                                                                                                                                                                                                                                           |
| -------------------------------------- | ----- | ------ | -------------- | ---- | ------- | --------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SPORTS/API_FOOTBALL/2025-12-20         | skip  | failed | not_applicable | 0    | 852     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/OPEN_METEO/2025-12-20           | skip  | failed | not_applicable | -    | 0       | -               | not_checked | vm_run_not_successful:launcher_script_nonzero_rc=1                                                                                                                                                                                                               |
| SPORTS/TRANSFERMARKT/2025-12-20        | skip  | failed | not_applicable | 0    | 852     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/SOCCER_FOOTBALL_INFO/2025-12-20 | skip  | failed | not_applicable | 0    | 852     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/UNDERSTAT/2025-12-20            | skip  | failed | not_applicable | 0    | 852     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/FOOTYSTATS/2025-12-20           | skip  | failed | not_applicable | 0    | 888     | captured        | not_checked | skip_signal_not_found                                                                                                                                                                                                                                            |
| SPORTS/BETFAIR/2025-12-20              | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_parquet_at:gs://instruments-store-sports-test-central-element-323112/instrument_availability/by_date/day=2025-12-20/pipeline_mode=batch_instruments_service/asset_group=sports/venue=BETFAIR/; manifest_status_invalid:no_matching_row                        |
| SPORTS/BETFAIR/2025-12-20              | skip  | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_parquet_at:gs://instruments-store-sports-test-central-element-323112/instrument_availability/by_date/day=2025-12-20/pipeline_mode=batch_instruments_service/asset_group=sports/venue=BETFAIR/; manifest_status_invalid:no_matching_row; skip_signal_not_found |
| SPORTS/BETFAIR/2025-12-20              | live  | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_parquet_at:gs://instruments-store-sports-test-central-element-323112/instrument_availability/by_date/day=2025-12-20/pipeline_mode=batch_instruments_service/asset_group=sports/venue=BETFAIR/; manifest_status_invalid:no_matching_row                        |
