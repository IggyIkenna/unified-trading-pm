---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep —
  89 conflict-cleared, bounded/deterministic items pulled directly from 39 source docs (RECLASSIFY_SPLIT bounded items
  from the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each
  todo cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation
  back into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related: [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/active/bucket_estate_consolidation_closeout_2026_07_24.md,
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md,
    /plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
    # + 24 more source docs cited per-todo below
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 13.3
estimate_calibrated_ai_days: 10.7
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

# cross-cutting satellite AO dispatch batch 13 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [INFRA] P2. enumerate every live Cloud Run service's actual runtime SA + role set into the registry (bounded
      audit) — deployment-service@f5ad937bee (2026-08-13 full read-only audit: 25 live Cloud Run rows / 23 distinct
      services across 9 runtime SAs enumerated into `live_runtime_bindings` + `live_runtime_sa_roles` sections; YAML
      validated; QG green; quickmerge landed on LDR) Source:
      `plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`
- [ ] [INFRA] P3. document which live services rely on the default-compute-SA and what secrets/buckets they can
      therefore reach (bounded documentation task) Source:
      `plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`
- [x] ✅ [DIAG] P2. verify the exact CME instrument_id string format for FUTURE contracts against the live catalogue
      before implementing tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md's already-ruled fix —
      unified-trading-pm@(this commit) (2026-08-14: confirmed `CME:FUTURE:<PRODUCT_ROOT>-USD@LIN-YYYYMMDD` via 3
      convergent code sites + a bounded live read of `prod/catalog.parquet`; recorded in both the source issue doc and
      `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 1) Source:
      `plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md`
- [ ] [CODE] P2. Diagnose how strategy-service's LDR HEAD went gate-red (clean-checkout re-run + git log -S on the
      introducing commits) Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [ ] [CODE] P2. Move the 11 Pydantic BaseModel subclasses out of service source or record a justified exemption Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [ ] [CODE] P2. Resolve the STEP 5.37 inline HF/LTV/margin thresholds against UAC LIQUIDATION_PARAMS_REGISTRY Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [ ] [CODE] P2. Fix or re-baseline the <300s quality-gate budget (326s+12s measured) Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [ ] [CODE] P2. Fix the gate's stale SCHEMA_CONTRACTS_AUDIT.md pointer message (and grep the fleet for the same
      template) Source:
      `plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [ ] [CODE] P2. Split the remaining MTDS >900L files + extract oversized fns/methods (market-tick-data-service) Source:
      `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [ ] [CODE] P2. Re-add 17 connector reconnect tests using terminating mocks (market-tick-data-service) Source:
      `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [ ] [CODE] P2. UAC generated-artifact churn: gitignore + git rm --cached openapi/ui-reference-data.json /
      capability-manifest.json (unified-api-contracts) Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [ ] [CODE] P2. All 18 MDPS adapters' process_to_candles(df, ...) -> Polars adapter-protocol seam
      (market-data-processing-service) Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [ ] [CODE] P2. Run PM bash scripts/quality-gates.sh to confirm the plan + codex update pass (unified-trading-pm)
      Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [ ] [CODE] P2. Retry the tradfi attempted_failed cells (13 cells / ~12.5k rows) surfaced by the digest Source:
      `plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`
- [ ] [INFRA] P3. disambiguate 'the planning VM' in monitoring/docs; always name the instance ID or a stable label
      Source: `plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`
- [ ] [INFRA] P3. wire an automated deploy/sync for glue-runner-crash-loop-watchdog.sh so a repo fix reaches the host
      Source: `plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`
- [ ] [BACKEND] P2. document the circular-dependency gap (scheduled workflow runs from default branch) in ci-cd-flow.md
      Source: `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [ ] [BACKEND] P2. sweep the fleet for the same 'set -uo pipefail' + RC=$? -e trap via the given rg command Source:
      `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [ ] [BACKEND] P2. add a meta-assertion that any job publishing a notify-consumed verdict output emits it on the
      failure path too Source:
      `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [ ] [CODE] P2. Pass --build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$$VERSION in strategy-service and greeks-service
      cloudbuild.yaml once each repo's own blocking issue clears Source:
      `plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md`
- [ ] [CODE] P2. Re-run hosted-baseline.sh to resync the derived cloud-build-router.yml snapshot with the live workflow
      Source: `plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md`
- [x] ✅ [DATA] P1. **MOOT — already deleted, confirmed live (2026-08-13, slot 29).** This todo's premise (run a fresh
      retention check, then delete) was stale: the source doc's own 2026-08-12 docs-drift note records that
      `ml-models-store` was already deleted 2026-08-08 (operator-authorized) via the sibling plan
      `bucket_fold_ml_2026_07_17.md`'s "Delete sources" todo — this batch's extraction just hadn't picked that up. Fresh
      live re-verification this session (not just trusting the note):
      `gcloud asset search-all-resources     --scope=projects/central-element-323112 --query="name:ml-" --asset-types="storage.googleapis.com/Bucket"`
      returns only `ml-store-test-central-element-323112` and `ml-store-prd-central-element-323112` (the folded
      canonical buckets) — zero hits for `ml-models-store`, confirming the flat legacy bucket is gone. Dead
      TF/yaml-reference half also re-confirmed clean: fresh
      `grep -rn "ml-models-store\b" deployment-service/terraform deployment-service/configs deployment-api     unified-api-contracts`
      across all 4 repos returns only comments/docstrings describing the already-executed fold (`outputs.tf`,
      `_core.py`, a test docstring, `_ml_training_contract.py`) — no live resource declarations or resolver calls. No
      retention check or delete action was needed or taken. Source:
      `plans/active/bucket_estate_consolidation_closeout_2026_07_24.md`
- [ ] [CODE] P2. Confirm whether any CARRY_STAKED_BASIS/CARRY_BASIS_PERP paper run's fill-rate or slippage figures were
      cited in an actual promotion/sizing decision, and flag for re-check if so Source:
      `plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md`
- [ ] [CODE] P2. make reconcile_release_tags.py's _source_touched() per-repo-source_dir-aware instead of using a flat
      repo-wide _NON_FUNCTIONAL_PATH_RE allowlist Source:
      `plans/active/issues/ibkr_gateway_infra_release_tag_stall_2026_08_11.md`
- [ ] [CODE] P2. Make claim/heartbeat behaviour under test injectable so the common cases can be covered without a real
      tmux server, per the doc's own P2 [SCRIPT] todo Source:
      `plans/active/issues/pm_bats_tmux_fixture_leak_wedges_shared_host_2026_08_10.md`
- [ ] [CODE] P2. Implement the schema/NaN contract in e2e-testing/scripts/validation/validate_shards_4pillar.py per the
      operator-ruled spec (wire _TICK_REQUIRED, add tick to _NAN_SCAN_COLUMNS, wire _DEFI_REQUIRED/_SPORTS_REQUIRED
      narrowly) Source: `plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md`
- [ ] [CODE] P2. Backfill the 10 dataless coins (WIF/BONK/JUP/JTO/RENDER/FET/TAO/ORDI/STX/LDO) into GCS perp funding via
      launch-cefi-sharded-backfill.sh -- operator-approved 2026-08-08, no further confirmation needed, ready to launch
      as a VM backfill. Source: `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`
- [ ] [CODE] P2. OKX-SWAP perp funding sparse (only ~9 coins captured in 2026 vs expected ~19+) -- verify the OKX
      derivative_ticker backfill universe in MTDS. Source:
      `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`
- [ ] [CODE] P2. P9.2 -- run scripts/repo-management/run-version-alignment.sh --fix in strategy-service after pulling
      main in PM; small, deterministic, worth a fresh re-verify since it may already be stale/resolved. Source:
      `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`
- [ ] [CODE] P2. Phase 1c: wire the drain registry into MTDS/MDPS/instruments-service/features-service backfill
      entrypoints Source: `plans/active/alert_driven_dependency_revocation_2026_08_12.md`
- [ ] [CODE] P2. Phase 1: add the flush-contract doc to spot-vms-for-backfill.md Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`
- [ ] [CODE] P2. Phase 2: add DependentAction StrEnum + evaluate_revocation() + alert-action map to UAC (code already
      written, blocked only on an unrelated peer's dirty tree clearing) Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`
- [ ] [CODE] P2. Phase 3: add RetryBudget/RETRY_BUDGETS registry to UAC with the documented default ladder Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`
- [ ] [CODE] P2. Phase 4: add the push actuator in deployment-service that consults evaluate_revocation() with no policy
      branch of its own Source: `plans/active/alert_driven_dependency_revocation_2026_08_12.md`
- [ ] [CODE] P2. Phase 5: add the VM-side drain-marker poll hook and Cloud Run admission-check skip gate Source:
      `plans/active/alert_driven_dependency_revocation_2026_08_12.md`
- [ ] [CODE] P2. Remove BLRS Stage 4's _write_agent_report() write path once superseded Source:
      `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [ ] [CODE] P2. File the dead-mode-kwarg bug (execution_fills/positions/strategy_instructions/pnl_attribution all
      silently drop a mode= path placeholder) as its own issue doc Source:
      `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [ ] [CODE] P2. Fix the stale scheduled-jobs table in agent-orchestrator-single-vm-architecture.md
      (opus/01:00-UTC-daily -> sonnet/hourly-retry) Source:
      `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [ ] [CODE] P2. Launch the now-unblocked EXTENDED-STARKNET instrument-catalogue + perp backfill
      (candles/funding/orderbook/trades) Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Step 2 IS-store backfill for Kraken/LIGHTER/PACIFICA/EXTENDED/BITGET gap-days so MTDS<->IS subsets
      close both ways Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Step 3 cross-data_type completeness capture per venue_data_types.yaml Source:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Verify/implement the DeFi catalogue MVP filter (MTDS reading IS catalogue as TVL-qualifying filter)
      Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. DeFi honest-absence residual-tail fixes: record genuine zeros post-capture, add missing subgraphs,
      catalogue monotonicity check Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. DeFi swallow-fixes (CF-11 class) in DefiManifestRecorder pass-through, liquidations_handler.py,
      polymarket_adapter Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Restore the dex_swaps_handler.py adapter-contract QG-5.70 baseline Source:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [ ] [CODE] P2. Flip data-pipeline-alerts.registry.yaml modes verbose->active as each escalation tier is confirmed
      wired Source: `plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`
- [ ] [CODE] P2. (stretch) Persist full launch-spec CLI args into DeploymentRegistryEntry for exact-replay relaunch
      Source: `plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`
- [ ] [CODE] P2. Wire the generalised extra='forbid'-style source-required checker into MTDS + MDPS quality-gates.sh
      Source: `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [ ] [CODE] P2. Run scripts/quality_gates/audit_source_column_distribution.py against prod post-backfill and report the
      per-cell source histogram Source: `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [ ] [CODE] P2. Update codex + audit instructions to the universal source-provenance rule Source:
      `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [ ] [CODE] P2. Flip the named stale/self-contradictory checkboxes (instruments_mtds_subset: N9c, N5r/N6r) once
      verified against current code Source: `plans/active/instruments_completion_tracker_2026_07_06.md`
- [ ] [CODE] P2. Add cbETH as COINBASE-ETHEREUM to the DeFi LST universe (full new-venue registration) Source:
      `plans/active/instruments_foundation_completeness_2026_06_24.md`
- [ ] [CODE] P2. Retirement completeness (§8) sweep -- verify every named pollutant (tradfi ICE/CBOE/VIX-cash,
      cefi-domain equity-perp singles) is absent on all 4 legs Source:
      `plans/active/instruments_foundation_completeness_2026_06_24.md`
- [ ] [CODE] P2. Generalise the cumulative-drawdown health metric from the 2 existing per-AG scripts (defi, cefi) to a
      single cross-AG metric covering tradfi/sports/prediction Source:
      `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [ ] [CODE] P2. Build the consolidation-reconcile script (actual shards vs materialised expected-universe, scoped
      --force after backfill) Source: `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [ ] [CODE] P2. Build the drilldown-correctness ep=0 reconciliation guard as a QG step + watchdog Source:
      `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [ ] [CODE] P2. Fix canonicalize_instruments_store_index.py's _bucket_for to resolve the prediction instruments-store
      bucket (currently a dead --asset-group prediction path) Source:
      `plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md`
- [ ] [CODE] P2. Investigate the systemic schema-drift dup (16% of shards with >1 manifest row) and fix writer-side
      row-key idempotency Source: `plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md`
- [ ] [CODE] P2. G1.run-prediction: run enumerate_expected_universe.py v2 at the cqg-bundle grain now that the IS
      catalogue-rollup loader wiring has landed (prediction_cqg_residual_2026_07_24.md is archived complete) Source:
      `plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md`
- [ ] [CODE] P2. add a git fetch+rebase step to each plan_health-family scheduled skill's STEP 0 (fixes the PM-checkout
      staleness gap the 2026-08-03 audit re-confirmed live) Source:
      `plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`
- [ ] [CODE] P2. re-run /plan-reconcile whole-corpus SOLO to record a clean, unconfounded benchmark number Source:
      `plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`
- [ ] [CODE] P2. apply the established ParallelPerSymbolRunner asyncio.gather+Semaphore pattern to the 8 remaining
      serial DeFi CLI handlers (dex_swaps_handler.py, evm_defi_collectors.py, gas_fee_handler.py, lst_rates_handler.py,
      liquidations_handler.py, liquidation_events_handler.py, vault_share_price_handler.py,
      eigenlayer_rewards_handler.py), verifying async-caller/ordering/line-cap per site Source:
      `plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`
- [ ] [CODE] P2. fix the 2 blocking-write sites in sync functions (websocket_runner.py::_record_empty_window,
      live_aggregator.py::_handle_zero_tick_window) by dispatching the write via a dedicated executor, per the same
      pattern already shipped for the async sites Source:
      `plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`
- [ ] [CODE] P2. confirm via migration_orphan_sweep.py/cefi-dedup-apply/cefi-content-apply run history or manifest
      history whether the cefi legacy-duplicate corpus is genuinely already gone, then flip the original checkbox in
      cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md citing this doc's todo-3 evidence Source:
      `plans/active/issues/cefi_legacy_dup_delete_tooling_gap_2026_08_09.md`
- [ ] [CODE] P2. execute the operator-approved sports CF-8 targeted backfill
      (market-tick-data-service/scripts/sports_captured_available_at_targeted_backfill_2026_07_14.py) plus the bundled
      CF-3/CF-4 legacy-row cleanup on instruments-store-sports-prd/market-data-tick-sports-prd, per the doc's own
      lease/snapshot/small-scale-first/verify/scale execution notes Source:
      `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`
- [ ] [CODE] P2. add --no-renames to the 4 git show call sites in agent-orchestrator/server/verify.py (~lines 890, 936,
      976, 1028) per the operator-decided option-B fix, plus a regression test pinning bundled-rename+flip detection
      (per task_template.md finding U, a named-file content-level fix, no further design call needed) Source:
      `plans/active/issues/checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md`
- [ ] [CODE] P2. author the implementation plan for the 2026-08-12-ruled local-ratchet-gate-breach escalation detector
      (new wall type in agent-orchestrator/server/escalation.py, 15-minute delayed LDR re-check before dispatch,
      AO-driven remediation that restores the breached ratchet/baseline) after confirming AO-dispatched-vs-human-plan
      routing with the operator Source:
      `plans/active/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md`
- [ ] [CODE] P2. Add AO wall_type for Cloud Build failures (agent-orchestrator/server/escalation.py WALL_TYPES, mirror
      main_ci_red routing) Source: `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [ ] [CODE] P2. Add AO wall_type for main-backmerge-to-ldr sync failures (same escalation.py mechanism) Source:
      `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [ ] [CODE] P2. Fix the 7 failing github-glue-slot-refresh-* systemd units on host i-042a6332509482556 (git-credential
      error on mirror-refresh side-timer) Source: `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [ ] [CODE] P2. Live-verify (or synthetically force) the cloud-build-failure-watcher's coverage-gap self-check actually
      pages CRITICAL when a pool's oldest fetched build is newer than the lookback cutoff Source:
      `plans/active/issues/cloud_build_failure_watcher_limit_30_coverage_gap_silently_drops_failures_under_load_2026_08_10.md`
- [ ] [CODE] P2. Add duration floor (N consecutive failed probes AND outage >= expected_recovery_time_seconds) to
      evaluate_dependency_health's no-fallback branch before any producer is wired Source:
      `plans/active/issues/dependency_health_alerting_never_wired_2026_08_12.md`
- [ ] [CODE] P2. Build the probe-driven producer + wire the *_event_handler.py subscriber into alerting-service's
      subscribers/alert_subscriber.py Source: `plans/active/issues/dependency_health_alerting_never_wired_2026_08_12.md`
- [ ] [CODE] P2. Add an integration test that drives a simulated outage from the producer's entry point and asserts a
      routed alert Source: `plans/active/issues/dependency_health_alerting_never_wired_2026_08_12.md`
- [ ] [CODE] P2. Add a status line to /codex/04-architecture/dependency-health-policy.md stating the feature is
      contract-and-config only until wired Source:
      `plans/active/issues/dependency_health_alerting_never_wired_2026_08_12.md`
- [ ] [CODE] P2. Bisect test_dp_recovery_actuators.py's full-suite contamination against predecessor test files
      (candidates: _\_relaunch_/fleet-monitor/dp-alerts suites; regression window b501a5e5, b34e85a2, 4ca051ea,
      dd7b62e1), find the shared-state leak, add cleanup Source:
      `plans/active/issues/deployment_service_qg_red_11_actuator_tests_suite_order_regression_2026_08_10.md`
- [ ] [CODE] P2. Confirm via Cloud Logging how far back the exit-code-monitor OOM recurrence goes (single blip vs
      sustained) Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [ ] [CODE] P2. Bump cpu/memory on data_pipeline_exit_code_monitor_job in
      terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf (mirror heartbeat-watcher precedent) -- may already be done
      live per the sibling sweep-overlap-storm doc, unconfirmed here Source:
      `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [ ] [CODE] P2. Live-verify vm-census/exit-code-last-run.json advances on schedule for 3+ consecutive cycles post-fix
      with no further signal-9 entries Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [ ] [CODE] P2. Cross-check #data-pipeline-alerts for DP_CRON_DID_NOT_FIRE::vm-census/exit-code-last-run.json during
      the stale window Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [ ] [CODE] P2. Parallelize per-VM GCS reads in sweep() (exit_code_fleet_monitor.py + heartbeat_stall_watcher.py) via
      ThreadPoolExecutor, target <5min sweep, keep classify/route/emit sequential; fallback to reduced cron cadence if
      not shippable Source: `plans/active/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`
- [ ] [DIAG] P2. run launch-measure-honest-coverage-vm.sh --oom-monitor for a fresh right-sizing verification Source:
      `plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`
- [ ] [CODE] P2. UNPAUSE uts-prod-dp-exit-code-monitor-cron in the documented order (verify deploy image carries
      ecd6d2bd90, tombstone-backfill the 393 names, then unpause) Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Make exit_code_fleet_monitor complete a full fleet sweep inside its task timeout or loudly report
      incomplete coverage Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Set the exit-code-monitor Cloud Run job's concurrency to 1 to stop */5 executions overlapping Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Investigate the shared trigger behind ~398 VMs hanging mid-shutdown in the same hour window Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Make a VM stuck mid-shutdown actually terminate (shutdown-path DELETE or a reaper watchdog) Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Verify whether the GCS-backed relaunch budget fix is actually present in the deployed
      deployment-api:latest image Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [ ] [CODE] P2. Re-probe the 39 VMs whose serial-console read returned no parseable timestamp Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
