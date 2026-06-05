---
title: Orphaned unmerged work on 7 tab/rootm/* branches (dead root-VM agent slots) — review-or-inherit before deletion
created: 2026-06-05
author: ikennaigboaka [slot-1·laptop]
source:
  - tab/rootm/* cleanup 2026-06-05 (global-unique tab-branch naming follow-up)
  - tab_branch_global_uniqueness (qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md § precondition)
locked_by: live-defi-rollout
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
3. **If genuinely valuable + unmerged** → cherry-pick / rebase onto a current `tab/<vm>/<N>` slot branch, QG-green,
   quickmerge → LDR (inherit the orphan work), then delete the rootm branch.

Until reviewed, these 7 branches are LEFT IN PLACE (deletion would lose the only copy). They no longer pollute the
divergence monitor's signal meaningfully (7 vs the prior 41), and the naming-collision class itself is fixed (no NEW
`tab/rootm/*` can be created — VM-name-scoped prefix + verify-slot-host-symmetry check #11).
