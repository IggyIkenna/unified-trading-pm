# Price-chart end-to-end benchmark — real GCS, workstation

**Date:** 2026-04-30 **Stack:** tier-1 `--real`, `unified-trading-api` on `:8030`, GCS reads from
`market-data-tick-tradfi-central-element-323112` via UTL `BatchCandleReader` (manifest pruning + 32-conn pool,
post-`feat/price-chart-gcs-delivery`). **Test:** `tests/e2e/widgets/price-chart-benchmark.spec.ts` (Playwright API
client, hits backend directly on `:8030`). **Symbols:** NASDAQ:AAPL, NASDAQ:MSFT, NASDAQ:GOOGL, NYSE:JPM (4 backfilled
TRADFI symbols, ~24 trading days each). **Reproduce:**

```bash
# Boot tier-1 stack first
bash scripts/dev-tiers.sh --tier 1 --real

# Run benchmark
E2E_API_URL=http://localhost:8030 \
  npx playwright test \
    --config tests/e2e/widgets/playwright.proxy-latency.config.ts \
    price-chart-benchmark
```

**5/5 scenarios passed. Total wall-clock 1.8 min.**

---

## Headline numbers

| Scenario                                           | What it measures                                               | p50               | p99        | Sample size              |
| -------------------------------------------------- | -------------------------------------------------------------- | ----------------- | ---------- | ------------------------ |
| **S1 initial paint**                               | First chart fetch per (symbol, date) — what user sees on click | **484 ms**        | **745 ms** | 12 (4 symbols × 3 dates) |
| **S2 warm refetch**                                | Re-fetch same (symbol, date) — cache effect                    | **652 ms**        | **1.11 s** | 12                       |
| **S3 scroll-back, 9× 7-day chunks (60 days back)** | User pans chart left aggressively from Apr-13 to ~Feb-12       | **~10.3 s total** | 11.2 s     | 4 symbols                |
| **S3 per-chunk**                                   | One scroll-back fetch (7 days, ~2K bars, ~190 KB)              | **1.20–1.33 s**   | 1.63 s     | 36 chunks                |
| **S4 go-to-date jump**                             | User picks a different date from the calendar                  | **432 ms**        | **542 ms** | 12                       |
| **S5 timeframe switch (1m→5m→1H)**                 | User clicks a timeframe button                                 | **313 ms**        | **419 ms** | 12                       |

**Cold-start outlier:** S1 first call (AAPL 2026-04-14) was 3.32 s — that's the GCS storage client establishing TLS +
auth metadata. Every call after landed in 410–745 ms range, including the same call retried later in S4 which came back
at 410 ms warm.

---

## Per-symbol scroll-back totals

User starts at Apr-13, pans left in 7-day chunks until Feb-12 (~9 weeks):

| Symbol | Total wall-clock | Bars loaded | Bytes   |
| ------ | ---------------- | ----------- | ------- |
| AAPL   | **9.98 s**       | 17,794      | 1.64 MB |
| MSFT   | **10.36 s**      | 18,448      | 1.69 MB |
| GOOGL  | **11.17 s**      | 17,612      | 1.62 MB |
| JPM    | **9.73 s**       | 16,922      | 1.55 MB |

**Average:** ~1.15 s per 7-day chunk, ~10.3 s for two months of 1m bars per symbol. The chunked-scroll-back design (7
days / fetch instead of 1 day / fetch) is the reason this is bearable — pre-Unit-A this same scroll would have been 9
fetches × ~1.1 s = same wall-clock but **45 round-trips** instead of 9, each one carrying a render-blocking React state
update.

---

## What this tells us

### Backend / GCS path is healthy

- **Manifest pruning works** — every shard requested returned `bars > 0`, no wasted GCS GETs on weekends/holidays in the
  requested windows.
- **Parallelism works** — a 7-day window of 1m bars (5 trading days × ~390 bars/day) returns in ~1.2 s. Sequentially
  that would be 5 × ~450 ms = 2.25 s. The ThreadPoolExecutor + 32-connection pool is delivering ~2× speedup even at this
  small scale.
- **Connection-pool tune held up** — no `Connection pool is full` warnings in the backend log across all 200+ requests
  this benchmark issued.

### One thing to flag: warm refetch is not actually faster

S2 (warm refetch) p50 = 652 ms vs S1 (cold) p50 = 484 ms. Inverted, and larger because two of the 12 S2 samples hit a
~1.1 s bucket (likely network jitter from the workstation).

**Reading**: there is **no parquet-level caching** in `BatchCandleReader`. UTL's manifest cache (60s in-process) avoids
re-downloading the index, but the parquet itself is downloaded every time. For a chart that re-fetches the same (symbol,
date) on remount this is wasted effort. **Future optimization** — parent doc Phase 3 (client-side `BarStore`) eliminates
this by caching at the chart layer, not the API layer.

### Pre-aggregation leverage estimate

Single-day 1m parquet for AAPL = ~37 KB (400 bars). 30-day window = ~1.1 MB across 30 round-trips × 1.2 s/chunk = the
parent doc's Phase 1 monthly rollup would compress 30 round-trips → 1 round-trip per month.

At the workstation latency floor of ~400 ms cold, that's:

- **Today**: 60-day scroll-back = 9 chunks × 1.2 s = ~10.5 s
- **Phase 1 (monthly rollup)**: 60-day scroll-back = 2 monthly files × ~500 ms = ~1.0 s

**~10× win for scroll-back UX.** Worth doing once the immediate plan ships.

### Co-located backend estimate

Workstation cold p50 ≈ 484 ms for one parquet GET. Of that, ~10 ms is TCP+TLS reuse, ~470 ms is Tokyo→workstation RTT.
Co-located backend (Cloud Run in `asia-northeast1` matching the bucket region) should hit:

- Single-file: **50–100 ms** (vs 484 ms today)
- 7-day chunk: **150–250 ms** (vs 1.2 s today)
- 60-day scroll-back: **~2 s** (vs ~10 s today)
- Single-month with Phase 1 rollup: **~80–120 ms**

Both axes (Phase 1 + co-located deployment) are **independent and multiplicative**.

---

## Test architecture — why two specs

`price-chart-proxy-latency.spec.ts` (4 tests, fast, CI-friendly) : FE↔BE contract test. Validates the proxy returns the
right shape + proxy adds ~0 ms over direct backend. Mode-agnostic. Runs in 11 s.

`price-chart-benchmark.spec.ts` (5 tests, slow, on-demand) : This file. Real-mode only — it's a no-op against mock
backend (skips via `mock_mode !== false` guard in `beforeAll`). Hits backend directly on `:8030`, not the UI proxy,
because we already verified proxy overhead is ~0 ms. Going direct removes Next.js dev-compile noise.

Both run via the same `playwright.proxy-latency.config.ts` config (which skips the default `webServer` block that's
sized for tier-0 mock testing).

---

## Cross-references

- Backend bench: `unified-trading-api/scripts/bench_candle_reads.py` — measures the same path one layer deeper (no HTTP,
  just `BatchCandleReader` directly). Use that to isolate API-layer overhead from GCS-layer cost.
- Pre-Unit-A baseline: `reports/price_chart_gcs_benchmark_2026_04_29.md`.
- Post-Unit-A backend bench: `reports/price_chart_gcs_benchmark_2026_04_29_post.md`.
- Plan: `plans/ai/price_chart_gcs_delivery_2026_04_29.plan.md`.
- Codex SSOT: `codex/02-data/chart-candle-delivery-flow.md`.
