---
title: "E2E Test: features-service (sports family)"
service: features-service (sports family)
date: 2026-03-22
status: pending
---

# E2E Test: features-service (sports family)

Follows `procedure.md`. Pipeline position: L3 features layer. Computes sports-domain features: form indicators,
head-to-head stats, league position, injury impact, home/away factors, odds movement features, pre-match and in-play
features.

## Upstream Dependencies

- **instruments-service** — `sports_reference_data` (fixture definitions, league/team metadata via instruments-service
  reference_data)
- **market-data-processing-service** — `sports_odds` (odds data from sportsbooks)

## Downstream Consumers

- **ml-training-service** — `sports_features` (batch feature sets for model training)
- **ml-inference-service** — `live_sports_features` (real-time features for live inference)

## Uniqueness

Sports-domain-specific. Uses instruments-service reference_data sub-package for reference data. Event-driven: matches
have discrete start/end times, not continuous like financial markets. Features change at match events (goals, cards,
substitutions, half-time), not on a continuous tick basis. Batch mode fetches from multiple providers (api_football,
footystats, understat, odds_api). Live mode consumes a PubSub subscription (`sports-odds-ready`) and publishes features
to a topic per feature group. Supports `--skip-fetch` to recompute features from already-fetched data.

## Frontend

Feeds sports analytics dashboards, match prediction panels, betting insight UIs, odds movement charts.

## Operations

| Operation | What it does                                                                                                         | Expected output                             |
| --------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| `batch`   | Fetch from providers + compute features for a given date                                                             | Parquet/GCS per provider per table per date |
| `live`    | Subscribe to `sports-odds-ready`, compute features on each event, publish to `features-sports-{feature_group}` topic | Real-time feature events on PubSub          |

## CLI Shape (from `cli/parser.py`)

```
--mode batch|live         Processing mode (REQUIRED)
--date YYYY-MM-DD         Processing date (required for batch)
--providers <csv>         Comma-separated providers (default: api_football,footystats,understat,odds_api)
--tables <csv>            Comma-separated table names (default: all)
--bucket <name>           GCS bucket (default: features-sports-{project_id})
--secret-name <name>      Secret Manager secret name override
--skip-fetch              Skip fetch, only run write step (batch only)
--subscription-id <id>    PubSub subscription (live only, default: sports-odds-ready)
--topic-id <id>           PubSub topic to publish (live only)
--feature-group <name>    Feature group for output (live only, default: odds)
--enable-persistence      Enable background GCS persistence (live only)
--log-level DEBUG|INFO|WARNING|ERROR
--run-tag <tag>           GCS prefix tag (default: batch; t1-recon for reconciliation)
```

**Note:** No `--operation` or `--asset-group` flags. The service is SPORTS-only by design. Mode is required (no
default). Date validation rejects future dates in batch mode. No `--dry-run` flag in parser (potential gap vs
procedure).

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

**Note:** The CLI parser does not define a `--dry-run` flag. This is a potential compliance gap with the procedure. Test
how the service behaves without it.

| #   | Mode                   | Provider subset | Expected                                                                     | Status |
| --- | ---------------------- | --------------- | ---------------------------------------------------------------------------- | ------ |
| 2.1 | batch                  | api_football    | Fetch from API Football, compute features. If no `--dry-run`, writes happen. |        |
| 2.2 | batch                  | footystats      | Fetch from FootyStats                                                        |        |
| 2.3 | batch                  | odds_api        | Fetch from The Odds API                                                      |        |
| 2.4 | batch                  | (all default)   | All 4 providers fetched                                                      |        |
| 2.5 | batch + `--skip-fetch` | (all)           | Skip fetch, only write from cached data. Tests fetch/write separation.       |        |

### Phase 3: Real Writes (dev, CSV sampling on)

| #   | Mode  | Providers     | CSV check                                         | GCS check                                               | Status |
| --- | ----- | ------------- | ------------------------------------------------- | ------------------------------------------------------- | ------ |
| 3.1 | batch | api_football  | Inspect CSV sample, verify feature schema         | Verify parquet in `features-sports-{project_id}` bucket |        |
| 3.2 | batch | footystats    | Inspect CSV sample                                | Verify parquet                                          |        |
| 3.3 | batch | understat     | Inspect CSV sample                                | Verify parquet                                          |        |
| 3.4 | batch | odds_api      | Inspect CSV sample, verify odds movement features | Verify parquet                                          |        |
| 3.5 | batch | (all default) | All provider CSVs present                         | All parquets written                                    |        |

### Phase 4: Category Sweep

**Note:** This service is SPORTS-only. No `--asset-group` flag exists. The sweep tests how the service responds to
non-sports contexts and validates that SPORTS data flows correctly.

| #   | Category context | Expected behaviour                                                                                                                          | Status |
| --- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| 4.1 | SPORTS (primary) | Full pipeline: fetch from 4 providers, compute features (form, H2H, league position, injury, home/away, odds movement). GCS write verified. |        |
| 4.2 | CEFI             | Not applicable. Service only processes sports data. Should not crash if CEFI instruments exist upstream.                                    |        |
| 4.3 | TRADFI           | Not applicable. Service ignores non-sports data.                                                                                            |        |
| 4.4 | DEFI             | Not applicable. Service ignores non-sports data.                                                                                            |        |
| 4.5 | PREDICTION       | Not applicable. Prediction markets (e.g. Polymarket) are separate from sports features. Service should not process them.                    |        |

### Phase 5: Live Mode

Live mode subscribes to a PubSub subscription and publishes computed features.

| #   | What                                              | Expected                                                            | Status |
| --- | ------------------------------------------------- | ------------------------------------------------------------------- | ------ |
| 5.1 | `--mode live --subscription-id sports-odds-ready` | Subscribes to PubSub, waits for messages                            |        |
| 5.2 | `--mode live --feature-group odds`                | Publishes to `features-sports-odds` topic                           |        |
| 5.3 | `--mode live --enable-persistence`                | Background GCS persistence active alongside PubSub publish          |        |
| 5.4 | Message processing                                | On receiving odds update: compute features, publish to output topic |        |
| 5.5 | Match event handling                              | Features recomputed at discrete match events (goals, cards, HT)     |        |
| 5.6 | Graceful shutdown                                 | Ctrl-C during subscription, clean exit, no partial writes           |        |
| 5.7 | PubSub connection failure                         | Circuit breaker / retry on subscription unavailable                 |        |

#### Phase 5b: Mock/Real A/B Comparison

| #    | What                                                  | Mock behaviour                                         | Real behaviour                                                  | Status |
| ---- | ----------------------------------------------------- | ------------------------------------------------------ | --------------------------------------------------------------- | ------ |
| 5b.1 | `CLOUD_MOCK_MODE=true --mode batch --date 2026-03-22` | Mock data generators produce synthetic sports features | Real provider APIs called, real feature computation             |        |
| 5b.2 | `CLOUD_MOCK_MODE=true --mode live`                    | Mock PubSub messages, synthetic feature output         | Real PubSub subscription, real odds data                        |        |
| 5b.3 | Feature schema parity                                 | Mock features must have same schema as real features   | Validates feature DataFrame columns match                       |        |
| 5b.4 | Provider count parity                                 | Mock should simulate same 4 providers                  | Real fetches from api_football, footystats, understat, odds_api |        |

### Phase 6: Mock Mode (scenario testing)

| #   | Scenario                                                            | What it tests                               | Expected                                                                 | Status |
| --- | ------------------------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------ | ------ |
| 6.1 | `CLOUD_MOCK_MODE=true --mode batch --date 2026-03-22`               | Basic mock batch                            | Mock data generated, local sink, no API calls                            |        |
| 6.2 | `CLOUD_MOCK_MODE=true` + single provider `--providers api_football` | Provider filtering in mock                  | Only API Football mock data generated                                    |        |
| 6.3 | `--mode batch --date 2027-01-01`                                    | Future date rejection                       | `ValueError: Date cannot be in the future` from `validate_args()`        |        |
| 6.4 | `--mode batch` (no `--date`)                                        | Missing required date                       | `ValueError: --date is required for --mode batch` from `validate_args()` |        |
| 6.5 | `--tables specific_table`                                           | Table filtering                             | Only specified tables fetched/written                                    |        |
| 6.6 | Provider API failure (one provider down)                            | Shard-level isolation                       | Other providers still processed, failed provider logged                  |        |
| 6.7 | config_source check                                                 | `CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local` | `config_source=local`, no GCS reads, no real API calls                   |        |
| 6.8 | Empty match day                                                     | Date with no fixtures                       | Service completes with empty output, no crash                            |        |

### Phase 7: Observability

| #   | Check                    | Expected                                                             | Status |
| --- | ------------------------ | -------------------------------------------------------------------- | ------ |
| 7.1 | UEI events               | STARTED, per-provider PROCESSING events, COMPLETED/FAILED            |        |
| 7.2 | Provider-level isolation | One provider failure (e.g. API Football down) does not crash others  |        |
| 7.3 | Error classification     | Failed provider fetches emit `ADAPTER_FETCH_FAILED` or equivalent    |        |
| 7.4 | Live mode PubSub metrics | Messages received/processed/published counts                         |        |
| 7.5 | Feature group tracking   | Which feature groups computed (form, H2H, odds, etc.) logged per run |        |
| 7.6 | Secret Manager access    | `--secret-name` override works, default SM resolution works          |        |
| 7.7 | GCS persistence in live  | `--enable-persistence` writes to GCS in background alongside PubSub  |        |

## Known Issues Audit

| #   | What to check                        | Why                                                                                                                                         | Status |
| --- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| K.1 | No `--dry-run` flag                  | Parser does not define `--dry-run`. Every other service in the procedure uses it. Compliance gap.                                           |        |
| K.2 | No `--operation` flag                | CLI uses `--mode` only, not the standardised `--operation/--mode/--asset-group` axes from `cli-convention.md`.                              |        |
| K.3 | No `--asset-group` flag              | Service is SPORTS-only. Acceptable if documented, but breaks the universal category sweep pattern.                                          |        |
| K.4 | `--mode` is required (no default)    | Unlike features-service (commodity family) which defaults to `live`, this service requires explicit `--mode`. Inconsistency across feature services. |        |
| K.5 | Future date validation only in batch | `validate_args()` rejects future dates for batch. Live mode has no date validation (correct -- live is real-time).                          |        |
| K.6 | `load_dotenv` location               | Need to verify `load_dotenv(override=False)` is used (not visible in parser.py, check main.py).                                             |        |
| K.7 | reference_data dependency            | Service depends on instruments-service reference_data sub-package for reference data. Verify it is installed in service `.venv`.            |        |
| K.8 | PubSub subscription default          | `sports-odds-ready` subscription must exist in the project. Verify with `gcloud pubsub subscriptions list`.                                 |        |
| K.9 | `--bucket` empty string default      | Default is empty string, resolved to `features-sports-{project_id}` at runtime. Verify resolution logic.                                    |        |

## AWS Testing

| #   | What                                 | Expected                                                   | Status |
| --- | ------------------------------------ | ---------------------------------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws ENVIRONMENT=dev` | ServiceRuntime accepts `aws`. S3 sink used instead of GCS. |        |
| A.2 | Batch mode with S3                   | Features written to S3 bucket                              |        |
| A.3 | Live mode PubSub equivalent          | SNS/SQS or equivalent messaging on AWS (if implemented)    |        |

## Frontend API Surface

| Endpoint / Event                                      | Consumer                                 | Payload                                        |
| ----------------------------------------------------- | ---------------------------------------- | ---------------------------------------------- |
| GCS parquet (batch)                                   | sports analytics UI, match prediction UI | Per-provider per-table feature DataFrames      |
| `features-sports-{feature_group}` PubSub topic (live) | ml-inference-service, betting insight UI | Real-time feature events per match             |
| Form indicators                                       | match prediction panels                  | Team form over last N matches                  |
| H2H stats                                             | match analysis UI                        | Historical head-to-head records                |
| Odds movement features                                | odds movement charts, betting insight UI | Pre-match and in-play odds trajectories        |
| League position data                                  | league table UI                          | Current standings, points, GD                  |
| Injury impact scores                                  | team news panels                         | Weighted injury impact on expected performance |

## Issues Found

(logged in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue      | Severity | Fixed? |
| ---------- | -------- | ------ |
| (none yet) |          |        |

## Next Service

After features-service (sports family) passes all phases, proceed to `012_features_calendar_service.md`
