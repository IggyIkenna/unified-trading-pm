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

- [ ] [BACKEND] P1. Root-cause the exact mechanism via a local repro (mock/replay the manifest + instruments-store reads
      for a 2022-11 date under `--skip-dependency-check`, profile with `tracemalloc`/`memray`) or targeted in-process
      instrumentation on a fresh VM (log RSS deltas around each step of
      `_run_preflight`/`_discover_instruments_from_manifest`/`filter_delta_one_instruments`). Distinguish hypothesis 1
      (flag-triggered) from hypothesis 2 (date-triggered) by running a CONTROLLED 4th combination once this lands:
      `--skip-dependency-check` + a post-2023-05-12 date that would otherwise pass preflight normally (isolates the
      flag's effect from the date's effect). Repo: features-service. Done when: the specific code path causing unbounded
      growth is identified with a citation (file:line + before/after RSS measurement), a regression test added,
      `bash scripts/quality-gates.sh` green, fix shipped via `quickmerge.sh --agent --files`.
- [ ] [DATA] P2. Once the above lands, backfill the remaining 2022-11-01..2023-05-11 gap for `returns` (repo:
      features-service — a VM launch, not a code change).

# Progress Log

- 2026-07-31 (slot-11, data_engineering craft, resuming `defi_satellite_ao_dispatch_batch3-014`): filed after 2
  independent runaway-memory launches (killed both before OOM) and 2 healthy control launches confirmed the flag/date
  correlation described above. Left the 2 healthy VMs running to cover the safe majority of the window.
