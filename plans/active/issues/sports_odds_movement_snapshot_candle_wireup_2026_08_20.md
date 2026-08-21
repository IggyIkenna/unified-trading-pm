---
doc_type: issue
title: >-
  Wire SportsOddsMovementAdapter/SportsOddsSnapshotAdapter into the live MDPS sports driver —
  operator-approved "wire up" over "retire" (2026-08-20)
summary: >-
  `sports_taxonomy_p2_migration_2026_08_08.md`'s "re-stamp odds_snapshot/odds_movement" todo turned out to gate on a
  false premise (0 real captures — see that plan's Progress Log 2026-08-15) and was closed as moot. But the deeper
  question underneath it — first flagged in `sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md` as
  "wire up vs retire, never made" — was still genuinely open. Verified live 2026-08-20: `reprocess_sports_odds.py`
  (the one scheduled Cloud Run job for sports MDPS) instantiates only `SportsBucketAssignmentAdapter`; a fleet-wide
  grep for `SportsOddsMovementAdapter(`/`SportsOddsSnapshotAdapter(` found zero non-test call sites outside the
  adapters' own modules. The computation itself is real and correct — `SportsOddsMovementAdapter` produces a genuine
  OHLC candle of `home_odds` (open/high/low/close from first/max/min/last per interval) — it has simply never been
  invoked by any production driver. Operator decision (interactive session, 2026-08-20): wire it up, not retire.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, unified-api-contracts]
scope: [engineer]
tags: [sports, mdps, odds, odds_horizon_bucket, candle, data-pipeline]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/archive/issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md,
    /codex/02-data/sports-data-types-catalog.md,
  ]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    /codex/02-data/sports-data-types-catalog.md,
    market-data-processing-service/scripts/reprocess_sports_odds.py,
    market-data-processing-service/market_data_processing_service/app/adapters/sports/odds_movement_adapter.py,
    market-data-processing-service/market_data_processing_service/app/adapters/sports/odds_snapshot_adapter.py,
    market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py,
  ]
source: >-
  Interactive session, 2026-08-20 — operator pushed back on an initial "retire the dead types" framing of
  sports_taxonomy_p2_migration_2026_08_08.md's blocked todo, correctly recalling that a real
  candle/acceleration view of the odds data exists. Verified against live code before answering; operator then
  approved wiring it up over shelving it.
---

# Wire the odds-movement/odds-snapshot candle computation into the live MDPS driver

## What's actually true (verified against live code, not the catalog doc's prose)

The `/codex/02-data/sports-data-types-catalog.md` correction banner (2026-08-15) describes the TARGET architecture —
`odds_horizon_bucket` "absorbs `odds_snapshot`/`odds_movement` as dimensions of itself (a `computation_type` column
distinguishing snapshot-LOCF vs movement-OHLC)" — but this is the intended design, not confirmed production
behavior. Checked directly:

- `reprocess_sports_odds.py` (`market-data-processing-service/scripts/`) is the **only** scheduled Cloud Run job for
  sports MDPS (daily Cloud Scheduler trigger, rolling 3-day window). It imports and calls only
  `SportsBucketAssignmentAdapter().process_to_bucketed_df(raw_df)`.
- `grep -rln "SportsOddsMovementAdapter(\|SportsOddsSnapshotAdapter(" --include="*.py"` across the entire fleet
  (excluding tests) returns hits **only inside the two adapter modules themselves** — no production script, Cloud
  Run job, CLI handler, or scheduler invokes either class.
- `SportsOddsMovementAdapter` (`odds_movement_adapter.py`) computes a genuine OHLC aggregation of `home_odds` —
  `open`/`high`/`low`/`close` = first/max/min/last within an interval, `trade_count` = observed-tick count. This is
  architecturally identical in kind to any other fleet OHLCV candle, just sports-specific. `SportsOddsSnapshotAdapter`
  computes the LOCF (point-in-time) form. Both are correctly implemented per the catalog doc's own "Snapshot vs Candle
  Discriminator" section — they are just never called.

Net: the "candles for acceleration" view the operator expected already exists in code and is correct; it has simply
never been given a live entry point.

## Decision

**Wire it up** (operator, 2026-08-20) — not retire. The catalog doc's target model (single `odds_horizon_bucket`
type, `computation_type` discriminating `bucket`/`snapshot`/`movement`) stays the right shape; what's missing is
actually invoking `SportsOddsMovementAdapter`/`SportsOddsSnapshotAdapter` from a live driver and writing their output
under that model.

## Follow-up

- [x] [DATA] P2. Scope how the movement/snapshot computation should be driven in production: either extend
      `reprocess_sports_odds.py` to also invoke `SportsOddsMovementAdapter`/`SportsOddsSnapshotAdapter` per the
      existing bucket-assignment cadence, or give them their own scheduled entry point if their natural cadence
      differs from bucket assignment's. Confirm the `DependencyChecker.check_sports_raw_source_captured` staleness
      guard (already shared by all three per the catalog doc) applies correctly to whichever path is chosen. —
      market-data-processing-service@e4b1f71aca (supersedes the c2de48b3b8 first cut — see the 2026-08-20
      remediation Progress Log entry below; that commit's own text describing "a fully independent second pass" is
      now WRONG and superseded, not just superficially outdated). Extended `reprocess_sports_odds.py` (own Cloud
      Run job, same schedule) rather than a separate entry point: movement/snapshot's calendar-interval cadence
      (fixed hourly buckets within the raw day, anchored to the actual `date_str`, see
      `odds_movement_snapshot_driver.py`) is architecturally distinct from bucket assignment's kickoff-relative
      horizons but shares the identical upstream dependency + shard key. A 10-angle review of the first cut found
      that running them as a genuinely INDEPENDENT second pass (as originally shipped) created real correctness
      bugs — see the remediation entry — so the final design MERGES all three computations into ONE per-date
      worker (`_process_sports_odds_one_date`) sharing a single raw-odds read + a single `prepare_tick_data()`
      call, not two sequential passes.
- [x] [DATA] P2. Confirm the output write path matches the catalog's target model — one row per
      (fixture, market, outcome, venue, snapshot-time/interval) written under `data_type=odds_horizon_bucket` with
      `computation_type` set to `snapshot`/`movement` (not the old standalone `odds_snapshot`/`odds_movement`
      data_type names) — per the catalog's "Snapshot vs Candle Discriminator" ruling, both forms mint keys via
      `canonical_writer_shaping.mdps_data_type_key(source_data_type, timeframe)`'s generic-fallback branch
      (`odds_snapshot_{tf}`/`odds_movement_{tf}`), already registered as real per-timeframe UAC contracts — confirm
      this still matches once real rows are produced, not just asserted from the doc. —
      market-data-processing-service@e4b1f71aca. Confirmed live against the real function body: neither
      `"odds_movement"` nor `"odds_snapshot"` is a key in `_DATA_TYPE_TO_MDPS_PREFIX`, so both fall through the
      generic-fallback branch exactly as the catalog claims, producing `odds_movement_1h`/`odds_snapshot_1h`
      (`MOVEMENT_SNAPSHOT_TIMEFRAME = "1h"`). **One correction to the catalog's claim**: `computation_type` is NOT a
      real `ManifestWriter.add()`/`record_*()` kwarg (verified against the live signature in
      `unified-trading-library/unified_trading_library/manifest_writer/_writer_ingest.py` — no such parameter
      exists in the v9 schema surface) — the catalog's "Schema fields" table describing it as a manifest column
      does not match the manifest writer's real kwarg surface. `computation_type` DOES land as a genuine column in
      the physical parquet output; the manifest instead discriminates the three computations via `venue`
      (movement/snapshot's coarse row uses a genuinely distinct sentinel, `ODDS_API_DERIVED`, from bucket
      assignment's `ODDS_API` — see the remediation entry's finding 1 for why `timeframe` alone was NOT a safe
      discriminator) plus `timeframe` carrying the minted `mdps_key` (`T-24h`.. for bucket assignment vs
      `odds_movement_1h`/`odds_snapshot_1h` for the other two).
- [x] [SCRIPT] P3. Once live, verify manifest rows land correctly (cluster validation, honest-coverage status rules
      per the catalog's Manifest Status Rules table) and that features-service/ml-service consumers (which read the
      `_ODDS_BUCKETED_PREFIXES` path prefix per the catalog's "Consumer inventory" section) pick up the new
      `computation_type=movement`/`snapshot` rows without needing a separate migration. (repo: features-service,
      ml-service) — **Consumer-code half DONE, live-verification half still open (split below).** Confirmed live
      2026-08-20 that the answer was NO (both existing readers hardcode a `bucketed.parquet` filename filter that
      excludes the new files) and shipped dedicated readers to close the gap:
      `features-service@c158b0845f` (new `gcs_reader_movement_snapshot.py::read_movement_snapshot_odds` — a
      SEPARATE module, not an addition to `gcs_reader.py`, which was already at the 900-line file-size cap) and
      `ml-service@8a909a3be4` (new `SportsFeatureLoaderMixin.read_movement_snapshot_odds` classmethod). Both are
      deliberately separate readers rather than a widened filter on the existing `bucketed.parquet` readers — the
      schemas are incompatible (bucketed.parquet = wide pivot of raw ticks with `horizon_name`/
      `bm_minutes_to_kickoff`/`home_odds`; movement/snapshot = a `CandleOutput`-shaped aggregate with
      `timestamp`/`open`/`high`/`low`/`close`/`computation_type`) — concatenating them would silently NaN-pad every
      existing consumer of `read_bucketed_odds`. Live end-to-end verification (real GCS write + manifest read-back
      for a real date) was NOT performed — genuinely open, tracked as its own todo below.
- [ ] [SCRIPT] P3. Run `reprocess_sports_odds.py --dry-run` against a real recent date range to sanity-check the
      merged bucket-assignment/movement/snapshot worker end-to-end against live raw odds (no writes); if that looks
      correct, a small real `--force` range for one date, verified via manifest read-back, to confirm real rows
      land and the loss guard / stale-shard reconcile behave correctly against production data. Not run as of the
      2026-08-20 remediation session either — flagged explicitly rather than claimed done. (repo:
      market-data-processing-service)

## Progress Log

- **2026-08-20**: doc authored recording the operator's live decision; verification (driver code + fleet-wide grep)
  done in the same session before the decision was asked for, per this workspace's "verify before presenting"
  convention.
- **2026-08-20 (later same day)**: wired up per the operator decision — `market-data-processing-service@c2de48b3b8`
  (new `odds_movement_snapshot_driver.py` + `reprocess_sports_odds.py` second independent per-date pass +
  `CandleAdapterRegistry.register()` TypeVar fix in `base_adapter.py`, needed because its prior non-generic
  `type[BaseCandleAdapter]` return annotation was erasing every adapter subclass's own attributes for any caller
  outside the class's own methods). Full `quality-gates.sh` green (ruff/basedpyright/pytest, 87.84% coverage, 9
  pre-existing basedpyright errors unchanged, 0 new). Shipped via quickmerge, landed on `live-defi-rollout`. Todos 1
  and 2 done with evidence above; todo 3 split — the features-service/ml-service consumer-compatibility check is
  DONE and found a real gap (new follow-up todo below); live end-to-end GCS verification was not attempted this
  session and stays open.
- **2026-08-20 (remediation, same day)**: `c2de48b3b8` went through a 10-angle independent code review before it
  had ever run in production (no live state to migrate) and the review found real, serious bugs — the operator
  authorized a full remediation pass. Rewrote the movement/snapshot integration rather than patching it:
  - **finding 1 (highest priority — could have corrupted the ALREADY-CORRECTLY-RUNNING bucket-assignment
    pipeline)**: the movement/snapshot coarse manifest row shared bucket assignment's own `venue=ODDS_API`
    identity, differing only by `timeframe` — a dimension bucket assignment's own pre-flight
    `ManifestWriter.lookup()` never specifies (verified live against `unified-trading-library`: an OMITTED
    `row_key` column is a WILDCARD match, not "must be empty"). Under "last-written row wins" this could have made
    bucket assignment's resume-skip read a movement/snapshot row's `capture_status` and silently skip a date it
    never actually captured. Fixed with a genuinely distinct venue sentinel
    (`_MANIFEST_VENUE_MOVEMENT_SNAPSHOT_AGGREGATE = "ODDS_API_DERIVED"`) that both sides' lookups always specify.
  - **findings 6/9 (architecture)**: merged bucket assignment + odds_movement + odds_snapshot into ONE per-date
    worker (`_process_sports_odds_one_date`) sharing a single raw-odds read + a single `prepare_tick_data()` call,
    replacing the prior two-SEQUENTIAL-pass design (was ~doubling GCS reads/CPU across a full historical
    backfill). Movement/snapshot candle-day boundaries are now anchored to the actual `date_str` being processed
    (`process_to_candles(..., anchor_date=...)`, a new keyword-only param on both adapters) instead of a
    per-instrument majority-vote over tick timestamps, which could tag a sparse instrument's candles onto the
    wrong calendar day near a UTC-midnight boundary.
  - **findings 2/3 (phantom captured with zero rows)**: a derive that produces candles but writes zero shards
    (every group dropped by a blank/NaN `league_id`) is no longer reported `captured`; the `league_id` guard moved
    upstream to `odds_movement_snapshot_driver.py::_instrument_groups` (matching the existing
    `fixture_id`/`bookmaker_key` guard pattern) with a warning log, instead of silently coercing to the literal
    string `"nan"` three layers downstream of where it was first seen.
  - **findings 4/7 (missing loss guards)**: both the `raw_df.empty` AND zero-candle paths now run
    loss-guard-then-stale-shard-reconcile, matching bucket assignment's own zero-row path, instead of an
    unconditional absence claim with no stale-shard cleanup.
  - **finding 5 (loss-guard zombie exemption)**: movement/snapshot's own candle-level loss guard can never carry
    `bm_time`/`fetch_utc` (a candle is an aggregate, not a raw tick), so it can never correctly apply the
    zombie-tick exemption bucket assignment's own guard has. It is now overridden by bucket assignment's
    raw-level, zombie-aware verdict for the SAME date (computed from the SAME raw/prepared frame in the merged
    worker) when that verdict found no unjustified loss — see `_movement_snapshot_write_allowed`'s docstring.
  - **finding 8 (reader gap)**: shipped dedicated readers in the two consuming repos (see the todo above) instead
    of leaving it as a documented gap.
  - **finding 10 (reuse)**: `_write_grouped_shard_files`/`_read_existing_shards` are now shared, parametrized
    primitives both bucket assignment and movement/snapshot call, instead of near-verbatim copies.
  - **findings 11-13 (cleanup)**: removed the now-redundant `prepare_odds_tick_data` wrapper (the method it wrapped
    was made public in the SAME original commit), defined the movement/snapshot computation-type pair once
    (`MOVEMENT_SNAPSHOT_COMPUTATION_TYPES`) instead of 5 hand-typed literal tuples, fixed a stale docstring
    reference.
  - New tests cover every finding directly, including a simulation of `ManifestWriter.lookup()`'s real matching
    semantics proving the two coarse row keys can never cross-match (finding 1), the phantom-captured/zero-shards
    case (finding 2), the blank-league_id case (finding 3), and the loss-guard override logic (finding 5). Full
    `quality-gates.sh` green in all three repos (market-data-processing-service: 2399 passed, 87.88% coverage, 9
    pre-existing basedpyright errors unchanged, 0 new; features-service and ml-service: full suites green, 0 new
    basedpyright errors). Shipped via quickmerge:
    `market-data-processing-service@e4b1f71aca`, `features-service@c158b0845f`, `ml-service@8a909a3be4`. All
    landed on `live-defi-rollout`.
  - **Still open, honestly**: live end-to-end verification against real production GCS/manifest (no `--dry-run` or
    real write was exercised in this remediation session either) — tracked as its own todo above, not claimed
    done.
