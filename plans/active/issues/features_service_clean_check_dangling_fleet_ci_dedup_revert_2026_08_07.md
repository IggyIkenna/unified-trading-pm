---
doc_type: issue
title: >-
  Uncommitted, unexplained staged revert of fleet-workflow-dedup thin-caller-stubs found in features-service-clean-check
  worktree -- stashed, not applied
summary: >-
  Found staged (index != HEAD, no commit) changes in the `features-service-clean-check` worktree that revert 5
  `.github/workflows/*.yml` files (`main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`,
  `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`, `update-dependency-version.yml`) from their current
  thin-caller-stub form (shipped by `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`, an active
  in-flight plan) back to full inline content -- 1450 insertions / 69 deletions, zero commit message or rationale
  anywhere. AO auto-nudge flagged this repo RED (dirty 5 files, 210m) during unrelated task
  `defi_satellite_ao_dispatch_batch9-018` (slot 8, gas_fees legacy purge VM monitoring). Could not determine intent
  (accidental partial apply of a revert experiment vs. a deliberate mid-flight rollback of the dedup plan by another
  worker), so per the exact precedent already on file for this same worktree
  (`features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md` -- "unimportant WIP ->
  slot-tagged stash" path when a finding is not part of the current task and intent can't be determined), stashed rather
  than committed or discarded: `stash@{0}` "slot8-2026-08-07: unexplained staged revert of fleet-workflow-dedup
  thin-caller-stubs...". Repo is now clean (`git status` empty, `ahead=0`).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, unified-trading-ci, unified-trading-pm]
scope: [engineer]
tags: [ci-cd, features-service, dangling-wip, stash, git-hygiene, fleet-workflow-dedup]
related:
  - /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md
  - /plans/active/issues/features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
created: "2026-08-07"
author: unknown
source: [backlog task defi_satellite_ao_dispatch_batch9-018, slot 8]
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.12
drift_direction: NA
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
    /plans/active/issues/features_service_clean_check_dangling_revert_of_hyperliquid_cefi_bucket_fix_2026_08_03.md,
    features-service/.github/workflows,
  ]
---

## What was found

`features-service-clean-check` worktree, branch `live-defi-rollout` @ `b0c15f11`: 5 workflow files had staged (index)
content differing from HEAD, worktree matching index (i.e. fully staged, `git add`-ed, never committed). The staged
content is the pre-dedup full-inline form of each workflow -- exactly what `git diff --cached` shows as a revert of
`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`'s thin-caller-stub migration for this repo. No
commit message, no branch note, no Progress Log entry in the dedup plan mentions touching `features-service-clean-check`
specifically as of the last read.

## Why not just commit it

- Not part of the current task (`defi_satellite_ao_dispatch_batch9-018`, an unrelated gas_fees GCS purge VM relaunch).
- The dedup plan is active/in-flight and high-blast-radius (26-repo fleet CI machinery) with a documented prior incident
  class (`shared_ci_workflow_repo_extraction_2026_08_06.md`'s "revert incident"). Committing an unexplained revert of
  live-dispatch-critical CI on a guess risks re-breaking fleet CI the same way.
- This exact worktree has a standing precedent for exactly this situation (see `related`), resolved by stashing +
  filing, not by guessing intent.

## Resolution path

Whoever next works `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` (or owns
`features-service-clean-check`) should: `git stash show -p stash@{0}` in that worktree, determine whether this is (a) an
abandoned experiment (drop the stash), (b) a deliberate rollback that should actually land (investigate why, then commit
with a real message + a Progress Log entry in the dedup plan), or (c) already superseded by a later commit (diff
`stash@{0}` against current HEAD to check). Stash entry:
`slot8-2026-08-07: unexplained staged revert of fleet-workflow-dedup thin-caller-stubs...`.

## Todos

- [ ] [INFRA] P2. Inspect `stash@{0}` in the `features-service-clean-check` worktree (`git stash show -p stash@{0}`) and
      disposition it per the Resolution path above: (a) abandoned experiment — drop the stash; (b) deliberate rollback
      that should land — investigate why, commit with a real message, add a Progress Log entry to
      `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`; or (c) already superseded by a later commit —
      diff `stash@{0}` against current HEAD to confirm, then drop it. Done when: the stash is resolved (dropped or
      landed) and this doc's Progress Log records which of (a)/(b)/(c) applied. Repo: features-service.

## Progress Log

- **2026-08-07 (slot 8, autonomous)**: Found + stashed during unrelated task `defi_satellite_ao_dispatch_batch9-018`.
  Filed this doc per the RED-git-status auto-nudge + existing worktree precedent. Not investigated further -- primary
  task (gas_fees purge VM monitoring, time-critical 45-min threshold validation) resumed immediately.
- **context-scout 2026-08-09**: populated context_scope (3 entries).
- **plan_reconciler 2026-08-10 (cross-cutting tranche)**: this doc had ZERO checkboxes despite `assigned_vm: planning` —
  structurally undispatchable (backlog regen is checkbox-driven). Converted the prose "Resolution path" into a real
  tracked todo above per the HARD RULE (every follow-up is a `- [ ]` todo, never prose). Did not investigate the stash
  myself — out of scope for a plan-reconciliation pass.
