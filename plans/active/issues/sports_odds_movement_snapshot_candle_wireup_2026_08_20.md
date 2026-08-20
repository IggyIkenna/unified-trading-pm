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

- [ ] [DATA] P2. Scope how the movement/snapshot computation should be driven in production: either extend
      `reprocess_sports_odds.py` to also invoke `SportsOddsMovementAdapter`/`SportsOddsSnapshotAdapter` per the
      existing bucket-assignment cadence, or give them their own scheduled entry point if their natural cadence
      differs from bucket assignment's. Confirm the `DependencyChecker.check_sports_raw_source_captured` staleness
      guard (already shared by all three per the catalog doc) applies correctly to whichever path is chosen. (repo:
      market-data-processing-service)
- [ ] [DATA] P2. Confirm the output write path matches the catalog's target model — one row per
      (fixture, market, outcome, venue, snapshot-time/interval) written under `data_type=odds_horizon_bucket` with
      `computation_type` set to `snapshot`/`movement` (not the old standalone `odds_snapshot`/`odds_movement`
      data_type names) — per the catalog's "Snapshot vs Candle Discriminator" ruling, both forms mint keys via
      `canonical_writer_shaping.mdps_data_type_key(source_data_type, timeframe)`'s generic-fallback branch
      (`odds_snapshot_{tf}`/`odds_movement_{tf}`), already registered as real per-timeframe UAC contracts — confirm
      this still matches once real rows are produced, not just asserted from the doc. (repo:
      market-data-processing-service, unified-api-contracts)
- [ ] [SCRIPT] P3. Once live, verify manifest rows land correctly (cluster validation, honest-coverage status rules
      per the catalog's Manifest Status Rules table) and that features-service/ml-service consumers (which read the
      `_ODDS_BUCKETED_PREFIXES` path prefix per the catalog's "Consumer inventory" section) pick up the new
      `computation_type=movement`/`snapshot` rows without needing a separate migration. (repo: features-service,
      ml-service)

## Progress Log

- **2026-08-20**: doc authored recording the operator's live decision; verification (driver code + fleet-wide grep)
  done in the same session before the decision was asked for, per this workspace's "verify before presenting"
  convention.
