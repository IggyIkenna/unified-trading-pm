---
doc_type: issue
title:
  "full-workspace-sit's SIT_VALIDATED stamping loop unconditionally skipped every pinned-detached-HEAD re-check (the
  promote gate's SIT-on-LDR mechanism), causing an infinite promote-gate loop for any BREAKING-delta repo — RESOLVED"
summary: >-
  The LDR→main promote gate's breaking-delta SIT check (`ldr_to_main_fleet_promote.sh` STEP 5) dispatches
  `full-workspace-sit` with `client_payload.sha` pinned to the EXACT LDR commit it needs re-validated. That job's "Clone
  all active repos" step then `git checkout <sha>`s the pinned repo, which detaches HEAD even though the commit is a
  legitimate live-defi-rollout commit. The downstream "Stamp SIT_VALIDATED + LDR tree" step's branch guard did a literal
  `[ "$(git rev-parse --abbrev-ref HEAD)" != "live-defi-rollout" ]` comparison, so it unconditionally skipped the stamp
  for every such pinned run — confirmed live in run 31110890960: SIT passed for alerting-service, then "skip
  alerting-service (on 'HEAD', not live-defi-rollout)". Because the promote gate's own re-check mechanism is exactly
  what triggers the pin, this created an INFINITE LOOP for any repo with a breaking delta: promote gate blocks ->
  dispatches SIT-on-LDR (pinned) -> SIT passes -> stamp skipped (detached HEAD) -> promote gate still sees a
  stale/missing `sit_validated_tree` -> blocks again -> dispatches again -> forever. This was blocking alerting-service
  PR #344 from promoting to main. Fixed by accepting a detached HEAD whose commit is live-defi-rollout's own tip or a
  verified ancestor of it (`git merge-base --is-ancestor`), since the real safety net against stamping a wrong tree is
  the CONSUMER's independent tree-equality check (`sit_validated_tree == LDR_TREE`), not this local branch-name guard.
  Verified live: pre-fix Firestore `sit_validated_tree` for alerting-service was stuck at a stale 2026-08-05 value
  despite repeated green pinned SIT runs; a fresh pinned dispatch AFTER the fix landed on `main` updated
  `sit_validated_tree` to the EXACT LDR tree of the pinned commit within the same run.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [system-integration-tests, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, sit, sit-gate, detached-head, promote-gate, ldr-main, stamping, infinite-loop]
related:
  [
    /plans/archive/2026_08/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
    /plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md,
  ]
created: 2026-08-06
last_updated: 2026-08-06
author: agent (slot session, system-integration-tests SIT stamp fix task)
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: cicd
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: system-integration-tests@0dc3ff1dff85a4bdaadcfdaa7812611cf88cbd48
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    system-integration-tests/.github/workflows/full-workspace-sit.yml,
    unified-trading-pm/scripts/cicd/ldr_to_main_fleet_promote.sh,
    /plans/archive/2026_08/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
  ]
source:
  [
    "Freshly diagnosed this session (2026-08-06) — confirmed via grep of plans/active/ and plans/active/issues/ that
    this exact detached-HEAD stamping-skip mechanism was not previously tracked (related docs cover adjacent SIT-gate
    flakiness but not this root cause)",
    "confirmed live in system-integration-tests run 31110890960: 'pinning alerting-service to dispatched sha
    7033bc94c00e' -> '✅ alerting-service alert/notification contract' -> 'skip alerting-service (on 'HEAD', not
    live-defi-rollout)'",
    "confirmed the resulting infinite loop by triggering ldr-to-main-promote-fleet.yml twice ~20 min apart for
    unified-trading-pm and observing the identical sit_validated_tree/LDR tree mismatch both times despite a full
    SIT-on-LDR run completing green for alerting-service in between",
  ]
---

> **🟢 ARCHIVED 2026-08-07 — RESOLVED** (no open todos, unlocked). Archived by cicd wall-resolution (`agt-cfe24e`) as
> part of the `terminal-status-archived` ratchet fix for the LDR→main promote gate.

# full-workspace-sit's SIT_VALIDATED stamping loop unconditionally skipped every pinned-detached-HEAD re-check

## Root cause

`system-integration-tests/.github/workflows/full-workspace-sit.yml`'s `cross-repo-invariants` job has two relevant
steps:

1. **"Clone all active repos as siblings"** — when the job is dispatched via `repository_dispatch` carrying
   `client_payload.repo` + `client_payload.sha` (the promote gate's SIT-on-LDR re-check mechanism, added 2026-08-06 per
   `sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md`), it
   `git fetch --depth=1 origin "$PINNED_SHA" && git checkout -q "$PINNED_SHA"` for exactly that one repo. This puts the
   clone in **detached HEAD** state (`git rev-parse --abbrev-ref HEAD` returns the literal string `"HEAD"`), even though
   the pinned commit is a perfectly legitimate `live-defi-rollout` commit — it is precisely the `LDR_SHA` the promote
   gate itself computed and asked to be re-validated.
2. **"Stamp SIT_VALIDATED + LDR tree"** — on a green cross-repo-invariants run, this step stamps
   `ci_status=SIT_VALIDATED` + the LDR tree fingerprint for covered repos. Its guard was:

   ```bash
   BR="$(git -C "$r" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
   if [ "$BR" != "live-defi-rollout" ]; then echo "skip $r (on '$BR', not live-defi-rollout)"; continue; fi
   ```

   For a pinned-detached-HEAD repo, `$BR` is literally `"HEAD"`, so this guard **unconditionally skipped the stamp** —
   even though the SIT run had just genuinely validated that exact commit.

Because the pin mechanism exists specifically for the promote gate's "this tree needs re-validation" case, the bug
created an **infinite loop** for any repo with a breaking main..LDR delta:

```
promote gate: SIT GATE BLOCK (sit_validated_tree stale/unset)
  -> dispatches full-workspace-sit pinned to LDR_SHA
  -> SIT passes (cross-repo-invariants green)
  -> stamp step: detached HEAD -> "skip <repo> (on 'HEAD', not live-defi-rollout)"
  -> Firestore sit_validated_tree never updated
  -> next promoter tick: SIT GATE BLOCK again (same stale sit_validated_tree)
  -> dispatches full-workspace-sit again
  -> ... forever
```

This was confirmed live in `system-integration-tests` run `31110890960`:

```
pinning alerting-service to dispatched sha 7033bc94c00e (was: ...)
✅ alerting-service pinned to 7033bc94c00e
...
✅ alerting-service alert/notification contract
...
skip alerting-service (on 'HEAD', not live-defi-rollout)
```

and by triggering `ldr-to-main-promote-fleet.yml` twice ~20 minutes apart, observing the IDENTICAL
`sit_validated_tree`/LDR-tree mismatch both times despite a green SIT-on-LDR run for alerting-service completing in
between. This was actively blocking `alerting-service` PR #344 (commit `4e252b4`) from promoting to `main`.

## Why the guard was safe to relax

The comment above the guard stated its intent: "only stamp a repo actually checked out on live-defi-rollout (the clone
may have fallen back to main; stamping a main tree would be wrong — though the consumer's tree-equality check would also
reject it)." That consumer-side safety net is real and independently verified —
`unified-trading-pm/scripts/cicd/ldr_to_main_fleet_promote.sh` (~line 693):

```bash
if [ "$SIT_STATUS" != "FAILING" ] && [ -n "$SIT_TREE" ] && [ "$LDR_TREE" = "$SIT_TREE" ]; then
  echo "SIT GATE PASS $REPO: ..."
```

This is an **exact tree-SHA comparison**, entirely independent of branch names — a repo that genuinely fell back to a
`main` clone would produce a different tree and fail this check regardless of what the local branch-name guard in
`full-workspace-sit.yml` did. The local guard is therefore only defense-in-depth, not the load-bearing safety mechanism,
and was safe to relax for the legitimate detached-HEAD case.

## Fix

`system-integration-tests/.github/workflows/full-workspace-sit.yml`, "Stamp SIT_VALIDATED + LDR tree" step: accept a
detached HEAD (`$BR = "HEAD"`) whose commit is either (a) exactly the tip of the local `live-defi-rollout` branch ref
captured at clone time (fast path — the common case, LDR was quiescent between the promote gate's read and this clone),
or (b) a verified ancestor of `origin/live-defi-rollout` via `git merge-base --is-ancestor` (after
`git fetch --unshallow`/`--deepen=1000`, since the initial clone is `--depth=1` and the pin-checkout's separate SHA
fetch has no connecting history to the branch tip). A clone that genuinely fell back to `main` still checks out a NAMED
branch (`"main"`), not a detached HEAD, so it is unaffected by the new branch and still falls through to the
(still-present) rejection.

Regression test: `system-integration-tests/tests/abbreviated/test_full_workspace_sit_stamp_detached_head_guard.py`
extracts the REAL guard bash from the live workflow YAML (via PyYAML, not a hand-copied replica) and runs it against
real temp git repos in all 5 relevant states: normal branch checkout (accept), main-fallback (reject — the guard's
original purpose), detached HEAD at LDR's exact tip (accept, fast path), detached HEAD at an ancestor after simulated
LDR churn (accept, merge-base path), and detached HEAD at an unrelated commit with no shared history (reject — proves
the fix doesn't just accept any detached HEAD).

**Shipped**: `system-integration-tests@0dc3ff1dff85a4bdaadcfdaa7812611cf88cbd48` (quickmerge, QG green,
`--skip-preflight` used because 3 unrelated sibling path-deps — features-service, strategy-service, deployment-api — had
unrelated uncommitted `semver-agent.yml` WIP from other concurrent slots; my change touches neither those repos nor
their content). Promoted LDR→main via `system-integration-tests` PR #345 (merged 2026-08-06T15:07:39Z).

## Live verification

1. **Pre-fix baseline** (Firestore `ci_status` doc for alerting-service, via `ci_status_store.py get-doc`):
   `sit_validated_tree: "4610b8ed52fd7b686f9f4c791ed138685c9de47a"`, `updated_at: 2026-08-05 15:04:07Z` — stale, from
   before the bug was even discovered, despite the confirmed green SIT run for a later pinned commit (`7033bc94c00e`) in
   between.
2. Confirmed the fix's content reached `main` (`git show origin/main:.github/workflows/full-workspace-sit.yml` contains
   the new `ON_LDR` guard logic) after PR #345 merged.
3. Manually dispatched a fresh `full-workspace-sit` `repository_dispatch` with
   `client_payload={repo: alerting-service, sha: 3fb8ac4bfddc31a73a2df31931e807e7c88b8112}` — the exact same
   pinned-detached-HEAD scenario the bug hit, using alerting-service's then-current LDR tip (tree
   `27e2d867f684950243a9a6169c8a01564aef1f05`).
4. Run `31114385051` executed the (now-fixed) workflow: cross-repo-invariants passed, then the Stamp step ran.
5. **Post-fix result**: re-reading the Firestore doc mid-run showed `sit_validated_tree` updated to
   `"27e2d867f684950243a9a6169c8a01564aef1f05"` — **the exact LDR tree of the pinned commit** — confirming the stamp
   landed for a pinned-detached-HEAD run for the first time. (`updated_at` itself did not change because
   `resolve_status`'s no-downgrade logic keeps a higher-ranked prior status (`MAIN_GREEN`, rank 4) over an incoming
   `SIT_VALIDATED` write for that field — per the workflow's own comment, "the TREE FINGERPRINT, not the status label,
   is the load-bearing proof," and the store records the fingerprint regardless of rank.)

## PR #344 (alerting-service) — separate, unrelated blocker

PR #344 (`chore(promote): LDR → main`, head `4e252b43b3032ba5abcc1ebe755f1fe2fc5cc88e`) was **not** confirmed to merge
as a direct result of this fix. Its `mergeStateStatus` is `DIRTY`/`CONFLICTING` — a genuine git content conflict against
`main`, entirely unrelated to the SIT-stamp bug: `main..promote` diffs on files like
`.github/workflows/main-backmerge-to-ldr.yml` (main references `runs-on: [self-hosted, glue]`, LDR has moved to
`ubuntu-latest`) and `.github/workflows/image-build-gate.yml` (main still points at `unified-trading-pm`'s reusable
workflow, LDR points at the newly-extracted `unified-trading-ci`) — the same class of workflow-template drift documented
in `/plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md`, caused by today's
shared-CI-repo extraction and being resolved by other concurrent slots. This is out of scope for this issue; the
SIT-stamp mechanism itself is proven fixed (item 5 above) independent of whether/when PR #344's separate merge conflict
resolves.

## Findings triage

In-scope, fixed same-session. No further action needed on the SIT-stamp bug itself. PR #344's unrelated merge-conflict
blocker is tracked by the concurrent shared-CI-repo-extraction work already in flight (see
`strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md` for the same class of issue); not duplicated
here.
