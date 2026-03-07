---
name: Version Cascade Rollout — Automated Cross-Repo Version Pinning
overview: |
  Roll out the full automated version cascade system to all 59 workspace repos.
  When any repo merges feat:/fix: to main, the cascade automatically:
    1. Bumps the repo's own pyproject.toml version
    2. Dispatches to unified-trading-pm → updates workspace-manifest.json + bumps PM version
    3. PM dispatches dependency-update to all direct dependents → each updates their pyproject.toml pin
  All cross-repo dispatches use the existing GH_PAT secret (already in workspace).
  Locally: uv.sources path deps always use latest. In CI: constraints ensure correct minimum.
todos:
  - id: vc-vb-rollout
    content:
      "Propagate canonical version-bump.yml to all 58 non-PM repos: adds dispatch step + uses GH_PAT + dynamic repo
      name. Run: python3 scripts/propagation/rollout-version-bump-workflow.py. Then quickmerge each repo (parallel
      agents, one per tier batch)."
    status: in_progress

  - id: vc-dep-rollout
    content:
      "Propagate update-dependency-version.yml to all 37 repos with dependencies. Run: python3
      scripts/propagation/rollout-dependency-update-workflow.py. Then quickmerge each repo (parallel agents)."
    status: in_progress

  - id: vc-ibkr-vb
    content:
      "Add version-bump.yml to ibkr-gateway-infra (the one repo missing it). Part of vc-vb-rollout but flag separately
      as it requires creating .github/workflows/ dir."
    status: in_progress

  - id: vc-pm-merge
    content:
      "Quickmerge unified-trading-pm with: updated update-repo-version.yml (GH_PAT), version-bump.yml template,
      update-dependency-version.yml template, rollout-version-bump-workflow.py, rollout-dependency-update-workflow.py,
      this plan."
    status: done

  - id: vc-pre-existing-blockers
    content: |
      Pre-existing issues discovered during rollout that block quickmerge in those repos (unrelated to cascade rollout):
      SKIP — needs code fix first:
        - unified-defi-execution-interface: import smoke test fails (uv pip install -e . needed)
        - unified-feature-calculator-library: 43% test coverage (needs tests for base.py, time_series.py, onchain.py, validations.py)
      UI repos with pre-commit YAML parse errors (.pre-commit-config.yaml line 12/13):
        - batch-audit-ui, onboarding-ui, settlement-ui, execution-analytics-ui
      UI repos with broken TypeScript/test setup:
        - live-health-monitor-ui (missing src modules), client-reporting-ui (missing recharts)
        - trading-analytics-ui (no test files), logs-dashboard-ui (OAuth in tests), ml-training-ui (playwright conflict)
        - strategy-ui (npm script name mismatch: typecheck vs type-check)
      Workflow files ARE written to disk in all these repos. Will commit once underlying issues fixed.
    status: todo

  - id: vc-verify
    content:
      "After all rollouts: merge a fix: commit in UAC and verify the full cascade fires — UAC bumps, PM manifest
      updates, dependent repos get pyproject.toml updated."
    status: todo
isProject: false
---

# Version Cascade Rollout

**Scope:** All 59 workspace repos **Prereq:** `GH_PAT` secret must exist in every repo (already present in workspace —
used by quickmerge) **Blocks:** Nothing currently blocked; enables automation of dependency_governance.plan.md

## How It Works

```
feat:/fix: → main (any repo)
  └─ version-bump.yml: bumps pyproject.toml, dispatches version-bump to PM (via GH_PAT)

PM receives dispatch → update-repo-version.yml:
  ├─ updates workspace-manifest.json[versions][repo] = new_version
  ├─ bumps PM's own pyproject.toml patch version
  └─ dispatches dependency-update to all direct dependents (via GH_PAT)

Each dependent → update-dependency-version.yml:
  └─ updates pyproject.toml dep constraint, commits [skip ci]
```

## Cascades Are Bounded

- `[skip ci]` on all auto-commits prevents re-triggering version-bump
- Only direct dependents are notified (no transitive fan-out)
- Constraint format: `>=MAJOR.MINOR.0,<MAJOR+1.0.0` (same major range, updated minor floor)

## Templates (canonical, managed in PM)

| Template                                                      | Purpose                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------- |
| `scripts/propagation/templates/version-bump.yml`              | Runs on push to main; bumps + dispatches to PM          |
| `scripts/propagation/templates/update-dependency-version.yml` | Runs on repository_dispatch; updates pyproject.toml pin |

## Rollout Scripts

| Script                                                      | Target                            |
| ----------------------------------------------------------- | --------------------------------- |
| `scripts/propagation/rollout-version-bump-workflow.py`      | 58 non-PM repos (all in manifest) |
| `scripts/propagation/rollout-dependency-update-workflow.py` | 37 repos with dependencies        |

## Repo Batches for Parallel Quickmerge

### Batch 1 — T0 Libraries (6 repos, no deps)

unified-api-contracts, unified-internal-contracts, unified-cloud-interface, unified-events-interface,
execution-algo-library, matching-engine-library

### Batch 2 — T1 Libraries (3 repos)

unified-reference-data-interface, unified-config-interface, unified-trading-library

### Batch 3 — T2 Libraries + T3 (8 repos)

unified-market-interface, unified-ml-interface, unified-trade-execution-interface, unified-sports-execution-interface,
unified-defi-execution-interface, unified-position-interface, unified-feature-calculator-library, unified-domain-client

### Batch 4 — Services Batch A (9 repos)

instruments-service, market-tick-data-service, market-data-processing-service, features-calendar-service,
features-delta-one-service, features-volatility-service, features-onchain-service, features-sports-service,
features-multi-timeframe-service

### Batch 5 — Services Batch B (9 repos)

features-cross-instrument-service, ml-training-service, ml-inference-service, strategy-service, execution-service,
alerting-service, pnl-attribution-service, position-balance-monitor-service, risk-and-exposure-service

### Batch 6 — APIs, UIs, Infra (11 repos)

strategy-validation-service, execution-results-api, market-data-api, client-reporting-api, deployment-service,
deployment-api, deployment-ui, system-integration-tests, ibkr-gateway-infra, unified-trading-codex, strategy-ui +
remaining UIs

### Batch 7 — UI-only repos (no pyproject.toml — version-bump only, no dep-update)

batch-audit-ui, trading-analytics-ui, live-health-monitor-ui, client-reporting-ui, logs-dashboard-ui, onboarding-ui,
settlement-ui, unified-trading-ui-auth, execution-analytics-ui, ml-training-ui
