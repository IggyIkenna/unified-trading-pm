---
doc_type: issue
title:
  "qg-host-governor per-repo sub-cap buckets by slot NUMBER ('2') instead of repo name in at least one invocation path —
  causes cross-repo starvation on shared hosts"
summary: >-
  `qg-host-governor.sh::_qg_repo_name()` is documented (its own 2026-08-09 comment) to prefer `PROJECT_ROOT` over
  `REPO_ROOT` specifically to avoid bucketing every repo in a `.tabs/<N>` slot under the slot NUMBER instead of the
  repo's own name — citing a prior live incident ("caught live 2026-08-09 via a 286s starvation on a bucket named '2'
  instead of 'unified-trading-pm'"). Reproduced the SAME bug class again this session: a plain `bash
  scripts/quality-gates.sh --no-fix` invocation from `market-tick-data-service`'s repo root bucketed under
  `.benchmarks/qg-governor-total/repo/2/` (the `.tabs/2` slot number) rather than `.../repo/market-tick-data-service/`,
  colliding with `deployment-service`'s concurrently-running QG (also in `.tabs/2`, also mis-bucketed under `2`) under
  the SAME per-repo sub-cap of 1 — producing a 24+ minute perpetual "busy" state with zero progress, even after the true
  competing process had exited cleanly. Exporting `PROJECT_ROOT=<absolute-repo-path>` before invoking correctly
  re-bucketed the run under `repo/market-tick-data-service/` (confirmed via directory listing) and it acquired a free
  slot within seconds — proving `PROJECT_ROOT` is not reliably populated in the environment by the time
  `qg_governor_acquire_total_instance` (called early in `base-service.sh`) reads it, at least for a bare `bash
  scripts/quality-gates.sh` invocation from a plain shell (not going through whatever wrapper the prior 2026-08-09 fix's
  own reproduction path used).
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [quality-gates, governor, concurrency, starvation, ci-blocker, P2]
created: 2026-08-09
author: unknown
last_updated: "2026-08-10"
priority: P2
parent_epic: infrastructure_master
source: >-
  Discovered while shipping a DeFi TheGraph key-rotation fix in market-tick-data-service — a plain QG invocation queued
  24+ minutes with "total-instance tokens busy (2 sub-cap 1 / host-wide cap 10)" despite only ONE live
  market-tick-data-service QG process existing on the host at any point during the wait.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: "unified-trading-pm@144a0cdd28d7d517677e274125ded02e3965186b"
context_scope:
  [
    unified-trading-pm/scripts/quality-gates-base/qg-host-governor.sh,
    unified-trading-pm/scripts/quality-gates-base/qg-common.sh,
    unified-trading-pm/scripts/quality-gates-base/base-service.sh,
  ]
related: []
---

## Root cause (diagnosed, not fixed — out of scope per operator instruction)

`_qg_repo_name()` (`qg-host-governor.sh`):

```bash
local root="${PROJECT_ROOT:-${REPO_ROOT:-}}"
[[ -n "$root" ]] && basename "$root" || echo "unknown"
```

This correctly PREFERS `PROJECT_ROOT` when set. `qg-common.sh` is supposed to populate it:

```bash
PROJECT_ROOT="${PROJECT_ROOT:-$QG_PROJECT_ROOT}"   # QG_PROJECT_ROOT = walk-up-to-pyproject.toml
```

But `base-service.sh` calls `qg_governor_acquire_total_instance` at line ~79, and the observed live bucketing
(`repo/2/slot.1`) proves `PROJECT_ROOT` was still empty at that call site for this invocation path — falling through to
`REPO_ROOT` (the `.tabs/<N>` slot dir set by `setup-tab-worktrees.sh`, whose basename is just the slot number, e.g.
`"2"`). Two repos sharing a slot (`market-tick-data-service` and `deployment-service`, both in `.tabs/2`) both bucket
under the SAME `"2"` name, and since every non-PM repo's sub-cap is 1, the second one to attempt acquisition starves
indefinitely behind the first — even after the first's QG process exits (a fresh new attempt starves too, since the "2"
bucket is still occupied by WHICHEVER of the two repos is currently running, and neither correctly identifies itself).

Either `qg-common.sh` isn't sourced early enough relative to `qg_governor_acquire_total_instance`'s call in this
invocation path, or something clears/never-sets `PROJECT_ROOT` between the two. Not further diagnosed (root-caused
enough to reproduce + work around; deeper trace is the fix owner's job).

## Reproduction

```bash
cd .../market-tick-data-service && bash scripts/quality-gates.sh --no-fix
# → "[qg-governor] total-instance tokens busy (2 sub-cap 1 / host-wide cap 10) — queued Ns" forever
ls .../​.benchmarks/qg-governor-total/repo/   # shows "2" and "99", NOT "market-tick-data-service"
```

## Workaround used this session (not a fix)

```bash
export PROJECT_ROOT="$(pwd)"   # absolute path to the repo root, before invoking quality-gates.sh
bash scripts/quality-gates.sh --no-fix
# → correctly buckets under repo/market-tick-data-service/, acquires cleanly within seconds
```

## Suggested fix directions (not performed here — operator instruction: diagnose + file, don't fix the governor)

1. Verify `qg-common.sh` is sourced (and `PROJECT_ROOT` assigned) BEFORE `qg_governor_acquire_total_instance` runs in
   every `base-*.sh` entry point, not just `base-service.sh`'s — a plain source-order audit.
2. Consider having `_qg_repo_name()` compute its own repo-root walk-up (mirroring `qg-common.sh`'s
   `_qg_walk_up_to_pyproject`) as a fallback BEFORE falling back to `REPO_ROOT`, so a slot-number bucket is never
   reachable even if the caller's sourcing order regresses again.
3. A stale-bucket self-heal (liveness-check the PID(s) implied by a bucket's lock file, per the existing `running.<pid>`
   marker pattern already used by the sibling heavy-phase `qg-governor` dir) would also have prevented the 24-minute
   hang even without the naming fix, since (per this session's observation) the ORIGINAL competing process in bucket "2"
   had already exited cleanly (EXIT=0) partway through the wait, yet the bucket stayed "busy" — worth checking whether
   release-on-exit is itself reliable, independent of the naming bug.

## RESOLVED 2026-08-10 — `unified-trading-pm@144a0cdd28d7d517677e274125ded02e3965186b`

### Fix

Direction 2 from the suggested-fixes list above, taken further: `_qg_repo_name()` no longer reads
`PROJECT_ROOT`/`REPO_ROOT` at all as its primary source — it queries **git directly**, which needs no caller-populated
env var and is therefore immune to the entire "which var, set in what order" class of bug (the precedence-only fix
shipped earlier the same day, `e3819eb4f1`, only reordered `PROJECT_ROOT:-REPO_ROOT` — it still depended on
`PROJECT_ROOT` being populated at call time, and this issue is exactly that assumption failing a second time):

1. **Primary**: `git remote get-url origin`, basename minus the `.git` suffix — the repo's actual GitHub identity.
   Verified live to also be the correct choice for a nested worktree (`.claude/worktrees/<branch>/`):
   `git rev-parse --show-toplevel` there returns the worktree's own branch/hash-named directory (wrongly making it look
   like a different "repo"), whereas `git remote get-url origin` correctly returns the SAME identity as the worktree's
   parent clone, since worktrees share their parent repo's remotes.
2. **Fallback**: `git rev-parse --show-toplevel`, basename — used only when there's no `origin` remote.
3. **Final fallback**: `PROJECT_ROOT`/`REPO_ROOT`/`pwd`, basename — used only if git itself is unavailable or cwd isn't
   a git working tree at all (matches this file's existing graceful-degradation posture).

Diff: `scripts/quality-gates-base/qg-host-governor.sh` (`_qg_repo_name()`, +38/-9 net).

### Regression test

New file `scripts/quality-gates-base/tests/test-qg-repo-name-slot-agnostic.sh` (12 assertions, all passing). Directly
reproduces both the original failure mode (PROJECT_ROOT unset) and the exact mechanism of THIS issue's reopened incident
(PROJECT_ROOT **and** REPO_ROOT both poisoned to a shared slot-like path, e.g. `.tabs/2`, for two different fixture
repos with distinct `origin` remotes) and asserts the two repos never bucket to the same key. Also covers: baseline
correct-name resolution, a real nested-worktree fixture (`git worktree add`), no-origin-remote fallback, and
non-git-tree fallback.

**Proved as a genuine regression guard, not just a new test**: ran this same test file against both prior versions of
`_qg_repo_name()` (the original `REPO_ROOT:-PROJECT_ROOT` bug and the `e3819eb4f1` precedence-only fix) — both FAIL
10/12 assertions (including the exact "poisoned PROJECT_ROOT/REPO_ROOT -> both resolve to `2`" case this issue is
about); the new fix passes 12/12.

Also fixed in passing (same test directory, one-line stale assertion, unrelated bug): the "default cap floored at 4"
case in `test-qg-total-instance-gate.sh` was stale against the 2026-08-09 operator ruling that raised the floor to 6
(`_qg_total_default_cap`'s own comment) — updated the expected value.

### Live verification

From within `market-tick-data-service` and `deployment-service` (both under `.tabs/2`, PROJECT_ROOT/REPO_ROOT explicitly
unset, `QG_REPO_INSTANCE_CAP=1` — the real prod sub-cap for every non-PM repo, i.e. the exact cap that starved before),
sourced the shipped `qg-host-governor.sh` from each repo's own cwd and called `qg_governor_acquire_total_instance`
**concurrently**:

```
[mtds] repo_name=market-tick-data-service
[mtds] ACQUIRED
[mtds] RELEASED
[deployment-service] repo_name=deployment-service
[deployment-service] ACQUIRED
[deployment-service] RELEASED
```

Both acquired and released without blocking each other (previously: 24+ minute starvation). Bucket directories created:
`repo/market-tick-data-service/` and `repo/deployment-service/` — two distinct, correctly-named buckets, never the bare
slot number `2`.

Full `unified-trading-pm` `bash scripts/quality-gates.sh --no-fix` ran green (sentinel matched HEAD); shipped via
`bash scripts/quickmerge.sh --agent`, landed on `live-defi-rollout` at `144a0cdd28d7d517677e274125ded02e3965186b`.
