---
title: "E2E Test: features-service (cross-instrument family)"
service: features-service (cross-instrument family)
date: 2026-03-22
status: pending
---

# E2E Test: features-service (cross-instrument family)

Follows `procedure.md`. Pipeline position: #8 (L3 features layer — aggregates upstream feature outputs).

## Upstream Dependencies

- **features-service (delta-one family)** — delta-one features (returns, momentum, trend) per instrument
- **features-service (volatility family)** — volatility features (realized vol, vol-of-vol, term structure) per instrument
- **market-data-processing-service** — multi-venue candle data (needed for cross-venue spread calculation)
- **instruments-service** — instrument universe definitions per category

All upstream services must have completed batch runs for the target date before this service can produce meaningful
output. In mock mode, pre-generated seed data bypasses upstream dependencies.

## Downstream Consumers

- **ml-training-service** — consumes cross-instrument features for model training
- **ml-inference-service** — consumes cross-instrument features for live prediction

## CLI Interface

```
features-service (cross-instrument family)
  --date DATE           Processing date (YYYY-MM-DD) [required]
  --asset-group CATEGORY   CEFI | DEFI | TRADFI [required]
  --mode MODE           batch | live [default: batch]
  --feature-groups GRP  Feature groups to calculate (default: all)
  --dry-run             Validate setup only, no writes
  --run-tag TAG         GCS output prefix (default: batch; use t1-recon for T+1 reconciliation)
```

**Note:** This service uses `--date` instead of `--start-date`/`--end-date`. No `--operation` flag — the service has a
single compute operation. Category is a required positional choice (CEFI, DEFI, TRADFI only — no SPORTS or PREDICTION).

## Feature Groups

| Group                     | What it computes                                           | Upstream needed         |
| ------------------------- | ---------------------------------------------------------- | ----------------------- |
| Cross-venue spreads       | Bid-ask spread differentials across venues for same symbol | Multi-venue candle data |
| Correlation matrices      | Rolling pairwise correlation between instruments           | Delta-one features      |
| Relative strength         | RSI-style ranking across instrument pairs                  | Delta-one features      |
| Pair statistics           | Cointegration, half-life, z-score for pair trades          | Delta-one + volatility  |
| Cross-instrument momentum | Momentum signals aggregated across related instruments     | Delta-one features      |

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

| #   | Category | Feature groups | Expected                                                       | Status |
| --- | -------- | -------------- | -------------------------------------------------------------- | ------ |
| 2.1 | CEFI     | (all)          | Reads delta-one + volatility features from GCS, no writes      |        |
| 2.2 | TRADFI   | (all)          | Reads delta-one + volatility features from GCS, no writes      |        |
| 2.3 | DEFI     | (all)          | Reads delta-one + volatility features from GCS, no writes      |        |
| 2.4 | CEFI     | spreads only   | `--feature-groups cross_venue_spreads`, only spread group runs |        |
| 2.5 | CEFI     | correlations   | `--feature-groups correlation_matrices`, only correlation runs |        |

Verify for each:

- Log shows "Dry run mode - validation complete"
- No GCS writes (check for "UCI dry-run mode ACTIVE")
- UEI events: VALIDATION_STARTED, VALIDATION_COMPLETED, STOPPED

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Category | CSV check                               | GCS check                         | Status |
| --- | -------- | --------------------------------------- | --------------------------------- | ------ |
| 3.1 | CEFI     | Inspect CSV — correlation matrix shape  | Verify parquet in features bucket |        |
| 3.2 | TRADFI   | Inspect CSV — pair statistics columns   | Verify parquet in features bucket |        |
| 3.3 | DEFI     | Inspect CSV — cross-venue spread values | Verify parquet in features bucket |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
  TESTNET_MODE=mainnet ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples \
  .venv/bin/python -c "
from features_cross_instrument_service.cli.main import main
import sys
sys.argv = ['features-cross-instrument', '--date', '2026-03-22', \
            '--asset-group', 'CEFI', '--mode', 'batch']
main()
"
```

After each run, verify GCS:

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('<features-bucket>')
blobs = list(bucket.list_blobs(prefix='cross-instrument/day=2026-03-22/', max_results=20))
print(f'Files written: {len(blobs)}')
for b in blobs[:5]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 4: Category Sweep

| #   | Category   | Expected                                                                | Status |
| --- | ---------- | ----------------------------------------------------------------------- | ------ |
| 4.1 | CEFI       | Cross-venue spreads across 17+ CeFi venues, correlation matrices        |        |
| 4.2 | TRADFI     | Pair statistics for equity/futures pairs, relative strength rankings    |        |
| 4.3 | DEFI       | Cross-protocol spreads (Aave/Uniswap/Hyperliquid), DeFi correlations    |        |
| 4.4 | SPORTS     | Not a valid category for this service — CLI rejects with argparse error |        |
| 4.5 | PREDICTION | Not a valid category for this service — CLI rejects with argparse error |        |

**Note:** Unlike most services, this CLI enforces `choices=["CEFI", "DEFI", "TRADFI"]` at the argparse level. SPORTS and
PREDICTION are rejected before the service starts. Verify argparse produces a clear error message, not a traceback.

```bash
for cat in CEFI TRADFI DEFI; do
  echo "=== $cat ==="
  CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
    .venv/bin/python -c "
from features_cross_instrument_service.cli.main import main
import sys
sys.argv = ['features-cross-instrument', '--date', '2026-03-22', \
            '--asset-group', '$cat', '--mode', 'batch']
main()
" 2>&1 | tail -10
done
```

Verify SPORTS/PREDICTION rejection:

```bash
.venv/bin/python -c "
from features_cross_instrument_service.cli.main import main
import sys
sys.argv = ['features-cross-instrument', '--date', '2026-03-22', \
            '--asset-group', 'SPORTS', '--mode', 'batch']
main()
" 2>&1 | tail -5
# Expected: argparse error "invalid choice: 'SPORTS'"
```

### Phase 5: Live Mode

Live mode subscribes to upstream feature-ready events and computes cross-instrument features incrementally.

| #   | What                             | Expected                                                         | Status |
| --- | -------------------------------- | ---------------------------------------------------------------- | ------ |
| 5.1 | `--mode live --asset-group CEFI` | LiveHandler starts, subscribes to upstream events                |        |
| 5.2 | Feature group filtering          | `--feature-groups cross_venue_spreads` limits live computation   |        |
| 5.3 | Event logging                    | UEI events: STARTED, per-group COMPLETED/FAILED, final COMPLETED |        |
| 5.4 | Graceful shutdown                | Ctrl-C → clean exit, no partial writes                           |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from features_cross_instrument_service.cli.main import main
import sys
sys.argv = ['features-cross-instrument', '--date', '2026-03-22', \
            '--asset-group', 'CEFI', '--mode', 'live']
main()
"
```

#### Phase 5b: Mock/Real A/B Comparison

Run the same date+category in both mock and real mode. Compare output schemas and value distributions:

| #    | Check                  | Expected                                                     | Status |
| ---- | ---------------------- | ------------------------------------------------------------ | ------ |
| 5b.1 | Schema parity          | Mock and real output have identical column names and dtypes  |        |
| 5b.2 | Row count plausibility | Mock produces non-zero rows; real produces >= mock row count |        |
| 5b.3 | Value range            | Correlation values in [-1, 1]; spreads non-negative          |        |
| 5b.4 | NaN density            | Mock has 0% NaN; real may have some but < 20%                |        |

```bash
# Mock run
CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true \
  ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples/mock \
  .venv/bin/python -c "
from features_cross_instrument_service.cli.main import main
import sys
sys.argv = ['features-cross-instrument', '--date', '2026-03-22', \
            '--asset-group', 'CEFI', '--mode', 'batch']
main()
"

# Real run
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
  ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples/real \
  .venv/bin/python -c "
from features_cross_instrument_service.cli.main import main
import sys
sys.argv = ['features-cross-instrument', '--date', '2026-03-22', \
            '--asset-group', 'CEFI', '--mode', 'batch']
main()
"

# Compare schemas
diff <(head -1 ./data/samples/mock/*.csv) <(head -1 ./data/samples/real/*.csv)
```

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                  | What it tests                                  | Expected                                         | Status |
| --- | ------------------------- | ---------------------------------------------- | ------------------------------------------------ | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true`    | Mock pipeline redirect                         | "MOCK MODE: redirecting to mock pipeline" logged |        |
| 6.2 | Missing upstream features | Delta-one features absent for target date      | Clear error, no crash, log explains missing dep  |        |
| 6.3 | Single instrument         | Only one instrument in category                | Correlation matrix is 1x1, pair stats empty      |        |
| 6.4 | High cardinality          | 500+ instruments                               | Memory stays bounded, no OOM                     |        |
| 6.5 | Partial upstream failure  | Volatility features present, delta-one missing | Computes what it can, logs missing groups        |        |
| 6.6 | config_source check       | `CLOUD_MOCK_MODE=true`                         | `config_source=local`, no GCS reads              |        |

### Phase 7: Observability

| #   | Check                 | Expected                                                | Status |
| --- | --------------------- | ------------------------------------------------------- | ------ |
| 7.1 | Service startup log   | Category, date, mode, feature groups all logged         |        |
| 7.2 | UEI events            | STARTED, VALIDATION_STARTED/COMPLETED, COMPLETED/FAILED |        |
| 7.3 | Shard-level isolation | One feature group failure doesn't crash others          |        |
| 7.4 | Dry-run warning       | "Dry run mode - validation complete" logged             |        |
| 7.5 | Error classification  | Upstream read failures emit structured error events     |        |
| 7.6 | Memory watchdog       | "Memory watchdog started" logged                        |        |
| 7.7 | Correlation ID        | All events carry correlation_id from startup            |        |

## Known Issues Audit

Check for these patterns known from earlier services:

| Pattern                      | What to check                                                     | Status |
| ---------------------------- | ----------------------------------------------------------------- | ------ |
| `load_dotenv(override=True)` | Should be `override=False` — shell intent wins                    |        |
| `os.getenv()` usage          | Should use `UnifiedCloudConfig` or `get_settings()`               |        |
| Hardcoded bucket names       | Should use `get_bucket_name()` or config-derived                  |        |
| asyncio nesting              | `asyncio.run()` inside `asyncio.run()` in handler chain           |        |
| Bare `raise` in loops        | Feature group loops must isolate failures (shard-level isolation) |        |
| `routing_key=` in data sinks | Should use `bucket=get_bucket_name(domain, category)`             |        |
| Category bucket routing      | DEFI features must write to DEFI bucket, not CEFI                 |        |
| `--dry-run` enforcement      | Dry-run must prevent ALL writes, not just some                    |        |

## AWS Testing

| #   | What                         | Expected                                   | Status |
| --- | ---------------------------- | ------------------------------------------ | ------ |
| A.1 | `CLOUD_PROVIDER=aws` startup | Accepted if AWS credentials configured     |        |
| A.2 | S3 write path                | Features written to S3 with correct prefix |        |
| A.3 | Provider mapping             | `s3` protocol maps to `aws` backend        |        |

Skip if AWS credentials are not configured locally.

## Frontend API Surface

This service feeds the following frontend components:

| Frontend component         | API endpoint / data path                   | What it renders                  |
| -------------------------- | ------------------------------------------ | -------------------------------- |
| Correlation heatmap        | Cross-instrument correlation matrix output | Pairwise instrument correlations |
| Pair trading analysis      | Pair statistics (cointegration, z-score)   | Pair trade candidates + signals  |
| Cross-instrument dashboard | Relative strength + momentum rankings      | Instrument ranking tables        |
| Cross-venue spread monitor | Cross-venue spread time series             | Spread convergence/divergence    |

Verify that output parquet schemas match what the frontend APIs expect. Check column names against API contract
definitions in UAC.

## Issues Found

(logged in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After features-service (cross-instrument family) passes all phases → proceed to `009_features_multi_timeframe_service.md`
