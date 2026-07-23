---
doc_type: codex-ssot
title: Service Orchestration Patterns
summary: >-
  14 service orchestration patterns from the instruments-service + MTDS refactors (34,765L→850L) — import contract,
  handler-orchestrator split, ServiceBootstrap entry, flat config, single adapter, error-by-category, preflight,
  async-gather, plus the HARD per-shard try/finally cleanup rule; instruments-service is the reference impl.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [service-structure, instruments, mtds, refactor, execution, uac]
related:
  [
    /codex/06-coding-standards/service-structure-standards.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/06-coding-standards/cli-convention.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
created: 2026-03-27
authoritative_for:
  [
    service orchestration patterns (handler-orchestrator split + library role boundaries),
    batch-service per-shard cleanup try/finally rule,
  ]
referenced_by:
  [
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/06-coding-standards/README.md,
    /codex/06-coding-standards/adapter-finalization-contract.md,
    /codex/06-coding-standards/cli-convention.md,
    /codex/06-coding-standards/data-engine-selection.md,
    /codex/06-coding-standards/service-structure-standards.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Service Orchestration Patterns

14 patterns extracted from the instruments-service and market-tick-data-service refactorings. Every service in the
Unified Trading System MUST follow these patterns. The instruments-service is the canonical reference implementation.
Patterns 11-14 capture additional lessons from the MTDS refactoring (34,765L to 850L).

---

## 1. Import Contract (Enforced in Every Module)

Every service module declares an import contract docstring at the top, listing exactly which libraries it imports from.
Services import from at most two sources: UTL (framework) and T0 contracts (UAC/UIC domain types). No direct imports
from UEI, UCI, UMI, UDC, or UCC — if something is needed from those libraries, it comes through UTL's re-exported
surface.

```python
"""Instruments engine orchestrator — the entire processing logic of the service.

IMPORT CONTRACT
---------------
This module imports from:
  1. unified_trading_library (UTL) — all infrastructure, framework, validation, storage
  2. unified_api_contracts (T0) — domain types (VenueMapping)

No direct imports from UEI, UCI, UMI, UDC, UCC. If something is needed from
those libraries, it must come through UTL's re-exported surface.
"""
```

**Why:** Prevents dependency spaghetti. Every service has exactly one framework dependency (UTL) and one schema
dependency (T0 contracts). UTL owns the re-export surface for lower-tier libraries.

**Reference:** `instruments-service/instruments_service/engine/orchestrator.py:1-21`

---

## 2. Handler-Orchestrator Split

Every service operation splits into two layers:

| Layer            | Class/Module                | Responsibility                                           |
| ---------------- | --------------------------- | -------------------------------------------------------- |
| **Handler**      | `UnifiedServiceHandler`     | Lifecycle, preflight, credentials, skip-sets, mode logic |
| **Orchestrator** | Pure functions in `engine/` | Stateless processing — takes inputs, returns results     |

The handler fetches credentials once in `preflight()`, then injects them into the orchestrator on each `process()` call.
The orchestrator never touches Secret Manager, storage availability checks, or CLI args directly.

```python
class InstrumentsHandler(UnifiedServiceHandler):
    def __init__(self, runtime: ServiceRuntime) -> None:
        super().__init__(runtime)
        self._completed_dates: set[str] = set()
        self._api_keys: dict[str, str] = {}

    async def preflight(self) -> None:
        # 1. Validate API keys (fail shard if missing)
        self._api_keys = validate_api_keys_for_venues(
            venues=active_venues,
            project_id=self.runtime.gcp_project_id or None,
        )
        # 2. Check which dates already have data
        self._completed_dates = validate_data_availability(...)

    async def process(self, payload: BatchPayload) -> object:
        if date in self._completed_dates and not redo_all:
            return None  # skip
        return await engine_orchestrator.process_instruments(
            date=date, categories=categories,
            redo_all=redo_all, api_keys=self._api_keys,
        )
```

**Why:** Testability. The orchestrator is unit-testable with zero mocking of cloud services. The handler is
integration-tested with emulators.

**Reference:** `instruments-service/instruments_service/cli/handlers/instruments_handler.py`

---

## 3. ServiceBootstrap Entry Point (~50 Lines)

The CLI entry point is a thin `ServiceBootstrap` call. Standard args (`--mode`, `--start-date`, `--end-date`,
`--asset-group`, `--log-level`) come from `ServiceCLI` inside UTL. The service adds only its own extra args.

```python
def main_service_cli() -> None:
    ServiceBootstrap(
        service_name=_SERVICE_NAME,
        operations={"instruments": InstrumentsHandler},
        config=get_config(),
        live_trigger="scheduled",
        interval_seconds=900,
        extra_args_fn=_add_service_args,
    ).run()
```

Extra args are registered via a callback, not by subclassing the parser:

```python
def _add_service_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--redo-all", action="store_true", default=False)
    parser.add_argument("--venues", nargs="+", default=None)
```

**Why:** Every service has an identical startup shape. `ServiceBootstrap` owns BatchIO/ScheduledIO routing, signal
handling, and health checks. Services never reimplement these.

**Reference:** `instruments-service/instruments_service/cli/main.py`

---

## 4. Config Flattened to 4-7 Fields

Service config inherits `UnifiedCloudConfig` and adds only service-specific tuning knobs. Everything else is resolved by
UTL, UCI, or the relevant interface at runtime.

```python
class InstrumentsServiceConfig(UnifiedCloudConfig):
    """Service configuration — 4 fields only."""
    service_name: str = Field(default="instruments-service")
    enable_ccxt_integration: bool = Field(default=True)
    catalogue_path_override: str = Field(default="")
    instruments_bucket_prefix: str = Field(default="instruments-store")
```

What is NOT in service config:

- Bucket names — resolved by `UTL get_bucket_name("instruments", category)`
- API URLs — instruments-service adapters read their own URLs from UCI provider manifest
- Deployment state — owned by `UTL ServiceBootstrap`
- Venue lists — owned by `UAC VenueMapping`

**Why:** Eliminates config duplication. When a bucket naming convention changes, it changes in one place (UTL), not in
21 service configs.

**Reference:** `instruments-service/instruments_service/config/service_config.py`

---

## 5. Single Adapter via Unified Interface

Each service has one adapter file per external data path. The adapter calls the interface; the interface handles vendor
routing, API key injection, and response normalisation. The adapter owns only orchestration logic: which venues to
fetch, how to gather results, and error policy.

```python
async def fetch_instruments_for_all_venues(
    venues: list[str],
    instrument_type: str | None = None,
    api_keys: dict[str, str] | None = None,
) -> list[InstrumentRecord]:
    # instruments-service owns: venue→adapter mapping, credential routing, response normalisation
    # This file owns: parallelism, dedup, error policy
    adapter = get_adapter_for_canonical_venue(canonical, api_key=api_key)
    records = await adapter.get_instruments(instrument_type=instrument_type)
```

The adapter maintains no local translation tables. All naming translation
(`canonical venue -> instruments-service adapter key`) and credential routing (`adapter key -> data source -> API key`)
is owned by the interface itself.

**Why:** Services never know about vendor-specific details. Adding a new venue means adding an adapter in
instruments-service, not touching the service.

**Reference:** `instruments-service/instruments_service/adapters/urdi_reference_provider.py`

---

## 6. Delete First, Then Centralise

When migrating logic from a service to a library:

1. Delete the local copy entirely
2. Import from the library
3. If the library is missing the feature, add it to the library first

No shims. No re-exports of old paths. No deprecation wrappers. Clean break.

**Anti-pattern (forbidden):**

```python
# DO NOT DO THIS
try:
    from unified_trading_library import VenueMapping
except ImportError:
    from instruments_service.legacy.venue_mapping import VenueMapping
```

**Correct:**

```python
from unified_api_contracts import VenueMapping
```

**Why:** Shims create invisible dependency chains that break silently when the shim target changes. Fail loud at import
time so the developer knows immediately.

---

## 7. Venue Availability as Lookup, Not Configuration

Venue launch dates live in `UAC VenueMapping`. Services query availability at runtime, never hardcode venue lists or
launch dates.

```python
_VENUE_MAPPING = VenueMapping()

def is_venue_available(venue: str, date: str) -> bool:
    return _VENUE_MAPPING.is_venue_available_on_date(venue, date)

# In the orchestrator:
active_venues = [v for v in venues if is_venue_available(v, date)]
```

**Why:** When a new venue goes live, update one record in UAC. All services pick it up automatically on the next run. No
service deployments needed.

**Reference:** `instruments-service/instruments_service/engine/orchestrator.py:48-70`

---

## 8. Error Handling by Category

Errors are classified into three categories with distinct handling:

| Category               | Examples                                     | Action                                      |
| ---------------------- | -------------------------------------------- | ------------------------------------------- |
| **Network errors**     | `ConnectionError`, `TimeoutError`, `OSError` | Log WARNING, return empty (BatchIO retries) |
| **Adapter errors**     | `ValueError`, `NotImplementedError`          | Log ERROR/DEBUG, skip venue                 |
| **Programming errors** | `TypeError`, `AttributeError`                | Propagate — fail the shard                  |

```python
async def _fetch_one(canonical: str, adapter_key: str) -> list[InstrumentRecord]:
    try:
        adapter = get_adapter_for_canonical_venue(canonical, api_key=api_key)
        records = await adapter.get_instruments(instrument_type=instrument_type)
        return records
    except NotImplementedError:
        logger.debug("instruments-service[%s]: instrument_type=%r not supported", canonical, instrument_type)
        return []
    except (OSError, ConnectionError, TimeoutError) as exc:
        logger.warning("instruments-service[%s]: network error (retryable): %s", canonical, exc)
        return []
    except ValueError as exc:
        logger.error("instruments-service[%s]: adapter error: %s", canonical, exc)
        return []
    # Programming errors propagate — fail the shard
```

**Why:** Network errors are transient and retryable. Adapter errors are venue-scoped and should not block other venues.
Programming errors indicate bugs that must be fixed, not silently swallowed.

**Reference:** `instruments-service/instruments_service/adapters/urdi_reference_provider.py:81-98`

See also: `unified-trading-pm/codex/04-architecture/shard-level-failure-isolation.md`

---

## 9. Preflight as Contract Enforcement

`preflight()` validates ALL preconditions before any processing begins. If a precondition fails, the shard fails
immediately with a clear error — not after silently producing partial or empty results.

Preflight checks:

1. **API keys exist** — `validate_api_keys_for_venues()` from UTL, backed by Secret Manager
2. **Storage writable** — bucket name resolves, write test succeeds
3. **Data availability queryable** — `validate_data_availability()` determines skip-set

```python
async def preflight(self) -> None:
    # Fail fast if keys are missing — don't discover this mid-run
    try:
        self._api_keys = validate_api_keys_for_venues(
            venues=active_venues,
            project_id=self.runtime.gcp_project_id or None,
        )
    except Exception as exc:
        logger.error("API key validation failed: %s", exc)
        raise  # shard fails before any fetch
```

In `CLOUD_MOCK_MODE`, key validation is a no-op (no real Secret Manager available).

**Why:** Fail-fast eliminates wasted compute. A 2-hour batch run that fails in the last minute because of a missing API
key is unacceptable.

**Reference:** `instruments-service/instruments_service/cli/handlers/instruments_handler.py:46-93`

---

## 10. Async Gather for Parallel Fetches

Each venue is independent. Use `asyncio.gather()` with per-venue error isolation so one venue's failure does not block
the others.

```python
results = await asyncio.gather(*[_fetch_one(c, k) for c, k in fetch_list])
return [record for batch in results for record in batch]
```

Each `_fetch_one` coroutine has its own try/except (see Pattern 8), so a network timeout on one venue returns `[]` for
that venue while the others succeed. The gather runs all venues concurrently.

**Why:** Sequential fetches across 30+ venues would take minutes. Parallel fetches complete in the time of the slowest
single venue. Per-venue error isolation ensures partial success is preserved.

**Reference:** `instruments-service/instruments_service/adapters/urdi_reference_provider.py:100`

---

## Library Role Boundaries

These four libraries form the dependency spine of every service. Their roles are strictly separated.

### UTL (unified-trading-library) — Smart Router + Service Framework

UTL is the service framework. It provides infrastructure and routing, never domain logic.

- `ServiceBootstrap`, `UnifiedServiceHandler`, `BatchPayload`, `ServiceRuntime`
- `get_data_sink()`, `get_bucket_name()`, `ManifestWriter`
- `DomainValidationService`, `ParquetSchemaEnforcer`
- `validate_api_keys_for_venues()`, `validate_data_availability()`
- `log_event()` (re-exported from UEI)
- Cloud routing (GCS/S3/local dispatch)

### UAC internal (unified_api_contracts.internal) — Internal Domain Schemas + Validation Rules

`unified_api_contracts.internal` owns all internal domain types that flow between services.

- `InstrumentRecord`, `CanonicalTradeTick`, `CanonicalFill`
- `CandleSchemaConfig`, tick quality rules
- Domain enums: `MarketCategory`, `AssetClass`, `InstrumentType`
- All Pydantic models for inter-service communication

### UAC (unified-api-contracts) — External Vendor Schema Normalisation

UAC owns the mapping from external vendor formats to canonical types.

- `VenueMapping` — venue launch dates, canonical name mapping
- Databento, Tardis, DeFi provider schemas
- Normalisation functions per source
- `classify_venue_error()` for adapter error classification

Import rule: services use `from unified_api_contracts import X` (root facades only). Never import from
`unified_api_contracts.canonical.*` or `unified_api_contracts.normalize_utils.*`.

### UMI (market-tick-data-service/market_tick_data_service/market_interface) — Market Data Fetching

UMI is for market data only. It provides vendor adapters for downloading price/trade data.

- WebSocket feeds, REST download orchestration
- Vendor adapters (Databento, Tardis, Hyperliquid, etc.)
- VCR cassette recording for deterministic replay

Services use UMI for market data, instruments-service for reference data. Never the other way around.

---

## Reference Implementations

The instruments-service demonstrates Patterns 1-10 in a working service. The market-tick-data-service demonstrates the
full Pattern 1-14 lifecycle (including the refactoring patterns 11-14 that produced an 850-line service from 34,765
lines).

### instruments-service (Patterns 1-10)

| File                                                      | Patterns                                                          |
| --------------------------------------------------------- | ----------------------------------------------------------------- |
| `instruments_service/cli/main.py`                         | 3 (ServiceBootstrap)                                              |
| `instruments_service/cli/handlers/instruments_handler.py` | 2 (Handler), 9 (Preflight)                                        |
| `instruments_service/engine/orchestrator.py`              | 1 (Import Contract), 7 (Venue Availability), 8 (Error Categories) |
| `instruments_service/adapters/urdi_reference_provider.py` | 5 (Single Adapter), 8 (Error Categories), 10 (Async Gather)       |
| `instruments_service/config/service_config.py`            | 4 (Flat Config)                                                   |

Patterns 6 (Delete First) applies during refactoring, not as a file in the service.

### market-tick-data-service (Patterns 1-14)

| File                                                         | Patterns                                                          |
| ------------------------------------------------------------ | ----------------------------------------------------------------- |
| `market_tick_data_service/cli/main.py`                       | 3 (ServiceBootstrap)                                              |
| `market_tick_data_service/cli/handlers/tick_data_handler.py` | 2 (Handler), 9 (Preflight), 11 (ApiKeyReloader)                   |
| `market_tick_data_service/engine/orchestrator.py`            | 1 (Import Contract), 7 (Venue Availability), 8 (Error Categories) |
| `market_tick_data_service/adapters/umi_market_provider.py`   | 5 (Single Adapter via UMI), 10 (Async Gather)                     |
| `market_tick_data_service/config/service_config.py`          | 4 (Flat Config)                                                   |
| `pyproject.toml`                                             | 13 (Dependency Cleanup)                                           |

---

## Import Contract: Direct Dependency Exceptions

The Import Contract (Pattern 1) states services import from UTL and T0 contracts only. However, some libraries are
direct dependencies that cannot be routed through UTL:

- **`unified_config_interface`** — BOOTSTRAP exception. Service config extends `UnifiedCloudConfig` directly
  (`config/service_config.py`). This is the only approved `os.environ` path (via `UnifiedCloudConfig` internals).
- **`unified_market_interface`** — Direct dep for market-data services. `get_market_adapter(venue)` is called from the
  service adapter layer. UMI is credentials-free so no Secret Manager wiring needed.
- **`unified_trading_library.events`** — Direct dep for `config_reloaders.py` (hot-reload subscriptions). UTL re-exports
  `log_event` but reloader setup needs the full UEI surface.

These MUST be declared in the workspace manifest with a `note` field explaining why each is a direct (not transitive)
dependency. Example:

```json
{
  "name": "unified-config-interface",
  "note": "config/service_config.py extends UnifiedCloudConfig — bootstrap exception"
}
```

---

## 11. Actual Library API Signatures (Reference)

Lessons learned from the market-tick-data-service refactoring (34,765L to 850L). These are the REAL signatures — do not
guess, do not hallucinate parameters that do not exist.

### ServiceRuntime (UTL `service_runtime.py`)

| Attribute        | Type                   | Notes                                         |
| ---------------- | ---------------------- | --------------------------------------------- |
| `category`       | `list[MarketCategory]` | NOT `categories` — singular name, plural type |
| `start_date`     | `str`                  | Direct attribute, ISO format                  |
| `end_date`       | `str`                  | Direct attribute, ISO format                  |
| `gcp_project_id` | `str`                  | NOT `gcs_project_id` or `project_id`          |
| `is_mock`        | `bool` (property)      | NOT `is_mock_mode`                            |
| `service_name`   | `str`                  |                                               |

Extra CLI args are accessed via `payload.extra.get("redo_all")` on `BatchPayload`, NOT on the runtime object.

### VenueMapping (UAC `registry/venue_mapping.py`)

- Does **NOT** have `get_venues_for_categories()` — services implement their own venue filtering using:
  - `tardis_to_venue` dict
  - `all_databento_venues` list
  - `all_defi_venues` list
- `is_venue_available_on_date(venue, date)` — exists, works
- Does **NOT** have `get_category_for_venue()` — not needed in the service pattern

### ManifestWriter (UCI `catalogue.py`)

```python
writer = ManifestWriter(service_name="my-service")
writer.add(
    dataset_id,
    category,
    processing_date,
    row_count,
    *,
    gcs_bucket,
    gcs_prefix,
    venue,
)
writer.write()  # flushes to cloud
```

### log_event (UEI)

```python
log_event("EVENT_NAME", details={"key": "value"})  # NOT kwargs
# severity="INFO" optional
```

### DataSink from get_data_sink()

```python
sink.write(
    data=df,
    partition={"day": date, "venue": venue},
    format="parquet",
    filename="ticks.parquet",
)
# NOT sink.write_parquet(df, bucket=, path=)
```

### get_market_adapter (UMI)

```python
get_market_adapter(venue)  # NO api_key param — UMI is credentials-free
# VenueName = Literal["binance", "bybit", "coinbase", "deribit", "okx"]
```

### UnifiedServiceHandler.process()

```python
async def process(self, payload: object) -> object:
    # Subclass MUST accept object, use isinstance guard
    if not isinstance(payload, BatchPayload):
        return None
    ...
```

### ApiKeyReloader (UTL) — replaces one-shot validate_api_keys_for_venues()

```python
reloader = ApiKeyReloader(venues=active_venues, project_id=project_id)
reloader.start()           # starts periodic refresh
reloader.current_keys      # dict[str, str], always fresh
```

Services MUST use `ApiKeyReloader` for ongoing key access. The old `validate_api_keys_for_venues()` is a one-shot call
that does not handle key rotation or expiry.

---

## 12. QG Hygiene Checklist (For Service Refactors)

When refactoring any service to the thin template pattern, run through this checklist BEFORE declaring done:

1. **Delete legacy `pytest.ini`** — use `pyproject.toml [tool.pytest.ini_options]` only. Two pytest configs cause silent
   conflicts.
2. **Fix deep imports in `scripts/`** — `from library.core.module import X` must become `from library import X`. Deep
   imports break when internals are reorganised.
3. **Delete orphaned root scripts** — `inspect_*.py`, `cleanup_*.sh`, `install.sh`, `test_*.sh` at repo root. Move to
   `scripts/` if still needed, otherwise delete.
4. **Delete orphaned root dirs** — `node_modules/`, `htmlcov/`, `logs/`, `sample_data/` at repo root. Add to
   `.gitignore` or delete entirely.
5. **Set `RUN_INTEGRATION=true`** with proper `tests/integration/test_library_contracts.py`. Integration tests verify
   UTL, UAC, UIC functionality — not just that imports succeed.
6. **Integration tests: verify behaviour, not imports** — `assert get_market_adapter("binance") is not None` is a real
   test. `import unified_trading_library` is not.
7. **Slim `pyproject.toml` deps** — remove all vendor-specific SDKs (`ccxt`, `tardis-client`, `databento`, `yfinance`),
   data science libs (`plotly`, `polars`, `numba`, `scipy`), and network libs (`websockets`, `aiohttp`, `httpx`,
   `requests`) that the service no longer imports directly.
8. **Update workspace manifest** — list only repos you directly `from X import` in production code. Transitive deps
   through UTL do not count. Add `note` field explaining why each dep is direct.
9. **Add `[tool.coverage.run] omit`** for boilerplate files: `__main__.py`, `config_reloaders.py`, `api/main.py`,
   `cli/main.py` — these are framework glue, not domain logic.
10. **Add `HARDCODED_PROTO_EXCLUDE_GLOBS`** if `ManifestWriter` `gcs_bucket` param triggers false positives in the
    hardcoded-protocol QG check.
11. **Use `ApiKeyReloader`** not one-shot `validate_api_keys_for_venues()` — see Pattern 11 above.

---

## 13. Dependency Cleanup Pattern

When refactoring a service to the thin template:

### Keep (always needed)

- `unified-trading-library` — provides everything transitively (UTL, UCI, UEI, UDC, UCC)
- `pandas` — DataFrame processing in orchestrator
- `pydantic`, `pydantic-settings` — config and validation
- `pyyaml` — config file parsing
- `fastapi`, `uvicorn` — health API

### Remove (vendor/science/network bloat)

| Category     | Packages to remove                                           |
| ------------ | ------------------------------------------------------------ |
| Vendor SDKs  | `ccxt`, `tardis-client`, `databento`, `yfinance`             |
| Data science | `plotly`, `polars`, `numba`, `scipy`, `scikit-learn`         |
| Network      | `websockets`, `asyncio-mqtt`, `aiohttp`, `httpx`, `requests` |
| Cloud        | `aiobotocore`, `db-dtypes`, `pandas-gbq`                     |

These are either unused after refactoring or provided transitively through UTL/UMI.

### Manifest rule

List only repos you directly `from X import` in production code. If a dep comes transitively through UTL (e.g.,
`unified-cloud-interface` is a UTL dep), it does NOT belong in your manifest. Example:

```json
{
  "dependencies": [
    { "name": "unified-trading-library", "note": "framework: ServiceBootstrap, DataSink, ManifestWriter" },
    { "name": "unified-api-contracts", "note": "domain types: VenueMapping, tardis_to_venue" },
    {
      "name": "market-tick-data-service/market_tick_data_service/market_interface",
      "note": "direct: get_market_adapter() in adapter layer"
    },
    { "name": "unified-config-interface", "note": "bootstrap: service_config extends UnifiedCloudConfig" }
  ]
}
```

---

## 14. Deduplication Protocol

When a service has parallel directories implementing the same logic (e.g., `engine/` vs `app/core/`):

### Step 1: Systematic diff

Diff ALL file pairs between the two directories. Do not assume one side is canonical — both may have evolved
independently with different strengths.

### Step 2: Compare on four axes

| Axis                       | Question                                           |
| -------------------------- | -------------------------------------------------- |
| **Functionality coverage** | Which side handles more edge cases?                |
| **Error handling quality** | Which side classifies errors properly (Pattern 8)? |
| **Type safety**            | Which side uses typed models vs raw dicts?         |
| **Logging richness**       | Which side has structured log_event calls?         |

### Step 3: Use the better side as REFERENCE, not as survivor

Neither side survives the refactor. The final target is a SINGLE `orchestrator.py` (approximately 200 lines) that
implements the thin template pattern. Use the better side's logic as the reference for what the orchestrator must do,
but rewrite it to fit the Handler-Orchestrator split (Pattern 2).

### Step 4: Delete both originals

After the new orchestrator is written and QG passes, delete both parallel directories entirely. No shims, no re-exports,
no "legacy" package kept around for compatibility.

**Why this matters:** The MTDS refactor found that `engine/` had better error handling but `app/core/` had better type
safety. Cherry-picking from both into a clean orchestrator produced a result better than either original — and 97%
smaller (34,765L to 850L).

---

## 15. Batch Service Lifecycle: Setup, Work, Cleanup (HARD RULE — codified 2026-05-28)

Every batch service that holds per-shard state — caches, lazy-loaded reference data, manifest read buffers, GCS clients,
data-sink buffers, polars/pyarrow arenas, anything else allocated to serve one (date, asset_group, venue, data_type,
instrument) tuple — MUST run an explicit cleanup hook on **every exit path** of its per-shard work. Success, freshness-
skip, missing-deps, missing-bucket, raised exception — every one.

This applies to the finest granularity the service exposes. If the CLI lets the operator drill down to one date × one
asset_group × one data_type × one instrument, the cleanup hook MUST fire even for that single-shard run. There is no
exit path where skipping cleanup is correct.

### Why

When the cleanup hook lives but is wired only into one early-exit branch (the "no work to do" path), the success path —
"loaded the data, did the work, wrote the outputs" — silently retains every cache it built up. In a long-running multi-
shard VM (the actual deployment shape; see
[`vm-tarball-deployment.md`](/codex/05-infrastructure/vm-tarball-deployment.md) § "Per-shard cleanup contract"), that
residue compounds shard-over-shard until the box swap-deadlocks.

A single `gc.collect()` at the outer process boundary cannot reach this state. The caches sit on service objects
(`candle_processing_service`, `sampling_service`, equivalents) whose references survive the orchestrator's local-scope
`del` — they may be module-level singletons, or held by per-asset_group sink registries, or pinned by a long-running
ResourceProfiler subscriber. Reference-counting GC won't reclaim them; cycle GC won't either. The only thing that
guarantees release is an explicit per-shard cleanup that the service itself wires in.

### The anti-pattern (the 2026-05-28 incident shape)

```python
class CandleOrchestrationBase:
    def _cleanup_after_day(self, date: str) -> None:
        """Cleanup in-memory data after processing a day."""
        # clears candle_processing_service.cache + sampling_service.cache + gc.collect()
        ...

class CandleOrchestrationService(...):
    def _load_tradable_context(self, ...):
        ...
        if tradable_instruments.empty:
            self._cleanup_after_day(date_str)   # ← only call site
            return None, None

    def process_category(self, ...):
        # ... does the actual work ...
        return results                           # ← cleanup hook NEVER fires here
```

The cleanup method exists. The cleanup method even calls `gc.collect()` and logs RSS. But it's only invoked from the
no-work-to-do branch. The success path leaks. **The pathology is the wiring, not the hook.**

### The correct pattern

```python
def process_category(self, ...):
    results: list[ProcessingResult] = []
    try:
        # ... all per-shard work, every early-exit `return results` stays inside the try ...
        return results
    finally:
        # Idempotent + cheap when there's nothing to free. Runs on success,
        # freshness-skip, missing-deps, missing-bucket, raised exception.
        try:
            self._cleanup_after_day(date_str)
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError) as cleanup_exc:
            logger.warning("Error during _cleanup_after_day for %s: %s", date_str, cleanup_exc)
```

The `try/finally` around the per-shard body guarantees the cleanup hook fires on every return path. The inner
`try/except` around the cleanup call keeps a cleanup failure from masking a real exception from the work itself.

### What "per-shard state" includes

Audit checklist for `_cleanup_after_<shard>()` implementations:

| Cache / state                                               | How it leaks                                                  | Cleanup primitive                              |
| ----------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------- |
| Per-service candle / aggregation caches                     | Module-level singleton; orchestrator's `del` doesn't reach    | `service.clear_cache_for_date(date)`           |
| Per-asset_group `DataSink` registry on the orchestrator     | Held in `self._data_sinks: dict[str, DataSink]`               | `self._data_sinks.clear()` or per-key `del`    |
| Lazy-loaded reference DataFrame (e.g. instruments universe) | Held in `self._instruments_df` (or equivalent)                | `self._instruments_df = None`                  |
| Manifest read buffer (decompressed parquet → pandas)        | Local in caller; should drop on scope exit but often pinned   | Force drop, then `gc.collect()`                |
| Polars / PyArrow arenas                                     | Not reclaimed by `gc.collect()` or `del`                      | See `data-engine-selection.md` (separate plan) |
| ResourceProfiler sample buffer                              | If the profiler retains samples per shard, it grows unbounded | Bounded ring buffer; profiler-side concern     |

The first four are in the service's control. The last two (Polars arenas, profiler buffers) need engine-/framework-level
discipline; see the architecture audit
[`plans/active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md`](../../plans/active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md).

### Granularity

The cleanup hook fires at whichever shard boundary the service's `process_category` (or equivalent) wraps. For MDPS,
that's per (date, asset_group). For services that loop per-(date, asset_group, data_type) inside the orchestrator, the
cleanup hook should fire at the innermost loop boundary where per-shard state is built up.

**Single-shard drilldown runs MUST still call cleanup.** A
`--start-date 2026-04-15 --end-date 2026-04-15 --asset-group cefi --data-types trades --venues BINANCE-FUTURES --instrument-ids BTCUSDT`
invocation processes exactly one shard, then exits the Python process. The cleanup hook should still fire — both to
validate the cleanup path is exercised by all real callers (no silent dead branch) and so that any post-exit teardown
the hook does (writing a final manifest snapshot, flushing a metrics buffer) happens.

### Reference implementation

- [`orchestration_base.py:79`](../../../market-data-processing-service/market_data_processing_service/app/core/orchestration_base.py#L79)
  — `_cleanup_after_day(date)` — clears per-service caches + `gc.collect()` + logs RSS.
- [`orchestration_service.py:132+`](../../../market-data-processing-service/market_data_processing_service/app/core/orchestration_service.py#L132)
  — `process_category(...)` wraps its body in `try/finally` so the cleanup fires on every exit path (landed at
  MDPS@dcd7416).

### Reference incidents

- **2026-05-28** — MDPS 7-day backfill on `e2-standard-8` (32 GB). The `_cleanup_after_day` hook existed but was only
  wired into the early-exit branch. Day 1 completed cleanly (28/28 outputs). Day 2 OOM'd at the date-boundary because
  the day-1 candle/sampling caches were still pinned. Empirical RSS at end of day 1: 25.1 GB (after a `del orchestrator
  - gc.collect()` at the process_handler boundary, which only reclaimed 87 MB). Plan: [`mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`](../../plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md)
    § "Finding A".

### Composes with

- [`vm-tarball-deployment.md`](/codex/05-infrastructure/vm-tarball-deployment.md) § "Per-shard cleanup contract" — the
  VM- lifecycle side of this rule. Long-running multi-shard VMs depend on the per-shard cleanup hook firing.
- [`cli-convention.md`](cli-convention.md) § "Instrument Identity and CLI Granularity" — defines what counts as a single
  shard, which determines where the cleanup hook attaches.
- `data-engine-selection.md` (codified 2026-05-28) — Polars/PyArrow arenas are NOT reclaimed by this rule's primitives;
  picking one engine end-to-end is the only mitigation for arena retention.
