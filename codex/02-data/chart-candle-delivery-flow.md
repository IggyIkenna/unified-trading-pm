---
doc_type: codex-ssot
title: Chart Candle Delivery — End-to-End Flow
summary:
  End-to-end SSOT for historical chart-candle delivery — price-chart widget → Next.js rewrite → unified-trading-api
  /market-data/candles → BatchCandleReader manifest-prune + parallel GCS processed_candles read → response envelope;
  covers per-category data_type divergence, mode toggles, perf shape, and a layer-by-layer debug path.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    market-data-processing-service,
    unified-trading-api,
    unified-trading-library,
    unified-trading-pm,
    unified-trading-system-ui,
  ]
scope: [engineer]
tags: [ui, mdps, manifest, data-pipeline, performance, mtds]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/partitioning.md,
  ]
created: 2026-04-30
authoritative_for: [chart candle delivery end-to-end flow (GCS parquet to price-chart widget)]
referenced_by:
  [/codex/02-data/availability-manifest-and-data-status.md, /codex/02-data/bar-boundary-candle-edge-convention.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Chart Candle Delivery — End-to-End Flow

> **This document is the single source of truth** for how a candle bar travels from a GCS parquet shard to a pixel on
> the price-chart widget. Engineers debugging "why isn't my chart loading" should start here, walk the path, and
> identify which layer is silent / broken.

**Status**: canonical (since 2026-04-30, after price-chart GCS delivery shipped on `feat/price-chart-gcs-delivery`
across 4 repos).

**Scope**: historical candle delivery only. Live tick / WebSocket bar deltas are deferred — see
`market_data_delivery_architecture_2026_04_27.md` §Phase 4 for the planned shape.

**Cross-refs**:

- `availability-manifest-and-data-status.md` — manifest schema + lifecycle
- `per-asset-group-bucket-layouts.md` — actual GCS hive paths per asset group
- `subscription-model.md` — domain client architecture
- `partitioning.md` — hive `key=value` pattern + BQ external table option

---

## End-to-end picture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser (chart widget)                                             │
│                                                                     │
│  components/widgets/terminal/price-chart-widget.tsx                 │
│         │                                                           │
│         │  reads from useTerminalData() context                     │
│         ▼                                                           │
│  components/widgets/terminal/use-terminal-page-data.ts              │
│   ├── useCandles()    ← React Query, initial paint + date pick      │
│   └── loadMoreCandles ← scroll-back, 7-day chunked window           │
│         │                                                           │
└─────────│───────────────────────────────────────────────────────────┘
          │  GET /api/market-data/candles
          │   ?venue=NASDAQ
          │   &instrument=AAPL
          │   &timeframe=1m
          │   &count=5000
          │   &mode=batch
          │   &from_date=2026-04-06
          │   &to_date=2026-04-13
          │
          ▼  (Next.js rewrites in next.config.mjs)
┌─────────────────────────────────────────────────────────────────────┐
│  Next.js dev server :3000                                           │
│                                                                     │
│  next.config.mjs rewrites:                                          │
│    /api/market-data/* → ${NEXT_PUBLIC_UNIFIED_API_URL}/market-data/*│
└─────────│───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  unified-trading-api :8030                                          │
│                                                                     │
│  routes/market_data.py — GET /market-data/candles                   │
│   ├── if mock_mode: return seed from MockStateStore (out of scope)  │
│   └── if real:                                                      │
│        ├── resolve project_id (UnifiedCloudConfig → env → 503)      │
│        └── BatchCandleReader(project_id).get_candles(...)           │
│              │                                                      │
│              ▼                                                      │
│        services/batch_candles.py                                    │
│         1. Build bucket name                                        │
│            market-data-tick-{cefi|tradfi|defi}-{[test-]project_id}  │
│         2. Manifest prune                                           │
│            ↓                                                        │
└──────────────┼──────────────────────────────────────────────────────┘
               │ GET _index/availability_index.parquet  (cached 60s)
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  GCS bucket: market-data-tick-tradfi-prd-{project_id}                   │
│                                                                     │
│  _index/availability_index.parquet  (canonical, ~60s fresh)         │
│  _index/per_vm/{instance}.parquet   (writers append here)           │
│                                                                     │
│  ↑ rebuild flow ──────────────────────────────────────────────────  │
│  market-data-processing-service writes processed_candles/ +         │
│  emits ManifestWriter.add() rows → per-VM shard.                    │
│  manifest-consolidator Cloud Run Job (cron */1 * * * *) merges      │
│  all per-VM shards into the canonical blob.                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
               │
               │ filter rows where:
               │   service_name='market-data-processing-service'
               │   data_type=ohlcv_1m | trades | ...
               │   timeframe=1m | 5m | 1h | ...
               │   venue=NASDAQ | BINANCE-FUTURES | ...
               │   instrument_id=AAPL | BTCUSDT | ...
               │   available=True
               │
               ▼  set of dates that have shards (skip empty days)
┌─────────────────────────────────────────────────────────────────────┐
│  ThreadPoolExecutor(max_workers=16)                                 │
│                                                                     │
│  Per remaining day, in parallel:                                    │
│   GET processed_candles/by_date/                                    │
│         day=YYYY-MM-DD/                                             │
│         timeframe={tf}/                                             │
│         data_type={dt}/                                             │
│         venue={V}/                                                  │
│         {SYMBOL}.parquet                                            │
│                                                                     │
│  → urllib3 pool tuned to maxsize=32 to avoid TLS re-handshakes      │
│  → pyarrow.parquet.read_table → pandas DataFrame                    │
└─────────────────────────────────────────────────────────────────────┘
               │
               │  dropna(open/high/low/close), sort by timestamp
               │  project to {time, open, high, low, close, volume}
               │  cap at limit (most recent N bars)
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Response envelope (single_response wrap):                          │
│                                                                     │
│  {                                                                  │
│    "data": [                                                        │
│      { "time": 1776085200, "open": 259.58, "high": 259.58,          │
│        "low": 259.58, "close": 259.58, "volume": 20.0 },            │
│      ...                                                            │
│    ],                                                               │
│    "mode": "batch",                                                 │
│    "as_of": "2026-04-13",                                           │
│    "instrument": "AAPL",                                            │
│    "timeframe": "1m"                                                │
│  }                                                                  │
└─────────────────────────────────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Back in use-terminal-page-data.ts                                  │
│                                                                     │
│  - Initial fetch: candleData = result.data                          │
│  - Scroll-back:   olderCandles = [...result.data, ...olderCandles]  │
│  - Merge + dedupe by time, sort ascending                           │
│  - Pass to <CandlestickChart> (Lightweight Charts wrapper)          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Layer-by-layer SSOT

### 1. Frontend widget

| Component                | Path                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------ |
| Chart widget (consumer)  | `unified-trading-system-ui/components/widgets/terminal/price-chart-widget.tsx`                   |
| Data hook                | `unified-trading-system-ui/components/widgets/terminal/use-terminal-page-data.ts`                |
| API hook (initial paint) | `unified-trading-system-ui/hooks/api/use-market-data.ts` — `useCandles(...)`                     |
| Static instrument list   | `use-terminal-page-data.ts` — `DEFAULT_INSTRUMENTS` (until watchlist follow-up plan replaces it) |

**Mode toggle**: `NEXT_PUBLIC_MOCK_API` env var.

- `true` → in-browser fixtures via `lib/api/mock-handler.ts`. Backend never hit.
- `false` → real API call through Next.js rewrite.

**Scroll-back contract**:

- Window: `SCROLLBACK_WINDOW_DAYS = 7` calendar days per fetch.
- History cap: `MAX_HISTORY_DAYS = 90` from initial as-of.
- One in-flight fetch at a time (`inflightRef`).
- Pointer (`earliestLoadedRef`) advances even on empty windows so consecutive empty days don't stall scroll-back.

### 2. Next.js proxy

| Component       | Path                                                            |
| --------------- | --------------------------------------------------------------- |
| Rewrite config  | `unified-trading-system-ui/next.config.mjs`                     |
| Backend URL env | `NEXT_PUBLIC_UNIFIED_API_URL` (default `http://localhost:8030`) |

Maps `/api/market-data/*` → `${NEXT_PUBLIC_UNIFIED_API_URL}/market-data/*`. Browser-side path stays under `/api/...`;
backend has no `/api` prefix.

### 3. unified-trading-api route

| Component         | Path                                                                                         |
| ----------------- | -------------------------------------------------------------------------------------------- |
| Route handler     | `unified-trading-api/unified_trading_api/routes/market_data.py` — `GET /market-data/candles` |
| Reader            | `unified-trading-api/unified_trading_api/services/batch_candles.py` — `BatchCandleReader`    |
| Per-symbol config | `unified-trading-api/unified_trading_api/config/curated_symbols.py`                          |

**Mode toggle**: `CLOUD_MOCK_MODE` env var.

- `true` → seed candles from in-memory `MockStateStore`.
- `false` → real GCS read via `BatchCandleReader`.

**Required env for real mode**:

- `CLOUD_PROVIDER=gcp`
- `GCP_PROJECT_ID=...` (or resolved via `UnifiedCloudConfig` → Secret Manager)
- `MARKET_DATA_BUCKET_VARIANT=prod|test` (default `prod`)
- ADC credentials for GCS

**Loud failure modes**:

- `venue` query param missing → 200 + `warning="venue required"` + empty data
- `project_id` unresolvable → 503 `{ "error": "project_id_unresolved" }`

### 4. Manifest layer

Full lifecycle is documented in `availability-manifest-and-data-status.md`. Quick recap as it pertains to the chart
route:

| Step              | Component                                  | Path                                                                      |
| ----------------- | ------------------------------------------ | ------------------------------------------------------------------------- |
| Read              | UTL `read_availability_index(bucket)`      | `unified-trading-library/unified_trading_library/manifest_writer.py:1764` |
| Cache             | In-process LRU (per process)               | TTL 60 s, key=bucket                                                      |
| Reader fallback   | Consolidated → per-VM merge → self-shard   | Same module                                                               |
| Write (per shard) | UTL `ManifestWriter.add(...)` + `.write()` | Same module                                                               |
| Consolidate       | `manifest-consolidator` Cloud Run Job      | `*/1 * * * *` cron, deployment-service Terraform                          |
| Rebuild from GCS  | `rebuild_processed_candles_manifest.py`    | `market-data-processing-service/scripts/`                                 |

**Read path used by the chart route** (`BatchCandleReader._prune_dates_via_manifest`):

1. `read_availability_index(bucket)` — first call cold-downloads, subsequent 60 s window → memory hit.
2. Filter to MDPS-owned rows for the exact `(data_type, timeframe, venue, instrument_id, available=True)` shard tuple.
3. Set of present dates → intersect with the requested window.
4. Empty manifest → no pruning (fall through; GCS is final source of truth).
5. No matching rows → no pruning (per-symbol manifest underfill is a known gap; covered in
   `availability-manifest-and-data-status.md` §Per-Service Shard Dimension Matrix).

**Critical invariant** (learned 2026-04-29): manifest writes MUST go through `ManifestWriter.add()` → per-VM shard.
Direct writes to `_index/availability_index.parquet` are silently overwritten by the next `manifest-consolidator` cron
cycle. The rebuild script honors this; the plan-doc §3a section explains why.

**Critical UTL fix** (also 2026-04-29, commit `7af5a4e` in unified-trading-library): the reader now always merges per-VM
shards regardless of feature flag, and `_read_and_merge_per_vm_shards` correctly handles `BlobMetadata` objects (was
`isinstance(p, str)` which silently dropped every shard). Without that fix our rebuild script's writes would land on
disk but never appear in `read_availability_index` output.

### 5. GCS data layer

Path conventions are SSOT in `per-asset-group-bucket-layouts.md`.

For chart candles specifically:

```
gs://market-data-tick-{cefi|tradfi|defi}-{[test-]project_id}/
  processed_candles/by_date/
    day=YYYY-MM-DD/
      timeframe={15s|1m|5m|15m|1h|4h|24h}/
        data_type={trades|ohlcv_1m|book_snapshot_5|...}/
          venue={NASDAQ|BINANCE-FUTURES|...}/
            {SYMBOL}.parquet
```

**⛔ SUPERSEDED 2026-07-26 (cefi_residual_followups_after_honest_done_2026_07_17.md Phase 2):** ~~Filename is the bare
symbol, not the canonical `venue:type:symbol` instrument-key.~~ Post the D3/D4 wire→canonical cutover, the leaf is
`{instrument_id}.parquet` where `instrument_id` IS the canonical id (`market-data-processing-service`
`output_path_helpers.py::candle_leaf_filename`) — a bare-wire-symbol filename is the legacy pre-migration form, not the
current writer output. The one exception: chain-bundle types (`options_chain`/`futures_chain`) write a single
`underlying={U}/ticks.parquet` per (date, root) instead of per-instrument. Tie-breaker SSOT:
[`cross-asset-canonical-target-ssot.md`](cross-asset-canonical-target-ssot.md) §0/§1. Per-category divergence (data_type
segment, unaffected by the leaf-naming correction above):

| Category | `data_type` segment value used by MDPS                   |
| -------- | -------------------------------------------------------- |
| CEFI     | `trades` (e.g. BINANCE-FUTURES)                          |
| TRADFI   | `ohlcv_1m` (e.g. NASDAQ, NYSE — pre-aggregated upstream) |
| DEFI     | varies by data_type — see `defi-data-types-catalog.md`   |

A reader that hardcodes `data_type=trades` for everything will silently return zero bars for all TRADFI symbols. The
chart route dispatches correctly via `curated_symbols.py`.

### 6. Parquet schema

Set by `market-data-processing-service` `canonical_writer.py`. Columns:

| Column                                               | Type             | Notes               |
| ---------------------------------------------------- | ---------------- | ------------------- |
| `timestamp`                                          | `datetime64[ns]` | Bar open time (UTC) |
| `timestamp_out`                                      | `int64`          | Sequence id         |
| `venue`, `symbol`, `instrument_id`                   | `string`         | Identity            |
| `open`, `high`, `low`, `close`                       | `float64`        | OHLC                |
| `volume`                                             | `float64`        | Trading volume      |
| `trade_count`, `buy_trade_count`, `sell_trade_count` | `int64`          |                     |
| `buy_volume`, `sell_volume`                          | `float64`        |                     |
| `delay_*_ms`                                         | `float64`        | Pipeline lag stats  |

Reader projects to chart-friendly `{time, open, high, low, close, volume}` where `time` is unix seconds. NaN OHLC rows
are dropped (TRADFI shards have NaN rows for outside-RTH minutes; chart never receives those).

---

## Configuration matrix

What flag controls what at each layer:

| Layer   | Env var / config                        | Effect                                                 |
| ------- | --------------------------------------- | ------------------------------------------------------ |
| Browser | `NEXT_PUBLIC_MOCK_API`                  | `true` = browser fixtures, `false` = call backend      |
| Browser | `NEXT_PUBLIC_UNIFIED_API_URL`           | Backend URL for the rewrite (default `localhost:8030`) |
| Backend | `CLOUD_MOCK_MODE`                       | `true` = seed candles, `false` = real GCS              |
| Backend | `CLOUD_PROVIDER=gcp`                    | Required when real                                     |
| Backend | `GCP_PROJECT_ID`                        | Required when real (or via `UnifiedCloudConfig`)       |
| Backend | `MARKET_DATA_BUCKET_VARIANT=prod\|test` | Bucket suffix toggle (default prod)                    |
| Backend | `DISABLE_AUTH=true`                     | Local dev only — skip API key check                    |

---

## Performance shape (current, 2026-04-30)

| Scenario          | Workstation p50 | Co-located backend (estimated) |
| ----------------- | --------------- | ------------------------------ |
| Single day, 1m    | ~1100 ms        | 50–100 ms                      |
| 7-day window, 1m  | ~1240 ms        | ~200 ms                        |
| 30-day window, 1m | ~2150 ms        | 300–400 ms                     |

Single-file timing breakdown: **97 % download (HTTP RTT), 0.2 % parse, 1.4 % project**. Bottleneck is round-trip, not
CPU.

Parallel speedup: **8.0×** for 10-day vs sequential, after the `urllib3 pool_maxsize=32` fix in
`BatchCandleReader._tune_connection_pool`. Pre-fix the pool was the default 10; concurrent requests past that point
re-handshook TLS and the parallel scenario fell to ~4× single-day instead of 1×.

Numbers from `unified-trading-pm/reports/price_chart_gcs_benchmark_2026_04_29*.md`.

**Future-leverage moves** (covered in `market_data_delivery_architecture_2026_04_27.md` §Phases):

- Phase 1: per-month parquet rollups → 22× round-trip reduction for typical 1-month chart windows.
- Phase 2: time-range addressing (`from_ts` / `to_ts` instead of `from_date` / `to_date`) + count-based fetches
  (`(end_ts, count)`).
- Phase 3: client-side BarStore — chart asks for visible-range, store decides what to fetch.
- Phase 4: WebSocket bar deltas for live updates.

---

## Debugging path — "my chart isn't loading"

Walk the layers in order:

1. **Is real mode actually on?** Check `NEXT_PUBLIC_MOCK_API` in the browser process env. If `true`, the route is never
   hit.
2. **Does the backend boot?** `curl http://localhost:8030/health`. If not, check `CLOUD_PROVIDER`, `GCP_PROJECT_ID`, and
   ADC creds.
3. **Does the route return 200 with bars?**
   `curl ":8030/market-data/candles?venue=NASDAQ&instrument=AAPL&timeframe=1m &count=10&mode=batch&as_of=<recent-date>"`.
   If `data` is empty, check:
   - Is the symbol in `curated_symbols.py` with the right `data_type`?
   - Does the GCS shard actually exist?
     `gcloud storage ls "gs://market-data-tick-tradfi-prd-{project}/processed_candles/by_date/day=YYYY-MM-DD/timeframe=1m/data_type=ohlcv_1m/venue=NASDAQ/AAPL.parquet"`
   - Did manifest pruning eat the dates? Check `read_availability_index({bucket})` — see
     `availability-manifest-and-data-status.md` for inspection commands.
4. **Does the UI proxy forward correctly?** `curl "http://localhost:3000/api/market-data/candles?..."`. Should return
   identical JSON to the backend direct call.
5. **Does `loadMoreCandles` silently break?** Check that response field name is `data` not `candles` (historical bug —
   fixed `feat/price-chart-gcs-delivery` in commit `252c7141`).

---

## Related decisions

- Why GCS via UTL, not BigQuery, for read path: `market_data_delivery_architecture_2026_04_27.md` (parent reference) +
  `price_chart_gcs_delivery_2026_04_29.plan.md` §Why GCS via UTL, not BQ.
- Why not commit a local `BarStore` yet: `market_data_delivery_architecture_2026_04_27.md` §Phase 3.
- Why scroll-back is chunked windows (7 days) and not bar-count-based: `price_chart_gcs_delivery_2026_04_29.plan.md`
  §Out of scope (defers to parent-doc Phase 2).
