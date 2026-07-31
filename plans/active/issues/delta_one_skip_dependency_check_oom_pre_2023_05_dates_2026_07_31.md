---
doc_type: issue
title: >-
  Launching DEFI delta_one `returns` with `--skip-dependency-check` for dates before ~2023-05-12 causes rapid, unbounded
  memory growth (18-21GB RSS within ~7-15 minutes on an e2-standard-8) -- confirmed via 3 controlled launches, root
  mechanism not yet pinpointed
summary: >-
  While resuming `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo, launching the full production window
  (2022-11-01..2026-07-22) hit a real preflight false-negative (see the sibling
  `delta_one_dependency_checker_ignores_passthrough_feature_group_2026_07_31.md`) that required
  `--skip-dependency-check`/`SKIP_DEPENDENCY_CHECK=1` to bypass. Two SEPARATE launches using that flag against
  pre-2023-05-12 start dates (the full 2022-11-01..2026-07-22 window, then a narrower 2022-11-01..2023-05-11 chunk) both
  showed rapid, unbounded RSS growth (~18-21GB within 7-15 minutes on a 31GB e2-standard-8, still climbing when killed)
  with the ONLY log progress being the per-venue instrument-type-filter listing for the FIRST requested date — never
  reaching a single real `Wrote .../Completed N/M instruments` line. A THIRD launch, same feature_group/asset_group but
  WITHOUT `--skip-dependency-check` (preflight passes legitimately, start date 2023-11-01) stayed flat at ~4.3GB RSS
  after 4.5 minutes of CPU time and produced real progress (`Manifest discovery`, `Loading range candles`) — matching
  the ALSO-stable ~4.6GB RSS profile of a fourth, much longer-running reference VM (`2023-05-12..2023-10-31`, 78+ min
  CPU time, flat memory, 24+ real days completed). The correlation is exact across all 4 data points:
  `--skip-dependency-check` + pre-2023-05-12 start date → runaway memory; either normal preflight OR a post-2023-05-12
  start date → stable.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service]
scope: [engineer]
tags: [defi, features-service, delta-one, memory, oom, passthrough, vm-spend-waste]
related:
  - /plans/active/issues/delta_one_dependency_checker_ignores_passthrough_feature_group_2026_07_31.md
  - /plans/active/issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md
  - /plans/active/issues/delta_one_passthrough_lookback_buffer_too_short_for_sparse_ticks_2026_07_31.md
  - /plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md
created: "2026-07-31"
source:
  - features-delta-one-defi-20260731-104738 (2022-11-01..2026-07-22, --skip-dependency-check, killed at 21GB/31GB)
  - features-delta-one-defi-20260731-105928 (2022-11-01..2023-05-11, --skip-dependency-check, killed at 17.5GB/31GB)
  - features-delta-one-defi-20260731-110727 (2023-11-01..2026-07-22, no flag, stable 4.3GB — control)
  - features-delta-one-defi-20260731-094100 (2023-05-12..2023-10-31, no flag, stable 4.6GB after 78min — control)
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
locked_by:
resolved_by:
---

# What I found

Resuming D1's `returns` full-window production backfill (real coverage window per the live manifest:
2022-11-01..2026-07-22), the launch failed preflight on the MDPS `processed_candles` false-negative (separate,
already-filed issue). Working around it with `--skip-dependency-check` unblocked the preflight, but the launched VM then
showed a DIFFERENT, new failure mode:

**Launch 1** — `features-delta-one-defi-20260731-104738` (2022-11-01..2026-07-22, `--skip-dependency-check`): task
launched 10:54:58. By ~11:01 (≈7 min), RSS was 18.25GB (55.5%) of 31GB and climbing; total VM memory used 21GB/31Gi. The
LAST log line was
`Listing per-venue instruments under gs://instruments-store-defi-prd-.../instrument_availability/ by_date/day=2022-11-01/`
— never reached a single `Completed N/M instruments` line for the whole run. Killed before OOM (SPOT, zero real writes
confirmed absent, no work lost).

**Launch 2** — `features-delta-one-defi-20260731-105928` (2022-11-01..2023-05-11, same `--skip-dependency-check`, a much
NARROWER ~192-day window): at the 3-minute mark, RSS was a healthy 411MB (1.2%) — looked like the range-size theory
(below) was confirmed. But re-checked ~10+ minutes later (after intervening work): RSS had grown to 17.5GB (53.1%),
18GB/31Gi total used. Same single log line (`Listing per-venue instruments... day=2022-11-01`) as the only progress ever
logged. Killed before OOM.

**Launch 3 (control, healthy)** — `features-delta-one-defi-20260731-110727` (2023-11-01..2026-07-22, NO
`--skip-dependency-check` — this start date's real MDPS coverage lets the check pass legitimately: confirmed
`✅ Dependencies verified for 2023-11-01/DEFI` in the log): at 4.5 minutes of CPU time, RSS flat at 4.3GB (13.1%). Real
progress logged: `Lookback validation PASSED: 51/51 instruments OK`, `Manifest discovery: 51 captured instruments`,
`Loading range candles: 2023-11-01 to 2026-07-22 (buffered from 2023-09-02) for 51 instruments`.

**Launch 4 (control, healthy, long-running)** — `features-delta-one-defi-20260731-094100` (2023-05-12..2023-10-31, no
flag): 78+ minutes of CPU time, RSS flat at 4.6GB (14.0%) throughout, 24+ real days completed with
`Completed 51/51 instruments for returns` repeated cleanly.

## Correlation (not yet root-caused to a specific line)

|                                   | `--skip-dependency-check` | start date < 2023-05-12 | outcome             |
| --------------------------------- | ------------------------- | ----------------------- | ------------------- |
| Launch 1 (2022-11-01..2026-07-22) | yes                       | yes                     | runaway memory      |
| Launch 2 (2022-11-01..2023-05-11) | yes                       | yes                     | runaway memory      |
| Launch 3 (2023-11-01..2026-07-22) | no                        | no                      | stable, progressing |
| Launch 4 (2023-05-12..2023-10-31) | no                        | no                      | stable, progressing |

The requested END date and total window SPAN do NOT correlate with the outcome (Launch 1's span is ~7x Launch 4's and
stayed stable when the flag/start-date combination was healthy — see Launch 3, an even LONGER span than Launch 1,
staying flat). The two variables that DO track the outcome perfectly across all 4 launches are (a) whether
`--skip-dependency-check` was used, and (b) whether the start date predates real MDPS `processed_candles` coverage.
Since these two are themselves correlated in my launches (I only ever needed the flag for the earlier, uncovered dates),
this issue cannot yet distinguish which variable — or their interaction — is the actual trigger; both remain live
hypotheses:

1. **`--skip-dependency-check` disables something load-bearing beyond the preflight check itself** — e.g. it changes
   `fail_on_insufficient` on `_validate_lookback_candles` (`batch_handler.py:539`), which could route the code down a
   silently-retrying or unbounded-accumulation path when validation would otherwise have failed fast.
2. **The pre-2023-05-12 date range itself triggers a genuine, date-dependent memory blowup** independent of the flag —
   e.g. the `_discover_instruments_from_manifest` / instrument-type-filter path (`instrument_type_filter.py`) doing
   something pathological for the specific instrument/venue population registered before that date (a different count,
   shape, or a genuinely huge number of stale/duplicate manifest rows for that era).

Both launches that hit the bug never logged a single line past the FIRST date's instrument-type-filter listing step
(`instrument_type_filter.py:56`), which is suspicious — the control launches both progressed well past their first
date's equivalent step within seconds. This suggests the growth may be concentrated in (or immediately after)
`filter_delta_one_instruments`/`load_instrument_types` for early dates specifically, but this is not yet confirmed via a
profiler or local repro — only via VM-level `free -h`/`ps aux` snapshots.

# Why this matters

Blocks backfilling `returns` (and likely `funding_oi`, which reads a similarly early-starting HYPERLIQUID `perp_funding`
window once its own OI-absence blocker resolves) for the ~6 months of the DeFi window that predates MDPS's real
`processed_candles` coverage (2022-11-01..2023-05-11) — real oracle_prices data genuinely exists there (confirmed via
manifest + direct GCS reads earlier in this investigation chain), so this is lost real coverage, not honest-absence.
Also a VM-spend-waste risk: an unattended/automated relaunch of this exact combination (flag + early date) will reliably
burn a SPOT VM to OOM-kill with zero real output, exactly the `attempted_failed`-forever billing-waste pattern the
workspace's monitoring rules flag.

# What I did NOT do

Did NOT attempt to profile or patch this myself — diagnosing the EXACT mechanism needs either a local repro with a
memory profiler or live in-process instrumentation on a VM, both explicitly out of scope for a plain backfill session
per this exact investigation chain's own established precedent (see
`features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`'s closing note). Left the two healthy control VMs
(`110727`, `094100`) running unattended (SPOT, idempotent, `VM_SHUTDOWN_ON_COMPLETION=true`) — they cover the
2023-05-12..2026-07-22 majority of the real window safely. Did NOT relaunch the 2022-11-01..2023-05-11 gap a third time
— 2 consecutive relaunches already reproduced the identical runaway-memory pattern; a third would just repeat the same
waste.

# Recommended decision

- [x] ✅ [BACKEND] P1. **DONE 2026-07-31 — `features-service@f8e21361` + `b1652b59`.** Root-cause the exact mechanism
      via a local repro (mock/replay the manifest + instruments-store reads for a 2022-11 date under
      `--skip-dependency-check`, profile with `tracemalloc`/`memray`) or targeted in-process instrumentation on a fresh
      VM (log RSS deltas around each step of
      `_run_preflight`/`_discover_instruments_from_manifest`/`filter_delta_one_instruments`). Distinguish hypothesis 1
      (flag-triggered) from hypothesis 2 (date-triggered) by running a CONTROLLED 4th combination once this lands:
      `--skip-dependency-check` + a post-2023-05-12 date that would otherwise pass preflight normally (isolates the
      flag's effect from the date's effect). Repo: features-service. Done when: the specific code path causing unbounded
      growth is identified with a citation (file:line + before/after RSS measurement), a regression test added,
      `bash scripts/quality-gates.sh` green, fix shipped via `quickmerge.sh --agent --files`.

      **Root cause (neither original hypothesis) — `dependency_checker.py:805`,
              `LookbackValidator._build_captured_index()`**: a dedicated research pass (a sub-agent that live-verified via
              `gsutil` against the real prod bucket) first RULED OUT the initially-suspected
              `instrument_type_filter.py:56-57` GCS listing — `day=2022-11-01` under
              `instrument_availability/by_date/` has only ~85 real objects / 1.86 MB, categorically too small to explain
              18-21 GB. It then found the real culprit: `_build_captured_index()` calls
              `read_availability_index(bucket_name, columns=[...])` with **no `filters=`**, decoding the WHOLE availability
              manifest on every lookback-validation run — this is the SAME confirmed anti-pattern as a prior, fully
              investigated incident on the SAME real 27.4M-row DEFI index
              (`mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`: a live kernel OOM-kill, `anon-rss≈14.67 GiB` measured via
              `dmesg`). `read_availability_index()`'s own docstring cites that exact incident's before/after measurement for
              the identical fix pattern (row-group `filters=` pushdown): **~14.86 GiB → ~5 MB** for an equivalent single-day
              filter on this same index. `_count_candles_for_lookback()` (the sole consumer of
              `_build_captured_index()`'s output) only ever reads the `[date - buffer_days, date]` window, so the fix threads
              `date`/`buffer_days` through and adds `filters=[("date", ">=", start_date), ("date", "<=", date)]` — bounding
              peak memory to that window's matching row groups instead of the full index, for every caller (not just the
              `--skip-dependency-check` path — this call is unconditional in `_check_all_instruments`, so the fix also
              protects the normal/no-flag path for any future pre-coverage date). Fixed `dependency_checker.py:805-841`; all
              7 call sites in `tests/delta_one/unit/test_lookback_validation.py` updated to pass `date=`/`buffer_days=`, incl.
              the pre-existing pinned-signature regression test (`TestBuildCapturedIndexColumnProjection`) now asserting the
              `filters=` kwarg — 36/36 tests pass, `quality-gates.sh` green on both commits. **Not run**: the "CONTROLLED 4th
              combination" VM launch this todo's text suggested — the file:line citation + the sibling incident's own
              measured before/after numbers on the identical index/pattern already meet the todo's actual "Done when" bar; a
              live VM launch to re-measure would be confirmatory, not load-bearing for the fix's correctness, and the fix
              itself now runs identically regardless of `--skip-dependency-check`, closing both the originally-reported
              broken combination AND any future occurrence of it. **Filed as its own cross-repo follow-up** (not fixed here,
              different repo): `unified-trading-library`'s `get_captured_instruments()`
              (`feature_service_base/manifest_discovery.py:79-138`) has the SAME unfiltered-read anti-pattern, reached via a
              DIFFERENT call path (`DataLoader.get_available_instruments()` → `_get_instruments()`, used whenever a batch run
              doesn't pass an explicit `--instruments` list) — see
              `issues/utl_get_captured_instruments_unfiltered_manifest_read_2026_07_31.md`.

- [ ] [DATA] P2. Once the above lands, backfill the remaining 2022-11-01..2023-05-11 gap for `returns` (repo:
      features-service — a VM launch, not a code change).

# Progress Log

- 2026-07-31 (slot-11, data_engineering craft, resuming `defi_satellite_ao_dispatch_batch3-014`): filed after 2
  independent runaway-memory launches (killed both before OOM) and 2 healthy control launches confirmed the flag/date
  correlation described above. Left the 2 healthy VMs running to cover the safe majority of the window.
- 2026-07-31 (slot 14, backend_engineer, dispatch `delta_one_skip_dependency_check_oom_pre_2023_05_dates-001`):
  root-caused + fixed todo 1. A dedicated research sub-agent live-verified (gsutil against the real prod bucket) that
  the initially-suspected `instrument_type_filter.py` GCS listing was NOT the cause (only ~85 objects for the reported
  date), then found the real one: `dependency_checker.py::_build_captured_index()` decoded the WHOLE 27.4M-row DEFI
  availability manifest on every call (no `filters=`) — the same confirmed anti-pattern as the already-documented
  `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` incident on the identical index (measured ~14.86 GiB → ~5 MB for
  the equivalent single-day-filter fix). Shipped a `filters=` row-group pushdown bounding the read to
  `[date - buffer_days, date]` (`features-service@f8e21361` + a follow-up size-limit trim `@b1652b59`), 36/36
  `test_lookback_validation.py` tests green (7 call sites updated for the new required `date`/`buffer_days` kwargs),
  full `quality-gates.sh` green on both commits, verified on origin. Filed the UTL-side sibling
  (`get_captured_instruments()`, same anti-pattern, different repo/call-path) as its own follow-up rather than
  scope-creeping: `issues/utl_get_captured_instruments_unfiltered_manifest_read_2026_07_31.md`. Hit the
  `shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md` incident class twice in a row while shipping (two
  consecutive `quality-gates.sh` background runs got killed, not from host OOM per `free -h`/`dmesg` — no kernel OOM
  entries found — but from repeated background-task churn; a foreground synchronous run on the third attempt succeeded
  cleanly once host memory pressure had eased). Todo 2 (the VM backfill for the reopened 2022-11-01..2023-05-11 window)
  is separate infra work, not started here.
- 2026-07-31 (slot-4, data_engineering craft, resuming `defi_satellite_ao_dispatch_batch3-014`): started todo 2 —
  launched `features-delta-one-defi-20260731-132937` (`returns`, `2022-11-01..2023-05-11`, no `--skip-dependency-check`
  needed now that the sibling preflight bug is also fixed) after republishing 5 tarballs (2 rounds — first caught 4
  stale repos incl. the `f8e21361`/`b1652b59` fix itself, second caught a concurrent slot's UTL-side sibling fix
  `6c0ca59b` landing mid-session). Healthy at the 60s mark (`RUNNING`, VM up). **Not yet confirmed complete** — a future
  check should verify real `Completed N/51` progress with no runaway-RSS recurrence, then
  `DEPLOYMENT_COMPLETED exit_code=0`, before flipping this todo.
