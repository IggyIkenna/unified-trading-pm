---
doc_type: plan
title: AO consolidated close-out — agent-orchestrator dispatch, worker/slot lifecycle, and framework tooling
summary: >-
  New "topic tranche" umbrella (sibling to the 5 asset groups + cross-cutting) for agent-orchestrator-internal work:
  backlog/dispatch scheduling, worker/slot lifecycle + multi-agent git-safety, orchestrator VM/auth infra, AO
  alerting/observability, and the `agent_operating_framework_master` process tooling that runs the orchestrator itself.
  Authored 2026-07-25 from a corpus-wide classification pass (36 docs, `parent_epic` ∈ `{orchestrator_master,
  agent_operating_framework_master}` plus 8 more reclassified out of the `infrastructure_master` "pure-infra" bucket) —
  part of making the AG↔topic partition (5 AGs + cross-cutting + ao + ci + infra) total across the whole plans/issues
  corpus, per operator request.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, close-out, consolidation, dispatch, slot-lifecycle, worktree]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-25
last_updated: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Corpus-wide classification pass (unified-trading-pm, 2026-07-25) splitting `parent_epic: {orchestrator_master,
  agent_operating_framework_master}` docs (all previously `asset_group: cross-cutting`) plus 8 reclassified
  `infrastructure_master` docs into this AO tranche, per operator request to make the 5-AG + cross-cutting + ao + ci +
  infra topic partition total (zero orphans) for sharded `/plan-reconcile` and `/ag-closeout-audit` runs.
---

# AO consolidated close-out

> **Purpose.** One place to see all agent-orchestrator-internal work. This plan **references** the source docs; it does
> not duplicate their content. Not a data-pipeline or single-AG concern — this is the orchestration substrate everything
> else runs on.

## Reachability map

1. **Dispatch/backlog scheduling bugs** → Track 1
2. **Worker/slot lifecycle + multi-agent git-safety** → Track 2
3. **Orchestrator VM/auth/DB infra** → Track 3
4. **AO alerting/observability + tooling regressions** → Track 4
5. **Session/remediation meta-plans** → Track 5

## Track 1 — Dispatch/backlog scheduling bugs · P0/P1

**Sources**:
[issues/ao_backlog_done_row_disappearance_2026_07_25.md](/plans/active/issues/ao_backlog_done_row_disappearance_2026_07_25.md)
(backlog `state.db` rows silently vanishing, prune bug) ·
[issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md](/plans/active/issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md)
(`PlanRegenLoop.prune_stale` wiped the entire live backlog on a transient zero-scan tick) ·
[issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md](/plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md)
(same backlog task dispatched to two slots simultaneously) ·
[issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md](/plans/active/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md)
(ready P1 task undispatched, no matching worker, autospawn gap) ·
[issues/dispatch_sequential_gate_fix_2026_07_24.md](/plans/active/issues/dispatch_sequential_gate_fix_2026_07_24.md)
(`_claim_plan_for_slot` pinned all tasks to one slot, defeating intra-plan concurrency) ·
[issues/gated_skip_park_no_slack_page_2026_07_25.md](/plans/active/issues/gated_skip_park_no_slack_page_2026_07_25.md)
(GATED skip-task auto-park path never pages Slack) ·
[issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md](/plans/active/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md)
(redispatch churn when a task is gated on an external CI promote, no durable park) ·
[issues/escalation_backlog_repo_collision_blind_spot_2026_07_25.md](/plans/active/issues/escalation_backlog_repo_collision_blind_spot_2026_07_25.md)
(escalation-dispatch vs backlog-dispatch repo-collision blind spot) ·
[issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md](/plans/active/issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md)
(orphan-reaper kills an in-flight detached quickmerge, marks false-done) ·
[issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md](/plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md)
(worker completes with no clean-exit signal, watchdog needlessly rekicks) ·
[issues/auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md](/plans/active/issues/auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md)
(`auto_park.py` doesn't mechanically enforce its own "no park without flipper" rule).

**Close-out criterion**: each dispatch-correctness bug fixed + a regression test added proving the specific race/gap
closed (backlog-prune, double-dispatch, autospawn, sequential-gate, GATED-skip-paging, redispatch-churn, repo-collision,
reaper-false-done, clean-exit-signal, auto-park-enforcement).

## Track 2 — Worker/slot lifecycle + multi-agent git-safety · P0/P1

**Sources**:
[issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md](/plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md)
(killed slot's watchdog frozen-kick loop leaves orphaned unpushed commits) ·
[issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md](/plans/active/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md)
(idle-slot dirty WIP never triggers orphan-inherit — spawn-only mechanism gap) ·
[issues/slot_double_reset_dataloss_race_2026_07_25.md](/plans/active/issues/slot_double_reset_dataloss_race_2026_07_25.md)
(slot worktree double-reset data-loss race, two realign code paths) ·
[issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md](/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md)
(slot recurring wedge at `context_pct=75` needing manual `/compact` confirmation) ·
[issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md](/plans/active/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md)
(shared-worktree autostash restores foreign WIP into the index) ·
[issues/ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md](/plans/active/issues/ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md)
(ahead-push sentinel stale after amend, no rejected-push retry) ·
[issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md](/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md)
(per-slot git-health reporter goes silent on token expiry) ·
[issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md](/plans/active/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md)
(git-health reporter races the FF-pull cron, phantom-dirty flicker) ·
[issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md](/plans/active/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md)
(shared UTL clone repeatedly reset to origin, destroying local commits) ·
[issues/orphan_rootm_branch_unmerged_work_2026_06_05.md](/plans/active/issues/orphan_rootm_branch_unmerged_work_2026_06_05.md)
(orphaned unmerged work on dead root-VM agent-slot branches).

**Close-out criterion**: each git-safety race fixed (killed-slot orphan recovery, idle-slot inherit, double-reset guard,
context-wedge auto-recovery, autostash foreign-WIP protection, sentinel/reporter staleness fixes, shared-clone reset
guard); orphaned branch work recovered or explicitly written off with evidence.

## Track 3 — Orchestrator VM/auth/DB infra · P1

**Sources**:
[issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md](/plans/active/issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md)
(planning-VM relaunch doesn't reprovision the self-hosted glue-runner pool) ·
[issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md](/plans/active/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md)
(SQLAlchemy `QueuePool` exhaustion under concurrent slot traffic) ·
[issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md](/plans/active/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md)
(unpinned JWT secret causes fleet-wide auth outage) ·
[issues/long_lived_vm_logs_not_backed_up_2026_07_02.md](/plans/active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md)
(long-lived planning/epic/central-brain/orchestrator-worker VM logs not backed up) ·
[orchestrator_vm_e2e_hardening_2026_07_24.md](/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md)
(bootstrap/watchdog/memory-guardrail, VM-from-scratch e2e — forked out of `monitoring_control_plane_master` as the
AO-internals slice) ·
[issues/orchestrator_slots_context_directive_issued_missing_migration_2026_07_25.md](/plans/active/issues/orchestrator_slots_context_directive_issued_missing_migration_2026_07_25.md)
(new `SlotRow` ORM column shipped without a hand-rolled migration).

**Close-out criterion**: VM relaunch reprovisions glue-runners; DB pool sized/tuned for concurrent slot load; JWT secret
pinned across the fleet; VM log backup wired; the e2e hardening suite green; the missing migration lands.

## Track 4 — AO alerting/observability + tooling regressions · P1/P2

**Sources**:
[agent_orchestrator_alert_channel_cleanup_2026_07_13.md](/plans/active/agent_orchestrator_alert_channel_cleanup_2026_07_13.md)
(AO alerts Slack channel dedup/lifecycle-churn/BLOCKED-schema redesign) ·
[ao_fleet_observability_kpis_2026_07_20.md](/plans/active/ao_fleet_observability_kpis_2026_07_20.md)
(dispatch-completion/escalator-efficacy/account-burn observability KPIs) ·
[issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md](/plans/active/issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md)
(`plan_health` test suite firing real Slack posts to the AO alerts channel) ·
[issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md](/plans/active/issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md)
(repo-docs cleanup deleted files still referenced in shipped AO server code) ·
[issues/playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md](/plans/active/issues/playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md)
(per-slot Playwright dev-server port collision producing false cross-slot test results) ·
[issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md](/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md)
(AO blocked-question escalation UX/dashboard + dead-agent-context problem).

**Close-out criterion**: alert channel dedup shipped; KPIs live in the dashboard; test suite stops leaking real Slack
posts; dead code refs restored or removed cleanly; Playwright port-collision fixed; blocked-questions UX redesigned.

## Track 5 — Session/remediation meta-plans · P2

**Sources**:
[ao_issue_docs_consolidated_remediation_2026_07_23.md](/plans/active/ao_issue_docs_consolidated_remediation_2026_07_23.md)
(held/blocked residual todos from an AO-scope remediation sweep) ·
[issues/ao_recovery_audit_layer1_deleted_2026_07_15.md](/plans/active/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md)
(AO custom recovery-audit-signoff role/agent deleted as cleanup collateral).

**Close-out criterion**: both docs' residual items closed or explicitly re-deferred with a named owner.

## Codex SSOTs (read before touching a track)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`.

## Progress Log

- **2026-07-25** — Doc authored from a corpus-wide classification pass splitting 234 `asset_group: cross-cutting` docs
  into the 5-AG + cross-cutting + ao + ci + infra topic partition, per operator request. 36 docs classified into this AO
  tranche (26 from `orchestrator_master`/`agent_operating_framework_master` directly + 8 reclassified out of
  `infrastructure_master`'s "pure-infra" bucket + 2 from other epics). No fixes applied in this pass — pure
  consolidation for `/ag-closeout-audit`/`/plan-reconcile` sharding.
