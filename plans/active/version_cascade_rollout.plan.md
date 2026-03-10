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
    status: done
    notes: |
      RESOLVED 2026-03-10: All 58 manifest repos already had version-bump.yml (UP-TO-DATE). After adding
      ml-inference-api, ml-training-api, trading-analytics-api to manifest (now 62 repos total), rollout script
      wrote version-bump.yml to all 3 new repos (committed bdb5f0f, 69ba6b9, a4eb327). Total: 62 version-bump.yml
      files across workspace, all YAML-valid.

  - id: vc-dep-rollout
    content:
      "Propagate update-dependency-version.yml to all 37 repos with dependencies. Run: python3
      scripts/propagation/rollout-dependency-update-workflow.py. Then quickmerge each repo (parallel agents)."
    status: done
    notes: |
      RESOLVED 2026-03-10: 38 repos already had update-dependency-version.yml. Script wrote to 3 previously missing
      repos (execution-results-api d4668cc, market-data-api already had it, client-reporting-api dfe1f2e) and 3
      new repos (ml-inference-api, ml-training-api, trading-analytics-api). Total: 47 update-dependency-version.yml
      files. All YAML-valid. 44 repos with dependencies now covered (3 new repos added to manifest).

  - id: vc-ibkr-vb
    content:
      "Add version-bump.yml to ibkr-gateway-infra (the one repo missing it). Part of vc-vb-rollout but flag separately
      as it requires creating .github/workflows/ dir."
    status: done
    notes: |
      RESOLVED 2026-03-09: version-bump.yml already committed to ibkr-gateway-infra in admin force-sync
      (commit 407c9f5). Verified: .github/workflows/version-bump.yml exists with correct GH_PAT dispatch step.

  - id: vc-pm-merge
    content:
      "Quickmerge unified-trading-pm with: updated update-repo-version.yml (GH_PAT), version-bump.yml template,
      update-dependency-version.yml template, rollout-version-bump-workflow.py, rollout-dependency-update-workflow.py,
      this plan."
    status: done

  - id: vc-pre-existing-blockers
    content: |
      Pre-existing issues discovered during rollout that block quickmerge in those repos (unrelated to cascade rollout):

      FIXED (2026-03-09):
        - unified-defi-execution-interface: basedpyright 78 errors resolved by adding ../unified-api-contracts to
          pyrightconfig.json extraPaths → 0 errors. Committed 3943161.
        - onboarding-ui: .pre-commit-config.yaml eslint hook now excludes .eslintrc.cjs (was causing
          "File ignored by default" warning → hook failure). Committed 598c31e.
        - settlement-ui: cloudbuild.yaml YAML parse error (python3 -c inline script at col 0 broke block scalar) —
          already fixed in prior admin force-sync a4d2429.
        - batch-audit-ui: pre-commit passes cleanly (trailing-whitespace/EOF auto-fixed in prior sync).
        - execution-analytics-ui: pre-commit passes cleanly (EOF auto-fixed in prior sync).
        - strategy-ui: no actual mismatch — package.json has BOTH typecheck and type-check scripts;
          pre-commit config does not reference either. Pre-commit passes cleanly.

      STILL BLOCKED — needs further work:
        - unified-feature-calculator-library: RESOLVED 2026-03-09 — version bumped to 0.2.0; 240 tests pass;
          MIN_COVERAGE=93 confirmed passing (commit 9721c16). No longer a blocker.
        - live-health-monitor-ui: missing src modules
        - client-reporting-ui: missing recharts dependency (VERIFIED resolved — recharts in package.json)
        - trading-analytics-ui: no test files (has tests/ dir and src/)
        - logs-dashboard-ui: OAuth in tests
        - ml-training-ui: playwright conflict
    status: in_progress

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
