---
doc_type: epic
title: Manifest evolution master — single owner for schema + writer code + GCS data layout (3-axis batch invariant)
summary:
  SUPERSEDED (2026-05-21) manifest-evolution epic — the 3-axis batch invariant (schema + writer code + GCS data layout
  co-evolve at one gate) plus honest-absence taxonomy and IS↔MTDS contract enforcement consolidated into
  manifest_master.md; archaeology only, no new work here.
status: superseded
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, instruments-service]
scope: [engineer, admin]
tags: [manifest, honest-coverage, data-correctness, consolidation, pipeline-mode, migration]
related:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/manifest-migration-coordination.md,
  ]
created: 2026-05-08
name:
tier:
priority: P0
assigned_vm: vm-defi
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
deadline: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-08
folds_in:
  [
    writegate_honest_coverage_endtoend_2026_05_06,
    hard_schema_enforcement_2026_05_08,
    wave3x_residual_ssots_2026_05_08,
    expected_universe_v2_design_2026_05_08,
    manifest_schema_final_gate_2026_05_09,
    manifest_cross_asset_rescan_design_2026_05_08,
    gcs_migration_bundle_pipeline_mode_2026_05_08,
    honest_coverage_formula_consolidation_2026_05_19,
    is_mtds_contract_audit_2026_05_20,
  ]
companion_to: [available_at_lookahead_bias_completion_2026_05_08]
todos: []
isProject: false
---

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BLOCK)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../active/code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> pins this epic's gates to a strict time-axis order: **Phase 2 (G3-G5 schema + writer code + GCS data layout) cannot
> start until the sequencing plan's Phase 1 freeze gate fires.** Schema-axis enforcer (this plan) composes with
> time-axis enforcer (sequencing plan); both gate together. Anti-sequencing audit in the sequencing plan flags 13 plans
> by re-migration risk — reviewers reject any plan that lands manifest-schema-affecting scope after the Phase 2 freeze
> gate fires.

# Manifest evolution master — SUPERSEDED 2026-05-21

> **⚠️ SUPERSEDED-BY 2026-05-21**: This master was consolidated with `manifest_migration_master_SUPERSEDED_2026_05_21`
> into a single everlasting epic: [`manifest_master.md`](manifest_master.md) (L1, vm-defi).
>
> All open scope (schema v8, honest absence taxonomy, writer code, GCS data layout, IS↔MTDS contract enforcement)
> continues there. This file is kept as **archaeology only** — DO NOT add new work here. New active plans declare
> `parent_epic: manifest_master` in frontmatter. Full epic-flow SSOT: [`README.md`](README.md).
>
> **[2026-07-12 correction, finding 322, §A2 B-queue**
> (`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`)**]**: the "IS↔MTDS contract enforcement"
> folded child, `plans/audit/is_mtds_contract_audit_2026_05_20.md` (`status: in-flight`), does NOT actually declare
> `parent_epic: manifest_master` as this banner promises — its own frontmatter still points at this dead epic
> (`parent_epic: manifest_evolution_SUPERSEDED_2026_05_21`), and it is absent from `manifest_master.md`'s "Assigned
> active plans" roster and from its "Upstream gates" line (which instead frames "IS→MTDS contract" as owned by
> `instruments_master`). The work item is genuinely orphaned between the two framings — flagging here since re-homing
> its frontmatter is out of this fix's file scope (not part of this chunk).

# Manifest evolution master — schema + writer code + GCS data layout co-evolve (3-axis batch invariant) — archaeology

> **🟡 SINGLE-OWNER UMBRELLA — codified 2026-05-08.** Seven previously-isolated manifest-touching plans now batch
> through this umbrella's gates. Isolated execution is BANNED — see § "Banned anti-patterns" below. Operator direction:
> _"manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution; don't allow
> execution in isolation."_

## Why this plan exists

User direction (this session, verbatim):

> aggregate manifest schema evolution into an owner plan which is marked as the highest prio items together with any
> plans current or necessary to migrate GCS data into the structure that's gonna work for the manifest and updating the
> code to write in a way where if it was to write after all the changes it would write to the correct manifest
> structure. So the manifest, the code and the data is all migrated in the same group plan to avoid collision risk. And
> then you can look at all of those little places where all the details are written and force them to be executed in
> batch on the plan don't allow them to be executed in isolation.

Translation: every manifest schema change, every writer code change, and every on-disk GCS data layout change MUST land
together at one of this umbrella's gates. A plan that touches one axis without the other two is a review-blocker.

## Three-axis batch invariant

Three axes co-evolve. They MUST be at the same version before ANY axis advances:

1. **Schema axis** — UAC `unified_api_contracts.canonical.crosscutting.honest_coverage` declarations + manifest parquet
   column shape + closed-set enums (`EMPTY_CONFIRMED_REASONS`, `BUNDLED_DATA_TYPES`, `ServiceEmissionPolicy`, etc.).
   Source: child plans `writegate` Phase 2.E + `hard_schema_enforcement` + `manifest_v7_schema_migration_design` +
   `expected_universe_v2_design`.
2. **Writer code axis** — UTL `ManifestWriter` (`record_captured` / `record_empty` / `record_failed` /
   `record_expected_unattempted`), per-adapter callsites, `assert_available_at_present`, cluster validation kwargs, QG
   STEP 5.64 (callsite AST walk), QG STEP 5.66 (per-VM shard isolation). Source: child plans `writegate` Phase
   2.A/3.D.5 + `hard_schema_enforcement` Phase 5.
3. **GCS data layout axis** — on-disk parquet partitions (`pipeline_mode=` hive key, `asset_group=` canonical key),
   per-VM shard partitions, manifest consolidator output. Source: child plans `gcs_migration_bundle_pipeline_mode` +
   `manifest_cross_asset_rescan` (apply-flips against full manifest).

Drift between any two axes = silent correctness bug. The historical incidents that motivate this umbrella — TradFi MVP
partial bundle (2026-05-06), MDPS 1440-NaN bars (2026-05-05), 2026-05-04 instruments-service `00f6352` chunk worker
without per-VM shard isolation, 5-CeFi-VM RED ALERT 2026-05-07 with all-blank reasons — are all instances of two axes
advancing while the third lagged.

## Folded sub-plans

| Child plan                                                                                                            | Scope                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Status (2026-05-08)                                                                                                                                                                      | Gate(s) it lands in                                                                                                                                                                                  |
| --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.md)         | Reason taxonomy expansion (Phase 2.E) + cluster-validation guard (3.D.5) + ServiceEmissionPolicy slice (a) shipped UAC@58c3b61                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Wave 4 slice (a) shipped; slices (b)/(c) planned                                                                                                                                         | G1 (reason taxonomy) + G2 (cluster validation) + G7 (service emission policy + workspace audit)                                                                                                      |
| [`hard_schema_enforcement_2026_05_08`](../active/hard_schema_enforcement_2026_05_08.md)                               | QG STEP 5.66 AST guard + `SCHEMA_VALIDATION_FAILED` enum addition + workspace cluster-validation enforcement                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Draft                                                                                                                                                                                    | G2 (cluster validation) + G7 (workspace audit)                                                                                                                                                       |
| [`wave3x_residual_ssots_2026_05_08`](../active/wave3x_residual_ssots_2026_05_08.md)                                   | Tracks A (UAC `HALF_DAY_SESSIONS` + `EXPECTED_PARTIAL_HALF_DAY` reason) + D (zero-activity-bar audit per CLAUDE.md 4-category rule)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | 5-track parallel plan; A + D in scope here                                                                                                                                               | G1 (reason taxonomy — Track A) + G2 (cluster validation overlap — Track D zero-activity-bar)                                                                                                         |
| [`expected_universe_v2_design_2026_05_08`](../active/expected_universe_v2_design_2026_05_08.md)                       | Per-instrument-grain enumerator (v2 supersedes v1 venue-grain); pre-populates `expected_unattempted` rows from instruments-service catalog                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Draft (Q3 launch-vs-v8 sequencing pending)                                                                                                                                               | G3 (enumerator launch) — sequenced AFTER G4 v8 schema                                                                                                                                                |
| [`manifest_schema_final_gate_2026_05_09`](../active/manifest_schema_final_gate_2026_05_09.md)                         | **CONSOLIDATED v8 SSOT.** One-shot maximalist plan: bundled Phase 3 parquet walk does FIVE migrations in ONE pass — pipeline_mode hive partition + category→asset_group rekey + 5 drift-axis fixes + v8 NULL-column backfill (`service_emission_state` + `last_emission_decision_at` + `expected_window_completeness_pct`) + cross-asset rescan class-A auto-fixes. Closed-set `ServiceEmissionStateEnum` ratified inline. Supersedes archived `manifest_v7_schema_migration_design_2026_05_08`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Active (P0; deadline 2026-05-23)                                                                                                                                                         | G4 (v8 schema atomic rename) + G5 (rescan apply-flips overlap — bundled in same parquet walk)                                                                                                        |
| [`manifest_cross_asset_rescan_design_2026_05_08`](../active/manifest_cross_asset_rescan_design_2026_05_08.md)         | Cross-asset-group `--apply-flips` reconciler against full manifest; runs AFTER v8 schema lands so `service_emission_state` column exists                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | Draft                                                                                                                                                                                    | G5 (rescan apply-flips)                                                                                                                                                                              |
| [`gcs_migration_bundle_pipeline_mode_2026_05_08`](../active/gcs_migration_bundle_pipeline_mode_2026_05_08.md)         | `pipeline_mode=` hive partition adoption (overnight migration of millions of parquets) + writer kwarg sweep (workspace `record_captured` callsites)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | Draft                                                                                                                                                                                    | G6 (pipeline_mode partition + writer adoption) + G7 (workspace audit)                                                                                                                                |
| [`bucket_name_ssot_canonicalisation_2026_05_10`](../active/bucket_name_ssot_canonicalisation_2026_05_10.md)           | Collapse three-layer bucket-name drift (yaml + per-family config.py + UTL resolver) to single SSOT; provision env-tiered buckets; physical data migration flat→env-tiered. **G6 prerequisite** — bucket names must resolve correctly before pipeline_mode hive migration runs.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Active (P0; deadline 2026-05-19)                                                                                                                                                         | G6 prerequisite (env-tiered bucket provisioning + physical migration)                                                                                                                                |
| [`expected_unattempted_propagation_chain_2026_05_12`](../active/expected_unattempted_propagation_chain_2026_05_12.md) | **Runtime propagation of honest-absence across the dependency chain**: instruments-service → MTDS → MDPS → features → ML. Each service reads upstream manifest at pre-flight and writes `expected_unattempted` rather than `attempted_failed` for shards skipped due to upstream honest absence or MVP-scope exclusion. Two new UAC `EmptyConfirmedReason` values + UTL cross-service manifest reader. Complement to G3 (G3 = historical batch enumerator; this = runtime propagation going forward).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | ✅ CODE COMPLETE 2026-05-19 (slot-5 closed all checkboxes). Production validation pending Phase 3 window (issue: `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`). | G3b (runtime propagation — sequenced AFTER G3 enumerator, BEFORE apply-flips in G5)                                                                                                                  |
| [`honest_coverage_formula_consolidation_2026_05_19`](../active/honest_coverage_formula_consolidation_2026_05_19.md)   | **Canonical formula SSOT for coverage % across the workspace.** `compute_honest_coverage()` + `CaptureStatusCounts` NamedTuple shipped in UAC (Phase 0 — uac@327fec6). Phases 1-8 migrate downstream consumers (deployment-api `data_status_service.py`, deployment-ui `DataStatusPanel.tsx`, IS + MTDS `/api/data-status`, per-service CLIs) to call the canonical function instead of re-deriving inline. Phase 6 CI ratchet snapshots daily coverage + blocks >0.5pp regressions; inline-formula linter blocks new re-implementations. Also patches `launch-instruments-backfill-vm.sh` to honor `--force=false` correctly (deployment-service@d673323) so manifest-driven skip actually fires in production backfills.                                                                                                                                                                                                                                                                                                                                          | Phase 0 shipped 2026-05-19. Phases 1-8 P0 pre-May-23. 2.4 calibrated AI-days.                                                                                                            | G1 (reason taxonomy convergence — EXPECTED\_\*/non-EXPECTED\_\* split for expected_unattempted) + G7 (workspace audit — CI ratchet + inline-formula linter)                                          |
| [`is_mtds_contract_audit_2026_05_20`](../active/is_mtds_contract_audit_2026_05_20.md)                                 | **IS↔MTDS contract enforcement.** Audit 2026-05-20 found 6 MTDS handlers hardcode venue URLs/universes despite IS having canonical adapters (Drift / Phoenix / Marinade / Jito / Solana LSTs / native-staking). 1 handler (Drift backfill) emits ZERO manifest rows for 0-record days (silent absence, the exact case CLAUDE.md "Never emit silent placeholders" forbids). `solana-defi-central` bucket on schema_version=4. Phase 1 extends UAC `InstrumentRecord` with archive-metadata fields (url_template, record_type names, coverage_start/end, listed_at/delisted_at) + adds `EXPECTED_PAST_SOURCE_COVERAGE_END` to `EmptyConfirmedReason`. Phase 2-3 rewire IS adapters + MTDS handlers to use the canonical pattern. Phase 4 migrates solana-defi v4→v8. Phase 5 re-backfills. Phase 7 wires THREE new QG steps — `no_silent_absence_handlers.sh`, `no_hardcoded_venue_urls.sh`, `no_hardcoded_venue_universe.sh` — alongside the honest_coverage ratchet. The QG step absence was THE root cause that let silent-absence/hardcoded-URL patterns persist. | Audit complete 2026-05-20. Phase 1-8 P0 pre-May-23. 5.6 calibrated AI-days.                                                                                                              | G1 (reason taxonomy — EXPECTED*PAST_SOURCE_COVERAGE_END) + G4 (v8 schema — solana-defi migration) + G6 (writer adoption — handlers emit record*\* per shard) + G7 (workspace audit — 3 new QG steps) |

The eleven children together cover schema + writer + data layout + runtime propagation + cross-service contract
enforcement. No isolated execution.

## Batch gates (sequenced phases)

Each gate is a **hard-stop**: ALL three axes (schema + writer + data) must reach the gate's target version before any
axis advances past it. Gates land in this order:

### G0 — Baseline frozen (PRE-REQUISITE)

- ✅ **Schema axis**: v5 4-state taxonomy (`captured` / `empty_confirmed` / `attempted_failed` / `expected_unattempted`)
  live; `EMPTY_CONFIRMED_REASONS` closed set live; `BUNDLED_DATA_TYPES` declared in UAC.
- ✅ **Writer axis**: `ManifestWriter` with `record_captured` + `record_empty` + `record_failed` +
  `record_expected_unattempted`; `assert_available_at_present` enforces per-row stamping; per-VM shard isolation
  (`MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`) live.
- ✅ **Data axis**: hive-vocab `category=` (legacy) + `asset_group=` (canonical) coexist on disk (reader tries canonical
  first, falls back to legacy — only documented exception to the migration-not-fallback rule).

Pass criterion: workspace QG green; manifest at v5 + ServiceEmissionPolicy slice (a) UAC@58c3b61 shipped.

### G1 — Reason taxonomy expansion (writegate Phase 2.E + wave3x Track A)

- **Schema axis**: UAC `EMPTY_CONFIRMED_REASONS` extends with `EXPECTED_PARTIAL_HALF_DAY` + any other Track-A residuals.
  `SCHEMA_VALIDATION_FAILED` added as a `record_failed` typed reason (per `hard_schema_enforcement` Phase 5).
- **Writer axis**: UTL `ManifestWriter` accepts new typed reasons; `LegacyBlankErrorReasonError` continues to reject
  blank reasons (per UTL@68b3804a).
- **Data axis**: reconciler `reconcile_legacy_blank_to_typed_reason.py` (wave3x Track C) flips legacy blank
  `error_reason` rows on disk to typed reasons. NO new placeholder parquets — manifest reason IS the SSOT.

Full-execution criterion: workspace grep `record_empty\(.*reason="\b` returns zero blank-string reasons; reconciler ran
on canonical manifest with non-zero rows flipped; sample probe of 5 random shards confirms typed reasons.

### G2 — Cluster validation MANDATORY at `record_captured` for bundled types (hard_schema_enforcement Phase 5 + wave3x Track D + writegate 3.D.5 Wave 3.X)

- **Schema axis**: `BUNDLED_DATA_TYPES` extended to cover `options_chain` (ES.OPT 11-cluster), `futures_chain`,
  `prediction_canonical_question_group`, sports per-fixture-bundle types (`ODDS_SNAPSHOT` / `ODDS_MOVEMENT` /
  `ARBITRAGE`). UAC `cluster_extractor` registry seeded for each.
- **Writer axis**: `ManifestWriter.record_captured(expected_root_clusters=, cluster_extractor=)` REQUIRES kwargs for
  every bundled type — `MissingClusterValidationError` raised if absent. QG STEP 5.64 walks every callsite literal +
  asserts kwargs present when data_type is bundled.
- **Data axis**: zero-activity-bar adapter audit (wave3x Track D) — every blank-source-response with catalog-alive
  instrument-day flips to category D (write zero-activity bars + record_captured) per CLAUDE.md 4-category rule.

Full-execution criterion: QG STEP 5.64 green; `MissingClusterValidationError` audit returns zero violations across all
12 affected repos; sample probe of 5 ES.OPT bundles confirms 11 clusters present per shard.

### G3 — Expected-universe enumerator v2 (per-instrument grain)

- **Schema axis**: manifest schema unchanged from G2 (still v6/v7 column set); v2 enumerator pre-populates
  `expected_unattempted` rows at per-instrument grain from instruments-service catalog cross-product.
- **Writer axis**: enumerator script `populate_expected_universe_v2.py` writes via `ManifestWriter` → per-VM shards →
  consolidator. Existing `record_captured` cleanly supersedes `expected_unattempted` rows by row_key.
- **Data axis**: per-VM shard isolation enforced; consolidator merges into canonical
  `_index/availability_index.parquet`.

Sequencing: this gate is **conditionally gated**: per `expected_universe_v2_design` Q3, the enumerator can launch EITHER
before G4 v8 schema (then re-runs after) OR after G4 (one-shot). **Decision: launch AFTER G4** — the v8 schema migration
is read-once + write-once + blocking; running v2 enumerator before doubles compute cost. Override per operator direction
at gate boundary.

Full-execution criterion: manifest contains expected_unattempted rows for 100% of (catalog × dates × data_types) across
all asset_groups; coverage % at each drilldown level computes correctly per CLAUDE.md formula
(`captured / (captured + empty_confirmed + attempted_failed + expected_unattempted)`).

### G4 — v8 schema migration (atomic rename + immutable service_emission_state)

- **Schema axis**: v8 manifest column set adds immutable `service_emission_state ∈ ServiceEmissionStateEnum` (closed
  set: `PUBLISHED_OK`, `PUBLISHED_DEGRADED`, `STALE_DATA_HEARTBEAT_ONLY`, `BLOCKED` per UAC@58c3b61
  ServiceEmissionPolicy slice (a); name ratified 2026-05-10 cross-plan audit Q1 — uses full `STALE_DATA_HEARTBEAT_ONLY`
  per Policy B larger-set-wins rule, matching `manifest_schema_final_gate_2026_05_09.md` § Phase 1.A which is the
  consolidated v8 SSOT — see `plans/archive/manifest_v7_schema_migration_design_2026_05_08.plan.md` § line 66 for
  archived predecessor).
- **Writer axis**: `ManifestWriter.record_captured(service_emission_state=...)` now REQUIRED kwarg; default-value
  protocol REJECTED — every callsite must declare. Migration script (one-time) populates `service_emission_state` for
  all v7-shaped legacy rows from a per-(service, output_data_type) seed dict.
- **Data axis**: atomic rename `_index/availability_index.parquet` → `_index/availability_index_v8.parquet`. NO fallback
  grace period (per CLAUDE.md "Manifest migration, NOT fallback" SSOT — overrides v7-design plan's 30-day fallback
  proposal). Reader-side fallback paths DELETED in same commit.

**Banned**: feature-flag fallback / 30-day grace period / parallel v7+v8 readers. One commit migrates everything;
fallback paths get deleted in the same commit.

Full-execution criterion: canonical manifest at v8 schema; zero v7-shaped rows present; reader fallback paths grep
returns zero hits; workspace QG green on UTL + every consumer service.

### G5 — Cross-asset-group rescan (apply-flips against full manifest)

- **Schema axis**: unchanged from G4 (v8 schema).
- **Writer axis**: `manifest_cross_asset_rescan` reconciler runs with `--apply-flips`; flips legacy capture_status
  values that don't match the new closed-set semantics (e.g. legacy `captured` rows that should be `attempted_failed`
  per the catalog-aware write-gate guard).
- **Data axis**: full manifest scan + per-shard parquet probe (count rows, NaN ratio, schema match) drives the flip
  decision; CSV diff exported for operator review BEFORE `--apply-flips` runs.

Full-execution criterion: rescan dry-run CSV reviewed by operator; `--apply-flips` runs against canonical manifest;
post-rescan manifest has zero capture_status mismatches per the catalog-aware guard.

### G6 — `pipeline_mode=` hive partition + writer adoption (gcs_migration_bundle)

- **Schema axis**: UAC `PIPELINE_MODE` enum (closed set: `batch_databento` / `batch_tardis` / `batch_yahoo` /
  `live_websocket` / etc.) seeded; `ManifestWriter.record_captured(pipeline_mode=)` REQUIRED kwarg.
- **Writer axis**: workspace-wide grep `record_captured\(` audit confirms every callsite passes `pipeline_mode=`. QG
  STEP 5.66 extension AST-walks the callsites + asserts kwarg present.
- **Data axis**: GCS bundle migration — overnight `gsutil rsync` writes `pipeline_mode=` hive partition into every
  affected parquet path. Old paths (without `pipeline_mode=`) deleted post-rsync verification.

**Banned**: rolling consumer migration with read-side fallback. The rsync + writer adoption + reader simplification ship
in the same commit batch.

Full-execution criterion: GCS rsync completes with object-count parity; sample probe of 5 random shards confirms
`pipeline_mode=` partition; `MissingPipelineModeKwargError` audit returns zero violations; reader fallback paths
deleted.

### G7 — Workspace-wide writer audit + consumer wiring (writegate Wave 4 slice c)

- **Schema axis**: every `(service, output_data_type)` pair in UAC `SERVICE_EMISSION_POLICY_SEED_DICT` declared.
- **Writer axis**: every per-service team consumes `publish_with_policy()` from UTL@1a7e1d4b; `EmissionDecision` routes
  the parquet write + alert.
- **Data axis**: every emission produces correct `service_emission_state` value at write-time; data-status UI surfaces
  the new column at every drilldown level.

Full-execution criterion: workspace QG STEP 5.64 + 5.66 green; every emission service has `publish_with_policy`
callsite; data-status UI renders `service_emission_state` color-coded per asset_group / venue.

## Per-axis dependencies

| Gate | Schema axis (UAC)                              | Writer axis (UTL + adapters)                         | Data axis (GCS / on-disk)                       |
| ---- | ---------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------- |
| G0   | v5 + slice (a)                                 | `ManifestWriter` 4-state                             | `category=` + `asset_group=` coexist            |
| G1   | reason taxonomy expanded                       | UTL accepts new typed reasons                        | reconciler flips legacy blanks                  |
| G2   | `BUNDLED_DATA_TYPES` extended                  | `record_captured` cluster kwargs MANDATORY           | zero-activity-bar audit applied                 |
| G3   | (no schema change)                             | enumerator v2 writes via `ManifestWriter`            | per-VM shards land catalog × dates × data_types |
| G4   | v8 schema (immutable `service_emission_state`) | `record_captured(service_emission_state=)` MANDATORY | atomic rename; legacy v7 paths deleted          |
| G5   | (no schema change)                             | rescan reconciler `--apply-flips`                    | manifest capture_status flipped on disk         |
| G6   | `PIPELINE_MODE` enum                           | `record_captured(pipeline_mode=)` MANDATORY          | `pipeline_mode=` hive partition on disk         |
| G7   | every (service, output_data_type) seeded       | every consumer wires `publish_with_policy`           | data-status UI renders new column               |

## Banned anti-patterns

- **Executing any one child plan in isolation** without bumping the other two axes. If
  `manifest_v7_schema_migration_design` ships v8 schema without the writer kwargs + GCS layout, every consumer breaks;
  if `gcs_migration_bundle_pipeline_mode` ships hive partition without the writer kwarg, manifest rows misalign with
  parquet paths; if `writegate` ships reason-taxonomy expansion without the reconciler, legacy blanks survive in
  production manifest.
- **v8 schema fallback grace periods** — read-side fallback for legacy schema where a one-time migration would suffice.
  The 30-day fallback in `manifest_v7_schema_migration_design` is REJECTED; replace with one-time migration + delete
  fallback in the same commit (CLAUDE.md "Manifest migration, NOT fallback").
- **`record_captured` calls without cluster validation kwargs** for bundled data_types — `MissingClusterValidationError`
  raised loud; zero tolerance.
- **Reader-side fallback for legacy schema** where a migration script would suffice. The one documented exception
  (hive-vocab `category=` vs `asset_group=`) survives; everything else gets deleted in the same commit as the migration.
- **Default-value protocols on new mandatory kwargs** — `service_emission_state` and `pipeline_mode` must be explicit at
  every callsite; defaulting hides drift.
- **Per-service consumer rollout without UAC SSOT update** — every new mandatory kwarg lands in UAC + UTL + every
  consumer in the same commit-batch.

## Full-execution criterion (per "Plans Run To Actual Completion" HARD RULE)

For each gate, "ran-to-completion on real infra" means:

- **G0**: shipped + verified (current state).
- **G1**: reconciler ran on canonical manifest in production GCS
  (`gs://central-element-323112-availability-manifest/...`); workspace grep `record_empty\(.*reason=""\)` returns zero
  hits; sample probe of 5 random shards confirms typed reasons.
- **G2**: QG STEP 5.64 green; sample probe of ES.OPT options bundles + futures bundles + sports fixture bundles confirms
  expected cluster counts.
- **G3**: canonical manifest contains `expected_unattempted` rows for 100% of (catalog × dates × data_types) across all
  5 asset_groups (cefi / defi / tradfi / sports / prediction); coverage % computes correctly at every drilldown.
- **G4**: canonical manifest at v8 schema; zero v7-shaped rows; reader fallback paths grep returns zero hits; workspace
  QG green.
- **G5**: rescan `--apply-flips` ran against canonical manifest; post-rescan zero capture_status mismatches per
  catalog-aware guard.
- **G6**: GCS rsync completed with object-count parity; sample probe confirms `pipeline_mode=` partition; QG STEP 5.66
  green.
- **G7**: workspace QG green on every service; data-status UI renders new columns; sample probe confirms end-to-end
  emission flow at each (service, output_data_type) pair.

NO smoke-only verification accepted. NO "operator-actionable" close-outs (per "Plans Run To Actual Completion" HARD
RULE). Each gate ships with the actual cloud-resource verification command logged + actual output captured.

## Done definition

The umbrella closes when:

1. All 7 child plans archive cleanly with their phases mapped to gates G0–G7.
2. Canonical manifest at v8 schema across all 5 asset_groups.
3. Workspace-wide `record_captured` callsite audit returns zero violations:
   - cluster validation kwargs for bundled types ✓
   - `service_emission_state` mandatory ✓
   - `pipeline_mode` mandatory ✓
   - `available_at` per-row stamping ✓
4. GCS data layout migrated: `pipeline_mode=` hive partition adopted; legacy paths deleted; object-count parity.
5. Coverage % at every drilldown level closes the formula `captured / (captured + empty_confirmed + attempted_failed
   - expected_unattempted)` to a non-zero denominator (i.e. expected universe enumerated).
6. data-status UI surfaces `service_emission_state` + `pipeline_mode` at every drilldown.

## Cross-cutting with `available_at` umbrella

The `available_at_lookahead_bias_completion_2026_05_08` plan is the sister umbrella for stamping. The two MUST gate
together at G0 baseline (both shipped Wave 4 slice (a) + assert_available_at_present already live), at G2 (cluster
validation overlap with available_at strict-mode), and at G7 (workspace audit covers BOTH `available_at` per-row
stamping AND `service_emission_state` declaration).

If you're touching one umbrella's schema, check the other before shipping.

## See also

- [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) — May-23 cutover master
- [`available_at_lookahead_bias_completion_2026_05_08`](../active/available_at_lookahead_bias_completion_2026_05_08.md)
  — sister umbrella for stamping
- [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) —
  manifest schema SSOT
- [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md) —
  4-category gap rule + reason taxonomy
- [`/codex/02-data/manifest-migration-coordination.md`](/codex/02-data/manifest-migration-coordination.md) — migration
  coordination playbook

## Audit-2026-05-10 finding — post-cutover Wave: lift cross-cutting per-data_type view to typed registry

**Source**:
[`plans/archive/issues/codex_vs_citadel_block_b_audit_findings_2026_05_10.md`](../archive/issues/codex_vs_citadel_block_b_audit_findings_2026_05_10.md)
Block B2.

**Finding**: UAC `external/` has 73 source sub-directories (per-source flat layout: `__init__.py` + `examples/` +
`mocks/` + `normalize.py` + `schemas.py`). The cross-cutting "per-data_type → which sources cover which (venue, day)"
view today comes from prose matrix docs
([`/codex/02-data/mtds-data-source-coverage-matrix.md`](/codex/02-data/mtds-data-source-coverage-matrix.md) +
[`sports-data-source-coverage-matrix.md`](/codex/02-data/sports-data-source-coverage-matrix.md), each ~500 lines)
hand-typed + cross-linked to UAC registry helpers. **Drift risk**: 2026-04-20 phantom-audit incident (false 26% sports
ODDS phantom) was matrix-doc / registry-code drift. ~5 documented incidents involved cross-cutting drift not catchable
from any single source's view.

**Recommendation**: KEEP per-source colocation (natural physical shape); LIFT cross-cutting view to typed-registry-
derived. Composes with operator's "common SSOT codebase + hooks + min duplicate" directive (Block A1 DECIDED-YES).

**Recommended post-cutover Wave to file under this master**:

- [ ] [SCRIPT] P1. **NEW** UAC `data_type_registry.py` — typed cross-cutting registry; per-source
      `external/{source}/registry.py` declares emissions as `SOURCE_EMITS: dict[DataType, EmissionSpec]` next to
      `schemas.py`.
- [ ] [SCRIPT] P1. **NEW** derived helpers `data_type_coverage(data_type)` + `sources_for(venue, data_type)` replace the
      prose matrix as SSOT.
- [ ] [SCRIPT] P1. **NEW** `scripts/render-coverage-matrix.py` generates the matrix doc from registry at PM QG time;
      commits the rendered .md artefact for human reading; QG asserts no manual edits to the rendered file.
- [ ] [SCRIPT] P1. **MIGRATE** 73 source dirs each get a `registry.py` (current implicit knowledge in adapter code
      becomes typed-explicit).
- [ ] [SCRIPT] P1. **DELETE** prose matrix doc once rendered version is canonical (~6 months after registry lands).

**Cost**: ~2-3 AI-days for registry + render script + 1-2 reference migrations; +1 AI-day per source family for sweep.
**Saved cost**: every drift-induced phantom incident goes away by construction (registry IS the matrix; can't drift).
**Timing**: post-cutover; rides with monorepo consolidation (Block A1).

**Plan status**: FYI for master-plan owner — NEW Wave not yet wired into the master's wave sequence. Master-plan owner
decides whether to fold into existing waves OR file standalone post-cutover.

## Referenced sub-plans (active, added 2026-05-14)

Active sub-plans owned by or closely coordinated with this epic:

| Plan                                                                                                           | Role                                                                                                 | Status |
| -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------ |
| [`active/mock_data_pipeline_benchmarking_2026_05_10`](../active/mock_data_pipeline_benchmarking_2026_05_10.md) | Mock data pipeline benchmarking — compute sizing + throughput benchmarks for backtest mock-data path | Active |
| [`active/features_modehandler_lift_2026_05_08`](../active/features_modehandler_lift_2026_05_08.md)             | Features ModeHandler lift — batch/live mode-handler abstraction lift across features-\* services     | Active |
| [`active/data_status_ui_phase_2f`](../active/data_status_ui_phase_2f.md)                                       | Data-status UI Phase 2F — deployment-ui data-status panel enhancements (honest-coverage surface)     | Active |
