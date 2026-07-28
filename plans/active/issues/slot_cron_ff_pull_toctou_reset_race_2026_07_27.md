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
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-library]
scope: [engineer, admin]
tags: [ci-cd, git, race-condition, slot-cron, multi-agent-safety, toctou]
related: [/codex/05-infrastructure/per-tab-worktrees.md]
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
resolved_by:
locked_by:
locked_since:
---

# slot-cron-ff-pull.sh TOCTOU race silently discards a fresh commit

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

- [ ] [SCRIPT] P1. Audit `slot-cron-ff-pull.sh`'s check-then-act sequence for the ahead/behind determination — the fix
      is almost certainly to make the check and the fast-forward/reset atomic with respect to the local ref (e.g. take
      the "ahead" measurement and the reset action from the SAME `git` invocation / same point-in-time ref read, rather
      than two separate calls with a window between them), or add a final re-check immediately before the reset/checkout
      executes and abort if the local HEAD moved since the initial read.
- [ ] [VERIFY] P2. Once fixed, stress-test by scripting a tight commit loop against a scratch repo while the cron sweeps
      it, confirming zero silent discards across many iterations (this bug is probabilistic/timing-dependent, a single
      clean run does not prove the fix).
