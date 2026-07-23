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
related: [/codex/05-infrastructure/cloud-agnostic-script-pattern.md, /codex/02-data/per-asset-group-bucket-layouts.md]
created: 2026-03-27
authoritative_for:
  [
    four-tier bucket isolation model (mock/dev/stg/prd/test),
    Group A vs Group B bucket classification,
    mock-tier scenario/grid prefix routing,
    bucket-name resolution authority (resolve_bucket_name vs UTL PATH_REGISTRY),
  ]
referenced_by:
  [
    /codex/05-infrastructure/deployment-ui-architecture.md,
    /codex/05-infrastructure/deployment-ui-environment-tiers.md,
    /codex/09-strategy/architecture-v2/instruments-resolver-architecture.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md,
    plans/archive/2026_07/bucket_env_split_rollout_2026_06.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
  ]
owner:
last_reviewed: 2026-07-20
code_refs:
  [
    unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py,
    unified-trading-library/unified_trading_library/config_interface/paths/registry.py,
    unified-trading-library/unified_trading_library/domain_client/clients/market_data.py,
    deployment-service/configs/cloud-providers.yaml,
  ]
---

# Bucket Isolation Model — Four-Tier Architecture

SSOT: `unified-trading-library` `resolve_bucket_name()` (`unified_trading_library.cloud_interface.bucket_naming`) and
`deployment-service/configs/cloud-providers.yaml`.

> **Stale pointer removed**: the old SSOT was `unified-cloud-interface/unified_cloud_interface/constants.py`
> (`get_bucket_environment`, `get_bucket_name`). That module is retired; all bucket resolution now routes through UTL
> `resolve_bucket_name()` + the YAML.

> **⚠️ A SECOND bucket-name registry still exists and disagrees with this one.** UTL
> `config_interface/paths/registry.py`'s `PATH_REGISTRY` / `build_bucket()` produces **un-tiered** names with no env
> axis, and several of them resolve to buckets that **no longer exist**. It is not a documentation-only drift — it is
> reached at runtime. **See § 11 before trusting any bucket name that did not come from `resolve_bucket_name()`.**

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

| yaml `kind`                    | Bucket prefix       | Per-AG?                       |
| ------------------------------ | ------------------- | ----------------------------- |
| `instruments-store`            | `instruments-store` | yes (CEFI/DEFI/TRADFI/SPORTS) |
| `market-data`                  | `market-data-tick`  | yes (CEFI/DEFI/TRADFI/SPORTS) |
| `instruments-store-prediction` | `instruments-store` | no — `-pred-` infix           |
| `market-data-tick-prediction`  | `market-data-tick`  | no — `-pred-` infix           |
| `features-calendar`            | `features-calendar` | no (cross-asset)              |

Naming: `{prefix}-{ag}-{env_short}-{project_id}` (e.g. `market-data-tick-cefi-prd-central-element-323112`). Cross-asset
kinds (no AG): `{prefix}-{env_short}-{project_id}` (e.g. `features-calendar-prd-central-element-323112`).

> **⛔ CORRECTED 2026-07-20** — two rows were removed from the table above because neither is a live Group-A kind:
>
> - **`data-catalogue`** — there is **no `data-catalogue` key in `cloud-providers.yaml`** (verified: grep returns zero
>   matches in the file). `resolve_bucket_name(kind="data-catalogue")` therefore **raises** `BucketNamingError`
>   (`bucket_naming.py:426`, the `yaml_kind not in storage_section_d` branch). The only workspace references hardcode a
>   flat, un-tiered name outside the resolver — `unified-trading-pm/scripts/catalogue/sync-to-mock.py:178` builds
>   `f"data-catalogue-{project_id}"`, and `scripts/catalogue/sync-catalogue-yaml.py:34` sets
>   `CATALOGUE_BUCKET_PREFIX = "data-catalogue"`. This is the same defect class as § 11. § 7 below is annotated
>   accordingly.
> - **DeFi raw on-chain** (`dex-pools`, `dex-swaps`, `evm-defi`, `eigenlayer-rewards`, `solana-defi`) — **all five kinds
>   are REMOVED from `cloud-providers.yaml`**, each with a dated in-file removal comment: `dex-swaps` / `evm-defi` /
>   `solana-defi` 2026-07-10 (`cloud-providers.yaml:117-118`), `eigenlayer-rewards` 2026-07-16 (`:127-129`), `dex-pools`
>   2026-07-13 (`:130-134`). Every writer/reader was repointed to `kind="tick-data"` — the shared
>   `market-data-tick-defi-{env}-{pid}` bucket — and the dedicated buckets were verified empty and deleted. The AWS
>   section mirrors the removals (`:238`, `:243`, `:245`).
>
> **Do not read the deleted DeFi prefixes as a delete authorisation for GCS object trees.** The `dex_pools/` and
> `lending_indices/` **object prefixes inside the consolidated defi bucket** are a separate question and are
> **DO-NOT-DELETE** — see `plans/active/issues/defi_dex_pools_delete_order_stale_2026_07_20.md`. Deleted _bucket kinds_
> ≠ deletable _object prefixes_.

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
> server-side copy, parity-verified) then deleted; ~41 buckets removed (estate 103 GCP: ~30 by the folds + 11 ml source
> buckets in the ml-fold GCP completion). The fold is documented per domain in
> `plans/active/bucket_fold_{features,ml,execution_strategy,portfolio_state}_2026_07_17.md` +
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
# unified_trading_library/cloud_interface/bucket_naming.py:142-152 (verbatim, verified 2026-07-20)
_DEPLOYMENT_ENV_SHORT_FORM: Final[dict[str, str]] = {
    "dev": "dev",
    "development": "dev",
    "staging": "stg",
    "stg": "stg",         # ← already-short form accepted
    "prod": "prd",
    "prd": "prd",         # ← already-short form accepted
    "production": "prd",
    "test": "test",       # 4 chars — the E2E `-test-` variant; well under the cap.
    "ci": "ci",           # ← CI tier
}
```

> **⛔ CORRECTED 2026-07-20** — the previous quote listed **6** keys and omitted `stg`, `prd` and `ci`. The code has
> **9**. The omission mattered in both directions: it hid the `ci` tier entirely, and it made the already-short forms
> (`stg`, `prd`) look like they would fail resolution when they resolve fine.

Resolution order (`_resolve_deployment_env_short`, `bucket_naming.py:155-177`): explicit `deployment_env=` argument →
`DEPLOYMENT_ENV` env var → `ENVIRONMENT` env var → `"prod"` default. **Pass `deployment_env=` explicitly to reach a
specific tier — never mutate the process env** (`:387-390`; env mutation is the banned config-env write). An env with no
known short form raises `BucketNamingError` rather than falling back (`:167-168`).

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

> **⛔ CORRECTED 2026-07-20 — the `-prd-` tier shown above is aspirational, not what the code does.** There is no
> `data-catalogue` key in `cloud-providers.yaml`, so this bucket is **not resolvable via `resolve_bucket_name()`** (it
> raises). The two live consumers hardcode the **flat, un-tiered** name outside the resolver:
> `unified-trading-pm/scripts/catalogue/sync-to-mock.py:178` (`f"data-catalogue-{project_id}"`) and
> `scripts/catalogue/sync-catalogue-yaml.py:34`. So the real name in use is `data-catalogue-{project_id}`, and the claim
> "each deployment env has its own catalogue" is **not implemented**.
>
> **UNVERIFIED**: whether either flat or `-prd-` bucket currently exists. A live `gcloud storage ls` probe of both names
> failed on 2026-07-20, but the failure did not distinguish 404 from a permissions denial, and project-wide
> `storage.buckets.list` is denied for `unified-trading-sa` — so absence is **not** established. Do not act on this as a
> confirmed 404 without a re-probe that distinguishes the two.
>
> Resolution is the same as § 11: either add a `data-catalogue` key to `cloud-providers.yaml` and repoint both scripts,
> or retire the scripts. Not decided here.

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

---

## 11. Bucket-name resolution authority

_Added 2026-07-20. Two bucket-name registries exist in the workspace and they disagree. This section states which one
wins, records the live defect the other one carries, and states what is still unknown._

### 11.1 The ruling

**`cloud-providers.yaml` via UTL `resolve_bucket_name(cloud, kind, asset_group, deployment_env)` is the SSOT for every
bucket name. It is the only authority.** Everything in §§ 1–10 above describes it.

Two properties make it the authority rather than merely the preferred option:

- **It has an env axis.** Names carry the tier: `market-data-tick-{ag}-prd-{pid}`, `instruments-store-{ag}-prd-{pid}`,
  `features-calendar-prd-{pid}`.
- **It raises rather than falling back.** An unknown cloud (`bucket_naming.py:406-407`), unknown asset_group
  (`:408-409`), missing yaml key (`:426`) or unresolvable env (`:167-168`) all raise `BucketNamingError`. A wrong input
  fails loud; it never silently yields a plausible-looking name.

### 11.2 The shadow registry — UTL `PATH_REGISTRY` / `build_bucket()`

`unified-trading-library/unified_trading_library/config_interface/paths/registry.py` carries a **second, independent**
bucket-name registry that produces **un-tiered** names. `build_bucket()` (`:307-314`) substitutes only `{project_id}`
and `{category}` — **there is no env parameter at all**:

```python
def build_bucket(name: str, *, project_id: str, asset_group: str = "") -> str:
    spec = get_spec(name)
    return spec.bucket_template.format(project_id=project_id, category=asset_group)
```

The file states the gap in its own comments (`:48-50`, on the `delta_one_features` row): _"The `-prd-` env tier is
hardcoded because this registry has no env axis (build_bucket substitutes only {project_id}/{category})."_

The Wave-3 folds (§ 2, Group B) repointed **only the Group-B rows** — those rows now carry a literal `-prd-` baked into
the template (`features-{category}-prd-{project_id}` at `:56`, `ml-store-prd-{project_id}` at `:105`,
`execution-store-prd-{project_id}` at `:183`, `portfolio-state-prd-{project_id}` at `:207`, and ~20 more). The **Group-A
rows were left un-tiered**:

| Row                 | Line  | `bucket_template`                           |
| ------------------- | ----- | ------------------------------------------- |
| `raw_tick_data`     | `:20` | `market-data-tick-{category}-{project_id}`  |
| `processed_candles` | `:27` | `market-data-tick-{category}-{project_id}`  |
| `instruments`       | `:34` | `instruments-store-{category}-{project_id}` |
| `calendar_features` | `:63` | `features-calendar-{project_id}`            |

### 11.3 The live defect — these names resolve to buckets that no longer exist

This is not documentation drift. Probed live 2026-07-20 (`gcloud storage ls`, project `central-element-323112`):

| Bucket name                                        | Produced by                   | Probe          |
| -------------------------------------------------- | ----------------------------- | -------------- |
| `market-data-tick-cefi-central-element-323112`     | `PATH_REGISTRY` (`:20`/`:27`) | **FAIL / 404** |
| `market-data-tick-defi-central-element-323112`     | `PATH_REGISTRY` (`:20`/`:27`) | **FAIL / 404** |
| `instruments-store-cefi-central-element-323112`    | `PATH_REGISTRY` (`:34`)       | **FAIL / 404** |
| `features-calendar-central-element-323112`         | `PATH_REGISTRY` (`:63`)       | **FAIL / 404** |
| `market-data-tick-cefi-prd-central-element-323112` | `resolve_bucket_name()`       | **OK**         |

The un-tiered names were the pre-env-split estate; they were migrated and deleted. `PATH_REGISTRY` still resolves to
them.

**They are reached at runtime.** `unified-trading-library/unified_trading_library/domain_client/clients/market_data.py`
imports `build_bucket` (`:13`) and calls it in `MarketTickDomainClient`:

- `:56` — `MarketTickDomainClient.get_tick_data()` (class at `:43`):
  `build_bucket("raw_tick_data", project_id=..., asset_group=asset_group)`, then `self._read_parquet(bucket, path)`
- `:71` — `get_available_dates()` (def `:69`): same call, then `self._list_blobs(bucket, "raw_tick_data/by_date/")`

`MarketCandleDomainClient` (class at `:82`) does the same for `processed_candles` at `:96` and `:112`. All four call
sites feed the resolved name straight into a storage operation.

### 11.4 Resolution

**`PATH_REGISTRY`'s bucket-naming responsibility is retired in favour of `resolve_bucket_name()`.** Its `path_template`
/ `partition_keys` / `file_template` responsibilities are a separate concern and are **not** in scope here — only
`bucket_template` + `build_bucket()` are superseded.

Two implementations satisfy the ruling; the choice between them is not made here:

- **(a) Retire `build_bucket()`** — rewrite each caller to `resolve_bucket_name(cloud=..., kind=..., asset_group=...)`,
  delete `bucket_template` from `DataSetSpec`. Cleanest; one registry survives. Cost: every `build_bucket` /
  `build_full_uri` caller changes, and `build_full_uri()` (`:322`) composes bucket + path, so it needs the resolver
  threaded through it.
- **(b) Give `PATH_REGISTRY` an env axis** — add `deployment_env` to `build_bucket()` and a `${DEPLOYMENT_ENV_SHORT}`
  placeholder to each template. Smaller diff. Cost: two registries survive, and they will drift again — this is the
  second time the Group-A rows have been left behind by a fold.

Until one lands, **any bucket name that did not come from `resolve_bucket_name()` is suspect** and must be probed before
use.

### 11.5 OPEN QUESTION — are UTL market-data domain-client reads currently failing in production?

**Unresolved, and it decides the severity.** The two possibilities are materially different and the evidence to date
does not separate them:

- **Live breakage** — a production consumer calls `MarketTickDomainClient.get_tick_data()` / `get_available_dates()` and
  has been getting 404s or empty reads since the un-tiered buckets were deleted. Severity P0.
- **Dead code** — `MarketTickDomainClient` / `MarketCandleDomainClient` have no live production caller, and the 404 is
  latent: harmless today, a trap for the next person who wires them up. Severity P2, fix-when-touched.

What is established: the names are produced (§ 11.2), the buckets are gone (§ 11.3), and the call sites feed them
directly to storage (§ 11.3). What is **NOT** established: whether any production code path reaches those methods.

Answering it requires a caller census of `MarketTickDomainClient` and `MarketCandleDomainClient` across all repos —
**grep-then-READ, not grep-then-conclude**: zero grep hits does not settle it, because domain clients are commonly
resolved at runtime through a registry or factory rather than imported by name. Also check `get_available_dates()`
specifically — `_list_blobs` on a missing bucket may return empty rather than raising, which would surface as a **silent
wrong-answer** (reported "no data available") rather than an error, and would be invisible in logs.

Note that `get_available_dates()` also performs a `_list_blobs(bucket, "raw_tick_data/by_date/")` — a whole-corpus
prefix listing. If that method does turn out to be live, it is a single-walk-discipline concern as well as a 404
concern.
