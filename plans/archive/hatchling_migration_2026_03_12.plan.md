---
doc_type: plan
title: hatchling-migration
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [batch-live-reconciliation-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-12'
overview: Migrate all repos from setuptools to hatchling build backend for clean uv editable installs
type: code
epic: none
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-library, code: C2, deployment: none, business: none}
- {repo: unified-cloud-interface, code: C2, deployment: none, business: none}
- {repo: unified-config-interface, code: C2, deployment: none, business: none}
- {repo: unified-events-interface, code: C2, deployment: none, business: none}
- {repo: unified-domain-client, code: C2, deployment: none, business: none}
- {repo: unified-api-contracts, code: C2, deployment: none, business: none}
- {repo: unified-internal-contracts, code: C2, deployment: none, business: none}
- {repo: unified-market-interface, code: C2, deployment: none, business: none}
- {repo: unified-trade-execution-interface, code: C2, deployment: none, business: none}
- {repo: unified-defi-execution-interface, code: C2, deployment: none, business: none}
- {repo: unified-sports-execution-interface, code: C2, deployment: none, business: none}
- {repo: unified-ml-interface, code: C2, deployment: none, business: none}
- {repo: unified-position-interface, code: C2, deployment: none, business: none}
- {repo: unified-reference-data-interface, code: C2, deployment: none, business: none}
- {repo: unified-feature-calculator-library, code: C2, deployment: none, business: none}
- {repo: matching-engine-library, code: C2, deployment: none, business: none}
- {repo: execution-algo-library, code: C2, deployment: none, business: none}
- {repo: execution-service, code: C2, deployment: none, business: none}
- {repo: alerting-service, code: C2, deployment: none, business: none}
- {repo: risk-and-exposure-service, code: C2, deployment: none, business: none}
- {repo: strategy-service, code: C2, deployment: none, business: none}
- {repo: strategy-validation-service, code: C2, deployment: none, business: none}
- {repo: trading-agent-service, code: C2, deployment: none, business: none}
- {repo: pnl-attribution-service, code: C2, deployment: none, business: none}
- {repo: instruments-service, code: C2, deployment: none, business: none}
- {repo: market-data-processing-service, code: C2, deployment: none, business: none}
- {repo: features-volatility-service, code: C2, deployment: none, business: none}
- {repo: features-multi-timeframe-service, code: C2, deployment: none, business: none}
- {repo: features-calendar-service, code: C2, deployment: none, business: none}
- {repo: features-onchain-service, code: C2, deployment: none, business: none}
- {repo: features-cross-instrument-service, code: C2, deployment: none, business: none}
- {repo: features-delta-one-service, code: C2, deployment: none, business: none}
- {repo: features-sports-service, code: C2, deployment: none, business: none}
- {repo: features-commodity-service, code: C2, deployment: none, business: none}
- {repo: ml-training-service, code: C2, deployment: none, business: none}
- {repo: ml-inference-service, code: C2, deployment: none, business: none}
- {repo: ml-inference-api, code: C2, deployment: none, business: none}
- {repo: ml-training-api, code: C2, deployment: none, business: none}
- {repo: market-data-api, code: C2, deployment: none, business: none}
- {repo: market-tick-data-service, code: C2, deployment: none, business: none}
- {repo: client-reporting-api, code: C2, deployment: none, business: none}
- {repo: trading-analytics-api, code: C2, deployment: none, business: none}
- {repo: execution-results-api, code: C2, deployment: none, business: none}
- {repo: deployment-service, code: C2, deployment: none, business: none}
- {repo: deployment-api, code: C2, deployment: none, business: none}
- {repo: position-balance-monitor-service, code: C2, deployment: none, business: none}
- {repo: ibkr-gateway-infra, code: C2, deployment: none, business: none}
depends_on: []
isProject: false
todos:
- {id: batch-1-t0-libraries, description: 'Migrate T0 libraries: unified-trading-library, unified-cloud-interface, unified-config-interface, unified-events-interface, unified-domain-client', status: done}
- {id: batch-2-interfaces, description: 'Migrate interfaces: unified-api-contracts, unified-internal-contracts, unified-market-interface, unified-trade-execution-interface, unified-defi-execution-interface, unified-sports-execution-interface, unified-ml-interface, unified-position-interface, unified-reference-data-interface', status: done}
- {id: batch-3-libraries-data, description: 'Migrate libs + data: unified-feature-calculator-library (src layout), matching-engine-library, execution-algo-library, instruments-service, market-data-processing-service', status: done}
- {id: batch-4-execution-trading, description: 'Migrate execution/trading/risk: execution-service, alerting-service, risk-and-exposure-service, strategy-service, strategy-validation-service, trading-agent-service, pnl-attribution-service', status: done}
- {id: batch-5-features-ml, description: 'Migrate features + ML: features-volatility/multi-timeframe/calendar/onchain/cross-instrument/delta-one/sports/commodity, ml-training-service, ml-inference-service', status: done}
- {id: batch-6-apis-infra, description: 'Migrate APIs + infra: ml-inference-api, ml-training-api, market-data-api, market-tick-data-service, client-reporting-api, trading-analytics-api, execution-results-api, deployment-service, deployment-api, position-balance-monitor-service, ibkr-gateway-infra', status: done}
---

# Hatchling Migration

## Motivation

Hatchling is strictly better than setuptools for uv-managed editable sibling repos:

1. **No `*.egg-info/` in source tree** — nothing to go stale, nothing to accidentally commit
2. **Pure `pyproject.toml` metadata** — `uv lock` reads metadata via `prepare_metadata_for_build_wheel` hook, never
   falls back to stale egg-info
3. **Simpler import mechanism** — direct sys.path entry vs setuptools' MetaPathFinder
4. **Zero config for standard layouts** — eliminates `[tool.setuptools.packages.find]` boilerplate

## Scope

47 repos migrated from `setuptools.build_meta` → `hatchling.build`. Already on hatchling (excluded):

- `batch-audit-api`, `batch-live-reconciliation-service`, `elysium-defi-system`

## Migration Rules Per Repo

### Standard layout (most repos)

```toml
# BEFORE
[build-system]
requires = ["setuptools>=75,<82"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]

# AFTER
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
# remove [tool.setuptools.*] entirely
```

### src layout (`unified-feature-calculator-library` only)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/unified_feature_calculator_library"]
```

### setuptools-scm repos (`strategy-validation-service`, `unified-sports-execution-interface`)

Drop `setuptools-scm>=8` from `requires` — both repos already have static `version =` in `[project]`.

### Data files (py.typed, _.json, _.yaml)

Hatchling auto-includes ALL files in discovered package directories — no `[tool.hatch.build.targets.wheel.include]`
needed.

## Commit Convention

`chore: migrate build backend from setuptools to hatchling` per repo
