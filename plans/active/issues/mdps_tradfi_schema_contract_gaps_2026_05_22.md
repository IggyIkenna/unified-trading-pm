---
title: "MDPS TradFi schema contract gaps — combo/UNKNOWN/futures_chain produce NaN bars"
created: 2026-05-22
source:
  - mdps_backfill_phase3_2026_05_22.md
  - plans/epics/mtds_mdps_master.md
priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

## What I found

`mdps-backfill-tradfi-20260522-051203` VM logs (launched 2026-05-22 05:12 UTC) emit `No SchemaContract registered`
warnings at `recovery=alert` for these `(venue, instrument_type)` combinations:

| Venue | instrument_type           | Impact                                                |
| ----- | ------------------------- | ----------------------------------------------------- |
| CME   | `combo`                   | Multi-leg combo futures → NaN bars, rows skipped      |
| CME   | `UNKNOWN`                 | Unknown instrument type → NaN bars, rows skipped      |
| CME   | `futures_chain`           | Continuation contracts → NaN bars, rows skipped       |
| ICE   | `G   FMZ0020-BRN FMZ0020` | Calendar spread (instrument_type is the ticker) → NaN |

Additionally, `SCHEMA_VALIDATION_FAILED` for `data_type=trades` bars: when no trades occur in a 1-min interval,
`open/high/low/close` are NaN, but the processed_candles schema marks them NOT NULLABLE → rows skipped entirely for that
interval. This affects all CME/ICE futures trade-bar dates.

**VIX is NOT affected**: VIX bars use `data_type=ohlcv` (not `data_type=trades`), which allows nullable OHLC.

**Root cause**: `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY` in `contracts.py` has entries for
`("tradfi", "future", "ohlcv_1m") → TRADFI_FUTURE_OHLCV_1M` and the 4 new entries added at UAC@`7cdee1bc`
(`futures_chain`, `combo`, `UNKNOWN`, `index`). However, the MDPS schema contract lookup also uses instrument_type for
processed_candles schema validation, and `combo`/`UNKNOWN`/`futures_chain` instrument types do not have entries for
`data_type=trades` in the registry — only `ohlcv_1m`.

## Why it matters

**Scope of impact**: CME/ICE multi-leg futures (combo spreads, continuation chains, calendar spreads) produce no
processed_candles output. These are significant instruments for TradFi:

- CME crude oil calendar spreads (CL spreads)
- CME equity futures combo legs
- ICE Brent calendar spreads

**VIX unblocked**: MTDS-3.3.TradFi-V (VIX bar verification) is NOT blocked. VIX uses ohlcv, which works.

**Strategy impact**: any TradFi strategy using CME/ICE spread/combo/continuation instruments will have NaN bars until
fixed.

## Recommended decision

Two-part fix:

**Fix A** — Add `data_type=trades` schema contracts for `combo`/`UNKNOWN`/`futures_chain` instrument types:

```python
# In unified_api_contracts/internal/schemas/contracts.py
("tradfi", "futures_chain", "trades"): TRADFI_FUTURE_TRADES_1M,
("tradfi", "combo", "trades"): TRADFI_FUTURE_TRADES_1M,
("tradfi", "UNKNOWN", "trades"): TRADFI_FUTURE_TRADES_1M,
```

Requires defining `TRADFI_FUTURE_TRADES_1M` schema class (nullable OHLC, required volume/trade_count).

**Fix B** — Allow nullable OHLC for `data_type=trades` in `processed_candles` schema:

```python
# processed_candles schema: open/high/low/close should be Optional[float] when data_type=trades
# (intervals with 0 trades have no price formation)
```

**Priority**: P2 — does not block VIX verification (MTDS-3.3.TradFi-V). Does block CME/ICE combo bar generation. After
current TradFi VM completes (~16 days), a follow-up VM with UAC@`7cdee1bc`+ these schema fixes will re-attempt
`combo`/`UNKNOWN`/`futures_chain` rows marked `attempted_failed`.

**Note on current VM strategy**: `mdps-backfill-tradfi-20260522-051203` was launched BEFORE UAC@`7cdee1bc` and these
schema fixes. The VM will complete normally (~16 days), marking regular `future` instruments as `captured` and
`combo`/`UNKNOWN`/`futures_chain` as `attempted_failed` (shard-level isolation, recovery=alert). A follow-up VM should
be launched after this VM completes, using a tarball that includes both UAC@`7cdee1bc` + the schema fixes above.
