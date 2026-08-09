---
doc_type: issue
title: safe-doc-push.sh prints ✅ success having committed nothing — new untracked files read as "already matches HEAD"
summary: >-
  safe-doc-push.sh exited 0 and printed "✅ Named files already match HEAD (a concurrent session landed identical
  content) -- treating as success" for five brand-new files that were NOT in HEAD and were never committed. The fallback
  fires when nothing ends up staged, then infers "already landed" from a no-diff-vs-HEAD comparison — but for a file
  absent from HEAD, "no diff" means "not there", not "identical". Under sustained concurrent write the staging step is
  exactly what fails (a foreign autostash sweep unstages the named paths), so the false-success path triggers precisely
  when the tool is most needed. An agent trusting the exit code would flip a plan checkbox for work that is not in git —
  the false-progress class CLAUDE.md calls its #1 problem, inside the tool built to prevent it.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [git, tooling, safe-doc-push, contention, false-progress, multi-agent]
related:
  [
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Hit live 2026-08-09 (slot 4 interactive session) while filing the AO context-lifecycle issue docs; reproduced across
  four consecutive invocations under concurrent write from a peer session in the same checkout.
depends_on: []
context_scope:
  [unified-trading-pm/scripts/dev/safe-doc-push.sh, /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md]
---

# safe-doc-push.sh reports success having committed nothing

## What happened

Five new issue docs were passed to `safe-doc-push.sh --files`. It printed:

```
  -> unstaging foreign path picked up from a concurrent process sharing this checkout: <peer file>
fatal: Unable to create '.../.git/index.lock': File exists.
  nothing staged for the named files -- checking if content already matches HEAD
✅ Named files already match HEAD (a concurrent session landed identical content) -- treating as success.
```

and exited **0**. The five files were untracked before the run and untracked after it — `git log -- <file>` returned
nothing for every one of them. Nothing was committed and nothing was pushed.

## Root cause

The fallback is sound for its intended case: two sessions racing to write the SAME edit to an EXISTING tracked file,
where the peer's commit landed first and the local copy now matches HEAD — correctly "already done".

It is wrong for a file that does not exist in HEAD at all. The comparison it makes ("does the named path differ from
HEAD?") returns "no difference" for both:

- a tracked file whose content matches HEAD → genuinely already landed ✅
- an untracked file absent from HEAD → **nothing to compare, nothing landed** ❌

The second case is read as the first.

## Why the timing makes it worse

The fallback is only reached when _nothing ends up staged_. Under sustained concurrent write that is the normal outcome,
not an edge case: a peer's `git pull --rebase --autostash` sweep unstages the named paths mid-run (observed repeatedly —
`git add` succeeded, then `git commit -- <paths>` failed with `pathspec ... did not match any file(s) known to git`). So
the false success fires exactly when contention is highest and the caller most needs a truthful answer.

## Blast radius

Any agent following the Commit+Push+Flip rule takes a 0 exit as proof the doc shipped and flips its plan checkbox in the
same turn. That records shipped work that is not in git — and because the local file still exists on disk, a later
session sees the content present and has no reason to suspect it was never committed. This is the exact false-progress
failure mode `/codex/12-agent-workflow/commit-push-flip-rule.md` exists to prevent.

## Todos

- [x] ✅ [SCRIPT] P1. Fix the fallback: before claiming "already matches HEAD", require the path to EXIST in HEAD
      (`git cat-file -e HEAD:<path>`). A path absent from HEAD must fall through to a real failure, never a success.
      Done-when: a test passes a new untracked file with staging forced to fail and asserts a NON-zero exit. —
      unified-trading-pm@963f8e670
- [x] ✅ [SCRIPT] P1. Make the success claim self-verifying end to end: after the commit step, assert
      `git log --oneline -1 -- <each named file>` is non-empty, and after the push assert
      `git branch -r --contains HEAD` includes the target branch. Report success ONLY on those verified facts, never on
      an intermediate command's exit code. Done-when: a test with a stubbed no-op commit asserts a non-zero exit. —
      unified-trading-pm@e169367bf
- [ ] [SCRIPT] P2. On the `index.lock` contention path specifically, distinguish "could not stage" from "nothing to
      stage" in the log line — the current wording ("nothing staged for the named files") reads as the benign case when
      it is actually a hard failure. Done-when: the two produce distinct messages and distinct exit codes.
- [ ] [SCRIPT] P2. Add a documented escape hatch for a checkout under sustained foreign write, since retrying in place
      cannot converge: land from a separate clone (what unblocked this incident) or fail loudly with that instruction.
      Done-when: the script prints the recovery path after N failed attempts instead of looping.

## Progress Log

- 2026-08-09 — Found while filing the AO context-lifecycle issue docs. Four consecutive `safe-doc-push.sh` invocations
  failed to land five new files while the peer session held the shared index; the fourth reported ✅ success. Docs were
  ultimately landed from an isolated clone (`eb2800912f`), touching no foreign lock or WIP.
- 2026-08-09 (slot 33) — Todo 1 shipped: added `files_exist_in_head()` (`git cat-file -e HEAD:<path>` per named file)
  and gated the "already matches HEAD" fallback on it passing, not just a quiet `git diff`. Reproduced the incident's
  actual mechanism (a stale `.git/index.lock` making `git add` fail while `git fetch`/no-op `git pull` still succeed —
  verified empirically) in a new end-to-end bats suite,
  `tests/test_safe_doc_push_untracked_file_never_false_success.bats`: confirmed it fails (false ✅, exit 0) against the
  pre-fix script and passes (non-zero exit, no false-success message) against the fix; a control case confirms the
  genuine already-landed-tracked-file short-circuit still works. Full existing suite
  (`test_safe_doc_push_failure_classification.bats`) still green. unified-trading-pm@963f8e670.
- 2026-08-09 (slot 11) — Todo 2 shipped: added `verify_files_in_history()` (`git log --oneline -1 -- <path>`
  non-empty per named file) and `verify_push_landed()` (`git branch -r --contains HEAD` lists `origin/${BRANCH}`),
  gated on both instead of trusting an intermediate command's exit code alone. Applied to all four success
  declarations: the pre-commit "already matches HEAD" fallback, the post-commit "nothing to commit" fallback, a
  real `git commit` exit 0 (right after `committed=true`), and `git push` exit 0. A verified-false claim now exits
  8 (documented in the script's EXIT CODES header) instead of printing a false ✅. New suite
  `tests/test_safe_doc_push_self_verifies_end_to_end.bats`: a stubbed no-op `git commit` (exit 0, creates no real
  commit) and a stubbed no-op `git push` (exit 0, doesn't update the remote-tracking ref) both now exit 8 instead
  of falsely reporting success; a genuine end-to-end success still verifies and prints the branch-contains proof.
  Full existing suite (`test_safe_doc_push_untracked_file_never_false_success.bats`,
  `test_safe_doc_push_failure_classification.bats`) still green (12/12 total). unified-trading-pm@e169367bf.
