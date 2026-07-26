---
doc_type: issue
title:
  agent-orchestrator /done cross-repo checkbox-flip verification can never pass for a task whose own job is to archive
  (git mv away) its own plan_ref file
summary: >-
  `server/verify.py`'s cross-repo PM-flip check (Mode 2) correctly finds a commit touching `plan_ref` via `git log --
  <path>` (which follows a path through its own deletion), but `_diff_flips_checkbox` only inspects that commit's diff
  AT THE LITERAL OLD PATH — a git-mv-plus-edit shows as a pure delete there (the added `[x]` content lives at the new
  archived path in the same commit), so it never finds the flip. The designed fallback (`checkbox_currently_checked`,
  reading `pm_worktree / pm_existing_ref` off disk) also fails, because `pm_existing_ref` is set to `pm_ref_matched`
  (the OLD path, found via the historical git-log match) whenever that branch is non-None -- it never falls through to
  checking whether the NEW (archived) path currently holds the checked-and-flipped content. Net effect: a `[DOC]`
  archival-ritual task that legitimately flips its own todo's checkbox and archives the very file that checkbox lives
  in, in one commit, can NEVER satisfy this gate -- reproduced live on
  `prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-003` (`unified-trading-pm@2641d8844`).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, done-gate, plan-flip-verification, archival, bug]
related:
  [
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md,
  ]
created: 2026-07-26
priority: P2
parent_epic: orchestrator_master
source:
  "worker, slot 6, hit live while completing prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-003 (archive
  the plan via the standard 6-step ritual)"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# /done checkbox-flip verification can't handle a self-archiving finalize task

## What I found

Task `prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-003`'s `done_definition` was literally "archive the
plan doc via the 6-step ritual" — meaning the SAME commit both flips the archival todo's own checkbox (`- [ ]` →
`- [x]`) AND `git mv`s the file from `plans/active/prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` to
`plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`. Committed + pushed as
`unified-trading-pm@2641d8844`; `git log -- plans/active/prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`
correctly shows this commit (git follows a pathspec through its own deletion). `git show --name-status` shows it as `D`
(delete) at the old path + `A` (add) at the new path — NOT a detected rename (`R`) at the default similarity threshold
`verify.py` presumably uses, since the diff also carries real content changes (banner + checkbox flip) on top of the
move.

`/api/slots/6/done` rejected twice in a row with:

```
{"detail":{"msg":"commit '2641d8844' does not touch the plan checkbox at
'plans/active/prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md' — flip the checkbox ...",
"reason":"cross_repo_pm_file_touched_no_checkbox_flip","sha":"2641d8844"}}
```

Reading `server/verify.py` (Mode 2, ~L750-790):

1. `_pm_log_commits_touching_plan_ref` finds the commit (git-log pathspec, as above) — `pm_shas` is non-empty,
   `pm_ref_matched` = the OLD path.
2. `_diff_flips_checkbox(pm_worktree, sha, pm_ref_matched, brief)` for each candidate sha — this almost certainly diffs
   the commit AT THE OLD PATH specifically. Since that path's diff in this commit is a pure delete (no `+` lines — the
   added `[x]` content is attributed to the NEW path, a different pathspec entirely), no flip is found.
   `checkbox_flipped = False`.
3. Fallback: `pm_existing_ref = pm_ref_matched` (non-None, so the "does any candidate path currently exist as a file"
   check is skipped) → `current_pm_text = _read_plan_text(pm_worktree / pm_existing_ref)` reads the OLD path — which no
   longer exists on disk (it was archived away) → returns `None` → `checkbox_currently_checked = False`.
4. Both the diff-based check and the currently-checked fallback fail →
   `reason: "cross_repo_pm_file_touched_no_checkbox_flip"`, `/done` rejected.

**The gap**: step 3's fallback assumes that if `pm_ref_matched` (the OLD path) was found via git-log, it should still be
a real file on disk today. That assumption breaks specifically when the task's own job was to move that file away (an
archival task) — the checked-and-flipped content now lives at the NEW (archived) path, which the fallback never checks.

## Why it matters

Every AO-dispatched `[DOC]` "archive plan X" todo (the standard 6-step-ritual pattern, used repeatedly across this
corpus — sports/tradfi/defi/cefi/prediction batch-finalize plans all end in exactly this kind of todo) will hit this
same rejection whenever the checkbox-flip and the archival `git mv` land in the same commit, which the archival ritual's
own "Done when" text explicitly asks for ("this finalize doc itself gets archived alongside it in the same commit"). A
worker hitting this has no clean self-service fix: splitting into two commits (flip in place, THEN `git mv`) would work
for a FUTURE such task, but can't retroactively fix an already-pushed single commit without rewriting shared history
(banned). This is a structural, repeatable dead-end for the entire finalize/archival todo class, not a one-off.

## Recommended decision

- [ ] [BACKEND] P2. Fix `server/verify.py`'s Mode-2 fallback: when `pm_ref_matched` (or any candidate path) no longer
      exists on disk, fall through to checking the OTHER candidate paths (including a plausible
      `plans/archive/**/<basename>` glob, or by following the git rename explicitly via `git log --follow -- <path>` /
      `git diff -M` to resolve the file's new location) for the checked-and-flipped content, rather than only checking
      the literal historically-matched path. Add a regression test mirroring this exact case: a single commit that both
      flips a plan's checkbox AND `git mv`s the file to `plans/archive/`. Repo: agent-orchestrator.
- [ ] [DOC] P3. Once the fix above ships, consider whether the archival-ritual's own "Done when" text (task_template.md
      / the 6-step-ritual convention) should recommend the safer two-commit split (flip in place → then `git mv`) as a
      workaround until the server-side fix lands, to avoid other workers hitting the same wall in the meantime.

## Progress Log

- 2026-07-26 (worker, slot 6): Filed after two failed `/done` attempts on
  `prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-003`; root-caused by reading `server/verify.py` directly
  rather than guessing. Filing `/blocked` to ask how to proceed with the already-completed archival work's `/done` call.
