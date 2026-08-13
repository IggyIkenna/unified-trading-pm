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
last_updated: "2026-08-12"
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

- [x] ✅ [INFRA] P0. **Make the pre-commit drift gate advisory for reconciling wrappers.** DONE — the code shipped
      2026-08-10 in unified-trading-pm@e59d4750fa (same-day as this doc's filing) but this checkbox was never flipped;
      caught while re-triaging this doc 2026-08-12. `check-branch-drift.sh` honours `DRIFT_GATE_ADVISORY=1` by WARNING
      and exiting 0 instead of hard-blocking; `safe-doc-push.sh` and `scripts/quickmerge.sh` both `export` it
      immediately before their own `git commit` call and `unset` it immediately after (verified: both scripts contain
      the export/unset pair). A bare `git commit` (the flag unset) still hard-fails, and `SKIP_BRANCH_DRIFT=1` is
      untouched. **What was actually missing**: the regression test this todo's own "Done when" required. Added
      unified-trading-pm@bdc6c3ab52 — `tests/test_check_branch_drift_advisory_mode.bats` (5/5): not-behind exits 0
      regardless of the flag, behind+unset hard-blocks, behind+advisory warns and exits 0, `SKIP_BRANCH_DRIFT` still
      wins, and a static containment check that both wrappers scope the export/unset to their own commit call. Repo:
      unified-trading-pm.
- [x] ✅ [INFRA] P0. **Fix the F2 misclassification.** DONE — shipped 2026-08-10 in unified-trading-pm@e59d4750fa
      alongside the drift-advisory todo above, same unflipped-checkbox gap. `commit_failure_is_retriable()` now returns
      RETRIABLE as soon as it sees `files were modified by this hook`, before even looking at hook ids — by design a
      mixed failure (autofix text plus a genuine unresolved violation in the same run) also classifies RETRIABLE; the
      worst case is one extra attempt, since the retry re-stages the autofix and the _next_ attempt (no longer carrying
      that text) correctly exits 6 on the surviving violation. **What was actually missing**: test coverage for the F2
      case itself — the existing test file only covered pure content rejections and pure drift, not the autofix signal.
      Added unified-trading-pm@bdc6c3ab52 — two new cases in `tests/test_safe_doc_push_failure_classification.bats` (9/9
      total): autofix-only is RETRIABLE, and autofix-plus-content-rejection is RETRIABLE by design (pinned so the
      deliberate one-extra-attempt tradeoff is never mistaken for a bug and "fixed" into a false hard-stop). Repo:
      unified-trading-pm.
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
- [x] ✅ [INFRA] P1. **quickmerge's `--isolated` does not protect its INPUTS.** DONE 2026-08-11 —
      unified-trading-pm@d001c8f879. **The hypothesis this todo was filed on is FALSE, and disproving it was the
      finding.** It claimed STAGE 0.4's reconcile runs against the caller's checkout before isolation copies files in.
      It does not: the isolated child is created `--detach` and STAGE 5's `_qm_checkout_ship_branch` keeps it detached
      for the whole run under `QM_IN_ISOLATION`, so `_qm_stage_0_4_not_behind_gate` — the only caller of
      `autostash_guard_bound_backlog` — sees an empty `git branch --show-current` and skips at every one of its 3 call
      sites. The parent re-execs and exits before reaching that stage too. The blamed mechanism is structurally
      unreachable during an isolated run, in both processes. **The real mechanism**: isolation COPIES `--files` into the
      throwaway worktree but never touches the caller's originals, which sit dirty in the shared checkout for the run's
      full duration — exactly what a CONCURRENT PEER's own extreme-backlog sweep acts on, since any tracked dirty file
      outside _that_ peer's `--files` is fair game once the >=10-entry trigger is armed. This is the only account that
      explains the second measured revert, which happened with no quickmerge of ours running at all. **Fix**: evacuate
      the caller's dirty `--files` into a NAMED stash for the run's duration and restore unconditionally on return
      (`_qm_iso_evac_find` / `_qm_iso_evacuate_caller_dirty` / `_qm_iso_restore_caller_dirty`). Looked up by MESSAGE,
      never `stash@{N}` — `refs/stash` is one ref shared by every linked worktree, so the child's own stash ops shift
      the index underneath us. **Two gaps found in review and closed before shipping**: (1) the restore was reachable
      only on the happy path — the sole trap was `_qm_cleanup_isolation EXIT`, which only removes the worktree — so a
      `set -e` trip, Ctrl-C, SIGTERM or a harness stop would have left the caller's files stashed and their tree showing
      them reverted with a clean `git status`: the exact symptom this issue exists to kill, self-inflicted and WORSE,
      since the marker lives only in scrollback that dies with the process. Now restored from EXIT/INT/TERM via
      `_qm_iso_signal_cleanup`, with three return codes (0 restored · 2 idempotent no-op, silent by design, which is
      what makes the re-fired EXIT trap safe · 1 genuine pop conflict, loud, entry never dropped); SIGKILL stays
      uncatchable and is documented as such rather than papered over. (2) A 15-way concurrent stress test measured **50%
      of the losing side's first `git stash push` failing on `.git/index.lock` contention** with no retry — not data
      loss (a failed push touches nothing) but a real reliability gap. Evacuate now retries the push 3x with backoff;
      restore deliberately does NOT retry the pop, because pop is apply-then-drop and a blind retry could double-apply
      and manufacture a conflict — it re-checks whether the entry still exists instead of reporting a false conflict.
      Re-measured after the fix: 30/30 evacuate, 30/30 restore, 0 leftover stashes. Tests:
      `tests/test_quickmerge_isolation_evacuates_caller_dirty.bats` (14, incl. a SIGTERM-mid-flight case proving the
      caller's dirty file is restored after the process exits 143, a real rc=1 conflict, and a deterministic
      `index.lock` retry proof).
- [x] ✅ [INFRA] P1. **A ship script cannot run from an arbitrary worktree — two separate directory-name assumptions.**
      DONE 2026-08-11 — unified-trading-pm@d001c8f879. Added `PM_ROOT`, resolved by CONTENT (mirroring
      `scripts/quality_gates/_pm_root.py`, the existing precedent): conventional `$WORKSPACE_ROOT/unified-trading-pm`
      first, then this run's own repo, then a content-matching sibling search keyed on `plans/` +
      `scripts/quality_gates/` being present. ~20 call sites migrated off the hardcoded literal. STAGE 1.5 now COUNTS
      real sibling repos before running dependency alignment and skips with a named diagnosis when there are none,
      instead of surfacing a bare `aligned: false` that is indistinguishable from a real regression. STAGE 2's
      pre-flight lookup now separates "no PM checkout resolvable" from "PM resolved but the script is missing".
      **Before**: a differently-named worktree got `not found at <path> — required`, with nothing pointing at the
      directory name as the cause; a sibling-less parent got a misleading alignment FAILURE (`aligned: true` in the real
      checkout, FAILED in the worktree). **After**: the differently-named worktree resolves via content search; the
      sibling-less parent gets `⚠️ Dependency alignment SKIPPED — … has no sibling repo checkouts at all`, naming the
      assumption. Tests: `tests/test_quickmerge_pm_root_resolution.bats` (9, incl. call-site tests asserting the literal
      directory-name assumption is gone from the executed paths). Both were hit by hand while shipping the parent P0
      from a private worktree, which is what surfaced them.
- [x] ✅ [INFRA] P1. **Two interactive sessions in ONE slot checkout destroyed uncommitted work twice in 30 minutes.**
      DONE 2026-08-11 — unified-trading-pm@83debfb40a. **The framing in this todo was wrong, and the correction is the
      main finding.** It said the `.agent-claim` heartbeat "is WARN-only by design and did not prevent it". The measured
      truth: `cursor-configs/hooks/session-start-collision-check.sh`'s live-process signal read ONLY `/proc/<pid>/cwd`
      and `/proc/<pid>/status`, and **macOS has no `/proc` at all** — so on the exact host class where the incident
      happened the scan was a silent structural no-op, counting zero foreign sessions no matter how many were live. Not
      "warned but too weakly": it could never fire. Proved by direct reproduction — a simulated peer process (renamed
      argv0, real cwd under a fake slot) produced ZERO warning from the unpatched hook and the correct warning after the
      fix, on identical input. Shipped: a `/proc`-first, `ps`/`lsof`-fallback path, portable across Linux and macOS,
      leaving the non-blocking contract untouched (`tests/test_session_start_collision_check.bats`, 10/10). Also shipped
      `scripts/dev/ship-from-worktree.sh` (`setup`/`cleanup`), which formalises the private-linked-worktree pattern that
      is the only thing that actually stopped the loss — leaf name derived via `git rev-parse --show-toplevel` rather
      than hardcoded, so it survives the sibling P1 on quickmerge's directory-name assumptions
      (`tests/test_ship_from_worktree.bats`, 16/16; dogfooded against the real slot-4 checkout, with isolation proven by
      the edit being visible in the worktree and absent from the slot tree). **Trap found while building it**: the
      worktree recipe circulated in this session (including in the sub-agent brief) symlinks the throwaway worktree's
      `.venv` at the operator's LIVE venv — a `uv sync --frozen` through that symlink can PRUNE packages out of the real
      environment (measured 2026-08-10; `scripts/quickmerge.sh` already used a shared venv cache for this reason). The
      helper uses the shared cache (`QM_ISO_VENV_CACHE`). **Do NOT read a package COUNT as the damage signal** —
      corrected 2026-08-12, after that framing produced a false alarm here. A later full QG took slot 4 from 388
      packages to 145, which is CONVERGENCE TO CORRECT, not a prune: 145 is what PM's own `uv.lock` declares (slots 2
      and 3 sit at 145 untouched, and `pydantic` is not in PM's lock at all), while slot 5's 388 is the outlier
      superset. The real signal is CAPABILITY — whether the tools the gate needs still run. Codex SSOT:
      `/codex/05-infrastructure/per-tab-worktrees.md`.
- [x] ✅ [OPERATOR] P2. **Decide whether the session-collision check should escalate past WARN.** RESOLVED 2026-08-12 —
      operator chose **option B**; shipped unified-trading-pm@6aba7ca9ff. New
      `cursor-configs/hooks/pretooluse-slot-collision-guard.py`, registered on `PreToolUse`/`Bash` by APPENDING to the
      existing matcher so `block_destructive_commands.py` keeps running (under `bypassPermissions` the
      `permissions.deny` list is discarded, making these hooks the only surviving guardrail —
      `/plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md`). **Blocks** (only with a live
      peer in the slot): a bare `git commit`, `quickmerge.sh --no-isolated`, and `safe-doc-push.sh` under
      `SDP_ISOLATED=0` — the variants that write the SHARED index. **Deliberately does NOT block** default
      `quickmerge.sh` / `safe-doc-push.sh`, which commit from a private worktree and are therefore the REMEDY, not the
      hazard; blocking them would push an agent toward a bare `git commit`, strictly worse. Anything already inside a
      linked worktree is exempt on the same principle, tested via `git rev-parse --git-dir` != `--git-common-dir` so it
      covers `ship-from-worktree.sh`, quickmerge isolation and any hand-rolled worktree alike. Fails OPEN on every error
      path (malformed payload, unparseable command, missing `pgrep`) — a guard that blocks on its own bug would wedge
      every commit. **Detection was EXTRACTED to `cursor-configs/hooks/lib/slot-collision-detect.sh`** and both hooks
      now share it: the macOS `/proc` gap survived unnoticed in a single copy, and a second copy is exactly how that
      returns fixed-in-one/broken-in-the-other. **Two real defects the gate caught in this work, both mine**: (1) the
      refactor added `dirname`/`grep` — external binaries absent from the curated-PATH degradation test — silently
      killing signal 2 again; caught by the existing 10-test suite, replaced with builtins. (2) The escape hatch was
      written as an `os.environ` read while documented as a `SLOT_COLLISION_GUARD=0 <cmd>` PREFIX; those are
      incompatible, since the hook is a child of the CLI and never sees a command's env prefix — it would have shipped
      an escape hatch that silently did nothing. Now matched in the command string, with a test pinning that the
      environment-only form does NOT pass. Tests: `tests/test_pretooluse_slot_collision_guard.bats` (17; only 6 are
      blocking cases — the rest pin the false-positive surface the operator explicitly paid for), plus the 10 existing
      session-start tests still green.
- [x] ✅ [INFRA] P2. **A liveness check built on `pgrep` substring matching is unsound on this shared host.**
      unified-trading-pm@37d7095041. Audited every standing `pgrep`-based liveness/collision helper in
      `scripts/`/`cursor-configs/` (grep for `pgrep -f`/`pgrep -af`, ~15 files). Most are one-shot lookups or already
      exact-PID-scoped (`_ancestor_pids`/`_cwd_of` in `cursor-configs/hooks/lib/slot-collision-detect.sh`, already fixed
      by the earlier session-collision todo). Found one genuinely unsound LOOP-shaped liveness check gating a
      destructive action: `scripts/dev/slot-cron-ff-pull.sh`'s `_resync_venv_if_lock_moved` decided whether to skip a
      `uv sync --frozen` (which this same issue doc's own P1 lesson says can PRUNE a live environment) via
      `pgrep -af 'pytest|quality-gates|basedpyright' | grep -qF "${PWD}"` — a substring test against the matched
      process's argv TEXT, not its actual cwd. The dangerous direction is a false negative (a live gate invoked via a
      relative path or wrapper, whose argv never literally spells out `${PWD}`, goes undetected and `uv sync` runs
      concurrently with it). Fixed by reusing `_cwd_of` from the already-existing collision-detect library — exact cwd
      match per candidate PID, portable macOS/Linux, with a substring fallback only if the library is missing. The
      originally-cited incident itself (`pgrep -f "quality-gates.sh --no-fix" | head -1`) was an ad-hoc watcher written
      live in a 2026-08-11 session, not standing repo code — nothing to fix there; the SSOT
      (`/codex/12-agent-workflow/async-wait-and-poll-discipline.md` §4) already documents that class. Tests:
      `tests/test_slot_cron_ff_pull_venv_resync_liveness.bats` (6/6) — exact-cwd match triggers the gate, a
      path-prefix-only match (the old bug's false-positive-by-substring shape) does not, no candidates / multiple
      candidates both behave correctly, and the substring pattern is confirmed gone from the primary path. Repo:
      unified-trading-pm. SSOT: `/codex/12-agent-workflow/async-wait-and-poll-discipline.md`.
- [x] ✅ [INFRA] P0. **Stop `safe-doc-push.sh` exiting 5 with the caller's edits silently reverted.** DONE — shipped
      2026-08-10 in unified-trading-pm@e59d4750fa, same unflipped-checkbox gap as the two todos above.
      `_sdp_fingerprint_named()` hashes every named file at entry (`_SDP_ENTRY_FINGERPRINT`);
      `_sdp_warn_if_content_vanished()` re-hashes before the exhausted-retries message and, on a mismatch, prints a loud
      warning naming `git stash list` / `git show 'stash@{0}:<path>'` and the run exits **10** instead of the
      plain-transient **5**. **What was actually missing**: the "Done when"'s own test requirement — a
      `test_tree_wip_guard.bats` comment claimed this was "already covered" but no test anywhere exercised
      `_sdp_fingerprint_named`/`_sdp_warn_if_content_vanished`. Added unified-trading-pm@bdc6c3ab52 — new
      `tests/test_safe_doc_push_entry_hash_reverted_edits.bats` (3/3, sed-extracted harness against a real git repo,
      same pattern as the failure-classification test): unchanged file compares clean, a file reverted to HEAD mid-run
      is caught and names the recovery ref, a file deleted mid-run (ABSENT) is caught too. Repo: unified-trading-pm.
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
- [x] ✅ [INFRA] P1. **prek's patch cache (`~/.cache/prek/patches/`) is host-global, not per-worktree — hardened
      regardless of confirmed root-cause status.** DONE 2026-08-12 — unified-trading-pm@62d1a42613. `quickmerge.sh` and
      `safe-doc-push.sh` now scope `PREK_HOME` per isolated worktree (verified live: a fresh `PREK_HOME` dir gets
      populated independently); the expensive, reusable subdirs (`repos`/`hooks`/`tools`/`cache`, ~20MB+ of installed
      hook environments) are symlinked in from a per-repo shared cache (`~/.cache/qm-iso-prek/<repo>`, mirroring the
      venv-cache pattern) so isolation doesn't reinstall every hook repo per commit; `patches`/`scratch` are left
      unlinked so prek creates them fresh, private to the run. Kept because it's a genuine, verified isolation
      improvement (reduces host-global state sharing) and every repo in the fleet gets it for free via the
      `scripts/quickmerge.sh` symlink architecture — but **retitled and downgraded from P0** because the NEXT todo
      falsifies the theory that this was ever the cause of the originally-reported symptom. Do not cite this as "the
      fix" for a revert — it closes a real, separate risk that was never actually confirmed to have fired.
- [x] ✅ [INFRA] P0. **The PREK_HOME hypothesis does NOT explain the originally-reported reverts — falsified by direct
      test, not just argued away.** Investigated 2026-08-12 (challenged by a peer agent's review, which was correct to
      push back). Built `scripts/dev/repro-prek-cross-worktree-race.sh`: two genuinely separate `git worktree`s, one
      slow hook, racing a file that exists independently at each worktree's own path — the specific mechanism the
      PREK_HOME fix was supposed to close. Ran it BOTH with a shared `PREK_HOME` (the pre-fix shape) and with isolated
      `PREK_HOME` (the fix): **both came back clean, zero cross-worktree corruption, no fix needed to prevent it.** The
      classic prek stash/restore race does not cross worktree boundaries via a shared patches directory, tested directly
      rather than assumed. Went further: built a REAL same-file concurrency test against the actual `safe-doc-push.sh`
      (2 independent clones + a disposable bare origin, not a synthetic repro) — two workers editing the SAME file
      concurrently, both non-overlapping lines (both edits correctly preserved via the existing rebase-retry reconcile)
      and overlapping lines (loud `rebase --abort` + exit 3, "genuine content collision, not contention" — never a
      silent drop). **7 distinct mechanisms tested this session, all clean**: cross-worktree ×2 PREK_HOME modes,
      same-file non-overlapping, same-file overlapping, plus the earlier-session single-shared-tree classic race
      (already covered by `repro-prek-stash-restore-race.sh`). Could not reproduce the originally-reported corruption
      through any constructible mechanism without the original raw `safe-doc-push.sh` output (only a hash-only summary
      survived from the original two occurrences). Strongest remaining lead, not yet confirmed: the affected file
      (`ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`) had an ACTIVE `UU` conflict in this shared checkout at
      investigation time, under heavy legitimate concurrent-peer commit traffic (5+ commits same day, unrelated
      investigation) — a shared-checkout collision against an actively-committing peer is a far more mundane explanation
      than a prek bug, but unconfirmed without the original logs. **Done when**: either the original logs surface and
      pin the mechanism down, or it recurs and the new forensic dump (next todo) captures it live. Repo:
      unified-trading-pm.
- [x] ✅ [INFRA] P1. **Make the next occurrence self-diagnosing instead of leaving a hash-only summary.** DONE
      2026-08-12 — unified-trading-pm@340bae9f60. All three revert-detection call sites in `quickmerge.sh`
      (`_qm_content_vanished`, `_qm_assert_entry_change_landed`) and `safe-doc-push.sh`
      (`_sdp_warn_if_content_vanished`, `_sdp_guard_already_landed_claim`, `_sdp_assert_entry_change_landed`) now write
      a durable, timestamped forensic snapshot the moment a revert is detected — entry fingerprints, entry HEAD blobs,
      current disk fingerprint, current HEAD, last 3 commits touching each named file, full `git status --porcelain`,
      `git stash list`, recent `prek/patches` listing, `git worktree list` — to
      `~/.cache/{sdp,qm}-forensics/revert-<ts>-<pid>.log`. Best-effort, never blocks the caller. Verified: existing
      regression coverage (`tests/test_safe_doc_push_entry_hash_reverted_edits.bats` 10/10,
      `tests/test_quickmerge_landed_content_assertion.bats`) still passes unchanged, and a direct manual invocation of
      the dump function confirmed correct, rich output. Repo: unified-trading-pm.
- [x] ✅ [INFRA] P0. **F9 — isolated mode's copy loop blindly `cp`'d the caller's on-disk file over a freshly-fetched
      origin/$BRANCH worktree with no check for peer divergence, silently clobbering a peer's already-landed content.**
      Found 2026-08-12. FIXED 2026-08-12, unified-trading-pm@f8d1ad47f1. **Root cause, precisely located**: the
      isolated-worktree copy loop (`scripts/dev/safe-doc-push.sh`, the `for _f in "${FILES[@]}"`loop inside the     isolation branch) did`cp
      "$_f" "$_sdp_iso_wt/$_f"` unconditionally for every tracked file — no comparison against
      what the freshly-checked-out worktree already held. If a peer landed different content in that file since the
      caller's last sync, the cp silently replaced it. `_sdp_reconcile_caller_duplicates` (the ORIGINAL suspect, still
      real and still narrower-than-ideal by design) only runs AFTER the push, to sync the caller's OWN copy back — it
      was never the mechanism that caused the loss; the loss happened before that function is ever reached. **Measured
      before the fix**: 4 workers × 6 rounds (24 ship attempts) against one shared file, no re-pull between a worker's
      own rounds — 12 of 18 markers vanished from the final tree despite being individually reported LANDED. Repro:
      `scripts/dev/repro-safe-doc-push-stale-local-clobber.sh` (permanent, re-runnable). **Fix, built**: capture each
      named file's blob at the caller's OWN pre-fetch HEAD (`_SDP_ISO_BASE_BLOBS`, captured before isolation's `git
      fetch`/`worktree add` — the only point where "HEAD" still means the caller's last-synced tip, not origin's fresh
      state). In the copy loop, compare that base blob against `origin/$BRANCH`'s CURRENT blob for the same path     (fetched moments earlier). Equal ⇒ nobody touched the file since the caller's last sync, blind copy stays exactly     as safe as before (the common case, unchanged). Different ⇒ a peer moved the file; abandon isolated mode for THIS     run (`_sdp_copy_ok=false`) and fall through to the existing shared-index fallback path, which reconciles through     git's own ancestor-aware 3-way merge machinery (ff-only / `--rebase
      --autostash`) and hard-stops loudly (exit 3,     "needs a human") on a genuine content conflict — proven, already-tested machinery, not reinvented. This is a     hybrid of the two options originally sketched: it never silently drops content (option b's guarantee) without     needing a hand-rolled merge-conflict detector, by reusing git's real reconcile path instead (simpler and more     robust than option a's proposed direct blob-level `git
      merge-file`). **Verified**: `bash
      -n` + shellcheck clean     (only 2 pre-existing, unrelated warnings elsewhere in the file); full existing bats regression suite (10 files,     39/39) passes unchanged, including all 3 isolated-mode-specific suites (untracked-duplicate, deletion-propagates,     identity-preserved); the repro script run TWICE post-fix: **0/11 confirmed-landed markers missing from the final     tree, both times** (workers whose local copy diverged hit real conflicts via the shared-index fallback and failed     loudly with rc=3, rather than any push silently succeeding while clobbering a peer's content). **quickmerge.sh     checked for the same mechanism and confirmed NOT vulnerable** (its isolated-worktree copy loop has the identical     blind-`cp`shape at line ~1032, but its worktree is created at the caller's local`HEAD`, and — critically —     STAGE 0.4's not-behind gate (`_qm_stage_0_4_not_behind_gate`, called unconditionally at line 1571, which the     isolated child also reaches after re-exec, before any commit) already fetches origin and either fast-forwards     cleanly, blocks loudly on `ahead=0` working-tree overlap (`PRECOMMIT_WORKING_TREE_CONFLICT`, exit 1 — this is the     exact F9-shaped scenario), or blocks loudly on a genuine rebase conflict (`BEHIND_DIVERGED_CONFLICT`/    `AUTOSTASH_POP_CONFLICT`,
      exit 1) — every branch either succeeds cleanly or hard-stops, no silent-proceed path exists. No fix needed there;
      this was a real check, not an assumption. **Done when**: repro script shows 0 missing markers post-fix (met,
      twice) and the sibling ship script is checked for the same class of defect (met — quickmerge.sh confirmed clean by
      trace, not just assumed). Repo: unified-trading-pm.
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
- [x] ✅ [INFRA] P1. **Make `prettier-autostage.sh` format regardless of drift.** DONE — shipped 2026-08-10 in
      unified-trading-pm@aa1f445933 (same session as the three todos above, same unflipped-checkbox gap — this is why it
      kept hitting live on 2026-08-11/12 even though the fix had already landed the day before). Rather than
      unconditionally removing the guard, it now mirrors `check-branch-drift.sh`'s own advisory mode: the "skip while
      behind" branch is itself gated on `DRIFT_GATE_ADVISORY:-0 != 1`, so under a reconciling wrapper (whose commit the
      drift gate will not block) formatting proceeds while behind, and the residue protection stays intact for a bare
      `git commit`. **What was actually missing**: test coverage proving the F3 loop is actually broken. Added
      unified-trading-pm@bdc6c3ab52 — new `tests/test_prettier_autostage_advisory_mode.bats` (2/2): behind+unset still
      skips (residue protection intact), behind+`DRIFT_GATE_ADVISORY=1` does NOT skip and falls through past the drift
      check entirely. Repo: unified-trading-pm.
- [x] ✅ [INFRA] P1. **Re-derive the push-governor's validation cap from measured host cores.** DONE 2026-08-10 —
      `_push_gov_validate_default_k()` now mirrors `qg-host-governor.sh`'s `max(2, floor(cores/4))`; measured 8 -> 2 on
      the 10-core operator host. Original text: `push-host-governor.sh` admits a fixed K=8 validation-phase tokens.
      Profiling 2026-08-10 showed the sweep is ~18.6s of real work inflated ~6x to 118s by concurrent hook chains on one
      laptop — 8 concurrent 19s sweeps produce exactly the observed wall time. Mirror `qg-host-governor.sh`'s
      `max(2, floor(cores/4))` derivation instead of a constant. **Done when**: the cap is core-derived, and a measured
      before/after shows per-run sweep wall time on a loaded host materially closer to its idle 18.6s. Repo:
      unified-trading-pm.
- [x] ✅ [INFRA] P1. **Shrink the 118s critical section itself.** Re-profiled 2026-08-12 (per-check timestamp method,
      same as the original 2026-08-10 profiling) and found the top cost was NOT residual contention or an
      intrinsically-expensive check — it was two SELF-INFLICTED regressions from earlier sessions, both fixed and
      shipped this session: - `check_plan_commit_sha_evidence.py --only`: **57s**, because `main()` verified every
      citation in the WHOLE corpus (not just staged files) even in `--only` mode — always true, but harmless until todo
      5 above added a `require_reachable` reachability check (2 extra git subprocess calls) for every self-citation, of
      which this corpus has hundreds. Fix: `--only` mode now skips verification entirely for citations outside the
      staged paths, since their violation status is filtered out and never reported anyway. `--only` run: 57s → 2.4s.
      Baseline (full-corpus) mode unaffected (unchanged 56.8s, off the precommit path). Tests:
      `scripts/quality_gates/test_check_plan_commit_sha_evidence.py` (+2, 9/9 total) — proves `--only` mode never calls
      the verifier for an unstaged citation, and baseline mode still verifies everything.
      unified-trading-pm@4e8447bd21. - `check_ag_closeout_linkage.py`: **42.7s** (31.1s of it kernel/syscall time),
      because `resolve_related_entry`'s legacy-form fallback ran a fresh `rglob` over the whole corpus PER `related:`
      ENTRY across every doc — with ~750 docs each carrying several entries, hundreds of full recursive directory walks
      per run. Fix: one `rglob("*.md")` walk building a memoized basename index; `resolve_related_entry` does O(1) dict
      lookups against it instead, with identical resolution semantics (verified via A/B diff of full-corpus output,
      byte-identical before/after). Run: 42.7s → 1.95s (`--only`), 2.2s (baseline). Tests:
      `scripts/plan-hygiene/test_check_ag_closeout_linkage.py` (7 new) — both fallback forms, the plans/-only scoping
      the bare-slug form has always had, and that the index is built exactly once per process.
      unified-trading-pm@d85ad41fac.

      **Done when, confirmed**: the precommit sweep on one staged file is now **20.8s** total wall (measured 2026-08-12,
                                  isolated worktree, host otherwise idle) — materially below the 60-80s measured commit inter-arrival rate, and
                                  down from the original 118s (loaded) / 85s (this session's own first re-measurement, itself inflated by a
                                  concurrent quickmerge run — see Progress Log). A follow-up per-check timing pass after both fixes shows no
                                  single check over 4s (`plan-commit-sha-evidence` 4.0s, `check_archive_candidates` 3.0s,
                                  `check_ag_closeout_linkage` 2.0s, `finalize-plan-coverage` 1.0s, everything else sub-second) — well-distributed,
                                  nothing left to move out of the per-commit path. Repo: unified-trading-pm.

- [x] ✅ [INFRA] P2. **Record the AO-vs-PM volume asymmetry in the codex** so the next person does not re-derive it —
      unified-trading-pm@baae1922bb. New § "1b. PM is the fleet's single write hotspot" in
      `/codex/12-agent-workflow/host-concurrency-and-commit-provenance.md` carries F1's measured table (118s loaded vs
      18.6s idle-worktree, 60-80s commit inter-arrival, 1318/59/152 commits-per-24h for PM/AO/MTDS), the dated
      measurement (2026-08-10), and the structural reason (Commit+Push+Flip means every agent in every repo writes to
      PM, so a fixed critical section safe at AO's ~1 commit/24min is unsafe at PM's ~1/60s) — plus which two
      mitigations actually landed against it (`DRIFT_GATE_ADVISORY`, isolated-worktree-by-default), so a reader isn't
      left wondering if the 118s number is still live. Repo: unified-trading-pm.
- [x] ✅ [DOC] P2. **Document the working sequence (reconcile → format → commit) in
      `/codex/05-infrastructure/per-tab-worktrees.md`** — unified-trading-pm@baae1922bb. New subsection "The working
      commit order — reconcile → format → commit" under the existing "Committing from a contended checkout" section:
      states the recipe, walks through why any OTHER order re-forms the F1/F2/F3 closed loop, notes the sanctioned
      scripts don't need it spelled out by hand (they set `DRIFT_GATE_ADVISORY=1` themselves) so this is for a bare
      `git commit` workaround specifically, and cross-references F4's exit-5-vs-exit-10 distinction right next to the
      existing "Exit codes worth recognising" list so an agent seeing "transient, re-run" reads the actual exit code
      before believing it. Repo: unified-trading-pm.

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
- [x] ✅ [INFRA] P2. **Slot 2's PM checkout is wedged and cannot receive any of these fixes.** CLOSED 2026-08-12 —
      re-verified directly
      (`git -C .tabs/2/unified-trading-pm fetch origin live-defi-rollout && git rev-list     HEAD..origin/live-defi-rollout --count`
      → 0; `git status --porcelain` → 0 lines; 0 `UU`/`AA`/`DD` entries). Slot 2 is fully fast-forwarded and clean — not
      the 81-commits/4-conflict-markers/22-dirty-files state this todo was originally filed against, and not even the
      3-behind state the 2026-08-12 STALE note found. The "Done when" (owner resolves the conflict, slot 2
      fast-forwards) has happened; nothing further to do here. Repo: unified-trading-pm.
- [x] ✅ [INFRA] P3. **`check_chain_set_inclusion` has 3 failing tests, pre-existing.** RE-VERIFIED 2026-08-12: all 3
      tests now PASS (`test_invariant_holds_on_live_uac`, `test_returns_violation_when_genesis_orphan`,
      `test_returns_violation_when_gas_fee_chain_id_orphan`), and running the check directly confirms the invariant it
      guards: `MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES ⊇ GAS_FEE_CHAIN_START_DATES`. `test_invariant_holds_on_live_uac`
      reads live `unified-api-contracts` registry data, so this was fixed by unrelated UAC data work landing between the
      2026-08-10 baseline (`c7fe11851a`) and now, not by anything in this session. No code or test change needed —
      triaged and confirmed already fixed. Repo: unified-trading-pm.

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
- [x] ✅ [INFRA] P0. **BLOCKED: a peer's uncommitted UTL edit red-lines every PM quality gate on this host.** CLOSED
      2026-08-12 — the premise is not just gone, it is superseded. Re-verified:
      `git -C unified-trading-library status     --porcelain` is still empty, `behind=0`/`ahead=0` against origin. The
      cited test, `tests/unit/test_capability_verdict_matrix.py::test_fixture_matches_live_engine_registry`, does not
      exist anywhere in the current UTL tree (`grep -rl test_fixture_matches_live_engine_registry .` — zero hits; the
      file itself has no delete history either, so it was never actually committed). `_per_vm_shard_backlog` was
      legitimately relocated out of `_state.py` into its own module by a real, shipped, unrelated commit —
      `77fef206 fix(manifest-writer): stop the real OOM driver in the per-VM shard flush path … Extracted     _per_vm_shard_backlog.py from _state.py (pure code motion) to stay under the file-size cap`
      — and every current import site (`manifest_writer/__init__.py`, `tests/unit/test_per_vm_shard_backlog.py`) already
      points at the new module; that test suite passes 6/6. There was never a "durable guard" to preserve here: the
      failure was tied to a specific peer's WIP against a specific pre-refactor file layout, both of which are gone, and
      the refactor made the old import path meaningless rather than merely fixing a revert. Nothing is blocked. Repo:
      unified-trading-pm.
- [x] ✅ [INFRA] P1. **One dead evidence citation red-lines the whole repo's promote flow.** `4f901b9916` (written by
      slot-12 at 16:50, a SHA that never existed here — the pre-rebase id of its own commit) failed
      `check_plan_commit_sha_evidence` corpus-wide, failing PM's gate, failing the promote PR — the "QG slice(s) FAILED
      | unified-trading-pm" → "PROMOTION LAG cause unknown" pair repeating hourly all day. Repaired to `72adcb234c`.
      Re-confirmed 2026-08-12: corpus is clean (0 unresolvable citations, 2887 checked) — the specific incident stays
      resolved. **The structural "Done when" is now DONE too** — unified-trading-pm@b7ba752839.
      `check_plan_commit_sha_evidence.py`'s existence-only test (`git cat-file -t <sha>`) is exactly why this slipped
      past precommit: it passes for ANY loose object, including a commit a rebase already rewrote away, which is
      precisely the shape both `4f901b9916` and the sibling `0f9b8a65ca` incident took (see
      `plans/active/issues/plan_commit_sha_evidence_unresolvable_0f9b8a65ca_2026_08_10.md`).
      `reconcile-sha-citations.sh` already explains why the precommit check itself cannot validate a SELF-citation to
      the very commit being created (it doesn't exist yet) — so the fix scopes a STRICTER test to self-citations only:
      `<repo>@<sha>` where `<repo>` is this repo's own name must now be an ancestor of some `origin/*` ref or of local
      `HEAD` (`_is_reachable_from_any_branch`), not merely a present object. A cross-repo citation keeps the weaker test
      (PM does not control when a sibling repo pushes). This directly rejects a guessed/pre-rebase self-citation AT
      COMMIT TIME instead of letting it land and fail corpus-wide hours later; re-ran the full corpus after the change
      and confirmed 0 regressions (2887 citations, 0 unresolvable — the change is additive-only for self-citations that
      are genuinely unreachable). Tests: `scripts/quality_gates/test_check_plan_commit_sha_evidence.py` (7/7) — pushed,
      local-only-unpushed, and dangling-orphan cases, both with and without `require_reachable`. `ruff`/`basedpyright`
      clean. Repo: unified-trading-pm.
- [ ] [INFRA] P2. **60 of 229 PM bats tests fail and NOTHING gates them.** Measured full run: 169 ok / 60 not ok. PM's
      gate (`base-service.sh`) carries bats as warn-only for service repos; PM's own 30 bats files are not invoked by
      its gate at all. None of the 60 are from this session's five new files. **Done when**: PM's bats suite is either
      gated or its failures are ratcheted.

## Deferred work after 2026-08-12

| Item                                                                                            | State / why deferred                                                                                                                                                                                                                                                                                                                                                           | Blocked on                                                                      |
| ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| F9 — fix isolated mode's blind-copy clobber                                                     | **Done 2026-08-12** — real root cause pinpointed (the copy loop, not `_sdp_reconcile_caller_duplicates`), fixed, verified twice against the repro (0/11 missing both runs), full regression suite green, sibling script (quickmerge.sh) checked and confirmed not vulnerable by the same mechanism.                                                                            | n/a — closed                                                                    |
| Confirm F9 is (or isn't) the ORIGINAL reported mechanism                                        | **Cannot be done yet** — the original report's raw `safe-doc-push.sh` logs no longer exist; only a hash-only summary survived. The new forensic-dump tooling makes the NEXT occurrence self-diagnosing, but there is nothing to check now. Moot either way now: the vulnerability F9 identified is fixed regardless of whether it was the ORIGINAL incident's exact mechanism. | a recurrence, captured live via the new forensics dump (informational only now) |
| Root-cause the isolated-worktree basedpyright false-positive (separate, already-closed finding) | **Closed as accepted-with-workaround**, not reopened — listed here only so a reader doesn't conflate it with F9; different investigation, different doc (archived).                                                                                                                                                                                                            | n/a — intentionally not being pursued                                           |

**Recommended next item**: none open with no external blocker — every actionable item in this doc is closed. The one
remaining row (confirming F9 against the original report) is blocked on a recurrence that may never come, and is no
longer load-bearing since the fix stands on its own measured evidence.

## Deferred work after 2026-08-10

| Item                                                              | State / why deferred                                                                                                                                                                                                                                            | Blocked on               |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| ~~Cross-repo citation reconciliation~~                            | **DONE 2026-08-10** — unified-trading-pm@7f9bd2a366; reachability + patch-id, neither design option needed                                                                                                                                                      | —                        |
| ~~`fix_prosewrap_padding.py` line-scoping~~                       | **CORRECTED 2026-08-12 (/plan-reconcile): DONE** — unified-trading-pm@a29967623a; fixer now takes the check's flagged line set, leaves everything else alone (byte-identical repair on pre-existing corruption vs whole-file mode, per the Todos section above) | —                        |
| quickmerge isolation back to laptop-default                       | **Not done** — proven on one repo/host only; wants a second repo + cache-invalidation check                                                                                                                                                                     | nobody; pick it up       |
| Slot 2 unwedge                                                    | **Operator-owned** — live conflict in another session's WIP, must not be resolved by a third party                                                                                                                                                              | that WIP's owner         |
| `check_chain_set_inclusion` 3 failures                            | **Not done** — pre-existing, unrelated to this work                                                                                                                                                                                                             | nobody; low priority     |
| PM CI green (ldr-docs-gate, na_corpus ratchet promotion deadlock) | **Cannot be done yet** — separate CI/promotion defects already being worked by a peer (two issue docs in slot 2's WIP)                                                                                                                                          | that peer's work landing |

| Item                                                                    | State / why deferred                                                                                                                                                                                                                                                | Blocked on         |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| UTL `_per_vm_shard_backlog` foreign WIP                                 | **Operator-owned** — uncommitted edit in a sibling clone; reverting it destroys another agent's work                                                                                                                                                                | that WIP's owner   |
| ~~Commit-time citation-resolves-against-origin gate~~                   | **CORRECTED 2026-08-12 (/plan-reconcile): DONE** — unified-trading-pm@b7ba752839; `check_plan_commit_sha_evidence.py` now requires a self-citation `<repo>@<sha>` to be reachable from `origin/*`/local `HEAD`, not merely a present loose object (see Todos above) | —                  |
| PM bats: 60/229 failing, ungated                                        | **Not done** — pre-existing, none from this session                                                                                                                                                                                                                 | nobody; pick it up |
| Release-tag stall (7 repos), UTL prod trigger, glue runner 228 restarts | **Not done** — untouched CI groups from the alert audit                                                                                                                                                                                                             | nobody; pick it up |

> **CORRECTED formatting 2026-08-12 (/plan-reconcile)**: this table's rows were previously merged into unwrapped run-on
> paragraph text (a prosewrap-style line-wrap corruption — ironic given this doc's own subject matter) and have been
> restored to proper Markdown table rows above, content unchanged apart from the 2 DONE corrections noted.

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
- **2026-08-12 (re-triage: four P0/P1 todos were already shipped code-wise, just never flipped)**: working this doc's
  remaining open todos in order, found that todos 1-4 (drift-gate-advisory, F2 misclassification, exit-5 silent revert,
  prettier-autostage mirroring) were ALL already implemented — in unified-trading-pm@e59d4750fa and @aa1f445933, both
  landed 2026-08-10, the same day this doc was filed — but the checkboxes were left unchecked. That is why F3's
  "skipping format while behind origin" message kept firing live on 2026-08-11/12 even though the mirror fix predates
  both incidents: the fix was live, the _symptom quoted in the dispatch_ was a stale citation, not a live gap. What was
  genuinely missing in every case was the test coverage each todo's own "Done when" required — verified by grepping
  `tests/` for every mechanism name (`DRIFT_GATE_ADVISORY`, `files were modified by this hook`,
  `_SDP_ENTRY_FINGERPRINT`, a prettier-autostage test file) and finding zero hits before this session. Added four bats
  files/additions (19 new test cases total) exercising each mechanism directly against real git repos, all green. One
  test written for the F2 case initially asserted the WRONG expected behavior (that a mixed autofix+content-rejection
  failure should be DETERMINISTIC) — running it against the real code showed it is RETRIABLE by design, per the
  function's own comment; corrected the test rather than the code, and documented why so the deliberate
  one-extra-attempt tradeoff is not later "fixed" into a false hard-stop.

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

- **2026-08-12 (todos 5 and 6 closed)**: `check_plan_commit_sha_evidence.py` now requires self-citations to be reachable
  from a branch, not merely present as an object — closes the structural "Done when" for the dead-citation todo
  (unified-trading-pm@b7ba752839, 7/7 new tests). Hit the same self-citation chicken-and-egg problem while authoring
  this: quickmerge's precommit gate hard-blocks a literal `<repo>@PENDING` token, so citing the very commit being
  created has to be a two-step ship (land the code first, then flip the checkbox with the real landed SHA) — the earlier
  todos 1-4 doc flip worked around this the same way. Also hit a live instance of this doc's own F4/loss-guard subject
  while shipping todo 5: quickmerge's reconcile reported this file's uncommitted edit as "GONE (content changed during
  the reconcile)" mid-run — the edit was NOT actually lost (verified present and intact immediately after, 22 checked +
  8 unchecked todos, no truncation), so the warning fired on a transient mid-reconcile state rather than a real loss
  this time; recorded here rather than silently ignored, since a false-positive "GONE" warning is itself worth a future
  look if it recurs. Todo 6: re-verified both stale BLOCKED items live — the UTL `_per_vm_shard_backlog` import is not
  just unblocked (`git status --porcelain` empty) but the whole premise is superseded: the symbol was legitimately
  relocated to its own module by commit `77fef206` (a real, shipped, unrelated refactor), the cited test file no longer
  exists anywhere in the tree, and the replacement test suite passes 6/6. Slot 2 is now 0 commits behind origin with 0
  dirty files (previously 81-behind/4-conflict-markers, then 3-behind per the 2026-08-12 STALE note) — fully
  fast-forwarded. Both closed as resolved, not re-scoped: neither retained a "durable guard" purpose once checked, since
  each was tied to a specific incident/file-layout that a legitimate later commit or the WIP's owner had already
  superseded.

- **2026-08-12 (todo B closed — the "118s" cost was two self-inflicted regressions, not intrinsic)**: re-profiled the
  precommit sweep expecting to find corpus-wide checks to relocate out of the per-commit path (the todo's own framing).
  Instead found the dominant costs were regressions THIS SESSION and an earlier one introduced:
  `check_plan_commit_sha_evidence.py --only` (57s — todo 5's `require_reachable` reachability check running against
  every self-citation in the whole corpus, not just staged files) and `check_ag_closeout_linkage.py` (42.7s, 31.1s
  kernel time — a fresh corpus-wide `rglob` per legacy-form `related:` entry, pre-existing, unrelated to this session).
  First lesson: a "shrink the critical section" todo should re-measure before assuming the original 2026-08-10 breakdown
  (Operator-ruling evidence/depends_on-DAG/Terminal-status/Line-caps) still holds two days and several fixes later — it
  did not. Second: my OWN fix for todo 5 introduced exactly the kind of regression this todo exists to catch, caught
  only because I profiled again rather than trusting the "Done when" was satisfied by shipping the reachability check
  alone. Per-check timing before fix: `plan-commit-sha-evidence` 57.0s, `check_ag_closeout_linkage` 26.0s (first pass,
  host also running a concurrent quickmerge — see below), `check_archive_candidates` 5.0s, `finalize-plan-coverage`
  1.0s. After both fixes, on an otherwise-idle host: total precommit sweep **20.8s** (down from 118s original / 85s this
  session's own noisy first re-measurement), no single check over 4s. Also caught mid-session: my FIRST re-measurement
  attempt (85s, then later a noisy 146s) was inflated by a background quickmerge I had running concurrently in the SAME
  worktree while trying to measure an "idle" baseline — exactly the "8 concurrent hook chains inflate 19s to 118s"
  contention mechanism F1 already describes, self-inflicted by not waiting for my own background ship to finish before
  profiling. Fixes: unified-trading-pm@4e8447bd21 (SHA-evidence), unified-trading-pm@d85ad41fac (AG-closeout linkage).

- **2026-08-12 (F9 found — the real mechanism, or at least a real one, after 3 sessions of clean negatives)**: a peer
  agent's review correctly challenged the PREK_HOME fix as unverified against the actual reported symptom (see the
  earlier-shipped correction to that todo). Built and ran a genuine stress test — 4 independent clones, 6 rounds each,
  all shipping to the SAME shared file via the real `safe-doc-push.sh`, no re-pull between a worker's own rounds — and
  it reproduced real, repeated data loss (12/18 confirmed-landed markers missing from the final tree) on a clean,
  uninterrupted run. Traced to `_sdp_reconcile_caller_duplicates` only refreshing a caller's local copy against
  reformatting-equivalent content, never genuinely different peer content — full mechanism and fix direction in the new
  F9 todo above. Nearly mis-attributed this to a git-rebase bug before catching that the loop's own zsh execution
  environment (not bash — `mapfile` doesn't exist, and bare `$var:literal` triggers zsh's history-modifier parsing and
  silently mangles the string) had corrupted an earlier diagnostic trace, producing "0 lines everywhere" garbage that
  briefly looked like a much stranger finding than it was. Promoted the stress harness as
  `scripts/dev/repro-safe-doc-push-stale-local-clobber.sh`. Explicitly NOT claiming this is confirmed to be the original
  reported mechanism — the raw logs from that report no longer exist — but it is the first REAL, reproducible data-loss
  mechanism found in 3 sessions of testing, and the fix is not yet built.

- **2026-08-12 (F9 fixed, and the earlier root-cause attribution corrected)**: the earlier entry above named
  `_sdp_reconcile_caller_duplicates` as the mechanism; that was wrong in a specific, useful way — that function only
  runs AFTER a successful push, to sync the CALLER's own copy back, and could not have caused the measured loss on its
  own. Re-reading the isolation copy loop line by line found the actual defect one step earlier:
  `cp "$_f" "$_sdp_iso_wt/$_f"` ran unconditionally, with no comparison against what the just-fetched worktree already
  held for that path — so a peer's freshly-landed content sitting right there in the worktree got silently overwritten
  the moment the caller's stale local copy was cp'd on top of it, before `_sdp_reconcile_caller_duplicates` ever runs.
  Fixed by capturing the caller's true pre-fetch base blob per file (the one point where "HEAD" still means the caller's
  own last sync, before isolation's own fetch/worktree-add), comparing it against origin's current blob right before the
  copy, and — on any mismatch — abandoning isolated mode for that run and falling through to the existing shared-index
  path, which reconciles through git's own ancestor-aware merge machinery and hard-stops loudly on a real conflict
  instead of guessing. Verified: full bats suite (39/39, unchanged), and the stress-test repro run twice post-fix — 0/11
  confirmed-landed markers missing both times (down from 12/18 missing pre-fix), with the divergent workers now failing
  loudly (rc=3) instead of any push silently clobbering a peer. Per the standing "roll it out everywhere, not just one
  place" instruction from earlier this session: traced quickmerge.sh's isolated mode for the identical blind-`cp` shape
  (found at line ~1032) and confirmed — by reading STAGE 0.4's not-behind gate, not by assuming — that it is NOT
  vulnerable: that gate runs unconditionally before any commit, even in the isolated child, and every one of its
  branches (fast-forward, `ahead=0` working-tree-overlap block, or genuine rebase-conflict block) either succeeds
  cleanly or hard-stops with `exit 1` — no silent-proceed path exists there. No fix needed in quickmerge.sh; this was
  checked, not skipped. Full detail in the F9 todo above.
