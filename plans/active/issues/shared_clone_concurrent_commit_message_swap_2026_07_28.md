---
doc_type: issue
title:
  Two concurrent `git commit` invocations in the SAME shared unified-trading-pm clone can produce a commit whose message
  belongs to the OTHER process while the tree content is the committing process's own staged files — a
  commit-message/content mismatch, not data loss
summary: >-
  While shipping two unrelated checkbox-flip + archival commits to `unified-trading-pm` on `live-defi-rollout`
  (`.tabs/4`, slot-4), a `git commit -m "docs(plans): flip sports-staleness + cloud-build-timeout items..."` call
  succeeded (prek hooks passed) but the resulting commit (`7d8d690b6`, later rebased from `d64190bb0`) carries the
  commit message `fix(infra): hard RLIMIT_AS fallback in run-bounded-analysis.sh...` — a DIFFERENT, unrelated commit
  message that another concurrent agent process (same slot-4 identity, i.e. a different Claude Code session/sub-agent
  sharing this exact working directory) was evidently committing at the same moment. Verified via `git show --stat
  <sha>`: the commit's actual diff is exactly my 3 intended files
  (`plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md`,
  `plans/active/issues/cloud_build_evidence_citation_short_hash_unresolvable_2026_07_27.md`, and the active->archive
  rename of `deployment_api_cloud_build_600s_timeout_flake_2026_07_27.md`) — NOT `scripts/dev/run-bounded-analysis.sh`.
  That file's own RLIMIT_AS content was confirmed still present, uncommitted, in the working tree afterward (`git status
  --porcelain` showed ` M scripts/dev/run-bounded-analysis.sh`), so the other process's real work was NOT lost — it was
  simply left staged-then-unstaged (I explicitly `git restore --staged` it per the "never commit a foreign file" rule)
  and its author will presumably re-commit it under a correct message later. The defect is purely the COMMIT MESSAGE
  attaching to the wrong TREE, most likely because `git commit -m "..."` and prek's hook chain read/wrote a shared
  per-repo file (candidate: `.git/COMMIT_EDITMSG`, or a prek/pre-commit temp-patch/stash race — several `Unstaged
  changes detected, stashing unstaged changes to /Users/.../.cache/prek/patches/<ts>-<pid>.patch` / `Restored working
  tree changes from` lines were observed during these same attempts) at the exact moment two `git commit` calls in the
  same `.git` overlapped.
status: open
nature: issue
asset_group: [infrastructure, meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [git, race-condition, shared-clone, multi-agent, commit-message, prek, per-tab-worktrees, evidence-integrity]
related:
  [
    /plans/active/issues/quickmerge_silent_push_failure_under_contention_2026_07_27.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-07-28
last_updated: 2026-07-28
parent_epic: infrastructure_master
priority: P2
source:
  "code_quick_cross_repo_fix_backlog_2026_07_28.md worker (slot-4, deployment-api items: sports staleness-budget mirror
  + cloud-build timeout raise), 2026-07-28 — discovered while flipping the source-doc checkboxes in unified-trading-pm
  and archiving one resolved issue doc; observed 3 consecutive commit-drift/hook-failure retries on the same 3-file
  commit, the 3rd of which landed with a foreign commit message."
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
locked_by:
resolved_by:
depends_on: []
---

# Concurrent same-clone `git commit` calls can swap commit MESSAGES (not content)

## What I found

Working in `unified-trading-pm` on `.tabs/4` (slot-4) — a clone that, per
`/codex/05-infrastructure/per-tab-worktrees.md`, is shared by potentially many concurrent agent sessions/sub-agents
dispatched to the same tab — I hit branch-drift rejections + a prettier auto-fix retry across 3 attempts to commit 2
unrelated checkbox-flip edits + 1 file archival (rename). On the 3rd attempt the commit succeeded (all prek hooks green)
but `git log -1` / `git show --stat HEAD` showed:

- **Commit message**:
  `fix(infra): hard RLIMIT_AS fallback in run-bounded-analysis.sh when systemd-run --user is unavailable` (mentions
  `mdps_candle_manifest_population_disconnect_2026_07_25.md todo 9`) — a topic I never touched.
- **Commit tree diff**: exactly my 3 intended files, matching my
  `git commit -m "docs(plans): flip sports-staleness + cloud-build-timeout items..."` call byte-for-byte.
- **Author**: `ikennaigboaka [slot-4·laptop]` — my own slot identity, consistent with either (a) another concurrent
  Claude Code session dispatched into this same `.tabs/4` clone under the same git identity, or (b) the commit-identity
  hook resolving identity from the slot/host regardless of which logical agent process is running.

`scripts/dev/run-bounded-analysis.sh` — the file the stray message actually describes — was confirmed **not** part of
the committed tree; `git status --porcelain` afterward showed it still modified-but-uncommitted in the working tree, so
the other process's actual code change was not lost, just left pending for its own author to re-stage and commit.

## Why it matters

- **Evidence-integrity risk**: a `- [x] ... — <repo>@<sha>` completion citation is only trustworthy if `<sha>`'s
  message/content actually describes the claimed change. A reviewer or `check_evidence_backed_completion.py`-style gate
  trusting the commit SUBJECT LINE alone (rather than diffing the tree) could be misled by this class of defect — here
  the tree was correct, but the mismatch means message-based auditing (`git log --grep`, changelog generation) can point
  at the wrong SHA for a topic, or fail to find the right SHA when grepping by expected message text.
- **Root cause is architectural, not incidental**: per-tab-worktrees intentionally shares ONE `.git` directory across
  however many agent sessions land in that tab concurrently (confirmed by this session alone observing ~15+ concurrent
  `quickmerge.sh`/`quality-gates.sh` processes across `.tabs/1-4` during this exact window, several with cwd inside this
  same `unified-trading-pm` clone). `git commit -m` is not inherently safe against a second `git commit` racing in the
  same `.git` — a shared `COMMIT_EDITMSG`/index-lock window can bleed state between them. This is a distinct symptom
  from the sibling doc `quickmerge_silent_push_failure_under_contention_2026_07_27.md` (which is about a swallowed
  non-fast-forward PUSH rejection) — this one is about the local **commit** step itself, before any push is attempted.

## Impact today

None observed beyond the confusing message — no content was lost or corrupted; both processes' real work ended up
correctly represented in git (mine committed with the wrong message, the other's left safely uncommitted for its owner
to re-land). Filed as a P2 evidence-integrity / infra hygiene finding, not a data-loss incident.

## Todos

- [ ] [INFRA] P2. Root-cause whether prek/pre-commit's hook chain (or bare git) shares a mutable per-repo file
      (`.git/COMMIT_EDITMSG`, an index lock, or a prek patch-stash tempfile keyed by repo path rather than PID) across
      concurrent `git commit` invocations in the same working directory; if confirmed, either (a) document a "one commit
      at a time per clone" discipline explicitly in `/codex/05-infrastructure/per-tab-worktrees.md` alongside the
      existing multi-agent-safety rules, or (b) if a cheap technical mitigation exists (e.g. verifying
      `git log -1 --format=%s` matches the intended message immediately after commit and re-committing with `--amend -m`
      ONLY when the calling process's own staged tree is unambiguously still what's at HEAD), propose it.
- [ ] [INFRA] P3. Add a cheap post-commit self-check to the `git-commit` skill / quickmerge Commit+Push+Flip step: after
      `git commit`, diff `HEAD`'s subject line against the message just passed; if they don't match, treat it as a WARN
      (not a silent pass) so a future occurrence surfaces immediately in the calling agent's own output rather than
      requiring an operator to notice a mismatched changelog entry later.

## Evidence

- Commit `7d8d690b6` (rebased from originally-observed `d64190bb0`) on `unified-trading-pm@live-defi-rollout`,
  2026-07-28 ~20:18 local: message is the RLIMIT_AS fix; `git show --stat` diff is my 3 files
  (`plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md`,
  `plans/active/issues/cloud_build_evidence_citation_short_hash_unresolvable_2026_07_27.md`,
  `plans/active/issues/deployment_api_cloud_build_600s_timeout_flake_2026_07_27.md` ->
  `plans/archive/issues/deployment_api_cloud_build_600s_timeout_flake_2026_07_27.md`).
- `scripts/dev/run-bounded-analysis.sh` confirmed still `M` (modified, uncommitted) in the working tree immediately
  after, containing the RLIMIT_AS/`ulimit -v` content the stray message describes — not lost, just not yet committed
  under its own name.
- Three consecutive commit attempts in this same session hit, in order: (1) branch-drift rejection (someone else
  pushed), (2) a plan-hygiene hook auto-fix requiring re-stage, (3) a prettier auto-fix requiring re-stage, (4) another
  branch-drift rejection, before the 5th attempt landed with the swapped message — i.e. this clone was under continuous
  multi-agent write contention for the several-minute span these attempts covered.
