---
doc_type: issue
title:
  features-service delta_one DataLoader can never resolve TradFi FUTURE/OPTION chain-bundle candle data — silent-miss, 0
  rows, no error
summary: >-
  Surfaced while running candle_canonical_path_migration_execution_2026_07_24.md todo 15's "both-axes reader load-test"
  (a derivative/trades slice AND a tradfi 1m slice, against real PROD data). The CEFI trades slice loaded cleanly (744
  rows), but the TradFi ohlcv_1m FUTURE slice returned 0 rows with a silent "No upstream MDPS data" WARNING even though
  the object demonstrably exists in GCS. Root cause: `DataLoader._canonical_candle_blob_paths`'s chain-bundle detection
  (`is_chain = data_type in {"options_chain", "futures_chain"}`) checks against RAW-TICK-only data_type sentinel values
  that never appear as a processed-candle `data_type=` (which is always an OHLCV/aggregation key like `ohlcv_1m`, or a
  source key like `trades`/`derivative_ticker`) — so `is_chain` is structurally always False for real candle reads, and
  the `underlying={u}/ticks.parquet` chain-bundle tail this class already knows how to build is dead code. Any TradFi
  (or other AG) FUTURE/OPTION/COMBO candle stored bundled-by-underlying is silently unreadable via this loader — exactly
  the "empty frames, NO errors" blast-radius risk the migration plan itself called out.
status: open
nature: issue
asset_group: [tradfi, cefi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [candle-canonical, delta_one, data-loader, silent-miss, chain-bundle, data-correctness]
related:
  [
    /plans/active/candle_canonical_path_migration_execution_2026_07_24.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-07-27 (slot-8) while running candle_canonical_path_migration_execution_2026_07_24.md todo 15's
    both-axes reader load-test",
  ]
resolved_by:
locked_by:
locked_since:
---

# delta_one DataLoader silent-misses TradFi FUTURE/OPTION chain-bundle candles

## What I found

Running the "both-axes reader load-test" required by `candle_canonical_path_migration_execution_2026_07_24.md` todo 15
(a derivative/trades slice AND a tradfi 1m slice, against real PROD data — chosen specifically because a tradfi-only
test can false-pass axis-1 while missing axis-2, per that plan's own blast-radius analysis) against the real
`features_service.delta_one.app.core.data_loader.DataLoader`:

- **CEFI axis (SOURCE, non-aggregated `data_type=trades`)**:
  `DataLoader("CEFI").load_candles(instrument_id="ASTER:PERPETUAL:0G-USDT@LIN", data_type="trades", ..., pipeline_mode="batch_aster")`
  on `day=2026-07-20` → **744 rows, non-empty. PASS.**
- **TradFi axis (`data_type=ohlcv_1m`, `instrument_type=FUTURE`)**:
  `DataLoader("TRADFI").load_candles(instrument_id="CME:FUTURE:AUD", data_type="ohlcv_1m", ..., pipeline_mode="batch_databento")`
  on `day=2026-07-22` → **0 rows, `is_empty()=True`**, log:
  `WARNING No upstream MDPS data for CME:FUTURE:AUD on 2026-07-22 (data_type=ohlcv_1m) — skipping date`. **FAIL —
  silent-miss, no exception.**

The object DOES exist in GCS and is directly listable:
`gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-22/pipeline_mode=batch_databento/timeframe=1m/data_type=ohlcv_1m/instrument_type=FUTURE/venue=CME/underlying=AUD/ticks.parquet`

Confirmed this is not a one-off: every `data_type=` value observed under tradfi `processed_candles/` (across
timeframe=1m/5m/15m/1h/4h/1d, `day=2026-07-22`) is `ohlcv_1m` — TradFi's SOURCE-equals-aggregate base-resolution key,
never the literal strings `"futures_chain"`/`"options_chain"`. Every FUTURE/COMBO instrument_type candle object on that
day is bundled `underlying={u}/ticks.parquet` (there is no per-contract flat `.parquet` on disk to fall back to).

**Root cause** (`features_service/delta_one/app/core/data_loader.py`):

- `DataLoader._DERIVATIVE_DATA_TYPES = {"options_chain", "futures_chain"}` (line ~650) and
  `_canonical_candle_blob_paths`'s `is_chain = data_type in self._DERIVATIVE_DATA_TYPES` (line ~454) gate whether the
  chain-bundle tail (`underlying={u}/ticks.parquet`) or the flat tail (`{instrument_id}.parquet`) is built.
- `"options_chain"`/`"futures_chain"` are **raw_tick_data-only** data_type sentinel values (see
  `market-tick-data-service`'s chain-bundle content tooling, which filters raw-tick objects on
  `instrument_type in {futures_chain, options_chain}`). They are never emitted as a **processed-candle** `data_type=`
  value — MDPS candle `data_type=` is always an OHLCV/aggregation key (`ohlcv_1m`) or a SOURCE key (`trades`,
  `derivative_ticker`), per the LOCKED canonical candle shape ruling in
  `issues/candle_feature_canonical_path_divergence_2026_07_20.md`.
- Consequence: `is_chain` is **structurally always False** for every real processed-candle read through this class — the
  chain-bundle branch (`_extract_underlying` + the `underlying=.../ticks.parquet` tail, both otherwise correctly
  implemented) is dead code. `candle_instrument_type_tokens` derives the right `instrument_type=` token (e.g.
  `"future"`/`"FUTURE"`) independently of `is_chain`, so the candidate paths built are always the flat
  `{instrument_id}.parquet` shape — which never exists on disk for a bundled-by-underlying instrument.
- By contrast, `features_service/volatility/core/data_loader.py` does NOT have this bug: its chain-aware callers
  (`load_options_chain`/`load_futures_chain`) pass the chain data_type literal explicitly themselves — chain-ness is a
  caller decision there, not data_type auto-detection off the candle's own `data_type=` value.

## Why it matters

This is exactly the "empty frames, NO errors" blast-radius risk
`candle_canonical_path_migration_execution_2026_07_24.md` itself flagged before the P7 migration ran ("silent-miss is
the hazard"). Any TradFi (or other AG, if the same bundling pattern applies) FUTURE/OPTION/COMBO instrument read through
`DataLoader.load_candles` returns a silently-empty, warning-only result — indistinguishable from genuine missing
upstream data — rather than raising or surfacing a `content_check=non_canonical`-style verdict.
`candle_canonical_path_migration_execution_2026_07_24.md`'s own todo 3 (readers dual-read via `candle_read_prefixes`)
was verified via a **code read only** ("every one dual-reads... no code change needed") and did not catch this, because
the bug is not in `candle_read_prefixes` itself (which correctly builds pm-partitioned/bare prefix candidates) — it is
in the CALLER's `is_chain` gate that decides which tail (`underlying=.../ticks.parquet` vs `{instrument_id}.parquet`) to
append. A live load-test was required to surface it, which is exactly why the migration plan called for one instead of
trusting the code-read alone.

## Recommended decision

Fix `is_chain` detection in `features_service/delta_one/app/core/data_loader.py`'s `_canonical_candle_blob_paths` (and
audit `_resolve_blob_paths`'s legacy/deep-historical branches + any sibling helper using the same
`_DERIVATIVE_DATA_TYPES` set) to key off **`instrument_type`** (e.g. `FUTURE`/`OPTION`/`COMBO`, whichever set MDPS
actually bundles by `underlying=`) rather than `data_type`, since `data_type` on the candle namespace is never
`"futures_chain"`/`"options_chain"`. Cross-check whether the same `_DERIVATIVE_DATA_TYPES`-style check exists anywhere
else in `unified-trading-api`'s `batch_candles.py` reader (item 3 of the migration plan lists it as a dual-reader too) —
it was not code-read as part of this finding.

## Todos

- [ ] [BACKEND] P1. Fix `DataLoader`'s chain-bundle detection in
      `features-service/features_service/delta_one/app/core/data_loader.py` to key off `instrument_type` (not
      `data_type`) for the `underlying=.../ticks.parquet` vs `{instrument_id}.parquet` tail choice; add a regression
      test reproducing this exact case (TRADFI, `data_type=ohlcv_1m`, `instrument_type=FUTURE`, bundled underlying) so
      it can never silently regress. (repo: features-service). **Done when**: the regression test fails before the fix
      and passes after, and a live re-run of the TradFi axis of the both-axes load-test above (same instrument/day)
      returns non-empty rows.
- [ ] [BACKEND] P2. Audit `unified-trading-api`'s `batch_candles.py` chart reader (also a named dual-reader in
      `candle_canonical_path_migration_execution_2026_07_24.md` todo 3) for the same `data_type`-based chain-detection
      pattern; fix if present. (repo: unified-trading-api). **Done when**: either confirmed not-affected (cite the code
      read) or fixed + regression-tested.
