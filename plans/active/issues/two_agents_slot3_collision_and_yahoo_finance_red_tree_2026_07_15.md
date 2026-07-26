---
doc_type: issue
title: Slot-3 two-agents-in-one-worktree collision + YAHOO_FINANCE fleet-blocking red IS tree
summary:
  A concurrent YAHOO_FINANCE phantom-venue-removal agent is actively writing into the SAME slot-3 worktree as the CeFi
  completion program's /autonomous session (live 0-min mtime on UAC files). It swept up a sibling agent's uncommitted
  UAC edit into uac@fec3f110, and its YAHOO_FINANCE removal broke instruments-service QG (test_silent_absent_fixes.py
  fixture + stale tradfi golden) — fleet-blocking for all IS commits. Operator-visibility issue — needs one slot-3
  session halted or explicit file ownership; the red IS tree needs the fec3f110 fallout fixed.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [multi-agent-safety, collision, red-tree, yahoo-finance, incident]
related: [/plans/archive/2026_07/cefi_completion_program_2026_07_15.md]
created: 2026-07-15
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
resolved_by:
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
