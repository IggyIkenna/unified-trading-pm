---
title: "E2E Test: risk-and-exposure-service"
service: risk-and-exposure-service
date: 2026-03-22
status: pending
---

# E2E Test: risk-and-exposure-service

Follows `procedure.md`. Pipeline position: #17 (L6 monitoring layer).

## Upstream / Downstream

| Direction      | Service                          | Data                                                   |
| -------------- | -------------------------------- | ------------------------------------------------------ |
| **Upstream**   | position-balance-monitor-service | `position_snapshots` (live and batch position state)   |
| **Upstream**   | market-data-processing-service   | `market_data_for_risk` (prices for mark-to-market)     |
| **Downstream** | pnl-attribution-service          | `risk_metrics` (exposure snapshots for risk-adj PnL)   |
| **Downstream** | alerting-service                 | `risk_alerts_circuit_breaker_triggers` (breach alerts) |
| **Downstream** | client-reporting-api             | `risk_exposure_reports` (GET /risk/exposure, heatmaps) |

## Operations

| Operation | What it does                                                                                             | Expected output                                          |
| --------- | -------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| `compute` | VaR, exposure by strategy/venue/asset class, margin utilisation, drawdown monitoring, concentration risk | Risk metrics written to GCS / event sink, alerts emitted |

## CLI Reference

```bash
# Batch mode (one-time risk calculation across all configured clients)
.venv/bin/python -m risk_and_exposure_service --operation compute --mode batch \
  --start-date 2026-03-01 --end-date 2026-03-21

# Live mode (continuous risk monitoring loop + FastAPI server)
.venv/bin/python -m risk_and_exposure_service --operation compute --mode live --interval 60

# Dry-run (no alerts, no writes)
.venv/bin/python -m risk_and_exposure_service --operation compute --mode batch \
  --start-date 2026-03-01 --end-date 2026-03-21 --dry-run
```

**Note:** No `--category` argument. Risk is computed across all positions regardless of market category. `--dry-run` IS
supported (unlike pnl-attribution-service). Batch mode iterates over client IDs from `MONITORED_CLIENT_IDS` env var
union `RiskLimitsClient.list_client_ids()`. Live mode runs two concurrent tasks: risk monitoring loop + FastAPI server.

## Frontend Surface

| Endpoint / View                           | What it feeds                                              |
| ----------------------------------------- | ---------------------------------------------------------- |
| GET /risk/exposure (client-reporting-api) | Live and batch exposure data by strategy/venue/asset class |
| POST /risk/circuit-breaker                | Trigger circuit breaker for a strategy/venue               |
| POST /risk/kill-switch                    | Emergency kill-switch to halt all trading                  |
| Risk Dashboard (Observe UI)               | Risk exposure heatmaps, VaR charts, concentration gauges   |
| Margin utilisation gauges                 | Real-time margin usage per venue/account                   |

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

| #   | Operation | Mode  | Flags       | Expected                                                        | Status |
| --- | --------- | ----- | ----------- | --------------------------------------------------------------- | ------ |
| 2.1 | compute   | batch | `--dry-run` | Reads positions, computes risk, no GCS writes, no alerts sent   |        |
| 2.2 | compute   | batch | `--dry-run` | Logs "DRY RUN" confirmation                                     |        |
| 2.3 | compute   | batch |             | Missing `MONITORED_CLIENT_IDS` and empty limits DB logs warning |        |
| 2.4 | compute   | batch |             | Missing `--start-date`/`--end-date` handled (batch-specific)    |        |

```bash
# 2.1: Dry-run batch compute
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  MONITORED_CLIENT_IDS=test-client-001 \
  .venv/bin/python -c "
from risk_and_exposure_service.cli.main import main
import sys
sys.argv = ['risk_and_exposure_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-20', '--dry-run']
main()
"

# 2.3: No clients configured — should warn and exit cleanly
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from risk_and_exposure_service.cli.main import main
import sys
sys.argv = ['risk_and_exposure_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-20']
main()
"
```

### Phase 3: Real Writes (dev environment only)

| #   | Operation | Mode  | GCS check                                                    | Status |
| --- | --------- | ----- | ------------------------------------------------------------ | ------ |
| 3.1 | compute   | batch | Risk snapshots written to `RISK_SNAPSHOTS_GCS_BUCKET`        |        |
| 3.2 | compute   | batch | Verify path: `risk/{client_id}/{date}/exposure_summary.json` |        |
| 3.3 | compute   | batch | Exposure aggregation computed per client                     |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
  TESTNET_MODE=mainnet MONITORED_CLIENT_IDS=test-client-001 \
  RISK_SNAPSHOTS_GCS_BUCKET=central-element-323112-risk-snapshots \
  .venv/bin/python -c "
from risk_and_exposure_service.cli.main import main
import sys
sys.argv = ['risk_and_exposure_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-21']
main()
"
```

After writes, verify GCS:

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('central-element-323112-risk-snapshots')
blobs = list(bucket.list_blobs(prefix='risk/test-client-001/', max_results=20))
print(f'Files written: {len(blobs)}')
for b in blobs[:5]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 4: Category Sweep

This service does NOT accept a `--category` argument. Risk is computed across all positions for each client, regardless
of market category. The category sweep validates that positions from different market categories are correctly included
in risk calculations.

| #   | Input data category  | Expected                                                          | Status |
| --- | -------------------- | ----------------------------------------------------------------- | ------ |
| 4.1 | CEFI positions       | VaR and exposure computed for CeFi exchange positions             |        |
| 4.2 | TRADFI positions     | Margin utilisation computed for TradFi broker positions           |        |
| 4.3 | DEFI positions       | DeFi exposure includes on-chain positions (collateral, LP tokens) |        |
| 4.4 | SPORTS positions     | Sports bet exposure tracked (open wagers, potential payout)       |        |
| 4.5 | PREDICTION positions | Service handles gracefully if no prediction positions exist       |        |
| 4.6 | Mixed positions      | Single client with cross-category positions — all included in VaR |        |

**Verification:** Configure a test client with positions across multiple categories. Run batch compute and inspect the
exposure summary to confirm all categories are represented.

### Phase 5: Live Mode

Live mode starts two concurrent async tasks: (1) risk monitoring loop at configurable interval, (2) FastAPI server for
pre-trade checks and exposure queries.

| #   | What                                            | Expected                                                   | Status |
| --- | ----------------------------------------------- | ---------------------------------------------------------- | ------ |
| 5.1 | `--operation compute --mode live --interval 60` | Starts risk monitor loop + FastAPI server concurrently     |        |
| 5.2 | Risk monitoring loop                            | Calls `monitor_client_risk()` every `--interval` seconds   |        |
| 5.3 | FastAPI server                                  | Listens on `config.api_host:config.api_port`               |        |
| 5.4 | Pre-trade risk check API                        | POST /risk/pre-trade-check returns approve/reject          |        |
| 5.5 | Circuit breaker trigger                         | Breach threshold emits alert via AlertManager              |        |
| 5.6 | Graceful shutdown                               | Ctrl-C stops monitor + server, closes position client      |        |
| 5.7 | Topology resolution                             | `get_messaging_protocol` and `get_storage_protocol` logged |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  MONITORED_CLIENT_IDS=test-client-001 \
  .venv/bin/python -c "
from risk_and_exposure_service.cli.main import main
import sys
sys.argv = ['risk_and_exposure_service', '--operation', 'compute', '--mode', 'live', '--interval', '30']
main()
"
```

#### Phase 5b: Mock/Real A/B

Run the same operation in both mock and real mode, compare outputs:

| #    | Mode | Expected                                                    | Status |
| ---- | ---- | ----------------------------------------------------------- | ------ |
| 5b.1 | Real | Risk metrics computed from actual position snapshots in GCS |        |
| 5b.2 | Mock | Mock pipeline (`run_mock_pipeline`) produces seed risk data |        |
| 5b.3 | A/B  | Mock output schema matches real output schema               |        |

```bash
# Real mode
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  MONITORED_CLIENT_IDS=test-client-001 \
  .venv/bin/python -c "
from risk_and_exposure_service.cli.main import main
import sys
sys.argv = ['risk_and_exposure_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-20']
main()
"

# Mock mode
CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true \
  .venv/bin/python -c "
from risk_and_exposure_service.cli.main import main
import sys
sys.argv = ['risk_and_exposure_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-20']
main()
"
```

### Phase 6: Mock Mode (scenario testing)

Mock mode is intercepted early in `main()` — if `RiskAndExposureServiceConfig().is_mock_mode()` returns True, the
service redirects to `run_mock_pipeline()` and exits. This bypasses the normal batch/live dispatch.

| #   | Scenario                 | What it tests                                 | Expected                              | Status |
| --- | ------------------------ | --------------------------------------------- | ------------------------------------- | ------ |
| 6.1 | Mock pipeline default    | `run_mock_pipeline()` produces seed risk data | Exit code 0, mock data generated      |        |
| 6.2 | Mock with local provider | `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`   | No GCS/cloud credentials required     |        |
| 6.3 | Mock output schema       | Fields match real risk output schema          | Same structure as real compute output |        |
| 6.4 | Mock no clients          | No `MONITORED_CLIENT_IDS` set in mock mode    | Mock pipeline handles gracefully      |        |
| 6.5 | config_source check      | `CLOUD_MOCK_MODE=true`                        | `config_source=local`, no GCS reads   |        |
| 6.6 | Stress scenario          | High number of clients / positions            | Service handles memory, no OOM        |        |

```bash
# 6.1: Default mock mode
CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true \
  .venv/bin/python -c "
from risk_and_exposure_service.cli.main import main
import sys
sys.argv = ['risk_and_exposure_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-20']
main()
"
```

### Phase 7: Observability

| #    | Check                       | Expected                                                         | Status |
| ---- | --------------------------- | ---------------------------------------------------------------- | ------ |
| 7.1  | ServiceRuntime log line     | Mode, environment, transport protocol, storage protocol logged   |        |
| 7.2  | UEI lifecycle events        | STARTED at boot, BATCH_STARTED/BATCH_COMPLETED or STOPPED/FAILED |        |
| 7.3  | correlation_id              | UUID generated and attached to all lifecycle events              |        |
| 7.4  | Topology logging            | `Transport protocol: X` and `Storage protocol: Y` logged         |        |
| 7.5  | CloudEventSink              | Event sink initialized with project_id and service_name          |        |
| 7.6  | GracefulShutdownHandler     | SIGTERM/SIGINT handled, clean exit with STOPPED event            |        |
| 7.7  | pre_crash_checkpoint        | `register_pre_crash_handlers` called at startup                  |        |
| 7.8  | setup_service_observability | Called with tracing enabled                                      |        |
| 7.9  | Position Monitor API URL    | Logged at startup for debugging connectivity                     |        |
| 7.10 | Client list logging         | Batch mode logs client count and IDs before processing           |        |

### Known Issues Audit

Check these patterns (from procedure.md fix strategies) before running:

| Pattern                      | Check                                                                | Status |
| ---------------------------- | -------------------------------------------------------------------- | ------ |
| `load_dotenv(override=True)` | Must be `override=False` — shell intent wins                         |        |
| Bucket resolution            | `RISK_SNAPSHOTS_GCS_BUCKET` used for snapshot sink                   |        |
| Protocol vs provider mapping | `get_messaging_protocol` / `get_storage_protocol` correctly resolved |        |
| asyncio nesting              | `main()` calls `asyncio.run()` once — no nesting                     |        |
| Mock mode redirect           | `is_mock_mode()` check before batch/live dispatch                    |        |
| Client ID sources            | Union of env var + risk-limits DB, deduplicated and sorted           |        |
| Empty client list            | Warning logged, clean exit (not crash)                               |        |
| GCS sink optional            | `RiskSnapshotSink` only created when `risk_snapshots_bucket` set     |        |
| Position client cleanup      | `position_client.close()` called in `finally` block                  |        |
| `--dry-run` enforcement      | Flag parsed but verify it actually suppresses writes and alerts      |        |

### AWS Testing

| #   | What                                 | Expected                       | Status |
| --- | ------------------------------------ | ------------------------------ | ------ |
| A.1 | `CLOUD_PROVIDER=aws ENVIRONMENT=dev` | S3 sink selected if configured |        |
| A.2 | AWS credentials absent               | Clear error, not a crash       |        |

### Frontend API Verification

After a successful batch compute, verify the downstream APIs serve correct data:

| #   | Endpoint                       | Expected                                                 | Status |
| --- | ------------------------------ | -------------------------------------------------------- | ------ |
| F.1 | GET /risk/exposure             | Returns exposure breakdown by strategy/venue/asset class |        |
| F.2 | GET /risk/exposure/{client_id} | Returns client-specific exposure summary                 |        |
| F.3 | POST /risk/circuit-breaker     | Triggers circuit breaker, returns confirmation           |        |
| F.4 | POST /risk/kill-switch         | Halts all trading, returns confirmation                  |        |
| F.5 | GET /risk/var                  | Returns VaR metrics per strategy/portfolio               |        |
| F.6 | GET /risk/margin               | Returns margin utilisation gauges per venue              |        |

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After risk-and-exposure-service passes all phases, proceed to `018_position_balance_monitor_service.md`
