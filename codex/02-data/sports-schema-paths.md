---
scope: [engineer, admin]
---

# Sports Schema Paths

## Overview

This document defines the canonical GCS path structures for sports features and sports odds data. Paths use Hive-style
partitioning (key=value) for BigQuery external table compatibility and efficient date-based queries.

---

## Canonical Paths

### sports_features

```
sports_features/by_date/day={date}/feature_group={feature_group}/
```

| Partition     | Description                  | Example                                                  |
| ------------- | ---------------------------- | -------------------------------------------------------- |
| day           | Processing date (YYYY-MM-DD) | day=2025-03-04                                           |
| feature_group | Feature group identifier     | feature_group=team_features, feature_group=odds_features |

**Example full path:**

```
gs://<bucket>/sports_features/by_date/day=2025-03-04/feature_group=team_features/features.parquet
```

### sports_odds

```
sports_odds/by_date/day={date}/venue={venue}/
```

| Partition | Description                    | Example                       |
| --------- | ------------------------------ | ----------------------------- |
| day       | Processing date (YYYY-MM-DD)   | day=2025-03-04                |
| venue     | Odds provider/venue identifier | venue=BETFAIR, venue=PINNACLE |

**Example full path:**

```
gs://<bucket>/sports_odds/by_date/day=2025-03-04/venue=BETFAIR/odds.parquet
```

---

## Pre-Upload Validation: validate_timestamp_date_alignment

**Required:** Call `validate_timestamp_date_alignment()` before every GCS write. This is mandatory per
[schema-governance.md](./schema-governance.md) and the schema-service-owned rule.

```python
from unified_domain_client import validate_timestamp_date_alignment

# Before every write
validate_timestamp_date_alignment(df, date=processing_date)
writer.write(df)  # only after validation passes
```

| Check                   | Description                                   |
| ----------------------- | --------------------------------------------- |
| Timestamp column exists | At least one datetime column found            |
| Date alignment          | Timestamps match expected partition date      |
| Threshold               | % of aligned rows >= threshold (default 100%) |
| Timezone                | Timestamps must be UTC                        |

Services writing to `sports_features` or `sports_odds` must define schemas in `schemas/output_schemas.py` and run this
validation before upload. See [schema-governance.md](./schema-governance.md) for full validation requirements.

---

## Path Migration Reference

For migrating legacy paths (e.g. day-YYYY-MM-DD or flat folder structures) to Hive format, reference:

**`market-tick-data-service/scripts/migrate_gcs_path_to_hive.py`**

That script demonstrates:

- Dry-run vs execute mode
- Server-side copy (no download/re-upload)
- day- to day= and dimension folder to key=value transformations
- Project ID from config or GCP_PROJECT_ID
- Date range and category filtering

**Usage pattern:**

```bash
# Dry-run (preview)
python scripts/migrate_gcs_path_to_hive.py --project-id PROJECT --start-date 2025-01-01 --end-date 2025-01-10

# Execute
python scripts/migrate_gcs_path_to_hive.py --project-id PROJECT --start-date 2025-01-01 --end-date 2025-01-10 --execute
```

Sports services adapting similar migrations should follow the same pattern: dry-run first, then execute; use server-side
copy where possible; delete old paths only after verification.

---

## SSOT — UAC `unified_api_contracts.sports.gcs_paths`

**Never hardcode `sports_reference/by_date/day=...` paths inline.** Every consumer (rescan / backfill / audit / FSS
reader / data-status / migration) must import from UAC:

```python
from unified_api_contracts.sports import (
    candidate_parquet_paths,        # data_type, day, league_id → ordered list of GCS paths
    candidate_parquet_uris,         # same but full gs:// URIs
    SPORTS_DATA_TYPE_TO_FOLDER,     # canonical data_type → entity folder name
    SPORTS_DATA_TYPE_LAYOUT,        # canonical data_type → SportsPathLayout enum
    SportsPathLayout,               # PER_DAY_PER_LEAGUE | PER_DAY_BARE | FLAT
    sports_bucket_name,             # project_id → instruments-store-sports-{project_id}
)
```

**Why this is mandatory:** the 2026-04-29 phantom-row audit incident — the audit script probed `entity=odds/`,
`entity=predictions/`, `entity=matches/` (lowercased data_type) and falsely reported 22-26% phantom rates because the
actual folder names are `entity=footystats_odds/`, `entity=footystats_predictions/`, `entity=footystats_matches/`. Each
script that constructs paths inline is one rename / migration / typo away from drifting. Single SSOT eliminates that.

**Path candidates returned by `candidate_parquet_paths(data_type, day, league_id)`:**

1. Per-league subpartition (modern layout — try first):
   `sports_reference/by_date/day={D}/entity={folder}/league={L}/{folder}.parquet`
2. Bare path (legacy + single-file-per-day entities — fallback):
   `sports_reference/by_date/day={D}/entity={folder}/{folder}.parquet`
3. Flat (singletons like VENUES — separate branch): `sports_reference/{folder}/{folder}.parquet`

`include_legacy_archive=True` adds `sports_reference_v1_archive/...` paths for migrations.

## Source coverage windows — `SOURCE_COVERAGE_START`

Sources have launch dates. Pre-launch dates must NOT count toward `expected_shards` denominators or they render as
`missing` forever. SSOT in same UAC module:

```python
from unified_api_contracts.sports import (
    SOURCE_COVERAGE_START,          # source_key → date
    get_source_coverage_start,
    clip_dates_to_source_coverage,  # source_key, start, end → (clipped_start, clipped_end)
)
```

| Source                     | Launch date |
| -------------------------- | ----------- |
| `api_football`             | 2018-01-01  |
| `footystats`               | 2019-01-01  |
| `understat`                | 2015-01-16  |
| `transfermarkt`            | 2019-01-01  |
| `soccer_football_info`     | 2019-01-01  |
| `open_meteo`               | 2019-03-02  |
| `odds_api`                 | 2020-06-06  |
| `mdps_odds_horizon_bucket` | 2020-06-06  |

The data-status reader's `_sports_expected_dates_for_league` accepts `source_key=` to apply the clip per shard.

## Manifest phantom audit + reconciliation

A "phantom" row says `capture_status=captured` but no parquet exists at any candidate path. Causes: stale rescan output,
schema migration churn, fake denorm rows from a fudge. The orchestrator's `_should_skip_shard` trusts the manifest —
phantoms cause permanent skip.

**Audit:**

```bash
cd instruments-service
.venv/bin/python scripts/reconcile_phantom_manifest_rows.py --dry-run
```

Uses `candidate_parquet_paths` SSOT + bulk-list pattern (one GCS list per day, in-memory set membership check) — 5 min
for ~600k rows. Per-row `exists()` would take 16h.

**Live flip:** drop `--dry-run` flag → flips phantom captured rows to `attempted_failed` so VMs auto-retry on next
`_should_skip_shard` pass. Use `--data-types` to scope.

**Critical rule:** do NOT write empty placeholder parquets to mask phantoms — that's fudging data quality. The
`record_empty(row_key=...)` API is for **legitimately-empty source responses only** (we tried, API returned 200 +
empty). Writing empty parquets at paths the orchestrator never attempted is dishonest: it overwrites the source-of-truth
distinction between "no data exists upstream" and "we never asked".

Reconciliation incident: 2026-04-29 — 167k fake PLAYER_VALUES denorm rows + 15k legacy phantoms cleaned up across ODDS /
PREDICTIONS / MATCHES / PLAYER_STATS / TEAMS / XG / SFI_PROGRESSIVE_STATS / STANDINGS / WEATHER / FIXTURE_EVENTS /
FIXTURE_LINEUPS / FIXTURE_STATS.

---

## Related

- [schema-governance.md](./schema-governance.md) — Schema definition, validation, NaN handling
- [hive-schema-compatibility.md](./hive-schema-compatibility.md) — Hive partitioning rationale
- [sports-data-migration.md](./sports-data-migration.md) — Broader sports bucket refactoring
- [availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md) — Honest-coverage v5 model

---

## Data Layer Separation

| Layer         | Service                                                  | Purpose                           | Odds? |
| ------------- | -------------------------------------------------------- | --------------------------------- | ----- |
| **Reference** | instruments-service                                      | Leagues, teams, stadiums, venues  | No    |
| **Features**  | features-sports-service                                  | 1000+ features, calculators, ML   | No    |
| **Market**    | market-tick-data-service, market-data-processing-service | Odds snapshots, ticks, sharp/soft | Yes   |

**Odds flow:** Odds come via market-tick-data-service (consumes UMI) and market-data-processing-service.
features-sports-service and strategy-service consume odds data; they never fetch directly from bookmakers. Interfaces
(UMI, USEI) own API keys.
