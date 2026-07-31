---
doc_type: issue
title: >-
  delta_one passthrough loader's per-instrument symbol filter never matches real oracle_prices rows -- manifest
  registers instrument_id with underscore separators (ETH_USD) but the raw parquet's symbol/feed columns use slash
  separators (ETH/USD), so _load_passthrough_range's exact-match filter silently returns 0 rows for nearly every
  instrument, even though real data exists -- confirmed live: 0/51 instruments completed across a 97-day span of a full
  verification run, despite the (now-fixed) timestamp bugs being completely resolved
summary: >-
  4th distinct bug found in `_passthrough_loader.py` this session (2026-07-31), independent of the 3 timestamp bugs
  already fixed (`features-service@3bce3997` / `c46509be` / `f34d2c1a`, see the sibling issue
  `delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`). With the timestamp bugs fully fixed and verified
  (confirmed live: the polars SchemaError is gone, real 172-day multi-instrument runs progress cleanly through loading
  with zero exceptions), a full verification-window run (`features-delta-one-defi-20260731-020600`,
  `returns`/`oracle_prices`, `2023-05-12..2023-10-31`) still produced `Completed 0/51 instruments for returns` on EVERY
  single date checked (spot-checked through 2023-08-17, ~97 days in) -- zero real writes, despite the range-level load
  claiming `Loaded range candles for 27/51 instruments (15m)` (i.e. real data genuinely exists for at least half the
  instruments somewhere in the window). Root-caused via direct comparison of the manifest-registered instrument_id
  against the raw parquet's actual column values (not guessed): `_load_passthrough_range()`'s per-instrument filter
  (`features_service/delta_one/app/core/_passthrough_loader.py:281-283`) does an EXACT uppercase string match between
  the manifest's raw_symbol segment (e.g. `ETH_USD`, underscore-separated -- confirmed via `dependency_checker.py`'s
  `_discover_instruments_from_manifest`, which synthesizes instrument_id directly from whatever the WRITER stamped into
  the manifest's own `instrument_id` field) and the raw file's `symbol`/`feed` column (e.g. `ETH/USD`, SLASH-separated
  -- confirmed via direct parquet inspection of a real 2023-05-31 oracle_prices row, both the `symbol` and `feed`
  columns literally contain `ETH/USD`). `"ETH_USD" != "ETH/USD"` under `==`, so the filter matches zero rows for any
  instrument whose real symbol contains a separator character that differs between the two conventions. This is a
  SEPARATE bug from the 3 timestamp bugs -- it exists in the same function chain but is a distinct code path (the symbol
  filter, not timestamp resolution) and was invisible until the timestamp bugs were cleared (a SchemaError crashed the
  run before this filter's effect could even be observed in isolation).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [defi, features-service, delta-one, passthrough, symbol-matching, data-correctness, vm-spend-waste]
related:
  - /plans/active/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
created: "2026-07-31"
author: slot-2 (data_engineering craft, defi_satellite_ao_dispatch_batch3-014)
source: [features-delta-one-defi-20260731-020600 full verification-window run, 0/51 completed across ~97 days]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# What I found

After shipping all 3 timestamp fixes in `_resolve_passthrough_timestamp` this session (see the sibling issue doc's
Progress Log for the full chain: `3bce3997` → `c46509be` → `f34d2c1a`), relaunched the real `returns`
verification-window run to confirm end-to-end success. The timestamp SchemaError is CONFIRMED completely gone — the run
progresses cleanly with zero exceptions across the entire log. But it still produces zero real output:

```
2026-07-31 02:19:30,944 INFO Completed 0/51 instruments for returns
2026-07-31 02:19:31,853 INFO Completed 0/51 instruments for returns
... (identical 0/51 on every date checked, 2023-05-12 through 2023-08-17)
```

`grep -c "record_captured\|Wrote.*rows"` across the full ~32,500-line log: 0. Zero real writes anywhere.

## Root cause: a symbol-format mismatch in the per-instrument filter

`_load_passthrough_range()` (`_passthrough_loader.py:222-267`) filters the loaded raw day-frames down to one instrument
via:

```python
if raw_symbol:
    sym_col = next((c for c in _PASSTHROUGH_SYMBOL_COLUMNS if c in raw.columns), None)
    if sym_col is not None:
        raw = raw.filter(pl.col(sym_col).cast(pl.Utf8).str.to_uppercase() == raw_symbol.upper())
```

`raw_symbol` comes from the manifest-discovered `instrument_id`'s third segment (`instrument_id.split(":")[2]`). Per
`dependency_checker.py`'s `_discover_instruments_from_manifest` (`_690:723`), that instrument_id is synthesized as
`f"{venue}:{data_type.upper()}:{row.instrument_id}"` where `row.instrument_id` is whatever the WRITER stamped into the
manifest at capture time — for CHAINLINK oracle_prices, that's the underscore-separated canonical form, e.g. `ETH_USD`.

The raw parquet's own `symbol`/`feed` columns (checked both — `_PASSTHROUGH_SYMBOL_COLUMNS` tries `symbol` first)
contain the SLASH-separated venue-native form instead. Confirmed via direct inspection of a real row
(`raw_tick_data/.../day=2023-05-31/.../data_type=oracle_prices/ETH_USD.parquet`):

```
>>> df.select("symbol", "feed").unique()
symbol: "ETH/USD"
feed:   "ETH/USD"
```

So the filter compares `"ETH/USD".upper()` (`"ETH/USD"`) against `"ETH_USD".upper()` (`"ETH_USD"`) — never equal. Every
instrument whose manifest-registered id uses an underscore where the raw file uses a slash (or any other separator
mismatch) silently filters to zero rows, with NO error or warning distinguishing it from genuine honest-absence — the
caller just sees `raw.is_empty()` and moves on (`_load_passthrough_range` returns `pl.DataFrame()`), logged upstream as
an ordinary "no candles" skip.

## Why 27/51 "succeeded" at the range level but still 0/51 completed at the per-date level

`_load_one_instrument_range` (`_tf_cluster_helper.py`) logged `Loaded range candles for 27/51 instruments (15m)` —
meaning 27 of the 51 manifest-discovered instrument_ids DID return non-empty data through the same filter. This is
consistent with the bug: some instruments' real symbol format happens to already match the manifest's registered form
(no separator, or the same separator both places — e.g. `BTC_USD`-style ids where the raw file ALSO uses underscore, or
single-word symbols with no separator at all), while others (like `ETH_USD` vs `ETH/USD`) never match. This explains why
the failure isn't 51/51 — it's the ones with a genuine format mismatch, which the per-date processing then also hits
identically to why 0 dates ever wrote real data: the SAME filter runs at the per-instrument level regardless of date, so
an instrument that fails to match once fails on every date, and enough of the 51 requested instruments hit this that not
a single date across the ~97 days checked produced any output.

# Why this matters

Blocks the `returns` leg of `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo from completing even with all 3
timestamp bugs fixed. Also affects `funding_oi` (once its separate structural OI-absence blocker,
`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`, is resolved) — the same filter is shared
code, not oracle_prices-specific.

# What I did NOT do

Did not patch the filter myself — the correct normalization (strip/replace separator characters before comparing, e.g.
`.str.replace_all("[/_-]", "")` on both sides, or map based on a known venue-symbol convention table) is a real design
decision about which separator forms are canonical across ALL DEFI pass-through venues (not just CHAINLINK), and this
session already shipped 3 fixes in the same file/function chain — stacking a 4th blind guess without checking every
affected venue's real symbol format risks the same "looked fixed, wasn't" pattern that took 3 iterations to fully
resolve for the timestamp bug. A repo owner should verify against every DEFI pass-through venue's actual raw symbol
format before choosing the normalization strategy.

# Recommended decision

- [ ] [BACKEND] P1. Normalize both sides of the symbol comparison in `_load_passthrough_range()`
      (`_passthrough_loader.py:281-283`) before matching — e.g. strip all non-alphanumeric separators from both
      `raw_symbol` and the raw column's values before the `==` check. Verify against real raw data for EVERY DEFI
      pass-through venue/data_type pair (not just CHAINLINK oracle_prices) before shipping, since a different venue may
      use yet another separator convention. Add a regression test using the exact real-data shape confirmed in this
      issue (`ETH_USD` manifest id vs `ETH/USD` raw symbol). Repo: features-service. Done when: a DEFI `returns` run
      over the verified-clean window (`2023-05-12..2023-10-31`) shows `Completed N/51 instruments` with N > 0 on
      multiple real dates, and writes real `record_captured` rows (verified via `gs://features-defi-prd-.../delta_one/`
      actually gaining a prefix).
- [ ] [DATA] P2. Once the above lands, resume `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo's `returns`
      leg over the full captured window. Repo: features-service.

# Progress Log

- 2026-07-31 (slot-2, data_engineering craft, D1 todo dispatch): filed after confirming all 3 timestamp bugs are
  genuinely fixed (SchemaError eliminated, confirmed via a real 97-day-deep run with zero exceptions) but the run still
  produces zero writes — root-caused via direct comparison of manifest instrument_id vs raw parquet column values (not
  guessed), confirmed with concrete evidence from the exact same file/instrument used throughout this session's
  investigation.
- 2026-07-31 (slot-5, data_engineering craft, D1 todo resume): shipped the recommended fix —
  `features-service@7e10172c` strips all non-alphanumeric separators from both sides of the `_load_passthrough_range()`
  symbol comparison (`_SYMBOL_SEPARATOR_PATTERN = "[^A-Z0-9]"`, applied via one shared pattern to both the Python-side
  `raw_symbol` and the polars column expr). Verified against real raw data for BOTH DEFI oracle_prices venues before
  shipping (not just CHAINLINK, per this doc's own caution): downloaded real CHAINLINK (`ETH_USD` day=2023-06-01) and
  PYTH (`BTC_USD` day=2025-01-01) parquet directly — both write slash-separated `symbol`/`feed` columns (`ETH/USD`,
  `BTC/USD`), confirming one normalization rule covers both venues. `funding_oi`/`perp_funding` is unaffected by this
  bug (its `raw_symbol` is blank for HYPERLIQUID's per-venue bundle rows, so the filter block never runs for it). Added
  6 regression tests incl. the exact real-data shape from this issue (`ETH_USD` manifest id vs `ETH/USD` raw symbol) —
  120/120 green. Full `quality-gates.sh` green, pushed to LDR. Relaunched the verification run
  (`features-delta-one-defi-20260731-025149`, `FEATURE_GROUP=returns FORCE=1`, same window `2023-05-12..2023-10-31` —
  `FORCE=1` is required because the pre-fix runs already wrote `empty_confirmed(SOURCE_RETURNED_ZERO)` manifest rows
  across this window, so a non-force run would skip-as-already-captured and give a false signal either way).
  **Caution for the next reader**: the first launch attempt fetched a STALE features-service tarball (pinned to the
  prior commit `f34d2c1a`, not this fix) — caught via the launcher's own freshness warning before it burned real VM
  time, deleted immediately (seconds-old, no work lost), republished via `create-code-tarballs.sh --include
  features-service` (required an incidental `deployment-service` venv bootstrap — `uv sync` — since
  `gcs_upload_via_adc.py` needs `deployment_service` importable; that also touched `deployment-service/uv.lock`,
  reverted before relaunch as unrelated drift), then relaunched clean. **Not yet confirmed end-to-end** — VM still
  running as this entry is written; do not flip the P1 checkbox below until the run's actual output confirms
  `Completed N/51` with N>0 and real GCS writes, per the stated done-when.
