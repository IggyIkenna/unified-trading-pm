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

- [ ] [DATA] P2. **Wire real byte-budget admission control into the CEFI Tardis per-symbol runner** — populate
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

- [ ] [DATA] P2. **Audit every OTHER `deployment-service/scripts/vm/launch-mtds-*-backfill-vm.sh` launcher for the same
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

- [ ] [DATA] P1. **Root-cause the actual retained-memory object(s) across date iterations in the sports odds_api
      download path** (`market_tick_data_service`, the code path `--operation download --asset-group SPORTS` walks
      per-date inside one process — likely `TickDataHandler.process()`'s date loop or the `odds_api` adapter/finalizer
      holding a growing cache/buffer keyed across dates instead of per-date). A memray/tracemalloc profile across 2-3
      consecutive real-fetch days would show whether it's an unbounded cache, an un-drained event-sink buffer, or
      accumulating asyncio/aiohttp session state. This is the durable fix; the small-chunk-size mitigation above is a
      workaround, not a repair. Repo: market-tick-data-service.
- [ ] [DATA] P2. **Consider an adaptive/smaller default `--chunk-size` specifically for "recent history" chunks** (the
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
