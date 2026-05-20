# A2 — expected_coverage() dump summary

_Generated: 2026-05-20T12:22:37.866574+00:00_

Window: 2020-01-01 → 2026-05-20

Total rows: 429,088

Output: `plans/audit/results/expected_coverage_dump_2026_05_20.parquet` (0.56 MiB)

## State breakdown

| State | Rows | % |
|---|---:|---:|
| `SHOULD_HAVE_DATA` | 298,143 | 69.48% |
| `NOT_YET_LIVE` | 117,557 | 27.40% |
| `EXPECTED_EMPTY` | 13,388 | 3.12% |

## Reason breakdown (EXPECTED_EMPTY + NOT_YET_LIVE cells)

| Reason | Rows |
|---|---:|
| `EXPECTED_PRE_VENUE_LAUNCH` | 86,475 |
| `EXPECTED_PRE_GENESIS_CHAIN` | 31,082 |
| `EXPECTED_WEEKEND` | 7,992 |
| `EXPECTED_DEPRECATED_DATA_TYPE` | 4,664 |
| `EXPECTED_HOLIDAY` | 732 |
| `EXPECTED_PARTIAL_HALF_DAY` | 120 |

## Per-asset-group breakdown

| asset_group | total cells | SHOULD_HAVE_DATA | EXPECTED_EMPTY |
|---|---:|---:|---:|
| defi | 291,500 | 182,055 | 4,664 |
| cefi | 79,288 | 67,332 | 0 |
| tradfi | 27,984 | 19,260 | 8,724 |
| sports | 25,652 | 25,652 | 0 |
| prediction | 4,664 | 3,844 | 0 |

## Notes

- No per-symbol axis in v1 (operator decision 2026-05-20). A3 introduces per-symbol comparison by reading manifest rows directly.
- Sports off-season calendars are not yet encoded in UAC; in-scope sports cells default to `SHOULD_HAVE_DATA`. Tracked in `expected_coverage_calendar_decisions_2026_05_20.md`.
- DeFi protocol pause windows are not yet encoded; in-scope DeFi cells default to `SHOULD_HAVE_DATA` once chain genesis + venue launch pass.
- `SourceCapability.coverage_start` (per-data_type) was promoted by slot-3 plan `uac_source_capability_metadata_promotion_2026_05_20.md` but a lookup index integration is pending (slot-3 Phase 4).
