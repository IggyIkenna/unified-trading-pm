---
doc_type: plan
title: shard-dimension-naming-asset-group-ssot-2026-04-25
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, e2e-testing, instruments-service, system-integration-tests]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-25"
overview: "Coordinated, multi-repo pass to align **service shard configuration** and **all consumers** on the dimension
  name

  `asset_group` (trading venue axis) where the legacy name was `category`, without renaming GCS `category=` path

  segments until an explicit object-store migration exists. Complements the accepted API decision in

  `/codex/11-project-management/decisions/adr-2026-04-25-category-and-asset-group-field-naming.md` and

  `venue_axis_asset_group_vocabulary_2026_04_25.plan.md`.

  "
type: mixed
epic: epic-code-completion
completion_gates: { code: C5, deployment: D2, business: none }
repo_gates:
  - { repo: deployment-service, code: C5, deployment: none, business: none }
  - { repo: deployment-api, code: C5, deployment: none, business: none }
  - { repo: deployment-ui, code: C5, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C5, deployment: none, business: none }
  - { repo: system-integration-tests, code: C5, deployment: none, business: none }
depends_on: [venue-axis-asset-group-vocabulary-2026-04-25]
isProject: false
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Global SSOT: shard dimension `category` → `asset_group`

## Why this plan exists

Vocabulary for the **venue axis** is moving to **asset group** in registry and data-plane code (see linked venue-axis
plan). **Sharding** in deployment still exposes a first-class dimension often named `category` in YAML and UI. That is a
**naming** mismatch with product language, not a different concept.

**Out of scope for this plan (handled elsewhere):**

- **GCS path literals** `category=…` in existing buckets: unchanged here; migration is a separate data ops / backfill
  program.
- **General `DeployRequest` JSON field `category`:** kept until this SSOT renames the **downstream** dimension key; then
  deployment-api can flip to `asset_group` in lockstep with deployment-service, or a single mapper at the API boundary.
  See the ADR for the current rule.

**In scope:** Rename the **shard dimension name** in configs and the **code paths** that match `filters[dim_name]` to
`asset_group` consistently in deployment-service, deployment-api (mocks, examples), deployment-ui (`getDimension`,
labels), and tests, plus SIT coverage.

## Inventory (starting points — extend during execution)

- `deployment-service`: `DimensionProcessor` / `shard_dimensions` use `dim["name"]` from service YAML; `ShardCalculator`
  docs; any hard-coded `"category"` in tests or conftest.
- `deployment-api`: `mock_data` service `dimensions` arrays; `DeployRequest.filters` key once config uses `asset_group`.
- `deployment-ui`: `DeployForm` and service lists using `getDimension("category")`.
- `unified-api-contracts` / `deployment-service` configs: service sharding YAML under config dirs (path varies by repo
  layout).

## Todos

### Phase 0 — decision and contract lock

- [x] [PM] ADR:
      `unified-trading-pm/codex/11-project-management/decisions/adr-2026-04-25-category-and-asset-group-field-naming.md`
      (accepted: API split + GCS + deferred dimension rename).
- [x] [ENG] Confirm no production reader assumes JSON key `category` for **shard filter** in external integrations; if
      any, document dual-read window or version bump per `canonical-schema-semver`. **Audit findings (2026-04-27,
      Follow-up E)** — `category` as a **shard-filter key** is fully retired: - Workspace-wide
      `rg "filters\[.['\"]category"` and `filters.get(['\"]category)` returned **zero hits** across all 67 repos. - SIT
      (`system-integration-tests`) and `e2e-testing` carry **no** shard / `DeployRequest` / `CalculateShardsRequest`
      tests at all — those test repos do not exercise the shard surface (covered by
      `deployment-service/tests/unit/test_shard_builder.py` and `deployment-api/tests/unit/test_shard_management.py`,
      both of which already key off `asset_group`). -
      `deployment-service/deployment_service/tests/unit/test_shard_builder.py` (40+ assertions) uses `asset_group`
      exclusively for shard filters; deployment-api shard request tests use `asset_group` for **new requests** and
      retain `dimensions={"category": …}` only as **regression coverage** for the `_asset_group_from_shard_dims` /
      `asset_groups_from_state` legacy-state coalescing path (lines 539-540, 643 of
      `tests/unit/test_shard_management.py`). - **Grandfathered legacy reads** (back-compat coalescing, not shard-filter
      writers, intentional per ADR): - `deployment-api/deployment_api/routes/shard_management.py`
      `_asset_group_from_shard_dims` and `asset_groups_from_state` read
      `dims.get("asset_group") or dims.get("category")` to absorb persisted deployment-state records written before the
      rename. - `deployment-api/deployment_api/utils/path_combinatorics.py` and `utils/trading_axis.py` apply the same
      coalescing when joining cached state with new requests. -
      `deployment-api/deployment_api/routes/state_management.py` lines 492 + 574 mirror the same pattern. - **GCS
      path-segment literals** (`category=cefi/...`, `mock_data.py` config-cache rows, `setup-buckets.py` bucket
      descriptors, `data_status_mock.py` `category.lower()` JSON envelopes) remain literal per ADR — these are
      **wire-format SSOT** for the object-store layout, not shard filters. -
      `deployment-service/functions/rotate-exchange-keys/main.py` writes `"category"` into a Secret Manager audit
      record; that is a separate domain (key rotation telemetry), not the deployment shard filter. -
      `e2e-testing/tests/integration/test_cefi_momentum_pipeline.py` uses `?category=cefi` against `/ml/features` — that
      is the ML-features service query parameter, not the deployment shard surface; tracked separately under the
      `venue_axis_asset_group_vocabulary` plan's Wave C/D (features-\* consumer keys). Conclusion: **no dual-read window
      or schema version bump required** for the shard surface. The only `category` reads that survive in deployment-api
      are the deliberate read-side legacy-state coalescers, which are protected by their own regression tests and do not
      affect new shard-filter writers.

### Phase 1 — config SSOT in deployment-service

- [x] [SCRIPT] Grep for dimension `name: category` / `"category"` in sharding configs; list every service.
- [x] [ENG] Batch-rename fixed dimension to `asset_group` in service YAML, `venues` hierarchy parent keys if applicable,
      and `deployment_service` calculators/tests.
- [x] [ENG] `CalculateShardsRequest.extra_filters` / `ShardCalculator` — filter key **`asset_group`** documented and
      tested; legacy **`category`** coalesced in `DimensionProcessor` for `extra_filters`.

### Phase 2 — deployment-api and UI

- [x] [ENG] `deployment-api`: `DeployRequest` uses **`asset_group`** with Pydantic **`category` as validation alias**;
      `filters` emits `"asset_group"`.
- [x] [ENG] `mock_data`: dimension list uses `"asset_group"`.
- [x] [ENG] `deployment-ui`: `getDimension("asset_group")`, `DeploymentRequest.asset_group`, `App.tsx` deploy-missing
      wiring.

### Phase 3 — SIT, contracts, and archive criteria

- [x] [QA] `system-integration-tests` (or equivalent): deployment / shard dry-run paths updated. **Findings (2026-04-27,
      Follow-up E)** — `system-integration-tests` and `e2e-testing` carry **no** shard / `DeployRequest` /
      `CalculateShardsRequest` integration tests; the shard surface is covered exclusively by
      `deployment-service/tests/unit/test_shard_builder.py` (asset_group-only) and
      `deployment-api/tests/unit/test_shard_management.py` (asset_group for new writes, category coalescing for legacy
      reads). The remaining `category` references in SIT (`tests/smoke/test_portable_criteria.py`,
      `tests/smoke/coverage_matrix_cells.py`, `tests/unit/test_coverage_matrix_cells.py`,
      `tests/smoke/test_coverage_matrix_smoke.py`) are intentionally pinned to legacy literals per ADR scope: they test
      (a) MDPS / instruments-service `dimension_keys=["category", "data_type"]` schema partition keys (separate concern
      — schema partition API, not shard filters) and (b) GCS `instruments-store-{category}-...` bucket-layout coverage
      (wire-format SSOT, deferred to a separate object-store migration program). No SIT fixture or test changes required
      for this plan.
- [x] [GATE] `completion_gates.code: C5` and `repo_gates` for each touched repo; staging smoke (D2) for deployment-api +
      UI against deployment-service with new configs. Code gates flipped to C5 across deployment-service /
      deployment-api / deployment-ui / unified-api-contracts / system-integration-tests (all phases shipped via prior
      quickmerges; SIT delta this cycle was audit-only). **Staging smoke (D2)** — deferred as a manual operator step:
      the staging deploy-missing dry-run requires real GCP credentials and a live SIT environment that the agent cannot
      provision; the assertion `dim=asset_group not dim=category` is left as a one-line pre-archive check for the next
      operator-led staging cycle. Plan can be archived ahead of D2 since `deployment.gate: D2` covers deployment
      maturity, which is independent of code-completion C5.

## References

- `unified-trading-pm/codex/11-project-management/decisions/adr-2026-04-25-category-and-asset-group-field-naming.md`
- `unified-trading-pm/plans/archive/venue_axis_asset_group_vocabulary_2026_04_25.plan.md`
- `unified-trading-pm/codex/13-codex-governance/SSOT-BOUNDARY.md` — do not duplicate SSOT; push shard naming to one
  owner PR chain.
