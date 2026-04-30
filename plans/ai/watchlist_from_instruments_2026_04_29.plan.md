---
title: Watchlist — Populate from instruments-service GCS catalogue
id: watchlist_from_instruments_2026_04_29
status: ready
created: 2026-04-29
last_updated: 2026-04-30
audience: backend engineers, frontend engineers
parent_reference: market_data_delivery_architecture_2026_04_27.md
sibling_plan: price_chart_gcs_delivery_2026_04_29.plan.md
codex_refs:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/per-category-bucket-layouts.md
  - codex/02-data/subscription-model.md
  - codex/02-data/data-status-drilldown.md
prior_audit: plans/ai/audit_instruments_gcs_2026_04_25.md
working_branch: feat/price-chart-gcs-delivery
---

## Status update — 2026-04-30

The chart plan (`price_chart_gcs_delivery_2026_04_29.plan.md`) has
shipped on branch `feat/price-chart-gcs-delivery` across
`unified-trading-api`, `unified-trading-system-ui`,
`unified-api-contracts`, `market-data-processing-service`. The chart
now reads real GCS candles end-to-end. Plan status:
`implemented`.

**Patterns established by the chart implementation that this plan
adopts**:

- **Reader stays in-API, not delegated to UTL domain client.**
  The chart implementation kept `BatchCandleReader` in
  `unified-trading-api/services/batch_candles.py` and added
  manifest-prune logic to it, instead of routing through
  `MarketCandleDataDomainClient`. Pragmatic — the codex domain-
  client refactor was scope-creep on top of "make the chart work."
  We mirror that decision: keep `InstrumentsReader` in-API, add
  manifest pruning, defer the domain-client refactor.
- **Manifest backfill is a per-service script.** MDPS landed
  `scripts/rebuild_processed_candles_manifest.py` that emits
  per-symbol manifest rows (`date, venue, data_type, timeframe,
  instrument_id`). instruments-service already publishes correct
  `(date, venue)` rows, so we don't need an analogous backfill
  script — but if we discover gaps in Unit C, we know the playbook.
- **`*_BUCKET_VARIANT=prod|test` env toggle.** Chart shipped
  `MARKET_DATA_BUCKET_VARIANT`; we ship `INSTRUMENTS_BUCKET_VARIANT`
  in the same shape.
- **Connection-pool tuning bonus.** The chart commit bumped
  urllib3 pool_maxsize 10→32 on the storage client to match the
  16-worker `ThreadPoolExecutor`. Apply the same to the
  instruments-store client — same parallelism shape.
- **Benchmark exists, output doc missing.** Chart shipped
  `scripts/bench_candle_reads.py` but the
  `plans/ai/reports/price_chart_gcs_benchmark_2026_04_29.md`
  referenced in the chart plan's frontmatter doesn't exist on disk
  yet. We follow the same benchmark pattern; we **also** write the
  report file so the convention sticks.

**What's already done that this plan can drop**:

- ✗ `MDPS underfilling manifest, per-symbol pruning blocked` —
  resolved by chart branch's MDPS backfill script (per-symbol
  granularity).
- ✗ Bench-script tooling boilerplate — copy structure from
  `unified-trading-api/scripts/bench_candle_reads.py`.

**What's NOT done that this plan still owns**:

- All instruments-side work. `InstrumentsReader` exists from a
  pre-branch commit (`292f4d8`) but bypasses the manifest. Route
  uses it directly. UTL domain-client refactor still untouched.
  Frontend silent fallback to `DEFAULT_INSTRUMENTS` still in place.
- `INSTRUMENTS_BUCKET_VARIANT` env not wired.

---

# Watchlist — Populate from instruments-service GCS

Operational plan to make the Terminal watchlist read its instrument
list from the `instruments-store-{cat}-{project}` GCS buckets via UTL
`InstrumentsDomainClient`, with manifest-driven venue pruning. Mirrors
the price-chart plan (`price_chart_gcs_delivery_2026_04_29.plan.md`) —
same architecture, different payload, different bucket family.

This runs **in parallel** with the chart plan. The two are
independent: charts read `processed_candles/`, watchlist reads
`instrument_availability/`. Different reader, same domain-client
pattern, same manifest-prune pattern, same lifecycle.

---

## Scope

**In:**

- Backend `/instruments/list` (and friends) reads via UTL
  `InstrumentsDomainClient` (codex SSOT for instruments reads —
  `subscription-model.md` §"InstrumentsDomainClient").
- Manifest pruning: `read_availability_index(bucket)` filters
  which `(date, venue)` shards have been written by
  instruments-service before fetching.
- Watchlist consumes the live API list, not `DEFAULT_INSTRUMENTS`.
- Bucket-variant toggle (prod vs test) — `INSTRUMENTS_BUCKET_VARIANT`
  config parallels `MARKET_DATA_BUCKET_VARIANT`.
- CEFI + TRADFI scope. DEFI / SPORTS / PREDICTION deferred (different
  path layouts; SPORTS especially diverges per codex).

**Out:**

- Live instrument metadata refresh (price, 24h change). Today's
  watchlist mixes `instruments-service` reference data with
  `tickers` price snapshot — keep that pattern, just change the
  reference-data source. Real-time ticker streaming stays out per
  the chart plan.
- Per-instrument trading-hours UI (open/close, holiday calendar).
  Schema carries it; rendering it is a separate UX plan.
- Replacing `lib/registry/instruments.ts` static snapshot. The
  31,961-row JSON snapshot is used by the *instruments page*, not
  the watchlist. Out of scope here.
- DEFI / SPORTS / PREDICTION watchlists. Path layouts differ
  (`per-category-bucket-layouts.md` §"instruments-service writes")
  and SPORTS uses an entirely different tree (`sports_reference/`
  with `entity=` partition key, no `venue=`). Each gets its own
  follow-up.
- Per-symbol pruning of the manifest. Instruments-service writes
  `(date, venue)` shards — that's the natural pruning grain. No
  per-instrument-key pruning is meaningful here.

---

## Architectural decisions

These mirror the chart plan §"Architectural decisions". Same
reasoning, abbreviated; see chart plan for citations.

### 1. Read path = keep `InstrumentsReader` in-API, add manifest prune

**Original plan said**: delete `InstrumentsReader`, route through UTL
`InstrumentsDomainClient`.

**Revised after chart-plan precedent**: keep `InstrumentsReader` in
`unified-trading-api/services/instruments_reader.py`, add
manifest-prune helper to it, mirror the chart's `BatchCandleReader`
shape. The domain-client refactor stays a separate plan.

Why the change: the chart plan landed by adding manifest pruning
to the existing in-API reader instead of replacing it with the UTL
client. Same decision pays here — less code churn, same swap-point
later when the domain-client refactor becomes its own plan, faster
path to a working watchlist.

Codex SSOT for the long-term shape is still
`subscription-model.md` §"InstrumentsDomainClient" — when the
domain-client refactor lands, it touches both readers in one shot.
For now: read directly, prune via manifest.

### 2. Manifest first, GCS second

`gs://instruments-store-{cat}-{project}/_index/availability_index.parquet`
exists today (verified 2026-04-29 — has rows for both CEFI and
TRADFI). Use it to:

- Resolve the most recent `as_of` date that has shards for the
  requested venue, instead of guessing yesterday and 404'ing on
  weekends.
- Filter the venue list per category to only those that
  instruments-service has actually published for the target date.

### 3. Manifest regeneration + caching — same as chart plan

`manifest-consolidator` Cloud Run Job runs `*/1 * * * *` per
**every** category bucket — including `instruments-store-*`. UTL's
60s in-process cache applies identically. **No new infra, no new
cache layer, no overrides.** See chart plan §3 for the full
lifecycle table.

### 4. Mock vs real on `CLOUD_MOCK_MODE`

Same convention. Mock = `service.list("instruments")` from
`MockStateStore`. Real = UTL client + manifest prune.

### 5. Bucket variant from config

`INSTRUMENTS_BUCKET_VARIANT=prod|test` (default `prod`). Hive
layout is identical across variants per codex.

### 6. `project_id` from `UnifiedCloudConfig`

Same resolution chain: UTL `UnifiedCloudConfig.project_id`
(Secret-Manager-backed) → `GCP_PROJECT_ID` env fallback → 503 if
both fail.

### 8. Search and instrument navigation — **open problem, deferred to Unit G**

**This plan does NOT solve search.** The current `WatchlistPanel.tsx`
has a plain `Array.filter(s.symbol.includes(query))` over the active
list — fine for the 9 hardcoded `DEFAULT_INSTRUMENTS` it sees today,
useless for the ~10K instruments instruments-service publishes per
day. The right shape is sketched here so the plan doesn't pretend
it's solved; **implementation lives in a follow-up plan
(`instrument_search_2026_05_XX.plan.md` — to be written)**.

**Real volume** (verified 2026-04-29 listing GCS):

| Bucket | Total/day | Dominant shape |
|---|---:|---|
| CEFI | ~6,170 | DERIBIT alone: 3,002 OPTION + 561 COMBO + 74 FUTURE + 16 PERPETUAL + 8 SPOT |
| TRADFI | ~600 | NASDAQ + NYSE equities (~600), CME futures (~150), ICE/CBOE/FX trivial |
| DEFI | ~2K | Uniswap V3/V4 pools dominant |
| **Total in scope** | **~8.7K** | (sports/prediction excluded per scope) |

The "150K" number people quote is the **pre-filter** universe.
UAC's three universe whitelists
(`cefi_instrument_universe.py`, `tradfi_instrument_universe.py`,
`defi_major_assets.py`) cut it ~15× at ingestion time. We're
searching ~10K, not 150K. Still too big for a flat list.

**Catalogue refresh cadence**: daily, per
`instruments-service/docs/instrument-catalogue.md` —
`--operation refresh-catalogue` writes one parquet per
`(category, venue, day)`. Not 15min. The 1h-TTL
`InstrumentsReader._cache` is the right window for the API; we
don't need to refresh more aggressively than the source.

**Three-layer proposal** (committed to in Unit G's planning, not
this plan):

1. **Server-side `/instruments/search` endpoint.** Build an
   in-memory index per (asset_group, day) — keys: `symbol`,
   `base_asset`, `quote_asset`, `raw_symbol`, `instrument_key`.
   At ~10K rows × 5 fields × ~12 bytes ≈ 600 KB total. Trivial.
   Filter by `q`, `asset_groups[]`, `types[]`, `venue`, return
   ranked top N. Doesn't need Postgres FTS / Elasticsearch /
   Algolia at this size.
2. **Type-aware drilldown for high-cardinality types.** Options
   and dated futures don't fit a flat list. Pattern: pick
   underlying → server returns chain (expiries × strikes × C/P)
   → user clicks cells to add. Backend already has
   `/api/derivatives/options-chain` and `/vol-surface` (mock
   today); point them at instruments-service parquet. Same
   data, different projection.
3. **Prebuilt watchlists (presets) shipped as UAC SSOT.** JSON
   under `unified_api_contracts/registry/preset_watchlists/`:
   `nasdaq_100.json`, `sp_500.json`, `top_20_crypto.json`,
   `defi_blue_chips.json`, `tradfi_major_futures.json`. Most
   already exist as universe whitelists in UAC — wrap them as
   user-facing watchlist definitions. Backend serves via
   `GET /instruments/presets`; UI joins each preset's
   `instrument_key` list against today's
   `instrument_availability/` to fill in name/venue/price.
   Updates: rare. NASDAQ-100 changes ~1×/quarter — maintain
   manually in UAC.

**Per-category UX summary** (Unit G implements):

| Category × type | UX shape |
|---|---|
| CEFI spot/perp (~120) | Flat virtualized list, default sort = market cap |
| CEFI options (~3,002 Deribit) | Chain picker — never flat list |
| CEFI dated futures (~74) | Flat list, default sort = expiry |
| TRADFI equities (~600) | Flat virtualized list, sortable by venue |
| TRADFI futures (~50 roots × few expiries) | Flat list grouped by root |
| TRADFI options | Disabled today (5,990/day per docs); chain picker when enabled |
| DEFI pools / lending (~2K) | Flat virtualized list filtered by `instrument_type` |
| SPORTS / PREDICTION | Out of scope (project-wide) |

**For this plan (Units A–F)**: watchlist tabs (CeFi/TradFi/DeFi)
populate with their full instrument lists. The existing
client-side `includes(query)` filter handles within-tab search
acceptably for ~600 TradFi or ~120 CEFI-non-option entries.
**Deribit options are explicitly NOT shown in the watchlist for
this plan** — they need the chain picker (Unit G), not a flat
list. The watchlist's instrument-type filter excludes
`instrument_type IN ('OPTION', 'COMBO')` until Unit G ships.

### 7. Frontend changes are minimal

`use-terminal-page-data.ts:176-239` already maps the API response
into watchlist rows. The mock-mode short-circuit at line 177
(`if (isMockDataMode()) return DEFAULT_INSTRUMENTS...`) stays — same
tiering convention as the chart plan. Real-API mode already calls
`useInstruments()`; we just need the backend to serve real GCS data
when called.

---

## Findings — current state (verified 2026-04-29)

### GCS layout

```
gs://instruments-store-{cefi|tradfi|defi|prediction}-{project_id}/
  _catalogue/                           ← service self-publish (separate concern)
  _index/
    availability_index.parquet          ← consolidated manifest
    per_vm/                             ← per-writer-VM shards (if enabled)
  instrument_availability/
    by_date/day=YYYY-MM-DD/
      venue=<VENUE>/
        instruments.parquet             ← the file we read
```

Verified bucket listings 2026-04-29:

- CEFI bucket: `instrument_availability/by_date/day=2026-04-14/`
  has `venue={ASTER, BINANCE-FUTURES, BINANCE-SPOT, BYBIT,
  COINBASE-SPOT, DERIBIT, HYPERLIQUID, OKX-FUTURES, OKX-SPOT,
  OKX-SWAP, ...}/`
- TRADFI bucket: same date has `venue={CBOE, CME, FX, ICE, NASDAQ,
  NYSE}/`
- Each `instruments.parquet` is 17 KB – 247 KB. Whole TRADFI day is
  ~377 KB across 6 venues.

**SPORTS quirk** (out of scope but flagged): writes
`sports_reference/by_date/day={date}/entity={entity}/` instead of
`instrument_availability/`. Reader must dispatch on category if/when
SPORTS is added. Codex `per-category-bucket-layouts.md` is SSOT.

**PREDICTION quirk:** no `venue=` partition (POLYMARKET-only).
Reader must dispatch on category here too. Out of scope for now.

### Schema (verified on TRADFI NASDAQ 2026-04-14)

Columns:

```
instrument_key, venue, instrument_type, raw_symbol, base_asset,
quote_asset, status, available_from_datetime,
available_to_datetime, asset_class, settle_asset, tick_size,
min_size, contract_size, expiry, strike, option_type, underlying,
margin_type, legs, is_trading_day, regular_open_utc,
regular_close_utc, early_close_utc, pre_market_open_utc,
post_market_close_utc, auction_open_utc, auction_close_utc,
holiday_calendar, timezone
```

29 columns. Sample:

```
instrument_key:          "NASDAQ:SPOT_PAIR:CTAS"
venue:                   "NASDAQ"
instrument_type:         "SPOT_PAIR"
raw_symbol:              "CTAS"
base_asset:              "CTAS"
quote_asset:             "USD"
status:                  "active"
asset_class:             "equity"        // one row in sample is "commodity" — schema allows mix
tick_size:               Decimal("0.01")
min_size:                Decimal("100")
available_from_datetime: "2015-01-01T00:00:00+00:00"
available_to_datetime:   None             // null = still active
is_trading_day:          True
regular_open_utc:        "2026-04-14T13:30:00+00:00"
regular_close_utc:       "2026-04-14T20:00:00+00:00"
holiday_calendar:        "NASDAQ"
timezone:                "America/New_York"
```

`tick_size` / `min_size` / `contract_size` / `strike` come back as
`Decimal`. Existing `InstrumentsReader._normalise_row` handles the
JSON-encoding (Decimal → float, Timestamp → ISO string, NaT/NaN →
None). UTL's domain client should produce JSON-serialisable rows
already; verify in Unit B.

### Backend — current state

`unified-trading-api/unified_trading_api/routes/instruments.py`:

- `GET /instruments/list?venue=&asset_group=&as_of=&page=&page_size=`
  — line 64. Real branch reads via `_get_instruments_reader(request)`
  → `InstrumentsReader.get_instruments(asset_group, venue, as_of)`.
  Mock branch reads from `MockStateStore`.
- `GET /instruments/catalogue` — line 94. Mock-only today
  (`service.list("instrument_catalogue")`). Real backend not wired.
- `GET /instruments/registry` — line 103. Mock-only.
- `GET /instruments/curated` — line 134. Returns the
  `CURATED_SYMBOLS` dict from `config/curated_symbols.py` directly.
  Independent of GCS. Stays as-is — used by the chart plan.

`unified-trading-api/unified_trading_api/services/instruments_reader.py`
exists, has 1h-TTL cache, calls
`build_bucket("instruments", project_id=…, category=…)` + builds
the blob path manually. **This is the file we delete in Unit A**,
replaced by UTL client calls.

### Frontend — current state

- `hooks/api/use-instruments.ts:50` — `useInstruments({venue,
  assetGroup, asOf})` calls `/api/instruments/list`.
- `components/widgets/terminal/use-terminal-page-data.ts:176` —
  consumes `useInstruments()` result, maps to watchlist rows. Falls
  back to `DEFAULT_INSTRUMENTS` if API returns empty.
- The empty-fallback to `DEFAULT_INSTRUMENTS` is **the bug** —
  today's API in real mode returns empty (because the reader either
  has no `project_id`, no GCS creds, or guesses an as-of with no
  shard) and the UI silently falls back to hardcoded values. We
  want the API to return real data, and the empty fallback to mean
  "really empty, show empty state".

### Existing instruments audit — `audit_instruments_gcs_2026_04_25.md`

The 2026-04-25 audit doc covers the same ground at the
*instruments-page* level (the standalone listing UI), not the
watchlist. It's still useful as background — schema notes,
category quirks, available endpoints. We cite it; we don't
duplicate it. This plan is watchlist-scoped.

---

## Goals

1. With backend on `:8030` (real mode) + UI on `:3000`, the
   Terminal watchlist tabs (CeFi / TradFi / DeFi / Other) populate
   from real GCS-backed instruments — for CEFI and TRADFI venues
   that have shards published for the most recent available date.
2. Switching watchlist tabs filters by category, not by `venue` —
   matches today's UI behavior.
3. Selecting an instrument from the watchlist still feeds
   `selectedInstrument` correctly into the chart's `useCandles`
   call. End-to-end: watchlist → chart works on real data for
   the same 6 MVP symbols the chart plan covers, plus their
   neighbours from the same venue parquets.
4. Manifest pruning so the route doesn't issue a GCS GET for a
   `(date, venue)` shard that doesn't exist. Worst-case behavior:
   missing shard → `[]` in the API response → empty watchlist row
   set, *not* a fallback to `DEFAULT_INSTRUMENTS`.
5. `INSTRUMENTS_BUCKET_VARIANT=test` toggles to the test bucket
   family without code changes.

---

## Plan units

Sequencing: E (benchmark) first, then A backend, B frontend, C
acceptance, D documentation.

### Unit E — instruments read latency benchmark

**Goal**: baseline numbers for one (`asset_group, venue, date`)
shard read, plus a "list all venues for date" multi-shard read.
Comparable shape to the chart plan's Unit E so we can spot
unexpected divergences.

**File**: new — `unified-trading-api/scripts/bench_instruments_reads.py`.

**Scenarios** (5 runs each, p50 + p99):

1. **Single venue, cold** — TRADFI/NASDAQ on a known-backfilled
   date. Capture `t_download_ms`, `t_parse_ms`, `t_normalise_ms`,
   `bytes_transferred`, `n_rows`.
2. **Single venue, warm** — same call again, connection reused.
3. **All TRADFI venues for one date, parallel** — 6 shards
   (CBOE, CME, FX, ICE, NASDAQ, NYSE), `ThreadPoolExecutor`. This
   is what populating the TradFi watchlist tab will cost.
4. **All TRADFI venues for one date, sequential** — same window,
   `max_workers=1`. Isolates per-file cost.
5. **Manifest-pruned all-venues** — first call
   `read_availability_index(bucket)`, derive the venue list for
   the target date, fetch only those. Compare to scenario 3.

**Output**: write to
`unified-trading-pm/plans/ai/reports/watchlist_instruments_benchmark_2026_04_30.md`
(directory pattern matches chart plan's frontmatter convention,
even though the chart's report file isn't on disk yet —
**we make sure ours lands**).

**Numbers to look for**:

- Single shard cold: ≤ 200ms p50 (smaller payloads than candle
  parquets, should be faster).
- 6-shard parallel: ≤ 400ms p99. That sets the watchlist tab-load
  budget.
- Manifest prune win: probably modest for instruments because
  shard count per day is bounded (≤ 10 venues), but worth knowing.

**No code merges.** Benchmark against current `InstrumentsReader`
code path. Re-run after Unit A so we have before/after numbers.

### Unit A — extend `InstrumentsReader` with manifest prune + bucket variant

**Mirrors what `BatchCandleReader` got in
`unified-trading-api` commit `2672e8f`.** Keep the file, extend the
class.

**Files:**

- `unified-trading-api/unified_trading_api/services/instruments_reader.py`
  — add `_prune_dates_via_manifest`, `_resolve_bucket` (with
  variant), `_tune_connection_pool`. Keep
  `_normalise_row` and the existing 1h-TTL row cache as-is.
- `unified-trading-api/unified_trading_api/routes/instruments.py`
  — extend `GET /instruments/list`'s real branch:
  1. Use the new `_resolve_bucket(category, project_id, variant)`
     helper.
  2. If `as_of` not provided: read manifest, pick the most recent
     date with `service_name=="instruments-service"` and the
     requested venue (or any venue if filter omitted).
  3. If `venue` provided: fetch the one shard via existing
     `InstrumentsReader.get_instruments`.
  4. If `venue` omitted: list venues from manifest for the chosen
     date, fetch each in parallel via
     `ThreadPoolExecutor(max_workers=min(16, n_venues))`.
  5. Concat. Pagination unchanged.
- `unified-trading-api/unified_trading_api/routes/instruments.py`
  — `/catalogue` and `/registry` real branches: same pattern,
  smaller surface (no pagination on `/catalogue`).

**Route behavior** (`/instruments/list`):

- Mock: unchanged.
- Real branch:
  - `project_id` resolution chain identical to chart plan.
  - Bucket: `instruments-store-{category}-{variant_suffix}{project_id}`.
  - Empty result → `paginated_response([], page, page_size)`. The
    UI's empty state handles it (no fallback to
    `DEFAULT_INSTRUMENTS` from the backend side; the fallback
    lives in the frontend mock-mode path only).
- Wire `GET /instruments/catalogue` and `GET /instruments/registry`
  to the same orchestrator. They differ only in pagination
  shape — same data source.

**Smoke before merging**:

```
curl ":8030/instruments/list?asset_group=tradfi&venue=NASDAQ&as_of=2026-04-14"
# → expect 41 rows matching the parquet content
curl ":8030/instruments/list?asset_group=tradfi&as_of=2026-04-14"
# → expect ~600 rows (sum across 6 venues)
```

### Unit B — frontend mapping verification + cleanup

**Files:**

- `components/widgets/terminal/use-terminal-page-data.ts:176-239`
  — verify the mapping handles the real schema's column names.
- `hooks/api/use-instruments.ts` — verify the response shape
  matches what the hook expects.

Schema-mapping checks:

| UI watchlist field | Backend column | Notes |
|--------------------|----------------|-------|
| `symbol` | `raw_symbol` | UI currently looks for `i.symbol` — backend column is `raw_symbol`. **Mismatch — fix in Unit A's projection or Unit B's mapping.** |
| `name` | `raw_symbol` for now | No display-name column in schema. Acceptable. |
| `venue` | `venue` | ✓ |
| `category` | derived from `asset_group` | UI uses "CeFi"/"TradFi"/"DeFi"/"Other"; backend has `asset_group=cefi/tradfi/defi`. Add a small mapping. |
| `instrumentKey` | `instrument_key` | snake↔camel conversion; one place to do it. |
| `midPrice` | (from `tickers`, not instruments) | UI joins on `tickers` already. Keep that. |
| `change` | (from `tickers`, not instruments) | Same. |

**Decide once**: do snake↔camel conversion in the backend
projection (so the frontend keeps its current camelCase shape) or
in the frontend mapping (so the backend matches the parquet
column names verbatim). Backend projection is cleaner — a single
boundary, frontend stays unchanged. **Pick backend projection.**

**Critical UX fix**: when API returns `[]` in real mode, the
watchlist must show an empty state with "no instruments
available — check data status" copy, not silently fall back to
`DEFAULT_INSTRUMENTS`. Today's fallback masks real backend
failures. The mock-mode path keeps using `DEFAULT_INSTRUMENTS`
unchanged.

### Unit C — full-stack acceptance

After A + B land:

1. Boot backend with `CLOUD_MOCK_MODE=false`,
   `GCP_PROJECT_ID=central-element-323112`,
   `INSTRUMENTS_BUCKET_VARIANT=prod`, ADC creds.
2. Boot UI with `NEXT_PUBLIC_MOCK_API=false`.
3. Open Terminal. Watchlist should show TRADFI venue's
   instruments (NASDAQ + NYSE + CME + … per the most recent date
   with shards).
4. Switch tabs CeFi / TradFi / DeFi / Other → each populates
   from its bucket. (DeFi will be empty for now — out of scope.)
5. Click an instrument → chart updates accordingly. The 6 MVP
   symbols from the chart plan should still resolve (their venues
   match: NASDAQ + NYSE + BINANCE-FUTURES).
6. Set `INSTRUMENTS_BUCKET_VARIANT=test` → confirm route now hits
   `*-test-*` buckets (will be empty unless test data is loaded;
   verifying routing not data).
7. Network tab: one `/api/instruments/list` call per category-tab
   change, 5-min React Query staleTime → tab-flipping doesn't
   re-fetch. Manifest read piggybacks on the first call; doesn't
   show as a separate request from the UI's perspective.

### Unit G — instrument search + drilldown + presets (separate plan)

**Out of scope for this plan**, but seeded here so it doesn't get
forgotten. Write `instrument_search_2026_05_XX.plan.md` covering:

- `/instruments/search` endpoint with in-memory index per
  (asset_group, day), 1h refresh aligned with `InstrumentsReader._cache`.
- `/instruments/option-chain?underlying=&venue=` — projects
  instruments-service OPTION rows for one underlying into a
  chain shape (expiries, strikes, call/put grid). Replace mock
  `/api/derivatives/options-chain`.
- `/instruments/preset-lists` — serves UAC SSOT presets.
  Add presets to `unified_api_contracts/registry/preset_watchlists/`:
  `nasdaq_100.json`, `sp_500.json`, `top_20_crypto.json`,
  `tradfi_major_futures.json`, `defi_blue_chips.json`.
- UI: replace `WatchlistPanel`'s flat-list search with a typeahead
  fed by `/instruments/search`; add option-chain drawer for
  Deribit options; add preset selector to the watchlist picker.

**Why split**: this plan delivers "watchlist shows real data".
Unit G delivers "watchlist is usable at scale". They're
separable: Unit G presupposes Units A–F are done, and Unit G's
work is roughly twice the size of A–F combined (UI components,
typeahead, chain picker, preset registry).

### Unit D — documentation

- This plan: mark Units A/B/C complete with date.
- Benchmark doc: re-run scenarios after Unit A.
- Stub follow-up plan
  `unified-trading-pm/plans/ai/watchlist_defi_sports_prediction_2026_05_XX.plan.md`
  for the categories deferred here. Note path quirks (SPORTS
  `sports_reference/`, PREDICTION no-venue).
- Update sibling chart plan to reference this plan in §"Out of
  scope" (replacing the placeholder watchlist follow-up note).

---

## Out-of-scope blockers worth flagging

1. **DEFI / SPORTS / PREDICTION watchlists.** Three separate path
   layouts. SPORTS especially diverges (`sports_reference/`,
   `entity=` partition, no `venue=`). Each needs its own reader
   branch. Tracked in follow-up plan stub from Unit D.
2. **Live tickers for real-API mode.** Watchlist rows show
   `midPrice` and `change` columns. Today these come from
   `/market-data/tickers` mock. A real-mode tickers source is its
   own plan (likely tied to the same MTDS pub-sub work that gates
   chart live-mode). Until then, real-API watchlist shows real
   instrument names + venue + type, but `midPrice=0` /
   `change=0`.
3. **Instruments-service writer underfilling the manifest.**
   Spot-checked CEFI manifest — instruments-service rows populate
   `(date, venue)` correctly (much better than MDPS for chart).
   No known gap, but if Unit C surfaces "venue X has shards but
   manifest doesn't list it" that's a writer-side fix in
   instruments-service.
4. **Instruments page (separate from watchlist).** The standalone
   listing UI uses
   `lib/registry/instruments-snapshot.json` (29-day-old static
   snapshot per the 2026-04-25 audit). Replacing that snapshot
   with a live API feed is a separate plan — different surface,
   different UX, different pagination needs.

---

## Acceptance criteria

A. Watchlist (real mode) populates from
   `instruments-store-{cefi,tradfi}-{project}/instrument_availability/`
   for the most recent date with shards, via UTL
   `InstrumentsDomainClient`.

B. NASDAQ tab on `2026-04-14` shows ~41 rows matching
   `gs://instruments-store-tradfi-{project}/instrument_availability/by_date/day=2026-04-14/venue=NASDAQ/instruments.parquet`.

C. Selecting AAPL / MSFT / GOOGL / JPM / BTCUSDT / ETHUSDT from
   the watchlist drives the chart correctly (per chart plan
   acceptance E).

D. Real-mode API empty result → UI shows "no instruments" empty
   state, **not** `DEFAULT_INSTRUMENTS`.

E. `INSTRUMENTS_BUCKET_VARIANT=test` flips bucket family without
   code changes.

F. Backend benchmarks documented:
   - 1-shard cold p99
   - 6-shard parallel p99
   - Manifest-prune win delta

G. `services/instruments_reader.py` extended with manifest prune
   + bucket variant + connection-pool tune. **Not deleted** —
   matches chart plan's `BatchCandleReader` precedent.

H. Benchmark report file lands at
   `plans/ai/reports/watchlist_instruments_benchmark_2026_04_30.md`
   with before/after numbers (single-shard + 6-shard parallel +
   manifest-pruned).

---

## Sequencing

1. **E** — benchmark current `InstrumentsReader` (no merge).
2. **A** — backend swap to UTL + manifest prune, snake→camel
   projection in route, delete `instruments_reader.py`.
3. **B** — frontend mapping verify + remove silent
   `DEFAULT_INSTRUMENTS` fallback in real-API path.
4. **C** — full-stack acceptance.
5. **E re-run** — diff into benchmark doc.
6. **D** — close out + follow-up plan stub.

After D: this plan's scope closes. DEFI/SPORTS/PREDICTION
watchlists + instruments-page snapshot replacement + real-mode
tickers all become separate plans.

---

## Static instruments stay until this plan lands

The chart plan is in flight (a separate agent is working it). Its
contract surface is `DEFAULT_INSTRUMENTS` in
`components/widgets/terminal/use-terminal-page-data.ts:41` — 9
hardcoded entries, of which 6 (`NASDAQ:AAPL`, `NASDAQ:MSFT`,
`NASDAQ:GOOGL`, `NYSE:JPM`, `BINANCE-FUTURES:BTCUSDT`,
`BINANCE-FUTURES:ETHUSDT`) have GCS shards backfilled.

**Until this plan finishes**, the chart agent should keep reading
from `DEFAULT_INSTRUMENTS` exactly as today:

- The chart's `useTerminalData()` derives `selectedInstrument` from
  the watchlist tab; the watchlist still maps over
  `DEFAULT_INSTRUMENTS` in mock mode. In real-API mode the watchlist
  *also* falls through to `DEFAULT_INSTRUMENTS` when the API
  returns empty (line 238 of `use-terminal-page-data.ts`) — that's
  the silent fallback we'll remove in Unit B, but it's keeping the
  chart usable today.
- The chart's `useCandles(venue, symbol, timeframe, ...)` call
  receives `selectedInstrument.venue` + `selectedInstrument.symbol`
  — exactly the strings `DEFAULT_INSTRUMENTS` ships. As long as
  those strings keep matching the GCS partition values
  (`NASDAQ` / `AAPL`, `BINANCE-FUTURES` / `BTCUSDT`, etc.), the
  chart works.
- **Don't change `DEFAULT_INSTRUMENTS`** while the chart plan is in
  flight. New entries added there must match a real
  `(venue, symbol)` parquet path, or the chart will render "No chart
  data available" for them — which is the correct empty state but
  looks like a regression in screenshots.

**When this plan lands** (Units A+B+C):

- Real-API watchlist switches to GCS-backed data via UTL.
  `DEFAULT_INSTRUMENTS` becomes mock-mode-only — its job is
  preserved, scope shrinks.
- The 6 MVP symbols stay in `DEFAULT_INSTRUMENTS` for the
  mock-mode tier. Real mode shows whatever instruments-service has
  published — much wider set than the 6 MVP.
- Unit B's removal of the silent real-API fallback to
  `DEFAULT_INSTRUMENTS` happens at the same time as Unit A so the
  UI never has a window where real mode returns empty AND the
  fallback is gone — both ship together.

**Migration coordination**: when Unit A+B merge, do a quick smoke on
the chart side to confirm the chart still gets the same 6 MVP
symbols in the watchlist (instruments-service should publish them
for current dates, but worth verifying — if instruments-service
isn't writing one of them on the day Unit C runs, the chart breaks
silently for that symbol). If a symbol is missing, file an
instruments-service issue, don't add it back to
`DEFAULT_INSTRUMENTS` as a workaround.

---

## Sibling plan coupling

The chart plan (`price_chart_gcs_delivery_2026_04_29.plan.md`) and
this plan are independent reads against different bucket families,
but acceptance C of this plan (selecting an instrument from the
watchlist drives the chart) requires both to be working. Ordering:

- Chart plan can land first — chart works against
  `DEFAULT_INSTRUMENTS` until this plan replaces them.
- This plan can land first — watchlist populates real instruments
  but selecting them drives the chart's mock-fallback (the chart's
  `isMockMode` path) until the chart plan lands.
- Either order is fine. They're additively safe.

The two plans share:

- The `read_availability_index` + UTL domain-client pattern.
- The `*_BUCKET_VARIANT=prod|test` toggle convention.
- The `project_id` resolution chain.
- The 60s manifest cache (different bucket key, same dict).

If we want to factor the shared bits into a single helper after
both land, that's a refactor follow-up — don't do it in either
plan, would couple them unnecessarily.
