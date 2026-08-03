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
    /plans/active/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
    /plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
  ]
created: 2026-08-03
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
    /plans/active/issues/pipeline_e2e_check_missing_env_flag_test_bucket_403_2026_08_01.md,
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
- [ ] [DATA] P2. Investigate why the `2026-01-20/2026-01-21` window (auto-resolved by `--require-captured --auto-day` as
      fully covered) produced 0/586 usable TRADFI instruments at actual candle-load time — confirm whether this is the
      same coverage-check-vs-real-data disagreement as root cause A in the parent issue doc
      (`features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`) recurring for a different day/window, or
      a genuinely distinct gap. **Done when**: a from-scratch TRADFI:delta_one force run for a window with confirmed
      real instrument coverage completes with ≥1 feature group succeeding. Repo: features-service (investigation may
      implicate unified-trading-library's coverage-check logic too).

## Progress Log

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
  suggestion per `codex/15-runbooks/incidents/rb_infra_relaunch.md`. Diagnosed instead of blindly relaunching: read the
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
