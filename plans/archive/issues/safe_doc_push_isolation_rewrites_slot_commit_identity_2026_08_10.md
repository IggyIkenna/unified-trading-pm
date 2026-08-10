---
doc_type: issue
title: safe-doc-push isolated-worktree mode silently mis-attributes slot commit identity to main
summary: >-
  safe-doc-push.sh's isolated-worktree mode (default since 2026-08-10) commits from a private worktree at
  `$TMPDIR/sdp-iso-$$/unified-trading-pm` — a path with no `.tabs/<N>/` segment — so the PATH-based fix-commit-identity
  hook derives `main` instead of the caller's slot and actively REWRITES a slot worker's `[slot-N·planning]` author to
  `[main·planning]`. Confirmed live on slot 31 (2026-08-10). Every slot worker's pure-doc commits silently ship
  mis-attributed to main, corrupting the attribution audit trail (a HARD RULE).
status: resolved
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [git-discipline, commit-identity, safe-doc-push, isolation, infra]
related:
  - /plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
drift_direction: advance-code
resolved_by: unified-trading-pm@015b869269
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - safe-doc-push.sh isolated-worktree mode (default since 2026-08-10)
depends_on: []
---

> **🟢 ARCHIVED 2026-08-10** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Resolution evidence carried in `resolved_by:` (unified-trading-pm@015b869269). Moved by
> slot-29 per the flip-then-mv two-commit pattern: the checkbox flip + `archive_exempt: true` bridge landed in
> `20b7784d1f` (file kept at the original path so the AO server's M3 flip verification saw the `- [x]`); this commit
> performs the `git mv` to `plans/archive/issues/` and drops the now-moot exempt line. No content was rewritten.

# safe-doc-push isolated-worktree mode silently mis-attributes slot commit identity to main

## What I found

`safe-doc-push.sh`'s isolated-worktree mode (the default since 2026-08-10, per
`pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` F6) creates its private commit worktree at
`$TMPDIR/sdp-iso-$$/unified-trading-pm` — a path with **no `.tabs/<N>/` segment**. The `fix-commit-identity` pre-commit
hook derives the commit label **purely from the PATH** (`scripts/hooks/slot-identity-lib.sh`: `…/.tabs/<N>/<repo>` →
`slot-<N>`; anything else → `main`). So inside the isolated worktree the hook resolves `main`, **actively REWRITES a
slot worker's correct `[slot-N·planning]` author to `[main·planning]`** via `git config --worktree`, then fails the
commit (exit 6) demanding a re-run — and the re-run lands with the mis-attributed identity.

**Confirmed live on slot 31, 2026-08-10** (first `safe-doc-push.sh` invocation of the session): the hook printed
`commit identity was 'ikennaigboaka [slot-31·planning]'` then
`Corrected to 'ikennaigboaka [main·planning]' for THIS worktree (git config --worktree)`. The isolated worktree was at
`/tmp/sdp-iso-238038/unified-trading-pm`. This was NOT a false alarm: the correction is the hook doing exactly what it
is designed to do — enforce path-derived identity — against a path shape the isolation mode violates.

## Why it matters

Commit attribution is a HARD RULE: author NAME must be `ikennaigboaka [slot-<N>·<host>]`, audited by
`scripts/dev/check-slot-commit-identity.sh`. Under the default isolated mode, **every slot worker's pure-doc commits
ship attributed to `main`**, silently corrupting the attribution audit trail and the "who shipped what" provenance for
plan flips. The workaround (`SDP_ISOLATED=0`, shared-index path from the caller's own `.tabs/<N>/` checkout) is
undocumented in the script's header and easy to miss.

This is **distinct** from F6/F7 in `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`: those cover
prek-vs-peer-unstaged-WIP (F6) and the hygiene sweep's hard-coded directory NAME (F7). The identity rewrite is a
separate failure of the same mitigation's path assumption.

## Recommended decision

Fix `safe-doc-push.sh` to propagate the caller's resolved slot identity into the isolated worktree before the inner
re-exec, so the default isolated mode preserves `[slot-<N>·<host>]` attribution for every worker — not just those who
happen to know the `SDP_ISOLATED=0` escape hatch.

- [x] ✅ [INFRA] P1. **Propagate caller slot identity into safe-doc-push's isolated worktree** (repo:
      unified-trading-pm) — unified-trading-pm@015b869269. Fix shipped + verified: the isolated commit worktree now
      carries the caller's `.tabs/<N>/` segment so `fix-commit-identity` derives `[slot-N·host]` and no-ops; regression
      bats test `tests/test_safe_doc_push_isolated_identity_preserved.bats` asserts the pushed commit's author carries
      the slot label. Live-verified on slot 29 (issue-doc flip landed as `[slot-29·planning]`, not `[main·planning]`).
      In the isolated-worktree branch (`scripts/dev/safe-doc-push.sh`, ~line 217), before re-exec'ing the inner script,
      set the caller's resolved identity on the worktree so `fix-commit-identity` derives the correct label — either (a)
      run `source scripts/hooks/slot-identity-lib.sh` + `slot_identity_resolve "$_sdp_origin_repo"` in the caller, then
      `git -C "$_sdp_iso_wt" config user.name "$SLOT_ID_EXPECTED_NAME"` + `config user.email "$SLOT_ID_CANON_EMAIL"`, or
      (b) pass `SLOT_CANON_NAME`/`SLOT_CANON_EMAIL` env (canon only, does NOT fix the PATH-derived label — prefer (a)).
      Verify: land a slot-31 doc flip via default isolated mode, confirm `git log -1 --format='%an'` reads
      `[slot-31·planning]`, and `check-slot-commit-identity.sh` passes. Also add a one-line note in the script header
      documenting `SDP_ISOLATED=0` as the documented escape hatch until the fix lands.

## Progress Log

- **slot-29 2026-08-10 (infra, todo -001, `safe_doc_push_isolation_rewrites_slot_commit_identity-001`)**: IMPLEMENTED +
  LIVE-VERIFIED, **SHIPPING BLOCKED on PM `qg_red`**. Implemented the fix in `scripts/dev/safe-doc-push.sh`: the
  isolated commit worktree is now built at `$TMPDIR/sdp-iso-$$/.tabs/<N>/unified-trading-pm` (carrying the caller's
  `.tabs/<N>/` segment, leaf stays `unified-trading-pm` per F7) so the PATH-based `fix-commit-identity` hook derives the
  caller's label and no-ops; identity resolved early via `slot-identity-lib.sh` against the caller repo path, with a
  belt-and-suspenders pre-stamp of the worktree config; header documents `SDP_ISOLATED=0` as the escape hatch.
  Regression bats test `tests/test_safe_doc_push_isolated_identity_preserved.bats` asserts the pushed commit's author
  carries the slot label. **Live-verified**: a real isolated-mode push from slot 29 (this issue's sibling doc flip)
  landed with author `ikennaigboaka [slot-29·planning]`, NOT `[main·planning]` (the exact bug). **BLOCKER**: PM
  `quality-gates.sh` is red on 8 PRE-EXISTING live-corpus test failures (`check_workspace_code_workspace_drift.py` ×5 +
  `check_finalize_plan_coverage.py` ×3 — see
  `/plans/archive/issues/pm_qg_pre_existing_red_workspace_drift_and_finalize_coverage_2026_08_10.md`, verified
  pre-existing at base HEAD). Fix committed locally as `7b84434c0f` (ahead=1) but NOT pushed — quickmerge sentinel
  requires a green PM QG, which the pre-existing red blocks. Joined fleet-wide repo-blocker `RB-5b82f02e` (PM qg_red,
  escalated). **Resume**: when PM QG is green (fleet fixing via the sibling issue's todos), re-run `quality-gates.sh` on
  this commit, quickmerge, flip this checkbox with evidence.
- **slot-29 2026-08-10 (infra, todo -001, SHIPPED)**: PM QG green after slot-23's `_pm_root.py` root-cause fix
  (`465ea24093`). Re-ran `quality-gates.sh` → **ALL QUALITY GATES PASSED (116s)**. Quickmerge `--agent --files` pushed
  both commits to `origin/live-defi-rollout`: `015b869269`
  (`fix(ao): propagate caller slot identity into safe-doc-push's isolated worktree` — author
  `ikennaigboaka [slot-29·planning]`, `Quickmerge: agent` trailer) + `22c6e73822` (depends_on hygiene). Verified:
  `git rev-list --count origin/live-defi-rollout..HEAD` = 0, tree clean. Checkbox flipped with evidence
  `unified-trading-pm@015b869269`. Task 2 (`safe_doc_push_isolation_rewrites_slot_commit_identity-001`) complete.
- **slot-29 2026-08-10 (archival)**: `archive_exempt: true` set as the SANCTIONED flip-then-mv bridge
  (`check_archive_candidates.sh` --only mode, flip-then-mv exemption 2026-08-09). Flipping this doc's last open todo to
  done makes it a 0-open/some-done/unlocked archive candidate; combining the flip with the `git mv` in ONE commit would
  show only a deletion at the original plan_ref path and defeat the AO server's cross-repo `/done` M3 checkbox-flip
  verification. Per the sanctioned pattern: the flip + `archive_exempt: true` land in THIS commit (file stays at the
  original path so M3 sees the `- [x]`); the `git mv` to `plans/archive/issues/` (dropping the now-moot exempt line,
  `status: resolved`, archive banner) is the IMMEDIATELY FOLLOWING commit. This is a bridge, not a durable exemption.
