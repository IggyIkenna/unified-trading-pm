---
doc_type: issue
title: >-
  safe-doc-push.sh's "extreme stash pile" quarantine-and-restore path silently dropped BOTH sides of a git-mv
  archival rename's content — recovered only because the content was reconstructible from session context
summary: >-
  While archiving two plans via a same-commit flip+archival git mv (per plan-completion-and-archival-discipline.md's
  sanctioned single-repo shape), scripts/dev/safe-doc-push.sh hit its "24 entries is extreme — quarantining current
  dirty tree into a named stash" defensive branch (pre-existing 24+ accumulated stash entries in this slot-3 checkout,
  unrelated to this task) and, across 2 separate invocations (default and SDP_ISOLATED=0), consistently failed with
  `fatal: pathspec 'plans/active/<old-path>.md' did not match any files` during its internal staging retry loop. After
  the failures, `git status`/`ls` confirmed BOTH renamed files' new-path content was gone from the working tree
  entirely (not staged, not on disk) while the old paths showed as a plain `deleted` (not a tracked rename) — i.e. the
  quarantine-and-restore cycle lost the git-mv'd content on BOTH sides, not just failed to commit it. No data was
  actually lost only because this session still had the exact final content in its own conversation context (from the
  Edit tool calls that produced it) and could reconstruct both files byte-for-byte via Write; a session that had
  already compacted, or a shorter/different agent flow, would not have that recovery path.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [safe-doc-push, git, archival, data-loss-risk, stash, tooling, big-finding]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-15"
author: ikennaigboaka [slot-3]
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: none
depends_on: []
parent_epic: infrastructure_master
resolved_by:
locked_by:
context_scope:
  [
    scripts/dev/safe-doc-push.sh,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
  ]
source: >-
  cefi_residual_ao_dispatch_2026_08_15_finalize.md re-verification/archival session, 2026-08-15 (slot-3, review).
---

# `safe-doc-push.sh` extreme-stash-quarantine path drops git-mv'd rename content

## What happened

Task: archive `cefi_residual_ao_dispatch_2026_08_15.md` + `cefi_residual_ao_dispatch_2026_08_15_finalize.md` (both
`git mv`'d to `plans/archive/2026_08/`), bundled with 3 unrelated small edits to other issue docs, via
`scripts/dev/safe-doc-push.sh "<msg>" --files "<old1> <new1> <old2> <new2> <doc3> <doc4> <doc5>"` — naming both old and
new paths for each rename, per the archival SSOT's explicit instruction.

**First invocation (default, isolated-worktree mode on):**

```
⚠ 24 autostash/safety-snapshot entries in the stash list — the autostash CHAIN may be active.
🛑 24 entries is extreme — quarantining current dirty tree into a named stash BEFORE the pull...
── attempt 1/6 ── through attempt 6/6, each:
❌ could not stage named files -- 'git add' failed for a non-lock reason:
fatal: pathspec 'plans/active/cefi_residual_ao_dispatch_2026_08_15.md' did not match any files
❌ Exhausted 6 attempts.
```

The script's own error text asserted "Your named file(s) are byte-identical to what you handed this script, so
re-running is safe" — this claim was checked and found FALSE for the renamed files (see below).

**Second invocation (`SDP_ISOLATED=0`, the SSOT's documented workaround for the isolated-worktree copy mechanism
dropping a rename's delete side):** identical failure, same pathspec error, same "24 entries is extreme" quarantine
branch firing.

**Post-failure state** (checked directly, not assumed):

```
$ git status --porcelain
 D plans/active/cefi_residual_ao_dispatch_2026_08_15.md
 D plans/active/cefi_residual_ao_dispatch_2026_08_15_finalize.md   # note: one ' D', one 'D ' — inconsistent index state
$ ls plans/archive/2026_08/cefi_residual_ao_dispatch_2026_08_15.md
ls: cannot access ...: No such file or directory
$ ls plans/archive/2026_08/cefi_residual_ao_dispatch_2026_08_15_finalize.md
ls: cannot access ...: No such file or directory
$ git ls-files plans/archive/2026_08/cefi_residual_ao_dispatch_2026_08_15*.md
(empty)
```

Both renamed files' new-path content was **absent from the working tree, the index, and (per `git ls-files`) not
tracked** — i.e. gone, not merely unstaged. The old paths were present in the index as plain deletions (not a
`git status` `renamed:` pairing), consistent with the working-tree side of the `git mv` having been lost during the
quarantine `git stash push` / restore cycle while only the delete-half of the index change survived.

Also observed both times: the reported `last push_err` cited a push target under
`/home/ubuntu/.cache/qg-tmp/bats-run-<random>/test/<N>/origin.git` — a bats-test fixture path, NOT this repo's real
`origin` (`git@github.com:IggyIkenna/unified-trading-pm.git`, confirmed via `git remote -v` immediately after). This
is very likely log/state contamination from a concurrent bats test run on this shared host exercising
`safe-doc-push.sh`'s own test suite, surfacing through the script's error-reporting path — a separate, lower-severity
observation flagged here rather than chased further (out of scope for this finding).

## Why it matters

`safe-doc-push.sh` is the CLAUDE.md-mandated path for "pure doc/plan-flip" commits — every plan archival in this
workspace is supposed to go through it. If its extreme-stash-pile defensive branch (a REAL, not rare, condition — this
slot's checkout already had 24+ such entries before this session even started, per the accompanying
`multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`) silently drops a `git mv`'d rename's
content on both the isolated AND shared-index code paths, this is a latent **data-loss** bug specifically on the exact
operation (`git mv` archival) the workspace's own plan-completion-and-archival-discipline.md ritual requires for every
single plan closeout. This session recovered only because the exact final content was still derivable from the
conversation's own history (the Edit tool calls that produced it); a worker picking this up cold from a stale Read, or
any non-Claude-Code agent without equivalent turn-by-turn content provenance, would have genuinely lost the archived
plan's final content with no recovery path — the git objects for the intermediate `git mv`'d state were never
committed, so there is nothing to `git show`/reflog-recover.

## Recommended decision

Root-cause the quarantine-and-restore code path (search `scripts/dev/safe-doc-push.sh` for "extreme" /
`autostash_guard_bound_backlog` / `autostash_guard_quarantine_stale_pop`) for how it re-extracts specific `--files`
paths from the quarantine stash after the pull. The leading hypothesis: it likely does something equivalent to
`git checkout stash@{N} -- <path>` per named file, which correctly restores a path with CONTENT in the stash snapshot
but has no defined behavior (or a silently-swallowed error) for a path that is supposed to be ABSENT in that same
snapshot (the old side of an already-`git mv`'d rename) — the isolated-worktree mode's `2026-08-10` fix for the
structurally identical "deleted file has nothing to copy" problem (per the archival SSOT) may not have been ported to
this quarantine-restore path.

## Todos

- [ ] [SCRIPT] P1. Reproduce in an isolated scratch repo (per this workspace's established pattern for verifying
      `safe-doc-push.sh` fixes, e.g. `check_create_only_archive_commits.py`'s own regression coverage): seed 24+ stash
      entries, `git mv` a file, run `safe-doc-push.sh --files "<old> <new>"`, confirm the same content-loss
      reproduces. Repo: unified-trading-pm.
- [ ] [SCRIPT] P1. Fix the quarantine-and-restore path so a named `--files` entry that is the OLD (now-absent) side of
      an already-staged rename is restored as a tracked deletion (not silently dropped), mirroring the 2026-08-10
      isolated-worktree fix's "propagate deletions" logic. Add a regression test covering this exact shape (rename +
      extreme stash pile). Repo: unified-trading-pm.
- [ ] [SCRIPT] P2. Once fixed, consider lowering the "24 entries is extreme" bar or adding a lighter-weight
      protect-and-restore path that doesn't require a full stash round-trip for the common case (few named files,
      most of the pile pre-existing and unrelated) — the current design pays the highest-risk code path exactly when
      the pile is largest, which is backwards from a safety standpoint. Repo: unified-trading-pm.
- [ ] [INFRA] P3. Separately (not blocking the above): this slot's checkout has 55 accumulated stash entries, the
      large majority auto-generated safety-snapshots/autostash remnants from past sessions (several look like
      superseded intermediate attempts at the same past prosewrap fix, per stash message inspection). Worth a careful,
      individually-reviewed cleanup pass (NOT a bulk drop — some entries may hold genuine unrecovered WIP) to bring
      this slot's pile back under whatever threshold "extreme" is, both to stop re-triggering this exact defensive
      branch and per the general no-let-it-grow-unbounded posture. Repo: unified-trading-pm (or a slot-3-specific
      maintenance task).

## Progress Log

- **2026-08-15 (slot-3, review)**: Filed while archiving `cefi_residual_ao_dispatch_2026_08_15.md` +
  `cefi_residual_ao_dispatch_2026_08_15_finalize.md`. Worked around it this session by reconstructing both files'
  exact final content from the session's own edit history (Write, not recovered via git) and shipping via a directly
  supervised `git commit`/`push` (verified hooks still fire — `.git/hooks/pre-commit` is a real installed prek hook,
  not merely wrapper-invoked) instead of the wrapper script. Did not attempt to fix the script itself this session
  (out of this task's scope) or bulk-drop the stash pile (risk of destroying genuine foreign WIP without individual
  review — left as its own P3 todo above).
