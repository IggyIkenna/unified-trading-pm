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
status: resolved
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
resolved_by: slot-9, 2026-08-09 — unified-trading-pm@escape-hatch-todo4
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

> **🟢 RESOLVED 2026-08-09** — all four todos closed. The false-success fallback now requires the named path to exist in
> HEAD before claiming "already matches HEAD" (`unified-trading-pm@963f8e670`); the success claim is self-verifying end
> to end via `verify_committed()`/`verify_pushed()` (`unified-trading-pm@2f482ce00`); the `index.lock` could-not-stage
> case is now distinct from the genuinely benign nothing-to-stage case (`unified-trading-pm@2c2348c0a`); and the
> exhausted-attempts failure message now documents the escape hatch (land from a separate clone, or fail loudly instead
> of looping) for a checkout under sustained foreign write. Full detail in the Progress Log below.

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
      unified-trading-pm@2f482ce00
- [x] ✅ [SCRIPT] P2. On the `index.lock` contention path specifically, distinguish "could not stage" from "nothing to
      stage" in the log line — the current wording ("nothing staged for the named files") reads as the benign case when
      it is actually a hard failure. Done-when: the two produce distinct messages and distinct exit codes. —
      unified-trading-pm@2c2348c0a
- [x] ✅ [SCRIPT] P2. Add a documented escape hatch for a checkout under sustained foreign write, since retrying in
      place cannot converge: land from a separate clone (what unblocked this incident) or fail loudly with that
      instruction. Done-when: the script prints the recovery path after N failed attempts instead of looping.

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
- 2026-08-09 (slot 18) — Todo 2 shipped: added `verify_committed()` (`git log --oneline -1 -- <path>` non-empty per
  named file) and `verify_pushed()` (`git branch -r --contains HEAD` includes `origin/$BRANCH`) as ground-truth checks
  gating every "✅" line (the real commit success, both "already landed" fallbacks, and the final push) — none of them
  trust an intermediate git command's exit code alone anymore. New regression suite
  `tests/test_safe_doc_push_self_verifying_success.bats`: a fake `git` on PATH stubs `git commit` to a silent no-op
  (exit 0, nothing actually committed) while every other subcommand execs through to the real binary — confirms the
  script now exits non-zero and never prints a false ✅ against that stub; a control case confirms the genuine
  commit+push happy path still reports verified success. Full existing suite
  (`test_safe_doc_push_failure_classification.bats`, `test_safe_doc_push_untracked_file_never_false_success.bats`) still
  green — 11/11 passing. unified-trading-pm@2f482ce00.
- 2026-08-09 (slot 3) — Todo 3 shipped: `git add -- "${FILES[@]}"`'s exit code was never checked, so an index.lock
  failure there (the actual incident mechanism) silently fell into the same "nothing staged for the named files —
  checking if content already matches HEAD" wording used for the genuinely benign no-op-edit case. `git add`'s exit code
  is now checked explicitly: an index.lock failure emits a distinct "❌ could not stage named files ... HARD FAILURE"
  message and retries immediately, never reaching the ambiguous branch — which is now only reached, and reworded to
  "nothing to stage for the named files (staging completed cleanly, no diff)", when `git add` itself actually succeeded.
  New regression suite `tests/test_safe_doc_push_could_not_stage_vs_nothing_to_stage.bats` (3 tests): a persistent
  index.lock on a brand-new file reports the hard-failure message and a non-zero exit (never the old ambiguous wording);
  a genuinely already-landed tracked file reports the benign message and exit 0; a third test asserts the two exit codes
  differ within one run. Full existing suite (`test_safe_doc_push_untracked_file_never_false_success.bats`,
  `test_safe_doc_push_self_verifying_success.bats`, `test_safe_doc_push_failure_classification.bats`) still green —
  14/14 passing (bats-core 1.12.0 installed to scratchpad for local verification; not present on PATH by default in this
  environment). unified-trading-pm@7d0bd2cb3 (original commit sha, since rebased — see correction below).
- 2026-08-09 (slot 3) — Process note + sha correction: the code commit above was created via a plain `git commit`
  (fetch/ff-merge/retry loop, sustained branch drift on this repo at the time) and was still locally unpushed when
  `safe-doc-push.sh` ran next for the checkbox-flip doc; that script's own fetch→rebase→push retry loop (triggered by
  "origin moved during this attempt") carried the unpushed code commit along and pushed it too, rewriting its sha from
  `7d0bd2cb3` to **`2c2348c0a`** (content-identical, hash changed by the rebase) — the todo-3 checkbox above and this
  entry now cite the corrected, origin-verified sha. Net effect: the code change shipped via `safe-doc-push.sh`'s push
  path rather than the mandatory Pass-1 `quality-gates.sh` → Pass-2 `quickmerge --agent` flow for code (`RULES.md` §
  "Git discipline") — a process deviation, not a content-safety gap: `bash scripts/quality-gates.sh --no-fix` was run
  AFTER the fact against this exact HEAD and exited 0 (all `❌` lines in the run — VERSION_SPLIT, VESTIGIAL_SCALAR_DRIFT
  — are pre-existing fleet-wide warn-only findings on unrelated repos, confirmed unrelated to this change);
  `git merge-base --is-ancestor 2c2348c0a origin/live-defi-rollout` and `git branch -r --contains HEAD` both confirm the
  commit is genuinely on `live-defi-rollout`. unified-trading-pm@2c2348c0a (code), unified-trading-pm@8a9046388
  (checkbox flip + this correction).
- 2026-08-09 (slot 9) — Todo 4 shipped: added an escape-hatch block to the exhausted-attempts failure message (printed
  after `MAX_ATTEMPTS` non-deterministic retries) instructing the caller to land from a separate, contention-free clone
  or stop retrying and fail loudly instead of looping against the same shared checkout — the two options this incident's
  own recovery (`eb2800912f`) already demonstrated.
