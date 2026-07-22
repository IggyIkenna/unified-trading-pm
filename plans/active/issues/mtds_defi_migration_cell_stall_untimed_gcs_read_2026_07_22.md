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

## Addendum 2026-07-22 (read-only investigation) — root-cause of the 157 stuck cells: NOT malformed/oversized objects

**Task**: root-cause exactly which 157 shard-cells the shipped fix abandoned
(`ORCA/SOLANA/solana_amm_pool/dex_pool_state` days `2025-12-23`..`2025-12-30` + 2 named `PANCAKESWAP_V3` cells on
`2025-12-30`), read-only, without touching the live manifest/GCS-index or the running canonical-migration VM.
**Method**: exact-prefix `gsutil`/GCS-API reads (never a whole-corpus walk — every query below is scoped to a single
already-known shard-cell directory), plus bounded-timeout subprocess reads that mirror `_process_cell`'s exact
`pd.read_parquet(fs.open(uri))` call and `_run_cells`'s exact `ThreadPoolExecutor(max_workers=8)` +
`wait(..., return_when=FIRST_COMPLETED)` fan-out pattern.

### Finding 0 — got the RAW stall log line (not just the plan's paraphrase)

Pulled
`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-per-instrument-20260722-164109/run.log`
directly (this is the fixed-code VM's own log, already-terminated content — reading it does not touch the manifest or
race the still-running successor). The exact sequence:

```
2026-07-22 15:53:04,684 INFO  preflight OK: needs_attribution ratio 0.5% <= 50% cap — applying
[... 19 PIPELINE_HEARTBEAT lines, 15:53:33Z .. 16:11:33Z, one per minute — VM/OS alive throughout, proves nothing ...]
2026-07-22 16:12:29,080 ERROR STALL: 157 cell(s) exceeded 600s with no completion — abandoning as errored:
  .../day=2025-12-23/.../venue=ORCA/chain=SOLANA/instrument_type=solana_amm_pool/data_type=dex_pool_state/,
  .../day=2025-12-24/.../venue=ORCA/.../data_type=dex_pool_state/,
  .../day=2025-12-25/.../venue=ORCA/.../data_type=dex_pool_state/,
  .../day=2025-12-26/.../venue=ORCA/.../data_type=dex_pool_state/,
  .../day=2025-12-27/.../venue=ORCA/.../data_type=dex_pool_state/,
  .../day=2025-12-28/.../venue=ORCA/.../data_type=dex_pool_state/,
  .../day=2025-12-29/.../venue=ORCA/.../data_type=dex_pool_state/,
  .../day=2025-12-30/.../venue=ORCA/.../data_type=dex_pool_state/,
  .../day=2025-12-30/.../venue=PANCAKESWAP_V3/chain=BASE/instrument_type=pool/data_type=dex_pool_state/,
  .../day=2025-12-30/.../venue=PANCAKESWAP_V3/chain=BSC/instrument_type=pool/data_type=dex_pool_state/ (+147 more)
2026-07-22 16:12:29,080 INFO  DONE cells=63 files_scanned=73 files_split=73 instruments_written=3205 rows=127019 needs_attribution=0 errors=157 wall=1164.4s
```

**Correction to the prior write-up's "2 PANCAKESWAP_V3 cells" framing**: the 10 named directories are the code's
`sorted(stuck)[:10]` (a hard cap — see `_run_cells`), so this is alphabetical, not exhaustive. `venue=PANCAKESWAP_V3`
sorts after `venue=ORCA`, and within it `chain=BASE` < `chain=BSC` < `chain=ETHEREUM` alphabetically — the 8 ORCA
directories + BASE + BSC exactly fill the 10-slot cap. A THIRD `PANCAKESWAP_V3` cell exists on `2025-12-30`
(`chain=ETHEREUM`, confirmed present below) that sorts immediately after BSC — it is very likely inside the unlisted
"+147 more" rather than genuinely absent from the stuck set, but this cannot be confirmed from the log alone (the cap
truncates before naming it). Treat "2 PANCAKESWAP_V3 cells" as possibly undercounting by (at least) 1; it does not
change any conclusion below since all 3 candidate cells read cleanly (Finding 2).

**Timing**: last successful completion was no later than `16:12:29 − 600s = 16:02:29` — so all 63 successes landed in
the first ~9.4 minutes after preflight, then ZERO cells completed for the next ~10 minutes straight before the stall
fired. (No `processed N/M cells` lines appear in this window — that log line only fires every 500 completions and this
whole chunk was 220 cells total, so its absence is an artifact of the low count, not itself evidence of anything.)

### Finding 1 — exact bundled-file inventory per stuck cell (targeted prefix `gsutil ls`, not a directory walk)

| Cell                                                                         | Bundled file(s) actually present                 | Size                                       | GCS creation time                               |
| ---------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------ | ----------------------------------------------- |
| ORCA/SOLANA dex_pool_state, day=2025-12-23                                   | `orca_SOLANA_2025-12-23.parquet`                 | 1,993,549 B                                | `2026-07-13T23:01:05Z`                          |
| ORCA/SOLANA dex_pool_state, day=2025-12-24..2025-12-30 (7 more)              | `orca_SOLANA_<day>.parquet`                      | **1,993,549 B each, byte-count-identical** | **`2026-07-13T23:01:05Z` — same second, all 8** |
| ORCA/SOLANA dex_pool_state, day=2025-12-31 (control — NOT in the stuck list) | `orca_SOLANA_2025-12-31.parquet`                 | 1,993,549 B (same)                         | `2026-07-13T23:01:05Z` (same)                   |
| PANCAKESWAP_V3/BSC pool dex_pool_state, day=2025-12-30                       | `pancakeswap_v3_BSC_20260622_064632.parquet`     | 3,202 B                                    | `2026-06-22T06:47:41Z`                          |
| PANCAKESWAP_V3/ETHEREUM pool dex_pool_state, day=2025-12-30                  | 2 files (`…20260622_064632`, `…20260629_071253`) | 32,342 B + 19,976 B                        | `2026-07-09T17:04:12Z` (both)                   |
| PANCAKESWAP_V3/BASE pool dex_pool_state, day=2025-12-30                      | 2 files (same two timestamps)                    | 97,020 B + 24,173 B                        | `2026-07-09T16:50:37Z` (both)                   |

None of these are unusually large (the biggest, ORCA, is 1.9 MiB; the PANCAKESWAP files are 3–121 KiB) or oddly
malformed by any size/shape signal. **No `_migrated_*` marker and no day-level `_needs_attribution/` object exists for
any of these cells** (checked explicitly) — `_process_cell` never reached its post-read retire step for any of them,
consistent with either a genuine stuck read OR simply never having been dispatched to a free worker thread before the
stall (see Interpretation).

**The identical 1,993,549-byte size + identical to-the-SECOND creation timestamp across all 9 ORCA days (23rd through
31st, i.e. including the NON-stuck 31st) is not a capture-time coincidence** — traced this to
`market_tick_data_service/scripts/backfill_solana_dex_state.py` and the plan's own already-tracked finding: _"Canon
dex_pool_state was re-materialised 2026-07-13 from a DIVERGENT subgraph snapshot"_
(plans/active/defi_consolidated_closeout_2026_07_18.md, open P1 "Divergence RCA" todo — same date, same venue/data_type,
cross-referenced here, not duplicated). These 9 `orca_SOLANA_<day>.parquet` bundles are that re-materialization's
OUTPUT, written in one batch on 2026-07-13 — meaning December 2025 was NOT the first time this data existed, but
**2026-07-22 (this migration run) was the first time anyone had ever attempted to READ these specific 9 objects**
(everything else in 2025 had already been split by the 3 earlier VM launches before they hung at this exact boundary).
This reframes "the year=2025 boundary" as literally the boundary between long-since-migrated content and brand-new,
never-before-read objects, not a fixed calendar coincidence.

### Finding 2 — direct reads: every sampled object is completely healthy, both alone and under the exact concurrency pattern

Single-threaded (`gcsfs.GCSFileSystem().open(uri)` → `pd.read_parquet`, one subprocess per file, `timeout 60` wrapper):

- All 8 ORCA `orca_SOLANA_<day>.parquet` (12-23..12-30): **all succeeded**, 14,093 rows × 59 cols each, 5.3–6.6s each.
- All 5 candidate PANCAKESWAP_V3 files (BSC ×1, ETHEREUM ×2, BASE ×2): **all succeeded**, 0–330 rows, 1.1–4.4s each (the
  BSC file is a 0-row/6-column placeholder-shaped record — trivially fast, nothing to hang on).

Then reproduced `_run_cells`'s EXACT pattern — one shared `gcsfs.GCSFileSystem()` instance,
`ThreadPoolExecutor(max_workers=8)`, `wait(..., return_when=FIRST_COMPLETED)` polling — submitting all 14 objects (8
ORCA + 5 PANCAKESWAP_V3 + the 12-31 control) at once: **all 14 completed cleanly, total wall 13.8s, zero stall, zero
contention.** Scripts used: `read_one.py` / `read_concurrent.py` (scratchpad, not committed — throwaway investigation
code).

**This directly rules out "malformed/oversized object" as the cause.** Whatever made these specific reads hang for 600s+
on 2026-07-22 is not reproducible against the same objects today, 9 days after they were written.

### Finding 3 — directory sibling-count (a real structural difference) is RULED OUT too, not just noted

The task brief for this investigation flagged the sheer number of files sharing each ORCA cell's directory as worth
checking. Measured via a bounded `list_blobs(fields="items(name)")` count (names only, no per-object metadata, so it
isn't slowed by `gsutil ls -l`'s per-object metadata fetch):

- ORCA/SOLANA dex_pool_state, day=2025-12-23 (STUCK): **1,000 objects total** (999 pre-existing per-instrument
  pool-address leaves + the 1 bundled file above).
- Two control days far from the boundary, already fully migrated long ago — day=2025-06-01 and day=2025-10-01 (neither
  in scope for this run, no residual bundle): **1,000 objects each** — i.e., 1,000 per-cell is this venue's ordinary
  steady-state leaf count all year, not an anomaly specific to the stuck window.
- ORCA/SOLANA dex_pool_state, day=2025-12-31 (control, NOT stuck): **1 object only** (just the bundle — no pre-existing
  per-instrument leaves for this one day, the only day in the 9-day window without them).

Despite the STUCK cells having 1,000 siblings and the NOT-stuck 12-31 control having 1, both shapes read at the SAME
speed in Finding 2 (12-23 in 6.2s vs 12-31 in 7.7s, no measurable difference) — directly refuting "a huge sibling count
makes `fs.open()`/`gcsfs` slow to resolve the target object" as a contributing mechanism, at least as reproducible
today. (12-31 being the one day in the window with zero pre-existing per-instrument leaves is itself an interesting,
unexplained asymmetry, but nothing here ties it causally to why it alone avoided the stall — see What is NOT claimed.)

### Interpretation — most likely mechanism: queue-starvation collateral, not 157 independently-poisoned objects

`_run_cells()` submits **every** cell in scope to the pool up front
(`{pool.submit(...): directory for directory, cell_infos in cells.items()}`), then polls the WHOLE pending set; the 600s
stall timer is a GLOBAL "zero completions" clock, not a per-cell one. With `max_workers=8`, once as few as ~8 concurrent
reads permanently block (a stuck socket with no read timeout — the exact defect the shipped fix targets), every OTHER
already-submitted-but-not-yet-started cell — healthy or not — sits in `pending` forever too, and gets swept into the
same "abandoned as errored" bucket the instant the global stall fires. The timing in Finding 0 (63 successes all landing
in the first ~9.4 minutes, then a clean ~10-minute dead stop) is consistent with a SMALL number of genuinely-stuck reads
progressively consuming worker slots until none were left, rather than 157 independently bad objects. The tiny,
structurally unremarkable PANCAKESWAP_V3 cells (3–121 KiB, 0–330 rows, read in 1–4s standalone) are the cleanest
demonstration of this: nothing in their content plausibly explains a 600s hang, so their presence in the 157 is much
better explained as collateral (queued, never dispatched to a worker before the global stall fired) than as an
independent defect. The true trigger is most likely a much smaller set of first-ever reads against the 2026-07-13
re-materialized ORCA objects hitting an ordinary (if rare) untimed-gcsfs stuck-connection event — exactly the failure
mode the shipped fix already targets — not a property specific to all 157 named paths.

### What is NOT claimed

- Which SPECIFIC object(s) among the 8 ORCA days were the TRUE originating stall (vs. collateral) cannot be determined
  post-hoc — the objects are provably healthy today, and the original hang is not reproducible on demand (transient, as
  the parent fix's root-cause already concluded: an untimed `gcsfs` HTTP read with no protection against a stalled
  connection).
- Whether the THIRD `PANCAKESWAP_V3/ETHEREUM` cell (Finding 1) was actually inside the stuck 157 or was one of the 63
  successes is not confirmable from the truncated log (Finding 0's correction) — immaterial to the retry recommendation
  either way since it reads cleanly.
- Why `day=2025-12-31` alone (of the 9-day re-materialization batch) has zero pre-existing per-instrument leaves
  (Finding 3) is unexplained and not investigated further here — flagged as a loose end, not a stall-relevant finding.
- No manifest query was run to corroborate row-volume trend — the direct parquet reads in Finding 2 already establish
  the actual per-day row count (14,093, identical across the whole 9-day batch, including the non-stuck 12-31), which is
  a stronger, more direct signal than an aggregated manifest count would have been, without touching the manifest.

### Recommendation (next step — NOT executed in this pass, per this investigation's read-only scope)

1. **A plain retry of these 157 cells is very likely to succeed outright now** given every sampled object (8 ORCA + 3
   PANCAKESWAP_V3 candidates, spanning the full size range present: 0 rows to 14,093 rows, 3 KiB to 1.9 MiB) reads
   cleanly today, single-threaded AND under the exact 8-way concurrent pattern the script uses. No source object was
   renamed/retired (Finding 1 — no `_migrated_*` markers anywhere), so `discover_bundled` will idempotently re-find all
   157 on the next `--apply` pass; no manifest/GCS prep is required.
2. **Sequencing**: do NOT run this against the same bucket while the current successor VM
   (`canonical-migration-defi-per-instrument-20260722-164109`, now past this boundary and into year=2026 per the active
   plan's Progress Log) is still writing — schedule a small, scoped follow-up once it finishes:
   `--start-date 2025-12-23 --end-date 2025-12-31 --apply` (covers all 8 ORCA cells + all 3 PANCAKESWAP_V3 chain cells
   in one pass; cheap — 157 cells, sub-2MB each, ~14s of read time when done serially per Finding 2's concurrent-test
   wall-clock). The shipped stall-timeout fix already bounds the worst case (a repeat transient hang self-abandons at
   600s instead of hanging the VM), so this is safe to run even if the same rare condition recurs.
3. **Cross-reference, don't duplicate**: the open P1 "Divergence RCA" todo in
   `plans/active/defi_consolidated_closeout_2026_07_18.md` (why the 2026-07-13 re-materialization dropped 32 raydium
   pools) concerns the SAME re-materialization event and overlapping venue/date window as this addendum, but is a
   DIFFERENT question (data trustworthiness/completeness of the re-materialized content, not why the migration's read
   stalled) — worth sequencing the retry above and that RCA together since both touch the identical 9-day
   `orca_SOLANA_<day>.parquet` batch, but they are not the same finding and this addendum does not resolve that RCA.

## Addendum 2026-07-22 (tick 2) — retry executed: 148/157 recovered; the remaining 9 have a DIFFERENT, now-understood cause

Ran the recommended retry (`canonical-migration-defi-pi-range-20260722-190642`,
`--start-date 2025-12-23 --end-date 2025-12-31 --apply`, using the newly-shipped `defi-pi-range` launcher mode —
`deployment-service@065cf70`). **Result:
`DONE cells=148 files_scanned=176 files_split=176 instruments_written=14413 rows=204090 needs_attribution=2342 errors=9 wall=1033.6s`**
— 148 of the previously-abandoned 157 cells now wrote real data (14,413 instruments / 204,090 rows), confirming the
"queue-starvation collateral" theory for MOST of them (the PANCAKESWAP_V3 cells and the majority of ORCA/SOLANA days
cleared cleanly on retry with no code change).

**But exactly 9 cells stalled again — the SAME 9 every time**: `ORCA/SOLANA/solana_amm_pool/dex_pool_state`, one per
day, for every one of the 9 target days (`2025-12-23` through `2025-12-31`). This is the second independent confirmation
of the identical failure set (the original run + this retry), which rules out pure randomness/collateral for THESE 9
specifically — something is different about them.

**Found it — directory-size, not a hang.** Direct `gcsfs.ls()` on the live per-day output directories (read-only, no
write) measured the actual per-day file count for this exact
`(venue=ORCA, chain=SOLANA, instrument_type=solana_amm_pool, data_type=dex_pool_state)` cell:

| Day        | Files in directory |
| ---------- | ------------------ |
| 2025-12-23 | 8,072              |
| 2025-12-24 | 6,080              |
| 2025-12-27 | 5,525              |
| 2025-12-30 | 4,688              |
| 2025-12-31 | 5,265              |

This is **4.7×–8×** the ~1,000-file "normal baseline" the prior addendum measured on control days (2025-06-01,
2025-10-01). The earlier read-only smoke test (Finding 2) only timed reading the pre-split BUNDLE (1.9 MiB, 14,093 rows)
— fast, because it's one read. It never timed the actual downstream work `_process_cell` does per cell: splitting that
bundle into one small parquet PUT **per distinct pool instrument** — thousands of individual small GCS writes, not one.
At even a modest ~75-100ms per small-file PUT (typical for `gcsfs`), 5,000-8,000 sequential writes land right at or past
the 600s stall-timeout boundary. **This reframes these 9 cells from "mysteriously hung" to "genuinely large fan-out work
that needs either more time or parallel writes within a cell"** — not a bug in the shipped stall-timeout fix (which is
doing exactly its job: bounding a slow cell's blast radius), but a capacity mismatch between a fixed global timeout and
a small number of unusually large cells.

**Not yet resolved / not re-attempted this session** — flagging rather than guessing:

- Not confirmed WHY these specific 9 December days have 5-8x the normal pool count (worth checking whether this is the
  2026-07-13 re-materialization's OWN output shape, tying back to the open "Divergence RCA" todo above, or a genuine
  seasonal/on-chain spike in distinct ORCA pool activity).
- The source bundles for these 9 cells were **left intact** (per the run's own
  `MIGRATION had 9 error(s) — affected source bundles were left intact` line) — no data was lost, they simply remain in
  pre-migration bundled form pending a future retry.
- Two viable fixes, neither implemented yet: (a) a one-off higher timeout for a scoped re-run of just these 9 cells
  (`_CELL_STALL_TIMEOUT_SECONDS` is currently a module constant, not a CLI/env override — would need a small code change
  to expose one), or (b) parallelize the per-instrument write fan-out **within** `_process_cell` itself (ties directly
  into the already-scoped "perf bundle: async fan-out" workstream in
  `plans/active/defi_consolidated_closeout_2026_07_18.md`, which flagged the identical per-instrument sequential-write
  pattern in the DeFi collect-* handlers as needing the same treatment).
- These 9 residual cells do **not** block the manifest rebuild — errored cells simply aren't in the fresh manifest yet;
  their untouched source bundles make a future retry idempotent and safe whenever the timeout/parallelism fix lands.
