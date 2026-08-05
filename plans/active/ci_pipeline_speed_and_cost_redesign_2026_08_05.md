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
- **CORRECTED 2026-08-05 (was wrong when this plan was opened)**: the interactive `gh` CLI session indeed lacks billing
  scope, but that was never the real path — `deployment-api` already holds a dedicated fine-grained PAT
  (`github-billing-token`, GSM secret in project `central-element-323112`, Account permission "Plan: Read-only" only)
  that has been used successfully in at least 3 prior sessions to pull real Actions spend (2026-07-10/11, 2026-07-23,
  2026-07-30 — see `plans/archive/issues/github_billing_dashboard_access_2026_07_09.md`). No operator OAuth needed. Also
  note the classic `/users/{user}/settings/billing/actions` endpoint this todo originally named is deprecated
  (`410 Gone`); the working replacement is the Enhanced Billing endpoint `GET /users/{username}/settings/billing/usage`
  (filter `product=actions`), which is exactly what `github-billing-token` reaches. Fastest path: read
  `deployment-api`'s own `/costs/summary`/`/costs/breakdown` routes (`deployment_api/routes/costs.py`) or check
  deployment-ui's `/ops/costs` page directly — both already surface this live. Direct `gcloud secrets versions access`
  also works but needs a live `gcloud auth login` session (hit intermittent human-account reauth failures 2026-08-05
  fetching it from an agent session — not a permission problem, just a stale local gcloud session; the `github-token-sa`
  service-account key sidesteps this entirely, see the resolved todo below).
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

- [x] ✅ [INFRA] P0. **Get real GitHub Actions billing numbers.** — Pulled live 2026-08-05 via `github-token-sa`'s GCP
      service-account key (sidesteps the human-account's intermittent gcloud MFA-reauth failures hit mid-session) →
      `github-billing-token` GSM secret → `GET /users/IggyIkenna/settings/billing/usage`. **July 2026:
      $1,179.13 total**
      (100% `sku=Actions Linux`, i.e. 100% GitHub-hosted `ubuntu-latest` billing — self-hosted runners bill $0
      against this API by design). Confirms the operator's "~$1k" recollection almost exactly; the "$5k" figure
      referenced when this plan opened does not match GH Actions billing specifically (likely conflated with AWS
      self-hosted infra spend, which is a separate cost surface — `deployment-api`'s `/costs/summary` covers both, worth
      cross-checking if the $5k figure still needs reconciling). **August 2026 (partial, through day 5): $89.44.**
      **Unexpected finding — by-repo breakdown**: `unified-trading-pm` alone is **41.0% of July's total**
      ($483.58) and
      **59.4% of August's partial total** ($53.15) — more than every actual trading-service repo
      combined, despite PM being a coordination/docs/CI-tooling repo, not a service. Spawned a follow-up investigation
      (see new todo below) rather than assume the cause.
- [x] ✅ [INFRA] P1. **Measure current LDR→main wall-clock, per repo** — measured 2026-08-05 against `execution-service`
      (heavy), `greeks-service` (light), `agent-orchestrator`, `unified-trading-pm`, sampling 08-02/03/04 PRs (excludes
      the 08-05 incident). **Result: the 3-5min target is already beaten by 10-50x for most of the fleet** —
      PR-open-to-merge is 4-16 seconds for every repo running "direct" mode (execution-service #544/#541, greeks-service
      #404/#402, agent-orchestrator #781/#774), because the required checks
      (`quality-gates-v2`/`sit-gate/fleet-green`/`quickmerge-provenance`) reference/reuse QG state that already ran when
      the commit landed on LDR — the heavy test/lint slices (1-2+ hrs sometimes) are NOT re-run inside the promotion
      PR's lifetime. **The real structural floor is invisible to "open→merge"**: it's the ~15-min promotion-cron cadence
      that decides WHEN a PR gets opened at all (before `createdAt`), giving an average ~7.5min PRE-PR latency not
      captured by this metric. **Outlier: PM runs a different "auto-drain" mode** with genuine 4s-34min variance even on
      clean days (PM #2088 = 4s, #2199 = 14m52s, #2266 = 33m48s) — looks like real retry/backoff churn in that mode, not
      cron-related; worth checking `ldr-to-main-promote-fleet.yml`'s auto-drain retry logic if a tight fleet-wide floor
      matters, separate from PM's ubuntu-latest billing-driver investigation above (different root cause, same repo).
- [ ] [INFRA] P1. **Find PM's dominant GitHub-hosted (`ubuntu-latest`) cost driver.** Follow-up from the P0 billing
      finding above (41-59% of ALL fleet Actions billing lands on `unified-trading-pm` specifically). First-pass grep
      (2026-08-05) found ≥18 PM workflow files with at least one `ubuntu-latest` job, incl. `branch-health.yml` (hourly
      cron, 3 ubuntu-latest jobs/tick), `ci-health.yml` (hourly, 1 job, intentionally GH-hosted per its own comment),
      and — the strongest suspect — `python-quality-gates-v2.yml`, a `workflow_call` reusable template: if OTHER repos'
      CI calls into it and its internal jobs hardcode `ubuntu-latest` for specific steps, billing attributes to PM (the
      file's home repo) even though the WORK is fleet-wide. Investigation in progress; done when the actual top 3-5
      cost-driving workflows are named with real July run-count evidence (`gh run list`), not just grep.
- [x] ✅ [INFRA] P1. **Audit the `update-dependency-version.yml` fan-out** — CLOSED as "already true", 2026-08-05.
      `update-repo-version.yml` (the sender, `.github/workflows/update-repo-version.yml:294-310`) computes
      `/tmp/dependents.txt` by walking `workspace-manifest.json`'s `repositories.<name>.dependencies` list and only
      including repos whose `dependencies` array actually names the bumped repo — a MINOR/PATCH bump's
      `repository_dispatch` (`:668-672`) fires ONLY to those real dependents, never the whole fleet. A MAJOR/breaking
      bump additionally triggers `cascade-qg-ordering.yml` (`:717` on), which does a topological forward-walk of
      "transitively affected repos" via the manifest's `topologicalOrder.levels` (`cascade-qg-ordering.yml:150-210`) —
      broader than direct dependents (by design — breaking changes legitimately need wider validation, matching this
      plan's own "done" criteria), but still graph-derived, not an unconditional blast. One deliberate special case:
      `pm_all_tiers = source_repo == "unified-trading-pm"` (`:170`) widens the cascade further specifically when PM
      itself is the source — reasonable given nearly everything depends on PM transitively. No fix needed; this todo was
      based on an untested assumption, not a confirmed bug.
- [ ] [OPERATOR] P1. **Decide the concurrency-reduction target** and execute: reduce `unified-trading-pm`'s glue pool
      (currently 5) and `agent-orchestrator`'s (currently 2) per the proposal in
      `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`'s 2026-08-05 entry — or a different target if the
      fresh EBS throughput headroom (500 MB/s vs the old 125 MB/s ceiling) changes the calculus. Verify with a
      steady-state (not spot-check) load measurement before and after, matching the rightsizing plan's own unfinished
      "longer-window measurement" todo. **RESOLVED 2026-08-05 — open question answered, concurrency cut is clear to
      proceed on this axis**: investigated whether AO's glue pool serves escalation-dispatch work in addition to its own
      CI. It does NOT, on either count the operator expected: (1) AO's `quality-gates-v2.yml` still runs its own CI on
      `[self-hosted, glue]` exactly like every other repo — unchanged. (2) The actual `/api/escalate` HTTP call fires
      from `unified-trading-pm`'s `escalate-to-orchestrator.yml` — PM's glue pool, not AO's; AO's own
      `escalate-to-orchestrator.yml` is vestigial (nothing calls it via `uses:`). (3) The worker that actually resolves
      an escalation never touches a GHA runner at all — `server/escalation.py` spawns it onto an AO "slot" (a persistent
      tmux session), a completely separate resource pool. So cutting AO's glue pool 2→1 only affects AO's own CI
      throughput, not escalation capacity — safe to decide purely on that basis. **Separate, real finding surfaced by
      this investigation** (not a CI-cost topic, flagging for the right owner): escalation dispatch is currently
      HARD-PINNED to the Anthropic/Claude account pool (`autospawn.pick_headroom_account(...)` with no `provider=` arg
      defaults to `"anthropic"`, `agent-orchestrator/server/autospawn.py:868-873`) — it does NOT use the DeepSeek/Claude
      blended routing that regular backlog dispatch already has (`select_account_for_spawn()`, same file `:1216+`). The
      operator's stated preference ("escalation work should be dispatchable to DeepSeek, we already have the
      observability for it") is NOT true of the current code — `EscalationQueueRow`/`activity_log` tracks escalation
      lifecycle but never DeepSeek spend, since escalations never route there today. Wiring escalation dispatch through
      the existing blended-routing path is a real, scoped follow-up but belongs in an agent-orchestrator
      dispatch/routing plan, not this CI-cost plan — not created here per the "ask before creating a plan" rule;
      operator to decide where it lands.
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
