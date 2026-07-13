---
doc_type: issue
title:
  Manifest consolidator prune race — a per-VM shard written seconds before two overlapping executions was pruned WITHOUT
  its rows merging into canonical (silent data loss class, observed once 2026-07-13, recovered idempotently)
summary: |
  During the 2026-07-13 sports FIXTURES pending-EU remediation, the first reconcile9 per-VM shard
  (_index/per_vm/fixtures-eu-reconcile9-20260713-142348.parquet, 9 rows, written 14:23:58Z) was pruned by the
  instruments-sports manifest consolidator WITHOUT its rows landing in the canonical availability_index.parquet.
  Timeline: shard written 14:23:58Z; per-minute cron execution created 14:24:06Z; overlapping MANUAL execution
  (gcloud run jobs execute --wait) created 14:24:21Z. A sibling shard written 20s earlier (the 30,183-row flip shard,
  14:23:38Z) DID merge in the same window — so the race window is narrow: a shard written between one execution's
  shard-listing and the other's prune step can be deleted unmerged. Recovery was idempotent re-write of the same rows
  at 14:31:00Z absorbed by the cron alone (merged + pruned cleanly within ~2 cycles). A later routine
  is-daily-enum-sports shard (14:50:21Z) also merged cleanly with no recurrence. This is a silent-data-loss class for
  ANY per-VM manifest shard (all asset groups, both surfaces) whenever two consolidator executions overlap — most
  likely when a manual/--wait execution overlaps the */1 cron. Suspect: prune cutoff vs shard-listing window in
  unified-trading-library's manifest consolidator (a merge run pruning shards it did not itself list/merge, or
  pruning on name-set rather than a content-write-marker stamped before prune).
status: open
nature: notes
asset_group: [sports, defi, cefi, tradfi]
stage: [data]
repos: [unified-trading-library, instruments-service]
scope: [engineer]
tags: [manifest, consolidator, race-condition, data-loss, per-vm-shards, cloud-run, data-correctness]
related:
  [
    plans/active/issues/sports_fixtures_pending_eu_phantom_denominator_2026_07_13.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source: |
  Observed live by the flip+reconcile leg of remediation workflow wf_8f931d1a-08f (operator session 2026-07-13) —
  see the sports_fixtures_pending_eu issue doc's step-2 evidence. Non-blocking for that remediation (idempotent
  re-run recovered), but the class is silent data loss for any concurrently-written manifest shard.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Manifest consolidator prune race (overlapping executions)

## Observed timeline (2026-07-13, instruments-sports surface)

| Time (UTC) | Event                                                                                              |
| ---------- | -------------------------------------------------------------------------------------------------- |
| 14:23:38Z  | Flip shard `fixtures-eu-flip-20260713-142325.parquet` (30,183 rows) written — **merged OK**        |
| 14:23:58Z  | Reconcile shard `fixtures-eu-reconcile9-20260713-142348.parquet` (9 rows) written                  |
| 14:24:06Z  | Per-minute cron consolidator execution created                                                     |
| 14:24:21Z  | Overlapping manual execution created (`gcloud run jobs execute … --wait`, completed as `…-llb88`)  |
| after      | Reconcile shard **pruned; its 9 rows absent from canonical** (verified by content re-download)     |
| 14:31:00Z  | Idempotent re-write of the same 9 rows (new shard) — cron-only absorption, merged + pruned cleanly |
| 14:50:21Z  | Routine `is-daily-enum-sports` shard merged cleanly — no recurrence observed                       |

## Why it matters

- Per-VM shards are the ONLY sanctioned write path into the availability index (hand-edits banned) — a pruned-unmerged
  shard is **silent** loss of manifest rows (capture evidence), invisible until someone diffs canonical content.
- Applies to every surface/asset group using the consolidator, not just sports; likeliest trigger is a manual `--wait`
  execution overlapping the `*/1` cron (exactly what operational runbooks tell people to do after a backfill).

## Suspected mechanism (to confirm in code)

A consolidator execution prunes shards it did not itself merge: if execution A lists shards, execution B lists the same
shards plus a newer one, A merges + prunes (or B prunes based on name-set/mtime cutoff) such that the newer shard is
deleted while only the older merge's content reaches the canonical write. Check in unified-trading-library's
consolidator (`manifest_consolidator`): the prune step's shard set vs the merge's actually-read shard set, and whether a
content-write success marker gates pruning per-shard.

## Todos

- [ ] [CODE] P1. Reproduce/confirm the mechanism in unified-trading-library `manifest_consolidator`: audit the
      shard-listing → merge → canonical-write → prune sequence for windows where a shard can be pruned by an execution
      that did not merge it (or whose merged content lost the canonical-write race to a concurrent execution).
- [ ] [CODE] P1. Fix so prune is gated per-shard on that shard's content having reached canonical (e.g. prune exactly
      the shard set read by the merge whose canonical write won, via generation-preconditioned GCS write + shard-list
      manifest in the canonical object's metadata; or single-flight lock so executions cannot overlap).
- [ ] [VERIFY] P2. Regression test simulating two overlapping executions with a shard written between their listings;
      plus a one-off historical sweep for other silently-lost shards (compare per-VM shard backups/\_audits provenance
      vs canonical content where provenance exists).

## Progress log

- 2026-07-13: Filed from live observation during the FIXTURES pending-EU remediation; recovery for the observed instance
  already done (idempotent re-write, 9/9 rows verified in canonical).
