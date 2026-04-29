---
title: "Instruments + Market Data — GCS→API→Trading Terminal Wiring"
id: instruments_market_data_batch_wiring_2026_04_26
status: in_progress
created: 2026-04-26
updated: 2026-04-26
feature_branch: live-defi-rollout
locked_by: live-defi-rollout
priority: P0
repos_affected:
  - unified-trading-api
  - unified-trading-system-ui
  - market-tick-data-service
  - instruments-service
scope_note: |
  TRADING TERMINAL only — /services/trading/terminal watchlist + price chart.
  The /services/data/* pages (instruments browser, coverage, gaps, etc.) are served by
  deployment-ui and are OUT OF SCOPE for this plan.
---

# Instruments + Market Data — Trading Terminal Batch Wiring

## Scope

Target surface: **`/services/trading/terminal`** — specifically:
- **Watch list** (left panel): instrument list scoped to asset group, live vs expired toggle
- **Price chart** (centre): TradingView Lightweight Charts with real candle data, scroll-back, timeframe switching

Out of scope: `/services/data/*`, deployment-ui data coverage pages (those stay separate).

Batch mode first. Live (WebSocket) wiring is a later phase once batch is validated.

---

## Track A — Instrument Wiring

### Current state (audit 2026-04-26)

**Backend**
- `GET /instruments/list` exists — filters by `venue` + `asset_group`, but reads from `MockDomainService` (hardcoded fixtures)
- `instruments-service` repo exists at `/home/hk/unified-trading-system-repos/instruments-service/` but is NOT integrated into unified-trading-api
- GCS has `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet` for CEFI/TRADFI/DEFI/PREDICTION
- SPORTS diverges: `sports_reference/by_date/day={date}/entity={entity}/{entity}.parquet` — no venue level, entity-based
- `GcsDomainService` has `_COLLECTION_TO_DATASET` mapping but no "instruments" entry

**Frontend**
- `use-terminal-page-data.ts` calls `useInstruments()` then falls back to `DEFAULT_INSTRUMENTS` (5 hardcoded symbols) when no real data
- `WatchlistPanel` is a clean presentational component — just needs real data fed in via props
- No live/expired toggle in current watchlist
- `WatchlistSymbol` type has no `expiry` or `status` field

### Instrument schema gaps (need to add)

| Field | Source | Note |
|-------|--------|------|
| `status` | GCS instruments parquet | `active` \| `expired` \| `delisted` |
| `expiry_date` | GCS instruments parquet | ISO date; options, futures, sports matches |
| `match_end` | GCS sports_reference | Match completion timestamp (sports) |
| `asset_group` | GCS parquet + UAC | CEFI/DEFI/TRADFI/SPORTS/PREDICTIONS |
| `instrument_type` | GCS parquet | spot/perp/future/option/lp_pool/odds |

### Backend caching strategy

Instruments update hourly at most (expiry events, new listings). Do NOT read parquet on every request.

Recommended: server-side in-memory cache on `GcsDomainService` with TTL = 1h.
- On first call to `service.list("instruments", ...)`: read parquet, populate cache
- Subsequent calls: return from cache if age < 1h
- On expiry/delist event (webhook or scheduled refresh): invalidate
- Size estimate: < 10MB per asset_group, < 50MB total (safe for in-memory)

### Live vs expired display

- **CeFi/TradFi**: filter by `expiry_date > today` for options/futures; perps/spot never expire
- **DeFi**: LP pools expire when liquidity is removed; `status === "active"`
- **Sports**: show `status !== "finished"` for live view; finished matches shown if user toggles "include expired"
- **Predictions**: markets close when resolved; `status === "active"` for live view

### Implementation steps (Track A)

**A1 — API**: Add `as_of` + `status` params to `GET /instruments/list`; add "instruments" collection to `GcsDomainService` with 1h cache; parse `instrument_availability` parquets (per-category path logic)

**A2 — API**: Handle SPORTS instruments separately via `sports_reference` entity path (fixtures entity = the instrument list for sports)

**A3 — UI**: Extend `WatchlistSymbol` type with `expiry_date?`, `status`, `asset_group`; add live/expired toggle to `WatchlistPanel`; update `use-terminal-page-data.ts` instruments mapping to pass through new fields

**A4 — UI**: Replace hardcoded `DEFAULT_INSTRUMENTS` fallback with proper loading state; show skeleton while instruments load

---

## Track B — Market Data (Candles) Wiring

### Current state (audit 2026-04-26)

**Backend**
- `GET /market-data/candles` exists — accepts `(instrument, interval, limit, _venue)` — `mode` and `as_of` NOT in route signature (ignored even if sent)
- `CanonicalParquetReader` is FULLY IMPLEMENTED in `market-tick-data-service/market_tick_data_service/reader.py`:
  - `read_shard(venue, date, data_type, instrument_type, instrument_id=None, ...)` with pyarrow predicate pushdown
  - `list_instruments(venue, date, ...)` for discovery
  - Tests exist
- `GcsDomainService` does NOT import or use `CanonicalParquetReader`
- GCS path templates per asset group:
  - CEFI/TRADFI: `raw_tick_data/by_date/day={date}/category={cat}/venue={venue}/instrument_type={itype}/data_type={dt}/{SYMBOL}.parquet`
  - DEFI: adds `chain={chain}/` partition
  - SPORTS: adds `league={league}/` partition, `category=sports` (lowercase)
  - PREDICTION: no `category=` or `venue=` partitions

**Frontend**
- `useCandles(venue, symbol, timeframe, 200, modeParam, asOfParam)` already passes `mode` + `asOf` to API
- `candleData` in `use-terminal-page-data.ts`: tries API first, falls back to `generateCandleData()` (mock)
- `CandlestickChart` already handles live tick update via `series.update()` (same-bar) vs full `setData()` reload
- Chart remounts on `key={symbol}-{timeframe}` change → clean re-render on instrument or timeframe switch
- **No scroll-back pagination** — fetches exactly 200 candles, no `subscribeVisibleTimeRangeChange` handler
- **No client-side cache** — React Query default cache only (staleTime = 0)
- WebSocket: `useWebSocket` connects to `ws://localhost:8030/ws`, enabled only in `context.mode === "live"`. Updates `livePrice`, `wsBid`, `wsAsk`, and current candle via `liveCandle` state

### Batch mode data flow (target)

```
User selects instrument + timeframe + date
  → useCandles(venue, symbol, tf, 200, "batch", asOf)
  → GET /api/market-data/candles?instrument=…&interval=1m&mode=batch&as_of=2026-01-15
  → API: GcsDomainService → CanonicalParquetReader.read_shard(venue, asOf, data_type, instrument_type, instrument_id=symbol)
  → Returns 200 OHLCV rows as JSON
  → UI: CandlestickChart.setData(rows)
```

### Scroll-back / historical pagination (target design)

Lightweight Charts exposes `subscribeVisibleTimeRangeChange`. When the left edge is reached:

```
User scrolls left past first candle
  → LWC fires visibleTimeRangeChange event
  → Detect: logicalRange.from < threshold (e.g. < 20 bars from left edge)
  → Trigger: fetchOlderCandles(symbol, tf, oldestLoadedTime - window)
  → GET /api/market-data/candles?instrument=…&mode=batch&from_date=…&to_date=…
  → Prepend response to existing array (setData with merged + sorted candles)
  → LWC preserves scroll position
```

### Client-side candle cache (target design)

React Query already caches by queryKey. Increase `staleTime` to preserve data across timeframe switches:

```typescript
// In useCandles:
staleTime: 5 * 60 * 1000,  // 5 min — batch data doesn't change
gcTime: 30 * 60 * 1000,    // 30 min in memory
```

For scroll-back pagination: accumulate loaded pages in a `useRef` map keyed by `{symbol}_{tf}_{from}`:
```
candleCache.set(`${symbol}_${tf}_${fromDate}`, pages)
```

When timeframe switches, keep the same visual time range centre (read `getVisibleLogicalRange` before switch, restore after new data loads).

### Live mode additions (future phase, after batch validated)

- WebSocket subscription to tick stream → `update()` on current candle (already partially wired)
- Historical data loaded via REST batch endpoint as seed
- New ticks appended via WebSocket; on candle close: `setData()` call to append completed candle
- Polling fallback if WebSocket drops (reconnect with exponential backoff — `useWebSocket` already has this)

### Implementation steps (Track B)

**B1 — API**: Add `mode: str = "batch"`, `as_of: date | None`, `from_date: date | None`, `to_date: date | None` params to `GET /market-data/candles`

**B2 — API**: Wire `GcsDomainService` to `CanonicalParquetReader` for "candles" collection — per-asset-group path template dispatch (CEFI/TRADFI vs DEFI vs SPORTS vs PREDICTION)

**B3 — API**: Map candle response from raw parquet columns (timestamp, open, high, low, close, volume) to API schema

**B4 — UI**: Add `from_date`/`to_date` params to `useCandles` hook and API fetch URL

**B5 — UI**: Add `subscribeVisibleTimeRangeChange` handler in `PriceChartWidget` — trigger `fetchOlderCandles` when near left edge; wire to parent via callback or local state in the widget

**B6 — UI**: Increase `staleTime` in `useCandles` to 5min; add candle page accumulator (prepend older pages)

**B7 — UI**: Restore visible range position after timeframe switch

---

## Candle data — per asset group architecture (confirmed 2026-04-26)

### CEFI (aggregate from trades)
- GCS data_type: `trades`
- Parquet columns: `instrument_key, price, size, aggressor_side, trade_id, ts_event (int64 ns), ts_init (int64 ns)`
- API flow: read_shard → convert ts_event ns→datetime → pandas resample by interval → OHLCV
- Column projection: load only `ts_event, price, size` (3 cols vs 7 full = ~60% smaller read)
- Venues confirmed with data: BINANCE-FUTURES, BYBIT, DERIBIT, OKX, HYPERLIQUID, COINBASE-SPOT

### TRADFI (native OHLCV — direct read)
- GCS data_type: `ohlcv_1m`, `ohlcv_15m`, `ohlcv_1h`, `ohlcv_1d`
- No aggregation needed — already OHLCV format from Databento
- Fastest path: `read_shard(venue, date, data_type="ohlcv_1m", ...)` → return directly
- Venues confirmed with data: NYSE, NASDAQ, CME, ICE, FX, CBOE

### DEFI (aggregate from oracle_prices — simpler than dex_swaps)
- GCS data_type: `oracle_prices` (preferred) or `dex_swaps`
- `oracle_prices` gives a clean price series; aggregate to bars like CEFI trades
- `dex_swaps` requires computing price from reserve amounts — more complex, skip for now
- Venues confirmed with data: UNISWAP_V3, AAVEV3, CURVE, LIDO, MORPHO on Ethereum

### TimeframeResampler
- EXISTS at `features-delta-one-service/features_delta_one_service/app/core/timeframe_resampler.py`
- Uses pandas resample with: open=first, high=max, low=min, close=last, volume=sum
- Do NOT import from features-delta-one-service in the API (wrong dependency direction)
- Pattern: inline the ~20-line aggregation directly in the API candles route, or add to UTL

### CanonicalParquetReader gap
- `read_shard()` does NOT expose a `columns` param — loads full DataFrame
- `list_instruments()` already uses `columns=["symbol"]` projection internally
- Fix: add `columns: list[str] | None = None` to `read_shard()` and pass through to pq.read_table
- This is a 3-line change in MTDS reader.py — required before CEFI wiring to avoid loading full trades rows

### Curated symbol config (replaces GCS instrument list)
Since only a handful of symbols have market data, define a static config in the API:
```python
CURATED_SYMBOLS = {
    "cefi": [
        {"venue": "BINANCE-FUTURES", "symbol": "BTCUSDT", "instrument_type": "perpetual", "data_type": "trades"},
        {"venue": "BINANCE-FUTURES", "symbol": "ETHUSDT", "instrument_type": "perpetual", "data_type": "trades"},
    ],
    "tradfi": [
        {"venue": "CME", "symbol": "ES1!", "instrument_type": "future", "data_type": "ohlcv_1m"},
    ],
    "defi": [
        {"venue": "UNISWAP_V3", "symbol": "WETH-USDC-500", "instrument_type": "lp_pool", "data_type": "oracle_prices"},
    ],
}
```
This drives the watchlist AND tells the candles route which data_type to use per symbol.
User to confirm exact symbols once GCS manifest is checked.

## Open questions / decisions needed

| # | Question | Status |
|---|----------|--------|
| 1 | Sports + Predictions — deferred, not in scope | RESOLVED: skip for now |
| 2 | QUANT vs PREDICTIONS naming — deferred | RESOLVED: not in scope for this plan |
| 3 | Exact symbols to include in CURATED_SYMBOLS per asset group | RESOLVED: 16 symbols hardcoded — user accepted |
| 4 | DEFI: oracle_prices vs dex_swaps for candles? | RESOLVED: oracle_prices |
| 5 | WebSocket / live tick layer | DEFERRED: batch only this round |
| 6 | GCS data access | RESOLVED 2026-04-26: ADC switched to harshkantariya@odum-research.com — read works |

---

## ⚠️ Operational guardrail (mandatory)

**GCS access is READ-ONLY.** No writes, no deletes, no metadata mutations against any
`market-data-tick-*` or `instruments-store-*` bucket. Use `download_bytes` and
`list_blobs` only.

---

## Phase plan (revised 2026-04-26)

P0–P4 already shipped (commit `live-defi-rollout` branch). Remaining work:

| Phase | Track | Work | Prerequisite | Status |
|-------|-------|------|-------------|--------|
| P0 | Both | Fix `/instruments/registry` `category` → `asset_group` | — | DONE |
| P1 | A | API: instruments GCS read + 1h cache | — | PENDING (P-A) |
| P2 | B | API: candles route — mode/as_of/from/to + GCS read | — | DONE |
| P3 | A | UI: real instrument list in watchlist | P1 | PENDING (P-A) |
| P4 | B | UI: real candles in chart, staleTime cache bump | P2 | DONE |
| **P5** | **B** | **UI: scroll-back pagination — `subscribeVisibleLogicalRangeChange`, page accumulator, prepend-on-scroll-left** | P4 | **NEW: this round** |
| **P6** | **B** | **UI: preserve visible range across timeframe switch** | P5 | NEW: this round |
| **P7** | **A** | **API: instruments-store reader (read instruments parquet for one day, one venue) + 1h cache** | — | NEW: this round |
| **P8** | **A** | **UI: useInstruments → real `/instruments/list?venue=…&asset_group=…&as_of=…` call; watchlist driven by API** | P7 | NEW: this round |
| **P9** | **B** | **Verify indicators (SMA/EMA/BB) render correctly with real candle data** | P5 | NEW: this round |
| **P10** | **B** | **Verify timeframe switching (1m/5m/15m/1H/4H/1D) works with real data** | P5 | NEW: this round |
| **P11** | **Both** | **Tests — backend pytest (batch_candles, routes), frontend vitest (useCandles, page-data hook), Playwright smoke (chart loads, scroll-back fires, timeframe switch)** | P5–P10 | NEW: this round |
| **P12** | **Both** | **Self-audit + commit at checkpoints** | P11 | NEW: this round |

### P5 implementation detail — scroll-back pagination

```
1. CandlestickChart receives onLoadMoreLeft(targetOldestTime: number) callback
2. After setData(), subscribe to chart.timeScale().subscribeVisibleLogicalRangeChange(range)
3. When range.from < 10 (close to left edge of loaded data), debounced fire onLoadMoreLeft(oldestLoadedTime)
4. Parent (use-terminal-page-data.ts) maintains `loadedPages` ref keyed by `${venue}:${symbol}:${tf}`:
   - Each page is { fromDate: string, toDate: string, candles: Candle[] }
   - On scroll-back: add a new page with from = oldestLoaded - 1 day, to = oldestLoaded
5. After fetchOlder resolves: prepend new candles to in-memory series, call setData(merged) — LWC preserves user's scroll position
6. Don't issue duplicate fetches — track inflight pages
7. Stop fetching once 21 days back (configurable), show "no more history" toast
```

### P7 implementation detail — instruments reader

```
GcsDomainService.list("instruments", filters={"venue": ..., "asset_group": ..., "as_of": ...})
  → bucket = build_bucket("instruments", project_id, category=asset_group.lower())
  → blob = "instrument_availability/by_date/day={as_of}/venue={venue}/instruments.parquet"
  → read with pq.read_table → to_pandas → to_dict('records')
  → cache key: f"{venue}:{asset_group}:{as_of}", TTL 1h
  → optional: include curated symbols' display metadata as fallback for missing fields
```

---

## Latency budget

| Operation | Target |
|-----------|--------|
| Instruments list (all CEFI, from cache) | < 50ms (cache hit) / < 1s (cache miss) |
| Instruments list (cache miss, GCS read) | < 2s |
| Candles 200 rows batch (GCS pyarrow) | < 1.5s |
| Candles scroll-back page (incremental) | < 1s |
| Full chart render after data arrives | < 200ms (LWC native) |
| E2E: instrument select → chart loaded | < 3s |

---

## Agent 1 GCS findings (2026-04-26)

### Buckets
- `market-data-tick-{asset_group}-{project_id}` (5 buckets)
- `instruments-store-{asset_group}-{project_id}` (5 buckets)
- Manifest: `_index/availability_index.parquet` in each bucket

### Path templates (CRITICAL — each group differs)

| Asset Group | Tick path template |
|-------------|-------------------|
| CEFI / TRADFI | `raw_tick_data/by_date/day={date}/category={cat}/venue={venue}/instrument_type={itype}/data_type={dt}/{SYMBOL}.parquet` |
| DEFI | same + `chain={chain}/` before `venue=` |
| SPORTS | same + `league={league}/` after `data_type=`, `category=sports` lowercase |
| PREDICTION | `raw_tick_data/by_date/day={date}/data_type=trades/venue=POLYMARKET/sub_category={crypto\|macro\|football}/{id}.parquet` |

Instruments path:
- CEFI/TRADFI/DEFI/PREDICTION: `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`
- SPORTS: `sports_reference/by_date/day={date}/entity=fixtures/fixtures.parquet` (fixtures = instrument catalogue)

### Coverage
| Group | Status | Key data types |
|-------|--------|---------------|
| CEFI | FULL | trades, book_snapshot_5, liquidations, derivative_ticker |
| TRADFI | FULL | trades, book_snapshot_10, tbbo, ohlcv_1m, ohlcv_15m |
| DEFI | FULL | dex_pools, dex_swaps, lending_indices, oracle_prices |
| SPORTS | ACTIVE | odds, fixtures, injuries, standings, xg, player_stats |
| PREDICTIONS | ACTIVE | trades, CLOB book_snapshot, order updates |

---

## Agent 2 backend findings (2026-04-26)

- `CanonicalParquetReader` — **FULLY IMPLEMENTED** at `market-tick-data-service/market_tick_data_service/reader.py`
- API `service.list()` — returns mock fixtures; `GcsDomainService` exists but uses generic blob lister, not CanonicalParquetReader
- `instruments-service` — separate repo, not integrated into API
- `GET /market-data/candles` — does NOT accept `mode` or `as_of` params (other routes like positions/execution do)
- Minimal changes: add params to routes + add CanonicalParquetReader to GcsDomainService "candles" collection

---

## Agent 3 UI findings (2026-04-26)

- `CandlestickChart` — fully implemented, handles live tick updates, no scroll-back
- `WatchlistPanel` — clean presentational component, receives props
- `use-terminal-page-data.ts` — already passes `mode` + `asOf` to `useCandles`; falls back to mock `generateCandleData()` when API returns nothing
- WebSocket integration — wired, enabled only in `context.mode === "live"`
- No client-side candle cache, no scroll-back pagination
- `DEFAULT_INSTRUMENTS` (5 hardcoded) — used as fallback; no expiry/status fields
