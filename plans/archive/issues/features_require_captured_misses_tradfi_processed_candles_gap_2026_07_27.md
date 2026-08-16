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
status: resolved
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
resolved_by: "features-service@4caac95e38 (live-VM confirmed 2026-08-16, slot-32, features-e2e-tradfi-20260816-030150-1efb38)"
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

- [x] ✅ [DATA] P3. **DONE 2026-08-16 — root-caused and fixed, not just tracked.** Track the pre-existing 'ticks'
      malformed instrument_id surfaced during the 2026-08-05 TRADFI delta_one re-run — features-service@6d2ad5dc89
      (+ tests). Root cause: NOT a data_type name mislabeled as an instrument (the 2026-08-05 guess was wrong) — every
      instrument in a chain-bundle candle shard (UAC `build_tradfi_partition_path`/`build_cefi_partition_path` v6
      layout: `.../underlying={U}/quote={Q}/margin={M}/ticks.parquet`) shares the SAME literal `ticks.parquet` leaf
      filename by design, with the real per-instrument identity in the `underlying=` path segment.
      `LookbackValidator._list_instrument_ids_for_prefix` took the filename stem as the instrument_id, collapsing every
      distinct TRADFI future/combo instrument (CL, ES, VIX, 6A, ...) down to the single string `"ticks"` — confirmed
      live via a read-only GCS listing of `market-data-tick-tradfi-prd-central-element-323112` for 2026-08-03/08-04:
      every processed-candle blob for `instrument_type=FUTURE`/`COMBO` ends in `underlying={X}/ticks.parquet`. Fixed by
      reconstructing `venue:instrument_type:underlying` from the path segments when the leaf is the generic `ticks`
      placeholder (new `_chain_bundle_instrument_id.instrument_id_from_candle_blob_name`, split out to stay under the
      900-line file cap); non-chain per-symbol shards are unaffected (filename stem still used directly). 3 new
      regression tests in `tests/delta_one/unit/test_lookback_validation.py`
      (`TestDiscoverInstrumentsChainBundleTicksLeaf`). Full `quality-gates.sh` green (18418 passed).
- [x] ✅ [DATA] P3. **RE-RUN DONE 2026-08-16 — dependency-checker layer now unblocked; force+skip proof still gated,
      root cause is now DIFFERENT and narrower.** Re-ran
      `python3 scripts/pipeline_e2e_check.py --day 2026-08-16 --family delta_one --asset-group TRADFI --legs force,skip --require-captured --auto-day`.
      `--auto-day` slid the window to 2026-08-06..2026-08-07 and the runtime dependency checker passed
      (`✅ Dependencies verified for 2026-08-06/TRADFI`) — confirming at least one real `capture_status=captured`
      TRADFI MDPS candle row now exists (a change from every row 2026-06-01..2026-08-05 being `empty_confirmed`, see
      2026-08-05 entry below). Both VM legs then failed at a DIFFERENT, later gate: features-service's own pre-flight
      `LookbackValidator` requires `max_lookback=200` (`expected=780, required=741` candles per instrument) and found
      **25/25 TRADFI delta_one instruments at 0/741** — `CME:COMBO:GC`, `CME:COMBO:SI`, `CME:COMBO:ZC`, `CME:COMBO:ZL`,
      `CME:COMBO:ZM` (full list in run.log) all show zero `processed_candles` at `timeframe=1m` across the entire
      200-day lookback, not just the empty-confirmed weekends. Report:
      `unified-trading-pm/plans/audit/results/data_pipeline_e2e_check_features_2026_08_16.md`. VM evidence:
      `features-e2e-tradfi-20260816-004617-1efb38` run.log (`vm-logs/…/run.log` in
      `deployment-scripts-central-element-323112`), `EXIT_STATUS=1` both legs. **Likely root cause, already tracked
      elsewhere — not re-investigated here (craft-scope: this task is a re-run/report, not an MDPS deep-dive)**: this
      matches the CME combo/chain-bundle candle silent-zero-output gap already under active investigation in
      `/plans/archive/2026_08/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md` (`status: open`, `assigned_vm: planning`) —
      that doc's own findings describe COMBO chain-bundle candles silently producing zero output despite confirmed real
      raw-tick input; the 200-day lookback zero-count found here for the same COMBO underlyings (GC/SI/ZC/ZL/ZM) is
      consistent with, and may be the same defect surfacing through, a different validator. No features-service code
      change needed for THIS finding — features-service@(no new code — re-run only). No new issue doc filed (would
      duplicate the existing open tracker); see the new follow-up todo below instead.

> **2026-08-06 archive-candidate audit**: Both original todos are [x] and the two-layer fix is confirmed working
> (features-service@1b272676 + @ecd548b8, re-run CONFIRMED 2026-08-05; the honest-empty TRADFI path is now correctly
> skipped). The genuine force+skip proof remaining gated on upstream TRADFI MDPS candle backfill is now tracked as the
> todo above (was prose-only here before 2026-08-16). The 'ticks' malformed instrument_id follow-up is DONE (2026-08-16,
> see above) — root cause was a chain-bundle candle-path parsing bug, not a data_type-name mislabel as the 2026-08-05
> Progress Log guessed.

## Follow-ups (new, 2026-08-16)

- [x] ✅ [DATA] P3. **DONE 2026-08-16 (slot-14, data_engineering) — root-caused + fixed a DIFFERENT bug than the
      sibling doc's COMBO gap; that gap was ALREADY resolved.** Before re-running, verified directly against live
      GCS + the availability manifest (bounded single-prefix reads, not a corpus walk): real `processed_candles`
      objects for CME COMBO `ohlcv_1m` on 2026-08-06 for every flagged underlying (`GC/SI/ZC/ZL/ZM`) already exist,
      and the manifest carries matching `capture_status=captured` rows (chain-bundle rows, `instrument_id=None`) —
      so `/plans/archive/2026_08/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`'s COMBO gap
      was NOT the blocker anymore. Re-ran the real VM anyway (`features-e2e-tradfi-20260816-010221-1efb38` /
      `-010602-1efb38`) and reproduced the
      IDENTICAL `LookbackValidator` `0/741` failure for all 5 underlyings despite the confirmed-present data —
      proving a SEPARATE, still-live bug. Root cause: `LookbackValidator._build_captured_index`
      (`features-service/features_service/delta_one/app/core/dependency_checker.py`) called `.astype(str)` on the
      manifest `instrument_id` column BEFORE checking for nulls — a chain-bundle row's real `None` became the
      literal string `"None"`, which never matched the `(venue, "")` fallback key
      `_count_candles_for_lookback` looks up, so genuinely captured bundle data silently counted as zero candles.
      Fixed: `features-service@c997516c3f` — `fillna("")` before the `str` cast. New regression test
      (`TestCountCandlesBlankInstrumentId::test_none_instrument_id_credited_for_cme_combo`) reproduces the real
      `None` shape (the existing tests only fabricated the `""` sentinel, which never exercised the bug); confirmed
      it fails pre-fix (`('CME', 'None')` in the index, not `('CME', '')`) and passes post-fix. Full
      `quality-gates.sh` green. **Re-ran the real VM a third time with the fix live**
      (`features-e2e-tradfi-20260816-015304-1efb38`, full run.log) — confirmed via the VM's own log:
      `Lookback validation PASSED: 25/25 instruments OK` (was `25/25 instruments have insufficient candles` /
      `0/741` for every underlying before the fix). **This todo's exact gate — the `LookbackValidator` 0/741-candle
      failure — is CONFIRMED CLEARED.** The VM then failed LATER, at a different, genuinely new gate (candle
      pre-load during actual feature compute, not lookback validation) — tracked as its own follow-up below rather
      than chased down here (different code path, out of this todo's scope).

- [x] ✅ [DATA] P2. **NEW 2026-08-16 — investigation DONE, root cause #1 FIXED (see slot-3 entry below); root cause #2
      remains open, tracked in the slot-33 fix-todo below.** With the `LookbackValidator` gate now clear (see todo above), the same VM run
      (`features-e2e-tradfi-20260816-015304-1efb38`) hit a DIFFERENT, later failure during actual feature compute:
      every one of 19 `delta_one` feature groups failed (`orchestrator_returned_false`), with repeated
      `No pre-loaded candles for CME:combo:/CME:COMBO:/CME:FUTURE:/CME:futures_chain:/CME:options_chain:/
      CBOE:FUTURE:VIX/CBOE:futures_chain: at 1h/24h — skipping` and summary lines `Loaded range candles for 0/7
      instruments (1m)` / `(1h)` (19 occurrences each). This is upstream of `LookbackValidator` (a different
      candle-loading mechanism inside the per-feature-group compute path, discovering only 7 instruments — not the
      25 `LookbackValidator` discovers) — not yet root-caused. Repo: features-service (delta_one compute/candle-load
      path) — investigate why the compute-time candle loader finds 0/7 for these CME instruments at 1h/24h when
      `LookbackValidator`'s own 1m-timeframe manifest read (same day, same underlyings) now succeeds. Evidence: VM
      run.log for `features-e2e-tradfi-20260816-015304-1efb38` (`vm-logs/…/run.log` in
      `deployment-scripts-central-element-323112`), `EXIT_STATUS=1`, `DEPLOYMENT_FAILED`. This is now the blocker for
      the genuine delta_one:TRADFI force+skip proof this doc's original todos were gated on.

      **ROOT-CAUSED 2026-08-16 (slot-33, data_engineering) — TWO distinct, converging mechanisms, both confirmed
      against live code + live GCS, neither fixed yet.** Independently re-ran the same check
      (`features-e2e-tradfi-20260816-022550-1efb38`, day=2026-08-16→auto-slid to 2026-08-06, before finding this
      todo's own entry above already existed — reconciling here rather than duplicating): confirmed the identical
      symptom (`Lookback validation PASSED: 25/25 instruments OK` then `Manifest discovery: 7 captured instruments`
      then every one of 19 feature groups fails with `No pre-loaded candles for CME:combo:/CME:COMBO:/CME:FUTURE:/
      CME:futures_chain:/CME:options_chain:/CBOE:futures_chain:/CBOE:FUTURE:VIX` — 0/7 instruments ever load any
      candle at any date/timeframe, including the well-formed `CBOE:FUTURE:VIX` id). Traced both the 7-vs-25
      instrument-count divergence AND the 0/7 load failure to their exact source:

      1. **Divergent instrument-discovery mechanisms** (the 7-vs-25 count gap): `LookbackValidator` discovers its 25
         instruments via a GCS blob-NAME listing + reconstruction (the already-fixed `_chain_bundle_instrument_id`
         helper). The actual compute-time loader instead calls `DataLoader.get_available_instruments()` →
         `unified_trading_library.feature_service_base.manifest_discovery.get_captured_instruments()` →
         `compose_instrument_ids()` (`unified-trading-library/unified_trading_library/feature_service_base/manifest_discovery.py:167-237`),
         which is MANIFEST-ROW-based, not blob-listing-based. Per that function's own docstring (lines 172-180), a
         manifest row with a blank/aggregate `instrument_id` (which chain-bundle candle rows genuinely have,
         confirmed live: `capture_status=captured` rows for CME COMBO carry `instrument_id=None`) is deliberately
         synthesized as `"{venue}:{instrument_type}:"` (empty final segment) rather than dropped — this is WHY the
         discovered list contains malformed entries like `CME:COMBO:`/`CME:FUTURE:`/`CME:futures_chain:` instead of
         the 25 real per-underlying ids LookbackValidator finds. The manifest simply never carries per-underlying
         granularity for TradFi chain-bundle-grain rows (by design — see the sibling doc's own "row_key instrument_id
         omission for aggregated shards" fix); only a blob-listing reconstruction (as LookbackValidator now does) can
         recover the real per-underlying identity.
      2. **`_resolve_blob_paths`/`_canonical_candle_blob_paths` blob-naming assumption is TOO NARROW** (why even the
         well-formed `CBOE:FUTURE:VIX` id — NOT blank/malformed — still loads 0 candles):
         `features-service/features_service/delta_one/app/core/data_loader.py:521,547-549` gates the
         `underlying={U}/ticks.parquet` filename convention on `_is_chain_bundle_instrument(instrument_id)`, which is
         true only for `instrument_type ∈ {combo, futures_chain, options_chain}` — for every other type (incl. plain
         `FUTURE`) it falls to `tail = f"{instrument_id}.parquet"` (e.g. `CBOE:FUTURE:VIX.parquet`). **Live GCS
         listing directly contradicts this assumption**: `market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-08-06/`
         shows `instrument_type=FUTURE/venue=CME/underlying=GOLD/ticks.parquet`,
         `.../underlying=COPPER/ticks.parquet`, etc. — i.e. **plain FUTURE-type TradFi candles ALSO use the
         `underlying=/ticks.parquet` convention**, not just COMBO/futures_chain/options_chain. So
         `_canonical_candle_blob_paths` never even tries the shape that actually exists on disk for ANY TradFi
         instrument, chain-bundle or not — every `blob_exists()` probe misses, hence 0/7 (and would be 0/25 even with
         fix #1 applied on its own).

      **Fix direction (not applied — needs its own scoped todo + tests + live re-verification, out of THIS check-only
      todo's estimate)**: (a) broaden `_canonical_candle_blob_paths` to ALWAYS also try the
      `underlying=/ticks.parquet` candidate when an underlying is extractable, regardless of `_is_chain_bundle_instrument`
      — additive to the existing candidate list (never removes the `{instrument_id}.parquet` candidate CEFI/DEFI/PREDICTION
      currently rely on), so this is low-blast-radius; (b) separately, `DataLoader.get_available_instruments()` needs a
      blob-listing-based discovery path (mirroring `LookbackValidator`'s already-fixed reconstruction, or reusing
      `_extend_with_derivative_scan`'s existing per-instrument listing fallback but invoked at DISCOVERY time, not just
      per-candidate-path time) for chain-bundle-grain manifest rows, since (a) alone can't help an already-blank
      `CME:COMBO:` id find a real underlying. Confirms this is now the genuine remaining blocker — see the new P2 todo
      below for the tracked fix.

      **INDEPENDENTLY CONVERGED 2026-08-16 (slot-3, data_engineering) — root cause #1 above FIXED, root cause #2 still
      open.** Dispatched to this same todo before finding slot-33's entry already existed (reconciling here, not
      duplicating). Root-caused via the identical mechanism slot-33's finding #1 describes —
      `compose_instrument_ids` (UTL `unified_trading_library/feature_service_base/manifest_discovery.py`) synthesizes
      a `"{venue}:{instrument_type}:"` placeholder for a chain-bundle manifest row with no per-instrument granularity,
      and `DataLoader.get_available_instruments()` passed that placeholder straight into the per-instrument candle
      loader — which can never resolve a blank symbol. **Fixed** (this is exactly slot-33's fix-direction (b) below,
      landed independently): moved `LookbackValidator`'s already-proven-correct candle-blob discovery
      (`_candidate_pipeline_mode_values`, `_list_instrument_ids_for_prefix`,
      `_discover_instruments_from_processed_candles`) out of `dependency_checker.py` into a shared
      `_chain_bundle_instrument_id` module, and added `expand_bundle_placeholder_ids()` — wired into
      `get_available_instruments()` via a new optional `timeframe` param (threaded through both
      `batch_handler.py`'s and `target_handler.py`'s instrument-resolution paths). A placeholder with no real
      underlyings discoverable is now dropped (honest skip) rather than silently passed through. 8 new regression
      tests (`tests/delta_one/unit/test_chain_bundle_instrument_id.py` + `TestGetAvailableInstruments` additions in
      `test_data_loader.py`); full `quality-gates.sh` green (18436 passed). Shipped:
      `features-service@4caac95e38`. **Root cause #2 (the `_canonical_candle_blob_paths`/`_is_chain_bundle_instrument`
      gating too narrow for plain-`FUTURE`-type TradFi ids, e.g. `CBOE:FUTURE:VIX`) was NOT touched by this fix** —
      confirmed still open per slot-33's live-GCS evidence below; a real end-to-end VM force-leg success still needs
      that second fix too (tracked in the slot-33 todo immediately below, part (a); part (b) of that todo is now DONE
      per this entry — do not re-implement it).

- [x] ✅ [DATA] P2. **DONE 2026-08-16 (slot-32, data_engineering) — live-VM confirmed, see UPDATE below.** **NEW 2026-08-16 (slot-33).** Fix the two root causes identified above (both in the "NEW 2026-08-16"
      todo's follow-through, not duplicated here): (a) `features-service/features_service/delta_one/app/core/data_loader.py`
      — broaden `_canonical_candle_blob_paths`'s `underlying=/ticks.parquet` candidate to apply regardless of
      `_is_chain_bundle_instrument`, additive to the existing `{instrument_id}.parquet` candidate; (b) give
      `DataLoader.get_available_instruments()` (or the shared UTL `get_captured_instruments`/`compose_instrument_ids`)
      a blob-listing-based fallback to recover real per-underlying instrument identity for chain-bundle manifest rows
      whose `instrument_id` is blank/aggregate, mirroring `LookbackValidator`'s already-shipped
      `_chain_bundle_instrument_id.instrument_id_from_candle_blob_name` reconstruction. **Done when**: a live
      `features-e2e-tradfi-*` VM force-leg run for `delta_one:TRADFI` loads real candle data for the CME
      COMBO/FUTURE/futures_chain/options_chain underlyings and at least one feature group succeeds (not
      `orchestrator_returned_false` for all 19). Repo: features-service (+ unified-trading-library if the discovery
      fallback lands there). Evidence for the root cause: `features-e2e-tradfi-20260816-022550-1efb38` run.log
      (`vm-logs/…/run.log` in `deployment-scripts-central-element-323112`); live GCS listing of
      `market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2026-08-06/` (60-object
      sample, `instrument_type=FUTURE` confirmed under `underlying=/ticks.parquet`).

      **UPDATE 2026-08-16 (slot-3): part (b) is DONE** — see the slot-3 entry immediately above this todo;
      `features-service@4caac95e38` already ships the blob-listing-based fallback this part asks for. **Part (a)
      remains genuinely open** — `_canonical_candle_blob_paths`'s narrow `_is_chain_bundle_instrument` gating was not
      touched by that fix. The "Done when" live-VM-success criterion needs part (a) too; not claiming this todo done.

      **DONE 2026-08-16 (slot-32, data_engineering) — "Done when" criterion measured live, satisfied; closing.**
      Live-verified against a fresh independent force-leg run on `features-service@4caac95e` (VM
      `features-e2e-tradfi-20260816-030150-1efb38`, `python -m features_service --feature-family delta_one --operation
      compute --mode batch --start-date 2026-08-06 --end-date 2026-08-07 --asset-group TRADFI --feature-group ALL
      --timeframe 1m --force`), read directly from the live-tee'd `run.log`
      (`vm-logs/features-e2e-tradfi-20260816-030150-1efb38/run.log` in `deployment-scripts-central-element-323112`,
      9407 lines at capture time, mid-run — not a terminal `EXIT_STATUS`, but the done-when criterion doesn't require
      one). Measured, not inferred:
      - `orchestrator_returned_false`: **0 occurrences** in the entire log (was "all 19" pre-fix).
      - Real per-underlying candle data loads and writes feature partitions for CME **COMBO** (`CME:COMBO:GC`,
        `CME:COMBO:SI`, `CME:COMBO:ZC` — e.g. `Wrote 1/2 daily partitions for CME:COMBO:ZC`) and CME **FUTURE**
        (`CME:FUTURE:AUD`, `COPPER`, `JPY`, `SILVER`, `SOYBEAN`, `SOYOIL`, `SP500`, `TNOTE10Y`, `TNOTE2Y`, `WHEAT`,
        plus `CBOE:FUTURE:VIX`) — 14 distinct real underlyings, each with `Wrote N/2 daily partitions` INFO lines
        confirming actual output, not silent 0-row skips.
      - Multiple feature groups genuinely succeed (event-horizon/time-since features, RSI, volume analysis, MACD all
        computing and writing) — far more than the "at least one" the done-when clause requires.
      - Zero `Traceback`/`ERROR` lines anywhere in the log.
      - `futures_chain`/`options_chain` instrument-type shards were **not observed** in this run (0 occurrences of
        either literal) — this day-range's TRADFI universe apparently has none in scope, so those two sub-types
        remain unconfirmed live (flagging honestly, not claiming coverage I didn't measure). COMBO + FUTURE are
        directly confirmed, which satisfies the done-when clause as written.
      - **Root cause (a) — the `_canonical_candle_blob_paths`/`_is_chain_bundle_instrument` gating slot-33 flagged as
        "too narrow" for plain-FUTURE ids — does not manifest as a live bug**: all 10 plain-FUTURE-type underlyings
        above load real candle data with zero additional fix beyond `4caac95e`'s part-(b) change. Most likely
        explanation: `_is_chain_bundle_instrument` classifies via the UAC venue-aware grain registry
        (`GRAIN_BUNDLE_BY_UNDERLYING`/`grain_for_instrument_type`), not a naive `instrument_type` string match, so it
        already correctly recognizes these CME FUTURE ids as chain-bundle-grain instruments — contradicting slot-33's
        "only for `instrument_type ∈ {combo, futures_chain, options_chain}`" characterization of the gate. Not
        re-implementing part (a); the code as shipped already clears the done-when bar.
      Conclusion: **both root causes are resolved in practice by the single already-shipped `features-service@4caac95e`
      commit** (part (b)'s blob-listing fallback) — part (a) was not a real live blocker. Closing this todo; this was
      the last open todo in this doc.
