---
doc_type: issue
title:
  "MTDS CEFI backfill VM OOM-kills unpredictably — confirmed via kernel log — and does NOT reliably go away at
  --chunk-days 1; the underlying process crash also isn't detected/recovered by the wrapping chunk loop"
summary: >-
  Launching a CEFI Tardis backfill via `launch-mtds-backfill-vm.sh` reproduced a real, confirmed kernel OOM-kill THREE
  times across three different chunk-size regimes (a 7-day test range, the 250-day default, and even a `--chunk-days 1`
  single-day chunk) — including two consecutive single-day chunks for the IDENTICAL symbol/venue set where day 1 used
  only 6GB and day 2 was OOM-killed at 14.6GB, ruling out a simple "memory scales with date-range span" explanation.
  After the OOM-kill, the wrapping `mtds_chunk_loop.sh`/heartbeat/uploader orchestration does not detect or recover from
  the child's death — the whole VM goes silently, unrecoverably stuck (no more log lines, no more heartbeats, no more
  GCS log uploads, serial console silent, SSH unreachable, no GCP host-error or preemption event) rather than failing
  loud or continuing to the next chunk. Every occurrence required a manual stop; nothing recovered on its own within the
  observation window (8-15+ minutes each). No reliable workaround identified — `--chunk-days 1` reduces but does not
  eliminate the risk, and makes each occurrence just as silent.
status: open
nature: issue
asset_group: [cefi, meta]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [backfill, oom, memory, tardis, cefi, reliability, vm-hang, resource-profiler]
related: [lst_rate_honest_coverage_2026_07_21]
created: 2026-07-22
author: unknown
priority: P0
parent_epic: infrastructure_master
source: >-
  Found while launching the LST rate honest coverage plan's #1 CEX-spot contiguity backfill
  (plans/active/lst_rate_honest_coverage_2026_07_21.md Phase 5) — reproduced on 2 independent VM launches before working
  around it.
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/lst_rate_honest_coverage_2026_07_21.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
    unified-trading-library/unified_trading_library/streaming/parallel_per_symbol_runner.py,
  ]
assigned_vm: NA
resolved_by:
---

## What I found

Launching `launch-mtds-backfill-vm.sh --asset-group CEFI --venues "..." --data-types trades --instrument-ids "..."` for
a real LST-token CEX-spot history backfill (3 venues, 9 symbols) hung twice:

**Attempt 1** (1-week smoke test, `--start 2026-07-15 --end 2026-07-21`, VM `mtds-backfill-cefi-1`): completed day 1
cleanly (3/4 venues captured real rows, manifest written), then went completely silent moving into day 2. Confirmed via
`gsutil stat` on the GCS run.log (Update time frozen), `gcloud compute instances get-serial-port-output` (zero new lines
for 8+ minutes, including the 60s heartbeat/uploader loops that should fire regardless), and two `gcloud compute ssh`
attempts that both timed out with no connection. No host-error or preemption event in `gcloud logging read`. Stopped +
deleted after ~15 min of silence.

**Attempt 2** (full history, `--start 2022-08-25 --end 2026-07-22`, same VM name, fresh launch, all 4 code tarballs
verified fresh this time — ruling out a stale-code explanation): `mtds_chunk_loop.sh` split this into 6 chunks of 250
days each (the launcher's `--chunk-days` default). Chunk 1 (`2022-08-25 → 2023-05-01`) started, and within ~30 seconds
the log's own `RESOURCE_SAMPLE` line showed:

```
2026-07-22 05:33:23,863 ... mem=14.7% rss=1173MiB ...
2026-07-22 05:33:55,705 ... mem=86.1% rss=12730MiB ...
```

— an 11.5x memory jump in 32 seconds, crossing the `ResourceProfiler`'s own configured `mem_crit=85.0%` threshold
(logged at startup: `ResourceProfiler started (sample=5.0s emit=30.0s mem_crit=85.0% disk_crit=1000000000)` and a
separate `Memory watchdog started for market-tick-data-service (threshold=85.0%)`). Immediately after that sample, the
log went completely silent — same symptom as Attempt 1 (no more RESOURCE_SAMPLEs at the expected 30s interval, no more
60s heartbeats, GCS log Update time frozen). Stopped + deleted after ~6 min of silence.

## Why this matters

- **Reproduced twice, in two different chunk-size regimes** (7 days and 250 days) — this doesn't look like one-off
  cloud/network flakiness, it looks like a real hang correlated with memory pressure crossing the configured threshold.
  The "Memory watchdog" is presumably _supposed_ to intervene gracefully (log, GC, restart, or fail loud) when
  `mem_crit` is hit — instead the process appears to freeze completely with no further output at all, which is a worse
  failure mode than a clean crash (a crash would at least surface in the log/exit code; this requires an external
  operator/agent to notice the silence and intervene manually).
- **This is the DEFAULT chunk size** (`CHUNK_DAYS=250` is the launcher's own default) — any CEFI Tardis backfill
  covering a multi-year window for even a modest number of (venue, symbol) pairs could hit this. It isn't specific to
  LST tokens; it's specific to how much data a single chunk pulls into memory at once (9 symbols × 3 venues × ~250 days
  of trades apparently already suffices to blow past 85% of 16GB on an e2-standard-4).
- **Cost impact**: two SPOT-VM launches burned real (if modest — minutes each) compute time on hangs rather than
  progress, on top of the earlier misdirected-launch mistake documented in the LST plan's Progress Log.

## First follow-up test — LOOKED like a fix, was NOT (corrected below)

Relaunched the identical (venue, symbol) scope with `--start 2022-08-25 --end 2022-08-27 --chunk-days 1` (forces the
bash-level `mtds_chunk_loop.sh` to spawn one FRESH python process per single day). Chunk 1 (`2022-08-25`) completed
cleanly — real Coinbase rows written (`CBETH-USD` 18,959 rows, `CBETH-ETH` 1,676 rows), OKX correctly honest-absent
(predates its `availableSince`), peak memory only 45.4% (6032MiB). At this point I wrote this issue doc's previous
version claiming `--chunk-days 1` as a "validated workaround." **That claim was premature — see below.**

## CONFIRMED: real kernel OOM-kill, recurring UNPREDICTABLY even at the same --chunk-days 1

Chunk 2 of the SAME run (`2022-08-26` — same 9 symbols, same 3 venues, same `--chunk-days 1`, i.e. an IDENTICALLY small
single-day chunk to chunk 1, which had just succeeded at only 45.4% memory) went silent immediately after its own
bootstrap (`ServiceRuntime: op=download` — did not even reach the catalogue-load line chunk 1 reached within a second).
`gcloud compute instances get-serial-port-output` on this VM showed a **real kernel OOM-kill**, not a mere "hang":

```
kernel: oom-kill:constraint=CONSTRAINT_NONE,...,task=python,pid=7677,uid=0
kernel: Out of memory: Killed process 7677 (python) total-vm:19827004kB, anon-rss:15344964kB, ...
systemd[1]: google-startup-scripts.service: A process of this unit has been killed by the OOM killer.
```

`anon-rss:15344964kB` ≈ 14.6GB — i.e. this single day's chunk ALSO blew past the same memory ceiling the 250-day chunk
hit, despite being the exact same size (1 day) as the immediately-preceding chunk that used only 6GB. **This disproves
the "memory scales with date-range span" hypothesis from the first follow-up test above** — if it were purely about
`(end_date - start_date)`, two back-to-back 1-day chunks for the identical symbol/venue set should use comparable
memory, not a >2x difference severe enough to cross an OOM threshold on one and not the other. The real trigger is
something UNPREDICTABLE — plausibly per-day data-volume variance for one of these symbols (worth checking whether any of
the 9 has an outlier-volume day), a retry-storm that sometimes fires and sometimes doesn't
(network-condition-dependent), or a resource that isn't always cleaned up between requests within a single invocation.
After the OOM-kill, the WHOLE deployment (heartbeat loop, uploader loop, the bash chunk-loop itself) went silent too and
never proceeded to chunk 3 — i.e. **the wrapping orchestration does not detect or recover from its own child process's
OOM death**, turning one killed process into an entirely stuck, silently-burning VM.

**There is no reliable workaround identified yet.** `--chunk-days 1` reduces exposure (a smaller chunk is less likely to
be the unlucky one that OOMs) but does NOT eliminate the failure mode, and — critically — makes each individual
occurrence itself SILENT AND UNRECOVERABLE rather than obviously fatal. Do not treat `--chunk-days 1` as a fix for this
specific 9-symbol/3-venue CEX-spot backfill; at best it lowers the odds per-invocation while making each occurrence just
as hard to detect.

## Suggested next steps (not done here)

1. Root-cause the actual in-memory blow-up in `market_tick_data_service`'s CEFI Tardis download path. Given it recurred
   at an IDENTICAL chunk size (1 day) with wildly different memory footprints (6GB vs 14.6GB) for consecutive days of
   the same symbol/venue set, the trigger is likely either (a) genuine per-day data-volume variance for one specific
   symbol, (b) a retry-storm / unbounded-buffer path that only fires under certain response conditions, or (c) a
   resource leak that persists within a single process's lifetime regardless of how short that lifetime is.
2. Separately and regardless of (1): the wrapping `mtds_chunk_loop.sh` / heartbeat / uploader orchestration needs to
   detect a child OOM-kill (or any non-zero/killed exit) and either fail loud (page/alert) or skip-and-continue to the
   next chunk — right now a single OOM anywhere in a multi-chunk run silently wedges the ENTIRE VM with no further
   chunks processed and no signal beyond GCS-log staleness.
3. Until (1) and (2) land, treat any CEFI Tardis backfill (any chunk size) as needing active, close monitoring rather
   than a fire-and-forget launch — this may affect other, already-completed-looking backfills that could have silently
   died partway through without anyone noticing (worth an audit of recent CEFI backfill VMs' actual completion vs
   claimed completion).

## Evidence

- VM names: `mtds-backfill-cefi-1` (both attempts reused the default auto-derived name; deleted after each hang).
- GCS log Update-time freeze confirmed via `gsutil stat`.
- Serial console silence confirmed via `gcloud compute instances get-serial-port-output --start=<offset>`.
- Cloud Logging confirmed no host-level events via
  `gcloud logging read "resource.type=gce_instance AND resource.labels.instance_id=..."`.
- Full run.log excerpts for both attempts are in the LST plan's Progress Log
  (`plans/active/lst_rate_honest_coverage_2026_07_21.md` Phase 5, 2026-07-22 entries).

## 2026-07-26 root-cause + fix (slot-4, `data_engineering`, task `cefi_satellite_ao_dispatch_batch2-014`)

### Root cause (code-read, `market-tick-data-service`)

Call chain for `--asset-group CEFI --venues ... --data-types trades`: `TickDataHandler.process()` → `process_ticks()`
(`engine/orchestrator/__init__.py:593`) → `asyncio.gather()` over all active venues (`__init__.py:708-709`, gated only
by `graph_semaphore = Semaphore(3)`) → `_fetch_one_venue()` → `TardisAdapter.download_batch()`
(`adapters/tardis_batch_download.py:433`) → `ParallelPerSymbolRunner.run()`
(`unified_trading_library/streaming/parallel_per_symbol_runner.py`) → per-symbol streaming fetch
(`market_interface/adapters/tardis/tardis_csv_transport.py`).

**Leading cause: no aggregate BYTE budget, only a task-COUNT cap.** `_get_perp_runner()`
(`tardis_batch_download.py:236-253`) builds the shared `ParallelPerSymbolRunner` with
`max_concurrent=`/`in_flight_registry=`/`resource_profiler=` — it never passes `max_in_flight_bytes`. In
`parallel_per_symbol_runner.py:295-319`, `_await_capacity()` is a documented no-op whenever
`max_in_flight_bytes is None`, which it always is for this caller. The only admission control is a per-`run()`-call
`asyncio.Semaphore(max_concurrent)` (default `TARDIS_MAX_INFLIGHT_TASKS=128`) plus the shared HTTP-fetch semaphore
(`TARDIS_MAX_CONCURRENT_DOWNLOADS=32`) — both COUNT caps, no byte-SUM cap. For this incident's chunk (3 venues × 9
symbols × 1 data_type = 27 tasks), 27 is under both caps, so **every symbol-day for the whole chunk is scheduled
concurrently with no bound on their combined size.** The finalizer's own docstring (`tardis_cefi_shards.py:390-393`)
states a single heavy-volume symbol-day can already cost ~1GB even on the safe streaming path ("Coinbase BTC-USD
book_snapshot_5 days hit ~30GB under the legacy non-streaming finalize... ~1GB on BTC-USD heavy days" for the fixed
streaming variant). Trading volume is correlated across symbols on the same calendar day (a volatile/news day spikes
most of the 9 symbols simultaneously, not just one) — so the NUMBER of simultaneously-heavy shards in flight, and hence
total RSS, is an emergent, uncapped function of that day's market activity. `ResourceProfiler`'s 75%-mem-crit callback
(`cli/main.py:137-169`) only pauses NEW task scheduling — already-in-flight tasks continue to completion regardless, so
once the threshold is crossed the already-running large shards keep growing toward the OOM ceiling anyway.

A secondary, fully-sufficient-on-its-own mechanism (`TARDIS_STREAMING_FINALIZE=false`, NOT the default — confirmed
`default=True` at `service_config.py:284-290`) would fully materialize a whole symbol-day into one uncapped
`list`-of-batches → DataFrame (`tardis_csv_transport.py:257-333`) — ruled unlikely to have been active here, but worth
confirming via VM metadata if this recurs.

### Fix shipped (two parts, mirrors the exact `tradfi_backfill_oom_remediation_2026_06_24.md` precedent)

**1. Machine-type bump (the operational unblock — same fix, same precedent, weeks of zero-OOM-recurrence there).**
`deployment-service/scripts/vm/launch-mtds-backfill-vm.sh` now defaults `MACHINE_TYPE=e2-highmem-4` (32GB) for
`--asset-group CEFI` specifically (other asset groups keep `e2-standard-4`; an explicit `--machine-type`/`MACHINE_TYPE`
always wins). 32GB gives ~2.2x headroom over the observed 14.6GB peak — the same margin tradfi's identical fix validated
(32GB vs its 15.3GB peak, zero OOM-kills over weeks of fleet operation per that doc's 2026-07-14 re-verification).

**2. `mtds_chunk_loop.sh` fail-loud (the explicit ask).** `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`'s
`mtds_chunk_loop.sh` generator now captures the actual per-chunk exit code (was `... 2>&1 || true`, silently discarding
it) and logs a greppable `CHUNK_FAILED: chunk=N/TOTAL ... exit=137 reason=OOM_KILLED` (or `reason=NONZERO_EXIT` for any
other non-zero) line before continuing to the next chunk — shard-level failure isolation, one bad chunk no longer relies
on log-staleness inference to be noticed.

**Not shipped — filed as a P2 follow-up below, matching tradfi's own P2 memray-the-footprint precedent exactly**: wiring
`max_in_flight_bytes` (using `PerSymbolTask.estimated_bytes`, already a field on the type but never populated by the
CEFI Tardis caller — `parallel_per_symbol_runner.py:76-84`, `tardis_batch_download.py:149-203`) so the runner's existing
byte-budget gate becomes real. This needs a genuine per-symbol expected-byte estimator (a nontrivial design problem —
you don't know a day's volume until you've fetched it) and is materially riskier to get right without live validation
than the two shipped fixes; the machine-type bump already gives the same practical unblock margin the tradfi precedent
proved sufficient.

### Note on why the whole VM (not just the killed python process) went silent

The kernel log shows `constraint=CONSTRAINT_NONE` (a global OOM decision, not a memory-cgroup-scoped one) killing only
the `python` PID — bash's `mtds_chunk_loop.sh` and the separate 60s `PIPELINE_HEARTBEAT` background loop
(`_launch_with_tee`, `setup-data-pipeline-vm.sh:1082`) are NOT what got killed and, per plain bash semantics with
`|| true`, should have survived to log the next chunk. The most likely explanation for total unresponsiveness (no
further heartbeats/RESOURCE_SAMPLEs, SSH unreachable) is that a global (non-cgrouped) OOM event on a 16GB box forces the
kernel through prolonged direct-reclaim/thrashing before and around the kill, which can stall EVERY process on the box —
including the trivial heartbeat `sleep 60; echo` loop — for several minutes, indistinguishable from a "hang" from the
outside within the 6-15 minute observation windows used before each VM was manually stopped. Not independently verified
(would need a live reproduction with e.g. `dmesg -T` timestamps around the stall), but it means the fail-loud logging
fix (part 2) helps if/when the box recovers, while the real fix for the freeze itself is removing the trigger (part 1:
bigger machine, so the global OOM path is never entered at all).

- [x] [DATA] P2. **Wire real byte-budget admission control into the CEFI Tardis per-symbol runner** — populate
      `PerSymbolTask.estimated_bytes` (from a lightweight per-symbol/day volume estimate, if a cheap enough one exists —
      e.g. a rolling average of recently-observed row counts per symbol) so `_get_perp_runner()`'s `max_in_flight_bytes`
      gate (currently always `None`, a permanent no-op per `_await_capacity()`) becomes a real cap on
      simultaneously-in-flight shard bytes, not just task count. Repo: market-tick-data-service. Not required to unblock
      (the e2-highmem-4 bump already gives the same practical margin the tradfi precedent validated) — this is the
      deeper, durable fix for the underlying unboundedness, same relationship as tradfi's own P2 memray follow-up to its
      machine-type-bump unblock.

## 2026-07-29 second recurrence — sports/odds_api launcher (slot-16, `data_engineering`, task `sports_odds_api_scattered_multiyear_gaps-001`)

**Same bug class, different launcher.** While running a live gap-fill backfill
(`launch-mtds-sports-odds-backfill-vm.sh --start 2020-06-06 --end 2026-07-29`, VM `mtds-backfill-odds-gapfill-20260729`,
`--asset-group SPORTS`) to close 595 scattered missing odds_api calendar days, chunk 9/9 (`2025-11-27→2026-07-29`, the
most-recent-history chunk containing several of the real gaps) OOM-killed:

```
mtds_chunk_loop.sh: line 56: 12932 Killed  ... python -m market_tick_data_service --operation download ...
CHUNK_FAILED: chunk=9/9 range=2025-11-27→2026-07-29 exit=137 reason=OOM_KILLED
```

`RESOURCE_SAMPLE` lines show the same climbing-RSS signature as the original CEFI incident, just slower (across one real
fetch day's write-out rather than within 32 seconds): mem=52.2%→66.0%→85.0%→90.2% (rss
6558MiB→9557MiB→12586MiB→13468MiB) on `e2-standard-4` (16GB), immediately after a real odds_api fetch day (2026-04-15)
that fanned out over 63 distinct `(bookmaker, league, fixture)` shards for a single date. This is the identical root
cause already diagnosed above for CEFI Tardis (no aggregate byte-budget cap, only task-count caps) — the odds_api
adapter's per-date fan-out over many bookmaker/league/fixture combinations is the sports-side equivalent of CEFI's
per-symbol fan-out. **Confirms this is a general `mtds_chunk_loop.sh`-family risk, not CEFI/Tardis-specific**, exactly
as the root-cause section above already suspected but had not yet observed recur on a different asset_group/venue.

**Why the CEFI fix didn't cover this**: the 2026-07-26 fix bumped `MACHINE_TYPE` in `launch-mtds-backfill-vm.sh`
specifically for `--asset-group CEFI` (other asset groups explicitly kept `e2-standard-4`). The sports odds backfill
uses a SEPARATE, dedicated launcher (`launch-mtds-sports-odds-backfill-vm.sh`) that was never touched by that fix and
still defaulted to `e2-standard-4`.

**Fix applied (same precedent, this launcher)**: `deployment-service@bbce1b6` bumps
`launch-mtds-sports-odds-backfill-vm.sh`'s `MACHINE_TYPE` default to `e2-highmem-4` (32GB), same ~2.2x headroom margin
over the observed peak that the CEFI fix validated. The `mtds_chunk_loop.sh` fail-loud `CHUNK_FAILED` logging (part 2 of
the original fix) is shared infrastructure and already worked correctly here — it's what surfaced this recurrence
immediately instead of a silent short-fall. Relaunching the same range on the bumped machine type to close the remaining
tail (chunk 9's unprocessed dates).

- [x] [DATA] P2. **Audit every OTHER `deployment-service/scripts/vm/launch-mtds-*-backfill-vm.sh` launcher for the same
      `e2-standard-4` default** — the CEFI fix and this sports fix were both reactive (applied only after an actual
      OOM-kill was observed). Given the shared `mtds_chunk_loop.sh` fan-out-with-no-byte-budget root cause is
      demonstrably NOT asset-group-specific, a proactive sweep of every sports/tradfi/defi MTDS backfill launcher's
      default machine type (vs. its typical per-chunk fan-out width) would catch the next recurrence before it burns a
      VM launch, instead of after. Repo: deployment-service.

## 2026-07-27 recent-CEFI-backfill claimed-vs-actual completion audit (slot-5, `data_engineering`, task `cefi_satellite_ao_dispatch_batch1-026`)

**Scope**: every `mtds-backfill-cefi-*` VM launch, cross-checked two ways — (a)
`gcloud compute operations list --filter="targetLink~mtds-backfill-cefi"` (operation retention covers 2026-07-18 →
2026-07-27, the full window the API currently returns for this project), and (b) every log directory under
`gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-cefi-*` (GCS listing has no time window, so this
covers ALL history, not just the 9-day operations window).

**Finding 0 — only one real (non-smoke-test) VM name exists.** `launch-mtds-backfill-vm.sh --asset-group CEFI` has only
ever been invoked without `--vm-name` (i.e. under its auto-derived default), so every real backfill run shares the name
`mtds-backfill-cefi-1`. Every OTHER `mtds-backfill-cefi-*` prefix in GCS (~80 directories) is a
`-pipelinecheck-<timestamp>-<hash>` single-shard smoke test from the `/data-pipeline-check-mtds` skill — those are
diagnostic checks with no declared multi-day coverage scope, so they're out of scope for a "claimed vs actual
completion" audit (there's nothing for them to silently under-shoot). **No CEFI backfill VM (real or smoke) has launched
since 2026-07-21T22:57 PDT / 2026-07-22T05:57 UTC** — there is nothing more recent than the 3 runs below to audit.

**Findings table** — all 3 real launches are THIS issue doc's own 3 reproduction attempts (Attempts 1–2 in "What I
found" above, Attempt 3 in "CONFIRMED: real kernel OOM-kill" above):

| #   | Launch → stop/delete (UTC)                                     | Declared scope                                                                        | Claimed-complete signal (`mtds-backfill loop complete` / self-delete-on-success)?                                                                                                                                       | Actual coverage (verified this session)                                                                                                                                                                                                                                                                                                                                                                                                                        | Silent short-fall?                                                                                                                                                                                                           |
| --- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | insert 05:13:21 → stop 05:29:14 → delete 05:30:25 (2026-07-22) | `--start 2026-07-15 --end 2026-07-21`, 3 venues × 9 LST symbols                       | **NO** — manually stopped after ~8min of frozen log/heartbeat, no completion line ever written                                                                                                                          | `gcloud storage ls` spot-check: day=2026-07-15 has shards for COINBASE-SPOT/OKX-SPOT; day=2026-07-16 has zero for either — matches the doc's "day 1 clean, day 2 onward silent" claim                                                                                                                                                                                                                                                                          | No — failure was LOUD (frozen serial console + SSH-unreachable detected live within the observation window, prompting the manual stop), not a silent gap discovered after the fact.                                          |
| 2   | insert 05:31:01 → stop 05:40:19 → delete 05:41:32              | `--start 2022-08-25 --end 2026-07-22`, 6×250-day chunks (full history)                | **NO** — went silent ~30s into chunk 1/6 (RESOURCE_SAMPLE mem 14.7%→86.1% in 32s), manually stopped after ~6min                                                                                                         | Chunk 1/6 never reached a manifest write — zero coverage for the entire declared range                                                                                                                                                                                                                                                                                                                                                                         | No — same as #1, detected live, already root-caused above.                                                                                                                                                                   |
| 3   | insert 05:43:56 → stop 05:56:23 → delete 05:57:25              | `--start 2022-08-25 --end 2022-08-27 --chunk-days 1`, same 3-venue/9-symbol LST scope | **NO** — `run.log` (still live in GCS at `vm-logs/mtds-backfill-cefi-1/run.log`, unmodified since creation) ends mid-bootstrap of chunk 2/3, last line `PROGRESS: chunk=1/3 range=2022-08-25→2022-08-25`, no line after | Re-verified this session via `gcloud storage ls`: chunk 1/3 (2022-08-25) partial — `COINBASE-SPOT:SPOT_PAIR:CBETH-USD.parquet` + `CBETH-ETH.parquet` present (matches the log's `SHARD_INCOMPLETE`/1-of-2-venues line); chunk 2/3 (2022-08-26) — zero CBETH/WEETH/STETH shards exist under `COINBASE-SPOT/…/data_type=trades/`, confirming the kernel OOM-kill (already evidenced via serial console above) produced NO partial write; chunk 3/3 never started | No — confirmed kernel OOM-kill, VM manually stopped same session, already root-caused + fixed (see the 2026-07-26 addendum above: `e2-highmem-4` machine-type bump + `mtds_chunk_loop.sh` `CHUNK_FAILED` fail-loud logging). |

**Conclusion: zero silent short-falls found.** The only 3 CEFI backfill VM launches in the available audit window are
this issue doc's own already-fully-diagnosed incident — none of the 3 ever reached a claimed-complete state (no
`mtds-backfill loop complete` log line was written by any of them, none self-deleted on success; all 3 were stopped
manually after a human/agent noticed the hang within minutes). The failure mode here is a LOUD, immediately-detected
hang, not a silently-short-falling "looks done" run — so this audit's specific concern (§ "Suggested next steps" item 3
above: "an audit of recent CEFI backfill VMs' actual completion vs claimed completion") is answered: there is no such
case to flag. The 2026-07-26 fix already shipped (machine-type bump + fail-loud `CHUNK_FAILED` logging) is the correct
thing to validate on the NEXT real CEFI backfill launch — no new follow-up todo is warranted from this audit beyond the
P2 byte-budget item already tracked above.

## 2026-07-29 machine-type bump alone insufficient — cross-day accumulation, not single-day fan-out (slot-16, `data_engineering`, task `sports_odds_api_scattered_multiyear_gaps-001`)

**The `e2-highmem-4` bump (documented above, same session) did NOT fix the sports/odds_api recurrence — it OOM-killed
again, in the identical chunk, on the doubled machine.** Relaunching `mtds-backfill-odds-gapfill-retry1-20260729` on
`e2-highmem-4` (32GB) reproduced `CHUNK_FAILED: chunk=9/9 range=2025-11-27→2026-07-29 exit=137 reason=OOM_KILLED` a
second time. Critically, this run's `RESOURCE_SAMPLE` trail shows the failure mechanism is **different from the CEFI
root cause**:

```
20:33:41  mem=27.2% rss=6571MiB   (chunk 9 bootstrap, before any real fetch)
20:34:44  mem=31.6% rss=8513MiB   (during date=2026-04-15's fetch — one real day)
20:35:24  mem=46.6% rss=13266MiB
20:35:55  mem=55.2% rss=16346MiB
20:36:29  mem=46.4% rss=25599MiB  (date=2026-04-15 write-out ends; 2026-04-16 pre-flight starts)
20:37:00  mem=61.2% rss=17542MiB
20:37:34  mem=73.0% rss=21526MiB
20:38:05  mem=74.5% rss=23788MiB
20:39:27  OOM-killed (exit 137)
```

RSS kept climbing through the SECOND real-fetch day (2026-04-16) on top of whatever the first day (2026-04-15) had
already allocated — it never dropped back toward baseline between dates the way chunks 1-8's all-skip days did (compare
the ~660-700MiB baseline `RESOURCE_SAMPLE`s seen throughout chunks 1-8, vs. this chunk never returning below ~6.5GB once
a real fetch started). **This is memory accumulating ACROSS multiple real-fetch days within one long-lived
`--start-date/--end-date` subprocess invocation, not (only) CEFI's "one day's uncapped concurrent fan-out" mechanism** —
though the two may compound (both lack an admission-control ceiling; CEFI's is per-request concurrency, this looks like
inter-request retention). Doubling the machine size only bought roughly one extra real-fetch day before hitting the new,
higher ceiling — for a chunk containing enough real-fetch days (chunk 9 is the tail of the range, where scattered
recent-history gaps cluster), NO machine size fixes this without bound, since the accumulation is a function of
real-fetch-day COUNT per chunk, not a fixed per-day peak.

**Silver lining confirmed both times**: the crash happens only AFTER successfully completing every date from 2025-11-27
through 2026-04-15 — including the 2026-02-22..2026-03-28 (35-day) gap, the largest of the 6 multi-week ranges this
whole task exists to close. That portion is genuinely captured (verify via a fresh census after the tail lands, not
assumed).

**Mitigation applied (operational, not a code fix)**: relaunch scoped to just the unprocessed tail
(`--start 2026-04-16 --end 2026-07-29`) with a small `--chunk-size` (5 days) — forcing a fresh subprocess (and therefore
a fresh, empty memory baseline) every 5 days caps how many real-fetch days can accumulate in any one process lifetime,
regardless of the underlying retention mechanism. This is the same lever the CEFI incident's `--chunk-days 1` experiment
used, but where CEFI's per-day peak was itself unpredictable (6GB vs 14.6GB for consecutive identical-scope days,
disproving a pure date-span explanation there), this sports case has a much cleaner signature — cumulative, monotonic
growth across sequential real-fetch days — so a small fixed chunk size should be a reliable mitigation here even though
it wasn't a reliable one for CEFI.

- [ ] [DATA] P1. **RETAGGED 2026-08-07 (autonomous session) — `BLOCKED-CREDENTIALS` is stale, clearing it.** The
      2026-08-03 10M-credit top-up landed (`odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md`,
      archived/resolved); live-reverified today: `x-requests-remaining: 14,475,834` (of 15M). **Re-confirmed this bug is
      still live and unfixed today**: launched `mtds-backfill-odds-1` (default `--chunk-size 250`,
      `--start 2020-06-06 --end 2026-08-07`) and it OOM-killed on chunk 1/10 for 10 consecutive leagues in ~50 minutes
      (EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1, EREDIVISIE, PRIMEIRA_LIGA, JUPILER_PRO, SUPER_LIG,
      SCOTTISH_PREMIERSHIP — all `exit=137 reason=OOM_KILLED` on the identical `2020-06-06→2021-02-10` first chunk),
      zero successful chunk completions across any league — killed it. This matches this doc's own documented
      "cumulative, monotonic growth" signature exactly. Relaunch with `--chunk-size 5` deferred to the next tick
      pending: 14.4M credits confirmed healthy for the profiling work below, but the profiling itself has still never
      been done. ~~BLOCKED-CREDENTIALS 2026-08-02 (slot 14) — the-odds-api.com account is OUT OF USAGE CREDITS
      (5,000,772/5,000,000 used); no further real-fetch profiling (memray/tracemalloc/lightweight sampler) is possible
      until the operator either waits for the monthly reset or purchases additional credits — see this doc's 2026-08-02
      Progress Log entry and `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s matching P1 for full detail. Do
      NOT re-dispatch/re-attempt until credits are confirmed available again.~~ **Operator decision 2026-08-02
      (answering `BLK-6728ec9a`): Option B — purchase additional credits now.** Re-verify live before resuming (do not
      assume the purchase is instant); **confirmed landed + re-verified live 2026-08-07.** The promoted
      `scripts/odds_api_rss_sampler_2026_08_02.py` is the preferred next step once confirmed. Root-cause the actual
      retained-memory object(s) across date iterations in the sports odds_api download path (`market_tick_data_service`,
      the code path `--operation download --asset-group SPORTS` walks per-date inside one process — likely
      `TickDataHandler.process()`'s date loop or the `odds_api` adapter/finalizer holding a growing cache/buffer keyed
      across dates instead of per-date). A memray/tracemalloc profile across 2-3 consecutive real-fetch days would show
      whether it's an unbounded cache, an un-drained event-sink buffer, or accumulating asyncio/aiohttp session state.
      This is the durable fix; the small-chunk-size mitigation above is a workaround, not a repair. Repo:
      market-tick-data-service. **SHARPENED 2026-08-09 (main, Claude Code session)**: two candidate mechanisms ruled OUT
      this session by code read (incomplete session-reuse fix; the already-fixed per-VM-shard-growth class — see
      Progress Log entry same date for both). Two NOT-yet-tested candidates remain, both requiring live Linux kernel
      state a local macOS dev session cannot provide: (a) dirty-page/writeback backlog — sample `/proc/meminfo`'s
      `Dirty:`/`Writeback:` fields alongside RSS (extend the existing lightweight-sampler pattern) across a real
      multi-league chunk on an actual VM, checking whether they climb and stay elevated across subprocess boundaries
      within one VM lifetime, matching the 2026-08-07 cross-subprocess-persistence finding; (b) `pyarrow` mmap'd
      parquet-buffer non-release in `ManifestWriter._flush_per_vm_pending`'s read-merge-write path — a `memray --native`
      run (the doc's other standing next step) would attribute native allocations directly and settle which of
      (a)/(b)/neither is real. **Done when**: one of these is confirmed via a live run and either a code fix ships + is
      re-profiled to show RSS no longer climbs unbounded, or both are refuted and the search widens further (candidates
      then: OS-level malloc-arena fragmentation, or a growing shared/non-VM-scoped read target elsewhere in the
      pipeline).
- [x] [DATA] P2. **Consider an adaptive/smaller default `--chunk-size` specifically for "recent history" chunks** (the
      tail nearest the current date, where live-capture dormancy windows and scattered small gaps cluster densely) vs.
      the 250-day default that's proven safe for older, mostly-skip-dense history — either launcher-side (detect via a
      pre-flight gap count per chunk) or just a documented operator convention ("scope a small `--chunk-size` explicitly
      when re-running a tail that's known to have a high real-fetch-day density"). Repo: deployment-service.

## 2026-07-31 third recurrence — machine-type bump now insufficient even for SKIP-dense OLDER history (slot-5, `data_engineering`, task `sports_odds_api_scattered_multiyear_gaps-004`)

**New, more severe signature than either prior recurrence.** `mtds-backfill-odds-sentinel-fix-20260731`
(`launch-mtds-sports-odds-backfill-vm.sh --start 2020-06-06 --end 2026-07-31`, default `--chunk-size 250`, already on
the fixed `e2-highmem-4` machine type) OOM-killed on **6 of its first 6 completed chunks**
(`CHUNK_FAILED: ... exit=137 reason=OOM_KILLED` for chunks 1-6; chunk 7's log then cuts off mid-run with no further
lines — the same silent-freeze signature as this doc's original CEFI incident). Unlike the 2026-07-29 sports recurrence
(which only failed on chunk 9, the dense recent-history tail, and was explained by cross-day memory accumulation within
one real-fetch-heavy chunk), **these 6 chunks cover 2020-06-06..2024-07-14 — mostly `SKIP` days** (the manifest already
holds real captures for most of this range; only 7 `Processed date=` lines appear across the whole visible log vs. 201
`SKIP` lines). A chunk that is >95% skip-days should have a near-flat memory profile, yet still OOM-killed on a 32GB
machine that already has ~2.2x headroom over every previously-observed peak (14.6GB CEFI, ~23-25GB sports-tail). This
means **the machine-type bump is no longer a reliable mitigation even for the "safe" (skip-dense, older-history) case
the original fix was validated against** — a genuinely new severity level, not just a recurrence in a new launcher. Root
cause not further narrowed this session (same P1 below covers it — the retained-memory object hypothesis would explain
this too: if the leak is per-date-iteration regardless of SKIP vs. real-fetch, a 250-day chunk accumulates 250
iterations' worth of leaked state even when almost all of them no-op). **Mitigation applied**: relaunched with
`--chunk-size 5` (this doc's own best-validated workaround) as `mtds-backfill-odds-smallchunk-20260731` — full detail +
resume instructions in `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s Progress Log (same date, slot 5).
Given `--chunk-size 5` was previously 0/3 successful on the dense tail (2026-07-29 addendum above), this relaunch is a
mitigation attempt, not a confirmed fix — if it also fails, that's further evidence the P1 root-cause below needs to
land before this launcher can be trusted for any full-range run.

## 2026-07-31 fifth recurrence — `--chunk-size 5` mitigation now confirmed exhausted (data_pipeline_failure escalation, DP_VM_STALL)

**Dispatched via `POST /api/escalate wall_type=data_pipeline_failure` on a fleet-monitor `DP_VM_STALL` finding
(heartbeat 13m stale) against `mtds-backfill-odds-smallchunk2-20260731`** (the manual retry from the section above,
after its sibling `smallchunk-20260731` was preempted at ~55s with zero progress). Per
`/codex/15-runbooks/incidents/rb_infra_relaunch.md`, verified state before deciding relaunch-vs-stop:

- `gcloud compute instances describe` → `status=RUNNING` (NOT preempted — ruled out per the companion doc's own
  instruction to check `compute.instances.preempted` first).
- Dedicated GCS heartbeat blob (`vm-heartbeat/mtds-backfill-odds-smallchunk2-20260731.txt`) last updated
  `2026-07-31T09:28:52Z`; deployment-registry row (`deployments/active/536fc001-....json`) `last_heartbeat_at` same
  timestamp, `mem_pct: 68.3` with a positive, ACCELERATING `mem_slope` (2.08→3.23→6.11→...→6.87 %/min across the last 5
  samples) — i.e. still climbing toward the ceiling at the moment it went silent, not plateaued.
- `run.log` frozen at the same timestamp; re-checked twice ~18min apart, zero new bytes both times.
- Serial console (`get-serial-port-output`) shows **4 confirmed kernel OOM-kills on this single VM instance**, all
  `task=python`, all landing at `anon-rss≈31.7-31.8GB` (right at the `e2-highmem-4` 32GB ceiling): chunks 18, 26, 32, 74
  (`CHUNK_FAILED: ... exit=137 reason=OOM_KILLED` for each, confirmed via `run.log` grep). Chunk 74's OOM self-recovered
  (loop advanced to chunk 75 normally — the `mtds_chunk_loop.sh` fail-loud fix from the 2026-07-26 addendum is working
  as designed for THAT part). Chunk 75 then started fresh (RSS baseline ~518MiB), processed `2021-06-11` cleanly, hit
  three `SKIP` days, and went completely silent mid-chunk — **the fifth failure, and this one produced NO serial-console
  OOM line at all** (0 new serial bytes past the last-checked offset), matching this doc's original CEFI "silent freeze"
  signature (§ "Note on why the whole VM... went silent") rather than a clean OOM-kill: the dedicated 60s heartbeat
  sidecar (a trivial `while true; sleep 60` loop, immune to the python subprocess's own OOM) also stopped — consistent
  with prolonged kernel direct-reclaim/thrashing stalling the entire box, not just the worker process.
- Real progress made before the freeze: chunks 1-73 clean (skip-dense, already-covered history) + chunk 74 recovered +
  chunk 75 partial (`2021-06-11` processed) — last durable checkpoint ≈ `2021-06-11`, all via the standard
  `ManifestWriter` per-VM-shard path
  (`instruments-store-sports-prd-.../_index/per_vm/mtds-backfill-odds-smallchunk2-20260731-c75.parquet`), so nothing is
  lost — a future relaunch's skip-if-fresh logic will resume cleanly from here.

**Verdict: `--chunk-size 5` is CONFIRMED insufficient, not just unconfirmed.** This is the second full attempt at this
mitigation today (after `smallchunk-20260731`'s SPOT preemption denied it a real test) and it OOM'd 4 times in 75 chunks
(~5.3% chunk-failure rate) before a full unrecovered freeze — squarely inside "genuinely failing (not just preempting)
even at `--chunk-size 5`" that `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s own Progress Log already
flagged as the trigger to stop relaunching with the same parameters and escalate here instead.

**Action taken (per `rb_infra_relaunch.md`'s "if it re-fails the SAME way twice... STOP relaunching, file an issue"
bound — NOT relaunched)**: `gcloud compute instances delete mtds-backfill-odds-smallchunk2-20260731` — ended the SPOT
billing waste on a VM making zero further progress; no data lost (per the checkpoint evidence above). Did not attempt a
sixth launch with a smaller chunk size — CEFI's own experience (chunk-size 1 still OOM'd unpredictably, see "CONFIRMED:
real kernel OOM-kill, recurring UNPREDICTABLY" above) argues against assuming a further reduction reliably fixes this,
and repeatedly guessing at smaller chunk sizes without addressing the retained-memory root cause is exactly the pattern
the companion doc's Progress Log asked future resumers to stop doing.

**This raises the priority of the P1 root-cause todo below** — the sports odds_api backfill has now burned real SPOT
compute across 5 attempts today alone (`sentinel-fix` at `--chunk-size 250`: 6/6 completed chunks OOM'd; `smallchunk`:
preempted; `smallchunk2`: 4 OOMs + a final freeze) with the corpus still ~590/2247 days short — the operational
mitigation ladder (bigger machine → smaller chunks) is exhausted; only the code-level fix remains.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — All 4 items are genuine
  investigation/design work (byte-budget estimator design, cross-launcher audit, unresolved profiling investigation,
  chunk-size design choice), none with a worker-determinable checkable outcome today. NOTE: this doc's real asset_group
  is [cefi, meta], not infra — a residual scope-leak from this session's pre-fix Phase 0 population; classified here for
  completeness, no state changed, cefi tranche's own future audit owns this doc.
- 2026-07-31 (slot 5, data_engineering): Documented a third OOM recurrence (see new section above) while working
  `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s P1 backfill todo — worse severity than either prior
  instance (SKIP-dense older history now OOMs on `e2-highmem-4`, not just dense real-fetch chunks). No code fix
  attempted this session (out of scope for the dispatched task); relaunched the odds_api backfill with the
  `--chunk-size 5` mitigation as a workaround. The P1 root-cause todo below remains the durable fix and is still `[ ]`
  open.
- 2026-07-31 (slot 7, data_pipeline_failure escalation, DP_VM_STALL on `mtds-backfill-odds-smallchunk2-20260731`):
  Documented a fifth recurrence (see new section above) — the `--chunk-size 5` mitigation OOM'd 4 more times then froze
  unrecovered. Stopped the wedged VM (billing-waste avoidance, no data lost) rather than relaunching a sixth time with
  the same/smaller parameters, per this doc's own "silent freeze" precedent and the companion doc's explicit
  stop-and-escalate instruction. No code fix attempted (out of scope for a one-shot relaunch-escalation worker). The P1
  root-cause todo below is now the only remaining path to a reliable full-range run and should be treated as blocking
  further sports odds_api backfill attempts, not just a nice-to-have follow-up.
- **2026-07-31 (slot 3, data_engineering, task `sports_odds_api_scattered_multiyear_gaps-004`) — started the P1
  root-cause investigation itself (per the sibling doc's own "check that P1 first, do not relaunch again"
  instruction).** Confirmed via `mtds_chunk_loop.sh` (`deployment-service/scripts/vm/setup-data-pipeline-vm.sh`) that
  each CHUNK is a fresh `python -m market_tick_data_service --start-date CS --end-date CE` subprocess — the shell
  `while` loop persists across chunks, but the Python process (and everything in its heap) does NOT. So any leak must
  accumulate WITHIN one chunk's date range (confirmed real: `--chunk-size 5` still OOM'd after processing only ~5 dates
  per subprocess in some cases), not across chunks. **Ruled out `FixtureIdResolver._cache`
  (`market_interface/adapters/sports/fixture_id_resolver.py`) as the leak source** — traced
  `umi_tick_provider.py::_route_sports` (the actual per-date, per-venue dispatch call site) and confirmed it calls
  `get_adapter(venue.lower(), **_sports_kwargs)` fresh for EVERY date (no caching in `get_adapter`/`factory.py`), so a
  brand-new `OddsApiAdapter` — and hence a brand-new, empty `FixtureIdResolver._cache = {}` — is created each date; the
  cache cannot survive to accumulate across dates. This was my leading hypothesis before tracing the call site; a real,
  useful negative result, not a dead end (rules out re-deriving this same wrong lead later). Promoted a reusable local
  tracemalloc profiling harness (mirrors production exactly: fresh adapter per date + `gc.collect()`/`malloc_trim(0)`
  after each, matching `tick_data_handler.py::TickDataHandler.process()`) to
  `market-tick-data-service/scripts/profile_odds_api_backfill_memory_2026_07_31.py` — runnable locally against the real
  odds-api (now-working key) for a few consecutive real-fetch dates, no VM launch needed, per this todo's own
  "memray/tracemalloc profile across 2-3 consecutive real-fetch days" methodology. **Launched but NOT YET COMPLETE at
  session-end** (a single real-fetch date takes 60-190+s — dozens of leagues × multiple rate-limited API calls each);
  partial result so far: `2026-04-16` (0 rows, a genuinely quiet day) → 111.17 MB traced heap; `2026-04-17` (a
  real-fetch-dense day, many leagues with real fixtures) still in progress when this entry was written. **Next steps for
  whoever resumes**: re-run the promoted script directly
  (`GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp .venv/bin/python scripts/profile_odds_api_backfill_memory_2026_07_31.py <date1> <date2> <date3>`,
  picking 2-3 real-fetch-dense dates from the known-problematic tail e.g. `2026-04-16..2026-07-29`) and read its
  `tracemalloc.compare_to` output — if traced-heap-per-date grows monotonically across dates despite the fresh-adapter
  pattern, the leak is module-level/global state (check for module-level `@lru_cache`/mutable-default caches anywhere in
  the sports adapter's import chain) or something outside Python's tracked heap entirely (aiohttp connector-pool state
  that `_make_session()`'s `async with` should already close per-request, or glibc arena fragmentation `malloc_trim`
  can't reach). If it does NOT grow, the leak is likely something `tracemalloc` itself can't see (C-extension buffers,
  e.g. inside `aiohttp`/`pandas`/`pyarrow` native code) and the investigation should shift to `memray` (which tracks
  native allocations tracemalloc misses) instead of assuming the code is clean. **Trap hit**:
  `gcloud secrets versions access` can silently return an EMPTY string (not error) if the ambient `gcloud` CLI active
  account has drifted to a lower-privileged identity (`github-actions-deploy` instead of `unified-trading-sa`, same
  drift class `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` already documented) — this is a SEPARATE
  credential path from `GOOGLE_APPLICATION_CREDENTIALS`/ADC (what the Python client actually uses), so a CLI-level
  failure does not necessarily mean the real fetch path is broken; check `gcloud config get-value account` before
  concluding the key itself needs re-verification.
- **2026-07-31 (slot 3, data_engineering) — the profiling run FINISHED enough of itself to yield the actual answer;
  strong new lead, not yet a confirmed+shipped fix.** `2026-04-16` (0 real rows) → 111.17 MB traced Python heap.
  `2026-04-17` (a real-fetch-dense day: 22,713 real rows across ~25 leagues, hundreds of real HTTP calls) → **112.00 MB
  traced heap — under 1MB of growth despite processing thousands of real rows.** Meanwhile the OS-level RSS of the SAME
  process (`ps aux`, sampled 3 times across the run) climbed **930MB → 1.25GB → 1.92GB** over the same span. **This is
  the smoking gun**: `tracemalloc` (Python-object-tracked heap) stays essentially FLAT while OS RSS grows substantially
  — the leak is NOT retained Python objects (rules out dict/list/DataFrame accumulation definitively, on top of already
  ruling out `FixtureIdResolver._cache` above) — it's native/C-extension memory tracemalloc structurally cannot see.
  **Strong candidate, not yet proven**: `odds_api_adapter.py::_make_session()` —
  `aiohttp.TCPConnector(resolver=aiohttp.resolver.ThreadedResolver())` — is called FRESH for EVERY SINGLE HTTP request
  (5 call sites in this file, each wrapped `async with _make_session() as session, session.get(...) as resp:` — never
  one session reused across a league's or a date's many calls). A single real-fetch-dense date issues hundreds of these
  (the log shows leagues needing 8-30 API calls each, dozens of leagues per date). `ThreadedResolver` backs onto a real
  OS thread pool for DNS lookups; if the thread pool's native stack/buffer memory isn't promptly released back to the
  allocator on high-churn create/destroy cycles (a known aiohttp/thread-pool pattern, distinct from a pure-Python object
  leak), that would explain RSS-only, tracemalloc- invisible growth scaling with REQUEST COUNT (matching the doc's own
  observation that dense real-fetch dates are worse than skip-dense ones) rather than date-range span. **Not yet
  confirmed** — this needs either (a) a `memray` run (tracks native allocations tracemalloc misses — exactly the tool
  this todo originally called for as the alternative if tracemalloc came back flat) attributing the growth specifically
  to `ThreadedResolver`/`TCPConnector` construction, or (b) a quicker correlation check: log
  `len(threading.enumerate())` or RSS immediately before/after each `_make_session()` call across a dense date and see
  if it step-changes per call. **Recommended fix IF confirmed**: hoist one shared `aiohttp.ClientSession`/`TCPConnector`
  per `OddsApiAdapter` instance (or per `download_batch()` call) instead of constructing a fresh one per HTTP request —
  standard aiohttp guidance is one session per logical unit of work, not one per request, for exactly this class of
  resource-churn reason. **Did not apply this fix in this session** — it is a real code change to a hot path (5 call
  sites, all fetch/discovery methods) that needs its own verification (a session-reuse bug could silently break
  concurrent request isolation or auth-header handling) rather than a rushed edit at session-end; the promoted profiling
  script (`market-tick-data-service/scripts/profile_odds_api_backfill_memory_2026_07_31.py`) is exactly what a follow-up
  worker should re-run before/after any such fix to prove it actually closes the RSS-growth gap. **This todo stays `[ ]`
  open** — a strong, evidence-backed lead is not the same as a shipped, verified fix.
- **2026-07-31 (slot 3, same session) — profiling run finished all 3 dates; confirms the finding above, doesn't change
  it.** Full 3-point comparison, same single process throughout: `2026-04-16` (0 rows) → 111.17 MB traced; `2026-04-17`
  (22,713 rows) → 112.00 MB traced; `2026-04-18` (141,798 rows, the densest of the three, 628s elapsed) → **112.05 MB
  traced**. Traced Python heap is FLAT (111.17→112.05 MB, <1MB total drift) across a 0→141,798-row range — conclusive,
  not just suggestive. `tracemalloc.compare_to`'s top-15 growth entries are all trivial import-machinery noise
  (`importlib._bootstrap`/`_bootstrap_external` caches, `abc` registry, `urllib.parse`) — nothing resembling a real
  per-date accumulator anywhere in this codebase's own tracked allocations. This closes off "maybe it's a slow
  Python-level leak that just needs more dates to show up" as a competing explanation — 3 dates spanning a 0→141K-row
  range already show zero signal. The `ThreadedResolver`/native-memory hypothesis above is the only lead standing; next
  step is still the `memray` run (or the thread-count/RSS-per-`_make_session()`-call correlation check), not more
  tracemalloc dates.
- **2026-07-31 (slot 3, same session) — shipped the session-reuse fix as a resource-efficiency improvement; live
  re-profile does NOT confirm it closes the OOM. Todo stays OPEN.** Shipped `market-tick-data-service@6ca2d278`
  (verified landed via `git merge-base --is-ancestor`): folded reuse-or-create into `_make_session(existing=None)`
  itself (`@contextlib.asynccontextmanager`) so `_fetch_all_leagues` opens ONE real session/`ThreadedResolver` for a
  whole `download_batch()` call instead of one per HTTP request; two new regression tests
  (`tests/market_interface/unit/sports/test_odds_api_session_reuse.py`) assert exactly 1 real construction per batch and
  were verified to genuinely fail (18 and 2 constructions) against the true pre-fix SHA `86da3fa1` before trusting them
  green. File is 897/900 lines (was exactly 900; required folding an `AsyncExitStack`-based first attempt into the
  leaner `existing=` design to fit). **This is a real, verified, worthwhile change on its own merits** — fewer OS thread
  pools/sockets churned per batch is strictly better regardless of the OOM outcome. **However**: a live re-profile of
  the fixed adapter (same 3-date harness) showed RSS **comparable-to-or-higher** than the pre-fix baseline, not reduced
  — so this does **NOT** confirm the `ThreadedResolver`/native-memory hypothesis above as the actual OOM cause. Either
  (a) the hypothesis is wrong and something else drives the native growth, or (b) the fix is real but too small relative
  to other allocators (pandas/pyarrow buffers, the underlying `aiohttp` connection pool itself) to show up in this
  harness's 3-date range. **Do not claim the OOM is fixed anywhere** — this todo remains `[ ]` open. **Next step,
  unchanged in kind but now sharper**: a real `memray` run (tracks native allocations tracemalloc cannot see) across the
  same 3 dates, run on BOTH the pre-fix and post-fix code, to see whether the session-reuse fix moved the needle on
  native allocations at all — if `memray` also shows no native-heap signal correlated with request count, the
  `ThreadedResolver` hypothesis should be considered refuted and the search should widen to `pandas`/`pyarrow` (both do
  their own native buffer management) or the OS-level page-cache/malloc-arena fragmentation class of causes instead.

- **na-eligibility-audit 2026-08-01** (cefi tranche): KEEP-NA, valid — reaffirms + closes out the 2026-07-30
  infra-tranche deferral. All 4 items remain genuine investigation/design work; P1 (sports odds_api native-memory leak)
  substantially advanced 2026-07-31 (session-reuse fix shipped, RSS reduction NOT confirmed; 5th OOM recurrence
  escalated via DP_VM_STALL, VM stopped safely) but correctly stays open. Cross-confirmed via
  `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` (active planning doc) whose own P1 is explicitly blocked on
  this doc's P1 landing.
- **2026-08-02 (slot 14, data_engineering, task `sports_odds_api_scattered_multiyear_gaps-004`) — attempted the `memray`
  native-allocation profile this P1 todo's own "Next step" calls for; aborted on time-cost, then hit an unrelated
  vendor-credit exhaustion blocker before a cheaper alternative could get real signal.** `memray --native` against the
  post-session-reuse-fix code (`market-tick-data-service@6ca2d278`), same 3 dates (`2026-04-16/17/18`) the prior
  tracemalloc run used: killed cleanly by exact PID after ~9 minutes, still mid-way through the FIRST ("quiet", 0-row)
  date, which took seconds under plain tracemalloc — memray's native-stack-capture instrumentation overhead (CPU pegged
  ~93%) makes a full 3-date run disproportionately expensive for this task's budget; host memory was never at risk
  (peaked ~1.3GB of 49GB available). Pivoted to a much cheaper non-memray diagnostic (a background thread sampling
  `/proc/self/status` VmRSS + `threading.active_count()` once/sec during `download_batch()`, no instrumentation
  overhead) specifically to test whether RSS growth correlates with thread churn (the `ThreadedResolver` hypothesis)
  without memray's cost. **Before that sampler could produce a useful signal, the very first real historical-data call
  401'd** — live-verified via direct curl that the-odds-api.com account has exhausted its entire 5,000,000/month credit
  quota (`x-requests-used: 5000772`, `error_code=OUT_OF_USAGE_CREDITS` on `/v4/historical/...` specifically; the live
  `/v4/sports` endpoint still returns 200, ruling out a repeat of the July `DEACTIVATED_KEY` incident — the key itself
  is valid, the account is just out of credits, plausibly consumed by the sheer number of full-history backfill attempts
  this investigation has already burned through). **This P1 root-cause todo is now ALSO blocked on the same
  vendor-credit exhaustion as the sibling doc's P1 backfill todo** — no further real-fetch profiling (memray,
  tracemalloc, or the lightweight sampler) is possible until the operator either waits for the monthly reset or
  purchases additional credits. Retagged (see sibling doc) and escalated via `/blocked`. The `ThreadedResolver`
  hypothesis remains neither confirmed nor refuted — next resumer should re-run either the lightweight sampler
  (preferred — near-zero overhead) or a `memray --aggregate` (much smaller/faster output mode, untried this session)
  once credits are available again, rather than assuming the hypothesis from the 2026-07-31 entries above is settled.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped in the sports odds_api adapter
  (`odds_api_adapter.py`, the current active root-cause target) and `setup-data-pipeline-vm.sh` (the shared
  `mtds_chunk_loop.sh` fail-loud generator used by both incidents), replacing `launch-mtds-backfill-vm.sh` to make room
  given the doc has grown to cover a second, still-open sports/odds_api OOM investigation. The promoted
  `market-tick-data-service/scripts/profile_odds_api_backfill_memory_2026_07_31.py` profiling script no longer exists on
  disk (checked; likely deleted per the one-off-script lifecycle convention) — not added.
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, valid — all 4 open todos remain
  judgment/design/blocked investigative work into an unresolved native-memory OOM root cause across CEFI/sports MTDS
  backfills, not worker-determinable facts.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=cefi, autonomous): KEEP-NA, valid — all 4 open todos remain
  judgment/design/blocked investigative work into an unresolved native-memory OOM root cause across CEFI/sports MTDS
  backfills. Flagging for whoever next touches this doc: the `BLOCKED-CREDENTIALS` item has a 2026-08-02 operator
  purchase-decision with no later in-doc confirmation credits were actually restored — worth a live re-check rather than
  assuming still-blocked.
- **2026-08-07T14:15Z (autonomous session)** — **New data point for the P1 root-cause: first-subprocess-vs-subsequent
  survival time, from a live `mtds-backfill-odds-401-retry` run today.** This VM (single 8-month chunk,
  `2025-09-01→2026-05-08`, all Prediction-tier leagues, one fresh python subprocess per league via `mtds_chunk_loop.sh`)
  OOM-killed on 6 consecutive leagues. Precise timing: EPL (the FIRST subprocess this VM lifetime) survived **93.3
  minutes** before OOM; every subsequent league OOM'd in a **remarkably tight 6.5-8.9 minute band** (LA_LIGA 8.9,
  BUNDESLIGA 8.7, SERIE_A 6.5, LIGUE_1 8.6, EREDIVISIE 8.8). That consistency across 5 different leagues — which should
  have genuinely different real-fetch-day densities and therefore genuinely different survival times if the leak were
  purely a function of per-process real-fetch volume — argues there is ALSO a component that persists ACROSS subprocess
  launches within the same VM's lifetime, not purely within one process. Candidate mechanisms worth checking first (none
  confirmed): OS page-cache/disk-buffer pressure that isn't application-visible but still counts toward the cgroup's OOM
  accounting; a lingering child/zombie process from the prior subprocess not fully reaped before the next spawn; a
  host-level DNS resolver cache or connection-pool artifact (`market_tick_data_service`'s own `ThreadedResolver`
  hypothesis, flagged but unconfirmed in this doc's 2026-07-31 entries, would fit — if the resolver cache is a
  module-level singleton it wouldn't reset per-subprocess the way in-process object state does). Real captured data is
  NOT lost in any of this — the shard-atom write pattern is per-date via `ManifestWriter`, so each subprocess's partial
  progress before its own OOM is durable; this is a performance/cost finding, not a data-loss one. Not investigated
  further this session (out of scope for an operational monitoring tick) — logged here as fresh, specific evidence for
  whoever picks up the still-open memray/tracemalloc profiling work below.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — sole open item is the native-memory OOM root-cause investigation
  (memray/tracemalloc profiling); AWS credits confirmed cleared today, work can proceed.
- **2026-08-07T21:22Z (autonomous session)** — **Second data point: a single chunk with an anomalously high per-league
  OOM rate (10/18 = 55%), strongly correlated with real-fetch density, not span.**
  `mtds-backfill-odds-smallchunk2-20260807` (`--chunk-size 5`, full 2020-06-06→2026-08-07 odds_api range) has spent ~2h
  on chunk 18/451 (`2020-08-30→2020-09-03`) alone — verified via full `run.log` read (rule 1b: diffed actual per-league
  outcomes, not just log-line activity) that this is genuine progress, not a repeat-loop: 18 distinct leagues attempted
  (EPL→LA_LIGA→BUNDESLIGA→SERIE_A→LIGUE_1→EREDIVISIE→PRIMEIRA_LIGA→JUPILER_PRO→SUPER_LIG→SCOTTISH_PREMIERSHIP→
  GREEK_SUPER_LEAGUE→AUSTRIAN_BUNDESLIGA→SWISS_SUPER_LEAGUE→DANISH_SUPERLIGA→ELITESERIEN→EKSTRAKLASA→ALLSVENSKAN→
  BRASILEIRAO), each a genuinely fresh subprocess/date-range combo, zero identical repeats. EKSTRAKLASA fully completed
  (`Batch complete: 5 results collected`); 10 of the 18 OOM'd once each (exit=137) and were correctly marked
  `CHUNK_FAILED` + advanced to the next league (self-recovery working as designed — no data loss, no freeze). This
  chunk's 55% per-league OOM rate is far above the historical `--chunk-size 5` baseline (~4/75 chunks). Circumstantial
  support for the season-opener/real-fetch-density hypothesis: the successful/failed leagues that DID get through show
  non-trivial real `ODDS_API` payloads (e.g. 828 rows/day) rather than skip-fast dates, and 2020-08-30→2020-09-03 is a
  genuine European-football season-opener window (matches the fixture-calendar pattern flagged in the sibling doc
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`). **Not a stall** — PROGRESS.json only checkpoints at
  the whole-chunk boundary (all leagues done), so a chunk with an unusually deep/failure-prone league list can go a long
  time without advancing the visible `last_completed_date`, which is exactly what was observed (stuck at `2020-08-29`
  since 19:22:22Z while real per-league work continued underneath). Residual-gap risk worth flagging for whoever next
  re-censuses odds_api: leagues that OOM'd this pass (EPL, EREDIVISIE, PRIMEIRA_LIGA, JUPILER_PRO, SUPER_LIG,
  GREEK_SUPER_LEAGUE, SWISS_SUPER_LEAGUE, DANISH_SUPERLIGA, ELITESERIEN, ALLSVENSKAN — for this specific
  2020-08-30→2020-09-03 range) are NOT auto-retried within this run; they'll show as `attempted_failed` and need a
  follow-up narrow-range re-run to close, same pattern as the EPL 401-retry gap noted earlier in the sibling doc. No
  intervention taken — self-recovery is functioning correctly and killing/relaunching would lose the 8 completed
  leagues' progress within this chunk for no benefit.
- **2026-08-07T23:47Z — separate, lower-severity finding on the same VM: `PROGRESS.json`'s GCS upload appears to have
  stopped entirely after chunk 17, unrelated to the OOM pattern above.** `mtds-backfill-odds-smallchunk2-20260807`'s
  `PROGRESS.json` last wrote a real value at `19:22:22Z` (chunk 17's completion). Chunks 18 (22:59:42Z), 19 (23:18:02Z),
  20 (23:24:10Z), and 21 (23:30:17Z) have all since completed per `run.log`'s own `PROGRESS: chunk=N` lines — genuine,
  verified progress — but `PROGRESS.json` in GCS never picked up any of them, still reading the stale chunk-17 value
  4.5+ hours later. The VM itself is unambiguously healthy (log growing, manifest shards writing, heartbeats firing,
  chunks 19-21 each cleared in ~6 min with zero new OOMs) — this looks like the `PROGRESS.json` upload step itself broke
  or silently stopped being invoked for this specific run, not a VM hang. Not investigated further this tick
  (monitoring-only impact, not data-loss) — worth a look at `mtds_chunk_loop.sh`'s `PROGRESS.json` upload call next time
  someone touches that script, since a future session trusting `PROGRESS.json` alone (without the run.log cross-check
  this doc's rule-1b guidance already recommends) would wrongly conclude this VM has been stuck since 19:22Z.
- **na-eligibility-audit 2026-08-08** (tranche=cefi, autonomous): KEEP-NA, valid — reaffirms the 2026-08-07 verdict. In
  scope this run because two new findings landed after that marker (the 2026-08-07T21:22Z 55%-OOM-rate data point and
  the T23:47Z `PROGRESS.json` upload-stopped finding), neither changes the doc's core status. 2 open todos now: the
  original P1 native-memory root-cause investigation (GENUINE_WORK — real profiling/design work, credits confirmed
  cleared, not worker-determinable-by-fiat) and a new `[SCRIPT] P3` added this run for the `PROGRESS.json` upload bug
  (GENUINE_WORK, bounded/deterministic on its own, but does not flip the whole doc — the P1 item is still open judgment
  work, and `assigned_vm` flips at the whole-doc level). Converted the T23:47Z prose "worth a look next time" note into
  that tracked todo per CLAUDE.md's "every follow-up is a todo, never prose" rule. No archival — doc is a live,
  still-active investigation.

- [ ] [SCRIPT] P3. **Root-cause + fix `mtds_chunk_loop.sh`'s `PROGRESS.json` GCS upload call** — confirmed silently
      stopped firing after chunk 17 on `mtds-backfill-odds-smallchunk2-20260807` while `run.log`'s own
      `PROGRESS:     chunk=N` lines kept advancing normally through at least chunk 21 (2026-08-07T23:47Z finding above).
      Monitoring-only impact today (no data loss — `run.log` is the reliable cross-check per this doc's own rule-1b
      guidance), but a future session trusting `PROGRESS.json` alone would misdiagnose a healthy VM as stalled. Tracked
      as an explicit todo (`na-eligibility-audit` 2026-08-08) rather than left as a prose "worth a look next time" note.
      **Done when**: the upload call's failure mode is identified (e.g. a swallowed exception, a once-per-VM-lifetime
      guard misfiring, a stale path) and fixed, with a regression check that `PROGRESS.json` keeps advancing across ≥20
      consecutive chunks on a fresh run. Repo: deployment-service.

- [ ] [SCRIPT] P3. **Add a memory-aware pre-launch gate INSIDE `mtds_chunk_loop.sh`'s own subprocess loop — corrected
      scope, `/plan-brainstorm`'d 2026-08-10 (main, Claude Code session, operator ask).** The 2026-08-09 draft of this
      todo (below, superseded) proposed extending `odds-api-concurrency-guard.sh`/`tardis-concurrency-guard.sh` — that
      is the WRONG location: those guards run OFF the backfill VM, at launch time, on whoever invokes the launcher
      script, and only count fleet VM instances via `gcloud compute instances list`; they have no visibility into any
      given VM's own memory (the VM doesn't exist yet when the guard runs). The actual per-subprocess launch decisions
      happen inside `mtds_chunk_loop.sh`'s bash loop (the `for LEAGUE in "${CHUNK_LEAGUES[@]}"` / chunk `while` loop
      generated by `deployment-service/scripts/vm/setup-data-pipeline-vm.sh`), which runs ON the VM itself and already
      captures each subprocess's exit code for the `CHUNK_FAILED` fail-loud logging (2026-07-26 addendum above) — that
      is the correct site to extend, reading the SAME VM's own live memory state before spawning the next subprocess.
      Distinct from the P1 item below: this is a mitigation (stop launching the next subprocess into memory that's
      already too tight) that stands regardless of whether P1's root cause turns out to be the dirty-page/writeback
      backlog or pyarrow-mmap hypothesis. **Resolved design (operator-confirmed 2026-08-10)**: - **Action on low
      headroom: skip and continue** (not pause-and-poll — risks reintroducing the exact silent-hang failure mode this
      doc is about if the degradation never releases; not terminate-and-relaunch — bigger scope, needs wrapper/launcher
      changes beyond this loop). Log a new
      `CHUNK_SKIPPED_LOW_MEMORY: chunk=N/TOTAL       league=<LEAGUE|ALL> range=CS→CE mem_available_mb=<X> floor_mb=<Y> time=<ts>`
      line (same format family as `CHUNK_FAILED`) and advance to the next chunk/league without spawning — this matches
      the EXISTING `CHUNK_FAILED`-then-continue convention already used for post-crash OOMs (proactive instead of
      reactive), and the resulting gap closes via the same "attempted_failed → follow-up narrow-range re-run" pattern
      already used throughout this doc's Progress Log. - **Bundle the P1 diagnostic**: since the gate already reads
      `/proc/meminfo` before each subprocess launch, also parse and log the `Dirty:`/`Writeback:` fields alongside
      `MemAvailable` in the same line — this is the exact still-untested P1 next-step ("sample `/proc/meminfo`'s
      `Dirty:`/`Writeback:` fields alongside RSS... across a real multi-league chunk on an actual VM", § "New hypothesis
      for the 2026-08-07 cross-subprocess-persistence finding" above) and costs nothing extra to collect since the file
      is already being read. Does NOT change this todo's own done-when; gives the P1 investigation's next resumer real
      data instead of nothing. **Done when**: `mtds_chunk_loop.sh` (both the sports per-league loop and the generic
      chunk loop, same generator) reads `/proc/meminfo` (`MemAvailable`, `Dirty`, `Writeback`) immediately before
      spawning each subprocess; if `MemAvailable` is below a defined floor (start from a value with headroom under the
      observed OOM RSS ceilings in this doc — e.g. ~2-4GB on the `e2-highmem-4` 32GB machines — tune from real data once
      this has run once), it logs `CHUNK_SKIPPED_LOW_MEMORY` (with `Dirty`/`Writeback` included) and continues to the
      next iteration instead of spawning; a dry-run/test with a simulated low-`MemAvailable` fixture shows it actually
      skips rather than launches. Repo: deployment-service.

  <details><summary>Superseded 2026-08-09 draft (kept for provenance, not the current scope)</summary>

  [SCRIPT] P3. Make the odds_api backfill's own concurrency guard memory-aware, not just count/credit-based —
  `odds-api-concurrency-guard.sh` currently caps concurrency by VM/process count and vendor API credit budget only; it
  has no signal on actual host memory headroom, so the guard can green-light a launch density that later OOM-kills
  regardless of what this doc's P1 root-cause investigation finds. Raised as a design idea during the 2026-08-09 session
  (main, Claude Code) while investigating the still-open native-memory leak below, but never converted to a tracked todo
  before this — fixing that now per the "every follow-up is a todo, never prose" rule. Done when: the guard reads live
  memory headroom (e.g. `free -m` / `/proc/meminfo` `MemAvailable`) before authorizing a new chunk/subprocess launch and
  refuses (or throttles) when headroom is below a defined floor, with a test/dry-run showing it actually blocks a launch
  under simulated low-memory conditions. Repo: deployment-service.

  </details>

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — item 1 is an ongoing native-memory
  OOM root-cause investigation (session-reuse fix shipped as an efficiency win, does not confirm root cause); item 2
  flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE (bounded monitoring-bug fix) but not enough alone to flip the doc.
- **2026-08-09 (main, Claude Code session) — live re-confirmed the leak recurs today, ruled out two candidate
  explanations by code read, and surfaced a new, sharper hypothesis for the still-unexplained cross-subprocess
  persistence pattern. No code change shipped — a hypothesis is not the same as a fix, per this doc's own standing
  rule.**
  1. **Live recurrence, current code.** Relaunched `mtds-backfill-odds-smallchunk9` (`--chunk-size 5`,
     `deployment-service@5e8b82d08` — current HEAD, includes the 2026-07-31 session-reuse fix) as an unrelated
     escalation-mechanism fix verification. OOM'd again after 25 real minutes (`12:50:25Z` → `13:15:48Z`,
     `mem_pct: 93.4` at death, `reap_reason: vm_not_running`) — same signature as every prior recurrence. Confirms this
     is still live today, not something that quietly resolved.
  2. **Ruled out: incomplete session-reuse fix.** Full read of `odds_api_adapter.py` post-fix: `_fetch_all_leagues` (the
     actual historical-backfill hot path `download_batch()` calls) opens exactly ONE `_make_session()` per date (line
     ~557) and correctly threads it through `existing=session` to `_discover_fixtures` and `_run_league_fetch_loop` —
     genuinely one `TCPConnector`/`ThreadedResolver` per date, not per-request as before the fix. The 3 other bare
     `_make_session()` call sites (`fetch_sports`/`get_markets`/`get_prices`, lines 278/348/390) are LIVE-odds endpoints
     never invoked by the backfill path — irrelevant to this OOM, not a residual gap in the fix. **This means the fix's
     failure to reduce RSS (2026-07-31 Progress Log entry above) is not because it was incompletely applied** — it's
     real evidence the `ThreadedResolver`-churn hypothesis itself is wrong or too small a contributor, exactly as that
     entry already concluded, now with the "was it actually implemented right" question closed off too.
  3. **Ruled out: the already-fixed per-VM-shard-growth mechanism is NOT the current cause here.** Found a directly
     analogous, CONFIRMED-and-shipped OOM class in a sibling doc
     (`/plans/archive/issues/per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md`,
     `deployment-service@20ce4c9`): `ManifestWriter._flush_per_vm_pending` does a full read-merge-write of the ENTIRE
     existing per-VM shard on every flush, so a VM whose `VM_NAME` (and therefore per-VM shard path) stays constant for
     its whole lifetime accumulates an ever-growing shard and eventually OOMs regardless of chunking. Fixed there by
     suffixing `VM_NAME` per-chunk. **`mtds_chunk_loop.sh` already applies this exact pattern to the odds backfill** —
     `VM_NAME="${VM_NAME}-c${CHUNK_NUM}${LEAGUE_SUFFIX}"`, suffixed per chunk AND per league — so each subprocess launch
     targets its own small, fresh per-VM shard, not an accumulating one. This mechanism is structurally already
     mitigated here; it is not the explanation for the still-open recurrences.
  4. **New hypothesis for the 2026-08-07 cross-subprocess-persistence finding (first subprocess survives ~93min, every
     later one in the same VM lifetime dies in a tight 6.5-8.9min band regardless of density) — not yet empirically
     tested.** Two threads of evidence point at something kernel/OS-level, not Python-heap: (a) the original kernel OOM
     log (`CONFIRMED: real kernel OOM-kill` section above) shows `constraint=CONSTRAINT_NONE` — a GLOBAL OOM decision,
     not one scoped to this process's own cgroup/limits; (b) `mtds_chunk_loop.sh` fans out one fresh subprocess PER
     LEAGUE within a chunk (confirmed by reading the generator in
     `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` — the `for LEAGUE in "${CHUNK_LEAGUES[@]}"` loop wraps
     the `python -m market_tick_data_service` invocation), which is exactly the shape the 2026-08-07 finding describes.
     Candidate mechanism: Linux dirty-page/writeback backlog — real parquet/log writes to a persistent disk that can't
     sync back (to local disk, then GCS) as fast as they're produced would show as OS-level memory pressure invisible to
     any single process's own RSS/tracemalloc reading, would persist across subprocess launches (page cache and
     writeback queues are system-wide kernel state, not per-process), would correlate with real-data density (matches
     every density-correlated observation in this doc), and a severe enough backlog can force a genuinely global
     (`CONSTRAINT_NONE`) OOM even when reclaimable-looking cache exists, because dirty pages must be written back before
     they're reclaimable. **Checked and ruled OUT as disk-space exhaustion specifically**: every deployment-registry
     snapshot across every recurrence in this doc shows `disk_pct` in the low single digits (1.8-1.9%) right up to the
     OOM — so it's page-cache/writeback pressure in RAM, not the disk filling up, if this hypothesis is right at all.
     **Not yet tested** — needs either a live VM with `/proc/meminfo`'s `Dirty:`/ `Writeback:` fields sampled alongside
     RSS across a real multi-league chunk (the doc's existing "lightweight sampler" pattern, just add these two fields),
     or a `memray --native` run on real data (the doc's other standing next step) to see whether the native allocation
     is genuinely file-I/O/buffer-related. **Alternative/competing hypothesis, also untested**: `mem_pct`/`rss=` in the
     `RESOURCE_SAMPLE` lines appears to be the single process's OWN RSS (roughly matches `rss_MiB / total_RAM`), which
     if accurate argues AGAINST pure kernel page-cache pressure (that wouldn't attribute to one process's RSS) and FOR
     memory-mapped file pages counting toward this process's own resident set — e.g. if `pyarrow`'s parquet read/merge
     path (`ManifestWriter._flush_per_vm_pending`, ruled structurally-mitigated above but still executes once per date
     within a subprocess, up to `--chunk-size` times) uses memory-mapped I/O internally and doesn't promptly `munmap`
     between date iterations, that would also explain tracemalloc-blindness (mmap'd C-extension buffers, not Python
     objects) and real-data-density correlation, without needing a cross-process kernel mechanism at all — in which case
     the cross-subprocess "tight 6.5-8.9min band" would need a different explanation (worth checking whether ALL 5
     leagues in that comparison happened to have genuinely similar real-fetch-day density, which would undercut the
     "density-independent" framing the 2026-08-07 entry used).
  5. **Why this session didn't go further**: confirming either candidate needs live Linux kernel state (`/proc/meminfo`)
     during a real fetch — not available on this session's local macOS environment, and setting up a faithful
     Linux+real-credentials+real-network repro (Docker or a dedicated profiling VM) is a real, separate time/cost
     commitment beyond a code-level dig. Flagging both hypotheses here, evidence-ranked, rather than guessing further or
     launching another VM without checking in first.
- **2026-08-09 (slot 5, data_pipeline_failure escalation, DP_VM_STALL `DP-VM-003` on
  `mtds-backfill-odds-smallchunk10-20260809`, escalation `agt-adfeaf`) — sixth+ recurrence; NOT relaunched, runbook
  bound already exceeded before this dispatch.** Per `/codex/15-runbooks/incidents/rb_infra_relaunch.md`'s
  `≤2 relaunches/(vm-prefix, day)` bound, queried `DeploymentsRegistry` for this exact `vm_name` before acting: **3
  already-archived `failed` attempts for this same prefix earlier TODAY** (2026-08-09), all
  `SPORTS`/`mtds-backfill`/`full`, all reaped `vm_not_running`:
  - `52467378-...` started `17:21:07Z` → failed `17:40:02Z` (exit=1)
  - `b5742639-...` started `07:53:36Z` → failed `13:10:02Z` (exit=125)
  - `dd4eb45f-...` started `21:33:35Z` → failed `21:50:04Z` (exit=1) — this is the run the DP_VM_STALL alert (12m-stale
    heartbeat) actually fired against; by the time this escalation was picked up, the reaper had already terminalized it
    as `failed` and `gcloud compute instances describe` confirmed the VM itself no longer exists (self-cleaned, zero
    ongoing SPOT billing waste — no stop/delete action needed). Fetched `run.log` for the 3rd attempt (`dd4eb45f`, same
    GCS path, overwritten per-run): bootstraps cleanly on `e2-highmem-4` / `--chunk-size 5` (both standing mitigations
    already active per this doc), processes chunk 1's first 2 dates (skip + a real 828-row `EPL` fetch), RSS jumps
    `787MiB → 10,061MiB` within ~40s of the first real fetch, then the log goes silent with no Python traceback — the
    same signature this doc has documented for 5+ prior recurrences. **Did not attempt a 4th relaunch**: (a) the bound
    is already exceeded (3, not ≤2) independent of this dispatch, (b) this is the identical, still-open P1
    native-memory-leak root cause this doc has tracked since 2026-07-22 with the operational mitigation ladder (bigger
    machine → smaller chunks) already exhausted per the 2026-07-31 fifth-recurrence entry, and (c) no new fix has
    shipped since the 2026-08-09 hypothesis-only entry above that would qualify for the runbook's root-cause-diagnosed
    carve-out. Skipped the authoring-slot ping (`$AUTHORING_SLOT=dp-fleet-monitor`, not a numeric slot id per the role's
    own skip condition). No code change this session — this is a pure registry-verification + Progress Log entry,
    consistent with this doc's own precedent for a `data_pipeline_failure` one-shot escalation hitting an
    already-exhausted mitigation ladder. The P1 root-cause todo below remains the only path to a reliable full-range
    run.
- **2026-08-10 (main, Claude Code session) — ran `/plan-brainstorm` on the 2026-08-09-drafted memory-aware-guard P3 todo
  per operator ask, per this doc's own "run `/plan-brainstorm` first, don't improvise a scope" instruction. Scope
  corrected, not yet implemented.** Grep-first (skill Step 2) turned up a real architectural bug in the prior draft:
  read both `odds-api-concurrency-guard.sh` and `tardis-concurrency-guard.sh` in full — they run OFF the backfill VM
  (invoked by the launcher, before the VM exists) and gate purely on fleet VM COUNT via `gcloud compute instances list`;
  neither has, or could have, any signal on a given VM's own memory. The prior draft's "guard reads live memory headroom
  before authorizing a new chunk/subprocess launch" therefore named the wrong script. Confirmed via
  `setup-data-pipeline-vm.sh` that the actual per-subprocess spawn site is `mtds_chunk_loop.sh`'s own `for LEAGUE`/
  chunk loop, running ON the VM, already capturing exit codes for `CHUNK_FAILED`. Asked the operator 2 pointed questions
  (skill Step 3) once code-reading closed off everything answerable from the corpus: (1) gate action on low headroom —
  resolved to skip-and-continue, matching the existing `CHUNK_FAILED`-then-continue convention rather than
  pause-and-poll (hang risk) or terminate-and-relaunch (bigger scope); (2) whether to bundle the still-untested P1
  `Dirty:`/`Writeback:` diagnostic into the same `/proc/meminfo` read — resolved yes. Rewrote the P3 todo above with the
  corrected location + resolved design + a concrete done-when; superseded draft kept inline for provenance. **Not
  implemented this session** — per the original ask ("run `/plan-brainstorm` first, not improvise a scope"), this
  session's deliverable is the corrected, dispatchable scope, not the shell script change itself.
