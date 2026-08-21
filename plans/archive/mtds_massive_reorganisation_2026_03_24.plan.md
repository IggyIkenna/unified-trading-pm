---
doc_type: plan
title: mtds-massive-reorganisation
summary: Reorganise market-tick-data-service from 34,765L/139 files to 850L/13 files following instruments-service patterns
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-24'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: market-tick-data-service, code: C4, deployment: none, business: none}
- {repo: unified-market-interface, code: C2, deployment: none, business: none}
- {repo: unified-api-contracts, code: C2, deployment: none, business: none}
- {repo: unified-api-contracts (internal), code: C2, deployment: none, business: none}
- {repo: unified-trading-pm (codex/ subdir), code: C5, deployment: none, business: none}
- {repo: unified-trading-pm, code: C5, deployment: none, business: none}
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-03-24
todos:
- {id: phase-0-codex-doc, content: '- [x] [AGENT] P0. Create service-orchestration-patterns.md in codex with 10 lessons

    ', status: done}
- {id: phase-0-pre-audit, content: '- [x] [AGENT] P0. Pre-audit: downstream consumers, import violations, UMI gaps, dedup analysis

    ', status: done}
- {id: phase-0-pm-plan, content: '- [x] [AGENT] P0. Create PM active plan file

    ', status: done}
- {id: phase-1-uac, content: '- [x] [AGENT] P0. UAC: schemas already existed; fixed __init__.py re-exports for Databento/Tardis/DeFi

    ', status: done}
- {id: phase-1-umi, content: '- [x] [AGENT] P0. UMI: created 5 new adapters (DatabentoCmeConverter, DatabentoOpraConverter, DatabentMBOAdapter, TardisIncrementalBookAdapter, L2BookState) + 36 tests

    ', status: done}
- {id: phase-1-uic, content: '- [x] [AGENT] P0. UIC: created 5 new files (tick_schemas.py, output_schemas.py, candle_schemas.py, validation.py, quality.py) in domain/market_tick_data/

    ', status: done}
- {id: phase-2-dedup, content: '- [x] [AGENT] P0. Dedup: app/core/ won all 10 pairs. Deleted engine/orchestrators/, engine/visualization/, engine/venues/, engine/uploaders/, 4 inferior duplicates

    ', status: done}
- {id: phase-3-config, content: '- [x] [AGENT] P0. Config: 10 files (4,400L) -> 1 file (75L) extending UnifiedCloudConfig. 6 fields only.

    ', status: done}
- {id: phase-4-rewrite, content: '- [x] [AGENT] P0. Core rewrite: CLI (52L), handler (126L), orchestrator (177L), adapter (68L) = 502L total

    ', status: done}
- {id: phase-5-dead-code, content: '- [x] [AGENT] P0. Deleted all dead code: 34,765L -> 850L (97.6% reduction). 139 files -> 13 files.

    ', status: done}
- {id: phase-6-docs, content: '- [x] [AGENT] P0. README rewritten (14.9KB -> 2.5KB). Deleted specs/, 3 audit files, legacy pytest.ini.

    ', status: done}
- {id: phase-7-hygiene, content: '- [x] [AGENT] P0. Fixed: deep import in seed_mock_data.py, deleted 4 orphaned root scripts, moved setup.sh to scripts/

    - [x] [AGENT] P0. Fixed: brittle getattr(self.runtime,...) -> typed ServiceRuntime fields + extra_args

    - [x] [AGENT] P0. Fixed: deleted node_modules/, htmlcov/, logs/, sample_data/ at root

    - [x] [AGENT] P0. Slimmed pyproject.toml deps: 50 -> 20 (removed plotly, polars, numba, ccxt, tardis-client, databento, yfinance, etc.)

    - [x] [AGENT] P0. Updated workspace manifest: 8 deps -> 3 direct deps (UTL, UAC, UIC)

    ', status: done}
- {id: phase-7-tests, content: '- [x] [AGENT] P0. Unit tests: 41 passing (config, orchestrator, adapter, handler, event_logging)

    - [x] [AGENT] P0. Integration tests: library contract tests for UTL, UAC, UIC, UConfigI, UMI

    - [x] [AGENT] P0. basedpyright: 0 errors, 0 warnings (fixed ServiceRuntime/VenueMapping/ManifestWriter APIs)

    - [x] [AGENT] P0. quality-gates.sh: ALL PASSED (43s)

    ', status: done, note: '41 tests, 0 basedpyright errors, QG green'}
- {id: phase-8-commit, content: '- [x] [AGENT] P0. Commit changes across all 6 repos

    ', status: done}
isProject: false
---

# Market-Tick-Data-Service Massive Reorganisation

## Context

instruments-service refactoring proved a tier-3 service can be reduced from ~2,000+ lines to 810 lines/8 files. Key:
enforce **Import Contract** (only UTL + UAC/UIC, never UCI/UCloudI directly).

market-tick-data-service was 34,765 lines / 139 files. Now **850 lines / 13 files** (97.6% reduction, QG green).

## Lessons Learned (for next service refactor)

### Phase 0: Pre-Audit Checklist

1. Diff duplicate directories (engine/ vs app/core/) -- take best-of-both, not just one side
2. Check UMI adapter gaps -- some things stay in service (Hyperliquid S3, sports transforms)
3. Audit downstream consumers -- usually just examples/scripts
4. Document import contract violations before fixing

### Phase 1: Library Enrichment

1. Check if schemas already exist in UAC before moving -- they often do
2. Domain validation rules go to UIC (not UTL!) -- UTL is framework only
3. Vendor adapters go to UMI -- include CME/OPRA/MBO domain-specific converters
4. UTL is a smart router, NOT a dumping ground

### Phase 2-5: Service Transformation

1. Use `live_trigger="pubsub"` for event-driven services (not "scheduled")
2. Config should have 4-7 fields only -- everything else from UTL/UCI/UAC
3. Single orchestrator handles ALL categories via UMI routing -- no per-category orchestrators
4. Shard-level failure isolation: per-venue catch with no raise

### Phase 6: Docs

1. README should be focused (~2-3KB), point to SSOTs (codex, UAC, UIC)
2. Delete: stale specs, audit files, HFT benchmark theatre
3. Delete legacy pytest.ini if pyproject.toml has [tool.pytest.ini_options]

### API Signature Verification

1. Always read actual library source before writing service code -- do not assume API shapes
2. Key gotchas: ServiceRuntime.category (not categories), gcp_project_id (not gcs/project_id), is_mock (not
   is_mock_mode)
3. VenueMapping has no get_venues_for_categories() -- implement per-service
4. ManifestWriter(service_name=) not ManifestWriter(sink)
5. process() must accept object (Liskov), use isinstance guard
6. ApiKeyReloader replaces validate_api_keys_for_venues

### Phase 7: QG Hygiene (often missed)

1. **Deep imports**: check scripts/ for `from library.core.module import` -- should be `from library import`
2. **Orphaned root scripts**: move to scripts/ or delete -- cleanup*local_files.sh, install.sh, test*\*.sh
3. **Orphaned dirs**: node_modules/, htmlcov/, logs/, sample_data/ -- delete or .gitignore
4. **RUN_INTEGRATION**: set true and add tests/integration/test_library_contracts.py
5. **Integration tests**: only test UTL, UAC, UIC -- verify functionality, not just imports
6. **pyproject.toml deps**: remove vendor-specific deps (ccxt, tardis-client, databento, yfinance, plotly, polars,
   numba, scipy, scikit-learn) -- they come transitively through UTL
7. **Workspace manifest deps**: only list DIRECT imports (UTL, UAC, UIC) -- transitive deps cause false QG failures
8. **pytest.ini**: delete if pyproject.toml has [tool.pytest.ini_options] -- dual config breaks xdist coverage
9. **coverage omit**: add [tool.coverage.run] omit for boilerplate (\_\_main\_\_.py, config_reloaders.py, api/main.py,
   cli/main.py)
10. **getattr(self.runtime, ...)**: use typed ServiceRuntime fields or extra_args dict

## Execution DAG

Phase 0 (lessons + audit) -> Phase 1 (library enrichment, PARALLEL) -> QG -> Phase 2-5 (MTDS transform, SEQUENTIAL) ->
QG -> Phase 6 (docs) -> Phase 7 (tests + hygiene) -> Phase 8 (commit)

## Final Structure (850 lines / 13 files)

```
market_tick_data_service/
    __init__.py (3L), __main__.py (12L)
    config/service_config.py (71L) -- 6 fields
    config_reloaders.py (148L)
    cli/main.py (52L) -- ServiceBootstrap
    cli/handlers/tick_data_handler.py (126L) -- UnifiedServiceHandler
    adapters/umi_tick_provider.py (68L) -- single UMI adapter
    engine/orchestrator.py (177L) -- stateless, import contract
    api/main.py (45L) -- health endpoint
```

## Success Criteria

- Import contract: zero direct UCI/UCloudI/UConfigI imports
- All 5 market categories (CeFi, TradFi, DeFi, Sports, Prediction Markets) supported
- quality-gates.sh pass, basedpyright clean, 93%+ coverage
- README under 3KB, zero stale specs
- pyproject.toml: only direct deps (UTL + framework)
- Workspace manifest: only direct deps (UTL, UAC, UIC)
