---
doc_type: epic
title: MTDS/MDPS Master — Market Data Pipeline Coordination
summary:
  L1 epic coordinating the MTDS/MDPS data pipeline — backfill-to-100% across all asset_groups, DeFi catalogue→per-pool
  capture, honest-absence swallow remediation, MDPS book-microstructure precompute + polars adapter seam + cost
  sharpening; live work runs through survivors M-1 (data_completion_to_100) and M-2 (MTDS/MDPS tech-debt, deferred); the
  Phase -2…14 migration history is provenance only.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-api, deployment-service, deployment-ui, execution-service, greeks-service]
scope: [engineer, admin]
tags: [mtds, mdps, backfill, polars, book-microstructure, data-correctness, cost, features]
related:
  [
    ../archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ../archive/2026_07/mdps_book_microstructure_precompute_columns_2026_06_28.md,
    ../archive/2026_07/tradfi_mdps_passthrough_dependency_gap_2026_06_28.md,
    ../archive/2026_07/mdps_features_full_month_benchmark_binance_2026_06_28.md,
    ../archive/2026_07/mdps_polars_engine_cost_sharpening_2026_06_28.md,
    ../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md,
    ../archive/2026_05/d4_mtds_adapters_preflight_2026_05_20.md,
    ../archive/2026_05/dex_perp_and_venue_data_expansion_2026_05_12.md,
    ../archive/2026_05/dex_perp_onboarding_handover_2026_05_07.HANDOVER.md,
    ../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
    ../archive/2026_05/mdps_streaming_and_backpressure_2026_05_07.md,
    ../archive/2026_05/mtds_databento_path_streaming_2026_05_07.md,
    ../archive/2026_05/mtds_per_instrument_download_api_2026_04_24.md,
    ../archive/2026_05/scratch_codefreeze_phase4_mtds_fanout_2026_05_12.md,
    ../archive/2026_05/wave3x_track_d_implementation_2026_05_19.md,
    archive/2026_05/canary_coverage_qg_enforcement_2026_05_20.md,
    issues/deployment_api_shard_detail_gcs_locked_2026_05_17.md,
    /plans/audit/results/archive/mega_audit_phase_a_issues_human_readable_2026_05_20.md,
    /plans/audit/results/archive/manifest_v8_compliance_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_v8_per_vm_shards_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_divergence_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_divergence_all_services_2026_05_20_summary.md,
    /plans/audit/is_mtds_contract_audit_2026_05_20.md,
    /plans/audit/archive/mtds_features_contract_audit_2026_05_20.md,
    /plans/audit/archive/mtds_strategy_contract_audit_2026_05_20.md,
    /plans/audit/archive/strategy_execution_contract_audit_2026_05_20.md,
    /plans/audit/archive/utl_consumer_contract_audit_2026_05_20.md,
    /plans/audit/archive/uac_consumer_contract_audit_2026_05_20.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/11-project-management/foundation-completion-gate-discipline.md,
    ../archive/2026_05/global_ledger_pnl_attribution_discovery_2026_05_21.md,
  ]
created: 2026-05-20
name: mtds_mdps_master
tier: L1
priority: P0
assigned_vm: vm-ml
parent: master_to_live_defi_2026_05_23
co_operators:
codex_ssots:
related_plans:
  - ../active/data_completion_to_100_all_ag_2026_06_21.md
  - ../active/data_source_provenance_enforcement_2026_07_24.md
  - ../active/defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md
  - ../active/legacy_bucket_dual_write_decommission_2026_07_24.md
  - ../active/mtds_file_size_refactor_2026_06_08.md
  - ../active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md
  - ../active/solana_dex_pool_swaps_indexer_2026_08_08.md
  - ../active/solana_dex_pool_swaps_indexer_2026_08_08_finalize.md
last_updated:
  2026-08-20 # was 2026-07-15 — added priority-venue live-feed + candle-derivation audit section for the
  # CeFi/Ethereum-DeFi/Betfair/prediction/Morpho/Uniswap/CoW-Swap set, see body. Prior entry: was 2026-06-26 —
  # corrected 2026-07-14, doc-reconciliation finding 174: body carried dated 2026-07-12/2026-07-13 banners weeks
  # after this field was last bumped; corrected 2026-07-15, plan-reconcile: related:/related_plans: repointed 4
  # folded plans from ../active/ to ../archive/2026_07/
locked_by: live-defi-rollout
locked_since: 2026-05-20
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# MTDS/MDPS Master — Market Data Pipeline Coordination

## Report

Live HTML ledger: https://claude.ai/code/artifact/2d3e1593-bafe-4eab-8bb6-df43cdd8b0d4 (generated 2026-08-19,
`/plan-reconcile mtds_mdps_master`)

> **🔵 CONSOLIDATION 2026-06-26 — live MTDS/MDPS work now runs through 2 themed survivors.** Per the operator's
> instruments/MTDS amalgamation
> ([`instruments_mtds_plan_consolidation_2026_06_26`](../archive/2026_06/instruments_mtds_plan_consolidation_2026_06_26.plan.md),
> archived 2026-06-30, consolidation), the done/largely-done MTDS/MDPS plans were archived and their residual todos
> folded into:
>
> - **M-1 · [`data_completion_to_100_all_ag_2026_06_21`](../active/data_completion_to_100_all_ag_2026_06_21.md)**
>   (repointed 2026-06-30 — `path_to_100pct_backfill_mtds_is_2026_06_17` was MERGED + archived, `superseded_by`
>   `data_completion_to_100_all_ag_2026_06_21`) — backfill-to-100% + DeFi catalogue→per-pool capture + honest-absence
>   swallow remediation (absorbed `defi_instrument_catalogue_and_capture_pipeline`,
>   `defi_mtds_subgraph_and_adapter_fixes`, `mtds_honest_absence_swallow_remediation`).
> - **M-2 · [`mtds_file_size_refactor_2026_06_08`](../active/mtds_file_size_refactor_2026_06_08.md)** (retitled
>   "MTDS/MDPS tech-debt & coverage") — **⏸️ DEFERRED 2026-06-26 (operator, non-essential)**: file-size splits + polars
>   adapter seam + coverage/QG residuals (absorbed `mdps_adapter_protocol_pandas_to_polars`,
>   `mtds_coverage_75_and_codex_zero`, `mdps_coverage_85pct`). Parked tech-debt; does not block data correctness or
>   backfill. The live MTDS-ship blocker is the separate issue `issues/fleet_mtds_qg_red_…`, NOT this **(was: presented
>   as a current/live blocker — corrected 2026-07-14, doc-reconciliation finding 172: that issue was RESOLVED
>   2026-06-30, QG green + Cloud Build SUCCESS, archived at
>   `plans/archive/issues/fleet_mtds_qg_red_hardcoded_url_record_empty_ratchet_2026_06_22.md`, confirmed by a subsequent
>   green-QG MTDS ship 2026-07-06 (`market-tick-data-service@f4dab8f9`); see `mtds_file_size_refactor_2026_06_08.md`'s
>   2026-07-12 correction, finding 186 — no live MTDS-ship blocker remains from that issue)**.
>
> Also archived: `mtds_backfill_phase3` + `mdps_backfill_phase3` (DONE/SUPERSEDED). Live blocker issues stay as issue
> docs: `issues/features_delta_one_tradfi_mdps_dependency_gap`, `issues/fleet_mtds_qg_red_…`,
> `issues/mtds_cefi_mvp_gate_…`. **The Phase -2…14 migration coordination below is HISTORICAL** (the May bucket-symmetry
>
> - v8 backfill window); read it for provenance, not as live work.
>
> **[2026-07-12 correction]**: the "live MTDS/MDPS work now runs through 2 themed survivors" claim above (was: presented
> as exhaustive) is stale — it does not cover the still-active, still-shipping manifest-canonicalisation family
> (`cefi_manifest_canonicalisation_2026_06_01`, `defi_manifest_canonicalisation_2026_06_01`,
> `prediction_manifest_canonicalisation_2026_06_01`, `tradfi_manifest_canonicalisation_2026_06_01`,
> `downstream_services_manifest_canonicalisation_2026_06_01`,
> `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`, `solana_defi_legacy_migration_2026_05_27`), none
> of which were archived or folded into M-1/M-2, and one of which
> (`downstream_services_manifest_canonicalisation_2026_06_01`, CF-11) shipped new work as late as 2026-07-10. These
> plans remain independently live under this epic (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`
> specifically: P0, GATE-0 done, Phase 1/2 --apply still pending); see the "Assigned active plans" roster-completeness
> correction below. Corrected per plan-reconciliation findings 166/170,
> `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 B-queue ruling.

> **🟢 [2026-07-13] CONSOLIDATION EXECUTED — the "2 themed survivors" claim is now TRUE.** Per operator ruling
> 2026-07-13 ("Approve all + unlock", `plans/archive/2026_07/mtds_consolidation_foldin_mapping_2026_07_12.md`), the
> 2026-07-12 correction above is resolved: **9 plans FOLDED into M-1 and archived** —
> `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01`, `data_source_provenance_all_asset_groups_2026_06_01`,
> `macro_econ_adapter_scaffolds_2026_06_09`, `cefi_manifest_canonicalisation_2026_06_01`,
> `tradfi_manifest_canonicalisation_2026_06_01`, `prediction_manifest_canonicalisation_2026_06_01`,
> `downstream_services_manifest_canonicalisation_2026_06_01`, `defi_manifest_canonicalisation_2026_06_01` (its own
> judgment-call, ruled FOLD → M-1), and `bar_edge_left_vs_right_remediation_2026_06_08` — all 130 open todos migrated
> verbatim into M-1's new "Folded-in scope 2026-07-13" section, each source plan SUPERSEDED-banner'd + `git mv`'d to
> `plans/archive/2026_07/`. **1 plan credited into M-2**: `mdps_polars_engine_cost_sharpening_2026_06_28` (already
> complete) folded its completion credit into M-2's Progress Log, archived. **4 plan-hygiene-debt plans
> simple-archived** (0 open todos, nothing to fold): `mdps_book_microstructure_precompute_columns_2026_06_28`,
> `mdps_features_full_month_benchmark_binance_2026_06_28`, `tradfi_mdps_passthrough_dependency_gap_2026_06_28`, and
> `solana_defi_legacy_migration_2026_05_27` (frontmatter `status` corrected from stale `active` → `complete`, unlocked).
> **2 plans KEPT, not folded**: `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` stays standalone (P0
> prerequisite-gate for the per-AG canonicalisation walks now folded into M-1 — folding a gate INTO what it gates is an
> unusual shape; operator overrode the seed mapping's proposed fold) and `sports_manifest_canonicalisation_2026_06_01`
> stays an `mtds_mdps_master` child per prior operator ruling (175/142/146).
> `mdps_features_reduced_artifact_tracker_2026_06_28` was KEPT (2026-07-13) as the live cross-epic tracker for the other
> 5 (non-archived) mini-plans — **since ARCHIVED 2026-07-27** (`/plans/archive/2026_07/`): all 9 mini-plans confirmed
> archived/complete, 0 orphaned scope. **Post-fold roster under this epic**: 2 survivors (M-1
> `data_completion_to_100_all_ag_2026_06_21`, M-2 `mtds_file_size_refactor_2026_06_08`) +
> `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` (standalone prerequisite) +
> `sports_manifest_canonicalisation_2026_06_01` (delegated vertical) +
> `mdps_features_reduced_artifact_tracker_2026_06_28` (cross-epic tracker) — no orphaned `parent_epic: mtds_mdps_master`
> plans remain outside this set. See `plans/archive/2026_07/mtds_consolidation_foldin_mapping_2026_07_12.md` for the
> full mapping + execution shas.
>
> **[2026-07-14 correction]**: the "no orphaned `parent_epic: mtds_mdps_master` plans remain outside this set" claim
> above (was: presented as exhaustive) was already stale within hours of being written and has no recurring
> re-verification mechanism. Two same-day plans — `aster_cefi_data_defi_bucket_migration_2026_07_13` and
> `bybit_futures_chain_write_shape_migration_2026_07_13` (both `status: active`, both `parent_epic: mtds_mdps_master`,
> filed the same day, hours after this banner) — sit outside the named roster (doc-reconciliation findings 176/177).
> Separately, the roster's candidate-enumeration only ever scanned `plans/active/*.md` non-recursively and never
> `plans/active/issues/*.md`, so issue docs carrying `parent_epic: mtds_mdps_master` (e.g.
> `issues/cefi_universe_capture_rule_2026_06_23.md`, `status: open`, unfinished P0 IS-layer todos) were silently
> excluded from the roster too (doc-reconciliation finding 168). Read the roster above as "themed-consolidation
> survivors as of 2026-07-13", not as an exhaustive enumeration of live `parent_epic: mtds_mdps_master` work — re-derive
> the current live set via `rg -l '^parent_epic: mtds_mdps_master' plans/active/*.md plans/active/issues/*.md`.
>
> **[2026-07-25 correction]**: `sports_manifest_canonicalisation_2026_06_01`, named above (line 147/153) as a live
> "delegated vertical" child of this epic, was subsequently **archived/superseded** — folded into
> `sports_consolidated_closeout_2026_07_19.md` (its 4 constituent plans, including this one, archived per that plan's
> Progress Log) and moved to `plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md`. It is correctly
> absent from the "Assigned active plans" auto-populated section below (currently 4 plans, none of them this one) — the
> 2026-07-13 prose roster above is stale on this one entry and should be read accordingly.

> **Operator directive 2026-05-20 round 5**: "EVERYTHING needs to be in writing contained within PM active plans which
> can reference issues and audits, but I should be able to go to an orchestrator with the problem and use ALL the PM
> active plans and their references to solve."
>
> **This plan is the operator-handoff entry point.** It does NOT duplicate content from referenced plans — it sequences
> them in the order they must execute and surfaces the cross-cutting concerns that span multiple plans (bucket
> asymmetry, code freeze, denominator fix, slot coordination).
>
> Linked from CLAUDE.md § "Data Pipeline Correctness Is The Heartbeat" + from
> `mega_audit_phase_a_issues_human_readable_2026_05_20.md` § 6 as the execution-ordering layer over the delegation SSOT.

## Why this plan exists

Mega-audit Phase A (rounds 1-4) surfaced multiple interlocking findings that share a single critical-path: **bucket
naming asymmetry blocks clean manifest audit, which blocks v8 backfill, which blocks paper-trade promotion**. The
existing plans each cover one slice cleanly; what was missing is the **execution ordering** + a **single document an
orchestrator can read once** to know what runs in what order, in what slot, with what code-freeze gate.

Symptoms the audit surfaced (linking to evidence):

1. **0% of 7.4M manifest rows at v8** ([A4](/plans/audit/results/archive/manifest_v8_compliance_2026_05_20_summary.md)).
   Confirmed writer-fleet-stale (residual analysis excludes 42 one-off shards; residual 3,853 shards still 100% v<8) —
   Docker images deployed to VMs built before the v8 constant bump.
2. **236,892 `MISSING_EXPECTED` + 765 `DIVERGENT_EMPTY` cells** across MTDS
   ([A3](/plans/audit/results/archive/manifest_divergence_2026_05_20_summary.md)).
3. **AWS bucket naming asymmetric to GCP** — naming convention drift: GCP
   `market-data-tick-defi-prd-central-element-323112` vs AWS `unified-trading-market-data-defi-427895769566` (no env
   tier; extra `unified-trading-` prefix). 62-char limit drove `prd` over `prod` on GCP per
   [bucket_name_ssot_canonicalisation_2026_05_10.md](bucket_name_ssot_canonicalisation_2026_05_10.md); AWS needs the
   same treatment for code-path identity.
4. **16 service buckets without consolidated manifest**
   ([A3 v2](/plans/audit/results/archive/manifest_divergence_all_services_2026_05_20_summary.md)) — 14 empty (Group B
   env-split rollback) + 2 with non-manifest data (execution-store-cefi, ml-training-artifacts).
5. **Hybrid consolidator runtime** (legacy GCE VM + 10 Cloud Run jobs) — resolved 2026-05-20: legacy VM deleted
   (deployment-service@73183b7), Cloud Run is canonical per
   [/codex/05-infrastructure/manifest-consolidator-ssot.md](/codex/05-infrastructure/manifest-consolidator-ssot.md).
6. **Denominator/numerator confusion in deployment-UI** — currently shows captured/in_scope ratio, but in_scope
   underreports what we COULD capture. See
   [honest_coverage_formula_consolidation_2026_05_19.md](honest_coverage_formula_consolidation_2026_05_19.md) for the
   formula work.

## Critical-path ordering (DO NOT REORDER)

> **Ordering rationale (operator question 2026-05-20 round 6)**: schema + labels MUST be clean BEFORE operational data
> backfill. The Phase 6 → 7 → 11 chain encodes this:
>
> 1. **Phase 6**: Docker rebuild + redeploy → writer fleet now produces v8 rows with typed `EmptyConfirmedReason`
>    (steady-state writers fixed).
> 2. **Phase 7**: existing v<8 rows migrated to v8 + bad reason labels flipped + 765 `DIVERGENT_EMPTY` cells triaged
>    (label-flip applied OR queued for Phase 11 re-backfill).
> 3. **Phase 11**: operational data backfill runs against the NOW-CLEAN manifest. Every new write lands at v8 + typed
>    reason because Phase 6 fixed the writer binaries.
>
> **Why this order is non-negotiable**: backfilling data into a stale-schema manifest (skip Phase 7) just grows the v<8
> backlog — millions of new rows at v6/v7, defeating the v8 invariant. Phase 7 is the SINGLE step that guarantees Phase
> 11's output is honest from the first row.

> **2026-05-20 round 5 re-sequencing**: operator directive added two prereqs BEFORE Phase 0 (strategy/ml/features
> consolidation + workspace-wide QG green) and four post-data phases (11-14) for backfill-to-100% + live-data
>
> - batch-live symmetry + strategy/execution topology cleanup.
>
> **2026-05-20 round 6 — strategy-service LOGIC freeze gate**:
>
> Operator directive: "strategy archetype refactor post consolidation is baked in as an assumption to the master plan
> and agents will halt on those repos until its complete which should be tonight." Plus operator note: "they should do
> the consolidation part and quality gates in advance of me."
>
> **What proceeds (NO freeze on these)**:
>
> - Phase -2 Bucket 3 stale-ref cleanup across slots 3-8 (logger strings, terraform destroy on archived dirs,
>   deployment-ui registry, UAC slugs — SURFACE cleanup, NOT logic).
> - Phase -2 consolidation Phase 11 sub-phases (11a-11h) in both `strategy_repo_consolidation_2026_05_19.md` +
>   `ml_repo_consolidation_2026_05_19.md`.
> - Phase -1 workspace-wide QG green (Harsh-side).
> - Phases 0-10 of data-pipeline migration once -2/-1 land GREEN.
>
> **What freezes until operator's Opus-1M `strategy_archetype_logic_audit_2026_05_20` session lands GREEN tonight +
> R-items dispatched**:
>
> - Strategy-service ARCHETYPE LOGIC changes (`strategy_service/strategy_service/engine/strategies/v2/`).
> - Allocation / rebalancing logic (`strategy_service/strategy_service/engine/allocator/`).
> - Collateral management code (per dimension 10 of the archetype audit).
> - Liquidation management code (per dimension 11).
> - Cross-venue transfer code (per dimension 12).
> - Venue restriction enforcement (per dimension 9).
> - Deployment topology dynamic-config + accounts/clients code (per dimension 14 — overlaps execution-service
>   `client_share_classes` consumers + agent-orchestrator account-management endpoints).
>
> Agents touching these surfaces during the freeze MUST stop + cite the gate. Resume signal: operator appends
> `🟢 STRATEGY-LOGIC UNFREEZE` to `plans/active/_agent_pings.md` referencing the audit's R-items.

```
                            ┌──────────────────────────────────────┐
                            │  Phase -2: Strategy/ML/Features      │
                            │  repo consolidation FINISH           │
                            │  (separate agent owns; ~20min ETA)   │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase -1: Workspace-wide QG green   │
                            │  (Harsh-side owns; gating for all    │
                            │  ikenna-side migration work)         │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 0: Pre-flight audits          │
                            │  (mega-audit Phase A — DONE)         │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 1: AWS↔GCP bucket name        │
                            │  symmetry audit + fix                │
                            │  (drop unified-trading- prefix,      │
                            │  add env-tier infix on AWS)          │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 2: CODE FREEZE WINDOW          │
                            │  ALL slots paused; broadcast ping    │
                            │  (operator-triggered start)          │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 3: Drain VM fleet              │
                            │  (gracefully stop + consolidate     │
                            │  per-VM shards to canonical)         │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 4: GCS bucket migration       │
                            │  (single → split per env-tier;       │
                            │  bucket-name SSOT cutover)           │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 5: AWS bucket migration       │
                            │  (symmetric to GCP; same code path)  │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 6: Docker rebuild + redeploy  │
                            │  (writer fleet → v8 binaries)        │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 7: Manifest v8 backfill +     │
                            │  label-flip historical rows          │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 8: Code-freeze release         │
                            │  Slots resume normal work            │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 9: Denominator/numerator fix  │
                            │  in deployment-UI (parallel to      │
                            │  Phase 10)                           │
                            └──────────────┬───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────────────────┐
                            │  Phase 10: QG enforcement upgrade    │
                            │  (manifest v8 + dependency-check)    │
                            └──────────────────────────────────────┘
```

## Phase reference table (orchestrator entry point)

Each phase points at the plan(s) that own the implementation detail. **The orchestrator's job is to read this table
top-down + dispatch slots accordingly.** No phase content duplicated here.

| Phase                                                                                                                                   | Plan(s)-of-record                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Owner slot                                                                                                                                                        | Pre-req                               | Verification (when done)                                                                                                                                                                                                                                                                |
| --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **-2. Strategy/ML/Features consolidation finish**                                                                                       | `strategy_repo_consolidation_2026_05_19.md` (Phase 11 cleanup — 30/31 base done; sub-phases 11a-11h appended by separate agent) + `ml_repo_consolidation_2026_05_19.md` (Phase 11 same structure) + `features_repo_consolidation_2026_05_08.md`. **Outstanding work** (per operator write-up 2026-05-20 round 5): ✅ **Bucket 1 DONE 2026-05-20**: `gh repo archive` executed for `ml-training-service` + `ml-inference-service` (`isArchived: true` confirmed via gh api). ✅ **Bucket 2 DONE 2026-05-20**: operator chose **unified bucket** for `strategy-store` — `strategy_execution_contract_remediation_2026_05_20.md` Phase 4a/4b unblocked; migration bundled into master coordinator Phase 1. 🟡 **Bucket 3** 545 stale refs to 5 archived services across 12 consumer repos (~50-150 real cleanup items) — separate-agent per-slot pings already dispatched to ikenna slots 3-8 with P0/P1 priority; **~4.75 cal AI-days fan-out**. 🟢 **Bucket 4 ACKED**: `strategy_archetype_logic_audit_2026_05_20` re-prioritised P0 + authorised to run **TONIGHT 2026-05-20 in parallel** with Phase 11 cleanup tail (operator round 5: "mostly done anyway"). Requires **Opus 4.7 (1M context)** — separate session. | Bucket 3: separate agent's slot dispatch (slots 3-8 per `ikenna_orchestrator/pings/slot_{3..8}.md`). Bucket 4: dedicated Opus-1M session (operator-orchestrated). | —                                     | Buckets 1+2 ACKED+DONE; Bucket 3 grep returns 0 real-cleanup hits across slots 3-8 dispatch; Bucket 4 strategy_archetype_logic_audit produces audit doc + R-items                                                                                                                       |
| **-1. Workspace-wide QG green**                                                                                                         | NEW CLAUDE.md HARD RULE this round + per-repo `bash scripts/quality-gates.sh` exit 0. **Round 6 ownership update 2026-05-20** (Harsh offline India tz): re-assigned to **Ikenna slots 9, 10, 11 BACKGROUND** (operator-choice: Ikenna AWS VM or local laptop) per `work_split_2026_05_20_ikenna.md` § Slots 9-11 with cluster split (A: UAC+UTL+IS / B: MTDS+features+MDPS / C: strategy+execution+ml — strategy under LOGIC-freeze, surface-only fixes). When Harsh wakes, Harsh-side slots resume QG ownership; slots 9-11 hand off via git rebase.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **Ikenna slots 9, 10, 11** (Harsh slots resume on his next online window)                                                                                         | Phase -2 GREEN                        | Every active repo: `bash scripts/quality-gates.sh` exit 0; QG-green evidence line on every PR going forward; 9 repos GREEN (3 per cluster × 3 slots)                                                                                                                                    |
| **0. Pre-flight audits**                                                                                                                | `/plans/audit/results/archive/mega_audit_phase_a_issues_human_readable_2026_05_20.md` + the 6 contract audits in `audit/`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | slot-1 main (mega-audit owner — already DONE round 4)                                                                                                             | Phase -1 GREEN                        | All R-items in mega-audit § 6 have named owner + plan; this file exists                                                                                                                                                                                                                 |
| **1. AWS↔GCP bucket-name symmetry audit + fix**                                                                                         | `bucket_name_ssot_canonicalisation_2026_05_10.md` (extension) + see new § "Phase 1 — bucket symmetry" below                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | **Slot 2 + Slot 3** (code_freeze owners — closest to bucket plumbing)                                                                                             | Phase 0 GREEN                         | A3 v2 re-run: AWS bucket names match GCP template (env-tier present, no `unified-trading-` prefix), all ≤63 chars                                                                                                                                                                       |
| **2. CODE FREEZE WINDOW**                                                                                                               | This plan § "Phase 2 — code freeze protocol"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | **Slot 1 main** (operator triggers; main broadcasts)                                                                                                              | Phase 1 GREEN                         | All non-freeze slots ACK'd in `_agent_pings.md`; zombie watchdog + Cloud Run consolidators still RUNNING                                                                                                                                                                                |
| **3. VM fleet drain**                                                                                                                   | `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.0 Stage 0 (existing)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | **Slot 2 + Slot 3**                                                                                                                                               | Phase 2 active                        | All non-essential VMs STOPPED; per-VM shards consolidated; manifest snapshot under `_index/snapshots/pre_migration_2026_05_XX.parquet`                                                                                                                                                  |
| **4. GCS bucket migration**                                                                                                             | `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.2-2.6 + `gcs_migration_bundle_pipeline_mode_2026_05_08.md` (single-walk discipline)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **Slot 2 + Slot 3**                                                                                                                                               | Phase 3 GREEN                         | Every GCS object lives under the new env-tiered bucket; `resolve_bucket_name()` returns the new bucket name for all kinds                                                                                                                                                               |
| **5. AWS bucket migration**                                                                                                             | `aws_migration_defi_first_2026_05_07.md` (extension) + see § "Phase 5 — AWS migration" below                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | **Slot 4** (api_keys owner — adjacent to AWS credentials work)                                                                                                    | Phase 4 GREEN                         | AWS bucket names match GCP template (per Phase 1 audit); s3:// objects migrated to new bucket names                                                                                                                                                                                     |
| **6. Docker rebuild + redeploy**                                                                                                        | `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7.A (extended this session to diagnose Docker staleness FIRST)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **Slot 5** (writegate owner; R6 in mega-audit)                                                                                                                    | Phase 5 GREEN                         | Sample 100 newest manifest rows per bucket; ALL at `schema_version=8` (steady-state writers confirmed deployed)                                                                                                                                                                         |
| **7. Manifest v8 backfill + label-flip (SCHEMA + LABELS clean — operational data backfill comes in Phase 11 ONLY after this is GREEN)** | `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7.B/7.C/7.D + `d3_manifest_v8_finish_2026_05_20.md` + `hard_schema_phase1_field_flip_migration_2026_05_19.md` (label-flip). **Scope** (HARD ORDER): (a) migrate every v<8 row → v8 schema; (b) flip every bad/blank `empty_confirmed.reason` to typed `EmptyConfirmedReason` enum value; (c) **triage the 765 `DIVERGENT_EMPTY` cells from A3** — per-cell decision: cells that were captured-but-mislabelled → label-flip to `captured` HERE in Phase 7; cells where the adapter genuinely returned 0 + needs re-fetch → mark for **Phase 11** consumption. **NO data backfill in Phase 7 — only label/schema correctness on existing rows.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **Slot 5**                                                                                                                                                        | Phase 6 GREEN                         | A4 re-run: 100% v8 + 0 NULL across all 10 buckets; label-flip-bad-rows reconciler outputs 0 mismatches; DIVERGENT_EMPTY triage CSV produced with per-cell classification (label-flip-applied vs Phase-11-rebackfill vs operator-scope)                                                  |
| **8. Code-freeze release**                                                                                                              | This plan § "Phase 8 — release protocol"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **Slot 1 main**                                                                                                                                                   | Phase 7 GREEN                         | Broadcast UNFREEZE ping; resume slot themes per `work_split_2026_05_19_ikenna.md`                                                                                                                                                                                                       |
| **9. Denominator/numerator fix in deployment-UI**                                                                                       | `honest_coverage_formula_consolidation_2026_05_19.md` + `data_status_drilldown_shard_atom_alignment_2026_05_07.md` + `deployment_ui_lifecycle_tabs_2026_05_08.md` (post-unfreeze)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | **Slot 6** (deployment-UI owner — unfrozen after Phase 8)                                                                                                         | Phase 8 GREEN                         | UI shows: numerator = `captured` cells; denominator = `captured + empty_confirmed + attempted_failed + expected_unattempted` (everything we tried OR could have tried). Out-of-scope cells NOT in denominator                                                                           |
| **10. QG enforcement upgrade**                                                                                                          | `canary_coverage_qg_enforcement_2026_05_20.md` (existing) + extend with manifest-v8 QG step + upstream-dep-check QG step                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **Slot 5** + **Slot 2/3**                                                                                                                                         | Phase 8 GREEN (parallel with Phase 9) | New QG steps: (a) `check_manifest_v8_writer_runtime.py` (samples recent writes for v8); (b) `check_dependency_fail_propagation.py` (per A5 findings); both ratchet to 0 violations workspace-wide                                                                                       |
| **11. Backfill to 100% per asset_group (OPERATIONAL data — runs against the now-clean v8 + correctly-labelled manifest from Phase 7)**  | mega-audit § 6 R1-R5 (DeFi 184k + Sports 25k + CeFi 16k + TradFi 7k + Prediction 3k `MISSING_EXPECTED`) + the **Phase-11-rebackfill** subset of DIVERGENT_EMPTY cells from Phase 7's triage CSV + `mtds_backfill_phase3_2026_05_22.md` Phase 3 (DeFi) + per-asset-group epic banners. (Note: `defi_upstream_46day_full_backfill_2026_05_16.md` was referenced here but never created — git history confirms no deleted/renamed match. Replaced by `mtds_backfill_phase3_2026_05_22.md` which IS the DeFi upstream backfill plan-of-record.) **Every new row lands at v8 + typed reason** (Phase 6 Docker rebuild + Phase 7 schema clean ensure this).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Slots 6 / 7 / 9 (unfrozen post Phase 8); slot 5 owns v8-correctness verification + per-batch sample-check (assert all newly-written rows at v8)                   | Phase 10 GREEN                        | A3 re-run per `asset_group`: 0 `MISSING_EXPECTED` cells without operator-acked `BLOCKED-_` status; 0 `DIVERGENT_EMPTY` residual (all cleared by Phase 7 triage OR Phase 11 re-backfill); numerator/denominator ratio per asset_group ≥ 99% (until proven otherwise per Phase 9 formula) |
| **12. Live-data adapter completion (master plan)**                                                                                      | NEW master plan: `live_data_adapter_master_2026_05_20_or_later.md` (operator-authorise creation). Covers every venue × data_type having a live equivalent — see A6 batch-live parity findings + mega-audit R17 (13 BATCH_ONLY cells + 146 MISSING_BOTH triaged). Plus live pipeline: `live_pipeline_mtds_mdps_features_2026_05_08.md` (existing) extended                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Slot 4 (live wiring; already in api_keys+defi_recursive_borrow theme) + slot 5 (live writer parity)                                                               | Phase 11 GREEN for the batch side     | A6 re-run: 0 BATCH_ONLY cells (every venue × data_type has matching live adapter); live adapters confirmed running with manifest emission @ v8                                                                                                                                          |
| **13. Batch-live symmetry verification**                                                                                                | `batch_live_symmetry_2026_05_10.md` (existing, extended this audit round) + new sub-plan if needed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Slot 3 (already owns batch_live_symmetry T1-3); slot 9 owns T4-7 post-unfreeze                                                                                    | Phase 12 GREEN                        | Live adapter can be started at any time for strategy-service consumption WITHOUT pricing-data gaps; batch-live formula identical across modes (per CLAUDE.md `Batch = Live (CRITICAL)`); cross-mode reconciler exit 0                                                                   |
| **14. Strategy + execution deployment topology cleanup**                                                                                | `strategy_execution_contract_remediation_2026_05_20.md` (existing) + `strategy_repo_consolidation_2026_05_19.md` residuals + execution-service deployment topology plans                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Slot 5 (writegate + strategy is already there) + slot 8 (defi_catalogue close → defi_execution wiring)                                                            | Phase 13 GREEN                        | Strategy + execution deployment topology validated end-to-end with the new bucket layout + manifest v8 + live adapters. Ready-state for paper-trade → live-trade promotion per `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`                                                |

> **Phase 11 add-on (2026-06-02) — MDPS leading-NaN historical densify reprocess.** The MDPS leading-NaN workstream
> (`plans/active/issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`, shipped 2026-06-02:
> market-data-processing-service@5a5e989/4fd962d/23d7add/56202b0) made every candle adapter emit dense, no-leading-NaN,
> no-NaN-OHLC candles **go-forward**. Historical parquets written before the fix still carry the legacy leading-NaN /
> NaN-OHLC shape. Remediation = **force-reprocess of already-`captured` cells** — re-run the MDPS adapters over
> historical raw ticks so the written candles densify. **This is NOT covered by the Phase 11 MISSING_EXPECTED
> backfill**: `mtds_backfill_phase3` runs `VM_FORCE=false` + `ManifestFreshnessCache`, which **skips already-captured
> cells**, so the leading-NaN cells are walked right past. It is **NOT** a manifest-consolidator task (the consolidator
> only merges manifest shards into `_index`) and **NOT** a GCS-object-migration walk
> (`gcs_migration_bundle_pipeline_mode` cannot re-derive dense candles — that needs the raw ticks + new finalizer).
> **Scope it as a `VM_FORCE=true` reprocess of the asset_groups/date-windows that backtest + features-onchain actually
> read**, folded into the next MDPS historical reprocess window (no standalone whole-corpus walk, per single-walk
> discipline). Tracked as the `[DATA] P1` item in the issue doc; Phase-11 owner pulls it into the operational-backfill
> scope. **Force-launch prerequisite SHIPPED 2026-06-02 — `deployment-service@709f845`.** The operational path to
> deliver `--force` to an MDPS candle VM was MISSING (the `mdps-backfill` VM_TASK ran `VM_BACKFILL_CMD` verbatim,
> ignoring the `VM_FORCE` bridge; the launcher dropped `--force`). `launch-mdps-backfill-vm.sh` now accepts `--force` /
> `FORCE=true` and threads it into the `process` CLI (`_write_candles(force=True)`). **Scope clarified (operator
> 2026-06-02): REAL data, not mock** — `pipeline_mode` has no `mock` value; mock is a credential-free test runtime,
> never a candle partition. **Launch handed to slot-1-main** (operator decision 2026-06-02): pull `--force` reprocess
> into the next window; **DeFi gates on the active `_index` single-walk contention (`defi_manifest` C0-GREEN)**;
> non-DeFi first. Invoke: `bash launch-mdps-backfill-vm.sh --force <ag> <start> <end> full`. (`[DATA] P1` stays OPEN —
> reprocess not yet run.)

- [ ] [DATA] P1. **MDPS leading-NaN historical densify reprocess** (migrated from
      `plans/archive/issues/mdps_state_adapter_leading_nan_audit_2026_05_29.md`, archived 2026-06-09 — code+tests
      shipped @5a5e989/4fd962d/23d7add/56202b0, only the operational backfill remains). Repo: `deployment-service`
      (launcher) + `market-data-processing-service` (finalizer). Force-reprocess already-`captured` candle cells so
      legacy leading-NaN / NaN-OHLC parquets densify — `VM_FORCE=true`, scoped to the asset_groups × date-windows that
      backtest + features-onchain actually read (NO standalone whole-corpus walk, per single-walk discipline).
      Force-launch path shipped @deployment-service@709f845. Invoke
      `bash launch-mdps-backfill-vm.sh --force <ag> <start> <end> full`; non-DeFi first, DeFi gates on `defi_manifest`
      C0-GREEN `_index` single-walk. **Handed to slot-1-main** (operator 2026-06-02). Done = manifest-verified dense
      candles + sample parquets show no leading-NaN for the reprocessed windows.

## Phase 1 — bucket-name symmetry (AWS ↔ GCP)

**Current asymmetry** (illustrated for MTDS DeFi):

| Cloud | Current name                                       | Length                       |
| ----- | -------------------------------------------------- | ---------------------------- |
| GCP   | `market-data-tick-defi-prd-central-element-323112` | 48 chars                     |
| AWS   | `unified-trading-market-data-defi-427895769566`    | 46 chars (NO env-tier infix) |

**Target symmetric naming**:

| Cloud | Target name                                        | Length   | Rationale                                                                              |
| ----- | -------------------------------------------------- | -------- | -------------------------------------------------------------------------------------- |
| GCP   | `market-data-tick-defi-prd-central-element-323112` | 48 chars | Already canonical                                                                      |
| AWS   | `market-data-tick-defi-prd-427895769566`           | 38 chars | Drop `unified-trading-` prefix; add env-tier infix `prd`; project-id naturally differs |

**Code-path identity benefit**: every caller already does `resolve_bucket_name(kind, asset_group)` → the YAML template
determines the name. With symmetric templates that differ ONLY by `${GCP_PROJECT_ID}` vs `${AWS_ACCOUNT_ID}`, the code
paths are identical — readers + writers don't branch on cloud.

**Phase 1 deliverables**:

1. - [x] ✅ **AWS bucket inventory audit** — 64-row CSV produced (64 kind×ag pairs; 34 drift, 3 already_symmetric).
         deployment-service@`43fb886` (backfill 2026-05-21). Evidence:
         `plans/audit/results/aws_gcp_bucket_symmetry_2026_05_20.csv` + summary.
2. - [x] ✅ **Bucket-spawning script audit** — 11 scripts audited; 2 drift fixes applied (manual-audit + audit-records);
         1 legacy bootstrap_aws.sh noted (intentional — not in normal flow). deployment-service@`68e3558` + `b9029ad`.
3. - [x] ✅ **YAML template alignment** — 34 kinds updated to drop `unified-trading-` prefix + add missing infixes
         (`tick-`, `-store-`). 4 known structural divergences documented in `check_symmetry.py`.
         deployment-service@`43fb886`.
4. - [x] ✅ **63-char cap re-verification** — all clear: 64 current names max 56 chars; 64 target max 40 chars.
         Automated going forward via `scripts/bucket_naming/check_symmetry.sh`. deployment-service@`68e3558`.
5. - [x] ✅ **`prd`/`stg`/`dev` consistency** — DEPLOYMENT_ENV_SHORT 3-char form (`dev`/`stg`/`prd`) used uniformly on
         both clouds; `check_symmetry.sh` covers this going forward. deployment-service@`68e3558`.

## Phase 2 — code freeze protocol

**When**: triggered by operator after Phase 1 GREEN. Operator broadcasts in `plans/active/_agent_pings.md` cross-side +
each side broadcasts in their own `_agent_pings.md`.

**What freezes**:

- ALL slot agents (ikenna 2-9 + harsh 2-N) — no new commits to live-defi-rollout during the migration window.
- ALL backfill / live writer VMs — drained gracefully per Phase 3.
- Cron schedules → operator decides per-job whether to disable or let queue (manifest consolidator should KEEP running
  to ingest the drain).
- Cloud Run consolidator jobs (10 of them) — KEEP running so drain consolidation works; once drain complete + migration
  starts, pause briefly.

**What does NOT freeze**:

- `vm_zombie_watchdog.py` — keeps running so abandoned VMs get cleaned up.
- Manifest consolidator Cloud Run jobs (10) — keep running until Phase 4 starts; then pause + resume post-migration.
- Operator + slot-1 main read-only work (status checks, audit re-runs).

**Broadcast ping template** (operator + slot-1 main fire this):

```
🔴 CODE FREEZE 2026-05-XX — data-pipeline migration window

Reason: bucket naming AWS↔GCP symmetry cutover + manifest v8 backfill.
Per plan: plans/active/mtds_mdps_master.md.

ALL SLOTS:
- DO NOT push to live-defi-rollout during the freeze window.
- DO NOT launch new backfill VMs.
- Existing in-flight code on tab branches: hold; do not merge.
- Read-only work allowed (status checks, audit re-runs, plan updates).

EXPECTED DURATION: ~24-48h (operator-confirmed end via UNFREEZE ping).

ACK CHECKLIST (slot-1 main tracks):
- [x] ikenna slot 2 — pm@28a465b29 "slot-2 ACK code freeze 2026-05-21 — holding LDR pushes"
- [x] ikenna slot 3 — functional delivery: deployment-service@c7e0fa2 migrate-flat-to-env-tiered.sh (2026-05-21); pushed to LDR (minor freeze discipline violation — inert script, no data movement; accepted by slot-1 main)
- [x] ikenna slot 4 — pm@b313ea37d "slot-4 ACK freeze + wave2 all-done status"
- [x] ikenna slot 5 — pm@523688ff2 "slot-5 ACK code-freeze 2026-05-21 — wave2 slot-C/D plan-docs pushed; holding code until UNFREEZE"
- [x] ikenna slot 6 — already frozen per mega-audit; wave commits compliant (pm@8c2a135fe)
- [x] ikenna slot 7 — already frozen per mega-audit; tab-branch work only
- [x] ikenna slot 8 — pm@35dc137a8 "slot-8 writegate Phase 1A+2A+2B DONE + ACK freeze 2026-05-21"
- [x] ikenna slot 9 — already frozen per mega-audit; no LDR pushes
- [x] harsh main + spawned slots — OFFLINE (India tz); covered by ikenna slot-1 main 2026-05-21
```

**During freeze**: slot-1 main monitors `_agent_pings.md` + runs `gcloud compute instances list` every 30 min to verify
drain progress.

## Phase 5 — AWS migration (symmetric to GCP)

Reference: existing `aws_migration_defi_first_2026_05_07.md` plus the Phase 1 symmetry work above.

Per operator directive 2026-05-20 round 5: "AWS buckets name wise to look as identical as possible apart from
project_id." Concrete shape:

```yaml
# cloud-providers.yaml (target — Phase 1 closes the diff)
aws:
  storage:
    market-data:
      CEFI: "market-data-tick-cefi-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}"
      DEFI: "market-data-tick-defi-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}"
      ...
    instruments-store:
      CEFI: "instruments-store-cefi-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}"
      ...
```

vs current AWS shape (which has `unified-trading-` prefix + no env tier).

**Phase 5 specific deliverables**:

1. - [ ] **AWS object migration** — `aws s3 sync` from current → target bucket names per Phase 1 inventory.
         Per-asset-group, single-walk discipline.
2. - [ ] **AWS bucket creation scripts** — confirm every target bucket has a Terraform / script provisioning step that
         creates it idempotently (existing check from operator: "scripts spawning them and checking if they exist
         already in deployment services for both clouds").
3. - [ ] **AWS old-bucket deletion** — only after Phase 7 verification GREEN
   - 30-day retention check.

## Phase 9 — denominator/numerator fix in deployment-UI

Per operator directive 2026-05-20 round 5: "we need the denominator is data status and numerator fixes so that we truly
showing % of data we try to capture vs amount we theoretically COULD capture until proven otherwise."

Current confusion (per `honest_coverage_formula_consolidation_2026_05_19.md`):

- Multiple formulas exist for "coverage %" across deployment-api consumers.
- Different denominators: sometimes `in_scope`, sometimes `captured + empty`, sometimes the A2 oracle's
  `SHOULD_HAVE_DATA` count.

**Target formula** (codified in this plan + the existing honest_coverage plan):

- **Numerator**: `count(capture_status == "captured")` — cells we successfully captured.
- **Denominator**: `count(capture_status in {captured, empty_confirmed, attempted_failed, expected_unattempted})` —
  every cell we tried OR could-have-tried, EXCLUDING `out_of_scope` / `NOT_IN_SCOPE` per the A2 oracle.
- **Display**: "% of in-scope cells captured" with breakdown panel showing the 4-state distribution.
- **Until proven otherwise**: any cell the A2 oracle says `SHOULD_HAVE_DATA` but the manifest says `empty_confirmed`
  (a.k.a. `DIVERGENT_EMPTY`) goes into the denominator AND triggers an investigation alert — these are the "lost data"
  cells the UI must surface.

## Slot dispatch table (cross-referencing mega-audit § 6)

| Slot | Mega-audit R-items                                                                                        | Phase ownership in this plan                                      |
| ---- | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| 1    | R10 (extend A3 to all services — DONE), R-NEW-1/2/3 coordination                                          | Phase 0 + 2 + 8 (broadcast + drain monitor + unfreeze)            |
| 2    | R19 (UAC import-surface QG), code_freeze §2.6                                                             | Phase 1 + 3 + 4 + 10 (bucket SSOT + drain + migration + QG)       |
| 3    | R19 alt, code_freeze §2.0-2.5                                                                             | Phase 1 + 3 + 4 (bucket symmetry + drain + migration)             |
| 4    | (api_keys + defi_recursive_borrow) — credentials unblock; **R-NEW-6 candidate**                           | Phase 5 (AWS migration) + R-NEW-6 detector if assigned            |
| 5    | R6, R9, R13, R14, R15, R16, R18, R22, R23 (writegate + v8 backfill + writer SSOT)                         | Phase 6 + 7 + 10 (Docker rebuild + v8 backfill + label flip + QG) |
| 6    | R1, R8, R11, R20 (DeFi MISSING_EXPECTED + UI lifecycle + protocol pause venue-level + lifecycle_class QG) | Phase 9 (denominator/numerator UI) — unfrozen post Phase 8        |
| 7    | R2, R7 (Sports MISSING_EXPECTED + sports off-season integration)                                          | Resume own backlog post-unfreeze                                  |
| 8    | R-NEW-6 candidate (defi-catalogue context); IS-side audits                                                | Phase 1 IS-bucket symmetry contribution + R-NEW-6 if assigned     |
| 9    | R3, R4, R5, R17 (Prediction/TradFi/CeFi A3 + A6)                                                          | Resume own backlog post-unfreeze                                  |

## MTDS QG-debt dispatch (slot 7, 2026-06-01 — surfaced shipping AUDIT-03 F-22)

MTDS `scripts/quality-gates.sh` is **pre-existing-red** on LDR (independent of F-22, which landed at mtds@`0716a544`):

- [ ] [SCRIPT] P1. **UTL top-level re-export gap.** `unified_trading_library` re-exports `gcs_delete_object` at top
      level but NOT `gcs_copy_object` / `gcs_describe_object` — so `migrate_prediction_to_pred_prd_v9.py` MUST
      deep-import `from unified_trading_library.cloud_interface import ...`, which the import-pattern QG step flags (and
      ruff rejects a `# noqa: qg-deep-import` as an invalid directive). Fix in UTL: add `gcs_copy_object` +
      `gcs_describe_object` to the top-level `__init__` re-exports (consistent with `gcs_delete_object` + the CLAUDE.md
      GCS-object-ops rule), then switch the MTDS migration imports to top-level. Repos: unified-trading-library +
      market-tick-data-service.
- [ ] [SCRIPT] P2. **ruff-format drift** in `scripts/backfill_drift_v2_historical.py` /
      `scripts/backfill_solana_dex_state.py` / `scripts/migrate_defi_full_v9_canonical.py` (3 files `ruff format` would
      reformat). Run FIX-mode QG + commit. Repo: market-tick-data-service. (Foreign migration scripts — left for the
      MTDS / slots-2/3 owner, not swept by slot 7.)

## Fleet data-fetch dispatch (slot 7, 2026-06-01 — from `running_vm_fleet_status_2026_05_27.md`)

- [x] ✅ [CODE] P1. **DONE 2026-06-02 (slot 7) — instruments-service@`35a745ef`.** Root cause: `_TARDIS_VENUE_EXCHANGES`
      (instruments-service `reference_data/router.py`) had **no OKX entries** → OKX-FUTURES discovery fell through to
      the adapter default `okex` (spot) and emitted `BTC-USDT` instead of native okex-futures dated ids. Added
      `okx-spot→okex` / `okx-swap→okex-swap` / `okx-futures→okex-futures` (matches UAC
      `venue_mapping.to_tardis_exchanges`) + regression test; live-validated (free `/exchanges/okex-futures`, 5740
      native syms). IS now emits native ids; MTDS consumes unchanged via `_resolve_dated_future_symbols`. Independent of
      the BLOCKED Tardis paid key. **Operational follow-up (next backfill window)**: re-run the OKX-FUTURES historical
      backfill (the 28k attempted_failed flip to captured); dry-run-validate the rebuilt symbol set vs the live listing
      first. Original diagnosis retained below.
  - **Original diagnosis (provenance)**: Tardis rejected `BTC-USDT` + dated contracts ("use the okex-futures exchanges
    API for allowed values"); valid IDs `BTC-USD-260626` / `BTC-USD_UM-260626`. Repo: instruments-service (venue symbol
    map — the owning side per IS→MTDS contract).
  - **Slot-7 FULL diagnosis + LIVE-VALIDATED fix spec 2026-06-01 — root cause is in instruments-service, NOT MTDS.**
    Traced end-to-end:
    1. **Venue→exchange map is CORRECT**: UAC `registry/venue_mapping.py` + `canonical/canonical_mappings.py` map
       `OKX-FUTURES` ↔ Tardis exchange **`okex-futures`** (OKX has 3 Tardis exchanges: `okex` spot / `okex-swap` perps /
       `okex-futures` fixed-expiry — instruments-service `engine/orchestrator.py` knows this).
    2. **The `/exchanges/okex-futures` metadata endpoint is FREE (no paid key)** + authoritative — **probed live
       2026-06-01**: 5,740 `availableSymbols` with native ids `BTC-USD-260626` / `BTC-USDT-260626` / `BTC-USD_UM-260626`
       (USDT-margined = `_UM`, `YYMMDD` expiry), each carrying `availableSince`/`availableTo`. instruments-service
       already uses this pattern: `reference_data/adapters/cefi/tardis.py::_fetch_exchange_instruments`
       (`/exchanges/{exchange}`).
    3. **The bug**: MTDS futures download takes its symbol list from **instruments-service's per-date parquet** via
       `market_interface/adapters/tradfi/tardis_adapter.py::_resolve_dated_future_symbols` (IS→MTDS contract — MTDS must
       NOT hardcode the universe). For OKX-FUTURES, IS is emitting canonical `BTC-USDT`-style symbols (looks sourced
       from `okex` spot), NOT the `okex-futures` native dated ids → Tardis 400.
    4. **Fix (owner = instruments-service, the universe SSOT)**: make OKX-FUTURES discovery pull from the
       **`okex-futures`** exchange's `availableSymbols[].id` (native dated ids) filtered by
       `availableSince`/`availableTo` — the same `_fetch_exchange_instruments` path it already uses for other venues;
       confirm it keys on `okex-futures` (not `okex`/ `okex-swap`) for the FUTURE `instrument_type`. **No MTDS change**
       needed if IS emits native ids (MTDS passes `_resolve_dated_future_symbols` output straight to the okex-futures
       CSV URL). **Data-correctness gate**: dry-run validate the rebuilt OKX-FUTURES symbol set against the live free
       `/exchanges/okex-futures` listing BEFORE relaunch — never re-request unverified symbols. **Independent of the
       BLOCKED Tardis paid key** (metadata endpoint is free; only the historical CSV download needs the key). Repo:
       **instruments-service** (OKX discovery) + verify MTDS consumes unchanged.

## Code-freeze + migration window estimate

- Phase 1 (bucket symmetry audit + YAML diff): **~3 cal AI-days** (slot 2 + 3 in parallel).
- Phase 2 broadcast: 0 cal (operator action).
- Phase 3 drain: **~0.5 cal AI-days** (script-driven, slot 2 + 3 coordinate VMs).
- Phase 4 GCS migration: **~8 cal AI-days** (single-walk; per `code_freeze_migrate_backfill_sequencing_2026_05_10.md`
  Phase 2.2-2.6).
- Phase 5 AWS migration: **~5 cal AI-days** (slot 4; smaller corpus than GCP).
- Phase 6 Docker rebuild: **~2 cal AI-days** (slot 5; image build + VM restart fleet).
- Phase 7 v8 backfill + label-flip: **~8 cal AI-days** (slot 5; per writegate Phase 7 + d3_manifest_v8_finish +
  hard_schema_phase1_field_flip).
- Phase 8 unfreeze: 0 cal (operator action).
- Phase 9 denominator/numerator: **~4 cal AI-days** (slot 6; parallel with Phase 10).
- Phase 10 QG enforcement: **~3 cal AI-days** (slot 5 + 2/3).

**Total**: ~36 cal AI-days (matches frontmatter estimate). Wall-clock with parallelism: ~7-10 calendar days end-to-end
(~24-48h hard freeze window for Phases 2-8; Phase 9-10 unfrozen).

## Continuous-verification column (per CLAUDE.md HARD RULE)

| Phase | Cutover criterion                          | Continuous verification                                                   |
| ----- | ------------------------------------------ | ------------------------------------------------------------------------- |
| 1     | All AWS templates symmetric to GCP in YAML | Daily diff check via `scripts/bucket_naming/check_symmetry.sh` (to build) |
| 2     | All slots ACK in ping ledger               | Slot-1 main tally                                                         |
| 3     | Zero non-essential VMs running             | `gcloud compute instances list \| wc -l` < threshold                      |
| 4     | 100% GCS objects under new bucket names    | `gsutil ls` count match                                                   |
| 5     | 100% S3 objects under new bucket names     | `aws s3 ls` count match                                                   |
| 6     | 100% new manifest writes at v8             | Sample 100 newest rows per bucket; A4 v2 residual re-run                  |
| 7     | 100% existing manifest rows at v8 + 0 NULL | A4 v1 + A4 v2 both 100% v8                                                |
| 8     | Broadcast UNFREEZE ack'd                   | `_agent_pings.md` UNFREEZE entry                                          |
| 9     | Deployment-UI shows correct formula        | Spot-check a known bucket — math matches                                  |
| 10    | QG steps ratchet to 0 violations           | `quality-gates.sh` exit 0 workspace-wide                                  |

## Zombie watchdog + Cloud Run consolidator continuity

Per operator concern 2026-05-20 round 5: "still need zombie watchdogs and manifest aggregators to work" during the
migration window.

**Keep running during freeze**:

- `vm_zombie_watchdog.py` — keeps cleaning abandoned VMs (essential during drain).
- 10 Cloud Run consolidator jobs (`uts-prod-manifest-consolidator-*`) — keep running through Phase 3 (so drain
  consolidation completes); pause briefly during Phase 4 bucket cutover; resume after Phase 4 GREEN.
- Cloud Scheduler crons `*/1 * * * *` — Cloud Run will queue if the bucket name changes mid-poll; safe.

**Pause briefly** (Phase 4-5 only):

- Consolidator jobs pause for the actual `gsutil cp` cutover window (~few hours).
- Resume immediately after the new bucket has the migrated objects.

## Cross-side ping broadcast (slot-1 main fires this when freeze starts)

Append to `plans/active/_agent_pings.md`:

```markdown
## 🔴 2026-05-XX CODE FREEZE — data-pipeline-master-coordination Phase 2 active

**Owner**: ikenna slot-1 main (this side) ↔ harsh main (cross-side). **Plan**: `plans/active/mtds_mdps_master.md`.
**Duration**: ~24-48h hard freeze (Phases 2-8); ~7-10 day full window incl. unfrozen Phases 9-10.

**ACK checklist** (slots respond in their own ping file):

- ikenna slot 2: [ ] / ikenna slot 3: [ ] / ikenna slot 4: [ ] / ikenna slot 5: [ ]
- ikenna slot 6: [ ] / ikenna slot 7: [ ] / ikenna slot 8: [ ] / ikenna slot 9: [ ]
- harsh main: [ ] / harsh spawned: [ ]

**During freeze**: no commits to LDR; no new backfill VMs; read-only work allowed. **Watchdog + consolidator**: KEEP
RUNNING (slot-1 monitors). **Resume signal**: 🟢 UNFREEZE ping in this same file when Phase 8 lands.
```

## Composes with

- CLAUDE.md § "Data Pipeline Correctness Is The Heartbeat" — this is the operationalisation of that rule.
- CLAUDE.md § "Pre-migration drain (GCS migration gate — HARD RULE)" — Phase 3 follows that recipe exactly.
- CLAUDE.md § "Plans Run To Actual Completion" — Phase 7 v8 backfill must run to 100%, not "most rows".
- `/codex/02-data/data-pipeline-correctness-hard-rule.md` — slot-freeze protocol § Invariant 4.
- `/codex/11-project-management/foundation-completion-gate-discipline.md` — Phase ordering follows layer-N+1 gate; data
  layer (3) gates everything above.

## Why this is the operator-handoff entry point

Operator can now hand this single file to an orchestrator agent + the orchestrator:

1. Reads § "Phase reference table" top-down to know what runs first.
2. Reads each cell's plan-of-record link for implementation detail.
3. Reads § "Slot dispatch table" to know which slot owns which phase.
4. Reads the mega-audit delegation SSOT for the underlying R-items.
5. Fires the broadcast ping at Phase 2 boundary; tracks ACKs.
6. Drives each phase to GREEN before unlocking the next.

No content in referenced plans needs to be duplicated here; this plan is the **ordering + cross-cutting-concerns
layer**, not a re-statement of the work.

## Codex SSOT updates (per CLAUDE.md Post-Plan-Phase Audit)

- [x] ✅ `/codex/02-data/data-pipeline-correctness-hard-rule.md` — add pointer to this coordinator plan as the canonical
      execution-ordering reference. — pm@HEAD
- [x] ✅ `/codex/11-project-management/foundation-completion-gate-discipline.md` — cite this plan as the example of how
      layers 1-3 are sequenced together for a major migration. — pm@HEAD
- [x] ✅ CLAUDE.md § "Data Pipeline Correctness Is The Heartbeat" — path corrected `plans/active/` → `plans/epics/`
      (pointer already existed, wrong path). — pm@HEAD

## Assigned active plans

_8 active plans declare `parent_epic: mtds_mdps_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`data_completion_to_100_all_ag_2026_06_21`](../active/data_completion_to_100_all_ag_2026_06_21.md)

**status**: active · **estimate**: 8 cal AI-days (class: infra) **title**: Data completion to 100% — all asset groups,
batch + live, manifest v9 (MTDS + IS)

### [`data_source_provenance_enforcement_2026_07_24`](../active/data_source_provenance_enforcement_2026_07_24.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: Data-source provenance enforcement — all
asset groups (split from M-1)

### [`legacy_bucket_dual_write_decommission_2026_07_24`](../active/legacy_bucket_dual_write_decommission_2026_07_24.md)

**status**: active · **estimate**: 2.4 cal AI-days (class: infra) **title**: Legacy tick-bucket dual-write remediation —
decommission (split from M-1)

### [`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`](../active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md)

**status**: active · **estimate**: 9.6 cal AI-days (class: infra)

## P1 — important; post-current-gate

### [`defi_cf2_cf3_legacy_canonical_backfill_2026_08_08`](../active/defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md)

**status**: active · **estimate**: 1.8 cal AI-days (class: research) **title**: DeFi CF-2/CF-3 legacy-vs-canonical
cell-diff gaps — scope + backfill/relabel campaign

## P2 — useful; opportunistic

### [`solana_dex_pool_swaps_indexer_2026_08_08`](../active/solana_dex_pool_swaps_indexer_2026_08_08.md)

**status**: active · **estimate**: 1.0 cal AI-days (class: brand-new) **title**: Solana ORCA/RAYDIUM dex_pool_swaps
indexer — signature-walk + swap decoder + manifest write

### [`solana_dex_pool_swaps_indexer_2026_08_08_finalize`](../active/solana_dex_pool_swaps_indexer_2026_08_08_finalize.md)

**status**: active · **estimate**: 0.1 cal AI-days (class: refactor) **title**: Solana dex_pool_swaps indexer — finalize

## P3 — backlog; revisit quarterly

### [`mtds_file_size_refactor_2026_06_08`](../active/mtds_file_size_refactor_2026_06_08.md)

**status**: active · **estimate**: 2 cal AI-days (class: refactor) **title**: MTDS/MDPS tech-debt & coverage — file-size
splits + polars seam + coverage/QG residuals (survivor M-2)

## Archived plans

### [`mdps_backfill_phase3_2026_05_22`](../archive/2026_05/mdps_backfill_phase3_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — All phases shipped (DeFi/TradFi/Sports/Pred fixes + monthly TradFi sharding +
consolidator fix); 6 items DEFERRED-OPERATOR-DECISION (verify gates pending long-running VMs). · **estimate**: 2.4 cal
AI-days (class: infra)

**Deferred (MIGRATED FROM archived plan)** — P0 verify backlog:

- **MDPS-3.3.CeFi + CeFi-V (P0, BLOCKED-OPERATOR-DECISION)**: Relaunch CeFi reprocessor VM + verify NaN check; gate:
  MTDS-3.2.A-V GREEN.
- **DeFi gap-fill backfill verify (P0, IN-PROGRESS — MIGRATED FROM `defi_market_data_staleness_2026_05_24` residual
  #1)**: the recurring DeFi collection schedule is deployed (deployment-service@7b1490f, root cause fixed); the one-off
  gap-fill VMs backfilling 2024→2026-05 must complete + manifest GREEN per venue. As of 2026-05-27
  `mtds-dex-swaps-backfill` was still RUNNING (forward walk ~2026-03-25); lst-rates / lending-indices VMs done. Verify
  completion + per-venue manifest GREEN, then close. (See also `features_backfill_phase3_2026_05_22.md`.)
- **MDPS-3.3.DeFi-V (P0, ✅ GREEN — 2026-05-24)**: All 16 fixes shipped; 101628 VMs TERMINATED; manifest consolidated.
  **Verified prod state (slot-4 2026-05-24 session 2)**: 334,964 total captured rows in combined availability index;
  22,717 `swaps_ohlcv_*` rows confirmed — `UNISWAP_V3` (19,756), `UNISWAP_V2` (2,190), CURVE (771); date range
  2024-05-03 → 2026-01-24; venue field = chain-stripped (e.g. `UNISWAP_V3` not `UNISWAP_V3-ETHEREUM`) ✓.
  `lending_indices`: **bypass type** — periodic supply/borrow-index snapshot consumed raw by features-onchain
  (`aave_lending_rates` / `aave_utilization`).

  `needs_candle_processing("lending_indices") is False`, no candle adapter, 0 `lending_ohlcv_*` expected by design (same
  as `oracle_prices`/`lst_rates`). Dead `DefiLendingIndicesAdapter` deleted mdps@5c2b612.

  `gas_fees`: bypass type — no adapter, 0 captured expected by design. **MTDS 2026 DEX gap** (permanent): CURVE/UNISWAP
  `dex_swaps` handler stopped writing after 2026-01-24 → all 2026-01-25→present cells are
  `empty_confirmed/SOURCE_RETURNED_ZERO`. Issue plan archived:
  `plans/active/issues/mdps_defi_swaps_ohlcv_schema_lookup_2026_05_23.md`.

- **MDPS-3.3.TradFi-V (P0, BLOCKED-OPERATOR-DECISION)**: 7 year VMs + 64 monthly VMs RUNNING (~66h ETA). Verify VIX
  bars + manifest v8 once 2025 VM completes.
- **MDPS-3.3.Sports-V + Pred-V (P0, BLOCKED-OPERATOR-DECISION)**: VMs still RUNNING. Verify NaN check + manifest v8 once
  complete.

### [`mtds_backfill_phase3_2026_05_22`](../archive/2026_05/mtds_backfill_phase3_2026_05_22.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-5 done: CeFi/TradFi/DeFi/Sports/Predictions backfill VMs launched + DeFi
gap filled + TradFi prd gap filled + manifest consolidator terraform fixed; 2 items DEFERRED. · **estimate**: 4.0 cal
AI-days (class: infra)

**Deferred (MIGRATED FROM archived plan)**:

- **MTDS-3.2.A-V (P0, BLOCKED-PHASE7-PREREQUISITE — 4 findings, 2026-05-24)**: CeFi MTDS verify gate run 2026-05-24.
  Bucket: `market-data-tick-cefi-central-element-323112`. 34,933,247 total rows. **4 findings**:

  **Finding 1 — schema_version FIXED ✅ (2026-05-24)**: v8 upgrade ran live via `upgrade_manifest_to_v8.py`. Result:
  34,839,742 rows upgraded (32,322,206 NULL + 2,517,536 pre-v8 → all set to 8); 93,505 already at v8. 100% of rows now
  at schema_version=8.

  **Finding 2 — Legacy markers (2.09M rows) — OPEN**:
  - `bait_sentinel_may4_burst_no_parquet` (960K): attempted_failed rows from May-4 phantom burst.
    `cleanup_may4_bait_sentinels.py` already ran to create these rows. Needs MTDS retry with `VM_FORCE=true` to
    re-attempt; OR relabel as `empty_confirmed[SOURCE_RETURNED_ZERO]` if Tardis confirms data absent.
  - `LegacyBlankErrorReasonError` (674K): pre-typed-reason rows. Relabeling pass via `legacy_reason_classifier.py`
    needed.
  - `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` (452K): May-7 reconciliation markers. Need investigation to determine
    correct `EmptyConfirmedReason` or retry target.

  **Finding 3 — Fresh failures (106K rows) — OPEN**:
  - BINANCE-SPOT (15,036): all `VENUE_FETCH_FAILED`, only `book_snapshot_5`+`trades`, all years 2020–2026,
    attempted_at=2026-05-06. Likely Tardis data gaps for specific dates. Action: MTDS retry with FORCE=true OR relabel
    as `empty_confirmed[EXPECTED_NO_SOURCE_DATA]` after Tardis probe.
  - DERIBIT (51,730): split evenly across `book_snapshot_5`/`derivative_ticker`/`trades` (17,240 each), all years.
    Expected historical gaps. Action: relabel as `empty_confirmed[EXPECTED_NO_SOURCE_DATA]`.
  - HYPERLIQUID (17K approx): expected gaps. Action: same as DERIBIT.

  **Finding 4 — Bait sentinel gate**: 960K rows with `bait_sentinel_may4_burst_no_parquet` were already flipped to
  `attempted_failed` by `cleanup_may4_bait_sentinels.py` (correct). MTDS preflight now excludes
  `captured AND instrument_count==0` (MTDS@e032b186). Gate unblocked for preflight; remediation still needed.

  **Gate status**: 2 of 4 criteria FAIL (fresh failures + legacy markers). v8 criterion now GREEN. Gate remains
  BLOCKED-PHASE7-PREREQUISITE until legacy markers relabeled + fresh failures resolved. Remediation tracked in
  `plans/active/issues/cefi_manifest_remediation_2026_05_24.md`.

- **Bucket naming migration (P2, DEFERRED)**: MTDS writes to flat bucket (legacy `cloud_constants.py`); migrate in
  `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 2.6.

## Deferred work — migrated from archived plans

- [ ] [AGENT] P2. **MIGRATED FROM: plans/archive/issues/audit_2026_05_08_substantial_unfixed_items.md** — Wire
      `ResourceProfiler.on_memory_warning` into MDPS `app/core/live_workers.py`. UTL `open_candle_writer` +
      `close_candle_writer` shipped (UTL@ac6e3244); MDPS Phase 1.2 callsite migration remains open. Also:
      `ConnectivityWatchdog` event-subscriber wire-in (subscribes to `CONNECTIVITY_GAP_DETECTED` to optionally pause
      MDPS feed during gaps). Gated on MDPS-coordinated tab without foreign WIP in tree.

- [ ] [AGENT] P2. **MIGRATED FROM: plans/archive/solana_amm_coverage_expansion_2026_05_13.md +
      plans/archive/solana_perp_dex_adapters_2026_05_13.md** — Implement MTDS Solana venue coverage: (a) dex_swaps write
      path to GCS + manifest entries for METEORA-SOLANA/PHOENIX-SOLANA/JUPITER-SOLANA/LIFINITY-SOLANA (backfill script
      exists but APPLY mode raises warning until MTDS receives new venue coverage); (b) MTDS Solana perp DEX source
      wiring for all 4 venues: DRIFT (Drift S3 historical archive), MANGO V4, ZETA, FLASH REST APIs — emit
      `perp_funding` parquets. (was: "Drift S3 historical archive" framed as the intended DRIFT source — **[2026-07-12
      correction]**: `solana_defi_legacy_migration_2026_05_27.md`'s Bug-D/Bug-D-followup investigation (slot-1
      2026-05-29) confirms BOTH Drift S3 archives are dead ends — V1 ends 2025-01-08, V2 bucket
      `drift-historical-data-v2` confirmed via `ListObjectsV2` to end 2025-01-07 with no further `market/*` keys — and
      ships a Helius-based replacement instead (Option 2: persistent sig→blockTime index via
      `build_drift_v2_sig_index.py`; handler `_backfill_drift_helius_date`; shipped `mtds@0e92e49a` + `mtds@9a840e01`,
      tests green 2026-05-29). Retarget this backlog item's DRIFT source to the Helius path, not the S3 archive.
      Corrected per plan-reconciliation finding 173,
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 B-queue ruling.) Referenced issue
      `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md` was never created. **PARTIAL DONE (slot-6
      2026-05-23)**: MDPS scanner `_DEFI_DEX_VENUE_SEGMENTS` now includes ORCA-SOLANA and RAYDIUM-SOLANA venue path
      segments (MDPS@305677e). Current on-disk data is `dex_pools` (pool state snapshots), not `dex_swaps` events — MTDS
      Solana swap-event backfill is still needed before MDPS can produce candles.

## MTDS/MDPS priority-venue live-feed + candle-derivation audit (2026-08-19)

Audit scope: CeFi (Deribit, Hyperliquid, Binance, OKX, Bybit, Aster), Ethereum DeFi (AAVE V3, Lido, EtherFi), sports
(Betfair), Polymarket, Kalshi, IBKR, Morpho, Uniswap, CoW Swap. **Verified 2026-08-19**: batch/REST adapter coverage
is essentially complete for this set — every venue except CoW Swap has an MTDS batch adapter file, and MDPS has real
(non-test) candle-derivation wiring for all of them except CoW Swap and (unverified) IBKR. The genuine gap is
**live-feed** coverage, not batch:

| Venue class | Live-feed status |
| --- | --- |
| Deribit, Binance, OKX, Bybit, Hyperliquid, Aster, Kalshi, Polymarket, Morpho, Uniswap V3 | real, unauthenticated live WS/polling — confirmed working, not scaffolds |
| AAVE V3 | live leg exists but is **liquidations-only** (no live rate/market-state stream) |
| Lido, EtherFi, Betfair | **BLOCKED-CREDENTIALS scaffolds** — registered in the WS factory so a naive check reports "live-wired," but `stream()` yields zero real ticks pending paid credentials (The Graph key + Ethereum RPC WS for the two LSTs; a subscribed Betfair Developer app key + SSO session for Betfair) |
| Uniswap V2 / V4 | no confirmed live leg (only V3 is wired) |
| IBKR | no live leg at all — architecturally can't be public WS (local TWS/IB Gateway socket only); MDPS candle path is UNVERIFIED — the generic tradfi candle adapters are written against Databento's raw schema, no test/wiring names IBKR specifically |
| CoW Swap | absent end-to-end — no MTDS adapter, no MDPS wiring, batch or live |
| Jupiter (spot), Raydium, Pacifica, Jito (LST, jitoSOL) | real, unauthenticated live WS — confirmed working, not scaffolds (Solana venue set, audited 2026-08-19 alongside execution/strategy — see `execution_master.md`'s "Solana venue set" section for full per-venue detail) |
| Jito Restaking (`JITORESTAKING-SOLANA`) | batch only (`restaking_jito_adapter.py`) — **no live connector found** this pass, unlike jitoSOL; scoping (does any archetype need it live) tracked in `execution_master.md`, not duplicated here |
| Drift | absent end-to-end — operator-killed 2026-07-16, reaffirmed 2026-08-14; **this session's operator request named Drift for reuse, a genuine conflict with that standing ruling** — the reconciliation todo lives in `execution_master.md` (`[OPERATOR]` tag), not duplicated here |

- [ ] [DATA] P2. **AAVE V3 — extend the live leg beyond liquidations-only.** `live/connectors/aave_liquidations_
      ethereum_ws.py` is real (OnChainEventPoller on `eth_getLogs`, ~12s poll) but only serves liquidation events; no
      live rate/market-state stream exists. Scope: does a live rate/utilization stream matter for the MVP archetype
      set, or is liquidations-only sufficient? If it matters, build it; if not, state that explicitly rather than
      leaving the gap unexplained.
- [ ] [DATA] P1. **Lido / EtherFi / Betfair — the live-WS scaffolds are dated 2026-07-07 and still credential-
      gated.** All three share `live/connectors/_defi_ws_blocked_credentials_base.py`'s pattern (Lido/EtherFi need a
      paid The Graph key + Ethereum-RPC WS; Betfair needs a subscribed Developer app key + SSO session — "no
      public/free tier"). Per the External-data-always-available rule, the scaffold itself is correct (built ahead
      of credentials); this is a credential-provisioning ask, not a build gap. Betfair specifically cross-references
      `/plans/active/issues/prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md` (1 open / 3 done) —
      that doc's live routing/fixture-mapping scope is broader than just the credential unblock, don't duplicate its
      tracking, just note the credential dependency here.
- [ ] [DATA] P2. **Uniswap V2 / V4 — no confirmed live leg, only V3 is wired** (`dex_swap_uniswap_v3_ws.py`
      deliberately polls the same subgraph the batch adapter reads, not raw `eth_subscribe`, to keep
      paper(W)==batch-rerun(W) parity — the other 21 scaffold venues in `dex_swap_scaffold_ws.py` remain untouched).
      Scope: does the MVP archetype set trade V2/V4 pools, or is V3-only sufficient for now? State explicitly either
      way rather than leaving V2/V4 silently uncovered.
- [ ] [DATA] P2. **IBKR — MDPS candle-derivation path is UNVERIFIED, not confirmed passing.** MTDS's IBKR batch
      adapter (`market_interface/adapters/tradfi/ibkr_adapter.py`) is marked `ENDPOINT_STATUS: IMPLEMENTED` (via a
      local TWS/IB Gateway socket, not a public API — architecturally can never have a live WS leg the way other
      venues do). MDPS's generic tradfi candle adapters (`tradfi/{trades_adapter,tbbo_adapter,ohlcv_passthrough}.py`)
      are registered by `MarketAssetGroup.TRADFI` + data_type (venue-agnostic) but their docstrings are explicitly
      written against Databento's raw schema — no test or wiring names IBKR at all. Done-when: either a passing
      test proves IBKR's `IBKRBar`/`IBKRTicker` shard shape parses cleanly through the generic tradfi adapters, or a
      dedicated IBKR candle path is built.
- [ ] [DATA] P1. **CoW Swap — genuinely greenfield end-to-end, confirmed 2026-08-19** (zero hits for
      "cowswap"/"cow_swap"/"cow swap" anywhere in MTDS or MDPS — no batch adapter, no live connector, no candle
      wiring; nothing to process since MTDS never writes CoW Swap raw shards). **This is not optional polish — it's
      required for batch=live=paper determinism** (CLAUDE.md "Live = batch (event-log spine)...
      paper(W)==batch-rerun(W) epsilon=0"; operator's explicit question this session: "we also need to have
      historical data for CoW batch-live symmetry... otherwise we can't replay the market data"). A live-only CoW
      Swap adapter with no MTDS/MDPS historical capture means the venue can never be backtested or paper-simulated.
      Build the MTDS batch adapter + candle-derivation wiring once the execution-service CoW Swap adapter (see
      `execution_master.md`) establishes what data shape is needed; sequence data build after or alongside
      execution build, not before it's clear what the venue's actual quote/settlement data shape looks like. Follow
      the existing MTDS backfill pattern other DEX venues already use (Uniswap/Raydium's batch adapter + candle
      wiring shape above) — don't invent a new one.
- [ ] [BACKEND] P2. **General principle, applied here as the concrete instance**: any genuinely greenfield venue
      built with a live execution adapter but no MTDS/MDPS historical capture is a batch=live=paper determinism gap,
      not just a CoW Swap-specific one. Checked against the rest of this session's priority-venue audits (CeFi,
      Ethereum DeFi, Solana): every other greenfield-adjacent build already sequences MTDS batch+live alongside
      execution (see the Pacifica/Jupiter-Kamino plans' own UAC→IS→MTDS→execution→strategy ordering) — CoW Swap is
      the one case that doesn't yet, which is why it gets its own explicit todo above rather than an assumption.
      Pointer only, not a duplicate SSOT — see also `system_readiness_master.md`'s W1/W2 readiness-dimension note.
