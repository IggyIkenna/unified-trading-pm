---
title: Market Data Delivery — How Mature Platforms Solve It
id: market_data_delivery_architecture_2026_04_27
status: reference
created: 2026-04-27
audience: architects, backend engineers, frontend engineers
---

# Market Data Delivery — Reference Architecture

How TradingView, Binance, Coinbase, Bloomberg, and Zerodha actually solve the "millions of instruments × real-time ticks
× multiple timeframes × historical back-scroll" problem, and where our current implementation diverges.

The goal isn't to copy any one of them — it's to extract the _invariant patterns_ that every mature platform converges
on, regardless of stack.

---

## 1. The problem, stated precisely

We are not delivering "data". We are delivering a **continuously-updated time series**, sliced by:

- **Symbol space** — 10⁶ instruments (CEFI + TRADFI + DEFI + options chains)
- **Resolution space** — at minimum {1s, 1m, 5m, 15m, 1H, 4H, 1D, 1W, 1M}
- **Time space** — from "right now, this millisecond" back to "decades of history"
- **Concurrency** — N user sessions × M panels per session × K subscriptions per panel

Each cell of the (symbol × resolution × time-range) cube has a different freshness, size, and access pattern. **Treating
them all the same is the mistake** that makes every naive implementation slow.

The constraint that defines the architecture: **a single chart pulls roughly 500–2000 bars at any moment**, ever. A user
looking at BTCUSDT 5m sees the last ~2 days. They never see "all 5m bars since 2017" — that's 600,000+ bars which would
render as a vertical line of pixels. So **the unit of delivery is a bounded window of bars, not a day, not a file, not a
date.**

---

## 2. The five invariants every mature platform follows

### Invariant 1 — Resolutions are pre-aggregated server-side, always

The client **never resamples**. The server maintains every supported resolution as its own materialised time series. A
5m bar is not a calculation the client runs over 5 trades; it is a row that exists in storage with columns
`(t, o, h, l, c, v)` already populated.

Why: a 1-minute window of BTCUSDT trades on Binance is ~30,000 trades. If the client downloads and aggregates them,
you've moved 5 MB to render 1 bar. Pre-aggregated, that 1 bar is 50 bytes.

How: a streaming aggregator reads the trade tape, maintains a rolling bucket per (symbol, resolution), and on bucket
close commits an immutable bar to storage. Same code runs once per resolution; output goes to a different storage shard.

This is the single biggest architectural decision. It compounds: every client request is 100×–10000× smaller, every
cache is 100×–10000× more effective, every latency budget is 100×–10000× more forgiving.

### Invariant 2 — Time, not date, is the addressing primitive

The API takes `(from_ts, to_ts)` in milliseconds (or `(end_ts, count)`), **never** `as_of=YYYY-MM-DD`. Reasons:

- A 4H bar can straddle midnight. A "day" is a UI concept.
- Markets close on holidays. Asking for "yesterday's 1m bars" returns nothing for TradFi on a Sunday; the client
  shouldn't have to know that.
- Pagination is symmetric: scroll left → `from -= window`; scroll right → `to += window`. Both are the same operation.
- Crossing month/year boundaries is automatic.

The server returns whatever bars exist in the requested time interval — nothing more, nothing less.

### Invariant 3 — Live updates flow through a separate, narrow channel

REST returns _historical_. WebSocket emits _deltas_. They are different contracts, never conflated. The WebSocket
message schema is:

```
{ type: "bar", symbol, resolution, bar: {t, o, h, l, c, v}, kind: "update" | "close" }
```

`kind: "update"` → the bar with timestamp `t` already exists in the client's local store; replace it (same-bar tick).

`kind: "close"` → the previous bar is final; this is the next bar's birth (append).

The client does not know or care that there are millions of trades behind each delta. It receives, on average, **one
message per resolution per bar boundary**, plus same-bar updates while the bar is still open.

For a chart on 1m, that's at most ~60 updates per minute (the open bar ticks roughly once per second, then closes), plus
one new bar per minute. ~120 messages/min steady state — trivial bandwidth, trivial CPU.

### Invariant 4 — The client owns a local, indexed bar store

Not React Query. Not LWC's internal cache. A first-class data structure, keyed by `(symbol, resolution)`, holding a
sorted dense array of bars covering some `[from_ts, to_ts]` window — possibly with gaps (holidays).

Operations:

- `getRange(symbol, resolution, from, to)` — returns whatever it has, triggers a fetch for whatever it doesn't, applies
  the result on resolve
- `applyDelta(symbol, resolution, bar, kind)` — `kind=update` overwrites the last bar; `kind=close` appends a new one
- `evict(maxBytes)` — LRU eviction of (symbol, resolution) cells the user hasn't viewed lately

The chart is a _view_ of this store. Switching timeframe doesn't refetch — it pivots the view to a different
`(symbol, resolution)` cell, which may already be populated. Switching symbol is the same. The store is the single
source of truth on the client.

### Invariant 5 — Storage is tiered by age, with retention compaction

Hot tier (last ~24h): in-memory or Redis, p50 ≤ 1 ms, p99 ≤ 10 ms Warm tier (last ~30 d): SSD/Parquet, p50 ≤ 50 ms Cold
tier (everything else): object storage / Parquet, p50 ≤ 500 ms

Retention by resolution:

| Resolution | Hot    | Warm   | Cold (forever)            |
| ---------- | ------ | ------ | ------------------------- |
| 1s / tick  | 1 d    | 7 d    | (rolled into 1m)          |
| 1m         | 24 h   | 30 d   | 90 d, then rolled into 5m |
| 5m         | 24 h   | 90 d   | 1 year, rolled into 1H    |
| 1H         | 7 d    | 1 y    | forever                   |
| 1D / 1W    | always | always | forever                   |

Older 1m data is _deleted_ once a coarser representation exists. Storage costs collapse without losing user-visible
information — nobody zooms to 1m on 5-year-old data.

The API picks the resolution. Asking for "1m from 2018" returns 1H bars with a `served_resolution: "1H"` field; the
chart adapts.

---

## 3. The data contracts (concrete schemas)

### REST — historical bars

```
GET /v2/candles
  ?symbol=BINANCE-FUTURES:BTCUSDT
  &resolution=5m
  &from=1776051200       # ms unix
  &to=1776137600
  &limit=2000            # optional cap, default 5000

200 OK
{
  "symbol": "BINANCE-FUTURES:BTCUSDT",
  "resolution": "5m",
  "served_resolution": "5m",   # may differ from requested for old data
  "bars": [
    { "t": 1776051300000, "o": 74632.3, "h": 74693.8, "l": 74571.9, "c": 74579.9, "v": 347.578 },
    ...
  ],
  "next_before_ts": 1776051000000,   # paginate left from here
  "next_after_ts":  1776137700000    # paginate right from here
}
```

Cacheable by edge with `Cache-Control: public, max-age=86400, immutable` when `to < now - 1h` (closed history is
forever-immutable). Recent windows get short or no-cache.

### WebSocket — live deltas

Connect: `wss://api/v2/stream` Subscribe:
`{ "op": "sub", "channels": ["BINANCE-FUTURES:BTCUSDT@5m", "BINANCE-FUTURES:ETHUSDT@1m"] }`

Server emits:

```
{ "type": "bar", "ch": "BINANCE-FUTURES:BTCUSDT@5m",
  "bar": { "t": 1776140100000, "o": ..., "h": ..., "l": ..., "c": ..., "v": ... },
  "kind": "update" }
```

`kind: "snapshot"` on first subscribe = the current open bar. `kind: "update"` while bar is open. `kind: "close"` when
bar finalises and the next one opens.

Reconnect protocol: client sends `{ "op": "resume", "since_ts": LAST_SEEN_TS }`, server replays missed `close` messages
from cache, then resumes live.

### Symbol metadata

```
GET /v2/symbols/{symbol}
{
  "symbol": "BINANCE-FUTURES:BTCUSDT",
  "venue": "BINANCE-FUTURES",
  "instrument_type": "perpetual",
  "tick_size": 0.01,
  "min_size": 0.001,
  "session": { "tz": "UTC", "open": null, "close": null },   # 24/7
  "available_from": 1573948800000,
  "resolutions": ["1m", "5m", "15m", "1H", "4H", "1D"],
  "currently_traded": true
}
```

This is what powers the symbol picker, watchlist row metadata, and "go to date" boundary checks.

---

## 4. Client-side architecture

```
+-----------------------------+
|         Chart UI            |   reads bars to render
|   (Lightweight Charts)      |   subscribes to view-range changes
+--------------+--------------+
               |
               v
+-----------------------------+
|       BarStore (singleton)  |   single source of truth
|                             |
|   bars: Map<(sym,res),     |   sorted dense array
|           Page>             |
|                             |
|   getRange(sym,res,from,to) |   coalesces fetches
|   applyDelta(sym,res,bar)   |   from WS
|   evict(maxBytes)           |   LRU
+----+---------+----------+---+
     |         |          |
     v         v          v
+--------+ +--------+ +--------+
| REST   | | WS     | | LocalStorage|
| client | | client | | (warm cache)|
+--------+ +--------+ +-------------+
```

### BarStore mechanics

- A **page** is `{from, to, bars: Bar[]}`. A `(symbol, resolution)` cell may hold multiple disjoint pages from previous
  fetches.
- `getRange` walks the existing pages, identifies missing sub-ranges, issues parallel fetches for each, merges on
  resolve. Concurrent calls for overlapping ranges share a single in-flight promise.
- `applyDelta` finds the appropriate page (the one whose `[from, to]` contains the bar's `t`) and either replaces the
  last bar (`update`) or extends the page right (`close`).
- Eviction runs on a soft schedule — e.g. when total bytes > 50 MB, drop pages from `(sym, res)` cells the user hasn't
  queried in 5 min.

### Chart integration

Lightweight Charts (or any chart) subscribes to **two events**:

1. _visible time range changed_ — when the left edge approaches the start of loaded data, ask the BarStore for an
   earlier page; same for right edge.
2. _time scale wheel/drag_ — same logic, debounced.

The chart never _triggers_ fetches directly — it tells the store what time range it now needs to see. The store decides
whether that needs a network call.

For a "Go to date" jump:

- User picks 2020-03-12.
- UI calls `barStore.getRange(sym, res, picked - 250 bars, picked + 100 bars)`.
- Store sees no overlap with existing pages, fetches the window, returns.
- Chart calls `setVisibleRange({ from: picked - 100 bars, to: picked + 50 bars })`.

---

## 5. Server-side architecture (the aggregator)

```
                    +------------------+
   trades stream -->| Per-symbol       |
   (Kafka/Redpanda) | bucket actor     |--> emit close → resolution shard
                    |  (1m, 5m, 15m,   |--> emit close → resolution shard
                    |   1H, 4H, 1D)    |--> emit close → resolution shard
                    +--------+---------+
                             |
                             | open-bar updates
                             v
                    +------------------+
                    | Pub-sub fanout   |
                    | (Redis Streams / |
                    |  NATS)           |
                    +--------+---------+
                             |
              +--------------+--------------+
              v                             v
     +----------------+            +----------------+
     | WS gateway     |            | REST gateway   |
     | (per-channel   |            | (range query → |
     |  fan-out)      |            |  storage tier) |
     +----------------+            +----------------+
```

Key properties:

- **One bucket actor per (symbol, resolution)**. They are independent — no global lock, horizontal sharding by symbol
  hash.
- **Bars are committed on close**, never updated. History is immutable; this is what enables aggressive edge caching.
- **The same actor that produces a bar emits its open-bar updates to pub-sub**. There is no second source of truth.
- **Resolution rollup happens on bar close**, not on a separate batch job: when a 1m closes at minute :05, if it's the
  5th of the 5m bucket, the 5m bar closes too. (1H from 5m, 1D from 1H, etc. — never 1D from 1m.)

For 10⁶ symbols × 9 resolutions, that's 9M actors. Each actor is ~1 KB state. 9 GB total — a single mid-size box,
sharded across 8–32 nodes in production for HA.

### Storage layout (cold tier, parquet)

Old approach (what we have):

```
raw_tick_data/by_date/day=2026-04-14/category=cefi/venue=BINANCE-FUTURES
  /instrument_type=perpetual/data_type=trades/BTCUSDT.parquet  (25 MB)
```

Mature approach:

```
ohlcv/symbol=BINANCE-FUTURES_BTCUSDT/resolution=5m/year=2026/month=04
  /bars.parquet  (~84 KB for the month)
```

Read pattern: a "give me 5m bars from 2026-03-01 to 2026-04-30" request opens 2 files instead of 60, transfers 168 KB
instead of 1.5 GB, and needs zero CPU on the server (parquet projection + range scan).

---

## 6. Operational concerns

### Latency budget

| Operation                      | p50    | p99    |
| ------------------------------ | ------ | ------ |
| Fetch 500 bars from hot        | 5 ms   | 25 ms  |
| Fetch 500 bars from warm       | 30 ms  | 120 ms |
| Fetch 2000 bars from cold      | 200 ms | 800 ms |
| WS subscribe → first snapshot  | 10 ms  | 50 ms  |
| Live tick → chart pixel update | 30 ms  | 150 ms |

The 2000-bars-from-cold p99 sets the worst-case "Go to date" UX: under 1 second, perceived as instant. Anything > 2s
feels broken.

### Caching layers

1. **Browser cache** — `Cache-Control: immutable` on closed history.
2. **CDN edge** — same headers, hours of TTL. Hit rate on closed history > 99% in practice.
3. **API gateway in-memory** — last 7 days of every (symbol, res) hot.
4. **Warm parquet** — SSD-backed, read by API.
5. **Cold parquet** — object storage.
6. **Source of truth** — the bucket-actor process holds the open bar.

A `/candles?symbol=BTCUSDT&resolution=5m&to=2020-01-01&from=2019-12-31` request for closed history typically never
reaches the API server — the CDN serves it.

### Cost shape

For 1M symbols × 9 resolutions × continuous bars:

- Storage (cold parquet, all history): ~5 TB. Pennies on object storage.
- Hot (Redis, last 24h all res): ~50 GB. One large box.
- Aggregator compute: ~16 cores per million symbols at average rates.
- Bandwidth: dominated by initial chart loads (~2 KB each), trivial.

Compare to per-trade delivery: 25 MB × millions of requests/day = TB of egress per day. Pre-aggregation is the entire
economic argument.

---

## 7. Where our current architecture diverges

| Concern              | Mature platform                        | Our current state                                 |
| -------------------- | -------------------------------------- | ------------------------------------------------- |
| Aggregation          | Server-side, on bar close, immutable   | Per-request, pandas resample over 25 MB of trades |
| Addressing           | `(from_ts, to_ts)`                     | `as_of=YYYY-MM-DD` (one day)                      |
| Storage layout       | `symbol/resolution/year-month`         | `day/venue/instrument_type/symbol` (raw trades)   |
| Live channel         | WebSocket bar deltas                   | Not wired (WS exists but not for bars)            |
| Client store         | Indexed `BarStore` with paging         | React Query keyed by params, no merge logic       |
| Pagination           | Symmetric left+right, time-based       | Left-only, day-by-day stepping                    |
| Resolution awareness | Server picks based on time span        | Client always asks for the same                   |
| Empty days           | Server returns `[]`, client paints gap | Client sees `[]`, thinks "no data"                |
| Fallback             | None — empty is empty                  | Mock-generated candles polluting real charts      |
| Fetch latency p99    | < 1s for any request                   | 5–7s for 25 MB raw-trades download                |
| Live tick path       | Pre-aggregated bar deltas              | None                                              |
| Cache hit rate       | > 99% on closed history                | 0% (every request is a fresh GCS read)            |

The single largest gap is **server-side OHLCV pre-aggregation**. Every other gap is downstream of it.

---

## 8. Phased migration path

A realistic path from where we are to where we should be, in order of leverage.

### Phase 0 — kill the mock fallback (done)

In real-API mode, return `[]` when GCS has no data; don't paint synthetic candles over real charts. ✓

### Phase 1 — pre-aggregate to OHLCV parquet

Run a one-time + daily job that reads the raw-trade parquets and emits:

```
ohlcv/symbol={SYM}/resolution={1m,5m,15m,1H,4H,1D}/year={YYYY}/month={MM}
  /bars.parquet
```

Per symbol per month per resolution. Typical size: 1m × 1 month ≈ 250 KB, 5m ≈ 50 KB, 1H ≈ 5 KB.

The API's `BatchCandleReader` switches from "read raw trades and resample" to "open the right OHLCV parquet and project
the time range." Latency drops from 5–7 s to < 200 ms.

### Phase 2 — switch the API to time-range addressing

Replace `as_of=YYYY-MM-DD` with `from=ms&to=ms&limit=N&resolution=R`. Mock service synthesises bars on the fly; real
service projects the parquet. Backwards compat: if the UI sends `as_of`, translate to `(start_of_day, end_of_day)`
server-side.

### Phase 3 — client-side BarStore

Replace the per-React-Query-keyed cache with a singleton store keyed by `(symbol, resolution)`. Implement `getRange`
with overlap detection and parallel page fetches. Chart subscribes to its visible-range and asks the store, rather than
triggering its own fetches.

This is the change that makes "Go to date" feel instant and pan-left seamless.

### Phase 4 — live bar deltas via WebSocket

Aggregator publishes open-bar updates to Redis Streams (or whatever pub-sub is already in the stack). WS gateway
subscribes per-channel and fans out. Client merges deltas into BarStore.

The chart shows the same data whether it was just fetched via REST or just received via WS. No special-casing.

### Phase 5 — resolution rollup + retention

Once OHLCV is the source of truth, drop old 1m data after 90 days (rolled into 5m which sticks for a year, etc.).
Storage cost stops growing; user UX is unaffected because nobody zooms to 1m on old data.

### Phase 6 — edge caching of immutable history

Move closed-history responses behind a CDN with `immutable` cache headers. After warm-up, > 99% of historical requests
never touch the API.

---

## 9. The five things to internalise

1. **Pre-aggregate on the server, never on the client.** This is the one decision that everything else hinges on.
2. **Time, not date, is the addressing primitive.** Days are a UI thing.
3. **REST for historical, WS for deltas — keep them separate.**
4. **The client owns a `BarStore`. The chart is its view.**
5. **Storage tiers by age; resolutions roll up; old fine-grained data is allowed to disappear.**

Everything mature platforms do — the smooth pan, the instant date jump, the tick-by-tick live update on a chart 5 years
deep — falls out of these five choices, in this order.
