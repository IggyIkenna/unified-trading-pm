---
doc_type: issue
title:
  slot-cron-ff-pull.sh has a narrow TOCTOU race between its "am I ahead?" check and its fast-forward reset — a commit
  landing in that window is silently discarded from the branch, reproduced twice on unified-trading-library
summary: >-
  During the Phase-7 self-hosted-runner fan-out (2026-07-27/28), `unified-trading-library`'s `live-defi-rollout` HEAD
  was silently reset back to `origin/live-defi-rollout` twice within ~13 minutes, discarding a real, freshly-made local
  commit each time (`61efd2e5` at 23:04:17, reset by 23:04:43 — 26s later; `dbb93c3a` at 23:10:30, reset by 23:17:23 —
  ~7min later). `git reflog` shows the exact mechanism: `branch: Reset to origin/live-defi-rollout` (a `git checkout -B
  <branch> origin/<branch>`-style operation, not a merge/rebase). The commits were not lost data — both were
  re-creatable and re-shipped successfully on retry — but this is a real, reproducible bug in shared multi-slot
  infrastructure that silently discards committed work, not a hypothetical.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library]
scope: [engineer, admin]
tags: [ci-cd, git, race-condition, slot-cron, multi-agent-safety, toctou, duplicate]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md,
  ]
created: 2026-07-28
priority: P1
parent_epic: infrastructure_master
source:
  "slot-1 (tabs/1), discovered during github_actions_operator_gated_followups_2026_07_17.md Phase-7 fan-out,
  /autonomous, 2026-07-27/28"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by: utl_shared_clone_commits_repeatedly_reset_2026_07_22
locked_by:
locked_since:
---

# slot-cron-ff-pull.sh TOCTOU race silently discards a fresh commit

> **🟢 RESOLVED 2026-07-28** — duplicate tracking of an already-homed issue; consolidated into
> `/plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` (see `resolved_by` above). Archived.

## What I found

`crontab -l` on the shared orchestrator VM (visible from any slot's `.tabs/N`) runs, every 5 minutes:

```
*/5 * * * * cd .../unified-trading-pm && { git fetch -q origin live-defi-rollout; git checkout -q origin/live-defi-rollout -- scripts/dev/slot-cron-ff-pull.sh scripts/dev/cron-branch-overrides.txt; } || true; cd .../.tabs/1 && bash .../slot-cron-ff-pull.sh --all-slots --quiet >> /tmp/slot-cron-ff-pull.log 2>&1
```

`/tmp/slot-cron-ff-pull.log` (shared across all slots this cron sweeps) shows the script correctly detects a repo with a
real unpushed commit and skips it — this is NOT a "blindly resets everything" bug:

```
[22:11:12Z] [skip:ahead] unified-trading-library (live-defi-rollout → live-defi-rollout) — 1 unpushed commit(s)
[22:16:12Z] [skip:ahead] unified-trading-library (live-defi-rollout → live-defi-rollout) — 1 unpushed commit(s)
```

But `git reflog` in `.tabs/1/unified-trading-library` shows the SAME repo's branch getting silently reset to origin at
other tick boundaries, discarding a commit that existed at the time:

```
057a8d72 HEAD@{2026-07-27 23:17:23 +0100}: branch: Reset to origin/live-defi-rollout   <- discarded dbb93c3a
dbb93c3a HEAD@{2026-07-27 23:10:30 +0100}: commit: feat(ci): Phase 7 ... rollout for unified-trading-library
057a8d72 HEAD@{2026-07-27 23:04:43 +0100}: branch: Reset to origin/live-defi-rollout   <- discarded 61efd2e5
61efd2e5 HEAD@{2026-07-27 23:04:17 +0100}: commit: feat(ci): Phase 7 ... rollout for unified-trading-library
```

**Reproduced twice, same repo, same session, ~13 minutes apart.** Both times the discarded commit was a real, valid,
already-passing-locally commit — not WIP, not garbage.

## Root cause (characterized, not yet fixed)

The script's own log proves it HAS an "am I ahead?" check that correctly skips a genuinely-ahead repo. The only
mechanism that explains a commit surviving that check yet still getting discarded is a **TOCTOU (time-of-check to
time-of-use) race**: the script reads git state (finds nothing ahead — HEAD == origin at that instant), and BEFORE it
executes its fast-forward/reset step, a NEW commit lands (created by whatever process — in this case, an autonomous
Workflow subagent's `git commit`). The reset then fires against the now-stale read, discarding the commit that appeared
in the gap. The 26-second occurrence is the sharpest evidence: `slot-cron-ff-pull.sh` runs on a `*/5 * * * *` cron, so a
26-second gap between commit and reset is far too short to be "the next scheduled tick" — it points at either sub-tick
re-invocation, or the check-then-act window inside a single tick being wide enough for an external `git commit` to land
between the two git calls.

## Why it matters

- This is shared, always-on, multi-slot infrastructure (`--all-slots`) — the race can hit ANY slot's ANY repo's ANY
  fresh commit, not just this one instance. It is a **silent** discard: no error, no warning to the committing process,
  the branch simply looks like the commit never happened. The only reason this was caught is that quickmerge itself
  failed downstream (`No differences from main — nothing to merge`) and the discrepancy was actively investigated via
  reflog rather than assumed to be operator/agent error.
- This is exactly the failure mode `CLAUDE.md`'s "Never `git reset --hard`/`clean -fd`/`restore` uncommitted work" rule
  exists to prevent for AGENTS — but this is infrastructure doing it TO a committed, valid state, not an agent violating
  the rule directly.

## Recommended fix path

- [x] [SCRIPT] P1. **AUDITED 2026-07-28 (slot-7) — this doc's own premise was WRONG; `slot-cron-ff-pull.sh` needs no
      fix.** Read the script in full plus dispatched an independent Explore agent to trace every `checkout`/`reset`/
      `update-ref`/`branch -f` call fleet-wide. Confirmed (again — this is the SECOND independent confirmation, six days
      after the first): `slot-cron-ff-pull.sh`'s only ref-mutating paths are a strict `git merge --ff-only` (fails
      rather than resets when local is ahead) and a patch-id-verified adopt-rebase (only fires when every local commit
      is already cherry-applied upstream). Its own header claim ("Never destructive... never reset --hard") holds. **The
      exact reflog signature this doc's title names (`branch: Reset to origin/live-defi-rollout`) is produced by
      `scripts/quickmerge.sh`'s `cascade_dep_branch()` (line ~476:
      `git checkout -B "$branch_name"     "origin/$branch_name"`), an ALREADY-TRACKED, ALREADY-PARTIALLY-FIXED issue** —
      `/plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` root-caused this same mechanism on
      2026-07-22 (todo 1, done) and shipped a preserve-before-reset guard (`unified-trading-pm@06dc7632`, todo 2, done):
      before the `checkout -B`, if the local branch has commits ahead of origin, the tip is saved to
      `refs/wip-preserve/cascade-<ancestor>-<sha12>` first. This doc's incident (`61efd2e5`/`dbb93c3a`, 2026-07-27
      23:04–23:17, `unified-trading-library`) is a **recurrence of that exact class**, not a new bug — this todo is
      DUPLICATE tracking of an issue that already has a home; consolidating there rather than maintaining two docs for
      one mechanism (this doc's `resolved_by` now points at it). **New findings from this pass, folded into the
      canonical doc as follow-up todos**: (1) checked whether the preserve mechanism actually protected
      `61efd2e5`/`dbb93c3a` — it did NOT: no `refs/wip-preserve/*` ref exists in `.tabs/1/unified-trading-library` for
      either sha, and both commit objects are now fully unreachable (`git     cat-file -e` fails on both) despite the
      guard being live in HEAD 5 days before the incident — the reason the guard didn't fire this time is NOT
      established (candidates: the executing session's own PM clone was stale and hadn't pulled `06dc7632` yet;
      something later cleaned up the preserve ref; a different code path). (2) Found + fixed an independent, real bug
      while reading `cascade_dep_branch()`: it ran `git fetch origin main` (not `$branch_name`) before both the
      preserve-check and the checkout — a stale holdover from before `live-defi-rollout` became the fleet integration
      branch (traced via `git log -L` to the original PR that added this function). Fixed:
      `unified-trading-pm@8ca436599` — now fetches `$branch_name` too, so `origin/$branch_name` is genuinely fresh at
      both check sites instead of implicitly depending on some OTHER process (`slot-cron-ff-pull.sh`'s own prefetch)
      having recently touched the same shared clone. This does not by itself explain the missing preserve ref (a stale
      origin ref can only ever make the ahead-count LARGER, never cause a false-negative skip), but it closes a real,
      independent correctness gap.
- [x] [SCRIPT] P1. ✅ **DONE 2026-07-28 (slot 10)** — root-caused via live reproduction, see the canonical doc's todo 7
      (`/plans/archive/2026_08/issues/utl_shared_clone_commits_repeatedly_reset_2026_07_22.md`): the preserve-guard's ahead-check
      and its `checkout -B` are non-atomic, and a concurrent commit landing in that gap is silently discarded without
      ever triggering the preserve ref — reproduced exactly (matching reflog signature + missing preserve ref) against a
      scratch clone. Not a stale-PM-clone issue; the guard itself has an inherent TOCTOU race.
- [ ] [VERIFY] P2. Once the above is root-caused, stress-test by scripting a tight commit loop against a scratch repo
      while a concurrent `cascade_dep_branch` sweeps it, confirming the preserve ref reliably appears across many
      iterations (this bug is probabilistic/timing-dependent — a single clean run does not prove the fix). See the
      canonical doc.
