---
doc_type: codex-ssot
title: Sports Features Bucket (`sports_features/`) Path Layout SSOT
summary:
  sports_features/ has TWO co-existing writer layouts, not one — odds_features/odds_targets write DAY-LEVEL (no
  league_id column upstream), while derived_features/fixture_features write PER-LEAGUE with the RAW api-football numeric
  league id in the GCS path but the CANONICAL UAC league_id in the manifest key; every reader must probe both shapes.
status: current
nature: ssot
asset_group: [sports]
stage: [data]
repos: [features-service, ml-service, unified-trading-pm]
scope: [engineer]
tags: [sports, features, gcs-path, path-layout, per-league, day-level, manifest-key, single-walk]
related:
  [
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-27"
authoritative_for: [sports_features/ GCS path layout, sports feature-group day-level vs per-league write shapes]
referenced_by: []
owner:
last_reviewed: "2026-07-27"
code_refs:
  [
    features-service/features_service/sports/data/writer.py,
    features-service/features_service/sports/cli/handlers/batch_handler.py,
    ml-service/ml_service/training/app/core/sports_feature_loader.py,
  ]
---

# Sports Features Bucket (`sports_features/`) Path Layout SSOT

> **Scope.** This doc covers ONLY the `sports_features/` bucket tree (features-service's sports feature-group output).
> The `sports_reference/` raw-data tree (fixtures, odds, standings, etc.) is a DIFFERENT bucket area with its own
> PER_LEAGUE/BARE/FLAT taxonomy — see `/codex/02-data/sports-gcs-path-ssot.md`. Do not conflate the two.

## What it is

`sports_features/` holds the parquet output of features-service's sports feature groups (`odds_features`,
`odds_targets`, `derived_features`, `fixture_features`). All writes land under the Hive root
`sports_features/by_date/day={date}/…` — but **two different sub-layouts co-exist**, keyed by whether the feature
group's export DataFrame carries a `league_id` column.

## The two layouts

**Ground truth**: `features-service/features_service/sports/data/writer.py:26-27`

```python
DEFAULT_PATH_TEMPLATE = "sports_features/by_date/day={date}/feature_group={feature_group}/"
LEAGUE_PATH_TEMPLATE = "sports_features/by_date/day={date}/league={league_id}/feature_group={feature_group}/"
```

1. **Day-level** — `sports_features/by_date/day={date}/feature_group={feature_group}/features.parquet`. Used for
   `odds_features` and `odds_targets`: their export DataFrames carry no `league_id` column (odds rows key on the raw
   the-odds-api `event_id`, not an api-football league), so `_write_per_league()` falls through to a single un-sharded
   `write_sports_table()` call (`features-service/features_service/sports/cli/handlers/batch_handler.py:326-331`).

2. **Per-league** —
   `sports_features/by_date/day={date}/league={raw_af_id}/feature_group={feature_group}/features.parquet`. Used for
   `derived_features` and `fixture_features`: their export DataFrames DO carry `league_id`, so `_write_per_league()`
   groups by league and writes one parquet per league (`batch_handler.py:299-361`). The GCS path key uses the **RAW
   api-football numeric league id** (e.g. `league=103`) — this is deliberate and historical/addressable, **NOT to be
   renamed in place** (existing parquets stay addressable at their original path).

## The manifest-key vs GCS-path split (the non-obvious part)

For per-league writes, the GCS path and the manifest row key use **different** league identifiers:

- **GCS path** keeps the raw value (`league=103`) so existing parquets remain addressable.
- **Manifest composite key** uses the **canonical UAC `league_id`** (e.g. `EPL`), resolved via `_canonical_league_id()`
  (`batch_handler.py:93-112`) — this is what the data-status reader expects, and what
  `record_captured`/`record_expected_unattempted`/`record_failed` calls key on
  (`table_row_counts[f"{table_name}::{lid_canonical}"]`, `batch_handler.py:350-352`).

`_canonical_league_id()` handles both cases already present in the fixtures parquet: an already-canonical alphabetic id
(e.g. `"EPL"`) passes through uppercased; a numeric id (e.g. `"103"`) resolves via `get_league_by_api_football_id()` to
its canonical UAC league_id.

**Failure-atom alignment** (`batch_handler.py:639-648`, issue
`sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14`): a per-league group's `attempted_failed` row
is recorded at the SAME per-league canonical atom the success/expected_unattempted paths use — never at the day-level
atom (`league_id=""`) — so a later successful per-league run's `captured` row actually supersedes the prior failure in
the manifest dedup instead of going stale.

## Readers must handle BOTH layouts

Any reader of `sports_features/` (ml-service's training loader is the reference consumer) MUST probe both the day-level
blob AND the per-league partitions and union the results — a per-league group has **never** had a day-level blob in any
era of the bucket, so skipping the per-league probe silently drops `derived_features` (the primary ~559-column ML
feature source).

**Ground truth**: `ml-service/ml_service/training/app/core/sports_feature_loader.py:52-94` documents this exact contract
(`SportsFeatureLoaderMixin` docstring) and lines 135-146 (`_list_league_blob_paths`) implement the per-league probe as a
single bounded prefix list (`sports_features/by_date/day={date}/league=`) — never a whole-corpus GCS walk, per the
single-walk discipline.

## Summary table

| feature_group      | league_id column? | GCS path shape                                                                                          | Manifest key league_id    |
| ------------------ | ----------------- | ------------------------------------------------------------------------------------------------------- | ------------------------- |
| `odds_features`    | No                | `sports_features/by_date/day={date}/feature_group=odds_features/features.parquet`                       | n/a (day-level atom)      |
| `odds_targets`     | No                | `sports_features/by_date/day={date}/feature_group=odds_targets/features.parquet`                        | n/a (day-level atom)      |
| `derived_features` | Yes               | `sports_features/by_date/day={date}/league={raw_af_id}/feature_group=derived_features/features.parquet` | canonical UAC `league_id` |
| `fixture_features` | Yes               | `sports_features/by_date/day={date}/league={raw_af_id}/feature_group=fixture_features/features.parquet` | canonical UAC `league_id` |

## Related

- `/codex/02-data/sports-gcs-path-ssot.md` — the SEPARATE `sports_reference/` raw-data path SSOT (fixtures, odds,
  standings). Do not confuse with this doc.
- `/codex/02-data/availability-manifest-and-data-status.md` — the 4-state `capture_status` / shard-atom contract this
  doc's manifest-key section builds on.
- Issue `sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14` — the incident that established the
  dual-probe reader contract and the per-league failure-atom alignment fix.
