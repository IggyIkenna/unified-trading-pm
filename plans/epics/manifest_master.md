---
doc_type: epic
title: Manifest Master (L1)
summary:
  L1 epic owning manifest schema (v9 current, MANIFEST_SCHEMA_VERSION=9, adds source column) + evolution discipline +
  honest-absence taxonomy + backfill execution (Stages 0-4) + GCS layout + IS↔MTDS contract; enforces the 3-axis batch
  invariant (schema + writer code + on-disk GCS layout land together) over the SOURCE-AWARE
  {mode}_{source}[_{transport}] partition.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, execution-service, features-service, instruments-service, ml-service]
scope: [engineer, admin]
tags: [manifest, data-status, honest-coverage, backfill, pipeline-mode, single-walk, canonicalisation, data-correctness]
related:
  [
    ../archive/2026_05/bucket_name_ssot_canonicalisation_2026_05_10.md,
    ../archive/2026_05/d3_manifest_v8_finish_2026_05_20.md,
    ../archive/2026_05/d5_features_missing_data_downgrade_2026_05_20.md,
    ../archive/expected_unattempted_propagation_chain_2026_05_12.plan.md,
    ../archive/2026_05/gate_3_phantom_audit_runbook_2026_05_13.md,
    ../archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md,
    ../archive/2026_05/honest_coverage_formula_consolidation_2026_05_19.md,
    ../archive/2026_05/manifest_cross_asset_rescan_design_2026_05_08.md,
    ../archive/2026_05/manifest_schema_final_gate_2026_05_09.md,
  ]
created: 2026-05-21
name: manifest_master
tier: L1
priority: P0
assigned_vm: vm-defi
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md
  - ../active/data_completion_cefi_2026_07_15.md
  - ../active/data_completion_cefi_2026_07_15_finalize_2026_07_27.md
  - ../active/data_completion_defi_2026_07_15.md
  - ../active/data_completion_prediction_2026_07_15.md
  - ../active/data_completion_sports_2026_07_24.md
  - ../active/data_completion_tradfi_2026_07_15.md
  - ../active/data_pipeline_reconciliation_skill_2026_07_20.md
  - ../active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md
  - ../active/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04_finalize_2026_08_09.md
  - ../active/defi_migration_audit_log_2026_07_24.md
  - ../active/defi_venue_lst_rates_residual_2026_07_24.md
  - ../active/infra_ops_residual_migration_verification_2026_07_24.md
  - ../active/is_catalogue_g1_root_audit_log_2026_07_24.md
  - ../active/master_data_canonicalisation_migration_catalogue_2026_06_07.md
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Manifest Master (L1)

**Owns**: manifest schema (**v9 current** — `MANIFEST_SCHEMA_VERSION = 9` live 2026-05-30, UTL@`c7bfa427`; v9 adds the
`source` column per `tradfi_massive_dual_source_2026_05_28` Phase 3; the historical Stage 0-4 / `d3_manifest_v8_finish`
content below is the v8-era backfill window, kept as provenance. SSOT:
[`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) §
schema-version history) + evolution discipline + honest absence taxonomy + backfill execution (Stages 0-4) + GCS data
layout + IS↔MTDS contract enforcement. The 3-axis batch invariant: every manifest schema change + every writer code
change + every on-disk GCS data layout change MUST land together at one of this epic's gates. **Partition is
SOURCE-AWARE `{mode}_{source}[_{transport}]`** (`pipeline-mode-partition.md`).

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

- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
- [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md)
- [`/codex/02-data/manifest-migration-coordination.md`](/codex/02-data/manifest-migration-coordination.md)
- [`/codex/02-data/service-output-emission-semantics.md`](/codex/02-data/service-output-emission-semantics.md)

## Composition with other epics

- **Upstream gates**: `instruments_master` (IS→MTDS contract; archive-metadata fields on `InstrumentRecord`),
  `mtds_mdps_master` (writer code axis — MTDS handlers consume IS catalogue)
  > **[2026-07-12 correction, finding 322, §A2 B-queue]**: `manifest_evolution_SUPERSEDED_2026_05_21.md`'s supersession
  > banner claims "IS↔MTDS contract enforcement" (incl. its folded child
  > `plans/audit/is_mtds_contract_audit_2026_05_20.md`) "continues" in this epic, but that child plan's own frontmatter
  > still declares `parent_epic: manifest_evolution_SUPERSEDED_2026_05_21` (never re-homed here) and it does not appear
  > in this epic's "Assigned active plans" section — it is orphaned between the "upstream gate owned by
  > instruments_master" framing above and the dead epic's promise. Not fixed here (re-homing the child plan's
  > frontmatter is out of this chunk's file scope).
- **Downstream consumers**: All L0 asset-group epics (defi/cefi/tradfi/sports/predictions read manifest for data
  completeness gates); `features_and_ml_master` (features `available_at` lookahead-bias guard reads manifest)
- **Co-located VM**: `defi_master` (manifest backfill priority work)
- **Cross-cutting**: `batch_live_symmetry_master` (manifest is the data-completeness SSOT batch=live gates against);
  `observability_master` (manifest divergence alerts)

## Assigned active plans

_15 active plans declare `parent_epic: manifest_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28`](../active/cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: CeFi E4→E8 orphan-sweep + legacy gap-fill +
manifest rebuild — VM execution chain

### [`data_completion_cefi_2026_07_15`](../active/data_completion_cefi_2026_07_15.md)

**status**: active · **estimate**: 2 cal AI-days (class: infra) **title**: Data completion to 100% — CeFi manifest
canonicalisation + backfill (split from M-1)

### [`data_completion_defi_2026_07_15`](../active/data_completion_defi_2026_07_15.md)

**status**: active · **estimate**: 2 cal AI-days (class: infra) **title**: Data completion to 100% — DeFi manifest
canonicalisation + backfill (split from M-1)

### [`data_completion_prediction_2026_07_15`](../active/data_completion_prediction_2026_07_15.md)

**status**: active · **estimate**: 2 cal AI-days (class: infra) **title**: Data completion to 100% — Prediction manifest
canonicalisation + backfill (split from M-1)

### [`data_completion_sports_2026_07_24`](../active/data_completion_sports_2026_07_24.md)

**status**: active · **estimate**: 2 cal AI-days (class: infra) **title**: Data completion to 100% — Sports manifest
canonicalisation + backfill (parity sibling of M-1)

### [`data_completion_tradfi_2026_07_15`](../active/data_completion_tradfi_2026_07_15.md)

**status**: active · **estimate**: 2 cal AI-days (class: infra) **title**: Data completion to 100% — TradFi manifest
canonicalisation + backfill (split from M-1)

### [`data_pipeline_reconciliation_skill_2026_07_20`](../active/data_pipeline_reconciliation_skill_2026_07_20.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: design) **title**: /data-pipeline-reconciliation —
per-asset-group four-surface canonicalisation reconciliation skill

### [`defi_migration_audit_log_2026_07_24`](../active/defi_migration_audit_log_2026_07_24.md)

**status**: active · **estimate**: 0.6 cal AI-days (class: design)

### [`defi_venue_lst_rates_residual_2026_07_24`](../active/defi_venue_lst_rates_residual_2026_07_24.md)

**status**: active · **estimate**: 0.6 cal AI-days (class: design) **title**: DeFi venue hygiene + lst-rates aggregation
residual — forked from migration_verification_orphan_safety_2026_06_10

### [`infra_ops_residual_migration_verification_2026_07_24`](../active/infra_ops_residual_migration_verification_2026_07_24.md)

**status**: active · **estimate**: 1.8 cal AI-days (class: design) **title**: Infra/ops residual tail — forked from
migration_verification_orphan_safety_2026_06_10

### [`is_catalogue_g1_root_audit_log_2026_07_24`](../active/is_catalogue_g1_root_audit_log_2026_07_24.md)

**status**: active · **estimate**: 0.6 cal AI-days (class: design)

### [`master_data_canonicalisation_migration_catalogue_2026_06_07`](../active/master_data_canonicalisation_migration_catalogue_2026_06_07.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: design)

## P1 — important; post-current-gate

### [`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04`](../active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md)

**status**: active · **estimate**: 3.6 cal AI-days (class: refactor) **title**: >-

## P2 — useful; opportunistic

### [`data_completion_cefi_2026_07_15_finalize_2026_07_27`](../active/data_completion_cefi_2026_07_15_finalize_2026_07_27.md)

**status**: active · **estimate**: 0.2 cal AI-days (class: infra) **title**: >-

## P3 — backlog; revisit quarterly

### [`defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04_finalize_2026_08_09`](../active/defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04_finalize_2026_08_09.md)

**status**: active · **estimate**: 0.16 cal AI-days (class: infra) **title**: >-

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

- [ ] [AGENT] P2. **[2026-07-12 correction]** `ManifestWriter.add` is a LIVE, actively-extended write path, NOT
      dead/soft-deprecated code awaiting a grep-confirm-then-delete (was: "Design and land a successor plan for full
      `ManifestWriter.add` deletion: that method was soft-deprecated in the wave-2 plan (Phase 3 swapped all call sites
      to `record_captured`/`record_empty`)... grep workspace for any remaining `.add(` call sites → confirm 0 remaining
      callers → delete `ManifestWriter.add`" — false premise). Re-verified 2026-07-12: 4 live non-test call sites in
      market-tick-data-service — `market_tick_data_service/scripts/_rebuild_sports_write.py:187`,
      `market_tick_data_service/scripts/_rebuild_cefi_cf11.py:184`,
      `market_tick_data_service/cli/handlers/_defi_manifest.py:474`,
      `market_tick_data_service/scripts/rebuild_defi_manifest.py:478` — and this exact last call site was actively
      enhanced as recently as M-COORD-5 (mtds@f80c50f1, per
      `active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`: writer.add(...) now passes
      asset_group=defi + the source-aware pipeline_mode/source/transport). **MIGRATED FROM:
      plans/archive/wave2_polymarket_record_captured_from_counts_2026_05_09.md Phase 4.** Corrected todo: any future
      deletion of `ManifestWriter.add` must first migrate these 4 live call sites to `record_captured`/`record_empty` —
      do not merely grep-confirm zero callers, there are non-zero callers today. Corrected per plan-reconciliation
      finding 137, `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified"
      blanket ruling.

> **MIGRATED FROM:** `bucket_name_ssot_canonicalisation_2026_05_10.md` (archived 2026-05-23) — bucket naming SSOT
> complete for DeFi/CeFi/core paths; remaining items are env-tiered migration + prediction bucket + workspace audit.

- [ ] [OPERATOR+AGENT] P1. **Phase 0d — migrate flat-bucket data into env-tiered buckets** (DEFERRED-OPERATOR-DECISION)
      — operator must approve the migration date + window before execution. Flat-bucket data still in
      `unified-trading-defi-*` style buckets; env-tiered target is `uts-prod-defi-*`. Full migration playbook in
      `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0d.
- [x] ✅ [OPERATOR+AGENT] P2. **DONE 2026-07-27 (slot-11).** **Prediction bucket naming migration** — verified, not just
      grep-confirmed. The legacy prediction buckets (`market-data-tick-prediction-*`, `instruments-store-prediction-*`)
      are already purge-deleted (`plans/active/legacy_bucket_dual_write_decommission_2026_07_24.md` — "prediction: ✅
      DONE 2026-07-13", both live + noncurrent versions removed, confirmed 404). A fresh grep of
      market-tick-data-service + instruments-service found every LIVE production code path (`reader.py`,
      `live/websocket_runner.py`, `engine/orchestrator/__init__.py`, `market_interface/adapters/prediction/*`,
      `cli/handlers/websocket_streaming_handler.py`, `instruments_service/engine/orchestrator/catalogue.py`) already
      routes through `resolve_bucket_name(kind="market-data-tick-prediction"/"instruments-store-prediction", ...)` per
      STEP 5.69 — the dedicated flat-kind pattern, by design (see `catalogue.py`'s `resolve_instruments_store_kind()`
      docstring). The only remaining raw legacy-bucket-name literals are confined to dated one-off
      migration/reconciliation/purge scripts under `scripts/*_2026_0[5-7]_*.py` (e.g.
      `migrate_prediction_to_pred_prd_v9.py`, `purge_prediction_index_final_residuals_2026_07_11.py`) whose entire
      purpose was migrating away from / auditing / purging that now-deleted legacy bucket — expected historical residue
      of already-completed one-off tooling (source plan `prediction_manifest_canonicalisation_2026_06_01.md` E7/E8/E8b,
      also DONE), not an open migration gap. No operator decision needed — the migration itself is already complete.
      Source: `plans/archive/2026_07/prediction_satellite_ao_dispatch_batch2_2026_07_25.md` todo 1.
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
