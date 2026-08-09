---
doc_type: plan
title: AO consolidated close-out — agent-orchestrator dispatch, worker/slot lifecycle, and framework tooling
summary: >-
  New "topic tranche" umbrella (sibling to the 5 asset groups + cross-cutting) for agent-orchestrator-internal work:
  backlog/dispatch scheduling, worker/slot lifecycle + multi-agent git-safety, orchestrator VM/auth infra, AO
  alerting/observability, and the `agent_operating_framework_master` process tooling that runs the orchestrator itself.
  Authored 2026-07-25 from a corpus-wide classification pass over `parent_epic` ∈ `{orchestrator_master,
  agent_operating_framework_master}` plus docs reclassified out of the `infrastructure_master` "pure-infra" bucket —
  part of making the AG↔topic partition (5 AGs + cross-cutting + ao + ci + infra) total across the whole plans/issues
  corpus, per operator request. The Tracks' **Sources** lists below are the authoritative membership (they are what a
  topic-scoped `/plan-reconcile ao` / `/ag-closeout-audit ao` run resolves against) — count them, do not restate a count
  here.
status:
  complete # (was: active) 2026-07-30 finalize sweep (ao_consolidated_closeout_2026_07_25_finalize_2026_07_30.md): both
  # `## Todos` items re-verified against their own stated regression-test done-when (agent-orchestrator@64b5310 +
  # @77fc60a both confirmed ancestors of live-defi-rollout HEAD, both named regression tests re-run live and PASS);
  # zero `- [ ]` remain, `locked_by:` empty -- archival-eligible per plan-completion-and-archival-discipline.md.
nature: process
asset_group:
  [ao] # corrected 2026-07-29 (ag-closeout-audit cross-cutting-tranche run) -- was [cross-cutting]. This is the `ao`
  # tranche's OWN top-level consolidated-closeout/coordinator doc; the 2026-07-27 asset_group_ao_ci_infra_schema_
  # expansion retag (unified-trading-pm@a97bc7bed) re-derived membership for docs CITED in each tranche's Sources
  # list but missed each tranche's own master doc, which still carried its pre-2026-07-27 [cross-cutting] tag.
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, close-out, consolidation, dispatch, slot-lifecycle, worktree]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-25
last_updated: "2026-07-29"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
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
  agent_operating_framework_master}` docs (all previously `asset_group: cross-cutting`) plus reclassified
  `infrastructure_master` docs into this AO tranche, per operator request to make the 5-AG + cross-cutting + ao + ci +
  infra topic partition total (zero orphans) for sharded `/plan-reconcile` and `/ag-closeout-audit` runs.
---

## Deferred work — migrated to:

**N/A — this doc is a pure reachability digest, not a work-owning plan** (its own words: "this doc carries **zero todos
of its own**" outside the 2 `## Todos` items just closed). Archiving it does NOT close the AO tranche's underlying work
— the 2026-07-30 `/ag-closeout-audit ao` audit found 37/44 Sources still orphaned; that live picture is tracked in
`ao_satellite_ao_dispatch_batch1_2026_07_26.md` (+ its gated finalize) and the still-open
`ao_open_issues_consolidated_close_out_2026_07_17.md`, not here.

> **🗄️ ARCHIVED 2026-07-30** (`ao_consolidated_closeout_2026_07_25_finalize_2026_07_30.md`'s own todo) — this doc's own
> scope (its 2 `## Todos` items) is complete and `locked_by:` is empty; per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` a plan with every top-level todo `[x]` archives
> immediately. Does not represent the `ao` topic tranche being done — see the still-active satellite/open-issues plans
> named above for that.

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

## AO-dispatch batches extracted from these Sources (the actual dispatch surface)

This doc is a **digest** — being listed as a Source below is discoverability, NOT dispatch, and this doc carries **zero
todos of its own**. The plans that actually work these docs' open items:

- [ao_satellite_ao_dispatch_batch1_2026_07_26](/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md) —
  **archived 2026-08-01, all 11 todos `[x]`** (was `status: draft`; operator-approved and shipped) + its gated pair
  [ao_satellite_ao_dispatch_batch1_finalize_2026_07_26](/plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md),
  also archived. Superseded by
  [ao_satellite_ao_dispatch_batch2_2026_07_30](/plans/active/ao_satellite_ao_dispatch_batch2_2026_07_30.md),
  [batch3_2026_07_31](/plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md),
  [batch4_2026_08_01](/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md) (now archived, complete),
  and [batch5_2026_08_03](/plans/active/ao_satellite_ao_dispatch_batch5_2026_08_03.md) (`status: draft`, awaiting
  operator approval) — each with its own gated `_finalize` pair — as the tranche's iterative-drain audit cycle continued
  per the skill's own methodology.
- [ao_open_issues_consolidated_close_out_2026_07_17](/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md)
  — an earlier AO-scope tracker (8 open todos as of 2026-08-04) that is **not** in the Sources lists below but does
  cover some of them (its Recovery-audit Layer-1 producer todo owns
  `issues/ao_recovery_audit_layer1_deleted_2026_07_15.md`). Confirmed (2026-08-04) as a genuine `ao`-tranche covering
  plan — treated as such by every batch2-5 audit run since.
- **2026-08-04 (`/ag-closeout-audit ao`, autonomous) — Orthogonality HARD CHECK found + retagged 8 genuine `ao`
  mistags** (bare `[meta]`/`[cross-cutting]` with `orchestrator_master`/`agent_operating_framework_master`
  `parent_epic`, each verified by reading the doc's real content, not tag shape):
  [ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02](/plans/active/issues/ao_done_gate_tag_correlation_false_match_on_leading_marker_2026_08_02.md),
  [boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31](/plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md),
  [orphaned_wip_slot12_slot8_recovery_2026_08_04](/plans/active/issues/orphaned_wip_slot12_slot8_recovery_2026_08_04.md),
  [backlog_regen_reverted_p1_2_park_2026_08_01](/plans/active/issues/backlog_regen_reverted_p1_2_park_2026_08_01.md),
  [p1_2_backlog_hand_park_did_not_persist_2026_07_31](/plans/archive/issues/p1_2_backlog_hand_park_did_not_persist_2026_07_31.md),
  [fleet_git_health_ip_185_known_human_planning_vm_2026_08_03](/plans/archive/issues/fleet_git_health_ip_185_known_human_planning_vm_2026_08_03.md),
  [na_and_ag_closeout_audit_population_overlap_2026_07_31](/plans/active/issues/na_and_ag_closeout_audit_population_overlap_2026_07_31.md),
  [na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30](/plans/active/issues/na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30.md).
  None yet covered by a dispatched batch — see this run's own report (`ag_closeout_audit_ao_parked_2026_08_04.md` / the
  next satellite batch) for disposition.

## Track 1 — Dispatch/backlog scheduling bugs · P0/P1

**Sources**:
[issues/ao_backlog_done_row_disappearance_2026_07_25.md](/plans/archive/issues/ao_backlog_done_row_disappearance_2026_07_25.md)
(backlog `state.db` rows silently vanishing — RESOLVED 2026-07-28,
`agent-orchestrator@b926a9262c4ef592f1bfe644b0c0e03cac3335ef`) ·
[issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md](/plans/archive/issues/orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md)
(`PlanRegenLoop.prune_stale` wiped the entire live backlog on a transient zero-scan tick — now archived, resolved) ·
[issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md](/plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md)
(same backlog task dispatched to two slots simultaneously) ·
[issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md](/plans/archive/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md)
(ready P1 task undispatched, no matching worker, autospawn gap) ·
[issues/dispatch_sequential_gate_fix_2026_07_24.md](/plans/archive/issues/dispatch_sequential_gate_fix_2026_07_24.md)
(`_claim_plan_for_slot` pinned all tasks to one slot, defeating intra-plan concurrency) ·
[issues/gated_skip_park_no_slack_page_2026_07_25.md](/plans/archive/issues/gated_skip_park_no_slack_page_2026_07_25.md)
(GATED skip-task auto-park path never pages Slack) ·
[issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md](/plans/archive/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md)
(redispatch churn when a task is gated on an external CI promote, no durable park) ·
[issues/escalation_backlog_repo_collision_blind_spot_2026_07_25.md](/plans/archive/issues/escalation_backlog_repo_collision_blind_spot_2026_07_25.md)
(escalation-dispatch vs backlog-dispatch repo-collision blind spot) ·
[issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md](/plans/active/issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md)
(orphan-reaper kills an in-flight detached quickmerge, marks false-done) ·
[issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md](/plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md)
(worker completes with no clean-exit signal, watchdog needlessly rekicks) ·
[issues/auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md](/plans/archive/issues/auto_park_no_flipper_rule_not_mechanism_enforced_2026_07_20.md)
(`auto_park.py` doesn't mechanically enforce its own "no park without flipper" rule).

**Close-out criterion**: each dispatch-correctness bug fixed + a regression test added proving the specific race/gap
closed (backlog-prune, double-dispatch, autospawn, sequential-gate, GATED-skip-paging, redispatch-churn, repo-collision,
reaper-false-done, clean-exit-signal, auto-park-enforcement).

## Track 2 — Worker/slot lifecycle + multi-agent git-safety · P0/P1

**Sources**:
[issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md](/plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md)
(killed slot's watchdog frozen-kick loop leaves orphaned unpushed commits) ·
[issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md](/plans/archive/issues/idle_slot_dirty_wip_never_auto_resolves_2026_07_20.md)
(idle-slot dirty WIP never triggers orphan-inherit — spawn-only mechanism gap) ·
[issues/slot_double_reset_dataloss_race_2026_07_25.md](/plans/archive/issues/slot_double_reset_dataloss_race_2026_07_25.md)
(slot worktree double-reset data-loss race, two realign code paths) ·
[issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md](/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md)
(slot recurring wedge at `context_pct=75` needing manual `/compact` confirmation) ·
[issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md](/plans/archive/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md)
(shared-worktree autostash restores foreign WIP into the index) ·
[issues/ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md](/plans/active/issues/ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24.md)
(ahead-push sentinel stale after amend, no rejected-push retry) ·
[issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md](/plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md)
(per-slot git-health reporter goes silent on token expiry) ·
[issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md](/plans/archive/issues/git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md)
(git-health reporter races the FF-pull cron, phantom-dirty flicker) ·
[issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md](/plans/active/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md)
(shared UTL clone repeatedly reset to origin, destroying local commits) ·
[issues/orphan_rootm_branch_unmerged_work_2026_06_05.md](/plans/archive/issues/orphan_rootm_branch_unmerged_work_2026_06_05.md)
(orphaned unmerged work on dead root-VM agent-slot branches) ·
[issues/slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md](/plans/active/issues/slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md)
(retagged `[ao]` 2026-08-09 from a `[cross-cutting]` mistag — WorkerLivenessWatchdog resume-kick loop stuck at
`phase=pre_boot`, never escalating to a clean kill+respawn; 1 of its 3 open items already claimed by
`ao_satellite_ao_dispatch_batch5_2026_08_03.md`, 2 remain `[OPERATOR]`-gated).

**Close-out criterion**: each git-safety race fixed (killed-slot orphan recovery, idle-slot inherit, double-reset guard,
context-wedge auto-recovery, autostash foreign-WIP protection, sentinel/reporter staleness fixes, shared-clone reset
guard); orphaned branch work recovered or explicitly written off with evidence.

## Track 3 — Orchestrator VM/auth/DB infra · P1

**Sources**:
[issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md](/plans/archive/issues/central_vm_relaunch_does_not_reregister_glue_runners_2026_07_24.md)
(planning-VM relaunch doesn't reprovision the self-hosted glue-runner pool) ·
[issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md](/plans/active/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md)
(SQLAlchemy `QueuePool` exhaustion under concurrent slot traffic) ·
[issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md](/plans/archive/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md)
(unpinned JWT secret causes fleet-wide auth outage) ·
[issues/long_lived_vm_logs_not_backed_up_2026_07_02.md](/plans/active/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md)
(long-lived planning/epic/central-brain/orchestrator-worker VM logs not backed up) ·
[orchestrator_vm_e2e_hardening_2026_07_24.md](/plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md)
(bootstrap/watchdog/memory-guardrail, VM-from-scratch e2e — forked out of `monitoring_control_plane_master` as the
AO-internals slice) ·
[issues/orchestrator_slots_context_directive_issued_missing_migration_2026_07_25.md](/plans/archive/issues/orchestrator_slots_context_directive_issued_missing_migration_2026_07_25.md)
(new `SlotRow` ORM column shipped without a hand-rolled migration).

**Close-out criterion**: VM relaunch reprovisions glue-runners; DB pool sized/tuned for concurrent slot load; JWT secret
pinned across the fleet; VM log backup wired; the e2e hardening suite green; the missing migration lands.

## Track 4 — AO alerting/observability + tooling regressions · P1/P2

**Sources**:
[agent_orchestrator_alert_channel_cleanup_2026_07_13.md](/plans/archive/2026_07/agent_orchestrator_alert_channel_cleanup_2026_07_13.md)
(complete, archived 2026-07-27 — AO alerts Slack channel dedup/lifecycle-churn/BLOCKED-schema redesign) ·
[ao_fleet_observability_kpis_2026_07_20.md](/plans/archive/2026_07/ao_fleet_observability_kpis_2026_07_20.md)
(dispatch-completion/escalator-efficacy/account-burn observability KPIs, archived 2026-07-31) ·
[issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md](/plans/archive/issues/plan_health_tests_leak_real_slack_alerts_2026_07_24.md)
(`plan_health` test suite firing real Slack posts to the AO alerts channel) ·
[issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md](/plans/archive/issues/ao_repo_docs_deleted_against_instructions_dead_code_refs_2026_07_23.md)
(repo-docs cleanup deleted files still referenced in shipped AO server code) ·
[issues/playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md](/plans/archive/issues/playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md)
(per-slot Playwright dev-server port collision producing false cross-slot test results) ·
[issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md](/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md)
(AO blocked-question escalation UX/dashboard + dead-agent-context problem).

**Close-out criterion**: alert channel dedup shipped; KPIs live in the dashboard; test suite stops leaking real Slack
posts; dead code refs restored or removed cleanly; Playwright port-collision fixed; blocked-questions UX redesigned.

## Track 5 — Session/remediation meta-plans · P2

**Sources**:
[ao_issue_docs_consolidated_remediation_2026_07_23.md](/plans/archive/2026_07/ao_issue_docs_consolidated_remediation_2026_07_23.md)
(archived 2026-07-27 — the Q2-held todos shipped and 2 of 4 non-dispatchable items resolved; the remaining 2,
route-collision + backlog-relations-view, are DEFERRED per operator instruction rather than held open) ·
[issues/ao_recovery_audit_layer1_deleted_2026_07_15.md](/plans/active/issues/ao_recovery_audit_layer1_deleted_2026_07_15.md)
(AO custom recovery-audit-signoff role/agent deleted as cleanup collateral) ·
[ao_open_issues_consolidated_close_out_2026_07_17.md](/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md)
(9 open/32 done — added 2026-07-26, resolved `autonomous_session_operator_decisions_2026_07_25.md` entry #25, option A/C
combined: this doc was the single most-important covering plan actually tracking real AO-tranche work and had been
missing from Sources entirely) ·
[context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md](/plans/active/context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md)
(retagged `[ao]` 2026-08-09 from a `[ao, cross-cutting]` mistag — `context_scout`/`plan-brainstorm` skill-authoring
plumbing, 1 of 11 items still open).

**Close-out criterion**: all three docs' residual items closed or explicitly re-deferred with a named owner.

## Todos

- [x] ✅ [DECISION] P1. **Operator-ruled 2026-07-29 (interactive decision session), retagged from `[OPERATOR]` now
      resolved: fix false-positive detection first, then escalation speed — land
      `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`'s two-consecutive-stale-verify-windows
      fix first, then `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`'s faster hard-kill
      escalation on top of it, in that sequence — this matches both docs' own already-recorded 2026-07-26 gating
      (`autonomous_session_operator_decisions_2026_07_25.md` entry #21, option A), now formalized as the resolution of
      this tranche's direction contradiction. See the two sequenced implementation todos below.** Resolve the
      worker-liveness/watchdog kick+escalation direction contradiction — six docs claim this mechanism and two of them
      prescribe OPPOSITE directions; the 2026-07-26 `/ag-closeout-audit ao` run escalated this as the largest single
      blocker and separately found 32 of this tranche's 35 Sources orphaned (no covering plan) with only a
      `status: draft` satellite batch1 (+ finalize) drafted against 10 of them.
- [x] ✅ [BACKEND] P1. **Land FIRST (sequenced ahead of the hard-kill-escalation todo directly below — do not start that
      one until this todo is done; per the 2026-07-29 operator sequencing ruling above).** Make the liveness kick
      host-load-aware / require two-window confirmation, per
      `/plans/archive/issues/host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`'s own spec:
      before firing `worker_kicked`, require the ping/pane to be stale across TWO consecutive verify windows (not one),
      OR widen `verify_window_s` adaptively when host load average / swap pressure is high, OR gate the kick on a
      progress marker (don't kick a pane whose progress advanced within the last N seconds even if the latest read is
      stale). Done when: a regression test simulating pane-read latency > `verify_window_s` while progress markers keep
      advancing produces ZERO `worker_kicked` events. Repo: agent-orchestrator. — agent-orchestrator@64b5310: added
      `_progress_marker_shields_kick` (new `kick_progress_grace_seconds` tuning knob, default 90s) to
      `WorkerLivenessKicker._tick_once` — a worker whose `last_ping` advanced within the grace window is never kicked
      even when the pane read classifies frozen/idle, since the pane-classification path in
      `server/worker_liveness/__init__.py` (not `worker_liveness_watchdog.py`) is what actually emits `worker_kicked`.
      Regression test `test_pane_read_latency_with_advancing_progress_markers_produces_zero_kicks` simulates 4 ticks of
      a persistently-FROZEN pane read while `last_ping` keeps advancing — asserts zero `worker_kicked`/
      `worker_kick_failed` events and that `_kick_session` is never even called. Full local QG green (1993 passed,
      ruff/basedpyright clean).
- [x] ✅ [INFRA] P2. **Land ONLY AFTER the host-load-aware two-window todo directly above is done — per the 2026-07-29
      operator sequencing ruling above; do not start this todo first.** Escalate the watchdog from soft-kick to
      hard-kill + respawn after N consecutive `post_kick_classification=frozen` observations (e.g. N=3, ~15-20 min)
      instead of soft-kicking indefinitely, per
      `/plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`'s own spec; the
      daily hard-kill budget (50) is ample. Re-scope N/timing against the CORRECTED classifier from the todo above, not
      before landing it. SSOT: `/codex/04-architecture/autonomous-recovery-matrix.md`. Repo: agent-orchestrator. —
      agent-orchestrator@77fc60a: **audit finding — the escalation mechanism this todo asks for was already shipped**
      (`kick_escalation_threshold` config field, default 3, introduced in `5b07bd3`; the ping-advanced-reset bug that
      let the 2026-07-21 incident's wedged worker dodge escalation for 55 kicks was already fixed in `2a48eda`,
      pre-dating this plan). `WorkerLivenessKicker._tick_once` already forces
      `_maybe_auto_respawn_stuck_slot(...,     force=True)` — which kills the wedged tmux session and resumes the
      in-flight task via `--resume` (`_kill_wedged_for_resume`) — once `_consecutive_kick_failures` reaches
      `kick_escalation_threshold`, gated on `genuinely_recovered` (pane verified 'working'), not merely `ping_advanced`.
      Re-scope check (the actual remaining ask, now that the host-load-aware grace-shield fix — the todo directly above,
      `64b5310` — has landed): with `kick_progress_grace_seconds=90s` shielding a slot whose ping is recently advancing
      from ever being kicked at all, a genuinely-wedged slot (no ping progress, beyond grace) reaches the N=3 threshold
      at the SAME real-world cadence observed in the original incident (~5-6 min/kick × 3 ≈ 15-18 min) — matching the
      todo's own "e.g. N=3, ~15-20 min" estimate exactly. No numeric change to `kick_escalation_threshold` or the
      grace/debounce timings is warranted. Added regression test
      `test_genuinely_wedged_slot_still_escalates_after_grace_fix` (composes the grace-shield fix with the escalation
      mechanism in one kicker instance: a stale-beyond-grace slot still reaches `force=True` at exactly
      `kick_escalation_threshold` consecutive kicks) to close the one real gap found — no prior test exercised both
      fixes together. Full local QG green (2002 passed, ruff/basedpyright clean).

## Codex SSOTs (read before touching a track)

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`, `…/agent-orchestrator-overview.md`,
`/codex/04-architecture/agent-orchestrator-alerting.md`, `/codex/05-infrastructure/per-tab-worktrees.md`.

## Progress Log

- **2026-07-25** — Doc authored from a corpus-wide classification pass splitting 234 `asset_group: cross-cutting` docs
  into the 5-AG + cross-cutting + ao + ci + infra topic partition, per operator request. Docs were classified into this
  AO tranche from `orchestrator_master`/`agent_operating_framework_master` directly, from `infrastructure_master`'s
  "pure-infra" bucket, and from a couple of other epics — see the Tracks' **Sources** lists for the membership itself.
  No fixes applied in this pass — pure consolidation for `/ag-closeout-audit`/`/plan-reconcile` sharding.
- **2026-07-26** (`/plan-reconcile ao`, autonomous) — **Corrected a countable contradiction between this doc's own
  narrative and its own Sources lists.** The 2026-07-25 entry claimed 36 docs in this AO tranche, made up of 26 from
  `orchestrator_master`/`agent_operating_framework_master` plus 8 reclassified out of `infrastructure_master` plus 2
  from other epics. Measured directly from the Tracks' Sources lists: **35** docs — **23** `orchestrator_master` and
  **3** `agent_operating_framework_master` (26 ✓), **7** (not 8) `infrastructure_master`, and **1**
  `observability_master` plus **1** `escalation_and_disaster_recovery_master` (2 ✓). So the `infrastructure_master` leg,
  and therefore the total, was over-stated by one. Per this skill's "prefer deleting a derivable restated fact over
  correcting it" rule the hardcoded counts were **removed** from the `summary`/`source` frontmatter and this log rather
  than re-pinned (a hardcoded count re-stales the next time a Source is added), and the Sources lists were named as the
  membership SSOT. **Not resolved by this pass**: whether an 8th `infrastructure_master` doc was _intended_ for this
  tranche and dropped during authoring — that is a classification/ownership call for `/ag-closeout-audit ao`, not a
  count correction, and removing the number does not assert the membership is complete.
- **2026-07-26** (`/ag-closeout-audit ao`, autonomous) — **First full closeout-completeness audit of this tranche.** All
  35 Sources read end to end (single-threaded — the run environment exposed no Workflow/Agent tool, so the skill's
  per-doc fan-out could not be used; recorded as this run's main coverage caveat). Result: **2 archivable now** (the
  `ao_repo_docs_deleted…` and `orchestrator_slots_context_directive…` docs, both 100% `[x]` with gates re-measured), **1
  covered** (`issues/ao_recovery_audit_layer1_deleted_2026_07_15.md`, by
  `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md`'s Layer-1-producer todo), and **32 orphaned** —
  the direct consequence of this doc carrying zero todos while no `ao_*batch*` plan had ever existed. Phase 3 drafted
  `ao_satellite_ao_dispatch_batch1_2026_07_26` + its finalize pair (both **`status: draft`** — flipping to `active` is
  the operator's call) covering 13 source-doc todos across 10 conflict-cleared docs, one of which folds a genuine
  duplicate pair (`git_status_reporter_stale_public_url_token_expiry` and
  `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage` prescribe the identical loopback fix to the same
  script). Four premises were re-measured rather than trusted: the DB-pool `BEGIN IMMEDIATE`-on-reads root cause is
  **still unfixed** at HEAD, all 7 `tab/rootm/*` branches are **GONE** from all six repos (so
  `orphan_rootm_branch_unmerged_work_2026_06_05.md`'s "left in place" premise is false), `agent-orchestrator@867b1731e`
  is on LDR but **not** on `main`, and the PM empty-string-fallback ratchet is **back at baseline** (so
  `plan_health_tests_leak…`'s "blocks every PM code quickmerge" claim no longer holds). **The largest single blocker is
  not a missing batch** — six docs claim the worker-liveness/watchdog kick+escalation mechanism and two of them
  prescribe OPPOSITE directions on it; that ordering is an operator decision, escalated by this run.
- **2026-07-29** (interactive decision session) — **Operator resolved the worker-liveness/watchdog kick+escalation
  direction contradiction escalated above.** Ruling: fix false-positive detection first, then escalation speed — land
  `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`'s two-consecutive-stale-verify-windows fix
  first, then `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`'s faster hard-kill escalation on
  top of it. This formalizes the sequencing both issue docs had already independently recorded on 2026-07-26
  (`autonomous_session_operator_decisions_2026_07_25.md` entry #21, option A) as the tranche-level resolution. The
  blocking todo was flipped `[x]` and retagged `[DECISION]` (was `[OPERATOR]`, now resolved), and two concrete
  `[BACKEND]`/`[INFRA]` implementation todos were added in explicit sequence (first the two-window fix, then — gated on
  it landing — the faster hard-kill escalation), each citing its source issue doc's own spec verbatim rather than
  re-deriving it.
- **2026-07-30** (`/ag-closeout-audit ao`, autonomous, Phases 0-2 only) — **Second full closeout-completeness audit.**
  All 44 AG-primary docs read end to end (single-threaded; the run environment again exposed no Workflow/Agent tool, so
  the skill's per-doc fan-out could not be used — same coverage caveat as the 2026-07-26 run). **Result: 37 of 44
  orphaned** (30 `orphaned_never_touched`, 7 `orphaned_partial_coverage`), 7 covered — barely moved from the 2026-07-26
  run's 32/35 despite batch1 landing 5 todos: batch1's shipped work closed only PARTS of 4 source docs, and 15 more docs
  have landed in this tranche since. **The dominant structural cause is unchanged and worth stating plainly: this doc is
  a Sources digest and says so** ("being listed as a Source below is discoverability, NOT dispatch"), so a Track-1..5
  Sources entry is not coverage; and `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s two `## Deferred` sections hold
  15 docs that are explicitly NOT dispatched. Mechanically: of the 44 members only **12** are cited anywhere inside a
  real `- [ ]`/`- [x]` covering todo; the other 32 appear solely in digest/Deferred/Progress-Log prose. **Highest-value
  now-actionable orphan**:
  `/plans/archive/issues/orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md`'s
  `[DEVOPS] P1` (pin `ORCHESTRATOR_JWT_SECRET_GCS`) — its only blocker was an operator-chosen maintenance window, which
  the 2026-07-28 CLAUDE.md ruling removed; it is a fleet-wide ~4.5h-outage root cause sitting unclaimed by any covering
  plan. **Phase 3 deliberately NOT run** (no batch2 drafted): the skill forbids shipping a drafted pair without operator
  approval and no operator was reachable this run. **Corpus-hygiene fixes applied this run** (Phase 0.3 Orthogonality
  HARD CHECK): the dual-tag `<one specific AG> + cross-cutting` mistag class is **CLEAN — 0 hits corpus-wide** (the 4
  `cross-cutting` multi-tag docs are all the legitimate spans-all-5-AGs pattern). Four genuine content mistags were
  retagged to `[ao]` instead, each verified by reading the doc, not by tag shape:
  `ao_open_issues_consolidated_close_out_2026_07_17.md` (was `[meta]` — this tranche's single most-important covering
  plan, 9 open todos, named as covering in this very doc, yet invisible to `ao`'s own membership rule),
  `issues/branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md`,
  `issues/per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27.md`, and
  `issues/wip_preserve_refs_silently_unrecovered_2026_07_29.md` (all three were bare `[cross-cutting]` with
  `parent_epic: orchestrator_master` and per-slot/worktree content — the post-2026-07-27 muscle-memory mistag class the
  skill predicts). Membership 40 → 44; `check_ag_closeout_linkage.py` re-run after the retag: still 0 orphans, and
  `check_frontmatter_schema.py` clean on all 4. **But that green is vacuous for this tranche and the audit says so** —
  the check's `REAL_AGS` tuple still covers only the 5 original AGs, so no `ao` doc is ever evaluated by it; measured
  blast radius + the separate `ci`-closeout-archived defect are annotated onto the existing owner,
  `/plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md`'s open `[DOC] P3`, rather than forked
  into a competing issue doc. **Not fixed, reported**: ~13 further `[meta]`-tagged docs with `orchestrator_master` /
  `agent_operating_framework_master` parentage read as AO content but were left untouched — that corpus-wide `meta`
  triage is already owned by the doc just cited, and retagging them mid-flight would collide with the 8 sibling tranche
  audits running concurrently against this same corpus.
- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
  Companion gated finalize plan authored: `ao_consolidated_closeout_2026_07_25_finalize_2026_07_30.md`.
- **2026-07-30 (finalize sweep)** — `ao_consolidated_closeout_2026_07_25_finalize_2026_07_30.md`'s todo re-verified both
  `## Todos` commits directly (not trusting this doc's own evidence copy): `agent-orchestrator@64b5310` and `@77fc60a`
  both confirmed ancestors of `live-defi-rollout` HEAD, and their named regression tests
  (`test_pane_read_latency_with_advancing_progress_markers_produces_zero_kicks`,
  `test_genuinely_wedged_slot_still_escalates_after_grace_fix`) re-run live — **2 passed**. Zero `- [ ]` remain in this
  doc's `## Todos` section and `locked_by:` is empty, so this doc is archival-eligible; archived per the 6-step ritual.
  Migrated the composed grace-shield + escalation contract into
  `/codex/04-architecture/agent-orchestrator-worker-liveness.md`'s new § "WorkerLivenessKicker — host-load-aware grace
  shield + hard-kill escalation" (it previously described only the Watchdog kill layer, not the Kicker nudge layer where
  this fix landed). Archiving this digest does not close the tranche: 37/44 Sources are still orphaned per the
  2026-07-30 `/ag-closeout-audit ao` finding above — see `ao_satellite_ao_dispatch_batch1_2026_07_26.md` and
  `ao_open_issues_consolidated_close_out_2026_07_17.md` for the live picture.
