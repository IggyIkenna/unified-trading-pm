---
doc_type: issue
title:
  Sports manifest consolidator crash-looping (DuckDB merge) + read_availability_index silently returns 0 rows while
  stale
summary: >-
  uts-prod-manifest-consolidator-instruments-sports has been crash-looping (exit code 1, truncated traceback at
  manifest_consolidator.py line 587 _duckdb_consolidate_and_write, consistent with an OOM-kill) for 15+ minutes as of
  2026-07-12 ~07h46 UTC -- the consolidated availability_index.parquet for instruments-store-sports-prd-* has not
  advanced past 2026-07-12T07:30:46Z. Separately and more urgently, read_availability_index() for this bucket is
  currently returning an EMPTY (0-row) DataFrame with no error/warning, while a raw gcsfs read of the same blob confirms
  4,914,272 real rows exist -- a silent-placeholder violation that could cause any consumer calling this function right
  now to make wrong decisions (e.g. a backfill VM believing nothing has been captured).
status: open
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, market-tick-data-service]
scope: [engineer, admin]
tags: [infrastructure, manifest-consolidator, sports, duckdb, oom, silent-placeholder, data-correctness]
related:
  [
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-12
parent_epic: infrastructure_master
priority: P0
source: [slot-11, sports_p2_history_reference_and_odds_2015_to_present-002]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Sports manifest consolidator crash-looping + silent empty read

## What I found

While re-verifying item #6 of `sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` (the cross-source
zero-missing gate), I ran two local force-refetch closer scripts (weather/SFI/transfermarkt blank-reason residual — see
that plan's Progress Log for the correctness fix) that wrote many per-VM manifest shards in quick succession against
`instruments-store-sports-prd-central-element-323112`, concurrently with slot-6's already-running
`footystats_residual_closer_2026_07_12.py` (also writing shards heavily). Partway through my second TM closer run I
started hitting `ManifestConsolidatorStaleError` on nearly every date.

**Consolidator health check** (`gcsfs` blob-metadata read of `_index/availability_index.parquet`):

- 2026-07-12T07:03:12Z — fresh (age 0.4s)
- 2026-07-12T07:29:28Z — fresh (age 76s) — briefly recovered after an earlier ~2min blip
- 2026-07-12T07:46:xx UTC (this writing) — blob `updated` timestamp STILL `2026-07-12T07:30:46.756Z`, age ~927s (15.5
  min) and climbing. Not recovering.

**Cloud Run job status** (`uts-prod-manifest-consolidator-instruments-sports`, region `asia-northeast1`): 5 consecutive
execution failures observed, one per minute (the job's own schedule), ALL exit code 1:

| execution | start (UTC) | completion (UTC)        | result |
| --------- | ----------- | ----------------------- | ------ |
| rjlp7     | 07:39:05    | 07:40:21                | FAILED |
| 2mdk8     | 07:40:05    | 07:41:31                | FAILED |
| c6dhn     | 07:41:05    | 07:42:23                | FAILED |
| rbxxz     | 07:42:05    | 07:43:32                | FAILED |
| 6vb5p     | 07:43:05    | (running at check time) | —      |

Cloud Logging
(`resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-manifest-consolidator-instruments-sports"`) shows
the SAME truncated traceback on every failed execution:

```
Traceback (most recent call last):
  File "/app/unified_trading_library/manifest_consolidator.py", line 587, in consolidate
    merge_result = _duckdb_consolidate_and_write(
```

The traceback is cut off mid-frame — no exception class/message ever reaches the log, immediately followed by
`Container called exit(1)`. This shape (a partial stderr flush with the process dying mid-traceback) is consistent with
an OOM-kill inside the DuckDB merge, not a normal Python exception (which would print through to the final
`ExceptionType: message` line). The job's Cloud Run spec (visible via `executions describe`) allocates 4 CPU / 16Gi
memory — plausible to exceed under an unusually high concurrent per-VM shard count (my 2 closer runs + slot-6's
footystats closer were all writing frequent shards to the same bucket in the same window). NOT independently confirmed
via Cloud Monitoring memory metrics — flagging as the most likely hypothesis, not a certainty.

**Separate, more urgent finding — silent empty read**: while the consolidator was down, I called
`read_availability_index('instruments-store-sports-prd-central-element-323112')` from a FRESH python process (no cache
carried over) and got `len(df) == 0` — repeatable across at least 3 independent fresh-process calls, with the FULL
37-column schema (not a schema mismatch, genuinely zero rows). A raw `gcsfs` read of the exact same blob path at the
same time, bypassing `read_availability_index` entirely, correctly returned 4,914,272 rows. Per the function's own
docstring/exception path (`_read_consolidated_if_fresh` → raises `ManifestConsolidatorStaleError` when stale AND per-VM
shards exist, refusing "to fall back to the per-VM shard merge (can OOM on large buckets)"), this looks like an
UNHANDLED case in the read path is returning an empty DataFrame instead of either (a) raising the same loud
`ManifestConsolidatorStaleError`, or (b) successfully falling back to a genuine per-VM merge. I did not have time in
this session to isolate the exact branch (`_read_and_merge_per_vm_shards` returning `None`/empty un-guarded, or a
`_CANONICAL_CACHE` poisoning path) — see todo #3 below.

## Why it matters

- Any consumer of `read_availability_index` for this bucket during the outage window silently sees "nothing has been
  captured" instead of a loud failure — the exact "silent placeholder" anti-pattern the workspace hard rules ban
  (`codex/02-data/honest-absence-downstream-handling.md`). A backfill VM or gate-check reading this during the window
  could conclude a 100% gap and trigger unnecessary re-fetches, or a downstream service could report false
  zero-coverage.
- The consolidator crash-looping for 15+ minutes (and counting) means EVERY in-flight sports data_engineering task right
  now (including slot-6's footystats residual closer, still running) is working against an increasingly stale canonical
  index — my own two TM closer runs each lost several dates to the exact same `ManifestConsolidatorStaleError` crash
  mid-run, requiring a second pass to recover.
- This directly blocks `sports_p2_history_reference_and_odds_2015_to_present` item #6 (this issue's source task) from
  reaching a trustworthy full-gate verification: any "pending_fetch==0" claim made while the consolidator is unhealthy
  is unverifiable.

## Recommended decision

1. **Immediate**: someone with GCP access should check whether `uts-prod-manifest-consolidator-instruments-sports` has
   recovered
   (`gcloud run jobs executions list --job=uts-prod-manifest-consolidator-instruments-sports --project=central-element-323112 --region=asia-northeast1 --limit=3`,
   and blob mtime via `gcsfs.GCSFileSystem().info(...)`); if still crash-looping, check Cloud Monitoring
   memory-utilization for the job to confirm/refute the OOM hypothesis, and consider a memory bump (16Gi → 24-32Gi) or
   throttling concurrent per-VM-shard writers as a mitigation.
2. Root-cause `read_availability_index`'s silent-empty-on-stale-plus-no-fallback path in
   `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py` (`_read_and_merge_per_vm_shards` /
   the branch after `_read_consolidated_if_fresh` returns `None`) — it should NEVER return an empty DataFrame silently;
   either raise `ManifestConsolidatorStaleError` (matching the documented contract) or genuinely merge the per-VM
   shards.
3. Re-verify `sports_p2_history_reference_and_odds_2015_to_present` item #6 only AFTER the consolidator has been
   confirmed healthy for a sustained window (no crash-looping) — see that plan's own Progress Log for current per-source
   `pending_fetch` counts as of this session.

## Todos

- [ ] [INFRA] P0. Confirm current health of `uts-prod-manifest-consolidator-instruments-sports` (Cloud Run job,
      `market-tick-data-service` image) — if still crash-looping, check Cloud Monitoring memory metrics for the job
      during the 07:35-07:46 UTC window on 2026-07-12 to confirm/refute the OOM hypothesis; bump memory limit or add
      shard-count throttling if confirmed. (repo: market-tick-data-service / deployment infra)
- [x] ✅ [SCRIPT] P0. Root-cause + fix the silent-empty-read path in `read_availability_index`
      (`unified-trading-library/unified_trading_library/manifest_writer/_read_index.py`) so a stale-consolidator +
      failed/empty per-VM-merge case always raises `ManifestConsolidatorStaleError` (or another loud, typed error)
      instead of returning `len(df)==0` silently. Add a regression test simulating stale-consolidated + unreadable
      per-VM shards. (repo: unified-trading-library). **DONE 2026-07-12 (slot-3)** — `unified-trading-library@b5ab0c01`.
      Root cause: `_read_and_merge_per_vm_shards` collapses "no per-VM shards exist at all" and "shards exist but every
      single one failed to list/download/parse" into the same `None` return; the caller (`read_availability_index` /
      `_read_availability_index_slim`) then falls through the self-shard fallback to a silent `return _empty` when the
      self-shard is also absent — exactly reproducing the production incident (stale consolidator + real per-VM shards
      from other VMs + this VM having no self-shard → 0 rows returned while the raw blob had 4.9M). Fix: extracted the
      shared "stale consolidated" branch into a new `_read_slow_path()` helper that reuses the already-computed
      `shards_exist` flag (from `_per_vm_shards_exist`) as the authoritative signal — when shards are KNOWN to exist but
      both the merge and self-shard read come back empty, raises `ManifestConsolidatorStaleError` via a new
      `_raise_shards_exist_but_unreadable()` helper instead of silently returning empty; a genuinely-empty bucket
      (`shards_exist=False`) still legitimately returns empty, unchanged. The extraction also fixed a `ruff C901`
      complexity violation the inline fix first introduced (`read_availability_index` was 27 > 26) and de-duplicated the
      same branch between the full and slim read paths. 2 new regression tests in
      `tests/unit/test_manifest_writer_per_vm.py` (`test_reader_raises_when_shards_exist_but_all_unreadable` — proven to
      fail on pre-fix code via a `git stash` round-trip (`DID NOT RAISE`), matching the workspace's regression-test bar
      — and `test_reader_returns_self_shard_when_other_shards_all_unreadable`, a control confirming the legitimate
      self-shard recovery path is unaffected). Full `quality-gates.sh` green (140s), 43/43 tests passing in the affected
      files.
- [ ] [DATA] P1. Once (1) and (2) are fixed and the consolidator has run cleanly for several consecutive minutes, re-run
      the full 6-source gate check for `sports_p2_history_reference_and_odds_2015_to_present` item #6 and flip its
      checkbox if all sources show `pending_fetch == 0` (or only genuine non-covered/window-closed residual). (repo:
      instruments-service)

## Progress Log

### 2026-07-12 ~07:46 UTC — slot-11: filed, consolidator still crash-looping at file time

Filed while `uts-prod-manifest-consolidator-instruments-sports` was actively crash-looping (5 consecutive failed
executions, one per minute) and the consolidated blob was 15.5+ minutes stale. `read_availability_index` confirmed
returning 0 rows across 3 independent fresh-process calls during this window; raw `gcsfs` read of the same blob
confirmed 4,914,272 real rows (no data loss — read-path bug only). Did not attempt to fix the consolidator or the UTL
read-path bug myself this session (out of scope for the sports_p2 VERIFY task + genuine cross-repo infra fix); flagging
for operator review + a dedicated follow-up dispatch.

### 2026-07-12 — slot-3 (sonnet/high): closed the read-path fix todo

`unified-trading-library@b5ab0c01` — see the flipped checkbox above for the full readout. Root-caused via direct code
read (not inference): `_read_and_merge_per_vm_shards` returns `None` both when no shards exist AND when every shard
fails to list/download/parse, and the caller's final self-shard fallback silently returned an empty DataFrame when that
also came back `None` — exactly reproducing this issue's observed 0-rows-while-4.9M-real-rows-exist state. Fixed by
reusing the already-computed `shards_exist` flag to raise `ManifestConsolidatorStaleError` instead of falling through to
empty, only when shards are confirmed to exist elsewhere. 2 new regression tests, one proven to fail on pre-fix code.
Did NOT touch todo 1 (consolidator health/OOM) or todo 3 (sports_p2 re-gate) — separate scope; this was dispatched
specifically as the read-path fix task.
