---
doc_type: issue
title: deployment-ui unit-coverage floor RED (pre-existing, blocks unrelated shipping)
summary:
  deployment-ui's `quality-gates.sh` unit-test coverage step fails the global 70%/67%/70%/64%
  (lines/functions/statements/branches) threshold at ~24-25% actual, on a clean tree with zero relation to the change
  being shipped (a script-lifecycle-marker comment-only stamp). Confirmed pre-existing via stash+clean-tree reproduction
  (byte-identical failure percentages).
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [coverage, quality-gates, deployment-ui, repo-blocker]
related: []
created: 2026-07-31
parent_epic: deployment_and_user_management_master
priority: P2
source: [features_service_coverage_and_script_canon_2026_06_10.md script-canon sweep, slot 10 session 2026-07-31]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

While shipping a purely mechanical change (adding the required `# Epic:`/`# Lifecycle:`/`# Delete-when:`
lifecycle-marker header to 4 `deployment-ui/scripts/*.sh` files, per `/codex/06-coding-standards/script-homes.md` —
`scripts/` is explicitly excluded from coverage by design), `bash scripts/quality-gates.sh` failed at the unit-test
coverage step:

```
Statements   : 24.42% ( 693/2837 )
Branches     : 16.16% ( 401/2480 )
Functions    : 22.58% ( 168/744 )
Lines        : 25.11% ( 634/2524 )
ERROR: Coverage for lines (25.11%) does not meet global threshold (70%)
ERROR: Coverage for functions (22.58%) does not meet global threshold (67%)
ERROR: Coverage for statements (24.42%) does not meet global threshold (70%)
ERROR: Coverage for branches (16.16%) does not meet global threshold (64%)
```

Verified pre-existing (not caused by this session's diff) per the RULES.md § 4b protocol:
`git stash push --include-untracked`, re-ran `npx vitest run --coverage` on the clean tree at `origin/live-defi-rollout`
HEAD — reproduced the same failure, coverage numbers within noise (24.39/16.16/22.44/25.11 vs 24.42/16.16/22.58/25.11 —
floating test-order variance, not a real diff). `git stash pop` restored my diff afterward.

The gap between actual (~24%) and the 70% floor is large and structural — this reads as a repo where the coverage floor
was set (or inherited from the shared `base-ui.sh` default) without the test suite actually reaching it, not a fresh
regression. The QG script's own `CODEX_*_EXCLUDE_GLOBS` comments already document several other "pre-existing"
accepted-debt exclusions for this repo (hardcoded-colour / console.\* / localhost-URL globs), consistent with
deployment-ui carrying known, already-tolerated gaps elsewhere.

## Why it matters

Every future commit to `deployment-ui` — regardless of content — currently fails the mandatory
`quality-gates.sh`-green-tree-before-commit HARD RULE, because Pass 1 QG cannot pass. This blocks ALL shipping through
the sanctioned two-pass flow, not just this session's script-marker change.

## Recommended decision

Either (a) raise `deployment-ui`'s real unit-test coverage to the shared floor over time (large effort — ~45pp gap
across 4 dimensions), or (b) if the shared 70/67/70/64 floor was never meant to apply to this repo as-is, set a
repo-specific `MIN_COVERAGE_*` override in `deployment-ui/scripts/quality-gates.sh` (mirroring the pattern already used
for the `CODEX_*_EXCLUDE_GLOBS`) with a comment citing this issue, then track closing that gap as its own follow-up.
Either path needs an owner decision on target coverage — filing as a real backlog todo below rather than deciding
unilaterally.

- [ ] [BACKEND] P2. deployment-ui: decide + implement the coverage-floor fix (raise real coverage OR set a documented
      repo-specific override in `scripts/quality-gates.sh`), citing this issue doc. Repo: deployment-ui.
