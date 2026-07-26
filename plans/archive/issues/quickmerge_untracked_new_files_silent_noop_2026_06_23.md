---
doc_type: issue
title: quickmerge silently no-ops on a new-file-only ship (untracked --files invisible to the "nothing to merge" guard)
summary:
  "`scripts/quickmerge.sh:1175` short-circuits with **`No differences from main — nothing to merge`** when the unit
  being shipped is composed **entirely of NEW (untracked) files**:"
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [quickmerge, quality-gates, scripts, infrastructure, verification]
related: []
created: 2026-06-23
parent_epic: infrastructure_master
priority: P1
source:
  [
    "scripts/quickmerge.sh:1175",
    "data_completion_to_100_all_ag_2026_06_21.md (B2 IntraClientRebalanceCoordinator ship, 2026-06-23)",
  ]
assigned_vm: NA
resolved_by: unified-trading-pm@04c0eef0e (fix) + unified-trading-pm@3ddd1a4f2 (regression test)
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-26
---

> **🟢 RESOLVED 2026-07-26** — fix shipped `unified-trading-pm@04c0eef0e`, regression test
> `unified-trading-pm@3ddd1a4f2` (`scripts/quality-gates-base/tests/test-quickmerge-untracked-new-file-guard.sh`),
> tracking-home P0 in `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` flipped done, closed via AO batch
> `ci_satellite_ao_dispatch_batch1_2026_07_26.md` todo 1. Archived — no deferred work.

## What I found

`scripts/quickmerge.sh:1175` short-circuits with **`No differences from main — nothing to merge`** when the unit being
shipped is composed **entirely of NEW (untracked) files**:

```bash
# quickmerge.sh:1175
if git rev-parse origin/main &>/dev/null && [ -z "$(git diff origin/main 2>/dev/null)" ]; then
  echo "[$REPO_NAME] No differences from main — nothing to merge"
```

`git diff origin/main` (worktree vs commit, no `--cached`) does **not** see untracked files. So when
`quickmerge --agent --files '<new-file-a> <new-file-b>'` is run and every `--files` path is a brand-new untracked file,
the guard reads an empty diff → concludes "nothing to merge" → **exits before staging/committing the `--files`**. The
ship silently produces NOTHING (no commit, no LDR push, no staging PR) while exiting cleanly — the same dangerous "ships
NOTHING" class as the documented clean-tree early-exit, but triggered on a DIRTY tree whose only changes are new files.

Reproduced 2026-06-23 shipping the `IntraClientRebalanceCoordinator` unit (`strategy_service/transfer_coordinator.py` +
`tests/unit/transfer_coordinator/` — all new files): three `quickmerge --agent --files` runs each printed "No
differences from main — nothing to merge" and left the files untracked. Contrast: line 508
(`[ -z "$(git status --porcelain)" ] && git diff origin/main --quiet`) correctly uses `git status --porcelain` (which
DOES include untracked) for its own clean-tree gate — line 1175 is the inconsistent one.

## Why it matters

A new-module ship (a brand-new file + its new test dir — extremely common) silently no-ops. The agent reads exit 0 +
"nothing to merge" and can wrongly believe the unit shipped, or burns several quickmerge cycles diagnosing. It defeats
the strict-quickmerge ship path for exactly the case it should handle cleanly. Cross-cutting: `quickmerge.sh` is the PM
SSOT symlinked into every repo, so the fix is fleet-wide.

## Workaround (used 2026-06-23)

`git add` the new `--files` BEFORE running quickmerge, so `git diff origin/main` (now seeing the staged-new files as
additions) is non-empty and the guard passes. The coordinator ultimately shipped via a hand Pass-2 commit carrying the
`Quickmerge: agent` trailer (`strategy-service@1450019e`) from the QG-green tree, since the quickmerge churn (rapid LDR
version bumps from a concurrent promotion cascade) compounded the issue.

## Recommended decision

Fix line 1175 to account for untracked `--files`: gate on `git status --porcelain` being empty (consistent with
line 508) rather than only `git diff origin/main`, OR when `--files` are explicitly supplied, stage them before the
guard (quickmerge already re-asserts `--files` scope on the commit-retry). Add a regression: a new-file-only
`quickmerge --agent --files <newfile>` must produce a commit. Owner: whoever owns `cicd_quality_gates_2026_06_18.md`
(the structured-quickmerge / QUICKMERGE_BLOCKED contract lives there). Low-risk 1-liner but it changes fleet-wide ship
behaviour, so it wants a deliberate test, not a hot-patch under time pressure.

> **[2026-07-12 correction, finding 348, §A2 B-queue**
> (`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`)**]**: the "Owner" pointer above is doubly
> dead — `cicd_quality_gates_2026_06_18.md` was superseded 2026-06-24 into `cicd_consolidated_remaining_2026_06_24.md`,
> which was itself superseded 2026-06-30 by `plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` (verified via
> both docs' own `status: superseded` / `superseded_by` frontmatter). `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md`,
> which declares itself the sole current SSOT for the pipeline/quickmerge area, does not mention this bug (grep for
> "untracked"/"1175" returns zero hits there). Re-verified 2026-07-12: the underlying bug is still live — current
> `scripts/quickmerge.sh` line ~1188 still gates only on `git diff origin/main` (untracked-blind), unchanged. This P1
> bug is therefore untracked by any live plan; not reassigned here (picking a new owner is an operator/triage call, out
> of this chunk's file scope) — flagging so the next triage pass routes it (candidate:
> `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md`, since it claims exclusive current SSOT status for this exact contract).

> **[2026-07-14 correction, findings 107/201]**: routed per the candidate above — this bug is now recorded as an open P1
> todo in `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` Phase 2 (its pipeline/quickmerge health-work section), so it is
> no longer untracked by any live plan. Fix itself is still NOT implemented — this only closes the tracking/ownership
> gap, not the underlying bug.

> **[2026-07-26 RESOLVED]**: the fix landed in `unified-trading-pm@04c0eef0e` — the guard at (now) `quickmerge.sh`
> ~L1237 ALSO checks `git status --porcelain -- $FILES_ARG` (scoped to the supplied `--files`, mirroring the existing
> `git status --porcelain` clean-tree guard) so a brand-new untracked `--files` path falls through instead of
> early-exiting as "No differences from main". The deliberate regression test called for above is
> `scripts/quality-gates-base/tests/test-quickmerge-untracked-new-file-guard.sh` (extracts the real guard from
> `quickmerge.sh`, not a replica; 4 fixture cases — confirmed it fails 2/4 against the pre-fix commit and passes 4/4
> against the fix, so it actually reproduces this bug rather than trivially passing). Tracking-home P0 in
> `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` flipped to done in the same batch. Closed via AO batch
> `ci_satellite_ao_dispatch_batch1_2026_07_26.md` todo 1.
