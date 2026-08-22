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
    /plans/archive/issues/instruments_schema_not_locked_versioned_2026_08_18.md,
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

- **2026-08-22 (T2 session, separate incident, same shared checkout, plain — NOT `--isolated` —
  quickmerge)**: shipping the point-in-time-equivalence work
  (`instruments_catalogue_definitions_and_field_history_2026_08_17.md`'s replay-proof todo) via
  `bash scripts/quickmerge.sh "..." --agent --files '<2 files>'` (no `--isolated`) hit a related but
  DISTINCT trigger of the same root-cause class: STAGE 1.6's dependency-version-gate auto-pull
  (`unified-api-contracts` pinned-version-behind-staging path) ran its own `git pull` with an
  autostash, then the autostash POP conflicted against `tests/unit/test_orchestrator_helpers.py` —
  a pre-existing, foreign, uncommitted WIP file this session never touched (dirty since before this
  session started; owner unknown, no `.agent-claim` marker present). Result: `git status` showed
  `UU tests/unit/test_orchestrator_helpers.py` (real git-stash-pop conflict markers — the
  7-angle-bracket "Updated upstream" / 7-equals / 7-angle-bracket "Stashed changes" sequence — in
  the working-tree file itself, confirmed via `git ls-files -u` + grep, not inferred), which then
  hard-blocked quickmerge's own STAGE 0.4
  not-behind-gate on its NEXT retry: `QUICKMERGE_BLOCKED code=PRECOMMIT_UNMERGED_INDEX ... error:
  Pulling is not possible because you have unmerged files.` No rebase was in progress
  (`.git/rebase-merge`/`rebase-apply` both absent) — this was a `stash pop` conflict, not a rebase
  conflict, so the CLAUDE.md-documented `rebase --abort` recovery recipe does not directly apply.
  This session did NOT touch/resolve the conflicted file (hard rule: never resolve a dirty file you
  don't own without knowing which side is correct) and could not complete the ship as a result —
  reported to the operator as a genuine blocker rather than force-resolved. Confirms the underlying
  problem is broader than `--isolated`'s evacuation-stash bug specifically: ANY quickmerge path that
  internally autostashes+pulls+pops on a shared checkout with a concurrent foreign dirty file is at
  risk, not just the `--isolated` worktree-evacuation path documented above.

- [ ] [SCRIPT] P1. Extend the same-class fix above (or add a parallel one) to STAGE 1.6's
      dependency-version-gate auto-pull path in `quickmerge.sh` (plain, non-`--isolated` mode) —
      today its `git pull --autostash` can pop-conflict against a concurrent foreign session's
      dirty file in the shared checkout, hard-blocking the CALLING session's own unrelated commit
      with no safe self-service recovery (resolving the conflict requires knowing which side is
      correct, which only the foreign file's owner does). Candidate fix: detect an unmerged
      index BEFORE attempting the pull and fail fast with a clear "not your conflict to resolve"
      message (already partially true via `QUICKMERGE_BLOCKED code=PRECOMMIT_UNMERGED_INDEX`'s
      recovery text) — or scope the autostash to exclude paths outside the caller's own `--files`
      list, mirroring the session-scoped-evacuation fix proposed above for `--isolated`. Repo:
      unified-trading-pm. Done-when: a reproduction (a foreign dirty file with a real conflict
      against origin, one quickmerge run with an UNRELATED `--files` list) either succeeds without
      touching the foreign file, or fails with a message that clearly identifies the file as not
      the caller's own and does not leave the caller session responsible for resolving it.

- **2026-08-22 (cross-session forensics, peers `2-f2`/`2-83`, relayed by T2 session)** — attribution
  for the live `test_orchestrator_helpers.py` UU conflict above, gathered so whoever resolves it
  doesn't have to re-derive it:
  - The dirty set also included `instruments_service/reference_data/catalogue_field_history.py`,
    `tests/unit/test_catalogue_point_in_time_equivalence.py` (untracked), and
    `scripts/quality-gates.sh` — all confirmed as THIS T2 session's own two dispatched sub-agents'
    in-progress work (the equivalence-proof + query-don't-derive-gate todos on
    `instruments_catalogue_definitions_and_field_history_2026_08_17.md`), not foreign. `2-83`
    flagged a live hazard while these stay staged in the shared index: any OTHER slot-2 session
    committing in `instruments-service` should `git restore --staged` them first, or they ride
    along into an unrelated commit.
  - The genuinely foreign, unresolved piece is narrower than first reported: only
    `instruments_service/engine/orchestrator/defi.py` (modified) +
    `tests/unit/test_orchestrator_helpers.py` (UU, 2 conflicting hunks). `2-f2` traced the conflict's
    other side to a LANDED commit, `878bc989` (`ikennaigboaka [slot-8·planning]`, an AO worker — not
    a laptop session — 2026-08-22 14:10:43 UTC, `fix(defi): migrate IS-producibility denominator
    consumers to UAC DEFI_LIVE_VENUES`). Context: `unified-api-contracts@326f9a6bfa` split
    `VENUES_BY_ASSET_GROUP["defi"]` (now full canonical membership, matching cefi/tradfi/sports/
    prediction) from the new `DEFI_LIVE_VENUES` (the IS-producible, phase-live subset, 103 of 126) —
    slot-8's commit moves denominator consumers onto the narrower, correct constant. If the
    conflicting local WIP in `defi.py`/`test_orchestrator_helpers.py` still treats
    `VENUES_BY_ASSET_GROUP["defi"]` as the producibility denominator, that side is the stale one —
    **a hypothesis for the resolver to verify, not yet confirmed**, since neither peer would resolve
    a file they don't own without the actual owner confirming. The owner is likely reachable only via
    the `planning` VM/AO channel, not a laptop-slot broadcast (`ListAgents`' peer-session list did
    not surface it) — worth checking AO's own dispatch/worker log for whatever task landed `878bc989`
    before assuming a human session owns the other side.
