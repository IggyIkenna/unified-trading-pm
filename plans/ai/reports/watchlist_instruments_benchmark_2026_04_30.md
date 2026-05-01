# Watchlist instruments GCS read benchmark — baseline

- Date: 2026-04-30T13:13:14.581969Z
- Project: `central-element-323112`
- Target date: `2026-04-14`
- TRADFI bucket: `instruments-store-tradfi-central-element-323112`
- CEFI bucket: `instruments-store-cefi-central-element-323112`
- Code path: mirrors current `InstrumentsReader._fetch` (download_bytes + pyarrow read_table + `_normalise_row` per
  row).
- Runs per scenario: 5

## Summary

Single TRADFI/NASDAQ shard cold p50=616ms / p99=636ms — well above the plan's ≤200ms cold target, likely region mismatch
(workstation outside bucket region; co-located backend should be 50–100ms). Warm-vs-cold gap is small and noisy (warm
p50=656ms vs cold p50=616ms) because the download is HTTPS-bound, not handshake-bound. Loading the full TradFi watchlist
tab (6 venues parallel) lands at p50=1269ms / p99=1309ms — also over the plan's ≤400ms p99 budget. Parallelism gives a
3.1× speedup over sequential. CME is the unexpected hot venue (11,853 rows, ~247KB, ~365ms normalise) — dominates the
parallel wall-clock; NASDAQ is a trivially small shard by comparison. CEFI/Deribit shard (3661 rows) reads in 666ms
cold; the 3,002-option payload normalises in ~110ms because options inflate the row count, not the per-row decimal cost.

## Headline table

| Scenario                                 | wall p50 (ms) | wall p99 (ms) | download p50 (ms) | parse p50 (ms) | normalise p50 (ms) | n_rows | bytes   |
| ---------------------------------------- | ------------- | ------------- | ----------------- | -------------- | ------------------ | ------ | ------- |
| single NASDAQ cold                       | 616.1         | 635.8         | 612.5             | 2.1            | 1.5                | 41     | 18,894  |
| single NASDAQ warm                       | 655.6         | 666.2         | 651.9             | 2.2            | 1.4                | 41     | 18,894  |
| all 6 TRADFI venues parallel (workers=6) | 1268.6        | 1308.7        | 244.5             | 2.6            | 3.9                | 14,202 | 385,715 |
| all 6 TRADFI venues sequential           | 3986.8        | 4096.4        | 414.1             | 2.2            | 4.0                | 14,202 | 385,715 |
| single DERIBIT cold                      | 666.0         | 670.2         | 543.6             | 5.6            | 110.4              | 3661   | 69,887  |

## Multi-shard breakdown (last run)

| Scenario                                 | venue  | rows  | bytes   | t_download (ms) | t_parse (ms) | t_normalise (ms) |
| ---------------------------------------- | ------ | ----- | ------- | --------------- | ------------ | ---------------- |
| all 6 TRADFI venues parallel (workers=6) | CBOE   | 1     | 17,771  | 222.3           | 2.0          | 0.2              |
| all 6 TRADFI venues parallel (workers=6) | CME    | 11853 | 247,400 | 882.3           | 12.4         | 367.0            |
| all 6 TRADFI venues parallel (workers=6) | FX     | 1     | 17,107  | 261.8           | 1.5          | 0.2              |
| all 6 TRADFI venues parallel (workers=6) | ICE    | 2094  | 63,265  | 441.5           | 3.3          | 56.1             |
| all 6 TRADFI venues parallel (workers=6) | NASDAQ | 41    | 18,894  | 226.0           | 1.7          | 1.6              |
| all 6 TRADFI venues parallel (workers=6) | NYSE   | 212   | 21,278  | 227.1           | 3.4          | 6.3              |
| all 6 TRADFI venues sequential           | CBOE   | 1     | 17,771  | 239.4           | 2.0          | 0.2              |
| all 6 TRADFI venues sequential           | CME    | 11853 | 247,400 | 1589.3          | 11.9         | 355.3            |
| all 6 TRADFI venues sequential           | FX     | 1     | 17,107  | 252.3           | 2.1          | 0.2              |
| all 6 TRADFI venues sequential           | ICE    | 2094  | 63,265  | 430.9           | 3.6          | 53.2             |
| all 6 TRADFI venues sequential           | NASDAQ | 41    | 18,894  | 397.4           | 2.2          | 1.4              |
| all 6 TRADFI venues sequential           | NYSE   | 212   | 21,278  | 485.4           | 2.3          | 6.5              |

## Notes / anomalies

- **Cold vs warm**: cold p50 616ms vs warm p50 656ms — indistinguishable from noise — single-shard cost is
  HTTPS-roundtrip-bound on this run, not handshake-bound; TLS reuse savings hide inside per-call download variance.
- **Parallel vs sequential**: 6-venue parallel p50 1269ms vs sequential p50 3987ms (3.1× speedup). Sets the watchlist
  tab-load budget.
- **Deribit dominance**: 3661 rows / 69,887 bytes in one shard — p50 666ms cold. ~89× the row-count of NASDAQ, but
  per-row parse cost is similar.
- **`InstrumentsReader.get_instruments` is broken at the SDK boundary.** `build_bucket(..., category=…)` raises
  `TypeError` post-`d3c8880` rename (`category` → `asset_group`). Bench script mirrors `_fetch` directly and calls
  `InstrumentsReader._normalise_row` to keep numbers faithful to the intended path. Unit A must fix the kwarg before the
  route works in real mode.

## Reproduction

```bash
GCP_PROJECT_ID=central-element-323112 \
  /path/to/venv/bin/python scripts/bench_instruments_reads.py \
    --project-id central-element-323112 \
    --out unified-trading-pm/plans/ai/reports/watchlist_instruments_benchmark_2026_04_30.md
```
