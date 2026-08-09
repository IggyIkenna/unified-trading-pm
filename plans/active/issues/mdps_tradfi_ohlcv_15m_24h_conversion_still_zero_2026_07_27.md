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
  [
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
  ]
created: "2026-07-27"
author: unknown
parent_epic: tradfi_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [tradfi_satellite_ao_dispatch_batch2-001, slot-6 live verification runs 2026-07-27]
resolved_by:
locked_by:
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py,
    market-data-processing-service/market_data_processing_service/app/adapters/tradfi/ohlcv_passthrough.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
depends_on: []
# 2026-07-30 (slot-7, main ruling on BLK-c2d17da7/BLK-7abe9c2b): the "re-run
# mdps-backfill-tradfi-*" verify todo is a REAL dependency on the sibling
# "Deeper root cause" todo above it (a re-run before that fix ships is
# provably a wasted-cost negative result, confirmed twice by independent
# static-code reads) — sequential=true wires prereqs.completed_tasks in
# plan_order so the backlog dispatcher stops re-offering the verify todo to
# fresh slots until the root-cause todo actually ships. Mirrors the
# tradfi_casing_100pct_redrift_2026_07_27.md precedent for this exact shape.
sequential: true
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

- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-16, data_engineering) — `market-data-processing-service@21aa1af` + live
      re-run `mdps-backfill-tradfi-20260727-203609`.** Root-cause finding (2): trace why CME combo/chain-bundle
      `ohlcv_1m`/`ohlcv_1s` raw ticks (confirmed read via "Streaming chain bundle" log lines) never produce an
      `ohlcv_15m`/`ohlcv_24h` candle write attempt of ANY kind (no captured write, no empty_confirmed write, no WARNING,
      no ERROR) for CME. Check whether the aggregation step for `instrument_type=combo` shards is silently no-op'ing
      (e.g., an early-return on an unhandled `instrument_type` branch, a silently-empty resample/rollup producing 0
      output rows that never reach a manifest-write call at all) — this is the higher-severity finding since it produces
      NO signal whatsoever. Repo: market-data-processing-service. Done when: the exact code path that swallows the CME
      combo aggregation output is identified with file:line, a fix or an explicit loud-fail (so a future recurrence is
      never silent again) ships, and a re-run over an affected date shows a real `ohlcv_15m`/`ohlcv_24h` candle write
      attempt for CME (captured, empty_confirmed-with-evidence, or record_failed — anything but silence).

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
      full `quality-gates.sh` GREEN (`.qg_last_passed_sha=0e4f5b3`).
      **LIVE RE-RUN — done-when part 3 MET (2026-07-27 20:36–20:39 UTC).** VM `mdps-backfill-tradfi-20260727-203609`
      (SPOT, e2-standard-8, asia-northeast1-c), `--force --venues CME --data-types "ohlcv_15m ohlcv_24h" tradfi
      2026-07-20 2026-07-20`, MDPS pinned `@21aa1af`; `EXIT_STATUS=0`, rc=0, "🏁 tradfi processing complete:
      112/112 succeeded, 0 errors in 12.5s". The path that was a **totally silent no-op** (the finding's own
      definition of silence: "no captured, no empty_confirmed, no WARNING, no ERROR") is now **LOUD**: **280**
      `WARNING Chain-bundle streaming produced 0 candles for instrument_id= @ {15m,1h,4h,24h} (venue=CME
      underlying={CRUDE,ETH,COPPER,BTC,GOLD,SILVER,PLATINUM,NATGAS,WTI,…}) — recording manifest signal (was a
      SILENT skip before finding 2)` lines across 112 read chain bundles. The verbatim WARNING string is literal
      proof the VM ran `@21aa1af`. Log: `gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-tradfi-20260727-203609/run.log`.
      **HONEST NUANCE (→ P2, NOT part of this done-when):** NO manifest ROW was written, because **every** CME combo
      underlying resolved `symbols_processed=0` / **empty `instrument_id`** — the helper's guard correctly declines
      a per-shard row without a valid `instrument_id` (writing one would violate the shard-atom-identical rule).
      So the pipeline is no longer silent (280 WARNINGs where before there were zero), but the manifest stays
      row-less for CME combo pending the deeper P2 fix (why `symbols_processed=0`). My re-run CONFIRMED that deeper
      bug on real infra: 112 combo bundles read, **0** instruments resolved across all ~15 underlyings.

- [x] ✅ [DATA] P2. **DONE 2026-08-03 (slot 5, worker) — `market-data-processing-service@0671953`.** Deeper root cause
      (discovered by finding-2 investigation, slot-16 2026-07-27): CME combo produces ZERO candles in the FIRST place
      (my finding-2 fix makes that VISIBLE as `attempted_failed`, it does NOT make combo convert). Two candidate
      mechanisms, both un-fixed: (a) `_streaming_filter_slice` filters each raw slice by
      `slice_df["data_type"] == data_type`, but the requested output `data_type` (`ohlcv_15m`/`ohlcv_24h`) may not match
      the raw on-disk `data_type` column (`ohlcv_1m`/`ohlcv_1s`) → all rows dropped → `symbols_processed==0`; (b) per
      `adapters/tradfi/ohlcv_passthrough.py` `TradfiOhlcv15mAdapter` docstring, "a 1s/1m→15m aggregation writer to
      actually feed this class does NOT exist yet" — so the ohlcv_15m/24h derivation may be structurally incomplete for
      tradfi. Determine which, and whether CME combo `ohlcv_15m`/`ohlcv_24h` is SUPPOSED to convert (fix the filter /
      wire the aggregation writer) or is genuinely absent (attempted_failed is then honest-terminal, not billing-waste).
      Repo: market-data-processing-service. Cross-refs `data_completion_tradfi_2026_07_15.md` part 3/4. **EVIDENCE
      (finding-2 live re-run `mdps-backfill-tradfi-20260727-203609`, 2026-07-20, `@21aa1af`):** `symbols_processed=0`
      for EVERY CME combo underlying — 112 chain bundles read (14 symbol groups in CRUDE, 33 in COPPER, …), **0**
      instruments resolved, 0 candles at all 4 timeframes. This strongly favours mechanism (a) (the
      `_streaming_filter_slice` `data_type` mismatch drops every row → `symbols_processed==0`) and/or (b) (no 1s/1m→15m
      aggregation writer). Next: instrument the slice-filter to log pre/post-filter row counts + the on-disk vs
      requested `data_type` values for one CME combo bundle, and decide convert-vs-honest-absent.

      **MECHANISM CONFIRMED (2026-07-30, slot-7, independent static-code read against the live tree — mechanism (a),
      not (b)):** `market_data_processing_service/app/core/live_workers_streaming.py:771` resolves
      `related_data_types = getattr(adapter, "related_data_types", None)`, then `_streaming_filter_slice`
      (`:251-266`) branches: if `related_data_types` is truthy, filters `slice_df["data_type"].isin(related_types)`
      (an inclusive membership match); if falsy, falls to the strict `slice_df["data_type"] == data_type` (exact match
      against the REQUESTED output type). Grepped every TradFi ohlcv adapter in
      `app/adapters/tradfi/ohlcv_passthrough.py` (`TradfiOhlcvPassthroughAdapter`, `TradfiOhlcv1sAdapter`,
      `TradfiOhlcv1mAdapter`, `TradfiOhlcv15mAdapter` `data_type="ohlcv_15m"` at `:405`, `TradfiOhlcv24hAdapter`
      `data_type="ohlcv_24h"` at `:413`) plus `base_adapter.py` — **none define `related_data_types`** (confirmed by
      grep — zero hits in `app/adapters/tradfi/`), vs. the precedent pattern already shipped for sports/defi/prediction
      (`app/adapters/sports/odds_snapshot_adapter.py:36`, `.../arbitrage_adapter.py:36`,
      `.../bucket_assignment_adapter.py:645`, `.../odds_movement_adapter.py:36` all set
      `related_data_types: list[str] = ["odds", "trades", "ODDS", "TRADES"]`;
      `app/adapters/defi/swap_adapter.py:66` sets `["swaps", "dex_pool_swaps", "dex_swaps"]`;
      `app/adapters/prediction/trades_adapter.py:97` sets `["trades"]`). So every TradFi 15m/24h request against raw
      on-disk `ohlcv_1m`/`ohlcv_1s` rows hits the strict-equality branch and drops 100% of rows —
      `symbols_processed=0` is the DIRECT, deterministic consequence, matching the live measurement exactly. Mechanism
      (b) (missing aggregation writer) is NOT independently confirmed or ruled out by this read — the filter drop
      happens upstream of any aggregation step, so (b) may or may not also apply once (a) is fixed; the next worker
      should re-check once (a) ships. **Fix direction**: add `related_data_types: list[str] = ["ohlcv_1m", "ohlcv_1s"]`
      (or the correct raw-input set per timeframe) to `TradfiOhlcv15mAdapter`/`TradfiOhlcv24hAdapter` (and any other
      TradFi coarser-timeframe adapter with the same gap), mirroring the sports/defi/prediction pattern exactly. This
      is bounded, deterministic-outcome, AO-eligible backend work (repo: market-data-processing-service). Ruling:
      BLK-c2d17da7/BLK-7abe9c2b (main, 2026-07-30) — the sibling re-run-verify todo below is gated on this via this
      doc's new `sequential: true` frontmatter field until this fix ships.

      **FIX SHIPPED 2026-08-03 (slot 5, worker) — `market-data-processing-service@0671953`.** Added
      `related_data_types: list[str] = ["ohlcv_1m", "ohlcv_1s"]` to both `TradfiOhlcv15mAdapter` and
      `TradfiOhlcv24hAdapter` (`app/adapters/tradfi/ohlcv_passthrough.py`), mirroring the sports/defi/prediction
      pattern exactly per the 2026-07-30 static analysis's fix direction. `_streaming_filter_slice` now takes the
      inclusive `.isin()` branch for these two adapters instead of the strict `== data_type` branch, so raw
      `ohlcv_1m`/`ohlcv_1s` rows are no longer dropped when the requested output is `ohlcv_15m`/`ohlcv_24h`. 4 new
      regression tests added to `tests/unit/test_tradfi_adapters.py`: 2 assert the class attribute is declared
      correctly on each adapter, 1 proves at the actual `_streaming_filter_slice` call site (imported from
      `live_workers.py`'s `LiveOrchestrationMixin`) that raw `ohlcv_1m` rows now survive the filter for an
      `ohlcv_15m` request. Full `quality-gates.sh` green (twice — see note below), 45/45 `test_tradfi_adapters.py`
      tests pass. Shipped via `quickmerge --agent --files` to `live-defi-rollout`, verified `0671953` is an ancestor
      of `origin/live-defi-rollout`. **Process note**: ran `quality-gates.sh` once BEFORE committing (wrong order per
      `unified-trading-pm/agents/worker.md` § 5a — the sentinel keys to HEAD, so running QG on a dirty tree writes a
      sentinel for the PRE-fix SHA); caught it via the sentinel/HEAD mismatch check before shipping, committed, then
      re-ran QG on the correct committed SHA (`0671953`, sentinel matched) before Pass 2. Mechanism (b) (missing
      1s/1m→15m aggregation writer, flagged as un-ruled-out by the 2026-07-30 analysis) was NOT separately
      re-investigated this pass — the fix here only addresses mechanism (a); whoever runs the P2 re-run-verify todo
      below should watch for whether `symbols_processed` becomes nonzero (mechanism (a) alone sufficient) or stays
      zero even with rows surviving the filter (mechanism (b) also applies, needs its own fix).

- [x] ✅ [SCRIPT] P2. **DONE 2026-08-03 (slot 8, worker).** Once finding (1) or (2) ships, re-run
      `mdps-backfill-tradfi-*` (`--force`) over 2026-07-20..2026-07-24 and confirm a non-zero `Candles` count in the
      processing summary AND a non-zero `rows_added` in the next manifest-consolidator pass, closing out
      `data_completion_tradfi_2026_07_15.md` line-629's part-1/part-2 deploy verification with the positive evidence
      this issue's own verification runs could not produce.

      **Prereq confirmed shipped**: `market-data-processing-service@0671953` (the "Deeper root cause" mechanism-(a) fix
      below) verified as an ancestor of MDPS HEAD before dispatch.

      **Re-run**: refreshed the stale floating MDPS tarball (pinned `e90e5be1`, one commit behind — the documented
      manual-refresh gap from this doc's own 2026-07-27 Progress Log trap 3 recurred) via
      `create-code-tarballs.sh --include market-data-processing-service`, confirmed the new floating manifest pins
      `0671953`, then launched `mdps-backfill-tradfi-20260803-104812` (SPOT, e2-standard-8,
      `--force --data-types "ohlcv_15m ohlcv_24h" --venues "CME NASDAQ NYSE" tradfi 2026-07-20 2026-07-24 full`,
      `MDPS_TARBALL_SHA=0671953e9cc496dad47486b7d71c44c70a6838f7` pinned explicitly).

      **Done-when MET — both halves positive**:
      - **Candles**: nonzero on all 5 dates (33,926 / 21,014 / 20,990 / 12,465 / 11,316 = **99,711 total**), vs. the
      prior verification runs' `Candles: 0` across every date. Success=345/Failed=813 instrument-day attempts across
      the run.
      - **rows_added**: directly confirmed by re-querying the canonical
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` AFTER triggering
      `uts-prod-manifest-consolidator-market-data-tradfi` (Cloud Run Job execute) — **788 new `capture_status=captured`
      rows** now present, matching the exact scope (venue∈{CME,NASDAQ,NYSE}, date 2026-07-20..24, data_type∈{ohlcv_15m},
      `service_name=market-data-processing-service`), byte-identical to this VM's own pre-consolidation per-VM shard
      (`_index/per_vm/mdps-backfill-tradfi-20260803-104812.parquet`, 788 rows, 100% `captured`) — proving the
      consolidator genuinely merged this run's output into the canonical index, not just a coincidental pre-existing
      count.

      **Two NEW, previously-undocumented blockers found live during this re-run** (neither was part of finding (1)/(2)'s
      scope; the mechanism-(a) fix correctly let real rows reach the write step, which is what SURFACED these — same
      pattern as this doc's own history): see the two new todos below. One (`ohlcv_24h` naming) is FIXED as part of this
      todo (bounded, in-file, same investigation); the other (combo/futures_chain crash) is deliberately NOT fixed here
      pending an operator/owner judgment call — see its todo for why.

- [x] ✅ [DATA] P2. **DONE 2026-08-03 (slot 8, worker) — `unified-api-contracts@079d48ff`.** NEW finding from the
      2026-08-03 re-run (`mdps-backfill-tradfi-20260803-104812`): `ohlcv_24h` shard writes crashed "No SchemaContract
      registered" for **100% of every TradFi instrument_type** (future/equity/ETF/option alike — 579/813 errors this
      run), not just the CME-combo blocker findings (1)/(2) already covered. Root cause: MDPS's live write path
      (`canonical_writer_shaping.py::mdps_data_type_key`) has a pass-through branch —
      `if source_data_type.startswith("ohlcv_"): return source_data_type` — that returns an already-`ohlcv_`-prefixed
      token UNCHANGED, silently skipping `_normalise_timeframe`'s `"24h"->"1d"` translation for that branch. So TradFi's
      REAL runtime `SchemaContract` lookup key is the literal `ohlcv_24h` string the CLI/manifest/GCS paths use
      everywhere else — not `unified_api_contracts.internal.schemas._candle_contracts`'s internal `ohlcv_1d` convention
      (confirmed via direct `lookup_contract()` REPL testing + the live error text). Every tradfi
      re-aggregated-timeframe contract in that module was registered ONLY under `ohlcv_1d`, so this had ALWAYS been
      broken for every TradFi instrument_type at the daily grain — previously masked because NASDAQ/NYSE equity daily
      writes never got past the "no raw tick data" gate (finding (1)'s
      `SOURCE_RETURNED_ZERO`/`NO_RAW_TICK_DATA_FOR_SHARD` path) in any prior verification run, so `lookup_contract` was
      never actually invoked for `ohlcv_24h` before this CME-driven run.

      **Fix shipped**: added an `ohlcv_24h`-keyed alias (identical shape/columns, same `_build(...)` call with
      `data_type="ohlcv_24h"` instead of `_trades_key("1d")`) for `future`/`equity`/`options_chain`/`index` — the
      instrument_types `unified_api_contracts.registry.market_data_categories.VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`
      confirms legitimately carry `ohlcv_24h`. Deliberately did NOT touch the shared `mdps_data_type_key` pass-through
      logic itself (lower blast radius — many other asset_group callers rely on that exact branch; the registry-side
      alias is the narrow fix). 4 new unit tests in `test_mdps_candle_contracts.py` (`test_tradfi_ohlcv_24h_alias_resolves`
      parametrized future/equity, + options_chain/index variants), 303/303 tests pass, full `quality-gates.sh` green.
      Shipped `unified-api-contracts@079d48ff`, verified ancestor of `origin/live-defi-rollout`.

      **Not yet re-verified live** — the fix landed AFTER the 2026-08-03 re-run above (which is what surfaced it), so no
      fresh VM run has confirmed `ohlcv_24h` now writes successfully for future/equity. Next worker touching this AG
      should fold a `--data-types ohlcv_24h` check into their next scheduled tradfi verification pass rather than
      spending a dedicated VM run solely to confirm this narrow fix — low cost, not urgent enough to justify a solo run.

- [x] ✅ [CODE] P2. **DEFAULT-RULED 2026-08-06, option (a): scope the CLI/orchestration layer to exclude
      instrument_type=combo/futures_chain from 15m/24h requests up-front — market-data-processing-service@68f95f6.**
      `[CODE]` tag (was `[OPERATOR]`) — cleanest option per the doc's own framing; verified no downstream consumer
      (features-service, strategy-service, ml-service) expects combo-grain 15m/24h candles, and UAC
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` confirms these combinations are excluded. NEW finding from the
      2026-08-03 re-run: `instrument_type=COMBO` shard writes crash "No SchemaContract registered" for BOTH `ohlcv_15m`
      and `ohlcv_24h` (432/813 errors this run, 100% of all COMBO attempts) — CME calendar-spread/combo chain-bundle
      candles. Unlike the `ohlcv_24h` finding above, this is **NOT a registry gap to fix** —
      `unified_api_contracts.registry.market_data_categories.VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("tradfi", "combo")]`
      and `[("tradfi","futures_chain")]` are BOTH tradfi-owner-verified (2026-06-08/06-22) as deliberately
      `{"trades","ohlcv_1s","ohlcv_1m","tbbo"}` — explicitly EXCLUDING `ohlcv_15m`/`ohlcv_24h`, per that registry's own
      comment: "Kept tight (no mbp_10/24h) to avoid over-fanning cells the writer never captures." Registering a
      SchemaContract for combo at these timeframes (as this todo's sibling P2 fix does for future/equity) would make the
      schema layer CONTRADICT that audited policy — reverted an initial attempt to do exactly that during this
      investigation once the policy was found (see this doc's commit history / the reverted diff in
      `unified-api-contracts@079d48ff`'s predecessor working state).

      **Open question needing an owner/operator judgment call** (why this is a new todo, not a same-turn fix): the MDPS
      `--data-types "ohlcv_15m ohlcv_24h"` backfill CLI is currently ATTEMPTING these writes for CME combo shards at all
      — per the policy above, it should not be. Two candidate fixes, either plausible:
      (a) the CLI/orchestration layer should exclude `instrument_type=combo`/`futures_chain` from 15m/24h requests
      up-front (scope the request correctly, matching the verified-valid-data-types policy) — cleanest, but needs to
      confirm no downstream consumer actually expects combo-grain 15m/24h candles to exist;
      (b) the write path should catch `SchemaContractNotFoundError` for this specific KNOWN-EXCLUDED
      (instrument_type, data_type) combination and degrade to a loud WARNING + graceful skip (mirroring finding (2)'s
      `_record_streaming_empty_timeframe` pattern) instead of an unhandled crash that aborts the whole date's subprocess
      (`rc=1`, per this re-run's `subprocess-per-date: date=<D> rc=1 (FAILED)` lines) — lower-risk but treats a policy
      violation as routine rather than fixing the root scoping bug.
      Repo: market-data-processing-service (CLI/orchestration scoping) or market-data-processing-service (crash
      handling), depending on which direction is chosen. Evidence: `mdps-backfill-tradfi-20260803-104812` run.log,
      432 `No SchemaContract registered ... instrument_type='COMBO'` lines across `ohlcv_15m`+`ohlcv_24h`.

- [ ] [DATA] P3. NEW finding from the 2026-08-03 re-run: `instrument_type=ETF` (52 errors) and `instrument_type=OPTION`
      (34 errors, singular — distinct from the already-registered `options_chain` per-underlying bundle grain) have
      **ZERO SchemaContract coverage at ANY timeframe** in `unified_api_contracts.internal.schemas._candle_contracts`
      (not even the raw `ohlcv_1m`/`ohlcv_1s` pass-through other instrument_types get in `contracts.py`), despite
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE[("tradfi","etf")]` explicitly listing `ohlcv_1m`/`ohlcv_15m`/
      `ohlcv_24h`/`trades`/`tbbo`/`mbp_10` as valid (MVP TradFi scope per workspace CLAUDE.md: BlackRock spot ETFs
      IBIT/ETHA on NASDAQ) — so unlike the combo/futures_chain finding above, ETF genuinely NEEDS registration, it's not
      a policy conflict. `("tradfi","option")` is `frozenset()` in that same registry (a LEAF grain that should roll up
      into `options_chain`, same shape as `("tradfi","combo")` vs `("tradfi","futures_chain")`) — so its crash is likely
      the SAME class of caller-scoping issue as the combo/futures_chain todo above, not a registration gap. Left unfixed
      here (out of this todo's bounded scope; ETF needs a real schema-shape decision — same per-instrument shape as
      `future`/`equity`, or its own — before registering, and OPTION needs the same caller-scoping investigation as
      combo/futures_chain). Repo: unified-api-contracts (ETF registration) + market-data-processing-service (OPTION
      caller-scoping investigation). Evidence: same run.log, 52 `instrument_type='ETF'` + 34 `instrument_type='OPTION'`
      "No SchemaContract registered" lines.

      **BLOCKED (slot-11, 2026-07-30) — do not dispatch until the P2 "Deeper root cause" todo above ships.** Static
      code read confirms mechanism (a) from that todo is STILL live, unfixed: `market-data-processing-service`
      `app/core/live_workers_streaming.py:771` resolves `related_data_types = getattr(adapter, "related_data_types",
      None)`, then `_streaming_filter_slice` (line 253-268) falls to `slice_df[slice_df["data_type"] == data_type]`
      (the requested OUTPUT type, e.g. `ohlcv_15m`/`ohlcv_24h`) whenever `related_data_types` is falsy. Grepped the
      full TradFi adapter hierarchy (`app/adapters/tradfi/ohlcv_passthrough.py`: `TradfiOhlcvPassthroughAdapter`,
      `TradfiOhlcv1sAdapter`, `TradfiOhlcv1mAdapter`, `TradfiOhlcv15mAdapter`, `TradfiOhlcv24hAdapter`) plus
      `app/adapters/base_adapter.py` — **none define `related_data_types`**, so the getattr always returns `None` for
      every TradFi timeframe adapter. Raw CME combo tick input is written with `data_type=ohlcv_1m`/`ohlcv_1s`, so the
      `== data_type` filter against a requested `ohlcv_15m`/`ohlcv_24h` output drops every row →
      `symbols_processed=0` — exactly what `mdps-backfill-tradfi-20260727-203609`'s live re-run measured. NASDAQ/NYSE
      also still lack raw tick data for the 2026-07-20..24 window per this doc's own Run-2 analysis (the tracked,
      out-of-scope phantom-seed gap). Net: a re-run now is expected to reproduce `Candles=0` for every venue in scope
      — spending real VM/GCS cost without producing the positive evidence this todo needs. Filed `/blocked`
      (`BLK-7abe9c2b`) asking whether to run anyway (negative-result confirmation) or hold until the deeper-root-cause
      fix ships; recommended holding. This todo effectively `depends_on` the P2 "Deeper root cause" todo above even
      though no formal `depends_on` field links them.

      **RE-CHECKED 2026-07-31T15:22Z (slot 14) — still genuinely blocked, re-dispatched despite `sequential: true`.**
      Independently re-verified (not just trusting the prior note): grepped
      `market_data_processing_service/app/adapters/tradfi/ohlcv_passthrough.py` +
      `app/adapters/base_adapter.py` for `related_data_types` — **zero hits**, so the "Deeper root cause" P2
      todo's fix has still NOT shipped and the strict-equality filter drop is still live. Skipping this run
      rather than reproducing the known `Candles=0` result at real VM/GCS cost. Same dispatch-ordering gap as
      this doc's `sequential: true` frontmatter is meant to prevent — a same-plan todo with a documented
      blocking dependency is still reaching dispatch ahead of the todo it depends on; worth folding into the
      `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` audit's scope if it recurs
      again on a future dispatch. No code shipped, no VM launched.

**UNBLOCKED 2026-08-09 (plan_reconciler) — the P2 "Deeper root cause" dependency has shipped and is verified LIVE.**
Direct code check (not just re-reading this doc):
`market_data_processing_service/app/adapters/tradfi/ohlcv_passthrough.py` now declares
`related_data_types: list[str] = ["ohlcv_1m", "ohlcv_1s"]` on both `TradfiOhlcv15mAdapter` and `TradfiOhlcv24hAdapter` —
commit `de8ea9f` ("fix(tradfi): declare related_data_types on ohlcv_15m/24h adapters to unblock CME combo aggregation"),
reachable on `origin/live-defi-rollout`. Per this todo's own stated dependency logic, the OPTION half (same
caller-scoping/mechanism-(a) class as combo/futures_chain) is now unblocked for dispatch. The ETF half remains
separately gated — its own text above already states ETF needs a real schema-shape registration decision unrelated to
this mechanism, not just the P2 fix.

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
  - **Lesson / trap 3 (tarball refresh, 2026-07-27)**: the MDPS tarball is NOT auto-built by CI on LDR push — the
    floating `gs://deployment-scripts-central-element-323112/code/market-data-processing-service-code.manifest.json` was
    3 commits stale (pointed at `f8cb0216`, pre-fix). The refresh is the DOCUMENTED manual step
    `bash deployment-service/scripts/vm/create-code-tarballs.sh --include market-data-processing-service`
    (vm-tarball-deployment.md § refresh cycle). Two gotchas hit: (a) the upload path needs `deployment-service/.venv`
    (imports `deployment_service.vm.gcs_upload_cli` via UTL's ADC StorageClient — the codex-mandated non-gsutil path); a
    fresh slot has no DS venv → `uv sync` in deployment-service first. (b) `SKIP_PREFLIGHT=true` to bypass the
    non-blocking UAC/UTL pyproject-floor WARNINGs. After refresh, floating + `@21aa1af` pinned tarball/manifest both
    present; all 5 core repos were clean at LDR-tip so the refresh advanced them safe-forward (UAC@25085037,
    MTDS@a6c8e29e, deployment@5b5d227d, MDPS@21aa1af; UTL skipped, already deployed).
  - **2026-07-27 20:36 UTC — live re-run LAUNCHED (in flight).** VM `mdps-backfill-tradfi-20260727-203609` (SPOT,
    e2-standard-8, asia-northeast1-c),
    `--force --venues CME --data-types "ohlcv_15m ohlcv_24h" tradfi 2026-07-20 2026-07-20 full`, MDPS_TARBALL_SHA pinned
    to `21aa1af`; launcher confirmed "all 5 tarball(s) current". 2026-07-20 = a confirmed affected date (run 2 above:
    336 "Streaming chain bundle" CME lines, zero candle output, zero WARNING/ERROR). Logs:
    `gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-tradfi-20260727-203609/` (`run.log`,
    `EXIT_STATUS`). Watchdog armed (scratchpad `watch_cme_vm.sh`, bg id byp59ywio, 45-min cap, polls VM status +
    EXIT_STATUS + preemption).
  - **2026-07-27 20:39 UTC — finding (2) COMPLETE.** VM terminal (`EXIT_STATUS=0`, self-deleted). Re-run produced **280
    loud WARNINGs** for CME `ohlcv_{15m,1h,4h,24h}` on day=2026-07-20 where before there was total silence → done-when
    part 3 ("anything but silence") MET; the verbatim WARNING string ("was a SILENT skip before finding 2") proves the
    VM ran `@21aa1af`. NO manifest row written (every CME combo underlying `symbols_processed=0` / empty
    `instrument_id`; the helper correctly declines a per-shard row without a valid shard identity) — that manifest-row
    gap is the deeper **P2**, now confirmed on real infra (112 combo bundles read → 0 instruments resolved). Finding-(2)
    flipped `- [x] ✅`; task `/done`. Watchdog `byp59ywio` exited clean (scratchpad one-off, session-isolated /
    auto-cleaned).
  - **Still open on this issue doc (NOT finding-2):** the deeper **P2** (why `symbols_processed=0` — convert-vs-honest-
    absent) and the P2 re-run-verify todo. Separate tracked todos, not part of finding-2's done-when.

- **2026-08-03 (slot 8, worker) — re-run-verify todo CLOSED, positive evidence obtained, 2 new findings tracked.**
  Confirmed the "Deeper root cause" mechanism-(a) fix (`market-data-processing-service@0671953`, mdps
  `related_data_types` on `TradfiOhlcv15mAdapter`/`TradfiOhlcv24hAdapter`) was already an ancestor of MDPS HEAD, then
  discovered the floating MDPS tarball was stale (pinned `e90e5be1`, one commit behind — the SAME documented
  manual-refresh trap from this doc's 2026-07-27 Progress Log, recurring) and refreshed it before dispatch.
  - **Re-run `mdps-backfill-tradfi-20260803-104812`** (SPOT,
    `--force --data-types "ohlcv_15m ohlcv_24h" --venues "CME NASDAQ NYSE" tradfi 2026-07-20 2026-07-24 full`,
    `MDPS_TARBALL_SHA` pinned): **99,711 total candles** across all 5 dates (vs. prior `Candles: 0` on every date) —
    mechanism-(a) confirmed genuinely working end-to-end for non-combo CME instrument_types. Triggered
    `uts-prod-manifest-consolidator-market-data-tradfi` (Cloud Run Job execute) and directly re-queried the canonical
    `_index/availability_index.parquet`: **788 new `captured` rows**, byte-identical to this VM's own per-VM shard row
    count — proving the consolidator genuinely merged real output, not a stale/ coincidental count. Both halves of the
    done-when MET; flipped `- [x] ✅`.
  - **2 NEW blockers surfaced by the SAME mechanism** (mechanism-(a) let real rows reach the write step for the first
    time, which is what exposed both): (1) `ohlcv_24h` — 100% failure for EVERY tradfi instrument_type, root-caused to
    `mdps_data_type_key`'s pass-through branch skipping `"24h"->"1d"` timeframe normalisation for already-`ohlcv_`-
    prefixed tokens. **Fixed same-session** (`unified-api-contracts@079d48ff`, verified ancestor of origin) — a narrow,
    low-risk registry-side `ohlcv_24h` alias for future/equity/options_chain/index, NOT a change to the shared writer
    logic. (2) `instrument_type=COMBO` crashes at 15m/24h — investigated further and found this is NOT a registry gap:
    `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` deliberately, verifiedly excludes combo/futures_chain from those
    timeframes. Initially (wrongly) added a registry entry for combo anyway before catching this — **reverted** once the
    policy was found, re-tested (303/303 tests green), then shipped only the correct future/equity/options_chain/ index
    alias. Left as a new `[OPERATOR]` todo (needs a judgment call: fix the CLI's scoping vs. catch-and-degrade in the
    write path) plus a P3 for the separately-discovered ETF/OPTION zero-coverage gap. See the two new todos above.

- **context-scout 2026-08-03**: refreshed context_scope (6 entries — swapped
  `batch_workers.py`/`live_workers_streaming.py` (Findings 1/2, both DONE) for `canonical_writer_shaping.py`,
  `ohlcv_passthrough.py`, and UAC's `market_data_categories.py` — the files central to the doc's current open work (the
  `[OPERATOR]` COMBO SchemaContract scoping call and the P3 ETF/OPTION coverage gap)).

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

# Codex SSOTs

None new — this is an implementation-bug finding against the existing honest-absence/FetchEvidence contract
(`/codex/02-data/honest-absence-downstream-handling.md`), not a contract change.
