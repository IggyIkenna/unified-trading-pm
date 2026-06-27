---
title: quickmerge silently no-ops on a new-file-only ship (untracked --files invisible to the "nothing to merge" guard)
created: 2026-06-23
parent_epic: infrastructure_master
assigned_vm: NA
status: active
priority: P1
source:
  - scripts/quickmerge.sh:1175
  - data_completion_to_100_all_ag_2026_06_21.md (B2 IntraClientRebalanceCoordinator ship, 2026-06-23)
locked_by: live-defi-rollout
---

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
