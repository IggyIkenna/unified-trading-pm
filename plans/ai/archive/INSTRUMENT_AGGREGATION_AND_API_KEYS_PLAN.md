# Instrument Aggregation, API Keys, and Reader Standardization Plan

**Status:** Draft
**Scope:** instruments-service, unified-trading-services, unified-trading-deployment-v3, market-tick-data-handler, market-data-processing-service
**Goal:** One canonical instruments cache, one API key source, one reader pattern.

> **Source of truth:** `unified-trading-codex/02-data/instruments-and-api-keys-standard.md` and `.cursor/rules/instruments-domain-and-api-keys.mdc`. This plan is historical context; use the canonical docs for implementation.

---

## 1. API Keys: Full Standardization

### 1.1 Single Source of Truth

| Layer | Responsibility |
|-------|----------------|
| **Secret Manager (GCP)** | Store all API keys. No env vars in production. |
| **unified-config-interface** | Define secret names in `UnifiedCloudConfig` (tardis_secret_name, databento_secret_name, graph_secret_name, alchemy_secret_name, aavescan_secret_name, etc.) |
| **unified-trading-services** | `get_secret_client(secret_name, project_id, fallback_env_var)` — **only** way to resolve API keys |
| **Services** | Call `get_secret_client` via config secret names. Never `os.environ.get` for API keys. |

### 1.2 Required API Keys by Data Source

| Data Source | Secret Name (config) | Used For | Mode |
|-------------|----------------------|----------|------|
| **Tardis** | tardis_secret_name | CEFI instruments, historical tick | Batch, Live |
| **Databento** | databento_secret_name | TRADFI instruments, historical tick | Batch |
| **The Graph** | graph_secret_name | DeFi instruments (Uniswap, Aave, etc.) | Batch, Live |
| **Alchemy** | alchemy_secret_name | Ethereum RPC (DeFi) | Batch, Live |
| **AaveScan** | aavescan_secret_name | Aave protocol data | Batch |
| **Envio** | envio_secret_name | Envio API (UniswapV4, features-onchain) | Optional |

**Flag:** Any data source we need but don't have a secret for → add to UnifiedCloudConfig and document.

### 1.3 Violations to Fix (instruments-service)

| File | Current | Fix |
|------|---------|-----|
| `scripts/test_batch_cost_comparison.py` | `os.environ.get("DATABENTO_API_KEY")` | Use `get_secret_client` |
| `scripts/find_subgraph_ids.py` | `os.environ.get("THEGRAPH_API_KEY", "test-key")` | Use `get_secret_client` |
| `dependency_checker.py` | `os.environ.get(env_var)` as fallback | Keep as fallback only; primary = Secret Manager |

### 1.4 Scripts / Tests Exception

- **Tests:** May use env vars for mocking; exempt.
- **Scripts that need API keys:** Must use `get_secret_client`. No direct `os.environ.get` for API keys.

---

## 2. Instrument Reading: Standardize on InstrumentsDomainClient

### 2.1 Canonical Reader

**InstrumentsDomainClient** (unified-domain-client) is the **only** canonical way to read instruments.

- Reads from: `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`
- Uses: `StandardizedDomainCloudService`, `get_storage_client`
- Method: `get_instruments_for_date(date, venue=..., instrument_type=..., ...)`
- Internal: `_load_instruments_by_venue` — **private** to UDS; not for direct use by services

### 2.2 Migrations Required

| Repo | Current | Target |
|------|---------|--------|
| **market-tick-data-handler** | `_load_instruments_by_venue` in download_handler.py (duplicate logic) | Use `InstrumentsDomainClient.get_instruments_for_date` |
| **market-data-processing-service** | `_load_instruments_by_venue` in cloud_data_provider.py | Use `InstrumentsDomainClient.get_instruments_for_date` |
| **UTDv3 data-status API** | Direct GCS reads for aggregated instruments | Use `InstrumentsDomainClient.get_aggregated_instruments` (new, see §3) |

### 2.3 Deprecate

- **unified-trading-services** `InstrumentsDomainClient` — migrate to unified-domain-client. UDS is the canonical implementation.

---

## 3. Aggregated Instruments: Move to instruments-service

### 3.1 Current State

- **UTDv3** `scripts/download_instruments.py` and `scripts/aggregate_instruments.py`:
  - Download instrument parquet from GCS (by date/venue)
  - Aggregate into `aggregated/aggregated_instruments_{date}.parquet` per category bucket
  - Used by: data-status (instrument filters), DataStatusTab UI
- **Problem:** Aggregation lives in deployment repo; instruments-service should own it.

### 3.2 Target Architecture

| Component | Responsibility |
|-----------|----------------|
| **instruments-service** | Own aggregation. New CLI mode: `--operation aggregate` (batch, daily). |
| **unified-domain-client** | Expose `InstrumentsDomainClient.get_aggregated_instruments(category)` — reads latest `aggregated/aggregated_instruments_*.parquet` |
| **UTDv3** | Remove aggregation scripts; call instruments-service or UDS. Data-status uses UDS `get_aggregated_instruments`. |

### 3.3 instruments-service: New Aggregate Operation

**CLI:**
```bash
instruments-service --mode batch --operation aggregate [--delta-only | --redo-all]
```

**Behavior:**
- **Delta-only (default):** Aggregate only new/changed data since last aggregated file (previous day).
- **--redo-all:** Re-aggregate all historical data (for schema changes, backfills). Use when instrument schema changes.
- **Output:** `aggregated/aggregated_instruments_{date}.parquet` per category bucket (CEFI, TRADFI, DEFI).
- **Schedule:** Daily batch job (e.g. cron after instruments-service main run).

### 3.4 UDS: New Method

```python
# InstrumentsDomainClient
def get_aggregated_instruments(
    self,
    category: str,
    date: str | None = None,
) -> pd.DataFrame:
    """
    Get all instruments that ever existed (deduplicated, latest per instrument_key).
    Reads from aggregated/aggregated_instruments_{date}.parquet.
    If date is None, uses latest available file.
    """
```

Used by:
- UTDv3 data-status (instrument filters)
- Downstream services needing "all instruments" for filtering

### 3.5 Migration Steps

1. Move `InstrumentAggregator` from UTDv3 to instruments-service (e.g. `instruments_service/engine/aggregation.py`).
2. Add `--operation aggregate` to instruments-service CLI.
3. Add `get_aggregated_instruments` to UDS `InstrumentsDomainClient`.
4. Update UTDv3 data-status API to use UDS `get_aggregated_instruments`.
5. Deprecate UTDv3 `scripts/aggregate_instruments.py` and aggregation logic in `download_instruments.py`.
6. Document daily schedule: instruments-service `--operation instruments` → then `--operation aggregate`.

---

## 4. UTDv3 Changes

### 4.1 Remove / Deprecate

- `scripts/aggregate_instruments.py` — logic moves to instruments-service.
- Aggregation in `scripts/download_instruments.py` — either remove or delegate to instruments-service.

### 4.2 Update

- **data-status API** (`api/routes/data_status.py`): Use `InstrumentsDomainClient.get_aggregated_instruments(category)` instead of direct GCS reads.
- **DataStatusTab UI** (`ui/src/components/DataStatusTab.tsx`): No change if API contract stays same; backend switches to UDS.
- **VM startup / cron:** Add instruments-service `--operation aggregate` as daily job after main instruments run.

### 4.3 Config

- Ensure `DEPLOYMENT_CONFIG_DIR` or equivalent points to instruments-service config for aggregation (bucket names, project ID).

### 4.4 UTDv3 Docs to Update

- `docs/cli.md` — Document that instrument aggregation is now via instruments-service; remove references to `aggregate_instruments.py`.
- `configs/checklist.instruments-service.yaml` — Add `--operation aggregate` as daily batch step.

---

## 5. Summary: One Canonical Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│ API Keys                                                                 │
│   Secret Manager → get_secret_client (UCS) → services             │
│   No os.environ.get for API keys in production code                      │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ Instrument Reading                                                       │
│   InstrumentsDomainClient (UDS) → get_instruments_for_date()             │
│   InstrumentsDomainClient (UDS) → get_aggregated_instruments() [NEW]     │
│   All services use UDS; no duplicate _load_instruments_by_venue          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ Aggregation                                                              │
│   instruments-service --operation aggregate (daily batch)                 │
│   Output: aggregated/aggregated_instruments_{date}.parquet per category   │
│   Delta by default; --full for schema changes                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Implementation Order

1. **API keys:** Fix instruments-service script violations (§1.3).
2. **UDS:** Add `get_aggregated_instruments` to `InstrumentsDomainClient`.
3. **instruments-service:** Add `--operation aggregate` handler, move aggregation logic from UTDv3.
4. **UTDv3:** Update data-status to use `get_aggregated_instruments`.
5. **market-tick-data-handler:** Migrate to `InstrumentsDomainClient`.
6. **market-data-processing-service:** Migrate to `InstrumentsDomainClient`.
7. **UTDv3:** Remove/deprecate aggregation scripts.

---

## 7. References

- `.cursor/plans/INSTRUMENTS_DOMAIN_DECISIONS.md` — Design rationale (no fallbacks, add to UCS)
- `instruments-service/docs/API_KEYS_STANDARDIZED_PROCESS.md`
- `.cursor/plans/INSTRUMENTS_SERVICE_COMPLETE_REFACTORING.md`
- `unified-trading-deployment-v3/scripts/download_instruments.py`
- `unified-trading-services/unified_trading_services/domain/clients.py`
