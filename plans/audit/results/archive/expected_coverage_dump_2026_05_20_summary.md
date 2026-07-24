---
doc_type: audit-result
title: A2 — expected_coverage() dump summary
summary:
  A2 materialized expected_coverage() oracle dump over 2020-01-01→2026-05-20 (419,760 rows) — 68.62% SHOULD_HAVE_DATA /
  28.01% NOT_YET_LIVE / 3.37% EXPECTED_EMPTY; defi dominates (291,500 cells); no per-symbol axis in v1 and sports
  off-season / DeFi protocol pauses still default to SHOULD_HAVE_DATA.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [audit, honest-coverage, uac, data-quality, golden-window, defi]
related:
  [
    /plans/audit/results/archive/expected_coverage_calendar_decisions_2026_05_20.md,
    /plans/audit/results/archive/manifest_divergence_2026_05_20_summary.md,
  ]
created: 2026-05-20
audited_scope:
  Full materialization of the UAC expected_coverage() oracle for every in-scope (asset_group, source, data_type, date)
  cell over 2020-01-01→2026-05-20 — state + reason + per-asset-group breakdown
date: 2026-05-20
auditor: semver
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
---

# A2 — expected_coverage() dump summary

_Generated: 2026-05-21T07:04:55.039290+00:00_

Window: 2020-01-01 → 2026-05-20

Total rows: 419,760

Output: `plans/audit/results/expected_coverage_dump_2026_05_20.parquet` (0.55 MiB)

## State breakdown

| State              |    Rows |      % |
| ------------------ | ------: | -----: |
| `SHOULD_HAVE_DATA` | 288,055 | 68.62% |
| `NOT_YET_LIVE`     | 117,557 | 28.01% |
| `EXPECTED_EMPTY`   |  14,148 |  3.37% |

## Reason breakdown (EXPECTED_EMPTY + NOT_YET_LIVE cells)

| Reason                          |   Rows |
| ------------------------------- | -----: |
| `EXPECTED_PRE_VENUE_LAUNCH`     | 86,475 |
| `EXPECTED_PRE_GENESIS_CHAIN`    | 31,082 |
| `EXPECTED_WEEKEND`              |  7,992 |
| `EXPECTED_DEPRECATED_DATA_TYPE` |  4,664 |
| `EXPECTED_KNOWN_SOURCE_GAP`     |    760 |
| `EXPECTED_HOLIDAY`              |    732 |
| `EXPECTED_PARTIAL_HALF_DAY`     |    120 |

## Per-asset-group breakdown

| asset_group | total cells | SHOULD_HAVE_DATA | EXPECTED_EMPTY |
| ----------- | ----------: | ---------------: | -------------: |
| defi        |     291,500 |          182,055 |          4,664 |
| cefi        |      79,288 |           67,332 |              0 |
| tradfi      |      27,984 |           19,260 |          8,724 |
| sports      |      16,324 |           15,564 |            760 |
| prediction  |       4,664 |            3,844 |              0 |

## Notes

- No per-symbol axis in v1 (operator decision 2026-05-20). A3 introduces per-symbol comparison by reading manifest rows
  directly.
- Sports off-season calendars are not yet encoded in UAC; in-scope sports cells default to `SHOULD_HAVE_DATA`. Tracked
  in `expected_coverage_calendar_decisions_2026_05_20.md`.
- DeFi protocol pause windows are not yet encoded; in-scope DeFi cells default to `SHOULD_HAVE_DATA` once chain
  genesis + venue launch pass.
- `SourceCapability.coverage_start` (per-data_type) was promoted by slot-3 plan
  `uac_source_capability_metadata_promotion_2026_05_20.md` but a lookup index integration is pending (slot-3 Phase 4).
