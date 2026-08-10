---
doc_type: issue
title: safe-doc-push isolated-worktree mode silently mis-attributes slot commit identity to main
summary: >-
  safe-doc-push.sh's isolated-worktree mode (default since 2026-08-10) commits from a private worktree at
  `$TMPDIR/sdp-iso-$$/unified-trading-pm` — a path with no `.tabs/<N>/` segment — so the PATH-based fix-commit-identity
  hook derives `main` instead of the caller's slot and actively REWRITES a slot worker's `[slot-N·planning]` author to
  `[main·planning]`. Confirmed live on slot 31 (2026-08-10). Every slot worker's pure-doc commits silently ship
  mis-attributed to main, corrupting the attribution audit trail (a HARD RULE).
status: open
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
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  - safe-doc-push.sh isolated-worktree mode (default since 2026-08-10)
---

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

- [ ] [INFRA] P1. **Propagate caller slot identity into safe-doc-push's isolated worktree** (repo: unified-trading-pm).
      In the isolated-worktree branch (`scripts/dev/safe-doc-push.sh`, ~line 217), before re-exec'ing the inner script,
      set the caller's resolved identity on the worktree so `fix-commit-identity` derives the correct label — either (a)
      run `source scripts/hooks/slot-identity-lib.sh` + `slot_identity_resolve "$_sdp_origin_repo"` in the caller, then
      `git -C "$_sdp_iso_wt" config user.name "$SLOT_ID_EXPECTED_NAME"` + `config user.email "$SLOT_ID_CANON_EMAIL"`, or
      (b) pass `SLOT_CANON_NAME`/`SLOT_CANON_EMAIL` env (canon only, does NOT fix the PATH-derived label — prefer (a)).
      Verify: land a slot-31 doc flip via default isolated mode, confirm `git log -1 --format='%an'` reads
      `[slot-31·planning]`, and `check-slot-commit-identity.sh` passes. Also add a one-line note in the script header
      documenting `SDP_ISOLATED=0` as the documented escape hatch until the fix lands.
