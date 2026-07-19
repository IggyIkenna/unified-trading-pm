---
doc_type: issue
title: "P0: Databento TradFi FUTURE/OPTION captures write blank instrument_id (futures_chain shape) — shard-atom mismatch fails CME ohlcv_1m Phase-D"
summary:
  The Databento adapter statically maps every FUTURE->futures_chain / OPTION->options_chain regardless of data_type or
  symbol count, so venue_fetch blanks instrument_id and sets underlying=<root> for ALL Databento TradFi FUTURE/OPTION
  captures (CME/ICE/CBOE/FX). The Phase-D checker matches CME ohlcv_1m on the canonical per-contract id -> no_matching_row
  even though the fetch succeeded. Needs a shard-atom ruling (per-root chain vs per-contract) before the fix + the MVP
  backfill.
status: open
nature: bug
asset_group: tradfi
stage: data
repos: [market-tick-data-service]
scope: databento-future-option
tags: [shard-atom, manifest, honest-coverage, canonical-id, phase-d, data-correctness]
related: [tradfi_consolidated_closeout_2026_07_18, databento_adapter, pipeline_e2e_check]
created: 2026-07-19
priority: P0
---

# P0 — Databento TradFi FUTURE/OPTION captures write blank `instrument_id` (futures_chain shape)

## Discovery

Phase-D MTDS gate (2026-07-19): `TRADFI:CME:ohlcv_1m` force-leg **FAILED** `manifest_status_invalid:no_matching_row`,
even though a same-day measurement proved the fetch works (wrote 159,174 + 820,639 real CME ES ohlcv_1m rows). NASDAQ/NYSE
ohlcv_1m PASS. Root-caused via grep-then-READ (workflow `wf_c5d562c6-7e0`, diagnose-cme agent).

## Root cause (writer)

`market-tick-data-service/.../adapters/tradfi/databento_adapter.py:179-185`:
```python
_PARTITION_INSTRUMENT_TYPE: dict[InstrumentType, str] = {
    InstrumentType.FUTURE: "futures_chain",   # unconditional — regardless of data_type or symbol count
    InstrumentType.OPTION: "options_chain",
    InstrumentType.EQUITY: "equity",
    ...
}
```
Every Databento `FUTURE` row is written `instrument_type=futures_chain`. Since `futures_chain ∈
_UNDERLYING_PARTITIONED_TYPES` (`engine/orchestrator/symbol_rules.py:258`),
`engine/orchestrator/venue_fetch.py:451-459` sets `is_derivative=True` →
`instrument_id_for_manifest = ""` and `underlying_for_manifest = <translated root>` (ES→SP500 via UAC
`tradfi_symbology.py:166`). So the **real** manifest row for CME ohlcv_1m is
`instrument_type=futures_chain, underlying="SP500", instrument_id=""`. This is unlike the dynamic
`tradfi_shared.py::_shard_instrument_type_for` (chain only when a shard genuinely spans >1 symbol) used by the *other*
TradFi adapters (Yahoo/ECB/OFR/FRED/IBKR) — Databento is the outlier.

## Consequence (checker)

`scripts/pipeline_e2e_check.py` derives `is_bundled_chain` from the shard's **`data_type`** (`"ohlcv_1m"` ∉
`{options_chain,futures_chain}`) → `False` → it matches on `instrument_id` (falling back to the hardcoded
`smoke_matrix._REPRESENTATIVE_SYMBOL["CME"]="ESM26"`), but every real CME row has `instrument_id=""` → **zero rows match
→ `no_matching_row`**. NASDAQ/NYSE are `EQUITY` (never blanked) so they match. This is exactly and only a FUTURE-vs-EQUITY
distinction.

## The decision needed (shard-atom SSOT — do NOT guess)

Is the intended manifest shard atom for a TradFi **ohlcv_1m FUTURE** series:
- **(A) per-root chain** (`underlying=SP500, instrument_id=""`) — one ohlcv shard per root, per-contract identity only in
  parquet content. Then the **writer is correct** and the **fix is the checker**: make `is_bundled_chain=True` for TradFi
  FUTURE/OPTION venues so it matches on `underlying`. Surgical, no migration.
- **(B) per-contract** (`instrument_id=CME:FUTURE:SP500-USD@LIN-YYYYMMDD`) — matching the plan's canonical id that carries
  an expiry. Then the **writer is wrong** (blanking instrument_id breaks per-instrument honest-coverage for ALL Databento
  FUTURE/OPTION data_types, not just ohlcv_1m) and the fix is `databento_adapter.py`'s static map → dynamic (mirror
  `_shard_instrument_type_for`), **plus a manifest re-migration** of existing CME/ICE captures.

The plan's canonical derivative id (`-USD@LIN-YYYYMMDD`, per-contract) leans toward **(B)**, but the manifest shard-atom
granularity for ohlcv time-series is a separate axis from the id shape — hence the ruling. **Blocked on operator/SSOT
decision (`BLOCKED-OPERATOR-DECISION`).**

## Impact + holds

- **Scope**: every Databento TradFi FUTURE/OPTION capture (CME/ICE futures + options, all data_types), not just CME
  ohlcv_1m. Under (B) it is a corpus-wide honest-coverage-credit gap.
- **HOLD the CME/ICE MVP backfills** until this is decided — running them now bakes the current (possibly-wrong) shape
  into PROD + a future migration. NASDAQ/NYSE (EQUITY) + CBOE/FX ohlcv_24h (Yahoo, non-Databento) MVP backfills are
  **unaffected** and may proceed.

## Files cited

- `market_tick_data_service/market_interface/adapters/tradfi/databento_adapter.py:179-185`
- `market_tick_data_service/market_interface/adapters/tradfi/databento_enrichment.py:91-102,139`
- `market_tick_data_service/engine/orchestrator/symbol_rules.py:258`
- `market_tick_data_service/engine/orchestrator/venue_fetch.py:317-400,451-459`
- `market_tick_data_service/engine/orchestrator/manifest_finalize.py:309`
- `market_tick_data_service/scripts/pipeline_e2e_check.py:194,452,481,664,706,815-821,901`
- `unified-trading-library/.../pipeline_e2e_check/shard_verify.py:67-124`
