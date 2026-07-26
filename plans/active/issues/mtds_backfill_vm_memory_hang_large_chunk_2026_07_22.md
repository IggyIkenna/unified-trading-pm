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
