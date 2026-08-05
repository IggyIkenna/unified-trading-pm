---
doc_type: plan
title: CI pipeline redesign — fast LDR→main (3-5min target), needs-driven cross-repo triggering, cost right-sizing
summary: >-
  Operator target: LDR→main should take 3-5 minutes regardless of repo when little has changed, cross-repo workflow
  triggering should fire only when genuinely needed, and fleet CI cost (AWS self-hosted + GitHub Actions billing) should
  track actual task volume (~300 tasks/day) instead of the current multiple-of-that footprint. Seeded from a same-day
  live investigation (2026-08-05) that found and fixed a real crash-loop bug, root-caused the capacity crisis to
  disk-throughput saturation (not CPU), and raised the CI VM's EBS ceiling — this plan is where the remaining, bigger
  design work (measurement, fan-out audit, concurrency right-sizing, cost accounting) lives.
status: active
nature: process
asset_group: [ci, infrastructure]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator, system-integration-tests]
scope: [engineer, admin]
tags: [ci-cd, cost, self-hosted-runners, capacity, cross-repo-dispatch, pipeline-speed]
related:
  [
    /plans/active/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    /plans/active/issues/qg_v2_digest_refresh_fastpath_gap_2026_08_05.md,
    /plans/archive/2026_06/quality_gates_speed_and_config_ssot_2026_06_09.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-08-05
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: infra
drift_direction: advance-code
depends_on: [ci_runner_fleet_split_and_vm_rightsizing_2026_08_03]
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md,
    scripts/workflow-templates/self-hosted-qg-repos.txt,
    scripts/workflow-templates/update-dependency-version.yml,
  ]
source:
  [
    "operator, 2026-08-05, live session — 'a simple CI flow LDR to main should take max 3-5 mins regardless of the
    repo... currently we spend 1k monthly on gh plus... 5k gh ci spend alone'",
  ]
last_updated: 2026-08-05
locked_by:
locked_since:
supersedes:
superseded_by:
---

# CI pipeline redesign — speed + needs-driven fan-out + cost

## Why this plan exists

Same-day investigation (2026-08-05) chasing a stuck dashboard deploy surfaced a chain of real, concrete findings —
recorded in full in `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s 2026-08-05 entry. Summary:

- **Fixed and shipped this session**: agent-orchestrator's `glue-1` runner crash-loop (89 restarts, a DELETE-retry race
  in `glue-runner-run.sh`) — code fix `unified-trading-pm@a4eb9a288`, deployed live to the VM.
- **Fixed this session**: the CI VM's EBS volume was throughput-capped at gp3's 125 MB/s baseline (confirmed via
  `iostat`: 89.5% util, 101-deep queue, throughput AT the ceiling — NOT a CPU or IOPS problem, load-average readings
  were mostly I/O wait). Raised to 500 MB/s / 6000 IOPS via `aws ec2 modify-volume` (no downtime).
- **Also fixed this session**: `python-quality-gates-v2.yml`'s metadata-only fast-path didn't cover the bot's
  digest-only refresh commit shape — every UTL base-image republish ran the FULL gate on all ~24 fleet repos
  simultaneously for a single-line Dockerfile bump. Fixed (`qg_v2_digest_refresh_fastpath_gap_2026_08_05.md`).
- **Investigated and explicitly NOT pursued**: scoping `pytest` to changed files for a faster local/quickmerge loop.
  This exact idea was already designed, measured, and rejected by the operator on 2026-06-17
  (`quality_gates_speed_and_config_ssot_2026_06_09.md` Phase 2 — "🔴 CLOSED — DO NOT BUILD THE FAST TIER"): the
  safely-scopable slice was measured at ~1.1% of gate wall-clock (tests are 67.4%, deliberately kept always-full because
  this codebase's dynamic-dispatch/factory-registry wiring makes test-impact-selection unreliable — a
  deselected-but-actually-impacted test is a false green). Also: quickmerge's local Pass-1 QG run happens on each
  agent's own machine, not the shared CI VM, so scoping it wouldn't have addressed the capacity crisis regardless.
  Recorded here so it isn't re-investigated from scratch next time someone has the same instinct.
- **Not yet measured**: actual GitHub Actions billing (`$1k`/`$5k` figures from the operator) — the working `gh` token
  here only carries `repo`/`read:org`/`gist` scope, not the `user` scope the billing API requires, and granting it needs
  an interactive OAuth prompt not available in an unattended session.
- **Concrete, evidenced but NOT yet decided**: reducing per-repo self-hosted runner slot counts as the direct
  concurrency lever (unified-trading-pm has 5 glue + 3 writer; agent-orchestrator has 2 glue + 1 writer; the other 23
  repos already have the minimum, 1 each) — proposed in the issue doc, needs an explicit target before touching
  fleet-wide runner provisioning.

## What "done" looks like

- LDR→main for a small/no-op change completes in 3-5 minutes, verified across a representative sample of repos (not just
  the 1-2 already-fast ones).
- A dependency-version bump from UTL/UAC/PM only triggers downstream `repository_dispatch` for repos that actually
  declare that dependency — not the whole fleet unconditionally — UNLESS the bump is breaking (breaking changes
  legitimately need broader validation).
- Fleet CI cost (AWS self-hosted compute + GitHub Actions billed minutes, once both are measured) has a stated,
  understood relationship to actual task volume (~300 tasks/day), and any residual gap is explained, not hand-waved.

## Todos

- [ ] [OPERATOR] P0. **Get real GitHub Actions billing numbers.** Either grant the working `gh` CLI expanded scope
      (`gh auth refresh -h github.com -s user`, interactive) so `gh api /users/IggyIkenna/settings/billing/actions`
      resolves, or pull the numbers directly from github.com → Settings → Billing, for the last full month: total
      Actions minutes consumed, split by runner type (GitHub-hosted `ubuntu-latest` vs self-hosted — only the former
      bills against Actions minutes), and the actual $ figure to reconcile against the "$1k"/"$5k" estimate referenced
      when this plan was opened.
- [ ] [INFRA] P1. **Measure current LDR→main wall-clock, per repo, for a genuinely small/no-op change** — not the Aug-5
      numbers (those were mid-incident). Pick 4-5 repos spanning the fleet (a heavy one like `execution-service`, a
      light one, PM itself, agent-orchestrator) and time an actual promote-PR from open to merged under normal
      (non-incident) load. This is the baseline the 3-5min target gets measured against — without it, "should take 3-5
      min" is a goal, not yet a gap.
- [ ] [INFRA] P1. **Audit the `update-dependency-version.yml` fan-out**: does every UTL/UAC/PM bump currently dispatch
      to literally every repo in `workspace-manifest.json`'s `dependency_caps`/dep-graph, or only repos that actually
      declare that dependency? If it's unconditional, that's the direct fix for "should only trigger other repo flows if
      those are really needed" — scope the dispatch to the real dependency graph. If it's already scoped, document that
      (closes this todo as "already true", not a re-investigation).
- [ ] [OPERATOR] P1. **Decide the concurrency-reduction target** and execute: reduce `unified-trading-pm`'s glue pool
      (currently 5) and `agent-orchestrator`'s (currently 2) per the proposal in
      `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s 2026-08-05 entry — or a different target if the
      fresh EBS throughput headroom (500 MB/s vs the old 125 MB/s ceiling) changes the calculus. Verify with a
      steady-state (not spot-check) load measurement before and after, matching the rightsizing plan's own unfinished
      "longer-window measurement" todo.
- [ ] [INFRA] P2. **Re-evaluate whether `unified-trading-library` and `e2e-testing`** (reverted to GitHub-hosted
      `ubuntu-latest` specifically due to the capacity crisis — see `self-hosted-qg-repos.txt`'s own changelog comments)
      can return to self-hosted now that the EBS throughput ceiling is raised. If yes, that's a direct GH Actions
      billing reduction (those two repos' real test runs are currently BILLED minutes as a workaround).
- [ ] [INFRA] P2. **Check whether `glue-runner-crash-loop-watchdog.sh` (RESTART_THRESHOLD=5 default) actually paged**
      for agent-orchestrator's 89-restart crash-loop found this session. If it didn't fire, that's a real alerting gap
      on top of the crash-loop bug itself — worth its own fix so the NEXT crash-loop doesn't need a live manual
      investigation to surface.
- [ ] [INFRA] P3. **Once real GH billing numbers exist (todo 1)**, produce the actual cost-vs-volume reconciliation the
      operator asked for: ~300 tasks/day, expected CI-minute footprint at some stated per-task assumption, actual
      measured footprint, and where the delta comes from (concurrency fan-out, retries/re-triggers, the already-fixed
      digest-refresh churn, or something not yet found).
- [ ] [INFRA] P1. **Warm git-object cache for JIT-ephemeral runner checkouts** (operator, 2026-08-05: "why fresh-clone
      every time when we already keep clones current via cron"). Confirmed live: `glue-runner-run.sh`'s JIT-ephemeral
      branch runs `rm -rf _work/* _diag/*.log` before EVERY job, and `python-quality-gates-v2.yml`'s `actions/checkout`
      steps use `fetch-depth: 1`/`2` — shallow, but still a genuine cold network clone every run (no existing git
      history to fetch against once `_work` is wiped). No reference-clone/warm-mirror mechanism exists anywhere in this
      setup today (verified: zero hits for `--reference`/`--shared`/mirror patterns across
      `scripts/self-hosted-runners/` and `.github/workflows/`). Proposed design — same "lives OUTSIDE `_work`, survives
      the wipe" pattern this codebase already uses for `RUNNER_TOOL_CACHE`: maintain a cron-refreshed bare mirror clone
      per repo (same idea as the existing per-slot `slot-cron-ff-pull.sh`, just serving the runner instead of a
      worktree), and have each job's checkout use `git clone --reference <mirror> --dissociate` against it — `_work`
      still gets wiped fresh every job (isolation preserved, the actual reason the wipe exists), but the git OBJECT DATA
      is already local, so only genuinely new commits since the last cron refresh come over the network. Needs real
      testing before rollout (confirm `actions/checkout`'s behavior against a pre-seeded reference, or replace it with a
      custom checkout step) — this touches every job on the shared runner, don't ship blind. Directly reduces disk WRITE
      I/O on the same EBS volume this session's capacity investigation was about.

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — the gate set, quickmerge, LDR-is-SSOT, promotion flow this plan operates inside
  of; do not duplicate its content here.
