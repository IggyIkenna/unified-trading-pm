---
title: features-service DeFi end-to-end test blocked on multiple data layer issues
created: 2026-05-29
status: open
source:
  - features-service@9f6bc119
  - market-data-tick-defi-central-element-323112 (legacy)
  - market-data-tick-defi-prd-central-element-323112 (prd)
locked_by: live-defi-rollout
priority: P2
---

> **🟦 OPERATOR DECISION LEDGER — 2026-06-01 (Ikenna, recorded slot-1).** FINAL rulings on the 4 routed DeFi calls.
> Execution: **slot 7**, recorded into `features_and_ml_master` (SSOT). **No legacy-bucket manifest rebuild** — that
> would be manifest-canonicalisation work owned by slots 2/3.
>
> - **#1** — map `volume_analysis` / `vwap` / `microstructure` → **`dex_pool_swaps`** via UAC
>   `resolve_data_type_for_feature_group()` (not a hardcoded override). features-service, self-contained. [slot 7 code]
> - **#2** — legacy bucket = **read-only-historical-archive**. Do NOT rebuild its manifest, do NOT load from it via
>   features-service. [policy only — record, no code]
> - **#3** — `dex_swaps` OHLC semantics: **investigate** the MDPS writer; report whether O/H/L/C are spot price or a
>   normalized metric. File a UAC contract-doc todo OR an MDPS-bug todo per the finding. No blind edit. [slot 7 reports]
> - **#4** — drop duplicate columns `swap_count` (==`trade_count`) + `volume_quote_usd` (==`volume`) from
>   `DEX_SWAPS_SCHEMA` as a UAC cleanup — only if it does not collide with `defi_manifest_canonicalisation`. [slot 7 >
>   code]

## What I found

While trying to run a smoke test of features-service `delta_one` against real DeFi data (operator-directed 2026-05-29
after the CeFi MDPS canary VM failed), I hit a cascade of issues at the data-layer boundary that need workspace-level
decisions before features-service work can resume against either bucket.

### Issue 1 — PRD bucket uses different `data_type` names for V3 pools, features-service code can't find them

PRD's manifest reports 1,569,407 rows of DeFi index data with venue/data_type distribution:

| data_type         | rows in PRD manifest |
| ----------------- | -------------------- |
| `dex_pool_swaps`  | 114,322              |
| `dex_pool_state`  | 113,613              |
| `dex_swaps`       | **94,672**           |
| `oracle_prices`   | 69,366               |
| `lending_indices` | 64,404               |
| …                 | …                    |

**Crucially**, the physical PRD layout for `data_type=dex_swaps` on 2026-05-22 contains only 9 venues — none of which
are UNISWAP:

```
BALANCER-ARBITRUM, BALANCER-AVALANCHE, BALANCER-BASE, BALANCER-ETHEREUM,
BALANCER-OPTIMISM, BALANCER-POLYGON, CURVE-AVALANCHE, CURVE-ETHEREUM, SUSHISWAP-ARBITRUM
```

`features_service.delta_one.engine.orchestrator.DEFI_DATA_TYPE_OVERRIDES` hardcodes `volume_analysis`, `vwap`,
`microstructure` → `dex_swaps`. With this mapping, **all UNISWAP V3 data is invisible to features-service in PRD** — the
V3 concentrated-liquidity pools are written under `dex_pool_swaps`, not the old constant-product `dex_swaps` name.

### Issue 2 — Legacy bucket manifest is incomplete for the most-important pools

The legacy bucket (`market-data-tick-defi-central-element-323112`) physically has the UNISWAP V3 ETH/USDC pool
(`0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640`) under `data_type=dex_swaps/venue=UNISWAP_V3-ETHEREUM/` for every day from
at least 2024-07-01 onward (verified via direct GCS probe — 162-171 parquets per day, all 6 timeframes present,
file-level data passes invariants).

But the bucket's `_index/availability_index.parquet` has **1,812,297 total rows** of which **zero** match this pool. The
MDPS canonical writer never registered these instruments in the legacy manifest after the bucket migration.

Downstream effect: `data_loader._collect_daily_frames` queries the manifest first, gets nothing, falls back to per-day
`blob_exists` probes (legacy code path). The fallback finds _some_ files but not consistently — see Issue 4.

### Issue 3 — `PROTOCOL_DATA_SOURCE_BUCKET_DEFI` workaround required to read legacy

`features_service.delta_one.app.core.data_loader._get_source_bucket` resolves the source bucket via:

```
UCI get_data_source(routing_key="defi") → fallback to resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")
```

Both resolve to the env-tiered `market-data-tick-defi-prd-central-element-323112` (the new SSOT). To read the legacy
bucket where the historical data actually lives, set:

```bash
PROTOCOL_DATA_SOURCE_BUCKET_DEFI=market-data-tick-defi-central-element-323112
```

This is **the only documented workaround** as of 2026-05-29. The features-service code intentionally moved off the
legacy bucket because it's "deprecated + un-consolidated (stale manifest, thousands of accumulated per-VM shards, full
pre-migration history)" — per the docstring at `features_service/delta_one/app/core/data_loader.py:42-50`. The
workaround is for TESTING ONLY; **production must use PRD**.

### Issue 4 — Lookback loader only pulls partial days (79 rows when 240 expected)

With the legacy-bucket workaround in place:

- Target: 2024-07-22, base timeframe 1h, lookback-buffer-days 10
- Expected: 10 days × 24 hours = 240 candles
- Loaded: **79 candles** (32% of expected)
- 4h compute fails: `"Insufficient data for volume_analysis: have 79 rows, need 120"`

DeFi (like CeFi) operates 24/7 — there is no legitimate reason for a multi-day window of an active top-3 pool to return
only 79 hourly candles. Either the manifest gap (Issue 2) is making the loader silently drop dates the manifest doesn't
know about, or there's a per-day filter / partial-load path being exercised. **Root cause not yet identified beyond the
manifest hypothesis** — full trace would need DEBUG-level logging across the inner loop and per-day cardinality
assertion.

### Issue 5 — `data_type=dex_swaps` OHLC values look wrong (price ≈ 1.0 for ETH/USDC)

The single parquet I downloaded for verification (UNISWAP V3 ETH/USDC 0x88e6a0c2... 2024-07-15, 1h):

| field            | value                                |
| ---------------- | ------------------------------------ |
| open             | 1.000513                             |
| high             | 1.001652                             |
| low              | 0.998193                             |
| close            | 0.999771                             |
| volume           | 1.187e7                              |
| volume_quote_usd | **1.187e7** (identical to `volume`)  |
| trade_count      | 392                                  |
| swap_count       | **392** (identical to `trade_count`) |

ETH on 2024-07-15 was ~$3,200. ETH/USDC OHLC should show prices in the $3,000-3,500 range. The pool address
`0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640` IS verified as the canonical USDC/WETH 0.05% pool (chain probe of pool
metadata confirms). So either:

- (a) the `open/high/low/close` columns are NOT the spot ETH/USDC price — they're some normalized quantity
  (price-relative-to-previous? sqrt-tick-ratio? token0/token1 with one side near zero?), OR
- (b) MDPS aggregation for V3 pools is computing the wrong field, OR
- (c) the schema does NOT use spot price as `open/high/low/close` for DEX swaps at all and we're misreading the
  contract.

Additionally:

- `volume` == `volume_quote_usd` to last decimal across all 24 rows
- `trade_count` == `swap_count` to last digit across all 24 rows

Either these are duplicate columns by design (then the contract should drop one and document it) or one of each pair is
being silently overwritten by the other during canonical-writer compute. Either way it's a UAC schema cleanup target.

## Why it matters

We **cannot** validate features-service `delta_one` against either DeFi bucket today:

- **PRD**: features-service `dex_swaps` mapping misses all UNISWAP V3 (the biggest data set in PRD). Only
  Balancer/Curve/Sushi reachable.
- **Legacy**: workaround required; lookback partial (Issue 4); OHLC values look semantically wrong (Issue 5).

This blocks the operator-directed "validate features-service against the data we have" workstream until at least one of
these is resolved.

CeFi has the same shape (different mechanism — operator/Sonnet-4.6 canary VM failure 2026-05-28; raw exists but
processed is sparse — see `mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`).

## Recommended decision

**Operator-only design calls needed**:

1. **DEFI data_type mapping** — Should `features_service.delta_one.engine.orchestrator.DEFI_DATA_TYPE_OVERRIDES` map
   `volume_analysis`/`vwap`/`microstructure` to `dex_pool_swaps` (the V3 concentrated-liquidity schema) instead of / in
   addition to `dex_swaps`? This is the unblock for PRD-based testing. Probably needs a UAC
   `resolve_data_type_for_feature_group()` reconciliation (per the comment at orchestrator.py:124).
2. **Legacy bucket consolidation runner** — Should we run a one-shot manifest-rebuild over the legacy bucket so the
   existing data becomes discoverable for the testing-only window? Or formally declare the legacy bucket
   read-only-historical-archive and never load from it via features-service?
3. **dex_swaps OHLC contract** — what DO the `open/high/low/close` columns represent? File a UAC contract doc if they're
   a normalized metric, or raise an MDPS bug if they should be spot price.
4. **Duplicate columns** — drop `swap_count` (==trade_count) and `volume_quote_usd` (==volume) from `DEX_SWAPS_SCHEMA`
   as a UAC cleanup, OR document why they're separate.

**Things I can implement once those decisions land**:

- Update `DEFI_DATA_TYPE_OVERRIDES` to the new data_type names.
- Run a smoke test against PRD with the corrected mapping.
- Update the env-var workaround documentation (or remove it once legacy is fully decommissioned).

## Provenance / how to reproduce

```bash
# 1. Confirm legacy bucket has the pool physically
gcloud storage ls "gs://market-data-tick-defi-central-element-323112/processed_candles/by_date/day=2024-07-15/timeframe=1h/data_type=dex_swaps/venue=UNISWAP_V3-ETHEREUM/UNISWAP_V3-ETHEREUM:POOL:0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640.parquet"
# → present

# 2. Confirm legacy manifest does NOT have the pool
.venv/bin/python -c "
import polars as pl, io
from google.cloud import storage
b = storage.Client().bucket('market-data-tick-defi-central-element-323112')
df = pl.read_parquet(io.BytesIO(b.blob('_index/availability_index.parquet').download_as_bytes()))
print(df.filter(df['instrument_id'].str.contains('0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640')).shape)
"
# → (0, 32)

# 3. Confirm PRD physically lacks UNISWAP venues under dex_swaps
gcloud storage ls 'gs://market-data-tick-defi-prd-central-element-323112/processed_candles/by_date/day=2026-05-22/timeframe=1h/data_type=dex_swaps/' | grep -i uniswap
# → empty

# 4. Confirm feature-service mapping
grep -A 20 "DEFI_DATA_TYPE_OVERRIDES" features-service/features_service/delta_one/engine/orchestrator.py
# → maps volume_analysis/vwap/microstructure → dex_swaps

# 5. Feature compute attempt (legacy + workaround)
PROTOCOL_DATA_SOURCE_BUCKET_DEFI=market-data-tick-defi-central-element-323112 \
GCP_PROJECT_ID=central-element-323112 \
features-service --feature-family delta_one --operation compute --mode batch \
  --asset-group DEFI --start-date 2024-07-22 --end-date 2024-07-22 \
  --feature-group volume_analysis --timeframe 1h \
  --instruments "UNISWAP_V3-ETHEREUM:POOL:0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640" \
  --max-workers 1 --skip-preflight --skip-dependency-check \
  --lookback-buffer-days 10 --dry-run
# → "Insufficient data for volume_analysis: have 79 rows, need 120"
```

## Related plans

- `plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md` — CeFi MDPS memory pathology + canary VM
  failure (parallel issue, different bucket / mechanism)
- `plans/active/features_calc_efficiency_and_correctness_2026_05_27.md` — original 4h/24h blocking issue § 1.0b
- `plans/active/features_registry_status_versioning_2026_05_28.md` — yesterday's shipped registry / status / version
  work (downstream consumer of whatever data layer fix lands here)
- `codex/02-data/feature-formula-versioning.md` — codex SSOT for downstream feature versioning

## Status taxonomy

`BLOCKED-OPERATOR-DECISION` — operator must pick between (1) extend DEFI_DATA_TYPE_OVERRIDES to PRD's data_type names,
(2) rebuild legacy manifest, or (3) wait for MDPS refactor + canonical migration to finish before any features-service
work against DeFi. Until one of these lands, features-service smoke tests against real DeFi data cannot proceed.

## Unblock progress 2026-05-29 evening — CeFi path-of-least-resistance kicked off

Operator directive 2026-05-29 16:00 IST: "we already have raw tick data — just use the date range that has it. If not in
prd, copy from legacy to test." Pivoted from the four open DeFi decisions above to running the chain on CeFi via legacy
raw → test bucket, since legacy CeFi raw has all the top venues (BINANCE-FUTURES, BINANCE-SPOT, BYBIT, COINBASE-SPOT,
DERIBIT, KRAKEN-FUTURES/SPOT, OKX-SPOT/SWAP, BITFINEX-FUTURES, BITGET-FUTURES/SPOT, UPBIT) for the 2026-04-15 →
2026-05-04 window.

**Test scope** (kept narrow for first end-to-end pass):

- Venues: BINANCE-FUTURES + BYBIT (no Tardis-key dependency for either)
- Instruments: BTCUSDT + ETHUSDT (top 2 perp pairs)
- Data types: trades + book_snapshot_5 + derivative_ticker + liquidations
- Window: 2026-04-15 → 2026-05-04 (21 days)

**Step 1 — Raw copy DONE 18:32 IST**: 334 of 336 expected parquets copied from
`market-data-tick-cefi-central-element-323112` → `market-data-tick-cefi-test-central-element-323112`. The 2 missing
files (`day=2026-05-04 BINANCE-FUTURES book_snapshot_5 ETHUSDT.parquet`, `day=2026-05-04 BYBIT trades BTCUSDT.parquet`)
are missing in the source legacy bucket too — not a copy failure. MDPS will record_empty for those shards.

**Step 2 — MDPS canary** —

- **First attempt 18:44 IST → STUCK + KILLED 19:30 IST**: VM `mdps-backfill-cefi-main-test-20260529-184417`
  (e2-standard-8, 32 GB). T+10min check: 3,920 parquets, day-1 had all 7 timeframes ✓. T+30min check: still 3,920
  parquets (zero growth in 20 min). Latest event was `PROCESS_MEMORY_WARNING` —
  `process_rss=31.2 GB / system_memory_percent=95.4% / process_cpu_percent=136.4% / process_num_threads=75`. Confirmed:
  backpressure-gating wedge, NOT a crash. The `_cleanup_after_day` fix alone isn't enough on e2-standard-8 for this
  scope. Root cause: filter-pushdown bug (`mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`) means MDPS reads
  ALL ~9 instruments per venue per data_type per day, ignoring `MDPS_INSTRUMENT_IDS=BTCUSDT+ETHUSDT` filter. Peak
  per-day RSS exceeds 32 GB even at day-1.
- **Second attempt 19:34 IST**: VM `mdps-backfill-cefi-main-test-20260529-193445` (e2-highmem-8, **64 GB** = 2×
  headroom). Same scope, same env vars; only machine type changed. If filter-pushdown peak is ~31 GB, this VM should
  clear it with 33 GB margin.
- **v2 T+15min**: memory 29% / RSS 22.8 GB / day-18 already at 189 parquets ✓ healthy.
- **v2 T+30min**: memory **61%** / RSS **44.6 GB** (doubled in 15min). 8 days have output (04-15 → 04-22). VM still
  RUNNING. Per-day-cleanup not aggressive enough yet — memory still climbing but plenty of headroom on 64 GB.

**Step 3 — features-service smoke 20:32–20:39 IST** — TWO REAL BUGS FOUND + ONE SUCCESS:

- First smoke attempt FAILED with `unable to vstack, column names don't match: "buy_volume" and "buy_trade_count"`. Root
  cause: **MDPS canonical_writer produces inconsistent column ORDER across days**. Day-15 (written by v1 VM before
  crash): `..., buy_volume, sell_volume, buy_trade_count, sell_trade_count, ...`. Day-16+ (written by v2 VM, current
  code): `..., buy_trade_count, sell_trade_count, buy_volume, sell_volume, ...`. Same 35 columns, same data, just
  different order. Polars `vstack` is strict on column order. This is BOTH (a) an MDPS bug — canonical_writer should
  produce stable column ordering — AND (b) a features-service improvement opportunity — `data_loader._concat_and_sort`
  should use `pl.concat([...], how="diagonal_relaxed")` to handle column-order drift. File as findings against MDPS +
  features-service.

- Second smoke attempt (after day-15 BTCUSDT vanished — v2 may have overwritten or relocated): vstack error GONE ✓ but
  new gate: `Insufficient data for technical_indicators: have 43 rows, need 50` (1h). 7 days of BTCUSDT present in test
  bucket (04-16 → 04-22 = 168 hours raw) but only 43 hours actually loaded. Likely the loader's per-instrument concat is
  silently dropping rows that don't match schema/window strictly. Will resolve once MDPS writes more days OR a
  feature_group with smaller lookback runs.

**Success surface validated**:

- Bucket override (`PROTOCOL_DATA_SOURCE_BUCKET_CEFI`) works for both manifest read + per-day blob reads ✓
- features-service loads MDPS-test-bucket data successfully ✓
- FINDING-B failure manifest writes work (`record_failed` rows landed in `features-delta-one-cefi-PID`) ✓
- Path-partition versioning code path reached (even though no successful write yet, the gate logic ran)

**Remaining blockers**:

- MDPS column-order drift fix needed (or features-service load_candles needs `diagonal_relaxed`).
- Sufficient BTCUSDT days for 50-bar lookback. Once MDPS clears more days, retry.

**v2 T+60min** (current): memory **cycled back to 29% / 23 GB** — confirms per-day cleanup IS working between days (peak
~45 GB during processing, floor ~23 GB after day-rollover). 4,403 parquets, 18 contiguous BTCUSDT days (04-16 → 05-03).
Memory amplitude proves the filter-pushdown bug is what's driving peak: each day's processing allocates ~20 GB over the
23 GB baseline, then releases. The baseline itself is ~150× the raw input size (156 MB/day raw → 23 GB resident) —
confirms operator's observation that "32 GB should have been overprovisioned." Root cause: queue-time over-allocation
per audit § 5 (un-shipped 3-line fix to `_collect_matching_parquet_blobs`).

**Step 3 retry — features-service smoke 21:18 IST** — Real progress + new bug:

- **Loaded 168 candles ✓** (7 days × 24 hours of 1h BTCUSDT). MDPS data is consistent + features-service is consuming
  it.
- **NEW BUG: timezone-aware vs naive datetime join mismatch**:
  `datatypes of join keys don't match - "timestamp": datetime[ns, UTC] on left does not match "timestamp": datetime[ns] on right (and no other type was available to cast to)`.
  MDPS canonical_writer produces `timestamp` as **naive** (no time zone) but `available_at` as **UTC-aware**. Some join
  in features-service compares the two and polars refuses to cross types. Code at
  `features_service/delta_one/engine/orchestrator.py:760` has `tz_localize("UTC")` for one path but not the join that's
  failing here. **Third real bug surfaced by the smoke** (after column-order drift + load-volume gating).

Compounding tally for the day:

1. MDPS canonical_writer column-order drift across days (v1 vs v2)
2. MDPS filter-pushdown bug: 150× memory overhead vs raw input size (audit § 5 fix still un-shipped)
3. MDPS/features-service tz-aware vs naive datetime contract mismatch on `timestamp` vs `available_at`

Each of these is a real cross-repo finding that blocks features-service from writing its first real parquet to
`gs://features-delta-one-cefi-*`. The audit items (l) / (live-versioning) / (batch-live) remain BLOCKED on a clean
end-to-end write, but the pipeline shape is proven working.

**Step 3 — Features-service smoke** (pending Step 2 success): once MDPS produces processed candles in test bucket,
features-service runs with `PROTOCOL_DATA_SOURCE_BUCKET_CEFI=market-data-tick-cefi-test-central-element-323112`. First
write to `gs://features-delta-one-cefi-*` unblocks audit items (l) / (live-versioning) / (batch-live) per
`plans/audit/results/features_and_ml_master_audit_2026_05_29.md`.

The four DeFi operator-decisions in the original issue body remain open — this CeFi pivot is the parallel path, not a
replacement.

---

## EOD handoff 2026-05-29 21:30 IST — for Ikenna

### What completed today

- **MDPS canary v2 SUCCESS**: VM `mdps-backfill-cefi-main-test-20260529-193445` (e2-highmem-8, 64 GB) ran from 19:34 →
  21:19 IST (~2h15m), emitted `PROCESSING_COMPLETED` + `STOPPED` cleanly, self-deleted on stop. Output in
  `gs://market-data-tick-cefi-test-central-element-323112/processed_candles/by_date/`:
  - **4,424 processed parquets** across 21 days × 7 timeframes × 4 data_types × 2 venues
  - **19 BTCUSDT days present** (04-16 → 05-04). Edges 04-15 + 05-05 were source-missing in legacy raw, not a canary
    failure.
- **Drift gate operational** — features-service@dd2ed36f shipped `BASELINE_FORMULA_HASHES` + QG STEP 5.91 +
  DRIFTED-detection. State: MATCH=5 / DRIFTED=0 / NEW=29.
- **Audit shipped** — `plans/audit/results/features_and_ml_master_audit_2026_05_29.md`. 14 GREEN / 3 DRIFT (text-fixed
  in same commit) / 3 BLOCKED (l + live-versioning + batch-live, all waiting on the first features-delta-one parquet) /
  2 NOT-RUN (ml-service).

### What's BLOCKED — three cross-repo bugs need a slot

Each bug below independently blocks features-service from writing its first real parquet. Ordered by fastest unblock
first:

**1. MDPS / features-service tz-aware vs naive datetime contract drift (P0 — fastest unblock)**

- Symptom:
  `datatypes of join keys don't match - "timestamp": datetime[ns, UTC] on left does not match "timestamp": datetime[ns] on right`.
- Cause: MDPS canonical_writer produces `timestamp` as **naive** (no tz) but `available_at` as **UTC-aware**.
  Features-service joins them in delta_one's PIT / lookahead enforcement.
- Fix options:
  - (a) MDPS — make canonical_writer produce `timestamp` as UTC-aware (preferred, since `available_at` already is);
    ~5-line change in the writer.
  - (b) features-service — add `.dt.replace_time_zone("UTC")` on the naive side at the failing join site. Code site near
    `features_service/delta_one/engine/orchestrator.py:760` (`tz_localize("UTC")` already exists for one path; need to
    locate the joining one).
- Single PR either way; ~30 min work. After this, features-service should write the first real parquet to
  `gs://features-delta-one-cefi-{pid}/feature_group=*/feature_group_version=1/...`. That write unblocks audit items
  (l) + (live-versioning) + (batch-live).

**2. MDPS canonical_writer column-order drift across days (P0 — silent corruption risk)**

- Symptom: Day-15 (written by killed v1 VM) has `..., buy_volume, sell_volume, buy_trade_count, sell_trade_count, ...`.
  Day-16+ (v2) has `..., buy_trade_count, sell_trade_count, buy_volume, sell_volume, ...`. Same 35 cols, same data,
  different order. Polars `vstack` is strict → load fails.
- Cause: canonical_writer derives column order from a non-deterministic source (probably `dict()` iteration on an older
  Python or a `set`). Two MDPS code paths produce two different orders.
- Fix:
  - (a) MDPS — declare a canonical column order in `unified_api_contracts.internal.MDPS_CANDLE_SCHEMA` and have the
    writer reorder to it before `write_parquet`. Single SSOT.
  - (b) features-service — change `data_loader._concat_and_sort` (and any other `vstack` callsite) to
    `pl.concat([...], how="diagonal_relaxed")` to tolerate column-order mismatches defensively.
- Both should ship. (b) protects against future MDPS schema-evolution surprises.

**3. MDPS filter-pushdown queue-time fix (P1 — wasteful, not a correctness blocker)**

- Symptom: 23 GB resident baseline for processing 156 MB/day of raw input. ~150× overhead. e2-highmem-8 (64 GB) needed;
  e2-standard-8 wedges.
- Cause: `_collect_matching_parquet_blobs` queues every file from every day before filtering on `MDPS_INSTRUMENT_IDS`.
  1,440 files queued as polars lazy frames = ~25 GB queue overhead.
- Fix: 3-line change in `_collect_matching_parquet_blobs` per audit § 5 of
  `plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md` — filter at queue time, not at work time.
  Per-day peak should drop to <500 MB.
- Plan already filed; just needs to ship.

### What's READY to be used

- Test bucket `market-data-tick-cefi-test-central-element-323112/processed_candles/` has **4,424 high-quality processed
  candles** for BINANCE-FUTURES + BYBIT × 9 instruments × 4 data_types × 7 timeframes × 2026-04-16 → 2026-05-04 (19
  days).
- Once bug 1 ships, this bucket is the unblock-data for the features-service smoke chain. Invocation:
  ```bash
  PROTOCOL_DATA_SOURCE_BUCKET_CEFI=market-data-tick-cefi-test-central-element-323112 \
  GCP_PROJECT_ID=central-element-323112 \
  features-service --feature-family delta_one --operation compute --mode batch \
    --asset-group CEFI --start-date 2026-04-22 --end-date 2026-04-22 \
    --feature-group technical_indicators --timeframe 1h \
    --instruments "BINANCE-FUTURES:PERPETUAL:BTCUSDT" \
    --max-workers 1 --skip-preflight --skip-dependency-check
  ```

### What can be picked up later (lower priority)

- Audit items (c) + (d) — ml-service inference / training tests, separate audit pass.
- Audit item (o) — "listed" backlog trend (needs week-over-week snapshots; first one taken today at `listed=1329`).
- DeFi parallel path — the four original operator decisions in this issue body (data_type override / legacy manifest /
  OHLC contract / duplicate columns) are still open. CeFi pivot proved we can validate features-service without
  resolving DeFi first; DeFi remains a separate workstream.

### Plan & code commits today

- features-service: `9a53b888` (Phase 1) → `e4e085d1` (Phase 2) → `0fe3160d`/`9f6bc119` (Phase 3 + path-partition
  correction) → `32c0a1ce` (Phase 4) → `dd2ed36f` (drift gate operational + QG STEP 5.91).
- unified-trading-pm: features_registry_status_versioning plan + 5 phase flips + features_and_ml audit-instructions
  extension + features_and_ml audit-result doc + this issue doc with continuous status updates.
