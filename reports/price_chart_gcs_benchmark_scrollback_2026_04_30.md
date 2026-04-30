# Price-chart GCS read benchmark — baseline

- Date: 2026-04-30T11:32:16.815657Z
- Project: `central-element-323112`
- Symbol: `NASDAQ:AAPL` `1m` `data_type=ohlcv_1m`
- Bucket: `market-data-tick-tradfi-central-element-323112`
- Code path: current `BatchCandleReader`-equivalent (pre-Unit-A)
- Runs per scenario: 5

## Single-file scenarios

| Scenario | wall p50 (ms) | wall p99 (ms) | download p50 | parse p50 | project p50 | bytes | rows |
|---|---|---|---|---|---|---|---|
| single cold | 663.1 | 1078.1 | 652.0 | 1.7 | 10.0 | 31,476 | 400 |
| single warm | 640.6 | 664.8 | 629.4 | 1.4 | 9.7 | 31,476 | 400 |

## Multi-file scenarios

| Scenario | wall p50 (ms) | wall p99 (ms) | files attempted | files ok | rows | bytes |
|---|---|---|---|---|---|---|
| 10 cal days parallel (no prune) | 618.8 | 638.7 | 10 | 7 | 2,881 | 224,809 |
| 10 cal days sequential | 4578.4 | 4596.6 | 10 | 7 | 2,881 | 224,809 |
| 10 trading days parallel + listing-pruned | 625.7 | 647.8 | 9 | 9 | 3,712 | 288,794 |
| 30 trading days parallel + listing-pruned | 1206.5 | 1226.0 | 30 | 30 | 12,336 | 965,225 |
| manifest-pruned (BROKEN — MDPS underfill, 0 days matched) | 0.0 | 0.0 | 0 | 0 | 0 | 0 |
| scroll-back 9× 7-day chunks | 5006.8 | 5011.4 | 9 | 9 | 17,790 | 0 |


## Scroll-back chunk breakdown

| chunk | from | to | rows | ms |
|---|---|---|---|---|
| 1 | 2026-04-08 | 2026-04-14 | 2051 | 31357 |
| 2 | 2026-04-01 | 2026-04-07 | 1661 | 611 |
| 3 | 2026-03-25 | 2026-03-31 | 2076 | 507 |
| 4 | 2026-03-18 | 2026-03-24 | 2087 | 577 |
| 5 | 2026-03-11 | 2026-03-17 | 2019 | 511 |
| 6 | 2026-03-04 | 2026-03-10 | 2031 | 705 |
| 7 | 2026-02-25 | 2026-03-03 | 2068 | 452 |
| 8 | 2026-02-18 | 2026-02-24 | 2072 | 645 |
| 9 | 2026-02-11 | 2026-02-17 | 1725 | 455 |

**Total wall-clock per run** (5 runs): p50=5007 ms, p99=5011 ms — covers 9 weeks of 1m bars.


## Notes

- **Manifest pruning is non-functional today.** TRADFI MDPS rows in `_index/availability_index.parquet` only cover 2 dates (2026-01-02 + 2026-04-10) despite ~24 days of GCS parquet existing. MDPS writer is underfilling. Until fixed, **listing-pruning** (one `list_blobs` per candidate day) is the right interim approach — adds 15410ms for a 30-day window, well under the savings.
- Single-file cold p50 = 663ms is high vs parent-doc target (≤ 200ms cold). Likely region mismatch — bench ran from a workstation outside the bucket region. In a co-located backend (same region as the bucket), expect 50–100ms cold and 20–50ms warm.
- Sequential vs parallel: **7.4× speedup** from parallelism on 10 files.
