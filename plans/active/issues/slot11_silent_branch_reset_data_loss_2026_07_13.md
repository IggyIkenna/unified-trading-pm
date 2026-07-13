---
doc_type: issue
title: Slot 11 — an external process silently `git reset`-discarded 2 committed local commits (UTL + UAC)
summary:
  During a normal /boot task on slot 11, two already-committed local commits (unified-trading-library@a0ef1d67,
  unified-api-contracts@164a3937) vanished from HEAD — git reflog shows "Reset to origin/live-defi-rollout" entries I
  did not issue myself. Both commits were recovered via `git cherry-pick` from reflog; no work was permanently lost this
  time, but the mechanism is unidentified and could silently destroy uncommitted OR committed agent work fleet-wide.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags: [git-safety, incident, slot-infrastructure, data-loss-risk]
related: [codex/05-infrastructure/per-tab-worktrees.md]
created: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
author: slot-11
source: [utl_reuse_phase7_low_lint_tail_2026_07_13.md, slot-11 backend-engineer task]
resolved_by:
locked_by:
---

# Slot 11 — an external process silently `git reset`-discarded 2 committed local commits

## What I found

While shipping `utl_reuse_phase7_low_lint_tail_2026_07_13.md` from slot 11, I committed locally (not yet pushed) in 5
repos. Roughly ~20-25 minutes later, when I went to inspect 2 of those repos again, the commits were GONE from `HEAD` —
replaced by whatever `origin/live-defi-rollout` pointed to at that moment. `git reflog` in both repos shows the smoking
gun:

```
unified-trading-library:
a90da8f6 HEAD@{0}: checkout: moving from live-defi-rollout to live-defi-rollout
a90da8f6 HEAD@{1}: branch: Reset to origin/live-defi-rollout
a0ef1d67 HEAD@{2}: commit: feat(risk): add leg_snapshot_builder ...   <- MY COMMIT, DISCARDED

unified-api-contracts:
48bfadff HEAD@{1}: checkout: moving from live-defi-rollout to live-defi-rollout
48bfadff HEAD@{2}: branch: Reset to origin/live-defi-rollout
164a3937 HEAD@{3}: commit: fix(registry): sanction execution-service's ...   <- MY COMMIT, DISCARDED
```

Both `HEAD@{1}`/`HEAD@{2}` reflog messages say **"branch: Reset to origin/live-defi-rollout"** — this is NOT a
`git merge --ff-only` (which I used everywhere else and which produces a `merge: Fast-forward` reflog line, visible
elsewhere in the same reflogs) and NOT anything I ran myself (I never issued `git reset` in either repo this session).
Something ELSE — running with write access to my slot's repo clones — reset the branch ref straight to
`origin/live-defi-rollout`, silently discarding my already-committed work. The working tree was ALSO hard-reset (my new
files were physically deleted from disk, not just un-committed), so this was a `git reset --hard` or equivalent, not a
soft/mixed reset.

3 sibling repos in the SAME slot, committed in the SAME session, around the SAME time, were **not** affected
(strategy-service, execution-service, system-integration-tests, unified-trading-pm all still had my commits at `HEAD`
when I checked). So this isn't a blanket per-slot wipe — it hit 2 of 7 touched repos, seemingly at random (or by some
criterion I haven't identified — possibly whichever repos a periodic per-slot ff-pull/drift-repair script touched during
the window my commits existed unpushed).

**Recovery**: both commits were fully recoverable via `git reflog` + `git cherry-pick` (git never garbage-collects
reachable-via-reflog commits within the default 90-day window), so in THIS case no work was permanently lost. But if the
same mechanism fires on a repo where the agent has already moved on (reflog entry ages out, or the agent force-cleans
reflog, or simply doesn't think to check), this would be **silent, permanent loss of committed work** fleet-wide, for
any slot, any repo, any time between commit and push.

## Why it matters

This is the exact failure mode `codex/05-infrastructure/per-tab-worktrees.md` + `CLAUDE.md` § "Multi-agent safety" warn
AGENTS not to inflict on each other ("never force-push", "never git reset --hard ... uncommitted work") — but here the
actor was NOT an agent following documented git discipline; it was something else with write access to a slot clone that
used `git reset` instead of `git merge --ff-only`/`git pull --rebase --autostash` (which the worker/RULES.md docs
mandate for agents). If this is the same "structural pre-spawn branch-state gate" or "slot-cron-ff-pull.sh" mechanism
CLAUDE.md references (`worktree_clean_check.check_slot_branch_state` — "repairs a stale upstream + FFs when behind and
QUARANTINES a detached/wrong-branch/diverged clone"), it may have a bug where it treats "local HEAD ahead of origin with
uncommitted-to-origin work" the same as "diverged" and "repairs" it via a destructive `reset --hard` instead of the
documented non-destructive path (which would refuse to FF and leave the commits alone, or quarantine the clone for a
human to look at).

## Recommended decision

Operator/main to investigate what actually issued the two `Reset to origin/live-defi-rollout` reflog entries (likely
candidates: a per-slot cron health-check / drift-repair script, or a respawn/restart routine that resets a clone
believed-idle back to origin before reassigning it). Once identified: the repair path for "ahead of origin" must NEVER
be a `reset --hard` — it should either no-op (agent is mid-task, has local commits to push) or, at most, `git stash` the
divergent state somewhere recoverable (never silently discard). Given this can destroy real work fleet-wide with no
operator visibility unless the affected agent happens to notice (as I did here), this is a P0 data-safety gap.

## Todos

- [ ] [INFRA] P0. Identify the process that produced the "branch: Reset to origin/live-defi-rollout" reflog entries on
      slot 11 (unified-trading-library + unified-api-contracts) around 2026-07-13 11:30-11:50 UTC — check
      slot-cron-ff-pull.sh, worktree_clean_check.check_slot_branch_state, and any respawn/idle-reclaim routine for a
      `git reset --hard origin/<branch>` (or equivalent) call path. (repo: agent-orchestrator or
      unified-trading-pm/scripts, whichever owns the mechanism)
- [ ] [INFRA] P0. Whatever the mechanism, change its behavior for a clone with local commits not on origin: refuse
      (no-op + log) rather than reset; only auto-repair a clone that is BOTH commit-less-ahead AND has no reflog entries
      newer than N minutes (genuinely idle), never one with fresh local commits. (repo: same as above)
- [ ] [VERIFY] P1. Audit other active slots for the same reflog signature ("Reset to origin/<branch>" with a discarded
      commit reachable only via reflog) to see how widespread this already is / has been. (repo: unified-trading-pm — a
      fleet-wide grep script)
