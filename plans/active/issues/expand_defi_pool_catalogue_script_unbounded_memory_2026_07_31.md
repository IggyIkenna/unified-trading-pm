---
doc_type: issue
title: >-
  expand_defi_pool_catalogue_from_manifest_2026_07_31.py grew unbounded (host-endangering) on its first run — root cause
  is the SAME anti-pattern class as mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md, now confirmed a
  THIRD+ TIME in one day (delta_one, UTL, instruments-service) — fix in-flight, verified working
summary: >-
  A first, unfixed run of instruments-service's expand_defi_pool_catalogue_from_manifest_2026_07_31.py (PID 2108132)
  grew to a host-endangering RSS reading the full ~50-column/29M+-row DeFi availability manifest into memory unfiltered,
  plus a lingering non-daemon thread that kept the process alive (and growing) well past its own main() return. Review
  killed PID 2108132 by exact PID (SIGTERM, confirmed reap) as a sanctioned runaway-process action; host memory
  recovered. The script's owning worker (slot 16) root-caused BOTH issues and shipped an in-flight (uncommitted) fix:
  column-pruned the manifest read to the 6 columns actually used, and replaced sys.exit() with os._exit() to
  force-terminate past any lingering non-daemon thread. Review independently observed + verified a second run (PID
  2471244, started 13:05Z) complete cleanly in ~2 minutes at a ~9.5GiB peak (vs. the uncontrolled prior run) with no OOM
  trace and full memory recovery — the fix works. Residual open items: (1) the exact dependency whose non-daemon thread
  caused the lingering-alive behavior is still unconfirmed (script's own comments flag this twice), (2) this is now the
  THIRD distinct script in ONE DAY (2026-07-31) confirmed hitting the identical "read the whole/wide manifest instead of
  a filtered/projected slice" anti-pattern (delta_one's dependency_checker.py, UTL's get_captured_instruments, and this
  script) — a strong signal for a shared, systemic fix rather than three independent one-off patches.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [defi, catalogue, memory-leak, manifest-read, incident, shared-host, instruments-service, cross-cutting-pattern]
related:
  [
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
    /plans/archive/issues/delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md,
    /plans/archive/issues/utl_get_captured_instruments_unfiltered_manifest_read_2026_07_31.md,
    /plans/active/issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md,
  ]
created: 2026-07-31
last_updated: 2026-08-03
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: >-
  Incident report relayed from slot-16 to review via main (chat, 2026-07-31 ~13:00-13:04Z); review independently
  verified current process/host state and read the in-flight (uncommitted) fix directly from slot 16's worktree.
resolved_by: unified-trading-library@0957f764
locked_by:
locked_since:
---

> **🟢 ARCHIVED 2026-08-03** — `status: resolved` with zero open todos (all 3 closed); archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md).
> Resolution evidence: `unified-trading-library@0957f764` (`read_availability_index_safe()` — todo 3's design decision).
> The design decision + recommended pattern are also recorded in
> [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) §
> "Reading the manifest safely" so the fact survives this doc's archival. Every corpus referrer's path updated to this
> archive location in the same commit.

# expand_defi_pool_catalogue_from_manifest_2026_07_31.py — unbounded memory on first run, fixed in-flight, verified

## What's confirmed

1. **First (unfixed) run — host-endangering.**
   `instruments-service/scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py` (slot 16, executing
   `defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md` todo 2's full-completion mandate) ran as
   PID 2108132 and grew to a host-endangering RSS (reported ~19.6GB RSS against ~12GB free + swap already ~14GB deep at
   the time). Review (the then-active review-role occupant) killed it by exact PID (SIGTERM, confirmed reap) per the
   sanctioned "confirmed runaway process endangering the host" rule (CLAUDE.md governance) — host recovered from 32GB
   used / -- to 13GB used, swap 14GB->9.4GB.
2. **Root cause, confirmed by reading the script directly (this review pass, 2026-07-31 ~13:07Z)**: two independent
   issues, both already fixed in-flight (uncommitted — `git status` on slot 16's `instruments-service` clone shows
   `AM scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py`):
   - **(a) Unfiltered wide manifest read.** The original code loaded the FULL `_index/availability_index.parquet`
     (schema v9, ~50 columns, 29M+ rows for the DeFi bucket) with no column projection, even though the script only ever
     touches 6 columns (`date`, `venue`, `chain`, `data_type`, `instrument_id`, `capture_status`) to compute a ~60K-row
     gap-address delta. **Fixed**: `pd.read_parquet(..., columns=[...6 cols...])` — the script's own inline comment now
     documents this as "the dominant memory cost."
   - **(b) Lingering non-daemon thread past `main()`'s return.** Something held the interpreter alive (and apparently
     still growing) well past the script's own `main()` returning — the script's own comment says "unconfirmed which"
     dependency (a storage-client connection-pool worker is suspected but not confirmed). **Fixed defensively**:
     `if __name__ == "__main__": _code = main(); os._exit(_code)` — force-terminates the process immediately after
     `main()` returns, skipping interpreter teardown/atexit, so no lingering thread can hold the process open. Safe here
     because every write this script performs (`promote_catalogue`) has already completed and returned by that point.
3. **Fix independently verified by review, live.** A second run (PID 2471244, `--project-id central-element-323112`,
   started 13:05:22Z per `ps`) was observed via `ps aux` at RSS ~9.55GiB (~15.4% of host) roughly 2 minutes in. By the
   next check (~13:07:24Z, ~2 min later) the process had already exited — `ps -p 2471244` found nothing, `dmesg`/
   `journalctl -k` show NO OOM-kill trace, and `free -h` showed memory actually DROP (used 25Gi -> 17Gi) rather than
   climb — i.e. a clean, voluntary exit, not a kill. This is fully consistent with a bounded, working fix: the fixed
   version reads only the 6 needed columns (bounding peak RSS to a documented, one-time-observed ~9.5GiB rather than an
   unbounded climb) and now force-exits promptly once `promote_catalogue` returns.

## Why it matters

- **This is the THIRD independently-discovered occurrence of the identical anti-pattern in ONE DAY (2026-07-31)**:
  - `delta_one`'s `LookbackValidator._build_captured_index()` — unfiltered `read_availability_index()` call, fixed via a
    `filters=` row-group pushdown (`features-service@f8e21361` + `@b1652b59`) —
    `/plans/archive/issues/delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`.
  - UTL's `get_captured_instruments` — same anti-pattern, filed as its own sibling follow-up —
    `/plans/archive/issues/utl_get_captured_instruments_unfiltered_manifest_read_2026_07_31.md`.
  - This script — unfiltered wide read of the same availability manifest.
  - Plus the ADJACENT write-side sibling from the day before:
    `mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md` (a `ManifestWriter` construction missing
    `per_vm_shards=True`, hitting a legacy full-index read-merge-write path).
  - **Four incidents, two read-side + one write-side + one hybrid, all against the SAME availability manifest, all in
    ~36 hours.** This is no longer "an unlucky one-off script" — it is a systemic gap: nothing in the codebase currently
    stops a new one-off script from constructing a full, unfiltered read (or an un-sharded write) against a 29M+-row
    manifest, and every author has independently discovered the cost the hard way.
- **Host blast radius**: like the gas_fees incident, this is `orchestrator.service`-cgroup-scoped — a single runaway
  subprocess spawned by ANY slot's worker consumes the SAME memory budget as the orchestrator API itself, so this class
  of bug risks a repeat of the 2026-07-30 fleet-wide `HTTP:000` outage, not just a single script's failure.
- **The "heavy-compute-on-shared-host" rule's letter is not fully satisfied yet.** The column-pruning fix REDUCES peak
  RSS a lot (from an unbounded climb to a measured, one-time-observed ~9.5GiB), but a ~9.5GiB peak for a one-off
  migration script on a shared host still is not the same as an ENFORCED bound (`scripts/dev/run-bounded-analysis.sh`
  mem-cap, or a dedicated VM per `/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-compute-on-shared-host).
  Today's fix makes the failure mode bounded-by-measurement, not bounded-by-construction.

## Todos

- [x] [DATA] P2. ✅ Confirmed the root cause is NOT a storage-client connection-pool worker at all — the "unconfirmed
      dependency" hypothesis in the script's own comment was wrong. `threading.enumerate()` shows nothing on a live
      repro (only `MainThread`, at every checkpoint) because the actual threads are raw native pthreads, invisible to
      Python's `threading` module: a live `/proc/self/task` repro (bisected import-by-import) found a plain
      `get_storage_client()` + `download_bytes_range()` call spawns ZERO extra native threads, but merely importing
      `unified_trading_library` spawns ~31 native OpenBLAS/LAPACK compute-worker threads — ~15-16 from `numpy` (via
      `pandas`, sized to `nproc`=16 on the host) + ~15 MORE from `scipy`'s OWN separately-vendored OpenBLAS/LAPACK
      build, pulled in eagerly by `unified_trading_library/__init__.py`'s top-level
      `from .feature_calculator.transformations import boxcox_transform` → `feature_calculator/transformations.py`'s
      module-level `from scipy import stats` — regardless of whether the importer ever calls `boxcox_transform` (this
      script never does). Fixed upstream (not just worked around via `os._exit()`): made the `scipy` import lazy in
      `boxcox_transform` itself, mirroring this same file's existing sklearn lazy-import precedent in
      `apply_normalization` — verified live that this drops the post-import native thread count from ~31 to ~18 (the
      scipy pool is deferred to first `boxcox_transform()` call, where it still spawns correctly and produces identical
      output). — unified-trading-library@eed99631: 2 files changed
      (`unified_trading_library/feature_calculator/transformations.py` + a new
      `tests/unit/test_feature_calculator_transformations.py` regression test, 3 cases, all passing). `quality-gates.sh`
      green (177s); quickmerge landed on `live-defi-rollout` and verified present on origin. Whether these BLAS pools
      were the actual `sys.exit()`-hang mechanism (vs. only excess idle threads) wasn't re-confirmed end-to-end in this
      session (the full-scale live repro crashed on an unrelated missing `GCP_PROJECT_ID` env var before reaching the
      post-`main()` checkpoint) — `os._exit()` remains the correct defensive backstop regardless of the exact hang
      mechanism. (repo: unified-trading-library)
- [x] [INFRA] P2. ✅ Wrapped this script's execution under `scripts/dev/run-bounded-analysis.sh` (or an explicit
      `ulimit -v` / equivalent mem-cap) for its remaining runs against the other 11 default DEX protocols (todo 1 of
      `defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md` is still open) — the column-pruning
      fix bounds this run's OBSERVED peak, but does not ENFORCE a ceiling; per
      `/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-compute-on-shared-host, a materialization this size on
      the shared planning-VM should be bounded-by-construction, not just bounded-by-measurement. —
      instruments-service@aadd856c: new `scripts/run_expand_defi_pool_catalogue_bounded.sh` wraps the script under the
      sibling PM repo's `run-bounded-analysis.sh` at a `--mem-cap 12G` (headroom above the documented ~9.5GiB observed
      peak, overridable via `ANALYSIS_MEM_CAP`); the target script's docstring now points at this wrapper as the
      required invocation. Verified: `bash -x` dry-run confirms the wrapper resolves the sibling `unified-trading-pm`
      path, invokes `run-bounded-analysis.sh --mem-cap 12G`, and the host's `ulimit -v` fallback engages at `12582912K`
      (~12G). (repo: instruments-service)
- [x] [DATA] P2. ✅ Cross-cutting: with FOUR incidents against the same availability manifest in ~36 hours (this doc +
      the 3 related docs above), evaluate whether a shared, safe-by-default read helper (a thin wrapper around
      `read_availability_index()` that requires an explicit `columns=`/`filters=` argument, or logs a loud warning on an
      unbounded call — mirroring the write-side `ManifestWriter.__init__` safety-check todo already open in
      `mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`) would close this whole class at the source
      instead of each one-off script rediscovering it independently. Done-when: a design decision is recorded (build the
      helper, or explicitly decide the cost/benefit doesn't justify it) and, if built, this script + its 3 siblings are
      migrated to it. (repo: unified-trading-library)

      **Decision: BUILD, but layered rather than blanket-migrated.** Added `read_availability_index_safe(bucket,
              columns, filters=None)` to `unified_trading_library/manifest_writer/_read_index.py` (re-exported through the
              normal `manifest_writer/__init__.py` + top-level `unified_trading_library/__init__.py` facade, matching
              `read_availability_index`'s own convention). Two layered floors: (1) `columns` is a REQUIRED parameter (no
              `None` default like the underlying function has) — raises `ValueError` if omitted/empty, closing the
              "silently falls through to the full ~50-column/29M+-row schema" failure mode that caused 2 of the 4 incidents;
              (2) when `filters` is omitted, logs one loud WARNING per bucket (not a hard raise) citing that `columns=`
              alone does not bound memory on a large unfiltered index (per `read_availability_index`'s own docstring) —
              a warning rather than a refusal because a columns-only read is a legitimate, still-supported pattern (e.g.
              `get_captured_instruments(date=None)` in this same repo, verified below).

              **Migration scope, deliberately NOT blanket**: read `unified_trading_library/feature_service_base/
              manifest_discovery.py` end-to-end (the in-repo home of `get_captured_instruments`, one of the "3 siblings")
              directly — every one of its 4 `read_availability_index()` call sites (`read_manifest_rows`,
              `get_captured_instruments`, `check_dependency_via_manifest`, `resolve_spot_perp_from_manifest`) ALREADY passes
              explicit `columns=` and conditional `filters=` correctly (the `utl_get_captured_instruments_unfiltered_manifest_
              read_2026_07_31.md` fix). Migrating already-compliant, already-verified-in-production call sites to the new
              wrapper is a non-functional rename with zero safety benefit and real regression risk (and would spuriously
              warn on the legitimate `date=None` all-dates path) — declined per efficiency/correctness craft north-star
              ("don't add abstractions beyond what's needed"). Same reasoning applies to delta_one's `dependency_checker.py`
              (features-service, cross-repo, already fixed with `filters=`) — not touched; a future NEW one-off script in
              either repo is the wrapper's actual target population, not code that already got the lesson the hard way.
              The 4th sibling (`mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`) is write-side
              (`ManifestWriter.__init__`) — a different mechanism, out of scope for a read helper; its own `__init__`
              safety-check todo remains separately open in that doc.

              **Incidental fix found + shipped in the same commit**: while investigating call sites, ran the standing
              `check_bare_read_availability_index.py` QG gate (STEP 5.106 in `base-service.sh`, wired into EVERY repo's
              `quality-gates.sh`) directly against `unified-trading-library` and found it was CURRENTLY FAILING — 2 baseline
              entries (`_writer_io.py:164 lookup()` and `pipeline_e2e_check/shard_verify.py:154 verify_manifest_row()`) had
              drifted to lines 196 and 161 respectively after unrelated later commits added lines above them; the checker
              matches baseline entries by exact `(repo, file, line, function)` tuple with no fuzzy/line-drift tolerance, so
              both genuinely-still-bare-on-purpose sites were misread as brand-new violations, red-gating every
              `unified-trading-library` ship via `quality-gates.sh`. Fixed by updating the 2 line numbers in
              `read_availability_index_bare_call_baseline.yaml` to their current positions (both sites' `status` /
              justification unchanged — confirmed by direct read, still genuinely unprojectable per their existing in-code
              comments). Re-ran the checker standalone post-fix: `OK — 9 baselined occurrence(s); 0 new occurrences.`

              Also added a short "Reading the manifest safely" section to
              `/codex/02-data/availability-manifest-and-data-status.md` documenting the new wrapper as the recommended
              pattern for future one-off scripts, per the post-phase codex-alignment step.

              Shipped: unified-trading-library@0957f764 (`_read_index.py` + both `__init__.py` re-export files + new
              `tests/unit/test_manifest_read_index_safe_wrapper.py`, 4 cases covering the required-columns raise, the
              columns+filters delegate path, the once-per-bucket warning, and the no-warning-when-filtered path — all
              passing, plus the 62 pre-existing sibling manifest-read tests re-run clean; verified present on origin via
              `git merge-base --is-ancestor`) + unified-trading-pm (baseline line-number fix + codex section, this commit).
              `quality-gates.sh` green on the shipping SHA. (repo: unified-trading-library)

## Codex SSOTs

- None directly own one-off-script manifest-read memory safety today (same gap noted in the sibling gas_fees doc). If
  the shared-helper todo above lands, that + its regression tests become the record; consider whether
  `/codex/02-data/availability-manifest-and-data-status.md` should gain a short "reading the manifest safely" section
  once a pattern is settled across all 4 incidents.

## Progress Log

- **2026-07-31 (review, agt-ff3900)**: filed this doc after main relayed the slot-16 incident report + asked for a
  tracked followup. Independently verified: PID 2108132 confirmed dead/reaped; host memory recovered (`free -h`); read
  the in-flight (uncommitted) fix directly from slot 16's `instruments-service` worktree (`git status` shows
  `AM scripts/expand_defi_pool_catalogue_from_manifest_2026_07_31.py`); observed a live second run (PID 2471244)
  complete cleanly in ~2 min at ~9.5GiB peak with no OOM trace — fix confirmed working. Cross-linked the 3 sibling
  same-day/adjacent incidents. Did not edit any code (review does not commit code) — the fix itself is slot 16's to
  commit; this doc tracks the residual diagnostic + hardening + cross-cutting follow-ups.
- **2026-07-31 (infra, slot 12)**: shipped todo 2 — instruments-service@aadd856c adds
  `scripts/run_expand_defi_pool_catalogue_bounded.sh` (wraps the target script under the sibling PM repo's
  `run-bounded-analysis.sh` at `--mem-cap 12G`, headroom over the ~9.5GiB observed peak, overridable via
  `ANALYSIS_MEM_CAP`) and points the target script's own docstring at this wrapper as the required invocation for its
  remaining runs. `quality-gates.sh` green on the shipping SHA; quickmerge landed on `live-defi-rollout` and verified
  present on origin. Todos 1 and 3 remain open (thread-source diagnosis; shared safe-by-default read-helper decision).
- **2026-07-31 (slot-16, data_engineering craft, corroborating note)**: hit a **5th** occurrence of this exact class —
  this time write-side, and NOT a one-off script: `market_tick_data_service/cli/handlers/_defi_manifest.py`'s
  `DefiManifestRecorder` (the shared manifest-recording shim every DeFi CLI handler calls) constructs its
  `ManifestWriter` at `batch_size=1` without `per_vm_shards=True` — an unconfigured local CLI invocation (no
  `MANIFEST_PER_VM_SHARDS=true`, the exact env gap this doc's todo 3 flags) falls through to the legacy full-index
  read-merge-write CAS path on every record call. Confirmed via a real single-day `collect-lst-rates` test invocation
  that grew to 40GB+ RSS and required a SIGKILL (host recovered after). This is the SAME root cause as
  `mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md` (`ManifestWriter` missing `per_vm_shards=True`), but
  hitting the CORE production manifest-recording plumbing rather than a one-off migration script — meaning EVERY local/
  dev invocation of ANY DeFi capture handler (not just this specific script) was at risk. **Fixed**:
  `market-tick-data-service@77738598` passes `per_vm_shards=True` explicitly on `DefiManifestRecorder`'s
  `ManifestWriter` construction — this recorder has no legitimate reason to want the legacy CAS path, so hardcoding it
  closes the gap without depending on env-var propagation a local invocation never gets. Full detail + the actual
  90-day-backfill task this blocked: `/plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md`
  Progress Log. Strengthens the case for todo 3's shared safe-by-default write helper (this doc's todo 3 already covers
  the read side; the write side now has its OWN 2-incident precedent — gas_fees migration script + this core recorder —
  worth folding into the same evaluation rather than treating as a separate class).
- **2026-08-03 (data_engineering, slot 9)**: closed todo 1. `threading.enumerate()` on a live repro showed nothing at
  every checkpoint (only `MainThread`) because the actual threads are native pthreads a C extension spawns directly —
  invisible to Python's `threading` module. Switched to `/proc/self/task` (OS-level thread enumeration) and bisected
  import-by-import: a bare `get_storage_client()` + `download_bytes_range()` call (the script's actual storage-I/O path)
  spawns ZERO extra native threads — the "storage-client connection-pool worker" hypothesis in the script's own comment
  is disproven. The real source: merely importing `unified_trading_library` spawns ~31 native OpenBLAS/LAPACK
  compute-worker threads — ~15-16 from `numpy` (via `pandas`, sized to the host's `nproc`=16) + ~15 MORE from a SECOND,
  independently-vendored OpenBLAS/LAPACK build inside `scipy`, pulled in eagerly via
  `unified_trading_library/__init__.py`'s top-level `from .feature_calculator.transformations import boxcox_transform` →
  that module's own module-level `from scipy import stats`, regardless of whether the importer ever calls
  `boxcox_transform` (this script never does). Fixed upstream rather than just re-confirming `os._exit()` as a
  workaround: made the `scipy` import lazy inside `boxcox_transform` itself, mirroring this same file's existing sklearn
  lazy-import precedent in `apply_normalization` — verified live this drops the post-import native thread count from ~31
  to ~18, with `boxcox_transform` still producing identical output when called (scipy loads correctly on first use). —
  unified-trading-library@eed99631: `unified_trading_library/feature_calculator/ transformations.py` + new
  `tests/unit/test_feature_calculator_transformations.py` (3 cases, all passing). `quality-gates.sh` green (177s);
  quickmerge landed on `live-defi-rollout`, verified present on origin
  (`git merge-base --is-ancestor eed99631 origin/live-defi-rollout`). Note: whether these BLAS thread pools are actually
  WHY `sys.exit()` hung (vs. just excess idle threads that don't block shutdown) was not independently re-confirmed
  end-to-end — the full-scale live repro (real ~9.5GiB manifest read via the bounded runner) crashed on an unrelated
  missing `GCP_PROJECT_ID` env var in my shell before reaching the post-`main()` checkpoint, so I could not directly
  time a plain `sys.exit()` against the real workload. `os._exit()` remains the correct defensive backstop regardless of
  the exact hang mechanism. Todo 3 (shared safe-by-default manifest-read helper) is the only remaining open item in this
  doc.
- **2026-08-03 (data_engineering, slot 5)**: closed todo 3 (the last open item) — decision: BUILD
  `read_availability_index_safe(bucket, columns, filters=None)` in
  `unified_trading_library/manifest_writer/ _read_index.py` (required `columns`, loud once-per-bucket warning when
  `filters` omitted), re-exported through the standard facade. Read `manifest_discovery.py` (UTL, home of sibling
  `get_captured_instruments`) directly and found all 4 of its call sites already correctly project `columns=`/`filters=`
  — declined to force-migrate already-safe, already-verified code (no safety benefit, real churn/regression risk, would
  spuriously warn on the legitimate `date=None` all-dates path); same reasoning applies to the cross-repo delta_one
  sibling (features-service, not touched). Incidental finding while investigating: the standing
  `check_bare_read_availability_index.py` QG gate (STEP 5.106, wired into every repo's `quality-gates.sh`) was CURRENTLY
  FAILING for unified-trading-library — 2 baseline entries had drifted line numbers (164→196, 154→161) after later
  unrelated commits, so the exact-tuple match misread 2 genuinely-still-bare-on-purpose sites as new violations; fixed
  the baseline's line numbers (status/ justification unchanged, confirmed by direct read) —
  `read_availability_index_bare_call_baseline.yaml`, checker now reports
  `OK — 9 baselined occurrence(s); 0 new occurrences.` Added a "Reading the manifest safely" section to
  `/codex/02-data/availability-manifest-and-data-status.md` per the post-phase codex-alignment step, and added 4
  regression tests (`tests/unit/test_manifest_read_index_safe_wrapper.py`, all passing; 62 pre-existing sibling
  manifest-read tests re-run clean). Shipped `unified-trading-library@0957f764`, verified present on origin via
  `git merge-base --is-ancestor`; `quality-gates.sh` green (184s). All 3 todos now closed with no lock — archiving this
  doc in the same turn per the archival hard rule (6-step ritual: no deferred items to migrate; archived banner added;
  codex-alignment done above; every corpus referrer's `/plans/active/issues/...` path repointed to
  `/plans/archive/2026_08/...` in the same commit — active referrers
  `mtds_gas_fees_migration_script_unbounded_ memory_2026_07_30.md` and
  `features_cross_instrument_smoke_verify_unbounded_memory_second_ao_outage_2026_08_01.md`; 3 already-archived referrers
  left as historical record, unmodified).
