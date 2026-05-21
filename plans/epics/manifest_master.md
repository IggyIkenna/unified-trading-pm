---
name: manifest_master
type: epic
tier: L1
status: active
priority: P0
assigned_vm: vm-defi
parent: master_to_live_defi_2026_05_23
owner: ikenna
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
asset_group: cross-cutting
related_plans:
  - ../active/bucket_name_ssot_canonicalisation_2026_05_10.md
  - ../active/d3_manifest_v8_finish_2026_05_20.md
  - ../active/d5_features_missing_data_downgrade_2026_05_20.md
  - ../active/expected_unattempted_propagation_chain_2026_05_12.md
  - ../active/gate_3_phantom_audit_runbook_2026_05_13.md
  - ../active/gcs_migration_bundle_pipeline_mode_2026_05_08.md
  - ../active/honest_coverage_formula_consolidation_2026_05_19.md
  - ../active/manifest_cross_asset_rescan_design_2026_05_08.md
  - ../active/manifest_schema_final_gate_2026_05_09.md

---

# Manifest Master (L1)

**Owns**: manifest schema (v8 current; evolution discipline) + honest absence taxonomy + backfill execution (Stages 0-4) +
GCS data layout + IS↔MTDS contract enforcement. The 3-axis batch invariant: every manifest schema change + every writer
code change + every on-disk GCS data layout change MUST land together at one of this epic's gates.

**Assigned VM**: `vm-defi` (co-located with `defi_master` — manifest backfill is the primary DeFi pain).

## Scope inherited from `manifest_evolution_SUPERSEDED_2026_05_21` + `manifest_migration_SUPERSEDED_2026_05_21` (consolidated 2026-05-21)

Two pre-2026-05-21 masters were consolidated into this single everlasting epic:

### From `manifest_evolution_SUPERSEDED` (schema + writer code + GCS data layout co-evolve)

3-axis batch invariant:
1. **Schema axis** — UAC `honest_coverage` declarations + manifest parquet column shape + closed-set enums
   (`EMPTY_CONFIRMED_REASONS`, `BUNDLED_DATA_TYPES`, `ServiceEmissionPolicy`).
2. **Writer code axis** — UTL `ManifestWriter` (`record_captured` / `record_empty` / `record_failed` /
   `record_expected_unattempted`), per-adapter callsites, `assert_available_at_present`, cluster validation kwargs, QG
   STEP 5.64 + 5.66.
3. **GCS data layout axis** — on-disk parquet partitions (`pipeline_mode=` hive key, `asset_group=` canonical key),
   per-VM shard partitions, manifest consolidator output.

Drift between any two axes = silent correctness bug. Banned: isolated execution on one axis.

### From `manifest_migration_SUPERSEDED` (Stage 0-4 backfill execution)

- **Stage 0** — Pre-migration VM drain + state freeze (BOTH GCP + AWS VM fleets). Manifest consolidator final run +
  snapshot to `_index/snapshots/pre_migration_<date>.parquet`. Operator-enforced lock.
- **Stages 1-4** — `data_available_at` sports atomic 4-repo source rename; MDPS placeholder method deletion
  (`_create_empty_output`, `_create_full_day_empty_output`, `_create_closed_market_candle`); MTDS reconcilers
  (1440-NaN, partial bundles); expected-absence backfill; raw-tables migration; cross-asset rescan with `--apply-flips`.
- **Stage 0 pre-migration drain** composes with `code_freeze_migrate_backfill_sequencing` (Phase 1 freeze gate).

Full archaeology:
[`manifest_evolution_SUPERSEDED_2026_05_21.md`](manifest_evolution_SUPERSEDED_2026_05_21.md) +
[`manifest_migration_SUPERSEDED_2026_05_21.md`](manifest_migration_SUPERSEDED_2026_05_21.md).

## Codex SSOTs

- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md)
- [`codex/02-data/manifest-migration-coordination.md`](../../codex/02-data/manifest-migration-coordination.md)
- [`codex/02-data/service-output-emission-semantics.md`](../../codex/02-data/service-output-emission-semantics.md)

## Composition with other epics

- **Upstream gates**: `instruments_master` (IS→MTDS contract; archive-metadata fields on `InstrumentRecord`),
  `mtds_mdps_master` (writer code axis — MTDS handlers consume IS catalogue)
- **Downstream consumers**: All L0 asset-group epics (defi/cefi/tradfi/sports/predictions read manifest for data
  completeness gates); `features_and_ml_master` (features `available_at` lookahead-bias guard reads manifest)
- **Co-located VM**: `defi_master` (manifest backfill priority work)
- **Cross-cutting**: `batch_live_symmetry_master` (manifest is the data-completeness SSOT batch=live gates against);
  `observability_master` (manifest divergence alerts)

## Assigned active plans

_9 active plans declare `parent_epic: manifest_master` in their frontmatter. Workers pick up in priority order (P0 first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`d3_manifest_v8_finish_2026_05_20`](../active/d3_manifest_v8_finish_2026_05_20.md)
**status**: active · **estimate**: 2.4 cal AI-days (class: infra)
**title**: D3 — Manifest v8 finish + reason-enum wiring + divergence-detector

### [`d5_features_missing_data_downgrade_2026_05_20`](../active/d5_features_missing_data_downgrade_2026_05_20.md)
**status**: active · **estimate**: 0.8 cal AI-days (class: refactor)
**title**: D5 — Features missing-data downgrade plan

### [`expected_unattempted_propagation_chain_2026_05_12`](../active/expected_unattempted_propagation_chain_2026_05_12.md)
**status**: active · **estimate**: 6.6 cal AI-days (class: brand-new)

### [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../active/gcs_migration_bundle_pipeline_mode_2026_05_08.md)
**status**: active · **estimate**: 4.8 cal AI-days (class: infra)

### [`honest_coverage_formula_consolidation_2026_05_19`](../active/honest_coverage_formula_consolidation_2026_05_19.md)
**status**: in-flight · **estimate**: 2.4 cal AI-days (class: refactor)

### [`manifest_schema_final_gate_2026_05_09`](../active/manifest_schema_final_gate_2026_05_09.md)
**status**: active · **estimate**: 2.1 cal AI-days (class: design)

## P1 — important; post-current-gate

### [`manifest_cross_asset_rescan_design_2026_05_08`](../active/manifest_cross_asset_rescan_design_2026_05_08.md)
**status**: done · **estimate**: 2.4 cal AI-days (class: infra)

## P2 — useful; opportunistic

### [`bucket_name_ssot_canonicalisation_2026_05_10`](../active/bucket_name_ssot_canonicalisation_2026_05_10.md)
**status**: active · **estimate**: 10.0 cal AI-days (class: refactor)

### [`gate_3_phantom_audit_runbook_2026_05_13`](../active/gate_3_phantom_audit_runbook_2026_05_13.md)
**status**: active · **estimate**: 0.8 cal AI-days (class: infra)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

