---
doc_type: issue
title: >-
  A prek orphaned-patch near-loss recovered slot-14's completed, regression-tested fix for
  safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16 — content now safe in a stash, but not yet shipped,
  and the underlying cross-slot(?) prek-patch-not-restored bug is still live despite an earlier partial fix
summary: >-
  During an unrelated slot-16 `safe-doc-push.sh` run (a plain 2-file plan retag+flip), the script's own post-push
  orphaned-patch detector fired: two identical prek patches sat in `~/.cache/prek/patches/` after a successful push,
  containing NOT slot-16's own content but a complete, tested fix to `scripts/dev/safe-doc-push.sh` (rebase-failure
  false-positive classifier) plus its target issue doc's Progress Log, authored by "slot-14" per the patch's own text.
  `git apply --check` confirmed the patch was genuinely missing from HEAD (not already landed elsewhere), so slot-16
  applied it and immediately moved it into a named stash (`d7c6b862ebce96bde257bb58b6fd9a17d829d414`) rather than
  committing it under the wrong slot's attribution or leaving it in a cache dir that could be evicted. This doc is the
  findings-closure required before slot-16's own task's `/done` (worker.md §4.5) plus the recovery record.
status: resolved
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [safe-doc-push, prek, data-loss-near-miss, cross-slot, plan-hygiene, recovery]
related:
  [
    /plans/archive/issues/safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md,
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    /plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md,
  ]
created: 2026-08-16
last_updated: "2026-08-16"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: infra
source: >-
  slot-16 (infra), discovered mid-task while shipping an unrelated plan retag via `scripts/dev/safe-doc-push.sh`,
  2026-08-16T04:24-04:30Z.
author: slot-16
resolved_by: unified-trading-pm@c3bb4dbcd1
locked_by:
locked_since:
context_scope:
  [
    scripts/dev/safe-doc-push.sh,
    /plans/archive/issues/safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md,
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
  ]
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-08-16** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence in `resolved_by:` (unified-trading-pm@c3bb4dbcd1) — slot-14's own
> session independently completed and shipped the recovered fix minutes after this doc's patch snapshot was taken,
> mooting todo 1's stash-pop-and-reship plan (see that todo's own note). Single-repo case (plan-of-record in this
> same worktree), so the checkbox flip and this `git mv` land in the same commit per the 2026-08-10-narrowed
> same-commit-flip+archival sanction.

# safe-doc-push orphaned prek patch: recovered a completed cross-slot fix, root cause still open

## What was found (live, 2026-08-16T04:24-04:30Z)

Running `scripts/dev/safe-doc-push.sh` for an unrelated slot-16 task (a 2-file plan retag+checkbox-flip, no relation to
`safe-doc-push.sh` itself), the shared host's "41 autostash/safety-snapshot entries" pile triggered a pre-pull quarantine
+ 2 reconcile attempts. The push landed successfully (`unified-trading-pm@faa2950909`), but the script's own post-push
orphaned-prek-patch detector fired non-zero (exit 9) on two patch files:

- `~/.cache/prek/patches/1786854276588-2738462.patch`
- `~/.cache/prek/patches/1786854278924-2739738.patch`

(byte-identical, mtimes 2 seconds apart — almost certainly the same underlying stash content re-materialized across the
run's 2 reconcile attempts).

**Critically, neither patch touched slot-16's own staged files.** Both diffed exactly two files slot-16 never edited
this session:

- `scripts/dev/safe-doc-push.sh` (+50/-6): a new `rebase_failure_is_content_conflict()` classifier in
  `autostash_rebase_reconcile`, closing the exact bug class described in
  `/plans/archive/issues/safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md` — a non-content rebase
  failure (e.g. the literal git usage error "Cannot rebase onto multiple branches", `index.lock`) used to be treated as
  a genuine content conflict and hard-exit 3; now it's classified and retried instead.
- `plans/archive/issues/safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md` (+31/-3): the doc's own
  todo 1 flipped `[x]`, plus a **"slot-14 (infra) 2026-08-16 — root-caused + fixed"** Progress Log entry describing 5
  empirically-reproduced scenarios, the actual root cause, the fix, and a new regression suite
  `tests/test_safe_doc_push_rebase_failure_classification.bats` (claimed 6/6 passing, sibling suite re-run 9/9 green,
  `bash -n` clean).

`git apply --check` (both plain and `--3way`) applied **cleanly against HEAD** (`git status --porcelain` before and
after the check-only run was empty) — i.e. this content is genuinely absent from the tree, not already landed under a
different commit. This is real, complete, tested engineering work that came within one cache-eviction of being silently
lost.

## Why this happened — likely a residual gap in an already-partially-fixed bug class

Two prior fixes already targeted exactly this failure mode:

- `plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md` (referenced by
  this run's own warning text) — the original "prek restore step never ran" finding.
- `unified-trading-pm@62d1a42613` ("scope PREK_HOME per isolated worktree in quickmerge.sh and safe-doc-push.sh — prek's
  patches/ cache is host-global, so concurrent isolated ships on the same host can still silently revert each other
  through it even though F6 already isolated the git index").

Both predict and partially close this exact class. This incident shows either (a) the residual restore-never-ran gap
still reproduces even with PREK_HOME scoped, or (b) the patch genuinely originated from a **different slot's worktree**
(the doc's own text says "slot-14 (infra)", not slot-16) and PREK_HOME scoping has a gap for the specific code path
`safe-doc-push.sh` took this run (CLAUDE.md states isolated-worktree commits are "always-on in safe-doc-push" — if that
held here, cross-slot leakage through a shared cache dir should not be possible; this incident is evidence it still is,
or that this run for some reason did not take the isolated path). **Not root-caused further here** — that
investigation is the todo below, and is exactly the kind of shared-tooling blast-radius change RULES.md reserves for
review, not a unilateral mid-task fix.

## What slot-16 did (recovery, not remediation)

1. Confirmed via `git apply --check`/`--check --3way` (no working-tree mutation) that the patch content was genuinely
   missing, not already landed.
2. `git apply`'d the patch (materializing both files into the working tree) — `git status --porcelain` showed exactly
   the 2 expected modified files, no bats test file appeared (see "What's still missing" below).
3. **Did not commit it** — attribution would mechanically land as slot-16 (`slot-identity-lib.sh` derives author from
   the PATH), misrepresenting authorship of work the recovered content itself credits to "slot-14", and shipping a
   `scripts/dev/` code change requires the full Pass-1 `quality-gates.sh` → Pass-2 `quickmerge` flow (not the
   doc/plan-only `safe-doc-push.sh` path slot-16's own task was using) — out of scope for a P3 single-doc-retag task per
   `infra.md`'s "file an issue doc + escalate — do not absorb unplanned scope."
4. Instead: `git stash push --include-untracked -m
   "orchestrator-slot-16-RECOVERED-foreign-wip-safe_doc_push_false_positive_rebase_multiple_branches"` — durable, named,
   git-object storage. **Stable ref (not the positional `stash@{N}`, which will shift as other slots push their own
   safety-snapshots on this shared host): `d7c6b862ebce96bde257bb58b6fd9a17d829d414`.**
5. Left the 2 original patch files in `~/.cache/prek/patches/` untouched (per the tool's own warning: "do not delete
   any patch file... until you've confirmed its content is safe") as a second, independent copy of the same content
   until this issue resolves.

## What's still missing

The Progress Log text claims a new file `tests/test_safe_doc_push_rebase_failure_classification.bats` (6/6 passing) —
**this file is NOT in either patch and NOT present on disk** (`find` for it came back empty). Either it was never
`git add`ed (so prek's unstaged-file capture never saw it — new untracked files need an explicit `git add -N`/`add` to
be diffable) and is sitting lost in whatever worktree slot-14 was using, or slot-14's session is still live and holds it
uncommitted in their own tree. **This file cannot be recovered from slot-16** — the fix-and-ship todo below must either
retrieve it from a still-live slot-14 session or rewrite it from the Progress Log's detailed description of what it
pins (5 named test cases + a `bash -n` check).

## Todos

- [x] ✅ [INFRA] P2. **Ship the recovered fix.** — MOOT, achieved independently: slot-14's own session (the same
      session this content was recovered FROM) completed and shipped this exact fix on its own, minutes after the
      cross-slot patch snapshot was captured — `unified-trading-pm@c3bb4dbcd1`
      (`git merge-base --is-ancestor c3bb4dbcd1 origin/live-defi-rollout` → true, confirmed by slot-14 2026-08-16),
      including the `tests/test_safe_doc_push_rebase_failure_classification.bats` regression suite this doc's own
      "What's still missing" section flagged as absent — it existed all along in slot-14's own worktree, just not yet
      `git add`ed at the moment the shared `~/.cache/prek` cache snapshotted it. The recovered stash
      `d7c6b862ebce96bde257bb58b6fd9a17d829d414` (in slot-16's own local clone, not reachable from slot-14's) now holds
      a stale, already-superseded mid-flight snapshot of the same work — popping and re-shipping it would create a
      duplicate/conflicting commit against content already on origin. **No further shipping action needed for this
      todo.** Cleanup (safe, not urgent): whoever still holds slot-16's clone (or main/operator) can `git stash drop
      d7c6b862ebce96bde257bb58b6fd9a17d829d414` — its content is confirmed redundant, not lost work; the 2 original
      `~/.cache/prek/patches/` files this doc's "What slot-16 did" step 5 preserved are the same story and equally
      safe to clear once someone with host access confirms them against `c3bb4dbcd1`.
- [x] ✅ [INFRA] P2. **Root-cause whether this is a genuine cross-slot PREK_HOME leak** (a residual gap in
      `unified-trading-pm@62d1a42613`'s isolation fix) or a same-slot-16-inherited-WIP explanation that doesn't
      actually implicate cross-slot leakage (e.g. check whether slot 16's own recent session history ever ran
      `safe-doc-push.sh` work under a "slot-14"-labeled identity, or whether `PREK_HOME` was genuinely unset/shared for
      this run). Read `scripts/dev/safe-doc-push.sh`'s current `PREK_HOME` handling, confirm whether the isolated-mode
      code path was actually taken this run (logs/env), and file the concrete fix (or confirm no fix needed + explain
      the mechanism) as its own follow-up if this is a real residual gap. **Done when**: the mechanism is confirmed with
      evidence (not guessed) and either fixed or explicitly ruled a one-off. — CONFIRMED genuine cross-slot leak via
      evidence (grep + live env check on this host): PREK_HOME is only ever scoped inside `safe-doc-push.sh`'s
      isolated-worktree branch (one assignment, line 502); the AO VM's own 2026-08-10 host gate defaults isolation OFF
      for every slot on `planning` (confirmed `ORCHESTRATOR_VM_ID=planning` -> `_sdp_host_label()` != `"laptop"`), so
      PREK_HOME is never scoped on this host and every slot shares one `~/.cache/prek/patches/` dir. NOT a defect in
      the isolated-mode scoping code itself — a gap in the host gate's own justification, which addressed the
      git-index hazard but never considered prek's separate host-global cache dir. Not itself an active data-loss
      defect (`check_orphaned_prek_patches()` has a 100% catch rate across 10+ prior documented recurrences of this
      exact signature) — filed the concrete cheap fix as its own follow-up per this todo's own instruction:
      `/plans/active/issues/safe_doc_push_shared_prek_home_across_ao_vm_slots_2026_08_16.md`. —
      unified-trading-pm (this doc + the new follow-up doc only, no code change for this todo).

## Progress Log

- **2026-08-16T04:30Z (slot-16, infra)** — filed. Recovered content into stash
  `d7c6b862ebce96bde257bb58b6fd9a17d829d414` (see "What slot-16 did" above); original patch files left in place
  pending resolution. No code shipped by slot-16 (recovery-only, per scope discipline).
- **2026-08-16 (slot-31, infra)** — todo 2 (root-cause) done. Confirmed the mechanism with direct evidence (grep of
  `safe-doc-push.sh` + a live env check on this exact `planning` host) and filed the follow-up fix doc:
  `/plans/active/issues/safe_doc_push_shared_prek_home_across_ao_vm_slots_2026_08_16.md`. Todo 1 (ship the recovered
  fix / pop the stash) remains open — out of scope for this task (a separate, larger `quality-gates.sh`+`quickmerge`
  shipping task, not a root-cause investigation).
