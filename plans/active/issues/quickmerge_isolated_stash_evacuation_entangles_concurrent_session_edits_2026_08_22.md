---
doc_type: issue
title: quickmerge --isolated stash-evacuation entangles a DIFFERENT concurrent session's edits to the same file, and does not restore on a mid-run STAGE-1 failure
summary: >-
  Live-caught 2026-08-22 (T2, instruments-service): `quickmerge.sh --isolated` evacuates named
  --files from the caller tree via `git stash push -- <files>` before entering the isolated
  worktree. That stash is FILE-granular, not session-granular — if a different concurrent session
  is mid-edit on the SAME file in the SAME shared checkout, its uncommitted hunks ride along in
  the same stash entry. When the isolated run then fails at STAGE 1 (dependency validation) before
  reaching its own commit, the evacuation stash was never restored to the caller tree: both
  sessions' edits vanished from the working tree simultaneously, recoverable only by manually
  finding and disentangling the stash. No data was lost (stash@{0} preserved it), but a live peer
  session's build_instrument_catalogue.py briefly had zero trace of its own uncommitted work.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, instruments-service]
scope: [engineer]
tags: [quickmerge, isolated-worktree, concurrency, shared-checkout, data-loss-near-miss]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/issues/instruments_schema_not_locked_versioned_2026_08_18.md,
  ]
context_scope:
  [unified-trading-pm/scripts/quickmerge.sh]
created: "2026-08-22"
last_updated: "2026-08-22"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: NA
effort: medium
drift_direction: NA
sequential: false
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
author: T2 session (B23 part-4 wiring task, 2026-08-22)
source: [live incident during B23 part-4 instrument_catalogue SchemaContract gate wiring]
---

# quickmerge --isolated stash-evacuation entangles concurrent-session edits

## What happened

Shipping `instruments-service`'s B23 part-4 change (wiring the locked+versioned
`instrument_catalogue` `SchemaContract` gate into `promote_catalogue`,
`scripts/build_instrument_catalogue.py` + 2 test files) via
`bash scripts/quickmerge.sh "..." --agent --isolated --files '...'`:

1. First `--isolated` attempt failed at **STAGE 1: Dependency Validation** — `unified-api-contracts`
   (a sibling repo, dependency of instruments-service) had an uncommitted working-tree diff versus
   `origin/live-defi-rollout` (8 files: `_mvp_scope_rules.py`, `market_data_categories.py`,
   `defi_venue_capabilities.py`, etc. — a DIFFERENT session's live
   `prediction_layer1_expected_zero_denominator_undefined` investigation, confirmed unrelated to
   this task). Quickmerge correctly refuses to proceed ("Do NOT use --dep-branch... commit the
   dependency changes first" — an agent must not touch a dependency it doesn't own).
2. Waited ~9 minutes (a bounded background poll on `unified-api-contracts`'s dirty-file-count) —
   unchanged. Retried quickmerge — same STAGE 1 failure (the other session's work was still live and
   ongoing; new untracked files kept appearing in `instruments-service` too, confirming an active
   peer session, not stale/abandoned WIP).
3. **After both failed attempts, `git status` on the caller checkout showed
   `scripts/build_instrument_catalogue.py` and
   `tests/unit/scripts/test_promote_catalogue_dedup_aware_guard.py` as completely CLEAN** — this
   session's edits to both files were gone from the working tree. Root cause: `--isolated` mode's
   preamble message ("Your dirty --files are evacuated from the caller tree for the run's
   duration... restored automatically when this run finishes (success or failure)") ran a
   `git stash push -- <named files>` before entering the isolated worktree, but by the time the
   run reached this evacuation, **a different concurrent session had ALSO started editing the SAME
   two files** (`scripts/build_instrument_catalogue.py` +
   `tests/unit/scripts/test_promote_catalogue_dedup_aware_guard.py`) as part of an unrelated,
   in-progress `instruments_catalogue_definitions_and_field_history_2026_08_17.md` feature
   (field-change-log + monthly-rollup catalogue writers, evidenced by new untracked modules
   `instruments_service/reference_data/catalogue_field_history.py` /
   `catalogue_monthly_rollup.py` and a new test file
   `tests/unit/scripts/test_promote_catalogue_field_history_wiring.py`). `git stash push -- <file>`
   is **file-granular, not session/hunk-granular** — it stashed the WHOLE file's dirty content,
   which by then contained BOTH sessions' uncommitted hunks interleaved in one diff. When STAGE 1
   failed (before the isolated run reached anything that would pop/restore the evacuation stash),
   the "restored automatically... on failure" claim did not hold: the caller tree was left at clean
   HEAD, with BOTH sessions' work reachable only via the stash entry
   (`qm-iso-evac-45922-2026-08-22T06:54:58Z`).

## Impact

No data was permanently lost — the stash entry preserved everything, and this session found and
recovered it. But for several minutes, a live concurrent session's uncommitted
`build_instrument_catalogue.py` edits were invisible on disk with zero warning, in a shared
checkout neither session has exclusive ownership of. Had that other session inspected its own file
during that window, it would have seen its own work vanished — a genuine near-miss for the
`data-loss-near-miss` tag on this doc.

## Recovery performed (this session)

1. `git stash apply stash@{0}` (not `pop` — kept as a durable backup) to restore the COMBINED
   (both-sessions) content back to the caller tree's working files, un-blocking the concurrent
   session immediately.
2. Extracted this session's own 3 hunks (import-list addition, a new
   `_coerce_string_dtype_for_contract` helper, and the B23 part-4 gate block) via
   `git diff HEAD stash@{0} -- scripts/build_instrument_catalogue.py`, hand-verified against this
   session's own known edits, and replayed them onto a **separate scratch copy** of the clean
   `git show HEAD:...` base (never re-editing the shared working-tree file itself).
3. Staged that scratch copy directly into the git INDEX via `git hash-object -w` +
   `git update-index --cacheinfo`, bypassing `git add` entirely so the WORKING TREE file was never
   touched a second time — it still carries both sessions' uncommitted work for the peer session to
   find. Verified: `git diff --cached` contains zero of the other session's markers
   (`catalogue_field_history`, `write_monthly_catalogue`, `compute_field_changes`); the working tree
   file still contains both sessions' markers.
4. `git stash list` still shows `qm-iso-evac-45922-2026-08-22T06:54:58Z` — intentionally NOT
   dropped, kept as a second recovery path in case the disentanglement above missed anything.

## Recommended fix (not implemented here — PM/infra scope, outside this session's T2 repo authorization)

- `--isolated`'s evacuation stash should be **session-scoped**, not blind file-content capture — e.g.
  stash via a 3-way diff against the LAST KNOWN state this session itself wrote (so only this
  session's own hunks are captured), or refuse to evacuate a file whose on-disk mtime is newer than
  this session's own last edit to it (the same `mtime <120s` / liveness-gated heuristic this
  workspace already uses for inherited-dirty-WIP elsewhere).
- The "restored automatically when this run finishes (success or failure)" claim needs an actual
  `trap`/`finally` that fires on EVERY exit path, including a STAGE 1 (or any pre-commit stage)
  failure inside the isolated worktree — today it appears to only fire on paths that reach later in
  the script.
- Consider: STAGE 1's dependency-validation check (a sibling repo's `git diff` against origin) runs
  BEFORE any evacuation is needed at all when the conflict is fully knowable up front — reordering
  STAGE 1 ahead of the evacuation step would avoid ever stashing named files for a run that's
  going to fail anyway on an unrelated dependency.

## Progress Log

- **2026-08-22 (T2 session)**: incident caught + recovered live while shipping B23 part-4
  (`instruments_schema_not_locked_versioned_2026_08_18.md`'s last remaining todo). Filed here per
  findings-triage ("a doc/mechanism that misled/harmed you is a finding — fix or flag it"); the
  actual fix is PM/infra-scope (`unified-trading-pm/scripts/quickmerge.sh`), outside this T2
  session's authorized repos (instruments-service / market-tick-data-service /
  market-data-processing-service only), so filed as a tracked issue rather than patched blind.

- [ ] [SCRIPT] P1. Implement one of the recommended fixes above in
      `unified-trading-pm/scripts/quickmerge.sh`'s `--isolated` evacuation/restore path — either
      session-scoped evacuation, a guaranteed trap-based restore on every exit path, or reordering
      STAGE 1 ahead of evacuation. Repo: unified-trading-pm. Done-when: a reproduction (two
      concurrent dirty edits to the same file, one quickmerge run that fails at STAGE 1) no longer
      loses either session's edits from the working tree, verified by a new test/reproduction
      script.
