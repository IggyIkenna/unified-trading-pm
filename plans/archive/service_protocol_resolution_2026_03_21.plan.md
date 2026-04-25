---

name: service-protocol-resolution-2026-03-21 overview: > Standardise the entire service control surface: CLI axes, env
vars, config resolution, protocol selection, testnet switching, and error handling. Every service gets the same control
interface. Libraries derive everything from a minimal set of inputs. Schemas enforce valid values. Startup validation
catches misconfig before anything runs. CLI capabilities registered in PM manifest so there's zero ambiguity about what
any service accepts. type: code epic: epic-code-completion status: active priority: P0 owner: human locked_by:
live-defi-rollout locked_since: 2026-03-21 tags: [infrastructure, protocol, topology, cli, config, all-services,
control-surface]

completion_gates: code: C5 deployment: none business: none

context: |

## The Control Surface

Every service in the system is driven by exactly three input channels:

| Channel      | Type                 | What it controls                                    | Examples                                                     |
| ------------ | -------------------- | --------------------------------------------------- | ------------------------------------------------------------ |
| **CLI**      | Cold, sharding       | Domain work, time range, venue/instrument selection | --operation, --mode, --asset-group, --scenario               |
| **Env vars** | Cold, infrastructure | Cloud target, project, environment, data mode       | CLOUD_PROVIDER, GCP_PROJECT_ID, ENVIRONMENT, CLOUD_MOCK_MODE |
| **Config**   | Hot, reloadable      | Domain params, tuning, feature flags                | GCS/local YAML files via config reloader                     |

Everything else is **derived**. No PROTOCOL\_\* env vars. No duplicated config. Libraries resolve what they need from
these three channels via UTL.

## The Dimensions

| Dimension          | Schema Location                      | Valid Values                                     | Who sets it            |
| ------------------ | ------------------------------------ | ------------------------------------------------ | ---------------------- |
| **Environment**    | UIC `EnvironmentMode`                | `dev`, `staging`, `prod`                         | Env: `ENVIRONMENT`     |
| **Cloud provider** | UIC `CloudProvider`                  | `gcp`, `aws`                                     | Env: `CLOUD_PROVIDER`  |
| **Runtime mode**   | UIC `RuntimeMode`                    | `batch`, `live`                                  | CLI: `--mode`          |
| **Data mode**      | UIC `DataMode`                       | `real`, `mock`                                   | Env: `CLOUD_MOCK_MODE` |
| **Category**       | UIC `MarketCategory`                 | `CEFI`, `TRADFI`, `DEFI`, `SPORTS`, `PREDICTION` | CLI: `--asset-group`   |
| **Testnet mode**   | UAC per-venue                        | `mainnet`, `testnet` (venue-specific endpoints)  | Env: `TESTNET_MODE`    |
| **Operation**      | Per-service (registered in manifest) | Service-specific                                 | CLI: `--operation`     |
| **Scenario**       | UIC `MockScenario`                   | `default`, `stress`, `empty`, custom             | CLI: `--scenario`      |
| **Log level**      | UIC `LogLevel` (existing)            | `DEBUG`, `INFO`, `WARNING`, `ERROR`              | CLI: `--log-level`     |

Every value above is a schema in UIC or UAC. Wrong value → startup validation error with clear message.

## Config Source Resolution

| CLOUD_MOCK_MODE | Config source     | Domain data source                           |
| --------------- | ----------------- | -------------------------------------------- |
| `true`          | Local YAML files  | Mock/sample data (local or GCS test buckets) |
| `false`         | GCS config bucket | Real cloud storage (GCS/S3)                  |

Config is always small enough for local. Domain data is never local (too big) — even in mock mode it reads from GCS test
buckets with sample data, or uses CSV sampling (optional, default on in dev).

## Testnet Resolution

Testnet is NOT limited to DeFi. It applies to any venue with a testnet:

- DeFi: Sepolia, Tenderly fork
- CeFi: OKX testnet, Binance testnet
- TradFi: IBKR paper trading
- Prediction: Polymarket testnet

UAC capability_declarations already have `supports_testnet` and `environments` (testnet URLs, mainnet URLs) per venue.
When `TESTNET_MODE=true`, interfaces resolve to testnet endpoints + testnet API keys from SM. The mapping from
`TESTNET_MODE` → actual endpoint is owned by UAC (per venue). Services don't know or care about specific testnet URLs.

## The Flow

```
Service CLI (--operation compute --mode batch --asset-group DEFI --scenario default)
  + Env (CLOUD_PROVIDER=gcp GCP_PROJECT_ID=xxx ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=true)
    → Service validates all inputs against UIC/UAC schemas (fail loud on invalid)
    → Service passes to UTL ServiceRuntime(mode, provider, environment, data_mode, testnet)
      → UTL reads runtime-topology.yaml: batch + gcp → storage=gcs, messaging=gcs
      → UTL configures UCI: get_data_sink(provider="gcs", bucket=derived)
      → UTL configures UEI: setup_events(mode="batch")
      → UTL configures config reloader: source=gcs (or local if mock)
      → Interfaces get testnet=true → UAC resolves testnet endpoints per venue
        → Everything just works
```

## Manifest Registry

PM workspace-manifest.json gains a `cli_capabilities` section per service:

```json
"instruments-service": {
  "cli_capabilities": {
    "operations": ["instruments", "aggregate", "corporate_actions"],
    "categories": ["CEFI", "TRADFI", "DEFI", "SPORTS"],
    "supports_live": true,
    "extra_args": ["--venues", "--tickers", "--force", "--output-format"]
  }
}
```

This becomes the registry of what each service accepts. Quality gates can validate CLI parsers match the manifest.

## Error Handling

Invalid control surface input → standardised error from UTL:

```
STARTUP_VALIDATION_FAILED: Invalid CLOUD_PROVIDER='azure'. Valid: gcp, aws.
STARTUP_VALIDATION_FAILED: Invalid --mode='stream'. Valid: batch, live.
STARTUP_VALIDATION_FAILED: TESTNET_MODE=true but venue BINANCE has no testnet endpoints in UAC.
STARTUP_VALIDATION_FAILED: --asset-group PREDICTION not supported by instruments-service. Valid: CEFI, TRADFI, DEFI, SPORTS.
```

One error code, one library (UTL), clear message. Every service gets this for free via ServiceCLI.

## Dependency DAG

```
Phase 1: Schemas (UIC + UAC)
  ↓
Phase 2: UTL ServiceRuntime + topology reader + startup validation
  ↓
Phase 3: UCI factory bridge (auto-derive protocol from provider+mode)
  ↓
Phase 4: ServiceCLI integrates ServiceRuntime
  ↓
Phase 5: All services adopt (PARALLEL)
  ↓
Phase 6: PM manifest cli_capabilities registry
  ↓
Phase 7: Cleanup + validation
```

todos:

# Phase 1 — Schemas (UIC + UAC)

- id: p1-uic-control-surface-schemas content: |
  - [x] [AGENT] P0. Add/verify control surface schemas in UIC: EnvironmentMode (dev/staging/prod), CloudProvider
        (gcp/aws), RuntimeMode (batch/live — already exists, verify), DataMode (real/mock), MarketCategory
        (CEFI/TRADFI/DEFI/SPORTS/PREDICTION), MockScenario (default/stress/empty), TestnetMode (mainnet/testnet). Each
        is a StrEnum. LogLevel already exists — verify. No duplicates — check nothing redefines these elsewhere. status:
        done
- id: p1-uac-testnet-registry content: |
  - [x] [AGENT] P0. Verify UAC capability_declarations have testnet endpoints for all venues that support testnet.
        Check: Binance, OKX, Deribit, Bybit, IBKR (paper), Polymarket, Aave (Sepolia), Uniswap (Sepolia), Hyperliquid
        (testnet). For each: base_url (mainnet), testnet_url, testnet_api_key_secret_name. This is the SSOT for
        TESTNET_MODE resolution. status: done
- id: p1-uic-startup-error-codes content: |
  - [ ] [AGENT] P1. Add STARTUP_VALIDATION_FAILED error code to UIC error taxonomy. Standardised format:
        "STARTUP_VALIDATION_FAILED: {message}". UTL raises this on invalid CLI/env/config inputs. status: done

# Phase 2 — UTL ServiceRuntime + Topology Reader

- id: p2-utl-topology-reader content: |
  - [ ] [AGENT] P0. Build topology_reader.py in UTL. Reads runtime-topology.yaml from PM (or bundled copy). Functions:
        get_storage_protocol(cloud_provider, mode) → gcs|s3|local, get_messaging_protocol(cloud_provider, mode) →
        pubsub|sqs|local|in_memory, get_analytics_protocol(cloud_provider) → bigquery|athena|local. status: done
- id: p2-utl-service-runtime content: |
  - [ ] [AGENT] P0. Build ServiceRuntime class in UTL. Constructed from CLI args + env vars. Validates all inputs
        against UIC schemas (fail loud). Exposes: mode, provider, environment, data_mode, testnet, category, operation.
        Resolves derived values via topology reader. Single object passed to all library constructors. status: done
- id: p2-utl-startup-validation content: |
  - [ ] [AGENT] P0. Build startup_validation.py in UTL. Called by ServiceCLI before handler dispatch. Validates: all env
        vars are valid schema values, CLI args match manifest capabilities, required env vars are set (not placeholder
        defaults). Raises STARTUP_VALIDATION_FAILED with clear message. status: done
- id: p2-utl-config-source-resolution content: |
  - [ ] [AGENT] P1. Config source resolution in UTL. When CLOUD_MOCK_MODE=true → config reloader reads local YAML files.
        When false → reads from GCS config bucket. Service passes mode to UTL, UTL tells config interface where to look.
        status: done

# Phase 3 — UCI Factory Bridge

- id: p3-uci-gcs-datasink content: |
  - [ ] [AGENT] P0. Add GCSDataSink to UCI. Writes parquet to GCS bucket. Bucket resolved from routing_key + project_id
        convention. Handles Hive partitioning (day=, venue=). status: todo
- id: p3-uci-s3-datasink content: |
  - [ ] [AGENT] P1. Add S3DataSink to UCI. Same pattern for AWS. status: todo
- id: p3-uci-auto-derive-protocol content: |
  - [ ] [AGENT] P0. UCI get_data_sink() auto-derives provider from UTL ServiceRuntime when no explicit provider given.
        Remove PROTOCOL_DATA_SINK_BACKEND env var dependency. Same for get_event_bus(), get_data_source(). status: done
- id: p3-uci-unify-runtime-mode content: |
  - [ ] [AGENT] P0. Unify SERVICE_MODE → RUNTIME_MODE in UCI factory. Delete SERVICE_MODE references. Use RUNTIME_MODE
        everywhere (UIC canonical). status: done

# Phase 4 — ServiceCLI Integration

- id: p4-servicecli-service-runtime content: |
  - [ ] [AGENT] P0. ServiceCLI constructs ServiceRuntime from parsed args + env vars. Passes to handler via config dict.
        Handler.run() has full runtime context without reading env vars directly. status: done
- id: p4-servicecli-testnet-flag content: |
  - [ ] [AGENT] P1. ServiceCLI reads TESTNET_MODE env var, passes to ServiceRuntime. Interfaces resolve testnet
        endpoints from UAC capability_declarations automatically. status: done
- id: p4-servicecli-scenario-flag content: |
  - [ ] [AGENT] P2. ServiceCLI adds --scenario flag (optional, default "default"). Passes to ServiceRuntime. Mock data
        generators use scenario to select data variant. status: done

# Phase 5 — Service Migration (PARALLEL)

- id: p5-instruments-service content: |
  - [ ] [AGENT] P0. instruments-service: use ServiceRuntime. Remove direct env var reads for protocol selection. Verify
        GCS writes work with --mode batch + CLOUD_PROVIDER=gcp. QG. status: todo
- id: p5-market-tick-data-service content: |
  - [ ] [AGENT] P0. market-tick-data-service: same. Fix asyncio nesting in DownloadOperation. QG. status: todo
- id: p5-features-onchain-service content: |
  - [ ] [AGENT] P0. features-onchain-service: same. QG. status: todo
- id: p5-features-delta-one-service content: |
  - [ ] [AGENT] P1. features-delta-one-service: same. QG. status: todo
- id: p5-features-volatility-service content: |
  - [ ] [AGENT] P1. features-volatility-service: same. QG. status: todo
- id: p5-strategy-service content: |
  - [ ] [AGENT] P1. strategy-service: same. QG. status: todo
- id: p5-execution-service content: |
  - [ ] [AGENT] P1. execution-service: same (no category). QG. status: todo
- id: p5-ml-training-service content: |
  - [ ] [AGENT] P1. ml-training-service: same. QG. status: todo
- id: p5-ml-inference-service content: |
  - [ ] [AGENT] P1. ml-inference-service: same. QG. status: todo
- id: p5-remaining-services content: |
  - [ ] [AGENT] P2. alerting-service, risk-and-exposure-service, pnl-attribution-service,
        position-balance-monitor-service: same pattern. QG each. status: todo

# Phase 6 — PM Manifest CLI Registry

- id: p6-manifest-cli-capabilities content: |
  - [ ] [AGENT] P1. Add cli_capabilities section to workspace-manifest.json for every service. Operations, categories,
        supports_live, extra_args. QG validates service parsers match manifest. status: done
- id: p6-qg-cli-manifest-check content: |
  - [ ] [AGENT] P2. Add QG check: service CLI parser operations/categories match PM manifest cli_capabilities. Drift =
        QG failure. status: todo

# Phase 7 — Cleanup + Validation

- id: p7-remove-protocol-env-vars content: |
  - [ ] [AGENT] P1. Remove all redundant PROTOCOL\_\* env vars from deployment-service, Dockerfiles, terraform, Cloud
        Build. Services no longer need them. status: todo
- id: p7-pipeline-e2e-gcs content: |
  - [ ] [AGENT] P0. End-to-end pipeline: instruments → market-tick-data → features-onchain with CLOUD*PROVIDER=gcp
        --mode batch. All three write to real GCS. No PROTOCOL*\* env vars. No GOOGLE_APPLICATION_CREDENTIALS. status:
        todo
- id: p7-pipeline-e2e-mock content: |
  - [ ] [AGENT] P1. Same pipeline with CLOUD_MOCK_MODE=true. Config from local files. Data from GCS test buckets. Same
        CLI, different env var. status: todo
- id: p7-pipeline-e2e-testnet content: |
  - [ ] [AGENT] P1. DeFi execution with TESTNET_MODE=true. Interfaces resolve to Sepolia endpoints. Aave supply on
        testnet via real CLI. status: todo
- id: p7-codex-control-surface-doc content: |
  - [ ] [AGENT] P1. Codex doc: 04-architecture/service-control-surface.md. The three channels, the dimensions, the flow
        diagram, the error handling, the manifest registry. status: done
