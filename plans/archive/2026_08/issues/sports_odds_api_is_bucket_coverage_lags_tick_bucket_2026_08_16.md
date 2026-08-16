---
doc_type: issue
title: "Sports instruments-store manifest under-reports odds_api coverage vs the tick bucket (547 vs 247 missing days over the same window)"
summary: >-
  While investigating the `[DIAG] P3` "23 sentinel-free missing odds_api days" todo
  (`sports_satellite_ao_dispatch_batch12_2026_08_09.md:153`), a fresh census over the exact
  2020-06-06..2026-04-15 window used by the original root-cause investigation found the two sports manifest
  surfaces materially disagree on odds_api coverage: `instruments-store-sports-prd-central-element-323112` (the
  Axis-10b SSOT routing manifest) shows 547 missing calendar days for `source=odds_api`, while
  `market-data-tick-sports-prd-central-element-323112` (the bytes-physically-live-here tick bucket, and the bucket
  `check_shard_freshness`/the live backfill fleet actually read+write) shows only 247 missing days for the SAME
  window. This is the same cross-bucket-mirror-sync-gap class already tracked for `trades`/`TRADES` labeling in
  `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md`, here manifesting as coverage under-count
  rather than a stale label.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [sports, odds-api, manifest, cross-bucket, mirror-sync, data-correctness, honest-coverage]
related:
  [
    /plans/archive/2026_08/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md,
    /plans/active/issues/sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md,
    /plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16 (slot-15)"
author: slot-32 (data_engineering)
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
source: ["sports_satellite_ao_dispatch_batch12_2026_08_09-153 (23 sentinel-free days investigation)"]
resolved_by: slot-15 (data_engineering), 2026-08-16
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
---

# Sports IS-bucket odds_api coverage lags the tick bucket

> **🟩 RESOLVED / ARCHIVED 2026-08-16 (slot-15, data_engineering).** Diagnostic question answered: NOT the
> `trades`/`TRADES` cross-bucket mirror-mislabel (0/339 differential days carry that data_type — ruled out
> directly). The 547-vs-247 `source=odds_api` day-coverage gap is instead the ALREADY-TRACKED, actively-running
> odds_api backfill gap owned by `/plans/active/issues/sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`
> (P1) — root cause: `instruments-store-sports-prd`'s `odds_api` rows were migrated in from MTDS/the tick-bucket
> via a one-time script that itself left residual gaps, which that P1 doc's vendor-refetch VM campaign has been
> closing since 2026-07-27 (635 → 291 missing days as of its latest census). No new fix scoped here; no
> successor doc — future odds_api coverage monitoring belongs to that P1 doc.

## What I found

Reproduced the 2x2 `(has odds_api row) x (has ODDS_API sentinel row)` classification from
`sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s root-cause section, over the exact same
`2020-06-06..2026-04-15` window, against BOTH candidate sports manifest surfaces (single read each, column-pruned +
date-filtered, no whole-corpus walk;
`market-tick-data-service/scripts/sports/investigate_23_sentinel_free_odds_gaps_2026_08_16.py --bucket-kind
{instruments-store,market-data}`):

| bucket                                     | days missing `source=odds_api` (of 2140 calendar days) | days with `venue=ODDS_API` sentinel |
| ------------------------------------------- | -------------------------------------------------------- | ------------------------------------ |
| `instruments-store-sports-prd` (SSOT routing manifest, Axis-10b) | **547** | 2140/2140 (100%) |
| `market-data-tick-sports-prd` (bytes physically live here; `get_tick_data_bucket()`/`check_shard_freshness` target) | **247** | 2139/2140 (99.95%) |

Both surfaces now show **0** sentinel-free residual for this window (the original "23 sentinel-free" finding is fully
resolved — see the companion Progress Log entry in the source doc) — but the two surfaces disagree by 300 days on
plain odds_api presence for the identical window. `instruments-store-sports-prd` is the more pessimistic/stale of the
two.

This is architecturally expected to some degree — sports routes every `data_type` through the IS-bucket manifest as
its documented SSOT/routing surface even though the actual bytes live in the tick bucket (Axis-10b pattern,
`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py::_SPORTS_CROSS_BUCKET_DATA_TYPES`) — but the
mirror is evidently NOT staying in sync: a 300-day gap over a 2140-day window (14%) is too large to be simple
propagation lag. The sibling doc `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md` found the exact
same shape of gap (a live producer still writing rows the IS-bucket mirror never receives) for the `trades`/`TRADES`
data_type — this finding is very likely the SAME underlying sync gap, just observed via `source=odds_api` coverage
instead of a data_type label.

## Why it matters

Any future census/audit/investigation that reads `instruments-store-sports-prd` as "the" sports odds_api coverage
source (as the original 2026-07-29/30 root-cause investigation did, and as `four-surface-reconciliation-procedure.md`
would default to for a "check the SSOT manifest" instruction) will systematically OVER-report the true gap — this is
exactly what already happened once: the original investigation's 595/572/23 numbers were all measured against the
IS-bucket, which turns out to be the less-complete of the two surfaces for this source. A P3 diagnostic task
re-running the same query today would have reproduced a smaller-but-still-nonzero apparent gap purely from mirror
lag, not from a real missing-data problem, had it not also cross-checked the tick bucket directly.

## What I did NOT do

Did not investigate the mirror-sync mechanism itself (whether it's driven by the manifest consolidator's cross-bucket
sync, a writer double-stamp, or a one-time migration that was never made durable) — that diagnostic work belongs to
whoever picks up the todo below, and likely overlaps significantly with the sibling `trades`/`TRADES` doc's own
Progress Log findings (which already identified "the sports odds_api writer is still actively stamping
`data_type=trades`/`TRADES`... into this [IS-bucket] surface" as of 2026-08-15 — the write side for odds_api coverage
specifically was not separately confirmed live vs stale here).

## Recommended decision

- [x] ✅ [DATA] P3. **DETERMINED 2026-08-16 (slot-15, data_engineering) — verdict (b) with a twist: NOT the
      trades/TRADES mirror-mislabel class, AND not a NEW gap either — this is the ALREADY-TRACKED odds_api
      backfill gap in `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` (P1). No new fix scoped; no
      separate action needed beyond that doc's own already-active remediation.** Investigated directly rather
      than waiting on the sibling `[OPERATOR]` VM todo (still `[ ]` open, per a fresh read of that doc today) —
      see Progress Log for the full method + evidence. Repos: instruments-service, market-tick-data-service.

## Progress Log

- **2026-08-16 (slot-32, data_engineering)**: filed while investigating the "23 sentinel-free missing odds_api days"
  `[DIAG] P3` todo — see the companion addendum in
  `/plans/archive/2026_08/issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`'s Progress Log for that task's
  own resolution (the 23-day residual is fully closed; this doc tracks the separate bucket-divergence finding
  surfaced along the way).
- **2026-08-16 (slot-15, data_engineering) — investigated + resolved, verdict (b)-not-(a), and further identified
  as ALREADY-TRACKED, not a new gap.** The sibling `sports_p2_trades_mirror_unstamped_instruments_store_2026_08_15.md`
  `[OPERATOR]` relabel-VM todo is still `[ ]` open (not yet executed), so re-running this doc's own script
  post-fix (the todo's literal instruction) wasn't yet possible — investigated the ROOT CAUSE directly instead,
  which the AO-eligibility rule favors over waiting idle on another doc's operator-gated VM.
  - **Method (2 single-walk, column-pruned + date-filtered `read_availability_index()` reads, no new
    whole-corpus GCS walk)**: (1)
    `market-tick-data-service/scripts/sports/investigate_odds_api_is_bucket_gap_2026_08_16.py` reproduced the
    547-vs-247 `source=odds_api` day-presence gap over the same `2020-06-06..2026-04-15` window (fresh
    read: IS-bucket 1593/2140 days present, tick-bucket 1893/2140), computed the exact 339-day differential set
    (days present in the tick-bucket but absent-by-`source` in the IS-bucket), then for EVERY differential day
    inspected the IS-bucket's full row set (any source/data_type) for that date. Result: **0/339 differential
    days carry a `data_type=trades`/`TRADES` row** — the trades-mirror mislabel this todo asked about as
    hypothesis (a) is definitively ruled out; every differential day already has SOME IS-bucket row (0
    total-absence days), just never one with `source=odds_api`. (2)
    `market-tick-data-service/scripts/sports/probe_odds_source_field_2026_08_16.py` drilled into a 4-day sample
    of the differential set: the `data_type=odds` rows present on those dates all carry `source=footystats,
    pipeline_mode=batch_footystats` — a DIFFERENT vendor's own `odds`-labeled product, not a mislabeled
    `odds_api` row with a blank/wrong `source` field. So the differential is a genuine absence of any
    `odds_api`-sourced row on those IS-bucket days, not a same-vendor mislabel of any kind.
  - **Cross-referencing this genuine-absence finding against the active corpus** (grepped `related:` +
    `source:` fields, then read `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md` in full — the doc was
    already in this issue's own `related:` list) found the exact mechanism: that P1 doc's own "What I found"
    section states `instruments-store-sports-prd`'s `odds_api` rows were **migrated in from MTDS/the tick-bucket
    via a one-time `migrate_orphaned_mtds_odds_api_bucket_rows_2026_07_13.py` script**, and that migration itself
    left residual gaps — exactly explaining why the tick-bucket (the live writer's direct target) has better
    coverage than the IS-bucket (a one-time historical migration snapshot, now being incrementally backfilled).
    That doc has been actively running VM-launched vendor re-fetches for this precise gap since 2026-07-27,
    converging 635 → 590 → 300 → 291 missing days (latest census 2026-08-11T16:29Z, wider `..2026-08-11` window,
    `smallchunk23` VM active at last check) — this IS the dedicated backfill fix hypothesis (a) asked about a
    DIFFERENT sibling for; the real answer is a THIRD doc already owns it. (Absolute counts aren't
    directly comparable across the two docs' different window ceilings/census methodologies — not reconciled
    further here, out of this diagnostic todo's scope — but the mechanism match — one-time-migration-into-IS-
    bucket + active vendor-refetch backfill converging over weeks — is unambiguous.)
  - **No new fix scoped or launched** — `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`'s own P1/P2
    chain already owns relaunching + re-censusing this exact gap; duplicating a second backfill effort here
    would risk the concurrent-VM double-spend this workspace already guards against
    (`odds-api-concurrency-guard.sh`, cap=1). Added this doc to that P1 doc's own `related:` would be circular
    (already present); no code fix needed here beyond the two read-only investigation scripts (both `Lifecycle:
    oneoff`, delete-when this doc archives). Flipping this checkbox — the diagnostic question is fully answered
    (NOT (a) trades-mislabel; not a new (b) either — it's the already-active P1 backfill's own known-and-tracked
    gap) and no further action belongs to THIS doc.
