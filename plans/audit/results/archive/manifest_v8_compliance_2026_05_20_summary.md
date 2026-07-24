---
doc_type: audit-result
title: A4 — Manifest v8 deep compliance summary
summary:
  A4 deep manifest v8 compliance scan — 0% v8 across all 10 MTDS+IS master indexes (defi has 1.29M NULL rows); code side
  scanned 235 consumer files, 3 with hardcoded v<8 (rebuild_sports_manifest.py, UAC manifest_schema.py, UTL
  manifest_writer.py from_dict default=1) + 25 legacy-fallback files needing sunset dates.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [audit, manifest, data-correctness, migration, data-status, quality-gates]
related:
  [
    /plans/audit/results/archive/manifest_v8_compliance_2026_05_20.md,
    /plans/audit/results/archive/manifest_v8_per_vm_shards_2026_05_20_summary.md,
  ]
created: 2026-05-20
audited_scope:
  10 MTDS+IS master _index/availability_index.parquet schema_version distributions + 235 manifest-consumer code files
  (hardcoded v<8 constants, v8 indicators, legacy-fallback patterns)
date: 2026-05-20
auditor: semver
parent_epic: manifest_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# A4 — Manifest v8 deep compliance summary

_Generated: 2026-05-20T10:30:27.552858+00:00_

## Data side — `_index/availability_index.parquet` `schema_version` distribution per bucket

| asset_group | bucket                                              | schema_version |      rows |
| ----------- | --------------------------------------------------- | -------------: | --------: |
| cefi        | instruments-store-cefi-prd-central-element-323112   |              4 |    12,361 |
| cefi        | instruments-store-cefi-prd-central-element-323112   |              6 |    18,021 |
| cefi        | market-data-tick-cefi-prd-central-element-323112    |              4 |    16,224 |
| cefi        | market-data-tick-cefi-prd-central-element-323112    |              5 |    30,704 |
| cefi        | market-data-tick-cefi-prd-central-element-323112    |              6 | 2,246,785 |
| cefi        | market-data-tick-cefi-prd-central-element-323112    |              7 |   339,218 |
| defi        | instruments-store-defi-prd-central-element-323112   |              4 |    69,630 |
| defi        | instruments-store-defi-prd-central-element-323112   |              6 |    58,266 |
| defi        | market-data-tick-defi-prd-central-element-323112    |              6 |   308,330 |
| defi        | market-data-tick-defi-prd-central-element-323112    |              7 |    11,600 |
| defi        | market-data-tick-defi-prd-central-element-323112    |           <NA> | 1,286,260 |
| prediction  | instruments-store-pred-prd-central-element-323112   |              4 |     3,145 |
| prediction  | instruments-store-pred-prd-central-element-323112   |              6 |       795 |
| prediction  | market-data-tick-pred-prd-central-element-323112    |              4 |    14,296 |
| prediction  | market-data-tick-pred-prd-central-element-323112    |              5 |         2 |
| prediction  | market-data-tick-pred-prd-central-element-323112    |              6 |       234 |
| prediction  | market-data-tick-pred-prd-central-element-323112    |           <NA> |     2,280 |
| sports      | instruments-store-sports-prd-central-element-323112 |              2 |       434 |
| sports      | instruments-store-sports-prd-central-element-323112 |              4 |    11,752 |
| sports      | instruments-store-sports-prd-central-element-323112 |              5 |   481,109 |
| sports      | instruments-store-sports-prd-central-element-323112 |              6 | 1,409,896 |
| sports      | instruments-store-sports-prd-central-element-323112 |              7 |   759,329 |
| sports      | instruments-store-sports-prd-central-element-323112 |           <NA> |    13,176 |
| sports      | market-data-tick-sports-prd-central-element-323112  |              4 |    17,288 |
| sports      | market-data-tick-sports-prd-central-element-323112  |              6 |   140,212 |
| tradfi      | instruments-store-tradfi-prd-central-element-323112 |              4 |    11,301 |
| tradfi      | instruments-store-tradfi-prd-central-element-323112 |              6 |     8,897 |
| tradfi      | market-data-tick-tradfi-prd-central-element-323112  |              4 |    16,656 |
| tradfi      | market-data-tick-tradfi-prd-central-element-323112  |              6 |    89,272 |
| tradfi      | market-data-tick-tradfi-prd-central-element-323112  |              7 |       440 |
| tradfi      | market-data-tick-tradfi-prd-central-element-323112  |           <NA> |    35,033 |

## Data side — per-asset-group v<8 row counts (review-blocking)

| asset_group | total rows | v8 rows |  v<8 rows | NULL rows |  v8 % |
| ----------- | ---------: | ------: | --------: | --------: | ----: |
| cefi        |  2,663,313 |       0 | 2,663,313 |         0 | 0.00% |
| defi        |  1,734,086 |       0 |   447,826 |         0 | 0.00% |
| tradfi      |    161,599 |       0 |   126,566 |         0 | 0.00% |
| sports      |  2,833,196 |       0 | 2,820,020 |         0 | 0.00% |
| prediction  |     20,752 |       0 |    18,472 |         0 | 0.00% |

## Code side — files consuming manifest rows

- Total consumer files: 235
- Files with hardcoded `schema_version` < 8: **3** (review-blocking)
- Files with explicit v8 indicator: 27
- Files with legacy-fallback pattern: 25

### Files with hardcoded v<8 schema_version (REVIEW-BLOCKING)

| Repo                    | File                                                              | v<8 count | legacy_fallback count |
| ----------------------- | ----------------------------------------------------------------- | --------: | --------------------: |
| deployment-service      | `scripts/rebuild_sports_manifest.py`                              |         1 |                     0 |
| unified-api-contracts   | `unified_api_contracts/canonical/crosscutting/manifest_schema.py` |         1 |                     1 |
| unified-trading-library | `unified_trading_library/manifest_writer.py`                      |         1 |                     2 |

### Files with legacy-fallback patterns (review per-file for sunset date)

| Repo                           | File                                                               | legacy_fallback count |
| ------------------------------ | ------------------------------------------------------------------ | --------------------: |
| deployment-api                 | `tests/unit/test_data_status_service.py`                           |                     3 |
| deployment-api                 | `deployment_api/services/data_status_drilldown.py`                 |                     1 |
| deployment-api                 | `deployment_api/services/data_status_service.py`                   |                     3 |
| deployment-service             | `scripts/vm/vm_zombie_watchdog.py`                                 |                     1 |
| instruments-service            | `scripts/reconcile_attempted_failed_to_captured_2026_05_13.py`     |                     1 |
| instruments-service            | `scripts/enumerate_expected_universe.py`                           |                     1 |
| instruments-service            | `scripts/reconcile_blank_error_reason_rows.py`                     |                     1 |
| instruments-service            | `scripts/migrate_defi_legacy_venue_chain.py`                       |                     1 |
| instruments-service            | `scripts/migrate_solana_bare_name_venues.py`                       |                     1 |
| instruments-service            | `scripts/reconcile_phantom_manifest_rows_all.py`                   |                     1 |
| market-data-processing-service | `scripts/reprocess_sports_odds.py`                                 |                     2 |
| market-tick-data-service       | `market_tick_data_service/scripts/migrate_solana_defi_v4_to_v8.py` |                     2 |
| market-tick-data-service       | `market_tick_data_service/engine/orchestrator.py`                  |                     2 |
| market-tick-data-service       | `tests/unit/scripts/test_migrate_defi_canonical.py`                |                     3 |
| unified-api-contracts          | `unified_api_contracts/canonical/crosscutting/manifest_schema.py`  |                     1 |
| unified-api-contracts          | `scripts/generate_instrument_catalogue.py`                         |                     1 |
| unified-trading-library        | `tests/unit/test_manifest_writer_v6.py`                            |                     4 |
| unified-trading-library        | `tests/unit/test_manifest_migrations_v7_to_v8.py`                  |                    17 |
| unified-trading-library        | `tests/unit/test_manifest_writer_v7.py`                            |                     7 |
| unified-trading-library        | `tests/unit/test_manifest_writer_capture_status.py`                |                     3 |
| unified-trading-library        | `unified_trading_library/manifest_reader_fallback.py`              |                     3 |
| unified-trading-library        | `unified_trading_library/manifest_consolidator.py`                 |                     1 |
| unified-trading-library        | `unified_trading_library/manifest_writer.py`                       |                     2 |
| unified-trading-library        | `unified_trading_library/legacy_reason_classifier.py`              |                     1 |
| unified-trading-library        | `unified_trading_library/manifest_migrations/v7_to_v8.py`          |                    12 |

## Next actions

- Any v<8 row at the data side requires backfill/migration before next bucket cutover (per single-walk discipline, must
  bundle into Phase 2 migration).
- Any v<8 hardcoded constant in code requires update + a QG check that raises on resurgence.
- Legacy-fallback patterns should be reviewed for sunset dates — temporary state per CLAUDE.md must have a named
  successor plan.
- Recommend new QG step: `scripts/quality_gates/check_manifest_schema_version_constants.py` that scans the workspace for
  any non-v8 manifest-schema constant.
