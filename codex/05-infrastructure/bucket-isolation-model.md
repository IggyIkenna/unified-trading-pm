---
doc_type: codex-ssot
title: Bucket Isolation Model — Four-Tier Architecture
summary:
  Four-tier GCS/S3 bucket isolation (mock / dev / stg / prd / test) resolved by UTL resolve_bucket_name(); Group A raw
  data (env-tiered) vs Group B derived data naming, mock-tier scenario/grid routing, prod-tier IAM write-protection, and
  GCS lifecycle expiry rules.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [infrastructure, bucket, canonicalisation, storage]
related: [codex/05-infrastructure/cloud-agnostic-script-pattern.md, codex/02-data/per-asset-group-bucket-layouts.md]
created: 2026-03-27
authoritative_for:
  [
    four-tier bucket isolation model (mock/dev/stg/prd/test),
    Group A vs Group B bucket classification,
    mock-tier scenario/grid prefix routing,
  ]
referenced_by:
  [
    codex/05-infrastructure/deployment-ui-architecture.md,
    codex/05-infrastructure/deployment-ui-environment-tiers.md,
    codex/09-strategy/architecture-v2/instruments-resolver-architecture.md,
    codex/16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md,
    plans/archive/2026_07/bucket_env_split_rollout_2026_06.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
  ]
owner:
last_reviewed: 2026-06-29
code_refs:
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

### Group B — Derived Data (env-tiered, Wave-3 folded)

Derived data is tier-specific (each tier writes its own bucket set) **and Wave-3-folded** (2026-07-17/19): the former
per-kind / per-AG bucket explosion collapsed into five canonical folded buckets. The kind/AG axis that used to be in the
**bucket name** is now a top-level **object-key PREFIX** on the path. Resolution is unchanged for callers —
`resolve_bucket_name(kind=<any retired kind>)` transparently returns the folded bucket via UTL `_KIND_ALIASES` (soft
window; see below).

| Folded bucket     | Per-AG?                                | Retired kinds folded in                                                                                                                | Object-key prefix (was the bucket-name axis)                                                                                   |
| ----------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `features-{ag}`   | **Yes** (cefi/defi/tradfi/sports/pred) | `features-delta-one`, `-volatility`, `-onchain`, `-xinstrument`, `-mtf`                                                                | `delta_one/` \| `volatility/` \| `onchain/` \| `xinstrument/` \| `mtf/`                                                        |
| `ml-store`        | No (cross-asset flat)                  | `ml-models-store`, `-predictions-store`, `-configs-store`, `-training-artifacts`, `ml-artifacts`                                       | `models/` \| `predictions/` \| `configs/` \| `training-artifacts/` \| `artifacts/`                                             |
| `execution-store` | No (cross-asset flat; **ag→prefix**)   | per-AG `execution-store-{cefi,defi,tradfi,sports}` (dict) + `execution-store-prediction`                                               | `{cefi,defi,tradfi,sports}/…` (asset_group) + `pred/` (prediction branch)                                                      |
| `strategy-store`  | No (cross-asset flat)                  | (already flat — gained its `-{env}-` tier in this wave)                                                                                | — (no fold; env-tier only)                                                                                                     |
| `portfolio-state` | No (cross-asset flat)                  | `positions-store`, `pnl-attribution-store`, `risk-metrics-store`, `pnl-attribution-output`, `archetype-state`, `position-store-sports` | `positions/` \| `pnl-attribution/` \| `risk-metrics/` \| `pnl-attribution-output/` \| `archetype-state/` \| `position-sports/` |

Naming (per-AG, `features-{ag}`): `{prefix}-{ag}-{env_short}-{project_id}` (e.g.
`features-cefi-prd-central-element-323112`). Naming (cross-asset, the other four): `{prefix}-{env_short}-{project_id}`
(e.g. `ml-store-prd-central-element-323112`, `execution-store-prd-central-element-323112`,
`portfolio-state-prd-central-element-323112`).

> **SUPERSEDED (2026-07-19, Wave-3 folds)** — the prior per-kind bucket rows (`features-delta-one`, `ml-models-store`,
> per-AG `execution-store-{ag}`, the six portfolio stores, …) are RETIRED. The source buckets were migrated (additive
> server-side copy, parity-verified) then deleted; ~30 buckets removed (estate 114 GCP). The fold is documented per
> domain in `plans/active/bucket_fold_{features,ml,execution_strategy,portfolio_state}_2026_07_17.md` +
> `plans/active/bucket_fold_closeout_2026_07_17.md`. Each writer/reader now prepends its object-key prefix (a wrong
> prefix = silent empty read — guarded by writer↔reader parity unit tests in UTL `tests/config_interface/`).

> **`_KIND_ALIASES` soft window** — UTL `bucket_naming._KIND_ALIASES` maps every retired kind → its folded key (applied
> once, non-transitively, BEFORE the yaml lookup). The retired per-kind yaml keys are KEPT during the soft window so
> un-redeployed consumers still resolve; the alias shadows them. The aliases + retired yaml keys are hard-removed at the
> **alias-sunset** phase (closeout plan P3) once every `resolve_bucket_name` caller of the old kind is grep-clean.

> **Prior env-split state (folded into the above)**: Group B env-split was temporarily rolled back (2026-05-19) while G4
> canonicalisation migrations ran, then re-scoped 2026-07-13 (operator ruling — single migration, no double migrates) to
> land via these Wave-3 consolidation folds (folded buckets env-tiered from birth);
> `bucket_env_split_rollout_2026_06.md` is archived/superseded.

---

## 3. Bucket Naming Examples

```
# Group A — env tier after AG
instruments-store-defi-prd-central-element-323112
market-data-tick-cefi-prd-central-element-323112
features-calendar-prd-central-element-323112

# Group B — env tier after AG (the one remaining per-AG folded kind: features-{ag})
features-cefi-prd-central-element-323112     # kind=features-delta-one|-volatility|-mtf|… ag=cefi (per-kind → object prefix)

# Group B — env tier after prefix (cross-asset folded kinds; kind/AG axis → object prefix)
strategy-store-prd-central-element-323112
ml-store-prd-central-element-323112          # kind=ml-models-store|-predictions-store|… (per-kind → models/|predictions/|…)
execution-store-prd-central-element-323112   # any asset_group (ag → {category}/ prefix) + prediction (→ pred/)
portfolio-state-prd-central-element-323112   # positions|pnl-attribution|risk-metrics|archetype-state|… (→ domain prefix)

# Mock tier (mode-based, any env)
features-cefi-mock-central-element-323112
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

# Group B — features (Wave-3 folded: 5 per-kind → per-AG features-{ag}; kind → object-key prefix)
bucket = resolve_bucket_name(cloud="gcp", kind="features-delta-one", asset_group="defi")
# → "features-defi-prd-central-element-323112"   (writer prepends "delta_one/" to the object key)

# Group B — cross-asset strategy store
bucket = resolve_bucket_name(cloud="gcp", kind="strategy-store")
# → "strategy-store-prd-central-element-323112"

# Group B — cross-asset folded stores (kind/AG axis → object-key prefix, NOT bucket name)
resolve_bucket_name(cloud="gcp", kind="ml-models-store")            # → "ml-store-prd-…"        (prefix "models/")
resolve_bucket_name(cloud="gcp", kind="execution-store", asset_group="cefi")  # → "execution-store-prd-…" (prefix "cefi/")
resolve_bucket_name(cloud="gcp", kind="positions-store")           # → "portfolio-state-prd-…" (prefix "positions/")
```

Services must never hardcode bucket names. `resolve_bucket_name()` handles Group A/B classification, tier resolution,
and project ID injection automatically. The YAML (`cloud-providers.yaml`) is the SSOT for kind→template mappings;
`resolve_bucket_name()` is the SSOT for resolution.
