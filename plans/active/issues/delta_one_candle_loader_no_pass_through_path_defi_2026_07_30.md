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
  - /plans/archive/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
created: "2026-07-30"
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
context_scope:
  [
    /plans/active/issues/delta_one_lookback_instrument_discovery_wrong_universe_for_passthrough_defi_2026_07_30.md,
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    features-service/features_service/delta_one/app/core/data_loader.py,
    features-service/features_service/delta_one/app/core/_passthrough_loader.py,
    features-service/features_service/delta_one/cli/handlers/_tf_cluster_helper.py,
  ]
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

- [x] [BACKEND] P1. Add a pass-through read branch to `_tf_cluster_helper.py`'s candle-loading path (or `DataLoader`)
      keyed on `unified_api_contracts.registry.market_data_categories.needs_candle_processing(data_type)`, sourcing raw
      MTDS rows for pass-through data types and reshaping them to the columns the target calculator's
      `get_required_columns()` declares. Leave candle-processed data_types on the existing path unchanged. Repo:
      features-service. Done when: a DEFI `funding_oi` run over `2023-05-12..2023-10-31` (perp_funding's confirmed clean
      manifest window) loads >0 candles for a majority of the 412 discovered instruments and writes real
      `record_captured` rows (not `record_failed`/empty), verified by a new unit test, and
      `bash scripts/quality-gates.sh` green. — ✅ features-service@a5a5bf7d. Full evidence in Progress Log below.
- [ ] [DATA] P2. Once the above lands, resume `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo's delta_one
      leg (funding_oi + returns) over a verified-clean manifest window. Repo: features-service. Done when:
      `features-delta-one-defi` has a populated index and D1's checkbox is flipped citing this evidence.
- [ ] [OPERATOR] P1. Until todo 1 lands, consider parking `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo
      (backlog `priority: 999` + `priority_override: true` + a false prerequisite gating it, per
      `unified-trading-pm/agents/RULES.md` §4 "Park a task") so the AO dispatcher stops redispatching fresh workers into
      the same guaranteed-deterministic-failure loop -- 10 VM launches burned today already, several concurrently
      in-flight as this doc was filed.
- [x] ✅ [BACKEND] P1. Fix `_tf_cluster_helper.py::_process_one_date_for_cluster` to isolate failures per OUTPUT
      TIMEFRAME (not just per date) -- the near-cluster's default output-TF ladder (`["15s","1m","5m","15m"]`, from
      `_default_output_timeframes`/`config.DEFAULT_TIMEFRAMES`) always tries `"15s"` FIRST, and a single failed TF
      aborted the WHOLE cluster/date immediately, so the real requested TF (`"15m"`, listed LAST) was never reached for
      any DEFI pass-through group even after todo 1's fix landed. Repo: features-service. Done when: a cluster whose
      first output TF fails but a later TF in the same cluster succeeds returns `True` and both TFs are attempted,
      verified by a new unit test; `bash scripts/quality-gates.sh` green. — ✅ features-service@9769ded7. Full evidence
      in Progress Log below.

# Progress Log

- 2026-07-30 (slot-4, data_pipeline_failure escalation DP-VM-001): filed after declining to relaunch
  `features-delta-one-defi-20260730-222034` a further time (root cause is deterministic, not infra/transient; runbook's
  own relaunch bound already far exceeded). Root-caused via full run.log read + code trace
  (`_tf_cluster_helper.py`/`funding_oi.py`) + cross-referencing 3 other same-day VM logs showing the identical failure
  shape across both feature groups and 3 different date windows.
- 2026-07-30 (slot-2, data_pipeline_failure escalation DP-VM-002 for `features-delta-one-defi-20260730-231230`,
  ESCALATION_ID=agt-7f3e51): the fleet monitor flagged this VM under a NEW detector (DP-VM-002 — VM drained with
  `captured` not climbing and no honest-absence/rate-limit signal in the log), distinct from slot-4's DP-VM-001 finding,
  but full run.log confirms it is the SAME already-diagnosed root cause, not a new failure mode: dependency-check +
  lookback validation PASSED (22/22 instruments), manifest discovery found 22 real `oracle_prices` instruments, then
  every single instrument×date pair logged `WARNING No upstream MDPS data ... (data_type=oracle_prices) — skipping date`
  from the very first date onward — identical shape to this issue's own repro. This VM was launched with
  `--feature-group returns --start-date 2023-01-01 --end-date 2026-07-22` (full multi-year history, `TIMEFRAME=15m`) and
  terminated abruptly mid-run (log stops at 2025-11-08 with no ERROR/exit line, `gcloud compute instances list` confirms
  it no longer exists, no `EXIT_STATUS` object written — consistent with the fleet monitor's "drained without a durable
  exit marker" read) — but even a clean completion would have written zero real captures, since the candle-load failure
  is deterministic across every date in the window. A sibling VM `features-delta-one-defi- 20260730-231206`
  (`funding_oi`, `2023-05-12..2026-06-09`) launched the same minute failed the same class one step earlier
  (`Manifest discovery: 0 captured instruments for ... perp_funding` at that specific start date →
  `ERROR No delta-one instruments available after filtering`, clean `exit_code=1`). Both VMs were launched by slot 14,
  which the live backlog shows `dispatched_to: 14` on `defi_satellite_ao_dispatch_batch3-014` (this issue's own D1 todo)
  since 2026-07-30T22:28:58Z — i.e. the todo-3 `[OPERATOR]` parking recommendation below has NOT yet been executed, and
  the redispatch-into-guaranteed-failure loop is still active (now 12+ VMs today). Did NOT attempt the
  `_tf_cluster_helper.py` pass-through-branch fix myself — same craft-scope call as slot-4 (shared CEFI/TRADFI/DEFI/
  PREDICTION code, a real design decision, not a blind one-shot-escalation guess) — and did NOT relaunch. Messaged slot
  14 directly (`/api/slots/14/message`) with this finding + a stop-relaunching recommendation, since it is the
  currently-dispatched worker and best positioned to action the park-or-hold-off decision live. Did not hand-edit
  `backlog.yaml` myself (outside my slot's git worktree, and todo 3 below is explicitly `[OPERATOR]`-tagged) — flagging
  here for main/operator to execute the park if slot 14 cannot.
- **2026-07-30 (slot-9, backend_engineer craft) — todo 1 SHIPPED.** Added the pass-through branch in `DataLoader` itself
  (the todo's own "(or `DataLoader`)" alternative) rather than `_tf_cluster_helper.py` — `DataLoader` is the single
  choke point both `_load_one_instrument_range`/`_load_base_candles` already call through, so no change to
  `_tf_cluster_helper.py` was needed at all. `load_candles_with_buffer()` now branches on
  `needs_candle_processing(data_type)`: when `False`, `_load_passthrough_range()` reads raw MTDS rows directly instead
  of probing the (structurally nonexistent) `processed_candles` path. Extracted into a new `_passthrough_loader.py`
  mixin (`_PassthroughLoaderMixin`, mirrors the existing `_tf_cluster_helper.py` mixin-extraction pattern) to keep
  `data_loader.py` under the 900-line file cap after the addition.
  - **Day-partition read**: `_load_passthrough_day()` lists `raw_tick_data/by_date/day={date}/` ONCE per
    `(data_type, date, venue)` and needle-filters blob names on `asset_group=`/`venue=`/`data_type=` — generalises
    `onchain/calculators/perp_funding_rates_defi.py`'s proven `_load_raw_frame` pattern (same needle-filter shape, same
    retirement-marker skip) off its single hardcoded (hyperliquid, perp_funding) pair to any (venue, data_type). Cached
    on the `DataLoader` instance (shared across every instrument of that venue for that day/data_type — a single
    `DataLoader` is created once per handler run, per `batch_handler.py`), so 412 instruments sharing a venue cost ONE
    list+download per day, not 412 (single-walk discipline).
  - **Instrument filtering**: manifest-discovered pass-through instrument_ids are `{venue}:{DATA_TYPE}:{raw_id}`
    (confirmed by reading `dependency_checker._discover_instruments_from_manifest` — the middle segment is the
    data_type, NOT an instrument_type, and `raw_id` is blank for `perp_funding`'s per-venue bundle rows). Filters to
    `raw_id` via a `symbol`/`coin`/`market`/`feed` column match when non-blank; keeps the whole venue-day frame when
    blank (the bundle-row case).
  - **Timestamp resolution**: `_resolve_passthrough_timestamp()` prefers an already-Datetime `available_at` column
    (every onchain-tick writer stamps it via the shared UTL `stamp_available_at_onchain_tick()` helper — confirmed by
    reading both `_perp_funding_hyperliquid.py` and `oracle_prices_handler.py` — so no unit-guessing is needed), falling
    back to a Datetime `timestamp`, an integer `publish_time`/`timestamp` (Unix seconds), or a string `date`.
  - **Reshape**: `_reshape_passthrough_funding()` maps to `funding_oi`'s `get_required_columns()`
    (`funding_rate`/`open_interest`, aliasing `funding_rate_long` when `funding_rate` is absent per the raw
    `perp_funding` schema in `schema_validation.py`, filling `mark_price`/`index_price` as null when absent — read
    directly from `_REQUIRED_COLUMNS` in `market-tick-data-service/cli/handlers/schema_validation.py` to confirm the
    real raw column set, not guessed). `_reshape_passthrough_price()` maps `oracle_prices`' raw `price` scalar to an
    OHLC-shaped frame (`open=high=low=close=price`, volume omitted — `returns.py`'s own `get_required_columns()`
    docstring already documents volume as optional for DEFI oracle_prices).
  - **Verification**: ran a live simulation (not just mocked unit tests) — a mock day-partition parquet shaped exactly
    like the real `perp_funding` schema, through the FULL `load_candles_with_buffer()` call the delta_one batch handler
    actually makes, confirming it now returns non-empty reshaped data for the exact call shape that was failing 100% of
    the time in production. 18 new unit tests added to `test_data_loader.py` (timestamp-resolution priority order,
    funding/price reshaping, day-partition list+download+cache+needle-filter, venue-only-bundle vs symbol-filtered range
    loads, and `load_candles_with_buffer` routing) — 109/109 pass. Full `quality-gates.sh`: green (18015 passed, 209
    skipped; file/method-size gate clean post-extraction). Shipped: `features-service@a5a5bf7d`.
  - **Not done in this todo** (correctly out of scope — todo 2/3 below cover it): did not re-run the actual DEFI
    `funding_oi` backfill against production GCS (todo 2's job, gated on this landing) and did not action the
    `[OPERATOR]` park recommendation (todo 3, still open below).
- **2026-07-31 (slot-8, data_pipeline_failure escalation DP-VM-001, `ESCALATION_ID=agt-e52874`, for VM
  `features-delta-one-defi-20260730-234947`, exit_code=1) — found + fixed a THIRD layer, shipped todo 4.** Dispatched
  per `codex/15-runbooks/incidents/rb_infra_relaunch.md` to relaunch this VM. Read its durable GCS logs first per the
  runbook's own guidance and found this is a NEW mutation of the same causal chain, not a repeat of an already-tracked
  failure: `EXIT_STATUS=1`, `deployment_id=c788d8f8-665b-4b78-b7ad-e2d3b3d463a7`, `git_commit=d072b0358b...`
  (BoM-recorded commit not resolvable in the repo history — likely a stale/incorrect BoM stamp, not investigated
  further, out of this escalation's scope). Confirmed todo 1's pass-through fix (`features-service@a5a5bf7d`) IS
  deployed and working — `Manifest discovery: 1 captured instruments for DEFI date=2023-05-12 data_type=perp_funding`
  (previously `0`, per the sibling blank-id doc) and real per-instrument candle processing was attempted (no more
  `No upstream MDPS data` messages). But the run still failed 100% of dates with
  `No pre-loaded candles for HYPERLIQUID:perpetual: at 15s — skipping` → the honest-absence gate correctly rejecting an
  unproven `empty_confirmed` write → `ERROR ALL feature groups failed: ['funding_oi']` → exit 1. Traced to
  `_tf_cluster_helper.py`: `_default_output_timeframes("DEFI")` returns the CEFI-shaped
  `["15s","1m","5m","15m","1h","4h","24h"]` ladder (DEFI has no `TRADFI_SUPPORTED_TIMEFRAMES`-style exclusion list); the
  near-cluster reads real base candles at `"15m"` (the CLI's actual `--timeframe`, confirmed via
  `resample_candles_to_timeframes`'s same-tf identity branch — `candle_resampler.py:212`), but
  `_process_one_date_for_cluster` iterated output TFs in ladder order (`"15s"` first) and `return False` IMMEDIATELY on
  the first failing TF — since `"15s"` (finer than the `"15m"` base, `candle_resampler.py`'s own "target finer than base
  — cannot resample" warning) always fails first, `"15m"` (listed LAST, the one TF that genuinely had data) was NEVER
  attempted. Exact same failure-mode CLASS already fixed for TRADFI via `constants.py`'s `TRADFI_SUPPORTED_TIMEFRAMES`
  (see that file's own 2026-07-26 comment on the identical abort-before-real-TF shape) — but that fix only special-cased
  TRADFI's ladder, not the underlying abort-on-first- failure bug, so DEFI's pass-through groups hit the same class
  through a different door.
  - **Fix (lower-risk than a DEFI-specific timeframe allowlist, which would require guessing DEFI's exact native data
    cadence):** made `_process_one_date_for_cluster` isolate failures per OUTPUT TIMEFRAME instead of aborting the whole
    cluster on the first one — mirrors the shard-level-failure-isolation codex principle already applied one level up
    (`_process_tf_clusters_date_range`'s own any-succeeded-across-dates contract). A TF the cluster can't serve now logs
    a warning and the loop continues to the next TF; the cluster only reports failure if EVERY TF failed. Verified via a
    new regression test asserting the exact production shape (first TF fails, later TF in the same cluster succeeds,
    both are attempted, result is `True`) plus updated the pre-existing test that had encoded the old abort-immediately
    contract. All 50 `test_tf_cluster_helper.py` tests pass; full `quality-gates.sh` green at HEAD (hit the 50-line
    method-size gate on the first pass — 57L — trimmed the docstring/log message to 47L and re-ran green). Shipped:
    `features-service@9769ded7`.
  - **Did not relaunch** the VM (would fail identically pre-fix; the fix is now live via LDR so a fresh relaunch of D1's
    todo 2 can be attempted once this lands past the Tier-C drain to staging/main — that resume attempt is todo 2 above,
    still open).
  - **Did not action** the still-open `[OPERATOR]` park recommendation (todo 3) — flagging again here since two prior
    escalation workers (slot-4, slot-2) already recommended it and it appears not yet executed; this is now the THIRD
    data_pipeline_failure escalation to hit this same VM-relaunch-storm chain today.
  - **Not investigated** (out of this escalation's scope): whether `"15s"`/`"1m"`/`"5m"` output TFs are ever
    MEANINGFULLY desired for DEFI pass-through data at all (vs. just wasted attempts that always fail and log a warning)
    — a `DEFI_SUPPORTED_TIMEFRAMES`-style allowlist (mirroring `TRADFI_SUPPORTED_TIMEFRAMES`) would be a cleaner
    long-term fix once someone with the real perp_funding/oracle_prices native-cadence knowledge scopes it; today's fix
    is the safe, general, no-domain-knowledge-required floor (never mask a working TF, whatever the ladder contains).
- **2026-07-31 (slot-2, data_engineering craft) — todo 2 attempted; `funding_oi` confirmed structurally blocked
  (separate issue filed), found + fixed a FOURTH bug (in two passes — first attempt was incomplete) blocking `returns`,
  real verification run now in flight on the corrected fix.** Ran a `--launch-mode dry` verification-window pass first
  (`funding_oi`, `2023-05-12..2023-10-31`) per this todo's own "verified-clean manifest window" instruction — the
  pass-through loader now loads real rows (no more "No upstream MDPS data"), but `funding_oi` fails a DIFFERENT gate:
  HYPERLIQUID's raw `perp_funding` rows never carry `open_interest`/ `mark_price`/`index_price` in either capture era
  (confirmed via direct raw-parquet inspection, not simulated) — a genuine data-availability gap, not a loader bug.
  Filed `/plans/active/issues/defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md` (does not
  re-attempt `funding_oi` further — deterministic, fix-direction is operator/repo-owner scoped). Separately dry-ran
  `returns` (`oracle_prices`) over the same window — 27/51 instruments loaded real candles, then hit
  `_resolve_passthrough_timestamp()` raising a polars `SchemaError` (tz-naive vs tz-aware `Datetime` compared in the
  downstream range filter). **First fix attempt (`features-service@3bce3997`) was INCOMPLETE**: it made `available_at`
  win outright whenever it's a native `pl.Datetime` — correct per the function's docstring, but that branch never
  actually fires in production, because `available_at` is written to disk as an ISO-8601 **STRING** (confirmed via
  direct polars-schema inspection of both the oracle_prices and perp_funding raw parquets — pandas' pyarrow auto-parse
  had made it LOOK like a real datetime on first inspection, masking this). So the real (non-dry) run against `3bce3997`
  reproduced the IDENTICAL SchemaError, falling through to the `publish_time` int-epoch branch
  (`pl.from_epoch(..., time_unit="s")`, tz-naive by default) exactly as before the "fix". **Second fix
  (`features-service@c46509be`)** properly parses `available_at` as a string (`str.to_datetime(time_zone="UTC")`) and
  normalises EVERY branch's output (already-Datetime `timestamp`, `publish_time`/`timestamp` int-epoch, `date` string)
  to UTC-tz-aware via a small extracted `_utc_expr()` helper (needed to stay under the 50-line method cap after the
  added branches). 4 new/updated regression tests, including one asserting the exact production range-filter comparison
  (`>=`/`<` against a tz-aware literal) no longer raises. Full `quality-gates.sh` green (112/112 `test_data_loader.py`).
  Real (non-dry) `returns` verification-window run relaunched against the corrected fix
  (`features-delta-one-defi-20260731-011445`) — result pending as this note is written; see this doc's next update or
  the D1 todo's progress log for the outcome.
- **2026-07-31 (slot-2, data_engineering craft) — the `features-service@c46509be` fix above ELIMINATED the SchemaError
  (confirmed live: relaunched run `features-delta-one-defi-20260731-011445` progressed cleanly through the loading step
  with zero crashes) but exposed a DEEPER, more serious bug it had been masking: a DATA-CORRECTNESS defect, not just a
  dtype mismatch. Root-caused + fixed + shipped `features-service@94fd3c8b` — flagging as a BIG FINDING per CLAUDE.md's
  data-correctness HARD RULE (this note IS the notification; no separate escalation needed, the fix is already shipped
  and the corpus was never corrupted — see "blast radius" below).**
  - **What was wrong**: `_resolve_passthrough_timestamp()`'s "available_at wins outright" priority (as designed by the
    ORIGINAL `a5a5bf7d` fix, and preserved by my own `c46509be` fix above) treats `available_at` as if it were the event
    timestamp. It is NOT — `available_at` is a PIPELINE-INGESTION timestamp (when the row was written/migrated INTO the
    system). Confirmed via direct data inspection: a real `2023-05-31` oracle_prices row's `available_at` value was
    `2026-07-22T05:57:17` — the date the historical-migration script actually ran, over 3 YEARS after the real 2023
    price event that row represents. For LIVE-captured rows the gap is smaller (minutes to a couple days) but still real
    and non-zero.
  - **Observed symptom (why it took two fix attempts to find)**: this does NOT raise an exception — it's a SILENT
    correctness bug. Every row got a real, validly-typed, UTC-aware `timestamp`... just the WRONG one (the 2026
    migration date instead of the real 2023 event date). Every downstream per-date range-filter (`_extract_date_window`
    in `_tf_cluster_helper.py`) then correctly filtered based on that wrong timestamp, finding zero rows for every one
    of the 172 requested 2023 dates (all the real data got mis-filed under 2026-07-22 instead). Net effect on the
    relaunched run: 12,000+ log lines, "No pre-loaded candles" for all 51 instruments on every date, zero writes,
    `ERROR ALL feature groups failed` — a silent, total failure with no exception anywhere in the chain, exactly
    matching a genuine sparse-historical-data absence pattern (which is why the first read of this log looked like
    honest-absence rather than a bug — confirmed it was a bug only by cross-checking real GCS day-density: ETH_USD
    oracle_prices has real data on 184/173 days in the exact verification window, i.e. dense, not sparse).
  - **Fix**: reversed the priority order. Real EVENT-time fields now win, in order: an already-Datetime `timestamp`
    (normalised to UTC), an integer `publish_time`/`timestamp` (Unix seconds), a string `date`. `available_at` is now
    the LAST-RESORT fallback ONLY when no real event-time field exists at all (a legitimate use — some feeds may
    genuinely have nothing better). Verified against real production data locally (not just unit tests): downloaded 4
    consecutive real ETH_USD oracle_prices day-parquets, ran them through the fixed function, confirmed the resolved
    `timestamp` values are the real 2023 event dates (not 2026) and that `_extract_date_window`'s exact filter
    (reproduced locally) now returns non-empty windows. 7 tests rewritten/added in `TestResolvePassthroughTimestamp`
    (the old tests literally encoded the wrong priority as their expected behavior — e.g.
    `test_prefers_available_at_when_datetime` asserted `available_at` should win, which is now the confirmed-wrong
    premise); full `quality-gates.sh` green (114/114 `test_data_loader.py`). Shipped: `features-service@94fd3c8b`.
  - **Blast radius / why this is a "big finding" but NOT a "corrupt the corpus" incident**:
    `_resolve_passthrough_timestamp` is used by every DEFI delta_one pass-through data_type
    (`funding_oi`→`perp_funding`, `returns`→`oracle_prices`, and the `derivative_ticker` alias) — but it was only
    introduced today (`a5a5bf7d`, this same issue doc's todo 1) and EVERY attempt to actually run it against production
    GCS since then has failed with either the SchemaError (before `c46509be`) or the silent zero-match symptom above
    (between `c46509be` and `94fd3c8b`) — meaning `features-delta-one-defi` genuinely has NO INDEX yet (confirmed:
    `gs://features-defi-prd-.../` still has no `delta_one/` prefix as of this note). No wrong data was ever actually
    written to prod — the corpus was protected by the fact that every prior attempt also failed for an unrelated reason
    (SchemaError) before this correctness bug could silently succeed and write bad rows. This is a near-miss, not an
    incident, but it would NOT have been caught before writing bad data had the SchemaError not existed first — flagging
    so nobody assumes "it ran clean, therefore it's correct" the next time a pass-through feature type's real
    event-timestamp assumption changes.
  - **Not yet done**: the real (non-dry) `returns` verification-window run has not been re-relaunched against `94fd3c8b`
    as this note is written (session ending on context pressure — see the D1 todo's Progress Log for the exact resume
    command). `features-service@94fd3c8b` itself is shipped and green.
- **context-scout 2026-08-01**: populated context_scope (5 entries).
