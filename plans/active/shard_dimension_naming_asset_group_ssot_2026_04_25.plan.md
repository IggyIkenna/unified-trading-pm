---
name: shard-dimension-naming-asset-group-ssot-2026-04-25
overview: |
  Coordinated, multi-repo pass to align **service shard configuration** and **all consumers** on the dimension name
  `asset_group` (trading venue axis) where the legacy name was `category`, without renaming GCS `category=` path
  segments until an explicit object-store migration exists. Complements the accepted API decision in
  `codex/11-project-management/decisions/adr-2026-04-25-category-and-asset-group-field-naming.md` and
  `venue_axis_asset_group_vocabulary_2026_04_25.plan.md`.
type: mixed
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: D2
  business: none

repo_gates:
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: system-integration-tests
    code: C0
    deployment: none
    business: none

depends_on:
  - venue-axis-asset-group-vocabulary-2026-04-25

isProject: false
---

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
- [ ] [ENG] Confirm no production reader assumes JSON key `category` for **shard filter** in external integrations; if
      any, document dual-read window or version bump per `canonical-schema-semver`.

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

- [ ] [QA] `system-integration-tests` (or equivalent): deployment / shard dry-run paths updated.
- [ ] [GATE] `completion_gates.code: C5` and `repo_gates` for each touched repo; staging smoke (D2) for deployment-api +
      UI against deployment-service with new configs.

## References

- `unified-trading-pm/codex/11-project-management/decisions/adr-2026-04-25-category-and-asset-group-field-naming.md`
- `unified-trading-pm/plans/active/venue_axis_asset_group_vocabulary_2026_04_25.plan.md`
- `unified-trading-pm/codex/13-codex-governance/SSOT-BOUNDARY.md` — do not duplicate SSOT; push shard naming to one
  owner PR chain.
