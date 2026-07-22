---
doc_type: issue
title:
  "migrate_defi_batch_to_per_instrument hung indefinitely at the year=2025 boundary across 3 independent VM launches
  (workers=16/8/1) -- root cause: an untimed gcsfs read inside a ThreadPoolExecutor fan-out, fixed with a stall timeout
  + shard-level abandonment"
summary: >-
  The R3 canonical-migration VM (`canonical-migration-defi-per-instrument-*`) hung at the exact same shard boundary
  across three separately-launched, independently-diagnosed VMs spanning `--workers 16`, `--workers 8`, and finally
  fully serial `--workers 1` -- ruling out thread-count contention as the cause. Root-caused by reading `_run_cells()`
  in `market_tick_data_service/scripts/migrate_defi_batch_to_per_instrument.py`: `_process_cell()` calls
  `pd.read_parquet(fs.open(info.full))` (a `gcsfs` network read) with no timeout anywhere in the call chain, inside a
  `ThreadPoolExecutor` whose consumer loop (`as_completed()`) blocks indefinitely if even ONE submitted future never
  completes -- worker count is irrelevant once a single cell's read hangs, since `as_completed()` simply never yields
  that future and the loop waits forever. Fixed by replacing the `as_completed()` consumer with a bounded polling loop
  (`concurrent.futures.wait(..., timeout=poll_interval, return_when=FIRST_COMPLETED)`) that abandons and marks-errored
  whatever is still pending after `_CELL_STALL_TIMEOUT_SECONDS` (600s) of zero completions, logging the exact shard
  directory so a future occurrence is pinpointable instead of an opaque whole-VM silence. Also hardened process exit
  (`os._exit()` after `main()` returns, bypassing `concurrent.futures`'s own atexit thread-join hook) so an abandoned,
  still-blocked worker thread cannot hang the VM's process exit either.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [backfill, vm-hang, reliability, shard-level-failure-isolation, gcsfs, thread-pool, canonical-migration, defi]
related:
  - plans/active/defi_consolidated_closeout_2026_07_18.md
  - mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md
created: 2026-07-22
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.15
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
source: >-
  Discovered 2026-07-22 while recovering the glued-id manifest rebuild VM through its 3rd/4th/5th incidents in one
  session -- see plans/active/defi_consolidated_closeout_2026_07_18.md Progress Log, entries 5-6.
resolved_by: "market-tick-data-service@7dc8dcd6"
---

## What happened (VERIFIED, not inferred)

Three separate VM launches of `canonical-migration-defi-per-instrument-*` (running
`market_tick_data_service.scripts.migrate_defi_batch_to_per_instrument --start-date 2025-01-01 --end-date 2025-12-31 --apply`)
each hung with **identical** symptoms at the **same** transition point -- immediately after the script's own
`preflight OK: needs_attribution ratio ... applying` log line, before the next expected `processed N/M cells` or
`DONE cells=...` line:

| VM           | `--workers`      | Silence duration before recovery                                                                                                                                                                  | Detection                                            |
| ------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| `...-062439` | 16               | ~49 min (all-signals-dark: app log, heartbeat, AND OS-level serial console simultaneously)                                                                                                        | Triangulated 3-signal check                          |
| `...-080408` | 8                | ~20-22 min (same signature, tightened watchdog threshold)                                                                                                                                         | Same triangulation, faster                           |
| `...-093218` | 1 (fully serial) | **6+ hours** (heartbeat kept ticking the whole time -- a SEPARATE backgrounded loop independent of the main script -- masking the real stall from a naive "any new log line = progress" watchdog) | Manual grep of non-heartbeat log lines vs wall clock |

Halving workers (16→8) did not fix it. Going fully serial (1 worker) did not fix it either -- it only delayed the hang
to later in the scan (the tail end of the year, after emitting PLAN lines for essentially every day) rather than
preventing it. This ruled out thread-count/concurrency-contention as the cause and pointed at something
content-dependent (a specific shard-cell) rather than a resource-pressure or scheduling issue.

No OOM-killer, kernel-panic, or `hung_task` kernel signature was found in any VM's serial console (grepped explicitly).
No `compute.instances.preempted` operation on the hung VMs (checked via `gcloud compute operations list`) -- these were
genuine application-level hangs, not SPOT reclaims (a SEPARATE, correctly-diagnosed preemption did also occur on VM
`...-053820` earlier in the same session, and is NOT part of this finding).

## Root cause (read directly from source)

`market_tick_data_service/scripts/migrate_defi_batch_to_per_instrument.py`:

- `_process_cell()` (line ~482) reads every bundled file in a shard-cell via `pd.read_parquet(fs.open(info.full))` -- a
  `gcsfs`-backed network read with **no timeout** anywhere in the call chain (gcsfs's default HTTP client has no read
  timeout configured here).
- `_run_cells()` (line ~593, pre-fix) submitted all cells to a `ThreadPoolExecutor` and consumed results via
  `for fut in as_completed(futs): fut.result()`. `as_completed()` only yields a future once it completes -- if ANY ONE
  future never completes (a thread permanently blocked on a stalled socket read), the loop waits on it forever,
  regardless of how many other workers/threads exist or how many OTHER cells already finished.
- Progress was only logged every 500 completed cells (`if done % 500 == 0`), so a hang anywhere in the last <500 cells
  produced ZERO diagnostic output identifying which cell was stuck -- exactly the opaque-silence symptom observed on all
  three VMs.
- `_preflight_needs_attribution_ratio()` calls the SAME `_run_cells()` in dry-run mode first, so the identical hang risk
  exists in the preflight pass too (consistent with VM1's hang occurring immediately after "preflight OK" with zero PLAN
  lines ever printed -- that hang was actually IN the apply-pass's own fan-out, not the preflight's, since "preflight
  OK" is only logged once the preflight pass has already fully completed).

## Fix shipped

`_run_cells()` rewritten to poll with
`concurrent.futures.wait(pending, timeout=min(30, _CELL_STALL_TIMEOUT_SECONDS), return_when=FIRST_COMPLETED)` instead of
`as_completed()`. If `_CELL_STALL_TIMEOUT_SECONDS` (600s) elapses with zero new completions, every still-pending future
is abandoned: logged BY SHARD DIRECTORY (up to 10 named, `+N more`), counted into `stats.errored`, and the loop returns
rather than blocking forever. The executor itself is shut down non-blocking (`pool.shutdown(wait=False)`) so an
abandoned, still-running thread doesn't block the `with`-block's implicit teardown.

Separately, since Python's `concurrent.futures.thread` module registers a process-wide `atexit` hook that joins EVERY
thread any `ThreadPoolExecutor` ever spawned (regardless of `shutdown(wait=False)` on the specific pool instance), a
genuinely-abandoned worker thread could still hang the whole VM's process exit at interpreter shutdown even after
`_run_cells()` itself returns cleanly. Fixed by replacing `sys.exit(main())` with an explicit `os._exit()` after
flushing stdout/stderr -- this terminates the OS process immediately, bypassing that hook entirely (safe: `main()` has
already returned, so there is no in-flight write to interrupt).

Added a regression test (`TestCellStallAbandonment` in
`tests/unit/scripts/test_migrate_defi_batch_to_per_instrument.py`) that monkeypatches `_CELL_STALL_TIMEOUT_SECONDS` down
to 0.2s and `_process_cell` to block on one directory while completing normally on others, asserting `_run_cells()`
returns promptly with exactly the stuck cell marked `errored` and the healthy cells unaffected.

## What is NOT claimed

- The exact shard/day/instrument that was actually stuck on all three prior VMs was never identified (the fix makes this
  diagnosable on the NEXT occurrence, via the new per-directory stall log line -- it does not retroactively explain
  which specific object triggered the historical hangs).
- Whether the underlying `gcsfs`/GCS-side condition (a stalled connection, a specific malformed/huge object, or a
  transient network partition) recurs is unknown -- the fix bounds the BLAST RADIUS (one cell fails instead of the whole
  VM hanging for hours) but does not itself prevent the underlying stall from happening again.
- No claim this affects any OTHER `migrate_*` one-off script in the same `scripts/` directory -- this fix is scoped to
  `migrate_defi_batch_to_per_instrument.py` only; a grep for the same `ThreadPoolExecutor` + `as_completed()` pattern in
  sibling migration scripts was not performed as part of this fix (worth a follow-up audit if this pattern shows up
  elsewhere).

## Related

Same FAILURE CLASS (an orchestration layer that does not detect/recover from a child hang, leaving a VM silently stuck)
as `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`, but a DIFFERENT script, DIFFERENT code path, and a
DIFFERENT confirmed root cause (that one is a genuine kernel OOM-kill in the CEFI Tardis backfill path; this one is an
untimed blocking read in the DeFi per-instrument migration path) -- filed separately, not a duplicate.
