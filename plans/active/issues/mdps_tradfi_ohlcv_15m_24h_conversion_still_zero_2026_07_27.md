---
doc_type: issue
title:
  MDPS tradfi ohlcv_15m/24h conversion is STILL zero after deploying the row_key/source canonical_writer fixes — two
  NEW, orthogonal blockers found live (record_empty/FetchEvidence rejection for NASDAQ/NYSE; silent zero-candle output
  for CME combo aggregation)
summary: >-
  `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s first todo deployed the two already-shipped
  `canonical_writer.py` fixes (omit `instrument_id` for aggregated shards; thread `source` from `pipeline_mode`) via a
  clean-LDR-checkout tarball rebuild (`market-data-processing-service@3328ffd0`) and relaunched `mdps-backfill-tradfi-*`
  twice to verify. Both live runs (2026-07-13..19, 2026-07-20..24; ~5,400+ instrument-day attempts total, `--force`)
  confirm the deployed fix works as intended — ZERO occurrences of the two target errors (`MalformedRowKeyError`,
  missing-`source` rejection) across either run. But BOTH runs also show `Candles: 0` in the processing summary for
  every single date, and a post-run manifest-consolidator pass reports `rows_added: 0, verdict: empty, no_op: true` —
  meaning literally nothing new landed in the tradfi manifest from either run. Two distinct, previously-undocumented
  blockers were found live, causing this: (1) **NASDAQ/NYSE equity writes are REJECTED at the validation gate.**
  `canonical_writer` calls `manifest_writer.record_empty(reason=SOURCE_RETURNED_ZERO)` for these venues on regular
  trading days (confirmed 2026-07-13 = Monday, 2026-07-20 = Monday — not weekends) WITHOUT supplying the `FetchEvidence`
  the gate now requires to prove honest absence (`http_status in 2xx AND response_received AND rows_in_response == 0 AND
  error_signal == ""`). The gate correctly logs a WARNING and refuses the write (this is the gate working as designed —
  it is guarding against exactly the "failure masquerading as honest absence" anti-pattern) — 5,470 rejections on
  2026-07-13/14 alone, 1,180 more on 2026-07-20..24, 100% `reason=SOURCE_RETURNED_ZERO`, 100% venue NASDAQ/NYSE. The
  orchestration layer's own per-date summary counts these as `Success` (not `Failed`), so nothing surfaces this at the
  run-level metrics — only the per-row WARNING log line reveals it. (2) **CME combo/chain-bundle candles silently
  produce zero output**, with no error at all. Both runs show MDPS correctly streaming CME raw tick data (`Streaming
  chain bundle: N symbol groups in
  raw_tick_data/.../venue=CME/instrument_type=combo/data_type=ohlcv_1m/underlying=.../ticks.parquet`, hundreds of lines
  per date, all commodities/futures roots) — so the 1m/1s raw input exists and is read. But zero `ohlcv_15m`/`ohlcv_24h`
  candle files ever appear under `processed_candles/by_date/day=<D>/.../venue=CME/...` for any processed date, zero
  WARNING/ERROR lines mention CME at all, and the manifest shows no new CME rows for these dates either (a pre-existing
  broader query found only 1-2 `empty_confirmed` CME `ohlcv_24h` rows per day scattered across all history — these do
  not correspond to the dates in either verification window and were not touched by either run). This is a genuine
  silent-failure/no-signal gap — worse than (1) because there is no log line at all to find it by; it only surfaced by
  cross-checking `processed_candles/` GCS listing + the manifest-consolidator's own `rows_added: 0` verdict against the
  "Streaming chain bundle" evidence that real input existed.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-data-processing-service, market-tick-data-service, unified-trading-library]
scope: [engineer]
tags:
  [
    tradfi,
    mdps,
    canonical_writer,
    ohlcv_15m,
    ohlcv_24h,
    manifest,
    honest-absence,
    fetch-evidence,
    silent-failure,
    data-correctness,
  ]
related:
  [/plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md, /plans/active/data_completion_tradfi_2026_07_15.md]
created: "2026-07-27"
parent_epic: tradfi_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [tradfi_satellite_ao_dispatch_batch2-001, slot-6 live verification runs 2026-07-27]
resolved_by:
locked_by:
depends_on: []
---

# What I found

Deploying the two already-shipped `canonical_writer.py` fixes (row_key `instrument_id` omission for aggregated shards;
`source` threaded from `pipeline_mode`) and relaunching `mdps-backfill-tradfi-*` against two different date windows
produced ZERO new captured `ohlcv_15m`/`ohlcv_24h` cells for tradfi, despite the two specific target bugs being
confirmed fixed (no occurrences across ~5,400+ processing attempts). Two NEW, independent blockers explain why:

**Run 1** — `mdps-backfill-tradfi-20260727-183828`,
`--force --data-types "ohlcv_15m ohlcv_24h" --venues "CME NASDAQ NYSE" tradfi 2026-07-13 2026-07-19 full`. Summary:
`Success=4572, Failed=0, Skipped=0, Candles=0` across all 7 dates. 5,470 WARNING lines, 100%
`empty_confirmed manifest write failed ... reason=SOURCE_RETURNED_ZERO ... requires FetchEvidence`, 100% venue NASDAQ
(270) / NYSE (5,200), 100% `instrument_type` EQUITY/ETF. Zero CME rows were even enumerated for this window (confirmed
via direct manifest query — 0 rows any `capture_status` for CME `ohlcv_15m`/`ohlcv_24h` on 07-13/14/15) — this specific
absence is the ALREADY-TRACKED, explicitly out-of-scope "part 4" phantom-seed/expected-universe gap from
`data_completion_tradfi_2026_07_15.md`'s own 4-part diagnosis (massive-keyed seeds don't cover recent forward dates),
not a new finding.

**Run 2** — `mdps-backfill-tradfi-20260727-185026`, same flags, `tradfi 2026-07-20 2026-07-24 full` (a window chosen
specifically because a broader manifest query showed CME `ohlcv_24h` DOES have existing `empty_confirmed` rows on these
dates, unlike run 1's window). Summary: `Success=808, Failed=0, Skipped=0, Candles=0` across all 5 dates. 1,180 WARNING
lines, identical pattern (100% NASDAQ/NYSE `SOURCE_RETURNED_ZERO`/FetchEvidence rejection). This time CME WAS processed
— 336 "Streaming chain bundle" INFO lines confirm real `ohlcv_1m`/`ohlcv_1s` raw tick data was read for every
commodity/futures root (BTC, CRUDE, GOLD, COPPER, NAT-GAS variants, PLATINUM, SILVER, WTI variants, MBT, ETH) across all
5 dates — but zero CME WARNING/ERROR lines, zero new `processed_candles/` objects for CME on any of these dates, and the
post-run manifest-consolidator invocation (`_index/latest.json`, `last_run_at: 2026-07-27T18:55:46Z`) reports
`shards_scanned: 1, shards_changed: 0, rows_added: 0, verdict: "empty", no_op: true` — proving nothing landed anywhere
in the manifest from this run, for any venue.

# Why it matters

This is the actual remaining blocker on `data_completion_tradfi_2026_07_15.md`'s 4-part ohlcv_15m/24h conversion goal
(parts 1+2 of that diagnosis — row_key/source — are now confirmed fixed and deployed; this issue documents that parts
3/4 alone are NOT sufficient to explain the continued zero-conversion — there are at least two MORE blockers neither
previously diagnosed). Finding (1) is a validation gate correctly refusing a mis-classified write — but the CALLING code
(whatever in canonical_writer/orchestration_service decides to call `record_empty(reason= SOURCE_RETURNED_ZERO)` for
these equities) needs to either supply real `FetchEvidence` or call `record_failed` instead, per the gate's own error
message. Finding (2) is more serious: a `no silent placeholders` violation in the opposite direction — not a
false-positive absence stamp, but a totally silent, unsignaled non-write for a case where real input data demonstrably
exists. Neither finding was on any tracked plan before this verification pass.

# Recommended decision

- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-6, data_engineering)** — Root-cause finding (1): locate the MDPS caller that
      invokes `manifest_writer.record_empty(reason=SOURCE_RETURNED_ZERO)` for NASDAQ/NYSE equity ohlcv_15m/24h
      aggregation without supplying `FetchEvidence`. Determine whether the "zero rows" condition genuinely reflects "no
      raw tick input existed for this instrument/day" or should instead call `record_failed`. Repo:
      market-data-processing-service.

      **Root cause identified**: `market_data_processing_service/app/core/batch_workers.py`'s `_handle_empty_tick_data`
                              (the batch-mode empty-tick-data handler) unconditionally defaulted `empty_reason =
                              EmptyConfirmedReason.SOURCE_RETURNED_ZERO` for every non-SPORTS asset_group and called
                              `record_empty_for_shard(...)` (→ `canonical_writer_manifest.py:182`'s `manifest_writer.record_empty(...)`) with no
                              `fetch_evidence` — the function's own signature doesn't even accept one. This is a DERIVATION step (reading
                              already-captured raw tick parquet), not a live vendor fetch, so there is no `FetchEvidence` to supply — the call
                              always violated the `SOURCE_RETURNED_ZERO` hard-requirement (operator decision 2026-06-22,
                              `mtds_honest_absence_swallow_remediation_2026_06_10` Phase 2 KEYSTONE) the moment that gate landed. The code's
                              own pre-existing comment (`writegate_phase_3.D.5_wave3`) already stated the correct target behavior:
                              cefi/defi/tradfi instrument-day-grain empty is NOT a legitimate `empty_confirmed` state (only venue-level
                              calendar rules are) — it should flip to `attempted_failed`; `record_empty_for_shard` was only ever the
                              "conservative interim" until a catalog-aware writer-side guard (full "Wave 3", still unbuilt) could ship.

                              **Fix shipped**: (1) added a new closed-taxonomy `RecordFailedReason.NO_RAW_TICK_DATA_FOR_SHARD` value
                              (`unified-api-contracts@349795f4`, `unified_api_contracts/canonical/crosscutting/honest_coverage.py`). (2)
                              `batch_workers.py`'s `_handle_empty_tick_data` now routes cefi/defi/tradfi through `record_failed_for_shard`
                              with this reason instead of `record_empty_for_shard(SOURCE_RETURNED_ZERO)`; SPORTS is unchanged (already has its
                              own typed calendar-aware `classify_sports_empty_reason` path) — `market-data-processing-service@b6079c5`,
                              with 2 new unit tests (`test_tradfi_empty_routes_to_record_failed_not_record_empty`,
                              `test_sports_empty_still_routes_to_record_empty`) + updated docstrings/comments. Both repos: full
                              `quality-gates.sh` green, `basedpyright`/`ruff` clean.

                              **Live re-verification (Done-when satisfied)**: rebuilt the TRADFI tarball from a clean LDR checkout (both fixes
                              included) and relaunched `mdps-backfill-tradfi-20260727-194704` (`--force`, CME/NASDAQ/NYSE ohlcv_15m/24h,
                              2026-07-13 — the exact date that previously produced 5,470 rejection warnings). Result: 2,284/2,284 succeeded, 0
                              errors, **ZERO** `canonical_writer` WARNING lines (vs. the prior run's thousands) — only normal, auto-retried
                              GCS 429 backoffs. Read the VM's own per-VM manifest shard directly (`_index/per_vm/mdps-backfill-tradfi-
                              20260727-194704.parquet`, pre-consolidation ground truth — the shared consolidator's next cycle hadn't run yet):
                              **2,735 rows (135 NASDAQ + 2,600 NYSE), 100% `capture_status=attempted_failed`,
                              `error_reason=NO_RAW_TICK_DATA_FOR_SHARD`** — exactly the intended classification, correctly written, no
                              rejection. Fix confirmed working end-to-end in production.

- [ ] [DATA] P1. Root-cause finding (2): trace why CME combo/chain-bundle `ohlcv_1m`/`ohlcv_1s` raw ticks (confirmed
      read via "Streaming chain bundle" log lines) never produce an `ohlcv_15m`/`ohlcv_24h` candle write attempt of ANY
      kind (no captured write, no empty_confirmed write, no WARNING, no ERROR) for CME. Check whether the aggregation
      step for `instrument_type=combo` shards is silently no-op'ing (e.g., an early-return on an unhandled
      `instrument_type` branch, a silently-empty resample/rollup producing 0 output rows that never reach a
      manifest-write call at all) — this is the higher-severity finding since it produces NO signal whatsoever. Repo:
      market-data-processing-service. Done when: the exact code path that swallows the CME combo aggregation output is
      identified with file:line, a fix or an explicit loud-fail (so a future recurrence is never silent again) ships,
      and a re-run over an affected date shows a real `ohlcv_15m`/`ohlcv_24h` candle write attempt for CME (captured,
      empty_confirmed-with-evidence, or record_failed — anything but silence).

      **Root cause identified + fix shipped (slot-16, data_engineering, 2026-07-27) — `market-data-processing-service@21aa1af`.**
          Exact silent-swallow: `market_data_processing_service/app/core/live_workers_streaming.py`
          `_streaming_write_per_tf` — the loop's `if not tf_candles: continue` (pre-fix ~line 555) skipped a timeframe that
          accumulated ZERO candles with NO manifest write and NO log of any kind. CME combo/chain-bundle files dispatch to
          the STREAMING path (`_maybe_dispatch_chain_streaming` → `_process_chain_bundle_streaming`, because they are
          `underlying={ROOT}/ticks.parquet` chain bundles), NOT the eager path — and the eager path's per-timeframe
          `_write_or_record_empty_timeframe` (which DOES emit a signal on empty) has no streaming-path equivalent. That
          asymmetry is the silence. **Fix**: new `_record_streaming_empty_timeframe` helper emits an honest manifest signal
          per empty timeframe, mirroring `batch_workers._handle_empty_tick_data` (finding 1): SPORTS →
          `record_empty_for_shard` (calendar-aware typed reason); cefi/defi/tradfi → `record_failed_for_shard`
          (`NO_RAW_TICK_DATA_FOR_SHARD`, `attempted_failed`; `SOURCE_RETURNED_ZERO` empty would be FetchEvidence-gate
          rejected). A loud WARNING fires even in the degenerate no-`instrument_id` case (never silent again). 3 unit tests
          added (`test_empty_tf_candles_records_failed_signal`, `_sports_records_empty`, `_no_instrument_id_no_manifest_row`),
          full `quality-gates.sh` GREEN (`.qg_last_passed_sha=0e4f5b3`). **REMAINING (this todo stays open):** the done-when's
          live re-run — launch a narrow CME `mdps-backfill-tradfi-*` (`--force --venues CME --data-types "ohlcv_15m ohlcv_24h"`)
          over an affected date (e.g. 2026-07-20) once the MDPS tarball for `@21aa1af` is CI-built on LDR, and confirm the
          per-VM manifest shard now carries a real CME `ohlcv_15m`/`ohlcv_24h` `attempted_failed` row instead of silence.

- [ ] [DATA] P2. Deeper root cause (discovered by finding-2 investigation, slot-16 2026-07-27): CME combo produces ZERO
      candles in the FIRST place (my finding-2 fix makes that VISIBLE as `attempted_failed`, it does NOT make combo
      convert). Two candidate mechanisms, both un-fixed: (a) `_streaming_filter_slice` filters each raw slice by
      `slice_df["data_type"] == data_type`, but the requested output `data_type` (`ohlcv_15m`/`ohlcv_24h`) may not match
      the raw on-disk `data_type` column (`ohlcv_1m`/`ohlcv_1s`) → all rows dropped → `symbols_processed==0`; (b) per
      `adapters/tradfi/ohlcv_passthrough.py` `TradfiOhlcv15mAdapter` docstring, "a 1s/1m→15m aggregation writer to
      actually feed this class does NOT exist yet" — so the ohlcv_15m/24h derivation may be structurally incomplete for
      tradfi. Determine which, and whether CME combo `ohlcv_15m`/`ohlcv_24h` is SUPPOSED to convert (fix the filter /
      wire the aggregation writer) or is genuinely absent (attempted_failed is then honest-terminal, not billing-waste).
      Repo: market-data-processing-service. Cross-refs `data_completion_tradfi_2026_07_15.md` part 3/4.
- [ ] [SCRIPT] P2. Once finding (1) or (2) ships, re-run `mdps-backfill-tradfi-*` (`--force`) over
      2026-07-20..2026-07-24 and confirm a non-zero `Candles` count in the processing summary AND a non-zero
      `rows_added` in the next manifest-consolidator pass, closing out `data_completion_tradfi_2026_07_15.md` line-629's
      part-1/part-2 deploy verification with the positive evidence this issue's own verification runs could not produce.

# Progress Log

- **2026-07-27 (slot-16, data_engineering) — finding (2) code shipped, live re-run pending.** Fix
  `market-data-processing-service@21aa1af` (LDR): streaming chain-bundle empty-timeframe now emits an honest manifest
  signal instead of silently skipping. QG green, 3 unit tests pass. See the finding-(2) todo annotation above for the
  file:line + fix detail.
  - **Lesson / trap 1**: chain bundles (`underlying={ROOT}/ticks.parquet`) NEVER hit the eager path — they dispatch to
    streaming BEFORE the eager read (`_maybe_dispatch_chain_streaming`, `live_workers.py:264`). So finding (1)'s
    `batch_workers._handle_empty_tick_data` fix (empty raw INPUT) and the eager `_write_or_record_empty_timeframe`
    (adapter-produced-empty) both MISS combo entirely. The streaming path was the only one with no empty-signal.
  - **Lesson / trap 2**: my first hypothesis (market_state=CLOSED dropping all combo bars because streaming passes no
    `instrument_metadata`) was WRONG — `MarketStateDetector` with empty metadata returns `NORMAL` for a weekday TRADFI
    bar (only weekends/holidays → CLOSED), so weekday combo bars are NOT dropped on that basis. The zero-candle cause is
    upstream of market-state (the data_type filter or the missing 1s/1m→15m aggregation writer — see the new
    deeper-root-cause P2 todo).
  - **Resume here**: do the done-when's live re-run (finding-2 todo REMAINING) — narrow CME `mdps-backfill-tradfi-*`
    `--force --venues CME --data-types "ohlcv_15m ohlcv_24h"` for one affected date, after the MDPS `@21aa1af` tarball
    is CI-built on LDR; read the per-VM manifest shard for a CME `attempted_failed` row. Then flip finding-(2) to
    `- [x] ✅`.

# Codex SSOTs

None new — this is an implementation-bug finding against the existing honest-absence/FetchEvidence contract
(`/codex/02-data/honest-absence-downstream-handling.md`), not a contract change.
