---
doc_type: issue
title:
  A verified-done plan/issue doc archived via `git mv` was later found back at its original active path with pre-archive
  content — the archival action was silently undone by later concurrent fleet activity, with no trace of the archiving
  commit surviving in that path's git log.
summary: >
  Found 2026-08-09 during the plan_reconciler sports-tranche run (`agt-8da8df`, slot 14) while re-verifying
  `sports_index_recency_masked_captured_atoms_2026_07_13.md` as a fully-done archive candidate (all 7 todos done,
  unlocked). `unified-trading-pm@f44dfadd4` (2026-08-08T01:02:55Z, slot-11, dispatch `agt-2add8d`) had ALREADY archived
  this exact doc — same evidence basis (all 7 todos done, the doc's own 2026-08-05 Progress Log already said "closes the
  last open todo") — via a clean `git mv` to `plans/archive/2026_08/`, and additionally repointed 5 real path-format
  referrers to the new location. By 2026-08-09, the doc was back at
  `plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md` with PRE-archive content (`status:
  open`), and `git log -- <that active path>` shows NO trace of `f44dfadd4` or its immediately preceding commit
  `ad137ae4e` (a `locked_by: ""` normalization on the same doc) — the path's history jumps directly from `1c4896fb87`
  (2026-07-30) to a run of later commits (context-scope backfills, an unrelated archival, a 2026-08-05 todo flip) that
  are NOT descended from the archive-era commits at all. The archive-side copy
  (`plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md`) does not exist in the current tree
  either — so this is not a duplicate-copy ("create-only archive commit") bug, it is a full, clean reversion of the
  entire archival action, both sides.

  A SIBLING doc archived by the exact same commit, `dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md`
  (not sports-tranche — DeFi/dex-pool related), shows the identical pattern: currently sitting back at
  `plans/active/issues/dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md`. Two-for-two on the one commit
  checked is enough to treat this as a real, repeatable failure mode rather than a one-off fluke, though the sample is
  still small (only this one archival commit has been checked).

  Nothing appears destroyed — the active-path copies carry full, coherent content (this is not the content-clobber shape
  of `quickmerge_concurrent_same_file_edit_blind_overwrite_2026_08_08.md`; both files read as complete, valid docs with
  all their historical Progress Log entries intact) — but a deliberate housekeeping action (archival) was silently
  undone, is invisible to the corpus's own `check_terminal_status_archived` / `check_create_only_archive_commits`
  mechanical gates (neither currently flags either doc, since post-reversion each looks like an ordinary never-archived
  active doc with `status: open`, no archive-side duplicate exists to trip the create-only check), and the archiving
  agent's own commit message and evidence trail (visible via `git log <sha>` with no path filter) is the only surviving
  record that the archival ever happened.

  Root cause NOT diagnosed in this pass (out of scope for a sports-tranche run; would need bisecting the actual merge
  DAG around 2026-08-08 01:00Z–2026-08-09 across whichever slots touched this file, which requires reflog/full-history
  spelunking beyond what a single-tranche reconciliation pass should spend on an infra/process question). Leading
  hypothesis, NOT verified: a slot with a LOCAL checkout predating `ad137ae4e`/`f44dfadd4` (i.e. still holding the
  pre-archive, `locked_by: ""`-unnormalized version of the file in its working tree) made an UNRELATED edit to a
  nearby/same file under `plans/active/issues/`, and `quickmerge`'s `git pull --rebase --autostash` reconciliation (or a
  `docs(plans):` fast-path via `safe-doc-push.sh`) resolved the ensuing state in favor of that stale branch's tree for
  this specific file — effectively re-creating the pre-archive blob at the active path while the archive-side create
  silently vanished. This would be a distinct failure mode from the already-documented
  `quickmerge_concurrent_same_file_edit_blind_overwrite_2026_08_08.md` (that incident is same-file
  content-clobber-via-non-conflicting-line-ranges; this one is a full delete+create pair — the two SIDES of one archival
  `git mv` — being unwound as a unit by something in the merge path, not just one hunk landing wrong).
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [backend, git-discipline, quickmerge, archival, cross-cutting, ci-cd, conflict-detection, data-integrity]
related:
  [
    /plans/archive/issues/quickmerge_concurrent_same_file_edit_blind_overwrite_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
author: plan_reconciler
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: NA
source:
  plan_reconciler sports-tranche run 2026-08-09 (`agt-8da8df`, slot 14), discovered while re-verifying an archive
  candidate that turned out to already have an (undone) prior archival attempt.
resolved_by:
locked_by:
depends_on: []
---

# Archived plan doc silently resurrected by later concurrent merge activity

## What was found

1. `unified-trading-pm@f44dfadd4` (2026-08-08T01:02:55Z) `git mv`'d
   `plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md` →
   `plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md`, with real evidence (all 7 todos
   done, converging with a 2026-08-05 fleet-wide re-verification already in the doc's own Progress Log), and also
   repointed 5 real path-format referrers.
2. By 2026-08-09, both the active-path original and the archive-path copy are gone from where `f44dfadd4` put them — the
   doc is back at the ORIGINAL active path with PRE-archive content (`status: open`), and the archive-path copy does not
   exist anywhere in the current tree.
3. `git log -- plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md` (the current active path)
   shows no trace of `f44dfadd4` or `ad137ae4e` (its immediately preceding commit on the same doc) — those two commits
   exist in the repo (`git show <sha>` resolves both, with real diffs matching their commit messages) but are not
   ancestors of the current tip at that path.
4. The exact same commit (`f44dfadd4`) also archived a second, unrelated doc
   (`dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md`) in the same operation — that doc shows the
   identical resurrection pattern, currently back at its active path. Not sports-tranche; not fixed in this pass.

## Why it matters

- The archival ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) is a HARD RULE ("a plan
  with every todo done + unlocked MUST be archived immediately") enforced by a mechanical gate
  (`check_terminal_status_archived`) that this run's own commit hit directly (see Progress Log below). If an already-
  correctly-archived doc can silently revert to active with its pre-resolution content, the corpus's archived/active
  boundary is not durable under this workspace's concurrent-fleet-merge conditions — any of the ~30 parallel slots'
  `git pull --rebase --autostash` reconciliation, or the `docs(plans):` fast path via `safe-doc-push.sh`, is a candidate
  mechanism, unconfirmed.
- Downstream cost: this run re-did ~10 minutes of duplicate work (re-verifying evidence a prior agent had already
  verified and acted on correctly) purely because the action didn't stick. At fleet scale, an unknown number of other
  archived docs could be silently un-archived the same way, silently re-inflating the `plans/active/` corpus size /
  NA-ratchet / near-complete-candidate counts that other audits (`/na-eligibility-audit`, `check_na_corpus_ratchet.py`)
  track as ground truth.
- No content was destroyed (git history has everything, and the current active-path copies are coherent, complete docs)
  — this is a process-durability bug, not a data-loss incident. Filed at P1 (repeatable pattern, not urgent-blocking)
  rather than P0.

## Recommended next steps (for the engineering owner, not resolved here)

1. Confirm the mechanism: pick one of the two known-affected docs, and walk the actual merge/rebase DAG around
   2026-08-08T01:00Z–2026-08-09 (`git log --all --graph` scoped to a tight window, or `git reflog` on any slot that
   might still have the relevant local state) to find the specific commit/rebase that reintroduced the pre-archive blob.
2. If the hypothesis in the summary holds (a stale-branch rebase/merge resolving in favor of an outdated tree for a file
   that had since been moved elsewhere), this is likely NOT specific to archival — the same mechanism could
   theoretically resurrect any deleted/moved file under high concurrent load, which is a broader class than just the
   plan-archival ritual. Scope the fix accordingly once the mechanism is confirmed.
3. Consider whether `check_terminal_status_archived` / `check_create_only_archive_commits` (or a new check) should also
   catch "this exact path was VALIDLY deleted by a reachable commit that is not an ancestor of HEAD at this path" as its
   own hard-fail signal — that is precisely the fingerprint of this incident and would make it self-detecting instead of
   relying on an agent noticing it by chance while re-verifying an archive candidate.

## Progress Log

- **2026-08-09 plan_reconciler (sports tranche, `agt-8da8df`)**: filed. Re-archived
  `sports_index_recency_masked_captured_atoms_2026_07_13.md` a second time in the same run (see that doc's own Progress
  Log + this run's `plan_reconciler_findings_sports_2026_08_09.md`), with an immediate verify-at-HEAD + solo push to
  minimize repeating the same race window. Did NOT re-archive
  `dex_pool_state_build_instrument_id_colon_in_symbol_2026_08_04.md` (out of sports-tranche scope) — flagging here for
  whichever tranche/pass owns it, or a future `all` unsharded run.
