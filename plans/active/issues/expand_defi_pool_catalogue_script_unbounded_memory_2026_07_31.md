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
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: [defi, catalogue, memory-leak, manifest-read, incident, shared-host, instruments-service, cross-cutting-pattern]
related:
  [
    /plans/active/issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md,
    /plans/active/issues/delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md,
    /plans/archive/issues/utl_get_captured_instruments_unfiltered_manifest_read_2026_07_31.md,
    /plans/active/issues/defi_dex_pools_catalogue_undercoverage_vs_historical_capture_2026_07_28.md,
  ]
created: 2026-07-31
last_updated: 2026-07-31
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
resolved_by:
locked_by:
locked_since:
---

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
    `/plans/active/issues/delta_one_skip_dependency_check_oom_pre_2023_05_dates_2026_07_31.md`.
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

- [ ] [DATA] P2. Confirm which dependency's non-daemon thread/connection-pool worker was keeping the process alive past
      `main()`'s return (the script's own comment flags this as "unconfirmed which" — `os._exit()` is a correct
      defensive fix regardless, but the actual leak source is still undiagnosed and may recur in a sibling script that
      shares the same storage-client dependency). Done-when: the specific thread/resource is named with evidence (e.g.
      `py-spy dump` or `threading.enumerate()` on a live repro), and a note is added to this doc (or a fix upstream in
      the shared dependency if the thread itself is avoidable, not just work-aroundable via `os._exit()`). (repo:
      instruments-service, unified-trading-library)
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
- [ ] [DATA] P2. Cross-cutting: with FOUR incidents against the same availability manifest in ~36 hours (this doc + the
      3 related docs above), evaluate whether a shared, safe-by-default read helper (a thin wrapper around
      `read_availability_index()` that requires an explicit `columns=`/`filters=` argument, or logs a loud warning on an
      unbounded call — mirroring the write-side `ManifestWriter.__init__` safety-check todo already open in
      `mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`) would close this whole class at the source
      instead of each one-off script rediscovering it independently. Done-when: a design decision is recorded (build the
      helper, or explicitly decide the cost/benefit doesn't justify it) and, if built, this script + its 3 siblings are
      migrated to it. (repo: unified-trading-library)

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
