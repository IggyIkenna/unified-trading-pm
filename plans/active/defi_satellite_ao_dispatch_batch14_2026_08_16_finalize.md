---
doc_type: plan
title: DeFi satellite AO batch 14 — finalize (reconcile 8 source docs + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch14_2026_08_16.md — machine-held via depends_on +
  gate_on_depends: true until every one of that plan's 8 todos is done. Reconciles each of the 8 source docs
  (flip/cite the item each batch14 todo closed), re-checks the deferred items listed in batch14's own "Not extracted
  this batch" section for whether any blocking condition has since cleared, then archives batch14 via the standard
  6-step ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-14, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
depends_on: [defi_satellite_ao_dispatch_batch14_2026_08_16]
gate_on_depends: true
source: >-
  Satellite-batch extraction from `/ag-closeout-audit defi` (2026-08-16), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, and a batch-style
  extraction plan's finalize additionally reconciles every named source doc's checkbox.
assigned_role: data_engineering
effort: medium
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 14 — finalize

**status: active — gated on batch14's 8 todos via `depends_on` + `gate_on_depends: true`; the dispatcher will not
release these until batch14 is fully done.**

## Todos

- [ ] [REVIEW] P1. **Source-doc reconciliation**: for each of batch14's 8 todos, confirm the cited source doc's own
      item was flipped or annotated with the closing citation as that todo's Done-when specified. The 8 source docs
      to check: `plans/active/issues/mtds_qg_red_morpho_url_and_sports_contract_regression_2026_08_15.md` (todo 1),
      `plans/active/issues/instruments_service_defi_golden_red_capability_drift_2026_08_14.md` (todos 1 and 2 — was "1 and
      3", corrected 2026-08-18 per plan_reconciler: that doc's Todos section has only 2 items),
      `plans/active/issues/defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (all 3 items),
      `plans/active/issues/dp_vm_001_mdps_defi_2022_exit_nonzero_singledate_hang_2026_08_15.md` (the BACKEND item
      only — leave the OPERATOR item open), `plans/active/issues/dp_vm_001_mdps_defi_2026_lock_ttl_staleness_budget_mismatch_2026_08_15.md`
      (the full doc), `plans/archive/2026_08/issues/defi_dex_pool_density_drop_pool_level_followup_2026_08_14.md` (the full
      doc), `plans/active/issues/pendle_venue_onboarding_2026_08_16.md` (the 2 P2 wiring items + config item only —
      leave the P3 archetype-inclusion item open), `plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md`
      (todo 3). Repo: unified-trading-pm. Done when: every one of the 8 source docs shows the corresponding item(s)
      closed in its own text, or a citation note pointing back at the batch14 todo that closed it, with no orphaned
      "still looks open" gap.
- [ ] [DOC] P2. **Re-check the deferred items** listed in batch14's own "Not extracted this batch" section: has any
      blocking condition cleared since batch14 was drafted (an operator ruling landed on one of the 5
      operator-gated items, `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`'s dispatcher-wiring
      work landed — clearing the kamino/morpho baseline close-out condition, or `solana_lst_carry_jupiter_perps_and_kamino_borrow_2026_08_12.md`'s
      §A/§A.3 gates resolved)? Repo: unified-trading-pm. Done when: each deferred item has an explicit
      still-held / cleared verdict recorded here, with citations for any newly-cleared item (feed any newly-cleared
      item into a future batch15 candidate list rather than drafting it here).
- [ ] [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch14_2026_08_16.md`** via the standard 6-step ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): (1) confirm every deferred item from
      todo 2 above has an explicit still-held/cleared verdict, no orphaned prose; (2) add the archived-banner
      cross-reference; (3) run the post-phase codex audit — cite any codex doc this batch's shipped work should
      update (e.g. `defi-canonical-naming-ssot.md` if the golden-reconciliation work changes the AAVE_V3 rewards
      contract); (4) confirm no new CLAUDE.md contract needs codifying; (5) update every corpus referrer
      (`defi_consolidated_closeout_2026_07_18.md`'s covering-plan discovery list, if it names batch14) to the
      archived path; (6) `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm. Done when: batch14 is at
      its archived path with every referrer updated and this finalize plan's own todos all `[x]`.

## Progress Log

- 2026-08-16 (satellite-batch extraction, `/ag-closeout-audit defi` follow-up): drafted alongside batch14,
  `status: active`, gated on batch14's 8 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting
  on batch14's operator approval (flip `draft` → `active`) + dispatch + completion.
**context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
