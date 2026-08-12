---
doc_type: issue
title:
  Sports-prd manifest consolidator's canonical rows_out frozen at exactly 9,239,513 for 5+ hours despite continuous
  shard processing — masks real progress fleet-wide, not just AF
summary: >-
  Found as a side effect of the `sports_af_full_entity_completion_2026_08_03.md` campaign: a FIXTURE_STATS backfill VM
  (`af-backfill-20260804-130914`) ran ~11min with confirmed real writes (run.log: `ManifestWriter: per-VM shard updated
  ... 372 new`, genuine dedup against existing per-league parquets), but an immediate re-census against the canonical
  `_index/availability_index.parquet` showed exactly zero movement. Investigated the `uts-prod-manifest-consolidator-
  instruments-sports` Cloud Run job's actual execution logs (not just scheduler health) rather than accept "probably
  just lag" at face value. The scheduler/job themselves are healthy (fires every 1min, executions complete
  successfully). But `rows_out` — the canonical row count after each successful merge — has been **bit-for-bit identical
  (9,239,513) across every single successful merge from 2026-08-04T08:06:48Z through at least 13:08:48Z (5+ hours, ~35+
  successful merges)**, despite `shards` processed ranging 3-15 per cycle and `dedup_dropped` ranging from 187 to
  2,000,000 rows. The arithmetic is exact every time: `dedup_dropped = rows_in - rows_out`. This means every row
  entering the merge over 5+ hours — across the ENTIRE sports-prd bucket's shard traffic (fixtures, stats, lineups,
  enrichment crons, multiple backfill VMs, not just AF) — has been classified as a duplicate and silently dropped, not
  merged into canonical. Given the volume and diversity of jobs writing to this bucket throughout the day, it is not
  credible that zero genuinely-new distinct rows were produced in 5+ hours. This is not the previously-resolved
  `manifest_consolidator_stale_sports_bucket_2026_07_21.md` issue (that was a loud-fail read-path staleness error under
  a specific opt-in flag; this consolidator reports `success=True error=-` every cycle — it thinks it's working
  correctly). Not root-caused to a specific line of merge/dedup logic — flagging for someone with context on
  `manifest_consolidator.py`'s incremental anti-join/UNION ALL path (SSOT below, § "Incremental cycle (steady state)").
status: false-positive
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, deployment-service, instruments-service]
scope: [engineer]
tags: [manifest, consolidator, sports, data-correctness, dedup, cross-cutting, false-alarm-likely]
related:
  [
    /plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/archive/issues/manifest_consolidator_stale_sports_bucket_2026_07_21.md,
    /plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
  ]
created: "2026-08-04"
author: unknown
parent_epic: infrastructure_master
priority: P3
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: ["sports_af_full_entity_completion campaign, autonomous continuation, 2026-08-04"]
resolved_by:
locked_by:
depends_on: []
---

> **🟨 LIKELY FALSE ALARM 2026-08-05T17:03Z — read this before anything else in this doc.** A pre-existing, already-
> RESOLVED sister doc, `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`, investigated the EXACT same
> symptom on this SAME consolidator five days earlier and proved the premise wrong via a live diagnostic (operator-
> authorised pause-cron + snapshot + probe): **`dedup_dropped` is not an independently-measured quantity — it is
> `rows_in - rows_out`, derived, per `manifest_consolidator.py:998`.** So "every shard row is a duplicate" and "row
> count didn't grow" are the SAME statement restated, not two corroborating pieces of evidence. That investigation
> directly diffed a live shard against the canonical using the module's own dedup-key resolution and found shard rows'
> `attempted_at` timestamps ALREADY present in canonical — i.e. genuinely absorbed via in-place UPDATE, not dropped. I
> made the identical reasoning error the 07-29 doc's ORIGINAL (later-disproven) report made. **This does NOT invalidate
> the census-based progress figures in `sports_af_full_entity_completion_2026_08_03.md`** — those read the canonical
> directly and their movements track real backfill activity (FIXTURE_STATS' -294/-243 progress this session matches its
> own actively-running VM; STANDINGS/TEAMS' drops match other jobs' backlog draining) — census-based tracking is
> unaffected and reliable either way. What's now in doubt is only the "the consolidator is silently dropping new
> content" framing below — the "stuck" plateaus this doc documents are plausibly just cycles where the merged shards'
> content was ENTIRELY already-captured (e.g. a backfill VM's own
> `Per-fixture pre-fetch skip: N pairs already in existing per-league parquets` re-processing), which produces the exact
> same static-`rows_out` signature with zero actual bug. I have NOT run the same live pause+snapshot+probe diagnostic
> myself to definitively confirm this (that's a real live-bucket intervention I'm not taking unilaterally, per the same
> discipline the 07-29 doc's own resolution followed) — downgrading status to `likely-false-alarm` and priority
> accordingly rather than closing outright without that direct confirmation. Recommend whoever next touches this doc
> either runs that diagnostic to confirm, or simply closes this as a duplicate false-alarm citing the 07-29 doc's
> resolution. Everything below this banner is retained as the original (now-superseded) report.

## What I found

Running the AF entity-completion campaign, a FIXTURE_STATS backfill VM (`af-backfill-20260804-130914`, ran
12:10:17Z→12:21:20Z, ~11min) logged genuine work:

```
2026-08-04 12:19:27,905 INFO ManifestWriter: per-VM shard updated (10873 total entries, 372 new, process_final=False)
  at instruments-store-sports-prd-central-element-323112/_index/per_vm/af-backfill-20260804-130914-c1.parquet
2026-08-04 12:19:33,557 INFO Per-fixture: skipping 3 entities already in manifest, fetching ['fixture_stats']
2026-08-04 12:19:34,697 INFO Per-fixture pre-fetch skip: 89 (entity, fixture_id) pairs already in existing per-league
  parquets — skipping api_football calls (pass --force to re-fetch regardless)
```

An immediate re-census (`instruments-service/scripts/census_fixture_stats_lineups_widening_volume_2026_07_31.py`, reads
the canonical `_index/availability_index.parquet` via the UTL storage client) showed **exactly zero movement** (still
77,092 resolved / 56,940 needed, identical to before the run).

Rather than accept "consolidator lag" on faith, pulled the actual `uts-prod-manifest-consolidator-instruments-sports`
Cloud Run job execution logs:

```bash
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-manifest-consolidator-instruments-sports" AND textPayload:"error=-"' \
  --project=central-element-323112 --format="value(timestamp,textPayload)" --freshness=8h --limit=60
```

Every successful merge (`error=-`, i.e. not skipped on the per-cycle lock) from **2026-08-04T08:06:48Z through
13:08:48Z** — 5+ hours, ~35+ successful merges — reports:

```
rows_out=9239513   (IDENTICAL every single time)
```

while `shards` (3-15), `rows_in` (9,242,283-11,280,424), and `dedup_dropped` (187-2,000,000) all vary substantially
cycle to cycle. The arithmetic holds exactly every time: `dedup_dropped == rows_in - rows_out`. Representative sample
(full 8h trend pulled and reviewed, not just these rows):

```
2026-08-04T08:06:48Z shards=9  rows_in=10239513 rows_out=9239513 dedup_dropped=1000000
2026-08-04T09:50:31Z shards=12 rows_in=11239513 rows_out=9239513 dedup_dropped=2000000
2026-08-04T11:45:37Z shards=3  rows_in=9739513  rows_out=9239513 dedup_dropped=500000
2026-08-04T12:59:39Z shards=4  rows_in=9269304  rows_out=9239513 dedup_dropped=29791
2026-08-04T13:08:48Z shards=3  rows_in=9282491  rows_out=9239513 dedup_dropped=42978
```

Before 08:06Z the value was different (9,248,476 from ~05:17Z, ticking to 9,248,477 once around 06:43Z, then dropping to
9,239,513 at 08:06Z) — so the canonical figure DOES change occasionally; it is not permanently hardcoded. But since
08:06Z it has not moved by a single row across 5+ hours of continuous, substantial shard-processing activity spanning
the whole sports-prd bucket (not just AF — this bucket also receives writes from Transfermarkt/Footystats/soccer-info
enrichment crons, `expected-universe-v2-sports`, and every sports fixtures schedule cron, per the scheduler job list).

**The scheduler/job infrastructure itself is healthy** — this is not the previously-resolved
`manifest_consolidator_stale_sports_bucket_2026_07_21.md` staleness/loud-fail issue (that was a read-path error under
`MANIFEST_ALLOW_STALE_FALLBACK`; this consolidator returns `success=True error=-` every cycle, i.e. it believes it
completed a normal merge). The existing `ConsolidatorLivenessMonitor` watchdog only checks heartbeat AGE (did it run
recently), not output correctness — so it would not catch this class of bug (running fine, producing a frozen output).

## Why this matters beyond the AF campaign

This consolidator serves the ENTIRE sports-prd bucket. If it has genuinely stopped merging new content into canonical
for 5+ hours, every backfill/enrichment job writing to this bucket during that window (not just the AF campaign) is
similarly invisible to anything reading the canonical manifest — census scripts, completion gates, downstream readers.
The underlying per-fixture DATA itself is confirmed durable and correctly deduped independent of this (the AF backfill's
own pre-fetch skip logic reads real per-league parquets directly, not the canonical manifest), so no data is being lost
— but genuine completion cannot currently be confirmed via manifest-based census for this bucket, and any process gating
on canonical manifest completeness (e.g. `assert_consolidator_healthy`, downstream readers assuming freshness ==
correctness) could be silently working off stale/incomplete state without any loud failure.

## What I did NOT do

Did not read `manifest_consolidator.py`'s incremental anti-join/UNION ALL merge logic (SSOT
`/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Incremental cycle (steady state)" — the
`_stale_drop_predicate` and dedup-key logic mentioned there is the most likely place to look) to find the actual root
cause — that's a genuinely separate investigation from the AF campaign this finding surfaced from, and I don't have
enough context on that merge path to safely change currently-live production consolidator code. Did not pause or attempt
to manually trigger a recovery merge (`MANIFEST_ALLOW_STALE_FALLBACK=true`, `launch-sports-manifest-rescan-vm.sh`) — the
former is an opt-in read-path fallback for a different failure mode (stale/missing canonical, not a frozen-but-present
one), and the latter's own header describes an unrelated narrower purpose (FIXTURES canonical-league-ID remapping) with
real risk (singleton lock, explicit warnings against deleting what might be another dispatch's live VM).

## Impact on the AF campaign specifically

Continuing to launch AF backfill VMs regardless — the underlying per-fixture data writes are durable and correctly
deduped independent of this bug, so real work continues to accumulate even though it won't be census-visible until this
resolves. But the AF campaign's own completion criterion (census-confirmed convergence to ~0 needed per entity, so the
operator can downgrade the API-Football subscription) cannot be truthfully declared while this consolidator stays frozen
— see `sports_af_full_entity_completion_2026_08_03.md` for the live tracking.

## Update 2026-08-05T00:22Z — still frozen, +1 tick does not indicate recovery

Re-checked ~11 hours later. `rows_out` ticked from 9,239,513 → **9,239,514 around 2026-08-04T18:55:18Z** (a delta of
exactly **+1 row**), then **re-froze at the new value through at least 2026-08-05T00:22:59Z** — another 5.5+ hours, ~35+
more successful merges, same pattern (`shards` 6-18, `dedup_dropped` up to 2,015,177 every cycle, `rows_out` unchanged).
This is not a resolution — if anything it reinforces the original finding: across the full ~16-hour window observed so
far, canonical has grown by exactly 1 row despite continuous, heavy shard/dedup churn. Whatever is misclassifying new
content as duplicates is letting through roughly nothing, not intermittently failing. Still unresolved, still needs
someone with `manifest_consolidator.py` merge/dedup-key context.

## Reproduction / verification for whoever picks this up

```bash
# Confirm current state (should still show a flat rows_out if unresolved):
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="uts-prod-manifest-consolidator-instruments-sports" AND textPayload:"error=-"' \
  --project=central-element-323112 --format="value(timestamp,textPayload)" --freshness=2h --limit=20 | sort
```

If `rows_out` is still flat, next step is reading `manifest_consolidator.py`'s merge/dedup key logic directly (not just
log output) to find why genuinely-new per-VM shard rows are being classified as duplicates of existing canonical rows.

## Update 2026-08-05T16:04Z — genuine bursty recovery in progress, not fixed, still worth tracking

Pulled the full trend from 2026-08-05T01:26Z through 16:04Z (~14.5h). **`rows_out` is now moving for real**: from
9,241,283 (01:26Z) to 9,270,239 (16:04Z), **+28,956 rows**. The pattern is bursty, not steady: long stuck plateaus
(1-2.5h each, e.g. 01:52Z→04:16Z flat, 06:59Z→08:45Z flat, 12:19Z→14:00Z flat, 15:38Z→16:04Z flat-so-far) interleaved
with active windows of small, steady per-cycle growth (e.g. 08:52Z→12:19Z: ~600-1,000 rows added roughly every 10min,
totaling ~16,257 rows over that one window alone). This is a materially different shape than the original finding (a
full, unbroken 16h dead flat-line from 08:06Z 08-04 through 18:55Z 08-04) — something has genuinely changed for the
better, though it is NOT a clean fix: the plateaus mean the underlying misclassification bug is still firing some
fraction of the time, just not permanently. Confirms real, substantial downstream effect: a re-census now shows
STANDINGS (64,439→51,740 needed, -12,699) and TEAMS (64,723→47,020 needed, -17,703) dropping dramatically — neither
entity has had an AF backfill VM launched against it this entire campaign (verified via `gcloud compute operations list`
— no STANDINGS/TEAMS-named or otherwise-suspicious af-backfill launches), so this is very likely backlogged work from
OTHER routine sports jobs (enrichment crons, fixtures-schedule crons — this bucket serves the whole sports-prd estate,
not just AF) that was sitting unconsolidated during the freeze and is now draining through. Still not root-caused at the
code level — flagging the plateau/burst pattern as an additional clue for whoever picks this up (sounds like an
intermittent lock-contention or partial-batch-skip condition, not a permanent logic bug, given it now completes real
merges some fraction of the time).
