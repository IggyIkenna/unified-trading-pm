---
name: mtds_mdps_master
title: "Data pipeline master coordination — 2026-05-20"
type: epic
tier: L1
status: active
priority: P0
assigned_vm: vm-ml
parent: master_to_live_defi_2026_05_23
created: 2026-05-20
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-20
related_plans:
  - ../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md
  - ../archive/2026_05/d4_mtds_adapters_preflight_2026_05_20.md
  - ../archive/2026_05/dex_perp_and_venue_data_expansion_2026_05_12.md
  - ../archive/2026_05/dex_perp_onboarding_handover_2026_05_07.HANDOVER.md
  - ../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md
  - ../archive/2026_05/mdps_streaming_and_backpressure_2026_05_07.md
  - ../archive/2026_05/mtds_databento_path_streaming_2026_05_07.md
  - ../archive/2026_05/mtds_per_instrument_download_api_2026_04_24.md
  - ../archive/2026_05/scratch_codefreeze_phase4_mtds_fanout_2026_05_12.md
  - ../active/wave3x_track_d_implementation_2026_05_19.md
  - strategy_repo_consolidation_2026_05_19.md
  - ml_repo_consolidation_2026_05_19.md
  - features_repo_consolidation_2026_05_08.md
  - strategy_execution_contract_remediation_2026_05_20.md # operator bucket-strategy decision lines 378/384/388
  - bucket_name_ssot_canonicalisation_2026_05_10.md
  - code_freeze_migrate_backfill_sequencing_2026_05_10.md
  - aws_migration_defi_first_2026_05_07.md
  - gcs_migration_bundle_pipeline_mode_2026_05_08.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
  - d3_manifest_v8_finish_2026_05_20.md
  - manifest_cross_asset_rescan_design_2026_05_08.md
  - manifest_schema_final_gate_2026_05_09.md
  - hard_schema_phase1_field_flip_migration_2026_05_19.md
  - honest_coverage_formula_consolidation_2026_05_19.md
  - data_status_drilldown_shard_atom_alignment_2026_05_07.md
  - archive/2026_05/canary_coverage_qg_enforcement_2026_05_20.md # ✅ ARCHIVED 2026-05-21 (all 20/20 items done)
  - deployment_ui_lifecycle_tabs_2026_05_08.md
  - issues/deployment_api_shard_detail_gcs_locked_2026_05_17.md
  - audit/results/mega_audit_phase_a_issues_human_readable_2026_05_20.md
  - audit/results/manifest_v8_compliance_2026_05_20_summary.md
  - audit/results/manifest_v8_per_vm_shards_2026_05_20_summary.md
  - audit/results/manifest_divergence_2026_05_20_summary.md
  - audit/results/manifest_divergence_all_services_2026_05_20_summary.md
  - audit/is_mtds_contract_audit_2026_05_20.md
  - audit/mtds_features_contract_audit_2026_05_20.md
  - audit/mtds_strategy_contract_audit_2026_05_20.md
  - audit/strategy_execution_contract_audit_2026_05_20.md
  - audit/utl_consumer_contract_audit_2026_05_20.md
  - audit/uac_consumer_contract_audit_2026_05_20.md
  - ../../codex/02-data/data-pipeline-correctness-hard-rule.md
  - ../../codex/05-infrastructure/manifest-consolidator-ssot.md
  - ../../codex/11-project-management/foundation-completion-gate-discipline.md
---

# Data pipeline master coordination — 2026-05-20

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

1. **0% of 7.4M manifest rows at v8** ([A4](../audit/results/manifest_v8_compliance_2026_05_20_summary.md)). Confirmed
   writer-fleet-stale (residual analysis excludes 42 one-off shards; residual 3,853 shards still 100% v<8) — Docker
   images deployed to VMs built before the v8 constant bump.
2. **236,892 `MISSING_EXPECTED` + 765 `DIVERGENT_EMPTY` cells** across MTDS
   ([A3](../audit/results/manifest_divergence_2026_05_20_summary.md)).
3. **AWS bucket naming asymmetric to GCP** — naming convention drift: GCP
   `market-data-tick-defi-prd-central-element-323112` vs AWS `unified-trading-market-data-defi-427895769566` (no env
   tier; extra `unified-trading-` prefix). 62-char limit drove `prd` over `prod` on GCP per
   [bucket_name_ssot_canonicalisation_2026_05_10.md](bucket_name_ssot_canonicalisation_2026_05_10.md); AWS needs the
   same treatment for code-path identity.
4. **16 service buckets without consolidated manifest**
   ([A3 v2](../audit/results/manifest_divergence_all_services_2026_05_20_summary.md)) — 14 empty (Group B env-split
   rollback) + 2 with non-manifest data (execution-store-cefi, ml-training-artifacts).
5. **Hybrid consolidator runtime** (legacy GCE VM + 10 Cloud Run jobs) — resolved 2026-05-20: legacy VM deleted
   (deployment-service@73183b7), Cloud Run is canonical per
   [codex/05-infrastructure/manifest-consolidator-ssot.md](../../codex/05-infrastructure/manifest-consolidator-ssot.md).
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

| Phase                                                                                                                                   | Plan(s)-of-record                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Owner slot                                                                                                                                                        | Pre-req                               | Verification (when done)                                                                                                                                                                                                                                                              |
| --------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **-2. Strategy/ML/Features consolidation finish**                                                                                       | `strategy_repo_consolidation_2026_05_19.md` (Phase 11 cleanup — 30/31 base done; sub-phases 11a-11h appended by separate agent) + `ml_repo_consolidation_2026_05_19.md` (Phase 11 same structure) + `features_repo_consolidation_2026_05_08.md`. **Outstanding work** (per operator write-up 2026-05-20 round 5): ✅ **Bucket 1 DONE 2026-05-20**: `gh repo archive` executed for `ml-training-service` + `ml-inference-service` (`isArchived: true` confirmed via gh api). ✅ **Bucket 2 DONE 2026-05-20**: operator chose **unified bucket** for `strategy-store` — `strategy_execution_contract_remediation_2026_05_20.md` Phase 4a/4b unblocked; migration bundled into master coordinator Phase 1. 🟡 **Bucket 3** 545 stale refs to 5 archived services across 12 consumer repos (~50-150 real cleanup items) — separate-agent per-slot pings already dispatched to ikenna slots 3-8 with P0/P1 priority; **~4.75 cal AI-days fan-out**. 🟢 **Bucket 4 ACKED**: `strategy_archetype_logic_audit_2026_05_20` re-prioritised P0 + authorised to run **TONIGHT 2026-05-20 in parallel** with Phase 11 cleanup tail (operator round 5: "mostly done anyway"). Requires **Opus 4.7 (1M context)** — separate session. | Bucket 3: separate agent's slot dispatch (slots 3-8 per `ikenna_orchestrator/pings/slot_{3..8}.md`). Bucket 4: dedicated Opus-1M session (operator-orchestrated). | —                                     | Buckets 1+2 ACKED+DONE; Bucket 3 grep returns 0 real-cleanup hits across slots 3-8 dispatch; Bucket 4 strategy_archetype_logic_audit produces audit doc + R-items                                                                                                                     |
| **-1. Workspace-wide QG green**                                                                                                         | NEW CLAUDE.md HARD RULE this round + per-repo `bash scripts/quality-gates.sh` exit 0. **Round 6 ownership update 2026-05-20** (Harsh offline India tz): re-assigned to **Ikenna slots 9, 10, 11 BACKGROUND** (operator-choice: Ikenna AWS VM or local laptop) per `work_split_2026_05_20_ikenna.md` § Slots 9-11 with cluster split (A: UAC+UTL+IS / B: MTDS+features+MDPS / C: strategy+execution+ml — strategy under LOGIC-freeze, surface-only fixes). When Harsh wakes, Harsh-side slots resume QG ownership; slots 9-11 hand off via git rebase.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **Ikenna slots 9, 10, 11** (Harsh slots resume on his next online window)                                                                                         | Phase -2 GREEN                        | Every active repo: `bash scripts/quality-gates.sh` exit 0; QG-green evidence line on every PR going forward; 9 repos GREEN (3 per cluster × 3 slots)                                                                                                                                  |
| **0. Pre-flight audits**                                                                                                                | `audit/results/mega_audit_phase_a_issues_human_readable_2026_05_20.md` + the 6 contract audits in `audit/`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | slot-1 main (mega-audit owner — already DONE round 4)                                                                                                             | Phase -1 GREEN                        | All R-items in mega-audit § 6 have named owner + plan; this file exists                                                                                                                                                                                                               |
| **1. AWS↔GCP bucket-name symmetry audit + fix**                                                                                         | `bucket_name_ssot_canonicalisation_2026_05_10.md` (extension) + see new § "Phase 1 — bucket symmetry" below                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | **Slot 2 + Slot 3** (code_freeze owners — closest to bucket plumbing)                                                                                             | Phase 0 GREEN                         | A3 v2 re-run: AWS bucket names match GCP template (env-tier present, no `unified-trading-` prefix), all ≤63 chars                                                                                                                                                                     |
| **2. CODE FREEZE WINDOW**                                                                                                               | This plan § "Phase 2 — code freeze protocol"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | **Slot 1 main** (operator triggers; main broadcasts)                                                                                                              | Phase 1 GREEN                         | All non-freeze slots ACK'd in `_agent_pings.md`; zombie watchdog + Cloud Run consolidators still RUNNING                                                                                                                                                                              |
| **3. VM fleet drain**                                                                                                                   | `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.0 Stage 0 (existing)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | **Slot 2 + Slot 3**                                                                                                                                               | Phase 2 active                        | All non-essential VMs STOPPED; per-VM shards consolidated; manifest snapshot under `_index/snapshots/pre_migration_2026_05_XX.parquet`                                                                                                                                                |
| **4. GCS bucket migration**                                                                                                             | `code_freeze_migrate_backfill_sequencing_2026_05_10.md` § Phase 2.2-2.6 + `gcs_migration_bundle_pipeline_mode_2026_05_08.md` (single-walk discipline)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | **Slot 2 + Slot 3**                                                                                                                                               | Phase 3 GREEN                         | Every GCS object lives under the new env-tiered bucket; `resolve_bucket_name()` returns the new bucket name for all kinds                                                                                                                                                             |
| **5. AWS bucket migration**                                                                                                             | `aws_migration_defi_first_2026_05_07.md` (extension) + see § "Phase 5 — AWS migration" below                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | **Slot 4** (api_keys owner — adjacent to AWS credentials work)                                                                                                    | Phase 4 GREEN                         | AWS bucket names match GCP template (per Phase 1 audit); s3:// objects migrated to new bucket names                                                                                                                                                                                   |
| **6. Docker rebuild + redeploy**                                                                                                        | `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7.A (extended this session to diagnose Docker staleness FIRST)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **Slot 5** (writegate owner; R6 in mega-audit)                                                                                                                    | Phase 5 GREEN                         | Sample 100 newest manifest rows per bucket; ALL at `schema_version=8` (steady-state writers confirmed deployed)                                                                                                                                                                       |
| **7. Manifest v8 backfill + label-flip (SCHEMA + LABELS clean — operational data backfill comes in Phase 11 ONLY after this is GREEN)** | `writegate_honest_coverage_endtoend_2026_05_06.md` § Phase 7.B/7.C/7.D + `d3_manifest_v8_finish_2026_05_20.md` + `hard_schema_phase1_field_flip_migration_2026_05_19.md` (label-flip). **Scope** (HARD ORDER): (a) migrate every v<8 row → v8 schema; (b) flip every bad/blank `empty_confirmed.reason` to typed `EmptyConfirmedReason` enum value; (c) **triage the 765 `DIVERGENT_EMPTY` cells from A3** — per-cell decision: cells that were captured-but-mislabelled → label-flip to `captured` HERE in Phase 7; cells where the adapter genuinely returned 0 + needs re-fetch → mark for **Phase 11** consumption. **NO data backfill in Phase 7 — only label/schema correctness on existing rows.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | **Slot 5**                                                                                                                                                        | Phase 6 GREEN                         | A4 re-run: 100% v8 + 0 NULL across all 10 buckets; label-flip-bad-rows reconciler outputs 0 mismatches; DIVERGENT_EMPTY triage CSV produced with per-cell classification (label-flip-applied vs Phase-11-rebackfill vs operator-scope)                                                |
| **8. Code-freeze release**                                                                                                              | This plan § "Phase 8 — release protocol"                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **Slot 1 main**                                                                                                                                                   | Phase 7 GREEN                         | Broadcast UNFREEZE ping; resume slot themes per `work_split_2026_05_19_ikenna.md`                                                                                                                                                                                                     |
| **9. Denominator/numerator fix in deployment-UI**                                                                                       | `honest_coverage_formula_consolidation_2026_05_19.md` + `data_status_drilldown_shard_atom_alignment_2026_05_07.md` + `deployment_ui_lifecycle_tabs_2026_05_08.md` (post-unfreeze)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | **Slot 6** (deployment-UI owner — unfrozen after Phase 8)                                                                                                         | Phase 8 GREEN                         | UI shows: numerator = `captured` cells; denominator = `captured + empty_confirmed + attempted_failed + expected_unattempted` (everything we tried OR could have tried). Out-of-scope cells NOT in denominator                                                                         |
| **10. QG enforcement upgrade**                                                                                                          | `canary_coverage_qg_enforcement_2026_05_20.md` (existing) + extend with manifest-v8 QG step + upstream-dep-check QG step                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **Slot 5** + **Slot 2/3**                                                                                                                                         | Phase 8 GREEN (parallel with Phase 9) | New QG steps: (a) `check_manifest_v8_writer_runtime.py` (samples recent writes for v8); (b) `check_dependency_fail_propagation.py` (per A5 findings); both ratchet to 0 violations workspace-wide                                                                                     |
| **11. Backfill to 100% per asset_group (OPERATIONAL data — runs against the now-clean v8 + correctly-labelled manifest from Phase 7)**  | mega-audit § 6 R1-R5 (DeFi 184k + Sports 25k + CeFi 16k + TradFi 7k + Prediction 3k MISSING_EXPECTED) + the **Phase-11-rebackfill** subset of DIVERGENT_EMPTY cells from Phase 7's triage CSV + `defi_upstream_46day_full_backfill_2026_05_16.md` extended + per-asset-group epic banners. **Every new row lands at v8 + typed reason** (Phase 6 Docker rebuild + Phase 7 schema clean ensure this).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Slots 6 / 7 / 9 (unfrozen post Phase 8); slot 5 owns v8-correctness verification + per-batch sample-check (assert all newly-written rows at v8)                   | Phase 10 GREEN                        | A3 re-run per asset_group: 0 `MISSING_EXPECTED` cells without operator-acked `BLOCKED-*` status; 0 `DIVERGENT_EMPTY` residual (all cleared by Phase 7 triage OR Phase 11 re-backfill); numerator/denominator ratio per asset_group ≥ 99% (until proven otherwise per Phase 9 formula) |
| **12. Live-data adapter completion (master plan)**                                                                                      | NEW master plan: `live_data_adapter_master_2026_05_20_or_later.md` (operator-authorise creation). Covers every venue × data_type having a live equivalent — see A6 batch-live parity findings + mega-audit R17 (13 BATCH_ONLY cells + 146 MISSING_BOTH triaged). Plus live pipeline: `live_pipeline_mtds_mdps_features_2026_05_08.md` (existing) extended                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Slot 4 (live wiring; already in api_keys+defi_recursive_borrow theme) + slot 5 (live writer parity)                                                               | Phase 11 GREEN for the batch side     | A6 re-run: 0 BATCH_ONLY cells (every venue × data_type has matching live adapter); live adapters confirmed running with manifest emission @ v8                                                                                                                                        |
| **13. Batch-live symmetry verification**                                                                                                | `batch_live_symmetry_2026_05_10.md` (existing, extended this audit round) + new sub-plan if needed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Slot 3 (already owns batch_live_symmetry T1-3); slot 9 owns T4-7 post-unfreeze                                                                                    | Phase 12 GREEN                        | Live adapter can be started at any time for strategy-service consumption WITHOUT pricing-data gaps; batch-live formula identical across modes (per CLAUDE.md `Batch = Live (CRITICAL)`); cross-mode reconciler exit 0                                                                 |
| **14. Strategy + execution deployment topology cleanup**                                                                                | `strategy_execution_contract_remediation_2026_05_20.md` (existing) + `strategy_repo_consolidation_2026_05_19.md` residuals + execution-service deployment topology plans                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Slot 5 (writegate + strategy is already there) + slot 8 (defi_catalogue close → defi_execution wiring)                                                            | Phase 13 GREEN                        | Strategy + execution deployment topology validated end-to-end with the new bucket layout + manifest v8 + live adapters. Ready-state for paper-trade → live-trade promotion per `promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`                                              |

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
- [ ] ikenna slot 3 — NO ACK YET; migrate-flat-to-env-tiered.sh still MISSING
- [x] ikenna slot 4 — pm@b313ea37d "slot-4 ACK freeze + wave2 all-done status"
- [ ] ikenna slot 5 — NO ACK YET
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
- `codex/02-data/data-pipeline-correctness-hard-rule.md` — slot-freeze protocol § Invariant 4.
- `codex/11-project-management/foundation-completion-gate-discipline.md` — Phase ordering follows layer-N+1 gate; data
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

- [x] ✅ `codex/02-data/data-pipeline-correctness-hard-rule.md` — add pointer to this coordinator plan as the canonical
      execution-ordering reference. — pm@HEAD
- [x] ✅ `codex/11-project-management/foundation-completion-gate-discipline.md` — cite this plan as the example of how
      layers 1-3 are sequenced together for a major migration. — pm@HEAD
- [x] ✅ CLAUDE.md § "Data Pipeline Correctness Is The Heartbeat" — path corrected `plans/active/` → `plans/epics/`
      (pointer already existed, wrong path). — pm@HEAD

## Assigned active plans

_10 active plans declare `parent_epic: mtds_mdps_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate

### [`d4_mtds_adapters_preflight_2026_05_20`](../archive/2026_05/d4_mtds_adapters_preflight_2026_05_20.md)

**status**: ✅ ARCHIVED 2026-05-21 — Phases 1-4 done; 8 BATCH_ONLY cells BLOCKED-OPERATOR-DECISION
(hyperliquid/aster/curve/jito/morpho/kalshi/polymarket) · **estimate**: 2.4 cal AI-days (class: infra) **title**: D4 —
MTDS adapters preflight + batch-live parity

### [`live_pipeline_mtds_mdps_features_2026_05_08`](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)

**status**: active

## P1 — important; post-current-gate

### [`dex_perp_and_venue_data_expansion_2026_05_12`](../archive/2026_05/dex_perp_and_venue_data_expansion_2026_05_12.md)

**status**: ✅ ARCHIVED 2026-05-21 · **estimate**: 8 cal AI-days (class: brand-new)

### [`mdps_streaming_and_backpressure_2026_05_07`](../archive/2026_05/mdps_streaming_and_backpressure_2026_05_07.md)

**status**: active · **estimate**: 3.0 cal AI-days (class: design)

### [`mtds_databento_path_streaming_2026_05_07`](../archive/2026_05/mtds_databento_path_streaming_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-21 — 100% complete (0 open todos); all Databento path-streaming phases done ·
**estimate**: 1.2 cal AI-days (class: design)

## P2 — useful; opportunistic

### [`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md)

**status**: active · **estimate**: 1.5 cal AI-days (class: design) **title**: available_at + lookahead-bias master —
SINGLE OWNER for all stamping work

### [`dex_perp_onboarding_handover_2026_05_07.HANDOVER`](../archive/2026_05/dex_perp_onboarding_handover_2026_05_07.HANDOVER.md)

**status**: ✅ ARCHIVED 2026-05-21 — all tracked checkboxes done; follow-on expansion also archived · **estimate**: 6
cal AI-days (class: design)

### [`mtds_per_instrument_download_api_2026_04_24`](../archive/2026_05/mtds_per_instrument_download_api_2026_04_24.md)

**status**: active · **estimate**: 4.8 cal AI-days (class: design)

### [`scratch_codefreeze_phase4_mtds_fanout_2026_05_12`](../archive/2026_05/scratch_codefreeze_phase4_mtds_fanout_2026_05_12.md)

**status**: active · **estimate**: 0.8 cal AI-days (class: refactor)

### [`wave3x_track_d_implementation_2026_05_19`](../active/wave3x_track_d_implementation_2026_05_19.md)

**status**: active · **estimate**: 8 cal AI-days (class: brand-new)

## P3 — backlog; revisit quarterly

_(no plans currently assigned at this priority)_
