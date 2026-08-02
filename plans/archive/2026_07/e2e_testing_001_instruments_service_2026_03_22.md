---
title: "E2E Test: instruments-service"
service: instruments-service
date: 2026-03-21
status: superseded
superseded_by: plans/archive/2026_08/instruments_service_e2e_live_mock_observability_2026_07_27.md
---

# E2E Test: instruments-service

> **ARCHIVED (2026-07-27) — point-in-time snapshot, re-scoped.** Phases 1-4 + the 2026-03-23 DEFI E2E audit (6 logged
> bugs) are real completed work but 4+ months cold — re-verify live if you still care about those bugs. The
> USRI-not-installed finding is moot (USRI merged into instruments-service's own `sports/` sub-package, 2026-03
> consolidation). Phases 5-7 (never run) were re-scoped as fresh work in
> `instruments_service_e2e_live_mock_observability_2026_07_27.md`, which ran to completion and archived 2026-08-02:
> `plans/archive/2026_08/instruments_service_e2e_live_mock_observability_2026_07_27.md`.

Follows `procedure.md`. Pipeline position: #1 (no upstream dependencies).

## Operations

| Operation                      | What it does                             | Expected output                        |
| ------------------------------ | ---------------------------------------- | -------------------------------------- |
| `instruments`                  | Fetch instrument definitions from venues | Parquet per venue per date             |
| `aggregate`                    | Deduplicate instruments across venues    | Single aggregated parquet per category |
| `corporate_actions`            | Fetch dividends/splits/earnings (TRADFI) | Corporate actions parquet              |
| `corporate_actions_backfill`   | Full history fetch                       | Historical corporate actions           |
| `generate_date_views`          | Transform by_ticker → by_date            | Date-indexed views                     |
| `corporate_actions_update`     | Incremental update                       | Updated corporate actions              |
| `corporate_actions_production` | Full pipeline (fetch+backfill+views)     | All of the above                       |
| `live`                         | Periodic batch (every N minutes)         | Same as instruments, on schedule       |

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                  | Status |
| --- | ------------------------------------------------------------------------------- | ------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                        | PASS   |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK                        | PASS   |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                        | PASS   |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED | PASS   |
| 1.5 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED | PASS   |
| 1.6 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error | PASS   |

### Phase 2: Dry-Run (batch, real data, no writes)

| #   | Operation   | Category   | Expected                                                                 | Status                                                      |
| --- | ----------- | ---------- | ------------------------------------------------------------------------ | ----------------------------------------------------------- |
| 2.1 | instruments | CEFI       | Fetch from Tardis/CCXT, no GCS writes                                    | PASS — 19 venues fetched, dry-run confirmed                 |
| 2.2 | instruments | TRADFI     | Fetch from EOD/IBKR, no GCS writes                                       |                                                             |
| 2.3 | instruments | DEFI       | Fetch from subgraphs, no GCS writes                                      | PASS — 108 instruments/day, 7 days, Balancer 400 (isolated) |
| 2.4 | instruments | SPORTS     | Fetch from sportsbooks, no GCS writes                                    |                                                             |
| 2.5 | instruments | PREDICTION | Should skip gracefully (not implemented)                                 |                                                             |
| 2.6 | aggregate   | (all)      | Read existing GCS data, no new writes                                    |                                                             |
| 2.7 | —           | —          | Corporate actions operation moved to features-service (calendar family). |                                                             |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Operation   | Category | CSV check                         | GCS check                 | Status |
| --- | ----------- | -------- | --------------------------------- | ------------------------- | ------ |
| 3.1 | instruments | CEFI     | Inspect CSV sample, verify schema | Verify parquet in GCS     |        |
| 3.2 | instruments | TRADFI   | Inspect CSV sample                | Verify parquet            |        |
| 3.3 | instruments | DEFI     | Inspect CSV sample                | Verify parquet            |        |
| 3.4 | aggregate   | (all)    | N/A (aggregated)                  | Verify aggregated parquet |        |

### Phase 4: Category Sweep

| #   | Category   | Expected venues                                                                      | Expected instrument count (approx)                     | Status  |
| --- | ---------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------ | ------- |
| 4.1 | CEFI       | 17 venues, 389,245 instruments                                                       | GCS verified: `instruments-store-cefi-*`               | PASS    |
| 4.2 | TRADFI     | 7 venues, 1,212,352 instruments (CME 1.08M, ICE 99K, NASDAQ 12K, NYSE 12K)           | GCS verified: `instruments-store-tradfi-*`             | PASS    |
| 4.3 | DEFI       | 14 protocols, 108 instruments/day (Balancer=0, Hyperliquid=0), 756 total over 7 days | DEFI bucket correct; Balancer broken; Aster casing bug | PARTIAL |
| 4.4 | SPORTS     | 101 leagues configured, SportsOrchestrator called                                    | **ISSUE #12: USRI not installed**                      | FAIL    |
| 4.5 | PREDICTION | Explicit "not supported" message, returns empty                                      | Correct behavior                                       | PASS    |

### Phase 5: Live Mode (15-minute clock-aligned schedule)

Instruments "live" = periodic batch on 15-min UTC intervals (00, 15, 30, 45). Not a persistent WebSocket — a Cloud Run
Job scheduled via cron. For local testing: run the `live` operation and verify it:

1. Waits until the next 15-min boundary (e.g. if started at 17:03, waits until 17:15)
2. Filters out instruments expiring at or before that timestamp
3. Produces deterministic output — same time = same instruments
4. Downstream services can rely on this schedule for dependency checks

| #   | What                                          | Expected                                                         | Status |
| --- | --------------------------------------------- | ---------------------------------------------------------------- | ------ |
| 5.1 | `--operation live --mode batch --interval 15` | Waits for next 15-min boundary, then runs                        |        |
| 5.2 | Clock alignment                               | Runs at :00/:15/:30/:45, not at arbitrary times                  |        |
| 5.3 | Event logging                                 | UEI events: STARTED, per-venue COMPLETED/FAILED, final COMPLETED |        |
| 5.4 | Graceful shutdown                             | Ctrl-C during wait → clean exit, no partial writes               |        |

### Phase 6: Mock Mode (scenario testing)

Mock mode must test failure scenarios that affect the whole pipeline:

| #   | Scenario                  | What it tests                                     | Expected                                         | Status |
| --- | ------------------------- | ------------------------------------------------- | ------------------------------------------------ | ------ |
| 6.1 | `--scenario default`      | Normal mock instruments                           | Mock data generated, local sink                  |        |
| 6.2 | `--scenario stress`       | High cardinality (10x instruments)                | Service handles memory, writes succeed           |        |
| 6.3 | `--scenario missing_data` | Instruments disappear mid-day                     | Downstream services get empty, handle gracefully |        |
| 6.4 | Fake symbols              | Inject non-existent `FAKE-EXCHANGE:SPOT:NOSYMBOL` | Pipeline skips/errors cleanly, no crash          |        |
| 6.5 | Missing entire category   | DEFI instruments missing                          | market-tick-data gets nothing for DEFI, skips    |        |
| 6.6 | Corrupt expiry dates      | `expiry="not-a-date"`                             | Parser handles, logs warning, doesn't crash      |        |
| 6.7 | config_source check       | `CLOUD_MOCK_MODE=true`                            | `config_source=local`, no GCS reads              |        |

### Phase 7: Observability

| #   | Check                   | Expected                                      | Status |
| --- | ----------------------- | --------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line | All dimensions logged                         |        |
| 7.2 | UEI events              | STARTED, COMPLETED, per-venue events          |        |
| 7.3 | Shard-level isolation   | One venue failure doesn't crash others        |        |
| 7.4 | Dry-run warning         | "DRY RUN" + "UCI dry-run mode ACTIVE" logged  |        |
| 7.5 | Error classification    | ADAPTER_FETCH_FAILED events for failed venues |        |
| 7.6 | Memory watchdog         | "Memory watchdog started" logged              |        |

## DEFI Category E2E Audit (2026-03-23)

### Run Parameters

- Date range: 2026-03-17 to 2026-03-23 (7 days)
- Mode: dry-run (no GCS writes, real API calls)
- Duration: ~6 minutes
- Exit code: 0

### Data Availability Summary

| Protocol    | Instruments/day | Status | Notes                                    |
| ----------- | --------------- | ------ | ---------------------------------------- |
| UniswapV2   | 7               | OK     | 500 pairs fetched, top 7 filtered        |
| UniswapV3   | 30              | OK     | 500 pools fetched, top 30 filtered       |
| UniswapV4   | 22              | OK     | 500 pools fetched, top 22 filtered       |
| Curve       | 4               | OK     | 49 pools fetched, 4 filtered             |
| Balancer    | 0               | FAIL   | 400 Bad Request every day (see Issue #1) |
| AaveV3      | 12              | OK     | 86 markets fetched, 12 filtered          |
| Aave Plasma | 12              | OK     | Same 86 markets, 12 filtered             |
| EtherFi     | 1               | OK     | 1 LST instrument                         |
| Lido        | 2               | OK     | 2 LST instruments                        |
| Morpho      | 1               | OK     | 7 markets fetched, 1 filtered            |
| Euler       | 2               | OK     | 2 markets                                |
| Fluid       | 6               | OK     | 6 markets                                |
| Hyperliquid | 0               | WARN   | No error, returns 0 (see Issue #3)       |
| Aster       | 20              | OK     | 326 perps fetched, 20 filtered           |
| Ethena      | 1               | OK     | 1 yield-bearing instrument               |
| **Total**   | **108/day**     |        | **756 instruments across 7 days**        |

### Consistency

- 108 instruments per day, identical count across all 7 days -- deterministic pipeline
- 7/7 days processed successfully (100%)
- 7 processing errors (1/day, all Balancer)

### Issues Found (DEFI E2E Audit)

| #   | Issue                               | Severity | Root Cause                                                                                                                                                                                   | Fix Location                                                                           |
| --- | ----------------------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| 1   | Balancer 400 Bad Request (7/7 days) | P1       | URL mismatch: request hits `api-v3.balancer.fi/` but UMI adapter defines `api-v3.balancer.fi/graphql`. instruments-service may be calling the base URL without `/graphql` path               | unified-market-interface `balancer_adapter.py` or instruments-service DeFi processor   |
| 2   | Aster venue casing: `defi/ASTER`    | P2       | Aster writes as lowercase `defi/ASTER` while all others write `DEFI/VENUE-ETHEREUM`. Downstream consumers querying `DEFI/` prefix will miss Aster data                                       | instruments-service `defi_orchestration.py` — Aster adapter returns lowercase category |
| 3   | Hyperliquid returns 0 instruments   | P2       | No error logged, silently returns empty. May be intentional (no on-chain instruments on Ethereum?) or adapter not querying correctly. Needs classification: expected-empty or broken adapter | instruments-service or UMI `hyperliquid_adapter`                                       |
| 4   | Data catalogue entries missing      | P3       | `dataset_id=instruments_` and `dataset_id=instruments_defi` not found in PM `data-catalogue.instruments-service.yaml` — warns 2x per day (14 warnings total)                                 | unified-trading-pm `configs/data-catalogue.instruments-service.yaml`                   |
| 5   | Pydantic settings UserWarning       | P3       | `A custom validator is returning a value other than self` on every startup. Not blocking but noisy                                                                                           | unified-config-interface or instruments-service config model                           |
| 6   | CFE venue not in UAC                | P3       | `instruments-service handles 1 venue(s) not in UAC INSTRUMENT_TYPES_BY_VENUE: ['CFE']` — not DEFI-specific but logged on startup                                                             | unified-api-contracts `INSTRUMENT_TYPES_BY_VENUE` missing CFE                          |

### Error Handling Assessment

| Check                                       | Result | Notes                                                                     |
| ------------------------------------------- | ------ | ------------------------------------------------------------------------- |
| Balancer failure isolated (no cascade)      | PASS   | Other 14 protocols unaffected, pipeline continues                         |
| Balancer error classified                   | WARN   | Classified as `UNKNOWN` — should be `API_SCHEMA_CHANGED` or `BAD_REQUEST` |
| Empty protocol result handled (Hyperliquid) | PASS   | Returns 0, logs INFO, continues                                           |
| Dry-run enforced                            | PASS   | All writes redirected to local temp dirs                                  |
| Memory watchdog active                      | PASS   | "Memory watchdog started" logged                                          |
| API key retrieval from Secret Manager       | PASS   | Tardis + Graph API keys retrieved successfully                            |
| CCXT exchange pre-loading                   | PASS   | 3/3 exchanges loaded (binance 4280, bybit 3379, deribit 4368)             |
| ServiceRuntime dimensions logged            | PASS   | op, mode, provider, env, data_mode, testnet, dry_run all present          |

### Architecture Compliance Assessment

| Check                                       | Result | Notes                                                                            |
| ------------------------------------------- | ------ | -------------------------------------------------------------------------------- |
| Bucket routing: DEFI category → defi bucket | PASS   | `instruments-store-defi-central-element-323112` (Issue #11 from Phase 4.3 FIXED) |
| UCI DataSink abstraction used               | PASS   | All writes via `LocalDataSink` / `DataSink` interface                            |
| UEI event logging initialized               | PASS   | `GcsEventSink` configured for batch mode                                         |
| OpenTelemetry tracing                       | PASS   | Enabled, service=instruments-service                                             |
| Venue-partitioned storage layout            | PASS   | `day=YYYY-MM-DD/venue=PROTOCOL-CHAIN/` structure                                 |
| Sequential protocol processing              | PASS   | Protocols processed one at a time within each day                                |
| Date batching                               | PASS   | 84 day-venue combinations (7 days × 12 venues) tracked                           |

### Previous Issues Status

| Issue                              | Severity | Fixed?                            |
| ---------------------------------- | -------- | --------------------------------- |
| `load_dotenv(override=True)`       | P1       | Yes                               |
| `--dry-run` not enforced           | P1       | Yes (framework-level)             |
| `ENVIRONMENT=development` rejected | P2       | Yes                               |
| `TESTNET_MODE=mainnet` rejected    | P2       | Yes                               |
| Asyncio nesting in handlers        | P1       | Yes                               |
| Raw API keys in .env               | P0       | Yes                               |
| Hardcoded bucket names in .env     | P2       | Yes                               |
| DEFI wrote to CEFI bucket (#11)    | P1       | **Yes** (confirmed in this audit) |

## Next Service

After instruments-service passes all phases → proceed to `002_market_tick_data_service.md`
