---
title: "CME legacy 2-segment instrument_id not re-normalized in MDPS — partition_mismatch / 'malformed instrument_id'"
created: 2026-05-26
author: harsh-main
source:
  - "market-data-tick-tradfi-central-element-323112/_index/per_vm/mdps-tradfi-2020-20260523-125440.parquet (attempted_failed error_reason)"
  - plans/active/issues/mdps_tradfi_schema_contract_gaps_2026_05_22.md
priority: P2
status: solved
locked_by: live-defi-rollout
locked_since: 2026-05-26
---

> **Related (sibling facet, same failing rows):**
> [`mdps_tradfi_schema_contract_gaps_2026_05_22.md`](mdps_tradfi_schema_contract_gaps_2026_05_22.md) covers the
> **NaN-OHLC / missing-SchemaContract** facet. This issue covers the **malformed `instrument_id`** facet. The same CME
> `attempted_failed` rows fail BOTH validators (`schema_violation` non-nullable OHLC **and** `partition_mismatch`
> malformed id). Fix both before re-attempting the affected range.

## What I found

The `mdps-tradfi-2020` backfill VM writes `attempted_failed` manifest rows whose `error_reason` is a
`StreamingParquetWriter pre-write validation failed` with, among others:

```
[partition_mismatch] N row(s) inconsistent with partition_path
  'day=2020-02-09/category=tradfi/venue=CME/instrument_type=UNKNOWN/data_type=ohlcv_1m':
  malformed instrument_id: 'CME:ESH0'; malformed instrument_id: 'CME:E2AG0 C3370'; ...
```

Diagnosis chain:

1. **Canonical contract** (`unified_trading_library/io/instrument_id_validator.py`): a valid `instrument_id` is
   `VENUE:INSTRUMENT_TYPE:SYMBOL` — exactly **3** colon-segments (`_split_instrument_id` → `split(":", 2)`,
   `len == 3`). `CME:ESH0` is **2** segments → "malformed"; the partition even carries `instrument_type=UNKNOWN`.
2. **The current classifier is correct.** Live-tested
   `market_tick_data_service.market_interface.adapters.tradfi.databento_classifier.classify_databento_symbol`:
   `ESH0 → FUTURE/ES`, `E2AG0 C3370 → OPTION/ES`, `ESM6 → FUTURE`, `GCZ4 C2000 → OPTION`. So today's MTDS code would
   build proper `CME:future:ESH0`.
3. **Therefore the bad ids are LEGACY data** — 2020 CME ticks written by an older MTDS version (pre-classifier) and
   stored with 2-segment ids + `instrument_type=UNKNOWN`.
4. **MDPS carries them through unchanged.** `market-data-processing-service` does **not** import
   `classify_databento_symbol` and does no `instrument_id`/`instrument_type` re-derivation — it passes the raw row's
   stored id straight into the OHLCV write, where the 3-segment validator rejects it.

This is **not** the KRAKEN `:`-in-symbol case (handled by `split(":", 2)` maxsplit). It is a missing-segment /
un-reclassified-legacy-data problem.

## Why it matters

- Every legacy CME (and any other pre-classifier-era) instrument with a 2-segment / `UNKNOWN` id produces **zero**
  processed_candles output — the rows are `attempted_failed`, so the tradfi OHLCV coverage for those instruments/dates
  is silently absent.
- Re-fetching the raw data from Databento to re-stamp ids is **not** viable (Databento quota exhausted).
- Affects the TradFi data-pipeline-correctness gate (CME futures/options OHLCV).

## Recommended decision

**Fix C — Re-normalize `instrument_id` at the processing boundary** (preferred; no raw re-fetch):
when MDPS reads a row whose `instrument_id` is malformed (≠ 3 segments) or `instrument_type` is `UNKNOWN`, re-derive
the canonical id from the raw `symbol` via the classifier + `build_instrument_id`, and re-stamp `instrument_type`.

Open design points (resolved during implementation):

- The classifier lives in **MTDS**; MDPS does not depend on MTDS. The shared re-normalization helper must live in a
  lib both import (UTL or UAC), or the classifier relocates there.
- Requires the raw `symbol` (e.g. `ESH0`) to still be present on the row MDPS processes — confirm before implementing.

Compose with the sibling issue's **Fix A/B** (nullable-OHLC trades schema + `combo`/`UNKNOWN`/`futures_chain` contracts)
so a single follow-up reprocess of the affected CME range clears both `schema_violation` and `partition_mismatch`.

## Resolution

**SOLVED (code) — `market-data-processing-service@fa39207`** (2026-05-26). Implemented **Fix C**:
`_renormalize_legacy_tradfi_instrument_ids` in `app/core/canonical_writer.py`, called at the top of
`write_candle_parquet` before instrument_type inference + partition_path build. For tradfi rows whose id is 2-segment,
it extracts the symbol embedded in the malformed id, classifies it via `classify_databento_symbol` (MTDS; MDPS depends
on MTDS), and rebuilds the canonical id via `build_instrument_id(venue, type, underlying, expiry_date=, strike=,
option_right=)` — mirroring `DatabentoAdapter` exactly. No re-fetch needed (the symbol is recoverable from the id), so
the Databento quota exhaustion is moot.

**Key correctness point:** the canonical id is NOT `CME:future:ESH0` — `build_instrument_id` encodes
underlying+expiry(+strike+right), so distinct contracts stay distinct:

- `CME:ESH0` → `CME:FUTURE:ES-20200320`
- `CME:E2AG0 C3370` → `CME:OPTION:ES-20200221-3370-C`
- `CME:ESM6` → `CME:FUTURE:ES-20260619`

Gated to tradfi; no-op for non-tradfi, already-canonical (≥3-segment), and unclassifiable symbols (shard isolation —
left unchanged to fail loud rather than be silently coerced).

**Verified:** lint ✓ + basedpyright ✓ (MDPS `quality-gates.sh` steps 0–2 green); 2 regression tests added to
`tests/unit/test_streaming_write_per_tf.py` — both pass (`uv run --with pytest-timeout pytest -k renormalize`).

**Follow-ups (this issue is code-solved, not operationally-closed):**

1. **Reprocess** the affected legacy CME range (re-run the `mdps-tradfi` backfill) so the existing `attempted_failed`
   rows are re-attempted with canonical ids — the fix only takes effect on reprocess.
2. Land the sibling **Fix A/B** (nullable-OHLC trades schema + `combo`/`UNKNOWN`/`futures_chain` contracts) from
   [`mdps_tradfi_schema_contract_gaps_2026_05_22.md`](mdps_tradfi_schema_contract_gaps_2026_05_22.md) before the
   reprocess, so a single pass clears both `partition_mismatch` and `schema_violation`.
3. **Env gap:** MDPS `quality-gates.sh` TESTS step needs `pytest-timeout` in the provisioned env (pre-existing; not
   introduced here) — tests were run via `uv run --with pytest-timeout`.
