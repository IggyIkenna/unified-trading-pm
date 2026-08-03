---
doc_type: issue
title:
  "LADBROKES_UK->LADBROKES / SPORT888->BET888SPORT venue re-stamp only covers the raw-tick shape — 4 derived-candle
  data_types (arbitrage_opportunity/odds_horizon_bucket/odds_movement/odds_snapshot) still carry the old venue name"
summary: >-
  sports_consolidated_native_ao_extract_2026_07_25.md's Track C todo re-stamped the raw-tick shape
  (instrument_type=ODDS/data_type=TRADES, GCS root raw_tick_data/by_date/...) for LADBROKES_UK->LADBROKES and
  SPORT888->BET888SPORT: restamp_sports_bookmaker_venue_2026_07_27.py rewrote 24,268 + 37,722 GCS objects (byte-content
  + path), and manifest_swap_venue_restamp_2026_07_27.py relabeled 8,859 + 13,997 manifest rows, both verified 0 stale
  rows remaining. The SAME two venues also carry 4 derived-candle data_types (instrument_type=MATCH_ODDS:
  arbitrage_opportunity, odds_horizon_bucket, odds_movement, odds_snapshot — live census 2026-07-27: LADBROKES_UK 1,396
  shards/273,645 rows, SPORT888 1,184 shards/224,705 rows across these 4 types combined) that live under a COMPLETELY
  DIFFERENT GCS root prefix (market-data-processing-service's `processed_candles/by_date/day={date}/timeframe={tf}/
  data_type={dt}/venue={V}/...`, not market-tick-data-service's `raw_tick_data/`), confirmed by direct path sampling —
  the raw-tick restamp tool's prefix scan structurally cannot reach these objects. This was flagged explicitly (not
  silently dropped) in the Track C todo's own corrected scope text as needing its own follow-up tooling; this doc is
  that follow-up.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [data-correctness, sports, venue-mapping, manifest, candles, follow-up]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: sports_master
source: >-
  Live manifest census (2026-07-27, this session) against
  gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet, filtered venue in
  {LADBROKES_UK, SPORT888} & pipeline_mode=batch_odds_api, broken down by (instrument_type, data_type). GCS path
  structure confirmed via direct `list_blobs` sampling of both raw_tick_data/ (raw-tick shape only, verified) and
  market-data-processing-service's processed_candles/ path-builder convention
  (scripts/reconcile_1440_nan_placeholders.py, scripts/migrate_candle_canonical_2026_07.py).
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
assigned_role: data_engineering
resolved_by: "slot-13 (data_engineering), sports_venue_restamp_derived_candle_gap-001, 2026-08-03"
context_scope:
  [
    market-tick-data-service/scripts/sports/restamp_sports_bookmaker_venue_2026_07_27.py,
    market-tick-data-service/scripts/sports/manifest_swap_venue_restamp_2026_07_27.py,
    market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/epics/sports_master.md,
  ]
---

# sports venue re-stamp — derived-candle shape gap (LADBROKES_UK/SPORT888)

## What was measured

Live manifest census (2026-07-27), `venue in {LADBROKES_UK, SPORT888}` & `pipeline_mode=batch_odds_api`, broken down by
`(instrument_type, data_type)`:

| venue        | instrument_type | data_type             | shards | row_count_sum |
| ------------ | --------------- | --------------------- | ------ | ------------- |
| LADBROKES_UK | MATCH_ODDS      | arbitrage_opportunity | 378    | 91,080        |
| LADBROKES_UK | MATCH_ODDS      | odds_horizon_bucket   | 272    | 6,525         |
| LADBROKES_UK | MATCH_ODDS      | odds_movement         | 366    | 85,320        |
| LADBROKES_UK | MATCH_ODDS      | odds_snapshot         | 380    | 90,720        |
| SPORT888     | MATCH_ODDS      | arbitrage_opportunity | 316    | 67,680        |
| SPORT888     | MATCH_ODDS      | odds_horizon_bucket   | 254    | 5,985         |
| SPORT888     | MATCH_ODDS      | odds_movement         | 308    | 65,880        |
| SPORT888     | MATCH_ODDS      | odds_snapshot         | 306    | 65,160        |

Direct GCS sampling confirmed the raw-tick shape (`instrument_type=ODDS/data_type=TRADES`) lives under
`raw_tick_data/by_date/day={D}/pipeline_mode=batch_odds_api/asset_group=sports/venue={V}/league_id={L}/ instrument_type={ODDS|odds}/data_type={TRADES|trades}/ticks.parquet`
— the ONLY shape `restamp_sports_bookmaker_venue_2026_07_27.py`'s prefix scan (`.../venue={V}/`, no further segments)
can find, since it never recurses outside `raw_tick_data/`. The 4 derived-candle `data_type`s are produced by
market-data-processing-service's candle writer under a disjoint root prefix,
`processed_candles/by_date/day={date}/timeframe={tf}/data_type={dt}/venue={V}/[underlying={U}/]{instrument_id}.parquet`
(confirmed via `market-data-processing-service/scripts/reconcile_1440_nan_placeholders.py`'s and
`migrate_candle_canonical_2026_07.py`'s own path-building code) — a genuinely separate bucket-tree the raw-tick tool was
never going to reach.

## Why it matters

The parent plan's Track C done-when ("a corpus-wide sports venue census shows 0 rows for LADBROKES_UK/SPORT888") is only
satisfied for the raw-tick shape (confirmed 0 stale rows, 2026-07-27, this session — GCS content-rewrite + manifest-swap
both verified). A literal corpus-wide census still shows non-zero LADBROKES_UK/SPORT888 rows until these 8 candle
shards' worth of objects (1,396 + 1,184 = 2,580 GCS objects, ~547,725 combined rows across manifest metadata) are also
re-stamped. This is real, live production data (not placeholders — `arbitrage_opportunity`/ `odds_movement`/etc. row
counts are all non-zero), so leaving it un-tracked would let the venue-casing/alias drift this whole Track C effort is
closing out quietly persist in the candle layer indefinitely.

## Recommended decision

Build a companion tool mirroring `restamp_sports_bookmaker_venue_2026_07_27.py` +
`manifest_swap_venue_restamp_2026_07_27.py`'s proven read/transform/write + CAS-swap pattern, but rooted at
market-data-processing-service's `processed_candles/` prefix instead of `raw_tick_data/`, scoped to exactly the 4
`data_type`s enumerated above for `venue in {LADBROKES_UK, SPORT888}`. This is mechanically the same operation already
proven safe twice this session (copy/rewrite/verify, then a report-free live-index CAS relabel) — no new design judgment
is needed, which is why this is filed `assigned_vm: planning` rather than a human/NA judgment call.

## Todos

- [x] ✅ [DATA] P2. **Build + run the derived-candle venue re-stamp** for LADBROKES_UK->LADBROKES and
      SPORT888->BET888SPORT across the 4 `data_type`s (arbitrage_opportunity/odds_horizon_bucket/odds_movement/
      odds_snapshot). **Path-shape correction**: this doc's own "What was measured" section understated the real
      canonical path — live GCS sampling + the UTL `build_canonical_candle_path` SSOT both confirm it also carries
      `pipeline_mode=` and `instrument_type=` segments the doc's text omitted:
      `processed_candles/by_date/day={D}/pipeline_mode={pm}/timeframe={tf}/data_type={dt}/instrument_type={it}/venue={V}/{instrument_id}.parquet`.
      Content-rewrite covers THREE columns carrying the venue token (not just one) — `venue` (direct), `symbol` and
      `instrument_id` (colon-segment index 1) — confirmed by direct inspection of a real captured object. Built
      `market-data-processing-service/scripts/sports/restamp_sports_candle_venue_2026_08_03.py` (day/timeframe scope
      derived from the live manifest's distinct `(date, timeframe)` pairs, never a blind range). Verified live against
      prod: dry-run then `--apply` for both venues × all 4 data_types, 0 failed / 0 content_mismatch — LADBROKES_UK
      372+266+362+374=1,374 objects, SPORT888 308+254+304+300=1,166 objects. `market-data-processing-service@28ffed1`.
      **Done when**: satisfied — see the manifest-swap todo's fresh census below.
- [x] ✅ [DATA] P2. **Manifest-swap the same 4 data_types** for the two venues, mirroring
      `manifest_swap_venue_restamp_2026_07_27.py`'s live-index CAS relabel pattern, widened to all 4 data_types in one
      CAS pass per venue. Built
      `market-tick-data-service/scripts/sports/manifest_swap_venue_restamp_candles_2026_08_03.py`. Verified live against
      prod: LADBROKES_UK 1,674 rows removed+added, SPORT888 1,184 rows removed+added, snapshot-verified pre-write,
      post-write re-download confirms 0 stale rows for each. **Done when — satisfied**: a final combined census across
      both venues + all 4 data_types independently confirms 0 stale old-venue rows remaining, 3,578 new-venue rows now
      present. `market-tick-data-service@06cd3ca5`.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries).
- **2026-08-03T~19:30Z** (AO dispatch, slot 13, `data_engineering`) — Shipped both todos. Verified live against prod the
  doc's own claimed candle path shape was incomplete (missing `pipeline_mode=`/`instrument_type=` segments) before
  building against it — corrected via direct GCS sampling + the UTL `build_canonical_candle_path` SSOT. Built +ran
  `restamp_sports_candle_venue_2026_08_03.py` (GCS content-rewrite, `market-data-processing-service@28ffed1`) then
  `manifest_swap_venue_restamp_candles_2026_08_03.py` (manifest CAS relabel, `market-tick-data-service@06cd3ca5`) for
  both venues across all 4 data_types — 0 failed/content_mismatch throughout, final combined census confirms 0 stale
  old-venue rows, 3,578 new-venue rows present. Both repos' `quality-gates.sh` full runs green; both SHAs verified
  ancestors of `origin/live-defi-rollout`. Doc `status` flipped to `resolved`; archiving per issue-doc-lifecycle (all
  todos done, unlocked).
