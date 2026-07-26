---
doc_type: issue
title: Orphaned unmerged work on 7 tab/rootm/* branches (dead root-VM agent slots) — review-or-inherit before deletion
summary:
  "`tab/rootm/*` branches were created by VMs that ran the OLD setup-tab-worktrees.sh as `$USER=root` (prefix collapsed
  to `rootm` — the collision class fixed by the VM-name-scoped prefix, 2026-06-04)..."
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    deployment-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [infrastructure, quickmerge, refactor, orchestrator, migration, plan-hygiene]
related: []
created: 2026-06-05
parent_epic: infrastructure_master
priority: P2
source:
  [
    tab/rootm/* cleanup 2026-06-05 (global-unique tab-branch naming follow-up),
    tab_branch_global_uniqueness (qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md § precondition),
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
---

## What I found

`tab/rootm/*` branches were created by VMs that ran the OLD setup-tab-worktrees.sh as `$USER=root` (prefix collapsed to
`rootm` — the collision class fixed by the VM-name-scoped prefix, 2026-06-04). During cleanup, **34 branches were
deleted** (each either `⊆ live-defi-rollout` or all-commits `git cherry -`-superseded → zero work lost). **7 branches
were KEPT** because they carry commits NOT in LDR (genuine unmerged work from those dead root-VM agent slots, mostly
"agent slot 7"):

| repo                     | branch      | unmerged commits (HEAD-first)                                                                                                                                                            |
| ------------------------ | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| agent-orchestrator       | tab/rootm/5 | `feat(watchdog): WorkerLivenessWatchdog — auto-kill stuck/silent/context-full workers`                                                                                                   |
| deployment-service       | tab/rootm/2 | consolidator liveness watchdog (Cloud Run Job + Scheduler), sharded legacy→canonical tick-bucket migration launcher, vm-launcher token/env fixes, mtds-code SHA-pin (5 commits)          |
| market-tick-data-service | tab/rootm/2 | tardis OKX book_snapshot_5 concurrency cap, solana-defi pyarrow filter-pushdown OOM fix, tardis available_from_datetime symbol filter (5 commits)                                        |
| strategy-service         | tab/rootm/7 | `fix(kill-switch): update kill switch bus subscriber`                                                                                                                                    |
| unified-api-contracts    | tab/rootm/7 | UAC additions: incident module, risk module, instruments catalog, CeFi perp endpoints, alerting thresholds, circuit breaker, predictions canonical groups, databento schemas (2 commits) |
| unified-trading-library  | tab/rootm/2 | `style(manifest): ruff format`                                                                                                                                                           |
| unified-trading-library  | tab/rootm/7 | `feat(cloud-interface): add messaging module and update factory`                                                                                                                         |

## Why it matters

Several look like real, potentially-valuable work (UAC risk/incident modules, mtds data-pipeline fixes, deployment
consolidator watchdog + migration launchers, a UCI messaging module). Some may be **functionally superseded** by
different commits already on LDR (e.g. a `WorkerLivenessWatchdog` and a consolidator watchdog are already described as
shipped in CLAUDE.md) — but they are NOT patch-identical (`git cherry +`), so they weren't auto-classifiable as
superseded. They must be reviewed per commit, not blind-deleted.

## Recommended decision (per the inherited-WIP rule — inherit or surface, never silently drop)

For each of the 7 branches, a slot owning that repo should:

1. Diff the unmerged commits vs current LDR (`git log origin/live-defi-rollout..origin/tab/rootm/<N>` + read the actual
   changes).
2. **If the functionality already exists on LDR** (superseded-in-spirit) → confirm, then
   `git push origin --delete tab/rootm/<N>`.
3. **If genuinely valuable + unmerged** → cherry-pick/rebase the commits into your current slot's clone (already checked
   out on `live-defi-rollout`), QG-green, `quickmerge --agent --files "<paths>"` (inherits the orphan work), then delete
   the rootm branch. **[2026-07-12 correction]** was: "cherry-pick / rebase onto a current `tab/<vm>/<N>` slot branch,
   QG-green, quickmerge → LDR" — the `tab/<vm>/<N>` tab-branch model is RETIRED (since 2026-06-08; each slot is now a
   `git clone --reference` with its own `.git`, checked out directly on `live-defi-rollout` — no tab branch exists to
   rebase onto). Corrected per plan-reconciliation finding 82,
   `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 "50 reclassified" blanket ruling.

Until reviewed, these 7 branches are LEFT IN PLACE (deletion would lose the only copy). They no longer pollute the
divergence monitor's signal meaningfully (7 vs the prior 41), and the naming-collision class itself is fixed (no NEW
`tab/rootm/*` can be created — VM-name-scoped prefix + verify-slot-host-symmetry check #11).
