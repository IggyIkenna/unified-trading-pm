---
doc_type: issue
title: "Fleet promoter ldr-to-main-promote-fleet stalled 3+ hours — glue runner pool depleted"
summary: >-
  Discovered while investigating sit-gate/fleet-green auto-retrigger failures (slot 12, 2026-08-06). The LDR→main fleet
  promoter (ldr-to-main-promote-fleet.yml) produced 13 consecutive cancelled runs between 19:00–22:30 UTC because only 1
  of 4 `glue`-labeled self-hosted runners was online and not busy. Each `*/5` schedule event queued a new run that
  cancelled its queued predecessor before any runner picked it up — effectively zero promotions for 3+ hours fleet-wide,
  blocking all ldr_main repos including system-integration-tests (215 commits behind main with the SIT poll-budget fix
  system-integration-tests@69b93bc staged on LDR but unreachable).
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, fleet-promoter, self-hosted-runners, ldr-to-main]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_08/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: 2026-08-06
author: slot-12
priority: P1
parent_epic: infrastructure_master
source: ["Surfaced while investigating sit-gate fleet-green auto-retrigger failures (slot 12, 2026-08-06)."]
execution_scope: orchestrator-agent
assigned_vm: planning
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /plans/archive/2026_08/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
    .github/workflows/ldr-to-main-promote-fleet.yml,
    scripts/cicd/glue_runner_health_monitor.py,
  ]
---

# Fleet promoter stalled 3+ hours — glue runner pool depleted

## What I found

1. The `ldr-to-main-promote-fleet` workflow produced **13 consecutive cancelled runs** between 19:00 and 22:30 UTC on
   2026-08-06 (runs 31126553404 through 31128865834). Zero promotions completed in this window.
2. Root cause: the `glue` self-hosted runner pool was at 25% capacity. Of 4 `glue`-labeled runners, only 2 were online
   (`glue-ip-172-31-3-59-1` and `-2`), and one of those was busy with another job. The remaining 2 runners (`-3` and
   `-5`) were offline.
3. With `concurrency.group: ldr-to-main-promote-fleet` + `cancel-in-progress: false`, GitHub allows at most one queued
   run behind the in-progress one. Each new `*/5` schedule event replaced the queued run — but with no runner available,
   no run ever started, creating an indefinite cancel-treadmill.
4. Resolved when a glue runner became available: the 22:30 run (31129033588) reached `in_progress` at ~22:35 UTC.
5. Impact: system-integration-tests (215 commits behind main) and all other `ldr_main` repos were blocked from promotion
   for the entire duration. The SIT poll-budget fix (system-integration-tests@69b93bc) remains on LDR only.

## Why it matters

The fleet promoter is the single chokepoint for all LDR→main promotion. When it stalls, every `ldr_main` repo's fixes
are trapped on LDR indefinitely. The current runner pool has no headroom: 4 runners with only 2 online means any burst
of load or a single additional offline runner triggers a complete stall.

## Recommended decision

- [x] ✅ [INFRA] P1. Add a runner-health monitor for the `glue` pool: alert when fewer than N runners are online (repo:
      unified-trading-pm). Minimum viable: a scheduled workflow that counts online glue runners and posts to Slack when
      the count drops below a threshold (suggest 3). — unified-trading-pm@64c3fd63a + evidence
- [x] ✅ [INFRA] P2. Investigate why glue-3 and glue-5 are offline — restart or replace (repo: unified-trading-pm). —
      unified-trading-pm@HEAD (investigation finding: no restart/replace needed — see Progress Log 2026-08-07)
- [x] ✅ [INFRA] P2. Hardening: add a `workflow_dispatch` trigger to `ldr-to-main-promote-fleet.yml` so an operator can
      manually kick off a promotion tick when the schedule is stuck (already exists — confirmed at line 53 of
      .github/workflows/ldr-to-main-promote-fleet.yml with dry_run + only_repo inputs; no code change needed).

## Follow-ups

- [x] ✅ [INFRA] P1. **Live recurrence signal (2026-08-07, slots 2 + archive-candidates-audit):** the glue runner pool
      has been observed at genuinely 0 registered runners twice on 2026-08-07 (13:34-13:38 UTC per slot 2's finding, and
      re-confirmed via `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` returning `{"total_count": 0}` again
      during this archive sweep) — worse than the original 08-06 incident's 25% pool and the 08-07 morning 100%-online
      check. Determine whether this is the same JIT-restart-window false-positive class the 08-07 morning investigation
      ruled out, or a genuine new pool-depletion/deregistration event; if genuine, escalate per the runner-health
      monitor shipped in this doc's first todo (repo: unified-trading-pm). — **RESOLVED 2026-08-08 (interactive
      session): NEITHER. 0 registered runners is the INTENDED, PERMANENT end-state, not an incident.**
      `self_hosted_runner_public_repo_revert_2026_08_05.md` todo #24 (`unified-trading-pm@c8cd56251e`, landed on `main`
      ~11:23-11:38 UTC 2026-08-07 — i.e. BEFORE both 13:34-13:38 UTC observations) stopped+disabled the
      `github-glue-runner@glue-{1..5}`/`writer-{1,2}` systemd units on CI VM `i-042a6332509482556`, correctly and
      intentionally: PM went public 2026-08-06 and self-hosted-on-a-public-repo is a fork-PR RCE exposure, not a cost
      saving. So the monitor's own threshold is now obsolete for PM rather than tripped — **no escalation is due, and
      re-registering the pool would REGRESS the security decision.** Independently cross-confirmed 2026-08-08 ~03:00 UTC
      from the orchestrator VM (`i-0c9b283b31d6b5ca7`) via SSM: every `github-glue-runner*@*.service` unit resolves
      `not-found`, and the 12 orphaned `github-glue-token-refresh-*.timer` units that fed the dead pool's token cache
      were still firing every 5 min and failing `203/EXEC` on the removed `/opt/github-glue-runners/refresh-gh-token.sh`
      — those 12 timers were `disable --now`'d in this same session (see Progress Log). Retiring the now-obsolete
      `glue-pool-starvation-monitor`/`glue-runner-health-monitor` for PM is already tracked in
      `/plans/active/issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md`, not here.
      Additionally cross-confirmed by slot-4 (2026-08-08): `ldr-to-main-promote-fleet.yml` runs on `ubuntu-latest` (not
      the glue pool); last 9 completed runs (01:30–03:00 UTC) all `completed success`; `*/15` cadence stable; no
      cancel-treadmill — same JIT-restart-window false-positive class as 08-07 morning.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — promoter gate set
- `/codex/05-infrastructure/vm-launcher-runbook.md` — runner infrastructure

## Progress Log

- **2026-08-06 (slot 12)**: Filed after discovering promoter stall during sit-gate fleet-green investigation. Promoter
  self-recovered at ~22:35 UTC when a glue runner picked up the 22:30 run.
- **context-scout 2026-08-07**: populated context_scope (5 entries).
- **2026-08-07 (slot 9, fleet_promoter_glue_runner_stall-002)**: Investigated glue-3 and glue-5 offline status. GitHub
  API (`repos/IggyIkenna/unified-trading-pm/actions/runners`) confirms all 5 glue runners (`glue-ip-172-31-3-59-{1..5}`)
  are **online** and not busy as of 2026-08-07. Cross-referenced
  `glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md` Progress Log (2026-08-06 session): glue-3 and glue-5 were in
  the **normal JIT-runner between-job restart window** (`Restart=always`, `StartLimitIntervalSec=0`), not a real failure
  — they self-recovered within ~6 minutes, and the crash-loop watchdog was false-positiving on clean `Result=success`
  exits throughout that window. That false-positive bug was already fixed and shipped as `879e3e109`. **No restart or
  replacement was needed**: the runners recovered by design, monitoring is now correct, and the pool is fully healthy.
  SSM host-level verification not possible from `ikenna-worker` identity (consistent with all prior entries in the
  sibling issue doc); GitHub API is the authoritative signal and shows clean state.
- **2026-08-07 (slot 2, semver_agent_squash_promote_blind_to_patch_fixes investigation)**: Recurrence observed while
  verifying an unrelated semver-agent fix — `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` returned
  `{"total_count": 0, "runners": []}` (HTTP 200, not an auth artifact), checked repeatedly 13:34–13:38 UTC: genuinely 0
  runners registered, not just some offline — worse than the 08-06 incident (25% pool) and the 08-07 morning check (100%
  online). Preceding `ldr-to-main-promote-fleet` runs across roughly an hour (12:23–13:30 UTC) show a run of consecutive
  `cancelled` conclusions matching the original incident's cancel-treadmill signature (`cancel-in-progress: false`
  should queue, not cancel — something external is re-dispatching faster than any runner can pick up work, or the pool
  emptied entirely). The most recent dispatch (run `31182919694`, 13:30:06 UTC) was still `status=pending` as of 13:38
  UTC (~8 min, not yet a new multi-hour stall by itself — flagging the pattern, not overstating this one run's age). Did
  not investigate further or attempt a fix (out of scope for the semver-agent task in progress; this doc's owners
  already have the runbook). Impact: blocks LDR→main promotion fleet-wide, which in turn is delaying live-fire
  verification of 15 repos' semver-agent fix. Flagging as a live recurrence — worth a fresh look at whether this is the
  same JIT-restart-window false-positive class or a genuine new pool-depletion event.
- **archive-candidates-audit 2026-08-07 (slot 3, cicd)**: KEEP_OPEN — re-checked
  `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` while classifying this doc for the archive sweep: still
  `{"total_count": 0}`, corroborating slot 2's same-day finding rather than a one-off blip. Out of scope for this
  escalation to investigate further (unrelated to the QG wall dispatched here — the failing quality-gates-v2 slice runs
  on GitHub-hosted runners, not `glue`). Synthesized a tracked Follow-up todo above; doc stays open pending that
  investigation.
- **2026-08-07 (fleet_workflow_template_dedup todo 5 session)**: **Correction — the "0 glue runners" signal above was a
  red herring for THIS workflow specifically, not a real blocker.** `ldr-to-main-promote-fleet.yml`'s own `runs-on:` was
  flipped `[self-hosted, glue]` → `ubuntu-latest` by `unified-trading-pm@c8cd56251e` (12:23 UTC, the
  `self_hosted_runner_public_repo_revert_2026_08_05.md` todo-24 revert) — i.e. BEFORE slot-2's 13:34–13:38 UTC
  observation. Once on `ubuntu-latest`, this workflow's runs no longer depend on the glue pool's registered-runner count
  at all, so a genuinely-empty glue pool (itself real and expected post-revert — PM no longer routes ANY workflow to
  self-hosted) cannot be what stalled it. The real cause was the separate cancel-treadmill livelock slot-2 root-caused
  and fixed at 16:36 UTC (`383090a998`, `*/5`→`*/15` cadence cut) — confirmed via `gh run list`: runs 15:45–17:19 UTC
  are all `cancelled` (the livelock), runs 17:30 UTC onward are all `completed success`. **Fleet promotion is healthy
  again as of this check (18:00 UTC).** Also observed several `workflow_dispatch` events firing every few minutes in
  that 17:00–18:00 UTC window — looks like the exact ad-hoc-dispatch anti-pattern this doc's sibling livelock issue
  warns against (multiple sessions manually checking their own promotion status); did not dispatch it myself, flagging
  for whoever owns that pattern to stop.
- **2026-08-08 ~03:00 UTC (interactive session, slot 1)** _(restored after being silently overwritten by a concurrent
  commit ~3 min later — see d52a11058's entry below for that session's independent, compatible finding)_: Closed the
  last open todo, which ALSO clears a live orchestrator error loop. **Why this doc mattered beyond its own content:**
  `sync_backlog_to_db` was logging
  `ERROR ... REFUSING to reset task id fleet_promoter_glue_runner_stall-001 — it is done with done_sha=64c3fd63a` on
  **every** `PlanRegenLoop` tick — 60 occurrences in the 6h before this session. That is the
  `regen_positional_task_ids_not_content_stable_2026_07_17.md` guard (`agent-orchestrator@9c7a0fd`, "make the
  sibling-reset case impossible or LOUD") **working exactly as designed, not a new bug**: this doc's done rows were
  pruned from `backlog.yaml`, so regen restarted its positional numbering at `-001` and derived that id for the single
  remaining OPEN todo, colliding with the DB's already-`done` `-001`. The guard refused the reset (protecting
  `done_sha=64c3fd63a`'s audit history) and re-fired every tick because the collision was structural. Closing the last
  open todo removes the plan's only regen-derived task, so the collision — and the error loop — cannot recur for this
  slug. No AO code and no `state.db` row was touched. **Separately fixed on the orchestrator VM in the same session**
  (both verified live, `i-0c9b283b31d6b5ca7`): (1) the 12 orphaned `github-glue-token-refresh-*.timer` units were
  `systemctl disable --now`'d — they had been firing every 5 min and failing `203/EXEC` since
  `/opt/github-glue-runners/` was removed with the decommissioned pool, taking the VM's failed-unit count 13 → 1;
  **deliberately NOT restored**, as re-creating that token cache serves only the pool the public-repo revert
  intentionally tore down. (2) `GCP_PROJECT_ID` was added to the orchestrator's `.env.local` — UTL's
  `cloud_interface.get_project_id()` reads `GCP_PROJECT_ID`/ `AWS_ACCOUNT_ID`, but only `GOOGLE_CLOUD_PROJECT` was set,
  so every `[alerts-ledger] GCS persist failed (worker_liveness)` warning traced to that one missing var.
- **2026-08-08 (slot 4, fleet_promoter_glue_runner_stall-004)**: Investigated the P1 follow-up.
  `gh api repos/IggyIkenna/unified-trading-pm/actions/runners` still returns `{"total_count":0,"runners":[]}` (confirmed
  same empty glue pool) — but this is **not a genuine new pool-depletion event**: the 08-07 afternoon session's finding
  holds. `ldr-to-main-promote-fleet.yml` runs on `ubuntu-latest` (line 75 confirmed), not the glue pool; 0 glue runners
  is expected post-`c8cd56251e` revert and has no bearing on this workflow. Fleet promotion is **healthy**: last 9
  completed runs (01:30–03:00 UTC today) are all `completed success`; the `*/15` cadence is stable; no cancel-treadmill.
  **Verdict: same class as 08-07 morning's JIT-restart-window false-positive — the 0-glue-runner count is structural,
  not a recurrence of the original stall pattern.** No escalation needed. Todo flipped closed.
