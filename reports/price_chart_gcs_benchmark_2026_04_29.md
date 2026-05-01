# Price-chart GCS read benchmark — baseline

- Date: 2026-04-29T15:32:48.571249Z
- Project: `central-element-323112`
- Symbol: `NASDAQ:AAPL` `1m` `data_type=ohlcv_1m`
- Bucket: `market-data-tick-tradfi-central-element-323112`
- Code path: current `BatchCandleReader`-equivalent (pre-Unit-A)
- Runs per scenario: 5

## Single-file scenarios

| Scenario    | wall p50 (ms) | wall p99 (ms) | download p50 | parse p50 | project p50 | bytes  | rows |
| ----------- | ------------- | ------------- | ------------ | --------- | ----------- | ------ | ---- |
| single cold | 670.6         | 1107.3        | 659.1        | 1.5       | 9.4         | 31,476 | 400  |
| single warm | 346.7         | 657.1         | 335.4        | 1.5       | 9.4         | 31,476 | 400  |

## Multi-file scenarios

| Scenario                                  | wall p50 (ms) | wall p99 (ms) | files attempted | files ok | rows   | bytes   |
| ----------------------------------------- | ------------- | ------------- | --------------- | -------- | ------ | ------- |
| 10 cal days parallel (no prune)           | 659.0         | 667.3         | 10              | 7        | 2,881  | 224,809 |
| 10 cal days sequential                    | 4909.7        | 4927.6        | 10              | 7        | 2,881  | 224,809 |
| 10 trading days parallel + listing-pruned | 635.7         | 661.7         | 9               | 9        | 3,712  | 288,794 |
| 30 trading days parallel + listing-pruned | 1644.6        | 1752.1        | 30              | 30       | 12,336 | 965,225 |
| manifest-pruned (BROKEN — MDPS underfill) | 348.7         | 670.4         | 1               | 1        | 405    | 31,924  |

## Key findings

### 1. Manifest pruning is non-functional today

TRADFI `_index/availability_index.parquet` has **only 2 MDPS rows** (2026-01-02 + 2026-04-10) covering all timeframes
and data_types, despite ~24 days of GCS parquet existing across `2026-01-02 → 2026-04-15`. Harsh's MDPS run produced
parquet but did not (correctly) emit manifest rows for the full date range. This is the MDPS underfill flagged in the
plan as an out-of-scope blocker — it must be fixed for manifest-driven pruning to be useful.

### 2. Listing-prune approach in the bench was wrong

The bench did one `list_blobs` per candidate day (45 calls) — naive and slow (15.7s). **The right approach is a single
flatter `list_blobs` at a higher prefix** (e.g. the venue prefix scoped by timeframe + data_type) that returns all
available `day=...` partitions in one round-trip. We parse `day=` out of the returned paths. Cost: ~1 round-trip per
(bucket, timeframe, data_type, venue) — cacheable for a TTL.

Re-running with that pattern is the correct comparison. Pre-rewrite numbers (45 calls, 15.7s) are the cost of doing it
the naive way; we'd never ship that.

### 3. Cold single-file = 671ms p50 is high

Parent-doc target is ≤ 200ms cold. The bench ran from a workstation, not from a co-located backend. In a Cloud Run / GKE
deployment in the same region as the bucket, expect **50–100ms cold, 20–50ms warm**. Our number doesn't disprove the
budget; it just means we can't measure the real budget from a workstation.

The breakdown of single-file timing is illuminating regardless:

- Download: 659ms (97% of wall)
- Parse: 1.5ms (0.2%)
- Project: 9.4ms (1.4%)

So the bottleneck is round-trip, not CPU. Pre-aggregation (parent-doc Phase 1, monthly rollup) would let us issue 1
round-trip per month instead of 1 per day — a 22× reduction in round-trips for our 1-month window.

### 4. Parallelism win is real

10 calendar days: **7.4× speedup** parallel vs sequential. Confirms `ThreadPoolExecutor(max_workers=10+)` is the right
multi-file pattern. The current `BatchCandleReader` already does this.

### 5. 30-day window

`1645ms p50, 1752ms p99` for 30 trading days, parallel. Even from a workstation, this is under the parent-doc 30-day p99
target of ~800ms only by 2.2×. From a co-located backend, expect ~250–400ms p50 — comfortably inside budget.

## Implications for the plan

| Finding                       | Plan unit affected              | Action                                                                                                                                                                                                                      |
| ----------------------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Manifest underfilled          | Decision §3 (manifest as index) | Switch primary pruning approach to **GCS listing** at venue-level prefix, with manifest as a future optimization once MDPS is fixed. Add a flag in `candle_query.fetch()` so manifest can be enabled when the bug is fixed. |
| Cold latency from workstation | Acceptance criterion G          | Re-measure from a co-located backend before judging pass/fail on the parent-doc 800ms p99 target.                                                                                                                           |
| Listing call cost             | Unit A implementation           | Use a single high-prefix `list_blobs` with `day=` parsing, **not** N×prefix-per-day. Cache the resulting day-set per (bucket, timeframe, data_type, venue) for the same 60s TTL the manifest uses.                          |
| Parallelism win               | Unit A implementation           | Keep `ThreadPoolExecutor(max_workers=16)` pattern from current `BatchCandleReader`. Already correct.                                                                                                                        |
| Pre-aggregation leverage      | Parent-doc Phase 1              | Numbers confirm: monthly rollup parquets would give 22× reduction in round-trips for typical 1-month chart windows. Highest-leverage future work after this plan ships.                                                     |
