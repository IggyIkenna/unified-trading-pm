---
doc_type: audit-result
title: A4 v2 — Per-VM shard schema_version compliance
summary:
status:
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-20"
audited_scope:
date:
auditor:
parent_epic:
severity:
resulting_plan:
lib_version:
doc_versions_checked:
---

# A4 v2 — Per-VM shard schema_version compliance

_Generated: 2026-05-20T13:14:13.522872+00:00_

Total per-VM shards inspected: 3895

## Per-bucket aggregates

| bucket                                                | shards | total rows | v8 rows |  v8 % |   v<8 rows | NULL rows |
| ----------------------------------------------------- | -----: | ---------: | ------: | ----: | ---------: | --------: |
| `instruments-store-cefi-prd-central-element-323112`   |    512 |     39,962 |       0 | 0.00% |     39,962 |         0 |
| `instruments-store-defi-prd-central-element-323112`   |     37 |     70,474 |       0 | 0.00% |     70,474 |         0 |
| `instruments-store-pred-prd-central-element-323112`   |    151 |      4,001 |       0 | 0.00% |      4,001 |         0 |
| `instruments-store-sports-prd-central-element-323112` |     77 | 10,722,574 |       0 | 0.00% | 10,709,398 |    13,176 |
| `instruments-store-tradfi-prd-central-element-323112` |     46 |     20,205 |       0 | 0.00% |     20,205 |         0 |
| `market-data-tick-cefi-prd-central-element-323112`    |  1,584 |  5,259,458 |       0 | 0.00% |  5,259,458 |         0 |
| `market-data-tick-defi-prd-central-element-323112`    |      8 |  1,895,926 |       0 | 0.00% |    609,666 | 1,286,260 |
| `market-data-tick-pred-prd-central-element-323112`    |      9 |     16,862 |       0 | 0.00% |     14,582 |     2,280 |
| `market-data-tick-sports-prd-central-element-323112`  |     23 |    169,197 |       0 | 0.00% |    169,197 |         0 |
| `market-data-tick-tradfi-prd-central-element-323112`  |  1,448 |    194,779 |       0 | 0.00% |    159,746 |    35,033 |

## Per-VM shards at v<8 OR with NULL schema_version (review-blocking)

Total problematic shards: **3894**

| asset_group | bucket               | shard                                                                 |     total |       v<8 |      NULL | versions |
| ----------- | -------------------- | --------------------------------------------------------------------- | --------: | --------: | --------: | -------- |
| sports      | `instruments-sports` | `_legacy_seed.20260506-120021.bak.parquet`                            | 1,868,303 | 1,868,303 |         0 | 2,4,5,6  |
| sports      | `instruments-sports` | `blank-reason-recon-sports-20260507-175543.parquet`                   | 1,868,285 | 1,868,285 |         0 | 5,6,7    |
| sports      | `instruments-sports` | `_legacy_seed.parquet`                                                | 1,812,693 | 1,812,693 |         0 | 2,4,5,6  |
| defi        | `market-defi`        | `expected-universe-enum-defi-20260507-155353.parquet`                 | 1,286,260 |         0 | 1,286,260 | (empty)  |
| cefi        | `market-cefi`        | `blank-reason-recon-cefi-20260507-173136.parquet`                     | 1,238,229 | 1,238,229 |         0 | 5,6,7    |
| cefi        | `market-cefi`        | `local-99178-edc2.parquet`                                            |   983,904 |   983,904 |         0 | 6        |
| sports      | `instruments-sports` | `af-backfill-test-20260501-095.20260506-120021.bak.parquet`           |   574,599 |   574,599 |         0 | 6        |
| sports      | `instruments-sports` | `af-backfill-test-20260501-095.parquet`                               |   462,082 |   462,082 |         0 | 6        |
| cefi        | `market-cefi`        | `reconcile-tardis-thirdkey-drift-20260507-174536.parquet`             |   451,799 |   451,799 |         0 | 6,7      |
| sports      | `instruments-sports` | `af-backfill-20260429-105528.20260506-120021.bak.parquet`             |   417,838 |   417,838 |         0 | 6        |
| cefi        | `market-cefi`        | `_legacy_seed.parquet`                                                |   352,028 |   352,028 |         0 | 4,5,6    |
| sports      | `instruments-sports` | `af-backfill-20260429-105528.parquet`                                 |   340,989 |   340,989 |         0 | 6        |
| sports      | `instruments-sports` | `af-backfill-20260507-033214.parquet`                                 |   310,494 |   310,494 |         0 | 7        |
| defi        | `market-defi`        | `local-10889-bd08.parquet`                                            |   307,341 |   307,341 |         0 | 6        |
| sports      | `instruments-sports` | `manifest-recon-from-per-league-parquets.20260506-120021.bak.parquet` |   292,127 |   292,127 |         0 | 5        |
| defi        | `market-defi`        | `local-29870-9b39.parquet`                                            |   275,000 |   275,000 |         0 | 6        |
| sports      | `instruments-sports` | `manifest-recon-from-per-league-parquets.parquet`                     |   203,809 |   203,809 |         0 | 5        |
| sports      | `instruments-sports` | `af-backfill-20260505-105528.20260506-120021.bak.parquet`             |   190,415 |   190,415 |         0 | 6        |
| sports      | `instruments-sports` | `flip-phantom-corrective-20260506-114110.20260506-120021.bak.parquet` |   176,021 |   176,021 |         0 | 5,6      |
| sports      | `instruments-sports` | `af-backfill-20260507-002914.parquet`                                 |   148,770 |   148,770 |         0 | 7        |
| sports      | `instruments-sports` | `fs-backfill-20260507-010724.parquet`                                 |   147,164 |   147,164 |         0 | 7        |
| sports      | `instruments-sports` | `af-backfill-20260505-105528.parquet`                                 |   134,212 |   134,212 |         0 | 6        |
| sports      | `instruments-sports` | `manifest-canonicalize-league-ids.20260506-120021.bak.parquet`        |   108,969 |   108,969 |         0 | 5,6      |
| sports      | `instruments-sports` | `local-55602-8d93.parquet`                                            |   104,113 |   104,113 |         0 | 6        |
| sports      | `instruments-sports` | `weather-backfill-20260429-105525.parquet`                            |   100,542 |   100,542 |         0 | 6        |
| sports      | `instruments-sports` | `manifest-canonicalize-league-ids.parquet`                            |   100,386 |   100,386 |         0 | 6        |
| sports      | `instruments-sports` | `af-backfill-20260504-183526.20260506-120021.bak.parquet`             |    98,951 |    98,951 |         0 | 6        |
| sports      | `instruments-sports` | `weather-backfill-20260504-160617.parquet`                            |    86,418 |    86,418 |         0 | 6        |
| sports      | `instruments-sports` | `weather-backfill-20260504-225316.parquet`                            |    81,669 |    81,669 |         0 | 6        |
| sports      | `instruments-sports` | `sfi-backfill-20260501-102703.parquet`                                |    76,063 |    76,063 |         0 | 6        |
| sports      | `instruments-sports` | `af-backfill-20260504-232814.20260506-120021.bak.parquet`             |    75,973 |    75,973 |         0 | 6        |
| sports      | `instruments-sports` | `fs-backfill-20260501-014139.parquet`                                 |    75,786 |    75,786 |         0 | 6        |
| sports      | `instruments-sports` | `fs-backfill-20260501-102703.parquet`                                 |    75,706 |    75,706 |         0 | 6        |
| sports      | `instruments-sports` | `af-backfill-20260504-183526.parquet`                                 |    75,382 |    75,382 |         0 | 6        |
| sports      | `instruments-sports` | `weather-backfill-20260504-183642.parquet`                            |    71,568 |    71,568 |         0 | 6        |
| sports      | `instruments-sports` | `weather-backfill-20260507-010923.parquet`                            |    71,389 |    71,389 |         0 | 7        |
| sports      | `instruments-sports` | `sfi-backfill-20260507-010938.parquet`                                |    71,368 |    71,368 |         0 | 7        |
| defi        | `instruments-defi`   | `_legacy_seed.parquet`                                                |    69,674 |    69,674 |         0 | 4        |
| sports      | `instruments-sports` | `recover-fixtures-flip-20260506-165630.parquet`                       |    69,149 |    69,149 |         0 | 5,6      |
| sports      | `instruments-sports` | `local-67763-68a4.parquet`                                            |    65,294 |    65,294 |         0 | 6        |
| sports      | `instruments-sports` | `af-backfill-20260504-232814.parquet`                                 |    54,369 |    54,369 |         0 | 6        |
| tradfi      | `market-tradfi`      | `expected-universe-enum-tradfi-20260507-154607.parquet`               |    35,033 |         0 |    35,033 | (empty)  |
| sports      | `instruments-sports` | `fixtures-recovery-20260506-165630.parquet`                           |    34,583 |    34,583 |         0 | 6        |
| sports      | `instruments-sports` | `fill-missing-player-stats-20260506-082808.parquet`                   |    27,057 |    27,057 |         0 | 6        |
| cefi        | `market-cefi`        | `cefi-bitget-futures-2025-light-20260506-180338.parquet`              |    27,010 |    27,010 |         0 | 6        |
| sports      | `instruments-sports` | `fs-backfill-20260501-154804.parquet`                                 |    24,703 |    24,703 |         0 | 6        |
| sports      | `instruments-sports` | `fs-backfill-20260429-105528.parquet`                                 |    23,196 |    23,196 |         0 | 6        |
| sports      | `instruments-sports` | `af-backfill-20260501-012419.20260506-120021.bak.parquet`             |    23,130 |    23,130 |         0 | 6        |
| sports      | `instruments-sports` | `fs-backfill-20260501-165342.parquet`                                 |    22,015 |    22,015 |         0 | 6        |
| cefi        | `instruments-cefi`   | `_legacy_seed.parquet`                                                |    21,952 |    21,952 |         0 | 4        |

_(showing first 50 of 3894 problematic shards — see CSV for full list)_

## Composition with A4 v1 (master availability_index)

Master availability_index has 0% v8 rows workspace-wide (A4 v1). If per-VM shards are also v<8, the consolidator
preserves the source version (correct behavior). If per-VM shards ARE at v8 but master isn't, the consolidator should be
regenerating master from per-VM shards — gap.

Compare aggregates above to A4 v1 numbers to identify drift between the two paths.
