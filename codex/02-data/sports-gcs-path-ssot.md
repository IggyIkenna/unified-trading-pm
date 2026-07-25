---
doc_type: codex-ssot
title: Sports GCS Path SSOT
summary:
  Canonical GCS path resolver for sports parquet (UAC candidate_parquet_paths / SPORTS_DATA_TYPE_TO_FOLDER); three
  layouts (PER_LEAGUE/BARE/FLAT) plus non-obvious entity= folder names — never hardcode paths (phantom-row trap).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [sports, uac, single-walk, data-correctness, audit, canonicalisation]
related:
  [
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/sports-adapter-dependency-order.md,
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-05-08
authoritative_for:
  [sports GCS parquet path resolver and entity-folder naming, sports path-layout taxonomy (PER_LEAGUE/BARE/FLAT)]
referenced_by:
  [
    /codex/01-domain/sports-instruments.md,
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/sports-data-types-catalog.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Sports GCS Path SSOT

> **⚠️ CORRECTION (2026-07-19).** Two path facts drifted: (1) live sports_reference paths carry a **`pipeline_mode=`
> segment** (`sports_reference/by_date/day={D}/pipeline_mode=batch_api_football/entity={E}/…`), not the
> `pipeline_mode`-less layout some examples below show — readers PREFIX-MATCH canonical-then-legacy. (2) The **fixtures
> entity is SPLIT**: `entity=fixtures_schedule` + `entity=fixtures_outcomes` (2026-05-23), replacing the now-FROZEN bare
> `entity=fixtures`. Note the live layout is under `sports_reference/by_date/` — `sports_reference_v2/by_date/` is a
> DEAD abandoned layout (frozen 2026-04-20), do not read/write it. See
> `plans/active/sports_consolidated_closeout_2026_07_19.md` (ENTITY-SPLIT / STORE).

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

### An `entity=` name is NEVER a `data_type` (HARD RULE)

The left column is the ONLY legal `data_type` vocabulary; the right column names a GCS folder and nothing else.
Promoting an `entity=` name into a data_type registry mints a **phantom data_type** — a key nothing writes and nothing
reads, whose real consequence is silent: the UTL write-time mis-stamp guard is gated on
`has_source_priority(asset_group, data_type)` (`_writer_ingest.py`), so the pair the writer ACTUALLY uses goes
unregistered and **every row of it is written with source validation OFF**.

This has happened. `FIXTURE_PLAYER_STATS` (the `entity=fixture_player_stats` folder) was seeded into `SOURCE_PRIORITY` +
`AVAILABILITY_AT_SEMANTICS` at `106430c9` (2026-05-06) by analogy with its `FIXTURE_*` neighbours, while the real
data_type `PLAYER_STATS` already existed in `SPORTS_DATA_TYPE_TO_SOURCE`. Nothing ever wrote the phantom: at detection
(2026-07-15) the live IS sports index held **219,508 `PLAYER_STATS` rows and ZERO `FIXTURE_PLAYER_STATS` rows**, and the
mis-stamp guard had been OFF for every one of them. Reconciled onto `PLAYER_STATS` (unified-api-contracts@57bcc7c5 → the
A2 fix); the cross-registry drift guard `test_every_sports_data_type_to_source_key_has_source_priority` now fails closed
on a recurrence.

**Same class as the ODDS split-brain** (`ODDS` stripped by `8fb1f54f`, partially reverted by `c75101be`) — two
registries disagreeing about one data_type, detected only because a guard was added. When adding a sports data_type:
register it in `SPORTS_DATA_TYPE_TO_SOURCE` **and** `SOURCE_PRIORITY` **and** `AVAILABILITY_AT_SEMANTICS`, keyed on the
data_type the writer emits — never the folder name.

## Hive-vocab discipline

Sports paths use the canonical hive vocabulary per CLAUDE.md "Asset-group vocabulary":

- `asset_group=sports` (canonical) — written by all new code.
- `category=sports` (legacy) — preserved on disk for older parquets; readers fall back per the manifest schema rule.

The resolver writes canonical for new paths; reader fallback is hive-key-agnostic for backward compat.

> **✅ SPORTS-CANON ALIGNMENT (2026-06-01) — bucket deletion CLOSED 2026-07-16/17.** The legacy no-env
> `instruments-store-sports-central-element-323112` bucket (which held `category=` paths) was migrated onto
> `instruments-store-sports-prd-central-element-323112` and **DELETED 2026-07-16T19:52Z** (968,927 objects + 34,596
> versions purged, 0 errors; `describe` → 404; no-resurrection proved by a clean `tofu plan`). The
> `market-data-tick-sports-central-element-323112` bucket was similarly **DELETED 2026-07-17T~16:50Z** (342,629
> objects/versions purged, 0 errors; `describe` → 404). Both legacy no-env sports buckets no longer exist — do NOT write
> new code that depends on them. Evidence: `plans/active/sports_legacy_bucket_cutover_2026_07_16.md` § "FINAL STATUS"
> (T5.4); full detail in `plans/archive/2026_07/sports_legacy_bucket_cutover_history_2026_07_24.md`. The post-phase
> codex audit of this SSOT (confirming no reader still special-cases the legacy shape) is tracked as **T6.7**, still
> open P1, in `plans/active/sports_legacy_cutover_closeout_tasks_2026_07_24.md`.

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
- `/plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` and
  `/plans/active/issues/reconciliation_skill_sports_raw_tick_ssot_wrong_bucket_2026_07_24.md` — both stem from the same
  underlying dual-bucket architecture this doc describes (`instruments-store-sports-*`'s `sports_reference/` reference
  tree vs `market-data-tick-sports-*`'s standard `raw_tick_data/` raw-tick tree): the phantom auditor and, separately,
  `/data-pipeline-reconciliation`'s own governing codex (`four-surface-reconciliation-procedure.md` §4.2/§6) each
  independently conflated the two buckets before being corrected.

## Reviewer checklist

- [ ] No hardcoded `entity=<folder>` strings outside `unified_api_contracts/canonical/domain/sports/gcs_paths.py` across
      the workspace (`rg 'entity=[a-z_]+' --type py` + manual review).
- [ ] Every sports reader uses `candidate_parquet_paths()` (or its `_uris` counterpart for full GCS URIs).
- [ ] Data-status reconciler regex matches both `category=` and `asset_group=` hive prefixes (per phantom-audit
      hardening 2026-05-04).
- [ ] New sports data_types added to `SPORTS_DATA_TYPE_TO_FOLDER` + `SPORTS_DATA_TYPE_LAYOUT` in the same UAC commit.
