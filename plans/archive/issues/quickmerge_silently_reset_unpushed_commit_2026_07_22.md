---
doc_type: issue
title:
  "quickmerge.sh --agent silently reset a repo's OWN unpushed commit back to origin mid-run (root cause unconfirmed) —
  recovered, no data lost"
summary: >-
  During the defi_consolidated_closeout_2026_07_18.md session, `bash scripts/quickmerge.sh "..." --agent --files
  'unified_trading_library/__init__.py'` in unified-trading-library committed a small, fully quality-gate-verified
  change (top-level re-export of the DeFi token-metadata resolver), then invoked quickmerge, which printed only STAGE 0
  (cascade_dep_branch, correctly scoped to the ancestor unified-api-contracts) followed by "Nothing to commit — exiting
  fast" (quickmerge.sh:508) and exited 0. Immediately after, `git log --oneline -1` showed HEAD back at `a45056d9` — the
  PRE-commit state — with the just-committed content gone from the branch. `git reflog` confirmed: `7b06340b
  HEAD@{2026-07-22 02:01:35}: commit: fix(defi): top-level re-export...` followed two minutes later by `a45056d9
  HEAD@{2026-07-22 02:04:15}: branch: Reset to origin/live-defi-rollout` + `a45056d9 HEAD@{2026-07-22 02:04:15}:
  checkout: moving from live-defi-rollout to live-defi-rollout`. The commit object itself survived (dangling, `git
  cat-file -t 7b06340b` → `commit`) and was recovered via `git checkout -B live-defi-rollout 7b06340b`. Investigated but
  could NOT confirm root cause: (1) `cascade_dep_branch` (quickmerge.sh:362-470) only ever `cd`s into ANCESTOR repo
  directories inside a `(...)` subshell before running `git checkout -B`, and its own printed trace showed it only
  touched unified-api-contracts (confirmed separately: unified-api-contracts's OWN reflog shows 3 harmless resets to a
  commit it was already AT, at 02:01:43/02:04:16/ 02:07:32 — real but no-op, unrelated to the destructive one); (2) the
  workspace's `slot-cron-ff-pull.sh` (`*/5 * * * *` cron, `/tmp/slot-cron-ff-pull.log`) explicitly documents itself as
  non-destructive ("Never destructive. Never runs merge --no-ff, never rebase, never reset --hard") and has an explicit
  ahead-only skip path (`[skip:ahead] ... N unpushed commit(s)`) — its own log shows NO entry for
  unified-trading-library in the 01:04Z-01:05Z window (the incident's UTC-equivalent timestamp), which argues against it
  being the cause; (3) the ONLY other `git checkout -B "$branch" "origin/$branch"` call sites in quickmerge.sh (lines
  1388, 1409) are inside STAGE 5+ (Create PR), which is unreachable after the STAGE-0-then-"nothing to commit"-exit
  trace actually printed. No confirmed root cause. On retry (same commit, re-run minutes later with a fresh QG sentinel)
  quickmerge shipped cleanly with no recurrence — so this may be a rare race (e.g. the `git fetch origin main --quiet`
  at quickmerge.sh:506 racing against something), not a deterministic bug.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library]
scope: [engineer, admin]
tags: [quickmerge, data-loss, git-safety, race-condition, agent-workflow, unconfirmed-root-cause]
related:
  [
    plans/active/issues/quickmerge_agent_sentinel_race_vs_own_rebase_2026_07_16.md,
    plans/active/issues/quickmerge_sentinel_invalidated_by_its_own_autopull_2026_07_18.md,
    codex/08-workflows/ci-cd-flow.md,
    plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-22
priority: P1
parent_epic: deployment_and_user_management_master
source: "Hit live while shipping defi_consolidated_closeout_2026_07_18.md Track 1 work, slot-4, 2026-07-22"
execution_scope: local-only
drift_direction: neutral
depends_on: []
assigned_vm: NA
resolved_by: unified-trading-pm@06dc7632
locked_by:
last_updated: 2026-07-22
---

# quickmerge.sh silently reset an unpushed commit (root cause unconfirmed)

## What happened

1. `unified-trading-library`: committed `7b06340b` (small, QG-verified, additive change).
2. Ran `bash scripts/quickmerge.sh "..." --agent --files 'unified_trading_library/__init__.py'`.
3. Output showed ONLY: STAGE 0 cascade (ancestor `unified-api-contracts` correctly touched, confirmed no-op) →
   `[unified-trading-library] Using .venv...` → `Installing project dependencies...` →
   `[unified-trading-library] Nothing to commit — exiting fast` → exit 0.
4. `git log --oneline -1` immediately after: `a45056d9` (the commit's PARENT — my commit was gone).
5. `git reflog` confirmed a `Reset to origin/live-defi-rollout` + same-second `checkout` entry landed between the commit
   and the "Nothing to commit" print.

## Impact

None — caught immediately (this session's own established pattern of verifying `git log`/`git status` after every
git-affecting step), recovered via `git checkout -B live-defi-rollout 7b06340b` (the commit object was never garbage
collected — dangling but intact), re-shipped successfully on retry. Documented here because a less-careful session would
have silently lost the commit and re-done the work, or worse, believed it shipped when `quickmerge.sh` exited 0.

## What was ruled out

- **`cascade_dep_branch`'s own checkout (line 448)**: correctly subshell-scoped (`cd "$ancestor_path"` before any git
  command); its OWN printed trace + the ancestor repo's OWN reflog confirm it only ever touched `unified-api-contracts`,
  and only as a harmless no-op (already at that commit).
- **`slot-cron-ff-pull.sh`**: explicitly documented as non-destructive with an ahead-only skip path; its log
  (`/tmp/slot-cron-ff-pull.log`) shows no entry for `unified-trading-library` in the incident's time window.
- **quickmerge.sh:1388/1409** (`STAGE 5: Create PR`'s own `git checkout -B`): unreachable given the trace shows the
  script exited at the STAGE-0-adjacent "Nothing to commit" line (508), before STAGE 5.

## What's NOT ruled out

- A race in `git fetch origin main --quiet` (quickmerge.sh:506, right before the "Nothing to commit" check) — if this or
  something it triggers internally does more than fetch under some condition, that's the remaining unexplored code path.
- A concurrent process outside quickmerge.sh entirely (this host had another slot's `quality-gates.sh` running against a
  DIFFERENT `.tabs/3` clone at the same time — confirmed via `ps`/`lsof`, but that's a separate `.git` directory and
  should be unable to touch `.tabs/4`'s checkout).
- Non-reproducible on retry (same commit message + files, minutes later, clean ship) — consistent with a rare race
  rather than a deterministic logic bug, which makes this harder to root-cause from a single occurrence.

## Recommended follow-up (not done this session — filing, not fixing blind)

- Add a defensive post-STAGE-0 assertion in quickmerge.sh: after `cascade_dep_branch` returns, verify
  `git rev-parse HEAD` in the CALLING repo still matches what it was before STAGE 0 ran (a one-line guard that would
  have turned this into a loud, actionable failure instead of a silent no-op "Nothing to commit").
- If this recurs, capture `bash -x` trace output (or `set -x` around STAGE 0) to catch the exact command that runs the
  reset — this session's investigation was necessarily after-the-fact (reflog + log-grepping), which could rule
  candidates OUT but not conclusively identify the actual culprit.

## Workaround used this session

Verify `git log --oneline -1` + `git status --porcelain` immediately after every `quickmerge.sh` invocation, before
treating a `--files`-scoped ship as done. This is already this session's standing practice (per the workspace's
commit-push-flip-rule + async-wait-discipline rules); this incident is the concrete case that validated why the
verification step matters even for a "boring" single-file ship.

## Root cause CONFIRMED (2026-07-22) — `cascade_dep_branch`'s unconditional `checkout -B`

Found while investigating the sibling doc `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` and re-reading
`cascade_dep_branch()` (`scripts/quickmerge.sh:362-470`) line by line rather than trusting the earlier "only touched
unified-api-contracts, ruled out" conclusion — that conclusion checked THIS session's own cascade trace, but never
considered a **different, concurrent** slot's quickmerge invocation.

`cascade_dep_branch(branch_name)` walks every transitive internal-dependency ancestor of the repo being shipped (via
`workspace-manifest.json`) and, for each ancestor, `cd`s into `$WORKSPACE_ROOT/$ancestor` — a **single shared directory
on the host, not a private per-slot worktree** — and runs, unconditionally:

```bash
git checkout -B "$branch_name" "origin/$branch_name" --quiet
```

`checkout -B` **resets** `refs/heads/$branch_name` to `origin/$branch_name` regardless of whether the local branch
already has commits ahead of origin. Dirty (uncommitted) changes are protected via `git stash push -u` immediately
before this — but a **committed, unpushed** commit is not stashed and is silently discarded. The git reflog message this
produces is literally `branch: Reset to origin/<branch>` — an EXACT match for both this doc's and the sibling doc's
observed reflog signature — and since `checkout -B` never deletes the commit object (only moves the ref), it remains
recoverable via reflog until the next gc, matching both docs' "recovered, nothing permanently lost" finding.

`branch_name` is routinely the fleet's own integration branch (`live-defi-rollout`), which is also normally what's
checked out in every ancestor clone — so **any** concurrent agent's `quickmerge.sh --dep-branch <name>` invocation
(cascading to that branch) that walks through a widely-depended-upon ancestor like `unified-trading-library` or
`unified-api-contracts` can silently wipe out a **different agent's** committed-but-unpushed work sitting in that shared
clone, with zero warning. This is the confirmed mechanism for both this doc AND
`utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` (same repos affected, same reflog signature, same
recoverable-via-reflog profile).

**Fixed**: `unified-trading-pm@06dc7632`. Before the `checkout -B`, if `refs/heads/$branch_name` already exists with
commits ahead of `origin/$branch_name`, its tip is preserved to a named, content-addressed local ref
(`refs/wip-preserve/cascade-<ancestor>-<sha12>`) via `git update-ref` — durable (survives independently of reflog
expiry), loudly logged with the exact recovery command, and a no-op for the common case (no local-ahead commits).
Verified against a real git fixture reproducing the exact incident (ahead-by-1 commit → checkout -B discards it from the
branch → but it's fully recoverable via the preserve ref → `git checkout -B <branch> <preserve-ref>` restores it). STAGE
5's own two `checkout -B` call sites (lines ~1475/1496) were checked and are **not** affected — both already gate on
`refs/heads/$BRANCH` existing first and only fall through to `checkout -B` when there is no pre-existing local branch to
lose, unlike the ancestor-cascade call site which reset unconditionally.

**Not addressed**: pushing the preserve ref for durability beyond the local clone (deliberately out of scope — adds
network dependency to a step every concurrent agent's cascade calls). Also not addressed: this doc's own earlier "the
ONLY remaining unexplored path is a race in `git fetch origin main --quiet`" hypothesis is now superseded — the actual
mechanism was a **different session's** cascade, not a race inside this session's own run.
