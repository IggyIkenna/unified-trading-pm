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
      market-data-processing-service@c2de48b3b8. Extended `reprocess_sports_odds.py` (own Cloud Run job, same
      schedule) rather than a separate entry point: verified live that movement/snapshot's calendar-interval cadence
      (fixed hourly buckets within the raw day, see `odds_movement_snapshot_driver.py`) is architecturally distinct
      from bucket assignment's kickoff-relative horizons but shares the identical upstream dependency + shard key,
      so one driver is the natural fit. Implemented as a FULLY INDEPENDENT second per-date `ThreadPoolExecutor` pass
      (own raw-odds read, own loss guard, own manifest rows) — zero changes to the existing bucket-assignment
      control flow, so this cannot regress its loss-guard/shard-isolation behaviour. The staleness guard itself
      lives in `process_handler.py`'s generic CLI path (`_sports_derived` frozenset already covers all three types)
      but this reprocessor doesn't route through that handler; movement/snapshot inherit the SAME upstream-freshness
      protection indirectly by reading the SAME `_read_raw_odds()` the bucket-assignment path already gates on.
- [x] [DATA] P2. Confirm the output write path matches the catalog's target model — one row per
      (fixture, market, outcome, venue, snapshot-time/interval) written under `data_type=odds_horizon_bucket` with
      `computation_type` set to `snapshot`/`movement` (not the old standalone `odds_snapshot`/`odds_movement`
      data_type names) — per the catalog's "Snapshot vs Candle Discriminator" ruling, both forms mint keys via
      `canonical_writer_shaping.mdps_data_type_key(source_data_type, timeframe)`'s generic-fallback branch
      (`odds_snapshot_{tf}`/`odds_movement_{tf}`), already registered as real per-timeframe UAC contracts — confirm
      this still matches once real rows are produced, not just asserted from the doc. —
      market-data-processing-service@c2de48b3b8. Confirmed live against the real function body: neither
      `"odds_movement"` nor `"odds_snapshot"` is a key in `_DATA_TYPE_TO_MDPS_PREFIX`, so both fall through the
      generic-fallback branch exactly as the catalog claims, producing `odds_movement_1h`/`odds_snapshot_1h`
      (`MOVEMENT_SNAPSHOT_TIMEFRAME = "1h"`). **One correction to the catalog's claim**: `computation_type` is NOT a
      real `ManifestWriter.add()`/`record_*()` kwarg (verified against the live signature in
      `unified-trading-library/unified_trading_library/manifest_writer/_writer_ingest.py` — no such parameter
      exists in the v9 schema surface) — the catalog's "Schema fields" table describing it as a manifest column
      does not match the manifest writer's real kwarg surface. `computation_type` DOES land as a genuine column in
      the physical parquet output; the manifest instead discriminates the three computations via the `timeframe`
      column carrying the minted `mdps_key` (`T-24h`.. for bucket assignment vs `odds_movement_1h`/`odds_snapshot_1h`
      for the other two) — a deliberate, documented substitute, not an oversight.
- [~] [SCRIPT] P3. Once live, verify manifest rows land correctly (cluster validation, honest-coverage status rules
      per the catalog's Manifest Status Rules table) and that features-service/ml-service consumers (which read the
      `_ODDS_BUCKETED_PREFIXES` path prefix per the catalog's "Consumer inventory" section) pick up the new
      `computation_type=movement`/`snapshot` rows without needing a separate migration. (repo: features-service,
      ml-service) — **PARTIAL, 2026-08-20**. Consumer-code half is DONE and the answer is NO, contrary to this
      todo's framing: read both readers' real code
      (`features-service/features_service/sports/data/gcs_reader.py::read_bucketed_odds` line ~632,
      `ml-service/ml_service/training/app/core/sports_feature_loader.py::_load_odds_event_teams` line ~267) — BOTH
      filter their `list_blobs` prefix match to `b.name.endswith("bucketed.parquet")` explicitly, not just a
      `data_type=odds_horizon_bucket/` prefix. The new writer deliberately names its output
      `movement.parquet`/`snapshot.parquet` (never `bucketed.parquet` — a DIFFERENT filename was required so
      `_delete_stale_shards`' filename-suffix-scoped reconcile could never cross-delete between the three
      computations sharing one prefix), so neither existing reader will pick up the new rows — **a real, separate
      consumer-side follow-up is needed**, tracked below. Live end-to-end verification (real GCS write + manifest
      read-back for a real date) was NOT performed this session — no live write against production GCS/manifest was
      exercised; a `--dry-run` invocation was not run either. This remains open.
- [ ] [DATA] P2. features-service `gcs_reader.py::read_bucketed_odds` and ml-service
      `sports_feature_loader.py::_load_odds_event_teams`'s blob-listing filter both hardcode
      `b.name.endswith("bucketed.parquet")` — confirmed live 2026-08-20 (see the PARTIAL todo above) that this
      EXCLUDES the new `movement.parquet`/`snapshot.parquet` files the 2026-08-20 wire-up writes under the same
      `data_type=odds_horizon_bucket/league_id={league_id}/` prefix. Widen both suffix checks (or generalize to a
      shared `{"bucketed.parquet", "movement.parquet", "snapshot.parquet"}` set / a `computation_type`-aware read
      path) so movement/snapshot rows actually reach features-service/ml-service consumers. (repo: features-service,
      ml-service)
- [ ] [SCRIPT] P3. Run `reprocess_sports_odds.py --dry-run` against a real recent date range to sanity-check the
      movement/snapshot pass end-to-end against live raw odds (no writes); if that looks correct, a small real
      `--force` range for one date, verified via manifest read-back, to confirm real rows land and the loss guard /
      stale-shard reconcile behave correctly against production data. Not run in the 2026-08-20 session — flagged
      explicitly rather than claimed done. (repo: market-data-processing-service)

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
