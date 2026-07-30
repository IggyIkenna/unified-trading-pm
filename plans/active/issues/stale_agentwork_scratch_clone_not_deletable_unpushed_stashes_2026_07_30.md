---
doc_type: issue
title: >-
  Stale `instruments-service-agentwork-sports-2026-07-13/` scratch clone was NOT deleted as instructed — its tracked
  work is provably already shipped, but 10 lingering stash entries (~5,000 lines of diffs spanning 2026-07-09..07-25)
  are unproven-unpushed WIP and deleting the directory would drop them irrecoverably
summary: >-
  Operator instruction 2026-07-30 was "delete the stale scratch clone, but FIRST confirm nothing unpushed; if it has
  real unpushed work, do NOT delete it, report that instead." The confirmation step FAILED OPEN on the stash stack. The
  clone's tracked content is clean: its one non-remote branch commit (`bc53bafe`, the catalogue-enumeration-gap script +
  test) and its one untracked file (`sports_attempted_failed_residual_closer_2026_07_13.py`) are BYTE-IDENTICAL to
  versions already on `origin/live-defi-rollout` in the real `instruments-service` clone (`f6f16785` and `98e7a784`
  respectively) — verified by diff, zero delta. But `git stash list` holds 10 entries dated 2026-07-09 through
  2026-07-25 (2 named checkpoints + 1 `quickmerge-36591` + 7 bare `autostash` residue) totalling roughly 5,000 lines of
  diff across adapters, goldens, orchestrator internals and docs. NONE of the 10 reverse-apply cleanly against the
  current `instruments-service` tree, so none is provably already-shipped — though three weeks of surrounding drift is
  sufficient on its own to explain a failed context match, so that is NOT evidence they contain unique work either. It
  is simply unproven in both directions. Per the operator's own stated condition, and per the workspace HARD RULE that
  destroying a stash is UNRECOVERABLE, the directory was left in place (1.2 GB) pending a ruling. The QG false-positive
  that motivated the deletion is independently FIXED and no longer depends on this directory going away.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, instruments-service]
scope: [engineer, admin]
tags: [cleanup, git, stash, scratch-clone, quality-gates, disk]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /cursor-configs/SUB_AGENT_MANDATORY_RULES.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: NA
drift_direction: flat
source: ["2026-07-30 operator instruction to delete the stale scratch clone (infra-methodology fix pass)"]
resolved_by:
locked_by:
---

# Stale agentwork scratch clone — deletion blocked on unproven stash WIP

Directory: `unified-trading-system-repos/.tabs/3/instruments-service-agentwork-sports-2026-07-13/` (1.2 GB, local to
slot 3 only — never pushed anywhere, not part of the per-slot worktree model).

## What was verified (all measured this session, nothing inferred)

| Surface                                           | Finding                                                                                                    | Safe to drop?                                                              |
| ------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `git status --porcelain`                          | 1 untracked file: `scripts/backfill/sports_attempted_failed_residual_closer_2026_07_13.py`                 | YES — byte-identical to `origin/live-defi-rollout` (`98e7a784`)            |
| Branch `agentwork/sports_residual_fix_2026_07_13` | 0 commits not reachable from a remote                                                                      | YES — nothing unique                                                       |
| Branch `backup-catalogue-gap-script-2026-07-23`   | 1 commit `bc53bafe` (measure script 407L + test 298L)                                                      | YES — both files byte-identical to `origin/live-defi-rollout` (`f6f16785`) |
| `refs/stash` (10 entries, 2026-07-09..07-25)      | ~5,000 lines of diff: adapters, expected-universe goldens, orchestrator internals, `docs/*_INSTRUMENTS.md` | **UNKNOWN — this is the blocker**                                          |
| `live-defi-rollout` / `main` local branches       | behind remote (2 / 1573), no local-only commits                                                            | YES                                                                        |

`git log @{u}..` on the checked-out branch reports `no upstream configured` (an `agentwork/` branch never had one), so
the operator's suggested command alone does not answer the question — `git rev-list --count --all --not --remotes` is
the check that does, and it returns 3 (the one branch commit above + the 2 commit objects behind `stash@{0}`).

## Why this is not just "drop the stashes"

`git stash drop` on foreign/unproven WIP is UNRECOVERABLE and is a named HARD RULE in both
`/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` § Foot-guns and `/cursor-configs/CLAUDE.md` § Multi-agent safety.
Deleting the directory drops all 10 at once with no undo. The already-applied test (`git apply --reverse --check` of
each stash's diff against the current `instruments-service` tree) came back negative for all 10 — but that test has a
known false-negative mode here: three weeks of surrounding churn defeats the context match even for content that DID
ship. So the honest verdict is **unproven, not unsafe** — which under the operator's own stated condition ("if it has
real unpushed work, do NOT delete it") means: do not delete.

## The motivating QG failure is already fixed, independently of this

The stated reason for the deletion was that this directory read as a real repo to
`scripts/quality_gates/check_repo_docs_ssot.py` (its `_iter_repo_docs()` `iterdir()`s every workspace sibling), so its
frozen 3-week-old `docs/` contributed 6 non-baselined violations and failed the gate. That is fixed at the source: the
script now skips `*-agentwork-*` / `scratch-clone` / dot-prefixed directories (`_is_scratch_clone()`), mirroring
`check_frontmatter_schema.py`'s `.claude/`-worktree exclusion. **The gate is green with the directory still present** —
so nothing is blocked on this decision; the only remaining cost is 1.2 GB of disk.

## Todos

- [ ] [OPERATOR] P2. Rule on how to retire `.tabs/3/instruments-service-agentwork-sports-2026-07-13/`. **Options:** **A
      [WORKER REC]: bundle-then-delete** — `git bundle create <archive>.bundle --all refs/stash` plus the reflog'd stash
      commits into a durable location, verify the bundle lists all 10 stash objects, THEN delete the directory. Reclaims
      the 1.2 GB, keeps every byte recoverable, and costs a few MB. **B: delete outright** — accept losing 10 stashes of
      3-week-old WIP on the reasoning that anything that mattered shipped through the real clone weeks ago (defensible,
      but unprovable, and irreversible). **C: leave it** — zero risk, keeps paying 1.2 GB and leaves a directory that
      future tooling must keep remembering to exclude. **Other**: operator can type a custom answer. **Done when**: the
      directory is either gone (A or B) or explicitly recorded as KEEP with a re-review date (C).
- [ ] [SCRIPT] P3. If option A is ruled: write the bundle, verify it (`git bundle verify` + confirm all 10 stash commits
      are listed), record the bundle path here, and only then delete the directory. **Done when**: the bundle verifies,
      its path is cited in this doc, and the source directory no longer exists.
