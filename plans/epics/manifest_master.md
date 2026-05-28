---
name: manifest_master
title: "Manifest Master (L1)"
type: epic
tier: L1
status: active
priority: P0
assigned_vm: vm-defi
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md
  - ../archive/2026_05/d3_manifest_v8_finish_2026_05_20.md
  - ../archive/2026_05/d5_features_missing_data_downgrade_2026_05_20.md
  - ../archive/expected_unattempted_propagation_chain_2026_05_12.plan.md
  - ../archive/2026_05/gate_3_phantom_audit_runbook_2026_05_13.md
  - ../archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md
  - ../archive/2026_05/honest_coverage_formula_consolidation_2026_05_19.md
  - ../archive/2026_05/manifest_cross_asset_rescan_design_2026_05_08.md
  - ../archive/2026_05/manifest_schema_final_gate_2026_05_09.md
---

# Manifest Master (L1)

**Owns**: manifest schema (v8 current; evolution discipline) + honest absence taxonomy + backfill execution (Stages
0-4) + GCS data layout + IS↔MTDS contract enforcement. The 3-axis batch invariant: every manifest schema change + every
writer code change + every on-disk GCS data layout change MUST land together at one of this epic's gates.

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
  (`_create_empty_output`, `_create_full_day_empty_output`, `_create_closed_market_candle`); MTDS reconcilers (1440-NaN,
  partial bundles); expected-absence backfill; raw-tables migration; cross-asset rescan with `--apply-flips`.
- **Stage 0 pre-migration drain** composes with `code_freeze_migrate_backfill_sequencing` (Phase 1 freeze gate).

Full archaeology: [`manifest_evolution_SUPERSEDED_2026_05_21.md`](manifest_evolution_SUPERSEDED_2026_05_21.md) +
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

_9 active plans declare `parent_epic: manifest_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## Assigned active plans

_9 active plans declare `parent_epic: manifest_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`d3_manifest_v8_finish_2026_05_20`](../archive/2026_05/d3_manifest_v8_finish_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases 1-3 done (100% v8 dist confirmed); Phase 4 BLOCKED-OPERATOR-DECISION (765
DIVERGENT_EMPTY → D4 resolution) · **estimate**: 2.4 cal AI-days (class: infra) **title**: D3 — Manifest v8 finish +
reason-enum wiring + divergence-detector

### [`d5_features_missing_data_downgrade_2026_05_20`](../archive/2026_05/d5_features_missing_data_downgrade_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases 0-1 done; P1 ml-service item DEFERRED → `ml_service_hardening_2026_06_01.md`

### [`expected_unattempted_propagation_chain_2026_05_12`](../archive/expected_unattempted_propagation_chain_2026_05_12.plan.md)

**status**: ✅ ARCHIVED 2026-05-21 — runtime propagation code complete (Phases 0-5 shipped); production validation
pending Phase 3 MTDS run window per `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`

### [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases 1-7 done; Phase 8 DEFERRED-writegate-6.x (2026-06-15 date-gate) ·
**estimate**: 4.8 cal AI-days (class: infra)

### [`honest_coverage_formula_consolidation_2026_05_19`](../archive/2026_05/honest_coverage_formula_consolidation_2026_05_19.md)

**status**: ✅ ARCHIVED 2026-05-23 — All 26 todos done. `compute_honest_coverage` consolidated + UTL published +
MDPS/IS/deployment-api migrated. Tier-3 sentinel propagation →
`expected_unattempted_validation_pending_phase3_2026_05_19.md`. Baseline script → `master_to_live_defi_2026_05_23.md`
Group H. · **estimate**: 2.4 cal AI-days (class: refactor)

### [`manifest_schema_final_gate_2026_05_09`](../archive/2026_05/manifest_schema_final_gate_2026_05_09.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 0-9 + schema code complete (v8 writer-path shipped). Phases 10-13 require
operator GCS VM execution (backfill runs, paper-trade smoke, live cutover). · **estimate**: 2.1 cal AI-days (class:
design)

## P1 — important; post-current-gate

### [`manifest_cross_asset_rescan_design_2026_05_08`](../archive/2026_05/manifest_cross_asset_rescan_design_2026_05_08.md)

**status**: ✅ ARCHIVED 2026-05-21 · **estimate**: 2.4 cal AI-days (class: infra)

## P2 — useful; opportunistic

### [`bucket_name_ssot_canonicalisation_2026_05_10`](../archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 0a/0b/0c/0e/L1/L2-non-service complete. 13 service-code legacy delegate rows
remain DEFERRED (BLOCKED-PHASE-2.6 or BLOCKED-UTL-MIGRATION). · **estimate**: 10.0 cal AI-days (class: refactor)

### [`gate_3_phantom_audit_runbook_2026_05_13`](../archive/2026_05/gate_3_phantom_audit_runbook_2026_05_13.md)

**status**: ✅ ARCHIVED 2026-05-21 — Gate 3 FIRED 2026-05-17; 0 phantoms all 5 asset_groups · **estimate**: 0.8 cal
AI-days (class: infra)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_

## Archived plans

### [`bucket_name_ssot_canonicalisation_2026_05_10`](../archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 0a/0b/0c/0e/L1/L2-non-service complete.

**Deferred (migrated):**

- **L2 dependency_checker.py probe templates** (ml-inference × 2, execution-service × 5, features-service × 16):
  BLOCKED-UTL-MIGRATION. Must land in same window as flat→env-tiered data migration.
- **L3 legacy UTL `get_bucket_name` consumers** (instruments-service × 4, pnl-attribution × 2, execution-service × 1,
  UTL × 1, deployment-service × 3): BLOCKED-PHASE-2.6. Must flip during write-pause window.
- **L5 deployment-api internal templates** (`DataStatusService._BUCKET_TEMPLATES`, 3 shapes +
  `upcoming_fixtures._SPORTS_BUCKET_TEMPLATE` + 3 f-strings): BLOCKED-PHASE-2.6. Must flip in lockstep with data
  migration.

## Deferred work — migrated from archived plans

- [ ] [AGENT] P2. **MIGRATED FROM: plans/archive/wave2_polymarket_record_captured_from_counts_2026_05_09.md Phase 4** —
      Design and land a successor plan for full `ManifestWriter.add` deletion: that method was soft-deprecated in the
      wave-2 plan (Phase 3 swapped all call sites to `record_captured` / `record_empty`), but the method body was not
      deleted because the plan lacked a dedicated "deletion + 1-cycle deprecation" successor. Successor plan should:
      grep workspace for any remaining `.add(` call sites → confirm 0 remaining callers → delete `ManifestWriter.add` →
      update codex `availability-manifest-and-data-status.md` to mark the method removed.

> **MIGRATED FROM:** `bucket_name_ssot_canonicalisation_2026_05_10.md` (archived 2026-05-23) — bucket naming SSOT
> complete for DeFi/CeFi/core paths; remaining items are env-tiered migration + prediction bucket + workspace audit.

- [ ] [OPERATOR+AGENT] P1. **Phase 0d — migrate flat-bucket data into env-tiered buckets** (DEFERRED-OPERATOR-DECISION)
      — operator must approve the migration date + window before execution. Flat-bucket data still in
      `unified-trading-defi-*` style buckets; env-tiered target is `uts-prod-defi-*`. Full migration playbook in
      `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0d.
- [ ] [OPERATOR+AGENT] P2. **Prediction bucket naming migration** (DEFERRED-OPERATOR-DECISION) — prediction service uses
      legacy bucket naming pattern; migrate to `resolve_bucket_name()` pattern per STEP 5.69. Requires operator decision
      on migration window + dry-run first.
- [ ] [AGENT] P2. **Workspace-grep audit for legacy bucket references** — run workspace-wide grep to verify zero inline
      `gs://` f-strings remain after bucket SSOT rollout. Generate audit table confirming all call sites use
      `resolve_bucket_name()`. Update QG ratchet baseline.
- [ ] [AGENT] P2. **Legacy bucket rename delegation** — delegate any remaining legacy bucket renames to the appropriate
      service-repo owners. Confirm each service's QG STEP 5.69 check is green.

> **MIGRATED FROM:** `manifest_schema_final_gate_2026_05_09.md` (archived 2026-05-23) — v8 schema design complete;
> Phases 8-13 are execution gates tracked in mtds_mdps_master + master plan.

- [ ] [OPERATOR] P1. **Phase 0.A+0.B pre-audit** — run `gcs_migration Phase 0` pre-audit on same-region test bucket +
      `measure-honest-coverage.py` on production manifests for each asset_group before full migration execution. Human
      sign-off required before Phase 9 VM launches.
- [ ] [AGENT] P2. **Phase 4.DEFAULT-REMOVAL-v8kwargs** — remove `= None` defaults from v8 schema kwargs across UTL
      `ManifestWriter` + UAC schema definitions; enforce required fields. Low urgency once v8 migration runs are
      complete.
- [ ] [OPERATOR] P1. **Phase 8.A+8.B sign-off** — operator reviews class-C triage rows + appends sign-off section to
      `manifest_divergence_triage_2026_05_09.md` confirming production manifest state post-migration.
