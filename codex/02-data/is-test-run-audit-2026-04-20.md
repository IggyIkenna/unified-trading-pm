---
doc_type: codex-ssot
title: IS_TEST_RUN Audit — Per-Service Status (2026-04-20)
summary: >-
  Per-service inventory (2026-04-20) of how IS_TEST_RUN=true routes writes to the -test-{pid} sibling bucket — which
  services carry the is_test_run config field, how each routes writes (UTL get_write_bucket_name auto-honours it;
  services that build bucket names manually must swap the suffix themselves), and the MDPS dep-checker IS_TEST_RUN
  auto-trigger; Phase-1 deliverable of the institutional smoke matrix plan.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [deployment-service, features-service, instruments-service, market-data-processing-service, market-tick-data-service]
scope: [engineer, admin]
tags: [smoke-test, bucket-name, infrastructure, audit, verification]
related: [/codex/02-data/per-asset-group-bucket-layouts.md, /codex/02-data/bucket-naming-and-config.md]
created: 2026-04-20
authoritative_for: [IS_TEST_RUN test-bucket write routing per-service audit (2026-04-20)]
referenced_by:
owner:
last_reviewed: 2026-05-17
code_refs:
---

# IS_TEST_RUN Audit — Per-Service Status (2026-04-20)

**Purpose**: Per-service inventory of how `IS_TEST_RUN=true` (env var) → `-test-` bucket suffix is honoured. Written as
the Phase 1 deliverable of the institutional smoke matrix plan
(`plans/archive/institutional_smoke_matrix_2026_04_20.plan.md`). Pairs with the per-asset-group bucket SSOT
(`per-asset-group-bucket-layouts.md`).

**Status**: canonical reference for Phase 2 (per-service smoke scripts). Updated post-propagation.

**Naming convention** (single SSOT, mirrors `per-asset-group-bucket-layouts.md`):

- PROD: `{prefix}-{category_lower}-{project_id}` — e.g. `instruments-store-cefi-central-element-323112`
- TEST: `{prefix}-{category_lower}-test-{project_id}` — e.g. `instruments-store-cefi-test-central-element-323112`

UTL helper `unified_trading_library.core.cloud_constants.get_write_bucket_name(domain, category)` already auto-honours
`IS_TEST_RUN` env var via `get_env_var("IS_TEST_RUN")`. Services that route writes through `get_write_bucket_name()` get
test-bucket routing for free. Services that build bucket names manually (via `*_bucket_template` Fields or
`get_bucket_for_category()`) MUST consult `cfg.is_test_run` and swap the suffix themselves.

---

## Audit matrix (post-Phase-1)

| #   | Service                                    | Has `is_test_run` field? | How writes route                                                | Dep-checker test_mode auto-trigger? |
| --- | ------------------------------------------ | ------------------------ | --------------------------------------------------------------- | ----------------------------------- |
| 1   | instruments-service                        | YES (pre-existing)       | orchestrator: `cfg.is_test_run` → `instruments-store-*-test-*`  | n/a (no dep-checker)                |
| 2   | market-tick-data-service                   | YES (pre-existing)       | orchestrator `get_tick_data_bucket()` honours `cfg.is_test_run` | n/a (no dep-checker)                |
| 3   | market-data-processing-service             | YES (Phase 1 added)      | dep-checker: `test_mode=True` swaps via UPSTREAM_DEPS_TEST      | YES (Phase 1 — IS_TEST_RUN env)     |
| 4   | features-service (sports family)           | YES (Phase 1 added)      | service writes via UTL `get_write_bucket_name()` → auto-test    | n/a (no dep-checker)                |
| 5   | features-service (calendar family)         | YES (Phase 1 added)      | shared bucket (no category) — `cfg.is_test_run` swaps suffix    | n/a (no dep-checker)                |
| 6   | features-service (onchain family)          | YES (Phase 1 added)      | `output_bucket_template` + `cfg.is_test_run` to swap suffix     | n/a (no dep-checker)                |
| 7   | features-service (delta-one family)        | YES (Phase 1 added)      | `output_bucket_template` + `cfg.is_test_run` to swap suffix     | n/a (no dep-checker)                |
| 8   | features-service (volatility family)       | YES (Phase 1 added)      | `output_bucket_template` + `cfg.is_test_run` to swap suffix     | n/a (no dep-checker)                |
| 9   | features-service (cross-instrument family) | YES (Phase 1 added)      | `output_bucket_template` + `cfg.is_test_run` to swap suffix     | n/a (no dep-checker)                |
| 10  | features-service (multi-timeframe family)  | YES (Phase 1 added)      | `output_bucket_template` + `cfg.is_test_run` to swap suffix     | n/a (no dep-checker)                |
| 11  | features-service (commodity family)        | YES (Phase 1 added)      | `commodity_profiles_bucket` + `cfg.is_test_run` swaps           | n/a (no dep-checker)                |
| 12  | ml-training-service                        | YES (Phase 1 added)      | per-bucket templates + `cfg.is_test_run` to swap suffix         | n/a (no dep-checker)                |
| 13  | ml-inference-service                       | YES (Phase 1 added)      | per-bucket templates + `cfg.is_test_run` to swap suffix         | n/a (no dep-checker)                |

---

## Reference helper SSOT

```python
# unified_trading_library/core/cloud_constants.py
def get_write_bucket_name(
    domain: str,
    category: Optional[str] = None,
    project_id: Optional[str] = None,
) -> str:
    """Like get_bucket_name() but honours IS_TEST_RUN=true by routing
    to the -test-{pid} sibling bucket."""
    base = get_bucket_name(domain, category, project_id)
    is_test_run = (get_env_var("IS_TEST_RUN") or "").lower() in ("true", "1", "yes")
    if not is_test_run:
        return base
    pid = project_id or get_project_id()
    return base.replace(f"-{pid}", f"-test-{pid}")
```

**Use `get_write_bucket_name(...)` for ALL write paths.** Reads (instrument catalogues, corporate actions, ref-data)
should keep calling `get_bucket_name(...)` so test runs still see canonical production reference data.

---

## Per-service `is_test_run` Field declaration (Phase 1 standard)

```python
from pydantic import AliasChoices, Field
from unified_trading_library import UnifiedCloudConfig

class MyServiceConfig(UnifiedCloudConfig):
    is_test_run: bool = Field(
        default=False,
        validation_alias=AliasChoices("IS_TEST_RUN"),
        description="Route writes to -test- bucket instead of prod (E2E test mode)",
    )
```

---

## Bucket-resolver helper inventory (per-service)

| Service                                    | Bucket helper                                               | Where it lives                                                 |
| ------------------------------------------ | ----------------------------------------------------------- | -------------------------------------------------------------- |
| instruments-service                        | UTL `get_bucket_name("instruments", category)`              | `engine/orchestrator.py` (uses cfg.is_test_run separately)     |
| market-tick-data-service                   | `get_tick_data_bucket(config, category)`                    | `engine/orchestrator.py:1313`                                  |
| market-data-processing-service             | `_resolve_upstream_bucket()` + `OUTPUT_BUCKETS_TEST` map    | `app/core/dependency_checker.py:349`                           |
| features-service (sports family)           | UTL `get_bucket_name("features_sports")`                    | (no shared category) — call `get_write_bucket_name()` at write |
| features-service (calendar family)         | `cfg.source_bucket_template` (shared)                       | `config.py:40` — wrap with `cfg.is_test_run` swap              |
| features-service (onchain family)          | `cfg.output_bucket_template`                                | `config.py:69` — wrap with `cfg.is_test_run` swap              |
| features-service (delta-one family)        | `cfg.output_bucket_template`                                | `config.py:147` — wrap with `cfg.is_test_run` swap             |
| features-service (volatility family)       | `cfg.output_bucket_template`                                | `config.py:40` — wrap with `cfg.is_test_run` swap              |
| features-service (cross-instrument family) | `cfg.output_bucket_template`                                | `config.py:129` — wrap with `cfg.is_test_run` swap             |
| features-service (multi-timeframe family)  | `cfg.output_bucket_template`                                | `config.py:165` — wrap with `cfg.is_test_run` swap             |
| features-service (commodity family)        | `cfg.commodity_profiles_bucket`                             | `config.py:64` — wrap with `cfg.is_test_run` swap              |
| ml-training-service                        | `cfg.features_*_bucket_template` + `ml-models-store-*`      | `config.py:54+` — wrap with `cfg.is_test_run` swap             |
| ml-inference-service                       | `cfg.features_*_bucket_template` + `ml-predictions-store-*` | per-bucket — wrap with `cfg.is_test_run` swap                  |

**Phase-1 scope**: every service has the `is_test_run` field landed. Phase-2 will run smoke matrices that set
`IS_TEST_RUN=true`, exercise each service's write paths, and confirm shards land in `-test-` buckets. If a write path is
discovered to bypass the field (i.e. writes to PROD even with IS_TEST_RUN=true), Phase 2 will add the swap at the
write-call site as a per-service fix item.

---

## Dep-checker IS_TEST_RUN auto-trigger (Phase 1.5)

UTL `BaseDependencyChecker.__init__` now resolves `test_mode` as:

```python
def __init__(self, project_id=None, test_mode=False):
    if not test_mode:
        # Auto-trigger from IS_TEST_RUN env var if not explicitly set
        env_test = (get_env_var("IS_TEST_RUN") or "").lower() in ("true", "1", "yes")
        test_mode = env_test
    self.test_mode = test_mode
```

This means any service that calls `DependencyChecker()` (no args) automatically uses TEST upstream maps when
`IS_TEST_RUN=true`. MDPS `process_handler.py` and any future service dep-checker get this for free.

Today only MDPS has a dep-checker. Future services that add one inherit the auto-trigger via `BaseDependencyChecker`.

---

## Verification

After the smoke matrix runs in Phase 2 with `IS_TEST_RUN=true`, every shard landed in a `-test-` bucket should appear
under `gs://{prefix}-{category}-test-{project_id}/...`. The Phase 6 end-to-end validation asserts this invariant.

## Cross-references

- Per-asset-group bucket layouts SSOT: `/codex/02-data/per-asset-group-bucket-layouts.md`
- Plan: `plans/archive/institutional_smoke_matrix_2026_04_20.plan.md`
- UTL helper: `unified_trading_library/core/cloud_constants.py:215` (`get_write_bucket_name`)
- MDPS dep-checker: `market-data-processing-service/market_data_processing_service/app/core/dependency_checker.py`
- `setup-buckets.py` (existing test-bucket provisioner):
  `deployment-service/scripts/setup-buckets.py --include-test --test-only`
- New idempotent provision script: `deployment-service/scripts/provision-test-buckets.sh`
- New lifecycle config: `deployment-service/configs/test-bucket-lifecycle.json`
- New verification CLI: `deployment-service/scripts/verify-test-bucket-lifecycle.sh`
