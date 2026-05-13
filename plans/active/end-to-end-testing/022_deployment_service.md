---
title: "E2E Test: deployment-service"
service: deployment-service
date: 2026-03-22
status: pending
---

# E2E Test: deployment-service

Follows `procedure.md` with adaptations. Pipeline position: **Infrastructure** (not in the data pipeline DAG). This
service manages deployment of the other 20+ services to Cloud Run / GKE / Compute Engine. It does NOT process market
data, so many standard test axes (mode batch/live, category sweep, testnet) do not apply in the traditional sense.

## Architecture Overview

- **CLI**: Click-based (`@click.group()` with subcommands), NOT ServiceCLI. No `--operation`/`--mode`/`--asset-group`
  axes.
- **Command groups**: `calculation` (active: `calculate`, `list-services`, `info`, `venues`), `data-status` (active),
  `deployment` (stub), `management` (stub), `analysis` (stub), `validation` (stub), `reporting` (stub).
- **Config**: `DeploymentConfig` extends `UnifiedCloudConfig` (Pydantic). ~60 fields covering GCP/AWS regions,
  concurrency limits, quota broker, VM orchestration, auto-scheduler, performance tuning.
- **Backends**: Cloud Build (GCP) and AWS CodeBuild. State stored in GCS/S3.
- **Sharding engine**: `ShardCalculator` + `ConfigLoader` read YAML configs from `configs/` directory (15 service
  sharding configs, venues.yaml, data catalogues).
- **Frontend**: Feeds deployment-ui Admin > DevOps tab (8 sub-tabs: deployments, builds, scaling, health, costs, etc.).

## Operations (CLI Subcommands)

| Subcommand      | What it does                                             | Active? |
| --------------- | -------------------------------------------------------- | ------- |
| `calculate`     | Compute deployment shards for a service                  | Yes     |
| `list-services` | List all services with sharding configs                  | Yes     |
| `info`          | Show detailed sharding config for a service              | Yes     |
| `venues`        | Show available venues by category                        | Yes     |
| `data-status`   | Check data completion status for a service across dates  | Yes     |
| `deploy`        | Trigger actual deployment (Cloud Run/GKE/Compute Engine) | Stub    |
| `manage`        | Service management (scale, restart, health)              | Stub    |
| `analyze`       | Deployment analysis (cost, performance)                  | Stub    |
| `validate`      | Pre-deployment validation checks                         | Stub    |
| `report`        | Deployment reporting                                     | Stub    |

## Test Matrix

### Phase 1: Config Validation (no network, fast)

Test that `DeploymentConfig` validates all env var combinations correctly:

| #   | Env vars / flags                                             | Expected                       | Status |
| --- | ------------------------------------------------------------ | ------------------------------ | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp GCP_PROJECT_ID=test-project`             | OK, effective_region=asia-ne1  |        |
| 1.2 | `CLOUD_PROVIDER=aws AWS_REGION=ap-northeast-1`               | OK, effective_region=ap-ne1    |        |
| 1.3 | `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`                  | OK, mock mode                  |        |
| 1.4 | `CLOUD_PROVIDER=azure`                                       | Validation error               |        |
| 1.5 | Default config (no env vars)                                 | OK, defaults applied           |        |
| 1.6 | `DEFAULT_MAX_CONCURRENT=3000 MAX_CONCURRENT_HARD_LIMIT=2500` | Check if soft > hard is caught |        |
| 1.7 | `--cloud gcp` CLI flag                                       | Overrides env var              |        |
| 1.8 | `--cloud aws` CLI flag                                       | Switches to AWS backend        |        |
| 1.9 | `--config-dir /nonexistent`                                  | ClickException raised          |        |

### Phase 2: Shard Calculation (dry-run, read-only)

Run each `calculate` subcommand and verify output correctness. No cloud writes happen -- shard calculation is pure
computation from YAML configs.

| #    | Command                                                                                                                 | Expected                                        | Status |
| ---- | ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------ |
| 2.1  | `calculate -s instruments-service --start-date 2024-01-01 --end-date 2024-01-03 --dry-run`                              | Shards shown, "DRY RUN" message                 |        |
| 2.2  | `calculate -s instruments-service --start-date 2024-01-01 --end-date 2024-01-03 -o json`                                | Valid JSON with summary + shards array          |        |
| 2.3  | `calculate -s instruments-service --start-date 2024-01-01 --end-date 2024-01-03 -o commands`                            | CLI commands per shard printed                  |        |
| 2.4  | `calculate -s market-tick-data-service --asset-group CEFI --start-date 2024-01-01 --end-date 2024-01-01`                | CEFI-only shards                                |        |
| 2.5  | `calculate -s instruments-service --max-shards 5 --start-date 2024-01-01 --end-date 2024-12-31`                         | ShardLimitExceeded error (>5 shards)            |        |
| 2.6  | `calculate -s nonexistent-service --start-date 2024-01-01 --end-date 2024-01-01`                                        | FileNotFoundError for missing config            |        |
| 2.7  | `calculate -s execution-service --cloud-config-path gs://bucket/configs/ --start-date 2024-01-01 --end-date 2024-01-01` | Dynamic GCS discovery (requires GCS access)     |        |
| 2.8  | `calculate -s instruments-service --start-date 2024-01-01 --end-date 2024-01-03 --ignore-start-dates`                   | All date-venue combos (no launch date filter)   |        |
| 2.9  | `calculate -s instruments-service --venue binance --start-date 2024-01-01 --end-date 2024-01-01`                        | Filtered to binance only                        |        |
| 2.10 | `list-services`                                                                                                         | Lists all 15 configured services                |        |
| 2.11 | `info -s instruments-service`                                                                                           | Dimensions, CLI args, compute recs, runtime est |        |
| 2.12 | `venues`                                                                                                                | Categories with venues listed                   |        |

### Phase 3: Data Status (network required, read-only)

The `data-status` command reads from GCS to check data completion. No writes.

| #    | Command                                                                                                    | Expected                                    | Status |
| ---- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------- | ------ |
| 3.1  | `data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21`                         | Tree output with completion %               |        |
| 3.2  | `data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21 -o json`                 | JSON output                                 |        |
| 3.3  | `data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21 -o summary`              | Summary output                              |        |
| 3.4  | `data-status -s instruments-service --start-date 2026-03-01 --end-date 2026-03-21 -t`                      | With timestamps (oldest/newest)             |        |
| 3.5  | `data-status -s instruments-service --start-date 2026-03-01 --end-date 2026-03-21 -m`                      | Missing dates listed                        |        |
| 3.6  | `data-status -s instruments-service --start-date 2026-03-01 --end-date 2026-03-21 -b`                      | Benchmark info shown                        |        |
| 3.7  | `data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21 --check-venues`          | Venue coverage within parquet files         |        |
| 3.8  | `data-status -s market-tick-data-service --start-date 2026-03-21 --end-date 2026-03-21 --check-data-types` | Per-data_type completion                    |        |
| 3.9  | `data-status -s execution-service --start-date 2026-03-21 --end-date 2026-03-21`                           | Dynamic dimension display (no completion %) |        |
| 3.10 | `data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21 --mode live`             | Live mode path prefix                       |        |
| 3.11 | `data-status -s market-tick-data-service --check-venues`                                                   | Error: --check-venues only for instruments  |        |

### Phase 4: Config Loading Sweep

Verify all 15 sharding config YAMLs load without error and produce valid shards:

| #    | Service config                                   | Expected                                        | Status |
| ---- | ------------------------------------------------ | ----------------------------------------------- | ------ |
| 4.1  | `sharding.instruments-service.yaml`              | Valid dimensions, venues resolved               |        |
| 4.2  | `sharding.market-tick-data-service.yaml`         | Valid dimensions with data_types                |        |
| 4.3  | `sharding.features-service (delta-one family).yaml`       | Valid dimensions with feature_groups            |        |
| 4.4  | `sharding.features-service (volatility family).yaml`      | Valid dimensions                                |        |
| 4.5  | `sharding.features-service (onchain family).yaml`         | Valid dimensions (DeFi protocols)               |        |
| 4.6  | `sharding.features-service (calendar family).yaml`        | Valid dimensions                                |        |
| 4.7  | `sharding.features-service (sports family).yaml`          | Valid dimensions (leagues)                      |        |
| 4.8  | `sharding.market-data-processing-service.yaml`   | Valid dimensions with timeframes                |        |
| 4.9  | `sharding.ml-training-service.yaml`              | Valid dimensions (dynamic GCS)                  |        |
| 4.10 | `sharding.ml-inference-service.yaml`             | Valid dimensions                                |        |
| 4.11 | `sharding.execution-service.yaml`                | Valid dimensions (dynamic GCS config discovery) |        |
| 4.12 | `sharding.strategy-service.yaml`                 | Valid dimensions                                |        |
| 4.13 | `sharding.pnl-attribution-service.yaml`          | Valid dimensions                                |        |
| 4.14 | `sharding.risk-and-exposure-service.yaml`        | Valid dimensions                                |        |
| 4.15 | `sharding.position-balance-monitor-service.yaml` | Valid dimensions                                |        |
| 4.16 | `venues.yaml`                                    | All categories present, venues listed           |        |
| 4.17 | `cloud-providers.yaml`                           | GCP + AWS provider configs loaded               |        |

### Phase 5: Cloud Provider A/B

Test that CLI correctly switches between GCP and AWS backends:

| #   | What                                               | Expected                                | Status |
| --- | -------------------------------------------------- | --------------------------------------- | ------ |
| 5.1 | `--cloud gcp calculate -s instruments-service ...` | GCS bucket paths in shard CLI commands  |        |
| 5.2 | `--cloud aws calculate -s instruments-service ...` | S3 bucket paths in shard CLI commands   |        |
| 5.3 | GCP effective properties                           | `effective_region=asia-northeast1`      |        |
| 5.4 | AWS effective properties                           | `effective_region=ap-northeast-1`       |        |
| 5.5 | State bucket derivation (GCP)                      | `unified-deployment-state-{project_id}` |        |
| 5.6 | State bucket derivation (AWS)                      | `unified-deployment-state-{account_id}` |        |

### Phase 3b: Data Source Toggle (--source flag)

Test the manifest vs GCS data source modes for `data-status`:

| #    | Command / Config                                                                                               | Expected                                                   | Status |
| ---- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ------ |
| 3b.1 | `data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21 --source manifest`           | Fast result from Parquet manifests via DuckDB              |        |
| 3b.2 | `data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21 --source gcs`                | Original GCS blob-scan behavior, same data                 |        |
| 3b.3 | `data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21 --source auto`               | Tries manifest first, falls back to GCS if no manifests    |        |
| 3b.4 | `data-status -s instruments-service --source manifest` vs `--source gcs` (same date range)                     | Output matches: same services, dates, completion %         |        |
| 3b.5 | `DATA_STATUS_SOURCE=manifest data-status -s instruments-service --start-date 2026-03-21 --end-date 2026-03-21` | Env var selects manifest mode                              |        |
| 3b.6 | `DATA_STATUS_SOURCE=gcs data-status ... --source manifest`                                                     | CLI flag overrides env var (manifest wins)                 |        |
| 3b.7 | `data-status -s instruments-service --source manifest --check-venues`                                          | Falls back to GCS or errors (venues need blob granularity) |        |
| 3b.8 | `data-status -s market-tick-data-service --source manifest --check-data-types`                                 | Falls back to GCS or errors (data-types need blob scan)    |        |
| 3b.9 | `data-status -s instruments-service --source manifest` with no manifests written                               | Graceful empty result or auto-fallback to GCS              |        |

### Phase 5b: Mock vs Real A/B

| #    | Config                                  | Expected                                        | Status |
| ---- | --------------------------------------- | ----------------------------------------------- | ------ |
| 5b.1 | `CLOUD_MOCK_MODE=true` + `calculate`    | Shard calculation works (local config only)     |        |
| 5b.2 | `CLOUD_MOCK_MODE=true` + `data-status`  | Should either use mock data or error gracefully |        |
| 5b.3 | `CLOUD_MOCK_MODE=false` + `calculate`   | Same as 5b.1 (calculate is config-only)         |        |
| 5b.4 | `CLOUD_MOCK_MODE=false` + `data-status` | Real GCS reads                                  |        |

### Phase 6: Stub Commands

Verify stub command groups don't crash and return clean empty results:

| #   | Command group | Expected                                | Status |
| --- | ------------- | --------------------------------------- | ------ |
| 6.1 | `deploy`      | Empty group (no subcommands registered) |        |
| 6.2 | `manage`      | Empty group (no subcommands registered) |        |
| 6.3 | `analyze`     | Empty group (no subcommands registered) |        |
| 6.4 | `validate`    | Empty group (no subcommands registered) |        |
| 6.5 | `report`      | Empty group (no subcommands registered) |        |

### Phase 7: Observability

| #   | Check                   | Expected                                                               | Status |
| --- | ----------------------- | ---------------------------------------------------------------------- | ------ |
| 7.1 | UEI setup               | `setup_events(service_name="deployment-service", mode="batch")` called |        |
| 7.2 | Tracing setup           | `setup_tracing("deployment-service")` called                           |        |
| 7.3 | GracefulShutdownHandler | Initialized at CLI group level                                         |        |
| 7.4 | Verbose mode (`-v`)     | DEBUG logging enabled                                                  |        |
| 7.5 | Error formatting        | Click-styled red error messages on stderr                              |        |
| 7.6 | ShardLimitExceeded      | Clean error message with count, exit code 1                            |        |
| 7.7 | FileNotFoundError       | Clean error message, exit code 1                                       |        |

## Known Issues Audit

Before testing, check for these patterns known from instruments-service E2E:

| Pattern                        | Applies? | Notes                                                 |
| ------------------------------ | -------- | ----------------------------------------------------- |
| `load_dotenv(override=True)`   | Check    | Deployment-service may have its own .env loading      |
| `os.getenv()` direct calls     | Check    | Should use `DeploymentConfig` everywhere              |
| Bucket resolution via env vars | Check    | `effective_state_bucket` property derives from config |
| Pydantic warnings suppressed   | Yes      | `warnings.filterwarnings("ignore")` in CLI main.py    |
| Config directory resolution    | Check    | `get_config_dir()` tries multiple heuristics          |

## AWS Testing

| #   | What                                                                                         | Expected                          | Status |
| --- | -------------------------------------------------------------------------------------------- | --------------------------------- | ------ |
| A.1 | `--cloud aws calculate -s instruments-service --start-date 2024-01-01 --end-date 2024-01-01` | AWS-specific shard output         |        |
| A.2 | `DeploymentConfig` with `CLOUD_PROVIDER=aws`                                                 | `effective_region=ap-northeast-1` |        |
| A.3 | AWS failover regions                                                                         | 4 AWS regions returned            |        |
| A.4 | GCP failover regions                                                                         | 4 GCP regions returned            |        |

## Frontend API Surface

deployment-service feeds the deployment-ui (richest satellite UI, 9/10 score). Key API endpoints that need E2E
verification once stub commands are implemented:

| Endpoint / Data           | UI Tab      | What deployment-ui displays                   |
| ------------------------- | ----------- | --------------------------------------------- |
| Shard calculation results | Deployments | Shard count, dimensions, CLI commands         |
| Data completion status    | Data Status | Tree view with completion %, missing dates    |
| Service list + configs    | Services    | Available services, sharding dimensions       |
| Venue coverage            | Venues      | Categories, venues per category               |
| Deployment state (future) | Builds      | Active builds, status, logs                   |
| Cost estimates (future)   | Costs       | Per-service, per-shard cost projections       |
| Scaling configs (future)  | Scaling     | Concurrency limits, VM orchestration settings |
| Health checks (future)    | Health      | Service health, stuck shards, OOM detection   |

## Issues Found

(logged in `plans/archive/issues/service_control_surface_issues_2026_03_21.md`)

| Issue      | Severity | Fixed? |
| ---------- | -------- | ------ |
| (none yet) |          |        |

## Next Service

After deployment-service passes all phases -> proceed to `023_trading_agent_service.md`
