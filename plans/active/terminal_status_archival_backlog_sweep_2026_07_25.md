---
doc_type: plan
title:
  Archive the terminal-status backlog — 53 resolved/false-positive/superseded issue docs + 13 complete/superseded plans
  dual-tracked in plans/active/
summary:
  /codex/11-project-management/issue-doc-lifecycle.md already mandates archive-on-resolve for issue docs and calls a
  resolved-but-still-in-active/issues/ doc review-blocking dual-tracking — but its own audit recipe grepped for a
  frontmatter field (resolved:) that no longer exists in the schema, so it silently caught zero real violations. A
  corrected, machine-enforced version (scripts/plan-hygiene/check_terminal_status_archived.py, wired into
  run_hygiene_sweep.sh, shrinking-ratchet baseline seeded at 66) found the true backlog — 53 issue docs plus the
  parallel plan-side case (13 plans/active/*.md docs whose terminal status is complete/superseded/cancelled). This plan
  archives every one of them per the SSOT's process — banner, git mv to plans/archive/[issues/], corpus-wide referrer
  fixup — so the ratchet baseline can shrink to 0.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [archival, plan-hygiene, issue-lifecycle, dual-tracking, backlog-sweep, terminal-status]
related:
  [/codex/11-project-management/issue-doc-lifecycle.md, /codex/11-project-management/cross-reference-path-convention.md]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "operator request 2026-07-25, following the terminal-status-archived gate finding (check_terminal_status_archived.py,
  seeded baseline 66)"
---

# Archive the terminal-status backlog

## Why `sequential: true`

Each todo's archival step ends with a corpus-wide referrer grep-fix (§ Procedure step 4) — the target set of files that
step touches is NOT knowable in advance and can genuinely overlap between two unrelated todos (a shared parent epic hub,
a shared consolidated-closeout doc, a shared codex SSOT that references several of these docs). The task_template.md §4
rule ("tasks that share a file → `sequential: true`") applies here by construction, not by default-reflex — 66
independent-looking archival todos each carry an unbounded, corpus-wide write footprint in their last step.

## Procedure (same for every todo below — do not repeat this per todo)

For the named doc:

1. **Re-verify the resolution still holds** before archiving — for `status: resolved`, confirm any cited
   `resolved_by:`/banner SHA is real and reachable (`git log --oneline -1 <sha>` in the named repo); for
   `false-positive`/`superseded`, confirm the stated rationale/successor is still accurate (a quick re-read, not a
   re-investigation). **If it doesn't hold, do NOT archive** — leave a `BLOCKED-OPERATOR-DECISION` note in this plan's
   Progress Log citing what doesn't check out, and skip to the next todo. This is the only judgment call in this plan;
   everything else is mechanical.
2. Add/confirm a resolution banner right after the doc's H1 heading, matching the established convention:
   `> **🟢 RESOLVED <date> — <ACKED-INTO-CODE|ACKED-OUT-OF-SCOPE|ACKED-AS-INVALID>** — <one-line citation>` for issue
   docs (state machine states: `/codex/11-project-management/issue-doc-lifecycle.md`); a simple
   `> **Archived <date>** — status was already <status>` for plan docs (no separate state-machine doc exists for plans;
   the terminal `status:` field is itself the record).
3. `git mv` the file: issue docs → `plans/archive/issues/<same-basename>.md`; plan docs →
   `plans/archive/<same-basename>.md` (flat, no date-sharded subdir — matches the one existing precedent,
   `plans/archive/issues/service_control_surface_issues_2026_03_21.md`).
4. `grep -rln "<basename-without-extension>" --include="*.md" plans/ codex/` (excluding the file's own new path) and
   repoint every hit's reference to the new `plans/archive/...` path — this is CLAUDE.md's "update every referrer's path
   corpus-wide" archival-ritual step, applied per-doc rather than per-plan.
5. Verify: `python3 scripts/plan-hygiene/check_terminal_status_archived.py --quiet` no longer lists this path, and
   `python3 scripts/docs/docspec.py`-backed
   `check_frontmatter_schema.py --files <the moved file + every referrer you touched>` is clean.
6. Commit + push per CLAUDE.md git discipline (stage by name, `docs(plans):` prefix, pre-commit
   `git status && git diff --cached --stat` with no path arg) — one commit per todo is fine given `sequential: true`
   serializes anyway; batching a few adjacent todos into one commit is also fine if convenient.

## Todos

- [ ] [INFRA] P0. Archive
      `plans/active/issues/api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/aster_capture_broken_coverage_and_completeness_2026_07_20.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@be0f537c7 (moved to plans/archive/issues/, banner added,
      check_terminal_status_archived.py confirmed clean; 4/5 referrers repointed, 1 blocked on a pre-existing line-cap
      violation — see Progress Log).
- [ ] [INFRA] P0. Archive
      `plans/active/issues/blocked_prerequisites_marker_excluded_from_dispatch_and_gate_2026_07_25.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/branch_quarantine_alert_blind_to_backlog_queue_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@e50c84c88 (moved to plans/archive/issues/, banner added, codex referrer in
      agent-orchestrator-alerting.md repointed + content updated to reflect the shipped fix;
      check_terminal_status_archived.py confirmed clean).
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/candle_feature_canonical_path_divergence_history_part1_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@db253f0c9 (moved to plans/archive/issues/, banner added, all 3 referrers
      repointed; check_terminal_status_archived.py confirmed clean).
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/candle_feature_canonical_path_divergence_history_part2_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@40f3c5b65 (moved to plans/archive/issues/, banner added, parent doc's 3
      referrers repointed; check_terminal_status_archived.py confirmed clean).
- [x] [INFRA] P0. ✅ Archive
      `plans/active/issues/cefi_okx_margin_type_wire_key_ambiguity_reclassification_2026_07_22.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it. —
      unified-trading-pm@24878e802 (moved to plans/archive/issues/, banner added, all 3 referrers repointed;
      check_terminal_status_archived.py confirmed clean).
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/cefi_residual_followups_after_honest_done_history_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@77abcc1e6 (moved to plans/archive/issues/, banner added, parent doc's
      referrer repointed; check_terminal_status_archived.py confirmed clean).
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/codex_alignment_deviations_2026_06_25.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it. —
      unified-trading-pm@9fe6cd627 (moved to plans/archive/issues/, banner added, plan_hygiene_master epic referrer
      repointed; check_terminal_status_archived.py confirmed clean).
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/defi_pool_canonical_instrument_id_policy_contradiction_2026_07_17.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@79d56a054 (moved to plans/archive/issues/, banner added, all 3 referrers
      repointed; check_terminal_status_archived.py confirmed clean).
- [ ] [INFRA] P0. Archive
      `plans/active/issues/deployment_api_cefi_venue_canonical_compare_test_regression_2026_07_21.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/deployment_api_inventory_cold_path_concurrent_oom_2026_07_24.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@54cbb2dae (moved to plans/archive/issues/, banner added, both referrers in
      the sibling reaper-drain doc repointed; check_terminal_status_archived.py confirmed clean).
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/deployment_promote_squash_ancestry_false_negative_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@bc48ccf2d (moved to plans/archive/issues/, banner added, all 5 referrers
      across 3 plans + 1 codex doc repointed; check_terminal_status_archived.py confirmed clean).
- [ ] [INFRA] P0. Archive
      `plans/active/issues/detached_nohup_worker_processes_reaped_as_orphans_by_config_dir_match_2026_07_24.md`
      (status=superseded, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/escalation_boot_template_ignores_one_shot_lifecycle_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@0c21c56c2 (moved to plans/archive/issues/, banner added, no other corpus
      referrers; check_terminal_status_archived.py confirmed clean).
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/finalize_plan_coverage_regression_2_plans_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@e31106704 (moved to plans/archive/issues/, banner added, no corpus referrers
      to repoint; check_terminal_status_archived.py confirmed clean).
- [ ] [INFRA] P0. Archive
      `plans/active/issues/fixtures_schedule_atom_migration_partial_landing_regression_2026_07_24.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@d31c02a96 (moved to plans/archive/issues/, banner added,
      check_terminal_status_archived.py confirmed clean; 0/1 referrer repointed, blocked on a pre-existing line-cap
      violation — see Progress Log).
- [x] [INFRA] P0. ✅ Archive `plans/active/issues/gas_fees_lst_rates_manifest_bucket_mismatch_2026_07_10.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it. — unified-trading-pm@f6ec0a848 (moved to plans/archive/issues/, banner added, 5/5 real path
      referrers repointed; check_terminal_status_archived.py confirmed clean).
- [ ] [INFRA] P0. Archive `plans/active/issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md`
      (status=superseded, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/gsutil_broken_credentials_blocks_vm_tarball_republish_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/instruments_service_deribit_combo_purge_test_drift_2026_07_21.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/instruments_service_fx_adapter_key_unresolved_2026_07_23.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/mdps_canonical_writer_adapter_contract_baseline_regression_2026_07_24.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/mdt_t2_6_league_case_duplicate_population_2026_07_16.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/mtds_lst_extended_rates_uncited_addresses_2026_07_19.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/mtds_rule11_shard_count_stale_baseline_2026_07_21.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive
      `plans/active/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/plan_hygiene_sweep_transient_failure_2026_07_25.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/plan_line_cap_remediation_2026_07_23.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/plan_reconciliation_operator_decisions_history_part1_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/plan_reconciliation_operator_decisions_history_part2_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/plan_reconciliation_operator_decisions_history_part3_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/plan_reconciliation_operator_decisions_history_part4_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive
      `plans/active/issues/precommit_hooks_workspace_root_resolves_to_main_not_worktree_2026_07_25.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive
      `plans/active/issues/precommit_plan_hygiene_hook_worktree_workspace_root_misresolution_2026_07_25.md`
      (status=superseded, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive
      `plans/active/issues/qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/recovery_plan_source_liveness_probe_gap_2026_07_25.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/sit_main_ldr_drift_no_auto_promote_2026_07_13.md` (status=resolved,
      doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/sports_closeout_batch1_task018_partial_progress_2026_07_24.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/sports_halftime_odds_sfi_vs_inplay_history_part1_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/sports_halftime_odds_sfi_vs_inplay_history_part2_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md`
      (status=superseded, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive
      `plans/active/issues/sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive
      `plans/active/issues/sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive
      `plans/active/issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/verify_p1_prereq_dag_2026_06_29.md` (status=resolved, doc_type=issue) per
      the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/issues/zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`
      (status=resolved, doc_type=issue) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/ag_closeout_audit_rollout_2026_07_25.md` (status=complete, doc_type=plan) per
      the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/artifact_pipeline_observability_history_2026_07_24.md` (status=complete,
      doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/defi_consolidated_closeout_history_2026_07_25.md` (status=complete,
      doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md`
      (status=complete, doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer
      lists it.
- [ ] [INFRA] P0. Archive `plans/active/infra_capture_and_devops_leftovers_2026_07_06_finalize_2026_07_25.md`
      (status=superseded, doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no
      longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md` (status=complete,
      doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/mvp_backfill_defi_onchain_v10_operational_log_part2_2026_07_24.md`
      (status=complete, doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer
      lists it.
- [ ] [INFRA] P0. Archive `plans/active/mvp_backfill_defi_onchain_v10_operational_log_part3_2026_07_24.md`
      (status=complete, doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer
      lists it.
- [ ] [INFRA] P0. Archive `plans/active/mvp_backfill_defi_onchain_v10_operational_log_part4_2026_07_24.md`
      (status=complete, doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer
      lists it.
- [ ] [INFRA] P0. Archive `plans/active/mvp_backfill_defi_onchain_v10_operational_log_part5_2026_07_24.md`
      (status=complete, doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer
      lists it.
- [ ] [INFRA] P0. Archive `plans/active/mvp_backfill_defi_onchain_v10_operational_log_part6_2026_07_24.md`
      (status=complete, doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer
      lists it.
- [ ] [INFRA] P0. Archive `plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (status=superseded,
      doc_type=plan) per the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.
- [ ] [INFRA] P0. Archive `plans/active/tradfi_massive_dual_source_2026_05_28.md` (status=superseded, doc_type=plan) per
      the Procedure below. Done when: `check_terminal_status_archived.py` no longer lists it.

## Deferred

None at authoring time — every violation the gate found is enumerated above. If step 1's re-verification fails for any
item, it becomes a `BLOCKED-OPERATOR-DECISION` Progress Log entry (see Procedure step 1), not a silent skip.

## Progress Log

- 2026-07-25 (slot-7): Todo 2 (`aster_capture_broken_coverage_and_completeness_2026_07_20.md`) archived — resolution
  re-verified (all 4 cited SHAs reachable: `execution-service@e11e6a136`, `unified-trading-pm@12b0d9db8`,
  `market-tick-data-service@d8efc6d6`, `market-tick-data-service@a7f7769a`), banner added, moved to
  `plans/archive/issues/`, `check_terminal_status_archived.py` confirmed clean. Step 4 (corpus-wide referrer fixup)
  completed for 5 of 6 referrers. **One referrer left un-fixed**:
  `plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` (its `related:` frontmatter still points
  at the old `plans/active/issues/...` path) — that file is 1216 lines, already over the 1000L hard line-cap
  (pre-existing, unrelated to this edit), and `check_line_caps.sh`'s scoped pre-commit check refuses ANY staged commit
  touching an over-cap file (by design, no exceptions — see the script's own comments). Fixing the referrer requires
  first splitting that doc under the cap, which is out of scope for a single-line path fix. Leaving as a known, tracked
  gap rather than blocking this archival or bypassing the gate.
- 2026-07-25 (slot-2): Todo (`fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md`) archived —
  resolution re-verified (`resolved_by` SHA `features-service@fb8d57c0` confirmed reachable), banner added, moved to
  `plans/archive/issues/`, `check_terminal_status_archived.py` confirmed clean. Same class of blocker as slot-7's entry
  above: its 1 corpus referrer (`plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md`) is already at exactly
  the 1000-line hard cap — the one-line path repoint pushes it to 1001 and `check_line_caps` hard-fails the commit.
  Reverted the repoint edit; left the stale `issues/...` relative reference un-fixed as a known, tracked gap rather than
  blocking this archival.
- **2026-07-25 (slot-7) — BLOCKED-OPERATOR-DECISION**: `gcs_hive_partition_malformed_paths_remediation_2026_06_01.md`
  (status=superseded). Re-verified the resolution itself holds (recurrence-guard SHA `unified-trading-pm@5d6d398e4`
  reachable; both cited successors — `plans/archive/2026_07/tradfi_manifest_canonicalisation_2026_06_01.md` E7 and
  `plans/archive/2026_07/cefi_manifest_canonicalisation_2026_06_01.md` E2 — exist, are themselves `status: superseded`
  (already archived), and each explicitly confirms completing the exact remediation this doc's Pattern 1/Pattern 2
  cite). **But the doc itself still carries `locked_by: live-defi-rollout`** in its frontmatter — per CLAUDE.md's plan-
  locking HARD RULE, a locked doc is never autonomously archived, only via an explicit `[unlock-plan]` from the
  operator. This exact blocker was already surfaced (not yet acted on) by
  `plans/active/issues/canonical_closeout_open_questions_2026_07_18.md`'s own C1 entry: "locked plans are never
  autonomous-archived; needs `[unlock-plan]`. REC: unlock + archive." Not archiving; leaving the checkbox unflipped and
  skipping this task (reason_code GATED) until the operator authorizes `[unlock-plan]`.
- **2026-07-25 (slot-2): BLOCKED-OPERATOR-DECISION — todo
  (`gcs_hive_partition_malformed_paths_remediation_2026_06_01.md`) NOT archived.** Resolution itself checks out
  (`resolved_by` cites `tradfi_manifest_canonicalisation_2026_06_01.md` E7
  - `cefi_manifest_canonicalisation_2026_06_01.md` E2, both already archived at `plans/archive/2026_07/`, confirming
    they ran to completion; recurrence-guard SHA `unified-trading-pm@5d6d398e4` reachable) — but the doc itself carries
    `locked_by: live-defi-rollout` with no `[unlock-plan]` on record. Per CLAUDE.md's plan-locking HARD RULE, a locked
    doc is never autonomous-archived. This is NOT a stray/boilerplate `locked_by` value on this particular doc — the
    corpus already flags it as a PARKED, unanswered operator-decision item:
    `canonical_closeout_open_questions_2026_07_18.md` § C. `/plan-reconcile` parked rulings, item **C1** — "archival of
    `gcs_hive_partition_malformed_paths_remediation_ 2026_06_01.md` (terminal/superseded but
    `locked_by: live-defi-rollout`) — locked plans are never autonomous-archived; needs `[unlock-plan]`. REC: unlock +
    archive." No operator answer is recorded there yet. Leaving the checkbox unchecked and NOT archiving this session —
    doing so would be the exact autonomous-unlock CLAUDE.md forbids. Next dispatch: check whether C1 has since been
    answered in `canonical_closeout_open_questions_2026_07_18.md`; if yes and the answer is unlock+archive, proceed per
    the normal Procedure; if still unanswered, this stays parked (not this sweep's call to make).
- **2026-07-25 (slot-3): RE-DISPATCHED, re-confirmed still parked, NOT archived.** Re-checked both gates slot-2 found:
  (1) `plans/active/issues/gcs_hive_partition_malformed_paths_remediation_2026_06_01.md` frontmatter still carries
  `locked_by: live-defi-rollout` (unchanged). (2) `canonical_closeout_open_questions_2026_07_18.md` § C1 still reads as
  a standing "REC: unlock + archive" recommendation with no recorded operator answer/decision timestamp — nothing has
  changed since slot-2's pass. No new archival action taken (would violate the plan-locking HARD RULE). This is the SAME
  dispatch-churn class main just filed for a different external gate:
  `plans/active/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` (an
  `auto_unpark__<task-id>`-style durable park, not a worker-applied `priority_override`, is the fix that survives
  backlog re-derivation) — cross-referencing rather than filing a duplicate issue doc. Not filing a fresh `/blocked`
  either: C1 is already a live, unanswered, correctly-worded operator recommendation in the tracker doc; a second
  identical escalation adds noise, not new information. Skipping this task via `/skip-current-task` so it releases
  cleanly; the durable-park BACKEND fix above is the tracked remediation for the repeat-dispatch cost itself.
- **2026-07-25 (slot-6): RE-DISPATCHED again, re-confirmed still parked, NOT archived.** Both gates unchanged since
  slot-3's pass: `locked_by: live-defi-rollout` still set on the doc's frontmatter; C1 in
  `canonical_closeout_open_questions_2026_07_18.md` still an unanswered `[unlock-plan]` recommendation. No new archival
  action (would violate the plan-locking HARD RULE). I don't have write access to the orchestrator's runtime
  `backlog.yaml` from this slot (it's server-side state, not a repo file I can edit), so I can't apply the durable-park
  fix myself — skipping via `/skip-current-task` per the same precedent as slot-3.
- **2026-07-25 (slot-9): RE-DISPATCHED again, re-confirmed still parked, NOT archived.** Both gates unchanged since
  slot-6's pass: `locked_by: live-defi-rollout` still on the doc; C1 in
  `canonical_closeout_open_questions_2026_07_18.md` still unanswered. No `backlog.yaml` in this slot's
  `agent-orchestrator` checkout either (confirmed via `find`) — same no-durable-park-access constraint slots 2/3/6 hit.
  Skipping via `/skip-current-task`; this is now the 4th consecutive re-dispatch of the identical parked task,
  underscoring `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`'s P3 backend todo (durable
  `auto_unpark__` prereq for worker-applied parks) — no new issue doc needed, that one already tracks it.
- **2026-07-25 (slot-10): RE-DISPATCHED again, re-confirmed still parked, NOT archived.** Both gates unchanged since
  slot-9's pass: `locked_by: live-defi-rollout` still on the doc's frontmatter; C1 in
  `canonical_closeout_open_questions_2026_07_18.md` still an unanswered `[unlock-plan]` recommendation. No new archival
  action taken (would violate the plan-locking HARD RULE). This is now the 5th consecutive re-dispatch of the identical
  parked task — the durable-park backend fix tracked in
  `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` (P3) is the actual remediation for this
  churn, not a fresh escalation. Skipping via `/skip-current-task`.
- **2026-07-25 (slot-11): RE-DISPATCHED again, re-confirmed still parked, NOT archived.** Both gates unchanged since
  slot-10's pass: `locked_by: live-defi-rollout` still on the doc's frontmatter; C1 in
  `canonical_closeout_open_questions_2026_07_18.md` still an unanswered `[unlock-plan]` recommendation. No new archival
  action taken (would violate the plan-locking HARD RULE). This is now the 6th consecutive re-dispatch of the identical
  parked task — same remediation tracked in `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`
  (P3), no fresh escalation needed. Skipping via `/skip-current-task`.
- **2026-07-25 (slot-4): RE-DISPATCHED again, re-confirmed still parked, NOT archived.** Both gates unchanged since
  slot-11's pass: `locked_by: live-defi-rollout` still on the doc's frontmatter (line 34); C1 in
  `canonical_closeout_open_questions_2026_07_18.md` (line 114-116) still an unanswered `[unlock-plan]` recommendation.
  No new archival action taken (would violate the plan-locking HARD RULE). This is now the 7th consecutive re-dispatch
  of the identical parked task — same remediation tracked in
  `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md` (P3), no fresh escalation needed.
  Skipping via `/skip-current-task`.
