---
doc_type: plan
title: defi satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the defi tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 16
  conflict-cleared, bounded/deterministic items pulled directly from 13 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md,
    /plans/active/issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md,
    /plans/active/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md,
    /plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md,
    /plans/active/issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md,
    /plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md,
    /plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md,
    /plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md,
    /plans/active/issues/solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# defi satellite AO dispatch batch 13 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] [CODE] P2. ✅ Delete the now-dead `_parse_curve` function in
      market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py (confirmed unreferenced dead
      code, mechanical deletion) Source:
      `plans/active/issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md` —
      market-tick-data-service@97a8b8e870. Deleted the function, its `DexPoolsHandler._parse_curve` class binding, and
      its direct unit test (`test_parse_curve_full`); confirmed no other code references remain (only historical
      comments in `_dex_pools_subgraph.py`/`_parse_balancer`'s docstring, left as-is — accurate prose, not broken code).
      Full quality-gates.sh green.
- [x] [CODE] P2. ✅ Determine the real scope of the HYPERLIQUID perp_funding gap around 2026-04-20 via a bounded
      manifest query across April-May 2026 (explicitly not a corpus walk, worker-determinable outcome) Source:
      `plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md`
      — market-tick-data-service@ba8b3146. Bounded
      `read_availability_index(..., filters=[("date",">=",...),("date","<=",...)])` query for
      `(cefi, perp_funding, HYPERLIQUID)` across 2026-04-01..2026-05-31 found **61/61 days captured, zero gap**
      (including 2026-04-20 itself). The original 2026-08-08 preflight failure no longer reproduces — the gap has since
      closed. Confirmed NOT the same root cause as `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`
      (different data_type, non-overlapping window). Full findings in the source issue doc's Progress Log.
- [ ] [CODE] P2. P3 test-isolation flake fix: add a setup_events() fixture to
      test_batch_harness.py::test_position_state_survives_across_ticks so it passes in isolation (strategy-service repo)
      -- bounded/mechanical, not a judgment call. Source:
      `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`
- [ ] [CODE] P2. Cross-check instrument_type=spot_pair (9,802 rows) against defi-canonical-naming-ssot.md's locked
      instrument_type list Source: `plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`
- [ ] [CODE] P2. Fix the deployment-api/instruments-service Distinct Values panel's <blank> instrument_type badge to
      exclude capture_status=empty_confirmed rows (mirrors the already-shipped attempted_failed enumeration-key fix,
      instruments-service@8b59e8ba2) Source:
      `plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`
- [ ] [CODE] P2. Add aggregator-routes as the 9th migrate_defi_full_v9_canonical.py migrator spec (per the 2026-08-08
      operator decision already ruling it a dedicated bucket, mirroring the shipped gas-fees/liquidations 7th/8th specs)
      Source: `plans/active/defi_migration_audit_log_2026_07_24.md`
- [ ] [CODE] P2. Redirect the 4 DeFi live handlers (dex_swaps_handler, solana_defi_handler, evm_defi_handler,
      aggregator_route_handler) that still write to non-migrated legacy buckets onto their dedicated migrated-bucket
      targets Source: `plans/active/defi_migration_audit_log_2026_07_24.md`
- [ ] [CODE] P2. Wire gas_fees into the manifest could-exist denominator as a per-chain expected cell (IS
      enumerate_expected_universe + deployment-api/UI data-status), the (b) half of the already-registered gas-fees
      manifest todo Source: `plans/active/defi_migration_audit_log_2026_07_24.md`
- [ ] [CODE] P2. Live-verify DP-LIVE-003 correctly RESOLVES (posts a checkbox RESOLVED bookend) for whichever of
      findings 3-10 get relaunched, per the doc's own [SCRIPT] P3 todo Source:
      `plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md`
- [ ] [CODE] P2. Extract the lst_rate_honest_coverage_2026_07_21.md Progress Log's VM-monitoring-history block
      (~2026-07-21..07-26 entries) into a companion doc, per Todo 1's stated pattern Source:
      `plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md`
- [ ] [CODE] P2. Root-cause why lending_indices capture stopped 2026-08-01 — read-only diagnosis (check for a stalled
      cron/Workflow trigger), reopened 2026-08-08 with the underlying stall independently reconfirmed real via a live
      availability_index re-check; the operator-blocking premise that originally parked it was resolved the same day.
      Source: `plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`
- [ ] [CODE] P2. Verify whether the declining DeFi shard-density trend (Dec2025-Feb2026 ~28,000 shards/day →
      2026-06-30..07-19 ~934/day, a >30x drop assumed but never confirmed to reflect venue retirement) is genuine or an
      actual capture gap — bounded cross-check with an explicit done-when already stated in the doc. Source:
      `plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md`
- [ ] [CODE] P2. Run /data-pipeline-check-is and /data-pipeline-check-mtds 3x each (baseline/mid-backfill/final) across
      the defi backfill using --day 2026-07-01 (operator-unparked 2026-08-08, exact commands already specified in the
      doc) — launcher-driven VM check, worker-executable, not yet dispatched anywhere Source:
      `plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md`
- [ ] [CODE] P2. todo1: investigate whether solana_dex_pool_swaps_indexer-002's workload characteristics (prompt size,
      tool-call pattern, worktree size) disproportionately trigger the now-root-caused fleet-wide TmuxPruner crash-loop,
      per agent-orchestrator logs/code Source:
      `plans/active/issues/solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md`
- [ ] [CODE] P2. Update defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md row 1's stale script-name/numbers
      once the gas_fees manifest purge is confirmed complete — bounded doc-hygiene edit Source:
      `plans/active/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`
- [ ] [CODE] P2. Relaunch the dex_swaps legacy-fold script WITHOUT --allow-stale-fallback once the DeFi manifest
      consolidator has genuinely caught up (mechanical rerun, worker can verify freshness precondition and execute)
      Source: `plans/active/issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
