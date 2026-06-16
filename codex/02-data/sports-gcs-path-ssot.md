---
scope: [engineer]
last_reviewed: 2026-05-17
---

# Sports GCS Path SSOT

**What it is.** The canonical path-resolver for sports parquet on GCS. Every sports reader / writer / data-status audit
/ phantom-row reconciler uses this SSOT — no hardcoded `entity=...` strings inline.

**SSOT module.**
[`unified_api_contracts/canonical/domain/sports/gcs_paths.py`](https://github.com/IggyIkenna/unified-api-contracts/tree/main/unified_api_contracts/canonical/domain/sports/gcs_paths.py)
in UAC. Re-exported via
`from unified_api_contracts.sports import candidate_parquet_paths, candidate_parquet_uris, SPORTS_DATA_TYPE_TO_FOLDER, SPORTS_DATA_TYPE_LAYOUT, SportsPathLayout, sports_bucket_name`.

## Why this SSOT exists

**Reference incident — phantom-row audit 2026-04-29.** A data-status reconciler probed `entity=odds/` for `ODDS_API`
fixtures and reported 26% phantom coverage. Reality: api_football odds are stored under `entity=footystats_odds/`
(historical naming from the migration era). The probe used a hardcoded path string instead of the canonical resolver —
so it scanned the wrong directory and produced fake phantoms.

The recovery: 167k fake `PLAYER_VALUES` denorm rows + 15k legacy phantoms cleaned up. The lesson: **never hardcode path
strings inline; always go through the resolver.**

## API surface

```python
from unified_api_contracts.sports import (
    candidate_parquet_paths,        # ordered list of GCS paths to probe
    candidate_parquet_uris,         # same, prefixed with gs://<bucket>/
    SPORTS_DATA_TYPE_TO_FOLDER,     # data_type → entity-folder canonical name
    SPORTS_DATA_TYPE_LAYOUT,        # data_type → SportsPathLayout enum
    SportsPathLayout,               # PER_LEAGUE | BARE | FLAT
    sports_bucket_name,             # asset_group=sports → GCS bucket name resolver
)

# Reader pattern: try canonical first, fall through fallbacks
for path in candidate_parquet_paths(data_type, day, league_id):
    if gcs_blob_exists(path):
        return read_parquet(path)
return None  # honest absence; record_empty(reason=EXPECTED_*)
```

## Path layout taxonomy

Three layout variants, declared per data_type in `SPORTS_DATA_TYPE_LAYOUT`:

### Layout 1 — `PER_LEAGUE` (default for fixture-grain data)

Per-league subpartition first; bare fallback for legacy.

```
gs://<bucket>/sports_reference/by_date/day=YYYY-MM-DD/entity=<folder>/league=<league_id>/<folder>.parquet  # canonical
gs://<bucket>/sports_reference/by_date/day=YYYY-MM-DD/entity=<folder>/<folder>.parquet                      # legacy fallback
```

Used by: `FIXTURE_LINEUPS`, `FIXTURE_EVENTS`, `FIXTURE_STATS`, `PLAYER_STATS`, `INJURIES`, `ODDS_SNAPSHOT`,
`ODDS_MOVEMENT`, `LINEUPS_PRE_MATCH`, etc. (see `SPORTS_DATA_TYPE_TO_FOLDER` for the full mapping).

### Layout 2 — `BARE` (per-league grouping intentionally absent)

```
gs://<bucket>/sports_reference/by_date/day=YYYY-MM-DD/entity=<folder>/<folder>.parquet
```

Used by: data_types where league_id grouping has no meaning (cross-league reference data).

### Layout 3 — `FLAT` (singletons; no by_date partition)

```
gs://<bucket>/sports_reference/<folder>/<folder>.parquet
```

Used by: `VENUES` (stadium reference table — single global file), other singletons.

## `entity=` folder naming — the phantom-row trap

Some sources have non-obvious `entity=` folder names that don't match the data_type name:

| `data_type`             | `entity=` folder              | Source                         |
| ----------------------- | ----------------------------- | ------------------------------ |
| `ODDS_API`              | `entity=odds_api`             | odds_api                       |
| `ODDS_SNAPSHOT` (fs)    | `entity=footystats_odds`      | footystats                     |
| `FIXTURE_STATS` (af)    | `entity=fixture_statistics`   | api_football                   |
| `PLAYER_STATS` (af)     | `entity=fixture_player_stats` | api_football                   |
| `INJURIES`              | `entity=fixture_injuries`     | api_football                   |
| `WEATHER`               | `entity=open_meteo_forecasts` | open_meteo                     |
| `SFI_PROGRESSIVE_STATS` | `entity=sfi_progressive`      | soccer_football_info           |
| `LINEUPS_PRE_MATCH`     | `entity=fixture_lineups`      | api_football (pre-kickoff cut) |

Hardcoding any of these inline is a phantom-row foot-gun. The resolver maintains the mapping; readers never need to know
it.

## Hive-vocab discipline

Sports paths use the canonical hive vocabulary per CLAUDE.md "Asset-group vocabulary":

- `asset_group=sports` (canonical) — written by all new code.
- `category=sports` (legacy) — preserved on disk for older parquets; readers fall back per the manifest schema rule.

The resolver writes canonical for new paths; reader fallback is hive-key-agnostic for backward compat.

> **🔎 SPORTS-CANON ALIGNMENT (2026-06-01):** After the `sports_manifest_canonicalisation_2026_06_01.md` C0 walk
> completes, the legacy no-env `instruments-store-sports-central-element-323112` bucket (which holds `category=` paths)
> will be **migrated to `instruments-store-sports-prd-…` and DELETED** — the legacy reader-fallback path for the
> instruments surface becomes redundant at that point. The `market-data-tick-sports-{no-env}` bucket will similarly be
> deleted. SSOT for the delete schedule: `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` §L6 + §L7. Do
> NOT write new code that depends on the legacy no-env sports buckets existing after the C-GREEN hand-off.

## Cross-references

- [`sports-data-source-coverage-matrix.md`](sports-data-source-coverage-matrix.md) — `SOURCE_COVERAGE_START` /
  `DATA_TYPE_COVERAGE_START` / `KNOWN_COVERAGE_GAPS` SSOTs (when each source has data; the temporal axis).
- [`sports-adapter-dependency-order.md`](sports-adapter-dependency-order.md) — adapter execution order at backfill time.
- [`sports-scheduling-and-sharding.md`](sports-scheduling-and-sharding.md) — per-source sharding strategy.
- [`availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md) — manifest schema for sports
  shards (asset_group, source, data_type, league_id, fixture_id_or_day).
- CLAUDE.md § "Sports GCS path SSOT" — the workspace rule that mandates resolver usage; this codex doc is its durable
  home.
- [`plans/epics/sports_master.md`](../../plans/epics/sports_master.md) — sports asset_group umbrella; cites this SSOT as
  the path-layout authority.

## Reviewer checklist

- [ ] No hardcoded `entity=<folder>` strings outside `unified_api_contracts/canonical/domain/sports/gcs_paths.py` across
      the workspace (`rg 'entity=[a-z_]+' --type py` + manual review).
- [ ] Every sports reader uses `candidate_parquet_paths()` (or its `_uris` counterpart for full GCS URIs).
- [ ] Data-status reconciler regex matches both `category=` and `asset_group=` hive prefixes (per phantom-audit
      hardening 2026-05-04).
- [ ] New sports data_types added to `SPORTS_DATA_TYPE_TO_FOLDER` + `SPORTS_DATA_TYPE_LAYOUT` in the same UAC commit.
