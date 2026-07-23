---
doc_type: codex-ssot
title: Service CLI Convention
summary: >-
  Service CLI SSOT — the four orthogonal axes (`--operation` what / `--mode` batch|live / `--asset-group` /
  `--log-level`), canonical `VENUE:INSTRUMENT_TYPE:SYMBOL` instrument-id parsing (split on first two colons), the
  6-tuple atomic shard, the pipe-delimited `--shard-key` form, and `--feature-family` / ml `--operation` dispatch.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-ui, execution-service, features-service, instruments-service, market-tick-data-service, ml-service]
scope: [engineer]
tags: [cli-convention, mtds, features, ml, instruments, mdps]
related:
  [
    /codex/02-data/data-status-drilldown.md,
    /codex/06-coding-standards/service-orchestration-patterns.md,
    /codex/04-architecture/features-service-architecture.md,
    /codex/04-architecture/ml-service-architecture.md,
  ]
created: 2026-03-27
authoritative_for: [service CLI convention and canonical instrument_id CLI parsing, shard-key CLI format]
referenced_by:
  [
    /codex/04-architecture/features-service-architecture.md,
    /codex/04-architecture/instruments-live-architecture.md,
    /codex/06-coding-standards/data-engine-selection.md,
    /codex/06-coding-standards/script-homes.md,
    /codex/06-coding-standards/service-orchestration-patterns.md,
    /codex/06-coding-standards/service-structure-standards.md,
  ]
owner:
last_reviewed:
code_refs:
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

| Axis                          | When to use                                                                                | Examples                                                                                                                                  |
| ----------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `--stage`                     | ML training pipeline phases                                                                | `feature-selection`, `hyperparameter-tuning`, `walk-forward`, `ensemble`, `meta-learning`                                                 |
| `--start-date` / `--end-date` | Batch time range                                                                           | `2024-07-01`                                                                                                                              |
| `--venues`                    | Venue filtering                                                                            | `BINANCE DERIBIT HYPERLIQUID`                                                                                                             |
| `--instruments`               | Instrument filtering                                                                       | Ticker symbols or IDs                                                                                                                     |
| `--feature-family`            | features-service dispatch (consolidated repo, 2026-05-08) — selects which sub-package runs | `onchain`, `volatility`, `cross_instrument`, `sports`, `calendar`, `commodity`, `delta_one`, `multi_timeframe` (UAC `FeatureFamily` enum) |
| `--feature-group`             | Feature service grouping                                                                   | `lending_rates`, `lst_yields`, `ALL`                                                                                                      |
| `--dry-run`                   | No writes, local output                                                                    | Boolean flag                                                                                                                              |
| `--force`                     | Skip existence checks                                                                      | Boolean flag                                                                                                                              |
| `--max-results`               | Limit output count                                                                         | Integer                                                                                                                                   |
| `--scenario`                  | Mock data variant                                                                          | `default`, `stress`, `empty`                                                                                                              |
| `--config`                    | Config file override                                                                       | Path to YAML                                                                                                                              |

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

| Service | Violation | Fix | | ------------------------ | --------------------------------------------------------- |
------------------------------------------------------------------------------------------------------------------------------------------------

| ----- | -------- | ----------- | ----------------------- | | instruments-service | `--mode` used for operation,
`--run-mode` for actual mode | Rename: `--operation` for what, `--mode` for batch/live | | market-tick-data-service |
`args.operation` referenced but not defined | Add `--operation` or fix reference | | ~~ml-training-service~~ |
~~`--mode` used for operation (train/evaluate)~~ | **DONE + REPO ARCHIVED** — ml-training-service + ml-inference-service
consolidated into `ml-service` (2026-05-20). `ml-service --operation train | infer | evaluate | grid-search | pipeline`
is canonical. | | UTL base_service.py | Passes `mode="service"` to UEI | Pass actual CLI mode (batch/live) |

### Instrument Identity and CLI Granularity (HARD RULE — codified 2026-05-28)

Every batch service that accepts an `--instrument-ids` (or `--instruments`) flag MUST treat the canonical instrument_id
form as a structured value, not as an opaque substring. The CLI is the contract — operators rely on it to scope work
down to the smallest atomic unit they care about. Substring matching against blob paths breaks that contract silently.

#### Canonical instrument_id form

```
VENUE:INSTRUMENT_TYPE:SYMBOL
```

Three colon-separated fields, no other punctuation. Examples (use these in plans + runbooks + tests):

| Asset group | Canonical id                                 | Notes                                                                |
| ----------- | -------------------------------------------- | -------------------------------------------------------------------- |
| CeFi perp   | `BINANCE-FUTURES:PERPETUAL:BTCUSDT`          | Venue suffix `-FUTURES` distinguishes from `BINANCE-SPOT`            |
| CeFi spot   | `COINBASE-SPOT:SPOT:BTC-USD`                 | Symbol may contain `-`; only the **first two** colons are separators |
| CeFi option | `DERIBIT:OPTION:BTC-31MAY24-50000-C`         | Symbol may contain `-`                                               |
| DeFi pool   | `UNISWAP-V3-ETHEREUM:DEX_POOL:USDC_WETH_500` | Chain-qualified venue per `_blob_matches_chain_split_venue` shape    |
| TradFi      | `CME:FUTURE:ES-20240315`                     | Symbol carries expiry                                                |
| Sports      | `SFI:FIXTURE:PREMIER_LEAGUE_2024_MCI_LIV`    | Sports uses `sports_reference/` shape; instrument_type is `FIXTURE`  |

#### Which axes derive from instrument_id, and which are independent

| Axis              | Derivable from instrument_id? | How                                                                                                                                                |
| ----------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `venue`           | ✅ Yes                        | First `:`-separated field                                                                                                                          |
| `instrument_type` | ✅ Yes                        | Second `:`-separated field                                                                                                                         |
| `symbol`          | ✅ Yes                        | Third+ field (may contain `-`)                                                                                                                     |
| `asset_group`     | ✅ Yes (via lookup)           | `VENUES_BY_ASSET_GROUP` reverse lookup in `unified_api_contracts.canonical.venue_taxonomy`                                                         |
| `data_type`       | ❌ No                         | A single instrument has multiple data_types (e.g. `trades` + `book_snapshot_5` + `funding_rate`). MUST be passed independently via `--data-types`. |
| `date`            | ❌ No                         | Time axis; MUST come from `--start-date` / `--end-date` or `--shard-key day` segment.                                                              |

This is the contract: **`--instrument-ids <canonical_form>` + `--data-types <type>` + `--start-date / --end-date`** is
sufficient to scope a run to one or more atomic shards. Operators MUST NOT have to also pass `--venues` or
`--asset-group` redundantly — those are derived from the canonical form.

#### The atomic shard

Composing the canonical form with the time axis + data_type gives the same 6-tuple the
[`--shard-key`](#--shard-key-for-surgical-per-shard-recovery-2026-05-07) section formalises:

```
(asset_group, venue, instrument_type, data_type, symbol, date)
```

Both representations are equivalent. `--shard-key` is the pipe-delimited single-string form (good for one-shot
deploy-missing buttons); `--instrument-ids` + `--data-types` + `--start-date` is the multi-shard form (good for narrow-
scope backfills covering several instruments / data_types / dates). Services should accept both surfaces and produce the
same atomic-shard set internally.

#### Parsing rule (the implementation contract)

Every service implementing `--instrument-ids` MUST parse the canonical form into its three components and filter blob
paths on each axis independently:

```python
def filter_blob_by_canonical_instrument_ids(
    blob_path: str,
    instrument_ids: list[str],
) -> bool:
    """Return True iff blob_path matches any of the canonical instrument_ids."""
    for iid in instrument_ids:
        parts = iid.split(":", 2)   # split on first two colons only — symbol may contain ":"
        if len(parts) != 3:
            continue                # fall through to bare-symbol fallback (legacy)
        venue, instrument_type, symbol = parts
        if (
            f"venue={venue}/" in blob_path
            and f"instrument_type={instrument_type.lower()}/" in blob_path
            and f"/{symbol}.parquet" in blob_path
        ):
            return True
    return False
```

#### Banned anti-patterns

- **Substring matching against the bare canonical form.** `BINANCE-FUTURES:PERPETUAL:BTCUSDT` is **not** a substring of
  any real blob path because the path uses `=` not `:` as the partition separator (`venue=BINANCE-FUTURES/...`). A
  substring filter against the canonical form returns ZERO blobs — the operator gets no work done and no error. This is
  what the MDPS scanner did pre-2026-05-28; the fix is documented at `orchestration_scanner.py:441-457`.
- **Bare-symbol substring across venues.** `instrument_ids=["BTCUSDT"]` substring-matches against every
  `*BTCUSDT*.parquet` across every venue, every instrument_type, every chain. The operator who passes "BTCUSDT" most
  likely meant ONE specific instrument; the service silently returns ALL of them. May be supported as a deprecated
  legacy convenience with a deprecation log, but MUST NOT be the documented happy path.
- **Mixing `--asset-group` + `--venues` + `--instrument-ids` redundantly.** If the canonical form is passed, the service
  derives venue and asset_group from it. Operator-passed `--venues` / `--asset-group` should validate-against the
  derivation (and fail loudly on mismatch), not silently override.

#### Reference incident

**2026-05-28** — MDPS narrow-scope smoke. The operator passed
`MDPS_INSTRUMENT_IDS="BINANCE-FUTURES:PERPETUAL:BTCUSDT BINANCE-FUTURES:PERPETUAL:ETHUSDT BYBIT:PERPETUAL:BTCUSDT BYBIT:PERPETUAL:ETHUSDT"`
(the documented canonical form) and `MDPS_VENUES="BINANCE-FUTURES BYBIT"`. The scanner did substring matching, the
canonical form matched zero blobs, the venue-prefix shortcut applied, and the scanner returned ~200 blobs (every
instrument in those two venues) instead of 4. Memory hit 70 GB. Operator-side post-mortem:
[`plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`](../../plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md)
§ "Finding B".

#### Composes with

- [`--shard-key` for surgical per-shard recovery](#--shard-key-for-surgical-per-shard-recovery-2026-05-07) — the
  single-string pipe-delimited form of the same 6-tuple.
- [`02-data/data-status-drilldown.md`](/codex/02-data/data-status-drilldown.md) — the UI-side drill-down hierarchy that
  emits these forms.
- [`service-orchestration-patterns.md`](service-orchestration-patterns.md) § 15 "Batch Service Lifecycle: Setup, Work,
  Cleanup" — a single-instrument drilldown invocation MUST still call the per-shard cleanup hook on exit.

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

- `--feature-family` is **mandatory**. Validated against the UAC `FeatureFamily` StrEnum (8 members); unknown family
  raises a CLI-level error before any sub-package is imported.
- The dispatcher in [`features_service/cli/main.py`](../../../features-service/features_service/cli/main.py) consumes
  `--feature-family` + forwards the remaining argv to the matching sub-package's `run(argv)` shim.
- All four standard axes (`--operation`, `--mode`, `--asset-group`, `--log-level`) apply uniformly across families.
  Family-specific flags (e.g. `--feature-group`, `--start-date`) are interpreted by the family's `run()` after dispatch.

Architecture SSOT:
[`/codex/04-architecture/features-service-architecture.md`](/codex/04-architecture/features-service-architecture.md).

### `--operation` for the consolidated ml-service (2026-05-20)

The pre-2026-05-20 layout had 2 separate repos (`ml-training-service`, `ml-inference-service`) with distinct CLIs. The
consolidated [`ml-service`](../../../ml-service/) replaces both with a single CLI dispatcher parameterised by
`--operation`:

```bash
python -m ml_service \
  --operation <train|infer|evaluate|grid-search|pre-selection|hyperparameter-grid|final-training|pipeline> \
  --mode batch \
  --asset-group TRADFI \
  --instruments ES_FRONT \
  --target-types swing_high swing_low \
  --start-date 2022-01-01 --end-date 2025-12-31
```

| `--operation`         | Mode       | Description                                                   |
| --------------------- | ---------- | ------------------------------------------------------------- |
| `train`               | batch      | Final-training run per archetype × asset-group                |
| `infer`               | batch/live | Batch or live inference against a recorded feature stream     |
| `evaluate`            | batch      | Model evaluation against a held-out fold                      |
| `grid-search`         | batch      | Hyperparameter grid search (coarse sweep)                     |
| `pre-selection`       | batch      | Feature pre-selection / importance ranking                    |
| `hyperparameter-grid` | batch      | Hyperparameter grid definition + validation                   |
| `final-training`      | batch      | Final model training with validated hyperparameters           |
| `pipeline`            | batch      | End-to-end ML pipeline (pre-select → grid → final → evaluate) |

Architecture SSOT:
[`/codex/04-architecture/ml-service-architecture.md`](/codex/04-architecture/ml-service-architecture.md).

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
mtds collect-lending-indices --shard-key="defi|AAVE_V3-ARBITRUM|lending_indices||USDC|2024-03-04"
```

Per-service implementations call `market_tick_data_service.cli.shard_key.decompose_shard_key(args)` once on entry to
flatten the shard key into the individual filter flags (`--asset-group` / `--venues` / `--data-types` /
`--instrument-type` / `--instrument-ids` / `--root` / `--day`). Existing handlers don't need to know about `--shard-key`
— they consume the unpacked flags.

Other services that backfill per-shard (instruments-service, features-\* services, MDPS) should adopt the same
convention. SSOT for the format + parser:
[`market_tick_data_service/cli/shard_key.py`](../../market-tick-data-service/market_tick_data_service/cli/shard_key.py).
SSOT for the drill-down hierarchy that emits this form:
[`/codex/02-data/data-status-drilldown.md`](/codex/02-data/data-status-drilldown.md) § "Per-asset_group depth table".
