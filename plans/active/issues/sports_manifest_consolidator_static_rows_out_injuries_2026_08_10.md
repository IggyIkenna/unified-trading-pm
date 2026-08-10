---
doc_type: issue
title:
  "sports manifest consolidator: rows_out static at 17090683 across >=5 consecutive real merges (23:49Z-00:49Z, 1h+)
  despite growing rows_in/dedup_dropped and confirmed live INJURIES VM writes — census reads may be stale"
summary: >-
  Cloud Logging shows `manifest-consolidator bucket=instruments-store-sports-prd-central-element-323112` genuine merge
  cycles (`error=-`, not the `error=locked` skip variant) reporting the EXACT SAME `rows_out=17090683` across 5
  consecutive real merges spanning `2026-08-09T23:49:05Z` -> `2026-08-10T00:49:04Z` (1h+), with `rows_in` climbing each
  cycle (17137532->17142139->17147899->17152507) and `dedup_dropped` climbing correspondingly
  (46849->51456->57216->61824) — i.e. every new input row is being deduplicated away as already-present, netting zero
  canonical growth. This overlaps a live INJURIES backfill VM (`af-backfill-20260809-222924`) actively writing NEW
  per-VM-shard content confirmed via both its own `[[VM_PROGRESS]] last_completed_date=...` log marker (monotonic real
  date advance, e.g. 2024-04-04->2024-09-13 in ~30min) and fresh per-VM-shard GCS object timestamps
  (`_index/per_vm/af-backfill-20260809-222924*`, latest update 01:21:19Z). A
  `census_all_af_entities_completion_2026_08_03.py` read taken across this window is essentially flat for INJURIES
  (needed=29,480, unchanged across 2 consecutive monitoring-loop ticks spanning ~50min) despite the VM's own progress
  marker showing substantial real advancement — **this pattern matches the already-RESOLVED
  `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` incident almost exactly (same symptom signature: static
  rows_out, growing dedup_dropped, live backfill VM confirmed writing) but that incident's root cause
  (check_shard_freshness's ODDS_API-sentinel collision silently skipping dates) was odds_api/date-freshness specific —
  this occurrence is for INJURIES (a different entity, different code path) so the same root cause is NOT assumed to
  apply without verification.** Additionally observed (secondary symptom, likely same underlying stall): in a 15-minute
  sample window (01:22:55Z-01:29:43Z) EVERY consolidator invocation attempt for this bucket returned `error=locked
  shards=0 rows_in=0 rows_out=0` — the lock was held continuously across that entire window before a new holder
  (`instance=1-c366fe97`) acquired a fresh lock at `01:30:54Z`; not confirmed whether this was a stale lock from a
  crashed holder or legitimate serialized contention, not investigated further (out of scope for the monitoring loop
  that found this).
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [manifest, consolidator, data-correctness, sports, injuries, api-football, zero-growth, stale-read, P1]
related:
  [
    /plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
  ]
created: 2026-08-10
author: claude-agent
last_updated: 2026-08-10
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  Found during the autonomous sports dual-fleet (INJURIES + odds_api) honest-coverage convergence monitoring loop
  (continuation of sports_all_vendor_honest_coverage_convergence_2026_08_07.md) while investigating why two consecutive
  INJURIES census reads were byte-identical despite confirmed live VM progress.
context_scope:
  [
    unified_trading_library/manifest_writer,
    instruments-service/scripts/census_all_af_entities_completion_2026_08_03.py,
    plans/active/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
  ]
---

## What was found

Two consecutive `census_all_af_entities_completion_2026_08_03.py` runs, ~50 minutes apart, both reported identical
`manifest rows (post-floor, <=today): 16176107` and identical `INJURIES needed=29480` — despite the live INJURIES
backfill VM's own `[[VM_PROGRESS]]` marker confirming substantial real, monotonic forward progress in that same window
(2024-04-04 -> 2024-09-13). Cross-checked via Cloud Logging: the manifest consolidator for this bucket
(`instruments-store-sports-prd-central-element-323112`) genuinely ran multiple times in this window with
`success=True error=-` (real merges, not the `error=locked` skip path), but every one reported the exact same
`rows_out=17090683` while `rows_in` and `dedup_dropped` both climbed in lockstep — i.e. all newly-ingested input rows
are being deduplicated away as already-canonical, netting zero growth cycle over cycle.

## Why it matters

The `census_all_af_entities_completion_2026_08_03.py`/`census_fixture_stats_lineups_widening_volume_2026_07_31.py`
scripts (the ground-truth measurement tools for the whole sports AF-entity-completion campaign, including the INJURIES
backfill currently in flight) read the CANONICAL manifest index, not per-VM shards directly. If the consolidator is
stuck in this static-`rows_out` state, EVERY census reading taken during the stall window under-reports genuine progress
— a monitoring session trusting the census alone (without cross-checking the VM's own progress markers, as this session
did) would wrongly conclude the campaign has stalled when it has not.

## Precedent

`sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` documents the IDENTICAL symptom signature (static
`rows_out`, growing `dedup_dropped`, confirmed live backfill VM writing) for `odds_api` specifically, resolved
2026-07-30 by finding the consolidator itself was not at fault — the real cause was `check_shard_freshness`'s
ODDS_API-sentinel logic silently skipping already-"fresh" dates upstream of the consolidator, so the consolidator was
correctly deduplicating genuinely-duplicate content. **Whether the same root cause (or a structurally similar one, e.g.
an INJURIES-entity freshness-sentinel collision) applies here is NOT yet verified** — this doc only establishes that the
symptom recurred for a different entity; the investigation that distinguished "consolidator bug" from "upstream
freshness-skip bug" for the odds_api case has not been repeated for INJURIES.

## Todos

- [ ] [SCRIPT] P1. Determine whether INJURIES' `check_shard_freshness` path (or equivalent freshness-sentinel logic) has
      the same class of bug the odds_api investigation found (silently marking dates "fresh" that shouldn't be, causing
      the writer to re-emit rows identical to what's already canonical, which the consolidator then
      correctly-but-uselessly dedupes away) — or whether this is a genuinely new, INJURIES-specific consolidator issue.
      Repo: market-tick-data-service or instruments-service (wherever INJURIES' freshness-check path lives).
- [ ] [SCRIPT] P2. Confirm whether the `error=locked` streak observed (01:22:55Z-01:29:43Z, every attempt in that window
      failed to acquire the lock) is a stale lock from a crashed/orphaned holder or legitimate serialized contention
      from concurrent consolidator invocations — check the lock file's held-since timestamp against the holder
      instance's actual liveness before assuming either. Repo: unified-trading-library (manifest_writer/consolidator
      lock logic).
- [ ] [DOCS] P3. If confirmed as a genuine, recurring consolidator defect (not just an upstream freshness-skip bug each
      time), consider whether `census_all_af_entities_completion_2026_08_03.py` and
      `census_fixture_stats_lineups_widening_volume_2026_07_31.py` should cross-check a live VM's own progress marker
      (e.g. `[[VM_PROGRESS]]`) against the canonical read and warn when they diverge, rather than silently trusting a
      potentially-stale canonical snapshot.
