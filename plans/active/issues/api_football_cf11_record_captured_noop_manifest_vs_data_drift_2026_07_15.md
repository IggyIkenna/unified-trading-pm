---
doc_type: issue
title:
  "RESOLVED: CF11 api_football residual was a manifest-vs-data drift (18 cells) — data parquets present + provider has
  the data, manifest stuck attempted_failed. Reconciled to captured. NOTE: record_captured() is NOT broken; the prior
  closers' real defect was never calling ManifestWriter.write() (staged rows sit on the writer instance's _records,
  which flush_all_pending_buckets() does NOT drain)"
summary:
  "data_engineering (slot-11, 2026-07-15, AO task sports_data_sources_canonical_completion-023). The 18 remaining CF11
  attempted_failed api_football cells (FIXTURE_EVENTS 8 / FIXTURE_LINEUPS 10, 11 match-days, leagues
  ARGENTINA_PRIMERA_NACIONAL/CHILE_PRIMERA_B/POLAND_I_LIGA/ENG_NATIONAL_LEAGUE) were a manifest-vs-data drift, NOT a
  data gap: (1) api_football HAS the events/lineups (live probe: 9-23 events + 34-40 lineups/fixture, only 1
  genuinely-empty fixture); (2) the canonical per-league DATA parquets are PRESENT on disk for all 18 cells (14-141 rows
  each). RESOLVED by reconciling each cell to captured from its present parquet (record_captured + write) —
  instruments-service one-off api_football_cf11_manifest_reconcile_2026_07_15.py: 18/18 captured, 0 CF11
  attempted_failed remaining, live-verified. IMPORTANT CORRECTION to this doc's first cut: record_captured() is NOT
  broken. It stages the captured row on the writer INSTANCE (self._records); persistence requires ManifestWriter.write()
  (or batch_size auto-write). The prior 2026-07-13 closer AND this session's first closer both called
  flush_all_pending_buckets() — which drains the bucket-level pending, NOT a live writer's un-written _records — so
  their record_captured rows were staged and then silently discarded when the per-date writer went out of scope.
  MANIFEST_WRITE_SCHEMA_MISSING is warn-only (validation skipped, row still staged) and was a red herring."
status: resolved
priority: P2
nature: notes
asset_group: [sports, meta]
stage: [meta]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    api_football,
    cf11,
    manifest,
    record_captured,
    manifest-writer-write,
    manifest-vs-data-drift,
    data-correctness,
    sports,
  ]
related:
  [
    ../sports_data_sources_canonical_completion_2026_07_13.md,
    manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md,
    sports_manifest_read_staleness_budget_missing_2026_07_15.md,
  ]
created: 2026-07-15
parent_epic: manifest_master
source:
  "data_engineering worker (slot-11, planning VM), 2026-07-15, AO task sports_data_sources_canonical_completion-023.
  Measurements live against instruments-store-sports-prd-central-element-323112 (read with
  MANIFEST_CONSOLIDATED_STALENESS_SEC=3600 — see sibling sports_manifest_read_staleness_budget_missing_2026_07_15.md).
  Provider probe via
  create_sports_reference_adapter('api_football').get_fixtures/get_fixture_events/get_fixture_lineups; reconcile via
  instruments-service/scripts/backfill/api_football_cf11_manifest_reconcile_2026_07_15.py."
locked_by:
resolved_by:
  "instruments-service@87d1a353 (api_football_cf11_manifest_reconcile_2026_07_15.py) — 18/18 captured, 0 CF11 remaining"
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
assigned_vm: planning
depends_on: []
---

## What I found (and the correction to the first cut)

The 18 remaining `CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` api_football `attempted_failed` cells were **manifest-vs-data
drift**, not a real data gap.

### The data is present (provider + on disk)

- **Provider probe** (live, read-only): every CF11 fixture returns real detail (events 9-23, lineups 34-40 per fixture);
  of ~20 probed fixtures only 1 (CHILE_PRIMERA_B 2024-08-01 fixture 1168951) is genuinely `events=0 lineups=0`, and its
  cell still has data from the other fixtures.
- **On-disk parquets present** for all 18 cells (`_list_present_parquet_leagues`; 14-141 rows/cell), e.g.
  `sports_reference/by_date/day=2021-06-09/pipeline_mode=batch_api_football/entity=fixture_events/league=ARGENTINA_PRIMERA_NACIONAL/fixture_events.parquet`.

### Why they were stuck — and the correction

The v9-rebuild CF-11 gate (`rebuild_sports_manifest_v9.py`) upgrades a `fixtures_truth`-confirmed match-day with an
empty guaranteed-type cell to `attempted_failed`. These cells were empty in the manifest at rebuild time even though the
parquet existed, so they were frozen `attempted_failed(CF11)`.

**This doc's first cut mis-attributed the block to `record_captured()` silently no-oping on
`MANIFEST_WRITE_SCHEMA_MISSING`. That is WRONG — corrected here after further repro:**

- `record_captured()` stages the row on the **writer instance** (`self._records`) and returns; it does NOT push to the
  process-global bucket pending. Persistence happens in `ManifestWriter.write()` (or `batch_size` auto-write).
- The prior 2026-07-13 closer and this session's first closer both created a fresh `ManifestWriter` per date and
  finished with `flush_all_pending_buckets()` — which drains the **bucket-level** pending, NOT a live writer's
  un-written `self._records`. So every `record_captured` row was staged and then silently discarded when the per-date
  writer fell out of scope → `flush_all_pending_buckets()=={}`, no per-VM shard, cell unchanged. My initial diagnostic
  reproduced exactly that mistake (checked `_get_pending_records(bucket)` / called `flush_all_pending_buckets()` instead
  of `writer.write()`), which is why I first concluded record_captured was broken.
- Adding `writer.write()` flips the cell immediately: proven with a direct `record_captured(...); mw.write()` → per-VM
  shard row `FIXTURE_EVENTS captured row_count=39 available_at=2021-06-09 17:00`. `MANIFEST_WRITE_SCHEMA_MISSING` is
  warn-only (validation skipped, row still staged — `_writer_validation.py::_validate_with_source`) and was a red
  herring.

### Resolution

`instruments-service/scripts/backfill/api_football_cf11_manifest_reconcile_2026_07_15.py` (shipped
`instruments-service@87d1a353`) reconciles each stuck CF11 cell to `captured` from its PRESENT parquet
(`record_captured` + `write()`; cells with no parquet are skipped + reported, never fake-stamped). Result: **18/18
captured, 0 `error_reason=CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE` api_football `attempted_failed` rows remaining**,
live-verified against the sports canonical (self-shard-merged read); the per-minute consolidator absorbs the reconcile
shard into the consolidated blob for all readers.

## Why it still matters (residual follow-ups — NOT blocking task -023)

- [ ] [DATA] P2. **Direct `_fetch_sports_reference_data` / backfill callers must call `ManifestWriter.write()`** (not
      just `flush_all_pending_buckets()`) or their `record_captured` rows are silently lost. Two separate CF11 closers
      hit this exact footgun. Options (repo: unified-trading-library / instruments-service): make
      `flush_all_pending_buckets()` also flush live writer instances' un-written `_records`, OR add a loud warning when
      a `ManifestWriter` is GC'd with non-empty `_records`, OR document the contract prominently on the
      `_fetch_sports_reference_data` docstring. Low-risk hardening that prevents a recurring silent-data-loss class.
- [ ] [DATA] P3. **Audit for other CF11-style manifest-vs-data drift** across sports (and other asset_groups): cells the
      rebuild marked `attempted_failed`/`empty` while the canonical parquet is present. If material, a general
      manifest-vs-parquet reconcile pass (generalising this one-off) is warranted (repo: instruments-service /
      market-tick-data-service). Cross-ref the sibling `record_captured` write-path defect
      `manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md` (parent_epic manifest_master) — that
      one (available_at validated-but-never-persisted, fixed UTL@9c9cdc50) is a DISTINCT prior defect in the same
      method; this doc is a sibling, not a dup.
