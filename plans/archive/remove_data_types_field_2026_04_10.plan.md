---
doc_type: plan
title: remove-data-types-field
summary: Remove deprecated data_types field from InstrumentDefinition and all consumers — PROTOCOL_CAPABILITIES in UAC is
  the SSOT
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, instruments-service, unified-api-contracts, unified-trading-library, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-10'
remaining_todos_consolidated_into: consolidated_operational_validation_2026_04_15
superseded_by: [consolidated_operational_validation_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-10
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: unified-trading-library, code: C0, deployment: none, business: none}
- {repo: unified-market-interface, code: C0, deployment: none, business: none}
- {repo: instruments-service, code: C0, deployment: none, business: none}
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: p1-uac-remove-field, content: '- [x] [AGENT] P0. Remove data_types from InstrumentDefinition + schemas in UAC

    ', status: done, note: 'Phase 1 — Removed field, validator, REQUIRED_BUSINESS_FIELDS entry'}
- {id: p1-uac-remove-canonical, content: '- [x] [AGENT] P0. Remove data_types from canonical domain reference schema

    ', status: done, note: Phase 1 — Removed from canonical/domain/reference/__init__.py}
- {id: p1-uac-remove-parquet, content: '- [x] [AGENT] P0. Remove data_types from INSTRUMENTS_PARQUET_SCHEMA

    ', status: done, note: Phase 1 — Removed from EXTENDED_COLUMNS and INSTRUMENTS_PARQUET_SCHEMA}
- {id: p1-uac-tests, content: '- [x] [AGENT] P0. Update UAC tests — remove data_types assertions

    ', status: done, note: 'Phase 1 — Removed TestValidateDataTypes class, fixture data_types arg, assertion'}
- {id: p1-uac-qg, content: '- [x] [SCRIPT] P0. Run UAC quality-gates.sh — must pass

    ', status: done, note: 'Phase 1 gate — Tests PASSED, Type check PASSED (pre-existing: file size, pip-audit)'}
- {id: p2-utl-remove-method, content: '- [x] [AGENT] P0. Remove get_instruments_by_data_type() from UTL domain clients

    ', status: done, note: Phase 2 — Removed from both domain/instruments_client.py and domain_client/clients/instruments.py}
- {id: p2-utl-remove-parsing, content: '- [x] [AGENT] P0. Remove data_types field mapping in UTL instrument parsing

    ', status: done, note: 'Phase 2 — Removed data_types from get_trading_metadata(), _apply_filters(), _optional_coverage_stats()'}
- {id: p2-utl-tests, content: '- [x] [AGENT] P0. Update UTL tests — remove data_types fixtures and test_get_instruments_by_data_type

    ', status: done, note: Phase 2 — Removed 3 test methods}
- {id: p2-utl-qg, content: '- [x] [SCRIPT] P0. Run UTL quality-gates.sh — must pass

    ', status: done, note: 'Phase 2 gate — Tests PASSED, Type check PASSED (pre-existing: function size, pip-audit)'}
- {id: p3-umi-stop-setting, content: '- [x] [AGENT] P1. Stop setting data_types on instruments in UMI DeFi adapters

    ', status: done, note: Phase 3 — Removed from 14 adapter files (12 DeFi + 2 onchain_perps)}
- {id: p3-umi-qg, content: '- [x] [SCRIPT] P1. Run UMI quality-gates.sh — must pass

    ', status: done, note: 'Phase 3 gate — 1985 passed (3 pre-existing TheGraph shard test failures, unrelated)'}
- {id: p3-instruments-svc, content: '- [x] [AGENT] P1. Remove data_types references in instruments-service if any remain

    ', status: done, note: Phase 3 — No data_types references found in instruments-service source. Already clean.}
- {id: p3-instruments-qg, content: '- [x] [SCRIPT] P1. Run instruments-service quality-gates.sh — no changes, already passing

    ', status: done, note: Phase 3 gate — No code changes needed}
- {id: p3-ui-schema, content: '- [x] [AGENT] P1. Remove data_types from UI internal-contracts schema mirror

    ', status: done, note: Phase 3 — No InstrumentDefinition.data_types in UI. Existing data_types refs are deployment/MTDS concepts (not in scope).}
- {id: p4-gcs-cleanup, content: '- [ ] [HUMAN] P2. Run instruments-service backfill to regenerate parquet without data_types column

    ', status: todo, note: Phase 4 — after all code changes merged. Existing GCS parquet has the column; new writes won't.}
- {id: p4-workspace-qg, content: '- [ ] [SCRIPT] P2. Run quality-gates.sh on all 5 affected repos — all must pass

    ', status: todo, note: Final validation}
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_operational_validation_2026_04_15.md](./consolidated_operational_validation_2026_04_15.md).** Original
> scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Remove `data_types` Field from InstrumentDefinition

## Context

The `data_types` field on `InstrumentDefinition` is a comma-separated string (e.g. `"trades,book_snapshot_5"`) that was
originally used to declare which data types an instrument supports. This is now redundant because:

- **UAC `PROTOCOL_CAPABILITIES`** declares data_types per protocol (SSOT for DeFi)
- **UAC `DATA_TYPES_BY_CATEGORY`** declares data_types per venue category (SSOT for CeFi/TradFi/Sports)
- **MTDS orchestrator** already routes via `get_valid_data_types_for_venue()` from UAC — does NOT read per-instrument
  data_types
- The field duplicates information that is better expressed at the protocol/category level, not per-instrument

Removing it eliminates a stale column from every instrument parquet file (~80 venues, millions of rows).

## Dependency DAG

```
Phase 1: UAC (field + schema + tests)
    ↓ QG gate
Phase 2: UTL (client methods + tests)
    ↓ QG gate
Phase 3: UMI + instruments-service + UI (stop writing, remove refs)  [PARALLEL]
    ↓ QG gate
Phase 4: GCS cleanup (regenerate parquet without column)  [HUMAN]
```

## Pre-Audit Manifest

### Phase 1 — unified-api-contracts (ROOT)

| File                                                | Line     | Content                                                    | Action            |
| --------------------------------------------------- | -------- | ---------------------------------------------------------- | ----------------- |
| `internal/reference/instrument_definition.py`       | 49       | `"data_types"` in REQUIRED_BUSINESS_FIELDS                 | REMOVE from list  |
| `internal/reference/instrument_definition.py`       | 60       | `data_types: str \| None = None`                           | REMOVE field      |
| `internal/reference/instrument_definition.py`       | 125-133  | `@field_validator("data_types") ... validate_data_types()` | REMOVE validator  |
| `canonical/domain/reference/__init__.py`            | 72       | `data_types: list[str] \| None = None`                     | REMOVE field      |
| `internal/domain/instruments/__init__.py`           | 76-81    | ColumnSchema `name="data_types"` (EXTENDED_COLUMNS)        | REMOVE entry      |
| `internal/domain/instruments/__init__.py`           | 468-474  | INSTRUMENTS_PARQUET_SCHEMA `name="data_types"` entry       | REMOVE entry      |
| `tests/internal/unit/test_instrument_definition.py` | 156, 164 | `assert inst.data_types ...`                               | REMOVE assertions |

### Phase 2 — unified-trading-library

| File                                   | Line              | Content                                        | Action                 |
| -------------------------------------- | ----------------- | ---------------------------------------------- | ---------------------- |
| `domain_client/clients/instruments.py` | 425               | `"data_types": ([s.strip()...])` field mapping | REMOVE from dict       |
| `domain_client/clients/instruments.py` | 432-456           | `get_instruments_by_data_type()` method        | REMOVE entire method   |
| `domain/instruments_client.py`         | 229-238           | `available_data_types` column filtering        | REMOVE filtering block |
| `domain/instruments_client.py`         | 375-447           | `get_instruments_by_data_type()` method        | REMOVE entire method   |
| `tests/unit/test_domain_clients.py`    | 426, 439, 537-542 | Test fixtures + test method                    | REMOVE                 |

### Phase 3 — unified-market-interface (12+ adapters SET data_types on instrument dicts)

| File                                            | Line               | Content                                      | Action               |
| ----------------------------------------------- | ------------------ | -------------------------------------------- | -------------------- |
| `adapters/defi/aave_lending.py`                 | 717, 766           | `"data_types": "rate_indices,..."`           | REMOVE key from dict |
| `adapters/defi/morpho_adapter.py`               | 223                | `"data_types": "rate_indices,utilization"`   | REMOVE key from dict |
| `adapters/defi/fluid_adapter.py`                | 179                | `"data_types": "rate_indices,oracle_prices"` | REMOVE key from dict |
| `adapters/defi/ethena_adapter.py`               | 111                | `"data_types": "yields,oracle_prices,..."`   | REMOVE key from dict |
| `adapters/defi/uniswap_v3_adapter.py`           | 494                | `"data_types": "swaps,liquidity"`            | REMOVE key from dict |
| `adapters/defi/uniswapv2_adapter.py`            | 389                | `"data_types": "swaps,liquidity"`            | REMOVE key from dict |
| `adapters/defi/uniswapv4_adapter.py`            | 382                | `"data_types": "swaps,liquidity"`            | REMOVE key from dict |
| `adapters/defi/balancer_adapter.py`             | 408                | `"data_types": "swaps"`                      | REMOVE key from dict |
| `adapters/defi/curve_adapter.py`                | 291                | `"data_types": "swaps,liquidity,volume"`     | REMOVE key from dict |
| `adapters/defi/lst_lido_adapter.py`             | 201                | `"data_types": "oracle_prices"`              | REMOVE key from dict |
| `adapters/defi/lst_etherfi_adapter.py`          | 203                | `"data_types": "oracle_prices,rewards"`      | REMOVE key from dict |
| `adapters/defi/euler_adapter.py`                | 203                | `"data_types": "rate_indices,oracle_prices"` | REMOVE key from dict |
| `adapters/onchain_perps/hyperliquid_adapter.py` | 200, 254, 318, 353 | `inst_def["data_types"] = ...`               | REMOVE assignments   |
| `adapters/onchain_perps/aster_adapter.py`       | 195, 242, 286      | `inst_def["data_types"] = ...`               | REMOVE assignments   |

### Phase 3 — instruments-service

No direct `data_types` field references on InstrumentDefinition in source code (orchestrator uses UAC). Only the
REQUIRED_BUSINESS_FIELDS validation may check for it — verify after UAC change.

### Phase 3 — unified-trading-system-ui

| File                                                                | Line     | Content                           | Action       |
| ------------------------------------------------------------------- | -------- | --------------------------------- | ------------ |
| `context/internal-contracts/schemas/domain/instruments/__init__.py` | ~491-496 | INSTRUMENTS_PARQUET_SCHEMA mirror | REMOVE entry |

### NOT in scope (generic data_types parameters — KEEP)

- `data_types` CLI parameters in MTDS, deployment-api, UMI adapter method signatures
  (`download_market_data(data_types=...)`)
- `PROTOCOL_CAPABILITIES.data_types` in UAC — this is the SSOT replacement
- `get_valid_data_types_for_venue()` in UAC — this is the SSOT routing function
- `DATA_TYPES_BY_CATEGORY` in UAC — this is the SSOT category mapping
- Venue config `data_types` in deployment-service (`venue_data_types.yaml`) — different concept

## Success Criteria

- **Phase 1**: UAC `quality-gates.sh` passes; `InstrumentDefinition` has no `data_types` field
- **Phase 2**: UTL `quality-gates.sh` passes; no `get_instruments_by_data_type()` method exists
- **Phase 3**: UMI + instruments-service + UI `quality-gates.sh` all pass; no adapter sets `data_types`
- **Phase 4**: `rg '"data_types"' --type py --glob '!.venv*' --glob '!tests*'` across all 5 repos returns zero hits for
  InstrumentDefinition.data_types (generic params still OK)
- **GCS**: New instrument parquet files written without `data_types` column
