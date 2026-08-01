---
doc_type: issue
title: >-
  delta_one funding_oi feature group is structurally infeasible for DEFI/HYPERLIQUID -- raw perp_funding rows NEVER
  carry open_interest/mark_price/index_price, in either the historical-migrated or the live-cron capture format, so
  every date fails the >50% NaN column-quality gate regardless of the (now-fixed) pass-through loader
summary: >-
  Sibling finding to the already-resolved `delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`
  (features-service@a5a5bf7d, which added the pass-through read branch so DEFI delta_one funding_oi/returns runs
  actually load raw MTDS rows instead of probing the nonexistent processed_candles path). That fix IS confirmed working
  -- the loader now reads real HYPERLIQUID perp_funding rows. But `funding_oi.py`'s `get_required_columns()` requires
  `["funding_rate", "open_interest"]`, and a direct inspection of the raw parquet (both the 2023-era
  `_migrated_hyperliquid_*` historical import AND a 2026-06-09 live-cron-captured file) shows HYPERLIQUID's perp_funding
  schema NEVER populates `open_interest` (nor `mark_price`/`index_price`) -- the live-cron schema doesn't even carry
  those columns at all (only `funding_rate`/`premium`/`timestamp`/identity columns); the older migrated-import schema
  has `long_oi_usd`/ `short_oi_usd`/`mark_price` columns present but NaN in every sampled row. This is a genuine
  data-shape gap, not a loader bug -- every `funding_oi` run for DEFI will keep failing the column-quality gate (`>50%
  NaN` rejection) on every date, deterministically, until either (a) MTDS's HYPERLIQUID adapter starts capturing OI (if
  Hyperliquid's API even exposes it at this grain), or (b) the calculator's column requirement is relaxed/reworked to
  not need OI.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service, market-tick-data-service]
scope: [engineer]
tags: [defi, features-service, delta-one, funding-oi, open-interest, data-availability, hyperliquid]
related:
  - /plans/active/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md
  - /plans/active/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
created: "2026-07-31"
source: [D1 todo delta_one leg verification-window dry-run, features-delta-one-defi-20260730-234947]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    /plans/active/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    features-service/features_service/delta_one/app/calculators/funding_oi.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py,
  ]
---

# What I found

Dispatched to `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo (delta_one leg), after confirming
`features-service@a5a5bf7d` (the pass-through candle-loader fix) is live in my worktree. Per the todo's own "re-read
before any VM launch" lesson, launched a `--launch-mode dry` verification-window run first
(`features-delta-one-defi-20260730-234947`, `funding_oi`, `2023-05-12..2023-10-31` -- the exact clean-manifest window
the sibling issue's own todo 1 recommended for verification) rather than committing straight to a full-history run.

## The pass-through fix IS working -- data loads now

```
2026-07-30 22:25:20,525 INFO Loading range candles: 2023-06-01 to 2023-06-07 ... for 412 instruments at 15m
```

(from the earlier pre-fix run) is gone. This run instead progressed past dependency-check + lookback validation cleanly
and reached the actual per-shard processing step -- no more "No upstream MDPS data" warnings.

## But every date fails a DIFFERENT gate -- the reshaped frame is >50% NaN

```
2026-07-30 23:56:36,389 WARNING Rejecting shard HYPERLIQUID:perpetual:/funding_oi: 104 columns exceed NaN threshold
  — open_interest=100.0%, mark_price=100.0%, index_price=100.0%, open_interest_raw=100.0%, oi_change=100.0%
2026-07-30 23:56:36,391 INFO Completed 0/1 instruments for funding_oi
...
2026-07-30 23:57:46,489 ERROR ALL feature groups failed: ['funding_oi']
```

Confirmed identically on BOTH sampled dates in the window (`2023-07-11`, `2023-10-31`) -- deterministic, not a one-off.

## Root cause: HYPERLIQUID's raw perp_funding data never carries OI/mark/index, in either capture era

Downloaded + inspected two real raw parquets directly (not simulated):

- `raw_tick_data/.../day=2023-07-11/.../venue=HYPERLIQUID/.../data_type=perp_funding/ETH.parquet` (24 rows, the
  `_migrated_hyperliquid_*` historical-import schema, `schema_version=9`): HAS columns `long_oi_usd`, `short_oi_usd`,
  `mark_price`, `index_price` (via `premium`) -- but every sampled row has `mark_price=NaN`, and `long_oi_usd`/
  `short_oi_usd` are also NaN in the same rows. Even if the reshape function were extended to map
  `long_oi_usd`+`short_oi_usd` -> `open_interest` (it currently doesn't -- only `funding_rate`/`funding_rate_long`
  aliasing exists), the underlying values are themselves absent for this era.
- `raw_tick_data/.../day=2026-06-09/.../venue=HYPERLIQUID/.../data_type=perp_funding/ETH.parquet` (live-cron capture,
  most recent schema): columns are just
  `protocol, coin, funding_rate, premium, timestamp_ms, timestamp, symbol, instrument_id, venue, chain, instrument_type, data_type, available_at`
  -- `open_interest`/`mark_price`/ `index_price`/`long_oi_usd`/`short_oi_usd` don't exist in this schema AT ALL, not
  even as null columns.

So this is not a reshape-mapping bug (unlike the sibling column-name gaps `derivative_ticker`'s comment already
anticipates for GMX/Aster/Extended) -- HYPERLIQUID's MTDS adapter has never captured open interest for perp_funding, in
any era sampled. `funding_oi.py`'s `get_required_columns() = ["funding_rate", "open_interest"]` hard-requires a field
this venue's capture never produces.

## Contrast: the `returns` (oracle_prices) leg does NOT have this problem

Spot-checked the same date's `oracle_prices` raw data (`CHAINLINK/ETH_USD.parquet`, `2023-07-11`): `price` column is
real and populated (`1867.703354`, non-null). `returns.py`'s `get_required_columns() = ["open", "high", "low", "close"]`
maps cleanly from a single populated `price` scalar via `_reshape_passthrough_price()`'s `open=high=low=close=price`
shape. No blocker expected here -- launched a separate dry-run to confirm (`features-delta-one-defi-20260731-000219`);
see this todo's own Progress Log entry for the result.

# Why this matters

The D1 backfill todo's done-when requires BOTH `funding_oi` and `returns` legs to populate `features-delta-one-defi`'s
index. `returns` is expected to clear once verified. `funding_oi` cannot clear via any code fix to the loader/reshape
layer alone -- MTDS's HYPERLIQUID adapter would need to start capturing OI (if Hyperliquid's public API even exposes
per-symbol OI at the `perp_funding` polling cadence -- not confirmed either way in this session), or the calculator's
requirement needs to be relaxed to tolerate a missing OI signal (e.g. compute `basis_bps`-only features and skip the
OI-derived ones), which is a design call, not a backfill-session fix.

# What I did NOT do

Did not touch `funding_oi.py`'s `get_required_columns()` or the MTDS HYPERLIQUID adapter -- both are real design
decisions (does the product want partial funding-only features, or is OI capture worth adding to the adapter) that a
one-shot backfill dispatch shouldn't guess at, mirroring the craft-scope discipline the two sibling issues on this same
chain already established. Did not relaunch `funding_oi` against a different window -- the failure is
column-shape-deterministic, not date-dependent, so no window will produce a different result without one of the two
fixes above.

# Recommended decision

- [ ] [OPERATOR] P2. Decide the fix direction for `funding_oi` DEFI/HYPERLIQUID: (a) extend the MTDS HYPERLIQUID
      perp_funding adapter to also capture open interest, if the venue's API exposes it at this polling grain -- the
      more correct fix if feasible; or (b) rework `funding_oi.py` to degrade gracefully when OI is absent (compute
      funding/basis features only, mark OI-derived columns as intentionally-null rather than failing the whole shard) --
      the pragmatic fix if OI genuinely isn't available from HYPERLIQUID at this endpoint. Either requires a repo
      owner's judgment call, not a blind backfill-session guess.
- [ ] [DATA] P3. Once a fix direction lands, resume the `funding_oi` leg of
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo over the verified-clean manifest window
      (`2023-05-12..2023-10-31`). Repo: features-service. Done when: a verification-window run writes real
      `record_captured` rows for `funding_oi` (not `record_failed`/rejected-shard).

# Progress Log

- 2026-07-31 (slot-2, data_engineering craft, D1 todo dispatch): filed after confirming the pass-through loader fix
  (a5a5bf7d) works but funding_oi still fails deterministically on a structural OI-absence gap, via direct raw-parquet
  inspection across two capture eras (not simulated/guessed). Did not relaunch `funding_oi` further -- deterministic,
  fix-direction is genuinely operator/repo-owner scoped.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
