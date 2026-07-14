---
doc_type: issue
title: slot-5 heartbeat/progress nudge falsely reports deployment-api dirty for 260+ minutes
summary:
  Every /api/slots/5/heartbeat and /progress call returns a GIT STATUS RED auto-nudge claiming deployment-api has 1
  dirty file, growing minute-by-minute (190m -> 261m+ observed across this session). Direct verification (`git status`,
  `git status --porcelain -uall`, `git diff --cached --stat`, `git diff --stat`, checked for a nested .git/submodule,
  `.git/index.lock`) shows the worktree is genuinely clean and up to date with origin/live-defi-rollout every single
  time. This is a false positive in the orchestrator's dirty-repo detector for this slot/repo, not a real
  uncommitted-work violation.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
source: [slot-5 session 2026-07-13, agt-507f36]
related: []
tags: [infra, agent-orchestrator, dirty-worktree-detector, false-positive]
depends_on: []
---

# slot-5 deployment-api dirty-worktree false positive

## What I found

Across this slot-5 session (2026-07-13), every `/api/slots/5/heartbeat` and `/api/slots/5/progress` response included
the same recurring nudge:

```
Your slot has 1 repo(s) past the yellow threshold:
  - deployment-api: dirty 1 files for 190m — COMMIT+PUSH
```

The reported duration climbed monotonically across calls (190m -> 200m -> 231m -> 261m+), consistent with the server
tracking a real timer against a real detected-dirty state — but manual verification at
`/home/ubuntu/unified-trading-system-repos/.tabs/5/deployment-api` at multiple points during this window found:

- `git status` -> "nothing to commit, working tree clean", branch up to date with `origin/live-defi-rollout`
- `git status --porcelain -uall` (includes untracked) -> empty
- `git diff --cached --stat` / `git diff --stat` -> empty
- No `.git/index.lock`
- No nested `.git` directory / no `.gitmodules` (ruled out a submodule reporting separately)
- `git rev-parse --show-toplevel` matches the expected worktree path (no stray secondary clone)

I never touched `deployment-api` in this session (my tasks were in features-service, strategy-service, and
instruments-service) — so there's no chance this is my own uncommitted WIP that I'm failing to see.

## Why it matters

This is a low-severity monitoring bug, not a data-correctness or safety issue, but a persistent false positive on the
dirty-repo detector erodes trust in the "GIT STATUS RED" nudge fleet-wide — if a worker eventually learns to ignore it
because it's usually noise, a genuine dirty-repo violation could get missed. It's also possible the detector is caching
a stale git-status snapshot per slot/repo pair and never invalidating it once a false state is recorded, which would
mean this specific slot+repo combination stays permanently "red" until the server restarts or the cache entry is
otherwise cleared — worth checking if other slot+repo pairs show similarly stuck durations.

## Recommended decision

Whoever owns the orchestrator's dirty-worktree detection (`server/` — the same subsystem that produces the
`slot_done_no_plan_flip` / dirty-repo checks referenced in `RULES.md` § 2): re-run the detector for slot 5 /
deployment-api and compare its raw git invocation against the manual checks above. Likely candidates: a stale cached
result never invalidated after the repo went clean, a race in how the detector shells out `git status` (e.g. wrong cwd,
a `$PWD` vs worktree-path mismatch), or a porcelain-parsing bug treating some non-dirty output as dirty.

## Todos

- [x] ✅ [SCRIPT] P3. Investigate + fix the agent-orchestrator dirty-worktree detector's false-positive on slot 5 /
      deployment-api (persisted 260+ minutes across repeated genuinely-clean verifications this session); check whether
      the detector caches a stale result instead of re-running `git status` fresh each check. (repo: agent-orchestrator)
      — **INVESTIGATED, slot 10 (infra), 2026-07-14.** unified-trading-pm@0c08a0afe, agent-orchestrator@f3b803371.
  - **No stale-cache bug found.** Traced the full pipeline: `slot-git-status-report.sh` (`unified-trading-pm`) runs a
    FRESH `git status --porcelain` every cron tick (no caching within the script — a new bash invocation each time); the
    server's `_propagate_not_clean_since()` (`server/routes/git_health.py`) only carries `not_clean_since` forward when
    the FRESH snapshot's `state=="clean" AND behind==0 AND ahead==0 AND dirty_files==0` is false — all four checked
    against THIS TICK's reported values, not a stale cache. The reporter's own `state` assignment is derived from the
    same `dirty_files`/`ahead`/`behind` it computes, so the two can't legitimately disagree. Read both files
    line-by-line; found no logic bug that would explain a sustained false "dirty" report on a genuinely clean repo.
  - **Could not reproduce the specific historical incident** — different slot (5), different host, ~14h+ before this
    dispatch; slot 10's own `deployment-api` right now reads genuinely clean by both the reporter's own
    `classify_repo()` (isolated-function test) and manual `git status`, so there was no live repro available.
  - **The real, fixable gap: the nudge/page never said WHICH file was supposedly dirty** — "1 dirty file(s)" with no
    path meant the ORIGINAL report's manual-verification-vs-claim mismatch could never be reconciled (was it a
    QG-generated untracked artifact? a race with `slot-cron-ff-pull.sh`? a different worktree entirely?). Fixed the
    diagnosability gap instead of guessing at an unreproducible root cause: `classify_repo()` now also captures up to 5
    raw `git status --porcelain` lines (status code + path) as `dirty_sample`, threaded through the JSON payload as
    `dirty_files_sample` (new optional/backward-compatible `RepoStatus` field — an older reporter that omits it posts
    the same shape as before), and surfaced in BOTH the in-app worker nudge (`maybe_nudge_on_red_repos`) and the
    Slack-paging summary (`maybe_alert_git_staleness`) — e.g.
    `deployment-api: dirty 1 files for 190m — COMMIT+PUSH [?? state.json.tmp]`. A future recurrence of this bug class is
    now immediately diagnosable instead of requiring another blind investigation.
  - Verified: isolated-function test of `classify_repo()` against a real clean repo AND a synthetic dirty repo (2 files:
    1 modified, 1 untracked) confirmed the new field populates correctly and is pipe/TAB-safe through the TSV transport.
    3 new unit tests (`tests/test_git_staleness_alerting.py`) cover the sample appearing in both the Slack-page and
    in-app-nudge summaries, and confirm the old (no-sample) shape still works unchanged. Full `quality-gates.sh` green
    on both repos (`unified-trading-pm` — scripts/** carve-out; `agent-orchestrator` — via `quickmerge --agent`).
