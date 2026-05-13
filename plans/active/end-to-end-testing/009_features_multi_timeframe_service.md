---
title: "E2E Test: features-service (multi-timeframe family)"
service: features-service (multi-timeframe family)
date: 2026-03-22
status: pending
---

# E2E Test: features-service (multi-timeframe family)

Follows `procedure.md`. Pipeline position: #9 (L3b features layer — multi-resolution aggregation of delta-one features).

## Upstream Dependencies

- **features-service (delta-one family)** — single-timeframe delta-one features (`delta_one_features_multi_tf` source spec)

This service reads delta-one features computed at a base timeframe and re-aggregates them at multiple higher timeframes
(5m, 15m, 1h, 4h, 1d). It does NOT re-fetch market data — it operates entirely on pre-computed feature outputs.

## Downstream Consumers

- **ml-training-service** — consumes multi-timeframe feature vectors for model training
- **ml-inference-service** — consumes multi-timeframe features for live prediction

## CLI Interface

```
features-multi-timeframe
  --operation OP        compute | info [required]
  --mode MODE           batch | live [required]
  --asset-group CAT        Asset category (default: crypto)
  --date DATE           Date partition (YYYY-MM-DD, defaults to today)
  --verbose / -v        Enable DEBUG logging
  --run-tag TAG         GCS output prefix (default: batch; use t1-recon for T+1 reconciliation)
```

**Note:** This service uses `--operation` (standard CLI convention) unlike features-service (cross-instrument family). The `info`
operation prints service metadata (base timeframe, supported timeframes, enabled feature groups, source specs) without
doing any computation. Category defaults to `crypto` (maps to CEFI/DEFI) and is free-text — no argparse `choices`
restriction. No `--dry-run` flag — use `info` operation for validation. No `--feature-groups` filtering.

## Operations

| Operation | What it does                                                        | Expected output                        |
| --------- | ------------------------------------------------------------------- | -------------------------------------- |
| `compute` | Read delta-one features, aggregate at 5m/15m/1h/4h/1d, write to GCS | Multi-timeframe feature parquet files  |
| `info`    | Print service config: timeframes, feature groups, source specs      | Metadata to stdout, no GCS interaction |

## Timeframes

| Timeframe | Resolution | Use case                         |
| --------- | ---------- | -------------------------------- |
| 5m        | Short      | Scalping, high-frequency signals |
| 15m       | Medium     | Intraday swing detection         |
| 1h        | Medium     | Intraday trend confirmation      |
| 4h        | Long       | Swing trading, regime detection  |
| 1d        | Daily      | Position sizing, macro trend     |

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

### Phase 2: Dry-Run (info operation — metadata only, no writes)

This service has no `--dry-run` flag. The `info` operation serves as the dry-run equivalent — it validates config and
prints metadata without touching GCS.

| #   | Operation | Category | Expected                                                     | Status |
| --- | --------- | -------- | ------------------------------------------------------------ | ------ |
| 2.1 | info      | crypto   | Prints base timeframe, supported timeframes, feature groups  |        |
| 2.2 | info      | forex    | Prints config — may have empty instrument list               |        |
| 2.3 | compute   | crypto   | Reads delta-one features from GCS, computes MTF aggregations |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from features_multi_timeframe_service.cli.main import main
import sys
sys.argv = ['features-multi-timeframe', '--operation', 'info', '--mode', 'batch', '--asset-group', 'crypto']
main()
"
```

Verify for `info`:

- Service config printed: base_timeframe, supported_timeframes, enabled_feature_groups, source_feature_group_timeframes
- No GCS reads or writes
- Clean exit code 0

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Category | Date       | CSV check                                | GCS check                         | Status |
| --- | -------- | ---------- | ---------------------------------------- | --------------------------------- | ------ |
| 3.1 | crypto   | 2026-03-22 | Inspect CSV — verify 5 timeframe columns | Verify parquet in features bucket |        |
| 3.2 | crypto   | 2026-03-21 | Inspect CSV — prior date                 | Verify parquet partition exists   |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
  TESTNET_MODE=mainnet ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples \
  .venv/bin/python -c "
from features_multi_timeframe_service.cli.main import main
import sys
sys.argv = ['features-multi-timeframe', '--operation', 'compute', '--mode', 'batch', \
            '--asset-group', 'crypto', '--date', '2026-03-22']
main()
"

# Inspect CSV samples
ls -la ./data/samples/
head -5 ./data/samples/*.csv
```

After each run, verify GCS:

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('<features-bucket>')
blobs = list(bucket.list_blobs(prefix='multi-timeframe/day=2026-03-22/', max_results=20))
print(f'Files written: {len(blobs)}')
for b in blobs[:5]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 4: Category Sweep

The CLI accepts free-text `--asset-group` (no argparse restriction). Test how the service handles each value:

| #   | Category   | Expected                                                                    | Status |
| --- | ---------- | --------------------------------------------------------------------------- | ------ |
| 4.1 | crypto     | Primary category — reads CEFI/DEFI delta-one features, computes MTF         |        |
| 4.2 | forex      | May have no instruments — should handle empty gracefully, not crash         |        |
| 4.3 | CEFI       | Test if uppercase CEFI maps correctly (or if only lowercase "crypto" works) |        |
| 4.4 | TRADFI     | May not be supported — should return empty or log "no instruments"          |        |
| 4.5 | DEFI       | DeFi instruments — should produce MTF features if delta-one exists          |        |
| 4.6 | SPORTS     | Not applicable — should handle gracefully, return empty                     |        |
| 4.7 | PREDICTION | Not applicable — should handle gracefully, return empty                     |        |

**Key question:** Does `--asset-group crypto` correctly resolve to the right GCS paths for CEFI and DEFI features? Or
does it only read from a `crypto/` prefix? This is a potential routing bug — log the actual GCS read paths.

```bash
for cat in crypto forex CEFI TRADFI DEFI SPORTS PREDICTION; do
  echo "=== $cat ==="
  CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
    .venv/bin/python -c "
from features_multi_timeframe_service.cli.main import main
import sys
sys.argv = ['features-multi-timeframe', '--operation', 'compute', '--mode', 'batch', \
            '--asset-group', '$cat', '--date', '2026-03-22']
main()
" 2>&1 | tail -10
done
```

### Phase 5: Live Mode

Live mode subscribes to `features-delta-one-ready` events and processes MTF features as upstream data arrives.

| #   | What                                                   | Expected                                                    | Status |
| --- | ------------------------------------------------------ | ----------------------------------------------------------- | ------ |
| 5.1 | `--operation compute --mode live --asset-group crypto` | LiveHandler starts, subscribes to delta-one-ready           |        |
| 5.2 | Event subscription                                     | PubSub subscription established (or mock equivalent)        |        |
| 5.3 | Incremental processing                                 | New delta-one features trigger MTF recompute                |        |
| 5.4 | Graceful shutdown                                      | Ctrl-C → clean exit via `svc.shutdown()`, no partial writes |        |

```bash
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false TESTNET_MODE=mainnet \
  .venv/bin/python -c "
from features_multi_timeframe_service.cli.main import main
import sys
sys.argv = ['features-multi-timeframe', '--operation', 'compute', '--mode', 'live', '--asset-group', 'crypto']
main()
"
```

#### Phase 5b: Mock/Real A/B Comparison

Run the same date+category in both mock and real mode. Compare output schemas and value distributions:

| #    | Check                  | Expected                                                    | Status |
| ---- | ---------------------- | ----------------------------------------------------------- | ------ |
| 5b.1 | Schema parity          | Mock and real output have identical column names and dtypes |        |
| 5b.2 | Timeframe columns      | Both outputs contain features at all 5 timeframes           |        |
| 5b.3 | Row count plausibility | Mock produces non-zero rows; real produces comparable count |        |
| 5b.4 | NaN density            | Mock has 0% NaN; real may have some but < 20%               |        |
| 5b.5 | Temporal consistency   | 1d features change less frequently than 5m features         |        |

```bash
# Mock run
CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true \
  ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples/mock \
  .venv/bin/python -c "
from features_multi_timeframe_service.cli.main import main
import sys
sys.argv = ['features-multi-timeframe', '--operation', 'compute', '--mode', 'batch', \
            '--asset-group', 'crypto', '--date', '2026-03-22']
main()
"

# Real run
CLOUD_PROVIDER=gcp ENVIRONMENT=development CLOUD_MOCK_MODE=false \
  ENABLE_CSV_SAMPLING=true CSV_SAMPLE_DIR=./data/samples/real \
  .venv/bin/python -c "
from features_multi_timeframe_service.cli.main import main
import sys
sys.argv = ['features-multi-timeframe', '--operation', 'compute', '--mode', 'batch', \
            '--asset-group', 'crypto', '--date', '2026-03-22']
main()
"

# Compare schemas
diff <(head -1 ./data/samples/mock/*.csv) <(head -1 ./data/samples/real/*.csv)
```

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                     | What it tests                              | Expected                                         | Status |
| --- | ---------------------------- | ------------------------------------------ | ------------------------------------------------ | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true`       | Mock pipeline redirect                     | "MOCK MODE: redirecting to mock pipeline" logged |        |
| 6.2 | Missing delta-one features   | No upstream features for target date       | Clear error message, no crash                    |        |
| 6.3 | Single timeframe only        | Config has only 1h in supported_timeframes | Only 1h aggregation produced, others skipped     |        |
| 6.4 | High cardinality instruments | 500+ instruments across all timeframes     | Memory bounded, no OOM                           |        |
| 6.5 | Sparse base data             | 5m base has gaps (missing candles)         | Higher TFs handle NaN gracefully, no crash       |        |
| 6.6 | config_source check          | `CLOUD_MOCK_MODE=true`                     | `config_source=local`, no GCS reads              |        |
| 6.7 | `info` in mock mode          | `--operation info` with mock mode          | Prints config, no mock pipeline redirect         |        |

### Phase 7: Observability

| #   | Check                 | Expected                                                    | Status |
| --- | --------------------- | ----------------------------------------------------------- | ------ |
| 7.1 | Service startup log   | operation, mode, category all logged                        |        |
| 7.2 | UEI events            | STARTED (via BaseFeatureServiceV2.startup()), STOPPED       |        |
| 7.3 | Shard-level isolation | One timeframe aggregation failure doesn't crash others      |        |
| 7.4 | Info operation        | Clean metadata output, exit code 0                          |        |
| 7.5 | Error classification  | Upstream read failures emit structured error events         |        |
| 7.6 | Memory watchdog       | "Memory watchdog started" logged via start_memory_watchdog  |        |
| 7.7 | Tracing               | setup_tracing called for "features-service (multi-timeframe family)" |        |
| 7.8 | Async lifecycle       | `svc.startup()` and `svc.shutdown()` both called cleanly    |        |

## Known Issues Audit

Check for these patterns known from earlier services:

| Pattern                      | What to check                                                       | Status |
| ---------------------------- | ------------------------------------------------------------------- | ------ |
| `load_dotenv(override=True)` | Should be `override=False` — shell intent wins                      |        |
| `os.getenv()` usage          | Should use `UnifiedCloudConfig` — CLI already uses it for LOG_LEVEL |        |
| Hardcoded bucket names       | Should use `get_bucket_name()` or config-derived                    |        |
| asyncio nesting              | CLI uses single `asyncio.run(_async_main())` — check handlers       |        |
| Bare `raise` in loops        | Timeframe loops must isolate failures (shard-level isolation)       |        |
| `routing_key=` in data sinks | Should use `bucket=get_bucket_name(domain, category)`               |        |
| Category mapping             | `crypto` → which GCS bucket? Must map correctly to CEFI/DEFI        |        |
| No `--dry-run` flag          | Is `info` operation sufficient? Or should compute have dry-run?     |        |
| Mock mode bypasses argparse  | `FeaturesMtfConfig().is_mock_mode()` checked BEFORE `parse_args()`  |        |

**Note on mock mode bypass:** The `_async_main()` function checks `is_mock_mode()` before parsing CLI args. This means
in mock mode, `--operation` and `--mode` flags are ignored entirely. This could mask CLI parsing bugs that only appear
in real mode. Log this as a finding if confirmed.

## AWS Testing

| #   | What                         | Expected                                       | Status |
| --- | ---------------------------- | ---------------------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws` startup | Accepted if AWS credentials configured         |        |
| A.2 | S3 write path                | MTF features written to S3 with correct prefix |        |
| A.3 | Provider mapping             | `s3` protocol maps to `aws` backend            |        |

Skip if AWS credentials are not configured locally.

## Frontend API Surface

This service feeds the following frontend components:

| Frontend component              | API endpoint / data path                  | What it renders                              |
| ------------------------------- | ----------------------------------------- | -------------------------------------------- |
| Multi-timeframe analysis charts | MTF feature parquet per instrument per TF | Feature values across 5m/15m/1h/4h/1d        |
| Feature comparison across TFs   | Side-by-side TF feature values            | How features differ at different resolutions |
| Signal confluence dashboard     | Alignment of signals across timeframes    | Higher-TF confirmation of lower-TF signals   |

Verify that output parquet schemas match what the frontend APIs expect. Check column names against API contract
definitions in UAC.

## Issues Found

(logged in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After features-service (multi-timeframe family) passes all phases → proceed to `010_ml_training_service.md`
