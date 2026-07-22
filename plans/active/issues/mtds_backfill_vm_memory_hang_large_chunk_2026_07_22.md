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
