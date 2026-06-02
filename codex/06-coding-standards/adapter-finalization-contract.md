# Adapter Finalization Contract — every MDPS candle adapter routes through `_finalize_session_grid`

> **SSOT.** Codified 2026-06-02 from `plans/active/issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md` (operator
> decisions 2026-06-01). Owns the rule: **every** `market-data-processing-service` candle adapter MUST hand its full-day
> grid to `BaseCandleAdapter._finalize_session_grid(...)` before returning, so the emitted series is dense,
> point-in-time-safe, and free of the banned NaN-OHLC / NaN-volume / leading-NaN shapes.

## Why this exists

`_finalize_session_grid` (`market_data_processing_service/app/adapters/base_adapter.py`) is the single place that
resolves the no-trade-bar NaN ↔ non-nullable-OHLC schema collision. Adapters that build a fixed `86400/interval` grid
and return it directly leak three defect shapes downstream (features-service / strategy-service trip on them, or carry
NaN-masking shims that hide the bug):

1. **Leading NaN** — bins before the instrument's first observation of the day (`apply_locf_fill` cannot fill a run that
   precedes the first value).
2. **NaN OHLC** — state-only streams (derivative ticker, liquidity/lending snapshots, book/quote) have no trades, so
   `close` is structurally NaN; the `processed_candles` schema marks OHLCV **non-nullable** (only `prediction`/`sports`
   use the nullable-OHLCV variant). A NaN-OHLC write is the banned 1440-NaN-bar incident shape (MDPS 2026-05-05).
3. **NaN volume** — a snapshot bar has no trade volume; left NaN it violates the required-`volume` column.

## The contract

**Every `process_to_candles` implementation ends with `return self._finalize_session_grid(output, ...)`.** No adapter
returns a raw `CandleOutput` built from the fixed full-day grid. Two modes:

### Close-driven (trades adapters + price-proxy snapshot adapters)

`self._finalize_session_grid(output)` — `close` is the first-observation trigger and OHLC source. Pre-first-trade
no-trade bins drop (cold-start) or carry from a prior-day seed; open no-trade bars after the first are forward-filled
`o=h=l=c=prev_close`, `volume=0`; `market_state==CLOSED` bins drop. Use this when `close` is already populated with a
real price **and** `volume` carries a real value that must not be zeroed.

### State-driven (`state_col`) — state-only adapters whose `close` is structurally NaN

`self._finalize_session_grid(output, state_col="<driver>")` — the named column's first non-NaN is the trigger and the
state driver becomes the candle price (`o=h=l=c=state`). `flow_cols` (default `DEFAULT_STATE_FLOW_COLS` = volume /
trade_count / buy_volume / sell_volume / buy_trade_count / sell_trade_count / total_volume / swap_count /
volume_quote_usd) are **zero-filled** on every kept bar (a snapshot has no trades). `seed_state` carries each named
secondary column's prior-day value into the leading bins under prior-day carry (PIT-safe).

## Per-adapter density contract (the 7 state adapters)

| Adapter                      | data_type           | Finalize call                                                                                       | Rationale                                                                                                        |
| ---------------------------- | ------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `cefi/derivative_adapter`    | `derivative_ticker` | `state_col="mark_price"`                                                                            | close structurally NaN; mark price is the candle price; volume→0                                                 |
| `cefi/futures_chain_adapter` | `futures_chain`     | `state_col="close"`                                                                                 | close already = `last_price`; volume (NaN) → 0                                                                   |
| `cefi/options_chain_adapter` | `options_chain`     | `state_col="mark_price"`                                                                            | close structurally NaN; mark price drives OHLC; volume→0                                                         |
| `cefi/book_snapshot_adapter` | `book_snapshot_5`   | `state_col="mid_price"` (+ pre-LOCF the quote mid/spread/depth)                                     | close structurally NaN; book mid drives OHLC; volume→0                                                           |
| `tradfi/tbbo_adapter`        | `tbbo`              | `state_col="mid_price"` (+ pre-LOCF the quote mid/spread; `MarketStateDetector` → CLOSED bins drop) | close structurally NaN; quote mid drives OHLC; volume→0                                                          |
| `defi/liquidity_adapter`     | `liquidity`         | close-driven (NO `state_col`)                                                                       | close already = `mid_price`; `volume` carries **real TVL** — a `state_col` flow zero-fill would wrongly null TVL |
| `defi/market_state_adapter`  | `market_state`      | close-driven (NO `state_col`)                                                                       | close already = available-liquidity; `volume` carries **real total-supply** — must not be zeroed                 |

**The liquidity/market_state caveat is load-bearing**: when a snapshot adapter repurposes `volume` to carry a real value
(TVL, supply), it MUST stay close-driven. Adding `state_col` would zero-fill `volume` and destroy that data. Pick
`state_col` only when `volume`/the flow columns are genuinely trade-derived (and therefore legitimately 0 on a snapshot
bar).

## Prior-day carry (Decision 1) — `seed_price` / `seed_ts` / `seed_state`

For a continuously-traded instrument the leading bins are seeded from the **prior day's last-known price** (known at
00:00 → zero look-ahead, batch==live) rather than dropped: `o=h=l=c=seed_price`, `volume=0`, `staleness` measured from
the prior trade. Cold-start (no prior observation anywhere) still drops; `CLOSED` still drops. The finalizer accepts the
seed; **sourcing + threading** the per-instrument seed from the prior day's last parquet/manifest into both the batch
and live call paths is the orchestration-layer work (see the audit doc's Decision-1 threading todo). Reprocessing
existing parquets to densify them rides the deferred GCS backfill pass — never a standalone whole-corpus walk
(single-walk discipline).

## Honest absence still holds

A window with **no observation at all and no seed** collapses to the zero-row honest-absence output
(`_make_empty_candle_output`), which the live-worker loop routes to `record_empty_for_shard`. A state adapter whose
driver column is entirely absent (e.g. a derivative tick with funding but no mark price) therefore yields honest absence
— never a fabricated NaN-OHLC row. This composes with `codex/02-data/honest-absence-downstream-handling.md` §
"Per-adapter density contract".

## Code-review checklist

- [ ] `process_to_candles` ends with `return self._finalize_session_grid(output, ...)` — no raw fixed-grid return.
- [ ] State-only adapter (close structurally NaN) passes the correct `state_col`; price-proxy/real-volume adapter stays
      close-driven.
- [ ] `state_col` is NOT used on an adapter that carries real data in a `flow_cols` column (volume=TVL/supply).
- [ ] Groupby-mean feature arrays (book/quote) are `apply_locf_fill`-ed before finalize so mid-day gaps are dense.
- [ ] A per-adapter test asserts: no leading NaN, no NaN OHLC, no NaN volume, and no-driver → honest absence (0 rows).
