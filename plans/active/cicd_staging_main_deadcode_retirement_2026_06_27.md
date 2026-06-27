---
doc_type: plan
title:
  CI/CD staging→main dead-code retirement — remove the squash/conflict-fallback/auto-collapse now all 21 are ldr_main
summary:
  WS-L Phase-1 cleanup. With all 21 standard repos on promotion_model=ldr_main, the staging→main squash machinery is
  dead code. Retire the staging→main squash step + the conflict-fallback + the WS-B auto-collapse SPEC per repo, and
  stop the redundant empty staging→main PRs across consecutive */15 runs. GATED on Phase-2 finalize because Phase-2
  rewrites the same staging-to-main.yml / version-cure files — retiring before that would collide.
status: draft
nature: process
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cicd, WS-L, ldr_main, dead-code, staging-to-main, cleanup]
related:
  [
    cicd_consolidated_remaining_2026_06_24.md,
    cicd_phase2_finalize_2026_06_27.md,
    ../epics/infrastructure_master.md,
    ../../codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-06-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-06-27
supersedes:
superseded_by: cicd_retire_staging_branch_2026_06_27
depends_on: cicd_phase2_finalize_2026_06_27
source: cicd_consolidated_remaining_2026_06_24.md (lines ~777, 1190)
assigned_role: infra
drift_direction: advance-code
---

# CI/CD staging→main dead-code retirement

> **WS-L cleanup lane.** **GATED — `depends_on: cicd_phase2_finalize`** (Phase-2 rewrites the same `staging-to-main.yml`
>
> - version-cure files; retiring first would collide). Held `draft` until Phase-2 finalize lands. **Model tier:
>   Sonnet/infra** — mechanical dead-code removal; no shims. **grep-then-READ before deleting** (0 hits ≠ no live caller
>   — features are runtime-resolved).

## Tasks

- [ ] [WORKFLOW] P2. Retire the `staging→main` squash step + the `staging-conflict-ldr-main-fallback` + the WS-B
      auto-collapse SPEC per repo now each is on `ldr_main` (all 21 are). These became dead code once the fleet bot owns
      the LDR→main path. **Gate:** the staging→main merge machinery is removed for `ldr_main` repos; grep proves no live
      caller; actionlint-clean; the LDR→main fleet bot remains the single promote path.
- [ ] [WORKFLOW] P3. Stop the redundant empty `staging→main` PRs across consecutive `*/15` runs (NICE-TO-HAVE) —
      re-check whether any still fire after the retirement above; if so, gate their creation on a real content delta.
      **Gate:** no empty staging→main PR is created on a `*/15` tick.

## Success criteria

- The staging→main squash/conflict-fallback/auto-collapse machinery is deleted (no shims), no live callers.
- No redundant empty staging→main PRs.

## Codex SSOT updates

- `codex/08-workflows/ci-cd-flow.md` — note the staging→main merge path is retired fleet-wide (LDR→main is the only
  promote path under `ldr_main`).

## Progress Log

- 2026-06-27: Split from the cicd consolidated tracker (WS-L dead-code lane). Gated on Phase-2 finalize.
