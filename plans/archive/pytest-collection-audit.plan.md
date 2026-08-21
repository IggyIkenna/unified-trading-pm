---
doc_type: plan
title: Pytest Collection Audit
summary: 'Ensure all Python repos pass pytest --collect-only -q for audit readiness.

  Scope: all 60+ Python repos in the unified-trading-system workspace.

  Root causes: missing path deps in workspace venv, import path changes from schema migrations.

  Fix checklist: workspace venv bootstrap, per-repo import fixes, pyproject.toml constraint updates.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, deployment-service, deployment-ui, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-05'
todos: []
isProject: false
---

# Pytest Collection Audit Plan

**Purpose:** Ensure all Python repos pass `pytest --collect-only -q` for audit readiness.

**Scope:** All 60+ Python repos in the unified-trading-system workspace.

**Status:** Complete (core repos)

---

## Root Causes

Collection failures typically stem from:

1. **Missing path deps in workspace venv** — `unified-internal-contracts`, `unified-api-contracts`, and other sibling
   libs not installed via `uv pip install -e <path-dep>` in `.venv-workspace`. Sub-agents and isolated runs often lack
   these deps.
2. **Import path changes** — Schema/package reorgs (e.g. `unified_api_contracts.sports` →
   `unified_api_contracts_external.sports`) break existing imports. Must align with external-import-standards (top-level
   imports only).
3. **Schema migrations** — `InstrumentDefinition` and other types moved between `unified-api-contracts` and
   `unified-internal-contracts`. Consumers must update imports and pyproject.toml constraints.

---

## Fix Checklist

### Workspace Environment

- From workspace root: `source .venv-workspace/bin/activate`
- Run `bootstrap.sh --no-clone --no-tools` if venv missing
- Install all path deps (full list, tier-ordered):

```bash
# Workspace venv bootstrap — from workspace root
source .venv-workspace/bin/activate
uv pip install -e unified-api-contracts -e unified-internal-contracts -e unified-cloud-interface -e unified-config-interface -e unified-events-interface -e unified-reference-data-interface -e unified-trading-library -e unified-domain-client -e unified-market-interface -e unified-ml-interface -e unified-trade-execution-interface -e unified-sports-execution-interface -e unified-defi-execution-interface -e matching-engine-library -e execution-algo-library -e unified-feature-calculator-library -e unified-position-interface
```

Additional path deps as needed per repo: `alerting-service`, `batch-audit-ui`, `client-reporting-api`,
`client-reporting-ui`, `deployment-api`, `deployment-service`, `deployment-ui`, `execution-algo-library`,
`execution-results-api`, `execution-service`, `features-calendar-service`, `features-cross-instrument-service`,
`features-delta-one-service`, `features-multi-timeframe-service`, `features-onchain-service`, `features-sports-service`,
`features-volatility-service`, `instruments-service`, `market-data-api`, `market-data-processing-service`,
`market-tick-data-service`, `ml-inference-service`, `ml-training-service`, `pnl-attribution-service`,
`position-balance-monitor-service`, `risk-and-exposure-service`, `strategy-service`, `strategy-validation-service`,
`system-integration-tests`. See `workspace-manifest.json` for canonical list.

### Per-Repo Fixes

- Fix imports per external-import-standards (top-level only; no nested module imports)
- Update pyproject.toml dependency constraints for migrated schemas
- Add missing path deps to `[tool.uv]` or install via workspace venv

---

## Verification

```bash
cd <repo>
uv run pytest --collect-only -q
```

Exit code 0 = collection passes. Any import/module error = fix required.

---

## Remaining Repos Fix Log

| Repo                             | Root cause                                                                     | Fix applied                                                                                        |
| -------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| instruments-service              | Wrong imports (STADIUM_MAPPINGS, TEAM_NAME_CORRECTIONS from team_mapping_data) | Fixed imports to team_mapping_data_bundesliga                                                      |
| risk-and-exposure-service        | Missing path deps in workspace venv                                            | `uv pip install -e unified-api-contracts -e unified-internal-contracts` + workspace venv bootstrap |
| ml-inference-service             | Missing unified-api-contracts, InferenceRequest, google-cloud-pubsub           | Added path dep; UIC InferenceRequest; google-cloud-pubsub; 96 tests collect                        |
| market-tick-data-service         | Missing path deps; nested imports                                              | Workspace venv bootstrap; external-import-standards                                                |
| features-delta-one-service       | Schema migrations; missing UAC/UIC                                             | Update pyproject.toml; install path deps                                                           |
| market-data-processing-service   | Missing path deps; import errors                                               | Workspace venv bootstrap; fix imports                                                              |
| strategy-service                 | Schema migrations; nested imports                                              | Top-level imports; update dependency constraints                                                   |
| pnl-attribution-service          | Missing path deps in workspace venv                                            | Workspace venv bootstrap; install sibling libs                                                     |
| ml-training-service              | Import path changes; schema migrations                                         | Top-level imports; pyproject.toml update                                                           |
| deployment-api                   | Missing path deps; nested imports                                              | Workspace venv bootstrap; external-import-standards                                                |
| features-multi-timeframe-service | Missing path deps; schema migrations                                           | Install path deps; update imports                                                                  |
| features-volatility-service      | Missing path deps; import errors                                               | Workspace venv bootstrap; fix imports                                                              |

---

## Verification Results (2026-03-05)

All core repos pass `pytest --collect-only -q`:

| Repo                              | Tests | Status |
| --------------------------------- | ----- | ------ |
| unified-internal-contracts        | 16    | OK     |
| unified-api-contracts             | 719   | OK     |
| unified-cloud-interface           | 118   | OK     |
| unified-config-interface          | 82    | OK     |
| unified-events-interface          | 40    | OK     |
| unified-domain-client             | 44    | OK     |
| unified-market-interface          | 407   | OK     |
| unified-ml-interface              | 401   | OK     |
| unified-trade-execution-interface | 561   | OK     |
| instruments-service               | 819   | OK     |
| ml-inference-service              | 96    | OK     |
| strategy-service                  | 264   | OK     |
| market-data-processing-service    | 224   | OK     |

## References

- **CONTRACTS_SEPARATION_AUDIT.md** — AC/UIC schema separation and migration
- **orphan-contracts-utilization.md** — Orphan schema test and utilization
- **external-import-standards.mdc** — Top-level imports only
- **agent-venv-bootstrap.mdc** — Workspace vs single-repo venv scenarios

---

## Execution Order

Run after orphan-contracts-utilization and before unit_tests_and_test_failure_action. Aligns with
phase2_library_tier_hardening (T0→T3) and phase3_service_hardening_integration.
