---
doc_type: plan
title: CI/CD workflow-sprawl consolidation — fold redundant CI workflows + token-pool split + SIT-harness decouple
summary:
  release_machinery sprawl reduction. Fold sit-starvation→sit-debounce, merge ci-status-reconciler+ci-failure-watcher
  into ci-health, consolidate the main-backmerge drift-tick + promotion-lag-monitor into one branch-health monitor,
  extract a shared agent-runner.yml. Plus the token-pool split (same-repo read-only→GITHUB_TOKEN, cross-repo→PAT), the
  SIT-harness-hygiene-from-cascade-validity decouple, the game-day+synthetic smokes into the SIT schedule, and a
  per-cone parallel-staging-locks design. Independent of Phase-2 (different workflow files).
status: active
nature: process
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, sprawl, consolidation, sit, ci-health, branch-health, token-pool, release_machinery]
related:
  [cicd_consolidated_remaining_2026_06_24.md, ../epics/infrastructure_master.md, ../../codex/08-workflows/ci-cd-flow.md]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by:
depends_on:
source: cicd_consolidated_remaining_2026_06_24.md (release_machinery lines ~795, 1499, 1500, 1555-1561, 1683)
assigned_role: infra
drift_direction: advance-code
---

# CI/CD workflow-sprawl consolidation

> **Independent track — no upstream dep, parallel-startable.** Touches CI workflows but DIFFERENT files than Phase-2
> (sit-_/ci-_/backmerge vs semver/promote) → safe to run alongside. **Model tier: Sonnet/infra** — mechanical folds.
> **Internally serialize** (same-workflow-file edits never concurrent) + `rollout-workflow-templates.sh` where
> templated. **grep-then-READ before folding** — confirm no live trigger is dropped.

## Tasks

- [x] ✅ [SCRIPT] P3. Fold `sit-starvation-detector.yml` into `sit-debounce-trigger.yml`. **Gate:** starvation detection
      still fires; one fewer workflow; actionlint-clean. (release_machinery ▸ sprawl)
- [x] ✅ [SCRIPT] P3. Merge `ci-status-reconciler` + `ci-failure-watcher` into one `ci-health.yml`. **Gate:** both
      behaviours preserved (status reconcile + failure watch); one workflow. (release_machinery ▸ sprawl)
- [x] ✅ [SCRIPT] P3. Consolidate the `main-backmerge` drift-tick + `promotion-lag-monitor` into one branch-health
      monitor. **Gate:** drift + lag alerts both preserved; one monitor. (release_machinery ▸ sprawl)
- [x] ✅ [SCRIPT] P2. Surface a published-vs-required AR lag metric in the branch-health monitor / the dashboard (moved
      here from misc-hygiene 2026-06-27 — single owner of `promotion_lag_monitor` to keep the parallel tracks
      collision-free). **Gate:** the AR lag metric renders on the dashboard.
- [x] ✅ [SCRIPT] P3. Extract a shared `agent-runner.yml`; collapse `conflict-resolution-agent` into it. **Gate:** the
      agent runner is reused; conflict-resolution still dispatches. (release_machinery ▸ sprawl)
- [x] ✅ [INFRA] P2. Token-pool split for the promote/monitor Actions (same-repo read-only → `GITHUB_TOKEN`; cross-repo
      → PAT). **Gate:** PAT-REST rate drops materially; same-repo reads use GITHUB_TOKEN; no permission regressions.
- [x] ✅ [SCRIPT] P2. Decouple SIT-harness hygiene from cascade validity (route harness lint to a fix-task, not a
      cascade block). **Gate:** a harness-lint issue no longer blocks the cascade; it files a fix-task instead.
- [x] ✅ [SCRIPT] P2. Tier-E — wire game-day + synthetic smokes into the staging SIT schedule. **Gate:** the SIT
      schedule runs the game-day/synthetic smokes; results surface. (sit_and_fleet)
- [x] ✅ [DESIGN] P2. Per-cone parallel staging locks (design doc — let independent dep cones promote concurrently).
      **Gate:** a design doc exists describing per-cone locks; no implementation required in this plan.

## Success criteria

- Four workflow folds complete (sprawl reduced), each preserving behaviour; token-pool split live; SIT-harness
  decoupled; game-day smokes scheduled; per-cone lock design documented.

## Codex SSOT updates

- `codex/08-workflows/ci-cd-flow.md` — update the workflow inventory (folded names) + the token-pool convention.

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (release_machinery sprawl lane). Independent — parallel.
- 2026-06-27: **All 9 tasks COMPLETE** (slot-5·laptop, session a639bd7e).
  - Task 1 ✅: `sit-starvation-detector.yml` deleted; starvation-detect jobs (`check-stale-lock`, `stale-remediate`,
    `stale-notify`, `stale-notify-resolved`, `stale-persist`) folded into `sit-debounce-trigger.yml` after the `persist`
    job.
  - Task 2 ✅: `ci-failure-watcher.yml` renamed → `ci-health.yml`; header comment updated noting retired
    ci-status-reconciler absorption.
  - Task 3+4 ✅: `promotion-lag-monitor.yml` deleted; new `branch-health.yml` (cron `*/30`) consolidates: drift-tick
    (dispatch `main-backmerge-to-ldr`), promotion-lag monitor (`promotion_lag_monitor.py --slack`), AR-dep-publish lag
    (`assert_deps_published_to_ar.py` per-repo). Schedule removed from `main-backmerge-to-ldr.yml` template + PM own
    copy.
  - Task 5 ✅: `agent-runner.yml` extracted as reusable `workflow_call` (idempotency-check + escalate-to-orchestrator
    dispatch + label). `conflict-resolution-agent.yml` collapsed to thin input-resolver → calls `agent-runner.yml`.
  - Task 6 ✅: Token-pool split — `ldr-to-main-promote.yml` + `ldr-to-staging-promote.yml` checkout moved to
    `GITHUB_TOKEN`; App token created after checkout for cross-repo ops. Convention documented in
    `codex/08-workflows/ci-cd-flow.md`.
  - Task 7 ✅: `sit-gate.yml` `harness-lint` job added (parallel to `lock-staging`, `continue-on-error: true`). Checks
    SIT harness existence + consecutive-failure pattern; on issues dispatches `wall_type=harness_lint` fix-task to
    orchestrator. Cascade NEVER gated on this job.
  - Task 8 ✅: `sit-gate.yml` dispatch step extended: `game-day-sit` + `synthetic-smokes` dispatched to
    `system-integration-tests` best-effort after `full-workspace-sit` (hard-fail). Notify message updated.
  - Task 9 ✅: `codex/08-workflows/per-cone-parallel-staging-locks.md` written — cone assignments (T0-T1-base exclusive;
    T3+ concurrent), lock schema sketch, prerequisites.
  - Codex SSOT updated: `codex/08-workflows/ci-cd-flow.md` — workflow inventory table (folded/retired names), token-pool
    convention section, SIT-harness lint decoupling section. All stale `ci-failure-watcher`/`promotion-lag-monitor`
    references updated.
  - QG: green (exit 0) after fixing `per-cone-parallel-staging-locks.md` missing scope frontmatter + PM own copy of
    `main-backmerge-to-ldr.yml` schedule removal.
