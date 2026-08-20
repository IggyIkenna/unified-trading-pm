---
doc_type: issue
title: >-
  The promote→main-backmerge-to-ldr cycle silently REVERTS a comment-only caller-stub
  change on 5 churn-heavy repos — shipped commit becomes a non-ancestor of
  origin/live-defi-rollout
summary: >-
  While shipping the fleet-wide caller-stub safety-net comment fix
  the batch17 caller-stub comment fix, the comment-only
  `.github/workflows/main-backmerge-to-ldr.yml` change was pushed to LDR and verified on
  origin, then silently dropped: within ~1h a `main-backmerge-to-ldr` run (P1's new
  fleet-wide drift-tick dispatch, often workflow_dispatch-triggered) made the shipped
  commit a NON-ANCESTOR of origin/live-defi-rollout. 5 repos hit it (deployment-service,
  execution-service, strategy-service, unified-api-contracts, unified-trading-library);
  2 re-shipped + converged (fix now also on main), the other 3 are additionally blocked by
  pre-existing QG reds. A `chore(promote): LDR → main` squash + the following backmerge
  re-introducing main's stale content is the suspected mechanism (the documented
  silent-revert-loss class), but the re-apply surviving on some repos and not others is not
  yet explained — needs a focused reproduction before the re-ship is trusted.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service, unified-api-contracts, unified-trading-library, unified-trading-ci, unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, backmerge, promote, ldr, silent-revert, comment-fix, drift-tick]
related:
  [
    /plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
context_scope:
  [
    /codex/08-workflows/ci-cd-flow.md,
    unified-trading-ci/.github/workflows/main-backmerge-to-ldr.yml,
    unified-trading-pm/.github/workflows/branch-health.yml,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: ci_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: cicd
effort: medium
drift_direction: advance-code
resolved_by:
supersedes:
superseded_by:
depends_on:
locked_by:
locked_since:
source: >-
  slot 6 worker, dispatch cross_cutting_satellite_ao_dispatch_batch17-640def3b3205 (item 2,
  caller-stub comment fix), 2026-08-20
---

# The promote→backmerge cycle silently REVERTS a comment-only caller-stub change

## What happened (measured, not inferred)

| Fact | Evidence |
| --- | --- |
| Comment fix committed to all 25 real caller stubs | perl replace, md5-verified identical across stubs; `git log --grep="correct main-backmerge"` finds the commit in every repo |
| Fix shipped to LDR + verified on origin | per-repo `git merge-base --is-ancestor HEAD origin/live-defi-rollout` passed immediately post-quickmerge |
| Fix silently reverted on 5 repos within ~1h | later `git show origin/live-defi-rollout:<file> \| rg -c "every 30 min"` = 1 (old comment back) on deployment-service, execution-service, strategy-service, unified-api-contracts, unified-trading-library |
| My commit became a NON-ANCESTOR of origin/live-defi-rollout (dropped, not merged-over) | `git merge-base --is-ancestor <my-sha> origin/live-defi-rollout` → NO on all 5; commit still exists as a dangling object locally |
| Suspected trigger: a `main-backmerge-to-ldr` run after a `chore(promote): LDR → main` squash | `gh run list --workflow main-backmerge-to-ldr.yml` shows `chore(promote)`-triggered runs + P1's new `workflow_dispatch` drift-tick runs (e.g. deployment-service run 32373806481, 9m7s, completed success) |
| Repos where the fix survived DID have the fix also on main | deployment-service / strategy-service: `origin/main:<file>` old-count = 0 after re-ship |
| 3 of the 5 are additionally blocked by pre-existing QG reds (NOT caused by this comment-only change) | features-service (RB-5e5dbb39), unified-trading-library (RB-09ca4f33), execution-service (RB-70f96454) |

## Why it matters

The comment fix is the "safety-net description" for the P1 fleet-wide drift-tick. If the
backmerge cycle silently reverts comment-only `.github` caller-stub changes on repos with
active promote traffic, then **any** caller-stub / workflow-comment edit on a churn-heavy repo
can be dropped without a conflict, without an error, and without the author noticing — the
"ahead=0 + clean tree ≠ landed" trap. This is a distinct mechanism from the parent issue's
"backmerge never runs / has no retry net": here the backmerge RUNS and actively re-introduces
stale content.

## Todos

- [ ] [CI] P2. **Reproduce + root-cause the backmerge revert of a comment-only caller-stub change.** Pick one
      repo (deployment-service is the cleanest — fix converged on main, so re-shipping is safe), ship the comment
      fix, then inspect the next `main-backmerge-to-ldr` run's merge-base and result tree. Confirm whether the
      `Promoted-From-LDR` trailer was stamped on the `chore(promote)` squash, whether the explicit merge-base
      path fired, and why `check_no_silent_revert_loss` did not trip on the caller-stub file (its scope is
      "LDR's OWN most recent commit" — a comment edit may fall outside the guard's file-content comparison). Fix
      the backmerge (or document the guard's scope limit) so a comment-only `.github` change survives a promote →
      backmerge round-trip. Repo: unified-trading-ci (+ unified-trading-pm if branch-health.yml is involved).
- [ ] [CI] P2. **Re-ship the 3 blocked repos once their QG reds clear** (features-service RB-5e5dbb39,
      unified-trading-library RB-09ca4f33, execution-service RB-70f96454): fresh-pull, re-apply the caller-stub
      comment fix, QG green → quickmerge `--agent`. Each still carries the local commit from 2026-08-20's first
      attempt. Repos: features-service, unified-trading-library, execution-service.

## Progress Log

### 2026-08-20 — filed from slot 6 (dispatch cross_cutting_satellite_ao_dispatch_batch17-640def3b3205, item 2)

Shipped the fleet-wide caller-stub comment fix to 25 repos. On re-verification (per the CLAUDE.md
`ahead=0 + clean tree ≠ landed` rule — quickmerge's own "Landed" is not trusted), 5 repos showed the
old comment back on `origin/live-defi-rollout` and my shipped commit was no longer an ancestor.
Re-shipped deployment-service + strategy-service + unified-api-contracts; deployment-service and
strategy-service converged (fix now on main AND LDR). The other 3 (features-service,
unified-trading-library, execution-service) hit pre-existing QG reds (unrelated Python test failures —
the change is comment-only YAML) and are parked on repo-blockers. Not yet root-caused why the backmerge
reverted the comment on 5 repos but the re-apply converged on 2; filed this issue with an explicit
reproduction todo rather than blindly re-shipping the same fix into a cycle that may drop it again.
