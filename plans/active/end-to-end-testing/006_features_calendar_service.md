---
title: "E2E Test: features-calendar-service"
service: features-calendar-service
date: 2026-03-22
status: pending
---

# E2E Test: features-calendar-service

Follows `procedure.md`. Pipeline position: #6 (L3 features layer).

**Upstream:** instruments-service (corporate actions, reference data), market-data-processing-service (candles — used
sparingly; most calendar features are time-based, not price-based).

**Downstream:** ml-training-service (calendar_features).

**Key uniqueness:** Calendar features are TIME-BASED, not price-based. They derive from reference data (earnings dates,
dividend ex-dates, economic calendars, expiry schedules) rather than candle/tick data. The service processes two
internal feature categories per run: `time_features` and `economic_events`. No `--asset-group` CLI arg — the service is
UNIVERSAL across all asset categories (TRADFI earnings, CEFI exchange events, etc.).

**Frontend:** Feeds calendar widget, earnings calendar, economic events timeline in Research/Data tabs.

## Operations

| Operation | What it does                                             | Expected output                             |
| --------- | -------------------------------------------------------- | ------------------------------------------- |
| `compute` | Generate calendar features (time_features + econ events) | Parquet per category per date in GCS        |
| `info`    | Display service configuration and status                 | Config dump to stdout (no writes)           |
| `live`    | Subscribe to PubSub, recompute for today on each event   | Calendar features published to PubSub + GCS |

## CLI Structure

The service uses a hand-rolled CLI (`batch_handler.py` `create_parser()`) rather than ServiceCLI. Key flags:

- `--operation compute|info` (required)
- `--mode batch|live` (required; legacy `info` mode mapped to `--operation info --mode batch`)
- `--start-date`, `--end-date` (required for `compute --mode batch`)
- `--dry-run` (write to `data/sample/` instead of GCS)
- `--force` (overwrite existing data)
- `--max-results` (limit days processed)
- `--run-tag` (GCS prefix: `batch` or `t1-recon`)

Note: No `--asset-group` flag. The service always processes BOTH `time_features` and `economic_events` internally.
Calendar features are universal across all market categories.

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars                                                                        | Expected                  | Status |
| --- | ------------------------------------------------------------------------------- | ------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet` | OK                        |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true`                     | OK                        |        |
| 1.3 | `CLOUD_PROVIDER=gcp ENVIRONMENT=staging TESTNET_MODE=testnet`                   | OK                        |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.5 | `TESTNET_MODE=sandbox`                                                          | STARTUP_VALIDATION_FAILED |        |
| 1.6 | `CLOUD_MOCK_MODE=maybe`                                                         | Pydantic validation error |        |

### Phase 2: Dry-Run (batch, real data, no writes)

| #   | Operation | Mode  | Expected                                                          | Status |
| --- | --------- | ----- | ----------------------------------------------------------------- | ------ |
| 2.1 | compute   | batch | Processes time_features + economic_events, writes to data/sample/ |        |
| 2.2 | compute   | batch | `--dry-run` flag confirmed in logs ("DRY RUN mode")               |        |
| 2.3 | info      | batch | Config dump: project_id, feature categories, FRED API status      |        |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Operation | Dates                     | GCS check                                 | Status |
| --- | --------- | ------------------------- | ----------------------------------------- | ------ |
| 3.1 | compute   | single day (2026-03-21)   | Verify time_features parquet in GCS       |        |
| 3.2 | compute   | single day (2026-03-21)   | Verify economic_events parquet in GCS     |        |
| 3.3 | compute   | 7-day range               | Verify 7 days x 2 categories = 14 files   |        |
| 3.4 | compute   | `--force` on existing day | Overwrites existing data, no skip         |        |
| 3.5 | compute   | `--max-results 3`         | Only 3 days processed despite wider range |        |

### Phase 4: Category Sweep

Calendar features do NOT take a `--asset-group` CLI arg — they are universal. However, we must verify that the features
produced are valid for all downstream consumers (TRADFI, CEFI, DEFI, SPORTS, PREDICTION).

| #   | Internal category | What to verify                                                   | Status |
| --- | ----------------- | ---------------------------------------------------------------- | ------ |
| 4.1 | time_features     | Day-of-week, month, quarter, holiday flags, days-to-expiry       |        |
| 4.2 | economic_events   | Earnings dates, dividend ex-dates, economic calendar events      |        |
| 4.3 | Schema check      | Output schema matches what ml-training-service expects           |        |
| 4.4 | Empty date check  | Weekend/holiday date produces valid output (flags set, no crash) |        |
| 4.5 | Future date check | End date beyond today handled gracefully (or rejected)           |        |

**GCS verification after writes:**

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('<calendar-features-bucket>')
blobs = list(bucket.list_blobs(prefix='calendar_features/', max_results=20))
print(f'Files written: {len(blobs)}')
for b in blobs[:5]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 5: Live Mode

Live mode subscribes to PubSub (`features-delta-one-ready-sub`), recomputes calendar features for today using the same
`CalendarOrchestrationService.process_day()` as batch, and publishes to `features-calendar-ready`.

| #   | What                              | Expected                                                       | Status |
| --- | --------------------------------- | -------------------------------------------------------------- | ------ |
| 5.1 | `--operation compute --mode live` | Subscribes to PubSub, processes events                         |        |
| 5.2 | Transport resolution              | `get_messaging_protocol(mode="live")` returns `pubsub`         |        |
| 5.3 | Dry-run live                      | `--dry-run` computes but does not publish to PubSub            |        |
| 5.4 | Event logging                     | UEI events: STARTED, DATA_BROADCAST per event, STOPPED         |        |
| 5.5 | Graceful shutdown                 | Ctrl-C -> `LiveHandler.cleanup()` closes source + sink cleanly |        |

#### Phase 5b: Mock/Real A/B

Run the same date range with `CLOUD_MOCK_MODE=true` and `CLOUD_MOCK_MODE=false` and compare:

| #    | Check                   | Expected                                                  | Status |
| ---- | ----------------------- | --------------------------------------------------------- | ------ |
| 5b.1 | Mock redirects pipeline | `is_mock_mode()` -> `run_mock_pipeline()` (separate path) |        |
| 5b.2 | Real produces parquet   | Non-mock writes to GCS bucket                             |        |
| 5b.3 | Schema parity           | Mock and real output schemas are identical                |        |

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                         | What it tests                                   | Expected                             | Status |
| --- | -------------------------------- | ----------------------------------------------- | ------------------------------------ | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true`           | Mock pipeline activation                        | `run_mock_pipeline()` called, no GCS |        |
| 6.2 | Mock with `CLOUD_PROVIDER=local` | No cloud credentials required                   | Completes without ADC                |        |
| 6.3 | Missing upstream data            | instruments-service produced no corp actions    | Graceful empty output, no crash      |        |
| 6.4 | Corrupt date inputs              | `--start-date not-a-date`                       | Parser error, clean exit             |        |
| 6.5 | Start > end date                 | `--start-date 2026-03-22 --end-date 2026-03-01` | Validation error, sys.exit(1)        |        |
| 6.6 | config_source check              | `CLOUD_MOCK_MODE=true`                          | `config_source=local`, no GCS reads  |        |

### Phase 7: Observability

| #   | Check                 | Expected                                                      | Status |
| --- | --------------------- | ------------------------------------------------------------- | ------ |
| 7.1 | UEI lifecycle events  | STARTED, VALIDATION*STARTED/COMPLETED, PROCESSING*\*, STOPPED |        |
| 7.2 | Per-category logging  | Each of time_features/economic_events logged separately       |        |
| 7.3 | Shard-level isolation | One category failure doesn't crash the other                  |        |
| 7.4 | Dry-run warning       | "DRY RUN mode" logged when `--dry-run` active                 |        |
| 7.5 | Correlation ID        | correlation_id present in all lifecycle events                |        |
| 7.6 | Memory watchdog       | "Memory watchdog started" logged                              |        |
| 7.7 | Graceful shutdown     | GracefulShutdownHandler registered on startup                 |        |
| 7.8 | Batch summary         | Results by category table logged at end of batch              |        |

## Known Issues Audit

Check for these patterns found in earlier services:

| Pattern                      | What to check                                                            | Status |
| ---------------------------- | ------------------------------------------------------------------------ | ------ |
| `load_dotenv(override=True)` | Must be `override=False` — shell env wins over .env                      |        |
| `--dry-run` enforcement      | Verify dry-run actually prevents GCS writes                              |        |
| Bucket resolution            | Uses `build_bucket()` not hardcoded env vars                             |        |
| asyncio nesting              | `LiveHandler.run()` is async; batch uses `asyncio.run()` — check nesting |        |
| `os.getenv()` usage          | Must use `UnifiedCloudConfig` except config-bootstrap exceptions         |        |
| LOG_LEVEL validation         | Invalid `LOG_LEVEL` env var -> clean `SystemExit` with valid options     |        |

## AWS Testing

| #   | What                                       | Expected                          | Status |
| --- | ------------------------------------------ | --------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=true`  | Service starts with mock mode     |        |
| A.2 | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=false` | Requires AWS credentials, S3 sink |        |

## Frontend API Surface

Calendar features feed these UI components:

| UI Component             | Data source                       | API endpoint (if applicable)    |
| ------------------------ | --------------------------------- | ------------------------------- |
| Calendar widget          | calendar_features/time_features   | `/api/features/calendar`        |
| Earnings calendar        | calendar_features/economic_events | `/api/features/earnings`        |
| Economic events timeline | calendar_features/economic_events | `/api/features/economic-events` |
| Research/Data tabs       | Both categories                   | Various                         |

Verify that the output schema from this service matches what the API layer expects.

## Issues Found

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After features-calendar-service passes all phases -> proceed to `008_ml_training_service.md`
