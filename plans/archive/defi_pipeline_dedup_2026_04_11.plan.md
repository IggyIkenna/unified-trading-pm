---
doc_type: plan
title: defi-pipeline-dedup
summary: Deduplicate DeFi data pipeline — collect-* as canonical path, bypass MDPS for pre-bucketed data, cross-service
  validation
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-data-processing-service, market-tick-data-service, unified-api-contracts]
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
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: market-data-processing-service, code: C0, deployment: none, business: none}
- {repo: features-onchain-service, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: phase-1-uac-metadata, content: '- [x] [AGENT] P0. Phase 1: UAC pipeline stage metadata + validation

    ', status: done, note: 'NEEDS_CANDLE_PROCESSING, MTDS_OUTPUT_PATH_TEMPLATES, MTDS_OUTPUT_BUCKET_DOMAINS, validate_venue_data_coverage(), exports, 35+ tests. QG passes.'}
- {id: phase-2-mtds-umi-delete, content: '- [x] [AGENT] P0. Phase 2: MTDS — delete UMI DeFi path (_DEFI_VENUE_TO_UMI, BaseDefiAdapter routing)

    ', status: done, note: 'Deleted _DEFI_VENUE_TO_UMI dict, DeFi routing block, BaseDefiAdapter import. DeFi guard in umi_tick_provider + orchestrator. 30+ new tests. QG passes (pre-existing failures only).'}
- {id: phase-3-mdps-bypass, content: '- [x] [AGENT] P0. Phase 3: MDPS — skip pass-through DeFi data types, delete 7 adapters

    ', status: done, note: Bypass guard in process_handler + orchestration_service. 7 adapters deleted. 26 new tests. QG passes.}
- {id: phase-4-fos-rewrite, content: '- [x] [AGENT] P0. Phase 4: features-onchain — rewrite data loaders to read from MTDS directly

    ', status: done, note: 'Rewrote load_rate_indices, load_oracle_prices, load_derivative_ticker to read from MTDS. New _resolve_mtds_parquet_files() helper. dependency_checker updated with 3 MTDS upstream deps. 22 new tests. QG passes (pre-existing failures only).'}
- {id: phase-5-validation, content: '- [x] [AGENT] P1. Phase 5: per-venue validation tests + QG checks across all 4 repos

    ', status: done, note: '454 total new tests across 4 repos: UAC (216), MTDS (165), MDPS (26), FOS (47). Per-venue matrix, collect handler schema, feature group source, bypass QG checks. All new tests pass.'}
isProject: false
---

# DeFi Data Pipeline Deduplication & Streamlining

## Context

Three problems in the DeFi data pipeline create redundancy and unnecessary processing:

1. **MTDS dual-path DeFi collection**: The `download` operation (via UMI `_DEFI_VENUE_TO_UMI` dict) AND 11 specialized
   `collect-*` handlers both fetch the same data from The Graph/RPC sources, writing to different GCS buckets with no
   deduplication.

2. **MDPS unnecessary processing**: 7 of 12 DeFi adapters are pure pass-through (LOCF + CandleOutput wrapping with
   OHLCV=NaN). Data like lending rates, oracle prices, and risk params arrive pre-bucketed from The Graph — wrapping
   them in candle schema adds no value. Only swaps and liquidity need real candle processing.

3. **No cross-service validation**: UAC declares `data_types` and `mtds_operations` per protocol but nothing enforces
   that the pipeline is complete end-to-end.

**Decisions**:

- `collect-*` handlers become the canonical DeFi collection path; UMI DeFi path is deleted
- Pre-bucketed DeFi data bypasses MDPS, flows directly to features-onchain-service
- UAC gets `NEEDS_CANDLE_PROCESSING` metadata and validation functions
- Every DeFi venue tested for one day across all three services after refactor

## Execution DAG

```
Phase 1: UAC (metadata + validation + tests)
    |
    QG gate
    |
    +-------------------+
    |                   |
Phase 2: MTDS        Phase 3: MDPS        [PARALLEL]
(delete UMI DeFi)    (bypass pass-through)
    |                   |
    QG gate             QG gate
    |                   |
    +-------------------+
            |
      Phase 4: features-onchain-service
      (read MTDS directly for bypass types)
            |
            QG gate
            |
      Phase 5: per-venue validation tests
            |
            All 4 repo QGs pass
```

## Pre-Audit Manifest

| Repo     | File                                            | Action                                                                      |
| -------- | ----------------------------------------------- | --------------------------------------------------------------------------- |
| **UAC**  | `registry/market_data_categories.py`            | ADD `NEEDS_CANDLE_PROCESSING`, `MTDS_OUTPUT_PATH_TEMPLATES`, functions      |
| **UAC**  | `registry/capability_declarations/_defi.py`     | ADD `validate_venue_data_coverage()`                                        |
| **UAC**  | `registry/capability_declarations/__init__.py`  | ADD re-export                                                               |
| **UAC**  | `registry/__init__.py`                          | ADD re-exports                                                              |
| **UAC**  | `__init__.py`                                   | ADD facade exports                                                          |
| **UAC**  | `tests/unit/test_defi_pipeline_completeness.py` | NEW file                                                                    |
| **MTDS** | `adapters/umi_tick_provider.py`                 | DELETE `_DEFI_VENUE_TO_UMI`, DeFi routing, `BaseDefiAdapter` import         |
| **MTDS** | `engine/orchestrator.py`                        | UPDATE to skip DeFi in download op                                          |
| **MTDS** | `tests/unit/test_defi_routing_isolation.py`     | NEW file                                                                    |
| **MDPS** | `cli/handlers/process_handler.py`               | ADD bypass filter                                                           |
| **MDPS** | `app/core/orchestration_service.py`             | ADD bypass guard                                                            |
| **MDPS** | `app/adapters/defi/lending_adapter.py`          | DELETE                                                                      |
| **MDPS** | `app/adapters/defi/oracle_adapter.py`           | DELETE                                                                      |
| **MDPS** | `app/adapters/defi/utilization_adapter.py`      | DELETE                                                                      |
| **MDPS** | `app/adapters/defi/rewards_adapter.py`          | DELETE                                                                      |
| **MDPS** | `app/adapters/defi/risk_params_adapter.py`      | DELETE                                                                      |
| **MDPS** | `app/adapters/defi/onchain_perp_adapter.py`     | DELETE                                                                      |
| **MDPS** | `app/adapters/defi/flash_loan_adapter.py`       | DELETE                                                                      |
| **MDPS** | `app/adapters/defi/__init__.py`                 | UPDATE remove deleted imports                                               |
| **MDPS** | `tests/unit/test_defi_bypass_routing.py`        | NEW file                                                                    |
| **FOS**  | `app/core/data_loader.py`                       | REWRITE `load_rate_indices`, `load_oracle_prices`, `load_derivative_ticker` |
| **FOS**  | `app/core/dependency_checker.py`                | UPDATE upstream deps                                                        |
| **FOS**  | `tests/unit/test_defi_data_source_routing.py`   | NEW file                                                                    |

## Phase 1: UAC — Pipeline Stage Metadata + Validation

### Success Criteria

- `cd unified-api-contracts && bash scripts/quality-gates.sh` passes
- `test_defi_pipeline_completeness.py` all green
- `from unified_api_contracts import needs_candle_processing` works

## Phase 2: MTDS — Deprecate UMI DeFi Path (PARALLEL with Phase 3)

### Success Criteria

- `cd market-tick-data-service && bash scripts/quality-gates.sh` passes
- No references to `_DEFI_VENUE_TO_UMI` or `BaseDefiAdapter` in source
- `download` op does not process any DeFi venue

## Phase 3: MDPS — Skip Pass-Through DeFi Data Types (PARALLEL with Phase 2)

### Success Criteria

- `cd market-data-processing-service && bash scripts/quality-gates.sh` passes
- Bypass data types produce no output when MDPS runs
- 5 meaningful DeFi adapters still functional (swap, liquidity, market_state, fx_rate, book_snapshot)

## Phase 4: features-onchain-service — Read from MTDS Directly

### Success Criteria

- `cd features-onchain-service && bash scripts/quality-gates.sh` passes
- No references to `processed_candles/.*rate_indices` or `processed_candles/.*oracle_prices` in source
- Dependency checker lists MTDS as upstream for bypass types

## Phase 5: Per-Venue Validation

### Representative Venues

| Protocol Class | Venue               | MTDS Operation                           | Data Types                   |
| -------------- | ------------------- | ---------------------------------------- | ---------------------------- |
| Lending        | AAVE_V3-ETHEREUM    | collect-lending-indices                  | lending_indices, risk_params |
| DEX            | UNISWAP_V3-ETHEREUM | collect-dex-swaps, collect-dex-pools     | swaps, dex_pools             |
| Yield          | LIDO-ETHEREUM       | collect-lst-rates, collect-oracle-prices | lst_rates, oracle_prices     |
| Perps          | HYPERLIQUID         | collect-perp-funding                     | perp_funding                 |
| Solana         | DRIFT-SOLANA        | collect-perp-funding                     | perp_funding                 |
| Gas            | (cross-chain)       | collect-gas-fees                         | gas_fees                     |
| Liquidations   | AAVE_V3-ETHEREUM    | collect-liquidations                     | liquidations                 |
| Rewards        | EIGENLAYER-ETHEREUM | collect-eigenlayer-rewards               | rewards                      |

### Success Criteria

- All 4 repo QGs pass
- Per-venue validation passes for all 8 representative venues
- ~200 total new tests across all repos

## Risk Assessment

| Risk                                                             | Impact | Mitigation                                                                    |
| ---------------------------------------------------------------- | ------ | ----------------------------------------------------------------------------- |
| GCS path mismatch between MTDS handlers and FOS reader           | HIGH   | `MTDS_OUTPUT_PATH_TEMPLATES` in UAC is SSOT; both services import from it     |
| Bucket name mismatch (MTDS tick bucket vs MDPS processed bucket) | HIGH   | Phase 4.4 updates dependency_checker bucket templates explicitly              |
| Schema divergence (MTDS raw columns vs old MDPS candle columns)  | MEDIUM | Keep existing schema normalization logic from fallback path                   |
| CeFi/TradFi regression                                           | LOW    | Regression tests in every phase; bypass guard only applies to DeFi data types |
