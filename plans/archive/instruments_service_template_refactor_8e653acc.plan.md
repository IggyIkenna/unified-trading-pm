---
doc_type: plan
title: Instruments Service Template Refactor
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-24'
remaining_todos_consolidated_into: consolidated_operational_validation_2026_04_15
superseded_by: [consolidated_operational_validation_2026_04_15.plan.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: Refactor instruments-service from ~104 files/12,000+ lines to ~18-20 files/~1,800 lines by making URDI the sole external API path, removing all service-level infrastructure, canonicalization, aggregation, and validation logic, and delegating every cross-cutting concern to UTL/UDC/UCI/UAC. The result is the template all other services follow.
todos:
- {id: t0a-uac-naming-fix, content: 'TRACK 0a — repo: unified-api-contracts. Fix naming inconsistency in unified_api_contracts/canonical/canonical_mappings.py: VenueMapping.all_tardis_exchanges uses lowercase API names (e.g. binance-futures) but DATA_SOURCE_TO_VENUES[''tardis''] uses uppercase canonical names (e.g. BINANCE-SPOT). Align all_tardis_exchanges entries to uppercase canonical names matching venue_constants.py. This unblocks deletion of normalizer shims in instruments-service. Run: cd unified-api-contracts && bash scripts/quickmerge.sh ''fix: align Tardis venue names to uppercase canonical format'' --agent', status: completed}
- {id: t0b-uac-ticker-registry, content: 'TRACK 0b — repo: unified-api-contracts. Add TRADFI_TICKER_UNIVERSE dict to unified_api_contracts/registry/ alongside representative_sample.py. Copy content from instruments-service/instruments_service/config/data/tickers.json (keys: sp500_tickers, etf_tickers, nasdaq_tickers). Export from unified_api_contracts/__init__.py. After this, instruments-service config_reloaders.py will import from unified_api_contracts.registry instead of the local tickers.json. Run: cd unified-api-contracts && bash scripts/quickmerge.sh ''feat: add TRADFI_TICKER_UNIVERSE to UAC registry'' --agent', status: completed}
- {id: t0c-urdi-symbol-sports, content: 'TRACK 0c — repo: unified-reference-data-interface. Two moves: (1) Absorb Tardis symbol parsing: move logic from instruments-service/instruments_service/engine/processors/symbol_parser.py (435 lines — _ALL_QUOTE_SUFFIXES, _CRYPTO_QUOTE_CURRENCIES, parse functions) into unified_reference_data_interface/adapters/tardis.py so its InstrumentRecord output has instrument_key fully resolved with correct base/quote/symbol. (2) Absorb sports normalization: move instruments-service/instruments_service/sports/ entire directory (7 files: team_normalizer.py 648L, league_registry, fixture_parser, team_aliases, player_aliases, round_names, prediction_market_resolver) into api_football.py and betfair.py adapters so they return fully canonical InstrumentRecord. After this, URDI sports adapters resolve team names and canonical keys internally. Run: cd unified-reference-data-interface && bash scripts/quickmerge.sh ''feat: absorb Tardis symbol parsing and sports normalization
    into URDI adapters'' --to-staging --agent', status: completed}
- {id: t1a-utl-scheduled-io, content: 'TRACK 1a — repo: unified-trading-library. Create unified_trading_library/service_framework/io_scheduled.py with class ScheduledIO(ServiceIO[BatchPayload, object]). Constructor params: interval_seconds=900, alignment=''utc_midnight''. Behaviour: sleep until next wall-clock-aligned timestamp (e.g. :00/:15/:30/:45 for 15-min), yield BatchPayload(date=today_utc_iso, extra={''aligned_ts'': iso_string}), after process() returns write result via StorageOutput asynchronously, handle SIGTERM by finishing current cycle then stopping. Also update service_framework/bootstrap.py: add live_trigger param to ServiceBootstrap; when live_trigger=''scheduled'' and --mode live, use ScheduledIO instead of LiveIO. Export ScheduledIO from service_framework/__init__.py and UTL __init__.py. This replaces the 357-line live_mode_handler.py pattern used in instruments-service and every other scheduled-live service. Run: cd unified-trading-library && bash scripts/quickmerge.sh
    ''feat: add ScheduledIO wall-clock aligned execution mode'' --to-staging --agent', status: completed}
- {id: t1b-utl-catalogue-writer, content: 'TRACK 1b — repo: unified-trading-library. Edit unified_trading_library/io/base_writer.py. Add optional catalogue_enabled=False to BaseGCSWriter.__init__(). When True, after every successful upload, call UCI ManifestWriter.write(ManifestRecord(service_name, dataset_id, date_from_path, record_count, written_at)). Services opt in by passing catalogue_enabled=True — zero explicit catalogue wiring in service code. Run: cd unified-trading-library && bash scripts/quickmerge.sh ''feat: add automatic ManifestWriter integration to BaseGCSWriter'' --to-staging --agent', status: completed}
- {id: t1c-utl-data-availability, content: 'TRACK 1c — repo: unified-trading-library. Edit unified_trading_library/startup_validation.py. Add function validate_data_availability(service_name, bucket, path_pattern, start_date, end_date) -> set[str]. Calls UDC DataCompletionChecker(bucket, path_pattern).get_completed_dates(start_date, end_date). Returns set of already-completed date strings. Emits DATA_GAP_DETECTED via log_event for missing dates. Export from UTL __init__.py. This replaces all service-level gap-detection logic. Run: cd unified-trading-library && bash scripts/quickmerge.sh ''feat: add validate_data_availability preflight helper'' --to-staging --agent', status: completed}
- {id: t1d-utl-exports, content: 'TRACK 1d — repo: unified-trading-library. Check unified_trading_library/__init__.py for: DateValidator, should_skip_date, TimestampAlignmentResult, validate_timestamp_date_alignment (all from unified-trading-library (domain_client/)). Add any missing re-exports so all are available as: from unified_trading_library import should_skip_date. Run: cd unified-trading-library && bash scripts/quickmerge.sh ''chore: re-export UDC date/timestamp helpers from UTL'' --agent', status: completed}
- {id: t2a-split-ccxt-service, content: 'TRACK 2a — repo: instruments-service. MUST happen before t2c. Split engine/venues/ccxt_service.py (866 lines, 34 from 900 hard block) into: (1) engine/venues/ccxt_service.py — CCXT client init, exchange loading, market loading (~300 lines), (2) engine/venues/ccxt_symbols.py — symbol parsing, instrument type mapping, leverage field extraction (~300 lines). Update all internal imports. Run: cd instruments-service && bash scripts/quality-gates.sh --skip-typecheck to verify.', status: completed}
- {id: t2b-split-cefi-processor, content: 'TRACK 2b — repo: instruments-service. MUST happen before t2c. Split engine/operations/instruments/processors/cefi_processor.py (827 lines) into: (1) engine/processors/cefi_market_data.py — spot/futures/options market data fetching from CCXT/Tardis (~400 lines), (2) engine/processors/cefi_metadata.py — CCXT metadata enrichment, Tardis-specific field enrichment (~400 lines). Update all imports.', status: completed}
- {id: t2c-delete-all-redundant, content: 'TRACK 2c — repo: instruments-service. Depends on t2a, t2b. Delete the following files/directories entirely — each has a specific replacement listed: (1) instruments_service/app/ (all 19 files, ~5,000 lines) — orchestration logic → new engine/orchestrator.py (t2g), infrastructure calls → UTL APIs; (2) instruments_service/schemas/parquet.py (581L) — replaced by UIC INSTRUMENTS_SCHEMA + UTL ParquetSchemaEnforcer; (3) instruments_service/monitors/ (~100L) — FreshnessMonitor wired inside UTL ScheduledIO; (4) instruments_service/io/ (~100L) — replaced by UTL BaseGCSWriter directly; (5) instruments_service/auth_s2s.py (6L) — inline create_s2s_auth_dependency at call site; (6) instruments_service/broadcast_sink.py (29L) — replaced by UTL event_sink; (7) instruments_service/utils/ most files (~300L) — UTL equivalents exist; (8) engine/validation/selective_validator.py (140L) — deleted, URDI handles credentials; (9) app/core/selective_validation.py (144L)
    — deleted, same reason; (10) app/core/instrument_validation.py (~199L) — deleted, venue allowlist is URDI adapter coverage; (11) app/core/processors/ duplicate set (~800L) — canonical set is engine/processors/; (12) instruments_service_modular_attempt.py — dead code; (13) sports/ entire directory (~1,000L) — only safe after TRACK 0c, verify URDI absorbs it first; (14) config/instrument_definitions.py + data/tickers.json — only safe after TRACK 0b; (15) config/ticker_lists.py (20L), config/equity_definitions.py (20L), config/data_type_config.py (13L), config/api_keys.py (8L) — all deprecated or trivially redundant constants; (16) engine/processors/canonical_key_generator.py (273L) — URDI returns canonical instrument_key, no service-level generation needed; (17) engine/processors/symbol_parser.py (435L) — only safe after TRACK 0c; (18) engine/processors/derived_fields_populator.py — merged into cefi_metadata.py (t2b) or deleted if URDI covers. Run: cd instruments-service && bash scripts/quality-gates.sh
    after each batch of deletions.', status: completed}
- {id: t2d-strip-service-config, content: 'TRACK 2d — repo: instruments-service. Replace instruments_service/config/service_config.py (337 lines) with a ~30-line version. Keep ONLY: service_name=''instruments-service'', enable_ccxt_integration=True (env: ENABLE_CCXT_INTEGRATION), config_store_bucket='''' (env: CONFIG_STORE_BUCKET), catalogue_path_override='''' (env: INSTRUMENTS_CATALOGUE_PATH). Remove everything else: all per-category bucket fields (UTL cloud_constants.get_bucket_name() constructs instruments-store-{category}-{gcp_project_id} automatically), all DeFi API URL fields (these are URDI adapter config injected via UCI provider manifest at runtime, not service config), all deployment_id/shard_launched_at fields (UTL ServiceBootstrap state), all ccxt caching/batch size fields. Check config/venue_config.py (244L): if TradFiInstrument/UnifiedInstrumentConfig are superseded by UIC InstrumentRecord, delete it; otherwise keep temporarily and add to backlog.', status: completed}
- {id: t2e-slim-config-reloaders, content: 'TRACK 2e — repo: instruments-service. Depends on t0b (UAC ticker registry). Edit instruments_service/config_reloaders.py (229 lines). (1) Replace module-level mutable global lists (_active_subscription_list etc) with a proper class holding instance state. (2) Replace _load_ticker_universe_fallback() which reads local tickers.json with: from unified_api_contracts.registry import TRADFI_TICKER_UNIVERSE (added in t0b). (3) Simplify to ~80-100 lines using DomainConfigReloader from UTL which already handles the cloud reload pattern.', status: completed}
- {id: t2f-expand-urdi-provider, content: 'TRACK 2f — repo: instruments-service. Depends on t0c. Edit instruments_service/adapters/urdi_reference_provider.py. Expand URDI_SUPPORTED_VENUES from 9 venues to ALL venues URDI has adapters for. Confirmed URDI adapter list (from unified-reference-data-interface/unified_reference_data_interface/adapters/): binance, bybit, okx, deribit, coinbase, hyperliquid, polymarket, polygon, tardis, databento, ibkr, uniswap_v2, uniswap_v3, uniswap_v4, aave_v3, balancer, curve, morpho, lido, etherfi, euler, fluid, ethena, api_football, betfair. Add fetch_instruments_for_all_venues() method that calls URDI for all configured venues with NO fallback — if a venue has no URDI adapter, log a warning and skip it. instruments-service has zero direct external API calls.', status: completed}
- {id: t2g-build-engine-orchestrator, content: 'TRACK 2g — repo: instruments-service. Depends on t2c, t2f. Create instruments_service/engine/orchestrator.py (~150-200 lines). This is the entire processing logic of the service. Method signature: async def process_instruments(date: str, categories: list[str], redo_all: bool = False) -> dict[str, int]. Logic: (1) for each venue in configured_venues: if should_skip_date(venue, date): continue (from unified_domain_client), (2) call urdi_reference_provider.fetch_instruments_for_all_venues(venues, date) — returns list[InstrumentRecord] already canonical, (3) if enable_ccxt_integration: call engine/processors/cefi_metadata.enrich(records) to add CCXT leverage/margin fields not present in InstrumentRecord, (4) df = pd.DataFrame([r.model_dump() for r in records]), (5) DomainValidationService(''instruments'').validate(df) (from unified_domain_client — flags anomalies via log_event), (6) ParquetSchemaEnforcer(INSTRUMENTS_SCHEMA).validate_dataframe(df)
    (from unified_trading_library — blocks bad writes), (7) BaseGCSWriter(catalogue_enabled=True).write(df, path=''instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet''). Return instrument counts by category. No threading. No direct cloud SDK imports. No external API calls.', status: completed}
- {id: t2h-build-cli, content: 'TRACK 2h — repo: instruments-service. Depends on t2g, t1a. Delete: cli/live_mode_handler.py (357L), cli/handlers/instrument_handler.py (492L), cli/parser.py (309L), cli/base_handler.py (122L), cli/handlers/__init__.py (69L). Create cli/handlers/instruments_handler.py (~50 lines): class InstrumentsHandler(UnifiedServiceHandler) with async preflight() that calls validate_data_availability(service_name=''instruments-service'', bucket=..., path_pattern=''instrument_availability/by_date/day={date}/...'', start_date=..., end_date=...) from UTL and async process(payload: BatchPayload) -> object that calls engine/orchestrator.process_instruments(payload.date, payload.categories, redo_all=payload.extra.get(''redo_all'', False)). Update cli/main.py to ~20 lines: ServiceBootstrap(service_name=''instruments-service'', operations={''instruments'': InstrumentsHandler}, config=get_config(), live_trigger=''scheduled'', extra_args_fn=lambda p: p.add_argument(''--redo-all'',
    action=''store_true'') or p.add_argument(''--venues'', nargs=''+'')).run(). No --operation aggregate.', status: completed}
- {id: t2i-qg-and-quickmerge, content: 'TRACK 2i — repo: instruments-service. Run: cd instruments-service && bash scripts/quality-gates.sh. Fix all ruff, basedpyright, and coverage failures. Check file sizes: all files must be under 700 lines (warn), none over 900 (block). Then: cd instruments-service && bash scripts/quickmerge.sh ''feat!: refactor instruments-service as canonical service template — URDI primary path, UTL framework, zero service-level infrastructure'' --to-staging --agent', status: in_progress}
isProject: false
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_operational_validation_2026_04_15.plan.md](./consolidated_operational_validation_2026_04_15.plan.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Instruments-Service Template Refactor

## Vision: What This Service Should Be

The canonical instruments-service after this refactor has one job:

> For a given date and set of categories, ask URDI for canonical instrument records, optionally enrich with CCXT
> metadata, validate, and write to storage.

Everything else — scheduling, batch/live mode, CLI arg parsing, storage routing, catalogue writes, data availability
checking, freshness monitoring, credential management, canonicalization, symbol parsing, sports normalization — is
handled by UTL, UDC, UCI, UAC, or URDI. The service contains no knowledge of external APIs, cloud SDKs, or
infrastructure.

The resulting ~20-file service is the template for all other services in the system.

---

## Architecture: Role of Each Library

Understanding this hierarchy is essential before touching any code:

- **UAC (`unified-api-contracts`)** — SSOT for venue names, canonical mappings, domain enums, ticker registries. Nothing
  venue-related gets defined outside UAC.
- **UIC (`unified-api-contracts, internal`)** — owns `InstrumentRecord` schema, `INSTRUMENTS_SCHEMA` for parquet. The
  canonical output type.
- **UCI (`unified-cloud-interface`)** — cloud-agnostic storage/queue/secret clients, `ManifestWriter`/`ManifestReader`
  for data catalogue.
- **URDI (`unified-reference-data-interface`)** — 28+ per-venue adapters that fetch raw data and return
  `InstrumentRecord[]` already in canonical format. URDI is the ONLY path for external API calls. It handles its own
  credentials via UTL's standard credential injection — instruments-service never sees API keys.
- **UDC (`unified-trading-library (domain_client/)`)** — `DataCompletionChecker`, `DateValidator`, `should_skip_date`,
  `TimestampAlignmentResult`, `DomainValidationService`. All data-availability and validation logic lives here.
- **UTL (`unified-trading-library`)** — `ServiceBootstrap`, `ServiceCLI`, `BatchIO`, `ScheduledIO`, `BaseGCSWriter`,
  `ParquetSchemaEnforcer`, `FreshnessMonitor`, `DomainConfigReloader`. All cross-cutting service infrastructure.

---

## What Is Wrong Now (Current State)

### Structural duplications

- Two orchestration trees: `app/core/instruments_service.py` (827L, mixin-composed) AND
  `engine/operations/instruments/orchestrator.py` (OrchestratorBase). CLI only uses `app/core`.
- Two processor sets: `app/core/processors/` AND `engine/processors/`. `symbol_parser.py` duplicated at ~450L each.
- Two storage implementations: `app/core/cloud_instrument_storage.py` (476L) AND `io/writer.py` (BaseGCSWriter
  subclass).

### Service is doing URDI's and UAC's job

- `engine/processors/canonical_key_generator.py` (273L) — URDI returns `InstrumentRecord` with `instrument_key` already
  canonical. Redundant.
- `engine/processors/symbol_parser.py` (435L) — Tardis symbol parsing. The URDI Tardis adapter should own this.
- `sports/` directory (7 files, ~1,000L) — sports team/league normalization. URDI's `api_football.py` and `betfair.py`
  should own this.
- UAC naming inconsistency (lowercase Tardis names vs uppercase canonical names) forced local normalizer shims.

### Config is 6× too large

`config/` has 7 files, ~~690 lines. Legitimate service config is 4 fields (~~30 lines). Everything else belongs in UTL
(`cloud_constants`), UCI (provider URLs), UAC registry (ticker lists), or UTL `ServiceBootstrap` (deployment state).

### Batch/live duplication

`live_mode_handler.py` (357L) re-implements: wall-clock alignment, threading, Queue-based async persistence,
`while True` loop. This exact pattern exists in multiple services. UTL's `ScheduledIO` absorbs it once for all.

### CLI boilerplate

`cli/parser.py` (309L) re-defines args already in UTL `ServiceCLI` (`STANDARD_MODES`, `STANDARD_CATEGORIES`,
`--log-level`, etc.). `cli/base_handler.py` (122L) duplicates UTL `BaseModeHandler`.

### No aggregator needed

The aggregator (`engine/operations/aggregate/aggregator.py`, 232L) compacted per-date/venue parquet files into a daily
snapshot. With `DataCompletionChecker` (UDC) checking which dates have data and `ManifestWriter/ManifestReader` (UCI)
providing the catalogue view, downstream services can query what's available directly. The aggregator and its handler
are removed entirely.

### Validation duplicated

- `engine/validation/selective_validator.py` (140L) + `app/core/selective_validation.py` (144L) — validate API keys.
  With URDI as sole API path, instruments-service has no API keys to validate. Both deleted.
- `app/core/instrument_validation.py` (~199L) — venue allowlist checks. URDI adapter coverage IS the allowlist. Deleted.
- `schemas/parquet.py` (581L) — duplicate of UIC `INSTRUMENTS_SCHEMA`. Deleted.
- Correct call: `DomainValidationService("instruments").validate(df)` from UDC +
  `ParquetSchemaEnforcer(INSTRUMENTS_SCHEMA)` from UTL.

---

## Target Directory Structure

```
instruments_service/
├── __init__.py
├── config/
│   ├── __init__.py                 # exports get_config, instruments_config
│   └── service_config.py           # ~30 lines: 4 fields only (see below)
├── config_reloaders.py             # ~80 lines: DomainConfigReloader for subscription list
├── engine/
│   ├── __init__.py
│   ├── orchestrator.py             # ~150 lines: the entire processing logic
│   └── processors/
│       ├── __init__.py
│       ├── cefi_market_data.py     # split from cefi_processor.py (~400L)
│       └── cefi_metadata.py        # CCXT enrichment fields post-URDI (~400L)
└── adapters/
    ├── __init__.py
    └── urdi_reference_provider.py  # expanded to cover all 25+ URDI-supported venues
└── cli/
    ├── __init__.py
    ├── main.py                     # ~20 lines: ServiceBootstrap entry only
    └── handlers/
        ├── __init__.py
        └── instruments_handler.py  # ~50 lines: InstrumentsHandler(UnifiedServiceHandler)
```

**Note on `engine/venues/`:** `ccxt_service.py` (866L, must split → `ccxt_service.py` + `ccxt_symbols.py`) and
`venue_adapter_loader.py` may be retained temporarily if the CCXT metadata enrichment path still needs them. Once URDI
fully covers all venues, they are deleted too.

---

## Files Deleted and Why

| File                                                     | Lines    | Reason                                                                   |
| -------------------------------------------------------- | -------- | ------------------------------------------------------------------------ |
| `instruments_service/app/` (all 19 files)                | ~5,000   | Orchestration → engine/orchestrator.py; infrastructure → UTL             |
| `schemas/parquet.py`                                     | 581      | UIC owns INSTRUMENTS_SCHEMA                                              |
| `monitors/`                                              | ~100     | FreshnessMonitor wired inside UTL ScheduledIO                            |
| `io/`                                                    | ~100     | Use UTL BaseGCSWriter directly                                           |
| `auth_s2s.py`                                            | 6        | Inline at call site                                                      |
| `broadcast_sink.py`                                      | 29       | Use UTL event_sink                                                       |
| `utils/` (most)                                          | ~300     | UTL has equivalents                                                      |
| `engine/processors/canonical_key_generator.py`           | 273      | URDI returns canonical instrument_key                                    |
| `engine/processors/symbol_parser.py`                     | 435      | Moves to URDI tardis.py adapter (Track 0c)                               |
| `engine/processors/derived_fields_populator.py`          | varies   | Merged into cefi_metadata.py                                             |
| `app/core/processors/`                                   | ~800     | Duplicate; engine/processors/ is canonical                               |
| `instruments_service_modular_attempt.py`                 | varies   | Dead code                                                                |
| `sports/` (7 files)                                      | ~1,000   | Moves to URDI api_football.py/betfair.py (Track 0c)                      |
| `config/instrument_definitions.py` + `data/tickers.json` | ~42+data | Moves to UAC registry (Track 0b)                                         |
| `config/ticker_lists.py`                                 | 20       | Deprecated re-export                                                     |
| `config/equity_definitions.py`                           | 20       | Deprecated re-export                                                     |
| `config/data_type_config.py`                             | 13       | Duplicates service_config defaults                                       |
| `config/api_keys.py`                                     | 8        | Duplicates service_config defaults                                       |
| `engine/validation/selective_validator.py`               | 140      | URDI handles credentials                                                 |
| `app/core/selective_validation.py`                       | 144      | Duplicate, same reason                                                   |
| `app/core/instrument_validation.py`                      | ~199     | Venue allowlist is URDI adapter coverage                                 |
| `engine/operations/aggregate/aggregator.py`              | 232      | Aggregation replaced by DataCompletionChecker + ManifestReader catalogue |
| `cli/handlers/aggregate_handler.py`                      | varies   | No --operation aggregate                                                 |
| `cli/live_mode_handler.py`                               | 357      | Replaced by UTL ScheduledIO                                              |
| `cli/handlers/instrument_handler.py`                     | 492      | Replaced by InstrumentsHandler(UnifiedServiceHandler)                    |
| `cli/parser.py`                                          | 309      | UTL ServiceCLI owns standard args                                        |
| `cli/base_handler.py`                                    | 122      | Use UTL BaseModeHandler                                                  |
| `cli/handlers/__init__.py`                               | 69       | ServiceBootstrap does dispatch                                           |

---

## File Size Compliance (700-line warn, 900-line block)

Two files must be split BEFORE the main deletions (Tracks 2a, 2b) to avoid breaching 900 lines when app/core logic
merges in:

- `**engine/venues/ccxt_service.py` (866L) → split into `ccxt_service.py` + `ccxt_symbols.py`
- `**engine/processors/cefi_processor.py` (827L) → split into `cefi_market_data.py` + `cefi_metadata.py`

---

## API Credential Handling

instruments-service has **zero direct external API calls** after this refactor. The credential flow is:

```
UTL ServiceBootstrap
  → resolves credentials from Secret Manager via get_secret_client()
  → injects into URDI adapter constructors at startup
URDI adapters
  → use injected credentials to call external APIs
  → return InstrumentRecord[] to instruments-service
instruments-service
  → receives InstrumentRecord[] — never sees raw API credentials or responses
```

This is the standardised UTL credential injection pattern used by all services. The `selective_validator.py` files
(which validate API keys in the service) are deleted because the service no longer needs to know which credentials are
required for which venues.

---

## The Canonical Process Flow (Post-Refactor)

```python
# Everything instruments-service does, in order:

async def process(payload: BatchPayload) -> object:
    # 1. Skip dates before venue's available_from
    records: list[InstrumentRecord] = []
    for venue in configured_venues:
        if should_skip_date(venue, payload.date):          # UDC
            continue
        records.extend(await urdi_provider.fetch(venue, payload.date))  # URDI → canonical InstrumentRecord[]

    # 2. Optional CCXT metadata enrichment (leverage, margin fields not in InstrumentRecord)
    if config.enable_ccxt_integration:
        records = cefi_metadata.enrich(records)            # engine/processors/cefi_metadata.py

    # 3. Validate
    df = pd.DataFrame([r.model_dump() for r in records])
    DomainValidationService("instruments").validate(df)    # UDC — logs anomalies
    ParquetSchemaEnforcer(INSTRUMENTS_SCHEMA).validate_dataframe(df)  # UTL — blocks bad writes

    # 4. Write (catalogue write is automatic via catalogue_enabled=True in BaseGCSWriter)
    BaseGCSWriter(catalogue_enabled=True).write(df, path=...)

    return df
```

No threading. No Queue. No wall-clock math. No direct cloud SDK imports. No API keys. No canonical key generation. No
aggregation.

---

## Service Config (4 Fields)

```python
class InstrumentsServiceConfig(UnifiedCloudConfig):
    service_name: str = "instruments-service"
    enable_ccxt_integration: bool = Field(default=True, env="ENABLE_CCXT_INTEGRATION")
    config_store_bucket: str = Field(default="", env="CONFIG_STORE_BUCKET")
    catalogue_path_override: str = Field(default="", env="INSTRUMENTS_CATALOGUE_PATH")
```

Bucket names: UTL `cloud_constants.get_bucket_name("instruments", category)` constructs
`instruments-store-{category}-{gcp_project_id}` automatically. DeFi API URLs: URDI adapters read their own URLs from UCI
provider manifest at startup. Deployment state: UTL ServiceBootstrap carries `deployment_id`, `shard_launched_at`.

---

## CLI Surface (2 Files)

```python
# cli/main.py — ~20 lines
ServiceBootstrap(
    service_name="instruments-service",
    operations={"instruments": InstrumentsHandler},
    config=get_config(),
    live_trigger="scheduled",          # → UTL picks ScheduledIO for --mode live
    extra_args_fn=lambda p: (
        p.add_argument("--redo-all", action="store_true"),
        p.add_argument("--venues", nargs="+"),
    ),
).run()
```

```python
# cli/handlers/instruments_handler.py — ~50 lines
class InstrumentsHandler(UnifiedServiceHandler):
    async def preflight(self) -> None:
        self._completed = await validate_data_availability(  # UTL
            service_name="instruments-service",
            bucket=cloud_constants.get_bucket_name("instruments"),
            path_pattern="instrument_availability/by_date/day={date}/...",
            start_date=self.runtime.start_date,
            end_date=self.runtime.end_date,
        )

    async def process(self, payload: BatchPayload) -> object:
        if payload.date in self._completed and not payload.extra.get("redo_all"):
            return None  # skip — already done
        return await engine_orchestrator.process_instruments(
            date=payload.date,
            categories=payload.categories,
        )
```

---

## Execution Order

Tracks must be completed in order. Each track is a separate quickmerge in its repo.

1. **Track 0a** — UAC naming fix (`unified-api-contracts`)
2. **Track 0b** — UAC ticker registry (`unified-api-contracts`)
3. **Track 0c** — URDI symbol parsing + sports absorption (`unified-reference-data-interface`)
4. **Track 1a** — UTL ScheduledIO (`unified-trading-library`)
5. **Track 1b** — UTL BaseGCSWriter catalogue integration (`unified-trading-library`)
6. **Track 1c** — UTL validate_data_availability (`unified-trading-library`)
7. **Track 1d** — UTL UDC re-exports (`unified-trading-library`)
8. **Track 2a** — Split ccxt_service.py (`instruments-service`) — before any deletions
9. **Track 2b** — Split cefi_processor.py (`instruments-service`) — before any deletions
10. **Track 2c** — Delete all redundant files (`instruments-service`)
11. **Track 2d** — Strip service_config.py to 4 fields (`instruments-service`)
12. **Track 2e** — Slim config_reloaders.py (`instruments-service`)
13. **Track 2f** — Expand URDI reference provider to all venues (`instruments-service`)
14. **Track 2g** — Build engine/orchestrator.py (`instruments-service`)
15. **Track 2h** — Build new CLI surface (`instruments-service`)
16. **Track 2i** — Quality gates pass + quickmerge (`instruments-service`)

---

## Expected Outcome

- instruments-service: ~104 Python files → ~18-20 files; ~12,000+ lines → ~1,800 lines
- `config/` → 2 files, ~40 lines, 4 fields
- `cli/` → 2 files, ~70 lines total
- `engine/` → 4 files: orchestrator.py, cefi_market_data.py, cefi_metadata.py, (optionally ccxt_service.py +
  ccxt_symbols.py until URDI fully covers all CCXT venues)
- `adapters/` → 1 file: urdi_reference_provider.py
- No batch/live distinction in service code — UTL `ScheduledIO`/`BatchIO` selected by framework
- No external API calls, no credential management, no canonicalization, no aggregation
- No validation logic — UDC `DomainValidationService("instruments")` + UTL `ParquetSchemaEnforcer`
- Config is 4 fields. CLI is 20 lines. Handler is 50 lines. Engine is 150 lines.
- Template is directly portable: copy these 4 directories into any other service
