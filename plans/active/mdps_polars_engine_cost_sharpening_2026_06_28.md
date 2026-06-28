---
doc_type: plan
title: MDPS engine cost-sharpening — pure-Polars seam + subprocess-per-date + manifest double-read fix
summary:
  "Un-defer the M-2 Polars work: replace the Polars→Pandas→Polars chain with a pure-Polars lazy path, adopt
  subprocess-per-date execution, fix the 526MB manifest double-read and the canonical-ID CLI matcher — to hit the
  audited 3x wall / 5x peak RSS / 7.8x retention wins and stop the ~15GB arena leak."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [mdps, polars, performance, memory, cost, subprocess-per-date, manifest-io, cli, refactor]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ./mdps_features_full_month_benchmark_binance_2026_06_28.md,
    ../active/mtds_file_size_refactor_2026_06_08.md,
    ../audit/results/mdps_engine_benchmark_findings_2026_05_28.md,
    ../audit/results/mdps_long_running_efficiency_SUMMARY_2026_05_28.md,
  ]
created: 2026-06-28
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 2
assigned_role: data_engineering
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on:
source: [../audit/results/mdps_engine_benchmark_findings_2026_05_28.md, ../active/mtds_file_size_refactor_2026_06_08.md]
---

# MDPS engine cost-sharpening — pure-Polars seam

"Sharpen the code so it's fast and saves cost." The 2026-05-28 audits already measured the lever: the current
**Polars→Pandas→Polars** chain is the worst of all paths; **pure-Polars lazy (scan_parquet + projection pushdown)** is
**3× faster wall, 5× lower peak RSS, 7.8× less retention**, and the current path leaks ~15 GB into Polars/PyArrow arenas
on multi-day runs. The seam is parked (deferred) in M-2 `mtds_file_size_refactor`; this plan un-defers the Polars
portion.

**Execution model:** Opus / thinking high (or xhigh for the hot loop) — a refactor across large MDPS files
(orchestrator/adapters) where engine semantics + memory behaviour must be reasoned about together; not a mechanical
sweep. Sonnet for the CLI-matcher + manifest-read sub-fixes once the engine path is in.

## The four audited fixes (in priority order)

1. **Pure-Polars data path** — replace the Polars→Pandas→Polars chain with `scan_parquet` LazyFrame + projection
   pushdown end-to-end; eager only at the write boundary. (Audit Path A vs Path C.)
2. **subprocess-per-date execution model** — current in-process is unreliable beyond ~1–2 days on 32 GB; isolate per
   date so arenas are reclaimed by process exit.
3. **Manifest double-read fix** — orchestrator double-reads the 526 MB `availability_index.parquet` per shard (32–80 GB
   allocate-then-free churn per 16-day backfill); read once / push column selection down.
4. **CLI canonical-ID matcher** — canonical `VENUE:INSTRUMENT_TYPE:SYMBOL` returns zero blobs (substring matcher
   mismatches the `=` separator); fix so canonical IDs resolve.

## Todos

- [x] ✅ [IMPLEMENT] P2. (opus/xhigh) Convert the candle aggregation path to pure-Polars lazy (scan + projection
      pushdown, group_by_dynamic), eager only at write. Delete the Pandas hop (no-tech-debt). Preserve the right-edge
      `t_close` aggregation semantics exactly. — Gate: a single-shard run produces byte-identical candles to the
      pre-refactor output (a golden-parquet diff) and lower peak RSS. — market-data-processing-service@c7e0437.
      Evidence: `_aggregate_from_15s_polars` collapsed to a single LazyFrame chain that `.collect()`s once at the end
      (closed=right/label=right semantics preserved; dead `_TIMEFRAME_FREQ_MAP` removed); 36/36 fast_candle_aggregation
      + writer_schema_preservation tests pass (golden-equivalence tests pin first/last 1m bin values, vwap recompute,
      and the constant-volume invariant at 1m/5m/15m/1h/24h); MDPS QG green (sentinel 3604451).
- [x] ✅ [IMPLEMENT] P2. Adopt subprocess-per-date as the default batch execution model (the audit's Phase 1.1
      decision); keep a flag for in-process. — Gate: a 7-day backfill completes without the multi-day RSS climb;
      per-date RSS returns to baseline between dates. — market-data-processing-service@85060ff. Evidence: parser
      `--subprocess-per-date` switched to `argparse.BooleanOptionalAction` with `default=True`; child argv builder
      appends `--no-subprocess-per-date` to prevent infinite recursion now that default=True; in-process opt-out
      preserved via `--no-subprocess-per-date` (single-date smoke / debugging / already-isolated parent). 16/16
      process_handler tests pass — new tests pin the default, the opt-out flag, the default-path dispatch via
      `_run_date_as_subprocess`, and the recursion guard. MDPS QG green.
- [x] ✅ [IMPLEMENT] P2. Fix the manifest double-read (read once, column-pruned) and the canonical-ID CLI matcher. —
      Gate: a 16-day backfill shows the manifest read once per shard; a canonical `VENUE:TYPE:SYMBOL` CLI arg returns
      the expected blobs (regression test). — market-data-processing-service@eee8433. Evidence:
      `dependency_checker.check_upstream_manifest_has_live_gap` now calls `read_availability_index(bucket,
      columns=[date,venue,data_type,capture_status,error_reason])` (UTL slim reader → only 5 columns decoded from the
      ~526 MB upstream parquet; UTL keys the slim cache by `(bucket, columns)` so the full-read cache stays warm for
      other consumers). `GCSDataSource.list_instrument_files` routes `--instrument-ids` through
      `blob_matches_any_instrument_id` so canonical `VENUE:INSTRUMENT_TYPE:SYMBOL` IDs match the hive-path
      `venue=…/instrument_type=…/symbol=…` partitions (the prior `iid in blob_name` substring returned ZERO blobs
      because the path uses `=` separators, not `:`). 67/67 data_source + dependency_checker_coverage tests pass (new
      regression tests pin the slim `columns=` kwarg and the canonical-ID → expected-blob resolution). MDPS QG green.
- [x] ✅ [TEST] P2. Golden-output equivalence tests (candle values unchanged) + a memory-regression smoke (peak RSS
      under a declared ceiling for the canary shard). — Gate: tests pass in MDPS `quality-gates.sh`. —
      market-data-processing-service@2dd13db. Evidence: golden-equivalence already landed with item 1
      (`TestLazyAggregationGoldenEquivalence` in `tests/unit/test_fast_candle_aggregation.py` pins first/last 1m bin
      values, vwap recompute, volume invariant 1m/5m/15m/1h/24h). Memory-regression smoke added as
      `TestLazyAggregatorMemoryBar` in `tests/perf/test_polars_instrument_day_memory.py` — bars set well below the
      audit's Path-A baseline with headroom (aggregator RSS growth <400MB, Python heap Δ <100MB for 9 instr × 5760 15s
      × 6 TFs); auto-enrolled in the per-shard memory regression gate in `scripts/quality-gates.sh` (120s timeout). 5/5
      perf tests pass; MDPS QG green.
- [ ] [VERIFY] P2. Re-run the Plan-7 benchmark cells (current vs this Polars path) on the real Binance full month;
      confirm the deltas land near the audited 3× / 5× / 7.8×. — Gate: benchmark table shows the improvement on a real
      full month (feeds Plan 7's cost model).
- [ ] [AGENT] P2. MDPS QG green; quickmerge `--agent --files`; update M-2 `mtds_file_size_refactor` to mark the Polars
      seam done (cross-plan flip in the same turn). — Gate: QG green; CI `quality-gates-v2` green; M-2 checkbox flipped.

## Current-state delta (audited 2026-06-28)

- **Audited baseline (2026-05-28):** current path C (Polars→Pandas→Polars) = 1.4s / 1861 MB peak / 2471 MB retention on
  the 9-instrument shard; target path A (pure-Polars lazy) = 0.5s / 344 MB / 318 MB. Engine-mixing owns the ~15 GB
  multi-day arena residue; in-process is unreliable beyond ~1–2 days on 32 GB.
- **Seam location:** parked (deferred) in M-2 `mtds_file_size_refactor`. This plan lifts ONLY the engine swap + the 3
  sub-fixes (subprocess-per-date, manifest double-read, canonical-ID matcher), not the >900-line file split.

## Notes

- Output correctness is non-negotiable: the golden-parquet diff gates every engine change — a faster path that changes a
  single candle value is a regression, not a win.
- File-size refactor (splitting the >900-line files) is M-2's separate concern; this plan touches only what the engine
  swap requires — it does not take on the full mechanical split.
