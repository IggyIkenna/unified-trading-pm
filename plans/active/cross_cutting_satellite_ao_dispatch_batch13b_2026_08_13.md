---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 13 part 2 — 2026-08-13
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep —
  39 conflict-cleared, bounded/deterministic items pulled directly from 11 source docs (RECLASSIFY_SPLIT bounded items
  from the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each
  todo cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation
  back into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: draft
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/mtds_main_promotion_stall_and_qg_alert_redispatch_2026_08_11.md,
    /plans/active/issues/mtds_type_ignore_ratchet_blocks_prek_intel_mac_fix_2026_08_03.md,
    /plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md,
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    /plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md,
    /plans/active/issues/plan_reconciler_findings_all_2026_08_12.md,
    /plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md,
    /plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md,
    /plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md,
    /plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md,
    /plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 5.8
estimate_calibrated_ai_days: 4.7
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# cross-cutting satellite AO dispatch batch 13b — 2026-08-13

> **`status: draft` — NOT ingested/dispatched.** Flip to `status: active` only after operator review. Every todo below
> was classified bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13
> full-sweep audit and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [ ] [CODE] P2. Diagnose why no successor promote PR opened for market-tick-data-service (check
      ldr_to_main_fleet_promote.sh per-repo logic and ahead_by trend) Source:
      `plans/active/issues/mtds_main_promotion_stall_and_qg_alert_redispatch_2026_08_11.md`
- [ ] [CODE] P2. Read unified-trading-ci's python-quality-gates-v2.yml on: trigger config to find and fix the ~15-min
      redispatch, or migrate the Slack step to the dedup'd notify-slack.yml carrier Source:
      `plans/active/issues/mtds_main_promotion_stall_and_qg_alert_redispatch_2026_08_11.md`
- [ ] [CODE] P2. Investigate and document why standalone quality-gates.sh --no-fix treats the local type:ignore ratchet
      (STEP 5.94/5.95) as non-fatal while quickmerge's internal re-gate treats the identical finding as fatal Source:
      `plans/active/issues/mtds_type_ignore_ratchet_blocks_prek_intel_mac_fix_2026_08_03.md`
- [ ] [CODE] P2. Resolve the diff base to the branch's own last-gated point instead of a fixed origin/main proxy Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md`
- [ ] [CODE] P2. Add a detector for a non-convergeable (monotonically-growing-violation-count) ratchet gate distinct
      from an ordinary retryable failure Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md`
- [ ] [CODE] P2. Fix the ldr-to-main-promote.yml rate mismatch that lets a fast-failing check manufacture an unbounded
      stream of superseded PRs Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md`
- [ ] [CODE] P2. Extend the proven --diff-base pattern to check_ag_closeout_linkage Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md`
- [ ] [CODE] P2. Make check_ui_api_flow_coverage.py hard-fail instead of silently exiting 0 when its manifest file is
      missing Source:
      `plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md`
- [ ] [CODE] P2. Fix the client_context.py docstring (remove the nonexistent max_leverage field, correct
      min_balance_per_venue naming) Source:
      `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md`
- [ ] [CODE] P2. Instantiate or explicitly waive clients.yaml for every factory-registered archetype that can run
      Source: `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md`
- [ ] [CODE] P2. Record the resolved per-client config surface ownership in codex (per-client-isolation-architecture.md)
      Source: `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md`
- [ ] [CODE] P2. Mine unified-trading-system-ui backtest views for the analytics surface before extending the analytics
      schema section further Source:
      `plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md`
- [ ] [CODE] P2. Verify current DeFi canonical-migration-defi-rebuild fleet completion and consolidated-manifest
      freshness state Source: `plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md`
- [ ] [CODE] P2. Determine the root cause of sports data being ~4 weeks stale Source:
      `plans/active/issues/pipeline_smoke_sweep_findings_2026_07_20.md`
- [ ] [CODE] P2. dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md -- parallelize
      exit_code_fleet_monitor.py/heartbeat_stall_watcher.py's sweep() via ThreadPoolExecutor Source:
      `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md`
- [ ] [CODE] P2. dp_vm_002_mdps_cefi_2021_silent_zero_false_positive_2026_08_11.md -- re-launch mdps-cefi-2021 sharded
      backfill from checkpoint Source: `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md`
- [ ] [CODE] P2. sports_features_2026_backfill_launch_window_was_today_2026_08_10.md -- clamp per-year sports features
      backfill launcher's end_date Source: `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md`
- [ ] [CODE] P2. check_na_corpus_ratchet.py -diff-base fenced-code-block checkbox-overcounting bug (Section 3 log)
      Source: `plans/active/issues/plan_reconciler_findings_all_2026_08_12.md`
- [ ] [CODE] P2. Item A -- retag deployment_api_quickmerge_blocked_pre_existing_test_failures_2026_08_04.md asset_group
      cross-cutting->ui Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item G -- correct stale G3/G10 status text in batch_live_reconciliation_service_audit_2026_05_27.md
      citing the successor doc Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item H -- live re-verify citadel_paper_batch_live_reconciliation_2026_06_19.md P9.2's UAC version-drift
      citation against current UAC Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item J -- fix check_na_corpus_ratchet.py's --diff-base fenced-code-block checkbox-overcounting regex
      bug Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item K -- add the missing backlog todo to
      plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md once grace lifts Source:
      `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item L -- backfill the real sha in over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md's
      placeholder evidence citation Source: `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. Item N -- fix 3 docs' stale 'closeout over 1000-line hard cap' citations (now 720 lines) Source:
      `plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_10.md`
- [ ] [CODE] P2. De-cohort the freshness thresholds (e.g. 90d + hash(path) % 14 jitter, or stagger last_reviewed on bulk
      authoring) Source: `plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md`
- [ ] [CODE] P2. Write up the correctness-ratchet-vs-hygiene-ratchet distinction (currently only in commit messages) as
      a doc Source: `plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md`
- [ ] [CODE] P2. Implement the safe-field allow-list + UnsafeConfigChangeError guard in
      strategy-service/strategy_service/config_reloaders.py per the operator-confirmed 2026-08-12 ruling (option A)
      Source: `plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md`
- [ ] [CODE] P2. FLEET-WIDE: instruments-store _index v9-COLUMN populate for cefi/tradfi/defi (+ prediction source) —
      pattern-identical to the already-shipped sports v9-column populate script Source:
      `plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`
- [ ] [CODE] P2. Key execution policies by (client_id, slot_label) — §B Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Give the execution-policy registry a GCS loader + DomainConfigReloader subscription — §B Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Wire policy evaluation into the live execution path (select_algorithm takes config_algorithm from the
      resolved policy) — §B Source: `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Add the reference price to the shared instruction envelope with its mark mode — §C Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Subscribe strategy-service to ClientDomainConfig — §D Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Resolve execution-service's missing config.py (rename-vs-document decision applied consistently) — §D
      Source: `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Close the Bybit API-key reload asymmetry in DATA_SOURCE_TO_SECRET — §D Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. G1 — feed config_algorithm through the already-threaded selector hook Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Delete the shadow BookType (J1) and import UAC's enum Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`
- [ ] [CODE] P2. Add a participation cap to the passive fill path, filtered to the filling side per PB.8 — §K Source:
      `plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
