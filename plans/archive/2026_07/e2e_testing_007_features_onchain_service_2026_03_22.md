> **SUPERSEDED (archived 2026-07-27).** Blank, never-executed test-matrix template. Superseded by the
> `/data-pipeline-check-features` skill + `plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md` (real
> per-handler GCS coverage checks for the features-onchain leg).

---

title: "E2E Test: features-service (onchain family)" service: features-service (onchain family) date: 2026-03-22 status:
pending
---

# E2E Test: features-service (onchain family)

Follows `procedure.md`. Pipeline position: #7 (L3 features layer).

**Upstream:** market-tick-data-service (DeFi tick data), instruments-service (DeFi instruments).

**Downstream:** ml-training-service (onchain_features).

**Key uniqueness:** DeFi-only feature service. Computes on-chain metrics: lending rates, LST yields, Aave utilization,
flash loan availability, protocol rewards, macro sentiment. Uses Web3/RPC for some calculations. Category should be DEFI
exclusively — CEFI is accepted by the parser but should produce DeFi-relevant output only. TRADFI/SPORTS/PREDICTION are
not accepted.

**Frontend:** Feeds DeFi analytics dashboard, on-chain metrics in Observe > Strategy Health.

## Operations

| Operation | What it does                                                 | Expected output                           |
| --------- | ------------------------------------------------------------ | ----------------------------------------- |
| `compute` | Calculate on-chain features for a date range + feature group | Parquet per feature group per date in GCS |

## CLI Structure

Uses `ServiceCLI` from unified-trading-library with custom `_extra_args`:

- `--operation compute` (only operation, required)
- `--mode batch|live` (required; `incremental` accepted as deprecated alias for `live`)
- `--asset-group CEFI|DEFI` (required, single-value)
- `--feature-group` (required): `macro_sentiment`, `lending_rates`, `lst_yields`, `aave_lending_rates`,
  `aave_utilization`, `aave_risk_params`, `lst_staking_yields`, `protocol_rewards`, `flash_loan_availability`, `ALL`
- `--start-date`, `--end-date` (required, YYYY-MM-DD)
- `--max-workers` (default 4)
- `--max-results` (optional, limits output files per shard)
- `--skip-dependency-check` (skip upstream validation)
- `--no-fail-on-missing-deps` (continue despite missing upstream data)
- `--run-tag` (GCS prefix: `batch` or `t1-recon`)
- `--dry-run`, `--force`, `--log-level`

Note: `onchain_perps` feature group is DEPRECATED — Hyperliquid/Aster now use CEFI bucket via features-service
(delta-one family).

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

| #    | Feature group           | Category | Expected                                         | Status |
| ---- | ----------------------- | -------- | ------------------------------------------------ | ------ |
| 2.1  | macro_sentiment         | DEFI     | Fetch macro data, no GCS writes                  |        |
| 2.2  | lending_rates           | DEFI     | Fetch lending rates, no GCS writes               |        |
| 2.3  | aave_lending_rates      | DEFI     | Fetch Aave rates, no GCS writes                  |        |
| 2.4  | aave_utilization        | DEFI     | Fetch Aave utilization, no GCS writes            |        |
| 2.5  | aave_risk_params        | DEFI     | Fetch Aave risk parameters, no GCS writes        |        |
| 2.6  | lst_yields              | DEFI     | Fetch LST yield data, no GCS writes              |        |
| 2.7  | lst_staking_yields      | DEFI     | Fetch staking yields, no GCS writes              |        |
| 2.8  | protocol_rewards        | DEFI     | Fetch protocol reward data, no GCS writes        |        |
| 2.9  | flash_loan_availability | DEFI     | Fetch flash loan availability, no GCS writes     |        |
| 2.10 | ALL                     | DEFI     | All feature groups processed, no GCS writes      |        |
| 2.11 | macro_sentiment         | CEFI     | Accepted by parser — verify behavior is sensible |        |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Feature group       | Category | GCS check                         | Status |
| --- | ------------------- | -------- | --------------------------------- | ------ |
| 3.1 | macro_sentiment     | DEFI     | Verify parquet in GCS             |        |
| 3.2 | lending_rates       | DEFI     | Verify parquet in GCS             |        |
| 3.3 | ALL                 | DEFI     | Verify all feature groups written |        |
| 3.4 | ALL with --force    | DEFI     | Overwrites existing data          |        |
| 3.5 | ALL --max-results 2 | DEFI     | Only 2 output files per shard     |        |

### Phase 4: Category Sweep (MANDATORY)

The parser accepts `CEFI` and `DEFI` only. TRADFI/SPORTS/PREDICTION are rejected at the argparse level. We must verify
both accepted categories AND confirm graceful rejection of unsupported ones.

| #   | Category   | Expected                                                        | Status |
| --- | ---------- | --------------------------------------------------------------- | ------ |
| 4.1 | DEFI       | Primary path — all feature groups produce meaningful output     |        |
| 4.2 | CEFI       | Accepted — verify what features are produced (macro_sentiment?) |        |
| 4.3 | TRADFI     | Rejected by argparse: "invalid choice: 'TRADFI'"                |        |
| 4.4 | SPORTS     | Rejected by argparse: "invalid choice: 'SPORTS'"                |        |
| 4.5 | PREDICTION | Rejected by argparse: "invalid choice: 'PREDICTION'"            |        |

**GCS verification after DEFI writes:**

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('<onchain-features-bucket>')
blobs = list(bucket.list_blobs(prefix='onchain_features/', max_results=20))
print(f'Files written: {len(blobs)}')
for b in blobs[:5]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 5: Live Mode (if applicable)

The parser accepts `live` mode (and `incremental` as deprecated alias). Verify live mode behavior.

| #   | What                                                                                                                   | Expected                                        | Status |
| --- | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------ |
| 5.1 | `--operation compute --mode live --asset-group DEFI --feature-group ALL --start-date 2026-03-22 --end-date 2026-03-22` | Live handler invoked                            |        |
| 5.2 | `--mode incremental`                                                                                                   | Deprecated alias accepted, normalized to `live` |        |
| 5.3 | Event logging                                                                                                          | UEI events: STARTED, per-group COMPLETED/FAILED |        |
| 5.4 | Graceful shutdown                                                                                                      | Ctrl-C -> cleanup callback runs                 |        |

#### Phase 5b: Mock/Real A/B

| #    | Check             | Expected                                          | Status |
| ---- | ----------------- | ------------------------------------------------- | ------ |
| 5b.1 | Mock batch output | `CLOUD_MOCK_MODE=true` produces mock features     |        |
| 5b.2 | Real batch output | `CLOUD_MOCK_MODE=false` fetches from real sources |        |
| 5b.3 | Schema parity     | Mock and real output schemas are identical        |        |

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                    | What it tests                                   | Expected                                               | Status |
| --- | --------------------------- | ----------------------------------------------- | ------------------------------------------------------ | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true`      | Mock data generation                            | Mock features generated, no real RPC calls             |        |
| 6.2 | `CLOUD_PROVIDER=local`      | No cloud credentials required                   | Completes without ADC                                  |        |
| 6.3 | Missing upstream tick data  | market-tick-data-service produced nothing       | Graceful empty or error, no crash                      |        |
| 6.4 | `--skip-dependency-check`   | Skips upstream validation                       | Proceeds even without upstream data                    |        |
| 6.5 | `--no-fail-on-missing-deps` | Continues despite missing deps                  | Processes what it can, logs warnings                   |        |
| 6.6 | Invalid date range          | `--start-date 2026-03-22 --end-date 2026-03-01` | Validation error: "Start date must be before end date" |        |
| 6.7 | Future end date             | `--end-date 2027-01-01`                         | Validation error: "End date cannot be in the future"   |        |
| 6.8 | config_source check         | `CLOUD_MOCK_MODE=true`                          | `config_source=local`, no GCS reads                    |        |

### Phase 7: Observability

| #   | Check                   | Expected                                                    | Status |
| --- | ----------------------- | ----------------------------------------------------------- | ------ |
| 7.1 | ServiceRuntime log line | All dimensions logged (operation, mode, category)           |        |
| 7.2 | UEI lifecycle events    | STARTED, per-feature-group events, COMPLETED/FAILED         |        |
| 7.3 | Shard-level isolation   | One feature group failure doesn't crash others              |        |
| 7.4 | Dry-run warning         | "DRY RUN" or dry-run confirmation in logs                   |        |
| 7.5 | Error classification    | ADAPTER_FETCH_FAILED events for failed data sources         |        |
| 7.6 | Memory watchdog         | "Memory watchdog started" logged                            |        |
| 7.7 | Graceful shutdown       | GracefulShutdownHandler registered + cleanup callback       |        |
| 7.8 | Correlation ID          | correlation_id present in error events                      |        |
| 7.9 | Tracing                 | `setup_tracing("features-service (onchain family)")` called |        |

## Known Issues Audit

Check for these patterns found in earlier services:

| Pattern                       | What to check                                                      | Status |
| ----------------------------- | ------------------------------------------------------------------ | ------ |
| `load_dotenv(override=True)`  | Confirmed `override=False` in `cli/main.py` line 30                |        |
| `--dry-run` enforcement       | Verify dry-run prevents GCS writes (dumps to local instead)        |        |
| Bucket resolution             | Uses `build_bucket()` / `build_path()` not hardcoded env vars      |        |
| asyncio nesting               | ComputeHandler is `BaseModeHandler` (async `run()`); check nesting |        |
| `os.getenv()` usage           | Must use `UnifiedCloudConfig` except config-bootstrap exceptions   |        |
| Deprecated `incremental` mode | Normalized to `live` in `validate_args()` and `normalize_args()`   |        |
| Web3 RPC calls in unit tests  | Must be mocked — never hit real RPCs in tests                      |        |

## AWS Testing

| #   | What                                       | Expected                          | Status |
| --- | ------------------------------------------ | --------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=true`  | Service starts with mock mode     |        |
| A.2 | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=false` | Requires AWS credentials, S3 sink |        |

## Frontend API Surface

On-chain features feed these UI components:

| UI Component                   | Data source                              | API endpoint (if applicable)        |
| ------------------------------ | ---------------------------------------- | ----------------------------------- |
| DeFi analytics dashboard       | onchain_features (all groups)            | `/api/features/onchain`             |
| Observe > Strategy Health      | onchain_features/macro_sentiment         | `/api/features/onchain/macro`       |
| Lending rates panel            | onchain_features/lending_rates           | `/api/features/onchain/lending`     |
| Flash loan availability widget | onchain_features/flash_loan_availability | `/api/features/onchain/flash-loans` |

Verify that the output schema from this service matches what the API layer expects.

## Issues Found

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |
|       |          |        |

## Next Service

After features-service (onchain family) passes all phases -> proceed to `008_ml_training_service.md`
