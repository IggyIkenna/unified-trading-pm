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
status: resolved
nature: issue
asset_group: [ao]
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
resolved_by: "agent-orchestrator@587c8db"
locked_by:
---

> **🟢 ARCHIVED 2026-07-28** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's archive-on-resolve rule. Both todos closed:
> `agent-orchestrator@587c8db` (server/verify.py Mode-2/Mode-1 fallback + regression tests); the P3 doc
> follow-up resolved as now-moot.

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

- [x] ✅ [BACKEND] P2. **DONE 2026-07-28 — `agent-orchestrator@587c8db`.** Fixed `server/verify.py`'s Mode-2 (and,
      as a bonus consistency fix, Mode-1) fallback: `_resolve_current_plan_text()` now tries every literal candidate
      path first, then falls through to a `plans/archive/**/<basename>` glob when none exist on disk — no longer
      pinned to `pm_ref_matched` (the historically-matched OLD path) once it's gone from disk. Regression tests added
      mirroring this exact case (a single commit that both flips a plan's checkbox AND `git mv`s the file to
      `plans/archive/`), both cross-repo and single-repo:
      `tests/test_done_gate_plan_flip_hard_reject.py::test_done_accepts_cross_repo_when_checkbox_flip_bundled_with_archival_git_mv`
      and `::test_done_accepts_single_repo_when_checkbox_flip_bundled_with_archival_git_mv`. Full `quality-gates.sh`
      green (1915 passed). See the companion fix in `ao_m3_verify_plan_flip_blind_to_archival_rename_2026_07_26.md`
      (same commit, same root function — the diff-based detection ALSO now follows a same-commit archival rename).
- [x] ✅ [DOC] P3. **RESOLVED — now moot, no doc change needed.** The server-side fix above makes the bundled
      "flip + `git mv`" single-commit pattern (CLAUDE.md's own prescribed archival wording) work correctly through
      `/done` — there is no longer a wall for the two-commit-split workaround to route around. Recommending the
      workaround now would just be extra ritual friction for a gap that no longer exists.

## Progress Log

- 2026-07-26 (worker, slot 6): Filed after two failed `/done` attempts on
  `prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-003`; root-caused by reading `server/verify.py` directly
  rather than guessing. Filing `/blocked` to ask how to proceed with the already-completed archival work's `/done` call.
