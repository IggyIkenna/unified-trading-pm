---
name: frontend-backend-bilateral-plan5-dead-code-cleanup
overview:
  Delete truly abandoned types, superseded venue adapters, deprecated constants, and dead code branches after Plan 4
  disposition
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: strategy-service
    code: C0
    deployment: none
    business: none
  - repo: execution-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-api
    code: C0
    deployment: none
    business: none

depends_on:
  - frontend-backend-bilateral-plan4-strategy-type-completion

todos:
  - id: p5-1-abandoned-venue-types
    content: |
      - [ ] [AGENT] P0. Delete abandoned venue adapter types from UAC. These are raw exchange response types superseded by canonical types:
        **CCXT abstraction (all 8):** CcxtAggTrade, CcxtFundingRate, CcxtMarket, CcxtOhlcv, CcxtOpenInterest, CcxtOrderBook, CcxtTicker, CcxtTrade
        **Kalshi (all 3):** KalshiMarket, KalshiOrderBook, KalshiTrade
        **Manifold (all 3):** ManifoldMarket, ManifoldPrice, ManifoldTrade
        **Coinbase partial (4):** CoinbaseOrderBook, CoinbaseProductsResponse, CoinbaseTicker, CoinbaseTrade
        **Upbit (1):** UpbitTicker
        **Data vendors (all):** TardisAvailableSymbol, TardisExchangeDetail, TardisInstrumentDetail, DatabentoReferenceInstrument, PolygonDividendsResponse, PolygonOptionContractsResponse, PolygonSplitsResponse, PolygonTickersResponse
        Pre-audit: for each, grep workspace to confirm zero real usage (excluding tests, __init__.py re-exports, and imports that import but never call). Remove from __all__ exports and delete the source files/classes.
    status: todo
  - id: p5-2-removed-provider-types
    content: |
      - [ ] [AGENT] P0. Delete types from removed providers (per CLAUDE.md: Elysium, Arkham, Bloxroute, Pyth, Infura — all deleted from UAC). If any types referencing these providers survived the earlier cleanup, delete them now. Also check for: Bitstamp, Bybit (removed from UAC per memory).
    status: todo
  - id: p5-3-deprecated-constants
    content: |
      - [ ] [AGENT] P0. Delete deprecated config constants from UAC that are superseded by the registry pattern:
        **Only delete constants marked DELETE by Plan 4 pre-audit.** Expected candidates:
        - VALID_BOOK_TYPES, VALID_CATEGORIES, VALID_INSTRUCTION_TYPES, VALID_MODES, VALID_TIMEFRAMES (if superseded by enums)
        - VENUE_TO_DATA_SOURCE, VENUE_TO_DATA_SOURCES (if superseded by VENUE_CATEGORY_MAP)
        - TRADFI_DATABENTO_INSTRUMENTS, TRADFI_EQUITIES, TRADFI_FUTURES, TRADFI_INSTRUMENTS, TRADFI_TICKER_UNIVERSE (if superseded by instruments-service registry)
        - CONFIG_SCHEMA, INSTRUCTION_SCHEMA, OPTIONAL_CONFIG_FIELDS, REQUIRED_CONFIG_FIELDS (if superseded by Pydantic config classes)
        - ENDPOINT_REGISTRY (if superseded by OpenAPI spec)
        For each: verify no runtime code depends on it (tests-only or import-chain-only = safe to delete).
    status: todo
  - id: p5-4-infra-monitoring-types
    content: |
      - [ ] [AGENT] P1. Delete infrastructure/monitoring types that were speculative:
        CanonicalCloudStorage, CanonicalComputeJob, CanonicalContainerRegistry, CanonicalMessageQueue, CanonicalOLAPTable, CanonicalScheduledJob, CanonicalSecretStore, CanonicalVirtualMachine
        CoLocationPerformanceMetric, SubMillisecondLatencyRecord, TickToTradeMetric, LatencyBenchmarkReport, LatencyPercentile
        Only delete if Plan 4 pre-audit marks them DELETE. Some monitoring types may be needed if ML monitoring is being wired.
    status: todo
  - id: p5-5-superseded-defi-constants
    content: |
      - [ ] [AGENT] P1. After Plan 4 wires DeFi types, delete DeFi constants that are confirmed superseded:
        - DEFI_INSTRUMENTS (if superseded by instruments-service DeFi adapters)
        - DEFI_LENDING_ASSETS (if superseded by InstrumentDomainConfig)
        - DEFI_MAJOR_ASSET_ADDRESSES, DEFI_MAJOR_ASSET_SYMBOLS (if superseded by InstrumentDomainConfig.defi_major_assets)
        Only delete what Plan 4 task p4-2 confirms is superseded. If Plan 4 migrated usage to the new pattern, delete the old constants here.
    status: todo
  - id: p5-6-strategy-service-dead-branches
    content: |
      - [ ] [AGENT] P1. Clean up dead branches in strategy-service (97 dead branch modules):
        After Plan 4 exports the orphaned strategies, re-run the dead code audit on strategy-service.
        Delete modules that are still dead after wiring:
        - Phase-1 backtesting framework (if replaced by batch orchestrator pattern): backtest_engine.py, fill_simulator.py, flash_loan_simulator.py
        - Duplicate position/exposure monitors (if superseded by position-balance-monitor-service)
        - Unused rebalancers (defi_vault_rebalancer.py, portfolio_rebalancer.py) if not used by any exported strategy
        Be conservative: only delete what the re-audit confirms is dead AFTER Plan 4 wiring.
    status: todo
  - id: p5-7-execution-service-dead-branches
    content: |
      - [ ] [AGENT] P1. Clean up dead branches in execution-service (132 dead branch modules):
        After Plan 4 wires DeFi/sports types, re-run dead code audit.
        Expected safe deletions:
        - Abandoned Solana protocol stubs (drift, jupiter, kamino, marinade, orca, raydium) IF not needed by documented Solana strategies. Note: Solana DeFi is documented as "not yet implemented" — if these are placeholder stubs, keep them. If they're broken incomplete code, delete and document in codex that Solana needs fresh implementation.
        - Duplicate backtest infra (almgren-chriss sweep, parallel runner) if superseded
        - Dead test data generators
        - Orphan monitoring if superseded by ServiceBootstrap lifecycle
    status: todo
  - id: p5-8-unified-trading-api-dead
    content: |
      - [ ] [AGENT] P1. Clean up unified-trading-api dead code (20 dead branches, 28 orphan modules):
        After Plan 3 adds missing routes, re-run dead code audit.
        Delete unused router stubs, orphaned middleware, dead utility modules.
    status: todo
  - id: p5-9-uac-export-cleanup
    content: |
      - [ ] [AGENT] P0. Clean up UAC __all__ exports after deletions:
        1. Remove deleted types from __init__.py __all__ lists
        2. Remove deleted types from domain facade re-exports (market.py, execution.py, etc.)
        3. Ensure no broken imports anywhere in the workspace
        4. Re-run the type usage audit script to verify: DEAD count should drop from 169 to <20
    status: todo
  - id: p5-10-re-run-audits
    content: |
      - [ ] [AGENT] P0. Re-run all audits to verify cleanup:
        1. `bash unified-trading-pm/scripts/openapi/generate-unified-openapi.sh` — verify orphan count drops significantly
        2. Type usage audit: DEAD should be <20 (down from 169)
        3. Dead code audit: orphan modules should decrease across all services
        4. Broken $refs should remain 0
        5. Regenerate and sync TypeScript types to UI
    status: todo
  - id: p5-11-tests-qg
    content: |
      - [ ] [AGENT] P0. Run QG on all affected repos:
        1. unified-api-contracts
        2. strategy-service
        3. execution-service
        4. unified-trading-api
        5. Every downstream repo that imports deleted types (pre-audit from p5-1 through p5-8 identifies these)
        No regressions. No broken imports. All tests pass.
    status: todo
---

## Context

### Problem

169 dead types, 550 orphan modules, 477 dead branch modules across 25 services. After Plan 4 completes the strategy/type
wiring, a significant portion will become alive. What remains dead after Plan 4 is genuinely abandoned and should be
deleted.

### Key Principle

**Plan 4 runs first.** This plan only deletes what Plan 4's pre-audit marks as DELETE. We never delete a type that a
documented strategy needs — we wire it first (Plan 4), then clean up what's left (this plan).

### Pre-Audit from Plan 4

Plan 4 task p4-0 produces a disposition manifest. This plan consumes that manifest:

- Types marked DELETE → deleted here
- Types marked COMPLETE → already wired by Plan 4, now alive
- Types marked KEEP → left alone (test fixtures, representative samples)

### Safe Deletion Categories (from audit)

1. **CCXT abstraction** (8 types) — all dead, replaced by venue-specific adapters
2. **Kalshi/Manifold** (6 types) — prediction markets removed/never launched
3. **Data vendors** (8 types) — Tardis, Polygon, Databento integrations abandoned
4. **Removed providers** — Elysium, Arkham, Bloxroute, Pyth, Infura, Bitstamp, Bybit
5. **Deprecated config constants** — replaced by registry pattern or Pydantic configs
6. **Speculative infra types** — never implemented cloud resource types

### Execution DAG

```
Phase 1 (PARALLEL — safe deletions, no dependencies on Plan 4):
  p5-1: Abandoned venue types
  p5-2: Removed provider types

Phase 2 (PARALLEL — needs Plan 4 pre-audit manifest):
  p5-3: Deprecated constants (per manifest)
  p5-4: Infra/monitoring types (per manifest)
  p5-5: Superseded DeFi constants (per manifest + p4-2)

Phase 3 (PARALLEL — needs Plan 4 wiring complete):
  p5-6: Strategy-service dead branches (re-audit after Plan 4)
  p5-7: Execution-service dead branches (re-audit after Plan 4)
  p5-8: Unified-trading-api dead code (re-audit after Plan 3)

Phase 4 (SEQUENTIAL — depends on all above):
  p5-9: UAC export cleanup
  p5-10: Re-run all audits
  p5-11: QG on all repos
```

### Success Criteria

- **C2**: DEAD types <20 (down from 169); orphan modules reduced by >50%; tests pass
- **C3**: basedpyright + ruff clean
- **C4**: QG pass on all affected repos
- **C5**: Quickmerged; OpenAPI spec regenerated with lower orphan count
