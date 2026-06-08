---
title:
  SYSTEMIC bar-edge violation — pre-aggregated vendor-bar ingestion stamps the OPEN (left) edge while the canon + MDPS
  grid are CLOSE (right) edge
created: 2026-06-08
source:
  - plans/audit/results/tradfi_massive_migration_audit_2026_06_08.md (§ Cross-cutting bar-edge convention audit)
  - 3-repo read-only sweep 2026-06-08 (instruments-service / market-tick-data-service / market-data-processing-service +
    features-service + scripts)
locked_by: live-defi-rollout
supersedes:
  plans/active/issues/hyperliquid_ohlcv_left_edge_timestamp_2026_06_08.md (that bug is one instance of this class)
priority: P2
status: active
---

# Systemic bar-edge (open vs close) violation across pre-aggregated OHLCV ingestion

> **🔴 SCOPED 2026-06-08 (operator) → remediation wrapper `bar_edge_left_vs_right_remediation_2026_06_08.md`** (parent
> `mtds_mdps_master`, vm-cross-cutting, P0). This doc remains the SURFACING + site register; the actionable phases
> (gate-close → fix latent ingestion → purge left-edge `features-*` corpus) live in the wrapper. **Blocking scope
> (precise): the FEATURE LAYER** (closed-candle-on-the-left = look-ahead leakage) until the gate catches edge errors +
> the pre-fix corpus is recomputed — it does NOT block the raw/manifest `--apply` (the MDPS processed candle store is
> data-verified right-edge). This issue archives once the wrapper's phases are acked into execution.

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
- **✅ FIXED 2026-06-08 (features-service@7a4fafd9, QG green) — features-service re-resamplers (the only realized live
  bugs).** Both shipped right-edge: `candle_resampler.resample_ohlcv` → `closed="right", label="right"`;
  `flow_interaction` → bar stamped `truncate("1m") + 1m` (close). Regression guards added
  (`test_resample_right_edge_close_labels` asserts `00:05:00/00:10:00` labels + correct grouping; right-edge assertion
  in `test_flow_interaction_basic_cvd`); test inputs corrected to the real right-edge convention; `test_1m_to_1h_ratio`
  origin fixed. **⚠️ FOLLOW-UP (open): existing `features-*` parquets computed BEFORE this fix carry the old left-edge
  timestamps** — the fix only corrects NEW computes. A feature recompute over the affected history is required to purge
  the left-edge corpus (scope = every coarser-than-base delta_one tf + cross_instrument `flow_interaction` outputs).
  Tracked here; size + sequencing TBD (recompute vs let-it-roll-forward) — operator/Ikenna call. Original evidence (ran
  both functions on a synthetic RIGHT-edge 1m series, features-service venv polars 1.40):
  - `candle_resampler.resample_ohlcv(1m→5m)` → output stamped `00:00:00 / 00:05:00 / 00:10:00` (LEFT labels) **and
    miscomposed**: the "5-minute bar" at `00:00:00` contains only minutes 1–4 (close=104, vol=10) instead of the correct
    `00:05:00` bar over minutes 1–5 (close=105, vol=15). So `closed="left", label="left"` both **mislabels (open edge)
    and splits the window** — a real corruption of every coarser-than-base feature timeframe. Feeds features via
    `_tf_cluster_helper.py`. Fix → `closed="right", label="right"`.
  - `flow_interaction` `dt.truncate("1m")` → a trade at `00:00:30` lands in bar `00:00:00` (open), vs canonical
    `00:01:00` (close) — 1-minute-early CVD/imbalance features. Fix → stamp `truncate + 1m` (or
    `compute_bar_close_boundary`). Both **bypass the MDPS gate** (in-memory, downstream of the right-edge candle store)
    → they take CORRECT data and degrade it. **These are the actionable bugs.**
- **bypass-MDPS direct-`write_chunk` candle fetchers — RESOLVED as LATENT (data-checked, not realized in prod).** On the
  overlapping day 2026-05-21 (defi raw 2020→2026-05-28 vs processed 2024→2026-05-22 — wide overlap; my earlier
  "disjoint" was just the tails): (1) the only DeFi processed candle type is `dex_swaps`, built from individual swap
  **events** (UNISWAP_V3 raw `timestamp` = Unix **seconds, per-swap, irregular** — trade-time, not bar edges) → MDPS
  tick-aggregates to the verified right-edge candle; (2) **no perp venues (hyperliquid/pacifica/lighter) exist in defi
  raw** on 2026-05-26/27/28 — the pre-aggregated candle fetchers with the `t`/`periodStartUnix` open-edge code are **not
  writing to prod**, and uniswap's hourly `periodStartUnix` path does not feed the consumed `dex_swaps` candle. So their
  open-edge bug is a **latent code bug** (would matter only if those sources activate and their pre-agg output is
  consumed as candles), **NOT a current data corruption.** Instruments-service reference-data (hyperliquid/aster/ccxt/
  polygon) is reference/universe data, not the candle store. Fix the code for correctness-in-depth, but no prod
  candle-store corruption exists today.

> **Net (post a+b data verification):** the MDPS processed candle store is right-edge CORRECT everywhere verified
> (tradfi databento ohlcv, defi dex_swaps). The **only realized bugs are the two features-service re-resamplers** — both
> reproduced by running the real code — which corrupt correct right-edge candles into left-edge downstream of the gate.
> Everything else (raw open-edge artifacts, instruments-service refdata, inactive pre-agg fetchers) is by-design or
> latent, not a live data-correctness incident.
>
> **STATUS 2026-06-08:** the two features-service calculators (the only realized bugs) are **FIXED**
> (features-service@7a4fafd9, QG green; awaiting staging-unlock to promote — see below). REMAINING: (1) recompute the
> pre-fix left-edge `features-*` corpus; (2) optional correctness-in-depth fixes for the latent pre-agg fetchers +
> instruments-service refdata so they can't bite if activated. Neither is a live incident.

## Shipping status

- **features-service@7a4fafd9** on `live-defi-rollout` (QG exit 0). Promotion to staging→main is **pending the staging
  lock** (`workspace-manifest.json.staging_status` — execution-service breaking-bump cascade, unrelated); it joins the
  committed-LDR backlog that drains via the staging→main automation / a per-repo staging PR when the lock clears.

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
