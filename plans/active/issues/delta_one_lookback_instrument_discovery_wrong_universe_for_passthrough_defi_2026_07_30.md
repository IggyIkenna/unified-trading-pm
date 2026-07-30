---
doc_type: issue
title: >-
  delta_one LookbackValidator._discover_instruments() always walks MDPS processed_candles (dex_pool_swaps/dex_swaps POOL
  instruments) regardless of the requested feature_group's real data_type -- structurally blocks funding_oi/returns for
  DEFI on every date
summary: >-
  Working the D1 DeFi features backfill todo (`defi_satellite_ao_dispatch_batch3_2026_07_26.md`), both delta_one
  `funding_oi` and `returns` feature-group backfills for asset_group=DEFI failed lookback-validation with 0/N candles
  for every one of ~1000 instruments, on two different date windows (2024-02-15..03-15, both `15s` and corrected `15m`
  timeframe). Root cause is NOT a data-availability gap -- it is a genuine instrument-universe mismatch bug in
  `features_service/delta_one/app/core/dependency_checker.py`'s `LookbackValidator`. `funding_oi`/`returns` resolve (via
  `unified_api_contracts.resolve_data_type_for_feature_group`) to DEFI overrides `perp_funding` / `oracle_prices`
  respectively -- both explicitly declared pass-through (`NEEDS_CANDLE_PROCESSING["perp_funding"] = False`,
  `["oracle_prices"] = False` in `unified_api_contracts/registry/market_data_categories.py`), meaning MDPS never
  candle-derives them (confirmed live: a corpus scan of `processed_candles/by_date/.../data_type=*` across multiple
  dates/pipeline_modes shows only `dex_pool_swaps`/`dex_swaps` ever appear -- zero `oracle_prices`/`perp_funding`
  objects exist under `processed_candles` anywhere, by design per `market_data_processing_service/app/adapters/defi/
  __init__.py`'s own pass-through docstring). But `LookbackValidator._discover_instruments()`
  (`dependency_checker.py:679`) unconditionally lists instruments from
  `processed_candles/by_date/day={date}/.../timeframe={timeframe}/` -- for DEFI this is ALWAYS the DEX-pool-swap
  instrument universe (e.g. `BALANCER-ARBITRUM:POOL:0xcc65...`), regardless of which feature_group/data_type was
  actually requested. It then checks THOSE pool instruments against `_build_captured_index()`'s manifest rows filtered
  to the requested group's real data_type (`perp_funding`/`oracle_prices`) -- a completely disjoint instrument set
  (oracle price feeds / perp-funding instruments are not DEX pools), so every instrument reads 0 candles no matter what
  date range is tried. This is date-invariant and universe-invariant: no window choice fixes it, because the bug is in
  which instruments get checked, not which dates have data. Confirmed real captured manifest rows DO exist for both
  `oracle_prices` (131,808 manifest rows) and `perp_funding` (12,500 rows, dense clean block 2023-05-12..2023-10-31,
  zero attempted_failed) in the live MTDS manifest -- the data the feature groups need is there; the validator is asking
  about the wrong instruments.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service, unified-api-contracts]
scope: [engineer]
tags: [defi, features-service, delta-one, lookback-validator, instrument-discovery, data-correctness]
related:
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
  - /plans/active/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md
created: "2026-07-30"
author: slot-3
source: [defi_satellite_ao_dispatch_batch3_2026_07_26.md-D1]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# What I found

Executing D1's delta_one leg (`defi_satellite_ao_dispatch_batch3_2026_07_26.md`, "materialise ... `basis_bps`/
`realized_vol_*` (delta_one, via the `funding_oi` and `returns` feature-groups)"), every launch failed lookback
pre-flight with **every single instrument at 0 candles**:

1. `features-delta-one-defi-20260730-205953` (`funding_oi`, `2024-02-15..2024-03-15`, default `15s` timeframe): 0/5472
   candles for all 1034 instruments — turned out to be a real but DIFFERENT bug (DEFI candles are stored at
   `timeframe=15m`, not the CLI's unconditional `15s` default — same class the launcher's own header comment already
   warns about for TRADFI; fixed for this run via `TIMEFRAME=15m` launcher override).
2. After the `15m` fix, `features-delta-one-defi-20260730-210821` (`funding_oi`, same window): dependency check now
   PASSED ("✅ Dependencies verified"), but lookback validation still failed — 0/91 candles for all 1031 instruments,
   all named `BALANCER-*:POOL:0x...` / similarly DEX-pool-shaped ids.
3. `features-delta-one-defi-20260730-210841` (`returns`, same window, same `15m` fix): identical shape — 0 candles, same
   DEX-pool instrument list.

## Why picking a different date does not fix this

`resolve_data_type_for_feature_group("funding_oi", "DEFI")` → `"perp_funding"`;
`resolve_data_type_for_feature_group("returns", "DEFI")` → `"oracle_prices"` (both via the `defi` entry in
`FEATURE_GROUP_DATA_TYPE_OVERRIDES`, `unified_api_contracts/registry/market_data_categories.py`). Both data types are
declared explicitly pass-through in the same module's `NEEDS_CANDLE_PROCESSING` map:

```python
"perp_funding": False,
...
"oracle_prices": False,
```

`market_data_processing_service/app/adapters/defi/__init__.py`'s own docstring confirms the design: "Pass-through data
types (lending_indices, rate_indices, oracle_prices, ... ) bypass MDPS entirely — they flow directly from MTDS collect-*
handlers to features-onchain-service." A live corpus check (`gcloud storage ls` across several dates/pipeline modes
under `market-data-tick-defi-prd-central-element-323112/processed_candles/`) confirms this in practice: only
`data_type=dex_pool_swaps` (pipeline_mode=batch_onchain_rpc) and `data_type=dex_swaps` (pipeline_mode=batch_databento)
ever appear under `processed_candles` — **zero** `oracle_prices` or `perp_funding` objects exist there, on any date.

`LookbackValidator._discover_instruments()` (`features_service/delta_one/app/core/dependency_checker.py:679`) walks
exactly this `processed_candles` prefix to build its instrument list, with no awareness of which data_type the caller
actually needs:

```python
tail = f"day={date}/timeframe={timeframe}/"
prefixes = [f"processed_candles/by_date/{tail}"]
prefixes.extend(
    f"processed_candles/by_date/day={date}/pipeline_mode={pm}/timeframe={timeframe}/"
    for pm in _candidate_pipeline_mode_values(asset_group)
)
```

For DEFI this ALWAYS resolves to the DEX-pool-swap instrument universe (`BALANCER-ARBITRUM:POOL:0x...`,
`UNISWAP_V3-ETHEREUM:POOL:...`, etc.) — the only instrument_type MDPS candle-derives for DeFi — regardless of whether
the caller asked for `funding_oi`/`returns` (pass-through data, different instruments entirely: oracle price feeds,
perp-funding-rate instruments) or `volume_analysis`/`vwap`/`microstructure` (which DO map to `dex_pool_swaps` and are
the only DEFI delta_one groups this discovery path is actually correct for).

`_check_all_instruments()` then validates those DEX-pool instrument ids against `_build_captured_index()`, which is
correctly filtered to the REQUESTED data_type (`perp_funding`/`oracle_prices`) — but a DEX pool id will never appear in
that index under those data_types (they cover a disjoint instrument set), so every instrument reads 0 candles. This is
**date-invariant**: I confirmed via the live MTDS manifest that both `oracle_prices` (131,808 rows) and `perp_funding`
(12,500 rows, with a clean 173-day zero-`attempted_failed` block `2023-05-12..2023-10-31`) have plenty of real captured
data — just under instrument ids the validator never asks about for these two feature groups.

# Why this matters

Every DEFI delta_one feature_group whose `resolve_data_type_for_feature_group` override maps to a pass-through type —
today that's `funding_oi` (`perp_funding`) and the ~13 groups mapped to `oracle_prices` (`technical_indicators`,
`moving_averages`, `oscillators`, `volatility_realized`, `momentum`, `returns`, `candlestick_patterns`,
`market_structure`, `round_numbers`, `streaks`, `temporal`, `economic_events`, `targets`) — is structurally unable to
pass delta_one's lookback pre-flight for DEFI, on ANY date, until this is fixed. Only `volume_analysis`/`vwap`/
`microstructure` (→ `dex_pool_swaps`) and `liquidations` (→ `liquidations`, itself candle-processed per
`NEEDS_CANDLE_PROCESSING`) are unaffected. This blocks D1's entire delta_one leg (`funding_oi`+`returns` were the two
groups D1 asked for) and would block essentially all other DEFI delta_one feature work too.

# What I did NOT do

Did not modify `LookbackValidator` — `_discover_instruments`/`_check_all_instruments` are shared across CEFI/TRADFI/
DEFI/PREDICTION, so a fix needs a scoped design decision (e.g. discover instruments from the MTDS manifest's
`candle_data_types`-matching rows instead of / in addition to the `processed_candles` GCS walk, when the requested
data_type is pass-through) rather than a rushed patch in the middle of a backfill session — same judgment call this
task's craft rules ask for ("if you uncover a correctness issue the plan didn't anticipate, file an issue doc + notify
the operator; do not absorb unplanned scope"). Did not re-attempt further date windows for `funding_oi`/`returns` — the
failure is instrument-universe-shaped, not date-shaped, so further windows would reproduce identically (verified across
2 separate windows/timeframes already).

# Recommended decision

Fix `_discover_instruments()` (or introduce a parallel discovery path used only when `candle_data_types` are all
pass-through per `needs_candle_processing()`) to source its instrument list from the MTDS availability-manifest rows
matching the requested `candle_data_types` (mirroring what `_build_captured_index()` already reads), instead of always
walking `processed_candles`. Add regression coverage asserting that a DEFI `funding_oi`/`returns` lookback check
discovers oracle-price/perp-funding-shaped instrument ids, not DEX-pool ids. Once fixed, resume D1's delta_one leg — the
MTDS manifest already has real, dense, zero-`attempted_failed` data for both `perp_funding` (`2023-05-12..2023-10-31`)
and (need a similar clean-window check) `oracle_prices` to backfill against.

# Progress Log

- 2026-07-30 (slot-3): filed, root-caused via live 2-attempt repro + code trace + manifest spot-checks. D1's onchain leg
  (`perp_funding_rates`, a separate feature_family unaffected by this DEFI delta_one-specific bug) proceeding in
  parallel — see `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo for the combined status.
