---
scope: [engineer]
---

# Service CLI Convention

## Standardised CLI Axes

Every service CLI MUST use these orthogonal axes. Each axis controls one concern.

### Axis 1: `--operation` (WHAT domain work to do)

- Required for all services
- Examples by service type:
  - Data pipeline: `download`, `compute`, `instruments`, `aggregate`
  - ML training: `train`, `evaluate`, `grid-search`
  - ML inference: `infer`, `predict`
  - Execution: `backtest`, `live-execution`
  - Features: `compute`
- This is the domain operation, not the infrastructure mode

### Axis 2: `--mode` (HOW infrastructure provisions)

- Required: `batch` or `live`
- Controls: transport (GCS/S3 vs PubSub/SQS), persistence strategy, deployment topology
- Defined by `runtime-topology.yaml` — services don't interpret this, they pass it to UTL which orchestrates libraries
- batch = GCS/S3 read/write, file-based, historical
- live = PubSub/SQS streaming, event-driven, real-time
- The service code should be mode-agnostic where possible — UTL handles the infrastructure switching

### Axis 3: `--asset-group` (WHAT market domain)

- Values: `CEFI`, `TRADFI`, `DEFI`, `SPORTS`
- nargs="+" to allow multiple: `--asset-group CEFI TRADFI`
- Documented exception: execution-service omits this — it routes based on instruction content (cross-category execution
  like HL basis trades)

### Axis 4: `--log-level` (observability override)

- Values: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- Default: `INFO`
- Overrides config/env var LOG_LEVEL
- Runtime adjustment: services SHOULD support dynamic log level change via admin endpoint (`POST /admin/log-level`) or
  config reloader for live services

### Optional Axes (service-specific)

| Axis                          | When to use                 | Examples                                                                                  |
| ----------------------------- | --------------------------- | ----------------------------------------------------------------------------------------- |
| `--stage`                     | ML training pipeline phases | `feature-selection`, `hyperparameter-tuning`, `walk-forward`, `ensemble`, `meta-learning` |
| `--start-date` / `--end-date` | Batch time range            | `2024-07-01`                                                                              |
| `--venues`                    | Venue filtering             | `BINANCE DERIBIT HYPERLIQUID`                                                             |
| `--instruments`               | Instrument filtering        | Ticker symbols or IDs                                                                     |
| `--feature-group`             | Feature service grouping    | `lending_rates`, `lst_yields`, `ALL`                                                      |
| `--dry-run`                   | No writes, local output     | Boolean flag                                                                              |
| `--force`                     | Skip existence checks       | Boolean flag                                                                              |
| `--max-results`               | Limit output count          | Integer                                                                                   |
| `--scenario`                  | Mock data variant           | `default`, `stress`, `empty`                                                              |
| `--config`                    | Config file override        | Path to YAML                                                                              |

### ServiceCLI (UTL shared abstraction)

All services SHOULD use `ServiceCLI` from `unified_trading_library.service_cli` for CLI dispatch. ServiceCLI:

- Parses the standardised axes
- Routes `--operation` to registered handler classes
- Passes `--mode` to UTL infrastructure orchestration
- Each handler extends `BaseModeHandler` with `validate_config()` and `async run()`

### Mock/Real (NOT a CLI flag)

Mock vs real is controlled by environment variables, not CLI flags:

- `CLOUD_MOCK_MODE=true/false` — sample data vs real cloud
- `MOCK_STATE_MODE=interactive/deterministic` — stateful vs stateless mock
- Same CLI invocation works in dev/staging/prod — env var controls infrastructure
- Mock scenarios selected via `--scenario` CLI flag (optional)

### Log Level Hierarchy

```
CLI --log-level  ->  ENV LOG_LEVEL  ->  Config  ->  Default (INFO)
```

For live services, support runtime adjustment:

- Admin endpoint: `POST /admin/log-level {"level": "DEBUG"}` — instant, resets on restart
- Config reloader: log_level field in domain config — persists across restarts

### Anti-Patterns

- Using `--mode` for operation (what) instead of infrastructure (how)
- Using `--run-mode` as a separate flag instead of `--mode`
- Hardcoding `mode="service"` in library calls — pass the actual CLI mode
- Creating service-specific CLI parsers when ServiceCLI covers the use case
- Using `--mock` as a CLI flag instead of `CLOUD_MOCK_MODE` env var

### Current Violations (to be fixed)

| Service                  | Violation                                                 | Fix                                                     |
| ------------------------ | --------------------------------------------------------- | ------------------------------------------------------- |
| instruments-service      | `--mode` used for operation, `--run-mode` for actual mode | Rename: `--operation` for what, `--mode` for batch/live |
| market-tick-data-service | `args.operation` referenced but not defined               | Add `--operation` or fix reference                      |
| ml-training-service      | `--mode` used for operation (train/evaluate)              | Rename to `--operation`, add `--mode batch/live`        |
| UTL base_service.py      | Passes `mode="service"` to UEI                            | Pass actual CLI mode (batch/live)                       |
