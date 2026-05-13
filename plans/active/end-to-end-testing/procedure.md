# End-to-End Service Testing Procedure

## Purpose

Systematically run each service through every valid infrastructure configuration combination. Find bugs at the service
level before they reach staging. Each service is tested, issues are logged in `plans/active/issues/`, fixes are applied,
then we move to the next service — carrying forward all fixes so each iteration gets faster.

## Test Axes (the grid)

Every service is tested across these dimensions:

| Axis               | Values                                             | Env var / flag        |
| ------------------ | -------------------------------------------------- | --------------------- |
| **Operation**      | Per-service (instruments, download, compute, etc.) | `--operation`         |
| **Mode**           | `batch`, `live`                                    | `--mode`              |
| **Cloud provider** | `gcp`, `local`                                     | `CLOUD_PROVIDER`      |
| **Data mode**      | `mock` (true), `real` (false)                      | `CLOUD_MOCK_MODE`     |
| **Environment**    | `dev`, `staging` (never `prod` in local testing)   | `ENVIRONMENT`         |
| **Testnet**        | `mainnet`, `testnet`                               | `TESTNET_MODE`        |
| **Category**       | `CEFI`, `TRADFI`, `DEFI`, `SPORTS`, `PREDICTION`   | `--asset-group`       |
| **Dry-run**        | on/off                                             | `--dry-run`           |
| **Scenario**       | `default`, `stress`                                | `--scenario`          |
| **CSV sampling**   | on/off                                             | `ENABLE_CSV_SAMPLING` |

Not all combinations are valid. The procedure defines which matter per service.

## Excluded Combinations

- `ENVIRONMENT=prod` — never in local dev
- `CLOUD_PROVIDER=aws` — unless AWS credentials are configured
- `--mode live` for pure batch services (instruments, features, ml-training)
- `TESTNET_MODE=testnet` for services that don't interact with exchanges

## Pre-Requisites

```bash
# Install latest libraries in service venv
cd <service-repo>
uv pip install -e ../unified-internal-contracts/ -e ../unified-trading-library/ \
  -e ../unified-cloud-interface/ -e ../unified-config-interface/ --python .venv/bin/python

# Verify ServiceRuntime works
.venv/bin/python -c "from unified_trading_library import ServiceRuntime; print('OK')"
```

## Per-Service Test Protocol

### Phase 1: Startup Validation (no network, fast)

Test that ServiceRuntime validates all env var combinations correctly:

```bash
# Valid combos — should log ServiceRuntime line and exit cleanly
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "from unified_trading_library import ServiceRuntime; \
  rt = ServiceRuntime.from_env_and_args(operation='<op>', mode='batch', service_name='<svc>'); \
  print(f'OK: {rt.mode.value} {rt.cloud_provider.value} {rt.data_mode.value}')"

# Invalid combos — should print STARTUP_VALIDATION_FAILED
CLOUD_PROVIDER=azure .venv/bin/python -c "from unified_trading_library.startup_validation import validate_env_vars; validate_env_vars()"
TESTNET_MODE=sandbox .venv/bin/python -c "from unified_trading_library.startup_validation import validate_env_vars; validate_env_vars()"
```

### Phase 2: Dry-Run (network, no writes)

Run each operation with `--dry-run`. Verify:

- Service starts, fetches data from sources (APIs, exchanges)
- No GCS/S3 writes (check logs for "UCI dry-run mode ACTIVE")
- Events are logged (check UEI output)
- Errors are classified (check for ADAPTER_FETCH_FAILED events)

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from <service>.cli.main import main_service_cli
import sys
sys.argv = ['<service>', '--operation', '<op>', '--mode', 'batch', \
            '--asset-group', 'CEFI', '--start-date', '2025-01-01', \
            '--end-date', '2025-01-01', '--dry-run']
main_service_cli()
"
```

### Phase 3: Real Writes (dev environment only)

Run with real GCS writes but in dev environment. Enable CSV sampling for local inspection:

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
  TESTNET_MODE=mainnet ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples \
  .venv/bin/python -c "
from <service>.cli.main import main_service_cli
import sys
sys.argv = ['<service>', '--operation', '<op>', '--mode', 'batch', \
            '--asset-group', 'CEFI', '--start-date', '2025-01-01', \
            '--end-date', '2025-01-01']
main_service_cli()
"

# Inspect CSV samples
ls -la ./data/samples/
head -5 ./data/samples/*.csv
```

### Phase 4: Category Sweep (MANDATORY — every category, no skipping)

**You MUST run every category: CEFI, TRADFI, DEFI, SPORTS, PREDICTION.** Do NOT skip a category because "it's not
relevant" or "it'll be empty". The purpose is to find routing bugs, missing venue wiring, and category-specific
failures.

If a category returns empty: that's a finding. Log it. Explain why. If it SHOULD have data (e.g. SPORTS should have
sportsbook fixtures), that's a bug — fix it.

If a category isn't yet supported (e.g. PREDICTION): the service must handle it explicitly — clear log message, return
empty, no crash, no fallthrough to other categories.

**Run each category with a REAL write (not just dry-run) and VERIFY GCS:**

```bash
for cat in CEFI TRADFI DEFI SPORTS PREDICTION; do
  echo "=== $cat ==="
  CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
    .venv/bin/python -c "
from <service>.cli.main import main_service_cli
import sys
sys.argv = ['<service>', '--operation', '<op>', '--mode', 'batch', \
            '--asset-group', '$cat', '--start-date', '2026-03-21', \
            '--end-date', '2026-03-21', '--force']
main_service_cli()
" 2>&1 | tail -10
done
```

After each run, **verify the data landed in GCS**:

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('<bucket-name>')
blobs = list(bucket.list_blobs(prefix='day=2026-03-21/', max_results=20))
print(f'Files written: {len(blobs)}')
for b in blobs[:5]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

Don't assume writes worked because the log says "Uploaded". Check GCS directly.

### Phase 5: Live Mode (if applicable)

For services that support live mode (market-tick-data, strategy, execution, position-balance-monitor):

```bash
# Live mode with testnet (safe — no real orders)
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false TESTNET_MODE=testnet \
  .venv/bin/python -c "
from <service>.cli.main import main_service_cli
import sys
sys.argv = ['<service>', '--operation', 'live', '--mode', 'live', '--asset-group', 'CEFI']
main_service_cli()
"
```

Check for:

- WebSocket connections established (UMI adapters)
- PubSub transport used (messaging=pubsub from topology)
- Event bus publishing (UEI events)
- Graceful shutdown on Ctrl-C
- Circuit breaker triggers on simulated failures

### Phase 6: Mock Mode

Run with `CLOUD_MOCK_MODE=true` and `CLOUD_PROVIDER=local`:

```bash
CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true \
  .venv/bin/python -c "
from <service>.cli.main import main_service_cli
import sys
sys.argv = ['<service>', '--operation', '<op>', '--mode', 'batch', \
            '--asset-group', 'CEFI', '--start-date', '2025-01-01', \
            '--end-date', '2025-01-01', '--scenario', 'stress']
main_service_cli()
"
```

Check for:

- Mock data generators produce output (UIC MockScenario)
- No cloud credentials required
- Config loaded from local YAML (config_source=local)
- Events logged to local sink

### Phase 7: Observability Check

For each run, verify:

- [ ] `ServiceRuntime:` log line with all dimensions
- [ ] UEI events emitted (STARTED, COMPLETED/FAILED)
- [ ] Error events have correlation_id
- [ ] Shard-level failure isolation (no crash on one venue failure)
- [ ] Memory watchdog active (for long-running)
- [ ] Prometheus metrics endpoint (if applicable)

## Fix Strategies (from instruments-service E2E)

These patterns will recur in every service. Fix them at the root, not per-service.

### Bucket Resolution: `routing_key` → `get_bucket_name()`

**Problem:** UCI `get_data_sink(routing_key="cefi")` resolves buckets from `PROTOCOL_DATA_SINK_BUCKET_CEFI` env vars.
When `.env` is cleaned up, those vars are gone → empty bucket → crash. **Fix:** Replace `get_data_sink(routing_key=X)`
with `get_data_sink(bucket=get_bucket_name(domain, category))`. UCI `get_bucket_name()` derives from project_id +
domain + category + environment. No env vars needed. **Apply to:** Every service that uses
`get_data_sink/get_data_source` with `routing_key=`.

### Protocol vs Provider: `gcs` ≠ `gcp`

**Problem:** Topology reader returns protocol names (`gcs`, `pubsub`, `s3`). UCI expects provider names (`gcp`, `aws`,
`local`). **Fix:** ServiceCLI maps `{"gcs": "gcp", "s3": "aws", "local": "local"}` when setting
`PROTOCOL_DATA_SINK_BACKEND`.

### Category Routing: Boolean flags vs Enum

**Problem:** Services use boolean flags (`cefi=True, tradfi=False`) instead of `MarketCategory` enum. New categories
(PREDICTION) aren't mapped → fall through to "process all". **Fix:** When all booleans are False but a category WAS
requested, don't default to all. Check if the requested category is unsupported and handle explicitly.

### asyncio Nesting

**Problem:** `BaseModeHandler.run()` is async (wrapped by ServiceCLI in `asyncio.run()`). Inner handlers call
`asyncio.run()` again → crash. **Fix:** `_run_sync_handler_in_thread()` — runs sync handlers in a `ThreadPoolExecutor`,
giving them their own event loop. Apply to every service where BaseModeHandler wrappers call sync code that internally
uses `asyncio.run()`.

### load_dotenv(override=True)

**Problem:** `.env` overrides explicit shell env vars. Operator sets `CLOUD_MOCK_MODE=true` on CLI but `.env` has
`false` → silent override → real writes. **Fix:** Always `override=False`. Shell intent wins.

### Cleanup After Runs

**Problem:** CSV samples, temp files, and parquet caches accumulate. **Fix:** After each E2E test:
`rm -rf ./data/samples/*.csv`. Add to procedure. Don't leave 250+ sample files from previous sessions.

## Issue Tracking

When an issue is found:

1. Add it to `plans/archive/issues/service_control_surface_issues_2026_03_21.md`
2. Note the service, severity, root cause, and fix approach
3. Add audit checklist for other services
4. Fix in the current service
5. Mark fixed, move to next service

## Service Order

Services are tested in pipeline order (upstream first → downstream):

1. **instruments-service** — pure data fetch, no upstream deps
2. **market-tick-data-service** — depends on instruments, has WebSocket/REST live mode
3. **features-service (onchain family)** — depends on market data, DeFi-specific
4. **features-service (delta-one family)** — depends on market data
5. **features-service (volatility family)** — depends on market data
6. **features-service (calendar family)** — depends on market data
7. **ml-training-service** — depends on features
8. **ml-inference-service** — depends on ML models
9. **strategy-service** — depends on features + ML, has live mode
10. **execution-service** — depends on strategy, has live mode, testnet
11. **pnl-attribution-service** — depends on execution
12. **risk-and-exposure-service** — depends on positions
13. **position-balance-monitor-service** — live mode, exchange connections
14. **alerting-service** — depends on all events

## Cleanup After Each Service

```bash
# Remove CSV samples
rm -rf ./data/samples/

# Check for any leaked temp files
find . -name "*.tmp" -not -path "./.venv*" -delete
```

## Service-Specific Notes

### instruments-service

- No live WebSocket — "live" means periodic batch (Cloud Run cron job)
- Categories: CEFI (19 venues), TRADFI (IBKR+EOD), DEFI (Aave/Uniswap/Hyperliquid), SPORTS (4 sportsbooks)
- PREDICTION: not yet implemented — should skip gracefully or return empty
- CSV sampling: `ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples`
- Known: asyncio nesting fixed via `_run_sync_handler_in_thread()`

### market-tick-data-service

- Live mode: WebSocket connections to exchanges (UMI adapters)
- Batch mode: REST API downloads (Tardis, Databento)
- Testnet: Binance testnet WebSocket, OKX testnet — need API keys in SM
- Known: asyncio nesting in DownloadOperation (uses `run_in_executor`)
- Sharding: `--shard-index` / `--total-shards` for parallel batch

### execution-service

- Live mode: order execution via UTEI adapters
- Testnet: CRITICAL — must use testnet to avoid real money
- No `--asset-group` (routing based on instruction content)
- Backtest mode: uses matching-engine-library internally

### strategy-service

- Live mode: consumes features, emits trade signals
- Backtest mode: replays historical data
- Needs ML models loaded (ml-inference dependency)
