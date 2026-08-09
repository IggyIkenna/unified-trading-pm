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
author: unknown
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
context_scope:
  [
    features-service/scripts/pipeline_e2e_check.py,
    features-service/features_service/delta_one/app/core/dependency_checker.py,
    /plans/archive/issues/features_e2e_check_full_matrix_widespread_real_failures_2026_07_27.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
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

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-27 — independently converged fixes from slot-4 and slot-2, merged here.** Compare
      `--require-captured`'s coverage-check query against the exact `market-data-processing-service` dependency-check
      path/date the runtime check enforces for TRADFI candles — confirm whether this is phantom-capture (manifest row
      without object) or a coverage-check granularity gap, then fix at the root. **Two real, complementary root causes
      confirmed against the live manifest+GCS (queried 2026-07-27, `market-data-tick-tradfi-prd-central-element-323112`,
      `service_name=market-data-processing-service`, every row for the failing days is `capture_status=empty_confirmed`
      — a genuinely closed TradFi market day, `record_empty_for_shard` writes a manifest row only, never a backing
      object, BY DESIGN — neither phantom-capture nor a manifest lie):** (1) **Coverage-check granularity gap**
      (`scripts/pipeline_e2e_check.py`, slot-4): `_window_is_covered` applied the same acceptable-status set (`CAPTURED`
      or `EMPTY_CONFIRMED`) to the TARGET/end day as to window-interior days, so an `EMPTY_CONFIRMED` target (e.g. a
      TradFi weekend) passed the coverage-check even though the exact GCS path the runtime dependency checker probes is
      guaranteed empty there. Fixed: `features-service@1b272676` (+ test reconciliation `4fbf4dc7`) — `_CoverageScan`
      gained `captured_days` (CAPTURED-only), and `_window_is_covered`/`_slide_to_covered_window` now require the TARGET
      day specifically to be in it, while window-interior days still tolerate the broader `canonical_days` set. (2)
      **Runtime dependency-checker manifest blindness** (`features_service/delta_one/app/core/dependency_checker.py`,
      slot-2): `DependencyChecker .check_dependencies()` does a raw GCS blob-existence probe with zero manifest
      awareness, called with `date=start_date` (the lookback WINDOW START, not the target day) from
      `batch_handler.py::_check_dependencies` — so it hard-fails on an honest-empty day even when the coverage-check
      (once fixed) correctly tolerates it as a window-interior day. Fixed: `features-service@ecd548b8` —
      `DependencyChecker` now reads the manifest for the checked date first and accepts `CAPTURED`/`EMPTY_CONFIRMED`,
      falling back to the raw GCS probe only when the manifest has no row for that date (5 regression tests,
      `tests/delta_one/unit/test_dependency_checker_manifest_aware.py`). Both fixes are needed — (1) alone doesn't touch
      the runtime checker (a window-interior empty-confirmed day could still hard-fail there); (2) alone doesn't stop
      `--require-captured` wasting a VM launch on an empty TARGET day. **A third, SEPARATE real bug was also caught and
      fixed along the way**: a different slot's concurrently-shipped `features-service@696768c7` (a genuine
      phantom-capture guard: a `capture_status=captured` manifest row with no backing object) applied its new GCS
      object-existence probe to EVERY `canonical` day, including `EMPTY_CONFIRMED` ones — since those never have a
      backing object BY DESIGN, this would have reclassified `canonical_days` to `[]` for any window containing a TradFi
      weekend/holiday, breaking `_window_is_covered` for nearly every multi-day TradFi window going forward (worse than
      the bug it fixed). **Independently caught and fixed by BOTH slot-4 (as part of `1b272676`, scoping the probe to
      the new `captured_days` field) and slot-2 (as a follow-up commit titled "exempt EMPTY_CONFIRMED-only candle days
      from the phantom-capture object probe")** — slot-4's landed first on `origin/live-defi-rollout` (verified via
      `git log`); slot-2's equivalent fix should be treated as superseded on rebase, not re-applied on top. See the
      Progress Log below for both investigations in full.
- [x] ✅ [DATA] P3. Re-run `/data-pipeline-check-features --family delta_one --asset-group TRADFI` — re-run completed
      2026-08-05, see Progress Log. Dependency checker fix CONFIRMED working. No TRADFI candle data exists yet — genuine
      force+skip proof still gated on TRADFI MDPS candle backfill. features-service@(no new code — re-run only)

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
  days. P3 (an actual VM re-run for a genuine force+skip proof) is left open below — not run this session. **Lesson for
  the next session touching `_scan_input_coverage`**: THREE different slots independently modified this exact function
  in the same session (features-service@696768c7 phantom-capture guard, this session's @c06a9bbf exemption fix, and a
  THIRD in-flight fix from another slot titled "require the TARGET day to have real captured MDPS candle data" touching
  the same file + the same `tests/unit/test_pipeline_e2e_check_candle_phantom_capture.py`, still shipping via quickmerge
  as of this entry). None of these were coordinated in advance — each slot discovered the collision only via
  `git pull --rebase` mid-quickmerge. If you land here next: (1) re-read the CURRENT `_scan_input_coverage` body rather
  than assuming any single commit message describes the whole function, (2) re-run
  `tests/unit/test_pipeline_e2e_check_candle_phantom_capture.py` in full (not just the tests you'd expect your own
  change to touch) before trusting the combined behavior, (3) if you find another edge case, re-verify against the REAL
  manifest/GCS first (this is what caught the empty_confirmed regression — a plausible-sounding fix commit message was
  NOT sufficient evidence on its own).

- 2026-07-27 (slot-4): **ROOT-CAUSED — coverage-check granularity gap, not phantom-capture.** Read the real availability
  index (`market-data-tick-tradfi-prd-central-element-323112`) for the exact days that failed (2026-07-04, 07-05, 07-18,
  07-19 — all TradFi weekends/holidays) and cross-checked against a live GCS listing at the exact
  `processed_candles/by_date/day={date}/` path the runtime `BaseDependencyChecker` probes: **every one of the 4 days has
  manifest rows with `capture_status=empty_confirmed` (never `captured`) for
  `service_name=market-data-processing-service`, and the real GCS listing returns 0 objects for all 4 days** — so the
  manifest is telling the truth (MDPS positively confirmed zero output because the market was closed); there is no
  phantom-capture / manifest-GCS divergence.

  The actual bug: `pipeline_e2e_check.py`'s `_ACCEPTABLE_INPUT_STATUSES` (`{CAPTURED, EMPTY_CONFIRMED}`) is applied
  uniformly to every day in a shard's coverage scan, including the TARGET/end day whose exact GCS path the runtime
  dependency checker enforces. Treating `EMPTY_CONFIRMED` as "acceptable" is correct for LOOKBACK-WINDOW _interior_ days
  (a rolling calculator should tolerate an individual confirmed-empty weekend elsewhere in its window — that was the
  original, deliberate intent per the code's own comment), but it is wrong for the _target_ day specifically: an
  `EMPTY_CONFIRMED` target day is, by definition, a day the writer confirmed has zero output objects — exactly what the
  runtime GCS listing then (correctly) finds. `_window_is_covered`/`_slide_to_covered_window` never distinguished the
  two, so `--auto-day` was free to land on (or the requested day could itself be) a confirmed-empty target and still
  report the window "covered".

  **Fix shipped**: `features-service@1b272676` (test reconciliation: `4fbf4dc7`) — `_CoverageScan` gained a
  `captured_days` field (CAPTURED-status-only, canonical-shaped days, tracked alongside the existing broader
  `canonical_days`). `_window_is_covered` now requires the TARGET day specifically to be in `captured_days` (real data
  proven to exist) while still allowing window-interior days to satisfy the broader `canonical_days` set
  (empty-confirmed still tolerated there). `_slide_to_covered_window` now draws its candidate list from `captured_days`
  instead of `canonical_days`, so `--auto-day` only ever lands on a day with real captured data — matching what the
  runtime dependency checker's real GCS listing will find. 4 new regression tests
  (`tests/unit/test_pipeline_e2e_check_target_day_requires_captured.py`) cover: an empty-confirmed-only target is
  rejected, a captured target is accepted, a window-interior empty-confirmed day is still tolerated, and `--auto-day`
  correctly skips empty-confirmed-only candidates to land on the nearest real-captured day.

  **Todo 2 (re-run) status**: separately checked the manifest over 2026-06-01..2026-07-27 for ANY
  `capture_status=captured` TRADFI/MDPS candle row — found none in that window. So the fix makes
  `--require-captured`/`--auto-day` correctly SKIP (rather than false-launch a VM on) every TRADFI weekend/holiday, but
  a genuine force+skip proof for `delta_one:TRADFI` is still gated on TRADFI MDPS candles actually being backfilled for
  at least one real trading day in the scanned window — todo 2 stays OPEN, now with a sharper blocking condition than
  "phantom-capture" (there is simply no real TRADFI candle data yet within the driver's scan horizon).

  **Reconciled with TWO other independent same-bug fixes that landed concurrently on `live-defi-rollout`** (this todo
  attracted 3 simultaneous dispatches — worth flagging to main/operator as a dedup gap, not just noted here):
  1. `features-service@696768c7` (slot-14) — same root symptom, different mechanism: adds `_candle_day_object_exists` (a
     real, bounded GCS existence probe) and applies it to EVERY `canonical` day (CAPTURED or EMPTY_CONFIRMED),
     reclassifying any day without a real backing object as `non_canonical`. **Rebase-merged, not simply taken as-is**:
     applying the probe to the whole `canonical` set (not just CAPTURED days) would have blanket-excluded every
     EMPTY_CONFIRMED weekend/holiday from `canonical_days` too — since `delta_one`'s own `min_lookback_days=1` means any
     Monday target's 2-day window already spans a Sunday, and any family with a larger multi-day lookback spans a
     weekend in virtually every window, this would have made `--require-captured` almost never judge a TRADFI multi-day
     window "covered" again (a worse regression than the original bug). Reconciled by scoping their object-existence
     probe to `captured_days` only (this fix's new field) — catches the same genuine phantom-capture case (a CAPTURED
     row with no real object) without touching `canonical_days`, so window-interior EMPTY_CONFIRMED tolerance survives
     intact. Their 4 tests (`tests/unit/test_pipeline_e2e_check_candle_phantom_capture.py`) updated to assert against
     `captured_days` instead of `canonical_days`/`non_canonical_days`; one new test added proving an EMPTY_CONFIRMED day
     is never even sent through the probe. All 18 tests across the 3 related test files pass.
  2. `features-service@ecd548b8` (slot-2) — a DIFFERENT, complementary layer: makes the RUNTIME
     `features_service.delta_one.app.core.dependency_checker.DependencyChecker` itself manifest-aware (consults the
     availability manifest first, accepts CAPTURED/EMPTY_CONFIRMED, falls back to the raw GCS probe only when the
     manifest has no row) — this affects real PRODUCTION delta_one runs, not just the `pipeline_e2e_check.py` pre-flight
     skip decision this todo's fix touches. Different file (`features_service/delta_one/app/core/dependency_checker.py`
     vs `scripts/pipeline_e2e_check.py`), no merge conflict, complementary rather than redundant: their fix stops the
     runtime hard-failing on an already-known-empty day; this todo's fix stops `--require-captured` wasting a VM launch
     on that day in the first place. Both are needed — this fix alone doesn't touch the runtime checker, so without
     slot-2's fix a non-`--require-captured` run (or a window whose target is genuinely captured but an interior day is
     empty-confirmed) could still hit the old hard-fail at the runtime layer.

  **A 4th concurrent dispatch was observed in-flight** (slot-2, commit message "fix(pipeline_e2e_check): exempt
  EMPTY_CONFIRMED-only candle days from the phantom-capture object probe", still running its own quickmerge as this
  fix's push landed first at `features-service@4fbf4dc7`) — same stated intent as this fix's reconciliation of slot-14's
  probe. Not coordinated with directly; whoever rebases second will find their change already subsumed and should drop
  the now-redundant hunks rather than re-applying an equivalent fix on top.

- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
- **2026-08-05 (slot-5, data_engineering, task features_require_captured_misses_tradfi_processed_candles_gap-002)**:
  Re-ran
  `/data-pipeline-check-features --family delta_one --asset-group TRADFI --day 2026-08-04 --legs force,skip --require-captured --auto-day`.
  Pipeline launched 2 VMs:
  1. `features-e2e-tradfi-20260805-123654-577c4e` — self-deleted during startup (no run.log produced; transient).
  2. `features-e2e-tradfi-20260805-123914-577c4e` — completed with EXIT_STATUS=1. Key findings from `run.log`:
     - **Dependency checker fix CONFIRMED WORKING**: `✅ Dependencies verified for 2026-08-03/TRADFI` — the slot-2
       manifest-aware dependency checker correctly reads the availability manifest and accepts the `empty_confirmed`
       status, exactly as designed.
     - **No TRADFI candle data exists**: pre-flight lookback validation found 1 instrument ("ticks" — appears to be a
       malformed instrument_id, possibly a data_type name picked up by the instrument scanner) with 0/370 required
       candles. Lookback validation: `max_lookback=200, timeframe=1m, buffer_days=1, expected=390, required=370`.
     - **Force leg: vm_not_success** (exit=1), honest failure — dependency check passed but no candle data to compute
       features from. Skip leg not attempted (force leg failed).
  - **Conclusion**: the require-captured gap is confirmed FIXED at both layers (coverage-check + runtime dependency
    checker), but a genuine delta_one:TRADFI force+skip proof remains gated on TRADFI MDPS candle backfill actually
    producing captured rows for at least one trading day. The "ticks" instrument_id is a separate, pre-existing bug (the
    instrument scanner found a data_type name, not a real instrument) — not blocking this shard's proof but worth
    tracking as a low-priority issue. No new code shipped — the fixes from 2026-07-27 are sufficient; the blocking
    condition is purely upstream data availability.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

## Follow-ups

- [ ] [DATA] P3. Track the pre-existing 'ticks' malformed instrument_id surfaced during the 2026-08-05 TRADFI delta_one
      re-run (the instrument scanner picked up a data_type name, not a real instrument) — the 2026-08-05 Progress Log
      says it is 'a separate, pre-existing bug... not blocking this shard's proof but worth tracking as a low-priority
      issue', a prose-only follow-up.

> **2026-08-06 archive-candidate audit**: Both todos are [x] and the two-layer fix is confirmed working
> (features-service@1b272676 + @ecd548b8, re-run CONFIRMED 2026-08-05; the honest-empty TRADFI path is now correctly
> skipped). But the genuine force+skip proof remains gated on upstream TRADFI MDPS candle backfill, and the 'ticks'
> malformed instrument_id is explicitly flagged in prose as 'worth tracking as a low-priority issue' — a follow-up that
> was never made a tracked todo.
