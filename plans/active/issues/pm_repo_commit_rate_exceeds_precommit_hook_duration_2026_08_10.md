---
doc_type: issue
title: >-
  PM's commit arrival rate is faster than its own pre-commit hook run, so the drift gate structurally cannot pass --
  quantified root cause of the doc-push livelock, plus three interacting defects that turn it into silent work loss
summary: >-
  Measured 2026-08-10 — `run_hygiene_sweep.sh --precommit` takes 118s on a SINGLE staged file, while
  `origin/live-defi-rollout` gained 60 commits in the preceding hour (mean interval 60s; 80s over 3h). The commit
  critical section is therefore 1.5-2x the commit inter-arrival interval, so a pre-commit drift gate evaluated around
  that sweep fails with near-certainty and the retry loop re-pays the full sweep. This is a structural livelock, not bad
  luck. It is PM-specific because PM is the fleet's single write hotspot — 1318 commits/24h versus 59 for
  agent-orchestrator (22x) and 152 for market-tick-data-service — since every agent in every repo flips plan checkboxes
  here while code repos are written by one agent at a time. Three further defects turn the livelock into silent data
  loss — exit 6 misclassifies prek's re-stage-and-rerun autofix signal as a deterministic content failure,
  `prettier-autostage.sh` refuses to format while behind origin (so the fast path can never self-correct), and the
  exit-5 "transient, just re-run" path leaves the caller's uncommitted edits reverted to HEAD while reporting nothing
  wrong.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [git, push-contention, safe-doc-push, quickmerge, prek, data-loss, multi-agent-safety, big-finding, plan-hygiene]
related:
  [
    /plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md,
    /plans/archive/issues/autostash_pop_restores_foreign_wip_into_the_index_2026_07_17.md,
    /plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/host-concurrency-and-commit-provenance.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: infra
effort: max
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-10 (slot-3) — eight consecutive `safe-doc-push.sh` runs to land two plan docs, two of
  which destroyed the session's uncommitted edits. Operator then asked for the contention itself to be fixed and for the
  AO-versus-PM difference to be explained.
depends_on: []
context_scope:
  [
    unified-trading-pm/scripts/dev/safe-doc-push.sh,
    unified-trading-pm/scripts/quickmerge.sh,
    unified-trading-pm/scripts/hooks/check-branch-drift.sh,
    unified-trading-pm/scripts/hooks/prettier-autostage.sh,
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    /plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md,
  ]
---

# The commit critical section is longer than the gap between commits

## F1 — the numbers (all measured this session, not estimated)

| Quantity                                              | Measured value              | How                                                   |
| ----------------------------------------------------- | --------------------------- | ----------------------------------------------------- |
| `run_hygiene_sweep.sh --precommit` on ONE staged file | **118s** (1:58.43)          | `time bash …/run_hygiene_sweep.sh --precommit <file>` |
| `origin/live-defi-rollout` commits, preceding hour    | **60** (mean interval 60s)  | `git log --since='1 hour ago' --oneline origin/…`     |
| Same, preceding 3 hours                               | **129** (mean interval 80s) | `git log --since='3 hours ago' --format=%ct` + awk    |
| unified-trading-pm commits / 24h                      | **1318**                    | `git log --since='24 hours ago' --oneline origin/…`   |
| agent-orchestrator commits / 24h                      | **59**                      | same                                                  |
| market-tick-data-service commits / 24h                | **152**                     | same                                                  |

**The hook run is 1.5–2x the commit inter-arrival interval.** On average 1.5–2 new commits land on origin during every
single hygiene sweep. A drift gate evaluated around that sweep therefore fails with near-certainty, and because the
retry loop restarts the whole attempt, each retry pays the full 118s again. Six attempts is up to ~12 minutes of hook
CPU whose failure was determined before it started.

## Why this is PM and not AO — the operator's question, answered

It is not that AO is better engineered. **PM receives 22x agent-orchestrator's commit volume** (1318 vs 59 per 24h),
because PM is the fleet's single write hotspot by design: every agent working in every repo commits its plan-checkbox
flips here (the Commit+Push+Flip HARD RULE), while a code repo is normally written by one agent at a time. AO's own repo
sees a commit roughly every 24 minutes — comfortably longer than a hook run — so the same scripts, the same hooks, and
the same drift gate never livelock there. The defect is not in AO's or PM's tooling differing; it is that a fixed
~2-minute critical section is safe at one commit per 24 minutes and structurally unsafe at one per 60 seconds.

This also means the problem gets monotonically worse as fleet concurrency grows, and no amount of retry tuning fixes it
— retries lengthen the critical section, which is the thing that has to shrink.

## F2 — exit 6 misclassifies prek's autofix signal as a deterministic content failure

Observed twice this session. Every sub-check reported ✅ and the sweep printed its own
`✅ plan-hygiene pre-commit: staged files clean.`, yet the run exited 6 with:

```
❌ COMMIT REJECTED BY A PRE-COMMIT HOOK -- this is a DETERMINISTIC content failure, NOT contention.
   Retrying will fail identically. Do NOT re-run this script until the content is fixed.
```

The real condition was prek's standard `- files were modified by this hook` — an autofix landed, so the correct response
is re-stage and re-run, which succeeds. `commit_failure_is_retriable()` classifies purely by `- hook id:` lines, so
"this hook rejected your content" and "this hook fixed your content" are indistinguishable to it. The message actively
instructs the next agent to stop when re-running is exactly right.

## F3 — `prettier-autostage.sh` refuses to format while behind origin

It prints
`skipping format (the drift gate will block this commit; avoids leaving reflow residue that stops slot FF-sync)` and
exits 0. Under F1 the tree is essentially always behind, so the docs fast path can never self-format. The three defects
compose into a closed loop with no exit:

1. behind origin → prettier declines to format
2. unformatted content is committed → the hygiene hook autofixes it
3. autofix trips `files were modified by this hook` → F2 reports a deterministic failure and says do not re-run

Breaking any one link breaks the loop. The sequence that actually works today is **reconcile → format → commit**, and
nothing in any of the three scripts tells the caller that.

## F4 — the exit-5 path destroys uncommitted work and reports "transient, just re-run"

Twice this session, `SCRIPT_EXIT=5` ("Exhausted 6 attempts … this is transient, not a defect. Re-run.") left the
caller's uncommitted edits to a TRACKED file reverted to HEAD content. Untracked files in the same `--files` list
survived both times. The content was recoverable from `stash@{0}` (verified complete — correct frontmatter, correct todo
count, both disposition markers), but only by explicitly going and looking; nothing in the exit path suggests the tree
was touched.

This is the same family as
[`/plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`](/plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md)
and its recorded `✅ Named files already match HEAD (a concurrent session landed identical content)` false-success — but
this instance is on the **exhausted-retries** path rather than the already-matches-HEAD branch, and the exit-5 wording
makes it worse: it tells the agent the tree is untouched and the fix is to re-run.

## F5 — a live instance of cross-file corpus interaction

While this session's push was in flight, a peer archived `ao_model_main_agent_as_first_class_slot_2026_08_10.md` and its
commit message records "repoint 3 referrers". This session's doc referenced that file too, but was still uncommitted, so
the peer's referrer sweep could not see it — and `check_reference_paths` then failed on THIS session's file because of a
commit that touched a completely different file.

Worth recording because it is the concrete counterexample to "if two commits touch different files they are
independent". The plan gates are corpus-level: `check_todo_regression` reads its baseline via
`git show origin/live-defi-rollout:<path>`, `check_depends_on_graph` walks 809 docs, and `check_reference_paths` /
`check_archive_candidates` / `check_ag_closeout_linkage` / `check_na_corpus_ratchet` are all corpus-scoped. Because they
run `--only <staged paths>` in precommit, an invariant broken by the _interaction_ of two commits on different files is
caught by neither commit's own run, and surfaces later at the promote-PR full QG.

## F6 — a peer session's dirty files make prek revert the hook's own autofix, then drift kills the retry

Captured verbatim from a live attempt this session, and it is the mechanism that ties F1–F4 together:

```
mixed line ending.......................................................Passed
Hook changes conflicted with the saved unstaged changes. Reverting the hook changes
Restored unstaged changes from `~/.cache/prek/patches/1786356290760-69280.patch`
Unstaged changes detected. Temporarily saving them to `~/.cache/prek/patches/1786356420446-38313.patch`
Conventional Commit.....................................................Passed
Locked-plan deletion gate...............................................Passed
Enforce slot·host commit identity.......................................Passed
Check branch drift (are you behind origin?).............................Failed
  ⚠️  BRANCH DRIFT: You are 1 commit(s) behind origin/live-defi-rollout
```

What happened, in order:

1. prek saved the working tree's **unstaged** changes to a patch. In a shared slot checkout those are a _peer session's_
   dirty files (here, two `defi_*` plans a concurrent session was editing), not the caller's.
2. The full hook chain ran and **passed**, including the 118s hygiene sweep, and its autofixes modified files.
3. Restoring the peer's saved patch **conflicted with the hook's own autofix**, so prek discarded the hook changes —
   `Reverting the hook changes`.
4. prek re-ran the whole chain from scratch (second patch id, 130s later — consistent with the 118s measurement).
5. That second run reached the drift gate, by which time origin had moved, and the commit died.

So the caller pays the sweep **twice per attempt** and still commits nothing. Note the two patch timestamps differ by
130s: the 118s sweep is being paid, discarded, and paid again inside a single attempt.

The load-bearing consequence: **any foreign uncommitted WIP in the shared checkout is sufficient to make a
corpus-autofixing hook chain unable to commit**, independent of drift. The caller has no way to fix this — the dirty
files belong to another session and must not be touched (per the multi-agent safety rules). This is the same family as
`prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08`, which `safe-doc-push.sh` already detects and
hard-stops on (`exit 7`) in its explicit form; the `Reverting the hook changes` variant above is not detected and falls
through into the retry loop instead.

## F7 — the hygiene sweep hard-codes the checkout's directory NAME, which blocks the worktree mitigation

Hit while landing this very doc from an isolated `git worktree` (the F6 mitigation). The commit was rejected by:

```
ERROR: plans/active not found at <scratchpad>/unified-trading-pm/plans/active
  ❌ Commit-SHA evidence — a staged todo cites <repo>@<sha> that does not resolve to a real commit
```

The worktree was at `<scratchpad>/wt-driftfix-96974`. `check_evidence_backed_completion.py` derives the PM repo root by
**assuming the checkout directory is literally named `unified-trading-pm`**, so in any worktree with a different
basename it looks in a path that does not exist, fails to find `plans/active`, and reports the failure as a **content
violation** ("a staged todo cites `<repo>@<sha>` that does not resolve") rather than as its own path- resolution error.
The staged doc cites no SHA at all — the message is entirely misleading.

This matters more than a cosmetic bug: **it obstructs the single mitigation that demonstrably works.** F6's fix is to
commit from an isolated index, and several sub-agents in the 2026-08-07 audit run independently reached the same
conclusion. If the hygiene gate only functions in a checkout named `unified-trading-pm`, every agent adopting that
mitigation hits a spurious content rejection. Workaround used here: name the worktree's leaf directory
`unified-trading-pm` (e.g. `<scratchpad>/wtpm2/unified-trading-pm`), which makes the derivation succeed. That is a
workaround, not a fix — the check should resolve the repo root from `git rev-parse --show-toplevel`, and a path it
cannot resolve should be a loud infrastructure error, never a content verdict.

## What actually fixes it

Measured constraint: retries are only expensive **before** the first successful commit. Verified live this session —
once `committed=true`, `safe-doc-push.sh`'s subsequent attempts skip the hook chain entirely and are seconds each
(attempt 1 passed all hooks and committed; attempt 2 was a bare rebase+push retry). So the whole problem reduces to
**getting the first commit through once, without re-paying 118s per drift collision**.

Directions, cheapest first — each is a todo below:

- **Make the drift gate advisory when a reconciling wrapper drives the commit.** `safe-doc-push.sh` and `quickmerge.sh`
  both rebase-and-push after committing, so blocking their commit on drift buys nothing that the post-commit rebase does
  not already provide, and costs a guaranteed livelock. A bare human `git commit` keeps the hard gate.
- **Reorder the fast path to reconcile → format → commit** so F3's loop cannot form.
- **Fix F2's classifier** so `files were modified by this hook` re-stages and retries instead of hard-stopping.
- **Make every non-success exit verify the caller's content is still on disk**, and loud-fail with the recovering stash
  ref when it is not.

## Todos

- [ ] [INFRA] P0. **Make the pre-commit drift gate advisory for reconciling wrappers.** Add an explicit opt-in (e.g.
      `DRIFT_GATE_ADVISORY=1`) that `check-branch-drift.sh` honours by WARNING instead of exiting 1, and set it in
      `safe-doc-push.sh` and `scripts/quickmerge.sh` around their own commit calls only — both already rebase before
      pushing, so the invariant the gate protects is still enforced, just after the commit rather than before it. A bare
      `git commit` by a human keeps the hard block, and the existing human-only `SKIP_BRANCH_DRIFT=1` override is
      untouched. **Done when**: a commit driven by either wrapper proceeds while behind origin, the wrapper's
      post-commit rebase still runs, a bare `git commit` while behind still hard-fails, and a regression test covers all
      three. Repo: unified-trading-pm.
- [ ] [INFRA] P0. **Fix the F2 misclassification.** `commit_failure_is_retriable()` must treat a prek failure whose only
      signal is `- files were modified by this hook` (with no hook reporting a content violation) as RETRIABLE —
      re-stage the named files and retry — rather than exiting 6 with "Do NOT re-run this script". **Done when**: a
      simulated autofix-only prek failure re-stages and retries to success, a genuine content rejection still exits 6
      with the hook's remedy line, and both are covered by tests. Repo: unified-trading-pm.
- [x] ✅ [INFRA] P0. **The silent-revert class also hits `quickmerge.sh`, and safe-doc-push's own "already landed"
      heuristic converts it into a FALSE SUCCESS.** DONE 2026-08-11 — unified-trading-pm@91d559ee19. **Root cause was
      not a missing check but a one-argument call-site bug.** `autostash_guard_bound_backlog` (tree-wip-guard.sh) takes
      ($1 protected paths, $2 remote ref); `quickmerge.sh` passed ONLY the remote ref, landing it in the PROTECTED slot.
      `protected` was therefore a branch name matching no path, so once the stash list crossed the guard's >=10
      extreme-backlog trigger it quarantined and `git checkout <branch> --`'d the caller's OWN `--files` — precisely
      what that function's own header says must NEVER happen. Reproduced live TWICE on 2026-08-11 while shipping this
      fix (43 autostash entries on the host, so the trigger was permanently armed): a run naming 5 files had all 5
      reverted mid-flight and carried on. `safe-doc-push.sh`'s call site always passed both args correctly, which is
      exactly why only quickmerge ever exhibited the loss. Shipped: **(a)** the call-site fix; **(b)**
      `_qm_assert_entry_change_landed` — HEAD's blob per named path recorded AT ENTRY, and after the push any path that
      had a real diff at entry whose HEAD blob is still the entry one exits **10** instead of printing a SHIPPED line
      (this also gives `_qm_content_vanished` its first call site — it was DEAD CODE from the day it was written, which
      is why the losses it was built for kept happening silently); **(c)** safe-doc-push's `_sdp_certify_success` gating
      ALL THREE success paths — exit **12** when every named file was already identical to HEAD at entry (the instance-4
      shape: undecidable from inside the process, so it refuses and prints the `git log -1 -- <path>` command that
      resolves it, rather than guessing; `SDP_ALLOW_NOOP=1` opts back into the old semantics) and exit **13** when the
      push landed without the change. The assertion is "moved off the PRE-RUN HEAD blob", NOT "equals your entry blob",
      so hook reflow (prosewrap/prettier) is not a false positive. Tests:
      `tests/test_autostash_guard_protects_caller_files.bats` (5 — incl. a CALL-SITE test on the argument ORDER, the
      only shape that would have caught this; the behavioural tests stayed green throughout),
      `tests/test_quickmerge_landed_content_assertion.bats` (7),
      `tests/test_safe_doc_push_landed_content_certification.bats` (5). Also repaired
      `tests/test_safe_doc_push_untracked_file_never_false_success.bats`, whose `.git/index.lock` premise went inert
      when isolated-worktree mode became the default (a linked worktree has its own index): failing at HEAD, passing at
      HEAD under `SDP_ISOLATED=0` — the mechanism had gone stale, not the fix. Codex SSOT:
      `/codex/12-agent-workflow/host-concurrency-and-commit-provenance.md` § 3a. **Original text:** four measured
      instances 2026-08-10, two of which destroyed this very todo. The sibling todo below covers safe-doc-push's exit-5
      path only; these are different. (1) A comment edit to `scripts/quality-gates-base/qg-host-governor.sh`, staged and
      passing, was silently dropped by quickmerge's autostash/`_qm_restage_target_files` reconcile — the run reported
      SUCCESS and pushed a commit with the OTHER named files but not that one; the edit survived in neither worktree nor
      HEAD (re-applied by hand, shipped as unified-trading-pm@7a6f9a47). Nothing warned. (2) A scoped `--files` run
      pushed a commit containing NEITHER named file — only a peer's untracked test file — while both named files stayed
      dirty on disk (agent-orchestrator@62649fb). (3) This todo, attempt 1: written, pushed, and afterwards CLEAN with
      `ahead=0`, present in neither worktree nor HEAD; unrecoverable from all 4 live stashes (incl. two
      `safety-snapshot: pre-reconcile quarantine`), checked individually. (4) This todo, attempt 2 — THE WORST SHAPE:
      `safe-doc-push.sh` exited **0** reporting
      `✅ Named files already match HEAD (a concurrent session landed identical content) -- treating as success.` It had
      not landed; the edit was reverted BEFORE the script hashed the file, so "matches HEAD" was true for the wrong
      reason. That heuristic cannot distinguish "someone else already pushed your content" from "your content was
      destroyed" — and resolves both to success. An autonomous run would record a green push and move on. **Why
      `_qm_unstage_foreign_paths()` (@bde0cc4a) does not cover this**: it stops FOREIGN work being committed under your
      message; it does nothing about YOUR work being reverted. Separate failure modes, only one fixed. Fix shape: hash
      the named files at ENTRY; before reporting success, require that HEAD contains THAT hash's content — not merely
      that the worktree matches HEAD. On mismatch, fail loudly naming a recovery ref. **Done when**: an induced run
      whose named file is reverted mid-flight exits non-zero naming the recovery ref instead of reporting "already match
      HEAD", and a test covers both branches. Repo: unified-trading-pm.
- [ ] [INFRA] P1. **quickmerge's `--isolated` does not protect its INPUTS.** Isolation re-execs inside a throwaway
      worktree, but STAGE 0.4's reconcile (and the autostash guard it calls) runs against the CALLER's checkout first —
      so the named files can be quarantined and reverted BEFORE isolation ever copies them in. That is how the loss
      above happened on an isolated run. The call-site fix closes the specific quarantine path, but the ordering is
      still wrong in principle: any future reconcile step added ahead of isolation reintroduces it. **Done when**:
      isolation snapshots the caller's `--files` content BEFORE any reconcile touches the caller's tree, and a
      regression test proves an isolated run ships the caller's content even when the caller's tree is reverted mid-run.
      Repo: unified-trading-pm.
- [ ] [INFRA] P1. **A ship script cannot run from an arbitrary worktree — two separate directory-name assumptions.**
      Measured 2026-08-11 while shipping the fix above from a private worktree (the only way to hold uncommitted work on
      a checkout a peer session keeps reverting): STAGE 2 resolved `pre-flight-audit.sh` via
      `WORKSPACE_ROOT=$(dirname $PWD)` and looked for it under `<parent>/unified-trading-pm/...`, failing unless the
      worktree directory is literally named `unified-trading-pm`; then STAGE 1.5's dependency alignment failed because
      the parent held no sibling repos (`aligned: true` in the real checkout, FAILED in the worktree). Both were worked
      around by hand — naming the worktree `unified-trading-pm` and symlinking 30 siblings into its parent. This is the
      same class as F7 (resolve from git, not from the directory name), one level up. **Done when**: quickmerge resolves
      the workspace root without depending on the checkout's directory name, or fails with a diagnosis naming the
      assumption instead of a missing-file error. Repo: unified-trading-pm.
- [ ] [INFRA] P1. **Two interactive sessions in ONE slot checkout destroyed uncommitted work twice in 30 minutes.**
      Measured 2026-08-11 in slot 4: after the quarantine fix above, a peer session sharing this checkout reverted this
      session's tracked edits again (5 files, `git status` clean, content in neither worktree nor HEAD; recovered from
      the `pre-reconcile quarantine` stash by path both times). The `.agent-claim` heartbeat is WARN-only by design and
      did not prevent it. The durable mitigation used here was to stop holding uncommitted work in the shared checkout
      at all and ship from a private `git worktree` — worth making the documented default for interactive sessions
      rather than an emergency manoeuvre. **Done when**: either the collision hook escalates past WARN when a second
      session writes the same checkout, or the shared-checkout ship path is documented as worktree-first with a
      one-command helper. Repo: unified-trading-pm. SSOT: `/codex/05-infrastructure/per-tab-worktrees.md`.
- [ ] [INFRA] P0. **Stop `safe-doc-push.sh` exiting 5 with the caller's edits silently reverted.** Before any
      non-success exit, compare the named files on disk against the content the script was invoked with (hash them at
      entry); if they no longer match, do not print "transient, not a defect — re-run" — print the recovering
      `git stash` ref and exit with a distinct code meaning "your edits are in the stash, not on disk". **Done when**:
      an induced exhausted-retries run with a reverted tracked file reports the stash ref instead of the transient
      message, and a test covers the entry-hash comparison. Repo: unified-trading-pm.
- [x] ✅ [INFRA] P0. **Break F6 — stop the hook chain fighting a peer session's unstaged WIP.** DONE 2026-08-10 —
      isolated-worktree mode is now the DEFAULT in `safe-doc-push.sh` (`SDP_ISOLATED=0` escapes; setup failure degrades
      to the legacy path rather than blocking). Proven 6/6 vs legacy 0/6 under peer noise. Original text: An isolated
      index is the structural fix: have `safe-doc-push.sh` perform its stage+commit in a throwaway `git worktree` (or
      equivalent isolated index) rather than the shared checkout, so prek's patch save/restore cycle only ever sees the
      caller's own files. Several sub-agents in the 2026-08-07 na-eligibility-audit run independently converged on
      exactly this workaround after giving up on the shared index (recorded in the sibling autostash doc), which is
      evidence the pattern works. Failing that, at minimum detect the `Reverting the hook changes` line and treat it the
      way `prek stash/restore race detected` is already treated (`exit 7` with a diagnosis) instead of silently
      retrying. **Done when**: a commit succeeds with unrelated foreign dirty files present in the checkout, and a
      regression test creates foreign unstaged WIP and proves the caller's commit still lands. Repo: unified-trading-pm.
- [x] ✅ [INFRA] P0. **Fix F7 — resolve the repo root from git, not from the directory name.** DONE 2026-08-10 — new
      `scripts/quality_gates/_pm_root.py` resolves by CONTENT (`plans/` + `scripts/quality_gates/` present), applied to
      13 call sites across 11 scripts; verified it resolves correctly given a bogus workspace root and that
      `check_plan_commit_sha_evidence.py` still passes normally. Original text: `check_evidence_backed_completion.py`
      (and any sibling doing the same) must derive the PM root via `git rev-parse --show-toplevel` rather than assuming
      a checkout literally named `unified-trading-pm`, and a path it cannot resolve must be reported as an
      infrastructure error, never as a content verdict — it currently reports "a staged todo cites `<repo>@<sha>` that
      does not resolve" for a doc citing no SHA at all. This is a prerequisite for the F6 worktree mitigation, which
      otherwise fails for every agent that adopts it. **Done when**: the commit- SHA evidence check passes from a
      worktree with an arbitrary directory name, an unresolvable repo root produces a distinct loud error, and a
      regression test runs the check from a differently-named worktree. Repo: unified-trading-pm.
- [ ] [INFRA] P1. **Make `prettier-autostage.sh` format regardless of drift.** Formatting is idempotent and has no
      dependency on origin's state; the current "skipping format while behind" guard is what prevents the fast path from
      ever self-correcting (F3). If the reflow-residue concern behind that guard is still real, satisfy it by formatting
      AFTER the wrapper's reconcile step rather than by declining to format at all. **Done when**: the guard is removed
      or moved after reconcile, a formatted-while-behind commit does not leave residue that breaks slot FF-sync, and the
      F3 loop is demonstrably broken. Repo: unified-trading-pm.
- [x] ✅ [INFRA] P1. **Re-derive the push-governor's validation cap from measured host cores.** DONE 2026-08-10 —
      `_push_gov_validate_default_k()` now mirrors `qg-host-governor.sh`'s `max(2, floor(cores/4))`; measured 8 -> 2 on
      the 10-core operator host. Original text: `push-host-governor.sh` admits a fixed K=8 validation-phase tokens.
      Profiling 2026-08-10 showed the sweep is ~18.6s of real work inflated ~6x to 118s by concurrent hook chains on one
      laptop — 8 concurrent 19s sweeps produce exactly the observed wall time. Mirror `qg-host-governor.sh`'s
      `max(2, floor(cores/4))` derivation instead of a constant. **Done when**: the cap is core-derived, and a measured
      before/after shows per-run sweep wall time on a loaded host materially closer to its idle 18.6s. Repo:
      unified-trading-pm.
- [ ] [INFRA] P1. **Shrink the 118s critical section itself** — profile `run_hygiene_sweep.sh --precommit` per sub-check
      and move anything whose cost is corpus-wide-but-not-staged-file-dependent out of the per-commit path (to the
      hourly sweep or the promote-PR QG). The gate set only needs to be _sound for the staged files_ at commit time.
      **Done when**: the measured precommit sweep on one staged file is materially below the measured commit
      inter-arrival time, with a per-check timing table recorded in this doc's Progress Log. Repo: unified-trading-pm.
- [ ] [INFRA] P2. **Record the AO-vs-PM volume asymmetry in the codex** so the next person does not re-derive it — fold
      F1's table and the "PM is the fleet's single write hotspot" explanation into
      `/codex/12-agent-workflow/host-concurrency-and-commit-provenance.md`, alongside the existing concurrency-cap
      rules. **Done when**: the codex doc carries the measured rates, the dated measurement, and the structural reason.
      Repo: unified-trading-pm.
- [ ] [DOC] P2. **Document the working sequence (reconcile → format → commit) in
      `/codex/05-infrastructure/per-tab-worktrees.md`** as the supported recipe for a contended doc push, and
      cross-reference F4 so an agent seeing exit 5 checks `git stash list` before believing "transient, re-run". **Done
      when**: the codex doc carries the recipe and the exit-5 caveat. Repo: unified-trading-pm.

- [x] [INFRA] P1. **Cross-repo evidence citations still go stale on rebase.** ✅ Done — neither option in the original
      framing was needed. `scripts/dev/reconcile-sha-citations.sh` gained a second pass that asks a question requiring
      no published map and no cross-repo coordination: **is the cited commit reachable from any ref in the sibling
      clone?** A commit reachable from no branch, no remote, and no tag is an orphan a rebase left behind, and its
      landed twin is the same-subject commit on the integration branch whose **patch-id** matches (patch-id is invariant
      under rebase — tree hash is not, since rebasing onto a moved base changes the tree). Runs from the existing call
      site in `safe-doc-push.sh`, and now also inside `quickmerge.sh`'s push-retry loop (each retry rebases and
      re-orphans what the last pass fixed). Prevention half: quickmerge prints `📌 CITE THIS: <repo>@<sha>` after
      post-push ancestry, the SHA that actually landed rather than the pre-rebase one the worker sees at commit time.
      Evidence: unified-trading-pm@7f9bd2a366; 11/11 in `scripts/dev/test-cross-repo-citation-reconcile.sh`, A/B 5/9
      against the pre-change reconciler. Repo: unified-trading-pm.
- [ ] [INFRA] P2. **quickmerge isolation is opt-in until the cached-venv path is proven under load.** The
      miniature-workspace + `~/.cache/qm-iso-venv/<repo>` fix took the isolated re-gate from 18 QG failures to 0 (1913
      passed), but it has been exercised on ONE repo (PM) on ONE host. Before flipping laptop default back on, verify on
      a service repo with a heavier suite and confirm the cached venv stays valid across a dependency bump. **Done
      when**: two repos pass an isolated `--isolated` quickmerge end-to-end and the cache is shown to refresh on a lock
      change. Repo: unified-trading-pm.
- [ ] [INFRA] P2. **Slot 2's PM checkout is wedged and cannot receive any of these fixes.** 81 commits behind, blocked
      on 4 unresolved conflict markers in `scripts/plan-hygiene/na_corpus_baseline.yaml` plus 22 dirty files (~86 min
      stale at 2026-08-10, no `.agent-claim`). Deliberately NOT resolved by this session — it is another session's
      in-flight work and the inherit path assumes CLEAN WIP, not a live conflict. **Done when**: the conflict is
      resolved by its owner (or explicitly abandoned) and slot 2 fast-forwards. Owner: whoever owns that WIP. Repo:
      unified-trading-pm.
- [ ] [INFRA] P3. **`check_chain_set_inclusion` has 3 failing tests, pre-existing.** Verified failing identically at the
      pre-F7 baseline `c7fe11851a`; untouched by this session. Recorded so the next person does not mistake them for
      isolation fallout. **Done when**: triaged or fixed. Repo: unified-trading-pm.

- [x] [INFRA] P1. **Isolated mode left the caller holding a stale untracked duplicate.** ✅ Done — reported live by a
      peer session minutes after isolation shipped: a NEW file pushed from the private worktree never becomes tracked in
      the caller's own checkout, so the caller keeps an untracked file at a path origin now tracks and the next
      `git pull --ff-only` refuses with "would be overwritten by merge … move or remove them" — which reads like a
      conflict and is not one. `_sdp_reconcile_caller_duplicates` now removes exactly the copies that are untracked here
      AND byte-identical to the blob that landed; anything that differs is left in place with a loud warning naming it a
      stale duplicate rather than a conflict. Evidence: unified-trading-pm@f71c12e40a;
      `tests/test_safe_doc_push_isolated_untracked_duplicate.bats` 2/2, A/B against the call-site-removed build fails at
      the `git pull --ff-only` assertion — the peer's exact symptom. Repo: unified-trading-pm.

- [x] [INFRA] P2. **The byte-identity condition in `_sdp_reconcile_caller_duplicates` almost never held for prose
      docs.** ✅ Fixed. The reconciler removed a caller-side leftover only when it was **byte-identical** to the landed
      blob — but prek runs prettier INSIDE the isolated worktree, so for any prose-wrapped `.md` the landed blob is
      re-wrapped and byte-identity never holds. It was a no-op on precisely the file class it was written for. Measured
      3 hits in one session (`plan_alignment_npm_global_eacces_…`, `sit_gate_treadmill_…`, `codex_freshness_ratchet_…`),
      every one a pure re-wrap with ZERO word-level difference; each cost a conflicted pull and once failed an unrelated
      quality gate via the conflict-marker check. Same wrong-property mistake
      `/codex/12-agent-workflow/measurement-claims-discipline.md` names — byte-identity standing in for "same content",
      broken by a formatter that does not change the content. Fix: new `_sdp_same_content()` compares with every
      whitespace run collapsed (same words, same order = same content, differently wrapped), scoped to `.md` ONLY — for
      code, whitespace is semantic and byte-identity stays the sole test. **Also closed the other half**: two of the
      three hits were TRACKED files, which the untracked-only loop never looked at; a tracked, locally-modified,
      content-equivalent doc named in THIS push's `--files` is now synced to the landed version instead of being left to
      conflict on the next pull. The loud-warning path for a REAL content delta is unchanged. Coverage:
      `tests/test_safe_doc_push_isolated_untracked_duplicate.bats` 6/6 — re-wrap recognised, a real word change refused,
      non-`.md` refused on whitespace, and the tracked-sync path asserted. **Caught by its own test**: the first cut
      made byte-identical files `continue` early, silently disabling the ORIGINAL untracked-duplicate removal; test 1
      failed and named it. Evidence: unified-trading-pm@54f9102183. Repo: unified-trading-pm. **Recovery note worth
      keeping**: this very todo was parked mid-session by quickmerge's own `safety-snapshot: pre-reconcile quarantine`
      when the autostash chain hit 65 entries — it announced the quarantine loudly and named the stash, so the text was
      recoverable in full from `stash@{0}` rather than lost. That mechanism worked; the standing hazard it points at is
      the 65-deep autostash pile itself.

- [x] [INFRA] P1. **The host gate silently disarmed the isolation regression test.** ✅ Done —
      `tests/test_safe_doc_push_isolated_identity_preserved.bats` exports `ORCHESTRATOR_VM_ID=planning` to pin the host
      label in its expected author string. When isolation became host-gated (default OFF on a named VM,
      unified-trading-pm@e3a7d5cf43) that export ALSO turned isolation off inside the test, so the test stopped
      exercising the mode it is named for — and then failed outright. Now forces `SDP_ISOLATED=1` and asserts the
      isolated-mode banner appears, so the author assertion cannot pass vacuously again. Evidence:
      unified-trading-pm@f71c12e40a. Repo: unified-trading-pm.

- [x] [INFRA] P1. **quickmerge's behind-origin block was a guess wearing a diagnosis's clothes.** ✅ Done — the ff-only
      pull ran with `2>/dev/null`, so when it failed with `ahead=0` the script INFERRED "working-tree overlap" and
      printed a RECOVERY line telling the agent to `git stash push -- <your-file>`. Hit live this session: the real
      cause was three unmerged index entries left by an earlier stash-apply, git had said so plainly, and the advice
      given would not have fixed it — one whole quickmerge run wasted before the actual message was recovered by hand.
      Now captures git's stderr, classifies `unmerged files` / `unresolved conflict` as its own
      `PRECOMMIT_UNMERGED_INDEX` code with the correct recovery (`git ls-files -u` → resolve → `git add`), and prints
      git's own first line in the overlap branch too, so the inference is always shown alongside the evidence for it.
      The capture uses `… && RC=0 || RC=$?` because `set -e` is active there and a bare assignment would have aborted
      quickmerge outright — verified errexit-safe, and the classifier verified against git's real wording. Evidence:
      unified-trading-pm@f71c12e40a. Repo: unified-trading-pm.

- [x] [INFRA] P1. **Script the two hand-steps that cost a tool call on every commit.** ✅ Done — operator directive
      2026-08-10: "anything which can be scripted in the git workflow for commits and tests should be, so we spend less
      agent credits." Two were costing a round trip each. (1) Prosewrap repair is now automatic: the check gained
      `--only --emit-lines`, which is the only thing in the repo that can distinguish a violation THIS commit introduced
      from the file's pre-existing debt, and `fix_prosewrap_padding.py --scoped` repairs exactly those lines;
      `run_hygiene_sweep --precommit` runs the pair and re-verifies, passing only because the check agrees afterwards,
      never because a fixer ran. (2) `<repo>@PENDING` lets a flip be authored before the ship: the quickmerge push that
      creates the commit substitutes the sha that actually landed, and a staged plan still carrying an unresolved
      placeholder is blocked at commit time. Evidence: unified-trading-pm@a29967623a;
      `tests/test_prosewrap_scoped_autorepair.bats` 5/5 + `tests/test_pending_evidence_placeholder.bats` 5/5. Repo:
      unified-trading-pm.

- [x] [INFRA] P2. **`fix_prosewrap_padding.py` cannot be auto-wired until it is line-scoped.** ✅ Done — line-scoping
      shipped with the item above; the fixer now takes the check's flagged line set and leaves everything else alone
      (asserted directly: the pre-existing corrupted line is byte-identical after a scoped repair, while whole-file mode
      still rewrites both lines for the supervised corpus-remediation path). Evidence: unified-trading-pm@a29967623a.
      Superseded framing, kept for the record: Agents are still hand-repairing prosewrap corruption (a peer did so
      today) even though the fixer exists, because it is whole-file scoped: measured on 25 active plans, it rewrites 10
      of them, one by 51 lines. Those edits are genuine repairs (the corpus check is at BASELINE, not zero — a green
      check does not mean a clean file), but auto-applying them at commit time would attach dozens of unrelated line
      changes to every plan commit, widening the merge-conflict surface on the busiest file class in a repo already
      fighting contention. The check's failure message now names the fixer and this caveat. **Done when**: the fixer
      accepts the check's flagged line set (or a `--only <file>` mode that repairs solely the violations this commit
      introduced), with a test proving it leaves pre-existing corruption elsewhere in the file untouched — then it can
      be wired into the `--only` precommit path as an autofix. Repo: unified-trading-pm.

## CI audit + QG-timing findings (2026-08-10 evening)

- [x] [INFRA] P0. **The QG duration cap was patched in the wrong file.** ✅ CPU-second budget first landed in
      `base-library.sh` (unified-trading-pm@32749169f3) — but PM and every service repo source **`base-service.sh`**,
      which still had the wall-clock check. Verified "on origin" without verifying "in the file that runs": shipped
      mistaken for live. Re-patched in `base-service.sh`. Evidence: pending ship (see Deferred).
- [x] [INFRA] P0. **The re-gate classifier gave a false all-clear on its first real failure.** ✅ It counted `❌` lines
      only; pytest emits `FAILED tests/...` with no `❌`, so a genuine test failure counted as zero and the run printed
      "every content check passed … Do NOT go looking for a content bug" while one was failing. A false all-clear is
      worse than the false alarm it replaced. Hardened to also match pytest-style `FAILED`/`ERROR`/`E`-prefixed lines,
      not just the emoji.
- [ ] [INFRA] P0. **BLOCKED: a peer's uncommitted UTL edit red-lines every PM quality gate on this host.**
      `tests/unit/test_capability_verdict_matrix.py::test_fixture_matches_live_engine_registry` dies with
      `ImportError: cannot import name '_per_vm_shard_backlog' from 'unified_trading_library.manifest_writer._state'`.
      Measured: the symbol IS on `origin/live-defi-rollout`, is ABSENT from the local working file, and the UTL clone is
      `behind=0` with 6 dirty files — so an uncommitted local edit removed it. NOT reverted: that is foreign WIP, and
      destroying it is the exact harm this issue doc exists to stop. **Owner: whoever holds that UTL WIP.** Until it is
      committed or parked, no PM ship can gate green from this checkout. **Done when**: the symbol resolves again and
      the test passes.
- [ ] [INFRA] P1. **One dead evidence citation red-lines the whole repo's promote flow.** `4f901b9916` (written by
      slot-12 at 16:50, a SHA that never existed here — the pre-rebase id of its own commit) failed
      `check_plan_commit_sha_evidence` corpus-wide, failing PM's gate, failing the promote PR — the "QG slice(s) FAILED
      | unified-trading-pm" → "PROMOTION LAG cause unknown" pair repeating hourly all day. Repaired to `72adcb234c`. The
      orphan-healing reconciler CANNOT fix this form: the SHA never existed locally, so there is no object to patch-id
      match. **Done when**: quickmerge refuses to commit a `- [x]` whose citation does not resolve against origin at
      commit time, closing it at the source instead of corpus-wide hours later.
- [ ] [INFRA] P2. **60 of 229 PM bats tests fail and NOTHING gates them.** Measured full run: 169 ok / 60 not ok. PM's
      gate (`base-service.sh`) carries bats as warn-only for service repos; PM's own 30 bats files are not invoked by
      its gate at all. None of the 60 are from this session's five new files. **Done when**: PM's bats suite is either
      gated or its failures are ratcheted.

## Deferred work after 2026-08-10

| Item                                                              | State / why deferred                                                                                                   | Blocked on               |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| ~~Cross-repo citation reconciliation~~                            | **DONE 2026-08-10** — unified-trading-pm@7f9bd2a366; reachability + patch-id, neither design option needed             | —                        |
| `fix_prosewrap_padding.py` line-scoping                           | **Not done** — precondition for auto-wiring it; today it rewrites whole files (10 of 25 sampled plans)                 | nobody; pick it up       |
| quickmerge isolation back to laptop-default                       | **Not done** — proven on one repo/host only; wants a second repo + cache-invalidation check                            | nobody; pick it up       |
| Slot 2 unwedge                                                    | **Operator-owned** — live conflict in another session's WIP, must not be resolved by a third party                     | that WIP's owner         |
| `check_chain_set_inclusion` 3 failures                            | **Not done** — pre-existing, unrelated to this work                                                                    | nobody; low priority     |
| PM CI green (ldr-docs-gate, na_corpus ratchet promotion deadlock) | **Cannot be done yet** — separate CI/promotion defects already being worked by a peer (two issue docs in slot 2's WIP) | that peer's work landing |

| UTL `_per_vm_shard_backlog` foreign WIP | **Operator-owned** — uncommitted edit in a sibling clone; reverting it
destroys another agent's work | that WIP's owner | | Commit-time citation-resolves-against-origin gate | **Not done** —
closes the dead-citation class at source | nobody; pick it up | | PM bats: 60/229 failing, ungated | **Not done** —
pre-existing, none from this session | nobody; pick it up | | Release-tag stall (7 repos), UTL prod trigger, glue runner
228 restarts | **Not done** — untouched CI groups from the alert audit | nobody; pick it up |

**Recommended next item**: unblock the UTL import — it red-lines every PM gate on this host, so nothing else can ship
until it clears. Then the commit-time citation gate, which removes the largest recurring cause of PM promote-flow
stalls. (Superseded recommendation: `fix_prosewrap_padding.py` line-scoping.)

**Superseded**: `fix_prosewrap_padding.py` line-scoping. Agents are still hand-repairing corruption a script already
knows how to fix, and it is the only remaining item that costs time on every affected commit. (Cross-repo citation
reconciliation, the previous recommendation, shipped 2026-08-10.)

## Lessons carried forward (would otherwise be re-learned)

- **A gating unit-test proves nothing about a shipping path.** Four defects shipped or nearly shipped today were
  invisible to code review and to unit tests, and surfaced only by running the thing end-to-end: `.git` is a FILE in a
  linked worktree; isolation re-exec'd the worktree's copy of its own script; a comment between a trailing `\` and
  `bash` detached the env assignments and recursed 116 deep / 722 worktrees; symlinking `.venv` let `uv sync --frozen`
  PRUNE the operator's real environment.
- **A clean-checkout concurrency test measures the easy case.** Legacy mode scores 5/6 on a clean checkout and 0/6 with
  a peer-noise writer. prek only does its patch save/restore when unstaged changes exist, so foreign WIP is the variable
  that matters — not load, not drift.
- **CORRECTION to an earlier claim in this doc**: the core-derived governor cap (K 8→2) was reverted. Three paired
  samples (K=8: 74/30/27s, K=2: 27/37/29s) are indistinguishable; the original 74s was ambient noise. The 118s sweep was
  real but measured WITHOUT isolation — isolation removed the contention that made admission control matter, so K is not
  the lever.
- **Rejected: copying the QG sentinel into the isolated worktree.** A sentinel attests one specific tree, and the
  worktree is deliberately a different tree (named files on origin/HEAD). Copying it would assert a gate result never
  obtained. The full re-gate stays — and it is what caught the F7 P0 already on live-defi-rollout.

## Progress Log

- **2026-08-10 (filed, slot-3 interactive)**: filed after eight consecutive `safe-doc-push.sh` invocations to land two
  plan docs, of which two destroyed this session's uncommitted edits (recovered from `stash@{0}` by extracting the
  single file with `git show 'stash@{0}:<path>'` rather than applying the stash, since the same autostashes also held a
  peer session's `defi_*` WIP). All F1 numbers measured directly this session with the commands in the table. F2/F3/F4
  each observed at least twice. F5 observed once, live, mid-push. Deliberately filed as a SEPARATE doc from
  `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` rather than folded into it: that doc's
  subject is the git-internals stash-interleaving mechanism and its candidate mitigations, whereas this doc's subject is
  the measured rate/duration mismatch that makes the race fire constantly, plus three script-level defects that are
  independently fixable without resolving the git mechanism at all. Cross-linked both ways.

- **2026-08-10 (profiling run — REFINES F1's 118s)**: profiled `run_hygiene_sweep.sh --precommit` per check by
  timestamping its own output lines. In an IDLE isolated worktree the same sweep, on the same single staged plan file,
  totals **18.6s**, not 118s. Breakdown of everything over 1s: Operator-ruling evidence **6.0s**, depends_on DAG
  **5.3s**, Terminal-status-archived **3.9s**, Line caps **1.5s** (remaining ~20 checks are sub-second each). So the
  118s measured in the loaded main checkout is roughly a **6x contention inflation of ~19s of real work**, not an
  intrinsic cost — which changes the fix. Shrinking the sweep helps, but the dominant lever is how many hook chains run
  concurrently on one host: `push-host-governor.sh` admits **K=8** validation-phase tokens, and 8 concurrent 19s sweeps
  on a laptop produce exactly the ~2min per-run wall time observed. Two consequences: (a) the per-check shrink todo
  should target the four checks above, which are ~89% of the sweep; (b) a separate todo should re-derive the validation
  cap from measured host cores rather than a fixed 8, the same way `qg-host-governor.sh` already does
  (`max(2, floor(cores/4))`). Filed as a correction to F1 rather than a new finding: F1's conclusion (hook chain longer
  than commit inter-arrival) holds — this identifies WHY it is that long.

- **2026-08-10 (A/B PROOF under concurrency — operator ask "test under high concurrency")**: built
  `scripts/dev/test-safe-doc-push-concurrency.sh` and ran it on identical configurations (6 workers, one shared
  checkout, a peer-noise writer continuously dirtying two unrelated tracked files for the whole run). Acceptance is
  three-part per worker: content landed byte-identical, no exit-0-without-content, and the CALLER's working-tree copy
  unchanged. **Legacy shared-index mode: 0/6 landed**, every worker `rc=7` (`prek stash/restore race detected`).
  **Isolated-worktree mode: 6/6 landed, 6/6 caller trees intact, 0 violations.** Throughput under a concurrent session
  goes from zero to complete. Note the peer-noise writer is load-bearing: an earlier run against a CLEAN checkout scored
  5/6 for legacy and proved nothing — foreign UNSTAGED WIP is what makes prek's patch save/restore collide with the
  hook's own autofix, which is the F6 mechanism.
- **2026-08-10 (four self-inflicted defects the harness caught, all pre-land)**: recorded because they are the argument
  for the harness existing. (1) `safe-doc-push` gated on `[[ ! -d .git ]]`, but `.git` is a FILE in a linked worktree —
  isolation re-execs into a worktree, so the child exited 2 and EVERY invocation would have failed; fixed via
  `git rev-parse --show-toplevel` (agent-orchestrator-independent, shipped `d93a3dc36d`). (2) isolation re-exec'd the
  WORKTREE's copy of the script rather than the caller's, silently substituting origin's version — a caller on a branch
  predating a fix would run old code with no indication; now re-execs `$_SDP_SELF`. (3) a comment placed between a
  trailing `\` and the `bash` call detached the env assignments, so `SDP_IN_ISOLATION` never reached the child and
  isolation recursed — 116 nested invocations and 722 stray worktrees (272 MB of git admin state) from ONE 6-worker run
  before it was killed by hand; fixed, plus a `SDP_ISO_DEPTH` backstop that hard-fails at depth >= 1 (exit 11) so a
  future handshake bug cannot repeat that blast radius. (4) the first harness had no peer-noise writer and so tested the
  easy case. None of these were reachable by reading the diff.
