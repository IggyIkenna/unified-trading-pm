---
doc_type: issue
title: >-
  Sports odds_horizon_bucket/arbitrage_opportunity candle shards fail to write when a batch mixes MATCH_ODDS and
  MATCH_ODDS_LAY rows under one StreamingParquetWriter partition (1,998 live rows/day, 2026-07-25/26)
summary: >-
  Discovered as a side effect of the free-text `error_reason` census
  (`sports_shard_enumeration_cartesian_blowup_2026_07_20.md` §2.5 update, 2026-07-27). 1,998 sports manifest rows
  (BETFAIR_EX_EU / BETFAIR_EX_UK / MATCHBOOK / SMARKETS, `data_type ∈ {odds_horizon_bucket_1h, arbitrage_opportunity}`,
  dated 2026-07-25/2026-07-26 — still recurring daily) are `attempted_failed` because UTL's
  `StreamingParquetWriter._run_pre_write_checks` rejects the batch: the partition path's declared `instrument_type`
  (e.g. `match_odds_lay`) disagrees with the `instrument_type` embedded in some rows' `instrument_id` (e.g.
  `match_odds`) within the SAME batch. Root-cause HYPOTHESIS (code-read, not yet independently verified against a live
  failing batch): `market_data_processing_service/app/core/canonical_writer_shaping.py::_infer_instrument_type` locks
  the partition's `instrument_type` from the FIRST sampled row at `open_candle_streaming_writer` time (docstring: "the
  partition instrument_type MUST agree with the per-row instrument_id -- the StreamingParquetWriter validates the two
  against each other"), but the caller's per-shard grouping key
  (`market_data_processing_service/app/core/live_workers_streaming.py`'s `_streaming_write_per_tf` / `type_candles`
  grouping) may not split MATCH_ODDS (back) and MATCH_ODDS_LAY rows into separate shards before opening one writer -- if
  a later chunk in the same open writer carries the OTHER instrument_type, every row in that chunk fails validation and
  the whole shard's write is rejected. This is a NEW manifest-write failure with real data-loss consequence (the shard's
  candles never land), distinct from (and now cleanly surfaced by, rather than masked by) the error_reason free-text bug
  fixed in market-data-processing-service@da98dc7.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, odds, partition-mismatch, streaming-writer, data-correctness, mdps]
related:
  [
    /plans/archive/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
  ]
created: 2026-07-27
last_updated: 2026-07-29
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
resolved_by: market-data-processing-service@1390312
source: >-
  Surfaced during sports_satellite_ao_dispatch_batch3_2026_07_25.md's "[DIAG] Determine whether the free-text
  error_reason pattern ... is still live-writing today" todo — a by-product finding from the census script
  (market-tick-data-service/scripts/sports_error_reason_free_text_census_2026_07_27.py), not the todo's own subject.
depends_on: []
---

> **🟢 ARCHIVED 2026-07-29 — ACKED-INTO-CODE.** Already fixed by `market-data-processing-service@1390312` (2026-07-27
> 08:12 UTC, shipped under a sibling finding's investigation) before this doc was even filed the same day — verified
> live 2026-07-29 that `_group_batches_by_own_type` + its regression test
> (`tests/unit/test_streaming_write_group_by_type.py`) are present and passing.

# Sports odds_horizon_bucket/arbitrage_opportunity partition_mismatch — MATCH_ODDS vs MATCH_ODDS_LAY

## What I found

The `market-data-tick-sports-prd` census (see the sibling doc's §2.5 update) surfaced 1,998 `attempted_failed` rows
(1,976 distinct free-text `error_reason` values before the fix in market-data-processing-service@da98dc7, all with the
SAME structural shape) whose message is a `StreamingParquetWriter` pre-write `partition_mismatch` rejection. Two
representative examples (venue/league/fixture redacted for brevity, full text in the sibling doc):

```
[partition_mismatch] 7 row(s) inconsistent with partition_path
'day=2026-07-25/asset_group=sports/venue=BETFAIR_EX_UK/instrument_type=MATCH_ODDS_LAY/data_type=odds_horizon_bucket_1h':
instrument_type mismatch in '...': partition declares match_odds_lay, id has match_odds
```

All 1,998 rows are dated 2026-07-25 or 2026-07-26 (the manifest's 2 most recent days at census time) — this is an
actively-recurring daily failure, not a one-off historical artifact.

## Why it matters

Every one of these shards is a genuine write FAILURE — the candle data for that (venue, league, fixture, timeframe)
combination on that day never lands in GCS. Before market-data-processing-service@da98dc7, this failure was doubly
invisible: the manifest correctly marked the shard `attempted_failed` (so it wasn't silently missing), but the
`error_reason` was an unclassified free-text sentence that no automated coverage/alerting consumer could route on —
functionally as opaque as a blank reason. Now that the error_reason is classified (`MALFORMED_ROW_KEY`), the FAILURE
ITSELF is still there — only its visibility/classification improved. The underlying write bug is unfixed.

## Recommended decision

- [x] ✅ [DIAG] P2. **ALREADY DONE — found already-shipped 2026-07-29 while triaging this doc.** Confirmed by direct
      code read: `_streaming_write_per_tf`'s pre-fix behavior accumulated every batch for a timeframe and derived the
      write partition's `instrument_type` from just the FIRST batch, force-writing every other batch (possibly a
      different real type, e.g. MATCH_ODDS vs MATCH_ODDS_LAY) under that same partition — exactly this doc's root-cause
      hypothesis, confirmed true. Root-caused and fixed under a sibling finding's own investigation
      (`mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md` Update 5's third bug), not re-derived here.
- [x] ✅ [CODE] P2. **ALREADY DONE — `market-data-processing-service@1390312`** ("fix(mdps): split chain-streaming write
      by per-batch instrument_type when no real chain root exists", 2026-07-27 08:12:34 UTC).
      `_group_batches_by_own_type` (`live_workers_streaming.py:481-507`) now groups batches by each batch's OWN inferred
      `instrument_type` whenever there is no genuine chain root (the sports legacy-sentinel `ticks.parquet` case),
      writing one file per type instead of force-combining MATCH_ODDS and MATCH_ODDS_LAY under one partition; a true
      chain (options_chain/futures_chain/DeFi reserves, single shared type) is unaffected, byte-identical to pre-fix
      behavior. Regression test `tests/unit/test_streaming_write_group_by_type.py` (`TestGroupBatchesByOwnType`) proves
      MATCH_ODDS/MATCH_ODDS_LAY split into separate groups (using the exact real crash order, MATCH_ODDS_LAY first)
      while same-market batches with multiple fixtures stay combined — verified present and passing in the current
      worktree. No new code shipped by this session — the fix predates this doc's own filing; closed on that evidence.
