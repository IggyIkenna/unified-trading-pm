---
doc_type: issue
title:
  git pull --rebase --autostash silently restores FOREIGN dirty files into the INDEX, so a by-name `git add` still
  commits another agent's uncommitted work — the stage-by-name rule gives no protection in a shared checkout
summary:
  The multi-agent safety rule is "stage by name, never git add . / -A", on the assumption that naming your own files is
  sufficient to keep a concurrent agent's uncommitted work out of your commit. In a shared per-slot checkout it is NOT.
  git pull --rebase --autostash (the reconcile step quickmerge STAGE 0.4 and every drift-recovery recipe tell you to
  run) stashes the WHOLE dirty tree - including files owned by other agents - and the pop restores them into the INDEX,
  i.e. already staged. A subsequent git commit commits the index, so it sweeps up every foreign file regardless of what
  you passed to git add. Measured 2026-07-17 - commit unified-trading-pm 1a59516af was intended to add ONE new issue
  doc; it landed with 3 files, silently publishing another agent's in-progress plan edits (157 insertions / 125
  deletions of real content, not a reformat) and a brand-new issue doc they had not yet committed, under this slot's
  authorship and commit message. No data was lost - the content is intact on origin - but their WIP was published
  earlier than intended and mis-attributed. The existing codex guidance only covers the autostash CONFLICT path ("rebase
  --abort + stash by name"); this is the NON-conflict happy path, which is why it is easy to miss. The pre-commit "git
  diff --cached --stat (NO path arg)" inspection step is the one control that would catch it, and it only works if the
  agent actually reads the file list rather than the summary line.
status: open
resolved_by:
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [multi-agent-safety, git, autostash, shared-checkout, foreign-wip, process, big-finding, commit-hygiene]
related: [/plans/archive/issues/sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17.md]
created: 2026-07-17
source:
  - Self-caught 2026-07-17 while committing an issue doc to unified-trading-pm, then flagged by the operator ("sure flag
    it"). Found by actually reading `git show --stat` on the pushed commit rather than trusting that `git add
    <one-file>` had scoped it - the pre-commit status check had shown the foreign files as "not staged", which is what
    made the sweep invisible until after the push.
assigned_vm: NA
assigned_role: devops
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
drift_direction: advance-code
parent_epic: agent_operating_framework_master
execution_scope: local-only
depends_on: []
last_updated: 2026-07-17
locked_by:
locked_since:
---

# `--autostash` restores foreign WIP into the index → by-name `git add` does not scope your commit

## The failure, measured

`unified-trading-pm@1a59516af` was meant to add one new file. It shipped three:

```
157  125   plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md   <- FOREIGN, real content
187    0   plans/active/issues/sports_fixture_round_..._2026_07_17.md            <- mine (intended)
118    0   plans/active/issues/tradfi_instrument_type_migration_..._2026_07_17.md <- FOREIGN, new file
```

The sequence that produced it (all of it "correct" per the current rules):

```bash
git pull --rebase --autostash origin live-defi-rollout   # reconcile — mandated by the drift recipe
git add plans/active/issues/<my-one-doc>.md              # stage BY NAME — the rule
git commit -F msg                                        # commits the INDEX → swept 2 foreign files
```

## Why the stage-by-name rule does not protect you

`--autostash` = `git stash` + restore. The restore re-applies the stashed changes **and their index state**. Foreign
files that were merely dirty in the working tree come back **staged**. `git commit` then commits the whole index — the
`git add <file>` you ran is irrelevant, because those foreign paths are already in it.

This is the **non-conflict** path. Existing guidance (`/codex/05-infrastructure/per-tab-worktrees.md`, CLAUDE.md
"Multi-agent safety") only addresses the conflict path — _"autostash conflict → `rebase --abort` + stash by name (never
`git stash drop` foreign WIP)"_ — so an agent doing everything right, on the happy path, still sweeps.

It is invisible pre-commit: `git status` correctly reports the foreign files as **"Changes not staged for commit"**
right up until the pull, and the post-pull index is never re-inspected.

## Impact

- **Not data loss.** Content is intact and on origin.
- **Mis-attribution + premature publication.** Another agent's in-progress work is published under your slot's name and
  commit message, before they chose to ship it. On a shipping-gated repo that can push someone else's half-finished
  change past a gate they intended to run themselves.
- **Silent.** Nothing fails. The only tell is reading `git show --stat` AFTER the push.
- The blast radius scales with how dirty the shared checkout is — and PM is routinely dirty across many agents.

## Candidate fixes (not yet decided)

- [ ] [DEVOPS] P2. Make the MANDATORY pre-commit inspection catch it: the rule already says run
      `git diff --cached --stat` (NO path arg) — but it must be run **AFTER** the pull/autostash, not before, and the
      agent must diff the staged list against the files they intend. Codify the ordering explicitly; today the recipe
      reads pull → add → commit with the inspection floating.
- [ ] [DEVOPS] P2. Prefer `git stash push -- <my paths>` + `git pull --ff-only` + `git stash pop` over `--autostash`
      when the tree contains files you do not own, OR `git restore --staged .` immediately after the pull and re-add by
      name (cheap, deterministic, no reliance on stash index semantics).
- [ ] [DEVOPS] P3. Consider a pre-commit hook that FAILS when the staged set contains paths the invoking agent did not
      explicitly name (e.g. compare against a `QM_FILES`-style env the wrapper sets) — the machine guard equivalent of
      the `Quickmerge:` trailer check. Would have blocked 1a59516af.
- [ ] [DOCS] P2. Fold the non-conflict autostash hazard into `/codex/05-infrastructure/per-tab-worktrees.md` +
      CLAUDE.md's Multi-agent safety block — currently both only warn about the conflict path, which is the rarer case.

## Do NOT "fix" a sweep by reverting

Once pushed, the foreign content is the other agent's only committed copy of that work. A revert or force-push to "clean
up" the attribution **deletes their uncommitted work** — turning a cosmetic problem into real data loss, and
force-pushing a shared branch is independently banned. The correct response is: leave it, tell the operator, and let the
owning agent carry on (their tree simply shows those files as already-committed after their next pull).
