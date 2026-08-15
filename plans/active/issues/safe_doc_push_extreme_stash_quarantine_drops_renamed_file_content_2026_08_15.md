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

**UPDATE 2026-08-15 (slot-19): the leading hypothesis below (quarantine-and-restore path) is REFUTED by
reproduction — see Progress Log. Left verbatim for provenance; do not root-cause against it.**

~~Root-cause the quarantine-and-restore code path (search `scripts/dev/safe-doc-push.sh` for "extreme" /
`autostash_guard_bound_backlog` / `autostash_guard_quarantine_stale_pop`) for how it re-extracts specific `--files`
paths from the quarantine stash after the pull. The leading hypothesis: it likely does something equivalent to
`git checkout stash@{N} -- <path>` per named file, which correctly restores a path with CONTENT in the stash snapshot
but has no defined behavior (or a silently-swallowed error) for a path that is supposed to be ABSENT in that same
snapshot (the old side of an already-`git mv`'d rename) — the isolated-worktree mode's `2026-08-10` fix for the
structurally identical "deleted file has nothing to copy" problem (per the archival SSOT) may not have been ported to
this quarantine-restore path.~~

**Actual root cause (confirmed by reproduction, 2026-08-15): the shared-index path's `git add -- "${FILES[@]}"`
call (safe-doc-push.sh, the `for attempt in ... git add -- "${FILES[@]}"` retry loop) fails on the OLD side of any
`--files`-named rename that the CALLER already staged via `git mv` before invoking this script — independent of
stash-pile size, autostash, or the extreme-quarantine branch entirely.** `git mv old new` removes `old` from the
index outright (folded into the new path's R100 rename pair) — it is not "tracked but missing from the working
tree" (the case `git add -- <path>`'s deletion-staging behaviour, and this script's own `reassert_renames` comment,
correctly handle), it has NO index entry at all. Naming that already-gone path in `--files` and calling
`git add -- "$path"` on it is what produces `fatal: pathspec '<old>' did not match any files`, identically on every
one of the 6 retry attempts (a deterministic content shape, not a transient race, so the retry loop can never
converge). The "24 entries is extreme" quarantine log line in the original report was a real but INCIDENTAL
co-occurrence (that checkout already carried 24+ unrelated stash entries), not the trigger — see Progress Log for a
0-stash-entry control repro that fails identically. Isolated-worktree mode (the default off the AO VM) does not hit
this: its copy loop starts from a FRESH worktree checked out at `origin/$BRANCH` (where the old path is still a
plain tracked file, not yet mv'd), so `rm -f`-ing it there and then `git add`-ing it genuinely IS the
tracked-but-missing shape.

## Todos

- [x] [SCRIPT] P1. Reproduce in an isolated scratch repo (per this workspace's established pattern for verifying
      `safe-doc-push.sh` fixes, e.g. `check_create_only_archive_commits.py`'s own regression coverage): seed 24+ stash
      entries, `git mv` a file, run `safe-doc-push.sh --files "<old> <new>"`, confirm the same content-loss
      reproduces. Repo: unified-trading-pm. — ✅ 2026-08-15 (slot-19): reproduced byte-for-byte (identical
      "🛑 10 entries is extreme — quarantining..." log line, identical
      `fatal: pathspec 'plans/active/<old>.md' did not match any files` repeated across all 6/6 attempts, identical
      "Exhausted 6 attempts" exit) via new `scripts/dev/repro-safe-doc-push-extreme-stash-rename-drop.sh`. Also ran a
      0-stash-entry control (no extreme pile at all, same `git mv` + `--files "<old> <new>"` shape) — it fails
      IDENTICALLY, which falsifies the quarantine-path hypothesis and pins the true mechanism to the shared-index
      `git add -- "${FILES[@]}"` call itself (see corrected Recommended decision above). Isolated-worktree mode
      (`SDP_ISOLATED=1`, the AO-VM-inapplicable laptop default) does NOT reproduce — lands cleanly, per its own
      code path already handling this shape correctly.
- [x] ✅ [SCRIPT] P1. Fix `safe-doc-push.sh`'s shared-index `git add -- "${FILES[@]}"` step (around the retry loop,
      `scripts/dev/safe-doc-push.sh`) so a named `--files` entry that is the OLD side of an already-`git mv`'d
      rename (no index entry, no disk file — NOT the "tracked but missing" shape `reassert_renames`/the deletion
      comment at line ~976 already handle) is skipped from the explicit `git add` call rather than passed to it
      verbatim, mirroring the isolated-worktree copy loop's existing deletion-propagation branch. Add a regression
      test covering this exact shape at LOW stash-pile size too (the extreme-quarantine framing was a red herring —
      don't gate the fix or its test on a large stash pile). `scripts/dev/repro-safe-doc-push-extreme-stash-rename-drop.sh`
      (this session) is a ready-made repro harness for verifying the fix. Repo: unified-trading-pm. —
      unified-trading-pm@60fa240ecc (slot-14, infra): implemented as a new `stage_named_files()` that stages per-file
      and checks the INDEX directly for the missing-from-disk case (needs-staging vs already-staged vs a genuine
      caller error) rather than a single combined `git add`, plus a companion fix re-deriving `KNOWN_RENAME_SOURCES`
      from `FILES` directly (absent-from-disk + present-in-HEAD) instead of an already-staged `-M` diff pair, which
      was silently empty on the isolated-worktree path — see Progress Log for full detail + regression coverage.
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
- **2026-08-15 (slot-19, infra)**: Reproduced todo 1 in an isolated scratch bare-repo + 2 worker clones (new
  `scripts/dev/repro-safe-doc-push-extreme-stash-rename-drop.sh`, mirrors the established
  `repro-safe-doc-push-stale-local-clobber.sh` pattern). Seeded 10 stash entries matching
  `autostash_guard_bound_backlog`'s own detection regex (its "extreme" bar is `>=10`, not literally 24 — the
  original report's 24 was this checkout's accumulated total, not a threshold), `git mv`'d a plan from
  `plans/active/` to `plans/archive/2026_08/`, bundled one unrelated sibling-doc edit, and ran
  `safe-doc-push.sh --files "<old> <new> <sibling>"`. **Confirmed byte-for-byte**: same "🛑 N entries is extreme"
  line, same `fatal: pathspec '<old-path>' did not match any files` on every one of 6/6 attempts, same "Exhausted 6
  attempts" terminal failure; ground-truth check on the bare origin (not the script's own claims) confirmed the new
  path never landed and the old path was still present — a genuine drop, not merely a reported one. Then ran a
  **0-stash-entry control** (identical `git mv` + `--files` shape, no pile at all, no quarantine branch eligible)
  and it failed IDENTICALLY — this falsifies the issue's original "quarantine-and-restore path" hypothesis. Traced
  the real mechanism to `safe-doc-push.sh`'s shared-index retry loop's `git add -- "${FILES[@]}"` call: a `git mv`
  removes the OLD path from the index entirely (folded into the destination's R100 pair), so it is a different
  shape from the "tracked but missing" case the script's own `reassert_renames`/line-~976 deletion comment already
  handles correctly — `git add` on a path with no index entry and no disk file is a hard, deterministic
  `fatal: pathspec ... did not match any files`, identical on every retry (matches `commit_failure_is_retriable`'s
  own framing of a deterministic-vs-transient failure, just one step earlier, at `git add` rather than
  `git commit`). Isolated-worktree mode (`SDP_ISOLATED=1`) does NOT reproduce (confirmed, same harness) because its
  copy loop starts from a fresh `origin/$BRANCH` checkout where the old path is still a genuinely-tracked file at
  that point, so the deletion-propagation branch it already has is the correct shape there. Corrected the
  Recommended decision section + reworded todo 2 accordingly (struck through, not deleted, for provenance); did not
  attempt the fix itself (todo 2, separate scope/todo). Left the repro script in place (`Delete-when: NA`, keep
  until todo 2 lands and is verified against it) as a ready-made regression harness for whoever picks up todo 2.
- **2026-08-15 (slot-14, infra)**: Root-caused and fixed todo 2 WITHOUT needing the full 24+-entry stash-pile
  reproduction (left as its own separate todo 1, not attempted here). Empirically confirmed via a real local repo
  (not simulated) that `git add -- <path>` fatals with `pathspec '<path>' did not match any files` for a path that is
  tracked-but-missing-from-disk ONCE its deletion is already staged in the index (the index has no entry left to
  "add") — reproduced on the exact real-world shape this incident hit: the archival SSOT has the caller `git mv` the
  plan BEFORE invoking `safe-doc-push.sh`, so the OLD path is already index-absent by the time the script's own
  `git add -- "${FILES[@]}"` runs, and that ONE combined call aborted staging of every OTHER named file too on the
  very first attempt (not just on a retry). Fixed by replacing the single combined `git add` with a new
  `stage_named_files()` that stages per-file and, for a missing-from-disk path, checks the INDEX directly
  (`git ls-files --error-unmatch`) rather than trusting `git add`'s exit code — distinguishing "needs staging" from
  "already staged, nothing to do" from "never existed anywhere, a real caller error" (the last case still fails
  loudly, naming the path). Separately found and fixed a second, related defect in the same block:
  `KNOWN_RENAME_SOURCES` (which `reassert_renames()` uses to re-stage a rename's deletion half after a reconcile) was
  captured via `git diff --cached --name-status -M`, which requires the rename to already be staged at that exact
  point — true for the shared-index path, but FALSE for the isolated-worktree path (the default), whose copy loop
  only `cp`/`rm -f`s the caller's files onto disk before the child re-execs and captures `KNOWN_RENAME_SOURCES` — so
  it was silently EMPTY on every isolated-mode run, permanently disabling `reassert_renames()` on the very path this
  incident's first invocation hit. Fixed by re-deriving `KNOWN_RENAME_SOURCES` from the `FILES` array directly
  (absent-from-disk + present-in-HEAD), independent of whether anything has been staged yet. Added
  `tests/test_safe_doc_push_extreme_quarantine_rename_survives.bats` (6 new cases, incl. one that reproduces the
  pre-fix fatal verbatim against a real repo for direct comparison) — full `tests/test_safe_doc_push_*.bats` suite
  (54 cases total) green, no regressions. Todo 1 (the extreme-stash-pile scratch-repo reproduction) and todo 3
  (lowering the "24 entries is extreme" bar) are separate, unattempted P1/P2 todos above — this fix addresses the
  content-loss mechanism directly and does not depend on reproducing the stash-pile branch specifically.
