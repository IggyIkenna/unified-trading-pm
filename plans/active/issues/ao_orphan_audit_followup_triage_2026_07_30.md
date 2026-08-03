---
doc_type: issue
title:
  Four concrete follow-ups from the 2026-07-30 `/ag-closeout-audit ao` orphan sweep — not yet tracked anywhere as
  actionable todos, only agreed in an interactive session
summary: >-
  The 2026-07-30 `/ag-closeout-audit ao` sweep (see `ao_open_issues_consolidated_close_out_2026_07_17.md`'s "Satellite
  AO-dispatch layer" section for the full bucketed index) classified 41 AO-tagged docs. The tracker doc itself is at
  996/1000 hard-capped lines with no room to add real `- [ ]` todos for the next steps the operator and main agent
  agreed on, so they're captured here instead. None of these four are done yet.
status: open
resolved_by:
locked_by:
nature: issue
asset_group: [ao]
scope: [engineer, admin]
stage: [meta]
repos: [unified-trading-pm]
tags: [agent-orchestrator, ag-closeout-audit, triage, orphan-docs, consolidation]
related:
  [
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
  ]
created: 2026-07-30
priority: P2
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
context_scope:
  [
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
source:
  "interactive session, 2026-07-30 — operator ran the ao-tranche orphan audit, had the tracker's related: links +
  archival gap fixed, then said: archive what can be archived now, then work the resolution bucket next. This issue
  captures the remaining agreed-but-untracked next steps so they survive a context compaction."
---

## Todos

- [ ] [OPERATOR] P1. **Approve/dispatch `ao_satellite_ao_dispatch_batch2_2026_07_30.md`** (flip `status: draft` →
      `active`). It already carries real, ready fixes for 6 docs from the orphan sweep (was 7 —
      `orphan_rootm_branch_unmerged_work_2026_06_05` resolved + archived 2026-07-30 directly, moot, no batch2 fix
      needed): `ao_done_require_origin_not_enforced_2026_07_29`, `dispatch_sequential_gate_fix_2026_07_24`,
      `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27`,
      `git_status_reporter_stale_public_url_token_expiry_2026_07_24`,
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24`,
      `ao_recovery_audit_layer1_deleted_2026_07_15` — nothing else is needed to unblock them. **Done when**:
      `status: active` + AO has picked it up (`/check-agent-orchestrator`).
- [ ] [OPERATOR] P1. **Rule on the 12 operator-gated docs from the orphan sweep**, one at a time — each is a genuine
      design/judgment fork with no evidence-based tiebreaker, per Phase 1 of the audit:
      `escalation_backlog_repo_collision_blind_spot_2026_07_25`,
      `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25`,
      `autostash_pop_restores_foreign_wip_into_the_index_2026_07_17`,
      `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24`, `long_lived_vm_logs_not_backed_up_2026_07_02`,
      `mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27`,
      `prediction_trades_migration_concurrent_dispatch_2026_07_28`,
      `idle_slot_dirty_wip_never_auto_resolves_2026_07_20`, `unified_trading_pm_stash_pile_accumulation_2026_07_26`,
      `per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27`,
      `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15`,
      `wip_preserve_refs_silently_unrecovered_2026_07_29`. **Done when**: each doc has a recorded ruling (fold into a
      batch, park explicitly, or close as moot).
- [ ] [REVIEW] P2. **Re-triage the 8 "conflict-gated" docs against current state** before drafting `batch3` — per the
      skill's own iterative-drain methodology, check whether the competing claim each collided with (in
      `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s `## Deferred` section) has since shipped or superseded:
      `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24`,
      `one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25`,
      `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26`,
      `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25`,
      `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21`,
      `utl_shared_clone_commits_repeatedly_reset_2026_07_22`,
      `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24`,
      `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25`. **Done when**: each is re-classified
      cleared/still-gated with evidence.
- [ ] [REVIEW] P2. **Read + properly bucket the remaining 7 "unclear" docs** the Phase-1 audit agent couldn't cleanly
      classify (was 8 — `unified_trading_system_ui_e2e_specs_hardcode_ports_bypass_per_slot_derivation_2026_07_28`
      bucketed **archivable/ACKED-INTO-CODE 2026-08-01**: its last open todo shipped unified-trading-system-ui@741d0a6b,
      all 3 batches done, no `locked_by` — archived per `/codex/11-project-management/issue-doc-lifecycle.md`):
      `ao_context_pct_0_for_monitor_heavy_workers_2026_07_29`,
      `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28`,
      `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25`,
      `na_eligibility_auditor_timer_not_yet_installed_2026_07_27`,
      `mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29`,
      `plan_health_tests_leak_real_slack_alerts_2026_07_24`,
      `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26`. **Done when**: each lands in one of the standard
      verdict buckets (conflict-gated / operator-gated / archivable / covered) with reasoning.

## Progress Log

- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — all 4
  todos are judgment-heavy, not worker-determinable alone: 2 are explicitly `[OPERATOR]`-tagged (approve/dispatch
  batch2, rule on 12 operator-gated docs each a genuine design/judgment fork with no evidence-based tiebreaker), the
  other 2 `[REVIEW]`-tagged items require open-ended audit judgment (classify 8 conflict-gated docs, bucket 7 unclear
  docs) — the same shape as this skill's own work, not a deterministic check. No stale/superseded items found.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: populated/refreshed context_scope (4 entries).
