---
scope: [engineer, admin]
---

# Dependency Cascade

**SSOT:** `unified-trading-pm/.github/workflows/cascade-qg-ordering.yml` (orchestrator),
`unified-trading-pm/scripts/cascade/invalidate-ci-status.py` (invalidation),
`unified-trading-pm/.github/workflows/downstream-fix-agent.yml` (auto-fix)

---

## Overview

When a breaking change lands on staging, the dependency cascade ensures all affected downstream repos are validated,
fixed if possible, and promoted — or explicitly invalidated if they can't be fixed automatically.

The cascade is **topological**: it processes repos in dependency order (T0 → T1 → T2 → T3 → services → UIs), failing
fast when a tier has failures.

## Cascade Flow

```mermaid
graph TD
    A[Breaking change merged to staging] --> B[semver-agent bumps version]
    B --> C[update-repo-version.yml dispatches dependency-update]
    C --> D{is_breaking=true?}
    D -->|No| E[Direct commit with skip ci]
    D -->|Yes| F[cascade-qg-ordering.yml fires]
    F --> G[Level 0: Run QG on direct dependents]
    G --> H{All pass?}
    H -->|Yes| I[Level 1: Run QG on 2nd-degree dependents]
    H -->|No| J[invalidate-ci-status.py: set STAGING_PENDING on all downstream]
    I --> K{All pass?}
    K -->|Yes| L[Continue to next level...]
    K -->|No| J
    J --> M[downstream-fix-agent.yml fires for each failure]
    M --> N{Claude fix + QG pass?}
    N -->|Yes| O[PR + Issue created, await /approve]
    N -->|No| P[Issue only, Telegram CRITICAL]
    L --> Q[All levels pass → SIT gate opens]
    O --> R[Human /approve → PR merges → re-run QG]
```

## Concurrency + manifest-write safety (codified 2026-06-10)

`cascade-qg-ordering.yml` runs in its **own** `concurrency.group: cascade-qg-ordering` with `cancel-in-progress: false`
(serialise cascades, never kill a running one). It must **NEVER share the high-frequency `manifest-update` group**:
GitHub holds only ONE pending run per concurrency group, so group-sharing evicted every queued cascade before it
executed — live evidence 2026-06-10: run 27264972415 (UTL 0.5.0 breaking cascade) cancelled in 4s with 0 jobs, and ALL
prior cascade runs had been cancelled the same way (the cascade had never executed a level live). Fixed PM@b6576fc27.
The manifest-write-loss concern (finding H2) that motivated the sharing is handled **in-code** by the workflow's
retry-with-rebase manifest push step, not by concurrency-group serialisation — group-sharing was redundant for safety
and fatal for liveness.

## Topological Fail-Fast Algorithm

1. Read `topologicalOrder.levels` from workspace-manifest.json
2. Find all repos that transitively depend on the changed repo
3. Group affected repos by their topological level
4. For each level (ascending):
   - Dispatch QG to all repos in the level (parallel within level)
   - Wait for completion (poll ci_status, 15min timeout per level)
   - If ANY repo fails: invalidate all subsequent levels → exit
   - If all pass: proceed to next level
5. All levels pass → SIT gate opens

### PM Special Case

PM and codex are "universal dependencies" — everything depends on them. When PM/codex has a breaking change:

- Run QG tier-by-tier: T0 (parallel) → T1 (parallel) → T2 → T3 → services → UIs
- Stop at first tier with any failure
- This is the same algorithm but with all repos as affected

## ci_status Invalidation

When a repo fails QG after a breaking update, `invalidate-ci-status.py` walks the manifest DAG forward from the failed
repo and sets all transitive dependents to `STAGING_PENDING`. This prevents stale green status on repos that haven't
been tested against the breaking change.

```
Failed repo X
  → X's direct dependents: set STAGING_PENDING
    → Their dependents: set STAGING_PENDING
      → ... (full transitive closure)
```

Uses `fcntl.flock` on `.workspace-manifest.lock` for safe concurrent writes.

## Autonomous Fix Agent

When a downstream repo's QG fails after a breaking dependency update:

1. Clone: target repo + breaking repo + PM + codex
2. Inject mandatory rules via `inject-mandatory-rules.sh`
3. Build prompt: breaking repo diff + QG failure output + target repo imports
4. Claude fixes code (renamed imports, removed APIs, changed signatures)
5. Validate: files exist, no merge markers, Python/TS syntax valid
6. Run QG (advisory)
7. If QG passes: PR + Issue + Telegram ("approve to merge")
8. If QG fails: Issue only + Telegram CRITICAL ("needs human")

**Agent NEVER self-merges.** Human comments `/approve` on the Issue.

### Approval Timeout Escalation

- 4h without `/approve`: Telegram WARNING
- 24h without `/approve`: Telegram CRITICAL
- For crypto 24/7: prevents fixes from sitting unreviewed while markets are live

### Auto-Merge Path (Non-Breaking Only)

For non-breaking dependency updates (is_breaking=false) where:

- QG passes
- SIT validates
- Repo is at 1.0.0+ (pre-1.0.0 always requires human approval)

The PR auto-merges without human intervention. MAJOR/breaking fixes always require `/approve`.

## Breaking Change Detection (Pre-1.0.0)

All repos are <1.0.0. Per semver, `feat!:` bumps MINOR (not MAJOR). **Since 2026-06-08, `is_breaking` is
CONTENT-based**: the verdict of the AST public-surface differ `scripts/cicd/detect_breaking_change.py` (removed/renamed
public export, incompatible signature, removed/renamed/retyped schema field, removed HTTP route = breaking;
additive/docstring/internal-refactor = NOT) — see `ci-cd-flow.md` § "Breaking = public-surface change". `feat!:` stays
an explicit human-declared breaking override; the commit type alone no longer determines `is_breaking`:

| Commit Type         | Pre-1.0.0 Bump | is_breaking                                              | Route                                                         |
| ------------------- | -------------- | -------------------------------------------------------- | ------------------------------------------------------------- |
| `fix:`              | PATCH          | differ verdict (typically false)                         | Direct commit, [skip ci]                                      |
| `feat:`             | MINOR          | differ verdict (false unless real public-surface change) | Direct commit, [skip ci] when false; PR path + lock when true |
| `feat!:`            | MINOR          | true (explicit override)                                 | PR path, staging lock, QG forced                              |
| Post-1.0.0 `feat!:` | MAJOR          | true                                                     | PR path, staging lock, approval issue                         |

## Dependency Caps

Repos can pin to old versions while fixing code:

```json
"dependency_caps": {
  "market-tick-data-service/market_tick_data_service/market_interface": "<0.3.0"
}
```

When a capped repo receives a breaking update, the constraint update is skipped. `run-version-alignment.sh` flags capped
repos as "pinned to old version — update needed."

## Reverse Dependency Sync

When T0 libraries (UAC, UIC, UEI, UCI, UTL, instruments-service) change schemas:

1. semver-agent dispatches `schema-changed` to PM
2. PM `schema-changed-handler.yml` clones the changed repo, reads the diff
3. Checks if cursor-rules or codex docs reference changed symbols
4. If yes: dispatches to rules-alignment-agent and codex-sync-agent
5. Agents update docs/rules to match new schema

This ensures documentation stays in sync with code without requiring PM/codex to be listed as formal dependents.

## Key Files

| File                                      | Purpose                           |
| ----------------------------------------- | --------------------------------- |
| `cascade-qg-ordering.yml`                 | Topological QG orchestrator       |
| `scripts/cascade/invalidate-ci-status.py` | Transitive ci_status invalidation |
| `downstream-fix-agent.yml`                | Claude-powered auto-fix           |
| `fix-approval-timeout.yml`                | 4h/24h escalation                 |
| `auto-merge-minor-fixes.yml`              | Non-breaking auto-merge           |
| `schema-changed-handler.yml`              | Reverse dep sync trigger          |
| `update-repo-version.yml`                 | Version cascade dispatcher        |
| `update-dependency-version.yml`           | Per-repo dep constraint updater   |
