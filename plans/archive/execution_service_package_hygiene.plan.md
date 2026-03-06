---
name: Execution-Service Package Hygiene
overview: |
  Follow-on to execution_services_hygiene_refactor (#12a). Removes dead modules,
  collapses single-file subdirectories, and fixes pre-existing test collection errors
  in execution-service. All changes are within execution-service only.

  Motivation:
  - 35 subdirectories at execution_service/ root is confusing; several are 1–2 files
  - analytics/ package is dead: 0 importers outside itself; re-exports benchmark.metrics
  - core/ has 1 file (audit_log.py), 1 importer (api/manual_instruction_api.py)
  - io/ has 2 files (__init__.py + loader.py), 1 importer (itself)
  - test_sports_execution.py crashes collect with ImportError on missing contracts
  - test_backtest_service_split.py imports visualizer_api (a separate service — wrong repo)

  References: execution_services_hygiene_refactor.plan.md (#12a)
  Execution order: After #12a (day4-quality-gates is complete)
todos:
  - id: fix-test-sports-collection
    content: "Fix test_sports_execution.py collection error: add pytest.importorskip('unified_internal_contracts.domain.execution_service.sports') at top of file so it skips gracefully when sports contracts are not yet published, instead of crashing the test runner."
    status: completed
  - id: delete-test-backtest-split
    content: "Delete tests/unit/test_backtest_service_split.py: this file imports visualizer_api which is a completely separate service not installed in execution-service's virtualenv. The file has no place in this repo. Delete it."
    status: completed
  - id: delete-analytics-package
    content: "Delete execution_service/analytics/ package: confirmed 0 importers outside the package itself. The package only re-exports symbols from execution_service.benchmark.metrics (PathAwareMetrics, StatisticalMetrics, compute_aggregate_metrics, compute_path_aware_metrics, compute_statistical_metrics). Remove analytics/__init__.py and the analytics/ directory."
    status: completed
  - id: merge-core-into-utils
    content: "Move execution_service/core/audit_log.py → execution_service/utils/audit_log.py. Update the one importer: execution_service/api/manual_instruction_api.py line 18 changes 'from execution_service.core.audit_log import persist_audit_log' → 'from execution_service.utils.audit_log import persist_audit_log'. Then remove the empty core/ directory."
    status: completed
  - id: merge-io-into-utils
    content: "Move execution_service/io/loader.py → execution_service/utils/loader.py. Update execution_service/io/__init__.py to import from new location, OR merge io/__init__.py re-exports directly into utils/. Then remove the empty io/ directory (or merge io/__init__.py into utils/__init__.py if utils re-exports the same symbols)."
    status: completed
  - id: verify-unit-tests-pass
    content: "After all moves/deletes, run: cd execution-service && python -m pytest tests/unit/ -q --tb=short 2>&1 | tail -20. Confirm: 0 collection errors, 0 failures, all previously passing tests still pass."
    status: completed
isProject: false
---

# Execution-Service Package Hygiene Plan

**Scope:** execution-service only — no cross-repo changes
**Execution order:** After #12a (completed 2026-03-06)
**Reference:** [execution_services_hygiene_refactor.plan.md](execution_services_hygiene_refactor.plan.md)

---

## What & Why

| Item                             | Action             | Reason                                                      |
| -------------------------------- | ------------------ | ----------------------------------------------------------- |
| `analytics/` package             | Delete             | 0 importers; pure re-export of `benchmark.metrics`          |
| `core/audit_log.py`              | Move to `utils/`   | Single file, single importer; merges into existing `utils/` |
| `io/loader.py`                   | Move to `utils/`   | Single file; `io/__init__.py` is the only consumer          |
| `test_sports_execution.py`       | Add `importorskip` | Contracts submodule not yet published; crashes collect      |
| `test_backtest_service_split.py` | Delete             | Imports `visualizer_api` (wrong service entirely)           |

## Acceptance Criteria

- `python -m pytest tests/unit/ -q` exits 0, 0 failures, 0 collection errors
- `ruff check execution_service/` passes with no new violations
- No references to `execution_service.analytics`, `execution_service.core`, or `execution_service.io` remain in any `.py` file
