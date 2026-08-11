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

- [ ] [DOC] P1. **Source-doc reconciliation**: for each of batch10's 9 todos, confirm the cited source doc's own open
      item was actually flipped/closed-by-citation as that todo's Done-when specified (todos 1-9, one check each — most
      todos already instruct flipping the source doc's own checkbox/status directly as part of their own Done-when, so
      this is a verification pass, not new investigation). Repo: unified-trading-pm. Done when: every one of the 8
      source docs listed in batch10's todos either shows the item closed in its own text, or a citation note pointing
      back at the batch10 todo that closed it, with no orphaned "still looks open" gap.
- [x] ✅ [DOC] P2. **Re-check the 27 Deferred items** (18 operator_gated, 4 too_large_or_risky, 4 time_gated, 1
      genuinely_human_only): has any blocking condition cleared since batch10 was drafted (an operator ruling landed,
      elapsed time passed, a competing claim shipped/superseded)? Per the skill's iterative-drain methodology, any item
      that clears becomes a batch11 candidate directly, without a fresh Phase-1 triage agent. Also re-check the 3
      reported frontmatter-mistag candidates (`cefi_ml_directional_continuous_live_2026_06_20.md`,
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md`,
      `issues/sports_manifest_consolidator_zero_growth_stall_2026_07_29.md`) — has the owning tranche (cefi / sports or
      ao) retagged any of them yet? Repo: unified-trading-pm. Done when: each of the 27 Deferred items and 3 mistag
      candidates has an explicit still-held / cleared / retagged verdict recorded here, with citations for any
      newly-cleared item. — **Done 2026-08-11 (slot-29)**: all 30 verdicts recorded below (1 cleared, 2 retagged, 27
      still-held). See Progress Log for the full per-item table.
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
- **data_engineering (slot-29) 2026-08-11T04:30Z**: P2 Re-check done — all 27 Deferred + 3 mistag candidates verdicted.
  Evidence: git-log check across all 30 paths since 2026-08-06 + targeted content reads for items showing substantive
  changes (non-context-scout/non-audit-marker commits).

  **Summary**: 1 cleared, 2 retagged, 27 still-held.

  **CLEARED (1 — operator_gated → archived):**
  | Doc | Category | Verdict | Evidence |
  |-----|----------|---------|----------|
  | `defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` | operator_gated | **CLEARED** — archived 2026-08-08 | `d1541a7f30`: PROD-bucket delete completed; doc `git mv`'d to `plans/archive/issues/`. No longer in the deferred pool. |

  **MISTAG CANDIDATES — RETAGGED (2 of 3):**
  | Doc | Batch10 finding | Verdict | Evidence |
  |-----|-----------------|---------|----------|
  | `cefi_ml_directional_continuous_live_2026_06_20.md` | `defi` tag likely droppable | **RETAGGED** 2026-08-08 — `asset_group: [cefi]` (was `[cefi, defi]`) | ag-closeout-audit cefi Phase 0.3 orthogonality check; doc scope is 100% CeFi |
  | `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` | `[cefi,defi]` likely needs `[cefi,tradfi]` | **RETAGGED** 2026-08-08 — `asset_group: [cefi]` (was `[cefi, defi]`) | ag-closeout-audit cefi Phase 0.3; tradfi tag was NOT added (cefi-only correction, tradfi re-tagging is the tradfi tranche's call) |
  | `sports_manifest_consolidator_zero_growth_stall_2026_07_29.md` | drop `defi`+`prediction` now that residual checkboxes are `[x]` | **NOT YET** — still `asset_group: [sports, prediction, defi, meta]`; 1 open `[ ]` todo remains | `0acf56a54c` touched it during archive sweep but did NOT drop the tags. The 2 residual checkboxes batch10 cited as done are both `[x]`, but the sports/ao owning tranche hasn't retagged. |

  **STILL HELD — operator_gated (17):**
  | Doc | Evidence |
  |-----|----------|
  | `defi_migration_audit_log_2026_07_24.md` | `4444749524` added KEEP-NA-valid marker (na-eligibility-audit, 2026-08-09); `2bd0cd7b26` extracted batch11 candidates — no operator ruling on the 10 remaining items |
  | `defi_venue_lst_rates_residual_2026_07_24.md` | `560d65af69`: SUSHISWAP migrate-todo premise found not to hold (multi-chain data-correctness finding) — the operator ruling on SUSHISWAP scope landed (`a55b820b76`), but the doc's residual item is a DIFFERENT question (classic-vs-V3 alias) still undecided |
  | `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` | `699d9a4643` ratchet fix; `4fe17cd68e` KEEP-NA marker — no operator ruling on dual-deposit cross-exchange cost calibration or food-chain wizard scoping |
  | `architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` | `4444749524` KEEP-NA-valid marker; context-scout sweep only — delete-vs-re-leg strategy decision still open |
  | `defi_adapter_dead_code_audit_2026_07_24.md` | `0ab50362a5` referrer fix (Jupiter archival); `c328a59f20` Jupiter closeout — 4 scoped disposition decisions still undecided |
  | `defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` | `6ecfc63424` RECLASSIFY sweep; `7ed185489c` KEEP-NA marker — 2 strategy-design decisions still open |
  | `defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md` | `4444749524` KEEP-NA-valid marker; context-scout only — canonical-schema DESIGN item still gates IMPL+VERIFY |
  | `defi_catalog_engine_config_key_contract_drift_2026_07_23.md` | `fefc03aed4` flipped finalize todo 3 (archival done); `19c2e7701c` flipped todo 1 — but the 3 trading-parameter/design rulings batch10 cited are separate open items in the source doc, not these 2 closed todos |
  | `defi_expected_unattempted_backlog_1m_2026_07_03.md` | `ba4158ae69` flipped a `[SCRIPT]` todo; context-scout — SSOT-contradiction judgment call still open |
  | `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md` | `6ecfc63424` RECLASSIFY sweep; context-scout — `[OPERATOR]` disposition of 567 objects still needed |
  | `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md` | `bc2d5c43fe` flipped `[CODE] P2` item — but the HOW-to-close design decision (the item batch10 cited) is a different open todo in the same doc (1 `[ ]` remains) |
  | `defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` | `4444749524` KEEP-NA-valid; `2bd0cd7b26` batch11 extraction — naming-convention reconciliation still deferred as risky design work |
  | `defi_turbo_api_hides_real_captured_data_2026_07_07.md` | **NOTABLE**: 2026-08-08 audit found the HYPERLIQUID/ASTER dual-counting question was already operator-ruled NOT-a-risk on 2026-07-07 — before batch10 was drafted. The doc was misclassified as operator_gated for that axis. However, the sibling CEFI/DEFI dual-counting axis ruling IS still open — so the doc remains operator_gated, just for a narrower reason than batch10 stated |
  | `defi_upstream_instruments_catalog_stale_2026_07_15.md` | `4444749524` KEEP-NA-valid; context-scout — ownership + design ruling still needed |
  | `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` | `a55b820b76` recorded operator rulings on related topics (SUSHISWAP, derivative_ticker, HYPERLIQUID/ASTER) but the which-side-is-authoritative ruling for THIS doc is still open |
  | `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` | `699d9a4643` ratchet fix; `6ecfc63424` RECLASSIFY sweep — HL coin-case design decision still open; items (b)+(c) already claimed by batch6 |
  | `solana_dex_pool_swaps_indexer_scope_2026_07_12.md` | `5fde96a5dc` KEEP-NA-STALE-DUPLICATE citation fix; context-scout — operator prioritization decision still open |

  **STILL HELD — too_large_or_risky (4):**
  | Doc | Evidence |
  |-----|----------|
  | `data_completion_defi_2026_07_15.md` | `6ecfc63424` RECLASSIFY sweep; `7ed185489c` KEEP-NA marker — live multi-phase migration still in progress, re-check its own named sub-items next round |
  | `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` | `b3241ef496`: root-caused OOM as unbounded cross-chunk accumulator, shipped fix, launched AO-dispatched retirement/rollup plan. 1 `[x]`, 5 `[ ]` remain — the dex_swaps migration (~3.46M rows) is still in progress, not complete |
  | `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` | `6ecfc63424` RECLASSIFY sweep; context-scout — same dex_swaps→dex_pool_swaps migration, same too-large precedent, not complete |
  | `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` | `6ecfc63424` RECLASSIFY sweep — money-path PnL/HWM, needs dedicated 3-lens review, no change |

  **STILL HELD — time_gated (4):**
  | Doc | Evidence |
  |-----|----------|
  | `defi_morpho_lending_indices_never_wired_2026_07_12.md` | `4444749524` KEEP-NA-valid; context-scout — blocked on `data_completion_defi_2026_07_15`'s own `depends_on` gate, not yet cleared |
  | `defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md` | `4444749524` KEEP-NA-valid; context-scout — item 3 (investigate capture stall) still pending; batch9's own report flagged it as possibly-stale premise |
  | `lst_rate_honest_coverage_2026_07_21.md` | `4444749524` KEEP-NA-valid; `f85fafdec7` closed 1 stale item + corrected 2 verification-method false-negatives — but items 1/3/4 batch10 cited are STILL blocked on their respective gates (P0 VM-memory-hang fix, 3-lens review, over_cap operator todo) |
  | `defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md` (time_gated entry) | Same doc as operator_gated entry above — the `[OPERATOR]` redeploy item is the time_gated sub-item; still blocked on instruments-service CI state |

  **STILL HELD — genuinely_human_only (1):**
  | Doc | Evidence |
  |-----|----------|
  | `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` | `6ecfc63424` RECLASSIFY sweep — still needs human sizing/scoping across 5 protocols; no change |
