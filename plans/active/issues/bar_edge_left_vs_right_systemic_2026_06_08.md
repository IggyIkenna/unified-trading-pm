---
title:
  SYSTEMIC bar-edge violation — pre-aggregated vendor-bar ingestion stamps the OPEN (left) edge while the canon + MDPS
  grid are CLOSE (right) edge
created: 2026-06-08
author: harsh
source:
  - plans/audit/results/tradfi_massive_migration_audit_2026_06_08.md (§ Cross-cutting bar-edge convention audit)
  - 3-repo read-only sweep 2026-06-08 (instruments-service / market-tick-data-service / market-data-processing-service +
    features-service + scripts)
locked_by: live-defi-rollout
supersedes:
  plans/active/issues/hyperliquid_ohlcv_left_edge_timestamp_2026_06_08.md (that bug is one instance of this class)
---

# Systemic bar-edge (open vs close) violation across pre-aggregated OHLCV ingestion

## What I found

Canonical OHLCV bar timestamp = **RIGHT edge `t_close`** (UAC `bar_boundary.py` `bar_window_for_close`; UTL
`compute_bar_close_boundary(ts, timeframe)`). A deep 3-repo sweep (operator-requested 2026-06-08, after the hyperliquid
single-instance bug) found this is **systematically violated wherever a PRE-AGGREGATED vendor bar is ingested** — the
code stamps the vendor's OPEN/start edge (or passes it through unconverted). The tick→candle aggregators are correct
(they build the bar and stamp `period_end`); the bug class is confined to **pre-aggregated bar ingestion**, but it is
broad and spans cefi/defi/tradfi and 3 repos + features-service.

### The root mechanism (why the MDPS gate does NOT save us)

1. The MDPS write-gate `assert_bar_boundary_contract` validates only: `t_close` is **grid-aligned** +
   `t_close − t_open == timeframe` + `available_at == t_close`. A **uniform one-interval left-shift on sub-daily bars
   stays on-grid** (a left-edge 1m stamp `10:00:00` is just as `%60==0` as the right-edge `10:01:00`), so the gate
   **passes it**. The gate enforces alignment, NOT which edge the bar represents. (This corrects the first audit's
   "gate-enforced → sound".)
2. MDPS `ohlcv_passthrough.py` (`market-data-processing-service/.../app/adapters/tradfi/ohlcv_passthrough.py:150-181`)
   builds a right-edge grid (`day_start + interval*(i+1)`) and maps source bars with
   `idx = (src_ts − day_start − 1)//interval`, **explicitly assuming the source timestamp is end-of-period (close)**
   (its own comment: "Source timestamp is end-of-period"). Feed it an **open-edge** source and every bar is placed **one
   interval early**, and the first (midnight-open) bar maps to `idx = −1` → **silently dropped**.

So: open-edge ingestion → (gate passes) → passthrough misplaces by one interval. Silent, on the heartbeat data path.

## DATA-STATE VERIFICATION (2026-06-08, read actual prod parquets) — REFRAMES the severity

Read raw + processed parquets from `gs://market-data-tick-{tradfi,defi}-prd-central-element-323112` to test the edge
against real data (not just code). **The headline correction: the CONSUMED candle store (`processed_candles/`) is
right-edge CORRECT — MDPS normalizes the open-edge raw. The open-edge problem is confined to the RAW artifact + paths
that BYPASS the processed layer.**

- **Databento RAW `data_type=ohlcv_1m` = OPEN-edge (CONFIRMED).** AAPL 2026-05-15: opening-auction volume spike (36,962)
  stamped `13:30:00` UTC (regular open), pre-market bars precede it; last regular volume at `19:59:00`. `timestamp`
  column = `ts_event` ns verbatim. So the raw corpus is open-edge, as the code/schema predicted.
- **Databento PROCESSED `processed_candles/timeframe=1m` = RIGHT-edge CORRECT (CONFIRMED).** ETHA 2026-01-21, same
  instrument, raw vs processed: | | opening auction (vol 447,598) | closing auction (vol 446,618) | | - | - | - | | RAW
  ohlcv_1m | `14:30:00` (open) | `21:00:00` | | PROCESSED 1m candle | `14:31:00` (close) | `21:01:00` | Processed = raw
  shifted **+1 interval** → MDPS correctly converts open→close `t_close`. Processed store is the canonical dense
  right-edge grid (1440 rows, `00:01:00 → 00:00:00`). **So the TradFi reference corpus is NOT corrupted for downstream
  consumers** — my earlier "reference corpus likely one-interval-early" was WRONG at the consumed layer (correct only
  about the raw artifact). This also means **Massive (also open-edge `t`) will be normalized the same way IF it routes
  through the same MDPS processed path** — the migration requirement is that Massive raw match Databento raw's
  representation, MDPS handles the edge.
- **DeFi PROCESSED candle = right-edge (CONFIRMED).** Balancer-Arbitrum dex_swaps 1m candle 2026-05-22: MDPS-built
  canonical schema (`timestamp/timestamp_out/available_at/ts_event`), minute-grid, tick-aggregated → right-edge.

### Revised severity (post-data)

- **Databento ohlcv raw open-edge** → **DOWNGRADED to ℹ️ by-design / not-a-downstream-bug** (MDPS converts; consumed
  candle verified right-edge). Keep only as a "raw representation is vendor-open-edge; never consume raw ohlcv directly
  — always the processed candle" note.
- **STILL 🔴 — features-service re-resamplers** (`candle_resampler.py:159` `closed/label="left"`;
  `flow_interaction.py:76` `dt.truncate("1m")`): these consume the CORRECT right-edge processed candles and **re-emit
  LEFT-edge**, bypassing the gate — they DEGRADE correct data. Highest live risk now; not data-verifiable without
  running, but code is unambiguous.
- **NEEDS PER-SOURCE DATA CHECK — bypass-MDPS direct-`write_chunk` candle fetchers** (pacifica/lighter/uniswap_v3 in
  MTDS; instruments-service reference-data hyperliquid/aster/ccxt/polygon): the question is whether their output is ever
  consumed RAW (open-edge) or always re-built by MDPS into a right-edge processed candle (as dex_swaps is). DeFi day
  ranges were disjoint (raw 05-26+, processed ≤05-22) + 24h crypto has no auction discriminator, so these are
  unverified-by-data this pass — flag for a targeted check on an overlapping day.

> **Net:** the systemic open-edge ingestion is real, but the MDPS processed layer is the safety net that DATA confirms
> works for the tradfi+defi candle store. The actionable bugs are the features-service re-resamplers (corrupt correct
> data) and any consumer that reads a raw/bypass artifact instead of the processed candle. The "reference corpus is
> wrong" alarm is RETRACTED at the consumed layer.

## The site register (verdicts with file:line)

### 🔴 HIGHEST — touches the TradFi reference corpus + live features path

| #   | site                                                                                                                                                       | edge stamped                                                                                                                                                                             | impact                                                                                                                                                                                                                                                                                                                                            | gate?                                |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| 1   | **Databento OHLCV** `market-tick-data-service/.../adapters/tradfi/databento_adapter.py` (`schema=db.Schema.OHLCV_1M`, `ts_event` preserved ~L528/673/1216) | OPEN — Databento OHLCV `ts_event` = interval **start** (documented). trades/tbbo `ts_event`=event-time = OK.                                                                             | The existing **Databento TradFi OHLCV corpus** (our "canonical reference" for Massive parity) is likely one-interval-early + midnight bar dropped via the passthrough above. **HIGH-confidence (code+schema); recommend a DATA-STATE confirmation before any fix** (compare a liquid instrument's bar to the known market print for that minute). | through MDPS (passthrough misaligns) |
| 2   | **features candle_resampler** `features-service/.../delta_one/app/core/candle_resampler.py:159`                                                            | `group_by_dynamic("timestamp", every, closed="left", label="left")` → resamples right-edge MDPS candles to **left-edge** coarse bars (docstring falsely claims byte-equivalence to MDPS) | LIVE on DeFi/features critical path; coarse-tf feature values misalign one bar vs natively-read MDPS files                                                                                                                                                                                                                                        | **BYPASSES gate** (in-memory)        |
| 3   | **features flow_interaction** `features-service/.../cross_instrument/app/calculators/flow_interaction.py:76,80`                                            | `dt.truncate("1m")` (floors to minute open) then renames `minute`→`timestamp`                                                                                                            | per-minute CVD/imbalance features stamped left-edge; PIT-join on `timestamp` vs right-edge candles off by one minute                                                                                                                                                                                                                              | **BYPASSES gate**                    |

### 🔴 instruments-service reference-data adapters (bypass MDPS gate entirely)

| site                       | edge                                                                          | note                                                                                 |
| -------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `cefi/hyperliquid.py:255`  | `t` (open), `T` ignored                                                       | the originally-filed instance ([[hyperliquid_ohlcv_left_edge_timestamp_2026_06_08]]) |
| `cefi/aster.py:375`        | Binance kline `[0]` (open); `[6]`=close ignored                               |                                                                                      |
| `cefi/ccxt_adapter.py:299` | `bar[0]` (open)                                                               | **high blast radius** — ccxt backs many CEX venues                                   |
| `tradfi/polygon.py:234`    | `bar.get("t")` (open)                                                         | polygon.io is a REMOVED TradFi provider, but the code path is wrong if exercised     |
| `cefi/tardis.py:856`       | 🟡 `timestamp` (Tardis trade_bar — likely CLOSE; never reads `openTimestamp`) | confirm against a live cassette; likely ✅                                           |

### 🔴 market-tick-data-service pre-aggregated candle ingestion

| site                                                       | edge                                                                  | write path                                                                     |
| ---------------------------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `umi_tick_provider.py:1115` `_fetch_pacifica_candles`      | `t` (open); `T` (close) available + ignored — exact hyperliquid shape | **direct `write_chunk` (bypass gate)**                                         |
| `umi_tick_provider.py:1945/1959` `_fetch_lighter_candles`  | `t` (open; UDF bar start)                                             | direct (bypass)                                                                |
| `market_interface/adapters/defi/uniswap_v3_adapter.py:714` | `periodStartUnix` (open)                                              | direct                                                                         |
| `tradfi/yahoo_finance_adapter.py:84-92`                    | DataFrame index (period start) for VIX `ohlcv_15m`                    | via umi → write_chunk                                                          |
| `tradfi/massive_tradfi_rest_connector.py:490`              | `t` (open)                                                            | (already in the Massive rebuild scope — `tradfi_massive_dual_source` Phase 4b) |
| 🟡 `cefi/ccxt_adapter.py:359`                              | `raw[0]` (open)                                                       | heartbeat-only today; latent if reused as a writer                             |
| ✅ `onchain_perps/extended_adapter.py:354` (`bar["T"]`)    | CLOSE                                                                 | the lone correct reference — proves the codebase knows `T` exists              |

### ⚪ cleanup (not a live bug)

- `market-data-processing-service/.../core/polars_candle_engine.py:138` `create_ohlcv_with_sides_polars` emits no
  `timestamp` column and has no live caller — dead code, flag for deletion.

### ✅ verified correct (no action)

MDPS tick→candle aggregator + grid + per-asset-group adapters (`base_adapter._create_interval_boundaries` =
`day_start + interval*(i+1)`) + `fast_candle_aggregation` (`closed="right", label="right"`) + `polars_candle_engine`
fill + the gate itself + the two 2026-05 reconcile scripts. The 2026-05-11 `available_at` double-add overshoot is fixed
and guarded.

## Why it matters

The bar-timestamp edge is a **cross-cutting correctness invariant** — every PIT join, every feature rolling window,
every cross-source/cross-timeframe merge assumes one consistent edge. Today right-edge (tick-aggregated + MDPS grid) and
open-edge (pre-aggregated ingestion) **co-exist silently**, off by one interval, and the gate does not catch it. The
Databento OHLCV case (#1) is the most consequential because it is the TradFi reference corpus that the Massive migration
is being matched against — and notably **Massive `t` is ALSO open-edge**, so the two TradFi vendors are at least
internally consistent with each other (both open), but both diverge from the canonical right-edge + from every
tick-aggregated source.

## Recommended decision

1. **Confirm #1 (Databento corpus) via data-state** before fixing — a wrong shift would corrupt the corpus; sample a
   liquid contract's bar vs the known market print for that minute.
2. **One canonical conversion at every pre-aggregated ingestion**: prefer the vendor's explicit close field where it
   exists (HL/Pacifica `T`, Binance kline `[6]`), else `compute_bar_close_boundary(open_ts, timeframe)` — never a
   hardcoded `+60s`. Fix the features resampler to `closed="right", label="right"` and `flow_interaction` to stamp the
   close edge.
3. **Close the gate's blind spot**: extend the bar-boundary QG check (`check_mdps_bar_boundary_compliance.py`) to
   reference-data + pre-aggregated ingestion adapters, and add a cross-source edge fixture (same instrument+window from
   a tick-aggregated and a pre-aggregated source must produce the SAME `t_close`). Consider an ingestion-time assertion
   that a vendor close field, when present, matches the stamped edge.
4. This is **cross-cutting (cefi/defi/tradfi, 4 repos)** — needs a remediation wrapper plan with `parent_epic:` +
   `assigned_vm:` once the operator scopes it; this issue doc is the surfacing. Owner pick: operator/Ikenna.

Composes with: UAC `bar_boundary.py` · the MDPS bar-boundary QG checks · `tradfi_massive_dual_source_2026_05_28.md`
Phase 4b (Massive #5 already requires interval-aware right-edge conversion).
