# TradFi Instrument-Pool Universe Audit (READ-ONLY, pre-migration)

**Date:** 2026-06-17 · **Author:** audit agent (slot, central VM)
**Scope:** TradFi raw tick data we ACTUALLY have, per `(venue, instrument_type, data_type)` shard, sampled one
representative weekday trading day per year (mid-June), 2020→2026.
**Bucket:** `gs://market-data-tick-tradfi-prd-central-element-323112/raw_tick_data/by_date/`
**Method:** `gcloud storage ls -r` per sample day, unioning BOTH legacy `category=tradfi/` and canonical
`asset_group=tradfi/` leaf forms; instrument stems / `underlying=` extracted from paths; CME chain contract months read
from the parquet `symbol` / `instrument_id` columns. Counts are grounded in `ls` line counts. No writes performed.

> **Migration state:** NOT applied. 2020–2025 days carry the OLD shape (`day=.../{asset_group|category}=tradfi/venue=…`,
> NO `pipeline_mode=`). Same venue's shards appear under BOTH `category=` (bulk) AND `asset_group=` (a small slice) on
> the same day — dual-written / partial migration. **2026 recent writes are canonical** (`day=…/pipeline_mode=batch_databento/asset_group=tradfi/venue=…`).

## Sample days (all weekdays, off US holidays)

| Year | Day        | Weekday | Total parquets (both leaves) | Notes                                              |
| ---- | ---------- | ------- | ---------------------------- | -------------------------------------------------- |
| 2020 | 2020-06-15 | Mon     | 545                          | CME + FX + ICE only; NO equities                   |
| 2021 | 2021-06-15 | Tue     | 542                          | same shape as 2020                                 |
| 2022 | 2022-06-15 | Wed     | 559                          | CME crypto futures (BTC/ETH) appear                |
| 2023 | 2023-06-15 | Thu     | **5663**                     | equities (NYSE/NASDAQ) onboard + option-strike explosion |
| 2024 | 2024-06-13 | Thu (06-15=Sat) | 779                  | files carry `_migrated_20260419…` suffix           |
| 2025 | 2025-06-13 | Fri (06-15=Sun) | 1169                 | tbbo/trades depth added on equities                |
| 2026 | 2026-05-13 | Wed     | 242                          | richest 2026 day; thinner than 2025 (mid-rollout)  |

> **No 2018 data** — canonical history begins 2020-01-01. 2026 is sparse: many days have 0 parquets; latest day
> `day=2026-06-05` (new `pipeline_mode=batch_databento` shape) carries only CBOE VIX (1 file) — TradFi 2026 ingestion is
> mid-rollout, NOT a full daily universe yet.

---

## CBOE

| data_type        | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Sample |
| ---------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ------ |
| index/ohlcv_15m  | 1    | 1    | 1    | 1    | 1    | 1    | 1    | `VIX`  |

CBOE = the **VIX index only**, single instrument, present every year (the static-universe exception — VIX index never
expires). Matches CLAUDE.md "VIX 15m: Barchart preload + Yahoo rolling 60d". No VX futures here (consistent with "Massive
does NOT cover VIX/VX futures").

---

## CME (the dominant TradFi venue — 557 of 1169 parquets in 2025)

### futures_chain — the contract-roll signal (universe lives INSIDE the parquet)

Each `underlying=<U>/ticks.parquet` bundles the whole front-month chain; the **contract months are the `symbol` column**,
not the path. ES chain read directly per year:

| Year | ES front contracts (`symbol`) | First `instrument_id` expiries                   |
| ---- | ----------------------------- | ------------------------------------------------ |
| 2020 | ESM0 ESU0 ESZ0                | ES-20200619 / 20200918 / 20201218                |
| 2021 | ESM1 ESU1 ESZ1 ESH2           | ES-20210618 / 20210917 / 20211217 / 20220318     |
| 2022 | ESM2 ESU2 ESZ2 ESH3           | ES-20220617 / 20220916 / 20221216 / 20230317     |
| 2023 | ESM3 ESU3 ESZ3 ESM4 ESH4      | ES-20230616 … 20240315 / 20240621                |
| 2024 | ESM4 ESU4 ESZ4 ESH5           | ES-20240621 / 20240920 / 20241220 / 20250321     |
| 2025 | ESM5 ESU5 ESZ5                | ES-20250620 / 20250919 / 20251219                |
| 2026 | ESM6 ESU6 ESZ6                | ES-20260619 / 20260918 / 20261218                |

**This is the universe-churn story in one table:** the M/U/Z (Jun/Sep/Dec) front rolls forward exactly one year-digit
per sample (ESM0→ESM6); on a mid-June day the spot June contract is at/near expiry so some years also carry the next-March
(ESH+1). ES chain 2025 verified REAL: 2603 rows, close 5928–6132, volume 1.83M.

**Chain underlyings present (path-level), per year:**

| data_type            | 2020      | 2021      | 2022                       | 2023                       | 2024                       | 2025                       | 2026                  |
| -------------------- | --------- | --------- | -------------------------- | -------------------------- | -------------------------- | -------------------------- | --------------------- |
| futures_chain/ohlcv_1m | ES, MES | ES, MES | BTC ES ETH MBT MES MET (6) | BTC ES ETH MBT MES MET (6) | BTC ES ETH MBT MES MET (6) | BTC ES ETH MBT MES MET (6) | CL ES GC MES NQ (5)   |
| futures_chain/trades   | ES, MES | ES, MES | BTC ES ETH MES (4)         | (4)                        | (4)                        | (4)                        | ES (1)                |

Churn: **crypto futures (BTC/ETH + micros MBT/MET) onboarded 2022**; ES/MES present from genesis. **2026 differs — adds
CL (crude), GC (gold), NQ (Nasdaq) but DROPS the BTC/ETH/MBT/MET crypto micros** for this sample day (the 2026 universe is
a different, partial set — flagged below).

### options_chain

`options_chain/ohlcv_1m` = `underlying=ES` only, every year (single underlying, ES options-on-future).

### future (per-contract individual files — option-on-future strikes)

`future/data_type=trades` holds **~503 individual strike parquets per day** every year 2020–2025 (e.g. `E3AM5_C5975`,
`E1AN3_P3360` = ES weekly call/put options-on-future strikes). The `E?A?<N>` symbol root carries the year digit, so the
strike universe rolls each year (E1AN0→E1AN5). `future/ohlcv_1m` is a SINGLE bundled `ticks.parquet` (148K+ rows) most
years; in 2023 it ALSO has 504 per-strike files (the 5663-parquet anomaly that day).

### combo (spread/calendar instruments)

`combo/ohlcv_1m` = 26–37 `underlying=` spreads per year (`12`, `23`, `3W`, `BO`, `BX`, `SP500`, `BTC`, `ETH`…), stable
~30-instrument set across all years. `combo/trades` = MES + SP500 (+ BTC/ETH from 2022).

---

## NASDAQ (equities — onboarded 2023)

| data_type        | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Sample                                  |
| ---------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | --------------------------------------- |
| equity/ohlcv_1m  | -    | -    | -    | 41   | 42   | 43   | 43   | AAPL ADBE ADI AMAT AMD AMGN AMZN AVGO … |
| equity/tbbo      | -    | -    | -    | -    | -    | 41   | -    | (NBBO depth added 2025 only)            |
| equity/trades    | -    | -    | -    | -    | 1 (IBIT) | 43 | -  | (tick trades added 2025)                |

NASDAQ equity universe is a **stable ~41–43 large-cap names** (NDX-style mega-caps) from 2023. `tbbo`/`trades` depth is a
2025-only layer and is ABSENT in 2026.

---

## NYSE (equities — onboarded 2023)

| data_type        | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Sample                          |
| ---------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ------------------------------- |
| equity/ohlcv_1m  | -    | -    | -    | 158  | 159  | 159  | 155  | A ABBV ABT ACGL ACN ADSK AFL …  |
| equity/tbbo      | -    | -    | -    | -    | -    | 159  | -    | (2025 only)                     |
| equity/trades    | -    | -    | -    | -    | -    | 159  | -    | (2025 only)                     |

NYSE = a **stable ~155–159 large-cap S&P universe** from 2023; ohlcv_1m is the through-line, tbbo/trades are 2025-only and
ABSENT 2026.

---

## ICE

| data_type        | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Universe (inside bundle)              |
| ---------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ------------------------------------- |
| future/ohlcv_1m  | 1    | 1    | 1    | 1    | 1    | 1    | -    | Brent (`BRN …`) — 148K rows in 1 file |
| future/tbbo      | -    | -    | -    | -    | -    | 1    | -    | 2025 only                             |
| future/trades    | -    | -    | -    | -    | -    | 1    | -    | 2025 only                             |

ICE = **Brent crude (BRN) futures only**, the whole chain bundled into one `ticks.parquet` (148,028 rows in 2025 — real).
ABSENT in the 2026 sample.

---

## FX (DEGENERATE — see Findings)

| data_type           | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Universe       |
| ------------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | -------------- |
| spot_pair/ohlcv_24h | 1    | 1    | 1    | 1    | 1    | 1    | -    | `KRW-USD`, 1–2 rows |

FX is a **single `ticks.parquet` with 1–2 rows, symbol KRW-USD only**, every year. This is effectively an empty/token FX
universe — a real gap (below). ABSENT in 2026.

---

# Findings

### 1. Universe-churn story (the headline)
- **CME futures roll cleanly and visibly**: ES front contracts march ESM0/U0/Z0 (2020) → ESM6/U6/Z6 (2026), one year per
  sample, with the spot-June expiry rolling to next-March in years sampled at/near expiry (ESH+1). Expiry dates in
  `instrument_id` (`ES-20200619` → `ES-20260619`) confirm. The contract roll lives INSIDE the chain parquet `symbol`
  column, NOT in the path — path-level audits of CME chains undercount and must read the file.
- **Asset-class onboarding waves**: 2020–2021 = CME + FX + ICE only. **2022** adds CME crypto futures (BTC/ETH + micros
  MBT/MET). **2023** is the big bang: NYSE (~158) + NASDAQ (~41) equities onboard. **2025** adds tbbo + tick `trades`
  depth on equities. Equity universes themselves are STABLE large-cap baskets (~159 NYSE / ~43 NASDAQ) once present.

### 2. CME-futures-data presence — **VERDICT: PRESENT and REAL across all years 2020–2025.**
CME is the dominant venue (557/1169 parquets in 2025). futures_chain, options_chain, per-strike `future/trades` (~503
files/day) and `combo` all carry genuine data every year. Spot-checked: ES chain 2025 = 2603 rows, close 5928–6132, vol
1.83M (correct ES level for Jun-2025); ICE Brent 2025 = 148K rows. The recent CME-via-Massive-S3-flat-file fix is NOT
contradicted by history — CME futures coverage is solid 2020→2025. **Caveat: 2026 CME coverage is THINNER** (5 chain
underlyings, only 1 `future/trades` ES file vs ~503 historically) — see #4.

### 3. FX is a near-empty gap (anomaly P1)
FX `spot_pair/ohlcv_24h` is a single 1–2 row `ticks.parquet` containing ONLY `KRW-USD`, every year 2020–2025. No EUR/USD,
GBP/USD, JPY, etc. The TradFi FX universe is effectively unpopulated — investigate whether this is intended (TradFi FX is
n/a for the MVP archetypes per the coverage matrix) or a silently-broken adapter.

### 4. 2026 is mid-rollout / partial (anomaly P1)
2026 daily parquet counts are a fraction of 2025 (242 vs 1169 on the richest day; most 2026 days = 0). The 2026 universe
is a DIFFERENT partial set (CME chains add CL/GC/NQ but drop the crypto micros; equity tbbo/trades, ICE, FX all absent).
Recent 2026 writes use the canonical `pipeline_mode=batch_databento/asset_group=` shape (`day=2026-06-05` = VIX only),
confirming TradFi 2026 ingestion is in progress, not a backfilled steady state.

### 5. Dual-leaf / partial-migration footprint (anomaly P2)
2020–2025 days carry the SAME venue's shards under BOTH `category=tradfi/` (bulk) and `asset_group=tradfi/` (a ~40–56-file
slice) — e.g. 2025-06-13 CME splits 51 `asset_group` + 506 `category`. An audit (and any consumer) that reads only one
leaf will undercount. 2026 is clean (`asset_group` only). The pre-migration `--apply` will need to reconcile/dedupe these
dual-written cells; the phantom-audit `prefix_tpls` MUST cover both legacy `category=` AND the no-`pipeline_mode=` old
`asset_group=` shape before any `--apply` (per the CLAUDE.md phantom-audit caveat) or it risks flipping real `captured`
rows to `attempted_failed`.

### 6. `_migrated_…` suffixed stems (informational)
2024 (and some 2020–2022) files carry stems like `AAPL_migrated_20260419T065848Z`, `ticks_migrated_…` from the
2026-04-19 migration pass — a partial in-place rename. Mostly cosmetic for this universe audit (the symbol root is
recoverable) but confirms historical days were touched by a prior migration and are not byte-stable.

### 7. The 2023-06-15 5663-parquet spike (informational)
2023 is ~10× any other year on this day, driven by equities onboarding (NYSE 158 + NASDAQ 41) PLUS a CME
`future/ohlcv_1m` per-strike explosion (504 individual option-on-future files that day vs the bundled single file other
years). Not an error — an inconsistency in how option-on-future strikes were materialised (per-file vs bundled) across
years; worth normalising.

---

## Anomalies for the operator (ranked)

1. **FX universe is degenerate** — KRW-USD only, 1–2 rows/day, all years. Confirm intended vs broken adapter. (P1)
2. **2026 TradFi ingestion is partial/mid-rollout** — most days empty; richest day 242 vs 1169 in 2025; CME 2026 thinner
   (1 `future/trades` file vs ~503). Confirm backfill is in flight before treating 2026 as covered. (P1)
3. **Dual-leaf (`category=` + `asset_group=`) on 2020–2025 days** — pre-migration `--apply` must dedupe; ensure
   phantom-audit `prefix_tpls` cover both old shapes before `--apply`. (P2)
4. **Equity tbbo/trades depth is 2025-only** — present 2025, absent 2023/2024/2026. Confirm whether back/forward-fill is
   expected. (P2)
5. **CME option-on-future strikes materialised per-file in 2023 but bundled other years** — normalise. (P3)

**CME-futures-data verdict for the operator: PRESENT and REAL for 2020–2025 (chains + per-strike + combo, spot-verified);
2026 is thin/in-progress.**
