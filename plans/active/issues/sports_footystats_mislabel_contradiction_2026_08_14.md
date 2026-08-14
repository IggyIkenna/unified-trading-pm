---
doc_type: issue
title:
  Track C footystats venue mislabel — completion-state CONTRADICTION between sessions (2026-07-27 claimed 0 stale rows,
  2026-08-14 live census finds 19,782 real shards through TODAY) + a previously-unexamined LADBROKES_UK/SPORT888 casing
  gap under the same footystats-derived odds_horizon_bucket shape
summary: >-
  Dispatched to execute sports_consolidated_closeout_2026_07_19.md's Track C "venue vocabulary cleanup" todo
  (casing/aliasing re-stamp + the footystats legacy-bundle mislabel, venue=ODDS_API->FOOTYSTATS, 42,476 rows). Live
  measurement (2026-08-14, this session) found the premise contradicted by the corpus's own history, plus one genuinely
  new, previously-untouched population. (1) `sports_consolidated_native_ao_extract_2026_07_25.md`'s 2026-07-27 Progress
  Log claims this exact population was migrated and verified clean: "removed 42,476 old-venue rows, added 42,476
  new-venue rows, VERIFY stale_remaining=0" and "FOOTYSTATS 42,476 rows -- all matching the raw-tick counts exactly."
  But a fresh live census against the SAME manifest index today finds `venue=ODDS_API`/`pipeline_mode=batch_footystats`
  still holding 19,782 shards (19,469 `captured`, real non-empty data, `source=footystats`), with dates running through
  2026-08-14 -- i.e. TODAY -- while `venue=FOOTYSTATS` itself shows 0 captured rows (independently corroborated by
  `sports_taxonomy_p2_migration_2026_08_08.md`'s own 2026-08-14 slot-26 closure note). The two states cannot both be
  true of a one-time historical batch job; the date range running through today points at an unfixed WRITER still
  emitting new objects under the wrong stamp daily, not stale residue. (2) A day BEFORE the 2026-07-27 rename executed,
  the archived `sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md` investigation (status: still `open`)
  had already measured that a straight rename-to-FOOTYSTATS is the WRONG fix for this exact population -- 56.40% of the
  footystats `(date, league)` cells already exist under `batch_odds_api`, so a 1:1 relabel creates DUPLICATE manifest
  rows; the operator-ruled correct fix is a de-cased PURGE, still open as that doc's own unchecked P0 todo. The
  2026-07-27 session that executed the rename does not appear to have read that finding. (3) New, previously-unexamined:
  `venue=LADBROKES_UK`/`SPORT888` ALSO appear under `pipeline_mode=batch_footystats` (`source=footystats`,
  `instrument_type=MATCH_ODDS`/`OVER_UNDER_*`, `data_type=odds_horizon_bucket`) -- a THIRD GCS/manifest shape distinct
  from both the raw-tick shape the 2026-07-27 restamp covered and the `processed_candles/` derived-candle shape
  `sports_venue_restamp_derived_candle_gap_2026_07_27.md` covered (resolved 2026-08-03). Measured: LADBROKES_UK 25,645
  shards / 2,454,668 rows / 570 days (2023-03-31..2026-04-14); SPORT888 96,239 shards / 9,857,007 rows / 1,350 days
  (2020-06-06..2026-04-14). No prior effort has touched this population.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [data-correctness, sports, venue-mapping, manifest, footystats, ssot-contradiction, writer-bug, casing, investigation]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/archive/2026_08/sports_venue_restamp_derived_candle_gap_2026_07_27.md,
    /plans/active/sports_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: sports_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
assigned_vm: planning
source:
  [
    "sports_satellite_ao_dispatch_batch13_2026_08_13.md todo 4 (Track C venue vocabulary cleanup), dispatched
    2026-08-14, slot-30",
    "Live read_availability_index census against gs://market-data-tick-sports-prd-central-element-323112, 2026-08-14",
  ]
context_scope:
  [
    market-tick-data-service/scripts/sports/restamp_sports_bookmaker_venue_2026_07_27.py,
    market-tick-data-service/scripts/sports/census_track_c_venue_restamp_targets_2026_07_27.py,
    market-tick-data-service/scripts/sports/manifest_swap_venue_restamp_2026_07_27.py,
    /plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
  ]
---

# Track C footystats mislabel: completion contradiction + a new bookmaker-casing gap

## What I found

**1. Completion-state contradiction (SSOT violation).**

| Source                                                             | Claim                                                                                                                                                               | Date       |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `sports_consolidated_native_ao_extract_2026_07_25.md` Progress Log | `venue=ODDS_API`/`batch_footystats`: 0 stale rows remaining (42,476 removed, 42,476 `FOOTYSTATS` rows added, `VERIFY stale_remaining=0`)                            | 2026-07-27 |
| This session, live `read_availability_index` census                | `venue=ODDS_API`/`pipeline_mode=batch_footystats`: **19,782 shards, 19,469 `captured`** (real data, `source=footystats`), date range through **2026-08-14** (today) | 2026-08-14 |
| `sports_taxonomy_p2_migration_2026_08_08.md` slot-26 closure note  | `venue=FOOTYSTATS`: 0 captured rows of any data_type                                                                                                                | 2026-08-14 |

Both cannot be true of a one-time historical migration. The date range on the still-populated
`ODDS_API`/`batch_footystats` rows running through **today** is the strongest signal: this reads as an **unfixed
writer/backfill path still emitting new objects under the wrong stamp daily**, not leftover residue from before the
2026-07-27 rename. The 2026-07-27 session's own tooling only ever touched the historical objects present _at that time_
(16,970 objects) — nothing in this corpus shows a writer-side fix (e.g. to whatever job produces
`pipeline_mode=batch_footystats` + `venue=ODDS_API` shards) that would stop new mis-stamped objects from continuing to
land. This is a hypothesis, not yet confirmed — the writer/job itself has not been located in this session.

**2. The rename-to-FOOTYSTATS approach was already determined to be the WRONG fix, one day before it was executed.**

`sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md` (archived, `status: open` — its correctness finding
was never closed even though the doc itself is filed under `archive/`) measured, on 2026-07-17: a straight
`venue=ODDS_API`→`FOOTYSTATS` rename/move is **not** a clean operation — 56.40% of the footystats `(date, league)` cells
already exist under `batch_odds_api` (the correct home, reached via a separate read-split-merge that doc DID execute and
verify). A 1:1 rename therefore creates **duplicate** manifest rows for content already correctly attributed elsewhere.
The operator-ruled correct fix for the remainder is a **de-cased PURGE** of the mis-stamped rows+objects, still that
doc's own open, unchecked P0 todo. The 2026-07-27 session that executed the FOOTYSTATS rename
(`sports_consolidated_native_ao_extract_2026_07_25.md`) does not cite or appear to have read this finding — it treated
the population as a simple casing/alias rename, the same class as `LADBROKES_UK`→`LADBROKES`, which it is not.

**3. New finding — a third, previously-untouched population with the same casing/alias defect.**

`venue=LADBROKES_UK` and `venue=SPORT888` also appear under `pipeline_mode=batch_footystats`, `source=footystats`,
`instrument_type=MATCH_ODDS`/`OVER_UNDER_1_5`/`OVER_UNDER_2_5`/`OVER_UNDER_3_5`/`OVER_UNDER_4_5`,
`data_type=odds_horizon_bucket` — a derived-odds shape, structurally distinct from both:

- the raw-tick shape (`instrument_type=ODDS`/`data_type=TRADES`, `pipeline_mode=batch_odds_api`) the 2026-07-27
  `restamp_sports_bookmaker_venue_2026_07_27.py` tool covers, and
- the `processed_candles/` derived-candle shape (`arbitrage_opportunity`/`odds_horizon_bucket`/`odds_movement`/
  `odds_snapshot` under MDPS's own root prefix) `sports_venue_restamp_derived_candle_gap_2026_07_27.md` covers (resolved
  2026-08-03, slot-13).

Measured (live census, this session):

| venue        | shards | row_count sum | date range                            |
| ------------ | ------ | ------------- | ------------------------------------- |
| LADBROKES_UK | 25,645 | 2,454,668     | 2023-03-31 .. 2026-04-14 (570 days)   |
| SPORT888     | 96,239 | 9,857,007     | 2020-06-06 .. 2026-04-14 (1,350 days) |

No prior investigation or tooling in this corpus has scoped, sized, or touched this population.

## Why it matters

This is real, live production sports odds data (>12.3M rows combined for the new LADBROKES_UK/SPORT888 finding alone)
still carrying the un-folded bookmaker-casing alias identified as a data-correctness defect back in the original Track C
finding. The ODDS_API/FOOTYSTATS population is a genuine SSOT contradiction between two "done" claims in the corpus's
own history, on ground a THIRD active plan (`sports_taxonomy_p2_migration_2026_08_08.md`) is concurrently working today
— dispatching yet another worker to re-run the existing FOOTYSTATS rename script would very likely repeat the
already-identified wrong fix (creating duplicate manifest rows) rather than resolve it.

## Recommended decision

1. **Do NOT re-run `restamp_sports_bookmaker_venue_2026_07_27.py --venue FOOTYSTATS`** — it was already determined
   (2026-07-17, one day before it was actually run) to be the wrong fix for this population.
2. Route ODDS_API/FOOTYSTATS resolution through the currently-active `sports_taxonomy_p2_migration_2026_08_08.md` plan
   (already working overlapping ground, closed an adjacent todo today) rather than a second independent effort — this
   doc is a pointer/handoff, not a competing claim on that ground.
3. For LADBROKES_UK/SPORT888 under `batch_footystats`/`odds_horizon_bucket`: before building a restamp tool, verify (per
   the original Track C todo's own UNIBET_UK/SMARKETS caution) that these are genuinely a casing/alias duplicate and not
   a content-distinct feed under this specific derived shape — a live content comparison, same method already used to
   disprove the UNIBET fold.

## Todos

- [ ] [DIAG] P1. Identify the writer/backfill job that produces `pipeline_mode=batch_footystats` + `venue=ODDS_API`
      objects (dates through 2026-08-14) and determine whether it needs a writer-side fix to stop the ongoing mis-stamp,
      vs. this being a one-off re-population this session mis-measured. Cross-reference
      `/plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md`'s still-open PURGE todo
      before choosing rename vs. purge vs. writer-fix. (repo: market-data-processing-service or wherever the footystats
      capture job lives)
- [ ] [REVIEW] P2. Reconcile the completion-state contradiction between
      `sports_consolidated_native_ao_extract_2026_07_25.md` (2026-07-27: claims 0 stale `ODDS_API`/`batch_footystats`
      rows) and this doc's 2026-08-14 measurement (19,782 real shards) — most likely writer-recurrence (see todo above),
      but state it explicitly once confirmed rather than leaving two "done" claims standing.
- [ ] [DATA] P2. Live-content-verify whether `LADBROKES_UK`/`SPORT888` under `batch_footystats`/`odds_horizon_bucket`
      are a genuine casing/alias duplicate (safe to fold, mirroring the existing `SPORTS_VENUE_FOLD` entries) or a
      content-distinct feed (like UNIBET_UK/UNIBET_EU turned out to be) before building any restamp tooling for this
      shape. (repo: market-tick-data-service)
- [ ] [CODE] P3. If todo 3 confirms a genuine casing/alias duplicate: build a restamp tool mirroring
      `restamp_sports_bookmaker_venue_2026_07_27.py`'s proven pattern, scoped to
      `instrument_type=MATCH_ODDS|OVER_UNDER_*`/`data_type=odds_horizon_bucket`/`pipeline_mode=batch_footystats`, and
      execute + manifest-swap for the ~121,884 shards / ~12.3M rows measured above. (repo: market-tick-data-service)
