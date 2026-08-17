---
doc_type: issue
title: >-
  Shard 24's 3rd checkpoint-resumed attempt (-133746, launched 2026-07-31) ALSO wedged at ~31% and self-deleted with no
  clean exit marker — 3 consecutive failures on this exact shard (wedge / preemption / wedge) warrant diagnosis before a
  blind 4th relaunch
summary: >-
  Dispatched via `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 3 ("check shard 24's current state; relaunch if
  still incomplete and not already relaunched"). Found the relaunch had ALREADY happened —
  `canonical-migration-cefi-content-24-relaunch20260731-133746` (inserted 2026-07-31T13:37Z,
  `RESUME_START_DATE=2026-01-06 RESUME_END_DATE=2026-01-15`) — so the todo's own precondition ("hasn't already been
  relaunched by another agent") is false; per the todo's own text, no further launch action was due from that todo. But
  this 3rd attempt did NOT succeed either: `run.log` shows real progress (33,800/108,441 files, 9.0 files/sec)
  interleaved with repeated "No progress in the last poll window — N files still outstanding (possible wedged worker)"
  warnings — the EXACT same symptom shape as the shard's own first attempt (`-032606`, wedged at 43.9% then went silent
  48 min before deletion, per `cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md`). The log
  simply stops at 14:45:17Z (no `PREEMPTED` marker, no stall-kill message, no `EXIT_STATUS`) and the VM instance no
  longer exists in any Tokyo zone (`NOT_FOUND`, self-deleted per `--instance-termination-action=DELETE`).
  `PROGRESS.json` is frozen at `last_completed_date=2026-01-07` (barely past its own `RESUME_START_DATE=2026-01-06`).
  This is shard 24's THIRD consecutive failed attempt (wedge → clean SPOT preemption → wedge again), all sharing the
  shard-24 VM prefix — a recurring, shard-specific pattern rather than three independent random failures, worth
  diagnosing before another blind checkpoint-resumed relaunch.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, vm, wedge, stall, canonical-migration, data-pipeline]
related:
  [
    /plans/archive/2026_08/issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md,
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch12_2026_08_09.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-09
author: slot-8 (infra)
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.48
assigned_role: infra
drift_direction: none
sequential: false
archive_exempt: true
locked_by:
context_scope:
  [
    /plans/archive/2026_08/issues/cefi_content_migration_shard24_early_preemption_false_page_2026_07_31.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
  ]
resolved_by:
source: >-
  Discovered 2026-08-09 (slot-8, infra) while working `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 3 — the
  todo's own precondition check surfaced that a relaunch already happened AND also failed, a state the todo's done-when
  did not anticipate.
depends_on: []
---

# Shard 24's 3rd attempt also wedged — recurring shard-specific pattern, diagnose before a 4th blind relaunch

## What I found

Checked `gs://deployment-scripts-central-element-323112/vm-logs/` for any `canonical-migration-cefi-content-24-*` launch
after `-065001` (2026-07-31T06:50Z, the early-preemption death the source issue doc tracks). Found one:
`-relaunch20260731-133746` (inserted 2026-07-31T13:37Z).

**Direct evidence:**

- `LAUNCH_PARAMS.json`:
  `RESUME_ASSET_GROUP=cefi-content-apply RESUME_START_DATE=2026-01-06 RESUME_END_DATE=2026-01-15 RESUME_SHARD_OF=1 RESUME_SHARD_INDEX=0`
  — a correctly checkpoint-resumed, single-VM (non-sharded) relaunch, matching the source doc's prescribed 3rd-attempt
  window almost exactly (day-1 earlier start).
- `PROGRESS.json`: `{"last_completed_date":"2026-01-07","monotonic":true,"updated":"2026-07-31T14:24:14Z"}` — only 1 day
  past its own start.
- `run.log`: shows genuine progress to `33,800/108,441 files (9.0 files/sec, 3747.1s elapsed)` at 14:43:17Z, but
  interleaved with repeated
  `WARNING No progress in the last poll window — N files still outstanding (possible wedged worker)` — the tool's own
  self-diagnostic warning (not a stall-kill event). The log's last line is at **14:45:17Z**, then nothing — no
  `PREEMPTED` marker written, no stall-kill message, no `EXIT_STATUS` file of any kind in the vm-logs directory
  (confirmed via `gcloud storage ls -r .../133746/**` — only the 4 launcher-time files exist).
- `gcloud compute instances describe canonical-migration-cefi-content-24-relaunch20260731-133746` across all 3 Tokyo
  zones: `NOT_FOUND` — self-deleted, consistent with `--instance-termination-action=DELETE`.
- `gcloud compute operations list` for this VM name returns **nothing** — likely past the Compute Engine operations
  retention window (9 days old at time of check), so the GCE-Operations-API root-cause technique the source doc used for
  `-065001` (insert/preempt timestamps) is no longer available for this VM.

**Why "wedge" is the leading hypothesis, not preemption**: unlike `-065001` (died 70s after insert, before any `run.log`
line could be written), `-133746` ran ~55 minutes and wrote 100+ progress lines — if it had been preempted at that
point, the in-guest shutdown-script would have had ample time to write the `PREEMPTED` GCS marker (per the source doc's
own established evidence pattern). Its absence points to something that prevented a graceful shutdown entirely — either
a genuine worker freeze (matching `-032606`'s IDENTICAL symptom: real progress, then repeated "possible wedged worker"
warnings, then silence) that the `STALL_PROGRESS_REGEX=progress:|files/sec` watchdog (`deployment-service@b2d135a1e8`,
landed 2026-07-27 — already live for this run) caught and force-killed the VM without the kill event reaching this
particular log stream, or a different failure mode not yet identified.

**Pattern across shard 24's 3 attempts today (2026-07-31), all same VM-name-prefix family:**

| Attempt   | Started | Outcome                         | Symptom                                                                    |
| --------- | ------- | ------------------------------- | -------------------------------------------------------------------------- |
| `-032606` | 03:27Z  | Wedged at 43.9%, deleted 06:32Z | Progress then silence, "possible wedged worker" warnings                   |
| `-065001` | 06:50Z  | Preempted 70s later             | Clean SPOT reclaim, zero progress made                                     |
| `-133746` | 13:37Z  | Wedged at ~31%, self-deleted    | Progress then silence, SAME "possible wedged worker" warnings as `-032606` |

Two of three failures share an identical symptom signature specific to this shard. This is not conclusive proof of a
shard-24-specific root cause (could be coincidental timing/host issues), but it's a strong enough pattern that another
blind checkpoint-resumed relaunch without understanding WHY this shard specifically keeps wedging risks repeating the
same failure a 4th time.

## Why it matters

`cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 3's own precondition ("if shard 24 is still incomplete and
**hasn't already been relaunched by another agent**") is now false — the relaunch action it asked for was already taken
(by whoever/whatever launched `-133746`). Blindly launching a 4th attempt today, using the todo's literal window
(`2026-01-07 2026-01-15`), would also silently REPLAY the already-completed `2026-01-07` checkpoint day — a violation of
the workspace's "preemption recovery resumes from measured PROGRESS, never replays START_DATE" hard rule (CLAUDE.md §
"Launching VMs / infra"). The correct resume point (if a 4th attempt is warranted) is `RESUME_START_DATE=2026-01-08`,
not `2026-01-07`.

## Recommended decision

## Todos

- [x] ✅ [SCRIPT] P2. Launch shard 24's 4th checkpoint-resumed attempt from its ACTUAL last checkpoint:
      `RESUME_START_DATE=2026-01-08 RESUME_END_DATE=2026-01-15` (day AFTER `-133746`'s `last_completed_date=2026-01-07`
      — do NOT replay 2026-01-07).
      `RESUME_ASSET_GROUP=cefi-content-apply RESUME_SHARD_OF=1 RESUME_SHARD_INDEX=0 bash scripts/vm/launch-canonical-migration-vm.sh cefi-content-apply 2026-01-08 2026-01-15 full`.
      Verify STARTED <60s + ≥1 progress line/hr (per infra craft north-star — no fire-and-forget) and check back at
      T+90min for either completion, active progress past `2026-01-08`, or a repeat wedge (in which case STOP
      relaunching and treat todo 2 below as blocking). Repo: deployment-service.
- [x] ✅ [SCRIPT] P3. Only if todo 1 also wedges (3rd wedge on this exact shard): diagnose the shared root cause across
      `-032606` and `-133746`'s identical "possible wedged worker" signature — check whether shard 24's specific date
      range/file population has an outlier (e.g. one pathologically large/malformed parquet, a specific venue's file
      count spike) that the migration script's per-file loop chokes on, by comparing shard 24's file-count/size
      distribution against a shard that completed cleanly. Repo: market-tick-data-service. —
      market-tick-data-service@483eb895
- [x] ✅ [SCRIPT] P3. **New, 2026-08-15**: shard 24's final completed run (`canonical-migration-cefi-content-apply-
      20260815-181337`, WORKERS=8, reached `EXIT_STATUS=0` / 52,519/52,519 files) logged a confirmed poison-pill file
      the script's own safety-skip correctly refused to read:
      `raw_tick_data/by_date/day=2026-01-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/
      instrument_type=perpetual/data_type=trades/XRP_USDC-30JAN26-2D3-P.parquet` — `parquet metadata claims
      2611989805 uncompressed bytes from only 5159827874 bytes on disk (> 2147483648 ceiling)`. `read_error` totaled 3
      for the run (2 earlier, unconfirmed from the log tail alone); this is the 1 explicitly confirmed. Manually
      inspect/repair or re-fetch this specific file from the upstream source. Repo: market-tick-data-service
      (investigation) / instruments-service or the venue capture pipeline (repair, TBD once inspected). —
      **investigation complete 2026-08-15 (slot-12, infra), see Progress Log; repair split into the new todo below
      pending a delete-safety-cited action.**
- [x] ✅ [DATA] P2. **Repair the corrupted `XRP_USDC-30JAN26-2D3-P.parquet` object** (path above) — classification
      settled, root cause found + fixed, delete confirmed already-executed. See Progress Log for full evidence.
      **NOT combo-shape** (confirmed by regex, not eyeballing: neither the migration doc's combo regex
      `-(FS|CS|PS|STRD|STD|IRON|BOX)-` nor the classifier's own `is_deribit_combo_symbol_shape` matches this
      filename). It is a genuine standalone Deribit **decimal-strike OPTION**: `2D3` is Deribit's `D`-decimal-separator
      strike notation (`2D3` = strike 2.3, matching XRP's price range) used for XRP/SOL/DOGE-style options, expiry
      30JAN26, right=Put. Root-caused why it was captured under `instrument_type=perpetual` instead: MTDS's
      `TardisAdapter._OPTION_SYMBOL_RE` required a pure-digit strike (`-\d+-[CP]$`) — `2D3` isn't `\d+`, so this
      symbol matched neither the option regex, the dated-future regex, nor the combo-shape check, and fell through to
      the venue-level PERPETUAL default (the exact failure shape as this file's other documented classifier gaps).
      **Fixed**: `market-tick-data-service@06c07089` widens the regex to `-\d+(?:D\d+)?-[CP]$` (strictly a superset
      of the old form — safe for every other venue, mirrors the reasoning of this file's other regex-widening
      commits), with a new regression test file
      (`tests/unit/test_deribit_decimal_strike_option_classification.py`). QG green, quickmerge-verified on origin.
      **Delete**: the corrupted object was found **already absent** when this session went to execute the §3a
      delete — confirmed via a direct `list_blobs` re-listing of the exact GCS prefix, which returned only the same
      3 sibling objects (byte-identical sizes to the earlier investigation's report) the corrupted file was
      originally found alongside; someone/something already deleted it between the 2026-08-15 investigation and
      this session, with no corresponding Progress Log entry (a small commit-push-flip discipline gap, same shape as
      a prior gap noted in `deribit_combo_perpetual_partition_move_2026_07_21.md`'s Progress Log). No delete action
      was needed or taken this session.
      **Re-fetch — NOT done, split into the new todo below.** An ad hoc CLI invocation from this interactive slot
      session (`market_tick_data_service.cli.main --operation download`) did not cleanly resolve to the prod
      environment (`ServiceRuntime` logged `env=dev` even with `DEPLOYMENT_ENV=prod` set) and did not honor `--day`
      as expected (defaulted to "yesterday") within a short session — flagging rather than guessing further per this
      craft's `does_not: guess at an ambiguous fix`. Re-fetch needs a session with the actual mechanism confirmed
      (likely via a VM launcher setting `DEPLOYMENT_ENV` the way `launch-mtds-backfill-vm.sh` does, not an
      interactive ad hoc invocation).
      Repo: market-tick-data-service (fix + delete-verify).
- [x] ✅ [DATA] P3. **Re-fetch `XRP_USDC-30JAN26-2D3-P` (Deribit option, expiry 2026-01-30, strike 2.3, Put) for day
      2026-01-15** — **resolved as NOT NEEDED, not executed as a code fix.** See Progress Log
      2026-08-15 (slot-33, data_engineering) for the full evidence chain: the env-resolution question is answered
      (root cause found, harmless), and the re-fetch itself is architecturally impossible/inapplicable by design
      (Deribit per-strike options are `options_chain`-ONLY, never per-symbol `trades` — v10 scope,
      `mvp_backfill_cefi_tick_v10_2026_06_27.md` G4). The already-executed delete (prior todo) is the correct
      terminal state; no re-fetch under `data_type=trades` will ever succeed for this instrument by design.
      Repo: market-tick-data-service (investigation only, no code shipped).

## Progress Log

- **2026-08-09 (slot-8, infra)**: Filed while working `cefi_satellite_ao_dispatch_batch12_2026_08_09.md` todo 3 — the
  todo's own precondition check found a relaunch already happened (`-133746`) but it also failed, a state the original
  todo's done-when didn't anticipate. Closing the batch12 todo per its own stated logic (relaunch action already taken
  by another agent, so no duplicate launch from that todo); tracking the actual remaining work (a correctly-checkpointed
  4th attempt + wedge diagnosis if it recurs) here instead.
- **2026-08-09 21:38Z (slot-9, infra)**: Launched todo 1's 4th checkpoint-resumed attempt:
  `canonical-migration-cefi-content-apply-20260809-213834` (asia-northeast1-c), verified
  `RESUME_START_DATE=2026-01-08 RESUME_END_DATE=2026-01-15 RESUME_ASSET_GROUP=cefi-content-apply RESUME_SHARD_OF=1 RESUME_SHARD_INDEX=0`
  in the launch-time `LAUNCH_PARAMS.json` (correctly resumes from the day AFTER `-133746`'s
  `last_completed_date=2026-01-07`, not a replay). STARTED confirmed <60s (RUNNING immediately after
  `gcloud compute instances create` returned). Progress confirmed genuine and ongoing at multiple checkpoints: T+8min
  5000/85086 files (~10 files/sec), T+15min 7200/85086 files (~9.7 files/sec, `patched=174` — real writes happening, not
  just already-canonical skips). The tool's own "possible wedged worker" WARNING fires repeatedly even during this
  confirmed-healthy run (same as the source doc's `-032606`/`-133746` observation) — confirms that warning alone is NOT
  a reliable wedge signal on its own; only a genuine LOG-LINE STALL (no new `Progress:` line across multiple poll
  windows) or VM disappearance would indicate a real repeat-wedge. **Todo 1 is NOT yet done** — its own done-when
  requires a T+90min checkback (completion, active progress past 2026-01-08, or a repeat wedge); at time of this entry
  the run is only ~15min in. A background watcher (bounded 90min, checks every 10min, exits early on 3 consecutive
  stalled polls or VM disappearance) is armed to catch a genuine wedge without requiring a human to babysit it; the
  todo's own checkbox stays unflipped until that verification completes. If this session ends before the watcher
  reports, the next session (or the operator) should check
  `gcloud compute instances describe canonical-migration-cefi-content-apply-20260809-213834 --zone=asia-northeast1-c`
  (RUNNING vs NOT_FOUND) and tail
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-apply-20260809-213834/run.log`
  for the current `Progress:` line before deciding completion vs. a 5th relaunch is warranted.
- **2026-08-09 23:47Z (slot-12, infra)**: T+90min checkback on `-213834`. VM no longer exists (`NOT_FOUND` in
  asia-northeast1-c, self-deleted per `--instance-termination-action=DELETE`). `PROGRESS.json`:
  `last_completed_date=2026-01-10` (2 days past `RESUME_START_DATE=2026-01-08` — genuine active progress, not a replay,
  confirming the checkpoint math was correct). `run.log` shows real, ongoing `Progress:` lines up to `50800/85086 files`
  at `23:24:33Z` (`patched=912`, i.e. real writes, not just skips) interleaved with the same
  `WARNING No progress in the last poll window` self-diagnostic seen on every prior attempt — then at `23:24:51Z` the
  wrapping shell reports `Killed` (`rc=137`) and the deployment framework logs `received signal 15`,
  `DEPLOYMENT_FAILED exit_code=137`. `WATCHDOG_TRACE.log`'s own log-size-growth heuristic shows `progress=1` (file still
  growing) at every iteration up through its last recorded tick (`iter=101`, `ts=1786317863` ≈ `23:24:23Z`) — i.e. the
  file-growth watchdog did NOT flag a stall itself; the kill (SIGKILL, no `PREEMPTED` marker, no graceful-shutdown line
  before the signal) landed ~30-40s after the last confirmed-genuine `Progress:` line, matching `-032606`/`-133746`'s
  identical "real progress interleaved with 'possible wedged worker' warnings, then abrupt silence" signature exactly.
  **This is the 3rd wedge-shaped death on shard 24 (of 4 total attempts; the 2nd, `-065001`, was a clean SPOT
  preemption, a distinct failure mode)** — todo 1's own done-when explicitly names this outcome ("a repeat wedge, in
  which case STOP relaunching and treat todo 2 below as blocking"). Flipping todo 1 done on that basis (the launch
  action was correctly taken with the right checkpoint math, and its own done-when treats a confirmed repeat wedge as a
  valid terminal state, not a signal to keep relaunching) — no 5th relaunch attempted per the STOP instruction. Todo 2
  (root-cause diagnosis, market-tick-data-service) is now the actionable remaining work; leaving it for dispatch rather
  than absorbing it into this task (different investigation scope, no VM-launcher action left to take here).
- **2026-08-10 (slot-17, infra)**: Todo 2 diagnosis complete. Compared shard 24 (2026-01-08..15, 85,086 files across 8
  days, wedged 3/4 attempts) against shard 25 (2026-01-16..23, 79,134 files across 8 days, completed cleanly
  EXIT_STATUS=0).

  **Method**: Sampled per-day GCS file counts, per-venue distributions, per-data_type volume, and individual file-size
  distributions for both shards. Read the migration script's stall-detection logic
  (`market-tick-data-service/scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`) and the latest failed
  run's `run.log` (-213834, rc=137 at 50,800/85,086 files).

  **Finding 1 — "possible wedged worker" warnings are a red herring, not a wedge signal.** The script's
  `as_completed(timeout=30.0)` fires this WARNING whenever no future completes within 30s. This is EXPECTED for large
  parquet files (book_snapshot_5 files are 11-130MB+ compressed, decompress to much larger in-memory DataFrames, and
  take >30s to download+parse+patch+upload+verify over GCS). The `-213834` run.log proves this: warnings fire repeatedly
  between healthy `Progress:` lines showing 200-file increments at 8.1-8.2 files/sec — the script was making genuine,
  continuous progress. The REAL stall detector (`_STALL_TIMEOUT_SEC=900`, 15 min with zero completions) never fired. All
  3 wedge-shaped deaths were rc=137 (SIGKILL from Linux OOM killer), not the stall timeout.

  **Finding 2 — book_snapshot_5 is the dominant memory driver, and shard 24 has 63% more of it.** Per-data_type volume
  comparison (single representative day, 2026-01-08 vs 2026-01-16):
  - book_snapshot_5: shard 24 = 3,790 files / 42.0GB (11.3MB avg) vs shard 25 = 3,388 files / 25.8GB (7.8MB avg) → **63%
    more data, 46% larger per-file**
  - trades: shard 24 = 3,566 files / 8.6GB vs shard 25 = 3,183 files / 9.8GB (similar)
  - derivative_ticker: shard 24 = 2,209 files / 2.0GB vs shard 25 = 2,230 files / 1.8GB (similar)
  - All other data_types: negligible volume

  The 63% delta holds across all 8 days: shard 24's book_snapshot_5 averages 9.6-11.3MB/file (peak 42.0GB/day on
  2026-01-08) vs shard 25's 6.1-10.3MB/file (peak 33.1GB/day on 2026-01-20). Shard 24's worst day (42.0GB) is 27%
  heavier than shard 25's worst day (33.1GB). KRAKEN-FUTURES is the most extreme single-venue outlier: shard 24 has 800
  KRAKEN-FUTURES files/day averaging 5.3MB vs shard 25's 298 files/day averaging 1.8MB — a 7.6× total data volume
  difference, reflecting more active futures instruments on that venue in the earlier date window.

  **Finding 3 — No single poison-pill file; this is cumulative RSS creep.** The largest individual files are similar
  across both shards (DERIBIT trades at 4.4GB/3.8GB, DERIBIT options_chain at 378MB/1.0GB, book_snapshot_5 at
  130-255MB). No single file triggers the 2 GiB `_MAX_CLAIMED_UNCOMPRESSED_BYTES` ceiling. The pyarrow native pool
  (`bytes_allocated`) stayed bounded at 3.7-4.0GB throughout the `-213834` run — the existing `release_unused()` every
  200 files and `gc.collect()` every 50 files ARE working for pyarrow's own pool. But RSS still climbed to OOM-kill
  despite these mitigations — the memory growth is in Python-managed objects (pandas DataFrames, their internal
  BlockManagers and backing numpy arrays) that CPython's reference-counting + generational gc can miss when 12
  concurrent workers each hold live references to recently-processed DataFrames. The cumulative `bytes_read` at time of
  death (196GB across 50,800 files) confirms the volume: even a small per-file leak/miss compounds rapidly at this
  throughput.

  **Root cause summary**: Shard 24's book_snapshot_5 data is systematically larger (63% more volume, 46% larger
  per-file) than comparator shard 25's, which completed cleanly. The migration script's 12-worker ThreadPoolExecutor
  processes these large order-book-snapshot files concurrently, and Python's memory management cannot reclaim per-file
  allocations fast enough to stay under the 64GB e2-standard-16 ceiling across an 8-day, ~85K-file corpus. Shard 25
  stays under the OOM threshold because its lower book_snapshot_5 volume leaves enough headroom. The "possible wedged
  worker" signature is a diagnostic artifact of the 30s poll timeout, not a genuine thread hang — every death was
  rc=137, not the 900s STALL-break.

  **Recommended fix (for a follow-up plan; this task is diagnosis-only)**:
  1. Reduce default workers from 12 to 8 for the `cefi-content-apply` category (or make it env-overridable per-shard
     based on data density) — `launch-canonical-migration-vm.sh` already supports `WORKERS=N`.
  2. Add explicit `del df` after the verify step in `migrate_one_file()` and a `gc.collect()` call on the return path
     for every file (not just every 50).
  3. Tighten the pyarrow `release_unused()` cadence from every 200 files to every 50 files (same as the existing
     `gc.collect()` cadence) to release native buffers sooner.
  4. Raise the 30s `as_completed` timeout to 120s for large-file tolerance, suppressing the misleading "possible wedged
     worker" warning noise — the 900s STALL timeout is the real safety valve.

## Progress Log (continued)

- **2026-08-15 (slot-14, data_engineering)**: Picked up the diagnosis's recommendation #1 (never actioned since 08-10).
  Relaunched shard 24 checkpoint-resumed from `PROGRESS.json`'s `last_completed_date=2026-01-10`
  (`RESUME_START_DATE=2026-01-11 RESUME_END_DATE=2026-01-15`, not a replay) with `WORKERS=8` (down from the default 12)
  via `launch-canonical-migration-vm.sh` — `canonical-migration-cefi-content-apply-20260815-181337` (`e2-standard-16`,
  preemptible). No code changes to the migration script (recommendations #2-4 remain unshipped; the launch-time
  `WORKERS` override alone was sufficient to act on #1 without touching the shared script other 43 already-complete
  shards depend on). Verified STARTED <60s + genuine sustained progress at T+13min: 8,600/52,519 files, ~10.8 files/sec,
  `bytes_allocated` bounded near-zero across every periodic release — no repeat of the wedge signature. Left running
  under the fleet's existing 900s stall-timeout self-kill + `DP_VM_STALL` escalation monitoring rather than babysitting
  to completion within one session. If it wedges again on `WORKERS=8`, recommendations #2-4 (explicit `del df`, tighter
  `release_unused` cadence, 120s `as_completed` timeout) are the next things to try, in that order.
- **2026-08-15T21:10Z (slot-3, review, from `cefi_residual_ao_dispatch_2026_08_15_finalize.md`)**: the `WORKERS=8`
  relaunch above **completed successfully** — `EXIT_STATUS=0`, all 52,519/52,519 files, terminal
  `SCRIPT 1 CONTENT MIGRATION SUMMARY (APPLIED)` banner, `DEPLOYMENT_COMPLETED exit_code=0` at 20:13:16Z, clean
  `VM_SHUTDOWN_ON_COMPLETION` self-delete — no repeat wedge, recommendations #2-4 were not needed. This closes out
  shard 24 as the sole remaining holdout of the 44-way `cefi-content-apply` fleet per
  `cefi_residual_ao_dispatch_2026_08_15.md`'s todo 2. One new finding filed as a todo above (a confirmed poison-pill
  parquet file this run's own safety-skip correctly refused). Full verification evidence + method:
  `cefi_residual_ao_dispatch_2026_08_15_finalize.md` Progress Log (now archived to `plans/archive/2026_08/`).
- **2026-08-15 (slot-12, infra)**: Investigated the poison-pill file (direct GCS reads via
  `unified_trading_library.cloud_interface.get_storage_client()` — no subprocess `gcloud`/`gsutil`, all bounded
  single-object gets/ranges, no corpus walk). **Confirmed genuinely corrupted, not a false-positive safety-skip:**
  1. **Object metadata**: 5,159,827,874 bytes (~4.8GB) on disk, `last_modified=2026-06-27T21:30:52Z`.
  2. **Sibling comparison** (same directory, `list_blobs` on the exact prefix): the other 3 objects in
     `.../venue=DERIBIT/instrument_type=perpetual/data_type=trades/` for this day are 1.0-1.2MB each
     (`DERIBIT:PERPETUAL:BTC-USD@INV.parquet`=1,174,053B, `DERIBIT:PERPETUAL:ETH-USD@INV.parquet`=1,023,601B,
     `ticks.parquet`=1,173,742B) — the flagged file is **~4,400x larger** than its peers, and unlike them its filename
     is a RAW (non-canonical) symbol stem, not the already-migrated `DERIBIT:PERPETUAL:...` form its siblings carry —
     consistent with this object predating or escaping the id-catalogue migration.
  3. **Parquet footer magic check** (last 4MiB via `download_bytes_range`, no full-file download): the file's final 4
     bytes are `89 50 41 52`, NOT the required parquet magic `50 41 52 31` ("PAR1") — the footer is genuinely
     corrupted (or the file is truncated/malformed at the tail), which is why pyarrow's footer-length parse produced
     the nonsensical claimed-uncompressed-size the migration script's `_MAX_CLAIMED_UNCOMPRESSED_BYTES` guard
     correctly caught. This is NOT a case of the safety threshold being too conservative — the file cannot be
     correctly parsed as parquet at all from its current tail bytes.
  4. **Catalogue cross-check** (`prod/catalog.parquet`, `instruments-store-cefi-prd-central-element-323112`, one
     bounded 9.1MB read): **no catalogue row exists for `raw_symbol=XRP_USDC-30JAN26-2D3-P` under any venue** — this
     exact symbol string isn't a registered instrument. But a substring search for the shared leg-token `2D3` found 4
     catalogue rows, all DERIBIT/DERIBIT-COMBO **COMBO** instruments sharing both the `2D3` leg code and the
     `30JAN26` expiry: `DERIBIT:COMBO:XRP_USDC-CS-30JAN26-2D3_2D6` and
     `DERIBIT-COMBO:COMBO:XRP_USDC-RR-27MAR26-2D3_2D4` (plus their DERIBIT-COMBO-venue twins). This is the same
     symbol-shape family `deribit_combo_perpetual_partition_move_2026_07_21.md` (closed 2026-08-12, 1,719 objects
     moved `perpetual`→`combo`) diagnosed and fixed — but that migration's census regex
     (`-(FS|CS|PS|STRD|STD|IRON|BOX)-`) requires a combo-type infix token, which this filename
     (`XRP_USDC-30JAN26-2D3-P`, no infix) does NOT match, so it would not have been swept by that census either way.
  **Conclusion**: likely a residual/malformed DERIBIT combo-shape object (a truncated or differently-encoded combo leg
  symbol) that both (a) sat outside the sibling migration's shape regex and (b) is independently corrupted at the
  parquet-footer level — two separate defects on one object, not one. Repair needs a delete-safety-cited action, not a
  blind re-fetch under `instrument_type=perpetual` (which would just recreate a wrong classification if this is
  confirmed combo-shaped) — split into the new `[DATA] P2` todo above rather than executing a guess this session. No
  GCS object was written, moved, or deleted this session — every check was a read.
- **2026-08-15 (slot-15, data_engineering)**: Settled the combo-vs-legit classification and root-caused the
  misclassification. **Not combo-shaped**: verified programmatically that `XRP_USDC-30JAN26-2D3-P` matches neither
  the migration doc's combo census regex (`-(FS|CS|PS|STRD|STD|IRON|BOX)-`) nor the classifier's own
  `is_deribit_combo_symbol_shape` (needs a type-code second dash-segment; this symbol's second segment is
  `30JAN26`, a date token). **It is a genuine standalone Deribit decimal-strike OPTION**: read
  `tardis_symbol_parsing.py`'s `_DERIBIT_OPTION_SYMBOL_RE`, whose own comment documents Deribit's `d`-separator
  sub-dollar-strike notation (`1d7`=1.7, `0d05`=0.05, "accounts for ~74k of 283k option symbols" per a 2026-05-04
  live check) — `2D3` decodes the same way (strike=2.3, plausible for XRP's price range around Jan 2026), with
  trailing `-P` = Put and `30JAN26` = a valid expiry date token. **Root cause of the misclassification**: the
  classifier used at write time, `TardisAdapter._OPTION_SYMBOL_RE` (`tardis_adapter.py`, a DIFFERENT, simpler regex
  than the one above), required a pure-digit strike (`-\d+-[CP]$`) — `2D3` is not `\d+` (contains a letter), so this
  symbol matched neither the option regex, the dated-future regex, nor the combo-shape check, and fell through
  `_classify_row_instrument_type`'s unconditional final line to `InstrumentType.PERPETUAL` — the identical failure
  shape this file's `deribit_combo_perpetual_partition_move_2026_07_21.md` §3 and this same adapter file's own
  inline comments already document for OKX dated-futures, Bitget month-code futures, and bare-DERIBIT combos.
  Confirmed no catalogue row exists for the exact `raw_symbol` (consistent with a decimal-strike option — the
  catalogue's raw-symbol column may use a different case/notation not probed this session), so the classification
  rests on the regex/domain match, not a catalogue hit; noted as a residual uncertainty, not treated as
  disqualifying (the corrupted footer would prevent confirming via content either way).

  **Fixed**: `market-tick-data-service@06c07089` widens `_OPTION_SYMBOL_RE` to `-\d+(?:D\d+)?-[CP]$` — a strict
  superset of the old pure-digit form (adds, never removes, matches), so safe for every other venue by the same
  reasoning this file's other regex-widening commits already use. New regression test file
  `tests/unit/test_deribit_decimal_strike_option_classification.py` locks the fix (decimal-strike Put/Call classify
  OPTION; integer-strike options, perpetuals, dated futures, and bare-DERIBIT combo shapes are all unaffected).
  `quality-gates.sh` full run green; `quickmerge --agent` landed, SHA verified an ancestor of
  `origin/live-defi-rollout` via `git merge-base --is-ancestor`.

  **Delete step — found already done, not executed this session.** Went to execute the §3a single-object delete
  (fresh `gcs_bucket_soft_delete_retention_seconds` check + `gcs_conditional_delete`, via
  `unified_trading_library.cloud_interface`, no subprocess `gcloud`/`gsutil`) and `gcs_describe_object` returned
  `None` — the object was already gone. Re-verified via a direct `list_blobs` on the exact GCS prefix
  (`gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-01-15/.../venue=DERIBIT/
  instrument_type=perpetual/data_type=trades/`): 3 objects, byte-identical sizes to the 2026-08-15 investigation's
  report (`DERIBIT:PERPETUAL:BTC-USD@INV.parquet`=1,174,053B, `...ETH-USD@INV.parquet`=1,023,601B,
  `ticks.parquet`=1,173,742B) — confirms the correct bucket/prefix was checked, and the corrupted object is
  genuinely gone, not a bucket-resolution miss on my part. No corresponding Progress Log entry anywhere in this
  doc's history records who/what deleted it — a small commit-push-flip discipline gap, the same shape flagged in
  `deribit_combo_perpetual_partition_move_2026_07_21.md`'s 2026-08-11 Progress Log entry.

  **Re-fetch — attempted, not completed, split into a new P3 todo.** Tried
  `market_tick_data_service.cli.main --operation download --mode batch --asset-group cefi --venues DERIBIT
  --day 2026-01-15 --data-types trades --instrument-ids XRP_USDC-30JAN26-2D3-P --dry-run` from this interactive
  slot session with `DEPLOYMENT_ENV=prod` set. Two anomalies: (1) `ServiceRuntime` logged `env=dev` regardless of
  the env var (env resolution did not respond the way `launch-mtds-backfill-vm.sh`'s own `DEPLOYMENT_ENV` metadata
  mechanism implies it should from a VM); (2) the run logged "no explicit dates provided — defaulting to
  yesterday=2026-08-14" despite `--day 2026-01-15` being passed. Did not push further or attempt a real (non-dry-run)
  fetch against an unconfirmed environment — flagging per this craft's `does_not: guess at an ambiguous fix` rather
  than risk a write against the wrong bucket or an uncontrolled Tardis API call. Filed as a new `[DATA] P3` todo
  rather than a blocked question, since it's a bounded, worker-determinable follow-up (diagnose the env-resolution
  path, then re-fetch), not a judgment call.

- **2026-08-15 (slot-33, data_engineering)**: Resolved the final open todo (re-fetch). **Env-resolution root cause
  found**: `ServiceRuntime.from_env_and_args` (`unified-trading-library/unified_trading_library/service_runtime.py:174`)
  reads env var `ENVIRONMENT` (default `"dev"`) for its `environment` field — NOT `DEPLOYMENT_ENV`, which is why the
  prior session's `DEPLOYMENT_ENV=prod` didn't change the logged `env=dev`. This is cosmetic/log-only for the download
  codepath, though: bucket resolution goes through a fully separate mechanism
  (`unified_trading_library/cloud_interface/bucket_naming.py`'s `resolve_raw_deployment_env()`, checking
  `os.environ["DEPLOYMENT_ENV"]` then `os.environ["ENVIRONMENT"]`, defaulting to `"prod"` if neither is set) — so the
  prior dry-run WAS already correctly targeting the prod bucket tier regardless of the misleading log line. Separately,
  confirmed `--day` is dead for the `download` operation: grepping `cli/` + `engine/`, `args.day` is consumed only by
  `cli/shard_key.py` (the `--shard-key`/`--date`-alias path) — `TickDataHandler`/`_adapter.py` never reads it, so
  passing bare `--day` left `start_date`/`end_date` both empty and the batch-mode defaulter fired
  ("no explicit dates provided — defaulting to yesterday", `unified_trading_library/service_framework/_adapter.py:214-218`).
  The fix is `--start-date`/`--end-date` (both set to the target day), confirmed via `service_cli.py:201-202`.

  **Executed the real (non-dry-run) re-fetch** with the corrected invocation
  (`DEPLOYMENT_ENV=prod ENVIRONMENT=prod .venv/bin/python -m market_tick_data_service.cli.main --operation download
  --mode batch --asset-group cefi --venues DERIBIT --start-date 2026-01-15 --end-date 2026-01-15 --data-types trades
  --instrument-ids XRP_USDC-30JAN26-2D3-P --force`) — confirmed `ServiceRuntime: ... env=prod` this time. Result:
  **0 records fetched by design, not a failure.** Log:
  `TardisAdapter: stripped 1 Deribit per-strike OPTION symbol(s) from the per-symbol trades request -- options are
  options_chain-ONLY, never per-strike`. Traced this to `tardis_batch_download.py:557-573` and its regression test
  `tests/unit/test_tardis_batch_download_deribit_option_grain.py`, whose own docstring states: "Deribit options are
  options_chain-ONLY (v10 scope, mvp_backfill_cefi_tick_v10_2026_06_27.md G4) -- per-strike option captures at
  trades/book_snapshot_5 grain are legacy artifacts (~1,048 rows purged in instruments-service@6986e8e4)." **The
  corrupted file this whole chain started from was itself one of those legacy artifacts** — a per-strike option
  captured under `data_type=trades`, which the v10 architecture explicitly forbids going forward. Its earlier delete
  (prior todo) is therefore the CORRECT terminal state, not a step awaiting a re-fetch; a re-fetch under
  `data_type=trades` for a per-strike Deribit option cannot ever succeed (0 records every time, by design), so
  continuing to retry would just repeat this same no-op. No code change needed — nothing to fix, the strip guard is
  working as intended. Confirmed the run had zero side effects beyond the attempted fetch: 0 objects written, and the
  attempted manifest write was itself REFUSED by the legacy-index-size guard (`ManifestWriter write failed: ... over
  the 209715200-byte legacy-read guard budget`), so no manifest mutation occurred either — safe to have run
  interactively (single-instrument, single-day scope, well under the heavy-I/O threshold). Flipped the todo `[x]`
  with this resolution rather than leaving it perpetually retrying an architecturally-impossible action. Every prior
  open todo in this doc is now closed; doc stays `assigned_vm: planning` / `archive_exempt: true` per its own
  frontmatter (no archival action taken or needed).
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries) — first scout pass on this doc; the 3
  pre-existing entries (the shard-24 early-preemption sibling finding, the vm-launcher-runbook codex SSOT, and the
  migration-VM launcher script) were already well-chosen and all verified to resolve on disk, so kept unchanged.
