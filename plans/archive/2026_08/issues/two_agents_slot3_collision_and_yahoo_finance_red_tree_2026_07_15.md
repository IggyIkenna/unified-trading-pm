---
doc_type: issue
title: Slot-3 two-agents-in-one-worktree collision + YAHOO_FINANCE fleet-blocking red IS tree
summary:
  A concurrent YAHOO_FINANCE phantom-venue-removal agent is actively writing into the SAME slot-3 worktree as the CeFi
  completion program's /autonomous session (live 0-min mtime on UAC files). It swept up a sibling agent's uncommitted
  UAC edit into uac@fec3f110, and its YAHOO_FINANCE removal broke instruments-service QG (test_silent_absent_fixes.py
  fixture + stale tradfi golden) — fleet-blocking for all IS commits. Operator-visibility issue — needs one slot-3
  session halted or explicit file ownership; the red IS tree needs the fec3f110 fallout fixed.
status: resolved
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-api-contracts, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [multi-agent-safety, collision, red-tree, yahoo-finance, incident]
related:
  [
    /plans/archive/2026_07/cefi_completion_program_2026_07_15.md,
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
created: 2026-07-15
author: unknown
last_updated: 2026-07-15
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: CeFi completion program /autonomous session (slot-3, 2026-07-15T14:36Z) + this session's 2026-07-16 recurrence
resolved_by: cicd-agt-9bdc09-2026-08-08
context_scope:
  [
    scripts/quickmerge.sh,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/2026_07/cefi_completion_program_2026_07_15.md,
  ]
---

# Slot-3 collision + YAHOO_FINANCE fleet-blocking red IS tree

> **Filed by**: the CeFi completion program `/autonomous` session (slot-3), 2026-07-15T14:36Z, per the big-finding
> escalation rule (multi-agent-safety + fleet-blocking cross-repo). Surfaced by sub-agent adb3a7cb which HARD-STOPPED
> rather than write into a live-contended worktree.

## The incident (facts)

1. **Two agents in one slot-3 worktree.** A "YAHOO_FINANCE phantom-venue removal" task is running in the SAME slot-3
   worktree as this CeFi `/autonomous` session. Evidence: `unified-trading-pm@f6fc0eda4` (its plan-flip),
   `unified-api-contracts@fec3f110` (its removal commit), and — decisively — UAC files
   `registry/market_data_categories.py`, `registry/expected_coverage.py`, `tests/unit/test_data_status_registries.py`
   show **0-min mtime** (actively being written) at 14:36Z. Violates "each slot = ONE agent".
2. **It swept a sibling's uncommitted work.** `fec3f110` folded in the CeFi UAC agent's bare-OKX liquidations restore
   (content-correct, but under a YAHOO_FINANCE commit message).
3. **It left the IS tree RED (fleet-blocking).** Removing YAHOO_FINANCE from UAC broke instruments-service QG:
   - `tests/unit/test_silent_absent_fixes.py::test_sole_no_adapter_yet_venue_returns_zero_counts_cleanly` uses
     YAHOO_FINANCE as its NO_ADAPTER_YET fixture → now `RuntimeError` (venue no longer resolves).
   - the IS `expected_universe` **tradfi** golden is stale (−13 YAHOO_FINANCE tuples).
   - IS QG = `1 failed, 4461 passed` → blocks ALL IS commits until fixed.

## What this BLOCKS in the CeFi program

- The E-companion (`build_expected` itype-aware + cefi golden, done + verified +6/−0) cannot ship until IS is green.
- Any WS-H IS-side apply (catalogue rebuild, re-census) should wait until the worktree is single-owner + green.

## Required actions (operator or whoever owns the YAHOO_FINANCE task)

1. **Halt one of the two slot-3 sessions** (or assign explicit non-overlapping file ownership). Continuing to co-write
   this worktree keeps corrupting work.
2. **Fix the fec3f110 IS fallout** (the YAHOO_FINANCE task's own cross-repo debt): regen the IS `expected_universe`
   tradfi golden (`scripts/regenerate_expected_universe_golden.py`) + fix `test_silent_absent_fixes.py` (substitute a
   still-declared NO_ADAPTER_YET venue such as `FX`, or retire the test). This unblocks the fleet.

## CeFi-program handling (autonomous, non-blocking)

- PROTECTING the live WIP: not touching the contested UAC/IS files while mtime is fresh.
- E core is landed + correct (uac@494fd90c, is@92f3ca22). E-companion held, ready to ship the moment IS is single-owner
  - green. WS-I is effectively already satisfied at runtime (see the CeFi plan's Progress Log tick 6).
- The `/autonomous` loop will re-check worktree liveness each tick and reconcile (fix the red tree + ship the
  E-companion with `--files`-scoped commits) once the concurrent agent goes idle (mtime stale > ~5 min) — unless the
  operator resolves it first.

## 2026-07-16 recurrence — deployment-ui, same root cause, a second concrete mechanism

**This file itself sat uncommitted/unpushed in the slot-3 worktree for over a day** (created 2026-07-15, never committed
until this update) — the P0 finding was invisible to any other session/slot until this continuation session happened to
notice it while checking for untracked files. Committing it now for that reason alone.

**The incident:** a second, independent Claude session (Opus 4.8, same slot-3/host identity, working the SAME
`data_status_page_ux_and_canonicalisation_2026_07_16` plan concurrently — apparently a still-running continuation of the
"prior agent" that shipped the plan's original P1/P4-A/P5/P7/P8/P2-backend batch) was actively building a
`FixturesBrowser` feature in `deployment-ui` (new component + uncommitted edits to `client.ts`/`mock-api.ts`/
`DataStatusTab.tsx`) at the same time a sub-agent dispatched by this session shipped the plan's P8 UI-P2 unit in the
same working tree. Sequence:

1. The dispatched sub-agent used `git add -p` to isolate its own hunks before its FIRST commit (Unit 1, P2 lifecycle
   cards) — clean.
2. For its SECOND commit (Unit 2, P8 UI-P2), it ran `quickmerge.sh ... --agent --files 'DataStatusTab.tsx ...'`.
   **`quickmerge`'s `--files` flag stages the NAMED FILES WHOLESALE (a plain `git add <path>`), not a partial-hunk
   stage** — so it silently swept the OTHER agent's unstaged `FixturesBrowser` import + mount + an unrelated wording
   tweak into commit `deployment-ui@b0525e5`. Because `FixturesBrowser.tsx` itself was never committed (still
   untracked), `live-defi-rollout` briefly carried a dangling import — a broken build on the shared integration branch.
3. The sub-agent caught this itself via a post-push `git ls-tree`/grep check, reverted the foreign hunks with a
   forward-fix commit (`deployment-ui@12c94be`), re-verified `tsc`/`eslint`/full `quality-gates.sh` green, and confirmed
   the other agent's actual WIP files were left intact and untouched in the working tree (verified again by the
   orchestrating session: `tsc --noEmit` clean on HEAD, `git grep FixturesBrowser` returns zero tracked hits, the two
   `FixturesBrowser.*` files are still present as untracked WIP).

**New mechanism, same root cause as the July 15 incident**: last time the collision vector was a full task
(YAHOO_FINANCE removal) editing shared files while a sibling agent's UAC edit was live; this time it's specifically
**`quickmerge --files` doing whole-file staging** — meaning ANY agent shipping a hot shared file (here,
`DataStatusTab.tsx`, which multiple plan points across this session all touch) while another agent has uncommitted,
unstaged changes to that SAME file will silently sweep them in, regardless of whether the two changes are otherwise
unrelated. `git add -p` (hunk-level) avoids it; `quickmerge --files` (whole-file) does not.

**Recommendation for the operator:** the July 15 doc's ask (`each slot = ONE agent`, or explicit non-overlapping file
ownership) still stands and is not something either concurrent session can enforce on its own — only spawning fewer
overlapping sessions per slot, or partitioning file ownership up front, actually closes this. As a lower-lift
mitigation, `quickmerge.sh`'s `--files` staging could hunk-scope via `git add -p`/`git diff <path> | git apply --cached`
restricted to the sub-agent's own edit regions instead of a whole-file `git add`, which would make this specific
mechanism (as opposed to the general two-agents-one-worktree problem) non-recurring. Not attempting that change myself —
it's a shared-tooling change outside this plan's scope and risks its own regressions under contention.

## 2026-07-17 — third recurrence, AND the stash/patch-protect mitigation itself has a gap

A sub-agent (P6 UI, same plan) hit the identical `quickmerge --files` whole-file sweep AGAIN on `client.ts` while
shipping the Catalogue Explorer piece — despite being explicitly briefed on the July-16 incident and instructed to use
the reverse-patch/stash-protect procedure that worked cleanly for the P3 UI unit. It caught its own mistake (diffed the
committed blob against expectation) and shipped a revert commit (`deployment-ui@57d913d`) — but **the revert only
removed the foreign hunk from the COMMIT, it did not restore the hunk to the WORKING TREE**, leaving the other agent's
own untracked `FixturesBrowser.tsx`/`.test.tsx` files referencing exports (`FixtureRow`, `FixturesByLeagueAndDay`,
`fetchFixturesBrowse`) that no longer existed anywhere — a genuine `tsc --noEmit` build break in the ambient working
tree, discovered by the orchestrating session doing a routine post-ship health check (not by the shipping agent itself,
which had already moved on and reported done).

**The gap this exposes**: "revert the accidental sweep" and "restore the other agent's WIP to the state it was in before
you touched it" are two DIFFERENT operations, and doing only the first leaves the working tree in a WORSE state than
before the collision (previously: two agents' uncommitted work coexisting fine; after a same-file whole-file sweep +
partial revert: the foreign agent's own files no longer compile, silently, until someone happens to run `tsc` against
the ambient tree). Fixed by the orchestrating session: manually re-extracted the exact removed hunk from the revert
commit's diff and re-inserted it as uncommitted content (not staged, not committed) at the same two locations in
`client.ts`/`mock-api.ts`, verified `tsc --noEmit` clean again.

**Sharper recommendation**: any agent that reverts an accidental foreign-hunk sweep MUST verify the OTHER agent's own
untracked/uncommitted files still typecheck against the reverted tree before considering the incident closed — a revert
is not complete until the counterpart's files build again, not just until your own commit looks clean.

## Todos

- [x] ✅ [INFRA] P2. **Hunk-scope `quickmerge.sh --files` staging** — switch `--files` from a whole-file `git add` to
      hunk-level staging (`git add -p` / a restricted `git diff <path> | git apply --cached`) so shipping a hot shared
      file no longer silently sweeps a concurrent agent's uncommitted WIP into the commit; not attempted in this doc
      ("outside this plan's scope and risks its own regressions under contention"). — **RULED 2026-08-06 (operator,
      interactive): DO NOT hunk-scope. Closed as decided-against, not as done.** (See also
      /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md, the doc that
      attacks the underlying collision rate instead.) Whole-file staging stays. Reasoning recorded so this is not
      re-proposed every time the foreign-WIP-sweep class recurs: hunk-level staging in the fleet's single most critical
      shipping path trades a **visible** failure for an **invisible** one. Sweeping in an extra file produces a commit
      that is wrong but obvious — it shows up in `git show --stat` and in review. A mis-applied hunk produces a commit
      that is silently **PARTIAL**: it compiles, it reviews clean, and it breaks `git bisect` because the tree at that
      commit never existed as anyone's working state. That is a strictly worse failure mode, and it lands in the path
      every repo ships through. **The class is being addressed where it actually belongs**: (a)
      `scripts/dev/safe-doc-push.sh`'s defensive unstage-by-name already isolates foreign staged content on the doc path
      (mandated fleet-wide 2026-08-06, `unified-trading-pm@73bfdbeda`), and (b) the `.agent-claim` liveness heartbeat +
      session-start collision warning tracked in
      `/plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md` attack the
      **collision rate** rather than the staging granularity. Reduce how often two agents share a checkout; do not make
      the commit itself lossy. **If this is ever revisited**, the bar is a mechanism that cannot produce a partial
      commit — not a more careful hunk selector.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the one open `[INFRA] P2` changes `quickmerge.sh --files`
  staging semantics, i.e. the fleet-wide SSOT shipping tool that every repo symlinks. The doc itself declines it as
  'outside this plan's scope and risks its own regressions under contention', and frames the primary ask as an operator
  policy call ('each slot = ONE agent, or explicit non-overlapping file ownership … not something either concurrent
  session can enforce on its own'). Same too-high-blast-radius class as
  `utl_shared_clone_commits_repeatedly_reset_2026_07_22.md` item 5, which batch1 already deferred for needing 'its own
  scoped plan with operator sign-off'.
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — marker was stale (claimed 2, held 5, missing
  epic-vs-source balance); dropped the generic `cefi_master` epic pointer, kept the named `quickmerge.sh` source file.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-08 (ao round-5 operator Q&A apply session, item 15)**: operator ruled "Build a collision-warning mechanism
  (detect + warn when 2 sessions share a slot, not a hard block)." Closed the `[OPERATOR]` follow-up todo; applied the
  decision to `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`'s already-designed
  candidate fixes 1+2 (unblocked, ready for dispatch there).

## Follow-ups

- [x] ✅ [OPERATOR] P2. **DECIDED 2026-08-08 (operator ruling, ao round-5 apply item 15 — see
      /plans/active/issues/ao_round5_apply_session_operator_qa_index_2026_08_08.md): "Build a collision-warning
      mechanism (detect + warn when 2 sessions share a slot, not a hard block)."** Not a hard each-slot-ONE-agent
      enforcement policy -- a detect-and-warn mechanism instead. Applied to the sibling doc that already carries the
      concrete mechanism design (candidate fixes 1+2):
      `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md` -- both its `[SCRIPT]` todos (live
      `.agent-claim` heartbeat + session-start collision warning) are now unblocked (warn, not refuse) and ready for
      dispatch. No further action needed on this doc itself.

> **2026-08-06 archive-candidate audit**: The sole hunk-scope todo was RULED decided-against 2026-08-06, but the
> na-eligibility-audit 2026-08-06 marker explicitly says 'Operator-gated, design-judgment, or standing-corpus-ruling
> work remains open' and the doc's core ask (each-slot-ONE-agent / explicit file ownership) is an unresolved operator
> policy call the doc itself declines to close, with the collision-class mitigation still tracked in a separate live
> issue doc — genuinely ambiguous, so kept open. [KEEP_OPEN todo synthesized from justification by archive sweep]

- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — re-verified; sole open item
  (`[OPERATOR] P2`, each-slot-ONE-agent / file-ownership policy) remains an unresolved operator policy decision the doc
  itself declines to make. Unchanged since the 2026-08-06 marker.
- **2026-08-08 (cicd escalation agt-9bdc09, archive-candidates ratchet cleanup)**: the `[OPERATOR] P2` item was resolved
  the same day (ao round-5 apply session item 15 — see the Follow-ups section above) and no other doc claims
  reconciliation ownership of this one. All todos are `[x]`, no `locked_by` — archiving now per the 6-step ritual
  (`status: resolved`, `git mv` to `plans/archive/2026_08/issues/`, referrer paths fixed corpus-wide).
