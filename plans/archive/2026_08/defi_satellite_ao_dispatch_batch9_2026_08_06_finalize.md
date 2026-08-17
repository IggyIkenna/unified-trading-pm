---
doc_type: plan
title: DeFi satellite AO batch 9 — finalize (reconcile 17 source docs + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch9_2026_08_06.md — machine-held via depends_on + gate_on_depends:
  true until every one of that plan's 18 todos is done. Mirrors batch1-8-finalize: reconcile each of the 18 source docs
  (flip/cite the item each batch9 todo closed), re-check the 2 conflict-parked Deferred items + the 33 non-batchable
  Deferred items for whether any blocking condition has since cleared, then archive batch9 via the standard 6-step
  ritual.
status: complete # (was: active) 2026-08-17 archival: all 3 todos done, no locked_by
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-9, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
depends_on: [defi_satellite_ao_dispatch_batch9_2026_08_06]
gate_on_depends: true
source: >-
  `/ag-closeout-audit defi` run 2026-08-06 (autonomous, scheduled ag_closeout_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 9 — finalize

> **🟢 ARCHIVED 2026-08-17** — all 3 todos done, no `locked_by`. Source-doc reconciliation (todo 1), the Deferred-item
> re-check (todo 2), and batch9's own archival (todo 3) are all complete — see each todo's own evidence below.
> Successor: none — self-contained gated closeout, no follow-up work spawned. Original path:
> `plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06_finalize.md`.

**status: active — gated on batch9's 18 todos via `depends_on` + `gate_on_depends: true`; the dispatcher will not
release these until batch9 is fully done.** (Batch9 itself stays `status: draft` until the operator approves dispatch —
this finalize plan needs no separate flip, `gate_on_depends` holds it correctly either way per the "no double gate"
finding in `cursor-configs/skills/ag-closeout-audit/SKILL.md`.)
**BANNER-FIXED 2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0)**: the "batch9 stays status: draft"
claim above is stale — `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s actual frontmatter is
`status: active — operator-approved 2026-08-06, dispatching`, and all 18 of its todos are now `[x]`. This finalize
plan's gate is clear and it is ready for dispatch.

## Todos

- [x] ✅ [DOC] P1. **Source-doc reconciliation** — **DONE 2026-08-16 (slot 23, data_engineering).** **Count correction**:
      batch9 actually carries **18** top-level `- [x]` todo checkboxes (`grep -c '^- \[x\]' defi_satellite_ao_dispatch_batch9_2026_08_06.md`
      = 18), not 17 as this doc's own text and batch9's frontmatter summary both claimed — the "17 distinct todos"
      count is stale/miscounted; leaving the number here would just re-rot it, so it's corrected in this entry rather
      than repeated. Checked all 18 source docs against their citing batch9 todo:
      - **16/18 already correctly closed-by-citation or self-closed**, no action needed: `canonical_id_builder_retrofit_checklist_2026_07_08.md`
        (archived, resolved), `defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`
        (archived, explicit batch9 citation), `defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md`
        (items 1-4 + item-4 audit shipped, only the genuinely-separate `[HUMAN]` backfill-decision item remains open),
        `defi_clean_path_fetch_evidence_fidelity_scope_2026_07_28.md` (archived, explicit citation),
        `defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md` (archived, resolved),
        `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` (explicit citation, closed-by-citation not
        reclassified, by design), `defi_lst_yields_coverage_extension_gcs_verified_2026_07_28.md` (archived, resolved),
        `data_pipeline_check_mdps_features_2026_07_20.md` todo 15 (full terminal-outcome evidence confirmed present at
        lines 911-914, matching batch9's own claim), `delta_one_get_available_instruments_unscoped_candle_data_types_2026_07_30.md`
        (archived, explicit citation), `mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` (archived,
        `status: complete`, explicit citation), `mtds_instruments_metadata_hive_canonicalisation_reader_gap_2026_07_26.md`
        (Follow-ups section shows todo 9(b-c) closed 2026-08-09 slot-28, matching batch9's own citation),
        `mtds_qg_red_uac_capability_declaration_drift_2026_08_05.md` (archived, resolved),
        `vault_share_price_handler_manifest_missing_instrument_id_2026_07_31.md` (MORPHO_VAULTS follow-up
        independently resolved 2026-08-16 by a separate slot-24 session, consistent with batch9's own "stays open per
        alternate done-when" framing), `data_completion_defi_2026_07_15.md` (explicit citation),
        `instruments_docs_audit_outstanding_items_2026_07_08.md` (explicit citation, C4 corrected), and the
        self-contained "Document collateral down-sizing contract" todo (no separate source doc — closes by its own
        cited commit SHAs).
      - **2/18 had a genuine orphaned-citation gap — FIXED this run**: (1)
        `defi_track5_coverage_mvp_backfill_2026_07_24.md`'s "Confirm the launcher + parallelization plan" todo (its
        Todo-3-position item) was still `[ ]` open with a stale 2026-08-03 na-eligibility-audit "not closing" note,
        even though batch9 todo 11 had already answered its exact done-when (launcher + concurrency figure) —
        flipped `[x]` with a citation back to batch9 todo 11. (2)
        `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`'s 2026-08-06 na-eligibility-audit entry
        flagged "1 untracked prose-only item (CLI/operator plumbing…)" as incidental/not-actioned — appended a
        closing citation to batch9 todo 5's shipped `strategy-service@8ee9894e` CLI flags, which is exactly that
        item. Both edits are pure append/checkbox-flip, no existing prose deleted (per the shared-doc anti-overwrite
        rule). Evidence: unified-trading-pm@(this commit).
      Zero remaining orphaned "still looks open" gaps found against batch9's 18 todos.
- [x] ✅ [DOC] P2. **Re-check the Deferred items — DONE 2026-08-17 (slot 14, data_engineering).** Live-verified every
      one of the 2 parked + 33 non-batchable items against current corpus state (file existence, `status:`, open-todo
      count, archival banners) rather than trusting batch9's 2026-08-06 snapshot.
      **(a) Both conflict-parked items CLEARED — no new batch10 park needed:**
      1. `issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`'s stall diagnosis — the doc's own item
         3 (`lending_indices` capture stall) was root-caused + fixed 2026-08-14 (slot-5): Cloud Run Job OOM/timeout on
         unbounded `ManifestFreshnessCache.bulk_load()`, fixed via `market-tick-data-service@4925f88d73` +
         `deployment-service@21e6814616`. batch9's exact parked claim ("diagnose the stall") is `[x]` DONE in the source
         doc. One narrower follow-up item remains (verify the fix post-image-redeploy) — correctly still `assigned_vm:
         NA` per that doc's own 2026-08-16 na-eligibility-audit KEEP-NA verdict; not the item batch9 parked, so no new
         batch10 todo needed.
      2. `issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md`'s split-vs-alternative question — the gating
         doc `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md` is ARCHIVED
         (`plans/archive/2026_08/issues/`), operator ruled **option A** 2026-08-06, shipped
         (`unified-trading-pm@d4f7fab9d8`, marker-only line-cap carve-out), all 3 todos done. The parked doc itself is
         now ARCHIVED 2026-08-15 (`plans/archive/2026_08/issues/`, all todos done — VM relaunch + 3 stale-checkbox
         closes applied, extraction downgraded to P3 soft-cap hygiene). Fully resolved, no new batch10 action.
      **(b) 33 non-batchable items — verdict per item (grouped, not restated individually where the disposition is
      identical):**
      - **10 already ARCHIVED (all confirmed `status: resolved/complete`, all todos done) — CLEARED, no batch10
        action**: `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md`,
        `issues/defi_catalog_dp_catalog_001_shrink_blocked_2026_08_02.md`,
        `issues/defi_hyperliquid_residual_manifest_rows_2026_08_04.md`,
        `plans/archive/issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (already archived when
        batch9 cited it), `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`,
        `issues/features_service_manifest_coverage_gap_2026_08_03.md` (archived 2026-08-16),
        `issues/lighter_tardis_writerless_route_hang_2026_07_28.md`,
        `/plans/archive/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` (already archived when
        cited), `issues/defi_bridge_events_historical_backfill_gap_2026_07_28.md`,
        `plans/archive/issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md` (already archived when cited),
        `issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05.md`.
      - **4 with 0 open todos but not yet archived (functionally done, pending a separate archival sweep — not this
        finalize's job, matches batch9's own "30 archivable_now, out of scope" note)**: `defi_venue_lst_rates_residual_2026_07_24.md`,
        `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`,
        `issues/features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md`,
        `issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`.
      - **19 still genuinely open, STILL HELD — correctly gated, no clearing found**: `defi_migration_audit_log_2026_07_24.md`
        (7 open todos remain correctly gated after today's 2026-08-17 na-eligibility-audit per-todo split already
        extracted its 5 clearable items to `defi_satellite_ao_dispatch_batch16_2026_08_17.md`, independent of this
        pass — no duplicate batch10 action), `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`,
        `issues/defi_adapter_dead_code_audit_2026_07_24.md`,
        `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md`,
        `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`,
        `issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`,
        `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`,
        `issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md`,
        `issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md`,
        `issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` (2026-08-16 na-audit re-confirmed KEEP-NA),
        `lst_rate_honest_coverage_2026_07_21.md` (2 items remain correctly KEEP-NA after today's 2026-08-17
        na-eligibility-audit per-todo split already extracted its 2 clearable items to the same
        `defi_satellite_ao_dispatch_batch16_2026_08_17.md` — no duplicate action), `issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`,
        `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`,
        `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`,
        `issues/mtds_gas_fees_migration_script_unbounded_memory_2026_07_30.md`,
        `issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
        `issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`,
        `issues/defi_cefi_venue_chain_axis_contamination_2026_07_28.md` (time_gated — not yet re-triageable).
      **Net: zero new batch10 candidates.** Everything that genuinely cleared since 2026-08-06 was already
      independently actioned by the standing daily `/na-eligibility-audit` cadence (which runs this exact corpus more
      frequently than this gated finalize) into `defi_satellite_ao_dispatch_batch16_2026_08_17.md` — drafting a
      redundant batch10 here would create the exact duplicate-dispatch hazard
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3 exists to prevent. Repo:
      unified-trading-pm.
- [x] ✅ [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch9_2026_08_06.md` — DONE 2026-08-17 (slot 14,
      data_engineering).** All 6 ritual steps: (1) every Deferred item from todo 2 above has an explicit still-held/
      cleared verdict recorded there — no orphaned prose, zero new batch10 candidates needed since the standing
      `/na-eligibility-audit` cadence already independently actioned everything that cleared, into
      `defi_satellite_ao_dispatch_batch16_2026_08_17.md`; (2) archived-banner + `plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md`
      original-path cross-reference added to the archived doc's top; (3) post-phase codex audit — batch9's own todo 2
      already shipped the relevant codex updates in-flight (`/codex/04-architecture/token-wrapping-and-collateral.md`
      § "USDC Margin Buffer", `/codex/09-strategy/architecture-v2/capability-wizard.md` § "Collateral down-sizing
      param"); nothing further to update — this finalize/archival pass itself established no new durable contract; (4)
      no new CLAUDE.md contract needed — routine dispatch-batch closeout, no new workspace rule emerged; (5) every
      corpus referrer fixed: `plans/active/INDEX.md` + the inventory dashboard regenerated via
      `scripts/plans/regenerate_active_plan_index.py` / `regenerate_active_plan_inventory.py` (batch9 entries dropped
      automatically), `plans/epics/defi_master.md`'s child-plan list + status roll-up hand-updated (batch9 + this
      finalize doc removed, matching the convention already used for batch8), path refs fixed in
      `defi_satellite_ao_dispatch_batch11_2026_08_09.md`, `issues/defi_mdps_candle_backfill_fleet_outcome_2026_08_06.md`
      (3 occurrences), and this doc's own `related`/`context_scope`. Prose-only citations without a leading path
      (`defi_satellite_ao_dispatch_batch9_2026_08_06.md` bare-named in `defi_track5_coverage_mvp_backfill_2026_07_24.md`,
      `data_completion_defi_2026_07_15.md`, `issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`,
      `issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`,
      `issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`,
      `issues/governance_sweep_deferred_followups_2026_08_06.md`,
      `issues/plan_reconciler_findings_defi_2026_08_17.md`) left unqualified per corpus convention — these are
      historical evidence citations, not resolvable links, matching how every other archived batch's citations are left
      elsewhere in this corpus; (6) `git mv`'d to `plans/archive/2026_08/defi_satellite_ao_dispatch_batch9_2026_08_06.md`.
      Repo: unified-trading-pm.

## Progress Log

- 2026-08-06 (scheduled `ag_closeout_auditor`, tranche=defi, autonomous, slot 3): Drafted alongside batch9,
  `status: active`, gated on batch9's 17 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on
  batch9's operator-approval flip to `active` and subsequent dispatch.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
