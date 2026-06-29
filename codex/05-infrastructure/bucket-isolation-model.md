---
scope: [engineer, admin]
last_reviewed: 2026-06-29
---

# Bucket Isolation Model — Four-Tier Architecture

SSOT: `unified-trading-library` `resolve_bucket_name()` (`unified_trading_library.cloud_interface.bucket_naming`) and
`deployment-service/configs/cloud-providers.yaml`.

> **Stale pointer removed**: the old SSOT was `unified-cloud-interface/unified_cloud_interface/constants.py`
> (`get_bucket_environment`, `get_bucket_name`). That module is retired; all bucket resolution now routes through UTL
> `resolve_bucket_name()` + the YAML.

---

## 1. Four-Tier Isolation

All GCS/S3 buckets resolve to one of four tiers based on runtime environment and mode:

| Tier   | Short form | Condition                                | Purpose                                           |
| ------ | ---------- | ---------------------------------------- | ------------------------------------------------- |
| `mock` | `mock`     | `CLOUD_MOCK_MODE=true` (any ENVIRONMENT) | Backtesting, scenario analysis, scenario prefixes |
| `dev`  | `dev`      | `DEPLOYMENT_ENV=dev`                     | Dev-local integration testing                     |
| `stg`  | `stg`      | `DEPLOYMENT_ENV=staging`                 | Staging integration — its **own** tier, NOT dev   |
| `prd`  | `prd`      | `DEPLOYMENT_ENV=prod` (or unset → prod)  | Production — IAM write-protected                  |
| `test` | `test`     | E2E test harness (`DEPLOYMENT_ENV=test`) | CI E2E (short-lived, lifecycle-deleted)           |

Resolution: UTL `_DEPLOYMENT_ENV_SHORT_FORM` dict (`dev→dev`, `staging→stg`, `prod→prd`). `mock` is a mode
(`CLOUD_MOCK_MODE=true`), not a `DEPLOYMENT_ENV` value — it overrides tier resolution for all envs.

> **Breaking change vs prior doc**: staging is its own `-stg-` tier, NOT an alias for `dev`. The old
> `get_bucket_environment()` mapping (`staging→dev`) is retired.

---

## 2. Group A vs Group B

### Group A — Raw / Shared Data (env-tiered)

Raw data is environment-tiered in GCS name. The naming convention adds the env short form after the AG suffix.

| Domain              | Bucket prefix                                                             |
| ------------------- | ------------------------------------------------------------------------- |
| `instruments-store` | `instruments-store`                                                       |
| `market-data`       | `market-data-tick`                                                        |
| `features-calendar` | `features-calendar`                                                       |
| `data-catalogue`    | `data-catalogue`                                                          |
| DeFi raw on-chain   | `dex-pools`, `dex-swaps`, `evm-defi`, `eigenlayer-rewards`, `solana-defi` |

Naming: `{prefix}-{ag}-{env_short}-{project_id}` (e.g. `market-data-tick-cefi-prd-central-element-323112`). Cross-asset
kinds (no AG): `{prefix}-{env_short}-{project_id}` (e.g. `features-calendar-prd-central-element-323112`).

### Group B — Derived Data (env-tiered)

Derived data is tier-specific. Each tier writes to its own bucket set.

| Domain                  | Bucket prefix           | Per-AG?                            |
| ----------------------- | ----------------------- | ---------------------------------- |
| `features-delta-one`    | `features-delta-one`    | Yes (cefi/defi/tradfi/sports/pred) |
| `features-volatility`   | `features-volatility`   | Yes                                |
| `features-onchain`      | `features-onchain`      | Yes (cefi/defi)                    |
| `features-xinstrument`  | `features-xinstrument`  | Yes                                |
| `features-mtf`          | `features-mtf`          | Yes                                |
| `execution-store`       | `execution-store`       | Yes (cefi/defi/tradfi/sports)      |
| `strategy-store`        | `strategy-store`        | No (cross-asset flat)              |
| `ml-training-artifacts` | `ml-training-artifacts` | No (cross-asset)                   |
| `ml-artifacts`          | `ml-artifacts`          | No                                 |
| `ml-models-store`       | `ml-models-store`       | No                                 |
| `ml-predictions-store`  | `ml-predictions-store`  | No                                 |
| `ml-configs-store`      | `ml-configs-store`      | No                                 |

Naming (per-AG): `{prefix}-{ag}-{env_short}-{project_id}` (e.g. `features-delta-one-cefi-prd-central-element-323112`)
Naming (cross-asset): `{prefix}-{env_short}-{project_id}` (e.g. `strategy-store-prd-central-element-323112`)

> **Prior state (rolled back)**: Group B env-split was temporarily rolled back (2026-05-19) while G4 canonicalisation
> migrations ran. Re-enabling per `bucket_env_split_rollout_2026_06.md` (in-flight 2026-06-29).

---

## 3. Bucket Naming Examples

```
# Group A — env tier after AG
instruments-store-defi-prd-central-element-323112
market-data-tick-cefi-prd-central-element-323112
features-calendar-prd-central-element-323112

# Group B — env tier after AG (per-AG kinds)
features-delta-one-cefi-prd-central-element-323112
execution-store-cefi-prd-central-element-323112

# Group B — env tier after prefix (cross-asset kinds)
strategy-store-prd-central-element-323112
ml-training-artifacts-prd-central-element-323112
ml-artifacts-prd-central-element-323112

# Mock tier (mode-based, any env)
features-delta-one-cefi-mock-central-element-323112
```

---

## 4. Env-to-Tier Mapping (UTL)

```python
# unified_trading_library.cloud_interface.bucket_naming
_DEPLOYMENT_ENV_SHORT_FORM = {
    "dev": "dev",
    "development": "dev",
    "staging": "stg",     # staging → stg (NOT dev)
    "prod": "prd",
    "production": "prd",
    "test": "test",
}
```

`CLOUD_MOCK_MODE=true` forces `mock` tier regardless of `DEPLOYMENT_ENV`.

> **Retired**: `unified_cloud_interface.constants.get_bucket_environment()` (3-tier: mock/dev/prod, staging→dev). Never
> call this — it returns wrong tiers for staging.

---

## 5. Scenario Routing (Mock Tier Only)

Within mock buckets, data is further isolated by scenario or grid prefix:

```
scenario=default/       # standard regression seed
scenario=stress/        # high cardinality load test
scenario=missing_data/  # failure mode testing
grid=defi-sweep-001/    # parameter sweep run
```

Resolution: UTL `get_scenario_prefix(scenario=..., grid_id=...)`. Returns `""` outside mock tier. Grid IDs take
precedence over scenarios when both are set.

---

## 6. Standard vs Custom Scenarios

Standard scenarios are defined in `unified-trading-pm/configs/standard-scenarios.yaml`.

| Type     | Lifetime  | Examples                                            |
| -------- | --------- | --------------------------------------------------- |
| Standard | Permanent | `default`, `stress`, `missing_data`, `corrupt_data` |
| Custom   | 30 days   | Grid sweeps, ad-hoc backtests, sync slices          |

Custom scenarios auto-expire via GCS lifecycle policy.

---

## 7. Data Catalogue

A shared catalogue bucket stores per-service Parquet manifests:

```
data-catalogue-prd-{project_id}/
  {service_name}/
    day={YYYY-MM-DD}/
      manifest.parquet
```

Each manifest records what data was written, when, and to which bucket/path.

The catalogue bucket is Group A (env-tiered). Each deployment env has its own catalogue.

---

## 8. Prod Bucket IAM Write-Protection

Prod buckets (`-prd-`) have IAM policies that restrict write access:

- Service accounts for batch/live workloads: read + write (scoped to their domain)
- CI/CD service accounts: read-only on prod, read + write on mock/dev
- Developer accounts: read-only on prod, read + write on mock/dev

`CLOUD_MOCK_MODE=true` or `DEPLOYMENT_ENV=dev` never resolves to prd tier, preventing accidental prod writes during
development or testing. Staging (`stg`) uses its own IAM write-protection separate from prod. See
`bucket_iam_write_protection_per_tier_2026_06_09.md` for the IAM rollout plan.

---

## 9. GCS Lifecycle Policies

Mock bucket cleanup rules:

| Rule                   | Target                          | Action               |
| ---------------------- | ------------------------------- | -------------------- |
| Custom scenario expiry | `scenario=*/` (non-standard)    | Delete after 30 days |
| Grid sweep expiry      | `grid=*/`                       | Delete after 30 days |
| Standard scenario data | `scenario={default,stress,...}` | No expiry            |

Test bucket cleanup: all content deleted after 7 days via lifecycle rule.

---

## 10. Usage in Services

```python
from unified_trading_library.cloud_interface import resolve_bucket_name

# Group A — instruments store
bucket = resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="cefi")
# → "instruments-store-cefi-prd-central-element-323112"

# Group B — features
bucket = resolve_bucket_name(cloud="gcp", kind="features-delta-one", asset_group="defi")
# → "features-delta-one-defi-prd-central-element-323112"

# Group B — cross-asset strategy store
bucket = resolve_bucket_name(cloud="gcp", kind="strategy-store")
# → "strategy-store-prd-central-element-323112"
```

Services must never hardcode bucket names. `resolve_bucket_name()` handles Group A/B classification, tier resolution,
and project ID injection automatically. The YAML (`cloud-providers.yaml`) is the SSOT for kind→template mappings;
`resolve_bucket_name()` is the SSOT for resolution.
