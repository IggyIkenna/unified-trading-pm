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
      code path already handling this shape correctly. Additionally (slot-25): confirmed the exact mechanism with a
      minimal `git init` sandbox — `git add -- old.md new.md` (bulk, AND solo `git add -- old.md` alone) both fail
      with the identical pathspec error the instant `old.md` has been `git mv`'d away, independent of any stash
      state at all.
- [x] ✅ [SCRIPT] P1. Fix `safe-doc-push.sh`'s shared-index `git add -- "${FILES[@]}"` step (around the retry loop,
      `scripts/dev/safe-doc-push.sh`) so a named `--files` entry that is the OLD side of an already-`git mv`'d
      rename (no index entry, no disk file — NOT the "tracked but missing" shape `reassert_renames`/the deletion
      comment at line ~976 already handle) is skipped from the explicit `git add` call rather than passed to it
      verbatim, mirroring the isolated-worktree copy loop's existing deletion-propagation branch. Add a regression
      test covering this exact shape at LOW stash-pile size too (the extreme-quarantine framing was a red herring —
      don't gate the fix or its test on a large stash pile). Repo: unified-trading-pm. — ✅ **authoritative fix
      landed by slot-14** (`stage_named_files()`, replacing the single combined `git add` with per-file staging
      that checks the INDEX directly for the missing-from-disk case — needs-staging vs already-staged vs a genuine
      caller error — plus re-deriving `KNOWN_RENAME_SOURCES` from `FILES` directly, absent-from-disk +
      present-in-HEAD, which ALSO fixed a second defect: the old `-M`-diff-based detection was silently empty on
      every isolated-worktree run, permanently disabling `reassert_renames()` there; see Progress Log for full
      detail + the 6-case bats suite). Slot-25 independently converged on the same mechanism (excluding
      `KNOWN_RENAME_SOURCES` from the bulk `git add`) via a separate scratch-repo sandbox before seeing slot-14's
      landed work; deferred to slot-14's version on reconciliation since it is strictly more complete (closes the
      isolated-mode detection gap slot-25's own approach did not). Slot-25 kept one additive piece on top:
      `sdp_recover_named_from_any_stash()`, a narrower, independent safety net (any named `--files` path missing
      from disk+index gets searched for across every stash entry and restored before a staging failure — covers
      the separate residual case of a quarantine cycle's `protected` check genuinely missing a path for some other
      reason; explicitly excludes any current rename source, since that function initially had a real bug where it
      resurrected a rename's OLD path from an unrelated stash entry, undoing the rename it was meant to help land
      — caught and fixed in the same session, see Progress Log). Regression coverage:
      `tests/test_safe_doc_push_extreme_quarantine_rename_survives.bats` (slot-14, 6 cases) +
      `scripts/dev/test-safe-doc-push-git-mv-rename-shared-index.sh` (slot-25, 0-stash-entry deterministic) +
      `scripts/dev/test-safe-doc-push-stash-recovery.sh` (slot-25, the safety-net's own shape) — all green, plus
      both `repro-safe-doc-push-extreme-stash-rename-{drop,loss}.sh` harnesses confirm no regression.
- [ ] [SCRIPT] P1. **RESIDUAL GAP found 2026-08-15 (session resumption, slot-2), post-fix**: `stage_named_files()`'s
      "already-staged, nothing to do" handling does NOT cover the case where the CALLER runs `git mv <old> <new>`
      themselves BEFORE ever invoking `safe-doc-push.sh` (as opposed to the script staging it mid-loop, which the
      fix above does handle). Reproduced live on a real archival (`plans/active/issues/sports_is_odds_horizon_bucket_
      blank_timeframe_odds_api_dominant_2026_08_15.md` → `plans/archive/2026_08/issues/...`, this slot's own dirty
      checkout, genuinely 18 pre-existing stash entries — not a synthetic repro): (1) manual `git mv` first, then
      `safe-doc-push.sh --files '<old> <new> <other>'` → fails deterministically on attempt 1/6 with the exact
      pre-fix `fatal: pathspec '<old>' did not match any files` error, twice in a row (not transient — 2 identical
      consecutive failures). (2) `git reset` (unstage everything, leave working tree as-is — old path absent, new
      path present, nothing staged) then re-run the SAME `safe-doc-push.sh` call → succeeds immediately on attempt
      1/6, logging `-> re-staging deletion of rename source` (the `reassert_renames()` path this fix added) and
      pushes cleanly. Both runs hit the SAME "18 entries is extreme, quarantining current dirty tree" branch, so the
      quarantine-stash-pop cycle itself isn't what differs — something about a rename staged via `git mv` BEFORE the
      stash/pop round-trip leaves the post-pop index in a shape `stage_named_files()`'s missing-from-disk check
      doesn't recognize as "already staged", falling through to the old bare-`git add` failure path instead. Not
      root-caused further this session (workaround found and used successfully: `git reset` before invoking the
      script if you already ran `git mv` yourself). Needs the same isolated-scratch-repo reproduction discipline this
      doc's own P1 fix used, specifically exercising `git mv` (not `rm`+`git add`) as the pre-staging step, across a
      stash-quarantine cycle. Repo: unified-trading-pm. — **investigated 2026-08-15 (slot-23, infra): could NOT
      reproduce against current code after 3 faithful attempts, incl. one forcing a genuine rebase + a control run
      against the PRE-slot-14-fix script — see Progress Log for the full evidence.** Leading hypothesis: the live
      repro predated slot-14's fix reaching that checkout. Not marking this done — no fix made, and the mechanism is
      not conclusively root-caused either way, only unreproduced.
- [x] ✅ [SCRIPT] P2. Once fixed, consider lowering the "24 entries is extreme" bar or adding a lighter-weight
      protect-and-restore path that doesn't require a full stash round-trip for the common case (few named files,
      most of the pile pre-existing and unrelated) — the current design pays the highest-risk code path exactly when
      the pile is largest, which is backwards from a safety standpoint. Repo: unified-trading-pm. — lowered
      `EXTREME_THRESHOLD` 10 → 8 in `autostash_guard_bound_backlog()` (scripts/dev/tree-wip-guard.sh), justified by
      the new recovery safety net bounding the residual risk; the round-trip is already skipped when there is
      nothing non-protected to quarantine (`to_quarantine` empty), so the "common case" cost was already close to
      zero — the earlier-engaging threshold is the change that matters here.
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
- **2026-08-15 (slot-25, infra, pass 1)**: Dispatched only the P2 todo; escalated (BLK-a6340305) since it's
  textually gated on the unshipped P1 fix — operator directed absorbing P1 into this task ("go on the side of the
  fuller solution"). Root-caused via code reading + a scratch-repo repro
  (`scripts/dev/repro-safe-doc-push-extreme-stash-rename-loss.sh`) before slot-19's landed correction was visible
  locally: a clean (non-conflicting) divergence already lands the rename correctly via the existing 2026-08-08
  `KNOWN_RENAME_SOURCES`/`reassert_renames` fix, and a genuinely conflicting one already hard-stops safely (UU,
  advisory, recoverable) — neither reproduced the exact silent-loss signature. Shipped `sdp_recover_named_from_any_
  stash()` (last-resort stash search-and-restore) plus the `EXTREME_THRESHOLD` 10→8 tuning against the
  "quarantine" hypothesis. Landed as 53fd9b7174, then hit a rebase conflict on THIS doc against slot-19's
  426bf93bce/535ac5a1b7 (landed concurrently, same file) on pull.
- **2026-08-15 (slot-25, infra, pass 2 — reconciliation)**: Read slot-19's landed diagnosis in full before
  reconciling. Independently verified their claim with a minimal `git init` sandbox (no stash, no autostash, no
  script involved at all): `git mv old new` then `git add -- old new` (and even solo `git add -- old` alone) both
  fail with the EXACT reported `fatal: pathspec 'old' did not match any files` the instant `old` has no index entry
  — this is deterministic git behaviour, present with ZERO stash entries. This falsifies pass 1's own
  "extreme-quarantine" framing exactly as slot-19 found; their root-cause diagnosis is correct and independently
  reproduced. Reconciled the doc keeping BOTH sessions' work (this Progress Log, the corrected Recommended
  decision, todo 1's evidence) rather than overwriting either. Implemented the actual fix on top: excluded every
  `KNOWN_RENAME_SOURCES` path from the bulk `git add -- "${FILES[@]}"` call (a clean staged rename's source needs
  no re-`add` — it's already correctly staged as part of the R100 pair; `reassert_renames()`, unchanged, still
  handles the case where a reconcile decomposes it into a genuine unstaged delete). `sdp_recover_named_from_any_
  stash()` and the lowered `EXTREME_THRESHOLD` from pass 1 are KEPT as independent defense-in-depth (a different,
  still-real risk: a quarantine cycle's `protected` check genuinely missing a path for some other reason) — neither
  overlaps with nor is contradicted by this fix. Added a new deterministic 0-stash-entry regression test
  (`scripts/dev/test-safe-doc-push-git-mv-rename-shared-index.sh`) directly mirroring slot-19's control repro shape,
  and re-ran slot-19's own `repro-safe-doc-push-extreme-stash-rename-drop.sh` plus this session's own two
  repro/test scripts to confirm the fix closes the loss with no regression anywhere. shellcheck -S error clean on
  every touched/new file. **Caught + fixed a bug in pass 1's own `sdp_recover_named_from_any_stash`**: re-running
  slot-19's repro against the new fix still failed (exit 14, "deletion of named file did not reach origin") because
  that function's missing-from-disk-AND-index check has no way to distinguish a genuinely lost file from a rename
  source's normal, correct, by-design absence — it was resurrecting the OLD path from an unrelated stash entry,
  literally undoing the rename it was supposed to help land. Fixed by excluding any path that
  `git diff --cached --name-status -M` currently shows as the source of a staged rename (must scan the UNFILTERED
  rename list — pathspec-restricting that diff collapses the rename to a plain `D`, which silently defeated the
  first attempt at this same check). All four repro/test scripts pass clean after this correction.
- **2026-08-15 (slot-25, infra, pass 3 — second reconciliation)**: A THIRD independent landing (slot-14,
  `unified-trading-pm@7e03ff2f01`) hit origin on the very next push attempt — same root cause, a more complete fix
  (`stage_named_files()` + the `KNOWN_RENAME_SOURCES` isolated-mode detection fix pass 2 had not found). Read it in
  full before reconciling again. Deferred entirely to slot-14's `stage_named_files()`/`KNOWN_RENAME_SOURCES`
  implementation for the P1 root cause (`git checkout --ours -- scripts/dev/safe-doc-push.sh` during the rebase,
  taking their landed version as the base) rather than keeping pass 2's own competing `_SDP_ADD_FILES`-exclusion
  approach, which — unlike slot-14's — did not close the isolated-worktree `KNOWN_RENAME_SOURCES`-detection gap.
  Re-applied only the genuinely additive piece on top of slot-14's version:
  `sdp_recover_named_from_any_stash()` (with pass 2's rename-source exclusion fix carried forward unchanged) at its
  two call sites. Re-ran every regression/repro script (this session's two tests, slot-19's and slot-25's repro
  harnesses) against the fully reconciled file — all green, shellcheck -S error clean. Net effect for future
  readers: the AUTHORITATIVE P1 fix is slot-14's `stage_named_files()`; this session's `sdp_recover_named_from_
  any_stash()` is a small, independent, additive safety net layered on top, not a competing implementation.
- **2026-08-15 (slot-25, infra, pass 4 — third reconciliation)**: A fourth concurrent landing (slot-2,
  `982f87d110`) hit origin mid-ship: a NEW, genuinely unresolved residual gap in `stage_named_files()` (a
  caller-pre-staged `git mv`, as opposed to the script staging it mid-loop, still hits the pre-fix pathspec error
  under a real quarantine pile — reproduced live, root cause not yet found, workaround documented). This is a
  DIFFERENT, newly-surfaced defect from the one this task's P1/P2 closed — kept slot-2's todo verbatim (unchecked,
  its own P1) rather than absorbing it into this task's scope: it needs its own isolated-scratch-repo root-cause
  investigation (per its own todo text) and this task has already gone three rounds of reconciliation past its
  original P2-only dispatch. Merged without further code changes — this task's own fix (slot-14's
  `stage_named_files()` + this session's `sdp_recover_named_from_any_stash()`) is unaffected by and does not
  address slot-2's finding either way.
- **2026-08-15 (slot-23, infra)**: Dispatched against this doc's original P1 fix todo (todo 2); found it already
  ✅ landed (slot-14) by the time of fresh-pull — no competing implementation attempted (discarded my own
  in-flight `_sdp_goneless_for_add`-based fix, textually equivalent in mechanism to slot-14's per-file staging but
  superseded before it reached a commit; see `git log` for the discarded diff if ever needed — nothing was lost,
  it never left this session's local index). Turned attention to slot-2's still-open residual-gap todo instead.
  Reproduced the exact described shape three separate ways, all against a real local origin+clone (no mocking):
  (a) slot-19's own `repro-safe-doc-push-extreme-stash-rename-drop.sh` harness (10 stash entries, `git mv` before
  invocation) — lands cleanly, both SDP_ISOLATED modes; (b) a custom repro forcing a genuine
  `autostash_rebase_reconcile` (a concurrent peer pushes a commit touching a file this checkout also has
  uncommitted-dirty, so the merge-pull hits "would be overwritten" and falls back to `--rebase --autostash`) —
  lands cleanly, `reassert_renames()` fires and the push succeeds; (c) the same forced-rebase shape but with the
  peer's edit on a DIFFERENT line of the same multi-line sibling file (non-overlapping, so the rebase auto-resolves
  instead of aborting on a real conflict) — lands cleanly. Then ran (b) and (c) again against the script checked
  out at `7e03ff2f01^` (the commit immediately BEFORE slot-14's fix, confirmed via `git log -- scripts/dev/
  safe-doc-push.sh`) as a control for whether the OLD code reproduces slot-2's failure-then-`git-reset`-workaround
  pattern: it did NOT fail — it also landed cleanly on the first attempt. This suggests the mechanism is narrower
  than either this doc or slot-2's finding assumed: an autostash pop that lands on a MOVED HEAD (any divergence
  forcing a real rebase, not only one that touches the rename source's own content — contra this doc's earlier
  "corrupts a RENAME" analysis) appears to decompose a clean R100 staged pair into a genuine tracked-but-missing
  shape before the staging step ever runs, which even the bare pre-fix `git add` already handled correctly. The
  goneless (no-index-entry) shape this whole issue is about therefore seems to require a rebase-FREE first attempt
  specifically — exactly what both repro harnesses in this corpus already exercise, and exactly what green results
  everywhere. Could not identify what differed in slot-2's live session; did not have access to their actual
  checkout state at the time. Leading hypothesis (circumstantial, not proven): their finding is dated "session
  resumption," and a long-running session that last fresh-pulled before slot-14's fix landed (21:49 UTC) would
  still run the old code without an explicit re-pull — which would fully explain both their failure (pre-fix
  bare `git add`, rebase-free first attempt, exactly this issue's original root cause) and their `git reset`
  workaround succeeding (post-reset, `old` becomes plain tracked-but-missing, which the OLD code handles fine too,
  independent of any fix). Left the residual-gap todo open and unchecked (see its own updated annotation above) —
  this is a "could not reproduce," not a "confirmed absent," verdict. Full regression sweep re-run against the
  fully reconciled current file: this session's new `tests/test_safe_doc_push_rename_source_goneless_add.bats`
  (3/3, end-to-end low-stash-pile coverage, updated to correctly attribute the landed fix to `stage_named_files()`
  rather than this session's own superseded approach), both `repro-safe-doc-push-extreme-stash-rename-{drop,loss}.sh`
  harnesses (NO DROP / NO LOSS), and the full `tests/test_safe_doc_push_*.bats` suite (51/51) — all green, no
  regressions.
- **2026-08-15 (slot-17, infra)**: Independently converged on the same could-not-reproduce verdict as slot-23
  before seeing their landed writeup (traced `stage_named_files()`'s branches by hand, then forced a real
  `autostash_rebase_reconcile` cycle via a different mechanism — a local unpushed commit ahead of origin before
  the `git mv`, rather than slot-23's peer-conflicting-edit approach — both against `unified-trading-pm@7e03ff2f01`
  and both landed cleanly). Deferring to slot-23's more complete writeup (their 3-scenario sweep includes a control
  against the pre-fix commit, which mine did not) rather than duplicating it here, and agree with their call to
  leave the todo unchecked — could-not-reproduce is not confirmed-absent. Kept my own repro,
  `scripts/dev/repro-sdp-caller-staged-rename-reconcile-forced.sh` (`Delete-when: NA`), as additional standing
  coverage: it exercises a still-distinct reconcile trigger (ahead>0 from a prior local commit, forcing the retry
  loop's `else` branch unconditionally) from both slot-23's peer-conflict-forced rebase and slot-19/25's
  rebase-free harnesses, so the corpus now has three independently-triggered reconcile shapes covered instead of
  one. No further code change made.
