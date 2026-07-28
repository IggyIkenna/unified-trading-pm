---
doc_type: issue
title:
  features-service delta_one's dependency checker resolves the WRONG market-data-tick bucket name for PREDICTION
  ("prediction" instead of "pred") — every PREDICTION:delta_one run fails its MDPS dependency check regardless of real
  data availability
summary: >-
  Running `/data-pipeline-check-features`'s benchmark leg for `PREDICTION:delta_one` (day=2026-07-19, 7-day window), the
  run failed its upstream dependency check with "The specified bucket does not exist" for
  `market-data-tick-prediction-central-element-323112`. The REAL bucket (confirmed via `gcloud storage buckets list`) is
  `market-data-tick-pred-prd-central-element-323112` — PREDICTION is the one asset_group whose bucket-name token is
  abbreviated to `pred`, not spelled out. `features_service/delta_one/app/core/dependency_checker.py`'s
  `_format_template_vars` does a naive `asset_group.lower()` with no abbreviation mapping, so every PREDICTION
  dependency check is checking a bucket that has never existed — this fails BEFORE the real data-availability question
  is ever asked, for every day, regardless of whether MDPS candles actually exist.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [features-service, delta-one, dependency-checker, bucket-naming, prediction, config-bug]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source: "slot-3, infra, todo 10 benchmark work (data_pipeline_check_mdps_features_2026_07_20.md), 2026-07-27"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# delta_one dependency checker resolves the wrong PREDICTION bucket name

## What I found

Running the `/data-pipeline-check-features` benchmark leg for `PREDICTION:delta_one` (day=2026-07-19, 7-day window
2026-07-12..2026-07-19), the VM (`features-e2e-prediction-20260727-184853-0f2a85`) failed its dependency check
immediately:

```
ERROR Missing: market-data-processing-service
ERROR   Path: gs://market-data-tick-prediction-central-element-323112/processed_candles/by_date/day=2026-07-12/
ERROR   Reason: 404 ... The specified bucket does not exist.
```

**Confirmed via `gcloud storage buckets list --filter="name~'market-data-tick'"`** — the real bucket is
`market-data-tick-pred-prd-central-element-323112` (and its `-test-` sibling `market-data-tick-pred-test-...`). Every
other asset_group uses its full name as the bucket token (`cefi`, `defi`, `tradfi`, `sports`) — **PREDICTION is the one
outlier abbreviated to `pred`**, and the checker's bucket name is missing BOTH the abbreviation AND the `-prd-` env-tier
segment entirely.

**Root cause (direct code read)**: `features_service/delta_one/app/core/dependency_checker.py`:

```python
UPSTREAM_DEPS: ClassVar[dict[str, dict[str, object]]] = {
    "market-data-processing-service": {
        "bucket_template": "market-data-tick-{asset_group_lower}-{project_id}",
        ...
```

and `_format_template_vars` (same file):

```python
def _format_template_vars(self, date: str, asset_group: str) -> dict[str, str]:
    return {..., "asset_group_lower": asset_group.lower(), ...}
```

`asset_group.lower()` on the CLI-passed `"PREDICTION"` produces `"prediction"` — there is no abbreviation-mapping step
anywhere in this file translating it to `"pred"`. This is EXACTLY the same class of bug this file's own comment (lines
~108-114) documents as already found and fixed on the OUTPUT-bucket side: a now-deleted `OUTPUT_BUCKETS` map named
`features-delta-one-prediction-{pid}` when the real bucket was `features-delta-one-pred-*` — fixed by routing output
resolution through `features_service.delta_one.config.get_output_bucket()`, which correctly resolves via the canonical
`cloud-providers.yaml`. **The upstream/input side (this dependency checker's `market-data-tick` bucket resolution) never
got the same fix** — it still hand-rolls the bucket name from a raw template string instead of going through a canonical
resolver that knows about the `pred` abbreviation.

**Not fully resolved this session**: the `UPSTREAM_DEPS` (non-test) `bucket_template` string
(`"market-data-tick-{asset_group_lower}-{project_id}"`) is ALSO missing the `-prd-` env-tier segment that every real
prod bucket has (confirmed: `market-data-tick-tradfi-prd-...`, `market-data-tick-cefi-prd-...`, etc. all have `-prd-`).
Yet a same-session `TRADFI:delta_one` dependency-check failure correctly showed the FULL, correct path
(`market-data-tick-tradfi-prd-central-element-323112/...`) — meaning either this exact `UPSTREAM_DEPS` template isn't
actually the one hit at runtime for non-PREDICTION asset_groups (a different resolution path may be in play that I
didn't fully trace), or `test_mode` behaves differently than assumed. Flagging as unresolved rather than guessing — the
PREDICTION-specific "prediction" vs "pred" token bug is independently confirmed and actionable regardless of this open
question.

## Why it matters

- **Every PREDICTION:delta_one run fails before the real data-availability question is ever asked** — the dependency
  check can never succeed for PREDICTION regardless of whether MDPS candles genuinely exist for the requested date,
  because it's checking a bucket that has never existed. This masks the REAL, separately-confirmed finding (PREDICTION
  MDPS candle production has a ~6-month gap, 2026-01-14 through ~2026-07-24, only just resuming) behind a config/naming
  bug that would ALSO block a request for a day that DOES have real data (e.g. 2026-07-25/26, confirmed to exist in the
  real bucket).
- Blocks `todo 10`'s benchmark measurement for `PREDICTION:delta_one` entirely — no throughput number can be measured
  until this is fixed (or `--skip-dependency-check` is used, not recommended per the checker's own guidance).
- The exact same bug class already bit the OUTPUT side and was fixed — this is the input-side twin, previously missed.

## Recommended fix path

- [x] [SCRIPT] P2. ✅ Route `features_service/delta_one/app/core/dependency_checker.py`'s `market-data-tick` bucket
      resolution through a canonical resolver — `features-service@bba7de58`. Not quite the originally-guessed shape (a
      simple `resolve_bucket_name(kind="market-data", asset_group=...)` swap): PREDICTION resolves via a **dedicated
      FLAT yaml kind** (`market-data-tick-prediction`), not an entry in the per-asset_group `market-data` dict
      (CEFI/DEFI/TRADFI/SPORTS only) — that call raises `BucketNamingError` for `asset_group="prediction"` rather than
      silently resolving wrong. Fixed by mirroring the IDENTICAL, already-shipped fix in
      `execution-service/execution_service/utils/dependency_checker.py` (`resolve_kind_prediction` special-case, lines
      ~223-230/387-391 there): added a `_resolve_mdps_bucket(asset_group_lower)` static helper that branches on
      `asset_group_lower == "prediction"` → `resolve_bucket_name(kind="market-data-tick-prediction")` (no
      `asset_group=`), else → `resolve_bucket_name(kind="market-data", asset_group=...)`. Used by both
      `_resolve_gcs_path` and `_mdps_manifest_capture_status`. 2 new regression tests added to
      `tests/delta_one/unit/test_dependency_checker_manifest_aware.py` (asserts the exact `resolve_bucket_name` call
      args for both the PREDICTION and non-PREDICTION branches) — 7/7 tests passing.
- [x] [SCRIPT] P3. ✅ Resolved as a side effect of the P2 fix above, not separately: the `UPSTREAM_DEPS` (non-test)
      `bucket_template`'s missing `-prd-` segment is a fallback ONLY reached when `resolve_bucket_name` raises inside
      the base class's `_resolve_gcs_path`/`_check_single_dependency` — which is now exactly what used to happen for
      PREDICTION (the raise) and never happens for the other 4 asset_groups (their `resolve_bucket_name` call already
      succeeded pre-fix, which is why TRADFI's dependency-check error correctly showed the full `-prd-` path). With
      PREDICTION now resolving successfully too, the buggy hardcoded fallback template is never exercised in
      non-test-mode for ANY asset_group — confirming the original "different resolution path" hypothesis was right, just
      not the fallback template itself being wrong in a way that mattered at runtime.
- [ ] [DATA] P3. Once the bucket-naming bug is fixed, re-run
      `/data-pipeline-check-features --family delta_one     --asset-group PREDICTION` for a day within the now-resumed
      candle-production window (≥2026-07-25) to get a genuine benchmark measurement — day=2026-07-19 (used this session)
      falls inside the confirmed ~6-month production gap and would still fail on data-availability even with the naming
      bug fixed.

## 2026-07-28 (slot-2, todo-10 remaining-scope attempt) — SECOND unfixed instance of the same bug class found + fixed

Attempted the P3 re-run above now that real candle data resumed
(`gs://market-data-tick-pred-prd-.../processed_candles/ by_date/day=2026-07-25/` and `day=2026-07-26/` both confirmed
present via `gcloud storage ls`):
`--day 2026-07-26 --asset-group PREDICTION --family delta_one --legs force --require-captured --auto-day`. The VM
(`features-e2e-prediction-20260728-132926-0f2a85`) launched clean, and this time the DEPENDENCY check itself passed
(`✅ Dependencies verified for 2026-07-25/PREDICTION` — confirming the P2 fix above works) — but the run still failed
(`exit_code=1`), this time inside `_run_lookback_validation`'s **pre-flight lookback validation**, with the identical
error class: `Kind 'market-data' on cloud 'gcp' has no entry for asset_group='prediction'`. Root cause: a SECOND,
independent call site — `LookbackValidator.validate_lookback_candles` in the same `dependency_checker.py` (line ~484) —
called `resolve_bucket_name(kind="market-data", asset_group=...)` directly instead of through the `_resolve_mdps_bucket`
helper the P2 fix introduced. The helper was added and used by `_resolve_gcs_path`/`_mdps_manifest_capture_status` (the
dependency-checker call sites) but `LookbackValidator` — a sibling class in the same file, called later in the same
request — was never migrated to it. Confirmed via direct `run.log` read
(`gs://deployment-scripts-central-element-323112/vm-logs/features-e2e-prediction-20260728-132926-0f2a85/run.log`).

- [x] [SCRIPT] P2. ✅ Fixed `LookbackValidator.validate_lookback_candles` to call
      `DependencyChecker._resolve_mdps_bucket(asset_group.lower())` instead of the raw
      `resolve_bucket_name(kind="market-data", asset_group=...)` — `features-service@89e3ad3b`. Added a regression test
      (`test_validate_prediction_resolves_via_dedicated_flat_kind` in
      `tests/delta_one/unit/test_lookback_validation.py`) asserting the resolver is called with
      `kind="market-data-tick-prediction"` (no `asset_group=`) for PREDICTION, mirroring the existing
      `TestResolveMdpsBucketPredictionAbbreviation` coverage on the dependency-checker side.
- [x] [DATA] P3. ✅ Re-ran after shipping — hit a THIRD and FOURTH unfixed instance of the identical bug class (see
      below). All four now fixed; `PREDICTION:delta_one` genuinely computes.

## 2026-07-28 (slot-2, continued) — THIRD + FOURTH instances found + fixed; confirmed genuinely computing end-to-end

Re-ran `PREDICTION:delta_one` after the P2 fix shipped (`features-service@89e3ad3b`) — but the deployed VM code tarball
(`gs://deployment-scripts-central-element-323112/code/features-service-code.tar.gz`) was still pinned to the PRE-fix
commit (`1a4adb22`): tarball builds are a manual/ad-hoc step (`deployment-service/scripts/vm/ create-code-tarballs.sh`),
not CI-automated, so a landed fix doesn't reach the next VM launch until someone rebuilds it. Rebuilt + re-uploaded
(`--include features-service`, pinned to `89e3ad3b`) and re-ran: dependency check AND lookback validation both passed
this time, but the run still failed — a THIRD instance, `_get_source_bucket` in `data_loader.py` (the actual candle-read
path hit during batch compute), calling `resolve_bucket_name(kind= "market-data", asset_group=...)` directly. Grepped
the whole `delta_one` module for the same raw-call pattern and found a FOURTH, currently-live but not-yet-exercised
instance: `_assert_upstream_candles_fresh` in `live_handler.py` (the live-mode startup gate) — same bug, would have hit
PREDICTION live-mode startup identically. Fixed both (`features-service@306bef65`), updated
`test_data_loader.py`/`test_live_startup_gate.py` to patch the new resolver, added a live-mode PREDICTION regression
test. Rebuilt the tarball again (pinned to `306bef65`) and re-ran: dependency check ✅, lookback validation ✅
(`0/0 instruments` — genuinely 0 required since day-2 of a resumed production window has no prior-day candles to
require, not a bug), and the VM is now GENUINELY COMPUTING — confirmed via live `run.log` tail showing real
per-instrument feature computation across the full KALSHI PREDICTION market universe (thousands of markets), honest
per-instrument/per-date `no_captured_input_for_window` skips for markets with no candle data (expected — the
2026-07-25/26 resumption is only 2 days deep so most PREDICTION markets genuinely have no MDPS history yet), and real
writes (`Wrote 1/2 daily partitions for KALSHI:PREDICTION_MARKET:...`). Also (unrelated, informational): found the SAME
raw-call pattern in `features_service/volatility/core/{dependency_checker, data_loader}.py` — currently unreachable for
PREDICTION since `volatility`'s CLI `ASSET_GROUP_CHOICES` only lists CEFI/TRADFI, so not fixed (no live bug), but the
next asset_group added to volatility's choices should route through the same `_resolve_mdps_bucket` pattern rather than
re-copy the raw call.

**Root cause class, fully closed for delta_one**: the PREDICTION-bucket special-case (`_resolve_mdps_bucket`) was
introduced once (the P2 fix) but only wired into ONE of the four call sites that independently resolved the MDPS candle
bucket in this module — the dependency checker, lookback validator, batch data loader, and live-mode startup gate had
each grown their own copy of the same `resolve_bucket_name(kind="market-data", asset_group=...)` call over time. All
four now route through the one helper.

- [x] [SCRIPT] P2. ✅ Fixed `_get_source_bucket` (data_loader.py) + `_assert_upstream_candles_fresh` (live_handler.py) —
      `features-service@306bef65`. 4/4 known call sites in `delta_one` now route through `_resolve_mdps_bucket`.
- [ ] [DATA] P3. `PREDICTION:delta_one` benchmark measurement (todo-10's original ask) is still open — the compute run
      launched 2026-07-28 14:28 UTC (`features-e2e-prediction-20260728-142821-0f2a85`) was left running (genuinely
      progressing, not stalled) rather than babysat to completion in-session given its large universe; a future session
      should check its final report (`plans/audit/results/data_pipeline_e2e_check_features_2026_07_26.md`, overwritten
      per-run) or re-run cleanly for the actual throughput number.
- [ ] [SCRIPT] P3. Latent (currently unreachable, no live bug today) copy of the same bug pattern in
      `features_service/volatility/core/{dependency_checker,data_loader}.py` — both call
      `resolve_bucket_name(kind="market-data", asset_group=...)` directly on a variable `asset_group`, same shape as the
      4 delta_one instances fixed this session. Unreachable today because `volatility`'s CLI `ASSET_GROUP_CHOICES`
      (repo: features-service) only lists CEFI/TRADFI — PREDICTION was never a valid choice. Fix before (not after)
      PREDICTION is ever added to `volatility`'s asset_group choices: route both through
      `DependencyChecker._resolve_mdps_bucket` (same fix pattern as this issue doc), or extract a shared helper if
      `dependency_checker.py` cross-family imports are undesirable.
