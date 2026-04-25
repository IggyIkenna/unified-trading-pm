---
title: "E2E Test: pnl-attribution-service"
service: pnl-attribution-service
date: 2026-03-22
status: pending
---

# E2E Test: pnl-attribution-service

Follows `procedure.md`. Pipeline position: #16 (L6 monitoring layer).

## Upstream / Downstream

| Direction      | Service                   | Data                                                              |
| -------------- | ------------------------- | ----------------------------------------------------------------- |
| **Upstream**   | execution-service         | `order_lifecycle_events` (fills, orders, execution timestamps)    |
| **Upstream**   | risk-and-exposure-service | `risk_metrics` (exposure snapshots for risk-adjusted attribution) |
| **Downstream** | client-reporting-api      | `pnl_reports` (GET /pnl/\*, P&L Attribution tab, equity curves)   |

## Operations

| Operation | What it does                                                                                                           | Expected output                                     |
| --------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `compute` | PnL breakdown by strategy, venue, instrument, time period. Attribution: alpha vs beta, market vs specific, fees impact | PnL attribution records written to GCS / event sink |

## CLI Reference

```bash
# Batch mode (required: --start-date, --end-date)
.venv/bin/python -m pnl_attribution_service --operation compute --mode batch \
  --start-date 2026-03-01 --end-date 2026-03-21

# Live mode (--interval in minutes, default 15)
.venv/bin/python -m pnl_attribution_service --operation compute --mode live --interval 15

# Health API server
.venv/bin/python -m pnl_attribution_service --serve
```

**Note:** No `--asset-group` argument. This service processes all fills/orders from execution-service regardless of
market category. No `--dry-run` flag in the parser — dry-run behavior must be verified at the framework level
(ServiceRuntime / UCI).

## Frontend Surface

| Endpoint / View                    | What it feeds                                                                 |
| ---------------------------------- | ----------------------------------------------------------------------------- |
| GET /pnl/\* (client-reporting-api) | PnL reports by strategy, venue, instrument, time period                       |
| P&L Attribution tab (Reports UI)   | Alpha vs beta decomposition, market vs specific return, fees impact breakdown |
| PnL time-series                    | 180 daily points per strategy for equity curves                               |
| Dashboard strategy cards           | Sharpe ratio, cumulative returns, max drawdown per strategy                   |

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

No `--dry-run` flag in the CLI parser. Dry-run must be tested via UCI framework-level dry-run mode if supported, or this
phase validates that the service starts, connects to upstream data, and logs correctly without causing side effects.

| #   | Operation | Mode  | Expected                                                         | Status |
| --- | --------- | ----- | ---------------------------------------------------------------- | ------ |
| 2.1 | compute   | batch | Reads execution fills from GCS, computes PnL, attempts GCS write |        |
| 2.2 | compute   | batch | Missing `--start-date`/`--end-date` triggers parser error        |        |
| 2.3 | compute   | batch | Empty fills (no execution data for date range) returns cleanly   |        |

```bash
# 2.1: Batch compute with date range
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from pnl_attribution_service.cli.main import run_cli
import sys
sys.argv = ['pnl_attribution_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-01', '--end-date', '2026-03-01']
run_cli()
"

# 2.2: Missing date args should error
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from pnl_attribution_service.cli.main import run_cli
import sys
sys.argv = ['pnl_attribution_service', '--operation', 'compute', '--mode', 'batch']
run_cli()
"
```

### Phase 3: Real Writes (dev environment only)

| #   | Operation | Mode  | GCS check                                                                          | Status |
| --- | --------- | ----- | ---------------------------------------------------------------------------------- | ------ |
| 3.1 | compute   | batch | PnL attribution records written to GCS pnl bucket                                  |        |
| 3.2 | compute   | batch | Verify attribution breakdown fields: strategy, venue, instrument, alpha/beta, fees |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
  TESTNET_MODE=mainnet ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples \
  .venv/bin/python -c "
from pnl_attribution_service.cli.main import run_cli
import sys
sys.argv = ['pnl_attribution_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-21']
run_cli()
"

# Inspect output
ls -la ./data/samples/
head -5 ./data/samples/*.csv
```

After writes, verify GCS:

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('<pnl-bucket-name>')
blobs = list(bucket.list_blobs(prefix='pnl/day=2026-03-20/', max_results=20))
print(f'Files written: {len(blobs)}')
for b in blobs[:5]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 4: Category Sweep

This service does NOT accept a `--asset-group` argument. It processes all fills from execution-service across all
categories. The category sweep validates that fills from different market categories are correctly attributed.

| #   | Input data category | Expected                                                        | Status |
| --- | ------------------- | --------------------------------------------------------------- | ------ |
| 4.1 | CEFI fills          | PnL attributed correctly for CeFi venue fills                   |        |
| 4.2 | TRADFI fills        | PnL attributed correctly for TradFi venue fills                 |        |
| 4.3 | DEFI fills          | PnL attributed correctly for DeFi venue fills (gas fees impact) |        |
| 4.4 | SPORTS fills        | PnL attributed correctly for sports bet settlements             |        |
| 4.5 | PREDICTION fills    | Service handles gracefully if no prediction fills exist         |        |
| 4.6 | Mixed fills         | Single run attributes across all categories correctly           |        |

**Verification:** Since there is no `--asset-group` flag, run a single batch compute over a date range that contains
fills from multiple categories. Inspect the output to confirm per-category attribution is present.

### Phase 5: Live Mode

| #   | What                                            | Expected                                                   | Status |
| --- | ----------------------------------------------- | ---------------------------------------------------------- | ------ |
| 5.1 | `--operation compute --mode live --interval 15` | Starts live PnL computation loop, runs every 15 min        |        |
| 5.2 | Event sink selection                            | PubSub sink when messaging=pubsub, GCS sink otherwise      |        |
| 5.3 | Topology resolution                             | `get_messaging_protocol` and `get_storage_protocol` logged |        |
| 5.4 | Graceful shutdown                               | Ctrl-C triggers GracefulShutdownHandler, clean exit        |        |
| 5.5 | UEI lifecycle events                            | STARTED at boot, STOPPED on clean exit                     |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from pnl_attribution_service.cli.main import run_cli
import sys
sys.argv = ['pnl_attribution_service', '--operation', 'compute', '--mode', 'live', '--interval', '15']
run_cli()
"
```

#### Phase 5b: Mock/Real A/B

Run the same operation in both mock and real mode, compare outputs:

| #    | Mode | Expected                                              | Status |
| ---- | ---- | ----------------------------------------------------- | ------ |
| 5b.1 | Real | PnL computed from actual execution fills in GCS       |        |
| 5b.2 | Mock | Mock pipeline (`run_mock_pipeline`) produces seed PnL |        |
| 5b.3 | A/B  | Mock output schema matches real output schema         |        |

```bash
# Real mode
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from pnl_attribution_service.cli.main import run_cli
import sys
sys.argv = ['pnl_attribution_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-20']
run_cli()
"

# Mock mode
CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true \
  .venv/bin/python -c "
from pnl_attribution_service.cli.main import run_cli
import sys
sys.argv = ['pnl_attribution_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-20']
run_cli()
"
```

### Phase 6: Mock Mode (scenario testing)

Mock mode is intercepted early in `run_cli()` — if `config.is_mock_mode()` returns True, the service redirects to
`run_mock_pipeline()` and exits. This bypasses CLI arg parsing for operation/mode.

| #   | Scenario                 | What it tests                                | Expected                                  | Status |
| --- | ------------------------ | -------------------------------------------- | ----------------------------------------- | ------ |
| 6.1 | Mock pipeline default    | `run_mock_pipeline()` produces seed PnL data | Exit code 0, mock data generated          |        |
| 6.2 | Mock with local provider | `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`  | No GCS credentials required               |        |
| 6.3 | Mock output schema       | Fields match real PnL output schema          | Same columns/types as real compute output |        |
| 6.4 | Mock empty fills         | No execution data in mock seed               | Returns cleanly with empty PnL            |        |
| 6.5 | config_source check      | `CLOUD_MOCK_MODE=true`                       | `config_source=local`, no GCS reads       |        |

```bash
# 6.1: Default mock mode
CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true \
  .venv/bin/python -c "
from pnl_attribution_service.cli.main import run_cli
import sys
sys.argv = ['pnl_attribution_service', '--operation', 'compute', '--mode', 'batch',
            '--start-date', '2026-03-20', '--end-date', '2026-03-20']
run_cli()
"
```

### Phase 7: Observability

| #   | Check                       | Expected                                                          | Status |
| --- | --------------------------- | ----------------------------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line     | All dimensions logged (mode, cloud_provider, data_mode)           |        |
| 7.2 | UEI lifecycle events        | STARTED emitted at boot, STOPPED/FAILED at exit                   |        |
| 7.3 | correlation_id              | UUID generated and attached to all lifecycle events               |        |
| 7.4 | Topology logging            | `Topology: messaging=X storage=Y (mode=Z)` logged                 |        |
| 7.5 | Event sink selection        | PubSubEventSink or GCSEventSink selected based on messaging proto |        |
| 7.6 | GracefulShutdownHandler     | SIGTERM/SIGINT handled, clean exit                                |        |
| 7.7 | Health API                  | `--serve` starts uvicorn on HEALTH_PORT (default 8009)            |        |
| 7.8 | setup_service_observability | Called with tracing enabled                                       |        |

### Phase 8: Backtest Chain Validation (execution fills → PnL → positions)

Verify PnL-attribution can consume execution-service backtest output and produce correct attribution, and that the two
independent PnL sources (strategy-service PnL, PnL-attribution from fills) reconcile.

#### 8a: Backtest Fill Ingestion

| #    | What                                       | Expected                                                                               | Status |
| ---- | ------------------------------------------ | -------------------------------------------------------------------------------------- | ------ |
| 8a.1 | Read backtest fills from execution-service | `PnlDomainAdapter.read_fills()` successfully parses backtest parquet                   |        |
| 8a.2 | Backtest fill schema accepted              | Extra backtest columns (`simulated`, `slippage_model`, `gas_cost`) do not break parser |        |
| 8a.3 | All fills ingested                         | Fill count from PnL matches fill count from execution-service output                   |        |
| 8a.4 | strategy_id preserved                      | Attribution groups correctly by `strategy_id`                                          |        |
| 8a.5 | DeFi venue fills handled                   | DeFi venue fills (Uniswap, Aave, etc.) attributed correctly                            |        |

#### 8b: DeFi-Specific Attribution

| #    | What                     | Expected                                                                           | Status |
| ---- | ------------------------ | ---------------------------------------------------------------------------------- | ------ |
| 8b.1 | Gas fee attribution      | Gas costs from DeFi fills attributed as separate cost component                    |        |
| 8b.2 | Protocol fee attribution | Uniswap/Aave protocol fees broken out from execution cost                          |        |
| 8b.3 | MEV cost attribution     | MEV exposure cost (if modeled) attributed separately                               |        |
| 8b.4 | Multi-leg attribution    | Recursive staked basis (N fills per instruction) attributed as single strategy PnL |        |
| 8b.5 | DeFi alpha decomposition | Alpha vs beta for DeFi strategies — benchmark = protocol base yield                |        |

#### 8c: Strategy PnL ↔ Attribution Reconciliation

| #    | What                                          | Expected                                                                  | Status |
| ---- | --------------------------------------------- | ------------------------------------------------------------------------- | ------ |
| 8c.1 | Strategy-service PnL (gross)                  | From `strategy-store-*/backtest/` results                                 |        |
| 8c.2 | PnL-attribution PnL (net of execution costs)  | From `pnl-store-*/pnl/` attribution output                                |        |
| 8c.3 | Reconciliation: gross - execution costs ≈ net | `strategy_pnl - (slippage + gas + protocol_fees + mev) ≈ attribution_pnl` |        |
| 8c.4 | Tolerance check                               | Difference < 1% of gross PnL (or exact if no execution cost modeling)     |        |
| 8c.5 | Per-strategy reconciliation                   | Check holds for each `strategy_id`, not just aggregate                    |        |
| 8c.6 | Execution alpha extraction                    | `execution_alpha = arrival_price_pnl - actual_fill_pnl` (per-strategy)    |        |

#### 8d: Arrival Price Benchmark

| #    | What                                     | Expected                                                            | Status |
| ---- | ---------------------------------------- | ------------------------------------------------------------------- | ------ |
| 8d.1 | Arrival price from strategy instructions | `read_strategy_instructions_path()` provides instruction price      |        |
| 8d.2 | Benchmark = instruction price            | Execution alpha measured against strategy's intended price          |        |
| 8d.3 | Current VWAP benchmark replaced          | If using VWAP, flag as known limitation; arrival price is preferred |        |

#### 8e: Grid Result Aggregation

| #    | What                              | Expected                                                                   | Status |
| ---- | --------------------------------- | -------------------------------------------------------------------------- | ------ |
| 8e.1 | PnL attribution across grid cells | Run attribution for each grid cell's execution output                      |        |
| 8e.2 | Cross-cell comparison             | Aggregate: best/worst Sharpe, total execution cost, alpha ranking          |        |
| 8e.3 | Config style impact on PnL        | Different config styles produce materially different PnL profiles          |        |
| 8e.4 | Optimal config identification     | Grid aggregation surface shows which config maximizes risk-adjusted return |        |

### Known Issues Audit

Check these patterns (from procedure.md fix strategies) before running:

| Pattern                      | Check                                                           | Status |
| ---------------------------- | --------------------------------------------------------------- | ------ |
| `load_dotenv(override=True)` | Must be `override=False` — shell intent wins                    |        |
| Bucket resolution            | Uses `get_bucket_name()` not `routing_key=`                     |        |
| Protocol vs provider mapping | `gcs` mapped to `gcp` correctly in sink selection               |        |
| asyncio nesting              | `run_cli()` is sync, no nested `asyncio.run()` detected         |        |
| Mock mode redirect           | `is_mock_mode()` check before CLI parsing — verify args ignored |        |
| Health port config           | `HEALTH_PORT` env var respected, default 8009                   |        |
| `--start-date`/`--end-date`  | Required for batch, enforced in `run_cli()` (not just parser)   |        |

### AWS Testing

| #   | What                                 | Expected                       | Status |
| --- | ------------------------------------ | ------------------------------ | ------ |
| A.1 | `CLOUD_PROVIDER=aws ENVIRONMENT=dev` | S3 sink selected if configured |        |
| A.2 | AWS credentials absent               | Clear error, not a crash       |        |

### Frontend API Verification

After a successful batch compute, verify the downstream API serves correct data:

| #   | Endpoint                        | Expected                                            | Status |
| --- | ------------------------------- | --------------------------------------------------- | ------ |
| F.1 | GET /pnl/summary                | Returns PnL summary for computed date range         |        |
| F.2 | GET /pnl/attribution/{strategy} | Returns alpha/beta decomposition for given strategy |        |
| F.3 | GET /pnl/timeseries/{strategy}  | Returns up to 180 daily equity curve points         |        |
| F.4 | GET /pnl/by-venue               | Returns PnL breakdown by venue                      |        |
| F.5 | GET /pnl/by-instrument          | Returns PnL breakdown by instrument                 |        |

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After pnl-attribution-service passes all phases, proceed to `017_risk_and_exposure_service.md`
