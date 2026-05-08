---
scope: [engineer]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

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
| `--feature-family`            | features-service dispatch (consolidated repo, 2026-05-08) — selects which sub-package runs | `onchain`, `volatility`, `cross_instrument`, `sports`, `calendar`, `commodity`, `delta_one`, `multi_timeframe` (UAC `FeatureFamily` enum) |
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

### `--feature-family` for the consolidated features-service (2026-05-08)

The pre-2026-05-08 layout had 8 separate `features-*-service` repos, each with its own `python -m features_<X>_service`
entry-point. The consolidated [`features-service`](../../../features-service/) replaces all 8 with a single CLI
dispatcher parameterised by `--feature-family`:

```bash
python -m features_service \
  --feature-family <onchain|volatility|cross_instrument|sports|calendar|commodity|delta_one|multi_timeframe> \
  --operation calculate \
  --mode batch \
  --asset-group DEFI \
  [--feature-group lst_yields] \
  [--shard-key '...']
```

Contract:

- `--feature-family` is **mandatory**. Validated against the UAC `FeatureFamily` StrEnum (8 members); unknown
  family raises a CLI-level error before any sub-package is imported.
- The dispatcher in
  [`features_service/cli/main.py`](../../../features-service/features_service/cli/main.py) consumes
  `--feature-family` + forwards the remaining argv to the matching sub-package's `run(argv)` shim.
- All four standard axes (`--operation`, `--mode`, `--asset-group`, `--log-level`) apply uniformly across
  families. Family-specific flags (e.g. `--feature-group`, `--start-date`) are interpreted by the family's
  `run()` after dispatch.

Architecture SSOT: [`../04-architecture/features-service-architecture.md`](../04-architecture/features-service-architecture.md).

### `--shard-key` for surgical per-shard recovery (2026-05-07)

The deployment-ui Data Status panel's Deploy-Missing button on a single leaf shard fires a backfill VM with a single
fully-qualified `--shard-key=...` flag rather than re-running the whole asset_group.

Format (pipe-delimited, 6 fields):

```
asset_group | venue | data_type | instrument_type | instrument_id_or_root | day
```

Empty fields are skipped (the underlying default applies). The 5th field routes to `--root` for bundled data_types
(`options_chain` / `futures_chain`) and to `--instrument-ids` otherwise — the `data_type` value drives the routing.

Example invocations:

```bash
# CeFi spot/perp single-instrument:
mtds collect-trades --shard-key="cefi|BINANCE-FUTURES|trades|PERPETUAL|btcusdt|2024-03-04"

# TradFi options bundle:
mtds collect-options-chain --shard-key="tradfi|CME|options_chain|options_chain|ES.OPT|2024-01-15"

# DeFi protocol shard with empty instrument_type:
mtds collect-lending-indices --shard-key="defi|AAVEV3-ARBITRUM|lending_indices||USDC|2024-03-04"
```

Per-service implementations call `market_tick_data_service.cli.shard_key.decompose_shard_key(args)` once on entry to
flatten the shard key into the individual filter flags (`--asset-group` / `--venues` / `--data-types` /
`--instrument-type` / `--instrument-ids` / `--root` / `--day`). Existing handlers don't need to know about
`--shard-key` — they consume the unpacked flags.

Other services that backfill per-shard (instruments-service, features-\* services, MDPS) should adopt the same
convention. SSOT for the format + parser:
[`market_tick_data_service/cli/shard_key.py`](../../market-tick-data-service/market_tick_data_service/cli/shard_key.py).
SSOT for the drill-down hierarchy that emits this form:
[`codex/02-data/data-status-drilldown-hierarchy.md`](../02-data/data-status-drilldown-hierarchy.md).
