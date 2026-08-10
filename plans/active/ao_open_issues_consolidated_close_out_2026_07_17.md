---
doc_type: plan
title:
  AO open-issues consolidated close-out — one local plan for every still-open agent-orchestrator issue doc, each item
  re-verified against code + the live planning-VM before inclusion
summary: |
  2026-07-17 operator-session sweep of the 10 open AO issue docs — every doc's claims re-verified against the current
  LDR code AND the production orchestrator on the planning VM (read-only SSM — live state.db, activity_log, process
  table, clone freshness) before a todo was admitted here. Measured live state at authoring — clones fresh (AO + PM
  behind=0, clean); churn much improved post-R1 (24h — 184 autospawns / 154 dispatched / 27 done vs the pre-fix
  1014/217/101) but 96 tmux_session_lost + 158 worker_polling_dead per day keeps the worker-lifecycle class hot; ~10
  orphaned claude processes alive right now (16 claude procs vs 4 live tmux sessions, incl. the 3 PIDs the
  orphaned-workers doc named and one fully-detached PPID-1 tree); audit_false_done reports **2 LIVE false-done rows**
  (sports_cf8…-001/-002 — real UTL fixes shipped 07-13/14, plan checkboxes never flipped; both predate the @86b8b8b
  gate so they are legacy poison, not a gate bypass); l2_book…-005/-007 STILL absent from the tasks table while their
  plan todos are open; the mvp-defi park is HOLDING (yaml priority 999); brief_hash NULL tail now 54 (moves). This plan
  is the single execution vehicle: each todo cites its source doc, and each source doc's archival is gated on its todos
  here. LOCAL track — operator-driven, never dispatched.
status: active
nature: process
asset_group: [ao] # corrected 2026-07-30 (/ag-closeout-audit ao) -- was [meta]; a real AO covering plan, not generic
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, deployment-ui]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    dispatch,
    backlog,
    regen,
    worker-lifecycle,
    orphan-process,
    auto-park,
    observability,
    consolidation,
  ]
related:
  [
    ../archive/issues/ao_skip_blind_spawn_budget_phantom_churn_2026_07_15.md,
    issues/orchestrator_concurrent_qg_saturation_and_dispatch_divergence_2026_07_17.md,
    issues/orphaned_workers_on_tmux_loss_stale_dispatch_2026_07_17.md,
    issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    issues/mvp_backfill_defi_v10_002_dispatch_thrash_2026_07_16.md,
    issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    ../archive/issues/ao_service_clone_frozen_by_untracked_checkpoint_2026_07_16.md,
    issues/ao_residuals_after_dispatch_hardening_2026_07_17.md,
    issues/ao_recovery_audit_layer1_deleted_2026_07_15.md,
    /plans/archive/2026_08/ao_docs_reconciliation_2026_07_15.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    ../epics/orchestrator_master.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_2026_07_30.md,
    /plans/archive/2026_07/ao_satellite_ao_dispatch_batch2_finalize_2026_07_30.md,
    /plans/active/ao_satellite_ao_dispatch_batch3_2026_07_31.md,
    /plans/active/ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md,
    /plans/archive/2026_07/ao_slot_capacity_policy_ci_scheduled_split_2026_07_29.md,
    /plans/active/orchestrator_vm_e2e_hardening_2026_07_24.md,
    /plans/active/deepseek_claude_blended_provider_routing_2026_07_28.md,
    /plans/archive/2026_08/omniroute_llm_gateway_pilot_design_2026_07_30.md,
    /plans/active/issues/ao_tranche_full_content_audit_findings_2026_07_31.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_progress_log_history_2026_08_03.md,
  ]
created: 2026-07-17
last_updated: 2026-08-10 # batch10 source-checkbox evidence reconciliation (3 flips). File near hard cap — next touch should split Progress Log history to the archive doc per the 08-03 precedent
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on:
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    /plans/archive/2026_08/ao_docs_reconciliation_2026_07_15.md,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/stale_dispatch.py,
    agent-orchestrator/server/routes/agents.py,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - "operator 2026-07-17 — 'for all the remaining issues check which are live vs resolved … for all the relevant open
    issue docs create ONE plan, local execution'"
  - "Live verification sweep this session: code at agent-orchestrator@6a30e45 / pm@bf2fbcfc5; production probe via
    read-only SSM on i-0c9b283b31d6b5ca7 (state.db mode=ro, activity_log 24h, ps/tmux, audit_false_done.py)"
---

# AO open-issues consolidated close-out

> **Human plan — operator session executes it** (`assigned_vm: NA`, never ingested). ONE plan for the whole remaining
> AO-issue pile so nothing needs rediscovering. Every todo below was admitted only after re-verifying its source doc's
> claim against current code AND the live VM — the classification table is the evidence record. Code ships via
> `quickmerge.sh --agent --files`; each shippable unit flips its todo here AND updates its source issue doc in the same
> turn; a source doc archives (6-step ritual) when its last todo here lands.

## Split-out child plans (2026-07-20) — work MOVED out of this plan

**29 of this plan's 34 todos have been split into eight focused plans** so separate agents can work them in parallel.
All are **LOCAL** (`assigned_vm: NA`, `execution_scope: local-only`) — operator-assigned agents on this host, never
AO-dispatched. Moved items are marked `➡️ MOVED` inline below and **must not be actioned here**; this plan keeps their
audit record only.

| #   | Plan                                           | Scope                                                                | Status (2026-07-20)                                                                                 |
| --- | ---------------------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| 1   | `ao_dispatch_liveness_p0_2026_07_20.md`        | P0 — prereq reaper kills freshly-spawned agents; slot race           | ✅ **ARCHIVED** — residual → Phase 8                                                                |
| 2   | `ao_scheduled_agent_hygiene_2026_07_20.md`     | P1 — make the daily reconciler observably work; boot gate            | ✅ ARCHIVED — residual → Phase 8                                                                    |
| 3   | `ao_failover_multi_vm_readiness_2026_07_20.md` | P2 — keep failover for multi-VM's return; fix + prove untested paths | ✅ **ARCHIVED** — 8/8, no residual                                                                  |
| 4   | `ao_backlog_regen_integrity_2026_07_20.md`     | P1 — regen/bootstrap data-integrity defects + the two rulings        | ✅ **ARCHIVED** — 7/7                                                                               |
| 5   | `ao_worker_lifecycle_reap_2026_07_20.md`       | P1 — orphan-process reap + stale-dispatch reclaim                    | ✅ **ARCHIVED** — residual → Phase 8                                                                |
| 6   | `ao_dispatch_cooldown_and_park_2026_07_20.md`  | P1 — the ONE fleet cooldown store + durable auto-park                | ✅ **ARCHIVED** — 5/5, no residual                                                                  |
| 7   | `ao_fleet_infra_hardening_2026_07_20.md`       | P1 — one state home, env-var sweep, frozen-clone visibility, QG cap  | ✅ **ARCHIVED** — 5/5, no residual (corrected 2026-08-06 (/plan-reconcile ao); was stale "🟡 OPEN") |
| 8   | `ao_fleet_observability_kpis_2026_07_20.md`    | P1 — efficiency KPIs, escalator efficacy, plan_health throttle       | ✅ **ARCHIVED 2026-07-31** — 9/9, no residual                                                       |

**`ao_fleet_observability_kpis` — ✅ ARCHIVED 2026-07-31, 9/9, no residual** (superseded the "live thread"/AF-1b note
that lived here — the escalation-redispatch cap it described landed as part of that plan's own closeout).

Also archived from this plan's lineage: `ao_config_env_var_consolidation_2026_07_18.md` (12/12 verified; its two
operator-gated `.env.local` residuals → Phase 8).

**Start immediately, fully parallel**: #1, #3, #4, #7 — no file overlap, no dependencies.

**The keystone is #4's preserve-by-`brief` todo** — an id-keyed park is silently dropped on the next id-shift regen, so
#6's durable auto-park is not durable until it lands. And **#6 builds the ONE fleet-scoped cooldown store** that #8's
escalator backoff must reuse; the master's own risk note is that three consumers each build their own engine and
diverge. #2's end-to-end reconcile proof needs #1 **deployed** (not merely merged — the reaper is what killed the 07-20
run). #5 waits on #1 because both touch the lifecycle loops.

**What deliberately REMAINS here**: originally 5 gated/last todos — the `tmux_session_lost` root-cause hunt (gated on
#1's re-measure), the 07-12 degradation onset, the two `[REVIEW]` doc close-out/archival passes (they fire as each
source doc's last todo lands), and the operator-sequenced Layer-1 producer rewire — **plus the 4 Phase-8 residuals
inherited from the archived children** (2 calendar-time re-measurements + 2 operator-gated `.env.local` actions), for a
genuine remainder of **9**. Separately, the 14 MOVED items once pending on those 3 children are now ALSO flipped `- [x]`
with `DONE via <child>` pointers (all archived); **all 29 MOVED items here are closed** (fixed 2026-08-08).

## Satellite AO-dispatch layer (2026-07-26 → 2026-07-31) — this plan's related: never linked to it until now

`batch1`/`batch2`/`batch3` + finalizes (now `assigned_vm: NA`/`local-only`),
`deepseek_claude_blended_provider_routing_2026_07_28.md`, `omniroute_llm_gateway_pilot_design_2026_07_30.md` — all newly
linked 2026-07-31. NOT linked: `infra_satellite_ao_dispatch_batch3_2026_07_30.md` (infra-tranche-owned).

**`/ag-closeout-audit ao` sweep (2026-07-30)** classified every AO-tagged doc against this plan's covering family
(reasoning in the audit's own workflow journal) — 30 of 41 genuinely open, no dispatch:

| Bucket                                                                                                                                                                                       | #   | Docs (`plans/active/issues/<name>.md` unless noted)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ✅ Resolved — archived 2026-07-30                                                                                                                                                            | 3   | `context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27`, `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24`, `unified_trading_system_ui_e2e_specs_hardcode_ports_bypass_per_slot_derivation_2026_07_28` (**archived 2026-08-01** — all 3 batched todos shipped, last one `unified-trading-system-ui@741d0a6b`; all now `plans/archive/issues/`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Fix queued in draft `batch2` (unblocks on flip)                                                                                                                                              | 5   | `ao_done_require_origin_not_enforced_2026_07_29`, `dispatch_sequential_gate_fix_2026_07_24`, `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27`, `git_status_reporter_stale_public_url_token_expiry_2026_07_24`, `ao_recovery_audit_layer1_deleted_2026_07_15` (was 7 — `orphan_rootm_branch_unmerged_work_2026_06_05` resolved + archived 2026-07-30, moot: all 7 dead-branch commit-sets superseded-in-spirit)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Self-owned active plan, just not linked here                                                                                                                                                 | 3   | `ao_fleet_observability_kpis_2026_07_20` (✅ ARCHIVED 2026-07-31, no fix needed), `ao_slot_capacity_policy_ci_scheduled_split_2026_07_29` (✅ fixed — now in `related:` 2026-07-31), `orchestrator_vm_e2e_hardening_2026_07_24` (✅ fixed — now in `related:` 2026-07-31)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Conflict-gated (re-triageable next batch)                                                                                                                                                    | 8   | `ahead_push_sentinel_stale_after_amend_no_rejected_push_retry_2026_07_24`, `one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25`, `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26`, `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25`, `killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21`, `utl_shared_clone_commits_repeatedly_reset_2026_07_22`, `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24`, `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Operator-gated (needs a ruling, not another audit)                                                                                                                                           | 8   | ~~`escalation_backlog_repo_collision_blind_spot_2026_07_25`~~ **RESOLVED 2026-08-01** (option b shipped `agent-orchestrator@7c937f99e0`, archived), `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25`, `autostash_pop_restores_foreign_wip_into_the_index_2026_07_17` **DECIDED 2026-08-01** (option 5 pre-commit / option 2 post-commit / option 4 docs, work not yet shipped — see doc's own Progress Log), `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24`, `long_lived_vm_logs_not_backed_up_2026_07_02`, `mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27`, `prediction_trades_migration_concurrent_dispatch_2026_07_28`, ~~`idle_slot_dirty_wip_never_auto_resolves_2026_07_20`~~ **MOOT 2026-08-01** (both todos already shipped 2026-07-24 by `ao_remediation_b_code_chain_2026_07_23`, predating the "gate cleared" note below — archived), `unified_trading_pm_stash_pile_accumulation_2026_07_26`, `per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27`, `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15`, ~~`wip_preserve_refs_silently_unrecovered_2026_07_29`~~ **ARCHIVED 2026-08-07** (all 5 todos shipped; daily sweep `agent-orchestrator@d36219c` + post-push gate `unified-trading-pm@98b99afa2`)                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| Cross-tranche-claimed                                                                                                                                                                        | 1   | ~~`blank_assigned_vm_dispatch_classification_gap_2026_07_26`~~ **ARCHIVED** (confirmed real owner: `ao_satellite_ao_dispatch_batch2_2026_07_30.md:302` — same ao tranche, not actually cross-tranche; now `plans/archive/issues/blank_assigned_vm_dispatch_classification_gap_2026_07_26.md` — verified by plan_reconciler agt-c7578b 2026-08-10)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Discussed in batch1, no closing todo                                                                                                                                                         | 1   | `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| Unclear, needs a closer read before bucketing                                                                                                                                                | 6   | `ao_context_pct_0_for_monitor_heavy_workers_2026_07_29`, `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28`, `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25`, ~~`na_eligibility_auditor_timer_not_yet_installed_2026_07_27`~~ **ARCHIVED 2026-08-06** (`/ag-closeout-audit ao` — all 4 todos were already `[x]`, `plans/archive/issues/`), `mtds_backfill_sequential_true_dispatch_order_violated_2026_07_29`, `plan_health_tests_leak_real_slack_alerts_2026_07_24`, `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Found 2026-07-31 audit, self-owned, never referenced                                                                                                                                         | 7   | `ag_closeout_audit_ao_parked_2026_07_31`, `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30`, `ao_done_gate_checkbox_flip_blind_to_paragraph_restructure_2026_07_31`, `ao_orphan_audit_followup_triage_2026_07_30`, `orchestrator_api_full_outage_stale_cgroup_memory_cap_2026_07_30`, `orchestrator_deploy_currency_gap_stale_reload_unit_and_tmp_exhaustion_2026_07_31`, `orphaned_commit_recovery_has_no_dispatch_path_2026_07_30`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| Found 2026-07-31 audit, genuine AO content but `asset_group` MISTAGGED (`meta`/`cross-cutting`/`infrastructure` — invisible to `/ag-closeout-audit ao`'s own membership rule until retagged) | 23  | `agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22`, `ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26`, `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26`, `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29`, `ao_park_disposition_blocked_answer_no_follow_through_2026_07_31`, `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30`, `backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30` (⚠️ likely duplicate of `ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26` — same `backlog-detail.spec.ts` queue-lag/sort symptom, filed 4 days apart, neither cross-references the other), `backlog_park_lost_across_sibling_todo_insertion_2026_07_30`, `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28`, `checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31`, `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29`, `context_scope_consumption_enforcement_2026_07_30`, `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29`, `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29`, `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25`, `git_health_not_clean_since_pinned_constant_2026_07_27`, `mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30`, `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27`, `orchestrator_vm_disk_io_contention_runner_burst_2026_07_28`, `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29`, `wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21`, `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27`, `workflow_template_drift_repeated_during_phase7_rollout_2026_07_27` |

## 2026-08-06 re-verification sweep of the 51 still-open docs — every doc individually checked against current code

All 51 docs the tables above track as still-open were re-verified this session (6 parallel read-only agents, each doc
read in full + cross-checked against current `agent-orchestrator` code / `git log` since filing, not just checkbox-
counted). Verdicts: **12 candidate-RESOLVED → 7 confirmed and archived**, **18 PARTIAL** (root cause fixed, one residual
sub-item), **21 STILL-OPEN** (defect confirmed still present, or genuinely operator-gated).

**Archived 2026-08-06** (6-step ritual applied, now `plans/archive/issues/`, corpus-wide referrer paths fixed):
`orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25` (dup routed elsewhere, closed),
`plan_health_tests_leak_real_slack_alerts_2026_07_24` (stale `status: open` corrected),
`host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26` (DEVOPS P1 shipped via `qg-host-governor.sh`,
checkbox never flipped), `per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27`,
`ao_dashboard_backlog_detail_queue_lag_e2e_flaky_2026_07_26` (fixed live today, `agent-orchestrator@e761cb1`, verified
2/2 × 3 runs), `backlog_detail_spec_queue_lag_sort_order_flake_2026_07_30` (confirmed duplicate of the prior doc, closed
via the same fix), `orchestrator_vm_swap_exhaustion_masked_as_cpu_2026_07_29` (sole residual self-admittedly
non-actionable, descoped).

**NOT archived despite looking done — caught by full-doc re-read, not just checkbox count**:
`gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25` — `## Todos` was fully `[x]`, but the doc's own Progress
Log documents a confirmed, still-unresolved third root-cause ("zero-derived-parent-row": the parent plan's task rows go
entirely missing from the backlog, reproduced twice, most recently 2026-08-02) that had only ever been narrated in prose
across multiple bounce notes — never given a real `- [ ]` todo. Added one (`[BACKEND] P1`) directly to the doc. This is
exactly the failure mode `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` §2 warns about ("every
follow-up is a todo, never prose") — worth a corpus-wide grep for the same shape (Progress Log narrating an unresolved
finding with no matching checkbox) if this recurs.

**Partial fix, stays active**: `orchestrator_vm_disk_io_contention_runner_burst_2026_07_28` — closed the `[OPERATOR] P2`
memory-cap item (moot, superseded by `rescale-memory-cap.sh`'s unconditional cron self-heal); the `[SCRIPT] P3` item is
a genuine conditional watch-condition (fleet-wide `PYRIGHT_TIMEOUT` bump, only actionable if a timeout-kill recurs
outside a burst window) — correctly stays open, not archived.

**Not touched, flagged for follow-up**:

- `ao_dispatch_priority_inversion_starvation_has_no_page_path_2026_07_30` — `archive_exempt: true`, its archival is
  explicitly owned by `ao_satellite_ao_dispatch_batch3_finalize_2026_07_31.md`'s own `[REVIEW] P0` todo; archiving it
  here would duplicate already-queued work. Left as-is per the standing ruling.
- `git_status_reporter_stale_public_url_token_expiry_2026_07_24` — genuinely has one real open `[INFRA] P3` (refresh
  `~/.orch_token`, a credential op, correctly operator-only) — not resolved, left open as-is, no new todo needed (it's
  already self-tracking).
- `ao_park_disposition_blocked_answer_no_follow_through_2026_07_31` — all todos `[x]`, `status: resolved`, but carries
  `locked_by: live-defi-rollout` / `locked_since: 2026-05-21` — a date that PREDATES this doc's own
  `created: 2026-07-31`, which cannot be a genuine lock. Looks like a stale copy-paste frontmatter artifact, not a real
  lock. Per the archival discipline's hard rule ("locked plans are a human-only unlock — MUST NEVER unlock
  autonomously"), **not archived here** — flagging for an operator decision: confirm the `locked_by` field is bogus and
  clear it, or explain what it's actually protecting.

**Remaining 39 non-archived docs (18 PARTIAL + 21 STILL-OPEN)**: every one already carries its own `- [ ]` todo(s) in
its own file (this corpus's standing convention — issue docs are self-tracking units, not orphaned prose) —
re-verification did not surface a second corpus-wide "prose-only, no todo" gap beyond the `gate_on_depends` case above.
The bucket table above is otherwise still accurate for these: most of the "Operator-gated" (9) and several of the
"Unclear"/"Mistagged" buckets are genuine operator/design-judgment calls per `task_template.md`'s
dispatch-scope-eligibility rule, not AO-dispatchable work — a batch7 satellite plan duplicating their todos was
considered and deliberately NOT drafted (would violate "a plan references, it does not duplicate" and risks
double-dispatch on work these docs already track). Operator-gated decisions ready for a ruling:
`blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24`,
`external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25`,
`mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27`,
`prediction_trades_migration_concurrent_dispatch_2026_07_28`,
`two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15`,
`checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31`,
`context_scope_consumption_enforcement_2026_07_30`, `dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29` —
each doc states its own options; see the doc for the precise A/B/C framing.

## Verified classification of the 10 open docs (2026-07-17, this session)

| #   | Issue doc                                         | Verdict                                                | Evidence (measured this session)                                                                                                                                                                                                                                                                                                                                                                                |
| --- | ------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `ao_skip_blind_spawn_budget_phantom_churn`        | **PARTIAL** — churn fixed, visibility half open        | R1 `ao@7baeedc`+`bf9a61b` on LDR; 24h spawn:dispatch now 184:154 (was 1014:217). No auto-park anywhere in `server/` — the silent-stuck class is live.                                                                                                                                                                                                                                                           |
| 2   | `orchestrator_concurrent_qg_saturation…`          | **LIVE** — nothing shipped                             | No QG throttle in `dispatch.py`/`autospawn.py` (grepped). Governor on the VM was `MODE=token K=2` (owned by `qg_host_adaptive_resource_governor`, NOT this plan).                                                                                                                                                                                                                                               |
| 3   | `orphaned_workers_on_tmux_loss_stale_dispatch`    | **LIVE** — both defects                                | Defect B measured NOW: 16 claude procs vs 4 live tmux; the 3 named PIDs (294936/1934909/1863748) still alive after ~4h + a detached PPID-1 tree. Defect A: requeue-on-dead exists since `ao@5b07bd3` but the resume-pending branch strands tasks (the 07-17 incident path); no `stale_dispatch_reclaimed` invariant exists. Right-now dispatched=2 both live (clean instant, hot class: 96 session-losses/24h). |
| 4   | `backlog_task_done_status_diverges…`              | **RESOLVED-CODE, 2 poisoned rows found by THIS audit** | `_diff_flips_checkbox` live in `verify.py:527`; all 4 fix commits on LDR + deployed (clone behind=0). `audit_false_done`: **false_done=2** — `sports_cf8_available_at_backfill_regression-001/-002`, done_shas = real UTL fixes (07-13/14, PREDATE the gate) → legacy poison, not a bypass.                                                                                                                     |
| 5   | `mvp_backfill_defi_v10_002_dispatch_thrash`       | **PARTIAL** — park holding                             | yaml `priority: 999` live on `-001`. Open: unpark wiring; the ID-shift park-loss defect (converges with #6); auto-park design (converges with #1).                                                                                                                                                                                                                                                              |
| 6   | `regen_positional_task_ids_not_content_stable`    | **LIVE** — nothing shipped                             | `_make_task_id` positional at `regen_backlog_from_plan.py`; NULL-hash tail measured 54 (was 56, moves); 0 non-done NULL rows (confirmed again).                                                                                                                                                                                                                                                                 |
| 7   | `ao_service_clone_frozen_by_untracked_checkpoint` | **PARTIAL** — root cause fixed, alerting open          | Service + PM clones behind=0 clean (measured). ff-pull streak alert still fires only when EVERY repo is dirty (read the script) — single-frozen-clone still silent. hk-host repos all behind=0 today.                                                                                                                                                                                                           |
| 8   | `ao_residuals_after_dispatch_hardening`           | **LIVE** — 5 open todos                                | l2_book-005/-007 STILL absent (only 4 rows, all done — re-measured). `ORCHESTRATOR_DB_PATH` gap bit AGAIN this session (audit tool needed explicit `--db`). Two items externally blocked (paused plan / awaiting design).                                                                                                                                                                                       |
| 9   | `ao_recovery_audit_layer1_deleted`                | **OPEN by operator ruling**                            | Ruling B (re-home producer), sequenced LAST after AO correctness work. Consuming half live, mock-fed.                                                                                                                                                                                                                                                                                                           |
| 10  | `ao_docs_reconciliation`                          | **LIVE tracker** — needs close-out pass                | Tiers 1–6 partially applied piecemeal across later sessions; which tiers actually landed has never been re-verified in one pass.                                                                                                                                                                                                                                                                                |

Docs checked and deemed AO-relevant: all 10. Other open issue docs in `plans/active/issues/` (sports/cefi/defi/etc.) are
NOT AO and are deliberately out of scope here.

## Todos

### Phase 0 — DB-state corrections (no code, operator-gated live changes)

- [x] [BACKEND] P0. **Reopen the 2 live false-`done` rows found by this session's audit** — ✅ **DONE via
      `ao_backlog_regen_integrity_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.**
      `sports_cf8_available_at_backfill_regression-001` (`done_sha=utl@f5f15e3a`) and `-002` (`utl@0f55cc2b`). Both
      done_shas are REAL UTL fixes whose plan checkboxes (`sports_cf8…_2026_07_13.md:348` and `:856`) never flipped;
      both predate the `@86b8b8b` checkbox-flip gate, so this is legacy poison the 07-16 sweep missed (they were likely
      UNAUDITABLE then; regen backfilled their `brief_hash` since). **OWNERSHIP (operator 2026-07-18): the underlying
      work is NOT AO's — it lives in `sports_cf8_available_at_backfill_regression_2026_07_13.md` (status: open, epic
      `mtds_mdps_master`, role `data_engineering`). The "is the work genuinely done" verdict + the checkbox flip belong
      to that plan's owner, not this AO plan.** The two rows: `-001` (`:348`) is a `[ ]`-open DATA re-emit task while
      the backlog row shows `done`; `-002` (`:856`) is a `[x]`-DONE BACKEND task the audit only flags because the cited
      `done_sha` isn't the commit that flipped the checkbox. AO scope here shrinks to: notify the sports/data owner to
      verify + flip (or reopen), then RE-RUN the audit. **Gate**: `audit_false_done.py --db … --pm …` reports
      `false_done: 0` after the sports owner's ruling is applied; the per-row decision is recorded on
      `backlog_task_done_status_diverges…`. Source: doc #4 + this session's probe. **➡️ MOVED 2026-07-20 to
      `ao_backlog_regen_integrity_2026_07_20.md` — do NOT action here.**
- [x] [BACKEND] P1. **Close doc #4 (`backlog_task_done_status_diverges…`) for real.** Its todos are all `[x]` and it ✅
      **DONE via `ao_backlog_regen_integrity_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** left
      `status: open` awaiting "an independent skeptical audit" — this session's audit found the 2 rows above, so the doc
      closes only after Phase-0 todo 1 lands. Also record the corollary amendment: the "no periodic sweep needed" ruling
      holds for the gated mechanism, but the UNAUDITABLE→auditable transition (regen backfilling `brief_hash` onto a
      legacy row) can SURFACE old poison at any time — so `audit_false_done.py` runs once per close-out/audit session
      (cheap, already scripted), not on a cron. **Gate**: doc flipped `resolved` + `resolved_by` filled + archived per
      ritual. **➡️ MOVED 2026-07-20 to `ao_backlog_regen_integrity_2026_07_20.md` — do NOT action here.**

### Phase 1 — backlog/regen integrity (code)

- [x] [BACKEND] P1. **Sibling-reset guard: never silently recycle a `done` row.** `bootstrap.py` brief_hash-mismatch ✅
      **DONE via `ao_backlog_regen_integrity_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** reset must refuse
      to reset a row that is `done` with a `done_sha`, logging an ERROR naming both briefs (a done row is audit
      history). Unit test where a done row's id is claimed by a different brief → row SURVIVES + error emitted;
      bug-inject to prove the test bites. Source: doc #6 todo 2. **Gate**: test green + bug-injection proof. **➡️ MOVED
      2026-07-20 to `ao_backlog_regen_integrity_2026_07_20.md` — do NOT action here.**
- [x] [BACKEND] P1. **Hand-tuned-field preservation across positional-ID shift.** The regen preserves ✅ **DONE via
      `ao_backlog_regen_integrity_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.**
      `priority`/`priority_override`/`prereqs.prerequisites` keyed by task id — an id shift (sibling completes →
      suffixes renumber) silently drops a park (measured: the mvp-defi park was lost exactly this way on 07-17,
      re-applied under `-001`). Key the preservation by `brief` (the same key the reconcile path already uses), not by
      id. Regression test: park a task, remove a sibling todo, regen → park survives under the new id. Source: doc #5
      fix-todo 3 (the NEW [CODE] P1). **Gate**: test green; the live park survives the next real regen tick after a
      todo-count change. **➡️ MOVED 2026-07-20 to `ao_backlog_regen_integrity_2026_07_20.md` — do NOT action here.**
- [x] [BACKEND] P2. **Bound the NULL-`brief_hash` tail (54 rows, all `done`).** Decide + implement ONE of: backfill from
      ✅ **DONE via `ao_backlog_regen_integrity_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.**
      `git show <done_sha>:<plan_ref>` where recoverable; age the exemption out (no in-flight NULL rows exist —
      re-measured 0 this session); or accept permanently with the WHY in the docstring + a growth alarm (growth =
      backfill regression, the real signal). Do NOT blanket-reset. Source: doc #6 todo 1. **Gate**: the doc's stated
      gate — count 0, or recorded decision + growth check. **➡️ MOVED 2026-07-20 to
      `ao_backlog_regen_integrity_2026_07_20.md` — do NOT action here.**
- [x] [BACKEND] P2. **Explain the l2_book absent rows.** `l2_book…-005/-007`: plan todos open (`BLOCKED-*` markers) on
      ✅ **DONE via `ao_backlog_regen_integrity_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** an ingested
      plan, no task rows (re-measured: only 4 l2_book rows, all done). Trace whether the orphan-GC pruned them
      (correct-ish: `BLOCKED-*` todos are non-dispatchable by design and SHOULD have no row — if so, record that as the
      designed behaviour and make `regen`/docs say it explicitly) or whether regen re-derives them under other ids. **Do
      NOT close by re-reopening** (decayed twice). Source: doc #8 todo 5. **Gate**: doc #8's stated gate — a recorded
      explanation, and either correct rows or a recorded by-design decision. **✅ EXPLAINED 2026-07-20 (B1) — BY DESIGN,
      on two independent mechanisms; recording the decision, NOT reopening.** (1) `_parse_open_todos`
      (`server/regen_backlog_from_plan.py:925`) skips **both** already-done `- [x]` checkboxes **and** `BLOCKED-*` /
      stretch-optional lines (`_NON_DISPATCHABLE_RE`). The l2_book plan today is 6 × `[x]` + 2 × `- [ ] BLOCKED-*`
      (`BLOCKED-OPERATOR-DECISION`, `BLOCKED-DATA-CORRECTNESS`) — so it contributes **ZERO current briefs**, and the two
      BLOCKED todos SHOULD have no row. That is stated in the code in three places (the docstring's "Non-dispatchable
      todos … wait on a human/external event", the inline comment at `:985`, and the `:1005` note covering "a worker
      adds an in-text `BLOCKED-*` marker to an already-queued todo"). (2) `_prune_stale` deletes DB rows filtered to
      `status='queued' AND dispatched_to IS NULL` — **done/dispatched rows are never touched** — so a todo checked off
      OUTSIDE the dispatch loop (human/other route) has its still-queued row garbage-collected and leaves no trace,
      while a task AO actually dispatched-and-completed keeps its row forever. **Also corrects the framing twice over**:
      re-measured 2026-07-20 there are **3** rows, not 4 (`-001`, `-004`, `-008`, all `done`), and the absent set is
      **`-002/-003/-005/-006/-007`** — five ids, not the two the todo names. Both mechanisms above cover the whole set,
      so no new defect. **Answering the second branch explicitly: no, regen does NOT re-derive them under other ids
      today — but it WOULD if unblocked.** Ids come from `next_index` (max-existing + 1) while dedup is by brief TEXT,
      so an un-BLOCKED todo returns with a NEW id rather than its historical one — expected, worth knowing before anyone
      treats a task id as a stable handle on a plan todo. **Residual doc work only** (the "make `regen`/docs say it
      explicitly" half): state in the regen docs that the tasks table is a projection of currently OPEN DISPATCHABLE
      todos plus dispatched history — **not** a durable ledger of plan completion — so a missing row is never by itself
      evidence of a lost task. **➡️ MOVED 2026-07-20 to `ao_backlog_regen_integrity_2026_07_20.md` — do NOT action
      here.**
- [x] [BACKEND] P2. **`audit_false_done` false-positive class — the AO/regen lesson from studying the sports rows.** ✅
      **DONE via `ao_backlog_regen_integrity_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** (Operator
      2026-07-18: the sports work itself is its owner's; but any AO/regen improvement surfaced by studying it belongs
      here.) `sports_cf8…-002`'s plan checkbox IS already `[x]` — the audit flags it ONLY because the row's cited
      `done_sha` isn't the commit that flipped the checkbox. Decide the intended contract: should `audit_false_done` /
      `verify.check_plan_flip` treat a checkbox that is currently `[x]` as HONEST regardless of which commit flipped it
      (checkbox state = truth), or must the `done_sha` itself be the flip-commit (provenance = truth)? A "checkbox `[x]`
      but wrong sha" false-positive pollutes the gate's signal. Trace both consumers, pick the rule, and make the
      audit + the done-gate agree on it. Source: sports_cf8 study, this session. **Gate**: a recorded decision;
      `audit_false_done` no longer flags an already-`[x]` row whose work is genuinely complete (or explicitly does, by
      ruling, with the reason documented). **➡️ MOVED 2026-07-20 to `ao_backlog_regen_integrity_2026_07_20.md` — do NOT
      action here.**

### Phase 2 — worker lifecycle (code)

- [x] [BACKEND] P1. **Orphan-process reap (Defect B) — the biggest live bleed.** ~10 orphaned `claude` workers are alive
      ✅ **DONE via `ao_worker_lifecycle_reap_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** right now on the
      VM (16 procs vs 4 live sessions; 3 are the doc's named PIDs, ~4h old, one tree fully detached at PPID 1), burning
      CPU + account budget and racing re-dispatched work. Implement BOTH halves: (a) the TmuxPruner kills the worker
      process tree whose slot config-dir maps to a dead/absent session (match by `claude_session_id`/config dir, never
      by name-grep alone); (b) a periodic orphan sweep (config-dir → PID → slot liveness) catching residue incl. PPID-1
      trees. Guards: never kill a PID belonging to a live session; **honor `boot_grace_seconds` — NEVER reap a slot's
      process inside its fresh-spawn grace window (a booting worker's tmux session isn't registered yet; this is the
      exact 6/6-AutoSpawn-workers-killed-56-120s-post-spawn incident class — config.py boot_grace_seconds exists
      precisely for this)**; dry-run mode; log every kill with slot + PID + age. Source: doc #3 Defect B. **Gate**: the
      doc's regression — simulated `tmux_session_lost` leaves zero detached claude processes for that slot; live sweep
      on the VM reports 0 orphans (one-time cleanup of the current ~10 included). **➡️ MOVED 2026-07-20 to
      `ao_worker_lifecycle_reap_2026_07_20.md` — do NOT action here.**
- [x] [BACKEND] P1. **Stale-dispatch invariant (Defect A, resume-path aware).** The pruner's requeue (`ao@5b07bd3`) ✅
      **DONE via `ao_worker_lifecycle_reap_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** already releases on
      a "requeue" verdict, but a `resume-pending` verdict keeps the task bound — and when the resume never happens
      (07-17 incident: slots went `killed` holding tasks), nothing reconciles. Add the reconciler invariant: a task
      `dispatched` to a slot with `worker_alive=false` AND `tmux_session IS NULL` for > one pruner tick beyond
      `resume_attempts` exhaustion → auto-release + `stale_dispatch_reclaimed` activity event. Must NOT fight the resume
      path — only fire after resume is exhausted/impossible. Source: doc #3 Defect A + doc #2 symptom 1. **Gate**: doc
      #3's regression test; live `dispatched` count equals live-worker-held count across a 24h window (spot-checked);
      **AND an explicit no-double-dispatch assertion — a task released by this invariant is NEVER simultaneously live on
      a resumed worker. The release fires strictly AFTER `resume_lifecycle` marks resume exhausted/impossible (order the
      two so the same task can never reach two agents); test the exact race (resume in-flight when the invariant tick
      fires → invariant defers, no release).** **➡️ MOVED 2026-07-20 to `ao_worker_lifecycle_reap_2026_07_20.md` — do
      NOT action here.**
- [ ] [INFRA] P0. **Root-cause the 96/day `tmux_session_lost` rate** (or record it as accepted churn). The 07-17
      incident was 5 losses in one second (backend/tmux blip); today's rate is 96/24h with 158 `worker_polling_dead`.
      Either find the driver (backend restarts? host pressure? tmux server?) or record the rate as expected with the
      lifecycle machinery absorbing it. Source: doc #3 timeline + this session's measurement. **Gate**: a named cause
      with evidence, or a recorded accepted-churn decision with the measured baseline. **⛔ SEQUENCED 2026-07-20 — do
      NOT start this before the prereq-reaper P0 lands.** That reaper (`ao_dispatch_liveness_p0_2026_07_20.md`) kills
      freshly-spawned sessions and is a live candidate for a share of this churn; its last todo re-measures the rate
      against the 192-events-since-07-18 baseline. **This todo stays HERE and owns the root-cause hunt** — it resumes
      only if the re-measure shows the rate did not drop. Starting now means measuring the same churn twice and possibly
      chasing a driver that the P0 fix removes.

### Phase 3 — spawn/park visibility (code + policy)

- [x] [BACKEND] P2. **Durable auto-park for fleet-skipped tasks (the visibility half R1 exposed).** R1 made ✅ **DONE
      via `ao_dispatch_cooldown_and_park_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** fleet-skipped tasks
      count 0 toward the spawn budget — which silenced the churn but also the SIGNAL (nothing tells anyone the task is
      stuck). Auto-park at ≥N distinct within-TTL skips carrying a `BLOCKED|PARKED|GATED` reason via the durable
      `priority_override`/false-prereq recipe (`ao@8dd5763`), WITH an unpark path when the condition clears, and an
      operator-visible surface (activity event + dashboard flag — the same class as `needs_operator_count`). This closes
      doc #1's last todo AND doc #5's auto-park design todo in one mechanism. **DEPENDS ON Phase-1 preserve-by-`brief`
      (Phase 1 todo 2): an id-keyed park is silently dropped on the next id-shift regen, so auto-park is NOT durable
      until that lands — sequence Phase 1 first.** **Park = the ≥N-skips escalation of the ONE fleet-scoped cooldown
      store built in Phase-6 (blocked-task cooldown); reuse that store, do not build a second park-specific cooldown.**
      Sources: doc #1 todo 2, doc #5 fix-todo 3(design). **Gate**: a fleet-skipped task auto-parks with a visible
      reason; clearing the condition unparks it; test-pinned. **➡️ MOVED 2026-07-20 to
      `ao_dispatch_cooldown_and_park_2026_07_20.md` — do NOT action here.**
- [x] [ADMIN] P2. **Wire the mvp-defi unpark.** `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` (still ✅
      **DONE via `ao_dispatch_cooldown_and_park_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** `false`) must
      be flipped by whoever lands the seed-chain/backfill progress (`data_completion_defi_2026_07_15`'s owner), or the
      park outlives its reason. Add the pointer on that plan + a line in the park's prereq description naming the
      flipper. ⚠️ **OPEN QUESTION (found 2026-07-20 via plan_health output): the named flipper plan may be STALE.**
      `plan_health` flagged `data_completion_defi_2026_07_15` as CONTRADICTED/superseded by
      `defi_consolidated_closeout_2026_07_18` — which declares the per-instrument re-architecture supersedes the
      batch-model tracks, DeFi capture STOPPED, and backfill GATED on T1–T3 canonicalisation. If that plan never
      progresses, this park **outlives its reason forever** (a permanent silent park). Decision needed: re-point the
      unpark to the `defi_consolidated_closeout` owner, or park it EXPLICITLY (documented) until the DeFi
      re-architecture resumes. Source: doc #5 fix-todo 2 + plan_health contradiction output. **Gate**: the owning plan
      (whichever it now is) carries the flip instruction; condition documented; no park without a named live flipper.
      **➡️ MOVED 2026-07-20 to `ao_dispatch_cooldown_and_park_2026_07_20.md` — do NOT action here.**

### Phase 4 — infra/ops hardening

- [x] [INFRA] P1. **State home = ONE in-repo source (`data/state/`); drop the two-places + the env overrides.** The
      wrong-DB GC incident + THREE bitten diagnostic sessions were the "one concept, two places" footgun:
      `ORCHESTRATOR_DB_PATH`/`ORCHESTRATOR_STATE_JSON` are set in the systemd unit (→ `/var/lib/orchestrator/…`, out of
      repo) while `config.py`'s default is in-repo `data/state/…`, so a CLI tool run as `ubuntu` without the unit env
      resolves the WRONG path. Operator ruling 2026-07-18: **keep AO backend state IN the repo, one definition, no
      duplicate var.** Resolution: make `config.py`'s in-repo `data/state/{state.db,state.json}` the SINGLE SSOT —
      REMOVE the unit `Environment=ORCHESTRATOR_DB_PATH/STATE_JSON` lines + `ReadWritePaths=/var/lib/orchestrator`, and
      stop setting those vars anywhere (the default IS the path → nothing to duplicate; service + CLI agree). ⚠️ **This
      reverses the deliberate `/var/lib` redeploy-wipe protection** — so it becomes a HARD requirement that the deploy
      path preserve state instead: `ao-self-pull.sh` + any redeploy/re-clone MUST NEVER `git clean -x` / wipe
      `data/state/` (it is gitignored → a bare FF-pull is already safe; the guard is against `clean -fdx` + fresh
      clone), and the SnapshotLoop S3/GCS archive stays the DR fallback. Migration (operator-gated, live): move the
      running `/var/lib/orchestrator/*.db` → `data/state/` on the VM, then restart. Source: doc #8 todo 2 + operator
      2026-07-18. **Gate**: `config.db_path()` as `ubuntu` with no env prints the in-repo path; service + a CLI audit
      tool resolve the SAME db; a simulated redeploy (FF-pull + `git clean -fd`) leaves `data/state/` intact. **➡️ MOVED
      2026-07-20 to `ao_fleet_infra_hardening_2026_07_20.md` — do NOT action here.** **✅ DONE 2026-07-23 via
      `ao_fleet_infra_hardening_2026_07_20.md` (archived 2026_07), todos 1+2** — the config change AND the
      operator-gated live migration both landed; the running VM state now resolves in-repo `data/state/`. Verified at
      flip: both child todos `- [x]` with evidence.
- [x] [INFRA] P2. **Duplicate-purpose env-var sweep (verify-consumer-then-remove).** Audit 2026-07-18: (1)
      `ORCHESTRATOR_OPERATOR` is written `= ORCHESTRATOR_VM_ID` by `bootstrap_vm.sh` on every host, but
      `host_operator()` already DERIVES operator from `vm_id` when unset → pure redundancy; stop writing it in bootstrap
      (keep the field as an optional override). (2) `ORCHESTRATOR_DB_PATH`/`STATE_JSON` two-places — folded into the
      state-home item above. (3) CHECKED & **KEEP** — `GOOGLE_CLOUD_PROJECT` vs `GCP_PROJECT_ID` are NOT a removable
      duplicate: the former is a Google-SDK standard the client reads directly, the latter is workspace canon (`auth.py`
      reads `google_cloud_project or gcp_project_id` — different consumers). (4) CHECKED & **KEEP** — the
      `WORKSPACE_ROOT`/`UNIFIED_TRADING_WORKSPACE_ROOT`/`ORCHESTRATOR_WORKSPACE_ROOT` trio is deliberately separate
      (own-config vs ambient passthrough, documented in `config.py`). **Gate**: `OPERATOR` no longer written by
      bootstrap + a host with only `VM_ID` set resolves the same operator; keep-decisions recorded in ENV_VARS.md. **➡️
      MOVED 2026-07-20 to `ao_fleet_infra_hardening_2026_07_20.md` — do NOT action here.** **✅ DONE 2026-07-23 via
      `ao_fleet_infra_hardening_2026_07_20.md` (archived 2026_07), todo 3.** Verified at flip: child todo `- [x]`.
- 🚫 **Per-repo freeze-streak alert (`slot-cron-ff-pull.sh` signal) + deployment-ui fleet-tab surface — DESCOPED
  2026-07-21 (operator).** Handed to the agent already working on the deployment-ui fleet tab; owned there, no longer
  our work. Was doc #7 todo 3 + operator 2026-07-18 (moved 2026-07-20 to `ao_fleet_infra_hardening` → then
  `monitoring_control_plane_master`, both now cleared). Removed as a `- [ ]` todo so it no longer reads as open work
  here; this line is the audit breadcrumb.
- [x] [INFRA] P2. **Fleet-wide frozen-clone sweep.** hk-host root repos measured behind=0 today, but the VM's SLOT
      clones + any other hosts were not swept. One pass: every host's root + slot clones, `HEAD..origin/LDR > 0` with
      untracked-only dirt → unfreeze (plain FF, per the doc's recipe). Source: doc #7 todo 4. **Gate**: sweep output
      recorded; zero frozen clones remain. **➡️ MOVED 2026-07-20 to `ao_fleet_infra_hardening_2026_07_20.md` — do NOT
      action here.** **✅ DONE 2026-07-23 via `ao_fleet_infra_hardening_2026_07_20.md` (archived 2026_07), todo 4.** ⚠️
      Note the gate's wording ("zero frozen clones remain") was CORRECTED in the child: the honest result is a measured
      375-clone sweep of this host (worst clone 7 behind, no 249-behind cases; 42 clean clones FF'd, dirty ones
      protected), not a proof that zero frozen clones exist fleet-wide forever. Read the child's todo for the measured
      numbers before re-asserting the stronger claim.
- [x] [INFRA] P2. **Dispatch-time full-QG throttle (coordinate, don't duplicate).** The shared-host "≤2 full QG" cap is
      unenforced at dispatch — 4-6 concurrent full-QG pytests saturated the VM on 07-17 (doc #2). The RAM/CPU admission
      governor (`qg_host_adaptive_resource_governor_2026_07_14`, active P1) is the natural enforcement point but was
      measured `MODE=token K=2` on this VM. Scope here: (a) record the requirement on the governor plan (dispatch-aware
      QG admission on the orchestrator host), (b) if the governor's Phase-3 ledger is not landing soon, implement the
      minimal dispatcher-side stagger (cap simultaneous ship-phase tasks per host). Do NOT build a second governor.
      Source: doc #2 fix-direction 1. **Gate**: concurrent full-QG on the VM measurably capped (via governor or
      stagger), evidence cited. **➡️ MOVED 2026-07-20 to `ao_fleet_infra_hardening_2026_07_20.md` — do NOT action
      here.** **✅ DONE 2026-07-23 via `ao_fleet_infra_hardening_2026_07_20.md` (archived 2026_07), todo 5.** Verified
      at flip: child todo `- [x]`.

### Phase 5 — doc close-outs + audits

- [x] [INFRA] P3. **07-12 degradation onset: name it or close it.** `worker_polling_dead` 0→587 + spawn:dispatch
      0.6:1→44:1 on 2026-07-12 was never explained (mechanism since fixed). One `activity_log` excavation pass → either
      a named cause or a recorded not-worth-it decision. Source: doc #8 todo 3. **Gate**: doc #8's gate — not silence. —
      ✅ **DONE via `/plans/archive/2026_07/ao_remediation_b_code_chain_2026_07_23.md` item 12 (this commit; slot 3)**,
      collapsed to one owner per that item's own duplicate-NOTE (this exact item). Named cause: the true onset was
      2026-07-12 15:00 UTC, a second, unalerted `ao-self-pull.sh` dirty-gate wedge (root: a `tempfile.gettempdir()`
      CWD-fallback bug in `regen_backlog_from_plan.py`), not the earlier, well-known 08:1x UTC `/tmp`-ENOSPC blip (which
      was real but contained). Root-fixed same day, `agent-orchestrator@fc9ac53`. Full hourly-breakdown methodology +
      activity-log evidence lives in that plan's Progress Log — not duplicated here.
- [ ] [REVIEW] P0. **`ao_docs_reconciliation` close-out pass.** Verify tier-by-tier (1–6) what has since landed (several
      tiers were executed piecemeal: Tier-4 → `ao_residuals`; X2 → recovery doc; some Tier-1 flips landed in later
      commits), apply/route what remains, then flip the tracker `resolved` + archive. Its own X5 lesson applies: every
      edit lands committed+pushed in the same session. Source: doc #10. **Gate**: each tier marked landed/routed/dropped
      with evidence; doc archived.
- [x] ✅ [REVIEW] P0. **Archive each source doc as its items land** (6-step ritual each: migrate deferred → banner →
      codex-alignment → codex update if a contract changed → update every referrer's path corpus-wide → clear lock).
      Docs #2 and #6-frontmatter carry bogus fields (`last_updated: 2026-06-27` predating `created`; stray
      `locked_by: live-defi-rollout`) — repair at archival. **Gate**: `plans/active/issues/` contains no
      resolved-but-unarchived AO doc; inventory regenerated. **✅ DONE 2026-08-10 — 0 archival actions required.**
      Re-derived the candidate set fresh (not the stale "Docs #2 and #6" reference): all 57 `plans/active/issues/*.md`
      docs matching `asset_group: [ao]` OR `parent_epic: orchestrator_master`, checked for 0-open-todos-with-`>0`-done +
      a terminal `status:` field. Result: **0 genuine orphans** — `check_archive_candidates.sh` (0 candidates,
      baseline 0) + `check_terminal_status_archived.py` (0 violations, baseline 0) both clean; the 4 near-miss docs are
      each correctly held back (gate_on_depends finalize, `archive_exempt: true`, or the standing corpus-wide
      `locked_by: live-defi-rollout`). `regenerate_active_plan_inventory.py` re-run clean (0 orphans, 297 plans). NOTE
      (2026-08-10, slot 24 re-verify): the corpus-wide gates have since drifted — `check_archive_candidates.sh` now
      flags 2 candidates and the inventory reports 3 orphans, both from new 2026-08-10 work; tracked as todo 5 in
      `/plans/active/ao_satellite_ao_dispatch_batch10_finalize_2026_08_09.md`.

### Phase 6 — operator-reported dispatch-policy gaps (2026-07-17, verified this session before writing)

> Reported verbally by the operator 2026-07-17; each item below was VERIFIED against code + the live VM before being
> written down. Per the operator's instruction these are RECORDED, not fixed, in this session.

- [x] [BACKEND] P2. **Paused-slot semantics — verified CORRECT in code; pin it with tests + close the one unchecked ✅
      **DONE via `ao_failover_multi_vm_readiness_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** path.**
      Findings (2026-07-17): `dispatch.pick_next_task` excludes paused via `_slot_configured` (`dispatch.py:186` —
      "paused: an explicit operator 'do not use this slot'"); AutoSpawn excludes paused (`autospawn.py:631`
      spawnability + `:2031` review/paused guard); `plan_health._pick_free_slot` and `escalation._pick_free_slot` both
      skip `paused`/`killed`; a paused slot's `/heartbeat` only refreshes ping + drains messages, never dispatches
      (`slots_worker.py:316`); the TmuxPruner never overwrites `paused` and never releases a paused slot's task
      (operator intent preserved). So the operator's expectation — no new task, no new work on a paused slot — HOLDS in
      code today. Remaining: (a) one regression test pinning "a paused slot receives no task from ANY path" (dispatch,
      autospawn, plan_health, escalation, AND the dead-slot failover/spill path — the spill path was NOT verified this
      session); (b) verify the dashboard renders paused distinctly so an operator-paused slot is never mistaken for a
      stuck one. NOTE (2026-07-18): the cited line numbers (`dispatch.py:186`, `autospawn.py:631/:2031`,
      `slots_worker.py:316`, etc.) DRIFTED after the config `.tuning.` call-site refactor — **verify by SYMBOL**
      (`_slot_configured`, `pick_next_task`, `_pick_free_slot`), not line. **Gate**: the all-paths test exists +
      bug-injection proves it bites; spill-path verdict recorded. **✅ SPILL-PATH VERDICT RECORDED 2026-07-20 (B3) — the
      answer splits: the PULL spills are safe, the PUSH spill is NOT.** The two affinity spills
      (`dispatch._task_is_routable_to` R5 high-affinity dead-target spill + the `medium` timeout spill) are **safe by
      construction** — they only ever answer "may the slot that is ASKING claim this task?", and a paused slot never
      asks (`_slot_configured` gates `pick_next_task`). But `failover._pick_least_loaded_slot` **PUSHES**: it sets
      `task.target_slot = best_slot` directly, and it selects over `select(SlotRow)` filtered ONLY by `exclude_slots` (=
      the offline HOST's slots). It does **not** filter `status == "paused"` — nor `killed`, nor review slots. Worse,
      the metric is "fewest queued-and-undispatched tasks pinned to it", and a paused slot has **zero** by definition
      (nothing dispatches to it) — so `min()` picks a paused slot **preferentially**. Net effect: failover would re-pin
      tasks onto the one slot guaranteed never to run them, stranding them invisibly — re-introducing the exact
      stranding class R5 was written to fix (see the `dispatch.py` R5 comment naming the two tasks stuck this way on
      2026-07-14), through a different door. **Severity P2 = LATENT, NOT LIVE, measured 2026-07-20**:
      `ORCHESTRATOR_FAILOVER_ENABLED` is unset (default `False`), `/api/ops/failover/status` reports
      `{"running": false, "status": "stopped"}`, and there are **0 `failover_rerouted` events for all time**. It is
      armed to bite the moment failover is switched on, though — **slot 0 is paused right now** and would be the
      preferred target. Fix is one predicate in `_pick_least_loaded_slot` (exclude `paused`/`killed`/review), plus the
      (a) all-paths regression test gaining a failover case. **➡️ THE FAILOVER HALF MOVED 2026-07-20 to
      `ao_failover_multi_vm_readiness_2026_07_20.md`** (the `_pick_least_loaded_slot` fix + the failover case of the
      all-paths test). **What REMAINS here**: the (a) all-paths regression test for the NON-failover paths (dispatch,
      autospawn, plan_health, escalation) and the (b) dashboard paused-rendering check. Do not write the failover
      predicate here.
- [x] [BACKEND] P3. **Is `server/failover.py` dead code under the single-VM architecture? (raised by B3, 2026-07-20)**
      ✅ **DONE via `ao_failover_multi_vm_readiness_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** Its entire
      premise is cross-HOST re-routing ("a host e.g. harsh-pc goes offline and its soft-pinned tasks never dispatch"),
      but multi-VM dispatch was **deprecated 2026-06-27** in favour of the single central VM + role-based dispatch
      (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`; `assigned_vm` ∈ `{planning,     NA}`).
      Live state agrees: failover is stopped, has never fired, and `fleet_registry_entries: 0` — it has no registry data
      to act on even if enabled. Per CLAUDE.md ("**Delete deprecated code** — no shims"), the honest resolution may be
      to DELETE the module + its config knobs rather than fix the paused-slot bug above. **Decide before doing the P2
      fix** — no point hardening a module that should not exist. **Gate**: an explicit keep-or-delete ruling; if keep, a
      named scenario under single-VM that still needs it. **✅ RULED 2026-07-20 (A5) — KEEP.** The named scenario the
      gate asked for: **multi-VM returns for resilience/backup** (operator, 2026-07-20). So the module stays and the
      paused-slot P2 above is **live work, not superseded**. **➡️ BOTH MOVED to
      `ao_failover_multi_vm_readiness_2026_07_20.md`** — which also covers the larger risk this audit exposed: the
      re-route and rollback paths have NEVER executed in production (0 events for all time), so the resilience feature
      is unproven, not merely off. Do NOT action either here.
- [x] [BACKEND] P1. **plan_health cadence — MEASURED 21 dispatches in 5.5h (11:02→16:30Z), overlapping instances
      confirmed (`superseded-plan_health` exit reasons + one ACTIVE at probe time).** Operator policy: once per 4–8h
      unless CI-triggered — NOT every 15–30 min. Root cause found: `main-backmerge-to-ldr.yml` § "Ping plan-health
      agent" POSTs `/api/plan-health/dispatch` on EVERY LDR→main promotion that lands PM content (fleet promote runs
      `*/15`, PM is busy — today's session alone drove ~10 promotions), and the server endpoint has NO cooldown, NO
      already-running coalesce (only the failure-page cooldown is deduped; the singleton reaper kills stragglers after
      the fact, which is where the `superseded-plan_health` churn comes from). Fix to implement: (a) server-side
      min-interval gate on `/api/plan-health/dispatch` (**default 2h — operator RATIFIED 2026-07-18; "adjust later"**;
      the value is an env-free `TuningDefaults` knob so it's a code-edit-and-redeploy, not an env var), `mode=reconcile`
      exempt, explicit `force=true` for operator/CI-emergency use) + at-most-one-live coalesce (a dispatch while one is
      active returns the active dispatch_id, HTTP 200, no spawn); (b) keep the promotion ping as a TRIGGER but let the
      server gate absorb the frequency (trigger-rich, execution-throttled). NOTE: 2h is the value the gate SHIPS with —
      there is no live knob today (the driver is the per-promotion backmerge ping), so the rate only drops once this
      gate lands. Also noted: every plan_health boot logs `boot_read_unconfirmed` for `agents/worker.md` (the file
      exists — the worker just never confirms it), a per-boot noise line worth one look while in the file. **Gate**:
      measured dispatch rate ≤ 1 per interval over a 24h window with promotions still flowing; zero
      `superseded-plan_health` exits in that window. **➡️ MOVED 2026-07-20 to
      `ao_fleet_observability_kpis_2026_07_20.md` — do NOT action here.** **✅ DONE 2026-07-23 via
      `ao_fleet_observability_kpis_2026_07_20.md`, todo AF-2+Phase-6** (server-side min-interval gate + at-most-one-live
      coalesce). Verified at flip: child todo `- [x]`.
- [x] [BACKEND] P1. **Blocked-task redispatch cooldown + change-triggered re-eligibility + worker ETA (operator policy,
      ✅ **DONE via `ao_dispatch_cooldown_and_park_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** new
      mechanism).** Today a skip-as-blocked only blocks the SKIPPING slot (24h slot-scoped TTL); any other idle
      same-role slot re-claims the task within ~minutes (measured: 117 `slot_task_skipped`/24h; the mvp thrash doc
      recorded 3 re-derivations of the same verdict in ~35 min). Operator policy to implement, verbatim: (1) when a
      worker declines a task as BLOCKED after reading the plan, the task is not re-dispatchable to ANY slot for a base
      cooldown of 10–15 min; (2) within/after that window, re-dispatch EARLY only if something RELEVANT changed — a
      prerequisite flip, a plan-todo/regen change on that task, a park/priority change — i.e. change-triggered
      re-eligibility, else (3) no change → next attempt no sooner than 1h; (4) the worker MAY supply an estimated
      unblock time on skip (e.g. "VM finishes in ~15 min") — extend the `/skip-current-task` payload with
      `estimated_unblock_minutes`, and the cooldown becomes that estimate (+small buffer) instead of the defaults.
      Design note: this is the missing middle layer between the existing slot-scoped skip TTL and Phase-3's auto-park
      (park = the ≥N-skips escalation of the same mechanism; the cooldown handles the 1st–Nth skip window). **Build
      exactly ONE fleet-scoped cooldown store** (keyed by task_id, with change-listeners on prerequisite/regen/park
      events) that is REUSED by Phase-3 auto-park AND AF-1's escalator backoff — do NOT ship three separate
      cooldown/backoff engines (they diverge). **New tunables (base cooldown, 1h fallback, N-skip park threshold,
      escalator cap) go on the env-free `config.tuning` / `TuningDefaults`, NOT a new `ORCHESTRATOR_*` alias** (per the
      2026-07-18 config split); reuse existing knobs where they fit (`slot_skip_ttl_hours`,
      `orphaned_task_reclaim_grace_seconds`, `dispatch_ack_timeout_seconds`). Sources: operator 2026-07-17 + doc #5's
      fleet-wide-cooldown gap. **Gate**: regression tests (skip-blocked → no cross-slot redispatch inside base cooldown;
      prereq flip → immediate re-eligibility; no change → 1h; ETA honoured); measured redispatch-of-declined-task rate
      drops to the policy curve on the live VM. **➡️ MOVED 2026-07-20 to `ao_dispatch_cooldown_and_park_2026_07_20.md` —
      do NOT action here.**
- [x] [INFRA] P1. **plan_reconciler daily 01:00 UTC was NOT RUNNING — part (a) DONE 2026-07-18 window armed; (b)/(c) +
      two NEW defects remain.** **(a) ✅ RE-ENABLED 2026-07-17T18:03Z (operator request, this session)**: ran
      `install-plan-reconciler-timer.sh --operator ubuntu --time 01:00` via SSM; verified `is-enabled=enabled`,
      `NextElapseUSecRealtime=Sat 2026-07-18 01:04:12 UTC`, unit files on disk. The Persistent catch-up fired
      immediately and **actually dispatched `agt-55b581`** (plan_reconciler, live on `orch-slot-2` at 18:04:25Z) — a
      bonus run the operator can inspect today alongside tomorrow's. **Diagnosis CORRECTED by the pre-install
      forensic**: the units were NOT absent — they existed since Jul 14 15:23 and were `enabled`; the timer was
      evidently INACTIVE (stopped), which `is-enabled` does not detect and `list-timers` omits (no next-elapse) — that's
      why it fired 07-15 then silently never again, and why yesterday's probe saw nothing. Journal history was
      unrecoverable (vacuumed), so WHAT stopped it is unknowable now; the liveness check below is the durable answer.
      **Two NEW defects found by the re-enable, to fix in code**: (1) the dispatch script's `curl --max-time 30` is
      shorter than the endpoint's real latency (measured 56s: initiated 18:03:29 → dispatched 18:04:25), so EVERY timer
      run logs `HTTP 000 / FAILURE` even when the dispatch succeeds — a false-failure that would mask real ones; bump to
      ≥120s or make the endpoint return 202 immediately. (2) `systemctl enable` alone doesn't guarantee a scheduled
      timer — the liveness assertion must check **`is-active` + a computed next-elapse**, not `is-enabled`. Remaining:
      **(b)** the daily liveness assertion (digest line or guard-cron: timer `is-active` AND next-elapse exists AND last
      successful dispatch < 26h → alert on breach); **(c)** audit whether the 2026-07-15 run (`agt-2d8441`) AND today's
      `agt-55b581` COMPLETED their work product (operator suspects the 07-15 one did not): pull their
      `plan_health_result`/`reconciler_candidate` events + any PM commits, record the verdict. **✅ (c) ANSWERED
      2026-07-20 by read-only SSM audit of the FULL window — the verdict is worse than "a run was missed": the scheduled
      plan_reconciler has NEVER ONCE COMPLETED A RUN since it was first installed.** Evidence: 5 reconcile-mode
      dispatches exist in `activity_log` for all time (07-15 `agt-2d8441`, 07-17 `agt-55b581`, 07-18 `agt-c02414`, 07-19
      `agt-722a19`, 07-20 `agt-99684d`); **0 of the 5 posted a `plan_health_result`**,
      `git ls-remote origin     'plan_reconciler/*'` returns **0 branches**, and there are **0 PRs** — i.e. zero work
      product against a contract (`agents/plan_reconciler.md` §258/§334) that REQUIRES pushing
      `plan_reconciler/$DISPATCH_ID` and POSTing a result even when it finds nothing. The timer itself is HEALTHY
      (`is-active`, `LastTrigger=2026-07-20 01:02:01`, `NextElapse=2026-07-21 01:04:31`) — arming it was never the
      problem. Per-run causes: **07-19 never spawned** — `plan_health_dispatch_failed` "benign: session already exists
      (raced by another spawn path)" after the escalation dispatcher took the same slot 2 eight seconds earlier
      (`escalation_dispatch_initiated` 01:03:06 → reconcile initiated 01:03:14); **07-20 spawned then was KILLED 19s
      after boot** by the prereq reaper (see the new P0 below); **07-15/17/18 each died 7–7.5 min after dispatch with no
      result** (cause NOT established — sub-question below). Also CONFIRMS defect (1) empirically: dispatch latency
      measured **55/56/55/55s** across 4 runs vs `--max-time 30`, so systemd logged `exit 1 / FAILURE` on 07-19 AND
      07-20 — the night it genuinely failed and the night it succeeded-then-was-killed are **indistinguishable** in the
      journal. **Gate**: (b) liveness assertion shipped; curl `--max-time` ≥180s (or 202-immediate); the two new defects
      below fixed; and the REAL gate — **one reconcile run observed end-to-end producing a `plan_health_result` + a
      pushed `plan_reconciler/*` branch**. Until that is seen once, treat this subsystem as NEVER-VERIFIED, not merely
      "re-armed". **➡️ REMAINING WORK MOVED 2026-07-20 to `ao_scheduled_agent_hygiene_2026_07_20.md` (AO-dispatched) —
      the curl fix, the (b) liveness assertion and the end-to-end verification gate live there now. Do NOT action here;
      this entry is kept as the audit record.** **✅ DONE 2026-07-23 — all remaining work landed or re-homed via
      `ao_scheduled_agent_hygiene_2026_07_20.md` (archived 2026_07)**: the curl false-failure fix
      (`agent-orchestrator@078c631`) and the (b) daily liveness assertion are both `- [x]` there. **The one residual —
      the REAL end-to-end gate ("prove ONE reconcile run producing a `plan_health_result` + a pushed `plan_reconciler/*`
      branch") — is NOT lost: it is tracked as its own Phase-8 todo below.** Flipping here removes double-tracking, it
      does not close the gate. Until that Phase-8 item ticks, this subsystem stays NEVER-VERIFIED, exactly as this entry
      warned.
- [x] [BACKEND] P0. **The prereq-blocked reaper KILLS freshly-spawned agents that land on a previously-blocked slot ✅
      **DONE via `ao_dispatch_liveness_p0_2026_07_20.md` (archived 2026_07); flipped 2026-07-20.** (generic; it is what
      killed the 07-20 reconcile run).** `server/worker_liveness_watchdog.py:1180-1265` keeps
      `self._prereq_blocked_since[sid]` keyed by **slot id only**, and never invalidates it when a NEW agent spawns into
      that slot. The early-out `if held_task is None and not had_session: continue` only skips when the slot has NO
      session — so once a fresh session appears on a slot whose timer already matured, the reaper kills it and logs the
      tell-tale `released_task: null, killed_session: true`. Measured 2026-07-20: `agt-99684d` booted on slot 3 at
      01:03:41 and was killed at 01:04:00 with `blocked_seconds: 3604` — an hour-old timer belonging to the slot's
      PREVIOUS occupant. **This is not reconciler-specific**: any dispatch (backlog worker, escalation, plan_health)
      landing on a slot with a matured prereq timer is killed within one watchdog tick. Fix BOTH: (i) pop
      `_prereq_blocked_since[sid]` on every spawn into the slot (or key the timer by slot+session/agent id so a new
      occupant re-arms from zero), and (ii) exclude non-backlog typed agents (plan_health / plan_reconciler /
      escalation) from this reaper entirely — its premise is "the BACKLOG queue is fully prereq-blocked so idle BACKLOG
      workers should be released", which says nothing about a scheduled agent. **Gate**: a regression test spawning into
      a slot with a matured `_prereq_blocked_since` asserts the new session SURVIVES; plus a test that a
      plan_reconciler-kind agent is never selected by the reaper. Provenance: B4 audit 2026-07-20. **➡️ MOVED 2026-07-20
      to `ao_dispatch_liveness_p0_2026_07_20.md` (AO-dispatched) — do NOT action here; this entry is kept only as the
      provenance record.**
- [x] [BACKEND] P2. **The /boot read-confirmation gate demands `worker.md` from typed agents that were never pointed at
      it — every plan_health/plan_reconciler boot is 428'd once.** `server/routes/slots_worker.py:80` calls
      `prompts.expected_read_files("worker", req.slot_role)` with the base role **hardcoded to `"worker"`**, so expected
      = `[RULES.md, worker.md, <craft>]`. A plan_health/plan_reconciler worker's boot stub points it at `RULES.md` +
      `plan_reconciler.md` (never `worker.md`), so the gate rejects the first `/boot` with 428 and logs
      `boot_read_unconfirmed {"missing": [".../agents/worker.md"], "provided": ["RULES.md", "plan_reconciler.md"]}` —
      **176 such events since 07-18**. It self-heals (the 428 hint makes the worker re-read and retry ~10s later, then
      `slot_boot` succeeds), so it is wasted tokens + a permanently noisy signal rather than an outage — but it is a
      latent hard-fail for any agent that does not retry, and it makes `boot_read_unconfirmed` useless as an alert. Fix:
      pass the ACTUAL agent kind (the spawn side already composes the right role), not the literal `"worker"`. **Gate**:
      a plan_reconciler boot confirms on the FIRST POST; `boot_read_unconfirmed` count drops to ~0 in a 24h window.
      Provenance: B4 audit 2026-07-20. **➡️ MOVED 2026-07-20 to `ao_scheduled_agent_hygiene_2026_07_20.md`
      (AO-dispatched) — do NOT action here.** **✅ DONE 2026-07-23 via `ao_scheduled_agent_hygiene_2026_07_20.md`
      (archived 2026_07), todo 3.** Verified at flip: child todo `- [x]`.
- [x] [BACKEND] P2. **Sub-question left open by the B4 audit: why did the 07-15/17/18 reconcile runs die 7–7.5 min in?**
      Each was `plan_health_dispatched` then `tmux_session_lost … archived_lifecycle_complete: true` ~7 min later with
      no result (07-15 `agt-2d8441` is odder still — `finished_at` 07:30, 6h25m after a session that vanished at 01:12).
      The 07-20 kill has a NAMED cause (prereq reaper); these three do not, and 7 min is far too short for an opus/max
      full-corpus reconcile when the haiku REPORT pass alone medians 280s. Do NOT assume the prereq-reaper fix covers
      them — verify by watching the next run, or by pulling those sessions' tmux/agent rows. **Gate**: each of the three
      has a named cause, or the next clean run proves the class is closed. **➡️ MOVED 2026-07-20 to
      `ao_scheduled_agent_hygiene_2026_07_20.md` — do NOT action here** (it was briefly duplicated in both plans; the
      hygiene plan owns it because the end-to-end reconcile run there is what will resolve or refute the class). **✅
      DONE 2026-07-23 via `ao_scheduled_agent_hygiene_2026_07_20.md` (archived 2026_07), todo 5** — named cause for all
      three via activity-log archaeology (identical signature: clean boot, real logged progress, then a clean death),
      NOT assumed from the reaper fix. The gate asked for "a named cause or the next clean run proves the class closed";
      the child answered with the former.

### Phase LAST — operator-sequenced

- [ ] [BACKEND] P0. **Recovery-audit Layer-1 producer rewire (operator ruling B, "do it at last").** Stand up the
      standalone recovery-audit-signoff producer (NOT an AO worker-role): consume PubSub `agent-recovery-actions`, POST
      verdicts to the live `POST /safety-ops/signoffs`; unmock the DART feed; clean the stale `routes/agents.py:146`
      comment. Only start once Phases 0–4 are done (the operator's sequencing). Source: doc #9. **Gate**: a real signoff
      flows PubSub→producer→alerting-service→DART with the mock feed retired; codex Layer-1 banner replaced with the
      live description.

### Phase 7 — INDEPENDENT AGENT-AUDIT FINDINGS (Claude, 2026-07-17) — ⚠️ NOT from the issue docs

> **These are MY OWN findings** from a fresh pass over the AO codebase, the live DB/activity-log, and the codex AO docs
> — kept deliberately SEPARATE from Phases 0–6 (which trace to issue docs or operator reports) so the operator can
> review them on their own merits. **REVIEWED + RATIFIED 2026-07-18**: AF-1 (ratified + root-cause-why-they-fail added),
> AF-2 (folded into the Phase-6 plan_health throttle — no separate work), AF-3 (LOW priority — 40 MB is not big; only
> unbounded growth matters), AF-4 (ratified — build the snapshot-age assertion), AF-5 (ratified + EXPANDED to
> per-account/agent/slot token+message usage), AF-6 (done, ao@c03ccce). Scope honesty: codex claims were SPOT-checked
> (alerting, governor, paused semantics, recovery Layer-1 — the last two via Phases 0–6 work), not exhaustively diffed;
> the deep codex↔code diff belongs to the Phase-5 `ao_docs_reconciliation` close-out. One false lead corrected along the
> way: an early probe reported `qg-host-governor.sh` missing from the VM — wrong path (it lives in
> `scripts/quality-gates-base/`, not `scripts/dev/`); at the real path it answers `MODE=token K=2` (drift already
> recorded on the governor plan, no new item).

- [x] [BACKEND] P1. **(AF-1) CI-wall escalator burn: 189 dispatches / 7d for 50 escalations, 83 UNRESOLVED (43%).**
      Measured from `activity_log` (7d, wall_type=`ldr_qg_failure`): `escalation_queued=50`, `escalation_dispatched=189`
      (≈3.8 dispatches per escalation — redispatch churn), `escalation_resolved=108`, `escalation_unresolved=83`. Every
      dispatch is a full cicd agent session; nothing in any open issue doc tracks escalator EFFICACY — the alerting
      codex governs how escalations PAGE, not whether they WORK. Proposal: (a) an unresolved-escalation triage pass
      (what are the 83 — one recurring wall or many?); (b) a redispatch cap + backoff per escalation_id — **implemented
      ON the ONE fleet-scoped cooldown store from the Phase-6 blocked-task item, not a separate escalator engine**; (c)
      a resolved:dispatched efficacy KPI in the daily digest; **(d) RATIFIED (operator 2026-07-18) — root-cause WHY the
      escalators fail: sample the 83 unresolved and classify the cause — boot prompt too shallow / missing context, the
      QG-failure payload handed to them is insufficient, OR the failures are genuinely too hard for the cicd role+model
      (→ needs a model bump / human hand-off). Route the fix by class (prompt hardening vs richer failure context vs
      model tier vs escalate-to-operator).** **Gate**: the 83 are explained WITH a cause-class breakdown; redispatch per
      escalation capped; efficacy KPI visible; the prompt/context/model fix (whichever the classification points to) is
      applied or a follow-up filed. **➡️ MOVED 2026-07-20 to `ao_fleet_observability_kpis_2026_07_20.md` — do NOT action
      here.** **✅ DONE 2026-07-23 via `ao_fleet_observability_kpis_2026_07_20.md`, todos AF-1a + AF-1b.** All four gate
      clauses met: the 83 explained with a cause-class breakdown (65% NEVER_FOUND_ROOT_CAUSE / 33% FOUND_THEN_SILENT /
      2% HIT_BLOCKED_QUESTION); redispatch capped on the shared cooldown store (`agent-orchestrator@5dd9bbc8`); efficacy
      KPI visible via AF-5; and the classified fix applied (`unified-trading-pm@a35c6996`) **with the re-measure filed
      as a follow-up** — that follow-up is the child plan's one remaining open todo, target ~2026-07-27. If the
      re-measure shows no drop, AF-1a reopens there, not here.
- [x] [INFRA] P2. **(AF-2) plan_health true daily volume is 55 dispatches/24h — 13 of which produced NO result.**
      `plan_health_dispatched=55`, `plan_health_result=42`, `plan_health_dispatch_failed=4` in the last 24h — worse than
      the 5.5h sample in Phase 6, and each run is a **haiku** worker (`agents/plan_health.md` `model: haiku` — NOT
      sonnet; the cheap radar) digesting ~449 plan skeletons. MEASURED 2026-07-18 (6-day activity_log): 288 dispatched /
      186 result / 59 failed → only ~65% produce a result; run duration median 280s, mean 288s, p90 6.5 min, max 10.5
      min. The result-less dispatches are pure waste (superseded/died mid-run). This is EVIDENCE strengthening the
      Phase-6 cooldown item, plus one addition: the cooldown gate should also require the PREVIOUS dispatch to have
      posted its result (or timed out) before a new one spawns. **Gate**: folded into the Phase-6 plan_health item's
      acceptance. **➡️ MOVED 2026-07-20 to `ao_fleet_observability_kpis_2026_07_20.md` — do NOT action here.** **✅ DONE
      2026-07-23** — its gate was explicitly "folded into the Phase-6 plan_health item's acceptance", and that item
      shipped via `ao_fleet_observability_kpis_2026_07_20.md` (AF-2+Phase-6 throttle). Flipped with the Phase-6 item
      above.
- [x] [BACKEND] P3. **(AF-3) `activity_log` has NO retention policy — unbounded growth on the hot DB.** 83,813 rows
      spanning 20 days (~4.2k/day), db 40 MB. Agents get `prune_finished_agents` (7d) and tasks get orphan-GC;
      `activity_log` has nothing (grepped `state_store/` — no delete/prune path). Fine today, but it is silent unbounded
      growth on the dispatch-hot SQLite file, and the log IS the fleet's audit stream. CONTEXT (operator asked
      2026-07-18): **83k rows / 40 MB is NOT big for SQLite** (it handles millions of rows comfortably) — there is NO
      problem today; the only real risk is UNBOUNDED growth over MONTHS (write-latency creep on the write-hot DB). So
      this stays **low priority**: a simple age-based prune (90d) OR just a growth alarm suffices — not urgent, no
      redesign. Proposal: age-based retention (e.g. 90d) with optional archive-to-S3 via the existing snapshot loop
      before delete. **Gate**: a retention decision recorded + implemented (or explicitly deferred with the growth-alarm
      in place). **➡️ MOVED 2026-07-20 to `ao_fleet_observability_kpis_2026_07_20.md` — do NOT action here.** **✅ DONE
      2026-07-23 via `ao_fleet_observability_kpis_2026_07_20.md`, todo AF-3.** The gate explicitly allowed "a retention
      decision recorded + implemented (or explicitly deferred with the growth-alarm in place)" — the recorded outcome is
      DEFER pruning WITH the growth alarm implemented, i.e. the acceptable-outcome branch, not an unfinished item.
- [x] [INFRA] P2. **(AF-4) Disaster-recovery snapshots are wired but their RECENCY is unverified — silent-by-absence
      risk.** `gcs_sync.SnapshotLoop` runs and `ORCHESTRATOR_S3_BUCKET=uts-orchestrator-state-427895769566` is set
      (systemd env; GCS unset by design on the AWS host). But no local `state.json` was found at the expected path
      during the probe, and NOTHING asserts snapshot age — a broken snapshot loop would look exactly like a working one
      until the day state.db is lost (same class as the reconciler timer that silently vanished, Phase 6). **RE-VERIFY
      FIRST (2026-07-18) — the "no local state.json at the expected path" evidence is likely a PROBE ARTIFACT**: the
      probe ran as `ubuntu` without the systemd env, so it checked the in-repo default, not
      `/var/lib/orchestrator/state.json` (same root as the Phase-4 DB_PATH bug). Once Phase-4 moves state in-repo to
      `data/state/`, the default path IS correct and the artifact disappears. **RATIFIED (operator 2026-07-18: "decide
      yourself" → BUILD it)** — a silent snapshot failure = eventual data loss, and the age assertion is cheap.
      Proposal: (a) re-measure the S3 object's last-modified NOW (the REAL signal, independent of local path); (b) add a
      snapshot-age assertion (digest line or health endpoint: last successful snapshot < N hours, alert on breach); (c)
      one documented restore drill. **Gate**: measured snapshot age recorded; the age assertion alerts when the loop is
      deliberately stopped in a test. **➡️ MOVED 2026-07-20 to `ao_fleet_observability_kpis_2026_07_20.md` — do NOT
      action here.** **✅ DONE 2026-07-23 via `ao_fleet_observability_kpis_2026_07_20.md`, todo AF-4** —
      `agent-orchestrator@3fd6129` (SnapshotRecencyCanary asserts the DR SQLite backup is fresh). Verified at flip: SHA
      exists on the branch.
- [x] [BACKEND] P2. **(AF-5) Dispatch→done conversion is ~18% and NO surfaced metric tracks fleet efficiency.** 24h: 310
      boots / 154 dispatches / 27 done — ≈11.5 boots and ≈5.7 dispatches per completed task even with the spawn budget
      fixed (the leaks are 117 skips + 96 session-losses, i.e. Phases 2/3/6 mechanics). The OBSERVABILITY gap is
      separate and unowned: no dashboard/digest KPI exposes boots-per-done or dispatch→done conversion, so the fleet
      "looks busy" while ~4 of 5 dispatches produce no completion, and nobody sees a regression until an operator
      manually reads the activity log (how every incident in this plan was found). Proposal: daily-digest + dashboard
      KPIs (spawns, dispatches, done, conversion %, boots-per-done, top skip reasons) with a wow-level alert on sharp
      regression. **RATIFIED + EXPANDED (operator 2026-07-18): ALSO attribute USAGE per slot / agent / account —
      tokens + messages consumed — so it is visible WHERE the account budget goes.** Today nothing shows which
      agent/slot/account burned the quota, yet the fleet hits usage limits even across 4 accounts; add per-account +
      per-agent token/message counters (sourced from the usage-poller / transcript sizes) and a "usage by account" view
      on the same surface, so an account nearing its cap and the agent driving it are both visible before failover
      fires. **Gate**: the efficiency KPIs render; a per-account usage breakdown is visible; the 2026-07-12-class
      degradation (spawn:dispatch 0.6:1→44:1) would have been caught within one digest cycle. **➡️ MOVED 2026-07-20 to
      `ao_fleet_observability_kpis_2026_07_20.md` — do NOT action here.** **✅ DONE 2026-07-23 via
      `ao_fleet_observability_kpis_2026_07_20.md`, todos AF-5 (backend) + AF-5-followup (dashboard card,
      `agent-orchestrator@efc52fa`).** Both the efficiency KPIs and the per-account usage breakdown the operator added
      at ratification are rendered.
- [x] [REVIEW] P3. ✅ **(AF-6) `ENV_VARS.md` residual multi-VM framing — DONE (ao@c03ccce).** Resolved as part of the
      `ao_config_env_var_consolidation_2026_07_18` Phase-4 rewrite: ENV_VARS.md was rewritten to the two-class shape,
      dropping the retired `tab/<vm_id>/<slot>` branch example and the "Fleet VM (epic worker)" section header for the
      single-VM `planning` reality, verified against `server/config.py`.

### Phase 8 — residuals inherited from ARCHIVED child plans (2026-07-20)

> Each child plan below landed all its code and was archived; the item left here is the part that **calendar time or an
> operator action** gates, not code. This plan now OWNS them — the child is archived and must not be reopened. Each
> cites its source so the evidence trail survives.

- [x] [BACKEND] P0. **Re-measure the `tmux_session_lost` rate and record the delta.** Baseline **192 events since
      2026-07-18** (measured 2026-07-20). All four fixes are confirmed LIVE on the VM (`1e7fec0`, `390cdde`, `d84109a`,
      `f641968` all ancestors of the deployed HEAD, verified by SSM 2026-07-20 14:19 UTC; service restarted 14:15:21
      UTC). Re-measure over a window comparable to the baseline. **Report the honest number either way** — if the rate
      does NOT drop, record that the reaper was NOT the driver, so the churn hunt resumes with one hypothesis eliminated
      rather than quietly assumed closed. **Gate**: before/after counts over comparable windows + an explicit verdict.
      _Source: `ao_dispatch_liveness_p0_2026_07_20.md` (archived), todo 8._ ✅ **Measured 2026-08-08**: pre-fix 2-day
      window (Jul 18-19): 89+100=189 events (~95/day). Post-fix comparable 2-day window (Aug 6-7): 293+352=645 events
      (~322/day). **VERDICT: rate did NOT drop; ~3.4× INCREASE. The 4 reaper fixes are NOT the primary driver of
      `tmux_session_lost`. Churn hunt resumes with orphan-reaper hypothesis eliminated.**
- [x] [BACKEND] P0. **Stale-dispatch invariant — the live 24h spot-check.** Code + 9 regression tests shipped
      (`agent-orchestrator@aa81706`, `server/stale_dispatch.reclaim_stale_dispatches()`), including the no-double-
      dispatch race assertion. **Only the operational proof remains**: live `dispatched` count equals live-worker-held
      count across a 24h window. Needs the fix live for a full day before it means anything. **Gate**: the 24h
      comparison, stated explicitly. _Source: `ao_worker_lifecycle_reap_2026_07_20.md` (archived), todo 4._ ✅
      **Measured 2026-08-08 ~08:21 UTC**: `dispatched`-status task count = 6; slots with `current_task` set = 6; exact
      1:1 mapping, zero orphans in either direction. 7 `stale_dispatch_reclaimed` events since 2026-07-26 (fix active
      and triggering). **VERDICT: PASS — invariant holds.**
- [x] ✅ [BACKEND] P0. **Prove ONE plan_reconciler run end-to-end (the reconciler's real gate) — plus pin two named
      residuals from the root-cause fix.** Two runs have died so far (07-20 `agt-751738` at 07:33:30, same
      `tmux_session_lost`/`archived_lifecycle_complete` signature as the historical 07-15/17/18 deaths) — root-caused to
      an UNGUARDED `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` reaping a live-working reconciler whose
      slot had flipped to `idle` (idle-reclaim, `ticks=2`), 1h38m BEFORE the `f641968` typed-agent-exemption guard was
      even committed — so the fix is plausible but UNTESTED (no reconcile run since it deployed). **Gate**: (a) observe
      a full run producing BOTH a `plan_health_result` activity row AND a pushed `plan_reconciler/<dispatch_id>` branch
      — cite the dispatch_id, result row, and branch name; do not tick on a green-looking journal line alone; (b) **R1**
      — pin the exact code path that flips a typed agent's slot `working`→`idle` (empirically happened at/around a
      service restart on 07-20; not yet located in code — checked & excluded: seed-from-tabs, claim_slot, the
      dispatch-ack requeue, the 25-min health stale-timeout); (c) **R2** — on the next run, confirm the watchdog logs an
      EXEMPTION for the reconciler's slot (the `typed_agent_sessions` continue at `worker_liveness_watchdog.py:1172`)
      instead of a kill, and capture the slot's status column during the run — if it still reaps, the `AgentRow` guard
      is being defeated (investigate whether a restart archives/clears the AgentRow or its `tmux_session`). **Operator
      direction 2026-07-20: hold this retry until the other concurrently-landing AO plans (`ao_dispatch_liveness_p0`,
      `ao_failover_multi_vm_readiness`, `ao_fleet_infra_hardening`, `ao_fleet_observability_kpis`,
      `ao_backlog_regen_integrity`, `ao_dispatch_cooldown_and_park`) settle** — a live central VM mid-restart-churn from
      several concurrent plans is a bad environment to draw conclusions in. **Gate cleared — corrected 2026-08-06
      (/plan-reconcile ao): all 6 named plans are now confirmed archived** (`ao_fleet_infra_hardening` corrected above
      to ✅ ARCHIVED, 5/5, no residual; the other 5 were already shown archived in the split-out table above). The hold
      no longer blocks a retry — this P0 stays unflipped, the run itself still needs to happen. \_Source:
      `ao_scheduled_agent_hygiene_2026_07_20.md` (archived), todo 4 (+ R1/R2 residuals carried in todo 5).* **✅ DONE
      2026-08-10 — (a)(b)(c) all recorded with evidence.** (a) A full run completed end-to-end, standing behavior since
      2026-08-06: cited `dispatch_id=agt-a398c9` — `plan_health_dispatch_initiated` row `396415` @ 2026-08-09 03:02:46
      UTC → `plan_health_result` @ 04:43:25 UTC (contradictions=5, doc_drift=5, fixes_applied=12, filed=4,
      commit_sha=40ad77233, pr_url=https://github.com/IggyIkenna/unified-trading-pm/pull/2653) → branch
      `plan_reconciler/agt-a398c9` on origin; 20 completed reconcile runs since 2026-08-06 each with a pushed branch.
      (b) R1 pinned: `WorkerLivenessWatchdog._reclaim_exited_slot()` (`worker_liveness_watchdog.py:1311-1359`), gated on
      `has_session()==False` → `reset_slot_worker_state(...,"idle")`; the OLD `_reclaim_idle_lingering_sessions` path is
      structurally incapable of touching a live typed agent. (c) R2 confirmed live: `orch-slot-19`'s reconciler sat
      3134s heartbeat-silent yet stayed `working`, protected by the terminal-lifecycle
      `watchdog_scheduled_heartbeat_timeout`=3600s (`config.py:499`) vs the persistent 900s (`config.py:489`). Residual
      filed separately: `/plans/active/issues/plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md`.
- [x] ✅ [BACKEND] P0. **Role lifecycle-field reclassification — align the declared `lifecycle` on plan-worker roles
      with reality.** `backend_engineer` / `ui_developer` / `quant_dev` / `infra` are declared `lifecycle: one_shot`;
      reclassify to `persistent`, and resolve `data_engineering` (scheduled-vs-persistent). **NOT required for
      correctness** — the shipped fix rekeyed reaping on DISPATCH CONTEXT (a bound `one_shot` `AgentRow`), so nothing
      reads `role.lifecycle` to decide reaping any more; this is a declared-vs-actual **documentation-integrity** item.
      The risk of leaving it is that the next person reads the field and believes it (it is exactly what caused the
      original bug — see the archived plan's Lessons: "Lifecycle is a property of the DISPATCH, not the role").
      **Operator-owned timing** (2026-07-21): "after updating docs, fixing this, and everything discussed." **Gate**:
      each role's `lifecycle` matches its real dispatch pattern, or a recorded decision says why the declared value
      stays. _Source: `ao_worker_lifecycle_dispatch_context_2026_07_21.md` (archived 2026-07-23), its "Deferred
      (tracked, not this plan's scope)" item — which had NO successor owner until this migration._ **✅ DONE 2026-08-10
      — all 5 role files reclassified.** `agents/{backend_engineer,ui_developer,quant_dev,infra,data_engineering}.md`
      now all declare `lifecycle: persistent` (they drain the backlog via the /boot→work→/done loop, not event-spawned
      one-offs); `data_engineering` resolved to `persistent` per the 2026-08-06 `task_role_group` ruling. Updated the
      agent-orchestrator tests/comments that hardcoded the old values (`test_role_registry.py` `_EXPECTED`,
      `test_reap_orphan_agents.py`, `test_task_usage_windows.py` docstrings, `tests/fixtures/agents/*.md` mirrors,
      `state_store/{agents,slots}.py` comments) + the 2 codex SSOTs (`agent-orchestrator-worker-liveness.md`,
      `agent-orchestrator-single-vm-architecture.md`). No dispatch/reap behavior changed (reaping keys on dispatch
      context, never this field). Commits: `agent-orchestrator@c72daaa` (state_store + tests) + `@4421129` (test
      fixtures), `unified-trading-pm@14f1dcd` (role files). Re-verified 2026-08-10 (slot 24, review): all 5 role files
      declare `lifecycle: persistent`.
- [x] ✅ [SCRIPT] P2. **Remove the dead `ORCHESTRATOR_REGEN_REQUIRE_VM_MATCH=true` from the live planning-VM
      `.env.local`.** — DONE 2026-07-21 (operator authorized, superseding the A6 "fold into re-bootstrap" default — done
      in-window alongside the DB migration). Took the `sed -i` backup-first route (backups
      `.env.local.bak.20260721T025759Z` + `.bak2.20260721T030238Z`) with a clean `disable`/`stop`/`start`. **The var
      removal alone would have left its 2-line explanatory comment ORPHANED above the unrelated
      `ORCHESTRATOR_WATCHDOG_DAILY_CAP`** — caught on operator recheck and removed too, so the net change vs the
      pre-edit backup is exactly 3 lines gone (the var + its 2 comments), file otherwise byte-identical. Behavioral
      removal was effective before the restart (the field was already a silent no-op via `extra="ignore"`). _Source:
      `ao_config_env_var_consolidation_2026_07_18.md` (archived), Phase-0 P2._
- [x] ✅ [SCRIPT] P2. **Verify the `.env.local` cleanup landed** — DONE 2026-07-21. Verified three ways: `diff` of the
      current `.env.local` vs the pre-edit backup = exactly the 3 intended lines removed; a full redacted inventory read
      confirmed no other retired/duplicate vars and no `ORCHESTRATOR_DB_PATH`/`STATE_JSON` present; and the backend came
      back clean (`curl localhost:8765/api/mode` → `mode=live`, `db_path` in-repo). _Source:
      `ao_config_env_var_consolidation_2026_07_18.md` (archived), Phase-5._

## Open questions — state as of 2026-07-20 (read this before picking up work)

Every item below is ALREADY a todo above; this section only separates **what needs an operator ruling** from **what is
just unfinished investigation**, and records the standing recommendation so the next session does not re-derive it.

**A — operator rulings. A1–A4 + the new A5/A6 were RULED 2026-07-20 (operator: "go with your recommended ones"); the
standing recommendation in each row IS now the ruling. A7 was RULED 2026-07-28 (operator gated-decision closeout pass) —
all seven are now resolved.**

| #   | Question                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Standing recommendation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A1  | NULL `brief_hash` tail (54 rows, all `done`) — backfill / age-out / accept-permanently? (Phase 1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | **Accept permanently + a growth alarm.** All 54 are `done` audit history, 0 in-flight; backfilling is write-risk for no gain. Growth is the real signal (growth = backfill regression).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| A2  | `audit_false_done` contract — checkbox-state as truth, or must `done_sha` be the flip-commit? (Phase 1)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | **Checkbox state = truth.** The gate answers "is the work done"; the checkbox is the SSOT. Keep the sha as provenance, but a mismatched sha must not manufacture a false-positive (that IS sports-002).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| A3  | mvp-defi unpark — the named flipper plan may be superseded (Phase 3)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Re-point the unpark to the `defi_consolidated_closeout_2026_07_18` owner, **or** park it explicitly until the DeFi re-architecture resumes. No park may exist without a named LIVE flipper.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| A4  | plan_health interval                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | **RULED 2026-07-18: 2h**, adjustable later. Ships with the Phase-6 gate; no live knob today.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| A5  | `failover.py` — delete, or keep-and-fix the paused-slot guard? (new, from B3)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | **RULED 2026-07-20: KEEP + fix.** _(An earlier same-day "DELETE" ruling was REVERSED by the operator within the hour: multi-VM is dormant but likely to return for resilience/backup, so the infra stays.)_ Work moved to `ao_failover_multi_vm_readiness_2026_07_20.md`. The paused-slot P2 below is therefore **NOT superseded — it is live work** and moves there too. Reversal lesson: "never fired" is evidence of DEAD code only if the capability is unwanted; otherwise it is evidence of UNTESTED code. That is a question about intent — ask it before proposing deletion of dormant infra.                                                                                                                                                                                                                                                                                                                                                                                                                        |
| A6  | VM `.env.local` tidy (vars now redundant against code defaults)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | **RULED 2026-07-20: fold into the next re-bootstrap.** Do NOT hand-edit the live VM — low value, non-zero risk, no urgency.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| A7  | `escalation_pipeline_mvp` — unpause or leave paused? **RULED 2026-07-28** (operator gated-decision closeout pass, general theme applied — see Progress Log). The plan itself was ARCHIVED 2026-07-23 (operator) and its 5 UNBUILT todos moved to the `escalation_and_disaster_recovery_master` epic; archiving did not answer this on its own, but the pause's own stated reason has since evaporated — the 2026-06-26 pause tied resumption to "next quarter together with W7/W8/W9 (message broker dependency)", and W9 (`role_registry_schema_and_broker_mvp`) was archived NOT-REQUIRED 2026-07-16, superseded by `assigned_role` dispatch (confirmed in the epic's own 2026-07-23 Progress Log — reply-routing already works via the existing `POST /api/blocked/{id}/answer` path, no broker needed). | **UNPAUSE now — resume the escalation pipeline workstream** (epic frontmatter flipped `status: paused` → `active`). With the blocking dependency gone and the 5 todos fully scoped + code-verified UNBUILT (not superseded by any newer work), the general rulings "unpause whatever needs unpausing to unblock a task" + "opt for full completions, no shortcuts, full functionality" apply directly: drive all 5 P1 todos in `escalation_and_disaster_recovery_master.md` § "P1 — escalation pipeline MVP" to FULL completion (role-agnostic escalation record, `open/in-progress/resolved` state + claim, scoped `/escalation/{id}` Slack link, answer-routing gate, deployment-ui filter tab) — no partial/MVP shortcut. **Prerequisite, before any of that code is written**: resolve the `/api/escalate` vs `/api/escalation/{id}` route-naming collision (rename one, or record why the near-collision is acceptable) — already correct regardless of the pause call, now added as the epic's explicit first P0 todo. |

**B — open investigations (no decision needed; just unfinished)**

| #   | Investigation                               | Note                                                                                                                                                                                                  |
| --- | ------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B1  | `l2_book-005/007` absent rows (Phase 1)     | ✅ **CLOSED 2026-07-20** — by design, two mechanisms (BLOCKED-\* never ingested; queued rows pruned when checked off outside dispatch). Absent set is 5 ids, not 2; 3 rows, not 4. Doc-only residual. |
| B2  | 96/day `tmux_session_lost` driver (Phase 2) | **Likely candidate found by B4** — the prereq reaper (new P0) kills fresh sessions. Re-measure AFTER that fix before hunting further; measured 192 events since 07-18.                                |
| B3  | Paused-slot SPILL path (Phase 6)            | ✅ **CLOSED 2026-07-20** — pull-spills safe; `failover._pick_least_loaded_slot` PREFERS paused slots. Latent (failover off, 0 events ever). Spawned a P3: is failover.py dead code under single-VM?   |
| B4  | plan_reconciler daily runs (Phase 6)        | ✅ **CLOSED 2026-07-20** — audited; verdict: 5 dispatches, **0 completions ever**. Spawned 3 new todos (P0 reaper, P2 boot-gate, P2 7-min-death).                                                     |

**Recommended NEXT: the P0 prereq-reaper fix** (Phase 6, filed by the B4 audit). B4 is closed and it turned up a bug
bigger than the thing it was checking: the reaper kills ANY freshly-spawned agent that lands on a slot with a matured
prereq timer — reconciler, escalation or backlog worker alike — within one watchdog tick. It is a silent work-destroyer
with a clear two-line fix and a cheap regression test, and it likely accounts for an unknown share of the fleet's "agent
vanished" churn (cf. B2's 96/day `tmux_session_lost`, which should be re-measured AFTER this lands — the two are
plausibly the same bug).

**Not an untracked finding:** plan_health's CLAUDE.md Tardis doc_drift (the "16/4 defaults ≈93% idle → scale up"
guidance contradicted by the 350x-collapse root cause) is ALREADY an open P0 `[DOC] OPERATOR RULING NEEDED` in
`plans/active/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md`. Do NOT file a duplicate — it is evidence for
the close-the-loop point: plan_health keeps correctly re-reporting a real, owned, unactioned item.

### Phase 9 — operator-reported dashboard bug (2026-07-24)

> **Renumbered from a duplicate "Phase 7" heading (P2 finding, corrected 2026-07-25)** — this section collided with the
> "INDEPENDENT AGENT-AUDIT FINDINGS (Claude, 2026-07-17)" Phase 7 above (line ~581), which
> `ao_fleet_observability_kpis_2026_07_20.md`'s "Phase 7 (AF-1…AF-5)" provenance citation resolves to. This section
> becomes Phase 9 (next free number after Phase 8) to disambiguate.

- [x] ✅ [UI] P0. **Blocked-question option buttons submit on click instead of select-then-submit.** — **DONE via
      `agent-orchestrator@1badd41`.** `BlockedCard` now tracks `selectedOption` state: clicking a lettered option only
      highlights it (`.opt.selected`, no `onAnswer` call); a new explicit Submit button (shown once an option is
      selected) commits it. Re-clicking a different option swaps the selection; typing in the free-text input or
      clicking "Other" clears any lettered selection (mutually exclusive). **Gate actually used**: not `layout.test.ts`
      as originally scoped (that harness is deliberately jsdom-free / pure-function-only — no React render, per
      `vitest.config.ts`'s own header comment — so it can't exercise a click/callback interaction); instead added
      `dashboard/tests/e2e/blocked-questions.spec.ts` (2 cases) against the dashboard's existing real Playwright+backend
      e2e infra. Verified fail-before/pass-after by hand: stashed the fix and reran the new spec — both cases failed,
      one option click fired `slot-blocked-answered` immediately, exactly the reported bug; restored the fix and reran —
      both passed. Full `quality-gates.sh` green (1791 passed), full e2e suite green (14/14, including the 3
      pre-existing specs — unaffected).

## Externally blocked (tracked, not actionable here)

- ~~`/api/escalate` vs `/api/escalation/{id}` collision~~ — **RESOLVED-BY-RULING 2026-07-28, no longer externally
  blocked.** Was blocked on the escalation workstream un-pausing (operator ruling); see A7 above — the epic is now
  UNPAUSED and this fix is its explicit first P0 todo (`escalation_and_disaster_recovery_master.md` § "P1 — escalation
  pipeline MVP"). **Retagged BLOCKED-OPERATOR-DECISION → [BACKEND] P0**, a normal fully-scoped AO-dispatchable todo;
  must still land BEFORE any of that section's other 5 todos are coded. Moved out of "externally blocked" — tracked at
  its new home only, to avoid a stale duplicate record here.
- Backlog-relations UI — **blocked on the design agent's deliverable** (brief handed 07-17,
  `agent-orchestrator/docs/BACKLOG_RELATIONS_UX_BRIEF.md`). Lives at doc #8 todo 4. BLOCKED-UPSTREAM-DESIGN.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` + `…/agent-orchestrator-overview.md` — AO
  runtime architecture (dispatch/spawn/slots).
- `/codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only alerting (Phase-3/4 visibility surfaces).
- `/codex/04-architecture/recovery-defence-in-depth-layers.md` + `…/autonomous-recovery-matrix.md` — Layer-1 rewire.
- `/codex/05-infrastructure/per-tab-worktrees.md` — slot clones, ff-pull, shared uv cache.
- `/codex/06-coding-standards/quality-gates.md` — the shared-host QG cap Phase-4 enforces.
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured-verdict discipline for every gate above.

## Progress Log

> **Line-cap remediation (2026-08-03, round 1)**: entries from this plan's 2026-07-17 authoring through the 2026-07-28
> A7 ruling were extracted verbatim to
> `/plans/archive/2026_08/ao_open_issues_consolidated_close_out_progress_log_history_2026_08_03.md` to bring this doc
> back under the 1000-line hard cap. **Line-cap remediation (2026-08-10, round 2)**: entries from the 2026-08-02 marker
> through the 2026-08-08 Phase-8 measurement entry were extracted verbatim to
> `/plans/archive/2026_08/ao_open_issues_consolidated_close_out_progress_log_history_2026_08_10.md`. New entries append
> below the kept 2026-08-09 (round9) entry.

- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — Prior verdict re-verified, no whole-doc RECLASSIFY. Of
  the 5 remaining un-extracted open items (365, 474, 479-already-extracted-to-batch10, 677, 807): item 365
  (tmux_session_lost root-cause) stays genuinely open-ended per its own 2026-08-08 re-measure showing the rate
  INCREASED, not a simple bounded task; item 474 (ao_docs_reconciliation close-out) requires deep cross-doc verification
  spanning many scattered commits, not a mechanical check; item 677 (Layer-1 producer rewire) is operator-sequenced to
  run last. Item 807 (prove one plan_reconciler run end-to-end) is flagged, not extracted: `plan_reconciler` graduated
  to steady-state direct-push 2026-08-09 (see `ao_scheduled_jobs_review_gate_and_health_audit_2026_08_09.md`'s
  Background — 28+ consecutive clean runs 2026-08-02→08-09), which makes this item's literal gate (observe a pushed
  `plan_reconciler/<dispatch_id>` branch) now inapplicable to the current mechanism — closing it properly needs to
  reconcile the gate's INTENT against the new steady-state facts, not just cite one recent run; left open rather than
  force a possibly-wrong extraction.
