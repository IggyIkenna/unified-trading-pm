---
doc_type: plan
title: ci satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the ci tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 24
  conflict-cleared, bounded/deterministic items pulled directly from 14 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: draft
nature: process
asset_group: [ci]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /plans/active/github_actions_operator_gated_followups_2026_07_17.md,
    /plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md,
    /plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md,
    /plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md,
    /plans/active/issues/deployment_service_basedpyright_ratchet_exceeded_sports_trigger_2026_08_08.md,
    /plans/active/issues/ff_pull_fleet_drift_rca_2026_08_11.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md,
    /plans/active/issues/ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md,
    /plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3.6
estimate_calibrated_ai_days: 2.9
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
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# ci satellite AO dispatch batch 13 — 2026-08-13

> **`status: draft` — NOT ingested/dispatched.** Flip to `status: active` only after operator review. Every todo below
> was classified bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13
> full-sweep audit and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [ ] [CODE] P2. add slot/clone identification to every slot-cron-ff-pull.sh log verdict (five clones per repo currently
      write indistinguishably into one log file) Source: `plans/active/issues/ff_pull_fleet_drift_rca_2026_08_11.md`
- [ ] [CODE] P2. confirm/fix ff-starvation-detect.sh's early exit on a detached HEAD (currently produces no verdict from
      either side, allowing unbounded drift) Source: `plans/active/issues/ff_pull_fleet_drift_rca_2026_08_11.md`
- [ ] [CODE] P2. apply SUPERSEDED banners to the 3 retired-but-still-scanned codex docs per the workspace's stated
      convention Source:
      `plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md`
- [ ] [CODE] P2. distinguish 'no-frontmatter' from 'frontmatter present but YAML-parse-error' in
      check_codex_doc_freshness.py's _parse_frontmatter/_check_parsed Source:
      `plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md`
- [ ] [CODE] P2. pull real AWS Cost Explorer / EC2 instance-hours data for the CI VM's 2026-07-27-present retry-storm
      window and compute an attributable $ figure (flagged extraction-ready since 2026-08-01, never actually dispatched)
      Source: `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`
- [ ] [CODE] P2. investigate the real cause of the 2026-07-30 14:54-15:01Z mass tmux_session_lost cluster via the doc's
      own named candidates (a/b/c: cgroup/systemd action, manual/scripted kill, AWS-side event) now that the OOM-killer
      hypothesis is ruled out Source: `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`
- [ ] [CODE] P2. Hold/confirm a clean 60-consecutive-minute zero-new-CI-alert window before closing the incident
      (worker-monitorable, outcome-determinable, same shape as the AO-dispatched monitoring pattern used in the sibling
      pytest_timeout_60s doc) Source:
      `plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`
- [ ] [CODE] P2. Re-attempt gh run cancel/delete on strategy-service runs 31164709790/31164709402/31164709423 once
      GitHub's run retention ages them out; done-when: --status queued empty fleet-wide Source:
      `plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`
- [ ] [CODE] P2. Confirm promote PR #2714 merged green (QG run 31405420640) and LDR->main caught up, then close the
      issue Source: `plans/active/issues/ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md`
- [ ] [CODE] P2. Port the same doomed check-run supersede guard to ldr-to-main-promote-fleet.yml's per-repo path if/when
      the fleet bot shows the same wait-on-doomed-run shape Source:
      `plans/active/issues/ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md`
- [ ] [CODE] P2. PROVE the CI bootstrap script on a real bare host (VM launch + systemd/IMDS/GCP-ADC/runner-registration
      verification) -- container leg already proven, bare-VM leg genuinely blocked only on provisioning Source:
      `plans/active/github_actions_operator_gated_followups_2026_07_17.md`
- [ ] [CODE] P2. implement the consumer-QG promote fan-out gate in UAC's promote-gate workflow (per the 2026-08-08
      operator ruling; design + target consumer already specified in the doc) Source:
      `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`
- [ ] [CODE] P2. fix or prove rollout-cloudbuild.py's --apply preserves consumer-only `substitutions` keys (currently
      invisible to _cloudbuild_markers()), per the doc's own stated done-when Source:
      `plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md`
- [ ] [CODE] P2. fix/annotate the ~23 basedpyright errors in
      deployment_service/sports_trigger_{evaluation,periodic,scheduler,state}.py to drop BASEDPYRIGHT_MAX_ERRORS back to
      <=1293 (coordinate file-family ownership with sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md first,
      per the doc's own conflict-check note) Source:
      `plans/active/issues/deployment_service_basedpyright_ratchet_exceeded_sports_trigger_2026_08_08.md`
- [ ] [CODE] P2. Disable/fix the 4 named vacuous crons (sit-debounce-trigger, freeze-deferred-build-replay,
      fix-approval-timeout, supersede-stale-dep-update-prs) -- the bounded sub-part of the F4 item, separable from
      digest-drift-sweep's open-ended non-convergence investigation Source:
      `plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md`
- [ ] [CODE] P2. Classify each of the 7 residually-stalled repos' commit ranges since their baseline tag as 'correctly
      quiet' (no SOURCE_DIR-touching commit since baseline) vs a genuine gap in the patch-fallback logic -- a checkable,
      worker-determinable fact per repo. Source:
      `plans/active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md`
- [ ] [CODE] P2. Hoist the superseded-promote-PR cleanup in ldr_to_main_fleet_promote.sh above the SIT gate, scoped to
      ancestor-of-current-tip + concluded-failure PRs only (design constraint already specified in the todo) Source:
      `plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md`
- [ ] [CODE] P2. Fix sit-gate-stuck-detector.yml's dedup key to include the streak-count / monotonic-worsening signal
      alongside the flat cooldown timer Source:
      `plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md`
- [ ] [CODE] P2. Re-check whether unified-api-contracts/market-tick-data-service SIT-gate streaks reset to 0 once LDR
      commit velocity drops Source:
      `plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md`
- [ ] [CODE] P2. Slack alerting via notify-slack.yml for the 3 governor triggers (over-cap RSS, >20% baseline drift,
      host RAM >80% abort) Source: `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`
- [ ] [CODE] P2. Raise the PYRIGHT_TIMEOUT default (or document the override) in base-service.sh / quality-gates.md
      Source: `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`
- [ ] [CODE] P2. Fix _qg_governor_default_k() to call the already-correct _qg_physical_cores() instead of its own
      undeduped lscpu invocation (hyperthreading double-count bug) Source:
      `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`
- [ ] [CODE] P2. Stamp work-start after admission so MAX_DURATION excludes governor queue-wait (already-cited concrete
      fix, not a design question) Source: `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`
- [ ] [CODE] P2. Re-measure GitHub Actions billing for the 17+PM reverted repos (should read $0/unmetered) and the
      self-hosted VM's steady-state load average before vs. after, via the already-proven github-billing-token GSM
      secret + aws ce get-cost-and-usage procedure Source:
      `plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
