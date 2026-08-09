---
doc_type: issue
title:
  a sports_reference entity=fixtures object under instruments-store-sports-prd contains instrument-catalog schema
  content instead of api-football fixture data
summary: >-
  While running the peripheral-bucket league-vocabulary migration
  (issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md), the cross-entity resolver's parquet
  read of an entity=fixtures object failed with a schema mismatch, not a missing-column error. Direct verification
  confirmed the object genuinely exists at
  sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet
  in instruments-store-sports-prd-central-element-323112, and its content is an INSTRUMENT-CATALOG schema
  (instrument_key, venue, instrument_type, raw_symbol, base_asset, quote_asset, asset_class, tick_size, contract_size,
  expiry, strike, option_type, underlying, margin_type, is_trading_day, trading-session timestamps, holiday_calendar,
  timezone, __fragment_index/__batch_index/__filename) — not api-football sports fixture data (af_league_id, teams,
  kickoff time, etc.). The same "No match for FieldRef.Name(af_league_id) in <schema>" error pattern recurred
  identically across 54 distinct league values during the 2026-08-09 dry-run census of this bucket (see the sibling
  issue's Progress Log), suggesting this is not an isolated one-object accident.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [sports, data-correctness, schema-contamination, gcs, instruments-store-sports-prd]
related:
  [
    /plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
    /plans/active/sports_closeout_track_x_hygiene_2026_07_25.md,
  ]
created: "2026-08-09"
author: sports_closeout_track_x_hygiene-006 (slot-6, data_engineering)
source: >-
  Discovered mid-migration while running the league-vocabulary resolver's cross-entity fixtures lookup for
  sports_closeout_track_x_hygiene-006's migration dispatch, 2026-08-09.
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md,
    /codex/02-data/sports-gcs-path-ssot.md,
    /codex/05-infrastructure/gcs-object-operations.md,
  ]
---

# Sports fixtures object carries instrument-catalog schema, not fixture data

## What was found (2026-08-09, mid-migration)

Running the league-vocabulary migration's cross-entity resolver (`_resolve_canonical_league()` in
`market-tick-data-service/scripts/sports/league_id_relocation/migrate_instruments_store_sports_league_vocabulary_2026_08_04.py`)
against `instruments-store-sports-prd-central-element-323112`, a `pd.read_parquet(..., columns=["af_league_id"])` call
raised:

```
No match for FieldRef.Name(af_league_id) in instrument_key: string
venue: string
instrument_type: string
raw_symbol: string
base_asset: string
quote_asset: string
status: string
available_from_datetime: timestamp[us, tz=UTC]
available_to_datetime: timestamp[us, tz=UTC]
asset_class: string
settle_asset: null
tick_size: decimal128(2, 2)
min_size: decimal128(1, 0)
contract_size: decimal128(1, 0)
expiry: timestamp[us, tz=UTC]
strike: null
option_type: null
underlying: null
margin_type: null
legs: null
is_trading_day: null
regular_open_utc: null
regular_close_utc: null
early_close_utc: null
pre_market_open_utc: null
post_market_close_utc: null
auction_open_utc: null
auction_close_utc: null
holiday_calendar: null
timezone: string
available_at: timestamp[us, tz=UTC]
__fragment_index: int32
__batch_index: int32
__last_in_fragment: bool
__filename: string
```

This is an `InstrumentRecord`-shaped schema (venue/instrument_type/base_asset/quote_asset/tick_size/contract_size/
expiry/strike/option_type/margin_type/trading-session-times/holiday_calendar) — the shape instruments-service uses for
its general instrument-universe catalog, NOT api-football sports fixture data.

**Direct verification** (bypassing the migration script, downloading the object directly via
`unified_trading_library.download_from_storage`):

- Path:
  `sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet`
- Bucket: `instruments-store-sports-prd-central-element-323112`
- The object genuinely EXISTS (not a 404 masked as something else) and is 8,194 bytes of valid parquet with the
  instrument-catalog schema above. `download_from_storage()` itself is NOT at fault here — it returned the real bytes at
  that path; those bytes are simply the wrong content type for the path they live at.
- Only 3 objects total exist under this exact `(day, pipeline_mode, league)` triple, which is why this wasn't previously
  caught by spot checks.

**Not isolated**: the same `"No match for FieldRef.Name(af_league_id)"` error pattern recurred for 54 distinct league
values during the 2026-08-09 full-bucket dry-run census (out of 450 non-numeric quarantined values) — see
`issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`'s 2026-08-09 Progress Log entry for the
full list of affected league values. Each occurrence was a small object count (single digits to low tens), consistent
with a rare/edge-case write-path bug rather than a bulk corruption.

## Why this is filed separately

This is a DIFFERENT correctness problem from the league-vocabulary-contamination issue that surfaced it: that issue is
about the wrong VALUE in the `league=` path segment; this is about the wrong CONTENT TYPE inside the object entirely
(sports fixture path, instrument-catalog payload). Fixing the vocabulary contamination does not touch this — these
objects need their own root-cause trace and remediation (most likely: quarantine/re-fetch, not a path rename, since the
content itself is wrong, not just misfiled).

## Required work (not started)

1. **Confirm scope**: enumerate every object across `instruments-store-sports-prd` (and check `features-sports-prd` too,
   given the sibling issue's finding that the SAME normalizer feeds both buckets) whose parquet schema does not match
   the expected schema for its `entity=` partition. A per-entity expected-schema check (not just `entity=fixtures`) is
   the right scope — this instance happened to be caught via the fixtures-specific `af_league_id` read, but the same
   failure mode could affect other entities silently.
2. **Root-cause**: identify the writer that produced `day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures`
   content shaped like instruments-service's `InstrumentRecord` catalog. Candidates to check: a shared serialization
   helper reused across both instrument-catalog and sports-fixture write paths that picked the wrong schema/template for
   this call; a path-construction bug that wrote instrument-catalog output to a sports-shaped path; or a cross-service
   GCS client misconfiguration (bucket/prefix mixup) on 2026-04-14 specifically.
3. **Remediate**: once root-caused, decide fix-at-write-path (if live) and whether the specific mis-shaped objects
   should be re-fetched from api-football (if recoverable) or quarantined/deleted per the delete-safety protocol (if
   not).

P1 because it is a **content-correctness** bug (wrong schema entirely, not just wrong path/value) that could silently
break any downstream reader assuming `entity=fixtures` always carries fixture columns — worse than the vocabulary
contamination this issue was found alongside.

Evidence: `sports_closeout_track_x_hygiene-006` dispatch session (slot-6, 2026-08-09) — direct GCS verification
transcript available in that session's Progress Log entry on
`plans/active/sports_closeout_track_x_hygiene_2026_07_25.md`.

## Todos

- [ ] [DATA] P1. Enumerate the full scope of schema-mismatched objects across `instruments-store-sports-prd` (all
      `entity=` partitions, not just `fixtures`) and `features-sports-prd`. Produce a per-entity, per-schema-shape
      count. This is corpus-scale (the sibling issue already flagged `instruments-store-sports-prd` as needing a
      dedicated bounded VM walk for a full census) — run as a bounded VM job, not an interactive dispatch. (repo:
      instruments-service / market-tick-data-service). **Done when**: a report exists listing every object whose parquet
      schema does not match its `entity=` partition's expected schema, with counts by entity/day/pipeline_mode.
- [ ] [DATA] P1. Root-cause the writer that produced the
      `day=2026-04-14/pipeline_mode=batch_api_football/     entity=fixtures/league=BOLIVIA_PRIMERA_DIVISION/fixtures.parquet`
      instrument-catalog-shaped object (and the 53 other affected league values found the same day's census — see the
      sibling issue's 2026-08-09 Progress Log for the full list). Check shared serialization/write helpers used by both
      instruments-service's catalog writer and the sports fixture writer for a schema-template mixup, and check for GCS
      bucket/prefix misconfiguration on that date. (repo: instruments-service / market-tick-data-service /
      unified-api-contracts). **Done when**: the root cause is identified and documented here with evidence (the exact
      write call responsible).
- [ ] [DATA] P1. Fix the write path (if still live) and remediate the existing mis-shaped objects (re-fetch if
      recoverable, else quarantine/delete per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`), gated on the
      two todos above. (repo: instruments-service / market-tick-data-service). **Done when**: a fresh scoped check of
      the affected (day, pipeline_mode, entity) triples returns 0 schema-mismatched objects.

## Progress Log

- **2026-08-09 (slot-6, data_engineering, discovered during `sports_closeout_track_x_hygiene-006`)**: filed this issue
  after direct GCS verification confirmed the anomaly is real (not a script bug) — see "What was found" above for the
  full transcript. Did not investigate root cause or remediate; out of scope for the migration task that surfaced it.
