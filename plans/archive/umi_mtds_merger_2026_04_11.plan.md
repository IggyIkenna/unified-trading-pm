---
doc_type: plan
title: umi-mtds-merger
summary: Merge unified-market-interface into market-tick-data-service as market_interface sub-package
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, execution-service, instruments-service, market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-11
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: market-tick-data-service, code: C4, deployment: none, business: none}
- {repo: execution-service, code: C4, deployment: none, business: none}
- {repo: features-sports-service, code: C4, deployment: none, business: none}
- {repo: position-balance-monitor-service, code: C4, deployment: none, business: none}
- {repo: e2e-testing, code: C4, deployment: none, business: none}
- {repo: unified-trading-pm, code: C4, deployment: none, business: none}
- {repo: unified-trading-library, code: C4, deployment: none, business: none}
depends_on: []
todos:
- {id: phase1-copy, content: '- [x] [AGENT] P0. Copy UMI source into MTDS market_interface sub-package, delete alt_data adapters (stubs superseded by URDI), fix intra-package imports, update MTDS internal imports, update pyproject.toml with UMI external deps

    ', status: done, note: 89 adapters + 12 clients copied. adapters/alt_data/ deleted. 13 external deps added. Ruff/basedpyright excludes for market_interface.}
- {id: phase2-downstream, content: '- [x] [AGENT] P0. Update all downstream consumers: execution-service (pyproject.toml + 4 test files), features-sports-service (pyproject.toml + 1 source + 2 tests), position-balance-monitor-service (1 test), e2e-testing (2 scripts), unified-trading-pm (5 scripts), unified-trading-library (comments)

    ', status: done, note: Zero unified_market_interface imports remaining across workspace. All pyproject.toml deps updated.}
- {id: phase3-tests, content: '- [x] [AGENT] P0. Move UMI tests into MTDS tests/market_interface/, update all test imports, delete alt_data tests

    ', status: done, note: UMI test tree copied. Alt-data tests deleted. Imports updated.}
- {id: phase4-validation, content: '- [x] [AGENT] P0. Final workspace-wide validation — zero stale references, all QGs green on affected repos

    ', status: done, note: '80+ files fixed across 12 repos. workspace-manifest.json, workspace-constraints.toml, 9 code-workspace files, 23 e2e VM scripts, 22 PM configs/scripts, CLAUDE.md files, pyrightconfig.json files, deployment-service, system-integration-tests. Glassnode+MEV dead stubs deleted. Zero functional UMI references remain outside archive/.'}
- {id: phase5-archive, content: '- [x] [HUMAN] P1. Archive unified-market-interface GitHub repo, remove from workspace manifest and .code-workspace

    ', status: done, note: User moved to archive/ locally 2026-04-11. GitHub repo archival pending (user action).}
isProject: false
---

# UMI into MTDS Merger

## Context

### Why

UMI's sole production consumer is MTDS. Every other service that used UMI types or adapters either imports them
transitively through MTDS or has a single shallow reference. This follows the established repo consolidation pattern
already completed for other interface repos:

- `unified-reference-data-interface` merged into `instruments-service` as `reference_data` sub-package
- `unified-defi-execution-interface` merged into `execution-service` as `defi_execution` sub-package
- `unified-trade-execution-interface` merged into `execution-service` as `trade_execution` sub-package
- `unified-position-interface` merged into `position-balance-monitor-service` as `position_interface` sub-package

Merging UMI into MTDS eliminates a standalone repo, simplifies the dependency graph, and keeps market data adapters
co-located with the service that orchestrates them.

### Alt-Data Adapter Deletion

8 alt-data adapters were deleted from UMI during the copy phase. These were stubs superseded by the full URDI
implementations now living in instruments-service. The URDI versions are 2-4x more complete (proper pagination, rate
limiting, error classification, schema validation). Deleted adapters:

- `adapters/alt_data/` (entire directory) — Arkham, Bloxroute, Pyth, and other removed providers

### Import Path

All consumers now use the new import path:

```python
from market_tick_data_service.market_interface import X
```

Instead of the old:

```python
from unified_market_interface import X
```

### Architectural Violation: features-sports-service

The `features-sports-service` OddsApiAdapter import was updated from UMI to the new MTDS sub-package path. However, this
is an architectural smell — features-sports-service should not import adapters directly. The correct long-term pattern
is for features-sports-service to read from MTDS GCS output (parquet files), not instantiate market data adapters. This
is tracked but not blocking for this merger.

### Lint/Type Exclusion

The `market_interface` sub-package is excluded from MTDS's own ruff and basedpyright configurations. UMI has its own
per-file suppressions and lint rules that differ from MTDS conventions. Forcing MTDS lint rules onto the copied UMI code
would create hundreds of spurious violations. The exclusion is intentional — UMI code retains its own quality baseline,
and any future cleanup is a separate effort.

## Execution DAG

```
Phase 1: Copy UMI into MTDS (source + pyproject.toml)
    |
    QG gate (MTDS)
    |
Phase 2: Update all downstream consumers        [SEQUENTIAL — each repo independent but imports must resolve]
    |     execution-service
    |     features-sports-service
    |     position-balance-monitor-service
    |     e2e-testing
    |     unified-trading-pm
    |     unified-trading-library
    |
    QG gate (all 6 repos)
    |
Phase 3: Move UMI tests into MTDS
    |
    QG gate (MTDS)
    |
Phase 4: Workspace-wide validation
    |
    All affected repo QGs pass, zero stale references
    |
Phase 5: Archive UMI repo                       [HUMAN — GitHub UI + workspace manifest]
```

## Pre-Audit Manifest

| Repo                                 | File                                                           | Action                                                                                   |
| ------------------------------------ | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **MTDS**                             | `market_tick_data_service/market_interface/`                   | NEW sub-package (89 adapters, 12 clients)                                                |
| **MTDS**                             | `market_tick_data_service/market_interface/adapters/alt_data/` | DELETED (stubs superseded by URDI)                                                       |
| **MTDS**                             | `pyproject.toml`                                               | ADD 13 UMI external deps                                                                 |
| **MTDS**                             | `ruff.toml` / `pyrightconfig.json`                             | ADD market_interface excludes                                                            |
| **MTDS**                             | `tests/market_interface/`                                      | NEW test directory (copied from UMI)                                                     |
| **execution-service**                | `pyproject.toml`                                               | REPLACE `unified-market-interface` with `market-tick-data-service`                       |
| **execution-service**                | 4 test files                                                   | UPDATE imports `unified_market_interface` to `market_tick_data_service.market_interface` |
| **features-sports-service**          | `pyproject.toml`                                               | REPLACE `unified-market-interface` with `market-tick-data-service`                       |
| **features-sports-service**          | 1 source file + 2 test files                                   | UPDATE imports                                                                           |
| **position-balance-monitor-service** | 1 test file                                                    | UPDATE imports                                                                           |
| **e2e-testing**                      | 2 scripts                                                      | UPDATE imports                                                                           |
| **unified-trading-pm**               | 5 scripts                                                      | UPDATE references                                                                        |
| **unified-trading-library**          | comments only                                                  | UPDATE references                                                                        |

## Phase 4: Workspace-Wide Validation

### Success Criteria

- `rg "unified_market_interface" --type py --glob '!.venv*' --glob '!**/node_modules/**'` returns zero results
- `rg "unified-market-interface" --glob '!.venv*' --glob '!**/node_modules/**' --glob '!*.md'` returns zero results
  (excluding this plan)
- `cd market-tick-data-service && bash scripts/quality-gates.sh` passes
- `cd execution-service && bash scripts/quality-gates.sh` passes
- `cd features-sports-service && bash scripts/quality-gates.sh` passes
- `cd position-balance-monitor-service && bash scripts/quality-gates.sh` passes
- `from market_tick_data_service.market_interface import ...` resolves in all consumers

## Phase 5: Archive UMI Repo

### Steps (Human)

1. GitHub UI: Settings > General > Archive this repository on `unified-market-interface`
2. Remove `unified-market-interface` entry from `workspace-manifest.json`
3. Remove `unified-market-interface` folder entry from `.code-workspace` files
4. Verify no CI/CD workflows reference the archived repo

## Risk Assessment

| Risk                                                                           | Impact | Mitigation                                                              |
| ------------------------------------------------------------------------------ | ------ | ----------------------------------------------------------------------- |
| Circular import between MTDS core and market_interface                         | HIGH   | market_interface is leaf sub-package with no imports from MTDS core     |
| features-sports-service direct adapter import breaks on MTDS internal refactor | MEDIUM | Documented as architectural violation; long-term fix is GCS-based reads |
| UMI lint suppressions mask real issues in MTDS CI                              | LOW    | Explicit ruff/basedpyright excludes keep the two codebases isolated     |
| Stale UMI references in documentation or scripts                               | LOW    | Phase 4 workspace-wide grep catches all remaining references            |
