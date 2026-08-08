---
doc_type: issue
title: >-
  glue-pool-starvation-monitor CRITICAL-looped every ~30min for 6+ hours on 9 permanently-stranded jobs — a direct side
  effect of self_hosted_runner_public_repo_revert_2026_08_05.md's same-day PM runner retirement, not a new outage
summary: >-
  `#ci-failures` fired `glue-pool-starvation-monitor` CRITICAL repeatedly (every ~30m per its 60m cooldown, confirmed
  still firing as of 2026-08-07T18:17:30Z, run 31206264300) for 9 `glue`-labelled jobs queued 359m-394m with zero glue
  jobs in progress. Root cause: `unified-trading-pm@c8cd56251e` (self_hosted_runner_public_repo_revert_2026_08_05.md
  todo #24, landed on `main` ~11:23-11:38 UTC 2026-08-07) reverted PM's ~40 self-hosted-routed workflows to
  `ubuntu-latest` and stopped+disabled the `github-glue-runner@glue-{1..5}`/`writer-{1,2}` systemd units on the CI VM
  (`i-042a6332509482556`) — correctly and intentionally, since PM went public 2026-08-06 and
  self-hosted-on-a-public-repo is a fork-PR RCE exposure, not a cost saving. 9 jobs (check-and-write x2, Doc frontmatter
  gate (LDR), sweep, replay, check-and-trigger, check-stale-lock, Dispatch judgment wall to orchestrator, reconcile —
  plus 3 more `glue-writer`-labelled `update-ci-status` jobs the monitor deliberately excludes by design) had already
  been dispatched with the OLD `[self-hosted, glue]`/`[self-hosted, glue-writer]` label set moments BEFORE the revert
  commit landed on `main`. A workflow run's requested runner labels are frozen at dispatch time and do not hot-swap when
  the workflow file later changes on the branch (the identical failure class already found same-day in
  `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`), so these 12 jobs became permanently
  unclaimable the moment the pool that could have served them was (correctly) torn down. This was never a broken
  controller, a missing dedicated PM runner, or a regression in the revert itself — it is the revert's own predicted
  fallout, explicitly flagged as a followup in the revert plan's own Progress Log ("glue-pool-starvation-monitor.yml ...
  NOT touched ... flagged here for whoever next touches this plan to consider retiring for the same reason") but not yet
  acted on before this incident materialized.
status: open # both immediate items resolved + verified live below; 1 non-blocking P3 audit todo remains
nature: issue
asset_group: [ci, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, glue-runner, self-hosted-runner, monitoring-gap, false-alarm, promotion-blocked, slack-alerting]
related:
  [
    /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md,
    /plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md,
    /plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md,
    /plans/archive/issues/fleet_promoter_glue_runner_stall_2026_08_06.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: 2026-08-07
last_updated: "2026-08-07"
author: ikennaigboaka [interactive session]
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: devops
resolved_by: "unified-trading-pm (this issue doc's own commit — see Fix applied)"
locked_by:
locked_since:
source: >-
  Operator-dispatched investigation of a live, confirmed-firing #ci-failures CRITICAL alert
  (glue-pool-starvation-monitor, 2026-08-07); operator had already ruled out "0 runners registered" and traced the
  host's per-repo pool naming convention before dispatch.
drift_direction: advance-process
depends_on: []
context_scope:
  [
    /plans/active/self_hosted_runner_public_repo_revert_2026_08_05.md,
    .github/workflows/glue-pool-starvation-monitor.yml,
    .github/workflows/glue-runner-health-monitor.yml,
    scripts/cicd/glue_pool_starvation_monitor.py,
    scripts/self-hosted-runners/setup-glue-runners.sh,
  ]
---

# glue-pool-starvation-monitor false CRITICAL loop — stale pre-revert jobs, not a live outage

## Investigation (confirming the alert was genuine, then finding why)

- `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` → `{"total_count":0,"runners":[]}`, confirmed accurate:
  PM's own base (untagged) `github-glue-runner@glue-N`/`@writer-N` pool is real infrastructure
  (`scripts/self-hosted-runners/setup-glue-runners.sh`'s default, unsuffixed `POOL_TAG`) — **not** a provisioning gap.
  Every OTHER repo on the shared CI VM (`i-042a6332509482556`) gets its own `POOL_TAG`-suffixed pool
  (`github-glue-runner-<repo>@.service`, per `setup-glue-runners.sh`'s `POOL_TAG` mechanism, added 2026-07-17 for
  exactly this multi-tenant reason) — PM alone uses the BASE, unsuffixed template because PM is the pool's original/home
  repo. So "no `github-glue-runner-unified-trading-pm@.service` templated unit" is correct and by design, not evidence
  of anything missing.
- SSM into the CI VM (`i-042a6332509482556`) confirmed: `/etc/systemd/system/github-glue-runner@.service` (the base
  template) exists, `/opt/github-glue-runners/{glue-1..5,writer-1,writer-2}` exist with live runner installs, but **zero
  instances are currently loaded/active** — `systemctl status github-glue-runner@glue-1.service` showed
  `Loaded: ... disabled` / `Active: inactive (dead)`, restart counter frozen at 1401 (not incrementing despite
  `Restart=always`/`StartLimitIntervalSec=0` on the unit). `journalctl` for `glue-1`, `glue-2`, and `writer-1` all show
  an identical, simultaneous systemd `Stopping ...` action at **2026-08-07T11:38:14Z** — an EXPLICIT external stop (not
  a crash; `Restart=always` only stands down after a deliberate stop), matching the exact "coordinated multi-unit stop"
  signature already documented in `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`.
- Traced the stop to its actual, intentional cause (NOT a mystery this time):
  `self_hosted_runner_public_repo_revert_2026_08_05.md` todo #24, "Revert unified-trading-pm's own self-hosted workflows
  to ubuntu-latest — DONE 2026-08-07," shipped as `unified-trading-pm@c8cd56251e` (commit author date
  `2026-08-07T11:23:30Z`, landed on `main` shortly after — timing matches the 11:38:14Z stop within the same operational
  window). Its own commit message: _"PM went public 2026-08-06, making ubuntu-latest free/unmetered for it and
  self-hosted-on-a-public-repo a fork-PR security exposure instead of a savings."_ That todo's own text confirms:
  **"PM's 8 self-hosted runners deregistered from GitHub + systemd units stopped/disabled on the CI VM, confirmed
  inactive with no re-registration."** This is a deliberate, correct, already-completed security fix — **not** something
  to undo. Restarting the glue pool would re-introduce the exact fork-PR exposure the revert was built to close.
- Checked what was actually still queued: `gh api .../actions/runs?status=queued` + per-run `.../jobs` showed exactly 9
  `["self-hosted","glue"]`-labelled jobs (matching the alert's named list verbatim: check-and-write x2, Doc frontmatter
  gate (LDR), sweep, replay, check-and-trigger, check-stale-lock, Dispatch judgment wall to orchestrator, reconcile)
  plus 3 `["self-hosted","Linux","X64","glue-writer"]`-labelled `update-ci-status` jobs (excluded from the monitor's
  count by its own exact-label-membership design, `glue_pool_starvation_monitor.py`'s `is_glue_job()` — correct, not a
  bug). Confirmed on `main` (the ref that governs scheduled/dispatch workflow content) that every one of these workflow
  files now reads `runs-on: ubuntu-latest` — the revert genuinely landed clean, fleet-wide, for these files. The queued
  jobs' `runs-on` request is frozen at the moment each run was CREATED (before `c8cd56251e` propagated), and GitHub does
  not retroactively re-resolve a queued job's labels when the workflow file later changes on the branch — the identical
  mechanism (and identical fix) as `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`, found and
  fixed in this same repo earlier the same day.

## Fix applied

1. **Cancelled all 12 permanently-unclaimable stuck runs** (the 9 glue-labelled ones the monitor named + the 3
   glue-writer `update-ci-status` ones it doesn't count but were equally stranded): run IDs
   `31177650317, 31177458699, 31177410146, 31177229604, 31175892678, 31175451109, 31175390901, 31175233084` (glue) and
   `31177696729, 31177335848, 31176690757` (glue-writer), via `gh api -X POST .../actions/runs/<id>/cancel`. All 12
   confirmed `status: completed, conclusion: cancelled` within seconds; a fresh `actions/runs?status=queued` sweep
   afterward shows zero `glue`/`glue-writer`-labelled jobs remaining (only 5 unrelated ancient zombie runs from
   2026-05-15/2026-07-30 with **zero enumerated jobs** — outside this alert's scope and invisible to the monitor's
   job-label scan regardless).
2. **Disabled `glue-pool-starvation-monitor.yml`'s `schedule:` trigger**, mirroring the EXACT fix already applied the
   same day to the sibling `glue-runner-health-monitor.yml` (`unified-trading-pm@95cce3aa4`, same root cause, same plan)
   — kept `workflow_dispatch` live for any future manual check. With PM's `glue` pool permanently retired by design, a
   routine schedule tick can never again see a genuine starvation signal — only ever a stale pre-revert straggler like
   this incident, which would otherwise falsely CRITICAL forever on a condition that will never resolve on its own.
   Re-enable the schedule only if a self-hosted `glue` pool is ever deliberately re-established for this repo (per the
   added in-file comment).
3. **Did NOT touch the CI VM's systemd units** — the glue-N/writer-N pool being `stopped`/`disabled` is the correct,
   intentional, already-completed end state of the security revert; restarting it would be a regression, not a fix.

**Live-verified**: manually dispatched `glue-pool-starvation-monitor.yml` (run `31209430842`, `workflow_dispatch`,
2026-08-07T18:58:57Z) AFTER the cancellations — `check` job logged
`glue pool healthy: no 'glue'-labelled job queued > 20m while idle.` and the `notify` job was correctly `skipped` (only
runs when `starved == 'true'`). Contrast: the prior scheduled run 8 minutes earlier (`31208567219`, `18:47:29Z`, before
the cancellations took effect) DID run `notify` with conclusion `success` — i.e., it genuinely posted CRITICAL to Slack,
confirming the alert was live and firing right up until this fix, not a stale/already-resolved read.

## Recovery-announcement logic — checked, confirmed absent, not added (reasoning below)

`glue-pool-starvation-monitor.yml`'s `notify` job only ever fires `if: needs.check.outputs.starved == 'true'` — there is
no sibling `resolved`/`cleared` job and no `recovery: true` call anywhere in the file, unlike `branch-health.yml`'s
`lag-notify-resolved` job (state-diffed via a cached `.lag-state.json`, per-pair `cleared_key`, `recovery: true`,
`cooldown_min: 30`) or `overnight-dead-man-switch.yml`'s equivalent pattern. **Confirmed real gap**: if this monitor is
ever re-armed on schedule, the operator would see CRITICAL pages but never an explicit "back to healthy" bookend in
Slack — a starvation episode clearing silently reads exactly like "nobody's watching anymore," which is a real,
previously-identified operator concern (see the todo below). **Not added here**: a correct transition-only recovery post
needs the same prior-state-tracking approach `branch-health.yml` already uses (an `actions/cache`-restored "was-starved"
flag, diffed against the current tick, so a "resolved" message posts exactly once per clearing rather than spamming
every healthy tick forever) — that is a real, if modest, additional job

- state-cache, not a one-line change, and building it into a monitor whose `schedule:` this same fix is disabling (item
  2 above) would add code that will not run routinely going forward. The sibling `glue-runner-health-monitor.yml` fix
  earlier today (`95cce3aa4`) made the identical judgment call: disable the schedule, do not also add recovery logic to
  a monitor going dormant.

## Still open

- [ ] [INFRA] P3. Audit which of this repo's standing CI monitors implement a real state-diffed recovery/all-clear post
      (confirmed present: `branch-health.yml`'s lag-monitor, `overnight-dead-man-switch.yml`; confirmed absent:
      `glue-pool-starvation-monitor.yml`, `glue-runner-health-monitor.yml` — both now schedule-disabled so the gap is
      dormant, not urgent) vs. ones that only ever post CRITICAL/WARNING and never confirm resolution. For any LIVE
      (schedule-active) monitor found missing it, add the `branch-health.yml`-pattern recovery job (cached prior-state
      diff + `recovery: true` + a short `cooldown_min`) — this is the gap the operator flagged directly: "if this got
      fixed and I didn't see a Slack alert that it got fixed, that would be a problem."

## Progress Log

- **2026-08-07 (interactive session)**: Investigated the confirmed-live `glue-pool-starvation-monitor` CRITICAL loop end
  to end (SSM host diagnosis, GH API job-label inspection, plan/issue-doc cross-reference), root-caused to same-day
  intentional runner retirement colliding with already-in-flight pre-revert queued jobs, cancelled all 12
  permanently-stranded runs, disabled the monitor's schedule (mirroring the sibling monitor's same-day precedent fix),
  and live-verified via a manual `workflow_dispatch` that the monitor now reports healthy. Filed this doc + the one P3
  follow-up (recovery-announcement audit) rather than silently letting the alerts merely stop.

- **na-eligibility-audit 2026-08-08** (tranche `ci`): KEEP-NA-STALE (already-duplicated) — the doc's sole open todo
  ("Audit which of this repo's standing CI monitors implement a real state-diffed recovery/all-clear post...") is
  already extracted verbatim into `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 4 (`status: draft`,
  `assigned_vm: planning`, drafted by `/ag-closeout-audit ci` the same day). Not reclassifying `assigned_vm` here —
  batch6 is still draft pending operator activation; flipping this doc too would risk a duplicate dispatch once batch6
  activates.
