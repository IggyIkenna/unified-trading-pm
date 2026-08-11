---
doc_type: plan
title: DeFi satellite AO batch 10 — finalize (reconcile 9 source docs + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch10_2026_08_06.md — machine-held via depends_on + gate_on_depends:
  true until every one of that plan's 9 todos is done. Mirrors batch1-9-finalize: reconcile each of the source docs
  (flip/cite the item each batch10 todo closed), re-check the 27 non-batchable Deferred items for whether any blocking
  condition has since cleared, then archive batch10 via the standard 6-step ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-10, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch10_2026_08_06.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-11"
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
    /plans/active/defi_satellite_ao_dispatch_batch10_2026_08_06.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
depends_on: [defi_satellite_ao_dispatch_batch10_2026_08_06]
gate_on_depends: true
source: >-
  `/ag-closeout-audit defi` run 2026-08-06 (autonomous, scheduled ag_closeout_auditor, slot 9), per task_template.md
  §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 10 — finalize

**status: active — gated on batch10's 9 todos via `depends_on` + `gate_on_depends: true`; the dispatcher will not
release these until batch10 is fully done.** (Batch10 itself stays `status: draft` until the operator approves dispatch
— this finalize plan needs no separate flip, `gate_on_depends` holds it correctly either way per the "no double gate"
finding in `cursor-configs/skills/ag-closeout-audit/SKILL.md`.)

## Todos

- [x] ✅ [DOC] P1. **Source-doc reconciliation**: for each of batch10's 9 todos, confirm the cited source doc's own open
      item was actually flipped/closed-by-citation as that todo's Done-when specified (todos 1-9, one check each — most
      todos already instruct flipping the source doc's own checkbox/status directly as part of their own Done-when, so
      this is a verification pass, not new investigation). Repo: unified-trading-pm. Done when: every one of the 8
      source docs listed in batch10's todos either shows the item closed in its own text, or a citation note pointing
      back at the batch10 todo that closed it, with no orphaned "still looks open" gap. — **DONE 2026-08-11 (slot-31)**:
      all 9 todos × 8 source docs checked. 7/8 clean (manifestwriter race: both items `[x]` w/ batch10 citations;
      bridge_events: `[x]` + genesis/zero-stale criteria in Progress Log; clean_path: item 4 `[x]` @17aed396;
      BLAZESTAKE: items 1-2 `[x]` w/ batch10 citations; yearn_v3: Todo 5 `[x]` + 08-11 slot-7 flip logged;
      lst_rate_honest_coverage: 3 checkboxes `[x]` w/ citations; over_cap_findings: Todo 2+3 `[x]` w/ batch10
      citations). 1 gap closed this turn: track5 Todo 1 lacked a batch10 citation note — Progress Log entry added
      recording batch10 todo 3's milestone (VM `mtds-perp-funding-backfill` RUNNING + unpark prereq flipped true
      2026-08-07T16:44Z); checkbox stays `[ ]` (backfill-to-100% genuinely open, not orphaned).
- [x] ✅ [DOC] P2. **Re-check the 27 Deferred items** (18 operator_gated, 4 too_large_or_risky, 4 time_gated, 1
      genuinely_human_only): has any blocking condition cleared since batch10 was drafted (an operator ruling landed —
      see `/plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md` and
      `/plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` — elapsed time passed, a competing
      claim shipped/superseded)? Per the skill's iterative-drain methodology, any item
      that clears becomes a batch11 candidate directly, without a fresh Phase-1 triage agent. Also re-check the 3
      reported frontmatter-mistag candidates (`cefi_ml_directional_continuous_live_2026_06_20.md`,
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`,
      `issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`) — has the owning tranche (cefi / sports or
      ao) retagged any of them yet? Repo: unified-trading-pm. Done when: each of the 27 Deferred items and 3 mistag
      candidates has an explicit still-held / cleared / retagged verdict recorded here, with citations for any
      newly-cleared item. — **DONE 2026-08-11 (slot-21)**: all 27+3 items re-checked. **5 items changed status** (4
      operator rulings landed: `kalshi_perp` 08-06, `turbo_api` 08-08, `catalog_engine` 08-09 per
      `/plans/active/issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`; 1 functionally
      complete), 2 mistag candidates retagged, 23 items still-held. Full per-item verdicts below.

      ### operator_gated (18) — verdicts

          1. **`defi_migration_audit_log_2026_07_24.md`** (10 of 11 items) — **STILL-HELD**: 14 open todos remain; migration
             tracking still in progress, no operator rulings on the held-back items since 08-06.
          2. **`defi_venue_lst_rates_residual_2026_07_24.md`** (SUSHISWAP classic-vs-V3 alias) — **STILL-HELD**: 1 open,
             `BLOCKED-OPERATOR-DECISION 2026-08-08` — scoping revealed premise doesn't hold as stated; operator decision
             still pending.
          3. **`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`** (dual-deposit cost calibration +
             food-chain wizard) — **STILL-HELD**: 3 open design-gated todos.
          4. **`architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`** (delete-vs-re-leg strategy decision)
             — **STILL-HELD**: 1 open, resync UI venue_set_variants.
          5. **`defi_adapter_dead_code_audit_2026_07_24.md`** (4 scoped disposition decisions) — **STILL-HELD**: 1 open,
             re-verify governance-parameters-refresh.
          6. **`defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md`** (2 strategy-design decisions) —
             **STILL-HELD**: 2 open, design decisions still pending.
          7. **`defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md`** (canonical-schema DESIGN item) —
             **STILL-HELD**: 2 open, [HUMAN] backfill-scope decision + code cleanup.
          8. **`defi_catalog_engine_config_key_contract_drift_2026_07_23.md`** (3 trading-parameter/design rulings) —
             **CLEARED**: operator RULED 2026-08-09 — pollable-candidate-registry design decided; remaining implementation
             is now AO-eligible (batch11 candidate).
          9. **`defi_expected_unattempted_backlog_1m_2026_07_03.md`** (SSOT-contradiction judgment call) — **CLEARED**: 0
             open todos (3 done), `status: open` but functionally complete — archive candidate, no longer operator-gated.
          10. **`defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`** (disposition of 567 objects) —
          **CLEARED**: operator RULED 2026-08-06 (option b) — "Re-emit all 567 GCS-present objects." Ruling landed;
          execution work is now AO-eligible (batch11 candidate).
          11. **`defi_legacy_precanonical_composite_venue_objects_2026_07_24.md`** (PROD-bucket delete) — **CLEARED**:
          archived 2026-08-08, `status: resolved`. PROD-bucket delete completed, reversibility-qualified agent-execution.
          No longer operator-gated.
          12. **`defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`** (HOW-to-close design decision) —
          **STILL-HELD**: 1 open DIAG P3, design decision still pending.
          13. **`defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`** (naming-convention reconciliation) —
          **STILL-HELD**: 1 open DATA P3, design decision still pending.
          14. **`defi_turbo_api_hides_real_captured_data_2026_07_07.md`** (CEFI/DEFI dual-counting axis) — **CLEARED**:
          operator RULED 2026-08-08 — axis decision made, remaining work is mechanical UAC registration (AO-eligible,
          batch11 candidate).
          15. **`defi_upstream_instruments_catalog_stale_2026_07_15.md`** (ownership + design ruling) — **STILL-HELD**: 1
          open DESIGN P3.
          16. **`deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md`** (which-side-is-authoritative) —
          **STILL-HELD**: 1 open, 0 done, operator ruling still pending.
          17. **`non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`** (HL coin-case design) — **STILL-HELD**: 3
          open (items (b)+(c) claimed by batch6 todo 24, still open as of 2026-08-05).
          18. **`solana_dex_pool_swaps_indexer_scope_2026_07_12.md`** (prioritization decision) — **STILL-HELD**: 1 open,
          waiting on `solana_dex_pool_swaps_indexer_2026_08_08.md`.

          ### too_large_or_risky (4) — verdicts

          19. **`data_completion_defi_2026_07_15.md`** — **STILL-HELD**: 17 open, 31 done. Live multi-phase canon-walk
          still in progress.
          20. **`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`** — **STILL-HELD**: 2 open, ~3.46M-row
          dex_swaps migration still too large for batch.
          21. **`defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`** — **STILL-HELD**: 1 open, same
          dex_swaps→dex_pool_swaps migration as #20.
          22. **`pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`** — **STILL-HELD** (category):
          operator RULED 2026-07-29 (Option B: ETH-underlying units), but remains money-path PnL/HWM work needing
          dedicated 3-lens review — too_large_or_risky classification unchanged despite ruling.

          ### time_gated (4) — verdicts

          23. **`defi_morpho_lending_indices_never_wired_2026_07_12.md`** — **STILL-HELD**: blocked on
          `data_completion_defi_2026_07_15`'s `depends_on` gate (17 open todos remain).
          24. **`defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`** (item 3 — capture stall investigation)
          — **STILL-HELD**: REOPENED 2026-08-08, live re-check pending; blocking condition not cleared.
          25. **`lst_rate_honest_coverage_2026_07_21.md`** (items 1, 3, 4) — **STILL-HELD**: item 1 blocked on P0
          VM-memory-hang fix (not yet resolved), item 3 money-path, item 4 blocked on
          `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`'s open `[OPERATOR]` todo.
          26. **`defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`** ([OPERATOR] redeploy item) — **STILL-HELD**:
          1 open DATA P3, possibly blocked on IS CI state.

          ### genuinely_human_only (1) — verdict

          27. **`features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`** — **STILL-HELD**: 1 open,
          partially closed by batch6 todo 18 (features-service@d8a643a0); still needs human sizing/scoping across 5
          protocols.

          ### frontmatter-mistag candidates (3) — verdicts

          28. **`cefi_ml_directional_continuous_live_2026_06_20.md`** — **RETAGGED**: cefi's ag-closeout-audit (2026-08-08)
          corrected `asset_group: [cefi]` (was `[cefi, defi]`). Defi tag dropped.
          29. **`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`** — **RETAGGED**: cefi's ag-closeout-audit
          (2026-08-08) corrected `asset_group: [cefi]` (was `[cefi, defi]`). Defi tag dropped.
          30. **`sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`** — **STILL-HELD**: defi tag NOT retagged;
          still carries `asset_group: [sports, prediction, defi, meta]`. Both residual checkboxes that justified the
          defi+prediction tags are now `[x]` DONE (per batch10's own report), but retagging belongs to sports/ao
          tranche per concurrent-sharded-worker safety rule.

          ### Summary

          | Category | Total | Still-Held | Cleared/Ruled | Retagged |
          |----------|-------|------------|---------------|----------|
          | operator_gated | 18 | 13 | 5 | — |
          | too_large_or_risky | 4 | 4 | 0 | — |
          | time_gated | 4 | 4 | 0 | — |
          | genuinely_human_only | 1 | 1 | 0 | — |
          | mistag candidates | 3 | 1 | — | 2 |
          | **Total** | **30** | **23** | **5** | **2** |

          **5 newly-cleared items for batch11 consideration**: `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`
          (ruled 08-09), `defi_expected_unattempted_backlog_1m_2026_07_03.md` (0 open, archive candidate),
          `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md` (ruled 08-06),
          `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (archived 08-08),
          `defi_turbo_api_hides_real_captured_data_2026_07_07.md` (ruled 08-08).

- [ ] [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch10_2026_08_06.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): (1) confirm every Deferred item from todo
      2 above is migrated with an explicit verdict, no orphaned prose; (2) add the archived-banner cross-reference; (3)
      run the post-phase codex audit — cite any codex doc this batch's shipped work should update; (4) confirm no new
      CLAUDE.md contract needs codifying; (5) update every corpus referrer (`plans/active/INDEX.md` +
      `defi_consolidated_closeout_2026_07_18.md`'s covering-plan discovery, if it lists batch10 by name) to the archived
      path; (6) `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm. Done when: batch10 is at its archived
      path with every referrer updated and this finalize plan's own todos all `[x]`.

## Progress Log

- 2026-08-06 (scheduled `ag_closeout_auditor`, tranche=defi, autonomous, slot 9): Drafted alongside batch10,
  `status: active`, gated on batch10's 9 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on
  batch10's operator-approval flip to `active` and subsequent dispatch.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries)
- **2026-08-11 (slot-21, infra→data_engineering, task finalize-002)**: P2 done — re-checked all 27 Deferred items + 3
  mistag candidates against live doc state. **5 items changed status**: 4 operator rulings landed (`catalog_engine`
  08-09, `kalshi_perp` 08-06, `turbo_api` 08-08, `legacy_precanonical` archived 08-08), 1 functionally complete
  (`expected_unattempted_backlog` 0 open todos). **2 mistag candidates retagged** by cefi tranche 08-08 (`cefi_ml`,
  `cryptovenue`). **23 items still-held** with unchanged blocking conditions. 5 newly-cleared items are batch11
  candidates per the iterative-drain methodology. Verdicts recorded inline above.
