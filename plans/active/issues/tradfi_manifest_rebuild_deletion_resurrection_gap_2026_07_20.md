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

## Measured post-purge manifest baseline (live `_index/availability_index.parquet`, 2026-07-20)

Total rows **5,209,585**:

| defect                                                                      | measured                                | target |
| --------------------------------------------------------------------------- | --------------------------------------- | ------ |
| (a) phantom `batch_databento` trades/tbbo `captured` (zero backing objects) | **16,389**                              | 0      |
| (b) `pipeline_mode=batch_massive` rows (objects now purged)                 | **686,005**                             | 0      |
| (c) blank `instrument_id` share                                             | **35.5%**                               | ↓      |
| (d) derivative rows in canonical `-USD@LIN` form                            | **0.0%** (bare roots: ETH, ZN, ES, ZB…) | ↑      |

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

- [ ] [BACKEND] P0. Coordinate with the in-flight peer tradfi-manifest rebuild; apply the drop(batch_massive) +
      re-stamp(phantom→empty_confirmed) surgery for (a)+(b) with the consolidator paused + canonical snapshotted, then
      the object-walk `rebuild_tradfi_manifest.py` for (c)+(d). Verify all four measured. (repo:
      market-tick-data-service)
- [ ] [BACKEND] P1. Add a manifest-vs-disk consistency check so a `captured` row with no object on disk fails loudly
      (prevents the phantom-row class recurring). (repo: market-tick-data-service)
- [ ] [DOCS] P1. If the deletion-resurrection gap is intended behaviour, document that dropping rows from the manifest
      requires surgical removal under a paused consolidator (a force-rebuild alone is insufficient).
      (codex/05-infrastructure/manifest-consolidator-ssot.md)
