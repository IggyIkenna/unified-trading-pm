---
doc_type: issue
title: Orphaned unmerged work on 7 tab/rootm/* branches (dead root-VM agent slots) — review-or-inherit before deletion
summary:
  "`tab/rootm/*` branches were created by VMs that ran the OLD setup-tab-worktrees.sh as `$USER=root` (prefix collapsed
  to `rootm` — the collision class fixed by the VM-name-scoped prefix, 2026-06-04)..."
status: resolved
nature: process
asset_group: [ao]
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
resolved_by: slot-1 (harsh_pc)
locked_by:
locked_since:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: "2026-07-30"
---

> **🗄️ ARCHIVED 2026-07-30 — MOOT, no cherry-pick needed.** The 7 branches themselves are already confirmed gone
> (2026-07-27 correction below), and the presence-check that was gating archival (does each branch's functionality
> already exist on LDR through other commits?) has now been run directly — every one of the 7 commit-sets is
> superseded-in-spirit by since-independently-developed code, generally more extensively: agent-orchestrator's
> `WorkerLivenessWatchdog` exists (`server/worker_liveness_watchdog.py` + 4 test files); deployment-service's
> consolidator watchdog exists (`vm_zombie_watchdog.py`, `deadman_poster.py`, `cloud_run_job_registry.py`);
> market-tick-data-service's tardis concurrency cap / `book_snapshot_5` handling / `available_from_datetime` filtering
> are all covered far more extensively than the single dead commit-sets (dedicated `test_tardis_concurrency_lease.py`,
> `book_snapshot_5` referenced across a dozen+ files); strategy-service's kill-switch subscriber exists in far more
> complete form (separate subscribers for risk/position/pnl/archetype/scenario, not just one generic update);
> unified-api-contracts' incident/risk/circuit-breaker modules exist (`incident.py`, `risk.py`,
> `registry/circuit_breakers/`); unified-trading-library's cloud-interface messaging module exists verbatim
> (`cloud_interface/messaging.py` + tests); the 7th commit (`ruff format`) is trivial/moot by nature. Nothing was lost —
> later, independent work simply overtook these dead branches' ideas. No cherry-pick, no further review needed.
> Satisfies `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s own "Done when" gate for its rootm-presence-check todo
> (dated verdict + evidence, this section) — flip that todo whenever that plan is next touched.

> **🟡 CORRECTION (2026-07-27)**: this doc's core premise — "7 branches left in place" — is now factually false.
> Independently re-verified fresh via `git ls-remote --heads origin 'tab/rootm/*'` across all 6 named repos
> (agent-orchestrator, deployment-service, market-tick-data-service, strategy-service, unified-api-contracts,
> unified-trading-library): **zero matches in every repo** — the branches no longer exist anywhere, matching the
> 2026-07-26 GitHub-branches-API finding already recorded in
> `/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s todo ("Read-only: is each of the 7 rootm commit-sets'
> functionality on LDR today?", still open as of 2026-07-27). **Disposition is ALREADY RESOLVED** — this is not an open
> A/B/C question: `/plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md` #23 recorded **option A**
> (status: resolved, 2026-07-26) — "Treat as most-likely-superseded, run batch1 todo 9's read-only presence-check,
> archive if all present" — and that presence-check is already correctly scoped as the batch1 todo above (with explicit
> no-push/no-cherry-pick/no-delete guardrails). **Do NOT archive this doc yet**: per its own instruction below, archival
> waits until `/plans/active/ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` writes a dated verdict onto this
> doc — that finalize plan currently only lists the 7-row rootm table as something still to verify (line 61), the batch1
> presence-check todo itself has not executed yet (still `- [ ]`), so no verdict exists here yet.

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

## Todos

- [x] ✅ [OPERATOR] P2. **Review + inherit-or-delete the 7 remaining `tab/rootm/*` branches** — per commit, per repo
      (agent-orchestrator, deployment-service, market-tick-data-service, strategy-service, unified-api-contracts×2,
      unified-trading-library×2): confirm superseded-in-spirit work vs. genuinely valuable unmerged work, then delete or
      cherry-pick+quickmerge accordingly. **RESOLVED 2026-07-30** — the branches are gone (2026-07-27 correction) and
      the presence-check landed a dated verdict directly on this doc (see the ARCHIVED banner above): all 7 commit-sets
      are superseded-in-spirit by since-independently-developed code. No cherry-pick performed or needed; nothing was
      lost.
