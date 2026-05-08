# Session 1: Registry & API Foundation

> **2026-03-24:** Historical session charter. API names below were updated to the **consolidated** surface
> (**`unified-trading-api`**, **`auth-api`**) where they referred to standalone repos now under **`archive/`**. See
> **`archive/README.md`** and **`scripts/dev/ui-api-mapping.json`**.

## Services & Repos Affected

> **DO NOT work on these repos in other sessions -- they are owned by this session.**

| Repo                              | What Changes                                                                                                                  | Risk |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---- |
| unified-internal-contracts        | OpenAPI spec fixes: add unified-trading-api paths, fix 11 empty schemas                                                       | MED  |
| unified-trading-api               | **NEW REPO** — scaffold FastAPI app, domain routes, WebSocket, middleware, MockStateStore, seed; merged OpenAPI introspection | HIGH |
| unified-trading-pm                | scripts/openapi/, ui-api-mapping.json updates (port 8020), dev-start.sh updates, workspace-manifest.json entry                | LOW  |
| unified-market-interface          | Ensure classify_venue_error called on adapter errors (read-only audit + small fixes)                                          | LOW  |
| unified-trade-execution-interface | Ensure classify_venue_error called on adapter errors (read-only audit + small fixes)                                          | LOW  |

### Shared Repo Boundaries

- **unified-api-contracts**: Session 1 OWNS registry/ and scripts/generate_ui_reference_data.py. Session 2 does NOT
  touch UAC. Session 4 may read VENUE_ERROR_MAP but does NOT modify it.
- **unified-internal-contracts**: Session 1 OWNS openapi/ directory. Session 4 OWNS domain/ml/ and testing/. No overlap.
- **unified-trading-pm**: Session 1 OWNS scripts/openapi/, scripts/dev/ui-api-mapping.json, and workspace-manifest.json
  (unified-trading-api entry only). Session 2 does NOT touch PM scripts. Session 4 OWNS scripts/load-testing/ and
  configs/performance-baselines.json.
- **execution-service**: Session 1 OWNS engine/ adapter error classification wiring and scripts/quality-gates.sh
  (adapter coverage QG check). Session 2 OWNS config hot-reload callback wiring only. Session 4 OWNS performance gate
  fixtures only. No file overlap.

## Plans Covered

| Plan                           | Phases    | Todos Remaining | Reference                                                   |
| ------------------------------ | --------- | --------------- | ----------------------------------------------------------- |
| Plan A: Registry & Schema Sync | Phase 0-3 | ~14 todos       | plans/active/plan_a_registry_schema_sync_2026_03_21.md |
| Plan H: API Consolidation      | Phase 0-6 | ~44 todos       | plans/active/plan_h_api_consolidation_2026_03_21.md    |

## What's Already Done (Don't Redo)

execution-service wiring as already done in prior sessions. **Verify status before re-doing** -- check UAC

- instruments_service_batch_validation Phase B1 (UAC reference data centralization) is DONE -- tradfi_symbology.py,
  defi_protocol_registry.py, market_data_categories.py all created in UAC.
- instrument_data_source_separation is a separate plan but touches UAC tradfi_symbology.py -- coordinate if needed but
  that plan is assigned to Session 3.

## Execution Order

1. **Plan A Phase 0** (PARALLEL, no dependencies):
   - p0-validate-missing-registries: audit generate_ui_reference_data.py for 9 missing registries
   - p0-validate-openapi-gaps: audit OpenAPI spec for empty schemas and missing APIs
   - p0-fix-aave-plasma-bug: fix error classifier mapping (verify not already done)
   - p0-add-18-missing-venue-error-maps: add to VENUE_ERROR_MAP (verify not already done)
   - p0-wire-classify-venue-error-execution: wire into execution-service adapter calls

2. **Plan A Phase 1** (SEQUENTIAL after Phase 0):
   - p1-enhance-registry-extractor: enhance generate_ui_reference_data.py for all 13 registries
   - p1-add-registry-tests: one test per registry category
   - p1-qg-gate-uac: quality-gates.sh on UAC

3. **Plan A Phase 2** (PARALLEL with Phase 1):
   - p2-add-unified-trading-api-spec: introspect unified-trading-api routes, add to OpenAPI
   - p2-fix-empty-schemas: populate 11 empty {} schemas from Pydantic models
   - p2-restore-openapi-typescript: fix codegen script output (currently .bak file)
   - p2-qg-gate-uic: quality-gates.sh on UIC

4. **Plan A Phase 3** (SEQUENTIAL after Phases 1+2):
   - p3-ci-trigger-uac-to-ui: GHA workflow for UAC commit -> registry regen
   - p3-ci-trigger-uic-to-ui: GHA workflow for UIC commit -> OpenAPI codegen
   - p3-qg-check-adapter-coverage: QG check for adapter error classification
   - p3-final-qg-sweep: all 5 backend repos

5. **Plan H Phase 0** (can start PARALLEL with Plan A Phase 1+):
   - Scaffold unified-trading-api repo (FastAPI, pyproject.toml, quality-gates.sh)
   - Health endpoint, entitlement middleware, MockStateStore
   - Add to workspace-manifest.json and ui-api-mapping.json

6. **Plan H Phase 1** (PARALLEL -- all 14 domain route modules independent):
   - market-data, execution, positions, trading-analytics, ml, reporting, audit, config, alerts, risk, instruments,
     documents, deployment, service-status, users

7. **Plan H Phases 2-4** (PARALLEL with each other, after Phase 1):
   - Phase 2: WebSocket endpoint + channels + mock/real mode + auth
   - Phase 3: seed_mock_data.py for all 16 domains
   - Phase 4: OpenAPI spec generation + TypeScript codegen

8. **Plan H Phases 5-6** (SEQUENTIAL after 2-4):
   - Phase 5: Update dev-start.sh, ui-api-mapping.json, deprecate old API repos
   - Phase 6: Final QG sweep

## Key Rules

- `uv pip install` not `pip install`
- Never run pytest directly -- use `bash scripts/quality-gates.sh`
- Do NOT run quickmerge -- only `git add` + `git commit`
- `basedpyright` not `pyright` (with `run_timeout 120`)
- Flat deps only in pyproject.toml -- no `[project.optional-dependencies]`
- For unified-trading-api (new repo): use `ARG PROJECT_ID` + base image pattern in Dockerfile, NOT `python:3.13-slim`
- Services use URDI for reference data, not UMI
- Every adapter MUST classify errors through UAC `classify_venue_error()` and emit `ADAPTER_FETCH_FAILED` events
- UAC import rules: consumers import from domain facades only (`from unified_api_contracts.{domain} import ...`), never
  from `canonical.*` or `normalize_utils.*`

## CITADEL AUDIT FINDINGS (2026-03-21)

This session needs to address the following honest status corrections:

1. **Registry generation: 0/9 new registries extracted.** generate_ui_reference_data.py exists but only handles 4/13
   categories. Phase 1 is correctly NOT STARTED — the script enhancement is real work, not a verification task.

2. **OpenAPI spec: 7 services missing, 66 empty schemas.** Phase 2 is correctly NOT STARTED. The empty schema count was
   originally reported as 11, then 86 by audit, corrected to 66 after removing intentional markers.

3. **unified-trading-api is P3 SCAFFOLD.** Route module files exist from a prior session but return mock data or "not
   yet wired" placeholder responses. Zero Pydantic response schemas are defined. Only 1 test. This is NOT a working API
   — it needs to be rebuilt properly with real models and response schemas.

4. **Plan A Phase 0 audits ARE genuinely done** — the audit correctly identified gaps. Execution work (Phase 1+) is what
   remains. Do not waste time re-auditing.

## Success Criteria

- [ ] All QGs pass on: unified-api-contracts, unified-internal-contracts, unified-trading-api, unified-market-interface,
      unified-trade-execution-interface
- [ ] generate_ui_reference_data.py extracts all 13 registry categories with tests
- [ ] OpenAPI spec has unified-trading-api, zero empty schemas
- [ ] CI trigger workflows created (UAC->UI, UIC->UI)
- [ ] unified-trading-api scaffolded with all 61 endpoints across 16 domains
- [ ] WebSocket endpoint with channel multiplexing (mock + real mode)
- [ ] unified-trading-api quality-gates.sh passes
- [ ] All 61 endpoints return correct mock data
- [ ] Entitlement filtering works (internal=all, external=scoped)
