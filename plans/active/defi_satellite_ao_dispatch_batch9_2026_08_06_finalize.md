---
doc_type: plan
title: DeFi satellite AO batch 9 — finalize (reconcile 17 source docs + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch9_2026_08_06.md — machine-held via depends_on + gate_on_depends:
  true until every one of that plan's 17 todos is done. Mirrors batch1-8-finalize: reconcile each of the 17 source docs
  (flip/cite the item each batch9 todo closed), re-check the 2 conflict-parked Deferred items + the 33 non-batchable
  Deferred items for whether any blocking condition has since cleared, then archive batch9 via the standard 6-step
  ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-9, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
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
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
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

**status: active — gated on batch9's 17 todos via `depends_on` + `gate_on_depends: true`; the dispatcher will not
release these until batch9 is fully done.** (Batch9 itself stays `status: draft` until the operator approves dispatch —
this finalize plan needs no separate flip, `gate_on_depends` holds it correctly either way per the "no double gate"
finding in `cursor-configs/skills/ag-closeout-audit/SKILL.md`.)
**BANNER-FIXED 2026-08-16 (plan_reconciler, defi tranche, dispatch agt-1a88e0)**: the "batch9 stays status: draft"
claim above is stale — `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s actual frontmatter is
`status: active — operator-approved 2026-08-06, dispatching`, and all 17 of its todos are now `[x]`. This finalize
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
- [ ] [DOC] P2. **Re-check the Deferred items**: (a) the 2 conflict-parked operator-decision-gated items
      (`defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`'s stall diagnosis,
      `lst_rate_honest_coverage_over_cap_findings_2026_08_03.md`'s split-vs-alternative — gated on
      `over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`'s own `[OPERATOR]` ruling) — has either operator
      question been ruled on since batch9 was drafted? (b) the 33 non-batchable items (20 operator_gated, 8
      genuinely_human_only, 3 too_large_or_risky, 2 time_gated) — has any blocking condition cleared (an operator ruling
      landed, elapsed time passed, a competing claim shipped/superseded)? Per the skill's iterative-drain methodology,
      any item that clears becomes a batch10 candidate directly, without a fresh Phase-1 triage agent. Repo:
      unified-trading-pm. Done when: each of the 2 parked items and the 33 Deferred items has an explicit still-held /
      cleared verdict recorded here, with citations for any newly-cleared item.
- [ ] [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch9_2026_08_06.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): (1) confirm every Deferred item from todo
      2 above is migrated with an explicit verdict, no orphaned prose; (2) add the archived-banner cross-reference; (3)
      run the post-phase codex audit — cite any codex doc this batch's shipped work should update; (4) confirm no new
      CLAUDE.md contract needs codifying; (5) update every corpus referrer (`plans/active/INDEX.md` +
      `defi_consolidated_closeout_2026_07_18.md`'s covering-plan discovery, if it lists batch9 by name) to the archived
      path; (6) `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm. Done when: batch9 is at its archived
      path with every referrer updated and this finalize plan's own todos all `[x]`.

## Progress Log

- 2026-08-06 (scheduled `ag_closeout_auditor`, tranche=defi, autonomous, slot 3): Drafted alongside batch9,
  `status: active`, gated on batch9's 17 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on
  batch9's operator-approval flip to `active` and subsequent dispatch.
- **context-scout 2026-08-07**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
