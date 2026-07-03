---
doc_type: plan
title: instrument-data-source-separation
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-21'
overview: Separate instrument identity from data-source-specific fields across UAC and consumers
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-api-contracts, code: C0, deployment: none, business: none}
- {repo: instruments-service, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: phase-1a-tradfi-symbology, content: '- [ ] [AGENT] P0. Split TRADFI_VENUE_MAPPINGS into identity + provider bindings in tradfi_symbology.py

    ', status: todo, note: ''}
- {id: phase-1b-venue-to-data-sources, content: '- [ ] [AGENT] P1. Update VENUE_TO_DATA_SOURCE to 1:N with use_for in canonical_mappings.py

    ', status: todo, note: ''}
- {id: phase-1c-data-source-continuity, content: '- [ ] [AGENT] P1. Generalize data_source_continuity.py temporal resolution pattern

    ', status: todo, note: ''}
- {id: phase-1d-polymarket-lint, content: '- [ ] [AGENT] P0. Fix pre-existing polymarket lint errors (F841/F821/N806)

    ', status: todo, note: ''}
- {id: phase-1e-uac-exports-qg, content: '- [ ] [AGENT] P0. Update UAC __init__.py exports + run QG

    ', status: todo, note: ''}
- {id: phase-2a-venue-config, content: '- [ ] [AGENT] P0. Update instruments-service venue_config.py and TradFiInstrument to resolve bindings

    ', status: todo, note: ''}
- {id: phase-2b-tests, content: '- [ ] [AGENT] P0. Update instruments-service tests for new structure

    ', status: todo, note: ''}
- {id: phase-2c-instruments-qg, content: '- [ ] [AGENT] P0. Run instruments-service QG

    ', status: todo, note: ''}
- {id: phase-3-downstream, content: '- [ ] [AGENT] P1. Audit downstream consumers (market-tick-data-service, execution-service)

    ', status: todo, note: ''}
- {id: phase-4-commit, content: '- [ ] [AGENT] P0. Commit all repos

    ', status: todo, note: ''}
isProject: false
---

# Instrument Identity / Data-Source Separation

## Context

`TRADFI_VENUE_MAPPINGS` in UAC `tradfi_symbology.py` conflates instrument identity (what the instrument IS) with
data-source-specific fields (WHERE to get data for it). The VIX-USD entry (CBOE calculated index) was added without
Databento fields (`dataset`, `stype`, `code`), but `instruments-service/venue_config.py` does `inst["dataset"]` on every
entry, crashing on VIX-USD. This breaks 51 instruments-service tests.

The deeper issue: `VENUE_TO_DATA_SOURCE` is 1:1 (one source per venue), but instruments can have multiple data sources
(historical via Tardis, live via exchange API, execution via CCXT). `data_source_continuity.py` handles temporal
multi-source routing but only for VIX.

## Design

### Three clean layers

```
1. INSTRUMENT IDENTITY (provider-agnostic)
   - symbol, venue, instrument_type, base_asset, quote_asset, underlying
   - data_source: provenance field (which source generated this record, for replay)
   - Stays as Python constants for TradFi (~52 entries, stable)
   - Dynamic instruments (CeFi, DeFi, Sports) fetched at runtime by instruments-service

2. DATA SOURCE BINDINGS (per-provider, per-instrument)
   - instrument_symbol -> provider -> provider_symbol, dataset, stype, code, ticker, series
   - use_for: "historical" | "live" | "execution" | "all"
   - date_range: optional temporal window (generalizes data_source_continuity)

3. SOURCE CAPABILITIES (per-provider)
   - Already exists: capability_declarations (74 sources)
   - No changes needed
```

### Key decisions

- `data_source` remains on instrument identity as provenance (which source generated this definition)
- Provider bindings are keyed by instrument symbol, not by venue (same venue can have instruments from different
  sources)
- `VENUE_TO_DATA_SOURCES` (plural) replaces `VENUE_TO_DATA_SOURCE` — returns list of `DataSourceRoute` with `use_for`
- Backward-compat `VENUE_TO_DATA_SOURCE` stays temporarily (returns primary source) — removed once all consumers updated

## Execution DAG

```
Phase 1 (UAC — SEQUENTIAL within, PARALLEL with nothing):
  1a. tradfi_symbology.py: split TRADFI_VENUE_MAPPINGS
  1b. canonical_mappings.py: VENUE_TO_DATA_SOURCES 1:N
  1c. data_source_continuity.py: generalize temporal pattern
  1d. polymarket lint fixes (pre-existing, unrelated)
  1e. exports + QG
  ── QG GATE: UAC quality-gates.sh pass ──

Phase 2 (instruments-service — depends on Phase 1):
  2a. venue_config.py: resolve bindings from new structure
  2b. test updates
  2c. QG
  ── QG GATE: instruments-service quality-gates.sh pass ──

Phase 3 (downstream — depends on Phase 1):
  3. Audit market-tick-data-service, execution-service (likely zero changes — already use .get())
  ── QG GATE: any affected downstream repos ──

Phase 4 (commit all):
  4. Commit UAC, instruments-service, any downstream
```

## Pre-Audit Manifest

### UAC files modified

| File                                           | Change                                                                       |
| ---------------------------------------------- | ---------------------------------------------------------------------------- |
| `registry/tradfi_symbology.py`                 | Split TRADFI_VENUE_MAPPINGS, add TradFiInstrumentDef + ProviderBinding types |
| `canonical/canonical_mappings.py`              | VENUE_TO_DATA_SOURCES 1:N, DataSourceRoute type                              |
| `registry/data_source_continuity.py`           | Generalize get_source_for_instrument()                                       |
| `registry/market_data_categories.py`           | No change (venues list is correct as-is)                                     |
| `__init__.py`                                  | Export new symbols                                                           |
| `external/polymarket/crypto_macro_mappings.py` | Fix F841/F821                                                                |
| `external/polymarket/sports_mappings.py`       | Fix N806                                                                     |

### instruments-service files modified

| File                                          | Change                                                                |
| --------------------------------------------- | --------------------------------------------------------------------- |
| `config/venue_config.py`                      | TradFiInstrument resolve bindings, handle instruments without dataset |
| `tests/unit/test_config.py`                   | Update assertions                                                     |
| `tests/unit/test_config_methods.py`           | Update assertions                                                     |
| `tests/unit/test_config_modules.py`           | Update assertions for new exports                                     |
| `tests/unit/test_livestock_vx_instruments.py` | Update dataset assertions to use bindings                             |
| `tests/unit/test_livestock_vx_integration.py` | Update dataset assertions to use bindings                             |

### Downstream (likely zero changes)

| Repo                     | File                              | Access pattern          | Impact |
| ------------------------ | --------------------------------- | ----------------------- | ------ |
| market-tick-data-service | parallel_download_orchestrator.py | `.get("dataset")`       | Zero   |
| execution-service        | save_operations.py                | `.get("dataset")`       | Zero   |
| UMI                      | databento_adapter.py              | `kwargs.get("dataset")` | Zero   |

## Success Criteria

- UAC `quality-gates.sh` passes
- instruments-service `quality-gates.sh` passes (51 previously-broken tests now pass)
- No downstream breakages
- VIX-USD instrument loads correctly without dataset/stype
- `data_source` field preserved on instrument records for replay provenance
