---
doc_type: issue
title:
  "Process gap — an active recovery/backfill plan tracked ~550,062 legacy-MDT rows as recoverable for 8 days after its
  source bucket was already deleted, because nothing re-verified the source still existed between planning and dispatch;
  durable fix = a periodic target-still-exists liveness probe for any recovery/backfill plan whose data source lives in
  a deletable bucket"
summary: >-
  `mdt_legacy_canonical_row_gap_2026_07_16.md` planned a 5-step recovery against
  `market-data-tick-sports-central-element-323112` on 2026-07-16/17. The bucket was manually deleted by the operator on
  2026-07-17T17:05:17Z — possibly same-day as (or before) the plan's own authoring — and no session touched the bucket
  again until `sports_satellite_ao_dispatch_batch2-033` was dispatched 8 days later on 2026-07-25 and its worker
  live-probed the bucket BEFORE writing STEP 1's script, discovering the 404
  (`mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`). In those 8 days the plan sat AO-dispatchable, its premise
  silently false, and nothing in the plan/dispatch lifecycle would have caught it without that one worker's defensive
  pre-implementation check. This is a systemic gap, not specific to MDT: any recovery/backfill plan whose source lives
  in a bucket someone can delete is vulnerable to the same silent-staleness failure mode.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [process-gap, retrospective, recovery-plan, liveness-probe, gcs, plan-hygiene]
related:
  [
    /plans/active/issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md,
    /plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
priority: P2
parent_epic: sports_master
source: "[main] interim guidance on sports_satellite_ao_dispatch_batch2-033, BLK-152099da"
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# Recovery/backfill plans have no source-liveness check between authoring and dispatch (2026-07-25)

## What happened

1. `mdt_legacy_canonical_row_gap_2026_07_16.md` authored 2026-07-16/17, planning a 5-step recovery of ~550,062
   legacy-only tick keys from `market-data-tick-sports-central-element-323112`.
2. The bucket was manually deleted by the operator on 2026-07-17T17:05:17Z (`storage.buckets.delete`, Cloud Audit Logs)
   — same-day as, or immediately after, the plan's authoring.
3. Zero sessions touched the bucket in the following 8 days (confirmed via this session's own research: the source doc's
   Progress Log shows STEPS 1-5 as planned-only, never executed).
4. `sports_satellite_ao_dispatch_batch2-033` dispatched the recovery's STEP 1 on 2026-07-25. The worker, before writing
   the read-only containment script, defensively live-probed the bucket rather than assuming the 2026-07-16 plan's
   premise still held — and found the 404. Full findings in `mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`.

## Why it matters

Nothing in the plan-authoring, plan-hygiene-sweep, or AO-dispatch lifecycle re-verifies that a recovery/backfill plan's
DATA SOURCE still exists between when the plan is written and when a worker is dispatched against it. The only reason
this was caught in 8 days rather than staying silently wrong indefinitely is that one worker happened to add a defensive
live-probe before writing code — a good habit, but not a systematized one. A plan can sit AO-dispatchable with a false
premise for an unbounded period; the failure mode is silent (a 404 the worker discovers, not something the plan-hygiene
sweep flags) and general (applies to ANY recovery/backfill plan whose source is a deletable GCS bucket, S3 bucket, or
similarly ephemeral store — not just this one).

## Recommended fix

A lightweight, generalizable pattern rather than a one-off patch for MDT specifically:

1. **At dispatch time, not just at authoring time**: for any todo tagged `[DATA]`/`[BACKEND]` whose brief references
   reading from a named bucket/prefix as its recovery SOURCE, the worker's pre-implementation step should include a
   cheap existence probe (`gcloud storage buckets describe` / `list_blobs` HEAD-equivalent) before writing the
   substantive script — exactly the pattern this session used organically. This doesn't need new tooling; it needs to
   become an explicit, named step in the recovery/backfill todo-authoring convention (`plans/active/task_template.md` or
   a sibling recovery-plan template) so it happens by habit, not luck.
2. **Optional, lower-priority**: a periodic (e.g. weekly) automated liveness sweep over any `status: open`
   `plans/active/issues/*.md` whose frontmatter or body names a specific bucket as a recovery source, flagging any whose
   target bucket no longer resolves — catching drift between authoring and dispatch even when no worker happens to probe
   first. This is a nice-to-have hardening, not required to close this finding; the todo below scopes only the cheap,
   high-value fix (item 1).

## Todos

- [ ] [DOC] P2. Add an explicit "live-probe the data source before writing the recovery/backfill script" step to
      `plans/active/task_template.md`'s AO-authoring guidance (or the nearest recovery/backfill-specific section) so
      future recovery/backfill todos carry this as a named pre-implementation step, not an incidental habit. (repo:
      unified-trading-pm)

## Codex SSOTs

None new — this is a plan-authoring convention gap, not a durable architectural contract; the fix belongs in
`plans/active/task_template.md`.
