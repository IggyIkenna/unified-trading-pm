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

- [ ] [INFRA] P1. **Cross-repo evidence citations still go stale on rebase.** `scripts/dev/reconcile-sha-citations.sh`
      heals a citation to a commit THIS push is rebasing, using ORIG_HEAD + preserved subjects. It cannot heal a PM plan
      citing `agent-orchestrator@<sha>` that AO's own push rebased — PM has no visibility of that rewrite. Options: a
      durable old→new map published per repo, or a reconciler that matches by patch-id across repos. **Done when**: a
      cross-repo citation invalidated by the other repo's rebase is auto-corrected, with a regression test. Repo:
      unified-trading-pm.
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

## Deferred work after 2026-08-10

| Item                                                              | State / why deferred                                                                                                   | Blocked on               |
| ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| Cross-repo citation reconciliation                                | **Not done** — needs a design call between a published old→new map vs patch-id matching                                | nobody; pick it up       |
| quickmerge isolation back to laptop-default                       | **Not done** — proven on one repo/host only; wants a second repo + cache-invalidation check                            | nobody; pick it up       |
| Slot 2 unwedge                                                    | **Operator-owned** — live conflict in another session's WIP, must not be resolved by a third party                     | that WIP's owner         |
| `check_chain_set_inclusion` 3 failures                            | **Not done** — pre-existing, unrelated to this work                                                                    | nobody; low priority     |
| PM CI green (ldr-docs-gate, na_corpus ratchet promotion deadlock) | **Cannot be done yet** — separate CI/promotion defects already being worked by a peer (two issue docs in slot 2's WIP) | that peer's work landing |

**Recommended next item**: cross-repo citation reconciliation. It is the only one that silently produces FALSE failures
on genuine work — the others are either visible, owned, or pre-existing.

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
