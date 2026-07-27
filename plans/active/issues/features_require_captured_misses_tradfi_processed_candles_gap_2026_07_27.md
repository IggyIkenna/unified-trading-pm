---
doc_type: issue
title:
  "features-service pipeline_e2e_check.py's --require-captured let a TRADFI:delta_one shard through with genuinely
  missing MDPS processed_candles input, wasting a VM launch on a predictable dependency failure"
summary:
  "Running /data-pipeline-check-features for delta_one:TRADFI (day=2026-07-19, auto-day-slid to 2026-07-18..2026-07-19)
  with --require-captured --auto-day, the driver proceeded to launch a real force-leg VM. The VM's own internal
  dependency check immediately failed: market-data-processing-service output missing at
  gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-18/ (No data for
  2026-07-18/TRADFI). Both force and skip legs recorded vm_not_success (exit=1) — an honest failure signal, not a false
  pass, but --require-captured's whole purpose is to skip cells like this BEFORE spending VM time, and it didn't."
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [features-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, require-captured, mdps-dependency, honest-absence, vm-spend]
related: [data_pipeline_check_mdps_features_2026_07_20]
created: 2026-07-27
priority: P2
parent_epic: infrastructure_master
source: "todo 9b full-matrix run (/data-pipeline-check-features), slot-3, 2026-07-27"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
---

# require-captured missed a TRADFI candle gap that the VM's own dependency check caught (2026-07-27)

## What happened

`cd features-service && python3 scripts/pipeline_e2e_check.py --day 2026-07-19 --family delta_one --asset-group TRADFI --legs force,skip --require-captured --auto-day`
launched a real VM (`features-e2e-tradfi-20260727-103425-2b064d`) rather than skipping with
`no_captured_input_for_window` (which is exactly what happened for DEFI and PREDICTION in the same run). The VM's
`run.log`:

```
ERROR DEPENDENCY CHECK FAILED
ERROR Missing: market-data-processing-service
ERROR   Path: gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-18/
ERROR   Reason: No data for 2026-07-18/TRADFI
```

The skip-leg VM (`features-e2e-tradfi-20260727-103823-2b064d`) hit the identical failure a few minutes later, since the
input gap didn't change.

## Why this matters

- `--require-captured`'s entire purpose (per the skill's own docs) is "skip unprovable ones instead of launching a VM
  that can only produce a false no-output failure" — it worked correctly for DEFI/PREDICTION but not TRADFI. Two
  possible root causes, not yet distinguished:
  1. **Phantom-capture on TRADFI candles**: the availability-index/manifest row(s) `--require-captured` reads say
     `captured` for the window, but the physical `processed_candles/by_date/day=2026-07-18/` object doesn't exist — the
     same "manifest says captured, GCS object missing" failure class documented elsewhere this session for other shards.
  2. **Coverage-check granularity gap**: `--require-captured`'s window check may pass on _some_ canonically-shaped
     TRADFI candle rows existing somewhere in the lookback window without verifying the _exact_ date/path the runtime
     dependency check requires. Not investigated further here — flagging as a real finding, not chasing root cause under
     time pressure mid a 29-cell matrix run.
- Real (small) VM spend wasted on a call that was always going to fail. On a full production-scale sweep, an uncaught
  version of this class of gap multiplied across many shards is real cost, not just an annoyance.

## Todos

- [x] [SCRIPT] P2. Compare `--require-captured`'s coverage-check query against the exact
      `market-data-processing-service` dependency-check path/date the runtime check enforces for TRADFI candles —
      confirm whether this is phantom-capture (manifest row without object) or a coverage-check granularity gap, then
      fix at the root (either the manifest/GCS divergence, or require-captured's query). — ✅ features-service@c06a9bbf
      (+ features-service@ecd548b8). Confirmed via the REAL manifest (queried 2026-07-27 against
      `market-data-tick-tradfi-prd-central-element-323112`): every `market-data-processing-service` row for
      2026-07-01..2026-07-05 is `capture_status=empty_confirmed`, not `captured` — this occurrence is neither phantom
      capture nor a coverage-check granularity gap. It's a THIRD, distinct cause: 2026-07-04 (the delta_one lookback
      window's START day) is a Saturday + US holiday, so MDPS correctly writes `empty_confirmed` (market closed, zero
      candles expected, `record_empty_for_shard` — no backing object BY DESIGN). The coverage-check already treated
      `empty_confirmed` as covered (correct); the VM-side runtime `DependencyChecker.check_dependencies()` did a raw GCS
      blob-existence probe with no manifest awareness at all and hard-failed on the honest-empty day. Fixed
      `features_service/delta_one/app/core/dependency_checker.py`'s `DependencyChecker` to consult the availability
      manifest first and accept `CAPTURED`/`EMPTY_CONFIRMED`, falling back to the real GCS probe only when the manifest
      has no row for that date (features-service@ecd548b8, 5 regression tests). **Cross-cutting discovery while
      investigating**: a DIFFERENT slot's concurrently-shipped commit (features-service@696768c7, landed the same
      session) fixes a REAL separate phantom-capture bug in `_scan_input_coverage` (a `capture_status=captured` manifest
      row with no backing object) by probing every manifest-canonical candle day for a real GCS object — but it applied
      that probe to `empty_confirmed` days too. Verified empirically (2026-07-27) that this reclassified the entire real
      2026-07-01..07-05 TRADFI window's `canonical_days` to `[]` (every day in that window is `empty_confirmed`), which
      would have broken `_window_is_covered` for nearly every multi-day TradFi window going forward — a much worse
      regression than the one it fixed. Corrected in features-service@c06a9bbf: `_scan_input_coverage` now tracks
      `capture_status` per canonical day and only requires the object-existence probe for days carrying a `CAPTURED`
      row; a day canonical purely via `EMPTY_CONFIRMED` is exempt (2 new regression tests). Re-verified against the real
      manifest/GCS post-fix: `canonical_days` for 2026-07-01..07-05 is correct and
      `_window_is_covered("2026-07-05", lookback=1) == True`.
- [ ] [DATA] P3. Re-run `/data-pipeline-check-features --family delta_one --asset-group TRADFI` once MDPS TRADFI candle
      backfill covers 2026-07-18 (or once the require-captured gap is fixed) to get a genuine force+skip proof for this
      shard. Not run this session (the fix above was verified directly against the real manifest/GCS resolution logic,
      not via a full VM launch) — still the open closure step.

## Progress Log

- 2026-07-27 (slot-7): **Independently corroborated on a THIRD occurrence.** The same full-matrix run (day=2026-07-05)
  hit the identical `DEPENDENCY CHECK FAILED — Missing market-data-processing-service` for `TRADFI:delta_one` at
  `gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-07-04/` — a THIRD distinct
  day (07-04 here, 07-18 in this doc's own finding) hitting the same TRADFI-candle coverage-check/dependency-check
  disagreement. Raises confidence this is a persistent gap, not a one-off manifest glitch for a single day. Folded into
  the broader multi-root-cause writeup (this is "Root cause A" there, alongside 5 sibling findings from the same run):
  `issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md`. Not fixed by either session — this
  doc's own todo above remains the tracked fix; not duplicating a second fix-todo in the broader doc.
- 2026-07-27 (slot-2, data_engineering, dispatched against `features_e2e_check_full_matrix_widespread_real_failures-001`
  which points here per its own "reconcile there, not here" note): **Root cause resolved with direct evidence, not
  inference.** Read `DependencyChecker.check_dependencies()`
  (`unified-trading-library/unified_trading_library/core/dependency_checker.py` +
  `features-service/features_service/delta_one/app/core/dependency_checker.py`) — it does a raw GCS blob-existence probe
  with zero manifest awareness, called with `date=start_date` (the lookback WINDOW START, not the target day) from
  `batch_handler.py::_check_dependencies`. Queried the REAL availability manifest for
  `market-data-tick-tradfi-prd-central-element-323112`, `date=2026-07-04`, `service_name=market-data-processing-service`
  — all 8 rows (one per timeframe) are `capture_status=empty_confirmed`. 2026-07-04 is a Saturday + US holiday;
  `record_empty_for_shard` (`market-data-processing-service/app/core/canonical_writer_manifest.py`) confirms
  `empty_confirmed` writes a manifest row only, never a parquet object — so a genuinely-closed market day has ZERO
  backing objects by design. The coverage-check (`_scan_input_coverage`) already correctly treats `empty_confirmed` as
  covered; the bug was isolated to the VM-side runtime check, which has no such concept. Fixed
  `features-service@ecd548b8`: `DependencyChecker` now reads the manifest for the checked date first and accepts
  `CAPTURED`/`EMPTY_CONFIRMED`, deferring to the original raw-GCS-probe fallback only when the manifest has no row for
  that date (so a genuinely never-attempted day still fails exactly as before). 5 new unit tests
  (`tests/delta_one/unit/test_dependency_checker_manifest_aware.py`). **While verifying, discovered a live regression in
  a commit that landed on `origin/live-defi-rollout` in the same window** (`features-service@696768c7`, a different
  slot's fix for the SAME symptom via a different, also-real root cause — a genuine phantom-`captured` manifest row
  elsewhere with no backing object). That commit's new object-existence probe ran unconditionally over every
  manifest-canonical candle day, including `empty_confirmed` ones — which, per the finding above, NEVER have a backing
  object by design. Empirically confirmed (real manifest+GCS, 2026-07-27): before my correction,
  `_scan_input_coverage(DELTA_ONE, TRADFI, "2026-07-01", "2026-07-05")` returned `canonical_days=frozenset()` for a
  window where every single day is legitimately covered (`empty_confirmed`) — i.e. the fix-in-flight would have made
  `_window_is_covered` FAIL for nearly every multi-day TradFi window (since TradFi weekends/holidays are common and now
  permanently "phantom"), a materially worse regression than the bug it fixed. Corrected in `features-service@c06a9bbf`:
  `_scan_input_coverage` now tracks `capture_status` per canonical day and only requires the object-existence probe for
  days carrying a `CAPTURED` row; `empty_confirmed`-only days are exempt (never touch the storage client). 2 new
  regression tests added to `tests/unit/test_pipeline_e2e_check_candle_phantom_capture.py` (the existing 5 tests from
  696768c7 still pass unmodified). Re-verified end-to-end against real production data:
  `_window_is_covered("2026-07-05", 1, scan.canonical_days) == True` for the exact TRADFI:delta_one window from the
  original bug report. Both fixes are complementary, not duplicative — one closes the runtime dependency-check's
  manifest blindness, the other prevents a second check's phantom-guard from over-firing on legitimate honest-empty
  days. P3 (an actual VM re-run for a genuine force+skip proof) is left open below — not run this session.
