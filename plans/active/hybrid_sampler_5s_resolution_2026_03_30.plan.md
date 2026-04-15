---
title: "Hybrid Sampler — 5s Resolution for Arb Detection"
priority: P1
status: active
owner: agent
created: 2026-03-30
---

## Context

The current sampler (`oddspapi_to_sampled_fast.py`) uses 1-minute buckets for the entire T-24h to T-0 window. This
causes two problems:

1. **Missed arbs**: An arb that opens at 14:30:12 and closes at 14:30:47 is invisible at 1-min sampling but visible at
   5s sampling.
2. **False stale rejections**: The backtest's 30s `bm_time` alignment check rejects valid arbs when two bookmakers'
   prices land in different minute buckets. At 5s resolution, both prices would be captured closer together in time and
   pass the check.

### Data Availability

- **OddsPapi**: Tick-level data (sub-second). Each bookmaker price update has a `bm_time` timestamp. OddsPapi betfair-ex
  returns 500s on historical — excluded from backfill.
- **Betfair**: 50ms tick data from historical tar, already sampled at 1-min by Rust parser. Could be re-sampled at 5s if
  we modify the Rust parser or post-process.

### Row Count Estimates

| Resolution                          | Buckets   | Estimated Rows | Notes            |
| ----------------------------------- | --------- | -------------- | ---------------- |
| 1-min (current)                     | 1,440     | 211M           | Current, working |
| 5s full 24h                         | 17,280    | ~489M          | Too large        |
| 5s last 6h                          | 4,320     | ~122M          | Feasible         |
| **Hybrid (5s last 2h + 1min rest)** | **2,760** | **~78M**       | Recommended      |

Hybrid is smaller than current 211M because join_asof only produces rows where the bookmaker actually had a price update
within the staleness window.

### Sampling Rule

- **Last value wins** (not average). If 5 ticks arrive within one 5s bucket, take the last.
- **30s staleness**: A price is valid for 30s after `bm_time`. If no update within 30s, the price is considered stale
  and excluded from arb detection.
- **Betfair floor filter**: Any exchange price <= 1.02 is filtered (market not open).

## Phases

### Phase 1: Hybrid Sampler [SEQUENTIAL]

- [x] [AGENT] P0. Update `oddspapi_to_sampled_fast.py` to support hybrid bucket grid:
  - T-24h to T-2h: 1-minute buckets (1,320 buckets) — ML features, stable prices
  - T-2h to T-0: 5-second buckets (1,440 buckets) — arb detection, fast-moving prices
  - CLI flag: `--hybrid` (default) vs `--uniform-interval N` (old behavior)
  - Note: `--hybrid` flag not explicit — hybrid is the default when `--interval` is omitted; `--interval N` is the
    legacy uniform mode.
  - join_asof with `by` parameter (already implemented) works at any resolution

- [ ] [AGENT] P0. Betfair data at 5s resolution:
  - Option A: Modify Rust parser to output at 5s intervals (changes `sample_interval_ms`)
  - Option B: Post-process `betfair_sampled.parquet` — the Rust parser already captures 1-min snapshots but the raw data
    is 50ms. Re-run parser with 5s interval for T-2h window.
  - Option C: Use the 1-min Betfair data as-is — `join_asof` will carry forward the last known Betfair price at each 5s
    bucket. Less accurate but no re-parsing needed.
  - **Recommended**: Option C for now (fast), Option A later for production.

- [ ] [AGENT] P1. Update `betfair_merge.py` to align Betfair timestamps to 5s boundaries (currently truncates to
      minutes). Trivial change: `second=(second // 5) * 5`.

### Phase 2: Backtest Updates [SEQUENTIAL after Phase 1]

- [ ] [AGENT] P0. Update `arb_rolling_backtest.py`:
  - `BM_TIME_STALENESS_MAX = 30` already set — no change needed
  - Pre-indexing by `fetch_utc` needs to handle 12x more snapshots in T-2h window
  - Consider: only run arb detection on T-2h to T-0 snapshots (skip T-24h to T-2h for arb)
  - Keep ML feature buckets at 1-min for the audit comparison

- [ ] [AGENT] P1. Performance: The backtest iterates every snapshot. With 5s buckets in the last 2h, that's 1,440 extra
      snapshots per fixture per day. Pre-filter must be fast. Consider: only check for arbs when a price actually
      changes (event-driven, not poll-based).

### Phase 3: Betfair 5s Parser [PARALLEL, lower priority]

- [ ] [AGENT] P2. Modify Rust betfair-parser `sample_interval_ms` from 60000 to 5000 for the T-2h window. Output: larger
      parquet but much more accurate for arb detection. Keep 1-min for T-24h to T-2h (or just output everything at 5s —
      disk is cheap).

- [ ] [AGENT] P2. Re-parse Betfair data.tar at 5s intervals:
      `cargo run --release -- --input data.tar --output betfair_5s.parquet --interval 5` Estimated size: 669MB × 12 =
      ~8GB (12x more rows). May need to split by date.

### Phase 4: Production [AFTER Phase 2 validated]

- [ ] [AGENT] P2. MTDS live adapter: OddsPapi WebSocket feed → 5s buckets for T-2h window. Same hybrid approach: 1-min
      for distant, 5s for close-to-kickoff.

- [ ] [AGENT] P2. Betfair streaming adapter: Already has 50ms resolution via MCM streaming. Just need to align to 5s
      buckets in the feature/arb pipeline.

## Success Criteria

1. Hybrid sampler produces ~78M rows (less than current 211M)
2. Backtest finds more arbs in T-2h to T-0 window (quantify vs 1-min baseline)
3. Fewer valid arbs rejected by staleness filter
4. Processing time stays under 5 minutes for full pipeline
5. No change to ML feature quality (T-24h to T-2h stays at 1-min)
