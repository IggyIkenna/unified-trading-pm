---
scope: [engineer]
---

# Bar-Boundary / Candle-Edge Convention — RIGHT edge (`t_close`) everywhere

Codified 2026-06-08 (plan:
[`bar_edge_left_vs_right_remediation_2026_06_08.md`](../../plans/active/bar_edge_left_vs_right_remediation_2026_06_08.md);
surfacing issue:
[`bar_edge_left_vs_right_systemic_2026_06_08.md`](../../plans/active/issues/bar_edge_left_vs_right_systemic_2026_06_08.md)).

## The invariant (HARD RULE)

**A CLOSED OHLCV/aggregate candle is timestamped on its RIGHT edge — its close time `t_close`** (the UAC
`bar_boundary.py` half-open window `[t_open, t_close)`; UTL `compute_bar_close_boundary(last_tick_ts, timeframe)`
returns `(t_open, t_close, available_at)`). Stamping the vendor's OPEN/left (bar-START) edge on a closed bar is
**look-ahead → leakage**: any feature / PIT-join / rolling window / cross-source merge keyed on that timestamp sees a
bar one interval before it actually closed.

- **Never consume raw `ohlcv` directly — always the MDPS processed candle.** Vendor raw `ohlcv` (Databento OHLCV,
  Massive `t`, Uniswap `periodStartUnix`, …) is OPEN-edge by representation; MDPS normalises it to the right edge in the
  processed candle store. Downstream reads the processed candle, not the raw artifact. (Data-state verified 2026-06-08:
  the MDPS `processed_candles/` store is right-edge correct; the open-edge lives only in the raw artifact + paths that
  bypass the processed layer.)
- **Conversion rule at any pre-aggregated ingestion**: prefer the vendor's explicit CLOSE field where it exists
  (Hyperliquid/Pacifica candle `T`, Binance kline index `[6]`); else `compute_bar_close_boundary(open_ts, timeframe)[1]`
  (`t_close`). **Never a hardcoded `+60s` / `+ interval`.**
- **Tick aggregators** stamp `period_end` (the grid close `day_start + interval*(i+1)`) — already right-edge; do not
  change them.

## Why the MDPS grid gate does NOT catch a left-edge bar

`assert_bar_boundary_contract` validates grid-alignment + interval width + `available_at`. A **uniform one-interval
left-shift stays on-grid** (a 1m open stamp `10:00:00` is just as `%60==0` as the close `10:01:00`), so the boundary
gate PASSES an open-edge bar. The gate enforces alignment, not which edge the bar represents — hence the dedicated edge
gates below.

## Enforcement

- **STEP 5.92 — `check_bar_edge_open_ingestion.py`** (`base-service.sh` + `base-library.sh`): AST, per-function; flags
  an ingestion/adapter function that consumes a vendor bar-START field (`periodStartUnix` / `openTimestamp` anywhere; a
  candle/ohlcv/kline-named function's `["t"]`/`.get("t")`) WITHOUT a close conversion (`compute_bar_close_boundary` /
  vendor close field / kline `[6]`). Baseline-ratchet (`bar_edge_open_ingestion_baseline.yaml`) — pre-existing latent
  sites are WARNINGS, a NEW open-edge site fails the commit. Escape: `# noqa: bar-boundary-open-edge`. (The broad
  `bar[0]`/DataFrame-`.index` open-index patterns are deliberately NOT static-flagged — too generic to separate from
  correct tick-aggregation internals — and are covered by the runtime assertion below instead.)
- **Runtime ingestion-time assertion** — `unified_trading_library.availability_stamping.assert_close_edge(...)`: where a
  vendor close field exists, assert the stamped edge matches it (or the canonical `compute_bar_close_boundary` close);
  raises on mismatch so an open edge can never silently pass through.
- **Cross-source edge fixture** (features-service / MDPS pytest): the same instrument + window from a tick-aggregated
  source and a pre-aggregated source MUST produce the SAME `t_close`. Runs in the repo's `quality-gates.sh`.
- **STEP 5.74 — `check_mdps_bar_boundary_compliance.py`**: bans inline truncation bypasses (`floor`/`round`/
  `dt.truncate`/`.replace(minute=0,…)`) — use `compute_bar_close_boundary`. (Complementary: 5.74 = no inline truncation;
  5.92 = no open-edge ingestion.)
- **Era/migration**: the per-AG `①–⑫` pre-apply audit `⑪ batch=live` also asserts edge-consistency; the
  `batch_live_symmetry` cross-source equivalence item (k) carries the same fixture.

## Databento raw corpus boundary — the `bar_edge="close"` row-level marker (2026-06-11)

Databento (and Massive, by representation) stamp raw `ohlcv_*` aggregates on the bar OPEN edge, and the MTDS writer
aliases `ts_event→timestamp` (`_COLUMN_ALIASES`, live since 2026-04-16) — so the PRE-conversion raw corpus carries
open-edge values under the column name `timestamp` (2026-06-10 census: 24/24 sampled raw tradfi ohlcv parquets, zero
`ts_event`). The bar_edge plan Phase 1 P0 fix (2026-06-11) closes the METASTABLE column-NAME-keyed MDPS shift:

- **MTDS converts at ingestion (new writes are close-edge)**: `databento_adapter._convert_ohlcv_open_edge_to_close`
  rewrites `ts_event` to `t_close` via `compute_bar_close_boundary` (interval-aware, `_OHLCV_DATA_TYPE_TIMEFRAME`;
  scoped to `ohlcv_*` data_types ONLY — trades/tbbo `ts_event` is point event time and stays) and stamps a row-level
  **`bar_edge="close"`** column. The marker is deliberately a COLUMN, not parquet footer metadata: MDPS reads raw
  parquets via polars `read_parquet` → `to_pandas()` and footer metadata does not survive that path — a column does. The
  writer's day-partition guard (`validate_day_partition_alignment(close_edge=True)`, keyed on the marker) validates the
  half-open `(day, day+1]` window for close-edge frames (the day's last bar legitimately closes at next-day midnight).
  Raw-surface `available_at` is now t_close-anchored for free (the writer stamps it from the post-alias `timestamp`
  column).
- **MDPS shifts only the PRE-conversion corpus, source/content-aware** (`ohlcv_passthrough._is_start_of_period_input`) —
  never keyed on the column NAME alone. Decision order: `bar_edge` marker (`"close"` → never shift; `"open"` → shift) →
  row-level `source` provenance (`databento`/`massive` = open-edge vendors → shift; yahoo/barchart already write the
  close edge → never) → literal `ts_event` column name (legacy raw shape) → unmarked-`ohlcv_1m` default = shift
  (census-grounded; unmarked 15m/24h is the yahoo/barchart close-edge corpus → no shift). Marked input is never
  double-shifted.
- **UAC** `external/databento/schemas.py` + `schemas_columns.py` document `ts_event` as the bar OPEN (start-of-period) —
  the prior "Bar close timestamp" description was wrong.

## Known latent (baselined, not prod-corrupting)

The consumed candle store is right-edge correct; the remaining open-edge sites are latent (not writing consumed candles
to prod) and baselined in STEP 5.92: `market_tick_data_service` Massive connector (`_normalise_ohlcv` — owned by
`tradfi_massive_dual_source_2026_05_28.md` Phase 4b), MDPS `liquidity_adapter._convert_timestamps`
(`periodStartUnix → processing_dt`, semantics under diagnosis). Clear a baseline row when its site is converted to the
close edge.
