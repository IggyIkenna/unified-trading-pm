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

# ⚠️ 2026-08-02 UPDATE — VERDICT OVERTURNED: OI _IS_ available at source (already in the corpus under `derivative_ticker`)

The original "structurally infeasible" verdict below inspected ONLY `perp_funding` (Hyperliquid's `/info fundingHistory`
REST endpoint, which genuinely returns just `fundingRate`/`premium`/`time` — no OI). It never checked
`derivative_ticker`, which MTDS captures from Hyperliquid's **S3 `asset_ctxs` archive** — and that archive DOES carry
open interest. `market_tick_data_service/adapters/hyperliquid_s3.py::_parse_asset_ctxs_csv` already parses
`open_interest`, `mark_price` (`mark_px`), `index_price` (`oracle_px`), `funding`, `premium`, `mid_px`, `day_ntl_vlm`.

**Evidence (direct parquet read, not simulated), same date slot-2 declared infeasible (2023-07-11), HYPERLIQUID ETH-USD
`derivative_ticker`:** 1442 rows (per-minute), `open_interest` 1442/1442 non-null & **all non-zero** (e.g. 427.7569),
`mark_price` 1442/1442 non-zero (1879.84…), `index_price` 1442/1442 non-zero (1880.4…). Confirmed the same
`derivative_ticker` prefix exists for HYPERLIQUID across all three eras (2023-07-11, 2024-06-01, 2026-06-09) in
`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=.../venue=HYPERLIQUID/instrument_type=perpetual/data_type=derivative_ticker/`.

Per the operator's interim guidance (reject C; investigate OI-availability first; **OI available → direction B**), the
fix direction is therefore **B**, and it does NOT require adding a new venue capture — the OI already exists in the
corpus under `derivative_ticker`. The remaining work is a scoped features-service change to source
`open_interest`/`mark_price`/`index_price` for delta_one `funding_oi` from the existing `derivative_ticker` capture
(per-minute) aligned to the hourly-settled `perp_funding` grain. Final B-implementation shape + effort is
repo-owner-ratifiable, but the precondition (OI-availability) is now CONFIRMED, not open. See 2026-08-02 Progress Log.

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

- [x] ✅ [OPERATOR] P2. Fix-direction RULED = **B** (2026-08-02): OI-availability is CONFIRMED at source (Hyperliquid
      `asset_ctxs` archive, already captured under `derivative_ticker` — see the 2026-08-02 UPDATE banner + Progress
      Log). Per the operator's own interim sequencing (OI available → B), C (descope) is rejected and A (degrade) is
      unnecessary. The final B-implementation shape/effort is repo-owner-ratifiable but the direction is settled.
- [ ] [BACKEND] P2. Implement direction B: source `open_interest`/`mark_price`/`index_price` for delta_one `funding_oi`
      from the existing HYPERLIQUID `derivative_ticker` capture (asset_ctxs, per-minute, already in the corpus) rather
      than the OI-less `perp_funding` rows — align the per-minute `derivative_ticker` OI to the hourly-settled
      `perp_funding` grain in the pass-through reshape path
      (`features_service/delta_one/app/core/_passthrough_loader.py` +
      `features_service/delta_one/app/calculators/funding_oi.py`). Repo: features-service. Done when: a DEFI
      `funding_oi` verification-window run over `2023-05-12..2023-10-31` loads non-null `open_interest` for a majority
      of HYPERLIQUID instruments and passes the >50% NaN column-quality gate, verified by a new unit test;
      `bash     scripts/quality-gates.sh` green.
- [ ] [DATA] P3. Once the [BACKEND] B fix above lands, resume the `funding_oi` leg of
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo over the verified-clean manifest window
      (`2023-05-12..2023-10-31`). Repo: features-service. Done when: a verification-window run writes real
      `record_captured` rows for `funding_oi` (not `record_failed`/rejected-shard).

# Progress Log

- 2026-07-31 (slot-2, data_engineering craft, D1 todo dispatch): filed after confirming the pass-through loader fix
  (a5a5bf7d) works but funding_oi still fails deterministically on a structural OI-absence gap, via direct raw-parquet
  inspection across two capture eras (not simulated/guessed). Did not relaunch `funding_oi` further -- deterministic,
  fix-direction is genuinely operator/repo-owner scoped.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **2026-08-02 (slot-8, data_engineering craft) — OI-availability investigation (operator's B-precondition) CONCLUDED:
  OI IS available; original "structurally infeasible" verdict OVERTURNED.** Operator/main gave interim guidance
  (disposition:partial): reject C, investigate OI-availability at source first, then B (if available) / A (if not). I
  traced the two capture paths: (1) `perp_funding` uses `/info fundingHistory` (`_perp_funding_hyperliquid.py`) —
  returns only `fundingRate`/`premium`/`time`, genuinely no OI (this is what slot-2 correctly saw); (2)
  `derivative_ticker` uses the Hyperliquid **S3 `asset_ctxs` archive** (`hyperliquid_s3.py::_parse_asset_ctxs_csv`)
  which DOES capture `open_interest`/`mark_price`/`index_price`/`funding`/`premium`/`mid_px` — slot-2 never checked this
  path. Verified against real corpus (direct parquet read):
  `gs://market-data-tick-cefi-prd-.../day=2023-07-11/.../venue=HYPERLIQUID/ .../data_type=derivative_ticker/HYPERLIQUID:PERPETUAL:ETH-USD@LIN.parquet`
  — 1442 per-minute rows, `open_interest` 1442/1442 non-null & all non-zero (427.7569…), `mark_price`/`index_price`
  likewise fully populated; same `derivative_ticker` prefix confirmed present for HYPERLIQUID on 2023-07-11, 2024-06-01,
  2026-06-09. So OI is available at source AND already in the corpus — no new venue capture needed. Per the operator's
  firm sequencing this settles the fix-direction to **B** (marked the `[OPERATOR] P2` resolved above, per the
  retag-on-resolve rule) and reduces it to a scoped features-service change (new `[BACKEND] P2` todo above): join the
  existing per-minute `derivative_ticker` OI to the hourly `perp_funding` grain in the delta_one pass-through reshape.
  Did NOT implement the B fix (repo-owner- ratifiable per operator guidance; it's a distinct backend_engineer todo) and
  did NOT relaunch (no fix has landed — a relaunch would still fail the NaN gate). Method note: read one small parquet
  via the repo `.venv` (bounded, single file — no whole-corpus walk).
