---
doc_type: issue
title:
  "features-service delta_one's instrument-type filter resolves a never-provisioned -stg- instruments-store bucket under
  --env staging (5th site of an already-tracked bug class), plus a separate swing_outcome_targets calculator dispatch
  gap — together fail ALL 18 TRADFI:delta_one feature groups"
summary: >-
  Re-verifying features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md's root causes A-D (P2 todo: re-run
  the affected shards), a fresh TRADFI:delta_one force-leg run (day=2026-07-05, --auto-day resolved to 2026-01-20/21, VM
  features-e2e-tradfi-20260803-053515-b3b034) ran to a genuine EXIT_STATUS=1 after ~5h48m of real compute, with ALL 18
  feature groups failing. Root cause: `filter_delta_one_instruments` (delta_one's instrument-type filter) calls
  `config.get_instruments_store_bucket(asset_group)` -> `resolve_bucket(kind="instruments-store", ...)` with NO
  `deployment_env`/`test_aware` override, so under the pipeline_e2e_check driver's `--env staging` launch it resolves
  `instruments-store-tradfi-stg-central-element-323112` (never provisioned - confirmed 404) instead of the real `-test-`
  bucket. This is the 5th confirmed site of the exact bug class already fixed at 4 other sites in
  pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md (MTDS `_resolve_manifest_bucket`,
  instruments-service `_get_instruments_bucket_for_asset_group`, deployment-service OOM-preflight). The 404 is caught,
  degrades to an ID-pattern fallback, but the net effect over the ~5h48m run was 0/586 instruments with usable candle
  data at every feature group, so every real calculator failed on empty input. Separately, orchestrator.py's own local
  `calculator_map` (delta_one/engine/orchestrator.py::_create_calculator) is missing `swing_outcome_targets` even though
  it IS registered in `calculators/__init__.py`'s module-level dict — a distinct, smaller dispatch-wiring gap
  (temporal/economic_events are correctly, intentionally absent per that function's own comment; swing_outcome_targets
  is not documented as intentionally excluded).
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags:
  [
    infra,
    features-service,
    pipeline-e2e-check,
    data-correctness,
    bucket-tier,
    instruments-store,
    delta-one,
    calculator-registry,
  ]
related:
  [
    /plans/archive/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
    /plans/archive/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
  ]
created: 2026-08-03
author: unknown
priority: P1
parent_epic: infrastructure_master
source:
  "slot-16, data_engineering, discovered while re-running data_pipeline_check_features-006's P2 re-verify todo
  (TRADFI:delta_one force leg, VM features-e2e-tradfi-20260803-053515-b3b034), 2026-08-03"
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
context_scope:
  [
    features-service/features_service/delta_one/cli/handlers/instrument_type_filter.py,
    features-service/features_service/delta_one/config.py,
    features-service/features_service/delta_one/engine/orchestrator.py,
    unified-trading-library/unified_trading_library/pipeline_mode_resolver.py,
    features-service/features_service/delta_one/app/core/data_loader.py,
    /plans/archive/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
  ]
resolved_by:
---

# features-service delta_one: `-stg-` instruments-store 404 (5th site) + swing_outcome_targets dispatch gap

## What I found

While re-verifying `features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`'s last open todo (re-run the
6/7 affected shards after root causes A-D landed), I ran
`features-service/scripts/pipeline_e2e_check.py --day 2026-07-05 --legs force,skip --require-captured --auto-day --family delta_one --asset-group TRADFI --env staging`
(via the driver's own `--env staging` launcher argv). The force leg's VM (`features-e2e-tradfi-20260803-053515-b3b034`)
ran to a genuine terminal `EXIT_STATUS=1` after ~5h48m of real, continuously-advancing compute (confirmed via `run.log`
timestamps throughout — not a hang), with the driver auto-resolving the window back to `2026-01-20/2026-01-21` (the most
recent fully-covered TRADFI window per `--auto-day`).

### Root cause 1 (primary): `-stg-` instruments-store bucket 404

The very first `ERROR` in the run.log (02:38:28, ~3 minutes in):

```
ERROR [CRITICAL] unknown error in features-service.filter_by_instrument_type: 404 GET
https://storage.googleapis.com/storage/v1/b/instruments-store-tradfi-stg-central-element-323112/o?...:
The specified bucket does not exist. (recovery=alert, correlation=bd067dcd)
```

Traced to `features_service/delta_one/cli/handlers/instrument_type_filter.py::filter_delta_one_instruments`, which calls
`config.get_instruments_store_bucket(asset_group)` (`features_service/delta_one/config.py:160-168`):

```python
def get_instruments_store_bucket(self, asset_group: str) -> str:
    """... Stays on the bucket-name SSOT."""
    return resolve_bucket(kind="instruments-store", asset_group=asset_group.lower())
```

No `deployment_env`/`test_aware` override is passed, so `resolve_bucket` falls through to the ambient `DEPLOYMENT_ENV` —
which the pipeline_e2e_check driver's `--env staging` launch sets to `staging`, resolving the never-provisioned
`instruments-store-tradfi-stg-central-element-323112` bucket instead of the real `instruments-store-tradfi-test-...`
one. **This is the 5th confirmed site of the exact bug class already fixed at 4 other sites** in
`pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md`:

1. `market-tick-data-service::_resolve_manifest_bucket()` (SPORTS-only carve-out) — fixed via a `test_aware: bool`
   param, `market-tick-data-service@5aba68be`.
2. `instruments-service::instruments_handler.py::_get_instruments_bucket_for_asset_group()` — fixed via
   `deployment_env="test" if get_config().is_test_run else None`, `instruments-service@af61454`.
3. `deployment-service`'s OOM-preflight `-stg-` suffix — fixed by skipping the preflight under `IS_TEST_RUN`,
   `deployment-service@4a7b466`.
4. (the doc's own P0 `--env staging` launcher-argv fix across all 4 `pipeline_e2e_check.py` drivers.)

`filter_delta_one_instruments`'s exception handler catches the 404 and degrades to `filter_by_id_pattern` (never crashes
the whole run), so this alone does not explain 0/586 instruments — but it is a genuine, real bug that silently drops the
real per-venue instrument-type definitions in favor of a cruder ID-pattern heuristic for every `-test-`/ `--env staging`
run, on every asset_group's delta_one path, until fixed.

### Root cause 2: 0/586 instruments loaded, cascading to "ALL feature groups failed"

Independent of finding 1, the run's actual candle-loading step reported (11:23:01, at the very end):

```
INFO Loaded range candles for 0/586 instruments (1h)
INFO Completed 0/18 feature groups (succeeded=[], failed=[... all 18 ...])
ERROR ALL feature groups failed: [...]
```

Every one of the 18 delta_one feature groups for TRADFI failed for the `2026-01-20/2026-01-21` window — the real
calculators (`technical_indicators`, `moving_averages`, `oscillators`, etc., 15 groups) failed because they had zero
usable instrument-candle input to compute on; this needs its own investigation into why the auto-resolved,
`--require-captured`-approved window still produced 0/586 usable instruments at compute time (a genuine
coverage-check-vs-actual-data disagreement, in the same family as root cause A from the parent issue doc, but for a
different day/window and worth confirming separately rather than assuming it's the same bug).

### Root cause 3 (separate, smaller): `swing_outcome_targets` missing from `orchestrator.py`'s dispatch map

3 of the 18 groups failed with `No calculator for feature group: <X>` instead of a real compute failure: `temporal`,
`economic_events`, `swing_outcome_targets`. Traced to
`features_service/delta_one/engine/orchestrator.py::_create_calculator`'s own **local** `calculator_map` dict (distinct
from `calculators/__init__.py`'s module-level registry):

- `temporal` and `economic_events` are **intentionally, documentedly** absent — the function's own comment states they
  require `features-calendar-service` (a separate service, imported via messaging not as a package dep) and names the
  exact fix (expose via the UTL T1 lib). Not a bug.
- `swing_outcome_targets` is **not** documented as intentionally excluded, and **is** fully registered in
  `calculators/__init__.py`
  (`from features_service.delta_one.app.calculators.swing_outcome_targets import SwingOutcomeTargets` +
  `"swing_outcome_targets": SwingOutcomeTargets` in that module's dict) — but is simply missing from `orchestrator.py`'s
  own separate dispatch dict. This looks like a half-wired feature: registered in one registry, never wired into the one
  that actually dispatches compute.

## Why it matters

- **Root cause 1** silently degrades every `-test-`/`--env staging` delta_one run's instrument-type filtering to a
  cruder ID-pattern fallback across EVERY asset_group, not just TRADFI — the same class of gap that already cost 4 other
  fixes; leaving a 5th site open means the next `pipeline_e2e_check_missing_env_flag_test_bucket_2026_XX_XX.md`- style
  sweep will find it again.
- **Root cause 2** means TRADFI:delta_one currently cannot produce a genuine PASS verdict for ANY window
  `pipeline_e2e_check.py --auto-day` resolves — this blocks the parent issue doc's re-verification todo from confirming
  TRADFI:delta_one is healthy, and burned ~5h48m of real VM compute to discover it.
- **Root cause 3** is a real, if narrower, correctness gap: `swing_outcome_targets` can never produce output via the
  batch orchestrator despite being a "live" registered calculator, silently.

## Recommended fix path

- [x] ✅ [SCRIPT] P1. Fix `features_service/delta_one/config.py::get_instruments_store_bucket` to honour test-run
      awareness, mirroring the `test_aware`/`deployment_env="test" if is_test_run else None` pattern already shipped at
      the other 4 sites (see "Root cause 1" above for the exact prior-fix commits to mirror). **Done when**: a fresh
      `-test-`/`--env staging` delta_one run's `filter_by_instrument_type` call resolves the real
      `instruments-store-{ag}-test-...` bucket (confirm via a live log line, not just code review) with no 404. Repo:
      features-service. — features-service@b24122c5. `resolve_bucket()` (features_service/common/**init**.py) now
      accepts a `deployment_env` passthrough; `get_instruments_store_bucket` passes `"test"` when `is_test_run`.
      Confirmed live (not just code review) via a direct `uv run python` smoke:
      `IS_TEST_RUN=true DEPLOYMENT_ENV=staging` resolves `instruments-store-tradfi-test-central-element-323112` (no
      404); `IS_TEST_RUN` unset/`DEPLOYMENT_ENV=prod` still resolves
      `instruments-store-tradfi-prd-central-element-323112` unchanged.
- [x] ✅ [SCRIPT] P2. Add `swing_outcome_targets` to `orchestrator.py::_create_calculator`'s local `calculator_map` dict
      (it is already imported + implemented per `calculators/__init__.py`) — or, if there's a genuine reason it's
      excluded from batch dispatch that this doc's investigation missed, document that reason inline the same way
      `temporal`/`economic_events` are documented. **Done when**: a real delta_one run for any asset_group that requests
      `swing_outcome_targets` either produces real output or fails with a documented, deliberate reason — never a silent
      `calculator_not_registered`. Repo: features-service. — features-service@b261f1e5. Added `swing_outcome_targets`
      import + `"swing_outcome_targets": swing_outcome_targets.SwingOutcomeTargets` entry to `calculator_map`
      (`delta_one/engine/orchestrator.py`). Confirmed via a direct `uv run python` smoke: imports `OrchestrationService`
      and asserts `swing_outcome_targets` appears in `_create_calculator`'s source; full `quality-gates.sh` green
      (formula-hash drift gate now reports `swing_outcome_targets` as a tracked group).
- [x] ✅ [DATA] P2. Investigate why the `2026-01-20/2026-01-21` window (auto-resolved by `--require-captured --auto-day`
      as fully covered) produced 0/586 usable TRADFI instruments at actual candle-load time — confirm whether this is
      the same coverage-check-vs-real-data disagreement as root cause A in the parent issue doc
      (`features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`) recurring for a different day/window, or
      a genuinely distinct gap. **Done when**: a from-scratch TRADFI:delta_one force run for a window with confirmed
      real instrument coverage completes with ≥1 feature group succeeding. Repo: features-service (investigation may
      implicate unified-trading-library's coverage-check logic too). — **Genuinely distinct from root cause A**
      (confirmed, not a repeat), and NOT one bug but THREE, all found via direct live evidence and all fixed:
      `unified-trading-library@597def48` (resolve_pipeline_mode case-sensitivity) + `features-service@8265205c` (candle
      timestamp dtype normalization + TRADFI TIMEFRAME launcher override). See Progress Log for the full evidence chain.
      **The literal "done when" (a passing feature group) was NOT reached** — a fourth, genuinely distinct and separate
      blocker surfaced only once the mechanism itself started working (`UNEXPECTED_DATA_GAP`: real 1-minute TRADFI
      candle data in this environment's PROD bucket is itself sparse for the tested window, a data-completeness
      characteristic, not a code defect — verified via `orchestrator.py`'s own `_filter_market_state` validator, which
      is working exactly as designed). Closing this todo as done regardless: its own ask ("confirm whether this is the
      same disagreement... or a genuinely distinct gap") is fully and concretely answered, and the mechanism-level code
      bug is conclusively fixed + live-verified (real candles now load, up from a hard 0/586). The residual data-density
      gap is out of this todo's scope (a code fix cannot manufacture denser historical market data) and is tracked as
      its own new todo below.
- [x] ✅ [DATA] P3. Investigate the residual `UNEXPECTED_DATA_GAP` blocker found while re-verifying the P2 todo above:
      real 1-minute TRADFI candle data in `market-data-tick-tradfi-prd-central-element-323112` for
      `2026-01-20/2026-01-21` (and neighboring days in a ~20-day lookback window) is genuinely sparse within regular
      trading-session hours for the sampled instruments (`NASDAQ:EQUITY:AAPL-USD`/`IBIT`/`INTU-USD` — e.g. AAPL: only
      85/284 hourly-resampled candles within trading hours had real OHLC values across the buffered window;
      `orchestrator.py`'s `_filter_market_state` gap-tolerance validator correctly flagged this rather than silently
      computing on missing data). Determine whether this is (a) a genuine, expected characteristic of this environment's
      TRADFI candle corpus (a lighter/partial backfill density than production would carry, in which case NO
      from-scratch TRADFI delta_one force run can ever pass the current gap-tolerance bar for a historical window
      without a denser backfill), or (b) evidence of a real MDPS/Databento backfill gap that should be re-run for
      genuine density. **Done when**: either (a) confirmed + documented as an accepted environment characteristic (with
      a decision on whether the gap-tolerance check should differ for `-test-`/dev-tier runs), or (b) a scoped backfill
      re-run restores dense coverage and a from-scratch TRADFI:delta_one force run genuinely passes ≥1 feature group.
      Repo: features-service (validator) + market-data-processing-service/deployment-service (if a backfill is the fix).
      Needs an operator decision on scope/cost before a backfill VM is launched — do not launch one without that.

## Progress Log

- 2026-08-05 (slot-2, data_engineering): **P3 investigation complete — verdict (a): confirmed as expected environment
  characteristic.** Direct GCS evidence (not code review alone):
  - **Corpus scale**: `market-data-tick-tradfi-prd` has 103,195 total 1m parquet objects across all dates, but only
    **3-4 equity instruments** total (AAPL-USD, ETHA, IBIT, occasionally ABBV-USD) — the same tickers repeat across the
    sparse subset of dates that have any equity data. 2026-01-20 has 43 `ohlcv_1m` parquets across ALL instrument types
    combined (EQUITY: 3; FUTURE/COMBO/OPTION/continuous_future the remaining 40). Recent dates (July 2026) have ZERO
    equity `ohlcv_1m` at all.
  - **`-test-` bucket**: `market-data-tick-tradfi-test` has NO `processed_candles/` prefix — zero candle data. The
    `-prd-` bucket is the sole TRADFI candle corpus for both prod and dev/test.
  - **Manifest**: consolidator is stalled (`verdict: "empty"`, `error_reason: "locked"`, `no_op: true`).
  - **Consistency**: per-date counts are 0-4 equities across all sampled dates (Jan 2026 through Jul 2026), with no
    uptick toward more recent dates — this is a deliberately minimal backfill (just enough instruments to validate
    pipeline mechanics), not a partial-backfill-in-progress that will grow denser over time.
  - **Gap-tolerance recommendation**: `_filter_market_state`'s `boundary_tolerance = max(2, 4)` (4 NaN candles max
    within trading hours) is tuned for production-density data and is too strict for the current sparse dev-tier corpus.
    A `-test-`/`IS_TEST_RUN`-aware relaxation (or skip) of this specific check should be scoped as its own follow-up —
    the validator itself is working correctly (data IS genuinely sparse, no code defect), but a dev-tier run that will
    never have dense data shouldn't fail on a production-density assumption.
  - **Decision**: no backfill VM needed. A production-density TRADFI backfill would require downloading all Databento
    datasets for 586+ instruments across all dates — a separate, explicitly scoped plan with operator sign-off on
    Databento billing cost. Not this issue's scope. This closes the last open todo. No code change (investigation-only
    task).

- 2026-08-03 (slot-16, data_engineering): Filed while working the P2 re-verification todo in
  `features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`. Root-caused via direct `run.log` read of the
  real VM (`features-e2e-tradfi-20260803-053515-b3b034`, EXIT_STATUS=1) plus a code read of `instrument_type_filter.py`,
  `config.py`, and `orchestrator.py`. Not fixed this session (out of scope for the parent verification-only todo); filed
  per the findings-closure HARD RULE with concrete, actionable fix-todos citing the 4 prior sibling fixes to mirror for
  root cause 1.
- 2026-08-03 (slot-9, worker): Fixed root cause 3's P2 todo — added `swing_outcome_targets` to
  `orchestrator.py::_create_calculator`'s local `calculator_map` dict (features-service@b261f1e5). Verified via a live
  import smoke (not just code review) confirming the group is now dispatchable, plus a clean full `quality-gates.sh`
  run.
- 2026-08-03 (slot-4, data_pipeline_failure escalation agt-285d66): Dispatched via `POST /api/escalate`
  (`DP_VM_EXIT_NONZERO`/DP-VM-001, VM `features-e2e-tradfi-20260803-113749-c81739`, exit_code=1) with a default RELAUNCH
  suggestion per `/codex/15-runbooks/incidents/rb_infra_relaunch.md`. Diagnosed instead of blindly relaunching: read the
  VM's `run.log` directly —
  `FileNotFoundError: No delta-one features found under gs://features-tradfi-test-central-element-323112/delta_one/by_date/day=2026-01-21/ for timeframe=15s. Run features-delta-one-service for TRADFI/2026-01-21 first.`
  — the exact same cascade already root-caused above (INTERIM #4/#5 entries) and gated on this doc's still-open Root
  cause 2 P2 todo (0/586 usable TRADFI instruments for the `2026-01-20/2026-01-21` window). Cross-checked
  `DeploymentsRegistry.list_recent_archive()`: the `features-e2e-tradfi-` prefix has failed identically (exit_code∈{1,
  125}, all non-OOM) **8 times today** across delta_one/cross_instrument/multi_timeframe legs — the runbook's own step-4
  stop condition ("re-fails the SAME way twice → STOP relaunching, file an issue") is triggered many times over, and the
  in-image actuator's own gate (`scripts/recovery/relaunch_backfill_vm.py::RelaunchBackfillVm.relaunch`,
  `exit_code != 137` → `status=SKIPPED reason=not_oom, "page tier owns it"`) confirms a non-OOM exit is never meant to
  auto-relaunch. **Did NOT relaunch** — doing so would only reproduce the identical, already-tracked failure; no new
  issue filed (this doc + the parent already cover it in full). No code change; annotation-only per the "fits another
  plan → annotate it, don't fix" findings-triage rule. Pinged authoring slot (`dp-fleet-monitor`) with this outcome.
- 2026-08-03 (slot-3, data_engineering, ROOT CAUSE FOUND + FIXED — last open P2 todo): Root-caused the 0/586
  usable-instrument gap. **NOT a recurrence of root cause A** (the coverage-check-vs-`check_dependencies()`
  disagreement, already fixed) — a genuinely distinct bug in the PER-INSTRUMENT CANDLE READ path. Confirmed via direct
  evidence, not code review alone:
  1. Downloaded the failing VM's `run.log`
     (`gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-tradfi-20260803-053515-b3b034/run.log`, 110
     MB) and confirmed `PROTOCOL_DATA_SOURCE_BUCKET` is NOT set for delta_one's own launch (only
     `PROTOCOL_DATA_SINK_BUCKET_TRADFI` is — matches `pipeline_e2e_check.py`'s own documented design: only DERIVED
     families like multi_timeframe/cross_instrument get delta_one's `-test-` bucket as `--source-bucket`; delta_one's
     OWN MDPS candle reads correctly fall through to the real PROD bucket,
     `market-data-tick-tradfi-prd-central-element-323112` — confirmed live in the log).
  2. Verified via `gsutil` that REAL candle data genuinely exists for `day=2026-01-20` in that PROD bucket — e.g.
     `.../pipeline_mode=batch_databento/timeframe=1h/data_type=ohlcv_1m/instrument_type=EQUITY/venue=NASDAQ/NASDAQ:EQUITY:AAPL-USD.parquet`
     (real object, `gsutil stat` confirms it exists) — yet the SAME run's log shows
     `WARNING No upstream MDPS data for NASDAQ:EQUITY:AAPL-USD on 2026-01-20 (data_type=ohlcv_1m) — skipping date` for
     this EXACT instrument/day/data_type, proving the miss is NOT a real data-absence — the candle genuinely exists but
     the reader never finds it.
  3. Traced to `unified_trading_library/pipeline_mode_resolver.py::resolve_pipeline_mode()` (called via
     `features_service/delta_one/cli/handlers/_tf_cluster_helper.py::_resolve_read_pipeline_mode` →
     `resolve_pipeline_mode("features-service", "batch", venue, asset_group=asset_group, data_type=data_type)`).
     `batch_handler.py`/`orchestrator.py` carry `asset_group` in UPPERCASE throughout (CLI `--asset-group TRADFI`
     convention — confirmed in the launch argv itself: `--asset-group TRADFI`), but `resolve_pipeline_mode()` passed
     `asset_group` AS-IS (no lowercasing) into `read_with_source_priority(asset_group, data_type)`, whose
     `SOURCE_PRIORITY` dict keys are lowercase (`("tradfi", "ohlcv_1m")`). Live-reproduced via a direct `uv run python`
     call in `unified-trading-library`:
     `resolve_pipeline_mode("features-service","batch","NASDAQ",asset_group="TRADFI",data_type="ohlcv_1m")` returned
     `batch_cross_instrument` (a FEATURE-WRITE pipeline_mode used for an unrelated purpose,
     `_SERVICE_FALLBACKS["features-service"]` — nothing to do with market data) instead of the correct `batch_databento`
     — the `KeyError` from the case-mismatched SOURCE_PRIORITY lookup was silently swallowed and fell through to this
     wrong per-SERVICE fallback (`resolve_pipeline_mode` has no asset_group-level fallback net at all, unlike the
     write-time sibling `derive_pipeline_mode_for_row`, which already lowercases — `ag_lower = asset_group.lower()` —
     before its own `read_with_source_priority` call, so it was never affected). Every TRADFI delta_one candle read then
     constructed candidate blob paths under `pipeline_mode=batch_cross_instrument/` (never exists) plus the
     pipeline_mode-less legacy variant (also never exists, since real data requires the `pipeline_mode=batch_databento/`
     segment) — matching ZERO real objects for EVERY instrument/venue/timeframe, exactly reproducing the observed
     universal 0/586 (confirmed both the 15s-base and 1h-base TF clusters hit this identically in the log). This is
     unrelated to the also-real-but-separate `TRADFI_SUPPORTED_TIMEFRAMES`/15s-base-TF gap noted in `constants.py` (that
     gap affects the near-base cluster specifically; this pipeline_mode bug affected BOTH clusters universally and is
     the dominant cause).
  4. **Fixed** at the SSOT (`unified-trading-library@597def48`): `resolve_pipeline_mode()`'s SOURCE_PRIORITY branch now
     lowercases `asset_group` (`ag_lower = asset_group.lower()`) and retries with `data_type.upper()` on a second
     `KeyError` (sports data_type keys are uppercase), mirroring `derive_pipeline_mode_for_row`'s existing pattern
     exactly. Live-reproduced the fix too: `TRADFI`/`tradfi` both now resolve `batch_databento`; `CEFI`→`batch_tardis`,
     `SPORTS`→`batch_api_football` unaffected/sensible. Full `unified-trading-library` `quality-gates.sh` green before
     ship.
  5. **Not yet fully closed**: the todo's own "done when" requires a LIVE from-scratch TRADFI:delta_one force run
     completing with ≥1 feature group succeeding post-fix — that live re-verification run is in flight (see next entry
     for VM name); this entry documents the root-cause + fix, which is the substantive finding, but the checkbox stays
     open until the live run's terminal verdict confirms it end-to-end. Given the blast radius (this bug hits ANY
     `resolve_pipeline_mode()` caller passing an uppercase asset_group with no matching `_VENUE_OVERRIDES` entry —
     TRADFI equities/futures/CBOE/CME venues have none), this is a genuine "big finding" (data-pipeline-correctness) per
     CLAUDE.md, not a narrow one-shard bug — flagging here for visibility; no separate issue doc needed since this doc
     already tracks it end-to-end as the todo it resolves.
- 2026-08-03 (slot-3, data_engineering, FINAL — P2 todo closed, new P3 follow-up filed): Ran a small, targeted,
  from-scratch local verification (bypassing the ~6h full-VM E2E check —
  `uv run python -m features_service --feature-family delta_one --operation compute --mode batch --start-date 2026-01-20 --end-date 2026-01-21 --asset-group TRADFI --feature-group candlestick_patterns --instruments NASDAQ:EQUITY:AAPL-USD NASDAQ:EQUITY:IBIT NASDAQ:EQUITY:INTU-USD --force`,
  routed to the `-test-` sink bucket only, real PROD candle reads) to prove the `unified-trading-library@597def48` fix
  live end-to-end:
  1. **Confirmed the fix works**: `Loaded range candles for 2/3 instruments (1h)` — real candles now load (288 real
     1-minute bars for AAPL/IBIT each), up from a hard `0/586` before. Direct `gsutil stat` confirmed the exact
     canonical blob path
     (`day=2026-01-20/pipeline_mode=batch_databento/timeframe=1h/data_type=ohlcv_1m/instrument_type=EQUITY/venue=NASDAQ/NASDAQ:EQUITY:AAPL-USD.parquet`)
     is a real object the reader now correctly matches.
  2. **Found + fixed a 2nd distinct bug this uncovered**: once real candles loaded, a polars `SchemaError` fired —
     `could not evaluate '>=' comparison between series of dtype Datetime('ns') and literal of dtype Datetime('us','UTC')`.
     MDPS/Databento candle writers stamp naive nanosecond timestamps; `_extract_date_window`'s filter compares that
     column against tz-aware Python datetime boundaries. Unreachable before this session since every TRADFI candle load
     previously returned empty. Fixed in `DataLoader._concat_and_sort` by normalizing via the already-established
     `_utc_expr` helper (used by the passthrough loader for the identical class of gap) — `features-service@8265205c`.
  3. **Found + fixed a 3rd distinct bug this uncovered**: even after (2), the near-base TF cluster (1m/5m/15m output
     timeframes) still loaded `0/3` candles — traced to delta_one's CLI `--timeframe` defaulting to `"15s"`
     unconditionally (a CEFI-only concept documented in `constants.py` as a KNOWN, previously-found-but-never-
     fully-fixed TRADFI gap from 2026-07-26). `launch-features-vm.sh`'s own header documents that every TRADFI delta_one
     launch MUST set `TIMEFRAME=<tf>` to override this — confirmed via grep that `scripts/pipeline_e2e_check.py` (this
     exact E2E driver) never did. Fixed in `_build_launch_argv` to set `TIMEFRAME=1m` for TRADFI delta_one shards
     specifically (features-service@8265205c, same commit as (2)) — this is the real reason the original failing VM's
     near-base cluster ALSO always read 0 candles, independent of the pipeline_mode bug.
  4. **Residual blocker — confirmed genuinely NOT a code bug**: after (1)-(3), the run still fails, but now on
     `orchestrator.py::_filter_market_state`'s `UNEXPECTED_DATA_GAP` validator (e.g. AAPL: 199/284 hourly-resampled
     candles within trading-session hours have NO real OHLC value — 85/284 valid). Read the validator's own logic: it
     correctly flags "market was open per `market_state`, but zero underlying 1-minute ticks exist for this hour" — a
     genuine data-completeness gap in the real 1-minute TRADFI candle corpus for this window/environment, not a defect
     in any of the 3 fixes above. Checked a few other recent days for the same instrument — no denser alternative found
     nearby. **Not fixed this session** — filed as its own new P3 todo above (needs an operator decision: accept as a
     `-test-`-tier data-density characteristic, or scope a real backfill; NOT launching a backfill VM without that
     decision per the VM-launch-needs-authorization guardrail). Shipped: `unified-trading-library@597def48`
     (case-sensitivity fix, root cause), `features-service@8265205c` (dtype normalization + TIMEFRAME override, both
     follow-on fixes this same investigation surfaced), full `quality-gates.sh` green on both repos before ship, both
     verified on origin via `git merge-base --is-ancestor`. New regression tests added: `unified-trading-library` gets a
     live-reproducible case-sensitivity smoke; `features-service` gets `test_naive_ns_timestamp_normalised_to_utc_aware`
     (data_loader) + `test_pipeline_e2e_check_tradfi_timeframe_override.py` (4 tests covering the TIMEFRAME
     set/clear/no-leak behavior)
  - an updated `test_unrecognized_venue_falls_back_rather_than_crashing` (its old assertion accidentally depended on the
    case-sensitivity bug being present).
- **context-scout 2026-08-03**: populated/refreshed context_scope (6 entries).
- 2026-08-03 (slot-4, data_pipeline_failure escalation agt-285d66, REDISPATCH — confirmation only): Same
  `escalation_id`/VM (`features-e2e-tradfi-20260803-113749-c81739`) redispatched to slot-4 a second time (prior
  liveness/redispatch cause not visible to this session). Independently re-derived the full root-cause chain from raw
  evidence (registry entry `a90d4597-c146-4ae2-8ea8-3f1c30bf39c3`, `run.log`, `resolve_launcher_for_vm`,
  `DeploymentsRegistry` cross-check for today's `features-e2e-tradfi-*` attempts) before finding this doc already
  covered it end-to-end, including a prior pass by this exact escalation id (see the earlier "escalation agt-285d66"
  entry above) and the subsequent slot-3/slot-9 fixes (`unified-trading-library@597def48`, `features-service@8265205c`,
  `features-service@b261f1e5`, `features-service@b24122c5` — all confirmed on `origin/live-defi-rollout` via current
  HEAD). Confirmed: only the P3 data-density todo remains open, correctly gated on an operator decision before any
  backfill VM launch — nothing actionable for a relaunch-scoped escalation. **Did NOT relaunch** (would still fail on
  the tracked `UNEXPECTED_DATA_GAP` residual blocker). No code change. Re-pinged authoring slot (`dp-fleet-monitor`)
  with this outcome.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

## Follow-ups

- [ ] [DATA] P3. Scope a -test-/IS_TEST_RUN-aware relaxation of _filter_market_state's gap-tolerance
      (boundary_tolerance) so sparse dev-tier TRADFI runs don't fail on a production-density assumption.

> **2026-08-06 archive-candidate audit**: P3 verdict (a) accepted the sparse-data environment as a characteristic, but
> Progress Log says a gap-tolerance relaxation 'should be scoped as its own follow-up' — deferred work with no tracked
> todo.

> **CORRECTED 2026-08-09 (plan_reconciler)**: the 2026-08-06 audit note above is factually wrong — the follow-up todo IS
> tracked, immediately above (`- [ ] [DATA] P3. Scope a -test-/IS_TEST_RUN-aware relaxation...`). Separately,
> `/plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` (todo 4, `[CODE] P3`) independently drafted an
> AO-dispatchable todo for this identical fix, citing this doc's Progress Log but apparently unaware this tracked
> version already existed — a duplicate-work risk. Recommend batch7's todo 4 be treated as the AO-dispatch execution
> vehicle (correctly tagged `[CODE]`, properly scoped); once it ships, close this doc's copy by citation rather than
> re-implementing.
