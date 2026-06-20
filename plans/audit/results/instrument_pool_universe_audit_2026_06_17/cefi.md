# CeFi Instrument-Pool Universe Audit — what we ACTUALLY have

**Created:** 2026-06-17
**Author:** data-audit agent (READ-ONLY GCS sampling; no writes to prod data)
**Source bucket:** `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/`
**Scope:** the captured CeFi instrument set per `(venue, data_type)` shard, sampled **one representative day per
year** across coverage. Counts are **distinct instruments** (unique parquet stems / `underlying=` keys, deduped across
the coexisting legacy-`asset_group=` and canonical-`pipeline_mode=batch_*/asset_group=` path forms).

> **Method note.** For each sample day I listed the whole `day=` partition recursively ONCE (`gcloud storage ls
> --recursive`, ≤2.5k objects/day, ~0.6 s) and parsed `venue=` / `data_type=` / `instrument_type=` / symbol in a single
> pass. The symbol is the parquet stem, EXCEPT (a) where a shard carries an `underlying=X/` partition the symbol is `X`,
> and (b) KRAKEN-SPOT splits the symbol across an unkeyed `BASE/QUOTE.parquet` sub-dir — reconstructed as `BASE-QUOTE`
> (see Anomaly A4). `processed_candles/` (ohlcv) is OUT of scope; this is the raw-tick universe only.

## Coverage envelope (discovered, not assumed)

- **First data day:** `2019-03-30` (DERIBIT-only Tardis). **Last data day:** `2026-05-24`. 2622 `day=` partitions.
- **Sample days used** (mid-June per year, nudged off weekends; 2026 has no mid-June data so the latest **full** day
  near the tail was used):
  `2019-06-17`, `2020-06-15`, `2021-06-15`, `2022-06-15`, `2023-06-15`, `2024-06-17`, `2025-06-16`, `2026-05-15`.

---

## FINDINGS (read this first)

### Universe-evolution story (healthy core, sensible growth)

The captured universe **grows monotonically and sensibly** from a 1-venue / 3-row seed in mid-2019 to a 13-to-17-venue,
~2.4k-object/day corpus by mid-2025, then **contracts sharply in the 2026 tail**:

| Year (sample)  | Venues present | Total parquet objects/day | Headline                                                       |
| -------------- | -------------- | ------------------------- | -------------------------------------------------------------- |
| 2019-06-17     | 1 (DERIBIT)    | 6                         | Tardis genesis; DERIBIT BTC/ETH only                           |
| 2020-06-15     | 11             | 529                       | Tardis multi-venue onboard (Binance/Bybit/OKX/Kraken/Bitfinex) |
| 2021-06-15     | 13             | 966                       | UPBIT + OKX-SWAP book/ticker fill in; alt expansion            |
| 2022-06-15     | 13             | 1162                      | Peak breadth-per-symbol on majors                              |
| 2023-06-15     | 13             | 1067                      | DERIBIT options begin (book=21); Kraken-Spot universe widens   |
| 2024-06-17     | 14             | 2223                      | **HYPERLIQUID** joins; DERIBIT options explode (trades=441)    |
| 2025-06-16     | 15             | 2436                      | **BITGET-FUTURES/SPOT** join; OKX-Spot widest (94)             |
| 2026-05-15     | 13             | 479                       | **Sharp contraction** — see Anomaly A1                         |

Symbol formats evolve correctly per venue and are internally consistent: Binance `BTCUSDT`, Bitfinex futures
`BTCF0:USTF0`, Coinbase/OKX/Kraken-spot `BTC-USD`, OKX swap `BTC-USDT-SWAP`, OKX dated futures `BTC-USD-250620`, Bybit
dated futures `BTC-26DEC25`, Kraken futures `PI_XBTUSD` (note: `XBT` not `BTC`), UPBIT `KRW-BTC` / `USDT-BTC`,
HYPERLIQUID `BTC-PERP`, DERIBIT perps `BTC-PERPETUAL` + USDC-margined `BTC_USDC-PERPETUAL` + options
`XRP_USDC-16JUN25-1D85-C`. No symbol-format drift WITHIN a venue across years. The captured set is **real and evolves
sensibly** for the established venues.

### Top anomalies / gaps worth the operator's eye

- **A1 — 2026 tail is a DEGRADED / partial period, NOT steady-state (HIGHEST PRIORITY).** The 2026-05-15 sample shows
  the universe collapsed: BINANCE-FUTURES book_snapshot_5 = **4** (was 33 in 2025), BYBIT trades = **9** (was 42),
  OKX-SPOT trades = **21** (was 94), OKX-SWAP trades = **9** (was 40), DERIBIT trades = **2** (was 291 — all options
  gone). **OKX-FUTURES, HYPERLIQUID are entirely ABSENT on 2026-05-15.** This is a per-day collapse, not a clean
  shutdown: cross-checking other 2026 days, `2026-01-15`/`2026-03-15` still carry 16-17 venues INCLUDING two NEW venues
  (`LIGHTER-ZKSYNC`, `PACIFICA-SOLANA`), but by `2026-05-10`+ the corpus is back down to 13 venues with shrunken
  per-venue universes. So the captured universe **peaks ~early-2026 then degrades through the final weeks of coverage**.
  Before the migration `--apply`, the operator should decide whether 2026-05 is genuinely the live universe or an
  artifact of a tapering/incomplete backfill — applying a manifest reconcile against this thinned tail risks marking
  recently-captured majors as missing.

- **A2 — `perp_funding` is NEVER captured as its own data_type (corpus-wide).** The only data_types present in
  `raw_tick_data` are `trades`, `book_snapshot_5`, `derivative_ticker`, `liquidations`, and a single stray
  `options_chain`. `venue_data_types.yaml` lists `perp_funding`, but funding is carried INSIDE `derivative_ticker` (the
  Tardis convention), so a phantom-audit/denominator that expects a standalone `perp_funding` shard per perp venue will
  see 100% "missing". Confirm the manifest does not enumerate `perp_funding` as an expected shard for CeFi.

- **A3 — Two new perp-DEX venues appear ONLY as `ohlcv_1m` inside raw_tick_data, and only mid-coverage.**
  `LIGHTER-ZKSYNC` and `PACIFICA-SOLANA` (present `2025-12`→`2026-03`, absent from the yaml venue list and from my
  mid-year samples) carry NO `trades`/`book_snapshot_5`/`derivative_ticker` — only `ohlcv_1m` parquets, which is a
  PROCESSED-candle data_type that should live under `processed_candles/`, not `raw_tick_data/`. This is a
  layout/data_type-placement bug for these two venues.

- **A4 — KRAKEN-SPOT shard has a structural path defect (symbol split across an unkeyed sub-dir).** Files land at
  `.../data_type=book_snapshot_5/ADA/USD.parquet` — i.e. an extra `BASE/` directory with no hive key between
  `data_type=` and the file. A naive stem-based reader counts the universe as **1 instrument ("USD")**; the true
  universe is 12-24 `BASE-USD` pairs (corrected in the tables below). This is the only venue with this defect (DERIBIT's
  3-deep nesting is the legitimate `underlying=` futures_chain key). Any consumer/migration that keys on the file stem
  will badly mis-count KRAKEN-SPOT — fix the writer path or special-case the reader before `--apply`.

- **A5 — `ASTER` is entirely ABSENT from the captured CeFi corpus.** Listed in `venue_data_types.yaml` but no shard
  exists on ANY sampled day (incl. recent 2026 days). Either never onboarded or its data lives elsewhere — a real gap
  vs the declared venue set.

- **A6 — Junk/placeholder symbols leak into the universe (minor but pollutes counts).** A bare `ticks.parquet` (stem
  `ticks`) appears where a shard has no real per-instrument split (DERIBIT trades 2021-2023; HYPERLIQUID trades every
  year shows exactly **1** "ticks"; BYBIT options_chain 2024). A `_unknown_.parquet` appears in 2019-06-17 DERIBIT
  derivative_ticker. And DERIBIT trades double-counts a coarse `BTC`/`ETH` underlying alongside `BTC-PERPETUAL` (the 7
  vs the real perps in 2023). These are honest-absence/placeholder artifacts, not tradeable instruments.

- **A7 — Stray loose parquets at the `by_date/` root (outside any `day=` partition).** Nine files sit directly under
  `raw_tick_data/by_date/` (e.g. `AVAXUSDT.parquet`, `BTC-28MAR25.parquet`, `BTC-PERPETUAL.parquet`, `SOL-ETH.parquet`,
  `KRW-LINK.parquet`) — un-partitioned orphans that no `day=`-keyed reader will ever see. Candidate cleanup before
  migration.

- **A8 — Dual-write path coexistence (expected, but note for `--apply`).** Both the legacy `asset_group=cefi/` form and
  the canonical `pipeline_mode=batch_tardis/asset_group=cefi/` (also `pipeline_mode=batch_hyperliquid/`) coexist on the
  SAME days (2020+) and are byte-duplicate. My counts dedupe across them. The phantom-audit `prefix_tpls` MUST cover
  both forms (per the CLAUDE.md Axis-10 warning) or `--apply` will flip real `captured` rows to `attempted_failed`.

---

## Per-venue universe tables

Cell = **distinct-instrument count** for that `(venue, data_type)` on that year's sample day. `—` = shard absent that
year (pre-genesis or not captured). A representative ~10-symbol sample follows each venue. `pre` = before venue genesis.

### BINANCE-FUTURES (perpetual)

| data_type         | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| ----------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades            | —    | 9    | 17   | 18   | 20   | 33   | 34   | 9    |
| book_snapshot_5   | —    | 9    | 17   | 18   | 20   | 32   | 33   | 4    |
| derivative_ticker | —    | 9    | 17   | 18   | 20   | 32   | 33   | 9    |
| liquidations      | —    | 9    | 17   | 18   | 20   | 32   | 32   | 9    |

Sample (2025): `ADAUSDC, ADAUSDT, APTUSDT, ARBUSDC, ARBUSDT, ATOMUSDT, AVAXUSDC, AVAXUSDT, BNBUSDC, BNBUSDT`.

### BINANCE-SPOT

| data_type       | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades          | —    | 16   | 29   | 31   | 29   | 47   | 43   | 20   |
| book_snapshot_5 | —    | 16   | 29   | 31   | 28   | 47   | 43   | 20   |

Sample (2024): `ADAUSDC, ADAUSDT, APTUSDC, APTUSDT, ARBUSDC, ARBUSDT, ATOMUSDC, ATOMUSDT, AVAXUSDC, AVAXUSDT`.

### BITFINEX-FUTURES (perpetual)

| data_type         | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| ----------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades            | —    | 2    | 4    | 8    | 8    | 8    | 8    | 8    |
| book_snapshot_5   | —    | 2    | 4    | 8    | 8    | 8    | 8    | 8    |
| derivative_ticker | —    | 2    | 4    | 8    | 8    | 8    | 8    | 8    |
| liquidations      | —    | 2    | 3    | 6    | 2    | 5    | 6    | 5    |

Sample: `ADAF0:USTF0, AVAXF0:USTF0, BTCF0:USTF0, DOGEF0:USTF0, ETHF0:USTF0, LINKF0:USTF0, SOLF0:USTF0, XRPF0:USTF0`.

### BITFINEX-SPOT

| data_type       | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades          | —    | 11   | 16   | 16   | 16   | 16   | 16   | —    |
| book_snapshot_5 | —    | 11   | 16   | 16   | 16   | 16   | 16   | —    |

Sample (2022): `ADAUSD, ATOUSD, BTCUSD, DOTUSD, ETCUSD, ETHUSD, FILUSD, LTCUSD, NEOUSD, SOLUSD`. (Absent on the
2026-05-15 sample day — see A1; present on other 2026 days.)

### BITGET-FUTURES (perpetual) — genesis ~2024-11

| data_type         | 2019-2024 | 2025 | 2026 |
| ----------------- | --------- | ---- | ---- |
| trades            | pre       | 24   | 24   |
| book_snapshot_5   | pre       | 24   | 22   |
| derivative_ticker | pre       | 24   | 24   |
| liquidations      | pre       | —    | 24   |

Sample: `ADAUSDT, APTUSDT, ARBUSDT, ATOMUSDT, AVAXUSDT, BCHUSDT, BNBUSDT, BTCUSDT, DOGEUSDT, DOTUSDT`.

### BITGET-SPOT — genesis ~2024-11

| data_type       | 2019-2024 | 2025 | 2026 |
| --------------- | --------- | ---- | ---- |
| trades          | pre       | 24   | 24   |
| book_snapshot_5 | pre       | 24   | 24   |

Sample: same 24-symbol majors as BITGET-FUTURES.

### BYBIT

| data_type         | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| ----------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades            | —    | 4    | 12   | 24   | 27   | 27   | 42   | 9    |
| book_snapshot_5   | —    | 4    | 12   | 24   | 26   | 9    | 38   | 6    |
| derivative_ticker | —    | 4    | 12   | 24   | 27   | 9    | 38   | 9    |
| liquidations      | —    | —    | 12   | 24   | 25   | 9    | 31   | 9    |

Sample (2025, mixed spot+perp+dated): `BTC-26DEC25, BTC-27JUN25, ETH-26DEC25, ADAUSD, ADAUSDT, APTUSDT, ARBUSDT,
ATOMUSDT, AVAXUSD, BNBUSDT`. Note the book/ticker dip in 2024 (9) vs trades (27) — uneven per-data_type coverage.

### COINBASE-SPOT

| data_type       | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades          | —    | 16   | 30   | 47   | 49   | 51   | 51   | 19   |
| book_snapshot_5 | —    | 3    | 6    | 9    | 17   | 15   | 17   | 17   |

Sample (2024 trades): `ADA-BTC, ADA-ETH, ADA-USD, ADA-USDT, APT-USD, APT-USDT, ARB-USD, ATOM-BTC, ATOM-USD, ATOM-USDT`.
Note book_snapshot_5 has always been a much narrower universe than trades here.

### DERIBIT (perpetual + futures_chain + options)

| data_type         | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| ----------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades            | 1    | 2    | 3\* | 3\* | 7\* | 441  | 291  | 2    |
| book_snapshot_5   | —    | 2    | 2    | 2    | 21   | 2    | 27   | 2    |
| derivative_ticker | 4\* | 2    | 2    | 2    | 2    | —    | 2    | 2    |
| liquidations      | 1    | —    | —    | —    | —    | —    | —    | —    |

`*` includes junk/coarse symbols (`ticks`, bare `BTC`/`ETH`, `_unknown_` in 2019 — Anomaly A6). The 2024/2025 trades
explosion (441/291) is the **options chain** (`MATIC_USDC-17JUN24-0D52-C` …) landing in `trades`. Sample (2025):
`BTC-PERPETUAL, ETH-PERPETUAL, BTC_USDC-PERPETUAL, BTC_USDT-PERPETUAL, XRP_USDC-16JUN25-1D85-C, …`. DERIBIT is the most
structurally heterogeneous venue (perp + USDC/USDT-margined perp + dated futures + options all interleaved).

### HYPERLIQUID (perpetual) — genesis ~2024 (own `pipeline_mode=batch_hyperliquid`)

| data_type         | 2019-2023 | 2024 | 2025 | 2026 |
| ----------------- | --------- | ---- | ---- | ---- |
| trades            | pre       | 1\*  | 1\*  | —    |
| book_snapshot_5   | pre       | 9    | 9    | —    |
| derivative_ticker | pre       | 17   | 19   | —    |

`*` trades is a single placeholder `ticks` file (A6) — HYPERLIQUID trades are NOT split per-instrument. book/ticker
carry the real `*-PERP` universe: `ADA-PERP, APT-PERP, ATOM-PERP, AVAX-PERP, BNB-PERP, BTC-PERP, CAKE-PERP, DOGE-PERP,
ETH-PERP, FIL-PERP`. Absent on the 2026-05-15 sample day (A1).

### KRAKEN-FUTURES (perpetual)

| data_type         | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| ----------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades            | —    | 3    | 3    | 3    | 3    | 3    | 3    | 2    |
| book_snapshot_5   | —    | 3    | 3    | 3    | 3    | 3    | 3    | 3    |
| derivative_ticker | —    | 3    | 3    | 3    | 6    | 3    | 5    | 3    |
| liquidations      | —    | 3    | 3    | 3    | 3    | 2    | 3    | —    |

Sample: `PI_ETHUSD, PI_XBTUSD, PI_XRPUSD` (+ `PF_USDTUSD, PI_BCHUSD, PI_LTCUSD` in widest years). Notably **flat/narrow**
(2-6) across all 7 years — a small, stable Kraken perp universe.

### KRAKEN-SPOT — counts CORRECTED for the path defect (A4)

| data_type       | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades          | —    | 12   | 15   | 18   | 22   | 24   | 24   | 24   |
| book_snapshot_5 | —    | 12   | 11   | 17   | 22   | 12   | 15   | 18   |

Sample (2025): `ADA-USD, AVAX-USD, DOT-USD, INJ-USD, LINK-USD, LTC-USD, NEAR-USD, SOL-USD, SUI-USD, TIA-USD` (Kraken
uses `XBT-USD`/`XDG-USD` for BTC/DOGE in some years). **A naive stem reader would show "1" here — do not trust raw stem
counts for this venue.**

### OKX-FUTURES (dated futures)

| data_type | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades    | —    | 40   | 64   | 72   | 44   | 45   | 26   | —    |

Sample (2025): `BTC-USD-250620, BTC-USD-250627, BTC-USD-250725, BTC-USD-260327, BTC-USDC-250627, BTC-USDT-250620, …`.
Dated-future universe naturally varies with the listed-expiry calendar. **Absent on 2026-05-15** (A1) — and the only
data_type OKX-FUTURES ever captured is `trades` (no book/ticker).

### OKX-SPOT

| data_type       | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades          | —    | 40   | 63   | 71   | 81   | 88   | 94   | 21   |
| book_snapshot_5 | —    | —    | 15   | 14   | 20   | 18   | 9    | 21   |

Sample (2025 trades): `ADA-USD, ADA-USDC, ADA-USDT, APT-USD, APT-USDC, APT-USDT, ARB-USD, ARB-USDC, ARB-USDT, ATOM-USD`.
Widest spot universe in the corpus (94 in 2025).

### OKX-SWAP (perpetual swap)

| data_type         | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| ----------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades            | —    | 16   | 28   | 31   | 38   | 40   | 40   | 9    |
| book_snapshot_5   | —    | —    | 8    | —    | 9    | —    | —    | 5    |
| derivative_ticker | —    | —    | 8    | 8    | 9    | 9    | 9    | 9    |
| liquidations      | —    | —    | 7    | 8    | 9    | 9    | 9    | 9    |

Sample: `ADA-USDT-SWAP, AVAX-USDT-SWAP, BNB-USDT-SWAP, BTC-USDT-SWAP, DOGE-USDT-SWAP, ETH-USDT-SWAP, LINK-USDT-SWAP,
SOL-USDT-SWAP, XRP-USDT-SWAP`. Note book_snapshot_5 is intermittent year-over-year (present 2021/2023/2026, absent
2020/2022/2024/2025) — uneven book coverage.

### UPBIT (Korean spot)

| data_type       | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --------------- | ---- | ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| trades          | —    | —    | 16   | 21   | 16   | 23   | 28   | 19   |
| book_snapshot_5 | —    | —    | 16   | 21   | 16   | 23   | 29   | 19   |

Sample (2025): `USDT-ADA, USDT-BTC, USDT-DOGE, USDT-ETH, USDT-NEAR, USDT-PEPE, USDT-SOL, USDT-TRX, USDT-UNI, USDT-USDC`
(+ `KRW-*` pairs). UPBIT first captured 2021.

### ASTER — declared in `venue_data_types.yaml`, **NOT FOUND** anywhere (A5)

| data_type | all years |
| --------- | --------- |
| (all)     | absent    |

### LIGHTER-ZKSYNC / PACIFICA-SOLANA — present 2025-12 → 2026-03 only, `ohlcv_1m` only (A3)

Not on the mid-year sample days; surfaced via spot-checks of `2026-01-15`. Carry only `ohlcv_1m` parquets in
`raw_tick_data` (a processed-candle data_type in the wrong layer), no tick-level shards.

---

## Empty-vs-populated summary (by sample-day)

- **Always populated (every captured year, every core data_type):** BINANCE-FUTURES, BINANCE-SPOT, BITFINEX-FUTURES,
  COINBASE-SPOT, DERIBIT, KRAKEN-FUTURES, KRAKEN-SPOT, OKX-SPOT (from 2020), OKX-SWAP/UPBIT (from 2021).
- **Genesis-gated (legitimately empty before onboarding):** UPBIT (2021+), HYPERLIQUID (2024+),
  BITGET-FUTURES/SPOT (~2024-11+).
- **Empty where you might expect data (real gaps/anomalies):** `perp_funding` everywhere (A2); ASTER everywhere (A5);
  DERIBIT `liquidations` only ever in 2019; OKX-FUTURES/HYPERLIQUID/BITFINEX-SPOT absent on the 2026-05-15 sample day
  (A1 tail degradation, present on other 2026 days); OKX-SWAP book_snapshot_5 intermittent.
- **Suspicious "1-instrument" shards (placeholder, not real universe):** HYPERLIQUID trades (`ticks`), BYBIT
  options_chain 2024 (`ticks`), DERIBIT 2019 trades/liquidations. KRAKEN-SPOT's apparent "1" is a PARSER artifact, not
  real (A4) — true universe is 12-24.

## Recommended operator actions before migration `--apply`

1. **Resolve the 2026 tail (A1)** — decide whether 2026-05 is the live universe or a tapering backfill; do not let the
   reconcile mark thinned-but-recently-captured majors as missing.
2. **Confirm `perp_funding` (A2) is not an enumerated expected shard** for CeFi (funding lives in `derivative_ticker`).
3. **Fix or special-case KRAKEN-SPOT path (A4)** so the migration counts `BASE-USD` pairs, not the `USD` stem.
4. **Verify phantom-audit `prefix_tpls` cover BOTH the legacy `asset_group=` and `pipeline_mode=batch_*` forms (A8)**
   before any `--apply`, per the Axis-10 false-positive warning.
5. **Relocate or drop the `ohlcv_1m`-only DEX venues (A3)** and clean the `by_date/` root orphans (A7).
