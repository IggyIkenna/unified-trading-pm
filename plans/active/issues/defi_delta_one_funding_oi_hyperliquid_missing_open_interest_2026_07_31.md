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
- [x] ✅ [BACKEND] P2. Implement direction B: source `open_interest`/`mark_price`/`index_price` for delta_one
      `funding_oi` from the existing HYPERLIQUID `derivative_ticker` capture (asset_ctxs, per-minute, already in the
      corpus) rather than the OI-less `perp_funding` rows — align the per-minute `derivative_ticker` OI to the
      hourly-settled `perp_funding` grain in the pass-through reshape path
      (`features_service/delta_one/app/core/_passthrough_loader.py` +
      `features_service/delta_one/app/calculators/funding_oi.py`). Repo: features-service. Done when: a DEFI
      `funding_oi` verification-window run over `2023-05-12..2023-10-31` loads non-null `open_interest` for a majority
      of HYPERLIQUID instruments and passes the >50% NaN column-quality gate, verified by a new unit test;
      `bash     scripts/quality-gates.sh` green. **DONE (2026-08-03, slot-8, backend_engineer craft)** —
      `_load_passthrough_range` now, for `data_type="perp_funding"`, recursively loads the same venue+symbol's
      `derivative_ticker` frame and backward-asof-joins its `open_interest`/`mark_price`/`index_price` onto the hourly
      funding rows (nearest known OI reading at-or-before each funding timestamp); `derivative_ticker` itself is
      unaffected. 2 new unit tests (`TestEnrichFundingOIFromDerivativeTicker` in
      `tests/delta_one/unit/test_data_loader.py`) cover the join (exact + nearest-prior match, asserting no unbounded
      recursion via day-load call-count) and the graceful-fallback path; all 130 delta_one data_loader/funding_oi tests
      pass; `bash scripts/quality-gates.sh` green. `features-service@0699c5db`. **Did NOT run a live GCS
      verification-window run** against real HYPERLIQUID data — that half of this todo's done-when is the
      separately-dispatched `[DATA] P3` todo directly below (data_engineering craft, its own `Done when` is exactly that
      run), matching the craft-scope split this issue's own prior sessions already established (backend implements +
      unit-tests; data re-verifies against real infra).
- [x] ✅ [DATA] P3. **RE-ATTEMPTED 2026-08-03 (slot-10, data_pipeline_failure escalation agt-dd3c9e) — DONE, real
      `record_captured` rows confirmed.** Once the [BACKEND] B fix above lands, resume the `funding_oi` leg of
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo over the verified-clean manifest window
      (`2023-05-12..2023-10-31`). Repo: features-service. Done when: a verification-window run writes real
      `record_captured` rows for `funding_oi` (not `record_failed`/rejected-shard). **MET** — see Progress Log entry
      below (`features-delta-one-defi-20260803-055219`, exit_code=0, real `funding_oi` partitions written for the
      majority of the window; `[BACKEND] P1`'s CEFI-bucket fix is confirmed live in production, not just unit tests).
- [x] ✅ [BACKEND] P1. **NEW, this session.** `_enrich_funding_oi_from_derivative_ticker`
      (`features_service/delta_one/app/core/_passthrough_loader.py:345`) is silently failing to find ANY matching
      `derivative_ticker` rows for HYPERLIQUID over `2023-05-12..2023-10-31`, even though real `derivative_ticker` data
      for that exact window is confirmed present on GCS (see Progress Log — dozens of
      `HYPERLIQUID:PERPETUAL:<SYM>-USD@LIN.parquet` objects live under
      `day=2023-07-11/pipeline_mode=batch_hyperliquid/`, an in-window date). The method's own empty-result path
      (`if oi_df.is_empty(): return funding_df`, line 374) is a SILENT no-op with no log line — so absence-of-evidence
      in `run.log` doesn't distinguish "no data" from "join found no match" without instrumenting it. Leading hypothesis
      (unconfirmed, needs a `[BACKEND]` worker's own trace, not guessed at here): a symbol/venue-key mismatch in the
      recursive `_load_passthrough_range(synthetic_id, "derivative_ticker", ...)` call —
      `synthetic_id = f"{venue}:derivative_ticker:{raw_symbol}"` is built from `perp_funding`'s OWN `raw_symbol` (bare,
      e.g. `"ETH"`, per the 2023-era migrated-import filename shape this doc's original investigation cited), but
      `derivative_ticker`'s live filenames use the fully-qualified `HYPERLIQUID:PERPETUAL:ETH-USD@LIN` shape — worth
      checking whether `_gather_passthrough_days`'s day-fetch + `_PASSTHROUGH_SYMBOL_COLUMNS` symbol-column filter
      (`symbol`/`coin`/`market`/`feed`) actually matches against this format, or whether the recursive call's own
      `raw_symbol` extraction (`parts[2] if len(parts) >= 3 else ""` on a `:`-split synthetic_id) is silently
      empty/wrong for this data_type's real symbol representation. Add a log line on the empty-result path first (turns
      future silent failures into a one-line diagnosis) before hunting further. Repo: features-service. Done when: the
      real symbol/matching gap is found + fixed, a new unit test reproduces the SPECIFIC HYPERLIQUID symbol-format shape
      this session found broken (not just the already-covered exact/nearest-prior-asof-match case), and a live
      verification-window re-run (the `[DATA] P3` todo above) writes real `record_captured` rows. **DONE (2026-08-03,
      slot-12, backend_engineer craft)** — the leading hypothesis (symbol-format mismatch) was WRONG; traced the real
      gap myself per the todo's own instruction. Both `perp_funding`'s and the recursive `derivative_ticker` call's
      `raw_symbol` are BLANK for the real production instrument_id (`HYPERLIQUID:PERP_FUNDING:`, a per-venue bundle row
      — matches the actual failed shard ID `HYPERLIQUID:perpetual:/funding_oi` in slot-2's run.log), so NO symbol filter
      ever applies on either side — the real bug is a BUCKET/asset_group mismatch. Confirmed live (bounded single-day
      `gcloud storage ls`, same `2023-07-11` date): `derivative_ticker` for HYPERLIQUID has ZERO objects in the DEFI
      bucket (`market-data-tick-defi-prd-...`) and dozens in the CEFI bucket (`market-data-tick-cefi-prd-...`) —
      HYPERLIQUID's `derivative_ticker` (S3 asset_ctxs OI/mark/index) capture writes exclusively to CEFI since its
      2026-07-06 DeFi->CeFi reclassification, mirroring the EXACT precedent already shipped for this venue in
      `onchain/calculators/perp_funding_rates_defi.py::_resolve_mtds_defi_perp_bucket`. `perp_funding` itself is
      unaffected (confirmed present in the DEFI bucket already, so untouched). Fix: new
      `_resolve_passthrough_source(data_type, venue)` resolves `(bucket, asset_group)` together (never independently, so
      they can't silently mismatch) — defaults to the run's own asset_group, overridden to CEFI only for
      `derivative_ticker` + HYPERLIQUID. Also added the requested log line (plus a matching one on the sibling
      `oi_only.is_empty()` empty-result branch) via a shared `_log_empty_oi_enrichment` helper (kept the enriching
      method under the 50-line cap). 8 new/extended unit tests (`TestResolvePassthroughSource`, `TestLoadPassthroughDay`
      x2, `TestEnrichFundingOIFromDerivativeTicker` x4) — critically, a NEW end-to-end regression
      (`test_real_bug_shape_blank_raw_symbol_wrong_bucket_end_to_end`) drives the real bucket-resolution/needle-filter
      path (does NOT mock `_load_passthrough_day` away, unlike every pre-existing test in this suite) using the REAL
      blank-raw_symbol production shape — this is why the prior `[BACKEND] P2` session's own unit tests passed while the
      real production join still failed (they used a fictitious `"ETH"` raw_symbol and mocked the loader too deep to
      exercise bucket resolution at all). All 18350 features-service tests pass; `bash scripts/quality-gates.sh` green
      (2 full runs). `features-service@6b2282c5` (verified ancestor of `origin/live-defi-rollout`). Did NOT run a live
      GCS verification-window run — that's the `[DATA] P3` todo below (data_engineering craft, its own done-when covers
      exactly that; same craft-scope split this issue's prior sessions established for `[BACKEND] P2`). Session also hit
      a pre-existing, unrelated `features-service` QG red (`tests/onchain/unit/test_smoke_matrix.py`, cross-repo drift
      from a sibling `e2e-testing` commit) — joined the already-open repo-blocker (`RB-417918ff`, filed by slot 13) as a
      waiter rather than duplicate; it resolved independently (`features-service@617388c5`) before this todo shipped.

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
- **2026-08-03 (slot-8, backend_engineer craft) — `[BACKEND] P2` B-implementation SHIPPED.** Extended
  `_load_passthrough_range` (`_passthrough_loader.py`) so `data_type="perp_funding"` recursively loads the same
  venue+symbol's `derivative_ticker` frame (reusing the exact same day-fetch/symbol-filter/timestamp-resolve path, no
  new venue capture) and backward-asof-joins its `open_interest`/`mark_price`/`index_price` onto the hourly funding rows
  — most recent known OI reading at-or-before each funding-settlement timestamp, since the two captures run on
  independent cadences (per-minute vs hourly). Extracted a `_reshape_passthrough` helper to keep
  `_load_passthrough_range` under the 50-line method cap. Added `TestEnrichFundingOIFromDerivativeTicker` (2 tests:
  exact + nearest-prior asof match with a day-load call-count assertion ruling out unbounded recursion; graceful null-OI
  fallback when derivative_ticker is empty) to `tests/delta_one/unit/test_data_loader.py`; all 130 delta_one
  data_loader/funding_oi tests pass; `bash scripts/quality-gates.sh` green. `features-service@0699c5db` (verified
  ancestor of `origin/live-defi-rollout`). Did NOT run a live GCS verification-window run — deferred to the `[DATA] P3`
  todo below (data_engineering craft, separately dispatched, its own done-when covers exactly that).
- **2026-08-03 (slot-2, data_engineering craft, dispatched to
  `delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi-002`) — `[DATA] P3` ATTEMPTED, still
  BLOCKED, new root cause found.** Confirmed `features-service@0699c5db` (the B-implementation) is live in-worktree,
  then launched the real verification-window run this todo calls for: `features-delta-one-defi-20260803-031632` (SPOT,
  `--feature-family delta_one --asset-group DEFI --feature-group funding_oi --timeframe 15m --start-date 2023-05-12 --end-date 2023-10-31`,
  `--launch-mode full`). Dependency-check and lookback-validation both PASSED cleanly (confirms the SIBLING
  `delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md` fix is holding). But every
  date the VM actually processed hit the SAME NaN-rejection this doc originally diagnosed —
  `Rejecting shard HYPERLIQUID:perpetual:/funding_oi: 104 columns exceed NaN threshold — open_interest=100.0%, mark_price=100.0%, index_price=100.0%, open_interest_raw=100.0%, oi_change=100.0%`
  — on every sampled date (2023-10-31, 2023-07-27, and the run's own final terminal date). VM exited `rc=1`,
  `ERROR ALL feature groups failed: ['funding_oi']`. Independently re-verified against the manifest itself (not just the
  log): read the run's own per-VM shard
  (`gs://features-defi-prd-.../\_index/per_vm/features-delta-one-defi-20260803-031632.parquet`, one bounded single-file
  read) — exactly 1 row, `capture_status=attempted_failed`, `error_reason=orchestrator_returned_false`. Zero
  `record_captured` rows anywhere. So the B-implementation's own unit tests (which mock the join inputs) pass, but the
  REAL production join is not finding any matching `derivative_ticker` rows for HYPERLIQUID over this exact window — a
  genuinely NEW bug, not a re-confirmation of the original one. Ruled out data-absence as the cause: confirmed live
  (bounded single-day `gsutil ls`, not a corpus walk) that `derivative_ticker` HYPERLIQUID data genuinely exists
  in-window — dozens of objects under
  `day=2023-07-11/pipeline_mode=batch_hyperliquid/asset_group=cefi/venue=HYPERLIQUID/instrument_type=perpetual/data_type=derivative_ticker/`
  (e.g. `HYPERLIQUID:PERPETUAL:ETH-USD@LIN.parquet`, `...BTC-USD@LIN.parquet`, etc.), so the join has real rows to find
  and isn't matching them. `_enrich_funding_oi_from_derivative_ticker`'s empty-result path
  (`_passthrough_loader.py:374`) is a silent no-op with no log line, so I could not pin the exact failing line without
  either instrumenting it or reproducing the exact `perp_funding` raw_symbol shape for this venue/window — correctly
  left to the new `[BACKEND] P1` todo (backend_engineer craft, not mine to freelance a debug session into, mirroring
  this doc's own established craft-scope split). Did NOT relaunch — the failure is systematic across every processed
  date, not a one-off, so a retry with the same code would reproduce identically. This ALSO means
  `delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md`'s own Todo 2 (`returns` +
  `funding_oi`, D1's checkbox) still cannot flip — `returns` remains complete (per that doc's own 2026-08-02 entry),
  `funding_oi` is now blocked on `[BACKEND] P1` instead of `[BACKEND] P2` (which itself IS done, just insufficient
  against real data). No manifest-integrity issue from this run itself — the one row it wrote is an honest
  `attempted_failed`, not a masked/fake success.
- **2026-08-03 (slot-12, backend_engineer craft) — `[BACKEND] P1` SHIPPED, real root cause found (NOT the leading
  hypothesis).** Traced the silent empty-result gap myself per the todo's own instruction, rather than assuming the
  symbol-format hypothesis. Both `perp_funding`'s manifest-discovered `raw_symbol` AND the recursive `derivative_ticker`
  call's `raw_symbol` are BLANK for the real production instrument_id (a per-venue bundle row,
  `HYPERLIQUID:PERP_FUNDING:`) — confirmed against the real failed shard ID slot-2 logged
  (`HYPERLIQUID:perpetual:/funding_oi`, blank middle segment). So the symbol filter never even engages on either side —
  the hypothesis was a plausible-sounding guess that turned out wrong. The REAL bug:
  `_enrich_funding_oi_from_derivative_ticker`'s recursive load reused `self._get_source_bucket()`, scoped to the run's
  own `asset_group` (DEFI) — but HYPERLIQUID's `derivative_ticker` (S3 asset_ctxs OI/mark/index) capture writes
  EXCLUSIVELY to the CEFI bucket, since HYPERLIQUID was reclassified DeFi->CeFi 2026-07-06 (same precedent already
  shipped for this exact venue in `onchain/calculators/perp_funding_rates_defi.py::_resolve_mtds_defi_perp_bucket`,
  which I found by grepping for how the pattern this module generalised off already solved the identical problem).
  Confirmed live (bounded single-day `gcloud storage ls`, `2023-07-11`, not a corpus walk):
  `market-data-tick-defi-prd-central-element-323112` has ZERO `derivative_ticker` objects for HYPERLIQUID;
  `market-data-tick-cefi-prd-central-element-323112` has dozens. `perp_funding` itself is unaffected (already correctly
  reads from the DEFI bucket, confirmed present there too — untouched by the fix). Shipped
  `_resolve_passthrough_source(data_type, venue)`, resolving `(bucket, asset_group)` TOGETHER (never as two independent
  lookups, so the bucket and the needle-filter's `asset_group=` path segment can never silently mismatch — a mismatch
  wouldn't error, `list_blobs` would just return zero objects). Also added the requested log line on the empty-result
  path (plus its sibling `oi_only.is_empty()` branch, same silent-no-op class) via a shared `_log_empty_oi_enrichment`
  helper (needed to keep `_enrich_funding_oi_from_derivative_ticker` under the 50-line QG cap after adding both warnings
  — first full QG run caught this at 53L, fixed + re-ran green). 8 new/extended unit tests:
  `TestResolvePassthroughSource` (4, unit-level bucket/asset_group resolution), `TestLoadPassthroughDay` (+2, confirm
  the CEFI bucket + `asset_group=cefi/` needle are actually used for HYPERLIQUID+derivative_ticker and that
  `perp_funding` is unaffected), `TestEnrichFundingOIFromDerivativeTicker` (+2 warning-log tests via caplog, verified
  against real polars null-Datetime semantics before writing, not assumed; +1 critical end-to-end regression,
  `test_real_bug_shape_blank_raw_symbol_wrong_bucket_end_to_end`, which does NOT mock `_load_passthrough_day` away
  unlike every pre-existing test in this class — drives the real bucket-resolution + needle-filter path down to a mocked
  storage client using the REAL blank-raw_symbol shape). This last test is the direct fix for why the prior
  `[BACKEND] P2` session's own unit tests passed while the real production join still failed: they used a fictitious
  `"ETH"` raw_symbol (matching the doc's original — also-wrong — hypothesis) and mocked `_load_passthrough_day` away
  entirely, so they never exercised bucket resolution at all. All 18350 features-service tests pass twice (once before
  committing to verify WIP after a session restart, once after committing on the real SHA per the QG-sentinel ordering
  rule); `bash scripts/quality-gates.sh` green. `features-service@6b2282c5` (independently verified ancestor of
  `origin/live-defi-rollout`, not just trusting quickmerge's own "Landed" message). Session also hit a pre-existing,
  unrelated `features-service` QG red (`tests/onchain/unit/test_smoke_matrix.py`,
  `TypeError: _verify_test_manifest() takes 3 positional arguments but 4 were given` — cross-repo drift from a sibling
  `e2e-testing` commit landing via the background fresh-pull cron mid-session) — verified it was unrelated to this diff
  (different feature family, dynamically loads a script from a repo I never touched, commit timestamp fell exactly
  between two consecutive QG runs of mine), found slot 13 had already independently confirmed + repo-blocked it
  (`RB-417918ff`, tracked in `features_smoke_matrix_verification_findings_2026_08_01.md`), joined as a waiter rather
  than duplicating; it resolved on its own (`features-service@617388c5`) before this todo needed to ship. Separately,
  this session's original QG-green state was lost to an orchestrator session restart mid-task; recovered cleanly via
  `git cherry-pick --no-commit` of the auto-preserved `chore(orphan-wip)` commit the orchestrator's dirty-state gate had
  committed on my behalf (`f3e899e0`, clean cherry-pick, no conflicts, confirmed byte-identical to the pre-restart diff)
  rather than redoing the investigation. Did NOT run a live GCS verification-window run — that's the `[DATA] P3` todo
  above (data_engineering craft, its own done-when covers exactly that; same craft-scope split this issue's prior
  sessions established for `[BACKEND] P2`).
- **2026-08-03 (slot-10, `data_pipeline_failure` escalation agt-dd3c9e) — `[DATA] P3` DONE, live verification
  confirmed.** Arrived via an unrelated DP-VM-001 (`DP_VM_EXIT_NONZERO`) alert on
  `features-delta-one-defi-20260803-031632` (this exact shard — slot-2's own `[DATA] P3` attempt above, still running
  the pre-`[BACKEND] P1` code). Root-caused it back to this doc before considering a relaunch: log showed
  `Rejecting shard HYPERLIQUID:perpetual:/funding_oi: 104 columns exceed NaN threshold — open_interest=100.0%, mark_price=100.0%, index_price=100.0%`
  across every processed date, matching this issue's own diagnosis exactly. Found ONE more contributing cause before
  relaunching: the VM code tarball (`gs://deployment-scripts-central-element-323112/code/features-service-code.tar.gz`)
  was pinned to `commit_sha 617388c5`, which PREDATES `[BACKEND] P1`'s fix (`features-service@6b2282c5`) —
  `git merge-base --is-ancestor 617388c5 6b2282c5` confirmed 617388c5 is an ancestor, i.e. strictly older. A same-args
  relaunch against that stale tarball would have reproduced the identical failure (the exact class this doc's own
  `features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` sibling issue already documents:
  `LC_TARBALL_FRESHNESS` defaults to `warn`, not `enforce`, so a stale tarball launches silently). Rebuilt
  - republished via `bash scripts/vm/create-code-tarballs.sh --include features-service` from a clean
    `origin/live-defi-rollout` checkout (features-service HEAD `c092df50`, a `6b2282c5` descendant); confirmed the new
    manifest (`commit_sha: c092df50...`) before relaunching. Relaunched the identical shard —
    `FEATURE_GROUP=funding_oi TIMEFRAME=15m bash scripts/vm/launch-features-vm.sh --feature-family delta_one --asset-group DEFI --start-date 2023-05-12 --end-date 2023-10-31 --launch-mode full`
    — as `features-delta-one-defi-20260803-055219` (SPOT), with the launcher's own `lc_verify_tarball_freshness`
    confirming "all 5 tarball(s) current" before boot. Polled to terminal state (background, ~8min run): `exit_code=0`,
    `status=completed`, run.log shows `Completed 1/1 feature groups (succeeded=['funding_oi'], failed=[])` /
    `Processing completed successfully`; grep counts across the full log — `Wrote 2/2 daily partitions` ×84,
    `Wrote 1/2 daily partitions` ×282 (real captured `funding_oi` output for the large majority of the window), vs
    `Insufficient data for reliable features` ×140 (still-correct, honest skips for the earliest slice of the window
    that hasn't yet accumulated the calculator's 500-candle rolling-window minimum — a genuine data-ramp-up condition,
    not a bug, shard-isolated rather than fatal this time). ManifestWriter's final per-VM shard write:
    `features-defi-prd-.../\_index/per_vm/features-delta-one-defi-20260803-055219.parquet` (599 total entries, 22 new,
    `process_final=True`). This is real, live-verified proof that `[BACKEND] P1`'s CEFI-bucket-resolution fix works in
    production (not just its unit tests) — flipping `[DATA] P3` above. Did NOT touch `[BACKEND] P1`/P2's own text (their
    craft's own DONE entries stand as written). Registry's `rows_out=0` counter did not reflect the real captured
    partitions — a pre-existing, separate cosmetic gap in this deployment's row-counting instrumentation, not filed as a
    new issue here (out of this escalation's scope; noted for whoever next touches `deployment_heartbeat.py`'s row
    counters). Pinged the authoring slot (`dp-fleet-monitor`) with this outcome and closed the DP-VM-001 escalation via
    `/done` — no new issue doc needed, this one already covered it end-to-end.
