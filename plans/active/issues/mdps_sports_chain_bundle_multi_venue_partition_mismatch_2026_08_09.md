---
doc_type: issue
title:
  "SPORTS chain-bundle candle writes derive ONE venue from row 0 of a genuinely multi-bookmaker combined DataFrame,
  causing structural [partition_mismatch] rejects for any match with odds from more than one bookmaker"
summary: >-
  Re-running the exact force+skip verification Finding 5 of
  mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md was dispatched for (day=2026-04-14,
  odds_horizon_bucket, after the staleness-guard blocker in
  mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check_2026_08_09.md was fixed) shows the staleness guard
  is now correctly bypassed (0 hits), but 0 `[partition_mismatch]` rejects was NOT achieved: 78 rejects across
  write@15m/write@1h. Finding 5's own fix (market-data-processing-service@551ca82) genuinely improved the situation (the
  partition venue is no longer unconditionally the sport-token "FOOTBALL") but did not fix the underlying structural bug
  — `_process_chain_timeframe` legitimately combines ALL bookmakers for one match into a single DataFrame, and
  `_build_candle_output_path`'s fallback derives ONE venue from row 0 of that combined frame, which is wrong for every
  OTHER bookmaker's rows whenever a match (the overwhelmingly common case for SPORTS odds aggregation) has odds from
  more than one bookmaker.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, data-correctness, partition-mismatch, candle-write, chain-bundle, venue-derivation]
related:
  [
    /plans/active/issues/mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md,
    /plans/archive/2026_08/issues/mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check_2026_08_09.md,
  ]
created: "2026-08-09"
author: mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check-6de668ad5496 (slot-31, data_engineering)
source: >-
  Discovered while re-running Finding 5's prescribed verification (todo 2 of
  mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check_2026_08_09.md), 2026-08-09, VM
  mdps-backfill-sports-pipelinecheck-20260809-222203-d0c755 (force leg).
resolved_by:
locked_by:
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
sequential: true
context_scope:
  [
    /plans/active/issues/mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md,
    market-data-processing-service/market_data_processing_service/app/core/candle_write_mixin.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers_chain.py,
  ]
---

# SPORTS chain-bundle candle writes: one venue derived from row 0 of a genuinely multi-bookmaker batch

## What I found

Re-ran the exact verification Finding 5's `[CODE] P2` todo (in
`mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md`) was dispatched for, now that the
staleness-guard blocker (`mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check_2026_08_09.md`, fixed by
`market-data-processing-service@d653a42`) no longer prevents the run:

```
pipeline_e2e_check.py --day 2026-04-14 --asset-group SPORTS --data-types odds_horizon_bucket
```

VM `mdps-backfill-sports-pipelinecheck-20260809-222203-d0c755` (force leg), `EXIT_STATUS=1`.

**Staleness guard: CONFIRMED FIXED** — 0 hits of "SPORTS staleness guard" in `run.log` (was the original blocker;
`d653a42` resolved it).

**`[partition_mismatch]`: NOT 0** — 78 reject events (39 at write@15m, 39 at write@1h; write@4h/24h did not individually
error, though the e2e-check driver reports all 4 timeframe-cells `failed` uniformly because the whole VM exited
nonzero). Sample:

```
write@15m: StreamingParquetWriter pre-write validation failed: [partition_mismatch] 9 row(s) inconsistent with
partition_path 'day=2026-04-14/asset_group=sports/venue=DRAFTKINGS/instrument_type=MATCH_ODDS/data_type=odds_horizon_bucket_15m':
venue mismatch in 'FOOTBALL:BETSSON:MATCH_ODDS:SERIE_B:2026-27:US_CATANZARO_1929-MODENA::HOME': partition declares
DRAFTKINGS, id has BETSSON

write@1h: StreamingParquetWriter pre-write validation failed: [partition_mismatch] 8 row(s) inconsistent with
partition_path 'day=2026-04-14/asset_group=sports/venue=PINNACLE/instrument_type=OVER_UNDER_2_5/data_type=odds_horizon_bucket_1h':
venue mismatch in 'FOOTBALL:MATCHBOOK:OVER_UNDER_2_5:CHAMPIONSHIP:2026-27:SOUTHAMPTON-BLACKBURN::OVER': partition
declares PINNACLE, id has MATCHBOOK
```

Both matches Finding 5 cited (`US_CATANZARO_1929-MODENA`, `SOUTHAMPTON-BLACKBURN`) are still affected — but by DIFFERENT
bookmaker pairs than Finding 5's original repro (that repro's exact SPORT888/BETONLINEAG/CORAL/UNIBET cells do NOT
reappear in this run's error set; `551ca82` genuinely fixed those specific rows). 6 distinct wrong-venue pairs observed
this run: DRAFTKINGS/BETSSON, CASUMO/BETSSON, MATCHBOOK/BETONLINEAG, PINNACLE/MATCHBOOK, BETONLINEAG/PINNACLE,
VIRGINBET/CASUMO — all on the same two matches, all `MATCH_ODDS`/`OVER_UNDER_*`/ `ASIAN_HANDICAP_*` instrument_types.

**Root cause, precisely located**:

1. `live_workers_chain.py::_process_chain_timeframe` (chain-bundle SPORTS odds path) legitimately groups tick data by
   `instrument_key` and processes EACH bookmaker's instrument separately through the adapter — but then
   `pl.concat(all_candles, how="vertical_relaxed")` **combines every bookmaker's candles for the whole file into ONE
   DataFrame**, returned as a single `candles_df`.
2. That combined multi-bookmaker `candles_df` flows through `_process_all_timeframes` →
   `_write_or_record_empty_timeframe` → `_write_candles` as **one write call** — there is no per-venue grouping between
   "process" and "write".
3. `candle_write_mixin.py::_build_candle_output_path` (lines ~279-286, post-`551ca82`) derives the partition's `venue=`
   segment from `input_venue` when truthy and `category != SPORTS` (correctly gated off for SPORTS by `551ca82`), else
   falls back to `candles_df["instrument_id"][0]` — **row 0 of the combined, genuinely multi-bookmaker frame**. Since
   ONE partition path is derived for the WHOLE batch but the batch spans MANY real bookmakers, every row whose bookmaker
   differs from row 0's is a guaranteed `[partition_mismatch]` reject.

`551ca82` fixed the degenerate case where `input_venue` was the sport token ("FOOTBALL") stamped on 100% of rows
(guaranteed mismatch for every row). Gating that shortcut off for SPORTS exposed the SAME underlying "one venue for a
multi-venue batch" defect one level down, in the row-0 fallback — now only rows that happen to share row 0's bookmaker
succeed, and everyone else still rejects. This is why some of Finding 5's original repro cells now pass (their row-0
bookmaker happened to be a match) while a different subset of rows in the SAME matches now fail.

## Why it matters

SPORTS odds aggregation is fundamentally multi-bookmaker per match (that is the entire point of the
`odds_horizon_bucket` chain-bundle adapter) — a match with odds from only ONE bookmaker is the unusual case, not the
norm. This bug is therefore structural, not date-specific: essentially any `odds_horizon_bucket` candle-write force run
for any day with multi-bookmaker matches will drop a large fraction of rows to `[partition_mismatch]` (this run: 78
reject events across just 2 matches / 2 timeframes). It blocks Finding 5's own done-when (0 partition_mismatch rejects)
from ever being reachable without a deeper fix than `551ca82` — and, more broadly, it means SPORTS
`odds_horizon_bucket`/`odds_snapshot`/`odds_movement` candle output for multi-bookmaker matches is silently incomplete
(each rejected row never reaches its own partition; whether it's retried at a corrected partition or genuinely lost
depends on downstream retry-shape, not audited here).

## Recommended decision

The fix needs to move the venue-partitioning boundary from "whole chain file" to "per-bookmaker-group" — a write call
(and therefore a partition path) may only ever cover rows that share one real venue. Two shapes:

- **A (recommended)**: In `_process_chain_timeframe`, instead of `pl.concat`-ing every instrument's candles into one
  frame and returning it for a single downstream write, group the per-instrument candle frames by their resolved venue
  (available at line ~669's `inst_info.get("venue")`) and either (a) return multiple `(venue, candles_df)` groups and
  have `_process_all_timeframes`/`_write_or_record_empty_timeframe` write one file per group, or (b) have
  `_process_chain_timeframe` itself call `_write_candles` per venue-group directly, bypassing the current single-call
  contract. (a) is more consistent with the existing single-call-per-timeframe shape but is a larger signature change
  through `_process_all_timeframes`; (b) is more localized but breaks the current "process returns a DataFrame, caller
  writes it" separation.
- **B**: Keep the single combined write, but change `_build_candle_output_path`'s fallback so a multi-venue `candles_df`
  raises/routes to a distinct typed failure instead of silently picking row 0 — this stops the SILENT wrong-partition
  write but does not fix the underlying incompleteness (rows still don't reach GCS); only useful as an interim safety
  net while (A) is implemented, not a real fix on its own.

## Todos

- [ ] [CODE] P1. Implement Option A (or an operator-ruled equivalent) so SPORTS chain-bundle candle writes route each
      bookmaker's rows to their own venue-partitioned file instead of combining all bookmakers into one write with one
      derived venue. Done-when: a from-scratch
      `pipeline_e2e_check.py --asset-group SPORTS --data-types     odds_horizon_bucket` force run against day=2026-04-14
      produces 0 `[partition_mismatch]` rejects. (repo: market-data-processing-service)
- [ ] [DATA] P2. Once the above lands, re-run the same verification and flip Finding 5's `[CODE] P2` todo in
      `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md` with this run's evidence (0
      partition_mismatch rejects for the SPORT888/BETONLINEAG/CORAL and UNIBET cells specifically, plus confirm no NEW
      mismatch pairs appear). (repo: market-data-processing-service)

## Progress Log

- 2026-08-09 (slot-31, data_engineering,
  `mdps_sports_staleness_guard_ambient_deployment_env_blocks_e2e_check-6de668ad5496`): filed while re-running Finding
  5's prescribed verification after the staleness-guard blocker was fixed — confirmed the guard fix (0 hits) but the
  verification's own done-when (0 partition_mismatch) is NOT met; root-caused to the row-0-of-a-combined-multi-venue-
  batch fallback in `_build_candle_output_path`, one level deeper than `551ca82`'s fix. Did not fix inline —
  restructuring the process/write boundary in `live_workers_chain.py` is a real code-design change, not a config/
  low-effort fix. Left Finding 5's `[CODE] P2` todo unchecked (its done-when still unmet) and did not flip it.
- 2026-08-09 (slot 11, `data_engineering`): Dispatched todo 2 (`-05aa5ad81aad`), but its own text ("Once the above
  lands...") gates it on todo 1, which is still `status: dispatched` (in-flight to another slot, `-494586d72f17`), not
  yet landed in code (confirmed via `git log` on `live_workers_chain.py`/ `candle_write_mixin.py` — no commit past
  `551ca82`). Added missing `sequential: true` (mirrors the fix pattern used for the sibling MTDS reader-gap doc) so the
  dispatcher serializes todo 1 before todo 2 instead of re-offering this same premature dispatch. Skipped
  `reason_code: GATED`, no code changed.
