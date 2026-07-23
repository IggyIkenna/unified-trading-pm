---
doc_type: codex-ssot
title: Service Control Surface
summary:
  Every service is driven by exactly three input channels — CLI (sharding), env (infra), config (hot) — validated into
  one ServiceRuntime object; lists the 9 control dimensions and their UIC/UAC StrEnum SSOTs.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, instruments-service, unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [uac, config, cli, ssot, infrastructure]
related: [/codex/04-architecture/service-framework.md, /codex/04-architecture/tier-and-import-architecture.md]
created: 2026-03-27
authoritative_for: [service control surface (CLI/env/config three-channel model), ServiceRuntime validated-input object]
referenced_by: [/codex/04-architecture/service-framework.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Service Control Surface

Every service in the Unified Trading System is driven by exactly **three input channels**. Everything else is derived.
No redundant env vars.

## The Three Channels

| Channel      | Type                 | What it controls                                    | Examples                                                                             |
| ------------ | -------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------ |
| **CLI**      | Cold, sharding       | Domain work, time range, venue/instrument selection | `--operation`, `--mode`, `--asset-group`, `--scenario`                               |
| **Env vars** | Cold, infrastructure | Cloud target, project, environment, data mode       | `CLOUD_PROVIDER`, `GCP_PROJECT_ID`, `ENVIRONMENT`, `CLOUD_MOCK_MODE`, `TESTNET_MODE` |
| **Config**   | Hot, reloadable      | Domain params, tuning, feature flags                | GCS/local YAML files via config reloader                                             |

## The Dimensions

| Dimension          | Schema                 | Valid Values                                     | Source                 |
| ------------------ | ---------------------- | ------------------------------------------------ | ---------------------- |
| **Environment**    | `UIC.EnvironmentMode`  | `dev`, `staging`, `prod`                         | Env: `ENVIRONMENT`     |
| **Cloud provider** | `UIC.CloudProvider`    | `gcp`, `aws`, `local`                            | Env: `CLOUD_PROVIDER`  |
| **Runtime mode**   | `UIC.RuntimeMode`      | `batch`, `live`                                  | CLI: `--mode`          |
| **Data mode**      | `UIC.DataMode`         | `real`, `mock`                                   | Env: `CLOUD_MOCK_MODE` |
| **Category**       | `UIC.MarketCategory`   | `CEFI`, `TRADFI`, `DEFI`, `SPORTS`, `PREDICTION` | CLI: `--asset-group`   |
| **Testnet mode**   | `UIC.TestnetMode`      | `mainnet`, `testnet`                             | Env: `TESTNET_MODE`    |
| **Operation**      | Per-service (manifest) | Service-specific                                 | CLI: `--operation`     |
| **Scenario**       | `UIC.MockScenario`     | `default`, `stress`, `empty`, ...                | CLI: `--scenario`      |
| **Log level**      | `UIC.LogLevel`         | `DEBUG`, `INFO`, `WARNING`, `ERROR`              | CLI: `--log-level`     |

Every value is a `StrEnum` in UIC or UAC. Invalid value → `STARTUP_VALIDATION_FAILED` with clear message.

## ServiceRuntime

`ServiceRuntime` (UTL) is the single object that encapsulates the full validated control surface. Constructed once at
startup from CLI args + env vars, then passed everywhere.

```python
from unified_trading_library import ServiceRuntime

runtime = ServiceRuntime.from_env_and_args(
    operation="compute",
    mode="batch",
    service_name="features-service (onchain family)",
    category=["DEFI"],
    scenario="default",
    log_level="INFO",
)

# Derived values (from topology reader)
runtime.storage_protocol   # "gcs"
runtime.messaging_protocol # "gcs" (batch) or "pubsub" (live)
runtime.config_source      # "local" (mock) or "gcs" (real)

# Boolean helpers
runtime.is_mock    # True when CLOUD_MOCK_MODE=true
runtime.is_testnet # True when TESTNET_MODE=testnet
runtime.is_live    # True when --mode=live
```

Services and libraries read from `ServiceRuntime` — never from env vars directly after startup.

## Config Source Resolution

| `CLOUD_MOCK_MODE` | Config source     | Domain data source                           |
| ----------------- | ----------------- | -------------------------------------------- |
| `true`            | Local YAML files  | Mock/sample data (local or GCS test buckets) |
| `false`           | GCS config bucket | Real cloud storage (GCS/S3)                  |

Config is always small enough for local. Domain data is never local (too big) — even in mock mode it reads from GCS test
buckets with sample data.

## Testnet Resolution

Testnet is **not** limited to DeFi. It applies to any venue with a testnet:

- **DeFi**: Sepolia, Tenderly fork
- **CeFi**: OKX testnet, Binance testnet
- **TradFi**: IBKR paper trading
- **Prediction**: Kalshi demo

UAC `capability_declarations` have `supports_testnet`, `auth_environments` (testnet/prod keys), and `base_urls`
(testnet/mainnet URLs) per venue. When `TESTNET_MODE=testnet`, interfaces resolve to testnet endpoints + testnet API
keys from Secret Manager. The mapping from `TESTNET_MODE` → actual endpoint is owned by UAC. Services don't know or care
about specific testnet URLs.

## The Flow

```
Service CLI (--operation compute --mode batch --asset-group DEFI --scenario default)
  + Env (CLOUD_PROVIDER=gcp GCP_PROJECT_ID=xxx ENVIRONMENT=dev CLOUD_MOCK_MODE=false TESTNET_MODE=testnet)
    → ServiceCLI validates all inputs against UIC schemas (StartupValidationError on invalid)
    → ServiceCLI constructs ServiceRuntime from CLI args + env vars
      → UTL topology reader: batch + gcp → storage=gcs, messaging=gcs
      → ServiceRuntime exposes: mode, provider, environment, data_mode, testnet, category
        → UCI ProtocolConfig.from_runtime() auto-derives protocol selection
        → Interfaces get testnet=true → UAC resolves testnet endpoints per venue
          → Everything just works
```

## Startup Validation

Invalid control surface input → standardised error from UTL:

```
STARTUP_VALIDATION_FAILED: Invalid CLOUD_PROVIDER='azure'. Valid: gcp, aws, local.
STARTUP_VALIDATION_FAILED: Invalid --mode='stream'. Valid: batch, live.
STARTUP_VALIDATION_FAILED: TESTNET_MODE=true but venue BINANCE has no testnet endpoints in UAC.
STARTUP_VALIDATION_FAILED: --asset-group PREDICTION not supported by instruments-service. Valid: CEFI, TRADFI, DEFI, SPORTS.
```

One error code (`STARTUP_VALIDATION_FAILED`), one library (UTL), clear message. Every service gets this for free via
`ServiceCLI`.

## Manifest Registry

PM `workspace-manifest.json` has a `cli_capabilities` section per service:

```json
"instruments-service": {
  "cli_capabilities": {
    "operations": ["instruments", "aggregate"],
    "categories": ["CEFI", "TRADFI", "DEFI", "SPORTS"],
    "supports_live": true,
    "extra_args": ["--venues", "--tickers"]
  }
},
"features-service (calendar family)": {
  "cli_capabilities": {
    "operations": ["compute", "corporate_actions", "economic_results"],
    "categories": ["CEFI", "TRADFI", "DEFI", "SPORTS"],
    "supports_live": true,
    "extra_args": []
  }
}
```

This is the registry of what each service accepts. Quality gates validate CLI parsers match the manifest.

## SSOT Locations

| What               | Where                                                                                                 |
| ------------------ | ----------------------------------------------------------------------------------------------------- |
| Dimension schemas  | `unified_api_contracts/internal/modes.py` (EnvironmentMode, TestnetMode, DataMode, RuntimeMode, etc.) |
| Market categories  | `unified_api_contracts/internal/market_category.py` (MarketCategory with PREDICTION)                  |
| Startup error      | `unified_api_contracts/internal/schemas/errors.py` (StartupValidationError)                           |
| Env var names      | `unified_api_contracts/internal/env_canon.py` (EnvVars class)                                         |
| ServiceRuntime     | `unified-trading-library/service_runtime.py`                                                          |
| Startup validation | `unified-trading-library/startup_validation.py`                                                       |
| ServiceCLI         | `unified-trading-library/service_cli.py`                                                              |
| Topology reader    | `unified-trading-library/topology/topology_reader.py`                                                 |
| Protocol config    | `unified-cloud-interface/protocol.py` (ProtocolConfig.from_runtime)                                   |
| Testnet endpoints  | `unified-api-contracts/registry/capability_declarations/` (per venue)                                 |
| CLI capabilities   | `unified-trading-pm/workspace-manifest.json` (per service)                                            |
