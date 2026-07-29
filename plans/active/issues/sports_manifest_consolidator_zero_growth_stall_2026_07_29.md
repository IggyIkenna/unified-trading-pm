---
doc_type: issue
title:
  "sports instruments-store manifest consolidator: canonical rows_out static (9,411,982) across every real merge cycle
  for 47+ minutes while active backfill writes were in flight — new data is not being absorbed"
summary: >-
  Cloud Logging shows `manifest-consolidator bucket=instruments-store-sports-prd-central-element-323112` real-merge
  cycles (the ones that acquire the lock and do a genuine DuckDB merge, not the `error=locked` skips) reporting the
  EXACT SAME `rows_out=9411982` across at least 5 consecutive real merges spanning 20:47:50 -> 21:35:14 UTC (47+
  minutes), with `shards=3-4` and nonzero `dedup_dropped` (3863-4710) each time but zero net row growth. This window
  overlaps a live backfill VM (`mtds-backfill-odds-gapfill-tail3-20260729`) actively writing NEW per-VM-shard rows for
  previously-absent dates. A day-level census of the canonical taken after these merges is byte-identical to one taken
  before any backfill work started this session (595 missing odds_api days, same 27 named gap ranges, unchanged) despite
  VM logs showing confirmed successful processing of many of those exact dates across 3 separate VM runs this session.
  The canonical for this bucket appears to not be absorbing new content at all right now.
status: open
nature: issue
asset_group: [sports, meta]
stage: [data]
repos: [unified-trading-library, market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags: [manifest, consolidator, data-correctness, data-loss-risk, sports, silent-drop, P0]
related:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
created: 2026-07-29
priority: P0
parent_epic: sports_master
source: [sports_odds_api_scattered_multiyear_gaps-001]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
assigned_vm: planning
resolved_by:
---

# Sports manifest consolidator: zero row growth despite active backfill writes

## What I found

While backfilling `odds_api` gaps in `instruments-store-sports-prd-central-element-323112`'s manifest
(`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`, task `sports_odds_api_scattered_multiyear_gaps-001`), I ran 3
separate VMs across ~2.5 hours (`mtds-backfill-odds-gapfill-20260729`, `-retry1-20260729`, `-tail2-20260729`,
`-tail3-20260729`), each writing per-VM manifest shards via `ManifestWriter` (`MANIFEST_PER_VM_SHARDS=true`) — VM logs
repeatedly confirmed real writes, e.g.:

```
ManifestWriter: per-VM shard updated (500 total entries, 500 new, process_final=False) at
  instruments-store-sports-prd-central-element-323112/_index/per_vm/mtds-backfill-odds-gapfill-tail3-20260729.parquet
```

A day-level census of `_index/availability_index.parquet` (single read, filtered `source=odds_api, date>=2020-06-06`)
run AFTER all this work — including after the confirmed successful processing of the entire `2020-06-06..2026-04-15`
range (2 independent VM runs each got this far before their final chunk failed) — is **byte-identical** to a census I
ran before any backfill work started: 595 missing days, the same 27 named contiguous gap ranges unchanged, including the
35-day `2026-02-22..2026-03-28` range that both VM runs' logs show being processed with real per-day
`Processed date=... N venues ok` / `ManifestWriter` lines.

**Cloud Logging confirms the canonical is not growing.** Filtering
`resource.type="cloud_run_job" AND textPayload:"bucket=instruments-store-sports-prd-central-element-323112" AND textPayload:"manifest-consolidator bucket="`
over a 6h window, every REAL merge (i.e. not one of the very frequent `error=locked` skips — each real merge holds the
lock ~680-715 SECONDS, so the `*/1` cron effectively serializes to ~1 real attempt every ~12 minutes for this bucket)
reports:

| timestamp (UTC) | shards | rows_in   | rows_out      | dedup_dropped | pruned_shards |
| --------------- | ------ | --------- | ------------- | ------------- | ------------- |
| 20:47:50        | 3      | 9,416,692 | **9,411,982** | 4,710         | 0             |
| 20:59:41        | 4      | 9,416,604 | **9,411,982** | 4,622         | 1             |
| 21:11:26        | 3      | 9,415,845 | **9,411,982** | 3,863         | 1             |
| 21:23:00        | 3      | 9,416,604 | **9,411,982** | 4,622         | 0             |
| 21:35:14        | 3      | 9,415,845 | **9,411,982** | 3,863         | 1             |

`rows_out` is **exactly 9,411,982 in every single real merge**, across 47+ minutes, while `shards` and `dedup_dropped`
both fluctuate cycle to cycle (proving the merge IS reading different/changing shard content each time, not literally a
no-op). Net row growth is zero. This overlaps precisely with `tail3`'s chunks 1-4 actively writing to its own per-VM
shard during this exact window (`21:08-21:34`).

`gcloud storage ls gs://instruments-store-sports-prd-central-element-323112/_index/per_vm/` right now shows only 2
files: `_legacy_seed.parquet` and `sports-fixtures-job.parquet` — none of my 4 VMs' shard files exist there anymore
(consistent with `pruned_shards` firing), yet none of their content appears to have landed in the canonical either.

## Why it matters

This is the **live-fleet-wide sports manifest**, not just the odds_api backfill's target. If the consolidator for this
bucket genuinely is not absorbing new shard content right now:

- **Every other in-flight sports write (any slot, any VM, the routine live/forward capture pipeline) is at the same
  risk** — this is not scoped to my task's writer, it's a property of the consolidator/canonical pairing for this one
  (very large, 9.4M-row) bucket.
- **Downstream honest-coverage / data-status reads are stale-but-confident** — anything reading
  `availability_index.parquet` for `instruments-store-sports-prd` right now is working off a canonical that has not
  reflected new captures for at least this session's duration, with no loud failure signal (the consolidator itself
  reports `success=True` on every cycle — this is not a crash, it looks like a "healthy, steady-state, nothing-new"
  bucket from the consolidator's own self-report).
- This directly blocks `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s P1 backfill todo from EVER showing
  verified completion via the standard census methodology, regardless of how many more VM launches attempt the backfill
  — if genuinely new rows are not being retained, no amount of re-running the launcher fixes it.

## What I did NOT do

I did not read the `manifest_consolidator.py` DuckDB merge/dedup source to pin the exact mechanism (dedup key collision,
a stale canonical read racing the per-VM shard write, a schema/column-order issue silently dropping rows per the
UNION-ALL invariants documented in `manifest-consolidator-ssot.md` §"UNION-ALL correctness", or something else) — that
is real code-reading + likely a live repro, out of scope for what I can respons ibly finish in this session on top of
the OOM investigation already in flight. I also did not attempt a manual `--force` full rebuild (codex-documented recipe
requires PAUSING the cron first + a snapshot; a P0-scale, cross-cutting live-bucket intervention should not be a
unilateral worker action without the pause-first + snapshot discipline the SSOT mandates, and possibly operator
awareness given the blast radius).

## Recommended decision

- [ ] [OPERATOR] P0. **Confirm scope + authorize a live diagnostic session** on the
      `instruments-store-sports-prd-central-element-323112` consolidator: is `rows_out` genuinely static across
      real-content-bearing shards (data loss / silent-drop bug), or is there a legitimate explanation (e.g. my specific
      shard's rows are somehow exact duplicates of already-canonical content, which the day-level census above argues
      strongly against for the `2020-2025` genuinely-absent-before dates)? Needs someone to read
      `unified-trading-library/unified_trading_library/manifest_consolidator.py`'s dedup-key + UNION-ALL logic against a
      live shard sample, ideally with the pause-cron + snapshot discipline `manifest-consolidator-ssot.md` mandates for
      any diagnostic write action.
- [ ] [DATA] P1. **Once root-caused, fix + verify**: re-run the day-level odds_api census after the fix lands and
      confirm the `2020-06-06..2026-04-15` range (already twice-confirmed processed in VM logs) actually shows 0 missing
      days — this is the blocking prerequisite for `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s P1
      checkbox. Repo: unified-trading-library.
- [ ] [DATA] P2. **Audit whether this affects other large sports buckets** (`market-data-tick-sports-prd` — note its OWN
      consolidator cycle in the same logging window showed `shards=1 rows_in=0 rows_out=0` repeatedly, which reads as
      genuinely idle rather than stalled, but worth a second look once the instruments-store mechanism is understood) or
      is specific to `instruments-store-sports-prd`'s size/shape.

## Codex SSOTs

`/codex/05-infrastructure/manifest-consolidator-ssot.md` (merge engine, UNION-ALL invariants, pause-first discipline for
any direct canonical intervention).
