---
title: Code-freeze → migrate → backfill sequencing master (May-23 cutover orchestration umbrella)
type: orchestration-umbrella
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: cutover-bounded
locked_by: live-defi-rollout
locked_since: 2026-05-10
companion_to:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/manifest_evolution_master_2026_05_08.md
  - plans/epics/manifest_migration_master_2026_05_07.md
  - plans/active/available_at_lookahead_bias_completion_2026_05_08.md
---

# Code-freeze → migrate → backfill sequencing master

## Why this plan exists

Operator framing 2026-05-10: _"Imagine before doing any manifest, migration or cloud schema migrations or data migrations on physical files we first wanna get all the code in services and the UAC and UTL work done so that we won't have to migrate again later. Can we prioritise plan items which get us there so that after that's all done we can migrate manifest and gcs and then after that we can resume backfills for instruments up until features service for everything."_

This plan is the **execution-sequencing umbrella** for the May-23 cutover. It does NOT duplicate scope from existing plans — it indexes them, sequences them into a strict three-phase model, and closes the gaps the audit surfaced. The durable readiness model lives in
[`plans/active/master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md); the schema/writer/data-layout co-evolution gates live in
[`plans/epics/manifest_evolution_master_2026_05_08.md`](../epics/manifest_evolution_master_2026_05_08.md); the migration coordinator lives in
[`plans/epics/manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md). This plan composes them along the time axis.

The principle: **code shape decisions → migration → backfill, in that order, no doubling back.** Every migration of physical files (manifest schema bump, GCS hive-vocab rekey, OHLCV legacy filename → per-instrument rename, pipeline_mode partition addition, AWS cloud-parity bundle) is **one-shot**. If a code-shape decision lands AFTER a physical migration runs, the workspace pays the re-migration tax — millions of parquets walked twice, manifest rewritten twice, backfill VMs idle waiting, May-23 deadline at risk.

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

Each phase has a **freeze gate**: nothing in phase N+1 starts until phase N is operationally complete (not just code-shipped). Per CLAUDE.md HARD RULE _"Plans Run To Actual Completion, Not Smoke-Test Green"_, "shipped" means data on real infrastructure with verification probes, not just a green QG.

## Phase 1 — Code-complete inventory

Plans in this section MUST run to ✅ shipped before Phase 2 starts. The umbrella enforcer is
[`plans/epics/manifest_evolution_master_2026_05_08.md`](../epics/manifest_evolution_master_2026_05_08.md) gates **G1 (reason taxonomy) → G2 (cluster validation) → G3 (enumerator launch)**; this section indexes the plans those gates consume.

### Phase 1.A — UAC + UTL foundation (writegate / honest coverage)

- [ ] [PLAN] P0. **`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`** — UTL `ManifestWriter.record_captured()` 4-pillar gate signature, typed-error taxonomy (`EMPTY_CONFIRMED_REASONS`), cluster validation kwargs, ServiceEmissionPolicy seed dict, 37-callsite MDPS/MTDS writer migration. **Status check**: Wave 4 slice (a) shipped (UAC@58c3b61 + UTL@1a7e1d4b + PM@0e2eb08e); slice (b) Phase 5.1-5.7 (~2d MDPS ohlcv_1h POC + manifest_completeness helper + UAC manifest schema columns + deployment-api/ui surface) PLANNED 2026-05-08; slice (c) Phase 6.1-6.9 (~3-5wk per-service rollout) PLANNED. **Phase 1 blocker**: slice (b) MUST land before Phase 2.1 manifest schema bump can rename/freeze.
- [ ] [PLAN] P0. **`plans/active/wave3x_residual_ssots_2026_05_08.md`** — 5 parallel tracks for residual UAC SSOTs. Track A (HALF_DAY_SESSIONS + VENUE_SESSION_HOURS) shipped UAC@bdc84ed. Tracks B/C/D/E open (sports per-source SSOTs / reconcilers / zero-activity-bar audit / sports availability stamping cascade).
- [ ] [PLAN] P0. **`plans/active/available_at_lookahead_bias_completion_2026_05_08.md`** — Sister umbrella for stamping work. Per-source `available_at` semantics + UTL `stamp_available_at_*` helpers + LookaheadBiasError gate strict-mode rollout across every features-* calculator. **Phase 1 blocker**: every per-source stamping helper must be final before Phase 3 backfills emit their first new row (otherwise re-stamping at Phase 3 = re-write of Phase 2 migrated parquets).
- [ ] [PLAN] P1. **`plans/active/expected_universe_v2_design_2026_05_08.md`** — Per-instrument-grain enumerator (v2 supersedes v1 venue-grain). DRAFT. Pre-populates `expected_unattempted` rows from instruments-service catalogue. Gate G3 of `manifest_evolution_master`. May be deferred behind Phase 2.1 v7 schema bump per audit Q3.

### Phase 1.B — Schema + writer hardening

- [ ] [PLAN] P0. **`plans/active/hard_schema_enforcement_2026_05_08.md`** — Workspace-wide hard schema enforcement at write boundary; flips required fields nullable→required across asset_groups (base_currency / quote_currency / chain_id / contract_address / decimals / fixture_id / futures_expiry). **Sequenced AFTER** `tradfi_master` Q1+Q2 futures-expiry ships (avoids mass-fail-during-transit per existing plan body). **Phase 1 blocker**: SCHEMA_VALIDATION_FAILED enum extension lands here; needed before Phase 2.5 cross-asset rescan can flip rows.
- [ ] [PLAN] P0. **`plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`** — Collapse 3-layer drift (yaml + per-family config.py + UTL resolver) to one canonical SSOT (yaml = canonical per slot 4 decision 2026-05-11). **OPERATOR DECISION 2026-05-11 (Ikenna): option (b) — provision env-tiered buckets to match yaml + migrate flat-bucket data into them.** Phase 1 (this section) covers: Phase 0a (operator decision recorded ✅), Phase 0b (yaml additive corrections — missing `prediction`/`sports` keys, GCP `features-calendar` uncomment, canonical `-test-` variant), L2 config.py migration (resolver-call repointing), legacy `get_bucket_name` delegate, QG STEP 5.69 design. Phase 0c (provision ~180-300 new env-tiered buckets on GCP + AWS via Terraform / `setup-buckets.sh`) + Phase 0d (flat→tiered data migration with ≤0.01% drift verification + write-pause cutover) move to **Phase 2.4 sub-steps below** (window 2026-05-15→05-19). **Phase 1 blocker**: bucket-name resolution code + yaml additive corrections must be final before Phase 2.4 provisioning + data migration starts.

### Phase 1.C — Live-pipeline activation code

- [ ] [PLAN] P0. **`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`** — Live (websocket-streaming) pipeline activation for MTDS → MDPS → features-service across 5 asset_groups. NEW UAC `ServiceEmissionPolicy` schema column, `pipeline_mode` hive partition, `PipelineMode` facade. Health-API extension + circuit-breaker wiring. Instrument-cache-delta hot-reload. Replay subsystem. **Tab 2 PM/evening 2026-05-08 progress**: 4 UTL primitives shipped (streaming facade / StreamingHealthSnapshot / InstrumentLifecycleCacheDeltaReloader / batch_live_reconciler); MTDS/MDPS/features service-wiring deferred post-features-consolidation. **Phase 1 blocker**: Phase 0-3 (UAC + UTL foundations) done; Phase 4-5 (per-asset-group cascade) requires features_repo_consolidation Phase 7.
- [ ] [PLAN] P0. **`plans/active/features_repo_consolidation_2026_05_08.md`** — Merge 8 separate features-* repos into single features-service with sub-packages. NEW UAC `feature_family` schema column. Lift 4 cross-family helpers into UTL. **Deadline 2026-05-13**. **Phase 1 blocker**: Phase 7 (consolidated features-service deployable) must land before live-pipeline Phase 4-5 can wire MDPS↔features in-process handoff. Backfill-side: Phase 3.4 features-service compute relaunch in this plan reads from single consolidated repo, not the 8 archived ones.
- [ ] [PLAN] P1. **`plans/active/basefc_validation_flip_2026_05_10.md`** — Mandatory `ClassVar` enforcement across 75 feature calculators (paradigm-split rollout). Deadline 2026-05-20.
- [ ] [PLAN] P1. **`plans/active/mdps_streaming_and_backpressure_2026_05_07.md`** — MDPS streaming + backpressure successor (awaits live-pipeline Phase 0-3).
- [ ] [PLAN] P1. **`plans/active/mtds_databento_path_streaming_2026_05_07.md`** — MTDS Databento path-streaming successor.

### Phase 1.D — Service code: alerting / risk / strategy / DART

- [ ] [PLAN] P0. **`plans/active/alerting_service_live_rules_2026_05_07.md`** — Production rule SSOT + thresholds + paging logic for live pipeline. Sub-E codex doc category for ML alerting rules (deferred per Tab 5 EOD-summary 2026-05-08; tracked in
      [`feedback_capture_discoveries_as_plan_todos_immediately.md`](../../) auto-memory).
- [ ] [PLAN] P0. **`plans/active/risk_simulations_limits_alerting_2026_05_10.md`** — Risk rule taxonomy + per-archetype/venue/account/client limits + alerting wire + pre-flight check API. Parent: strategy_and_dart_master.
- [ ] [PLAN] P0. **`plans/active/disaster_recovery_circuit_breakers_2026_05_10.md`** — Disaster recovery + reconciliation + circuit breakers + kill switches (cutover MVP). Parent: master_to_live_defi.
- [ ] [PLAN] P1. **`plans/active/promote_workflow_may23_cli_path_2026_05_10.md`** — Promote workflow May-23 dual-track cutover (CLI primary + minimal UI parallel).
- [ ] [PLAN] P1. **`plans/active/topology_qgroup_gap_closure_2026_05_09.md`** — Topology Q-group GAP closure (18 GAPs + 2 WATCH + 1 ISSUE before May-23).

### Phase 1.E — DeFi-specific code (chain primitives + archetypes)

- [ ] [PLAN] P0. **`plans/active/defi_catalogue_chain_primitives_2026_05_10.md`** — DeFi catalogue + chain primitives (chain genesis dates, protocol launch dates, token metadata). Parent: defi_master.
- [ ] [PLAN] P0. **`plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md`** — ARBITRAGE_PRICE_DISPERSION canonicalisation + strategy-service catalog + tracer + P&L attribution. Parent: defi_master.
- [ ] [PLAN] P0. **`plans/active/defi_recursive_borrow_archetypes_2026_05_10.md`** — Recursive-borrow archetype definitions for carry_staked_basis (Phase 9). PLANNED. Parent: defi_master.
- [ ] [PLAN] P0. **`plans/active/defi_simulation_realism_2026_05_10.md`** — DeFi matching engine extension + risk-modeling enhancements. Parent: defi_master.
- [ ] [PLAN] P0. **`plans/active/cme_polymarket_arb_2026_05_08.md`** — InstrumentType.EVENT_CONTRACT enum + linked_canonical_question_group cross-link + MTDS binary-outcome shard atom + cme_polymarket_event_arb strategy archetype.

### Phase 1.F — Cross-cutting code

- [ ] [PLAN] P0. **`plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md`** — Cross-cutting 6-tab restructure (Deploy / Monitor / Data Status / Builds / Readiness / Config). NEW UAC `LifecycleClass` enum + `EnvironmentTier` enum. Parent: cross_cutting_may_23_2026.epic.
- [ ] [PLAN] P0. **`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`** — Full credential provisioning for May-23 live-DeFi cutover.
- [ ] [PLAN] P0. **`plans/active/wallet_treasury_client_flow_2026_05_10.md`** — Wallet / treasury / client lifecycle MVP.
- [ ] [PLAN] P1. **`plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md`** — Client reporting + PnL attribution MVP.

### Phase 1 freeze gate (✅ to flip Phase 2 startable)

The freeze gate fires when ALL of the following are true. The umbrella `manifest_evolution_master` G2 gate is the technical enforcer; this section is the operator-readable checklist.

- [ ] **Schema columns frozen**: UAC manifest schema for v8 (incl. `service_emission_state`, `pipeline_mode`, `feature_family`) reviewed + merged + tagged. No further column adds. Column declaration is owned by [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) per operator decision 2026-05-11 (resolves codex_audit F3 ambiguity — the final-gate plan is the canonical v8 owner; writegate slice (b)'s Phase 5.2 "UAC manifest schema columns" is SUPERSEDED, slice (b) retains the UTL `manifest_completeness` helper + MDPS POC + deployment-api/ui surfaces).
- [ ] **error_reason taxonomy closed**: `EMPTY_CONFIRMED_REASONS` final set declared in UAC; `LegacyBlankErrorReasonError` rejecting any blank reason at write boundary (already shipped UTL@68b3804a per CLAUDE.md). New reason additions require explicit P0 RFC + this plan re-opens.
- [ ] **All 37 MDPS/MTDS callsites migrated** to `ManifestWriter.record_captured(...) / record_empty(...) / record_failed(...) / record_expected_unattempted(...)`. AST sweep (writegate plan QG STEP 5.64) green workspace-wide.
- [ ] **ServiceEmissionPolicy seed dict locked**: 19+ rows covering MDPS / features / ml-training / ml-inference / strategy / execution / position-balance / risk / instruments / alerting (+ any added during Phase 1).
- [ ] **available_at per-row stamping wired** at every write boundary; LookaheadBiasError strict-mode green at every features-* calculator.
- [ ] **features_repo_consolidation Phase 7** done — single features-service repo deployable; 8 child repos archived.
- [ ] **bucket_name SSOT** — single UAC bucket_config registry; all per-service config.py duplicates deleted.
- [ ] **Workspace QG green** across UAC + UTL + every service repo; basedpyright clean; no `# type: ignore` masking architectural violations.
- [ ] **Codex SSOTs updated** per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE — every doc that the Phase 1 plans should have touched is current.

## Phase 2 — One-shot physical migrations

Plans in this section run AFTER Phase 1 freeze gate. They MUST run to operational completion (not just code-shipped) per CLAUDE.md _"Plans Run To Actual Completion"_ HARD RULE. The umbrella enforcer is `manifest_evolution_master` gate **G4 (v8 schema atomic rename) + G5 (rescan apply-flips)**; the migration coordinator is `manifest_migration_master_2026_05_07`.

### Phase 2.0 — Pre-migration VM drain + state freeze (GAP — to formalize)

**Status: GAP. No active plan owns this today.** Per audit, 37 in-flight backfill VMs (writegate audit 2026-05-07) need a clean drain + state freeze before Phase 2.1 starts. If VMs are still writing during a manifest schema migration, every concurrent CAS write produces drift between writer-version-N and writer-version-N+1 rows — silent data corruption.

**Disposition** (per AskUserQuestion answer 2026-05-10): add as a pre-phase to `plans/epics/manifest_migration_master_2026_05_07.md` Stage 1, NOT a standalone plan.

- [ ] [SCRIPT] P0. **GAP-2.0.A** — Add **Stage 0 pre-drain phase** to
      [`plans/epics/manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md) ahead of Stage 1. Body content:
  1. Inventory every running backfill VM via the per-prefix watchdog
     (`deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` registry — bare `gcloud compute instances list` filtered by prefix).
  2. For each running VM, inspect last STARTED→PROGRESS→STOPPED event in `gs://${PID}-events/events/${service}/${YYYY-MM-DD}/${vm_name}/hour=*/*.jsonl` per CLAUDE.md "No fire-and-forget VM launches" HARD RULE.
  3. Send SIGTERM to each VM's runner via launcher's `--graceful-stop` flag (fall back to gcloud auto-shutdown if launcher lacks the flag).
  4. Wait for STOPPED event with non-empty progress metadata; verify last-written shard finalized (parquet exists at canonical path + manifest row landed in `_index/per_vm/<vm-name>.parquet`).
  5. Run manifest consolidator one final time so all per-VM shards merge into canonical `_index/availability_index.parquet` before schema migration touches it.
  6. Snapshot canonical manifest to `_index/snapshots/pre_migration_2026_05_15.parquet` (read-only audit trail; recoverable in case Phase 2.1 atomic rename fails).
  7. Lock `live-defi-rollout` branch from launching new backfill VMs until Phase 2 completes (operator-enforced; no technical gate).
- [ ] [AGENT] P0. **GAP-2.0.B** — Confirm Stage 0 covers BOTH GCP + AWS VM fleets (per `aws_migration_defi_first_2026_05_07.md` 5 in-flight cross-cloud rsync jobs from 2026-05-08 Tab 4 close-out). AWS-side VM drain has its own watchdog + event-stream surface; same recipe applies.
- [ ] [DOC] P0. **GAP-2.0.C** — Update CLAUDE.md "No fire-and-forget VM launches" HARD RULE with "Pre-migration drain" sub-section pointing at Stage 0.

### Phase 2.1 — Manifest v5/v6/v7 → v8 atomic rename

The v8 schema target + flip semantics live in two existing plans (updated 2026-05-11 per operator decision resolving codex_audit F3 ambiguity):

- **Schema column declaration** — [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) ("One-shot maximalist plan that lands the BEST manifest (v8 with all designed columns) on real GCS infra by 2026-05-23 ... slice b spec landed as part of this plan"). Operator decision 2026-05-11 confirmed this plan is the canonical v8 owner; writegate slice (b)'s Phase 5.2 ("UAC manifest schema columns") is SUPERSEDED + bannered. Writegate slice (b) retains the UTL `manifest_completeness` helper (Phase 5.1) + MDPS `ohlcv_1h` POC (Phase 5.3-5.4) + deployment-api/ui surfaces (Phase 5.5) + codex/CLAUDE.md updates (Phase 5.6).
- **Rescan flip schema + apply-flips execution** — `manifest_cross_asset_rescan_design_2026_05_08.md` (class A mutable / class B immutable / class C triage closed sets, per-asset-group rules, concurrency safety).

The plan items here promote the existing pieces to execution shape:

- [ ] [PLAN] P0. **`plans/active/manifest_cross_asset_rescan_design_2026_05_08.md`** — Cross-asset-group `--apply-flips` reconciler. **Disposition**: promote draft → active execution plan. The plan today has:
  1. **Class A mutable** flips (`capture_status` / `error_reason` / `attempted_at` / `path` reconciled to disk truth).
  2. **Class B immutable** columns the rescan respects but does NOT flip (`pipeline_mode` / `available_at` / `service_emission_state` set at write-time, not by walk).
  3. **Class C triage** disagreements routed to operator review at `gs://{pid}-rescan-triage/{run_id}/triage.jsonl`.
  4. Per-asset-group rules respecting `venue_trading_calendar` / `PROTOCOL_LAUNCH_DATES` / `SOURCE_COVERAGE_START` / market lifecycle.
  5. Phantom audit integration (target: 0 phantoms across 5 asset_groups; baseline 354 from 2026-05-04).
     The plan still needs:
  - Atomic rename procedure: per-VM shard tree → consolidator merges with v8 schema → atomic mv `_index/availability_index_v8.parquet` over `_index/availability_index.parquet` → reader fallback grace period DELETED in same commit per CLAUDE.md "Manifest migration, NOT fallback" rule.
  - Verification probe: read 100 random rows post-rename; assert all v8 columns populated; assert ZERO rows with v5/v6/v7 shape; assert reader-fallback path raises `ManifestSchemaError` on any pre-v8 input.
  - Launcher script (`deployment-service/scripts/vm/launch-cross-asset-rescan-vm.sh`; queued per the existing plan body).
  - `cross_asset_rescan.py` Python (Harsh Tab 4 scope per existing plan body).
- [ ] [PLAN] P0. **`plans/active/manifest_schema_final_gate_2026_05_09.md`** — UAC manifest schema column declaration for v8 (operator decision 2026-05-11; supersedes the prior "writegate slice (b) Phase 5.1" attribution). **Phase 2 entry blocker**: column set must be final before the rescan plan can write rows in v8 shape. The new `EXPECTED_KNOWN_SOURCE_GAP` value for UAC `EmptyConfirmedReason` (operator-approved 2026-05-11 per `wave3x_track_d_findings_2026_05_11.md` TL;DR #2 — covers VIX 15m mid-history gap + sports `KNOWN_COVERAGE_GAPS`) lands in this same Phase 1 window.
- [ ] [PLAN] P1. **`plans/active/expected_universe_v2_design_2026_05_08.md`** — Promote draft to active execution plan if launched in Phase 2 (per audit Q3 sequencing-vs-v8 decision). If deferred behind v8, defer to Phase 3.

### Phase 2.2 — GCS bundled migration: pipeline_mode + category-rekey + drift sweep

- [ ] [PLAN] P0. **`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`** — BUNDLED overnight GCS migration. **CRITICAL CONSTRAINT**: this plan walks every parquet ONCE; it MUST include all Phase 2 GCS-touching changes in the same walk. Bundled changes:
  1. NEW `pipeline_mode={batch_databento, batch_tardis, ..., live_websocket}` hive partition column.
  2. Finish dual-vocab `category=` → `asset_group=` rekey; legacy reader fallback DELETED.
  3. Sweep 5 drift axes from 2026-05-04 phantom-audit (path-prefix / instrument_type casing / schema-4 empty instrument_type / chain-bundle equivalence / hive-vocab `category=`/`asset_group=`).
  4. **NEW (closed gap 2)**: OHLCV legacy filename → per-instrument file rename (see GAP-2.3 below).
- [ ] [SCRIPT] P0. **GAP-2.2.A** — Verify `gcs_migration_bundle_pipeline_mode` Phase 2 enumerates ALL Phase 1 schema columns (must include `service_emission_state` + `feature_family` if Phase 2.1 v7 lands first). Cross-reference with `manifest_cross_asset_rescan_design`. Update `gcs_migration_bundle_pipeline_mode` Phase 2 body if any column missing.
- [ ] [DOC] P1. **GAP-2.2.B** — Update CLAUDE.md "Honest absence vs fake placeholders" HARD RULE with reference to Phase 2.2 single-walk discipline. Reviewers should reject any post-Phase-2 plan that proposes another whole-corpus walk.

### Phase 2.3 — OHLCV legacy filename → per-instrument rename reconcile (GAP)

**Status: GAP. Scattered across `gcs_migration_bundle` Phase 2 + per-service writer plans; no single owner.** Per CLAUDE.md "Honest absence vs fake placeholders" reference incident 2026-05-05 — MDPS reader expected legacy `ticks.parquet` while MTDS evolved to per-instrument `{instrument_id}.parquet`; silent placeholder rows hid the drift for years.

**Disposition** (per AskUserQuestion answer 2026-05-10): add as Phase 2 sub-step inside `gcs_migration_bundle_pipeline_mode_2026_05_08.md` (closest existing plan), NOT a standalone plan. Bundles into the same one-walk migration so manifest only rewrites once.

- [ ] [SCRIPT] P0. **GAP-2.3.A** — Append Phase 2.X "OHLCV legacy filename rename" sub-section to
      [`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`](gcs_migration_bundle_pipeline_mode_2026_05_08.md) Phase 2. Body:
  1. Inventory every parquet path matching legacy `ticks.parquet` under MTDS + MDPS + features-* GCS roots (audit script using existing `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` HTTP-pool-tuned listing pattern).
  2. For each legacy path, rename to per-instrument shape `{instrument_id}.parquet` (extract instrument_id from row data, NOT path heuristic — paths can be misleading per the 2026-05-05 incident).
  3. Update manifest row_keys for renamed files (atomic per-row rewrite via consolidator; safe because Phase 2.1 v7 schema migration runs before this).
  4. Verification: post-rename, ZERO `ticks.parquet` paths exist; manifest row count delta ZERO (rename is path-only, not schema or data); `instrument_id` column populated in every renamed parquet.
- [ ] [SCRIPT] P1. **GAP-2.3.B** — Audit features-* readers for `ticks.parquet` literal path references (the 2026-05-05 silent-placeholder bug had MDPS reader hardcoded to legacy filename); flag any consumer that would break post-rename. Fix sites in same logical unit as Phase 2.3.A.

### Phase 2.4 — AWS DeFi-first cloud-parity migration + env-tiered bucket provisioning + flat→tiered data migration (operator decision (b) 2026-05-11)

- [ ] [PLAN] P0. **`plans/active/aws_migration_defi_first_2026_05_07.md`** — AWS Migration DeFi-First. **Status (per Tab 4 PM@4a3c157d 2026-05-08)**: Phase 1 smoke against real AWS S3 GREEN; Phase 2 10 buckets created on real S3; Phase 5 KICKED OFF (5 cross-cloud rsync jobs at 14:20 UTC 2026-05-08); Glue/Athena Phase 5b ENABLED. Remaining: full bundle backfill + AWS-side manifest consolidator + AWS-side data-status UI.
- [ ] [SCRIPT] P0. **GAP-2.4.A** — Verify `aws_migration_defi_first` migration writes use the same Phase 1.B `bucket_name_ssot_canonicalisation` resolver. If AWS-side resolver was wired pre-Phase-1, double-check the SSOT is in sync now (CLAUDE.md "Two teammates × multiple parallel agents" + bucket-name SSOT triple-drift incident from Tab 4 close-out).
- [ ] [SCRIPT] P0. **GAP-2.4.B (NEW per operator decision (b) 2026-05-11)** — Provision env-tiered buckets to match yaml across **both clouds**, **all envs (staging / prod / development)**, and **all yaml `${DEPLOYMENT_ENV}`-bearing kinds** (features-delta-one × {cefi, tradfi, defi, prediction, sports} × env, features-volatility × {cefi, tradfi, defi, prediction, sports} × env, features-onchain × {cefi, defi, prediction, sports} × env, features-sports × env, features-prediction × env, ml-models-store × env, ml-predictions-store × env, ml-configs-store × env, strategy-store × {cefi, tradfi, defi, prediction} × env, execution-store × {cefi, tradfi, defi, prediction} × env, dex-pools × env, dex-swaps × env, evm-defi × env, eigenlayer-rewards × env). Estimated total: ~180-300 new buckets across both clouds × 3 envs. Implementation: extend `deployment-service/terraform/modules/storage_buckets` (or `setup-buckets.sh`) with the resolver-derived name list; run `gcloud storage buckets create` / `aws s3 mb` per name; verification probe `gcloud storage ls` / `aws s3 ls` per name. Owner: Harsh slot 4 (he provisions, per operator's "assume harsh will provision the buckets" 2026-05-11). bucket_name_ssot plan Phase 0c.
- [ ] [SCRIPT] P0. **GAP-2.4.C (NEW per operator decision (b) 2026-05-11)** — Migrate flat-bucket data into env-tiered buckets (Phase 2 physical migration; data preservation critical). For every existing FLAT bucket on GCP (`features-delta-one-cefi-{pid}`, `features-onchain-{pid}`, `features-sports-{pid}`, `features-volatility-{ag}-{pid}`, `features-calendar-{pid}`, etc.) AND on AWS (existing flat counterparts if any beyond the 10 DeFi buckets created Phase 2 of aws_migration), copy ALL data into the new env-tiered prod bucket via `gcloud storage cp -r --preserve-symlinks` (GCP) / `aws s3 sync` (AWS). Drift verification: post-copy object count + total size + spot-check 100 random parquets per bucket must match within ≤0.01%. **Cutover window**: pause writes to flat buckets during migration (operator-coordinated; ~few hours per asset_group depending on volume). Post-migration: archive (don't delete) flat buckets to `*-archived-flat-2026-05-19/` prefix + 30-day retention; delete after manifest + downstream verification confirms zero readers still hit flat names. bucket_name_ssot plan Phase 0d. **Composes with Phase 2.5 cross-asset rescan**: rescan reads env-tiered buckets, not flat ones; rescan launcher reads from yaml SSOT post-migration so the read-path matches the write-path.
- [ ] [DOC] P0. **GAP-2.4.D (NEW per operator decision (b) 2026-05-11)** — Update reader/writer audit table verifying every consumer post-Phase-0d hits env-tiered bucket names (not flat). bucket_name_ssot plan done-def #6 extension.
- [ ] [SCRIPT] P0. **GAP-2.4.E (NEW per operator extension (b+) 2026-05-11)** — Sync script (prod → staging/dev) with truncated date window + same-region enforcement. New script `deployment-service/scripts/sync-buckets-prod-to-{staging,dev}.sh` + Cloud Scheduler daily cron. Per `(kind, asset_group)` cross-product, copies last `N` years (default `N=2` for staging, `N=1` for dev) of data from prod bucket to staging/dev bucket. Same-region enforced (no cross-region egress). Manifest sync: re-run consolidator on staging/dev post-data-sync so manifest matches truncated window. Verification: post-sync staging/dev row count = (prod row count for `day >= today - N*365`); spot-check 100 random parquets readable. **Ships Phase 1 code-complete; first execution Phase 3 / post-cutover (no urgency pre-2026-05-23 since dev/staging not in active use yet).** bucket_name_ssot plan Phase 0h.
- [ ] [AGENT] P1. **GAP-2.4.F (NEW per operator extension (b+) 2026-05-11; OPERATOR RATIFIED ap-northeast-1 2026-05-11)** — Region-pinning audit + enforcement. **Operator decision (a) ratified ap-northeast-1 (Tokyo) for AWS** — matched-region with GCP `asia-northeast1` (Tokyo). The 10 DeFi buckets shipped 2026-05-08 via `setup-defi-buckets.sh:28` (default `ap-northeast-1`) are already there; ratification is zero-cost. Yaml entries audited for region consistency: **GCP all `asia-northeast1` (Tokyo); AWS all `ap-northeast-1` (Tokyo)** — within-cloud syncing (Phase 0h) is $0; cross-cloud rsync (`aws_migration_defi_first` Phase 5) is same-metro Tokyo (~1ms RTT, ~$0.01-0.02/GB egress vs ~$0.09/GB trans-Pacific = ~5× cheaper). Bucket provisioning (GAP-2.4.B) creates buckets in canonical region; reject any `--location=<other-region>`. **PM stub yaml** `configs/cloud-providers.yaml:59` updated `${AWS_REGION:-us-east-1}` → `${AWS_REGION:-ap-northeast-1}` per operator ratification. bucket_name_ssot plan Phase 0i. See [`plans/active/issues/aws_region_decision_brief_2026_05_11.md`](issues/aws_region_decision_brief_2026_05_11.md) for full trade-off analysis.
- [ ] [SCRIPT] P0. **GAP-2.4.G (NEW per operator extension (b+) 2026-05-11)** — Yaml extends env tier to ALL `${DEPLOYMENT_ENV}`-MISSING bucket kinds (`instruments-store-{ag}-{env}-{pid}`, `market-data-tick-{ag}-{env}-{pid}`, etc. — currently env-less). Confirm with operator which buckets stay env-less (`terraform-state` likely; `secrets` definitely). Composes with `pipeline_mode={batch_databento, live_websocket, live_rest}` hive partition INSIDE the bucket (env tier at BUCKET NAME level, pipeline_mode at PATH level — orthogonal). bucket_name_ssot plan Phase 0e. **Phase 1 code-complete scope** (lands BEFORE Phase 0c provisioning).
- [ ] [SCRIPT] P0. **GAP-2.4.H (NEW per operator extension (b+) 2026-05-11)** — VM launcher scripts (~30 under `deployment-service/scripts/vm/`) audit for hardcoded bucket references; ensure each launcher reads `DEPLOYMENT_ENV` (env / CLI flag) and passes to VM via `metadata` so the VM's bucket-resolution lands on the right env-tiered bucket. Add `--env <prod|staging|dev>` CLI flag to each launcher OR centralise via a single helper script. Workspace QG step (companion to STEP 5.69) AST-walks launcher scripts for non-helper bucket references. bucket_name_ssot plan Phase 0f. **Phase 1 code-complete scope**.
- [x] [AGENT] P0. **GAP-2.4.I (NEW per operator extension (b+) 2026-05-11)** — Verify deployment UI env-tier already shipped. ✅ VERIFIED: per `codex/05-infrastructure/deployment-ui-architecture.md` § "Environment tier" — UI env tier resolved from `window.location.hostname` (each env has own domain → own deployment-api Cloud Run → own GCS bucket scope → own service account). Cross-env data leakage impossible. No additional UI work; Phase 0c provisioning lands env-tiered buckets the per-env deployment-api consumes. bucket_name_ssot plan Phase 0g (already shipped pre-2026-05-11).

### Phase 2.5 — Manifest cross-asset rescan with --apply-flips

- [ ] [PLAN] P0. **`plans/active/manifest_cross_asset_rescan_design_2026_05_08.md`** (continuation from Phase 2.1) — Run `--apply-flips` against full migrated manifest. This is Phase 5 of `manifest_migration_master`. Catches:
  - 1440-NaN flip (any MDPS empty-placeholder rows → `attempted_failed` with `MalformedTickFieldError`).
  - Partial-bundle reflip (any cluster-coverage-violated bundles → `attempted_failed` with `ClusterCoverageError`).
  - Pre-v7 cleanup (any straggler rows in pre-v7 shape → `attempted_failed` with `SCHEMA_VALIDATION_FAILED`).
  - GCS available_at backfill (rows with NULL `available_at` get stamped via `stamp_available_at_*` based on per-source semantics from Phase 1).

### Phase 2 freeze gate (✅ to flip Phase 3 startable)

- [ ] **Manifest schema is v8** workspace-wide; every row populated; reader fallback for v5/v6/v7 deleted; ZERO drift in 4-state taxonomy at every coverage drilldown level.
- [ ] **GCS bundled migration complete**: `pipeline_mode` partition added; `category=` rekey done; 5 drift axes swept; OHLCV legacy filenames renamed; ZERO regressions on a 100-shard random read sample.
- [ ] **AWS cross-cloud parity**: every DeFi-relevant bucket has S3 mirror; Glue catalog crawled; Athena query returns expected rows on `paper-vs-live` smoke.
- [ ] **`--apply-flips` rescan complete**: every shard with drift state flipped to correct manifest state; verification probe (random 100 shards) shows manifest matches on-disk truth.
- [ ] **Manifest snapshot saved** at `_index/snapshots/post_migration_2026_05_19.parquet` (recovery point before Phase 3 backfill writes start).
- [ ] **No backfill VMs launched** during Phase 2 window. (Operator-enforced lock.)

## Phase 3 — Resume backfills end-to-end

Plans in this section run AFTER Phase 2 freeze gate. They are the actual data-population step against final-state code + final-state schema + final-state on-disk layout. The umbrella enforcer is `master_to_live_defi_2026_05_23` Group D (Coverage & shard) + Group F (Trading prerequisites — live-only).

### Phase 3.1 — Instruments-service catalogue forward-fill

- [ ] [PLAN] P0. **`plans/epics/instruments_live_master_2026_05_08.md`** — Instruments-service live activation across 5 asset_groups. Per-asset-group cadence: TradFi 15-min Polygon/Yahoo, CeFi 15-min CCXT, Sports trigger-driven (daily fixture re-poll + season-roll + transfer-window + weather), Predictions 15-min market-discovery. Cloud Scheduler driver + new "Scheduled Jobs" deployment-UI tab. **Phase 3 entry**: Phase F (live activation) starts after Phase 2 freeze; until then stays in Phase A-E (preflight DAG).

### Phase 3.2 — MTDS multi-venue backfill VM relaunch

- [ ] [SCRIPT] P0. **MTDS-3.2.A** — Relaunch CeFi backfill VMs (15 venues — Bybit / Binance / OKX / Bitfinex / Bitget / Kraken / Deribit / Hyperliquid / Aster + others per `cefi_master_2026_05_07` Phase 1A). Per-VM shard isolation enforced (`MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`). Watch event-stream per CLAUDE.md "No fire-and-forget VM launches" HARD RULE.
- [ ] [SCRIPT] P0. **MTDS-3.2.B** — Relaunch TradFi backfill VMs (Databento — ES.OPT 11-cluster + futures-chains + ETFs per `tradfi_master_2026_05_07` Phase 1).
- [ ] [SCRIPT] P0. **MTDS-3.2.C** — Relaunch DeFi backfill VMs (Pyth Solana + Chainlink EVM oracle prices + DEX-perp forward-poll Hyperliquid/Aster + Lighter/Pacifica/Extended replay per `defi_master_2026_05_07` Phase 9).
- [ ] [SCRIPT] P0. **MTDS-3.2.D** — Relaunch Sports backfill VMs (af / fs / sfi / us per `sports_master_2026_05_07` Phase 1; OPERATOR-GATED pending Stage 1 sports rename completion in Phase 1.D).
- [ ] [SCRIPT] P0. **MTDS-3.2.E** — Relaunch Predictions backfill VMs (Polymarket + Kalshi per `predictions_master_2026_05_07` Phase 1; canonical_question_group rekey already in Phase 2.2).

### Phase 3.3 — MDPS bar reprocessor relaunch

- [ ] [SCRIPT] P0. **MDPS-3.3.A** — Relaunch MDPS reprocessors per asset_group, reading from migrated MTDS shards. Use Phase 1.C live-pipeline in-process MDPS↔features handoff if features-repo-consolidation Phase 7 done; else fall back to standalone MDPS VMs.
- [ ] [SCRIPT] P0. **MDPS-3.3.B** — Verify zero 1440-NaN-bar regressions via post-launch sampling (10 random instrument-days; assert OHLC populated OR catalog says instrument-not-listed; per CLAUDE.md "Honest absence vs fake placeholders" rule).

### Phase 3.4 — Features-service compute relaunch

- [ ] [SCRIPT] P0. **FEAT-3.4.A** — Relaunch consolidated features-service compute (single repo per Phase 1.C consolidation). All 5 asset_groups + cross-instrument calculators. LookaheadBiasError strict-mode green.
- [ ] [SCRIPT] P0. **FEAT-3.4.B** — Verify per-feature-family output shapes match Phase 1.C schema declarations; post-launch sampling 100 random feature rows per family.

### Phase 3.5 — ML training + inference relaunch

- [ ] [PLAN] P0. **`plans/epics/ml_and_features_master_2026_05_07.md`** Phase 1A-2E — UAC feature-DAG SSOT + features-service writers + pre-join consolidation. **Critical path subset only**; Phase 4 (ML model lifecycle) is mostly post-May-23.
- [ ] [SCRIPT] P0. **ML-3.5.A** — Relaunch ml-training jobs against migrated features. Sanity replay on 3 representative shards per `ml_and_features_master` Phase 5.
- [ ] [SCRIPT] P0. **ML-3.5.B** — Relaunch ml-inference for live-pipeline serving. Tier-up alerting per `alerting_service_live_rules_2026_05_07`.

### Phase 3.6 — Strategy archetype paper-trade smoke

- [ ] [PLAN] P0. **`plans/active/defi_master_2026_05_07.md`** Phase 9-10 — DeFi 2 archetypes paper-trade smoke (carry_staked_basis + ARBITRAGE_PRICE_DISPERSION).
- [ ] [PLAN] P0. **`plans/epics/strategy_and_dart_master_2026_05_07.md`** — Strategy archetype paper-trade smoke for CeFi / TradFi / Sports / Predictions; DART manual-trade UI live for human override.
- [ ] [PLAN] P1. **`plans/active/batch_live_symmetry_2026_05_10.md`** — 8-tab design symmetry (May-23 cutover-blocking subset).

### Phase 3.7 — 7-day continuous live-DeFi run on real wallet

- [ ] [PLAN] P0. **`plans/active/defi_master_2026_05_07.md`** Phase 11+ — 7-day continuous run gate on real wallet. **Final cutover gate per master plan Group F-G live-only items.**

### Phase 3 freeze gate (✅ to declare May-23 cutover ready)

Per CLAUDE.md _"Plans Run To Actual Completion"_, gate fires only when:

- [ ] All 5 asset_group backfills shipped and verified (manifest captured rows match expected; sample parquets show real OHLC, not placeholders).
- [ ] Features-service compute green at every feature_family for every asset_group.
- [ ] ML training shipped; inference serving live with alerting tier-up green.
- [ ] All archetype paper-trade smokes green.
- [ ] DeFi 2 archetypes ≥7 continuous days live on real wallet (final cutover gate).
- [ ] Codex SSOTs reflect final state.

## Anti-sequencing audit (plans that risk forcing re-migration)

Per AskUserQuestion answer 2026-05-10: explicit list of active plans whose work, if shipped after Phase 2 freeze, would force a second migration walk. Each gets an explicit decision: **ship before Phase 2 freeze, or defer post-cutover.**

| Plan                                                                                                                       | Risk shape                                                                                                                                                              | Decision                                                                                                                                              |
| -------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `wave3x_residual_ssots_2026_05_08.md` Track D (zero-activity-bar adapter audit)                                            | If audit finds new shard atom dimension or new error reason needed → manifest schema bump → another Phase 2.1                                                           | **Ship before Phase 2 freeze (Phase 1.A).** Audit must complete; new findings either land in Phase 1 schema or are deferred post-cutover.             |
| `wave3x_residual_ssots_2026_05_08.md` Track E (sports availability_at stamping cascade)                                    | If stamping rules change post-Phase 2.5 → re-stamping requires manifest column rewrite                                                                                  | **Ship before Phase 1 freeze (Phase 1.A).** Folded into `available_at_lookahead_bias_completion`.                                                     |
| `expected_universe_v2_design_2026_05_08.md` (per-instrument-grain enumerator)                                              | v2 changes manifest row count semantics (instrument-grain expected_unattempted rows) → if launched post-Phase-2 needs another consolidator pass                         | **Defer behind Phase 2.1 v7 schema bump per audit Q3.** Either ship in Phase 1.A OR defer post-cutover; do NOT ship between Phase 2.1 and 2.5.        |
| `arbitrage_price_dispersion_finalisation_2026_05_09.md` (canonical group changes)                                          | If new canonical_question_group landed post-Phase-2.2 rekey → second rekey walk                                                                                         | **Ship before Phase 1 freeze (Phase 1.E). ✅ SHIPPED 2026-05-09 per slot 5 audit 2026-05-11**: UAC `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` enum present at `enums.py:68` (no `LEVERAGED_FUNDING_ARB` standalone); Phases A-E shipped per plan body commit ledger (strategy-service@24f8494 dispatcher + @0b4ef0e helper module + @04c0d52 engine 8-step loop + @de9b4b0 multi-pair allocator; pnl-attribution archetype rows shipped; codex circular-ref resolved Phase E). **NO new canonical_question_group introduced; NO new StrategyArchetype enum value.** Anti-sequencing risk = NONE. Two P1 carryover items (canonical BTC/USDT slot entry at archetype_slot_resolver.py + slot_resolver test) — non-blocking for Phase 2 (config additions land at strategy-service, not UAC/manifest). |
| `cme_polymarket_arb_2026_05_08.md` (InstrumentType.EVENT_CONTRACT)                                                         | New InstrumentType enum value affects shard atom keys → manifest column population shape changes                                                                        | **Ship before Phase 1 freeze (Phase 1.E). ✅ Phase 1 SHIPPED uac@b95d146 per slot 5 audit 2026-05-11**: `InstrumentType.EVENT_CONTRACT` present at `_instrument_enums.py:54` + `INSTRUMENT_TYPES_BY_VENUE[CME]` (venue_constants.py:358) + `INSTRUMENT_TYPE_FOLDER_MAP["EVENT_CONTRACT"] = "event_contracts"` + Databento BAG classifier (`external/databento/normalize.py:69-110`). **Enum value MUST be referenced in v8 schema declaration** ([`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) — canonical v8 owner per operator decision 2026-05-11 commit `39ab61e5`; supersedes prior "writegate slice (b) Phase 5.1" attribution). Phases 2-5 BLOCKED (predictions-master Phase 5 + tradfi-master Q1+Q2) — POST-CUTOVER per plan body, explicitly OUT of May-23 scope. No additional anti-sequencing risk for the post-cutover Phases 2-5 since they don't introduce further enum values into v8 — `linked_canonical_question_group` is a cross-link field, not a new shard atom dimension. |
| `hard_schema_enforcement_2026_05_08.md` (nullable→required flips per asset_group)                                          | If required-field flip lands post-Phase-2 → mass-fail-during-transit; row state transitions retroactively                                                               | **Sequenced AFTER tradfi_master Q1+Q2 futures-expiry per existing plan body, but BEFORE Phase 2.5 cross-asset rescan.** Phase 1.B ownership.          |
| `aws_migration_defi_first_2026_05_07.md` Phase 5 cross-cloud rsync (running 2026-05-08)                                    | If GCP-side schema migrates AFTER AWS rsync runs → AWS S3 has stale-shape parquets diverging from GCP                                                                   | **Ship Phase 5 GCP→S3 rsync AFTER Phase 2.2 GCS bundled migration completes.** Stop in-flight rsync if mid-Phase-2; restart post-2.2.                 |
| `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0c provisioning + Phase 0d data migration (operator decision (b) 2026-05-11) | If env-tier bucket provisioning + flat→tiered data migration lands AFTER Phase 2.5 rescan → rescan rewrites flat-bucket rows that get re-migrated; manifest re-sync needed | **Ship Phase 0c provisioning + Phase 0d data migration as Phase 2.4 sub-steps (GAP-2.4.B + GAP-2.4.C above) BEFORE Phase 2.5 cross-asset rescan.** Rescan reads env-tiered buckets natively post-migration. Operator decision (b) accepts this scope; alternative (a) would have skipped both. |
| `simulation_scenarios_topology_price_shocks_2026_05_09.md`                                                                 | If simulation harness writes simulated parquets to same buckets → could conflict with Phase 2.2 single-walk discipline                                                  | **Confirm simulation outputs go to dedicated `*-sim-*` buckets per `bucket_name_ssot_canonicalisation`.** Otherwise defer simulation runs to Phase 3. |
| `mock_data_pipeline_benchmarking_2026_05_10.md`                                                                            | Same as above (synthetic-data harness writes)                                                                                                                           | **Confirm mock buckets isolated.** Defer benchmarking runs to Phase 3 if not.                                                                         |
| `wave2_polymarket_record_captured_from_counts_2026_05_09.md`                                                               | Wave-2 Polymarket SSOT migration changes how `record_captured` row counts populated for prediction shards → manifest row population shape changes for prediction venues | **Already PLANNED + DEFERRED per current plan body.** Confirm not slipping into Phase 2 window.                                                       |
| `data_status_drilldown_shard_atom_alignment_2026_05_07.md` + `data_status_comprehensive_test_coverage_2026_05_07.md`       | UI work; if drives changes to manifest writer code post-freeze → re-migration                                                                                           | **Ship UI parts before/after Phase 2 freely; any writer-code changes MUST land in Phase 1.**                                                          |
| `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`                                                          | Canonicalisation may add new strategy_id values to manifest — affects shard atom                                                                                        | **Ship before Phase 1 freeze (Phase 1.E).** Stream B mostly shipped via `arbitrage_price_dispersion_finalisation_2026_05_09` (row above). Stream C owns the **8 → 11 StrategyArchetype enum expansion** per `defi_recursive_borrow_archetypes` AD-1 flip 2026-05-10 cross-plan audit Q10 ratification — must ship CARRY_RECURSIVE_BORROW_LENDING_ONLY + CARRY_RECURSIVE_BORROW_PERP_HEDGED + the 3rd-TBD enum value in v8 schema declaration window. Per slot 5 audit 2026-05-11: NEITHER enum value present in UAC `internal/architecture_v2/enums.py:31-118` yet (verified grep). Stream C is Phase 1 critical path. |
| `defi_recursive_borrow_archetypes_2026_05_10.md` (NEW StrategyArchetype enum values per AD-1 flip 2026-05-10)              | New StrategyArchetype enum values (`CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED`) affect manifest `strategy_id` shard atom column         | **Ship before Phase 1 freeze (Phase 1.E) via `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07` Stream C** (most-comprehensive-owner rule per AD-1 flip + cross-plan audit Q10 ratification 2026-05-10). Recursive-borrow plan body Phase 1 transferred to `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1 (UAC SSOT) + Phase 3 (MTDS adapter rewrites + Bug 1/2/3 fixes + production backfill VM); Phase 9 backtest gated on catalogue plan reporting `captured` for Aave V3 Ethereum + Compound V3 Ethereum/Arbitrum/Base SUPPLY_APY/BORROW_APY/UTILISATION across 2022-03-01 → present. Per slot 5 audit 2026-05-11: enum values NOT yet in UAC enum (verified grep `EVENT_CONTRACT\|CARRY_RECURSIVE_BORROW`). Slot 5 → [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) owner handshake (operator decision 2026-05-11 commit `39ab61e5` re-routed v8 schema declaration ownership from writegate slice (b) Phase 5.1 to the final-gate plan). |
| `defi_catalogue_chain_primitives_2026_05_10.md` (NEW data_type enums + 26 protocol entries + chain primitives)             | New `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` / `LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` data_type enums affect manifest `data_type` column population; new 26 protocol entries + `MevSubmissionMode.JITO_BUNDLE` + `LST_TOKEN_TO_PROTOCOL_ASSET` SSOT + `PERP_MARGIN_TIERS` table; new bundled data_types affect `BUNDLED_DATA_TYPES` cluster validation registry | **Ship Phase 1 (UAC SSOT extensions) BEFORE Phase 1 freeze 2026-05-15.** Phase 1 is SEQUENTIAL gate per the catalogue plan's execution DAG — Phases 2-6 (instruments-service + MTDS + connector buildout + chain primitives + backfills) fan out PARALLEL once Phase 1 lands. **Existing UAC state per slot 5 audit 2026-05-11**: `CHAIN_GENESIS_DATES` (chain_env.py:91) covers 22 chains ✅ + `PROTOCOL_LAUNCH_DATES` (chain_env.py:144) covers ~50+ (chain, protocol) entries including Aave V3 multi-chain + Compound V3 + Uniswap V2-V4 + Spark + Lido + Solana protocols ✅. **OPEN per Phase 1A audit**: 26 new venues (Yearn / Convex / Beefy / Pendle / Idle / Balancer / Sushi V2+V3 / PancakeSwap V3 / Camelot V3 / Aerodromeq V3 / Velodrome V2 / TraderJoe V2 / Raydium / Orca / Jupiter / Spark / Radiant / RocketPool / Solblaze / EigenLayer / Symbiotic / Karak / Renzo / KelpDAO / Puffer / Jito-restaking) + Solana Jito MEV + per-venue margin-tier table + dual-prediction module pick (canonical/domain/prediction → canonical/domain/predictions) + LST_TOKEN_TO_PROTOCOL_ASSET SSOT verify. **Lending-indices data_types must land in v8 declaration** ([`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) — canonical v8 owner per operator decision 2026-05-11 commit `39ab61e5`; slot 5 → final-gate owner handshake). |
| `mtds_per_instrument_download_api_2026_04_24.md`                                                                           | Currently flagged "post-May-23"; safe                                                                                                                                   | **Defer post-cutover.** No Phase 2 risk.                                                                                                              |
| `simulation_scenarios_post_cutover_2026_06_01.md` + `fund_administration_service_and_pooled_subscription_redemption_*.md` | Already planned post-cutover                                                                                                                                            | **No risk.**                                                                                                                                          |

**Rule**: any plan touching manifest schema / writer code / GCS path templates / hive-vocab keys / parquet column shapes / shard atom keys / error-reason taxonomy must surface in this audit before Phase 2 freeze. New plans created during Phase 1 must be added to this audit at creation time. Reviewers reject any plan that lands Phase 1.X scope after the freeze gate fires.

## Codex SSOT updates (per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE)

This plan is itself an orchestration umbrella; the codex SSOTs it touches are the cross-cutting ones already listed in CLAUDE.md. Per the hard rule, every Phase boundary in this plan triggers a codex audit pass. Specifically:

- [ ] [DOC] P0. After Phase 1 freeze gate fires: walk every codex doc the Phase 1 plans touch (per their own Codex SSOT update phases). Verify the doc layer reflects the frozen schema state. List per-plan-phase in `unified-trading-pm/codex/` is owned by each consumed plan; this plan does not duplicate.
- [ ] [DOC] P0. After Phase 2 freeze gate fires: update [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md) "v8 schema" section to be the canonical post-migration shape; remove v5/v6/v7 fallback documentation. Update [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md) reason taxonomy section to closed-set state. Update [`codex/05-infrastructure/vm-tarball-deployment.md`](../../codex/05-infrastructure/vm-tarball-deployment.md) with Phase 3 backfill VM relaunch sequencing. Add new codex stub `codex/02-data/cross-asset-rescan-protocol.md` (also listed in the rescan plan's Codex SSOT updates).
- [ ] [DOC] P0. After Phase 3 freeze gate fires: master plan
      [`plans/active/master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) Group D + F + G readiness columns flip to ✅ green for every asset_group on the cutover critical path.

## Cross-plan coordination banners (per CLAUDE.md HARD RULE)

This plan introduces a workspace-wide sequencing constraint. Per CLAUDE.md "Cross-Plan Coordination Banners" rule, the following plans MUST receive a banner pointing back here in a follow-up commit:

- [ ] [DOC] P0. **`plans/active/master_to_live_defi_2026_05_23.md`** — top-of-file `> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing**` banner pointing here. BE AWARE tag.
- [ ] [DOC] P0. **`plans/epics/manifest_evolution_master_2026_05_08.md`** — same banner. BLOCK tag (Phase 2 cannot start before this plan's Phase 1 freeze gate).
- [ ] [DOC] P0. **`plans/epics/manifest_migration_master_2026_05_07.md`** — same banner. BLOCK tag for Stage 1 onwards (must wait Phase 2.0 pre-drain).
- [ ] [DOC] P0. **`plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`** — banner notes that Phase 2.X (OHLCV rename) and verification of all Phase 1 schema columns are gap-closure work to land in this plan.
- [ ] [DOC] P0. **`plans/active/aws_migration_defi_first_2026_05_07.md`** — banner notes Phase 5 cross-cloud rsync sequencing constraint vs Phase 2.2.
- [ ] [DOC] P1. **`plans/active/writegate_honest_coverage_endtoend_2026_05_06.md`** — banner notes its slice (b) + slice (c) are Phase 1 freeze blockers.
- [ ] [DOC] P1. **`plans/active/features_repo_consolidation_2026_05_08.md`** — banner notes Phase 7 is Phase 1 freeze blocker.
- [ ] [DOC] P1. **`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md`** — banner notes its Phase 4-5 cascade depends on features-repo-consolidation Phase 7 + Phase 2 GCS bundled migration.
- [ ] [DOC] P1. **`plans/active/aws_migration_defi_first_2026_05_07.md`** — banner specifies bucket-name SSOT alignment dependency.

## Done definition

The plan is done when ALL of the following are true:

- ✅ Phase 1 freeze gate fired with verifiable evidence (workspace QG green; AST sweep of `record_captured` callsites green; ServiceEmissionPolicy seed dict locked; bucket_name SSOT consolidated; features-repo Phase 7 archived).
- ✅ Phase 2 freeze gate fired with verifiable evidence (manifest v7 workspace-wide; `pipeline_mode` partition added everywhere; `category=` rekey done; OHLCV legacy filenames renamed; AWS cross-cloud parity green; `--apply-flips` rescan complete).
- ✅ Phase 3 freeze gate fired with verifiable evidence (all 5 asset_group backfills shipped and verified; features-service compute green; ML training + inference live; archetype paper-trade smokes green; DeFi 2 archetypes ≥7 continuous days live on real wallet).
- ✅ All anti-sequencing audit decisions resolved (every plan listed has shipped per its decision OR is explicitly deferred post-cutover).
- ✅ All gap closures landed (GAP-2.0 VM drain + GAP-2.2 / GAP-2.3 / GAP-2.4 sub-step additions to existing plans).
- ✅ All cross-plan coordination banners landed.
- ✅ Codex SSOTs updated per "Post-Plan-Phase Codex Audit" HARD RULE.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE):

- ✅ The May-23 cutover master plan's Group F-G readiness columns are green for every asset_group on the critical path.
  - **What ran**: every Phase 3.X backfill VM fleet to natural shutdown; manifest-verified row counts; sample-inspected parquets per asset_group.
  - **Verification**: `gcloud storage ls gs://${PID}-events/events/.../{YYYY-MM-DD}/...` shows STARTED + progress + STOPPED; `gcloud storage cat gs://.../availability_index.parquet` shows v7 schema everywhere; sample parquet read returns populated rows (no NaN placeholders).
- ✅ Live-DeFi 7-day continuous run shipped per `defi_master_2026_05_07` Phase 11+.

**Handoff exception(s)**: Post-cutover plans (`simulation_scenarios_post_cutover_2026_06_01.md` etc.) explicitly deferred per anti-sequencing audit; out of scope for this plan.

## Temporary states + their canonical follow-up plans

- **`expected_universe_v2_design_2026_05_08.md` deferred behind Phase 2.1 v8 schema bump** — successor: this plan's Phase 2.1 entry. Re-evaluate after Phase 2.1 ships whether v2 enumerator runs in Phase 2.X or post-cutover.
- **v8 schema design split across two plans** — column declaration owned by [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) (operator decision 2026-05-11 resolving codex_audit F3); rescan flip schema + apply-flips execution owned by `manifest_cross_asset_rescan_design_2026_05_08.md`. Writegate slice (b) Phase 5.2 SUPERSEDED — bannered in writegate plan, slice (b) retains UTL helper + MDPS POC + deployment-api/ui surfaces.
- **GAP-2.0 VM drain + state freeze procedure** — successor: addition to `manifest_migration_master_2026_05_07.md` Stage 0 per disposition.
- **GAP-2.3 OHLCV legacy filename rename** — successor: addition to `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 2.X per disposition.

## Composes with

- CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green" HARD RULE — every phase gate requires operational evidence, not smoke-test green.
- CLAUDE.md "Capture Discoveries As Plan Todos Immediately" HARD RULE — gap closures captured in this plan vs scattered across chat / auto-memory.
- CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE — banner-add tasks listed above.
- CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE — codex updates per phase boundary.
- CLAUDE.md "Plans must capture full codebase impact upfront" HARD RULE — full impact surface enumerated via the Phase 1.A-F + Phase 2.0-2.5 + Phase 3.1-3.7 inventory.
- CLAUDE.md "Plan Archival" HARD RULE — at archive time, every deferred item migrates to an active home.
- CLAUDE.md "Citadel-Grade Planning Standards § 1 Pre-Audit" — pre-audit shipped as the audit report at top of this session; this plan is the captured output.
- `master_to_live_defi_2026_05_23.md` — the readiness model; this plan is the time-axis sequencing of how the readiness model fills in.
- `manifest_evolution_master_2026_05_08.md` — the schema-axis enforcer; this plan is the time-axis enforcer.
- `manifest_migration_master_2026_05_07.md` — the migration-stage coordinator; this plan adds Stage 0 (VM drain) and Phase 3 (backfill resumption) as bookends.

## DONE-2026-05-11 — slot 6 (harsh-workspace-qg-tab) day-1 status (freeze-gate items 8 + 9)

Slot 6 day-1 work toward the Phase 1 freeze gate (2026-05-15). Freeze-gate items 8 + 9 remain `- [ ]` — this is the
running-status note + EOD deferral-audit, not a flip. Re-runs across days 2-4.

**Shipped 2026-05-11**:

- `PM@a4512ed3` — **Track D P0-2 (slot 6 half — the QG gate, not the code fix)** — new QG STEP 5.67
  (`scripts/quality-gates-base/base-service.sh` + `scripts/quality_gates/check_banned_placeholder_methods.py` +
  `scripts/quality_gates/banned_placeholder_methods_baseline.yaml`): AST-walk detecting `_create_empty_output` /
  `_handle_empty_tick_data` / `_create_full_day_empty_output` / `_create_closed_market_candle` /
  `_maybe_write_vix_gap_placeholder` defs + direct `*.upload_bytes(...)` candle writes that bypass `record_captured`.
  Baseline-aware SHRINKING ratchet: the 8 currently-known MDPS occurrences are `pending_removal` → WARNINGS
  (exit-clean, doesn't break MDPS QG); any NEW occurrence not in the baseline fails CI. Verified exit 0 on MDPS / on
  no-occurrence repos, exit 1 on a synthetic new `def _create_empty_output`; `bash -n` clean; ruff-clean. **The P0-2
  *code fixes* — delete legacy `orchestration_writer._write_candles`, fix `tradfi/ohlcv_passthrough.py`, flip
  `output_schemas.py` OHLCV nullability, resolve the triple-SSOT — are writegate Phase 2.A + slot 5 (NOT slot 6).** As
  writegate Phase 2.A deletes the methods, it removes the matching baseline entries. **Follow-ups (slot 6, not
  blocking)**: (a) add a `test_check_banned_placeholder_methods.py` mirroring `test_check_removed_symbols.py`; (b)
  add STEP 5.67 to `codex/06-coding-standards/quality-gates.md` STEP list (Post-Plan-Phase Codex Audit); (c) verify
  whether `live_workers.py:199 _handle_empty_tick_data` + `output_writer_service.py:319 upload_bytes` are the
  good/legit variants (Track D D4 hinted live_workers does the A/B/C split correctly) — if so, narrow the heuristic
  rather than keep them baselined.
- **Track D P0-3 disposition (commodity phantom-row)** — `features-service/market(...)/commodity/cli/handlers/batch_handler.py:251-290`
  `_write_manifest` calls `writer.add(...)` for every (commodity, day) regardless of `_process_day` success → a
  fully-failed run still populates `captured`-shaped rows → `_should_skip_shard` permanently skips them. **Classified**
  (case-B/C phantom-manifest-row bug, exactly the class CLAUDE.md "Manifest phantom audit" warns about). **Captured**:
  `wave3x_track_d_findings_2026_05_11.md` § features-set-2 (D6, with the fix + owner) + `plans/active/issues/qg_sweep_2026_05_11.md`
  § cross-refs + this DONE block's deferred-work table. **Owner-routed**: slot 5 (live-pipeline) + writegate Phase 2.A
  (the fix is in `features-service` which is slot-2-sole-writer-until-Phase-7 territory — slot 6 is read-only across
  service repos). No separate issue doc (would duplicate the Track D doc). Slot 6's P1 phantom-audit pass watches for
  re-growth from this bug if/when the commodity backfill runs.
- `market-tick-data-service@3da026d` — **Track D P0-1 fix** (`wave3x_track_d_findings_2026_05_11.md` P0-1; owner
  re-routed to slot 6 by operator 2026-05-11): `engine/orchestrator.py` honest-coverage sentinel pass called
  `ManifestWriter.record_empty(row_key=...)` with NO `reason=` at 3 callsites (:2671 sports / :2808 Tier-3
  per-instrument / :2849 Tier-2 venue-level) + `scripts/rebuild_prediction_manifest.py:351` — `LegacyBlankErrorReasonError`
  swallowed by the wrapping `except Exception: "non-blocking"` → sentinel pass aborted silently for CeFi/sports on any
  zero-data-shard date (no `empty_confirmed` / `attempted_failed` rows landed → absence masked as "never attempted").
  Fix: all 4 callsites pass `reason="SOURCE_RETURNED_ZERO"`; new `except (LegacyBlankErrorReasonError, UnknownEmptyConfirmedReasonError): raise`
  before the swallowing `except` (manifest-contract violations now fail loud); imports from the UAC/UTL root facades.
  Verified ruff-clean + zero new basedpyright errors + all 12 `test_orchestrator_capture_status.py` /
  `test_rebuild_prediction_manifest_force.py` tests pass. **Slot-1 to-route**: tell slot 5 / the writegate Phase 2.A
  owner that P0-1 is done (Track D doc routed it to them; operator moved it to slot 6); the Track D doc's P0-1 owner
  pointer is now stale.
- `PM@cfeb79fc` — STARTED boot-ack ping.
- `PM@04ed9203` — **freeze-gate item 9 (codex SSOT audit pass)** — `plans/active/issues/codex_audit_2026_05_11.md`:
  25 Phase 1 plans scanned; 91 codex doc paths referenced; 58 present / 33 referenced-but-not-yet-created (all 33 are
  unchecked `- [ ]` items in their owning plans — expected pending Phase-1 work, deadline = this freeze gate). Per-plan
  pending-codex breakdown table = the freeze-gate-9 readiness checklist. Findings: F2 (codex
  `availability-manifest-and-data-status.md` v8 dataclass missing `feature_family` which UTL code has @`c16cef3` —
  routed to slot 2's `features_repo_consolidation` codex phase); F3 (v8 manifest-schema declaration owner ambiguous —
  this plan `:139`/`:174-179` says "writegate slice (b) Phase 5.1, NOT a separate file"; codex doc +
  `manifest_schema_final_gate_2026_05_09.md` say the final-gate plan — needs a slot-1/operator reconcile; tracked in
  `codex_audit_2026_05_11.md` § Open questions Q1). Core schema/manifest/pipeline codex docs spot-checked: healthy.
- `PM@e8cbe46b` — **freeze-gate item 8 (workspace QG) — static day-1 baseline** — `plans/active/issues/qg_sweep_2026_05_11.md`:
  `ruff check` (source dirs only) 20/22 repos CLEAN; `features-service` 13×I001 import-org (auto-fixable —
  mid-consolidation by slot 2, expected); `system-integration-tests` 4×C901 complexity 9-11 > SIT-local-limit 7
  (pre-existing, not slot-2-related). `# type: ignore`: 344 total, 343 coded form, **0 actual bare directives
  workspace-wide** (the classic architectural-violation-masker is absent). basedpyright + full `quality-gates.sh` sweep
  **deferred days 2-4** — slot worktrees have no per-repo `.venv`; needs `bash scripts/setup.sh` per repo first (~30-60
  min for 22 repos).

**Deferred work (slot 6) — all captured in active plans / issue docs**:

| Deferred item | Why | Tracked in |
| --- | --- | --- |
| Full `bash scripts/quality-gates.sh` workspace sweep (basedpyright + pytest + 60+ STEP checks) | slot worktrees have no per-repo `.venv` — `setup.sh` per repo needed first | `plans/active/issues/qg_sweep_2026_05_11.md` § "Days 2-4 follow-up" (1)+(2); `plans/active/work_split_2026_05_11_harsh.md` § Slot 6 full-execution criterion |
| Sampled `# type: ignore[...]` reason-comment audit (~20-30 of 343) | day-1 only confirmed zero *bare* directives; per-line architectural check pending | `plans/active/issues/qg_sweep_2026_05_11.md` § "Days 2-4 follow-up" (3) |
| Phantom manifest audit (P1) — `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group {cefi,defi,sports,tradfi,prediction} --dry-run` | laptop run impractical (no output in 4min on `cefi --dry-run --workers 32`; CLAUDE.md: cross-region listing 18× slower) — proper path = GCE same-region VM per `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit — re-runnable recipe"; ADC present, deps importable from `.venv-workspace`. 2026-05-04 baseline = 354 residual; watch the Track-D commodity-phantom-row bug | `plans/active/work_split_2026_05_11_harsh.md` § Slot 6 (P1); `plans/active/issues/qg_sweep_2026_05_11.md` § cross-refs + "Days 2-4 follow-up" (1) |
| ~~AST/grep QG STEP for banned placeholder methods~~ — **SHIPPED `PM@a4512ed3` (STEP 5.67, baseline-aware ratchet, warn-mode for the 8 known MDPS occurrences, errors on new ones)** | Residual: writegate Phase 2.A removes the matching `banned_placeholder_methods_baseline.yaml` entries as it deletes the methods (writegate's job, not slot 6). Slot-6 follow-ups (not blocking): (a) `test_check_banned_placeholder_methods.py`; (b) add STEP 5.67 to `codex/06-coding-standards/quality-gates.md` STEP list; (c) verify `live_workers.py:199 _handle_empty_tick_data` + `output_writer_service.py:319 upload_bytes` are the legit variants → narrow the heuristic if so | DONE block above (slot-6 follow-ups (a)/(b)/(c)); `plans/active/issues/qg_sweep_2026_05_11.md` § "Days 2-4 follow-up" (5); `wave3x_track_d_findings_2026_05_11.md` § "Recommended decision" (3) (now resolved) |
| Codex SSOT audit pass — deepen currency spot-checks on the ~50 present docs the Phase 1.D/E/F plans touch (alerting/risk/DR, DeFi, UI/credentials) | day-1 only spot-checked the schema/manifest/pipeline core + alerting cluster | `plans/active/issues/codex_audit_2026_05_11.md` § "Days 2-4 follow-up" |
| 33 codex docs referenced-but-not-yet-created for freeze-gate item 9 | all are `- [ ]` items in their owning Phase 1 plans — those plans' codex phases create them by 2026-05-15 | `plans/active/issues/codex_audit_2026_05_11.md` § "Pending codex work" table (per-plan); each owning plan's "Codex SSOT updates" phase |

EOD deferral-audit (per CLAUDE.md "End-of-cycle audit clause"): every row above is grep-findable in `plans/active/`
(work-split, the 3 slot-6 issue docs in `plans/active/issues/`, or — for the 33 codex docs — the owning plans' `- [ ]`
todos). No deferral lives only in chat.

## DONE-2026-05-11 — slot 5 (ikenna-defi-phase-1e-tab) DeFi Phase 1.E sequencing readiness audit

Slot 5 (Ikenna side, `tab/ikennaigboaka/5`) day-1 against the work-split § "Slot 5 — DeFi Phase 1.E sequencing
readiness + cross-plan coordination" scope. Audit the 4 Phase 1.E plans (`defi_catalogue_chain_primitives_2026_05_10`
+ `arbitrage_price_dispersion_finalisation_2026_05_09` + `cme_polymarket_arb_2026_05_08` +
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
    declaration** ([`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) — canonical v8 owner per operator decision 2026-05-11 commit `39ab61e5`; slot 5 → final-gate owner handshake). Phases 2-5 BLOCKED
    (predictions-master Phase 5 + tradfi-master Q1+Q2 + post-cutover per plan body) — explicitly OUT of May-23 scope.
    No additional anti-sequencing risk from post-cutover phases since `linked_canonical_question_group` is a cross-link
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
    `defi_archetypes_canonicalisation` Stream C (the canonical owner) before Phase 1 freeze; slot 5 → [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) owner v8 schema
    declaration handshake per work-split Cross-tab handshakes (P0).
  - **NEW row — `defi_catalogue_chain_primitives_2026_05_10.md`**: NEW `SUPPLY_APY` / `BORROW_APY` / `UTILISATION` /
    `LIQUIDATION_THRESHOLD` / `EMODE_PARAMS` data_type enums + 26 venue entries + Solana Jito MEV mode + PERP_MARGIN_TIERS
    table + LST_TOKEN_TO_PROTOCOL_ASSET SSOT. **Existing UAC state per audit**: `CHAIN_GENESIS_DATES` (chain_env.py:91)
    covers 22 chains ✅; `PROTOCOL_LAUNCH_DATES` (chain_env.py:144) covers ~50+ (chain, protocol) entries including
    Aave V3 multi-chain + Compound V3 + Uniswap V2-V4 + Spark + Lido + Rocket Pool + Etherfi + Ethena + Maker + Frax +
    Solana protocols ✅ (Tab 14 audit 2026-05-08 refined many to subgraph-truth dates). **Open per Phase 1A**: 26 new
    venue entries (Yearn / Convex / Beefy / Pendle / Idle / Balancer / Sushi V2+V3 / PancakeSwap V3 / Camelot V3 /
    Aerodromeq V3 / Velodrome V2 / TraderJoe V2 / Raydium / Orca / Jupiter / Spark verify / Radiant / RocketPool verify /
    Solblaze / EigenLayer / Symbiotic / Karak / Renzo / KelpDAO / Puffer / Jito-restaking). Phase 1 SEQUENTIAL gate for
    the catalogue plan's execution DAG; ~145-260 AI-day total scope across Phases 1-8 for May-23 cutover.
    **Lending-indices data_types must land in v8 declaration** ([`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md) — canonical v8 owner per operator decision 2026-05-11 commit `39ab61e5`; slot 5 → final-gate owner handshake).
  - **`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` row extended**: Stream B mostly shipped via
    `arbitrage_price_dispersion_finalisation`; Stream C owns the 8 → 11 StrategyArchetype enum expansion (must ship
    CARRY_RECURSIVE_BORROW_LENDING_ONLY + CARRY_RECURSIVE_BORROW_PERP_HEDGED + 3rd-TBD per AD-1 flip 2026-05-10).
    Stream C is Phase 1 critical path.
- `PM@8ea02ccd` — **Cross-plan banner sweep — 3 missing banners added**. Per work-split § Slot 5 P1 (banner sweep
  helper to slot 1 P0 banner verification): walked the 9 banner targets at this plan § "Cross-plan coordination
  banners" + the 3 new (b+)-driven targets. **Result of grep audit 2026-05-11**:
  - ✅ 8 of 9 prior banner targets verified PRESENT (master_to_live_defi:26 / manifest_evolution_master:29 (epic) /
    manifest_migration_master:27 (epic) / gcs_migration_bundle_pipeline_mode:547 / aws_migration_defi_first:19
    (already added by slot 1 PM@1b9e6451 yesterday per work-split note) / writegate_honest_coverage_endtoend:32 /
    features_repo_consolidation:931 / live_pipeline_mtds_mdps_features:938).
  - ✅ 3 missing banners ADDED this commit:
    - `deployment_ui_lifecycle_tabs_2026_05_08.md` — BE-AWARE banner clarifying env-tier UI surface already shipped
      pre-2026-05-11 per `codex/05-infrastructure/deployment-ui-architecture.md`; no additional UI work for (b+)
      data-plane provisioning.
    - `simulation_scenarios_topology_price_shocks_2026_05_09.md` — BE-AWARE banner citing the anti-sequencing audit
      row (Phase 2.2 single-walk discipline risk if sim harness writes synthetic parquets into real buckets);
      required mitigation = dedicated `*-sim-*` env-tiered buckets per yaml SSOT.
    - `client_reporting_pnl_attribution_mvp_2026_05_10.md` — BE-AWARE banner citing the bucket-name SSOT (b+)
      requirement that client-reporting + pnl-attribution output buckets MUST use
      `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)` not inline f-strings (QG STEP
      5.69 ratchet); Phase 0c bucket provisioning lands these.

**Open questions surfaced 2026-05-11 — NONE from slot 5 directly.** The work-split LEDGER cited two cross-side pings
from harsh-main 2026-05-11 07:10 UTC overlapping slot 5 + slot 1 scope (`EXPECTED_KNOWN_SOURCE_GAP` enum decision +
v8-schema-owner ambiguity); the v8-schema-owner question is writegate-Phase-5.1-ownership (slot 2's plan-of-record),
NOT a Phase 1.E sequencing question — slot 5 defers to slot 1 + operator for those.

**Findings raised 2026-05-11** (per CLAUDE.md "Findings Triage Discipline"):

- **Case-3 (outside my plan, fits another active plan)**: NEW UAC StrategyArchetype enum values
  `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_RECURSIVE_BORROW_PERP_HEDGED` are owned by
  `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07` Stream C per AD-1 flip 2026-05-10. **Not fixing
  here** — surfaced in the new audit table row for `defi_recursive_borrow_archetypes`. Stream C agent picks up.
- **Case-3 (outside my plan, fits another active plan)**: lending-indices data_types (SUPPLY_APY / BORROW_APY /
  UTILISATION / LIQUIDATION_THRESHOLD / EMODE_PARAMS) are owned by `defi_catalogue_chain_primitives` Phase 1-LENDING
  (folded in from recursive-borrow per Q11 ratification). **Not fixing here** — surfaced in the new audit table row.
  Catalogue Phase 1 agent picks up.
- **Case-3 (handshake to slot 2)**: both new-enum work streams (defi_recursive_borrow new StrategyArchetype values
  via Stream C, defi_catalogue new data_type enums) need slot 2's v8 schema declaration to reference them. Captured
  in the audit table rows' decision columns + work-split § Cross-tab handshakes "Slot 5 → Slot 2 (P0)" entry.

**Deferrals after 2026-05-11 slot 5 session**:

| Item                                                               | Status as of 2026-05-11                                                          | Successor / blocker                                                                                                       |
| ------------------------------------------------------------------ | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| UAC `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `_PERP_HEDGED` enum add | `todo` — NEITHER present in `unified-api-contracts/.../enums.py:31-118`          | `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` Stream C — Phase 1 critical path before 2026-05-15      |
| UAC `SUPPLY_APY/BORROW_APY/UTILISATION/LIQUIDATION_THRESHOLD/EMODE_PARAMS` data_type enum add | `todo` — not present in `canonical/domain/market_data/data_types.py` per Phase 1-LENDING todo | `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1-LENDING + Phase 1A — Phase 1 critical path before 2026-05-15 |
| 26 new venue entries in `defi_venue_capabilities.py`               | `todo` per `defi_catalogue_chain_primitives` Phase 1A                            | `defi_catalogue_chain_primitives_2026_05_10.md` Phase 1A — Phase 1 critical path                                          |
| v8 schema declaration referencing 3 new enum sets above            | `todo` — owned by `manifest_schema_final_gate_2026_05_09.md` per operator decision 2026-05-11 commit `39ab61e5` (writegate slice (b) Phase 5.1 SUPERSEDED) | [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md); slot 5 → final-gate owner handshake                         |
| `arbitrage_price_dispersion_finalisation` 2 P1 carryover items     | `todo` — config additions at strategy-service, no UAC/manifest impact            | `arbitrage_price_dispersion_finalisation_2026_05_09.md` Phase A remaining items (canonical BTC/USDT slot + resolver test) |
| `cme_polymarket_arb` Phases 2-5                                    | `blocked` — POST-CUTOVER per plan body; deps = predictions-master + tradfi-master | `cme_polymarket_arb_2026_05_08.md` post-May-23 follow-up                                                                  |
| `defi_recursive_borrow_archetypes` Phase 2+ (config schema → backtest → live) | `blocked-after-defi_catalogue Phase 3 backfill captured`                         | `defi_catalogue_chain_primitives_2026_05_10.md` Phase 3 lending-indices backfill                                          |
| Anti-sequencing audit row (P1) — `mock_data_pipeline_benchmarking_2026_05_10.md` bucket isolation confirmation | `todo` — verified row stays in audit table; not personally confirmed     | Owner = the mock_data_pipeline plan; banner-sweep parallel target if it touches bucket-naming                             |

**EOD deferral-audit** (per CLAUDE.md "End-of-cycle audit clause"): each row above is grep-findable in `plans/active/`
under the cited plan-of-record's `- [ ]` todos OR in this plan's audit table (rows added this commit). Slot 5 did NOT
create new issue docs — all findings route to existing active plans per Findings Triage Discipline case-3 (outside my
plan, fits another active plan). No deferral lives only in chat.
