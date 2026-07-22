---
doc_type: issue
title:
  "MTDS sports: 1,266,874 pipeline_mode=batch_api_football rows (incl. 7,248 genuinely `captured`) present in the
  raw-tick manifest today, 2026-07-22 -- ~19+ days after the 2026-06-24 operator-ruled wipe, writer never disabled"
summary:
  "Found while scoping K1/K2 casing-migration completeness (sports_master_closeout_2026_07_21.md, sixth wave) -- a broad
  manifest query for lowercase data_type=trades/instrument_type=odds rows in the MTDS sports raw-tick index
  (market-data-tick-sports-prd) turned up 1,286,319 rows, far exceeding K1/K2's real batch_odds_api scope (373,296).
  Investigated before assuming anything: 1,265,534 of those are pipeline_mode=batch_api_football. Per
  market-tick-data-service/scripts/wipe_api_football_sports_odds_2026_06_24.py's own docstring, api_football is NOT a
  sanctioned bookmaker-odds source for MTDS ('no MTDS odds adapter, no SOURCE_PRIORITY key... every source=api_football
  row in the MTDS sports manifest is odds-like wrong-source data') and the operator ruled 2026-06-24 to WIPE EVERYTHING
  source=api_football from the MTDS sports manifest+GCS (that run dropped 1,398,423 rows + deleted 231,532 objects).
  Today's population (1,266,874 total batch_api_football rows in the same manifest, of which 1,265,534 sit at the exact
  wiped shape data_type=trades/instrument_type=odds) has `attempted_at`/`written_at` reaching 2026-07-13 -- 19+ days
  after the wipe cutoff -- meaning whatever writer produced the original 1.4M-row population was never disabled, and has
  been re-accumulating rows for nearly 3 weeks. capture_status breakdown of the lowercase trades/odds subset:
  empty_confirmed=1,200,270 (94.8%), attempted_failed=58,016 (4.6%), captured=7,248 (0.57%, real data, data-dates
  2020-08-24..2025-04-11 -- i.e. backfill-shaped, not new-day captures). Exact writer call site NOT pinpointed in this
  pass (grep for the literal pipeline_mode/source string across market_tick_data_service/ turned up only READERS
  (sports_catalog_reader.py, for a DIFFERENT bucket/surface -- instruments-service fixtures_schedule reference data, not
  MTDS raw tick) and league-ID-resolution helpers, not a manifest-writing call site) -- flagged as the concrete next
  step, not resolved here. Likely related to (but a DISTINCT manifest surface from) the already-tracked
  sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md, which documents an
  analogous nightly-re-seeded api_football population on the INSTRUMENTS-SERVICE (IS) sports index -- that doc's
  127,018-row finding is IS-side (instruments-store-sports); this finding is MTDS-side (market-data-tick-sports-prd), a
  different bucket, different capture_status distribution (mostly empty_confirmed/attempted_failed, not
  expected_unattempted), and a materially different scale on the `captured` (real-data) tail. Possibly the same root
  cause (an api_football cron/writer never disabled after the ruling), possibly two independent leaks -- unconfirmed."
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [api-football, wrong-source, sports, mtds, manifest, operator-ruling, data-correctness, re-accumulation]
related:
  [
    plans/active/sports_master_closeout_2026_07_21.md,
    plans/active/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md,
    plans/active/issues/mtds_sports_api_football_blank_source_2026_06_28.md,
    plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md,
  ]
created: 2026-07-22
parent_epic: sports_master
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: unknown
assigned_vm: NA
execution_scope: local-only
source: [sports_master_closeout_2026_07_21.md sixth wave, 2026-07-22]
resolved_by:
locked_by:
---

## Why this is NOT a K1/K2 scope item

K1 ("emit UPPER at the LIVE writer") named a single, specific writer function -- `_build_sports_shard_path`
(`venue_fetch.py:871-900`) -- as "the currently-running writer" to fix; it is the ODDS_API adapter's shard-path builder,
`pipeline_mode=batch_odds_api`. K2 ("migrate the historical lower-case rows") inherits that same writer's scope by
construction (the migration tool + manifest-swap report are keyed off objects `migrate_sports_casing_ 2026_07_22.py`
actually copied -- all `batch_odds_api`). Both are now fully shipped and verified complete for that scope: 0 remaining
lowercase rows, 373,297 canonical rows, in `pipeline_mode=batch_odds_api` (verified 2026-07-22, see the sixth-wave
Progress Log in `sports_master_closeout_2026_07_21.md`).

The original 2026-07-19/20 K2 scope estimate ("~1.8M `trades` rows, 91.5% of the bucket") did not filter by
`pipeline_mode` and so conflated the true `batch_odds_api` population with this `batch_api_football` population (and a
small `batch_polymarket_clob` population, 20,785 rows, ALL `capture_status=empty_confirmed` -- zero real data, almost
certainly the already-tracked cross-AG prediction-bleed residual documented elsewhere in
`sports_master_closeout_2026_07_21.md`, not a new finding). Casing-fixing a population that is (a) a different,
unidentified writer, (b) 99.4% non-data bookkeeping rows, and (c) already operator-ruled OUT of the canonical sports
odds model entirely would be pointless at best and would mask this actual finding at worst. This issue exists so that
"decide explicitly" question from the original K2 todo has an honest, evidence-based answer instead of a silent scope
narrowing.

## What actually needs doing (not attempted in this pass -- real investigative work, own risk profile)

1. Find the write-path that stamps `pipeline_mode=batch_api_football` + `data_type=trades`/`instrument_type=odds`
   captures/attempts into the MTDS sports manifest (grep across `market_tick_data_service/` for the literal string
   turned up only unrelated readers -- the writer likely constructs `pipeline_mode` from an enum/source variable rather
   than a hardcoded literal, or lives in a script/cron not yet checked, e.g. an `af-backfill-*` VM fleet mirroring the
   one named in `api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md`).
2. Confirm whether it is still actively running today (last measured `attempted_at`=2026-07-13; re-check).
3. Per the 2026-06-24 operator ruling (still standing, no reversal found for the MTDS-side wipe specifically -- unlike
   the footystats ODDS decision which WAS reversed 2026-06-27, a different data_type/source pair), disable the write
   path, then re-run (or extend) `wipe_api_football_sports_odds_2026_06_24.py` for the re-accumulated population.
4. Decide the fate of the 7,248 genuinely `captured` rows specifically (real backfilled historical data, data-dates
   2020-08-24..2025-04-11) -- wipe with the rest per the standing ruling, or carve out if there's a reason they're
   legitimate.

## Evidence (measured 2026-07-22, live MTDS sports index read)

```
pipeline_mode=batch_api_football total rows:                1,266,874
  lowercase data_type=trades/instrument_type=odds subset:    1,265,534
    capture_status=empty_confirmed:                          1,200,270  (94.8%)
    capture_status=attempted_failed:                             58,016  (4.6%)
    capture_status=captured (REAL DATA):                          7,248  (0.57%)
  attempted_at / written_at range:                    2026-05-05 .. 2026-07-13
  captured-subset data-date range:                    2020-08-24 .. 2025-04-11
  rows with data-date AFTER the 2026-06-24 wipe cutoff:              120

pipeline_mode=batch_polymarket_clob total rows:                 20,785
  ALL capture_status=empty_confirmed, venue=KALSHI, source=polymarket_clob
  -- zero real data; almost certainly cross-AG prediction-bleed residual, not this issue's scope.
```
