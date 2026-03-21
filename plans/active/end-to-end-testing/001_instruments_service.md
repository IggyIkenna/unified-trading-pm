---
title: "E2E Test: instruments-service"
service: instruments-service
date: 2026-03-21
status: in_progress
---

# E2E Test: instruments-service

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

| #   | Operation         | Category   | Expected                                 | Status                                      |
| --- | ----------------- | ---------- | ---------------------------------------- | ------------------------------------------- |
| 2.1 | instruments       | CEFI       | Fetch from Tardis/CCXT, no GCS writes    | PASS — 19 venues fetched, dry-run confirmed |
| 2.2 | instruments       | TRADFI     | Fetch from EOD/IBKR, no GCS writes       |                                             |
| 2.3 | instruments       | DEFI       | Fetch from subgraphs, no GCS writes      |                                             |
| 2.4 | instruments       | SPORTS     | Fetch from sportsbooks, no GCS writes    |                                             |
| 2.5 | instruments       | PREDICTION | Should skip gracefully (not implemented) |                                             |
| 2.6 | aggregate         | (all)      | Read existing GCS data, no new writes    |                                             |
| 2.7 | corporate_actions | TRADFI     | Fetch from FMP, no GCS writes            |                                             |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Operation   | Category | CSV check                         | GCS check                 | Status |
| --- | ----------- | -------- | --------------------------------- | ------------------------- | ------ |
| 3.1 | instruments | CEFI     | Inspect CSV sample, verify schema | Verify parquet in GCS     |        |
| 3.2 | instruments | TRADFI   | Inspect CSV sample                | Verify parquet            |        |
| 3.3 | instruments | DEFI     | Inspect CSV sample                | Verify parquet            |        |
| 3.4 | aggregate   | (all)    | N/A (aggregated)                  | Verify aggregated parquet |        |

### Phase 4: Category Sweep

| #   | Category   | Expected venues                                                            | Expected instrument count (approx)           | Status |
| --- | ---------- | -------------------------------------------------------------------------- | -------------------------------------------- | ------ |
| 4.1 | CEFI       | 17 venues, 389,245 instruments                                             | GCS verified: `instruments-store-cefi-*`     | PASS   |
| 4.2 | TRADFI     | 7 venues, 1,212,352 instruments (CME 1.08M, ICE 99K, NASDAQ 12K, NYSE 12K) | GCS verified: `instruments-store-tradfi-*`   | PASS   |
| 4.3 | DEFI       | 15 protocols, ~120 instruments fetched                                     | **ISSUE #11: wrote to CEFI bucket not DEFI** | FAIL   |
| 4.4 | SPORTS     | 101 leagues configured, SportsOrchestrator called                          | **ISSUE #12: USRI not installed**            | FAIL   |
| 4.5 | PREDICTION | Explicit "not supported" message, returns empty                            | Correct behavior                             | PASS   |

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

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue                              | Severity | Fixed?                |
| ---------------------------------- | -------- | --------------------- |
| `load_dotenv(override=True)`       | P1       | Yes                   |
| `--dry-run` not enforced           | P1       | Yes (framework-level) |
| `ENVIRONMENT=development` rejected | P2       | Yes                   |
| `TESTNET_MODE=mainnet` rejected    | P2       | Yes                   |
| Asyncio nesting in handlers        | P1       | Yes                   |
| Raw API keys in .env               | P0       | Yes                   |
| Hardcoded bucket names in .env     | P2       | Yes                   |

## Next Service

After instruments-service passes all phases → proceed to `002_market_tick_data_service.md`
