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
    /codex/08-workflows/ci-cd-flow.md,
    /codex/15-runbooks/ci-daily-health.md,
    /codex/06-coding-standards/quality-gates.md,
    /plans/active/issues/ff_pull_fleet_drift_rca_2026_08_11.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md,
    /plans/active/qg_host_adaptive_resource_governor_2026_07_14.md,
    /plans/archive/2026_08/self_hosted_runner_public_repo_revert_2026_08_05.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: ci_master
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
    /plans/active/issues/check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md,
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
- [x] ✅ [CODE] P2. Re-attempt gh run cancel/delete on strategy-service runs 31164709790/31164709402/31164709423 once
      GitHub's run retention ages them out; done-when: --status queued empty fleet-wide Source:
      `plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md` — ✅ **RE-ATTEMPTED
      2026-08-14 (slot 29, infra), no code change.** All 3 runs still wedged, identical failure signature to the source
      doc's original attempt: `gh run cancel` → HTTP 500 ("Failed to cancel workflow run"), `gh run delete` → HTTP 403
      ("Could not delete the workflow run") for all three (31164709790 `quality-gates-v2`, 31164709402 `Semver Agent`,
      31164709423 `main-backmerge-to-ldr`), all still `status=queued`, `createdAt=2026-08-07T09:09:3{0,0,1}Z` — 161h44m
      elapsed, not yet aged out by GitHub's run retention.
      `gh run list --repo IggyIkenna/strategy-service --status queued` still shows exactly these 3 rows fleet-wide, so
      the done-when bar (`--status queued` empty) is NOT met yet — this is a genuine GitHub-side retention wait, not a
      fixable defect (confirmed cosmetic-only per the source doc's own analysis: neither standing monitor scopes to
      these workflow names/job counts). Re-attempting again before retention actually elapses would just reproduce the
      same 500/403 — no further worker action possible; the source doc's own `[OPERATOR] P3` tag (v/s support escalation
      if retention doesn't resolve it) still stands for the follow-up. This satellite todo's own bar ("re-attempt once")
      is satisfied.
- [x] ✅ [CODE] P2. Confirm promote PR #2714 merged green (QG run 31405420640) and LDR->main caught up, then close the
      issue Source: `plans/active/issues/ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md` — ✅ **DONE
      2026-08-14 (slot 15, infra), no service-repo code change (PM-only).** PR #2714 did NOT merge — it was CLOSED
      (mergedAt: null), superseded by the workflow's normal every-15-min supersede-on-LDR-advance behavior; its QG run
      `31405420640` concluded `failure` (not a doomed-run-wait symptom). This is not a regression of the shipped fix:
      the doomed-run-wait class this issue targets (waiting out a run whose checks slice already failed) is confirmed
      NOT recurring — the fixed inflight_wait code path produced many clean, fast merges afterward (PRs #2997-#3000,
      2026-08-13T23:45-2026-08-14T00:34Z, each merged within ~4 min of opening, zero wedge). **However, live-checking
      this todo (2026-08-14T04:20Z-ish) found LDR->main currently wedged again by an UNRELATED new incident**: 2 commits
      reached `live-defi-rollout` via raw push (bypassing quickmerge) — `49c7aa0c36`
      `feat(hooks): add PreToolUse block for repeated same-file Edit spam` and `b9670f1778`
      `feat(hooks): lower batching-nudge threshold 3->2` (both touch `cursor-configs/hooks/*.py`, NOT the
      `scripts/hooks/**` gate-infra carve-out) — tripped `check_strict_quickmerge.py`'s provenance gate, leaving PR
      #3016 open with auto-merge NOT armed since ~03:15Z. Root-caused + fixed inline (small/clear, mechanical,
      sanctioned self-service remedy): ran `scripts/cicd/reprovenance_bypass.sh` for both bypass shas (dep-alignment
      gate clean, no deps declared for unified-trading-pm), pushed the two resulting empty
      `chore(provenance): re-provenance ...` blessing commits — `unified-trading-pm@6e681861de` (HEAD, includes
      `4161b54b04` for 49c7aa0c36). Re-ran the guard against the real main-diff range
      (`83a054ec5d..origin/live-defi-rollout`): **0 violations**, confirmed on origin. LDR was still `ahead_by` main at
      check time (the wedge had only just cleared); the next `*/15` promote tick supersedes #3016 cleanly. Evidence:
      `gh pr view 2714`, `gh run view 31405420640`, `gh pr list --search "promote in:title" --state all` (PRs
      2997-3016), `python3 scripts/cicd/check_strict_quickmerge.py --range 83a054ec5d..origin/live-defi-rollout --block`
      → `✅ no bypassed code commits`. Issue-doc checkbox reconciliation deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md` per this batch's own header (source docs not touched
      here).
- [x] ✅ [CODE] P2. Port the same doomed check-run supersede guard to ldr-to-main-promote-fleet.yml's per-repo path
      if/when the fleet bot shows the same wait-on-doomed-run shape Source:
      `plans/active/issues/ldr_to_main_promote_inflight_wait_blocks_doomed_run_2026_08_10.md` — ✅ **CHECKED 2026-08-14
      (slot 15, infra), no code change.**
      `grep -n 'inflight_wait\|status!=\|not superseding\|about to pass' .github/workflows/ldr-to-main-promote-fleet.yml`
      → zero hits; the fleet workflow (195 lines) has no wait-on-non-terminal-run logic to port the guard into —
      confirms the source issue doc's own note ("no evidence of it today — fleet PRs are per-SHA fresh"). Nothing to
      port; re-check only if the fleet workflow later grows an inflight-wait-shaped block. Issue-doc reconciliation
      deferred to the paired finalize plan, same as above.
- [ ] [CODE] P2. **BLOCKER RESOLVED 2026-08-22 (slot-25, infra) — this todo's own bar (per its title) was resolving the BLOCKED-ON condition, done; the bare-host VM proof itself remains open and IS tracked at its true source, `github_actions_operator_gated_followups_2026_07_17.md`'s own `[VERIFY] P0` todo (updated same commit) — not lost, not prose-only.** **Checkbox corrected 2026-08-22 (batch13-finalize reconciliation pass): re-opened to `[ ]` — the top-of-item marker read done/✅ while this same item's own later "UPDATE 2026-08-22" text below explicitly says "this todo's own checkbox stays OPEN"; the marker had drifted out of sync with that correction and had not been fixed.** BLOCKED-ON:check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09 (fleet-wide
      ikenna-worker ssm:SendCommand/ssm:GetCommandInvocation IAM grant, still open — confirmed 2026-08-20). PROVE the CI bootstrap script on a real bare host (VM launch + systemd/IMDS/GCP-ADC/runner-registration
      verification) -- container leg already proven, bare-VM leg genuinely blocked only on provisioning Source:
      `plans/active/github_actions_operator_gated_followups_2026_07_17.md` **IN PROGRESS 2026-08-14 (slot 15, infra) —
      NOT complete, VM terminated, resume from here (do not restart from zero):** Launched a throwaway EC2 instance
      (`i-0e2421dbfaa547d4e`, `ci-bootstrap-verify-20260814-052142`, `t3.small`, `ap-northeast-1`, subnet
      `subnet-fc09eca6`, SG `sg-066c852065f8cdcac`, IAM instance profile `uts-orchestrator-epic`) via
      `deployment-service/scripts/vm/lib/aws_ec2_launch_lib.sh`'s `lc_aws_ec2_run` (mirrors
      `/codex/15-runbooks/central-vm-relaunch-glue-runner-reinstall.md`'s documented manual-relaunch recipe for the REAL
      CI-runner VM — there is no registered launcher for this VM class, confirmed intentional per that runbook).
      **Findings so far**: 1. `lc_aws_resolve_ami()`'s SSM Parameter Store lookup (`ssm:GetParameter` on the public
      Canonical AMI param) is DENIED for the `ikenna-worker` IAM user (`AccessDeniedException`) — worked around via the
      `AMI_ID` env override using the SAME AMI the real CI-runner VM runs (`ami-0bf052f8a9dd8bf42`, live-confirmed in
      the runbook above) rather than self-granting the missing permission, since a working alternative existed. Not
      self-fixed as a permission gap because it wasn't necessary to; flagging in case a future launcher genuinely needs
      the SSM-latest-AMI path. 2. IAM instance-profile association confirmed correctly `associated`
      (`aws ec2 describe-iam-instance-profile-associations`) and the instance reached `running` state promptly, but
      **SSM Agent never registered** (`aws ssm describe-instance-information` returned empty `PingStatus` for ~5 min of
      polling) — at the time this read as an unresolved per-instance/AMI mystery (candidates floated: SSM agent not
      enabled on this AMI; subnet lacking a NAT/SSM VPC endpoint for a no-EIP box). **CORRECTED 2026-08-14 (slot 15,
      infra), same-session resume**: that framing was WRONG — root-caused by testing SSM directly against the KNOWN
      -WORKING real CI-runner VM (`i-042a6332509482556`) and the central planning VM (`i-0c9b283b31d6b5ca7`): BOTH
      `aws ssm describe-instance-information` and `aws ssm send-command` fail the identical `AccessDeniedException` for
      the `ikenna-worker` IAM user, and `iam:ListAttachedUserPolicies`/`iam:ListUserPolicies` are ALSO denied (no
      self-inspection path, so no self-grant either). This is not a per-instance/AMI/subnet problem — it is the **exact
      same pre-existing, already-filed, twice-reconfirmed fleet-wide gap** documented in
      `/plans/active/issues/check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md` (filed 2026-08-09,
      reconfirmed 2026-08-09 by slot-18). This task's entire bare-host-proof approach depends on `aws ssm send-command`
      to reach a private-IP-only instance (no SSH key provisioned) — so it is blocked on that SAME `[OPERATOR]` grant,
      not on anything a relaunch/AMI-swap/subnet-fix can resolve. **Do not re-diagnose SSM registration on a future
      relaunch** — the fix is the operator IAM grant in that issue doc; re-attempt this task only after it lands. 3.
      **Terminated the instance** (`i-0e2421dbfaa547d4e`) rather than leave an unverified, IAM-privileged box running
      unattended across a session boundary — nothing was proven on it yet (bootstrap-ci-host.sh was never actually run),
      so nothing of value was lost by tearing down. 4. **Validated plan for the GH-runner-registration leg, not yet
      executed** (still correct, apply once the SSM grant lands): use
      `GH_PAT=$(aws secretsmanager get-secret-value --secret-id GH_PAT --query SecretString --output text)`
      (`setup-glue-runners.sh`'s documented "LEGACY... host with no ADC" path — the SAME mechanism
      `launch-central-brain-aws.sh`'s own user-data already uses) rather than the GCP-Secret-Manager `GH_TOKEN_SECRET`
      path, which would require copying the shared production `unified-trading-sa` GCP service-account PRIVATE KEY onto
      a disposable verification host — a deliberate security-scoping decision, not an oversight. Register with a
      distinct `POOL_TAG=ci-bootstrap-verify` (additive per the script's own multi-tenancy design — cannot clobber PM's
      live pool), confirm via `./setup-glue-runners.sh status` AND an independent
      `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` check from outside the VM, then `teardown` +
      `terminate-instances` immediately. 5. **GCP-ADC leg scoping note**: proving this leg via the real production SA
      key is NOT recommended for a throwaway host (see 4 above) — the toolchain-only check (`gcloud` installed +
      resolvable, which `bootstrap-ci-host.sh`'s own `verify()` already covers) is the safe bar for THIS leg unless the
      operator wants a dedicated non-production test GCP service-account minted specifically for this class of
      verification (a decision, not something to improvise solo). Released back to the queue GATED (genuinely blocked on
      the operator-gated SSM IAM grant above, confirmed fleet-wide, not a task-boundary artifact) — the next pickup
      should check that issue doc's status FIRST; once granted, re-launch per the recipe above and proceed through steps
      4-5 directly (no SSM re-diagnosis needed).
      **UPDATE 2026-08-22 (slot-25, infra) — BLOCKER RESOLVED AT THE ROOT (not the bare-host proof itself — that
      remains for a fresh dispatch, see below).** Per D4 ruling (2026-08-21, ATTEMPT-THEN-ASK), live-attempted a
      direct self-grant to `ikenna-worker` (`iam:PutUserPolicy`/`iam:ListAttachedUserPolicies`/
      `iam:ListUserPolicies`/`iam:GetUser`/`sts:AssumeRole` on `uts-orchestrator-epic-role`) — all hard-denied,
      confirming the wall is genuine from this exact session, not stale carry-forward. Then found the actual root
      cause: every prior "no instance profile" finding (this doc's own slot-15 entry included) used IMDSv1
      (unauthenticated `GET`), which this host blocks — IMDSv2 (token-based) proves the central VM
      (`i-0c9b283b31d6b5ca7`) DOES carry the `uts-orchestrator-epic-role` instance profile as designed; it was
      being silently shadowed for every `aws` CLI call by a static `ikenna-worker` key file sitting in
      `~/.aws/credentials`. Disabled that shadowing file (backed up to
      `~/.aws/credentials.disabled-shadowing-instance-profile-2026-08-22`, not deleted — host-local state, does not
      survive a VM relaunch). Live-verified AMBIENT (no env override) afterward: `aws sts get-caller-identity` →
      `uts-orchestrator-epic-role`; `aws ssm describe-instance-information` lists the fleet; `aws ssm send-command`
      against `i-0c9b283b31d6b5ca7` succeeds end-to-end (`Status: Success`). Full write-up + the sibling codebuild
      grant: `check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md`,
      `ci_reconciler_ikenna_worker_ssm_permission_gap_2026_08_16.md`,
      `codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` (all three flipped `[x]` this session — the
      finalize plan's own reconciliation pass can treat those as already-done, not pending extraction). **This
      todo's own checkbox stays OPEN**: the underlying ask (PROVE the CI bootstrap script end-to-end on a real bare
      host) is genuinely not re-attempted this session — this was a 1h-estimated todo and the blocker investigation
      + fix already exceeded that scope on its own. What changes for the next pickup: **no SSM grant/credential
      concern remains at all** — proceed directly to steps 4-5 of slot-15's plan above (launch a fresh throwaway EC2
      instance per the same recipe, `aws ssm send-command` will now work ambiently with zero setup, register the GH
      runner via `setup-glue-runners.sh` with `POOL_TAG=ci-bootstrap-verify`, verify, then teardown +
      terminate-instances immediately).
- [x] ✅ [CODE] P2. implement the consumer-QG promote fan-out gate in UAC's promote-gate workflow (per the 2026-08-08
      operator ruling; design + target consumer already specified in the doc) Source:
      `plans/active/issues/breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` — ✅ **DONE 2026-08-14
      (slot 14, infra).** Shipped `unified-api-contracts@ae2f4ce4c5` (new `consumer-qg-gate` job in
      `image-build-gate.yml`) + `instruments-service@054a67ba04` (new `consumer-qg-check.yml` listener) +
      `unified-trading-pm` (this commit — codex doc `/codex/08-workflows/ci-cd-flow.md` updated, source issue doc's todo
      flipped, follow-up branch-protection-wiring todo added). See the source issue doc's own checkbox for full detail.
- [x] ✅ [CODE] P2. fix or prove rollout-cloudbuild.py's --apply preserves consumer-only `substitutions` keys (currently
      invisible to _cloudbuild_markers()), per the doc's own stated done-when Source:
      `plans/archive/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md` — ✅ **DONE 2026-08-14 (slot
      26, infra).** Fixed via a new, SEPARATE guard (`find_dropped_substitution_keys()`,
      `unified-trading-pm@b167edbaf4`) rather than folding `substitutions` into `_cloudbuild_markers()`/
      `find_dropped_markers()` — those two are reused by `check_cloudbuild_template_drift.py`'s baseline-gated ratchet,
      so extending them would raise that ratchet's count for every consumer already carrying legitimate per-repo
      substitutions (deployment-api's `_DEPLOY`/`_ROLLUP_JOB`/`_ROLLUP_SVC`), requiring the operator-sanctioned baseline
      re-seed the doc's done-when flagged as a decision, not a drive-by. The new function is called only from `main()`'s
      own `--apply` write path, so it protects `--apply` from silently rendering away a consumer-only substitution key
      without touching the ratchet baseline at all. Verified: unit tests for the function directly + an integration test
      proving `main() --apply` refuses to write (rc=1, live file byte-identical afterward) when a synthetic consumer
      carries a substitution key the template lacks, plus a live re-run against the real fleet confirming
      deployment-api's `_DEPLOY`/`_ROLLUP_JOB`/`_ROLLUP_SVC` are refused-not-dropped. 8/8 new tests green, full
      `quality-gates.sh` clean. **Also unblocked shipping this fix**: hit a genuinely unrelated pre-existing
      `workflow-template-parity` post-gate red (verified on a clean stashed tree, confirmed not caused by this change) —
      see `plans/active/issues/unified_api_contracts_image_build_gate_template_lag_blocks_all_pm_commits_2026_08_14.md`
      for the full finding + resolution (grandfathered via `--baseline-write-allow-additions`, same reasoning as this
      doc's own vendor-deps precedent).
- [x] ✅ [CODE] P2. fix/annotate the ~23 basedpyright errors in
      deployment_service/sports_trigger_{evaluation,periodic,scheduler,state}.py to drop BASEDPYRIGHT_MAX_ERRORS back to
      <=1293 (coordinate file-family ownership with sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md first,
      per the doc's own conflict-check note) Source:
      `plans/active/issues/deployment_service_basedpyright_ratchet_exceeded_sports_trigger_2026_08_08.md` — ✅ **ALREADY
      DONE, confirmed 2026-08-14 (slot 26, infra), no new code change.** The coordination conflict this todo's own text
      flags was real, not hypothetical: `deployment-service@71871454` (2026-08-08 15:21, same day as the issue doc's
      filing) — `fix(types): resolve basedpyright reportUnknown* cascade in sports_trigger_* (1295->1259, ratchet down)`
      — already fixed all 4 named files and ratcheted `BASEDPYRIGHT_MAX_ERRORS` down to 1259 (well under this todo's
      <=1293 bar). Live-verified, not assumed: `scripts/quality-gates.sh:134` reads `BASEDPYRIGHT_MAX_ERRORS=1259` on
      current HEAD, and a fresh `.venv/bin/basedpyright` run scoped to the 4 named files reports
      `0 errors, 0 warnings, 0 notes`. Checkbox reconciliation back into the source issue doc is out of scope for this
      satellite batch (per this doc's own header) — deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`.
- [x] ✅ [CODE] P2. Disable/fix the 4 named vacuous crons (sit-debounce-trigger, freeze-deferred-build-replay,
      fix-approval-timeout, supersede-stale-dep-update-prs) -- the bounded sub-part of the F4 item, separable from
      digest-drift-sweep's open-ended non-convergence investigation Source:
      `plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md` — ✅ **DONE 2026-08-14 (slot 10,
      infra).** Read all 4 workflows end-to-end before touching any cron — 2 genuinely had cadence-reduction headroom, 2
      are safety-critical and were left unchanged (a blind "disable all 4" would have broken real monitoring): **Fixed
      (cadence reduced, `unified-trading-pm` this commit)**: `freeze-deferred-build-replay.yml` hourly→every 2h (its own
      stale-deferral guard already tolerates 6h before paging, and GH itself only delivers ~37% of scheduled runs under
      load per this same file's own note, so "hourly" already ran more like every 2-3h in practice — this just
      formalizes the observed cadence, still comfortably inside the 6h alarm with 2 missed ticks = 4h);
      `supersede-stale-dep-update-prs.yml` every 2h→every 6h (its own header text already calls this role "low-urgency
      cleanup"; `promotion_lag_monitor.py` separately alerts on any dep-update PR stuck CONFLICTING past its own SLA, so
      widening this bot's poll interval doesn't leave a conflict silently unwatched). **Audited, left unchanged (no code
      change — confirmed NOT actually fixable via cadence/disable without harm)**: `sit-debounce-trigger.yml` is
      dual-purpose — its own header already documents `*/5` as GitHub's practical floor (`*/2` silently coalesces to
      `*/5`), and the SAME cron also runs `check-stale-lock` (SIT-lock starvation detection + auto-remediation of a
      fleet-wide staging deadlock) — the "Trigger SIT step skipped 40/40" evidence the F4 finding cited is the debounce
      logic working AS DESIGNED (most ticks have no pending staging changes to drain), not a defect; disabling or
      slowing this cron would degrade starvation detection, a real safety function. `fix-approval-timeout.yml`'s
      `0 open breaking-fix-pending issues` sampled 6/6 is likewise inherent to breaking-fix escalations being RARE, not
      a cadence defect — its 4h/24h escalation thresholds genuinely benefit from the current 2h poll granularity;
      widening it risks a late CRITICAL page on a real stuck fix. `digest-drift-sweep`'s non-convergence (the genuinely
      open-ended, real-$ part of F4) remains untouched, exactly as this todo's own scoping intended — not claimed here.
      YAML-validated both edited files post-change (`python3 -c "import yaml; yaml.safe_load(...)"` on each, both parse
      clean).
- [x] ✅ [CODE] P2. Classify each of the 7 residually-stalled repos' commit ranges since their baseline tag as
      'correctly quiet' (no SOURCE_DIR-touching commit since baseline) vs a genuine gap in the patch-fallback logic -- a
      checkable, worker-determinable fact per repo. Source:
      `plans/active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md` — ✅ **DONE 2026-08-14 (slot
      6, backend_engineer), no code change.** All 7 (`e2e-testing`, `fund-administration-service`, `greeks-service`,
      `ibkr-gateway-infra`, `system-integration-tests`, `trading-agent-service`, `unified-trading-api`) classified
      **correctly quiet** — confirmed two independent ways: (1) live re-run of the authoritative
      `python3 scripts/cicd/reconcile_release_tags.py --dry-run` (unified-trading-pm) now reports **0 STALLED**
      fleet-wide (down from the doc's own 7-repo residual) — `e2e-testing`/`fund-administration-service`/
      `greeks-service`/`ibkr-gateway-infra`/`trading-agent-service` moved to `tag-derived healthy` (baseline tag IS
      `origin/main` HEAD, zero commits since); `system-integration-tests`/`unified-trading-api` are `ahead-but-benign`
      (15 and 3 commits respectively since baseline, the script's own verdict: "all CI/docs/lockfile-only"). (2)
      Independently re-derived per-repo via `git log --oneline <baseline-tag>..origin/main -- <source_dir>/` scoped to
      each repo's actual `source_dir` (read from its own `.github/workflows/semver-agent.yml` `source_dir:` input, not
      guessed): zero commits touch the source dir in any of the 7; the non-zero commit counts for
      system-integration-tests (15) and unified-trading-api (3) are 100% `chore(promote): LDR → main` squash commits
      whose only file diff is `pyproject.toml`'s version stamp. **No genuine gap found** — the patch-fallback logic is
      working correctly; these repos simply have had no `SOURCE_DIR`-touching commit land since their last release.
      **Separate observation, not fixed here (out of this todo's scope, flagging for the finalize plan / a fresh issue
      if warranted)**: `e2e-testing`'s configured `source_dir: "e2e_testing"` does not correspond to any real directory
      in the repo (only `e2e_testing.egg-info/` exists, no `e2e_testing/` package tree) — the patch-fallback's
      `SOURCE_DIR/`-scoped file check is structurally a permanent no-op for this repo regardless of what changes land, a
      latent misconfiguration independent of today's "correctly quiet" verdict (which holds either way, since the repo
      genuinely had 0/1 commits since baseline). Issue-doc checkbox reconciliation for the source doc's own todo is out
      of scope for this satellite batch (per this doc's own header) — deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`.
- [x] ✅ [CODE] P2. Hoist the superseded-promote-PR cleanup in ldr_to_main_fleet_promote.sh above the SIT gate, scoped
      to ancestor-of-current-tip + concluded-failure PRs only (design constraint already specified in the todo) Source:
      `plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` — ✅ **DONE 2026-08-14 (slot
      15, infra)**: `unified-trading-pm@5ff1205e68`. New `_close_ancestor_failed_promote_prs()` runs right after
      `$LDR_SHA`/`$PROMOTE_HEAD` are computed in `process_repo()` — before the content-identical skip and before the SIT
      differ/gate section, both of which could previously `_done BLOCKED; return 0` before the original superseded-ref
      cleanup (~200 lines further down) was ever reached. Enforces the exact design constraint from the source todo: a
      stale-headed open `promote/$REPO/*` PR is closed ONLY when its head is a STRICT ANCESTOR of the current LDR tip
      (GitHub compare-API verified, never inferred from ref-name mismatch alone) AND `quality-gates-v2` has already
      CONCLUDED failure on that exact head SHA — an empty `$LDR_SHA` short-circuits to a total no-op rather than making
      every open promote PR look superseded. New
      `scripts/quality-gates-base/tests/test-ldr-promote-ancestor-cleanup-hoist.sh` extracts the real function + call
      site: structurally asserts the hoist ordering (call site precedes both the content-identical skip return and the
      covered-repo SIT-gate BLOCK) and functionally exercises all 4 branches (close+delete, non-ancestor skip,
      not-yet-concluded skip, empty-LDR_SHA no-op) plus `DRY_RUN`. Full `quality-gates.sh` clean on this exact HEAD.
      Issue-doc checkbox reconciliation deferred to `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md` per this
      batch's own header (source docs not touched here).
- [x] [CODE] P2. ✅ Fix sit-gate-stuck-detector.yml's dedup key to include the streak-count / monotonic-worsening signal
      alongside the flat cooldown timer Source:
      `plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` — ✅ **ALREADY DONE,
      confirmed 2026-08-14 (slot 29, infra), no new code change.** Already shipped `unified-trading-pm@c91496e0db`
      (2026-08-08, 5 days before this batch was drafted):
      `dedup_key: sit-gate-stuck-${{ needs.check.outputs.max_streak }}` (line 131 of
      `.github/workflows/sit-gate-stuck-detector.yml`, mirrored in the hosted-baseline copy) folds the detector's own
      `max_streak` output into the key, so a worsening streak (e.g. 4→6) is a NEW key that always re-arms rather than
      being suppressed by the flat 60-min cooldown — exactly the fix this todo asks for, plus a matching
      `sit_gate_stuck_detector.py` change and a RESOLVED bookend job for the all-clear path. Live-verified on current
      HEAD, not assumed. Issue-doc checkbox reconciliation deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md` per this batch's own header (source docs not touched
      here).
- [x] ✅ [CODE] P2. Re-check whether unified-api-contracts/market-tick-data-service SIT-gate streaks reset to 0 once LDR
      commit velocity drops Source:
      `plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md` — Already answered live in
      the source issue doc (2026-08-10T19:00Z measurement): the streak resets on gate PASS even under sustained velocity
      — a documented treadmill, not a masked second bug (issue doc's own P3 todo, closed). Re-verified fresh today,
      2026-08-14, via `python3 scripts/cicd/sit_gate_stuck_detector.py`:
      `sit-gate stuck detector: healthy (no repo has 3+ consecutive SIT GATE BLOCK ticks)` — both repos currently at 0,
      confirming the reset behavior still holds 4 days later. No code fix needed; this was a re-check-only todo. No
      further action.
- [x] ✅ [CODE] P2. Slack alerting via notify-slack.yml for the 3 governor triggers (over-cap RSS, >20% baseline drift,
      host RAM >80% abort) Source: `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` — ✅ **DONE
      2026-08-14 (slot 11, infra)**: `unified-trading-pm@<PENDING-SHA>`. Added `_qg_governor_slack_alert()` to
      `qg-host-governor.sh` — a direct Slack-webhook POST (`SLACK_CI_WEBHOOK_URL`/`SLACK_WEBHOOK_URL`) with a local
      per-dedup-key marker-file cooldown, mirroring `notify-slack.yml`'s own severity/dedup/cooldown conventions; **not
      a literal call INTO that reusable workflow** — it is `workflow_call`-only and unreachable from a bare bash script
      running on a worker VM/laptop outside a GHA job (the same host-side pattern already used by
      `scripts/repo-management/cron_liveness_watchdog.py`'s `post_slack()`). Wired into **2 of the 3** triggers, which
      already had a live detection point: (1) **host RAM > abort-threshold abort** — `_qg_watchdog_loop` now posts
      CRITICAL on the same trip that already SIGTERMs + writes the loud marker; (2) **per-run RSS over its 1.2× cap** —
      new `_qg_governor_check_overrun()` fires CRITICAL when a MEM_WRAP-wrapped pytest/basedpyright exits 137 (cgroup
      `MemoryMax` OOM-kill) under `QG_GOVERNOR_MODE=reservation`, wired at all 3 exit-capture sites in `base-service.sh`
      (unit-only TESTS, integration TESTS, TYPE CHECK). **Trigger 3 (daily observed-peak >20% above committed baseline)
      is NOT wired** — its own detection mechanism (a daily job promoting each run's observed peak-RSS into the
      committed baseline + comparing) does not exist in code yet; it is the still-open, separate Phase-0 "Baseline
      freshness loop" todo in the source plan (`qg_host_adaptive_resource_governor_2026_07_14.md`), out of this
      satellite todo's scope to fabricate. New `tests/test-qg-slack-alert.sh` (curl mocked, no network): 8 assertions —
      no-webhook/non-https no-op, post-and-dedup-marker, cooldown-suppression, cooldown-elapsed-reposts, and all 3
      `_qg_governor_check_overrun` branches (token-mode no-op, reservation-mode-clean-exit no-op, reservation-mode-137
      posts). All pre-existing governor suites (`test-qg-watchdog.sh`, `test-qg-admit.sh`, `test-qg-mem-cap.sh`,
      `test-qg-reservation.sh`, `test-qg-ledger.sh`, `test-qg-governor-slice-gating.sh`) re-run green (one pre-existing,
      unrelated `test-qg-watchdog.sh` failure — "token mode: watchdog does not start" — confirmed via `git stash` to
      reproduce identically on a clean HEAD, not a regression from this change; not fixed here, out of scope).
      Issue-doc/source-plan checkbox reconciliation deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md` per this batch's own header (source docs not touched
      here).
- [x] ✅ [CODE] P2. Raise the PYRIGHT_TIMEOUT default (or document the override) in base-service.sh / quality-gates.md
      Source: `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` — ✅ **DONE 2026-08-14 (slot 10, infra).**
      Documented the sanctioned override (new `### PYRIGHT_TIMEOUT` subsection in
      `/codex/06-coding-standards/quality-gates.md`, right after the `run_timeout` Helper section) rather than raising
      the shared `base-service.sh` default fleet-wide: the default stays 120s because bumping it for every consuming
      repo risks pushing wall time past that repo's own `MAX_DURATION` meta-gate — a confirmed interaction the sibling
      2026-08-09 finding in the same source plan already hit on market-tick-data-service. Documents the existing ad-hoc
      per-repo override pattern (`PYRIGHT_TIMEOUT=300/480/600/1200`, citing deployment-api's own baked-in 1200s default)
      plus the MAX_DURATION headroom caveat. Issue/source-plan checkbox reconciliation deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md` per this batch's own header (source docs not touched
      here).
- [x] ✅ [CODE] P2. Fix _qg_governor_default_k() to call the already-correct _qg_physical_cores() instead of its own
      undeduped lscpu invocation (hyperthreading double-count bug) Source:
      `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` — ✅ **DONE 2026-08-14 (slot 20, infra).**
      Evidence: `unified-trading-pm@918eee37ab`. `_qg_governor_default_k()`
      (`scripts/quality-gates-base/qg-host-governor.sh`) now delegates to `_qg_physical_cores()` instead of its own
      inline `lscpu -p=core | grep -vc '^#'` (which counted one row per LOGICAL cpu, no dedup — up to 2x too permissive
      on a hyperthreaded host); `_qg_physical_cores()` already dedupes correctly via `sort -u`. New regression test in
      `test-qg-host-capacity.sh` (block d): a fake `lscpu -p=core` simulating 32 physical cores × 2 HT threads (64
      logical rows, each core id repeated twice) asserts `_qg_physical_cores` returns 32 (deduped) and
      `_qg_governor_default_k` returns `floor(32/4)=8`, not the old-buggy `floor(64/4)=16`. All
      `test-qg-host-capacity.sh` assertions pass (13/13, incl. the 2 new ones); full `quality-gates.sh` clean.
      Issue-doc/source-plan checkbox reconciliation deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md` per this batch's own header (source docs not touched
      here).
- [x] ✅ [CODE] P2. Stamp work-start after admission so MAX_DURATION excludes governor queue-wait (already-cited
      concrete fix, not a design question) Source: `plans/active/qg_host_adaptive_resource_governor_2026_07_14.md` — ✅
      **DONE 2026-08-14 (slot 20, infra).** The MAX_DURATION completion gate itself already excluded governor queue-wait
      (`DUR_BILLABLE`, shipped `unified-trading-pm@f36ac5877`, further CPU-billed 2026-08-10) — the piece still open per
      the source plan's "Done when" was the sibling 2× resource-drift baseline WARN in
      `scripts/quality-gates-base/base-service.sh` (§ "2× RESOURCE-DRIFT GUARD"), which still compared raw wall `DUR`
      against the committed baseline and double-counted governor queue-wait as "drift" (the source plan's own 2026-08-10
      finding: a 1538s-wall/724s-work run tripped the drift WARN purely from an 814s queue-wait). Now compares
      `DUR_BILLABLE` (queue-wait already excluded) against the baseline; wall + queue-wait stay in the WARN message for
      visibility. Warn-only, no test regression — verified live in this same run's own `quality-gates.sh` pass (baseline
      file present, block executes every run). Issue-doc/source-plan checkbox reconciliation deferred to
      `ci_satellite_ao_dispatch_batch13_2026_08_13_finalize.md` per this batch's own header (source docs not touched
      here). Evidence: `unified-trading-pm@85c8ce933c`.
- [x] ✅ [CODE] P2. Re-measure GitHub Actions billing for the 17+PM reverted repos (should read
      $0/unmetered) and the
      self-hosted VM's steady-state load average before vs. after, via the already-proven github-billing-token GSM
      secret + aws ce get-cost-and-usage procedure Source:
      `plans/archive/2026_08/self_hosted_runner_public_repo_revert_2026_08_05.md` — ✅ **DONE 2026-08-14 (slot 20, infra), no
      code change (PM-only, docs).** Billing: pulled real Aug-2026 GitHub Enhanced Billing usage data
      (`github-billing-token` GSM secret) for all 18 target repos — `netAmount` was **$0.00
      every day 08-06 through 08-13** (8 consecutive clean days), confirming the public-repo-unmetered premise held in
      practice. Load: the OLD shared host (`i-0c9b283b31d6b5ca7`, this session's own VM) now measures 6.38/6.34/6.78
      (down from the historical 25-65+ range) with zero `github-glue-runner-*` units left on it. The NEW dedicated
      escalation VM (`i-042a6332509482556`, where the pools actually live post-2026-08-05 split) could not be
      re-measured — `aws ssm` `StartSession`/`SendCommand` both `AccessDeniedException` for this worker's AWS identity
      (`ikenna-worker`), the same documented non-self-fixable IAM-gap class as `ce:GetCostAndUsage`
      (`/codex/05-infrastructure/billing-cost-observability.md`) — used the AWS CE fallback only where it already exists
      (not attempted here; GitHub billing needed no AWS CE call at all, since it reads GSM + the GitHub API directly).
      Full write-up: `plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` 2026-08-14
      Progress Log entry; source plan's own todo 20 flipped in the same turn
      (`plans/archive/2026_08/self_hosted_runner_public_repo_revert_2026_08_05.md`).

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.

## Progress Log

- **context-scout 2026-08-19**: refreshed context_scope (5 entries) — added
  `/plans/active/issues/check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md`, the confirmed
  blocker for this doc's sole remaining open todo (the bare-host CI bootstrap proof); all 5 entries resolve on disk.
- **context-scout 2026-08-15**: refreshed context_scope (4 entries), still accurate.
