---
doc_type: issue
title:
  "Post-purge tradfi manifest cleanup: a force-rebuild does NOT drop the 686k stale massive + 16k phantom rows
  (deletion-resurrection gap)"
summary:
  After the authorized massive purge removed 1,701,422 batch_massive OBJECTS, the tradfi availability manifest still
  carries 686,005 stale batch_massive rows + 16,389 phantom batch_databento trades/tbbo captured rows (zero backing
  objects) + 35.5% blank instrument_id + 0% derivative -USD@LIN. A `consolidate(force=True)` will NOT drop the stale
  rows — the consolidator re-scans 100% of the canonical on a full rebuild and a pure DELETION correction survives
  trivially (the documented deletion-resurrection gap). rebuild_tradfi_manifest.py (additive per-VM shards, merged) also
  does not drop them. Fixing (a)+(b) needs surgical index removal; fixing (c)+(d) needs the object-walk id
  re-derivation. Both target a live _index a peer is already rebuilding — coordinate before any cutover.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [manifest, consolidator, deletion-resurrection, phantom-rows, data-correctness, tradfi, coordinate]
related:
  [
    massive_purge_blocked_databento_l1_entitlement_2026_07_20,
    reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-20
priority: P0
parent_epic: tradfi_master
source: "Post-purge manifest analysis (slot-1, 2026-07-20, RUN_TS=20260720-193849)"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by:
---

# Post-purge tradfi manifest cleanup — the naive force-rebuild won't drop the stale rows

## ✅ RESOLVED (a)+(b) — surgical drop applied under paused consolidator (slot-1, 2026-07-20T20:09Z)

**(a) phantom + (b) massive are DONE via a CAS surgical drop.** (c)/(d) are SCOPED FOLLOW-UP (see below). The apply was
done directly, NOT handed off — the field turned out to be CLEAR for the tick `_index` (the only peer rebuild in flight,
`rebuild_gated.py`, writes the **instruments-store catalogue**, not this tick bucket; the only per-VM shard is the
frozen `_legacy_seed`).

**CRITICAL CORRECTION — the "16,389 phantom" count was CONTAMINATED; blind-dropping it would have destroyed real data.**
The phantom set was defined from a heuristic shard list (`phantom_db_l1_shards.json`, 3,488 CME/NYSE/NASDAQ tbbo+trades
shard-keys). A mandatory on-disk re-verification of every candidate shard (2,393 `(venue,day)` prefixes, delimiter walk)
found that **79 of the candidate shards actually HAVE `batch_databento` objects on disk** — CME is a databento-native
venue (GLBX) and genuinely holds historical tbbo/trades. Those 79 shards carry **12,790 real `captured` manifest rows**.
Only **3,413 shards (3,615 rows) are TRUE phantoms** (zero object on disk). Reconciliation is exact:
`16,405 candidate db-captured L1 rows = 12,790 KEPT (real data) + 3,615 TRUE phantom`. **Dropping the stale 16,389 would
have deleted ~12,790 rows of real captured coverage.** This is exactly why the task mandated on-disk re-verification
before dropping.

| step                     | value                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| consolidator PAUSED      | `gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-tradfi-cron --location asia-northeast1` (verified PAUSED)                                                                                                                                                                                                                                                                                                                                     |
| consolidator RESUMED     | `gcloud scheduler jobs resume …` (verified ENABLED `*/1`)                                                                                                                                                                                                                                                                                                                                                                                                             |
| snapshot                 | `_index/snapshots/pre_manifest_surgical_cleanup_20260720T200716Z.parquet` (gen `1784578000150929`, 5,209,585 rows)                                                                                                                                                                                                                                                                                                                                                    |
| (b) massive dropped      | **686,005** (`pipeline_mode==batch_massive`; GCS re-verified 0 objects across 12 sampled days 2020→2026)                                                                                                                                                                                                                                                                                                                                                              |
| (a) TRUE phantom dropped | **3,615** (db-captured L1 rows in the 3,413 disk-verified zero-object shards; NOT the contaminated 16,389)                                                                                                                                                                                                                                                                                                                                                            |
| rows                     | 5,209,585 → **4,519,965** (−689,620)                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| CAS write                | `if_generation_match=1784578000150929` → new gen `1784578157569319`; `schema_version` preserved **int64** (unique=[9])                                                                                                                                                                                                                                                                                                                                                |
| markers                  | `consolidator_content_write_at` PRESERVED (18:41:37 → next cycle no-op), `consolidator_run_at` refreshed (20:09:00)                                                                                                                                                                                                                                                                                                                                                   |
| durability               | `_legacy_seed` is EXCLUDED from every merge path when a canonical exists (`manifest_consolidator.py:783,873-875`); watched **2 post-resume cycles** (20:11:43Z + 20:12:37Z) — both `verdict=empty, shards_changed=0, rows_added=0, error_reason=""`; post-cycle index re-verified **4,519,965 rows, residual batch_massive=0, schema_version int64**, stall_state `streak=0`, only `_legacy_seed` in `per_vm/` — NO resurrection, NO `ManifestConsolidatorStaleError` |

capture_status deltas reconcile exactly: `captured −679,609` (675,994 massive + 3,615 phantom), `empty_confirmed −9,541`
(massive), `attempted_failed −470` (massive), `expected_unattempted` unchanged.

**(c)/(d) SCOPED FOLLOW-UP (not forced — provably entangled, and largely already resolved):**

- **(d) is ~91% `-USD@LIN` ALREADY** (the "0.0%" baseline below was measured pre-migration; the canonical-path migration
  has since landed canonical ids). Post-drop derivatives are **91.08% `-USD@LIN`**; the residual ~9% is `instrument_id`
  in `'ticks'`/blank form.
- **(c)'s real defect is small.** Of the 35.5% blank `instrument_id`, **1,765,757 are legitimate Option-A bundle/chain
  atoms keyed by `underlying`** (NOT defects, per contract). The genuine blank-no-underlying defect is **~82,032 rows
  (1.8%)**.
- **Why not forced now:** `instrument_id` is in `_OPTIONAL_DEDUP_COLS` (`manifest_consolidator.py:522-536`), so the
  object-walk re-derivation (`rebuild_tradfi_manifest.py`) writes rows with a DIFFERENT dedup key than the
  blank/`'ticks'` rows — a merge would ADD canonical rows ALONGSIDE the defective ones (or double-count), NOT flip them.
  Fixing (c)/(d) therefore requires the object-walk rebuild PLUS a second surgical drop of the superseded
  blank/`'ticks'` rows — a separate, heavier operation partly already covered by the in-flight catalogue rebuild + the
  expected-universe-v2 enumerator. Tracked as the follow-up todo below.

## Measured post-purge manifest baseline (live `_index/availability_index.parquet`, 2026-07-20)

Total rows **5,209,585**:

> ⚠️ This baseline is the ORIGINAL first-pass measurement. See the ✅ RESOLVED section above for the CORRECTED numbers:
> (a) the real phantom count is **3,615**, not 16,389 (the 16,389 was contaminated with 12,790 real-data rows — proven
> by on-disk re-verification); (d) is already **~91% `-USD@LIN`** (this "0.0%" was a pre-migration measurement).

| defect                                                                      | measured (first pass)          | corrected (disk-verified) | target |
| --------------------------------------------------------------------------- | ------------------------------ | ------------------------- | ------ |
| (a) phantom `batch_databento` trades/tbbo `captured` (zero backing objects) | ~~16,389~~                     | **3,615** (dropped)       | 0      |
| (b) `pipeline_mode=batch_massive` rows (objects now purged)                 | **686,005**                    | 686,005 (dropped)         | 0      |
| (c) blank `instrument_id` share                                             | **35.5%**                      | 82,032 real (1.76M legit) | ↓      |
| (d) derivative rows in canonical `-USD@LIN` form                            | ~~0.0%~~ (stale pre-migration) | **91.08%**                | ↑      |

## The gap — a force-rebuild does NOT drop (a) or (b)

`unified_trading_library/manifest_consolidator.py:844-875` (`consolidate(force=True)`): a full rebuild window-dedups the
canonical + every per-VM shard, and `canon_read` re-scans **100% of the canonical's CURRENT state**. The code comment
(`:850-862`, `legacy_seed_captured_outranks_resurrection_risk_2026_07_15`) is explicit:

> a DELETION correction — when a row is removed from the canonical entirely (not flipped to a different status) … there
> is no competing row left for any tie-break to apply to: … the row is simply the ONLY row for that key on the next full
> rebuild, so it survives trivially.

So the 686,005 massive rows and 16,389 phantom `captured` rows — which must be DROPPED (massive) or DEMOTED (phantom
captured → empty_confirmed) — are NOT removed by `consolidate(force=True)`. `rebuild_tradfi_manifest.py` also does not
drop them: it writes ADDITIVE per-VM shards (captured-from-disk + CF-11 honest-absence re-emit of empty/failed rows
only), which the consolidator MERGES with the stale canonical.

## What actually fixes each defect

- **(a) phantom captured → empty_confirmed**: a STATE-FLIP (captured → non-captured) IS honored by the consolidator's
  captured-outranks demotion (a newer non-captured row for the same key beats a stale captured claim). So writing
  competing `empty_confirmed` rows for the 16,389 phantom keys via a per-VM shard works — OR surgical in-place re-stamp.
- **(b) drop 686,005 massive rows**: a DELETION, which the consolidator resurrects. Requires **surgical removal from the
  canonical parquet** (drop `pipeline_mode=batch_massive` rows) with the consolidator PAUSED (the 2026-07-15 Part-2 fix
  excludes `_legacy_seed` on force when a canonical exists, so once removed they stay removed across cycles — provided
  no shard re-adds them).
- **(c)/(d) id canonicalization**: the surgical drop/re-stamp does NOT touch ids — a projection confirms (c) actually
  rises to 37.3% after dropping massive. Lowering blank-id and producing `-USD@LIN` requires the **object-walk
  re-derivation** (`rebuild_tradfi_manifest.py` over the post-migration canonical disk paths, which carry the `-USD@LIN`
  ids), then a consolidation that lets those rows win their shard atoms.

## VERIFIED non-destructively (projection)

A local projection over the downloaded canonical (drop `batch_massive`; re-stamp the 16,389 phantom captured →
`empty_confirmed`) yields **(a) 0, (b) 0**, rows 5,209,585 → 4,523,580. Artifact:
`/tmp/tradfi_index_corrected_projection.parquet` (local, not applied). (c)/(d) unchanged by this projection — they need
the object-walk rebuild.

## Why this is coordinate-before-cutover (not a blind run)

- The live `_index` is rewritten by the **manifest consolidator every minute** (Cloud Scheduler `*/1`), and a **peer is
  actively rebuilding the tradfi manifest** (`unified-trading-pm@384f0345a` — "/data-pipeline-check-mtds … blocked only
  on a fresh consolidator run; 2025d rebuild HANGING on the redundant re-emit"; `mtds@ac051bfe` — "stamp tradfi
  schema_version int64 not string"). Concurrent writes to the same `_index` are the exact
  `reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12` incident class.
- The correct live procedure (SSOT `manifest-consolidator-ssot.md` § "Full / --force rebuild"): pause the tradfi tick
  consolidator Cloud Scheduler cron → snapshot the canonical → apply (surgical drop/re-stamp for a/b + object-walk
  rebuild for c/d) → verify → resume. Pausing a shared prod cron + colliding with an in-flight peer rebuild is a
  coordinate-and-announce action, per the operator's Phase-3 instruction.

## Follow-up todos

- [x] [BACKEND] P0. ✅ Applied the surgical drop(batch_massive)+drop(TRUE-phantom) for (a)+(b) with the consolidator
      PAUSED + canonical snapshotted + CAS write (`if_generation_match`), disk-verifying every candidate phantom shard
      first (caught 12,790 contaminated rows). Watched 2 clean no-op cycles post-resume; index 5,209,585→4,519,965,
      massive=0, schema_version int64. — `market-data-tick-tradfi` `_index` gen `1784578157569319`, 2026-07-20T20:09Z
      (slot-1).
- [ ] [BACKEND] P1. (c)/(d) object-walk id re-derivation follow-up: `rebuild_tradfi_manifest.py` over post-migration
      disk paths to land `-USD@LIN` for the residual ~35k `'ticks'`/blank derivative rows + reduce the ~82k
      blank-no-underlying ids. **NOT a simple merge-flip**: `instrument_id` ∈ `_OPTIONAL_DEDUP_COLS`, so re-derived rows
      carry a NEW dedup key and land ALONGSIDE the defective rows — the rebuild must be paired with a second surgical
      drop of the superseded blank/`'ticks'` rows under a paused consolidator (same recipe as (a)/(b)). Largely mooted
      by the in-flight catalogue rebuild + expected-universe-v2 enumerator; measure before doing. (repo:
      market-tick-data-service)
- [ ] [BACKEND] P1. Add a manifest-vs-disk consistency check so a `captured` row with no object on disk fails loudly
      (prevents the phantom-row class recurring — this exact class produced BOTH the 3,615 real phantoms AND the
      contaminated 16,389 list). (repo: market-tick-data-service)
- [x] [DOCS] P1. ✅ The deletion-resurrection gap is intended behaviour; dropping rows requires surgical removal under a
      paused consolidator (force-rebuild is insufficient) — the `_legacy_seed` merge-exclusion
      (`manifest_consolidator.py:783,873-875`) makes a surgical drop durable. Documented here + in the codex SSOT §
      "Surgical row removal". (codex/05-infrastructure/manifest-consolidator-ssot.md)
