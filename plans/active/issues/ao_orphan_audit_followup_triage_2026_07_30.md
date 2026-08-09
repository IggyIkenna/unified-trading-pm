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
author: unknown
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
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
source:
  "interactive session, 2026-07-30 — operator ran the ao-tranche orphan audit, had the tracker's related: links +
  archival gap fixed, then said: archive what can be archived now, then work the resolution bucket next. This issue
  captures the remaining agreed-but-untracked next steps so they survive a context compaction."
---

## Todos

- [x] ✅ [OPERATOR] P1. **Approve/dispatch `ao_satellite_ao_dispatch_batch2_2026_07_30.md`** (flip `status: draft` →
      `active`). It already carries real, ready fixes for 6 docs from the orphan sweep (was 7 —
      `orphan_rootm_branch_unmerged_work_2026_06_05` resolved + archived 2026-07-30 directly, moot, no batch2 fix
      needed): `ao_done_require_origin_not_enforced_2026_07_29`, `dispatch_sequential_gate_fix_2026_07_24`,
      `branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27`,
      `git_status_reporter_stale_public_url_token_expiry_2026_07_24`,
      `orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24`,
      `ao_recovery_audit_layer1_deleted_2026_07_15` — nothing else is needed to unblock them. **Done when**:
      `status: active` + AO has picked it up (`/check-agent-orchestrator`). **na-eligibility-audit 2026-08-03
      (blocker-currency check): the first half is done — `ao_satellite_ao_dispatch_batch2_2026_07_30.md` now reads
      `status: active`** (flipped from `draft`), and shows real, substantive progress (4 of 8 todos already `[x]`,
      including a root-caused-and-fixed `agent-orchestrator@77769ab` item and a confirmed-moot item) — i.e. it has been
      worked, not merely approved-on-paper. Did not independently re-verify the second half (AO backlog pickup via
      `/check-agent-orchestrator`) this pass. Checkbox stays open since 4 of batch2's own todos remain `[ ]`, but the
      "approve/dispatch" ask itself is satisfied; a future toucher should check batch2's own remaining todos rather than
      re-approving anything here. **CLOSED 2026-08-06 (`/plan-reconcile ao`, operator present)** — measured at HEAD:
      `ao_satellite_ao_dispatch_batch2_2026_07_30.md` reads `status: active` with 4 open / 4 done todos. The ask this
      checkbox encodes ("approve/dispatch", i.e. flip draft→active) is fully satisfied and has been since 2026-08-03. It
      was left `- [ ]` on the mistaken basis that batch2's own remaining todos keep it open — but those belong to
      batch2's checkboxes, not to this approval ask, so holding this one open is false-unchecked and would have
      re-surfaced an operator decision that is already made. Nothing further is required of the operator here.
- [ ] [REVIEW] P1. **RULED 2026-08-06 (operator, separate interactive session): default disposition is
      fold-into-nearest-active-batch** for whichever of the 12 still genuinely need one — **a concurrent
      `/plan-reconcile ao` pass (same day, operator present) independently pre-screened the list against live state and
      found 5 of the 12 already moot/cleared, narrowing what this ruling actually applies to; both findings merged
      below, no conflict between them.** `[REVIEW]` tag (was `[OPERATOR]`) — for each doc the pre-screen table marks
      "genuine"/"partly", find the active batch/plan that already covers the closest related ground and fold the doc's
      remaining work into it (citing why that batch is the right home); only flag a doc back to the operator if NO
      natural home exists. Close-as-moot is still available per-doc if content resolves elsewhere before this is worked.
      **Done when**: each of the still-genuine docs has a recorded disposition (folded-into-<batch>, parked-flagged, or
      closed-as-moot) with evidence. **Rule on the 12 operator-gated docs from the orphan sweep**, one at a time — each
      is a genuine design/judgment fork with no evidence-based tiebreaker, per Phase 1 of the audit:
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

      **PRE-SCREEN 2026-08-06 (`/plan-reconcile ao`, operator present) — 5 of the 12 need no ruling; measured at HEAD,
      not recalled.** The list was assembled 2026-07-30 and has decayed since. Current state:

                                      | Doc                                                    | State at HEAD                     | Ruling needed? |
                                      | ------------------------------------------------------ | --------------------------------- | -------------- |
                                      | `escalation_backlog_repo_collision_blind_spot_2026_07_25` | ARCHIVED, `resolved`, 0 open / 2 done | **No — moot**  |
                                      | `autostash_pop_restores_foreign_wip_into_the_index_2026_07_17` | ARCHIVED, `resolved`, 0 open / 3 done | **No — moot**  |
                                      | `idle_slot_dirty_wip_never_auto_resolves_2026_07_20`    | ARCHIVED, `resolved`, 0 open / 9 done | **No — moot**  |
                                      | `per_slot_ff_pull_status_report_crons_stale_fleet_wide_2026_07_27` | ARCHIVED, `resolved`, 0 open / 3 done | **No — moot**  |
                                      | `external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25` | hold RELEASED 2026-08-06 (its blocking plan is archived, 0 open / 11 done) | **No — cleared** |
                                      | `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24` | active, 1 open `[DESIGN] P2`      | Yes — genuine  |
                                      | `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15` | active, 1 open `[INFRA] P2`       | Yes — genuine  |
                                      | `mdps_odds_horizon_bucket_launch_prep_stale_todo_duplicate_dispatch_2026_07_27` | active, 1 open `[BACKEND] P3`     | Yes — genuine  |
                                      | `prediction_trades_migration_concurrent_dispatch_2026_07_28` | active, 3 open `[BACKEND] P2`     | Partly         |
                                      | `unified_trading_pm_stash_pile_accumulation_2026_07_26` | active, 2 open `[OPERATOR] P3`    | Action, not decision |
                                      | `long_lived_vm_logs_not_backed_up_2026_07_02`           | active, 3 open `[SCRIPT] P2/P3`   | **Likely mis-tagged** |
                                      | `wip_preserve_refs_silently_unrecovered_2026_07_29`     | **ARCHIVED 2026-08-07**, 0 open / 5 done | **No — complete** |

      **Correction to this todo's own framing**: it asserts each of the 12 "is a genuine design/judgment fork with no
      evidence-based tiebreaker". That is no longer true, and for at least one doc was probably never true.
      `long_lived_vm_logs_not_backed_up_2026_07_02`'s three open items are bounded implementation todos naming
      concrete files (`launcher_common.sh`, `aws_ec2_launch_lib.sh`, `test_vm_launcher_scripts.py`) with stated
      done-whens — that is dispatch-eligible work under the workspace's own bounded-outcome bar, not an operator
      decision. `unified_trading_pm_stash_pile_accumulation_2026_07_26`'s two items are operator *actions* (agents are
      barred from `git stash drop` on foreign WIP), which is a different category again from a judgment call. Whoever
      picks this up should re-classify per-doc rather than inheriting the blanket "all 12 are judgment forks" label.

- [x] ✅ [REVIEW] P2. **Re-triage the 8 "conflict-gated" docs against current state** before drafting `batch3` — per the
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
      cleared/still-gated with evidence. **DONE (na-eligibility-audit 2026-08-03)** —
      `ao_satellite_ao_dispatch_batch1_2026_07_26.md` (now archived) records exactly this re-triage as completed
      2026-07-31 (interactive session): its own `## Deferred` banner gives a verdict for all 8 named docs —
      `ahead_push_sentinel_...`/`reaper_kills_inflight_...` re-triaged (verdicts recorded in their own Progress Logs),
      `orchestrator_failover_double_dispatch_...` still gated (different reason, root cause unidentified),
      `killed_slot_orphans_...` checkbox fixed, `one_shot_worker_completes_...`/
      `host_saturation_false_worker_kicks_...`/`utl_shared_clone_commits_repeatedly_reset_...` reclassified,
      `slot_recurring_wedge_...` needed one more live check. All 8 accounted for with evidence, matching this todo's
      done-when exactly.
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
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — deduped 2 accidental repeated entries (a duplicate
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md` and a leading-slash-vs-not duplicate of `ag-closeout-audit/SKILL.md`)
  that had crept in since the last scout pass; content otherwise unchanged.
- **na-eligibility-audit 2026-08-03** (reclassify pass): KEEP-NA, valid (blocker-currency only) — annotated todo 1 in
  place: `ao_satellite_ao_dispatch_batch2_2026_07_30.md` is now `status: active` with 4/8 todos done, so the
  approve/dispatch ask is satisfied even though the checkbox stays open pending batch2's own remainder. The other 3 open
  todos (rule on 12 operator-gated docs, bucket 7 unclear docs — todo 3 already closed) are unchanged judgment-heavy
  work per the 2026-08-01 verdict. Not a RECLASSIFY case. `assigned_vm` untouched.
- **context-scout 2026-08-03 (re-pass, updated methodology)**: re-verified, unchanged (4 entries). **Stale-candidate-
  pointer finding (not fixed here, flagged for `/plan-reconcile`)**: todo 1's list of 6 docs
  `ao_satellite_ao_dispatch_ batch2_2026_07_30.md` allegedly "carries real, ready fixes" for includes
  `ao_recovery_audit_layer1_deleted_2026_07_15` — `grep -in recovery` against the live batch2 doc returns zero hits
  naming that doc or its subject matter; batch2 does not actually cover it.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate. Re-verified: the
  stale-pointer finding above (batch2 doesn't actually cover `ao_recovery_audit_layer1_deleted_2026_07_15`) is still
  unfixed on the live batch2 doc.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (4 entries), still accurate. Re-verified: the
  stale-pointer finding (batch2 doesn't actually cover `ao_recovery_audit_layer1_deleted_2026_07_15` — a fresh
  `grep -in recovery` against the live batch2 doc still returns no hit naming that doc or its Layer-1-producer subject
  matter) is still unfixed on the live batch2 doc.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-affirmed. Both open `[REVIEW]` items are audit/judgment work
  (fold the still-genuine 12-minus-5-moot operator-gated docs into their nearest active batch; bucket the 7 unclear
  docs), the same shape as this skill's own work, not a deterministic worker-alone outcome. No new stale/superseded
  items found this pass.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — this doc's own 2 open items are themselves
  audit-judgment work (classify OTHER docs), not bounded per-fact checks — no round7-10 precedent converts an open-ended
  classification task into a mechanical one. Note: the doc's own earlier "Correction to this todo's own framing" already
  flags that ≥1 of the 12 named downstream docs (`long_lived_vm_logs_not_backed_up_2026_07_02`) is itself bounded,
  dispatch-eligible work — but that doc is not in this round's candidate list, so out of scope here; flagging for
  whoever next works this doc's own `[REVIEW] P1` item.
