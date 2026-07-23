---
title: Price Chart — Historical Data from GCS to UI
id: price_chart_gcs_delivery_2026_04_29
status: implemented
created: 2026-04-29
last_updated: 2026-04-29
benchmark_baseline: reports/price_chart_gcs_benchmark_2026_04_29.md
benchmark_post: reports/price_chart_gcs_benchmark_2026_04_29_post.md
audience: backend engineers, frontend engineers
parent_reference: market_data_delivery_architecture_2026_04_27.md
codex_refs:
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/data-status-drilldown.md
  - /codex/02-data/subscription-model.md
  - /codex/02-data/per-category-bucket-layouts.md
---

# Price Chart — Historical Data from GCS to UI

Operational plan to make the Terminal price-chart widget render real historical OHLCV candles read from GCS
`processed_candles/` via the codex-blessed UTL domain-client path, with manifest-driven date pruning so we don't burn
time on empty-day round-trips.

---

## Scope

**In:**

- Historical candle delivery for the Terminal price-chart widget at `http://localhost:3000/services/trading/terminal`.
- Backend reads via UTL `MarketCandleDataDomainClient` (codex SSOT for candle reads — see `subscription-model.md`).
- Manifest pruning via `_index/availability_index.parquet` — `read_availability_index(bucket)` from UTL — cached per
  bucket.
- Static instrument list on the UI side — `DEFAULT_INSTRUMENTS` is the contract surface for this plan. Five symbols
  Harsh has backfilled: `NASDAQ:AAPL`, `NASDAQ:MSFT`, `NASDAQ:GOOGL`, `NYSE:JPM`, `BINANCE-FUTURES:BTCUSDT`,
  `BINANCE-FUTURES:ETHUSDT`.
- Bucket-variant toggle (prod vs test) through config — same hive layout, different bucket suffix.

**Out:**

- Watchlist sourced from `instruments-service`. Deferred to a follow-up plan once the chart read path is sound.
- Live tick / WebSocket bar deltas. WS endpoint exists at `unified-trading-api/routes/websocket.py`; real-mode
  subscriber to MTDS/MDPS pub-sub is not wired. Deferred — see §"Live mode appendix".
- BigQuery as a primary read path. Codex SSOT is GCS parquet via UTL domain client; BQ stays a possible future
  optimization, not the default. See §"Why GCS via UTL, not BQ" below.
- Per-month OHLCV rollup, time-range (`from_ts`/`to_ts`) addressing, client-side BarStore, edge cache. All Phase-N items
  in `market_data_delivery_architecture_2026_04_27.md`.

---

## Architectural decisions (with citations)

### 1. Read path = UTL `MarketCandleDataDomainClient`, not raw GCS, not BQ

`/codex/02-data/subscription-model.md` §"MarketCandleDataDomainClient":

> "Services don't hardcode GCS paths. Instead, they declare upstream dependencies… Domain clients wrap
> `StandardizedDomainCloudService`, providing domain-specific query methods over a generic cloud I/O layer."

The current `unified_trading_api/services/batch_candles.py` (`BatchCandleReader`) directly uses
`unified_trading_library.get_storage_client`

- pyarrow + manual hive path construction. That's a partial reimplementation of what
  `MarketCandleDataDomainClient.get_candles(date, instrument_id, timeframe, data_type, venue)` already does in UTL. **We
  delete `BatchCandleReader` and call UTL directly from the route.** Less code, codex-aligned, future swaps to BQ or a
  different storage backend happen once inside UTL instead of in every consumer.

### 2. Manifest first, GCS second

`/codex/02-data/availability-manifest-and-data-status.md` §"What Is the Availability Manifest?":

> "Every GCS data bucket has an `_index/availability_index.parquet` file. This parquet file is the index of what data
> exists in that bucket… The deployment-api reads it via `read_availability_index()`."

Existing precedent: `/codex/02-data/data-status-drilldown.md` documents `/api/data-status/shard-detail` doing exactly
this — read the manifest, resolve a single GCS object path, return data + signed URL. We reuse the same pattern for the
chart route.

**Caveat:** spot-checked the TRADFI manifest and MDPS rows currently have empty `venue`/`instrument_id` columns (only
`(date, data_type, timeframe)` is populated). Per-symbol pruning isn't possible from the manifest today — only
per-`(date, timeframe)`. That's still enough to skip weekend/holiday days for TRADFI, which is the dominant cost on
scroll-back. Per-symbol pruning is blocked on an MDPS writer-side fix (see §"Out-of-scope blockers" below).

### 3. Pruning — phased by data scale (codex industry-standard pattern)

`/codex/02-data/partitioning.md` §"The Cost Optimization" sets the end-state explicitly: hive paths exist so **BigQuery
external tables can index GCS partitions without reading the parquet bytes**. That's the industry-standard pattern at
scale and it's already part of the codebase's design — just not yet wired for `processed_candles/`.

The right phasing depends on data volume:

**Phase 1 (this plan, today's scale: ~thousands of objects per bucket)**

- **Use `rebuild_manifest_from_canonical_paths(bucket, prefix='processed_candles/by_date')`** from UTL
  `manifest_writer.py:2758`. This is the canonical tool — `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh`
  already documents it as the post-backfill manifest reconciliation step. Run once manually now to populate the TRADFI
  manifest. Takes 1–2 minutes. Cost: a few cents in list ops.
- **Use the resulting `_index/availability_index.parquet`** from the route via `read_availability_index(bucket)` (60s
  in-process cache, lazy load — covered in §3a below).
- **Do not list GCS at runtime.** The route reads the manifest parquet only. List-blobs costs scale with object count
  and we shouldn't bake them into the hot path even at small scale.

**Phase 2 (separate later plan — BQ external table → manifest regenerator)**

Tracked as its own follow-up plan, not blocking chart delivery. Owner

- timing TBD. Brief specified here so the boundary is clear.

**Goal**: a scheduled job that uses BigQuery external tables (codex `partitioning.md` "cost optimization" pattern) to
regenerate `_index/availability_index.parquet` for every category bucket, at arbitrary scale (the 100 TB-multi-bucket
end-state).

**What it does**:

- Creates one BQ external table per category bucket over the hive layout (`processed_candles/by_date/...`), e.g.
  ```sql
  CREATE EXTERNAL TABLE candles_data.processed_candles_tradfi
  OPTIONS (
    format = 'PARQUET',
    uris = ['gs://market-data-tick-tradfi-{project}/processed_candles/by_date/*'],
    hive_partition_uri_prefix = 'gs://market-data-tick-tradfi-{project}/processed_candles/by_date',
    require_hive_partition_filter = true
  );
  ```
- A scheduled job (Cloud Scheduler cron) issues one SQL against `INFORMATION_SCHEMA.PARTITIONS` per bucket — sub-second
  regardless of bucket size, no list_blobs, no parquet bytes scanned.
- The query output populates the same canonical `_index/availability_index.parquet` so consumers (this chart route,
  deployment-api data-status, dependency checkers) need zero changes. **The on-disk manifest contract stays exactly the
  same** — only the regenerator changes.

**Why it's a separate plan, not this one**:

- Adds infra (BQ external tables × N buckets, Cloud Scheduler job, Terraform). Outside the chart-delivery surface.
- Touches every consumer's index format expectations only if we drift the schema — which we won't. So consumers are
  decoupled.
- May already be partially implemented — there's a stale wrong-URI external table at `candles_data.candles_cefi_v2`
  (listing today's buckets, file pattern doesn't match anything, looks like an incomplete attempt). Whoever owned that
  may have intended this but not finished. Worth confirming with that owner before building from scratch.

**Trigger to escalate Phase 2 priority** (write down so we don't forget):

- Any one bucket has >1M objects, OR
- Phase-1 rebuild takes >5 min wall-clock, OR
- We move to per-month parquet rollup (parent-doc Phase 1) and the manifest needs more frequent regeneration.

**For this plan today**: assume Phase 2 doesn't exist. Just run the UTL Phase-1 rebuild once manually. Document the
follow-up plan stub at `unified-trading-pm/plans/ai/manifest_regenerator_via_bq_2026_05.plan.md` during Unit F closeout
— empty skeleton with the spec above + a note pointing at the stale `candles_cefi_v2` table to investigate.

**What this plan does today**

- Run the existing UTL rebuild function manually, once, to fix TRADFI's underfilled manifest.
- Use the resulting manifest at runtime via `read_availability_index`.
- Document Phase 2 (BQ external table-driven rebuild) as the scale-out path. Not implemented now because the gain is
  invisible at our current data volume; pre-implementing without measurement is cargo-culting.

**Trigger to move to Phase 2** (write down so it's not forgotten):

- Any one bucket has >1M objects, OR
- The rebuild step takes >5 min wall-clock on a fresh run, OR
- We move to per-month parquet rollup (parent-doc Phase 1) and the manifest consequently needs more frequent
  regeneration.

Whichever fires first. Document the switch decision against this plan when triggered.

### 3a. Manifest regeneration + read-side caching

This is a thing the platform already solves. We are a _reader_, not a writer or regenerator. Worth being explicit about
who does what so the plan doesn't accidentally take on responsibility that lives elsewhere.

**How the manifest gets regenerated** (see UTL `unified_trading_library/manifest_consolidator.py` module docstring):

- Each writer VM (MTDS / MDPS / instruments-service) writes its own per-VM shard at `_index/per_vm/{instance}.parquet` —
  Phase 1 of the per-VM-sharding fix. No CAS contention, no 429 thundering herd.
- A separate Cloud Run Job, **`manifest-consolidator`**, runs on Cloud Scheduler `*/1 * * * *` (one cycle per minute,
  per category bucket). It lists every per-VM shard, concats + dedupes (last write wins), and rewrites the canonical
  `_index/availability_index.parquet` via generation-match CAS.
- Deployment lives in `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`. CLI is
  `python -m unified_trading_library.manifest_consolidator --bucket {bucket}`.
- Emits `MANIFEST_CONSOLIDATED` / `MANIFEST_CONSOLIDATION_FAILED` events per cycle for monitoring.

**So when MDPS writes a new shard**, the row appears in the consolidated manifest within ~1–2 minutes (one consolidator
cycle). **Not our problem to schedule, not our problem to debug** — if the consolidator is down, the data-status page
will surface stale numbers and an MDPS owner gets paged, not us.

**How the cache works** (UTL `read_availability_index`):

- **In-process LRU** in the API process — `_INDEX_CACHE: dict[bucket → (timestamp, df)]`, TTL **60 seconds**
  (`_INDEX_CACHE_TTL = 60.0`). First read of a bucket downloads the consolidated parquet; subsequent reads in the same
  minute hit memory.
- **Cache invalidation on write** — any `ManifestWriter.write()` call from the same process (we won't write — but the
  function exists) calls `_invalidate_index_cache(bucket)` so a writer-VM always sees its own row on the next read.
- **Three-layer staleness fallback when reading**:
  1. If consolidated blob is fresh (`written_at` within `manifest_consolidated_staleness_sec`, default 120s), return it.
     Plus merge in the caller's own per-VM shard so a writer-then-read sequence sees its own rows without waiting for
     the next consolidator cycle.
  2. If consolidated blob is missing or stale, list + merge per-VM shards live (slower but always current).
  3. If neither exists, fall through to caller's own self-shard (cheap targeted GET).

**What this plan does:**

- Backend imports `read_availability_index` from UTL and calls it during the route's prune step.
- We **do not** add a custom cache layer. UTL's 60-second in-process cache is the right granularity for our use case
  (chart pages aren't issuing thousands of req/s; minute-level staleness is invisible to a human picking dates).
- We **do not** schedule consolidation. Cloud Scheduler already does it.
- We **do not** invalidate the cache on chart navigation. The 60s TTL handles natural decay; if the consolidator just
  landed a new shard, the user's next click within the same minute will miss it — acceptable. They click again 60s later
  and see it.

**Where the cache lives in our process:** UTL's module-level dict. That means each `unified-trading-api` worker (uvicorn
workers) has its own copy. With 4 workers × 5 category buckets × ~few MB per manifest parquet, that's ~80 MB worst-case
in memory across the fleet — fine. If it ever isn't, the right fix is a process-local shared cache (Redis), not a
per-route cache layer in our code.

**Where the file lives + cache lifecycle (explicit):**

The canonical manifest is **always in GCS** — `gs://market-data-tick-{cat}-{project}/_index/availability_index.parquet`.
The in-process cache is purely an optimization layer; GCS is the source of truth. The cache is **lazy** (not preloaded
at service startup) and **per-worker** (each uvicorn worker holds its own copy in a UTL module-level dict).

| Event                                                            | Effect on cache                                                                        |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| API process boots                                                | Cache empty for all buckets                                                            |
| First `/candles` request needing TRADFI manifest                 | Download `_index/availability_index.parquet` (~0.5–1s cold), store in dict, serve      |
| Second request 5s later                                          | Memory hit, no GCS call                                                                |
| Request 65s later                                                | TTL expired → next request triggers fresh download                                     |
| MDPS writes new shard for `day=YYYY-MM-DD`                       | MDPS writes its per-VM shard. **Cache doesn't know.**                                  |
| `manifest-consolidator` Cloud Run Job next cycle (≤ 1 min later) | Rewrites canonical `_index/availability_index.parquet`. **Cache still doesn't know.**  |
| Next request within our 60s TTL                                  | Stale dataframe, user doesn't see the new day. Acceptable.                             |
| Next request after TTL expiry                                    | Fresh download, sees the new day                                                       |
| API process restart                                              | Cache dies with the process; first request after restart pays cold-download cost again |

**Worst-case staleness window**: TTL (60s) + consolidator interval (60s) = **~2 minutes** between MDPS landing a new
shard and chart users being able to see it. Fine for chart UX.

**Why lazy, not eager**: a startup preload would add boot complexity for a one-time-per-minute saving on first request.
Not worth it. First chart load already involves a parquet read; the manifest read piggybacks on that latency budget.

**Why we don't lengthen the TTL**: 60s is UTL's default and the right grain. Lengthening it means users see missing days
for longer after backfills. The latency benefit beyond 60s is sub-millisecond — already negligible.

**Memory footprint sanity check**: 4 workers × 5 category buckets × few MB per manifest ≈ ~80 MB worst-case. Fine. If
this ever needs to scale (many more workers), the right fix is a shared cache (Redis), not custom logic in our code.

**Unit D verification gotcha**: if the `manifest-consolidator` Cloud Run Job is not deployed in the target environment
(e.g. a dev project where infra wasn't applied), `read_availability_index` falls back to the per-VM-shard merge path
which is slower but correct. A slow first chart load in a fresh environment is probably that, not a bug on our side.
Check `gs://market-data-tick-{cat}-{project}/_index/availability_index.parquet` exists and `written_at` is recent before
assuming a problem is ours.

### 4. Mock vs real backend = `CLOUD_MOCK_MODE`, route honors it

Per project convention (`feedback project_market_data_routing_2026_04`):

- `mock_mode=true` → seed data from in-memory mock store.
- `mock_mode=false` → real GCS reads via UTL.

The `/market-data/candles` route stays mock-aware. Tier choice picks which side of the branch you're on.

### 5. Bucket variant from config

Codex `per-category-bucket-layouts.md` §"Test-mode variants":

> "Test-mode variants append `-test-`: e.g. `instruments-store-cefi-test-{project_id}`."

Hive partition shape is identical across prod and test variants, only the bucket name changes. Backend config exposes
`MARKET_DATA_BUCKET_VARIANT` (default `prod`); the UTL client receives the resolved bucket name.

### 6. `project_id` from `UnifiedCloudConfig`

Read via UTL → Secret Manager (canonical path). `GCP_PROJECT_ID` env fallback for local dev. Loud failure (503) if
neither resolves.

### 7. Frontend stays mock-on-`NEXT_PUBLIC_MOCK_API`

Tier choice on the frontend stays as-is. When real-mode UI is running, it always hits the backend; when mock-mode UI is
running, it stays in its in-browser fixture path. **No frontend mock-branch removal.**

### Why GCS via UTL, not BQ (current decision, revisit later)

BQ has tables provisioned (`market_data_hft.candles_{tf}_trades`, clustered on `venue, symbol, instrument_id`,
partitioned on `DAY(timestamp)`) and a UTL helper (`MarketDataProvider.get_candles` in
`unified_trading_library/core/cloud_data_provider.py:405`) that issues parameterised SQL.

But:

- **BQ load is sparse.** Verified 2026-04-29: `candles_1m_trades` contains only 2 days of `BINANCE-FUTURES:BTC-USDT`
  from 2023. AAPL, MSFT, GOOGL, JPM — none of them are in BQ. So today, even if we wanted to query BQ, there's nothing
  to read.
- **BQ duplicates state.** GCS parquet is the SSOT (MDPS writes there). Loading into BQ adds a second pipeline + a drift
  surface. Codex doesn't mandate it.
- **Latency**: BQ has ~1s minimum job-submit. For single-shard reads, GCS wins. For 30-day windows, BQ wins (single
  round-trip vs N×0.2s GCS reads). Once we measure (Unit E benchmark), we can decide per-window.
- **Cost**: BQ on-demand at $6.25/TB. Partition+cluster pruning means a 200-bar query scans KBs — pennies. Cost isn't
  the blocker.

**Forward path:** if later benchmarks show BQ wins on multi-day back-scroll, swap the UTL client's internal
implementation. Route stays unchanged. The point of routing through UTL today is exactly that swap-ability.

---

## Findings — current state (verified 2026-04-29)

### GCS layout

Real layout (project `central-element-323112`), confirmed by listing buckets:

```
gs://market-data-tick-{cefi|tradfi|defi}-{project_id}/processed_candles/
  by_date/day=YYYY-MM-DD/
    timeframe={15s,1m,5m,15m,1h,4h,24h}/
      data_type={trades|ohlcv_1m|book_snapshot_5|...}/
        venue=<VENUE>/
          <SYMBOL>.parquet
```

Filename is the bare symbol (`BTCUSDT.parquet`, `AAPL.parquet`), not the canonical `venue:type:symbol` instrument-key.
The `market-data-processing-service/docs/GCS_PATHS.md` doc claims an `instrument_type=` partition segment that **does
not exist** in actual objects — codex's `per-category-bucket-layouts.md` is the SSOT and matches reality. Verified
2026-04-29.

**Critical category divergence:**

| Category | `data_type` partition value used by MDPS |
| -------- | ---------------------------------------- |
| CEFI     | `trades` (e.g. BINANCE-FUTURES)          |
| TRADFI   | `ohlcv_1m` (e.g. NASDAQ, NYSE)           |
| DEFI     | varies — not in scope this plan          |

A reader that hardcodes `data_type=trades` for everything will return empty for all TRADFI symbols. Reader must dispatch
on category.

**Schema** of one parquet (verified on `tradfi/.../day=2026-04-13/.../venue=NASDAQ/AAPL.parquet`):
`timestamp, timestamp_out, venue, symbol, instrument_id, open, high, low, close, volume, trade_count, buy_*_volume, delay_*_ms`.
`timestamp` is `datetime64[ns]`, bar open. Matches what the chart needs after projection to `{time, o, h, l, c, v}`.

### Manifest

`gs://market-data-tick-tradfi-{project}/_index/availability_index.parquet` exists. Read 2026-04-29 — 18,149 rows, schema
v6 (24 columns). Service breakdown: MTDS 17,764, migrate-tradfi-canonical 342, **MDPS 43**.

MDPS rows have empty `venue` / `instrument_type` / `instrument_id`, populated
`(date, data_type, timeframe, instrument_count)`. Per-shard gating works at the (date, timeframe, data_type)
granularity; per-symbol gating doesn't until MDPS fixes its writer.

### Backend

`unified-trading-api/unified_trading_api/routes/market_data.py:33` — `GET /market-data/candles`. Today branches at line
50 on `mock_mode`; real branch instantiates `BatchCandleReader(project_id)` from `app.state.service._project_id`.
`BatchCandleReader` directly does storage + parquet I/O.

**Plan's change**: route still branches on `mock_mode`; real branch calls UTL
`MarketCandleDataDomainClient.get_candles(...)` after a manifest-prune step. `BatchCandleReader` deleted.

### Frontend

`components/widgets/terminal/use-terminal-page-data.ts` — already calls `/api/market-data/candles` via `useCandles()`
hook. Next.js rewrites proxy to backend. The mock-mode short-circuit at line 688 stays — when UI is in mock mode it
doesn't talk to the backend; when real, it does. **No frontend changes required for this plan.**

### BigQuery

Datasets `market_data_hft`, `market_data_candles_trades`, `candles_data` all exist. Schema right (DAY-partitioned +
clustered on venue/symbol/ instrument_id). **Inventory: ~empty for our target symbols.** Single BTC-USDT row family
from 2023. Treated as future optimization; not read in this plan's scope.

### Symbol/data-type alignment for `DEFAULT_INSTRUMENTS`

| UI venue              | UI symbol       | Bucket | `data_type` to use | GCS shard exists?             |
| --------------------- | --------------- | ------ | ------------------ | ----------------------------- |
| `BINANCE-FUTURES`     | `BTCUSDT`       | cefi   | `trades`           | ✅ verified 2026-04-14        |
| `BINANCE-FUTURES`     | `ETHUSDT`       | cefi   | `trades`           | ✅ verified 2026-04-14        |
| `NASDAQ`              | `AAPL`          | tradfi | `ohlcv_1m`         | ✅ verified 2026-04-13        |
| `NASDAQ`              | `MSFT`          | tradfi | `ohlcv_1m`         | ✅ verified 2026-04-13        |
| `NASDAQ`              | `GOOGL`         | tradfi | `ohlcv_1m`         | ✅ verified 2026-04-13        |
| `NYSE`                | `JPM`           | tradfi | `ohlcv_1m`         | ✅ verified 2026-04-13        |
| `HYPERLIQUID`         | `ETH`           | cefi   | `trades`           | not verified — out of MVP set |
| `CME`                 | `ES`            | tradfi | `ohlcv_1m`         | not verified — out of MVP set |
| `UNISWAP_V3-ETHEREUM` | `WETH-USDC-500` | defi   | varies             | not in scope                  |

**MVP target symbols for D-grade acceptance: 6 symbols with verified-existing shards.** Others render "No chart data
available" — correct behavior, not a regression.

---

## Goals

1. Backend `/market-data/candles` (real mode) reads candles via UTL `MarketCandleDataDomainClient.get_candles(...)`
   after a manifest-prune step that filters out dates with no MDPS shard for the requested `(timeframe, data_type)`.
2. Mock mode keeps returning seed candles — symbols UI sends now resolve to seed data the same way other widgets do.
3. Bucket variant (prod / test) is config-driven; flipping the env var changes which bucket family the UTL client
   targets, no code change.
4. `project_id` resolved via `UnifiedCloudConfig` (Secret Manager path), `GCP_PROJECT_ID` env as fallback. Loud 503 if
   both fail.
5. Opening `http://localhost:3000/services/trading/terminal` and selecting any of the 6 MVP symbols + a backfilled date
   renders real OHLCV candles from GCS — bytes match what `gcloud storage cat` of the parquet would show, projected to
   `{time, o, h, l, c, v}`.
6. Selecting a date with no shard renders the existing "No chart data available" empty state. Synthetic-fallback amber
   badge is **never** shown on the real-API path.
7. Scroll-back pagination walks one earlier `day=` partition per fetch, manifest-pruned to skip empty days, capped at
   `MAX_HISTORY_DAYS=30`.

---

## Plan units

Sequencing: E (benchmark) first, then A+F backend, B in parallel with A, C frontend if needed, D full-stack. F is a
documentation-only unit.

### Unit E — GCS read latency benchmark

**Goal**: capture today's read-path numbers before any refactor lands, so we have a baseline to measure plan changes
(manifest pruning, UTL path, future BQ swap) against.

**File**: new — `unified-trading-api/scripts/bench_candle_reads.py`.

**Symbol**: `NASDAQ:AAPL` 1m, `data_type=ohlcv_1m`. Recent backfilled trading day from the Jan→Apr-14 window Harsh ran
MDPS over.

**Scenarios** (5 runs each, report p50 + p99, log raw to a parquet):

1. **Single parquet, cold** — one file, fresh `get_storage_client()`.
   - `t_download_ms` (download_bytes call)
   - `t_parse_ms` (`pq.read_table`)
   - `t_project_ms` (project to `{time, o, h, l, c, v}`)
   - `bytes_transferred`, `n_rows`, `n_records_after_dropna`
2. **Single parquet, warm** — same call right after #1, connection reused. Captures TLS handshake savings.
3. **10 parquets, parallel** — 10 consecutive trading days (`from_date`/`to_date` window) using existing
   `ThreadPoolExecutor(max_workers=min(16, n))` pattern.
4. **10 parquets, sequential** — same window with `max_workers=1`. Isolates per-file cost.
5. **10 parquets, parallel + manifest pruned** — same as #3 but prefiltered via `read_availability_index(bucket)` so we
   only fetch days that exist. Pick a window that includes a weekend so pruning actually skips something. Captures the
   manifest-pruning win.
6. **30-day window, parallel + pruned** — bigger version of #5 to estimate worst-case scroll-back
   (`MAX_HISTORY_DAYS=30`).

**Capture per scenario**: wall-clock total, sum of download/parse/ project ms across files, total bytes, speedup ratios.

**Output**: write results table to `unified-trading-pm/reports/price_chart_gcs_benchmark_2026_04_29.md` (baseline) and
`unified-trading-pm/reports/price_chart_gcs_benchmark_2026_04_29_post.md` (post-Unit-A re-run for diff).

**Numbers to look for** (from parent doc §6 latency budget):

- Single file p50 download ≤ 50ms (warm), ≤ 200ms (cold). If higher, region mismatch or unexpected file size.
- 10-file parallel should be 5–8× sequential. If not, workers are serializing somewhere.
- 30-day pruned should ≤ 800ms p99. That's the parent doc's "fetch 2000 bars from cold" target.
- Manifest pruning win: scenario #5 vs #3 difference is the cost of empty-day round-trips today. If it's <10%, pruning
  is a nice-to-have; if >50% on a TRADFI window with weekends, pruning is mandatory.

**No code merges, no behavior changes.** Pure measurement. Runs against the current `BatchCandleReader` — gives us a
"before" number we can compare to "after" once Unit A lands.

### Unit A — backend route swaps to UTL domain client + manifest prune

**Files:**

- `unified-trading-api/unified_trading_api/routes/market_data.py`
- `unified-trading-api/unified_trading_api/services/batch_candles.py` → **delete**.
- New: `unified-trading-api/unified_trading_api/services/candle_query.py` — thin orchestrator that:
  1. Resolves bucket from `(category, project_id, variant)`.
  2. Loads `read_availability_index(bucket)` (UTL), cached in-process for ~60s, filters to the requested
     `(timeframe, data_type)` and date window — produces the list of days to actually fetch.
  3. For each remaining day, calls UTL
     `MarketCandleDataDomainClient.get_candles(date, instrument_id, timeframe, data_type, venue)`.
  4. Concatenates results, projects to `{time, o, h, l, c, v}`, dedupes + sorts, caps at `limit`.
- `unified-trading-api/unified_trading_api/config/curated_symbols.py` → keep as the per-symbol config source. Update
  entries so `data_type=ohlcv_1m` is used for TRADFI venues (NASDAQ, NYSE) and `data_type=trades` for CEFI
  (BINANCE-FUTURES, etc.). Verify the 6 MVP symbols have entries.

**Route behavior** (`/market-data/candles`):

- Mock mode (`get_mock_mode(request)` true): unchanged — `service.list("candles", filters={"instrument": ...})`, return
  seed.
- Real mode: call `candle_query.fetch(...)`. Empty result → return `single_response([], ...)` so chart shows "No chart
  data available".
- `project_id` resolution:
  1. `UnifiedCloudConfig().project_id` — canonical path (UTL → SM).
  2. fallback: `os.environ["GCP_PROJECT_ID"]`.
  3. neither → return 503 `{"error": "project_id_unresolved"}`.
- Bucket variant: read `MARKET_DATA_BUCKET_VARIANT` (default `prod`) from config. UTL bucket name =
  `market-data-tick-{category}-{variant_suffix}{project_id}` where `variant_suffix` is `""` for prod or `"test-"` for
  test.

**Smoke before merging:**

```
curl ":8030/market-data/candles?venue=NASDAQ&instrument=AAPL\
&timeframe=1m&count=400&mode=batch&as_of=2026-04-13"
# → expect ~390 bars matching the parquet's content
```

### Unit B — `curated_symbols.py` data-type per category

Audit `DEFAULT_INSTRUMENTS` against `curated_symbols.py`. Issues spot- checked 2026-04-29:

- TRADFI symbols (AAPL/MSFT/GOOGL/JPM) need entries with `data_type=ohlcv_1m`. If the file has them with
  `data_type=trades`, fix.
- BINANCE-FUTURES BTCUSDT/ETHUSDT need `data_type=trades`.
- Symbols not yet backfilled (HYPERLIQUID:ETH, CME:ES, UNISWAP_V3-ETHEREUM:WETH-USDC-500) — leave entries optional. UTL
  client returns `[]`, chart shows empty state. No regression.

Eventually `curated_symbols.py` should be replaced by the instruments-service catalogue lookup. Out of scope; flagged in
follow-up plan.

### Unit C — frontend (no-op verify)

The frontend's mock-mode short-circuit stays. Verify (don't change):

- `components/widgets/terminal/use-terminal-page-data.ts:688` — when `NEXT_PUBLIC_MOCK_API=false` (real-API mode),
  `apiCandles` reads from `useCandles` response. Path is correct as-is.
- `loadMoreCandles` (line 401) — early-returns in mock mode, fetches in real mode. Correct.
- Synthetic-data badge — only renders on the mock path (`isMockMode && candleData.length > 0`). On real-API path it
  can't fire. Correct.

If verification surfaces drift, fix in this unit. Otherwise unit closes with a note in the plan: "frontend already
correct, no changes required."

### Unit D — full-stack verification

After A + B + (E baseline) land:

1. Boot backend on `:8030` with:
   - `CLOUD_MOCK_MODE=false`
   - `GCP_PROJECT_ID=central-element-323112`
   - `MARKET_DATA_BUCKET_VARIANT=prod`
   - ADC creds available (`gcloud auth application-default login` or `GOOGLE_APPLICATION_CREDENTIALS=...`)
2. Boot UI with `NEXT_PUBLIC_MOCK_API=false`.
3. Open `http://localhost:3000/services/trading/terminal`.
4. For each MVP symbol:
   - Pick a backfilled date.
   - Pick a timeframe (start with 1H to match a known parquet).
   - Verify chart renders. Pixel-spot-check OHLC against parquet content via `gcloud storage cat … | parquet-tools head`
     or a 5-line python read.
5. Network tab: exactly one `/api/market-data/candles?...` call per `(symbol, timeframe, date)` change. No extra calls.
6. Scroll-back: one fetch per earlier day. Skipped days (manifest said empty) don't appear as fetches. Cap at 30 days
   back from initial as_of.
7. Pick a non-backfilled date. Confirm "No chart data available" empty state. **Confirm zero amber "Mock data:
   synthetic" badges.**
8. Switch timeframe (1m/5m/15m/1H/4H/1D). Each change → one fetch. Bar density reflows.

### Unit F — documentation update

**Files:**

- This plan doc: mark units A/B/C/D as completed with date.
- `unified-trading-pm/reports/price_chart_gcs_benchmark_2026_04_29.md`: Unit E baseline results.
- `unified-trading-pm/reports/price_chart_gcs_benchmark_2026_04_29_post.md`: post-Unit-A re-run for diff against
  baseline.
- `/codex/02-data/per-category-bucket-layouts.md`: confirm the file matches reality — it does, per the listing I did
  2026-04-29. No edit needed unless drift surfaces.
- Follow-up plan stub `unified-trading-pm/plans/ai/watchlist_from_instruments_2026_04_30.plan.md` — empty skeleton
  noting we'll source the watchlist from instruments-service once the chart path is live.

---

## Out-of-scope blockers worth flagging

These don't block this plan but limit how far it can optimize. Each needs a separate plan / separate owner.

1. **MDPS manifest writer underfilling.** Per `/codex/02-data/availability-manifest-and-data-status.md` §"Per-Service
   Shard Dimension Matrix · Layer 2.5", MDPS rows should populate `(venue, data_type, instrument_type, timeframe)`. They
   currently only populate `(date, data_type, timeframe)` — `venue` and `instrument_id` empty. This blocks per-symbol
   pruning. Fix lives in `market-data-processing-service` ManifestWriter call sites.
2. **BQ candles backfill.** `market_data_hft.candles_*` has 2 days of 2023 BTC-USDT and nothing else. If we ever want to
   switch the UTL client to BQ-backed for multi-day windows, the same parquet data MDPS writes to GCS needs to land in
   BQ too. Likely a `bq load` step at the end of MDPS's pipeline, or a scheduled parquet-to-BQ load job. Owner: MDPS /
   data engineering.
3. **Frontend instrument list.** `DEFAULT_INSTRUMENTS` is hardcoded. Real fix is reading from instruments-service via
   the matching domain client (`InstrumentsDomainClient.get_instruments_for_date`). Separate plan.

---

## Live mode appendix — out of scope, documented for later

Asked: "is the websocket implemented to support live data?"

**Answer**: endpoint exists, real-mode subscriber not wired.

- `unified-trading-api/unified_trading_api/routes/websocket.py:127` — `@router.websocket("/ws")` registers. UI connects
  via `ws://localhost:8030/ws` from `components/widgets/terminal/use-terminal-page-data.ts:467` guarded on
  `context.mode === "live"`.
- Mock-mode generator (line 270) emits Brownian-motion ticks every 0.5–2s. Works.
- Real-mode branch: docstring says _"In real mode: subscribes to PubSub topics via UCI"_ — but the actual `else` branch
  isn't wired. The intended architecture is in place; the implementation is missing.
- Where real ticks come from: MTDS (`market-tick-data-service`) owns the venue-side tick ingest. MDPS aggregates to
  bars. Per parent doc §3, bars and open-bar updates should publish to a pub-sub topic; the API's `/ws` should subscribe
  and forward.
- **No codex doc** currently SSOTs the MDPS→pub-sub→API→UI live forwarding path. Closest is parent doc
  `market_data_delivery_architecture_2026_04_27.md` §3 (proposed schema, not codex-blessed yet).

**For this plan's scope**: live tick delivery is deferred. The chart's existing locally-ticking `liveCandle` overlay
continues to animate the open bar in real-API mode. It overlays on top of the most recent real bar; on bar-close
boundary the next backend fetch picks up the closed bar and the overlay restarts. Acceptable interim behavior; codex
parent-doc Phase 4 replaces it wholesale.

---

## Acceptance criteria

A. With backend on `:8030` (`CLOUD_MOCK_MODE=false`, `GCP_PROJECT_ID=central-element-323112`,
`MARKET_DATA_BUCKET_VARIANT=prod`) and UI on `:3000` (`NEXT_PUBLIC_MOCK_API=false`), loading
`http://localhost:3000/services/trading/terminal` and selecting `NASDAQ:AAPL` with `2026-04-13` and `1H` renders candles
whose `(o, h, l, c, v)` match
`gs://market-data-tick-tradfi-central-element-323112/processed_candles/by_date/day=2026-04-13/timeframe=1h/data_type=ohlcv_1m/venue=NASDAQ/AAPL.parquet`.

B. Same for the other 5 MVP symbols on dates with backfilled shards.

C. Selecting a non-backfilled date renders "No chart data available for X". Amber synthetic-data badge is not visible.

D. Scrolling back walks one earlier `day=` partition per fetch against the backend, manifest-pruned to skip days marked
empty, cap at 30 days from initial as-of.

E. Switching timeframe (1m/5m/15m/1H/4H/1D) issues exactly one fetch per (timeframe, date, instrument) tuple.

F. Network panel shows zero `generateCandleData` / `mock01` / `mockRange` calls on the chart's data path in real-API
mode.

G. Backend benchmarks documented in `reports/price_chart_gcs_benchmark_2026_04_29{,_post}.md` show 30-day pruned p99 ≤
800ms (parent doc target). If it's slower, note the gap and what would close it (Phase-1 monthly rollup, BQ swap, etc.)
— closing the gap is not a blocker for this plan.

H. `MARKET_DATA_BUCKET_VARIANT=test` flip targets the `*-test-*` bucket family without code changes. (Even if test
bucket is empty — verifying the routing, not the data.)

---

## Sequencing summary

1. **E** — benchmark current code (no merge, no behavior change). Captures baseline.
2. **A + B** — backend swaps to UTL + manifest prune; `curated_symbols` aligned with category data-types.
3. **C** — frontend no-op verify (likely closes empty).
4. **D** — full-stack acceptance.
5. **E re-run** — same scenarios, new code path. Diff numbers go into the benchmark doc.
6. **F** — plan + benchmark doc closeout, follow-up plan stub.

After F: this plan's scope closes. Watchlist follow-up + MDPS manifest writer + BQ backfill are tracked separately.

---

## Pointers back to the parent reference

| This plan does                                                      | Parent doc Phase                                                                             |
| ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Read pre-aggregated candles only — never raw, never resample        | Invariant 1 — preserved                                                                      |
| Address by `(date, timeframe)` — keep `as_of`/`from_date`/`to_date` | Defers Invariant 2 (time-range) → parent Phase 2                                             |
| No client BarStore — keep React Query keying                        | Defers parent Phase 3                                                                        |
| No WS bar deltas — locally-ticking open bar overlay                 | Defers parent Phase 4                                                                        |
| No monthly rollup — full-day parquets                               | Defers parent Phase 1                                                                        |
| Manifest-prune at the API layer                                     | Net new — codex SSOT pattern, lights up the path the parent doc's later phases will optimize |
| Single domain-client entrypoint = swap-able later                   | Foundation for parent Phase 1 (storage swap) and a future BQ-backed implementation           |

The plan deliberately stays at the lowest-leverage rung that lights up the read path. Parent doc Phase 1 (per-month
OHLCV rollup) is the next-leverage move once we have working baseline numbers from Unit E.
