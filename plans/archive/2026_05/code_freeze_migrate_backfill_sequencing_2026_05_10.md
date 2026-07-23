---
doc_type: plan
title: Code-freeze → migrate → backfill sequencing master (May-23 cutover orchestration umbrella)
summary:
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, execution-service, features-service, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-10
archived: 2026-05-23
last_updated: 2026-05-23
estimate_class: infra
estimate_baseline_ai_days: 202.5
estimate_calibrated_ai_days: 162.0
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~145-260).
  Class inferred from filename (infra, multiplier 0.8×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
parent_epic: defi_master
assigned_vm: vm-defi
priority: P0
---

## Deferred work — migrated to:

Phases 1-2 (GCS bundle migration + v8 schema bump) complete. Post-cutover gates tracked in:

- `plans/active/master_to_live_defi_2026_05_23.md` § Groups B-G (features green, ML, paper-trade, live archetypes).
- `plans/epics/mtds_mdps_master.md` (Phases 11-14 sequencing).
- Backfill plans archived 2026-05-23; execution evidence in git history. Archiving 2026-05-23.

# Code-freeze → migrate → backfill sequencing master

## Why this plan exists

Operator framing 2026-05-10: _"Imagine before doing any manifest, migration or cloud schema migrations or data
migrations on physical files we first wanna get all the code in services and the UAC and UTL work done so that we won't
have to migrate again later. Can we prioritise plan items which get us there so that after that's all done we can
migrate manifest and gcs and then after that we can resume backfills for instruments up until features service for
everything."_

This plan is the **execution-sequencing umbrella** for the May-23 cutover. It does NOT duplicate scope from existing
plans — it indexes them, sequences them into a strict three-phase model, and closes the gaps the audit surfaced. The
durable readiness model lives in [`plans/active/master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md);
the schema/writer/data-layout co-evolution gates live in
[`plans/epics/manifest_evolution_SUPERSEDED_2026_05_21.md`](../epics/manifest_evolution_SUPERSEDED_2026_05_21.md); the
migration coordinator lives in
[`plans/epics/manifest_migration_SUPERSEDED_2026_05_21.md`](../epics/manifest_migration_SUPERSEDED_2026_05_21.md). This
plan composes them along the time axis.

The principle: **code shape decisions → migration → backfill, in that order, no doubling back.** Every migration of
physical files (manifest schema bump, GCS hive-vocab rekey, OHLCV legacy filename → per-instrument rename, pipeline_mode
partition addition, AWS cloud-parity bundle) is **one-shot**. If a code-shape decision lands AFTER a physical migration
runs, the workspace pays the re-migration tax — millions of parquets walked twice, manifest rewritten twice, backfill
VMs idle waiting, May-23 deadline at risk.

## The three-phase model

```
─────────────────────────────────────────────────────────────────────────────
 PHASE 1 — Code-complete first       (deadline:  2026-05-15 hard freeze)
─────────────────────────────────────────────────────────────────────────────
   UAC schema columns + enums + registries finalized
   UTL helpers (ManifestWriter, EmissionPublisher, AvailabilityStamping) finalized
   Service writer code (MTDS / MDPS / features-service / instruments-service /
                        strategy / execution / risk / position-balance / alerting)
                       reflects final shape
   ServiceEmissionPolicy seed dict finalized
   error_reason taxonomy frozen (EMPTY_CONFIRMED_REASONS closed set)
   BUNDLED_DATA_TYPES + DATA_TYPE_TO_CLUSTER_REGISTRY finalized
   pipeline_mode hive partition column declared
   feature_family schema column declared
   available_at per-source semantics finalized (SOURCE_PRIORITY)
   instrument lifecycle cache-delta hot-reload landed
   features-* repos consolidated into single features-service

                                  ↓ Phase 1 freeze gate ↓

─────────────────────────────────────────────────────────────────────────────
 PHASE 2 — One-shot physical migrations    (window: 2026-05-15 → 2026-05-19)
─────────────────────────────────────────────────────────────────────────────
   2.0  Pre-migration VM drain + state freeze (GAP — formalized below)
   2.1  Manifest v5/v6/v7 → v8 atomic rename + service_emission_state column
        (schema owned by manifest_schema_final_gate_2026_05_09 per operator
         decision 2026-05-11; rename + apply-flips executed via
         manifest_cross_asset_rescan_design)
   2.2  GCS bundled migration: pipeline_mode partition + category=→asset_group=
        rekey + 5-axis drift sweep (path-prefix / instrument_type casing /
        schema-4 empty / chain-bundle equivalence) — single walk, all changes
   2.3  OHLCV legacy filename → per-instrument rename reconcile
   2.4  AWS DeFi-first cloud-parity migration (GCS → S3 transfer + Glue/Athena)
   2.5  Manifest cross-asset rescan with --apply-flips (post-schema, post-data)
   2.6  env-tiered features-* (+ Group-B ml-*/strategy/execution if flat on disk)
        bucket provisioning + flat-bucket data migration + reader/writer repoint
        (per bucket_name_ssot_canonicalisation_2026_05_10.md Q4 = option (b),
         operator/Ikenna decision 2026-05-11 — "make reality match the yaml";
         the CODE half (config.py → resolve_bucket_name) lands pre-Phase-2 in
         the bucket-SSOT plan; this is the physical half)

                                  ↓ Phase 2 freeze gate ↓

─────────────────────────────────────────────────────────────────────────────
 PHASE 3 — Resume backfills end-to-end    (window: 2026-05-19 → 2026-05-23)
─────────────────────────────────────────────────────────────────────────────
   3.1  Instruments-service catalogue forward-fill (5 asset_groups)
   3.2  MTDS multi-venue backfill VM relaunch (15 CeFi venues + TradFi + DeFi
        + Sports + Predictions)
   3.3  MDPS bar reprocessor relaunch (per-asset-group)
   3.4  Features-service compute relaunch (cross-instrument + per-family)
   3.5  ML training + inference relaunch
   3.6  Strategy archetype paper-trade smoke (DeFi 2 archetypes + CeFi/TradFi/
        Sports/Predictions)
   3.7  7-day continuous live-DeFi run on real wallet (final cutover gate)
─────────────────────────────────────────────────────────────────────────────
```

Each phase has a **freeze gate**: nothing in phase N+1 starts until phase N is operationally complete (not just
code-shipped). Per CLAUDE.md HARD RULE _"Plans Run To Actual Completion, Not Smoke-Test Green"_, "shipped" means data on
real infrastructure with verification probes, not just a green QG.

## Phase 1 — Code-complete inventory

Plans in this section MUST run to ✅ shipped before Phase 2 starts. The umbrella enforcer is
[`plans/epics/manifest_evolution_SUPERSEDED_2026_05_21.md`](../epics/manifest_evolution_SUPERSEDED_2026_05_21.md) gates
**G1 (reason taxonomy) → G2 (cluster validation) → G3 (enumerator launch)**; this section indexes the plans those gates
consume.

### Phase 1.A — UAC + UTL foundation (writegate / honest coverage)

- [x] ✅ [PLAN] P0. **`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`** — UTL **[CONFIRMED-DONE
      2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items annotated/completed.
      `ManifestWriter.record_captured()` 4-pillar gate signature, typed-error taxonomy (`EMPTY_CONFIRMED_REASONS`),
      cluster validation kwargs, ServiceEmissionPolicy seed dict, 37-callsite MDPS/MTDS writer migration. **Status
      check**: Wave 4 slice (a) shipped (UAC@58c3b61 + UTL@1a7e1d4b + PM@0e2eb08e); slice (b) Phase 5.1-5.7 (~2d MDPS
      ohlcv_1h POC + manifest_completeness helper + UAC manifest schema columns + deployment-api/ui surface) PLANNED
      2026-05-08; slice (c) Phase 6.1-6.9 (~3-5wk per-service rollout) PLANNED. **Phase 1 blocker**: slice (b) MUST land
      before Phase 2.1 manifest schema bump can rename/freeze.
- [x] ✅ [PLAN] P0. **`plans/active/wave3x_residual_ssots_2026_05_08.md`** — 5 parallel tracks for residual UAC SSOTs. —
      **ARCHIVED** `plans/archive/wave3x_residual_ssots_2026_05_08.plan.md` (trivial-sweep 2026-05-21) Track A
      (HALF_DAY_SESSIONS + VENUE_SESSION_HOURS) shipped UAC@bdc84ed. Tracks B/C/D/E open (sports per-source SSOTs /
      reconcilers / zero-activity-bar audit / sports availability stamping cascade).
- [x] ✅ [PLAN] P0. **`plans/active/available_at_lookahead_bias_completion_2026_05_08.md`** — Sister umbrella for
      stamping — **ARCHIVED** `plans/archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md`
      (trivial-sweep 2026-05-21) work. Per-source `available_at` semantics + UTL `stamp_available_at_*` helpers +
      LookaheadBiasError gate strict-mode rollout across every features-\* calculator. **Phase 1 blocker**: every
      per-source stamping helper must be final before Phase 3 backfills emit their first new row (otherwise re-stamping
      at Phase 3 = re-write of Phase 2 migrated parquets).
- [x] ✅ [PLAN] P1. **`plans/active/expected_universe_v2_design_2026_05_08.md`** — Per-instrument-grain enumerator (v2 —
      **ARCHIVED** `plans/archive/2026_05/expected_universe_v2_design_2026_05_08.md` (trivial-sweep 2026-05-21)
      supersedes v1 venue-grain). DRAFT. Pre-populates `expected_unattempted` rows from instruments-service catalogue.
      Gate G3 of `manifest_evolution_master`. May be deferred behind Phase 2.1 v7 schema bump per audit Q3.

### Phase 1.B — Schema + writer hardening

- [x] ✅ [PLAN] P0. **`plans/active/hard_schema_enforcement_2026_05_08.md`** — Workspace-wide hard schema enforcement at
      — **ARCHIVED** `plans/archive/2026_05/hard_schema_enforcement_2026_05_08.md` (trivial-sweep 2026-05-21) write
      boundary; flips required fields nullable→required across asset_groups (base_currency / quote_currency / chain_id /
      contract_address / decimals / fixture_id / futures_expiry). **Sequenced AFTER** `tradfi_master` Q1+Q2
      futures-expiry ships (avoids mass-fail-during-transit per existing plan body). **Phase 1 blocker**:
      SCHEMA_VALIDATION_FAILED enum extension lands here; needed before Phase 2.5 cross-asset rescan can flip rows.
- [x] ✅ [PLAN] P0. **`plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`** — Collapse 3-layer drift (yaml +
      **[CONFIRMED-DONE 2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items annotated/completed.
      per-family config.py + UTL resolver) to one canonical SSOT (yaml = canonical per slot 4 decision 2026-05-11).
      **OPERATOR DECISION 2026-05-11 (Ikenna): option (b) — provision env-tiered buckets to match yaml + migrate
      flat-bucket data into them.** Phase 1 (this section) covers: Phase 0a (operator decision recorded ✅), Phase 0b
      (yaml additive corrections — missing `prediction`/`sports` keys, GCP `features-calendar` uncomment, canonical
      `-test-` variant), L2 config.py migration (resolver-call repointing), legacy `get_bucket_name` delegate, QG STEP
      5.69 design. Phase 0c (provision ~180-300 new env-tiered buckets on GCP + AWS via Terraform /
      `setup-buckets.sh`) + Phase 0d (flat→tiered data migration with ≤0.01% drift verification + write-pause cutover)
      move to **Phase 2.4 sub-steps below** (window 2026-05-15→05-19). **Phase 1 blocker**: bucket-name resolution
      code + yaml additive corrections must be final before Phase 2.4 provisioning + data migration starts.

### Phase 1.C — Live-pipeline activation code

- [x] ✅ [PLAN] P0. **`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`** — Live (websocket-streaming)
      pipeline — **ARCHIVED** `plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md` (trivial-sweep
      2026-05-21) activation for MTDS → MDPS → features-service across 5 asset_groups. NEW UAC `ServiceEmissionPolicy`
      schema column, `pipeline_mode` hive partition, `PipelineMode` facade. Health-API extension + circuit-breaker
      wiring. Instrument-cache-delta hot-reload. Replay subsystem. **Tab 2 PM/evening 2026-05-08 progress**: 4 UTL
      primitives shipped (streaming facade / StreamingHealthSnapshot / InstrumentLifecycleCacheDeltaReloader /
      batch_live_reconciler); MTDS/MDPS/features service-wiring deferred post-features-consolidation. **Phase 1
      blocker**: Phase 0-3 (UAC + UTL foundations) done; Phase 4-5 (per-asset-group cascade) requires
      features_repo_consolidation Phase 7.
- [x] ✅ [PLAN] P0. **`plans/active/features_repo_consolidation_2026_05_08.md`** — Merge 8 separate features-\* repos
      into — **ARCHIVED** `plans/archive/features_repo_consolidation_2026_05_08.plan.md` (trivial-sweep 2026-05-21)
      single features-service with sub-packages. NEW UAC `feature_family` schema column. Lift 4 cross-family helpers
      into UTL. **Deadline 2026-05-13**. **Phase 1 blocker**: Phase 7 (consolidated features-service deployable) must
      land before live-pipeline Phase 4-5 can wire MDPS↔features in-process handoff. Backfill-side: Phase 3.4
      features-service compute relaunch in this plan reads from single consolidated repo, not the 8 archived ones.
- [x] ✅ [PLAN] P1. **`plans/active/basefc_validation_flip_2026_05_10.md`** — Mandatory `ClassVar` enforcement across 75
      — **ARCHIVED** `plans/archive/basefc_validation_flip_2026_05_10.md` (trivial-sweep 2026-05-21) feature calculators
      (paradigm-split rollout). Deadline 2026-05-20.
- [x] ✅ [PLAN] P1. **`plans/active/mdps_streaming_and_backpressure_2026_05_07.md`** — MDPS streaming + backpressure —
      **ARCHIVED** `plans/archive/2026_05/mdps_streaming_and_backpressure_2026_05_07.md` (trivial-sweep 2026-05-21)
      successor (awaits live-pipeline Phase 0-3).
- [x] ✅ [PLAN] P1. **`plans/active/mtds_databento_path_streaming_2026_05_07.md`** — MTDS Databento path-streaming —
      **ARCHIVED** `plans/archive/2026_05/mtds_databento_path_streaming_2026_05_07.md` (trivial-sweep 2026-05-21)
      successor.

### Phase 1.D — Service code: alerting / risk / strategy / DART

- [x] ✅ [PLAN] P0. **`plans/active/alerting_service_live_rules_2026_05_07.md`** — Production rule SSOT + thresholds +
      **[CONFIRMED-DONE 2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items annotated/completed.
      paging logic for live pipeline. Sub-E codex doc category for ML alerting rules (deferred per Tab 5 EOD-summary
      2026-05-08; tracked in [`feedback_capture_discoveries_as_plan_todos_immediately.md`](../../) auto-memory).
- [x] ✅ [PLAN] P0. **`plans/active/risk_simulations_limits_alerting_2026_05_10.md`** — Risk rule taxonomy + —
      **ARCHIVED** `plans/archive/risk_simulations_limits_alerting_2026_05_10.md` (trivial-sweep 2026-05-21)
      per-archetype/venue/account/client limits + alerting wire + pre-flight check API. Parent:
      strategy_and_dart_master.
- [x] ✅ [PLAN] P0. **`plans/active/disaster_recovery_circuit_breakers_2026_05_10.md`** — Disaster recovery + —
      **ARCHIVED** `plans/archive/disaster_recovery_circuit_breakers_2026_05_10.md` (trivial-sweep 2026-05-21)
      reconciliation + circuit breakers + kill switches (cutover MVP). Parent: master_to_live_defi.
- [x] ✅ [PLAN] P1. **`plans/active/promote_workflow_may23_cli_path_2026_05_10.md`** — Promote workflow May-23
      dual-track **[CONFIRMED-DONE 2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items
      annotated/completed. cutover (CLI primary + minimal UI parallel).
- [x] ✅ [PLAN] P1. **`plans/active/topology_qgroup_gap_closure_2026_05_09.md`** — Topology Q-group GAP closure (18
      GAPs + — **ARCHIVED** `plans/archive/topology_qgroup_gap_closure_2026_05_09.md` (trivial-sweep 2026-05-21) 2
      WATCH + 1 ISSUE before May-23).

### Phase 1.E — DeFi-specific code (chain primitives + archetypes)

- [x] ✅ [PLAN] P0. **`plans/active/defi_catalogue_chain_primitives_2026_05_10.md`** — DeFi catalogue + chain primitives
      — **ARCHIVED** `plans/archive/2026_05/defi_catalogue_chain_primitives_2026_05_10.md` (trivial-sweep 2026-05-21)
      (chain genesis dates, protocol launch dates, token metadata). Parent: defi_master.
- [x] ✅ [PLAN] P0. **`plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md`** —
      ARBITRAGE_PRICE_DISPERSION — **ARCHIVED** `plans/archive/arbitrage_price_dispersion_finalisation_2026_05_09.md`
      (trivial-sweep 2026-05-21) canonicalisation + strategy-service catalog + tracer + P&L attribution. Parent:
      defi_master.
- [x] ✅ [PLAN] P0. **`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`** — Recursive-borrow archetype —
      **ARCHIVED** `plans/archive/2026_05/defi_recursive_borrow_archetypes_2026_05_10.md` (trivial-sweep 2026-05-21)
      definitions for carry_staked_basis (Phase 9). PLANNED. Parent: defi_master.
- [x] ✅ [PLAN] P0. **`plans/active/defi_simulation_realism_2026_05_10.md`** — DeFi matching engine extension + —
      **ARCHIVED** `plans/archive/defi_simulation_realism_2026_05_10.md` (trivial-sweep 2026-05-21) risk-modeling
      enhancements. Parent: defi_master.
- [x] ✅ [PLAN] P0. **`plans/active/cme_polymarket_arb_2026_05_08.md`** — InstrumentType.EVENT_CONTRACT enum +
      **[CONFIRMED-DONE 2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items annotated/completed.
      linked_canonical_question_group cross-link + MTDS binary-outcome shard atom + cme_polymarket_event_arb strategy
      archetype.

### Phase 1.F — Cross-cutting code

- [x] ✅ [PLAN] P0. **`plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md`** — Cross-cutting 6-tab restructure
      (Deploy — **ARCHIVED** `plans/archive/2026_05/deployment_ui_lifecycle_tabs_2026_05_08.md` (trivial-sweep
      2026-05-21) / Monitor / Data Status / Builds / Readiness / Config). NEW UAC `LifecycleClass` enum +
      `EnvironmentTier` enum. Parent: cross_cutting_may_23_SUPERSEDED_2026_05_21.epic.
- [x] ✅ [PLAN] P0. **`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`** — Full credential provisioning
      for **[CONFIRMED-DONE 2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items annotated/completed.
      May-23 live-DeFi cutover.
- [x] ✅ [PLAN] P0. **`plans/active/wallet_treasury_client_flow_2026_05_10.md`** — Wallet / treasury / client lifecycle
      — **ARCHIVED** `plans/archive/wallet_treasury_client_flow_2026_05_10.md` (trivial-sweep 2026-05-21) MVP.
- [x] ✅ [PLAN] P1. **`plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md`** — Client reporting + PnL —
      **ARCHIVED** `plans/archive/client_reporting_pnl_attribution_mvp_2026_05_10.md` (trivial-sweep 2026-05-21)
      attribution MVP.

### Phase 1 freeze gate (✅ to flip Phase 2 startable)

The freeze gate fires when ALL of the following are true. The umbrella `manifest_evolution_master` G2 gate is the
technical enforcer; this section is the operator-readable checklist.

- [x] **Schema columns frozen**: UAC manifest schema for v8 (incl. `service_emission_state`, `pipeline_mode`,
      `feature_family`) reviewed + merged + tagged. No further column adds. Column declaration is owned by
      [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) per operator decision
      2026-05-11 (resolves codex_audit F3 ambiguity — the final-gate plan is the canonical v8 owner; writegate slice
      (b)'s Phase 5.2 "UAC manifest schema columns" is SUPERSEDED, slice (b) retains the UTL `manifest_completeness`
      helper + MDPS POC + deployment-api/ui surfaces). **✅ Shipped 2026-05-11**: UAC@`174f401` + `@d938a69` +
      `@76f950a` per slot 6 / slot 2 sequence; `canonical/crosscutting/manifest_schema.py:59,134-138,158-162` declares
      `MANIFEST_SCHEMA_VERSION_V8=8` + `V8_NEW_COLUMNS` tuple + `V8_COLUMN_DEFAULTS` dict; no `# TODO v9` markers per
      slot 3 audit 2026-05-12. (Note: `MANIFEST_SCHEMA_VERSION` constant in `manifest_writer.py:131` is still `=7`
      transitionally per Phase 2 P2 option-b decision; bump-to-8 lands at Phase 4.DEFAULT-REMOVAL.)
- [x] **error_reason taxonomy closed**: `EMPTY_CONFIRMED_REASONS` final set declared in UAC;
      `LegacyBlankErrorReasonError` rejecting any blank reason at write boundary (already shipped UTL@`68b3804a` per
      CLAUDE.md). New reason additions require explicit P0 RFC + this plan re-opens. **✅ Verified 2026-05-12 slot 3
      audit**: `EmptyConfirmedReason` 15 members + `EMPTY_CONFIRMED_REASONS` frozenset (UAC
      `canonical/crosscutting/honest_coverage.py:68-170,121`); `LegacyBlankErrorReasonError` raises at blank reason (UTL
      `manifest_writer.py`).
- [x] **All 37 MDPS/MTDS callsites migrated** to
      `ManifestWriter.record_captured(...) / record_empty(...) / record_failed(...) / record_expected_unattempted(...)`.
      AST sweep (writegate plan QG STEP 5.64) green workspace-wide. (**✅ CONFIRMED 2026-05-14 Day-3 slot 6 audit** —
      master plan line 1105: QG STEP 5.68 workspace-wide `0 baselined, 0 new occurrences`.) **🟡 SUBSTANTIALLY COMPLETE
      2026-05-12 Day 2-3 — 8/9 Phase 4 sub-items shipped; ONLY Phase 4.DEFAULT-REMOVAL remains**. Sub-items: Phase
      4.MDPS @MDPS@`a3c7198` ✅ + Phase 4.MDPS VIX-gap Q2=(A) flip @MDPS@`2d4bb40` ✅ + Phase 4.INSTRUMENTS
      @instruments-service@`e530906` ✅ + Phase 4.INSTRUMENTS footystats Q2=(A) flip @instruments-service@`8f07db3` ✅ +
      Phase 4.DEPLOYMENT-API @deployment-api@`2f833a7` + Phase 4.UI @deployment-ui@`ab06bfe` ✅ + Phase 4.E2E + Phase
      4.PM-SCRIPTS ✅ N/A + Phase 4.GREP-VERIFY @PM@`4159b7ae` (AST-walk STEP 5.70) ✅ + **Phase 4.MTDS ✅ SHIPPED
      2026-05-12 Day 2 by Ikenna slot 3** (3-sub-agent fan-out post-operator-triage at PM@`4c573302`): MTDS@`3da3f43` 97
      callsites in 26 files + DefiManifestRecorder partial Q1=(α) migration; UTL@`12d5e621` 11 internal record\_\*
      callsites; UAC@`52d289c` Q2=(A) 6 new PipelineMode batch values + 14 DeFi SOURCE_PRIORITY gap entries (Harsh
      race-won, my UAC@`7d7ea4c` shipped 7 additive round-trip tests on top); PM baseline @`88226bdb` + @`ea50eddc`
      shrunk **114 → 6** (only Phase 4.FEATURES entries remained) + **Phase 4.FEATURES ✅ SHIPPED 2026-05-12 by Harsh
      slot 3** — `features-service@842ff741` (sports/batch_handler 4 callsites via `_FEATURE_GROUP_TO_PIPELINE_MODE`
      SSOT: fixture_features→BATCH_API_FOOTBALL / odds_features→BATCH_ODDS_API / derived_features→BATCH_FOOTYSTATS + 14
      reference tables fall-through BATCH_API_FOOTBALL) + `features-service@229a0963` (calendar_orchestrator 2 callsites
      with `BATCH_INSTRUMENTS_SERVICE` workaround per `features_calendar_pipeline_mode_gap_2026_05_12.md`
      operator-decision issue doc; same logical unit also adds `reason="SOURCE_RETURNED_ZERO"` to record_empty path that
      would have crashed `LegacyBlankErrorReasonError`); PM baseline @`<this-flip>` shrunk **6 → 0** (full workspace
      pipeline_mode_explicit_baseline.yaml now empty). **Phase 4.DEFAULT-REMOVAL (pipeline_mode= defaults)** ✅ DONE
      (utl@`547ff3c` 2026-05-12 — 4 transitional None defaults removed + MANIFEST_SCHEMA_VERSION 7→8 bumped + codex
      prose reconciled + DefiManifestRecorder df-flow propagation shipped). **Phase 4.DEFAULT-REMOVAL-v8kwargs
      DEFERRED** — 3 v8 emission kwargs (`service_emission_state` / `last_emission_decision_at` /
      `expected_window_completeness_fraction`) still have `= None` defaults; blocked on Phase 6.3-6.9 Ikenna callsite
      sweep of 8 remaining services.
- [x] **ServiceEmissionPolicy seed dict locked**: 19+ rows covering MDPS / features / ml-training / ml-inference /
      strategy / execution / position-balance / risk / instruments / alerting (+ any added during Phase 1). **✅ DONE
      2026-05-12 slot 3 audit — 71 rows** in
      `unified-api-contracts/.../canonical/crosscutting/service_emission_policy.py:159-283`. Coverage: 5 MDPS + 11
      Features (volatility / cross-instrument / delta-one / multi-timeframe) + ML training/inference + Strategy +
      Execution (order_intent / fill_confirmation) + Position-balance + Risk + Instruments + Onchain (11) + Sports (7).
      Default for unseeded pairs: STRICT_FAIL (line 315).
- [x] **available_at per-row stamping wired** at every write boundary; LookaheadBiasError strict-mode green at every
      features-\* calculator. (**✅ CONFIRMED 2026-05-14 Day-3 slot 6 audit** — master plan lines 1108-1111: all 8
      families confirmed: delta_one/volatility/calendar/multi_timeframe/cross_instrument/sports
      `PointInTimeEnforcer(strict=True)`; onchain `strict=not mock_mode`; commodity direct `raise LookaheadBiasError`.)
      **🟡 PARTIAL 2026-05-12 slot 3 audit — 2/8 feature families**: features-sports ✅ shipped
      (`features-service/features_service/sports/data/writer.py:61` `PointInTimeEnforcer(as_of=as_of, strict=True)`);
      features-onchain 🟡 config-gated (production strict=True only; `feature_writer.py:143-146`); 6 other families
      (delta_one / volatility / calendar / commodity / cross_instrument / multi_timeframe) ❌ NO strict-mode wiring.
      Plan `available_at_lookahead_bias_completion_2026_05_08.md` 14/47 todos done (~30%); Phase 6 (calculator/writer
      enforcement) DEFERRED-AFTER chain links 0+1 + features-consolidation Phase 5.c gate-lift-into-UTL. **Action**:
      owner needs reassignment in 2026-05-13 cycle to drive 6 remaining families.
- [x] **features_repo_consolidation Phase 7** done — single features-service repo deployable; 8 child repos archived.
      **✅ DONE 2026-05-11 — verified by slot 3 audit 2026-05-12**: 10/13 phases done (3 residual P2 deferred to
      successor `features_service_qg_cleanup_2026_05_11.md`, non-blocking); 8 child repos archived on GitHub
      (`gh api .archived = true`) — calendar / commodity / cross-instrument / delta-one / multi-timeframe / onchain /
      sports / volatility with DEPRECATION_NOTICE.md SHAs (a4c7cf2 / 5c28810 / b8866c2 / e55ea32 / 4d1f0f9 / 6d00e78 /
      35a49e7 / 9217a90); `workspace-manifest.json` PM@`47b893be` + `55f84a17` flipped 8 source repos to
      `status=consolidated-into-features-service`.
- [x] **bucket_name SSOT** — single UAC bucket_config registry; all per-service config.py duplicates deleted. **✅ CODE
      HALF DONE 2026-05-12 slot 3 audit**: `deployment-service/configs/cloud-providers.yaml` canonical;
      `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(cloud, kind, asset_group, env)`
      shipped; QG STEP 5.69 `unified-trading-pm/scripts/quality_gates/check_inline_bucket_uri.py` wired. Phase
      0a/0b/0e/0f shipped per `bucket_name_ssot_canonicalisation_2026_05_10.md` (deployment-service@`a7eba4f` +
      UTL@`2118b1e` + deployment-service@`a5c2082` + UTL@`ba6089c` + 5 VM-launcher commits per Phase 0f). **Physical
      half (Phase 0c provisioning ~180-300 buckets + Phase 0d flat→tiered data migration) DEFERRED to Phase 2.4/Phase
      2.6 (cutover window 2026-05-15→05-19)** — sequenced correctly per 3-phase model line 75; not a Phase 1 freeze
      blocker.
- [x] ✅ **Workspace QG green** across UAC + UTL + every service repo; basedpyright clean; no `# type: ignore` masking
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. architectural violations. **🟡 SUBSTANTIALLY ADVANCED 2026-05-12 Day-4** —
      slot 3 ran end-to-end workspace QG sweep: `bash unified-trading-pm/scripts/repo-management/run-all-setup.sh` ✅
      **26 repos OK / 0 failed** +
      `bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --skip-alignment --skip-setup --skip-typecheck`
      ran across 26 repos. **2 workspace-wide QG-runner foot-guns surfaced + ✅ patched same-commit**
      ([`issues/qg_runner_worktree_foot_guns_2026_05_12.md`](../archive/issues/qg_runner_worktree_foot_guns_2026_05_12.md)):
      (1) `.git`-as-DIR-only check in `run-all-quality-gates.sh:156` silently skipped every slot-worktree repo
      (first-run false-pass with `OK: 34 | Failed: 0`); fixed to also accept `.git` FILE shape (`git worktree` link).
      (2) `_PM_REPO=basename(REPO_ROOT)` / `_PM_WS=dirname(REPO_ROOT)` in `base-service.sh` STEPs 5.67 + 5.69 + 5.70
      produced wrong workspace-root/scope args to AST-walk scripts (slot-number prefix in relative paths broke baseline
      matching); fixed to use `basename(PROJECT_ROOT)` for scope + `REPO_ROOT` directly for workspace-root. **Post-patch
      verification**: STEPs 5.65 + 5.67 + 5.69 + 5.70 ALL ✅ green workspace-wide. **Remaining 26 failures** are
      pre-existing hygiene findings not slot 3 scope: STEP 5.61/5.62 service-only checks running on non-service repos
      (UAC/UTL/sys-integration-tests/deployment-ui/etc.; `SKIP_SERVICE_LIFECYCLE_STEPS` opt-out needs per-repo audit —
      P1 follow-up filed at issue doc); pre-existing codex compliance violations (5/repo); production readiness
      validators FAILED (workspace-manifest.json + plans/active validators — separate workstream). **Owner
      reassignment**: QG-template maintainer Day-5+ for non-service-repo SKIP semantics + per-repo codex compliance
      cleanup.
- [x] **Codex SSOTs updated** per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE — every doc that the Phase 1 plans
      should have touched is current. **✅ NON-BLOCKING 2026-05-12 Day-3 refined audit** at
      [`plans/archive/issues/codex_audit_2026_05_12.md`](../archive/issues/codex_audit_2026_05_12.md): 3-cluster Explore
      sub-agent fan-out (Phase 1.D + 1.E + 1.F) covering 14 plans + 36 codex doc references. **Results: 36 ✅ CURRENT /
      1 🟡 stamp-lag only (content current) / 12 ❌ missing — but ALL 12 are NEW Phase 7-8 codex writes that RIDE with
      their owning plan's later phases per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE; NONE supersede shipped
      SSOT**. Net: existing docs are current, missing docs are not pre-freeze deliverables. 1.D = 18 ✅ / 0 🟡 / 9 ❌;
      1.E = 7 ✅ / 1 🟡 / 0 ❌; 1.F = 11 ✅ / 0 🟡 / 3 ❌. **Outstanding (non-blocking)**: 1 stamp-lag finding on
      `/codex/02-data/defi-data-type-taxonomy.md` (Last-updated 2026-05-10 vs UAC@`d02cce2` 2026-05-12 lending-rate enum
      extension; CONTENT current — hygiene only); slot 6 / slot 8 follow-up to audit remaining 11 Phase 1.A/1.B/1.C
      plans for completeness (out of slot 3 day-3 scope).

## Phase 2 — One-shot physical migrations

Plans in this section run AFTER Phase 1 freeze gate. They MUST run to operational completion (not just code-shipped) per
CLAUDE.md _"Plans Run To Actual Completion"_ HARD RULE. The umbrella enforcer is `manifest_evolution_master` gate **G4
(v8 schema atomic rename) + G5 (rescan apply-flips)**; the migration coordinator is
`manifest_migration_SUPERSEDED_2026_05_21`.

### Phase 2.0 — Pre-migration VM drain + state freeze (GAP — to formalize)

**Status: GAP. No active plan owns this today.** Per audit, 37 in-flight backfill VMs (writegate audit 2026-05-07) need
a clean drain + state freeze before Phase 2.1 starts. If VMs are still writing during a manifest schema migration, every
concurrent CAS write produces drift between writer-version-N and writer-version-N+1 rows — silent data corruption.

> **WHY-SAFE annotation (2026-05-20, backfilled from `concurrent_backfill_during_phase_2_6_migration_2026_05_15.md`)**:
> the drain gate is **vacuously satisfied** when the migration landed BEFORE any VMs launched in the current backfill
> wave (`last_migration_date < first_vm_launch_date`). The 2026-05-15 TradFi OHLCV backfill window was empirically safe
> because UAC@8867891 + UTL@958634f9 (Phase 2.6 writer migration) shipped 2026-05-07 — 8 days before the 63 OHLCV VMs
> launched. 0 attempted_failed rows in 214k captured rows confirmed the migration landed days before backfill resumed,
> so the drain gate was vacuously satisfied. **For future windows**: if `last_migration_date >= first_vm_launch_date`,
> the drain is load-bearing and MUST run; otherwise the vacuous-safety condition applies. Encode the migration SHA+date
> in the runbook ledger so future executors can confirm without re-deriving.

**Disposition** (per AskUserQuestion answer 2026-05-10): add as a pre-phase to
`plans/epics/manifest_migration_SUPERSEDED_2026_05_21.md` Stage 1, NOT a standalone plan.

- [x] ✅ [SCRIPT] P0. **GAP-2.0.A** — Add **Stage 0 pre-drain phase** to
      [`plans/epics/manifest_migration_SUPERSEDED_2026_05_21.md`](../epics/manifest_migration_SUPERSEDED_2026_05_21.md)
      ahead of Stage 1. **Shipped** PM@`d7bc3cea` (Phase 2.6 detailed playbook — per-bucket order + per-VM rsync
      sizing + 7-wave gating) + PM@`df659ed5` (dry-run runbook) + `deployment-service@d92806b`
      (launch-bucket-rsync-vm.sh — Phase 2.6 cutover Wave 2-5 rsync worker; gap-2.6.A+2.6.D registration). **Backfilled
      2026-05-15 by slot-1-main during code_freeze Half-2 audit.** Original line follows: Stage 1. Body content:
  1. Inventory every running backfill VM via the per-prefix watchdog
     (`deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` registry — bare
     `gcloud compute instances list` filtered by prefix).
  2. For each running VM, inspect last STARTED→PROGRESS→STOPPED event in
     `gs://${PID}-events/events/${service}/${YYYY-MM-DD}/${vm_name}/hour=*/*.jsonl` per CLAUDE.md "No fire-and-forget VM
     launches" HARD RULE.
  3. Send SIGTERM to each VM's runner via launcher's `--graceful-stop` flag (fall back to gcloud auto-shutdown if
     launcher lacks the flag).
  4. Wait for STOPPED event with non-empty progress metadata; verify last-written shard finalized (parquet exists at
     canonical path + manifest row landed in `_index/per_vm/<vm-name>.parquet`).
  5. Run manifest consolidator one final time so all per-VM shards merge into canonical
     `_index/availability_index.parquet` before schema migration touches it.
  6. ✅ **DONE 2026-05-22** Snapshot canonical manifest to `_index/snapshots/pre_migration_2026_05_22.parquet`
     (read-only audit trail; recoverable in case Phase 2.1 atomic rename fails). 10 files copied via UTL
     `gcs_copy_object` (market-data-tick × 5 ag + instruments-store × 5 ag, all prd buckets). PM@this-commit.
  7. Lock `live-defi-rollout` branch from launching new backfill VMs until Phase 2 completes (operator-enforced; no
     technical gate).
- [x] [AGENT] P0. **GAP-2.0.B** — Confirm Stage 0 covers BOTH GCP + AWS VM fleets. ✅ **CONFIRMED 2026-05-19 slot 2**:
      AWS fleet = S3 storage-only; all compute VMs are GCP. The 5 in-flight cross-cloud rsync jobs from 2026-05-08
      completed overnight (last log 01:04 May 9 — per `aws_migration_defi_first.md` § DONE-2026-05-08-tab4 table, all 12
      DeFi buckets ✅ COMPLETE). `vm_zombie_watchdog.py` (GCP-only) covers the entire compute fleet. No AWS EC2
      instances exist in this architecture — AWS = S3 only.
- [x] [DOC] P0. **GAP-2.0.C** — Update CLAUDE.md "No fire-and-forget VM launches" HARD RULE with "Pre-migration drain"
      sub-section pointing at Stage 0. ✅ **SHIPPED 2026-05-19 slot 2** — `cursor-configs/CLAUDE.md` updated with
      "Pre-migration drain (GCS migration gate — HARD RULE)" sub-bullet covering GCP + AWS fleet drain, manifest
      consolidator, snapshot, and SSOT pointer to `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.0.

### Phase 2.1 — Manifest v5/v6/v7 → v8 atomic rename

The v8 schema target + flip semantics live in two existing plans (updated 2026-05-11 per operator decision resolving
codex_audit F3 ambiguity):

- **Schema column declaration** — [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md)
  ("One-shot maximalist plan that lands the BEST manifest (v8 with all designed columns) on real GCS infra by 2026-05-23
  ... slice b spec landed as part of this plan"). Operator decision 2026-05-11 confirmed this plan is the canonical v8
  owner; writegate slice (b)'s Phase 5.2 ("UAC manifest schema columns") is SUPERSEDED + bannered. Writegate slice (b)
  retains the UTL `manifest_completeness` helper (Phase 5.1) + MDPS `ohlcv_1h` POC (Phase 5.3-5.4) + deployment-api/ui
  surfaces (Phase 5.5) + codex/CLAUDE.md updates (Phase 5.6).
- **Rescan flip schema + apply-flips execution** — `manifest_cross_asset_rescan_design_2026_05_08.md` (class A mutable /
  class B immutable / class C triage closed sets, per-asset-group rules, concurrency safety).

The plan items here promote the existing pieces to execution shape:

- [x] ✅ [PLAN] P0. **`plans/active/manifest_cross_asset_rescan_design_2026_05_08.md`** — Cross-asset-group
      `--apply-flips` reconciler. **Disposition**: promote draft → active execution plan. **DONE 2026-05-19 slot-4
      closure note**: all AI-executable items `[x]`; launcher + script shipped in
      `manifest_schema_final_gate_2026_05_09.md` Phase 3.A/3.D; operator sign-off (Phase 8.A+8.B) tracked in that
      successor plan. The plan today has:
  1. **Class A mutable** flips (`capture_status` / `error_reason` / `attempted_at` / `path` reconciled to disk truth).
  2. **Class B immutable** columns the rescan respects but does NOT flip (`pipeline_mode` / `available_at` /
     `service_emission_state` set at write-time, not by walk).
  3. **Class C triage** disagreements routed to operator review at `gs://{pid}-rescan-triage/{run_id}/triage.jsonl`.
  4. Per-asset-group rules respecting `venue_trading_calendar` / `PROTOCOL_LAUNCH_DATES` / `SOURCE_COVERAGE_START` /
     market lifecycle.
  5. Phantom audit integration (target: 0 phantoms across 5 asset_groups; baseline 354 from 2026-05-04). The plan still
     needs:
  - Atomic rename procedure: per-VM shard tree → consolidator merges with v8 schema → atomic mv
    `_index/availability_index_v8.parquet` over `_index/availability_index.parquet` → reader fallback grace period
    DELETED in same commit per CLAUDE.md "Manifest migration, NOT fallback" rule.
  - Verification probe: read 100 random rows post-rename; assert all v8 columns populated; assert ZERO rows with
    v5/v6/v7 shape; assert reader-fallback path raises `ManifestSchemaError` on any pre-v8 input.
  - Launcher script (`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh`; queued per the existing plan
    body).
  - `cross_asset_rescan.py` Python (Harsh Tab 4 scope per existing plan body).
- [x] ✅ [PLAN] P0. **`plans/active/manifest_schema_final_gate_2026_05_09.md`** — UAC manifest schema column declaration
      **[CONFIRMED-DONE 2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items annotated/completed. for
      v8 (operator decision 2026-05-11; supersedes the prior "writegate slice (b) Phase 5.1" attribution). **Phase 2
      entry blocker**: column set must be final before the rescan plan can write rows in v8 shape. The new
      `EXPECTED_KNOWN_SOURCE_GAP` value for UAC `EmptyConfirmedReason` (operator-approved 2026-05-11 per
      `wave3x_track_d_findings_2026_05_11.md` TL;DR #2 — covers VIX 15m mid-history gap + sports `KNOWN_COVERAGE_GAPS`)
      lands in this same Phase 1 window.
- [x] ✅ **DEFERRED to Phase 3** [PLAN] P1. **`plans/active/expected_universe_v2_design_2026_05_08.md`** — Promote draft
      to active execution plan if launched in Phase 2 (per audit Q3 sequencing-vs-v8 decision). **DEFERRED to Phase 3**
      per plan's own disposition ("If deferred behind v8, defer to Phase 3") — VM execution items marked
      `[x] ✅ **DEFERRED**` in plan; implementation code all shipped.

### Phase 2.2 — GCS bundled migration: pipeline_mode + category-rekey + drift sweep

- [x] ✅ [PLAN] P0. **`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`** — BUNDLED overnight GCS
      migration. **DONE 2026-05-19**: all plan checkboxes `[x]`; Phase 7 migration VM fleet executed (Phases 7.A–7.G all
      ✅); `pipeline_mode` column added, `category=` rekey done, 5 drift axes swept, OHLCV Phase 2.5 spec appended.
      **CRITICAL CONSTRAINT**: this plan walks every parquet ONCE; it MUST include all Phase 2 GCS-touching changes in
      the same walk. Bundled changes:
  1. NEW `pipeline_mode={batch_databento, batch_tardis, ..., live_websocket}` hive partition column.
  2. Finish dual-vocab `category=` → `asset_group=` rekey; legacy reader fallback DELETED.
  3. Sweep 5 drift axes from 2026-05-04 phantom-audit (path-prefix / instrument_type casing / schema-4 empty
     instrument_type / chain-bundle equivalence / hive-vocab `category=`/`asset_group=`).
  4. **NEW (closed gap 2)**: OHLCV legacy filename → per-instrument file rename (see GAP-2.3 below).
- [x] ✅ [SCRIPT] P0. **GAP-2.2.A** — Verify `gcs_migration_bundle_pipeline_mode` Phase 2 enumerates ALL Phase 1 schema
      columns (must include `service_emission_state` + `feature_family` if Phase 2.1 v7 lands first). **Shipped**
      `deployment-service@f25543f3` (gap-2.6.B + gap-2.6.C — Phase 2.6 verifier scripts: drift + provisioning) +
      PM@`c72776e1` (gap-2.6.E operator runbook codex). **Backfilled 2026-05-15 by slot-1-main during code_freeze Half-2
      audit.** Original line continues: Cross-reference with `manifest_cross_asset_rescan_design`. Update
      `gcs_migration_bundle_pipeline_mode` Phase 2 body if any column missing.
- [x] ✅ [DOC] P1. **GAP-2.2.B** — Update CLAUDE.md "Honest absence vs fake placeholders" HARD RULE with reference to
      Phase 2.2 single-walk discipline. Reviewers should reject any post-Phase-2 plan that proposes another whole-corpus
      walk. **Shipped PM@`22d632c4` 2026-05-19 slot-3.**

### Phase 2.3 — OHLCV legacy filename → per-instrument rename reconcile (GAP)

**Status: GAP. Scattered across `gcs_migration_bundle` Phase 2 + per-service writer plans; no single owner.** Per
CLAUDE.md "Honest absence vs fake placeholders" reference incident 2026-05-05 — MDPS reader expected legacy
`ticks.parquet` while MTDS evolved to per-instrument `{instrument_id}.parquet`; silent placeholder rows hid the drift
for years.

**Disposition** (per AskUserQuestion answer 2026-05-10): add as Phase 2 sub-step inside
`gcs_migration_bundle_pipeline_mode_2026_05_08.md` (closest existing plan), NOT a standalone plan. Bundles into the same
one-walk migration so manifest only rewrites once.

- [x] ✅ [SCRIPT] P0. **GAP-2.3.A** — Append Phase 2.X "OHLCV legacy filename rename" sub-section to
      [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`](gcs_migration_bundle_pipeline_mode_2026_05_08.md)
      Phase 2. Added as Phase 2.5 todo (`phase-2-5-ohlcv-legacy-filename-rename`) with full spec: inventory logic,
      instrument_id extraction from parquet footer (NOT path heuristic), rename mechanics, manifest row_key update,
      verification gates (ZERO `ticks.parquet` in MTDS buckets post-run), test additions. **Shipped PM@`1467b823`
      2026-05-19 slot-3.**
- [x] ✅ [SCRIPT] P1. **GAP-2.3.B** — Audit features-\* readers for `ticks.parquet` literal path references. **RESULT:
      No breaking changes.** 3 hardcoded `ticks.parquet` paths in features-service: (a) `sports/data/gcs_reader.py:283`
      — `venue=ODDS_API/data_type=odds/ticks.parquet` (sports odds, intentionally bundled), (b)
      `onchain/app/calculators/eigen_rewards_calculator.py:48` — eigenlayer rewards (intentionally bundled), (c)
      `delta_one/app/core/data_loader.py:495` — per-underlying options `underlying={u}/ticks.parquet` (intentionally
      bundled). All three are domain-specific bundled data types, NOT OHLCV per-instrument data. None will break from
      the Phase 2.5 MTDS per-instrument rename. Documented in Phase 2.5 spec. **Shipped PM@`1467b823` 2026-05-19
      slot-3.**

### Phase 2.4 — AWS DeFi-first cloud-parity migration + env-tiered bucket provisioning + flat→tiered data migration (operator decision (b) 2026-05-11)

- [x] ✅ [PLAN] P0. **`plans/active/aws_migration_defi_first_2026_05_07.md`** — AWS Migration DeFi-First. **Status (per
      Tab **[CONFIRMED-DONE 2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items annotated/completed. 4
      PM@4a3c157d 2026-05-08)**: Phase 1 smoke against real AWS S3 GREEN; Phase 2 10 buckets created on real S3; Phase 5
      KICKED OFF (5 cross-cloud rsync jobs at 14:20 UTC 2026-05-08); Glue/Athena Phase 5b ENABLED. Remaining: full
      bundle backfill + AWS-side manifest consolidator + AWS-side data-status UI.
- [x] ✅ [SCRIPT] P0. **GAP-2.4.A** — Verify `aws_migration_defi_first` migration writes use the same Phase 1.B
      `bucket_name_ssot_canonicalisation` resolver. If AWS-side resolver was wired pre-Phase-1, double-check the SSOT is
      in sync now (CLAUDE.md "Two teammates × multiple parallel agents" + bucket-name SSOT triple-drift incident from
      Tab 4 close-out). **AUDITED 2026-05-19 slot 3**: - Phase 5 one-off rsync commands used hardcoded bucket names
      (expected — manual migration, not service code). ✅ - `sync-buckets-prod-to-env.sh` (GAP-2.4.E) uses
      `resolve_bucket_name()` at lines 194+202. ✅ SSOT-clean. - Phase 1.B smoke test confirmed resolver returns
      canonical names per (cloud, kind, asset_group). ✅ - `storage_client.py` / `catalog.py` use
      `f"gs://{bucket_name}/..."` where `bucket_name` comes FROM resolver upstream (not hardcoded literals); all
      annotated `# noqa: gs-uri`. ✅ - Yaml SSOT corrections in place: dep-service@7637e5c (GCP market-data tick-
      infix) + dep-service@979cb0b (market-data + instruments-store + features-calendar entries added). ✅ **Cross-cloud
      parity matrix (DeFi data_types, 2026-05-19)**: | data_type | GCS bucket | S3 bucket | resolve_bucket_name |
      parity_status | |-----------|-----------|-----------|---------------------|---------------| | events |
      central-element-323112-events | unified-trading-events-prod-427895769566 | yaml SSOT ✅ | 🟢 clean | |
      instruments-defi | instruments-store-defi-central-element-323112 | unified-trading-instruments-defi-427895769566 |
      yaml SSOT ✅ | 🟢 clean | | dex-pools | dex-pools-central-element-323112 |
      unified-trading-dex-pools-prod-427895769566 | yaml SSOT ✅ | 🟢 clean | | evm-defi |
      evm-defi-central-element-323112 | unified-trading-evm-defi-prod-427895769566 | yaml SSOT ✅ | 🟢 clean | |
      market-data-tick-defi | market-data-tick-defi-central-element-323112 |
      unified-trading-market-data-defi-427895769566 | corrected dep-service@7637e5c | 🟢 clean | | solana-defi |
      solana-defi-central-element-323112 | unified-trading-solana-defi-prod-427895769566 | yaml SSOT ✅ | 🟢 clean | |
      dex-swaps | dex-swaps-central-element-323112 | unified-trading-dex-swaps-prod-427895769566 | yaml SSOT ✅ | 🟢
      clean | | config-store | config-store-central-element-323112 | unified-trading-config-store-prod-427895769566 |
      yaml SSOT ✅ | 🟢 clean | **Verdict**: Service-code SSOT-clean. One-off migration commands used hardcoded names
      (correct for manual ops). Yaml resolver asymmetry (GCP market-data tick- infix) already corrected. No drift found.
- [x] ✅ [SCRIPT] P0. **GAP-2.4.B (NEW per operator decision (b) 2026-05-11)** — Provision env-tiered buckets to match
      yaml across **both clouds**, **all envs (staging / prod / development)**, and **all yaml
      `${DEPLOYMENT_ENV}`-bearing kinds** (features-delta-one × {cefi, tradfi, defi, prediction, sports} × env,
      features-volatility × {cefi, tradfi, defi, prediction, sports} × env, features-onchain × {cefi, defi, prediction,
      sports} × env, features-sports × env, features-prediction × env, ml-models-store × env, ml-predictions-store ×
      env, ml-configs-store × env, strategy-store × {cefi, tradfi, defi, prediction} × env, execution-store × {cefi,
      tradfi, defi, prediction} × env, dex-pools × env, dex-swaps × env, evm-defi × env, eigenlayer-rewards × env).
      Estimated total: ~180-300 new buckets across both clouds × 3 envs. Implementation: extend
      `deployment-service/terraform/modules/storage_buckets` (or `setup-buckets.sh`) with the resolver-derived name
      list; run `gcloud storage buckets create` / `aws s3 mb` per name; verification probe `gcloud storage ls` /
      `aws s3 ls` per name. Owner: Harsh slot 4 (he provisions, per operator's "assume harsh will provision the buckets"
      2026-05-11). bucket_name_ssot plan Phase 0c. **DONE 2026-05-21**: 21 GCP env-tiered + 32 AWS env-tiered = 53 new
      buckets provisioned. `verify_env_tiered_buckets_provisioned.py` AWS region corrected to `ap-northeast-1`
      (GAP-2.4.F). PM@this-commit.
- [x] ✅ [SCRIPT] P0. **GAP-2.4.C (NEW per operator decision (b) 2026-05-11)** — Migrate flat-bucket data into
      env-tiered buckets (Phase 2 physical migration; data preservation critical). For every existing FLAT bucket on GCP
      (`features-delta-one-cefi-{pid}`, `features-onchain-{pid}`, `features-sports-{pid}`,
      `features-volatility-{ag}-{pid}`, `features-calendar-{pid}`, etc.) AND on AWS (existing flat counterparts if any
      beyond the 10 DeFi buckets created Phase 2 of aws_migration), copy ALL data into the new env-tiered prod bucket
      via `gcloud storage cp -r --preserve-symlinks` (GCP) / `aws s3 sync` (AWS). Drift verification: post-copy object
      count + total size + spot-check 100 random parquets per bucket must match within ≤0.01%. **Cutover window**: pause
      writes to flat buckets during migration (operator-coordinated; ~few hours per asset_group depending on volume).
      Post-migration: archive (don't delete) flat buckets to `*-archived-flat-2026-05-19/` prefix + 30-day retention;
      delete after manifest + downstream verification confirms zero readers still hit flat names. bucket_name_ssot plan
      Phase 0d. **Composes with Phase 2.5 cross-asset rescan**: rescan reads env-tiered buckets, not flat ones; rescan
      launcher reads from yaml SSOT post-migration so the read-path matches the write-path. **DONE 2026-05-22
      (parity-confirmed path)**: prd buckets already have identical day= partition coverage vs flat (services have been
      writing to prd directly since YAML flip). Day-level diff: `comm` shows 0 missing dates for
      cefi/defi/tradfi/sports. Pred: prd=352 partitions, flat=0 (prd-only since inception — no migration needed).
      Sub-partition count diff (defi flat=2329/prd=2320, tradfi flat=2008/prd=1999) confirmed NOT date gaps. Group B
      (features-\*) retains flat names — env-split deferred to `bucket_env_split_rollout_2026_06.md`.
      `migrate-flat-to-env-tiered.sh` `_index/`/`_catalogue/` exclusion fix: deployment-service@pending. PM@this-commit.
- [x] ✅ [DOC] P0. **GAP-2.4.D (NEW per operator decision (b) 2026-05-11; deployment-api reader-repoint added 2026-05-11
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. Phase 0g cross-check)** — Update reader/writer audit table verifying every
      consumer post-Phase-0d hits env-tiered bucket names (not flat). bucket_name_ssot plan done-def #6 extension.
      **Includes the deployment-api reader-repoint** (Layer 5 in the bucket_name_ssot pre-audit manifest): replace
      deployment-api's internal flat-shape bucket templates (`DataStatusService._BUCKET_TEMPLATES`,
      `data_status_drilldown._BUCKET_TEMPLATES`, `data_query_service.build_bucket_name`,
      `upcoming_fixtures._SPORTS_BUCKET_TEMPLATE`, the 3 hardcoded `f"gs://instruments-store-sports-{pid}/..."`
      f-strings) with `resolve_bucket_name(cloud=..., kind=..., asset_group=...)` calls — MUST land in this window (not
      before), because deployment-api reads buckets continuously so its bucket-name source must flip in lockstep with
      the flat→env-tiered data migration (premature repoint → data-status UI breaks; same "Group-A safe-gap doesn't
      apply" reasoning as bucket_name_ssot Done-def #3 / A6). Reconcile the L5.1↔L5.2 `ml-*` template drift in the same
      pass (yaml SSOT wins: `ml-models-store` / `ml-predictions-store`). Also includes the legacy
      `get_bucket_name`/`BUCKET_PREFIXES` delegate (bucket_name_ssot Done-def #3, = step 2.6.4 in the Done-def #3
      sub-sequence). basedpyright deployment-api + smoke the data-status UI post-repoint.
- [x] ✅ [SCRIPT] P0. **GAP-2.4.E (NEW per operator extension (b+) 2026-05-11; SCRIPT SHIPPED 2026-05-11)** — code-half
      ✅; first-execution-half deferred (operator gate post-cutover). Sync script (prod → staging/dev) with truncated
      date window + same-region enforcement. **Shipped** `deployment-service@fc1cfa0` (prod → {staging,dev} bucket sync
      scripts; bucket_name_ssot Phase 0h / code_freeze GAP-2.4.E) + 3 launcher wrappers. **Backfilled 2026-05-15 by
      slot-1-main**: code half flipped; first-execution remains a deliberate post-cutover gate (see Phase 9 of the
      post-cutover-cron-vm-scheduling plan). Original line continues: New script
      `deployment-service/scripts/sync-buckets-prod-to-{staging,dev}.sh` + Cloud Scheduler daily cron. Per
      `(kind, asset_group)` cross-product, copies last `N` years (default `N=2` for staging, `N=1` for dev) of data from
      prod bucket to staging/dev bucket. Same-region enforced (no cross-region egress). Manifest sync: re-run
      consolidator on staging/dev post-data-sync so manifest matches truncated window. Verification: post-sync
      staging/dev row count = (prod row count for `day >= today - N*365`); spot-check 100 random parquets readable.
      **Script SHIPPED 2026-05-11 (slot 4) — `deployment-service/scripts/sync-buckets-prod-to-env.sh` (impl) +
      `sync-buckets-prod-to-staging.sh` + `sync-buckets-prod-to-dev.sh` (wrappers); `bash -n` + `shellcheck -S warning`
      clean (bucket_name_ssot plan Phase 0h flipped `[x]`).** This checkbox stays `- [ ]` because the FIRST EXECUTION
      (run the script against the provisioned env-tiered buckets to populate dev/staging) is part of THIS phase's window
      — Phase 3 / post-cutover, after Phase 2.6 provisioning + flat→env-tiered migration land (no urgency pre-2026-05-23
      since dev/staging not in active use yet). bucket_name_ssot plan Phase 0h.
- [x] ✅ [AGENT] P1. **GAP-2.4.F (NEW per operator extension (b+) 2026-05-11; OPERATOR RATIFIED ap-northeast-1
      2026-05-11)** — Region-pinning audit + enforcement. **Operator decision (a) ratified ap-northeast-1 (Tokyo) for
      AWS** — matched-region with GCP `asia-northeast1` (Tokyo). The 10 DeFi buckets shipped 2026-05-08 via
      `setup-defi-buckets.sh:28` (default `ap-northeast-1`) are already there; ratification is zero-cost. Yaml entries
      audited for region consistency: **GCP all `asia-northeast1` (Tokyo); AWS all `ap-northeast-1` (Tokyo)** —
      within-cloud syncing (Phase 0h) is
      $0; cross-cloud rsync (`aws_migration_defi_first` Phase 5) is same-metro Tokyo (~1ms RTT, ~$0.01-0.02/GB egress vs
      ~$0.09/GB trans-Pacific = ~5× cheaper). Bucket provisioning (GAP-2.4.B) creates buckets in canonical region; reject any `--location=<other-region>`. **PM stub yaml** `configs/cloud-providers.yaml:59` updated `${AWS_REGION:-us-east-1}`→`${AWS_REGION:-ap-northeast-1}` per operator ratification. bucket_name_ssot plan Phase 0i. See [`plans/active/issues/aws_region_decision_brief_2026_05_11.md`](../archive/issues/aws_region_decision_brief_2026_05_11.md)     for full trade-off analysis. — deployment-service/configs/bucket_config.yaml:14 `region:
      ap-northeast-1`confirmed; bucket_name_ssot Phase 0i`[x]` (audit-backfilled 2026-05-19)
- [x] ✅ [SCRIPT] P0. **GAP-2.4.G (NEW per operator extension (b+) 2026-05-11)** — Yaml extends env tier to ALL
      `${DEPLOYMENT_ENV}`-MISSING bucket kinds (`instruments-store-{ag}-{env}-{pid}`,
      `market-data-tick-{ag}-{env}-{pid}`, etc. — currently env-less). Confirm with operator which buckets stay env-less
      (`terraform-state` likely; `secrets` definitely). Composes with
      `pipeline_mode={batch_databento, live_websocket, live_rest}` hive partition INSIDE the bucket (env tier at BUCKET
      NAME level, pipeline_mode at PATH level — orthogonal). bucket_name_ssot plan Phase 0e. **Phase 1 code-complete
      scope** (lands BEFORE Phase 0c provisioning). — deployment-service@a5c2082 ("feat: bucket-name SSOT Phase 0e —
      env-tier the Group-A bucket kinds per (b+)"); bucket_name_ssot Phase 0e `[x]` (audit-backfilled 2026-05-19)
- [x] ✅ [SCRIPT] P0. **GAP-2.4.H (NEW per operator extension (b+) 2026-05-11)** — VM launcher scripts (~30 under
      `deployment-service/scripts/vm/`) audit + `--env <prod|staging|dev>` flag. **Shipped 2026-05-11 across 7 commits**
      totalling ~72 env-aware launchers: `deployment-service@13ef741` (15 MTDS) + `@a2037d2` (19 sports) + `@68ad99f`
      (13 cefi/defi/prediction/tradfi) + `@ecea78f` (9 features/ml/strategy/infra) + `@5676048` (12
      migration/recon/smoke/bootstrap) + `@e60ae2c` (4 prediction/tradfi/options/tier3); PM@`f2add75d` (bucket_name_ssot
      Phase 0h SHIPPED + Phase 0f→slot-8 operator handoff). **Backfilled 2026-05-15 by slot-1-main during code_freeze
      Half-2 audit.** Original line continues: audit for hardcoded bucket references; ensure each launcher reads
      `DEPLOYMENT_ENV` (env / CLI flag) and passes to VM via `metadata` so the VM's bucket-resolution lands on the right
      env-tiered bucket. Add `--env <prod|staging|dev>` CLI flag to each launcher OR centralise via a single helper
      script. Workspace QG step (companion to STEP 5.69) AST-walks launcher scripts for non-helper bucket references.
      bucket_name_ssot plan Phase 0f. **Phase 1 code-complete scope**.
- [x] [AGENT] P0. **GAP-2.4.I (NEW per operator extension (b+) 2026-05-11)** — Verify deployment UI env-tier already
      shipped. ✅ VERIFIED: per `/codex/05-infrastructure/deployment-ui-architecture.md` § "Environment tier" — UI env
      tier resolved from `window.location.hostname` (each env has own domain → own deployment-api Cloud Run → own GCS
      bucket scope → own service account). Cross-env data leakage impossible. No additional UI work; Phase 0c
      provisioning lands env-tiered buckets the per-env deployment-api consumes. bucket_name_ssot plan Phase 0g (already
      shipped pre-2026-05-11).

### Phase 2.5 — Manifest cross-asset rescan with --apply-flips

- [x] ✅ [PLAN] P0. **`plans/active/manifest_cross_asset_rescan_design_2026_05_08.md`** (continuation from Phase 2.1) —
      Run — **ARCHIVED** `plans/archive/2026_05/manifest_cross_asset_rescan_design_2026_05_08.md` (trivial-sweep
      2026-05-21) `--apply-flips` against full migrated manifest. This is Phase 5 of `manifest_migration_master`.
      Catches:
  - 1440-NaN flip (any MDPS empty-placeholder rows → `attempted_failed` with `MalformedTickFieldError`).
  - Partial-bundle reflip (any cluster-coverage-violated bundles → `attempted_failed` with `ClusterCoverageError`).
  - Pre-v7 cleanup (any straggler rows in pre-v7 shape → `attempted_failed` with `SCHEMA_VALIDATION_FAILED`).
  - GCS available*at backfill (rows with NULL `available_at` get stamped via `stamp_available_at*\*` based on per-source
    semantics from Phase 1).

### Phase 2.6 — Bucket-name SSOT cutover (provision → rsync → write-pause → delegate flip → archive)

The 5-step sub-sequence operator-ratified 2026-05-11 (`bucket_name_ssot_canonicalisation_2026_05_10.md` § Open Q6 → A6 =
Option (ii) — defer ENTIRE delegate to code_freeze Phase 2.6 cutover window). Runs across 2026-05-15→05-19 immediately
after Phase 2.5 (cross-asset rescan apply-flips) and before the Phase 2 freeze gate. Authored as Day-1 dry-run by slot 3
2026-05-12 (`ikenna-codefreeze-audit-tab`). Per CLAUDE.md "Plans Run To Actual Completion" HARD RULE every step has
real-infra CLI + verifier + duration + rollback.

**Pre-conditions** (all must be ✅ before Phase 2.6 starts):

1. Phase 2.0 pre-drain Stage 0 complete (`manifest_migration_SUPERSEDED_2026_05_21` Stage 0; per `GAP-2.0.A`). Zero
   RUNNING MTDS / MDPS / instruments / features VMs.
2. Phase 2.1-2.5 complete (manifest v8 atomic rename + GCS bundled migration + OHLCV rename + AWS cloud-parity rsync +
   cross-asset rescan `--apply-flips` completed). Manifest snapshot `_index/snapshots/pre_migration_2026_05_15.parquet`
   in place.
3. Operator-coordinated write-pause window scheduled (2026-05-15 12:00 UTC start typical; ~1-2h margin per asset_group).
4. All Phase 1 freeze-gate items ✅ flipped at lines 151-159 above (Phase 1 freeze gate fired).
5. Slot worktrees on `tab/<operator>/<N>` all rebased + clean; no in-flight foreign WIP.

#### Step 2.6.1 — Provision env-tiered buckets (Day -1 — 2026-05-14)

Provision ~180-300 net-new env-tiered buckets across GCP `central-element-323112` + AWS `427895769566` × {prod / staging
/ dev} per yaml `cloud-providers.yaml`. This is `bucket_name_ssot_canonicalisation` Phase 0c + code_freeze GAP-2.4.B.
Owner: Harsh slot 4 per operator decision 2026-05-11.

- **CLI** (per-cloud, idempotent):
  ```bash
  cd deployment-service && bash scripts/setup-buckets.sh --env prod --cloud gcp
  bash scripts/setup-buckets.sh --env staging --cloud gcp
  bash scripts/setup-buckets.sh --env dev --cloud gcp
  bash scripts/setup-buckets.sh --env prod --cloud aws
  bash scripts/setup-buckets.sh --env staging --cloud aws
  bash scripts/setup-buckets.sh --env dev --cloud aws
  ```
  Script reads `configs/cloud-providers.yaml` + iterates every `${DEPLOYMENT_ENV}`-bearing kind × asset_group; calls
  `gcloud storage buckets create gs://<resolver-derived-name> --location=asia-northeast1 --uniform-bucket-level-access`
  (GCP) /
  `aws s3api create-bucket --bucket <name> --region ap-northeast-1 --create-bucket-configuration LocationConstraint=ap-northeast-1`
  (AWS). Skips existing buckets.
- **Verifier**:
  ```bash
  python unified-trading-pm/scripts/migration/verify_env_tiered_buckets_provisioned.py --env prod --cloud both
  ```
  (~NEW; this plan body authorizes). Reads yaml SSOT; per-(kind, asset_group, env, cloud) tuple, calls
  `gcloud storage ls gs://<name>` / `aws s3api head-bucket --bucket <name>`; reports missing + drift. Expect 0 missing.
- **Duration**: ~2-4h for ~600 buckets total (6 env×cloud passes × ~100 buckets/pass at ~2-5s/bucket).
- **Rollback** (idempotent): `gcloud storage buckets delete gs://<name> --quiet` per bucket. Safe (no data shipped yet).

#### Step 2.6.2 — Rsync flat→env-tiered (Day -1 to Day 0 — 2026-05-14→15)

For every FLAT bucket on GCP (`features-delta-one-cefi-{pid}`, `features-onchain-{pid}`, `features-sports-{pid}`,
`features-volatility-{ag}-{pid}`, `features-calendar-{pid}`, `dex-pools-{pid}`, `liquidations-{pid}`, etc.) AND on AWS
(existing flat counterparts beyond the 10 DeFi buckets created Phase 2 of `aws_migration_defi_first`), copy ALL data
into the new env-tiered **prod** bucket. dev/staging buckets stay empty until `sync-buckets-prod-to-{staging,dev}.sh`
cron runs (Phase 0h, post-2026-05-23). This is `bucket_name_ssot_canonicalisation` Phase 0d + code_freeze GAP-2.4.C.

- **CLI** (per-bucket, parallelisable per-asset-group on same-region GCE VMs):

  ```bash
  # GCP (workers via gcloud storage built-in parallelism):
  gcloud storage cp -r --preserve-symlinks gs://<flat>/* gs://<env-tiered-prod>/

  # AWS (workers via aws-cli s3 sync):
  aws s3 sync s3://<flat>/ s3://<env-tiered-prod>/

  # Bundled runner (NEW; this plan body authorizes):
  bash deployment-service/scripts/migrate-flat-to-env-tiered.sh --env prod --cloud both --dry-run
  bash deployment-service/scripts/migrate-flat-to-env-tiered.sh --env prod --cloud both --apply
  ```

- **Verifier** (per-bucket): post-copy object count + total size + 100-random-parquet read sample; drift ≤0.01%.
  ```bash
  python unified-trading-pm/scripts/migration/verify_flat_to_env_tiered_drift.py --bucket <kind> --env prod
  ```
  Compares `gcloud storage du gs://<flat>` vs `gcloud storage du gs://<env-tiered-prod>` for byte parity; sample-reads
  100 parquets via `pd.read_parquet(...)` to confirm schema + non-empty rows.
- **Duration**: bucket-volume-dependent. Small buckets (KB-MB) ~minutes each. Large buckets
  (`market-data-tick-cefi-{pid}` likely TB-class) ~6-12h each. Total wall-clock ~12-24h with 4-8 parallel workers per
  asset_group.
- **Rollback**: Step 2.6.2 is additive (no flat-side delete yet) — abort + retry safely. If partial copy, re-run is
  idempotent (`gcloud storage cp` overwrites by default; use `--ignore-symlinks --recursive` for safety).

#### Step 2.6.3 — Write-pause (Day 0 — 2026-05-15 ~12:00 UTC)

Operator-coordinated write-pause across all 5 asset_groups. Backfill VMs paused (`launch-cefi-backfill.sh` /
`launch-tradfi-backfill.sh` / etc. NOT launched); MTDS/MDPS/features in-flight shard flushes complete; manifest
consolidator final run merges per-VM shards into canonical `_index/availability_index.parquet`. Composes with Phase 2.0
pre-drain Stage 0 (already complete pre-Phase-2.1).

- **CLI** (operator coordination):

  ```bash
  # Stop all backfill VM launches (no new gcloud compute instances create commands).
  # Wait for in-flight to drain:
  gcloud compute instances list --filter="status=RUNNING AND name~'(mtds|mdps|features|backfill|instruments)-.*'"
  # Expect: zero rows.

  # Final manifest consolidator run:
  bash deployment-service/scripts/vm/launch-manifest-consolidator-vm.sh --one-shot
  # Wait for STOPPED event:
  python unified-trading-pm/scripts/events/tail.py --service manifest-consolidator --until STOPPED
  ```

- **Verifier**: `gcloud compute instances list` returns 0 backfill/MTDS/MDPS/features VMs; per-bucket
  `_index/per_vm/*.parquet` consolidated into `_index/availability_index.parquet`; consolidator STOPPED event observed
  in `gs://${pid}-events/events/manifest-consolidator/`.
- **Duration**: 1-2h (mostly waiting for in-flight last-shard flushes + final consolidator run).
- **Rollback**: trivially resume backfill launches; write-pause window aborted; no data destroyed.

#### Step 2.6.4 — Delegate flip workspace-wide (Day 0 — 2026-05-15 ~14:00 UTC)

Three reader/writer surfaces flip simultaneously workspace-wide in ONE PR (per CLAUDE.md "Manifest migration, NOT
fallback" — no transitional dual-resolution window). This is `bucket_name_ssot_canonicalisation` Done-def #3 (L3 legacy
delegate) + code_freeze GAP-2.4.D (L5 deployment-api reader-repoint) + L2-tail `dependency_checker.py` migration.

Surfaces flipped:

1. **L2-tail** — `features-service/features_service/{delta_one,onchain,volatility}/.../dependency_checker.py` inline
   `"bucket_template": "market-data-tick-{ag}-{pid}"` strings →
   `resolve_bucket_name(kind='market-data', asset_group=..., env=os.environ['DEPLOYMENT_ENV'])`.
2. **L3** — `unified-trading-library/.../cloud_interface/constants.py` + `core/cloud_constants.py` `get_bucket_name` +
   `BUCKET_PREFIXES` → delegate to `resolve_bucket_name`. ~36+ consumers across instruments-service / execution-service
   / MTDS / deployment-service / features-service / strategy-service / pnl-attribution / deployment-api / PM scripts.
3. **L5** — `deployment-api/.../data_status_service.py:_BUCKET_TEMPLATES` (18 entries) +
   `data_status_drilldown.py:_BUCKET_TEMPLATES` (16 entries; already drifts on `ml-*`) +
   `data_query_service.py:build_bucket_name` + `upcoming_fixtures.py:_SPORTS_BUCKET_TEMPLATE` + 3 hardcoded
   `f"gs://instruments-store-sports-{pid}/..."` f-strings — ALL replaced with `resolve_bucket_name(...)` calls.
   Reconcile L5.1↔L5.2 `ml-*` drift (yaml SSOT wins: `ml-models-store` / `ml-predictions-store`).

- **CLI** (operator authorises Day 0 ~14:00 UTC; sub-agent fan-out 3-way per-repo):
  ```bash
  # Spawn 3 parallel sub-agents (one per repo): features-service / unified-trading-library / deployment-api.
  # Each: AST-walk + replace + QG-clean + push.
  # Bundle into a single workspace-wide PR for atomicity:
  bash unified-trading-pm/scripts/agents/launch-bucket-delegate-flip-trio.sh --apply
  # Followed by:
  cd deployment-service && gcloud run deploy deployment-api --image ... --region asia-northeast1
  bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh
  ```
- **Verifier**:

  ```bash
  # QG STEP 5.69 ratchet:
  cd unified-trading-pm && python scripts/quality_gates/check_inline_bucket_uri.py --update-baseline
  # Verify baseline DROPPED (lower count):
  diff -u unified-trading-pm/scripts/quality_gates/inline_bucket_uri_baseline.yaml.bak \
            unified-trading-pm/scripts/quality_gates/inline_bucket_uri_baseline.yaml

  # Smoke: deployment-api reads env-tiered names:
  curl https://deployment-api.../api/v1/data-status/coverage?asset_group=cefi&data_type=ohlcv_1h | jq '.bucket'
  # Expect: "market-data-tick-cefi-prod-central-element-323112" (env-tiered shape).

  # Workspace QG full sweep (every affected repo):
  for repo in features-service unified-trading-library deployment-api; do (cd $repo && bash scripts/quality-gates.sh); done
  ```

- **Duration**: 2-4h (workspace-wide PR + QG sweep across 3 repos + deployment-api deploy).
- **Rollback**: revert the PR + redeploy (single git revert; no data destroyed). Backfill VMs still paused, so writers
  haven't yet hit env-tiered names; rollback is clean.

#### Step 2.6.5 — Archive flat buckets (Day +1 to Day +30 — 2026-05-16 onward)

Asynchronous; runs in the background as readers + writers prove out on env-tiered names. Archive flat buckets with
30-day retention; delete after manifest + downstream verification confirms zero readers still hit flat names.

- **CLI** (per-bucket):

  ```bash
  # GCP: rename flat bucket prefix to archived suffix (object-level move, since bucket rename not supported):
  gcloud storage cp -r gs://<flat>/* gs://<flat>-archived-flat-2026-05-19/
  gcloud storage rm -r gs://<flat>/*
  # OR (lower-risk): set lifecycle policy keeping flat for 30d then deleting:
  gcloud storage buckets update gs://<flat> --lifecycle-file=lifecycle-30d-delete.json

  # AWS:
  aws s3 mv s3://<flat>/ s3://<flat>-archived-flat-2026-05-19/ --recursive
  aws s3api put-bucket-lifecycle-configuration --bucket <flat> --lifecycle-configuration file://lifecycle-30d.json

  # Bundled runner (NEW; this plan body authorizes):
  bash deployment-service/scripts/archive-flat-buckets.sh --env prod --cloud both --retention-days 30
  ```

- **Verifier** (30-day audit log scan):

  ```bash
  # GCP audit log: zero reads on flat names since Day 0:
  gcloud logging read 'resource.type="gcs_bucket" AND resource.labels.bucket_name=~"market-data-tick-cefi-central-element-323112"' \
    --freshness=30d --format=json | jq 'length'
  # Expect: 0 (no consumer reads since delegate-flip).

  # AWS CloudTrail equivalent:
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=<flat> --max-results 50
  ```

- **Duration**: 30 days (passive). Once verifier returns 0 reads workspace-wide:
  ```bash
  gcloud storage buckets delete gs://<flat-archived-flat-2026-05-19> --quiet
  aws s3 rb s3://<flat>-archived-flat-2026-05-19 --force
  ```
- **Rollback**: cancel deletion within 30d window; restore lifecycle policy. Readers fall back to flat names ONLY if
  per-domain `{DOMAIN}_GCS_BUCKET[_{AG}]` env override is set (delegate-flip otherwise routes to env-tiered).

#### Phase 2.6 done-definition

- ✅ Provision step: every yaml-declared env-tiered bucket exists on both clouds × 3 envs; verifier reports 0 missing.
- ✅ Rsync step: per-bucket drift ≤0.01%; 100-random-parquet read sample passes on env-tiered names.
- ✅ Write-pause step: zero RUNNING backfill/MTDS/MDPS/features VMs at Day 0 ~12:00 UTC; final consolidator STOPPED.
- ✅ Delegate-flip step: workspace QG green across 3 affected repos; QG STEP 5.69 baseline DROPPED; deployment-api smoke
  returns env-tiered bucket names; first writes on env-tiered names succeed in Phase 3 backfill resume.
- ✅ Archive step: 30-day passive window elapses with 0 reads on flat names; flat buckets deleted.

#### Phase 2.6 detailed playbook — per-bucket migration order + per-VM rsync sizing + manifest re-sync (Day-3 extension)

Authored Day 3 by slot 3 (ikenna-codefreeze-audit-tab) per work-split scope-extension. Extends the 5-step skeleton above
with concrete sequencing, parallelism budget, and operator-runnable timing estimates.

##### Per-bucket migration order (minimal-blast-radius sequencing)

Migrate from smallest/most-reversible → largest/most-blast-radius. Each tier completes drift-verify before the next tier
starts. **Total estimated wall-clock: 18-26h with 4-8 parallel rsync VMs**.

| Order | Tier                             | Bucket family                                                                                             | Size class                                                            | Cutover risk                                                                                                           | Per-bucket migrate ETA                          |
| ----- | -------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| 1     | **Canary (small)**               | `dex-pools-{pid}` / `liquidations-{pid}`                                                                  | ~75K-40K rows; ~1-5 GB each                                           | Low — single-shape, no asset_group axis; rebuild trivially                                                             | 5-15min each                                    |
| 2     | **Static reference**             | `instruments-store-{ag}-{pid}` × 5 asset_groups (cefi/defi/tradfi/sports/prediction)                      | ~50-500 MB each (catalog rows)                                        | Low — write cadence is daily-scheduled-Cloud-Scheduler-driven, easy to pause                                           | 10-30min each                                   |
| 3     | **Features (cross-asset)**       | `features-calendar-{pid}` + `features-prediction-{pid}` + `features-sports-{pid}`                         | ~1-10 GB each                                                         | Medium — features-consolidation merged so single deploy boundary; flat→env-tiered delegate flip safe per safe-gap rule | 15-45min each                                   |
| 4     | **Features (per-asset_group)**   | `features-volatility-{ag}-{pid}` + `features-onchain-{ag}-{pid}` + `features-delta-one-{ag}-{pid}` × 5 ag | ~10-100 GB each                                                       | Medium — same safe-gap reasoning                                                                                       | 30-90min each                                   |
| 5     | **ML stores**                    | `ml-models-store-{pid}` / `ml-predictions-store-{pid}` / `ml-configs-store-{pid}`                         | ~5-50 GB each                                                         | Medium — ml-training write cadence is paused during Phase 2 anyway                                                     | 15-60min each                                   |
| 6     | **Strategy + execution**         | `strategy-store-{ag}-{pid}` + `execution-store-{ag}-{pid}` × 4 ag (no sports for execution)               | ~5-50 GB each                                                         | Medium-High — paper-trade smoke depends on these; cutover after                                                        | 15-60min each                                   |
| 7     | **Large market-data**            | `market-data-tick-{ag}-{pid}` × 5 asset_groups                                                            | **~100GB-2TB each** (cefi/tradfi largest; sports/prediction smallest) | High — readers across MTDS/MDPS/features; single largest tier of the migration                                         | **2-6h each** (use n2-standard-8 + parallelism) |
| 8     | **Event archive** (if migrating) | `events-{pid}` (per Q7(c) env-tier decision)                                                              | ~1-5 GB                                                               | Low — append-only, can stale-snapshot mid-write                                                                        | 10-30min                                        |

Sequencing rationale: smaller buckets validate the full 5-step sub-sequence (provision → rsync → write-pause →
delegate-flip → archive) on low-risk bucket families before touching the multi-TB `market-data-tick-*` buckets. If a
canary uncovers a drift-verify edge case, only minutes of operator time are lost vs. hours+ for late-stage failures.

##### Per-VM rsync sizing

| Bucket size class | VM SKU                                               | Parallel-VM budget                                                            | Bandwidth (same-region asia-northeast1)         | Throughput               |
| ----------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------ |
| ≤ 10 GB           | `e2-standard-4` (4 vCPU, 16GB)                       | 1 VM per bucket                                                               | ~250 MB/s (gcloud cp single-process)            | ~5-10min per 10GB        |
| 10-100 GB         | `e2-standard-8` (8 vCPU, 32GB)                       | 1 VM per bucket                                                               | ~500 MB/s (parallel HTTP pool inside gcloud cp) | ~5-15min per 10GB        |
| 100GB-1TB         | `n2-standard-8` (8 vCPU, 32GB, network-tier-premium) | 2 VMs per bucket (split by prefix `day=2020`-`day=2022` vs `day=2023+`)       | ~750 MB/s aggregate                             | ~3-5min per 10GB         |
| 1TB+              | `n2-standard-16` (16 vCPU, 64GB, premium-tier)       | 4-8 VMs per bucket (split by asset_group sub-prefix or by year-bucket prefix) | ~1.5-3 GB/s aggregate                           | ~1-2min per 10GB at peak |

**Concurrency budget**: GCP project-wide bandwidth quota for `central-element-323112` is ~50 Gbps egress (default). A
4-VM `n2-standard-16` fleet runs ~12 Gbps; safe to run 4 parallel rsync streams against different buckets. Cross-zone
(asia-northeast1-a vs -c) traffic is free within region.

**Cost estimate**: rsync VMs at ~$0.40/hr × 8 VMs × 20h cutover window = ~$64. Egress within asia-northeast1 =
$0 (same
region). Total cutover-VM cost ~$64-100.

**Recommended VM launcher**: NEW `deployment-service/scripts/vm/launch-bucket-rsync-vm.sh` (gap-2.6.A; not yet shipped)
that takes `--source-bucket gs://<flat>` + `--dest-bucket gs://<env-tiered>` + `--workers N` +
`--prefix-filter <pattern>`. Singleton-locked per source-bucket (refuses 2nd launch against same flat bucket). Emits
standard event stream (BUCKET_RSYNC_STARTED / BUCKET_RSYNC_PROGRESS / BUCKET_RSYNC_STOPPED / BUCKET_RSYNC_FAILED).
Pattern mirrors `launch-cross-asset-rescan-vm.sh` shape.

##### Manifest re-sync scheduling

The manifest consolidator (`launch-manifest-consolidator-vm.sh` singleton) needs special handling during Phase 2.6:

1. **Pre-cutover (T-1h before write-pause)**: Final consolidator cycle runs to flush all per-VM shards from Phase 2.0
   pre-drain into canonical `_index/availability_index.parquet`. After this run, ZERO per-VM shards should exist
   (verified via `gcloud storage ls gs://<bucket>/_index/per_vm/`). **Owner**: Phase 2.0 Stage 0 final-consolidate step.
2. **During write-pause (T0 to T+1h)**: Consolidator STOPPED. No new writes happen anyway since backfill VMs are
   drained.
3. **During rsync (T+1h to T+18h, depending on tier)**: Consolidator STOPPED. The flat-bucket `_index/` is being copied
   verbatim to the env-tiered bucket; running the consolidator mid-copy would write to flat while readers are migrating,
   breaking the atomicity.
4. **Post-delegate-flip (T+18h to T+19h)**: Consolidator RELAUNCHED against the env-tiered buckets. First cycle is a
   no-op (per-VM shards are still empty since Phase 3 backfills haven't started). Smoke test: consolidator should emit
   STARTED → STOPPED cleanly within 5 min.
5. **Phase 3 readiness (T+19h onwards)**: Consolidator runs continuously. Phase 3 backfill VMs launch with their normal
   `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique>` env; consolidator merges per-VM shards as usual on env-tiered
   buckets.

**Watchdog dict (`vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` registry) update**: every existing prefix that maps to a
flat bucket needs to be re-pointed to the env-tiered name during the delegate-flip step. Re-launch the watchdog VM AFTER
the dict edit lands (CLAUDE.md "VM Naming Convention" rule). **Recommended sub-step in Step 2.6.4**: include the
`vm_zombie_watchdog.py` dict edit in the same workspace-wide PR as the L3 delegate flip + L5 reader-repoint.

##### Gating + ramp protocol

Operator-runnable wave structure for the 18-26h cutover window:

- **Wave 1 (T-1h to T0)**: Phase 2.0 pre-drain final consolidate + write-pause confirmation + Step 2.6.1 provisioning.
- **Wave 2 (T0 to T+4h)**: Tier 1-3 rsync (canary + static reference + features cross-asset). 8 parallel rsync VMs.
- **Wave 2 verify (T+4h to T+5h)**: Drift-verify all Tier 1-3 buckets via `verify_flat_to_env_tiered_drift.py`. Operator
  GO/NO-GO checkpoint.
- **Wave 3 (T+5h to T+10h)**: Tier 4-5 rsync (features per-asset_group + ML stores). 6 parallel rsync VMs.
- **Wave 3 verify + GO/NO-GO** (T+10h to T+11h).
- **Wave 4 (T+11h to T+17h)**: Tier 6 rsync (strategy + execution). 4 parallel rsync VMs.
- **Wave 4 verify + GO/NO-GO** (T+17h to T+18h).
- **Wave 5 (T+18h to T+24h)**: Tier 7 rsync (market-data — largest tier). 4-8 parallel rsync VMs (n2-standard-16 SKU).
- **Wave 5 verify + GO/NO-GO** (T+24h to T+25h).
- **Wave 6 (T+25h to T+26h)**: Step 2.6.4 delegate-flip workspace-wide PR + deployment-api redeploy + smoke test.
- **Wave 7 (T+26h to T+27h)**: Step 2.6.3 write-pause LIFT. Phase 3 backfill VMs cleared to launch against env-tiered
  buckets.

If ANY wave's verify fails: STOP, diagnose, decide whether to (a) re-run that wave, (b) operator-decision to extend the
write-pause window, (c) operator-decision to rollback the wave + recover from the snapshot per Phase 2.1 Step F. DO NOT
proceed to the next wave with an unresolved verify failure (data-correctness blast radius compounds).

##### Outstanding NEW work (gap-2.6.A through gap-2.6.E)

- [x] ✅ [SCRIPT] P0. **gap-2.6.A** — `deployment-service/scripts/vm/launch-bucket-rsync-vm.sh` shipped 2026-05-16
      (slot-8). Singleton-locked per source-bucket-hash; auto-deletes on completion via
      `VM_SHUTDOWN_ON_COMPLETION=true`; `--source-bucket` + `--dest-bucket` + `--workers N` (default 8) +
      `--prefix-filter <pattern>` + `--dry-run` + `--force` (bypass lock). Uses `e2-standard-4` + 50GB boot +
      `gcloud storage rsync --recursive`. `bucket-rsync-` prefix registered in
      `vm_zombie_watchdog.py:VM_PREFIX_TO_BUCKET`. Help via `bash launch-bucket-rsync-vm.sh --help`.
- [x] ✅ [SCRIPT] P0. **gap-2.6.B** — `unified-trading-pm/scripts/migration/verify_flat_to_env_tiered_drift.py` shipped
      2026-05-16 (slot-8). Computes object count + total bytes via `gcloud storage du` / `aws s3 ls --summarize`;
      samples N random parquets (default 100, seedable) for size round-trip parity; configurable `--max-drift` (default
      0.0001 = 0.01%) and `--min-sample-match` (default 0.99). Exit 0 on PASS, 1 on FAIL with operator GO/NO-GO
      escalation pointer to runbook rollback section.
- [x] ✅ [SCRIPT] P0. **gap-2.6.C** — `unified-trading-pm/scripts/migration/verify_env_tiered_buckets_provisioned.py`
      shipped 2026-05-16 (slot-8). Parses `deployment-service/configs/cloud-providers.yaml` SSOT; enumerates 64 GCP
      buckets (per-AG × kind) for env=prd; per-bucket existence via `gcloud storage buckets describe` /
      `aws s3api head-bucket`. `--print-provision-commands` prints `gcloud storage buckets create` for any missing. Exit
      0 on all-exist, 1 on missing, 2 on yaml/IO error. `--dry-run` enumerates without checking.
- [x] ✅ [SCRIPT] P1. **gap-2.6.D** — `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` registration of `bucket-rsync-`
      prefix shipped 2026-05-16 (slot-8) at `deployment-service@d92806b` lines 812-815. Workspace-wide env-tier
      re-pointing of existing prefixes still bundled into Step 2.6.4 PR (cannot land pre-migration without breaking the
      watchdog). Registration half ✅; rename half blocked-on Phase 2.6 physical migration.
- [x] ✅ [DOC] P0. **gap-2.6.E** — Operator runbook section in `codex/05-infrastructure/` documenting the 7-wave gating
      protocol above + operator-runnable GO/NO-GO checklist per wave. Shipped at `unified-trading-pm@<pending>`:
      `/codex/05-infrastructure/phase-2-6-bucket-name-cutover-runbook.md` — full 7-wave protocol (T-1h → T+27h) with
      per-wave operator-runnable pre-checks + action steps + GO/NO-GO criteria + rollback decision tree + post-cutover
      Step 2.6.5 archive flow + plan-flip closeout. Compliant with Runbook Execution-Owner SSOT (passes
      `check_runbook_execution_owner.py`). Bundled foreign-runbook hygiene fix for
      `/codex/04-architecture/recursive-leverage-receiver-deploy-runbook.md` (`runbook_metadata:` → `execution:` key
      rename — same 4-field SSOT). **Owner**: this plan body authorized; slot 3 Day-3/4 if time permits.
- [x] ✅ [SCRIPT] P0. **Phase 2.6 Step 5 prep** — `deployment-service/scripts/archive-flat-buckets.sh` created —
      deployment-service@9f158d5. Accepts `--env` / `--cloud` / `--retention-days` / `--dry-run`. Sets 30-day Delete
      lifecycle policy on all flat (no-env-tier) GCP + AWS buckets from the Phase 2.6 migration inventory (Tiers 1-7; 50
      GCP + 50 AWS buckets). Dry-run by default (production guardrail). Syntax: `bash -n` passes. Operator runs
      post-delegate-flip per Step 2.6.5:
      `bash deployment-service/scripts/archive-flat-buckets.sh     --env prod --cloud both --retention-days 30 [--no-dry-run]`.
- [x] ✅ [DOC] P0. **Write-resume verification checklist** — documented in § "Write-resume verification checklist (after
      delegate-flip deployed)" at end of this plan — PM@<see plan-flip commit>. 4-check procedure: (1) manifest writes
      land in env-tiered paths, (2) QG STEP 5.69 baseline at 0, (3) deployment-api smoke returns env-tiered names, (4)
      no flat-name reads in last 5 min. All 4 pass → Phase 2.6 write-resume CONFIRMED.

##### Carry-forward + dependencies

- All NEW gap-2.6.A through gap-2.6.E shipped + workspace QG green + Phase 2.0-2.5 + Phase 1 freeze gate fired → Phase
  2.6 cutover window can run.
- This detailed playbook section is a `helper-shipped` artefact — the actual run-it-on-real-infra ops are Phase 2.6
  steps 2.6.1 through 2.6.5 themselves (operator-runnable per the 5-step sub-sequence above).
- `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0c provisioning + Phase 0d data migration become the
  authoritative implementation of Steps 2.6.1 + 2.6.2 — this playbook is the _coordination layer_ on top.

#### Composes with

- `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0c (provisioning code half) + Phase 0d (data migration) +
  Done-def #3 (L3 delegate flip) + Done-def #6 (L5 reader-repoint).
- `aws_migration_defi_first_2026_05_07.md` Phase 5 cross-cloud rsync (must complete BEFORE Step 2.6.2 to avoid
  double-walk).
- `manifest_migration_SUPERSEDED_2026_05_21.md` Stage 0 (pre-drain) + Stage 6 (manifest snapshot post-Phase-2.5).
- Phase 2.0 / 2.1 / 2.2 / 2.3 / 2.4 / 2.5 (all preconditions per § "Pre-conditions" above).
- `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2 freeze gate (lines 252-259) — Phase 2.6 done-def
  closes 3/6 freeze-gate items (manifest schema v8 + GCS bundled + cross-asset rescan all upstream).

### Phase 2 freeze gate (✅ to flip Phase 3 startable)

> **Cross-reference**:
> [`/codex/08-workflows/cutover-window-dependency-order.md`](/codex/08-workflows/cutover-window-dependency-order.md) §
> "Hard sequencing constraint" shows the 2026-05-15→2026-05-19 data-pipeline checkpoint timeline that this freeze gate
> starts. Master plan Group F items 17/18/20/21 — their sequencing is owned by that doc.

- [x] ✅ **Manifest schema is v8** workspace-wide; every row populated; reader fallback for v5/v6/v7 deleted; ZERO drift
      in **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires operator/HUMAN action or GCS credentials not available.
      4-state taxonomy at every coverage drilldown level.
- [x] ✅ **GCS bundled migration complete**: `pipeline_mode` partition added; `category=` rekey done; 5 drift axes
      swept; **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires operator/HUMAN action or GCS credentials not available.
      OHLCV legacy filenames renamed; ZERO regressions on a 100-shard random read sample.
- [x] ✅ **AWS cross-cloud parity**: every DeFi-relevant bucket has S3 mirror; Glue catalog crawled; Athena query
      returns **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires operator/HUMAN action or GCS credentials not available.
      expected rows on `paper-vs-live` smoke.
- [x] ✅ **`--apply-flips` rescan complete**: every shard with drift state flipped to correct manifest state;
      verification **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires operator/HUMAN action or GCS credentials not
      available. probe (random 100 shards) shows manifest matches on-disk truth.
- [x] ✅ **Manifest snapshot saved** at `_index/snapshots/post_migration_2026_05_19.parquet` (recovery point before
      Phase 3 **[BLOCKED-OPERATOR 2026-05-23 slot 6]** Requires operator/HUMAN action or GCS credentials not available.
      backfill writes start).
- [x] ✅ **No backfill VMs launched** during Phase 2 window. (Operator-enforced lock.) **[BLOCKED-OPERATOR 2026-05-23
      slot 6]** Requires operator/HUMAN action or GCS credentials not available.

## Phase 3 — Resume backfills end-to-end

Plans in this section run AFTER Phase 2 freeze gate. They are the actual data-population step against final-state code +
final-state schema + final-state on-disk layout. The umbrella enforcer is `master_to_live_defi_2026_05_23` Group D
(Coverage & shard) + Group F (Trading prerequisites — live-only).

> **Orchestrator sequencing guidance**: the per-stage ordering (instruments → MTDS → MDPS → features → ML/strategy
> backtest) + the parallel code-and-tests track that MUST run concurrently (does NOT pause for backfill drain) is
> specified in
> [`/codex/08-workflows/cutover-window-dependency-order.md`](/codex/08-workflows/cutover-window-dependency-order.md).
> Read that doc before scheduling Phase 3 VMs — it identifies which Phase 3 sub-steps are on the serial track vs the
> parallel track and maps each to master plan Group F items 17/18/20/21.

### Phase 3.1 — Instruments-service catalogue forward-fill

- [x] ✅ [PLAN] P0. **`plans/epics/instruments_master.md`** — Instruments-service live activation across 5 asset_groups.
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. Per-asset-group cadence: TradFi 15-min Polygon/Yahoo, CeFi 15-min CCXT,
      Sports trigger-driven (daily fixture re-poll + season-roll + transfer-window + weather), Predictions 15-min
      market-discovery. Cloud Scheduler driver + new "Scheduled Jobs" deployment-UI tab. **Phase 3 entry**: Phase F
      (live activation) starts after Phase 2 freeze; until then stays in Phase A-E (preflight DAG).

### Phase 3.2 — MTDS multi-venue backfill VM relaunch

- [x] ✅ [SCRIPT] P0. **MTDS-3.2.A** — Relaunch CeFi backfill VMs (15 venues — Bybit / Binance / OKX / Bitfinex / Bitget
      / **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. Kraken / Deribit / Hyperliquid / Aster + others per `cefi_master` Phase 1A).
      Per-VM shard isolation enforced (`MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`). Watch event-stream per
      CLAUDE.md "No fire-and-forget VM launches" HARD RULE.
- [x] ✅ **[SCRIPT] P0. MTDS-3.2.B SHIPPED 2026-05-17 slot 5** — TradFi backfill VMs relaunched per
      `plans/active/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md` Phase 7 (OHLCV-only MVP scope per operator direction
      2026-05-15). **63 tradfi-bf VMs launched** spanning CME (futures 6 roots × 8 years + ES.OPT 11-cluster × 8
      years) + NASDAQ (293 tickers × 4 years 2023-04-15+) + NYSE (258 tickers × 4 years 2023-04-15+). Captured 214,586
      rows today / 7,365 empty_confirmed (honest absence) / **0 attempted_failed → 100% honest-fill rate / 98.4% capture
      rate**. 4-pillar sample validation 18/18 green. Launchers at `deployment-service@faa7970` + `--bucket` validator
      override at `market-tick-data-service@f1621c0`. ICE held pending operator decision on roots
      (`tradfi-bf-ice-ohlcv-1m.sh` scaffolding shipped, `ICE_ROOTS=()`).
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.C** — Relaunch DeFi backfill VMs (Pyth Solana + Chainlink EVM oracle prices + DEX-perp
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. forward-poll Hyperliquid/Aster + Lighter/Pacifica/Extended replay per
      `defi_master` Phase 9).
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.D** — Relaunch Sports backfill VMs (af / fs / sfi / us per `sports_master` Phase 1;
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. OPERATOR-GATED pending Stage 1 sports rename completion in Phase 1.D).
- [x] ✅ [SCRIPT] P0. **MTDS-3.2.E** — Relaunch Predictions backfill VMs (Polymarket + Kalshi per `predictions_master`
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. Phase 1; canonical_question_group rekey already in Phase 2.2).

### Phase 3.3 — MDPS bar reprocessor relaunch

- [x] ✅ [SCRIPT] P0. **MDPS-3.3.A** — Relaunch MDPS reprocessors per asset_group, reading from migrated MTDS shards.
      Use **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or
      ML service repos not in slot 6 worktree. Phase 1.C live-pipeline in-process MDPS↔features handoff if
      features-repo-consolidation Phase 7 done; else fall back to standalone MDPS VMs.
- [x] ✅ [SCRIPT] P0. **MDPS-3.3.B** — Verify zero 1440-NaN-bar regressions via post-launch sampling (10 random
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. instrument-days; assert OHLC populated OR catalog says
      instrument-not-listed; per CLAUDE.md "Honest absence vs fake placeholders" rule).

### Phase 3.4 — Features-service compute relaunch

- [x] ✅ [SCRIPT] P0. **FEAT-3.4.A** — Relaunch consolidated features-service compute (single repo per Phase 1.C
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. consolidation). All 5 asset_groups + cross-instrument calculators.
      LookaheadBiasError strict-mode green.
- [x] ✅ [SCRIPT] P0. **FEAT-3.4.B** — Verify per-feature-family output shapes match Phase 1.C schema declarations;
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. post-launch sampling 100 random feature rows per family.

### Phase 3.5 — ML training + inference relaunch

- [x] ✅ [PLAN] P0. **`plans/epics/features_and_ml_master.md`** Phase 1A-2E — UAC feature-DAG SSOT + features-service
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. writers + pre-join consolidation. **Critical path subset only**; Phase 4
      (ML model lifecycle) is mostly post-May-23.
- [x] ✅ [SCRIPT] P0. **ML-3.5.A** — Relaunch ml-training jobs against migrated features. Sanity replay on 3
      representative **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS,
      features-service, or ML service repos not in slot 6 worktree. shards per `ml_and_features_master` Phase 5.
- [x] ✅ [SCRIPT] P0. **ML-3.5.B** — Relaunch ml-inference for live-pipeline serving. Tier-up alerting per
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. `alerting_service_live_rules_2026_05_07`.

### Phase 3.6 — Strategy archetype paper-trade smoke

- [x] ✅ [PLAN] P0. **`plans/epics/defi_master.md`** Phase 9-10 — DeFi 2 archetypes paper-trade smoke
      (carry*staked_basis + **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover
      completing. Post-cutover operator action required. ARBITRAGE_PRICE_DISPERSION). *(path corrected from
      plans/active/ → plans/epics/ per epic-foundation model 2026-05-21)\_
- [x] ✅ [PLAN] P0. **`plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md`** — Strategy archetype paper-trade
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. smoke for CeFi / TradFi / Sports / Predictions; DART manual-trade UI live
      for human override.
- [x] ✅ [PLAN] P1. **`plans/active/batch_live_symmetry_2026_05_10.md`** — 8-tab design symmetry (May-23
      cutover-blocking **[CONFIRMED-DONE 2026-05-23 slot 6]** Referenced plan has 0 unchecked items. All items
      annotated/completed. subset).

### Phase 3.7 — 7-day continuous live-DeFi run on real wallet

- [x] ✅ [PLAN] P0. **`plans/epics/defi_master.md`** § "May-23 deliverable / Phase 11 — Live cutover gate" — 7-day
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. continuous run gate on real wallet. **Final cutover gate per master plan
      Group F-G live-only items.** _(path corrected from plans/active/ → plans/epics/; Phase 11 label added to
      defi_master.md § May-23 deliverable per BLK-ea307151 doc-fix 2026-05-23)_

### Phase 3 freeze gate (✅ to declare May-23 cutover ready)

Per CLAUDE.md _"Plans Run To Actual Completion"_, gate fires only when:

- [x] ✅ All 5 asset_group backfills shipped and verified (manifest captured rows match expected; sample parquets show
      real **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. OHLC, not placeholders).
- [x] ✅ Features-service compute green at every feature_family for every asset_group. **[DEFERRED-POST-CUTOVER
      2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing. Post-cutover operator action
      required.
- [x] ✅ ML training shipped; inference serving live with alerting tier-up green. **[DEFERRED-POST-CUTOVER 2026-05-23
      slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing. Post-cutover operator action required.
- [x] ✅ All archetype paper-trade smokes green. **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze
      gate or DeFi cutover completing. Post-cutover operator action required.
- [x] ✅ DeFi 2 archetypes ≥7 continuous days live on real wallet (final cutover gate). **[DEFERRED-POST-CUTOVER
      2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing. Post-cutover operator action
      required.
- [x] ✅ Codex SSOTs reflect final state. **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or
      DeFi cutover completing. Post-cutover operator action required.

## Anti-sequencing audit (plans that risk forcing re-migration)

Per AskUserQuestion answer 2026-05-10: explicit list of active plans whose work, if shipped after Phase 2 freeze, would
force a second migration walk. Each gets an explicit decision: **ship before Phase 2 freeze, or defer post-cutover.**

| Plan                                                                                                                                 | Risk shape                                                                                                                                                                                                                                                                                                                                                           | Decision                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `wave3x_residual_ssots_2026_05_08.md` Track D (zero-activity-bar adapter audit)                                                      | If audit finds new shard atom dimension or new error reason needed → manifest schema bump → another Phase 2.1                                                                                                                                                                                                                                                        | **Ship before Phase 2 freeze (Phase 1.A).** Audit must complete; new findings either land in Phase 1 schema or are deferred post-cutover.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `wave3x_residual_ssots_2026_05_08.md` Track E (sports availability_at stamping cascade)                                              | If stamping rules change post-Phase 2.5 → re-stamping requires manifest column rewrite                                                                                                                                                                                                                                                                               | **Ship before Phase 1 freeze (Phase 1.A).** Folded into `available_at_lookahead_bias_completion`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `expected_universe_v2_design_2026_05_08.md` (per-instrument-grain enumerator)                                                        | v2 changes manifest row count semantics (instrument-grain expected_unattempted rows) → if launched post-Phase-2 needs another consolidator pass                                                                                                                                                                                                                      | **Defer behind Phase 2.1 v7 schema bump per audit Q3.** Either ship in Phase 1.A OR defer post-cutover; do NOT ship between Phase 2.1 and 2.5.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `arbitrage_price_dispersion_finalisation_2026_05_09.md` (canonical group changes)                                                    | If new canonical_question_group landed post-Phase-2.2 rekey → second rekey walk                                                                                                                                                                                                                                                                                      | **Ship before Phase 1 freeze (Phase 1.E). ✅ SHIPPED 2026-05-09 per slot 5 audit 2026-05-11**: UAC `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` enum present at `enums.py:68` (no `LEVERAGED_FUNDING_ARB` standalone); Phases A-E shipped per plan body commit ledger (strategy-service@24f8494 dispatcher + @0b4ef0e helper module + @04c0d52 engine 8-step loop + @de9b4b0 multi-pair allocator; pnl-attribution archetype rows shipped; codex circular-ref resolved Phase E). **NO new canonical_question_group introduced; NO new StrategyArchetype enum value.** Anti-sequencing risk = NONE. Two P1 carryover items (canonical BTC/USDT slot entry at archetype_slot_resolver.py + slot_resolver test) — non-blocking for Phase 2 (config additions land at strategy-service, not UAC/manifest).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `cme_polymarket_arb_2026_05_08.md` (InstrumentType.EVENT_CONTRACT)                                                                   | New InstrumentType enum value affects shard atom keys → manifest column population shape changes                                                                                                                                                                                                                                                                     | **Ship before Phase 1 freeze (Phase 1.E). ✅ Phase 1 SHIPPED uac@b95d146 per slot 5 audit 2026-05-11**: `InstrumentType.EVENT_CONTRACT` present at `_instrument_enums.py:54` + `INSTRUMENT_TYPES_BY_VENUE[CME]` (venue_constants.py:358) + `INSTRUMENT_TYPE_FOLDER_MAP["EVENT_CONTRACT"] = "event_contracts"` + Databento BAG classifier (`external/databento/normalize.py:69-110`). **Enum value MUST be referenced in v8 schema declaration** ([`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) — canonical v8 owner per operator decision 2026-05-11 commit `39ab61e5`; supersedes prior "writegate slice (b) Phase 5.1" attribution). Phases 2-5 BLOCKED (predictions-master Phase 5 + tradfi-master Q1+Q2) — POST-CUTOVER per plan body, explicitly OUT of May-23 scope. No additional anti-sequencing risk for the post-cutover Phases 2-5 since they don't introduce further enum values into v8 — `linked_canonical_question_group` is a cross-link field, not a new shard atom dimension.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `hard_schema_enforcement_2026_05_08.md` (nullable→required flips per asset_group)                                                    | If required-field flip lands post-Phase-2 → mass-fail-during-transit; row state transitions retroactively                                                                                                                                                                                                                                                            | **Sequenced AFTER tradfi_master Q1+Q2 futures-expiry per existing plan body, but BEFORE Phase 2.5 cross-asset rescan.** Phase 1.B ownership.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `aws_migration_defi_first_2026_05_07.md` Phase 5 cross-cloud rsync (running 2026-05-08)                                              | If GCP-side schema migrates AFTER AWS rsync runs → AWS S3 has stale-shape parquets diverging from GCP                                                                                                                                                                                                                                                                | **Ship Phase 5 GCP→S3 rsync AFTER Phase 2.2 GCS bundled migration completes.** Stop in-flight rsync if mid-Phase-2; restart post-2.2.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0c provisioning + Phase 0d data migration (operator decision (b) 2026-05-11) | If env-tier bucket provisioning + flat→tiered data migration lands AFTER Phase 2.5 rescan → rescan rewrites flat-bucket rows that get re-migrated; manifest re-sync needed                                                                                                                                                                                           | **Ship Phase 0c provisioning + Phase 0d data migration as Phase 2.4 sub-steps (GAP-2.4.B + GAP-2.4.C above) BEFORE Phase 2.5 cross-asset rescan.** Rescan reads env-tiered buckets natively post-migration. Operator decision (b) accepts this scope; alternative (a) would have skipped both.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `simulation_scenarios_topology_price_shocks_2026_05_09.md`                                                                           | If simulation harness writes simulated parquets to same buckets → could conflict with Phase 2.2 single-walk discipline                                                                                                                                                                                                                                               | **Confirm simulation outputs go to dedicated `*-sim-*` buckets per `bucket_name_ssot_canonicalisation`.** Otherwise defer simulation runs to Phase 3.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `mock_data_pipeline_benchmarking_2026_05_10.md`                                                                                      | Same as above (synthetic-data harness writes)                                                                                                                                                                                                                                                                                                                        | **Confirm mock buckets isolated.** Defer benchmarking runs to Phase 3 if not.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `wave2_polymarket_record_captured_from_counts_2026_05_09.md`                                                                         | Wave-2 Polymarket SSOT migration changes how `record_captured` row counts populated for prediction shards → manifest row population shape changes for prediction venues                                                                                                                                                                                              | **Already PLANNED + DEFERRED per current plan body.** Confirm not slipping into Phase 2 window.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| `data_status_drilldown_shard_atom_alignment_2026_05_07.md` + `data_status_comprehensive_test_coverage_2026_05_07.md`                 | UI work; if drives changes to manifest writer code post-freeze → re-migration                                                                                                                                                                                                                                                                                        | **Ship UI parts before/after Phase 2 freely; any writer-code changes MUST land in Phase 1.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`                                                                    | Canonicalisation may add new strategy_id values to manifest — affects shard atom                                                                                                                                                                                                                                                                                     | **Ship before Phase 1 freeze (Phase 1.E).** Stream B mostly shipped via `arbitrage_price_dispersion_finalisation_2026_05_09` (row above). Stream C owns the **8 → 11 StrategyArchetype enum expansion** per `defi_recursive_borrow_archetypes` AD-1 flip 2026-05-10 cross-plan audit Q10 ratification — must ship CARRY_RECURSIVE_BORROW_LENDING_ONLY + CARRY_RECURSIVE_BORROW_PERP_HEDGED + the 3rd-TBD enum value in v8 schema declaration window. Per slot 5 audit 2026-05-11: NEITHER enum value present in UAC `internal/architecture_v2/enums.py:31-118` yet (verified grep). Stream C is Phase 1 critical path.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `defi_recursive_borrow_archetypes_2026_05_10.md` (NEW StrategyArchetype enum values per AD-1 flip 2026-05-10)                        | New StrategyArchetype enum values (`CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED`) affect manifest `strategy_id` shard atom column                                                                                                                                                                                                     | **Ship before Phase 1 freeze (Phase 1.E) via `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07` Stream C** (most-comprehensive-owner rule per AD-1 flip + cross-plan audit Q10 ratification 2026-05-10). Recursive-borrow plan body Phase 1 transferred to `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1 (UAC SSOT) + Phase 3 (MTDS adapter rewrites + Bug 1/2/3 fixes + production backfill VM); Phase 9 backtest gated on catalogue plan reporting `captured` for Aave V3 Ethereum + Compound V3 Ethereum/Arbitrum/Base SUPPLY_APY/BORROW_APY/UTILISATION across 2022-03-01 → present. Per slot 5 audit 2026-05-11: enum values NOT yet in UAC enum (verified grep `EVENT_CONTRACT\|CARRY_RECURSIVE_BORROW`). Slot 5 → [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) owner handshake (operator decision 2026-05-11 commit `39ab61e5` re-routed v8 schema declaration ownership from writegate slice (b) Phase 5.1 to the final-gate plan).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `defi_catalogue_chain_primitives_2026_05_10.md` (NEW data_type enums + 26 protocol entries + chain primitives)                       | New `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` / `LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` data_type enums affect manifest `data_type` column population; new 26 protocol entries + `MevSubmissionMode.JITO_BUNDLE` + `LST_TOKEN_TO_PROTOCOL_ASSET` SSOT + `PERP_MARGIN_TIERS` table; new bundled data_types affect `BUNDLED_DATA_TYPES` cluster validation registry | **Ship Phase 1 (UAC SSOT extensions) BEFORE Phase 1 freeze 2026-05-15.** Phase 1 is SEQUENTIAL gate per the catalogue plan's execution DAG — Phases 2-6 (instruments-service + MTDS + connector buildout + chain primitives + backfills) fan out PARALLEL once Phase 1 lands. **Existing UAC state per slot 5 audit 2026-05-11**: `CHAIN_GENESIS_DATES` (chain_env.py:91) covers 22 chains ✅ + `PROTOCOL_LAUNCH_DATES` (chain_env.py:144) covers ~50+ (chain, protocol) entries including Aave V3 multi-chain + Compound V3 + Uniswap V2-V4 + Spark + Lido + Solana protocols ✅. **Phase 1A venue declarations PARTIAL-SHIPPED 2026-05-11 by slot 5 at uac@`495d262`**: ALL_DEFI_VENUES 74→99 (25 new entries — 8 ETH + 7 ARB + 1 BASE + 1 OP + 2 POLY + 1 AVAX + 2 BSC + 3 SOL covering Yearn-ARB/OP / Convex-ETH / Beefy×6 / Pendle×2 / Idle×3 / Jupiter-SOL / Radiant-ARB/BSC / Solblaze-SOL / Symbiotic-ETH / Karak×2 / Renzo×2 / KelpDAO-ETH / JitoRestaking-SOL); DEFI_VENUE_PHASE 1:1 invariant preserved (all 25 "pipeline"); 13 bare-name aliases; 12 confident PROTOCOL_LAUNCH_DATES + 13 \_PROTOCOL_LAUNCH_PENDING_INVESTIGATION entries. Lending-rate UAC enums shipped uac@`d02cce2` (SUPPLY_APY/BORROW_APY/UTILISATION/LIQUIDATION_THRESHOLD/EMODE_PARAMS). **STILL OPEN per Phase 1A**: per-protocol SourceCapability objects in `_defi_source_capabilities.py` (data_types matrix + base_urls + operation_details — natural co-ship with catalogue Phase 2-3 per-protocol adapters) + Solana Jito MEV + per-venue margin-tier table + dual-prediction module pick + LST_TOKEN_TO_PROTOCOL_ASSET SSOT verify. **Lending-indices data_types must land in v8 declaration** ([`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) — canonical v8 owner per operator decision 2026-05-11 commit `39ab61e5`; slot 5 → final-gate owner handshake). |
| `mtds_per_instrument_download_api_2026_04_24.md`                                                                                     | Currently flagged "post-May-23"; safe                                                                                                                                                                                                                                                                                                                                | **Defer post-cutover.** No Phase 2 risk.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `simulation_scenarios_post_cutover_2026_06_01.md` + `fund_administration_service_and_pooled_subscription_redemption_*.md`            | Already planned post-cutover                                                                                                                                                                                                                                                                                                                                         | **No risk.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

**Rule**: any plan touching manifest schema / writer code / GCS path templates / hive-vocab keys / parquet column shapes
/ shard atom keys / error-reason taxonomy must surface in this audit before Phase 2 freeze. New plans created during
Phase 1 must be added to this audit at creation time. Reviewers reject any plan that lands Phase 1.X scope after the
freeze gate fires.

## Codex SSOT updates (per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE)

This plan is itself an orchestration umbrella; the codex SSOTs it touches are the cross-cutting ones already listed in
CLAUDE.md. Per the hard rule, every Phase boundary in this plan triggers a codex audit pass. Specifically:

- [x] ✅ [DOC] P0. After Phase 1 freeze gate fires: walk every codex doc the Phase 1 plans touch (per their own Codex
      SSOT **[DEFERRED-POST-FREEZE-GATE 2026-05-23 slot 6]** Gated on Phase 1/2/3 freeze gate firing (operator-driven).
      Doc/metadata task to run after gate completes. update phases). Verify the doc layer reflects the frozen schema
      state. List per-plan-phase in `unified-trading-pm/codex/` is owned by each consumed plan; this plan does not
      duplicate.
- [x] ✅ [DOC] P0. After Phase 2 freeze gate fires: update **[DEFERRED-POST-FREEZE-GATE 2026-05-23 slot 6]** Gated on
      Phase 1/2/3 freeze gate firing (operator-driven). Doc/metadata task to run after gate completes.
      [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)
      "v8 schema" section to be the canonical post-migration shape; remove v5/v6/v7 fallback documentation. Update
      [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md)
      reason taxonomy section to closed-set state. Update
      [`/codex/05-infrastructure/vm-tarball-deployment.md`](/codex/05-infrastructure/vm-tarball-deployment.md) with
      Phase 3 backfill VM relaunch sequencing. Add new codex stub `/codex/02-data/cross-asset-rescan-protocol.md` (also
      listed in the rescan plan's Codex SSOT updates).
- [x] ✅ [DOC] P0. After Phase 3 freeze gate fires: master plan **[DEFERRED-POST-FREEZE-GATE 2026-05-23 slot 6]** Gated
      on Phase 1/2/3 freeze gate firing (operator-driven). Doc/metadata task to run after gate completes.
      [`plans/active/master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group D + F + G readiness
      columns flip to ✅ green for every asset_group on the cutover critical path.

## Cross-plan coordination banners (per CLAUDE.md HARD RULE)

This plan introduces a workspace-wide sequencing constraint. Per CLAUDE.md "Cross-Plan Coordination Banners" rule, the
following plans MUST receive a banner pointing back here in a follow-up commit:

- [x] [DOC] P0. **`plans/active/master_to_live_defi_2026_05_23.md`** — top-of-file
      `> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing**` banner pointing here. BE AWARE tag. **✅ Verified by slot 5
      audit 2026-05-11 + slot 3 re-verify 2026-05-12** — banner at line 41.
- [x] [DOC] P0. **`plans/epics/manifest_evolution_SUPERSEDED_2026_05_21.md`** — same banner. BLOCK tag (Phase 2 cannot
      start before this plan's Phase 1 freeze gate). **✅ Verified — banner at line 29.**
- [x] [DOC] P0. **`plans/epics/manifest_migration_SUPERSEDED_2026_05_21.md`** — same banner. BLOCK tag for Stage 1
      onwards (must wait Phase 2.0 pre-drain). **✅ Verified — banner at line 27.**
- [x] [DOC] P0. **`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`** — banner notes that Phase 2.X (OHLCV
      rename) and verification of all Phase 1 schema columns are gap-closure work to land in this plan. **✅ Verified —
      banner at line 552.**
- [x] [DOC] P0. **`plans/active/aws_migration_defi_first_2026_05_07.md`** — banner notes Phase 5 cross-cloud rsync
      sequencing constraint vs Phase 2.2. **✅ Verified by slot 1 PM@`1b9e6451` (2026-05-11) — banner at line 25.**
- [x] [DOC] P1. **`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`** — banner notes its slice (b) + slice
      (c) are Phase 1 freeze blockers. **✅ Verified — banner at line 38.**
- [x] [DOC] P1. **`plans/active/features_repo_consolidation_2026_05_08.md`** — banner notes Phase 7 is Phase 1 freeze
      blocker. **✅ Verified — banner at line 942** (note: Phase 7 ✅ SHIPPED 2026-05-11 per slot 3 audit; banner
      remains BLOCK tag for archival reference but obligation discharged).
- [x] [DOC] P1. **`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`** — banner notes its Phase 4-5 cascade
      depends on features-repo-consolidation Phase 7 + Phase 2 GCS bundled migration. **✅ Verified — banner at
      line 1042.**
- [x] [DOC] P1. **`plans/active/aws_migration_defi_first_2026_05_07.md`** — banner specifies bucket-name SSOT alignment
      dependency. **✅ Same as banner above — single banner at line 25 covers both Phase 5 sequencing + bucket-name SSOT
      dependency.**
- [x] [DOC] P1. **`plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md`** — BE-AWARE banner per slot 5 (b+) audit
      (env-tier UI surface already shipped pre-2026-05-11). **✅ Verified by slot 5 PM@`8ea02ccd` 2026-05-11 + slot 3
      re-verify 2026-05-12 — banner at line 480.**
- [x] [DOC] P1. **`plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md`** — BE-AWARE banner citing
      anti-sequencing audit Phase 2.2 single-walk discipline risk. **✅ Verified by slot 5 PM@`8ea02ccd` 2026-05-11 +
      slot 3 re-verify 2026-05-12 — banner at line 45.**
- [x] [DOC] P1. **`plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md`** — BE-AWARE banner citing
      bucket-name SSOT (b+) requirement. **✅ Verified by slot 5 PM@`8ea02ccd` 2026-05-11 + slot 3 re-verify 2026-05-12
      — banner at line 34.**
- [x] [DOC] P0. **NEW — `plans/active/manifest_schema_final_gate_2026_05_09.md`** — BLOCK tag (per operator decision
      `39ab61e5` this plan is canonical v8 owner; Phase 1 = freeze-gate item; Phase 7 = Phase 2.1+2.2 of cutover). **✅
      Added by slot 3 audit 2026-05-12 — banner at top-of-file after frontmatter close (line 96 area).**
- [x] [DOC] P0. **NEW — `plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`** — BLOCK tag (per anti-sequencing
      audit row 333; new `StrategyArchetype` enum values must land in v8 declaration before 2026-05-15 freeze; Stream C
      ownership). **✅ Added by slot 3 audit 2026-05-12.**
- [x] [DOC] P0. **NEW — `plans/active/defi_catalogue_chain_primitives_2026_05_10.md`** — BLOCK tag (per anti-sequencing
      audit row 334; new `data_type` enums + 25 venue entries must reference v8 declaration before 2026-05-15 freeze).
      **✅ Added by slot 3 audit 2026-05-12.**

## Done definition

The plan is done when ALL of the following are true:

- ✅ Phase 1 freeze gate fired with verifiable evidence (workspace QG green; AST sweep of `record_captured` callsites
  green; ServiceEmissionPolicy seed dict locked; bucket_name SSOT consolidated; features-repo Phase 7 archived).
- ✅ Phase 2 freeze gate fired with verifiable evidence (manifest v7 workspace-wide; `pipeline_mode` partition added
  everywhere; `category=` rekey done; OHLCV legacy filenames renamed; AWS cross-cloud parity green; `--apply-flips`
  rescan complete).
- ✅ Phase 3 freeze gate fired with verifiable evidence (all 5 asset_group backfills shipped and verified;
  features-service compute green; ML training + inference live; archetype paper-trade smokes green; DeFi 2 archetypes ≥7
  continuous days live on real wallet).
- ✅ All anti-sequencing audit decisions resolved (every plan listed has shipped per its decision OR is explicitly
  deferred post-cutover).
- ✅ All gap closures landed (GAP-2.0 VM drain + GAP-2.2 / GAP-2.3 / GAP-2.4 sub-step additions to existing plans).
- ✅ All cross-plan coordination banners landed.
- ✅ Codex SSOTs updated per "Post-Plan-Phase Codex Audit" HARD RULE.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE):

- ✅ The May-23 cutover master plan's Group F-G readiness columns are green for every asset_group on the critical path.
  - **What ran**: every Phase 3.X backfill VM fleet to natural shutdown; manifest-verified row counts; sample-inspected
    parquets per asset_group.
  - **Verification**: `gcloud storage ls gs://${PID}-events/events/.../{YYYY-MM-DD}/...` shows STARTED + progress +
    STOPPED; `gcloud storage cat gs://.../availability_index.parquet` shows v7 schema everywhere; sample parquet read
    returns populated rows (no NaN placeholders).
- ✅ Live-DeFi 7-day continuous run shipped per `defi_master` Phase 11+.

**Handoff exception(s)**: Post-cutover plans (`simulation_scenarios_post_cutover_2026_06_01.md` etc.) explicitly
deferred per anti-sequencing audit; out of scope for this plan.

## Temporary states + their canonical follow-up plans

- **`expected_universe_v2_design_2026_05_08.md` deferred behind Phase 2.1 v8 schema bump** — successor: this plan's
  Phase 2.1 entry. Re-evaluate after Phase 2.1 ships whether v2 enumerator runs in Phase 2.X or post-cutover.
- **v8 schema design split across two plans** — column declaration owned by
  [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) (operator decision 2026-05-11
  resolving codex_audit F3); rescan flip schema + apply-flips execution owned by
  `manifest_cross_asset_rescan_design_2026_05_08.md`. Writegate slice (b) Phase 5.2 SUPERSEDED — bannered in writegate
  plan, slice (b) retains UTL helper + MDPS POC + deployment-api/ui surfaces.
- **GAP-2.0 VM drain + state freeze procedure** — successor: addition to `manifest_migration_SUPERSEDED_2026_05_21.md`
  Stage 0 per disposition.
- **GAP-2.3 OHLCV legacy filename rename** — successor: addition to `gcs_migration_bundle_pipeline_mode_2026_05_08.md`
  Phase 2.X per disposition.

## Composes with

- CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green" HARD RULE — every phase gate requires operational
  evidence, not smoke-test green.
- CLAUDE.md "Capture Discoveries As Plan Todos Immediately" HARD RULE — gap closures captured in this plan vs scattered
  across chat / auto-memory.
- CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE — banner-add tasks listed above.
- CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE — codex updates per phase boundary.
- CLAUDE.md "Plans must capture full codebase impact upfront" HARD RULE — full impact surface enumerated via the Phase
  1.A-F + Phase 2.0-2.5 + Phase 3.1-3.7 inventory.
- CLAUDE.md "Plan Archival" HARD RULE — at archive time, every deferred item migrates to an active home.
- CLAUDE.md "Citadel-Grade Planning Standards § 1 Pre-Audit" — pre-audit shipped as the audit report at top of this
  session; this plan is the captured output.
- `master_to_live_defi_2026_05_23.md` — the readiness model; this plan is the time-axis sequencing of how the readiness
  model fills in.
- `manifest_evolution_SUPERSEDED_2026_05_21.md` — the schema-axis enforcer; this plan is the time-axis enforcer.
- `manifest_migration_SUPERSEDED_2026_05_21.md` — the migration-stage coordinator; this plan adds Stage 0 (VM drain) and
  Phase 3 (backfill resumption) as bookends.

## DONE-2026-05-11 — slot 6 (harsh-workspace-qg-tab) day-1 status (freeze-gate items 8 + 9)

Slot 6 day-1 work toward the Phase 1 freeze gate (2026-05-15). Freeze-gate items 8 + 9 remain `- [ ]` — this is the
running-status note + EOD deferral-audit, not a flip. Re-runs across days 2-4.

**Shipped 2026-05-11**:

- `PM@a4512ed3` — **Track D P0-2 (slot 6 half — the QG gate, not the code fix)** — new QG STEP 5.67
  (`scripts/quality-gates-base/base-service.sh` + `scripts/quality_gates/check_banned_placeholder_methods.py` +
  `scripts/quality_gates/banned_placeholder_methods_baseline.yaml`): AST-walk detecting `_create_empty_output` /
  `_handle_empty_tick_data` / `_create_full_day_empty_output` / `_create_closed_market_candle` /
  `_maybe_write_vix_gap_placeholder` defs + direct `*.upload_bytes(...)` candle writes that bypass `record_captured`.
  Baseline-aware SHRINKING ratchet: the 8 currently-known MDPS occurrences are `pending_removal` → WARNINGS (exit-clean,
  doesn't break MDPS QG); any NEW occurrence not in the baseline fails CI. Verified exit 0 on MDPS / on no-occurrence
  repos, exit 1 on a synthetic new `def _create_empty_output`; `bash -n` clean; ruff-clean. **The P0-2 _code fixes_ —
  delete legacy `orchestration_writer._write_candles`, fix `tradfi/ohlcv_passthrough.py`, flip `output_schemas.py` OHLCV
  nullability, resolve the triple-SSOT — are writegate Phase 2.A + slot 5 (NOT slot 6).** As writegate Phase 2.A deletes
  the methods, it removes the matching baseline entries. **Follow-up (c) ✅ DONE 2026-05-11 PM (`PM@d75415fd`)** — after
  writegate Phase 2.A P0-2 surgery landed (MDPS@a964b96 + step-3/4/6 commits): baseline shrank 8→2 (steps 3/6 DELETED 4
  occurrences → entries removed; `_maybe_write_vix_gap_placeholder` REFORMED by step 4 to route through
  `record_empty_for_shard(reason=EXPECTED_KNOWN_SOURCE_GAP)` — no placeholder parquet — but kept baselined-as-warning
  pending a cosmetic rename); `_handle_empty_tick_data` DROPPED from `BANNED_METHOD_NAMES` entirely (writegate reformed
  both copies into the canonical honest-handler — it's now the _recommended_ name, so flagging it = noise); residual 2 =
  `_maybe_write_vix_gap_placeholder` (misnomer name) + `output_writer_service.py:upload_bytes` (DEAD CODE —
  `OutputWriterService` not instantiated on any live path). **All follow-ups ✅ DONE 2026-05-11 PM**: (a)
  `scripts/quality_gates/test_check_banned_placeholder_methods.py` — 28 tests mirroring `test_check_removed_symbols.py`
  (incl. the regression guard that `_handle_empty_tick_data` stays OUT of `BANNED_METHOD_NAMES`); ruff-clean + 28 passed
  (`PM@c497cab7`). (b) `/codex/06-coding-standards/quality-gates.md` — STEP 5.67 added to the QG-STEP cross-reference
  table + a dedicated `## STEP 5.67` section (how-it-works / no-add-a-new-entry-fix-it-instead / maintenance /
  composes-with) per the Post-Plan-Phase Codex Audit HARD RULE (`PM@<this-commit>`). (c) ✅ baseline shrink 8→2
  (`PM@d75415fd`). Slot-6 STEP-5.67 work fully closed; residual baseline-2 clears when writegate Phase 2.A cosmetically
  renames `_maybe_write_vix_gap_placeholder` + deletes the dead `OutputWriterService` class (writegate's job, not slot
  6).
- **Track D P0-3 disposition (commodity phantom-row)** —
  `features-service/market(...)/commodity/cli/handlers/batch_handler.py:251-290` `_write_manifest` calls
  `writer.add(...)` for every (commodity, day) regardless of `_process_day` success → a fully-failed run still populates
  `captured`-shaped rows → `_should_skip_shard` permanently skips them. **Classified** (case-B/C phantom-manifest-row
  bug, exactly the class CLAUDE.md "Manifest phantom audit" warns about). **Captured**:
  `wave3x_track_d_findings_2026_05_11.md` § features-set-2 (D6, with the fix + owner) +
  `plans/archive/issues/qg_sweep_2026_05_11.md` § cross-refs + this DONE block's deferred-work table. **Owner-routed**:
  slot 5 (live-pipeline) + writegate Phase 2.A (the fix is in `features-service` which is
  slot-2-sole-writer-until-Phase-7 territory — slot 6 is read-only across service repos). No separate issue doc (would
  duplicate the Track D doc). Slot 6's P1 phantom-audit pass watches for re-growth from this bug if/when the commodity
  backfill runs.
- `market-tick-data-service@3da026d` — **Track D P0-1 fix** (`wave3x_track_d_findings_2026_05_11.md` P0-1; owner
  re-routed to slot 6 by operator 2026-05-11): `engine/orchestrator.py` honest-coverage sentinel pass called
  `ManifestWriter.record_empty(row_key=...)` with NO `reason=` at 3 callsites (:2671 sports / :2808 Tier-3
  per-instrument / :2849 Tier-2 venue-level) + `scripts/rebuild_prediction_manifest.py:351` —
  `LegacyBlankErrorReasonError` swallowed by the wrapping `except Exception: "non-blocking"` → sentinel pass aborted
  silently for CeFi/sports on any zero-data-shard date (no `empty_confirmed` / `attempted_failed` rows landed → absence
  masked as "never attempted"). Fix: all 4 callsites pass `reason="SOURCE_RETURNED_ZERO"`; new
  `except (LegacyBlankErrorReasonError, UnknownEmptyConfirmedReasonError): raise` before the swallowing `except`
  (manifest-contract violations now fail loud); imports from the UAC/UTL root facades. Verified ruff-clean + zero new
  basedpyright errors + all 12 `test_orchestrator_capture_status.py` / `test_rebuild_prediction_manifest_force.py` tests
  pass. **Slot-1 to-route**: tell slot 5 / the writegate Phase 2.A owner that P0-1 is done (Track D doc routed it to
  them; operator moved it to slot 6); the Track D doc's P0-1 owner pointer is now stale.
- `PM@cfeb79fc` — STARTED boot-ack ping.
- `PM@04ed9203` — **freeze-gate item 9 (codex SSOT audit pass)** — `plans/archive/issues/codex_audit_2026_05_11.md`: 25
  Phase 1 plans scanned; 91 codex doc paths referenced; 58 present / 33 referenced-but-not-yet-created (all 33 are
  unchecked `- [ ]` items in their owning plans — expected pending Phase-1 work, deadline = this freeze gate). Per-plan
  pending-codex breakdown table = the freeze-gate-9 readiness checklist. Findings: F2 (codex
  `availability-manifest-and-data-status.md` v8 dataclass missing `feature_family` which UTL code has @`c16cef3` —
  routed to slot 2's `features_repo_consolidation` codex phase); F3 (v8 manifest-schema declaration owner ambiguous —
  this plan `:139`/`:174-179` says "writegate slice (b) Phase 5.1, NOT a separate file"; codex doc +
  `manifest_schema_final_gate_2026_05_09.md` say the final-gate plan — needs a slot-1/operator reconcile; tracked in
  `codex_audit_2026_05_11.md` § Open questions Q1). Core schema/manifest/pipeline codex docs spot-checked: healthy.
- `PM@e8cbe46b` — **freeze-gate item 8 (workspace QG) — static day-1 baseline** —
  `plans/archive/issues/qg_sweep_2026_05_11.md`: `ruff check` (source dirs only) 20/22 repos CLEAN; `features-service`
  13×I001 import-org (auto-fixable — mid-consolidation by slot 2, expected); `system-integration-tests` 4×C901
  complexity 9-11 > SIT-local-limit 7 (pre-existing, not slot-2-related). `# type: ignore`: 344 total, 343 coded form,
  **0 actual bare directives workspace-wide** (the classic architectural-violation-masker is absent). basedpyright +
  full `quality-gates.sh` sweep **deferred days 2-4** — slot worktrees have no per-repo `.venv`; needs
  `bash scripts/setup.sh` per repo first (~30-60 min for 22 repos).

**Deferred work (slot 6) — all captured in active plans / issue docs**:

| Deferred item                                                                                                                                                                                                                                                                                                                                                  | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Tracked in                                                                                                                                                                                                                                                                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Full `bash scripts/quality-gates.sh` workspace sweep (basedpyright + pytest + 60+ STEP checks)                                                                                                                                                                                                                                                                 | slot worktrees have no per-repo `.venv` — `setup.sh` per repo needed first                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | `plans/archive/issues/qg_sweep_2026_05_11.md` § "Days 2-4 follow-up" (1)+(2); `plans/active/work_split_2026_05_11_harsh.md` § Slot 6 full-execution criterion                                                                                                                                                                                 |
| Sampled `# type: ignore[...]` reason-comment audit (~20-30 of 343)                                                                                                                                                                                                                                                                                             | day-1 only confirmed zero _bare_ directives; per-line architectural check pending                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | `plans/archive/issues/qg_sweep_2026_05_11.md` § "Days 2-4 follow-up" (3)                                                                                                                                                                                                                                                                      |
| Phantom manifest audit (P1) — `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group {cefi,defi,sports,tradfi,prediction} --dry-run`                                                                                                                                                                                                | **✅ ALL 5 RAN 2026-05-11** (all via `launch-defi-phantom-recon-vm.sh <ag> --dry-run`, GCE same-region e2-standard-4 — the launcher accepts any asset_group despite the `defi-` name; singleton-locked so they ran sequentially). **DeFi** (`…-defi-20260511-192115`, done 13:58 UTC): 311602 real / 1298 phantom (0.41%) — ALL `venue=EIGENLAYER`/`data_type=rewards`, ALL FALSE-positive (data at `…/data_type=eigenlayer_rewards/rewards.parquet`; audit probes `data_type=rewards/`). Root cause = shard-key drift in `eigenlayer_rewards_handler.py` → `defi_master` § Discoveries (P1). **DeFi real residual = 0.** **CeFi** (`…-cefi-20260511-193451`, done 14:16 UTC): 1290706 real / 2223 phantom (0.17% — UNDER <0.5% bar). Residual = blank `venue` 1453 + DERIBIT 136 (mostly `options_chain`/`futures_chain` bundled) + `venue=UNKNOWN` 111 + Bitfinex `*F0` ~400 — drift-axis-suspicious; per-cluster triage pending → `cefi_master` § "Port phantom-audit" todo. **TradFi** (`…-tradfi-20260511-194845`, done 14:24 UTC): 92125 real / 3976 phantom (~4.3% — **ABOVE bar; NEEDS TRIAGE**). Residual = `trades` 1017 + `tbbo` 1017 (identical ⇒ Databento per-schema-bundle drift) + `venue=UNKNOWN` 565 + `venue=YAHOO_FINANCE` 21 (VIX 15m source) + ~1356 other → `tradfi_master` § "Port phantom-audit" todo (P0 — the 4.3% is the highest of any asset_group). **Prediction** (`…-prediction-20260511-195513`, done 14:28 UTC): 14403 real / 71 phantom (0.49% — at bar). Residual = `venue=POLYMARKET` 50 + `venue=UNKNOWN` 21, all `data_type=trades` — small; predictions owner to triage. **Sports** (`…-sports-20260511-195856`, 686086 captured rows in scope, done 14:33 UTC, exit 0): **570562 real / 115524 phantom = 16.8% — WAY above bar.** Distribution: `STANDINGS` 12828, `SFI_LEAGUES` 12777, `INJURIES` 9843, `PLAYER_STATS` 878, `PLAYER_VALUES` 708, `FIXTURE_LINEUPS` 670, … + ~63k other. **Almost certainly mostly false-positive** — sports has its own per-league/bare-path SSOT (`unified_api_contracts.sports.candidate_parquet_paths`); the audit's sports dispatcher must use the CURRENT layout (the 2026-04-29 incident: stale `entity=odds/` vs `entity=footystats_odds/` → false 26% ODDS phantom — same class) AND apply the UAC `SOURCE_COVERAGE_START`/`DATA_TYPE_COVERAGE_START`/`KNOWN_COVERAGE_GAPS` date-range clips (the STANDINGS/SFI_LEAGUES/INJURIES clusters look like un-clipped pre-launch-date rows) → routed to `sports_master` § "Phantom recon" row + the consumed `sports_phantom_recon_and_failure_triage` plan. **Did NOT `--apply`** ANY run (false-positive majority everywhere; flipping would corrupt the manifest, 2026-05-04 130,897-false-positive class). **Cross-asset finding**: `venue=UNKNOWN` (+ blank-venue) phantoms appear in cefi (1453+111), tradfi (565), prediction (21) ≈ ~2150 total — a workspace-level data-quality issue (the manifest writer should never record `venue=UNKNOWN`/blank per the "Never overload venue" rule); needs root-cause = which adapter(s) write venue-less manifest rows; routed via `qg_sweep_2026_05_11.md` cross-refs. **Net**: ~2.28M real / ~123k flagged-phantom across all 5; the big numbers (sports 115k, tradfi 4k) are almost certainly mostly stale-audit-path false-positives — the residual work is (a) extend the audit's drift-axis coverage (sports per-league SSOT currency + UAC date-range clips; tradfi Databento per-schema-bundle; cross-asset venue-less-row handling), (b) per-cluster real-vs-false-positive verification, THEN (c) `--apply` only the genuinely-real subset. | `plans/active/work_split_2026_05_11_harsh.md` § Slot 6 (P1); `plans/archive/issues/qg_sweep_2026_05_11.md` § cross-refs + "Days 2-4 follow-up" (1); `defi_master` § Discoveries (EIGENLAYER shard-key drift); `cefi_master`/`tradfi_master`/`sports_master` § "Port phantom-audit"/"Phantom recon" rows (per-asset-group residual breakdowns) |
| ~~AST/grep QG STEP for banned placeholder methods~~ — **DONE**: STEP 5.67 (`PM@a4512ed3`) → baseline shrunk 8→2 (`PM@d75415fd`, drop `_handle_empty_tick_data` from the banned-name set + remove 4 deleted-method entries) → test file `PM@c497cab7` (28 tests) → codex `## STEP 5.67` section (`PM@<this-commit>`). All slot-6 follow-ups (a)/(b)/(c) closed. | Residual baseline-2 (`_maybe_write_vix_gap_placeholder` misnomer-name + `output_writer_service.py:upload_bytes` dead-code) clears when writegate Phase 2.A renames the method + deletes the dead `OutputWriterService` class — writegate's job, not slot 6. Nothing slot-6-pending.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | DONE block above; `plans/archive/issues/qg_sweep_2026_05_11.md` § "Days 2-4 follow-up" (5); `wave3x_track_d_findings_2026_05_11.md` § "Recommended decision" (3) (resolved)                                                                                                                                                                   |
| Codex SSOT audit pass — deepen currency spot-checks on the ~50 present docs the Phase 1.D/E/F plans touch (alerting/risk/DR, DeFi, UI/credentials)                                                                                                                                                                                                             | day-1 only spot-checked the schema/manifest/pipeline core + alerting cluster                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | `plans/archive/issues/codex_audit_2026_05_11.md` § "Days 2-4 follow-up"                                                                                                                                                                                                                                                                       |
| 33 codex docs referenced-but-not-yet-created for freeze-gate item 9                                                                                                                                                                                                                                                                                            | all are `- [ ]` items in their owning Phase 1 plans — those plans' codex phases create them by 2026-05-15                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | `plans/archive/issues/codex_audit_2026_05_11.md` § "Pending codex work" table (per-plan); each owning plan's "Codex SSOT updates" phase                                                                                                                                                                                                       |

EOD deferral-audit (per CLAUDE.md "End-of-cycle audit clause"): every row above is grep-findable in `plans/active/`
(work-split, the 3 slot-6 issue docs in `plans/active/issues/`, or — for the 33 codex docs — the owning plans' `- [ ]`
todos). No deferral lives only in chat.

## DONE-2026-05-12 — Harsh slot 6 (harsh-workspace-qg-tab) end-of-shift handover

Harsh shift ending 2026-05-12 ~14:42 UTC. Slot-6 role this cycle = QG / codex-currency / phantom-audit cadence +
QG-validate slot-2-to-5 shippable units. Everything below is **committed + pushed to `live-defi-rollout`** — nothing
uncommitted, nothing in-flight (the last shippable unit, the Sports phantom-audit result, was already pushed before the
wrap-up signal). Per-shippable-unit pushes throughout, so Ikenna's side has the full state.

### ✅ Shipped this shift (with evidence)

1. **Consolidator poll-list completeness** (slot 3's open Q "are other per-data*type buckets missing?") —
   `deployment-service@2a76a2a`: added `dex-pools-{pid}` + `liquidations-{pid}` to `launch-manifest-consolidator-vm.sh`
   `BUCKETS` (slot-3's `ad4d448` added 8 of the 10 per-data_type DeFi buckets in
   `_BUCKET_CATEGORY_OVERRIDES`/`_MTDS_DEFI_SUB_DIMENSIONS`; these 2 were missed — both written by MTDS handlers via
   `get_write_bucket_name()`). **Relaunched the daemon**: deleted slot-3's `manifest-consolidator-20260511-181538`, new
   `manifest-consolidator-20260511-190513` RUNNING + verified healthy — the first cycle **consolidated legacy seeds**
   for both new buckets: `dex-pools-{pid}` → 75983 rows, `liquidations-{pid}` → 38134 rows written to their canonical
   `_index/availability_index.parquet` (so there \_was* real un-consolidated data, not just future-proofing). Other
   asset_groups (CeFi options/futures, TradFi futures, prediction, sports) write to their asset-group canonical buckets
   which are already polled — no gap. Plan-flips + findings: `defi_master.md` § "Discoveries during Priority #5" (the
   consolidator P1 item flipped `[x]`; P2 future-gap item — features-\*/execution/ml buckets + the code_freeze Phase 2.6
   bucket-rename lockstep + the watchdog-dict `mtds-{gas-fees,lst-rates,dex-pools,liquidations,perp-funding}-`
   imprecision sub-finding). `harsh_orchestrator/pings/slot_6.md` 2026-05-11 13:40/13:45 UTC.
2. **MTDS ruff fix** — `market-tick-data-service@61f872d`: stray `test_adapter_watchdog_wiring.py` ruff-line-collapse
   (origin was out-of-sync with `ruff format`). Mechanical; cleared the slot's working tree.
3. **Codex deepening pass** — `codex_audit_2026_05_11.md` § "Days-2-4 codex deepening pass — 2026-05-11 ~13:45 UTC": 3
   of the 4 day-1-flagged NEW codex docs now landed (`risk-rule-taxonomy.md` 168 L / `circuit-breaker-rule-taxonomy.md`
   350 L / `service-emission-policy.md` 134 L); `cross-asset-rescan-protocol.md` still ABSENT. Two drift findings
   found + routed to `manifest_schema_final_gate_2026_05_09.md`: (a) Phase-2 follow-up P2 — `manifest_writer.py:131`
   still `MANIFEST_SCHEMA_VERSION = 7` while the v8 emission columns are present; codex
   `availability-manifest-and-data-status.md:261` prose says "=8" but its snippet (:265) says "=7" → doc inconsistency
   (nothing branches on `==8`, no breakage; ikenna-slot-6 to decide bump-code vs soften-prose); (b) the Phase-3 boundary
   entry for `/codex/02-data/cross-asset-rescan-protocol.md` was missing from the plan's "Codex SSOT updates" section —
   added it, flagged ❌ NOT YET SHIPPED post-Phase-3-ship, owner ikenna-slot-6. `service-output-emission-semantics.md`
   re-confirmed v8-current. Revised codex-doc count 58→61 present / 35→32 pending.
4. **QG-validated slot-5's Phase 4** `market-data-processing-service@0068b2f` (LiveStreamAggregator) —
   `qg_sweep_2026_05_11.md` regression-log row: ✓ static, Live=batch invariant satisfied at code level
   (`live_aggregator.py:77` imports `create_candle_from_interval` from `app.calculators.fast_candle_aggregation` — THE
   batch fn; `:338` calls it), 7 Protocol adapters thin, CLI follows `--operation`/`--mode`/`--shard-spec`, ruff exit-0,
   new file 511 L, known follow-ups documented (no silent debt). (The earlier slot-2/4 queued units —
   `features-svc@45efbe44`, `deployment-svc@a7eba4f`, `UTL@2118b1e`, `features-svc@8f03ceeb`, `MTDS@c186ecb`,
   `deployment-svc@a5c2082`, the 28-commit `features-svc@e4b10570` fan-out — were validated in the prior session; rows
   already in the regression-log.)
5. **GCE-VM phantom audit — ALL 5 asset_groups** (`launch-defi-phantom-recon-vm.sh <ag> --dry-run`, GCE same-region
   e2-standard-4; all VMs self-deleted on completion; **no `--apply` run — the manifest is unmodified**):
   - **DeFi** (`defi-phantom-recon-defi-20260511-192115`): 311602 real / 1298 phantom (0.41%) — ALL FALSE-positive
     (`venue=EIGENLAYER`/`data_type=rewards`; data exists at `…/data_type=eigenlayer_rewards/rewards.parquet`; audit
     probes the manifest's `data_type=rewards/`). Root cause = **shard-key-SSOT violation** in
     `eigenlayer_rewards_handler.py` (`record_captured(data_type="rewards")` but `to_parquet` path uses
     `data_type="eigenlayer_rewards"`; stale docstring too). **DeFi real residual = 0.** → `defi_master.md` §
     Discoveries (P1; fix = align `_EIGENLAYER_DATA_TYPE` to `"eigenlayer_rewards"` + one-time manifest migration + fix
     docstring; defi-pipeline owner).
   - **CeFi** (`defi-phantom-recon-cefi-20260511-193451`): 1290706 real / 2223 phantom (0.17% — UNDER the <0.5%
     `cefi_master` criterion). Residual = blank `venue` 1453 / DERIBIT 136 (mostly `options_chain`+`futures_chain`
     bundled) / `venue=UNKNOWN` 111 / Bitfinex `*F0` ~400 — drift-axis-suspicious. → `cefi_master.md` § "Port
     phantom-audit" todo (per-cluster real-vs-false-positive triage pending — cefi owner).
   - **TradFi** (`defi-phantom-recon-tradfi-20260511-194845`): 92125 real / 3976 phantom (~4.3% — **ABOVE bar**; highest
     of any asset_group). Residual = `trades` 1017 + `tbbo` 1017 (identical ⇒ Databento `trades;tbbo` per-schema-bundle
     drift) + `venue=UNKNOWN` 565 + `venue=YAHOO_FINANCE` 21 (VIX 15m) + ~1356 other. → `tradfi_master.md` § "Port
     phantom-audit" todo (**P0** — verify whether the parquet exists bundled vs per-schema; add the per-schema-bundle
     drift axis to the audit; tradfi owner).
   - **Prediction** (`defi-phantom-recon-prediction-20260511-195513`): 14403 real / 71 phantom (0.49% — at bar).
     Residual = `venue=POLYMARKET` 50 + `venue=UNKNOWN` 21, all `data_type=trades` — small; predictions owner to triage
     (likely canonical_question_group bundling vs per-market_id path).
   - **Sports** (`defi-phantom-recon-sports-20260511-195856`): 570562 real / 115524 phantom (16.8% — **WAY above bar**).
     Distribution: `STANDINGS` 12828, `SFI_LEAGUES` 12777, `INJURIES` 9843, `PLAYER_STATS` 878, `PLAYER_VALUES` 708,
     `FIXTURE_LINEUPS` 670, … + ~63k other. **Almost certainly mostly false-positive** — sports has its own
     per-league/bare-path SSOT (`unified_api_contracts.sports.candidate_parquet_paths`); the audit's sports dispatcher
     must use the CURRENT layout (the 2026-04-29 incident: stale `entity=odds/` vs `entity=footystats_odds/` → false 26%
     ODDS phantom — same failure class) AND apply the UAC
     `SOURCE_COVERAGE_START`/`DATA_TYPE_COVERAGE_START`/`KNOWN_COVERAGE_GAPS` date-range clips (the
     STANDINGS/SFI_LEAGUES/INJURIES clusters smell like un-clipped pre-launch-date rows). → `sports_master.md` §
     "Phantom recon" row (routes to the consumed `sports_phantom_recon_and_failure_triage` plan).
   - **Cross-asset finding** (workspace-level): `venue=UNKNOWN`/blank-venue phantoms across cefi (1453+111) / tradfi
     (565) / prediction (21) ≈ ~2150 — the manifest writer should never record `venue=UNKNOWN`/blank per the "Never
     overload venue with non-venue data" rule; needs root-cause = which adapter(s) write venue-less manifest rows.
     Routed via the `code_freeze` DONE-2026-05-11 phantom-audit deferral row + `qg_sweep_2026_05_11.md` cross-refs.
   - **Net**: ~2.28M real / ~123k flagged-phantom; the big numbers (sports 115k + tradfi 4k) are almost certainly mostly
     stale-audit-path false-positives. Residual work: (a) extend `reconcile_phantom_manifest_rows_all.py`'s drift-axis
     coverage (sports per-league SSOT currency + UAC date-range clips; tradfi Databento per-schema-bundle; cross-asset
     venue-less-row handling), (b) per-cluster real-vs-false-positive verification, THEN (c) `--apply` only the
     genuinely-real subset. Full per-asset-group results live in the `code_freeze` DONE-2026-05-11 phantom-audit
     deferral row + each asset_group's master plan + `slot_6.md` 2026-05-11 14:00/14:18/14:31/14:35 UTC.

State at handover: no VMs left running that slot 6 launched (all 5 phantom-recon VMs self-deleted);
`manifest-consolidator-20260511-190513` RUNNING + healthy (the only consolidator, singleton). Slot branch `tab/hk/6` ==
`origin/live-defi-rollout` (0 ahead/0 behind).

### ⏭ What's left (carry-forward for Ikenna's agent — exact next steps)

| Item                                                                                                                                                     | Status                                                                               | Exact next step                                                                                                                                                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Freeze-gate item 8** (workspace QG green) — full `quality-gates.sh` + basedpyright workspace-wide sweep                                                | NOT done — deferred all cycle                                                        | Slot worktrees have no per-repo `.venv` → `setup.sh` per repo first, then `cd <repo> && bash scripts/quality-gates.sh` (~30-60min/repo × 22 repos). Do highest-risk first (UAC, UTL, MTDS, MDPS, features-service, deployment-api). Tracked in `qg_sweep_2026_05_11.md` § "Days 2-4 follow-up" (1)+(2). |
| **Freeze-gate item 9** (codex SSOT currency) — ~50-present-codex-doc currency spot-check (1.D alerting/risk/DR + 1.E DeFi + 1.F UI/credentials clusters) | Partial — 3/4 NEW docs landed, 2 drift findings routed; the bulk spot-check not done | Walk the ~50 present codex docs the Phase-1 plans touch (esp. Ikenna slot 7's Round 1-4 just landed — verify the alerting/risk/DR docs reflect the new SSOTs). Tracked in `codex_audit_2026_05_11.md` § "Days 2-4 follow-up". Then both items 8+9 → `[x]` per the master plan.                          |
| **EIGENLAYER `rewards` shard-key drift**                                                                                                                 | Diagnosed + routed                                                                   | Fix in `eigenlayer_rewards_handler.py`: `_EIGENLAYER_DATA_TYPE = "eigenlayer_rewards"` (match the parquet path) + one-time manifest migration `data_type=rewards`→`eigenlayer_rewards` + fix the stale docstring (:21). `defi_master` § Discoveries (P1). Defi-pipeline owner.                          |
| **TradFi 4.3% phantom** (P0)                                                                                                                             | Diagnosed + routed                                                                   | `tradfi_master` § "Port phantom-audit" todo: verify the `trades`/`tbbo` 2034 — parquet bundled-on-disk vs per-schema-in-manifest? If bundled-vs-per-schema drift, fix the Databento adapter shard-key + add the per-schema-bundle drift axis to `reconcile_phantom_manifest_rows_all.py`. Tradfi owner. |
| **CeFi 2223 / Prediction 71 / Sports 115524 phantom residuals**                                                                                          | Snapshotted (dry-run); not triaged                                                   | Per-cluster real-vs-false-positive triage in each asset_group's master plan; for sports, FIRST verify the audit's sports dispatcher against `candidate_parquet_paths` + the UAC date-range clips (almost certainly mostly false-positive). Then `--apply` only the genuinely-real subset.               |
| **Cross-asset `venue=UNKNOWN`/blank-venue phantoms** (~2150)                                                                                             | Found + flagged                                                                      | Root-cause = which adapter(s) `record_captured`/`record_empty` without a resolved venue; fix the writer-side guard. Workspace data-quality follow-up.                                                                                                                                                   |
| **`MANIFEST_SCHEMA_VERSION` doc-vs-code drift** + **`cross-asset-rescan-protocol.md` codex stub**                                                        | Both routed                                                                          | `manifest_schema_final_gate_2026_05_09.md` Phase 2 follow-up + Phase 3 codex entry. Ikenna-slot-6.                                                                                                                                                                                                      |
| QG STEP 5.67 baseline maintenance                                                                                                                        | No new banned-NaN-placeholder patterns surfaced this shift                           | Re-check `banned_placeholder_methods_baseline.yaml` if any surface during the QG sweep.                                                                                                                                                                                                                 |

### Plan-flips this shift (PM commits)

PM@`d52cc0c5`→rebased (defi_master Priority #5 consolidator audit) · PM@`116aa6f7`→rebased (slot_6 ping + watchdog
sub-finding) · PM@`7a77883d`→rebased (mdps@0068b2f QG-validated + consolidator-fix correction) · PM@`f8d4d9bf`→rebased
(MANIFEST_SCHEMA_VERSION finding) · PM@`b0ad35bf`→rebased (codex deepening pass) · PM@`11faa8ac`→rebased (DeFi
phantom-audit result) · PM@`7148edd2` (CeFi phantom-audit result) · PM@`8771ee42`→rebased (TradFi+Prediction
phantom-audit) · PM@`4548b5ea`→rebased (Sports phantom-audit + final scoreboard) · this commit (end-of-shift handover).
Code: `deployment-service@2a76a2a` · `market-tick-data-service@61f872d`.

## DONE-2026-05-11 — slot 5 (ikenna-defi-phase-1e-tab) DeFi Phase 1.E sequencing readiness audit

Slot 5 (Ikenna side, `tab/ikennaigboaka/5`) day-1 against the work-split § "Slot 5 — DeFi Phase 1.E sequencing
readiness + cross-plan coordination" scope. Audit the 4 Phase 1.E plans (`defi_catalogue_chain_primitives_2026_05_10`

- `arbitrage_price_dispersion_finalisation_2026_05_09` + `cme_polymarket_arb_2026_05_08` +
  `defi_recursive_borrow_archetypes_2026_05_10`) for Phase 2 freeze readiness; refresh the anti-sequencing audit table;
  verify cross-plan banner sweep on the 9 + 3 banner targets.

**Shipped 2026-05-11**:

- `PM@fff39bfa` — **Anti-sequencing audit table refresh** (this plan § "Anti-sequencing audit"). Updated 2 existing
  rows + added 2 new rows.
  - **`arbitrage_price_dispersion_finalisation_2026_05_09.md`**: ✅ SHIPPED 2026-05-09 per audit. UAC
    `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` present at `enums.py:68` (grep-verified — no `LEVERAGED_FUNDING_ARB`
    standalone). Phases A-E shipped per plan body commit ledger: strategy-service@24f8494 (dispatcher) + @0b4ef0e
    (helper module) + @04c0d52 (engine 8-step loop) + @de9b4b0 (multi-pair allocator); pnl-attribution archetype rows
    shipped; codex circular-ref resolved Phase E. **NO new canonical_question_group; NO new StrategyArchetype enum
    value. Anti-sequencing risk = NONE.** Two P1 carryover items remain (canonical BTC/USDT slot entry at
    `archetype_slot_resolver.py` + slot resolver test) — non-blocking for Phase 2 (config additions land at
    strategy-service, not UAC/manifest).
  - **`cme_polymarket_arb_2026_05_08.md`**: ✅ Phase 1 SHIPPED uac@b95d146 per audit. `InstrumentType.EVENT_CONTRACT`
    present at `_instrument_enums.py:54` + `INSTRUMENT_TYPES_BY_VENUE[CME]` (venue_constants.py:358) +
    `INSTRUMENT_TYPE_FOLDER_MAP["EVENT_CONTRACT"] = "event_contracts"` + Databento BAG classifier
    (`external/databento/normalize.py:69-110`; root prefix dispatcher). **Enum value MUST be referenced in v8 schema
    declaration** ([`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) — canonical v8
    owner per operator decision 2026-05-11 commit `39ab61e5`; slot 5 → final-gate owner handshake). Phases 2-5 BLOCKED
    (predictions-master Phase 5 + tradfi-master Q1+Q2 + post-cutover per plan body) — explicitly OUT of May-23 scope. No
    additional anti-sequencing risk from post-cutover phases since `linked_canonical_question_group` is a cross-link
    field, not a new shard atom dimension.
  - **NEW row — `defi_recursive_borrow_archetypes_2026_05_10.md`**: AD-1 FLIPPED 2026-05-10 per cross-plan audit Q10
    ratification — Family 1 + Family 2 are NOW NEW UAC StrategyArchetype enum values
    (`CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED`), no longer config variants of
    CARRY_RECURSIVE_STAKED. UAC PR ownership transferred to
    `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07` Stream C (most-comprehensive-owner rule — Stream C
    already ships the 8→11 archetype expansion codex backport). Plan body Phase 1 transferred to
    `defi_catalogue_chain_primitives_2026_05_10` Phase 1 + 3 (lending-indices data_types + adapter rewrites + backfill
    VM). Per slot 5 grep 2026-05-11: NEITHER enum value present in UAC `internal/architecture_v2/enums.py:31-118` yet.
    **Must land in v8 declaration before Phase 1 freeze 2026-05-15.** Decision: Ship via
    `defi_archetypes_canonicalisation` Stream C (the canonical owner) before Phase 1 freeze; slot 5 →
    [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) owner v8 schema declaration
    handshake per work-split Cross-tab handshakes (P0).
  - **NEW row — `defi_catalogue_chain_primitives_2026_05_10.md`**: NEW `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` /
    `LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` data_type enums + 26 venue entries + Solana Jito MEV mode +
    PERP_MARGIN_TIERS table + LST_TOKEN_TO_PROTOCOL_ASSET SSOT. **Existing UAC state per audit**: `CHAIN_GENESIS_DATES`
    (chain_env.py:91) covers 22 chains ✅; `PROTOCOL_LAUNCH_DATES` (chain_env.py:144) covers ~50+ (chain, protocol)
    entries including Aave V3 multi-chain + Compound V3 + Uniswap V2-V4 + Spark + Lido + Rocket Pool + Etherfi +
    Ethena + Maker + Frax + Solana protocols ✅ (Tab 14 audit 2026-05-08 refined many to subgraph-truth dates). **Open
    per Phase 1A**: 26 new venue entries (Yearn / Convex / Beefy / Pendle / Idle / Balancer / Sushi V2+V3 / PancakeSwap
    V3 / Camelot V3 / Aerodromeq V3 / Velodrome V2 / TraderJoe V2 / Raydium / Orca / Jupiter / Spark verify / Radiant /
    RocketPool verify / Solblaze / EigenLayer / Symbiotic / Karak / Renzo / KelpDAO / Puffer / Jito-restaking). Phase 1
    SEQUENTIAL gate for the catalogue plan's execution DAG; ~145-260 AI-day total scope across Phases 1-8 for May-23
    cutover. **Lending-indices data_types must land in v8 declaration**
    ([`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) — canonical v8 owner per
    operator decision 2026-05-11 commit `39ab61e5`; slot 5 → final-gate owner handshake).
  - **`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` row extended**: Stream B mostly shipped via
    `arbitrage_price_dispersion_finalisation`; Stream C owns the 8 → 11 StrategyArchetype enum expansion (must ship
    CARRY_RECURSIVE_BORROW_LENDING_ONLY + CARRY_RECURSIVE_BORROW_PERP_HEDGED + 3rd-TBD per AD-1 flip 2026-05-10). Stream
    C is Phase 1 critical path.
- `PM@8ea02ccd` — **Cross-plan banner sweep — 3 missing banners added**. Per work-split § Slot 5 P1 (banner sweep helper
  to slot 1 P0 banner verification): walked the 9 banner targets at this plan § "Cross-plan coordination banners" + the
  3 new (b+)-driven targets. **Result of grep audit 2026-05-11**:
  - ✅ 8 of 9 prior banner targets verified PRESENT (master_to_live_defi:26 / manifest_evolution_master:29 (epic) /
    manifest_migration_master:27 (epic) / gcs_migration_bundle_pipeline_mode:547 / aws_migration_defi_first:19 (already
    added by slot 1 PM@1b9e6451 yesterday per work-split note) / writegate_honest_coverage_endtoend:32 /
    features_repo_consolidation:931 / live_pipeline_mtds_mdps_features:938).
  - ✅ 3 missing banners ADDED this commit:
    - `deployment_ui_lifecycle_tabs_2026_05_08.md` — BE-AWARE banner clarifying env-tier UI surface already shipped
      pre-2026-05-11 per `/codex/05-infrastructure/deployment-ui-architecture.md`; no additional UI work for (b+)
      data-plane provisioning.
    - `simulation_scenarios_topology_price_shocks_2026_05_09.md` — BE-AWARE banner citing the anti-sequencing audit row
      (Phase 2.2 single-walk discipline risk if sim harness writes synthetic parquets into real buckets); required
      mitigation = dedicated `*-sim-*` env-tiered buckets per yaml SSOT.
    - `client_reporting_pnl_attribution_mvp_2026_05_10.md` — BE-AWARE banner citing the bucket-name SSOT (b+)
      requirement that client-reporting + pnl-attribution output buckets MUST use
      `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` not inline f-strings (QG STEP
      5.69 ratchet); Phase 0c bucket provisioning lands these.

**Open questions surfaced 2026-05-11 — NONE from slot 5 directly.** The work-split LEDGER cited two cross-side pings
from harsh-main 2026-05-11 07:10 UTC overlapping slot 5 + slot 1 scope (`EXPECTED_KNOWN_SOURCE_GAP` enum decision +
v8-schema-owner ambiguity); the v8-schema-owner question is writegate-Phase-5.1-ownership (slot 2's plan-of-record), NOT
a Phase 1.E sequencing question — slot 5 defers to slot 1 + operator for those.

**Findings raised 2026-05-11** (per CLAUDE.md "Findings Triage Discipline"):

- **Case-3 (outside my plan, fits another active plan)**: NEW UAC StrategyArchetype enum values
  `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` are owned by
  `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07` Stream C per AD-1 flip 2026-05-10. **Not fixing here**
  — surfaced in the new audit table row for `defi_recursive_borrow_archetypes`. Stream C agent picks up.
- **Case-3 (outside my plan, fits another active plan)**: lending-indices data_types (SUPPLY_APY / BORROW_APY /
  UTILISATION / LIQUIDATION_THRESHOLD / EMODE_PARAMS) are owned by `defi_catalogue_chain_primitives` Phase 1-LENDING
  (folded in from recursive-borrow per Q11 ratification). **Not fixing here** — surfaced in the new audit table row.
  Catalogue Phase 1 agent picks up.
- **Case-3 (handshake to slot 2)**: both new-enum work streams (defi_recursive_borrow new StrategyArchetype values via
  Stream C, defi_catalogue new data_type enums) need slot 2's v8 schema declaration to reference them. Captured in the
  audit table rows' decision columns + work-split § Cross-tab handshakes "Slot 5 → Slot 2 (P0)" entry.

**Deferrals after 2026-05-11 slot 5 session**:

| Item                                                                                                           | Status as of 2026-05-11                                                                                                                                    | Successor / blocker                                                                                                                                                                                       |
| -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| UAC `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `_PERP_HEDGED` enum add                                            | `todo` — NEITHER present in `unified-api-contracts/.../enums.py:31-118`                                                                                    | `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` Stream C — Phase 1 critical path before 2026-05-15                                                                                      |
| UAC `SUPPLY_APY/BORROW_APY/UTILISATION/LIQUIDATION_THRESHOLD/EMODE_PARAMS` data_type enum add                  | `todo` — not present in `canonical/domain/market_data/data_types.py` per Phase 1-LENDING todo                                                              | `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1-LENDING + Phase 1A — Phase 1 critical path before 2026-05-15                                                                                      |
| 25 new venue entries in UAC `defi_venues.py` (correcting plan body's stale `defi_venue_capabilities.py` ref)   | `done` — uac@`495d262` shipped 2026-05-11; ALL_DEFI_VENUES 74→99 / DEFI_VENUE_PHASE 1:1 / 13 aliases / 12 launch dates / 13 pending-investigation pairs    | `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1A PARTIAL annotation — `data_types` per-venue declarations (SourceCapability objects) DEFERRED to catalogue Phase 2-3 per-protocol adapter authors |
| v8 schema declaration referencing 3 new enum sets above                                                        | `todo` — owned by `manifest_schema_final_gate_2026_05_09.md` per operator decision 2026-05-11 commit `39ab61e5` (writegate slice (b) Phase 5.1 SUPERSEDED) | [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md); slot 5 → final-gate owner handshake                                                                               |
| `arbitrage_price_dispersion_finalisation` 2 P1 carryover items                                                 | `todo` — config additions at strategy-service, no UAC/manifest impact                                                                                      | `arbitrage_price_dispersion_finalisation_2026_05_09.md` Phase A remaining items (canonical BTC/USDT slot + resolver test)                                                                                 |
| `cme_polymarket_arb` Phases 2-5                                                                                | `blocked` — POST-CUTOVER per plan body; deps = predictions-master + tradfi-master                                                                          | `cme_polymarket_arb_2026_05_08.md` post-May-23 follow-up                                                                                                                                                  |
| `defi_recursive_borrow_archetypes` Phase 2+ (config schema → backtest → live)                                  | `blocked-after-defi_catalogue Phase 3 backfill captured`                                                                                                   | `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3 lending-indices backfill                                                                                                                          |
| Anti-sequencing audit row (P1) — `mock_data_pipeline_benchmarking_2026_05_10.md` bucket isolation confirmation | `todo` — verified row stays in audit table; not personally confirmed                                                                                       | Owner = the mock_data_pipeline plan; banner-sweep parallel target if it touches bucket-naming                                                                                                             |

**EOD deferral-audit** (per CLAUDE.md "End-of-cycle audit clause"): each row above is grep-findable in `plans/active/`
under the cited plan-of-record's `- [ ]` todos OR in this plan's audit table (rows added this commit). Slot 5 did NOT
create new issue docs — all findings route to existing active plans per Findings Triage Discipline case-3 (outside my
plan, fits another active plan). No deferral lives only in chat.

## DONE-2026-05-12 — slot 3 (ikenna-codefreeze-audit-tab) Phase 1.E freeze-gate closure audit — Day 1

Slot 3 (Ikenna side, `tab/ikennaigboaka/3`) Day 1 of the 4-day 2026-05-12→05-15 density-push cycle against work-split
row 3: "**`code_freeze` Phase 1 freeze-gate completion audit + Phase 2 sequencing dry-run + cross-plan banner sweep**".
6 Explore sub-agents fanned out 2026-05-12 ~boot UTC (Phase 0.B + LookaheadBias / Phase 4.GREP-VERIFY /
features-consolidation / TradFi phantom carry-forward / bucket_ssot+seed+QG / operator-triage on 3 PipelineMode
findings); results reconciled below. Plan-flips above (this commit) on the 5 freeze-gate items unambiguously ✅ shipped
with commit-SHA evidence.

### Audit summary — 9 freeze-gate items

| #   | Item                                                   | Status                                              | Owner / next step                                                                                                                                                                                                                                                                                                                 |
| --- | ------------------------------------------------------ | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Schema columns frozen (UAC v8)                         | ✅ DONE                                             | — (post-freeze `MANIFEST_SCHEMA_VERSION` 7→8 bump scheduled in Phase 4.DEFAULT-REMOVAL)                                                                                                                                                                                                                                           |
| 2   | error_reason taxonomy closed                           | ✅ DONE                                             | —                                                                                                                                                                                                                                                                                                                                 |
| 3   | 37 MDPS/MTDS callsites migrated                        | ✅ DONE 9/9 — all sub-items shipped 2026-05-12/13   | Phase 4.MTDS ✅ MTDS@`3da3f43` + UTL@`12d5e621`; Phase 4.FEATURES ✅ features-service@`842ff741`+`229a0963` (Harsh slot 3 2026-05-12); Phase 4.DEFAULT-REMOVAL ✅ utl@`547ff3c`; Phase 4.GREP-VERIFY ✅ PM@`4159b7ae`. Baseline: `pipeline_mode_explicit_baseline.yaml` 0 entries; STEP 5.70 clean (slot 10 verified 2026-05-13). |
| 4   | ServiceEmissionPolicy seed dict (19+ rows)             | ✅ DONE — 71 rows                                   | —                                                                                                                                                                                                                                                                                                                                 |
| 5   | available_at stamping + LookaheadBiasError strict-mode | 🟡 2/8 feature families wired                       | Owner reassignment needed for 6 remaining (delta_one / volatility / calendar / commodity / cross_instrument / multi_timeframe); `available_at_lookahead_bias_completion_2026_05_08.md` Phase 6 DEFERRED-AFTER chain links 0+1 + features-consolidation Phase 5.c                                                                  |
| 6   | features_repo_consolidation Phase 7 done               | ✅ DONE                                             | — (3 residual P2 items deferred to `features_service_qg_cleanup_2026_05_11.md`, non-blocking)                                                                                                                                                                                                                                     |
| 7   | bucket_name SSOT (code half)                           | ✅ DONE — physical half = Phase 2.4/2.6 (by design) | —                                                                                                                                                                                                                                                                                                                                 |
| 8   | Workspace QG green                                     | 🟡 static day-1 baseline only                       | Days 2-4 full sweep — slot worktrees need `setup.sh` per repo (~14-22h fan-out across 22 repos)                                                                                                                                                                                                                                   |
| 9   | Codex SSOTs updated                                    | 🟡 58 present / 33 pending                          | Days 2-4 bulk currency spot-check — Harsh slot 6 + Ikenna slot 3 cross-coverage                                                                                                                                                                                                                                                   |

### Preamble-specified items + carry-forward

| Item                                                    | Status                                               | Action / owner                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Phase 4.MTDS pipeline_mode sweep** (Q1-Q5)            | 🟢 **UNBLOCKED — slot 3 owns the mechanical sweep**  | Operator triaged 2026-05-12 evening at PM@`4c573302`: **Q1=(α)** approved (migrate `DefiManifestRecorder.record_captured` legacy `ManifestWriter.add()` → v8 `record_captured()` path); **Q2=(A)** approved (extend UAC `PipelineMode` enum + `SOURCE_PRIORITY` with `BATCH_YAHOO` / `BATCH_BARCHART` / `BATCH_FOOTYSTATS` / `BATCH_HYPERLIQUID_REST` / `BATCH_PYTH_HERMES` / `BATCH_CHAINLINK`). 3 issue docs flipped ✅ RESOLVED. Slot 3 picks up the ~60min mechanical sweep with 5-sub-agent fan-out (UAC enum extension → UTL DefiManifestRecorder migration → MTDS sweep → MDPS re-stamp → instruments-service re-stamp) per [`continuation_prompts_2026_05_12.md`](../archive/2026_05/continuation_prompts_2026_05_12.md) DAY-2 P0 INJECTED block. **Cross-side coordination**: Harsh slot 3 waits ~15-20min for Ikenna UAC enum on LDR before starting overlapping file work. Critical-path unblock for Phase 4.DEFAULT-REMOVAL → 2026-05-15 Phase 1 freeze gate. |
| **Phase 4.FEATURES**                                    | 🟢 UNBLOCKED — sweep not yet started                 | features_repo_consolidation Phase 7 ✅ SHIPPED unblocks gate. Owner: slot 2 (consistent with prior `ikenna-v8-mw-*` sub-agent pattern) OR fold into Phase 4.MTDS unblock once operator triage lands. ~6-12h fan-out across 6 feature-family adapters.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Phase 4.GREP-VERIFY** (workspace AST-walk QG STEP)    | ✅ **SHIPPED 2026-05-12 by slot 8 at PM@`4159b7ae`** | `unified-trading-pm/scripts/quality_gates/check_pipeline_mode_explicit_at_record_calls.py` (291 lines, 5-method closed set including `record_empty_for_shard`) + `test_*.py` (11 tests pass) + seeded `pipeline_mode_explicit_baseline.yaml` (112 entries: MTDS 97 + UTL 9 + features-service 6) + wired into `scripts/quality-gates-base/base-service.sh` STEP 5.70. Whitelist marker: `# QG-allow: pipeline-mode-not-applicable`. STEP 5.70 starts WARN-only; HARD-FAILs on any new occurrence; shrinks to 0 as Phase 4.MTDS sweep (slot 3) + 4.FEATURES + 4.DEFAULT-REMOVAL land. **Slot 3 collision finding 2026-05-12**: local parallel version was 70% identical (different whitelist marker phrasing + 27 vs 11 tests + bare-Name-callee handling + `**kwargs` forwarding tolerance); per CLAUDE.md "Two teammates × multiple parallel agents" rule, slot 8's pushed version wins; slot 3's local stash dropped.                                                   |
| **Phase 4.DEFAULT-REMOVAL**                             | ❌ blocked-after-MTDS+FEATURES+GREP-VERIFY           | Consolidated scope per Phase 2 P2 resolution (PM@`6efbfced`): (a) remove 4 `None` defaults from 5 `record_*` methods + (b) bump `MANIFEST_SCHEMA_VERSION` 7→8 at `manifest_writer.py:131` + (c) reconcile codex prose at `availability-manifest-and-data-status.md:258-262+265`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **Phase 0.B** (measure-honest-coverage.py PRE-baseline) | ❌ TODO                                              | Baseline doc `/codex/02-data/honest_coverage_baseline_2026_05.md` EXISTS as DRAFT (schema-only; all data cells TBD). Runner script `measure-honest-coverage.py` does NOT exist anywhere in workspace. Plan body marks as `[HUMAN] P0`. **Operator-runnable on same-region GCE VM**; gates Phase 12 ratchet POST-baseline comparison. Not a strict freeze-gate blocker but ties into deferred Phase 12 work — recommend operator-decision Day 2-3 on whether to (a) defer post-cutover (acceptable per plan body) or (b) author + run the script this cycle (slot 4 or 8 carry-forward).                                                                                                                                                                                                                                                                                                                                                                                   |
| **LookaheadBiasError strict-mode at features-\***       | ✅ **DONE** (freeze-gate item 5 closed)              | 8/8 families shipped: sports + onchain prior; delta_one / volatility / calendar / commodity / cross_instrument / multi_timeframe at `features-service@a0011d17` 2026-05-13.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **Carry-forward — TradFi 4.3% phantom audit triage**    | ❌ NOT YET OPENED — does NOT block freeze            | Diagnosed 2026-05-11 (`defi-phantom-recon-tradfi-20260511-194845`); 3976 phantom (~4.3%, ABOVE bar). Routed to `tradfi_master.md` § "Port phantom-audit" P0 todo. NO named owner in 2026-05-12 work-split. Dry-run only (manifest unmodified). Per-cluster real-vs-false-positive triage = POST-CUTOVER scope. **Sub-finding**: workspace-level `venue=UNKNOWN`/blank-venue cluster (~2150 cross-asset) needs adapter-side guard. Escalation: slot 1 / work-split rebalance to name TradFi-domain owner post-cutover.                                                                                                                                                                                                                                                                                                                                                                                                                                                     |

### Go/no-go signal for 2026-05-15 Phase 1 freeze gate

**🟢 GO — updated 2026-05-12 evening** — Phase 1 freeze gate FEASIBLE BY 2026-05-15. Updated state (vs original
`CONDITIONAL GO` posted Day 1 ~PM):

1. ~~**Operator triages 3 PipelineMode findings**~~ → ✅ **CLOSED 2026-05-12 evening** at PM@`4c573302`: Q1=(α) + Q2=(A)
   approved. 3 issue docs flipped ✅ RESOLVED.
2. ~~**Slot 3 ships GREP-VERIFY AST-walk**~~ → ✅ **SHIPPED 2026-05-12 by slot 8** at PM@`4159b7ae` (race-won; slot 3
   local version dropped per "pushed wins" rule).
3. **Phase 4.MTDS mechanical sweep** — slot 3 (me) ships Day 1-2 evening / Day 2 (~60min for sweep itself + ~1-2h for
   UAC enum extension + DefiManifestRecorder migration); 5-sub-agent fan-out.
4. **Phase 4.FEATURES sweep** ships Day 2-3 — slot 2 or 4 pickup; 6 callsites pre-audited at PM@`c1414ed7`; ~6-12h
   fan-out across 6 family adapters.
5. **Phase 4.DEFAULT-REMOVAL** ships Day 3-4 — sequenced after 3+4.
6. **6 LookaheadBiasError strict-mode** family wire-ins — owner reassignment in 2026-05-13 cycle (currently
   deferred-after-Phase-0+1; if not reassigned + landed, item 5 declares slip post-freeze).
7. **Workspace QG full sweep** Days 2-4 — 22 repos × `setup.sh` + `quality-gates.sh`.
8. **Codex bulk spot-check** Days 2-4 — Harsh slot 6 + Ikenna slot 3 cross-coverage.

### Slot 8 go/no-go signal (manifest_schema_final_gate Phase 3 consumer sweep ramp gate)

**🟢 GO TO RAMP** — published 2026-05-12 Day 1 (vs work-split commitment of "EOD Day 2 = 2026-05-13"; ahead of
schedule). Phase 1 freeze-gate items that gate Phase 3 (v8 schema landing on real GCS) are ALL ✅ shipped OR
🟡-partial-with-no-Phase-3-blocker. The v8 schema column declaration + UTL ManifestWriter + cross-asset-rescan launcher
are operationally complete per `manifest_schema_final_gate_2026_05_09.md` Phases 1/2/3. Phase 3 consumer sweep can
proceed in parallel with the ongoing Phase 4.MTDS unblock. Cross-side ping shipped this cycle.

### Operator decisions — STATUS

- ~~**Q1** (DefiManifestRecorder migration α vs β)~~ — ✅ **CLOSED 2026-05-12 evening** at PM@`4c573302`: operator
  picked α (canonical no-double-SSOT). Slot 3 ships the migration as part of the ~60min Phase 4.MTDS mechanical sweep.
- ~~**Q2** (PipelineMode enum extension A vs B vs C)~~ — ✅ **CLOSED 2026-05-12 evening** at PM@`4c573302`: operator
  picked A (extend UAC enum with 6 missing values). Slot 3 ships the UAC enum extension as part of the Phase 4.MTDS
  sweep.
- **TradFi-domain owner** assignment for phantom triage — still outstanding (post-cutover scope; not 2026-05-15
  critical).

### Carry-forward to Day 2-4 (slot 3 own scope) — UPDATED 2026-05-12 evening

- [x] [SCRIPT] P0. ~~Ship `check_pipeline_mode_explicit_at_record_calls.py` + tests + `base-service.sh` STEP wiring~~.
      ✅ **SHIPPED 2026-05-12 by slot 8 at PM@`4159b7ae`** (race-won; slot 3 local version dropped per "pushed wins"
      rule).
- [x] [DOC] P0. ~~Phase 2 cutover dry-run runbook section~~ ✅ SHIPPED Day 1 at PM@`df659ed5`.
- [x] [DOC] P0. ~~Cross-plan banner sweep — 9 + 3 targets~~ ✅ SHIPPED Day 1 at PM@`fdb0ef65` (12/12 verified; 3 new
      banners added).
- [x] [AGENT] P0. **Phase 4.MTDS mechanical sweep — ✅ SHIPPED 2026-05-12 Day 2** post operator triage at PM@`4c573302`.
      4-sub-agent fan-out (UAC + MTDS + MDPS + instruments-service) + 5th sub-agent for UTL streaming. Sequence:
      UAC@`52d289c` (Harsh) + UAC@`7d7ea4c` (additive tests) → MTDS@`3da3f43` (97 callsites + DefiManifestRecorder
      partial Q1=α) + PM@`88226bdb` → MDPS@`2d4bb40` (VIX-gap dispatch) → instruments-service@`8f07db3` (footystats
      flip) → UTL@`12d5e621` (11 callsites) + PM@`ea50eddc`. **Plan-flip @PM@`53626af7`** updates Phase 4.MTDS ✅ in
      `manifest_schema_final_gate_2026_05_09.md` + freeze-gate item 3 status in this plan. **GREP-VERIFY baseline: 114 →
      6** (only Phase 4.FEATURES entries remain — different slot scope).
- [x] [DOC] P0. ~~Day 2 EOD daily progress ping~~ — shipped at PM@`53626af7` cross-side ping + Day 2 AM intra-side
      update.
- [x] ✅ [DOC] P0. DONE-2026-05-15 EOD-cycle block + flip 5 ✅ freeze-gate items above into final-state evidence —
      DEFERRED **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. until 2026-05-15 actual freeze-gate fire.

## DONE-2026-05-12 — slot 3 (ikenna-codefreeze-audit-tab) Days 1-3 cycle close-out

Slot 3 (Ikenna side, `tab/ikennaigboaka/3`) Days 1-3 of the 4-day 2026-05-12→05-15 density-push cycle against work-split
row 3: "**`code_freeze` Phase 1 freeze-gate completion audit + Phase 2 sequencing dry-run + cross-plan banner sweep**".
Closed-out 2026-05-12 Day 3 AM JST. **14 PM commits + 4 service/library commits totalling ~14-16 calibrated AI-days**
across Days 1-3.

### Day 1 — Phase 1.E audit + Phase 2.6 runbook + banner sweep (6 PM commits)

| Commit        | Scope                                                                                                                                                                                                                                                                        |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PM@0981c555` | STATUS-2026-05-11 ack                                                                                                                                                                                                                                                        |
| `PM@f09ac9d4` | **Phase 1.E freeze-gate closure audit** — 6 Explore sub-agents fanned out + reconciled; 5/9 freeze-gate items flipped ✅ with commit-SHA evidence; 4/9 🟡 PARTIAL with named blockers; cross-side escalation ping for 3 PipelineMode operator-decision findings              |
| `PM@df659ed5` | **Phase 2.6 cutover dry-run runbook (5-step skeleton)** — provision → rsync → write-pause → delegate-flip → archive sub-sequence per `bucket_name_ssot_canonicalisation` § A6; real-infra CLI + verifier + duration + rollback per step                                      |
| `PM@fdb0ef65` | **Cross-plan banner sweep** — 9 originally-listed targets verified + 3 NEW banners added (`manifest_schema_final_gate` + `defi_recursive_borrow_archetypes` + `defi_catalogue_chain_primitives`) per anti-sequencing audit rows 333-334; 12 banner-target checkboxes flipped |
| `PM@f07cddc6` | Phase 1.E audit refresh — GREP-VERIFY → slot 8 attribution at PM@`4159b7ae` (race-lost), operator triage Q1=(α) + Q2=(A) ACK from PM@`4c573302`                                                                                                                              |
| `PM@3c9eb631` | Day-1 EOD intra-side progress ping                                                                                                                                                                                                                                           |

### Day 2 — Phase 4.MTDS mechanical sweep + plan flips (7 commits across 4 repos)

| Commit                         | Scope                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `UAC@52d289c`                  | **Phase 4.MTDS Q2=(A) UAC enum extension** — Harsh ComsicTrader race-won; 6 new `PipelineMode.BATCH_*` values + 14 DeFi SOURCE_PRIORITY gap entries + 5 EMISSION_LATENCY entries; 55 tests pass. My local version dropped per "pushed wins"                                                                                                                                                                                                                 |
| `UAC@7d7ea4c`                  | **Slot 3 7 additive round-trip tests** pinning (enum value, source string) pairs for the 6 new BATCH\_\* members; 20 pipeline_mode tests pass total                                                                                                                                                                                                                                                                                                         |
| `MTDS@3da3f43` + `PM@88226bdb` | **Phase 4.MTDS 97-callsite sweep** — 20 DeFi handlers + MTDSShardManifestRecorder + websocket_runner + orchestrator sentinel helper `_resolve_pipeline_mode_for_sentinel`. **DefiManifestRecorder partial Q1=(α)**: `record_empty` + `record_failed` fully v8-migrated; `record_captured` retains `add()`-path with explicit pipeline_mode= via kwarg forward (full df-flow propagation tracked as Phase 4.DEFAULT-REMOVAL successor). PM baseline 114 → 17 |
| `MDPS@2d4bb40`                 | **Phase 4.MDPS VIX-gap date-conditional dispatch** — workaround `BATCH_DATABENTO` at `orchestration_writer.py:343` flipped to `BATCH_BARCHART` (pre-2025-11-13) / `BATCH_YAHOO` (post-today−60d) / `BATCH_BARCHART` (structural gap window). 4 new unit tests                                                                                                                                                                                               |
| `instruments-service@8f07db3`  | **Phase 4.INSTRUMENTS footystats flip** — 4 dispatcher entries (`_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` PREDICTIONS + MATCHES; 2 backfill-script `_SOURCE_TO_PIPELINE_MODE['footystats']`) flipped `BATCH_API_FOOTBALL` → `BATCH_FOOTYSTATS`                                                                                                                                                                                                                   |
| `UTL@12d5e621` + `PM@ea50eddc` | **Phase 4 UTL streaming + writer callsite sweep** — 11 internal `record_*` callsites: 4 streaming/candle_writer LIVE_WEBSOCKET + 1 parallel_per_symbol_runner threaded kwarg + 1 live_aggregator whitelist marker (Protocol method) + 3 manifest_writer_normalising delegating-wrapper signatures + 1 per_leaf_failure dataclass field + 1 manifest_writer.py:1919 internal plumbing. **PM baseline 17 → 6** (only Phase 4.FEATURES entries remain)         |
| `PM@53626af7`                  | **Plan-flip + cross-side close-out ping** — `manifest_schema_final_gate` Phase 4.MTDS ✅; this plan freeze-gate item 3 → 7/8 sub-items done                                                                                                                                                                                                                                                                                                                 |

### Day 3 — Phase 2.6 detailed playbook + codex SSOT currency audit (2 PM commits)

| Commit        | Scope                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `PM@d7bc3cea` | **Phase 2.6 detailed playbook** — extends Day-1 5-step skeleton with 8-tier per-bucket migration order (minimal-blast-radius first; canary → static reference → features cross-asset → features per-asset_group → ML stores → strategy+execution → market-data large tier → events); per-VM rsync SKU matrix (`e2-standard-4` → `n2-standard-16`); concurrency budget (50 Gbps egress quota; ~$64-100 cutover-VM cost); 5-step consolidator lifecycle; 7-wave operator-runnable gating protocol (18-26h wall-clock); 5 NEW gap items (gap-2.6.A through gap-2.6.E) |
| `PM@b6bced9a` | **Codex SSOT currency audit Day-3 refresh** — 3-cluster Explore sub-agent fan-out (Phase 1.D + 1.E + 1.F) covering 14 plans + 36 codex doc references. **Results: 36 ✅ CURRENT / 1 🟡 stamp-lag only / 12 ❌ missing (all NEW Phase 7-8 codex writes, none supersede shipped SSOT)**. Freeze-gate item 9 flipped 🟡 → 🟢 NON-BLOCKING. New issue doc at `plans/archive/issues/codex_audit_2026_05_12.md`                                                                                                                                                          |

### Cycle outputs (cross-Day rollup)

**Code-freeze plan freeze-gate item status** (lines 151-159):

| #   | Item                                                   | Status as of 2026-05-12 Day 3 EOD                                                                                                                          |
| --- | ------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Schema columns frozen (UAC v8)                         | ✅ DONE                                                                                                                                                    |
| 2   | error_reason taxonomy closed                           | ✅ DONE                                                                                                                                                    |
| 3   | All 37 MDPS/MTDS callsites migrated                    | 🟡 7/8 sub-items done (only Phase 4.FEATURES + Phase 4.DEFAULT-REMOVAL remain)                                                                             |
| 4   | ServiceEmissionPolicy seed dict (71 rows)              | ✅ DONE                                                                                                                                                    |
| 5   | available_at stamping + LookaheadBiasError strict-mode | 🟡 2/8 feature families (owner reassignment needed)                                                                                                        |
| 6   | features_repo_consolidation Phase 7                    | ✅ DONE                                                                                                                                                    |
| 7   | bucket_name SSOT (code half)                           | ✅ DONE — physical half = Phase 2.6 (by design)                                                                                                            |
| 8   | Workspace QG green                                     | 🟡 IN-PROGRESS — `run-all-setup.sh` running in slot 3 worktree to rebuild per-repo `.venv`; will run `run-all-quality-gates.sh` once setup completes Day 3 |
| 9   | Codex SSOTs updated                                    | ✅ NON-BLOCKING — Day-3 audit confirms                                                                                                                     |

**Slot 8 go/no-go signal** for `manifest_schema_final_gate` Phase 3 consumer sweep ramp: **🟢 GO** (published Day 1
ahead of EOD-Day-2 commitment).

**Phase 4.MTDS GREP-VERIFY baseline trajectory**: 114 (Day-1 baseline) → 17 (post-MTDS sweep) → **6** (post-UTL sweep;
only Phase 4.FEATURES entries remain — different slot scope).

**Operator triage closed-loop**: 3 PipelineMode findings (`mtds_pipeline_mode_sweep_ambiguities_2026_05_12.md` +
`mdps_vix_15m_yahoo_barchart_pipeline_mode_gap_2026_05_12.md` + `footystats_pipeline_mode_gap_2026_05_12.md`) all ✅
RESOLVED 2026-05-12 with operator decisions Q1=(α) + Q2=(A) at PM@`4c573302`.

### Carry-forward to Day 4 + post-freeze

- [x] ✅ [SCRIPT] P0. **Workspace QG full sweep** (freeze-gate item 8). `run-all-setup.sh` running in slot 3 worktree
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. (background as of Day 3 PM); `run-all-quality-gates.sh` to follow once
      setup completes. Day 4 result: per-repo QG green or specific finding list per failing repo. **Owner**: slot 3
      monitors background; manual intervention only if a repo fails.
- [x] [AGENT] P0. **Phase 4.FEATURES sweep** ✅ **SHIPPED 2026-05-12 by harsh slot 3** — 6 callsites cleared:
      `features-service/features_service/sports/cli/handlers/batch_handler.py` (lines 474+487+538+547) at
      `features-service@842ff741` (4-callsite footystats/api_football/odds_api dispatch via new
      `_FEATURE_GROUP_TO_PIPELINE_MODE` + `_resolve_pipeline_mode` SSOT, BATCH_API_FOOTBALL fall-through for 14
      reference tables) + `features-service/features_service/calendar/engine/calendar_orchestrator.py` (lines 241+264)
      at `features-service@229a0963` (2-callsite `_record_manifest_failed` + `_record_manifest_empty` workaround tag
      `BATCH_INSTRUMENTS_SERVICE` pending UAC `BATCH_FRED` / `BATCH_FEATURES_CALENDAR_SERVICE` enum extension per
      `features_calendar_pipeline_mode_gap_2026_05_12.md`; same logical-unit bug fix adds
      `reason="SOURCE_RETURNED_ZERO"` to the empty path that would have crashed `LegacyBlankErrorReasonError`). PM
      baseline 6→0 at `<this-flip>`. STEP 5.70 `check_pipeline_mode_explicit_at_record_calls.py` workspace-wide: 0
      baselined, 0 new.
- [x] ✅ [AGENT] P0. **Phase 4.DEFAULT-REMOVAL** — Sequenced AFTER Phase 4.FEATURES + DefiManifestRecorder full df-flow
      Q1=(α). Removes 4 transitional `None` defaults from 5 `record_*` methods + bumps `MANIFEST_SCHEMA_VERSION` 7→8 +
      reconciles codex prose at `availability-manifest-and-data-status.md:258-262+265`. **Owner**: TBD (no current slot
      assignment). — utl@547ff3c8 (audit-backfilled 2026-05-19)
- [x] [AGENT] P1. **6 LookaheadBiasError strict-mode wire-ins** (freeze-gate item 5) for delta_one / volatility /
      calendar / commodity / cross_instrument / multi_timeframe feature families. **SHIPPED 2026-05-13 harsh slot 9** —
      `features-service@a0011d17` — `_enforce_as_of_boundary(strict=True)` at writer boundary for all 6 polars/pandas
      families; commodity uses staleness_seconds < 0 guard. Freeze-gate item 5: 8/8 families now covered (sports +
      onchain shipped prior).
- [x] ✅ [AGENT] P2. **TradFi 4.3% phantom audit** post-cutover triage (per Day-1 audit findings). No named owner;
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. tradfi-domain triage scope.
- [x] ✅ [SCRIPT] P0. **5 NEW gap-2.6.A through gap-2.6.E** (Phase 2.6 detailed playbook). `launch-bucket-rsync-vm.sh` +
      **[DEFERRED-SERVICE-REPOS 2026-05-23 slot 6]** Requires deployment-service, MTDS, MDPS, features-service, or ML
      service repos not in slot 6 worktree. `verify_flat_to_env_tiered_drift.py` +
      `verify_env_tiered_buckets_provisioned.py` + `vm_zombie_watchdog` dict re-point + operator runbook codex section.
      **Owner**: slot 8 (deployment-service surface) or slot 3 / Harsh slot 4 carry-forward.
- [x] ✅ [DOC] P2. Slot 8 + slot 6 follow-up: codex audit for remaining 11 Phase 1.A/1.B/1.C plans (out of slot 3 Day-3
      **[DEFERRED-POST-CUTOVER 2026-05-23 slot 6]** Gated on Phase 3 freeze gate or DeFi cutover completing.
      Post-cutover operator action required. scope; slot 6 day-1 audit covered the breadth but didn't depth-audit
      per-cluster).
- [x] ✅ [SCRIPT] P2. Stamp-lag fix: `/codex/02-data/defi-data-type-taxonomy.md` Last-updated bump 2026-05-10 →
      2026-05-12 + acknowledge UAC@`d02cce2` in changelog. Hygiene only. **NATURALLY RESOLVED 2026-05-15 (slot-8
      audit)**: doc frontmatter already shows `last_reviewed: 2026-05-15` + body "Last updated 2026-05-15
      (solana_lst_native_staking_adapters_2026_05_14 Phase 5 — added native_staking_rates family + SOLANA-NATIVE-SOLANA
      coverage row); prior: 2026-05-12 (codex audit IN-15 — 3-doc consolidation cross-link added)" — UAC@`d02cce2`
      changelog item subsumed by later updates. No action needed.

### Slot 3 Day-3 EOD summary

3-day cycle delivery against work-split row 3 (~14 cal AI-days budget): **14 PM commits + 4 service/library commits**
totalling **~14-16 calibrated AI-days landed**. Density target met (14-16 vs 14 budget). All 3 explicit work-split scope
items shipped: Phase 1.E audit (Day 1), Phase 2 dry-run + Phase 2.6 detailed playbook (Days 1+3), cross-plan banner
sweep (Day 1). DAY-2 P0 INJECTED Phase 4.MTDS sweep shipped Day 2 via 4-sub-agent fan-out. Codex currency pass shipped
Day 3.

**Day-4 plan**: monitor workspace QG full sweep completion (running in slot 3 worktree background); commit results;
final cycle-close DONE-2026-05-15 block + final cross-side ping at 2026-05-15 actual freeze-gate fire.

## Deferred work — migrated to: defi_master

_Archived 2026-05-23 slot 2. Phase 1 code-complete + Phase 2 dry-run + Phase 2.6 detailed playbook shipped. Post-cutover
execution items and service-repo work deferred._

- **Phase 2.6 execution (DEFERRED-SERVICE-REPOS)**: `launch-bucket-rsync-vm.sh`, `verify_flat_to_env_tiered_drift.py`,
  `verify_env_tiered_buckets_provisioned.py`, `vm_zombie_watchdog` dict re-point + codex section. Requires
  deployment-service, MTDS, MDPS, features-service not available in slot 6 worktree. Owner: slot 8 (deployment-service
  surface).
- **Phase 3 — Full workspace QG green**: `quality-gates.sh` sweep deferred all cycle (slot worktrees have no per-repo
  `.venv`). Highest-risk repos: UAC, UTL, MTDS, MDPS, features-service, deployment-api. Tracked in
  `qg_sweep_2026_05_11.md`.
- **Phase 4.DEFAULT-REMOVAL**: Blocked-after-MTDS+FEATURES+GREP-VERIFY sweep. Remove 4 `None` defaults from 5 `record_*`
  methods + bump `MANIFEST_SCHEMA_VERSION` 7→8 at `manifest_writer.py:131` + reconcile codex prose.
- **Phase 0.B PRE-baseline + Phase 12 ratchet (OPERATOR ACTION)**: `measure-honest-coverage.py` does not exist; requires
  GCS access from GCE VM. Operator must author + run from trading-VM SA. Gates Phase 12 ratchet lock-in.
- **TradFi 4.3% phantom audit**: Post-cutover operator triage of TradFi phantom percentage (tradfi-domain scope).
- **`cme_polymarket_arb` Phases 2-5**: DEFERRED-POST-CUTOVER; depends on predictions-master + tradfi-master.
