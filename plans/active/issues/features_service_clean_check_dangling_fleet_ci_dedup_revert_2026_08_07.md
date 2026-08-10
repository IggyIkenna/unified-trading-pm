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
- **slot-15 2026-08-10 (infra craft, investigated)**: `features-service-clean-check` is a linked worktree of slot 8's
  own `features-service` clone (same `.git` object store — stashes are repo-wide, not per-worktree); slot 8 confirmed
  dead (`status: killed`, `worker_alive: false`) before touching it, so no live-session race. Positional drift: the
  target stash is no longer `stash@{0}` (37 stashes deep now) — re-identified it by its exact message text, currently
  `stash@{8}`. **Disposition: (a) abandoned experiment — recommend DROP.** Evidence: (1)
  `git stash show stash@{8} --stat` confirms it reverts exactly the 5 named workflows from thin-caller-stub form back to
  full inline (1450 ins/69 del, matches this doc's own numbers); (2) `git log -1 -- <each file>` shows all 5 last
  touched by `b0c15f11` ("ci: fleet workflows -> thin caller stubs... fleet dedup"), 2026-08-07 — the EXACT commit this
  doc's own "What was found" section cites as the worktree's HEAD when the stash was taken, and HEAD has not moved past
  it since (no newer commit superseded it — ruling out disposition (c), not "superseded", just never-landed); (3)
  current HEAD content is still the thin-stub form (29-58 lines per file, not 200-450+) — the dedup plan
  (`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`) is still `status: active` and lists
  `features-service` among its rolled-out repos, i.e. the thin-stub form is still the currently-desired state, not
  something later reverted-and-then-redone; (4) `gh run list --repo IggyIkenna/features-service` shows 5/5 recent
  `quality-gates-v2` runs green under the current thin-stub CI — no evidence the dedup broke anything for this repo that
  would motivate a genuine rollback. No commit message, branch note, or plan Progress Log entry anywhere corroborates a
  deliberate rollback rationale (disposition (b)) — the balance of evidence is an abandoned local experiment. **Could
  not execute the drop**: `git stash drop stash@{8}` is hard-blocked by
  `agent-orchestrator/scripts/hooks/block_destructive_commands.py` for every autonomous worker, unconditionally (no
  reversibility carve-out, unlike the GCS/S3 delete path) — per `RULES.md` § 1's own guidance ("an unwanted stash gets
  inspected or escalated via a blocked-question... rather than attempting the blocked form"), filing `BLK` recommending
  a human/operator perform the drop directly rather than attempting to circumvent the hook. Todo stays open (stash still
  present, unresolved) pending that action.
