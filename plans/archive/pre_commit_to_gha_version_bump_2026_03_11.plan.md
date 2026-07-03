---
doc_type: plan
title: pre-commit-to-gha-version-bump
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
superseded_note: 'PARTIALLY SUPERSEDED 2026-03-13. The hook removal (rollout-remove-bump-library-version-hook) is complete

  and correct — stays done. The staging-to-main cascade fix (pm-changes-staging-to-main-cascade) is also

  still valid. What is superseded: the assumption that version-bump.yml on main is the fallback for direct

  fix:/feat: commits. New design: there are no direct fix:/feat: commits to main — everything goes through

  staging. version-bump.yml remains disabled (if: false). semver-agent.yml is the sole bumper and fires

  on staging. See full_autonomous_agent_ci todo: fix-semver-agent-template-staging-trigger.

  '
overview: Remove the local bump-library-version pre-commit hook from all 65 repos (it caused PATCH double-bumps before the GHA MINOR/MAJOR bump fired) and fix staging-to-main.yml to dispatch the dependency-update cascade after staging→main promotion (previously the cascade never fired because version-bump.yml skips chore(release) merge commits).
type: infra
epic: epic-infra
completion_gates: {code: C3, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: CI tooling — no cloud deployment required. BR N/A: internal.'}
depends_on: []
todos:
- {id: pm-changes-staging-to-main-cascade, content: 'Fix staging-to-main.yml to dispatch dependency-update cascade for promoted repos: capture PROMOTED_JSON (old→new versions) before clearing staging_versions, then dispatch dependency-update to all downstream dependents with correct bump_type. Also add rollout-remove-version-bump-hook.sh script to PM.', status: completed, notes: 'RESOLVED 2026-03-11: commit d424c32 in unified-trading-pm. Captures PROMOTED_JSON in Promote step, new cascade step dispatches dependency-update per promoted repo.'}
- {id: rollout-remove-bump-library-version-hook, content: 'Run bash unified-trading-pm/scripts/rollout-remove-version-bump-hook.sh across all 65 repos to remove the local bump-library-version pre-commit hook and delete scripts/bump-library-version.sh. The GHA version-bump.yml is the sole authoritative version bumper. Local hook caused incorrect PATCH pre-bumps on feature branches and a double-bump when the GHA MINOR/MAJOR bump then fired on squash-merge to main. Run --dry-run first to confirm scope, then run without flag.', status: completed, notes: 'RESOLVED 2026-03-11: 18 repos changed (49 already absent), 0 failed. Each repo committed with [skip ci]. Repos changed: execution-algo-library, instruments-service, matching-engine-library, unified-api-contracts, unified-cloud-interface, unified-config-interface, unified-defi-execution-interface, unified-domain-client, unified-events-interface, unified-internal-contracts, unified-market-interface, unified-ml-interface, unified-position-interface,
    unified-reference-data-interface, unified-sports-execution-interface, unified-trade-execution-interface, unified-trading-library, unified-trading-ui-auth.'}
isProject: false
---

# Pre-commit → GHA Version Bump Migration

**Problem:** Two version-bump sources conflicted:

1. `bump-library-version.sh` (local pre-commit hook) — always bumped PATCH on any code change, before commit. Ran on
   developer machines only (not on staging→main auto-merges).
2. `version-bump.yml` (GHA, post-merge to main) — correctly parsed `feat:`/`fix:`/`feat!:` commit messages and bumped
   MINOR/PATCH/MAJOR.

For a `feat:` commit: hook bumped `0.5.2→0.5.3` (PATCH), then GHA bumped `0.5.3→0.6.0` (MINOR) — **double bump**.
Feature branches showed wrong in-between versions.

**Second bug:** `staging-to-main.yml` used `--merge` (not `--squash`) for staging→main PRs, so the head commit message
was `"chore(release): promote staging to main"`. `version-bump.yml` saw no `feat:`/`fix:` prefix → `SKIP=true` → no
dispatch to PM → **dependency-update cascade never fired** after staging promotions. Downstream repos never received
updated constraints.

## Fix

- `staging-to-main.yml`: captures `PROMOTED_JSON` before clearing `staging_versions`, new cascade step dispatches
  `dependency-update` to all dependents with correct `bump_type`.
- All 65 repos: remove `bump-library-version` hook → `version-bump.yml` GHA is canonical.

## What Stays

- Local pre-commit hooks for **formatting only**: `ruff`, `ruff-format`, `prettier`, `conventional-pre-commit`, file
  hygiene. These remain as developer ergonomics.
- `version-bump.yml` remains the authoritative bumper until `semver-agent.yml` rollout replaces it (see
  `full_autonomous_agent_ci` plan todo `rollout-semver-agent-yml-replacing-version-bump`).
