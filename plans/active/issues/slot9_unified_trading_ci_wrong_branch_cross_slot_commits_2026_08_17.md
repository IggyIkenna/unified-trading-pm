---
doc_type: issue
title: slot 9's unified-trading-ci clone is checked out on main (not live-defi-rollout) carrying 3 unpushed commits attributed to slot-2/main-agent
summary: >-
  Slot 9's unified-trading-ci repo clone violates the Path-B invariant (every slot repo
  should be checked out directly on live-defi-rollout) — it is currently on local branch
  `main` (ahead 3 / behind 1 vs origin/main), while its local `live-defi-rollout` branch
  sits 27 commits behind origin/live-defi-rollout, untouched. The 3 ahead commits are
  authored `ikennaigboaka [slot-2·laptop]` and `ikennaigboaka [main·laptop]` — NOT slot 9
  — meaning this is cross-slot/cross-identity contamination, not slot 9's own work. Given
  the unclear provenance and the wrong-branch state, not pushing or otherwise mutating this
  repo myself; flagging for infra triage rather than guessing.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-ci]
scope: [engineer, admin]
tags: [infra, git, wrong-branch, cross-slot, per-tab-worktrees, provenance]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-17"
author: slot-9 (data_engineering)
last_updated: "2026-08-17"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
drift_direction: none
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  Discovered via the orchestrator's own "GIT STATUS RED" auto-nudge (message_ids 9204,
  9208) delivered on /boot to slot 9 while picking up an unrelated data_engineering task;
  investigated per the nudge's own instruction before acting, since the standard remedy
  (`git add . && git commit && git push`) does not cleanly apply to a wrong-branch,
  foreign-attributed state.
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
---

# slot 9's unified-trading-ci clone: wrong branch + cross-slot unpushed commits

## What I found

`cd .tabs/9/unified-trading-ci && git status --porcelain=v1 --branch`:

```
## main...origin/main [ahead 3, behind 1]
```

`git branch -vv`:

```
  live-defi-rollout 2c48c4b [origin/live-defi-rollout: behind 27] fix(semver): base the squash-promote PATCH-fallback on repo-wide source_touched, not SOURCE_DIR-prefix
* main              403c921 [origin/main: ahead 3, behind 1] fix: update before downstream merge
```

The clone is currently checked out on `main`, not `live-defi-rollout` — a direct violation of the Path-B
topology invariant (`/codex/05-infrastructure/per-tab-worktrees.md`: "each slot `.tabs/<N>/<repo>` is its OWN
`git clone --reference` checked out **directly on `live-defi-rollout`**"). The local `live-defi-rollout` branch
exists but is 27 commits stale — nobody has advanced it in this clone in some time (my session's own
fresh-pull loop this morning fast-forward-merged `origin/live-defi-rollout` onto whatever branch was checked
out at the time, silently succeeding without verifying branch identity — worth noting as a secondary gap in
the fresh-pull script itself, since it never asserts `git branch --show-current == live-defi-rollout`).

The 3 commits ahead of `origin/main`:

```
403c921 2026-08-16T19:03:20+01:00 ikennaigboaka [slot-2·laptop] fix: update before downstream merge
799f0f3 2026-08-16T19:10:14+01:00 ikennaigboaka [main·laptop] chore: merge origin/main into live-defi-rollout (sync Slack alert streak-sha linking commit)
3932f64 2026-08-16T19:09:31+01:00 ikennaigboaka [main·laptop] ci: add self_hosted_runner_labels input to image-build-validate.yml
```

None of these carry a `slot-9` identity — they're attributed to `slot-2` and the `main` agent, both on a
`laptop` host, not this VM. This is NOT slot 9's own in-flight work sitting here; it is either (a) leftover
state from when this clone (or its underlying `--reference` object store) was used by a different
slot/session before being reassigned to slot 9, or (b) some cross-checkout contamination worth its own root
cause. The commit subjects themselves look like real, intentional work (a semver-related merge-reconciliation
+ a CI workflow input addition), not scratch/garbage — i.e. this is probably real work that never finished
landing, not something safe to just discard.

## Why it matters

Per CLAUDE.md's Multi-agent safety section, a slot's HEAD must stay ancestor-or-equal of
`origin/live-defi-rollout` — this clone currently satisfies neither that invariant (wrong branch entirely) nor
does pushing the 3 `main`-branch commits obviously reconcile it, since their content and authorship don't
belong to this slot. Blindly pushing risks landing foreign, possibly-stale work under unclear conditions;
blindly discarding risks losing real work. Left as a standing GIT STATUS RED nudge, this will keep
re-triggering the orchestrator's auto-nudge on every dispatch to slot 9 without ever resolving, since the
standard remedy doesn't fit.

## Recommended decision

An infra-craft worker (or the main agent, given two of the three commits are attributed to it) should
determine: (1) whether these 3 commits' content is already landed elsewhere under a different sha (in which
case this branch state is just stale and can be reset to track `live-defi-rollout` cleanly), or (2) whether
they represent real unlanded work that needs to be cherry-picked/reconciled onto `live-defi-rollout` properly
via quickmerge, or (3) whether slot 9's `unified-trading-ci` clone itself needs to be re-cloned/repaired to
restore the Path-B invariant. Not resolving this myself — outside my task's scope and craft, and the
provenance is too unclear to act on unilaterally.

## Todos

- [ ] [INFRA] P2. Investigate slot 9's `unified-trading-ci` clone: reconcile or discard the 3 `main`-branch
      commits attributed to `slot-2`/`main` (see commit shas above), then re-checkout the clone onto
      `live-defi-rollout` and fast-forward it to `origin/live-defi-rollout` (currently 27 commits stale) to
      restore the Path-B invariant. Repo: unified-trading-ci (slot 9 clone specifically). Done when: `git branch
      -vv` in that clone shows `live-defi-rollout` checked out and current, with no stray `main`-branch ahead
      commits.
- [ ] [INFRA] P3. Check whether `agents/worker.md`'s fresh-pull loop (RULES.md §1b) should assert
      `git branch --show-current == live-defi-rollout` before its `git merge --ff-only` step, since it silently
      succeeded against whatever branch was checked out here without ever surfacing the wrong-branch state.
      Repo: unified-trading-pm. Done when: either the assertion is added, or a note explains why it's
      intentionally lenient.

## Progress Log

- **2026-08-17 (slot 9, data_engineering)**: filed after investigating a recurring "GIT STATUS RED" auto-nudge
  (message_ids 9204, 9208) that didn't fit the standard remedy. Not pushed/reset/touched — flagging for infra
  triage given foreign commit provenance and unclear resolution.
