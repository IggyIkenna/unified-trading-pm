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
status: resolved
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
  operator session 2026-07-13 — fix shipped UTL@97212d3b + prod rollout verified same day (execution 2knmt on the fixed
  image)
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

- [x] ✅ [CODE] P1. Reproduce/confirm the mechanism in unified-trading-library `manifest_consolidator` — CONFIRMED
      2026-07-13: `_write_consolidated._content_metadata()` stamped `consolidator_content_write_at` with
      `datetime.now(UTC)` at **canonical-WRITE time**, but the merged shard set was frozen earlier at **shard-LISTING
      time** (`_list_per_vm_shards_with_mtime`). Real cycles run 93–121s (per the `_LOCK_TTL_SECONDS` comment), so a
      shard written in `(listing, write − 5s skew)` was never merged yet fell BELOW the next execution's cutoff
      (`content_write_mtime − skew`) → classified "unchanged → already consolidated" → no-op branch →
      `_prune_consolidated_shards` deleted it unmerged. The CAS retry re-stamped `now()` even later while re-merging the
      SAME original shard list, widening the window. The soft lock serializes executions but cannot close this — the
      window exists within a single slow cycle; an overlapping manual `--wait` run maximizes it (exactly the incident
      timeline: flip shard 14:23:38 listed+merged; reconcile9 shard 14:23:58 written mid-merge; winner's marker
      landed >14:23:58; next execution pruned it unmerged).
- [x] ✅ [CODE] P1. Fix shipped `unified-trading-library@97212d3b`: `consolidator_content_write_at` now carries the
      merge's SHARD-LISTING start time (captured immediately before `_list_per_vm_shards_with_mtime`, threaded through
      `_duckdb_consolidate_and_write` → `_write_consolidated(listing_started_at=…)`; CAS retries re-stamp the SAME
      listing time). Prune cutoff = marker − skew therefore only ever covers shards provably visible to the winning
      merge's listing — a shard written between listing and write keeps `mtime > marker − skew`, re-classifies "changed"
      next cycle, and merges before it can satisfy any prune cutoff. `consolidator_run_at` (reader freshness /
      loud-fail-on-stale) still stamps the actual write instant — unchanged. Fail-toward-correctness: a losing CAS retry
      stamping an older listing time only moves the cutoff backward (idempotent re-merge, never a silent drop).
- [x] ✅ [VERIFY] P2. Regression test
      `tests/unit/test_manifest_consolidator.py::test_shard_written_between_listing_and_canonical_write_survives_next_cycle`
      (same commit @97212d3b): execution A lists only the flip shard, a mid-window shard lands during A's merge, A
      writes; asserts marker < mid-shard mtime < write time, execution B classifies it CHANGED + merges its rows into
      canonical, and `_prune_consolidated_shards(cutoff=marker_A)` prunes the settled shard but NOT the mid-window
      shard. Historical sweep (2026-07-13, read-only): sports canonical (4,863,784 rows) verified BY CONTENT against
      today's `_audits` provenance — all 9 `fixtures_eu_reconcile9_cells_20260713.csv` cells present with valid 4-state
      status, all 30,183 `fixtures_eu_flip_pairs_20260713.parquet` (league_id, date) keys present, 0 absent. Per-VM
      orphan sweep across 16 instruments-store/market-data-tick buckets (prd + legacy flat, ls only): backlogs are 1–9
      shards, almost all `_legacy_seed.parquet` (never pruned by design); non-seed stragglers on idle LEGACY flat
      buckets only (`instruments-store-sports…/fixtures-recovery-20260627-183725.parquet`,
      `market-data-tick-tradfi…/manifest-recon-apply-tradfi-20260624-{002811,004328}.parquet`, plus a
      `_legacy_seed.20260703-083335.bak.parquet` misfiled inside `market-data-tick-cefi…/_index/per_vm/`) — consistent
      with merged-but-never-pruned on idle buckets (no subsequent content write to advance the cutoff), not with loss;
      no mutation performed.

## Progress log

- 2026-07-13: Filed from live observation during the FIXTURES pending-EU remediation; recovery for the observed instance
  already done (idempotent re-write, 9/9 rows verified in canonical).
- 2026-07-13 (fix session): Mechanism confirmed + fixed + regression-tested at `unified-trading-library@97212d3b` (QG
  green, quickmerged to LDR). **Deployment note (NOT yet live in prod)**: the deployed consolidators are Cloud Run Jobs
  (`uts-prod-manifest-consolidator-*` + legacy flat variants, ~20 jobs) running image `market-tick-data-service:latest`
  with UTL installed as a dep — per the SSOT's image deploy-hygiene note, this UTL fix does NOT reach them until the
  MTDS image is rebuilt (BASE_IMAGE_DIGEST bump) and the jobs re-resolve `:latest` (job re-deploy / new execution
  pulls). AWS mirrors via ECR `market-tick-data-service:latest` Batch-Fargate jobs. Until then, mitigation stands: avoid
  manual `gcloud run jobs execute --wait` overlapping the `*/1` cron right after writing shards; verify landings by
  content.

- 2026-07-13 (rollout, final): PROD ROLLOUT VERIFIED — fix live in the deployed consolidator fleet. Chain: UTL promote
  PR #549 auto-merged 18:16:53Z (main ≡ LDR); UTL base image republished 17:44:41Z from build 582dbdd4 whose commit IS
  97212d3b (ancestry-verified); MTDS pin bump b11199cb (`BASE_IMAGE_DIGEST` → sha256:b7e391f8) shipped to LDR, carried
  to main via promote PR #548 (green v2, auto-merge re-armed after the fleet failed to arm it; merged 19:08:53Z); MTDS
  image rebuilt (build 609af88b SUCCESS 19:16:58Z; `:latest` → sha256:f9645265 built from LDR commit 97a8330 whose
  Dockerfile pin = b7e391f8). Verified live: execution uts-prod-manifest-consolidator-instruments-sports-2knmt
  (19:19:02Z) ran image @sha256:f9645265 and completed succeededCount=1; per_vm shard dir near-empty (absorption
  normal). The prune race is closed in production. Residual (non-blocking): AWS ECR Batch-Fargate mirrors pick the fix
  up on their next image sync; the manual-overlap mitigation is no longer required on GCP.
- 2026-07-13 (AWS mirror synced): ECR `market-tick-data-service:latest` was 6 weeks stale (2026-05-31, digest ad21c436 —
  the 26 Batch-Fargate consolidators ran pre-fix code). Fresh image built from pinned main@80fa2903 (UTL base
  sha256:b7e391f8 = contains 97212d3b) and pushed: ECR digest sha256:4e60180c at 21:03:35Z (old image untagged). Batch
  job definitions verified to reference `:latest` by TAG (Fargate pulls at each per-minute task start → automatic
  pickup). VERIFICATION CAVEAT: post-push Batch execution observation is BLOCKED from the human-planning host (role
  uts-orchestrator-epic-role lacks batch:ListJobs + s3:ListBucket) — pickup is structurally certain but unobserved from
  here; confirm from a Batch-read-capable role/console if desired. The GCP + AWS fleets now both run the prune-race fix;
  issue remains resolved.
