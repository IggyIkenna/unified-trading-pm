---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Bucket Isolation Model -- Three-Tier Architecture

SSOT: `unified-cloud-interface/unified_cloud_interface/constants.py` (`get_bucket_environment`, `get_bucket_name`,
`get_scenario_prefix`)

---

## 1. Three-Tier Isolation

All GCS/S3 buckets resolve to one of three tiers based on runtime environment:

| Tier   | Condition                                     | Purpose                                     |
| ------ | --------------------------------------------- | ------------------------------------------- |
| `mock` | `CLOUD_MOCK_MODE=true` (any ENVIRONMENT)      | Backtesting, scenario analysis, experiments |
| `dev`  | `ENVIRONMENT in (dev, development, staging)`  | Realistic E2E testing, staging integration  |
| `prod` | Everything else (including unset ENVIRONMENT) | Production -- IAM write-protected           |

Resolution function: `get_bucket_environment()` in `constants.py`.

---

## 2. Group A vs Group B

### Group A -- Raw / Shared Data (no env suffix)

Raw data is immutable and environment-independent. All tiers read from the same bucket.

| Domain              | Bucket prefix       |
| ------------------- | ------------------- |
| `instruments`       | `instruments-store` |
| `market_data`       | `market-data-tick`  |
| `features_calendar` | `features-calendar` |
| `data_catalogue`    | `data-catalogue`    |

Naming: `{prefix}-{category}-{project_id}` (with category) or `{prefix}-{project_id}` (without).

### Group B -- Derived Data (env-isolated)

Derived data is tier-specific. Each tier writes to its own bucket set.

| Domain                | Bucket prefix          |
| --------------------- | ---------------------- |
| `features_delta_one`  | `features-delta-one`   |
| `features_onchain`    | `features-onchain`     |
| `features_volatility` | `features-volatility`  |
| `execution`           | `execution-store`      |
| `strategy`            | `strategy-store`       |
| `ml_models`           | `ml-models-store`      |
| `ml_predictions`      | `ml-predictions-store` |
| `ml_configs`          | `ml-configs-store`     |
| `pnl`                 | `pnl-store`            |

Naming: `{prefix}-{category}-{env}-{project_id}` (with category) or `{prefix}-{env}-{project_id}` (without).

---

## 3. Bucket Naming Examples

```
# Group A -- no env in name
instruments-store-defi-my-proj
market-data-tick-cefi-my-proj
data-catalogue-my-proj

# Group B -- env tier in name
strategy-store-defi-mock-my-proj      (mock tier)
strategy-store-defi-dev-my-proj       (dev tier)
strategy-store-defi-prod-my-proj      (prod tier)
execution-store-mock-my-proj          (mock, no category)
```

---

## 4. Env-to-Tier Mapping

```python
def get_bucket_environment() -> str:
    if CLOUD_MOCK_MODE == "true":
        return "mock"
    if ENVIRONMENT in ("dev", "development", "staging"):
        return "dev"
    return "prod"
```

Staging shares the `dev` tier. This is intentional -- staging validates against dev-grade data before promoting to prod.

---

## 5. Scenario Routing (Mock Tier Only)

Within mock buckets, data is further isolated by scenario or grid prefix:

```
scenario=default/       # standard regression seed
scenario=stress/        # high cardinality load test
scenario=missing_data/  # failure mode testing
grid=defi-sweep-001/    # parameter sweep run
```

Resolution: `get_scenario_prefix(scenario=..., grid_id=...)` returns the prefix string. Returns `""` outside mock tier.

Grid IDs take precedence over scenarios when both are set.

---

## 6. Standard vs Custom Scenarios

Standard scenarios are defined in `unified-trading-pm/configs/standard-scenarios.yaml`.

| Type     | Lifetime  | Examples                                            |
| -------- | --------- | --------------------------------------------------- |
| Standard | Permanent | `default`, `stress`, `missing_data`, `corrupt_data` |
| Custom   | 30 days   | Grid sweeps, ad-hoc backtests, sync slices          |

Custom scenarios auto-expire via GCS lifecycle policy (see section 9).

---

## 7. Data Catalogue

A shared catalogue bucket stores per-service Parquet manifests:

```
data-catalogue-{project_id}/
  {service_name}/
    day={YYYY-MM-DD}/
      manifest.parquet
```

Each manifest records what data was written, when, and to which bucket/path. DuckDB queries across manifests to answer
"what data exists for date X, service Y?"

The catalogue bucket is Group A (no env suffix) -- it tracks data across all tiers.

### Data Status Integration

deployment-service `data-status` CLI reads manifests as a fast alternative to GCS blob scanning:

    python -m deployment_service data-status --service instruments-service --source manifest
    python -m deployment_service data-status --service instruments-service --source gcs
    python -m deployment_service data-status --service instruments-service --source auto

Feature toggle: `--source` flag overrides `DATA_STATUS_SOURCE` env var (default: `auto`).

ManifestReader provides:

- get_freshness(): per-service/venue freshness with hours-since-last-write
- get_completion(): completion percentage, missing dates, per-venue breakdown
- is_available(): checks DuckDB installed + not local mode

---

## 8. Prod Bucket IAM Write-Protection

Prod buckets have IAM policies that restrict write access:

- Service accounts for batch/live workloads: read + write (scoped to their domain)
- CI/CD service accounts: read-only on prod, read + write on mock/dev
- Developer accounts: read-only on prod, read + write on mock/dev

`CLOUD_MOCK_MODE=true` or `ENVIRONMENT=dev` never resolves to prod tier, preventing accidental prod writes during
development or testing.

---

## 9. GCS Lifecycle Policies

Mock bucket cleanup rules:

| Rule                   | Target                          | Action               |
| ---------------------- | ------------------------------- | -------------------- |
| Custom scenario expiry | `scenario=*/` (non-standard)    | Delete after 30 days |
| Grid sweep expiry      | `grid=*/`                       | Delete after 30 days |
| Standard scenario data | `scenario={default,stress,...}` | No expiry            |

Lifecycle rules are applied at the bucket level via Terraform/gcloud. Standard scenario names are exempt from cleanup.

---

## 10. Usage in Services

```python
from unified_cloud_interface import get_bucket_name, get_scenario_prefix

bucket = get_bucket_name("strategy", "DEFI")
prefix = get_scenario_prefix(scenario="stress")
full_path = f"{prefix}day=2026-03-23/output.parquet"
```

Services must never hardcode bucket names. The `get_bucket_name` function handles Group A/B classification, tier
resolution, and project ID injection automatically.
