---
doc_type: issue
title:
  "MTDS CEFI backfill VM hangs at ~85-86% memory when a single chunk spans a large date range (250-day default, and even
  a 7-day test range)"
summary: >-
  Launching a CEFI Tardis backfill via `launch-mtds-backfill-vm.sh` (default `--chunk-days 250`) reproduced TWICE: the
  VM's `market_tick_data_service --operation download` process makes real progress for a few seconds, then a
  `RESOURCE_SAMPLE` log line shows memory jumping to ~86% (12.7GB rss on an e2-standard-4, 16GB RAM) — right at the
  `ResourceProfiler`'s own configured `mem_crit=85.0%` threshold — and then goes completely silent: no more log lines,
  no more heartbeats, no more GCS log uploads, serial console silent, SSH unreachable, no GCP host-error or preemption
  event. A SHORTER 1-week test range hit the same "stuck right after day 1" symptom (not confirmed at the time to be
  memory-correlated, but the pattern — works briefly, then goes fully silent with no recovery — is identical). Both
  times the VM had to be manually stopped; nothing recovered on its own within the observation window (8-15+ minutes
  each).
status: open
nature: issue
asset_group: [cefi, meta]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer]
tags: [backfill, oom, memory, tardis, cefi, reliability, vm-hang, resource-profiler]
related: [lst_rate_honest_coverage_2026_07_21]
created: 2026-07-22
priority: P1
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

## What I did NOT do

- Did not dig into `market_tick_data_service`'s download/streaming code to find the exact root cause (could be an
  unbounded in-memory accumulation across all (venue, symbol) combinations before writing, a `pandas.concat` growing
  unbounded, a retry loop holding references, or something in the `ResourceProfiler`/watchdog itself deadlocking rather
  than the actual downloader) — that's real debugging work for whoever picks this up, not something I could responsibly
  rush given how much else was in flight this session.
- Did not test whether a MUCH smaller `--chunk-days` (e.g. 1 or 7) avoids the hang entirely by keeping each chunk's
  memory footprint small AND letting each chunk be a fresh process (memory resets between bash-loop iterations) — this
  is my planned workaround for my own backfill (tracked in the LST plan), but I have not yet confirmed it avoids the
  hang; if it does, that's a strong hint the bug is in per-chunk memory accumulation specifically, not a leak that
  persists cross-process.

## Suggested next steps (not done here)

1. Reproduce with `--chunk-days 1` for the same instrument/venue/date scope and confirm whether the hang recurs. If it
   doesn't, that isolates the bug to "too much data in one chunk" rather than a cross-process leak.
2. If it does recur even at `--chunk-days 1`, the bug is likely in a single day's worth of data for these specific
   symbols (worth checking if any of the 9 symbols/venues have unusually high trade volume that could blow up a single
   day's in-memory frame).
3. Either way: the "Memory watchdog" apparently doesn't actually recover/fail-loud when `mem_crit` triggers — that
   silent-hang behavior is worth fixing on its own regardless of the download-side root cause, since it turns an
   otherwise-recoverable OOM condition into a fully-silent, unmonitorable-except-by-external-log-staleness hang.

## Evidence

- VM names: `mtds-backfill-cefi-1` (both attempts reused the default auto-derived name; deleted after each hang).
- GCS log Update-time freeze confirmed via `gsutil stat`.
- Serial console silence confirmed via `gcloud compute instances get-serial-port-output --start=<offset>`.
- Cloud Logging confirmed no host-level events via
  `gcloud logging read "resource.type=gce_instance AND resource.labels.instance_id=..."`.
- Full run.log excerpts for both attempts are in the LST plan's Progress Log
  (`plans/active/lst_rate_honest_coverage_2026_07_21.md` Phase 5, 2026-07-22 entries).
