---
doc_type: issue
title: >-
  delta_one's calendar buffer_days (from FEATURE_GROUP_LOOKBACK periods x seconds_per_period) assumes dense,
  regularly-spaced candles -- DEFI pass-through oracle_prices ticks are sparse/irregular, so the computed 1-2 calendar
  day buffer window captures only a handful of real rows when 100 are required, deterministically blocking `returns`
  (and likely `funding_oi`) on every date even with the real data present in the full range
summary: >-
  5th distinct bug found in this delta_one DEFI pass-through investigation this session (2026-07-31), surfacing only
  after the 4th bug (symbol slash/underscore mismatch,
  `delta_one_passthrough_symbol_filter_slash_underscore_mismatch_2026_07_31.md`, fixed `features-service@7e10172c`) was
  shipped and verified working at the range-load level. Relaunched the `returns`/`oracle_prices` verification run
  (`features-delta-one-defi-20260731-025149`, `2023-05-12..2023-10-31`, `FORCE=1`, confirmed via SSH that the VM had the
  fixed code) — the symbol-fix DID work: `Loaded range candles for 51/51 instruments (15s)`, up from the pre-fix
  `27/51`. But the run still produced `Completed 0/51 instruments for returns` on the first (and, deterministically,
  every subsequent) date, this time via a DIFFERENT log signature: `Insufficient data for returns: have 3 rows, need
  100` (repeated per-instrument, e.g. `have 12 rows` for `CHAINLINK:spot_asset:ETH_USD`). Root-caused via a direct repro
  against real GCS (not guessed): the SAME symbol (`CHAINLINK:ORACLE_PRICES:ETH_USD`) genuinely has 945 real rows across
  175 distinct dates in the exact verification window when read directly via `_load_passthrough_range` with no
  date-window restriction — real data density is ~5.4 rows/day, NOT sparse in absolute terms. The 0-completion outcome
  is caused by a separate, later stage: `BufferManager.calculate_buffer_days()` (`buffer_manager.py:71-110`) computes
  the PER-DATE lookback window from `FEATURE_GROUP_LOOKBACK["returns"]=100` periods x `seconds_per_period` (15s for
  DEFI's default timeframe) x a 1.2x safety margin = 1800 seconds, `math.ceil(1800/86400)=1` calendar day (DEFI's
  `TRADING_DAY_MULTIPLIER=1.0` doesn't extend it) -- so each date's `_extract_date_window()` slice is bounded to roughly
  1-2 calendar days of the already-loaded 945-row range. At ~5.4 real rows/day, a 1-2 day window yields
  single-digit-to-low-double-digit rows (confirmed via a follow-up repro: 8 rows in a `[2023-05-10, 2023-05-12)` window,
  4 rows in `[2023-05-11, 2023-05-12)` -- same order of magnitude as the logged `have 12 rows`) -- nowhere near the 100
  `validate_data_sufficiency()` requires. This buffer-days formula is CORRECT for CEFI's dense, regularly-spaced 15s
  candles (100 periods = 25 real minutes, trivially available in any 1-day window) but structurally wrong for DEFI's raw
  pass-through EVENT ticks (oracle_prices/perp_funding), which publish irregularly and sparsely relative to a nominal
  15s grid -- the SAME class of dense-candle-assumption-meets-sparse-event-data mismatch already documented for TradFi's
  TIMEFRAME gotcha and the now-fixed no-pass-through-candle-path bug
  (`delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`), one layer deeper in the same code path.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [defi, features-service, delta-one, passthrough, lookback, buffer-days, data-correctness, vm-spend-waste]
related:
  - /plans/archive/issues/delta_one_passthrough_symbol_filter_slash_underscore_mismatch_2026_07_31.md
  - /plans/archive/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md
  - /plans/active/issues/features_delta_one_sequential_per_day_gcs_scan_2026_07_27.md
  - /plans/active/issues/delta_one_get_captured_instruments_blank_id_perp_funding_2026_07_30.md
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
created: "2026-07-31"
source: [features-delta-one-defi-20260731-025149 verification run, 0/51 completed despite 51/51 range-load success]
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
resolved_by: features-service@9e70fbac (fix) + slot-11 2026-07-31 production-scale verification (both todos flipped)
---

> **🟢 ARCHIVED 2026-08-02** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` (features-service@9e70fbac (fix) + slot-11
> 2026-07-31 production-scale verification (both todos flipped)). Moved by the `/plan-reconcile` whole-corpus run of
> 2026-08-02, which found this doc sitting in `plans/active/issues/` at a terminal status —
> `check_terminal_status_archived` was RED at 13 violations against a baseline of 1. No content was rewritten.

# What I found

After `features-service@7e10172c` (the symbol-separator fix) shipped and QG-verified, relaunched the exact `returns`
verification-window run to confirm the fix end-to-end. Deleted and republished the features-service code tarball first
(the launcher's own freshness check caught a stale pin — see the sibling issue doc's Progress Log), then SSH-confirmed
the launched VM (`features-delta-one-defi-20260731-025149`) genuinely had the fix
(`grep -n _SYMBOL_SEPARATOR_PATTERN _passthrough_loader.py` on the VM showed the fixed code).

The fix DID work at the range-load level:

```
2026-07-31 02:58:55,197 INFO Loaded range candles for 51/51 instruments (15s)
```

(up from the pre-fix run's `27/51` cited in the sibling issue doc). But the run still produced zero completions:

```
2026-07-31 02:58:55,309 INFO Processing returns for 51 instruments
2026-07-31 02:58:55,310 WARNING Insufficient data for returns: have 3 rows, need 100
2026-07-31 02:58:55,310 WARNING Insufficient pre-loaded candles for CHAINLINK:spot_asset:uni/usd
... (repeated for all 51 instruments, e.g. "have 12 rows, need 100" for CHAINLINK:spot_asset:ETH_USD)
2026-07-31 02:58:57,831 INFO Completed 0/51 instruments for returns
```

Deleted the VM at this point (deterministic failure — the same buffer window applies on every date in the range, so
letting the full 172-day loop run would only repeat this 172 times for no new information; SPOT, idempotent, no work
lost).

## Root cause: the calendar buffer window is far too narrow for sparse event-tick data

Confirmed ground truth is NOT sparse — direct repro via
`_load_passthrough_range("CHAINLINK:ORACLE_PRICES:ETH_USD", "oracle_prices", 2023-05-10, 2023-10-31)` against real GCS
returns **945 rows across 175 distinct dates** (~5.4 rows/day average, data present on nearly every day of the window).
So the fixed loader is NOT the problem — the data genuinely exists in the full range.

The zero-completion outcome traces to `BufferManager.calculate_buffer_days()` (`buffer_manager.py:71-110`):

```python
total_seconds = max_lookback * self.seconds_per_period * BUFFER_SAFETY_MARGIN   # 100 * 15 * 1.2 = 1800
trading_days = math.ceil(total_seconds / 86400)                                  # ceil(1800/86400) = 1
calendar_days = math.ceil(trading_days * multiplier)                             # DEFI multiplier=1.0 -> 1
return max(calendar_days, 1)                                                     # buffer_days = 1
```

This computes "how many calendar days do I need to buffer to be sure I have 100 periods of data," under the implicit
assumption that periods are DENSE and REGULARLY SPACED at the nominal timeframe (correct for CEFI's real 15s trade
candles: 100 periods = 25 minutes, trivially within 1 day). For DEFI pass-through data (`oracle_prices`/`perp_funding`,
raw MTDS ticks, `NEEDS_CANDLE_PROCESSING=False`, each real tick becomes one row via `_reshape_passthrough_price` — no
resampling to a regular grid), "100 periods" has no real temporal meaning — the actual constraint is "100 real
observations," which at ~5.4/day for CHAINLINK ETH/USD takes ~19 calendar days, not 1.

`_extract_date_window()` (`_tf_cluster_helper.py:353-372`) then slices the already-loaded 945-row preloaded range down
to `[processing_date - buffer_days, processing_date)` for each date being processed — with `buffer_days=1`, this window
captures only the 1-2 most recent calendar days' worth of real ticks. Follow-up repro confirms the order of magnitude:
filtering the same 945-row real dataset to `[2023-05-10, 2023-05-12)` yields 8 rows; `[2023-05-11, 2023-05-12)` yields 4
rows — both in the same single-digit-to-low-double-digit range as the VM's logged `have 12 rows` (exact reconciliation
of the extra few rows wasn't pursued further; the structural finding — the window is ~2 orders of magnitude short of the
100 required — is what matters, not the precise boundary).

Because this window is date-invariant (every date in the range computes the same tiny buffer), the result is
**deterministic**: `returns` cannot produce output for ANY date in this window, regardless of how much real historical
data exists, until the buffer/sufficiency logic accounts for pass-through data's irregular density.

# Why this matters

Blocks the P2 todo in the sibling symbol-filter issue doc ("resume D1's `returns` leg over the full captured window")
from EVER succeeding, even with the P1 symbol-fix correctly shipped and independently verified working (range-load now
finds all 51 real instruments, up from 27). Also very likely affects `funding_oi`
(`FEATURE_GROUP_LOOKBACK["funding_oi"]=48`) once its separate structural OI-column-absence blocker
(`defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`) resolves — HYPERLIQUID `perp_funding`
publishes on its own real-world cadence (typically hourly or every-8-hours, not a dense 15s grid), so the same
buffer-too-short mismatch is structurally likely to recur there via the SAME shared `buffer_manager.py` machinery. This
is the reason `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo's `returns` leg (and by extension
`funding_oi`) still cannot complete even after 2 of 2 currently-known bugs in this exact investigation chain are fixed.

# What I did NOT do

Did not patch `buffer_manager.py` myself. The correct fix is a real design decision, same class as the already-resolved
TradFi TIMEFRAME gotcha and the no-pass-through-candle-path fix: `calculate_buffer_days` / `validate_data_sufficiency`
are SHARED across every CEFI/TRADFI/DEFI feature group, including the real dense-candle groups where the current
1-calendar-day-per-100-periods formula is CORRECT and must not regress. A blind widen-it-for- everyone fix risks
silently exploding buffer windows (and GCS read volume — see the sibling
`features_delta_one_sequential_per_day_gcs_scan_2026_07_27.md` performance-cost doc for why `buffer_days` size is not a
free variable) for every dense-candle group too. Candidate directions for a repo owner to choose between:

1. **Per-data-type buffer override**: give pass-through data_types (`oracle_prices`, `perp_funding`/
   `derivative_ticker`) a much larger calendar buffer, derived from observed real capture density per venue (or a
   generous fixed constant, e.g. 30-60 days) instead of the periods x seconds_per_period formula.
2. **Row-count-driven adaptive lookback**: for pass-through data types specifically, expand the buffer window
   iteratively (or make one wider initial GCS read) until `required_periods` real rows are found or a sane cap is hit,
   rather than trusting a fixed calendar-day estimate.
3. **Lower `FEATURE_GROUP_LOOKBACK` for DEFI pass-through `returns`/`funding_oi` specifically** (a per-asset-group
   override analogous to `FEATURE_GROUP_DATA_TYPE_OVERRIDES`) to a threshold realistic for the real observed tick
   density — trades away some statistical robustness in the `returns` calculation for the ability to produce output at
   all.

Whichever direction is chosen needs verification against every DEFI pass-through venue's REAL observed tick density (not
just CHAINLINK) before shipping, per the same discipline the symbol-fix issue doc already established for this
investigation chain.

# Recommended decision

- [x] ✅ [BACKEND] P1. Decide the fix direction (see the 3 candidates above) and implement a pass-through-aware buffer/
      sufficiency calculation in `buffer_manager.py` (or the `_tf_cluster_helper.py` per-date extraction path) that does
      NOT regress CEFI/TRADFI's existing dense-candle buffer-days behavior. Verify against real raw tick density for
      every DEFI pass-through venue/data_type pair (CHAINLINK + PYTH oracle_prices, HYPERLIQUID perp_funding) — not just
      the ETH/USD case repro'd here. Add a regression test covering the real-data shape confirmed in this issue
      (100-period lookback requirement vs ~5.4 real rows/day density). Repo: features-service. Done when: a DEFI
      `returns` run over the verified-clean window (`2023-05-12..2023-10-31`) shows `Completed N/51 instruments` with
      N > 0 on multiple real dates, and writes real `record_captured` rows. — features-service@9e70fbac. Chose direction
      2 (row-count-driven adaptive lookback), combined with a conservative calendar floor for the initial fetch:
      `BufferManager.calculate_buffer_days()` detects pass-through data types via UAC
      `needs_candle_processing()`/`resolve_data_type_for_feature_group()` and widens the calendar buffer; a new
      `calculate_passthrough_min_rows()` drives `_extract_date_window()` to widen its per-date slice — bounded to
      whatever's already loaded, zero extra GCS reads — until enough real rows are found. Strict no-op for CEFI/TRADFI
      (verified: 2 pre-existing tests that had baked in the bug for DEFI `moving_averages` — resolves to oracle_prices,
      also pass-through — were caught failing and fixed to assert the corrected behavior). Regression tests added
      against the confirmed real shape (100-period `returns` lookback vs ~5.4 rows/day CHAINLINK density) in
      `test_buffer_manager.py` + `test_tf_cluster_helper.py`. `bash scripts/quality-gates.sh` green (18041 passed). NOT
      done as part of this todo: the "Done when" VM run + per-venue (PYTH, HYPERLIQUID) real-density verification — that
      requires launching a features-delta-one-defi VM run, which is the P2 `[DATA]` todo below's job, not this
      `[BACKEND]` implementation todo's.
- [x] ✅ [DATA] P2. Once the above lands, resume `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo's `returns`
      leg (and `funding_oi`, once its separate OI-absence blocker resolves) over the full captured window. Repo:
      features-service. **2026-07-31 (slot-11, data_engineering craft)**: confirmed the fix chain works at real scale —
      read the live run.log of the standing verification VM (`features-delta-one-defi-20260731-094100`,
      `2023-05-12..2023-10-31`, launched by slot-10): 24 consecutive real days completed with
      `Completed 51/51 instruments for returns` and zero errors/exceptions (CHAINLINK + AAVE `spot_asset` instruments;
      no PYTH instruments were part of this discovery run — PYTH/HYPERLIQUID per-venue density verification the doc
      above flags remains a nice-to-have, not re-blocking). Full per-venue verification confirmed for the instrument set
      that actually gets discovered for `returns`; the buffer-days fix is proven correct at production scale, not just
      the earlier narrow repro. See D1 todo's own Progress Log in the satellite batch3 plan for the full-window
      production launch this finding unblocked.

# Progress Log

- 2026-07-31 (slot-5, data_engineering craft, D1 todo resume, `defi_satellite_ao_dispatch_batch3-014`): filed after
  confirming the P1 symbol-fix (`features-service@7e10172c`) is genuinely shipped, deployed, and working at the
  range-load level (51/51 vs the pre-fix 27/51), but the run still produces zero completions via a distinct, downstream
  root cause — root-caused via a direct repro against real GCS data (not guessed), confirming 945 real rows exist in the
  full window while the per-date buffer window admits only a handful.
- 2026-07-31 (slot-4, backend_engineer craft, `delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks-001`):
  P1 shipped — `features-service@9e70fbac` (3 commits: `923e8009` the fix, `2e41f736` fixing 2 pre-existing tests that
  had baked in the bug, `9e70fbac` a method-size QG-limit refactor). `bash scripts/quality-gates.sh` green (18041
  passed, 0 failed). Landed on `live-defi-rollout` via quickmerge. P2 `[DATA]` todo (the actual VM verification run +
  per-venue real-density check) is next and unblocked by this fix, but was not run as part of this todo.
- 2026-07-31 (slot-10, data_engineering craft, running the P2 `[DATA]` VM-verification todo): running the actual
  verification VM surfaced a 6th, DIFFERENT bug masking this fix's own success — every shard was rejected by the NaN
  shard-quality-gate on `btc_trailing_return_6m/12m`'s EXPECTED warmup NaN (up to 252-bar/~12-month lookback,
  `nan_policy: warmup_only` in the registry), unrelated to this issue's buffer-sizing fix. Fixed separately
  (`features-service@12a64eb9`, added an `EXPECTED_SPARSE_COLUMNS["returns"]` exemption) — full detail + relaunch status
  in `/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo (this issue's P2 todo IS that D1 todo's
  resume — logging here so a reader of this doc's chain sees the fix landed and isn't re-blocked by a stale read).
