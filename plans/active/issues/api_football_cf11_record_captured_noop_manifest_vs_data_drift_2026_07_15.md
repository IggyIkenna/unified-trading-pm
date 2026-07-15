---
doc_type: issue
title:
  "CF11 api_football residual is a manifest-vs-data drift the standard path CANNOT resolve: the data parquets are
  present + the provider has the data, but UTL ManifestWriter.record_captured() SILENTLY NO-OPS for sports
  FIXTURE_EVENTS/FIXTURE_LINEUPS (MANIFEST_WRITE_SCHEMA_MISSING → row never staged), so the manifest stays
  attempted_failed(CF11) forever"
summary:
  "data_engineering (slot-11, 2026-07-15, AO task sports_data_sources_canonical_completion-023) tried to backfill the 18
  remaining CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE api_football attempted_failed rows (FIXTURE_EVENTS 8 / FIXTURE_LINEUPS
  10, 11 match-days, leagues ARGENTINA_PRIMERA_NACIONAL/CHILE_PRIMERA_B/POLAND_I_LIGA/ENG_NATIONAL_LEAGUE). Root-caused
  it is NOT a data gap: (1) api_football HAS the events/lineups (live probe: 9-23 events + 34-40 lineups per fixture for
  every cell except 1 genuinely-empty fixture); (2) the canonical per-league DATA parquets are PRESENT on disk for every
  cell (verified via _list_present_parquet_leagues). The blocker is a UTL bug: ManifestWriter.record_captured() for
  sports per-fixture data_types emits MANIFEST_WRITE_SCHEMA_MISSING and returns WITHOUT staging a captured row (repro:
  direct record_captured() with the present 39-row parquet → flush_all_pending_buckets()=={}, no per-VM shard written,
  cell stays attempted_failed). Because record_captured no-ops, neither a live re-fetch (redo_all=True force re-fetch
  re-writes the parquet but records nothing) nor a direct data-backed reconcile can flip these to captured. The prior
  2026-07-13 closer left the same rows attempted_failed for the same reason."
status: open
priority: P1
nature: notes
asset_group: [sports, meta]
stage: [meta]
repos: [unified-trading-library, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [api_football, cf11, manifest, record_captured, schema-missing, manifest-vs-data-drift, data-correctness, sports]
related: [../sports_data_sources_canonical_completion_2026_07_13.md]
created: 2026-07-15
parent_epic: infrastructure_master
source:
  "data_engineering worker (slot-11, planning VM), 2026-07-15, AO task sports_data_sources_canonical_completion-023. All
  measurements live against instruments-store-sports-prd-central-element-323112 (_index/availability_index.parquet
  ~5.35M rows, read with MANIFEST_CONSOLIDATED_STALENESS_SEC=3600 to bypass the false-stale guard — see sibling issue
  sports_manifest_read_staleness_budget_missing_2026_07_15.md). Provider probe via
  create_sports_reference_adapter('api_football').get_fixtures/get_fixture_events/get_fixture_lineups; record_captured
  no-op repro via a direct ManifestWriter.record_captured() call with the on-disk parquet."
locked_by:
resolved_by:
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
---

## What I found

The 18 remaining `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` api_football `attempted_failed` cells are **manifest-vs-data
drift**, not a real data gap, and the standard resolution path **cannot** clear them because of an upstream UTL bug.

### 1. The data is present (both at the provider and on disk)

- **Provider probe** (live api_football, read-only): every CF11 fixture returns real detail — e.g. 2021-06-09
  ARGENTINA_PRIMERA_NACIONAL fixtures 684618/684616/684621 → events 16/9/14, lineups 39/40/40; 2025-09-02
  ENG_NATIONAL_LEAGUE → events 11-23, lineups 34-36; POLAND_I_LIGA 2025-08-21 → events 11-21. Of ~20 probed fixtures
  only ONE (CHILE_PRIMERA_B 2024-08-01 fixture 1168951) is genuinely `events=0 lineups=0`; its cell still has data from
  the other two fixtures.
- **On-disk parquets present** (verified via `instruments_service.engine.orchestrator._list_present_parquet_leagues`):
  the canonical per-league parquet exists for every CF11 cell, e.g.
  `sports_reference/by_date/day=2021-06-09/pipeline_mode=batch_api_football/entity=fixture_events/league=ARGENTINA_PRIMERA_NACIONAL/fixture_events.parquet`
  (39 rows). The pipeline's own pre-fetch skip logs confirm it: "6 (entity, fixture_id) pairs already in existing
  per-league parquets — skipping api_football calls".

### 2. record_captured() silently no-ops for these cells → manifest never becomes captured (THE BUG)

`unified_trading_library.manifest_writer.ManifestWriter.record_captured()` for
`data_type in {FIXTURE_EVENTS, FIXTURE_LINEUPS}` (asset_group=sports, source=api_football, a valid non-empty df with
`available_at`) **emits `MANIFEST_WRITE_SCHEMA_MISSING` (validation_source=write_auto) and returns without staging a
captured row**. Reproduced three ways, all with `flush_all_pending_buckets() == {}`, no per-VM shard written, and the
cell unchanged at `attempted_failed(CF11)`:

- via the orchestrator per-fixture write path `_write_per_fixture_entities` (redo_all=False, override recovery);
- via a FORCE re-fetch (`_fetch_sports_reference_data(..., fixture_ids_override, recovery_fixture_ids, redo_all=True)`)
  — re-fetches + re-writes the parquet ("39 fixture_events rows written") but records nothing;
- via a DIRECT
  `record_captured(row_key={date,data_type,league_id}, df=<on-disk 39-row parquet>, asset_group='sports', data_type='FIXTURE_EVENTS', league_id='ARGENTINA_PRIMERA_NACIONAL', source='api_football', pipeline_mode=BATCH_API_FOOTBALL)`
  — same no-op.

Ruled OUT as the cause: schema MISMATCH (docstring says warn-only, row still written), `MissingSourceError`
(`source='api_football'`, `source_required('sports','FIXTURE_EVENTS')==False`), write-universe gate (all 4 leagues
`_is_in_canonical_write_universe==True`), and a merge tie-break (no shard is written at all — it is a record-level
no-op, not a merge outcome). The remaining suspect is the `MANIFEST_WRITE_SCHEMA_MISSING` path in `_writer_captured.py`
treating "no contract schema registered for (sports, FIXTURE_EVENTS/LINEUPS)" as a **skip** rather than the docstring's
advertised warn-and-write.

### 3. Why the cells got marked attempted_failed in the first place

The v9-rebuild CF-11 gate (`market-tick-data-service/.../rebuild_sports_manifest_v9.py`, operator directive 2026-06-02)
upgrades a `fixtures_truth`-confirmed match-day with an empty guaranteed-type cell to `attempted_failed` (never
`empty_confirmed`). With record_captured unable to ever write a captured row for these data_types, any cell that was
empty at rebuild time is frozen `attempted_failed(CF11)` permanently even after the parquet lands — an unbreakable drift
loop. Note there are ~37,892 captured api_football FIXTURE_EVENTS rows in the manifest already; those were stamped by
the rebuild's own parquet-walk writer (which bypasses record_captured), NOT by record_captured — consistent with
record_captured being broken for this data_type.

## Why it matters

- **Data-correctness heartbeat.** The manifest reports `attempted_failed` for cells whose data is fully present and
  valid — a false-negative that blocks the plan's "0 attempted_failed" target and misleads every downstream coverage
  consumer.
- **Broader blast radius than 18 cells.** record_captured is the sanctioned per-shard write-path entry point. If it
  silently drops sports FIXTURE_EVENTS/FIXTURE_LINEUPS captures, the LIVE/daily sports pipeline's captures for these
  data_types are ALSO not being recorded via record_captured — the manifest is being kept honest only by the periodic
  rebuild walk, not by the write path. That is a latent, ongoing manifest-vs-data drift for all sports per-fixture
  entities, not a one-off.

## Recommended decision

Fix record_captured's schema-missing handling (root fix), then reconcile the 18 stuck cells. Do NOT relabel them
`empty_confirmed` — the CF-11 gate deliberately forbids that (it would be re-upgraded to attempted_failed on the next
rebuild) and the data is genuinely present.

- [ ] [DATA] P1. Root-cause + fix the `MANIFEST_WRITE_SCHEMA_MISSING` branch in
      `unified-trading-library/unified_trading_library/manifest_writer/_writer_captured.py::record_captured` so a
      MISSING contract schema is warn-AND-write (matching the documented MISMATCH behavior + the docstring), not a
      silent skip that drops the captured row (repo: unified-trading-library). Add a regression test:
      `record_captured(asset_group='sports', data_type='FIXTURE_EVENTS', df=<valid>, source='api_football')` MUST stage
      a captured row (flush produces a shard). Confirm whether the real fix is registering the sports
      FIXTURE_EVENTS/FIXTURE_LINEUPS/FIXTURE_STATS contract schemas in the UAC registry instead (if they are genuinely
      unregistered) — either way the row must be written.
- [ ] [DATA] P1. After the record_captured fix lands, reconcile the CF11 residual by force re-driving exactly these
      cells through the targeted-recovery path
      `_fetch_sports_reference_data(date, entities_to_fetch=[FIXTURE_EVENTS|FIXTURE_LINEUPS], fixture_ids_override=<af     source_fixture_ids for the date>, recovery_fixture_ids=frozenset(<same>), redo_all=True, manifest=<ManifestWriter>)`
      per date (repo: instruments-service). Set `MANIFEST_CONSOLIDATED_STALENESS_SEC=3600` for the manifest reads. The
      11 dates + af league ids + source_fixture_ids are enumerated in the Progress-Log note referenced by AO task -023;
      the CHILE_PRIMERA_B 2024-08-01 fixture 1168951 is the one genuinely-empty fixture (its cell still has data from
      the other fixtures, so the cell → captured). Verify 0 `error_reason=CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE`
      api_football rows remain in the consolidated manifest.
- [ ] [DATA] P2. Audit the scope of the drift: count captured sports FIXTURE_EVENTS/FIXTURE_LINEUPS/FIXTURE_STATS
      manifest rows written by record_captured vs. by the rebuild walk since the schema went missing, to size how many
      live/daily sports per-fixture captures are silently not being recorded by the write path (repo:
      market-tick-data-service / instruments-service). If material, this gates the sports availability view's honesty
      between rebuilds.
