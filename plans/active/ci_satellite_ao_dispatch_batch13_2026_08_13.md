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
status: active
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

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] [CODE] P2. ✅ add slot/clone identification to every slot-cron-ff-pull.sh log verdict (five clones per repo
      currently write indistinguishably into one log file) — unified-trading-pm@c89e109ea7 + `_clone_tag` (slot-<N>/main
      from cwd) prefixed on every `log()` verdict; 14/14 bats green. Source:
      `plans/active/issues/ff_pull_fleet_drift_rca_2026_08_11.md`
- [x] [CODE] P2. ✅ confirm/fix ff-starvation-detect.sh's early exit on a detached HEAD (currently produces no verdict
      from either side, allowing unbounded drift) — unified-trading-pm@bb75f3d5ce + new `FF-PULL DETACHED HEAD` verdict
      fires on behind>0 detached clone (before the false "clean→FF would succeed" exit); 12/12 bats green. Source:
      `plans/active/issues/ff_pull_fleet_drift_rca_2026_08_11.md`
- [x] [CODE] P2. ✅ apply SUPERSEDED banners to the 3 retired-but-still-scanned codex docs — already present on origin,
      no code change: data-catalogue-schema.md ⛔ banner @06a2301cb49 (2026-07-20) + ui-dependency-matrix.md &
      ui-functionality-requirements.md 🟡 banners @8fcb74f6a51 (2026-05-13), each pointing at its successor, all
      pre-dating this batch. Source:
      `plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md`
- [x] ✅ [CODE] P2. distinguish 'no-frontmatter' from 'frontmatter present but YAML-parse-error' in
      check_codex_doc_freshness.py's _parse_frontmatter/_check_parsed Source:
      `plans/active/issues/codex_freshness_ratchet_trips_on_calendar_blocking_all_pm_code_commits_2026_08_11.md` — ✅
      `unified-trading-pm@a68d8b716d`: `_parse_frontmatter` now raises typed `FrontmatterParseError` (with the parser's
      message) for present-but-unparseable frontmatter (missing closing delimiter / YAMLerror / non-mapping); genuinely
      absent frontmatter still returns None. `_check_doc` + `main()` catch it and emit reason=`yaml-parse-error` with
      detail instead of the misleading `no-frontmatter`. Blocks by default (fail-closed via `partition_by_agency`).
      40/40 unit tests pass (14 new).
- [x] ✅ [CODE] P2. pull real AWS Cost Explorer / EC2 instance-hours data for the CI VM's 2026-07-27-present retry-storm
      window and compute an attributable
      $ figure (flagged extraction-ready since 2026-08-01, never actually dispatched)
      Source: `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` — ✅ **DONE 2026-08-14
      (slot 11, infra).** `ce:GetCostAndUsage`/`GetCostAndUsageWithResources` are DENIED for this worker's AWS identity
      (`ikenna-worker`, not the self-service `uts-orchestrator-epic-role` — confirmed no IAM self-manage/AssumeRole
      path either, so not self-fixable per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`) — a
      pre-documented, non-blocking drift (`billing-cost-observability.md` already notes `ce:*` DENIED for this exact
      identity, verified 2026-07-08). Used the real replacement path that doc names: the AWS CUR→Athena billing stack
      (`aws_billing.cur_uts_cost_usage`, workgroup `uts-billing`, region `us-east-1`) — same live data Cost Explorer
      would have shown, already provisioned for exactly this purpose. Confirmed `i-0c9b283b31d6b5ca7` (EIP
      `13.113.200.22`) is the CI/AO host in question. Queried real `BoxUsage` line items (`line_item_resource_id LIKE
      '%i-0c9b283b31d6b5ca7%'`) for 2026-07-27→2026-08-13 (last complete CUR day; today not yet delivered), grouped by
      day/usage-type/instance-type — 23 real billed rows, matching the archived
      `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md`'s independently-priced rate ($1.09368/hr
      `m8i.4xlarge` /
      $0.54684/hr `m8i.2xlarge`, ap-northeast-1) to 5 decimal places. **Real totals**: 394.97 instance-hours /
      **$374.41**
      BoxUsage spend across the full 07-27→08-13 window (91.4% uptime — gaps from the 08-07 stop/resize + 08-09
      type-change reboot). **Retry-storm-attributable slice**: the resize-up fix (m8i.2xlarge→m8i.4xlarge, applied
      2026-07-27, reverted 2026-08-07 per the rightsizing plan's downsize todo) ran 213.84h at m8i.4xlarge + 19.50h at a
      brief `c7i.4xlarge` experiment (07-28/07-29) + 30.18h at m8i.2xlarge (the partial days either side of the resize)
      = **$267.90 real spend over the 11-day 07-27→08-07 fix window**, vs a **$144.37** steady-state baseline (264h ×
      $0.54684/hr had it stayed at m8i.2xlarge the whole window) — **retry-storm-attributable extra AWS EC2 compute
      cost ≈ $123.53**
      (≈$11.23/day while active; not sustained — reverted after 11 days once the CI-runner-fleet-split
      absorbed the load). Side-by-side with this doc's existing GH-Actions-dollar figure (~$10
      / 3.5-day sample, ≈$90/mo if sustained): the AWS EC2 compute bucket was **>12x larger** in absolute $ terms over
      its active window, confirming the P2 finding's hypothesis that this was the bigger, previously-unquantified cost
      bucket. The 2026-08-09+ move to `c8i-flex.4xlarge` is a SEPARATE, later rightsizing/generation change (not
      retry-storm remediation) — excluded from the attributable figure. Reconciliation of this evidence back into the
      source issue doc's own checkbox is out of scope for this satellite batch (per this doc's own header) — deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`.
- [x] ✅ [CODE] P2. investigate the real cause of the 2026-07-30 14:54-15:01Z mass tmux_session_lost cluster via the
      doc's own named candidates (a/b/c: cgroup/systemd action, manual/scripted kill, AWS-side event) now that the
      OOM-killer hypothesis is ruled out Source:
      `plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` — ✅ **DONE 2026-08-14 (slot 6,
      infra).** Verdict: candidate (a), system-wide thread/PID exhaustion (NOT memory — distinct from the
      already-ruled-out kernel OOM-killer). (b) manual/scripted kill and (c) AWS-side event both directly ruled out via
      CloudTrail/CloudWatch/auth.log evidence. Full timeline + log excerpts in the source doc's Progress Log (2026-08-14
      entry) and its own todo checkbox (now flipped). No code change — a forensic finding, not a fix; the mitigation
      (host thread-headroom / QG governor live-admission cutover) is already tracked separately in
      `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md`.
- [x] ✅ [CODE] P2. Hold/confirm a clean 60-consecutive-minute zero-new-CI-alert window before closing the incident
      (worker-monitorable, outcome-determinable, same shape as the AO-dispatched monitoring pattern used in the sibling
      pytest_timeout_60s doc) Source:
      `plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md` — ✅ **CONFIRMED CLEAN
      2026-08-14 (slot 26, infra), ~7 days elapsed, no code change.** No new occurrence of the incident's own signature
      (zombie `queued`/`cancelled` run with 0 jobs on `ldr-to-main-promote-fleet`/`ldr-to-main-promote`, or a
      `glue-pool-starvation-monitor` CRITICAL page) since the 2026-08-07 17:42Z fix — the last recurrence of the
      cancelled/zero-jobs signature was 2026-08-07T17:19:08Z (per the doc's own 2026-08-09 check), and live-reverified
      here (2026-08-14T02:05Z UTC): `gh api .../actions/runs?status=queued` shows zero currently-queued runs of either
      workflow; the last 10 `ldr-to-main-promote-fleet` runs (2026-08-14T00:29Z-02:00Z, mix of `schedule`+
      `workflow_dispatch`) are all `conclusion=success`. `glue-pool-starvation-monitor` has not run since
      2026-08-08T08:30:59Z (its `schedule:` trigger is now deliberately commented out in
      `.github/workflows/glue-pool-starvation-monitor.yml` — no self-hosted `glue` pool left to starve — not a
      monitoring gap). Scanned the live `ci-failures` Slack channel 2026-08-13T09:00Z→2026-08-14T02:01Z (30 most recent
      messages): zero hits for either signature; every message in that window is unrelated routine fleet noise (QG-slice
      failures, LDR-CI-red transitions, cloud-build fallbacks, provenance-gate blocks, branch-health lag) — a much
      higher-frequency, always-on alert class this todo's own bar was never meant to gate on (the source doc's "check
      for and cancel any pre-existing queued run" mitigation text scopes the "60 consecutive minutes... zero new CI
      alerts" bar to THIS incident's own recurrence, not literal channel silence, which this repo's steady fleet-wide CI
      volume never reaches). Confirmed the two `[~]` P2 monitor-hardening todos in the source doc are also already
      SHIPPED in code (checkbox stale, not touched here — cross-doc reconciliation is this batch's paired finalize
      plan's job): `promote-fleet-startup-failure-monitor` queued-threshold hardening (unified-trading-pm@c526128fb0 +
      unified-trading-pm@ff435d5b53) and `glue-runner-crash-loop-watchdog` busy-status hardening
      (unified-trading-pm@e0901407f2). **Verdict: the 60-min clean-window bar is met — exceeded ~168x over**; closing
      this todo is worker-determinable per the evidence above, no operator judgment call needed. Reconciling this back
      into the source issue doc's own "Blocking the 60-min clean-window bar" checkbox is out of scope for this satellite
      batch (per this doc's own header) — deferred to `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`.
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
