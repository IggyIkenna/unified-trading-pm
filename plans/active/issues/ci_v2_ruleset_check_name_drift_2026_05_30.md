---
title: Branch-protection rulesets fleet-wide require check contexts no current workflow emits (un-mergeable PRs) — symptom of in-flight ci_canonical_v2_migration + bootstrap name bug
created: 2026-05-30
author: ikenna (slot-1 interactive)
source:
  - plans/active/ci_canonical_v2_migration_2026_05_29.md
  - "observation workflow wf_0cd5b4b6-464 (per-repo ruleset vs emitted check-run names, 2026-05-30)"
locked_by: live-defi-rollout
---

## What I found

Across the fleet, the GitHub **branch-protection rulesets** require status-check
**contexts that no current workflow emits**, so PRs to `staging` and `main` are
**un-mergeable via the normal PR flow** (the required check stays perpetually
"Expected"/pending). Of 25 repos audited: **17 have broken gates, 8 have no
rulesets, 0 are correctly configured.** Every repo that has these rulesets has
them mismatched.

Two rulesets are involved, both `enforcement: active`, **no bypass actors**
(blocks even repo admins):

- `require-quality-gates` → target `~DEFAULT_BRANCH` (main); requires bare
  `quality-gates-v2` (some repos also stale `check-staging-lock`).
- `require-staging-lock-check` → target `refs/heads/staging`; requires a mix of
  stale strings across repos: `quality-gates`, `call-quality-gates / quality-gates`,
  `Staging Lock Check / check-staging-lock`.

**Ground-truth emitted check-run names** (from real recent PRs) are different:

- QG check: `Quality Gates (<repo>) / quality-gates` **and** `Quality Gates (<repo>) / quality-gates-v2`
  (both appear — the reusable job was renamed `quality-gates` → `quality-gates-v2`
  mid-migration; old PRs carry the old suffix, recent ones the new).
- Staging-lock check: bare `check-staging-lock` (stable; the workflow's display
  name `Staging Lock Check` is NOT part of the recorded context).

### Root causes

1. **In-flight `ci_canonical_v2_migration`** (Phase 4 bootstrap `quality-gates-v2.yml`,
   Phase 5 delete v1) is actively landing on repos. The QG check-run name is still
   moving (`/ quality-gates` → `/ quality-gates-v2`), so there is no stable target
   to point the rulesets at until it settles.
2. **Bootstrap name bug**: the Phase-4 bootstrap renders every repo's
   `quality-gates-v2.yml` job with **`name: Quality Gates (alerting-service)`** hardcoded
   instead of substituting the repo name. Confirmed on features-service: PR commit
   `8f517193` re-introduced `name: Quality Gates (alerting-service)`. So those repos
   emit a check literally named for alerting-service, which no per-repo ruleset can match.
3. **Rulesets were never updated** as the workflow check names changed (and the
   `Staging Lock Check / check-staging-lock` → `check-staging-lock` rename). They are
   stale snapshots from various points in the migration. There is **no IaC** managing
   these rulesets (set up manually via the GitHub API), so they don't self-heal.

## Why it matters

- Manual PRs to `staging`/`main` cannot merge across ~17 repos → everything is forced
  through the `workspace-sweep: live-defi-rollout → staging` job or admin override.
  This already blocked a normal promotion (alerting-service PR #17, 2026-05-30).
- The gates are effectively non-enforcing in spirit (un-satisfiable), so QG/staging-lock
  protection is not doing its job on the PR path.

## Already done (this session)

- **alerting-service** `require-staging-lock-check` (id 13788730) corrected to
  `["Quality Gates (alerting-service) / quality-gates", "check-staging-lock"]` — the
  only ruleset edited. NOTE: this may need re-alignment to `/ quality-gates-v2` once the
  migration settles (the QG suffix is still moving). Its `require-quality-gates` (main,
  id 13787630) is still stale (`quality-gates-v2`).
- No other rulesets changed; a manual fix to features-service's hardcoded name was
  **abandoned** (it collided with the active migration's Phase-4 bootstrap, which
  re-introduces the bug — the fix belongs in the bootstrap generator, not the rendered file).

## Recommended decision (owner: ci_canonical_v2_migration)

Do this as the **final step of the v2 migration**, not piecemeal now:

1. **Fix the Phase-4 bootstrap** so the `quality-gates-v2.yml` job `name:` substitutes
   the repo name (`Quality Gates (<repo>)`) instead of hardcoding `alerting-service`.
   Re-render all repos. (This is the "template name bug".)
2. **Settle the QG check name** (`/ quality-gates` vs `/ quality-gates-v2`) — pick the
   canonical v2 name and finish deleting v1 so only one QG check-run name is emitted.
3. **Align all rulesets** to the final stable contexts, fleet-wide:
   - `require-quality-gates` (main) → `["Quality Gates (<repo>) / <final-qg-job>"]`
   - `require-staging-lock-check` (staging) → `["Quality Gates (<repo>) / <final-qg-job>", "check-staging-lock"]`
   Use each repo's actual emitted check-run name (not assumptions). A small script that
   PUTs the corrected `required_status_checks` per repo via `gh api` is sufficient
   (~34 rulesets). **Codify it** (commit the script / IaC) so the rulesets stop drifting
   when workflow names change again.
4. Re-align alerting-service's already-edited staging ruleset to the final name in the
   same pass.

## Appendix — per-repo ruleset IDs + current required contexts (observed 2026-05-30)

| repo | main `require-quality-gates` (id / required) | staging `require-staging-lock-check` (id / required) |
| --- | --- | --- |
| alerting-service | 13787630 / `quality-gates-v2` | 13788730 / `Quality Gates (alerting-service) / quality-gates`, `check-staging-lock` (already edited) |
| batch-live-reconciliation-service | 13787691 / `quality-gates-v2` | 13788766 / `quality-gates`, `Staging Lock Check / check-staging-lock` |
| client-reporting-api | 13787647 / `quality-gates-v2` | 13788738 / `quality-gates`, `Staging Lock Check / check-staging-lock` |
| deployment-api | 13787655 / `quality-gates-v2` | 13788743 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| deployment-service | 13787653 / `quality-gates-v2` | 13788742 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| deployment-ui | 13787657 / `check-staging-lock`, `quality-gates-v2` | 13788744 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| execution-service | 13647462 / `check-staging-lock`, `quality-gates-v2` | 13788729 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| ibkr-gateway-infra | 13787650 / `quality-gates-v2` | 13788741 / `quality-gates`, `Staging Lock Check / check-staging-lock` |
| instruments-service | 13787597 / `check-staging-lock`, `quality-gates-v2` | 13788713 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| market-data-processing-service | 13787601 / `quality-gates-v2` | 13788715 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| market-tick-data-service | 13787599 / `check-staging-lock` | 13788714 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| strategy-service | 13787628 / `check-staging-lock` | 13788728 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| system-integration-tests | 13787666 / `quality-gates-v2` | 13788747 / `quality-gates`, `Staging Lock Check / check-staging-lock` |
| trading-agent-service | 13787685 / `quality-gates-v2` | 13788761 / `quality-gates`, `Staging Lock Check / check-staging-lock` |
| unified-api-contracts | 13787580 / `quality-gates-v2` | 13788676 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| unified-trading-library | 13787584 / `quality-gates-v2` | 13788697 / `check-staging-lock`, `call-quality-gates / quality-gates` |
| unified-trading-pm | 13647441 / `quality-gates-v2` | (no staging ruleset) |

Repos with no branch rulesets (not affected): agent-orchestrator, e2e-testing,
features-service, fund-administration-service, greeks-service, ml-service,
unified-trading-api, unified-trading-system-ui.
