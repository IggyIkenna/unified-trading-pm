---
doc_type: issue
title:
  "CeFi raw-tick batch capture appears HALTED since >=2026-07-21 -- Cloud Run job
  uts-prod-market-tick-data-service-cefi-t1-recon crash-looping on signal 9 (SIGKILL/OOM) since >=2026-07-23, before any
  venue download begins"
summary: >-
  Found via the /data-pipeline-reconciliation --asset-group cefi run's own Phase-0 manifest read: `capture_status` by
  `date` collapses from a steady ~1,000-1,200 captured/day baseline (through 2026-07-20) to 5 (2026-07-21) then ZERO
  captured AND zero attempted_failed for three straight days (2026-07-22/23/24) -- zero of both means no write attempt
  landed at all, not merely that attempts are failing. The corpus-wide `attempted_at` maximum across the full
  9,045,162-row cefi manifest is 2026-07-24T01:31:59Z, ~23h stale at probe time. Followed up with read-only `gcloud
  scheduler/run/logging` checks against central-element-323112: the primary cefi triggers (0600/0900 UTC crons) are
  ENABLED and firing on schedule, but the Cloud Run Job they invoke (`uts-prod-market-tick-data-service-cefi-t1-recon`,
  4 CPU / 8Gi memory) logs "Container terminated on signal 9" (SIGKILL, consistent with OOM) within ~10-40s of every
  execution since at least 2026-07-23, before any per-venue download work begins -- confirmed on both the 06:00 and
  09:00 UTC executions for 07-23 and 07-24. The 07-21/22 failures show a different, earlier-stage signature (a single
  bare ERROR log with no INFO bootstrap output at all) that was NOT confirmed to be the same regression. This is NOT
  documented anywhere in the actively-worked cefi migration issue docs reviewed this run
  (`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` discusses OOM kills of a SEPARATE manifest-dedup
  script on a shared operator dev host and, separately, on a dedicated e2-standard-8 VM -- both explicitly different
  infrastructure from this isolated, 8Gi-limited Cloud Run Job). Filed per the workspace's data-pipeline-correctness
  HARD RULE (a live production capture outage is a BIG finding requiring operator notification, which this run also did
  in its final chat response).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, capture-halt, oom, cloud-run, data-pipeline-correctness, manifest, crash-loop]
related:
  [
    /plans/audit/results/data_pipeline_reconciliation_cefi_2026_07_24.md,
    /plans/audit/results/data_pipeline_reconciliation_cefi_2026_07_20.md,
    /plans/active/issues/cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md,
    /plans/active/issues/cefi_high_attempted_failed_batch_cluster_2026_07_23.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: 2026-07-24
parent_epic: cefi_master
priority: P0
source: >-
  /data-pipeline-reconciliation --asset-group cefi (raw-tick layer) dispatched sub-agent run, 2026-07-24/25 -- an
  anomaly this run's own Phase-0 manifest read surfaced (not something it was dispatched to look for), followed up with
  a read-only, targeted GCP infra check per the skill's own "grep-then-READ, not grep-then-conclude" discipline.
resolved_by:
locked_by:
assigned_vm: planning
code_refs:
  [
    market-tick-data-service (op=download mode=batch handler,
    service unclear which module -- not identified this run),
    deployment-service/scripts/vm/ (not applicable -- this is a Cloud Run Job,
    not a VM),
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# CeFi raw-tick batch capture appears HALTED since >=2026-07-21 -- Cloud Run job crash-looping on signal 9

## What is measured, and how confident each part is

### (a) HIGH CONFIDENCE -- the manifest shows the estate has stopped growing

Full-corpus cefi manifest read (`read_availability_index`, filters=[("asset_group","==","cefi")], 9,045,162 rows,
fully-consolidated index, 28.6s old at read time -- not a stale fallback):

| date       | attempted_failed | captured | empty_confirmed | expected_unattempted |
| ---------- | ---------------- | -------- | --------------- | -------------------- |
| 2026-07-18 | 127              | 1,204    | 1,765           | 16,606               |
| 2026-07-19 | 112              | 1,203    | 1,789           | 16,581               |
| 2026-07-20 | 118              | 1,227    | 1,745           | 16,571               |
| 2026-07-21 | **0**            | **5**    | 1,193           | 17,481               |
| 2026-07-22 | **0**            | **0**    | 1,182           | 17,484               |
| 2026-07-23 | **0**            | **0**    | 1,182           | 17,484               |
| 2026-07-24 | **0**            | **0**    | 1,182           | 17,484               |

Corpus-wide `attempted_at` maximum (across all 8,901,202 non-blank values): **`2026-07-24T01:31:59.195992+00:00`** --
~23h stale at probe time (`~2026-07-25T00:41Z`). `_index/per_vm/` (the per-VM staging area a healthy capture writer
continuously deposits shards into for the consolidator to merge) contains exactly **1 file**, and that file
(`_legacy_seed.parquet`) is the Surface-C dedup migration script's own output artifact, not a live writer's shard.

### (b) HIGH CONFIDENCE -- the crons are enabled and firing, so the trigger layer is not the problem

```
gcloud scheduler jobs list --project=central-element-323112 --location=asia-northeast1
```

`uts-prod-market-tick-data-service-cefi-t1-schedule` (`0 6 * * *`, ENABLED, lastAttemptTime=2026-07-24T06:00:01Z) and
`market-tick-daily-trigger` (`0 9 * * *`, ENABLED, lastAttemptTime=2026-07-24T09:00:06Z) both fired on schedule through
2026-07-24. (A differently-named job, `market-tick-cefi-daily-download`, is `PAUSED` since `2026-07-16T07:46:21Z` --
over a week before the cliff started; almost certainly a pre-existing/superseded job, not implicated -- worth a 5-minute
check to confirm it's genuinely dead code, but not the cause of THIS incident.)

### (c) HIGH CONFIDENCE -- the invoked Cloud Run Job is crash-looping on apparent OOM, at least since 2026-07-23

```
gcloud run jobs executions list --job=uts-prod-market-tick-data-service-cefi-t1-recon --region=asia-northeast1
```

`FAILED_COUNT=1` on every execution from at least 2026-07-15 through 2026-07-24 (20 checked) -- **this specific count is
NOT new** and by itself does not explain the cliff (captures were healthy through 07-20 despite it; treat it as a
chronic, non-blocking partial failure baseline, not the smoking gun).

```
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-market-tick-data-service-cefi-t1-recon"'
```

For 2026-07-24T09:00-09:04Z and 2026-07-24T06:00-06:03Z, and again for 2026-07-23 at both trigger times: the container
logs ~15 lines of normal bootstrap --

```
ServiceRuntime: op=download mode=batch provider=gcp env=production data=real testnet=mainnet dry_run=False
ApiKeyReloader started: 24 venues, refresh every 300s
API keys validated for 3 data source(s): ['aster', 'hyperliquid', 'tardis']
```

-- and then **`WARNING: Container terminated on signal 9.`**, TWICE per execution window (a retry also gets killed),
**before any per-venue download work begins** (no log line after `API keys validated` ever appears). Signal 9 = SIGKILL,
consistent with an OOM kill. Configured resources (`gcloud run jobs describe`): **4 CPU / 8Gi memory**.

### (d) LOWER CONFIDENCE -- whether 07-21/07-22 share this exact cause

Searched explicitly for `signal 9` in the 2026-07-20/21/22 logs for this job: **not found**. Those days' failures show
only a single bare `ERROR`-severity log entry per execution with **no INFO bootstrap output preceding it at all** --
qualitatively different from 07-23/24's ~15-line-then-OOM pattern. This could mean: (i) an even earlier-stage failure
(e.g. image pull / cold-start) that predates the in-process OOM regression, (ii) a logging/routing gap that simply
didn't capture the INFO lines for those days, or (iii) a genuinely different, unrelated failure mode. **Not resolved
this run** -- whoever picks this up should pull the full log payload (not just severity>=WARNING) for 07-21 and 07-22
specifically.

## What is NOT established (do not assume)

1. **The code/config change that pushed this job's memory footprint past 8Gi**, and when it landed. Would need a
   `market-tick-data-service` commit-log / deploy-history read around 07-21..07-23 -- not done this run (out of the
   reconciliation skill's scope; this issue doc is the handoff).
2. **Whether this is causally related to** the Surface-C manifest-dedup script's OOMs documented in
   `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 6 -- that doc's OOMs happened on (i) a
   **shared operator dev host** (`earlyoom`, SIGTERM/143) and (ii) a **dedicated e2-standard-8 VM** (SIGKILL/137) --
   both explicitly DIFFERENT infrastructure from this **isolated Cloud Run Job's own container memory limit**. They may
   be coincidental (same general week of heavy cefi migration activity) rather than one root cause. Worth checking
   whether the two share a common code path (e.g. both import the same heavy pandas/canonicalization module at startup)
   before assuming either way.
3. Whether `market-tick-cefi-daily-download`'s week-old PAUSE (item (b) above) is dead/superseded code or a second,
   independent gap.

## Why this is filed as a BIG finding, not folded into an existing doc

Per `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` and `CLAUDE.md`'s findings-triage rule: a data-correctness finding
outside every currently-open plan's stated scope goes to `plans/active/issues/<slug>_<date>.md`, and a **big finding**
(data-correctness, live production) additionally requires operator notification in-chat. This is a live capture OUTAGE,
categorically different from the canonicalisation/migration-shape work the currently-open cefi docs
(`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`,
`cefi_consolidated_closeout_aggregated_sources_2026_07_24.md`) are tracking -- none of those docs mention this Cloud Run
job or its crash-loop. Every day this continues is a permanent gap in the historical record for that day's
live/near-real-time capture window (a later backfill can fill `expected_unattempted`/`attempted_failed` cells
retroactively for BATCH-sourced data, but not for anything that was only ever available live/near-real-time).

## Recommended next steps (not executed this run -- read-only reconciliation)

1. Pull full (not severity-filtered) Cloud Logging output for the 2026-07-21 and 2026-07-22 executions of
   `uts-prod-market-tick-data-service-cefi-t1-recon` to determine if they share the signal-9 OOM pattern or are a
   distinct, earlier failure.
2. Identify the `market-tick-data-service` deploy/commit that shipped around 2026-07-21..23 and check for anything that
   would increase this job's steady-state or peak memory (new import, larger in-memory universe/catalogue load,
   accidental `columns=None` full-schema read analogous to the dedup script's own documented OOM cause).
3. Either raise the Cloud Run Job's memory allocation (mirroring the dedup-VM precedent's "bump to a bigger
   machine/allocation" fix) as an immediate mitigation, or fix the underlying memory growth -- operator's call which
   comes first.
4. Once fixed, verify recovery the same way this issue found the problem: `capture_status` by `date` should show
   `captured` counts return to the ~1,000-1,200/day baseline, and `attempted_at` max should advance past
   `2026-07-24T01:31:59Z`.
5. Confirm whether `market-tick-cefi-daily-download` (PAUSED since 2026-07-16) is dead code; if so, consider removing it
   to reduce future investigation noise.

## Follow-up investigation + immediate mitigation (2026-07-25, `/autonomous` continuation session)

**Root-cause hypothesis (not yet 100% confirmed, but strong circumstantial fit).** `market-tick-data-service@a6e974b6`
(2026-07-20T09:27, one day before the capture cliff began) changed `HyperliquidS3Downloader` (hyperliquid + aster are 2
of this job's 3 active data sources, confirmed from its own bootstrap log) from a per-instrument, per-day trades fetch
to a "parse-once-per-day" cache: it now (a) fetches all 24 hourly S3 objects for a day CONCURRENTLY via
`ThreadPoolExecutor(max_workers=12)` and materializes all 24 decompressed hour-texts in one Python list before parsing
any of them, then (b) parses and holds EVERY coin's full-day trades in memory
(`self._trades_cache: dict[coin, list[...]]`) instead of just the one coin previously being fetched. The intent (per the
commit message) was fixing a 165x-redundant re-fetch that made full-universe BACKFILLS take weeks — a real problem for
that use case — but the same code path also now runs for this job's routine twice-daily incremental capture, where the
old per-coin behavior was never the bottleneck it solved for. This is a plausible, well-motivated perf-tradeoff
regression, not a code defect per se; it was not caught because nobody load-tested this job's specific memory profile
against the new caching shape before it shipped. **Not proven** — the code was read, not profiled; a proper root-cause
confirmation would need a memory profile of an actual execution, which this session did not run (see the
immediate-mitigation choice below for why).

**Immediate mitigation applied (2026-07-25T01:3xZ), not a permanent fix:**

```
gcloud run jobs update uts-prod-market-tick-data-service-cefi-t1-recon --region=asia-northeast1 \
  --project=central-element-323112 --memory=16Gi   # was 8Gi
gcloud run jobs execute uts-prod-market-tick-data-service-cefi-t1-recon --region=asia-northeast1 \
  --project=central-element-323112 --async          # manual test execution, not waiting for the 06:00/09:00 UTC cron
```

**Why memory-bump over a code fix, given the time pressure:** every day of continued outage is permanent data loss
(live/near-real-time capture cannot be backfilled after the fact); a memory-limit change is a pure infra config edit
with zero code-regression risk and is trivially reversible (`--memory=8Gi` reverts it), whereas a rushed code change to
`hyperliquid_s3.py` under time pressure risks introducing a NEW regression into a file 3 concurrent sessions' worth of
cefi migration work already touches this week. The 165x-speedup code itself is not reverted — it is a legitimate,
valuable fix for backfills — bumping the container's ceiling lets it coexist with this job's memory profile without
sacrificing that win. A proper permanent fix (bound the day-cache to only the currently-needed coin, or stream the 24
hours instead of materializing all of them before parsing) is a real follow-up, tracked as its own todo below — not
attempted here.

**Verification: CONFIRMED RECOVERED (2026-07-25T01:44:49Z).** The manual test execution
(`uts-prod-market-tick-data-service-cefi-t1-recon-mncmq`) ran for the full 10m2.49s and completed with
`status.conditions[type=Completed].status=True`, `succeededCount=1` — versus the prior pattern of dying within 10-40s on
every execution since 07-23. Direct log evidence (`gcloud logging read`, full transcript in this run's scratchpad):

- The job got past the exact point it previously died (`API keys validated for 3 data source(s)`), loaded the full
  429,129-row cefi catalogue, ran pre-flight checks across all 24 venues, and began real per-symbol Tardis streaming
  downloads (bitfinex-derivatives book_snapshot_5/derivative_ticker/trades, tens of thousands of rows per symbol).
- Real parquet shards were written to the canonical path and confirmed via
  `StreamingParquetWriter: uploaded market-data-tick-cefi-prd-.../raw_tick_data/by_date/day=2026-07-24/.../ BITFINEX-FUTURES:PERPETUAL:APE-USDT@LIN.parquet (27887 rows, ...)`
  (dozens of such lines, all real symbols, all 20K+ row shards) — this is genuine captured data, not a dry-run or a log
  artifact.
- **`peak_rss=8646.5MB` is logged directly by the service's own resource profiler** — this is MEASURED (not
  code-read-inferred) evidence that this exact run's peak memory usage (8,646.5 MiB) would NOT have fit in the OLD 8Gi
  (8,192 MiB) container, and DOES fit in the new 16Gi one. **This confirms "insufficient memory" as the proximate cause
  with measured evidence, not just a plausible hypothesis** — though it does not, by itself, isolate WHICH code path
  (the HyperLiquid day-cache vs. something else, e.g. the 429K-row catalogue load, or normal per-venue fan-out at this
  job's current universe size) is the dominant contributor; that attribution remains the hypothesis stated above.
- **Manifest confirms real capture, with the normal consolidation lag**: `_index/per_vm/` shows 6 fresh per-VM shard
  files timestamped 2026-07-25T01:40:37Z through 01:44:39Z (during/immediately after this execution) — the live writer's
  own output, not the stale dedup-migration artifact seen before. The consolidated `availability_index.parquet` read
  still shows 0 `captured` rows for `date=2026-07-24` because the periodic consolidator has not run again since this
  execution finished (routine, expected lag — not a new problem); it will pick these up on its next pass.
- A pre-existing, already-tracked issue class fired during the run and did NOT block progress:
  `Tardis HTTP 403 code=274 concurrent-IP-lock` on a couple of in-flight keys (matches
  `tardis_concurrent_ip_lockout_2026_07_12.md` / `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s own
  diagnosis, not new). One unrelated 404 on a `BINANCE-FUTURES` instrument-availability lookup, isolated per-shard, did
  not crash the run.

**Bottom line: the live production capture outage is RESOLVED as of this execution.** The regular 06:00/09:00 UTC crons
will now run against the 16Gi limit going forward. The underlying root-cause attribution (which specific code path
drives the ~8.6GB peak) and a permanent code-level fix remain open follow-ups, not blockers to capture resuming.

## Dominant-contributor isolation + permanent fix (2026-07-26, slot-14)

**The 16Gi bump did NOT fully resolve the outage — the job is still crash-looping.** Pulled the real
`gcloud run jobs executions list` history for `uts-prod-market-tick-data-service-cefi-t1-recon`: the 2026-07-25 06:00
and 09:00 UTC scheduled executions (`v26b6`, `7lx79`) both show `status.conditions[type=Completed].status=False`,
`retriedCount=1`, and (via `executions describe`) the terminal message **"Task ... failed with exit code: 0 and message:
The configured memory limit was reached."** — i.e. still OOM-killed at 16Gi.

**Measured evidence isolates the contributor — it is NEITHER of the two originally-hypothesized candidates.** Full (not
severity-filtered) Cloud Logging read of all 4 real attempts (both retries × both 06:00/09:00 executions):

- Every single attempt hangs with **ZERO further log output** immediately after issuing
  `TardisAdapter: bulk download okex-options/options_chain using grouped 'OPTIONS' symbol` /
  `Tardis streaming request: exchange=okex-options, symbol=OPTIONS, data_type=options_chain -> /tmp/tmp*.parquet` — for
  **~13-14 minutes**, before `Container terminated on signal 9.` Reproduced identically in all 4/4 attempts checked
  (06:00 attempt 1 @ 06:02:16, retry @ 06:17:23; 09:00 attempt 1 @ 09:02:05, retry @ 09:16:17).
- **HyperLiquid's per-day trades cache did NOT run in any of these executions** —
  `Pre-flight: venue=HYPERLIQUID ... fully covered, skipping` fires BEFORE OKX-options is reached every time, so
  `HyperliquidS3Downloader._trades_cache` is conclusively ruled out as the cause of THIS recurring OOM (it was the right
  code-read hypothesis for the ORIGINAL 07-23/24 die-within-10-40s signature, but that is a different failure mode than
  this one).
- The service's own `ResourceProfiler` (`RESOURCE_SAMPLE` log line, backed by `psutil.Process().memory_info().rss` —
  this process's own heap, which WOULD show the 429K-row `CeFiCatalogReader` catalogue DataFrame and any HL cache
  growth) stayed **flat at ~4.7-4.8GB for the entire ~13min hang**, ruling out per-venue-fan-out pandas heap growth and
  the one-time catalogue load (which happens once at the start, ~4.3GB, and does not grow further) as the ONGOING
  driver. Meanwhile `psutil.virtual_memory().percent` (host-level, includes page cache) and local disk usage
  (`disk=/tmp:X%`) climbed together in lockstep from ~37% to ~100% over the same window — consistent with an unbounded
  single-request download/decompress to local disk with no size or time cap, not a Python-heap leak.
- **Conclusion: the dominant, measured contributor is the OKX-options grouped-symbol Tardis bulk `options_chain`
  download** (`TardisAdapter._download_bulk` → `download_csv_streaming`, `tardis_bulk_download.py`) — either a genuinely
  oversized file for this exchange/day or an unbounded stream, with no total-size or wall-clock cap, so it runs until
  the CONTAINER's memory ceiling is hit regardless of what that ceiling is (this is why bumping 8Gi→16Gi only delayed,
  not fixed, the failure).

**Fix shipped**: wrapped the bulk chain download in `download_batch()` (`tardis_batch_download.py`) with
`asyncio.wait_for(..., timeout=300s)`. A timeout raises `TimeoutError`, which the EXISTING shard-level failure isolation
(`fetch_tick_data_for_venue` in `market-tick-data-service/market_tick_data_service/engine/orchestrator/ __init__.py`,
`except (OSError, ConnectionError, TimeoutError)`) already catches and records as a retryable failed shard — so a
runaway bulk download now fails fast and isolated (this one venue/data_type marked `attempted_failed`, retriable next
run) instead of hanging the whole job for ~13min until Cloud Run's OOM killer intervenes.
`market-tick-data-service@31958a05`. `quality-gates.sh` green on the committed HEAD (sentinel-verified), shipped via
quickmerge.

**Not yet done (follow-up, not blocking this todo's close)**: confirm on the NEXT scheduled 06:00/09:00 UTC execution
that the job now completes (or fails ONLY the OKX-options shard, isolated) rather than crash-looping; if 300s proves too
tight for a legitimately large OKX-options day, the constant (`_BULK_CHAIN_DOWNLOAD_TIMEOUT_SEC` in
`tardis_batch_download.py`) is a one-line tune. Whether the OKX-options download is oversized vs. simply
unbounded/hanging (no total-size logging exists yet) is unresolved — a future pass could add byte-count logging to the
streaming download to distinguish "genuinely huge legitimate file" from "runaway/never-terminating stream".

### Todos

- [x] ✅ [BACKEND] P1. Confirm (via a memory profile / Cloud Monitoring container-memory graph of an actual execution,
      not just code-reading) whether the OOM's proximate cause is insufficient memory — **CONFIRMED via the service's
      own `peak_rss=8646.5MB` resource-profiler log line, 2026-07-25T01:44Z execution** (exceeds the old 8Gi/8192MiB
      limit, fits the new 16Gi). **NOT yet isolated**: whether `market-tick-data-service@a6e974b6`'s HyperLiquid
      day-cache specifically is the dominant contributor vs. other factors (catalogue load, normal fan-out growth) — see
      the next todo.
- [x] ✅ [BACKEND] P2. **DONE 2026-07-26 (slot-14).** Isolated via a real-execution log profile (4/4 reproductions, see
      "Dominant-contributor isolation" section above): NEITHER HyperLiquid day-cache (never ran — HL was skipped, fully
      covered, in every hung execution) NOR the one-time catalogue load (flat RSS, one-time cost) is the driver. The
      measured dominant contributor is the OKX-options grouped-symbol Tardis bulk `options_chain` download, which has no
      total-size/wall-clock cap and runs until the container's memory ceiling is hit. Bounded it with
      `asyncio.wait_for(300s)` in `download_batch()` (`tardis_batch_download.py`), routing a timeout into the existing
      shard-level failure isolation instead of hanging the whole job. `market-tick-data-service@31958a05`,
      `quality-gates.sh` green, shipped via quickmerge.
- [ ] [OPERATOR] P2. Decide whether to keep the Cloud Run job at 16Gi permanently (small ongoing cost increase) once the
      root cause is confirmed/fixed, or revert to 8Gi after a code fix lands.
- [ ] [DATA] P2. Once the regular 06:00/09:00 UTC crons have run a few times on the new 16Gi limit, re-verify
      `capture_status` by `date` returns to the ~1,000-1,200/day baseline (this session only confirmed ONE manual
      execution recovered; the steady-state pattern across multiple scheduled runs is not yet observed).
