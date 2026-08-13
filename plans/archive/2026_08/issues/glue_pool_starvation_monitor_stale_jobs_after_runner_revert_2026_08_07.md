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
status: resolved
nature: issue
asset_group:
  [ci] # corrected 2026-08-09 (/ag-closeout-audit ci) -- was [ci, cross-cutting]; content is a CI-alert-tuning
  # incident (glue-pool-starvation-monitor false-CRITICAL after a self-hosted-runner revert), squarely ci-tranche --
  # already flagged as a mistag by the 2026-08-08 cross-cutting tranche run, never retagged until now
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
assigned_role: cicd
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

> **🟢 ARCHIVED 2026-08-12 (/plan-reconcile) — COMPLETE.** 0 open todos, unlocked. The `archive_exempt: true` /
> line-cap-deadlock premise this doc was held open on is now FALSE: `cross_cutting_consolidated_closeout_2026_07_25.md`
> is live-verified at 732 lines, well under the 1000-line hard cap (a prior doc's "1007L, over cap" claim and another's
> "720 lines" claim were both stale/wrong at different points — 732 is the current truth as of this sweep). The
> same-line link-repoint this doc was blocked on has been applied there; archiving now.

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

- [x] ✅ [INFRA] P3. Audit which of this repo's standing CI monitors implement a real state-diffed recovery/all-clear
      post (confirmed present: `branch-health.yml`'s lag-monitor, `overnight-dead-man-switch.yml`; confirmed absent:
      `glue-pool-starvation-monitor.yml`, `glue-runner-health-monitor.yml` — both now schedule-disabled so the gap is
      dormant, not urgent) vs. ones that only ever post CRITICAL/WARNING and never confirm resolution. For any LIVE
      (schedule-active) monitor found missing it, add the `branch-health.yml`-pattern recovery job (cached prior-state
      diff + `recovery: true` + a short `cooldown_min`) — this is the gap the operator flagged directly: "if this got
      fixed and I didn't see a Slack alert that it got fixed, that would be a problem." **DONE 2026-08-09,
      `unified-trading-pm` (this commit)** — full enumeration + fixes in the Progress Log below. Note: this todo's own
      premise about `overnight-dead-man-switch.yml` was STALE — re-verified live, it has NO dedup_key/cooldown and NO
      resolved job at all (a one-shot nightly liveness check, not a re-nagging standing-condition monitor); it is
      correctly excluded from this fix (see Progress Log for why) but was wrongly cited as "confirmed present."

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

- **2026-08-09 (slot 7, `ci_satellite_ao_dispatch_batch6_2026_08_08.md` todo 4)**: Full audit + fix.
  `unified-trading-pm@c717af0fd`.

  **Citation corrected 2026-08-09 (`ci_satellite_ao_dispatch_batch6_finalize` todo 1)**: `c717af0fd` does not resolve to
  a commit in this repo (a pre-rebase SHA — confirmed via `git cat-file -e`). The real work is
  `unified-trading-pm@4bd8a11d0b` ("feat(cicd): add state-diffed recovery/all-clear bookend to 6 CI monitors"), verified
  ancestor of `origin/live-defi-rollout` — the same correction batch6's own plan already made for its todo 4.

  **Method**: enumerated every `.github/workflows/*.yml` with a `schedule:` trigger (27 files), read each one in full,
  and classified by whether it is a genuine STANDING-CONDITION monitor (uses `dedup_key` + `cooldown_min` to re-nag
  while a bad state persists — the exact shape that leaves an operator wondering "is this still broken?") vs. a per-run
  pass/fail report (no dedup/cooldown; a fresh success is silently suppressed by `notify-slack.yml`'s routine-green
  filter, a fresh failure just posts again next run — no persisting-alert illusion to correct).

  **Correction to this doc's own premise**: `overnight-dead-man-switch.yml` was cited above as "confirmed present" for
  the recovery pattern. Re-read in full: its `notify` job has no `dedup_key`/`cooldown_min` at all and there is no
  sibling resolved/recovery job anywhere in the file — it is a one-shot nightly liveness check (03:00 UTC), not a
  re-nagging standing-condition monitor, so the "recovery bookend" concept doesn't apply to it the way it does to
  `branch-health.yml`'s lag-monitor. Correctly excluded from the fix below, but the earlier "confirmed present"
  characterization was wrong.

  **CONFIRMED PRESENT** (genuine dedup'd standing-condition alert + a real resolved/recovery job, verified by reading
  the file — not just grepping for the word "recovery"): `branch-health.yml` (`lag-notify-resolved`; note its sibling
  `ar-lag-notify` job in the SAME file has NO resolved counterpart — a smaller gap, flagged below, not fixed here since
  AR-dep-publish-lag is a WARNING-only advisory, not the operator's stated pain point),
  `cloud-build-failure-watcher.yml` (`notify-recovery`), `reconcile-release-tags.yml` (`stall-notify-resolved`),
  `sit-debounce-trigger.yml` (`stale-notify-resolved`), `stale-build-watcher.yml` (`notify-recovery`), `ci-health.yml`
  and `ldr-ci-monitor.yml` (both compute recovery TRANSITIONS inside their backing Python script —
  `ci_failure_watcher.py`'s `detect_resolved_prs()`/`kind: "recovered"` and `ldr_ci_monitor.py`'s RED→GREEN transition
  detector — verified by reading the scripts, not just the YAML).

  **CONFIRMED ABSENT + LIVE (schedule-active) — FIXED this commit** (6 monitors: a real dedup'd standing-condition alert
  with no all-clear path):
  1. `fix-approval-timeout.yml` (`dedup_key: fix-approval-timeout:outstanding`, cooldown 120m)
  2. `ldr-docs-gate.yml` (`dedup_key: ldr-docs-gate-red`, cooldown 60m)
  3. `freeze-deferred-build-replay.yml`'s `notify-stale-deferral` (`dedup_key: stale-freeze-deferral`, cooldown 720m)
  4. `promote-fleet-startup-failure-monitor.yml` (`dedup_key: promote-fleet-startup-failure`, cooldown 60m)
  5. `ruleset-drift-alert.yml` (`dedup_key: ruleset-drift-detected`, cooldown 120m)
  6. `sit-gate-stuck-detector.yml` (`dedup_key: sit-gate-stuck-<max_streak>`, cooldown 60m)

  **Fix mechanism**: rather than re-derive the prev-tick-vs-this-tick diff per workflow (as
  `cloud-build-failure-watcher.yml`/`stale-build-watcher.yml` each do inline in bash), added ONE shared, unit-tested
  helper `scripts/cicd/alert_recovery.py` (`compute_recovery()` — a transition-only recovery: prior tick alerted AND
  this tick doesn't; `read_prev_alert()`/`write_state()` — a missing/corrupt state file reads as "no prior alert", never
  a false recovery) + `scripts/cicd/test_alert_recovery.py` (10 tests: the 4-case transition table, missing/
  corrupt-file handling, state round-trip, and 3 CLI-level tests). Every one of the 6 workflows now: restores a
  per-workflow `actions/cache` state file (mirrors `branch-health.yml`'s `.lag-state.json` pattern — no new GCP auth
  needed for the 4 files that had none), calls the shared CLI to compute+persist `recovered`, and gates a new
  `notify-*-resolved` job (severity INFO, `conclusion: success`, `recovery: true`, its own distinct `dedup_key` + short
  `cooldown_min` so the resolved bookend never shares a cooldown with the alert itself) on `recovered=='true'`.

  **Not fixed (documented, not silently dropped)** — monitors that alert on a bad state but are NOT this todo's
  dedup'd-standing-condition shape, so adding a resolved bookend would need a bigger redesign (adding dedup/cooldown
  first) rather than just the recovery bookend this todo scoped:
  - `ldr-to-main-promote-fleet.yml` (`notify` conflict alert, `notify-arm-failed`) and `ldr-to-main-promote.yml`
    (`notify-arm-failed`) — neither has a `dedup_key` at all, so each re-posts every tick the condition persists
    (spammy) rather than dedup'd-silent-until-fixed; the harm shape here is "too noisy," not "silently resolved," so
    it's a different fix (add dedup, not add recovery) — flag for a future todo, not addressed here.
  - `branch-health.yml`'s `ar-lag-notify` (AR-dep-publish-lag) — has `dedup_key`/`cooldown_min` but no resolved sibling;
    smaller/lower-severity gap (WARNING advisory, not an operator-named pain point) than the 6 fixed above.
  - Per-run pass/fail reporters with no dedup/cooldown (`cassette-drift-check.yml`,
    `removed-symbols-workspace- sweep.yml`, `build-smoke-all-repos.yml`, `cold-storage-cleanup.yml`,
    `readiness-verifier.yml`, `secret-health-check.yml`, `digest-drift-sweep.yml`, `ci-status-consolidator.yml`,
    `version-coherence-check.yml`, `workspace-quickmerge-validation.yml`, `supersede-stale-dep-update-prs.yml`) — a
    fresh green run is already silent (suppressed by the carrier's routine-green filter) and a fresh red run posts again
    on its own merits; there is no re-nagging illusion of being unwatched to correct.
  - `glue-pool-starvation-monitor.yml` / `glue-runner-health-monitor.yml` — confirmed still schedule-disabled (verified
    live in both files' `on:` blocks), so out of scope per this todo's own text.

  **Verification**: `scripts/cicd/test_alert_recovery.py` green (10/10) standalone; full `quality-gates.sh` run cited
  below.

- **cicd escalation agt-558c62 2026-08-09**: all items resolved (0 open todos), genuinely archival-eligible, but
  `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` (1007L, already over the 1000L hard line-cap) cites
  this doc via a markdown-syntax link — archiving would hit the exact deadlock documented in
  `/plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` (a same-line link-repoint
  edit in an over-cap file has no `check_line_caps.sh` carve-out). Set `archive_exempt: true`, kept `status: open`
  (terminal status without physical archival would itself fail `check_terminal_status_archived`). Un-set once the
  deadlock doc's operator decision lands and the archival can complete.

- **na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:3e317fe1078c4dd1]:
  KEEP-NA, valid — confirmed independently: 0 open `- [ ]` todos, `archive_exempt: true` with the line-cap-deadlock
  reason still current (the referring doc's `check_line_caps.sh` deadlock is unresolved). Not archive-eligible until
  that deadlock doc's operator decision lands, per the doc's own prior entry.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).

## na-eligibility-audit verdict

**na-eligibility-audit 2026-08-10** (ci tranche, autonomous, dispatch agt-74eff9) [body-hash:aabe4e5e555cea20]: KEEP-NA,
valid — 0 open '- [ ]' todos confirmed (doc's sole P3 INFRA todo flipped [x] 2026-08-09, unified-trading-pm@4bd8a11d0b
-- a fleet-wide 27-workflow recovery-bookend audit; citation self-corrected in-doc 2026-08-09 after an initial wrong
SHA, verified ancestor of live-defi-rollout). Doc is content-complete ('all items resolved (0 open todos), genuinely
archival-eligible' per its own 2026-08-09 Progress Log entry) but is deliberately held status:open + archive_exempt:true
rather than physically archived, because the referring doc
plans/active/cross_cutting_consolidated_closeout_2026_07_25.md is over its 1000-line hard cap and a same-line
link-repoint edit there has no check_line_caps.sh carve-out (tracked in
plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md).
