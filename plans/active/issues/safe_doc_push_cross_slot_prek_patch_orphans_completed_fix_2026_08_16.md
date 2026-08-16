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
status: open
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
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
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
resolved_by:
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
  `/plans/archive/issues/safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md` (archived since — this doc
  was in `plans/active/issues/` when slot-16 wrote this note) — a non-content rebase
  failure (e.g. the literal git usage error "Cannot rebase onto multiple branches", `index.lock`) used to be treated as
  a genuine content conflict and hard-exit 3; now it's classified and retried instead.
- `plans/archive/issues/safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md` (+31/-3, archived since): the doc's own
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

- [ ] [INFRA] P2. **Ship the recovered fix.** Pop stash `d7c6b862ebce96bde257bb58b6fd9a17d829d414` (verify it's still
      the expected 2-file diff before popping — a lot of other slots also push safety-snapshot stashes to this same
      list), locate or rewrite `tests/test_safe_doc_push_rebase_failure_classification.bats` per this doc's "What's
      still missing" section, run the full `quality-gates.sh` (this is a `scripts/dev/` code change, not a pure
      doc/plan-flip), and ship via `quickmerge --agent --files 'scripts/dev/safe-doc-push.sh
      plans/archive/issues/safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md
      tests/test_safe_doc_push_rebase_failure_classification.bats'`. Commit message MUST credit the recovery lineage
      (cite this issue doc + the original slot-14 authorship) rather than presenting it as new work. **Done when**: the
      fix is live on `origin/live-defi-rollout`, QG green, and the stash is dropped only after the push is verified
      landed (`git merge-base --is-ancestor`).
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
