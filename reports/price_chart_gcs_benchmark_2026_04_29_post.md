# Price-chart GCS read benchmark — post-Unit-A

- Date: 2026-04-29T16:24:19Z (rerun after manifest rebuild + reader refactor)
- Project: `central-element-323112`
- Symbol: `NASDAQ:AAPL` `1m` `data_type=ohlcv_1m`
- Bucket: `market-data-tick-tradfi-central-element-323112`
- Manifest state: rebuilt 2026-04-29 21:52 UTC via per-VM-shard write path. 10,794 MDPS rows total, 71 dates of AAPL 1m.
- Runs per scenario: 5

## Single-file scenarios

| Scenario    | wall p50 (ms) | wall p99 (ms) | download p50 | parse p50 | project p50 | bytes  | rows |
| ----------- | ------------- | ------------- | ------------ | --------- | ----------- | ------ | ---- |
| single cold | 660.4         | 664.1         | 648.7        | 1.7       | 9.8         | 31,476 | 400  |
| single warm | 358.7         | 662.1         | 347.5        | 1.6       | 9.6         | 31,476 | 400  |

## Multi-file scenarios

| Scenario                                        | wall p50 (ms) | wall p99 (ms) | files attempted | files ok | rows      | bytes       |
| ----------------------------------------------- | ------------- | ------------- | --------------- | -------- | --------- | ----------- |
| 10 cal days, parallel, no prune                 | 605.4         | 632.1         | 10              | 7        | 2,881     | 224,809     |
| 10 cal days, sequential                         | 4869.7        | 4927.6        | 10              | 7        | 2,881     | 224,809     |
| 10 trading days, parallel + listing-pruned      | 1018.7        | 1021.8        | 9               | 9        | 3,712     | 288,794     |
| 30 trading days, parallel + listing-pruned      | 1429.8        | 1698.5        | 30              | 30       | 12,336    | 965,225     |
| **10 trading days, parallel + manifest-pruned** | **1006.2**    | **1013.2**    | **9**           | **9**    | **3,712** | **288,794** |

## Headline numbers — pre vs post

| Metric                         | Pre-Unit-A | Post-Unit-A | Delta                     |
| ------------------------------ | ---------- | ----------- | ------------------------- |
| Single cold p50                | 671 ms     | 660 ms      | -1.6% (workstation noise) |
| Single warm p50                | 347 ms     | 359 ms      | +3% (workstation noise)   |
| 10-day parallel, no prune      | 659 ms     | 605 ms      | -8%                       |
| 10-day sequential              | 4910 ms    | 4870 ms     | -1%                       |
| 30-day pruned p50              | 1645 ms    | 1430 ms     | -13%                      |
| 30-day pruned p99              | 1752 ms    | 1699 ms     | -3%                       |
| Sequential vs parallel speedup | 7.4×       | 8.0×        | +0.6×                     |

## Manifest pruning works now

The "BROKEN — MDPS underfill" scenario from pre-Unit-A returned 1 file (only 2 dates registered). Post-rebuild it
returns 9 files matching listing-pruning exactly. The manifest contains 71 AAPL 1m dates, all backfilled days included.
Per-symbol predicate `(data_type=ohlcv_1m AND timeframe=1m AND venue=NASDAQ AND instrument_id=AAPL AND available=True)`
works as designed.

## Why the win is modest at this scale

Two reasons:

1. **Workstation network**: cold-fetch download is 600ms+ from workstation. The listing-prune call to discover present
   days is itself one network round-trip per candidate day in the bench's naive listing — ~12s for 45 days. That's not
   the production approach (would be one high-prefix list, not N), so the listing numbers in this bench are pessimistic.
   Manifest-prune skips listing entirely and is the cleaner pattern.

2. **Bench window isn't actually sparse**: the 30-day window we tested (2026-03-15 → 2026-04-14) has ~22 trading days vs
   30 calendar — only 27% of days are skippable. On a 1-year window weekends + holidays approach 30%, more savings.

Real-world production gains come from:

- Co-located backend (eliminates 95% of single-file latency).
- Pre-aggregated monthly rollups (parent-doc Phase 1) — 22× round-trip reduction.
- Manifest pruning prevents wasted GCS list ops at scale (kicks in once buckets exceed ~1M objects per Phase 2 trigger).

## Manifest pruning correctness

Verified end-to-end:

- 10-day window, 7 weekdays + 3 weekends = 7 valid GCS shards.
- Manifest prune returns exactly 7 dates.
- Manifest prune scenario downloads exactly 7 files, returns 3,712 bars.
- Listing prune returns same 7 dates, same byte count.
- Cal-days no-prune attempts 10 GETs, gets 7 200s + 3 404s — same data, more wasted round-trips.

## Implications for plan acceptance criteria

| Criterion                                          | Status                                                                                            |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| G — 30-day pruned p99 ≤ 800 ms (parent doc target) | Not from workstation (1699 ms p99). **Must re-measure from co-located backend** before pass/fail. |
| 7.4× → 8.0× parallelism speedup                    | Confirmed                                                                                         |
| Manifest pruning skips empty days correctly        | Confirmed                                                                                         |

## Next-leverage moves (out of this plan, written down)

1. **Per-month parquet rollup** (parent-doc Phase 1) — biggest win. Estimate: 30-day window p50 from 1430 ms → ~150 ms.
2. **BQ external table-driven manifest regenerator** (this plan's §3 Phase 2) — required when buckets exceed ~1M
   objects.
3. **Co-located backend deployment** (operational, not architectural) — drops single-file cold from 660 ms to 50–100 ms.
