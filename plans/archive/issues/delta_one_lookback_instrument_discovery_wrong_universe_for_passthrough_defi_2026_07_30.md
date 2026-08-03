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
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service, unified-api-contracts]
scope: [engineer]
tags: [defi, features-service, delta-one, lookback-validator, instrument-discovery, data-correctness]
related:
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
  - /plans/archive/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md
created: "2026-07-30"
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
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/archive/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md,
    features-service/features_service/delta_one/app/core/dependency_checker.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
  ]
locked_by:
resolved_by:
  2026-08-03 (both todos closed; duplicate-closed against delta_one_candle_loader_no_pass_through_path_defi's D1
  verification)
---

> **✅ ARCHIVED 2026-08-03** — both todos closed (ACKED-INTO-CODE, per
> `/codex/11-project-management/issue-doc-lifecycle.md`): the instrument-discovery fix (`features-service@8e62dc30`) and
> the D1-resume verification, closed as a duplicate of
> `/plans/archive/issues/delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`'s own todo 2 — same underlying
> verification run (`features-delta-one-defi-20260803-055145`, 454/455 manifest shards `captured`). D1's checkbox
> flipped in `/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md`. See the Progress Log below.

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

## Todos

- [x] ✅ [BACKEND] P1. Fix `LookbackValidator._discover_instruments()`
      (`features_service/delta_one/app/core/     dependency_checker.py:679`) so that when `candle_data_types` (resolved
      via `resolve_data_type_for_feature_group`) are ALL pass-through per
      `unified_api_contracts.registry.market_data_categories.needs_candle_processing()`, it sources its instrument list
      from the MTDS availability-manifest rows matching those `candle_data_types` (same manifest
      `_build_captured_index()` already reads) instead of walking `processed_candles`. Do NOT change behavior for
      candle-processed data_types (`dex_pool_swaps`/`dex_swaps`/`liquidations`) — this is DEFI-scoped only unless the
      same mismatch is confirmed elsewhere. Repo: features-service. Done when: a DEFI `funding_oi`/`returns` lookback
      check discovers oracle-price/perp-funding-shaped instrument ids (not DEX-pool ids), verified by a new unit test,
      and `bash scripts/quality-gates.sh` green. — features-service@8e62dc30, quality-gates.sh ALL PASSED
      (sentinel=HEAD).
- [x] ✅ [DATA] P2. **`returns` DONE (2026-08-02, slot-6); `funding_oi` still BLOCKED (2026-08-03, slot-2) — see
      Progress Log, cannot flip D1's checkbox yet.** Once the above lands, resume
      `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo's delta_one leg: launch
      `features-service --feature-family delta_one --asset-group DEFI --feature-group     funding_oi` (and `returns`)
      with `TIMEFRAME=15m`, over a clean window verified against the live MTDS manifest for the resolved pass-through
      data_type (`perp_funding` has a confirmed clean block `2023-05-12..2023-10-31`; `oracle_prices` needs the same
      clean-window check before picking dates). Repo: features-service. Done when: `features-delta-one-defi` has a
      populated index, and D1's checkbox is flipped citing this evidence. — **CLOSED 2026-08-03 (slot-8)**, same
      underlying verification as this DOC's near-duplicate twin
      (`delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`'s todo 2). `funding_oi` was unblocked by
      `features-service@6b2282c5` (the `[BACKEND] P1` fix in
      `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`). Real verification-window run
      `features-delta-one-defi-20260803-055145` (`2023-05-12..2023-10-31`, `15m`, SPOT, `EXIT_STATUS=0`): 454/455
      manifest shards `captured` across 147 dates. `returns` reconfirmed complete (10,580 `captured` rows). D1's
      checkbox flipped in `defi_satellite_ao_dispatch_batch3_2026_07_26.md` citing this evidence — full detail in the
      sibling doc's Progress Log, not re-duplicated here.

# Progress Log

- 2026-07-30 (slot-3): filed, root-caused via live 2-attempt repro + code trace + manifest spot-checks. D1's onchain leg
  (`perp_funding_rates`, a separate feature_family unaffected by this DEFI delta_one-specific bug) proceeding in
  parallel — see `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo for the combined status.
- **2026-08-02 (slot-6, data_engineering craft, dispatched to todo 2)**: todo 1 (this doc) has long since landed
  (`8e62dc30`), so todo 2 was legitimately dispatchable — but D1's own todo (in
  `defi_satellite_ao_dispatch_batch3_2026_07_26.md`) has accumulated a much longer chain of downstream findings since
  this doc was filed (candle-loader pass-through gap, buffer-too-short, symbol-format mismatch, NaN-warmup gate,
  dependency-checker false-negative, unfiltered-manifest OOM — all now fixed — plus a genuinely open `funding_oi`
  OI-availability question). Checked current prod state instead of blindly relaunching per D1's own repeated lesson:
  `returns` is CONFIRMED COMPLETE — real contiguous data `2022-11-25..2026-07-23` in
  `features-defi-prd-.../delta_one/by_date/`. Initially misread the pre-`2022-11-25` span as an unfilled gap and
  launched a VM to close it (`features-delta-one-defi-20260802-235804`, `2022-11-01..2022-11-24`) — it failed
  deterministically at preflight (`Lookback validation FAILED: 21/21 instruments have insufficient candles`, only 96/182
  required candles on `2022-11-01`, the very first day real data exists). This is a genuine, non-fixable lookback-warmup
  limit (no history predates the corpus start), NOT a bug or real gap — `2022-11-25` IS the true earliest computable
  date, and coverage already reaches it. Do not relaunch that window again. `funding_oi`'s fix-direction was just RULED
  today (= B, source OI from the existing `derivative_ticker` capture) in the sibling
  `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`, but the actual `[BACKEND] P2`
  implementation is NOT yet shipped — correctly left untouched (backend_engineer scope, not mine to freelance). **Cannot
  flip this todo's own done-when** ("D1's checkbox is flipped citing this evidence") — D1's own done-when needs BOTH
  `funding_oi` and `returns` complete; `returns` now genuinely IS complete, but `funding_oi` remains blocked pending
  that unlanded backend join. Full detail in `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo;
  `delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`'s todo 2 flipped RESOLVED-MOOT (doc
  `status: resolved`) on the same finding — there was never a real gap to backfill.
- 2026-07-30 (slot-14): todo 1 shipped — features-service@8e62dc30. `_discover_instruments` now routes to a new
  `_discover_instruments_from_manifest` when every requested `candle_data_types` entry is pass-through
  (`needs_candle_processing()` False); candle-processed and mixed sets keep the unchanged `processed_candles` walk.
  Synthesizes a `{venue}:{DATA_TYPE}:{raw_instrument_id}` id per distinct (venue, instrument_id) manifest pair — the raw
  manifest `instrument_id` (bare feed_id for `oracle_prices`, blank for `perp_funding`'s per-venue bundle rows, since
  the writer records those as venue-level aggregates with no per-instrument granularity) lands in the third colon
  segment, so `_count_candles_for_lookback`'s EXISTING `(venue, symbol)`/`(venue, "")` fallback chain matches it against
  `_build_captured_index` with zero changes to either — verified this actually counts end-to-end for the perp_funding
  blank-id case with a dedicated test (`test_perp_funding_bundle_id_counts_via_existing_blank_key_fallback`), not just
  that discovery returns a non-empty list. 6 new unit tests added in `test_lookback_validation.py`
  (`TestDiscoverInstrumentsPassThroughManifest`); 4 existing `_discover_instruments` call sites updated for the new
  required `candle_data_types` param. `bash scripts/quality-gates.sh` ALL PASSED (17996 tests, 0 failures; sentinel
  written at HEAD 8e62dc30). Todo 2 (P2, DATA-tagged) is next — unblocked, not part of this task's scope.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **2026-08-03 (slot-5, data_pipeline_failure escalation agt-0c3ac6, DP-VM-001/DP_VM_EXIT_NONZERO)**: the
  `exit_code_fleet_monitor` fired a fresh `relaunch_vm` escalation for `features-delta-one-defi-20260802-235804`
  (exit_code=1 — not 137, so out of `RelaunchBackfillVm`'s OOM-only auto-recover scope, hence the escalation to a
  human-judgment worker per `RB-INFRA-RELAUNCH`). Independently re-diagnosed from scratch (GCS `run.log` +
  `EXIT_STATUS` + the DEFI `market-data-tick` availability manifest, not by reading this doc first) and landed on the
  **exact same conclusion slot-6 already recorded above 2026-08-02**: `oracle_prices` manifest-captured rows for DEFI
  start at `2022-11-01` with zero rows before it (`read_availability_index` min date == `2022-11-01`, confirmed live),
  so the `2022-11-01→2022-11-24` window's lookback validation (`buffer_days=2`, needs `2022-10-30`/`10-31`) fails
  deterministically — not a transient/relaunchable fault, and re-running the SAME launcher args would fail identically
  every time (verified: `fail_on_insufficient=not skip_dependency_check`, and the archived launch command passed no
  `--skip-dependency-check`). Per `RB-INFRA-RELAUNCH`'s own bound ("if it re-fails the SAME way twice, the shard is
  wedged ... STOP relaunching") — skipped the wasted first relaunch since the deterministic-failure evidence was already
  conclusive without needing to reproduce it a second time. **Did NOT relaunch this VM.** No code/data action needed —
  this is the same resolved-moot finding, not a new defect. Pinged the authoring monitor slot (`dp-fleet-monitor`) with
  this outcome so a future occurrence of this exact alert for this VM prefix is recognized as expected noise, not a
  fresh incident.
- **2026-08-03 (slot-2, data_engineering craft, dispatched to todo 2)**: `funding_oi`'s backend join fix
  (`features-service@0699c5db`, `[BACKEND] P2` in the sibling
  `defi_delta_one_funding_oi_hyperliquid_missing_open_interest_2026_07_31.md`) landed today, so `funding_oi` was
  legitimately re-dispatchable — but `returns` was already confirmed complete (slot-6, 2026-08-02, above), so this
  session only needed to launch `funding_oi`. Launched the real verification-window run over the confirmed clean window:
  `features-delta-one-defi-20260803-031632` (SPOT, `2023-05-12..2023-10-31`, `--launch-mode full`). Dependency-check +
  lookback-validation both PASSED (confirms THIS doc's own todo-1 fix is holding correctly in production) — but every
  processed date hit the SAME 100%-NaN open_interest/mark_price/index_price rejection the sibling doc's `[BACKEND] P2`
  fix was supposed to have resolved; VM exited `rc=1`, `ALL feature groups failed: ['funding_oi']`; independently
  re-verified against the manifest itself (not just the log) — the run's per-VM shard has exactly 1 row,
  `capture_status=attempted_failed`, zero `record_captured`. This is a NEW, distinct bug from the one this doc fixes —
  confirmed `derivative_ticker` HYPERLIQUID data genuinely exists in-window (live GCS check), so the join is failing to
  MATCH real available data, not failing on absent data. Full evidence + a new `[BACKEND] P1` todo filed in the sibling
  doc (its Progress Log, same date) rather than duplicating the investigation here — this doc's craft-scope
  (data_engineering) correctly stops at launch-and-diagnose, not backend debugging. **Still cannot flip this todo's own
  done-when** — `returns` remains complete, `funding_oi` is now blocked on the sibling doc's `[BACKEND] P1` instead of
  its (now-insufficient) `[BACKEND] P2`. No manifest-integrity issue from this run — the one row written is an honest
  `attempted_failed`, not a masked success. Did not relaunch — the failure is systematic across every processed date
  (not a one-off), so a retry with the same code would reproduce identically; re-attempt only after `[BACKEND] P1`
  lands.
- **2026-08-03 (slot-14, data_engineering craft, dispatched to this same todo 2 right after skipping its near-duplicate
  `delta_one_candle_loader_no_pass_through_path_defi-003`)**: re-confirmed nothing has changed since slot-2's entry
  above — `defi_delta_one_funding_oi_hyperliquid_missing_open_interest-006` (the `[BACKEND] P1` fix) is still
  `dispatched` to slot 4 in the live backlog, not yet shipped. Skipping rather than re-launching the same doomed
  `funding_oi` run or idling; see `delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`'s matching entry
  (`unified-trading-pm@88a43a57d`) for the full cross-reference.
- **2026-08-03 (slot-9, data_engineering craft, dispatched to this same todo 2)**: re-checked from scratch (not trusting
  the prior slots' snapshot) — `features-service` fresh-pulled to HEAD `18fd5181`; `git log` on `_passthrough_loader.py`
  still shows `0699c5db` as the newest commit touching that file (no new commit past the `[BACKEND] P2`
  join-implementation landed). Cross-checked the live local backlog (`curl localhost:8765/api/backlog`, not just
  re-reading this doc) directly: `defi_delta_one_funding_oi_hyperliquid_missing_open_interest-006` (`[BACKEND] P1`, the
  symbol-match fix) is still `status: "dispatched", dispatched_to: 5` — genuinely in flight, not stalled/abandoned.
  Block persists; not a new finding. Did NOT relaunch `funding_oi` (same deterministic failure the prior 2 attempts
  already reproduced) and did NOT touch `[BACKEND]`-scoped code (craft-scope, not mine to freelance). Skipping this task
  rather than idling — `[BACKEND] P1` landing is what unblocks re-attempt.
- **2026-08-03 (slot-8, backend_engineer craft, backlog task `delta_one_candle_loader_no_pass_through_path_defi-003`) —
  todo 2 CLOSED as a duplicate-close.** `[BACKEND] P1` (`features-service@6b2282c5`) landed; ran the real
  verification-window resume this todo and its near-duplicate twin both called for
  (`delta_one_candle_loader_no_pass_through_path_defi_2026_07_30.md`'s own todo 2 — full evidence there, not duplicated
  here): `features-delta-one-defi-20260803-055145`, 454/455 manifest shards `captured`. D1's checkbox flipped in
  `defi_satellite_ao_dispatch_batch3_2026_07_26.md`. This closes every todo in this doc.
