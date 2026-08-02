---
doc_type: issue
title: >-
  delta_one funding_oi (DEFI) fails "No delta-one instruments available after filtering" --
  get_captured_instruments()/compose_instrument_ids() likely drops perp_funding's blank-instrument_id venue-bundle
  manifest rows, unlike LookbackValidator's own fallback-aware discovery
summary: >-
  After landing BOTH same-session fixes for D1's delta_one leg (`features-service@8e62dc30` LookbackValidator
  manifest-discovery for pass-through types, and `features-service@f932908b` scoping DataLoader.candle_data_types to the
  requested feature_group), a fresh `--feature-group funding_oi --asset-group DEFI` launch
  (`features-delta-one-defi-20260730-231206`, 2023-05-12 start) now correctly passes lookback validation ("1/1
  instruments OK") but then fails the ACTUAL compute step: `Manifest discovery: 0 captured instruments for DEFI
  date=2023-05-12 data_type=perp_funding` -> `No delta-one instruments available after filtering` -> `Processing
  failed`, exit_code=1. This is despite the live MTDS manifest independently confirmed to hold 12,500 real `captured`
  perp_funding rows for exactly this date range (see the companion
  `delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md` issue's own manifest
  read). The likely root cause: `perp_funding`'s MTDS manifest rows are WRITTEN as venue-level aggregate bundles with a
  BLANK `instrument_id` (no per-instrument granularity) -- LookbackValidator's OWN fix (8e62dc30) had to add a special
  blank-id fallback-key match specifically to handle this shape, per that commit's own message: "the raw manifest
  instrument_id (bare feed_id for oracle_prices, blank for perp_funding's per-venue bundle rows...) lands in the third
  colon segment, so `_count_candles_for_lookback`'s EXISTING (venue, symbol)/(venue, "") fallback chain matches it". The
  GENERIC, shared UTL `get_captured_instruments()` / `compose_instrument_ids()` (used by
  `DataLoader.get_available_instruments()`, a DIFFERENT call path from LookbackValidator) does NOT appear to have this
  same blank-id fallback, so it silently drops perp_funding's bundle rows and reports 0 captured instruments -- even
  though the LookbackValidator's own discovery, moments earlier in the SAME run, correctly found and validated 1.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service, unified-trading-library]
scope: [engineer]
tags: [defi, features-service, delta-one, instrument-discovery, blank-instrument-id, data-correctness]
related:
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
  - /plans/active/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md
  - /plans/active/issues/delta_one_get_available_instruments_unscoped_candle_data_types_2026_07_30.md
created: "2026-07-30"
source: [defi_satellite_ao_dispatch_batch3_2026_07_26.md-D1]
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md,
    /plans/active/issues/delta_one_get_available_instruments_unscoped_candle_data_types_2026_07_30.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    unified-trading-library/unified_trading_library/feature_service_base/manifest_discovery.py,
  ]
locked_by:
resolved_by:
---

# What I found

Live repro, same session as the two companion fixes above:

```
VM: features-delta-one-defi-20260730-231206
CMD: python -m features_service --feature-family delta_one --operation compute --mode batch \
     --start-date 2023-05-12 --end-date 2026-06-09 --asset-group DEFI --feature-group funding_oi --timeframe 15m

23:15:06 Lookback validation: max_lookback=48, timeframe=15m, buffer_days=1, expected=96, required=91
23:15:59 Lookback validation PASSED: 1/1 instruments OK          <- LookbackValidator (8e62dc30 fix) works
23:15:59 Processing 1 feature groups, lookback buffer: 1 days
23:16:47 Manifest discovery: 0 captured instruments for DEFI date=2023-05-12 data_type=perp_funding   <- DIFFERENT path
23:16:47 Listing per-venue instruments under gs://instruments-store-defi-prd.../instrument_availability/by_date/day=2023-05-12/
23:16:53 ERROR No delta-one instruments available after filtering
23:16:53 ERROR Processing failed
[vm-exec] command exited rc=1
```

The pre-flight `LookbackValidator._discover_instruments_from_manifest` (my earlier same-session fix,
`features-service@8e62dc30`) correctly finds 1 instrument for `data_type=perp_funding` on this date and passes. Seconds
later, the ACTUAL instrument-resolution call for real processing — `DataLoader.get_available_instruments()` →
`get_captured_instruments(bucket=..., date=..., data_type="perp_funding", ...)` (a UTL function, NOT the code I patched)
— reports **0** captured instruments for the exact same `(date, data_type)` pair, then falls back to a legacy per-venue
instruments-store listing that also comes up empty, and the run aborts.

# Why this matters

This is the actual remaining blocker on D1's delta_one `funding_oi` leg (the `returns`/`oracle_prices` leg appears NOT
to hit this — a parallel VM launch for `returns` is iterating real oracle-price instrument ids like
`CHAINLINK:spot_asset:DAI_USD`, not failing this way, consistent with oracle_prices manifest rows carrying a real bare
feed_id rather than a blank one). Two independent discovery paths in the SAME codebase now disagree about whether
perp_funding data is "available" for the same date — one (LookbackValidator, already fixed with an explicit blank-id
fallback) says yes; the other (`get_captured_instruments`, the one that actually gates real compute) says no. Until this
is fixed, `funding_oi` can never produce real DEFI delta_one output no matter how the backfill is launched.

# What I did NOT do

Did not patch `get_captured_instruments()`/`compose_instrument_ids()` — these are shared UTL functions
(`unified_trading_library`), used broadly across services, not scoped to delta_one/DEFI. A same-session patch
mid-backfill to a shared library, on top of 2 other same-session fixes already shipped, is exactly the kind of
blast-radius risk this craft's "do not absorb unplanned scope" discipline flags — this needs its own reviewed, scoped
fix with regression coverage for the blank-id case specifically (mirroring LookbackValidator's own `(venue, "")`
fallback-key pattern, adapted for whatever `compose_instrument_ids`' real signature/contract is). Did not investigate
`compose_instrument_ids`'s source in depth — only traced the failure to this call boundary via the log evidence above.

# Recommended decision

Read `unified_trading_library`'s `get_captured_instruments()` / `compose_instrument_ids()` implementation and add the
same blank-instrument_id venue-bundle fallback LookbackValidator already uses (synthesize a `{venue}:{DATA_TYPE}:` id,
or whatever key shape delta_one's downstream consumer expects, when the raw manifest `instrument_id` is empty but the
row is genuinely `captured`). Add a regression test asserting a DEFI `perp_funding` manifest row with blank
`instrument_id` is NOT silently dropped. Once fixed, resume the `funding_oi` leg (repro command above,
`2023-05-12..2026-06-09`).

## Todos

- [x] ✅ [BACKEND] P1. Fix `get_captured_instruments()`/`compose_instrument_ids()` (repo: unified-trading-library) to
      synthesize a valid instrument id for a captured manifest row with a blank `instrument_id` (perp_funding's
      venue-level-bundle shape), instead of silently excluding it. Mirror LookbackValidator's `(venue, "")` fallback-key
      precedent (`features_service/delta_one/app/core/dependency_checker.py`, `features-service@8e62dc30`). Repo:
      unified-trading-library. Done when: a DEFI `perp_funding` manifest row with blank `instrument_id` is returned by
      `get_captured_instruments()`, verified by a new unit test; `bash     scripts/quality-gates.sh` green in both
      unified-trading-library and features-service (post wheel-bump). — unified-trading-library@9fb3a73d
- [ ] [DATA] P2. BLOCKED-OPERATOR-DECISION (funding_oi/HYPERLIQUID is structurally infeasible — the venue never captures
      open_interest, so no relaunch can produce real rows; fix-direction is a repo-owner/operator design call tracked in
      `/plans/active/issues/defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`'s
      `[OPERATOR] P2`. DO NOT relaunch until that decision lands — every prior relaunch was guaranteed-wasted VM spend,
      see 2026-08-02 Progress Log). Once the fix-direction lands, resume
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 delta_one `funding_oi` leg: relaunch
      `--feature-family delta_one --asset-group DEFI --feature-group funding_oi     --start-date 2023-05-12 --end-date 2026-06-09 --timeframe 15m`
      (SPOT). Repo: features-service. Done when: `features-delta-one-defi` has real funding_oi rows for HYPERLIQUID, not
      empty_confirmed/failed.

# Progress Log

- 2026-07-30 (slot-14): filed immediately after both companion fixes (8e62dc30, f932908b) landed and were verified live
  — this is the newly-exposed NEXT layer of the same instrument-discovery inconsistency, not a regression from either
  fix.
- 2026-07-30 (slot-14, self-correction — read after filing): **downgraded confidence.**
  `delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md` (slot-4, filed EARLIER the same session, which I
  only read after filing this doc) shows a `funding_oi` run on `date=2023-06-01` reaching
  `Manifest discovery: 25 captured instruments for DEFI date=2023-06-01 data_type=perp_funding` — a NON-ZERO count, via
  the SAME `get_captured_instruments()` call path this doc claims returns 0. So the function does NOT unconditionally
  drop perp_funding's blank-id rows — my repro's `date=2023-05-12` (the very FIRST date of the confirmed clean manifest
  window) returning 0 while `2023-06-01` (20 days later) returns 25 looks more like a boundary/edge condition on the
  FIRST day specifically than a blanket blank-id bug. Left this doc open (P2, downgraded from P1) as a narrower "does
  day-1-of-window behave differently" question for whoever picks up todo 1 below — but the DOMINANT,
  confirmed-deterministic blocker on this leg is slot-4's candle-loader finding (no pass-through read branch), NOT this
  one. Do not treat this doc as the primary blocker to fix first.
- 2026-07-30 (slot-8): shipped todo 1 (`unified-trading-library@9fb3a73d`). Confirmed the underlying defect is real
  regardless of the day-1-vs-day-20 discrepancy noted above: `compose_instrument_ids()` unconditionally dropped ANY row
  whose `instrument_id` was blank/an aggregate sentinel (`nan`/`None`/`<aggregate>`/`_AGGREGATE`/`<empty>`) — the
  25-instrument non-zero count on `2023-06-01` reported by slot-4 must have come from rows carrying a real (non-blank)
  bare `instrument_id`, not a counter-example to this bug; whichever rows on that date genuinely WERE blank-id bundle
  rows would have been silently dropped from that 25 too. Fixed to mirror LookbackValidator's `(venue, "")` fallback-key
  precedent: a row with venue + instrument_type resolvable now synthesizes `"{venue}:{instrument_type}:"` (trailing
  empty segment) instead of being dropped; only rows with no resolvable venue/instrument_type at all are still dropped.
  Added a direct DEFI `perp_funding` blank-`instrument_id` regression test
  (`test_defi_perp_funding_blank_id_venue_bundle_row_not_dropped`) plus updated the two pre-existing tests that asserted
  the OLD drop behavior (`test_empty_instrument_id_skipped` → renamed
  `test_blank_instrument_id_synthesizes_bundle_id_when_venue_and_type_resolvable`; `test_aggregate_sentinels_skipped` →
  renamed `test_aggregate_sentinels_synthesize_bundle_id`). All 29 unit tests + full `quality-gates.sh` green. Did NOT
  investigate the day-1-vs-day-20 boundary question further — out of this todo's scope (the fix here addresses the
  blank-id drop unconditionally, which is a real defect independent of whichever specific dates it was masking). Did NOT
  touch downstream `features-service` DataLoader path-resolution for the now-returned trailing-empty-segment ids
  (`HYPERLIQUID:perpetual:`) — that's the companion candle-loader-pass-through issue's scope, not this UTL-function
  fix's.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **2026-08-02 (slot-8, data_engineering craft) — todo 2 NOT relaunched; marked BLOCKED-OPERATOR-DECISION after
  re-confirming the funding_oi/HYPERLIQUID leg is structurally infeasible.** Dispatched todo 2 ("resume the funding_oi
  leg"). Before launching any VM (per this chain's own repeated "relaunching is guaranteed-wasted spend" lesson),
  verified the state end-to-end: (1) UTL blank-id fix (todo 1, `9fb3a73d`) confirmed on LDR — instrument discovery is no
  longer the blocker; (2) `funding_oi.py::get_required_columns()` STILL hard-requires
  `["funding_rate", "open_interest"]` with NO commits since 2026-07-31, and the MTDS HYPERLIQUID perp_funding handler
  has NO OI-capture fix landed either — so the
  `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md` structural gap (HYPERLIQUID never captures
  OI in either capture era, direct-parquet-confirmed by slot-2) is fully current, `status: open`, `[OPERATOR] P2`
  fix-direction decision UNMADE; (3) live GCS check — `gs://features-defi-prd-central-element-323112/delta_one/by_date/`
  contains ONLY `feature_group=returns` (303,812 parquet objects — the returns leg IS complete) and ZERO `funding_oi`
  objects. Every funding_oi relaunch fails the >50% NaN column-quality gate deterministically on every date; no
  window/SPOT-flag choice changes that. Did NOT launch a VM (guaranteed waste, exactly the 10+ VM storm 2026-07-30
  already proved). Marked todo 2 above `BLOCKED-OPERATOR-DECISION` (a live token → non-dispatchable per
  `regen_backlog_from_plan._is_non_dispatchable`, stops the redispatch-into-failure loop) and posted a `/blocked`
  question surfacing the operator fix-direction decision. Also flagging for main/operator: the parent
  `defi_satellite_ao_dispatch_batch3_2026_07_26.md` D1 todo (line ~103) carries a `BLOCKED-ON:` prefix that is NOT a
  recognized non-dispatchable token (the regex only matches
  `BLOCKED-OPERATOR/CREDENTIALS/BILLING/UPSTREAM-*/PLAYWRIGHT/JURISDICTION`), so that P1 todo is STILL dispatchable and
  can re-trigger the same VM storm — but it bundles a still-doable onchain leg + the already-done returns leg, so it
  needs a main/operator SPLIT (not a blanket block), which is out of this worker's scope.
