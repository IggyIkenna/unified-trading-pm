---
title: "Hyperliquid cefi data stranded on retired pipeline_mode=batch_hyperliquid_rest — missed by the v9 migration"
created: 2026-06-17
author: ikennaigboaka [slot-1·laptop]
status: active
priority: P2
locked_by: live-defi-rollout
source:
  - 2026-06-17 carry_staked_basis harness work — verifying HL funding read path surfaced the stranded pipeline_mode
parent_epic: mtds_mdps_master
---

# Hyperliquid cefi data stranded on `batch_hyperliquid_rest` (missed by v9 migration)

## What I found

Operator R4 (2026-06-07) retired the glued-transport `hyperliquid_rest` pipeline_mode → canonical
`pipeline_mode=batch_hyperliquid` (vendor only) with `transport=rest` as a separate manifest column
(`default_transport_for_source`). The **code** is fully on the canonical form (UAC `PipelineMode` has no
`*_HYPERLIQUID_REST` members; zero active emitters of a glued literal fleet-wide; new writes go to `batch_hyperliquid`).

**But the on-disk DATA was never migrated, and the rename is in NO v9 migration script** (verified 2026-06-17 — grep for
`hyperliquid_rest` across `market_tick_data_service/scripts/migrate_*_v9*.py` = zero hits):

- GCS `market-data-tick-cefi-prd-central-element-323112`, `asset_group=cefi`, `venue=HYPERLIQUID` — **two data_types
  still under `pipeline_mode=batch_hyperliquid_rest`**: `derivative_ticker` AND `book_snapshot_5` (probed
  day=2026-04-01).
- **Zero** cefi HL objects on the canonical `pipeline_mode=batch_hyperliquid`.
- Live manifest distribution (r3 verdict_cefi 2026-06-17): `batch_hyperliquid_rest` **19.4K** objects still keyed on the
  retired literal (the `batch_hyperliquid` 49.5K is the SEPARATE defi/perp_funding dataset, not this).
- The standardisation plan (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`) does NOT track this
  specific cefi-HL object migration — its "BREAKING object migration" tranche is the live/replay objects, not this.

## Why it matters

The cefi HL `derivative_ticker` (perp funding) + `book_snapshot_5` are stranded on a **retired** pipeline_mode literal.
Prefix-matching readers (`batch_hyperliquid*`, the documented convention) still read it (`batch_hyperliquid_rest`
prefix-matches `batch_hyperliquid`), so this is NOT silent data loss — but: (1) exact-literal consumers miss it (the
carry harness did, now fixed to read canonical-first + legacy-fallback at `e2e@8623c1c`); (2) the transport is glued
into the path instead of the `transport` column, violating the canonical convention; (3) the 19.4K stale-keyed objects
will keep tripping audits + confusing the canonical-form verifier until migrated.

## Recommended decision / todos

- [ ] [DATA] P2. **Add the `hyperliquid_rest → batch_hyperliquid` rename to the v9 migration**: a GCS object migration
      that, for `asset_group=cefi venue=HYPERLIQUID` under `pipeline_mode=batch_hyperliquid_rest` (data_types
      `derivative_ticker` + `book_snapshot_5` + any others), moves/rewrites objects to `pipeline_mode=batch_hyperliquid`
      and stamps `transport=rest` in the manifest column. Use the gcs_copy_object/gcs_delete_object path ops (250x
      faster than gsutil); single-walk discipline; pre-migration drain first. **Repo: market-tick-data-service +
      deployment-service.**
- [ ] [DATA] P2. Re-key the 19.4K manifest rows from `batch_hyperliquid_rest` → `batch_hyperliquid` (+ transport=rest)
      in the SAME walk. Verify the canonical-form auditor (`audit_canonical_form.py`) goes green for HL cefi after.
      **Repo: market-tick-data-service.**
- [ ] [DATA] P3. Once migrated, drop the transitional `hyperliquid_rest` read-tokens in UAC `possible_manifest.py`
      (POSSIBLE_SOURCES CEFI/DEFI) and remove the `_VENUE_DIR_LEGACY_PIPELINE_MODES` fallback in the carry harness.
      **Repo: unified-api-contracts + e2e-testing.**
- [ ] [DOCS] P3. Update the stale `BATCH_HYPERLIQUID_REST`/`hyperliquid_rest` refs in
      `codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`. **Repo: unified-trading-pm.**

Cross-link: `plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` (the R4 retirement SSOT
— this gap belongs to its completion).
