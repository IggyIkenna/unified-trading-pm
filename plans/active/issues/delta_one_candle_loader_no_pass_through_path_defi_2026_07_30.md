---
doc_type: issue
title: >-
  delta_one's candle-loading path (DataLoader / _tf_cluster_helper) has no pass-through data-read branch -- every
  funding_oi/returns DEFI run reads 0/N candles for every instrument on every date, deterministically, after the
  (already-fixed) instrument-discovery bug -- ACTIVE VM-SPEND WASTE: 6+ relaunches today hit this identically
summary: >-
  Sibling bug to the already-resolved
  `delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md`
  (features-service@8e62dc30, which fixed `LookbackValidator._discover_instruments()` to source DEFI funding_oi/returns
  instrument lists from the MTDS manifest instead of the DEX-pool `processed_candles` walk). That fix is CONFIRMED
  WORKING -- lookback pre-flight now correctly discovers 412/25 real perp_funding/oracle_prices instruments instead of
  the wrong DEX-pool universe. But the actual feature-COMPUTE step, once past pre-flight, still calls
  `_tf_cluster_helper._load_base_candles()` / `_load_range_candles_with_buffer()`, which unconditionally read via
  `DataLoader.load_candles_with_buffer(data_type=<resolved_type>, timeframe=...)` -- and for DEFI's pass-through data
  types (`perp_funding`, `oracle_prices`; declared `NEEDS_CANDLE_PROCESSING=False` in
  `unified_api_contracts/registry/market_data_categories.py`), MDPS NEVER writes `processed_candles` by design (raw MTDS
  -> features directly, no candle-derivation step). So this candle-read call returns "No upstream MDPS data" for every
  single instrument x date pair, 100% of the time, on every date range tried (a 7-day window and 2 separate multi-year
  full-history windows) -- deterministic, not a data-availability gap. The correctly-discovered instruments (412 for
  funding_oi, confirmed via manifest) then all fail with "0 candles", the honest-absence gate correctly REJECTS the
  resulting empty-write attempt (no FetchEvidence -- working as designed, not itself a bug), and the VM exits 1. **This
  is now costing real, ongoing VM spend**: 10 `features-delta-one-defi-*` VM launches fired TODAY (2026-07-30) against
  this same D1 todo, 6 with a confirmed `exit_code=1` (2 more still running as of this writing, already showing the
  identical "No upstream MDPS data ... (data_type=perp_funding) -- skipping date" pattern live) -- because the plan's D1
  todo checkbox stays `- [ ]` (its done-when is genuinely unmet) it keeps getting redispatched to fresh workers, each of
  whom (reasonably) attempts a plausible variant (narrow window / full-history window / funding_oi / returns) that
  reproduces the SAME deterministic failure every time. Further relaunching without a code fix is pointless -- every
  future attempt will fail identically regardless of date range, window size, or funding_oi-vs-returns choice, because
  BOTH map to pass-through data types for DEFI.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [defi, features-service, delta-one, data-loader, pass-through, candle-loading, data-correctness, vm-spend-waste]
related:
  - /plans/active/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md
  - /plans/active/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
created: "2026-07-30"
author: slot-4 (data_pipeline_failure escalation, DP-VM-001)
source: [DP_VM_EXIT_NONZERO escalation for features-delta-one-defi-20260730-222034]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# What I found

Dispatched as a `data_pipeline_failure` escalation (`wall_type=data_pipeline_failure`, DP-VM-001 `DP_VM_EXIT_NONZERO`)
to relaunch VM `features-delta-one-defi-20260730-222034` (exited `exit_code=1`) per
`codex/15-runbooks/incidents/rb_infra_relaunch.md`. Before relaunching, read the VM's durable GCS logs
(`gs://deployment-scripts-central-element-323112/vm-logs/features-delta-one-defi-20260730-222034/{EXIT_STATUS,run.log,TARBALL_PINS.json}`)
to understand why it failed, per the runbook's own guidance ("if it re-fails the SAME way twice ... STOP relaunching,
file an issue"). Command run:
`features_service --feature-family delta_one --operation compute --mode batch --start-date 2023-06-01 --end-date 2023-06-07 --asset-group DEFI --feature-group funding_oi --timeframe 15m`
-- this is exactly the P2 follow-on todo recommended by the just-landed
`delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md` fix
(features-service@8e62dc30).

## The instrument-discovery fix is confirmed working

```
2026-07-30 22:23:23,937 INFO ✅ Dependencies verified for 2023-06-01/DEFI
2026-07-30 22:24:11,609 INFO Lookback validation PASSED: 25/25 instruments OK
2026-07-30 22:25:08,364 INFO Manifest discovery: 51 captured instruments for DEFI date=2023-06-01 data_type=oracle_prices
2026-07-30 22:25:13,685 INFO Manifest discovery: 25 captured instruments for DEFI date=2023-06-01 data_type=perp_funding
```

Correct, real instrument ids are now discovered (not the old wrong DEX-pool universe) -- `8e62dc30` did exactly what it
was supposed to.

## But the compute step's candle-loading path was never updated for pass-through data types

```
2026-07-30 22:25:20,525 INFO Loading range candles: 2023-06-01 to 2023-06-07 (buffered from 2023-05-31) for 412 instruments at 15m
2026-07-30 22:25:20,613 WARNING No upstream MDPS data for UNISWAP_V3:pool:WMATIC-DAI-30 on 2023-05-31 (data_type=perp_funding) — skipping date
... (repeats for all 412 instruments x all 7 dates, both the 15m cluster AND the 1h cluster)
2026-07-30 22:26:01,569 INFO Loaded range candles for 0/412 instruments (15m)
2026-07-30 22:31:58,924 INFO Loaded range candles for 0/412 instruments (1h)
2026-07-30 22:26:09,852 WARNING empty_confirmed manifest write failed for funding_oi date=2023-06-01: record_empty(reason=SOURCE_RETURNED_ZERO) requires FetchEvidence proving a clean 200+empty fetch ...
2026-07-30 22:32:54,128 ERROR ALL feature groups failed: ['funding_oi']
```

`features_service/delta_one/cli/handlers/_tf_cluster_helper.py`'s `_load_base_candles()` /
`_load_range_candles_with_buffer()` / `_load_one_instrument_range()` call
`self.data_loader.load_candles_with_buffer(instrument_id=..., data_type=data_type, ...)` unconditionally -- there is no
branch that checks `unified_api_contracts.registry.market_data_categories.needs_candle_processing(data_type)` before
choosing a read strategy. For DEFI's `funding_oi` (-> `perp_funding`) and `returns` (-> `oracle_prices`), both declared
pass-through (`NEEDS_CANDLE_PROCESSING["perp_funding"] = False`, `["oracle_prices"] = False`), MDPS never writes
`processed_candles` for these types (confirmed in the sibling issue's own corpus scan: zero
`oracle_prices`/`perp_funding` objects exist under `processed_candles`, on any date, by design -- see
`market_data_processing_service/app/adapters/defi/__init__.py`'s pass-through docstring). So `load_candles_with_buffer`
structurally CANNOT return data for these types -- not a coverage gap, a data-shape mismatch between what the loader
reads (candle-derived OHLCV) and what pass-through data actually is (raw per-instrument scalar/derivative-ticker rows
that MTDS captures directly, never candle-resampled).

This is corroborated by the calculators themselves: `features_service/delta_one/app/calculators/funding_oi.py`'s
`FundingOI.get_required_columns()` returns `["funding_rate", "open_interest"]` and its own `validate()` docstring says
_"Derivative ticker data may not have OHLCV - it has funding/OI columns"_ -- the calculator was ALREADY written
expecting raw derivative-ticker-shaped rows, not OHLCV candles. The candle-loading path upstream of it, however, was
never given a way to source that shape for DEFI's pass-through mapping.

## This is deterministic, not date- or window-dependent -- confirmed across every attempt made today

| VM                                        | feature_group | window                                | result                                                                                                                                              |
| ----------------------------------------- | ------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `features-delta-one-defi-20260730-222034` | funding_oi    | 2023-06-01..2023-06-07                | 0/412 candles, both 15m+1h clusters, exit 1                                                                                                         |
| `features-delta-one-defi-20260730-222059` | returns       | 2023-06-01..2023-06-07                | same shape, exit 1                                                                                                                                  |
| `features-delta-one-defi-20260730-223654` | funding_oi    | 2023-05-12..2026-06-09 (full history) | same "No upstream MDPS data" pattern live (still running as of this writing)                                                                        |
| `features-delta-one-defi-20260730-223716` | returns       | 2022-11-01..2026-07-22 (full history) | failed differently -- a dependency-check miss for the start date -- but the underlying candle-load gap is the same class once past dependency-check |

10 `features-delta-one-defi-*` VMs launched today total (`205659`, `205953`, `210041`, `210821`, `210841` -- pre-fix,
covered by the sibling issue -- plus the 5 above, all POST-fix). Every post-fix attempt that reached the candle-load
step failed identically regardless of date range or window size. **No further relaunch of `funding_oi`/`returns` for
DEFI delta_one will succeed until this is fixed in code** -- this is not an infra/OOM/stall condition the
`rb_infra_relaunch.md` runbook's blind-relaunch actuator can resolve, and its own `≤2 relaunches/(vm-prefix, day)` bound
is already far exceeded (10 today). Per that runbook's own guidance ("if it re-fails the SAME way twice ... STOP
relaunching, file an issue"), **I did not relaunch VM `features-delta-one-defi-20260730-222034` again.**

# Why this matters

Every DEFI delta_one feature_group whose data_type is pass-through (today: `funding_oi`, `returns`, and ~13 more per the
sibling issue's enumeration -- `technical_indicators`, `moving_averages`, `oscillators`, `volatility_realized`,
`momentum`, `candlestick_patterns`, `market_structure`, `round_numbers`, `streaks`, `temporal`, `economic_events`,
`targets`) is structurally unable to complete via this candle-loading path, on any date, until it gains a pass-through
read branch. This blocks the remainder of D1's delta_one leg
(`/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md`) entirely, and every VM launch attempt against it
between now and the fix is guaranteed-wasted compute spend.

# What I did NOT do

Did not patch `_tf_cluster_helper.py` / `DataLoader` -- this is shared code across CEFI/TRADFI/DEFI/PREDICTION (same
craft-scope discipline the prior slot used for the sibling `LookbackValidator` bug: a real design decision about how a
pass-through data type is represented for feature computation -- raw rows re-shaped into a `funding_rate`/
`open_interest`-columned frame keyed by timestamp, most likely, mirroring what the ALREADY-WORKING onchain
`perp_funding_rates_defi.py` calculator does by reading MTDS raw directly -- is out of scope for a one-shot VM-relaunch
escalation to guess at mid-incident. Did not relaunch the VM again (bound exceeded + deterministic failure -- would
waste more compute for a guaranteed-identical result). Did not touch the already-resolved sibling issue doc (its own
scope -- instrument discovery -- is genuinely fixed and unaffected by this).

# Recommended decision

Give `_tf_cluster_helper._load_base_candles()`/`_load_range_candles_with_buffer()` (or the `DataLoader` they call) a
pass-through branch: when `needs_candle_processing(data_type)` is `False`, read the raw MTDS rows for the requested
data_type directly (mirroring the manifest-guided read `_discover_instruments_from_manifest` already added) and present
them to `_acquire_candles`'s consumers as a `pl.DataFrame` shaped the way the calculator's own `get_required_columns()`
expects (`funding_rate`/`open_interest` for `funding_oi`; whatever `returns`'s `oracle_prices`-mapped calculator needs
-- check its `get_required_columns()` before assuming an OHLC-like `close` column suffices). Keep the existing
MDPS-candle path unchanged for candle-processed types (`dex_pool_swaps`/`dex_swaps`/`liquidations`). Add regression
coverage asserting a DEFI `funding_oi`/`returns` run actually loads non-empty data for a known-good manifest window
(e.g. `perp_funding`'s confirmed clean block `2023-05-12..2023-10-31` per the sibling issue) and writes real (not
`record_failed`) rows.

## Todos

- [ ] [BACKEND] P1. Add a pass-through read branch to `_tf_cluster_helper.py`'s candle-loading path (or `DataLoader`)
      keyed on `unified_api_contracts.registry.market_data_categories.needs_candle_processing(data_type)`, sourcing raw
      MTDS rows for pass-through data types and reshaping them to the columns the target calculator's
      `get_required_columns()` declares. Leave candle-processed data_types on the existing path unchanged. Repo:
      features-service. Done when: a DEFI `funding_oi` run over `2023-05-12..2023-10-31` (perp_funding's confirmed clean
      manifest window) loads >0 candles for a majority of the 412 discovered instruments and writes real
      `record_captured` rows (not `record_failed`/empty), verified by a new unit test, and
      `bash scripts/quality-gates.sh` green.
- [ ] [DATA] P2. Once the above lands, resume `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo's delta_one
      leg (funding_oi + returns) over a verified-clean manifest window. Repo: features-service. Done when:
      `features-delta-one-defi` has a populated index and D1's checkbox is flipped citing this evidence.
- [ ] [OPERATOR] P1. Until todo 1 lands, consider parking `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo
      (backlog `priority: 999` + `priority_override: true` + a false prerequisite gating it, per
      `unified-trading-pm/agents/RULES.md` §4 "Park a task") so the AO dispatcher stops redispatching fresh workers into
      the same guaranteed-deterministic-failure loop -- 10 VM launches burned today already, several concurrently
      in-flight as this doc was filed.

# Progress Log

- 2026-07-30 (slot-4, data_pipeline_failure escalation DP-VM-001): filed after declining to relaunch
  `features-delta-one-defi-20260730-222034` a further time (root cause is deterministic, not infra/transient; runbook's
  own relaunch bound already far exceeded). Root-caused via full run.log read + code trace
  (`_tf_cluster_helper.py`/`funding_oi.py`) + cross-referencing 3 other same-day VM logs showing the identical failure
  shape across both feature groups and 3 different date windows.
