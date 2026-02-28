---
name: Bloat Extraction Completion
overview: "Finish the work started in service_bloat_extraction_88f98116.plan.md. All major extractions are done. This plan fixes the residual breakage (21 test failures from signal→instruction renames, execution-results-api HTTP decoupling TODOs) and updates all plan todos to reflect reality. Unblocks schema_ownership_three_tiers_267ab636.plan.md which depends on api-contracts being the clean SSOT for provider schemas."
todos:
  - id: fix-exec-test-renames
    content: "execution-services: Fix 21 failing unit tests caused by signal→instruction method renames from backtest migration. Key failures: _filter_signal_schedule_by_window → _filter_instruction_schedule_by_window, _inject_signal_schedule_into_strategy_config → _inject_instruction_schedule_into_strategy_config, _convert_instructions_to_signals → removed, _extract_signal_benchmark_points → _extract_instruction_benchmark_points, _generate_date_range → moved, _load_venue_book_types → moved. Also fix test_order_tracker.py KeyError on unknown instruction ID (API changed). Target: 0 failures in tests/unit/."
    status: completed
  - id: fix-exec-results-api-decoupling
    content: "execution-results-api: Complete the 3 HTTP decoupling TODOs left in execution_results_api/: (1) /api/v1/config/algorithms + /strategies + /generate + /generate-all — currently 501, needs HTTP call to execution-services or extract grid_generator to a shared lib; (2) /api/v1/validate/dependencies — stub, needs HTTP call to execution-services; (3) backtest subprocess in backtest_service.py — 2 sites still call python -m execution_services.cli.backtest directly, needs HTTP API call. Decision: add a /run endpoint to execution-services FastAPI (if one exists) or leave as subprocess with clear TODO comment documenting the HTTP migration path."
    status: pending
  - id: update-bloat-plan-todos
    content: "Update service_bloat_extraction_88f98116.plan.md: mark all 9 completed todos as completed (mtdh-delete-engine-dir, mtdh-delete-deprecated-handler, mtdh-schemas-to-api-contracts, mtdh-venue-clients-to-umi, exec-extract-visualizer-api, exec-complete-backtest-migration, exec-venue-adapters-to-umi, exec-algorithms-to-library, exec-orders-to-utei). Mark update-cleanup-checklist as in_progress."
    status: completed
  - id: update-cleanup-checklist
    content: "Update unified-trading-pm/plans/ai/service_cleanup_checklist.md with actual line counts and extraction results from the completed bloat extraction work. Record: MTDH reduced from ~30k to ~10k lines (66%), execution-services removed ~33k lines, new repos: execution-results-api. Link to schema_ownership plan for next steps on api-contracts restructure."
    status: pending
isProject: false
---

# Bloat Extraction Completion Plan

## Reference
- **Completed by**: service_bloat_extraction_88f98116.plan.md (all major todos done)
- **Unblocks**: schema_ownership_three_tiers_267ab636.plan.md (api-contracts now has provider schemas as SSOT via thin re-exports; full restructure into api_contracts_external/ is the schema ownership plan's job)

## What Was Done (service_bloat_extraction)

| Item | Lines Removed | Done |
|---|---|---|
| MTDH: app/ duplicate + handler + backup | ~12,291 | ✅ |
| MTDH: Schemas → thin re-exports to api-contracts | ~1,500 net | ✅ |
| MTDH: Venue clients (already in UMI) | ~476 | ✅ |
| EXEC: backtest/ → engine/backtest/ | ~7,663 | ✅ |
| EXEC: orders/ → UTEI + BaseConnector | ~426 | ✅ |
| EXEC: Venue adapters → UDEI/UMI | ~3,349 | ✅ |
| EXEC: Algo calc extraction | ~374 | ✅ |
| EXEC: visualizer-api → new repo | ~7,807 | ✅ |
| **Total removed** | **~33,886** | ✅ |

## What Remains (this plan)

### 1. Test fixes (execution-services, 21 failures)
All from the `backtest/ → engine/backtest/` rename. Tests still reference old method names. No logic changes needed — just rename test calls to match new names.

### 2. execution-results-api decoupling (3 TODOs)
The new service has 3 stub endpoints that call back to execution-services internals. Minimal fix: document the HTTP migration path clearly in code and leave as functional stubs (501/subprocess) until execution-services adds a proper REST API.

### 3. Plan bookkeeping
Update todos in both plans + cleanup checklist.

## Relationship to Schema Ownership Plan

The schema_ownership plan restructures api-contracts into:
- `api_contracts_external/` — raw provider schemas (databento, defi, nautilus moved here by bloat extraction as thin re-exports)
- `unified_normalised_contracts/` — canonical normalised schemas

When schema_ownership runs, the thin re-exports in MTDH (`databento_schema.py`, `defi_schema.py`, `nautilus_schema.py`) will need their import paths updated from `api_contracts.databento.schemas` to `api_contracts_external.databento.schemas`. This is a one-line change per file, already anticipated by the re-export pattern.

No conflict. Schema ownership is the clean-up pass after bloat extraction moved the code.
