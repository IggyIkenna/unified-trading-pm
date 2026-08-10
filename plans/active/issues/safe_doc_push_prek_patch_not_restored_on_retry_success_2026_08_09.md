---
doc_type: issue
title:
  "safe-doc-push.sh: a prek-patch stash of unstaged, out-of-scope files is saved before a retried commit attempt but
  never restored when that retry succeeds — silently drops uncommitted working-tree edits"
summary: >-
  `scripts/dev/safe-doc-push.sh` stages ONLY the caller-named `--files` (by design — this is what makes it safe under
  shared-checkout contention). prek's own pre-commit-hook wrapper independently stashes ANY other unstaged changes in
  the working tree (files outside the commit scope) into a patch file before running hooks, then restores them after —
  this is prek's own mechanism, not something safe-doc-push.sh implements itself. Live-observed 2026-08-09: on a COMMIT
  RETRY (the script's own attempt-2-of-6 loop, triggered by a `plan-hygiene` hook failure on attempt 1 that required
  fixing the staged content and re-running), prek saved a SECOND patch
  (`~/.cache/prek/patches/1786283053921-3898887.patch`) holding unstaged edits to two OTHER files
  (`plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md`,
  `plans/active/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md` — checkbox flips made earlier in
  the same session, not part of this commit's `--files` scope) before the retry's hooks ran. The retry succeeded and the
  script printed `✅ Pushed afd6891bb3 -> live-defi-rollout` — but the script's own visible output never showed a
  matching "Restored unstaged changes from patch" line for THAT SECOND patch (only the first attempt's patch was
  restored). Post-success, `git status --porcelain` was clean and both files' edits (checkbox flips + Progress Log
  entries, made via editor tool calls earlier in the session, never committed) were GONE from the working tree —
  recovered only because the orphaned patch file was still sitting in `~/.cache/prek/patches/` and `git apply` on it
  succeeded cleanly. Without noticing the missing "Restored" line and going looking for the patch file, this would have
  read as ordinary, unremarked data loss — the two edited files would simply have reverted to their pre-session state
  with no error, no warning, and no trace in `git status`.
status: open
nature: issue
asset_group: [ci, ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [safe-doc-push, prek, precommit, data-loss, quickmerge, ci, plan-hygiene]
related:
  [
    /scripts/dev/safe-doc-push.sh,
    /plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
  ]
created: 2026-08-09
author: data_engineering worker (slot 8, prediction_satellite_ao_dispatch_batch8-001)
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: cicd
drift_direction: none
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Found live 2026-08-09 while shipping prediction_satellite_ao_dispatch_batch8-001's line-cap remediation — a
  commit-hygiene-hook failure on attempt 1 forced a retry; the retry's own prek patch (holding unrelated in-session
  edits to two other plan docs) was never restored after the retry succeeded, silently dropping those edits from the
  working tree until manually recovered from the orphaned patch file."
context_scope:
  [
    /scripts/dev/safe-doc-push.sh,
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
  ]
---

# safe-doc-push.sh drops unrelated unstaged edits on a hook-triggered retry

## What I found

`safe-doc-push.sh` is the sanctioned fast path for pure-docs commits (CLAUDE.md § "Git discipline", "pure doc/plan-flip
→ scripts/dev/safe-doc-push.sh"). Its retry loop (attempt N/6) re-runs `git commit` when a hook fails for a
contention-shaped reason and reconciles. Each `git commit` invocation triggers prek, and prek's own patch-based
stash/restore of unstaged changes (files NOT in this commit's staged set) runs around EVERY hook execution — this is
prek's mechanism, invoked implicitly, not something `safe-doc-push.sh` calls directly.

Live sequence observed 2026-08-09 (full raw output in the session transcript):

1. Attempt 1: prek saves patch A (unstaged edits to the 2 unrelated plan docs), runs hooks, hook `plan-hygiene` FAILS (a
   real content issue in the staged files — `check_todo_regression`), prek **restores patch A** ("Restored unstaged
   changes from patch A").
2. Content fixed (staged files edited to resolve the check_todo_regression failure), `git commit` re-invoked (attempt 2
   of the script's internal retry loop).
3. Attempt 2: prek saves patch B (the SAME unstaged edits to the 2 unrelated docs — untouched since attempt 1). Hooks
   run and pass this time. Commit succeeds. Push succeeds (`✅ Pushed afd6891bb3 -> live-defi-rollout`).
4. **No "Restored unstaged changes from patch B" line ever printed.** `git status --porcelain` immediately after was
   clean — the 2 unrelated docs' edits were gone from the working tree, with patch B sitting unreferenced in
   `~/.cache/prek/patches/`.

## Why it matters

This is silent, unannounced data loss for ANY uncommitted, unstaged edit sitting in the working tree at the moment a
`safe-doc-push.sh` (or any prek-wrapped `git commit`) call needs an internal retry. In an unattended, long-running agent
session (the normal operating mode per `agents/worker.md`) this is exactly the shape of loss nobody would catch without
independently noticing the missing "Restored" line and knowing to go recover the orphaned patch file by hand — most
sessions would simply report the task done and move on, having silently discarded real prior work. The immediate
instance here was recoverable (the patch file survives in `~/.cache/prek/patches/` until some future cleanup), but
relying on that cache directory never being cleared, or on an agent noticing the anomaly at all, is not a safety margin
— it's luck.

## Recommended fix

Root-cause is inside prek's own patch stash/restore lifecycle (not `safe-doc-push.sh`'s own logic), so the real fix
likely lives in prek's hook-runner config/wrapper rather than the script itself — needs someone with prek internals
context to confirm whether this is a known prek behavior (patch only restored on the FIRST hook run of a `git commit`
invocation, dropped on subsequent internal retries within the same invocation) or a genuine prek bug. Candidate
mitigations, cheapest first:

1. **Immediate safety net**: `safe-doc-push.sh`'s retry loop should `git stash list` / check for orphaned
   `~/.cache/prek/patches/*.patch` files newer than the loop's own start time immediately after a successful push, and
   loudly warn (not silently succeed) if any exist — turns silent loss into a visible, actionable alert.
2. **Real fix**: whatever triggers prek's own patch save should also guarantee a matching restore on every code path out
   of the hook run, success or failure, first attempt or retry — file upstream against prek if this is confirmed a
   prek-level defect rather than something `safe-doc-push.sh` is doing wrong in how it invokes retries.

## Todos

- [x] ✅ [DEVOPS] P1. Investigate whether this is a prek-level defect (patch restore only wired to the FIRST hook
      invocation per `git commit` call, not to every internal retry) or something `safe-doc-push.sh`'s retry loop is
      doing that suppresses the restore step. Reproduce deliberately (stage a file that fails `plan-hygiene` once then
      passes, with an unrelated unstaged edit present) rather than relying on the live incident alone. — Verdict: NOT a
      confirmed prek-level defect; see Progress Log 2026-08-10 for the full reproduction + reasoning. —
      unified-trading-pm (this doc only, no code change for this todo).
- [x] ✅ [DEVOPS] P1. Add the immediate safety net from the Recommended fix above — unified-trading-pm@24ac737541: added
      `check_orphaned_prek_patches()` to `scripts/dev/safe-doc-push.sh`, called once after a successful push. It
      compares every `~/.cache/prek/patches/*.patch` file's mtime against this run's start epoch
      (`_SDP_RUN_START_EPOCH`, captured before any commit could run); a hit means a patch created during this run
      outlived a successful push, i.e. its restore never happened. Prints a loud, actionable warning and exits 9 (new
      documented exit code) instead of 0. Verified functionally with a standalone positive/negative test (injected patch
      → detected, exit 1 from the check function; no patch → clean exit 0).

      **Reconciled against todo-1's note that `locked_git_commit()`'s `_prek_race_snapshot`/`_prek_race_check`
                  (shipped `f8a307badf`, 2026-08-09) might already cover this**: confirmed it does cover the SAME-PROCESS
                  retry-drops-the-restore scenario from the original incident (the edited file already has an unstaged diff
                  before the snapshot, so a dropped restore on ANY subsequent attempt's commit call changes its post-commit hash
                  and gets caught) — but it is scoped strictly to files already unstaged-dirty at the moment THIS script's OWN
                  `locked_git_commit()` call starts, and only fires around that specific call. It cannot see: (a) a patch left
                  behind by a DIFFERENT process's `git commit` in the same shared `~/.cache/prek/patches/` cache dir (a bare
                  `git commit` outside this script, or a peer session not going through `locked_git_commit`), or (b) a file that
                  only became unstaged-dirty after this script's own snapshot was taken. `check_orphaned_prek_patches()` closes
                  both gaps by checking the shared cache dir directly, once, for the whole run — genuinely complementary, not
                  redundant, so both mechanisms are now kept.

- [x] ✅ [DEVOPS] P2. **RE-SCOPED (2026-08-10, per todo 1's verdict — reproduction did NOT confirm a genuine prek
      defect):** do not file upstream against prek. Instead, document in `scripts/dev/safe-doc-push.sh`'s own header
      comment that a prior live incident (this issue doc) suspected a prek patch-restore defect but a deliberate
      reproduction (2 sequential `git commit` invocations, fail-then-pass hook, unrelated unstaged edit, with and
      without inter-attempt delay) could not reproduce it — the actual risk is the cross-process race documented in
      `prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`, which the checksum safety net
      (`_prek_race_check`) already guards against. — unified-trading-pm@fe47a4b219: added a header comment block to
      `scripts/dev/safe-doc-push.sh` (before `set -uo pipefail`) stating the reproduction verdict and pointing at
      `_prek_race_snapshot`/`_prek_race_check` as the actual mitigation in place.

## Progress Log

- **2026-08-09 (slot 8, data_engineering, `prediction_satellite_ao_dispatch_batch8-001`)**: filed after live-hitting
  this mid-task. Recovered the dropped edits via `git apply` on the orphaned patch file before continuing; did not
  attempt the DEVOPS-scoped fix itself (outside this task's craft/scope — a plan-hygiene tooling defect, not a
  data-pipeline change) — filed here per findings-triage for a same-session fix-vs-file decision.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: RECLASSIFY, conflict-cleared —
  `assigned_vm: NA -> planning`. First audit pass on this doc (no prior marker). All 3 remaining open todos are
  bounded/worker-determinable: todo 1 is a deliberate reproduction with a concrete recipe already specified ("stage a
  file that fails `plan-hygiene` once then passes, with an unrelated unstaged edit present"), todo 2 is a
  fully-specified, additive (non-destructive) code change to `safe-doc-push.sh`'s own retry loop with a stated
  done-when, and todo 3 is a conditional next step naturally sequenced after todo 1's diagnostic verdict (file upstream
  / pin a known-good prek version / document the workaround) — no genuine design ambiguity or operator gate anywhere in
  the doc. Conflict-check: grepped `plans/active/*.md` for `prek`+`patch`/`safe-doc-push` — no active
  `assigned_vm: planning` plan or `ao_satellite_ao_dispatch_batch*` doc covers this specific prek-patch-restore-on-retry
  bug (broad `patch`/`safe-doc-push` hits were unrelated false positives on the common word "patch" or on the
  already-closed `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01` doc's own, different,
  already-shipped mis-attribution fix). Also directly relevant: this exact bug class (a concurrent session's git/prek
  machinery silently discarding uncommitted foreign edits) is called out as a currently-live hazard in this session's
  own `SUB_AGENT_MANDATORY_RULES.md` — worth fixing at the root rather than leaving as a standing risk. Gated finalize
  twin authored:
  `/plans/active/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09_finalize_2026_08_10.md`.
- **2026-08-10 (slot 12, infra, `safe_doc_push_prek_patch_not_restored_on_retry_success-824ee8f3a711`)**: todo 1
  investigated. **Deliberate reproduction** (scratch repo, prek 0.4.12, a local `gate` hook that fails once via a marker
  file then passes, an unrelated file with an unstaged edit present throughout — the exact recipe this todo specifies):
  ran two SEQUENTIAL `git commit` invocations (attempt 1 fails the gate hook, attempt 2 — after "fixing" by letting the
  marker be consumed — passes), matching the live incident's attempt-1-fails/attempt-2-succeeds shape. prek printed a
  distinct `Temporarily saving...`/`Restored unstaged changes from` pair around **both** commits, and the unrelated
  file's unstaged edit survived intact after both. Repeated back-to-back with **zero delay** between the two commits (no
  backoff sleep) to rule out a timestamp/PID patch-filename collision — same clean result, distinct patch filenames both
  times, edit preserved. **Verdict: NOT reproducible as a general "prek only wires the restore to the first hook
  invocation of a `git commit` call" defect** — prek's stash/restore is reliable across repeated sequential invocations
  in an otherwise-uncontended checkout. The live incident's actual mechanism is far more likely the ALREADY-KNOWN,
  ALREADY-PARTLY-FIXED cross-process race documented in
  `prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md` (a concurrent process/session sharing the SAME
  checkout interleaves its own prek stash/restore window with this one, and the later restore can silently reinstate a
  stale snapshot over a newer edit) — that class of bug produces exactly the symptom reported here (a "Restored" line
  present for the first pair but the edit still ending up reverted/dropped) without requiring any defect in prek's own
  single-process logic. Timing note: the checksum-based safety net for that exact race
  (`_prek_race_snapshot`/`_prek_race_check` in `locked_git_commit`, commit `f8a307badf`, 2026-08-09T11:21:14Z) landed
  the SAME calendar day as this incident — plausible the incident's checkout simply hadn't pulled that fix yet, or the
  incident happened in the narrow window before it landed. Either way, that safety net is CONTENT-diff-based (hashes
  every already-unstaged file immediately before and after each `git commit` call and hard-stops on any mismatch), so it
  structurally covers THIS todo's failure signature too, regardless of root cause — it does not care whether the drop
  came from a cross-process race or a same-process anomaly, only whether the content silently changed underneath an
  unstaged edit during a commit call. **Disposition for todo 3**: since the reproduction did NOT confirm a genuine
  prek-level defect, todo 3 (upstream-file / pin-known-good-version / document-workaround) should be RE-SCOPED, not
  executed as originally worded — see todo 3's own updated wording below.
- **2026-08-10 (slot 8, cicd, `safe_doc_push_prek_patch_not_restored_on_retry_success-3e24fb54367b`)**: todo 2 shipped —
  `check_orphaned_prek_patches()` added to `scripts/dev/safe-doc-push.sh`, unified-trading-pm@24ac737541. Started this
  work before todo-1's parallel investigation (slot 12) landed its re-scoping note on this doc; reconciled on completion
  rather than discarding — confirmed by inspecting `_prek_race_snapshot`/`_prek_race_check`'s actual scope (per-call,
  only already-unstaged files at snapshot time, only around this script's own commit calls) that the two mechanisms are
  complementary, not duplicative: the checksum check catches a same-process retry silently reverting an edit it already
  knew was dirty; the new orphan scan catches any leftover patch in the shared cache dir regardless of which
  process/commit-call produced it. Both now ship together. See todo 2's own entry above for the full reconciliation
  reasoning.
- **2026-08-10 (slot 8, cicd, `safe_doc_push_prek_patch_not_restored_on_retry_success-e302dfdaa856`)**: todo 3 shipped
  (re-scoped form) — unified-trading-pm@c692a472e6: added a header comment block to `scripts/dev/safe-doc-push.sh`
  (immediately before `set -uo pipefail`) recording the reproduction verdict from todo 1 — no confirmed prek-level
  defect, do not file upstream — and pointing at `_prek_race_snapshot`/`_prek_race_check` as the mechanism that already
  covers this failure signature regardless of root cause. All 3 todos in this doc are now done and unlocked (`locked_by`
  empty) — archival-eligible per the plan-completion-and-archival-discipline SSOT; will `git mv` to `plans/archive/` in
  a separate follow-up commit (never bundled with the checkbox-flip commit).
