---
doc_type: issue
title:
  'quickmerge.sh''s final `git push -u origin "$BRANCH" --quiet 2>/dev/null` silently swallows non-fast-forward
  rejections under high branch contention — script exits 0 having done nothing, wasting a full QG cycle per attempt'
summary: >-
  Discovered while shipping ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3 (slot-git-status-report.sh loopback
  preference) on a `live-defi-rollout` branch receiving a new commit from another slot roughly every 10-30s.
  `scripts/quickmerge.sh` line 1667 runs `git push -u origin "$BRANCH" --quiet 2>/dev/null` with NO exit-code check and
  BOTH stdout and stderr suppressed. When the push is rejected as non-fast-forward (near-certain on this branch once the
  ~1-2 minute quality-gates.sh + audit pipeline between quickmerge's own "Not-Behind Gate" pre-check and this final push
  line has elapsed), the failure is completely invisible: no error line, no non-zero exit surfaced, the script proceeds
  straight into PR-creation/reporting steps and exits 0 as if the commit had landed. Confirmed directly: ran
  quickmerge.sh --agent 5 times in a row for the same 7 already-committed local commits; all 5 runs printed "Proceeding
  to push." as their last content line and then exited (the 5th completed with observed exit code visible via the
  pipeline wrapper), yet `git merge-base --is-ancestor HEAD origin/live-defi-rollout` reported NOT an ancestor after
  every single run. A subsequent manual `git fetch && git rebase origin/live-defi-rollout && git push origin
  HEAD:live-defi-rollout` (with the push's real exit code checked) succeeded on the very first attempt. Each of the 5
  silent-failure runs cost a full quality-gates.sh cycle (60-300s depending on host load) for zero effect — pure wasted
  compute under exactly the contention regime (many concurrent slots on one shared branch) this fleet runs in
  constantly.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quickmerge, git-push, silent-failure, race-condition, branch-contention, ci-cd, ldr]
related: [/plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md, /codex/08-workflows/ci-cd-flow.md]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
source:
  "slot-11 (infra), discovered while shipping ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3 (5 consecutive
  silent-failure quickmerge runs on the same commits)"
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
---

# quickmerge.sh's final push silently swallows non-fast-forward rejections

## What I found

`scripts/quickmerge.sh:1667`:

```bash
git push -u origin "$BRANCH" --quiet 2>/dev/null
```

No `if`/exit-code check, `--quiet` suppresses git's own progress/error text, and `2>/dev/null` throws away whatever
stderr survives `--quiet` (including the `! [rejected]` / `(non-fast-forward)` lines git normally prints on a rejected
push). Every step after this line (issue-ref extraction, PR-base selection, PR creation, merge/reporting) runs
unconditionally, so a rejected push produces IDENTICAL script output and exit status to a successful one — nothing
downstream can distinguish the two.

On a low-contention branch this is latent (a push here rarely loses the race). On `live-defi-rollout` under real fleet
load — dozens of concurrent slots, a new commit landing roughly every 10-30 seconds — the window between quickmerge's
own STAGE 0.4 "Not-Behind Gate" (which does correctly rebase-and-recheck) and this final push line is however long STAGE
1 (dependency validation) through STAGE 3 (pre-commit hooks) take, commonly 1-3 minutes for unified-trading-pm's full
quality-gates.sh. On this shared host that window is long enough that the branch has essentially always moved again by
push time, so the rejection (and the silent swallow of it) is not an edge case here — it is closer to the common case.

## Evidence

Reproduced directly on `ao_satellite_ao_dispatch_batch1_2026_07_26.md` item 3's shipping commits (same 7-9 already-
committed local commits, no content changes between attempts):

| Attempt | Result                                                            | Log's last content line     | `git merge-base --is-ancestor HEAD origin/…` after |
| ------- | ----------------------------------------------------------------- | --------------------------- | -------------------------------------------------- |
| 1       | died mid-QG (separate host-memory-pressure issue, not this bug)   | mid quality-gates.sh output | NOT_PUSHED                                         |
| 2       | died mid-QG (same memory-pressure issue)                          | mid quality-gates.sh output | NOT_PUSHED                                         |
| 3       | completed                                                         | "Proceeding to push."       | NOT_PUSHED                                         |
| 4       | completed                                                         | "Proceeding to push."       | NOT_PUSHED                                         |
| 5       | completed (exit code captured downstream of a `\| tail` pipe = 0) | "Proceeding to push."       | NOT_PUSHED                                         |

Attempts 3-5 are the ones that isolate this bug specifically (1-2 were a separate, already-documented host-contention
issue killing the process before reaching the push line at all). After attempt 5, a manual recovery:

```bash
git fetch origin live-defi-rollout --quiet
git rebase origin/live-defi-rollout   # trivial, no conflicts (doc/plan files only)
git push origin HEAD:live-defi-rollout   # exit code checked explicitly this time
```

succeeded on the FIRST manual attempt, landing `unified-trading-pm@7d7c77665`. This confirms the content/commits were
never the problem — only the swallowed push failure was.

## Why it matters

- Every silently-failed quickmerge run burns a full `quality-gates.sh` cycle (pytest suite, basedpyright, ~80+ Citadel
  compliance checks, strategy-manifest validation, etc. — 60-300s depending on host load) for zero effect. Under the
  "everyone shares one host, many slots run QG concurrently" model this workspace already operates under (see
  `/codex/06-coding-standards/quality-gates.md` shared-host throttling), this is a real, recurring, avoidable compute
  cost — not a one-off.
- It also produces a misleading signal to the calling agent: `quickmerge.sh --agent` exiting 0 with no visible error is
  the documented "shipped" signal (worker.md / commit-push-flip-rule.md), so an agent that doesn't independently
  re-verify via `git merge-base --is-ancestor` (as this session did, only because of a suspicious NOT_PUSHED count
  during routine monitoring) would report a task `/done` while the actual commits never landed — a false-progress class
  this workspace explicitly guards against elsewhere (commit-push-flip-rule.md), but this one code path defeats that
  guard silently.

## Recommended decision

Make the final push fail loudly and (ideally) self-heal one retry cycle, mirroring the pattern STAGE 0.4's "Not-Behind
Gate" already uses:

```bash
if ! git push -u origin "$BRANCH"; then
  echo "[$REPO_NAME] ⚠️  push rejected (branch moved) — rebasing and retrying once..." >&2
  git fetch origin "$BRANCH" --quiet
  git rebase "origin/$BRANCH" || { echo "[$REPO_NAME] ❌ rebase conflict on push-retry — resolve manually"; exit 1; }
  git push -u origin "$BRANCH" || { echo "[$REPO_NAME] ❌ push failed after retry — branch contention too high, retry the whole quickmerge run"; exit 1; }
fi
```

At minimum, even without adding a retry, the exit code MUST be checked and a non-zero result must abort the script
loudly (non-zero exit, stderr visible) rather than silently proceeding into PR-creation as if the push had landed.

## Todos

- [ ] [SCRIPT] P1. Fix `scripts/quickmerge.sh`'s final `git push -u origin "$BRANCH"` (currently line ~1667) to check
      the push's exit code and fail loudly (non-zero exit + visible error) on rejection, instead of the current
      `--quiet 2>/dev/null` silent-swallow. Strongly prefer adding one rebase-and-retry cycle (mirroring STAGE 0.4's
      existing "Not-Behind Gate" pattern) since a single retry would have fixed 100% of the reproduction cases above.
      **Done-when:** a deliberately-staged non-fast-forward push (push to a test branch, have another process land a
      commit on it between quickmerge's pre-check and its final push, confirm quickmerge either recovers via retry or
      exits non-zero with a visible error) no longer silently exits 0 with nothing pushed. (repo: unified-trading-pm)
