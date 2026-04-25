---
title: "E2E Test: features-commodity-service"
service: features-commodity-service
date: 2026-03-22
status: pending
---

# E2E Test: features-commodity-service

Follows `procedure.md`. Pipeline position: L3 features layer. Computes commodity-specific factor signals
(contango/backwardation, roll yield, seasonal patterns, inventory signals, weather-related factors, COT positioning, rig
count, price momentum).

## Upstream Dependencies

- **instruments-service** — `instruments_universe` (commodity instrument definitions)
- **market-data-processing-service** — `processed_candles_ohlcv` (price data for momentum, volatility factors)

## Downstream Consumers

- **ml-training-service** — `commodity_features` (batch feature sets for model training)
- **ml-inference-service** — `live_commodity_features` (real-time factor signals for live inference)

## Uniqueness

Domain-specific to commodity markets. Factors are fundamentals-driven, not purely price-derived: storage alpha, weather
delta, COT positioning, rig count, seasonal patterns. Uses `SignalComposer` to compose `FactorValue` objects into a
`CommoditySignal` with master signal, regime state, and staleness tracking. Factor groups are registry-based
(`FACTOR_REGISTRY`) with pluggable data sources (`DATA_SOURCE_REGISTRY`). Live mode is the CLI default (event-driven
signal computation); batch mode requires `--start-date`.

## Frontend

Feeds commodity-specific dashboards (factor heatmaps, seasonal pattern charts, contango/backwardation curves, inventory
signal panels).

## Operations

| Operation        | What it does                                  | Expected output                                        |
| ---------------- | --------------------------------------------- | ------------------------------------------------------ |
| `live` (default) | Event-driven signal computation per commodity | `CommoditySignal` published to event bus per commodity |
| `batch`          | Historical date-range factor computation      | Parquet/GCS output per commodity per date              |

## CLI Shape (from `cli/main.py`)

```
--commodity <CODE>     Commodity code (e.g. NG, CL). Default: all enabled.
--mode batch|live      Execution mode (default: live)
--dry-run              Validate config + factor setup, skip publish
--start-date YYYY-MM-DD  Required for --mode batch
--end-date YYYY-MM-DD    Defaults to --start-date
--run-tag <tag>        GCS prefix tag (default: batch; t1-recon for reconciliation)
--verbose / -v         DEBUG logging
```

**Note:** No `--operation` or `--asset-group` flags. The service is commodity-domain-only. Category is implicitly TRADFI
(energy, metals, agriculture) with possible CEFI overlap (gold-backed tokens). Mock mode is detected via
`config.is_mock_mode()` and redirects to `run_mock_pipeline()`.

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

### Phase 2: Dry-Run (batch + live, real data, no writes)

| #   | Mode  | Commodity        | Expected                                                                    | Status |
| --- | ----- | ---------------- | --------------------------------------------------------------------------- | ------ |
| 2.1 | batch | NG (natural gas) | Fetch from data sources, compute factors, skip publish. `--dry-run` logged. |        |
| 2.2 | batch | CL (crude oil)   | Same as 2.1 for crude oil                                                   |        |
| 2.3 | batch | (all enabled)    | All commodities processed, no publishes                                     |        |
| 2.4 | live  | NG               | Event-driven compute, `Dry run -- skipping publish` logged                  |        |
| 2.5 | live  | (all enabled)    | All enabled commodities, dry-run skip publish per commodity                 |        |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Mode  | Commodity | CSV check                                                     | GCS check                                   | Status |
| --- | ----- | --------- | ------------------------------------------------------------- | ------------------------------------------- | ------ |
| 3.1 | batch | NG        | Inspect CSV sample, verify factor schema (FactorValue fields) | Verify parquet in GCS                       |        |
| 3.2 | batch | CL        | Inspect CSV sample                                            | Verify parquet                              |        |
| 3.3 | batch | (all)     | All commodity CSVs present                                    | All commodity parquets in GCS               |        |
| 3.4 | live  | NG        | N/A (publishes to event bus)                                  | Verify event bus publish or GCS persistence |        |

### Phase 4: Category Sweep

**Note:** This service does not have a `--asset-group` flag. It is implicitly commodity-domain (TRADFI). The sweep tests
how the service behaves when upstream instruments from different categories are present.

| #   | Category context                                                                     | Expected behaviour                                                                                       | Status |
| --- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | ------ |
| 4.1 | TRADFI commodities (energy: NG, CL, HO; metals: GC, SI, HG; agriculture: ZC, ZW, ZS) | Primary path. All commodity factors computed.                                                            |        |
| 4.2 | CEFI (gold-backed tokens, e.g. PAXG)                                                 | If configured in `enabled_commodities`, processes. Otherwise skipped gracefully.                         |        |
| 4.3 | DEFI                                                                                 | Not applicable. No DEFI commodities expected. Service should not crash if upstream has DEFI instruments. |        |
| 4.4 | SPORTS                                                                               | Not applicable. Service ignores non-commodity instruments.                                               |        |
| 4.5 | PREDICTION                                                                           | Not applicable. Service ignores prediction instruments.                                                  |        |

### Phase 5: Live Mode

Live is the default mode. The service iterates over `enabled_commodities` from config, computes factor signals via
`SignalComposer`, and publishes via `SignalPublisher`.

| #   | What                                         | Expected                                                                                                                                                 | Status |
| --- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 5.1 | `--mode live` (default, no commodity filter) | All enabled commodities processed, signals published                                                                                                     |        |
| 5.2 | `--mode live --commodity NG`                 | Single commodity processed                                                                                                                               |        |
| 5.3 | Factor source failure (one source down)      | Shard-level isolation: other factors still computed. `ADAPTER_FETCH_FAILED` or error log for failed source. `_collect_factor_values` skips with warning. |        |
| 5.4 | All factors fail for one commodity           | `No factor values computed` error logged, `PROCESSING_COMPLETED` with `status=no_factors`, returns False but continues to next commodity                 |        |
| 5.5 | Graceful shutdown                            | Ctrl-C during commodity iteration, clean exit                                                                                                            |        |

#### Phase 5b: Mock/Real A/B Comparison

| #    | What                                                        | Mock behaviour                                                               | Real behaviour                                  | Status |
| ---- | ----------------------------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------- | ------ |
| 5b.1 | `CLOUD_MOCK_MODE=true --mode live`                          | Redirects to `run_mock_pipeline()` immediately                               | Normal factor computation pipeline              |        |
| 5b.2 | `CLOUD_MOCK_MODE=true --mode batch --start-date 2026-03-22` | Redirects to `run_mock_pipeline()` (mock check happens before mode dispatch) | BatchHandler processes date range               |        |
| 5b.3 | Signal schema parity                                        | Mock signals must have same schema as real (CommoditySignal fields)          | Validates FactorValue + CommoditySignal schemas |        |

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                       | What it tests                               | Expected                                                                                                     | Status |
| --- | ------------------------------ | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------ | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true` default | Mock pipeline activation                    | `MOCK MODE: redirecting to mock pipeline` logged, `run_mock_pipeline()` runs                                 |        |
| 6.2 | Mock with `--commodity NG`     | Single commodity mock                       | Mock pipeline runs (commodity filter may or may not apply in mock)                                           |        |
| 6.3 | Mock with `--dry-run`          | Mock + dry-run interaction                  | Mock check happens first (line 246-252 in main.py), dry-run may be ignored in mock path                      |        |
| 6.4 | Invalid commodity code         | `--commodity NOSYMBOL`                      | Factor sources return empty, `No factor values computed` logged, returns 1                                   |        |
| 6.5 | Empty factor registry          | All factor groups unregistered              | Warning per group, no factors, returns 1                                                                     |        |
| 6.6 | Data source fetch failure      | Source raises exception                     | `Data source fetch failed` error logged, empty data used, factor computation may still succeed with defaults |        |
| 6.7 | config_source check            | `CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local` | `config_source=local`, no GCS reads, mock pipeline used                                                      |        |

### Phase 7: Observability

| #   | Check                        | Expected                                                                                                | Status |
| --- | ---------------------------- | ------------------------------------------------------------------------------------------------------- | ------ |
| 7.1 | UEI events                   | `STARTED`, `PROCESSING_STARTED` per commodity, `PROCESSING_COMPLETED` per commodity, `STOPPED`          |        |
| 7.2 | PROCESSING_COMPLETED details | `commodity`, `master_signal`, `regime`, `factor_count`, `stale_factor_count`, `dry_run` fields          |        |
| 7.3 | FAILED event on error        | `FAILED` with `commodity` and `error` details                                                           |        |
| 7.4 | Shard-level isolation        | One commodity failure does not crash others (try/except in commodity loop, lines 284-296)               |        |
| 7.5 | Staleness tracking           | `stale_factor_ids` populated when factor data is outdated                                               |        |
| 7.6 | Regime state                 | `RegimeState.UNKNOWN` with `regime_confidence=0.0` (historical return series not available in CLI pass) |        |
| 7.7 | Dry-run warning              | `Dry run -- skipping publish` logged per commodity                                                      |        |

## Known Issues Audit

| #   | What to check                                            | Why                                                                                                                                                          | Status |
| --- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------ |
| K.1 | `load_dotenv(override=False)`                            | Line 24: confirmed `override=False` -- shell env vars win. PASS.                                                                                             |        |
| K.2 | No `--operation` flag                                    | CLI does not follow standardised `--operation/--mode/--asset-group` axes from `cli-convention.md`. Uses `--commodity` instead. Potential compliance issue.   |        |
| K.3 | `os.environ.get("LOG_LEVEL")` in `_validate_log_level()` | Line 217: uses `os.environ.get()` directly, not `UnifiedCloudConfig`. Tagged `# config-bootstrap: pre-UCC init` -- this is the approved bootstrap exception. |        |
| K.4 | No `--asset-group` flag                                  | Service is commodity-only, no MarketCategory routing. If CEFI gold-backed tokens need processing, how are they routed?                                       |        |
| K.5 | Mock mode short-circuits before `setup_events`           | Lines 246-252: mock mode returns before `setup_events()` is called (line 254). No UEI events in mock mode.                                                   |        |
| K.6 | Broad exception catch in commodity loop                  | Lines 294-296: catches `(ValueError, OSError, RuntimeError, KeyError)` -- adequate but may miss other exception types.                                       |        |
| K.7 | `SignalPublisher` topic resolution                       | Verify `config.signal_topic_template` resolves correctly in dev/staging environments.                                                                        |        |

## AWS Testing

| #   | What                                 | Expected                                                         | Status |
| --- | ------------------------------------ | ---------------------------------------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws ENVIRONMENT=dev` | ServiceRuntime accepts `aws`. S3 sink used instead of GCS.       |        |
| A.2 | Batch mode with S3                   | BatchHandler writes to S3 bucket (if AWS credentials configured) |        |

## Frontend API Surface

| Endpoint / Event                 | Consumer                                  | Payload                                                                    |
| -------------------------------- | ----------------------------------------- | -------------------------------------------------------------------------- |
| `CommoditySignal` event (PubSub) | ml-training-service, ml-inference-service | `commodity`, `master_signal`, `regime`, `factor_count`, `stale_factor_ids` |
| GCS parquet (batch)              | commodity dashboards, analytics UIs       | Per-commodity factor values with timestamps                                |
| Factor heatmap data              | commodity dashboard UI                    | Factor group scores per commodity per date                                 |
| Seasonal pattern data            | seasonal chart UI                         | Historical seasonal patterns per commodity                                 |

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue      | Severity | Fixed? |
| ---------- | -------- | ------ |
| (none yet) |          |        |

## Next Service

After features-commodity-service passes all phases, proceed to `011_features_sports_service.md`
